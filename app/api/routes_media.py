"""
Раздача изображений вместо публичного StaticFiles на /storage (S2):
  /media/cards/{id}.jpg  — готовая карточка, публично (id сессии неугадываемый — 128 бит);
  /media/photos/{id}.jpg — сырое фото ребёнка, только для активной сессии и только доверенному
                           клиенту (киоск/оператор; проверка в AccessControlMiddleware).
"""
import io
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from app.config.settings import settings
from app.composition.qr import generate_qr_code
from app.storage.database import db
from app.session.manager import session_manager

router = APIRouter(tags=["Media"])

SESSION_ID_RE = re.compile(r"^sess_[A-Za-z0-9_]{1,64}$")
NO_CACHE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


def _safe_file(path_str, base_dir) -> Path:
    if not path_str:
        raise HTTPException(status_code=404)
    p = Path(path_str).resolve()
    if not p.is_file() or not p.is_relative_to(Path(base_dir).resolve()):
        raise HTTPException(status_code=404)
    return p


@router.get("/media/cards/{session_id}.jpg", summary="Card image (public, by unguessable session id)")
async def card_image(session_id: str):
    if not SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=404)
    sess = db.get_session(session_id)
    path = _safe_file(sess and sess.get("final_card_path"), settings.CARDS_DIR)
    return FileResponse(path, media_type="image/jpeg",
                        headers={"Cache-Control": "private, max-age=600", "X-Content-Type-Options": "nosniff"})


@router.get("/api/qr.png", summary="QR code for the operator panel (generated locally)")
async def qr_png(data: str = Query(..., min_length=1, max_length=512)):
    # Раньше панель оператора отдавала URL стенда (а теперь и токен камеры) стороннему api.qrserver.com (S10)
    img = generate_qr_code(data, size=300)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return Response(buf.getvalue(), media_type="image/png", headers=NO_CACHE)


@router.get("/media/photos/{session_id}.jpg", summary="Raw photo of the active session (kiosk review only)")
async def raw_photo(session_id: str):
    sess = session_manager.get_active_session()
    if not sess or sess.id != session_id:
        raise HTTPException(status_code=404)
    path = _safe_file(sess.photo_path, settings.PHOTOS_DIR)
    return FileResponse(path, media_type="image/jpeg", headers=NO_CACHE)
