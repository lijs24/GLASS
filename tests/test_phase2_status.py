from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.phase2_status import (
    build_phase2_status,
    build_phase2_status_compare,
    write_phase2_status_compare,
    write_phase2_status_markdown,
)


def _write_checkpoint(path: Path, *, gate: int, status: str = "green") -> Path:
    target = path / f"s2_gate_{gate}_status.md"
    target.write_text(
        "\n".join(
            [
                f"# S2-Gate {gate} Status",
                "",
                f"- Gate: S2-Gate {gate}",
                "- Scope: fixture checkpoint",
                f"- Status: {status}",
                "- Date: 2026-06-18",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return target


def _write_acceptance(
    path: Path,
    *,
    integration_engine_policy_passed: bool = True,
    runtime_default_passed: bool = True,
) -> None:
    engine_policy_status = "passed" if integration_engine_policy_passed else "failed"
    engine_policy_failed_items = [] if integration_engine_policy_passed else [
        {
            "item": "H",
            "status": "implicit_cuda_fast_path",
            "backend": "cuda",
            "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
            "failures": ["cuda_fast_path_not_explicit"],
        }
    ]
    runtime_default_status = "passed" if runtime_default_passed else "failed"
    runtime_default_failed_masters = [] if runtime_default_passed else [
        {
            "name": "bias_legacy",
            "type": "bias",
            "tile_stack_mode": "legacy_streaming_accumulator",
            "status": "failed",
            "failures": ["legacy_master_stack_mode"],
        }
    ]
    acceptance_passed = integration_engine_policy_passed and runtime_default_passed
    write_json(
        path,
        {
            "status": "passed" if acceptance_passed else "failed",
            "passed": acceptance_passed,
            "benchmark_contract": {"name": "fixture_contract"},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "contract_bundle_schema": {"status": "passed"},
            "native_guardrails_bundle": {
                "status": "present",
                "bundle_status": "passed",
                "resident_result_contract_source": "run_default",
                "resident_result_contract_run_default": True,
                "resident_result_contract_json": "C:/glass_runs/run/resident_result_contract.json",
                "resident_native_calibration_artifact": True,
                "resident_calibration_master_count": 3,
                "resident_calibrated_light_count": 200,
            },
            "resident_registration_fastpath": {
                "exists": True,
                "available": True,
                "artifact_count": 1,
                "path": "C:/glass_runs/run/resident_registration_fastpath.json",
                "resident_registration": {
                    "mode": "similarity_cuda_triangle",
                    "triangle_descriptor_fit_batch": True,
                    "triangle_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
                    "triangle_descriptor_fit_reference_device_reuse": True,
                    "triangle_descriptor_fit_moving_device_reuse": True,
                    "triangle_descriptor_fit_output_device_reuse": True,
                    "triangle_pixel_refine_batch": True,
                    "triangle_pixel_refine_batch_metric_mode": "flattened_frame_candidate_grid",
                    "triangle_warp_batch": True,
                    "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
                    "triangle_warp_batch_frame_count": 188,
                },
                "artifact": {
                    "resident_warp_copy_mode": "default_stream_async_device_to_device",
                    "resident_warp_scratch_bytes": 493209636,
                },
                "resident_io_pipeline": {
                    "warp_copy_mode": "default_stream_async_device_to_device",
                    "warp_scratch_bytes": 493209636,
                },
            },
            "resident_contracts": {
                "calibration": {"passed": True},
                "result": {"passed": True},
            },
            "release_contract_evidence": {
                "pipeline_contract": {
                    "status": "passed" if acceptance_passed else "failed",
                    "integration_default_engine_policy": integration_engine_policy_passed,
                    "integration_engine_policy_status": engine_policy_status,
                    "integration_engine_policy_non_resident_count": 0
                    if integration_engine_policy_passed
                    else 1,
                    "integration_engine_policy_failed_count": 0
                    if integration_engine_policy_passed
                    else 1,
                    "integration_engine_policy": {
                        "status": engine_policy_status,
                        "check_name": "integration_default_engine_policy",
                        "check_present": True,
                        "check_passed": integration_engine_policy_passed,
                        "output_count": 1,
                        "non_resident_count": 0 if integration_engine_policy_passed else 1,
                        "resident_count": 1 if integration_engine_policy_passed else 0,
                        "failed_count": 0 if integration_engine_policy_passed else 1,
                        "failed_items": engine_policy_failed_items,
                        "rows": [
                            {
                                "item": "H",
                                "backend": "cuda_resident_stack"
                                if integration_engine_policy_passed
                                else "cuda",
                                "memory_mode": "resident"
                                if integration_engine_policy_passed
                                else None,
                                "tile_stack_mode": None
                                if integration_engine_policy_passed
                                else "cuda_streaming_accumulator_fast_path",
                                "required": not integration_engine_policy_passed,
                                "passed": integration_engine_policy_passed,
                                "status": "resident_not_required"
                                if integration_engine_policy_passed
                                else "implicit_cuda_fast_path",
                                "failures": []
                                if integration_engine_policy_passed
                                else ["cuda_fast_path_not_explicit"],
                            }
                        ],
                    },
                    "stack_engine_runtime_default": runtime_default_passed,
                    "stack_engine_runtime_default_status": runtime_default_status,
                    "stack_engine_runtime_default_legacy_master_count": 0
                    if runtime_default_passed
                    else 1,
                    "stack_engine_runtime_default_failed_master_count": 0
                    if runtime_default_passed
                    else 1,
                    "stack_engine_runtime_default_failed_output_count": 0,
                    "runtime_default": {
                        "status": runtime_default_status,
                        "check_name": "stack_engine_runtime_default_path",
                        "check_present": True,
                        "check_passed": runtime_default_passed,
                        "master_count": 1,
                        "master_stack_engine_count": 1
                        if runtime_default_passed
                        else 0,
                        "master_resident_count": 0,
                        "legacy_master_count": 0 if runtime_default_passed else 1,
                        "integration_output_count": 1,
                        "integration_stack_engine_default_count": 0,
                        "integration_resident_count": 1,
                        "explicit_cuda_fast_path_count": 0,
                        "failed_master_count": 0 if runtime_default_passed else 1,
                        "failed_output_count": 0,
                        "failed_masters": runtime_default_failed_masters,
                        "failed_outputs": [],
                    },
                }
            },
            "checks": [
                {"name": "contract_resident_registration_fastpath_present", "passed": True},
                {
                    "name": "contract_resident_registration_fastpath_true:descriptor_batch",
                    "passed": True,
                },
            ],
            "speedup_summary": {
                "speedup_vs_wbpp": 58.0,
                "glass": {"weighted_frame_count": 193},
                "comparison": {
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.002,
                    "coverage_fraction": 0.957,
                },
            },
        },
    )


def _write_default_route_acceptance(path: Path, *, route_passed: bool = True) -> None:
    write_json(
        path,
        {
            "status": "passed" if route_passed else "failed",
            "passed": route_passed,
            "benchmark_contract": {"name": "default_route_fixture_contract"},
            "speedup_summary": {
                "speedup_vs_wbpp": 28.75,
                "glass": {"weighted_frame_count": 193},
                "comparison": {
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.002,
                    "coverage_fraction": 0.97,
                },
            },
            "checks": [
                {
                    "name": "contract_required_command_token:--memory-mode resident",
                    "passed": route_passed,
                },
                {
                    "name": "contract_required_command_token:--backend cuda",
                    "passed": route_passed,
                },
                {
                    "name": (
                        "contract_required_command_token:"
                        "--resident-registration similarity_cuda_triangle"
                    ),
                    "passed": route_passed,
                },
                {
                    "name": "contract_required_command_token_group:resident_h2d_or_runtime_preset",
                    "passed": route_passed,
                },
            ],
        },
    )


def _write_registration_results(path: Path, *, admission_status: str = "accepted") -> None:
    blocked = admission_status == "blocked"
    allow_rejected = admission_status == "allowed_quality_rejected_reference"
    quality_gate_status = "rejected" if blocked or allow_rejected else "accepted"
    reason = None
    if blocked:
        reason = "reference frame failed the quality gate"
    elif allow_rejected:
        reason = "quality-rejected reference explicitly allowed by registration policy"
    write_json(
        path,
        {
            "schema_version": 1,
            "reference_frame_id": "F000001",
            "quality_reference_frame_id": "F000001",
            "requested_reference_frame_id": None,
            "reference_admission": {
                "status": admission_status,
                "reference_frame_id": "F000001",
                "quality_gate_status": quality_gate_status,
                "quality_gate_enforced": True,
                "reference_selection_fallback": blocked or allow_rejected,
                "allow_quality_rejected_reference": allow_rejected,
                "reason": reason,
            },
            "registration_results": [
                {
                    "frame_id": "F000001",
                    "status": "quality_rejected" if blocked else "reference",
                    "quality_gate_status": quality_gate_status,
                    "registration_solution_source": (
                        "quality_reference_admission" if blocked else "streaming_star_detector"
                    ),
                }
            ],
        },
    )


def _write_quality_results(path: Path, *, rejected: bool = False) -> None:
    bad_status = "rejected" if rejected else "accepted"
    bad_warnings = (
        ["saturation_fraction 0.00879 exceeds max_saturation_fraction=0.005"]
        if rejected
        else []
    )
    write_json(
        path,
        {
            "schema_version": 1,
            "quality_gate_policy": {
                "max_saturation_fraction": 0.005,
                "saturation_level": 5000.0,
            },
            "frame_quality": [
                {
                    "frame_id": "F_SAT",
                    "star_count": 90,
                    "fwhm_px": 5.8,
                    "eccentricity": 0.44,
                    "background_rms": 24.0,
                    "snr": 33.0,
                    "quality_score": 420.0,
                    "weight": 0.42,
                    "saturation_fraction": 0.0087890625,
                    "saturated_pixel_count": 36,
                    "saturation_level": 5000.0,
                    "saturation_source": "threshold",
                    "quality_gate_status": bad_status,
                    "quality_gate_warnings": bad_warnings,
                },
                {
                    "frame_id": "F_OK",
                    "star_count": 120,
                    "fwhm_px": 2.1,
                    "eccentricity": 0.31,
                    "background_rms": 18.0,
                    "snr": 55.0,
                    "quality_score": 1000.0,
                    "weight": 1.0,
                    "saturation_fraction": 0.0,
                    "saturated_pixel_count": 0,
                    "saturation_level": 5000.0,
                    "saturation_source": "threshold",
                    "quality_gate_status": "accepted",
                    "quality_gate_warnings": [],
                },
            ],
            "reference_frame_id": "F_OK",
        },
    )


def _write_quality_metrics_compare(path: Path, *, passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "quality_metrics_compare",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "baseline": {"metric_count": 7, "frame_count": 2},
            "candidate": {"metric_count": 7, "frame_count": 2},
            "metric_rows": [
                {
                    "metric": "fwhm_px",
                    "bad_median_ratio": 1.0 if passed else 1.4,
                }
            ],
            "checks": [
                {
                    "name": "candidate_metric_summary_preserved",
                    "passed": True,
                    "evidence": {"missing_metrics": []},
                },
                {
                    "name": "bad_median_ratio_within_limit",
                    "passed": passed,
                    "evidence": {
                        "max_bad_median_ratio": 1.2,
                        "failing_metrics": []
                        if passed
                        else [{"metric": "fwhm_px", "bad_median_ratio": 1.4}],
                    },
                },
            ],
        },
    )


def _write_resident_winsorized_benchmark_audit(path: Path, *, passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "resident_winsorized_benchmark_audit",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "contract_name": "s2_gate_266_default_resident_winsorized_microbenchmark",
            "contract_path": "benchmarks/resident_winsorized_microbenchmark_contract.json",
            "benchmark_path": "runs/checkpoints/s2_gate_265_resident_winsorized_benchmark.json",
            "failed_checks": [] if passed else ["hardened_master_rms_within_contract"],
            "checks": [
                {"name": "artifact_type_matches", "passed": True},
                {"name": "benchmark_passed", "passed": passed},
                {"name": "hardened_master_rms_within_contract", "passed": passed},
            ],
            "summary": {
                "frame_count": 8,
                "shape": [16, 16],
                "hardened_master_rms": 5.0e-6 if passed else 9.0e-4,
                "hardened_master_max_abs": 1.5e-5,
                "fast_approx_master_rms": 0.5,
                "cuda_hardened_s": 0.002,
                "cuda_fast_approx_s": 0.001,
                "cpu_baseline_s": 0.01,
            },
        },
    )


def _write_resident_winsorized_sweep_audit(path: Path, *, passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "resident_winsorized_sweep_audit",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
            "contract_path": "benchmarks/resident_winsorized_sweep_contract.json",
            "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
            "failed_checks": [] if passed else ["frame_200_hardened_master_rms_within_contract"],
            "checks": [
                {"name": "artifact_type_matches", "passed": True},
                {"name": "sweep_passed", "passed": passed},
                {"name": "required_frame_count_passed", "passed": passed},
                {"name": "frame_200_hardened_master_rms_within_contract", "passed": passed},
            ],
            "summary": {
                "frame_counts": [8, 32, 128, 200],
                "run_count": 4,
                "required_frame_count": 200,
                "required_frame_count_passed": passed,
                "required_frame_master": {
                    "rms": 2.3e-5 if passed else 8.0e-5,
                    "max_abs": 6.1e-5,
                    "p99_abs": 4.9e-5,
                },
                "required_frame_timing_s": {
                    "cpu_baseline": 0.012,
                    "cuda_fast_approx": 0.001,
                    "cuda_hardened": 0.002,
                },
                "max_hardened_master_rms": 2.3e-5 if passed else 8.0e-5,
            },
        },
    )


def _write_pipeline_contract(
    path: Path,
    *,
    passed: bool = True,
    resident_result_contract_passed: bool = True,
    rejection_sample_accounting_passed: bool = True,
    sample_accounting_closure_passed: bool = True,
    integration_engine_policy_passed: bool = True,
    runtime_default_passed: bool = True,
) -> None:
    pipeline_passed = (
        passed
        and resident_result_contract_passed
        and rejection_sample_accounting_passed
        and sample_accounting_closure_passed
        and integration_engine_policy_passed
        and runtime_default_passed
    )
    resident_result_checks = [
        {
            "name": "source_terms_present",
            "passed": resident_result_contract_passed,
            "note": ""
            if resident_result_contract_passed
            else "resident output lost source term provenance",
            "evidence": {
                "available": resident_result_contract_passed,
                "required": True,
                "actual": ["coverage", "weight", "rejection"]
                if resident_result_contract_passed
                else [],
            },
        },
        {"name": "required_maps_exist", "passed": True},
    ]
    engine_policy_failed = []
    if not integration_engine_policy_passed:
        engine_policy_failed = [
            {
                "item": "H",
                "status": "implicit_cuda_fast_path",
                "backend": "cuda",
                "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                "failures": ["cuda_fast_path_not_explicit"],
            }
        ]
    runtime_default_failed_masters = [] if runtime_default_passed else [
        {
            "name": "bias_legacy",
            "type": "bias",
            "tile_stack_mode": "legacy_streaming_accumulator",
            "status": "failed",
            "failures": ["legacy_master_stack_mode"],
        }
    ]
    runtime_default = {
        "passed": runtime_default_passed,
        "status": "passed" if runtime_default_passed else "failed",
        "master_count": 1,
        "master_stack_engine_count": 1 if runtime_default_passed else 0,
        "master_resident_count": 0,
        "legacy_master_count": 0 if runtime_default_passed else 1,
        "integration_output_count": 1,
        "integration_stack_engine_default_count": 0,
        "integration_resident_count": 1,
        "explicit_cuda_fast_path_count": 0,
        "failed_masters": runtime_default_failed_masters,
        "failed_outputs": [],
    }
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "pipeline_invariant_contract",
            "status": "passed" if pipeline_passed else "failed",
            "passed": pipeline_passed,
            "checks": [
                {"name": "integration_output_maps_available", "passed": passed},
                {"name": "integration_dq_contract", "passed": passed},
                {"name": "integration_stack_result_contract", "passed": passed},
                {
                    "name": "integration_resident_result_contract",
                    "passed": resident_result_contract_passed,
                },
                {"name": "integration_dq_map_pixels_match_summary", "passed": passed},
                {"name": "integration_coverage_map_pixels_match_dq", "passed": passed},
                {"name": "integration_rejection_map_pixels_match_dq", "passed": passed},
                {
                    "name": "integration_default_engine_policy",
                    "passed": integration_engine_policy_passed,
                    "evidence": {
                        "output_count": 1,
                        "non_resident_count": 0 if integration_engine_policy_passed else 1,
                        "resident_count": 1 if integration_engine_policy_passed else 0,
                        "top_level_present": not integration_engine_policy_passed,
                        "top_level_default_ok": not integration_engine_policy_passed,
                        "failed": engine_policy_failed,
                    },
                },
                {
                    "name": "stack_engine_runtime_default_path",
                    "passed": runtime_default_passed,
                    "evidence": {
                        "master_count": runtime_default["master_count"],
                        "master_stack_engine_count": runtime_default[
                            "master_stack_engine_count"
                        ],
                        "master_resident_count": runtime_default[
                            "master_resident_count"
                        ],
                        "legacy_master_count": runtime_default[
                            "legacy_master_count"
                        ],
                        "integration_output_count": runtime_default[
                            "integration_output_count"
                        ],
                        "integration_stack_engine_default_count": runtime_default[
                            "integration_stack_engine_default_count"
                        ],
                        "integration_resident_count": runtime_default[
                            "integration_resident_count"
                        ],
                        "explicit_cuda_fast_path_count": runtime_default[
                            "explicit_cuda_fast_path_count"
                        ],
                        "failed_masters": runtime_default["failed_masters"],
                        "failed_outputs": runtime_default["failed_outputs"],
                    },
                },
                {
                    "name": "integration_rejection_sample_counts_match_maps",
                    "passed": rejection_sample_accounting_passed,
                    "evidence": {
                        "verified_records": 1,
                        "required_records": 1,
                        "failed": []
                        if rejection_sample_accounting_passed
                        else [
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
                },
                {
                    "name": "integration_sample_accounting_closure",
                    "passed": sample_accounting_closure_passed,
                    "evidence": {
                        "output_count": 1,
                        "present_count": 1,
                        "failed": []
                        if sample_accounting_closure_passed
                        else [
                            {
                                "item": "H",
                                "status": "failed",
                                "input_valid_samples_before_rejection": 9,
                                "valid_samples_after_rejection": 6,
                                "rejected_samples": 2,
                            }
                        ],
                    },
                },
            ],
            "calibration": {
                "master_count": 3,
                "calibrated_light_count": 200,
                "resident_native_calibration_artifact": True,
                "resident_calibrated_light_count": 200,
            },
            "integration": {
                "engine_policy": {
                    "passed": integration_engine_policy_passed,
                    "top_level_present": not integration_engine_policy_passed,
                    "top_level_default_ok": not integration_engine_policy_passed,
                    "output_count": 1,
                    "non_resident_count": 0 if integration_engine_policy_passed else 1,
                    "resident_count": 1 if integration_engine_policy_passed else 0,
                    "failed": engine_policy_failed,
                    "outputs": [
                        {
                            "item": "H",
                            "backend": "cuda_resident_stack"
                            if integration_engine_policy_passed
                            else "cuda",
                            "memory_mode": "resident"
                            if integration_engine_policy_passed
                            else None,
                            "tile_stack_mode": None
                            if integration_engine_policy_passed
                            else "cuda_streaming_accumulator_fast_path",
                            "required": not integration_engine_policy_passed,
                            "passed": integration_engine_policy_passed,
                            "status": "resident_not_required"
                            if integration_engine_policy_passed
                            else "implicit_cuda_fast_path",
                            "failures": []
                            if integration_engine_policy_passed
                            else ["cuda_fast_path_not_explicit"],
                        }
                    ],
                },
                "outputs": [
                    {
                        "item": "H",
                        "backend": "cuda_resident_stack",
                        "memory_mode": "resident",
                        "resident_result_contract": {
                            "required": True,
                            "passed": resident_result_contract_passed,
                            "status": "passed"
                            if resident_result_contract_passed
                            else "failed",
                            "contract": {
                                "schema_version": 1,
                                "status": "passed"
                                if resident_result_contract_passed
                                else "failed",
                                "passed": resident_result_contract_passed,
                                "checks": resident_result_checks,
                            },
                        },
                        "sample_accounting_closure": {
                            "present": True,
                            "required": True,
                            "status": "passed"
                            if sample_accounting_closure_passed
                            else "failed",
                            "passed": sample_accounting_closure_passed,
                            "input_total_match": True,
                            "valid_rejection_match": sample_accounting_closure_passed,
                            "input_samples": 12,
                            "input_valid_samples_before_rejection": 9,
                            "input_invalid_samples_before_rejection": 3,
                            "valid_samples_after_rejection": 6,
                            "rejected_samples": 3
                            if sample_accounting_closure_passed
                            else 2,
                        },
                    }
                ],
                "maps": [
                    {"item": "H", "map": "master"},
                    {"item": "H", "map": "coverage"},
                    {"item": "H", "map": "dq"},
                ],
            },
            "stack_engine_runtime_default": runtime_default,
            "pixel_verification": {
                "enabled": True,
                "tile_size": 256,
                "tolerance_pixels": 0,
                "integration_outputs": [
                    {
                        "item": "H",
                        "status": "verified",
                        "rejection_sample_accounting": {
                            "status": "verified",
                            "verified": True,
                            "ok": rejection_sample_accounting_passed,
                            "required": True,
                            "rejection": "winsorized_sigma",
                            "map_rejected_sample_sum": 6
                            if rejection_sample_accounting_passed
                            else 7,
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
                                    "actual": 6 if rejection_sample_accounting_passed else 7,
                                    "summary": 6,
                                    "delta": 0 if rejection_sample_accounting_passed else 1,
                                    "passed": rejection_sample_accounting_passed,
                                },
                                {
                                    "source": "dq_provenance_summary.rejected_samples",
                                    "actual": 6 if rejection_sample_accounting_passed else 7,
                                    "summary": 6,
                                    "delta": 0 if rejection_sample_accounting_passed else 1,
                                    "passed": rejection_sample_accounting_passed,
                                },
                            ],
                        },
                    }
                ],
            },
        },
    )


def _write_stack_engine_contract(
    path: Path,
    *,
    ready: bool = True,
    passed: bool = True,
    gap_count: int = 0,
) -> None:
    recommendation = (
        "stack_engine_default_ready"
        if ready and gap_count == 0
        else "stack_engine_contract_gaps_remain"
    )
    blockers = []
    if not ready:
        blockers.append(
            {
                "name": "phase2_stack_engine_default_gaps",
                "gap_count": gap_count,
                "gap_surfaces": [
                    {
                        "surface": "integration",
                        "item": "H",
                        "engine_family": "legacy",
                        "gap_reason": "legacy_or_unknown_engine",
                    }
                ]
                if gap_count
                else [],
            }
        )
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "stack_engine_default_contract",
            "status": "passed" if passed else "failed",
            "passed": passed,
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "resident_calibration_contract_attached": False,
            "resident_result_contract_attached": False,
            "checks": [
                {"name": "calibration_masters_use_stack_engine", "passed": passed},
                {"name": "integration_outputs_use:stack_engine_cpu", "passed": passed},
            ],
            "adoption": {
                "target_engine": "stack_engine_cpu",
                "surface_count": 4,
                "stack_engine_surface_count": 4 - gap_count,
                "cuda_resident_surface_count": 0,
                "contract_ready_count": 4 - gap_count,
                "result_contract_passed_count": 4 - gap_count,
                "fallback_count": 0,
                "phase2_stack_engine_default_gap_count": gap_count,
                "gap_surfaces": blockers[0]["gap_surfaces"] if blockers else [],
                "recommendation": recommendation,
            },
            "default_promotion": {
                "ready": ready,
                "status": "ready" if ready else "blocked",
                "required_scope": "all",
                "actual_scope": "all",
                "surface_count": 4,
                "calibration_surface_count": 3,
                "integration_surface_count": 1,
                "phase2_stack_engine_default_gap_count": gap_count,
                "recommendation": recommendation,
                "blocker_count": len(blockers),
                "blockers": blockers,
            },
        },
    )


def _write_release_decision(
    path: Path,
    *,
    ready: bool = True,
    warp_quality_ready: bool | None = None,
    resident_fastpath_ready: bool | None = None,
    include_runtime_repeat: bool = True,
    runtime_ratio: float = 1.053,
) -> None:
    payload = {
        "schema_version": 1,
        "artifact_type": "release_promotion_decision",
        "status": "default_change_ready" if ready else "release_candidate_ready",
        "passed": True,
        "release_candidate_ready": True,
        "default_change_ready": ready,
        "recommendation": "promote_default_candidate"
        if ready
        else "repeat_benchmark_before_default_change",
        "speedup": {"actual": 58.0, "required_min": 2.0},
        "pipeline_handoff": {
            "source": "explicit_pipeline_contract",
            "status": "passed",
            "passed": True,
            "pixel_verification_enabled": True,
        },
    }
    if include_runtime_repeat:
        payload["runtime_repeat"] = {
            "present": True,
            "run_count": 3,
            "considered_run_count": 3,
            "best_label": "repeat02",
            "best_elapsed_s": 22.6,
            "slowest_elapsed_s": round(22.6 * runtime_ratio, 3),
            "elapsed_ratio_vs_best": runtime_ratio,
            "max_elapsed_ratio_vs_best": 1.25,
            "recommendation": "best_observed:repeat02",
        }
    if warp_quality_ready is not None:
        payload["warp_quality_handoff"] = {
            "source": "acceptance_audit",
            "present": True,
            "status": "passed" if warp_quality_ready else "failed",
            "ready": warp_quality_ready,
            "path": "warp_quality_contract.json",
            "exists": True,
            "artifact_type": "warp_quality_contract",
            "contract_status": "passed" if warp_quality_ready else "failed",
            "contract_passed": warp_quality_ready,
            "check_count": 9,
            "output_count": 1,
            "failed_checks": [] if warp_quality_ready else ["warp_quality_contract_passed"],
            "failed_acceptance_checks": []
            if warp_quality_ready
            else ["warp_quality_contract_passed"],
        }
    if resident_fastpath_ready is not None:
        failed_checks = (
            []
            if resident_fastpath_ready
            else ["contract_resident_registration_fastpath_descriptor_batch_mode"]
        )
        payload["resident_registration_fastpath_handoff"] = {
            "source": "explicit_resident_artifacts_json",
            "present": True,
            "status": "passed" if resident_fastpath_ready else "failed",
            "ready": resident_fastpath_ready,
            "required_by_benchmark_contract": True,
            "path": "resident_artifacts.json",
            "exists": True,
            "available": True,
            "resident_registration_mode": "similarity_cuda_triangle",
            "descriptor_fit_batch_mode": "native_batch_shared_reference_device",
            "pixel_refine_batch_mode": "native_batch_one_seed_per_frame",
            "triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
            "triangle_warp_batch_frame_count": 3,
            "warp_copy_mode": "default_stream_async_device_to_device",
            "passed_check_count": 23 if resident_fastpath_ready else 22,
            "failed_check_count": 0 if resident_fastpath_ready else 1,
            "failed_checks": failed_checks,
            "failed_acceptance_checks": failed_checks,
        }
    write_json(path, payload)


