from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.email.service import email_service
from app.session.manager import session_manager
from app.storage.database import db

router = APIRouter(prefix="/api/email", tags=["Email"])


class EmailSendRequest(BaseModel):
    email: str = Field(min_length=5, max_length=128)
    session_id: Optional[str] = None


@router.post("/send", summary="Отправить интерактивный паспорт участника на Email")
async def send_passport_email(payload: EmailSendRequest):
    sess = None
    if payload.session_id:
        sess = db.get_session(payload.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Сессия с указанным идентификатором не найдена")
    else:
        sess = session_manager.get_active_session()
        if not sess or not getattr(sess, "final_card_path", None):
            sess = db.get_last_completed_session(max_age_seconds=1800)
        if not sess:
            raise HTTPException(status_code=400, detail="В данный момент нет доступной сессии для отправки")

    try:
        result = await email_service.send_card_email(payload.email, sess)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
