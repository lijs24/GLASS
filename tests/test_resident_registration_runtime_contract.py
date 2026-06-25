from __future__ import annotations

from pathlib import Path

from glass.engine.resident_registration_runtime_contract import (
    build_resident_registration_runtime_contract,
    write_resident_registration_runtime_contract,
)
from glass.io.json_io import read_json, write_json


def _write_triangle_run(run: Path, *, fallback_frame_count: int = 0) -> None:
    write_json(
        run / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "resident_registration": {"mode": "similarity_cuda_triangle"},
                    "timing_s": {"resident_registration_warp": 0.25},
                    "triangle_catalog_batch": True,
                    "triangle_descriptor_generation_batch": True,
                    "triangle_descriptor_fit_batch": True,
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_dispatch": "chunked",
                    "triangle_warp_batch_frame_count": 2,
                    "triangle_warp_batch_fallback_frame_count": fallback_frame_count,
                    "triangle_warp_batch_native_chunk_count": 1,
                    "triangle_warp_batch_native_chunk_frames": 2,
                    "triangle_warp_batch_native_total_s": 0.2,
                    "warp_coverage": {
                        "available": True,
                        "frame_count": 3,
                        "warped_frame_count": 2,
                    },
                }
            ]
        },
    )
    write_json(
        run / "registration_results.json",
        {
            "results": [
                {"frame_id": "F001", "status": "ok"},
                {"frame_id": "F002", "status": "ok"},
                {"frame_id": "F003", "status": "reference"},
                {"frame_id": "F004", "status": "excluded"},
            ]
        },
    )
    write_json(
        run / "resident_frame_masks.json",
        {
            "summary": {
                "passed": True,
                "frame_count": 4,
                "active_frame_count": 3,
                "masked_frame_count": 1,
            }
        },
    )


def _write_registration_source_dq_input(
    run: Path,
    *,
    invalid_samples: int = 1,
    applied_invalid_samples: int = 1,
    pre_visible_invalid_samples: int = 1,
    post_deferred_invalid_samples: int = 0,
    required_not_visible_invalid_samples: int = 0,
) -> None:
    payload = read_json(run / "registration_results.json")
    rows = payload["results"]
    for row in rows:
        frame_id = str(row["frame_id"])
        is_target = frame_id == "F001"
        row["source_dq_registration_input"] = {
            "frame_id": frame_id,
            "row_count": 1 if is_target else 0,
            "invalid_samples": invalid_samples if is_target else 0,
            "applied_invalid_samples": applied_invalid_samples if is_target else 0,
            "pre_registration_catalog_visible_invalid_samples": (
                pre_visible_invalid_samples if is_target else 0
            ),
            "post_registration_deferred_invalid_samples": (
                post_deferred_invalid_samples if is_target else 0
            ),
            "required_invalid_samples_not_visible_to_registration_catalog": (
                required_not_visible_invalid_samples if is_target else 0
            ),
            "application_order_counts": {"calibration_pre_registration": 1}
            if is_target
            else {},
            "registration_catalog_visibility_counts": {
                "pre_registration_catalog_visible": 1
            }
            if is_target
            else {},
            "status_counts": {"applied": 1} if is_target else {},
            "source_counts": {"resident_calibrated_source_dq_sidecar": 1}
            if is_target
            else {},
            "sidecar_path_count": 1 if is_target else 0,
            "sidecar_paths": ["source_dq/F001_dq.fits"] if is_target else [],
            "catalog_input_semantics": (
                "source_dq_applied_before_registration_catalog"
                if is_target
                else "no_source_dq_rows_for_frame"
            ),
        }
    payload["source_dq_registration_input_summary"] = {
        "schema_version": 1,
        "available": True,
        "source_dq_row_count": 1,
        "registration_row_count": len(rows),
        "registration_rows_with_source_dq_input": len(rows),
        "registration_rows_missing_source_dq_input": 0,
        "frames_with_source_dq_rows": 1,
        "frames_with_invalid_samples": 1 if invalid_samples else 0,
        "invalid_samples": invalid_samples,
        "applied_invalid_samples": applied_invalid_samples,
        "pre_registration_catalog_visible_invalid_samples": pre_visible_invalid_samples,
        "post_registration_deferred_invalid_samples": post_deferred_invalid_samples,
        "required_invalid_samples_not_visible_to_registration_catalog": (
            required_not_visible_invalid_samples
        ),
        "catalog_input_semantics": "source_dq_rows_joined_to_registration_results",
    }
    write_json(run / "registration_results.json", payload)


def test_resident_registration_runtime_contract_passes_batched_triangle_run(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run)

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is True
    assert payload["applicable"] is True
    assert payload["summary"]["expected_warped_frame_count"] == 2
    assert payload["summary"]["warp_frames_per_s"] == 8.0
    checks = {check["name"]: check for check in payload["checks"]}
    assert checks["triangle_warp_batch_has_no_fallback"]["passed"] is True


def test_resident_registration_runtime_contract_fails_native_warp_fallback(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run, fallback_frame_count=1)

    path = write_resident_registration_runtime_contract(run)
    payload = read_json(path)

    assert payload["passed"] is False
    assert "triangle_warp_batch_has_no_fallback" in payload["failed_checks"]


