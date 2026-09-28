"""
Доказательство дефекта idle-автосброса на ИСХОДНОЙ версии kiosk_app.jsx (git HEAD):
браузер получает старый JSX вместо текущего, сервер — текущий (API совместим для этого сценария).

    python tests/tools/evidence_idle_head.py
"""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from e2e.conftest import LiveServer, SCREENS, allow_only_local_and_cdn  # noqa: E402


def main():
    head_jsx = subprocess.run(["git", "show", "HEAD:frontend/static/js/kiosk_app.jsx"], cwd=ROOT,
                              capture_output=True, check=True).stdout
    srv = LiveServer().start()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1920, "height": 1080})
            ctx.set_default_navigation_timeout(90_000)
            ctx.route("**/*", allow_only_local_and_cdn)
            ctx.route("**/static/js/kiosk_app.jsx", lambda r: r.fulfill(status=200, body=head_jsx,
                                                                       content_type="text/babel; charset=utf-8"))
            page = ctx.new_page()
            page.goto(srv.url + "/kiosk")
            page.get_by_text("КЕМ ТЫ СТАНЕШЬ В").wait_for(timeout=60_000)
            page.get_by_role("button", name="Начать создание своего образа").click()
            page.get_by_text("УЛЫБНИСЬ В КАМЕРУ").wait_for(timeout=20_000)
            t0 = time.time()
            page.get_by_text("ТЫ ЕЩЁ ЗДЕСЬ?").wait_for(timeout=20_000)
            print(f"[HEAD] модалка появилась через {time.time() - t0:.1f} с")
            samples = []
            for _ in range(12):
                time.sleep(1)
                num = page.locator("div.fixed >> div.rounded-full").first.inner_text()
                samples.append(num)
            welcome = page.get_by_text("КЕМ ТЫ СТАНЕШЬ В").count()
            SCREENS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SCREENS / "evidence_HEAD_idle_countdown_stuck.png"))
            print(f"[HEAD] отсчёт в модалке по секундам: {samples}; Welcome на экране через 12 с: {bool(welcome)}")
            b.close()
    finally:
        srv.stop()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
