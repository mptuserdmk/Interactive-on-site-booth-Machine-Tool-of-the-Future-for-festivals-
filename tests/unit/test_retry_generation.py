# -*- coding: utf-8 -*-
import pytest
from app.session.manager import session_manager
from app.session.models import SessionState


async def test_retry_generation_endpoint_when_no_active_session(client):
    resp = await client.post("/api/session/retry-generation")
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Повторная генерация доступна только в состоянии ошибки"


async def test_retry_generation_endpoint_when_wrong_state(client):
    await client.post("/api/session/new")
    resp = await client.post("/api/session/retry-generation")
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Повторная генерация доступна только в состоянии ошибки"


async def test_retry_generation_method_success(tmp_path, monkeypatch):
    photo_file = tmp_path / "portrait.jpg"
    photo_file.write_bytes(b"dummy image data")

    sess = await session_manager.new_session()
    sess.photo_path = str(photo_file)
    sess.element = "space"
    sess.power = "precision"
    sess.color = "azure"
    sess.status = SessionState.ERROR
    sess.meta["error_code"] = "ai_generation_failed"

    called = []
    async def dummy_pipeline(sess_arg, combo_arg):
        called.append(sess_arg.id)

    monkeypatch.setattr(session_manager, "_run_generation_and_composition_pipeline", dummy_pipeline)

    res = await session_manager.retry_generation()
    assert res.status == SessionState.GENERATING
    assert res.error_message is None
    import asyncio
    await asyncio.sleep(0.05)
    assert called == [sess.id]
