"""Tests for app.core.utils."""

from app.core.utils import ensure_string


def test_ensure_string_returns_str_unchanged() -> None:
    assert ensure_string("hello") == "hello"


def test_ensure_string_joins_gemini_style_list() -> None:
    content = [{"text": "hello"}, {"text": " world"}]
    assert ensure_string(content) == "hello world"


def test_ensure_string_coerces_non_str_non_list() -> None:
    assert ensure_string(42) == "42"