def _write_publish_preflight(
    path: Path,
    *,
    ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
    include_rejection_sample_accounting: bool = True,
    sample_accounting_closure_ready: bool = True,
    include_sample_accounting_closure: bool = True,
    stack_engine_ready: bool = True,
    include_stack_engine_contract: bool = True,
    resident_winsorized_sweep_ready: bool = True,
    include_resident_winsorized_sweep: bool = True,
    integration_engine_policy_ready: bool = True,
    include_integration_engine_policy: bool = True,
    stack_runtime_default_ready: bool = True,
    matrix_stack_runtime_default_ready: bool | None = None,
    default_promotion_stack_runtime_default_ready: bool | None = None,
    include_stack_runtime_default: bool = True,
    direct_runtime_evidence_ready: bool = True,
    include_direct_runtime_evidence: bool = True,
    direct_runtime_acceptance_source: str = "explicit_resident_artifacts_json",
    direct_runtime_pipeline_calibration_source: str = "resident_artifacts_json_fallback",
    direct_runtime_pipeline_resident_lights: int = 200,
    direct_publication_guard_ready: bool = True,
    direct_publication_guard_lights: int | None = None,
    include_direct_publication_guard: bool = True,
    release_quality_publication_guard_ready: bool = True,
    release_quality_publication_guard_raw_status: str = "passed",
    release_quality_publication_guard_phase2_status: str = "passed",
    include_release_quality_publication_guard: bool = True,
    release_quality_publication_guard_final_checks_ready: bool | None = None,
    include_release_quality_publication_guard_final_checks: bool = True,
    release_quality_publication_guard_final_evidence_ready: bool | None = None,
    include_release_quality_publication_guard_final_evidence: bool = True,
    release_quality_publication_guard_final_evidence_compatible_missing: bool = False,
    resident_fastpath_handoff_ready: bool = True,
    include_resident_fastpath_handoff: bool = True,
    resident_result_contract_ready: bool = True,
    include_resident_result_contract: bool = True,
    stack_publication_audit_ready: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
    include_stack_publication_audit: bool = True,
    quality_metrics_compare_ready: bool = True,
    include_quality_metrics_compare: bool = True,
) -> None:
    matrix_runtime_ready = (
        stack_runtime_default_ready
        if matrix_stack_runtime_default_ready is None
        else matrix_stack_runtime_default_ready
    )
    default_runtime_ready = (
        stack_runtime_default_ready
        if default_promotion_stack_runtime_default_ready is None
        else default_promotion_stack_runtime_default_ready
    )
    runtime_defaults_ready = matrix_runtime_ready and default_runtime_ready
    publication_guard_lights = (
        direct_runtime_pipeline_resident_lights
        if direct_publication_guard_lights is None
        else direct_publication_guard_lights
    )
    direct_publication_guard_passed = (
        direct_publication_guard_ready
        and direct_runtime_evidence_ready
        and direct_runtime_acceptance_source == "explicit_resident_artifacts_json"
        and direct_runtime_pipeline_calibration_source
        == "resident_artifacts_json_fallback"
        and publication_guard_lights >= 200
    )
    release_quality_publication_guard_passed = (
        release_quality_publication_guard_ready
        and release_quality_publication_guard_raw_status == "passed"
        and release_quality_publication_guard_phase2_status == "passed"
    )
    if release_quality_publication_guard_final_checks_ready is None:
        release_quality_publication_guard_final_checks_ready = (
            release_quality_publication_guard_passed
        )
    if release_quality_publication_guard_final_evidence_ready is None:
        release_quality_publication_guard_final_evidence_ready = (
            release_quality_publication_guard_final_checks_ready
        )
    release_quality_publication_guard_final_evidence_passed = (
        not include_release_quality_publication_guard_final_evidence
        or release_quality_publication_guard_final_evidence_compatible_missing
        or release_quality_publication_guard_final_evidence_ready
    )
    release_quality_publication_guard_preflight_passed = (
        release_quality_publication_guard_passed
        and (
            release_quality_publication_guard_final_checks_ready
            or not include_release_quality_publication_guard_final_checks
        )
        and release_quality_publication_guard_final_evidence_passed
    )
    artifact_ready = ready and (
        rejection_sample_accounting_ready or not include_rejection_sample_accounting
    ) and (
        sample_accounting_closure_ready or not include_sample_accounting_closure
    ) and (
        stack_engine_ready or not include_stack_engine_contract
    ) and (
        resident_winsorized_sweep_ready or not include_resident_winsorized_sweep
    ) and (
        integration_engine_policy_ready or not include_integration_engine_policy
    ) and (
        runtime_defaults_ready or not include_stack_runtime_default
    ) and (
        direct_runtime_evidence_ready or not include_direct_runtime_evidence
    ) and (
        direct_publication_guard_passed or not include_direct_publication_guard
    ) and (
        release_quality_publication_guard_preflight_passed
        or not include_release_quality_publication_guard
    ) and (
        resident_fastpath_handoff_ready or not include_resident_fastpath_handoff
    ) and (
        resident_result_contract_ready or not include_resident_result_contract
    ) and (
        (
            stack_publication_audit_ready
            and stack_publication_policy_ready
            and stack_publication_resident_winsorized_ready
        )
        or not include_stack_publication_audit
    ) and (
        quality_metrics_compare_ready or not include_quality_metrics_compare
    )
    summary = {
        "release_tag": "v0.1.0-test",
        "asset_count": 4,
        "package_count": 4,
        "primary_package": "cuda13",
        "ordered_try_list": ["cuda13", "cuda12", "cuda11", "cpu"],
        "source_stamps": ["abcdef0"],
        "default_promotion_status": "default_promotion_ready" if ready else "blocked",
        "default_route_check_count": 4 if ready else 2,
        "default_route_speedup_vs_reference": 28.75,
    }
    checks = []
    failed_checks = [] if artifact_ready else ["manifest_assets_match_github_plan"]
    if include_rejection_sample_accounting:
        status = "passed" if rejection_sample_accounting_ready else "failed"
        summary.update(
            {
                "github_plan_phase2_rejection_sample_accounting_status": status,
                "github_plan_matrix_rejection_sample_accounting_status": status,
                "matrix_rejection_sample_accounting_status": status,
                "default_promotion_rejection_sample_accounting_status": status,
            }
        )
        checks = [
            {
                "name": "github_plan_phase2_rejection_sample_accounting_passed",
                "passed": rejection_sample_accounting_ready,
            },
            {
                "name": "github_plan_matrix_rejection_sample_accounting_passed",
                "passed": rejection_sample_accounting_ready,
            },
            {
                "name": "matrix_rejection_sample_accounting_passed",
                "passed": rejection_sample_accounting_ready,
            },
            {
                "name": "default_promotion_rejection_sample_accounting_passed",
                "passed": rejection_sample_accounting_ready,
            },
            {
                "name": "github_plan_matrix_rejection_accounting_matches_matrix",
                "passed": rejection_sample_accounting_ready,
            },
        ]
        if not rejection_sample_accounting_ready:
            failed_checks = [
                "github_plan_phase2_rejection_sample_accounting_passed",
                "github_plan_matrix_rejection_sample_accounting_passed",
                "matrix_rejection_sample_accounting_passed",
                "default_promotion_rejection_sample_accounting_passed",
            ]
    if include_sample_accounting_closure:
        status = "passed" if sample_accounting_closure_ready else "failed"
        summary.update(
            {
                "github_plan_phase2_sample_accounting_closure_status": status,
                "github_plan_matrix_sample_accounting_closure_status": status,
                "matrix_sample_accounting_closure_status": status,
                "default_promotion_sample_accounting_closure_status": status,
            }
        )
        checks.extend(
            [
                {
                    "name": "github_plan_phase2_sample_accounting_closure_passed",
                    "passed": sample_accounting_closure_ready,
                },
                {
                    "name": "github_plan_matrix_sample_accounting_closure_passed",
                    "passed": sample_accounting_closure_ready,
                },
                {
                    "name": "matrix_sample_accounting_closure_passed",
                    "passed": sample_accounting_closure_ready,
                },
                {
                    "name": "default_promotion_sample_accounting_closure_passed",
                    "passed": sample_accounting_closure_ready,
                },
                {
                    "name": "github_plan_matrix_sample_closure_matches_matrix",
                    "passed": sample_accounting_closure_ready,
                },
            ]
        )
        if not sample_accounting_closure_ready:
            failed_checks = [
                *failed_checks,
                "github_plan_phase2_sample_accounting_closure_passed",
                "github_plan_matrix_sample_accounting_closure_passed",
                "matrix_sample_accounting_closure_passed",
                "default_promotion_sample_accounting_closure_passed",
            ]
    if include_integration_engine_policy:
        status = "passed" if integration_engine_policy_ready else "failed"
        summary.update(
            {
                "matrix_integration_engine_policy_ready": integration_engine_policy_ready,
                "matrix_acceptance_integration_engine_policy_status": status,
                "matrix_pipeline_integration_engine_policy_status": status,
                "default_promotion_integration_engine_policy_ready": (
                    integration_engine_policy_ready
                ),
                "default_promotion_acceptance_integration_engine_policy_status": status,
                "default_promotion_pipeline_integration_engine_policy_status": status,
            }
        )
        checks.extend(
            [
                {
                    "name": "windows_release_matrix_acceptance_integration_engine_policy_passed",
                    "passed": integration_engine_policy_ready,
                },
                {
                    "name": "windows_release_matrix_pipeline_integration_engine_policy_passed",
                    "passed": integration_engine_policy_ready,
                },
                {
                    "name": "default_promotion_acceptance_integration_engine_policy_passed",
                    "passed": integration_engine_policy_ready,
                },
                {
                    "name": "default_promotion_pipeline_integration_engine_policy_passed",
                    "passed": integration_engine_policy_ready,
                },
                {
                    "name": "matrix_integration_engine_policy_matches_default_promotion",
                    "passed": integration_engine_policy_ready,
                },
            ]
        )
        if not integration_engine_policy_ready:
            failed_checks = [
                *failed_checks,
                "windows_release_matrix_acceptance_integration_engine_policy_passed",
                "windows_release_matrix_pipeline_integration_engine_policy_passed",
                "default_promotion_acceptance_integration_engine_policy_passed",
                "default_promotion_pipeline_integration_engine_policy_passed",
                "matrix_integration_engine_policy_matches_default_promotion",
            ]
    if include_stack_engine_contract:
        status = "passed" if stack_engine_ready else "failed"
        summary.update(
            {
                "github_plan_phase2_stack_engine_contract_status": status,
                "github_plan_matrix_stack_engine_contract_status": status,
                "matrix_stack_engine_contract_status": status,
                "default_promotion_stack_engine_contract_status": status,
                "matrix_stack_engine_contract_default_gap_count": (
                    0 if stack_engine_ready else 1
                ),
                "default_promotion_stack_engine_contract_default_gap_count": (
                    0 if stack_engine_ready else 1
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "github_plan_phase2_stack_engine_default_contract_ready",
                    "passed": stack_engine_ready,
                },
                {
                    "name": "github_plan_matrix_stack_engine_contract_ready",
                    "passed": stack_engine_ready,
                },
                {
                    "name": "github_plan_stack_engine_contract_agreement_passed",
                    "passed": stack_engine_ready,
                },
                {
                    "name": "matrix_stack_engine_contract_ready",
                    "passed": stack_engine_ready,
                },
                {
                    "name": "default_promotion_stack_engine_contract_ready",
                    "passed": stack_engine_ready,
                },
                {
                    "name": "github_plan_matrix_stack_engine_contract_matches_matrix",
                    "passed": stack_engine_ready,
                },
                {
                    "name": "matrix_stack_engine_contract_matches_default_promotion",
                    "passed": stack_engine_ready,
                },
            ]
        )
        if not stack_engine_ready:
            failed_checks = [
                *failed_checks,
                "github_plan_phase2_stack_engine_default_contract_ready",
                "github_plan_matrix_stack_engine_contract_ready",
                "github_plan_stack_engine_contract_agreement_passed",
                "matrix_stack_engine_contract_ready",
                "default_promotion_stack_engine_contract_ready",
            ]
    if include_stack_runtime_default:
        matrix_status = "passed" if matrix_runtime_ready else "failed"
        default_status = "passed" if default_runtime_ready else "failed"
        runtime_match = runtime_defaults_ready
        summary.update(
            {
                "matrix_stack_engine_runtime_default_ready": matrix_runtime_ready,
                "matrix_acceptance_stack_engine_runtime_default_status": matrix_status,
                "matrix_pipeline_stack_engine_runtime_default_status": matrix_status,
                "matrix_stack_engine_runtime_default_acceptance_legacy_master_count": (
                    0 if matrix_runtime_ready else 1
                ),
                "matrix_stack_engine_runtime_default_pipeline_failed_output_count": (
                    0 if matrix_runtime_ready else 1
                ),
                "default_promotion_stack_engine_runtime_default_ready": (
                    default_runtime_ready
                ),
                "default_promotion_acceptance_stack_engine_runtime_default_status": (
                    default_status
                ),
                "default_promotion_pipeline_stack_engine_runtime_default_status": (
                    default_status
                ),
                "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count": (
                    0 if default_runtime_ready else 1
                ),
                "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count": (
                    0 if default_runtime_ready else 1
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
                    "passed": matrix_runtime_ready,
                },
                {
                    "name": "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
                    "passed": matrix_runtime_ready,
                },
                {
                    "name": "default_promotion_acceptance_stack_engine_runtime_default_passed",
                    "passed": default_runtime_ready,
                },
                {
                    "name": "default_promotion_pipeline_stack_engine_runtime_default_passed",
                    "passed": default_runtime_ready,
                },
                {
                    "name": "matrix_stack_engine_runtime_default_matches_default_promotion",
                    "passed": runtime_match,
                },
            ]
        )
        if not matrix_runtime_ready:
            failed_checks = [
                *failed_checks,
                "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
                "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
            ]
        if not default_runtime_ready:
            failed_checks = [
                *failed_checks,
                "default_promotion_acceptance_stack_engine_runtime_default_passed",
                "default_promotion_pipeline_stack_engine_runtime_default_passed",
            ]
        if not runtime_match:
            failed_checks = [
                *failed_checks,
                "matrix_stack_engine_runtime_default_matches_default_promotion",
            ]
    if include_direct_runtime_evidence:
        summary.update(
            {
                "matrix_direct_runtime_evidence_ready": direct_runtime_evidence_ready,
                "matrix_direct_runtime_acceptance_source": (
                    direct_runtime_acceptance_source
                ),
                "matrix_direct_runtime_acceptance_check_count": (
                    24 if direct_runtime_evidence_ready else 0
                ),
                "matrix_direct_runtime_pipeline_calibration_source": (
                    direct_runtime_pipeline_calibration_source
                ),
                "matrix_direct_runtime_pipeline_resident_lights": (
                    direct_runtime_pipeline_resident_lights
                    if direct_runtime_evidence_ready
                    else 0
                ),
                "default_promotion_direct_runtime_evidence_ready": (
                    direct_runtime_evidence_ready
                ),
                "default_promotion_direct_runtime_acceptance_source": (
                    direct_runtime_acceptance_source
                ),
                "default_promotion_direct_runtime_acceptance_check_count": (
                    24 if direct_runtime_evidence_ready else 0
                ),
                "default_promotion_direct_runtime_pipeline_calibration_source": (
                    direct_runtime_pipeline_calibration_source
                ),
                "default_promotion_direct_runtime_pipeline_resident_lights": (
                    direct_runtime_pipeline_resident_lights
                    if direct_runtime_evidence_ready
                    else 0
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "windows_release_matrix_direct_acceptance_fastpath_evidence",
                    "passed": direct_runtime_evidence_ready
                    and direct_runtime_acceptance_source
                    == "explicit_resident_artifacts_json",
                },
                {
                    "name": "windows_release_matrix_direct_pipeline_calibration_evidence",
                    "passed": direct_runtime_evidence_ready
                    and direct_runtime_pipeline_calibration_source
                    == "resident_artifacts_json_fallback"
                    and direct_runtime_pipeline_resident_lights >= 200,
                },
                {
                    "name": "default_promotion_direct_acceptance_fastpath_evidence",
                    "passed": direct_runtime_evidence_ready
                    and direct_runtime_acceptance_source
                    == "explicit_resident_artifacts_json",
                },
                {
                    "name": "default_promotion_direct_pipeline_calibration_evidence",
                    "passed": direct_runtime_evidence_ready
                    and direct_runtime_pipeline_calibration_source
                    == "resident_artifacts_json_fallback"
                    and direct_runtime_pipeline_resident_lights >= 200,
                },
                {
                    "name": "matrix_direct_runtime_evidence_matches_default_promotion",
                    "passed": direct_runtime_evidence_ready,
                },
            ]
        )
        if not direct_runtime_evidence_ready:
            failed_checks = [
                *failed_checks,
                "windows_release_matrix_direct_acceptance_fastpath_evidence",
                "windows_release_matrix_direct_pipeline_calibration_evidence",
                "default_promotion_direct_acceptance_fastpath_evidence",
                "default_promotion_direct_pipeline_calibration_evidence",
                "matrix_direct_runtime_evidence_matches_default_promotion",
            ]
    if include_direct_publication_guard:
        summary.update(
            {
                "github_plan_matrix_release_direct_publication_guard_ready": (
                    direct_publication_guard_passed
                ),
                "github_plan_matrix_release_direct_publication_guard_lights": (
                    publication_guard_lights
                ),
                "github_plan_matrix_default_promotion_release_direct_publication_guard_ready": (
                    direct_publication_guard_passed
                ),
                "github_plan_matrix_default_promotion_release_direct_publication_guard_lights": (
                    publication_guard_lights
                ),
                "matrix_release_direct_publication_guard_ready": (
                    direct_publication_guard_passed
                ),
                "matrix_release_direct_publication_guard_source_ready": (
                    direct_runtime_acceptance_source
                    == "explicit_resident_artifacts_json"
                    and direct_runtime_pipeline_calibration_source
                    == "resident_artifacts_json_fallback"
                ),
                "matrix_release_direct_publication_guard_count_ready": (
                    publication_guard_lights >= 200
                ),
                "matrix_release_direct_publication_guard_check_passed": (
                    direct_publication_guard_passed
                ),
                "matrix_release_direct_publication_guard_lights": (
                    publication_guard_lights
                ),
                "matrix_default_promotion_release_direct_publication_guard_ready": (
                    direct_publication_guard_passed
                ),
                "matrix_default_promotion_release_direct_publication_guard_lights": (
                    publication_guard_lights
                ),
                "default_promotion_release_direct_publication_guard_ready": (
                    direct_publication_guard_passed
                ),
                "default_promotion_release_direct_publication_guard_lights": (
                    publication_guard_lights
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "github_plan_matrix_release_decision_direct_publication_guard_passed",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "matrix_release_decision_direct_runtime_publication_guard_passed",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "default_promotion_release_decision_direct_runtime_publication_guard_passed",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "matrix_release_decision_direct_publication_guard_matches_default_promotion",
                    "passed": direct_publication_guard_passed,
                },
                {
                    "name": "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest",
                    "passed": direct_publication_guard_passed,
                },
            ]
        )
        if not direct_publication_guard_passed:
            failed_checks = [
                *failed_checks,
                "github_plan_matrix_release_decision_direct_publication_guard_passed",
                "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed",
                "matrix_release_decision_direct_runtime_publication_guard_passed",
                "default_promotion_release_decision_direct_runtime_publication_guard_passed",
            ]
    if include_release_quality_publication_guard:
        summary.update(
            {
                "matrix_release_quality_publication_guard_present": True,
                "matrix_release_quality_publication_guard_ready": (
                    release_quality_publication_guard_passed
                ),
                "matrix_release_quality_publication_guard_check_passed": (
                    release_quality_publication_guard_passed
                ),
                "matrix_release_quality_publication_guard_layers_ready": (
                    release_quality_publication_guard_passed
                ),
                "matrix_release_quality_publication_guard_raw_status": (
                    release_quality_publication_guard_raw_status
                ),
                "matrix_release_quality_publication_guard_phase2_status": (
                    release_quality_publication_guard_phase2_status
                ),
                "matrix_default_promotion_release_quality_publication_guard_ready": (
                    release_quality_publication_guard_passed
                ),
                "matrix_default_promotion_release_quality_publication_guard_raw_status": (
                    release_quality_publication_guard_raw_status
                ),
                "matrix_default_promotion_release_quality_publication_guard_phase2_status": (
                    release_quality_publication_guard_phase2_status
                ),
                "default_promotion_release_quality_publication_guard_present": True,
                "default_promotion_release_quality_publication_guard_ready": (
                    release_quality_publication_guard_passed
                ),
                "default_promotion_release_quality_publication_guard_check_passed": (
                    release_quality_publication_guard_passed
                ),
                "default_promotion_release_quality_publication_guard_layers_ready": (
                    release_quality_publication_guard_passed
                ),
                "default_promotion_release_quality_publication_guard_raw_status": (
                    release_quality_publication_guard_raw_status
                ),
                "default_promotion_release_quality_publication_guard_phase2_status": (
                    release_quality_publication_guard_phase2_status
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "matrix_release_decision_quality_compare_publication_guard_passed",
                    "passed": release_quality_publication_guard_passed,
                },
                {
                    "name": "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed",
                    "passed": release_quality_publication_guard_passed,
                },
                {
                    "name": "default_promotion_release_decision_quality_compare_publication_guard_passed",
                    "passed": release_quality_publication_guard_passed,
                },
                {
                    "name": "matrix_release_decision_quality_publication_guard_matches_default_promotion",
                    "passed": release_quality_publication_guard_passed,
                },
                {
                    "name": "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest",
                    "passed": release_quality_publication_guard_passed,
                },
            ]
        )
        if include_release_quality_publication_guard_final_checks:
            checks.extend(
                [
                    {
                        "name": "matrix_release_decision_release_quality_publication_guard_passed",
                        "passed": (
                            release_quality_publication_guard_final_checks_ready
                        ),
                    },
                    {
                        "name": "matrix_default_promotion_release_decision_release_quality_publication_guard_passed",
                        "passed": (
                            release_quality_publication_guard_final_checks_ready
                        ),
                    },
                    {
                        "name": "default_promotion_release_decision_release_quality_publication_guard_passed",
                        "passed": (
                            release_quality_publication_guard_final_checks_ready
                        ),
                    },
                    {
                        "name": "matrix_release_decision_release_quality_publication_guard_matches_default_promotion",
                        "passed": (
                            release_quality_publication_guard_final_checks_ready
                        ),
                    },
                    {
                        "name": "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest",
                        "passed": (
                            release_quality_publication_guard_final_checks_ready
                        ),
                    },
                ]
            )
        if include_release_quality_publication_guard_final_evidence:
            final_evidence_ready = (
                release_quality_publication_guard_final_evidence_ready
            )
            final_raw_ready = (
                None
                if release_quality_publication_guard_final_evidence_compatible_missing
                else final_evidence_ready
            )
            final_phase2_ready = (
                None
                if release_quality_publication_guard_final_evidence_compatible_missing
                else final_evidence_ready
            )
            final_evidence_fields = {
                "final_checks_ready": (
                    True
                    if release_quality_publication_guard_final_evidence_compatible_missing
                    else final_evidence_ready
                ),
                "final_checks_match": True,
                "raw_final_checks_ready": final_raw_ready,
                "phase2_final_checks_ready": final_phase2_ready,
            }
            for prefix in (
                "matrix_release_decision_release_quality_publication_guard",
                "matrix_default_promotion_release_decision_release_quality_publication_guard",
                "default_promotion_release_decision_release_quality_publication_guard",
            ):
                for suffix, value in final_evidence_fields.items():
                    summary[f"{prefix}_{suffix}"] = value
        if not release_quality_publication_guard_passed:
            failed_checks = [
                *failed_checks,
                "matrix_release_decision_quality_compare_publication_guard_passed",
                "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed",
                "default_promotion_release_decision_quality_compare_publication_guard_passed",
                "matrix_release_decision_quality_publication_guard_matches_default_promotion",
                "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest",
            ]
        if (
            include_release_quality_publication_guard_final_checks
            and not release_quality_publication_guard_final_checks_ready
        ):
            failed_checks = [
                *failed_checks,
                "matrix_release_decision_release_quality_publication_guard_passed",
                "matrix_default_promotion_release_decision_release_quality_publication_guard_passed",
                "default_promotion_release_decision_release_quality_publication_guard_passed",
                "matrix_release_decision_release_quality_publication_guard_matches_default_promotion",
                "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest",
            ]
        if (
            include_release_quality_publication_guard_final_evidence
            and not release_quality_publication_guard_final_evidence_passed
        ):
            failed_checks = [
                *failed_checks,
                "release_quality_publication_guard_final_evidence_ready",
            ]
    if include_resident_fastpath_handoff:
        raw_status = "passed" if resident_fastpath_handoff_ready else "failed"
        phase2_status = (
            "passed" if resident_fastpath_handoff_ready else "attention_required"
        )
        raw_check_count = 31 if resident_fastpath_handoff_ready else 0
        summary.update(
            {
                "github_plan_matrix_resident_fastpath_handoff_ready": (
                    resident_fastpath_handoff_ready
                ),
                "github_plan_matrix_resident_fastpath_handoff_raw_status": raw_status,
                "github_plan_matrix_resident_fastpath_handoff_phase2_status": (
                    phase2_status
                ),
                "github_plan_matrix_resident_fastpath_handoff_raw_check_count": (
                    raw_check_count
                ),
                "matrix_resident_fastpath_handoff_ready": (
                    resident_fastpath_handoff_ready
                ),
                "matrix_resident_fastpath_handoff_raw_status": raw_status,
                "matrix_resident_fastpath_handoff_phase2_status": phase2_status,
                "matrix_resident_fastpath_handoff_raw_check_count": raw_check_count,
                "default_promotion_resident_fastpath_handoff_ready": (
                    resident_fastpath_handoff_ready
                ),
                "default_promotion_resident_fastpath_handoff_raw_status": raw_status,
                "default_promotion_resident_fastpath_handoff_phase2_status": (
                    phase2_status
                ),
                "default_promotion_resident_fastpath_handoff_raw_check_count": (
                    raw_check_count
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "github_plan_matrix_resident_fastpath_release_handoff_ready",
                    "passed": resident_fastpath_handoff_ready,
                },
                {
                    "name": "matrix_resident_fastpath_release_handoff_ready",
                    "passed": resident_fastpath_handoff_ready,
                },
                {
                    "name": "default_promotion_resident_fastpath_release_handoff_ready",
                    "passed": resident_fastpath_handoff_ready,
                },
                {
                    "name": "github_plan_matrix_resident_fastpath_handoff_matches_matrix",
                    "passed": resident_fastpath_handoff_ready,
                },
                {
                    "name": "matrix_resident_fastpath_handoff_matches_default_promotion",
                    "passed": resident_fastpath_handoff_ready,
                },
            ]
        )
        if not resident_fastpath_handoff_ready:
            failed_checks = [
                *failed_checks,
                "github_plan_matrix_resident_fastpath_release_handoff_ready",
                "matrix_resident_fastpath_release_handoff_ready",
                "default_promotion_resident_fastpath_release_handoff_ready",
                "github_plan_matrix_resident_fastpath_handoff_matches_matrix",
                "matrix_resident_fastpath_handoff_matches_default_promotion",
            ]
    if include_resident_result_contract:
        status = "passed" if resident_result_contract_ready else "failed"
        required_count = 1
        failed_count = 0 if resident_result_contract_ready else 1
        summary.update(
            {
                "github_plan_matrix_resident_result_contract_ready": (
                    resident_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_status": status,
                "github_plan_matrix_resident_result_contract_phase2_check_passed": (
                    resident_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_required_count": (
                    required_count
                ),
                "github_plan_matrix_resident_result_contract_failed_count": (
                    failed_count
                ),
                "matrix_resident_result_contract_ready": (
                    resident_result_contract_ready
                ),
                "matrix_resident_result_contract_status": status,
                "matrix_resident_result_contract_phase2_check_passed": (
                    resident_result_contract_ready
                ),
                "matrix_resident_result_contract_required_count": required_count,
                "matrix_resident_result_contract_failed_count": failed_count,
                "default_promotion_resident_result_contract_ready": (
                    resident_result_contract_ready
                ),
                "default_promotion_resident_result_contract_status": status,
                "default_promotion_resident_result_contract_phase2_check_passed": (
                    resident_result_contract_ready
                ),
                "default_promotion_resident_result_contract_required_count": (
                    required_count
                ),
                "default_promotion_resident_result_contract_failed_count": (
                    failed_count
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "github_plan_matrix_resident_result_contract_handoff_passed",
                    "passed": resident_result_contract_ready,
                },
                {
                    "name": "matrix_resident_result_contract_handoff_passed",
                    "passed": resident_result_contract_ready,
                },
                {
                    "name": "default_promotion_resident_result_contract_handoff_passed",
                    "passed": resident_result_contract_ready,
                },
                {
                    "name": "github_plan_matrix_resident_result_contract_matches_matrix",
                    "passed": resident_result_contract_ready,
                },
                {
                    "name": "matrix_resident_result_contract_matches_default_promotion",
                    "passed": resident_result_contract_ready,
                },
            ]
        )
        if not resident_result_contract_ready:
            failed_checks = [
                *failed_checks,
                "github_plan_matrix_resident_result_contract_handoff_passed",
                "matrix_resident_result_contract_handoff_passed",
                "default_promotion_resident_result_contract_handoff_passed",
                "github_plan_matrix_resident_result_contract_matches_matrix",
                "matrix_resident_result_contract_matches_default_promotion",
            ]
    if include_resident_winsorized_sweep:
        status = "passed" if resident_winsorized_sweep_ready else "failed"
        required_frame_passed = resident_winsorized_sweep_ready
        summary.update(
            {
                "matrix_resident_winsorized_sweep_status": status,
                "matrix_resident_winsorized_sweep_required_frame_count": 200,
                "matrix_resident_winsorized_sweep_required_frame_count_passed": (
                    required_frame_passed
                ),
                "matrix_resident_winsorized_sweep_check_count": 27,
                "default_promotion_resident_winsorized_sweep_status": status,
                "default_promotion_resident_winsorized_sweep_required_frame_count": 200,
                "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
                    required_frame_passed
                ),
                "default_promotion_resident_winsorized_sweep_check_count": 27,
            }
        )
        checks.extend(
            [
                {
                    "name": "matrix_resident_winsorized_sweep_audit_passed",
                    "passed": resident_winsorized_sweep_ready,
                },
                {
                    "name": "matrix_resident_winsorized_required_frame_passed",
                    "passed": required_frame_passed,
                },
                {
                    "name": "matrix_resident_winsorized_sweep_check_count",
                    "passed": resident_winsorized_sweep_ready,
                },
                {
                    "name": "default_promotion_resident_winsorized_sweep_audit_passed",
                    "passed": resident_winsorized_sweep_ready,
                },
                {
                    "name": "default_promotion_resident_winsorized_required_frame_passed",
                    "passed": required_frame_passed,
                },
                {
                    "name": "default_promotion_resident_winsorized_sweep_matches_matrix",
                    "passed": resident_winsorized_sweep_ready,
                },
            ]
        )
        if not resident_winsorized_sweep_ready:
            failed_checks = [
                *failed_checks,
                "matrix_resident_winsorized_sweep_audit_passed",
                "matrix_resident_winsorized_required_frame_passed",
                "default_promotion_resident_winsorized_sweep_audit_passed",
                "default_promotion_resident_winsorized_required_frame_passed",
            ]
    if include_stack_publication_audit:
        publication_ready = (
            stack_publication_audit_ready
            and stack_publication_policy_ready
            and stack_publication_resident_winsorized_ready
        )
        status = "passed" if publication_ready else "failed"
        summary.update(
            {
                "matrix_stack_engine_publication_audit_status": status,
                "matrix_stack_engine_publication_audit_ready": publication_ready,
                "matrix_stack_engine_publication_policy_agreement": (
                    stack_publication_policy_ready
                ),
                "matrix_stack_engine_publication_resident_winsorized_agreement": (
                    stack_publication_resident_winsorized_ready
                ),
                "default_promotion_stack_engine_publication_audit_status": status,
                "default_promotion_stack_engine_publication_audit_ready": (
                    publication_ready
                ),
                "default_promotion_stack_engine_publication_policy_agreement": (
                    stack_publication_policy_ready
                ),
                "default_promotion_stack_engine_publication_resident_winsorized_agreement": (
                    stack_publication_resident_winsorized_ready
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "matrix_stack_engine_publication_audit_passed",
                    "passed": publication_ready,
                },
                {
                    "name": "matrix_stack_engine_publication_policy_chain_passed",
                    "passed": stack_publication_policy_ready,
                },
                {
                    "name": "matrix_stack_engine_publication_resident_winsorized_chain_passed",
                    "passed": stack_publication_resident_winsorized_ready,
                },
                {
                    "name": "default_promotion_stack_engine_publication_audit_passed",
                    "passed": publication_ready,
                },
                {
                    "name": "default_promotion_stack_engine_publication_policy_chain_passed",
                    "passed": stack_publication_policy_ready,
                },
                {
                    "name": "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
                    "passed": stack_publication_resident_winsorized_ready,
                },
                {
                    "name": "matrix_stack_engine_publication_audit_matches_default_promotion",
                    "passed": publication_ready,
                },
            ]
        )
        if not publication_ready:
            failed_checks = [
                *failed_checks,
                "matrix_stack_engine_publication_audit_passed",
                "default_promotion_stack_engine_publication_audit_passed",
                "matrix_stack_engine_publication_audit_matches_default_promotion",
            ]
            if not stack_publication_policy_ready:
                failed_checks.extend(
                    [
                        "matrix_stack_engine_publication_policy_chain_passed",
                        "default_promotion_stack_engine_publication_policy_chain_passed",
                    ]
                )
            if not stack_publication_resident_winsorized_ready:
                failed_checks.extend(
                    [
                        "matrix_stack_engine_publication_resident_winsorized_chain_passed",
                        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
                    ]
                )
    if include_quality_metrics_compare:
        status = "passed" if quality_metrics_compare_ready else "failed"
        failed_count = 0 if quality_metrics_compare_ready else 1
        summary.update(
            {
                "matrix_quality_metrics_compare_present": True,
                "matrix_quality_metrics_compare_ready": quality_metrics_compare_ready,
                "matrix_quality_metrics_compare_status": status,
                "matrix_quality_metrics_compare_failed_check_count": failed_count,
                "default_promotion_quality_metrics_compare_present": True,
                "default_promotion_quality_metrics_compare_ready": (
                    quality_metrics_compare_ready
                ),
                "default_promotion_quality_metrics_compare_status": status,
                "default_promotion_quality_metrics_compare_failed_check_count": (
                    failed_count
                ),
            }
        )
        checks.extend(
            [
                {
                    "name": "windows_release_matrix_quality_metrics_compare_handoff_passed",
                    "passed": quality_metrics_compare_ready,
                },
                {
                    "name": "default_promotion_quality_metrics_compare_handoff_passed",
                    "passed": quality_metrics_compare_ready,
                },
                {
                    "name": "matrix_quality_metrics_compare_matches_default_promotion",
                    "passed": quality_metrics_compare_ready,
                },
            ]
        )
        if not quality_metrics_compare_ready:
            failed_checks = [
                *failed_checks,
                "windows_release_matrix_quality_metrics_compare_handoff_passed",
                "default_promotion_quality_metrics_compare_handoff_passed",
                "matrix_quality_metrics_compare_matches_default_promotion",
            ]
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_publish_preflight",
            "status": "publish_preflight_ready" if artifact_ready else "blocked",
            "passed": artifact_ready,
            "recommendation": "publish_release_bundle"
            if artifact_ready
            else "fix_publish_preflight_blockers",
            "failed_checks": failed_checks,
            "summary": summary,
            "checks": checks,
        },
    )


