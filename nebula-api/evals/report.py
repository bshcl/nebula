"""Machine-readable eval reports and a diff between two runs.

Scores stay deterministic. This module does not call a model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Group one run by suite (case mode) and keep each case pass/fail."""
    suites: dict[str, dict[str, Any]] = {}
    cases: list[dict[str, Any]] = []
    for result in results:
        mode = str(result.get("mode") or "unknown")
        bucket = suites.setdefault(mode, {"mode": mode, "passed": 0, "total": 0})
        bucket["total"] += 1
        passed = bool(result.get("passed"))
        if passed:
            bucket["passed"] += 1
        cases.append(
            {
                "id": result.get("id", "<unknown>"),
                "mode": mode,
                "passed": passed,
                "reason": result.get("reason", ""),
            }
        )

    suite_rows: list[dict[str, Any]] = []
    for bucket in suites.values():
        total = int(bucket["total"])
        passed_count = int(bucket["passed"])
        bucket["pass_rate"] = round(passed_count / total, 4) if total else 0.0
        suite_rows.append(bucket)

    passed_count = sum(1 for case in cases if case["passed"])
    total = len(cases)
    return {
        "passed": passed_count,
        "total": total,
        "pass_rate": round(passed_count / total, 4) if total else 0.0,
        "suites": suite_rows,
        "cases": cases,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def load_report(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} is not an eval report object")
    return loaded


def diff_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    """List case ids whose pass/fail flipped between two reports."""
    before_cases = {case["id"]: bool(case["passed"]) for case in before.get("cases", [])}
    after_cases = {case["id"]: bool(case["passed"]) for case in after.get("cases", [])}

    pass_to_fail: list[str] = []
    fail_to_pass: list[str] = []
    added: list[str] = []
    for case_id, passed in after_cases.items():
        if case_id not in before_cases:
            added.append(case_id)
        elif before_cases[case_id] and not passed:
            pass_to_fail.append(case_id)
        elif not before_cases[case_id] and passed:
            fail_to_pass.append(case_id)

    removed = [case_id for case_id in before_cases if case_id not in after_cases]
    return {
        "pass_to_fail": pass_to_fail,
        "fail_to_pass": fail_to_pass,
        "added": added,
        "removed": removed,
    }


def format_summary(report: dict[str, Any]) -> str:
    lines = ["Suites:"]
    for suite in report["suites"]:
        lines.append(f"  {suite['mode']} {suite['passed']}/{suite['total']}")
    lines.append(f"\nSummary: {report['passed']}/{report['total']} passed")
    return "\n".join(lines)


def format_diff(changes: dict[str, list[str]]) -> str:
    lines = ["Eval diff:"]
    for key in ("pass_to_fail", "fail_to_pass", "added", "removed"):
        ids = changes[key]
        shown = ", ".join(ids) if ids else "(none)"
        lines.append(f"  {key}: {shown}")
    return "\n".join(lines)
