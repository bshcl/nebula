"""Smoke tests for the offline eval harness."""

from app.config import settings
from evals.run_eval import run_route_case
from evals.scoring import load_cases, score_route


def test_load_cases_has_route_only_entries() -> None:
    cases = load_cases()
    assert len(cases) >= 4
    assert all(case["mode"] == "route_only" for case in cases)


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
