from langchain_core.tools import tool
from app.core import mcp_manager
from app.core.config import get_logger, settings
from app.core.rag_engine import rag_engine

logger = get_logger(__name__)


class MapTools:
    """Geographic perception tools backed by the Google Maps MCP server."""

    @staticmethod
    @tool
    async def search_nearby_places(query: str) -> str:
        """
        Search for places, restaurants, or landmarks on the map.
        Args:
            query: Search keywords, e.g. 'ramen near shibuya Station'
        """
        logger.debug("MCP map search: query=%s", query)

        if not mcp_manager.mcp_session:
            return "Error: Maps service is disconnected. Please try again later."

        try:
            result = await mcp_manager.mcp_session.call_tool(
                "maps_search_places", {"query": query}
            )
            return str(result.content)[: settings.TOOL_RESULT_MAX_CHARS]
        except Exception as e:
            logger.warning("Maps search failed: %s", e)
            return f"Maps search failed: {e}"

    @staticmethod
    @tool
    async def get_place_details(place_id: str) -> str:
        """
        Fetch detailed information for a specific place.
        Args:
            place_id: Unique place identifier from search results.
        """
        if not mcp_manager.mcp_session:
            return "Error: Maps service is not ready."

        try:
            result = await mcp_manager.mcp_session.call_tool(
                "maps_get_place_details", {"place_id": place_id}
            )
            return str(result.content)[: settings.TOOL_RESULT_MAX_CHARS]
        except Exception as e:
            logger.warning("Place details lookup failed: %s", e)
            return f"Failed to fetch place details: {e}"


class InteractionTools:
    """In-game interaction tools that modify player state or inventory."""

    @staticmethod
    @tool
    def send_gift(item_name: str) -> str:
        """
        Grant a gift item to the player inventory (gameplay side effect).
        Call only when mood >= 90 and the player explicitly asks for a gift.
        Args:
            item_name: Short snake_case or english id for the gift, e.g. star_candy.
        """
        cleaned = (item_name or "").strip().replace(" ", "_")
        if not cleaned:
            return (
                "System message: Gift failed — empty item name. "
                "Do not emit a GIFT signal. Apologize in character."
            )

        logger.info("Gift triggered: item=%s", cleaned)
        return (
            f"System message: Successfully granted {cleaned}. "
            f"In your player-facing reply, include the exact signal [[GIFT:{cleaned}]] "
            "and confirm delivery in character (tsundere tone)."
        )


class WorldKnowledgeTools:
    """RAG-backed tools for official Nebula world lore and canonical information."""

    @staticmethod
    @tool
    async def query_nebula_lore(query: str) -> str:
        """
        Query official lore about Nebula System, TYORA, Sakura, or world rules.
        Args:
            query: Topic or question to look up in the knowledge base.
        """
        retriever = rag_engine.get_retriever()
        if not retriever:
            return "Error: RAG engine is not initialized. Please try again later."

        logger.debug("RAG lore query: query=%s", query)
        docs = await retriever.ainvoke(query)

        if not docs:
            return "No matching entries in the lore codex."

        context = "\n---\n".join([doc.page_content for doc in docs])
        return f"[Nebula Lore Retrieval Result]\n{context}"


class EnvironmentTools:
    """Mock environment data for testing or fallback scenarios."""

    @staticmethod
    @tool
    def get_weather_mock(city: str) -> str:
        """
        Return mock weather data for a given city (testing/fallback only).
        Args:
            city: City name.
        """
        return (
            f"Mock weather in {city}: sunny with a temperature of 22°C."
            "Comfort index: excellent."
        )
