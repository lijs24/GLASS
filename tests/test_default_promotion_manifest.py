from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.gpu.compatibility import recommend_windows_cuda_packages
from glass.io.json_io import read_json, write_json
from glass.report.default_promotion_manifest import build_default_promotion_manifest


def _write_release_decision(
    path: Path,
    *,
    ready: bool = True,
    include_direct_publication_guard: bool = True,
    direct_publication_guard_ready: bool = True,
    include_resident_fastpath_handoff: bool = True,
    resident_fastpath_ready: bool = True,
    direct_acceptance_source: str = "explicit_resident_artifacts_json",
    direct_calibration_source: str = "resident_artifacts_json_fallback",
    direct_resident_lights: int = 200,
    include_quality_publication_guard: bool = True,
    quality_publication_guard_ready: bool = True,
    quality_publication_compare_present: bool = True,
    phase2_quality_publication_guard_ready: bool | None = None,
) -> None:
    phase2_quality_publication_guard_ready = (
        quality_publication_guard_ready
        if phase2_quality_publication_guard_ready is None
        else phase2_quality_publication_guard_ready
    )
    direct_guard = {
        "present": True,
        "ready": direct_publication_guard_ready,
        "decision_check_passed": direct_publication_guard_ready,
        "status": "passed" if direct_publication_guard_ready else "blocked",
        "passed": direct_publication_guard_ready,
        "checks_passed": direct_publication_guard_ready,
        "source_ready": direct_publication_guard_ready,
        "count_ready": direct_publication_guard_ready,
        "leaf_checks_ready": direct_publication_guard_ready,
        "raw_ready": direct_publication_guard_ready,
        "phase2_ready": direct_publication_guard_ready,
        "phase2_check_passed": direct_publication_guard_ready,
        "raw_source_ready": direct_publication_guard_ready,
        "phase2_source_ready": direct_publication_guard_ready,
        "raw_count_ready": direct_publication_guard_ready,
        "phase2_count_ready": direct_publication_guard_ready,
        "raw_leaf_checks_ready": direct_publication_guard_ready,
        "phase2_leaf_checks_ready": direct_publication_guard_ready,
        "raw_matrix_acceptance_source": direct_acceptance_source,
        "raw_default_promotion_acceptance_source": direct_acceptance_source,
        "phase2_matrix_acceptance_source": direct_acceptance_source,
        "phase2_default_promotion_acceptance_source": direct_acceptance_source,
        "raw_matrix_acceptance_check_count": 24,
        "raw_default_promotion_acceptance_check_count": 24,
        "phase2_matrix_acceptance_check_count": 24,
        "phase2_default_promotion_acceptance_check_count": 24,
        "raw_matrix_pipeline_calibration_source": direct_calibration_source,
        "raw_default_promotion_pipeline_calibration_source": direct_calibration_source,
        "phase2_matrix_pipeline_calibration_source": direct_calibration_source,
        "phase2_default_promotion_pipeline_calibration_source": direct_calibration_source,
        "raw_matrix_pipeline_resident_lights": direct_resident_lights,
        "raw_default_promotion_pipeline_resident_lights": direct_resident_lights,
        "phase2_matrix_pipeline_resident_lights": direct_resident_lights,
        "phase2_default_promotion_pipeline_resident_lights": direct_resident_lights,
    }
    checks = []
    if include_direct_publication_guard:
        checks.append(
            {
                "name": "stack_engine_publication_direct_runtime_evidence_passed",
                "passed": direct_publication_guard_ready,
            }
        )
    quality_status = "passed" if quality_publication_guard_ready else "blocked"
    phase2_quality_status = (
        "passed" if phase2_quality_publication_guard_ready else "blocked"
    )
    quality_guard = (
        {
            "present": True,
            "ready": (
                quality_publication_guard_ready
                and phase2_quality_publication_guard_ready
            ),
            "status": quality_status
            if quality_publication_guard_ready
            else "blocked",
            "passed": (
                quality_publication_guard_ready
                and phase2_quality_publication_guard_ready
            ),
            "checks_passed": (
                quality_publication_guard_ready
                and phase2_quality_publication_guard_ready
            ),
            "compatible_missing": not quality_publication_compare_present,
            "quality_compare_present": quality_publication_compare_present,
            "raw_present": quality_publication_compare_present,
            "raw_ready": quality_publication_guard_ready,
            "raw_matrix_status": quality_status,
            "raw_matrix_failed_check_count": (
                0 if quality_publication_guard_ready else 1
            ),
            "raw_default_promotion_status": quality_status,
            "raw_default_promotion_failed_check_count": (
                0 if quality_publication_guard_ready else 1
            ),
            "phase2_present": quality_publication_compare_present,
            "phase2_ready": phase2_quality_publication_guard_ready,
            "phase2_check_passed": phase2_quality_publication_guard_ready,
            "phase2_matrix_status": phase2_quality_status,
            "phase2_matrix_failed_check_count": (
                0 if phase2_quality_publication_guard_ready else 1
            ),
            "phase2_default_promotion_status": phase2_quality_status,
            "phase2_default_promotion_failed_check_count": (
                0 if phase2_quality_publication_guard_ready else 1
            ),
            "failed_checks": []
            if quality_publication_guard_ready
            and phase2_quality_publication_guard_ready
            else ["stack_engine_publication_quality_metrics_compare_passed"],
        }
        if include_quality_publication_guard
        else {}
    )
    if include_quality_publication_guard:
        checks.append(
            {
                "name": "stack_engine_publication_quality_metrics_compare_passed",
                "passed": (
                    quality_publication_guard_ready
                    and phase2_quality_publication_guard_ready
                ),
            }
        )
    if include_resident_fastpath_handoff:
        checks.append(
            {
                "name": "resident_registration_fastpath_handoff",
                "passed": resident_fastpath_ready,
            }
        )
    fastpath_failed_checks = (
        []
        if resident_fastpath_ready
        else ["contract_resident_registration_fastpath_descriptor_batch_mode"]
    )
    resident_fastpath_handoff = (
        {
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
            "failed_checks": fastpath_failed_checks,
            "failed_acceptance_checks": fastpath_failed_checks,
        }
        if include_resident_fastpath_handoff
        else {}
    )
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
            "speedup": {"actual": 58.1, "required_min": 2.0},
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
            "pipeline_resident_winsorized_semantics_release": {
                "schema_version": 1,
                "status": "passed",
                "ready": True,
                "scope": "passed",
                "output_count": 1,
                "required_count": 1,
                "failed_count": 0,
                "legacy_completion_count": 1,
                "descriptor_sources": [
                    "resident_artifacts.integration_rejection"
                ],
                "failed_items": [],
                "rows": [
                    {
                        "item": "H",
                        "required": True,
                        "present": True,
                        "passed": True,
                        "status": "passed",
                        "rejection": "winsorized_sigma",
                        "descriptor_source": (
                            "resident_artifacts.integration_rejection"
                        ),
                        "integration_results_descriptor_present": False,
                        "resident_artifacts_descriptor_present": True,
                        "legacy_completion_applied": True,
                        "legacy_completion_source": "fast_approx_algorithm",
                        "resident_winsorized_mode": "fast_approx",
                        "algorithm": (
                            "two_stage_winsorized_mean_std_rejection_approximation"
                        ),
                        "scale_estimator": "mean_std_two_stage_winsorized",
                        "cpu_baseline_parity": False,
                        "parity_status": "known_non_parity_pending_cuda_update",
                        "approximation": True,
                    }
                ],
            },
            "stack_engine_publication_direct_runtime_evidence": direct_guard
            if include_direct_publication_guard
            else {},
            "stack_engine_publication_quality_metrics_compare": quality_guard,
            "resident_registration_fastpath_handoff": resident_fastpath_handoff,
            "checks": checks,
        },
    )


