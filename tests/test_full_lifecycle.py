import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import httpx
from app.main import app

async def run_full_test():
    print("=" * 65)
    print("🚀 ПОЛНЫЙ ТЕСТ ВСЕХ GET И POST ЗАПРОСОВ (ИНТЕРФЕЙС И КНОПКИ)")
    print("=" * 65)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. HTML Pages
        print("\n[1/6] Проверка открытия всех экранов (GET HTML)...")
        for p in ["/", "/kiosk", "/operator", "/mobile-camera"]:
            r = await client.get(p)
            assert r.status_code == 200, f"Ошибка {p}: {r.status_code}"
            print(f"  ✓ GET {p:<18} -> 200 OK")

        # 2. Schema and Diagnostics
        print("\n[2/6] Проверка схемы квиза и диагностики (GET API)...")
        r_health = await client.get("/api/health")
        assert r_health.status_code == 200
        print(f"  ✓ GET /api/health          -> 200 OK")

        r_schema = await client.get("/api/quiz/schema")
        assert r_schema.status_code == 200
        schema = r_schema.json()
        assert len(schema) == 3
        print(f"  ✓ GET /api/quiz/schema     -> 200 OK (3 вопроса)")

        r_combos = await client.get("/api/quiz/combinations")
        assert r_combos.status_code == 200
        assert len(r_combos.json()) == 100
        print(f"  ✓ GET /api/quiz/combinations -> 200 OK (100 комбинаций загружено)")

        # 3. Session Creation (Кнопка «СОЗДАТЬ ОБРАЗ»)
        print("\n[3/6] Проверка кнопки «СОЗДАТЬ ОБРАЗ» (POST /api/session/new)...")
        r_new = await client.post("/api/session/new")
        assert r_new.status_code == 200
        sess = r_new.json()
        sess_id = sess["id"]
        assert sess["status"] == "PHOTO_PENDING"
        print(f"  ✓ POST /api/session/new    -> Сессия создана: {sess_id} (PHOTO_PENDING)")

        # 4. Camera Capture & Confirm (Кнопка «СДЕЛАТЬ ФОТО» и «ПОДТВЕРДИТЬ»)
        print("\n[4/6] Проверка кнопок съемки и пересъемки...")
        r_cap = await client.post("/api/camera/capture")
        assert r_cap.status_code == 200
        print(f"  ✓ POST /api/camera/capture -> Кадр захвачен: {r_cap.json()['photo_url']}")

        r_retake = await client.post("/api/session/photo/retake")
        assert r_retake.status_code == 200
        print(f"  ✓ POST /api/session/photo/retake -> Сброс для пересъемки [OK]")

        # Снимаем повторно и подтверждаем
        await client.post("/api/camera/capture")
        r_confirm = await client.post("/api/session/photo/confirm")
        assert r_confirm.status_code == 200
        assert r_confirm.json()["session"]["status"] == "QUIZ_ELEMENT"
        print(f"  ✓ POST /api/session/photo/confirm -> Переход к выбору стихии [OK]")

        # 5. Quiz Steps (Кнопки карточек: Стихия -> Суперсила -> Цвет)
        print("\n[5/6] Проверка кнопок выбора характеристик (Квиз)...")
        # Стихия
        r_e = await client.post("/api/session/answer", json={"question_type": "element", "answer_id": "space"})
        assert r_e.status_code == 200
        assert r_e.json()["session"]["status"] == "QUIZ_POWER"
        print(f"  ✓ Нажатие карточки 'Космос'     -> Статус: QUIZ_POWER")

        # Суперсила
        r_p = await client.post("/api/session/answer", json={"question_type": "power", "answer_id": "precision"})
        assert r_p.status_code == 200
        assert r_p.json()["session"]["status"] == "QUIZ_COLOR"
        print(f"  ✓ Нажатие карточки 'Точность'   -> Статус: QUIZ_COLOR")

        # Цвет
        r_c = await client.post("/api/session/answer", json={"question_type": "color", "answer_id": "azure"})
        assert r_c.status_code == 200
        print(f"  ✓ Нажатие карточки 'Лазурный'  -> Запуск AI генерации и сборки паспорта...")

        # Ожидание сборки
        await asyncio.sleep(2.0)

        r_active = await client.get("/api/session/active")
        cur_sess = r_active.json()
        print(f"  ✓ Паспорт собран! Профессия: '{cur_sess.get('machine_name')}', Статус: {cur_sess['status']}")
        assert cur_sess.get("final_card_path") is not None

        # 6. Print & Reprint & Reset
        print("\n[6/6] Проверка печати, повторной печати и сброса...")
        r_pr = await client.post("/api/print/trigger-active")
        assert r_pr.status_code == 200
        print(f"  ✓ POST /api/print/trigger-active -> Отправлено на печать")

        r_repr = await client.post("/api/print/reprint", json={"session_id": sess_id})
        assert r_repr.status_code == 200
        assert r_repr.json()["success"] is True
        print(f"  ✓ POST /api/print/reprint        -> Быстрая повторная печать [OK]")

        r_card = await client.get(f"/card/{sess_id}")
        assert r_card.status_code == 200
        print(f"  ✓ GET /card/{sess_id}            -> Digital-страница по QR-коду [200 OK]")

        r_rst = await client.post("/api/session/reset")
        assert r_rst.status_code == 200
        print(f"  ✓ POST /api/session/reset        -> Сброс на главный экран [OK]")

    print("\n" + "=" * 65)
    print("🎉 ВСЕ ЭНДПОИНТЫ И ДЕЙСТВИЯ КНОПОК РАБОТАЮТ БЕЗУПРЕЧНО (100% УСПЕХ)!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_full_test())
