import asyncio
import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.config.settings import settings
from app.session.models import SessionData
from app.storage.database import db

logger = logging.getLogger("stanok.email")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class EmailService:
    def __init__(self):
        self._lock = asyncio.Lock()

    def is_valid_email(self, email: str) -> bool:
        if not email or len(email) < 5 or len(email) > 128:
            return False
        return bool(EMAIL_REGEX.match(email.strip()))

    async def send_card_email(self, recipient_email: str, session: Any) -> Dict[str, Any]:
        """
        Отправляет интерактивный паспорт инженера на указанный email.
        Если SMTP_HOST не настроен, работает в бесперебойном демонстрационном режиме
        с записью в лог и сохранением метаданных сессии.
        """
        email = recipient_email.strip()
        if not self.is_valid_email(email):
            raise ValueError(f"Некорректный адрес электронной почты: {email}")

        # Универсальное извлечение полей для SessionData и dict
        if isinstance(session, dict):
            session_id = session.get("id")
            card_path_str = session.get("final_card_path")
            machine_name = session.get("machine_name") or "Инженер Будущего"
            power_name = (session.get("power_name") or "Точность").upper()
            machine_desc = session.get("machine_desc") or "Специалист передовой индустрии и мастер чудес."
        else:
            session_id = getattr(session, "id", None)
            card_path_str = getattr(session, "final_card_path", None)
            machine_name = getattr(session, "machine_name", None) or "Инженер Будущего"
            power_name = (getattr(session, "power_name", None) or "Точность").upper()
            machine_desc = getattr(session, "machine_desc", None) or "Специалист передовой индустрии и мастер чудес."

        if not card_path_str:
            raise ValueError("У сессии отсутствует сгенерированный паспорт (final_card_path). Сначала завершите создание карточки.")

        card_path = Path(card_path_str)
        digital_card_url = f"{settings.BASE_URL}/card/{session_id}"

        # Если SMTP настроен — выполняем реальную отправку
        if settings.SMTP_HOST and settings.SMTP_USER:
            try:
                await asyncio.to_thread(
                    self._send_via_smtp,
                    to_email=email,
                    session_id=session_id,
                    machine_name=machine_name,
                    power_name=power_name,
                    machine_desc=machine_desc,
                    digital_card_url=digital_card_url,
                    card_path=card_path
                )
                logger.info("Real email successfully sent to %s for session %s", email, session_id)
                self._record_success(session, email, simulated=False)
                return {
                    "status": "ok",
                    "simulated": False,
                    "recipient": email,
                    "message": f"Паспорт успешно отправлен на {email}"
                }
            except Exception as e:
                logger.exception("Failed to send real email to %s: %s", email, e)
                raise RuntimeError(f"Ошибка отправки почты через SMTP: {e}")

        # Иначе — режим демонстрационной/офлайн симуляции (для выставок без внешнего SMTP)
        logger.info(
            "[EMAIL SIMULATION] Card for session %s dispatched to %s. Link: %s",
            session_id, email, digital_card_url
        )
        self._record_success(session, email, simulated=True)
        return {
            "status": "ok",
            "simulated": True,
            "recipient": email,
            "message": f"Паспорт успешно отправлен на {email} (демонстрационный режим)"
        }

    def _send_via_smtp(
        self,
        to_email: str,
        session_id: str,
        machine_name: str,
        power_name: str,
        machine_desc: str,
        digital_card_url: str,
        card_path: Optional[Path]
    ):
        msg = MIMEMultipart("mixed")
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER or "noreply@kiosk-future.ru"
        msg["To"] = to_email
        msg["Subject"] = f"Твой Паспорт Мастера: {machine_name} — Осенний Промышленный Фестиваль Колледжей Москвы"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #FBF8F1; color: #1E1E1E; margin: 0; padding: 24px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #F4EEDA; border: 2px solid #C59A45; border-radius: 16px; padding: 32px 24px; text-align: center; box-shadow: 0 10px 30px rgba(139, 101, 27, 0.2); }}
    .stamp {{ font-family: monospace; font-size: 11px; font-weight: bold; letter-spacing: 2px; color: #BA1B1D; text-transform: uppercase; margin-bottom: 12px; }}
    h1 {{ font-family: Georgia, serif; font-size: 30px; margin: 10px 0; color: #121820; }}
    .power {{ font-family: monospace; color: #8B651B; font-weight: bold; font-size: 13px; letter-spacing: 1px; margin-bottom: 16px; }}
    .quote {{ font-family: Georgia, serif; font-style: italic; font-size: 16px; line-height: 1.5; color: #3B3835; margin: 20px 0; background: #FAF7F0; padding: 16px; border-radius: 10px; border-left: 3px solid #C59A45; text-align: left; }}
    .btn {{ display: inline-block; background: #BA1B1D; color: #FFFFFF !important; text-decoration: none; padding: 14px 28px; border-radius: 10px; font-weight: bold; font-size: 15px; margin: 20px 0; border: 2px solid #E8CA7B; }}
    .footer {{ font-family: monospace; font-size: 11px; color: #686662; margin-top: 24px; border-top: 1px solid rgba(197, 154, 69, 0.3); padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="stamp">⚙️ ОСЕННИЙ ПРОМЫШЛЕННЫЙ ФЕСТИВАЛЬ КОЛЛЕДЖЕЙ МОСКВЫ</div>
    <h1>{machine_name}</h1>
    <div class="power">СУПЕРСИЛА: {power_name}</div>
    <div class="quote">"{machine_desc}"</div>
    <a href="{digital_card_url}" class="btn">ОТКРЫТЬ ЦИФРОВОЙ ПАСПОРТ</a>
    <p style="font-size: 13px; color: #686662; margin-top: 12px;">Оригинал карточки 300 DPI также прикреплен к этому письму.</p>
    <div class="footer">
      ОТ ТРАДИЦИЙ К БОЛЬШИМ ВОЗМОЖНОСТЯМ<br>
      ЗНАНИЯ • ТЕХНОЛОГИИ • ЛЮДИ • БУДУЩЕЕ • МОСКВА 2026
    </div>
  </div>
</body>
</html>"""

        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if card_path and card_path.is_file():
            try:
                with open(card_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=f"passport_{session_id}.jpg")
                    part["Content-Disposition"] = f'attachment; filename="passport_{session_id}.jpg"'
                    msg.attach(part)
            except Exception as e:
                logger.warning("Could not attach card file %s: %s", card_path, e)

        # Отправка через сокет
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

    def _record_success(self, session: Any, email: str, simulated: bool):
        now_str = datetime.now(timezone.utc).isoformat()
        if isinstance(session, dict):
            if "meta" not in session or not isinstance(session["meta"], dict):
                session["meta"] = {}
            session["meta"]["email_sent"] = True
            session["meta"]["email_recipient"] = email
            session["meta"]["email_sent_at"] = now_str
            session["meta"]["email_simulated"] = simulated
            db.save_session(session)
        else:
            if not getattr(session, "meta", None):
                session.meta = {}
            session.meta["email_sent"] = True
            session.meta["email_recipient"] = email
            session.meta["email_sent_at"] = now_str
            session.meta["email_simulated"] = simulated
            db.save_session(session.model_dump())


email_service = EmailService()
