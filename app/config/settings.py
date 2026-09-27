import os
import socket
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_local_ip() -> str:
    """Find the local network IP so iPhones/tablets on same WiFi can connect easily."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Doesn't actually make connection, just determines routing
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class Settings(BaseSettings):
    # App info
    APP_NAME: str = "AI-Фотолокация «Станок Будущего»"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOCAL_IP: str = get_local_ip()
    BASE_URL: str = f"http://{LOCAL_IP}:{8000}"
    
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
    
    # AI Provider: 'mock', 'fal', 'replicate', 'openai', 'stability'
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = ""
    AI_TIMEOUT_SECONDS: int = 25
    AI_FALLBACK_ON_ERROR: bool = True
    
    # Printer
    PRINTER_NAME: str = ""  # Empty string = default Windows printer
    ENABLE_AUTO_PRINT: bool = True
    PRINT_SIMULATION_MODE: bool = False  # If True, simulates print without sending to physical hardware
    
    # Privacy / Cleanup
    DELETE_SOURCE_PHOTOS_AFTER_PRINT: bool = True
    
    # Branding
    FESTIVAL_NAME: str = "FUTURE INDUSTRY 2026"
    FESTIVAL_HASHTAG: str = "#ФЕСТИВАЛЬ2026"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
settings.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
settings.CARDS_DIR.mkdir(parents=True, exist_ok=True)
settings.FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
