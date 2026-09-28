"""
Профиль нагрузки «Станка Будущего». Только против своего экземпляра на 127.0.0.1:

    python tests/load/live_server.py --port 8765
    locust -f tests/load/locustfile.py --headless -u 20 -r 2 -t 15m --host http://127.0.0.1:8765

Реальный профиль: 600 посетителей / 10 ч ≈ 1 сессия в минуту, пик ×5. Один киоск (одна активная
сессия), 1 оператор, 1–3 окна MJPEG, 3–5 WS-клиентов, гости открывают карточки по QR.
KioskUser — fixed_count=1: киоск физически один, параллельные «киоски» воевали бы за одну сессию.
"""
import random
import re
import threading
import time

from locust import HttpUser, User, between, constant, events, task

try:
    import websocket  # websocket-client
except ImportError:  # pragma: no cover
    websocket = None

KNOWN_CARDS = []
_lock = threading.Lock()
FPS_SAMPLES = []
EXPECTED_CONFLICT = {409}

ANSWERS = [
    ("element", ["space", "atom", "robots", "medicine", "metal"]),
    ("power", ["precision", "speed", "power", "mind", "care"]),
    ("color", ["azure", "gold", "emerald", "white"]),
]


def _ok(r, allowed=(200,)):
    if r.status_code in allowed or r.status_code in EXPECTED_CONFLICT:
        r.success()
    else:
        r.failure(f"HTTP {r.status_code}: {r.text[:120]}")


class KioskUser(HttpUser):
    """Полный цикл посетителя с человеческими паузами."""
    fixed_count = 1
    wait_time = between(2, 5)

    @task
    def full_cycle(self):
        with self.client.post("/api/session/new", name="POST /api/session/new", catch_response=True) as r:
            _ok(r)
        time.sleep(random.uniform(1, 3))
        with self.client.post("/api/camera/capture", name="POST /api/camera/capture", catch_response=True) as r:
            _ok(r)
        time.sleep(random.uniform(0.5, 1.5))
        with self.client.post("/api/session/photo/confirm", name="POST /api/session/photo/confirm",
                              catch_response=True) as r:
            _ok(r)
        for qt, opts in ANSWERS:
            time.sleep(random.uniform(0.8, 2.0))
            with self.client.post("/api/session/answer", json={"question_type": qt, "answer_id": random.choice(opts)},
                                  name=f"POST /api/session/answer [{qt}]", catch_response=True) as r:
                _ok(r)
        t0 = time.time()
        sid, status = None, None
        while time.time() - t0 < 30:
            r = self.client.get("/api/session/active", name="GET /api/session/active (poll)")
            data = r.json() if r.status_code == 200 else None
            status = data and data.get("status")
            sid = data and data.get("id")
            if status in ("COMPLETED", "ERROR"):
                break
            time.sleep(0.25)
        elapsed_ms = (time.time() - t0) * 1000
        events.request.fire(request_type="CYCLE", name="cycle color->COMPLETED", response_time=elapsed_ms,
                            response_length=0, exception=None if status == "COMPLETED" else Exception(status),
                            context={})
        if status == "COMPLETED" and sid:
            with _lock:
                KNOWN_CARDS.append(sid)
                del KNOWN_CARDS[:-50]
        time.sleep(random.uniform(2, 4))
        with self.client.post("/api/session/reset", name="POST /api/session/reset", catch_response=True) as r:
            _ok(r)


class OperatorUser(HttpUser):
    """Панель оператора: health каждые 10 с, история, статус принтера."""
    weight = 3
    wait_time = constant(10)

    @task(3)
    def health(self):
        self.client.get("/api/health", name="GET /api/health")

    @task(2)
    def history(self):
        r = self.client.get("/api/session/history?limit=15", name="GET /api/session/history")
        if r.status_code == 200:
            with _lock:
                for h in r.json():
                    if h.get("status") == "COMPLETED" and h["id"] not in KNOWN_CARDS:
                        KNOWN_CARDS.append(h["id"])

    @task(1)
    def print_status(self):
        self.client.get("/api/print/status", name="GET /api/print/status")


class GuestUser(HttpUser):
    """Гость сканирует QR: страница карточки + скачивание JPEG."""
    weight = 10
    wait_time = between(1, 4)

    @task
    def open_card(self):
        with _lock:
            sid = random.choice(KNOWN_CARDS) if KNOWN_CARDS else None
        if not sid:
            self.client.get("/api/quiz/schema", name="GET /api/quiz/schema")
            return
        r = self.client.get(f"/card/{sid}", name="GET /card/{id}")
        m = re.search(r'<img src="([^"]+)"', r.text or "")
        if m:
            self.client.get(m.group(1), name="GET card image")


class WsUser(User):
    """Держит /ws и считает сообщения."""
    weight = 2
    wait_time = constant(1)

    def on_start(self):
        url = self.host.replace("http", "ws", 1) + "/ws"
        t0 = time.time()
        try:
            self.ws = websocket.create_connection(url, timeout=10)
            events.request.fire(request_type="WS", name="connect /ws", response_time=(time.time() - t0) * 1000,
                                response_length=0, exception=None, context={})
        except Exception as e:  # noqa: BLE001
            self.ws = None
            events.request.fire(request_type="WS", name="connect /ws", response_time=(time.time() - t0) * 1000,
                                response_length=0, exception=e, context={})

    @task
    def listen(self):
        if not self.ws:
            return
        self.ws.settimeout(1)
        try:
            msg = self.ws.recv()
            events.request.fire(request_type="WS", name="recv SESSION_UPDATE", response_time=0,
                                response_length=len(msg), exception=None, context={})
        except websocket.WebSocketTimeoutException:
            pass
        except Exception as e:  # noqa: BLE001
            events.request.fire(request_type="WS", name="recv SESSION_UPDATE", response_time=0,
                                response_length=0, exception=e, context={})
            self.on_start()

    def on_stop(self):
        if self.ws:
            self.ws.close()


class StreamUser(HttpUser):
    """Держит MJPEG /api/camera/stream 10 с и считает FPS."""
    fixed_count = 3
    wait_time = constant(0)

    @task
    def watch(self):
        frames, t0 = 0, time.time()
        with self.client.get("/api/camera/stream", stream=True, name="GET /api/camera/stream (10s)",
                             catch_response=True, timeout=30) as r:
            for chunk in r.iter_content(chunk_size=65536):
                frames += chunk.count(b"--frame")
                if time.time() - t0 > 10:
                    break
            fps = frames / (time.time() - t0)
            FPS_SAMPLES.append(fps)
            r.success()


@events.test_stop.add_listener
def _report(environment, **_):
    if FPS_SAMPLES:
        s = sorted(FPS_SAMPLES)
        print(f"[MJPEG] окон={len(s)} FPS min={s[0]:.1f} median={s[len(s) // 2]:.1f} max={s[-1]:.1f}")