def _write_phase2_status(
    path: Path,
    decision: Path,
    *,
    ready: bool = True,
    include_default_route: bool = True,
    default_route_ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
    sample_accounting_closure_ready: bool = True,
    resident_result_contract_ready: bool = True,
    include_stack_engine_contract: bool = True,
    stack_engine_ready: bool = True,
    stack_engine_gap_count: int = 0,
    include_resident_winsorized_sweep: bool = True,
    resident_winsorized_sweep_ready: bool = True,
    resident_winsorized_sweep_required_frame_ready: bool = True,
    resident_winsorized_sweep_check_count: int = 27,
    resident_winsorized_sweep_required_frame_count: int = 200,
    include_stack_publication_audit: bool = True,
    stack_publication_audit_ready: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
    include_integration_engine_policy: bool = True,
    acceptance_integration_engine_policy_ready: bool = True,
    pipeline_integration_engine_policy_ready: bool = True,
    pipeline_integration_engine_policy_check_present: bool = True,
    include_stack_engine_runtime_default: bool = True,
    acceptance_stack_engine_runtime_default_ready: bool = True,
    pipeline_stack_engine_runtime_default_ready: bool = True,
    pipeline_stack_engine_runtime_default_check_present: bool = True,
    include_resident_fastpath_handoff: bool = True,
    resident_fastpath_ready: bool = True,
    include_quality_metrics_compare: bool = True,
    quality_metrics_compare_ready: bool = True,
) -> None:
    acceptance_policy_chain_ready = (
        acceptance_integration_engine_policy_ready
        if include_integration_engine_policy
        else True
    )
    pipeline_policy_chain_ready = (
        pipeline_integration_engine_policy_ready
        and pipeline_integration_engine_policy_check_present
        if include_integration_engine_policy
        else True
    )
    acceptance_runtime_default_chain_ready = (
        acceptance_stack_engine_runtime_default_ready
        if include_stack_engine_runtime_default
        else True
    )
    pipeline_runtime_default_chain_ready = (
        pipeline_stack_engine_runtime_default_ready
        and pipeline_stack_engine_runtime_default_check_present
        if include_stack_engine_runtime_default
        else True
    )
    pipeline_ready = (
        ready
        and resident_result_contract_ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and pipeline_policy_chain_ready
        and pipeline_runtime_default_chain_ready
    )
    phase2_ready = (
        pipeline_ready
        and acceptance_policy_chain_ready
        and acceptance_runtime_default_chain_ready
        and (resident_fastpath_ready if include_resident_fastpath_handoff else True)
        and (stack_engine_ready if include_stack_engine_contract else True)
        and (
            stack_publication_audit_ready
            and stack_publication_policy_ready
            and stack_publication_resident_winsorized_ready
            if include_stack_publication_audit
            else True
        )
        and (
            resident_winsorized_sweep_ready
            and resident_winsorized_sweep_required_frame_ready
            if include_resident_winsorized_sweep
            else True
        )
        and (
            quality_metrics_compare_ready
            if include_quality_metrics_compare
            else True
        )
    )
    failed_pipeline_checks = []
    if not resident_result_contract_ready:
        failed_pipeline_checks.append("integration_resident_result_contract")
    if not rejection_sample_accounting_ready:
        failed_pipeline_checks.append("integration_rejection_sample_counts_match_maps")
    if not sample_accounting_closure_ready:
        failed_pipeline_checks.append("integration_sample_accounting_closure")
    if include_integration_engine_policy and not pipeline_policy_chain_ready:
        failed_pipeline_checks.append("integration_default_engine_policy")
    if include_stack_engine_runtime_default and not pipeline_runtime_default_chain_ready:
        failed_pipeline_checks.append("stack_engine_runtime_default_path")
    stack_engine_recommendation = (
        "stack_engine_default_ready"
        if stack_engine_ready and stack_engine_gap_count == 0
        else "stack_engine_contract_gaps_remain"
    )
    payload = {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "status": "green" if phase2_ready else "attention_required",
        "passed": phase2_ready,
        "latest_checkpoint": {
            "gate": 252,
            "status": "green" if ready else "failed",
            "green": ready,
        },
        "release_decision": {
            "artifact_type": "release_promotion_decision",
            "path": str(decision),
            "status": "default_change_ready" if ready else "release_candidate_ready",
            "passed": True,
            "release_candidate_ready": True,
            "default_change_ready": ready,
            "recommendation": "promote_default_candidate"
            if ready
            else "repeat_benchmark_before_default_change",
            "runtime_repeat_present": True,
            "runtime_repeat_considered_run_count": 3,
            "runtime_repeat_elapsed_ratio_vs_best": 1.053,
            "resident_registration_fastpath_handoff": {
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
                "failed_checks": []
                if resident_fastpath_ready
                else ["contract_resident_registration_fastpath_descriptor_batch_mode"],
                "failed_acceptance_checks": []
                if resident_fastpath_ready
                else ["contract_resident_registration_fastpath_descriptor_batch_mode"],
            }
            if include_resident_fastpath_handoff
            else None,
        },
            "pipeline_contract": {
                "audit_type": "pipeline_invariant_contract",
                "status": "passed" if pipeline_ready else "failed",
            "passed": pipeline_ready,
            "check_count": 16,
            "failed_check_count": len(failed_pipeline_checks),
            "failed_checks": failed_pipeline_checks,
            "integration_output_count": 1,
            "integration_map_count": 6,
            "integration_dq_contract": True,
            "integration_stack_result_contract": True,
            "integration_resident_result_contract": resident_result_contract_ready,
            "resident_result_contract": {
                "status": "passed" if resident_result_contract_ready else "failed",
                "check_present": True,
                "check_passed": resident_result_contract_ready,
                "required_count": 1,
                "failed_count": 0 if resident_result_contract_ready else 1,
                "failed_check_count": 0 if resident_result_contract_ready else 1,
                "failed_checks": []
                if resident_result_contract_ready
                else ["source_terms_present"],
                "failed_items": []
                if resident_result_contract_ready
                else [
                    {
                        "item": "H",
                        "backend": "cuda_resident_stack",
                        "memory_mode": "resident",
                        "status": "failed",
                        "required": True,
                        "passed": False,
                        "failed_checks": [
                            {
                                "name": "source_terms_present",
                                "evidence": {
                                    "actual": [],
                                    "available": False,
                                    "required": True,
                                },
                            }
                        ],
                    }
                ],
            },
            "integration_resident_result_contract_status": "passed"
            if resident_result_contract_ready
            else "failed",
            "integration_resident_result_contract_check_present": True,
            "integration_resident_result_contract_check_passed": (
                resident_result_contract_ready
            ),
            "integration_resident_result_contract_required_count": 1,
            "integration_resident_result_contract_failed_count": 0
            if resident_result_contract_ready
            else 1,
            "integration_resident_result_contract_failed_check_count": 0
            if resident_result_contract_ready
            else 1,
            "integration_resident_result_contract_failed_checks": []
            if resident_result_contract_ready
            else ["source_terms_present"],
            "integration_resident_result_contract_failed_items": []
            if resident_result_contract_ready
            else [
                {
                    "item": "H",
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "status": "failed",
                    "required": True,
                    "passed": False,
                }
            ],
            "integration_dq_map_pixels_match_summary": True,
            "integration_coverage_map_pixels_match_dq": True,
            "integration_rejection_map_pixels_match_dq": True,
            "integration_rejection_sample_counts_match_maps": rejection_sample_accounting_ready,
            "integration_sample_accounting_closure": sample_accounting_closure_ready,
            "rejection_sample_accounting": {
                "status": "passed" if rejection_sample_accounting_ready else "failed",
                "check_present": True,
                "check_passed": rejection_sample_accounting_ready,
                "failed_count": 0 if rejection_sample_accounting_ready else 1,
                "failed_items": []
                if rejection_sample_accounting_ready
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
            "rejection_sample_accounting_status": "passed"
            if rejection_sample_accounting_ready
            else "failed",
            "rejection_sample_accounting_failed_count": 0
            if rejection_sample_accounting_ready
            else 1,
            "sample_accounting_closure": {
                "status": "passed" if sample_accounting_closure_ready else "failed",
                "check_present": True,
                "check_passed": sample_accounting_closure_ready,
                "present_count": 1,
                "failed_count": 0 if sample_accounting_closure_ready else 1,
                "failed_items": []
                if sample_accounting_closure_ready
                else [
                    {
                        "item": "H",
                        "input_valid_samples_before_rejection": 9,
                        "valid_samples_after_rejection": 6,
                        "rejected_samples": 2,
                    }
                ],
            },
            "sample_accounting_closure_status": "passed"
            if sample_accounting_closure_ready
            else "failed",
            "sample_accounting_closure_present_count": 1,
            "sample_accounting_closure_failed_count": 0
            if sample_accounting_closure_ready
            else 1,
            "pixel_verification_enabled": True,
            "pixel_verification_tile_size": 2048,
            "resident_native_calibration_artifact": True,
            "resident_calibrated_light_count": 200,
        },
        "checks": [
            {
                "name": "stack_engine_default_contract_ready",
                "passed": stack_engine_ready if include_stack_engine_contract else False,
            },
            {
                "name": "release_decision_resident_fastpath_handoff_ready",
                "passed": resident_fastpath_ready
                if include_resident_fastpath_handoff
                else False,
            },
            {
                "name": "pipeline_resident_result_contract_passed",
                "passed": resident_result_contract_ready,
            },
        ],
    }
    if include_integration_engine_policy or include_stack_engine_runtime_default:
        acceptance_ready = (
            acceptance_policy_chain_ready and acceptance_runtime_default_chain_ready
        )
        payload["acceptance_audit"] = {
            "status": "passed" if acceptance_ready else "failed",
            "passed": acceptance_ready,
        }
    if include_integration_engine_policy:
        acceptance_policy_status = (
            "passed" if acceptance_integration_engine_policy_ready else "failed"
        )
        pipeline_policy_status = (
            "passed"
            if pipeline_integration_engine_policy_ready
            else "failed"
        )
        acceptance_failed_items = (
            []
            if acceptance_integration_engine_policy_ready
            else [
                {
                    "item": "H",
                    "status": "implicit_cuda_fast_path",
                    "backend": "cuda",
                    "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                    "failures": ["cuda_fast_path_not_explicit"],
                }
            ]
        )
        pipeline_failed_items = (
            []
            if pipeline_integration_engine_policy_ready
            else [
                {
                    "item": "H",
                    "status": "implicit_cuda_fast_path",
                    "backend": "cuda",
                    "tile_stack_mode": "cuda_streaming_accumulator_fast_path",
                    "failures": ["cuda_fast_path_not_explicit"],
                }
            ]
        )
        payload["acceptance_audit"].update(
            {
                "pipeline_integration_engine_policy_status": acceptance_policy_status,
                "pipeline_integration_engine_policy_check_present": True,
                "pipeline_integration_engine_policy_check_passed": (
                    acceptance_integration_engine_policy_ready
                ),
                "pipeline_integration_engine_policy_non_resident_count": 0
                if acceptance_integration_engine_policy_ready
                else 1,
                "pipeline_integration_engine_policy_failed_count": 0
                if acceptance_integration_engine_policy_ready
                else 1,
                "pipeline_integration_engine_policy": {
                    "status": acceptance_policy_status,
                    "check_name": "integration_default_engine_policy",
                    "check_present": True,
                    "check_passed": acceptance_integration_engine_policy_ready,
                    "non_resident_count": 0
                    if acceptance_integration_engine_policy_ready
                    else 1,
                    "resident_count": 1
                    if acceptance_integration_engine_policy_ready
                    else 0,
                    "failed_count": 0
                    if acceptance_integration_engine_policy_ready
                    else 1,
                    "failed_items": acceptance_failed_items,
                },
            }
        )
        payload["pipeline_contract"].update(
            {
                "integration_default_engine_policy": (
                    pipeline_integration_engine_policy_ready
                    if pipeline_integration_engine_policy_check_present
                    else None
                ),
                "integration_engine_policy_status": pipeline_policy_status,
                "integration_engine_policy_check_present": (
                    pipeline_integration_engine_policy_check_present
                ),
                "integration_engine_policy_check_passed": (
                    pipeline_integration_engine_policy_ready
                    if pipeline_integration_engine_policy_check_present
                    else None
                ),
                "integration_engine_policy_non_resident_count": 0
                if pipeline_integration_engine_policy_ready
                else 1,
                "integration_engine_policy_failed_count": 0
                if pipeline_integration_engine_policy_ready
                else 1,
                "integration_engine_policy": {
                    "status": pipeline_policy_status,
                    "check_present": pipeline_integration_engine_policy_check_present,
                    "check_passed": pipeline_integration_engine_policy_ready
                    if pipeline_integration_engine_policy_check_present
                    else None,
                    "non_resident_count": 0
                    if pipeline_integration_engine_policy_ready
                    else 1,
                    "resident_count": 1 if pipeline_integration_engine_policy_ready else 0,
                    "failed_count": 0
                    if pipeline_integration_engine_policy_ready
                    else 1,
                    "failed_items": pipeline_failed_items,
                },
            }
        )
        payload["checks"].extend(
            [
                {
                    "name": "acceptance_pipeline_integration_engine_policy_passed",
                    "passed": acceptance_policy_chain_ready,
                },
                {
                    "name": "pipeline_integration_engine_policy_passed",
                    "passed": pipeline_policy_chain_ready,
                },
            ]
        )
    if include_stack_engine_runtime_default:
        acceptance_runtime_status = (
            "passed" if acceptance_stack_engine_runtime_default_ready else "failed"
        )
        pipeline_runtime_status = (
            "passed" if pipeline_stack_engine_runtime_default_ready else "failed"
        )
        acceptance_failed_masters = (
            []
            if acceptance_stack_engine_runtime_default_ready
            else [
                {
                    "group_id": "bias_0",
                    "engine_family": "legacy",
                    "reason": "legacy_master_accumulator",
                }
            ]
        )
        pipeline_failed_outputs = (
            []
            if pipeline_stack_engine_runtime_default_ready
            else [
                {
                    "item": "H",
                    "engine_family": "legacy",
                    "reason": "legacy_or_unknown_engine",
                }
            ]
        )
        payload["acceptance_audit"].update(
            {
                "pipeline_stack_engine_runtime_default_status": (
                    acceptance_runtime_status
                ),
                "pipeline_stack_engine_runtime_default_check_present": True,
                "pipeline_stack_engine_runtime_default_check_passed": (
                    acceptance_stack_engine_runtime_default_ready
                ),
                "pipeline_stack_engine_runtime_default_master_count": 3,
                "pipeline_stack_engine_runtime_default_legacy_master_count": (
                    0 if acceptance_stack_engine_runtime_default_ready else 1
                ),
                "pipeline_stack_engine_runtime_default_failed_master_count": (
                    0 if acceptance_stack_engine_runtime_default_ready else 1
                ),
                "pipeline_stack_engine_runtime_default_failed_output_count": 0,
                "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": 1,
                "pipeline_stack_engine_runtime_default": {
                    "status": acceptance_runtime_status,
                    "check_name": "stack_engine_runtime_default_path",
                    "check_present": True,
                    "check_passed": acceptance_stack_engine_runtime_default_ready,
                    "master_count": 3,
                    "master_stack_engine_count": 3
                    if acceptance_stack_engine_runtime_default_ready
                    else 2,
                    "master_resident_count": 0,
                    "legacy_master_count": 0
                    if acceptance_stack_engine_runtime_default_ready
                    else 1,
                    "integration_output_count": 1,
                    "integration_stack_engine_default_count": 1,
                    "integration_resident_count": 0,
                    "explicit_cuda_fast_path_count": 1,
                    "failed_master_count": 0
                    if acceptance_stack_engine_runtime_default_ready
                    else 1,
                    "failed_output_count": 0,
                    "failed_masters": acceptance_failed_masters,
                    "failed_outputs": [],
                },
            }
        )
        payload["pipeline_contract"].update(
            {
                "stack_engine_runtime_default_status": pipeline_runtime_status,
                "stack_engine_runtime_default_check_present": (
                    pipeline_stack_engine_runtime_default_check_present
                ),
                "stack_engine_runtime_default_check_passed": (
                    pipeline_stack_engine_runtime_default_ready
                    if pipeline_stack_engine_runtime_default_check_present
                    else None
                ),
                "stack_engine_runtime_default_legacy_master_count": 0,
                "stack_engine_runtime_default_failed_master_count": 0,
                "stack_engine_runtime_default_failed_output_count": (
                    0 if pipeline_stack_engine_runtime_default_ready else 1
                ),
                "stack_engine_runtime_default_explicit_cuda_fast_path_count": 1,
                "stack_engine_runtime_default": {
                    "status": pipeline_runtime_status,
                    "check_name": "stack_engine_runtime_default_path",
                    "check_present": (
                        pipeline_stack_engine_runtime_default_check_present
                    ),
                    "check_passed": pipeline_stack_engine_runtime_default_ready
                    if pipeline_stack_engine_runtime_default_check_present
                    else None,
                    "master_count": 3,
                    "master_stack_engine_count": 3,
                    "master_resident_count": 0,
                    "legacy_master_count": 0,
                    "integration_output_count": 1,
                    "integration_stack_engine_default_count": 1
                    if pipeline_stack_engine_runtime_default_ready
                    else 0,
                    "integration_resident_count": 0,
                    "explicit_cuda_fast_path_count": 1,
                    "failed_master_count": 0,
                    "failed_output_count": 0
                    if pipeline_stack_engine_runtime_default_ready
                    else 1,
                    "failed_masters": [],
                    "failed_outputs": pipeline_failed_outputs,
                },
            }
        )
        payload["checks"].extend(
            [
                {
                    "name": "acceptance_pipeline_stack_engine_runtime_default_passed",
                    "passed": acceptance_stack_engine_runtime_default_ready,
                },
                {
                    "name": "pipeline_stack_engine_runtime_default_passed",
                    "passed": pipeline_runtime_default_chain_ready,
                },
            ]
        )
    if include_quality_metrics_compare:
        payload["quality_metrics_compare"] = {
            "status": "passed" if quality_metrics_compare_ready else "failed",
            "passed": quality_metrics_compare_ready,
            "check_count": 3 if quality_metrics_compare_ready else 4,
            "failed_check_count": 0 if quality_metrics_compare_ready else 1,
            "failed_checks": []
            if quality_metrics_compare_ready
            else ["bad_median_ratio_within_limit"],
            "baseline_metric_count": 7,
            "candidate_metric_count": 7,
            "metric_row_count": 7,
            "threshold_failure_count": 0 if quality_metrics_compare_ready else 1,
            "threshold_failures": []
            if quality_metrics_compare_ready
            else [{"metric": "fwhm_px", "bad_median_ratio": 1.4}],
            "path": "runs/checkpoints/quality_metrics_compare.json",
        }
        payload["checks"].append(
            {
                "name": "quality_metrics_compare_passed",
                "passed": quality_metrics_compare_ready,
            }
        )
    if include_resident_winsorized_sweep:
        payload["resident_winsorized_sweep_audit"] = {
            "schema_version": 1,
            "path": "C:/glass_runs/run/resident_winsorized_sweep_audit.json",
            "status": "passed" if resident_winsorized_sweep_ready else "failed",
            "passed": resident_winsorized_sweep_ready,
            "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
            "contract_path": "benchmarks/resident_winsorized_sweep_contract.json",
            "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
            "check_count": resident_winsorized_sweep_check_count,
            "failed_check_count": 0 if resident_winsorized_sweep_ready else 1,
            "failed_checks": []
            if resident_winsorized_sweep_ready
            else ["frame_200_hardened_master_rms_within_contract"],
            "frame_counts": [8, 32, 128, 200],
            "run_count": 4,
            "required_frame_count": resident_winsorized_sweep_required_frame_count,
            "required_frame_count_passed": resident_winsorized_sweep_required_frame_ready,
            "required_frame_master_rms": 2.3e-5,
            "required_frame_master_max_abs": 6.1e-5,
            "max_hardened_master_rms": 2.3e-5,
            "required_frame_cuda_hardened_s": 0.0012,
        }
        payload["checks"].append(
            {
                "name": "resident_winsorized_sweep_audit_passed",
                "passed": resident_winsorized_sweep_ready,
            }
        )
    if include_stack_engine_contract:
        payload["stack_engine_contract"] = {
            "path": "C:/glass_runs/run/stack_engine_contract.json",
            "audit_type": "stack_engine_default_contract",
            "status": "passed",
            "passed": True,
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "adoption_recommendation": stack_engine_recommendation,
            "adoption_surface_count": 4,
            "adoption_contract_ready_count": 4 - stack_engine_gap_count,
            "adoption_stack_engine_surface_count": 4 - stack_engine_gap_count,
            "adoption_cuda_resident_surface_count": 0,
            "adoption_phase2_stack_engine_default_gap_count": stack_engine_gap_count,
            "adoption_gap_surfaces": [
                {
                    "surface": "integration",
                    "item": "H",
                    "engine_family": "legacy",
                    "gap_reason": "legacy_or_unknown_engine",
                }
            ]
            if stack_engine_gap_count
            else [],
            "default_promotion_ready": stack_engine_ready,
            "default_promotion_status": "ready" if stack_engine_ready else "blocked",
            "default_promotion_recommendation": stack_engine_recommendation,
            "default_promotion_phase2_stack_engine_default_gap_count": (
                stack_engine_gap_count
            ),
            "default_promotion_blocker_count": 0 if stack_engine_ready else 1,
            "default_promotion_blockers": []
            if stack_engine_ready
            else [
                {
                    "name": "phase2_stack_engine_default_gaps",
                    "gap_count": stack_engine_gap_count,
                }
            ],
        }
    if include_stack_publication_audit:
        publication_failed_checks = []
        if not stack_publication_audit_ready:
            publication_failed_checks.append("stack_engine_publication_audit_passed")
        if not stack_publication_policy_ready:
            publication_failed_checks.append(
                "stack_engine_publication_audit_policy_chain_passed"
            )
        if not stack_publication_resident_winsorized_ready:
            publication_failed_checks.append(
                "stack_engine_publication_audit_resident_winsorized_chain_passed"
            )
        payload["stack_engine_publication_audit"] = {
            "path": "C:/glass_runs/run/stack_engine_publication_audit.json",
            "status": "passed" if stack_publication_audit_ready else "blocked",
            "passed": stack_publication_audit_ready,
            "recommendation": "publication_chain_ready"
            if stack_publication_audit_ready
            else "fix_stack_engine_publication_chain",
            "check_count": 21,
            "failed_check_count": len(publication_failed_checks),
            "failed_checks": publication_failed_checks,
            "publish_preflight_integration_engine_policy": {
                "status": "publish_preflight_ready"
                if stack_publication_policy_ready
                else "blocked",
                "ready": stack_publication_policy_ready,
            },
            "phase2_publish_preflight_integration_engine_policy": {
                "status": "publish_preflight_ready"
                if stack_publication_policy_ready
                else "blocked",
                "ready": stack_publication_policy_ready,
            },
            "publish_preflight_integration_engine_policy_ready": (
                stack_publication_policy_ready
            ),
            "phase2_publish_preflight_integration_engine_policy_ready": (
                stack_publication_policy_ready
            ),
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight": (
                stack_publication_policy_ready
            ),
            "publish_preflight_resident_winsorized_sweep": {
                "status": "publish_preflight_ready"
                if stack_publication_resident_winsorized_ready
                else "blocked",
                "ready": stack_publication_resident_winsorized_ready,
            },
            "phase2_publish_preflight_resident_winsorized_sweep": {
                "status": "publish_preflight_ready"
                if stack_publication_resident_winsorized_ready
                else "blocked",
                "ready": stack_publication_resident_winsorized_ready,
            },
            "publish_preflight_resident_winsorized_sweep_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_publish_preflight_resident_winsorized_sweep_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight": (
                stack_publication_resident_winsorized_ready
            ),
        }
        payload["checks"].extend(
            [
                {
                    "name": "stack_engine_publication_audit_passed",
                    "passed": stack_publication_audit_ready,
                },
                {
                    "name": "stack_engine_publication_audit_policy_chain_passed",
                    "passed": stack_publication_policy_ready,
                },
                {
                    "name": "stack_engine_publication_audit_resident_winsorized_chain_passed",
                    "passed": stack_publication_resident_winsorized_ready,
                },
            ]
        )
    if include_default_route:
        payload["default_route_acceptance"] = {
            "path": "C:/glass_runs/run/default_route_acceptance.json",
            "status": "passed" if default_route_ready else "failed",
            "passed": default_route_ready,
            "acceptance_passed": default_route_ready,
            "benchmark_contract": {"name": "default_route_fixture_contract"},
            "speedup_vs_reference": 28.75,
            "active_frames": 193,
            "route_contract_passed": default_route_ready,
            "route_check_count": 4 if default_route_ready else 2,
            "route_failed_checks": []
            if default_route_ready
            else ["contract_required_command_token:--backend cuda"],
        }
    write_json(path, payload)


