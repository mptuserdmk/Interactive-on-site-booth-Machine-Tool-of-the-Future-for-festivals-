import time
import cv2
import threading
import numpy as np
from pathlib import Path
from typing import Optional, Generator, Tuple
from app.config.settings import settings
from app.camera.models import CameraStatus

class CameraManager:
    def __init__(self):
        self.camera_index = settings.CAMERA_INDEX
        self.cap: Optional[cv2.VideoCapture] = None
        self.lock = threading.RLock()
        self.is_running = False
        self.last_frame: Optional[np.ndarray] = None
        self.last_capture_time = 0
        self.ota_last_photo: Optional[bytes] = None
        # Non-blocking camera init in background thread
        threading.Thread(target=self._init_camera, daemon=True).start()

    def _init_camera(self):
        try:
            # Try to open OpenCV camera with default backend (fast)
            cap = cv2.VideoCapture(self.camera_index)
            if cap and cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
                cap.set(cv2.CAP_PROP_FPS, settings.CAMERA_FPS)
                with self.lock:
                    self.cap = cap
                    self.is_running = True
            else:
                with self.lock:
                    self.is_running = False
        except Exception as e:
            with self.lock:
                self.is_running = False

    def get_status(self) -> CameraStatus:
        available = self.is_running and (self.cap is not None and self.cap.isOpened())
        return CameraStatus(
            is_available=available,
            source_type="usb" if available else "mobile_ota_ready",
            device_index=self.camera_index,
            resolution=f"{settings.CAMERA_WIDTH}x{settings.CAMERA_HEIGHT}",
            fps=settings.CAMERA_FPS,
            error=None if available else "USB camera not connected. Mobile OTA Camera is ready."
        )

    def generate_mock_frame(self, text="FUTURE INDUSTRY CAMERA MOCK") -> np.ndarray:
        """Generates high-tech placeholder frame if no webcam is physically connected."""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Gradient background
        for y in range(720):
            frame[y, :] = [int(15 + y * 0.03), int(20 + y * 0.04), int(30 + y * 0.05)]
        
        # Grid lines
        for x in range(0, 1280, 80):
            cv2.line(frame, (x, 0), (x, 720), (40, 50, 70), 1)
        for y in range(0, 720, 80):
            cv2.line(frame, (0, y), (1280, y), (40, 50, 70), 1)
        
        # Center box & text
        cv2.rectangle(frame, (340, 160), (940, 560), (0, 210, 255), 2)
        cv2.circle(frame, (640, 360), 120, (0, 255, 136), 2)
        cv2.putText(frame, text, (400, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 210, 255), 2)
        cv2.putText(frame, "STAND HERE / TOUCH TO SHOOT", (420, 600), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 255), 1)
        return frame

    def read_frame(self) -> Tuple[bool, np.ndarray]:
        with self.lock:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    if settings.CAMERA_MIRROR:
                        frame = cv2.flip(frame, 1)
                    self.last_frame = frame
                    return True, frame
            
            # Fallback mock frame
            frame = self.generate_mock_frame()
            self.last_frame = frame
            return True, frame

    def capture_usb_snapshot(self, output_path: Path) -> Path:
        """Captures a high-resolution snapshot from USB webcam."""
        with self.lock:
            success, frame = self.read_frame()
            if not success or frame is None:
                frame = self.generate_mock_frame("CAPTURED MOCK PHOTO")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), frame)
            return output_path

    def save_mobile_ota_photo(self, photo_bytes: bytes, output_path: Path) -> Path:
        """Saves a photo sent over WiFi from an iPhone/Android device."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(photo_bytes)
        return output_path

    async def get_mjpeg_stream(self):
        """Yields MJPEG stream asynchronously without blocking FastAPI event loop."""
        import asyncio
        loop = asyncio.get_event_loop()
        while True:
            success, frame = await loop.run_in_executor(None, self.read_frame)
            if not success or frame is None:
                frame = self.generate_mock_frame()
            
            # Compress to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.05)  # 20 FPS, non-blocking

camera_manager = CameraManager()
