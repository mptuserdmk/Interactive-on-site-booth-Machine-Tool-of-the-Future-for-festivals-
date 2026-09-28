"""
Гонки вокруг глобальной active_session (H1, H2, H3).

Все тесты детерминированы: «медленный AI» и «медленный принтер» — это asyncio.Event-гейты
(фикстуры ai_gate / print_gate), а не sleep.
"""
import asyncio

import pytest

from helpers import active_state, db_state, do, drive_to, printed_files, printed_session_ids, wait_for_status, wait_until

pytestmark = [pytest.mark.integration, pytest.mark.regression]


@pytest.mark.parametrize("taps", [2, 5, 10])
async def test_double_tap_color_starts_exactly_one_pipeline(client, fast_pipeline, ai_calls, taps):
    """H2: двойной/многократный тап по цвету → ровно 1 генерация AI и 1 печать."""
    sid = await drive_to(client, "QUIZ_COLOR")
    responses = await asyncio.gather(*[do(client, "color") for _ in range(taps)])
    codes = sorted(r.status_code for r in responses)
    await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=20)
    await asyncio.sleep(0.2)  # дать «лишним» пайплайнам, если они есть, дойти до печати
    assert len(ai_calls) == 1, f"AI вызван {len(ai_calls)} раз(а) на {taps} тапов; коды ответов {codes}"
    assert printed_session_ids() == [sid], f"напечатано: {printed_session_ids()}"
    assert codes.count(200) == 1 and codes.count(409) == taps - 1, codes


async def test_sequential_double_color_is_rejected(client, fast_pipeline, ai_calls):
    """H2: второй тап после того, как первый уже отработал (не параллельно)."""
    sid = await drive_to(client, "QUIZ_COLOR")
    r1 = await do(client, "color")
    r2 = await do(client, "color")
    await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=20)
    await asyncio.sleep(0.2)
    assert r1.status_code == 200
    assert r2.status_code == 409
    assert len(ai_calls) == 1
    assert printed_session_ids() == [sid]


async def test_new_session_during_generation_does_not_print_foreign_card(client, fast_pipeline, ai_gate):
    """H3: сессия A генерируется, оператор жмёт «Новая сессия» (B), затем B проходит весь цикл,
    и только потом A «досчитывается». Печать не должна уйти не туда, ни одна карточка — дважды."""
    ai_gate.hold = 1  # «висит» только первая генерация (A)
    sid_a = await drive_to(client, "GENERATING")
    await wait_until(lambda: sid_a in ai_gate.calls, what="пайплайн A вошёл в AI")
    sid_b = await drive_to(client, "COMPLETED")
    assert sid_b != sid_a
    ai_gate.gate.set()
    await asyncio.sleep(0.8)  # пайплайн A с ускоренными моками успевает дойти до печати
    files = printed_files()
    assert files.count(f"{sid_b}_card.jpg") == 1, (
        f"карточка B напечатана {files.count(f'{sid_b}_card.jpg')} раз, A — {files.count(f'{sid_a}_card.jpg')} раз; "
        f"статус A в БД: {db_state(sid_a)()['status']}")
    assert all(f in (f"{sid_a}_card.jpg", f"{sid_b}_card.jpg") for f in files)
    final_a = await wait_for_status(db_state(sid_a), {"COMPLETED", "ERROR", "IDLE"}, timeout=10)
    files = printed_files()
    assert files.count(f"{sid_b}_card.jpg") == 1, files
    if final_a["status"] == "COMPLETED":
        assert files.count(f"{sid_a}_card.jpg") == 1
    assert (await active_state(client))["id"] == sid_b


async def test_new_session_during_generation_old_session_not_left_hanging(client, fast_pipeline, ai_gate):
    """H3: после «Новая сессия» старая A не должна навсегда остаться в READY_TO_PRINT/GENERATING."""
    sid_a = await drive_to(client, "GENERATING")
    await wait_until(lambda: sid_a in ai_gate.calls, what="пайплайн A вошёл в AI")
    r = await do(client, "new")
    assert r.status_code == 200
    ai_gate.gate.set()
    final_a = await wait_for_status(db_state(sid_a), {"COMPLETED", "ERROR", "IDLE"}, timeout=10)
    assert final_a["status"] in {"COMPLETED", "ERROR", "IDLE"}
    st = await active_state(client)
    assert st["id"] == r.json()["id"] and st["status"] == "PHOTO_PENDING"


