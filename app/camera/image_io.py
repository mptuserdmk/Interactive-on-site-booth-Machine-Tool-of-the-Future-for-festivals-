"""
Приём фото с телефона ассистента (S4, H16).

- лимит размера (settings.MAX_UPLOAD_MB) — плюс UploadSizeLimitMiddleware режет запрос по Content-Length
  ещё до разбора multipart;
- формат определяется по содержимому, а не по имени/Content-Type; SVG/HTML/EXE → 415;
- HEIC (галерея iPhone) → 415 с понятной подсказкой вместо ERROR посреди пайплайна;
- decompression bomb: проверка числа пикселей ДО декодирования;
- EXIF Orientation применяется (портреты с iPhone больше не «боком»);
- перекодирование в чистый JPEG: отрезает полиглоты (JPEG+HTML/ZIP) и метаданные с GPS;
- одновременно декодируется не более 2 фото — 100 параллельных загрузок не съедают память.
"""
import io
import threading
from typing import Tuple

from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from app.config.settings import settings

ALLOWED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}
HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1", b"avif"}
MAX_PIXELS = 40_000_000
MIN_SIDE = 32
MAX_SIDE = 2560
_decode_slots = threading.BoundedSemaphore(2)


class UploadRejected(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def max_upload_bytes() -> int:
    return settings.MAX_UPLOAD_MB * 1024 * 1024


def _is_heif(data: bytes) -> bool:
    return len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in HEIF_BRANDS


def normalize_photo(data: bytes) -> Tuple[bytes, Tuple[int, int]]:
    """Проверяет загруженные байты и возвращает чистый JPEG (RGB, без EXIF) и его размер."""
    if not data:
        raise UploadRejected(400, "Пустой файл")
    if len(data) > max_upload_bytes():
        raise UploadRejected(413, f"Файл больше {settings.MAX_UPLOAD_MB} МБ")
    if _is_heif(data):
        raise UploadRejected(415, "Формат HEIC/HEIF не поддерживается. На iPhone: Настройки → Камера → "
                                  "Форматы → «Наиболее совместимый», или снимайте кнопкой 📸 на странице")
    with _decode_slots:
        try:
            with Image.open(io.BytesIO(data)) as im:
                if im.format not in ALLOWED_FORMATS:
                    raise UploadRejected(415, f"Формат {im.format} не поддерживается: нужен JPEG или PNG")
                w, h = im.size
                if w * h > MAX_PIXELS:
                    raise UploadRejected(413, f"Слишком большое разрешение: {w}×{h}")
                if min(w, h) < MIN_SIDE:
                    raise UploadRejected(422, f"Слишком маленькое изображение: {w}×{h}")
                img = ImageOps.exif_transpose(im)
                img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
                if img.mode in ("RGBA", "LA", "P"):
                    rgba = img.convert("RGBA")
                    bg = Image.new("RGB", rgba.size, (255, 255, 255))
                    bg.paste(rgba, mask=rgba.getchannel("A"))
                    img = bg
                else:
                    img = img.convert("RGB")
                out = io.BytesIO()
                img.save(out, "JPEG", quality=92)
                return out.getvalue(), img.size
        except UploadRejected:
            raise
        except Image.DecompressionBombError as e:
            raise UploadRejected(413, "Слишком большое разрешение изображения") from e
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as e:
            raise UploadRejected(415, "Файл не является изображением JPEG/PNG") from e


class UploadSizeLimitMiddleware:
    """413 по заголовку Content-Length до того, как multipart-парсер запишет тело во временный файл."""

    def __init__(self, app, paths):
        self.app = app
        self.paths = set(paths)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] in self.paths:
            length = Headers(scope=scope).get("content-length")
            if length and length.isdigit() and int(length) > max_upload_bytes() + 64 * 1024:
                resp = JSONResponse({"detail": f"Файл больше {settings.MAX_UPLOAD_MB} МБ"}, status_code=413)
                return await resp(scope, receive, send)
        await self.app(scope, receive, send)
