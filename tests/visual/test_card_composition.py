"""
Композиция карточки (H16, H17, QR, DPI) по всем 100 комбинациям и разным входным фото.

Границы текста проверяются white-box: перехватываем ImageDraw.text и считаем textbbox каждого вызова —
это работает и до, и после фикса, не требуя инструментирования прод-кода.
"""
from functools import lru_cache

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw

from helpers import make_photo_bytes, write_photo

pytestmark = pytest.mark.visual

CARD_W, CARD_H = 1200, 1800
INNER = (45, 45, CARD_W - 45, CARD_H - 45)          # внутренняя рамка карточки (линия на 40 px)
PHOTO_BOX = (70, 175, CARD_W - 70, 975)
QR_BOX = (CARD_W - 70 - 220 - 10, CARD_H - 70 - 260 - 10, CARD_W - 70 + 10, CARD_H - 70 - 260 + 230)
ALL_COMBOS = list(range(1, 101))


def _intersects(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _inside(a, box):
    return a[0] >= box[0] and a[1] >= box[1] and a[2] <= box[2] and a[3] <= box[3]


@lru_cache(maxsize=4096)
def _glyph(font, ch):
    im = Image.new("L", (160, 160), 0)
    ImageDraw.Draw(im).text((20, 20), ch, font=font, fill=255)
    return im.tobytes()


def missing_glyphs(text, font):
    if not hasattr(font, "getbbox") or not hasattr(font, "path"):
        return []
    notdef = _glyph(font, "\U000F0000")
    return sorted({ch for ch in text if not ch.isspace() and _glyph(font, ch) == notdef})


@pytest.fixture
def text_recorder(monkeypatch):
    records = []
    orig = ImageDraw.ImageDraw.text

    def rec(self, xy, text, *args, **kwargs):
        font = kwargs.get("font") if "font" in kwargs else (args[1] if len(args) > 1 else None)
        if self.im is not None and self.im.size == (CARD_W, CARD_H):
            records.append((str(text), self.textbbox(xy, text, font=font), font))
        return orig(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", rec)
    return records


@pytest.fixture(scope="module")
def portrait_path(tmp_path_factory):
    return write_photo(tmp_path_factory.mktemp("in") / "ai.jpg", size=(768, 1024))


def compose(combo_id, ai_path, out_path, session_id="sess_0123456789abcdef0123456789abcdef"):
    from app.composition.composer import card_composer
    from app.quiz.combinations import combination_manager
    combo = combination_manager.get_by_id(combo_id)
    card_composer.compose_card(session_id=session_id, ai_image_path=ai_path, combo=combo, output_path=out_path)
    return combo


def decode_qr(card: Image.Image):
    """Как камера телефона: несколько вырезок/масштабов, первый успешный результат.
    (Детектор OpenCV нестабилен на отдельных сочетаниях отступа и масштаба.)"""
    x0, y0, x1, y1 = QR_BOX
    full = cv2.cvtColor(np.array(card.convert("RGB")), cv2.COLOR_RGB2BGR)
    for margin in (10, 40, 20, 0):
        crop = full[y0 - margin:y1 + margin, x0 - margin:x1 + margin]
        for scale in (1, 2, 3):
            arr = crop if scale == 1 else cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            data, _, _ = cv2.QRCodeDetector().detectAndDecode(arr)
            if data:
                return data
    return ""


@pytest.mark.regression
@pytest.mark.parametrize("combo_id", ALL_COMBOS)
def test_card_layout_all_combinations(combo_id, portrait_path, tmp_path, text_recorder):
    """H17: весь текст внутри рамки, не залезает на QR/фото, нет «квадратиков» вместо символов."""
    out = tmp_path / "card.jpg"
    combo = compose(combo_id, portrait_path, out)
    with Image.open(out) as im:
        assert im.size == (CARD_W, CARD_H)
    problems = []
    for text, bbox, font in text_recorder:
        if not _inside(bbox, INNER):
            problems.append(f"вне рамки {bbox}: {text!r}")
        if _intersects(bbox, QR_BOX) and "digital" not in text:
            problems.append(f"на QR {bbox}: {text!r}")
        if text.startswith("СТИХИЯ:"):
            badge = (PHOTO_BOX[0] + 25, PHOTO_BOX[3] - 70, PHOTO_BOX[0] + 360, PHOTO_BOX[3] - 20)
            if not _inside(bbox, badge):
                problems.append(f"вылезает из плашки {badge} → {bbox}: {text!r}")
        elif _intersects(bbox, PHOTO_BOX):
            problems.append(f"на фото {bbox}: {text!r}")
        miss = missing_glyphs(text, font)
        if miss:
            problems.append(f"нет глифов {miss} в шрифте {getattr(font, 'path', '?')}: {text!r}")
    for i, (t1, b1, _) in enumerate(text_recorder):
        for t2, b2, _ in text_recorder[i + 1:]:
            if _intersects(b1, b2):
                problems.append(f"текст наезжает на текст: {t1!r} × {t2!r}")
    assert not problems, f"комбинация #{combo_id} «{combo['machine_name']}»:\n  " + "\n  ".join(problems)


@pytest.mark.parametrize("combo_id", [1, 38, 50, 72, 100])
def test_qr_decodes_to_card_url(combo_id, portrait_path, tmp_path):
    from app.composition.qr import get_digital_card_url
    sid = "sess_0123456789abcdef0123456789abcdef"
    out = tmp_path / "card.jpg"
    compose(combo_id, portrait_path, out, session_id=sid)
    with Image.open(out) as card:
        assert decode_qr(card) == get_digital_card_url(sid)


@pytest.mark.regression
def test_card_has_300_dpi_metadata(portrait_path, tmp_path):
    """Новая находка: README обещает 300 DPI, а JPEG сохраняется без плотности → драйвер
    печатает в масштабе по умолчанию (72/96 DPI) или обрезает."""
    out = tmp_path / "card.jpg"
    compose(1, portrait_path, out)
    with Image.open(out) as im:
        dpi = im.info.get("dpi")
    assert dpi is not None and round(dpi[0]) == 300 and round(dpi[1]) == 300, f"dpi={dpi}"


@pytest.mark.regression
def test_card_shows_distinct_session_code(portrait_path, tmp_path, text_recorder):
    """Новая находка: на карточке печатается session_id[:8] → у всех «SESS_202…», оператор не может
    сопоставить карточку с историей."""
    ids = []
    for sid in ("sess_20260928120000_ab12", "sess_20260928120001_cd34"):
        text_recorder.clear()
        compose(1, portrait_path, tmp_path / f"{sid}.jpg", session_id=sid)
        ids.append(next(t for t, _, _ in text_recorder if "ID:" in t))
    assert ids[0] != ids[1], ids


PHOTO_VARIANTS = {
    "portrait": dict(size=(768, 1024)),
    "landscape": dict(size=(1600, 900)),
    "square": dict(size=(1024, 1024)),
    "tiny_1px": dict(size=(1, 1)),
    "panorama": dict(size=(4000, 300)),
    "big_12mp": dict(size=(4000, 3000)),
    "png_alpha": dict(size=(800, 800), mode="RGBA", fmt="PNG"),
    "cmyk_jpeg": dict(size=(800, 1000), mode="CMYK"),
    "exif_rot6": dict(size=(800, 600), exif_orientation=6),
}


@pytest.mark.parametrize("variant", list(PHOTO_VARIANTS))
def test_compose_photo_variants(variant, tmp_path):
    ext = "png" if PHOTO_VARIANTS[variant].get("fmt") == "PNG" else "jpg"
    src = tmp_path / f"in.{ext}"
    src.write_bytes(make_photo_bytes(**PHOTO_VARIANTS[variant]))
    out = tmp_path / "card.jpg"
    compose(1, src, out)
    with Image.open(out) as im:
        assert im.size == (CARD_W, CARD_H)
        assert im.mode == "RGB"


def _region_mean(img, box):
    return float(np.asarray(img.crop(box).convert("L")).mean())


@pytest.mark.regression
async def test_iphone_exif_orientation_respected_on_card(client, fast_pipeline):
    """H16: фото из галереи iPhone (данные «боком» + EXIF Orientation=6) печатается повернутым."""
    import io
    from helpers import db_state, wait_for_status
    # правильный портрет: светлое «лицо» сверху по центру
    portrait = Image.open(io.BytesIO(make_photo_bytes(size=(600, 800))))
    sensor = portrait.rotate(90, expand=True)  # так iPhone хранит пиксели
    exif = Image.Exif()
    exif[0x0112] = 6
    buf = io.BytesIO()
    sensor.save(buf, "JPEG", exif=exif.tobytes())

    r = await client.post("/api/session/new")
    sid = r.json()["id"]
    r = await client.post("/api/camera/upload-ota", files={"file": ("IMG_0001.jpg", buf.getvalue(), "image/jpeg")})
    assert r.status_code == 200, r.text
    await client.post("/api/session/photo/confirm")
    for qt, aid in (("element", "space"), ("power", "precision"), ("color", "white")):
        await client.post("/api/session/answer", json={"question_type": qt, "answer_id": aid})
    done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=15)
    assert done["status"] == "COMPLETED", done["error_message"]
    with Image.open(done["final_card_path"]) as card:
        top_center = _region_mean(card, (450, 180, 750, 320))
        left_middle = _region_mean(card, (120, 450, 330, 750))
    assert top_center > left_middle, (
        f"лицо не сверху: яркость верх-центр={top_center:.0f}, лево-середина={left_middle:.0f} → фото повернуто")
