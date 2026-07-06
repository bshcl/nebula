from app.models.base_state import BaseState


class NPCState(BaseState):
    """Soul agent state: mood and long-term memory."""

    mood: int
    summary: str
