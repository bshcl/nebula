"""Smoke tests for the offline eval harness."""

from app.config import settings
from evals.run_eval import run_route_case
from evals.scoring import load_cases, score_route


def test_load_cases_has_route_only_entries() -> None:
    cases = load_cases()
    assert len(cases) >= 4
    route_cases = [case for case in cases if case["mode"] == "route_only"]
    assert len(route_cases) >= 4
    # New suite files (e.g. reject.yaml) must be picked up by load_cases().
    modes = {case["mode"] for case in cases}
    assert "tool_reject" in modes
    assert "output_reject" in modes
    assert "quest_flow" in modes
    assert "fallback_soul" in modes


def test_run_quest_flow_claim_when_ready() -> None:
    from evals.run_eval import run_quest_flow_case

    result = run_quest_flow_case(
        {
            "id": "unit_quest_ready",
            "mode": "quest_flow",
            "input": {"setup": "ready", "quest_id": "quest_first_hello"},
            "expect": {
                "outcome": "success",
                "status": "claimed",
                "inventory_has": "navigator_emblem",
            },
        }
    )
    assert result["passed"] is True
    assert result["actual"]["outcome"] == "success"


def test_run_fallback_soul_cloud_failure() -> None:
    from evals.run_eval import run_fallback_soul_case

    result = run_fallback_soul_case(
        {
            "id": "unit_fallback_soul",
            "mode": "fallback_soul",
            "input": {"simulate": "cloud_soul_failure"},
            "expect": {
                "has_messages": True,
                "fallback": "soul_local_ollama",
                "reply_contains": "[[SYSTEM:OFFLINE]]",
            },
        }
    )
    assert result["passed"] is True
    assert "soul_local_ollama" in result["actual"]["fallbacks"]


def test_run_tool_reject_unknown_gift() -> None:
    from evals.run_eval import run_tool_reject_case

    result = run_tool_reject_case(
        {
            "id": "unit_reject_gift",
            "mode": "tool_reject",
            "input": {"tool": "send_gift", "item_name": "legendary_blade"},
            "expect": {"reason": "unknown_item"},
        }
    )
    assert result["passed"] is True
    assert result["actual"] == "unknown_item"


def test_run_output_reject_illegal_anim() -> None:
    from evals.run_eval import run_output_reject_case

    result = run_output_reject_case(
        {
            "id": "unit_reject_anim",
            "mode": "output_reject",
            "input": {"reply": "Hi [[ANIM:DANCE]]"},
            "expect": {"reason": "removed_anim:DANCE"},
        }
    )
    assert result["passed"] is True
    assert result["actual"] == "removed_anim:DANCE"


def test_score_route_pass_and_fail() -> None:
    assert score_route(expected="angry", actual="angry")["passed"] is True
    assert score_route(expected="angry", actual="world")["passed"] is False


def test_run_route_case_angry() -> None:
    previous = settings.SKIP_WORLD_NODE
    settings.SKIP_WORLD_NODE = False
    try:
        result = run_route_case(
            {
                "id": "unit_angry",
                "mode": "route_only",
                "input": {"mood": 10},
                "expect": {"route": "angry"},
            }
        )
    finally:
        settings.SKIP_WORLD_NODE = previous

    assert result["passed"] is True
    assert result["actual"] == "angry"
