"""Tests for NPC reply output guardrails."""

from app.agentkit.guardrails import OfflineTagFilter, sanitize_npc_reply


def test_keeps_allowed_anim_and_offline_on_a_real_fallback() -> None:
    raw = "[[ANIM:WAVE]] 哼。 [[SYSTEM:OFFLINE]]"
    result = sanitize_npc_reply(raw, allow_offline=True)
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


def test_strips_gift_id_missing_from_catalog() -> None:
    raw = "[[GIFT:star_candy]] take [[GIFT:legendary_blade]]"
    result = sanitize_npc_reply(
        raw,
        allowed_gift_ids={"star_candy", "navigator_emblem"},
    )
    assert "[[GIFT:star_candy]]" in result.text
    assert "legendary_blade" not in result.text
    assert "removed_unknown_gift:legendary_blade" in result.violations


def test_strips_inventory_count_claim() -> None:
    raw = "Hmph. You have 3 star_candy in your bag. Come in."
    result = sanitize_npc_reply(raw)
    assert "3" not in result.text
    assert "Come in." in result.text
    assert "removed_inventory_claim" in result.violations


def test_plain_number_is_not_an_inventory_claim() -> None:
    raw = "I have been waiting 3 days."
    result = sanitize_npc_reply(raw)
    assert result.violations == []
    assert result.text == raw


def test_strips_offline_tag_unless_the_turn_really_fell_back() -> None:
    raw = "Hello. [[SYSTEM:OFFLINE]]"
    result = sanitize_npc_reply(raw)
    assert "[[SYSTEM:OFFLINE]]" not in result.text
    assert result.text == "Hello."
    assert "removed_offline_tag" in result.violations


def test_offline_filter_holds_a_tag_split_across_tokens() -> None:
    stream = OfflineTagFilter()
    assert stream.feed("Hello [[SYS") == "Hello "
    assert stream.feed("TEM:OFFLINE]] there") == " there"
    assert stream.finish() == ""
