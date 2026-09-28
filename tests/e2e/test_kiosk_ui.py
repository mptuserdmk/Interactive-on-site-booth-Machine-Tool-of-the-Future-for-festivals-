"""
E2E киоска (Chromium, 1920×1080, touch): путь посетителя, idle-модалка, двойной тап, ошибки, потеря связи,
офлайн, разрешения, зоны касания. Скриншоты — docs/evidence/screens/.
"""
import json
import time

import pytest
from playwright.sync_api import expect

from .conftest import LiveServer, ROOT, block_all_external, shot

pytestmark = [pytest.mark.e2e, pytest.mark.slow]
T = 20_000  # мс
# Первая отрисовка ждёт React/Babel с CDN (S10): из сети проверки HEAD к unpkg.com занимал до 29 с.
# Раскладку проверяем отдельно от сети; офлайн-сценарий — test_kiosk_works_fully_offline.
FIRST_PAINT = 90_000


def open_kiosk(page, live_server):
    t0 = time.perf_counter()
    page.goto(live_server.url + "/kiosk")
    expect(page.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=FIRST_PAINT)
    return time.perf_counter() - t0


def start_to_quiz(page):
    page.get_by_role("button", name="Начать создание своего образа").click()
    expect(page.get_by_text("УЛЫБНИСЬ В КАМЕРУ")).to_be_visible(timeout=T)
    page.get_by_role("button", name="Сделать фотографию").click()
    expect(page.get_by_text("ТВОЙ КАДР ОТЛИЧНЫЙ")).to_be_visible(timeout=T)


def test_full_visitor_journey(kiosk_page, live_server):
    page = kiosk_page
    tti = open_kiosk(page, live_server)
    print(f"\n[UX] Welcome видим через {tti:.2f} с после goto")
    shot(page, "01_welcome")
    start_to_quiz(page)
    photo = page.get_by_role("img", name="Сделанный снимок")
    expect(photo).to_be_visible()
    page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=photo.element_handle(), timeout=T)
    shot(page, "02_photo_review")

    page.get_by_role("button", name="Переснять фотографию").click()
    expect(page.get_by_text("УЛЫБНИСЬ В КАМЕРУ")).to_be_visible(timeout=T)
    page.get_by_role("button", name="Сделать фотографию").click()
    page.get_by_role("button", name="Подтвердить фотографию и перейти к выбору").click()

    page.get_by_role("button", name="Выбрать вариант Космос").click()
    shot(page, "03_quiz_power")
    page.get_by_role("button", name="Выбрать вариант Точность").click()
    page.get_by_role("button", name="Выбрать цвет Лазурный").click()
    t_color = time.perf_counter()
    expect(page.get_by_text("НЕЙРОСЕТЬ ГЕНЕРИРУЕТ ОБРАЗ")).to_be_visible(timeout=T)
    shot(page, "04_generating")
    expect(page.get_by_text("ПАСПОРТ НАПЕЧАТАН!")).to_be_visible(timeout=T)
    print(f"[UX] выбор цвета → «ПАСПОРТ НАПЕЧАТАН» на экране: {time.perf_counter() - t_color:.2f} с")
    card = page.get_by_role("img", name="Итоговый паспорт инженера")
    page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=card.element_handle(), timeout=T)
    shot(page, "05_result")

    page.get_by_role("button", name="Завершить сессию и перейти к следующему участнику").click()
    expect(page.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=T)
    assert page.errors == [], page.errors


def test_double_tap_color_prints_once(kiosk_page, live_server):
    page = kiosk_page
    open_kiosk(page, live_server)
    before = live_server.api("GET", "/api/print/status").json()["total_printed"]
    start_to_quiz(page)
    page.get_by_role("button", name="Подтвердить фотографию и перейти к выбору").click()
    page.get_by_role("button", name="Выбрать вариант Атом").click()
    page.get_by_role("button", name="Выбрать вариант Ум").click()
    btn = page.get_by_role("button", name="Выбрать цвет Золотой")
    # тройной тап в одном такте браузера — до того, как React перерисует экран
    btn.evaluate("b => { b.click(); b.click(); b.click(); }")
    expect(page.get_by_text("ПАСПОРТ НАПЕЧАТАН!")).to_be_visible(timeout=T)
    time.sleep(3)
    after = live_server.api("GET", "/api/print/status").json()["total_printed"]
    assert after - before == 1, f"тройной тап → напечатано {after - before}"


def test_idle_modal_stay_and_auto_reset(kiosk_page, live_server):
    page = kiosk_page
    open_kiosk(page, live_server)
    page.get_by_role("button", name="Начать создание своего образа").click()
    expect(page.get_by_text("УЛЫБНИСЬ В КАМЕРУ")).to_be_visible(timeout=T)
    expect(page.get_by_text("ТЫ ЕЩЁ ЗДЕСЬ?")).to_be_visible(timeout=17_000)
    shot(page, "06_idle_modal")
    page.get_by_role("button", name="Продолжить работу с киоском").click()
    expect(page.get_by_text("ТЫ ЕЩЁ ЗДЕСЬ?")).to_be_hidden()
    expect(page.get_by_text("УЛЫБНИСЬ В КАМЕРУ")).to_be_visible()
    # без касаний: 15 с + 5 с отсчёт → приветствие
    expect(page.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=25_000)


