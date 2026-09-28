"""
Модульные проверки комбинаций, композиции и mock AI (бывший скрипт, переведён на pytest).
Раньше писал в боевые storage/photos и storage/cards по относительным путям (T1) —
теперь только в tmp_path.
"""
from pathlib import Path

import pytest

from helpers import write_photo

pytestmark = pytest.mark.unit


def test_combinations():
    from app.quiz.combinations import combination_manager
    combos = combination_manager.get_all()
    assert len(combos) == 100
    c1 = combination_manager.find("space", "precision", "azure")
    assert c1 is not None
    assert c1["machine_name"] == "Космический Токарь-Оптик"


def test_card_composition(tmp_path):
    from app.composition.composer import card_composer
    from app.quiz.combinations import combination_manager
    from PIL import Image

    combo = combination_manager.find("space", "precision", "azure")
    test_img = write_photo(tmp_path / "test_portrait.jpg")
    out_card = tmp_path / "test_card.jpg"
    card_composer.compose_card("test_sess_001", test_img, combo, out_card)
    assert out_card.exists()
    with Image.open(out_card) as im:
        assert im.size == (1200, 1800)


async def test_mock_ai(tmp_path, fast_mock_ai):
    from app.ai.manager import ai_manager
    from app.ai.models import AIGenerationRequest
    from app.quiz.combinations import combination_manager

    combo = combination_manager.find("robots", "mind", "emerald")
    test_img = write_photo(tmp_path / "test_portrait.jpg")
    gen_out = tmp_path / "test_ai.jpg"
    req = AIGenerationRequest(
        session_id="test_sess_002", element="robots", power="mind", color="emerald",
        prompt="Test Prompt", input_photo_path=str(test_img),
    )
    res = await ai_manager.generate_image(req, combo, gen_out)
    assert res.success
    assert Path(res.image_path).exists()
    assert res.is_fallback is False
