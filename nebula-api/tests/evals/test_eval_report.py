"""Report JSON and the pass/fail diff between two eval runs."""

import json
from pathlib import Path

from evals.report import build_report, diff_reports, load_report, write_report
from evals.run_eval import main


def test_diff_lists_cases_that_flip() -> None:
    before = build_report(
        [
            {"id": "kept", "mode": "route_only", "passed": True, "reason": "ok"},
            {"id": "broke", "mode": "route_only", "passed": True, "reason": "ok"},
            {"id": "fixed", "mode": "tool_reject", "passed": False, "reason": "no"},
            {"id": "gone", "mode": "route_only", "passed": True, "reason": "ok"},
        ]
    )
    after = build_report(
        [
            {"id": "kept", "mode": "route_only", "passed": True, "reason": "ok"},
            {"id": "broke", "mode": "route_only", "passed": False, "reason": "mismatch"},
            {"id": "fixed", "mode": "tool_reject", "passed": True, "reason": "ok"},
            {"id": "new_case", "mode": "quest_flow", "passed": True, "reason": "ok"},
        ]
    )

    changes = diff_reports(before, after)

    assert changes["pass_to_fail"] == ["broke"]
    assert changes["fail_to_pass"] == ["fixed"]
    assert changes["added"] == ["new_case"]
    assert changes["removed"] == ["gone"]
    assert before["suites"][0]["mode"] == "route_only"
    assert before["suites"][0]["passed"] == 3
    assert before["suites"][0]["total"] == 3


def test_report_round_trip(tmp_path: Path) -> None:
    report = build_report(
        [{"id": "angry_low_mood", "mode": "route_only", "passed": True, "reason": "ok"}]
    )
    path = tmp_path / "eval-last.json"
    write_report(path, report)
    assert load_report(path)["cases"][0]["id"] == "angry_low_mood"


def test_main_writes_out_and_diffs_a_baseline(tmp_path: Path, capsys) -> None:
    baseline = {
        "passed": 0,
        "total": 1,
        "pass_rate": 0.0,
        "suites": [],
        "cases": [
            {
                "id": "angry_low_mood",
                "mode": "route_only",
                "passed": False,
                "reason": "old",
            }
        ],
    }
    before = tmp_path / "eval-before.json"
    before.write_text(json.dumps(baseline), encoding="utf-8")
    out = tmp_path / "nested" / "eval-after.json"

    code = main(["--out", str(out), "--diff", str(before)])

    assert code == 0
    written = load_report(out)
    assert written["passed"] == written["total"]
    assert written["total"] > 0
    assert any(case["id"] == "angry_low_mood" and case["passed"] for case in written["cases"])
    captured = capsys.readouterr()
    assert "fail_to_pass: angry_low_mood" in captured.out
    assert "route_only" in captured.out
