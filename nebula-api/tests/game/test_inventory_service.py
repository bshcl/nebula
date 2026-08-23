"""Tests for authoritative inventory grant."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.game.inventory.service import grant_item
from app.infra.models import Base, ChatSession

# Must match the ChatSession.id created in the db fixture below.
TEST_SESSION_ID = "test-session"


@pytest.fixture()
def db():
    """In-memory SQLite session with one chat session ready for grants."""
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


def test_grant_item_stacks_qty(db):
    """Granting the same item twice should increase qty (stacking)."""
    first = grant_item(db, TEST_SESSION_ID, "star_candy", qty=1)
    assert first["item_id"] == "star_candy"
    assert first["qty"] == 1

    second = grant_item(db, TEST_SESSION_ID, "star_candy", qty=1)
    assert second["qty"] == 2
    assert second["total_qty"] == 2


def test_grant_two_different_items(db):
    """Different item_ids should create two independent inventory rows."""
    a = grant_item(db, TEST_SESSION_ID, "star_candy", qty=1)
    b = grant_item(db, TEST_SESSION_ID, "navigator_emblem", qty=1)
    assert a["qty"] == 1
    assert b["qty"] == 1
    assert a["item_id"] != b["item_id"]


def test_grant_rejects_bad_qty(db):
    with pytest.raises(ValueError, match="qty"):
        grant_item(db, TEST_SESSION_ID, "star_candy", qty=0)


def test_grant_rejects_empty_item(db):
    with pytest.raises(ValueError, match="item_id"):
        grant_item(db, TEST_SESSION_ID, "  ", qty=1)
