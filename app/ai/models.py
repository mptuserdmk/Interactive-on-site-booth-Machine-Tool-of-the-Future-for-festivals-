from pydantic import BaseModel
from typing import Optional, Dict, Any

class AIGenerationRequest(BaseModel):
    session_id: str
    element: str
    power: str
    color: str
    prompt: str
    negative_prompt: Optional[str] = None
    input_photo_path: str

class AIGenerationResult(BaseModel):
    success: bool
    image_path: Optional[str] = None
    provider_name: str
    duration_seconds: float
    error: Optional[str] = None
    is_fallback: bool = False
