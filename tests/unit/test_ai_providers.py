"""
AI-провайдеры (H7, H8, H9) и валидация ответов. Сеть полностью замокана respx:
любой незамоканный запрос падает, реальные платные API не вызываются.
"""
import io
import json

import httpx
import pytest
import respx
from PIL import Image

from helpers import make_photo_bytes, write_photo

pytestmark = [pytest.mark.unit, pytest.mark.respx(assert_all_mocked=True, assert_all_called=False)]

BOTHUB_EDIT = "https://openai.bothub.chat/v1/images/edits"
BOTHUB_GEN = "https://openai.bothub.chat/v1/images/generations"
FAL_URL = "https://fal.run/fal-ai/flux/dev/image-to-image"
REPL_URL = "https://api.replicate.com/v1/predictions"
IMG_URL = "https://cdn.example.test/out.png"


def png_bytes(size=(512, 512)):
    buf = io.BytesIO()
    Image.new("RGB", size, (10, 200, 120)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def req(tmp_path):
    from app.ai.models import AIGenerationRequest
    photo = write_photo(tmp_path / "in.jpg")
    return AIGenerationRequest(session_id="sess_test", element="space", power="precision", color="azure",
                               prompt="p", input_photo_path=str(photo))


@pytest.fixture
def combo():
    from app.quiz.combinations import combination_manager
    return combination_manager.find("space", "precision", "azure")


@pytest.fixture
def api_key(monkeypatch):
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-test-0123456789abcdef")
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 2)


def provider(name):
    from app.ai.manager import ai_manager
    return ai_manager.providers[name]


def is_image(path):
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


# --- Успешные пути ------------------------------------------------------------------------

async def test_bothub_success_url(respx_mock, req, combo, api_key, tmp_path):
    respx_mock.post(BOTHUB_EDIT).respond(200, json={"data": [{"url": IMG_URL}]})
    respx_mock.get(IMG_URL).respond(200, content=png_bytes(), headers={"content-type": "image/png"})
    res = await provider("bothub").generate(req, combo, tmp_path / "out.jpg")
    assert res.success, res.error
    assert is_image(res.image_path)


async def test_bothub_success_b64(respx_mock, req, combo, api_key, tmp_path):
    import base64
    respx_mock.post(BOTHUB_EDIT).respond(200, json={"data": [{"b64_json": base64.b64encode(png_bytes()).decode()}]})
    res = await provider("bothub").generate(req, combo, tmp_path / "out.jpg")
    assert res.success, res.error


async def test_fal_success(respx_mock, req, combo, api_key, tmp_path):
    respx_mock.post(FAL_URL).respond(200, json={"images": [{"url": IMG_URL}]})
    respx_mock.get(IMG_URL).respond(200, content=png_bytes())
    res = await provider("fal").generate(req, combo, tmp_path / "out.jpg")
    assert res.success, res.error


@pytest.mark.regression
async def test_replicate_success_no_nameerror(respx_mock, req, combo, api_key, tmp_path):
    """H7: в cloud_providers.py не импортирован asyncio → NameError → всегда тихий fallback."""
    respx_mock.post(REPL_URL).respond(201, json={"urls": {"get": "https://api.replicate.com/v1/predictions/p1"}})
    respx_mock.get("https://api.replicate.com/v1/predictions/p1").respond(
        200, json={"status": "succeeded", "output": [IMG_URL]})
    respx_mock.get(IMG_URL).respond(200, content=png_bytes())
    res = await provider("replicate").generate(req, combo, tmp_path / "out.jpg")
    assert res.success, f"Replicate упал: {res.error}"


# --- Ошибочные ответы: провайдер обязан вернуть success=False (чтобы сработал fallback) ------

BAD_RESPONSES = {
    "http_401": lambda: httpx.Response(401, json={"error": "invalid key"}),
    "http_429": lambda: httpx.Response(429, json={"error": "rate limit"}),
    "http_500": lambda: httpx.Response(500, text="Internal Server Error"),
    "empty_data": lambda: httpx.Response(200, json={"data": []}),
    "broken_json": lambda: httpx.Response(200, text="{not json"),
    "no_url_no_b64": lambda: httpx.Response(200, json={"data": [{"revised_prompt": "x"}]}),
}


@pytest.mark.parametrize("case", list(BAD_RESPONSES))
async def test_bothub_bad_responses_fail_cleanly(respx_mock, req, combo, api_key, tmp_path, case):
    respx_mock.post(BOTHUB_EDIT).mock(side_effect=lambda request: BAD_RESPONSES[case]())
    res = await provider("bothub").generate(req, combo, tmp_path / "out.jpg")
    assert res.success is False
    assert res.error


async def test_bothub_timeout_fails_cleanly(respx_mock, req, combo, api_key, tmp_path):
    respx_mock.post(BOTHUB_EDIT).mock(side_effect=httpx.ReadTimeout("timeout"))
    res = await provider("bothub").generate(req, combo, tmp_path / "out.jpg")
    assert res.success is False


