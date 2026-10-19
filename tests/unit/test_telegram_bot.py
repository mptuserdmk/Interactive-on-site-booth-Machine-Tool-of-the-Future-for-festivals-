import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from app.config.settings import settings
from app.bot.service import TelegramBotService


@pytest.fixture
def tg_service():
    srv = TelegramBotService()
    return srv


def test_telegram_bot_is_configured(tg_service, monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    assert tg_service.is_configured is False

    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "123")  # too short
    assert tg_service.is_configured is False

    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ")
    assert tg_service.is_configured is True


def test_telegram_extract_session_id():
    # Canonical format
    assert TelegramBotService._extract_session_id("/start sess_123456789abcdef0") == "sess_123456789abcdef0"
    assert TelegramBotService._extract_session_id("?start=sess_9876543210fedcba") == "sess_9876543210fedcba"
    assert TelegramBotService._extract_session_id("sess_abcdef0123456789") == "sess_abcdef0123456789"
    # Plain start without session
    assert TelegramBotService._extract_session_id("/start") is None
    assert TelegramBotService._extract_session_id("") is None


@pytest.mark.asyncio
async def test_telegram_deliver_card_deduplication(tg_service, tmp_path):
    # Create fake card file
    card_file = tmp_path / "sess_dedup_card.jpg"
    card_file.write_bytes(b"FAKE_CARD_JPEG")

    tg_service._find_card_file = MagicMock(return_value=card_file)
    tg_service._send_photo = AsyncMock(return_value=True)
    tg_service._schedule_followup = MagicMock()

    with patch("app.bot.service.db.get_session", return_value={"machine_name": "Токарь", "power_name": "Точность"}):
        with patch("app.bot.service.db.save_telegram_link"):
            # First delivery succeeds
            await tg_service._deliver_card(12345, "sess_dedup", "tester", "Тестер")
            assert tg_service._send_photo.await_count == 1
            assert "12345:sess_dedup" in tg_service._delivered

            # Second delivery with same session and chat is skipped due to deduplication!
            await tg_service._deliver_card(12345, "sess_dedup", "tester", "Тестер")
            assert tg_service._send_photo.await_count == 1  # Still 1, NOT called again!


@pytest.mark.asyncio
async def test_telegram_deliver_card_in_flight_skip(tg_service):
    # Simulate delivery already in flight
    tg_service._in_flight.add("555:sess_inflight")
    tg_service._send_photo = AsyncMock()

    await tg_service._deliver_card(555, "sess_inflight", "tester", "Тестер")
    assert tg_service._send_photo.await_count == 0
