"""Read helpers for item_masters (rules truth, not player bag state)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.infra.models import ItemMaster
from app.shared.item_types import GrantSource


def get_item_master(db: Session, item_id: str) -> ItemMaster | None:
    """Return the catalog row for item_id, or None if it does not exist."""
    cleaned = (item_id or "").strip()
    if not cleaned:
        return None
    return db.query(ItemMaster).filter(ItemMaster.item_id == cleaned).first()


def npc_gift_reject_reason(item: ItemMaster | None) -> str | None:
    """Return a stable reject reason for send_gift, or None if grant is allowed.

    Reasons (for trace / system messages):
    - unknown_item
    - inactive_item
    - not_giftable_by_npc
    """
    if item is None:
        return "unknown_item"
    if not item.is_active:
        return "inactive_item"
    source = item.grant_source
    if isinstance(source, GrantSource):
        allowed = source == GrantSource.NPC_GIFT
    else:
        allowed = str(source) == GrantSource.NPC_GIFT.value
    if not allowed:
        return "not_giftable_by_npc"
    return None
