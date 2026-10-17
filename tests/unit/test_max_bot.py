import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from app.config.settings import settings
from app.bot.max_service import MaxBotService


@pytest.fixture
def max_service():
    srv = MaxBotService()
    return srv


def test_max_bot_is_configured(max_service, monkeypatch):
    monkeypatch.setattr(settings, "MAX_BOT_TOKEN", "")
    assert max_service.is_configured is False

    monkeypatch.setattr(settings, "MAX_BOT_TOKEN", "123")  # too short
    assert max_service.is_configured is False

    monkeypatch.setattr(settings, "MAX_BOT_TOKEN", "valid_secret_token_123")
    assert max_service.is_configured is True


def test_max_bot_auth_headers(max_service, monkeypatch):
    monkeypatch.setattr(settings, "MAX_BOT_TOKEN", "my_token_xyz")
    headers = max_service.auth_headers
    assert headers["Authorization"] == "my_token_xyz"
    assert headers["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_handle_update_bot_started(max_service):
    max_service._deliver_card = AsyncMock()
    max_service._send_welcome = AsyncMock()

    # Update with payload
    update = {
        "update_type": "bot_started",
        "chat_id": 99999,
        "payload": "session_abc_123",
        "user": {"user_id": 99999, "name": "Тестер", "username": "tester"}
    }
    await max_service._handle_update(update)
    max_service._deliver_card.assert_awaited_once_with(99999, "session_abc_123", "tester", "Тестер")

    # Update without payload
    update_no_payload = {
        "update_type": "bot_started",
        "chat_id": 88888,
        "payload": "",
        "user": {"user_id": 88888, "name": "Новичок"}
    }
    await max_service._handle_update(update_no_payload)
    max_service._send_welcome.assert_awaited_once_with(88888, "Новичок")


@pytest.mark.asyncio
async def test_handle_update_message_created(max_service):
    max_service._deliver_card = AsyncMock()
    max_service._send_welcome = AsyncMock()
    max_service._send_help = AsyncMock()

    # Message /start session_id
    update_start = {
        "update_type": "message_created",
        "message": {
            "sender": {"user_id": 111, "name": "Иван", "username": "ivan"},
            "recipient": {"chat_id": 222},
            "body": {"text": "/start my_test_session"}
        }
    }
    await max_service._handle_update(update_start)
    max_service._deliver_card.assert_awaited_once_with(222, "my_test_session", "ivan", "Иван")

    # Message general text
    update_text = {
        "update_type": "message_created",
        "message": {
            "sender": {"user_id": 111, "name": "Иван"},
            "recipient": {"chat_id": 222},
            "body": {"text": "Привет, бот"}
        }
    }
    await max_service._handle_update(update_text)
    max_service._send_help.assert_awaited_once_with(222, "Иван")


@pytest.mark.asyncio
async def test_send_photo_flow(max_service, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_BOT_TOKEN", "valid_token_xyz")
    max_service._client = AsyncMock()

    # Create dummy image file
    dummy_img = tmp_path / "test_card.jpg"
    dummy_img.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 50)

    # Mock response 1: POST /uploads returns url with mediafile_token
    slot_resp = MagicMock()
    slot_resp.status_code = 200
    slot_resp.json.return_value = {
        "url": "https://iu.oneme.ru/uploadImage?mediafile_token=TOKEN_ABC_999"
    }

    # Mock response 2: upload image to url
    upload_resp = MagicMock()
    upload_resp.status_code = 200

    # Mock response 3: POST /messages
    msg_resp = MagicMock()
    msg_resp.status_code = 200

    max_service._client.post.side_effect = [slot_resp, upload_resp, msg_resp]

    success = await max_service._send_photo(chat_id=12345, file_path=dummy_img, caption="Готово!")
    assert success is True
    assert max_service._client.post.call_count == 3


def test_extract_session_id_formats(max_service):
    # Canonical session id
    assert max_service._extract_session_id("sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9") == "sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9"
    # Deep link query format start=sess_...
    assert max_service._extract_session_id("start=sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9") == "sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9"
    # Query with question mark ?start=sess_...
    assert max_service._extract_session_id("?start=sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9") == "sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9"
    # Full URL
    assert max_service._extract_session_id("https://max.ru/stanok_bot?start=sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9") == "sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9"
    # Text with command
    assert max_service._extract_session_id("/start sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9") == "sess_3a8b2c1d4e5f60718293a4b5c6d7e8f9"
    # Custom test session
    assert max_service._extract_session_id("/start my_custom_test_session") == "my_custom_test_session"
    # Bare command or empty
    assert max_service._extract_session_id("/start") is None
    assert max_service._extract_session_id("") is None
    assert max_service._extract_session_id(None) is None


@pytest.mark.asyncio
async def test_bot_started_auto_fallback_recent_session(max_service):
    max_service._deliver_card = AsyncMock()
    max_service._send_welcome = AsyncMock()

    with patch("app.bot.max_service.db.get_last_session_for_chat", return_value=None), \
         patch("app.bot.max_service.db.get_last_completed_session", return_value={"id": "sess_recovered_99"}):
        update = {
            "update_type": "bot_started",
            "chat_id": 55555,
            "payload": "",  # payload lost or stripped
            "user": {"user_id": 55555, "name": "Посетитель"}
        }
        await max_service._handle_update(update)
        max_service._deliver_card.assert_awaited_once_with(
            55555, "sess_recovered_99", None, "Посетитель", is_fallback=True
        )


@pytest.mark.asyncio
async def test_message_created_auto_fallback_recent_session(max_service):
    max_service._deliver_card = AsyncMock()
    max_service._send_welcome = AsyncMock()

    with patch("app.bot.max_service.db.get_last_session_for_chat", return_value=None), \
         patch("app.bot.max_service.db.get_last_completed_session", return_value={"id": "sess_recent_88"}):
        update = {
            "update_type": "message_created",
            "message": {
                "sender": {"user_id": 777, "name": "Участник"},
                "recipient": {"chat_id": 777},
                "body": {"text": "/start"}  # bare start without payload
            }
        }
        await max_service._handle_update(update)
        max_service._deliver_card.assert_awaited_once_with(
            777, "sess_recent_88", None, "Участник", is_fallback=True
        )


@pytest.mark.asyncio
async def test_deliver_card_safe_against_none_session(max_service, tmp_path):
    dummy_img = tmp_path / "sess_test_safe_card.jpg"
    dummy_img.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 20)

    max_service._send_photo = AsyncMock(return_value=True)

    with patch("app.bot.max_service.db.get_session", return_value=None), \
         patch.object(max_service, "_find_card_file", return_value=dummy_img), \
         patch("app.bot.max_service.db.save_telegram_link"):
        # Calling _deliver_card when db.get_session returns None must NOT crash with AttributeError
        await max_service._deliver_card(
            chat_id=123,
            session_id="sess_test_safe",
            username="user_safe",
            first_name="Мастер"
        )
        max_service._send_photo.assert_awaited_once()
        args, kwargs = max_service._send_photo.call_args
        assert args[0] == 123
        assert args[1] == dummy_img
        assert "Инженер Будущего" in args[2]  # Safe default used

