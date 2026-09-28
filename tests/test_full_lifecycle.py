"""
Полный жизненный цикл через HTTP API (бывший скрипт с asyncio.run, переведён на pytest).

Отличия от старой версии:
- изоляция окружения в conftest.py (tmp-каталоги, PRINT_SIMULATION_MODE=true, CAMERA_INDEX=99);
- вместо sleep(2.0) — ожидание статуса с таймаутом (T2).
"""
import os

import pytest

from helpers import active_state, db_state, run_kiosk_flow, wait_for_status

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("path", ["/", "/kiosk", "/operator", "/mobile-camera"])
async def test_html_pages_open(client, path):
    r = await client.get(path)
    assert r.status_code == 200


async def test_health_and_schema(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    r = await client.get("/api/quiz/schema")
    assert r.status_code == 200
    assert len(r.json()) == 3
    r = await client.get("/api/quiz/combinations")
    assert r.status_code == 200
    assert len(r.json()) == 100


async def test_full_visitor_cycle(client, fast_pipeline):
    r = await client.post("/api/session/new")
    assert r.status_code == 200
    sess = r.json()
    assert sess["status"] == "PHOTO_PENDING"
    sid = sess["id"]

    r = await client.post("/api/camera/capture")
    assert r.status_code == 200
    assert r.json()["session_id"] == sid

    r = await client.post("/api/session/photo/retake")
    assert r.status_code == 200
    assert r.json()["session"]["status"] == "PHOTO_PENDING"

    await client.post("/api/camera/capture")
    r = await client.post("/api/session/photo/confirm")
    assert r.json()["session"]["status"] == "QUIZ_ELEMENT"

    r = await client.post("/api/session/answer", json={"question_type": "element", "answer_id": "space"})
    assert r.json()["session"]["status"] == "QUIZ_POWER"
    r = await client.post("/api/session/answer", json={"question_type": "power", "answer_id": "precision"})
    assert r.json()["session"]["status"] == "QUIZ_COLOR"
    r = await client.post("/api/session/answer", json={"question_type": "color", "answer_id": "azure"})
    assert r.status_code == 200

    done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=15)
    assert done["status"] == "COMPLETED", done.get("error_message")
    assert done["machine_name"] == "Космический Токарь-Оптик"
    assert done["final_card_path"]
    assert done["print_status"] == "printed"

    r = await client.post("/api/print/reprint", json={"session_id": sid})
    assert r.status_code == 200
    assert r.json()["success"] is True

    r = await client.get(f"/card/{sid}")
    assert r.status_code == 200

    r = await client.post("/api/session/reset")
    assert r.status_code == 200
    st = await active_state(client)
    assert st is None or st["status"] == "IDLE"
    assert db_state(sid)()["status"] == "COMPLETED"


@pytest.mark.load
@pytest.mark.skipif(bool(os.environ.get("PYTEST_XDIST_WORKER")), reason="SLO-замер времени — только последовательно")
async def test_full_cycle_with_real_mock_delays(client):
    """Без ускорения: реальные задержки mock AI (1.5 с) + печать (2.5 с). SLO: ≤ 5 с до COMPLETED."""
    import time
    sid = await run_kiosk_flow(client)
    t0 = time.monotonic()
    done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=20)
    elapsed = time.monotonic() - t0
    assert done["status"] == "COMPLETED"
    print(f"\n[SLO] выбор цвета → COMPLETED: {elapsed:.2f} с")
    assert elapsed <= 5.0
