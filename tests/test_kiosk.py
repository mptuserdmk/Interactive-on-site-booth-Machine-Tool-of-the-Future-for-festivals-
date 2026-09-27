import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
from app.quiz.combinations import combination_manager
from app.composition.composer import card_composer
from app.storage.database import db
from app.ai.manager import ai_manager
from app.ai.models import AIGenerationRequest

def test_combinations():
    combos = combination_manager.get_all()
    assert len(combos) == 100, f"Expected 100 combinations, got {len(combos)}"
    
    # Check space + precision + azure
    c1 = combination_manager.find("space", "precision", "azure")
    assert c1 is not None
    assert c1["machine_name"] == "Космический Токарь-Оптик"
    print("✅ Combinations test passed (100 total)")

async def test_card_composition():
    combo = combination_manager.find("space", "precision", "azure")
    test_img = Path("storage/photos/test_portrait.jpg")
    
    # Create sample portrait
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (600, 800), (30, 45, 70))
    d = ImageDraw.Draw(img)
    d.rectangle([150, 200, 450, 600], fill=(70, 95, 140))
    d.text((200, 380), "SAMPLE STUDENT", fill="#ffffff")
    test_img.parent.mkdir(parents=True, exist_ok=True)
    img.save(test_img)

    out_card = Path("storage/cards/test_card.jpg")
    card_composer.compose_card("test_sess_001", test_img, combo, out_card)
    assert out_card.exists()
    print(f"✅ Card composition test passed (Created {out_card})")

async def test_mock_ai():
    combo = combination_manager.find("robots", "mind", "emerald")
    test_img = Path("storage/photos/test_portrait.jpg")
    gen_out = Path("storage/generated/test_ai.jpg")
    
    req = AIGenerationRequest(
        session_id="test_sess_002",
        element="robots",
        power="mind",
        color="emerald",
        prompt="Test Prompt",
        input_photo_path=str(test_img)
    )
    res = await ai_manager.generate_image(req, combo, gen_out)
    assert res.success
    assert Path(res.image_path).exists()
    print(f"✅ AI Generation test passed (duration: {res.duration_seconds}s)")

if __name__ == "__main__":
    test_combinations()
    asyncio.run(test_card_composition())
    asyncio.run(test_mock_ai())
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
