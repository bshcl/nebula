"""Tests for Soul quest tools (InjectedState + SessionLocal)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agentkit.observability import clear_trace, get_trace, start_trace
from app.game.inventory.seed import seed_item_masters
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
    seed_item_masters(seed)
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
    assert "quest_already_claimed" in second
    assert "[[GIFT:" not in second


def test_claim_via_tool_rejects_if_not_ready(tool_db):
    result = QuestTools.claim_quest_reward.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "quest_not_ready" in result
    assert "[[GIFT:" not in result


def test_claim_rejects_unknown_quest(tool_db):
    result = QuestTools.claim_quest_reward.invoke(
        {"quest_id": "quest_does_not_exist", "state": _state()}
    )
    assert "unknown_quest" in result
    assert "[[GIFT:" not in result


def test_claim_not_ready_records_trace(tool_db):
    clear_trace()
    start_trace(session_id=TEST_SESSION_ID, mood_before=50)

    result = QuestTools.claim_quest_reward.invoke(
        {"quest_id": DEFAULT_QUEST_ID, "state": _state()}
    )
    assert "quest_not_ready" in result

    trace = get_trace()
    assert trace is not None
    assert "claim_quest_reward:quest_not_ready" in trace.tool_rejections
    clear_trace()
