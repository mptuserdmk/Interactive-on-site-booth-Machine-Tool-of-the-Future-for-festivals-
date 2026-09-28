"""
POST /api/camera/upload-ota (S4, H16): размер, тип, магические байты, decompression bomb, полиглоты,
HEIC, path traversal, параллельные загрузки.
"""
import asyncio
import io

import psutil
import pytest
from PIL import Image

from helpers import active_state, make_photo_bytes

pytestmark = [pytest.mark.security]

URL = "/api/camera/upload-ota"


def _stored(sid):
    from app.config.settings import settings
    return settings.PHOTOS_DIR / f"{sid}_raw.jpg"


async def upload(client, content, name="photo.jpg", ctype="image/jpeg"):
    return await client.post(URL, files={"file": (name, content, ctype)})


def bomb_png(w=20000, h=20000):
    buf = io.BytesIO()
    Image.new("1", (w, h), 0).save(buf, "PNG", optimize=True)
    return buf.getvalue()


async def test_valid_jpeg_accepted_and_stored_as_jpeg(client):
    r = await upload(client, make_photo_bytes())
    assert r.status_code == 200, r.text
    with Image.open(_stored(r.json()["session_id"])) as im:
        assert im.format == "JPEG"


@pytest.mark.regression
async def test_png_disguised_as_jpg_is_normalized_to_jpeg(client):
    r = await upload(client, make_photo_bytes(fmt="PNG", mode="RGBA"), name="x.jpg")
    assert r.status_code == 200, r.text
    with Image.open(_stored(r.json()["session_id"])) as im:
        assert im.format == "JPEG", f"на диске лежит {im.format} под именем .jpg"


@pytest.mark.regression
@pytest.mark.parametrize("case,content,ctype", [
    ("empty", b"", "image/jpeg"),
    ("text", b"hello, I am not an image", "image/jpeg"),
    ("html", b"<html><script>alert(1)</script></html>", "text/html"),
    ("svg", b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>', "image/svg+xml"),
    ("exe", b"MZ\x90\x00" + b"\x00" * 200, "application/octet-stream"),
    ("heic", b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 500, "image/heic"),
])
async def test_non_images_rejected(client, case, content, ctype):
    """S4/H16: не-изображение принимается (200), сессия уходит в PHOTO_TAKEN, а потом падает в ERROR."""
    r = await upload(client, content, name=f"x.{case}", ctype=ctype)
    assert r.status_code in (400, 415, 422), f"{case}: {r.status_code} {r.text[:120]}"
    st = await active_state(client)
    assert not st or st["status"] != "PHOTO_TAKEN"


@pytest.mark.regression
async def test_heic_rejection_message_is_actionable(client):
    content = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 500
    r = await upload(client, content, name="IMG_0001.HEIC", ctype="image/heic")
    assert r.status_code == 415
    assert "HEIC" in r.text


@pytest.mark.regression
async def test_oversized_upload_rejected_413(client):
    """S4: await file.read() целиком в память без лимита."""
    big = make_photo_bytes(size=(64, 64)) + b"\x00" * (16 * 1024 * 1024)
    r = await upload(client, big)
    assert r.status_code == 413, f"16 МБ приняты: {r.status_code}"


@pytest.mark.regression
async def test_oversized_by_content_length_rejected_before_parsing(client):
    """Лимит должен срабатывать по заголовку Content-Length, до разбора multipart во временный файл."""
    body = b"x" * 1024
    r = await client.post(URL, content=body, headers={
        "content-type": "multipart/form-data; boundary=zzz", "content-length": str(200 * 1024 * 1024)})
    assert r.status_code == 413


@pytest.mark.regression
async def test_decompression_bomb_rejected(client):
    """S4: PNG 20000×20000 (400 МП) весит ~50 КБ, при декодировании — сотни МБ/ГБ."""
    data = bomb_png()
    assert len(data) < 2 * 1024 * 1024
    r = await upload(client, data, name="bomb.png", ctype="image/png")
    assert r.status_code in (400, 413, 415, 422), f"бомба принята: {r.status_code}"


@pytest.mark.regression
async def test_huge_resolution_12000px_rejected_or_downscaled(client):
    data = bomb_png(12000, 12000)
    r = await upload(client, data, name="big.png", ctype="image/png")
    if r.status_code == 200:
        with Image.open(_stored(r.json()["session_id"])) as im:
            assert max(im.size) <= 4096, im.size
    else:
        assert r.status_code in (400, 413, 422)


@pytest.mark.regression
async def test_polyglot_payload_stripped(client):
    """JPEG + хвост с HTML/ZIP: должен быть перекодирован, хвост не сохраняется."""
    payload = make_photo_bytes() + b"<script>alert(document.cookie)</script>PK\x03\x04zipzip"
    r = await upload(client, payload)
    assert r.status_code == 200
    assert b"<script>" not in _stored(r.json()["session_id"]).read_bytes()


async def test_path_traversal_in_filename_ignored(client):
    from app.config.settings import settings
    r = await upload(client, make_photo_bytes(), name="..\\..\\..\\evil.jpg")
    assert r.status_code == 200
    assert not (settings.STORAGE_DIR / "evil.jpg").exists()
    assert not (settings.PHOTOS_DIR.parent.parent / "evil.jpg").exists()
    assert _stored(r.json()["session_id"]).exists()


@pytest.mark.regression
async def test_exif_orientation_normalized_on_upload(client):
    """H16: фото с EXIF Orientation=6 сохраняется «как есть»; Pillow дальше его не поворачивает."""
    r = await upload(client, make_photo_bytes(size=(800, 600), exif_orientation=6))
    assert r.status_code == 200
    with Image.open(_stored(r.json()["session_id"])) as im:
        assert im.size == (600, 800), f"размер на диске {im.size}, ориентация не применена"
        assert im.getexif().get(0x0112, 1) == 1


@pytest.mark.slow
async def test_parallel_uploads_no_5xx_bounded_memory(client):
    """100 параллельных загрузок по ~1 МБ: нет 5xx, RSS процесса растёт умеренно."""
    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    photo = make_photo_bytes(size=(2000, 1500))
    rs = await asyncio.gather(*[upload(client, photo) for _ in range(100)])
    rss1 = proc.memory_info().rss
    codes = sorted({r.status_code for r in rs})
    print(f"\n[S4] 100 параллельных загрузок: коды={codes}, ΔRSS={(rss1 - rss0) / 2**20:.0f} МБ")
    assert all(r.status_code < 500 for r in rs)
    assert rss1 - rss0 < 800 * 2**20
