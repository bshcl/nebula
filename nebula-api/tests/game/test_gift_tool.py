"""Tests for gameplay InteractionTools (gift grant protocol)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.game.inventory import service as inventory_service
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
