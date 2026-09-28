import asyncio
import logging
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Set
from app.config.settings import settings
from app.storage.database import db
from app.storage.files import delete_file_safely
from app.session.models import SessionState, SessionData
from app.quiz.combinations import combination_manager
from app.quiz.engine import is_valid_answer
from app.ai.manager import ai_manager
from app.ai.models import AIGenerationRequest
from app.ai.prompts import build_ai_prompt
from app.composition.composer import card_composer
from app.printing.manager import print_manager

logger = logging.getLogger("stanok.session")

PHOTO_STATES = {SessionState.PHOTO_PENDING, SessionState.PHOTO_TAKEN}
TERMINAL_STATES = {SessionState.IDLE, SessionState.COMPLETED, SessionState.ERROR}
CANCELLABLE_STATES = {SessionState.GENERATING, SessionState.COMPOSING}

# question_type -> (статус, в котором вопрос допустим, следующий статус)
QUIZ_STEPS = {
    "element": (SessionState.QUIZ_ELEMENT, SessionState.QUIZ_POWER),
    "power": (SessionState.QUIZ_POWER, SessionState.QUIZ_COLOR),
    "color": (SessionState.QUIZ_COLOR, SessionState.GENERATING),
}


class SessionError(Exception):
    """Ошибка бизнес-логики сессии; status_code уходит клиенту как HTTP-код."""
    status_code = 409


class InvalidTransition(SessionError):
    status_code = 409


class InvalidAnswer(SessionError):
    status_code = 422


class SessionNotFound(SessionError):
    status_code = 404


class RateLimited(SessionError):
    status_code = 429


