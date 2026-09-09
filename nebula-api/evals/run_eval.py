"""Run golden eval cases (route / reject / quest / fallback) without live LLM calls."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

# Allow `python evals/run_eval.py` from nebula-api root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep harness output readable (settings import configures app logging).
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.agentkit.guardrails.output_filter import sanitize_npc_reply  # noqa: E402
from app.agentkit.observability import clear_trace, get_trace, start_trace  # noqa: E402
from app.config import settings  # noqa: E402
from app.game.inventory.catalog import (  # noqa: E402
    get_item_master,
    npc_gift_reject_reason,
)
from app.game.inventory.seed import seed_item_masters  # noqa: E402
from app.game.inventory.service import list_inventory  # noqa: E402
from app.game.npc.routing import post_analyzer_router  # noqa: E402
from app.game.quests.guards import claim_reject_reason  # noqa: E402
# MODIFIED: mark/claim live in service (authoritative ledger), not guards.
from app.game.quests.service import (  # noqa: E402
    claim_quest_reward,
    get_quest_status,
    mark_quest_ready,
)
from app.infra.models import Base, ChatSession  # noqa: E402
from evals.scoring import load_cases, score_reason, score_route  # noqa: E402

# Runner-owned temp session for claim cases (YAML stays rule-only).
_EVAL_SESSION_ID = "eval-claim-session"


def _make_eval_db() -> Session:
    """In-memory SQLite + item_masters seed. Does not touch var/nebula.db."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    seed_item_masters(session)
    session.commit()
    return session


def _result_shell(case: dict[str, Any], scored: dict[str, Any]) -> dict[str, Any]:
    """Shared return shape so main() can print every mode the same way."""
    return {
        "id": case.get("id", "<unknown>"),
        "description": case.get("description", ""),
        **scored,
    }


def run_route_case(case: dict[str, Any]) -> dict[str, Any]:
    """Execute one route_only case and return a scored result."""
    case_id = case.get("id", "<unknown>")
    case_input = case.get("input") or {}
    expected = (case.get("expect") or {}).get("route")
    if expected is None:
        raise ValueError(f"case {case_id} missing expect.route")
    if "mood" not in case_input:
        raise ValueError(f"case {case_id} missing input.mood")

    mood = int(case_input["mood"])
    skip_world = bool(case_input.get("skip_world_node", False))

    previous_skip = settings.SKIP_WORLD_NODE
    settings.SKIP_WORLD_NODE = skip_world
    try:
        actual = post_analyzer_router({"mood": mood})  # type: ignore[arg-type]
    finally:
        settings.SKIP_WORLD_NODE = previous_skip

    return _result_shell(case, score_route(expected=expected, actual=actual))


def run_tool_reject_case(case: dict[str, Any]) -> dict[str, Any]:
    """Deterministic tool pre-check eval (no LangChain invoke, no LLM).

    IN:    case["input"].tool + tool-specific fields; case["expect"].reason
    STEPS: 1) open temp db  2) branch on tool  3) call guard helpers  4) score
    OUT:   {id, description, passed, expected, actual, reason}
    DON'T: mutate var/nebula.db; invoke send_gift/claim tools; call an LLM
    """
    case_id = case.get("id", "<unknown>")
    case_input = case.get("input") or {}
    expected = (case.get("expect") or {}).get("reason")
    if expected is None:
        raise ValueError(f"case {case_id} missing expect.reason")

    tool = case_input.get("tool")
    db = _make_eval_db()
    try:
        if tool == "send_gift":
            item_name = case_input.get("item_name") or ""
            item = get_item_master(db, item_name)
            actual = npc_gift_reject_reason(item)
        elif tool == "claim_quest_reward":
            quest_id = case_input.get("quest_id") or ""
            db.add(
                ChatSession(
                    id=_EVAL_SESSION_ID,
                    bot_name="Sakura",
                    bot_personality="tsundere",
                    mood=50,
                )
            )
            db.commit()
            # Not marked ready on purpose → expect quest_not_ready
            actual = claim_reject_reason(db, _EVAL_SESSION_ID, quest_id)
        else:
            raise ValueError(f"case {case_id} unsupported tool={tool!r}")
    finally:
        db.close()

    return _result_shell(case, score_reason(expected=expected, actual=actual))