async def test_reset_during_generation_kiosk_stays_idle(client, fast_pipeline, ai_gate, broadcast_log):
    """H3: «Сброс» во время генерации → киоск остаётся на Welcome, не «прыгает» обратно
    в COMPOSING/результат, когда старый пайплайн досчитается."""
    sid_a = await drive_to(client, "GENERATING")
    await wait_until(lambda: sid_a in ai_gate.calls, what="пайплайн A вошёл в AI")
    r = await do(client, "reset")
    assert r.status_code == 200
    mark = len(broadcast_log)
    ai_gate.gate.set()
    await wait_for_status(db_state(sid_a), {"COMPLETED", "ERROR", "IDLE"}, timeout=10)
    await asyncio.sleep(0.3)
    st = await active_state(client)
    assert st is None or st["status"] == "IDLE", f"после сброса активна сессия в статусе {st and st['status']}"
    leaked = [s for s in broadcast_log[mark:] if s[1] not in ("IDLE", None)]
    assert leaked == [], f"после сброса киоску разослано: {leaked}"
    assert set(printed_session_ids()) <= {sid_a}


async def test_reset_during_printing_card_still_printed_once_kiosk_idle(client, fast_pipeline, print_gate):
    """Сброс по idle-таймеру во время печати: карточка A печатается ровно один раз,
    A в истории COMPLETED, киоск остаётся на Welcome."""
    sid_a = await drive_to(client, "PRINTING")
    await wait_until(lambda: any(s == sid_a for s, _ in print_gate.calls), what="печать A началась")
    r = await do(client, "reset")
    assert r.status_code == 200
    print_gate.gate.set()
    final_a = await wait_for_status(db_state(sid_a), {"COMPLETED", "ERROR"}, timeout=10)
    await asyncio.sleep(0.2)
    assert final_a["status"] == "COMPLETED"
    assert printed_session_ids() == [sid_a]
    st = await active_state(client)
    assert st is None or st["status"] == "IDLE"


async def test_trigger_print_during_auto_print_does_not_double_print(client, fast_pipeline, print_gate):
    """Оператор жмёт «ПЕЧАТАТЬ», пока идёт автопечать → вторая печать не уходит."""
    sid = await drive_to(client, "PRINTING")
    await wait_until(lambda: any(s == sid for s, _ in print_gate.calls), what="автопечать началась")
    # до фикса роут ждёт вторую печать → запрос выполняем задачей, иначе тест сам себя заблокирует
    task = asyncio.create_task(do(client, "trigger_print"))
    await asyncio.sleep(0.2)
    print_gate.gate.set()
    r = await asyncio.wait_for(task, timeout=10)
    await wait_for_status(db_state(sid), {"COMPLETED", "ERROR"}, timeout=10)
    await asyncio.sleep(0.2)
    assert r.status_code == 409
    assert printed_session_ids() == [sid]


async def test_photo_upload_during_generation_does_not_hijack_session(client, fast_pipeline, ai_gate):
    """Ассистент прислал фото с телефона, пока идёт генерация: сессия A не должна вернуться в PHOTO_TAKEN."""
    from helpers import make_photo_bytes
    sid_a = await drive_to(client, "GENERATING")
    await wait_until(lambda: sid_a in ai_gate.calls, what="пайплайн A вошёл в AI")
    r = await client.post("/api/camera/upload-ota", files={"file": ("p.jpg", make_photo_bytes(), "image/jpeg")})
    assert r.status_code == 409
    assert db_state(sid_a)()["status"] == "GENERATING"
    ai_gate.gate.set()
    done = await wait_for_status(db_state(sid_a), {"COMPLETED", "ERROR"}, timeout=10)
    assert done["status"] == "COMPLETED"
