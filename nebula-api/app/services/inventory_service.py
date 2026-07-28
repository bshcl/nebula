"""Authoritative inventory mutations (server is source of truth)."""

from sqlalchemy.orm import Session

from app.models.db_models import ChatSession, InventoryItem


def list_inventory(
    db: Session,
    session_id: str,
) -> list[dict]:
    """Return all stacked items for a session (read-only)."""

    if not session_id or not str(session_id).strip():
        raise ValueError("session_id is required")

    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise ValueError(f"Session not found: {session_id}")

    rows = (
        db.query(InventoryItem)
        .filter(InventoryItem.session_id == session_id)
        .order_by(InventoryItem.item_id.asc())
        .all()
    )
    return [
        {
            "item_id": row.item_id,
            "qty": row.qty,
        }
        for row in rows
    ]


def grant_item(
    db: Session,
    session_id: str,
    item_id: str,
    qty: int = 1,
    *,
    commit: bool = True,
) -> dict:
    """Grant items into a session bag. Returns item_id, qty, and total_qty.

    Set commit=False when the caller needs to commit inventory with other
    writes in one transaction (e.g. quest claim + mood update).
    """

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

    if commit:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
    else:
        # Flush so callers see persisted identity without ending the transaction.
        db.flush()

    return {
        "item_id": cleaned_item,
        "qty": existing.qty,  # stacked total after grant (MVP)
        "total_qty": existing.qty,
        "granted_qty": qty,  # how many added this call
    }