def _write_doctor(path: Path) -> None:
    devices = [
        {
            "device_id": 0,
            "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
            "compute_capability": "12.0",
            "driver_version": "596.21",
        }
    ]
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "recommendation": "cuda",
            "cuda": {
                "wrapper_importable": True,
                "native_extension_loaded": True,
                "cuda_available": True,
                "probe_skipped": False,
                "devices": devices,
            },
            "windows_cuda_packages": recommend_windows_cuda_packages(devices),
        },
    )


def test_default_promotion_manifest_passes_ready_artifacts(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    doctor = tmp_path / "doctor.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision)
    _write_doctor(doctor)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        doctor_json=doctor,
        require_doctor=True,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "default_promotion_ready"
    assert payload["recommendation"] == "promote_resident_cuda_default"
    assert payload["default_candidate"]["memory_mode"] == "resident"
    assert payload["default_candidate"]["fallback_memory_mode"] == "tile"
    assert payload["default_route_acceptance"]["route_contract_passed"] is True
    assert payload["stack_engine_contract"]["ready"] is True
    assert payload["stack_engine_contract"]["adoption_recommendation"] == "stack_engine_default_ready"
    assert checks["runtime_repeat_ratio_within_bound"] is True
    assert checks["default_route_acceptance_present"] is True
    assert checks["default_route_acceptance_passed"] is True
    assert checks["default_route_acceptance_route_contract_passed"] is True
    assert checks["default_route_acceptance_route_check_count"] is True
    assert checks["quality_metrics_compare_handoff_passed"] is True
    assert payload["quality_metrics_compare"]["present"] is True
    assert payload["quality_metrics_compare"]["ready"] is True
    assert payload["quality_metrics_compare"]["phase2_check_passed"] is True
    assert checks["pipeline_pixel_maps_match_dq"] is True
    assert checks["pipeline_resident_result_contract_handoff_passed"] is True
    assert payload["resident_result_contract"]["ready"] is True
    assert payload["resident_result_contract"]["phase2_check_passed"] is True
    assert payload["resident_result_contract"]["failed_count"] == 0
    assert checks["pipeline_rejection_sample_accounting_passed"] is True
    assert checks["pipeline_sample_accounting_closure_passed"] is True
    assert checks["release_decision_direct_runtime_publication_guard_passed"] is True
    assert checks["release_decision_quality_compare_publication_guard_passed"] is True
    assert checks["resident_registration_fastpath_release_handoff_ready"] is True
    assert payload["resident_registration_fastpath_release_handoff"]["ready"] is True
    assert payload["resident_registration_fastpath_release_handoff"][
        "raw_passed_check_count"
    ] == 23
    assert payload["resident_registration_fastpath_release_handoff"][
        "phase2_passed_check_count"
    ] == 23
    assert payload["release_decision_direct_runtime_publication_guard"]["ready"] is True
    assert payload["release_decision_direct_runtime_publication_guard"][
        "raw_matrix_acceptance_source"
    ] == "explicit_resident_artifacts_json"
    assert payload["release_decision_direct_runtime_publication_guard"][
        "raw_matrix_pipeline_calibration_source"
    ] == "resident_artifacts_json_fallback"
    assert payload["release_decision_direct_runtime_publication_guard"][
        "raw_matrix_pipeline_resident_lights"
    ] == 200
    assert payload["release_decision_quality_compare_publication_guard"][
        "ready"
    ] is True
    assert payload["release_decision_quality_compare_publication_guard"][
        "quality_compare_present"
    ] is True
    assert payload["release_decision_quality_compare_publication_guard"][
        "raw_matrix_status"
    ] == "passed"
    assert payload["release_decision_quality_compare_publication_guard"][
        "phase2_matrix_status"
    ] == "passed"
    assert checks["acceptance_integration_engine_policy_handoff_passed"] is True
    assert checks["pipeline_integration_engine_policy_default_passed"] is True
    assert payload["integration_engine_policy"]["ready"] is True
    assert payload["integration_engine_policy"]["pipeline_non_resident_count"] == 0
    assert checks["acceptance_stack_engine_runtime_default_handoff_passed"] is True
    assert checks["pipeline_stack_engine_runtime_default_handoff_passed"] is True
    assert payload["stack_engine_runtime_default"]["ready"] is True
    assert payload["stack_engine_runtime_default"]["acceptance_legacy_master_count"] == 0
    assert payload["stack_engine_runtime_default"]["pipeline_failed_output_count"] == 0
    assert checks["phase2_stack_engine_default_contract_ready"] is True
    assert checks["resident_winsorized_sweep_audit_passed"] is True
    assert checks["resident_winsorized_sweep_required_frame_passed"] is True
    assert checks["resident_winsorized_sweep_check_count"] is True
    assert checks["stack_engine_publication_audit_passed"] is True
    assert checks["stack_engine_publication_policy_chain_passed"] is True
    assert checks["stack_engine_publication_resident_winsorized_chain_passed"] is True
    assert payload["stack_engine_publication_audit"]["ready"] is True
    assert (
        payload["stack_engine_publication_audit"]["publish_preflight_policy_ready"]
        is True
    )
    release_winsorized = payload["release_decision"][
        "resident_winsorized_semantics"
    ]
    assert release_winsorized["status"] == "passed"
    assert release_winsorized["required_count"] == 1
    assert release_winsorized["legacy_completion_count"] == 1
    assert release_winsorized["descriptor_sources"] == [
        "resident_artifacts.integration_rejection"
    ]
    assert payload["resident_winsorized_sweep_audit"]["required_frame_count"] == 200
    assert checks["windows_package_try_list_has_cpu_fallback"] is True


def test_default_promotion_manifest_allows_missing_release_quality_guard(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, include_quality_publication_guard=False)
    _write_phase2_status(phase2, decision)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    guard = payload["release_decision_quality_compare_publication_guard"]
    assert payload["passed"] is True
    assert checks["release_decision_quality_compare_publication_guard_passed"][
        "passed"
    ] is True
    assert guard["present"] is False
    assert guard["ready"] is True
    assert guard["compatible_missing"] is True


def test_default_promotion_manifest_blocks_failed_release_quality_guard(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, quality_publication_guard_ready=False)
    _write_phase2_status(phase2, decision)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    guard = payload["release_decision_quality_compare_publication_guard"]
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "release_decision_quality_compare_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert checks["release_decision_quality_compare_publication_guard_passed"][
        "passed"
    ] is False
    assert guard["ready"] is False
    assert guard["decision_check_passed"] is False
    assert guard["raw_matrix_status"] == "blocked"
    assert guard["raw_matrix_failed_check_count"] == 1


