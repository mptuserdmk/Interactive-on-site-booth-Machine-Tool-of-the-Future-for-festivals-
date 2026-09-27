import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.routes_session import router as session_router
from app.api.routes_camera import router as camera_router
from app.api.routes_print import router as print_router
from app.api.routes_health import router as health_router
from app.api.routes_ws import router as ws_router
from app.storage.database import db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Интерактивная AI-фотолокация для фестивалей: USB/Mobile съемка, 100 комбинаций, Pillow композиция и печать.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and Storage Mounts
frontend_dir = settings.BASE_DIR / "frontend"
static_dir = frontend_dir / "static"
templates_dir = frontend_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

templates = Jinja2Templates(directory=str(templates_dir))

# Include API Routers
app.include_router(session_router)
app.include_router(camera_router)
app.include_router(print_router)
app.include_router(health_router)
app.include_router(ws_router)

# UI Routes
@app.get("/", summary="Root redirect to Kiosk")
async def root_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="kiosk.html",
        context={"settings": settings}
    )

@app.get("/kiosk", summary="Visitor Touchscreen Kiosk UI")
async def kiosk_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="kiosk.html",
        context={"settings": settings}
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
    sess = db.get_session(session_id)
    return templates.TemplateResponse(
        request=request,
        name="digital_card.html",
        context={
            "session": sess,
            "settings": settings
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(f"🚀 AI FESTIVAL KIOSK STARTED")
    print(f"🖥️  Kiosk Display:         http://localhost:{settings.PORT}/kiosk")
    print(f"🎛️  Operator Dashboard:    http://localhost:{settings.PORT}/operator")
    print(f"📱  iPhone Mobile Camera:  http://{settings.LOCAL_IP}:{settings.PORT}/mobile-camera")
    print(f"📚  OpenAPI / Swagger:     http://localhost:{settings.PORT}/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