def test_error_state_is_not_shown_as_success(kiosk_page, live_server):
    """Раньше ERROR рендерился ResultScreen-ом: «🎉 ОБРАЗ УСПЕШНО СОЗДАН!»."""
    page = kiosk_page
    fake = {"id": "sess_" + "e" * 32, "created_at": "2026-09-28T10:00:00+00:00", "status": "ERROR",
            "error_message": "Не удалось создать изображение: AI недоступен", "print_status": "pending", "meta": {}}
    page.route("**/api/session/active", lambda r: r.fulfill(status=200, content_type="application/json",
                                                             body=json.dumps(fake)))
    page.goto(live_server.url + "/kiosk")
    expect(page.get_by_text("УПС! ЧТО-ТО ПОШЛО НЕ ТАК")).to_be_visible(timeout=T)
    expect(page.get_by_text("ОБРАЗ УСПЕШНО СОЗДАН")).to_have_count(0)
    shot(page, "07_error_screen")


def test_action_error_is_visible_to_visitor(kiosk_page, live_server):
    page = kiosk_page
    open_kiosk(page, live_server)
    page.route("**/api/session/new", lambda r: r.fulfill(status=500, content_type="application/json",
                                                          body='{"detail":"Внутренняя ошибка"}'))
    page.get_by_role("button", name="Начать создание своего образа").click()
    expect(page.get_by_role("alert")).to_be_visible(timeout=5000)
    shot(page, "08_action_error_toast")


def test_server_restart_kiosk_reconnects(browser):
    """H18: обрыв WS/рестарт сервера → баннер «нет связи», затем автопереподключение без F5."""
    srv = LiveServer().start()
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    try:
        page = ctx.new_page()
        page.route("**/*", lambda route: route.continue_() if "127.0.0.1" in route.request.url or
                   any(h in route.request.url for h in ("unpkg.com", "cdn.tailwindcss.com")) else route.abort())
        page.goto(srv.url + "/kiosk")
        expect(page.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=FIRST_PAINT)
        srv.stop()
        expect(page.get_by_text("НЕТ СВЯЗИ СО СТЕНДОМ — ПЕРЕПОДКЛЮЧАЕМСЯ…")).to_be_visible(timeout=10_000)
        shot(page, "09_connection_lost")
        srv.start()
        expect(page.get_by_text("НЕТ СВЯЗИ СО СТЕНДОМ — ПЕРЕПОДКЛЮЧАЕМСЯ…")).to_be_hidden(timeout=20_000)
        page.get_by_role("button", name="Начать создание своего образа").click()
        expect(page.get_by_text("УЛЫБНИСЬ В КАМЕРУ")).to_be_visible(timeout=T)
    finally:
        ctx.close()
        srv.stop()


VENDORED = all((ROOT / "frontend" / "static" / "vendor" / n).exists() for n in (
    "react-18.3.1.production.min.js", "react-dom-18.3.1.production.min.js",
    "babel-standalone-7.26.10.min.js", "tailwindcss-3.4.17.js"))


@pytest.mark.regression
@pytest.mark.xfail(not VENDORED, strict=True, reason="S10: без scripts/vendor_frontend.py киоск офлайн — белый экран")
def test_kiosk_works_fully_offline(browser, live_server):
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    ctx.route("**/*", block_all_external)
    page = ctx.new_page()
    try:
        page.goto(live_server.url + "/kiosk")
        shot(page, "10_offline_kiosk")
        expect(page.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=15_000)
        page.get_by_role("button", name="Начать создание своего образа").click()
        expect(page.get_by_text("УЛЫБНИСЬ В КАМЕРУ")).to_be_visible(timeout=T)
    finally:
        ctx.close()


RESOLUTIONS = [(1080, 1920), (1920, 1080), (2560, 1440), (3840, 2160), (1024, 768), (1366, 1024)]


@pytest.mark.parametrize("w,h", RESOLUTIONS, ids=[f"{w}x{h}" for w, h in RESOLUTIONS])
def test_resolutions_no_horizontal_scroll(browser, live_server, w, h):
    from .conftest import allow_only_local_and_cdn
    ctx = browser.new_context(viewport={"width": w, "height": h}, has_touch=True)
    ctx.route("**/*", allow_only_local_and_cdn)
    page = ctx.new_page()
    try:
        page.goto(live_server.url + "/kiosk")
        expect(page.get_by_text("КЕМ ТЫ СТАНЕШЬ В")).to_be_visible(timeout=FIRST_PAINT)
        cta = page.get_by_role("button", name="Начать создание своего образа")
        box = cta.bounding_box()
        shot(page, f"res_{w}x{h}_welcome")
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 0, f"горизонтальный скролл {overflow}px"
        assert box and box["y"] + box["height"] <= h, f"кнопка «СОЗДАТЬ ОБРАЗ» ниже первого экрана: {box}"
    finally:
        ctx.close()


def test_touch_targets_at_least_64px(kiosk_page, live_server):
    page = kiosk_page
    open_kiosk(page, live_server)
    start_to_quiz(page)
    page.get_by_role("button", name="Подтвердить фотографию и перейти к выбору").click()
    expect(page.get_by_role("button", name="Выбрать вариант Космос")).to_be_visible(timeout=T)
    small = page.evaluate("""() => [...document.querySelectorAll('button')]
        .filter(b => b.offsetParent)
        .map(b => ({t: (b.getAttribute('aria-label') || b.innerText).slice(0, 40), r: b.getBoundingClientRect()}))
        .filter(x => x.r.width < 64 || x.r.height < 64)
        .map(x => `${x.t}: ${Math.round(x.r.width)}×${Math.round(x.r.height)}`)""")
    assert small == [], small
