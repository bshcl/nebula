"""Tests for health endpoint."""

from main import health_check


def test_health_returns_ok() -> None:
    assert health_check() == {"status": "ok"}