def test_resident_registration_runtime_contract_allows_minimal_output_without_coverage(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run)
    artifact = read_json(run / "resident_artifacts.json")
    artifact["artifacts"][0]["warp_coverage"] = {
        "available": False,
        "frame_count": 0,
        "warped_frame_count": 2,
    }
    write_json(run / "resident_artifacts.json", artifact)

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is True
    assert payload["summary"]["warp_coverage_required"] is False


def test_resident_registration_runtime_contract_allows_fused_deferred_warp_path(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run)
    artifact = read_json(run / "resident_artifacts.json")
    artifact["artifacts"][0].update(
        {
            "triangle_warp_batch": False,
            "triangle_warp_batch_mode": "fused_matrix_deferred",
            "triangle_warp_batch_frame_count": 0,
            "triangle_warp_batch_native_chunk_count": 0,
            "triangle_warp_batch_native_chunk_frames": 0,
            "warp_coverage": {"available": False, "frame_count": 0, "warped_frame_count": 0},
        }
    )
    write_json(run / "resident_artifacts.json", artifact)

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is True
    assert payload["summary"]["triangle_native_batch_required"] is False


def test_resident_registration_runtime_contract_passes_positive_source_dq_visibility(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run)
    _write_registration_source_dq_input(run)
    write_json(
        run / "resident_source_dq_execution.json",
        {
            "artifact": "resident_source_dq_execution",
            "summary": {
                "passed": True,
                "status": "passed",
                "input_invalid_samples_before_rejection": 1,
                "applied_invalid_samples": 1,
            },
            "groups": [
                {
                    "filter": "H",
                    "passed": True,
                    "input_invalid_samples_before_rejection": 1,
                    "applied_invalid_samples": 1,
                    "required_invalid_samples_not_visible_to_registration_catalog": 0,
                    "pre_registration_catalog_visible_invalid_samples": 1,
                    "post_registration_deferred_invalid_samples": 0,
                    "application_order_counts": {"calibration_pre_registration": 1},
                    "registration_catalog_visibility_counts": {
                        "pre_registration_catalog_visible": 1
                    },
                }
            ],
        },
    )

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is True
    assert payload["summary"]["source_dq_positive"] is True
    assert payload["summary"]["source_dq_pre_registration_catalog_visible_invalid_samples"] == 1
    assert payload["summary"]["registration_source_dq_input_available"] is True
    assert payload["summary"]["registration_source_dq_input_invalid_samples"] == 1
    assert payload["summary"]["registration_source_dq_input_applied_invalid_samples"] == 1


def test_resident_registration_runtime_contract_fails_positive_source_dq_without_registration_input(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run)
    write_json(
        run / "resident_source_dq_execution.json",
        {
            "artifact": "resident_source_dq_execution",
            "summary": {
                "passed": True,
                "status": "passed",
                "input_invalid_samples_before_rejection": 1,
                "applied_invalid_samples": 1,
            },
            "groups": [
                {
                    "filter": "H",
                    "passed": True,
                    "input_invalid_samples_before_rejection": 1,
                    "applied_invalid_samples": 1,
                    "required_invalid_samples_not_visible_to_registration_catalog": 0,
                    "pre_registration_catalog_visible_invalid_samples": 1,
                    "post_registration_deferred_invalid_samples": 0,
                    "application_order_counts": {"calibration_pre_registration": 1},
                    "registration_catalog_visibility_counts": {
                        "pre_registration_catalog_visible": 1
                    },
                }
            ],
        },
    )

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is False
    assert "registration_results_carry_source_dq_input_if_positive" in payload["failed_checks"]


def test_resident_registration_runtime_contract_fails_required_source_dq_after_registration(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_triangle_run(run)
    write_json(
        run / "resident_source_dq_execution.json",
        {
            "artifact": "resident_source_dq_execution",
            "summary": {
                "passed": True,
                "status": "passed",
                "input_invalid_samples_before_rejection": 1,
                "applied_invalid_samples": 1,
            },
            "groups": [
                {
                    "filter": "H",
                    "passed": True,
                    "input_invalid_samples_before_rejection": 1,
                    "applied_invalid_samples": 1,
                    "required_invalid_samples_not_visible_to_registration_catalog": 1,
                    "pre_registration_catalog_visible_invalid_samples": 0,
                    "post_registration_deferred_invalid_samples": 1,
                    "application_order_counts": {"post_registration_pre_warp": 1},
                    "registration_catalog_visibility_counts": {"not_catalog_visible": 1},
                }
            ],
        },
    )

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is False
    assert "source_dq_registration_visibility_closes" in payload["failed_checks"]
    assert (
        payload["summary"][
            "source_dq_required_invalid_samples_not_visible_to_registration_catalog"
        ]
        == 1
    )


def test_resident_registration_runtime_contract_is_not_applicable_for_non_triangle_path(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    write_json(
        run / "resident_artifacts.json",
        {"artifacts": [{"resident_registration": {"mode": "off"}}]},
    )

    payload = build_resident_registration_runtime_contract(run)

    assert payload["passed"] is True
    assert payload["applicable"] is False
    assert payload["summary"]["registration_mode"] == "off"
