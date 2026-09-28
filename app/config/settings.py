import secrets
import socket
from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def _is_lan_ip(ip: str) -> bool:
    return bool(ip) and not ip.startswith(("127.", "169.254.", "0."))


def get_local_ip() -> str:
    """Find the local network IP so iPhones/tablets on same WiFi can connect easily.
    Без маршрута по умолчанию (Wi-Fi площадки без интернета) UDP-трюк не работает — тогда берём
    адрес интерфейса, а не 127.0.0.1: иначе на напечатанных QR будет 127.0.0.1 (H11)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Doesn't actually make connection, just determines routing
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if _is_lan_ip(ip):
            return ip
    except Exception:
        pass
    try:
        _, _, addrs = socket.gethostbyname_ex(socket.gethostname())
        lan = [a for a in addrs if _is_lan_ip(a)]
        lan.sort(key=lambda a: not a.startswith(("192.168.", "10.", "172.")))
        if lan:
            return lan[0]
    except Exception:
        pass
    return "127.0.0.1"

class Settings(BaseSettings):
    # App info
    APP_NAME: str = "AI-Фотолокация «Станок Будущего»"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOCAL_IP: str = ""  # пусто → определяется автоматически
    BASE_URL: str = ""  # пусто → http://{LOCAL_IP}:{PORT} (раньше порт был захардкожен 8000, H11)
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    PHOTOS_DIR: Path = BASE_DIR / "storage" / "photos"
    GENERATED_DIR: Path = BASE_DIR / "storage" / "generated"
    CARDS_DIR: Path = BASE_DIR / "storage" / "cards"
    FALLBACK_DIR: Path = BASE_DIR / "assets" / "fallback"
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = BASE_DIR / "data" / "kiosk.db"
    
    # Camera
    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 1920
    CAMERA_HEIGHT: int = 1080
    CAMERA_FPS: int = 30
    CAMERA_MIRROR: bool = True
    MAX_UPLOAD_MB: int = 15  # лимит фото с телефона (S4)
    # Без USB-камеры «снимать» заглушку (демо). На фестивале — false: иначе ребёнку печатается mock-кадр
    CAMERA_MOCK_FALLBACK: bool = True

    # AI Provider: 'mock', 'bothub', 'fal', 'replicate', 'openai', 'stability'
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = ""
    BOTHUB_MODEL: str = "gemini-2.5-flash-image"
    AI_TIMEOUT_SECONDS: int = 35
    AI_FALLBACK_ON_ERROR: bool = True
    
    # Printer
    PRINTER_NAME: str = ""  # Empty string = default Windows printer
    ENABLE_AUTO_PRINT: bool = True
    PRINT_SIMULATION_MODE: bool = False  # If True, simulates print without sending to physical hardware
    
    REPRINT_COOLDOWN_SECONDS: int = 10  # защита бумаги от «REPRINT ×100»

    # Privacy / Cleanup: исходное фото и AI-портрет удаляются, как только карточка собрана
    # или сессия завершилась неудачей/брошена (название сохранено для совместимости .env)
    DELETE_SOURCE_PHOTOS_AFTER_PRINT: bool = True
    
    # Branding
    FESTIVAL_NAME: str = "FUTURE INDUSTRY 2026"
    FESTIVAL_HASHTAG: str = "#ФЕСТИВАЛЬ2026"

    # Access control (S1): пустой токен → случайный при каждом старте (печатается в консоли)
    ACCESS_TOKEN: str = ""
    CAMERA_TOKEN: str = ""
    TRUST_LOOPBACK: bool = True
    ENABLE_API_DOCS: bool = False  # /docs, /redoc, /openapi.json (S9)

    class Config:
        env_file = ".env"
        extra = "allow"

    @model_validator(mode="after")
    def _fill_derived(self):
        if not self.LOCAL_IP:
            self.LOCAL_IP = get_local_ip()
        if not self.BASE_URL:
            self.BASE_URL = f"http://{self.LOCAL_IP}:{self.PORT}"
        self.BASE_URL = self.BASE_URL.rstrip("/")
        if not self.ACCESS_TOKEN:
            self.ACCESS_TOKEN = secrets.token_urlsafe(12)
        if not self.CAMERA_TOKEN or self.CAMERA_TOKEN == self.ACCESS_TOKEN:
            self.CAMERA_TOKEN = secrets.token_urlsafe(9)
        return self

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
settings.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
settings.CARDS_DIR.mkdir(parents=True, exist_ok=True)
settings.FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
