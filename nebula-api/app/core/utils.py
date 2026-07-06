"""Helpers for normalizing LLM output into plain strings."""

from typing import Any


def ensure_string(content: Any) -> str:
    """Coerce model output (str, list, or other) into a single string.

    Handles OpenAI/Groq string content and Gemini-style list payloads.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ).strip()

    return str(content)
