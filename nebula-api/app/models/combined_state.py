from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CombinedState(TypedDict):
    """Global LangGraph state contract for the Nebula NPC workflow."""

    messages: Annotated[list, add_messages]
    mood: int
    summary: str
    location: str
    weather: str
    remaining_steps: int
