import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(r"c:\Users\andersneo\Desktop\PROJECTFINALMGOK\docs\evidence\screens")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("[1/11] Opening Kiosk Welcome screen...")
        page.goto("http://localhost:8000/kiosk", wait_until="networkidle")
        page.wait_for_selector("#react-kiosk-root")
        time.sleep(1.2)
        page.screenshot(path=str(OUT_DIR / "live_01_welcome.png"))

        print("[2/11] Starting session (Clicking 'СОЗДАТЬ ОБРАЗ МАСТЕРА')...")
        start_btn = page.locator("button:has-text('СОЗДАТЬ ОБРАЗ МАСТЕРА')")
        start_btn.click()
        page.wait_for_selector("text=ОПТИЧЕСКИЙ ВИЗОР")
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "live_02_camera.png"))

        print("[3/11] Taking photo snapshot...")
        shutter_btn = page.locator("button[aria-label='Сделать фотографию']")
        shutter_btn.click()
        page.wait_for_selector("text=ТВОЙ КАДР ОТЛИЧНЫЙ!")
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "live_03_photo_review.png"))

        print("[4/11] Confirming photo...")
        confirm_btn = page.locator("button:has-text('ПОДТВЕРДИТЬ КАДР')")
        confirm_btn.click()
        page.wait_for_selector("text=ВЫБЕРИ СВОЙ ВАЙБ")
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "live_04_quiz_element.png"))

        print("[5/11] Selecting Element (Космос)...")
        page.locator("button[aria-label*='Космос']").click()
        page.wait_for_selector("text=ВЫБЕРИ СУПЕРСИЛУ")
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "live_05_quiz_power.png"))

        print("[6/11] Selecting Superpower (Точность)...")
        page.locator("button[aria-label*='Точность']").click()
        page.wait_for_selector("text=ВЫБЕРИ ЦВЕТ ОБРАЗА")
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "live_06_quiz_color.png"))

        print("[7/11] Selecting Color (Лазурный)...")
        page.locator("button[aria-label*='Лазурный']").click()
        time.sleep(0.8)
        page.screenshot(path=str(OUT_DIR / "live_07_generating.png"))

        print("[8/11] Waiting for 3-panel folding triptych result screen...")
        page.wait_for_selector("text=ОБРАЗ УСПЕШНО СОЗДАН!", timeout=20000)
        # Give 2.5 seconds for the animated central QR portal to unfold smoothly
        time.sleep(2.5)
        page.screenshot(path=str(OUT_DIR / "live_08_result_triptych.png"))

        print("[9/11] Opening Operator Dashboard...")
        page.goto("http://localhost:8000/operator", wait_until="networkidle")
        time.sleep(1.5)
        page.screenshot(path=str(OUT_DIR / "live_09_operator.png"))

        print("[10/11] Opening Mobile Camera page...")
        page.goto("http://localhost:8000/mobile-camera", wait_until="networkidle")
        time.sleep(1.0)
        page.screenshot(path=str(OUT_DIR / "live_10_mobile_camera.png"))

        print("[11/11] Inspecting recent session digital card...")
        api_res = page.evaluate("() => fetch('/api/session/history?limit=1').then(r => r.json())")
        if api_res and len(api_res) > 0:
            sid = api_res[0].get("id")
            print(f"Navigating to digital card: http://localhost:8000/card/{sid}")
            page.goto(f"http://localhost:8000/card/{sid}", wait_until="networkidle")
            time.sleep(1.2)
            page.screenshot(path=str(OUT_DIR / "live_11_digital_card.png"))

        browser.close()
        print("SUCCESS! All 11 live screens captured!")

if __name__ == "__main__":
    run()
