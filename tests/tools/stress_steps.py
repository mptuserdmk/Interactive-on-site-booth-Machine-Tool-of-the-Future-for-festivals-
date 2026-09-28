"""Сводка стресс-теста по ступеням: p50/p95/ошибки агрегата и CPU/RSS сервера.
    python tests/tools/stress_steps.py docs/evidence/locust/stress_stats_history.csv docs/evidence/stress_server_metrics.csv
"""
import csv
import sys
from collections import defaultdict


def main(hist_path, metrics_path=None):
    rows = [r for r in csv.DictReader(open(hist_path, encoding="utf-8")) if r["Name"] == "Aggregated"]
    by_users = defaultdict(list)
    for r in rows:
        by_users[int(r["User Count"])].append(r)
    t0 = int(rows[0]["Timestamp"]) if rows else 0
    metrics = list(csv.DictReader(open(metrics_path, encoding="utf-8"))) if metrics_path else []
    print("VU | RPS | p50 мс | p95 мс | p99 мс | ошибок/с | CPU сервера % ядра (макс) | RSS МБ")
    prev_t = None
    for users in sorted(by_users):
        rs = by_users[users]
        last = rs[-1]
        ts = [int(r["Timestamp"]) - t0 for r in rs]
        cpu = [float(m["cpu_pct_one_core"]) for m in metrics
               if metrics and min(ts) - 5 <= float(m["t_s"]) - (0 if prev_t is None else 0) <= max(ts) + 5]
        rss = [float(m["rss_mb"]) for m in metrics if min(ts) - 5 <= float(m["t_s"]) <= max(ts) + 5]
        print(f"{users} | {float(last['Requests/s']):.1f} | {last['50%']} | {last['95%']} | {last['99%']} | "
              f"{float(last['Failures/s']):.2f} | {max(cpu) if cpu else '-'} | {max(rss) if rss else '-'}")
    total = rows[-1]
    print(f"Итого запросов: {total['Total Request Count']}, ошибок: {total['Total Failure Count']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:])
