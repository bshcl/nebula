"""API tests for GET /api/v1/inventory/{session_id}."""

from app.models.db_models import ChatSession
from app.services.inventory_service import grant_item

SESSION_ID = "inv-api-session"


def test_get_inventory_stacked_items(client, db_session) -> None:
    db_session.add(
        ChatSession(
            id=SESSION_ID,
            bot_name="Sakura",
            bot_personality="tsundere",
            mood=50,
        )
    )
    db_session.commit()

    grant_item(db_session, SESSION_ID, "hero_badge", qty=1)
    grant_item(db_session, SESSION_ID, "hero_badge", qty=1)
    grant_item(db_session, SESSION_ID, "star_candy", qty=3)

    response = client.get(f"/api/v1/inventory/{SESSION_ID}")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["session_id"] == SESSION_ID
    # list_inventory orders by item_id ascending
    assert body["data"]["items"] == [
        {"item_id": "hero_badge", "qty": 2},
        {"item_id": "star_candy", "qty": 3},
    ]


def test_get_inventory_empty(client, db_session) -> None:
    db_session.add(
        ChatSession(
            id=SESSION_ID,
            bot_name="Sakura",
            bot_personality="tsundere",
            mood=50,
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/inventory/{SESSION_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["items"] == []


def test_get_inventory_unknown_session_returns_404(client) -> None:
    response = client.get("/api/v1/inventory/missing-session")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
