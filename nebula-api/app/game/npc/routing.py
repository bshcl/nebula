"""Pure mood/route decisions for the NPC graph (no LLM / tool imports)."""

from __future__ import annotations

from typing import Literal

from app.agentkit.observability import get_trace
from app.config import get_logger, settings
from app.game.npc.state import CombinedState

logger = get_logger(__name__)


def mood_router(state: CombinedState) -> Literal["angry", "normal"]:
    """Route to angry or normal path based on current mood."""
    if state["mood"] < settings.ANGRY_THRESHOLD:
        return "angry"
    return "normal"


def post_analyzer_router(state: CombinedState) -> Literal["angry", "world", "soul"]:
    """Route to angry, world, or soul path based on mood and SKIP_WORLD_NODE."""
    route = mood_router(state)
    if route == "angry":
        trace = get_trace()
        if trace:
            trace.mark_route("angry")
        return "angry"
    if settings.SKIP_WORLD_NODE:
        logger.info("Demo mode: skipping world_node")
        trace = get_trace()
        if trace:
            trace.mark_route("soul")
        return "soul"
    trace = get_trace()
    if trace:
        trace.mark_route("world")
    return "world"
