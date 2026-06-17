from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.release_promotion_decision import build_release_promotion_decision


def _write_acceptance(path: Path, *, passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "status": "passed" if passed else "failed",
            "passed": passed,
            "speedup_summary": {
                "speedup_vs_wbpp": 46.8,
                "min_speedup": 2.0,
            },
            "release_contract_evidence": {
                "pipeline_contract": {
                    "status": "passed" if passed else "failed",
                    "failed_checks": [] if passed else ["pipeline_contract_passed"],
                },
                "stack_engine_default_promotion": {
                    "status": "passed" if passed else "failed",
                    "default_promotion_ready": passed,
                    "default_promotion_blocker_count": 0 if passed else 1,
                    "stack_engine_contract_scope": "all",
                    "failed_checks": [] if passed else ["contract_stack_engine_default_promotion_ready"],
                },
            },
        },
    )


def _write_stack_contract(path: Path) -> None:
    write_json(
        path,
        {
            "audit_type": "stack_engine_default_contract",
            "status": "passed",
            "passed": True,
            "scope": "all",
            "default_promotion": {
                "ready": True,
                "status": "ready",
                "blocker_count": 0,
            },
        },
    )


def _write_pipeline_contract(path: Path) -> None:
    write_json(
        path,
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "passed",
            "passed": True,
        },
    )


def _write_runtime_compare(path: Path) -> None:
    write_json(
        path,
        {
            "artifact_type": "resident_runtime_compare",
            "summary": {
                "run_count": 3,
                "best_label": "repeat_2",
                "best_elapsed_s": 18.0,
                "recommendation": "best_observed:repeat_2",
            },
            "ranked_runs": [
                {"label": "repeat_2", "total_elapsed_s": 18.0},
                {"label": "repeat_1", "total_elapsed_s": 18.5},
                {"label": "repeat_3", "total_elapsed_s": 19.0},
            ],
            "runs": [
                {"label": "repeat_1", "total_elapsed_s": 18.5},
                {"label": "repeat_2", "total_elapsed_s": 18.0},
                {"label": "repeat_3", "total_elapsed_s": 19.0},
            ],
        },
    )


def test_release_promotion_decision_requires_repeat_for_default_change(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    stack = tmp_path / "stack.json"
    pipeline = tmp_path / "pipeline.json"
    _write_acceptance(acceptance)
    _write_stack_contract(stack)
    _write_pipeline_contract(pipeline)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        stack_engine_contract=stack,
        pipeline_contract=pipeline,
    )

    assert payload["passed"] is True
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "repeat_benchmark_before_default_change"
    failed = {item["name"] for item in payload["checks"] if not item["passed"]}
    assert failed == {"runtime_repeat_evidence_ready"}


def test_release_promotion_decision_accepts_stable_runtime_compare(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert payload["recommendation"] == "promote_default_candidate"
    assert payload["runtime_repeat"]["elapsed_ratio_vs_best"] == 19.0 / 18.0


def test_release_promotion_decision_blocks_failed_acceptance(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    _write_acceptance(acceptance, passed=False)

    payload = build_release_promotion_decision(acceptance_audit=acceptance)

    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"


def test_release_promotion_decision_cli_writes_outputs_and_strict_status(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    out = tmp_path / "decision.json"
    markdown = tmp_path / "decision.md"
    _write_acceptance(acceptance)

    assert (
        main(
            [
                "release-promotion-decision",
                "--acceptance-audit",
                str(acceptance),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )
    assert read_json(out)["recommendation"] == "repeat_benchmark_before_default_change"
    assert "Release Promotion Decision" in markdown.read_text(encoding="utf-8")

    strict = tmp_path / "strict.json"
    assert (
        main(
            [
                "release-promotion-decision",
                "--acceptance-audit",
                str(acceptance),
                "--out",
                str(strict),
                "--fail-on-not-ready",
            ]
        )
        == 2
    )
