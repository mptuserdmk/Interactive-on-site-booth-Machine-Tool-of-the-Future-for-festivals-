"""
Spike: 50 одновременных POST /api/session/answer color против живого сервера (H2 под нагрузкой).
Ожидание: ровно 1 ответ 200, остальные 409; ровно 1 печать.

    python tests/load/spike_color.py --port 8766 --taps 50
"""
import argparse
import asyncio
import collections
import time

import httpx


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--taps", type=int, default=50)
    args = ap.parse_args()
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{args.port}", timeout=30,
                                 limits=httpx.Limits(max_connections=args.taps)) as c:
        await c.post("/api/session/reset")
        sid = (await c.post("/api/session/new")).json()["id"]
        await c.post("/api/camera/capture")
        await c.post("/api/session/photo/confirm")
        await c.post("/api/session/answer", json={"question_type": "element", "answer_id": "metal"})
        await c.post("/api/session/answer", json={"question_type": "power", "answer_id": "speed"})
        printed0 = (await c.get("/api/print/status")).json()["total_printed"]
        body = {"question_type": "color", "answer_id": "white"}
        t0 = time.perf_counter()
        rs = await asyncio.gather(*[c.post("/api/session/answer", json=body) for _ in range(args.taps)])
        dt = time.perf_counter() - t0
        codes = collections.Counter(r.status_code for r in rs)
        for _ in range(100):
            s = (await c.get("/api/session/active")).json()
            if s and s["status"] in ("COMPLETED", "ERROR"):
                break
            await asyncio.sleep(0.2)
        await asyncio.sleep(3)
        printed = (await c.get("/api/print/status")).json()["total_printed"] - printed0
        print(f"[SPIKE] {args.taps} одновременных тапов за {dt * 1000:.0f} мс: коды={dict(codes)}; "
              f"итоговый статус={s['status']}; напечатано карточек={printed}; сессия ...{sid[-6:]}")


if __name__ == "__main__":
    asyncio.run(main())
