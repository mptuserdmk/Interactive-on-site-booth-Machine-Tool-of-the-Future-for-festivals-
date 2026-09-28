"""
Офлайн-режим киоска (S10): скачивает закреплённые версии React, ReactDOM, Babel Standalone и Tailwind Play CDN
в frontend/static/vendor/. После этого kiosk.html грузит их локально и работает без интернета.

    python scripts\\vendor_frontend.py            # скачать и записать SHA-256 в vendor/SHA256SUMS
    python scripts\\vendor_frontend.py --verify   # проверить, что файлы не изменились

Запускать один раз при подготовке стенда (нужен интернет), затем закоммитить vendor/ вместе с SHA256SUMS.
Долгосрочно правильнее собрать фронт Vite-ом (JSX → JS заранее, Tailwind → CSS), отказавшись от Babel в браузере.
"""
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

VENDOR = Path(__file__).resolve().parent.parent / "frontend" / "static" / "vendor"
FILES = {
    "react-18.3.1.production.min.js": "https://unpkg.com/react@18.3.1/umd/react.production.min.js",
    "react-dom-18.3.1.production.min.js": "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js",
    "babel-standalone-7.26.10.min.js": "https://unpkg.com/@babel/standalone@7.26.10/babel.min.js",
    "tailwindcss-3.4.17.js": "https://cdn.tailwindcss.com/3.4.17",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def download():
    VENDOR.mkdir(parents=True, exist_ok=True)
    lines = []
    for name, url in FILES.items():
        if not url.startswith("https://"):
            raise SystemExit(f"только https: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "stanok-vendor/1.0"})  # noqa: S310
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310  # nosec B310 — только https-URL из FILES
            data = resp.read()
        if len(data) < 10_000 or data.lstrip()[:1] == b"<":
            raise SystemExit(f"{url}: подозрительный ответ ({len(data)} байт)")
        (VENDOR / name).write_bytes(data)
        lines.append(f"{sha256(VENDOR / name)}  {name}  {url}")
        print(f"OK {name}: {len(data)} байт")
    (VENDOR / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify() -> bool:
    sums = VENDOR / "SHA256SUMS"
    if not sums.exists():
        print("нет SHA256SUMS")
        return False
    ok = True
    for line in sums.read_text(encoding="utf-8").splitlines():
        digest, name = line.split()[:2]
        p = VENDOR / name
        good = p.exists() and sha256(p) == digest
        ok &= good
        print(("OK  " if good else "BAD ") + name)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        sys.exit(0 if verify() else 1)
    download()
