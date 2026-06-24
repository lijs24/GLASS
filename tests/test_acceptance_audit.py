from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.dq_contract_profile import resident_dq_provenance_contract
from glass.report.acceptance_audit import build_acceptance_audit, write_acceptance_audit_markdown


def _write_manifest(path: Path, *, light: int = 200, bias: int = 20, dark: int = 20, flat: int = 20) -> None:
    frames = []
    for frame_type, count in {"light": light, "bias": bias, "dark": dark, "flat": flat}.items():
        frames.extend({"id": f"{frame_type}_{idx}", "frame_type": frame_type} for idx in range(count))
    write_json(path, {"frames": frames, "summary": {"count": len(frames)}})


def _write_glass_run(
    path: Path,
    *,
    elapsed_s: float = 100.0,
    active: int = 193,
    zero: int = 7,
    command: str | None = None,
    run_timing_extra: dict[str, object] | None = None,
    resident_timing: dict[str, float] | None = None,
    resident_io_pipeline: dict[str, object] | None = None,
    resident_registration_mode: str | None = None,
    resident_dq: bool = False,
    frame_accounting: bool = False,
) -> None:
    path.mkdir()
    run_timing: dict[str, object] = {"total_elapsed_s": elapsed_s, "memory_mode": "resident"}
    if run_timing_extra is not None:
        run_timing.update(run_timing_extra)
    write_json(path / "run_timing.json", run_timing)
    if command is not None:
        (path / "run_command.txt").write_text(command, encoding="utf-8")
    weights = {f"L{idx:04d}": 1.0 for idx in range(active)}
    weights.update({f"Z{idx:04d}": 0.0 for idx in range(zero)})
    output = {
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "frame_count": active + zero,
        "master_path": "master.fits",
    }
    resident_artifact: dict[str, object] = {}
    if resident_timing is not None:
        resident_artifact["timing_s"] = resident_timing
    if resident_io_pipeline is not None:
        resident_artifact["resident_io_pipeline"] = resident_io_pipeline
    if resident_registration_mode is not None:
        resident_artifact["resident_registration"] = {"mode": resident_registration_mode}
    if resident_dq:
        master = path / "master.fits"
        weight_map = path / "weight_map.fits"
        dq_map = path / "dq_map.fits"
        coverage_map = path / "coverage_map.fits"
        low_rejection_map = path / "low_rejection_map.fits"
        high_rejection_map = path / "high_rejection_map.fits"
        write_fits_data(master, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
        write_fits_data(weight_map, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
        dq_values = np.array(
            [
                [0, int(DQFlag.WARP_EDGE), int(DQFlag.LOW_REJECTED)],
                [int(DQFlag.HIGH_REJECTED), int(DQFlag.WARP_EDGE | DQFlag.HIGH_REJECTED), 0],
            ],
            dtype=np.uint32,
        )
        write_fits_data(dq_map, dq_values, dtype=np.float32)
        write_fits_data(coverage_map, np.ones((2, 3), dtype=np.float32), dtype=np.float32)
        write_fits_data(
            low_rejection_map,
            np.array([[0, 0, 1], [0, 0, 0]], dtype=np.float32),
            dtype=np.float32,
        )
        write_fits_data(
            high_rejection_map,
            np.array([[0, 0, 0], [1, 2, 0]], dtype=np.float32),
            dtype=np.float32,
        )
        dq_summary = {
            "valid": 2,
            "no_data": 0,
            "warp_edge": 2,
            "low_rejected": 1,
            "high_rejected": 2,
        }
        dq_coverage_provenance = {
            "active_frame_count": active,
            "source_terms": [
                "post_rejection_coverage",
                "low_rejection",
                "high_rejection",
                "geometric_warp_coverage",
            ],
            "finite_pre_rejection_coverage": {"finite_pixels": 1000},
            "post_rejection_coverage": {"finite_pixels": 6},
            "rejected_sample_count": 4,
            "geometric_zero_pixels": 0,
            "geometric_partial_pixels": 12,
            "partial_pre_rejection_pixels": 12,
        }
        output.update(
            {
                "master_path": str(master),
                "weight_map_path": str(weight_map),
                "dq_map_path": str(dq_map),
                "coverage_map_path": str(coverage_map),
                "low_rejection_map_path": str(low_rejection_map),
                "high_rejection_map_path": str(high_rejection_map),
                "output_map_policy": {
                    "available": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                    "mode": "audit",
                    "skipped": [],
                    "written": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                },
                "dq_summary": dq_summary,
                "dq_coverage_provenance": dq_coverage_provenance,
            }
        )
        resident_artifact.update(
            {
                "master_path": str(master),
                "weight_map_path": str(weight_map),
                "dq_map_path": str(dq_map),
                "coverage_map_path": str(coverage_map),
                "low_rejection_map_path": str(low_rejection_map),
                "high_rejection_map_path": str(high_rejection_map),
                "output_map_policy": {
                    "available": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                    "mode": "audit",
                    "skipped": [],
                    "written": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                },
                "dq_summary": dq_summary,
                "dq_coverage_provenance": dq_coverage_provenance,
            }
        )
    write_json(
        path / "integration_results.json",
        {
            "frame_weights": weights,
            "weighting": "none",
            "rejection": "winsorized_sigma",
            "outputs": [output],
        },
    )
    if resident_artifact:
        write_json(path / "resident_artifacts.json", {"artifacts": [resident_artifact]})
    if frame_accounting:
        write_json(
            path / "registration_results.json",
            {
                "source_stage": "resident_calibrated_stack",
                "results": [
                    *[
                        {"frame_id": f"L{idx:04d}", "status": "ok"}
                        for idx in range(active)
                    ],
                    *[
                        {"frame_id": f"Z{idx:04d}", "status": "excluded"}
                        for idx in range(zero)
                    ],
                ],
            },
        )
        write_json(
            path / "frame_accounting.json",
            {
                "schema_version": 1,
                "artifact": "frame_accounting",
                "integration_source_stage": "resident_calibrated_stack",
                "summary": {
                    "input_light_frames": active + zero,
                    "resident_calibrated_frames": active + zero,
                    "registration_accepted_frames": active,
                    "integrated_frames": active,
                    "zero_weight_frames": zero,
                    "exception_frames": zero,
                    "final_status_counts": {"integrated": active, "zero_weight": zero},
                },
                "exception_summary": {
                    "count": zero,
                    "final_status_counts": {"zero_weight": zero},
                    "primary_stage_counts": {"integration": zero},
                },
                "exception_frames": [
                    {
                        "frame_id": f"Z{idx:04d}",
                        "filter": "H",
                        "final_status": "zero_weight",
                        "primary_stage": "integration",
                        "primary_reason": "integration weight is zero",
                        "registration_status": "excluded",
                        "integration_status": "zero_weight",
                        "integration_weight": 0.0,
                    }
                    for idx in range(zero)
                ],
                "frames": [
                    *[
                        {
                            "frame_id": f"L{idx:04d}",
                            "final_status": "integrated",
                            "integration_status": "used",
                            "integration_weight": 1.0,
                            "registration_status": "ok",
                        }
                        for idx in range(active)
                    ],
                    *[
                        {
                            "frame_id": f"Z{idx:04d}",
                            "final_status": "zero_weight",
                            "integration_status": "zero_weight",
                            "integration_weight": 0.0,
                            "registration_status": "excluded",
                        }
                        for idx in range(zero)
                    ],
                ],
            },
        )


def _write_wbpp_result(path: Path, *, elapsed_s: float = 1000.0) -> None:
    path.write_text(
        "\ufeff" + json.dumps({"elapsed_s": elapsed_s, "dataset": "fixture"}),
        encoding="utf-8",
    )


def _write_compare(
    path: Path,
    *,
    shape_match: bool = True,
    rms: float = 0.001,
    p99: float = 0.002,
    scale: float = 8.764434957115609e-06,
    offset: float = 0.0006274500691899127,
    min_coverage: float = 190.0,
    coverage_fraction: float = 0.97,
) -> None:
    write_json(
        path,
        {
            "shape_match": shape_match,
            "rms_diff": rms,
            "abs_diff_p99": p99,
            "candidate_transform": {
                "applied": True,
                "scale": scale,
                "offset": offset,
                "clip_low": None,
                "clip_high": None,
            },
            "comparison_region": {
                "coverage_fraction": coverage_fraction,
                "compared_pixels": 123,
                "min_coverage": min_coverage,
            },
        },
    )


def _write_contract(path: Path, *, max_runtime_factor: float = 1.3) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "name": "fixture_contract",
            "dataset_requirements": {
                "light": 200,
                "bias": 20,
                "dark": 20,
                "flat": 20,
                "active_light_frames": 190,
            },
            "runtime": {
                "release_baseline_elapsed_s": 30.0,
                "max_runtime_regression_factor": max_runtime_factor,
                "min_speedup_vs_reference": 20.0,
            },
            "comparison": {
                "required_scale": 8.764434957115609e-06,
                "required_offset": 0.0006274500691899127,
                "required_min_coverage": 190.0,
                "min_coverage_fraction": 0.95,
                "max_rms_diff": 0.01,
                "max_abs_diff_p99": 0.01,
            },
            "required_command_tokens": [
                "--memory-mode resident",
                "--resident-registration similarity_cuda_triangle",
                "--flat-floor 0.05",
            ],
            "timing_baseline": {
                "warning_regression_factor": 1.15,
                "stages_s": {
                    "master_build_or_load": 10.0,
                    "light_read_upload_calibrate": 15.0,
                    "resident_registration_warp": 11.0,
                    "output_write": 1.0,
                },
            },
        },
    )


def _add_resident_registration_fastpath_contract(path: Path) -> None:
    payload = read_json(path)
    payload["resident_registration_fastpath"] = {
        "required": True,
        "required_values": {
            "resident_registration.mode": "similarity_cuda_triangle",
            "resident_registration.triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
            "resident_registration.triangle_pixel_refine_batch_mode": "native_batch_one_seed_per_frame",
            "resident_registration.triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
            "resident_registration.triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
            "artifact.resident_warp_copy_mode": "default_stream_async_device_to_device",
            "resident_io_pipeline.warp_copy_mode": "default_stream_async_device_to_device",
        },
        "required_true_fields": [
            "resident_registration.triangle_descriptor_fit_batch",
            "resident_registration.triangle_descriptor_fit_reference_device_reuse",
            "resident_registration.triangle_descriptor_fit_moving_device_reuse",
            "resident_registration.triangle_descriptor_fit_output_device_reuse",
            "resident_registration.triangle_pixel_refine_batch",
            "resident_registration.triangle_warp_batch",
        ],
        "required_positive_fields": [
            "resident_registration.triangle_descriptor_fit_reference_device_bytes",
            "resident_registration.triangle_descriptor_fit_moving_device_bytes",
            "resident_registration.triangle_descriptor_fit_output_device_bytes",
            "resident_registration.triangle_pixel_refine_workspace_bytes",
            "artifact.resident_warp_scratch_bytes",
            "resident_io_pipeline.warp_scratch_bytes",
        ],
        "required_min_fields": {
            "resident_registration.triangle_warp_batch_frame_count": 1,
        },
        "required_component_seconds": [
            "triangle_descriptor_fit_batch",
            "triangle_pixel_refine_batch",
        ],
    }
    write_json(path, payload)


