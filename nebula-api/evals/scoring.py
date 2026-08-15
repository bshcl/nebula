"""Load eval cases and score simple expectations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CASES_DIR = Path(__file__).resolve().parent / "cases"

_REQUIRED_CASE_KEYS = ("id", "mode", "input", "expect")


def _load_file(cases_file: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(cases_file.read_text(encoding="utf-8")) or {}
    cases = raw.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError(f"{cases_file.name} must contain a top-level 'cases' list")

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"{cases_file.name} cases[{index}] must be a mapping")
        missing = [key for key in _REQUIRED_CASE_KEYS if key not in case]
        if missing:
            raise ValueError(f"{cases_file.name} cases[{index}] missing keys: {', '.join(missing)}")
    return cases


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and lightly validate golden cases.

    Accepts a single YAML file or a directory; a directory picks up every
    *.yaml inside, so new suites only need a new file.
    """
    target = path or CASES_DIR

    if target.is_dir():
        files = sorted(target.glob("*.yaml"))
        if not files:
            raise ValueError(f"no case files found in {target}")
    else:
        files = [target]

    cases: list[dict[str, Any]] = []
    for cases_file in files:
        cases.extend(_load_file(cases_file))

    if not cases:
        raise ValueError(f"no cases loaded from {target}")
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
