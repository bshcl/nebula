"""Pydantic request/response models for the HTTP surface.

One module per domain: `chat.py` today, `battle.py` and friends later.
"""

from app.schemas.chat import ChatMessage, ChatRequest

__all__ = ["ChatMessage", "ChatRequest"]
