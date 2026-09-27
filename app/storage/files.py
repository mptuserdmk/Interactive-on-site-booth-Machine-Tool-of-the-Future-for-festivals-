import os
import shutil
from pathlib import Path
from typing import Optional
from app.config.settings import settings

def save_uploaded_bytes(data: bytes, dest_path: Path) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(data)
    return dest_path

def delete_file_safely(file_path: Optional[str]) -> bool:
    if not file_path:
        return False
    try:
        p = Path(file_path)
        if p.exists() and p.is_file():
            p.unlink()
            return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
    return False

def clean_session_source_photo(session_id: str, photo_path: Optional[str]):
    """Privacy cleanup: Removes raw participant photo if configured."""
    if settings.DELETE_SOURCE_PHOTOS_AFTER_PRINT and photo_path:
        delete_file_safely(photo_path)
