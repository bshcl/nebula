"""API tests for /api/v1/quests/{session_id}/{quest_id}."""

from app.infra.models import ChatSession

SESSION_ID = "quest-api-session"
QUEST_ID = "quest_first_hello"


def _seed_session(db_session) -> None:
    db_session.add(
        ChatSession(
            id=SESSION_ID,
            bot_name="Sakura",
            bot_personality="tsundere",
            mood=50,
        )
    )
    db_session.commit()


def test_get_quest_status(client, db_session) -> None:
    _seed_session(db_session)

    response = client.get(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["quest_id"] == QUEST_ID
    assert body["data"]["status"] == "not_started"
    assert body["data"]["reward_item_id"] == "navigator_emblem"


def test_ready_then_claim(client, db_session) -> None:
    _seed_session(db_session)

    ready = client.post(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}/ready")
    assert ready.status_code == 200
    assert ready.json()["data"]["status"] == "ready_to_claim"

    claim = client.post(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}/claim")
    assert claim.status_code == 200
    data = claim.json()["data"]
    assert data["status"] == "claimed"
    assert data["grant"]["item_id"] == "navigator_emblem"
    assert data["grant"]["granted_qty"] == 1
    assert data["mood"] == 75  # 50 + 25


def test_claim_without_ready_returns_400(client, db_session) -> None:
    _seed_session(db_session)

    response = client.post(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}/claim")
    assert response.status_code == 400
    assert "not ready" in response.json()["detail"].lower()


def test_claim_already_claimed_returns_400(client, db_session) -> None:
    _seed_session(db_session)
    client.post(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}/ready")
    client.post(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}/claim")

    again = client.post(f"/api/v1/quests/{SESSION_ID}/{QUEST_ID}/claim")
    assert again.status_code == 400
    assert "already claimed" in again.json()["detail"].lower()


def test_quest_unknown_session_returns_404(client) -> None:
    response = client.get(f"/api/v1/quests/missing-session/{QUEST_ID}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
