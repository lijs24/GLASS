from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.release_promotion_decision import build_release_promotion_decision


def _write_acceptance(path: Path, *, passed: bool = True) -> None:
    accounting_status = "passed" if passed else "failed"
    sample_closure_status = "passed" if passed else "failed"
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
                    "rejection_sample_accounting": {
                        "status": accounting_status,
                        "check_present": True,
                        "check_passed": passed,
                        "failed_count": 0 if passed else 1,
                    },
                    "sample_accounting_closure": {
                        "status": sample_closure_status,
                        "check_present": True,
                        "check_passed": passed,
                        "present_count": 1,
                        "failed_count": 0 if passed else 1,
                    },
                },
                "stack_engine_default_promotion": {
                    "status": "passed" if passed else "failed",
                    "default_promotion_ready": passed,
                    "default_promotion_blocker_count": 0 if passed else 1,
                    "stack_engine_contract_scope": "all",
                    "failed_checks": [] if passed else ["contract_stack_engine_default_promotion_ready"],
                },
            },
            "pipeline_contract": {
                "audit_type": "pipeline_invariant_contract",
                "status": "passed" if passed else "failed",
                "passed": passed,
                "check_count": 6,
                "check_names": [
                    "integration_dq_contract",
                    "integration_stack_result_contract",
                    "integration_resident_result_contract",
                    "integration_dq_map_pixels_match_summary",
                    "integration_coverage_map_pixels_match_dq",
                    "integration_rejection_map_pixels_match_dq",
                    "integration_rejection_sample_counts_match_maps",
                    "integration_sample_accounting_closure",
                ],
                "failed_checks": []
                if passed
                else [
                    "integration_dq_contract",
                    "integration_dq_map_pixels_match_summary",
                    "integration_rejection_sample_counts_match_maps",
                    "integration_sample_accounting_closure",
                ],
                "rejection_sample_accounting": {
                    "status": accounting_status,
                    "check_name": "integration_rejection_sample_counts_match_maps",
                    "check_present": True,
                    "check_passed": passed,
                    "accounted_output_count": 1,
                    "failed_count": 0 if passed else 1,
                    "failed_items": []
                    if passed
                    else [
                        {
                            "item": "H",
                            "map_rejected_sample_sum": 7,
                            "source_counts": [
                                {
                                    "name": "dq_coverage_provenance.rejected_sample_count",
                                    "count": 6,
                                }
                            ],
                        }
                    ],
                },
                "sample_accounting_closure": {
                    "status": sample_closure_status,
                    "check_name": "integration_sample_accounting_closure",
                    "check_present": True,
                    "check_passed": passed,
                    "present_count": 1,
                    "failed_count": 0 if passed else 1,
                    "failed_items": []
                    if passed
                    else [
                        {
                            "item": "H",
                            "input_valid_samples_before_rejection": 9,
                            "valid_samples_after_rejection": 6,
                            "rejected_samples": 2,
                        }
                    ],
                },
                "integration": {
                    "outputs": [
                        {
                            "item": "H",
                            "sample_accounting_closure": {
                                "present": True,
                                "required": True,
                                "status": sample_closure_status,
                                "passed": passed,
                                "input_valid_samples_before_rejection": 9,
                                "valid_samples_after_rejection": 6,
                                "rejected_samples": 3 if passed else 2,
                                "valid_rejection_match": passed,
                            },
                        }
                    ],
                    "maps": [
                        {"item": "H", "map": "master"},
                        {"item": "H", "map": "coverage"},
                        {"item": "H", "map": "dq"},
                    ],
                },
                "pixel_verification": {
                    "enabled": passed,
                    "tile_size": 2048,
                    "integration_outputs": [
                        {
                            "item": "H",
                            "rejection_sample_accounting": {
                                "status": "verified",
                                "verified": True,
                                "ok": passed,
                                "required": True,
                                "map_rejected_sample_sum": 6 if passed else 7,
                                "source_counts": [
                                    {
                                        "name": "dq_coverage_provenance.rejected_sample_count",
                                        "count": 6,
                                    }
                                ],
                            },
                        }
                    ],
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


def _write_pipeline_contract(
    path: Path,
    *,
    rejection_sample_accounting_passed: bool = True,
    sample_accounting_closure_passed: bool = True,
) -> None:
    pipeline_passed = rejection_sample_accounting_passed and sample_accounting_closure_passed
    write_json(
        path,
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "passed" if pipeline_passed else "failed",
            "passed": pipeline_passed,
            "checks": [
                {"name": "integration_dq_contract", "passed": True},
                {"name": "integration_stack_result_contract", "passed": True},
                {"name": "integration_resident_result_contract", "passed": True},
                {"name": "integration_dq_map_pixels_match_summary", "passed": True},
                {"name": "integration_coverage_map_pixels_match_dq", "passed": True},
                {"name": "integration_rejection_map_pixels_match_dq", "passed": True},
                {
                    "name": "integration_rejection_sample_counts_match_maps",
                    "passed": rejection_sample_accounting_passed,
                },
                {
                    "name": "integration_sample_accounting_closure",
                    "passed": sample_accounting_closure_passed,
                },
            ],
            "rejection_sample_accounting": {
                "status": "passed" if rejection_sample_accounting_passed else "failed",
                "check_name": "integration_rejection_sample_counts_match_maps",
                "check_present": True,
                "check_passed": rejection_sample_accounting_passed,
                "accounted_output_count": 1,
                "failed_count": 0 if rejection_sample_accounting_passed else 1,
                "failed_items": []
                if rejection_sample_accounting_passed
                else [
                    {
                        "item": "H",
                        "map_rejected_sample_sum": 7,
                        "source_counts": [
                            {
                                "name": "dq_coverage_provenance.rejected_sample_count",
                                "count": 6,
                            }
                        ],
                    }
                ],
            },
            "sample_accounting_closure": {
                "status": "passed" if sample_accounting_closure_passed else "failed",
                "check_name": "integration_sample_accounting_closure",
                "check_present": True,
                "check_passed": sample_accounting_closure_passed,
                "present_count": 1,
                "failed_count": 0 if sample_accounting_closure_passed else 1,
                "failed_items": []
                if sample_accounting_closure_passed
                else [
                    {
                        "item": "H",
                        "input_valid_samples_before_rejection": 9,
                        "valid_samples_after_rejection": 6,
                        "rejected_samples": 2,
                    }
                ],
            },
            "integration": {
                "outputs": [
                    {
                        "item": "H",
                        "sample_accounting_closure": {
                            "present": True,
                            "required": True,
                            "status": "passed"
                            if sample_accounting_closure_passed
                            else "failed",
                            "passed": sample_accounting_closure_passed,
                            "input_valid_samples_before_rejection": 9,
                            "valid_samples_after_rejection": 6,
                            "rejected_samples": 3
                            if sample_accounting_closure_passed
                            else 2,
                            "valid_rejection_match": sample_accounting_closure_passed,
                        },
                    }
                ],
                "maps": [
                    {"item": "H", "map": "master"},
                    {"item": "H", "map": "coverage"},
                    {"item": "H", "map": "dq"},
                ],
            },
            "pixel_verification": {
                "enabled": True,
                "tile_size": 2048,
                "integration_outputs": [
                    {
                        "item": "H",
                        "rejection_sample_accounting": {
                            "status": "verified",
                            "verified": True,
                            "ok": rejection_sample_accounting_passed,
                            "required": True,
                            "map_rejected_sample_sum": 6
                            if rejection_sample_accounting_passed
                            else 7,
                            "source_counts": [
                                {
                                    "name": "dq_coverage_provenance.rejected_sample_count",
                                    "count": 6,
                                }
                            ],
                        },
                    }
                ],
            },
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


def _write_runtime_compare_with_slow_warmup(path: Path) -> None:
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
                {"label": "repeat_3", "total_elapsed_s": 18.1},
                {"label": "repeat_1", "total_elapsed_s": 29.0},
            ],
            "runs": [
                {"label": "repeat_1", "total_elapsed_s": 29.0},
                {"label": "repeat_2", "total_elapsed_s": 18.0},
                {"label": "repeat_3", "total_elapsed_s": 18.1},
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
    assert payload["pipeline_handoff"]["source"] == "explicit_pipeline_contract"
    assert payload["pipeline_handoff"]["pixel_verification_enabled"] is True
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
    assert payload["pipeline_handoff"]["source"] == "acceptance_pipeline_contract"
    assert payload["runtime_repeat"]["elapsed_ratio_vs_best"] == 19.0 / 18.0


def test_release_promotion_decision_can_ignore_explicit_warmup_run(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_runtime_compare_with_slow_warmup(runtime)

    blocked = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=2,
    )
    ready = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=2,
        ignore_warmup_runs=1,
    )

    assert blocked["default_change_ready"] is False
    assert blocked["runtime_repeat"]["elapsed_ratio_vs_best"] == 29.0 / 18.0
    assert ready["default_change_ready"] is True
    assert ready["runtime_repeat"]["ignored_warmup_labels"] == ["repeat_1"]
    assert ready["runtime_repeat"]["considered_run_count"] == 2
    assert ready["runtime_repeat"]["elapsed_ratio_vs_best"] == 18.1 / 18.0


def test_release_promotion_decision_blocks_failed_acceptance(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    _write_acceptance(acceptance, passed=False)

    payload = build_release_promotion_decision(acceptance_audit=acceptance)

    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"


def test_release_promotion_decision_blocks_missing_pipeline_dq_handoff(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    pipeline = tmp_path / "pipeline.json"
    _write_acceptance(acceptance)
    write_json(
        pipeline,
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "passed",
            "passed": True,
        },
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        pipeline_contract=pipeline,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["release_candidate_ready"] is False
    assert checks["pipeline_handoff_evidence_present"] is True
    assert checks["pipeline_integration_dq_contract_passed"] is False
    assert checks["pipeline_pixel_verification_enabled"] is False
    assert checks["pipeline_pixel_verification_passed"] is False


def test_release_promotion_decision_blocks_rejection_sample_accounting_drift(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    stack = tmp_path / "stack.json"
    pipeline = tmp_path / "pipeline.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_stack_contract(stack)
    _write_pipeline_contract(pipeline, rejection_sample_accounting_passed=False)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        stack_engine_contract=stack,
        pipeline_contract=pipeline,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert payload["pipeline_handoff"]["rejection_sample_accounting_status"] == "failed"
    assert checks["pipeline_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_passed"]["evidence"]["failed_count"] == 1


def test_release_promotion_decision_blocks_sample_accounting_closure_drift(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    stack = tmp_path / "stack.json"
    pipeline = tmp_path / "pipeline.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_stack_contract(stack)
    _write_pipeline_contract(pipeline, sample_accounting_closure_passed=False)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        stack_engine_contract=stack,
        pipeline_contract=pipeline,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert payload["pipeline_handoff"]["sample_accounting_closure_status"] == "failed"
    assert checks["pipeline_sample_accounting_closure_passed"]["passed"] is False
    assert checks["pipeline_sample_accounting_closure_passed"]["evidence"] == {
        "check": False,
        "status": "failed",
        "present_count": 1,
        "failed_count": 1,
        "failed_items": [
            {
                "item": "H",
                "input_valid_samples_before_rejection": 9,
                "valid_samples_after_rejection": 6,
                "rejected_samples": 2,
            }
        ],
    }


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
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "Release Promotion Decision" in markdown_text
    assert "Pipeline DQ Handoff" in markdown_text

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