def run_quest_flow_case(case: dict[str, Any]) -> dict[str, Any]:
    """Quest service flow eval — ledger mutations, not tool pre-guards.

    IN:    case["input"].setup + quest_id; case["expect"].outcome (+ status/inventory_*)
    STEPS: 1) temp db + ChatSession  2) setup board  3) claim_quest_reward once
           4) read status/inventory  5) score vs expect
    OUT:   {id, description, passed, expected, actual, reason}
    DON'T: call LLM; call claim_reject_reason; touch var/nebula.db
    """
    case_id = case.get("id", "<unknown>")
    case_input = case.get("input") or {}
    expect = case.get("expect") or {}
    setup = case_input.get("setup")
    quest_id = case_input.get("quest_id") or ""

    # MODIFIED: validate required fields early (clearer than a later KeyError).
    if not setup:
        raise ValueError(f"case {case_id} missing input.setup")
    if not quest_id:
        raise ValueError(f"case {case_id} missing input.quest_id")
    if "outcome" not in expect:
        raise ValueError(f"case {case_id} missing expect.outcome")

    db = _make_eval_db()
    try:
        # MODIFIED: every path needs a ChatSession before service calls.
        db.add(
            ChatSession(
                id=_EVAL_SESSION_ID,
                bot_name="Sakura",
                bot_personality="tsundere",
                mood=50,
            )
        )
        db.commit()

        # --- setup = arrange the board BEFORE the exam question ---
        # MODIFIED: do not call claim_reject_reason here (that belongs to reject.yaml).
        if setup == "not_ready":
            pass  # session only; quest stays not ready
        elif setup == "ready":
            mark_quest_ready(db, _EVAL_SESSION_ID, quest_id)
        elif setup == "already_claimed":
            # First successful claim is fixture, not the assertion under test.
            mark_quest_ready(db, _EVAL_SESSION_ID, quest_id)
            claim_quest_reward(db, _EVAL_SESSION_ID, quest_id)
        else:
            raise ValueError(f"case {case_id} unsupported setup={setup!r}")

        # --- exam: one authoritative claim via service ---
        # MODIFIED: expected business failures become outcome="error", not harness crash.
        try:
            claim_quest_reward(db, _EVAL_SESSION_ID, quest_id)
            outcome_actual = "success"
        except ValueError:
            outcome_actual = "error"

        status_actual = get_quest_status(db, _EVAL_SESSION_ID, quest_id)["status"]
        items = list_inventory(db, _EVAL_SESSION_ID)
        qty_by_id = {row["item_id"]: row["qty"] for row in items}
    finally:
        db.close()

    # MODIFIED: multi-field expect — gather mismatches instead of score_reason(str).
    mismatches: list[str] = []
    if outcome_actual != expect["outcome"]:
        mismatches.append(
            f"outcome expected={expect['outcome']!r} actual={outcome_actual!r}"
        )

    if "status" in expect and status_actual != expect["status"]:
        mismatches.append(
            f"status expected={expect['status']!r} actual={status_actual!r}"
        )

    if expect.get("inventory_empty"):
        if items:
            mismatches.append(f"inventory_empty expected but got {items!r}")

    if "inventory_has" in expect:
        item_id = expect["inventory_has"]
        if item_id not in qty_by_id:
            mismatches.append(f"inventory missing item_id={item_id!r} got={items!r}")

    if "inventory_qty" in expect:
        # Default item for qty check: inventory_has, else the only stacked row.
        item_id = expect.get("inventory_has")
        if item_id is None and len(qty_by_id) == 1:
            item_id = next(iter(qty_by_id))
        actual_qty = qty_by_id.get(item_id or "", 0)
        if actual_qty != expect["inventory_qty"]:
            mismatches.append(
                f"inventory_qty expected={expect['inventory_qty']!r} "
                f"actual={actual_qty!r} item_id={item_id!r}"
            )

    passed = not mismatches
    actual_summary = {
        "outcome": outcome_actual,
        "status": status_actual,
        "inventory": items,
    }
    return _result_shell(
        case,
        {
            "passed": passed,
            "expected": expect,
            "actual": actual_summary,
            "reason": "ok" if passed else "; ".join(mismatches),
        },
    )

