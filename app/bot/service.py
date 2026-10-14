import asyncio
import logging
from pathlib import Path
from typing import Optional
import httpx

from app.config.settings import settings
from app.storage.database import db

logger = logging.getLogger("stanok.bot")


class TelegramBotService:
    def __init__(self):
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None
        self.last_update_id = 0
        self.bot_username: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(settings.TELEGRAM_BOT_TOKEN and len(settings.TELEGRAM_BOT_TOKEN.strip()) > 10)

    @property
    def api_url(self) -> str:
        return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN.strip()}"

    async def start(self):
        if not self.is_configured:
            logger.info("Telegram Bot: TELEGRAM_BOT_TOKEN is not configured — bot will not start")
            return

        self._running = True
        
        # Configure proxy (HTTP, HTTPS, SOCKS5)
        proxy = (getattr(settings, "TELEGRAM_PROXY_URL", "") or getattr(settings, "PROXY_URL", "") or "").strip() or None
        if proxy:
            # Mask credentials if present for secure logging
            safe_proxy = proxy.split("@")[-1] if "@" in proxy else proxy
            logger.info("🤖 Telegram Bot: connecting via proxy (%s)", safe_proxy)
        else:
            logger.info("🤖 Telegram Bot: direct connection (no proxy configured)")

        self._client = httpx.AsyncClient(proxy=proxy, timeout=45.0)

        # 1. Verify token & get bot username
        try:
            resp = await self._client.get(f"{self.api_url}/getMe")
            if resp.status_code != 200:
                logger.error("Telegram Bot authentication failed: HTTP %s: %s", resp.status_code, resp.text[:120])
                self._running = False
                return
            data = resp.json()
            if not data.get("ok"):
                logger.error("Telegram Bot getMe returned error: %s", data)
                self._running = False
                return

            result = data.get("result", {})
            self.bot_username = result.get("username", "")
            if not settings.TELEGRAM_BOT_USERNAME and self.bot_username:
                settings.TELEGRAM_BOT_USERNAME = self.bot_username

            logger.info(
                "🤖 Telegram Bot started successfully: @%s (ID: %s, Name: %s)",
                self.bot_username,
                result.get("id"),
                result.get("first_name")
            )
        except Exception as e:
            logger.warning("Failed to connect to Telegram Bot API (check token or proxy): %s", e)
            self._running = False
            return

        # 2. Polling loop
        while self._running:
            try:
                params = {
                    "offset": self.last_update_id + 1,
                    "timeout": 25,
                    "allowed_updates": ["message"]
                }
                resp = await self._client.get(f"{self.api_url}/getUpdates", params=params)
                if resp.status_code != 200:
                    logger.warning("Telegram getUpdates returned HTTP %s", resp.status_code)
                    await asyncio.sleep(3.0)
                    continue

                res_json = resp.json()
                if not res_json.get("ok"):
                    await asyncio.sleep(3.0)
                    continue

                updates = res_json.get("result", [])
                for upd in updates:
                    upd_id = upd.get("update_id")
                    if upd_id:
                        self.last_update_id = max(self.last_update_id, upd_id)

                    message = upd.get("message")
                    if message:
                        await self._handle_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._running:
                    break
                logger.warning("Telegram polling error: %s", e)
                await asyncio.sleep(2.0)

        logger.info("Telegram Bot polling stopped")

    async def stop(self):
        self._running = False
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    async def _handle_message(self, message: dict):
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        text = (message.get("text") or "").strip()
        from_user = message.get("from", {})
        username = from_user.get("username")
        first_name = from_user.get("first_name", "Мастер")

        if not chat_id:
            return

        # Handle /start or /start <session_id>
        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            session_id = parts[1].strip() if len(parts) > 1 else ""

            if session_id:
                await self._deliver_card(chat_id, session_id, username, first_name)
            else:
                await self._send_welcome(chat_id, first_name)
        else:
            await self._send_help(chat_id, first_name)

    def _find_card_file(self, session_id: str, session: Optional[dict]) -> Optional[Path]:
        raw_path = session.get("final_card_path") if session else None
        candidates = [
            Path(raw_path) if raw_path else None,
            settings.CARDS_DIR / f"{session_id}_card.jpg",
            settings.CARDS_DIR / f"{session_id}.jpg",
        ]
        for c in candidates:
            if c and c.is_file():
                return c
        return None

    async def _deliver_card(self, chat_id: int, session_id: str, username: Optional[str], first_name: str):
        """Looks up session, waits if still generating, and sends the finished card photo."""
        session_id = session_id.strip()
        if session_id.startswith("start="):
            session_id = session_id[6:].strip()

        logger.info("Delivering card for session %s to chat %s (@%s)", session_id, chat_id, username or "none")

        # 1. Check session in DB
        session = db.get_session(session_id)
        if not session:
            # Wait briefly in case session was just saved or DB write is finishing
            await asyncio.sleep(1.0)
            session = db.get_session(session_id)

        # 2. Wait up to 30 seconds if card is still in progress
        card_file = self._find_card_file(session_id, session)

        retries = 15
        while not card_file and retries > 0:
            if retries == 15:
                await self._send_message(
                    chat_id,
                    f"⏳ Твой цифровой паспорт ещё куётся на «Станке Будущего»! Подожди пару секунд, сейчас пришлю..."
                )
            await asyncio.sleep(2.0)
            session = db.get_session(session_id) or session
            card_file = self._find_card_file(session_id, session)
            retries -= 1

        if not card_file or not card_file.is_file():
            await self._send_message(
                chat_id,
                f"⚠️ Не удалось найти готовую карточку для сессии <code>{session_id}</code>.\n\n"
                f"Пожалуйста, обратись к мастеру станка — он распечатает твой паспорт вручную!"
            )
            return

        # 3. Send photo
        machine_name = session.get("machine_name", "Инженер Будущего")
        power_name = session.get("power_name", "Точность")
        location = session.get("location", "Центральный кластер")
        festival_name = getattr(settings, "FESTIVAL_NAME", "FUTURE INDUSTRY 2026")
        hashtag = getattr(settings, "FESTIVAL_HASHTAG", "#ФЕСТИВАЛЬ2026")

        caption = (
            f"🎉 <b>Твой цифровой паспорт готов!</b>\n\n"
            f"🛠 <b>Специальность:</b> {machine_name}\n"
            f"⚡ <b>Суперсила:</b> {power_name}\n"
            f"📍 <b>Гильдия:</b> {location}\n\n"
            f"🏛 <i>{festival_name}</i>\n"
            f"<b>{hashtag}</b>"
        )

        success = await self._send_photo(chat_id, card_file, caption)
        if success:
            try:
                db.save_telegram_link(chat_id, session_id, username, first_name)
            except Exception as e:
                logger.warning("Could not record telegram_link: %s", e)

    async def _send_welcome(self, chat_id: int, first_name: str):
        msg = (
            f"👋 Привет, {first_name}!\n\n"
            f"Я официальный бот интерактивной фотолокации <b>«Станок Будущего»</b>.\n\n"
            f"📸 <b>Как получить паспорт инженера:</b>\n"
            f"1. Подойди к экрану нашего киоска.\n"
            f"2. Сделай фото и выбери черты своей специальности.\n"
            f"3. Наведи камеру смартфона на появившийся QR-код — и я моментально пришлю твою карточку сюда!"
        )
        await self._send_message(chat_id, msg)

    async def _send_help(self, chat_id: int, first_name: str):
        msg = (
            f"Привет, {first_name}!\n\n"
            f"Чтобы получить свою готовую карточку, отсканируй QR-код на экране фотолокации «Станок Будущего».\n"
            f"Если у тебя есть код сессии, отправь команду: <code>/start код_сессии</code>"
        )
        await self._send_message(chat_id, msg)

    async def _send_message(self, chat_id: int, text: str):
        if not self._client or not self.is_configured:
            return
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            await self._client.post(f"{self.api_url}/sendMessage", json=payload)
        except Exception as e:
            logger.warning("Telegram sendMessage error: %s", e)

    async def _send_photo(self, chat_id: int, file_path: Path, caption: str) -> bool:
        if not self._client or not self.is_configured:
            return False
        try:
            with open(file_path, "rb") as f:
                photo_bytes = f.read()

            files = {
                "photo": ("card.jpg", photo_bytes, "image/jpeg")
            }
            data = {
                "chat_id": str(chat_id),
                "caption": caption,
                "parse_mode": "HTML"
            }
            resp = await self._client.post(f"{self.api_url}/sendPhoto", data=data, files=files, timeout=30.0)
            if resp.status_code == 200:
                logger.info("Successfully sent photo to chat %s", chat_id)
                return True
            else:
                logger.error("Failed to sendPhoto: HTTP %s: %s", resp.status_code, resp.text[:120])
                return False
        except Exception as e:
            logger.exception("Exception in sendPhoto: %s", e)
            return False


bot_service = TelegramBotService()


async def start_telegram_bot():
    await bot_service.start()


async def stop_telegram_bot():
    await bot_service.stop()
