from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.config.settings import settings
from app.session.manager import session_manager
from app.printing.manager import print_manager

router = APIRouter(prefix="/api/print", tags=["Printing"])

class ReprintRequest(BaseModel):
    session_id: str = Field(max_length=128)

class ToggleAutoPrintRequest(BaseModel):
    enabled: bool

@router.get("/status", summary="Get printer status and available devices")
async def get_print_status():
    status = print_manager.get_status()
    if isinstance(status, dict):
        status["enable_auto_print"] = settings.ENABLE_AUTO_PRINT
    return status

@router.post("/toggle-auto-print", summary="Toggle auto-print mode")
async def toggle_auto_print(payload: ToggleAutoPrintRequest):
    settings.ENABLE_AUTO_PRINT = payload.enabled
    return {
        "status": "ok",
        "enable_auto_print": settings.ENABLE_AUTO_PRINT
    }

@router.post("/trigger-active", summary="Trigger print for the active session")
async def trigger_active_print():
    await session_manager.trigger_print()
    return {"status": "ok"}

@router.post("/reprint", summary="Reprint a previous card without regenerating with AI")
async def reprint_card(payload: ReprintRequest):
    result = await session_manager.reprint_session(payload.session_id)
    return result

