from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.resident_regression_gate import build_resident_regression_gate


def _write_run(
    path: Path,
    *,
    elapsed_s: float = 10.0,
    output_value: float = 1.0,
    pipeline_passed: bool = True,
    stack_engine_passed: bool = True,
    resident_result_passed: bool = True,
    frame_masks_passed: bool = True,
    dq_passed: bool = True,
    dq_lifecycle_passed: bool = True,
    source_dq_passed: bool = True,
    master_cache_passed: bool = True,
    active_frame_count: int = 2,
    masked_frame_count: int = 0,
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    master_path = path / "integration" / "resident_master_H.fits"
    write_fits_data(master_path, np.full((2, 2), output_value, dtype=np.float32))
    write_json(path / "run_timing.json", {"total_elapsed_s": elapsed_s})
    write_json(
        path / "resident_artifacts.json",
        {
            "schema_version": 1,
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["F001", "F002"],
                    "master_path": str(master_path),
                    "resident_registration": {
                        "active_frame_count": active_frame_count,
                        "triangle_determinism_signature_mode": (
                            "catalog_descriptor_fit_exact_float32_sha256"
                        ),
                        "triangle_determinism_moving_frame_count": 1,
                        "triangle_determinism_threshold_count": 1,
                        "triangle_determinism_reference_combined_sha256": "ref",
                        "triangle_determinism_moving_catalog_combined_sha256": "moving",
                        "triangle_determinism_selected_fit_combined_sha256": "fit",
                        "triangle_determinism_trial_combined_sha256": "trial",
                        "triangle_determinism": {
                            "moving": {
                                "F002": {
                                    "status": "ok",
                                    "threshold_mode": "fixed",
                                    "selected_threshold": 350.0,
                                    "threshold_candidates": [350.0],
                                    "reference_catalog": {"sha256": "rcat", "stored_count": 8},
                                    "moving_catalog": {"sha256": "moving", "stored_count": 8},
                                    "reference_descriptor": {"sha256": "rdesc", "count": 8},
                                    "moving_descriptor": {"sha256": "mdesc", "count": 8},
                                    "selected_fit": {"sha256": "fit"},
                                    "trial_signature": {"sha256": "trial"},
                                }
                            }
                        },
                    },
                }
            ],
        },
    )
    write_json(
        path / "registration_results.json",
        {
            "results": [
                {
                    "frame_id": "F002",
                    "status": "ok",
                    "matched_stars": 4,
                    "inliers": 4,
                    "rms_px": 0.2,
                    "matrix": [[1.0, 0.0, 1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]],
                }
            ]
        },
    )
    write_json(
        path / "frame_accounting.json",
        {
            "frames": [
                {
                    "frame_id": "F002",
                    "final_status": "integrated",
                    "registration_status": "ok",
                    "integration_status": "used",
                    "integration_weight": 1.0,
                }
            ]
        },
    )
    write_json(path / "pipeline_contract.json", {"passed": pipeline_passed, "status": "passed" if pipeline_passed else "failed"})
    write_json(
        path / "stack_engine_contract.json",
        {"passed": stack_engine_passed, "status": "passed" if stack_engine_passed else "failed"},
    )
    write_json(
        path / "resident_result_contract.json",
        {
            "artifact_type": "resident_cuda_result_contract",
            "passed": resident_result_passed,
            "status": "passed" if resident_result_passed else "failed",
        },
    )
    write_json(path / "resident_dq_pixel_closure.json", {"passed": dq_passed, "status": "passed" if dq_passed else "failed"})
    write_json(
        path / "resident_dq_lifecycle.json",
        {
            "artifact": "resident_dq_lifecycle",
            "summary": {
                "passed": dq_lifecycle_passed,
                "status": "passed" if dq_lifecycle_passed else "failed",
            },
        },
    )
    write_json(
        path / "resident_source_dq_execution.json",
        {
            "artifact": "resident_source_dq_execution",
            "summary": {
                "passed": source_dq_passed,
                "status": "passed" if source_dq_passed else "failed",
            },
        },
    )
    write_json(
        path / "resident_master_cache.json",
        {
            "artifact": "resident_master_cache",
            "summary": {
                "passed": master_cache_passed,
                "status": "passed" if master_cache_passed else "failed",
            },
        },
    )
    write_json(
        path / "resident_frame_masks.json",
        {
            "summary": {
                "passed": frame_masks_passed,
                "active_frame_count": active_frame_count,
                "masked_frame_count": masked_frame_count,
            }
        },
    )


def test_resident_regression_gate_passes_matching_run_with_contracts(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed_s=10.0)
    _write_run(candidate, elapsed_s=10.5)

    payload = build_resident_regression_gate(
        baseline,
        candidate,
        max_elapsed_ratio=1.1,
        min_active_frame_count=2,
        max_masked_frame_count=0,
    )

    assert payload["passed"] is True
    assert payload["failed_checks"] == []
    assert payload["runtime_comparison"]["elapsed_ratio"] == 1.05


def test_resident_regression_gate_fails_runtime_contract_and_frame_mask(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed_s=10.0)
    _write_run(
        candidate,
        elapsed_s=13.0,
        pipeline_passed=False,
        resident_result_passed=False,
        frame_masks_passed=False,
        dq_passed=False,
        dq_lifecycle_passed=False,
        source_dq_passed=False,
        master_cache_passed=False,
        active_frame_count=1,
        masked_frame_count=2,
    )

    payload = build_resident_regression_gate(
        baseline,
        candidate,
        max_elapsed_ratio=1.1,
        min_active_frame_count=2,
        max_masked_frame_count=1,
    )

    assert payload["passed"] is False
    assert "runtime_within_threshold" in payload["failed_checks"]
    assert "candidate_pipeline_contract_passed" in payload["failed_checks"]
    assert "candidate_resident_result_contract_passed" in payload["failed_checks"]
    assert "candidate_resident_frame_masks_passed" in payload["failed_checks"]
    assert "candidate_dq_pixel_closure_passed" in payload["failed_checks"]
    assert "candidate_resident_dq_lifecycle_passed" in payload["failed_checks"]
    assert "candidate_resident_source_dq_execution_passed" in payload["failed_checks"]
    assert "candidate_resident_master_cache_passed" in payload["failed_checks"]
    assert "candidate_active_frame_count_at_least_min" in payload["failed_checks"]
    assert "candidate_masked_frame_count_at_most_max" in payload["failed_checks"]


def test_resident_regression_gate_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    out = tmp_path / "gate.json"
    markdown = tmp_path / "gate.md"
    _write_run(baseline, elapsed_s=10.0)
    _write_run(candidate, elapsed_s=10.1)

    assert (
        main(
            [
                "resident-regression-gate",
                "--baseline-run",
                str(baseline),
                "--candidate-run",
                str(candidate),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--max-elapsed-ratio",
                "1.05",
                "--min-active-frame-count",
                "2",
                "--max-masked-frame-count",
                "0",
                "--fail-on-failure",
            ]
        )
        == 0
    )
    assert read_json(out)["passed"] is True
    assert "Resident Regression Gate" in markdown.read_text(encoding="utf-8")