def _write_resident_registration_fastpath_artifact(
    run: Path,
    *,
    descriptor_batch: bool = True,
) -> None:
    write_json(
        run / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "resident_warp_scratch_bytes": 4096,
                    "resident_warp_copy_mode": "default_stream_async_device_to_device",
                    "resident_io_pipeline": {
                        "warp_scratch_bytes": 4096,
                        "warp_copy_mode": "default_stream_async_device_to_device",
                    },
                    "resident_registration": {
                        "mode": "similarity_cuda_triangle",
                        "triangle_descriptor_fit_batch": descriptor_batch,
                        "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                        "triangle_descriptor_fit_reference_device_reuse": True,
                        "triangle_descriptor_fit_reference_device_bytes": 128,
                        "triangle_descriptor_fit_moving_device_reuse": True,
                        "triangle_descriptor_fit_moving_device_bytes": 256,
                        "triangle_descriptor_fit_output_device_reuse": True,
                        "triangle_descriptor_fit_output_device_bytes": 512,
                        "triangle_pixel_refine_batch": True,
                        "triangle_pixel_refine_batch_mode": "native_batch_one_seed_per_frame",
                        "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                        "triangle_pixel_refine_workspace_bytes": 1024,
                        "triangle_warp_batch": True,
                        "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                        "triangle_warp_batch_frame_count": 3,
                    },
                    "fine_timing": {
                        "registration_component_seconds": {
                            "triangle_descriptor_fit_batch": 0.1,
                            "triangle_pixel_refine_batch": 0.2,
                        }
                    },
                }
            ]
        },
    )


def _add_dq_contract(path: Path) -> None:
    payload = read_json(path)
    payload["dq_provenance"] = resident_dq_provenance_contract(
        min_active_frame_count=190,
        dq_map_verify_tile_size=2,
        count_map_verify_tile_size=2,
    )
    write_json(path, payload)


def _add_frame_accounting_contract(path: Path, *, active: int = 193, zero: int = 7) -> None:
    payload = read_json(path)
    payload["frame_accounting"] = {
        "required": True,
        "required_input_light_frames": active + zero,
        "required_integrated_frames": active,
        "required_zero_weight_frames": zero,
        "required_registration_accepted_frames": active,
        "min_integrated_frames": 190,
        "required_integration_source_stage": "resident_calibrated_stack",
        "required_final_status_counts": {
            "integrated": active,
            "zero_weight": zero,
        },
        "match_integration_frame_weights": True,
        "match_speedup_summary": True,
        "match_dq_active_frame_count": True,
        "match_registration_accepted_frames": True,
    }
    write_json(path, payload)


def _add_pipeline_contract_requirement(path: Path) -> None:
    payload = read_json(path)
    payload["pipeline_contract"] = {
        "required": True,
        "required_audit_type": "pipeline_invariant_contract",
        "require_passed": True,
        "min_check_count": 1,
        "required_check_names": [
            "calibration_master_surface_contract",
            "resident_calibrated_light_contract",
            "resident_calibrated_light_dq_contract",
            "resident_source_dq_integration_effect_contract",
            "integration_default_engine_policy",
            "stack_engine_runtime_default_path",
            "integration_resident_result_contract",
        ],
        "allow_failed_checks": False,
    }
    write_json(path, payload)


def _add_stack_engine_default_promotion_requirement(path: Path) -> None:
    payload = read_json(path)
    payload["stack_engine_default_promotion"] = {
        "required": True,
        "required_audit_type": "stack_engine_default_contract",
        "require_passed": True,
        "require_default_promotion_ready": True,
        "required_scope": "all",
        "required_recommendation": "stack_engine_default_ready",
        "max_default_gap_count": 0,
        "max_blocker_count": 0,
        "allow_failed_checks": False,
    }
    write_json(path, payload)


def _add_warp_quality_contract_requirement(path: Path) -> None:
    payload = read_json(path)
    payload["warp_quality_contract"] = {
        "required": True,
        "required_artifact_type": "warp_quality_contract",
        "required_contract_surface": "resident_in_vram",
        "require_passed": True,
        "min_check_count": 7,
        "min_output_count": 2,
        "required_check_names": [
            "resident_warp_surface_present",
            "resident_warp_outputs_present",
            "resident_warp_frame_masks_close",
            "resident_warp_geometric_coverage_closes",
            "resident_warp_valid_fraction_meets_threshold",
            "resident_warp_skipped_frames_within_threshold",
            "resident_all_accepted_registration_frames_warped",
        ],
        "allow_failed_checks": False,
    }
    write_json(path, payload)


def _write_resident_determinism(
    path: Path,
    *,
    strict_passed: bool = False,
    relative_rms: float = 0.011916,
    rms: float = 3.751400,
    mean_abs: float = 0.642260,
) -> None:
    write_json(
        path,
        {
            "audit_type": "resident_triangle_determinism",
            "summary": {
                "passed": strict_passed,
                "output_difference_count": 1,
                "output_numerical_drift_count": 1,
                "output_numerical_drift_max_relative_rms": relative_rms,
            },
            "timing": {"candidate_over_baseline_ratio": 0.95},
            "output_numerical_drifts": [
                {
                    "key": "H:200:F000061:F000260",
                    "field": "master_path",
                    "drift": {
                        "available": True,
                        "joint_finite_pixels": 61651200,
                        "mean_abs": mean_abs,
                        "rms": rms,
                        "p99_abs": 3.408920,
                        "relative_rms_to_baseline_std": relative_rms,
                    },
                }
            ],
        },
    )


def _runtime_default_state(
    *,
    passed: bool = True,
    legacy_master: bool = False,
    failed_output: bool = False,
) -> dict:
    failed_masters = []
    if legacy_master:
        failed_masters = [
            {
                "name": "bias_legacy",
                "type": "bias",
                "tile_stack_mode": "legacy_streaming_accumulator",
                "path_exists": True,
                "stack_engine_enabled": False,
                "contract_ok": True,
                "status": "failed",
                "failures": [
                    "master_stack_engine_not_enabled",
                    "legacy_master_stack_mode",
                ],
            }
        ]
    failed_outputs = []
    if failed_output:
        failed_outputs = [
            {
                "item": "H",
                "backend": "cuda",
                "memory_mode": None,
                "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                "status": "implicit_cuda_fast_path",
                "passed": False,
                "required": True,
                "failures": [
                    "integration_engine_policy_failed",
                    "unsupported_integration_runtime_status",
                ],
            }
        ]
    ok = passed and not failed_masters and not failed_outputs
    return {
        "passed": ok,
        "status": "passed" if ok else "failed",
        "master_required": True,
        "master_count": 1,
        "master_stack_engine_count": 0 if legacy_master else 1,
        "master_resident_count": 0,
        "legacy_master_count": 1 if legacy_master else 0,
        "integration_required": True,
        "integration_output_count": 1,
        "integration_stack_engine_default_count": 0,
        "integration_resident_count": 0 if failed_output else 1,
        "explicit_cuda_fast_path_count": 0,
        "failed_masters": failed_masters,
        "failed_outputs": failed_outputs,
        "masters": failed_masters
        or [
            {
                "name": "master_bias",
                "type": "bias",
                "tile_stack_mode": "stack_engine_cpu",
                "path_exists": True,
                "stack_engine_enabled": True,
                "contract_ok": True,
                "status": "passed",
                "failures": [],
            }
        ],
        "outputs": failed_outputs
        or [
            {
                "item": "H",
                "backend": "cuda_resident_stack",
                "memory_mode": "resident",
                "tile_stack_mode": None,
                "status": "resident_not_required",
                "passed": True,
                "required": False,
                "failures": [],
            }
        ],
        "stack_result_contract_failures": [],
        "resident_result_contract_failures": [],
    }


def _runtime_default_check(
    *,
    passed: bool = True,
    legacy_master: bool = False,
    failed_output: bool = False,
) -> dict:
    state = _runtime_default_state(
        passed=passed,
        legacy_master=legacy_master,
        failed_output=failed_output,
    )
    return {
        "name": "stack_engine_runtime_default_path",
        "passed": state["passed"],
        "evidence": {
            "master_count": state["master_count"],
            "master_stack_engine_count": state["master_stack_engine_count"],
            "master_resident_count": state["master_resident_count"],
            "legacy_master_count": state["legacy_master_count"],
            "integration_output_count": state["integration_output_count"],
            "integration_stack_engine_default_count": state[
                "integration_stack_engine_default_count"
            ],
            "integration_resident_count": state["integration_resident_count"],
            "explicit_cuda_fast_path_count": state["explicit_cuda_fast_path_count"],
            "failed_masters": state["failed_masters"],
            "failed_outputs": state["failed_outputs"],
        },
        "note": "fixture runtime-default guard",
    }


def _write_pipeline_contract(
    path: Path,
    *,
    passed: bool = True,
    include_resident_calibrated_dq: bool = True,
    include_source_dq_effect: bool = True,
) -> None:
    runtime_default = _runtime_default_state(passed=passed, legacy_master=not passed)
    checks = [
        {
            "name": "calibration_master_surface_contract",
            "passed": passed,
            "evidence": {"master_count": 1, "failed": [] if passed else ["resident_calibration_H"]},
            "note": "",
        },
        {
            "name": "resident_calibrated_light_contract",
            "passed": passed,
            "evidence": {"light_count": 3, "failed": [] if passed else ["light_001"]},
            "note": "",
        },
        *(
            [
                {
                    "name": "resident_calibrated_light_dq_contract",
                    "passed": passed,
                    "evidence": {
                        "light_count": 3,
                        "source_dq_status": "passed" if passed else "failed",
                        "source_dq_passed": passed,
                        "contract_sources": ["resident_source_dq_execution"] if passed else [],
                        "failed": [] if passed else ["light_001"],
                    },
                    "note": "",
                }
            ]
            if include_resident_calibrated_dq
            else []
        ),
        *(
            [
                {
                    "name": "resident_source_dq_integration_effect_contract",
                    "passed": passed,
                    "evidence": {
                        "exists": True,
                        "required": True,
                        "status": "passed" if passed else "source_dq_not_reflected_in_integration",
                        "expected_applied_invalid_samples": 2,
                        "observed_integration_invalid_samples": 2 if passed else 0,
                    },
                    "note": "",
                }
            ]
            if include_source_dq_effect
            else []
        ),
        {
            "name": "integration_resident_result_contract",
            "passed": passed,
            "evidence": {"required_count": 1, "failed": [] if passed else ["H"]},
            "note": "",
        },
        {
            "name": "integration_default_engine_policy",
            "passed": True,
            "evidence": {
                "output_count": 1,
                "non_resident_count": 0,
                "resident_count": 1,
                "top_level_present": False,
                "top_level_default_ok": False,
                "failed": [],
            },
            "note": "resident-only fixture",
        },
        _runtime_default_check(passed=passed, legacy_master=not passed),
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "checks": checks,
            "integration": {
                "engine_policy": {
                    "passed": True,
                    "top_level_present": False,
                    "top_level_default_ok": False,
                    "output_count": 1,
                    "non_resident_count": 0,
                    "resident_count": 1,
                    "failed": [],
                    "outputs": [
                        {
                            "item": "H",
                            "backend": "cuda_resident_stack",
                            "memory_mode": "resident",
                            "tile_stack_mode": None,
                            "required": False,
                            "passed": True,
                            "status": "resident_not_required",
                            "failures": [],
                        }
                    ],
                },
                "outputs": [
                    {
                        "item": "H",
                        "resident_result_contract": {
                            "required": True,
                            "present": True,
                            "passed": passed,
                            "status": "passed" if passed else "failed",
                        },
                    }
                ]
            },
            "stack_engine_runtime_default": runtime_default,
            "pixel_verification": {"enabled": False},
        },
    )