def _write_stack_engine_publication_audit(
    path: Path,
    *,
    passed: bool = True,
    integration_engine_policy_ready: bool = True,
    resident_winsorized_ready: bool = True,
    resident_result_contract_ready: bool = True,
    direct_runtime_ready: bool = True,
) -> None:
    artifact_ready = (
        passed
        and integration_engine_policy_ready
        and resident_winsorized_ready
        and resident_result_contract_ready
        and direct_runtime_ready
    )
    status = "passed" if artifact_ready else "blocked"
    policy_status = (
        "publish_preflight_ready" if integration_engine_policy_ready else "blocked"
    )
    winsorized_status = (
        "publish_preflight_ready" if resident_winsorized_ready else "blocked"
    )
    resident_result_status = (
        "publish_preflight_ready" if resident_result_contract_ready else "blocked"
    )
    direct_runtime_status = (
        "publish_preflight_ready" if direct_runtime_ready else "blocked"
    )
    failed_checks = []
    if not passed:
        failed_checks.append("stack_engine_publication_audit_passed")
    if not integration_engine_policy_ready:
        failed_checks.extend(
            [
                "publish_preflight_integration_engine_policy_ready",
                "phase2_publish_preflight_integration_engine_policy_ready",
                "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight",
            ]
        )
    if not resident_winsorized_ready:
        failed_checks.extend(
            [
                "publish_preflight_resident_winsorized_sweep_ready",
                "phase2_publish_preflight_resident_winsorized_sweep_ready",
                "phase2_publish_preflight_resident_winsorized_matches_publish_preflight",
            ]
        )
    if not resident_result_contract_ready:
        failed_checks.extend(
            [
                "publish_preflight_resident_result_contract_ready",
                "phase2_publish_preflight_resident_result_contract_ready",
                "phase2_publish_preflight_resident_result_contract_matches_publish_preflight",
            ]
        )
    if not direct_runtime_ready:
        failed_checks.extend(
            [
                "publish_preflight_direct_runtime_evidence_ready",
                "phase2_publish_preflight_direct_runtime_evidence_ready",
                "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight",
            ]
        )
    checks = [
        {"name": "source_contract_ready", "passed": passed},
        {"name": "phase2_direct_contract_ready", "passed": passed},
        {"name": "publish_preflight_stack_engine_ready", "passed": passed},
        {"name": "phase2_publish_preflight_stack_engine_ready", "passed": passed},
        {
            "name": "publish_preflight_resident_winsorized_sweep_ready",
            "passed": resident_winsorized_ready,
        },
        {
            "name": "phase2_publish_preflight_resident_winsorized_sweep_ready",
            "passed": resident_winsorized_ready,
        },
        {
            "name": "phase2_publish_preflight_resident_winsorized_matches_publish_preflight",
            "passed": resident_winsorized_ready,
        },
        {
            "name": "publish_preflight_resident_result_contract_ready",
            "passed": resident_result_contract_ready,
        },
        {
            "name": "phase2_publish_preflight_resident_result_contract_ready",
            "passed": resident_result_contract_ready,
        },
        {
            "name": "phase2_publish_preflight_resident_result_contract_matches_publish_preflight",
            "passed": resident_result_contract_ready,
        },
        {
            "name": "publish_preflight_integration_engine_policy_ready",
            "passed": integration_engine_policy_ready,
        },
        {
            "name": "phase2_publish_preflight_integration_engine_policy_ready",
            "passed": integration_engine_policy_ready,
        },
        {
            "name": "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight",
            "passed": integration_engine_policy_ready,
        },
        {
            "name": "publish_preflight_direct_runtime_evidence_ready",
            "passed": direct_runtime_ready,
        },
        {
            "name": "phase2_publish_preflight_direct_runtime_evidence_ready",
            "passed": direct_runtime_ready,
        },
        {
            "name": "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight",
            "passed": direct_runtime_ready,
        },
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "glass_stack_engine_publication_audit",
            "status": status,
            "passed": artifact_ready,
            "recommendation": "publication_chain_ready"
            if artifact_ready
            else "fix_stack_engine_publication_chain",
            "failed_checks": failed_checks,
            "layers": {
                "source_contract": {"status": "passed", "ready": passed, "gap_count": 0},
                "phase2_direct_contract": {
                    "status": "passed",
                    "ready": passed,
                    "gap_count": 0,
                },
                "publish_preflight": {
                    "status": "publish_preflight_ready",
                    "ready": passed,
                    "gap_count": 0,
                },
                "phase2_publish_preflight": {
                    "status": "publish_preflight_ready",
                    "ready": passed,
                    "gap_count": 0,
                },
                "publish_preflight_resident_winsorized_sweep": {
                    "status": winsorized_status,
                    "ready": resident_winsorized_ready,
                },
                "phase2_publish_preflight_resident_winsorized_sweep": {
                    "status": winsorized_status,
                    "ready": resident_winsorized_ready,
                },
                "publish_preflight_resident_result_contract": {
                    "status": resident_result_status,
                    "ready": resident_result_contract_ready,
                },
                "phase2_publish_preflight_resident_result_contract": {
                    "status": resident_result_status,
                    "ready": resident_result_contract_ready,
                },
                "publish_preflight_integration_engine_policy": {
                    "status": policy_status,
                    "ready": integration_engine_policy_ready,
                },
                "phase2_publish_preflight_integration_engine_policy": {
                    "status": policy_status,
                    "ready": integration_engine_policy_ready,
                },
                "publish_preflight_direct_runtime_evidence": {
                    "status": direct_runtime_status,
                    "ready": direct_runtime_ready,
                },
                "phase2_publish_preflight_direct_runtime_evidence": {
                    "status": direct_runtime_status,
                    "ready": direct_runtime_ready,
                },
            },
            "checks": checks,
        },
    )


def _doctor_payload() -> dict:
    return {
        "recommendation": "cuda",
        "cuda": {
            "wrapper_importable": True,
            "native_extension_loaded": True,
            "cuda_available": True,
            "devices": [
                {
                    "device_id": 0,
                    "name": "Fixture GPU",
                    "compute_capability": "12.0",
                    "memory_total_mib": 97886,
                    "driver_version": "596.21",
                }
            ],
        },
        "windows_cuda_packages": {"ordered_try_list": ["cuda13", "cuda12", "cuda11", "cpu"]},
    }


