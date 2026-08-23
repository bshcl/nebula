"""Idempotent seed rows for item_masters.

Authored catalog content lives here (not in infra). init_db calls
seed_item_masters() so a fresh SQLite file already has the MVP gifts/rewards.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.infra.models import ItemMaster
from app.shared.item_types import GrantSource, ItemCategory

# Minimal catalog for the current gameplay loop.
# Add rows here when a new item_id appears in quests, gifts, or battle.
DEFAULT_ITEMS: list[dict[str, object]] = [
    {
        "item_id": "star_candy",
        "display_name": "Star Candy",
        "category": ItemCategory.GIFT,
        "grant_source": GrantSource.NPC_GIFT,
        "is_active": True,
        "stackable": True,
    },
    {
        "item_id": "navigator_emblem",
        "display_name": "Navigator Emblem",
        "category": ItemCategory.QUEST,
        "grant_source": GrantSource.QUEST_REWARD,
        "is_active": True,
        "stackable": True,
    },
]


def seed_item_masters(db: Session) -> int:
    """Insert missing DEFAULT_ITEMS rows. Returns how many rows were added."""
    added = 0
    for row in DEFAULT_ITEMS:
        item_id = str(row["item_id"])
        exists = db.query(ItemMaster).filter(ItemMaster.item_id == item_id).first()
        if exists:
            continue
        db.add(ItemMaster(**row))
        added += 1
    if added:
        db.commit()
    return added