def _write_pipeline_contract_with_rejection_sample_drift(path: Path) -> None:
    checks = [
        {
            "name": "calibration_master_surface_contract",
            "passed": True,
            "evidence": {"master_count": 1, "failed": []},
            "note": "",
        },
        {
            "name": "resident_calibrated_light_contract",
            "passed": True,
            "evidence": {"light_count": 3, "failed": []},
            "note": "",
        },
        {
            "name": "integration_resident_result_contract",
            "passed": True,
            "evidence": {"required_count": 1, "failed": []},
            "note": "",
        },
        {
            "name": "integration_default_engine_policy",
            "passed": True,
            "evidence": {
                "output_count": 1,
                "non_resident_count": 0,
                "resident_count": 1,
                "top_level_present": False,
                "top_level_default_ok": False,
                "failed": [],
            },
            "note": "resident-only fixture",
        },
        _runtime_default_check(),
        {
            "name": "integration_rejection_sample_counts_match_maps",
            "passed": False,
            "evidence": {
                "verified_records": 1,
                "required_records": 1,
                "failed": [
                    {
                        "item": "H",
                        "status": "verified",
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
            "note": "fixture sample-count drift",
        },
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "failed",
            "passed": False,
            "checks": checks,
            "integration": {
                "engine_policy": {
                    "passed": True,
                    "top_level_present": False,
                    "top_level_default_ok": False,
                    "output_count": 1,
                    "non_resident_count": 0,
                    "resident_count": 1,
                    "failed": [],
                    "outputs": [
                        {
                            "item": "H",
                            "backend": "cuda_resident_stack",
                            "memory_mode": "resident",
                            "tile_stack_mode": None,
                            "required": False,
                            "passed": True,
                            "status": "resident_not_required",
                            "failures": [],
                        }
                    ],
                },
                "outputs": [
                    {
                        "item": "H",
                        "resident_result_contract": {
                            "required": True,
                            "present": True,
                            "passed": True,
                            "status": "passed",
                        },
                    }
                ]
            },
            "stack_engine_runtime_default": _runtime_default_state(),
            "pixel_verification": {
                "enabled": True,
                "integration_outputs": [
                    {
                        "item": "H",
                        "status": "verified",
                        "rejection_sample_accounting": {
                            "status": "verified",
                            "verified": True,
                            "ok": False,
                            "required": True,
                            "rejection": "winsorized_sigma",
                            "map_rejected_sample_sum": 7,
                            "source_counts": [
                                {
                                    "name": "dq_coverage_provenance.rejected_sample_count",
                                    "count": 6,
                                },
                                {
                                    "name": "dq_provenance_summary.rejected_samples",
                                    "count": 6,
                                },
                            ],
                            "source_matches": [
                                {
                                    "source": "dq_coverage_provenance.rejected_sample_count",
                                    "actual": 7,
                                    "summary": 6,
                                    "delta": 1,
                                    "passed": False,
                                },
                                {
                                    "source": "dq_provenance_summary.rejected_samples",
                                    "actual": 7,
                                    "summary": 6,
                                    "delta": 1,
                                    "passed": False,
                                },
                            ],
                            "semantics": (
                                "Low/high rejection count maps store rejected-sample counts; "
                                "DQ low/high flags store pixels touched by rejection."
                            ),
                        },
                    }
                ],
            },
        },
    )


def _write_pipeline_contract_with_sample_closure_drift(path: Path) -> None:
    checks = [
        {
            "name": "calibration_master_surface_contract",
            "passed": True,
            "evidence": {"master_count": 1, "failed": []},
            "note": "",
        },
        {
            "name": "resident_calibrated_light_contract",
            "passed": True,
            "evidence": {"light_count": 3, "failed": []},
            "note": "",
        },
        {
            "name": "integration_resident_result_contract",
            "passed": True,
            "evidence": {"required_count": 1, "failed": []},
            "note": "",
        },
        {
            "name": "integration_default_engine_policy",
            "passed": True,
            "evidence": {
                "output_count": 1,
                "non_resident_count": 0,
                "resident_count": 1,
                "top_level_present": False,
                "top_level_default_ok": False,
                "failed": [],
            },
            "note": "resident-only fixture",
        },
        _runtime_default_check(),
        {
            "name": "integration_sample_accounting_closure",
            "passed": False,
            "evidence": {
                "output_count": 1,
                "present_count": 1,
                "failed": [
                    {
                        "item": "H",
                        "status": "failed",
                        "input_valid_samples_before_rejection": 9,
                        "valid_samples_after_rejection": 6,
                        "rejected_samples": 2,
                    }
                ],
            },
            "note": "fixture sample-closure drift",
        },
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "failed",
            "passed": False,
            "checks": checks,
            "integration": {
                "engine_policy": {
                    "passed": True,
                    "top_level_present": False,
                    "top_level_default_ok": False,
                    "output_count": 1,
                    "non_resident_count": 0,
                    "resident_count": 1,
                    "failed": [],
                    "outputs": [
                        {
                            "item": "H",
                            "backend": "cuda_resident_stack",
                            "memory_mode": "resident",
                            "tile_stack_mode": None,
                            "required": False,
                            "passed": True,
                            "status": "resident_not_required",
                            "failures": [],
                        }
                    ],
                },
                "outputs": [
                    {
                        "item": "H",
                        "resident_result_contract": {
                            "required": True,
                            "present": True,
                            "passed": True,
                            "status": "passed",
                        },
                        "sample_accounting_closure": {
                            "present": True,
                            "required": True,
                            "status": "failed",
                            "passed": False,
                            "input_total_match": True,
                            "valid_rejection_match": False,
                            "input_samples": 12,
                            "input_valid_samples_before_rejection": 9,
                            "input_invalid_samples_before_rejection": 3,
                            "valid_samples_after_rejection": 6,
                            "rejected_samples": 2,
                            "semantics": (
                                "input valid samples before rejection must equal "
                                "valid samples after rejection plus rejected samples"
                            ),
                        },
                    }
                ]
            },
            "stack_engine_runtime_default": _runtime_default_state(),
            "pixel_verification": {"enabled": False},
        },
    )


def _write_pipeline_contract_with_engine_policy_drift(path: Path) -> None:
    checks = [
        {
            "name": "calibration_master_surface_contract",
            "passed": True,
            "evidence": {"master_count": 1, "failed": []},
            "note": "",
        },
        {
            "name": "resident_calibrated_light_contract",
            "passed": True,
            "evidence": {"light_count": 3, "failed": []},
            "note": "",
        },
        {
            "name": "integration_resident_result_contract",
            "passed": True,
            "evidence": {"required_count": 0, "failed": []},
            "note": "",
        },
        {
            "name": "integration_default_engine_policy",
            "passed": False,
            "evidence": {
                "output_count": 1,
                "non_resident_count": 1,
                "resident_count": 0,
                "top_level_present": True,
                "top_level_default_ok": True,
                "failed": [
                    {
                        "item": "H",
                        "status": "implicit_cuda_fast_path",
                        "backend": "cuda",
                        "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                        "failures": ["cuda_fast_path_not_explicit"],
                    }
                ],
            },
            "note": "fixture implicit non-resident CUDA fast path",
        },
        _runtime_default_check(passed=False, failed_output=True),
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "failed",
            "passed": False,
            "checks": checks,
            "integration": {
                "engine_policy": {
                    "passed": False,
                    "top_level_present": True,
                    "top_level_default_ok": True,
                    "output_count": 1,
                    "non_resident_count": 1,
                    "resident_count": 0,
                    "failed": [
                        {
                            "item": "H",
                            "status": "implicit_cuda_fast_path",
                            "backend": "cuda",
                            "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                            "failures": ["cuda_fast_path_not_explicit"],
                        }
                    ],
                    "outputs": [
                        {
                            "item": "H",
                            "backend": "cuda",
                            "memory_mode": None,
                            "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                            "required": True,
                            "passed": False,
                            "status": "implicit_cuda_fast_path",
                            "failures": ["cuda_fast_path_not_explicit"],
                        }
                    ],
                },
                "outputs": [
                    {
                        "item": "H",
                        "backend": "cuda",
                        "memory_mode": None,
                        "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                        "resident_result_contract": {
                            "required": False,
                            "present": False,
                            "passed": False,
                            "status": "not_required",
                        },
                    }
                ],
            },
            "stack_engine_runtime_default": _runtime_default_state(
                passed=False,
                failed_output=True,
            ),
            "pixel_verification": {"enabled": False},
        },
    )


def _write_stack_engine_contract(path: Path, *, passed: bool = True, ready: bool = True) -> None:
    blockers = [] if ready else [
        {
            "name": "phase2_stack_engine_default_gaps",
            "gap_count": 1,
        }
    ]
    checks = [
        {
            "name": "calibration_masters_use_stack_engine",
            "passed": passed,
            "evidence": {"master_count": 3, "failed": [] if passed else ["bias"]},
            "note": "",
        },
        {
            "name": "integration_outputs_use:any",
            "passed": passed,
            "evidence": {"output_count": 1, "failed": [] if passed else [0]},
            "note": "",
        },
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "stack_engine_default_contract",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "scope": "all",
            "expected_integration_engine": "any",
            "checks": checks,
            "adoption": {
                "target_engine": "stack_engine_cpu",
                "surface_count": 4,
                "stack_engine_surface_count": 4 if ready else 3,
                "cuda_resident_surface_count": 0 if ready else 1,
                "phase2_stack_engine_default_gap_count": 0 if ready else 1,
                "recommendation": "stack_engine_default_ready" if ready else "resident_cuda_surfaces_remain",
                "gap_surfaces": []
                if ready
                else [
                    {
                        "surface": "integration",
                        "item": "H",
                        "engine_family": "cuda_resident_stack",
                        "gap_reason": "resident_cuda_surface",
                    }
                ],
            },
            "default_promotion": {
                "ready": ready,
                "status": "ready" if ready else "blocked",
                "required_scope": "all",
                "actual_scope": "all",
                "surface_count": 4,
                "calibration_surface_count": 3,
                "integration_surface_count": 1,
                "phase2_stack_engine_default_gap_count": 0 if ready else 1,
                "recommendation": "stack_engine_default_ready" if ready else "resident_cuda_surfaces_remain",
                "blocker_count": len(blockers),
                "blockers": blockers,
            },
        },
    )


def _write_resident_contract(path: Path, *, artifact_type: str, passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": artifact_type,
            "audit_type": artifact_type,
            "status": "passed" if passed else "failed",
            "passed": passed,
            "output_count": 1,
            "checks": [
                {
                    "name": "fixture_resident_contract_check",
                    "passed": passed,
                    "evidence": {"fixture": True},
                    "note": "",
                }
            ],
            "outputs": [{"index": 0, "filter": "H", "status": "passed" if passed else "failed"}],
        },
    )


def _write_warp_quality_contract(path: Path, *, passed: bool = True) -> None:
    check_names = [
        "resident_warp_surface_present",
        "resident_warp_outputs_present",
        "resident_warp_skipped_rows_have_reasons",
        "resident_warp_frame_masks_close",
        "resident_warp_geometric_coverage_closes",
        "resident_warp_output_maps_ready",
        "resident_warp_valid_fraction_meets_threshold",
        "resident_warp_skipped_frames_within_threshold",
        "resident_all_accepted_registration_frames_warped",
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "warp_quality_contract",
            "contract_surface": "resident_in_vram",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "output_count": 2,
            "summary": {
                "output_count": 2,
                "skipped_count": 0 if passed else 1,
                "artifact_ready_count": 2 if passed else 1,
                "min_valid_fraction": 0.997 if passed else 0.72,
            },
            "checks": [
                {
                    "name": name,
                    "passed": passed,
                    "evidence": {"fixture": True, "output_count": 2},
                    "note": "",
                }
                for name in check_names
            ],
        },
    )


