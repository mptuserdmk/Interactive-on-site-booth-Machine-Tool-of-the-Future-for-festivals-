"""
H13/H14: блокирующий код в async-обработчиках и стоимость кадра MJPEG.
Меряем «задержку event loop»: фоновая корутина тикает каждые 5 мс, максимум просрочки = lag.
"""
import asyncio
import os
import time

import pytest

from helpers import do, drive_to, make_photo_bytes

# Замеры времени бессмысленны при параллельном прогоне (-n N) и под трассировкой coverage:
# запускать отдельно: pytest -m load -p no:xdist
pytestmark = [
    pytest.mark.load,
    pytest.mark.skipif(bool(os.environ.get("PYTEST_XDIST_WORKER")), reason="замер задержки — только последовательно"),
]


class LoopLag:
    def __init__(self, period=0.005):
        self.period = period
        self.max_lag = 0.0
        self._stop = False

    async def run(self):
        loop = asyncio.get_running_loop()
        while not self._stop:
            t = loop.time()
            await asyncio.sleep(self.period)
            self.max_lag = max(self.max_lag, loop.time() - t - self.period)

    async def __aenter__(self):
        self._task = asyncio.create_task(self.run())
        await asyncio.sleep(0.02)
        return self

    async def __aexit__(self, *exc):
        self._stop = True
        await self._task


@pytest.mark.regression
async def test_pipeline_does_not_block_event_loop(client, fast_print):
    """H13: Pillow-композиция и mock-обработка в event loop → MJPEG/WS замирают."""
    from helpers import db_state, wait_for_status
    sid = await drive_to(client, "QUIZ_COLOR")
    async with LoopLag() as lag:
        await do(client, "color")
        await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=20)
    print(f"\n[H13] max event-loop lag во время генерации+композиции: {lag.max_lag * 1000:.0f} мс")
    assert lag.max_lag < 0.1


@pytest.mark.regression
async def test_upload_processing_does_not_block_event_loop(client):
    photo = make_photo_bytes(size=(4000, 3000))
    async with LoopLag() as lag:
        r = await client.post("/api/camera/upload-ota", files={"file": ("p.jpg", photo, "image/jpeg")})
    assert r.status_code == 200
    print(f"\n[H13] max lag при загрузке 12 МП: {lag.max_lag * 1000:.0f} мс")
    assert lag.max_lag < 0.1


async def test_capture_lag(client):
    async with LoopLag() as lag:
        r = await do(client, "capture")
    assert r.status_code == 200
    print(f"\n[H13] max lag при capture (mock-кадр): {lag.max_lag * 1000:.0f} мс")
    assert lag.max_lag < 0.1


@pytest.mark.regression
def test_mock_frame_cost():
    """H14: generate_mock_frame() — Python-цикл по 720 строкам на КАЖДЫЙ кадр КАЖДОГО клиента."""
    from app.camera.manager import camera_manager
    camera_manager.read_frame()
    n = 60
    t0 = time.perf_counter()
    for _ in range(n):
        camera_manager.read_frame()
    per_frame = (time.perf_counter() - t0) / n
    print(f"\n[H14] read_frame() без камеры: {per_frame * 1000:.2f} мс/кадр "
          f"→ 3 клиента × 20 FPS = {per_frame * 60 * 100:.0f}% одного ядра только на генерацию кадра")
    assert per_frame < 0.002
