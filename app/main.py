import logging
from contextlib import asynccontextmanager
from urllib.parse import urlencode
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config.settings import settings
from app.api.routes_session import router as session_router
from app.api.routes_camera import router as camera_router
from app.api.routes_print import router as print_router
from app.api.routes_health import router as health_router
from app.api.routes_ws import router as ws_router
from app.api.routes_media import router as media_router, SESSION_ID_RE
from app.security import AccessControlMiddleware
from app.camera.image_io import UploadSizeLimitMiddleware
from app.storage.database import db
from app.session.manager import SessionError
from app.storage.files import delete_file_safely

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("stanok")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # После kill/падения процесса сессии оставались в GENERATING/PRINTING навсегда; фото детей — на диске
    interrupted = db.mark_interrupted_sessions()
    for row in interrupted:
        delete_file_safely(row.get("photo_path"))
        delete_file_safely(row.get("generated_image_path"))
    if interrupted:
        logger.warning("Recovered %d interrupted sessions after restart", len(interrupted))
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Интерактивная AI-фотолокация для фестивалей: USB/Mobile съемка, 100 комбинаций, Pillow композиция и печать.",
    # Документация API в проде закрыта (S9); включается ENABLE_API_DOCS=true
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan
)

# Фронт и API на одном origin — CORS не нужен (раньше allow_origins=["*"] + credentials, S6).
# Доступ: loopback доверенный, остальные устройства — по токену; чужой Origin → 403 (S1, S6)
app.add_middleware(UploadSizeLimitMiddleware, paths=["/api/camera/upload-ota"])  # S4
app.add_middleware(AccessControlMiddleware)

# Static mount. /storage больше НЕ раздаётся как статика: фото детей были публичны (S2)
frontend_dir = settings.BASE_DIR / "frontend"
static_dir = frontend_dir / "static"
templates_dir = frontend_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))
VENDOR_DIR = static_dir / "vendor"


def vendor_assets() -> dict:
    """Какие фронтенд-библиотеки лежат локально (офлайн-режим, S10). Остальное — с CDN."""
    has = lambda name: (VENDOR_DIR / name).is_file()  # noqa: E731
    return {
        "react": has("react-18.3.1.production.min.js") and has("react-dom-18.3.1.production.min.js"),
        "babel": has("babel-standalone-7.26.10.min.js"),
        "tailwind": has("tailwindcss-3.4.17.js"),
    }

@app.exception_handler(SessionError)
async def session_error_handler(request: Request, exc: SessionError):
    # Недопустимый переход state machine — 409/422/404/429 с понятным текстом, а не 500 (H5, H6)
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

# Include API Routers
app.include_router(session_router)
app.include_router(camera_router)
app.include_router(print_router)
app.include_router(health_router)
app.include_router(ws_router)
app.include_router(media_router)

# UI Routes
@app.get("/", summary="Root redirect to Kiosk")
async def root_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="kiosk.html",
        context={"settings": settings, "vendor": vendor_assets()}
    )

@app.get("/kiosk", summary="Visitor Touchscreen Kiosk UI")
async def kiosk_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="kiosk.html",
        context={"settings": settings, "vendor": vendor_assets()}
    )

@app.get("/operator", summary="Operator Control Dashboard")
async def operator_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="operator.html",
        context={"settings": settings}
    )

@app.get("/mobile-camera", summary="iPhone / Mobile OTA Camera Interface")
async def mobile_camera_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="mobile_camera.html",
        context={"settings": settings}
    )

@app.get("/card/{session_id}", summary="Digital Badge Landing Page (QR Destination)")
async def digital_card_page(request: Request, session_id: str):
    sess = db.get_session(session_id) if SESSION_ID_RE.match(session_id) else None
    # Ссылка «Поделиться» собирается на сервере из канонического URL, а не из request.url (S13)
    share_url = "https://t.me/share/url?" + urlencode({
        "url": f"{settings.BASE_URL}/card/{session_id}",
        "text": "Моя профессия будущего на фестивале Станок Будущего!"
    })
    return templates.TemplateResponse(
        request=request,
        name="digital_card.html",
        context={
            "session": sess,
            "settings": settings,
            "share_url": share_url
        },
        status_code=200 if sess else 404
    )

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 AI FESTIVAL KIOSK STARTED")
    print(f"🖥️  Kiosk Display:         http://localhost:{settings.PORT}/kiosk")
    print(f"🎛️  Operator Dashboard:    http://localhost:{settings.PORT}/operator")
    print(f"📱  iPhone Mobile Camera:  http://{settings.LOCAL_IP}:{settings.PORT}/mobile-camera")
    print(f"📚  OpenAPI / Swagger:     http://localhost:{settings.PORT}/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
