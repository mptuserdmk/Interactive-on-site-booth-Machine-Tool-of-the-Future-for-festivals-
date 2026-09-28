"""SVG-график метрик процесса из monitor.py (без внешних зависимостей).
    python tests/tools/plot_metrics.py docs/evidence/soak_metrics.csv docs/evidence/soak_metrics.svg
"""
import csv
import sys

SERIES = [("rss_mb", "RSS, МБ", "#2a6fdb"), ("handles", "handles", "#d9480f"),
          ("threads", "потоки", "#2b8a3e"), ("storage_mb", "storage, МБ", "#862e9c")]


def main(src, dst):
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    t = [float(r["t_s"]) / 60 for r in rows]
    w, h, pad = 900, 150, 50
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{(h + 40) * len(SERIES) + 20}" '
           f'font-family="Segoe UI, sans-serif" font-size="12"><rect width="100%" height="100%" fill="white"/>']
    for i, (key, label, color) in enumerate(SERIES):
        y0 = 20 + i * (h + 40)
        vals = [float(r[key]) for r in rows]
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        pts = " ".join(f"{pad + (tt - t[0]) / ((t[-1] - t[0]) or 1) * (w - 2 * pad):.1f},"
                       f"{y0 + h - (v - lo) / span * h:.1f}" for tt, v in zip(t, vals))
        out.append(f'<text x="{pad}" y="{y0 - 5}" fill="{color}">{label}: мин {lo:g}, макс {hi:g}, '
                   f'начало {vals[0]:g}, конец {vals[-1]:g}</text>')
        out.append(f'<rect x="{pad}" y="{y0}" width="{w - 2 * pad}" height="{h}" fill="none" stroke="#ccc"/>')
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5"/>')
        out.append(f'<text x="{pad}" y="{y0 + h + 15}" fill="#666">0 мин</text>'
                   f'<text x="{w - pad - 60}" y="{y0 + h + 15}" fill="#666">{t[-1] - t[0]:.0f} мин</text>')
    out.append("</svg>")
    open(dst, "w", encoding="utf-8").write("\n".join(out))
    print(dst)


if __name__ == "__main__":
    main(*sys.argv[1:])
