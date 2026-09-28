"""
WS: N одновременных клиентов /ws, задержка broadcast и утечки соединений.

    python tests/load/ws_bench.py --port 8765 --clients 50 --rounds 20 [--pid SERVER_PID]

Латентность = от отправки HTTP-запроса, меняющего сессию, до получения SESSION_UPDATE каждым клиентом.
"""
import argparse
import asyncio
import json
import statistics
import time

import httpx
import psutil
import websockets


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--clients", type=int, default=50)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--pid", type=int, default=None)
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    wsurl = f"ws://127.0.0.1:{args.port}/ws"
    proc = psutil.Process(args.pid) if args.pid else None
    h0 = proc.num_handles() if proc else None

    conns = [await websockets.connect(wsurl, open_timeout=20) for _ in range(args.clients)]
    # выбрать стартовое сообщение (если есть активная сессия)
    for c in conns:
        try:
            await asyncio.wait_for(c.recv(), 0.2)
        except asyncio.TimeoutError:
            pass
    h1 = proc.num_handles() if proc else None

    latencies = []
    async with httpx.AsyncClient(base_url=base, timeout=30) as http:
        await http.post("/api/session/new")
        for _ in range(args.rounds):
            async def recv_one(c, t0):
                while True:
                    msg = json.loads(await asyncio.wait_for(c.recv(), 10))
                    if msg.get("type") == "SESSION_UPDATE":
                        return time.perf_counter() - t0
            t0 = time.perf_counter()
            waiters = [asyncio.create_task(recv_one(c, t0)) for c in conns]
            r = await http.post("/api/camera/capture")
            assert r.status_code == 200, r.text
            res = await asyncio.gather(*waiters, return_exceptions=True)
            latencies += [x for x in res if isinstance(x, float)]
            lost = sum(1 for x in res if not isinstance(x, float))
            if lost:
                print(f"  раунд: {lost} клиентов не получили сообщение")
            await asyncio.sleep(0.1)
        await http.post("/api/session/reset")

    for c in conns:
        await c.close()
    await asyncio.sleep(2)
    h2 = proc.num_handles() if proc else None

    lat = sorted(latencies)
    p = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))] * 1000  # noqa: E731
    print(f"[WS] клиентов={args.clients} раундов={args.rounds} доставок={len(lat)}/{args.clients * args.rounds}")
    print(f"[WS] broadcast p50={p(0.5):.0f} мс p95={p(0.95):.0f} мс max={lat[-1] * 1000:.0f} мс "
          f"mean={statistics.mean(lat) * 1000:.0f} мс")
    if proc:
        print(f"[WS] handles сервера: до={h0} с {args.clients} клиентами={h1} после закрытия={h2}")


if __name__ == "__main__":
    asyncio.run(main())
