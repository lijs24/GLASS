from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.phase2_status import build_phase2_status, build_phase2_status_compare


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
    rejection_sample_accounting_passed: bool = True,
    sample_accounting_closure_passed: bool = True,
    integration_engine_policy_passed: bool = True,
    runtime_default_passed: bool = True,
) -> None:
    pipeline_passed = (
        passed
        and rejection_sample_accounting_passed
        and sample_accounting_closure_passed
        and integration_engine_policy_passed
        and runtime_default_passed
    )
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
                {"name": "integration_resident_result_contract", "passed": passed},
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


def _write_release_decision(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
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
            "runtime_repeat": {
                "present": True,
                "run_count": 3,
                "considered_run_count": 3,
                "best_label": "repeat02",
                "best_elapsed_s": 22.6,
                "slowest_elapsed_s": 23.8,
                "elapsed_ratio_vs_best": 1.053,
                "max_elapsed_ratio_vs_best": 1.25,
                "recommendation": "best_observed:repeat02",
            },
            "pipeline_handoff": {
                "source": "explicit_pipeline_contract",
                "status": "passed",
                "passed": True,
                "pixel_verification_enabled": True,
            },
        },
    )


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
    stack_publication_audit_ready: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
    include_stack_publication_audit: bool = True,
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
        (
            stack_publication_audit_ready
            and stack_publication_policy_ready
            and stack_publication_resident_winsorized_ready
        )
        or not include_stack_publication_audit
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
    direct_runtime_ready: bool = True,
) -> None:
    artifact_ready = (
        passed
        and integration_engine_policy_ready
        and resident_winsorized_ready
        and direct_runtime_ready
    )
    status = "passed" if artifact_ready else "blocked"
    policy_status = (
        "publish_preflight_ready" if integration_engine_policy_ready else "blocked"
    )
    winsorized_status = (
        "publish_preflight_ready" if resident_winsorized_ready else "blocked"
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
    publish_preflight_resident_winsorized_status: str = "passed",
    publish_preflight_resident_winsorized_required_frame_passed: bool = True,
    publish_preflight_resident_winsorized_check_count: int = 27,
    publish_preflight_stack_publication_status: str = "passed",
    publish_preflight_stack_publication_ready: bool = True,
    publish_preflight_stack_publication_policy_agreement: bool = True,
    publish_preflight_stack_publication_resident_winsorized_agreement: bool = True,
    stack_publication_passed: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
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
            "check_count": 21,
            "failed_check_count": 0 if stack_publication_passed else 1,
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
    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert checks["resident_registration_fastpath_contract_passed_for_default"] is True
    assert checks["acceptance_pipeline_integration_engine_policy_passed"] is True
    assert checks["acceptance_pipeline_stack_engine_runtime_default_passed"] is True
    assert checks["default_route_acceptance_passed"] is True
    assert checks["default_route_acceptance_route_contract_passed"] is True
    assert checks["pipeline_integration_engine_policy_passed"] is True
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
    winsorized_audit = tmp_path / "resident_winsorized_benchmark_audit.json"
    winsorized_sweep_audit = tmp_path / "resident_winsorized_sweep_audit.json"
    _write_acceptance(acceptance)
    _write_default_route_acceptance(default_route_acceptance)
    _write_pipeline_contract(pipeline_contract)
    _write_stack_engine_contract(stack_engine_contract)
    _write_release_decision(release_decision)
    _write_publish_preflight(publish_preflight)
    _write_stack_engine_publication_audit(publication_audit)
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
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS Phase 2 Status" in text
    assert "Acceptance" in text
    assert "Native resident result source: run_default" in text
    assert "Native calibrated lights: 200" in text
    assert "Registration fast path: present" in text
    assert "Registration fast path contract: passed" in text
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
    assert status["publish_preflight"]["status"] == "publish_preflight_ready"
    assert direct_check["passed"] is False
    assert direct_check["evidence"]["matrix_ready"] is True
    assert direct_check["evidence"]["matrix_acceptance_source"] == "phase2_status_handoff"
    assert direct_check["evidence"]["matrix_acceptance_check"] is False
    assert direct_check["evidence"]["matrix_pipeline_check"] is True


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
    assert checks["windows_publish_preflight_resident_winsorized_sweep_preserved"] is True
    assert checks["windows_publish_preflight_resident_winsorized_status_preserved"] is True
    assert checks["stack_engine_publication_audit_passed_preserved"] is True
    assert checks["stack_engine_publication_policy_chain_preserved"] is True
    assert checks["stack_engine_publication_resident_winsorized_chain_preserved"] is True
    assert checks["stack_engine_publication_direct_runtime_chain_preserved"] is True
    assert checks["pipeline_contract_passed_preserved"] is True
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
            stack_publication_passed=False,
            stack_publication_policy_ready=False,
            stack_publication_resident_winsorized_ready=False,
            pipeline_passed=False,
            pipeline_dq_contract=False,
            pixel_verification=False,
            pipeline_engine_policy_status="failed",
            pipeline_runtime_default_status="failed",
            pipeline_runtime_default_legacy_master_count=1,
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
    assert checks["stack_engine_publication_audit_passed_preserved"] is False
    assert checks["stack_engine_publication_policy_chain_preserved"] is False
    assert checks["stack_engine_publication_resident_winsorized_chain_preserved"] is False
    assert checks["stack_engine_publication_direct_runtime_chain_preserved"] is False
    assert checks["pipeline_contract_passed_preserved"] is False
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
