"""SQLAlchemy ORM models for chat sessions, messages, and item catalog."""

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

from app.shared.item_types import GrantSource, ItemCategory

Base = declarative_base()

DEFAULT_SESSION_TITLE = "New Session"


def _enum_values(enum_cls: type[PyEnum]) -> list[str]:
    """Persist enum .value strings (npc_gift) instead of member names (NPC_GIFT)."""
    return [member.value for member in enum_cls]


def _string_enum(enum_cls: type[PyEnum], *, name: str) -> Enum:
    """VARCHAR + CHECK constraint — portable across SQLite and MySQL."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=_enum_values,
        validate_strings=True,
    )


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


class ItemMaster(Base):
    """System catalog of items the game world recognizes.

    Player bags (inventory_items) hold ownership state; this table holds the
    rules truth: does the item exist, is it active, and which channel may grant it.
    """

    __tablename__ = "item_masters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, nullable=False, unique=True, index=True)
    display_name = Column(String, nullable=False)
    category = Column(_string_enum(ItemCategory, name="item_category"), nullable=False)
    grant_source = Column(
        _string_enum(GrantSource, name="item_grant_source"),
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    stackable = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class InventoryItem(Base):
    """One stacked inventory row per (session_id, item_id)."""

    __tablename__ = "inventory_items"
    # Composite unique: same item stacks via qty instead of duplicate rows.
    # item_id is the business key matching ItemMaster.item_id (no FK yet —
    # existing rows may predate the catalog; enforce via tool/service checks).
    __table_args__ = (UniqueConstraint("session_id", "item_id", name="uix_session_item"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), index=True)
    item_id = Column(String, nullable=False)  # e.g. "star_candy"
    qty = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuestProgress(Base):
    """Per-session quest state machine row."""

    __tablename__ = "quest_progress"
    __table_args__ = (UniqueConstraint("session_id", "quest_id", name="uix_session_quest"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), index=True)
    quest_id = Column(String, nullable=False)
    # not_started | active | ready_to_claim | claimed
    status = Column(String, nullable=False, default="not_started")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
