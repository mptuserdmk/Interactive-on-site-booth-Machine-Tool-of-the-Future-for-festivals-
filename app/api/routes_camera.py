from fastapi import APIRouter, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from pathlib import Path
from datetime import datetime
from app.config.settings import settings
from app.camera.manager import camera_manager
from app.session.manager import session_manager

router = APIRouter(prefix="/api/camera", tags=["Camera"])

@router.get("/status", summary="Get USB and mobile camera status")
async def get_camera_status():
    return camera_manager.get_status()

@router.get("/stream", summary="Live MJPEG video stream from camera")
async def stream_camera():
    return StreamingResponse(
        camera_manager.get_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/capture", summary="Capture snapshot from USB webcam")
async def capture_usb_snapshot():
    sess = session_manager.get_active_session()
    if not sess:
        sess = session_manager.create_session()
        
    out_path = settings.PHOTOS_DIR / f"{sess.id}_raw.jpg"
    camera_manager.capture_usb_snapshot(out_path)
    await session_manager.attach_photo(out_path)
    return {
        "status": "ok",
        "session_id": sess.id,
        "photo_url": f"/storage/photos/{out_path.name}"
    }

@router.post("/upload-ota", summary="Over-the-air photo upload from iPhone/Android")
async def upload_ota_photo(file: UploadFile = File(...)):
    sess = session_manager.get_active_session()
    if not sess:
        sess = session_manager.create_session()
        
    out_path = settings.PHOTOS_DIR / f"{sess.id}_raw.jpg"
    contents = await file.read()
    camera_manager.save_mobile_ota_photo(contents, out_path)
    await session_manager.attach_photo(out_path)
    return {
        "status": "ok",
        "session_id": sess.id,
        "photo_url": f"/storage/photos/{out_path.name}",
        "message": "Photo uploaded from mobile camera successfully"
    }