class SessionManager:
    def __init__(self):
        self.active_session: Optional[SessionData] = None
        self._listeners = []
        # Фоновые пайплайны по id сессии: пайплайн работает со СВОЕЙ сессией, а не с active_session (H3)
        self._tasks: Dict[str, asyncio.Task] = {}
        # Сессии, для которых печать уже зарезервирована/идёт — защита от двойной печати
        self._printing: Set[str] = set()
        self._last_reprint: Dict[str, float] = {}

    def add_listener(self, callback):
        self._listeners.append(callback)

    async def _notify(self, sess: Optional[SessionData] = None):
        """Рассылает состояние киоску. Сессии, отвязанные от киоска (фоновая допечатка
        после «Новая сессия»/«Сброс»), не транслируются — иначе киоск «прыгает» назад."""
        if sess is None:
            active = self.active_session
            data = active.model_dump() if active else {"id": None, "status": SessionState.IDLE.value}
        elif sess is self.active_session:
            data = sess.model_dump()
        else:
            return
        for cb in list(self._listeners):
            try:
                await cb(data)
            except Exception:
                logger.exception("Error in session event listener")

    async def _notify_listeners(self):
        await self._notify()

    def _save(self, sess: SessionData):
        db.save_session(sess.model_dump())

    def _require(self, allowed: Set[SessionState], action: str) -> SessionData:
        sess = self.active_session
        if not sess or sess.status not in allowed:
            status = sess.status.value if sess else "нет активной сессии"
            raise InvalidTransition(f"Действие «{action}» недоступно: {status}")
        return sess

    def _cleanup_personal_files(self, sess: SessionData):
        """Фото ребёнка и AI-портрет с его лицом больше не нужны, когда карточка собрана
        или сессия завершилась неудачей/брошена (H15). Карточку удаляет retention-скрипт."""
        if settings.DELETE_SOURCE_PHOTOS_AFTER_PRINT:
            delete_file_safely(sess.photo_path)
            delete_file_safely(sess.generated_image_path)

    def _detach_active(self, cancel_generation: bool):
        """Отвязывает активную сессию от киоска.
        GENERATING/COMPOSING: при сбросе генерация отменяется, при «Новая сессия» — дорабатывает в фоне
        и печатает СВОЮ карточку. READY_TO_PRINT/PRINTING: печать всегда завершается в фоне.
        Фото/квиз: сессия брошена → IDLE, фото удаляется. Терминальные статусы в истории не трогаем (H4)."""
        sess = self.active_session
        if not sess:
            return
        self.active_session = None
        if sess.status in CANCELLABLE_STATES:
            task = self._tasks.get(sess.id)
            if cancel_generation and task and not task.done():
                task.cancel()
        elif sess.status in PHOTO_STATES or sess.status.value.startswith("QUIZ_"):
            sess.status = SessionState.IDLE
            self._save(sess)
            self._cleanup_personal_files(sess)

    def create_session(self) -> SessionData:
        self._detach_active(cancel_generation=False)
        session = SessionData(
            id=f"sess_{secrets.token_hex(16)}",
            created_at=datetime.now(timezone.utc).isoformat(),
            status=SessionState.PHOTO_PENDING
        )
        self.active_session = session
        self._save(session)
        return session

    async def new_session(self) -> SessionData:
        session = self.create_session()
        await self._notify(session)
        return session

    def get_active_session(self) -> Optional[SessionData]:
        return self.active_session

    async def reset(self):
        self._detach_active(cancel_generation=True)
        await self._notify()

    async def update_status(self, new_status: SessionState, error_msg: Optional[str] = None):
        if new_status == SessionState.IDLE:
            await self.reset()
            return
        if not self.active_session:
            return
        self.active_session.status = new_status
        if error_msg:
            self.active_session.error_message = error_msg
        self._save(self.active_session)
        await self._notify(self.active_session)

    def begin_photo(self) -> SessionData:
        """Сессия для нового фото (USB или телефон ассистента). Если активной нет или она завершена —
        начинается новая; во время квиза и генерации фото принять нельзя."""
        sess = self.active_session
        if sess is None or sess.status in TERMINAL_STATES:
            return self.create_session()
        if sess.status in PHOTO_STATES:
            return sess
        raise InvalidTransition(f"Фото сейчас принять нельзя: {sess.status.value}")

    async def attach_photo(self, session_id: str, photo_path: Path):
        sess = self.active_session
        if not sess or sess.id != session_id or sess.status not in PHOTO_STATES:
            delete_file_safely(str(photo_path))
            raise InvalidTransition("Сессия изменилась, пока сохранялось фото")
        sess.photo_path = str(photo_path)
        sess.status = SessionState.PHOTO_TAKEN
        self._save(sess)
        await self._notify(sess)

    async def confirm_photo(self):
        sess = self._require({SessionState.PHOTO_TAKEN}, "подтвердить фото")
        if not sess.photo_path:
            raise InvalidTransition("Нет фото для подтверждения")
        sess.status = SessionState.QUIZ_ELEMENT
        self._save(sess)
        await self._notify(sess)

    async def retake_photo(self):
        sess = self._require(PHOTO_STATES, "переснять фото")
        delete_file_safely(sess.photo_path)
        sess.photo_path = None
        sess.status = SessionState.PHOTO_PENDING
        self._save(sess)
        await self._notify(sess)

    async def set_quiz_answer(self, question_type: str, answer_id: str):
        if question_type not in QUIZ_STEPS or not is_valid_answer(question_type, answer_id):
            raise InvalidAnswer(f"Недопустимый ответ: {question_type}={answer_id[:32]!r}")
        expected, next_status = QUIZ_STEPS[question_type]
        # Проверка и смена статуса идут без await → повторный тап (H2) увидит уже новый статус
        sess = self._require({expected}, f"ответ «{question_type}»")

        if question_type == "color":
            combo = combination_manager.find(sess.element, sess.power, answer_id)
            if not combo:
                raise InvalidAnswer("Комбинация не найдена")
            sess.color = answer_id
            sess.combination_id = combo["id"]
            sess.element_name = combo["element_name"]
            sess.power_name = combo["power_name"]
            sess.color_name = combo["color_name"]
            sess.machine_name = combo["machine_name"]
            sess.machine_desc = combo["description"]
            sess.location = combo["location"]
            sess.status = SessionState.GENERATING
            self._save(sess)
            self._start_pipeline(sess, combo)
        else:
            setattr(sess, question_type, answer_id)
            sess.status = next_status
            self._save(sess)

        await self._notify(sess)

    def _start_pipeline(self, sess: SessionData, combo: Dict[str, Any]):
        task = asyncio.get_running_loop().create_task(
            self._run_generation_and_composition_pipeline(sess, combo), name=f"pipeline-{sess.id}")
        self._tasks[sess.id] = task
        task.add_done_callback(lambda t, sid=sess.id: self._tasks.pop(sid, None))

    async def _fail(self, sess: SessionData, public_message: str):
        sess.status = SessionState.ERROR
        sess.error_message = public_message
        self._save(sess)
        self._cleanup_personal_files(sess)
        await self._notify(sess)

    async def _run_generation_and_composition_pipeline(self, sess: SessionData, combo: Dict[str, Any]):
        start_time = time.time()
        try:
            # 1. AI Generation
            gen_out = settings.GENERATED_DIR / f"{sess.id}_ai.jpg"
            ai_req = AIGenerationRequest(
                session_id=sess.id,
                element=sess.element,
                power=sess.power,
                color=sess.color,
                prompt=build_ai_prompt(combo),
                input_photo_path=sess.photo_path or str(settings.STORAGE_DIR / "sample.jpg")
            )
            ai_result = await ai_manager.generate_image(ai_req, combo, gen_out)
            sess.meta.update({
                "ai_provider": ai_result.provider_name,
                "ai_fallback": ai_result.is_fallback,
                "ai_seconds": ai_result.duration_seconds,
            })

            if not ai_result.success:
                logger.error("AI generation failed for %s: %s", sess.id, ai_result.error)
                await self._fail(sess, "Не удалось создать изображение: AI недоступен")
                return

            sess.generated_image_path = ai_result.image_path
            sess.status = SessionState.COMPOSING
            self._save(sess)
            await self._notify(sess)

            # 2. Pillow-композиция в пуле потоков: не блокирует event loop (H13)
            card_out = settings.CARDS_DIR / f"{sess.id}_card.jpg"
            await asyncio.to_thread(
                card_composer.compose_card,
                session_id=sess.id,
                ai_image_path=Path(ai_result.image_path),
                combo=combo,
                output_path=card_out
            )

            sess.final_card_path = str(card_out)
            sess.status = SessionState.READY_TO_PRINT
            sess.duration_seconds = round(time.time() - start_time, 2)
            self._save(sess)
            self._cleanup_personal_files(sess)
            auto_print = settings.ENABLE_AUTO_PRINT
            if auto_print:
                self._printing.add(sess.id)  # резерв до первого await: ручная печать сюда не влезет
            await self._notify(sess)

            # 3. Print — всегда своей сессии, даже если киоск уже перешёл к следующему посетителю
            if auto_print:
                await self._print(sess)

        except asyncio.CancelledError:
            sess.status = SessionState.IDLE
            sess.error_message = "Генерация прервана сбросом"
            self._save(sess)
            self._cleanup_personal_files(sess)
            self._printing.discard(sess.id)
            raise
        except Exception:
            logger.exception("Pipeline error for %s", sess.id)
            self._printing.discard(sess.id)
            await self._fail(sess, "Не удалось собрать карточку")

    async def _print(self, sess: SessionData):
        self._printing.add(sess.id)
        try:
            sess.status = SessionState.PRINTING
            sess.print_status = "printing"
            self._save(sess)
            await self._notify(sess)

            print_res = await print_manager.print_card(Path(sess.final_card_path), sess.id)

            if print_res.get("success"):
                sess.print_status = "printed"
                sess.status = SessionState.COMPLETED
                sess.error_message = None
            else:
                # Раньше статус навсегда оставался PRINTING
                sess.print_status = "error"
                sess.status = SessionState.ERROR
                sess.error_message = f"Ошибка печати: {print_res.get('error') or 'принтер не ответил'}"
            self._save(sess)
            await self._notify(sess)
        finally:
            self._printing.discard(sess.id)

    async def trigger_print(self):
        """Ручная печать активной сессии (оператор): только готовая карточка, без двойной печати."""
        sess = self.active_session
        if (not sess or not sess.final_card_path
                or sess.status not in (SessionState.READY_TO_PRINT, SessionState.ERROR)
                or sess.id in self._printing):
            status = sess.status.value if sess else "нет активной сессии"
            raise InvalidTransition(f"Печатать нечего или печать уже идёт: {status}")
        self._printing.add(sess.id)
        task = asyncio.get_running_loop().create_task(self._print(sess), name=f"print-{sess.id}")
        self._tasks[f"print-{sess.id}"] = task
        task.add_done_callback(lambda t, key=f"print-{sess.id}": self._tasks.pop(key, None))

    async def reprint_session(self, session_id: str) -> Dict[str, Any]:
        """Reprint any previous card without calling AI again!"""
        sess_dict = db.get_session(session_id)
        if not sess_dict or not sess_dict.get("final_card_path"):
            raise SessionNotFound("Карточка не найдена")
        if session_id in self._printing:
            raise InvalidTransition("Карточка уже печатается")
        now = time.monotonic()
        last = self._last_reprint.get(session_id)
        if last is not None and now - last < settings.REPRINT_COOLDOWN_SECONDS:
            raise RateLimited(f"Повторная печать не чаще раза в {settings.REPRINT_COOLDOWN_SECONDS} с")
        self._last_reprint[session_id] = now

        card_path = Path(sess_dict["final_card_path"])
        self._printing.add(session_id)
        try:
            return await print_manager.print_card(card_path, session_id)
        finally:
            self._printing.discard(session_id)


session_manager = SessionManager()
