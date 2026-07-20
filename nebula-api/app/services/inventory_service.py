"""Authoritative inventory mutations (server is source of truth)."""

from sqlalchemy.orm import Session

from app.models.db_models import ChatSession, InventoryItem


def grant_item(db: Session, session_id: str, item_id: str, qty: int = 1) -> dict:
    """Grant items into a session bag. Returns item_id, qty, and total_qty."""

    if not session_id or not str(session_id).strip():
        raise ValueError("session_id is required")

    cleaned_item = (item_id or "").strip()
    if not cleaned_item:
        raise ValueError("item_id is required")

    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("qty must be a positive integer")

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    existing = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.session_id == session_id,
            InventoryItem.item_id == cleaned_item,
        )
        .first()
    )
    if existing:
        existing.qty += qty
    else:
        existing = InventoryItem(
            session_id=session_id,
            item_id=cleaned_item,
            qty=qty,
        )
        db.add(existing)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "item_id": cleaned_item,
        "qty": existing.qty,  # stacked total after grant (MVP)
        "total_qty": existing.qty,
        "granted_qty": qty,  # optional: how many added this call
    }
