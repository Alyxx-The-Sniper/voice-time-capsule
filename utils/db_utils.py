import sqlite3
from datetime import datetime, timezone
from typing import Union
import os

DB_PATH = "db.sqlite"

def strip_path(path):
    return os.path.basename(path) if path else path

def init_db():
    """Initialize database and create required tables if they don't exist.
    Also adds delivered_at and ip columns if missing (for legacy dbs)."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Messages table (with delivered_at and ip columns)
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                token TEXT PRIMARY KEY,
                email TEXT,
                ip TEXT,
                created_at TEXT,
                delivery_date TEXT,
                original_audio TEXT,
                ai_audio TEXT,
                transcript TEXT,
                enhanced_text TEXT,
                voice_id TEXT,
                delivered_at TEXT
            )
        ''')

        # For legacy: add delivered_at and ip if they don't exist
        c.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in c.fetchall()]
        if "delivered_at" not in columns:
            c.execute("ALTER TABLE messages ADD COLUMN delivered_at TEXT")
        if "ip" not in columns:
            c.execute("ALTER TABLE messages ADD COLUMN ip TEXT")

        # Cost log table
        c.execute('''
            CREATE TABLE IF NOT EXISTS cost_log (
                token TEXT PRIMARY KEY,
                duration_sec REAL,
                gpt_input INTEGER,
                gpt_output INTEGER,
                tts_chars INTEGER,
                cost_usd REAL
            )
        ''')

        conn.commit()

def insert_message(
    token: str,
    email: str,
    ip: str,
    created_at: str,
    delivery_date: str,
    original_audio: str,
    ai_audio: str,
    transcript: str,
    enhanced_text: str,
    voice_id: str
) -> None:
    """Insert a new message into the messages table."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO messages (
                token, email, ip, created_at, delivery_date,
                original_audio, ai_audio, transcript, enhanced_text, voice_id, delivered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        ''', (
            token,
            email,
            ip,
            created_at,
            delivery_date,
            original_audio,
            ai_audio,
            transcript,
            enhanced_text,
            voice_id
        ))
        conn.commit()

def mark_message_delivered(token: str) -> None:
    """Mark a message as delivered by setting delivered_at to now."""
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE messages SET delivered_at = ? WHERE token = ?", (now, token))
        conn.commit()

def get_message_by_token(token: str) -> Union[dict, None]:
    """Retrieve a message by its token."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE token = ?", (token,))
        row = c.fetchone()
        return dict(row) if row else None

def get_due_undelivered_messages(today: str) -> list[dict]:
    """Retrieve all messages scheduled for today that haven't been delivered."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE delivery_date = ? AND delivered_at IS NULL", (today,))
        rows = c.fetchall()
        return [dict(row) for row in rows]

def count_submissions_by_ip(ip: str, date_str: str) -> int:
    """Count how many submissions an IP made on a specific date."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM messages
            WHERE ip = ? AND DATE(created_at) = ?
        ''', (ip, date_str))
        return c.fetchone()[0]
