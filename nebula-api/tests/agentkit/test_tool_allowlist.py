"""Allowlist decisions, with no model and no game services."""

from app.agentkit.guardrails import ArgumentSpec, check_tool_call


SOUL = {
    "send_gift": (ArgumentSpec("item_name"),),
    "get_quest_status": (ArgumentSpec("quest_id", required=False),),
}


def test_unknown_tool_is_rejected() -> None:
    assert check_tool_call(SOUL, "drop_table", {}) == "tool_not_allowed"


def test_missing_required_argument() -> None:
    assert check_tool_call(SOUL, "send_gift", {}) == "missing_argument"


def test_unexpected_argument() -> None:
    reason = check_tool_call(SOUL, "send_gift", {"item_name": "star_candy", "qty": "9"})
    assert reason == "unexpected_argument"


def test_non_string_argument() -> None:
    assert check_tool_call(SOUL, "send_gift", {"item_name": 3}) == "bad_argument_type"


def test_optional_argument_may_be_omitted() -> None:
    assert check_tool_call(SOUL, "get_quest_status", {}) is None


def test_legal_call_passes() -> None:
    assert check_tool_call(SOUL, "send_gift", {"item_name": "star_candy"}) is None
