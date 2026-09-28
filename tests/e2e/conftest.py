"""
E2E-инфраструктура: изолированный живой сервер (tests/load/live_server.py) на 127.0.0.1 и политика сети
для браузера: разрешены только 127.0.0.1 и CDN, с которых киоск реально грузит React/Babel/Tailwind
(пока не выполнен scripts/vendor_frontend.py). Всё остальное блокируется.
"""
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCREENS = ROOT / "docs" / "evidence" / "screens"
CDN_HOSTS = ("unpkg.com", "cdn.tailwindcss.com")


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class LiveServer:
    def __init__(self, fast=False):
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.fast = fast
        self.workdir = tempfile.mkdtemp(prefix="stanok_e2e_")
        self.proc = None

    def start(self):
        args = [sys.executable, str(ROOT / "tests" / "load" / "live_server.py"), "--port", str(self.port),
                "--workdir", self.workdir] + (["--fast"] if self.fast else [])
        self.proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 40
        while time.time() < deadline:
            try:
                if httpx.get(self.url + "/api/quiz/schema", timeout=1).status_code == 200:
                    return self
            except httpx.HTTPError:
                pass
            time.sleep(0.3)
        raise RuntimeError("live server did not start")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(10)

    def api(self, method, path, **kw):
        return httpx.request(method, self.url + path, timeout=30, **kw)


@pytest.fixture(scope="session")
def live_server():
    srv = LiveServer().start()
    yield srv
    srv.stop()


@pytest.fixture(autouse=True)
def _slow_cdn_timeouts(request):
    """Пока React/Babel/Tailwind грузятся с CDN, первая отрисовка киоска занимает 15+ с (замер) —
    навигации даём 90 с, чтобы тесты мерили логику, а не сеть площадки."""
    if "browser" not in request.fixturenames:
        yield
        return
    browser = request.getfixturevalue("browser")
    orig = browser.new_context

    def patched(*a, **k):
        ctx = orig(*a, **k)
        ctx.set_default_navigation_timeout(90_000)
        return ctx

    browser.new_context = patched
    yield
    browser.new_context = orig


@pytest.fixture(autouse=True)
def _reset_live(request):
    if "live_server" in request.fixturenames:
        request.getfixturevalue("live_server").api("POST", "/api/session/reset")
    yield


def allow_only_local_and_cdn(route):
    host = httpx.URL(route.request.url).host
    if host in ("127.0.0.1", "localhost") or host in CDN_HOSTS:
        return route.continue_()
    return route.abort()


def block_all_external(route):
    host = httpx.URL(route.request.url).host
    return route.continue_() if host in ("127.0.0.1", "localhost") else route.abort()


@pytest.fixture
def kiosk_page(browser, live_server):
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, has_touch=True, locale="ru-RU")
    ctx.route("**/*", allow_only_local_and_cdn)
    page = ctx.new_page()
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    yield page
    ctx.close()


def shot(page, name):
    SCREENS.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(450)  # дождаться анимаций появления (animate-fade-in 0.25 с)
    page.screenshot(path=str(SCREENS / f"{name}.png"))
