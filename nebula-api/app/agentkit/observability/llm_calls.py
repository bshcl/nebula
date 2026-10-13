"""Append-only log of LLM attempts. No prices and no game names."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.agentkit.observability.request_context import get_trace
from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    request_id TEXT,
    session_id TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    fallback INTEGER NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    error TEXT
)
"""


def llm_calls_db_path() -> Path:
    return Path(settings.VAR_DIR) / "llm_calls.db"


def _connect() -> sqlite3.Connection:
    path = llm_calls_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(_SCHEMA)
    return connection


def record_llm_call(
    *,
    provider: str,
    model: str,
    latency_ms: int,
    fallback: bool,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    error: str | None = None,
    request_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Insert one attempt. Reads the current trace when ids are omitted."""
    trace = get_trace()
    if request_id is None and trace is not None:
        request_id = trace.request_id
    if session_id is None and trace is not None:
        session_id = trace.session_id
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO llm_calls (
                created_at, request_id, session_id, provider, model,
                latency_ms, fallback, prompt_tokens, completion_tokens, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                request_id,
                session_id,
                provider,
                model,
                latency_ms,
                1 if fallback else 0,
                prompt_tokens,
                completion_tokens,
                (error or "")[:200] or None,
            ),
        )


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["fallback"] = bool(item["fallback"])
    return item


def recent_llm_calls(limit: int = 20) -> list[dict[str, Any]]:
    """Newest attempts first. Each row has provider, latency_ms, and fallback."""
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, request_id, session_id, provider, model,
                   latency_ms, fallback, prompt_tokens, completion_tokens, error
            FROM llm_calls
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_dict(row) for row in rows]


def calls_for_request(request_id: str) -> list[dict[str, Any]]:
    """Attempts for one chat turn, oldest first, so the hop order stays visible."""
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, request_id, session_id, provider, model,
                   latency_ms, fallback, prompt_tokens, completion_tokens, error
            FROM llm_calls
            WHERE request_id = ?
            ORDER BY id ASC
            """,
            (request_id,),
        ).fetchall()
    return [_row_dict(row) for row in rows]


def daily_llm_summary() -> list[dict[str, Any]]:
    """Counts and mean latency by UTC day and provider."""
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT substr(created_at, 1, 10) AS day,
                   provider,
                   COUNT(*) AS calls,
                   SUM(fallback) AS fallbacks,
                   ROUND(AVG(latency_ms)) AS avg_latency_ms
            FROM llm_calls
            GROUP BY day, provider
            ORDER BY day DESC, provider ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _usage_tokens(response: LLMResult) -> tuple[int | None, int | None]:
    try:
        message = response.generations[0][0].message
    except (IndexError, AttributeError):
        return None, None
    usage = getattr(message, "usage_metadata", None)
    if usage is None:
        return None, None
    if isinstance(usage, dict):
        prompt = usage.get("input_tokens")
        completion = usage.get("output_tokens")
    else:
        prompt = getattr(usage, "input_tokens", None)
        completion = getattr(usage, "output_tokens", None)
    return (
        int(prompt) if isinstance(prompt, int) else None,
        int(completion) if isinstance(completion, int) else None,
    )


class LlmCallLogger(BaseCallbackHandler):
    """Record one model attempt. Attach a separate instance per provider hop."""

    def __init__(self, *, provider: str, model: str, fallback: bool) -> None:
        self.provider = provider
        self.model = model
        self.fallback = fallback
        self._started: dict[str, float] = {}

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self._started[str(run_id)] = time.perf_counter()

    def on_llm_end(self, response: LLMResult, *, run_id, **kwargs) -> None:  # type: ignore[no-untyped-def]
        prompt_tokens, completion_tokens = _usage_tokens(response)
        self._finish(run_id, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    def on_llm_error(self, error: BaseException, *, run_id, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self._finish(run_id, error=f"{type(error).__name__}: {error}")

    def _finish(
        self,
        run_id: object,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        error: str | None = None,
    ) -> None:
        started = self._started.pop(str(run_id), None)
        elapsed = time.perf_counter() - started if started is not None else 0.0
        record_llm_call(
            provider=self.provider,
            model=self.model,
            latency_ms=int(elapsed * 1000),
            fallback=self.fallback,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            error=error,
        )
