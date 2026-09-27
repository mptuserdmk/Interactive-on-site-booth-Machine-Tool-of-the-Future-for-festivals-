import os
import sys
import webbrowser
import threading
import time
import uvicorn
from app.config.settings import settings

def open_browser():
    time.sleep(1.5)
    kiosk_url = f"http://localhost:{settings.PORT}/kiosk"
    print(f"\n[INFO] Открываем экран киоска в браузере: {kiosk_url}")
    webbrowser.open(kiosk_url)

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print(f"⚡  AI-ФОТОЛОКАЦИЯ «СТАНОК БУДУЩЕГО»")
    print("=" * 65)
    print(f"🖥️  Экран киоска (для посетителя):     http://localhost:{settings.PORT}/kiosk")
    print(f"🎛️  Панель оператора (для ПК):         http://localhost:{settings.PORT}/operator")
    print(f"📱  Камера iPhone (по воздуху Wi-Fi): http://{settings.LOCAL_IP}:{settings.PORT}/mobile-camera")
    print(f"📚  OpenAPI / Swagger документация:   http://localhost:{settings.PORT}/docs")
    print("=" * 65 + "\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run FastAPI app
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
