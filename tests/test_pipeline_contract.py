from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import _write_default_pipeline_contract_artifact, main
from glass.engine.contracts import DQFlag
from glass.engine.pipeline import initialize_run
from glass.engine.rejection import (
    RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
    resident_rejection_descriptor,
)
from glass.engine.resident_calibration_artifacts import write_resident_calibration_artifacts
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.html_report import write_html_report
from glass.report.pipeline_contract import build_pipeline_contract_audit
from glass.synthetic.generator import generate_synthetic_dataset


def _write_resident_mask_artifacts(path: Path, *, frame_count: int = 3, active_frame_count: int = 3) -> None:
    active = max(0, min(int(active_frame_count), int(frame_count)))
    masked = max(0, int(frame_count) - active)
    frame_ids = [f"F{index + 1}" for index in range(int(frame_count))]
    active_ids = frame_ids[:active]
    masked_ids = frame_ids[active:]
    rows = []
    for frame_id in active_ids:
        rows.append(
            {
                "frame_id": frame_id,
                "filter": "H",
                "integration_weight": 1.0,
                "mask_status": "active",
                "auditable": True,
                "mask_categories": [],
                "mask_reasons": [],
                "observed_zero_weight_statuses": [],
                "registration_status": "ok",
                "registration_quality_status": "accepted",
                "registration_quality_final_status": "accepted",
                "weighting_status": "unit",
                "local_norm_status": "ok",
            }
        )
    for frame_id in masked_ids:
        rows.append(
            {
                "frame_id": frame_id,
                "filter": "H",
                "integration_weight": 0.0,
                "mask_status": "masked",
                "auditable": True,
                "mask_categories": ["registration"],
                "mask_reasons": ["registration_status:excluded"],
                "observed_zero_weight_statuses": ["weighting_status:zero_weight"],
                "registration_status": "excluded",
                "registration_quality_status": "rejected",
                "registration_quality_final_status": "excluded",
                "weighting_status": "zero_weight",
                "local_norm_status": "skipped_zero_weight",
            }
        )
    group_summary = {
        "frame_count": int(frame_count),
        "active_frame_count": active,
        "masked_frame_count": masked,
        "unknown_zero_weight_frame_count": 0,
        "active_frame_ids": active_ids,
        "masked_frame_ids": masked_ids,
        "unknown_zero_weight_frame_ids": [],
        "mask_category_counts": {"registration": masked} if masked else {},
        "status_counts": {"active": active, "masked": masked},
        "passed": True,
    }
    group = {
        "schema_version": 1,
        "artifact": "resident_frame_mask_contract_group",
        "filter": "H",
        "registration_mode": "similarity_cuda_triangle",
        "integration_dispatch": "stack",
        "summary": group_summary,
        "rows": rows,
        "semantics": "test resident frame mask contract",
    }
    write_json(
        path / "resident_frame_masks.json",
        {
            "schema_version": 1,
            "artifact": "resident_frame_mask_contract",
            "backend": "cuda_resident_stack",
            "source_stage": "resident_calibrated_stack",
            "summary": {**group_summary, "group_count": 1},
            "groups": [group],
            "pixel_mask_semantics": "test pixel masks remain in output maps",
        },
    )
    closure_checks = [
        "frame_mask_contract_passed",
        "frame_mask_active_matches_output_link",
        "active_frame_count_matches_provenance",
        "geometric_coverage_count_matches_active",
        "post_rejection_coverage_present",
        "geometric_coverage_present",
        "dq_summary_matches_provenance",
        "rejection_sample_count_recorded",
        "rejection_sample_count_matches",
        "sample_accounting_closure_passed",
        "active_not_greater_than_input_frame_count",
    ]
    write_json(
        path / "resident_dq_pixel_closure.json",
        {
            "schema_version": 1,
            "artifact": "resident_dq_pixel_closure",
            "backend": "cuda_resident_stack",
            "source_stage": "resident_calibrated_stack",
            "summary": {
                "group_count": 1,
                "passed_group_count": 1,
                "failed_group_count": 0,
                "failed_groups": [],
                "passed": True,
                "check_counts": {name: 1 for name in closure_checks},
                "failed_check_counts": {},
            },
            "groups": [
                {
                    "schema_version": 1,
                    "artifact": "resident_dq_pixel_closure_group",
                    "filter": "H",
                    "status": "passed",
                    "passed": True,
                    "frame_mask_active_frame_count": active,
                    "frame_mask_masked_frame_count": masked,
                    "geometric_warp_coverage_frame_count": active,
                    "provenance_active_frame_count": active,
                    "rejection": "winsorized_sigma",
                    "source_terms": [
                        "geometric_warp_coverage",
                        "post_rejection_coverage",
                        "low_rejection",
                        "high_rejection",
                    ],
                    "sample_accounting_closure": {
                        "status": "passed",
                        "passed": True,
                        "input_valid_samples_before_rejection": 9,
                        "valid_samples_after_rejection": 6,
                        "rejected_samples": 3,
                        "arithmetic_delta": 0,
                        "arithmetic_match": True,
                        "valid_rejection_match": True,
                    },
                    "checks": [
                        {"name": name, "passed": True, "details": {}}
                        for name in closure_checks
                    ],
                    "semantics": "test resident DQ pixel closure",
                }
            ],
        },
    )


def _write_resident_registration_quality_artifact(
    path: Path,
    *,
    frame_count: int = 3,
    active_frame_count: int = 3,
    registration_mode: str = "similarity_cuda_triangle",
) -> None:
    active = max(0, min(int(active_frame_count), int(frame_count)))
    masked = max(0, int(frame_count) - active)
    decisions = []
    for index in range(int(frame_count)):
        frame_id = f"F{index + 1}"
        if index == 0 and active > 0:
            decision_status = "reference"
            final_status = "reference"
            accepted = True
            action = "none"
            reasons: list[str] = []
            inliers = 0
            matched = 0
            rms = 0.0
        elif index < active:
            decision_status = "accepted"
            final_status = "ok"
            accepted = True
            action = "none"
            reasons = []
            inliers = 8
            matched = 8
            rms = 0.5
        else:
            decision_status = "rejected"
            final_status = "excluded"
            accepted = False
            action = "exclude"
            reasons = ["registration_inliers_below_min:2<4"]
            inliers = 2
            matched = 2
            rms = 2.0
        decisions.append(
            {
                "schema_version": 1,
                "frame_id": frame_id,
                "registration_mode": registration_mode,
                "requested_action": "auto",
                "effective_action": "exclude",
                "original_status": "reference" if decision_status == "reference" else "ok",
                "final_status": final_status,
                "decision_status": decision_status,
                "action_applied": action,
                "accepted": accepted,
                "matched_stars": matched,
                "inliers": inliers,
                "rms_px": rms,
                "thresholds": {
                    "min_inliers": 4,
                    "max_rms_px": None,
                    "max_rms_enabled": False,
                    "catalog_capacity_limited": False,
                },
                "diagnostics": {},
                "reasons": reasons,
            }
        )
    summary = {
        "frame_count": int(frame_count),
        "decision_status_counts": {
            **({"reference": 1} if active > 0 else {}),
            **({"accepted": max(0, active - 1)} if active > 1 else {}),
            **({"rejected": masked} if masked else {}),
        },
        "final_status_counts": {
            **({"reference": 1} if active > 0 else {}),
            **({"ok": max(0, active - 1)} if active > 1 else {}),
            **({"excluded": masked} if masked else {}),
        },
        "action_counts": {"none": active, **({"exclude": masked} if masked else {})},
        "rejected_frame_ids": [f"F{index + 1}" for index in range(active, int(frame_count))],
        "warning_frame_ids": [],
    }
    write_json(
        path / "resident_registration_quality.json",
        {
            "schema_version": 1,
            "source_stage": "resident_calibrated_stack",
            "registration_mode": registration_mode,
            "requested_action": "auto",
            "min_inliers": 4,
            "max_rms_px": None,
            "summary": summary,
            "decisions": decisions,
        },
    )


