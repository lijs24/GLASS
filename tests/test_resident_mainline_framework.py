from __future__ import annotations

from pathlib import Path
from argparse import Namespace

from glass.cli import _write_resident_mainline_framework
from glass.engine.pipeline import initialize_run
from glass.engine.resident_mainline_framework import (
    build_resident_mainline_framework,
    write_resident_mainline_framework,
)
from glass.io.json_io import read_json, write_json


def _touch(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fixture", encoding="utf-8")
    return str(path)


def _write_minimal_green_resident_run(
    run: Path,
    *,
    source_dq_invalid_samples: int = 0,
    source_dq_applied_samples: int | None = None,
) -> dict[str, str]:
    if source_dq_applied_samples is None:
        source_dq_applied_samples = source_dq_invalid_samples
    integration = run / "integration"
    maps = {
        "master_path": _touch(integration / "resident_master_H.fits"),
        "weight_map_path": _touch(integration / "resident_weight_map_H.fits"),
        "coverage_map_path": _touch(integration / "resident_coverage_map_H.fits"),
        "low_rejection_map_path": _touch(integration / "resident_low_rejection_map_H.fits"),
        "high_rejection_map_path": _touch(integration / "resident_high_rejection_map_H.fits"),
        "dq_map_path": _touch(integration / "resident_dq_map_H.fits"),
    }
    write_json(
        run / "run_timing.json",
        {
            "backend": "cuda",
            "memory_mode": "resident",
            "resident_runtime_preset": "throughput-v4-native-completion",
            "resident_registration": "similarity_cuda_triangle",
            "integration_rejection": "winsorized_sigma",
            "local_normalization": "on",
            "resident_local_normalization_mode": "grid_mean_std",
            "resident_warp_interpolation": "lanczos3",
            "total_elapsed_s": 3.0,
            "stages": [{"stage": "resident_calibration_integration", "elapsed_s": 2.5}],
        },
    )
    write_json(run / "run_state.json", {"current_stage": "integration", "failed_stage": None, "errors": []})
    write_json(
        run / "frame_accounting.json",
        {
            "summary": {
                "input_light_frames": 3,
                "resident_frame_mask_active_frames": 3,
                "resident_frame_mask_masked_frames": 0,
                "resident_dq_lifecycle_present": True,
                "resident_dq_lifecycle_passed": True,
                "resident_dq_lifecycle_status": "passed",
                "resident_dq_lifecycle_rows": 3,
                "resident_dq_lifecycle_active_frames": 3,
                "resident_dq_lifecycle_masked_frames": 0,
            }
        },
    )
    write_json(
        run / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    **maps,
                    "timing_s": {
                        "light_read_upload_calibrate": 1.0,
                        "resident_registration_warp": 0.1,
                        "resident_local_normalization": 0.1,
                        "resident_integration": 1.0,
                        "output_write": 0.1,
                    },
                }
            ]
        },
    )
    write_json(run / "resident_frame_masks.json", {"summary": {"passed": True, "active_frame_count": 3, "masked_frame_count": 0}})
    write_json(
        run / "resident_dq_lifecycle.json",
        {"summary": {"passed": True, "status": "passed", "frame_count": 3, "active_frame_count": 3, "masked_frame_count": 0}},
    )
    write_json(
        run / "resident_source_dq_execution.json",
        {
            "summary": {
                "passed": True,
                "status": "passed",
                "frame_count": 3,
                "active_frame_count": 3,
                "input_invalid_samples_before_rejection": int(source_dq_invalid_samples),
                "applied_invalid_samples": int(source_dq_applied_samples),
                "all_frame_input_invalid_samples_before_frame_mask": int(source_dq_invalid_samples),
                "all_frame_applied_invalid_samples": int(source_dq_applied_samples),
                "input_flagged_samples": int(source_dq_invalid_samples),
                "input_nonfinite_samples": 0,
                "source_dq_flag_counts": (
                    {"hot_pixel": int(source_dq_invalid_samples)}
                    if source_dq_invalid_samples
                    else {}
                ),
                "sidecar_source_counts": {"synthetic": 1} if source_dq_invalid_samples else {},
                "execution_routes": ["resident_in_memory_mask_streaming"],
            }
        },
    )
    for name in ("resident_dq_pixel_closure.json", "resident_master_cache.json"):
        write_json(run / name, {"summary": {"passed": True, "status": "passed"}})
    for name in (
        "pipeline_contract.json",
        "stack_engine_contract.json",
        "warp_quality_contract.json",
        "resident_result_contract.json",
        "integration_results.json",
        "calibration_artifacts.json",
        "registration_results.json",
        "local_norm_results.json",
    ):
        write_json(run / name, {"passed": True, "status": "passed"})
    return maps


