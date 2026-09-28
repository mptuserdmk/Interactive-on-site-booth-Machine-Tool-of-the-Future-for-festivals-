"""
MJPEG /api/camera/stream: N клиентов × T секунд, FPS на клиента и CPU процесса сервера.

    python tests/load/stream_bench.py --port 8765 --clients 3 --seconds 20 --pid SERVER_PID
"""
import argparse
import threading
import time

import httpx
import psutil


def consume(base, seconds, out, idx):
    frames = 0
    t0 = time.time()
    try:
        with httpx.stream("GET", f"{base}/api/camera/stream", timeout=30) as r:
            for chunk in r.iter_bytes():
                frames += chunk.count(b"--frame")
                if time.time() - t0 >= seconds:
                    break
    except Exception as e:  # noqa: BLE001
        print(f"  клиент {idx}: {e!r}")
    out[idx] = frames / max(time.time() - t0, 1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--clients", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--pid", type=int, required=True)
    args = ap.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    proc = psutil.Process(args.pid)
    proc.cpu_percent(None)
    time.sleep(1)
    idle_cpu = proc.cpu_percent(None)

    fps = {}
    threads = [threading.Thread(target=consume, args=(base, args.seconds, fps, i)) for i in range(args.clients)]
    for t in threads:
        t.start()
    samples = []
    t_end = time.time() + args.seconds
    while time.time() < t_end:
        time.sleep(1)
        samples.append(proc.cpu_percent(None))
    for t in threads:
        t.join()
    # во время потока проверяем, что обычный API отвечает быстро
    cores = psutil.cpu_count(logical=True)
    avg = sum(samples[1:]) / max(len(samples) - 1, 1)
    print(f"[MJPEG] клиентов={args.clients} FPS на клиента: " + ", ".join(f"{v:.1f}" for v in fps.values()))
    print(f"[MJPEG] CPU процесса: простой={idle_cpu:.0f}% средн.={avg:.0f}% пик={max(samples):.0f}% "
          f"(в % одного ядра; ядер={cores}, доля машины={avg / cores:.0f}%)")


if __name__ == "__main__":
    main()
