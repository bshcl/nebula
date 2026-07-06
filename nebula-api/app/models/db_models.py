"""SQLAlchemy ORM models for chat sessions and messages."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

DEFAULT_SESSION_TITLE = "New Session"


class ChatSession(Base):
    """Session metadata (mood, title, summary, bot profile)."""

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    bot_name = Column(String)
    bot_personality = Column(String)

    title = Column(String, default=DEFAULT_SESSION_TITLE)
    summary = Column(Text, default="")
    mood = Column(Integer, default=50)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class Message(Base):
    """A single chat message belonging to a session."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))

    role = Column(String)  # "user" or "assistant"
    content = Column(Text)

    is_archived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")
