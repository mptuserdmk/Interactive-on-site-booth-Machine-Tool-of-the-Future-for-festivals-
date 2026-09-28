"""
Пентест (только in-process / localhost): контроль доступа (S1), публичные фото (S2),
перечисление сессий (S3), CSRF/CORS (S6), WebSocket hijacking.

Акторы:
  client        — сам киоск/оператор на ПК стенда (loopback, доверенный);
  remote_client — «чужое» устройство в Wi-Fi площадки (192.168.1.66) без секретов.
"""
import re

import pytest

from helpers import db_state, do, drive_to, make_photo_bytes, printed_session_ids

pytestmark = [pytest.mark.security, pytest.mark.regression]

EVIL = "http://evil.example"

PROTECTED = [
    ("POST", "/api/session/new", None),
    ("POST", "/api/session/reset", None),
    ("POST", "/api/session/photo/confirm", None),
    ("POST", "/api/session/photo/retake", None),
    ("POST", "/api/session/answer", {"question_type": "element", "answer_id": "space"}),
    ("GET", "/api/session/active", None),
    ("GET", "/api/session/history", None),
    ("POST", "/api/camera/capture", None),
    ("GET", "/api/camera/status", None),
    ("POST", "/api/print/trigger-active", None),
    ("POST", "/api/print/reprint", {"session_id": "sess_x"}),
    ("GET", "/api/print/status", None),
    ("GET", "/api/health", None),
    ("GET", "/operator", None),
    ("GET", "/kiosk", None),
]


@pytest.mark.parametrize("method,url,body", PROTECTED, ids=[f"{m} {u}" for m, u, _ in PROTECTED])
async def test_remote_device_without_token_is_rejected(remote_client, method, url, body):
    """S1: любой гость в Wi-Fi площадки управляет стендом."""
    r = await remote_client.request(method, url, json=body)
    assert r.status_code == 401, f"{method} {url} без токена с чужого устройства → {r.status_code}"


async def test_remote_upload_without_token_is_rejected(remote_client):
    r = await remote_client.post("/api/camera/upload-ota", files={"file": ("x.jpg", make_photo_bytes(), "image/jpeg")})
    assert r.status_code == 401


async def test_remote_reprint_dos_blocked(client, remote_client, fast_pipeline):
    """S1: «reprint ×100» с телефона гостя = 100 карточек на бумаге."""
    sid = await drive_to(client, "COMPLETED")
    hist = await remote_client.get("/api/session/history")
    ids = [h["id"] for h in hist.json()] if hist.status_code == 200 else [sid]
    for _ in range(20):
        await remote_client.post("/api/print/reprint", json={"session_id": ids[0]})
    assert printed_session_ids() == [sid], f"гость напечатал {len(printed_session_ids()) - 1} лишних карточек"


