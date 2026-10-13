"""LLM attempt log: last N calls, one turn's hop order, and a daily rollup."""

from pathlib import Path

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from app.agentkit.observability.llm_calls import (
    LlmCallLogger,
    calls_for_request,
    daily_llm_summary,
    recent_llm_calls,
    record_llm_call,
)
from app.agentkit.observability.request_context import clear_trace, start_trace


@pytest.fixture()
def calls_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agentkit.observability.llm_calls.llm_calls_db_path",
        lambda: tmp_path / "llm_calls.db",
    )


def test_recent_calls_keep_provider_latency_and_fallback(calls_db: None) -> None:
    record_llm_call(provider="google", model="gemini-test", latency_ms=120, fallback=False)
    record_llm_call(provider="groq", model="groq-test", latency_ms=40, fallback=True)

    rows = recent_llm_calls(limit=10)

    assert rows[0]["provider"] == "groq"
    assert rows[0]["latency_ms"] == 40
    assert rows[0]["fallback"] is True
    assert rows[1]["provider"] == "google"
    assert rows[1]["fallback"] is False


def test_one_request_shows_the_provider_hop_order(calls_db: None) -> None:
    clear_trace()
    trace = start_trace(session_id="cost-session")
    try:
        record_llm_call(provider="google", model="gemini-test", latency_ms=10, fallback=False)
        record_llm_call(provider="groq", model="groq-test", latency_ms=20, fallback=True)
        record_llm_call(provider="ollama", model="llama3.2", latency_ms=30, fallback=True)
        hops = calls_for_request(trace.request_id)
    finally:
        clear_trace()

    assert [hop["provider"] for hop in hops] == ["google", "groq", "ollama"]
    assert [hop["fallback"] for hop in hops] == [False, True, True]
    assert hops[0]["request_id"] == trace.request_id


def test_daily_summary_groups_by_day_and_provider(calls_db: None) -> None:
    record_llm_call(provider="google", model="gemini-test", latency_ms=100, fallback=False)
    record_llm_call(provider="google", model="gemini-test", latency_ms=300, fallback=True)

    summary = daily_llm_summary()

    assert len(summary) == 1
    assert summary[0]["provider"] == "google"
    assert summary[0]["calls"] == 2
    assert summary[0]["fallbacks"] == 1
    assert summary[0]["avg_latency_ms"] == 200


def test_callback_records_tokens_without_calling_a_provider(calls_db: None) -> None:
    logger = LlmCallLogger(provider="google", model="gemini-test", fallback=False)
    message = AIMessage(
        content="ok",
        usage_metadata={"input_tokens": 3, "output_tokens": 5, "total_tokens": 8},
    )
    response = LLMResult(generations=[[ChatGeneration(message=message)]])

    logger.on_chat_model_start({}, [], run_id="run-1")
    logger.on_llm_end(response, run_id="run-1")

    row = recent_llm_calls(limit=1)[0]
    assert row["provider"] == "google"
    assert row["prompt_tokens"] == 3
    assert row["completion_tokens"] == 5
    assert row["fallback"] is False
    assert row["latency_ms"] >= 0
