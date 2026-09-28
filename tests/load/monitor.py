"""
Мониторинг процесса сервера (psutil): RSS, CPU, handles/FD, потоки, размер storage и БД.

    python tests/load/monitor.py --pid 1234 --interval 2 --out docs/evidence/soak_metrics.csv [--workdir DIR]
Останавливается, когда процесс завершается (или по Ctrl+C).
"""
import argparse
import csv
import time
from pathlib import Path

import psutil


def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    proc = psutil.Process(args.pid)
    proc.cpu_percent(None)
    wd = Path(args.workdir) if args.workdir else None
    t0 = time.time()
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "rss_mb", "cpu_pct_one_core", "handles", "threads", "storage_mb", "db_kb", "files"])
        while proc.is_running():
            try:
                time.sleep(args.interval)
                with proc.oneshot():
                    rss = proc.memory_info().rss / 2**20
                    cpu = proc.cpu_percent(None)
                    handles = proc.num_handles() if hasattr(proc, "num_handles") else proc.num_fds()
                    threads = proc.num_threads()
                storage = dir_size(wd / "storage") / 2**20 if wd else 0
                db_kb = ((wd / "kiosk.db").stat().st_size / 1024) if wd and (wd / "kiosk.db").exists() else 0
                nfiles = sum(1 for x in (wd / "storage").rglob("*") if x.is_file()) if wd else 0
                w.writerow([round(time.time() - t0, 1), round(rss, 1), round(cpu, 1), handles, threads,
                            round(storage, 1), round(db_kb, 1), nfiles])
                f.flush()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break


if __name__ == "__main__":
    main()
