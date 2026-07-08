from pydantic_settings import BaseSettings
from pydantic import Field


class AISettings(BaseSettings):
    """Configuration for LLM providers and Agent behavior thresholds."""

    # Required secret - loaded from .env file when variables names match field names.
    GOOGLE_API_KEY: str = Field(default=...)
    GROQ_API_KEY: str = Field(default=...)
    GOOGLE_MAPS_API_KEY: str = Field(default=...)

    # Cloud and local model identifiers
    PRIMARY_MODEL: str = "gemini-3.5-flash"
    BACKUP_MODEL: str = "gemini-3.1-flash-lite"
    LOCAL_MODEL: str = "llama3.2"
    GROQ_FALLBACK_MODEL: str = "llama-3.1-70b-versatile"

    # NPC mood boundaries used by the LangGraph workflow
    ANGRY_THRESHOLD: int = 20
    MOOD_MIN: int = 0
    MOOD_MAX: int = 100

    # Maximum characters returned by MCP / RAG tools to the LLM
    TOOL_RESULT_MAX_CHARS: int = 2000

    # RAG model identifier
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Skip world node if true
    SKIP_WORLD_NODE: bool = False
