"""
История сессий (H4) и жизненный цикл персональных данных — фото детей (H15, 152-ФЗ).
"""
from pathlib import Path

import pytest

from helpers import db_state, do, drive_to, wait_for_status

pytestmark = [pytest.mark.integration, pytest.mark.regression]


def _files(dir_attr):
    from app.config.settings import settings
    return sorted(p.name for p in Path(getattr(settings, dir_attr)).iterdir() if p.is_file())


async def test_reset_after_completed_keeps_completed_in_history(client, fast_pipeline):
    """H4: «Следующий участник» после печати не должен переписывать COMPLETED на IDLE."""
    sid = await drive_to(client, "COMPLETED")
    r = await do(client, "reset")
    assert r.status_code == 200
    assert db_state(sid)()["status"] == "COMPLETED"
    hist = (await client.get("/api/session/history")).json()
    assert [h["status"] for h in hist if h["id"] == sid] == ["COMPLETED"]


async def test_reset_after_error_keeps_error_in_history(client, fast_pipeline, failing_print):
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    await wait_for_status(db_state(sid), {"ERROR"}, timeout=5)
    await do(client, "reset")
    assert db_state(sid)()["status"] == "ERROR"


async def test_raw_photo_deleted_after_successful_print(client, fast_pipeline):
    sid = await drive_to(client, "COMPLETED")
    assert f"{sid}_raw.jpg" not in _files("PHOTOS_DIR")


async def test_raw_photo_deleted_even_if_print_failed(client, fast_pipeline, failing_print):
    """H15: при ошибке печати исходное фото ребёнка остаётся на диске навсегда."""
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    await wait_for_status(db_state(sid), {"ERROR", "COMPLETED", "PRINTING"}, timeout=5)
    import asyncio
    await asyncio.sleep(0.3)
    assert f"{sid}_raw.jpg" not in _files("PHOTOS_DIR"), "сырое фото ребёнка осталось после ошибки печати"


async def test_raw_photo_deleted_if_ai_failed(client, fast_pipeline, failing_ai):
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    await wait_for_status(db_state(sid), {"ERROR"}, timeout=5)
    assert f"{sid}_raw.jpg" not in _files("PHOTOS_DIR")


async def test_raw_photo_deleted_when_session_abandoned(client, fast_pipeline):
    """Ребёнок сфотографировался и ушёл посреди квиза (idle-сброс)."""
    sid = await drive_to(client, "QUIZ_POWER")
    assert f"{sid}_raw.jpg" in _files("PHOTOS_DIR")
    await do(client, "reset")
    assert f"{sid}_raw.jpg" not in _files("PHOTOS_DIR")


async def test_generated_face_image_not_kept_after_card_composed(client, fast_pipeline):
    """H15: storage/generated/{id}_ai.jpg — это лицо ребёнка (у mock — просто тонированное фото),
    не удаляется никогда и раздаётся публично."""
    sid = await drive_to(client, "COMPLETED")
    assert f"{sid}_ai.jpg" not in _files("GENERATED_DIR")


async def test_retention_script_removes_old_cards_and_rows(client, fast_pipeline, tmp_path):
    """Процедура удаления в конце дня: карточки и строки старше порога удаляются."""
    import time
    from app.config.settings import settings
    from scripts.cleanup_storage import cleanup  # регресс: скрипта не было

    sid = await drive_to(client, "COMPLETED")
    card = Path(settings.CARDS_DIR) / f"{sid}_card.jpg"
    assert card.exists()
    report = cleanup(older_than_hours=0, now=time.time() + 60, dry_run=False)
    assert not card.exists()
    assert db_state(sid)() is None
    assert report["cards_deleted"] >= 1
