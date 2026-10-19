import pytest
import numpy as np
from pathlib import Path
from app.camera.blink_detector import BlinkDetector, validate_photo, PhotoValidationResult


def test_blink_detector_mock_frame():
    detector = BlinkDetector.get_instance()
    # Synthetic mock frame
    mock_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    res = detector.validate(mock_frame)
    assert isinstance(res, PhotoValidationResult)
    assert res.code == "OK"
    assert res.details.get("is_mock") is True


def test_blink_detector_non_standard_dimensions():
    detector = BlinkDetector.get_instance()
    # Create arbitrary non-standard odd resolution image
    odd_image = np.ones((533, 719, 3), dtype=np.uint8) * 120
    # Must not raise (-215:Assertion failed) buf.shape() == m.shape()
    res = detector.validate(odd_image)
    assert isinstance(res, PhotoValidationResult)


def test_validate_photo_helper():
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)
    res = validate_photo(dummy)
    assert isinstance(res, PhotoValidationResult)
