"""
Реальный путь печати через GDI (без диалогов) на ВИРТУАЛЬНЫЙ принтер «Microsoft Print to PDF»
с выводом в файл во временной папке. Физический принтер не используется: имя принтера и output_file
проверяются жёстко, иначе тест не запускается.
"""
import sys
from pathlib import Path

import pytest

from helpers import write_photo

pytestmark = pytest.mark.e2e
VIRTUAL_PDF = "Microsoft Print to PDF"


@pytest.mark.skipif(sys.platform != "win32", reason="только Windows")
def test_gdi_print_to_virtual_pdf_printer(tmp_path):
    import win32print
    from PIL import Image
    from app.printing.manager import print_manager

    printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
    if VIRTUAL_PDF not in printers:
        pytest.skip("нет виртуального принтера Microsoft Print to PDF")

    card = tmp_path / "card.jpg"
    Image.new("RGB", (1200, 1800), (20, 30, 60)).save(card, "JPEG", dpi=(300, 300))
    out_pdf = tmp_path / "out.pdf"
    assert str(out_pdf).startswith(str(tmp_path))

    print_manager._gdi_print(card, VIRTUAL_PDF, output_file=str(out_pdf))

    assert out_pdf.exists(), "PDF не создан — путь печати не работает"
    data = out_pdf.read_bytes()
    assert data.startswith(b"%PDF") and len(data) > 10_000
    print(f"\n[print] GDI → «{VIRTUAL_PDF}»: {out_pdf.stat().st_size} байт, без диалогов")
