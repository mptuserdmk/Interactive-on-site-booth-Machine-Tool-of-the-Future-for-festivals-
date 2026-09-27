import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.config.settings import settings

class PrintManager:
    def __init__(self):
        self.printer_name = settings.PRINTER_NAME
        self.is_simulation = settings.PRINT_SIMULATION_MODE
        self.print_history: List[Dict[str, Any]] = []

    def get_available_printers(self) -> List[str]:
        if sys.platform == "win32":
            try:
                import win32print
                printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
                return printers
            except ImportError:
                return ["Default Windows Printer (Simulated/Direct)"]
        return ["Default System Printer"]

    def get_status(self) -> Dict[str, Any]:
        printers = self.get_available_printers()
        return {
            "is_ready": True,
            "printers": printers,
            "active_printer": self.printer_name or (printers[0] if printers else "Default"),
            "simulation_mode": self.is_simulation,
            "total_printed": len(self.print_history)
        }

    async def print_card(self, file_path: Path, session_id: str) -> Dict[str, Any]:
        """Prints physical card on photo printer."""
        if not file_path.exists():
            return {"success": False, "error": f"Card file not found: {file_path}"}

        start_time = time.time()

        if self.is_simulation or not sys.platform == "win32":
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

        # Windows Physical Print Execution
        try:
            # Method 1: win32print ShellExecute or default print association
            os.startfile(str(file_path), "print")
            
            log_entry = {
                "session_id": session_id,
                "file_path": str(file_path),
                "timestamp": time.time(),
                "status": "SENT_TO_SPOOLER"
            }
            self.print_history.append(log_entry)
            return {"success": True, "message": "Card sent to printer spooler", "duration": round(time.time() - start_time, 2)}
        except Exception as e:
            return {"success": False, "error": f"Print failed: {str(e)}"}

print_manager = PrintManager()
