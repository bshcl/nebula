"""Static quest definitions (config stand-in for MVP)."""

from typing import TypedDict


class QuestDef(TypedDict):
    quest_id: str
    title: str
    reward_item_id: str
    reward_qty: int
    mood_delta: int  # Large affinity boost on claim


QUESTS: dict[str, QuestDef] = {
    "quest_first_hello": {
        "quest_id": "quest_first_hello",
        "title": "Say hello to Sakura",
        "reward_item_id": "hero_badge",
        "reward_qty": 1,
        "mood_delta": 25,
    },
}

DEFAULT_QUEST_ID = "quest_first_hello"