def _status_payload(
    *,
    gate: int = 203,
    status: str = "green",
    checkpoint_green: bool = True,
    acceptance_passed: bool = True,
    acceptance_status: str = "passed",
    acceptance_pipeline_engine_policy_status: str = "passed",
    acceptance_pipeline_engine_policy_check_present: bool = True,
    acceptance_pipeline_engine_policy_check_passed: bool = True,
    acceptance_pipeline_runtime_default_status: str = "passed",
    acceptance_pipeline_runtime_default_check_present: bool = True,
    acceptance_pipeline_runtime_default_check_passed: bool = True,
    acceptance_pipeline_runtime_default_legacy_master_count: int = 0,
    fastpath_contract_status: str = "passed",
    fastpath_contract_check_count: int = 24,
    default_route_passed: bool = True,
    default_route_contract_passed: bool = True,
    cuda_available: bool = True,
    release_status: str = "release_manifest_ready",
    github_status: str = "release_plan_ready",
    publish_preflight_status: str = "publish_preflight_ready",
    publish_preflight_rejection_sample_status: str = "passed",
    publish_preflight_sample_closure_status: str = "passed",
    publish_preflight_integration_engine_policy_status: str = "passed",
    publish_preflight_integration_engine_policy_ready: bool = True,
    publish_preflight_stack_engine_status: str = "passed",
    publish_preflight_stack_runtime_default_status: str = "passed",
    publish_preflight_stack_runtime_default_ready: bool = True,
    publish_preflight_stack_runtime_default_legacy_master_count: int = 0,
    publish_preflight_stack_runtime_default_failed_output_count: int = 0,
    publish_preflight_direct_runtime_ready: bool = True,
    publish_preflight_direct_runtime_acceptance_source: str = "explicit_resident_artifacts_json",
    publish_preflight_direct_runtime_pipeline_source: str = "resident_artifacts_json_fallback",
    publish_preflight_direct_runtime_resident_lights: int = 200,
    publish_preflight_release_direct_publication_guard_ready: bool = True,
    publish_preflight_release_direct_publication_guard_lights: int = 200,
    publish_preflight_release_quality_publication_guard_present: bool = True,
    publish_preflight_release_quality_publication_guard_ready: bool = True,
    publish_preflight_release_quality_publication_guard_check_passed: bool = True,
    publish_preflight_release_quality_publication_guard_layers_ready: bool = True,
    publish_preflight_release_quality_publication_guard_raw_status: str = "passed",
    publish_preflight_release_quality_publication_guard_phase2_status: str = "passed",
    publish_preflight_release_quality_publication_guard_final_checks_present: bool = True,
    publish_preflight_release_quality_publication_guard_final_checks_passed: bool | None = None,
    publish_preflight_release_quality_publication_guard_final_evidence_present: bool = True,
    publish_preflight_release_quality_publication_guard_final_evidence_passed: bool | None = None,
    publish_preflight_release_quality_publication_guard_final_evidence_compatible_missing: bool = False,
    publish_preflight_resident_fastpath_handoff_ready: bool = True,
    publish_preflight_resident_fastpath_handoff_raw_status: str = "passed",
    publish_preflight_resident_fastpath_handoff_phase2_status: str = "passed",
    publish_preflight_resident_fastpath_handoff_raw_check_count: int = 31,
    publish_preflight_resident_result_contract_ready: bool = True,
    publish_preflight_resident_result_contract_status: str = "passed",
    publish_preflight_resident_result_contract_phase2_check_passed: bool = True,
    publish_preflight_resident_result_contract_required_count: int = 1,
    publish_preflight_resident_result_contract_failed_count: int = 0,
    publish_preflight_resident_winsorized_status: str = "passed",
    publish_preflight_resident_winsorized_required_frame_passed: bool = True,
    publish_preflight_resident_winsorized_check_count: int = 27,
    publish_preflight_stack_publication_status: str = "passed",
    publish_preflight_stack_publication_ready: bool = True,
    publish_preflight_stack_publication_policy_agreement: bool = True,
    publish_preflight_stack_publication_resident_winsorized_agreement: bool = True,
    publish_preflight_quality_metrics_compare_present: bool = True,
    publish_preflight_quality_metrics_compare_ready: bool = True,
    publish_preflight_quality_metrics_compare_status: str = "passed",
    publish_preflight_quality_metrics_compare_failed_check_count: int = 0,
    stack_publication_passed: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
    stack_publication_resident_result_contract_ready: bool = True,
    pipeline_passed: bool = True,
    pipeline_dq_contract: bool = True,
    pixel_verification: bool = True,
    pipeline_rejection_sample_check_present: bool = True,
    pipeline_rejection_sample_status: str = "passed",
    pipeline_sample_closure_check_present: bool = True,
    pipeline_sample_closure_status: str = "passed",
    pipeline_engine_policy_check_present: bool = True,
    pipeline_engine_policy_status: str = "passed",
    pipeline_runtime_default_check_present: bool = True,
    pipeline_runtime_default_status: str = "passed",
    pipeline_runtime_default_legacy_master_count: int = 0,
    pipeline_resident_result_check_present: bool = True,
    pipeline_resident_result_status: str = "passed",
    pipeline_resident_result_failed_count: int = 0,
    pipeline_resident_result_failed_checks: list[str] | None = None,
    stack_engine_ready: bool = True,
    stack_engine_status: str = "passed",
    stack_engine_gap_count: int = 0,
    resident_winsorized_sweep_passed: bool = True,
    resident_winsorized_sweep_required_frame_passed: bool = True,
    resident_winsorized_sweep_check_count: int = 27,
    resident_winsorized_sweep_required_frame_count: int = 200,
    default_change_ready: bool = True,
    release_recommendation: str = "promote_default_candidate",
) -> dict:
    stack_engine_recommendation = (
        "stack_engine_default_ready"
        if stack_engine_ready and stack_engine_gap_count == 0
        else "stack_engine_contract_gaps_remain"
    )
    resident_result_failed_checks = pipeline_resident_result_failed_checks or []
    publish_preflight_release_direct_publication_guard_passed = (
        publish_preflight_direct_runtime_ready
        and publish_preflight_release_direct_publication_guard_ready
        and publish_preflight_release_direct_publication_guard_lights >= 200
    )
    publish_preflight_release_quality_publication_guard_passed = (
        publish_preflight_release_quality_publication_guard_present
        and publish_preflight_release_quality_publication_guard_ready
        and publish_preflight_release_quality_publication_guard_check_passed
        and publish_preflight_release_quality_publication_guard_layers_ready
        and publish_preflight_release_quality_publication_guard_raw_status == "passed"
        and publish_preflight_release_quality_publication_guard_phase2_status
        == "passed"
    )
    if publish_preflight_release_quality_publication_guard_final_checks_passed is None:
        publish_preflight_release_quality_publication_guard_final_checks_passed = (
            publish_preflight_release_quality_publication_guard_passed
        )
    if publish_preflight_release_quality_publication_guard_final_evidence_passed is None:
        publish_preflight_release_quality_publication_guard_final_evidence_passed = (
            publish_preflight_release_quality_publication_guard_final_checks_passed
        )
    if publish_preflight_release_quality_publication_guard_present:
        release_quality_present = True
        release_quality_ready = publish_preflight_release_quality_publication_guard_ready
        release_quality_check = (
            publish_preflight_release_quality_publication_guard_check_passed
        )
        release_quality_layers = (
            publish_preflight_release_quality_publication_guard_layers_ready
        )
        release_quality_raw = (
            publish_preflight_release_quality_publication_guard_raw_status
        )
        release_quality_phase2 = (
            publish_preflight_release_quality_publication_guard_phase2_status
        )
        release_quality_passed = (
            publish_preflight_release_quality_publication_guard_passed
        )
    else:
        release_quality_present = None
        release_quality_ready = None
        release_quality_check = None
        release_quality_layers = None
        release_quality_raw = None
        release_quality_phase2 = None
        release_quality_passed = None
    publish_preflight_resident_fastpath_handoff_passed = (
        publish_preflight_resident_fastpath_handoff_ready
        and publish_preflight_resident_fastpath_handoff_raw_status == "passed"
        and publish_preflight_resident_fastpath_handoff_phase2_status == "passed"
        and publish_preflight_resident_fastpath_handoff_raw_check_count > 0
    )
    publish_preflight_resident_result_contract_passed = (
        publish_preflight_resident_result_contract_ready
        and publish_preflight_resident_result_contract_status == "passed"
        and publish_preflight_resident_result_contract_phase2_check_passed
        and publish_preflight_resident_result_contract_required_count > 0
        and publish_preflight_resident_result_contract_failed_count == 0
    )
    publish_preflight_quality_metrics_compare_passed = (
        publish_preflight_quality_metrics_compare_present
        and publish_preflight_quality_metrics_compare_ready
        and publish_preflight_quality_metrics_compare_status == "passed"
        and publish_preflight_quality_metrics_compare_failed_check_count == 0
    )
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "status": status,
        "passed": status == "green",
        "latest_checkpoint": {
            "gate": gate,
            "status": "green" if checkpoint_green else "failed",
            "green": checkpoint_green,
        },
        "acceptance_audit": {
            "status": acceptance_status,
            "passed": acceptance_passed,
            "pipeline_integration_engine_policy_status": (
                acceptance_pipeline_engine_policy_status
            ),
            "pipeline_integration_engine_policy_check_present": (
                acceptance_pipeline_engine_policy_check_present
            ),
            "pipeline_integration_engine_policy_check_passed": (
                acceptance_pipeline_engine_policy_check_passed
            ),
            "pipeline_stack_engine_runtime_default_status": (
                acceptance_pipeline_runtime_default_status
            ),
            "pipeline_stack_engine_runtime_default_check_present": (
                acceptance_pipeline_runtime_default_check_present
            ),
            "pipeline_stack_engine_runtime_default_check_passed": (
                acceptance_pipeline_runtime_default_check_passed
            ),
            "pipeline_stack_engine_runtime_default_master_count": 1,
            "pipeline_stack_engine_runtime_default_legacy_master_count": (
                acceptance_pipeline_runtime_default_legacy_master_count
            ),
            "pipeline_stack_engine_runtime_default_failed_master_count": (
                acceptance_pipeline_runtime_default_legacy_master_count
            ),
            "pipeline_stack_engine_runtime_default_failed_output_count": 0,
            "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": 0,
            "resident_registration_fastpath_contract_status": fastpath_contract_status,
            "resident_registration_fastpath_contract_check_count": fastpath_contract_check_count,
        },
        "default_route_acceptance": {
            "status": "passed" if default_route_passed else "failed",
            "passed": default_route_passed,
            "route_contract_passed": default_route_contract_passed,
        },
        "doctor": {"cuda_available": cuda_available},
        "release_manifest": {"status": release_status},
        "github_release_plan": {"status": github_status},
        "publish_preflight": {
            "status": publish_preflight_status,
            "github_plan_phase2_rejection_sample_accounting_status": (
                publish_preflight_rejection_sample_status
            ),
            "github_plan_matrix_rejection_sample_accounting_status": (
                publish_preflight_rejection_sample_status
            ),
            "matrix_rejection_sample_accounting_status": (
                publish_preflight_rejection_sample_status
            ),
            "default_promotion_rejection_sample_accounting_status": (
                publish_preflight_rejection_sample_status
            ),
            "github_plan_phase2_sample_accounting_closure_status": (
                publish_preflight_sample_closure_status
            ),
            "github_plan_matrix_sample_accounting_closure_status": (
                publish_preflight_sample_closure_status
            ),
            "matrix_sample_accounting_closure_status": (
                publish_preflight_sample_closure_status
            ),
            "default_promotion_sample_accounting_closure_status": (
                publish_preflight_sample_closure_status
            ),
            "matrix_integration_engine_policy_ready": (
                publish_preflight_integration_engine_policy_ready
            ),
            "matrix_acceptance_integration_engine_policy_status": (
                publish_preflight_integration_engine_policy_status
            ),
            "matrix_pipeline_integration_engine_policy_status": (
                publish_preflight_integration_engine_policy_status
            ),
            "default_promotion_integration_engine_policy_ready": (
                publish_preflight_integration_engine_policy_ready
            ),
            "default_promotion_acceptance_integration_engine_policy_status": (
                publish_preflight_integration_engine_policy_status
            ),
            "default_promotion_pipeline_integration_engine_policy_status": (
                publish_preflight_integration_engine_policy_status
            ),
            "github_plan_phase2_stack_engine_contract_status": (
                publish_preflight_stack_engine_status
            ),
            "github_plan_matrix_stack_engine_contract_status": (
                publish_preflight_stack_engine_status
            ),
            "matrix_stack_engine_contract_status": (
                publish_preflight_stack_engine_status
            ),
            "default_promotion_stack_engine_contract_status": (
                publish_preflight_stack_engine_status
            ),
            "matrix_stack_engine_contract_default_gap_count": (
                0 if publish_preflight_stack_engine_status == "passed" else 1
            ),
            "default_promotion_stack_engine_contract_default_gap_count": (
                0 if publish_preflight_stack_engine_status == "passed" else 1
            ),
            "matrix_stack_engine_runtime_default_ready": (
                publish_preflight_stack_runtime_default_ready
            ),
            "matrix_acceptance_stack_engine_runtime_default_status": (
                publish_preflight_stack_runtime_default_status
            ),
            "matrix_pipeline_stack_engine_runtime_default_status": (
                publish_preflight_stack_runtime_default_status
            ),
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count": (
                publish_preflight_stack_runtime_default_legacy_master_count
            ),
            "matrix_stack_engine_runtime_default_pipeline_failed_output_count": (
                publish_preflight_stack_runtime_default_failed_output_count
            ),
            "default_promotion_stack_engine_runtime_default_ready": (
                publish_preflight_stack_runtime_default_ready
            ),
            "default_promotion_acceptance_stack_engine_runtime_default_status": (
                publish_preflight_stack_runtime_default_status
            ),
            "default_promotion_pipeline_stack_engine_runtime_default_status": (
                publish_preflight_stack_runtime_default_status
            ),
            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count": (
                publish_preflight_stack_runtime_default_legacy_master_count
            ),
            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count": (
                publish_preflight_stack_runtime_default_failed_output_count
            ),
            "matrix_resident_winsorized_sweep_status": (
                publish_preflight_resident_winsorized_status
            ),
            "matrix_resident_winsorized_sweep_required_frame_count": 200,
            "matrix_resident_winsorized_sweep_required_frame_count_passed": (
                publish_preflight_resident_winsorized_required_frame_passed
            ),
            "matrix_resident_winsorized_sweep_check_count": (
                publish_preflight_resident_winsorized_check_count
            ),
            "default_promotion_resident_winsorized_sweep_status": (
                publish_preflight_resident_winsorized_status
            ),
            "default_promotion_resident_winsorized_sweep_required_frame_count": 200,
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
                publish_preflight_resident_winsorized_required_frame_passed
            ),
            "default_promotion_resident_winsorized_sweep_check_count": (
                publish_preflight_resident_winsorized_check_count
            ),
            "github_plan_phase2_rejection_sample_accounting_passed": (
                publish_preflight_rejection_sample_status == "passed"
            ),
            "github_plan_matrix_rejection_sample_accounting_passed": (
                publish_preflight_rejection_sample_status == "passed"
            ),
            "matrix_rejection_sample_accounting_passed": (
                publish_preflight_rejection_sample_status == "passed"
            ),
            "default_promotion_rejection_sample_accounting_passed": (
                publish_preflight_rejection_sample_status == "passed"
            ),
            "github_plan_matrix_rejection_accounting_matches_matrix": (
                publish_preflight_rejection_sample_status == "passed"
            ),
            "github_plan_phase2_sample_accounting_closure_passed": (
                publish_preflight_sample_closure_status == "passed"
            ),
            "github_plan_matrix_sample_accounting_closure_passed": (
                publish_preflight_sample_closure_status == "passed"
            ),
            "matrix_sample_accounting_closure_passed": (
                publish_preflight_sample_closure_status == "passed"
            ),
            "default_promotion_sample_accounting_closure_passed": (
                publish_preflight_sample_closure_status == "passed"
            ),
            "github_plan_matrix_sample_closure_matches_matrix": (
                publish_preflight_sample_closure_status == "passed"
            ),
            "windows_release_matrix_acceptance_integration_engine_policy_passed": (
                publish_preflight_integration_engine_policy_status == "passed"
                and publish_preflight_integration_engine_policy_ready
            ),
            "windows_release_matrix_pipeline_integration_engine_policy_passed": (
                publish_preflight_integration_engine_policy_status == "passed"
                and publish_preflight_integration_engine_policy_ready
            ),
            "default_promotion_acceptance_integration_engine_policy_passed": (
                publish_preflight_integration_engine_policy_status == "passed"
                and publish_preflight_integration_engine_policy_ready
            ),
            "default_promotion_pipeline_integration_engine_policy_passed": (
                publish_preflight_integration_engine_policy_status == "passed"
                and publish_preflight_integration_engine_policy_ready
            ),
            "matrix_integration_engine_policy_matches_default_promotion": (
                publish_preflight_integration_engine_policy_status == "passed"
                and publish_preflight_integration_engine_policy_ready
            ),
            "github_plan_phase2_stack_engine_default_contract_ready": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "github_plan_matrix_stack_engine_contract_ready": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "github_plan_stack_engine_contract_agreement_passed": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "matrix_stack_engine_contract_ready": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "default_promotion_stack_engine_contract_ready": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "github_plan_matrix_stack_engine_contract_matches_matrix": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "matrix_stack_engine_contract_matches_default_promotion": (
                publish_preflight_stack_engine_status == "passed"
            ),
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed": (
                publish_preflight_stack_runtime_default_status == "passed"
                and publish_preflight_stack_runtime_default_ready
                and publish_preflight_stack_runtime_default_legacy_master_count == 0
            ),
            "windows_release_matrix_pipeline_stack_engine_runtime_default_passed": (
                publish_preflight_stack_runtime_default_status == "passed"
                and publish_preflight_stack_runtime_default_ready
                and publish_preflight_stack_runtime_default_failed_output_count == 0
            ),
            "default_promotion_acceptance_stack_engine_runtime_default_passed": (
                publish_preflight_stack_runtime_default_status == "passed"
                and publish_preflight_stack_runtime_default_ready
                and publish_preflight_stack_runtime_default_legacy_master_count == 0
            ),
            "default_promotion_pipeline_stack_engine_runtime_default_passed": (
                publish_preflight_stack_runtime_default_status == "passed"
                and publish_preflight_stack_runtime_default_ready
                and publish_preflight_stack_runtime_default_failed_output_count == 0
            ),
            "matrix_stack_engine_runtime_default_matches_default_promotion": (
                publish_preflight_stack_runtime_default_status == "passed"
                and publish_preflight_stack_runtime_default_ready
                and publish_preflight_stack_runtime_default_legacy_master_count == 0
                and publish_preflight_stack_runtime_default_failed_output_count == 0
            ),
            "matrix_direct_runtime_evidence_ready": (
                publish_preflight_direct_runtime_ready
            ),
            "matrix_direct_runtime_acceptance_source": (
                publish_preflight_direct_runtime_acceptance_source
            ),
            "matrix_direct_runtime_acceptance_check_count": (
                24 if publish_preflight_direct_runtime_ready else 0
            ),
            "matrix_direct_runtime_pipeline_calibration_source": (
                publish_preflight_direct_runtime_pipeline_source
            ),
            "matrix_direct_runtime_pipeline_resident_lights": (
                publish_preflight_direct_runtime_resident_lights
                if publish_preflight_direct_runtime_ready
                else 0
            ),
            "default_promotion_direct_runtime_evidence_ready": (
                publish_preflight_direct_runtime_ready
            ),
            "default_promotion_direct_runtime_acceptance_source": (
                publish_preflight_direct_runtime_acceptance_source
            ),
            "default_promotion_direct_runtime_acceptance_check_count": (
                24 if publish_preflight_direct_runtime_ready else 0
            ),
            "default_promotion_direct_runtime_pipeline_calibration_source": (
                publish_preflight_direct_runtime_pipeline_source
            ),
            "default_promotion_direct_runtime_pipeline_resident_lights": (
                publish_preflight_direct_runtime_resident_lights
                if publish_preflight_direct_runtime_ready
                else 0
            ),
            "windows_release_matrix_direct_acceptance_fastpath_evidence": (
                publish_preflight_direct_runtime_ready
                and publish_preflight_direct_runtime_acceptance_source
                == "explicit_resident_artifacts_json"
            ),
            "windows_release_matrix_direct_pipeline_calibration_evidence": (
                publish_preflight_direct_runtime_ready
                and publish_preflight_direct_runtime_pipeline_source
                == "resident_artifacts_json_fallback"
                and publish_preflight_direct_runtime_resident_lights >= 200
            ),
            "default_promotion_direct_acceptance_fastpath_evidence": (
                publish_preflight_direct_runtime_ready
                and publish_preflight_direct_runtime_acceptance_source
                == "explicit_resident_artifacts_json"
            ),
            "default_promotion_direct_pipeline_calibration_evidence": (
                publish_preflight_direct_runtime_ready
                and publish_preflight_direct_runtime_pipeline_source
                == "resident_artifacts_json_fallback"
                and publish_preflight_direct_runtime_resident_lights >= 200
            ),
            "matrix_direct_runtime_evidence_matches_default_promotion": (
                publish_preflight_direct_runtime_ready
            ),
            "github_plan_matrix_release_direct_publication_guard_ready": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "github_plan_matrix_release_direct_publication_guard_lights": (
                publish_preflight_release_direct_publication_guard_lights
            ),
            "github_plan_matrix_default_promotion_release_direct_publication_guard_ready": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "github_plan_matrix_default_promotion_release_direct_publication_guard_lights": (
                publish_preflight_release_direct_publication_guard_lights
            ),
            "matrix_release_direct_publication_guard_ready": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_release_direct_publication_guard_source_ready": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_release_direct_publication_guard_count_ready": (
                publish_preflight_release_direct_publication_guard_lights >= 200
            ),
            "matrix_release_direct_publication_guard_check_passed": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_release_direct_publication_guard_lights": (
                publish_preflight_release_direct_publication_guard_lights
            ),
            "matrix_default_promotion_release_direct_publication_guard_ready": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_default_promotion_release_direct_publication_guard_lights": (
                publish_preflight_release_direct_publication_guard_lights
            ),
            "default_promotion_release_direct_publication_guard_ready": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "default_promotion_release_direct_publication_guard_lights": (
                publish_preflight_release_direct_publication_guard_lights
            ),
            "github_plan_matrix_release_decision_direct_publication_guard_passed": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_release_decision_direct_runtime_publication_guard_passed": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "default_promotion_release_decision_direct_runtime_publication_guard_passed": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_release_decision_direct_publication_guard_matches_default_promotion": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest": (
                publish_preflight_release_direct_publication_guard_passed
            ),
            "matrix_release_quality_publication_guard_present": (
                release_quality_present
            ),
            "matrix_release_quality_publication_guard_ready": release_quality_ready,
            "matrix_release_quality_publication_guard_check_passed": (
                release_quality_check
            ),
            "matrix_release_quality_publication_guard_layers_ready": (
                release_quality_layers
            ),
            "matrix_release_quality_publication_guard_raw_status": (
                release_quality_raw
            ),
            "matrix_release_quality_publication_guard_phase2_status": (
                release_quality_phase2
            ),
            "matrix_default_promotion_release_quality_publication_guard_ready": (
                release_quality_ready
            ),
            "matrix_default_promotion_release_quality_publication_guard_raw_status": (
                release_quality_raw
            ),
            "matrix_default_promotion_release_quality_publication_guard_phase2_status": (
                release_quality_phase2
            ),
            "default_promotion_release_quality_publication_guard_present": (
                release_quality_present
            ),
            "default_promotion_release_quality_publication_guard_ready": (
                release_quality_ready
            ),
            "default_promotion_release_quality_publication_guard_check_passed": (
                release_quality_check
            ),
            "default_promotion_release_quality_publication_guard_layers_ready": (
                release_quality_layers
            ),
            "default_promotion_release_quality_publication_guard_raw_status": (
                release_quality_raw
            ),
            "default_promotion_release_quality_publication_guard_phase2_status": (
                release_quality_phase2
            ),
            "matrix_release_decision_quality_compare_publication_guard_passed": (
                release_quality_passed
            ),
            "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed": (
                release_quality_passed
            ),
            "default_promotion_release_decision_quality_compare_publication_guard_passed": (
                release_quality_passed
            ),
            "matrix_release_decision_quality_publication_guard_matches_default_promotion": (
                release_quality_passed
            ),
            "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest": (
                release_quality_passed
            ),
            "matrix_release_decision_release_quality_publication_guard_passed": (
                publish_preflight_release_quality_publication_guard_final_checks_passed
                if publish_preflight_release_quality_publication_guard_final_checks_present
                else None
            ),
            "matrix_default_promotion_release_decision_release_quality_publication_guard_passed": (
                publish_preflight_release_quality_publication_guard_final_checks_passed
                if publish_preflight_release_quality_publication_guard_final_checks_present
                else None
            ),
            "default_promotion_release_decision_release_quality_publication_guard_passed": (
                publish_preflight_release_quality_publication_guard_final_checks_passed
                if publish_preflight_release_quality_publication_guard_final_checks_present
                else None
            ),
            "matrix_release_decision_release_quality_publication_guard_matches_default_promotion": (
                publish_preflight_release_quality_publication_guard_final_checks_passed
                if publish_preflight_release_quality_publication_guard_final_checks_present
                else None
            ),
            "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest": (
                publish_preflight_release_quality_publication_guard_final_checks_passed
                if publish_preflight_release_quality_publication_guard_final_checks_present
                else None
            ),
            **{
                f"{prefix}_{suffix}": (
                    (
                        True
                        if suffix in {"final_checks_ready", "final_checks_match"}
                        else None
                    )
                    if publish_preflight_release_quality_publication_guard_final_evidence_compatible_missing
                    else publish_preflight_release_quality_publication_guard_final_evidence_passed
                    if suffix != "final_checks_match"
                    else True
                )
                if publish_preflight_release_quality_publication_guard_final_evidence_present
                else None
                for prefix in (
                    "matrix_release_decision_release_quality_publication_guard",
                    "matrix_default_promotion_release_decision_release_quality_publication_guard",
                    "default_promotion_release_decision_release_quality_publication_guard",
                )
                for suffix in (
                    "final_checks_ready",
                    "final_checks_match",
                    "raw_final_checks_ready",
                    "phase2_final_checks_ready",
                )
            },
            "github_plan_matrix_resident_fastpath_handoff_ready": (
                publish_preflight_resident_fastpath_handoff_ready
            ),
            "github_plan_matrix_resident_fastpath_handoff_raw_status": (
                publish_preflight_resident_fastpath_handoff_raw_status
            ),
            "github_plan_matrix_resident_fastpath_handoff_phase2_status": (
                publish_preflight_resident_fastpath_handoff_phase2_status
            ),
            "github_plan_matrix_resident_fastpath_handoff_raw_check_count": (
                publish_preflight_resident_fastpath_handoff_raw_check_count
            ),
            "matrix_resident_fastpath_handoff_ready": (
                publish_preflight_resident_fastpath_handoff_ready
            ),
            "matrix_resident_fastpath_handoff_raw_status": (
                publish_preflight_resident_fastpath_handoff_raw_status
            ),
            "matrix_resident_fastpath_handoff_phase2_status": (
                publish_preflight_resident_fastpath_handoff_phase2_status
            ),
            "matrix_resident_fastpath_handoff_raw_check_count": (
                publish_preflight_resident_fastpath_handoff_raw_check_count
            ),
            "default_promotion_resident_fastpath_handoff_ready": (
                publish_preflight_resident_fastpath_handoff_ready
            ),
            "default_promotion_resident_fastpath_handoff_raw_status": (
                publish_preflight_resident_fastpath_handoff_raw_status
            ),
            "default_promotion_resident_fastpath_handoff_phase2_status": (
                publish_preflight_resident_fastpath_handoff_phase2_status
            ),
            "default_promotion_resident_fastpath_handoff_raw_check_count": (
                publish_preflight_resident_fastpath_handoff_raw_check_count
            ),
            "github_plan_matrix_resident_fastpath_release_handoff_ready": (
                publish_preflight_resident_fastpath_handoff_passed
            ),
            "matrix_resident_fastpath_release_handoff_ready": (
                publish_preflight_resident_fastpath_handoff_passed
            ),
            "default_promotion_resident_fastpath_release_handoff_ready": (
                publish_preflight_resident_fastpath_handoff_passed
            ),
            "github_plan_matrix_resident_fastpath_handoff_matches_matrix": (
                publish_preflight_resident_fastpath_handoff_passed
            ),
            "matrix_resident_fastpath_handoff_matches_default_promotion": (
                publish_preflight_resident_fastpath_handoff_passed
            ),
            "matrix_quality_metrics_compare_present": (
                publish_preflight_quality_metrics_compare_present
            ),
            "matrix_quality_metrics_compare_ready": (
                publish_preflight_quality_metrics_compare_ready
            ),
            "matrix_quality_metrics_compare_status": (
                publish_preflight_quality_metrics_compare_status
            ),
            "matrix_quality_metrics_compare_failed_check_count": (
                publish_preflight_quality_metrics_compare_failed_check_count
            ),
            "default_promotion_quality_metrics_compare_present": (
                publish_preflight_quality_metrics_compare_present
            ),
            "default_promotion_quality_metrics_compare_ready": (
                publish_preflight_quality_metrics_compare_ready
            ),
            "default_promotion_quality_metrics_compare_status": (
                publish_preflight_quality_metrics_compare_status
            ),
            "default_promotion_quality_metrics_compare_failed_check_count": (
                publish_preflight_quality_metrics_compare_failed_check_count
            ),
            "windows_release_matrix_quality_metrics_compare_handoff_passed": (
                publish_preflight_quality_metrics_compare_passed
            ),
            "default_promotion_quality_metrics_compare_handoff_passed": (
                publish_preflight_quality_metrics_compare_passed
            ),
            "matrix_quality_metrics_compare_matches_default_promotion": (
                publish_preflight_quality_metrics_compare_passed
            ),
            "github_plan_matrix_resident_result_contract_ready": (
                publish_preflight_resident_result_contract_ready
            ),
            "github_plan_matrix_resident_result_contract_status": (
                publish_preflight_resident_result_contract_status
            ),
            "github_plan_matrix_resident_result_contract_phase2_check_passed": (
                publish_preflight_resident_result_contract_phase2_check_passed
            ),
            "github_plan_matrix_resident_result_contract_required_count": (
                publish_preflight_resident_result_contract_required_count
            ),
            "github_plan_matrix_resident_result_contract_failed_count": (
                publish_preflight_resident_result_contract_failed_count
            ),
            "matrix_resident_result_contract_ready": (
                publish_preflight_resident_result_contract_ready
            ),
            "matrix_resident_result_contract_status": (
                publish_preflight_resident_result_contract_status
            ),
            "matrix_resident_result_contract_phase2_check_passed": (
                publish_preflight_resident_result_contract_phase2_check_passed
            ),
            "matrix_resident_result_contract_required_count": (
                publish_preflight_resident_result_contract_required_count
            ),
            "matrix_resident_result_contract_failed_count": (
                publish_preflight_resident_result_contract_failed_count
            ),
            "default_promotion_resident_result_contract_ready": (
                publish_preflight_resident_result_contract_ready
            ),
            "default_promotion_resident_result_contract_status": (
                publish_preflight_resident_result_contract_status
            ),
            "default_promotion_resident_result_contract_phase2_check_passed": (
                publish_preflight_resident_result_contract_phase2_check_passed
            ),
            "default_promotion_resident_result_contract_required_count": (
                publish_preflight_resident_result_contract_required_count
            ),
            "default_promotion_resident_result_contract_failed_count": (
                publish_preflight_resident_result_contract_failed_count
            ),
            "github_plan_matrix_resident_result_contract_handoff_passed": (
                publish_preflight_resident_result_contract_passed
            ),
            "matrix_resident_result_contract_handoff_passed": (
                publish_preflight_resident_result_contract_passed
            ),
            "default_promotion_resident_result_contract_handoff_passed": (
                publish_preflight_resident_result_contract_passed
            ),
            "github_plan_matrix_resident_result_contract_matches_matrix": (
                publish_preflight_resident_result_contract_passed
            ),
            "matrix_resident_result_contract_matches_default_promotion": (
                publish_preflight_resident_result_contract_passed
            ),
            "matrix_resident_winsorized_sweep_audit_passed": (
                publish_preflight_resident_winsorized_status == "passed"
            ),
            "matrix_resident_winsorized_required_frame_passed": (
                publish_preflight_resident_winsorized_required_frame_passed
            ),
            "matrix_resident_winsorized_sweep_check_count_passed": (
                publish_preflight_resident_winsorized_check_count > 0
            ),
            "default_promotion_resident_winsorized_sweep_audit_passed": (
                publish_preflight_resident_winsorized_status == "passed"
            ),
            "default_promotion_resident_winsorized_required_frame_passed": (
                publish_preflight_resident_winsorized_required_frame_passed
            ),
            "default_promotion_resident_winsorized_sweep_matches_matrix": (
                publish_preflight_resident_winsorized_status == "passed"
            ),
            "matrix_stack_engine_publication_audit_status": (
                publish_preflight_stack_publication_status
            ),
            "matrix_stack_engine_publication_audit_ready": (
                publish_preflight_stack_publication_ready
            ),
            "matrix_stack_engine_publication_policy_agreement": (
                publish_preflight_stack_publication_policy_agreement
            ),
            "matrix_stack_engine_publication_resident_winsorized_agreement": (
                publish_preflight_stack_publication_resident_winsorized_agreement
            ),
            "default_promotion_stack_engine_publication_audit_status": (
                publish_preflight_stack_publication_status
            ),
            "default_promotion_stack_engine_publication_audit_ready": (
                publish_preflight_stack_publication_ready
            ),
            "default_promotion_stack_engine_publication_policy_agreement": (
                publish_preflight_stack_publication_policy_agreement
            ),
            "default_promotion_stack_engine_publication_resident_winsorized_agreement": (
                publish_preflight_stack_publication_resident_winsorized_agreement
            ),
            "matrix_stack_engine_publication_audit_passed": (
                publish_preflight_stack_publication_status == "passed"
                and publish_preflight_stack_publication_ready
            ),
            "matrix_stack_engine_publication_policy_chain_passed": (
                publish_preflight_stack_publication_policy_agreement
            ),
            "matrix_stack_engine_publication_resident_winsorized_chain_passed": (
                publish_preflight_stack_publication_resident_winsorized_agreement
            ),
            "default_promotion_stack_engine_publication_audit_passed": (
                publish_preflight_stack_publication_status == "passed"
                and publish_preflight_stack_publication_ready
            ),
            "default_promotion_stack_engine_publication_policy_chain_passed": (
                publish_preflight_stack_publication_policy_agreement
            ),
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed": (
                publish_preflight_stack_publication_resident_winsorized_agreement
            ),
            "matrix_stack_engine_publication_audit_matches_default_promotion": (
                publish_preflight_stack_publication_status == "passed"
                and publish_preflight_stack_publication_ready
                and publish_preflight_stack_publication_policy_agreement
                and publish_preflight_stack_publication_resident_winsorized_agreement
            ),
        },
        "stack_engine_publication_audit": {
            "status": "passed" if stack_publication_passed else "blocked",
            "passed": stack_publication_passed,
            "recommendation": "publication_chain_ready"
            if stack_publication_passed
            else "fix_stack_engine_publication_chain",
            "check_count": 24,
            "failed_check_count": 0
            if (
                stack_publication_passed
                and stack_publication_policy_ready
                and stack_publication_resident_winsorized_ready
                and stack_publication_resident_result_contract_ready
                and publish_preflight_direct_runtime_ready
            )
            else 1,
            "publish_preflight_integration_engine_policy_ready": (
                stack_publication_policy_ready
            ),
            "phase2_publish_preflight_integration_engine_policy_ready": (
                stack_publication_policy_ready
            ),
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight": (
                stack_publication_policy_ready
            ),
            "publish_preflight_resident_winsorized_sweep_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_publish_preflight_resident_winsorized_sweep_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight": (
                stack_publication_resident_winsorized_ready
            ),
            "publish_preflight_resident_result_contract_ready": (
                stack_publication_resident_result_contract_ready
            ),
            "phase2_publish_preflight_resident_result_contract_ready": (
                stack_publication_resident_result_contract_ready
            ),
            "phase2_publish_preflight_resident_result_contract_matches_publish_preflight": (
                stack_publication_resident_result_contract_ready
            ),
            "publish_preflight_direct_runtime_evidence_ready": (
                publish_preflight_direct_runtime_ready
            ),
            "phase2_publish_preflight_direct_runtime_evidence_ready": (
                publish_preflight_direct_runtime_ready
            ),
            "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight": (
                publish_preflight_direct_runtime_ready
            ),
        },
        "pipeline_contract": {
            "status": "passed" if pipeline_passed else "failed",
            "passed": pipeline_passed,
            "integration_default_engine_policy": (
                pipeline_engine_policy_status == "passed"
            )
            if pipeline_engine_policy_check_present
            else None,
            "integration_engine_policy_status": pipeline_engine_policy_status,
            "integration_engine_policy": {
                "status": pipeline_engine_policy_status,
                "check_present": pipeline_engine_policy_check_present,
                "check_passed": (pipeline_engine_policy_status == "passed")
                if pipeline_engine_policy_check_present
                else None,
                "non_resident_count": 0 if pipeline_engine_policy_status == "passed" else 1,
                "resident_count": 1 if pipeline_engine_policy_status == "passed" else 0,
                "failed_count": 0 if pipeline_engine_policy_status == "passed" else 1,
                "failed_items": []
                if pipeline_engine_policy_status == "passed"
                else [
                    {
                        "item": "H",
                        "status": pipeline_engine_policy_status,
                        "backend": "cuda",
                        "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                        "failures": ["cuda_fast_path_not_explicit"],
                    }
                ],
            },
            "stack_engine_runtime_default": {
                "status": pipeline_runtime_default_status,
                "check_present": pipeline_runtime_default_check_present,
                "check_passed": (pipeline_runtime_default_status == "passed")
                if pipeline_runtime_default_check_present
                else None,
                "master_count": 1,
                "master_stack_engine_count": 1
                if pipeline_runtime_default_status == "passed"
                else 0,
                "master_resident_count": 0,
                "legacy_master_count": pipeline_runtime_default_legacy_master_count,
                "integration_output_count": 1,
                "integration_stack_engine_default_count": 0,
                "integration_resident_count": 1,
                "explicit_cuda_fast_path_count": 0,
                "failed_master_count": pipeline_runtime_default_legacy_master_count,
                "failed_output_count": 0,
                "failed_masters": []
                if pipeline_runtime_default_legacy_master_count == 0
                else [
                    {
                        "name": "bias_legacy",
                        "tile_stack_mode": "legacy_streaming_accumulator",
                        "status": "failed",
                    }
                ],
                "failed_outputs": [],
            },
            "integration_dq_contract": pipeline_dq_contract,
            "integration_resident_result_contract": (
                pipeline_resident_result_status == "passed"
            )
            if pipeline_resident_result_check_present
            else None,
            "resident_result_contract": {
                "status": pipeline_resident_result_status,
                "check_present": pipeline_resident_result_check_present,
                "check_passed": (pipeline_resident_result_status == "passed")
                if pipeline_resident_result_check_present
                else None,
                "required_count": 1 if pipeline_resident_result_check_present else 0,
                "failed_count": pipeline_resident_result_failed_count,
                "failed_check_count": len(resident_result_failed_checks),
                "failed_checks": resident_result_failed_checks,
                "failed_items": []
                if pipeline_resident_result_failed_count == 0
                else [
                    {
                        "item": "H",
                        "backend": "cuda_resident_stack",
                        "memory_mode": "resident",
                        "status": pipeline_resident_result_status,
                        "required": True,
                        "passed": False,
                        "failed_checks": [
                            {"name": name, "evidence": {"required": True}}
                            for name in resident_result_failed_checks
                        ],
                    }
                ],
            },
            "pixel_verification_enabled": pixel_verification,
            "integration_rejection_sample_counts_match_maps": (
                pipeline_rejection_sample_status == "passed"
            )
            if pipeline_rejection_sample_check_present
            else None,
            "rejection_sample_accounting": {
                "status": pipeline_rejection_sample_status,
                "check_present": pipeline_rejection_sample_check_present,
                "check_passed": (pipeline_rejection_sample_status == "passed")
                if pipeline_rejection_sample_check_present
                else None,
                "failed_count": 0 if pipeline_rejection_sample_status == "passed" else 1,
            },
            "integration_sample_accounting_closure": (
                pipeline_sample_closure_status == "passed"
            )
            if pipeline_sample_closure_check_present
            else None,
            "sample_accounting_closure": {
                "status": pipeline_sample_closure_status,
                "check_present": pipeline_sample_closure_check_present,
                "check_passed": (pipeline_sample_closure_status == "passed")
                if pipeline_sample_closure_check_present
                else None,
                "present_count": 1 if pipeline_sample_closure_check_present else 0,
                "failed_count": 0 if pipeline_sample_closure_status == "passed" else 1,
            },
        },
        "stack_engine_contract": {
            "audit_type": "stack_engine_default_contract",
            "status": stack_engine_status,
            "passed": stack_engine_status == "passed",
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "adoption_recommendation": stack_engine_recommendation,
            "adoption_phase2_stack_engine_default_gap_count": stack_engine_gap_count,
            "default_promotion_ready": stack_engine_ready,
            "default_promotion_status": "ready" if stack_engine_ready else "blocked",
            "default_promotion_recommendation": stack_engine_recommendation,
            "default_promotion_phase2_stack_engine_default_gap_count": (
                stack_engine_gap_count
            ),
            "default_promotion_blocker_count": 0 if stack_engine_ready else 1,
        },
        "resident_winsorized_sweep_audit": {
            "schema_version": 1,
            "status": "passed" if resident_winsorized_sweep_passed else "failed",
            "passed": resident_winsorized_sweep_passed,
            "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
            "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
            "check_count": resident_winsorized_sweep_check_count,
            "failed_check_count": 0 if resident_winsorized_sweep_passed else 1,
            "failed_checks": []
            if resident_winsorized_sweep_passed
            else ["frame_200_hardened_master_rms_within_contract"],
            "frame_counts": [8, 32, 128, 200],
            "run_count": 4,
            "required_frame_count": resident_winsorized_sweep_required_frame_count,
            "required_frame_count_passed": resident_winsorized_sweep_required_frame_passed,
            "required_frame_master_rms": 2.3e-5,
            "required_frame_master_max_abs": 6.1e-5,
            "max_hardened_master_rms": 2.3e-5,
        },
        "release_decision": {
            "status": "default_change_ready" if default_change_ready else "release_candidate_ready",
            "default_change_ready": default_change_ready,
            "recommendation": release_recommendation,
        },
        "checks": [],
    }


