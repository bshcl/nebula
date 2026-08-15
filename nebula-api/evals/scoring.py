"""Load eval cases and score simple expectations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CASES_PATH = Path(__file__).resolve().parent / "cases.yaml"

_REQUIRED_CASE_KEYS = ("id", "mode", "input", "expect")


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and lightly validate the golden case list from YAML."""
    cases_file = path or CASES_PATH
    raw = yaml.safe_load(cases_file.read_text(encoding="utf-8")) or {}
    cases = raw.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("cases.yaml must contain a top-level 'cases' list")
    if not cases:
        raise ValueError("cases.yaml contains no cases")

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}] must be a mapping")
        missing = [key for key in _REQUIRED_CASE_KEYS if key not in case]
        if missing:
            raise ValueError(f"cases[{index}] missing keys: {', '.join(missing)}")
    return cases


def score_route(*, expected: str, actual: str) -> dict[str, Any]:
    """Compare expected route to actual route."""
    passed = expected == actual
    return {
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "reason": "ok" if passed else f"route mismatch: expected={expected} actual={actual}",
    }


# Back-compat alias used while learning the harness
score_cases = score_route
