import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.config.settings import settings

class Database:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or settings.DB_PATH)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    element TEXT,
                    element_name TEXT,
                    power TEXT,
                    power_name TEXT,
                    color TEXT,
                    color_name TEXT,
                    combination_id INTEGER,
                    machine_name TEXT,
                    machine_desc TEXT,
                    location TEXT,
                    photo_path TEXT,
                    generated_image_path TEXT,
                    final_card_path TEXT,
                    print_status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    duration_seconds REAL,
                    meta_json TEXT
                )
            """)
            conn.commit()

    def save_session(self, data: Dict[str, Any]):
        now = datetime.utcnow().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sessions (
                    id, created_at, updated_at, status, element, element_name,
                    power, power_name, color, color_name, combination_id,
                    machine_name, machine_desc, location, photo_path,
                    generated_image_path, final_card_path, print_status,
                    error_message, duration_seconds, meta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("id"),
                data.get("created_at", now),
                now,
                data.get("status", "IDLE"),
                data.get("element"),
                data.get("element_name"),
                data.get("power"),
                data.get("power_name"),
                data.get("color"),
                data.get("color_name"),
                data.get("combination_id"),
                data.get("machine_name"),
                data.get("machine_desc"),
                data.get("location"),
                data.get("photo_path"),
                data.get("generated_image_path"),
                data.get("final_card_path"),
                data.get("print_status", "pending"),
                data.get("error_message"),
                data.get("duration_seconds"),
                json.dumps(data.get("meta", {}))
            ))
            conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("meta_json"):
                    try:
                        d["meta"] = json.loads(d["meta_json"])
                    except Exception:
                        d["meta"] = {}
                return d
            return None

    def get_recent_sessions(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

db = Database()
