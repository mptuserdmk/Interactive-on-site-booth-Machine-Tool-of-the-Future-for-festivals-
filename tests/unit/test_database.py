"""
SQLite (H12): параллельная запись, утечка соединений, восстановление после сбоев.
"""
import gc
import threading
import warnings
from datetime import datetime

import psutil
import pytest

pytestmark = pytest.mark.unit


def _row(i):
    return {"id": f"sess_t_{i:05d}", "created_at": datetime(2026, 9, 28, 12, 0, i % 60).isoformat(),
            "status": "COMPLETED", "machine_name": "Тест"}


def _handles():
    p = psutil.Process()
    return p.num_handles() if hasattr(p, "num_handles") else p.num_fds()


def test_parallel_writes_no_locked_errors(tmp_path):
    """H12: 1000 save_session из 20 потоков → нет 'database is locked', все строки на месте."""
    from app.storage.database import Database
    db = Database(tmp_path / "t.db")
    errors = []

    def worker(start):
        for i in range(start, start + 50):
            try:
                db.save_session(_row(i))
            except Exception as e:  # noqa: BLE001
                errors.append(repr(e))

    threads = [threading.Thread(target=worker, args=(k * 50,)) for k in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert len(db.get_recent_sessions(limit=200)) == 200
    conn = db.get_connection()
    try:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1000
    finally:
        conn.close()


def test_handles_stable_after_many_calls(tmp_path):
    """H12: число OS-handles/FD не растёт после 2000 операций."""
    from app.storage.database import Database
    db = Database(tmp_path / "t.db")
    for i in range(50):
        db.save_session(_row(i))
    gc.collect()
    before = _handles()
    for i in range(2000):
        db.save_session(_row(i % 200))
        db.get_session(f"sess_t_{i % 200:05d}")
    gc.collect()
    after = _handles()
    print(f"\n[H12] handles до={before} после={after}")
    assert after - before < 20


@pytest.mark.regression
def test_connections_are_closed_explicitly(tmp_path):
    """H12: `with conn:` в sqlite3 не закрывает соединение (только commit/rollback).
    В Python 3.13 это видно как ResourceWarning 'unclosed database'."""
    from app.storage.database import Database
    db = Database(tmp_path / "t.db")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        db.save_session(_row(1))
        db.get_session("sess_t_00001")
        db.get_recent_sessions(10)
        gc.collect()
    leaks = [str(w.message) for w in caught if issubclass(w.category, ResourceWarning)]
    assert leaks == [], leaks[:3]


def test_wal_mode_enabled(tmp_path):
    from app.storage.database import Database
    db = Database(tmp_path / "t.db")
    conn = db.get_connection()
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        conn.close()
    print(f"\n[H12] journal_mode={mode}")
    assert mode.lower() == "wal"


@pytest.mark.regression
@pytest.mark.parametrize("limit", [-1, 0, 10**9])
def test_history_limit_is_bounded(tmp_path, limit):
    """S5: LIMIT -1 в SQLite = без лимита."""
    from app.storage.database import Database
    db = Database(tmp_path / "t.db")
    for i in range(300):
        db.save_session(_row(i))
    assert len(db.get_recent_sessions(limit=limit)) <= 200


@pytest.mark.chaos
@pytest.mark.regression
def test_corrupted_db_file_does_not_crash_startup(tmp_path):
    """Chaos: файл БД повреждён (выдернули питание) → раньше Database() падал при импорте → белый экран."""
    from app.storage.database import Database
    p = tmp_path / "kiosk.db"
    p.write_bytes(b"this is not a sqlite database" * 100)
    db = Database(p)
    db.save_session(_row(1))
    assert db.get_session("sess_t_00001")["status"] == "COMPLETED"
    assert list(tmp_path.glob("kiosk.db.corrupt-*")), "повреждённый файл не сохранён для разбора"


@pytest.mark.chaos
@pytest.mark.regression
def test_db_file_deleted_at_runtime_recovers(tmp_path):
    """Chaos: kiosk.db удалили во время работы → sqlite создаёт пустой файл без таблицы → 'no such table'."""
    from app.storage.database import Database
    p = tmp_path / "kiosk.db"
    db = Database(p)
    db.save_session(_row(1))
    p.unlink()
    db.save_session(_row(2))
    assert db.get_session("sess_t_00002") is not None


@pytest.mark.chaos
@pytest.mark.regression
def test_interrupted_sessions_marked_on_startup():
    """Chaos: kill сервера в GENERATING/PRINTING → после рестарта сессии не висят в промежуточных статусах."""
    from helpers import make_sync_client
    from app.storage.database import db
    for i, st in enumerate(["GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING", "QUIZ_POWER"]):
        db.save_session({**_row(i), "status": st})
    with make_sync_client():
        pass  # lifespan (startup) отработал
    statuses = {r["id"]: r["status"] for r in db.get_recent_sessions(100)}
    stuck = {k: v for k, v in statuses.items() if v in ("GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING")}
    assert stuck == {}, stuck