def test_phase2_status_summarizes_green_handoff(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=201)
    latest = _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    default_route_acceptance = tmp_path / "default_route_acceptance.json"
    release = tmp_path / "release_manifest.json"
    github_plan = tmp_path / "github_release_plan.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    publication_audit = tmp_path / "stack_engine_publication_audit.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    stack_engine_contract = tmp_path / "stack_engine_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_stack_engine_contract(stack_engine_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight)
    _write_stack_engine_publication_audit(publication_audit)
    write_json(
        release,
        {
            "status": "release_manifest_ready",
            "passed": True,
            "recommendation": "ready_for_upload",
            "package_count": 4,
            "source_stamp": "abcdef0",
        },
    )
    write_json(
        github_plan,
        {
            "status": "release_plan_ready",
            "tag": "v0.1.0-test",
            "package_count": 4,
            "publication_ready": False,
            "recommendation": "authenticate_github_cli_then_run_release_command",
            "gh": {"available": True, "auth_ok": False},
            "script": {"path": "publish.ps1", "publish_default": False},
        },
    )

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        default_route_acceptance_audit=default_route_acceptance,
        release_manifest=release,
        github_release_plan=github_plan,
        publish_preflight=publish_preflight,
        stack_engine_publication_audit=publication_audit,
        pipeline_contract=pipeline_contract,
        stack_engine_contract=stack_engine_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    assert payload["status"] == "green"
    assert payload["latest_checkpoint"]["path"] == str(latest)
    assert payload["acceptance_audit"]["speedup_vs_reference"] == 58.0
    assert payload["acceptance_audit"]["native_guardrails_bundle_status"] == "present"
    assert payload["acceptance_audit"]["resident_result_contract_source"] == "run_default"
    assert payload["acceptance_audit"]["resident_result_contract_run_default"] is True
    assert payload["acceptance_audit"]["resident_native_calibration_artifact"] is True
    assert payload["acceptance_audit"]["resident_calibrated_light_count"] == 200
    assert payload["acceptance_audit"]["resident_registration_fastpath_status"] == "present"
    assert payload["acceptance_audit"]["resident_registration_fastpath_contract_status"] == "passed"
    assert payload["acceptance_audit"]["resident_registration_fastpath_mode"] == "similarity_cuda_triangle"
    assert payload["acceptance_audit"]["pipeline_integration_engine_policy_status"] == "passed"
    assert payload["acceptance_audit"]["pipeline_integration_engine_policy_check_present"] is True
    assert payload["acceptance_audit"]["pipeline_integration_engine_policy_check_passed"] is True
    assert (
        payload["acceptance_audit"]["pipeline_stack_engine_runtime_default_status"]
        == "passed"
    )
    assert (
        payload["acceptance_audit"][
            "pipeline_stack_engine_runtime_default_check_present"
        ]
        is True
    )
    assert (
        payload["acceptance_audit"][
            "pipeline_stack_engine_runtime_default_check_passed"
        ]
        is True
    )
    assert (
        payload["acceptance_audit"][
            "pipeline_stack_engine_runtime_default_legacy_master_count"
        ]
        == 0
    )
    assert payload["acceptance_audit"]["triangle_descriptor_fit_batch"] is True
    assert payload["acceptance_audit"]["triangle_warp_batch_frame_count"] == 188
    assert payload["default_route_acceptance"]["status"] == "passed"
    assert payload["default_route_acceptance"]["passed"] is True
    assert payload["default_route_acceptance"]["route_contract_passed"] is True
    assert payload["default_route_acceptance"]["route_check_count"] == 4
    assert payload["doctor"]["primary_gpu"] == "Fixture GPU"
    assert payload["release_manifest"]["package_count"] == 4
    assert payload["github_release_plan"]["status"] == "release_plan_ready"
    assert payload["publish_preflight"]["status"] == "publish_preflight_ready"
    assert payload["stack_engine_publication_audit"]["status"] == "passed"
    assert payload["stack_engine_publication_audit"]["passed"] is True
    assert (
        payload["stack_engine_publication_audit"][
            "publish_preflight_integration_engine_policy_ready"
        ]
        is True
    )
    assert (
        payload["stack_engine_publication_audit"][
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        ]
        is True
    )
    assert (
        payload["stack_engine_publication_audit"][
            "publish_preflight_direct_runtime_evidence_ready"
        ]
        is True
    )
    assert (
        payload["stack_engine_publication_audit"][
            "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
        ]
        is True
    )
    assert payload["publish_preflight"]["asset_count"] == 4
    assert payload["publish_preflight"]["primary_package"] == "cuda13"
    assert (
        payload["publish_preflight"]["github_plan_phase2_rejection_sample_accounting_status"]
        == "passed"
    )
    assert payload["publish_preflight"]["matrix_rejection_sample_accounting_passed"] is True
    assert (
        payload["publish_preflight"]["github_plan_phase2_sample_accounting_closure_status"]
        == "passed"
    )
    assert payload["publish_preflight"]["matrix_sample_accounting_closure_passed"] is True
    assert (
        payload["publish_preflight"]["github_plan_matrix_sample_closure_matches_matrix"]
        is True
    )
    assert payload["publish_preflight"]["matrix_integration_engine_policy_ready"] is True
    assert (
        payload["publish_preflight"][
            "matrix_acceptance_integration_engine_policy_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "matrix_pipeline_integration_engine_policy_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_integration_engine_policy_ready"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_acceptance_integration_engine_policy_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_pipeline_integration_engine_policy_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "windows_release_matrix_acceptance_integration_engine_policy_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "windows_release_matrix_pipeline_integration_engine_policy_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_acceptance_integration_engine_policy_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_pipeline_integration_engine_policy_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_integration_engine_policy_matches_default_promotion"
        ]
        is True
    )
    assert (
        payload["publish_preflight"]["github_plan_phase2_stack_engine_contract_status"]
        == "passed"
    )
    assert payload["publish_preflight"]["matrix_stack_engine_contract_ready"] is True
    assert (
        payload["publish_preflight"]["matrix_stack_engine_contract_default_gap_count"]
        == 0
    )
    assert (
        payload["publish_preflight"]["matrix_stack_engine_runtime_default_ready"]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_acceptance_stack_engine_runtime_default_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_pipeline_stack_engine_runtime_default_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
        ]
        == 0
    )
    assert (
        payload["publish_preflight"][
            "matrix_stack_engine_runtime_default_pipeline_failed_output_count"
        ]
        == 0
    )
    assert (
        payload["publish_preflight"][
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_stack_engine_runtime_default_matches_default_promotion"
        ]
        is True
    )
    assert payload["publish_preflight"]["matrix_direct_runtime_evidence_ready"] is True
    assert (
        payload["publish_preflight"]["matrix_direct_runtime_acceptance_source"]
        == "explicit_resident_artifacts_json"
    )
    assert payload["publish_preflight"]["matrix_direct_runtime_acceptance_check_count"] == 24
    assert (
        payload["publish_preflight"][
            "matrix_direct_runtime_pipeline_calibration_source"
        ]
        == "resident_artifacts_json_fallback"
    )
    assert payload["publish_preflight"]["matrix_direct_runtime_pipeline_resident_lights"] == 200
    assert (
        payload["publish_preflight"][
            "default_promotion_direct_runtime_evidence_ready"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "windows_release_matrix_direct_acceptance_fastpath_evidence"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "windows_release_matrix_direct_pipeline_calibration_evidence"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_direct_acceptance_fastpath_evidence"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_direct_pipeline_calibration_evidence"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_direct_runtime_evidence_matches_default_promotion"
        ]
        is True
    )
    assert (
        payload["publish_preflight"]["matrix_resident_winsorized_sweep_status"]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "matrix_resident_winsorized_sweep_required_frame_count"
        ]
        == 200
    )
    assert (
        payload["publish_preflight"][
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"]["matrix_resident_winsorized_sweep_check_count"]
        == 27
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_resident_winsorized_sweep_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_resident_winsorized_sweep_check_count"
        ]
        == 27
    )
    assert (
        payload["publish_preflight"][
            "matrix_resident_winsorized_sweep_check_count_passed"
        ]
        is True
    )
    assert (
        payload["publish_preflight"]["matrix_stack_engine_publication_audit_status"]
        == "passed"
    )
    assert (
        payload["publish_preflight"]["matrix_stack_engine_publication_audit_ready"]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_stack_engine_publication_policy_agreement"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_stack_engine_publication_resident_winsorized_agreement"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_stack_engine_publication_audit_status"
        ]
        == "passed"
    )
    assert (
        payload["publish_preflight"][
            "default_promotion_stack_engine_publication_audit_ready"
        ]
        is True
    )
    assert (
        payload["publish_preflight"][
            "matrix_stack_engine_publication_audit_matches_default_promotion"
        ]
        is True
    )
    assert payload["pipeline_contract"]["status"] == "passed"
    assert payload["pipeline_contract"]["integration_dq_contract"] is True
    assert payload["pipeline_contract"]["integration_resident_result_contract"] is True
    resident_result = payload["pipeline_contract"]["resident_result_contract"]
    assert resident_result["status"] == "passed"
    assert resident_result["check_present"] is True
    assert resident_result["failed_count"] == 0
    assert resident_result["failed_check_count"] == 0
    assert payload["pipeline_contract"]["integration_default_engine_policy"] is True
    assert payload["pipeline_contract"]["integration_engine_policy_status"] == "passed"
    assert payload["pipeline_contract"]["integration_engine_policy_check_present"] is True
    assert payload["pipeline_contract"]["stack_engine_runtime_default_status"] == "passed"
    assert (
        payload["pipeline_contract"]["stack_engine_runtime_default_check_present"]
        is True
    )
    assert (
        payload["pipeline_contract"]["stack_engine_runtime_default_check_passed"]
        is True
    )
    assert (
        payload["pipeline_contract"]["stack_engine_runtime_default_legacy_master_count"]
        == 0
    )
    assert payload["pipeline_contract"]["integration_stack_result_contract"] is True
    assert payload["pipeline_contract"]["pixel_verification_enabled"] is True
    assert payload["pipeline_contract"]["integration_dq_map_pixels_match_summary"] is True
    assert payload["pipeline_contract"]["integration_rejection_sample_counts_match_maps"] is True
    assert payload["pipeline_contract"]["rejection_sample_accounting_status"] == "passed"
    assert payload["pipeline_contract"]["rejection_sample_accounting_failed_count"] == 0
    assert payload["pipeline_contract"]["integration_sample_accounting_closure"] is True
    assert payload["pipeline_contract"]["sample_accounting_closure_status"] == "passed"
    assert payload["pipeline_contract"]["sample_accounting_closure_present_count"] == 1
    assert payload["pipeline_contract"]["sample_accounting_closure_failed_count"] == 0
    assert payload["stack_engine_contract"]["status"] == "passed"
    assert payload["stack_engine_contract"]["default_promotion_ready"] is True
    assert payload["stack_engine_contract"]["adoption_recommendation"] == "stack_engine_default_ready"
    assert payload["stack_engine_contract"]["adoption_phase2_stack_engine_default_gap_count"] == 0
    assert payload["release_decision"]["status"] == "default_change_ready"
    assert payload["release_decision"]["default_change_ready"] is True
    assert payload["release_decision"]["recommendation"] == "promote_default_candidate"
    assert payload["release_decision"]["runtime_repeat_elapsed_ratio_vs_best"] == 1.053
    assert payload["release_decision_runtime_repeat_closure"]["status"] == "passed"
    assert payload["release_decision_runtime_repeat_closure"]["ready"] is True
    assert payload["release_decision_runtime_repeat_closure"]["run_count"] == 3
    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert checks["resident_registration_fastpath_contract_passed_for_default"] is True
    assert checks["acceptance_pipeline_integration_engine_policy_passed"] is True
    assert checks["acceptance_pipeline_stack_engine_runtime_default_passed"] is True
    assert checks["default_route_acceptance_passed"] is True
    assert checks["default_route_acceptance_route_contract_passed"] is True
    assert checks["pipeline_integration_engine_policy_passed"] is True
    assert checks["pipeline_resident_result_contract_passed"] is True
    assert checks["pipeline_stack_engine_runtime_default_passed"] is True
    assert checks["pipeline_rejection_sample_accounting_passed"] is True
    assert checks["pipeline_sample_accounting_closure_passed"] is True
    assert checks["stack_engine_default_contract_ready"] is True
    assert checks["windows_publish_preflight_ready"] is True
    assert checks["windows_publish_preflight_rejection_sample_accounting_passed"] is True
    assert checks["windows_publish_preflight_sample_accounting_closure_passed"] is True
    assert checks["windows_publish_preflight_integration_engine_policy_passed"] is True
    assert checks["windows_publish_preflight_stack_engine_default_contract_ready"] is True
    assert checks["windows_publish_preflight_stack_engine_runtime_default_passed"] is True
    assert checks["windows_publish_preflight_direct_runtime_evidence_passed"] is True
    assert checks["windows_publish_preflight_resident_winsorized_sweep_passed"] is True
    assert (
        checks["windows_publish_preflight_stack_engine_publication_audit_passed"]
        is True
    )
    assert checks["stack_engine_publication_audit_passed"] is True
    assert checks["stack_engine_publication_audit_policy_chain_passed"] is True
    assert (
        checks["stack_engine_publication_audit_resident_winsorized_chain_passed"]
        is True
    )
    assert checks["stack_engine_publication_audit_direct_runtime_chain_passed"] is True
    assert checks["release_decision_runtime_repeat_evidence_ready"] is True


def test_phase2_status_surfaces_release_warp_quality_handoff(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=325)
    release_decision = tmp_path / "release_decision.json"
    out_md = tmp_path / "phase2.md"
    _write_release_decision(release_decision, warp_quality_ready=True)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    decision = payload["release_decision"]
    assert payload["status"] == "green"
    assert decision["warp_quality_handoff_status"] == "passed"
    assert decision["warp_quality_handoff_ready"] is True
    assert decision["warp_quality_handoff_output_count"] == 1
    assert checks["release_decision_warp_quality_handoff_ready"]["passed"] is True

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Warp quality handoff: passed ready=True outputs=1 failed=[]" in text


def test_phase2_status_surfaces_accepted_registration_admission(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=353)
    registration = tmp_path / "registration_results.json"
    out_md = tmp_path / "phase2.md"
    _write_registration_results(registration, admission_status="accepted")

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        registration_results=registration,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "green"
    assert payload["registration_admission"]["status"] == "accepted"
    assert payload["registration_admission"]["passed"] is True
    assert checks["registration_reference_admission_not_blocked"]["passed"] is True

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Registration admission: accepted passed=True blocked=False" in text


def test_phase2_status_blocks_registration_admission_failure(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=353)
    registration = tmp_path / "registration_results.json"
    out_md = tmp_path / "phase2.md"
    _write_registration_results(registration, admission_status="blocked")

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        registration_results=registration,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert payload["registration_admission"]["status"] == "blocked"
    assert payload["registration_admission"]["blocked"] is True
    check = checks["registration_reference_admission_not_blocked"]
    assert check["passed"] is False
    assert check["evidence"]["reason"] == "reference frame failed the quality gate"
    assert check["evidence"]["quality_reference_admission_row_count"] == 1

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Registration admission: blocked passed=False blocked=True" in text
    assert "reference frame failed the quality gate" in text


def test_phase2_status_surfaces_quality_saturation_summary(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=356)
    quality = tmp_path / "frame_quality.json"
    out_md = tmp_path / "phase2.md"
    _write_quality_results(quality)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        quality_results=quality,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    summary = payload["quality_saturation"]
    assert payload["status"] == "green"
    assert summary["status"] == "passed"
    assert summary["passed"] is True
    assert summary["frame_count"] == 2
    assert summary["saturated_frame_count"] == 1
    assert summary["quality_gate_saturation_rejected_count"] == 0
    assert summary["worst_frame_id"] == "F_SAT"
    assert checks["quality_saturation_no_rejections"]["passed"] is True

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Quality Saturation" in text
    assert "Quality saturation: passed passed=True" in text
    assert "saturation_rejected=0" in text


def test_phase2_status_surfaces_quality_metric_summary(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=358)
    quality = tmp_path / "frame_quality.json"
    out_md = tmp_path / "phase2.md"
    _write_quality_results(quality)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        quality_results=quality,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    summary = payload["quality_metrics"]
    metric_rows = {item["metric"]: item for item in summary["summary_rows"]}
    assert payload["status"] == "green"
    assert summary["status"] == "passed"
    assert summary["metric_count"] == 7
    assert summary["frame_count"] == 2
    assert metric_rows["fwhm_px"]["worst_frame_id"] == "F_SAT"
    assert metric_rows["snr"]["worst_frame_id"] == "F_SAT"
    assert checks["quality_metric_summary_available"]["passed"] is True

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Quality Metrics" in text
    assert "Quality metrics: passed metrics=7 frames=2" in text
    assert "fwhm_px: median=3.95" in text


def test_phase2_status_surfaces_quality_metrics_compare(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=360)
    compare = tmp_path / "quality_metrics_compare.json"
    out_md = tmp_path / "phase2.md"
    _write_quality_metrics_compare(compare)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        quality_metrics_compare=compare,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    summary = payload["quality_metrics_compare"]
    assert payload["status"] == "green"
    assert summary["status"] == "passed"
    assert summary["passed"] is True
    assert summary["baseline_metric_count"] == 7
    assert summary["candidate_metric_count"] == 7
    assert summary["failed_check_count"] == 0
    assert checks["quality_metrics_compare_passed"]["passed"] is True

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Quality Metrics Compare" in text
    assert "Quality metrics compare: passed passed=True" in text


