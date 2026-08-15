"""Nebula's NPC agents — which model, which tools, which prompt.

Model construction and fallback chains live in `app.agentkit.llm`.
"""

from typing import Any

from langgraph.prebuilt import create_react_agent

from app.agentkit.llm import create_cloud_llm, create_local_llm
from app.config import get_logger, settings
from app.game.npc.prompts import SOUL_MANAGER_PROMPT, WORLD_OBSERVER_PROMPT
from app.game.npc.state import CombinedState
from app.game.npc.tools import (
    EnvironmentTools,
    InteractionTools,
    MapTools,
    QuestTools,
    WorldKnowledgeTools,
)

logger = get_logger(__name__)

world_llm_cloud = create_cloud_llm(settings.PRIMARY_MODEL, temperature=0.0)
soul_llm_cloud = create_cloud_llm(settings.BACKUP_MODEL, temperature=0.7)

# Local fallback via Ollama — no tools bound, for maximum stability
local_llm = create_local_llm(settings.LOCAL_MODEL, temperature=0.0)

SOUL_TOOLS = [
    InteractionTools.send_gift,  # bonus path later; keep for now
    QuestTools.get_quest_status,
    QuestTools.mark_quest_ready,
    QuestTools.claim_quest_reward,
]
WORLD_TOOLS = [
    MapTools.search_nearby_places,
    MapTools.get_place_details,
    EnvironmentTools.get_weather_mock,
    WorldKnowledgeTools.query_nebula_lore,
]

soul_agent = create_react_agent(
    model=soul_llm_cloud,
    tools=SOUL_TOOLS,
    state_schema=CombinedState,
    name="soul_manager_cloud",
    prompt=SOUL_MANAGER_PROMPT,
)

world_agent_cloud: Any | None = None


def initialize_world_agent() -> None:
    """Lazily create the cloud World Observer agent (called from FastAPI lifespan)."""
    global world_agent_cloud
    world_agent_cloud = create_react_agent(
        model=world_llm_cloud,
        tools=WORLD_TOOLS,
        state_schema=CombinedState,
        name="world_observer_cloud",
        prompt=WORLD_OBSERVER_PROMPT,
    )
    logger.info("Cloud World Agent is ready")
