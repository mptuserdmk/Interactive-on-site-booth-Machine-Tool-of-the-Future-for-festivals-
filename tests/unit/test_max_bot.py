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
