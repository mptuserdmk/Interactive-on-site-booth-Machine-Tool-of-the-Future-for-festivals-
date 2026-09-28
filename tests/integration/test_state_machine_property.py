"""
Property-based (hypothesis.stateful): случайные последовательности действий киоска, оператора и
телефона ассистента не приводят к 5xx, двойной печати или зависшим сессиям.

Используется синхронный Starlette TestClient: его event loop живёт в отдельном потоке всё время
теста, поэтому фоновые пайплайны (asyncio.create_task) реально выполняются между шагами.
"""
import time
from types import SimpleNamespace

import pytest
from hypothesis import HealthCheck, settings as hsettings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from helpers import FAST_ASYNCIO, make_photo_bytes, make_sync_client

pytestmark = [pytest.mark.integration, pytest.mark.regression, pytest.mark.slow]

STUCK = {"GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING"}
ANSWERS = {
    "element": ["space", "atom", "robots", "medicine", "metal", "lava", ""],
    "power": ["precision", "speed", "power", "mind", "care", "flight"],
    "color": ["azure", "gold", "emerald", "white", "black"],
    "bogus": ["space"],
}


async def _instant(*_a, **_k):
    return None


class KioskMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        import app.ai.mock_provider as mp
        import app.printing.manager as pm
        from app.printing.manager import print_manager
        from app.session.manager import session_manager
        from app.storage.database import db

        self._patches = [(mp, "asyncio", mp.asyncio), (pm, "asyncio", pm.asyncio)]
        mp.asyncio = FAST_ASYNCIO
        pm.asyncio = FAST_ASYNCIO
        session_manager.active_session = None
        print_manager.print_history.clear()
        conn = db.get_connection()
        conn.execute("DELETE FROM sessions")
        conn.commit()
        conn.close()
        self.db = db
        self.pm = print_manager
        self.tc = make_sync_client()
        self.tc.__enter__()
        self.codes = []

    def _call(self, method, url, **kw):
        r = self.tc.request(method, url, **kw)
        self.codes.append((method, url, r.status_code))
        assert r.status_code < 500, f"{method} {url} → {r.status_code}: {r.text[:200]}"
        return r

    @rule()
    def new(self):
        self._call("POST", "/api/session/new")

    @rule()
    def capture(self):
        self._call("POST", "/api/camera/capture")

    @rule()
    def upload(self):
        self._call("POST", "/api/camera/upload-ota", files={"file": ("p.jpg", make_photo_bytes(size=(64, 80)), "image/jpeg")})

    @rule()
    def retake(self):
        self._call("POST", "/api/session/photo/retake")

    @rule()
    def confirm(self):
        self._call("POST", "/api/session/photo/confirm")

    @rule(qt=st.sampled_from(list(ANSWERS)), data=st.data())
    def answer(self, qt, data):
        aid = data.draw(st.sampled_from(ANSWERS[qt]))
        self._call("POST", "/api/session/answer", json={"question_type": qt, "answer_id": aid})

    @rule()
    def trigger_print(self):
        self._call("POST", "/api/print/trigger-active")

    @rule()
    def reset(self):
        self._call("POST", "/api/session/reset")

    @rule(ms=st.integers(min_value=0, max_value=150))
    def wait(self, ms):
        time.sleep(ms / 1000)

    @invariant()
    def active_status_is_valid(self):
        r = self.tc.get("/api/session/active")
        assert r.status_code == 200
        data = r.json()
        if data:
            from app.session.models import SessionState
            SessionState(data["status"])

    def teardown(self):
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                rows = self.db.get_recent_sessions(200)
                if not any(r["status"] in STUCK for r in rows):
                    break
                time.sleep(0.05)
            rows = self.db.get_recent_sessions(200)
            stuck = [(r["id"][-6:], r["status"]) for r in rows if r["status"] in STUCK]
            assert not stuck, f"зависшие сессии: {stuck}; шаги: {self.codes[-15:]}"
            printed = [e["session_id"] for e in self.pm.print_history]
            dup = {s for s in printed if printed.count(s) > 1}
            assert not dup, f"одна сессия напечатана несколько раз: {dup}"
            status = {r["id"]: r["status"] for r in rows}
            wrong = [s for s in printed if status.get(s) != "COMPLETED"]
            assert not wrong, f"напечатаны сессии не в COMPLETED: {[(s[-6:], status.get(s)) for s in wrong]}"
        finally:
            self.tc.__exit__(None, None, None)
            for mod, name, val in self._patches:
                setattr(mod, name, val)


KioskMachine.TestCase.settings = hsettings(
    max_examples=25, stateful_step_count=30, deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
TestKioskStateMachine = KioskMachine.TestCase
TestKioskStateMachine = pytest.mark.timeout(600)(TestKioskStateMachine)
