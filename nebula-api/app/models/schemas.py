"""Pydantic request/response schemas for the chat API."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in conversation history."""

    role: str = Field(description='Sender role: "user" or "assistant"')
    content: str = Field(description="Message text content")


class ChatRequest(BaseModel):
    """Incoming chat completion request from the Unity client."""

    session_id: str = Field(description="Unique session identifier")
    message: str = Field(description="Latest user message")
    history: list[ChatMessage] = Field(description="Prior messages for context")
    bot_name: str = Field(description="NPC display name")
    bot_personality: str = Field(description="NPC personality prompt fragment")


class ChatResponse(BaseModel):
    """Non-streaming chat response envelope (legacy / optional)."""

    status: str = Field(description='Outcome status, e.g. "success" or "error"')
    reply: str = Field(description="Assistant reply text")
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation id for multi-turn clients",
    )
