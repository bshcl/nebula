"""Tests for gameplay InteractionTools (gift grant protocol)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agentkit.observability import clear_trace, get_trace, start_trace
from app.game.inventory import service as inventory_service
from app.game.inventory.seed import seed_item_masters
from app.game.npc.tools import InteractionTools
from app.infra.models import Base, ChatSession

TEST_SESSION_ID = "tool-test-session"


@pytest.fixture()
def tool_db(monkeypatch):
    """Point InteractionTools.SessionLocal at an in-memory DB with one chat session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    seed = TestSession()
    seed.add(
        ChatSession(
            id=TEST_SESSION_ID,
            bot_name="Sakura",
            bot_personality="tsundere",
            mood=50,
        )
    )
    seed_item_masters(seed)
    seed.commit()
    seed.close()

    # Tools import SessionLocal into app.game.npc.tools — patch that binding.
    monkeypatch.setattr("app.game.npc.tools.SessionLocal", TestSession)
    return TestSession


def test_send_gift_includes_in_band_signal(tool_db) -> None:
    result = InteractionTools.send_gift.invoke(
        {"item_name": "star candy", "state": {"session_id": TEST_SESSION_ID}}
    )
    assert "[[GIFT:star_candy]]" in result

    db = tool_db()
    try:
        items = inventory_service.list_inventory(db, TEST_SESSION_ID)
    finally:
        db.close()
    assert len(items) == 1
    assert items[0]["item_id"] == "star_candy"
    assert items[0]["qty"] >= 1


def test_send_gift_rejects_empty_name(tool_db) -> None:
    result = InteractionTools.send_gift.invoke(
        {"item_name": "  ", "state": {"session_id": TEST_SESSION_ID}}
    )
    assert "[[GIFT:" not in result
    assert "failed" in result.lower()


def test_send_gift_requires_session_id() -> None:
    result = InteractionTools.send_gift.invoke({"item_name": "star_candy", "state": {}})
    assert "Missing session_id" in result
    assert "[[GIFT:" not in result


def test_send_gift_rejects_unknown_item_and_records_trace(tool_db) -> None:
    clear_trace()
    start_trace(session_id=TEST_SESSION_ID, mood_before=50)

    result = InteractionTools.send_gift.invoke(
        {
            "item_name": "legendary_blade",
            "state": {"session_id": TEST_SESSION_ID},
        }
    )
    assert "[[GIFT:" not in result
    assert "unknown_item" in result

    trace = get_trace()
    assert trace is not None
    assert "send_gift:unknown_item" in trace.tool_rejections

    db = tool_db()
    try:
        assert inventory_service.list_inventory(db, TEST_SESSION_ID) == []
    finally:
        db.close()
    clear_trace()


def test_send_gift_rejects_quest_reward_item(tool_db) -> None:
    result = InteractionTools.send_gift.invoke(
        {
            "item_name": "navigator_emblem",
            "state": {"session_id": TEST_SESSION_ID},
        }
    )
    assert "[[GIFT:" not in result
    assert "not_giftable_by_npc" in result
