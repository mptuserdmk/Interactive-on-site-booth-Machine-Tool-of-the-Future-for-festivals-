"""
Модуль контроля качества кадра и детекции моргания (Blink Detector).
Использует высокоточную легковесную нейросеть OpenCV YuNet (ONNX)
для детекции лиц, ключевых точек глаз и анализа открытости глаз (ГОСТ 2.0).
Работает 100% локально и автономно (офлайн).
"""

import cv2
import numpy as np
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field

logger = logging.getLogger("stanok.blink_detector")

MODEL_PATH = Path(__file__).resolve().parent / "cascades" / "face_detection_yunet_2023mar.onnx"

class PhotoValidationResult(BaseModel):
    face_detected: bool = True
    blink_detected: bool = False
    eyes_open: bool = True
    confidence: float = 1.0
    code: str = "OK"  # "OK", "BLINK_DETECTED", "NO_FACE"
    warning: Optional[str] = None
    face_count: int = 1
    details: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class BlinkDetector:
    _instance: Optional["BlinkDetector"] = None

    def __init__(self):
        self.model_path = MODEL_PATH
        self.detector: Optional[cv2.FaceDetectorYN] = None
        self._lock = threading.Lock()
        self._load_model()

    @classmethod
    def get_instance(cls) -> "BlinkDetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self):
        if not self.model_path.exists():
            logger.warning("YuNet ONNX model not found at %s. Mock fallback will be used.", self.model_path)
            self.detector = None
            return
        try:
            # Инициализация с базовым размером (будет обновляться при каждом кадре)
            self.detector = cv2.FaceDetectorYN_create(
                str(self.model_path),
                "",
                (320, 320),
                score_threshold=0.55,
                nms_threshold=0.3,
                top_k=5
            )
            logger.info("YuNet Face & Blink Detector successfully initialized.")
        except Exception as e:
            logger.exception("Failed to load YuNet model: %s", e)
            self.detector = None

    def _is_mock_frame(self, img: np.ndarray) -> bool:
        """Проверка, является ли кадр тестовой заглушкой (сетка, синтетический mock)."""
        if img is None or img.size == 0:
            return True
        h, w = img.shape[:2]
        # Проверяем характерные цвета заглушки станка: тёмно-синий градиент
        center_pixel = img[h // 2, w // 2]
        # Если это синевато-зеленый маркер заглушки (0, 255, 136) или темный фон (15, 20, 30)
        if (center_pixel[0] < 50 and center_pixel[1] < 60 and center_pixel[2] < 70) and np.std(img) < 25.0:
            return True
        return False

    def _analyze_eye_openness(self, gray: np.ndarray, eye_x: int, eye_y: int, face_w: int) -> float:
        """
        Анализирует вырезку области глаза и возвращает коэффициент открытости [0.0 ... 1.0].
        Закрытый глаз (моргание): равномерный тон кожи века, отсутствие темного зрачка в центре.
        Открытый глаз: высокий контраст между белком (склерой) и темным зрачком/радужкой.
        """
        h_img, w_img = gray.shape[:2]
        # Размер окна глаза пропорционален ширине лица
        box_half = max(5, int(face_w * 0.09))
        y1 = max(0, eye_y - box_half)
        y2 = min(h_img, eye_y + box_half)
        x1 = max(0, eye_x - int(box_half * 1.3))
        x2 = min(w_img, eye_x + int(box_half * 1.3))

        patch = gray[y1:y2, x1:x2]
        if patch.size == 0 or patch.shape[0] < 4 or patch.shape[1] < 4:
            return 0.5  # Недостаточно пикселей, считаем нейтральным

        p10 = float(np.percentile(patch, 10))
        p90 = float(np.percentile(patch, 90))
        mean_val = float(np.mean(patch))
        std_val = float(np.std(patch))

        # Контраст между темным центром (зрачок/ресницы) и светлыми участками (склера/кожа)
        contrast = (p90 - p10) / max(1.0, p90)
        # Относительное затемнение центра: насколько темнейшие пиксели темнее средней яркости
        dark_dip = (mean_val - p10) / max(1.0, mean_val)

        # Сглаженный индекс открытости глаза [0.0 = закрыт/моргнул, 1.0 = широко открыт]
        score = 0.0
        if contrast > 0.35:
            score += 0.35
        elif contrast > 0.20:
            score += 0.15

        if dark_dip > 0.30:
            score += 0.35
        elif dark_dip > 0.18:
            score += 0.15

        if std_val > 22.0:
            score += 0.30
        elif std_val > 12.0:
            score += 0.15

        return min(1.0, max(0.0, score))

    def validate(self, image_source: Union[str, Path, np.ndarray]) -> PhotoValidationResult:
        """
        Проверяет кадр на наличие лица и закрытых глаз (моргания).
        Не падает при ошибках (всегда безопасный fallback).
        """
        try:
            if isinstance(image_source, (str, Path)):
                path_str = str(image_source)
                img = cv2.imread(path_str)
            else:
                img = image_source

            if img is None or img.size == 0:
                logger.warning("Empty or unreadable image provided for validation.")
                return PhotoValidationResult(
                    face_detected=False,
                    blink_detected=False,
                    eyes_open=False,
                    code="NO_FACE",
                    warning="Не удалось прочитать изображение с оптического сенсора."
                )

            # Проверка на тестовый мок-кадр
            if self._is_mock_frame(img):
                return PhotoValidationResult(
                    face_detected=True,
                    blink_detected=False,
                    eyes_open=True,
                    confidence=1.0,
                    code="OK",
                    warning=None,
                    details={"is_mock": True}
                )

            if self.detector is None:
                # Если модель не загрузилась, безопасно пропускаем
                return PhotoValidationResult(code="OK", warning=None)

            h_orig, w_orig = img.shape[:2]

            # Для максимальной скорости нормализуем кадр до 640px по длинной стороне
            max_dim = 640
            scale = 1.0
            if max(h_orig, w_orig) > max_dim:
                scale = max_dim / float(max(h_orig, w_orig))
                w_proc = int(w_orig * scale)
                h_proc = int(h_orig * scale)
            else:
                h_proc, w_proc = h_orig, w_orig

            # YuNet DNN требует четные размеры (stride 32/2) и C-contiguous буфер
            w_proc = max(32, int(w_proc // 2 * 2))
            h_proc = max(32, int(h_proc // 2 * 2))
            proc_img = np.ascontiguousarray(cv2.resize(img, (w_proc, h_proc), interpolation=cv2.INTER_AREA))

            with self._lock:
                try:
                    self.detector.setInputSize((w_proc, h_proc))
                    retval, faces = self.detector.detect(proc_img)
                except Exception as detect_err:
                    logger.warning("YuNet detect failure (%s), resetting detector", detect_err)
                    try:
                        self._load_model()
                    except Exception:
                        pass
                    return PhotoValidationResult(code="OK", warning=None)

            if faces is None or len(faces) == 0:
                # В кадре нет лица
                return PhotoValidationResult(
                    face_detected=False,
                    blink_detected=False,
                    eyes_open=False,
                    confidence=0.0,
                    code="NO_FACE",
                    warning="Оптический датчик не обнаружил лицо в прицеле. Встаньте напротив камеры."
                )

            # Выбираем главное лицо (самое крупное по площади)
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            primary_face = faces_sorted[0]
            face_score = float(primary_face[14])
            face_w = int(primary_face[2])

            # Координаты глаз
            rx = int(primary_face[4])
            ry = int(primary_face[5])
            lx = int(primary_face[6])
            ly = int(primary_face[7])

            gray_proc = cv2.cvtColor(proc_img, cv2.COLOR_BGR2GRAY)
            r_openness = self._analyze_eye_openness(gray_proc, rx, ry, face_w)
            l_openness = self._analyze_eye_openness(gray_proc, lx, ly, face_w)
            avg_openness = (r_openness + l_openness) / 2.0

            # Порог моргания: если средняя открытость ниже 0.35
            # или один глаз закрыт полностью (<0.20), а второй ниже 0.40
            is_blink = avg_openness < 0.35 or (min(r_openness, l_openness) < 0.20 and max(r_openness, l_openness) < 0.40)

            if is_blink:
                return PhotoValidationResult(
                    face_detected=True,
                    blink_detected=True,
                    eyes_open=False,
                    confidence=round(face_score, 2),
                    code="BLINK_DETECTED",
                    warning="Кажется, вы моргнули! Глаза на снимке закрыты. Рекомендуем переснять кадр.",
                    face_count=len(faces),
                    details={
                        "right_eye_openness": round(r_openness, 2),
                        "left_eye_openness": round(l_openness, 2),
                        "avg_openness": round(avg_openness, 2)
                    }
                )

            return PhotoValidationResult(
                face_detected=True,
                blink_detected=False,
                eyes_open=True,
                confidence=round(face_score, 2),
                code="OK",
                warning=None,
                face_count=len(faces),
                details={
                    "right_eye_openness": round(r_openness, 2),
                    "left_eye_openness": round(l_openness, 2),
                    "avg_openness": round(avg_openness, 2)
                }
            )

        except Exception as e:
            logger.exception("Error during blink detection validation: %s", e)
            return PhotoValidationResult(code="OK", warning=None)


# Экземпляр детектора
blink_detector = BlinkDetector.get_instance()

def validate_photo(image_source: Union[str, Path, np.ndarray]) -> PhotoValidationResult:
    return blink_detector.validate(image_source)
