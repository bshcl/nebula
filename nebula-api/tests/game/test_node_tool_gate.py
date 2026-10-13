"""Illegal tool calls must not reach inventory or quest services."""

from app.agentkit.observability import clear_trace, get_trace, start_trace
from app.game.npc.tools import InteractionTools, QuestTools, authorize_tool_call


def test_unknown_tool_is_recorded_and_does_not_call_a_service(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("service reached")

    monkeypatch.setattr("app.game.npc.tools.inventory_service.grant_item", boom)
    monkeypatch.setattr("app.game.npc.tools.quest_service.claim_quest_reward", boom)

    clear_trace()
    start_trace(session_id="allowlist-session")
    try:
        reason = authorize_tool_call("soul", "drop_table", {})
    finally:
        clear_trace()

    assert reason == "tool_not_allowed"


def test_unknown_tool_rejection_is_on_the_trace() -> None:
    clear_trace()
    trace = start_trace(session_id="allowlist-session")
    try:
        authorize_tool_call("world", "send_gift", {"item_name": "star_candy"})
        assert "send_gift:tool_not_allowed" in trace.tool_rejections
        assert get_trace() is trace
    finally:
        clear_trace()


def test_send_gift_bad_type_never_reads_the_catalog(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("service reached")

    monkeypatch.setattr("app.game.npc.tools.get_item_master", boom)
    monkeypatch.setattr("app.game.npc.tools.inventory_service.grant_item", boom)

    clear_trace()
    start_trace(session_id="allowlist-session")
    try:
        result = InteractionTools.send_gift.func(item_name=5, state={"session_id": "s"})
    finally:
        clear_trace()

    assert "bad_argument_type" in result
    assert "[[GIFT:" not in result


def test_claim_bad_type_never_reaches_quest_service(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("service reached")

    monkeypatch.setattr("app.game.npc.tools.claim_reject_reason", boom)
    monkeypatch.setattr("app.game.npc.tools.quest_service.claim_quest_reward", boom)

    result = QuestTools.claim_quest_reward.func(quest_id=1, state={"session_id": "s"})
    assert "bad_argument_type" in result
