"""Deterministic pre-checks for quest tools (before authoritative mutations)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.game.inventory.catalog import get_item_master
from app.game.quests import service as quest_service
from app.game.quests.defs import QUESTS
from app.game.quests.service import CLAIMED, READY
from app.shared.item_types import GrantSource


def claim_reject_reason(db: Session, session_id: str, quest_id: str) -> str | None:
    """Return a stable reject reason for claim_quest_reward, or None if allowed.

    Reasons:
    - unknown_quest
    - quest_already_claimed
    - quest_not_ready
    - unknown_reward_item
    - inactive_reward_item
    - reward_not_quest_grantable
    """
    cleaned = (quest_id or "").strip()
    if not cleaned or cleaned not in QUESTS:
        return "unknown_quest"

    status_data = quest_service.get_quest_status(db, session_id, cleaned)
    status = status_data["status"]
    if status == CLAIMED:
        return "quest_already_claimed"
    if status != READY:
        return "quest_not_ready"

    reward_id = status_data["reward_item_id"]
    item = get_item_master(db, reward_id)
    if item is None:
        return "unknown_reward_item"
    if not item.is_active:
        return "inactive_reward_item"

    source = item.grant_source
    if isinstance(source, GrantSource):
        allowed = source == GrantSource.QUEST_REWARD
    else:
        allowed = str(source) == GrantSource.QUEST_REWARD.value
    if not allowed:
        return "reward_not_quest_grantable"
    return None