def test_phase2_status_blocks_failed_quality_metrics_compare(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=360)
    compare = tmp_path / "quality_metrics_compare.json"
    _write_quality_metrics_compare(compare, passed=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        quality_metrics_compare=compare,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    summary = payload["quality_metrics_compare"]
    assert payload["status"] == "attention_required"
    assert summary["status"] == "failed"
    assert summary["passed"] is False
    assert summary["failed_check_count"] == 1
    assert summary["threshold_failure_count"] == 1
    assert summary["threshold_failures"] == [
        {"metric": "fwhm_px", "bad_median_ratio": 1.4}
    ]
    assert checks["quality_metrics_compare_passed"]["passed"] is False


def test_phase2_status_blocks_quality_saturation_rejection(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=356)
    quality = tmp_path / "frame_quality.json"
    _write_quality_results(quality, rejected=True)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        quality_results=quality,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    summary = payload["quality_saturation"]
    assert payload["status"] == "attention_required"
    assert summary["status"] == "attention_required"
    assert summary["passed"] is False
    assert summary["quality_gate_saturation_rejected_count"] == 1
    assert summary["rejected_frame_ids"] == ["F_SAT"]
    check = checks["quality_saturation_no_rejections"]
    assert check["passed"] is False
    assert check["evidence"]["quality_gate_saturation_rejected_count"] == 1


def test_phase2_status_blocks_default_change_without_runtime_repeat(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=326)
    release_decision = tmp_path / "release_decision.json"
    out_md = tmp_path / "phase2.md"
    _write_release_decision(release_decision, include_runtime_repeat=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    closure = payload["release_decision_runtime_repeat_closure"]
    assert payload["status"] == "attention_required"
    assert checks["release_decision_default_change_ready"]["passed"] is True
    assert checks["release_decision_runtime_repeat_evidence_ready"]["passed"] is False
    assert closure["required"] is True
    assert closure["status"] == "failed"
    assert closure["ready"] is False
    assert closure["present"] is False

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert "Runtime repeat closure: failed required=True ready=False" in text


def test_phase2_status_blocks_failed_release_warp_quality_handoff(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=325)
    release_decision = tmp_path / "release_decision.json"
    _write_release_decision(release_decision, warp_quality_ready=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert payload["release_decision"]["warp_quality_handoff_status"] == "failed"
    assert checks["release_decision_warp_quality_handoff_ready"]["passed"] is False
    assert checks["release_decision_warp_quality_handoff_ready"]["evidence"][
        "failed_acceptance_checks"
    ] == ["warp_quality_contract_passed"]


def test_phase2_status_surfaces_release_resident_fastpath_handoff(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=329)
    release_decision = tmp_path / "release_decision.json"
    out_md = tmp_path / "phase2.md"
    _write_release_decision(release_decision, resident_fastpath_ready=True)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    decision = payload["release_decision"]
    assert payload["status"] == "green"
    assert decision["resident_registration_fastpath_handoff_status"] == "passed"
    assert decision["resident_registration_fastpath_handoff_ready"] is True
    assert decision["resident_registration_fastpath_handoff_required"] is True
    assert decision["resident_registration_fastpath_handoff_mode"] == (
        "similarity_cuda_triangle"
    )
    assert decision[
        "resident_registration_fastpath_handoff_descriptor_fit_batch_mode"
    ] == "native_batch_shared_reference_device"
    assert decision[
        "resident_registration_fastpath_handoff_triangle_warp_batch_frame_count"
    ] == 3
    assert checks["release_decision_resident_fastpath_handoff_ready"]["passed"] is True

    write_phase2_status_markdown(out_md, payload)
    text = out_md.read_text(encoding="utf-8")
    assert (
        "Resident fastpath handoff: passed ready=True required=True checks=23 failed=0"
        in text
    )


def test_phase2_status_blocks_failed_release_resident_fastpath_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=329)
    release_decision = tmp_path / "release_decision.json"
    _write_release_decision(release_decision, resident_fastpath_ready=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert (
        payload["release_decision"]["resident_registration_fastpath_handoff_status"]
        == "failed"
    )
    check = checks["release_decision_resident_fastpath_handoff_ready"]
    assert check["passed"] is False
    assert check["evidence"]["failed_check_count"] == 1
    assert check["evidence"]["failed_acceptance_checks"] == [
        "contract_resident_registration_fastpath_descriptor_batch_mode"
    ]


def test_phase2_status_blocks_acceptance_runtime_default_regression(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=294)
    acceptance = tmp_path / "acceptance.json"
    _write_acceptance(acceptance, runtime_default_passed=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert (
        payload["acceptance_audit"]["pipeline_stack_engine_runtime_default_status"]
        == "failed"
    )
    assert (
        payload["acceptance_audit"][
            "pipeline_stack_engine_runtime_default_legacy_master_count"
        ]
        == 1
    )
    assert checks["acceptance_pipeline_stack_engine_runtime_default_passed"][
        "passed"
    ] is False
    assert checks["acceptance_pipeline_stack_engine_runtime_default_passed"][
        "evidence"
    ]["legacy_master_count"] == 1


def test_phase2_status_blocks_pipeline_runtime_default_regression(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=294)
    pipeline_contract = tmp_path / "pipeline_contract.json"
    _write_pipeline_contract(pipeline_contract, runtime_default_passed=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        pipeline_contract=pipeline_contract,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert payload["pipeline_contract"]["stack_engine_runtime_default_status"] == "failed"
    assert (
        payload["pipeline_contract"][
            "stack_engine_runtime_default_legacy_master_count"
        ]
        == 1
    )
    assert checks["pipeline_stack_engine_runtime_default_passed"]["passed"] is False
    assert checks["pipeline_stack_engine_runtime_default_passed"]["evidence"][
        "legacy_master_count"
    ] == 1


def test_phase2_status_summarizes_resident_winsorized_benchmark_audit(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=267)
    winsorized_audit = tmp_path / "resident_winsorized_benchmark_audit.json"
    _write_resident_winsorized_benchmark_audit(winsorized_audit)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        resident_winsorized_benchmark_audit=winsorized_audit,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "green"
    assert payload["resident_winsorized_benchmark_audit"]["status"] == "passed"
    assert payload["resident_winsorized_benchmark_audit"]["contract_name"].startswith(
        "s2_gate_266"
    )
    assert payload["resident_winsorized_benchmark_audit"]["hardened_master_rms"] == 5.0e-6
    assert checks["resident_winsorized_benchmark_audit_passed"]["passed"] is True


def test_phase2_status_blocks_failed_resident_winsorized_benchmark_audit(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=267)
    winsorized_audit = tmp_path / "resident_winsorized_benchmark_audit.json"
    _write_resident_winsorized_benchmark_audit(winsorized_audit, passed=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        resident_winsorized_benchmark_audit=winsorized_audit,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert payload["resident_winsorized_benchmark_audit"]["failed_check_count"] == 1
    assert checks["resident_winsorized_benchmark_audit_passed"]["passed"] is False
    assert checks["resident_winsorized_benchmark_audit_passed"]["evidence"]["failed_checks"] == [
        "hardened_master_rms_within_contract"
    ]


def test_phase2_status_summarizes_resident_winsorized_sweep_audit(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=270)
    sweep_audit = tmp_path / "resident_winsorized_sweep_audit.json"
    _write_resident_winsorized_sweep_audit(sweep_audit)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        resident_winsorized_sweep_audit=sweep_audit,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "green"
    assert payload["resident_winsorized_sweep_audit"]["status"] == "passed"
    assert payload["resident_winsorized_sweep_audit"]["required_frame_count"] == 200
    assert payload["resident_winsorized_sweep_audit"]["required_frame_master_rms"] == 2.3e-5
    assert checks["resident_winsorized_sweep_audit_passed"]["passed"] is True


def test_phase2_status_blocks_failed_resident_winsorized_sweep_audit(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=270)
    sweep_audit = tmp_path / "resident_winsorized_sweep_audit.json"
    _write_resident_winsorized_sweep_audit(sweep_audit, passed=False)

    payload = build_phase2_status(
        checkpoint_dir=checkpoints,
        resident_winsorized_sweep_audit=sweep_audit,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "attention_required"
    assert payload["resident_winsorized_sweep_audit"]["failed_check_count"] == 1
    assert checks["resident_winsorized_sweep_audit_passed"]["passed"] is False
    assert checks["resident_winsorized_sweep_audit_passed"]["evidence"]["failed_checks"] == [
        "frame_200_hardened_master_rms_within_contract"
    ]


def test_cli_phase2_status_writes_outputs(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=202)
    acceptance = tmp_path / "acceptance.json"
    default_route_acceptance = tmp_path / "default_route_acceptance.json"
    out = tmp_path / "phase2_status.json"
    markdown = tmp_path / "phase2_status.md"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    stack_engine_contract = tmp_path / "stack_engine_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    publication_audit = tmp_path / "stack_engine_publication_audit.json"
    registration_results = tmp_path / "registration_results.json"
    quality_results = tmp_path / "frame_quality.json"
    quality_metrics_compare = tmp_path / "quality_metrics_compare.json"
    winsorized_audit = tmp_path / "resident_winsorized_benchmark_audit.json"
    winsorized_sweep_audit = tmp_path / "resident_winsorized_sweep_audit.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_stack_engine_contract(stack_engine_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight)
    _write_stack_engine_publication_audit(publication_audit)
    _write_registration_results(registration_results)
    _write_quality_results(quality_results)
    _write_quality_metrics_compare(quality_metrics_compare)
    _write_resident_winsorized_benchmark_audit(winsorized_audit)
    _write_resident_winsorized_sweep_audit(winsorized_sweep_audit)

    result = main(
        [
            "phase2-status",
            "--checkpoint-dir",
            str(checkpoints),
            "--acceptance-audit",
            str(acceptance),
            "--default-route-acceptance-audit",
            str(default_route_acceptance),
            "--pipeline-contract",
            str(pipeline_contract),
            "--stack-engine-contract",
            str(stack_engine_contract),
            "--release-decision",
            str(release_decision),
            "--publish-preflight",
            str(publish_preflight),
            "--stack-engine-publication-audit",
            str(publication_audit),
            "--registration-results",
            str(registration_results),
            "--quality-results",
            str(quality_results),
            "--quality-metrics-compare",
            str(quality_metrics_compare),
            "--resident-winsorized-benchmark-audit",
            str(winsorized_audit),
            "--resident-winsorized-sweep-audit",
            str(winsorized_sweep_audit),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--skip-cuda-probe",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "glass_phase2_status"
    assert payload["latest_checkpoint"]["gate"] == 202
    assert payload["acceptance_audit"]["contract_bundle_schema_status"] == "passed"
    assert payload["acceptance_audit"]["resident_result_contract_source"] == "run_default"
    assert payload["default_route_acceptance"]["route_contract_passed"] is True
    assert payload["pipeline_contract"]["integration_dq_contract"] is True
    assert payload["stack_engine_contract"]["default_promotion_ready"] is True
    assert payload["resident_winsorized_benchmark_audit"]["passed"] is True
    assert payload["resident_winsorized_sweep_audit"]["passed"] is True
    assert payload["release_decision"]["default_change_ready"] is True
    assert payload["publish_preflight"]["status"] == "publish_preflight_ready"
    assert payload["stack_engine_publication_audit"]["status"] == "passed"
    assert payload["registration_admission"]["status"] == "accepted"
    assert payload["registration_admission"]["passed"] is True
    assert payload["quality_saturation"]["status"] == "passed"
    assert payload["quality_saturation"]["quality_gate_saturation_rejected_count"] == 0
    assert payload["quality_metrics"]["status"] == "passed"
    assert payload["quality_metrics"]["metric_count"] == 7
    assert payload["quality_metrics_compare"]["status"] == "passed"
    assert payload["publish_preflight"]["matrix_quality_metrics_compare_status"] == "passed"
    assert (
        payload["publish_preflight"][
            "windows_release_matrix_quality_metrics_compare_handoff_passed"
        ]
        is True
    )
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status" in text
    assert "Acceptance" in text
    assert "Native resident result source: run_default" in text
    assert "Native calibrated lights: 200" in text
    assert "Registration fast path: present" in text
    assert "Registration fast path contract: passed" in text
    assert "Registration admission: accepted passed=True blocked=False" in text
    assert "Quality saturation: passed passed=True" in text
    assert "Quality metrics: passed metrics=7 frames=2" in text
    assert "Quality metrics compare: passed passed=True" in text
    assert "Triangle warp batch frames: 188" in text
    assert "Default Route Acceptance" in text
    assert "Route contract passed: True" in text
    assert "Pipeline Contract" in text
    assert "Integration DQ contract: True" in text
    assert "Resident Winsorized Benchmark Audit" in text
    assert "Hardened master RMS: 5e-06" in text
    assert "Resident Winsorized Sweep Audit" in text
    assert "Required frame count: 200" in text
    assert "DQ pixels match summary: True" in text
    assert "Rejection sample counts match maps: True" in text
    assert "Rejection sample accounting: passed failed=0" in text
    assert "StackEngine Default Contract" in text
    assert "Adoption recommendation: stack_engine_default_ready" in text
    assert "Default promotion: ready ready=True blockers=0" in text
    assert "Release Decision" in text
    assert "Default change ready: True" in text
    assert "Runtime repeat ratio vs best: 1.053" in text
    assert "Windows Publish Preflight" in text
    assert "Preflight status: publish_preflight_ready" in text
    assert "Default route checks: 4" in text
    assert "Rejection sample accounting statuses: phase2=passed" in text
    assert "Integration engine policy statuses: matrix-ready=True" in text
    assert "Integration engine policy checks: matrix-acceptance=True" in text
    assert "StackEngine default contract statuses: phase2=passed" in text
    assert "StackEngine default gaps: matrix=0, default-promotion=0" in text
    assert "StackEngine runtime default statuses: matrix-ready=True" in text
    assert "StackEngine runtime default checks: matrix-acceptance=True" in text
    assert "StackEngine runtime default drift counters: matrix-legacy=0" in text
    assert "Resident winsorized sweep statuses: matrix=passed" in text
    assert "Resident winsorized sweep required frame: matrix=200/True" in text
    assert "Resident winsorized sweep checks: matrix-count=27" in text
    assert "StackEngine publication audit statuses: matrix=passed/True" in text
    assert "StackEngine publication audit chains: matrix-policy=True" in text
    assert "StackEngine publication audit checks: matrix-audit=True" in text
    assert "Quality metrics compare handoff: matrix=passed/True/0" in text
    assert "Quality metrics compare checks: matrix=True" in text
    assert "StackEngine Publication Audit" in text
    assert "Policy checks: raw=True, phase2=True, agreement=True" in text


def test_phase2_status_blocks_missing_publish_preflight_engine_policy_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=285)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        include_integration_engine_policy=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert (
        checks["windows_publish_preflight_integration_engine_policy_passed"][
            "passed"
        ]
        is False
    )
    evidence = checks["windows_publish_preflight_integration_engine_policy_passed"][
        "evidence"
    ]
    assert evidence["matrix_ready"] is None
    assert evidence["matrix_acceptance_check"] is None
    assert evidence["agreement_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_engine_policy_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=285)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        integration_engine_policy_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert (
        checks["windows_publish_preflight_integration_engine_policy_passed"][
            "passed"
        ]
        is False
    )
    evidence = checks["windows_publish_preflight_integration_engine_policy_passed"][
        "evidence"
    ]
    assert evidence["matrix_ready"] is False
    assert evidence["matrix_acceptance_status"] == "failed"
    assert evidence["default_promotion_pipeline_check"] is False


def test_phase2_status_blocks_missing_publish_preflight_publication_audit_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=291)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        include_stack_publication_audit=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert (
        checks["windows_publish_preflight_stack_engine_publication_audit_passed"][
            "passed"
        ]
        is False
    )
    evidence = checks[
        "windows_publish_preflight_stack_engine_publication_audit_passed"
    ]["evidence"]
    assert evidence["matrix_status"] is None
    assert evidence["matrix_audit_check"] is None
    assert evidence["agreement_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_publication_policy_chain(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=291)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        stack_publication_policy_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert (
        checks["windows_publish_preflight_stack_engine_publication_audit_passed"][
            "passed"
        ]
        is False
    )
    evidence = checks[
        "windows_publish_preflight_stack_engine_publication_audit_passed"
    ]["evidence"]
    assert evidence["matrix_status"] == "failed"
    assert evidence["matrix_policy_agreement"] is False
    assert evidence["default_promotion_policy_agreement"] is False
    assert evidence["matrix_policy_check"] is False


def test_phase2_status_allows_missing_publish_preflight_quality_compare_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=364)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        include_quality_metrics_compare=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    quality_check = checks[
        "windows_publish_preflight_quality_metrics_compare_passed"
    ]
    assert status["status"] == "green"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert quality_check["passed"] is True
    assert quality_check["evidence"]["present"] is False
    assert quality_check["evidence"]["matrix_ready"] is None


def test_phase2_status_blocks_failed_publish_preflight_quality_compare_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=364)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        quality_metrics_compare_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    quality_check = checks[
        "windows_publish_preflight_quality_metrics_compare_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert quality_check["passed"] is False
    assert quality_check["evidence"]["present"] is True
    assert quality_check["evidence"]["matrix_ready"] is False
    assert quality_check["evidence"]["matrix_failed_check_count"] == 1
    assert quality_check["evidence"]["agreement_check"] is False


def test_phase2_status_surfaces_publish_preflight_release_quality_publication_guard(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=370)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(publish_preflight)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )
    markdown = tmp_path / "phase2_status.md"
    write_phase2_status_markdown(markdown, status)

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_passed"
    ]
    text = markdown.read_text(encoding="utf-8")

    assert status["status"] == "green"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert guard_check["passed"] is True
    assert guard_check["evidence"]["present"] is True
    assert guard_check["evidence"]["matrix_ready"] is True
    assert guard_check["evidence"]["matrix_raw_status"] == "passed"
    assert guard_check["evidence"]["final_checks_present"] is True
    assert guard_check["evidence"]["final_evidence_present"] is True
    assert guard_check["evidence"]["final_evidence_passed"] is True
    assert guard_check["evidence"]["release_matrix_check"] is True
    assert guard_check["evidence"]["matrix_final_checks_ready"] is True
    assert guard_check["evidence"]["matrix_raw_final_checks_ready"] is True
    assert guard_check["evidence"]["default_promotion_phase2_final_checks_ready"] is True
    assert "Release quality publication guard evidence" in text
    assert "Release quality publication guard checks" in text
    assert "Release quality publication guard final checks" in text
    assert "Release quality publication guard final evidence" in text


def test_phase2_status_allows_missing_publish_preflight_release_quality_publication_guard(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=370)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        include_release_quality_publication_guard=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_passed"
    ]

    assert status["status"] == "green"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert guard_check["passed"] is True
    assert guard_check["evidence"]["present"] is False
    assert guard_check["evidence"]["matrix_ready"] is None


def test_phase2_status_blocks_failed_publish_preflight_release_quality_publication_guard(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=370)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        release_quality_publication_guard_ready=False,
        release_quality_publication_guard_raw_status="failed",
        release_quality_publication_guard_phase2_status="attention_required",
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_passed"
    ]

    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["present"] is True
    assert guard_check["evidence"]["matrix_ready"] is False
    assert guard_check["evidence"]["matrix_raw_status"] == "failed"
    assert guard_check["evidence"]["matrix_phase2_status"] == "attention_required"
    assert guard_check["evidence"]["matrix_check"] is False


def test_phase2_status_blocks_failed_publish_preflight_release_quality_final_checks(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=376)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        release_quality_publication_guard_final_checks_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_passed"
    ]

    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["matrix_ready"] is True
    assert guard_check["evidence"]["matrix_check"] is True
    assert guard_check["evidence"]["final_checks_present"] is True
    assert guard_check["evidence"]["release_matrix_check"] is False
    assert guard_check["evidence"]["release_matrix_manifest_match_check"] is False
    assert (
        "matrix_release_decision_release_quality_publication_guard_passed"
        in guard_check["evidence"]["failed_checks"]
    )


def test_phase2_status_allows_compatible_missing_publish_preflight_release_quality_final_evidence(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=382)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        release_quality_publication_guard_final_evidence_compatible_missing=True,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_passed"
    ]

    assert status["status"] == "green"
    assert guard_check["passed"] is True
    assert guard_check["evidence"]["final_evidence_present"] is True
    assert guard_check["evidence"]["final_evidence_passed"] is True
    assert guard_check["evidence"]["matrix_final_checks_ready"] is True
    assert guard_check["evidence"]["matrix_raw_final_checks_ready"] is None
    assert guard_check["evidence"]["matrix_phase2_final_checks_ready"] is None


def test_phase2_status_blocks_failed_publish_preflight_release_quality_final_evidence(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=382)
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_publish_preflight(
        publish_preflight,
        release_quality_publication_guard_final_checks_ready=True,
        release_quality_publication_guard_final_evidence_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        publish_preflight=publish_preflight,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_passed"
    ]

    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["release_matrix_check"] is True
    assert guard_check["evidence"]["final_evidence_present"] is True
    assert guard_check["evidence"]["final_evidence_passed"] is False
    assert guard_check["evidence"]["matrix_final_checks_ready"] is False
    assert guard_check["evidence"]["matrix_raw_final_checks_ready"] is False


