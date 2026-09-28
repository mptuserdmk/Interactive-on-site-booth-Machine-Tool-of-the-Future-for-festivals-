import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.config.settings import settings
from app.camera.image_io import normalize_photo, max_upload_bytes, UploadRejected
from app.camera.manager import camera_manager, CameraUnavailable
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
    sess = session_manager.begin_photo()
    out_path = settings.PHOTOS_DIR / f"{sess.id}_raw.jpg"
    # OpenCV-захват и запись файла блокируют — в пул потоков (H13)
    try:
        await asyncio.to_thread(camera_manager.capture_usb_snapshot, out_path)
    except CameraUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    await session_manager.attach_photo(sess.id, out_path)
    return {
        "status": "ok",
        "session_id": sess.id,
        "photo_url": f"/media/photos/{sess.id}.jpg"
    }

@router.post("/upload-ota", summary="Over-the-air photo upload from iPhone/Android")
async def upload_ota_photo(file: UploadFile = File(...)):
    # Сначала проверка и нормализация (S4, H16), потом сессия: мусор не создаёт PHOTO_TAKEN
    contents = await file.read(max_upload_bytes() + 1)
    try:
        jpeg, _size = await asyncio.to_thread(normalize_photo, contents)
    except UploadRejected as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e
    sess = session_manager.begin_photo()
    out_path = settings.PHOTOS_DIR / f"{sess.id}_raw.jpg"
    await asyncio.to_thread(camera_manager.save_mobile_ota_photo, jpeg, out_path)
    await session_manager.attach_photo(sess.id, out_path)
    return {
        "status": "ok",
        "session_id": sess.id,
        "photo_url": f"/media/photos/{sess.id}.jpg",
        "message": "Photo uploaded from mobile camera successfully"
    }
