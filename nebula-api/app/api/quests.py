"""Quest API — status / ready / claim for a player session."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import quest_service

router = APIRouter(prefix="/quests", tags=["quests"])


def _http_value_error(exc: ValueError) -> HTTPException:
    msg = str(exc).lower()
    code = 404 if "not found" in msg or "unknown quest" in msg else 400
    return HTTPException(status_code=code, detail=str(exc))


@router.get("/{session_id}/{quest_id}")
async def get_quest(
    session_id: str, quest_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        data = quest_service.get_quest_status(db, session_id, quest_id)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    return {"status": "success", "data": data}


@router.post("/{session_id}/{quest_id}/ready")
async def mark_ready(
    session_id: str, quest_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Mark ready_to_claim (Unity/debug: Agent tools also call the service)."""
    try:
        data = quest_service.mark_quest_ready(db, session_id, quest_id)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    return {"status": "success", "data": data}


@router.post("/{session_id}/{quest_id}/claim")
async def claim_quest(
    session_id: str, quest_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        data = quest_service.claim_quest_reward(db, session_id, quest_id)
    except ValueError as exc:
        raise _http_value_error(exc) from exc
    return {"status": "success", "data": data}
