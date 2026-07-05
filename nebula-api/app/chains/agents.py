from typing import Any

from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from app.chains.tools import (
    EnvironmentTools,
    InteractionTools,
    MapTools,
    WorldKnowledgeTools,
)
from app.core.config import get_logger, settings
from app.core.prompts import SOUL_MANAGER_PROMPT, WORLD_OBSERVER_PROMPT
from app.models.combined_state import CombinedState

logger = get_logger(__name__)


def create_cloud_llm(model_name: str, temperature: float = 0.0) -> Runnable:
    """Build a cloud LLM with automatic Groq fallback on primary failure."""
    primary = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
    )
    backup = ChatGroq(
        model=settings.GROQ_FALLBACK_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=temperature,
    )
    return primary.with_fallbacks([backup])


world_llm_cloud = create_cloud_llm(settings.PRIMARY_MODEL, temperature=0.0)
soul_llm_cloud = create_cloud_llm(settings.BACKUP_MODEL, temperature=0.7)

# Local fallback via Ollama — no tools bound, for maximum stability
local_llm = ChatOllama(model=settings.LOCAL_MODEL, temperature=0.0)

SOUL_TOOLS = [InteractionTools.send_gift]
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
