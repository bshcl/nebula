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
    history: list[ChatMessage] = Field(
        default_factory=list,
        description=(
            "Legacy client field; ignored. Conversation context is loaded from the database."
        ),
    )
    bot_name: str = Field(description="NPC display name")
    bot_personality: str = Field(description="NPC personality prompt fragment")
