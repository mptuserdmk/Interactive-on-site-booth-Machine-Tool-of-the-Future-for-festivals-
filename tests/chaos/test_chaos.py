"""
Chaos / отказоустойчивость: AI, диск, камера, старт процесса с плохим окружением.
"""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import httpx
import numpy as np
import pytest
import respx

from helpers import db_state, do, drive_to, wait_for_status

pytestmark = pytest.mark.chaos
ROOT = Path(__file__).resolve().parents[2]
BOTHUB_EDIT = "https://openai.bothub.chat/v1/images/edits"


# --- AI -----------------------------------------------------------------------------------------

FAILURES = {
    "timeout": dict(side_effect=httpx.ReadTimeout("read timeout")),
    "connect_error": dict(side_effect=httpx.ConnectError("no internet")),
    "http_429": dict(status_code=429, json={"error": "rate limit"}),
    "http_500": dict(status_code=500, text="oops"),
    "not_image": dict(status_code=200, json={"data": [{"url": "https://cdn.example.test/x.png"}]}),
}


@pytest.mark.regression
@pytest.mark.parametrize("failure", list(FAILURES))
async def test_ai_outage_session_completes_via_fallback_and_is_flagged(client, fast_pipeline, monkeypatch, failure):
    """AI недоступен → карточка всё равно печатается (fallback), но это видно оператору (H8)."""
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_PROVIDER", "bothub")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-test-0123456789abcdef")
    with respx.mock(assert_all_called=False) as m:
        spec = FAILURES[failure]
        if "side_effect" in spec:
            m.post(BOTHUB_EDIT).mock(side_effect=spec["side_effect"])
        else:
            m.post(BOTHUB_EDIT).respond(**spec)
        m.get("https://cdn.example.test/x.png").respond(200, text="<html>captive portal</html>")
        sid = await drive_to(client, "QUIZ_COLOR")
        await do(client, "color")
        done = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=15)
    assert done["status"] == "COMPLETED", f"{failure}: {done['status']} {done['error_message']}"
    meta = json.loads(done.get("meta_json") or "{}")
    assert meta.get("ai_fallback") is True, f"{failure}: fallback не отмечен, meta={meta}"


# --- Диск ---------------------------------------------------------------------------------------

@pytest.mark.regression
async def test_disk_full_during_composition(client, fast_pipeline, monkeypatch):
    from app.composition.composer import card_composer
    from app.config.settings import settings

    def enospc(**kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(card_composer, "compose_card", enospc)
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    done = await wait_for_status(db_state(sid), {"ERROR"}, timeout=5)
    assert done["status"] == "ERROR"
    assert not (Path(settings.PHOTOS_DIR) / f"{sid}_raw.jpg").exists(), "фото осталось после сбоя"


async def test_health_reports_low_disk(client, monkeypatch):
    import shutil as _sh
    import app.api.routes_health as rh
    monkeypatch.setattr(rh.shutil, "disk_usage", lambda p: _sh._ntuple_diskusage(100 * 2**30, 99.5 * 2**30, int(0.5 * 2**30)))
    disk = (await client.get("/api/health")).json()["diagnostics"]["disk"]
    assert disk["ok"] is False


# --- Камера -------------------------------------------------------------------------------------

class DeadCapture:
    """USB-камеру выдернули: драйвер ещё «открыт», но кадры не приходят."""
    def isOpened(self):
        return True

    def read(self):
        return False, None

    def release(self):
        pass

    def set(self, *a):
        return True


class LiveCapture(DeadCapture):
    def read(self):
        return True, np.full((720, 1280, 3), 128, dtype=np.uint8)


@pytest.mark.regression
async def test_unplugged_camera_does_not_silently_capture_placeholder(client, monkeypatch):
    """Камеру выдернули → capture молча сохраняет mock-кадр «CAPTURED MOCK PHOTO» как фото ребёнка."""
    from app.camera.manager import camera_manager
    from app.config.settings import settings
    monkeypatch.setattr(camera_manager, "cap", DeadCapture())
    monkeypatch.setattr(camera_manager, "is_running", True)
    monkeypatch.setattr(settings, "CAMERA_MOCK_FALLBACK", False, raising=False)
    r = await do(client, "capture")
    assert r.status_code == 503, f"capture с мёртвой камеры → {r.status_code}"
    health = (await client.get("/api/health")).json()["diagnostics"]["camera"]
    assert health["ok"] is False


@pytest.mark.regression
async def test_camera_reconnects_after_replug(client, monkeypatch):
    """Камеру вставили обратно → стенд подхватывает её без перезапуска."""
    import app.camera.manager as cm
    from app.camera.manager import camera_manager
    from app.config.settings import settings
    monkeypatch.setattr(camera_manager, "cap", DeadCapture())
    monkeypatch.setattr(camera_manager, "is_running", True)
    monkeypatch.setattr(settings, "CAMERA_MOCK_FALLBACK", False, raising=False)
    monkeypatch.setattr(cm.cv2, "VideoCapture", lambda *a, **k: LiveCapture())
    await do(client, "capture")  # первая попытка может упасть и запустить переподключение
    r = await do(client, "capture")
    assert r.status_code == 200, r.text


# --- Старт процесса -----------------------------------------------------------------------------

def _run_import(tmp_path, extra_env, code="import app.main"):
    env = {k: v for k, v in os.environ.items()}
    env.update({
        "STORAGE_DIR": str(tmp_path / "s"), "PHOTOS_DIR": str(tmp_path / "s" / "p"),
        "GENERATED_DIR": str(tmp_path / "s" / "g"), "CARDS_DIR": str(tmp_path / "s" / "c"),
        "FALLBACK_DIR": str(tmp_path / "f"), "DB_PATH": str(tmp_path / "k.db"), "PYTHONIOENCODING": "utf-8",
        "PRINT_SIMULATION_MODE": "true", "CAMERA_INDEX": "99",
    })
    env.update(extra_env)
    return subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env={**env, "PYTHONPATH": str(ROOT)},
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def test_start_without_env_file(tmp_path):
    r = _run_import(tmp_path, {})
    assert r.returncode == 0, r.stderr[-800:]


def test_start_with_broken_env_value_gives_clear_error(tmp_path):
    r = _run_import(tmp_path, {"CAMERA_INDEX": "abc"})
    assert r.returncode != 0
    assert "CAMERA_INDEX" in r.stderr
    print("\n[chaos] битый .env →", r.stderr.strip().splitlines()[-1][:200])


def test_start_without_combinations_gives_clear_error(tmp_path):
    empty = tmp_path / "data"
    empty.mkdir()
    r = _run_import(tmp_path, {"DATA_DIR": str(empty)})
    assert r.returncode != 0
    assert "combinations.json" in r.stderr
    print("\n[chaos] нет combinations.json →", r.stderr.strip().splitlines()[-1][:200])


@pytest.mark.slow
def test_port_busy_gives_clear_error(tmp_path):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        code = ("import uvicorn; from app.main import app; "
                f"uvicorn.run(app, host='127.0.0.1', port={port}, log_level='error')")
        r = _run_import(tmp_path, {}, code=code)
    finally:
        s.close()
    out = r.stdout + r.stderr
    assert r.returncode != 0
    assert "10048" in out or "address already in use" in out.lower() or "only one usage" in out.lower(), out[-500:]
    print("\n[chaos] порт занят →", [l for l in out.splitlines() if "error" in l.lower()][:1])
