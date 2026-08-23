"""Tests for per-request observability context."""

from app.agentkit.observability import (
    clear_trace,
    get_trace,
    start_trace,
)


def test_start_trace_sets_context_and_ids() -> None:
    clear_trace()
    trace = start_trace(session_id="sess-1", mood_before=50)

    assert get_trace() is trace
    assert trace.session_id == "sess-1"
    assert trace.mood_before == 50
    assert len(trace.request_id) == 12
    clear_trace()
    assert get_trace() is None


def test_mark_helpers_and_summary() -> None:
    clear_trace()
    trace = start_trace(session_id="sess-2", mood_before=40)

    trace.mark_route("world")
    trace.mark_node("analyzer")
    trace.mark_node("analyzer")  # duplicate ignored
    trace.mark_node("soul_node")
    trace.mark_fallback("soul_local_ollama")
    trace.mark_tool_rejection("send_gift", "unknown_item")
    trace.mark_tool_rejection("send_gift", "unknown_item")  # duplicate ignored
    trace.mood_after = 45

    fields = trace.summary_fields()
    assert fields["route"] == "world"
    assert fields["nodes"] == "analyzer,soul_node"
    assert fields["fallbacks"] == "soul_local_ollama"
    assert fields["tool_rejections"] == "send_gift:unknown_item"
    assert fields["mood_before"] == 40
    assert fields["mood_after"] == 45
    assert isinstance(fields["duration_ms"], int)
    assert fields["duration_ms"] >= 0

    clear_trace()


def test_mark_tool_rejection_requires_both_parts() -> None:
    clear_trace()
    trace = start_trace(session_id="sess-3")
    trace.mark_tool_rejection("", "unknown_item")
    trace.mark_tool_rejection("send_gift", "")
    assert trace.summary_fields()["tool_rejections"] == "none"
    clear_trace()