async def test_operator_token_grants_access(remote_client):
    from app.config.settings import settings
    token = settings.ACCESS_TOKEN
    assert token and len(token) >= 12
    r = await remote_client.get("/api/session/history", headers={"X-Access-Token": token})
    assert r.status_code == 200
    r = await remote_client.get(f"/operator?token={token}", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "httponly" in r.headers.get("set-cookie", "").lower()
    assert "samesite=strict" in r.headers.get("set-cookie", "").lower()
    r = await remote_client.get("/operator")
    assert r.status_code == 200


async def test_wrong_token_rejected(remote_client):
    r = await remote_client.get("/api/session/history", headers={"X-Access-Token": "guess"})
    assert r.status_code == 401


async def test_camera_token_only_allows_upload(remote_client):
    from app.config.settings import settings
    ct = settings.CAMERA_TOKEN
    assert ct and ct != settings.ACCESS_TOKEN
    r = await remote_client.get(f"/mobile-camera?token={ct}", follow_redirects=False)
    assert r.status_code in (302, 303)
    r = await remote_client.post("/api/camera/upload-ota", files={"file": ("x.jpg", make_photo_bytes(), "image/jpeg")})
    assert r.status_code == 200, r.text
    for method, url, body in [("POST", "/api/session/reset", None), ("GET", "/api/session/history", None),
                              ("POST", "/api/print/reprint", {"session_id": "x"})]:
        r = await remote_client.request(method, url, json=body)
        assert r.status_code == 401, f"камерный токен открыл {url}"


async def test_guest_can_open_own_card(client, remote_client, fast_pipeline):
    sid = await drive_to(client, "COMPLETED")
    r = await remote_client.get(f"/card/{sid}")
    assert r.status_code == 200
    img = re.search(r'<img src="([^"]+)"', r.text)
    assert img, "на странице карточки нет изображения"
    r = await remote_client.get(img.group(1))
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/")


# --- S2: /storage как публичная статика ----------------------------------------------------

async def test_raw_child_photo_not_publicly_accessible(client, remote_client, fast_pipeline):
    """S2: сырое фото ребёнка доступно любому по /storage/photos/{id}_raw.jpg."""
    sid = await drive_to(client, "QUIZ_ELEMENT")
    for url in (f"/storage/photos/{sid}_raw.jpg", f"/media/photos/{sid}.jpg"):
        r = await remote_client.get(url)
        assert r.status_code in (401, 404), f"{url} → {r.status_code} ({len(r.content)} байт фото ребёнка)"


async def test_generated_face_not_publicly_accessible(remote_client):
    from app.config.settings import settings
    p = settings.GENERATED_DIR / "sess_leak_ai.jpg"
    p.write_bytes(make_photo_bytes())
    r = await remote_client.get("/storage/generated/sess_leak_ai.jpg")
    assert r.status_code in (401, 404), f"/storage/generated → {r.status_code}"


async def test_kiosk_can_see_raw_photo_for_review(client, fast_pipeline):
    sid = await drive_to(client, "PHOTO_TAKEN")
    r = await client.get(f"/media/photos/{sid}.jpg")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"


async def test_storage_directory_listing_disabled(client):
    for url in ("/storage/", "/storage/photos/", "/media/photos/", "/media/cards/"):
        r = await client.get(url)
        assert r.status_code != 200 or "<a href" not in r.text


# --- S3: предсказуемые ID + история ----------------------------------------------------------

async def test_session_id_is_unguessable(client):
    """S3: sess_YYYYMMDDHHMMSS_ + 4 hex = 65 536 вариантов на секунду."""
    from datetime import datetime
    ids = [(await do(client, "new")).json()["id"] for _ in range(20)]
    today = datetime.now().strftime("%Y%m%d")
    assert all(today not in i for i in ids), ids[:3]
    assert all(re.fullmatch(r"sess_[0-9a-f]{32}", i) for i in ids), ids[:3]
    assert len(set(ids)) == len(ids)


# --- S6: CORS / CSRF / WebSocket Origin ------------------------------------------------------

async def test_cors_does_not_reflect_foreign_origin(client):
    r = await client.options("/api/session/reset", headers={
        "Origin": EVIL, "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") not in (EVIL, "*"), dict(r.headers)
    r = await client.get("/api/session/history", headers={"Origin": EVIL})
    assert r.headers.get("access-control-allow-origin") not in (EVIL, "*")


async def test_csrf_from_foreign_origin_blocked_even_on_loopback(client, fast_pipeline):
    """Вредный сайт, открытый в браузере на ПК стенда, шлёт POST на http://localhost:8000 (no-cors)."""
    sid = await drive_to(client, "QUIZ_POWER")
    r = await client.post("/api/session/reset", headers={"Origin": EVIL})
    assert r.status_code == 403
    assert db_state(sid)()["status"] == "QUIZ_POWER"


async def test_same_origin_post_allowed(client):
    r = await client.post("/api/session/new", headers={"Origin": "http://testserver"})
    assert r.status_code == 200


def test_websocket_rejects_foreign_origin(sync_client):
    """Cross-Site WebSocket Hijacking: чужая страница подписывается на /ws и читает сессии."""
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with sync_client.websocket_connect("/ws", headers={"origin": EVIL}) as ws:
            ws.send_text('{"action":"PING"}')
            ws.receive_text()


def test_websocket_rejects_remote_without_token(remote_sync_client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with remote_sync_client.websocket_connect("/ws") as ws:
            ws.send_text('{"action":"PING"}')
            ws.receive_text()


def test_websocket_same_origin_works(sync_client):
    with sync_client.websocket_connect("/ws", headers={"origin": "http://testserver"}) as ws:
        ws.send_text('{"action":"PING"}')
        assert "PONG" in ws.receive_text()


# --- Rate limit печати ------------------------------------------------------------------------

async def test_reprint_rate_limited(client, fast_pipeline):
    sid = await drive_to(client, "COMPLETED")
    r1 = await client.post("/api/print/reprint", json={"session_id": sid})
    r2 = await client.post("/api/print/reprint", json={"session_id": sid})
    assert r1.status_code == 200 and r1.json()["success"] is True
    assert r2.status_code == 429, f"повторная допечатка сразу же: {r2.status_code}"