def _write_resident_pipeline_run(
    path: Path,
    *,
    missing_source_terms: bool = False,
    sample_closure_status: str | None = None,
    omit_rejection_semantics: bool = False,
    resident_artifact_legacy_rejection_semantics: bool = False,
    active_frame_count: int = 3,
) -> None:
    integration_dir = path / "integration"
    integration_dir.mkdir(parents=True)
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.ones((2, 2), dtype=np.float32)
    coverage = np.array([[0, 1], [1, 1]], dtype=np.float32)
    low = np.array([[0, 1], [0, 0]], dtype=np.float32)
    high = np.array([[0, 0], [2, 0]], dtype=np.float32)
    dq = np.array(
        [
            [int(DQFlag.NO_DATA), int(DQFlag.LOW_REJECTED)],
            [int(DQFlag.HIGH_REJECTED), 0],
        ],
        dtype=np.float32,
    )
    for name, data in {
        "master_H.fits": master,
        "weight_H.fits": weight,
        "coverage_H.fits": coverage,
        "dq_H.fits": dq,
        "low_H.fits": low,
        "high_H.fits": high,
    }.items():
        write_fits_data(integration_dir / name, data)
    source_terms = [] if missing_source_terms else [
        "post_rejection_coverage",
        "low_rejection",
        "high_rejection",
        "geometric_warp_coverage",
    ]
    dq_summary = {"valid": 1, "no_data": 1, "low_rejected": 1, "high_rejected": 1}
    provenance_summary = {
        "source_schema": "resident_dq_coverage_provenance",
        "stage": "integration",
        "engine": "cuda_resident_stack",
        "active_frame_count": active_frame_count,
        "source_terms": source_terms,
        "rejected_samples": 3,
        "output_dq_summary": dq_summary,
    }
    if sample_closure_status is not None:
        provenance_summary["sample_accounting_closure"] = {
            "status": sample_closure_status,
            "input_valid_samples_before_rejection": 9,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 3,
            "valid_rejection_match": sample_closure_status == "passed",
        }
    output = {
        "filter": "H",
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "frame_count": 3,
        "master_path": str(integration_dir / "master_H.fits"),
        "weight_map_path": str(integration_dir / "weight_H.fits"),
        "coverage_map_path": str(integration_dir / "coverage_H.fits"),
        "dq_map_path": str(integration_dir / "dq_H.fits"),
        "low_rejection_map_path": str(integration_dir / "low_H.fits"),
        "high_rejection_map_path": str(integration_dir / "high_H.fits"),
        "dq_summary": dq_summary,
        "dq_coverage_provenance": {
            "available": True,
            "active_frame_count": active_frame_count,
            "geometric_frame_count_matches_active": True,
            "rejected_sample_count": 3.0,
            "rejected_sample_count_source": "low_high_rejection_maps",
            "source_terms": source_terms,
        },
        "dq_provenance_summary": provenance_summary,
        "geometric_warp_coverage": {
            "available": True,
            "frame_count": active_frame_count,
            "frame_count_matches_active": True,
        },
        "output_map_policy": {
            "available": [
                "master",
                "weight",
                "coverage",
                "dq",
                "low_rejection",
                "high_rejection",
            ],
            "written": [
                "master",
                "weight",
                "coverage",
                "dq",
                "low_rejection",
                "high_rejection",
            ],
            "skipped": [],
        },
    }
    if not omit_rejection_semantics:
        output["integration_rejection"] = resident_rejection_descriptor(
            "winsorized_sigma",
            3.0,
            3.0,
        )
    write_json(
        path / "integration_results.json",
        {"rejection": "winsorized_sigma", "outputs": [output]},
    )
    if resident_artifact_legacy_rejection_semantics:
        write_json(
            path / "resident_artifacts.json",
            {
                "schema_version": 1,
                "backend": "cuda_resident_stack",
                "artifacts": [
                    {
                        "filter": "H",
                        "integration_rejection": {
                            "mode": "winsorized_sigma",
                            "low_sigma": 3.0,
                            "high_sigma": 3.0,
                            "algorithm": RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
                        },
                    }
                ],
            },
        )
    _write_resident_mask_artifacts(path, frame_count=3, active_frame_count=active_frame_count)
    _write_resident_registration_quality_artifact(path, frame_count=3, active_frame_count=active_frame_count)


def _write_resident_source_dq_execution_fixture(path: Path, *, passed: bool = True) -> None:
    input_invalid = 2
    applied_invalid = 2 if passed else 1
    group_checks = [
        {"name": "source_dq_summary_passed", "passed": passed, "details": {"passed": passed}},
        {
            "name": "invalid_samples_applied",
            "passed": passed,
            "details": {
                "input_invalid_samples": input_invalid,
                "applied_invalid_samples": applied_invalid,
            },
        },
        {"name": "no_unsupported_frames", "passed": True, "details": {"unsupported_frame_count": 0}},
        {"name": "native_method_available", "passed": True, "details": {"native_missing_frame_count": 0}},
        {
            "name": "no_calibrated_dq_disk_cache_required",
            "passed": True,
            "details": {
                "materializes_calibrated_dq_cache": False,
                "execution_route": "resident_in_memory_mask_streaming",
            },
        },
    ]
    write_json(
        path / "resident_source_dq_execution.json",
        {
            "artifact": "resident_source_dq_execution",
            "schema_version": 1,
            "summary": {
                "schema_version": 1,
                "status": "passed" if passed else "failed",
                "passed": passed,
                "group_count": 1,
                "frame_count": 3,
                "frame_with_invalid_count": 1,
                "applied_frame_count": 1,
                "input_invalid_samples_before_rejection": input_invalid,
                "applied_invalid_samples": applied_invalid,
                "input_flagged_samples": input_invalid,
                "input_nonfinite_samples": 0,
                "materializes_calibrated_dq_cache": False,
                "execution_routes": ["resident_in_memory_mask_streaming"],
                "estimated_peak_batch_mask_bytes": 4,
                "estimated_all_frame_mask_bytes": 12,
            },
            "groups": [
                {
                    "schema_version": 1,
                    "artifact": "resident_source_dq_execution_group",
                    "filter": "H",
                    "status": "passed" if passed else "failed",
                    "passed": passed,
                    "execution_route": "resident_in_memory_mask_streaming",
                    "native_method": "ResidentCalibratedStack.apply_invalid_mask_frame",
                    "native_methods": ["ResidentCalibratedStack.apply_invalid_mask_frame"],
                    "materializes_calibrated_dq_cache": False,
                    "frame_count": 3,
                    "height": 2,
                    "width": 2,
                    "frame_with_invalid_count": 1,
                    "applied_frame_count": 1,
                    "input_invalid_samples_before_rejection": input_invalid,
                    "applied_invalid_samples": applied_invalid,
                    "input_flagged_samples": input_invalid,
                    "input_nonfinite_samples": 0,
                    "source_dq_flag_counts": {"hot_pixel": input_invalid},
                    "source_counts": {"explicit_sidecar": 1},
                    "status_counts": {"applied": 1},
                    "streaming_memory": {
                        "invalid_mask_bytes_per_pixel": 1,
                        "estimated_per_frame_mask_bytes": 4,
                        "batch_frames": 1,
                        "estimated_batch_mask_bytes": 4,
                        "estimated_all_frame_mask_bytes": 12,
                    },
                    "checks": group_checks,
                }
            ],
        },
    )