def test_phase2_status_blocks_failed_stack_publication_policy_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=287)
    publication_audit = tmp_path / "stack_engine_publication_audit.json"
    _write_stack_engine_publication_audit(
        publication_audit,
        integration_engine_policy_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        stack_engine_publication_audit=publication_audit,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["stack_engine_publication_audit"]["status"] == "blocked"
    assert checks["stack_engine_publication_audit_passed"]["passed"] is False
    assert (
        checks["stack_engine_publication_audit_policy_chain_passed"]["passed"]
        is False
    )
    assert (
        checks["stack_engine_publication_audit_policy_chain_passed"]["evidence"][
            "phase2_ready_check"
        ]
        is False
    )
    assert (
        checks[
            "stack_engine_publication_audit_resident_winsorized_chain_passed"
        ]["passed"]
        is True
    )
    assert (
        checks[
            "stack_engine_publication_audit_resident_result_contract_chain_passed"
        ]["passed"]
        is True
    )


def test_phase2_status_blocks_failed_stack_publication_resident_result_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=345)
    publication_audit = tmp_path / "stack_engine_publication_audit.json"
    _write_stack_engine_publication_audit(
        publication_audit,
        resident_result_contract_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        stack_engine_publication_audit=publication_audit,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    result_check = checks[
        "stack_engine_publication_audit_resident_result_contract_chain_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["stack_engine_publication_audit"]["status"] == "blocked"
    assert checks["stack_engine_publication_audit_passed"]["passed"] is False
    assert result_check["passed"] is False
    assert result_check["evidence"]["raw_ready_check"] is False
    assert result_check["evidence"]["phase2_ready_check"] is False
    assert result_check["evidence"]["agreement_check"] is False
    assert (
        "publish_preflight_resident_result_contract_ready"
        in result_check["evidence"]["failed_checks"]
    )


def test_phase2_status_blocks_stack_engine_default_contract_gap(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=251)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    stack_engine_contract = tmp_path / "stack_engine_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_stack_engine_contract(stack_engine_contract, ready=False, gap_count=1)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        stack_engine_contract=stack_engine_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["stack_engine_contract"]["status"] == "passed"
    assert status["stack_engine_contract"]["default_promotion_ready"] is False
    assert (
        status["stack_engine_contract"]["adoption_phase2_stack_engine_default_gap_count"]
        == 1
    )
    check = checks["stack_engine_default_contract_ready"]
    assert check["passed"] is False
    assert check["evidence"]["adoption_gap_count"] == 1
    assert check["evidence"]["default_promotion_status"] == "blocked"


def test_phase2_status_blocks_default_ready_without_fastpath_contract(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=223)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    payload = read_json(acceptance)
    payload["checks"] = [
        item
        for item in payload["checks"]
        if not str(item.get("name") or "").startswith("contract_resident_registration_fastpath")
    ]
    write_json(acceptance, payload)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    fastpath_check = checks["resident_registration_fastpath_contract_passed_for_default"]
    assert fastpath_check["passed"] is False
    assert fastpath_check["evidence"]["status"] == "not_requested"
    assert fastpath_check["evidence"]["check_count"] == 0


def test_phase2_status_blocks_failed_default_route_acceptance_when_supplied(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=224)
    acceptance = tmp_path / "acceptance.json"
    default_route_acceptance = tmp_path / "default_route_acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance, route_passed=False)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        default_route_acceptance_audit=default_route_acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert checks["default_route_acceptance_passed"]["passed"] is False
    assert checks["default_route_acceptance_route_contract_passed"]["passed"] is False
    assert status["default_route_acceptance"]["route_failed_checks"] == [
        "contract_required_command_token:--memory-mode resident",
        "contract_required_command_token:--backend cuda",
        "contract_required_command_token:--resident-registration similarity_cuda_triangle",
        "contract_required_command_token_group:resident_h2d_or_runtime_preset",
    ]


def test_phase2_status_blocks_failed_publish_preflight_when_supplied(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=230)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight, ready=False)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert checks["windows_publish_preflight_ready"]["passed"] is False
    assert checks["windows_publish_preflight_ready"]["evidence"]["failed_checks"] == [
        "manifest_assets_match_github_plan"
    ]


def test_phase2_status_blocks_missing_publish_preflight_rejection_sample_accounting(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=241)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_rejection_sample_accounting=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert checks["windows_publish_preflight_rejection_sample_accounting_passed"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_rejection_sample_accounting_passed"][
        "evidence"
    ]["phase2_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_rejection_sample_accounting(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=241)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight, rejection_sample_accounting_ready=False)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert (
        status["publish_preflight"]["matrix_rejection_sample_accounting_status"]
        == "failed"
    )
    assert checks["windows_publish_preflight_rejection_sample_accounting_passed"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_rejection_sample_accounting_passed"][
        "evidence"
    ]["matrix_check"] is False


def test_phase2_status_blocks_missing_publish_preflight_sample_closure(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=250)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_sample_accounting_closure=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert checks["windows_publish_preflight_sample_accounting_closure_passed"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_sample_accounting_closure_passed"][
        "evidence"
    ]["phase2_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_sample_closure(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=250)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        sample_accounting_closure_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert status["publish_preflight"]["matrix_sample_accounting_closure_status"] == "failed"
    assert checks["windows_publish_preflight_sample_accounting_closure_passed"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_sample_accounting_closure_passed"][
        "evidence"
    ]["matrix_check"] is False


def test_phase2_status_blocks_failed_publish_preflight_stack_engine_contract(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=256)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        stack_engine_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert status["publish_preflight"]["matrix_stack_engine_contract_status"] == "failed"
    assert (
        status["publish_preflight"]["matrix_stack_engine_contract_default_gap_count"]
        == 1
    )
    assert checks["windows_publish_preflight_stack_engine_default_contract_ready"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_stack_engine_default_contract_ready"][
        "evidence"
    ]["matrix_check"] is False
    assert checks["windows_publish_preflight_stack_engine_default_contract_ready"][
        "evidence"
    ]["default_promotion_default_gap_count"] == 1


def test_phase2_status_blocks_missing_publish_preflight_runtime_default_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=298)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_stack_runtime_default=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    runtime_check = checks[
        "windows_publish_preflight_stack_engine_runtime_default_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert runtime_check["passed"] is False
    assert runtime_check["evidence"]["matrix_ready"] is None
    assert runtime_check["evidence"]["matrix_acceptance_check"] is None
    assert runtime_check["evidence"]["agreement_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_matrix_runtime_default(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=298)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        matrix_stack_runtime_default_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    runtime_check = checks[
        "windows_publish_preflight_stack_engine_runtime_default_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert runtime_check["passed"] is False
    assert runtime_check["evidence"]["matrix_ready"] is False
    assert runtime_check["evidence"]["matrix_acceptance_status"] == "failed"
    assert runtime_check["evidence"]["matrix_pipeline_failed_output_count"] == 1
    assert runtime_check["evidence"]["default_promotion_ready"] is True
    assert runtime_check["evidence"]["matrix_acceptance_check"] is False
    assert runtime_check["evidence"]["agreement_check"] is False


def test_phase2_status_blocks_failed_publish_preflight_default_runtime_default(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=298)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        default_promotion_stack_runtime_default_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    runtime_check = checks[
        "windows_publish_preflight_stack_engine_runtime_default_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert runtime_check["passed"] is False
    assert runtime_check["evidence"]["matrix_ready"] is True
    assert runtime_check["evidence"]["default_promotion_ready"] is False
    assert (
        runtime_check["evidence"]["default_promotion_acceptance_status"]
        == "failed"
    )
    assert (
        runtime_check["evidence"][
            "default_promotion_pipeline_failed_output_count"
        ]
        == 1
    )
    assert runtime_check["evidence"]["default_promotion_pipeline_check"] is False
    assert runtime_check["evidence"]["agreement_check"] is False


def test_phase2_status_blocks_missing_publish_preflight_direct_runtime_evidence(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=308)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_direct_runtime_evidence=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    direct_check = checks["windows_publish_preflight_direct_runtime_evidence_passed"]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert direct_check["passed"] is False
    assert direct_check["evidence"]["matrix_ready"] is None
    assert direct_check["evidence"]["matrix_acceptance_check"] is None
    assert direct_check["evidence"]["agreement_check"] is None


def test_phase2_status_blocks_stale_publish_preflight_direct_fastpath_source(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=308)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        direct_runtime_acceptance_source="phase2_status_handoff",
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    direct_check = checks["windows_publish_preflight_direct_runtime_evidence_passed"]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert direct_check["passed"] is False
    assert direct_check["evidence"]["matrix_ready"] is True
    assert direct_check["evidence"]["matrix_acceptance_source"] == "phase2_status_handoff"
    assert direct_check["evidence"]["matrix_acceptance_check"] is False
    assert direct_check["evidence"]["matrix_pipeline_check"] is True


def test_phase2_status_blocks_missing_publish_preflight_release_direct_guard(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=312)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_direct_publication_guard=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_direct_publication_guard_passed"
    ]
    assert status["status"] == "attention_required"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["github_plan_matrix_ready"] is None
    assert guard_check["evidence"]["matrix_release_check"] is None


def test_phase2_status_blocks_publish_preflight_release_direct_guard_regression(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=312)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        direct_publication_guard_lights=199,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    direct_check = checks["windows_publish_preflight_direct_runtime_evidence_passed"]
    guard_check = checks[
        "windows_publish_preflight_release_direct_publication_guard_passed"
    ]
    assert status["status"] == "attention_required"
    assert direct_check["passed"] is True
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["matrix_count_ready"] is False
    assert guard_check["evidence"]["matrix_lights"] == 199


def test_phase2_status_blocks_missing_publish_preflight_resident_winsorized_sweep(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=275)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_resident_winsorized_sweep=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    resident_check = checks[
        "windows_publish_preflight_resident_winsorized_sweep_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert resident_check["passed"] is False
    assert resident_check["evidence"]["matrix_audit_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_resident_winsorized_sweep(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=275)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        resident_winsorized_sweep_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    resident_check = checks[
        "windows_publish_preflight_resident_winsorized_sweep_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert (
        status["publish_preflight"]["matrix_resident_winsorized_sweep_status"]
        == "failed"
    )
    assert resident_check["passed"] is False
    assert resident_check["evidence"]["matrix_required_frame_check"] is False


def test_phase2_status_blocks_missing_publish_preflight_resident_fastpath_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=334)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_resident_fastpath_handoff=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    handoff_check = checks[
        "windows_publish_preflight_resident_fastpath_handoff_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["github_plan_matrix_ready"] is None
    assert handoff_check["evidence"]["matrix_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_resident_fastpath_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=334)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        resident_fastpath_handoff_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    handoff_check = checks[
        "windows_publish_preflight_resident_fastpath_handoff_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert (
        status["publish_preflight"][
            "matrix_resident_fastpath_handoff_raw_status"
        ]
        == "failed"
    )
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["matrix_check"] is False
    assert handoff_check["evidence"]["matrix_raw_check_count"] == 0


def test_phase2_status_blocks_missing_publish_preflight_resident_result_contract_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=343)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        include_resident_result_contract=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    handoff_check = checks[
        "windows_publish_preflight_resident_result_contract_handoff_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert checks["windows_publish_preflight_ready"]["passed"] is True
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["github_plan_matrix_ready"] is None
    assert handoff_check["evidence"]["matrix_check"] is None


def test_phase2_status_blocks_failed_publish_preflight_resident_result_contract_handoff(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=343)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    publish_preflight = tmp_path / "publish_preflight.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(
        publish_preflight,
        resident_result_contract_ready=False,
    )

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        publish_preflight=publish_preflight,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    handoff_check = checks[
        "windows_publish_preflight_resident_result_contract_handoff_passed"
    ]
    assert status["status"] == "attention_required"
    assert status["publish_preflight"]["status"] == "blocked"
    assert status["publish_preflight"]["matrix_resident_result_contract_status"] == "failed"
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["matrix_check"] is False
    assert handoff_check["evidence"]["matrix_failed_count"] == 1


def test_phase2_status_blocks_pipeline_rejection_sample_drift(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=236)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(pipeline_contract, rejection_sample_accounting_passed=False)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    accounting = status["pipeline_contract"]["rejection_sample_accounting"]
    assert status["status"] == "attention_required"
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_passed"]["passed"] is False
    assert accounting["status"] == "failed"
    assert accounting["check_present"] is True
    assert accounting["check_passed"] is False
    assert accounting["failed_count"] == 1
    assert accounting["failed_items"][0]["map_rejected_sample_sum"] == 7
    assert accounting["failed_items"][0]["failed_matches"][0] == {
        "source": "dq_coverage_provenance.rejected_sample_count",
        "actual": 7,
        "summary": 6,
        "delta": 1,
    }


def test_phase2_status_blocks_pipeline_resident_result_contract_failure(
    tmp_path: Path,
):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=338)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(
        pipeline_contract,
        resident_result_contract_passed=False,
    )
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    resident = status["pipeline_contract"]["resident_result_contract"]
    assert status["status"] == "attention_required"
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert checks["pipeline_resident_result_contract_passed"]["passed"] is False
    assert resident["status"] == "failed"
    assert resident["check_present"] is True
    assert resident["check_passed"] is False
    assert resident["required_count"] == 1
    assert resident["failed_count"] == 1
    assert resident["failed_check_count"] == 1
    assert resident["failed_checks"] == ["source_terms_present"]
    assert resident["failed_items"][0]["item"] == "H"
    assert resident["failed_items"][0]["backend"] == "cuda_resident_stack"


def test_phase2_status_blocks_pipeline_sample_closure_drift(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=245)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(
        pipeline_contract,
        sample_accounting_closure_passed=False,
    )
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    closure = status["pipeline_contract"]["sample_accounting_closure"]
    assert status["status"] == "attention_required"
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert checks["pipeline_sample_accounting_closure_passed"]["passed"] is False
    assert closure["status"] == "failed"
    assert closure["check_present"] is True
    assert closure["check_passed"] is False
    assert closure["present_count"] == 1
    assert closure["failed_count"] == 1
    assert closure["failed_items"][0]["input_valid_samples_before_rejection"] == 9
    assert closure["failed_items"][0]["valid_samples_after_rejection"] == 6
    assert closure["failed_items"][0]["rejected_samples"] == 2


def test_phase2_status_blocks_pipeline_engine_policy_drift(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=281)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance)
    _write_pipeline_contract(
        pipeline_contract,
        integration_engine_policy_passed=False,
    )
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    engine_policy = status["pipeline_contract"]["integration_engine_policy"]
    assert status["status"] == "attention_required"
    assert checks["pipeline_contract_passed"]["passed"] is False
    assert checks["pipeline_integration_engine_policy_passed"]["passed"] is False
    assert engine_policy["status"] == "failed"
    assert engine_policy["check_present"] is True
    assert engine_policy["check_passed"] is False
    assert engine_policy["non_resident_count"] == 1
    assert engine_policy["failed_count"] == 1
    assert engine_policy["failed_items"][0]["failures"] == ["cuda_fast_path_not_explicit"]


def test_phase2_status_blocks_acceptance_engine_policy_handoff_drift(tmp_path: Path):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    _write_checkpoint(checkpoints, gate=281)
    acceptance = tmp_path / "acceptance.json"
    pipeline_contract = tmp_path / "pipeline_contract.json"
    release_decision = tmp_path / "release_decision.json"
    _write_acceptance(acceptance, integration_engine_policy_passed=False)
    _write_pipeline_contract(pipeline_contract)
    _write_release_decision(release_decision)

    status = build_phase2_status(
        checkpoint_dir=checkpoints,
        acceptance_audit=acceptance,
        pipeline_contract=pipeline_contract,
        release_decision=release_decision,
        doctor_payload=_doctor_payload(),
    )

    checks = {item["name"]: item for item in status["checks"]}
    acceptance_policy = status["acceptance_audit"]["pipeline_integration_engine_policy"]
    assert status["status"] == "attention_required"
    assert checks["acceptance_audit_passed"]["passed"] is False
    assert checks["acceptance_pipeline_integration_engine_policy_passed"]["passed"] is False
    assert acceptance_policy["status"] == "failed"
    assert acceptance_policy["check_present"] is True
    assert acceptance_policy["check_passed"] is False
    assert acceptance_policy["non_resident_count"] == 1
    assert acceptance_policy["failed_count"] == 1


def test_phase2_status_compare_passes_non_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=203))
    write_json(candidate, _status_payload(gate=204))

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["status"] == "passed"
    assert checks["latest_checkpoint_gate_not_decreased"] is True
    assert checks["acceptance_audit_passed_preserved"] is True
    assert checks["default_route_acceptance_passed_preserved"] is True
    assert checks["default_route_acceptance_route_contract_preserved"] is True
    assert checks["resident_registration_fastpath_contract_passed_preserved"] is True
    assert checks["resident_registration_fastpath_contract_check_count_preserved"] is True
    assert checks["cuda_available_preserved"] is True
    assert checks["release_manifest_ready_preserved"] is True
    assert checks["github_release_plan_ready_preserved"] is True
    assert checks["windows_publish_preflight_ready_preserved"] is True
    assert checks["windows_publish_preflight_rejection_sample_accounting_preserved"] is True
    assert checks["windows_publish_preflight_rejection_sample_status_preserved"] is True
    assert checks["windows_publish_preflight_sample_accounting_closure_preserved"] is True
    assert checks["windows_publish_preflight_sample_closure_status_preserved"] is True
    assert checks["windows_publish_preflight_integration_engine_policy_preserved"] is True
    assert (
        checks[
            "windows_publish_preflight_integration_engine_policy_status_preserved"
        ]
        is True
    )
    assert checks["windows_publish_preflight_stack_engine_contract_preserved"] is True
    assert checks["windows_publish_preflight_stack_engine_status_preserved"] is True
    assert (
        checks[
            "windows_publish_preflight_stack_engine_runtime_default_preserved"
        ]
        is True
    )
    assert (
        checks[
            "windows_publish_preflight_stack_engine_runtime_default_status_preserved"
        ]
        is True
    )
    assert (
        checks["windows_publish_preflight_direct_runtime_evidence_preserved"]
        is True
    )
    assert (
        checks["windows_publish_preflight_direct_runtime_status_preserved"]
        is True
    )
    assert (
        checks[
            "windows_publish_preflight_release_direct_publication_guard_preserved"
        ]
        is True
    )
    assert (
        checks[
            "windows_publish_preflight_release_direct_publication_guard_status_preserved"
        ]
        is True
    )
    assert checks["windows_publish_preflight_resident_winsorized_sweep_preserved"] is True
    assert checks["windows_publish_preflight_resident_winsorized_status_preserved"] is True
    assert checks["windows_publish_preflight_resident_fastpath_handoff_preserved"] is True
    assert (
        checks[
            "windows_publish_preflight_resident_fastpath_handoff_status_preserved"
        ]
        is True
    )
    assert (
        checks[
            "windows_publish_preflight_resident_result_contract_handoff_preserved"
        ]
        is True
    )
    assert (
        checks[
            "windows_publish_preflight_resident_result_contract_status_preserved"
        ]
        is True
    )
    assert checks["stack_engine_publication_audit_passed_preserved"] is True
    assert checks["stack_engine_publication_policy_chain_preserved"] is True
    assert checks["stack_engine_publication_resident_winsorized_chain_preserved"] is True
    assert (
        checks["stack_engine_publication_resident_result_contract_chain_preserved"]
        is True
    )
    assert checks["stack_engine_publication_direct_runtime_chain_preserved"] is True
    assert checks["pipeline_contract_passed_preserved"] is True
    assert checks["pipeline_resident_result_contract_check_preserved"] is True
    assert checks["pipeline_resident_result_contract_passed_preserved"] is True
    assert (
        checks["pipeline_resident_result_contract_failure_count_not_increased"]
        is True
    )
    assert checks["acceptance_pipeline_integration_engine_policy_preserved"] is True
    assert (
        checks[
            "acceptance_pipeline_stack_engine_runtime_default_check_preserved"
        ]
        is True
    )
    assert (
        checks[
            "acceptance_pipeline_stack_engine_runtime_default_passed_preserved"
        ]
        is True
    )
    assert checks["pipeline_integration_dq_contract_preserved"] is True
    assert checks["pipeline_pixel_verification_preserved"] is True
    assert checks["pipeline_integration_engine_policy_check_preserved"] is True
    assert checks["pipeline_integration_engine_policy_passed_preserved"] is True
    assert checks["pipeline_stack_engine_runtime_default_check_preserved"] is True
    assert checks["pipeline_stack_engine_runtime_default_passed_preserved"] is True
    assert checks["pipeline_rejection_sample_accounting_check_preserved"] is True
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"] is True
    assert checks["pipeline_sample_accounting_closure_check_preserved"] is True
    assert checks["pipeline_sample_accounting_closure_passed_preserved"] is True
    assert checks["stack_engine_default_contract_ready_preserved"] is True
    assert checks["stack_engine_default_gap_count_not_increased"] is True
    assert checks["release_decision_default_change_ready_preserved"] is True
    assert checks["release_decision_promote_recommendation_preserved"] is True