def run_fallback_soul_case(case: dict[str, Any]) -> dict[str, Any]:
    """Soul cloud-failure fallback eval (mocked; no live providers).

    IN:    input.simulate; expect.has_messages / fallback / reply_contains
    STEPS: 1) start_trace
           2) mock soul_agent.ainvoke → raise; mock local_llm.ainvoke → fake reply
           3) run call_soul_agent(minimal state)
           4) read messages + trace.fallbacks
           5) score vs expect
    OUT:   {id, description, passed, expected, actual, reason}
    DON'T: call real Gemini/Groq/Ollama; raise in the harness instead of mocking
    """
    # Lazy import: graph pulls LLM client constructors; only needed for this mode.
    from app.game.npc.graph import call_soul_agent

    case_id = case.get("id", "<unknown>")
    case_input = case.get("input") or {}
    expect = case.get("expect") or {}
    simulate = case_input.get("simulate")

    if simulate is None:
        raise ValueError(f"case {case_id} missing input.simulate")
    if simulate != "cloud_soul_failure":
        raise ValueError(f"case {case_id} unsupported simulate={simulate!r}")
    if "has_messages" not in expect:
        raise ValueError(f"case {case_id} missing expect.has_messages")

    # Minimal CombinedState — only fields call_soul_agent reads.
    state = {
        "messages": [HumanMessage(content="hello")],
        "mood": 50,
        "summary": "",
        "location": "",
        "weather": "",
        "remaining_steps": 0,
        "session_id": "eval-fallback-session",
    }

    clear_trace()
    start_trace(session_id=state["session_id"], mood_before=state["mood"])

    # MODIFIED: replace whole LLM objects — ChatOllama is a Pydantic model and
    # rejects setattr on "ainvoke". Failures must still come from soul_agent so
    # call_soul_agent's except-branch runs.
    fake_local = AIMessage(content="Offline stub reply")
    mock_soul = AsyncMock()
    mock_soul.ainvoke = AsyncMock(
        side_effect=RuntimeError("simulated cloud soul failure")
    )
    mock_local = AsyncMock()
    mock_local.ainvoke = AsyncMock(return_value=fake_local)

    with (
        patch("app.game.npc.agents.soul_agent", mock_soul),
        patch("app.game.npc.graph.local_llm", mock_local),
    ):
        result = asyncio.run(call_soul_agent(state))  # type: ignore[arg-type]

    messages = result.get("messages") or []
    reply_text = ""
    if messages:
        reply_text = str(getattr(messages[-1], "content", messages[-1]))

    trace = get_trace()
    fallbacks = list(trace.fallbacks) if trace is not None else []
    clear_trace()

    mismatches: list[str] = []
    has_messages = bool(messages)
    if has_messages != bool(expect["has_messages"]):
        mismatches.append(
            f"has_messages expected={expect['has_messages']!r} actual={has_messages!r}"
        )

    if "fallback" in expect and expect["fallback"] not in fallbacks:
        mismatches.append(
            f"fallback expected={expect['fallback']!r} actual={fallbacks!r}"
        )

    if "reply_contains" in expect and expect["reply_contains"] not in reply_text:
        mismatches.append(
            f"reply_contains expected={expect['reply_contains']!r} actual={reply_text!r}"
        )

    passed = not mismatches
    actual_summary = {
        "has_messages": has_messages,
        "fallbacks": fallbacks,
        "reply": reply_text,
    }
    return _result_shell(
        case,
        {
            "passed": passed,
            "expected": expect,
            "actual": actual_summary,
            "reason": "ok" if passed else "; ".join(mismatches),
        },
    )


def run_output_reject_case(case: dict[str, Any]) -> dict[str, Any]:
    """Deterministic output-guard eval — same shell as tool_reject, different middle.

    IN:    case["input"].reply; case["expect"].reason  (a violation id)
    STEPS: 1) sanitize_npc_reply  2) pick matching violation  3) score
    OUT:   {id, description, passed, expected, actual, reason}
    DON'T: touch DB; call LLM; assert on full reply prose quality
    """
    case_id = case.get("id", "<unknown>")
    case_input = case.get("input") or {}
    expected = (case.get("expect") or {}).get("reason")
    if expected is None:
        raise ValueError(f"case {case_id} missing expect.reason")
    if "reply" not in case_input:
        raise ValueError(f"case {case_id} missing input.reply")

    result = sanitize_npc_reply(str(case_input["reply"]))
    # Prefer exact violation match; if missing, surface first violation (or None).
    if expected in result.violations:
        actual: str | None = expected
    elif result.violations:
        actual = result.violations[0]
    else:
        actual = None

    return _result_shell(case, score_reason(expected=expected, actual=actual))


def main() -> int:
    cases = load_cases()
    results: list[dict[str, Any]] = []

    for case in cases:
        mode = case.get("mode", "route_only")
        if mode == "route_only":
            result = run_route_case(case)
        elif mode == "tool_reject":
            result = run_tool_reject_case(case)
        elif mode == "output_reject":
            result = run_output_reject_case(case)
        # MODIFIED: wire quest_flow so quest.yaml is not silently SKIP'd.
        elif mode == "quest_flow":
            result = run_quest_flow_case(case)
        # MODIFIED: wire fallback_soul for fallback.yaml.
        elif mode == "fallback_soul":
            result = run_fallback_soul_case(case)
        else:
            print(f"SKIP  {case.get('id')} (unsupported mode={mode})")
            continue

        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}  {result['id']}: {result['reason']}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\nSummary: {passed}/{total} passed")
    return 0 if passed == total and total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
