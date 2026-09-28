"""
E2E панели оператора и мобильной камеры ассистента (эмуляция iPhone и Pixel), digital-карточка гостя.
"""
import re

import pytest
from playwright.sync_api import expect

from helpers import make_photo_bytes
from .conftest import allow_only_local_and_cdn, shot

pytestmark = [pytest.mark.e2e, pytest.mark.slow]
T = 20_000


def complete_session(live_server):
    live_server.api("POST", "/api/session/new")
    live_server.api("POST", "/api/camera/capture")
    live_server.api("POST", "/api/session/photo/confirm")
    for qt, a in (("element", "robots"), ("power", "care"), ("color", "emerald")):
        live_server.api("POST", "/api/session/answer", json={"question_type": qt, "answer_id": a})
    import time
    for _ in range(100):
        s = live_server.api("GET", "/api/session/active").json()
        if s and s["status"] in ("COMPLETED", "ERROR"):
            return s
        time.sleep(0.2)
    raise AssertionError("сессия не завершилась")


def test_operator_panel_health_qr_history_reprint(browser, live_server):
    ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
    ctx.route("**/*", allow_only_local_and_cdn)
    page = ctx.new_page()
    try:
        sess = complete_session(live_server)
        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))
        page.goto(live_server.url + "/operator")
        expect(page.locator("#stat-ai")).not_to_have_text("Проверка...", timeout=T)
        qr = page.locator("#ota-qr-image")
        page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=qr.element_handle(), timeout=T)
        assert "/api/qr.png" in qr.get_attribute("src")
        assert "token=" in page.locator("#ota-url-text").inner_text()
        expect(page.locator("#history-rows")).to_contain_text(sess["machine_name"], timeout=T)
        shot(page, "20_operator")
        page.locator("#history-rows button").first.click()
        page.wait_for_timeout(4000)
        assert dialogs and "очередь печати" in dialogs[-1], dialogs
        page.locator("#history-rows button").first.click()  # вторая допечатка сразу → 429 с понятным текстом
        page.wait_for_timeout(1500)
        assert "не чаще" in dialogs[-1], dialogs
    finally:
        ctx.close()


@pytest.mark.parametrize("device", ["iPhone 13", "Pixel 7"])
def test_mobile_camera_gallery_upload_reaches_kiosk(browser, playwright, live_server, tmp_path, device):
    photo = tmp_path / "IMG_0001.jpg"
    photo.write_bytes(make_photo_bytes(size=(1200, 1600)))
    dev = dict(playwright.devices[device])
    dev.pop("default_browser_type", None)
    mctx = browser.new_context(**dev)
    kctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    for c in (mctx, kctx):
        c.route("**/*", allow_only_local_and_cdn)
    try:
        kiosk = kctx.new_page()
        kiosk.goto(live_server.url + "/kiosk")
        expect(kiosk.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=90_000)  # CDN (S10)

        phone = mctx.new_page()
        phone.goto(live_server.url + "/mobile-camera")
        phone.set_input_files("#file-input", str(photo))
        expect(phone.locator("#toast")).to_contain_text("передано", timeout=T)
        shot(phone, f"21_mobile_{device.replace(' ', '_')}")
        # фото появляется на киоске через WebSocket, без перезагрузки
        expect(kiosk.get_by_text("ТВОЙ КАДР ОТЛИЧНЫЙ")).to_be_visible(timeout=T)

        # файл не-изображение → понятная ошибка, а не «undefined»
        bad = tmp_path / "doc.jpg"
        bad.write_bytes(b"not an image at all")
        phone.set_input_files("#file-input", str(bad))
        expect(phone.locator("#toast")).to_contain_text("Ошибка отправки", timeout=T)
        expect(phone.locator("#toast")).not_to_contain_text("undefined")
    finally:
        mctx.close()
        kctx.close()


def test_mobile_camera_network_error_message(browser, playwright, live_server, tmp_path):
    photo = tmp_path / "p.jpg"
    photo.write_bytes(make_photo_bytes())
    ctx = browser.new_context(**{k: v for k, v in playwright.devices["iPhone 13"].items() if k != "default_browser_type"})
    ctx.route("**/*", allow_only_local_and_cdn)
    page = ctx.new_page()
    try:
        page.goto(live_server.url + "/mobile-camera")
        page.route("**/api/camera/upload-ota", lambda r: r.abort("internetdisconnected"))
        page.set_input_files("#file-input", str(photo))
        expect(page.locator("#toast")).to_contain_text("Ошибка связи со стендом", timeout=T)
    finally:
        ctx.close()


def test_digital_card_pages(browser, live_server):
    sess = complete_session(live_server)
    ctx = browser.new_context(viewport={"width": 412, "height": 915})  # экран телефона гостя
    ctx.route("**/*", allow_only_local_and_cdn)
    page = ctx.new_page()
    try:
        r = page.goto(live_server.url + f"/card/{sess['id']}")
        assert r.status == 200
        img = page.get_by_role("img", name="Digital Card")
        page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=img.element_handle(), timeout=T)
        href = page.get_by_text("ПОДЕЛИТЬСЯ В TELEGRAM").get_attribute("href")
        assert re.match(r"^https://t\.me/share/url\?url=http", href) and "%2Fcard%2F" in href
        shot(page, "22_digital_card")
        r = page.goto(live_server.url + "/card/sess_does_not_exist")
        assert r.status == 404
        expect(page.get_by_text("Карточка не найдена")).to_be_visible()
    finally:
        ctx.close()
