"""
Рендер карточек «до / после» фикса композиции для отчёта (docs/evidence/cards/).
Версия «до» берётся из git HEAD (app/composition/composer.py) без изменения рабочего дерева.

    python tests/tools/render_cards_before_after.py 41 31 70
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
tmp = Path(tempfile.mkdtemp(prefix="stanok_render_"))
os.environ.update({"STORAGE_DIR": str(tmp / "s"), "PHOTOS_DIR": str(tmp / "s/p"), "GENERATED_DIR": str(tmp / "s/g"),
                   "CARDS_DIR": str(tmp / "s/c"), "FALLBACK_DIR": str(tmp / "f"), "DB_PATH": str(tmp / "k.db"),
                   "PRINT_SIMULATION_MODE": "true", "CAMERA_INDEX": "99", "BASE_URL": "http://192.168.1.38:8000"})
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402
from app.composition.composer import CardComposer  # noqa: E402
from app.quiz.combinations import combination_manager  # noqa: E402


def old_composer():
    src = subprocess.run(["git", "show", "HEAD:app/composition/composer.py"], cwd=ROOT, capture_output=True,
                         check=True).stdout.decode("utf-8")
    path = tmp / "composer_before.py"
    path.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("composer_before", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CardComposer()


def portrait():
    p = tmp / "portrait.jpg"
    img = Image.new("RGB", (768, 1024), (60, 80, 120))
    d = ImageDraw.Draw(img)
    d.ellipse([234, 180, 534, 560], fill=(220, 190, 170))
    d.rectangle([180, 600, 588, 1024], fill=(40, 120, 200))
    img.save(p, "JPEG")
    return p


def main(ids):
    out_dir = ROOT / "docs" / "evidence" / "cards"
    out_dir.mkdir(parents=True, exist_ok=True)
    before, after, photo = old_composer(), CardComposer(), portrait()
    sid = "sess_20260928120000_ab12"
    for cid in ids:
        combo = combination_manager.get_by_id(cid)
        a, b = tmp / f"before_{cid}.jpg", tmp / f"after_{cid}.jpg"
        before.compose_card(sid, photo, combo, a)
        after.compose_card(sid, photo, combo, b)
        ia, ib = Image.open(a), Image.open(b)
        pair = Image.new("RGB", (1200 * 2 + 40, 1800), "white")
        pair.paste(ia, (0, 0))
        pair.paste(ib, (1240, 0))
        pair = pair.resize((pair.width // 3, pair.height // 3), Image.Resampling.LANCZOS)
        target = out_dir / f"combo_{cid:03d}_before_after.jpg"
        pair.save(target, "JPEG", quality=88)
        print(target.relative_to(ROOT), "—", combo["machine_name"], "/", combo["location"])


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [41, 31])
