import qrcode
from PIL import Image
from pathlib import Path
from app.config.settings import settings

def generate_qr_code(url: str, size: int = 240) -> Image.Image:
    """Generates clean high-contrast QR code image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#0b101b", back_color="#ffffff").convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img

def get_digital_card_url(session_id: str) -> str:
    platform = (getattr(settings, "BOT_PLATFORM", "max") or "max").lower().strip()
    max_user = (getattr(settings, "MAX_BOT_USERNAME", "") or "").strip().lstrip("@")
    tg_user = (getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "").strip().lstrip("@")

    if platform in ("max", "both") and max_user:
        return f"https://max.ru/{max_user}?start={session_id}"
    if tg_user:
        return f"https://t.me/{tg_user}?start={session_id}"
    return f"{settings.BASE_URL}/card/{session_id}"
