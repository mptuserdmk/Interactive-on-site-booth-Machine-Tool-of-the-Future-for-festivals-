import sys
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.config.settings import settings

logger = logging.getLogger("stanok.print")

# Флаги PRINTER_INFO_2.Status (winspool.h)
PRINTER_STATUS_PROBLEMS = {
    0x00000001: "пауза",
    0x00000002: "ошибка принтера",
    0x00000008: "замятие бумаги",
    0x00000010: "нет бумаги",
    0x00000020: "ручная подача",
    0x00000040: "проблема с бумагой",
    0x00000080: "принтер offline",
    0x00000800: "лоток выдачи полон",
    0x00001000: "принтер недоступен",
    0x00040000: "нет красителя/ленты",
    0x00400000: "открыта крышка",
}
PRINTER_ATTRIBUTE_WORK_OFFLINE = 0x00000400

# GetDeviceCaps
HORZRES, VERTRES = 8, 10


class PrintManager:
    def __init__(self):
        self.printer_name = settings.PRINTER_NAME
        self.is_simulation = settings.PRINT_SIMULATION_MODE
        self.print_history: List[Dict[str, Any]] = []

    @staticmethod
    def _win32print():
        try:
            import win32print
            return win32print
        except ImportError:
            return None

    def get_available_printers(self) -> List[str]:
        wp = self._win32print() if sys.platform == "win32" else None
        if not wp:
            return []
        try:
            return [p[2] for p in wp.EnumPrinters(wp.PRINTER_ENUM_LOCAL | wp.PRINTER_ENUM_CONNECTIONS)]
        except Exception:
            logger.exception("EnumPrinters failed")
            return []

    def _printer_problem(self, wp, name: str) -> tuple[Optional[str], int]:
        try:
            handle = wp.OpenPrinter(name)
            try:
                info = wp.GetPrinter(handle, 2)
            finally:
                wp.ClosePrinter(handle)
        except Exception as e:
            return f"принтер не отвечает: {type(e).__name__}", 0
        status = int(info.get("Status", 0) or 0)
        problems = [text for flag, text in PRINTER_STATUS_PROBLEMS.items() if status & flag]
        if int(info.get("Attributes", 0) or 0) & PRINTER_ATTRIBUTE_WORK_OFFLINE:
            problems.append("принтер в режиме offline")
        return (", ".join(problems) or None), int(info.get("cJobs", 0) or 0)

    def get_status(self) -> Dict[str, Any]:
        """Раньше is_ready всегда был True (H10): оператор не видел, что принтер выключен или без бумаги."""
        printers = self.get_available_printers()
        base = {"printers": printers, "simulation_mode": self.is_simulation,
                "total_printed": len(self.print_history), "queue_jobs": 0}
        if self.is_simulation:
            return {**base, "is_ready": True, "problem": None, "active_printer": "SIMULATION"}

        wp = self._win32print() if sys.platform == "win32" else None
        target = self.printer_name or None
        problem = None
        jobs = 0
        if sys.platform != "win32":
            problem = "печать поддерживается только в Windows"
        elif wp is None:
            problem = "pywin32 не установлен — состояние принтера неизвестно"
        elif not printers:
            problem = "принтеры не найдены"
        else:
            if not target:
                try:
                    target = wp.GetDefaultPrinter()
                except Exception:
                    target = None
            if not target or target not in printers:
                problem = f"принтер «{target or 'по умолчанию'}» не найден"
            else:
                problem, jobs = self._printer_problem(wp, target)
        return {**base, "is_ready": problem is None, "problem": problem,
                "active_printer": target or "—", "queue_jobs": jobs}

    def _gdi_print(self, file_path: Path, printer_name: str, output_file: Optional[str] = None):
        """Печать без диалогов: JPEG → GDI-контекст конкретного принтера, вписываем в печатную область.
        Раньше os.startfile(path, "print") открывал интерактивный мастер «Печать изображений»
        (photowiz.dll) и печатал на принтер ПО УМОЛЧАНИЮ, игнорируя PRINTER_NAME."""
        import win32ui
        from PIL import Image, ImageWin

        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        try:
            area_w, area_h = hdc.GetDeviceCaps(HORZRES), hdc.GetDeviceCaps(VERTRES)
            with Image.open(file_path) as src:
                img = src.convert("RGB")
            if (img.width > img.height) != (area_w > area_h):
                img = img.rotate(90, expand=True)
            ratio = min(area_w / img.width, area_h / img.height)
            w, h = int(img.width * ratio), int(img.height * ratio)
            x, y = (area_w - w) // 2, (area_h - h) // 2
            if output_file:
                hdc.StartDoc(file_path.name, output_file)
            else:
                hdc.StartDoc(file_path.name)
            hdc.StartPage()
            ImageWin.Dib(img).draw(hdc.GetHandleOutput(), (x, y, x + w, y + h))
            hdc.EndPage()
            hdc.EndDoc()
        finally:
            hdc.DeleteDC()

    async def print_card(self, file_path: Path, session_id: str) -> Dict[str, Any]:
        """Prints physical card on photo printer."""
        if not file_path.exists():
            return {"success": False, "error": f"Card file not found: {file_path.name}"}

        start_time = time.time()

        if self.is_simulation:
            # Simulate print delay (3 seconds)
            await asyncio.sleep(2.5)
            log_entry = {
                "session_id": session_id,
                "file_path": str(file_path),
                "timestamp": time.time(),
                "status": "PRINTED_SIMULATED"
            }
            self.print_history.append(log_entry)
            return {"success": True, "message": "Printed in simulation mode", "duration": round(time.time() - start_time, 2)}

        status = self.get_status()
        if not status["is_ready"]:
            return {"success": False, "error": f"Принтер не готов: {status['problem']}"}

        try:
            await asyncio.to_thread(self._gdi_print, file_path, status["active_printer"])
            log_entry = {
                "session_id": session_id,
                "file_path": str(file_path),
                "timestamp": time.time(),
                "status": "SENT_TO_SPOOLER",
                "printer": status["active_printer"]
            }
            self.print_history.append(log_entry)
            return {"success": True, "message": "Card sent to printer spooler", "duration": round(time.time() - start_time, 2)}
        except Exception as e:
            logger.exception("Print failed for %s", session_id)
            return {"success": False, "error": f"Print failed: {type(e).__name__}: {str(e)[:120]}"}


print_manager = PrintManager()
