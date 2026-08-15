"""Authoritative quest state + claim (calls inventory.grant_item)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.game.inventory.service import grant_item
from app.game.quests.defs import QUESTS, QuestDef
from app.infra.models import ChatSession, QuestProgress

READY = "ready_to_claim"
CLAIMED = "claimed"
ACTIVE = "active"
NOT_STARTED = "not_started"


def _get_chat(db: Session, session_id: str) -> ChatSession:
    """Load chat session or raise. Return type is never None."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session not found: {session_id}")
    return session


def _get_or_create_progress(db: Session, session_id: str, quest_id: str) -> QuestProgress:
    if quest_id not in QUESTS:
        raise ValueError(f"Unknown quest: {quest_id}")

    row = (
        db.query(QuestProgress)
        .filter(QuestProgress.session_id == session_id, QuestProgress.quest_id == quest_id)
        .first()
    )
    if row:
        return row

    row = QuestProgress(session_id=session_id, quest_id=quest_id, status=NOT_STARTED)
    db.add(row)
    try:
        db.commit()
        db.refresh(row)  # ensure ORM has DB defaults / persistent state
    except Exception:
        db.rollback()
        raise
    return row


def get_quest_status(db: Session, session_id: str, quest_id: str) -> dict:
    _get_chat(db, session_id)
    row = _get_or_create_progress(db, session_id, quest_id)
    qdef = QUESTS[quest_id]
    return {
        "quest_id": quest_id,
        "title": qdef["title"],
        "status": row.status,
        "reward_item_id": qdef["reward_item_id"],
        "mood_delta": qdef["mood_delta"],
    }


def mark_quest_ready(db: Session, session_id: str, quest_id: str) -> dict:
    """MVP helper: mark quest completable (later: real completion rules)."""
    _get_chat(db, session_id)
    row = _get_or_create_progress(db, session_id, quest_id)
    if row.status == CLAIMED:
        raise ValueError(f"Quest already claimed: {quest_id}")

    row.status = READY
    row.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_quest_status(db, session_id, quest_id)


def claim_quest_reward(db: Session, session_id: str, quest_id: str) -> dict:
    """
    Agent may choose WHEN to call this; THIS function is authoritative.
    Grants item + applies mood_delta; idempotent after claimed.

    Uses grant_item(..., commit=False) so item + mood + quest status
    commit together (avoids partial success if the final commit fails).
    """
    chat = _get_chat(db, session_id)
    if quest_id not in QUESTS:
        raise ValueError(f"Unknown quest: {quest_id}")

    qdef: QuestDef = QUESTS[quest_id]
    row = _get_or_create_progress(db, session_id, quest_id)

    if row.status == CLAIMED:
        raise ValueError(f"Quest already claimed: {quest_id}")
    if row.status != READY:
        raise ValueError(
            f"Quest not ready to claim: quest_id={quest_id}, status={row.status}"
        )

    # 1) Stage inventory write without committing yet.
    grant = grant_item(
        db,
        session_id,
        qdef["reward_item_id"],
        qty=qdef["reward_qty"],
        commit=False,
    )

    # 2) Large affinity boost, clamped to project mood bounds.
    chat.mood = max(
        settings.MOOD_MIN,
        min(settings.MOOD_MAX, chat.mood + qdef["mood_delta"]),
    )

    # 3) State transition.
    row.status = CLAIMED
    row.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "quest_id": quest_id,
        "status": CLAIMED,
        "grant": grant,
        "mood": chat.mood,
        "mood_delta": qdef["mood_delta"],
    }
