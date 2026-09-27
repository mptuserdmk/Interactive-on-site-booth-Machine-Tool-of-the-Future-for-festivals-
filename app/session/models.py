from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class SessionState(str, Enum):
    IDLE = "IDLE"
    PHOTO_PENDING = "PHOTO_PENDING"
    PHOTO_TAKEN = "PHOTO_TAKEN"
    PHOTO_CONFIRMED = "PHOTO_CONFIRMED"
    QUIZ_ELEMENT = "QUIZ_ELEMENT"
    QUIZ_POWER = "QUIZ_POWER"
    QUIZ_COLOR = "QUIZ_COLOR"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    COMPOSING = "COMPOSING"
    READY_TO_PRINT = "READY_TO_PRINT"
    PRINTING = "PRINTING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class SessionData(BaseModel):
    id: str
    created_at: str
    status: SessionState = SessionState.IDLE
    element: Optional[str] = None
    element_name: Optional[str] = None
    power: Optional[str] = None
    power_name: Optional[str] = None
    color: Optional[str] = None
    color_name: Optional[str] = None
    combination_id: Optional[int] = None
    machine_name: Optional[str] = None
    machine_desc: Optional[str] = None
    location: Optional[str] = None
    photo_path: Optional[str] = None
    generated_image_path: Optional[str] = None
    final_card_path: Optional[str] = None
    print_status: str = "pending"
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
