"""Tests for session CRUD API routes."""


def test_get_session_returns_404_when_missing(client) -> None:
    response = client.get("/api/v1/sessions/nonexistent-session-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_list_sessions_empty(client) -> None:
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["sessions"] == []


def test_delete_session_returns_404_when_missing(client) -> None:
    response = client.delete("/api/v1/sessions/nonexistent-session-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"