def test_default_promotion_manifest_blocks_phase2_release_quality_mismatch(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(
        decision,
        quality_publication_guard_ready=True,
        phase2_quality_publication_guard_ready=False,
    )
    _write_phase2_status(phase2, decision)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        min_runtime_runs=3,
    )

    guard = payload["release_decision_quality_compare_publication_guard"]
    assert payload["passed"] is False
    assert "release_decision_quality_compare_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert guard["ready"] is False
    assert guard["raw_matrix_status"] == "passed"
    assert guard["phase2_matrix_status"] == "blocked"
    assert guard["phase2_matrix_failed_check_count"] == 1


def test_default_promotion_manifest_blocks_failed_resident_fastpath_handoff(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, resident_fastpath_ready=False)
    _write_phase2_status(phase2, decision, resident_fastpath_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    handoff = payload["resident_registration_fastpath_release_handoff"]
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "resident_registration_fastpath_release_handoff_ready" in payload[
        "failed_checks"
    ]
    assert checks["resident_registration_fastpath_release_handoff_ready"][
        "passed"
    ] is False
    assert handoff["raw_ready"] is False
    assert handoff["phase2_ready"] is False
    assert handoff["raw_failed_check_count"] == 1
    assert handoff["phase2_failed_check_count"] == 1


def test_default_promotion_manifest_summarizes_direct_runtime_evidence(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    acceptance = tmp_path / "acceptance.json"
    pipeline = tmp_path / "pipeline_contract.json"
    _write_release_decision(decision)
    decision_payload = read_json(decision)
    decision_payload["inputs"] = {
        "acceptance_audit": str(acceptance),
        "pipeline_contract": str(pipeline),
    }
    write_json(decision, decision_payload)
    _write_phase2_status(phase2, decision)
    phase2_payload = read_json(phase2)
    phase2_payload["pipeline_contract"]["path"] = str(pipeline)
    write_json(phase2, phase2_payload)
    write_json(
        acceptance,
        {
            "schema_version": 1,
            "resident_registration_fastpath": {
                "source": "explicit_resident_artifacts_json",
                "available": True,
                "exists": True,
                "path": "C:/glass_runs/default_resident/resident_artifacts.json",
            },
            "checks": [
                {
                    "name": "contract_resident_registration_fastpath_present",
                    "passed": True,
                    "evidence": {},
                }
            ],
        },
    )
    write_json(
        pipeline,
        {
            "schema_version": 1,
            "artifacts": {
                "calibration": {
                    "exists": True,
                    "generated_for_pipeline_contract": True,
                    "path_exists": False,
                    "source": "resident_artifacts_json_fallback",
                }
            },
            "calibration": {"calibrated_light_count": 200},
        },
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
        min_runtime_runs=3,
    )

    evidence = payload["runtime_default_direct_evidence"]
    assert evidence["ready"] is True
    assert evidence["acceptance_direct_fastpath"] is True
    assert evidence["acceptance_fastpath_source"] == "explicit_resident_artifacts_json"
    assert evidence["acceptance_fastpath_check_count"] == 1
    assert evidence["pipeline_direct_resident_calibration"] is True
    assert evidence["pipeline_calibration_artifact_source"] == "resident_artifacts_json_fallback"
    assert evidence["pipeline_resident_calibrated_light_count"] == 200


def test_default_promotion_manifest_blocks_unready_release_decision(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, ready=False)
    _write_phase2_status(phase2, decision, ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "release_decision_default_change_ready" in payload["failed_checks"]
    assert "phase2_status_green" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_missing_release_direct_publication_guard(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, include_direct_publication_guard=False)
    _write_phase2_status(phase2, decision)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    guard = payload["release_decision_direct_runtime_publication_guard"]
    assert payload["passed"] is False
    assert "release_decision_direct_runtime_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert checks["release_decision_direct_runtime_publication_guard_passed"][
        "passed"
    ] is False
    assert guard["present"] is False
    assert guard["decision_check_passed"] is None


def test_default_promotion_manifest_blocks_stale_release_direct_publication_source(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(
        decision,
        direct_acceptance_source="glass_run_discovery",
    )
    _write_phase2_status(phase2, decision)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    guard = payload["release_decision_direct_runtime_publication_guard"]
    assert payload["passed"] is False
    assert "release_decision_direct_runtime_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert guard["source_ready"] is False
    assert guard["raw_matrix_acceptance_source"] == "glass_run_discovery"


def test_default_promotion_manifest_blocks_short_release_direct_publication_count(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision, direct_resident_lights=199)
    _write_phase2_status(phase2, decision)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    guard = payload["release_decision_direct_runtime_publication_guard"]
    assert payload["passed"] is False
    assert "release_decision_direct_runtime_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert guard["count_ready"] is False
    assert guard["raw_matrix_pipeline_resident_lights"] == 199


def test_default_promotion_manifest_blocks_missing_default_route_evidence(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, include_default_route=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "default_route_acceptance_present" in payload["failed_checks"]
    assert "default_route_acceptance_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_contract_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_check_count" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_failed_default_route_evidence(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, default_route_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "default_route_acceptance_present" not in payload["failed_checks"]
    assert "default_route_acceptance_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_contract_passed" in payload["failed_checks"]
    assert "default_route_acceptance_route_check_count" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_failed_quality_metrics_compare(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        quality_metrics_compare_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "quality_metrics_compare_handoff_passed" in payload["failed_checks"]
    assert checks["quality_metrics_compare_handoff_passed"]["evidence"] == {
        "present": True,
        "ready": False,
        "status": "failed",
        "passed": False,
        "phase2_check_passed": False,
        "check_count": 4,
        "failed_check_count": 1,
        "failed_checks": ["bad_median_ratio_within_limit"],
        "baseline_metric_count": 7,
        "candidate_metric_count": 7,
        "metric_row_count": 7,
        "threshold_failure_count": 1,
        "threshold_failures": [{"metric": "fwhm_px", "bad_median_ratio": 1.4}],
        "path": "runs/checkpoints/quality_metrics_compare.json",
    }


def test_default_promotion_manifest_allows_missing_quality_metrics_compare(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        include_quality_metrics_compare=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is True
    assert "quality_metrics_compare_handoff_passed" not in payload["failed_checks"]
    assert payload["quality_metrics_compare"] == {
        "present": False,
        "ready": True,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "check_count": None,
        "failed_check_count": None,
        "failed_checks": [],
        "baseline_metric_count": None,
        "candidate_metric_count": None,
        "metric_row_count": None,
        "threshold_failure_count": None,
        "threshold_failures": [],
        "path": None,
    }
    assert checks["quality_metrics_compare_handoff_passed"]["passed"] is True


def test_default_promotion_manifest_blocks_rejection_sample_accounting_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, rejection_sample_accounting_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert "pipeline_rejection_sample_accounting_passed" in payload["failed_checks"]


def test_default_promotion_manifest_blocks_resident_result_contract_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, resident_result_contract_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    resident = payload["resident_result_contract"]
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert (
        "pipeline_stack_and_resident_result_contracts_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_resident_result_contract_handoff_passed"
        in payload["failed_checks"]
    )
    assert checks["pipeline_resident_result_contract_handoff_passed"][
        "passed"
    ] is False
    assert resident["ready"] is False
    assert resident["status"] == "failed"
    assert resident["top_level_check"] is False
    assert resident["check_present"] is True
    assert resident["check_passed"] is False
    assert resident["phase2_check_passed"] is False
    assert resident["required_count"] == 1
    assert resident["failed_count"] == 1
    assert resident["failed_check_count"] == 1
    assert resident["failed_checks"] == ["source_terms_present"]
    assert resident["failed_items"][0]["item"] == "H"


def test_default_promotion_manifest_blocks_sample_accounting_closure_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, sample_accounting_closure_ready=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert "pipeline_sample_accounting_closure_passed" in payload["failed_checks"]
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


def test_default_promotion_manifest_blocks_missing_integration_engine_policy(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        include_integration_engine_policy=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert (
        "acceptance_integration_engine_policy_handoff_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_integration_engine_policy_default_passed"
        in payload["failed_checks"]
    )
    assert payload["integration_engine_policy"]["present"] is False
    assert checks["acceptance_integration_engine_policy_handoff_passed"][
        "evidence"
    ] == {
        "status": None,
        "check_present": None,
        "check_passed": None,
        "phase2_check_passed": None,
        "non_resident_count": None,
        "failed_count": None,
        "failed_items": [],
    }
    assert checks["pipeline_integration_engine_policy_default_passed"][
        "evidence"
    ]["check_present"] is None


def test_default_promotion_manifest_blocks_failed_integration_engine_policy(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        acceptance_integration_engine_policy_ready=False,
        pipeline_integration_engine_policy_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert (
        "acceptance_integration_engine_policy_handoff_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_integration_engine_policy_default_passed"
        in payload["failed_checks"]
    )
    assert payload["integration_engine_policy"]["ready"] is False
    assert checks["acceptance_integration_engine_policy_handoff_passed"][
        "evidence"
    ]["non_resident_count"] == 1
    assert checks["pipeline_integration_engine_policy_default_passed"][
        "evidence"
    ]["failed_items"][0]["failures"] == ["cuda_fast_path_not_explicit"]


def test_default_promotion_manifest_blocks_missing_stack_engine_runtime_default(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        include_stack_engine_runtime_default=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert (
        "acceptance_stack_engine_runtime_default_handoff_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_stack_engine_runtime_default_handoff_passed"
        in payload["failed_checks"]
    )
    assert payload["stack_engine_runtime_default"]["present"] is False
    assert checks["acceptance_stack_engine_runtime_default_handoff_passed"][
        "evidence"
    ] == {
        "status": None,
        "check_present": None,
        "check_passed": None,
        "phase2_check_passed": None,
        "master_count": None,
        "legacy_master_count": None,
        "failed_master_count": None,
        "failed_output_count": None,
        "explicit_cuda_fast_path_count": None,
        "failed_masters": [],
        "failed_outputs": [],
    }


def test_default_promotion_manifest_blocks_acceptance_runtime_default_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        acceptance_stack_engine_runtime_default_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert (
        "acceptance_stack_engine_runtime_default_handoff_passed"
        in payload["failed_checks"]
    )
    assert (
        "pipeline_stack_engine_runtime_default_handoff_passed"
        not in payload["failed_checks"]
    )
    assert payload["stack_engine_runtime_default"]["acceptance_legacy_master_count"] == 1
    assert checks["acceptance_stack_engine_runtime_default_handoff_passed"][
        "evidence"
    ]["failed_masters"] == [
        {
            "group_id": "bias_0",
            "engine_family": "legacy",
            "reason": "legacy_master_accumulator",
        }
    ]


def test_default_promotion_manifest_blocks_pipeline_runtime_default_drift(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        pipeline_stack_engine_runtime_default_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "pipeline_contract_passed" in payload["failed_checks"]
    assert (
        "acceptance_stack_engine_runtime_default_handoff_passed"
        not in payload["failed_checks"]
    )
    assert (
        "pipeline_stack_engine_runtime_default_handoff_passed"
        in payload["failed_checks"]
    )
    assert payload["stack_engine_runtime_default"]["pipeline_failed_output_count"] == 1
    assert checks["pipeline_stack_engine_runtime_default_handoff_passed"][
        "evidence"
    ]["failed_outputs"] == [
        {
            "item": "H",
            "engine_family": "legacy",
            "reason": "legacy_or_unknown_engine",
        }
    ]


def test_default_promotion_manifest_blocks_missing_stack_engine_contract(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, include_stack_engine_contract=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["stack_engine_contract"]["present"] is False
    assert "phase2_status_green" not in payload["failed_checks"]
    assert "phase2_stack_engine_default_contract_ready" in payload["failed_checks"]
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"] == {
        "present": False,
        "phase2_check_passed": False,
        "status": None,
        "passed": None,
        "scope": None,
        "expected_integration_engine": None,
        "adoption_recommendation": None,
        "adoption_gap_count": None,
        "default_promotion_ready": None,
        "default_promotion_status": None,
        "default_promotion_blocker_count": None,
        "default_promotion_blockers": [],
    }


def test_default_promotion_manifest_blocks_stack_engine_default_gap(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["stack_engine_contract"]["present"] is True
    assert payload["stack_engine_contract"]["ready"] is False
    assert "phase2_status_green" in payload["failed_checks"]
    assert "phase2_stack_engine_default_contract_ready" in payload["failed_checks"]
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"][
        "adoption_gap_count"
    ] == 1
    assert checks["phase2_stack_engine_default_contract_ready"]["evidence"][
        "default_promotion_status"
    ] == "blocked"


def test_default_promotion_manifest_blocks_missing_resident_winsorized_sweep(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision, include_resident_winsorized_sweep=False)

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert "resident_winsorized_sweep_audit_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_required_frame_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_check_count" in payload["failed_checks"]
    assert payload["resident_winsorized_sweep_audit"]["present"] is False
    assert checks["resident_winsorized_sweep_audit_passed"]["evidence"] == {
        "present": False,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_checks": [],
    }


def test_default_promotion_manifest_blocks_failed_resident_winsorized_sweep(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        resident_winsorized_sweep_ready=False,
        resident_winsorized_sweep_required_frame_ready=False,
        resident_winsorized_sweep_check_count=26,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "resident_winsorized_sweep_audit_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_required_frame_passed" in payload["failed_checks"]
    assert "resident_winsorized_sweep_check_count" in payload["failed_checks"]
    assert checks["resident_winsorized_sweep_required_frame_passed"]["evidence"] == {
        "actual_frame_count": 200,
        "required_frame_count": 200,
        "required_frame_count_passed": False,
        "required_frame_master_rms": 2.3e-05,
        "required_frame_master_max_abs": 6.1e-05,
    }


def test_default_promotion_manifest_blocks_missing_publication_audit(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        include_stack_publication_audit=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" not in payload["failed_checks"]
    assert "stack_engine_publication_audit_passed" in payload["failed_checks"]
    assert "stack_engine_publication_policy_chain_passed" in payload["failed_checks"]
    assert (
        "stack_engine_publication_resident_winsorized_chain_passed"
        in payload["failed_checks"]
    )
    assert payload["stack_engine_publication_audit"]["present"] is False
    assert checks["stack_engine_publication_audit_passed"]["evidence"] == {
        "present": False,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_checks": [],
    }


def test_default_promotion_manifest_blocks_failed_publication_policy_chain(
    tmp_path: Path,
) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    _write_release_decision(decision)
    _write_phase2_status(
        phase2,
        decision,
        stack_publication_audit_ready=False,
        stack_publication_policy_ready=False,
    )

    payload = build_default_promotion_manifest(
        release_decision_json=decision,
        phase2_status_json=phase2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert "phase2_status_green" in payload["failed_checks"]
    assert "stack_engine_publication_audit_passed" in payload["failed_checks"]
    assert "stack_engine_publication_policy_chain_passed" in payload["failed_checks"]
    assert (
        "stack_engine_publication_resident_winsorized_chain_passed"
        not in payload["failed_checks"]
    )
    assert payload["stack_engine_publication_audit"]["ready"] is False
    assert checks["stack_engine_publication_policy_chain_passed"]["evidence"][
        "publish_preflight_policy_ready"
    ] is False
    assert checks["stack_engine_publication_policy_chain_passed"]["evidence"][
        "policy_agreement"
    ] is False


def test_default_promotion_manifest_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    decision = tmp_path / "decision.json"
    phase2 = tmp_path / "phase2.json"
    doctor = tmp_path / "doctor.json"
    out = tmp_path / "manifest.json"
    markdown = tmp_path / "manifest.md"
    _write_release_decision(decision)
    _write_phase2_status(phase2, decision)
    _write_doctor(doctor)

    result = main(
        [
            "default-promotion-manifest",
            "--release-decision",
            str(decision),
            "--phase2-status",
            str(phase2),
            "--doctor-json",
            str(doctor),
            "--require-doctor",
            "--min-runtime-runs",
            "3",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-not-ready",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["passed"] is True
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "Default Promotion Manifest" in markdown_text
    assert "Default Route Evidence" in markdown_text
    assert "Rejection sample accounting: `passed`" in markdown_text
    assert "Sample accounting closure: `passed`" in markdown_text
    assert "Quality metrics compare: present=`True` ready=`True`" in markdown_text
    assert (
        "Release resident winsorized semantics: `passed` "
        "required=`1` legacy-completions=`1`"
    ) in markdown_text
    assert "Acceptance integration engine policy: `passed`" in markdown_text
    assert "Pipeline integration engine policy: `passed`" in markdown_text
    assert "Integration engine policy ready: `True`" in markdown_text
    assert "Acceptance StackEngine runtime default: `passed`" in markdown_text
    assert "Pipeline StackEngine runtime default: `passed`" in markdown_text
    assert "StackEngine runtime default ready: `True`" in markdown_text
    assert "StackEngine Default Contract" in markdown_text
    assert "Adoption recommendation: `stack_engine_default_ready`" in markdown_text
    assert "Default promotion: `ready` ready=`True` blockers=`0`" in markdown_text
    assert "Resident Winsorized Sweep" in markdown_text
    assert "Required frame count: `200`" in markdown_text
    assert "StackEngine Publication Audit" in markdown_text
    assert "Release direct publication guard: ready=`True`" in markdown_text
    assert "Release direct publication sources: raw-acceptance=`explicit_resident_artifacts_json`" in markdown_text
    assert "Release quality compare publication guard: ready=`True`" in markdown_text
    assert "Release quality compare sources: raw=`passed` phase2=`passed`" in markdown_text
    assert "Policy chain: raw=`True` phase2=`True` agreement=`True`" in markdown_text
    assert "Resident winsorized chain: raw=`True` phase2=`True` agreement=`True`" in markdown_text
    assert "Route contract passed: `True`" in markdown_text
