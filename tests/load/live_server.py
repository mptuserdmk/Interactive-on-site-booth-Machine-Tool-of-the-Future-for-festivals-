"""
Изолированный экземпляр стенда для нагрузки, soak и E2E. Только 127.0.0.1.

    python tests/load/live_server.py --port 8765            # реальные задержки mock AI (1.5 с) и печати (2.5 с)
    python tests/load/live_server.py --port 8765 --fast     # без искусственных задержек (soak 600 сессий)

Всё пишется во временный каталог; PRINT_SIMULATION_MODE принудительно true; os.startfile заблокирован.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def prepare_env(workdir: Path):
    storage = workdir / "storage"
    os.environ.update({
        "AI_PROVIDER": "mock", "AI_API_KEY": "", "PRINT_SIMULATION_MODE": "true", "ENABLE_AUTO_PRINT": "true",
        "CAMERA_INDEX": "99", "STORAGE_DIR": str(storage), "PHOTOS_DIR": str(storage / "photos"),
        "GENERATED_DIR": str(storage / "generated"), "CARDS_DIR": str(storage / "cards"),
        "FALLBACK_DIR": str(workdir / "fallback"), "DB_PATH": str(workdir / "kiosk.db"),
        "ENABLE_API_DOCS": os.environ.get("ENABLE_API_DOCS", "false"),
    })
    if sys.platform == "win32":
        def _no_print(*a, **k):
            raise RuntimeError("os.startfile запрещён на тестовом сервере")
        os.startfile = _no_print  # type: ignore[attr-defined]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    workdir = Path(args.workdir or tempfile.mkdtemp(prefix="stanok_live_"))
    workdir.mkdir(parents=True, exist_ok=True)
    prepare_env(workdir)

    import uvicorn
    from app.config.settings import settings
    from app.printing.manager import print_manager
    assert settings.PRINT_SIMULATION_MODE and print_manager.is_simulation, "печать не в симуляции — стоп"

    if args.fast:
        import asyncio
        import app.ai.mock_provider as mp
        import app.printing.manager as pm

        class _Fast:
            @staticmethod
            async def sleep(*_a, **_k):
                await asyncio.sleep(0)

            def __getattr__(self, name):
                return getattr(asyncio, name)

        mp.asyncio = _Fast()
        pm.asyncio = _Fast()

    from app.main import app
    print(f"[live_server] pid={os.getpid()} workdir={workdir} fast={args.fast}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning", workers=1)


if __name__ == "__main__":
    main()
