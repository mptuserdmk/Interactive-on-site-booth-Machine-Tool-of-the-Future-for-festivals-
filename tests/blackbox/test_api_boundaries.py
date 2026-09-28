"""
Black-box: граничные и враждебные значения на публичных входах API. Главный инвариант — никаких 5xx.
"""
import pytest

pytestmark = pytest.mark.integration

WEIRD_IDS = ["sess_does_not_exist", "x" * 10_000, "' OR 1=1--", "%00", "..%2F..%2Fdata%2Fkiosk.db",
             "sess_20260928120000_ab12", "<script>alert(1)</script>", "😀", ""]


@pytest.mark.parametrize("limit", ["-1", "0", "1", "1000000000", "abc", "1e3", "999999999999999999999"])
async def test_history_limit_values_no_5xx(client, limit):
    r = await client.get(f"/api/session/history?limit={limit}")
    assert r.status_code < 500, (limit, r.status_code)
    if r.status_code == 200:
        assert len(r.json()) <= 200


@pytest.mark.regression
@pytest.mark.parametrize("limit", ["-1", "0", "1000000000"])
async def test_history_limit_out_of_range_rejected(client, limit):
    r = await client.get(f"/api/session/history?limit={limit}")
    assert r.status_code == 422, (limit, r.status_code)


@pytest.mark.parametrize("answer", ["", "x" * 10_240, "Космос", "<script>alert(1)</script>", "../../etc/passwd",
                                    "SPACE", " space", "null", "💥"])
async def test_answer_id_values_no_5xx(client, fast_pipeline, answer):
    await client.post("/api/session/new")
    await client.post("/api/camera/capture")
    await client.post("/api/session/photo/confirm")
    r = await client.post("/api/session/answer", json={"question_type": "element", "answer_id": answer})
    assert r.status_code < 500


@pytest.mark.regression
@pytest.mark.parametrize("answer", ["", "x" * 10_240, "<script>alert(1)</script>", "../../etc/passwd", "lava"])
async def test_unknown_answer_id_rejected_422(client, fast_pipeline, answer):
    """H5: неизвестный answer_id принимается, а на цвете молча превращается в комбинацию №1."""
    await client.post("/api/session/new")
    await client.post("/api/camera/capture")
    await client.post("/api/session/photo/confirm")
    r = await client.post("/api/session/answer", json={"question_type": "element", "answer_id": answer})
    assert r.status_code == 422, (answer[:20], r.status_code)


@pytest.mark.regression
@pytest.mark.parametrize("qt", ["", "elements", "COLOR", "photo", "x" * 1000])
async def test_unknown_question_type_rejected_422(client, fast_pipeline, qt):
    await client.post("/api/session/new")
    await client.post("/api/camera/capture")
    await client.post("/api/session/photo/confirm")
    r = await client.post("/api/session/answer", json={"question_type": qt, "answer_id": "space"})
    assert r.status_code == 422


@pytest.mark.regression
async def test_unknown_combination_never_silently_becomes_combo_1(client, fast_pipeline):
    """H5: element='lava' → на шаге цвета combination_manager.find() = None → молча комбинация №1."""
    from helpers import db_state, wait_for_status
    await client.post("/api/session/new")
    sid = (await client.post("/api/camera/capture")).json()["session_id"]
    await client.post("/api/session/photo/confirm")
    await client.post("/api/session/answer", json={"question_type": "element", "answer_id": "lava"})
    await client.post("/api/session/answer", json={"question_type": "power", "answer_id": "precision"})
    await client.post("/api/session/answer", json={"question_type": "color", "answer_id": "azure"})
    s = db_state(sid)()
    if s["status"] in ("GENERATING", "COMPOSING", "READY_TO_PRINT", "PRINTING"):
        s = await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=10)
    assert not (s["element"] == "lava" and s["combination_id"] == 1), "lava+precision+azure напечатан как «Космический Токарь-Оптик»"


@pytest.mark.parametrize("sid", WEIRD_IDS)
async def test_card_page_weird_ids_no_5xx(client, sid):
    r = await client.get(f"/card/{sid}")
    assert r.status_code < 500
    assert "sqlite" not in r.text.lower() and "Traceback" not in r.text


@pytest.mark.regression
async def test_card_page_unknown_session_is_404(client):
    r = await client.get("/card/sess_does_not_exist")
    assert r.status_code == 404


@pytest.mark.parametrize("sid", WEIRD_IDS)
async def test_reprint_weird_ids_no_5xx(client, sid):
    r = await client.post("/api/print/reprint", json={"session_id": sid})
    assert r.status_code < 500
    if r.status_code == 200:
        assert r.json()["success"] is False


@pytest.mark.parametrize("body", [None, {}, {"question_type": "element"}, {"answer_id": 1},
                                  {"question_type": ["element"], "answer_id": "space"}, "not json"])
async def test_answer_malformed_body_422(client, body):
    if body == "not json":
        r = await client.post("/api/session/answer", content=b"{not json", headers={"content-type": "application/json"})
    else:
        r = await client.post("/api/session/answer", json=body)
    assert r.status_code == 422


@pytest.mark.parametrize("method,url", [("GET", "/api/session/new"), ("DELETE", "/api/session/reset"),
                                        ("PUT", "/api/print/reprint"), ("GET", "/api/camera/upload-ota")])
async def test_wrong_methods_405(client, method, url):
    r = await client.request(method, url)
    assert r.status_code == 405
