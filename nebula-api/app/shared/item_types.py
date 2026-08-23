"""Stable item-catalog enums shared by ORM models and game services.

Kept in shared (not game/inventory) so infra/models can import them without
pointing dependencies back up into the game layer.
"""

from __future__ import annotations

from enum import Enum


class ItemCategory(str, Enum):
    """What the item is."""

    GIFT = "gift"
    QUEST = "quest"
    CONSUMABLE = "consumable"
    EQUIPMENT = "equipment"
    BATTLE = "battle"


class GrantSource(str, Enum):
    """Primary channel that may grant this item into a player bag."""

    NPC_GIFT = "npc_gift"
    QUEST_REWARD = "quest_reward"
    DROP = "drop"
    SHOP = "shop"
    GM_ONLY = "gm_only"
