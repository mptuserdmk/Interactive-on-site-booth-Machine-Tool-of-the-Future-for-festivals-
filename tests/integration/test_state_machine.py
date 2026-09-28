"""
White-box: переходы state machine сессии (app/session/manager.py) через HTTP API.

Целевой контракт (после фиксов):
  (нет | IDLE | COMPLETED | ERROR) --new--------------> PHOTO_PENDING
  (нет | терминальная)             --capture/upload---> новая сессия, PHOTO_TAKEN
  PHOTO_PENDING | PHOTO_TAKEN      --capture/upload---> PHOTO_TAKEN
  PHOTO_TAKEN                      --retake-----------> PHOTO_PENDING
  PHOTO_TAKEN                      --confirm----------> QUIZ_ELEMENT
  QUIZ_ELEMENT --element--> QUIZ_POWER --power--> QUIZ_COLOR --color--> GENERATING
  GENERATING --AI ok--> COMPOSING --> READY_TO_PRINT --(auto)--> PRINTING --ok--> COMPLETED
  GENERATING --AI fail (без fallback)--> ERROR;  PRINTING --печать не удалась--> ERROR
  READY_TO_PRINT | ERROR(с карточкой) --trigger-active--> PRINTING
  любое --reset--> активной сессии нет (IDLE), терминальный статус в БД сохраняется
Всё остальное — 409 Conflict, состояние не меняется (не 500 и не молчаливое 200).
"""
import pytest

from helpers import ACTIONS, active_state, db_state, do, drive_to, printed_session_ids, wait_for_status

pytestmark = pytest.mark.integration

QUIZ_STATES = ["QUIZ_ELEMENT", "QUIZ_POWER", "QUIZ_COLOR"]

INVALID = {
    "NONE": ["confirm", "retake", "element", "power", "color", "trigger_print"],
    "PHOTO_PENDING": ["confirm", "element", "power", "color", "trigger_print"],
    "PHOTO_TAKEN": ["element", "power", "color", "trigger_print"],
    "QUIZ_ELEMENT": ["confirm", "retake", "power", "color", "capture", "trigger_print"],
    "QUIZ_POWER": ["confirm", "retake", "element", "color", "capture", "trigger_print"],
    "QUIZ_COLOR": ["confirm", "retake", "element", "power", "capture", "trigger_print"],
}
INVALID_CASES = [(s, a) for s, acts in INVALID.items() for a in acts]


@pytest.mark.regression
@pytest.mark.parametrize("state,action", INVALID_CASES, ids=[f"{s}-{a}" for s, a in INVALID_CASES])
async def test_invalid_transition_is_409_and_state_unchanged(client, fast_pipeline, ai_calls, state, action):
    """H5/H6: недопустимое действие не должно давать 500 или молча менять/создавать сессию."""
    sid = await drive_to(client, state)
    before = await active_state(client)
    r = await do(client, action)
    assert r.status_code == 409, f"{state} + {action}: ожидали 409, получили {r.status_code} {r.text[:200]}"
    after = await active_state(client)
    assert (after or {}).get("status") == (before or {}).get("status")
    assert (after or {}).get("id") == (before or {}).get("id") == sid if sid else True
    assert ai_calls == [], "недопустимое действие запустило AI-генерацию"


@pytest.mark.regression
@pytest.mark.parametrize("action", ["confirm", "retake", "element", "power", "color", "capture", "trigger_print"])
async def test_invalid_transition_during_generating(client, fast_pipeline, ai_gate, action):
    sid = await drive_to(client, "GENERATING")
    r = await do(client, action)
    assert r.status_code == 409, f"GENERATING + {action}: {r.status_code} {r.text[:200]}"
    assert db_state(sid)()["status"] == "GENERATING"
    ai_gate.gate.set()
    done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=15)
    assert done["status"] == "COMPLETED"
    assert printed_session_ids() == [sid]


@pytest.mark.regression
@pytest.mark.parametrize("action", ["confirm", "retake", "element", "power", "color", "trigger_print"])
async def test_invalid_transition_after_completed(client, fast_pipeline, action):
    sid = await drive_to(client, "COMPLETED")
    r = await do(client, action)
    assert r.status_code == 409, f"COMPLETED + {action}: {r.status_code} {r.text[:200]}"
    assert db_state(sid)()["status"] == "COMPLETED"
    assert printed_session_ids() == [sid]


# --- Допустимые переходы -----------------------------------------------------------------

