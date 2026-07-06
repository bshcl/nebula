"""Query and update session memory (titles, summaries, archival flags)."""

from sqlalchemy.orm import Session

from app.models.db_models import ChatSession, Message


class MemoryService:
    """Helpers for unarchived message reads and session memory updates."""

    @staticmethod
    def get_unarchived_messages(db: Session, session_id: str) -> list[Message]:
        """Return unarchived messages for a session, oldest first."""
        return (
            db.query(Message)
            .filter(Message.session_id == session_id, Message.is_archived.is_(False))
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def get_unarchived_messages_count(db: Session, session_id: str) -> int:
        """Count unarchived messages for a session."""
        return (
            db.query(Message)
            .filter(Message.session_id == session_id, Message.is_archived.is_(False))
            .count()
        )

    @staticmethod
    def update_session_title(db: Session, session_id: str, new_title: str) -> None:
        """Update the display title for a chat session."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.title = new_title
            db.commit()

    @staticmethod
    def update_session_summary(db: Session, session_id: str, new_summary: str) -> None:
        """Update the compressed memory summary for a chat session."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.summary = new_summary
            db.commit()
