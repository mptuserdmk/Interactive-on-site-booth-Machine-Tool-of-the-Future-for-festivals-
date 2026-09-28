"""
Общая изоляция тестов «Станка Будущего».

ВАЖНО (T4): settings, db, camera_manager, print_manager, session_manager — синглтоны,
создаются при импорте app.*. Поэтому окружение выставляется здесь, на уровне модуля,
ДО любого импорта app.*. PHOTOS_DIR / GENERATED_DIR / CARDS_DIR / DB_PATH / FALLBACK_DIR
в Settings не выводятся из STORAGE_DIR, поэтому переопределяется каждый путь отдельно.
"""
import asyncio
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
for p in (str(ROOT), str(TESTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEST_ROOT = Path(tempfile.mkdtemp(prefix="stanok_tests_"))
TEST_STORAGE = TEST_ROOT / "storage"

TEST_ENV = {
    "AI_PROVIDER": "mock",
    "AI_API_KEY": "",
    "AI_FALLBACK_ON_ERROR": "true",
    "PRINT_SIMULATION_MODE": "true",
    "ENABLE_AUTO_PRINT": "true",
    "PRINTER_NAME": "",
    "DELETE_SOURCE_PHOTOS_AFTER_PRINT": "true",
    "CAMERA_INDEX": "99",
    "STORAGE_DIR": str(TEST_STORAGE),
    "PHOTOS_DIR": str(TEST_STORAGE / "photos"),
    "GENERATED_DIR": str(TEST_STORAGE / "generated"),
    "CARDS_DIR": str(TEST_STORAGE / "cards"),
    "FALLBACK_DIR": str(TEST_ROOT / "assets" / "fallback"),
    "DB_PATH": str(TEST_ROOT / "kiosk.db"),
}
os.environ.update(TEST_ENV)


# --- Жёсткий предохранитель от реальной печати (T3) ---------------------------------
class RealPrintForbidden(RuntimeError):
    pass


def _forbidden_startfile(*args, **kwargs):
    raise RealPrintForbidden(f"os.startfile запрещён в тестах (реальная печать): {args!r}")


if sys.platform == "win32":
    os.startfile = _forbidden_startfile  # type: ignore[attr-defined]

# Импорт app.* только после выставления окружения
from app.config.settings import settings  # noqa: E402
from app.printing.manager import print_manager  # noqa: E402

if not (settings.PRINT_SIMULATION_MODE and print_manager.is_simulation):
    raise RuntimeError("Тесты остановлены: PRINT_SIMULATION_MODE не включён, печать может уйти на железо")
if Path(settings.DB_PATH).resolve().is_relative_to(ROOT) or Path(settings.STORAGE_DIR).resolve().is_relative_to(ROOT):
    raise RuntimeError("Тесты остановлены: DB_PATH/STORAGE_DIR указывают внутрь репозитория")


# --- Контроль, что прогон не меняет боевые data/ и storage/ ---------------------------
_PROD_DIRS = [ROOT / "data", ROOT / "storage", ROOT / "assets"]


def _snapshot_prod_dirs():
    snap = {}
    for base in _PROD_DIRS:
        if not base.exists():
            snap[str(base)] = "<нет каталога>"
            continue
        for f in sorted(base.rglob("*")):
            if f.is_file():
                st = f.stat()
                snap[str(f)] = (st.st_size, st.st_mtime_ns, hashlib.sha256(f.read_bytes()).hexdigest())
    return snap


def pytest_sessionstart(session):
    session.config._prod_snapshot = _snapshot_prod_dirs()


def pytest_sessionfinish(session, exitstatus):
    before = getattr(session.config, "_prod_snapshot", None)
    if before is None:
        return
    after = _snapshot_prod_dirs()
    if before != after:
        changed = sorted(set(before.items()) ^ set(after.items()))
        tr = session.config.pluginmanager.get_plugin("terminalreporter")
        msg = "ПРОГОН ИЗМЕНИЛ БОЕВЫЕ ДАННЫЕ: " + "; ".join(str(c[0]) for c in changed[:20])
        if tr:
            tr.write_line(msg, red=True)
        session.exitstatus = 1
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


# --- Сброс синглтонов между тестами ----------------------------------------------------
def _clear_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    for f in d.iterdir():
        if f.is_file():
            f.unlink()


@pytest.fixture(autouse=True)
def reset_singletons():
    from app.session.manager import session_manager
    from app.storage.database import db

    from app.ai.manager import ai_manager

    session_manager.active_session = None
    print_manager.print_history.clear()
    ai_manager.stats.update(total=0, fallback_count=0, last_fallback=False, last_error=None, last_error_at=None)
    for attr in ("_printing", "_last_reprint"):
        if hasattr(session_manager, attr):
            getattr(session_manager, attr).clear()
    from app.camera.manager import camera_manager
    for attr, value in (("_fail_count", 0), ("_last_reopen", 0.0)):
        if hasattr(camera_manager, attr):
            setattr(camera_manager, attr, value)
    conn = db.get_connection()
    try:
        conn.execute("DELETE FROM sessions")
        conn.commit()
    finally:
        conn.close()
    for d in (settings.PHOTOS_DIR, settings.GENERATED_DIR, settings.CARDS_DIR):
        _clear_dir(Path(d))
    yield
    session_manager.active_session = None


@pytest.fixture
def fresh_session_manager():
    """Новый SessionManager без слушателей, изолированный от глобального WS-хука."""
    from app.session.manager import SessionManager
    return SessionManager()


from helpers import FAST_ASYNCIO  # noqa: E402


@pytest.fixture
def fast_mock_ai(monkeypatch):
    """MockProvider без искусственной задержки 1.5 с (остальной asyncio — настоящий)."""
    import app.ai.mock_provider as mp
    monkeypatch.setattr(mp, "asyncio", FAST_ASYNCIO)


@pytest.fixture
def fast_print(monkeypatch):
    """Симуляция печати без задержки 2.5 с."""
    import app.printing.manager as pm
    monkeypatch.setattr(pm, "asyncio", FAST_ASYNCIO)


@pytest.fixture
def fast_pipeline(fast_mock_ai, fast_print):
    return True


@pytest.fixture
def ai_calls(monkeypatch):
    """Счётчик вызовов AI (сколько раз реально «заплатили» за генерацию)."""
    from app.ai.manager import ai_manager
    calls = []
    orig = ai_manager.generate_image

    async def counting(request, combo, output_path):
        calls.append(request.session_id)
        return await orig(request, combo, output_path)

    monkeypatch.setattr(ai_manager, "generate_image", counting)
    return calls


@pytest.fixture
def ai_gate(monkeypatch):
    """AI «висит», пока тест не откроет gate.set(). Первые `hold` вызовов ждут, остальные нет."""
    from app.ai.manager import ai_manager
    state = SimpleNamespace(gate=asyncio.Event(), calls=[], hold=10**9)
    orig = ai_manager.generate_image

    async def gated(request, combo, output_path):
        state.calls.append(request.session_id)
        if len(state.calls) <= state.hold:
            await state.gate.wait()
        return await orig(request, combo, output_path)

    monkeypatch.setattr(ai_manager, "generate_image", gated)
    return state


@pytest.fixture
def print_gate(monkeypatch):
    """Печать «висит», пока тест не откроет gate.set()."""
    state = SimpleNamespace(gate=asyncio.Event(), calls=[])
    orig = print_manager.print_card

    async def gated(file_path, session_id):
        state.calls.append((session_id, str(file_path)))
        await state.gate.wait()
        return await orig(file_path, session_id)

    monkeypatch.setattr(print_manager, "print_card", gated)
    return state


@pytest.fixture
def failing_print(monkeypatch):
    """Принтер «без бумаги»: print_card возвращает ошибку."""
    async def fail(file_path, session_id):
        return {"success": False, "error": "Нет бумаги (тест)"}
    monkeypatch.setattr(print_manager, "print_card", fail)


@pytest.fixture
def failing_ai(monkeypatch):
    """AI возвращает неуспех без fallback."""
    from app.ai.manager import ai_manager
    from app.ai.models import AIGenerationResult

    async def fail(request, combo, output_path):
        return AIGenerationResult(success=False, provider_name="bothub", duration_seconds=0.0,
                                  error="Bothub API error 500: {\"internal\":\"stacktrace at /srv/secret\"}")
    monkeypatch.setattr(ai_manager, "generate_image", fail)


@pytest.fixture
def broadcast_log():
    """Все SESSION_UPDATE, которые ушли бы в WebSocket: [(session_id, status), ...]."""
    from app.session.manager import session_manager
    log = []

    async def rec(data):
        log.append((data.get("id"), data.get("status")))

    session_manager.add_listener(rec)
    yield log
    session_manager._listeners.remove(rec)


async def drain_background_tasks():
    """Отменяет фоновые пайплайны (asyncio.create_task без ссылки) после теста."""
    current = asyncio.current_task()
    pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
    for t in pending:
        t.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def _make_client(client_addr=("127.0.0.1", 50000)):
    import httpx
    from app.main import app
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False, client=client_addr)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30)


@pytest.fixture
async def client():
    """Клиент с адреса самого киоска (loopback)."""
    async with _make_client() as c:
        yield c
    await drain_background_tasks()


@pytest.fixture
async def remote_client():
    """Клиент «чужого» устройства в Wi-Fi площадки (гость/злоумышленник)."""
    async with _make_client(("192.168.1.66", 51234)) as c:
        yield c
    await drain_background_tasks()


from helpers import make_sync_client  # noqa: E402


@pytest.fixture
def sync_client():
    """Starlette TestClient (с loopback-адреса) — нужен для WebSocket-тестов и lifespan."""
    with make_sync_client() as c:
        yield c


@pytest.fixture
def remote_sync_client():
    with make_sync_client(("192.168.1.66", 51234)) as c:
        yield c
