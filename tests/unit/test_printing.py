"""
Печать (H10 и новые находки по os.startfile). Реальный принтер НЕ используется:
- os.startfile в conftest заменён на функцию, которая падает;
- win32print подменяется фейковым модулем.
"""
import sys
import types
from pathlib import Path

import pytest

from helpers import write_photo

pytestmark = pytest.mark.unit

STATUS_PAPER_OUT = 0x10
STATUS_OFFLINE = 0x80
STATUS_ERROR = 0x2


def fake_win32print(printers, status=0, jobs=0, default=None):
    m = types.ModuleType("win32print")
    m.PRINTER_ENUM_LOCAL = 2
    m.PRINTER_ENUM_CONNECTIONS = 4
    m.PRINTER_STATUS_PAPER_OUT = STATUS_PAPER_OUT
    m.PRINTER_STATUS_OFFLINE = STATUS_OFFLINE
    m.PRINTER_STATUS_ERROR = STATUS_ERROR
    m.PRINTER_ATTRIBUTE_WORK_OFFLINE = 0x400
    m.EnumPrinters = lambda flags, name=None, level=1: [(0, f"{p},,", p, "") for p in printers]
    m.GetDefaultPrinter = lambda: default or (printers[0] if printers else "")
    m.OpenPrinter = lambda name, defaults=None: name
    m.ClosePrinter = lambda h: None
    m.GetPrinter = lambda h, level=2: {"pPrinterName": h, "Status": status, "cJobs": jobs, "Attributes": 0}
    return m


@pytest.fixture
def hw_mode(monkeypatch):
    """Не-симуляционный режим менеджера печати (без реального принтера)."""
    from app.printing.manager import print_manager
    monkeypatch.setattr(print_manager, "is_simulation", False)
    return print_manager


@pytest.mark.regression
def test_no_printers_is_not_ready(hw_mode, monkeypatch):
    """H10: get_status() всегда is_ready=True."""
    monkeypatch.setitem(sys.modules, "win32print", fake_win32print([]))
    assert hw_mode.get_status()["is_ready"] is False


@pytest.mark.regression
@pytest.mark.parametrize("status", [STATUS_PAPER_OUT, STATUS_OFFLINE, STATUS_ERROR])
def test_printer_error_status_is_not_ready(hw_mode, monkeypatch, status):
    monkeypatch.setitem(sys.modules, "win32print", fake_win32print(["DNP DS620"], status=status))
    st = hw_mode.get_status()
    assert st["is_ready"] is False, st


@pytest.mark.regression
def test_configured_printer_missing_is_not_ready(hw_mode, monkeypatch):
    monkeypatch.setitem(sys.modules, "win32print", fake_win32print(["Samsung ML-1860 Series"]))
    monkeypatch.setattr(hw_mode, "printer_name", "DNP DS620")
    st = hw_mode.get_status()
    assert st["is_ready"] is False, st


@pytest.mark.regression
def test_pywin32_missing_status_unknown_not_ready(hw_mode, monkeypatch):
    """В прод-requirements.txt нет pywin32 → ImportError → «Default Windows Printer (Simulated/Direct)» и OK."""
    monkeypatch.setitem(sys.modules, "win32print", None)
    st = hw_mode.get_status()
    assert st["is_ready"] is False, st


def test_ready_printer_is_ready(hw_mode, monkeypatch):
    monkeypatch.setitem(sys.modules, "win32print", fake_win32print(["DNP DS620"], status=0, jobs=0))
    monkeypatch.setattr(hw_mode, "printer_name", "DNP DS620")
    st = hw_mode.get_status()
    assert st["is_ready"] is True, st
    assert st["active_printer"] == "DNP DS620"


def test_simulation_mode_ready():
    from app.printing.manager import print_manager
    assert print_manager.is_simulation is True
    assert print_manager.get_status()["is_ready"] is True


async def test_print_missing_file(fast_print):
    from app.printing.manager import print_manager
    res = await print_manager.print_card(Path("Z:/nope/card.jpg"), "sess_x")
    assert res["success"] is False
    assert "not found" in res["error"].lower() or "не найден" in res["error"].lower()


async def test_print_simulation_records_history(tmp_path, fast_print):
    from app.printing.manager import print_manager
    card = write_photo(tmp_path / "c.jpg")
    res = await print_manager.print_card(card, "sess_x")
    assert res["success"] is True
    assert print_manager.print_history[-1]["session_id"] == "sess_x"


async def test_hardware_print_exception_is_reported(hw_mode, tmp_path, monkeypatch):
    """os.startfile/драйвер бросает исключение → success=False и понятная ошибка, без падения."""
    import os
    card = write_photo(tmp_path / "c.jpg")

    def boom(*a, **k):
        raise OSError("Устройство не готово")

    monkeypatch.setattr(os, "startfile", boom, raising=False)
    monkeypatch.setattr(hw_mode, "_gdi_print", boom, raising=False)
    monkeypatch.setitem(sys.modules, "win32print", fake_win32print(["DNP DS620"]))
    monkeypatch.setattr(hw_mode, "printer_name", "DNP DS620")
    res = await hw_mode.print_card(card, "sess_x")
    assert res["success"] is False
    assert res["error"]


@pytest.mark.regression
async def test_hardware_print_targets_configured_printer_without_dialog(hw_mode, tmp_path, monkeypatch):
    """Новая находка: os.startfile(path, "print") для .jpg на Windows открывает интерактивный
    мастер «Печать изображений» (photowiz.dll) и печатает на принтер ПО УМОЛЧАНИЮ.
    PRINTER_NAME игнорируется, «автопечать» ждёт клика человека."""
    import os
    card = write_photo(tmp_path / "c.jpg")
    calls = []
    monkeypatch.setattr(os, "startfile", lambda *a, **k: calls.append(("startfile", a)), raising=False)
    monkeypatch.setattr(hw_mode, "_gdi_print", lambda path, printer: calls.append(("gdi", (str(path), printer))),
                        raising=False)
    monkeypatch.setitem(sys.modules, "win32print", fake_win32print(["Samsung ML-1860 Series", "DNP DS620"],
                                                                  default="Samsung ML-1860 Series"))
    monkeypatch.setattr(hw_mode, "printer_name", "DNP DS620")
    res = await hw_mode.print_card(card, "sess_x")
    assert res["success"] is True, res
    assert not any(kind == "startfile" for kind, _ in calls), f"печать через ShellExecute 'print': {calls}"
    assert any("DNP DS620" in str(args) for _, args in calls), f"не указан PRINTER_NAME: {calls}"


def test_pywin32_in_prod_requirements():
    """Без pywin32 в requirements.txt статус принтера на чистой машине не определяется вообще."""
    req = (Path(__file__).resolve().parents[2] / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pywin32" in req
