"""SQLAlchemy ORM models for chat sessions and messages."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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


class InventoryItem(Base):
    """One stacked inventory row per (session_id, item_id)."""

    __tablename__ = "inventory_items"
    # Composite unique: same item stacks via qty instead of duplicate rows.
    __table_args__ = (
        UniqueConstraint("session_id", "item_id", name="uix_session_item"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), index=True)
    item_id = Column(String, nullable=False)  # e.g. "star_candy"
    qty = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
