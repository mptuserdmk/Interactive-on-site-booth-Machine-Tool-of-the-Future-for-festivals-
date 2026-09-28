from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.session.manager import session_manager
from app.session.models import SessionData
from app.storage.database import db

router = APIRouter(prefix="/api/session", tags=["Session"])

class AnswerRequest(BaseModel):
    question_type: Literal["element", "power", "color"]
    answer_id: str = Field(min_length=1, max_length=32)

@router.post("/new", response_model=SessionData, summary="Create a new participant session")
async def create_new_session():
    return await session_manager.new_session()

@router.get("/active", response_model=Optional[SessionData], summary="Get current active session")
async def get_active_session():
    return session_manager.get_active_session()

@router.post("/photo/confirm", summary="Confirm captured photo and proceed to quiz")
async def confirm_photo():
    await session_manager.confirm_photo()
    return {"status": "ok", "session": session_manager.get_active_session()}

@router.post("/photo/retake", summary="Retake photo")
async def retake_photo():
    await session_manager.retake_photo()
    return {"status": "ok", "session": session_manager.get_active_session()}

@router.post("/answer", summary="Submit quiz answer (element, power, or color)")
async def submit_answer(payload: AnswerRequest):
    await session_manager.set_quiz_answer(payload.question_type, payload.answer_id)
    return {"status": "ok", "session": session_manager.get_active_session()}

@router.post("/reset", summary="Reset kiosk to IDLE state")
async def reset_session():
    await session_manager.reset()
    return {"status": "ok"}

@router.get("/history", summary="Get recent session history for operator")
async def get_history(limit: int = Query(30, ge=1, le=200)):
    return db.get_recent_sessions(limit=limit)