def test_phase2_status_compare_flags_handoff_regressions(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=203))
    write_json(
        candidate,
        _status_payload(
            gate=202,
            status="attention_required",
            checkpoint_green=False,
            acceptance_passed=False,
            acceptance_status="failed",
            acceptance_pipeline_engine_policy_status="failed",
            acceptance_pipeline_engine_policy_check_passed=False,
            acceptance_pipeline_runtime_default_status="failed",
            acceptance_pipeline_runtime_default_check_passed=False,
            acceptance_pipeline_runtime_default_legacy_master_count=1,
            cuda_available=False,
            release_status="failed",
            github_status="failed",
            publish_preflight_status="blocked",
            publish_preflight_rejection_sample_status="failed",
            publish_preflight_sample_closure_status="failed",
            publish_preflight_integration_engine_policy_status="failed",
            publish_preflight_integration_engine_policy_ready=False,
            publish_preflight_stack_engine_status="failed",
            publish_preflight_stack_runtime_default_status="failed",
            publish_preflight_stack_runtime_default_ready=False,
            publish_preflight_stack_runtime_default_legacy_master_count=1,
            publish_preflight_stack_runtime_default_failed_output_count=1,
            publish_preflight_direct_runtime_ready=False,
            publish_preflight_resident_fastpath_handoff_ready=False,
            publish_preflight_resident_fastpath_handoff_raw_status="failed",
            publish_preflight_resident_fastpath_handoff_phase2_status=(
                "attention_required"
            ),
            publish_preflight_resident_fastpath_handoff_raw_check_count=0,
            publish_preflight_resident_result_contract_ready=False,
            publish_preflight_resident_result_contract_status="failed",
            publish_preflight_resident_result_contract_phase2_check_passed=False,
            publish_preflight_resident_result_contract_failed_count=1,
            stack_publication_passed=False,
            stack_publication_policy_ready=False,
            stack_publication_resident_winsorized_ready=False,
            stack_publication_resident_result_contract_ready=False,
            pipeline_passed=False,
            pipeline_dq_contract=False,
            pixel_verification=False,
            pipeline_engine_policy_status="failed",
            pipeline_runtime_default_status="failed",
            pipeline_runtime_default_legacy_master_count=1,
            pipeline_resident_result_check_present=False,
            pipeline_resident_result_status="failed",
            pipeline_resident_result_failed_count=1,
            pipeline_resident_result_failed_checks=["source_terms_present"],
            pipeline_rejection_sample_status="failed",
            pipeline_sample_closure_status="failed",
            default_change_ready=False,
            release_recommendation="repeat_benchmark_before_default_change",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["latest_checkpoint_gate_not_decreased"] is False
    assert checks["overall_status_green_preserved"] is False
    assert checks["latest_checkpoint_green_preserved"] is False
    assert checks["acceptance_audit_passed_preserved"] is False
    assert checks["acceptance_status_preserved"] is False
    assert checks["default_route_acceptance_passed_preserved"] is True
    assert checks["default_route_acceptance_route_contract_preserved"] is True
    assert checks["resident_registration_fastpath_contract_passed_preserved"] is True
    assert checks["resident_registration_fastpath_contract_check_count_preserved"] is True
    assert checks["cuda_available_preserved"] is False
    assert checks["release_manifest_ready_preserved"] is False
    assert checks["github_release_plan_ready_preserved"] is False
    assert checks["windows_publish_preflight_ready_preserved"] is False
    assert checks["windows_publish_preflight_rejection_sample_accounting_preserved"] is False
    assert checks["windows_publish_preflight_rejection_sample_status_preserved"] is False
    assert checks["windows_publish_preflight_sample_accounting_closure_preserved"] is False
    assert checks["windows_publish_preflight_sample_closure_status_preserved"] is False
    assert checks["windows_publish_preflight_integration_engine_policy_preserved"] is False
    assert (
        checks[
            "windows_publish_preflight_integration_engine_policy_status_preserved"
        ]
        is False
    )
    assert checks["windows_publish_preflight_stack_engine_contract_preserved"] is False
    assert checks["windows_publish_preflight_stack_engine_status_preserved"] is False
    assert (
        checks[
            "windows_publish_preflight_stack_engine_runtime_default_preserved"
        ]
        is False
    )
    assert (
        checks[
            "windows_publish_preflight_stack_engine_runtime_default_status_preserved"
        ]
        is False
    )
    assert (
        checks["windows_publish_preflight_direct_runtime_evidence_preserved"]
        is False
    )
    assert (
        checks["windows_publish_preflight_direct_runtime_status_preserved"]
        is False
    )
    assert (
        checks[
            "windows_publish_preflight_release_direct_publication_guard_preserved"
        ]
        is False
    )
    assert (
        checks[
            "windows_publish_preflight_release_direct_publication_guard_status_preserved"
        ]
        is False
    )
    assert checks["windows_publish_preflight_resident_fastpath_handoff_preserved"] is False
    assert (
        checks[
            "windows_publish_preflight_resident_fastpath_handoff_status_preserved"
        ]
        is False
    )
    assert (
        checks[
            "windows_publish_preflight_resident_result_contract_handoff_preserved"
        ]
        is False
    )
    assert (
        checks[
            "windows_publish_preflight_resident_result_contract_status_preserved"
        ]
        is False
    )
    assert checks["stack_engine_publication_audit_passed_preserved"] is False
    assert checks["stack_engine_publication_policy_chain_preserved"] is False
    assert checks["stack_engine_publication_resident_winsorized_chain_preserved"] is False
    assert (
        checks["stack_engine_publication_resident_result_contract_chain_preserved"]
        is False
    )
    assert checks["stack_engine_publication_direct_runtime_chain_preserved"] is False
    assert checks["pipeline_contract_passed_preserved"] is False
    assert checks["pipeline_resident_result_contract_check_preserved"] is False
    assert checks["pipeline_resident_result_contract_passed_preserved"] is False
    assert (
        checks["pipeline_resident_result_contract_failure_count_not_increased"]
        is False
    )
    assert checks["acceptance_pipeline_integration_engine_policy_preserved"] is False
    assert (
        checks[
            "acceptance_pipeline_stack_engine_runtime_default_passed_preserved"
        ]
        is False
    )
    assert checks["pipeline_integration_dq_contract_preserved"] is False
    assert checks["pipeline_pixel_verification_preserved"] is False
    assert checks["pipeline_integration_engine_policy_check_preserved"] is True
    assert checks["pipeline_integration_engine_policy_passed_preserved"] is False
    assert checks["pipeline_stack_engine_runtime_default_check_preserved"] is True
    assert checks["pipeline_stack_engine_runtime_default_passed_preserved"] is False
    assert checks["pipeline_rejection_sample_accounting_check_preserved"] is True
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"] is False
    assert checks["pipeline_sample_accounting_closure_check_preserved"] is True
    assert checks["pipeline_sample_accounting_closure_passed_preserved"] is False
    assert checks["release_decision_default_change_ready_preserved"] is False
    assert checks["release_decision_promote_recommendation_preserved"] is False


def test_phase2_status_compare_flags_fastpath_contract_evidence_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=221))
    write_json(
        candidate,
        _status_payload(
            gate=222,
            fastpath_contract_status="not_requested",
            fastpath_contract_check_count=0,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["resident_registration_fastpath_contract_passed_preserved"]["passed"] is False
    assert checks["resident_registration_fastpath_contract_passed_preserved"]["evidence"] == {
        "baseline": "passed",
        "candidate": "not_requested",
    }
    assert checks["resident_registration_fastpath_contract_check_count_preserved"]["passed"] is False
    assert checks["resident_registration_fastpath_contract_check_count_preserved"]["evidence"] == {
        "baseline": 24,
        "candidate": 0,
    }


def test_phase2_status_compare_flags_acceptance_engine_policy_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=281))
    write_json(
        candidate,
        _status_payload(
            gate=282,
            status="attention_required",
            acceptance_passed=False,
            acceptance_status="failed",
            acceptance_pipeline_engine_policy_status="failed",
            acceptance_pipeline_engine_policy_check_passed=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["acceptance_pipeline_integration_engine_policy_preserved"][
        "passed"
    ] is False
    assert checks["acceptance_pipeline_integration_engine_policy_preserved"][
        "evidence"
    ] == {
        "baseline": {
            "status": "passed",
            "check_present": True,
            "check_passed": True,
        },
        "candidate": {
            "status": "failed",
            "check_present": True,
            "check_passed": False,
        },
    }


def test_phase2_status_compare_flags_acceptance_runtime_default_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=294))
    write_json(
        candidate,
        _status_payload(
            gate=295,
            status="attention_required",
            acceptance_passed=False,
            acceptance_status="failed",
            acceptance_pipeline_runtime_default_status="failed",
            acceptance_pipeline_runtime_default_check_passed=False,
            acceptance_pipeline_runtime_default_legacy_master_count=1,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks[
        "acceptance_pipeline_stack_engine_runtime_default_passed_preserved"
    ]["passed"] is False
    assert checks[
        "acceptance_pipeline_stack_engine_runtime_default_passed_preserved"
    ]["evidence"] == {
        "baseline": {
            "status": "passed",
            "check_passed": True,
            "legacy_master_count": 0,
        },
        "candidate": {
            "status": "failed",
            "check_passed": False,
            "legacy_master_count": 1,
        },
    }


def test_phase2_status_compare_flags_pipeline_engine_policy_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=281))
    write_json(
        candidate,
        _status_payload(
            gate=282,
            status="attention_required",
            pipeline_passed=False,
            pipeline_engine_policy_check_present=False,
            pipeline_engine_policy_status="not_available",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["pipeline_integration_engine_policy_check_preserved"][
        "passed"
    ] is False
    assert checks["pipeline_integration_engine_policy_check_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["pipeline_integration_engine_policy_passed_preserved"][
        "passed"
    ] is False
    assert checks["pipeline_integration_engine_policy_passed_preserved"]["evidence"] == {
        "baseline": "passed",
        "candidate": "not_available",
    }


def test_phase2_status_compare_flags_pipeline_runtime_default_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=294))
    write_json(
        candidate,
        _status_payload(
            gate=295,
            status="attention_required",
            pipeline_passed=False,
            pipeline_runtime_default_check_present=False,
            pipeline_runtime_default_status="not_available",
            pipeline_runtime_default_legacy_master_count=1,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["pipeline_stack_engine_runtime_default_check_preserved"][
        "passed"
    ] is False
    assert checks["pipeline_stack_engine_runtime_default_check_preserved"][
        "evidence"
    ] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["pipeline_stack_engine_runtime_default_passed_preserved"][
        "passed"
    ] is False
    assert checks["pipeline_stack_engine_runtime_default_passed_preserved"][
        "evidence"
    ] == {
        "baseline": {
            "status": "passed",
            "check_passed": True,
            "legacy_master_count": 0,
        },
        "candidate": {
            "status": "not_available",
            "check_passed": None,
            "legacy_master_count": 1,
        },
    }


def test_phase2_status_compare_flags_default_route_acceptance_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=223))
    write_json(
        candidate,
        _status_payload(
            gate=224,
            default_route_passed=False,
            default_route_contract_passed=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["default_route_acceptance_passed_preserved"]["passed"] is False
    assert checks["default_route_acceptance_passed_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["default_route_acceptance_route_contract_preserved"]["passed"] is False
    assert checks["default_route_acceptance_route_contract_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }


def test_phase2_status_compare_flags_rejection_sample_accounting_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=235))
    write_json(
        candidate,
        _status_payload(
            gate=236,
            pipeline_rejection_sample_check_present=False,
            pipeline_rejection_sample_status="not_available",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["pipeline_rejection_sample_accounting_check_preserved"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_check_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"]["passed"] is False
    assert checks["pipeline_rejection_sample_accounting_passed_preserved"]["evidence"] == {
        "baseline": "passed",
        "candidate": "not_available",
    }


def test_phase2_status_compare_flags_sample_closure_regression(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=244))
    write_json(
        candidate,
        _status_payload(
            gate=245,
            pipeline_sample_closure_check_present=False,
            pipeline_sample_closure_status="not_available",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["pipeline_sample_accounting_closure_check_preserved"]["passed"] is False
    assert checks["pipeline_sample_accounting_closure_check_preserved"]["evidence"] == {
        "baseline": True,
        "candidate": False,
    }
    assert checks["pipeline_sample_accounting_closure_passed_preserved"]["passed"] is False
    assert checks["pipeline_sample_accounting_closure_passed_preserved"]["evidence"] == {
        "baseline": "passed",
        "candidate": "not_available",
    }


def test_phase2_status_compare_flags_stack_engine_default_contract_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=250))
    write_json(
        candidate,
        _status_payload(
            gate=251,
            stack_engine_ready=False,
            stack_engine_gap_count=2,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["stack_engine_default_contract_ready_preserved"]["passed"] is False
    assert checks["stack_engine_default_contract_ready_preserved"]["evidence"][
        "baseline"
    ]["ready"] is True
    assert checks["stack_engine_default_contract_ready_preserved"]["evidence"][
        "candidate"
    ]["ready"] is False
    assert checks["stack_engine_default_gap_count_not_increased"]["passed"] is False
    assert checks["stack_engine_default_gap_count_not_increased"]["evidence"] == {
        "baseline": 0,
        "candidate": 2,
    }


def test_phase2_status_compare_flags_publish_preflight_sample_closure_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=249))
    write_json(
        candidate,
        _status_payload(
            gate=250,
            publish_preflight_sample_closure_status="failed",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["windows_publish_preflight_sample_accounting_closure_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_sample_accounting_closure_preserved"][
        "evidence"
    ]["candidate"]["checks_passed"] is False
    assert checks["windows_publish_preflight_sample_closure_status_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_sample_closure_status_preserved"][
        "evidence"
    ]["candidate"]["matrix_sample_accounting_closure_status"] == "failed"


def test_phase2_status_compare_flags_publish_preflight_engine_policy_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=284))
    write_json(
        candidate,
        _status_payload(
            gate=285,
            publish_preflight_integration_engine_policy_status="failed",
            publish_preflight_integration_engine_policy_ready=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["windows_publish_preflight_integration_engine_policy_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_integration_engine_policy_preserved"][
        "evidence"
    ]["candidate"]["checks_passed"] is False
    assert (
        checks[
            "windows_publish_preflight_integration_engine_policy_status_preserved"
        ]["passed"]
        is False
    )
    candidate_statuses = checks[
        "windows_publish_preflight_integration_engine_policy_status_preserved"
    ]["evidence"]["candidate"]
    assert candidate_statuses["matrix_integration_engine_policy_ready"] is False
    assert (
        candidate_statuses["matrix_acceptance_integration_engine_policy_status"]
        == "failed"
    )
    assert (
        payload["candidate"]["publish_preflight_integration_engine_policy"][
            "default_promotion_pipeline_integration_engine_policy_status"
        ]
        == "failed"
    )


def test_phase2_status_compare_flags_stack_publication_policy_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=286))
    write_json(
        candidate,
        _status_payload(
            gate=287,
            status="attention_required",
            stack_publication_passed=False,
            stack_publication_policy_ready=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["stack_engine_publication_audit_passed_preserved"]["passed"] is False
    assert checks["stack_engine_publication_policy_chain_preserved"]["passed"] is False
    assert (
        checks["stack_engine_publication_resident_winsorized_chain_preserved"][
            "passed"
        ]
        is True
    )
    assert (
        checks["stack_engine_publication_resident_result_contract_chain_preserved"][
            "passed"
        ]
        is True
    )
    candidate_policy = checks["stack_engine_publication_policy_chain_preserved"][
        "evidence"
    ]["candidate"]
    assert (
        candidate_policy[
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        ]
        is False
    )
    assert (
        payload["candidate"]["stack_engine_publication_audit"][
            "policy_checks_passed"
        ]
        is False
    )


def test_phase2_status_compare_flags_registration_admission_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline_payload = _status_payload(gate=352)
    baseline_payload["registration_admission"] = {
        "status": "accepted",
        "passed": True,
        "blocked": False,
        "reference_frame_id": "F000001",
        "reason": None,
    }
    candidate_payload = _status_payload(gate=353, status="attention_required")
    candidate_payload["registration_admission"] = {
        "status": "blocked",
        "passed": False,
        "blocked": True,
        "reference_frame_id": "F000001",
        "reason": "reference frame failed the quality gate",
    }
    write_json(baseline, baseline_payload)
    write_json(candidate, candidate_payload)

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    check = checks["registration_reference_admission_not_blocked_preserved"]
    assert payload["status"] == "regressed"
    assert check["passed"] is False
    assert check["evidence"]["baseline"]["status"] == "accepted"
    assert check["evidence"]["candidate"]["status"] == "blocked"
    assert payload["candidate"]["registration_admission"]["blocked"] is True


def test_phase2_status_compare_flags_quality_saturation_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline_payload = _status_payload(gate=355)
    baseline_payload["quality_saturation"] = {
        "status": "passed",
        "passed": True,
        "frame_count": 2,
        "saturated_frame_count": 1,
        "quality_gate_saturation_rejected_count": 0,
        "max_saturation_fraction": 0.00878906,
        "worst_frame_id": "F_SAT",
    }
    candidate_payload = _status_payload(gate=356, status="attention_required")
    candidate_payload["quality_saturation"] = {
        "status": "attention_required",
        "passed": False,
        "frame_count": 2,
        "saturated_frame_count": 1,
        "quality_gate_saturation_rejected_count": 1,
        "max_saturation_fraction": 0.00878906,
        "worst_frame_id": "F_SAT",
    }
    write_json(baseline, baseline_payload)
    write_json(candidate, candidate_payload)

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    check = checks["quality_saturation_no_rejections_preserved"]
    assert payload["status"] == "regressed"
    assert check["passed"] is False
    assert check["evidence"]["baseline"]["passed"] is True
    assert check["evidence"]["candidate"]["passed"] is False
    assert (
        check["evidence"]["candidate"]["quality_gate_saturation_rejected_count"]
        == 1
    )
    assert payload["candidate"]["quality_saturation"]["status"] == "attention_required"


def test_phase2_status_compare_flags_quality_metric_summary_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline_payload = _status_payload(gate=357)
    baseline_payload["quality_metrics"] = {
        "status": "passed",
        "passed": True,
        "frame_count": 2,
        "metric_count": 7,
        "metrics": [
            "star_count",
            "fwhm_px",
            "eccentricity",
            "background_rms",
            "snr",
            "quality_score",
            "weight",
        ],
    }
    candidate_payload = _status_payload(gate=358, status="attention_required")
    candidate_payload["quality_metrics"] = {
        "status": "not_available",
        "passed": False,
        "frame_count": 2,
        "metric_count": 0,
        "metrics": [],
    }
    write_json(baseline, baseline_payload)
    write_json(candidate, candidate_payload)

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    check = checks["quality_metric_summary_available_preserved"]
    assert payload["status"] == "regressed"
    assert check["passed"] is False
    assert check["evidence"]["baseline"]["metric_count"] == 7
    assert check["evidence"]["candidate"]["metric_count"] == 0
    assert payload["candidate"]["quality_metrics"]["status"] == "not_available"


def test_phase2_status_compare_flags_quality_metrics_compare_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline_payload = _status_payload(gate=359)
    baseline_payload["quality_metrics_compare"] = {
        "status": "passed",
        "passed": True,
        "failed_check_count": 0,
        "failed_checks": [],
        "threshold_failure_count": 0,
    }
    candidate_payload = _status_payload(gate=360, status="attention_required")
    candidate_payload["quality_metrics_compare"] = {
        "status": "failed",
        "passed": False,
        "failed_check_count": 1,
        "failed_checks": ["bad_median_ratio_within_limit"],
        "threshold_failure_count": 1,
    }
    write_json(baseline, baseline_payload)
    write_json(candidate, candidate_payload)

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    check = checks["quality_metrics_compare_passed_preserved"]
    assert payload["status"] == "regressed"
    assert check["passed"] is False
    assert check["evidence"]["baseline"]["passed"] is True
    assert check["evidence"]["candidate"]["passed"] is False
    assert check["evidence"]["candidate"]["failed_checks"] == [
        "bad_median_ratio_within_limit"
    ]
    assert payload["candidate"]["quality_metrics_compare"]["status"] == "failed"


def test_phase2_status_compare_flags_publish_preflight_quality_compare_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=363))
    write_json(
        candidate,
        _status_payload(
            gate=364,
            status="attention_required",
            publish_preflight_quality_metrics_compare_ready=False,
            publish_preflight_quality_metrics_compare_status="failed",
            publish_preflight_quality_metrics_compare_failed_check_count=1,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    handoff_check = checks[
        "windows_publish_preflight_quality_metrics_compare_preserved"
    ]
    status_check = checks[
        "windows_publish_preflight_quality_metrics_compare_status_preserved"
    ]
    assert payload["status"] == "regressed"
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["baseline"]["checks_passed"] is True
    assert handoff_check["evidence"]["candidate"]["checks_passed"] is False
    assert status_check["passed"] is False
    candidate_statuses = status_check["evidence"]["candidate"]
    assert candidate_statuses["matrix_quality_metrics_compare_ready"] is False
    assert candidate_statuses["matrix_quality_metrics_compare_status"] == "failed"
    assert candidate_statuses["matrix_quality_metrics_compare_failed_check_count"] == 1
    assert (
        payload["candidate"]["publish_preflight_quality_metrics_compare"][
            "default_promotion_quality_metrics_compare_status"
        ]
        == "failed"
    )


def test_phase2_status_compare_flags_stack_publication_resident_result_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=344))
    write_json(
        candidate,
        _status_payload(
            gate=345,
            status="attention_required",
            stack_publication_passed=False,
            stack_publication_resident_result_contract_ready=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    result_check = checks[
        "stack_engine_publication_resident_result_contract_chain_preserved"
    ]
    assert payload["status"] == "regressed"
    assert checks["stack_engine_publication_audit_passed_preserved"]["passed"] is False
    assert result_check["passed"] is False
    assert (
        result_check["evidence"]["candidate"][
            "phase2_publish_preflight_resident_result_contract_matches_publish_preflight"
        ]
        is False
    )
    assert (
        payload["candidate"]["stack_engine_publication_audit"][
            "resident_result_contract_checks_passed"
        ]
        is False
    )
    assert (
        checks["stack_engine_publication_policy_chain_preserved"]["passed"]
        is True
    )
    assert (
        checks["stack_engine_publication_resident_winsorized_chain_preserved"][
            "passed"
        ]
        is True
    )


def test_phase2_status_compare_markdown_expands_stack_publication_resident_result_failure(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "compare.json"
    markdown = tmp_path / "compare.md"
    write_json(baseline, _status_payload(gate=345))
    write_json(
        candidate,
        _status_payload(
            gate=346,
            status="attention_required",
            stack_publication_passed=False,
            stack_publication_resident_result_contract_ready=False,
        ),
    )
    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    write_phase2_status_compare(out, payload, markdown=markdown)

    text = markdown.read_text(encoding="utf-8")
    assert "## Failed Check Details" in text
    assert "stack_engine_publication_resident_result_contract_chain_preserved" in text
    assert "phase2_publish_preflight_resident_result_contract_ready" in text
    assert (
        '"phase2_publish_preflight_resident_result_contract_matches_publish_preflight": false'
        in text
    )


def test_phase2_status_compare_flags_publish_preflight_stack_engine_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=255))
    write_json(
        candidate,
        _status_payload(
            gate=256,
            publish_preflight_stack_engine_status="failed",
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["windows_publish_preflight_stack_engine_contract_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_stack_engine_contract_preserved"][
        "evidence"
    ]["candidate"]["checks_passed"] is False
    assert checks["windows_publish_preflight_stack_engine_status_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_stack_engine_status_preserved"][
        "evidence"
    ]["candidate"]["matrix_stack_engine_contract_status"] == "failed"


def test_phase2_status_compare_flags_publish_preflight_runtime_default_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=297))
    write_json(
        candidate,
        _status_payload(
            gate=298,
            publish_preflight_stack_runtime_default_status="failed",
            publish_preflight_stack_runtime_default_ready=False,
            publish_preflight_stack_runtime_default_legacy_master_count=1,
            publish_preflight_stack_runtime_default_failed_output_count=1,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks[
        "windows_publish_preflight_stack_engine_runtime_default_preserved"
    ]["passed"] is False
    assert checks[
        "windows_publish_preflight_stack_engine_runtime_default_preserved"
    ]["evidence"]["candidate"]["checks_passed"] is False
    assert checks[
        "windows_publish_preflight_stack_engine_runtime_default_status_preserved"
    ]["passed"] is False
    candidate_statuses = checks[
        "windows_publish_preflight_stack_engine_runtime_default_status_preserved"
    ]["evidence"]["candidate"]
    assert candidate_statuses["matrix_stack_engine_runtime_default_ready"] is False
    assert (
        candidate_statuses["matrix_acceptance_stack_engine_runtime_default_status"]
        == "failed"
    )
    assert (
        candidate_statuses[
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
        ]
        == 1
    )
    assert (
        payload["candidate"]["publish_preflight_stack_engine_runtime_default"][
            "matrix_pipeline_stack_engine_runtime_default_status"
        ]
        == "failed"
    )


def test_phase2_status_compare_flags_publish_preflight_direct_runtime_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=307))
    write_json(
        candidate,
        _status_payload(
            gate=308,
            status="attention_required",
            publish_preflight_direct_runtime_ready=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["windows_publish_preflight_direct_runtime_evidence_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_direct_runtime_evidence_preserved"][
        "evidence"
    ]["candidate"]["checks_passed"] is False
    assert checks["windows_publish_preflight_direct_runtime_status_preserved"][
        "passed"
    ] is False
    candidate_statuses = checks[
        "windows_publish_preflight_direct_runtime_status_preserved"
    ]["evidence"]["candidate"]
    assert candidate_statuses["matrix_direct_runtime_evidence_ready"] is False
    assert candidate_statuses["matrix_direct_runtime_acceptance_check_count"] == 0


def test_phase2_status_compare_flags_publish_preflight_release_direct_guard_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=311))
    write_json(
        candidate,
        _status_payload(
            gate=312,
            status="attention_required",
            publish_preflight_release_direct_publication_guard_lights=199,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    guard_check = checks[
        "windows_publish_preflight_release_direct_publication_guard_preserved"
    ]
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["candidate"]["checks_passed"] is False
    status_check = checks[
        "windows_publish_preflight_release_direct_publication_guard_status_preserved"
    ]
    assert status_check["passed"] is False
    candidate_statuses = status_check["evidence"]["candidate"]
    assert candidate_statuses["matrix_release_direct_publication_guard_lights"] == 199
    assert (
        candidate_statuses["matrix_release_direct_publication_guard_count_ready"]
        is False
    )
    assert (
        candidate_statuses[
            "github_plan_matrix_release_direct_publication_guard_ready"
        ]
        is False
    )


def test_phase2_status_compare_flags_publish_preflight_release_quality_guard_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=369))
    write_json(
        candidate,
        _status_payload(
            gate=370,
            status="attention_required",
            publish_preflight_release_quality_publication_guard_ready=False,
            publish_preflight_release_quality_publication_guard_raw_status="failed",
            publish_preflight_release_quality_publication_guard_phase2_status=(
                "attention_required"
            ),
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    guard_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_preserved"
    ]
    status_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_status_preserved"
    ]

    assert payload["status"] == "regressed"
    assert guard_check["passed"] is False
    assert guard_check["evidence"]["candidate"]["checks_passed"] is False
    assert status_check["passed"] is False
    candidate_statuses = status_check["evidence"]["candidate"]
    assert candidate_statuses["matrix_release_quality_publication_guard_ready"] is False
    assert (
        candidate_statuses["matrix_release_quality_publication_guard_raw_status"]
        == "failed"
    )
    assert (
        payload["candidate"]["publish_preflight_release_quality_publication_guard"][
            "matrix_release_quality_publication_guard_raw_status"
        ]
        == "failed"
    )


def test_phase2_status_compare_flags_missing_publish_preflight_release_quality_final_checks(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=376))
    write_json(
        candidate,
        _status_payload(
            gate=376,
            publish_preflight_release_quality_publication_guard_final_checks_present=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    final_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_final_checks_preserved"
    ]

    assert payload["status"] == "regressed"
    assert final_check["passed"] is False
    assert final_check["evidence"]["baseline"]["final_checks_present"] is True
    assert final_check["evidence"]["candidate"]["final_checks_present"] is False
    assert final_check["evidence"]["candidate"]["final_checks_passed"] is False
    assert (
        payload["candidate"]["publish_preflight_release_quality_publication_guard"][
            "matrix_release_decision_release_quality_publication_guard_passed"
        ]
        is None
    )


def test_phase2_status_compare_flags_missing_publish_preflight_release_quality_final_evidence(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=382))
    write_json(
        candidate,
        _status_payload(
            gate=382,
            publish_preflight_release_quality_publication_guard_final_checks_present=True,
            publish_preflight_release_quality_publication_guard_final_checks_passed=True,
            publish_preflight_release_quality_publication_guard_final_evidence_present=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    final_evidence_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_final_evidence_preserved"
    ]
    final_check = checks[
        "windows_publish_preflight_release_quality_publication_guard_final_checks_preserved"
    ]

    assert payload["status"] == "regressed"
    assert final_check["passed"] is True
    assert final_evidence_check["passed"] is False
    assert final_evidence_check["evidence"]["baseline"]["final_evidence_present"] is True
    assert final_evidence_check["evidence"]["candidate"]["final_evidence_present"] is False
    assert (
        payload["candidate"]["publish_preflight_release_quality_publication_guard"][
            "matrix_release_decision_release_quality_publication_guard_final_checks_ready"
        ]
        is None
    )


def test_phase2_status_compare_flags_publish_preflight_resident_fastpath_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=333))
    write_json(
        candidate,
        _status_payload(
            gate=334,
            status="attention_required",
            publish_preflight_resident_fastpath_handoff_ready=False,
            publish_preflight_resident_fastpath_handoff_raw_status="failed",
            publish_preflight_resident_fastpath_handoff_phase2_status=(
                "attention_required"
            ),
            publish_preflight_resident_fastpath_handoff_raw_check_count=0,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    handoff_check = checks[
        "windows_publish_preflight_resident_fastpath_handoff_preserved"
    ]
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["candidate"]["checks_passed"] is False
    status_check = checks[
        "windows_publish_preflight_resident_fastpath_handoff_status_preserved"
    ]
    assert status_check["passed"] is False
    candidate_statuses = status_check["evidence"]["candidate"]
    assert candidate_statuses["matrix_resident_fastpath_handoff_ready"] is False
    assert (
        candidate_statuses["matrix_resident_fastpath_handoff_raw_status"]
        == "failed"
    )
    assert candidate_statuses["matrix_resident_fastpath_handoff_raw_check_count"] == 0


def test_phase2_status_compare_flags_publish_preflight_resident_result_contract_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=343))
    write_json(
        candidate,
        _status_payload(
            gate=343,
            status="attention_required",
            publish_preflight_resident_result_contract_ready=False,
            publish_preflight_resident_result_contract_status="failed",
            publish_preflight_resident_result_contract_phase2_check_passed=False,
            publish_preflight_resident_result_contract_failed_count=1,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    handoff_check = checks[
        "windows_publish_preflight_resident_result_contract_handoff_preserved"
    ]
    assert handoff_check["passed"] is False
    assert handoff_check["evidence"]["candidate"]["checks_passed"] is False
    status_check = checks[
        "windows_publish_preflight_resident_result_contract_status_preserved"
    ]
    assert status_check["passed"] is False
    candidate_statuses = status_check["evidence"]["candidate"]
    assert candidate_statuses["matrix_resident_result_contract_ready"] is False
    assert candidate_statuses["matrix_resident_result_contract_status"] == "failed"
    assert candidate_statuses["matrix_resident_result_contract_failed_count"] == 1
    assert (
        payload["candidate"]["publish_preflight_resident_result_contract"][
            "matrix_resident_result_contract_status"
        ]
        == "failed"
    )


def test_phase2_status_compare_flags_publish_preflight_resident_winsorized_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=274))
    write_json(
        candidate,
        _status_payload(
            gate=275,
            publish_preflight_resident_winsorized_status="failed",
            publish_preflight_resident_winsorized_required_frame_passed=False,
            publish_preflight_resident_winsorized_check_count=26,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["windows_publish_preflight_resident_winsorized_sweep_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_resident_winsorized_sweep_preserved"][
        "evidence"
    ]["candidate"]["checks_passed"] is False
    assert checks["windows_publish_preflight_resident_winsorized_status_preserved"][
        "passed"
    ] is False
    candidate_statuses = checks[
        "windows_publish_preflight_resident_winsorized_status_preserved"
    ]["evidence"]["candidate"]
    assert candidate_statuses["matrix_resident_winsorized_sweep_status"] == "failed"
    assert (
        candidate_statuses[
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ]
        is False
    )
    assert candidate_statuses["matrix_resident_winsorized_sweep_check_count"] == 26


def test_phase2_status_compare_flags_publish_preflight_publication_audit_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=290))
    write_json(
        candidate,
        _status_payload(
            gate=291,
            publish_preflight_stack_publication_status="failed",
            publish_preflight_stack_publication_ready=False,
            publish_preflight_stack_publication_policy_agreement=False,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["windows_publish_preflight_stack_publication_audit_preserved"][
        "passed"
    ] is False
    assert checks["windows_publish_preflight_stack_publication_audit_preserved"][
        "evidence"
    ]["candidate"]["checks_passed"] is False
    assert checks["windows_publish_preflight_stack_publication_status_preserved"][
        "passed"
    ] is False
    candidate_statuses = checks[
        "windows_publish_preflight_stack_publication_status_preserved"
    ]["evidence"]["candidate"]
    assert candidate_statuses["matrix_stack_engine_publication_audit_status"] == "failed"
    assert candidate_statuses["matrix_stack_engine_publication_audit_ready"] is False
    assert (
        candidate_statuses["matrix_stack_engine_publication_policy_agreement"]
        is False
    )
    assert (
        payload["candidate"]["publish_preflight_stack_publication_audit"][
            "matrix_stack_engine_publication_audit_status"
        ]
        == "failed"
    )


def test_phase2_status_compare_flags_resident_winsorized_sweep_regression(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    write_json(baseline, _status_payload(gate=270))
    write_json(
        candidate,
        _status_payload(
            gate=271,
            resident_winsorized_sweep_passed=False,
            resident_winsorized_sweep_required_frame_passed=False,
            resident_winsorized_sweep_check_count=26,
        ),
    )

    payload = build_phase2_status_compare(
        baseline_status=baseline,
        candidate_status=candidate,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "regressed"
    assert checks["resident_winsorized_sweep_audit_passed_preserved"]["passed"] is False
    assert checks["resident_winsorized_sweep_required_frame_preserved"]["passed"] is False
    assert checks["resident_winsorized_sweep_check_count_not_decreased"]["passed"] is False
    assert checks["resident_winsorized_sweep_required_frame_preserved"]["evidence"][
        "candidate"
    ] == {"required_frame_count": 200, "required_frame_count_passed": False}
    assert payload["baseline"]["resident_winsorized_sweep_audit"]["check_count"] == 27
    assert payload["candidate"]["resident_winsorized_sweep_audit"]["check_count"] == 26


def test_cli_phase2_status_compare_writes_outputs_and_returns_failure(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "compare.json"
    markdown = tmp_path / "compare.md"
    write_json(baseline, _status_payload(gate=203))
    write_json(candidate, _status_payload(gate=202, cuda_available=False))

    result = main(
        [
            "phase2-status-compare",
            "--baseline-status",
            str(baseline),
            "--candidate-status",
            str(candidate),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-regression",
        ]
    )

    assert result == 2
    payload = read_json(out)
    assert payload["artifact_type"] == "glass_phase2_status_compare"
    assert payload["status"] == "regressed"
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status Compare" in text
    assert "latest_checkpoint_gate_not_decreased" in text
