"""Tests for Soul quest tools (InjectedState + SessionLocal)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.game.npc.tools import QuestTools
from app.game.quests.defs import DEFAULT_QUEST_ID
from app.infra.models import Base, ChatSession

TEST_SESSION_ID = "tool-test-session"


@pytest.fixture()
def tool_db(monkeypatch):
    """Point QuestTools.SessionLocal at an in-memory DB with one chat session."""
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

    # Tools import SessionLocal into app.game.npc.tools - patch that binding.
    monkeypatch.setattr("app.game.npc.tools.SessionLocal", TestSession)
    return TestSession


def _state() -> dict:
    return {"session_id": TEST_SESSION_ID}


def test_get_quest_status_requires_session_id():
    result = QuestTools.get_quest_status.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": {}}
    )
    assert "Missing session_id" in result


def test_get_quest_status_returns_json(tool_db):
    result = QuestTools.get_quest_status.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "System message:" in result
    assert DEFAULT_QUEST_ID in result
    assert "not_started" in result or "ready_to_claim" in result or "claimed" in result


def test_mark_and_claim_via_tools(tool_db):
    marked = QuestTools.mark_quest_ready.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "Quest marked ready" in marked
    assert "ready_to_claim" in marked

    claimed = QuestTools.claim_quest_reward.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "Claim success" in claimed
    assert "[[GIFT:navigator_emblem]]" in claimed
    assert "navigator_emblem" in claimed


def test_claim_via_tool_is_idempotent(tool_db):
    QuestTools.mark_quest_ready.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    QuestTools.claim_quest_reward.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    second = QuestTools.claim_quest_reward.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "already claimed" in second.lower()


def test_claim_via_tool_rejects_if_not_ready(tool_db):
    result = QuestTools.claim_quest_reward.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "not ready" in result.lower()
