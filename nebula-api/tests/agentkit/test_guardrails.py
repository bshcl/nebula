"""Tests for NPC reply output guardrails."""

from app.agentkit.guardrails import sanitize_npc_reply


def test_keeps_allowed_anim_and_offline() -> None:
    raw = "[[ANIM:WAVE]] 哼。 [[SYSTEM:OFFLINE]]"
    result = sanitize_npc_reply(raw)
    assert result.text == "[[ANIM:WAVE]] 哼。 [[SYSTEM:OFFLINE]]"
    assert result.violations == []
    assert result.changed is False


def test_removes_bad_anim_and_model_mood() -> None:
    raw = "[[ANIM:DANCE]] hi [[MOOD:99]]"
    result = sanitize_npc_reply(raw)
    assert "[[ANIM:DANCE]]" not in result.text
    assert "[[MOOD:" not in result.text
    assert "hi" in result.text
    assert "removed_anim:DANCE" in result.violations
    assert "removed_model_mood_tag" in result.violations


def test_keeps_valid_gift_strips_invalid() -> None:
    raw = "[[GIFT:navigator_emblem]] ok [[GIFT:bad id!]]"
    result = sanitize_npc_reply(raw)
    assert "[[GIFT:navigator_emblem]]" in result.text
    assert "[[GIFT:bad id!]]" not in result.text
    assert any(v.startswith("removed_gift:") for v in result.violations)


def test_strips_tool_xml() -> None:
    raw = "hello <tool_call>secret</tool_call> world"
    result = sanitize_npc_reply(raw)
    assert "<tool_call>" not in result.text
    assert "hello" in result.text and "world" in result.text
    assert "stripped_tool_xml" in result.violations