def _write_frame_accounting_fixture(path: Path, *, conflict: bool = False) -> None:
    if conflict:
        frames = [
            {
                "frame_id": "L0000",
                "filter": "H",
                "quality_gate_status": "rejected",
                "registration_status": "quality_rejected",
                "warp_status": "skipped",
                "local_norm_status": "not_run",
                "integration_status": "used",
                "integration_weight": 1.0,
                "integration_conflict_count": 3,
                "integration_conflicts": [
                    {
                        "stage": "quality",
                        "status": "rejected",
                        "reason": "positive integration weight for quality-rejected frame",
                    },
                    {
                        "stage": "registration",
                        "status": "quality_rejected",
                        "reason": "positive integration weight for non-accepted registration frame",
                    },
                    {
                        "stage": "warp",
                        "status": "skipped",
                        "reason": "positive integration weight for non-warped frame",
                    },
                ],
                "final_status": "integration_conflict",
            },
            {
                "frame_id": "L0001",
                "filter": "H",
                "quality_gate_status": "accepted",
                "registration_status": "ok",
                "warp_status": "accepted",
                "local_norm_status": "not_run",
                "integration_status": "used",
                "integration_weight": 1.0,
                "integration_conflict_count": 0,
                "integration_conflicts": [],
                "final_status": "integrated",
            },
            {
                "frame_id": "L0002",
                "filter": "H",
                "quality_gate_status": "accepted",
                "registration_status": "ok",
                "warp_status": "accepted",
                "local_norm_status": "not_run",
                "integration_status": "used",
                "integration_weight": 1.0,
                "integration_conflict_count": 0,
                "integration_conflicts": [],
                "final_status": "integrated",
            },
        ]
        final_counts = {"integration_conflict": 1, "integrated": 2}
        integrated = 2
        conflict_count = 1
        exception_frames = 1
    else:
        frames = [
            {
                "frame_id": f"L{index:04d}",
                "filter": "H",
                "quality_gate_status": "accepted",
                "registration_status": "ok" if index else "reference",
                "warp_status": "accepted",
                "local_norm_status": "not_run",
                "integration_status": "used",
                "integration_weight": 1.0,
                "integration_conflict_count": 0,
                "integration_conflicts": [],
                "final_status": "integrated",
            }
            for index in range(3)
        ]
        final_counts = {"integrated": 3}
        integrated = 3
        conflict_count = 0
        exception_frames = 0

    write_json(
        path / "frame_accounting.json",
        {
            "schema_version": 1,
            "artifact": "frame_accounting",
            "summary": {
                "input_light_frames": 3,
                "integrated_frames": integrated,
                "zero_weight_frames": 0,
                "integration_conflict_frames": conflict_count,
                "exception_frames": exception_frames,
                "final_status_counts": final_counts,
            },
            "exception_summary": {
                "count": exception_frames,
                "final_status_counts": {"integration_conflict": 1} if conflict else {},
                "primary_stage_counts": {"quality": 1} if conflict else {},
            },
            "exception_frames": [frames[0]] if conflict else [],
            "frames": frames,
        },
    )


def _write_nonresident_cuda_fast_path_pipeline_run(path: Path, *, explicit: bool) -> None:
    integration_dir = path / "integration"
    integration_dir.mkdir(parents=True)
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.ones((2, 2), dtype=np.float32)
    coverage = np.ones((2, 2), dtype=np.float32)
    dq = np.zeros((2, 2), dtype=np.float32)
    for name, data in {
        "master_H.fits": master,
        "weight_H.fits": weight,
        "coverage_H.fits": coverage,
        "dq_H.fits": dq,
    }.items():
        write_fits_data(integration_dir / name, data)
    engine_selection = {
        "default_engine": "stack_engine_cpu",
        "actual_backend": "cuda",
        "use_stack_engine": False,
        "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
        "backend": "auto",
        "cuda_available": True,
        "cuda_fast_path_eligible": True,
        "explicit_cuda_fast_path": explicit,
        "allow_cuda_streaming_accumulator_fast_path": explicit,
        "rejection": "none",
        "reason": "explicit_cuda_fast_path_requested"
        if explicit
        else "legacy_implicit_cuda_fast_path_fixture",
    }
    write_json(
        path / "integration_results.json",
        {
            "rejection": "none",
            "integration_engine_policy": engine_selection,
            "outputs": [
                {
                    "filter": "H",
                    "backend": "cuda",
                    "frame_count": 3,
                    "master_path": str(integration_dir / "master_H.fits"),
                    "weight_map_path": str(integration_dir / "weight_H.fits"),
                    "coverage_map_path": str(integration_dir / "coverage_H.fits"),
                    "dq_map_path": str(integration_dir / "dq_H.fits"),
                    "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                    "stack_engine_enabled": False,
                    "engine_selection": engine_selection,
                    "dq_summary": {"valid": 4, "no_data": 0},
                    "dq_provenance_summary": {
                        "source_schema": "cuda_streaming_accumulator_dq_provenance",
                        "stage": "integration",
                        "engine": "cuda_streaming_accumulator_fast_path",
                        "output_dq_summary": {"valid": 4, "no_data": 0},
                    },
                    "output_map_policy": {
                        "available": ["master", "weight", "coverage", "dq"],
                        "written": ["master", "weight", "coverage", "dq"],
                        "skipped": ["low_rejection", "high_rejection"],
                    },
                }
            ],
        },
    )


def test_pipeline_contract_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    local_norm_contract = tmp_path / "local_norm_contract.json"
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "local-norm-contract",
                "--run",
                str(run),
                "--out",
                str(local_norm_contract),
                "--fail-on-failed",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--local-norm-contract-json",
                str(local_norm_contract),
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["passed"] is True
    checks = {item["name"]: item for item in audit["checks"]}
    assert checks["integration_output_maps_available"]["passed"] is True
    assert checks["integration_dq_contract"]["passed"] is True
    assert checks["integration_default_engine_policy"]["passed"] is True
    assert checks["stack_engine_runtime_default_path"]["passed"] is True
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["calibrated_light_dq_contract"]["passed"] is True
    assert checks["local_normalization_contract"]["passed"] is True
    assert checks["local_normalization_continuous_contract_audit"]["passed"] is True
    assert checks["warp_outputs_have_dq_and_coverage"]["passed"] is True
    assert audit["artifacts"]["local_norm_contract"]["attached"] is True
    assert audit["artifacts"]["local_norm_contract"]["passed"] is True
    assert audit["local_normalization"]["contract_audit_attached"] is True
    assert audit["local_normalization"]["contract_audit_passed"] is True
    assert audit["integration"]["engine_policy"]["top_level"]["default_engine"] == "stack_engine_cpu"
    assert all(
        item["status"] == "stack_engine_default"
        for item in audit["integration"]["engine_policy"]["outputs"]
        if item["required"]
    )
    runtime_default = audit["stack_engine_runtime_default"]
    assert runtime_default["status"] == "passed"
    assert runtime_default["master_count"] >= 3
    assert runtime_default["legacy_master_count"] == 0
    assert runtime_default["integration_stack_engine_default_count"] >= 1
    assert runtime_default["failed_masters"] == []
    assert audit["calibration"]["master_count"] >= 3
    assert audit["calibration"]["calibrated_light_count"] >= 3
    assert all(item["contract_ok"] for item in audit["calibration"]["masters"])
    assert all(item["contract_ok"] for item in audit["calibration"]["calibrated_lights"])
    assert "GLASS Pipeline Invariant Contract Audit" in markdown.read_text(encoding="utf-8")
    assert "Integration Engine Policy" in markdown.read_text(encoding="utf-8")
    assert "StackEngine Runtime Default Path" in markdown.read_text(encoding="utf-8")


def test_pipeline_contract_pixel_verification_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "7",
            ]
        )
        == 0
    )

    audit = read_json(out)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["pixel_verification"]["enabled"] is True
    assert audit["pixel_verification"]["tile_size"] == 7
    assert checks["integration_stack_result_contract"]["passed"] is True
    assert audit["integration"]["outputs"][0]["stack_result_contract"]["passed"] is True
    assert checks["integration_dq_map_pixels_match_summary"]["passed"] is True
    assert checks["integration_coverage_map_pixels_match_dq"]["passed"] is True
    assert checks["integration_rejection_map_pixels_match_dq"]["passed"] is True
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is True


