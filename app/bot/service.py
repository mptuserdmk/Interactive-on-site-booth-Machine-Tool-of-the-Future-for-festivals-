import asyncio
import logging
import re
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
        self._in_flight: set = set()
        self._delivered: set = set()
        self._tasks: set = set()

    @staticmethod
    def _extract_session_id(text_or_payload: str) -> Optional[str]:
        """Универсально извлекает session_id из ссылки, параметра start, текста или deep-link."""
        if not text_or_payload:
            return None
        text = str(text_or_payload).strip()
        # 1. Поиск канонического паттерна сессий стенда: sess_[a-f0-9_]
        match = re.search(r"sess_[A-Za-z0-9_]{8,64}", text)
        if match:
            return match.group(0)

        # 2. Обработка произвольных тестовых ID или очистка параметров
        clean = text
        if clean.startswith("/start"):
            parts = clean.split(maxsplit=1)
            clean = parts[1].strip() if len(parts) > 1 else ""
        if clean.startswith("?start="):
            clean = clean[7:].strip()
        elif clean.startswith("start="):
            clean = clean[6:].strip()

        clean = clean.split("&")[0].split("?")[0].strip()
        if clean and re.match(r"^[A-Za-z0-9_\-]{6,64}$", clean):
            return clean
        return None

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

        # Build proxy candidates: configured proxy, protocol alternative (http <-> socks5), and direct fallback
        raw_proxy = (getattr(settings, "TELEGRAM_PROXY_URL", "") or getattr(settings, "PROXY_URL", "") or "").strip()
        candidates = []
        if raw_proxy:
            candidates.append(raw_proxy)
            if raw_proxy.startswith("http://"):
                candidates.append("socks5://" + raw_proxy[7:])
            elif raw_proxy.startswith("socks5://"):
                candidates.append("http://" + raw_proxy[9:])
            candidates.append(None)  # direct connection fallback
        else:
            candidates.append(None)

        connected = False
        last_error = ""

        for cand in candidates:
            safe_desc = cand.split("@")[-1] if cand and "@" in cand else (cand or "прямое подключение")
            try:
                test_client = httpx.AsyncClient(proxy=cand, timeout=20.0)
                resp = await test_client.get(f"{self.api_url}/getMe")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        self._client = test_client
                        result = data.get("result", {})
                        self.bot_username = result.get("username", "")
                        if not settings.TELEGRAM_BOT_USERNAME and self.bot_username:
                            settings.TELEGRAM_BOT_USERNAME = self.bot_username

                        logger.info(
                            "🤖 Telegram Bot подключен успешно: @%s через %s (ID: %s, Имя: %s)",
                            self.bot_username,
                            safe_desc,
                            result.get("id"),
                            result.get("first_name")
                        )
                        connected = True
                        break
                await test_client.aclose()
            except Exception as e:
                last_error = str(e)
                logger.debug("Попытка подключения через %s не удалась: %s", safe_desc, e)
                try:
                    await test_client.aclose()
                except Exception:
                    pass

        if not connected:
            logger.warning("Не удалось подключиться к Telegram Bot API (проверьте токен или прокси): %s", last_error)
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
                        t = asyncio.create_task(self._handle_message(message))
                        self._tasks.add(t)
                        t.add_done_callback(self._tasks.discard)

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
            session_id = self._extract_session_id(text)
            if session_id:
                await self._deliver_card(chat_id, session_id, username, first_name)
            else:
                last_sess = db.get_last_session_for_chat(chat_id) or db.get_last_completed_session(max_age_seconds=1800)
                if last_sess and last_sess.get("id"):
                    await self._deliver_card(chat_id, last_sess["id"], username, first_name, is_fallback=True)
                else:
                    await self._send_welcome(chat_id, first_name)
        else:
            session_id = self._extract_session_id(text)
            if session_id:
                await self._deliver_card(chat_id, session_id, username, first_name)
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

    def _schedule_followup(self, chat_id: int):
        task = asyncio.create_task(self._send_followup(chat_id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _send_followup(self, chat_id: int):
        try:
            await asyncio.sleep(2.0)
            follow_up_msg = (
                "Приглашаем вас подписаться:\n\n"
                "💬 MAX: https://max.ru/channel_cppm\n"
                "✈️ Telegram: https://t.me/cppm_centre\n"
                "💙 ВКонтакте: https://vk.ru/centre.cppm"
            )
            for _ in range(2):
                sent = await self._send_message(chat_id, follow_up_msg)
                if sent:
                    logger.info("Telegram Bot: приглашение к подписке успешно отправлено в чат %s", chat_id)
                    break
                await asyncio.sleep(1.0)
        except Exception as e:
            logger.warning("Telegram Bot: ошибка отправки follow-up сообщения с соцсетями: %s", e)

    async def _deliver_card(
        self,
        chat_id: int,
        session_id: str,
        username: Optional[str],
        first_name: str,
        is_fallback: bool = False
    ):
        """Looks up session, waits if still generating, and sends the finished card photo."""
        extracted = self._extract_session_id(session_id)
        if extracted:
            session_id = extracted
        session_id = session_id.strip()

        delivery_key = f"{chat_id}:{session_id}"
        if delivery_key in self._delivered:
            logger.info("Card for %s already delivered to chat %s, skipping redundant delivery", session_id, chat_id)
            return
        if delivery_key in self._in_flight:
            logger.info("Card delivery for %s to chat %s already in flight, skipping duplicate trigger", session_id, chat_id)
            return

        self._in_flight.add(delivery_key)
        try:
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
                if delivery_key in self._delivered:
                    return
                if retries == 15:
                    await self._send_message(
                        chat_id,
                        "⏳ Твой цифровой паспорт ещё куётся на «Станке Будущего»! Подожди пару секунд, сейчас пришлю..."
                    )
                await asyncio.sleep(2.0)
                if delivery_key in self._delivered:
                    return
                session = db.get_session(session_id) or session
                card_file = self._find_card_file(session_id, session)
                retries -= 1

            if not card_file or not card_file.is_file():
                if delivery_key not in self._delivered:
                    await self._send_message(
                        chat_id,
                        f"⚠️ Не удалось найти готовую карточку для сессии <code>{session_id}</code>.\n\n"
                        f"Пожалуйста, обратись к мастеру станка — он распечатает твой паспорт вручную!"
                    )
                return

            if delivery_key in self._delivered:
                return

            # 3. Send photo (safe against session=None)
            session_safe = session or {}
            machine_name = session_safe.get("machine_name") or "Инженер Будущего"
            power_name = session_safe.get("power_name") or "Точность"
            location = session_safe.get("location") or "Центральный кластер"
            festival_name = getattr(settings, "FESTIVAL_NAME", "ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ МОСКВЫ")
            hashtag = getattr(settings, "FESTIVAL_HASHTAG", "#ФЕСТИВАЛЬ2026")

            greeting = "🎉 <b>Твой цифровой паспорт готов!</b>"
            if is_fallback:
                greeting += "\n<i>(доставлен паспорт с недавней сессии на нашем станке)</i>"

            caption = (
                f"{greeting}\n\n"
                f"🛠 <b>Специальность:</b> {machine_name}\n"
                f"⚡ <b>Суперсила:</b> {power_name}\n"
                f"📍 <b>Гильдия:</b> {location}\n\n"
                f"🏛 <i>{festival_name}</i>\n"
                f"<b>{hashtag}</b>"
            )

            success = await self._send_photo(chat_id, card_file, caption)
            if success:
                self._delivered.add(delivery_key)
                try:
                    db.save_telegram_link(chat_id, session_id, username, first_name)
                except Exception as e:
                    logger.warning("Could not record telegram_link: %s", e)

                self._schedule_followup(chat_id)
        finally:
            self._in_flight.discard(delivery_key)

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

    async def _send_message(self, chat_id: int, text: str) -> bool:
        if not self._client or not self.is_configured:
            return False
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            resp = await self._client.post(f"{self.api_url}/sendMessage", json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.warning("Telegram sendMessage error: %s", e)
            return False

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
