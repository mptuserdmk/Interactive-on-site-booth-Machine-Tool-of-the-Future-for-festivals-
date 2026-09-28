"""Вспомогательные функции для тестов (импортируются как `from helpers import ...`)."""
import asyncio
import io
import time
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageDraw

class _FastAsyncio:
    """Подмена модуля asyncio внутри mock_provider/printing: sleep() без задержки, остальное настоящее."""

    @staticmethod
    async def sleep(_delay=0, *args, **kwargs):
        await asyncio.sleep(0)

    def __getattr__(self, name):
        return getattr(asyncio, name)


FAST_ASYNCIO = _FastAsyncio()

INTERMEDIATE_STATES = {
    "PHOTO_PENDING", "PHOTO_TAKEN", "QUIZ_ELEMENT", "QUIZ_POWER", "QUIZ_COLOR",
    "GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING",
}
FINAL_STATES = {"COMPLETED", "ERROR", "IDLE"}


def make_photo_bytes(size=(600, 800), mode="RGB", fmt="JPEG", exif_orientation: Optional[int] = None,
                     color=(70, 95, 140)) -> bytes:
    """Синтетический «портрет»: светлый прямоугольник-лицо сверху, чтобы видеть ориентацию."""
    if mode == "CMYK":
        img = Image.new("CMYK", size, (40, 20, 0, 60))
    elif mode == "RGBA":
        img = Image.new("RGBA", size, (*color, 128))
    else:
        img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    w, h = size
    if w > 4 and h > 4:
        draw.rectangle([w // 4, h // 10, 3 * w // 4, h // 3], fill="white" if mode != "CMYK" else (0, 0, 0, 0))
    buf = io.BytesIO()
    kwargs = {}
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = exif_orientation
        kwargs["exif"] = exif.tobytes()
    img.save(buf, fmt, **kwargs)
    return buf.getvalue()


def write_photo(path: Path, **kwargs) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(make_photo_bytes(**kwargs))
    return path


async def wait_for_status(get_state, statuses: Iterable[str], timeout: float = 10.0, interval: float = 0.02):
    """Ждёт, пока get_state() вернёт dict со статусом из statuses. Вместо sleep(2.0) (T2)."""
    statuses = set(statuses)
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = get_state()
        if asyncio.iscoroutine(last):
            last = await last
        if last and last.get("status") in statuses:
            return last
        await asyncio.sleep(interval)
    raise AssertionError(f"За {timeout} с статус не стал {sorted(statuses)}; последний: {last and last.get('status')}")


async def wait_until(predicate, timeout: float = 5.0, what: str = "условие"):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"За {timeout} с не выполнилось: {what}")


def db_state(session_id: str):
    from app.storage.database import db
    return lambda: db.get_session(session_id)


async def active_state(client):
    r = await client.get("/api/session/active")
    return r.json()


def make_sync_client(client_addr=("127.0.0.1", 50000), **kwargs):
    """Starlette TestClient (нужен для WebSocket и lifespan). Использовать как контекстный менеджер."""
    import warnings
    from starlette.testclient import TestClient
    from app.main import app
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return TestClient(app, raise_server_exceptions=False, client=client_addr, **kwargs)


def printed_session_ids():
    from app.printing.manager import print_manager
    return [e["session_id"] for e in print_manager.print_history]


def printed_files():
    from app.printing.manager import print_manager
    return [Path(e["file_path"]).name for e in print_manager.print_history]


ACTIONS = {
    "new": ("POST", "/api/session/new", None),
    "capture": ("POST", "/api/camera/capture", None),
    "retake": ("POST", "/api/session/photo/retake", None),
    "confirm": ("POST", "/api/session/photo/confirm", None),
    "element": ("POST", "/api/session/answer", {"question_type": "element", "answer_id": "space"}),
    "power": ("POST", "/api/session/answer", {"question_type": "power", "answer_id": "precision"}),
    "color": ("POST", "/api/session/answer", {"question_type": "color", "answer_id": "azure"}),
    "trigger_print": ("POST", "/api/print/trigger-active", None),
    "reset": ("POST", "/api/session/reset", None),
}


async def do(client, action: str):
    method, url, body = ACTIONS[action]
    return await client.request(method, url, json=body)


_PATH_TO_STATE = ["PHOTO_PENDING", "PHOTO_TAKEN", "QUIZ_ELEMENT", "QUIZ_POWER", "QUIZ_COLOR"]
_STEPS = ["new", "capture", "confirm", "element", "power"]


async def drive_to(client, state: str):
    """Доводит киоск до состояния state через API. Для GENERATING/READY_TO_PRINT/PRINTING/ERROR/COMPLETED
    тест сам готовит гейты/отказы (ai_gate, print_gate, failing_*). Возвращает id сессии или None."""
    if state == "NONE":
        return None
    if state in _PATH_TO_STATE:
        steps = _STEPS[: _PATH_TO_STATE.index(state) + 1]
    else:
        steps = _STEPS + ["color"]
    sid = None
    for step in steps:
        r = await do(client, step)
        assert r.status_code == 200, (step, r.status_code, r.text)
        if step == "new":
            sid = r.json()["id"]
    if state in ("COMPLETED", "ERROR", "READY_TO_PRINT"):
        await wait_for_status(db_state(sid), {state}, timeout=15)
    elif state in ("GENERATING", "PRINTING"):
        await wait_for_status(db_state(sid), {state}, timeout=15)
    return sid


async def run_kiosk_flow(client, element="space", power="precision", color="azure", photo: str = "capture"):
    """Полный путь посетителя через API до выбора цвета. Возвращает id сессии."""
    r = await client.post("/api/session/new")
    assert r.status_code == 200, r.text
    sid = r.json()["id"]
    if photo == "capture":
        r = await client.post("/api/camera/capture")
        assert r.status_code == 200, r.text
    elif photo == "upload":
        r = await client.post("/api/camera/upload-ota",
                              files={"file": ("p.jpg", make_photo_bytes(), "image/jpeg")})
        assert r.status_code == 200, r.text
    r = await client.post("/api/session/photo/confirm")
    assert r.status_code == 200, r.text
    for qt, aid in (("element", element), ("power", power), ("color", color)):
        r = await client.post("/api/session/answer", json={"question_type": qt, "answer_id": aid})
        assert r.status_code == 200, r.text
    return sid
