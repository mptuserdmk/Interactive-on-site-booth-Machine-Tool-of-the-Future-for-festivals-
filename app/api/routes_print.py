from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.session.manager import session_manager
from app.printing.manager import print_manager

router = APIRouter(prefix="/api/print", tags=["Printing"])

class ReprintRequest(BaseModel):
    session_id: str

@router.get("/status", summary="Get printer status and available devices")
async def get_print_status():
    return print_manager.get_status()

@router.post("/trigger-active", summary="Trigger print for the active session")
async def trigger_active_print():
    await session_manager.trigger_print()
    return {"status": "ok"}

@router.post("/reprint", summary="Reprint a previous card without regenerating with AI")
async def reprint_card(payload: ReprintRequest):
    result = await session_manager.reprint_session(payload.session_id)
    return result
