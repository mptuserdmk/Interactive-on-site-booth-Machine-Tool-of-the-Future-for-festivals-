"""
Контроль доступа к стенду (S1, S6).

Модель доверия:
  - loopback (127.0.0.1 / ::1) — сам ПК стенда: браузер киоска и оператор на этом же ПК;
  - остальные устройства в Wi-Fi площадки — только с токеном:
      ACCESS_TOKEN — полный доступ (ноутбук оператора, планшет-киоск),
      CAMERA_TOKEN — только /mobile-camera и загрузка фото (QR на панели оператора);
    токен передаётся один раз в ?token=..., дальше живёт в HttpOnly SameSite=Strict cookie,
    либо заголовком X-Access-Token (скрипты, мониторинг);
  - публично: страница карточки /card/{id} и её изображение /media/cards/{id}.jpg (id неугадываемый),
    статика /static/*;
  - CSRF / Cross-Site WebSocket Hijacking: небезопасные методы и WebSocket с Origin другого хоста → 403,
    даже с loopback (вредный сайт, открытый в браузере на ПК стенда).
"""
import secrets
from urllib.parse import urlencode, urlparse, parse_qsl

from starlette.datastructures import Headers
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config.settings import settings

COOKIE_FULL = "stanok_access"
COOKIE_CAMERA = "stanok_camera"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
PUBLIC_PREFIXES = ("/static/", "/card/", "/media/cards/")
PUBLIC_PATHS = {"/favicon.ico"}
CAMERA_PATHS = {"/mobile-camera", "/api/camera/upload-ota"}
LOOPBACK = {"127.0.0.1", "::1"}
COOKIE_MAX_AGE = 3 * 24 * 3600


def _same_origin(origin: str, host: str | None) -> bool:
    if not host or origin == "null":
        return False
    return urlparse(origin).netloc.lower() == host.lower()


def _match(value: str | None, expected: str) -> bool:
    return bool(value) and bool(expected) and secrets.compare_digest(value, expected)


def access_level(client_host: str | None, headers: Headers, cookies: dict) -> str | None:
    if settings.TRUST_LOOPBACK and client_host in LOOPBACK:
        return "full"
    header_token = headers.get("x-access-token")
    if _match(header_token, settings.ACCESS_TOKEN) or _match(cookies.get(COOKIE_FULL), settings.ACCESS_TOKEN):
        return "full"
    if _match(header_token, settings.CAMERA_TOKEN) or _match(cookies.get(COOKIE_CAMERA), settings.CAMERA_TOKEN):
        return "camera"
    return None


def _cookies(headers: Headers) -> dict:
    out = {}
    for part in headers.get("cookie", "").split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            out[k] = v
    return out


class AccessControlMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        headers = Headers(scope=scope)
        path = scope["path"]
        is_ws = scope["type"] == "websocket"
        method = scope.get("method", "GET")

        origin = headers.get("origin")
        if origin and (is_ws or method not in SAFE_METHODS) and not _same_origin(origin, headers.get("host")):
            return await self._deny(scope, receive, send, 403, "Запрос с чужого сайта отклонён")

        if not is_ws and (path.startswith(PUBLIC_PREFIXES) or path in PUBLIC_PATHS):
            return await self.app(scope, receive, send)

        # Одноразовая передача токена в ссылке/QR → cookie и редирект на чистый URL
        if not is_ws and method == "GET":
            query = dict(parse_qsl(scope.get("query_string", b"").decode("latin-1")))
            token = query.pop("token", None)
            if token:
                if _match(token, settings.ACCESS_TOKEN):
                    cookie = COOKIE_FULL
                elif _match(token, settings.CAMERA_TOKEN):
                    cookie = COOKIE_CAMERA
                else:
                    cookie = None
                if cookie:
                    target = path + ("?" + urlencode(query) if query else "")
                    resp = RedirectResponse(target, status_code=303)
                    resp.set_cookie(cookie, token, max_age=COOKIE_MAX_AGE, httponly=True, samesite="strict")
                    return await resp(scope, receive, send)

        level = access_level(scope.get("client", (None,))[0], headers, _cookies(headers))
        if level == "full" or (level == "camera" and path in CAMERA_PATHS):
            return await self.app(scope, receive, send)
        return await self._deny(scope, receive, send, 401, "Нужен код доступа стенда")

    @staticmethod
    async def _deny(scope, receive, send, status: int, message: str):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 4403 if status == 403 else 4401})
            return
        if scope["path"].startswith("/api/"):
            resp = JSONResponse({"detail": message}, status_code=status)
        else:
            resp = HTMLResponse(
                f"<!doctype html><meta charset='utf-8'><title>Доступ</title>"
                f"<body style='font-family:sans-serif;padding:40px'><h2>{message}</h2>"
                f"<p>Откройте ссылку с кодом доступа (он печатается в консоли стенда при запуске) "
                f"или отсканируйте QR на панели оператора.</p></body>",
                status_code=status)
        await resp(scope, receive, send)
