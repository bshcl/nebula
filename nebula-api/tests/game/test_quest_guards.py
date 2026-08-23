"""Tests for quest claim pre-checks."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.game.inventory.seed import seed_item_masters
from app.game.quests.guards import claim_reject_reason
from app.game.quests.service import mark_quest_ready
from app.infra.models import Base, ChatSession

TEST_SESSION_ID = "guard-test-session"


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    session.add(
        ChatSession(
            id=TEST_SESSION_ID,
            bot_name="Sakura",
            bot_personality="tsundere",
            mood=50,
        )
    )
    seed_item_masters(session)
    session.commit()
    try:
        yield session
    finally:
        session.close()


def test_claim_reject_unknown_quest(db) -> None:
    assert claim_reject_reason(db, TEST_SESSION_ID, "nope") == "unknown_quest"


def test_claim_reject_not_ready(db) -> None:
    assert (
        claim_reject_reason(db, TEST_SESSION_ID, "quest_first_hello") == "quest_not_ready"
    )


def test_claim_reject_none_when_ready(db) -> None:
    mark_quest_ready(db, TEST_SESSION_ID, "quest_first_hello")
    assert claim_reject_reason(db, TEST_SESSION_ID, "quest_first_hello") is None
