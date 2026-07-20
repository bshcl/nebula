"""Tests for authoritative quest claim loop."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.db_models import Base, ChatSession
from app.services.quest_service import claim_quest_reward, mark_quest_ready

TEST_SESSION_ID = "test-session"
TEST_QUEST_ID = "quest_first_hello"


@pytest.fixture()
def db():
    """In-memory SQLite with one chat session for quest claims."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(
        ChatSession(
            id=TEST_SESSION_ID,
            bot_name="Sakura",
            bot_personality="tsundere",
            mood=50,
        )
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()


def test_claim_grants_item_and_mood(db):
    mark_quest_ready(db, TEST_SESSION_ID, TEST_QUEST_ID)
    result = claim_quest_reward(db, TEST_SESSION_ID, TEST_QUEST_ID)

    assert result["status"] == "claimed"
    assert result["grant"]["item_id"] == "hero_badge"
    assert result["grant"]["granted_qty"] == 1
    assert result["mood"] == 75  # 50 + 25


def test_claim_is_idempotent(db):
    mark_quest_ready(db, TEST_SESSION_ID, TEST_QUEST_ID)
    claim_quest_reward(db, TEST_SESSION_ID, TEST_QUEST_ID)
    with pytest.raises(ValueError, match="already claimed"):
        claim_quest_reward(db, TEST_SESSION_ID, TEST_QUEST_ID)


def test_claim_rejects_if_not_ready(db):
    with pytest.raises(ValueError, match="not ready"):
        claim_quest_reward(db, TEST_SESSION_ID, TEST_QUEST_ID)
