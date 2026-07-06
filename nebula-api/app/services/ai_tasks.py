"""Background tasks for session title generation and memory compression."""

from langchain_core.runnables import Runnable

from app.core.config import get_logger
from app.core.database import SessionLocal
from app.core.utils import ensure_string
from app.models.db_models import ChatSession, Message
from app.services.memory_service import MemoryService
from app.models.db_models import DEFAULT_SESSION_TITLE

logger = get_logger(__name__)

MIN_MESSAGES_FOR_TITLE = 3
MIN_MESSAGES_FOR_COMPRESSION = 10

TITLE_PROMPT = """\
Based on the conversation below, generate a short title (max 8 words, no punctuation).
Output only the title text.

{context}"""

MEMORY_PROMPT = """\
You are a memory specialist. Merge the old memory with the new conversation.
Keep the summary within 50 words.

Old memory: {old_summary}

New conversation:
{formatted_text}

Output only the merged summary."""


async def generate_title_task(session_id: str, model: Runnable) -> None:
    """Background task: generate a semantic title for a chat session."""
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or (session.title and session.title != DEFAULT_SESSION_TITLE):
            return

        messages = MemoryService.get_unarchived_messages(db, session_id)
        logger.debug(
            "Title task messages for session %s: %d", session_id, len(messages)
        )
        if len(messages) < MIN_MESSAGES_FOR_TITLE:
            return

        context = "\n".join(f"{m.role}: {m.content}" for m in messages)
        prompt = TITLE_PROMPT.format(context=context)
        response = await model.ainvoke(prompt)

        new_title = ensure_string(response.content)
        new_title = new_title.replace("Title:", "").replace('"', "").strip()

        MemoryService.update_session_title(db, session_id, new_title)
        logger.info("Session %s title updated to: %s", session_id, new_title)

    except Exception:
        logger.exception("Title generation failed for session %s", session_id)
    finally:
        db.close()


async def compress_memory_task(session_id: str, model: Runnable) -> None:
    """Background task: compress unarchived messages into a session summary."""
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return

        new_messages = MemoryService.get_unarchived_messages(db, session_id)
        if len(new_messages) < MIN_MESSAGES_FOR_COMPRESSION:
            return

        formatted_text = "\n".join(f"{m.role}: {m.content}" for m in new_messages)
        old_summary = session.summary or "No prior memory."

        prompt = MEMORY_PROMPT.format(
            old_summary=old_summary,
            formatted_text=formatted_text,
        )
        response = await model.ainvoke(prompt)
        new_summary = ensure_string(response.content).strip()

        session.summary = new_summary
        db.query(Message).filter(
            Message.session_id == session_id,
            Message.is_archived.is_(False),
        ).update({"is_archived": True})

        db.commit()
        logger.info("Session %s memory compression completed", session_id)

    except Exception:
        logger.exception("Memory compression failed for session %s", session_id)
        db.rollback()
    finally:
        db.close()
