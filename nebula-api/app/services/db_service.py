"""Database operations for chat sessions and messages."""

from sqlalchemy.orm import Session

from app.models.db_models import ChatSession, Message


def get_all_session_ids(db: Session) -> list[str]:
    """Return all chat session IDs."""
    return [s.id for s in db.query(ChatSession.id).all()]


def get_chat_session_full(db: Session, session_id: str) -> ChatSession | None:
    """Return a full session row including mood, summary, and messages."""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def delete_chat_session(db: Session, session_id: str) -> bool:
    """Delete a session and all associated messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def save_message(db: Session, session_id: str, role: str, content: str) -> None:
    """Persist a single message row."""
    new_msg = Message(session_id=session_id, role=role, content=content)
    db.add(new_msg)
    db.commit()


def upsert_chat_session(
    db: Session,
    session_id: str,
    bot_name: str,
    bot_personality: str,
    mood: int,
) -> None:
    """Create or update session metadata (mood, bot profile)."""
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db_session.mood = mood
    else:
        db_session = ChatSession(
            id=session_id,
            bot_name=bot_name,
            bot_personality=bot_personality,
            mood=mood,
        )
        db.add(db_session)
    db.commit()
