import asyncio
import shutil
import socket
from urllib.parse import urlparse
from fastapi import APIRouter
from app.config.settings import settings, get_local_ip
from app.camera.manager import camera_manager
from app.printing.manager import print_manager
from app.ai.manager import ai_manager
from app.quiz.engine import get_questions_schema
from app.quiz.combinations import combination_manager

router = APIRouter(prefix="/api", tags=["Health & Schema"])

@router.get("/health", summary="Full system diagnostic status")
async def get_system_health():
    # 1. Camera
    cam_status = camera_manager.get_status()
    
    # 2. AI: «OK» только если ключ похож на настоящий и последняя генерация не ушла в mock (H8, H9)
    ai_provider = ai_manager.get_active_provider()
    ai_key_ok = await ai_provider.health_check()
    ai_stats = ai_manager.stats
    ai_healthy = ai_key_ok and not ai_stats["last_fallback"]
    
    # 3. Print: win32print может подвиснуть на сетевом принтере — в пул потоков (H13)
    pr_status = await asyncio.to_thread(print_manager.get_status)
    
    # 4. Disk space
    total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
    free_gb = round(free / (1024 ** 3), 2)
    
    # 5. Network connectivity: блокирующие сокет-проверки — в пул потоков (H13)
    network_ok, current_ip = await asyncio.to_thread(_network_probe)
    qr_host = urlparse(settings.BASE_URL).hostname or ""
    qr_url_ok = not (qr_host in ("localhost", "::1") or qr_host.startswith("127."))

    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "local_ip": settings.LOCAL_IP,
        "base_url": settings.BASE_URL,
        "mobile_camera_url": f"{settings.BASE_URL}/mobile-camera?token={settings.CAMERA_TOKEN}",
        "operator_url": f"{settings.BASE_URL}/operator",
        "kiosk_url": f"{settings.BASE_URL}/kiosk",
        "diagnostics": {
            "camera": {
                "ok": cam_status.is_available,
                "source": cam_status.source_type,
                "resolution": cam_status.resolution
            },
            "ai": {
                "ok": ai_healthy,
                "provider": ai_provider.name,
                "configured_provider": settings.AI_PROVIDER,
                "is_mock": ai_provider.name == "mock",
                "key_ok": ai_key_ok,
                "generations": ai_stats["total"],
                "fallback_count": ai_stats["fallback_count"],
                "last_fallback": ai_stats["last_fallback"],
                "last_error": ai_stats["last_error"]
            },
            "printer": {
                "ok": pr_status["is_ready"],
                "active_printer": pr_status["active_printer"],
                "problem": pr_status.get("problem"),
                "queue_jobs": pr_status.get("queue_jobs", 0),
                "simulation": pr_status["simulation_mode"]
            },
            "network": {
                "ok": network_ok,
                # Если QR на карточках ведёт на 127.0.0.1 или IP ПК сменился после старта — телефоны гостей
                # карточку не откроют (H11). Оператор должен это видеть до печати.
                "qr_url_ok": qr_url_ok and current_ip == settings.LOCAL_IP,
                "qr_base_url": settings.BASE_URL,
                "current_ip": current_ip,
                "ip_changed": current_ip != settings.LOCAL_IP
            },
            "disk": {
                "ok": free_gb > 1.0,
                "free_gb": free_gb
            }
        }
    }

def _network_probe():
    try:
        s = socket.create_connection(("8.8.8.8", 53), timeout=0.2)
        s.close()
        internet = True
    except OSError:
        internet = False
    return internet, get_local_ip()

@router.get("/quiz/schema", summary="Get quiz questions and choices")
async def get_quiz_schema():
    return get_questions_schema()

@router.get("/quiz/combinations", summary="Get all 100 combination mappings")
async def get_all_combinations():
    return combination_manager.get_all()