@pytest.mark.regression
@pytest.mark.parametrize("download", ["404", "html", "huge"])
async def test_bothub_bad_download_is_failure_not_success(respx_mock, req, combo, api_key, tmp_path, download):
    """Новая находка: провайдер пишет в *_ai.jpg всё, что вернул URL (404-страницу, HTML, 30 МБ мусора),
    и возвращает success=True. Тогда fallback НЕ срабатывает, а композиция падает → ERROR."""
    respx_mock.post(BOTHUB_EDIT).respond(200, json={"data": [{"url": IMG_URL}]})
    if download == "404":
        respx_mock.get(IMG_URL).respond(404, text="Not Found")
    elif download == "html":
        respx_mock.get(IMG_URL).respond(200, text="<html><body>Cloudflare</body></html>",
                                   headers={"content-type": "text/html"})
    else:
        respx_mock.get(IMG_URL).respond(200, content=b"\xff" * (30 * 1024 * 1024))
    res = await provider("bothub").generate(req, combo, tmp_path / "out.jpg")
    assert res.success is False, f"{download}: провайдер вернул success=True для не-изображения"


# --- Fallback и его видимость (H8) -----------------------------------------------------------

@pytest.mark.regression
async def test_fallback_to_mock_is_flagged(respx_mock, req, combo, api_key, tmp_path, monkeypatch, fast_mock_ai):
    from app.ai.manager import ai_manager
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_PROVIDER", "bothub")
    respx_mock.post(BOTHUB_EDIT).respond(500, text="boom")
    res = await ai_manager.generate_image(req, combo, tmp_path / "out.jpg")
    assert res.success and res.is_fallback
    assert res.provider_name == "mock"


@pytest.mark.regression
async def test_fallback_visible_in_session_and_health(respx_mock, client, fast_pipeline, monkeypatch):
    """H8: fallback на mock не виден ни в сессии, ни в /api/health — весь день печатаются «фейки»."""
    from app.config.settings import settings
    from helpers import db_state, drive_to, wait_for_status
    monkeypatch.setattr(settings, "AI_PROVIDER", "bothub")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-test-0123456789abcdef")
    respx_mock.post(BOTHUB_EDIT).respond(503, text="upstream down")
    respx_mock.post(BOTHUB_GEN).respond(503, text="upstream down")
    sid = await drive_to(client, "COMPLETED")
    sess = db_state(sid)()
    meta = json.loads(sess.get("meta_json") or "{}")
    assert meta.get("ai_fallback") is True, f"в сессии нет признака fallback: meta={meta}"
    health = (await client.get("/api/health")).json()
    ai = health["diagnostics"]["ai"]
    assert ai.get("fallback_count", 0) >= 1, ai
    assert ai["ok"] is False, "health показывает AI OK, хотя последняя генерация ушла в mock"


# --- Конфигурация ключа (H9) -----------------------------------------------------------------

@pytest.mark.regression
@pytest.mark.parametrize("key", ["ваш_bothub_api_ключ", "your_api_key_here", "   ", "sk-abc\n"])
async def test_placeholder_or_invalid_key_is_not_healthy(monkeypatch, key):
    """H9: плейсхолдер из .env.example даёт health OK."""
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_API_KEY", key)
    for name in ("bothub", "fal", "replicate"):
        assert await provider(name).health_check() is False, f"{name}: ключ {key!r} считается рабочим"


async def test_valid_looking_key_is_healthy(monkeypatch):
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-live-0123456789abcdefABCDEF")
    assert await provider("bothub").health_check() is True


async def test_placeholder_key_never_reaches_provider(respx_mock, req, combo, monkeypatch, tmp_path):
    """Доказательство H9: с ключом-плейсхолдером (кириллица) httpx не может даже собрать заголовок
    Authorization → запрос не уходит, результат — ошибка (→ тихий fallback на mock)."""
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_API_KEY", "ваш_bothub_api_ключ")
    route = respx_mock.post(BOTHUB_EDIT).respond(200, json={"data": [{"url": IMG_URL}]})
    res = await provider("bothub").generate(req, combo, tmp_path / "out.jpg")
    assert res.success is False
    assert route.called is False
    print(f"\n[H9] ошибка провайдера с ключом из .env.example: {res.error}")


async def test_unknown_provider_uses_mock(monkeypatch):
    from app.ai.manager import ai_manager
    from app.config.settings import settings
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    assert ai_manager.get_active_provider().name == "mock"


# --- Mock-провайдер на разных входах ------------------------------------------------------------

@pytest.mark.parametrize("kind", ["missing", "cmyk", "rgba_png", "tiny", "not_image"])
async def test_mock_provider_inputs(tmp_path, fast_mock_ai, combo, kind):
    from app.ai.mock_provider import MockProvider
    from app.ai.models import AIGenerationRequest
    p = tmp_path / "in.bin"
    if kind == "cmyk":
        p.write_bytes(make_photo_bytes(mode="CMYK"))
    elif kind == "rgba_png":
        p.write_bytes(make_photo_bytes(mode="RGBA", fmt="PNG"))
    elif kind == "tiny":
        p.write_bytes(make_photo_bytes(size=(1, 1)))
    elif kind == "not_image":
        p.write_bytes(b"GIF89a-not-really")
    r = AIGenerationRequest(session_id="s", element="space", power="precision", color="azure", prompt="p",
                            input_photo_path=str(p))
    res = await MockProvider().generate(r, combo, tmp_path / "out.jpg")
    if kind == "not_image":
        assert res.success is False
    else:
        assert res.success, res.error