@pytest.mark.parametrize("state,action,expected", [
    ("NONE", "new", "PHOTO_PENDING"),
    ("PHOTO_PENDING", "new", "PHOTO_PENDING"),
    ("QUIZ_POWER", "new", "PHOTO_PENDING"),
    ("PHOTO_PENDING", "capture", "PHOTO_TAKEN"),
    ("PHOTO_TAKEN", "capture", "PHOTO_TAKEN"),
    ("PHOTO_TAKEN", "retake", "PHOTO_PENDING"),
    ("PHOTO_PENDING", "retake", "PHOTO_PENDING"),
    ("PHOTO_TAKEN", "confirm", "QUIZ_ELEMENT"),
    ("QUIZ_ELEMENT", "element", "QUIZ_POWER"),
    ("QUIZ_POWER", "power", "QUIZ_COLOR"),
])
async def test_valid_transition(client, fast_pipeline, state, action, expected):
    await drive_to(client, state)
    r = await do(client, action)
    assert r.status_code == 200, r.text
    assert (await active_state(client))["status"] == expected


async def test_capture_without_session_creates_new_session(client, fast_pipeline):
    r = await do(client, "capture")
    assert r.status_code == 200
    st = await active_state(client)
    assert st["status"] == "PHOTO_TAKEN"
    assert st["id"] == r.json()["session_id"]


@pytest.mark.regression
async def test_capture_after_completed_starts_new_session(client, fast_pipeline):
    """Ассистент прислал фото следующего ребёнка, пока на экране результат предыдущего."""
    sid = await drive_to(client, "COMPLETED")
    r = await do(client, "capture")
    assert r.status_code == 200
    new_sid = r.json()["session_id"]
    assert new_sid != sid
    assert db_state(sid)()["status"] == "COMPLETED"
    assert (await active_state(client))["status"] == "PHOTO_TAKEN"


async def test_color_starts_pipeline_to_completed(client, fast_pipeline):
    sid = await drive_to(client, "QUIZ_COLOR")
    r = await do(client, "color")
    assert r.status_code == 200
    assert r.json()["session"]["status"] == "GENERATING"
    done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=15)
    assert done["status"] == "COMPLETED"
    assert done["print_status"] == "printed"


async def test_pipeline_passes_through_all_states(client, fast_pipeline, broadcast_log):
    sid = await drive_to(client, "COMPLETED")
    seen = [s for (i, s) in broadcast_log if i == sid]
    for expected in ["PHOTO_PENDING", "PHOTO_TAKEN", "QUIZ_ELEMENT", "QUIZ_POWER", "QUIZ_COLOR",
                     "GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING", "COMPLETED"]:
        assert expected in seen, f"статус {expected} не транслировался; видели {seen}"


async def test_no_auto_print_stays_ready_to_print_then_manual_print(client, fast_pipeline, monkeypatch):
    from app.config.settings import settings
    monkeypatch.setattr(settings, "ENABLE_AUTO_PRINT", False)
    sid = await drive_to(client, "READY_TO_PRINT")
    assert printed_session_ids() == []
    r = await do(client, "trigger_print")
    assert r.status_code == 200
    done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=10)
    assert done["status"] == "COMPLETED"
    assert printed_session_ids() == [sid]


async def test_ai_failure_without_fallback_goes_to_error(client, fast_pipeline, failing_ai):
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    done = await wait_for_status(db_state(sid), {"ERROR", "COMPLETED"}, timeout=10)
    assert done["status"] == "ERROR"
    assert printed_session_ids() == []


@pytest.mark.regression
async def test_print_failure_goes_to_error_not_stuck_in_printing(client, fast_pipeline, failing_print):
    """Новая находка N1: при ошибке печати статус навсегда остаётся PRINTING."""
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    done = await wait_for_status(db_state(sid), {"ERROR", "COMPLETED"}, timeout=5)
    assert done["status"] == "ERROR"
    assert done["print_status"] == "error"
    assert done["error_message"]


@pytest.mark.regression
async def test_manual_print_retry_after_print_error(client, fast_pipeline, monkeypatch):
    from app.printing.manager import print_manager
    orig = print_manager.print_card
    attempts = []

    async def flaky(file_path, session_id):
        attempts.append(session_id)
        if len(attempts) == 1:
            return {"success": False, "error": "Нет бумаги (тест)"}
        return await orig(file_path, session_id)

    monkeypatch.setattr(print_manager, "print_card", flaky)
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    await wait_for_status(db_state(sid), {"ERROR"}, timeout=5)
    r = await do(client, "trigger_print")
    assert r.status_code == 200
    done = await wait_for_status(db_state(sid), {"COMPLETED"}, timeout=5)
    assert done["print_status"] == "printed"


@pytest.mark.parametrize("state", ["PHOTO_PENDING", "PHOTO_TAKEN", "QUIZ_ELEMENT", "QUIZ_POWER", "QUIZ_COLOR"])
async def test_reset_from_interactive_states(client, fast_pipeline, state):
    await drive_to(client, state)
    r = await do(client, "reset")
    assert r.status_code == 200
    st = await active_state(client)
    assert st is None or st["status"] == "IDLE"


async def test_reset_without_session_is_ok(client):
    r = await do(client, "reset")
    assert r.status_code == 200


def test_actions_table_covers_all_endpoints():
    assert set(ACTIONS) >= {"new", "capture", "retake", "confirm", "element", "power", "color", "trigger_print", "reset"}
