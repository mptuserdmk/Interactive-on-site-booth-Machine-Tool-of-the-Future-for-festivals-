"""
Утечки информации (S8, S9), XSS (S7, S13), supply chain (S10, S12).
"""
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from helpers import db_state, do, drive_to, wait_for_status

pytestmark = [pytest.mark.security]

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "frontend" / "templates"


# --- S9 ---------------------------------------------------------------------------------------

@pytest.mark.regression
@pytest.mark.parametrize("url", ["/docs", "/redoc", "/openapi.json"])
async def test_api_docs_disabled_in_prod(client, url):
    r = await client.get(url)
    assert r.status_code == 404, f"{url} открыт в проде"


@pytest.mark.parametrize("url", ["/static/../.env", "/static/%2e%2e/.env", "/storage/../.env",
                                 "/static/..%5c..%5c.env", "/.env", "/static/../app/config/settings.py"])
async def test_env_and_sources_not_served(client, url):
    r = await client.get(url)
    assert r.status_code in (400, 401, 404), url
    assert "AI_API_KEY" not in r.text


# --- S8 ---------------------------------------------------------------------------------------

@pytest.mark.regression
async def test_provider_error_body_not_exposed_to_clients(client, fast_pipeline, failing_ai, broadcast_log):
    """S8: текст ответа провайдера целиком попадает в error_message и WS-broadcast всем клиентам."""
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    done = await wait_for_status(db_state(sid), {"ERROR"}, timeout=5)
    msg = done["error_message"] or ""
    assert "/srv/secret" not in msg and "stacktrace" not in msg, msg


@pytest.mark.regression
async def test_pipeline_exception_details_not_exposed(client, fast_pipeline, monkeypatch):
    from app.composition.composer import card_composer

    def boom(**kwargs):
        raise OSError(28, "No space left on device", r"C:\Users\Гусь\secret\storage\cards\x.jpg")

    monkeypatch.setattr(card_composer, "compose_card", boom)
    sid = await drive_to(client, "QUIZ_COLOR")
    await do(client, "color")
    done = await wait_for_status(db_state(sid), {"ERROR"}, timeout=5)
    assert "secret" not in (done["error_message"] or ""), done["error_message"]


async def test_500_has_no_traceback(client):
    r = await client.post("/api/session/photo/confirm")  # до фикса → необработанный ValueError
    assert "Traceback" not in r.text and "File \"" not in r.text


async def test_api_key_not_printed_to_logs(client, fast_pipeline, monkeypatch, capsys):
    import respx
    from app.config.settings import settings
    key = "sk-live-VERYSECRET-0123456789"
    monkeypatch.setattr(settings, "AI_PROVIDER", "bothub")
    monkeypatch.setattr(settings, "AI_API_KEY", key)
    with respx.mock(assert_all_called=False) as m:
        m.post("https://openai.bothub.chat/v1/images/edits").respond(401, json={"error": "bad key"})
        sid = await drive_to(client, "QUIZ_COLOR")
        await do(client, "color")
        await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=10)
    out = capsys.readouterr()
    assert key not in out.out + out.err


# --- S7 / S13 ---------------------------------------------------------------------------------

async def test_card_page_escapes_reflected_input(client):
    r = await client.get('/card/x?q="><script>alert(1)</script>')
    assert "<script>alert(1)" not in r.text
    assert '"><script>' not in r.text


@pytest.mark.regression
async def test_telegram_share_link_param_injection(client, fast_pipeline):
    """S13: ?&text=... из адресной строки подставляется в ссылку t.me без URL-кодирования."""
    sid = await drive_to(client, "COMPLETED")
    r = await client.get(f"/card/{sid}?&text=%D0%92%D0%97%D0%9B%D0%9E%D0%9C&url=https://phish.example")
    href = re.search(r'href="(https://t\.me/share/url\?[^"]+)"', r.text).group(1).replace("&amp;", "&")
    q = parse_qs(urlparse(href).query)
    assert len(q.get("text", [])) == 1 and "ВЗЛОМ" not in q["text"][0], q
    assert q.get("url") and len(q["url"]) == 1 and q["url"][0].endswith(f"/card/{sid}"), q


async def test_stored_xss_fields_rendered_via_innerhtml_are_server_controlled():
    """S7: в operator.html через innerHTML выводятся только поля, которые пишет сервер
    (combinations.json, генератор ID, state machine), и все они проходят через esc()."""
    html = (TEMPLATES / "operator.html").read_text(encoding="utf-8")
    block = html[html.index("tbody.innerHTML = list.map"):]
    block = block[: block.index(".join('')")]
    fields = set(re.findall(r"\$\{\s*(?:esc\()?item\.(\w+)", block))
    assert fields <= {"machine_name", "id", "status", "final_card_path"}, fields


async def test_answer_id_with_html_not_stored(client, fast_pipeline):
    await drive_to(client, "QUIZ_ELEMENT")
    r = await client.post("/api/session/answer", json={"question_type": "element",
                                                        "answer_id": "<img src=x onerror=alert(1)>"})
    assert r.status_code in (409, 422)


# --- S10 / S12 --------------------------------------------------------------------------------

EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["'](https?://[^"']+)|["'`](https?://api\.qrserver\.com[^"'`]*)""")


VENDORED = all((ROOT / "frontend" / "static" / "vendor" / n).exists() for n in (
    "react-18.3.1.production.min.js", "react-dom-18.3.1.production.min.js",
    "babel-standalone-7.26.10.min.js", "tailwindcss-3.4.17.js"))


@pytest.mark.regression
@pytest.mark.parametrize("page", [
    pytest.param("/kiosk", marks=pytest.mark.xfail(not VENDORED, strict=True,
                                                     reason="S10 открыт: нужен scripts/vendor_frontend.py")),
    "/operator", "/mobile-camera", "/card/sess_does_not_exist"])
async def test_pages_do_not_load_external_resources(client, page):
    """S10: без интернета киоск — белый экран (React/Babel/Tailwind с CDN), QR оператора — api.qrserver.com.
    Проверяется отрендеренный HTML: после вендоринга шаблон сам переключается на /static/vendor/."""
    html = (await client.get(page)).text
    found = []
    for m in EXTERNAL.finditer(html):
        url = m.group(1) or m.group(2)
        if url.startswith("https://t.me/share"):
            continue  # навигационная ссылка «Поделиться», не ресурс страницы
        found.append(url)
    assert found == [], f"{tpl} тянет внешние ресурсы: {found}"


@pytest.mark.regression
def test_dependencies_pinned_with_lockfile():
    """S12: зависимости `>=`, lock-файла нет → на стенде в день фестиваля ставятся другие версии."""
    lock = ROOT / "requirements.lock"
    assert lock.exists(), "нет requirements.lock"
    pins = [l for l in lock.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    assert pins and all("==" in l or l.strip().startswith("--") for l in pins), pins[:5]
    names = {re.split(r"[<>=\[;]", l)[0].strip().lower().replace("_", "-") for l in pins}
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    for line in req.splitlines():
        if line.strip() and not line.startswith("#"):
            name = re.split(r"[<>=\[;]", line)[0].strip().lower().replace("_", "-")
            assert name in names, f"{name} не закреплён в requirements.lock"