def test_resident_mainline_framework_passes_minimal_green_run(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_minimal_green_resident_run(run)

    payload = build_resident_mainline_framework(run, min_lights=3, min_active_frames=3)

    assert payload["artifact_type"] == "resident_mainline_framework"
    assert payload["source_artifact_type"] == "phase2_mainline_audit"
    assert payload["scope"] == "resident_run_postcondition"
    assert payload["framework_scope"] == "default"
    assert payload["passed"] is True
    assert payload["blocking"] is False
    assert payload["policy"]["requested_action"] == "warn"
    assert payload["source_dq"]["input_invalid_samples_before_rejection"] == 0
    assert payload["source_dq"]["applied_invalid_samples"] == 0


def test_resident_mainline_framework_strict_blocks_missing_map(tmp_path: Path) -> None:
    run = tmp_path / "run"
    maps = _write_minimal_green_resident_run(run)
    Path(maps["dq_map_path"]).unlink()

    payload = build_resident_mainline_framework(
        run,
        requested_action="strict",
        min_lights=3,
        min_active_frames=3,
    )

    assert payload["passed"] is False
    assert payload["blocking"] is True
    assert "resident_output_maps_present" in payload["failed_checks"]


def test_resident_mainline_framework_source_dq_positive_threshold_passes(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_minimal_green_resident_run(run, source_dq_invalid_samples=2)

    payload = build_resident_mainline_framework(
        run,
        requested_action="strict",
        min_lights=3,
        min_active_frames=3,
        min_source_dq_invalid_samples=2,
        min_source_dq_applied_samples=2,
    )

    assert payload["passed"] is True
    assert payload["source_dq"]["input_invalid_samples_before_rejection"] == 2
    assert payload["source_dq"]["applied_invalid_samples"] == 2
    assert payload["policy"]["min_source_dq_invalid_samples"] == 2
    assert payload["policy"]["min_source_dq_applied_samples"] == 2


def test_resident_mainline_framework_source_dq_positive_threshold_fails(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_minimal_green_resident_run(run, source_dq_invalid_samples=1)

    payload = build_resident_mainline_framework(
        run,
        requested_action="strict",
        min_lights=3,
        min_active_frames=3,
        min_source_dq_invalid_samples=2,
        min_source_dq_applied_samples=2,
    )

    assert payload["passed"] is False
    assert payload["blocking"] is True
    assert "resident_source_dq_invalid_threshold_met" in payload["failed_checks"]
    assert "resident_source_dq_applied_threshold_met" in payload["failed_checks"]


def test_resident_mainline_framework_source_dq_scope_relaxes_default_route(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_minimal_green_resident_run(run, source_dq_invalid_samples=1)
    timing = read_json(run / "run_timing.json")
    timing["resident_runtime_preset"] = "manual"
    timing["resident_registration"] = "translation_preview"
    timing["integration_rejection"] = "none"
    timing["local_normalization"] = "off"
    timing["resident_warp_interpolation"] = "bilinear"
    write_json(run / "run_timing.json", timing)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    artifact["coverage_map_path"] = None
    artifact["low_rejection_map_path"] = None
    artifact["high_rejection_map_path"] = None
    write_json(run / "resident_artifacts.json", resident)

    payload = build_resident_mainline_framework(
        run,
        requested_action="strict",
        framework_scope="source_dq_positive",
        min_lights=3,
        min_active_frames=3,
        min_source_dq_invalid_samples=1,
        min_source_dq_applied_samples=1,
    )

    assert payload["passed"] is True
    assert payload["framework_scope"] == "source_dq_positive"
    check_names = {check["name"] for check in payload["checks"]}
    assert "default_resident_cuda_route" not in check_names
    assert "resident_output_maps_present" not in check_names


def test_write_resident_mainline_framework(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_minimal_green_resident_run(run)
    out = write_resident_mainline_framework(run, min_lights=3, min_active_frames=3)

    assert out == run / "resident_mainline_framework.json"
    assert read_json(out)["passed"] is True


def test_cli_resident_mainline_framework_helper_updates_run_state_artifacts(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_minimal_green_resident_run(run)
    state = initialize_run(run)
    args = Namespace(
        resident_mainline_framework_gate="warn",
        resident_mainline_framework_scope="default",
        resident_mainline_min_lights=3,
        resident_mainline_min_active_frames=3,
        resident_mainline_max_masked_frames=0,
        resident_mainline_min_source_dq_invalid_samples=0,
        resident_mainline_min_source_dq_applied_samples=0,
    )

    path = _write_resident_mainline_framework(run, args, state)

    assert path == run / "resident_mainline_framework.json"
    assert state.failed_stage is None
    assert "resident_mainline_framework" in state.completed_stages
    assert state.artifacts[-1].stage == "resident_mainline_framework"


def test_cli_resident_mainline_framework_helper_strict_sets_failed_stage(tmp_path: Path) -> None:
    run = tmp_path / "run"
    maps = _write_minimal_green_resident_run(run)
    Path(maps["dq_map_path"]).unlink()
    state = initialize_run(run)
    args = Namespace(
        resident_mainline_framework_gate="strict",
        resident_mainline_framework_scope="default",
        resident_mainline_min_lights=3,
        resident_mainline_min_active_frames=3,
        resident_mainline_max_masked_frames=0,
        resident_mainline_min_source_dq_invalid_samples=0,
        resident_mainline_min_source_dq_applied_samples=0,
    )

    _write_resident_mainline_framework(run, args, state)

    assert state.failed_stage == "resident_mainline_framework"
    assert state.errors