def _write_contract_bundle(
    path: Path,
    *,
    pipeline: Path,
    stack: Path,
    passed: bool = True,
    resident_calibration: Path | None = None,
    resident_result: Path | None = None,
    warp_quality: Path | None = None,
    resident_result_source: str | None = None,
    resident_native_calibration: dict | None = None,
) -> None:
    artifacts = {
        "pipeline_contract": str(pipeline),
        "stack_engine_contract": str(stack),
        "guardrails_summary": str(path.with_name("guardrails_summary.json")),
    }
    argument_map = {
        "pipeline_contract_json": str(pipeline),
        "stack_engine_contract_json": str(stack),
    }
    if resident_calibration is not None:
        artifacts["resident_calibration_contract"] = str(resident_calibration)
    if resident_result is not None:
        artifacts["resident_result_contract"] = str(resident_result)
    if warp_quality is not None:
        artifacts["warp_quality_contract"] = str(warp_quality)
        argument_map["warp_quality_contract_json"] = str(warp_quality)
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "glass_acceptance_contract_bundle",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "purpose": "acceptance_audit_contract_inputs",
            "artifacts": artifacts,
            "resident_calibration_contract_json": None
            if resident_calibration is None
            else str(resident_calibration),
            "resident_result_contract_json": None if resident_result is None else str(resident_result),
            "warp_quality_contract_json": None if warp_quality is None else str(warp_quality),
            "resident_calibration_contract_attached": resident_calibration is not None,
            "resident_result_contract_attached": resident_result is not None,
            "warp_quality_contract_attached": warp_quality is not None,
            "resident_result_contract_source": resident_result_source,
            "resident_native_calibration": resident_native_calibration or {},
            "acceptance_audit_argument_map": argument_map,
            "checks": [
                {"name": "pipeline_contract", "passed": passed, "status": "passed" if passed else "failed"},
                {"name": "stack_engine_contract", "passed": passed, "status": "passed" if passed else "failed"},
            ],
        },
    )


def test_acceptance_audit_passes_real_benchmark_thresholds(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
    )

    assert audit["passed"] is True
    assert audit["frame_type_counts"] == {"light": 200, "bias": 20, "dark": 20, "flat": 20}
    assert audit["speedup_summary"]["speedup_vs_wbpp"] == 10.0


def test_acceptance_audit_accepts_passing_pipeline_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["pipeline_contract_present"]["passed"] is True
    assert checks["pipeline_contract_passed"]["passed"] is True
    assert checks["pipeline_contract_integration_default_engine_policy"]["passed"] is True
    assert checks["pipeline_contract_stack_engine_runtime_default"]["passed"] is True
    assert audit["pipeline_contract"]["passed"] is True
    assert audit["pipeline_contract"]["check_count"] == 7
    assert audit["pipeline_contract"]["integration_default_engine_policy"] is True
    assert audit["pipeline_contract"]["integration_engine_policy"]["resident_count"] == 1
    assert audit["pipeline_contract"]["runtime_default"]["status"] == "passed"
    assert audit["pipeline_contract"]["runtime_default"]["legacy_master_count"] == 0


