"""Run route_only golden cases against post_analyzer_router."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# Allow `python evals/run_eval.py` from nebula-api root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep harness output readable (settings import configures app logging).
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

from app.chains.routing import post_analyzer_router
from app.core.config import settings
from evals.scoring import load_cases, score_route


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
        # Router only reads mood (+ settings); other CombinedState fields unused here.
        actual = post_analyzer_router({"mood": mood})  # type: ignore[arg-type]
    finally:
        settings.SKIP_WORLD_NODE = previous_skip

    scored = score_route(expected=expected, actual=actual)
    return {
        "id": case_id,
        "description": case.get("description", ""),
        **scored,
    }


def main() -> int:
    cases = load_cases()
    results: list[dict[str, Any]] = []

    for case in cases:
        mode = case.get("mode", "route_only")
        if mode != "route_only":
            print(f"SKIP  {case.get('id')} (unsupported mode={mode})")
            continue
        result = run_route_case(case)
        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}  {result['id']}: {result['reason']}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\nSummary: {passed}/{total} passed")
    return 0 if passed == total and total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
