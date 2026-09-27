from pydantic import BaseModel
from typing import Optional

class CameraStatus(BaseModel):
    is_available: bool
    source_type: str  # 'usb', 'mobile_ota', 'mock'
    device_index: int
    resolution: str
    fps: int
    error: Optional[str] = None