def test_acceptance_audit_summarizes_pipeline_runtime_default(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    evidence = audit["release_contract_evidence"]["pipeline_contract"]
    runtime_default = evidence["runtime_default"]

    assert audit["passed"] is True
    assert checks["pipeline_contract_stack_engine_runtime_default"]["passed"] is True
    assert evidence["stack_engine_runtime_default"] is True
    assert evidence["stack_engine_runtime_default_status"] == "passed"
    assert runtime_default["check_present"] is True
    assert runtime_default["check_passed"] is True
    assert runtime_default["master_count"] == 1
    assert runtime_default["legacy_master_count"] == 0
    assert runtime_default["integration_resident_count"] == 1

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "StackEngine Runtime Default Path" in text
    assert "Legacy master rows: 0" in text
    assert "Explicit CUDA fast paths: 0" in text


def test_acceptance_audit_blocks_pipeline_runtime_default_drift(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    payload = read_json(pipeline)
    payload["status"] = "failed"
    payload["passed"] = False
    for check in payload["checks"]:
        if check["name"] == "stack_engine_runtime_default_path":
            check["passed"] = False
            check["evidence"] = _runtime_default_check(
                passed=False,
                legacy_master=True,
            )["evidence"]
    payload["stack_engine_runtime_default"] = _runtime_default_state(
        passed=False,
        legacy_master=True,
    )
    write_json(pipeline, payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    evidence = audit["release_contract_evidence"]["pipeline_contract"]
    runtime_default = evidence["runtime_default"]

    assert audit["passed"] is False
    assert checks["pipeline_contract_stack_engine_runtime_default"]["passed"] is False
    assert evidence["stack_engine_runtime_default"] is False
    assert evidence["stack_engine_runtime_default_status"] == "failed"
    assert evidence["stack_engine_runtime_default_legacy_master_count"] == 1
    assert runtime_default["failed_master_count"] == 1
    assert runtime_default["failed_masters"][0]["name"] == "bias_legacy"

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Runtime-default master mismatch bias_legacy" in text
    assert "legacy_streaming_accumulator" in text


def test_acceptance_audit_summarizes_pipeline_rejection_sample_accounting(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract_with_rejection_sample_drift(pipeline)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    evidence = audit["release_contract_evidence"]["pipeline_contract"]
    accounting = evidence["rejection_sample_accounting"]
    top_level_accounting = audit["pipeline_contract"]["rejection_sample_accounting"]

    assert audit["passed"] is False
    assert evidence["status"] == "failed"
    assert accounting["status"] == "failed"
    assert accounting["check_present"] is True
    assert accounting["check_passed"] is False
    assert accounting["pixel_verification_enabled"] is True
    assert accounting["accounted_output_count"] == 1
    assert accounting["required_count"] == 1
    assert accounting["verified_count"] == 1
    assert accounting["failed_count"] == 1
    assert accounting["failed_items"][0]["item"] == "H"
    assert accounting["failed_items"][0]["map_rejected_sample_sum"] == 7
    assert accounting["failed_items"][0]["source_counts"][0] == {
        "name": "dq_coverage_provenance.rejected_sample_count",
        "count": 6,
    }
    assert accounting["failed_items"][0]["failed_matches"][0] == {
        "source": "dq_coverage_provenance.rejected_sample_count",
        "actual": 7,
        "summary": 6,
        "delta": 1,
    }
    assert top_level_accounting["failed_count"] == 1

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Rejection Sample Accounting" in text
    assert "Check passed: False" in text
    assert "map_rejected_sample_sum=7" in text
    assert "dq_coverage_provenance.rejected_sample_count=6" in text
    assert "actual=7 summary=6 delta=1" in text


def test_acceptance_audit_summarizes_pipeline_sample_accounting_closure(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract_with_sample_closure_drift(pipeline)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    evidence = audit["release_contract_evidence"]["pipeline_contract"]
    closure = evidence["sample_accounting_closure"]
    top_level_closure = audit["pipeline_contract"]["sample_accounting_closure"]

    assert audit["passed"] is False
    assert evidence["status"] == "failed"
    assert evidence["sample_accounting_closure_status"] == "failed"
    assert evidence["sample_accounting_closure_present_count"] == 1
    assert evidence["sample_accounting_closure_failed_count"] == 1
    assert evidence["integration_sample_accounting_closure"] is False
    assert closure["status"] == "failed"
    assert closure["check_present"] is True
    assert closure["check_passed"] is False
    assert closure["present_count"] == 1
    assert closure["failed_count"] == 1
    assert closure["failed_items"][0]["item"] == "H"
    assert closure["failed_items"][0]["input_valid_samples_before_rejection"] == 9
    assert closure["failed_items"][0]["valid_samples_after_rejection"] == 6
    assert closure["failed_items"][0]["rejected_samples"] == 2
    assert top_level_closure["failed_count"] == 1
    assert audit["pipeline_contract"]["sample_accounting_closure_status"] == "failed"

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Integration Sample Accounting Closure" in text
    assert "Check passed: False" in text
    assert "input_valid_samples_before_rejection=9" in text
    assert "valid_samples_after_rejection=6" in text
    assert "rejected_samples=2" in text


def test_acceptance_audit_summarizes_pipeline_engine_policy_drift(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract_with_engine_policy_drift(pipeline)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    evidence = audit["release_contract_evidence"]["pipeline_contract"]
    engine_policy = evidence["integration_engine_policy"]

    assert audit["passed"] is False
    assert checks["pipeline_contract_integration_default_engine_policy"]["passed"] is False
    assert checks["pipeline_contract_integration_default_engine_policy"]["evidence"]["failed_count"] == 1
    assert evidence["status"] == "failed"
    assert evidence["integration_default_engine_policy"] is False
    assert evidence["integration_engine_policy_status"] == "failed"
    assert evidence["integration_engine_policy_non_resident_count"] == 1
    assert evidence["integration_engine_policy_failed_count"] == 1
    assert engine_policy["failed_items"][0]["item"] == "H"
    assert engine_policy["failed_items"][0]["failures"] == ["cuda_fast_path_not_explicit"]
    assert audit["pipeline_contract"]["integration_engine_policy_status"] == "failed"

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Integration Engine Policy" in text
    assert "Check passed: False" in text
    assert "implicit_cuda_fast_path" in text
    assert "cuda_fast_path_not_explicit" in text


def test_acceptance_audit_accepts_contract_bundle(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    _write_contract_bundle(bundle, pipeline=pipeline, stack=stack)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["contract_bundle"]["artifact_type"] == "glass_acceptance_contract_bundle"
    assert audit["contract_bundle"]["pipeline_contract_json"] == str(pipeline)
    assert audit["contract_bundle"]["stack_engine_contract_json"] == str(stack)
    assert audit["contract_bundle_schema"]["status"] == "passed"
    assert checks["contract_bundle_schema_version"]["passed"] is True
    assert checks["contract_bundle_purpose"]["passed"] is True
    assert checks["contract_bundle_required_artifacts"]["passed"] is True
    assert checks["contract_bundle_argument_map"]["passed"] is True
    assert audit["pipeline_contract"]["path"] == str(pipeline)
    assert audit["stack_engine_contract"]["path"] == str(stack)
    assert checks["pipeline_contract_passed"]["passed"] is True
    assert checks["stack_engine_contract_passed"]["passed"] is True


def test_acceptance_audit_enforces_resident_contract_bundle_attachments(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    resident_calibration = tmp_path / "resident_calibration_contract.json"
    resident_result = tmp_path / "resident_result_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    _write_resident_contract(
        resident_calibration,
        artifact_type="resident_cuda_calibration_contract",
        passed=True,
    )
    _write_resident_contract(
        resident_result,
        artifact_type="resident_cuda_result_contract",
        passed=True,
    )
    _write_contract_bundle(
        bundle,
        pipeline=pipeline,
        stack=stack,
        resident_calibration=resident_calibration,
        resident_result=resident_result,
    )

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["contract_bundle"]["resident_calibration_contract_json"] == str(resident_calibration)
    assert audit["contract_bundle"]["resident_result_contract_json"] == str(resident_result)
    assert audit["resident_contracts"]["calibration"]["path"] == str(resident_calibration)
    assert audit["resident_contracts"]["result"]["path"] == str(resident_result)
    assert checks["resident_calibration_contract_present"]["passed"] is True
    assert checks["resident_calibration_contract_type"]["passed"] is True
    assert checks["resident_calibration_contract_passed"]["passed"] is True
    assert checks["resident_result_contract_present"]["passed"] is True
    assert checks["resident_result_contract_type"]["passed"] is True
    assert checks["resident_result_contract_passed"]["passed"] is True


def test_acceptance_audit_enforces_warp_quality_contract_attachment(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    warp_quality = tmp_path / "warp_quality_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    _write_warp_quality_contract(warp_quality, passed=True)
    _write_contract_bundle(
        bundle,
        pipeline=pipeline,
        stack=stack,
        warp_quality=warp_quality,
    )

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
        require_warp_quality_contract=True,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["contract_bundle"]["warp_quality_contract_json"] == str(warp_quality)
    assert audit["contract_bundle"]["warp_quality_contract_attached"] is True
    assert audit["warp_quality_contract"]["path"] == str(warp_quality)
    assert audit["warp_quality_contract"]["passed"] is True
    assert checks["warp_quality_contract_present"]["passed"] is True
    assert checks["warp_quality_contract_type"]["passed"] is True
    assert checks["warp_quality_contract_passed"]["passed"] is True

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Warp Quality Contract" in text
    assert "Warp quality contract: passed" in text


def test_acceptance_audit_fails_when_required_warp_quality_contract_missing(
    tmp_path: Path,
):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        require_warp_quality_contract=True,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["warp_quality_contract"]["exists"] is False
    assert checks["warp_quality_contract_present"]["passed"] is False
    assert checks["warp_quality_contract_type"]["passed"] is False
    assert checks["warp_quality_contract_passed"]["passed"] is False


def test_acceptance_audit_fails_failed_warp_quality_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    warp_quality = tmp_path / "warp_quality_contract.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_warp_quality_contract(warp_quality, passed=False)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        warp_quality_contract_json=warp_quality,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["warp_quality_contract"]["path"] == str(warp_quality)
    assert audit["warp_quality_contract"]["passed"] is False
    assert checks["warp_quality_contract_present"]["passed"] is True
    assert checks["warp_quality_contract_type"]["passed"] is True
    assert checks["warp_quality_contract_passed"]["passed"] is False


def test_acceptance_audit_summarizes_native_guardrails_bundle_provenance(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    resident_result = tmp_path / "resident_result_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    _write_resident_contract(
        resident_result,
        artifact_type="resident_cuda_result_contract",
        passed=True,
    )
    _write_contract_bundle(
        bundle,
        pipeline=pipeline,
        stack=stack,
        resident_result=resident_result,
        resident_result_source="run_default",
        resident_native_calibration={
            "artifact_present": True,
            "master_count": 3,
            "resident_calibrated_light_count": 200,
        },
    )

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
    )

    native_bundle = audit["native_guardrails_bundle"]
    assert native_bundle["status"] == "present"
    assert native_bundle["resident_result_contract_source"] == "run_default"
    assert native_bundle["resident_result_contract_run_default"] is True
    assert native_bundle["resident_result_contract_json"] == str(resident_result)
    assert native_bundle["resident_native_calibration_artifact"] is True
    assert native_bundle["resident_calibration_master_count"] == 3
    assert native_bundle["resident_calibrated_light_count"] == 200
    markdown = tmp_path / "audit.md"
    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Native Guardrails Bundle Provenance" in text
    assert "Resident result contract source: run_default" in text
    assert "Resident calibrated light count: 200" in text


def test_acceptance_audit_fails_failed_resident_contract_bundle_attachment(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    resident_calibration = tmp_path / "resident_calibration_contract.json"
    resident_result = tmp_path / "resident_result_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    _write_resident_contract(
        resident_calibration,
        artifact_type="resident_cuda_calibration_contract",
        passed=True,
    )
    _write_resident_contract(
        resident_result,
        artifact_type="resident_cuda_result_contract",
        passed=False,
    )
    _write_contract_bundle(
        bundle,
        pipeline=pipeline,
        stack=stack,
        resident_calibration=resident_calibration,
        resident_result=resident_result,
    )

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["resident_contracts"]["result"]["passed"] is False
    assert checks["resident_result_contract_present"]["passed"] is True
    assert checks["resident_result_contract_type"]["passed"] is True
    assert checks["resident_result_contract_passed"]["passed"] is False


def test_acceptance_audit_explicit_contract_paths_override_bundle(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    bundle_pipeline = tmp_path / "bundle_pipeline_contract.json"
    bundle_stack = tmp_path / "bundle_stack_engine_contract.json"
    explicit_pipeline = tmp_path / "explicit_pipeline_contract.json"
    explicit_stack = tmp_path / "explicit_stack_engine_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(bundle_pipeline, passed=False)
    _write_stack_engine_contract(bundle_stack, passed=False, ready=False)
    _write_pipeline_contract(explicit_pipeline, passed=True)
    _write_stack_engine_contract(explicit_stack, passed=True, ready=True)
    _write_contract_bundle(bundle, pipeline=bundle_pipeline, stack=bundle_stack, passed=False)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
        pipeline_contract_json=explicit_pipeline,
        stack_engine_contract_json=explicit_stack,
    )

    assert audit["passed"] is True
    assert audit["contract_bundle"]["explicit_pipeline_contract_overrode_bundle"] is True
    assert audit["contract_bundle"]["explicit_stack_engine_contract_overrode_bundle"] is True
    assert audit["contract_bundle"]["pipeline_contract_json"] == str(explicit_pipeline)
    assert audit["contract_bundle"]["stack_engine_contract_json"] == str(explicit_stack)
    assert audit["pipeline_contract"]["path"] == str(explicit_pipeline)
    assert audit["stack_engine_contract"]["path"] == str(explicit_stack)


def test_acceptance_audit_fails_malformed_contract_bundle_schema_even_with_explicit_paths(
    tmp_path: Path,
):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    write_json(
        bundle,
        {
            "schema_version": 2,
            "artifact_type": "glass_acceptance_contract_bundle",
            "status": "passed",
            "passed": True,
            "purpose": "wrong_purpose",
            "artifacts": {"pipeline_contract": str(pipeline)},
            "acceptance_audit_argument_map": {"pipeline_contract_json": str(pipeline)},
        },
    )

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=bundle,
        pipeline_contract_json=pipeline,
        stack_engine_contract_json=stack,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["contract_bundle_schema"]["status"] == "failed"
    assert checks["contract_bundle_schema_version"]["passed"] is False
    assert checks["contract_bundle_purpose"]["passed"] is False
    assert checks["contract_bundle_required_artifacts"]["passed"] is False
    assert checks["contract_bundle_argument_map"]["passed"] is False
    assert checks["pipeline_contract_passed"]["passed"] is True
    assert checks["stack_engine_contract_passed"]["passed"] is True


def test_acceptance_audit_fails_missing_contract_bundle(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    missing_bundle = tmp_path / "missing_acceptance_contract_bundle.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        contract_bundle_json=missing_bundle,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["contract_bundle"]["exists"] is False
    assert checks["contract_bundle_present"]["passed"] is False
    assert checks["contract_bundle_type"]["passed"] is False


def test_acceptance_audit_fails_failed_pipeline_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "pipeline_contract.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_pipeline_contract(pipeline, passed=False)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["pipeline_contract_present"]["passed"] is True
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert audit["pipeline_contract"]["failed_checks"] == [
        "calibration_master_surface_contract",
        "resident_calibrated_light_contract",
        "resident_calibrated_light_dq_contract",
        "resident_source_dq_integration_effect_contract",
        "integration_resident_result_contract",
        "stack_engine_runtime_default_path",
    ]


def test_acceptance_audit_fails_missing_pipeline_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    pipeline = tmp_path / "missing_pipeline_contract.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["pipeline_contract_present"]["passed"] is False
    assert checks["pipeline_contract_present"]["evidence"]["exists"] is False
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert audit["pipeline_contract"]["check_count"] == 0


def test_acceptance_audit_applies_benchmark_pipeline_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    pipeline = tmp_path / "pipeline_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_pipeline_contract_requirement(contract)
    _write_pipeline_contract(pipeline, passed=True)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["contract_pipeline_contract_present"] is True
    assert checks["contract_pipeline_contract_audit_type"] is True
    assert checks["contract_pipeline_contract_passed"] is True
    assert checks["contract_pipeline_contract_min_check_count"] is True
    assert checks["contract_pipeline_contract_check:calibration_master_surface_contract"] is True
    assert checks["contract_pipeline_contract_check:resident_calibrated_light_contract"] is True
    assert checks["contract_pipeline_contract_check:resident_calibrated_light_dq_contract"] is True
    assert checks["contract_pipeline_contract_check:resident_source_dq_integration_effect_contract"] is True
    assert checks["contract_pipeline_contract_check:integration_default_engine_policy"] is True
    assert checks["contract_pipeline_contract_check:integration_resident_result_contract"] is True
    assert checks["contract_pipeline_contract_no_failed_checks"] is True
    pipeline_evidence = audit["release_contract_evidence"]["pipeline_contract"]
    assert pipeline_evidence["status"] == "passed"
    assert pipeline_evidence["required_by_benchmark_contract"] is True
    assert pipeline_evidence["pipeline_contract_passed"] is True
    assert pipeline_evidence["pipeline_contract_check_count"] == 7
    assert pipeline_evidence["benchmark_check_count"] == 12
    assert pipeline_evidence["failed_check_count"] == 0
    assert {item["name"] for item in pipeline_evidence["checks"]} >= {
        "pipeline_contract_present",
        "pipeline_contract_passed",
        "pipeline_contract_integration_default_engine_policy",
        "contract_pipeline_contract_present",
        "contract_pipeline_contract_passed",
        "contract_pipeline_contract_check:calibration_master_surface_contract",
        "contract_pipeline_contract_check:resident_calibrated_light_contract",
        "contract_pipeline_contract_check:resident_calibrated_light_dq_contract",
        "contract_pipeline_contract_check:resident_source_dq_integration_effect_contract",
        "contract_pipeline_contract_check:integration_default_engine_policy",
        "contract_pipeline_contract_check:stack_engine_runtime_default_path",
        "contract_pipeline_contract_check:integration_resident_result_contract",
    }


def test_acceptance_audit_benchmark_pipeline_contract_requires_resident_calibrated_light_dq(
    tmp_path: Path,
):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    pipeline = tmp_path / "pipeline_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_pipeline_contract_requirement(contract)
    _write_pipeline_contract(pipeline, passed=True, include_resident_calibrated_dq=False)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    missing = checks[
        "contract_pipeline_contract_check:resident_calibrated_light_dq_contract"
    ]
    assert missing["passed"] is False
    assert missing["evidence"]["required"] == "resident_calibrated_light_dq_contract"
    assert "resident_calibrated_light_contract" in missing["evidence"]["available"]


def test_acceptance_audit_benchmark_pipeline_contract_requires_source_dq_effect(
    tmp_path: Path,
):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    pipeline = tmp_path / "pipeline_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_pipeline_contract_requirement(contract)
    _write_pipeline_contract(pipeline, passed=True, include_source_dq_effect=False)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        pipeline_contract_json=pipeline,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    missing = checks[
        "contract_pipeline_contract_check:resident_source_dq_integration_effect_contract"
    ]
    assert missing["passed"] is False
    assert missing["evidence"]["required"] == "resident_source_dq_integration_effect_contract"
    assert "resident_calibrated_light_dq_contract" in missing["evidence"]["available"]


def test_acceptance_audit_benchmark_pipeline_contract_requires_artifact(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_pipeline_contract_requirement(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["pipeline_contract"] is None
    assert checks["contract_pipeline_contract_present"] is False
    assert checks["contract_pipeline_contract_passed"] is False
    assert checks["contract_pipeline_contract_check:integration_default_engine_policy"] is False
    assert checks["contract_pipeline_contract_check:stack_engine_runtime_default_path"] is False
    assert checks["contract_pipeline_contract_check:integration_resident_result_contract"] is False
    pipeline_evidence = audit["release_contract_evidence"]["pipeline_contract"]
    assert pipeline_evidence["status"] == "failed"
    assert pipeline_evidence["required_by_benchmark_contract"] is True
    assert pipeline_evidence["pipeline_contract_passed"] is None
    assert pipeline_evidence["failed_check_count"] >= 1


def test_acceptance_audit_applies_benchmark_stack_engine_default_promotion(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    stack_contract = tmp_path / "stack_engine_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_stack_engine_default_promotion_requirement(contract)
    _write_stack_engine_contract(stack_contract, passed=True, ready=True)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        stack_engine_contract_json=stack_contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["stack_engine_contract_present"] is True
    assert checks["stack_engine_contract_passed"] is True
    assert checks["contract_stack_engine_default_promotion_present"] is True
    assert checks["contract_stack_engine_default_promotion_contract_passed"] is True
    assert checks["contract_stack_engine_default_promotion_ready"] is True
    assert checks["contract_stack_engine_default_promotion_gap_count"] is True
    evidence = audit["release_contract_evidence"]["stack_engine_default_promotion"]
    assert evidence["status"] == "passed"
    assert evidence["required_by_benchmark_contract"] is True
    assert evidence["stack_engine_contract_passed"] is True
    assert evidence["default_promotion_ready"] is True
    assert evidence["benchmark_check_count"] >= 6
    assert evidence["failed_check_count"] == 0


def test_acceptance_audit_benchmark_stack_engine_default_promotion_requires_artifact(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_stack_engine_default_promotion_requirement(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["stack_engine_contract"] is None
    assert checks["contract_stack_engine_default_promotion_present"] is False
    assert checks["contract_stack_engine_default_promotion_contract_passed"] is False
    assert checks["contract_stack_engine_default_promotion_ready"] is False
    evidence = audit["release_contract_evidence"]["stack_engine_default_promotion"]
    assert evidence["status"] == "failed"
    assert evidence["required_by_benchmark_contract"] is True
    assert evidence["stack_engine_contract_passed"] is None
    assert evidence["failed_check_count"] >= 1


def test_acceptance_audit_benchmark_stack_engine_default_promotion_blocks_not_ready(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    stack_contract = tmp_path / "stack_engine_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_stack_engine_default_promotion_requirement(contract)
    _write_stack_engine_contract(stack_contract, passed=True, ready=False)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        stack_engine_contract_json=stack_contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["stack_engine_contract_present"] is True
    assert checks["stack_engine_contract_passed"] is True
    assert checks["contract_stack_engine_default_promotion_contract_passed"] is True
    assert checks["contract_stack_engine_default_promotion_ready"] is False
    assert checks["contract_stack_engine_default_promotion_gap_count"] is False
    assert checks["contract_stack_engine_default_promotion_blocker_count"] is False
    evidence = audit["release_contract_evidence"]["stack_engine_default_promotion"]
    assert evidence["status"] == "failed"
    assert evidence["stack_engine_contract_passed"] is True
    assert evidence["default_promotion_ready"] is False
    assert "contract_stack_engine_default_promotion_ready" in evidence["failed_checks"]


def test_acceptance_audit_cli_writes_stack_engine_default_promotion_evidence(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    stack_contract = tmp_path / "stack_engine_contract.json"
    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_stack_engine_default_promotion_requirement(contract)
    _write_stack_engine_contract(stack_contract, passed=True, ready=True)

    result = main(
        [
            "acceptance-audit",
            "--manifest",
            str(manifest),
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp),
            "--compare-json",
            str(compare),
            "--benchmark-contract",
            str(contract),
            "--stack-engine-contract-json",
            str(stack_contract),
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-active-frames",
            "190",
        ]
    )

    assert result == 0
    payload = read_json(out_json)
    evidence = payload["release_contract_evidence"]["stack_engine_default_promotion"]
    assert evidence["status"] == "passed"
    markdown = out_md.read_text(encoding="utf-8")
    assert "StackEngine Default Promotion Evidence" in markdown
    assert "Required by benchmark contract: True" in markdown
    assert "PASS: contract_stack_engine_default_promotion_ready" in markdown
    assert "Default promotion ready: True" in markdown


def test_acceptance_audit_cli_writes_pipeline_contract_evidence(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    pipeline = tmp_path / "pipeline_contract.json"
    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_pipeline_contract_requirement(contract)
    _write_pipeline_contract(pipeline, passed=True)

    result = main(
        [
            "acceptance-audit",
            "--manifest",
            str(manifest),
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp),
            "--compare-json",
            str(compare),
            "--benchmark-contract",
            str(contract),
            "--pipeline-contract-json",
            str(pipeline),
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-active-frames",
            "190",
        ]
    )

    assert result == 0
    payload = read_json(out_json)
    evidence = payload["release_contract_evidence"]["pipeline_contract"]
    assert evidence["status"] == "passed"
    markdown = out_md.read_text(encoding="utf-8")
    assert "Pipeline Contract Evidence" in markdown
    assert "Required by benchmark contract: True" in markdown
    assert "PASS: contract_pipeline_contract_passed" in markdown
    assert "integration_resident_result_contract" in markdown
    assert "StackEngine Runtime Default Path" in markdown
    assert "stack_engine_runtime_default_path" in markdown


def test_acceptance_audit_cli_accepts_contract_bundle(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    pipeline = tmp_path / "pipeline_contract.json"
    stack = tmp_path / "stack_engine_contract.json"
    warp_quality = tmp_path / "warp_quality_contract.json"
    bundle = tmp_path / "acceptance_contract_bundle.json"
    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_pipeline_contract_requirement(contract)
    _add_stack_engine_default_promotion_requirement(contract)
    _write_pipeline_contract(pipeline, passed=True)
    _write_stack_engine_contract(stack, passed=True, ready=True)
    _write_warp_quality_contract(warp_quality, passed=True)
    _write_contract_bundle(bundle, pipeline=pipeline, stack=stack, warp_quality=warp_quality)

    result = main(
        [
            "acceptance-audit",
            "--manifest",
            str(manifest),
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp),
            "--compare-json",
            str(compare),
            "--benchmark-contract",
            str(contract),
            "--contract-bundle",
            str(bundle),
            "--require-warp-quality-contract",
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-active-frames",
            "190",
        ]
    )

    assert result == 0
    payload = read_json(out_json)
    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["contract_bundle"]["path"] == str(bundle)
    assert payload["pipeline_contract"]["path"] == str(pipeline)
    assert payload["stack_engine_contract"]["path"] == str(stack)
    assert payload["warp_quality_contract"]["path"] == str(warp_quality)
    assert checks["contract_pipeline_contract_passed"]["passed"] is True
    assert checks["contract_stack_engine_default_promotion_ready"]["passed"] is True
    assert checks["warp_quality_contract_passed"]["passed"] is True
    markdown = out_md.read_text(encoding="utf-8")
    assert "Contract bundle: passed" in markdown
    assert "Warp quality contract: passed" in markdown
    assert "PASS: contract_pipeline_contract_passed" in markdown
    assert "PASS: contract_stack_engine_default_promotion_ready" in markdown


def test_acceptance_audit_applies_benchmark_warp_quality_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    warp_quality = tmp_path / "warp_quality_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=30.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_warp_quality_contract_requirement(contract)
    _write_warp_quality_contract(warp_quality, passed=True)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        warp_quality_contract_json=warp_quality,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["warp_quality_contract_passed"]["passed"] is True
    assert checks["contract_warp_quality_contract_present"]["passed"] is True
    assert checks["contract_warp_quality_contract_surface"]["passed"] is True
    assert checks["contract_warp_quality_contract_min_output_count"]["passed"] is True
    assert checks["contract_warp_quality_contract_no_failed_checks"]["passed"] is True


def test_acceptance_audit_blocks_missing_benchmark_warp_quality_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=30.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_warp_quality_contract_requirement(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["warp_quality_contract_present"]["passed"] is False
    assert checks["contract_warp_quality_contract_present"]["passed"] is False
    assert checks["contract_warp_quality_contract_passed"]["passed"] is False


def test_acceptance_audit_applies_benchmark_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05 --resident-runtime-preset throughput-v1"
        ),
        resident_timing={
            "master_build_or_load": 11.0,
            "light_read_upload_calibrate": 16.0,
            "light_read_worker_cumulative": 92.0,
            "resident_registration_warp": 12.0,
            "output_write": 3.5,
        },
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["required_command_token_groups"] = [
        {
            "name": "resident_h2d_or_runtime_preset",
            "any_of": [
                "--resident-h2d-mode pinned_ring",
                "--resident-runtime-preset throughput-v1",
            ],
        }
    ]
    timing_baseline = contract_payload["timing_baseline"]
    timing_baseline["stages_s"]["light_read_decode_worker"] = 45.0
    timing_baseline["cumulative_stages"] = ["light_read_decode_worker"]
    timing_baseline["stage_aliases"] = {
        "light_read_decode_worker": "light_read_worker_cumulative",
    }
    timing_baseline["stage_notes"] = {
        "light_read_decode_worker": "Cumulative worker time is informational.",
    }
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["benchmark_contract"]["name"] == "fixture_contract"
    assert checks["contract_max_runtime_vs_release_baseline"] is True
    assert checks["contract_required_command_token:--flat-floor 0.05"] is True
    assert checks["contract_required_command_token_group:resident_h2d_or_runtime_preset"] is True
    assert checks["contract_compare_scale"] is True
    assert checks["contract_compare_min_coverage"] is True
    regression = audit["performance_regression"]
    assert regression["status"] == "regressed"
    assert regression["worst_regression"]["stage"] == "output_write"
    assert regression["regressed_count"] == 1
    guidance = audit["optimization_guidance"]
    assert guidance["primary_target"] == "io_upload_calibration_pipeline"
    targets = {item["target_id"]: item for item in guidance["targets"]}
    assert targets["io_upload_calibration_pipeline"]["current_s"] == 16.0
    assert targets["resident_registration_warp"]["current_s"] == 12.0
    assert targets["output_write_policy"]["status"] == "regressed"
    cumulative = {
        item["stage"]: item
        for item in regression["items"]
        if item["stage"] == "light_read_decode_worker"
    }["light_read_decode_worker"]
    assert cumulative["actual_key"] == "light_read_worker_cumulative"
    assert cumulative["status"] == "informational_cumulative"
    assert cumulative["timing_kind"] == "worker_cumulative"


def test_acceptance_audit_contract_can_pin_ln_on_post_rejection_coverage(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=8.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05 --resident-output-maps audit"
        ),
        resident_dq=True,
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare, coverage_fraction=0.91)
    compare_payload = read_json(compare)
    compare_payload["comparison_region"]["glass_coverage_map"] = str(gp_run / "coverage_map.fits")
    write_json(compare, compare_payload)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["comparison"]["min_coverage_fraction"] = 0.90
    contract_payload["comparison"]["coverage_fraction_semantics"] = "post_rejection_coverage_map_fraction"
    contract_payload["comparison"]["max_rms_diff"] = 0.01
    contract_payload["comparison"]["max_abs_diff_p99"] = 0.01
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["minimum_coverage_fraction"]["passed"] is True
    assert checks["minimum_coverage_fraction"]["evidence"]["required"] == 0.90
    assert checks["minimum_coverage_fraction"]["evidence"]["source"] == "benchmark_contract"
    assert checks["contract_min_coverage_fraction"]["passed"] is True
    assert checks["contract_min_coverage_fraction"]["evidence"]["semantics"] == (
        "post_rejection_coverage_map_fraction"
    )
    assert checks["contract_coverage_fraction_semantics"]["passed"] is True
    assert checks["contract_coverage_fraction_semantics"]["evidence"]["matched_record_count"] >= 1


def test_acceptance_audit_accepts_default_route_evidence_for_resident_tokens(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command="glass run --flat-floor 0.05",
        run_timing_extra={
            "backend": "cuda",
            "backend_requested": "auto",
            "memory_mode": "resident",
            "memory_mode_requested": "resident",
            "resident_runtime_preset_effective": {
                "preset": "throughput-v3-io",
                "source": "resident_cuda_default",
            },
            "execution_default_resolution": {
                "schema_version": 1,
                "requested_backend": "auto",
                "requested_memory_mode": "resident",
                "effective_backend": "cuda",
                "effective_memory_mode": "resident",
                "reason": "resident_cuda_default",
                "default_runtime_preset": "throughput-v3-io",
            },
        },
        resident_timing={
            "master_build_or_load": 11.0,
            "light_read_upload_calibrate": 16.0,
            "resident_registration_warp": 12.0,
            "output_write": 3.5,
        },
        resident_registration_mode="similarity_cuda_triangle",
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["required_command_tokens"].append("--backend cuda")
    contract_payload["required_command_token_groups"] = [
        {
            "name": "resident_h2d_or_runtime_preset",
            "any_of": [
                "--resident-h2d-mode pinned_ring",
                "--resident-runtime-preset throughput-v3-io",
            ],
        }
    ]
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    memory_check = checks["contract_required_command_token:--memory-mode resident"]
    backend_check = checks["contract_required_command_token:--backend cuda"]
    registration_check = checks[
        "contract_required_command_token:--resident-registration similarity_cuda_triangle"
    ]
    flat_floor_check = checks["contract_required_command_token:--flat-floor 0.05"]
    runtime_group_check = checks[
        "contract_required_command_token_group:resident_h2d_or_runtime_preset"
    ]
    assert memory_check["evidence"]["command_match"] is False
    assert memory_check["evidence"]["artifact_match"]["reason"] == "resident_cuda_default"
    assert backend_check["evidence"]["artifact_match"]["actual"] == "cuda"
    assert registration_check["evidence"]["artifact_match"]["field"] == "resident_registration.mode"
    assert flat_floor_check["evidence"]["command_match"] is True
    assert runtime_group_check["passed"] is True
    assert runtime_group_check["evidence"]["artifact_matches"][0]["actual"] == "throughput-v3-io"


def test_acceptance_audit_applies_resident_registration_fastpath_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    markdown = tmp_path / "audit.md"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=20.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_resident_registration_fastpath_artifact(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_contract(contract)
    _add_resident_registration_fastpath_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["resident_registration_fastpath"]["available"] is True
    assert audit["resident_registration_fastpath"]["resident_registration"]["triangle_descriptor_fit_batch"] is True
    assert checks["contract_resident_registration_fastpath_present"] is True
    assert (
        checks[
            "contract_resident_registration_fastpath_true:"
            "resident_registration.triangle_descriptor_fit_batch"
        ]
        is True
    )
    assert (
        checks[
            "contract_resident_registration_fastpath_positive:"
            "artifact.resident_warp_scratch_bytes"
        ]
        is True
    )
    evidence = audit["release_contract_evidence"]["resident_registration_fastpath"]
    assert evidence["status"] == "passed"
    assert evidence["required_by_benchmark_contract"] is True
    assert evidence["available"] is True
    assert evidence["mode"] == "similarity_cuda_triangle"
    assert evidence["triangle_warp_batch_frame_count"] == 3
    assert evidence["failed_check_count"] == 0
    assert evidence["passed_check_count"] > 0

    write_acceptance_audit_markdown(markdown, audit)
    text = markdown.read_text(encoding="utf-8")
    assert "Resident Registration Fast Path Evidence" in text
    assert "Status: passed" in text
    assert "Triangle warp batch frames: 3" in text


def test_acceptance_audit_uses_explicit_resident_registration_fastpath_json(
    tmp_path: Path,
):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    fastpath_run = tmp_path / "fastpath_source"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "benchmark_contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=20.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_registration_mode=None,
        frame_accounting=True,
    )
    fastpath_run.mkdir()
    _write_resident_registration_fastpath_artifact(fastpath_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_contract(contract)
    _add_resident_registration_fastpath_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        resident_registration_fastpath_json=fastpath_run / "resident_artifacts.json",
    )

    checks = {item["name"]: item for item in audit["checks"]}
    fastpath = audit["resident_registration_fastpath"]
    evidence = audit["release_contract_evidence"]["resident_registration_fastpath"]
    assert audit["passed"] is True
    assert fastpath["source"] == "explicit_resident_artifacts_json"
    assert fastpath["path"] == str(fastpath_run / "resident_artifacts.json")
    assert fastpath["available"] is True
    assert fastpath["resident_registration"]["triangle_descriptor_fit_batch"] is True
    assert checks["contract_resident_registration_fastpath_present"]["passed"] is True
    assert evidence["status"] == "passed"
    assert evidence["source"] == "explicit_resident_artifacts_json"
    assert evidence["path"] == str(fastpath_run / "resident_artifacts.json")
    assert (
        checks[
            "contract_resident_registration_fastpath_value:"
            "resident_registration.mode"
        ]["passed"]
        is True
    )


def test_acceptance_audit_blocks_resident_registration_fastpath_regression(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=20.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_resident_registration_fastpath_artifact(gp_run, descriptor_batch=False)
    _write_wbpp_result(wbpp)
    _write_compare(compare)
    _write_contract(contract)
    _add_resident_registration_fastpath_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    evidence = audit["release_contract_evidence"]["resident_registration_fastpath"]
    failed_check = checks[
        "contract_resident_registration_fastpath_true:"
        "resident_registration.triangle_descriptor_fit_batch"
    ]
    assert audit["passed"] is False
    assert evidence["status"] == "failed"
    assert evidence["failed_check_count"] == 1
    assert (
        "contract_resident_registration_fastpath_true:"
        "resident_registration.triangle_descriptor_fit_batch"
    ) in evidence["failed_checks"]
    assert failed_check["passed"] is False
    assert failed_check["evidence"]["actual"] is False


def test_acceptance_audit_accepts_io_runtime_preset_from_artifact(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=18.8,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_io_pipeline={
            "h2d_mode": "pinned_ring",
            "prefetch_frames": 32,
            "prefetch_workers": 16,
            "calibration_batch_requested_frames": 16,
            "calibration_batch_requested_streams": 4,
            "calibration_wave_requested_frames": 4,
            "calibration_release_mode_requested": "callback_queue",
            "calibration_release_mode_effective": "callback_queue",
        },
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["required_command_token_groups"] = [
        {
            "name": "resident_h2d_or_runtime_preset",
            "any_of": [
                "--resident-h2d-mode pinned_ring",
                "--resident-runtime-preset throughput-v3-io",
            ],
        }
    ]
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    check = {
        item["name"]: item
        for item in audit["checks"]
    }["contract_required_command_token_group:resident_h2d_or_runtime_preset"]
    assert audit["passed"] is True
    assert check["passed"] is True
    assert check["evidence"]["matched"] == []
    assert check["evidence"]["resident_io_pipeline_records"] == 1
    assert any(match.get("preset") == "throughput-v3-io" for match in check["evidence"]["artifact_matches"])


def test_acceptance_audit_accepts_fused_runtime_preset_from_artifact(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=18.8,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_io_pipeline={
            "h2d_mode": "pinned_ring",
            "prefetch_frames": 12,
            "prefetch_workers": 7,
            "calibration_batch_requested_frames": 8,
            "calibration_batch_requested_streams": 4,
            "calibration_wave_requested_frames": 2,
            "calibration_release_mode_requested": "callback_queue",
            "calibration_release_mode_effective": "callback_queue",
        },
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["required_command_token_groups"] = [
        {
            "name": "resident_fused_runtime_preset",
            "any_of": ["--resident-runtime-preset throughput-v2-fused"],
        }
    ]
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    check = {
        item["name"]: item
        for item in audit["checks"]
    }["contract_required_command_token_group:resident_fused_runtime_preset"]
    assert audit["passed"] is True
    assert check["passed"] is True
    assert check["evidence"]["matched"] == []
    assert check["evidence"]["resident_io_pipeline_records"] == 1
    assert any(
        match.get("preset") == "throughput-v2-fused" for match in check["evidence"]["artifact_matches"]
    )


def test_acceptance_audit_accepts_native_completion_runtime_preset_from_artifact(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=18.8,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_io_pipeline={
            "h2d_mode": "pinned_ring",
            "prefetch_frames": 32,
            "prefetch_workers": 16,
            "calibration_batch_requested_frames": 16,
            "calibration_batch_requested_streams": 4,
            "calibration_wave_requested_frames": 4,
            "calibration_release_mode_requested": "callback_queue",
            "calibration_release_mode_effective": "callback_queue",
            "native_completion_calibration_policy": "cli_enabled",
            "native_completion_calibration_requested": True,
            "native_completion_calibration_enabled": True,
            "native_completion_calibration_consumer_wave_fill_source": "cli",
            "native_completion_calibration_consumer_wave_fill_requested_wait_us": 25,
            "calibration_batch_mode": "fits_u16be_bzero_native_completion_calibration_batch",
        },
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["required_command_token_groups"] = [
        {
            "name": "resident_native_completion_runtime_preset",
            "any_of": ["--resident-runtime-preset throughput-v4-native-completion"],
        }
    ]
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    check = {
        item["name"]: item
        for item in audit["checks"]
    }["contract_required_command_token_group:resident_native_completion_runtime_preset"]
    assert audit["passed"] is True
    assert check["passed"] is True
    assert check["evidence"]["matched"] == []
    assert check["evidence"]["resident_io_pipeline_records"] == 1
    assert any(
        match.get("preset") == "throughput-v4-native-completion"
        for match in check["evidence"]["artifact_matches"]
    )


def test_acceptance_audit_applies_resident_drift_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    resident_det = tmp_path / "resident_determinism.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _write_resident_determinism(resident_det)
    contract_payload = read_json(contract)
    contract_payload["resident_determinism"] = {
        "required": True,
        "require_strict_passed": False,
        "max_output_numerical_drift_count": 1,
        "max_output_numerical_drift_relative_rms": 0.02,
        "max_output_numerical_drift_rms": 4.0,
        "max_output_numerical_drift_mean_abs": 1.0,
    }
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        resident_determinism_json=resident_det,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["contract_resident_determinism_present"] is True
    assert checks["contract_output_numerical_drift_count"] is True
    assert checks["contract_output_numerical_drift_relative_rms"] is True
    assert checks["contract_output_numerical_drift_rms"] is True
    assert checks["contract_output_numerical_drift_mean_abs"] is True


def test_acceptance_audit_resident_drift_contract_catches_excessive_drift(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    resident_det = tmp_path / "resident_determinism.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _write_resident_determinism(resident_det)
    contract_payload = read_json(contract)
    contract_payload["resident_determinism"] = {
        "required": True,
        "max_output_numerical_drift_count": 0,
        "max_output_numerical_drift_relative_rms": 0.005,
        "max_output_numerical_drift_rms": 1.0,
        "max_output_numerical_drift_mean_abs": 0.1,
    }
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
        resident_determinism_json=resident_det,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["contract_resident_determinism_present"]["passed"] is True
    assert checks["contract_output_numerical_drift_count"]["passed"] is False
    assert checks["contract_output_numerical_drift_relative_rms"]["passed"] is False
    assert checks["contract_output_numerical_drift_rms"]["passed"] is False
    assert checks["contract_output_numerical_drift_mean_abs"]["passed"] is False
    assert checks["contract_output_numerical_drift_relative_rms"]["evidence"]["actual_max"] == 0.011916


def test_acceptance_audit_applies_dq_provenance_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["dq_provenance"]["record_count"] == 2
    assert audit["dq_provenance"]["records"][0]["normalized_from_legacy"] is True
    assert checks["contract_dq_provenance_records"] is True
    assert checks["contract_dq_source_schema:resident_dq_coverage_provenance"] is True
    assert checks["contract_dq_engine:cuda_resident_stack"] is True
    assert checks["contract_dq_min_active_frame_count"] is True
    assert checks["contract_dq_map_exists"] is True
    assert checks["contract_dq_output_flag:warp_edge"] is True
    assert checks["contract_dq_positive_output_flag:warp_edge"] is True
    assert checks["contract_dq_map_pixel_verification"] is True
    assert checks["contract_dq_map_summary_match:valid"] is True
    assert checks["contract_dq_map_summary_match:warp_edge"] is True
    assert checks["contract_coverage_map_pixel_verification"] is True
    assert checks["contract_coverage_map_finite_pixels_match"] is True
    assert checks["contract_coverage_zero_pixels_match_no_data"] is True
    assert checks["contract_low_rejection_map_available_or_skipped"] is True
    assert checks["contract_low_rejection_map_positive_pixels_match:low_rejected"] is True
    assert checks["contract_high_rejection_map_positive_pixels_match:high_rejected"] is True
    assert checks["contract_rejection_map_sum_matches_provenance"] is True
    assert checks["contract_resident_artifact_map_path:master"] is True
    assert checks["contract_resident_artifact_map_path:low_rejection"] is True
    assert checks["contract_resident_artifact_map_path:high_rejection"] is True
    assert checks["contract_dq_source_term:geometric_warp_coverage"] is True
    verification = audit["dq_provenance"]["records"][0]["dq_map_pixel_verification"]
    assert verification["status"] == "verified"
    assert verification["result"]["counts"]["high_rejected"] == 2
    count_maps = audit["dq_provenance"]["records"][0]["output_count_map_verification"]
    assert count_maps["coverage"]["result"]["finite_pixels"] == 6
    assert count_maps["low_rejection"]["result"]["positive_pixels"] == 1
    assert count_maps["high_rejection"]["result"]["rounded_sum"] == 3


def test_acceptance_audit_applies_frame_accounting_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        zero=7,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
        frame_accounting=True,
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    _add_frame_accounting_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["frame_accounting"]["exists"] is True
    assert audit["frame_accounting"]["summary"]["integrated_frames"] == 193
    assert audit["frame_accounting"]["exception_summary"]["count"] == 7
    assert audit["frame_accounting"]["exception_frames"][0]["primary_reason"] == "integration weight is zero"
    assert audit["optimization_guidance"]["exception_context"]["count"] == 7
    assert audit["optimization_guidance"]["exception_context"]["dominant_stage"] == "integration"
    assert checks["contract_frame_accounting_present"] is True
    assert checks["contract_frame_accounting_input_light_frames"] is True
    assert checks["contract_frame_accounting_integrated_frames"] is True
    assert checks["contract_frame_accounting_zero_weight_frames"] is True
    assert checks["contract_frame_accounting_final_status:integrated"] is True
    assert checks["contract_frame_accounting_final_status:zero_weight"] is True
    assert checks["contract_frame_accounting_no_integration_conflicts"] is True
    assert checks["contract_frame_accounting_matches_integration_weights"] is True
    assert checks["contract_frame_accounting_matches_speedup_summary"] is True
    assert checks["contract_frame_accounting_matches_dq_active_frames"] is True
    assert checks["contract_frame_accounting_matches_registration"] is True


def test_acceptance_audit_accepts_zero_weight_as_orthogonal_integration_status(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        zero=7,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
        frame_accounting=True,
    )
    accounting = read_json(gp_run / "frame_accounting.json")
    accounting["summary"]["final_status_counts"] = {
        "integrated": 193,
        "quality_rejected": 7,
    }
    accounting["summary"]["integration_status_counts"] = {"used": 193, "zero_weight": 7}
    accounting["exception_summary"]["final_status_counts"] = {"quality_rejected": 7}
    accounting["exception_summary"]["primary_stage_counts"] = {"quality": 7}
    for frame in accounting["frames"]:
        if frame["integration_status"] == "zero_weight":
            frame["final_status"] = "quality_rejected"
    for frame in accounting["exception_frames"]:
        frame["final_status"] = "quality_rejected"
        frame["primary_stage"] = "quality"
        frame["primary_reason"] = "registration quality gate rejected frame"
    write_json(gp_run / "frame_accounting.json", accounting)
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    _add_frame_accounting_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    zero_weight_check = checks["contract_frame_accounting_final_status:zero_weight"]
    assert zero_weight_check["passed"] is True
    assert zero_weight_check["evidence"]["source"] == "integration_status"
    assert checks["contract_frame_accounting_matches_integration_weights"]["passed"] is True


def test_acceptance_audit_frame_accounting_contract_catches_integration_conflict(
    tmp_path: Path,
):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        zero=7,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
        frame_accounting=True,
    )
    accounting = read_json(gp_run / "frame_accounting.json")
    accounting["frames"][0]["final_status"] = "integration_conflict"
    accounting["frames"][0]["integration_conflict_count"] = 1
    accounting["frames"][0]["integration_conflicts"] = [
        {
            "stage": "registration",
            "status": "failed",
            "reason": "positive integration weight for non-accepted registration frame",
        }
    ]
    accounting["summary"]["integration_conflict_frames"] = 1
    write_json(gp_run / "frame_accounting.json", accounting)
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    _add_frame_accounting_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    no_conflict = checks["contract_frame_accounting_no_integration_conflicts"]
    assert audit["passed"] is False
    assert no_conflict["passed"] is False
    assert no_conflict["evidence"]["conflict_count"] == 1
    assert no_conflict["evidence"]["conflicts"][0]["frame_id"] == "L0000"


def test_acceptance_audit_frame_accounting_contract_catches_mismatch(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        zero=7,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
        frame_accounting=True,
    )
    accounting = read_json(gp_run / "frame_accounting.json")
    accounting["summary"]["integrated_frames"] = 192
    accounting["summary"]["final_status_counts"]["integrated"] = 192
    write_json(gp_run / "frame_accounting.json", accounting)
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    _add_frame_accounting_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["contract_frame_accounting_integrated_frames"] is False
    assert checks["contract_frame_accounting_final_status:integrated"] is False
    assert checks["contract_frame_accounting_matches_integration_weights"] is False
    assert checks["contract_frame_accounting_matches_speedup_summary"] is False
    assert checks["contract_frame_accounting_matches_dq_active_frames"] is False


def test_acceptance_audit_rejection_sum_uses_explicit_tolerance(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        active=193,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
        resident_dq=True,
    )
    for artifact_name, list_key in [
        ("integration_results.json", "outputs"),
        ("resident_artifacts.json", "artifacts"),
    ]:
        payload = read_json(gp_run / artifact_name)
        payload[list_key][0]["dq_coverage_provenance"]["rejected_sample_count"] = 3
        write_json(gp_run / artifact_name, payload)
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["dq_provenance"]["rejection_map_sum_tolerance_samples"] = 1
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item for item in audit["checks"]}
    rejection_sum = checks["contract_rejection_map_sum_matches_provenance"]
    assert audit["passed"] is True
    assert rejection_sum["passed"] is True
    assert rejection_sum["evidence"]["tolerance_samples"] == 1
    assert rejection_sum["evidence"]["matches"][0]["delta"] == 1


def test_acceptance_audit_dq_contract_fails_when_artifact_missing(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)
    _add_dq_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert audit["dq_provenance"]["record_count"] == 0
    assert checks["contract_dq_provenance_records"] is False
    assert checks["contract_dq_source_schema:resident_dq_coverage_provenance"] is False
    assert checks["contract_dq_map_path_present"] is False
    assert checks["contract_dq_map_pixel_verification"] is False
    assert checks["contract_coverage_map_pixel_verification"] is False
    assert checks["contract_low_rejection_map_available_or_skipped"] is False


def test_acceptance_audit_contract_catches_missing_parameters(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=42.0,
        command="glass run --memory-mode resident --resident-registration similarity_cuda_triangle",
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare, scale=1.0, min_coverage=99.0, coverage_fraction=0.5)
    _write_contract(contract)
    contract_payload = read_json(contract)
    contract_payload["required_command_token_groups"] = [
        {
            "name": "resident_h2d_or_runtime_preset",
            "any_of": [
                "--resident-h2d-mode pinned_ring",
                "--resident-runtime-preset throughput-v1",
            ],
        }
    ]
    write_json(contract, contract_payload)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["contract_max_runtime_vs_release_baseline"] is False
    assert checks["contract_required_command_token:--flat-floor 0.05"] is False
    assert checks["contract_required_command_token_group:resident_h2d_or_runtime_preset"] is False
    assert checks["contract_compare_scale"] is False
    assert checks["contract_compare_min_coverage"] is False
    assert checks["contract_min_coverage_fraction"] is False


def test_acceptance_audit_cli_writes_outputs_and_returns_failure(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    resident_det = tmp_path / "resident_determinism.json"
    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    _write_manifest(manifest, light=199)
    _write_glass_run(gp_run, elapsed_s=100.0)
    _write_wbpp_result(wbpp, elapsed_s=150.0)
    _write_compare(compare, rms=0.02)
    _write_resident_determinism(resident_det)

    result = main(
        [
            "acceptance-audit",
            "--manifest",
            str(manifest),
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp),
            "--compare-json",
            str(compare),
            "--resident-determinism-json",
            str(resident_det),
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-active-frames",
            "190",
        ]
    )

    assert result == 2
    payload = read_json(out_json)
    assert payload["passed"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["minimum_light_frames"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["minimum_speedup"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["maximum_rms_diff"] is False
    assert payload["resident_determinism"]["path"] == str(resident_det)
    assert payload["resident_determinism"]["strict_passed"] is False
    assert payload["resident_determinism"]["output_numerical_drift_count"] == 1
    assert payload["output_numerical_drifts"][0]["drift"]["rms"] == 3.751400
    assert "FAIL: minimum_light_frames" in out_md.read_text(encoding="utf-8")
    assert "Resident Determinism" in out_md.read_text(encoding="utf-8")
    assert "relative_rms=0.011916" in out_md.read_text(encoding="utf-8")
