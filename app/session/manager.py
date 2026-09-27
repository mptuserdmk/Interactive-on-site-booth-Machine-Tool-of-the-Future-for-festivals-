import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.config.settings import settings
from app.storage.database import db
from app.storage.files import clean_session_source_photo
from app.session.models import SessionState, SessionData
from app.quiz.combinations import combination_manager
from app.ai.manager import ai_manager
from app.ai.models import AIGenerationRequest
from app.ai.prompts import build_ai_prompt
from app.composition.composer import card_composer
from app.printing.manager import print_manager

class SessionManager:
    def __init__(self):
        self.active_session: Optional[SessionData] = None
        self._listeners = []

    def add_listener(self, callback):
        self._listeners.append(callback)

    async def _notify_listeners(self):
        if self.active_session:
            data = self.active_session.model_dump()
            for cb in self._listeners:
                try:
                    await cb(data)
                except Exception as e:
                    print(f"Error in session event listener: {e}")

    def create_session(self) -> SessionData:
        sess_id = f"sess_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}"
        session = SessionData(
            id=sess_id,
            created_at=datetime.utcnow().isoformat(),
            status=SessionState.PHOTO_PENDING
        )
        self.active_session = session
        db.save_session(session.model_dump())
        return session

    def get_active_session(self) -> Optional[SessionData]:
        return self.active_session

    async def update_status(self, new_status: SessionState, error_msg: Optional[str] = None):
        if not self.active_session:
            return
        self.active_session.status = new_status
        if error_msg:
            self.active_session.error_message = error_msg
        db.save_session(self.active_session.model_dump())
        await self._notify_listeners()

    async def attach_photo(self, photo_path: Path):
        if not self.active_session:
            self.create_session()
        self.active_session.photo_path = str(photo_path)
        self.active_session.status = SessionState.PHOTO_TAKEN
        db.save_session(self.active_session.model_dump())
        await self._notify_listeners()

    async def confirm_photo(self):
        if not self.active_session or not self.active_session.photo_path:
            raise ValueError("No photo available to confirm")
        self.active_session.status = SessionState.QUIZ_ELEMENT
        db.save_session(self.active_session.model_dump())
        await self._notify_listeners()

    async def retake_photo(self):
        if not self.active_session:
            return
        self.active_session.photo_path = None
        self.active_session.status = SessionState.PHOTO_PENDING
        db.save_session(self.active_session.model_dump())
        await self._notify_listeners()

    async def set_quiz_answer(self, question_type: str, answer_id: str):
        if not self.active_session:
            self.create_session()

        if question_type == "element":
            self.active_session.element = answer_id
            self.active_session.status = SessionState.QUIZ_POWER
        elif question_type == "power":
            self.active_session.power = answer_id
            self.active_session.status = SessionState.QUIZ_COLOR
        elif question_type == "color":
            self.active_session.color = answer_id
            # All 3 choices made, resolve combination
            await self._resolve_combination_and_start()

        db.save_session(self.active_session.model_dump())
        await self._notify_listeners()

    async def _resolve_combination_and_start(self):
        sess = self.active_session
        if not (sess.element and sess.power and sess.color):
            return

        combo = combination_manager.find(sess.element, sess.power, sess.color)
        if not combo:
            # Fallback to default combination #1
            combo = combination_manager.get_by_id(1)

        sess.combination_id = combo["id"]
        sess.element_name = combo["element_name"]
        sess.power_name = combo["power_name"]
        sess.color_name = combo["color_name"]
        sess.machine_name = combo["machine_name"]
        sess.machine_desc = combo["description"]
        sess.location = combo["location"]
        sess.status = SessionState.GENERATING
        
        db.save_session(sess.model_dump())
        await self._notify_listeners()

        # Run pipeline in background
        import asyncio
        asyncio.create_task(self._run_generation_and_composition_pipeline(combo))

    async def _run_generation_and_composition_pipeline(self, combo: Dict[str, Any]):
        sess = self.active_session
        start_time = time.time()
        try:
            # 1. AI Generation
            gen_out = settings.GENERATED_DIR / f"{sess.id}_ai.jpg"
            prompt = build_ai_prompt(combo)
            
            ai_req = AIGenerationRequest(
                session_id=sess.id,
                element=sess.element,
                power=sess.power,
                color=sess.color,
                prompt=prompt,
                input_photo_path=sess.photo_path or str(settings.STORAGE_DIR / "sample.jpg")
            )
            
            ai_result = await ai_manager.generate_image(ai_req, combo, gen_out)
            
            if not ai_result.success:
                sess.status = SessionState.ERROR
                sess.error_message = f"AI Error: {ai_result.error}"
                db.save_session(sess.model_dump())
                await self._notify_listeners()
                return

            sess.generated_image_path = ai_result.image_path
            sess.status = SessionState.COMPOSING
            db.save_session(sess.model_dump())
            await self._notify_listeners()

            # 2. Local Pillow Card Composition
            card_out = settings.CARDS_DIR / f"{sess.id}_card.jpg"
            card_composer.compose_card(
                session_id=sess.id,
                ai_image_path=Path(ai_result.image_path),
                combo=combo,
                output_path=card_out
            )
            
            sess.final_card_path = str(card_out)
            sess.status = SessionState.READY_TO_PRINT
            sess.duration_seconds = round(time.time() - start_time, 2)
            db.save_session(sess.model_dump())
            await self._notify_listeners()

            # 3. Print
            if settings.ENABLE_AUTO_PRINT:
                await self.trigger_print()

        except Exception as e:
            print(f"Pipeline error: {e}")
            sess.status = SessionState.ERROR
            sess.error_message = str(e)
            db.save_session(sess.model_dump())
            await self._notify_listeners()

    async def trigger_print(self):
        sess = self.active_session
        if not sess or not sess.final_card_path:
            return
        
        sess.status = SessionState.PRINTING
        sess.print_status = "printing"
        db.save_session(sess.model_dump())
        await self._notify_listeners()

        print_res = await print_manager.print_card(Path(sess.final_card_path), sess.id)
        
        if print_res.get("success"):
            sess.print_status = "printed"
            sess.status = SessionState.COMPLETED
            # Privacy cleanup: delete original raw photo
            clean_session_source_photo(sess.id, sess.photo_path)
        else:
            sess.print_status = "error"
            sess.error_message = print_res.get("error")

        db.save_session(sess.model_dump())
        await self._notify_listeners()

    async def reprint_session(self, session_id: str) -> Dict[str, Any]:
        """Reprint any previous card without calling AI again!"""
        sess_dict = db.get_session(session_id)
        if not sess_dict or not sess_dict.get("final_card_path"):
            return {"success": False, "error": "Session card not found"}
        
        card_path = Path(sess_dict["final_card_path"])
        res = await print_manager.print_card(card_path, session_id)
        return res

session_manager = SessionManager()
