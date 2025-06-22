import os
from datetime import datetime, timezone
from typing import Union, List
from sqlalchemy import create_engine, func, Column, String, Float, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    token = Column(String, primary_key=True)
    email = Column(String)
    ip = Column(String)
    created_at = Column(String)
    delivery_date = Column(String)
    original_audio = Column(String)
    ai_audio = Column(String)
    transcript = Column(String)
    enhanced_text = Column(String)
    voice_id = Column(String)
    delivered_at = Column(String, nullable=True)

class CostLog(Base):
    __tablename__ = 'cost_log'
    token = Column(String, primary_key=True)
    duration_sec = Column(Float)
    gpt_input = Column(Integer)
    gpt_output = Column(Integer)
    tts_chars = Column(Integer)
    cost_usd = Column(Float, nullable=True)


# ---- UTILS ----

def strip_path(path):
    return os.path.basename(path) if path else path

def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

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
    """Insert a new message."""
    session = SessionLocal()
    try:
        msg = Message(
            token=token,
            email=email,
            ip=ip,
            created_at=created_at,
            delivery_date=delivery_date,
            original_audio=original_audio,
            ai_audio=ai_audio,
            transcript=transcript,
            enhanced_text=enhanced_text,
            voice_id=voice_id,
            delivered_at=None,
        )
        session.add(msg)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()

def mark_message_delivered(token: str) -> None:
    """Mark a message as delivered by setting delivered_at to now."""
    session = SessionLocal()
    try:
        msg = session.query(Message).filter_by(token=token).first()
        if msg:
            msg.delivered_at = datetime.now(timezone.utc).isoformat()
            session.commit()
    finally:
        session.close()

def get_message_by_token(token: str) -> Union[dict, None]:
    """Retrieve a message by its token."""
    session = SessionLocal()
    try:
        msg = session.query(Message).filter_by(token=token).first()
        return msg.__dict__ if msg else None
    finally:
        session.close()

def get_due_undelivered_messages(today: str) -> List[dict]:
    """Retrieve all messages scheduled for today that haven't been delivered."""
    session = SessionLocal()
    try:
        msgs = session.query(Message).filter_by(delivery_date=today, delivered_at=None).all()
        return [msg.__dict__ for msg in msgs]
    finally:
        session.close()

def count_submissions_by_ip(ip: str, date_str: str) -> int:
    """Count how many submissions an IP made on a specific date."""
    session = SessionLocal()
    try:
        count = session.query(func.count(Message.token)).filter(
            Message.ip == ip,
            func.DATE(Message.created_at) == date_str
        ).scalar()
        return count
    finally:
        session.close()