def test_pipeline_contract_pixel_verification_fails_corrupt_dq_summary(tmp_path: Path):
    run = tmp_path / "run"
    integration_dir = run / "integration"
    integration_dir.mkdir(parents=True)
    dq = np.array([[0, 0], [1, 0]], dtype=np.float32)
    coverage = np.array([[1, 1], [0, 1]], dtype=np.float32)
    zeros = np.zeros((2, 2), dtype=np.float32)
    ones = np.ones((2, 2), dtype=np.float32)
    for name, data in {
        "master_H.fits": ones,
        "weight_H.fits": ones,
        "coverage_H.fits": coverage,
        "dq_H.fits": dq,
        "low_H.fits": zeros,
        "high_H.fits": zeros,
    }.items():
        write_fits_data(integration_dir / name, data)
    write_json(
        run / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": str(integration_dir / "master_H.fits"),
                    "weight_map_path": str(integration_dir / "weight_H.fits"),
                    "coverage_map_path": str(integration_dir / "coverage_H.fits"),
                    "dq_map_path": str(integration_dir / "dq_H.fits"),
                    "low_rejection_map_path": str(integration_dir / "low_H.fits"),
                    "high_rejection_map_path": str(integration_dir / "high_H.fits"),
                    "dq_summary": {"valid": 4, "no_data": 0},
                    "dq_provenance_summary": {
                        "engine": "stack_engine_cpu",
                        "output_dq_summary": {"valid": 4, "no_data": 0},
                    },
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["integration_dq_map_pixels_match_summary"]["passed"] is False
    assert checks["integration_coverage_map_pixels_match_dq"]["passed"] is False


def test_pipeline_contract_passes_resident_result_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert checks["integration_resident_result_contract"]["passed"] is True
    assert checks["integration_resident_result_contract"]["evidence"]["required_count"] == 1
    resident_contract = audit["integration"]["outputs"][0]["resident_result_contract"]
    assert resident_contract["required"] is True
    assert resident_contract["passed"] is True
    assert resident_contract["contract"]["contract_type"] == "resident_cuda_result_contract"
    assert checks["resident_frame_mask_admission_contract"]["passed"] is True
    assert checks["resident_registration_quality_contract"]["passed"] is True
    assert checks["resident_dq_pixel_closure_contract"]["passed"] is True
    assert audit["resident_frame_masks"]["closure"]["active_frame_count"] == 3
    assert audit["resident_registration_quality"]["closure"]["active_decision_count"] == 3
    assert audit["resident_dq_pixel_closure"]["closure"]["active_frame_count"] == 3


def test_pipeline_contract_requires_resident_frame_masks_for_resident_output(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    (run / "resident_frame_masks.json").unlink()

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert checks["resident_frame_mask_admission_contract"]["passed"] is False
    assert checks["resident_frame_mask_admission_contract"]["evidence"]["required"] is True
    assert checks["resident_frame_mask_admission_contract"]["evidence"]["exists"] is False


def test_pipeline_contract_requires_resident_registration_quality_for_resident_output(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    (run / "resident_registration_quality.json").unlink()

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert checks["resident_registration_quality_contract"]["passed"] is False
    assert checks["resident_registration_quality_contract"]["evidence"]["required"] is True
    assert checks["resident_registration_quality_contract"]["evidence"]["exists"] is False


def test_pipeline_contract_blocks_resident_registration_quality_mask_drift(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, active_frame_count=2)
    _write_resident_registration_quality_artifact(run, frame_count=3, active_frame_count=3)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    evidence = checks["resident_registration_quality_contract"]["evidence"]

    assert audit["passed"] is False
    assert checks["resident_registration_quality_contract"]["passed"] is False
    assert evidence["active_decision_count"] == 3
    assert evidence["frame_mask_active_frame_count"] == 2
    assert "active_decision_count_matches_frame_masks" in evidence["failed_checks"]
    assert "rejected_decisions_match_masked_frames" in evidence["failed_checks"]


def test_pipeline_contract_blocks_resident_frame_mask_accounting_drift(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, active_frame_count=2)
    _write_frame_accounting_fixture(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    evidence = checks["resident_frame_mask_admission_contract"]["evidence"]

    assert audit["passed"] is False
    assert checks["resident_frame_mask_admission_contract"]["passed"] is False
    assert evidence["active_frame_count"] == 2
    assert evidence["integrated_frames"] == 3
    assert "active_count_matches_integrated_frames" in evidence["failed_checks"]


def test_pipeline_contract_blocks_resident_dq_pixel_closure_failure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    closure = read_json(run / "resident_dq_pixel_closure.json")
    closure["summary"]["passed"] = False
    closure["summary"]["failed_group_count"] = 1
    closure["summary"]["failed_check_counts"] = {"geometric_coverage_count_matches_active": 1}
    closure["groups"][0]["passed"] = False
    closure["groups"][0]["status"] = "failed"
    closure["groups"][0]["checks"][3]["passed"] = False
    write_json(run / "resident_dq_pixel_closure.json", closure)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    evidence = checks["resident_dq_pixel_closure_contract"]["evidence"]

    assert audit["passed"] is False
    assert checks["resident_dq_pixel_closure_contract"]["passed"] is False
    assert evidence["status"] == "failed"
    assert evidence["failed_groups"][0]["filter"] == "H"
    assert evidence["group_failed_checks"][0]["check"] == "geometric_coverage_count_matches_active"


def test_pipeline_contract_respects_resident_minimal_output_map_policy(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    output["output_map_policy"] = {
        "available": ["master"],
        "written": ["master"],
        "skipped": [],
        "mode": "minimal",
    }
    for key in [
        "weight_map_path",
        "coverage_map_path",
        "dq_map_path",
        "low_rejection_map_path",
        "high_rejection_map_path",
    ]:
        output[key] = None
    output["dq_summary"] = None
    write_json(run / "integration_results.json", integration)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert checks["integration_output_maps_available"]["passed"] is True
    assert checks["integration_dq_contract"]["passed"] is True
    assert checks["integration_resident_result_contract"]["passed"] is True


def test_pipeline_contract_accepts_resident_local_norm_group_rows(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    write_json(
        run / "local_norm_results.json",
        {
            "schema_version": 1,
            "source_stage": "resident_calibrated_stack",
            "mode": "resident_grid_mean_std",
            "enabled": True,
            "crop_box": None,
            "groups": [
                {
                    "filter": "H",
                    "enabled": True,
                    "mode": "resident_grid_mean_std",
                    "crop_box": None,
                    "frame_results": [
                        {
                            "frame_id": "F1",
                            "reference_frame_id": "F1",
                            "model": "resident_grid_mean_std",
                            "status": "reference",
                            "grid_coefficients": None,
                        },
                        {
                            "frame_id": "F2",
                            "reference_frame_id": "F1",
                            "model": "resident_grid_mean_std",
                            "status": "ok",
                            "grid_coefficients": {
                                "model": "resident_grid_pair_mean_std",
                                "grid_rows": 1,
                                "grid_cols": 1,
                            },
                        },
                    ],
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert checks["local_normalization_contract"]["passed"] is True
    assert checks["local_normalization_contract"]["evidence"]["row_count"] == 2


def test_default_resident_run_writes_pipeline_contract_artifact(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, resident_artifact_legacy_rejection_semantics=True)
    state = initialize_run(run)
    state.current_stage = "integration"

    path = _write_default_pipeline_contract_artifact(run, state)

    assert path == run / "pipeline_contract.json"
    assert path.exists()
    assert (run / "pipeline_contract.md").exists()
    payload = read_json(path)
    assert payload["passed"] is True
    assert payload["status"] == "passed"
    assert state.failed_stage is None
    assert any(item.stage == "pipeline_contract" for item in state.artifacts)


def test_default_resident_run_pipeline_contract_failure_marks_state(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(
        run,
        resident_artifact_legacy_rejection_semantics=True,
        active_frame_count=0,
    )
    state = initialize_run(run)
    state.current_stage = "integration"

    path = _write_default_pipeline_contract_artifact(run, state)

    assert path == run / "pipeline_contract.json"
    payload = read_json(path)
    assert payload["passed"] is False
    assert state.current_stage == "pipeline_contract"
    assert state.failed_stage == "pipeline_contract"
    assert "default pipeline contract failed" in state.errors
    assert any(item.stage == "pipeline_contract" for item in state.artifacts)


def test_default_resident_run_pipeline_contract_small_diagnostic_degenerate_is_nonblocking(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(
        run,
        resident_artifact_legacy_rejection_semantics=True,
        active_frame_count=1,
    )
    integration = read_json(run / "integration_results.json")
    integration["outputs"][0]["frame_count"] = 2
    write_json(run / "integration_results.json", integration)
    write_json(
        run / "frame_accounting.json",
        {
            "schema_version": 1,
            "artifact": "frame_accounting",
            "summary": {
                "input_light_frames": 2,
                "integrated_frames": 1,
                "zero_weight_frames": 1,
                "integration_conflict_frames": 0,
                "exception_frames": 1,
                "final_status_counts": {
                    "integrated": 1,
                    "registration_rejected": 1,
                },
            },
            "exception_frames": [],
            "frames": [],
        },
    )
    _write_resident_mask_artifacts(run, frame_count=2, active_frame_count=1)
    _write_resident_registration_quality_artifact(run, frame_count=2, active_frame_count=1)
    state = initialize_run(run)
    state.current_stage = "integration"

    path = _write_default_pipeline_contract_artifact(run, state)

    assert path == run / "pipeline_contract.json"
    payload = read_json(path)
    assert payload["passed"] is False
    assert state.failed_stage is None
    assert state.errors == []
    assert state.warnings == [
        "default pipeline contract failed in a non-blocking diagnostic small-frame run"
    ]


def test_pipeline_contract_passes_resident_source_dq_execution_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_source_dq_execution_fixture(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    source_dq = audit["resident_source_dq_execution"]

    assert audit["passed"] is True
    assert checks["resident_source_dq_execution_contract"]["passed"] is True
    assert checks["resident_source_dq_execution_contract"]["evidence"]["exists"] is True
    assert source_dq["status"] == "passed"
    assert source_dq["summary"]["input_invalid_samples_before_rejection"] == 2
    assert source_dq["summary"]["applied_invalid_samples"] == 2
    assert source_dq["groups"][0]["execution_route"] == "resident_in_memory_mask_streaming"
    assert source_dq["groups"][0]["materializes_calibrated_dq_cache"] is False
    assert audit["artifacts"]["resident_source_dq_execution"]["exists"] is True


def test_pipeline_contract_fails_resident_source_dq_execution_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_source_dq_execution_fixture(run, passed=False)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    evidence = checks["resident_source_dq_execution_contract"]["evidence"]

    assert audit["passed"] is False
    assert checks["resident_source_dq_execution_contract"]["passed"] is False
    assert evidence["status"] == "failed"
    assert evidence["failed_groups"][0]["filter"] == "H"
    assert evidence["failed_checks"][0]["check"] == "source_dq_summary_passed"
    assert any(item["check"] == "invalid_samples_applied" for item in evidence["failed_checks"])


def test_pipeline_contract_passes_frame_accounting_admission_consistency(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_frame_accounting_fixture(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert checks["frame_accounting_no_integration_conflicts"]["passed"] is True
    assert audit["artifacts"]["frame_accounting"]["exists"] is True
    assert audit["frame_accounting"]["present"] is True
    assert audit["frame_accounting"]["status"] == "passed"
    assert audit["frame_accounting"]["integration_conflict_frames"] == 0
    assert audit["frame_accounting"]["integrated_frames"] == 3


def test_pipeline_contract_blocks_frame_accounting_integration_conflicts(tmp_path: Path):
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"
    _write_resident_pipeline_run(run)
    _write_frame_accounting_fixture(run, conflict=True)

    result = main(
        [
            "pipeline-contract",
            "--run",
            str(run),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
        ]
    )

    audit = read_json(out)
    checks = {item["name"]: item for item in audit["checks"]}
    htmlish_markdown = markdown.read_text(encoding="utf-8")

    assert result == 2
    assert audit["passed"] is False
    assert checks["frame_accounting_no_integration_conflicts"]["passed"] is False
    assert checks["frame_accounting_no_integration_conflicts"]["evidence"]["integration_conflict_frames"] == 1
    assert checks["frame_accounting_no_integration_conflicts"]["evidence"]["conflicts"][0]["frame_id"] == "L0000"
    assert audit["frame_accounting"]["status"] == "failed"
    assert audit["frame_accounting"]["integration_conflicts"][0]["integration_conflict_count"] == 3
    assert "Frame Admission Accounting" in htmlish_markdown
    assert "integration conflicts `1`" in htmlish_markdown
    assert "positive integration weight for non-warped frame" in htmlish_markdown


def test_pipeline_contract_uses_resident_artifact_winsorized_semantics_handoff(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(
        run,
        omit_rejection_semantics=True,
        resident_artifact_legacy_rejection_semantics=True,
    )

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    contract = audit["integration"]["outputs"][0]["resident_result_contract"]["contract"]
    semantics = contract["rejection_semantics"]

    assert audit["passed"] is True
    assert checks["integration_resident_result_contract"]["passed"] is True
    assert semantics["descriptor_source"] == "resident_artifacts.integration_rejection"
    assert semantics["integration_results_descriptor_present"] is False
    assert semantics["resident_artifacts_descriptor_present"] is True
    assert semantics["legacy_completion_applied"] is True
    assert semantics["descriptor"]["resident_winsorized_mode"] == "fast_approx"
    assert semantics["descriptor"]["cpu_baseline_parity"] is False


def test_pipeline_contract_allows_explicit_nonresident_cuda_fast_path(tmp_path: Path):
    run = tmp_path / "run"
    _write_nonresident_cuda_fast_path_pipeline_run(run, explicit=True)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    engine_policy = audit["integration"]["engine_policy"]
    runtime_default = audit["stack_engine_runtime_default"]

    assert audit["passed"] is True
    assert checks["integration_default_engine_policy"]["passed"] is True
    assert checks["stack_engine_runtime_default_path"]["passed"] is True
    assert engine_policy["non_resident_count"] == 1
    assert engine_policy["failed"] == []
    assert engine_policy["outputs"][0]["status"] == "explicit_cuda_fast_path"
    assert runtime_default["explicit_cuda_fast_path_count"] == 1
    assert runtime_default["integration_stack_engine_default_count"] == 0
    assert runtime_default["failed_outputs"] == []


def test_pipeline_contract_blocks_implicit_nonresident_cuda_fast_path(tmp_path: Path):
    run = tmp_path / "run"
    _write_nonresident_cuda_fast_path_pipeline_run(run, explicit=False)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    engine_policy = audit["integration"]["engine_policy"]

    assert audit["passed"] is False
    assert checks["integration_default_engine_policy"]["passed"] is False
    assert checks["integration_default_engine_policy"]["evidence"]["failed"] == [
        {
            "item": "H",
            "status": "implicit_cuda_fast_path",
            "backend": "cuda",
            "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
            "failures": ["cuda_fast_path_not_explicit"],
        }
    ]
    assert engine_policy["failed"][0]["status"] == "implicit_cuda_fast_path"
    assert engine_policy["outputs"][0]["selection_explicit_cuda_fast_path"] is False


def test_pipeline_contract_blocks_legacy_master_runtime_default(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    calib_dir = run / "calib_cache"
    master_dir = calib_dir / "masters"
    light_dir = calib_dir / "calibrated"
    dq_dir = calib_dir / "dq"
    master_dir.mkdir(parents=True)
    light_dir.mkdir()
    dq_dir.mkdir()
    master_path = master_dir / "master_bias_legacy.fits"
    light_path = light_dir / "calibrated_L1.fits"
    dq_path = dq_dir / "dq_calibrated_L1.fits"
    write_fits_data(master_path, np.ones((2, 2), dtype=np.float32))
    write_fits_data(light_path, np.ones((2, 2), dtype=np.float32))
    write_fits_data(dq_path, np.zeros((2, 2), dtype=np.float32))
    write_json(
        run / "calibration_artifacts.json",
        {
            "masters": {
                "bias_legacy": {
                    "path": str(master_path),
                    "stats": {
                        "min": 1.0,
                        "max": 1.0,
                        "mean": 1.0,
                        "median": 1.0,
                        "std": 0.0,
                    },
                    "type": "bias",
                    "streaming": True,
                    "tile_stack_mode": "legacy_streaming_accumulator",
                    "stack_engine_enabled": False,
                    "stack_engine_fallback_reason": "diagnostic fixture",
                    "master_rejection": "none",
                    "tile_size": 2,
                }
            },
            "calibrated_lights": [
                {
                    "frame_id": "L1",
                    "path": str(light_path),
                    "dq_mask_path": str(dq_path),
                    "dq_summary": {"valid": 4, "no_data": 0},
                    "tile_count": 1,
                    "tile_size": 2,
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    runtime_default = audit["stack_engine_runtime_default"]

    assert audit["passed"] is False
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["stack_engine_runtime_default_path"]["passed"] is False
    assert runtime_default["legacy_master_count"] == 1
    assert runtime_default["failed_masters"][0]["name"] == "bias_legacy"
    assert "legacy_master_stack_mode" in runtime_default["failed_masters"][0]["failures"]


def test_pipeline_contract_surfaces_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="passed")

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    closure = audit["integration"]["outputs"][0]["sample_accounting_closure"]

    assert audit["passed"] is True
    assert checks["integration_sample_accounting_closure"]["passed"] is True
    assert checks["integration_sample_accounting_closure"]["evidence"]["present_count"] == 1
    assert closure["status"] == "passed"
    assert closure["input_valid_samples_before_rejection"] == 9
    assert closure["valid_samples_after_rejection"] == 6
    assert closure["rejected_samples"] == 3


def test_pipeline_contract_blocks_failed_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="failed")

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    closure = audit["integration"]["outputs"][0]["sample_accounting_closure"]

    assert audit["passed"] is False
    assert checks["integration_sample_accounting_closure"]["passed"] is False
    assert checks["integration_sample_accounting_closure"]["evidence"]["failed"] == [
        {
            "item": "H",
            "status": "failed",
            "input_valid_samples_before_rejection": 9,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 3,
        }
    ]
    assert closure["status"] == "failed"


def test_pipeline_contract_markdown_reports_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="passed")
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"

    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    text = markdown.read_text(encoding="utf-8")
    assert "Integration Sample Accounting Closure" in text
    assert "input-valid `9`" in text
    assert "rejected `3`" in text


def test_html_report_surfaces_pipeline_sample_accounting_closure(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, sample_closure_status="passed")
    audit = build_pipeline_contract_audit(run)
    integration = read_json(run / "integration_results.json")
    report = tmp_path / "report.html"

    write_html_report(
        report,
        integration=integration,
        pipeline_contract=audit,
        run_root=run,
    )

    text = report.read_text(encoding="utf-8")
    assert "pipeline contract sample-closure rows" in text
    assert "valid_rejection_match" in text
    assert "<td>passed</td>" in text


def test_html_report_surfaces_resident_registration_fastpath_release_evidence(
    tmp_path: Path,
):
    report = tmp_path / "report.html"
    write_html_report(
        report,
        acceptance_audit={
            "release_contract_evidence": {
                "resident_registration_fastpath": {
                    "status": "passed",
                    "required_by_benchmark_contract": True,
                    "source": "explicit_resident_artifacts_json",
                    "path": "resident_artifacts.json",
                    "available": True,
                    "artifact_count": 1,
                    "mode": "similarity_cuda_triangle",
                    "triangle_descriptor_fit_batch": True,
                    "triangle_descriptor_fit_batch_mode": (
                        "native_batch_shared_reference_device"
                    ),
                    "triangle_pixel_refine_batch": True,
                    "triangle_pixel_refine_batch_mode": (
                        "native_batch_one_seed_per_frame"
                    ),
                    "triangle_pixel_refine_batch_metric_mode": (
                        "flattened_frame_candidate_grid"
                    ),
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_frame_count": 200,
                    "resident_warp_copy_mode": (
                        "default_stream_async_device_to_device"
                    ),
                    "resident_io_pipeline_warp_copy_mode": (
                        "default_stream_async_device_to_device"
                    ),
                    "resident_warp_scratch_bytes": 4096,
                    "resident_io_pipeline_warp_scratch_bytes": 4096,
                    "passed_check_count": 12,
                    "failed_check_count": 0,
                    "failed_checks": [],
                    "checks": [
                        {
                            "name": "contract_resident_registration_fastpath_present",
                            "passed": True,
                            "evidence": {"available": True},
                        },
                        {
                            "name": (
                                "contract_resident_registration_fastpath_value:"
                                "resident_registration.mode"
                            ),
                            "passed": True,
                            "evidence": {
                                "actual": "similarity_cuda_triangle",
                                "required": "similarity_cuda_triangle",
                            },
                        },
                    ],
                }
            }
        },
    )

    text = report.read_text(encoding="utf-8")
    assert "resident_registration_fastpath" in text
    assert "similarity_cuda_triangle" in text
    assert "native_batch_shared_reference_device" in text
    assert "native_matrix_lanczos3_frames" in text
    assert "default_stream_async_device_to_device" in text
    assert "contract_resident_registration_fastpath_present" in text


def test_html_report_surfaces_failed_resident_fastpath_check_evidence(
    tmp_path: Path,
):
    report = tmp_path / "report.html"
    failed_check = (
        "contract_resident_registration_fastpath_true:"
        "resident_registration.triangle_descriptor_fit_batch"
    )
    write_html_report(
        report,
        acceptance_audit={
            "release_contract_evidence": {
                "resident_registration_fastpath": {
                    "status": "failed",
                    "required_by_benchmark_contract": True,
                    "source": "explicit_resident_artifacts_json",
                    "path": "resident_artifacts.json",
                    "available": True,
                    "artifact_count": 1,
                    "mode": "similarity_cuda_triangle",
                    "triangle_descriptor_fit_batch": False,
                    "triangle_descriptor_fit_batch_mode": (
                        "native_batch_shared_reference_device"
                    ),
                    "passed_check_count": 11,
                    "failed_check_count": 1,
                    "failed_checks": [failed_check],
                    "checks": [
                        {
                            "name": failed_check,
                            "passed": False,
                            "evidence": {
                                "actual": False,
                                "required": True,
                                "field": (
                                    "resident_registration."
                                    "triangle_descriptor_fit_batch"
                                ),
                            },
                        },
                    ],
                }
            }
        },
    )

    text = report.read_text(encoding="utf-8")
    assert failed_check in text
    assert "resident_registration.triangle_descriptor_fit_batch" in text
    assert "<td>False</td>" in text
    assert "<td>True</td>" in text
    assert "contract_resident_registration_fastpath_true" in text


def test_html_report_surfaces_resident_result_contract_failures(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, missing_source_terms=True)
    audit = build_pipeline_contract_audit(run)
    report = tmp_path / "report.html"

    write_html_report(report, pipeline_contract=audit, run_root=run)

    text = report.read_text(encoding="utf-8")
    assert "resident result-contract failure rows" in text
    assert "source_terms_present" in text
    assert "resident_contract_status" in text
    assert "<td>failed</td>" in text
    assert "cuda_resident_stack" in text


def test_html_report_surfaces_resident_source_dq_execution_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_source_dq_execution_fixture(run)
    audit = build_pipeline_contract_audit(run)
    report = tmp_path / "report.html"

    write_html_report(report, pipeline_contract=audit, run_root=run)

    text = report.read_text(encoding="utf-8")
    assert "resident source-DQ execution rows" in text
    assert "source_dq_execution" in text
    assert "resident_in_memory_mask_streaming" in text
    assert "ResidentCalibratedStack.apply_invalid_mask_frame" in text


def test_pipeline_contract_pixel_verification_reports_resident_rejection_sample_accounting(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    row = audit["pixel_verification"]["integration_outputs"][0]
    accounting = row["rejection_sample_accounting"]

    assert audit["passed"] is True
    assert checks["integration_rejection_map_pixels_match_dq"]["passed"] is True
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is True
    assert row["count_maps"]["high_rejection"]["result"]["positive_pixels"] == 1
    assert row["count_maps"]["high_rejection"]["result"]["rounded_sum"] == 2
    assert accounting["ok"] is True
    assert accounting["map_rejected_sample_sum"] == 3
    assert accounting["source_counts"] == [
        {"name": "dq_coverage_provenance.rejected_sample_count", "count": 3},
        {"name": "dq_provenance_summary.rejected_samples", "count": 3},
    ]


def test_pipeline_contract_pixel_verification_detects_resident_rejection_sample_drift(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    payload = read_json(run / "integration_results.json")
    output = payload["outputs"][0]
    output["dq_coverage_provenance"]["rejected_sample_count"] = 2.0
    output["dq_provenance_summary"]["rejected_samples"] = 2
    write_json(run / "integration_results.json", payload)

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    accounting = audit["pixel_verification"]["integration_outputs"][0]["rejection_sample_accounting"]

    assert audit["passed"] is False
    assert checks["integration_resident_result_contract"]["passed"] is True
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is False
    assert accounting["map_rejected_sample_sum"] == 3
    assert all(match["actual"] == 3 and match["summary"] == 2 for match in accounting["source_matches"])


def test_pipeline_contract_pixel_verification_detects_fractional_rejection_count_map(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    write_fits_data(run / "integration" / "low_H.fits", np.array([[0.0, 1.5], [0.0, 0.0]], dtype=np.float32))

    audit = build_pipeline_contract_audit(run, pixel_verify=True, pixel_verify_tile_size=1)
    checks = {item["name"]: item for item in audit["checks"]}
    low_map = audit["pixel_verification"]["integration_outputs"][0]["count_maps"]["low_rejection"]

    assert audit["passed"] is False
    assert checks["integration_rejection_map_pixels_match_dq"]["passed"] is False
    assert checks["integration_rejection_sample_counts_match_maps"]["passed"] is False
    assert low_map["count_integrity"]["passed"] is False
    assert low_map["result"]["fractional_pixels"] == 1


def test_pipeline_contract_accepts_resident_calibration_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    resident_calibration_contract = {
        "artifact_type": "resident_cuda_calibration_contract",
        "passed": True,
        "outputs": [
            {
                "index": 0,
                "filter": "H",
                "passed": True,
                "status": "passed",
                "master_path": str(run / "integration" / "master_H.fits"),
                "master_path_exists": True,
                "frame_count": 3,
                "set_count": 1,
                "bias_count": 2,
                "dark_count": 2,
                "flat_count": 2,
                "checks": [{"name": "resident_output_contracts_passed", "passed": True}],
            }
        ],
    }

    audit = build_pipeline_contract_audit(
        run,
        resident_calibration_contract=resident_calibration_contract,
    )
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert audit["calibration"]["resident_calibration_contract_attached"] is True
    assert audit["calibration"]["resident_master_count"] == 1
    assert audit["calibration"]["master_count"] == 1
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["resident_calibration_surface_contract"]["passed"] is True
    resident_row = audit["calibration"]["resident_masters"][0]
    assert resident_row["contract_ok"] is True
    assert resident_row["science_contract"]["contract_type"] == "resident_calibration_surface_contract"


def _write_resident_native_calibration_source(run: Path) -> None:
    cache_dir = run / "calib_cache" / "resident_masters"
    cache_dir.mkdir(parents=True)
    cache_key = "H_2x2_bias-B_dark-D_flat-F_abc123"
    for suffix in ["master_bias.npy", "master_dark.npy", "master_flat.npy", "master_stats.json"]:
        (cache_dir / f"{cache_key}_{suffix}").write_bytes(b"fixture")
    stats = {"min": 1.0, "max": 2.0, "mean": 1.5, "median": 1.5, "std": 0.1}
    write_json(
        run / "resident_artifacts.json",
        {
            "schema_version": 1,
            "backend": "cuda_resident_stack",
            "policy": {
                "flat_floor": 0.05,
                "flat_normalization": "median",
                "master_dark_includes_bias": True,
                "master_rejection": "winsorized_sigma",
            },
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["light_001", "light_002", "light_003"],
                    "master_path": str(run / "integration" / "master_H.fits"),
                    "master_stats": {
                        "bias_count": 2,
                        "dark_count": 2,
                        "flat_count": 2,
                        "set_count": 1,
                        "calibration_group_policy": "planner_matching_groups_per_light",
                        "sets": {
                            "set-H": {
                                "filter": "H",
                                "bias_group": "B",
                                "dark_group": "D",
                                "flat_group": "F",
                                "flat_bias_group": "B",
                                "bias_count": 2,
                                "dark_count": 2,
                                "flat_count": 2,
                                "dark_exposure_s": 60.0,
                                "master_dark_includes_bias": True,
                                "bias": stats,
                                "dark": stats,
                                "flat": stats,
                                "shape": {"height": 2, "width": 2},
                                "cache_dir": str(cache_dir),
                                "cache_key": cache_key,
                            }
                        },
                    },
                }
            ],
        },
    )


def test_pipeline_contract_accepts_resident_native_calibration_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_native_calibration_source(run)
    write_resident_calibration_artifacts(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is True
    assert audit["calibration"]["resident_native_calibration_artifact"] is True
    assert audit["calibration"]["local_master_count"] == 3
    assert audit["calibration"]["resident_calibrated_light_count"] == 3
    assert checks["calibration_master_surface_contract"]["passed"] is True
    assert checks["resident_calibrated_lights_present"]["passed"] is True
    assert checks["resident_calibrated_light_contract"]["passed"] is True
    assert "calibrated_light_dq_contract" not in checks


def test_pipeline_contract_maps_resident_source_dq_to_resident_calibrated_lights(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_native_calibration_source(run)
    _write_resident_source_dq_execution_fixture(run)
    write_resident_calibration_artifacts(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    lights = audit["calibration"]["resident_calibrated_lights"]

    assert audit["passed"] is True
    assert checks["resident_calibrated_light_contract"]["passed"] is True
    assert checks["resident_calibrated_light_dq_contract"]["passed"] is True
    assert checks["resident_calibrated_light_dq_contract"]["evidence"]["contract_sources"] == [
        "resident_source_dq_execution"
    ]
    assert len(lights) == 3
    assert all(light["resident_contract_ok"] for light in lights)
    assert all(light["dq_contract_ok"] for light in lights)
    assert all(not light["disk_dq_contract_ok"] for light in lights)
    assert all(light["resident_source_dq_contract_ok"] for light in lights)
    assert {light["dq_contract_source"] for light in lights} == {"resident_source_dq_execution"}
    assert lights[0]["resident_source_dq_contract"]["matching_group_count"] == 1
    assert lights[0]["resident_source_dq_contract"]["execution_routes"] == [
        "resident_in_memory_mask_streaming"
    ]


def test_pipeline_contract_fails_resident_calibrated_light_dq_when_source_dq_fails(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_native_calibration_source(run)
    _write_resident_source_dq_execution_fixture(run, passed=False)
    write_resident_calibration_artifacts(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    lights = audit["calibration"]["resident_calibrated_lights"]

    assert audit["passed"] is False
    assert checks["resident_calibrated_light_contract"]["passed"] is True
    assert checks["resident_calibrated_light_dq_contract"]["passed"] is False
    assert checks["resident_calibrated_light_dq_contract"]["evidence"]["source_dq_status"] == "failed"
    assert checks["resident_calibrated_light_dq_contract"]["evidence"]["failed"] == [
        "light_001",
        "light_002",
        "light_003",
    ]
    assert all(not light["dq_contract_ok"] for light in lights)
    assert all(not light["resident_source_dq_contract_ok"] for light in lights)


def test_pipeline_contract_synthesizes_resident_calibration_visibility_from_resident_artifacts(
    tmp_path: Path,
):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    _write_resident_native_calibration_source(run)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert not (run / "calibration_artifacts.json").exists()
    assert audit["passed"] is True
    assert audit["artifacts"]["calibration"]["exists"] is True
    assert audit["artifacts"]["calibration"]["path_exists"] is False
    assert audit["artifacts"]["calibration"]["source"] == "resident_artifacts_json_fallback"
    assert audit["calibration"]["generated_for_pipeline_contract"] is True
    assert audit["calibration"]["write_back"] is False
    assert audit["calibration"]["resident_native_calibration_artifact"] is True
    assert audit["calibration"]["resident_calibrated_light_count"] == 3
    assert checks["resident_calibrated_lights_present"]["passed"] is True
    assert checks["resident_calibrated_light_contract"]["passed"] is True


def test_pipeline_contract_cli_uses_resident_calibration_contract_json(tmp_path: Path):
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    resident_contract = tmp_path / "resident_calibration_contract.json"
    _write_resident_pipeline_run(run)
    write_json(
        resident_contract,
        {
            "artifact_type": "resident_cuda_calibration_contract",
            "passed": True,
            "outputs": [
                {
                    "index": 0,
                    "filter": "H",
                    "passed": True,
                    "status": "passed",
                    "master_path_exists": True,
                    "frame_count": 3,
                    "set_count": 1,
                    "bias_count": 2,
                    "dark_count": 2,
                    "flat_count": 2,
                    "checks": [{"name": "resident_output_contracts_passed", "passed": True}],
                }
            ],
        },
    )

    assert (
        main(
            [
                "pipeline-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--resident-calibration-contract-json",
                str(resident_contract),
            ]
        )
        == 0
    )

    audit = read_json(out)
    assert audit["calibration"]["resident_calibration_contract_attached"] is True
    assert {item["name"]: item["passed"] for item in audit["checks"]}[
        "resident_calibration_surface_contract"
    ] is True


def test_pipeline_contract_fails_resident_result_contract(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, missing_source_terms=True)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert checks["integration_resident_result_contract"]["passed"] is False
    assert checks["integration_resident_result_contract"]["evidence"]["failed"] == ["H"]
    resident_checks = {
        item["name"]: item for item in audit["integration"]["outputs"][0]["resident_result_contract"]["contract"]["checks"]
    }
    assert resident_checks["source_terms_present"]["passed"] is False


def test_pipeline_contract_fails_degenerate_resident_active_frame_count(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run, active_frame_count=1)

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    resident_checks = {
        item["name"]: item for item in audit["integration"]["outputs"][0]["resident_result_contract"]["contract"]["checks"]
    }

    assert audit["passed"] is False
    assert checks["integration_resident_result_contract"]["passed"] is False
    assert resident_checks["active_frame_count_valid"]["passed"] is True
    assert resident_checks["active_frame_count_not_degenerate"]["passed"] is False
    assert resident_checks["active_frame_count_not_degenerate"]["evidence"][
        "min_required_active_frame_count"
    ] == 2


def test_pipeline_contract_fails_missing_maps_and_crop_records(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "integration_results.json",
        {
            "rejection": "winsorized_sigma",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": "integration/master_H.fits",
                    "weight_map_path": None,
                    "coverage_map_path": None,
                    "dq_map_path": None,
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "dq_summary": {},
                }
            ],
        },
    )
    write_json(
        run / "local_norm_results.json",
        {
            "enabled": True,
            "reference_frame_id": "F1",
            "local_norm_results": [
                {
                    "frame_id": "F1",
                    "normalized_path": "local_norm_cache/local_norm_F1.fits",
                    "coverage_path": "registered_cache/coverage_F1.fits",
                    "dq_summary": {},
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["integration_output_maps_available"]["passed"] is False
    assert checks["integration_dq_contract"]["passed"] is False
    assert checks["local_normalization_contract"]["passed"] is False


def test_pipeline_contract_fails_malformed_calibration_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_pipeline_run(run)
    write_json(
        run / "calibration_artifacts.json",
        {
            "masters": {
                "bad_bias": {
                    "type": "bias",
                    "path": "calib_cache/masters/missing_bias.fits",
                    "tile_stack_mode": "stack_engine_cpu",
                    "stack_engine_enabled": True,
                    "stack_engine_dq_provenance": {
                        "result_contract": {
                            "contract_type": "stack_engine_result_contract",
                            "passed": True,
                        }
                    },
                }
            },
            "calibrated_lights": [
                {
                    "frame_id": "L1",
                    "path": "calib_cache/calibrated/missing_L1.fits",
                    "dq_mask_path": None,
                    "dq_summary": {},
                    "tile_count": 1,
                    "tile_size": 8,
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    master = audit["calibration"]["masters"][0]
    light = audit["calibration"]["calibrated_lights"][0]

    assert audit["passed"] is False
    assert checks["calibration_master_surface_contract"]["passed"] is False
    assert checks["calibrated_light_dq_contract"]["passed"] is False
    assert master["science_contract"]["stats"]["missing_keys"] == ["min", "max", "mean", "median", "std"]
    assert master["contract_ok"] is False
    assert light["dq_mask_path_exists"] is False
    assert light["dq_summary_has_valid"] is False
    assert light["contract_ok"] is False


def test_pipeline_contract_requires_stack_result_contract_for_cpu_stack_output(tmp_path: Path):
    run = tmp_path / "run"
    integration_dir = run / "integration"
    integration_dir.mkdir(parents=True)
    ones = np.ones((2, 2), dtype=np.float32)
    zeros = np.zeros((2, 2), dtype=np.float32)
    for name, data in {
        "master_H.fits": ones,
        "weight_H.fits": ones,
        "coverage_H.fits": ones,
        "dq_H.fits": zeros,
        "low_H.fits": zeros,
        "high_H.fits": zeros,
    }.items():
        write_fits_data(integration_dir / name, data)
    write_json(
        run / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": str(integration_dir / "master_H.fits"),
                    "weight_map_path": str(integration_dir / "weight_H.fits"),
                    "coverage_map_path": str(integration_dir / "coverage_H.fits"),
                    "dq_map_path": str(integration_dir / "dq_H.fits"),
                    "low_rejection_map_path": str(integration_dir / "low_H.fits"),
                    "high_rejection_map_path": str(integration_dir / "high_H.fits"),
                    "tile_stack_mode": "stack_engine_cpu",
                    "stack_engine_enabled": True,
                    "dq_summary": {"valid": 4},
                    "stack_engine_dq_provenance": {
                        "input_samples": 8,
                        "output_dq_summary": {"valid": 4},
                    },
                    "dq_provenance_summary": {
                        "source_schema": "stack_engine_dq_provenance",
                        "engine": "stack_engine_cpu",
                        "stage": "integration",
                    },
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}

    assert audit["passed"] is False
    assert checks["integration_stack_result_contract"]["passed"] is False
    assert checks["integration_stack_result_contract"]["evidence"]["failed"] == ["H"]
    assert audit["integration"]["outputs"][0]["stack_result_contract"]["status"] == "missing_or_failed"
