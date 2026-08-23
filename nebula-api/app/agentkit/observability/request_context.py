"""Per-request observability context using contextvars."""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class RequestTrace:
    """Breadcrumbs for one chat completion turn."""

    request_id: str
    session_id: str
    mood_before: int | None = None
    mood_after: int | None = None
    route: str | None = None
    nodes: list[str] = field(default_factory=list)
    fallbacks: list[str] = field(default_factory=list)
    tool_rejections: list[str] = field(default_factory=list)
    started_monotonic: float = field(default_factory=time.monotonic)

    def mark_node(self, node_name: str) -> None:
        if node_name and node_name not in self.nodes:
            self.nodes.append(node_name)

    def mark_route(self, route: str) -> None:
        self.route = route

    def mark_fallback(self, name: str) -> None:
        if name and name not in self.fallbacks:
            self.fallbacks.append(name)

    def mark_tool_rejection(self, tool_name: str, reason: str) -> None:
        """Record a deterministic tool pre-check rejection (not a system error)."""
        if not tool_name or not reason:
            return
        entry = f"{tool_name}:{reason}"
        if entry not in self.tool_rejections:
            self.tool_rejections.append(entry)

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started_monotonic) * 1000)

    def summary_fields(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "route": self.route or "unknown",
            "nodes": ",".join(self.nodes) if self.nodes else "-",
            "fallbacks": ",".join(self.fallbacks) if self.fallbacks else "none",
            "tool_rejections": (
                ",".join(self.tool_rejections) if self.tool_rejections else "none"
            ),
            "mood_before": self.mood_before,
            "mood_after": self.mood_after,
            "duration_ms": self.elapsed_ms(),
        }


_current_trace: ContextVar[RequestTrace | None] = ContextVar("nebula_request_trace", default=None)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def start_trace(*, session_id: str, mood_before: int | None = None) -> RequestTrace:
    trace = RequestTrace(
        request_id=new_request_id(),
        session_id=session_id,
        mood_before=mood_before,
    )
    _current_trace.set(trace)
    return trace


def get_trace() -> RequestTrace | None:
    return _current_trace.get()


def clear_trace() -> None:
    _current_trace.set(None)
