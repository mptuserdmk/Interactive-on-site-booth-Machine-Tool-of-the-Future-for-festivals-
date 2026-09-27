import shutil
import httpx
from fastapi import APIRouter
from app.config.settings import settings
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
    
    # 2. AI
    ai_provider = ai_manager.get_active_provider()
    ai_healthy = await ai_provider.health_check()
    
    # 3. Print
    pr_status = print_manager.get_status()
    
    # 4. Disk space
    total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
    free_gb = round(free / (1024 ** 3), 2)
    
    # 5. Network connectivity (Fast socket check)
    network_ok = True
    try:
        import socket
        s = socket.create_connection(("8.8.8.8", 53), timeout=0.2)
        s.close()
        network_ok = True
    except Exception:
        network_ok = False

    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "local_ip": settings.LOCAL_IP,
        "base_url": settings.BASE_URL,
        "mobile_camera_url": f"{settings.BASE_URL}/mobile-camera",
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
                "provider": ai_provider.name
            },
            "printer": {
                "ok": pr_status["is_ready"],
                "active_printer": pr_status["active_printer"],
                "simulation": pr_status["simulation_mode"]
            },
            "network": {
                "ok": network_ok
            },
            "disk": {
                "ok": free_gb > 1.0,
                "free_gb": free_gb
            }
        }
    }

@router.get("/quiz/schema", summary="Get quiz questions and choices")
async def get_quiz_schema():
    return get_questions_schema()

@router.get("/quiz/combinations", summary="Get all 100 combination mappings")
async def get_all_combinations():
    return combination_manager.get_all()
