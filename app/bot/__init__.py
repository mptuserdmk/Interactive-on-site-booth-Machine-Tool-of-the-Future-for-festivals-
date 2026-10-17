from app.bot.service import bot_service as telegram_bot_service, start_telegram_bot, stop_telegram_bot
from app.bot.max_service import max_bot_service, start_max_bot, stop_max_bot

# Алиас bot_service для обратной совместимости
bot_service = telegram_bot_service

__all__ = [
    "bot_service",
    "telegram_bot_service",
    "start_telegram_bot",
    "stop_telegram_bot",
    "max_bot_service",
    "start_max_bot",
    "stop_max_bot"
]
