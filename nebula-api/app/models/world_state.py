from app.models.base_state import BaseState


class WorldState(BaseState):
    """World observer state: location and weather cache."""

    location: str
    weather: str
