"""Chat API routes — streaming completions and session management."""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.chains.agents import soul_llm_cloud as llm
from app.chains.npc_graph import npc_brain
from app.core.config import get_logger
from app.core.database import get_db
from app.core.utils import ensure_string
from app.core.request_context import clear_trace, start_trace
from app.models.schemas import ChatRequest
from app.services import ai_tasks, db_service
from app.services.memory_service import MemoryService


logger = get_logger(__name__)

router = APIRouter()

# Default world-state placeholders until MCP / tools populate real values
DEFAULT_LOCATION = "Tokyo, Japan"
DEFAULT_WEATHER = "Sunny"
LANGGRAPH_REMAINING_STEPS = 15


async def graph_streamer(
    payload: ChatRequest,
    db: Session,
    background_tasks: BackgroundTasks,
) -> AsyncGenerator[str, None]:
    """Stream LangGraph node updates and persist the final assistant reply."""
    existing_session = db_service.get_chat_session_full(db, payload.session_id)
    current_mood = existing_session.mood if existing_session else 50

    trace = start_trace(session_id=payload.session_id, mood_before=current_mood)
    try:
        prior_messages = MemoryService.get_unarchived_messages(db, payload.session_id)
        if (
            prior_messages
            and prior_messages[-1].role == "user"
            and prior_messages[-1].content == payload.message
        ):
            prior_messages = prior_messages[:-1]

        history_messages: list[HumanMessage | AIMessage] = []
        for msg in prior_messages:
            if msg.role == "user":
                history_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                history_messages.append(AIMessage(content=msg.content))

        initial_state = {
            "messages": history_messages + [HumanMessage(content=payload.message)],
            "mood": current_mood,
            "summary": existing_session.summary if existing_session else "",
            "location": DEFAULT_LOCATION,
            "weather": DEFAULT_WEATHER,
            "remaining_steps": LANGGRAPH_REMAINING_STEPS,
            "session_id": payload.session_id,
        }

        full_response = ""
        final_mood = current_mood

        async for mode, chunk in npc_brain.astream(
            initial_state,
            stream_mode=["messages", "updates"],
        ):
            if mode == "updates":
                for node_name, output in chunk.items():
                    trace.mark_node(node_name)
                    logger.debug("LangGraph event: %s", {node_name: output})
                    if "mood" in output:
                        final_mood = output["mood"]
            elif mode == "messages":
                message_chunk, metadata = chunk
                node_name = metadata.get("langgraph_node", "")
                if node_name not in ("soul_node", "angry_node"):
                    continue

                token = ensure_string(message_chunk.content)
                if not token:
                    continue

                full_response += token
                yield token

        yield f"[[MOOD:{final_mood}]]"

        db_service.save_message(db, payload.session_id, "assistant", full_response)
        db_service.upsert_chat_session(
            db, payload.session_id, payload.bot_name, payload.bot_personality, final_mood
        )
        count = MemoryService.get_unarchived_messages_count(db, payload.session_id)
        if count >= 3:
            background_tasks.add_task(ai_tasks.generate_title_task, payload.session_id, llm)
        if count >= 10:
            background_tasks.add_task(ai_tasks.compress_memory_task, payload.session_id, llm)

        trace.mood_after = final_mood
        logger.info("chat_turn_complete %s", trace.summary_fields())
    finally:
        clear_trace()


@router.post("/completions")
async def chat_completions(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> StreamingResponse:
    """Main chat endpoint ―― accepts a user message and streams the NPC reply."""
    db_service.save_message(db, payload.session_id, "user", payload.message)
    return StreamingResponse(
        graph_streamer(payload, db, background_tasks),
        media_type="text/event-stream",
    )


@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return all chat session IDs."""
    ids = db_service.get_all_session_ids(db)
    return {"status": "success", "sessions": ids}


@router.get("/sessions/{session_id}")
async def get_session_data(session_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Load full session metadata and message history."""
    session = db_service.get_chat_session_full(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = [{"role": m.role, "content": m.content} for m in session.messages]
    return {
        "status": "success",
        "data": {
            "history": history,
            "mood": session.mood,
            "summary": session.summary,
            "title": session.title,
        },
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete a chat session and all associated messages."""
    if not db_service.get_chat_session_full(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    db_service.delete_chat_session(db, session_id)
    return {"status": "success", "message": "Session deleted successfully"}
