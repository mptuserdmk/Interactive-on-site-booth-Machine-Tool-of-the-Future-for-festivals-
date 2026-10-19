import asyncio
import logging
import re
import ssl
from pathlib import Path
from typing import Optional, Union, Any
from urllib.parse import parse_qs, urlparse
import httpx

from app.config.settings import settings
from app.storage.database import db

logger = logging.getLogger("stanok.bot.max")


class MaxBotService:
    """
    Сервис взаимодействия с официальным Bot API мессенджера МАКС (dev.max.ru).
    Работает локально по принципу Long Polling (GET /updates), не требует белого IP или вебхуков.
    """

    def __init__(self):
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None
        self.last_marker: Optional[int] = None
        self.bot_username: str = ""

    @staticmethod
    def _extract_session_id(text_or_payload: str) -> Optional[str]:
        """Универсально извлекает session_id из ссылки, параметра start, текста или payload."""
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

        # Отсекаем параметры URL если остались
        clean = clean.split("&")[0].split("?")[0].strip()
        if clean and re.match(r"^[A-Za-z0-9_\-]{6,64}$", clean):
            return clean
        return None

    @staticmethod
    def _extract_file_token(data: Any) -> Optional[str]:
        """
        Извлекает токен медиафайла из ответа сервера загрузки oneme.ru / dev.max.ru.
        Поддерживает форматы:
        - {"photos": {"0": {"token": "..."}}} (официальный ответ для картинок в oneme.ru)
        - {"photos": [{"token": "..."}]}
        - {"docs": ...} / {"files": ...}
        - {"token": "..."} / {"mediafile_token": "..."}
        """
        if not data:
            return None
        if isinstance(data, str):
            text = data.strip()
            # Проверка, не является ли сама строка JSON-объектом
            if text.startswith("{") and text.endswith("}"):
                try:
                    import json
                    parsed = json.loads(text)
                    return MaxBotService._extract_file_token(parsed)
                except Exception:
                    pass
            # Иначе ищем вхождение "token":"..." регулярным выражением
            match = re.search(r'"token"\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1).replace(r"\/", "/")
            return text if len(text) > 16 and not text.startswith("<") else None

        if not isinstance(data, dict):
            return None

        # 1. Специфика oneme.ru для photos: {"photos": {"0": {"token": "..."}}}
        photos = data.get("photos")
        if isinstance(photos, dict):
            for val in photos.values():
                if isinstance(val, dict) and val.get("token"):
                    return str(val["token"]).strip()
        elif isinstance(photos, list):
            for item in photos:
                if isinstance(item, dict) and item.get("token"):
                    return str(item["token"]).strip()

        # 2. Специфика docs / files / videos
        for container_key in ("docs", "files", "videos", "audios"):
            container = data.get(container_key)
            if isinstance(container, dict):
                for val in container.values():
                    if isinstance(val, dict) and val.get("token"):
                        return str(val["token"]).strip()
            elif isinstance(container, list):
                for item in container:
                    if isinstance(item, dict) and item.get("token"):
                        return str(item["token"]).strip()

        # 3. Прямые ключи
        for k in ("token", "mediafile_token", "file_token"):
            val = data.get(k)
            if val and isinstance(val, str):
                return val.strip()

        # 4. Рекурсивный поиск на случай глубокой вложенности
        for v in data.values():
            if isinstance(v, (dict, list)):
                found = MaxBotService._extract_file_token(v)
                if found:
                    return found

        return None

    @property
    def is_configured(self) -> bool:
        token = (getattr(settings, "MAX_BOT_TOKEN", "") or "").strip()
        return bool(token and len(token) > 5)

    @property
    def api_base(self) -> str:
        base = getattr(settings, "MAX_API_BASE", "https://platform-api2.max.ru") or "https://platform-api2.max.ru"
        return base.rstrip("/")

    @property
    def auth_headers(self) -> dict:
        token = (getattr(settings, "MAX_BOT_TOKEN", "") or "").strip()
        return {
            "Authorization": token,
            "Accept": "application/json",
            "User-Agent": "AI-Festival-Kiosk/1.0"
        }

    def _build_ssl_context(self) -> Union[ssl.SSLContext, bool]:
        """
        Создает SSL-контекст с поддержкой доверенных корневых сертификатов Минцифры РФ (Госуслуги)
        для взаимодействия с Bot API dev.max.ru / platform-api2.max.ru.
        """
        verify_ssl = getattr(settings, "MAX_BOT_VERIFY_SSL", True)
        if not verify_ssl:
            logger.info("MAX Bot: проверка SSL отключена через MAX_BOT_VERIFY_SSL=false")
            return False

        ca_bundle_path = Path(__file__).resolve().parent / "certs" / "russian_trusted_ca.pem"
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs()
            if ca_bundle_path.exists():
                ctx.load_verify_locations(cafile=str(ca_bundle_path))
                logger.debug("MAX Bot: загружены сертификаты Минцифры РФ из %s", ca_bundle_path)
            return ctx
        except Exception as e:
            logger.warning("MAX Bot: не удалось загрузить системные сертификаты (%s), пробуем cafile напрямую", e)
            try:
                if ca_bundle_path.exists():
                    return ssl.create_default_context(cafile=str(ca_bundle_path))
            except Exception:
                pass
            return False

    async def start(self):
        if not self.is_configured:
            logger.info("MAX Bot: MAX_BOT_TOKEN не настроен — сервис МАКС запускаться не будет")
            return

        self._running = True
        logger.info("MAX Bot: инициализация подключения к %s...", self.api_base)

        ssl_ctx = self._build_ssl_context()
        self._client = httpx.AsyncClient(
            verify=ssl_ctx,
            timeout=httpx.Timeout(connect=15.0, read=40.0, write=20.0, pool=30.0)
        )

        # 1. Проверяем токен и данные бота (GET /me или GET /users/me)
        connected = False
        try:
            resp = await self._client.get(f"{self.api_base}/me", headers=self.auth_headers)
            if resp.status_code == 404:
                resp = await self._client.get(f"{self.api_base}/users/me", headers=self.auth_headers)

            if resp.status_code == 200:
                user_data = resp.json()
                self.bot_username = user_data.get("username") or user_data.get("name") or user_data.get("first_name") or ""
                if not settings.MAX_BOT_USERNAME and self.bot_username:
                    settings.MAX_BOT_USERNAME = self.bot_username

                logger.info(
                    "🤖 MAX Bot подключен успешно: @%s (ID: %s, Имя: %s)",
                    self.bot_username or settings.MAX_BOT_USERNAME,
                    user_data.get("user_id"),
                    user_data.get("name") or user_data.get("first_name")
                )
                connected = True
            elif resp.status_code in (401, 403):
                logger.error("MAX Bot API: неверный токен (HTTP %s): %s", resp.status_code, resp.text[:120])
                self._running = False
                await self.stop()
                return
            else:
                logger.warning("MAX Bot /me вернул HTTP %s: %s", resp.status_code, resp.text[:120])
                connected = True
        except Exception as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                logger.warning("MAX Bot: ошибка проверки сертификата Минцифры. Переключаемся на verify=False fallback...")
                if self._client:
                    await self._client.aclose()
                self._client = httpx.AsyncClient(
                    verify=False,
                    timeout=httpx.Timeout(connect=15.0, read=40.0, write=20.0, pool=30.0)
                )
            else:
                logger.warning("MAX Bot: предупреждение при проверке /me: %s. Пробуем продолжить...", e)
            connected = True

        if not connected:
            self._running = False
            return

        # 2. Основной цикл Long Polling (GET /updates)
        logger.info("MAX Bot: запуск Long Polling цикла обновлений...")
        while self._running:
            try:
                params = {
                    "timeout": 25,
                    "types": "bot_started,message_created"
                }
                if self.last_marker is not None:
                    params["marker"] = str(self.last_marker)

                resp = await self._client.get(
                    f"{self.api_base}/updates",
                    params=params,
                    headers=self.auth_headers
                )

                if resp.status_code != 200:
                    logger.warning("MAX Bot /updates вернул HTTP %s: %s", resp.status_code, resp.text[:120])
                    await asyncio.sleep(3.0)
                    continue

                data = resp.json()
                new_marker = data.get("marker")
                if new_marker is not None:
                    self.last_marker = new_marker

                updates = data.get("updates", [])
                for upd in updates:
                    await self._handle_update(upd)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._running:
                    break
                err_str = str(e)
                if "CERTIFICATE_VERIFY_FAILED" in err_str:
                    logger.warning("MAX Bot: сбой сертификата в цикле polling. Переподключение с verify=False...")
                    if self._client:
                        try:
                            await self._client.aclose()
                        except Exception:
                            pass
                    self._client = httpx.AsyncClient(
                        verify=False,
                        timeout=httpx.Timeout(connect=15.0, read=40.0, write=20.0, pool=30.0)
                    )
                    await asyncio.sleep(1.0)
                    continue

                logger.warning("MAX Bot polling error: %s", e)
                await asyncio.sleep(2.0)

        logger.info("MAX Bot polling остановлен")

    async def stop(self):
        self._running = False
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    async def _handle_update(self, update: dict):
        """Обрабатывает события bot_started и message_created."""
        upd_type = update.get("update_type")

        # 1. Сценарий диплинка: пользователь открыл бота по QR https://max.ru/{bot}?start={session_id}
        if upd_type == "bot_started":
            chat_id = update.get("chat_id")
            user = update.get("user", {})
            if not chat_id:
                chat_id = user.get("user_id")

            payload = (update.get("payload") or "").strip()
            username = user.get("username")
            first_name = user.get("name") or user.get("first_name", "Мастер")

            logger.info("MAX bot_started: chat_id=%s payload=%s user=%s", chat_id, payload, username)

            if chat_id:
                session_id = self._extract_session_id(payload)
                if session_id:
                    await self._deliver_card(chat_id, session_id, username, first_name)
                else:
                    # Если payload был потерян/очищен клиентом, ищем недавнюю сессию пользователя или стенда
                    last_sess = db.get_last_session_for_chat(chat_id) or db.get_last_completed_session(max_age_seconds=1800)
                    if last_sess and last_sess.get("id"):
                        await self._deliver_card(chat_id, last_sess["id"], username, first_name, is_fallback=True)
                    else:
                        await self._send_welcome(chat_id, first_name)

        # 2. Пользователь отправил сообщение (например, /start <session_id> или текст)
        elif upd_type == "message_created":
            message = update.get("message", {})
            sender = message.get("sender", {})
            recipient = message.get("recipient", {})
            body = message.get("body", {})

            chat_id = recipient.get("chat_id") or sender.get("user_id")
            text = (body.get("text") or "").strip()
            username = sender.get("username")
            first_name = sender.get("name", "Мастер")

            if not chat_id:
                return

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

    async def _deliver_card(
        self,
        chat_id: int,
        session_id: str,
        username: Optional[str],
        first_name: str,
        is_fallback: bool = False
    ):
        """Находит карточку в SQLite, ждет завершения рендера и отправляет в чат МАКС."""
        extracted = self._extract_session_id(session_id)
        if extracted:
            session_id = extracted
        session_id = session_id.strip()

        logger.info("MAX: Доставка карточки для сессии %s в чат %s (@%s)", session_id, chat_id, username or "none")

        # 1. Поиск сессии в базе
        session = db.get_session(session_id)
        if not session:
            await asyncio.sleep(1.0)
            session = db.get_session(session_id)

        # 2. Ожидание завершения генерации до 30 секунд
        card_file = self._find_card_file(session_id, session)
        retries = 15
        while not card_file and retries > 0:
            if retries == 15:
                await self._send_message(
                    chat_id,
                    "⏳ Твой цифровой паспорт ещё куётся на «Станке Будущего»! Подожди пару секунд, сейчас пришлю..."
                )
            await asyncio.sleep(2.0)
            session = db.get_session(session_id) or session
            card_file = self._find_card_file(session_id, session)
            retries -= 1

        if not card_file or not card_file.is_file():
            await self._send_message(
                chat_id,
                f"⚠️ Не удалось найти готовую карточку для сессии {session_id}.\n\n"
                f"Пожалуйста, обратись к мастеру станка — он распечатает твой паспорт вручную!"
            )
            return

        # 3. Безопасное формирование текста карточки (защита от None session)
        session_safe = session or {}
        machine_name = session_safe.get("machine_name") or "Инженер Будущего"
        power_name = session_safe.get("power_name") or "Точность"
        location = session_safe.get("location") or "Центральный кластер"
        festival_name = getattr(settings, "FESTIVAL_NAME", "ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ МОСКВЫ")
        hashtag = getattr(settings, "FESTIVAL_HASHTAG", "#ФЕСТИВАЛЬ2026")

        greeting = "🎉 Твой цифровой паспорт готов!"
        if is_fallback:
            greeting += "\n(доставлен паспорт с недавней сессии на нашем станке)"

        caption = (
            f"{greeting}\n\n"
            f"🛠 Специальность: {machine_name}\n"
            f"⚡ Суперсила: {power_name}\n"
            f"📍 Гильдия: {location}\n\n"
            f"🏛 {festival_name}\n"
            f"{hashtag}"
        )

        # 4. Двухэтапная отправка изображения в МАКС
        success = await self._send_photo(chat_id, card_file, caption)
        if success:
            try:
                db.save_telegram_link(chat_id, session_id, username, first_name)
            except Exception as e:
                logger.warning("Не удалось зафиксировать delivery_link: %s", e)

            # Следующее сообщение через 2 секунды (требование ТЗ)
            try:
                await asyncio.sleep(2.0)
                follow_up_msg = (
                    "Приглашаем вас подписаться:\n\n"
                    "💬 MAX: https://max.ru/channel_cppm\n"
                    "✈️ Telegram: https://t.me/cppm_centre\n"
                    "💙 ВКонтакте: https://vk.ru/centre.cppm"
                )
                await self._send_message(chat_id, follow_up_msg)
                logger.info("MAX Bot: приглашение к подписке успешно отправлено в чат %s", chat_id)
            except Exception as e:
                logger.warning("MAX Bot: ошибка отправки follow-up сообщения с соцсетями: %s", e)

    async def _send_welcome(self, chat_id: int, first_name: str):
        msg = (
            f"👋 Привет, {first_name}!\n\n"
            f"Я официальный бот интерактивной фотолокации «Станок Будущего» в мессенджере МАКС.\n\n"
            f"📸 Как получить паспорт инженера:\n"
            f"1. Подойди к экрану нашего киоска.\n"
            f"2. Сделай фото и выбери черты своей специальности.\n"
            f"3. Наведи камеру смартфона на появившийся QR-код — и я моментально пришлю твою карточку сюда!"
        )
        await self._send_message(chat_id, msg)

    async def _send_help(self, chat_id: int, first_name: str):
        msg = (
            f"Привет, {first_name}!\n\n"
            f"Чтобы получить свою готовую карточку, отсканируй QR-код на экране фотолокации «Станок Будущего».\n"
            f"Если у тебя есть код сессии, отправь команду: /start код_сессии"
        )
        await self._send_message(chat_id, msg)

    async def _send_message(self, chat_id: int, text: str):
        if not self._client or not self.is_configured:
            return
        try:
            payload = {
                "text": text
            }
            await self._client.post(
                f"{self.api_base}/messages",
                params={"chat_id": chat_id},
                json=payload,
                headers=self.auth_headers,
                timeout=15.0
            )
        except Exception as e:
            logger.warning("MAX Bot sendMessage error: %s", e)

    async def _send_photo(self, chat_id: int, file_path: Path, caption: str) -> bool:
        """
        Отправляет фото в МАКС в два этапа:
        1. Запрос ссылки загрузки POST /uploads?type=image
        2. Отправка файла по полученной ссылке
        3. Отправка сообщения POST /messages с объектом attachments
        """
        if not self._client or not self.is_configured:
            return False

        try:
            # Шаг 1: Получаем слот для загрузки
            upload_slot_resp = await self._client.post(
                f"{self.api_base}/uploads",
                params={"type": "image"},
                headers=self.auth_headers,
                timeout=15.0
            )
            if upload_slot_resp.status_code != 200:
                logger.error("MAX Bot: ошибка /uploads (HTTP %s): %s", upload_slot_resp.status_code, upload_slot_resp.text[:120])
                return False

            slot_data = upload_slot_resp.json()
            upload_url = slot_data.get("url")
            if not upload_url:
                logger.error("MAX Bot: в ответе /uploads отсутствует поле 'url'")
                return False

            # Извлекаем mediafile_token из query параметров URL (если присутствует)
            parsed_url = urlparse(upload_url)
            qs_params = parse_qs(parsed_url.query)
            token = qs_params.get("mediafile_token", [None])[0] or slot_data.get("token") or slot_data.get("mediafile_token")

            # Шаг 2: Загружаем сам файл по upload_url
            with open(file_path, "rb") as f:
                photo_bytes = f.read()

            files = {"data": ("card.jpg", photo_bytes, "image/jpeg")}
            upload_resp = await self._client.post(upload_url, files=files, timeout=30.0)

            # Если токен не был в URL, извлекаем его из ответа сервера загрузки oneme.ru
            if not token and upload_resp.status_code == 200:
                try:
                    up_json = upload_resp.json()
                    token = self._extract_file_token(up_json)
                except Exception as e:
                    logger.warning("MAX Bot: ошибка парсинга JSON ответа загрузки: %s", e)

            # Резервный поиск по тексту, если JSON не распарсился
            if not token and upload_resp.status_code == 200:
                token = self._extract_file_token(upload_resp.text)

            if not token:
                logger.error("MAX Bot: не удалось определить токен файла после загрузки. Ответ (HTTP %s): %s", upload_resp.status_code, upload_resp.text[:200])
                return False

            # Шаг 3: Отправляем сообщение с вложением
            msg_payload = {
                "text": caption,
                "attachments": [
                    {
                        "type": "image",
                        "payload": {
                            "token": token
                        }
                    }
                ]
            }

            resp = await self._client.post(
                f"{self.api_base}/messages",
                params={"chat_id": chat_id},
                json=msg_payload,
                headers=self.auth_headers,
                timeout=20.0
            )

            if resp.status_code in (200, 201):
                logger.info("MAX Bot: карточка успешно доставлена в чат %s", chat_id)
                return True
            else:
                logger.error("MAX Bot: ошибка отправки сообщения с фото (HTTP %s): %s", resp.status_code, resp.text[:120])
                return False

        except Exception as e:
            logger.exception("MAX Bot send_photo exception: %s", e)
            return False


max_bot_service = MaxBotService()


async def start_max_bot():
    await max_bot_service.start()


async def stop_max_bot():
    await max_bot_service.stop()
