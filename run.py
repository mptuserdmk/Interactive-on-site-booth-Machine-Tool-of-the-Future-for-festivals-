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
    print("⚡  AI-ФОТОЛОКАЦИЯ «СТАНОК БУДУЩЕГО»")
    print("=" * 65)
    print(f"🖥️  Экран киоска (на этом ПК):        http://localhost:{settings.PORT}/kiosk")
    print(f"🎛️  Панель оператора (на этом ПК):    http://localhost:{settings.PORT}/operator")
    print(f"💻  Оператор с другого устройства:    {settings.BASE_URL}/operator?token={settings.ACCESS_TOKEN}")
    print(f"📱  Камера телефона (QR на панели):   {settings.BASE_URL}/mobile-camera?token={settings.CAMERA_TOKEN}")
    print(f"🔑  Код доступа оператора: {settings.ACCESS_TOKEN}  (задайте ACCESS_TOKEN в .env, чтобы не менялся)")
    if settings.ENABLE_API_DOCS:
        print(f"📚  OpenAPI / Swagger документация:   http://localhost:{settings.PORT}/docs")
    print("=" * 65 + "\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run FastAPI app (строго 1 процесс: состояние сессии в памяти)
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False, workers=1)
