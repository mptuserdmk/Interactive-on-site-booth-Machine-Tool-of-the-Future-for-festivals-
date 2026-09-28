import time
import asyncio
import threading
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from app.config.settings import settings
from app.camera.models import CameraStatus


class CameraUnavailable(Exception):
    pass


class CameraManager:
    FRAME_INTERVAL = 0.05  # 20 FPS
    REOPEN_INTERVAL = 2.0

    def __init__(self):
        self.camera_index = settings.CAMERA_INDEX
        self.cap: Optional[cv2.VideoCapture] = None
        self.lock = threading.RLock()
        self.is_running = False
        self.last_frame: Optional[np.ndarray] = None
        self.last_capture_time = 0
        self.ota_last_photo: Optional[bytes] = None
        self._fail_count = 0
        self._last_reopen = 0.0
        self._mock_frames = {}
        # Один общий JPEG на всех зрителей MJPEG: CPU не растёт с числом клиентов (H14)
        self._jpeg_lock = threading.Lock()
        self._jpeg_cache: Tuple[float, bytes] = (0.0, b"")
        # Non-blocking camera init in background thread
        threading.Thread(target=self._init_camera, daemon=True).start()

    def _open(self) -> bool:
        cap = cv2.VideoCapture(self.camera_index)
        if cap and cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, settings.CAMERA_FPS)
            with self.lock:
                self.cap = cap
                self.is_running = True
                self._fail_count = 0
            return True
        return False

    def _init_camera(self):
        try:
            if not self._open():
                with self.lock:
                    self.is_running = False
        except Exception:
            with self.lock:
                self.is_running = False

    def _reopen(self) -> bool:
        """USB-камеру выдернули и вставили обратно — подхватываем без перезапуска стенда."""
        now = time.monotonic()
        if now - self._last_reopen < self.REOPEN_INTERVAL and self._last_reopen:
            return False
        self._last_reopen = now
        with self.lock:
            old, self.cap = self.cap, None
        if old is not None:
            try:
                old.release()
            except Exception:
                pass
        try:
            return self._open()
        except Exception:
            return False

    def get_status(self) -> CameraStatus:
        available = self.is_running and (self.cap is not None and self.cap.isOpened()) and self._fail_count == 0
        return CameraStatus(
            is_available=available,
            source_type="usb" if available else "mobile_ota_ready",
            device_index=self.camera_index,
            resolution=f"{settings.CAMERA_WIDTH}x{settings.CAMERA_HEIGHT}",
            fps=settings.CAMERA_FPS,
            error=None if available else "USB camera not connected. Mobile OTA Camera is ready."
        )

    def generate_mock_frame(self, text="FUTURE INDUSTRY CAMERA MOCK") -> np.ndarray:
        """Generates high-tech placeholder frame if no webcam is physically connected.
        Кадр кэшируется: раньше Python-цикл по 720 строкам выполнялся на каждый кадр каждого клиента (H14)."""
        cached = self._mock_frames.get(text)
        if cached is not None:
            return cached
        y = np.arange(720, dtype=np.float32)[:, None]
        gradient = np.stack([15 + y * 0.03, 20 + y * 0.04, 30 + y * 0.05], axis=-1).astype(np.uint8)
        frame = np.ascontiguousarray(np.broadcast_to(gradient, (720, 1280, 3)))

        # Grid lines
        for x in range(0, 1280, 80):
            cv2.line(frame, (x, 0), (x, 720), (40, 50, 70), 1)
        for y_line in range(0, 720, 80):
            cv2.line(frame, (0, y_line), (1280, y_line), (40, 50, 70), 1)

        # Center box & text
        cv2.rectangle(frame, (340, 160), (940, 560), (0, 210, 255), 2)
        cv2.circle(frame, (640, 360), 120, (0, 255, 136), 2)
        cv2.putText(frame, text, (400, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 210, 255), 2)
        cv2.putText(frame, "STAND HERE / TOUCH TO SHOOT", (420, 600), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 255), 1)
        frame.setflags(write=False)
        self._mock_frames[text] = frame
        return frame

    def _read_camera(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self.lock:
            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self._fail_count = 0
                    if settings.CAMERA_MIRROR:
                        frame = cv2.flip(frame, 1)
                    self.last_frame = frame
                    return True, frame
                self._fail_count += 1
        return False, None

    def read_frame(self) -> Tuple[bool, np.ndarray]:
        ok, frame = self._read_camera()
        if ok:
            return True, frame
        if self.cap is not None:
            self._reopen()
            return True, self.generate_mock_frame("CAMERA NOT RESPONDING")
        # Fallback mock frame
        return True, self.generate_mock_frame()

    def capture_usb_snapshot(self, output_path: Path) -> Path:
        """Captures a high-resolution snapshot from USB webcam.
        Если камера была, но перестала отдавать кадры, — 503, а не заглушка вместо фото ребёнка."""
        with self.lock:
            ok, frame = self._read_camera()
            if not ok and self.cap is not None and self._reopen():
                ok, frame = self._read_camera()
            if not ok:
                if self.cap is None and settings.CAMERA_MOCK_FALLBACK:
                    frame = self.generate_mock_frame("CAPTURED MOCK PHOTO")
                else:
                    raise CameraUnavailable("USB-камера не отвечает: переподключите её или снимайте телефоном")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), frame)
            return output_path

    def save_mobile_ota_photo(self, photo_bytes: bytes, output_path: Path) -> Path:
        """Saves a photo sent over WiFi from an iPhone/Android device."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(photo_bytes)
        return output_path

    def _latest_jpeg(self) -> bytes:
        with self._jpeg_lock:
            ts, data = self._jpeg_cache
            now = time.monotonic()
            if data and now - ts < self.FRAME_INTERVAL * 0.9:
                return data
            success, frame = self.read_frame()
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                self._jpeg_cache = (now, buffer.tobytes())
            return self._jpeg_cache[1]

    async def get_mjpeg_stream(self):
        """Yields MJPEG stream asynchronously without blocking FastAPI event loop."""
        next_tick = time.monotonic()
        while True:
            frame_bytes = await asyncio.to_thread(self._latest_jpeg)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            next_tick += self.FRAME_INTERVAL
            await asyncio.sleep(max(0.0, next_tick - time.monotonic()))  # ровные 20 FPS

camera_manager = CameraManager()
