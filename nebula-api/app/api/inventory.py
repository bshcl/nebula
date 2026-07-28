"""Inventory API — authoritative bag reads for a player session."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/{session_id}")
async def get_inventory(session_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    List stacked inventory items for a session.

    Path: GET /api/v1/inventory/{session_id}
    """
    try:
        items = inventory_service.list_inventory(db, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "status": "success",
        "data": {
            "session_id": session_id,
            "items": items,
        },
    }
