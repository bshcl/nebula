"""LLM construction with automatic provider fallback.

Game-agnostic: callers pass model names, this module owns the fallback chain.
"""

from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from app.agentkit.observability.llm_calls import LlmCallLogger
from app.config import settings


def create_cloud_llm(model_name: str, temperature: float = 0.0) -> Runnable:
    """Build a cloud LLM with automatic Groq fallback on primary failure."""
    primary = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        # Retry briefly on transient 503; then fall through to Groq.
        max_retries=2,
        callbacks=[
            LlmCallLogger(provider="google", model=model_name, fallback=False),
        ],
    )
    backup = ChatGroq(
        model=settings.GROQ_FALLBACK_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        max_retries=1,
        callbacks=[
            LlmCallLogger(
                provider="groq",
                model=settings.GROQ_FALLBACK_MODEL,
                fallback=True,
            ),
        ],
    )
    return primary.with_fallbacks([backup])


def create_local_llm(model_name: str, temperature: float = 0.0) -> ChatOllama:
    """Build a local Ollama model — no tools bound, for maximum stability."""
    return ChatOllama(
        model=model_name,
        temperature=temperature,
        callbacks=[
            LlmCallLogger(provider="ollama", model=model_name, fallback=True),
        ],
    )
