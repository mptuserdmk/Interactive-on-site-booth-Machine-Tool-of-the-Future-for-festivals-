"""
Soak / «500 сессий подряд»: N полных циклов через HTTP против живого сервера.
Проверяет зависшие статусы и «печать не той карточки» (по /api/print/status→total_printed и истории).

    python tests/load/live_server.py --port 8765 --fast --workdir %TEMP%\\stanok_soak
    python tests/load/monitor.py --pid <PID> --interval 5 --out docs/evidence/soak_metrics.csv --workdir %TEMP%\\stanok_soak
    python tests/load/soak.py --port 8765 --sessions 600
"""
import argparse
import random
import statistics
import time

import httpx

ANSWERS = [("element", ["space", "atom", "robots", "medicine", "metal"]),
           ("power", ["precision", "speed", "power", "mind", "care"]),
           ("color", ["azure", "gold", "emerald", "white"])]
STUCK = {"GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sessions", type=int, default=500)
    ap.add_argument("--timeout", type=float, default=30)
    args = ap.parse_args()
    c = httpx.Client(base_url=f"http://127.0.0.1:{args.port}", timeout=30)
    durations, errors, statuses = [], [], {}
    ids = []
    t_start = time.time()
    for i in range(args.sessions):
        try:
            sid = c.post("/api/session/new").json()["id"]
            ids.append(sid)
            if random.random() < 0.3:
                files = {"file": ("p.jpg", _photo(), "image/jpeg")}
                assert c.post("/api/camera/upload-ota", files=files).status_code == 200
            else:
                assert c.post("/api/camera/capture").status_code == 200
            assert c.post("/api/session/photo/confirm").status_code == 200
            for qt, opts in ANSWERS:
                r = c.post("/api/session/answer", json={"question_type": qt, "answer_id": random.choice(opts)})
                assert r.status_code == 200, r.text
            t0 = time.time()
            st = None
            while time.time() - t0 < args.timeout:
                st = c.get("/api/session/active").json()
                if st and st["status"] in ("COMPLETED", "ERROR"):
                    break
                time.sleep(0.05)
            durations.append(time.time() - t0)
            statuses[st["status"] if st else None] = statuses.get(st["status"] if st else None, 0) + 1
            c.post("/api/session/reset")
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e)[:200])
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{args.sessions} за {time.time() - t_start:.0f} с, ошибок {len(errors)}", flush=True)

    hist = c.get(f"/api/session/history?limit=200").json()
    stuck = [h for h in hist if h["status"] in STUCK]
    printed = c.get("/api/print/status").json().get("total_printed")
    d = sorted(durations)
    print(f"[SOAK] сессий={args.sessions} за {time.time() - t_start:.0f} с; статусы={statuses}; ошибок клиента={len(errors)}")
    if d:
        print(f"[SOAK] цвет→финал p50={d[len(d) // 2]:.2f} с p95={d[int(len(d) * 0.95)]:.2f} с max={d[-1]:.2f} с "
              f"mean={statistics.mean(d):.2f} с")
    print(f"[SOAK] зависших в промежуточных статусах (последние 200): {len(stuck)}; напечатано={printed}")
    for e in errors[:5]:
        print("   ", e)


_PHOTO = None


def _photo():
    global _PHOTO
    if _PHOTO is None:
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (1200, 1600), (90, 120, 160)).save(buf, "JPEG", quality=90)
        _PHOTO = buf.getvalue()
    return _PHOTO


if __name__ == "__main__":
    main()
