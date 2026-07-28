"""Tests for gameplay InteractionTools (gift grant protocol)."""

from app.chains.tools import InteractionTools


def test_send_gift_includes_in_band_signal() -> None:
    result = InteractionTools.send_gift.invoke({"item_name": "star candy"})
    assert "[[GIFT:star_candy]]" in result
    assert "Successfully granted" in result


def test_send_gift_rejects_empty_name() -> None:
    result = InteractionTools.send_gift.invoke({"item_name": "  "})
    assert "[[GIFT:" not in result
    assert "failed" in result.lower()
