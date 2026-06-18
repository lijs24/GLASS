from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.gpu.compatibility import recommend_windows_cuda_packages
from glass.io.json_io import read_json, write_json
from glass.report.windows_release_matrix import build_windows_release_matrix


def _blackwell_doctor(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "cuda": {
                "wrapper_importable": True,
                "native_extension_loaded": True,
                "cuda_available": True,
                "probe_skipped": False,
                "devices": [
                    {
                        "device_id": 0,
                        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                        "compute_capability": "12.0",
                        "memory_total_mib": 97886,
                        "driver_version": "596.21",
                    }
                ],
            },
            "windows_cuda_packages": recommend_windows_cuda_packages(
                [
                    {
                        "device_id": 0,
                        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                        "compute_capability": "12.0",
                        "driver_version": "596.21",
                    }
                ]
            ),
        },
    )


def _cpu_only_doctor(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "product": "GLASS",
            "cuda": {
                "wrapper_importable": False,
                "native_extension_loaded": False,
                "cuda_available": False,
                "probe_skipped": False,
                "devices": [],
            },
            "windows_cuda_packages": recommend_windows_cuda_packages([]),
        },
    )


def _release_decision(
    path: Path,
    *,
    ready: bool = True,
    include_direct_publication_guard: bool = True,
    direct_publication_guard_ready: bool = True,
    direct_acceptance_source: str = "explicit_resident_artifacts_json",
    direct_calibration_source: str = "resident_artifacts_json_fallback",
    direct_resident_lights: int = 200,
    include_quality_publication_guard: bool = True,
    quality_publication_guard_ready: bool = True,
    quality_publication_compare_present: bool = True,
    phase2_quality_publication_guard_ready: bool | None = None,
    include_release_quality_publication_guard: bool = True,
    release_quality_publication_guard_ready: bool = True,
    release_quality_guard_present: bool = True,
    phase2_release_quality_publication_guard_ready: bool | None = None,
) -> None:
    phase2_quality_publication_guard_ready = (
        quality_publication_guard_ready
        if phase2_quality_publication_guard_ready is None
        else phase2_quality_publication_guard_ready
    )
    phase2_release_quality_publication_guard_ready = (
        release_quality_publication_guard_ready
        if phase2_release_quality_publication_guard_ready is None
        else phase2_release_quality_publication_guard_ready
    )
    direct_guard = {
        "ready": direct_publication_guard_ready,
        "checks_passed": direct_publication_guard_ready,
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
            "phase2_present": quality_publication_compare_present,
            "phase2_ready": phase2_quality_publication_guard_ready,
            "phase2_check_passed": phase2_quality_publication_guard_ready,
            "phase2_matrix_status": phase2_quality_status,
            "phase2_matrix_failed_check_count": (
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
    release_quality_raw_status = (
        "passed" if release_quality_publication_guard_ready else "failed"
    )
    release_quality_phase2_status = (
        "passed"
        if release_quality_publication_guard_ready
        else "attention_required"
    )
    phase2_release_quality_raw_status = (
        "passed" if phase2_release_quality_publication_guard_ready else "failed"
    )
    phase2_release_quality_phase2_status = (
        "passed"
        if phase2_release_quality_publication_guard_ready
        else "attention_required"
    )
    release_quality_guard = (
        {
            "present": True,
            "ready": (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            ),
            "status": "passed"
            if release_quality_publication_guard_ready
            else "blocked",
            "passed": (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            ),
            "checks_passed": (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            ),
            "compatible_missing": not release_quality_guard_present,
            "release_quality_guard_present": release_quality_guard_present,
            "raw_present": release_quality_guard_present,
            "raw_ready": release_quality_publication_guard_ready,
            "raw_matrix_raw_status": release_quality_raw_status,
            "raw_matrix_phase2_status": release_quality_phase2_status,
            "raw_matrix_check_passed": release_quality_publication_guard_ready,
            "raw_matrix_layers_ready": release_quality_publication_guard_ready,
            "raw_default_promotion_raw_status": release_quality_raw_status,
            "raw_default_promotion_phase2_status": release_quality_phase2_status,
            "raw_default_promotion_check_passed": (
                release_quality_publication_guard_ready
            ),
            "raw_default_promotion_layers_ready": (
                release_quality_publication_guard_ready
            ),
            "raw_matrix_check": release_quality_publication_guard_ready,
            "raw_matrix_default_check": release_quality_publication_guard_ready,
            "raw_default_promotion_check": release_quality_publication_guard_ready,
            "raw_matrix_default_match_check": (
                release_quality_publication_guard_ready
            ),
            "raw_matrix_manifest_match_check": (
                release_quality_publication_guard_ready
            ),
            "phase2_present": release_quality_guard_present,
            "phase2_ready": phase2_release_quality_publication_guard_ready,
            "phase2_check_passed": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_matrix_raw_status": phase2_release_quality_raw_status,
            "phase2_matrix_phase2_status": phase2_release_quality_phase2_status,
            "phase2_matrix_check_passed": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_matrix_layers_ready": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_default_promotion_raw_status": (
                phase2_release_quality_raw_status
            ),
            "phase2_default_promotion_phase2_status": (
                phase2_release_quality_phase2_status
            ),
            "phase2_default_promotion_check_passed": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_default_promotion_layers_ready": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_matrix_check": phase2_release_quality_publication_guard_ready,
            "phase2_matrix_default_check": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_default_promotion_check": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_matrix_default_match_check": (
                phase2_release_quality_publication_guard_ready
            ),
            "phase2_matrix_manifest_match_check": (
                phase2_release_quality_publication_guard_ready
            ),
            "failed_checks": []
            if (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            )
            else ["stack_engine_publication_release_quality_guard_passed"],
        }
        if include_release_quality_publication_guard
        else {}
    )
    if include_release_quality_publication_guard:
        checks.append(
            {
                "name": "stack_engine_publication_release_quality_guard_passed",
                "passed": (
                    release_quality_publication_guard_ready
                    and phase2_release_quality_publication_guard_ready
                ),
            }
        )
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "release_promotion_decision",
            "status": "default_change_ready" if ready else "release_candidate_ready",
            "release_candidate_ready": True,
            "default_change_ready": ready,
            "recommendation": "promote_default_candidate" if ready else "repeat_benchmark_before_default_change",
            "runtime_repeat": {
                "present": True,
                "run_count": 3,
                "considered_run_count": 3,
                "elapsed_ratio_vs_best": 1.0140343433372492,
                "recommendation": "best_observed:repeat02",
            },
            "stack_engine_publication_direct_runtime_evidence": direct_guard
            if include_direct_publication_guard
            else {},
            "stack_engine_publication_quality_metrics_compare": quality_guard,
            "stack_engine_publication_release_quality_guard": release_quality_guard,
            "checks": checks,
        },
    )


def _acceptance(path: Path) -> None:
    write_json(path, {"schema_version": 1, "status": "passed", "passed": True})


def _default_promotion(
    path: Path,
    *,
    ready: bool = True,
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
    include_integration_engine_policy: bool = True,
    acceptance_integration_engine_policy_ready: bool = True,
    pipeline_integration_engine_policy_ready: bool = True,
    pipeline_integration_engine_policy_check_present: bool = True,
    include_stack_publication_audit: bool = True,
    stack_publication_audit_ready: bool = True,
    stack_publication_policy_ready: bool = True,
    stack_publication_resident_winsorized_ready: bool = True,
    include_stack_engine_runtime_default: bool = True,
    acceptance_stack_engine_runtime_default_ready: bool = True,
    pipeline_stack_engine_runtime_default_ready: bool = True,
    pipeline_stack_engine_runtime_default_check_present: bool = True,
    include_direct_runtime_evidence: bool = True,
    direct_acceptance_fastpath_ready: bool = True,
    direct_acceptance_fastpath_source: str = "explicit_resident_artifacts_json",
    direct_pipeline_calibration_ready: bool = True,
    direct_pipeline_calibration_source: str = "resident_artifacts_json_fallback",
    include_release_direct_publication_guard: bool = True,
    release_direct_publication_guard_ready: bool = True,
    release_direct_publication_acceptance_source: str = "explicit_resident_artifacts_json",
    release_direct_publication_calibration_source: str = "resident_artifacts_json_fallback",
    release_direct_publication_resident_lights: int = 200,
    include_release_quality_publication_guard: bool = True,
    release_quality_publication_guard_ready: bool = True,
    release_quality_publication_compare_present: bool = True,
    phase2_release_quality_publication_guard_ready: bool | None = None,
    include_release_decision_release_quality_publication_guard: bool = True,
    release_decision_release_quality_publication_present: bool = True,
    release_decision_release_quality_publication_guard_ready: bool = True,
    release_decision_release_quality_guard_present: bool = True,
    phase2_release_decision_release_quality_publication_guard_ready: bool | None = None,
    resident_fastpath_release_handoff_ready: bool = True,
    include_quality_metrics_compare: bool = True,
    quality_metrics_compare_ready: bool = True,
) -> None:
    phase2_release_quality_publication_guard_ready = (
        release_quality_publication_guard_ready
        if phase2_release_quality_publication_guard_ready is None
        else phase2_release_quality_publication_guard_ready
    )
    phase2_release_decision_release_quality_publication_guard_ready = (
        release_decision_release_quality_publication_guard_ready
        if phase2_release_decision_release_quality_publication_guard_ready is None
        else phase2_release_decision_release_quality_publication_guard_ready
    )
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
    publication_audit_chain_ready = (
        stack_publication_audit_ready
        and stack_publication_policy_ready
        and stack_publication_resident_winsorized_ready
        if include_stack_publication_audit
        else True
    )
    manifest_ready = (
        ready
        and resident_result_contract_ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and (
            release_direct_publication_guard_ready
            if include_release_direct_publication_guard
            else True
        )
        and (
            release_quality_publication_guard_ready
            and phase2_release_quality_publication_guard_ready
            if include_release_quality_publication_guard
            else True
        )
        and (
            release_decision_release_quality_publication_guard_ready
            and phase2_release_decision_release_quality_publication_guard_ready
            if include_release_decision_release_quality_publication_guard
            else True
        )
        and acceptance_policy_chain_ready
        and pipeline_policy_chain_ready
        and acceptance_runtime_default_chain_ready
        and pipeline_runtime_default_chain_ready
        and resident_fastpath_release_handoff_ready
        and publication_audit_chain_ready
        and (stack_engine_ready if include_stack_engine_contract else True)
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
    stack_recommendation = (
        "stack_engine_default_ready"
        if stack_engine_ready and stack_engine_gap_count == 0
        else "stack_engine_contract_gaps_remain"
    )
    resident_result_contract = {
        "present": True,
        "ready": resident_result_contract_ready,
        "status": "passed" if resident_result_contract_ready else "failed",
        "top_level_check": resident_result_contract_ready,
        "check_present": True,
        "check_passed": resident_result_contract_ready,
        "phase2_check_passed": resident_result_contract_ready,
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
            }
        ],
    }
    payload = {
            "schema_version": 1,
            "artifact_type": "default_promotion_manifest",
            "status": "default_promotion_ready" if manifest_ready else "blocked",
            "passed": manifest_ready,
            "default_change_ready": manifest_ready,
            "recommendation": "promote_resident_cuda_default"
            if manifest_ready
            else "fix_default_blockers",
            "default_candidate": {
                "memory_mode": "resident",
                "fallback_memory_mode": "tile",
                "resident_runtime_preset": "throughput-v1",
                "integration_engine": "cuda_resident_stack",
            },
            "default_route_acceptance": {
                "present": True,
                "status": "passed" if ready else "failed",
                "passed": ready,
                "route_contract_passed": ready,
                "route_check_count": 4 if ready else 2,
                "speedup_vs_reference": 28.75,
            },
            "pipeline_contract": {
                "status": "passed" if manifest_ready else "failed",
                "passed": manifest_ready,
                "integration_resident_result_contract": resident_result_contract_ready,
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
            },
            "resident_result_contract": resident_result_contract,
        }
    if include_quality_metrics_compare:
        payload["quality_metrics_compare"] = {
            "present": True,
            "ready": quality_metrics_compare_ready,
            "status": "passed" if quality_metrics_compare_ready else "failed",
            "passed": quality_metrics_compare_ready,
            "phase2_check_passed": quality_metrics_compare_ready,
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
    if include_integration_engine_policy:
        acceptance_policy_status = (
            "passed" if acceptance_integration_engine_policy_ready else "failed"
        )
        pipeline_policy_status = (
            "passed" if pipeline_integration_engine_policy_ready else "failed"
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
        payload["integration_engine_policy"] = {
            "present": True,
            "ready": acceptance_policy_chain_ready and pipeline_policy_chain_ready,
            "acceptance_status": acceptance_policy_status,
            "acceptance_check_present": True,
            "acceptance_check_passed": acceptance_integration_engine_policy_ready,
            "acceptance_phase2_check_passed": acceptance_policy_chain_ready,
            "acceptance_non_resident_count": 0
            if acceptance_integration_engine_policy_ready
            else 1,
            "acceptance_failed_count": 0
            if acceptance_integration_engine_policy_ready
            else 1,
            "acceptance_failed_items": acceptance_failed_items,
            "pipeline_status": pipeline_policy_status,
            "pipeline_check_present": pipeline_integration_engine_policy_check_present,
            "pipeline_check_passed": pipeline_integration_engine_policy_ready
            if pipeline_integration_engine_policy_check_present
            else None,
            "pipeline_phase2_check_passed": pipeline_policy_chain_ready,
            "pipeline_default_engine_policy": pipeline_integration_engine_policy_ready
            if pipeline_integration_engine_policy_check_present
            else None,
            "pipeline_non_resident_count": 0
            if pipeline_integration_engine_policy_ready
            else 1,
            "pipeline_failed_count": 0
            if pipeline_integration_engine_policy_ready
            else 1,
            "pipeline_failed_items": pipeline_failed_items,
        }
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
        payload["stack_engine_runtime_default"] = {
            "present": True,
            "ready": (
                acceptance_runtime_default_chain_ready
                and pipeline_runtime_default_chain_ready
            ),
            "acceptance_status": acceptance_runtime_status,
            "acceptance_check_present": True,
            "acceptance_check_passed": acceptance_stack_engine_runtime_default_ready,
            "acceptance_phase2_check_passed": acceptance_runtime_default_chain_ready,
            "acceptance_master_count": 3,
            "acceptance_legacy_master_count": 0
            if acceptance_stack_engine_runtime_default_ready
            else 1,
            "acceptance_failed_master_count": 0
            if acceptance_stack_engine_runtime_default_ready
            else 1,
            "acceptance_failed_output_count": 0,
            "acceptance_explicit_cuda_fast_path_count": 1,
            "acceptance_failed_masters": acceptance_failed_masters,
            "acceptance_failed_outputs": [],
            "pipeline_status": pipeline_runtime_status,
            "pipeline_check_present": pipeline_stack_engine_runtime_default_check_present,
            "pipeline_check_passed": pipeline_stack_engine_runtime_default_ready
            if pipeline_stack_engine_runtime_default_check_present
            else None,
            "pipeline_phase2_check_passed": pipeline_runtime_default_chain_ready,
            "pipeline_master_count": 3,
            "pipeline_legacy_master_count": 0,
            "pipeline_failed_master_count": 0,
            "pipeline_failed_output_count": 0
            if pipeline_stack_engine_runtime_default_ready
            else 1,
            "pipeline_explicit_cuda_fast_path_count": 1,
            "pipeline_failed_masters": [],
            "pipeline_failed_outputs": pipeline_failed_outputs,
        }
    if include_stack_engine_contract:
        payload["stack_engine_contract"] = {
            "present": True,
            "ready": stack_engine_ready,
            "phase2_check_passed": stack_engine_ready,
            "status": "passed",
            "passed": True,
            "scope": "all",
            "adoption_recommendation": stack_recommendation,
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
    if include_resident_winsorized_sweep:
        payload["resident_winsorized_sweep_audit"] = {
            "present": True,
            "path": "runs/checkpoints/s2_gate_269_resident_winsorized_sweep_audit.json",
            "status": "passed" if resident_winsorized_sweep_ready else "failed",
            "passed": resident_winsorized_sweep_ready,
            "phase2_check_passed": resident_winsorized_sweep_ready,
            "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
            "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
            "check_count": resident_winsorized_sweep_check_count,
            "failed_check_count": 0 if resident_winsorized_sweep_ready else 1,
            "failed_checks": []
            if resident_winsorized_sweep_ready
            else ["frame_200_hardened_master_rms_within_contract"],
            "frame_counts": [8, 32, 128, 200],
            "run_count": 4,
            "required_frame_count": 200,
            "required_frame_count_passed": resident_winsorized_sweep_required_frame_ready,
            "required_frame_master_rms": 2.3e-5,
            "required_frame_master_max_abs": 6.1e-5,
            "required_frame_cuda_hardened_s": 0.0012,
        }
    if include_stack_publication_audit:
        failed_checks = []
        if not stack_publication_audit_ready:
            failed_checks.append("stack_engine_publication_audit_passed")
        if not stack_publication_policy_ready:
            failed_checks.append("stack_engine_publication_audit_policy_chain_passed")
        if not stack_publication_resident_winsorized_ready:
            failed_checks.append(
                "stack_engine_publication_audit_resident_winsorized_chain_passed"
            )
        publication_ready = (
            stack_publication_audit_ready
            and stack_publication_policy_ready
            and stack_publication_resident_winsorized_ready
        )
        payload["stack_engine_publication_audit"] = {
            "present": True,
            "ready": publication_ready,
            "path": "runs/checkpoints/s2_gate_286_stack_engine_publication_audit.json",
            "status": "passed" if publication_ready else "failed",
            "passed": publication_ready,
            "recommendation": "publish_stack_engine_default"
            if publication_ready
            else "fix_stack_engine_publication_blockers",
            "check_count": 18,
            "failed_check_count": len(failed_checks),
            "failed_checks": failed_checks,
            "phase2_audit_check_passed": stack_publication_audit_ready,
            "policy_chain_phase2_check_passed": stack_publication_policy_ready,
            "resident_winsorized_chain_phase2_check_passed": (
                stack_publication_resident_winsorized_ready
            ),
            "publish_preflight_policy_ready": stack_publication_policy_ready,
            "phase2_policy_ready": stack_publication_policy_ready,
            "policy_agreement": stack_publication_policy_ready,
            "publish_preflight_resident_winsorized_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "phase2_resident_winsorized_ready": (
                stack_publication_resident_winsorized_ready
            ),
            "resident_winsorized_agreement": (
                stack_publication_resident_winsorized_ready
            ),
            "publish_preflight_policy_layer": {
                "ready": stack_publication_policy_ready,
                "status": "passed" if stack_publication_policy_ready else "failed",
            },
            "phase2_policy_layer": {
                "ready": stack_publication_policy_ready,
                "status": "passed" if stack_publication_policy_ready else "failed",
            },
            "publish_preflight_resident_winsorized_layer": {
                "ready": stack_publication_resident_winsorized_ready,
                "status": "passed"
                if stack_publication_resident_winsorized_ready
                else "failed",
            },
            "phase2_resident_winsorized_layer": {
                "ready": stack_publication_resident_winsorized_ready,
                "status": "passed"
                if stack_publication_resident_winsorized_ready
                else "failed",
            },
        }
    if include_direct_runtime_evidence:
        payload["runtime_default_direct_evidence"] = {
            "present": True,
            "ready": direct_acceptance_fastpath_ready
            and direct_pipeline_calibration_ready,
            "decision_inputs_present": True,
            "acceptance_audit_path": "runs/checkpoints/s2_gate_305_acceptance_direct_fastpath_runtime_default.json",
            "acceptance_audit_exists": True,
            "acceptance_audit_read_error": None,
            "acceptance_fastpath_source": direct_acceptance_fastpath_source,
            "acceptance_fastpath_artifact_path": "C:/glass_runs/default_resident/resident_artifacts.json",
            "acceptance_fastpath_available": direct_acceptance_fastpath_ready,
            "acceptance_fastpath_exists": direct_acceptance_fastpath_ready,
            "acceptance_fastpath_check_count": 24,
            "acceptance_fastpath_failed_check_count": 0
            if direct_acceptance_fastpath_ready
            else 1,
            "acceptance_fastpath_failed_checks": []
            if direct_acceptance_fastpath_ready
            else ["contract_resident_registration_fastpath_present"],
            "acceptance_direct_fastpath": direct_acceptance_fastpath_ready,
            "pipeline_contract_path": "runs/checkpoints/s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json",
            "pipeline_contract_exists": True,
            "pipeline_contract_read_error": None,
            "pipeline_calibration_artifact_source": direct_pipeline_calibration_source,
            "pipeline_calibration_artifact_exists": direct_pipeline_calibration_ready,
            "pipeline_calibration_artifact_generated_for_contract": (
                direct_pipeline_calibration_ready
            ),
            "pipeline_calibration_artifact_path_exists": False,
            "pipeline_calibration_artifact_path": "C:/glass_runs/default_resident/calibration_artifacts.json",
            "pipeline_resident_native_calibration_artifact": (
                direct_pipeline_calibration_ready
            ),
            "pipeline_resident_calibrated_light_count": 200
            if direct_pipeline_calibration_ready
            else 0,
            "pipeline_direct_resident_calibration": direct_pipeline_calibration_ready,
        }
    if include_release_direct_publication_guard:
        payload["release_decision_direct_runtime_publication_guard"] = {
            "present": True,
            "ready": release_direct_publication_guard_ready,
            "decision_check_passed": release_direct_publication_guard_ready,
            "source_ready": release_direct_publication_guard_ready,
            "count_ready": release_direct_publication_guard_ready,
            "leaf_checks_ready": release_direct_publication_guard_ready,
            "raw_matrix_acceptance_source": (
                release_direct_publication_acceptance_source
            ),
            "raw_matrix_pipeline_calibration_source": (
                release_direct_publication_calibration_source
            ),
            "raw_matrix_pipeline_resident_lights": (
                release_direct_publication_resident_lights
            ),
        }
    if include_release_quality_publication_guard:
        release_quality_status = (
            "passed" if release_quality_publication_guard_ready else "blocked"
        )
        phase2_release_quality_status = (
            "passed"
            if phase2_release_quality_publication_guard_ready
            else "blocked"
        )
        payload["release_decision_quality_compare_publication_guard"] = {
            "present": True,
            "ready": (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            ),
            "decision_check_passed": (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            ),
            "quality_compare_present": release_quality_publication_compare_present,
            "compatible_missing": not release_quality_publication_compare_present,
            "layers_ready": (
                release_quality_publication_guard_ready
                and phase2_release_quality_publication_guard_ready
            ),
            "raw_matrix_status": release_quality_status,
            "raw_matrix_failed_check_count": (
                0 if release_quality_publication_guard_ready else 1
            ),
            "phase2_matrix_status": phase2_release_quality_status,
            "phase2_matrix_failed_check_count": (
                0 if phase2_release_quality_publication_guard_ready else 1
            ),
        }
    if include_release_decision_release_quality_publication_guard:
        release_quality_raw_status = (
            "passed"
            if release_decision_release_quality_publication_guard_ready
            else "failed"
        )
        release_quality_phase2_status = (
            "passed"
            if release_decision_release_quality_publication_guard_ready
            else "attention_required"
        )
        phase2_release_quality_raw_status = (
            "passed"
            if phase2_release_decision_release_quality_publication_guard_ready
            else "failed"
        )
        phase2_release_quality_phase2_status = (
            "passed"
            if phase2_release_decision_release_quality_publication_guard_ready
            else "attention_required"
        )
        payload["release_decision_release_quality_publication_guard"] = {
            "present": release_decision_release_quality_publication_present,
            "ready": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "decision_check_passed": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "status": "passed"
            if release_decision_release_quality_publication_guard_ready
            else "blocked",
            "passed": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "checks_passed": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "compatible_missing": (
                not release_decision_release_quality_publication_present
                or not release_decision_release_quality_guard_present
            ),
            "release_quality_guard_present": (
                release_decision_release_quality_guard_present
            ),
            "decision_check_ready": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "checks_ready": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "layers_ready": (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            ),
            "raw_present": release_decision_release_quality_guard_present,
            "raw_ready": release_decision_release_quality_publication_guard_ready,
            "raw_matrix_raw_status": release_quality_raw_status,
            "raw_matrix_phase2_status": release_quality_phase2_status,
            "raw_matrix_check_passed": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_matrix_layers_ready": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_default_promotion_raw_status": release_quality_raw_status,
            "raw_default_promotion_phase2_status": release_quality_phase2_status,
            "raw_default_promotion_check_passed": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_default_promotion_layers_ready": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_matrix_check": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_matrix_default_check": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_default_promotion_check": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_matrix_default_match_check": (
                release_decision_release_quality_publication_guard_ready
            ),
            "raw_matrix_manifest_match_check": (
                release_decision_release_quality_publication_guard_ready
            ),
            "phase2_present": release_decision_release_quality_guard_present,
            "phase2_ready": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_check_passed": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_matrix_raw_status": phase2_release_quality_raw_status,
            "phase2_matrix_phase2_status": phase2_release_quality_phase2_status,
            "phase2_matrix_check_passed": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_matrix_layers_ready": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_default_promotion_raw_status": (
                phase2_release_quality_raw_status
            ),
            "phase2_default_promotion_phase2_status": (
                phase2_release_quality_phase2_status
            ),
            "phase2_default_promotion_check_passed": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_default_promotion_layers_ready": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_matrix_check": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_matrix_default_check": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_default_promotion_check": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_matrix_default_match_check": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "phase2_matrix_manifest_match_check": (
                phase2_release_decision_release_quality_publication_guard_ready
            ),
            "failed_checks": []
            if (
                release_decision_release_quality_publication_guard_ready
                and phase2_release_decision_release_quality_publication_guard_ready
            )
            else ["stack_engine_publication_release_quality_guard_passed"],
        }
    fastpath_failed_checks = (
        []
        if resident_fastpath_release_handoff_ready
        else ["contract_resident_registration_fastpath_descriptor_batch_mode"]
    )
    payload["resident_registration_fastpath_release_handoff"] = {
        "present": True,
        "ready": resident_fastpath_release_handoff_ready,
        "raw_ready": resident_fastpath_release_handoff_ready,
        "phase2_ready": resident_fastpath_release_handoff_ready,
        "agreement": resident_fastpath_release_handoff_ready,
        "decision_check_passed": resident_fastpath_release_handoff_ready,
        "phase2_check_passed": resident_fastpath_release_handoff_ready,
        "raw_status": "passed"
        if resident_fastpath_release_handoff_ready
        else "failed",
        "phase2_status": "passed"
        if resident_fastpath_release_handoff_ready
        else "failed",
        "raw_required": True,
        "phase2_required": True,
        "raw_source": "explicit_resident_artifacts_json",
        "phase2_source": "explicit_resident_artifacts_json",
        "raw_path": "resident_artifacts.json",
        "phase2_path": "resident_artifacts.json",
        "raw_mode": "similarity_cuda_triangle",
        "phase2_mode": "similarity_cuda_triangle",
        "raw_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
        "phase2_descriptor_fit_batch_mode": "native_batch_shared_reference_device",
        "raw_pixel_refine_batch_mode": "native_batch_one_seed_per_frame",
        "phase2_pixel_refine_batch_mode": "native_batch_one_seed_per_frame",
        "raw_triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
        "phase2_triangle_warp_batch_mode": "native_matrix_lanczos3_frames",
        "raw_triangle_warp_batch_frame_count": 3,
        "phase2_triangle_warp_batch_frame_count": 3,
        "raw_warp_copy_mode": "default_stream_async_device_to_device",
        "phase2_warp_copy_mode": "default_stream_async_device_to_device",
        "raw_passed_check_count": 23
        if resident_fastpath_release_handoff_ready
        else 22,
        "phase2_passed_check_count": 23
        if resident_fastpath_release_handoff_ready
        else 22,
        "raw_failed_check_count": 0
        if resident_fastpath_release_handoff_ready
        else 1,
        "phase2_failed_check_count": 0
        if resident_fastpath_release_handoff_ready
        else 1,
        "raw_failed_checks": fastpath_failed_checks,
        "phase2_failed_checks": fastpath_failed_checks,
    }
    write_json(path, payload)


def test_windows_release_matrix_passes_blackwell_default(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    acceptance = tmp_path / "acceptance.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _acceptance(acceptance)
    _default_promotion(default_promotion)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        acceptance_audit_json=acceptance,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "release_matrix_ready"
    assert payload["current_machine"]["primary_package"] == "cuda13"
    assert payload["default_promotion_manifest"]["status"] == "default_promotion_ready"
    assert payload["default_runtime"]["resident_runtime_preset"] == "throughput-v1"
    assert checks["default_promotion_manifest_present"] is True
    assert checks["default_promotion_manifest_ready"] is True
    assert checks["default_promotion_default_route_passed"] is True
    assert checks["default_promotion_quality_metrics_compare_handoff_passed"] is True
    assert payload["default_promotion_manifest"]["quality_metrics_compare_present"] is True
    assert payload["default_promotion_manifest"]["quality_metrics_compare_ready"] is True
    assert checks["default_promotion_rejection_sample_accounting_passed"] is True
    assert checks["default_promotion_sample_accounting_closure_passed"] is True
    assert checks["default_promotion_resident_result_contract_handoff_passed"] is True
    assert payload["default_promotion_manifest"]["resident_result_contract_ready"] is True
    assert (
        payload["default_promotion_manifest"][
            "resident_result_contract_phase2_check_passed"
        ]
        is True
    )
    assert payload["default_promotion_manifest"]["resident_result_contract_failed_count"] == 0
    assert checks["default_promotion_acceptance_integration_engine_policy_passed"] is True
    assert checks["default_promotion_pipeline_integration_engine_policy_passed"] is True
    assert payload["default_promotion_manifest"]["integration_engine_policy_ready"] is True
    assert (
        checks["default_promotion_acceptance_stack_engine_runtime_default_passed"]
        is True
    )
    assert (
        checks["default_promotion_pipeline_stack_engine_runtime_default_passed"]
        is True
    )
    assert payload["default_promotion_manifest"]["stack_engine_runtime_default_ready"] is True
    assert (
        payload["default_promotion_manifest"][
            "acceptance_stack_engine_runtime_default_legacy_master_count"
        ]
        == 0
    )
    assert (
        payload["default_promotion_manifest"][
            "pipeline_stack_engine_runtime_default_failed_output_count"
        ]
        == 0
    )
    assert (
        payload["default_promotion_manifest"][
            "pipeline_integration_engine_policy_non_resident_count"
        ]
        == 0
    )
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"] is True
    assert checks["default_promotion_direct_pipeline_calibration_evidence"] is True
    assert checks["release_decision_direct_runtime_publication_guard_passed"] is True
    assert checks["release_decision_quality_compare_publication_guard_passed"] is True
    assert checks["release_decision_release_quality_publication_guard_passed"] is True
    assert (
        checks[
            "default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "default_promotion_release_decision_quality_compare_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "default_promotion_release_decision_release_quality_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_resident_fastpath_release_handoff_ready"]
        is True
    )
    assert payload["release_decision_direct_runtime_publication_guard"]["ready"] is True
    assert payload["release_decision_quality_compare_publication_guard"][
        "ready"
    ] is True
    assert payload["release_decision_quality_compare_publication_guard"][
        "raw_matrix_status"
    ] == "passed"
    assert payload["release_decision_release_quality_publication_guard"][
        "ready"
    ] is True
    assert payload["release_decision_release_quality_publication_guard"][
        "release_quality_guard_present"
    ] is True
    assert payload["release_decision_release_quality_publication_guard"][
        "raw_matrix_raw_status"
    ] == "passed"
    assert payload["default_promotion_manifest"][
        "runtime_default_direct_acceptance_fastpath_source"
    ] == "explicit_resident_artifacts_json"
    assert payload["default_promotion_manifest"][
        "runtime_default_direct_pipeline_calibration_source"
    ] == "resident_artifacts_json_fallback"
    assert payload["default_promotion_manifest"][
        "release_decision_direct_runtime_publication_guard_ready"
    ] is True
    assert payload["default_promotion_manifest"][
        "release_decision_quality_compare_publication_guard_ready"
    ] is True
    assert payload["default_promotion_manifest"][
        "release_decision_quality_compare_publication_guard_raw_status"
    ] == "passed"
    assert payload["default_promotion_manifest"][
        "release_decision_release_quality_publication_guard_ready"
    ] is True
    assert payload["default_promotion_manifest"][
        "release_decision_release_quality_publication_guard_release_quality_present"
    ] is True
    assert payload["default_promotion_manifest"][
        "release_decision_release_quality_publication_guard_raw_matrix_raw_status"
    ] == "passed"
    assert payload["default_promotion_manifest"][
        "resident_registration_fastpath_release_handoff_ready"
    ] is True
    assert payload["default_promotion_manifest"][
        "resident_registration_fastpath_release_handoff_raw_passed_check_count"
    ] == 23
    assert checks["default_promotion_stack_engine_contract_ready"] is True
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"] is True
    assert checks["default_promotion_resident_winsorized_required_frame_passed"] is True
    assert checks["default_promotion_resident_winsorized_sweep_check_count"] is True
    assert checks["default_promotion_stack_engine_publication_audit_passed"] is True
    assert (
        checks["default_promotion_stack_engine_publication_policy_chain_passed"]
        is True
    )
    assert (
        checks[
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
        ]
        is True
    )
    assert payload["default_promotion_manifest"][
        "resident_winsorized_sweep_required_frame_count"
    ] == 200
    assert payload["default_promotion_manifest"][
        "stack_engine_publication_audit_ready"
    ] is True
    assert checks["required_cuda_package_compatible:cuda13"] is True
    assert checks["required_cuda_package_compatible:cuda12"] is True
    assert checks["required_cuda_package_compatible:cuda11"] is True
    assert [row["label"] for row in payload["packages"]] == ["cuda11", "cuda12", "cuda13", "cpu"]


def test_windows_release_matrix_allows_missing_quality_publication_guards(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision, include_quality_publication_guard=False)
    _default_promotion(
        default_promotion,
        include_release_quality_publication_guard=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is True
    assert checks["release_decision_quality_compare_publication_guard_passed"][
        "passed"
    ] is True
    assert checks[
        "default_promotion_release_decision_quality_compare_publication_guard_passed"
    ]["passed"] is True
    assert payload["release_decision_quality_compare_publication_guard"][
        "present"
    ] is False
    assert payload["release_decision_quality_compare_publication_guard"][
        "ready"
    ] is True
    assert payload["default_promotion_manifest"][
        "release_decision_quality_compare_publication_guard_present"
    ] is None


def test_windows_release_matrix_allows_missing_release_quality_publication_guards(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision, include_release_quality_publication_guard=False)
    _default_promotion(
        default_promotion,
        release_decision_release_quality_publication_present=False,
        release_decision_release_quality_guard_present=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is True
    assert checks["release_decision_release_quality_publication_guard_passed"][
        "passed"
    ] is True
    assert checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["passed"] is True
    assert payload["release_decision_release_quality_publication_guard"][
        "present"
    ] is False
    assert payload["release_decision_release_quality_publication_guard"][
        "ready"
    ] is True
    assert payload["default_promotion_manifest"][
        "release_decision_release_quality_publication_guard_present"
    ] is False
    assert payload["default_promotion_manifest"][
        "release_decision_release_quality_publication_guard_compatible_missing"
    ] is True


def test_windows_release_matrix_blocks_failed_release_quality_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision, quality_publication_guard_ready=False)
    _default_promotion(default_promotion)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    guard = payload["release_decision_quality_compare_publication_guard"]
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["release_decision_quality_compare_publication_guard_passed"][
        "passed"
    ] is False
    assert guard["ready"] is False
    assert guard["decision_check_passed"] is False
    assert guard["raw_matrix_status"] == "blocked"
    assert guard["raw_matrix_failed_check_count"] == 1


def test_windows_release_matrix_blocks_failed_release_quality_publication_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision, release_quality_publication_guard_ready=False)
    _default_promotion(default_promotion)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    guard = payload["release_decision_release_quality_publication_guard"]
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["release_decision_release_quality_publication_guard_passed"][
        "passed"
    ] is False
    assert guard["ready"] is False
    assert guard["decision_check_passed"] is False
    assert guard["raw_matrix_raw_status"] == "failed"
    assert guard["failed_checks"] == [
        "stack_engine_publication_release_quality_guard_passed"
    ]


def test_windows_release_matrix_blocks_failed_default_promotion_quality_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        release_quality_publication_guard_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks[
        "default_promotion_release_decision_quality_compare_publication_guard_passed"
    ]["evidence"]
    assert payload["passed"] is False
    assert checks[
        "default_promotion_release_decision_quality_compare_publication_guard_passed"
    ]["passed"] is False
    assert evidence["ready"] is False
    assert evidence["raw_status"] == "blocked"
    assert evidence["raw_failed_count"] == 1


def test_windows_release_matrix_blocks_default_promotion_quality_mismatch(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        release_quality_publication_guard_ready=True,
        phase2_release_quality_publication_guard_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks[
        "default_promotion_release_decision_quality_compare_publication_guard_passed"
    ]["evidence"]
    assert payload["passed"] is False
    assert checks[
        "default_promotion_release_decision_quality_compare_publication_guard_passed"
    ]["passed"] is False
    assert evidence["raw_status"] == "passed"
    assert evidence["phase2_status"] == "blocked"
    assert evidence["phase2_failed_count"] == 1


def test_windows_release_matrix_blocks_missing_default_promotion_release_quality_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        include_release_decision_release_quality_publication_guard=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["evidence"]
    assert payload["passed"] is False
    assert checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["passed"] is False
    assert evidence["present"] is None
    assert evidence["ready"] is None


def test_windows_release_matrix_blocks_failed_default_promotion_release_quality_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        release_decision_release_quality_publication_guard_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["evidence"]
    assert payload["passed"] is False
    assert checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["passed"] is False
    assert evidence["ready"] is False
    assert evidence["raw_matrix_raw_status"] == "failed"
    assert evidence["raw_matrix_check_passed"] is False


def test_windows_release_matrix_blocks_default_promotion_release_quality_mismatch(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        release_decision_release_quality_publication_guard_ready=True,
        phase2_release_decision_release_quality_publication_guard_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["evidence"]
    assert payload["passed"] is False
    assert checks[
        "default_promotion_release_decision_release_quality_publication_guard_passed"
    ]["passed"] is False
    assert evidence["raw_matrix_raw_status"] == "passed"
    assert evidence["phase2_matrix_raw_status"] == "failed"
    assert evidence["phase2_matrix_check_passed"] is False


def test_windows_release_matrix_blocks_failed_resident_fastpath_handoff(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    acceptance = tmp_path / "acceptance.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _acceptance(acceptance)
    _default_promotion(
        default_promotion,
        resident_fastpath_release_handoff_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        acceptance_audit_json=acceptance,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["default_promotion_manifest"]["status"] == "blocked"
    check = checks["default_promotion_resident_fastpath_release_handoff_ready"]
    assert check["passed"] is False
    assert check["evidence"]["raw_ready"] is False
    assert check["evidence"]["phase2_ready"] is False
    assert check["evidence"]["raw_failed_check_count"] == 1
    assert check["evidence"]["phase2_failed_check_count"] == 1


def test_windows_release_matrix_blocks_cpu_only_cuda_release(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    _cpu_only_doctor(doctor)
    _release_decision(decision)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["cuda_available_for_release_machine"] is False
    assert checks["required_cuda_package_compatible:cuda13"] is False
    assert payload["recommendation"] == "fix_release_matrix_blockers"


def test_windows_release_matrix_blocks_missing_default_promotion_manifest(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_present"] is False
    assert checks["default_promotion_manifest_ready"] is False
    assert checks["default_promotion_default_route_passed"] is False


def test_windows_release_matrix_blocks_failed_default_promotion_manifest(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_present"] is True
    assert checks["default_promotion_manifest_ready"] is False
    assert checks["default_promotion_default_route_passed"] is False
    assert checks["default_promotion_rejection_sample_accounting_passed"] is True
    assert checks["default_promotion_sample_accounting_closure_passed"] is True
    assert checks["default_promotion_stack_engine_contract_ready"] is True


def test_windows_release_matrix_blocks_rejection_sample_accounting_drift(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, rejection_sample_accounting_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_present"]["passed"] is True
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["default_promotion_rejection_sample_accounting_passed"]["evidence"] == {
        "pipeline_contract_status": "failed",
        "pipeline_contract_passed": False,
        "check": False,
        "status": "failed",
        "failed_count": 1,
        "failed_items": [
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
    }


def test_windows_release_matrix_blocks_failed_quality_metrics_compare(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, quality_metrics_compare_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_present"]["passed"] is True
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert (
        checks["default_promotion_quality_metrics_compare_handoff_passed"][
            "passed"
        ]
        is False
    )
    assert checks["default_promotion_quality_metrics_compare_handoff_passed"][
        "evidence"
    ] == {
        "present": True,
        "ready": False,
        "status": "failed",
        "passed": False,
        "phase2_check_passed": False,
        "failed_check_count": 1,
        "failed_checks": ["bad_median_ratio_within_limit"],
        "threshold_failure_count": 1,
        "threshold_failures": [{"metric": "fwhm_px", "bad_median_ratio": 1.4}],
    }


def test_windows_release_matrix_allows_missing_quality_metrics_compare(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_quality_metrics_compare=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is True
    assert (
        "default_promotion_quality_metrics_compare_handoff_passed"
        not in payload["failed_checks"]
    )
    assert checks["default_promotion_quality_metrics_compare_handoff_passed"][
        "passed"
    ] is True
    assert checks["default_promotion_quality_metrics_compare_handoff_passed"][
        "evidence"
    ] == {
        "present": None,
        "ready": None,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_check_count": None,
        "failed_checks": [],
        "threshold_failure_count": None,
        "threshold_failures": [],
    }


def test_windows_release_matrix_blocks_resident_result_contract_drift(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, resident_result_contract_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    resident = payload["default_promotion_manifest"]
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_present"]["passed"] is True
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert (
        checks["default_promotion_resident_result_contract_handoff_passed"][
            "passed"
        ]
        is False
    )
    assert (
        "default_promotion_resident_result_contract_handoff_passed"
        in payload["failed_checks"]
    )
    assert resident["resident_result_contract_ready"] is False
    assert resident["resident_result_contract_status"] == "failed"
    assert resident["resident_result_contract_top_level_check"] is False
    assert resident["resident_result_contract_check_present"] is True
    assert resident["resident_result_contract_check_passed"] is False
    assert resident["resident_result_contract_phase2_check_passed"] is False
    assert resident["resident_result_contract_required_count"] == 1
    assert resident["resident_result_contract_failed_count"] == 1
    assert resident["resident_result_contract_failed_check_count"] == 1
    assert resident["resident_result_contract_failed_checks"] == [
        "source_terms_present"
    ]
    assert checks["default_promotion_resident_result_contract_handoff_passed"][
        "evidence"
    ]["failed_items"][0]["item"] == "H"


def test_windows_release_matrix_blocks_sample_accounting_closure_drift(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, sample_accounting_closure_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_present"]["passed"] is True
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_sample_accounting_closure_passed"]["passed"] is False
    assert checks["default_promotion_sample_accounting_closure_passed"]["evidence"] == {
        "pipeline_contract_status": "failed",
        "pipeline_contract_passed": False,
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


def test_windows_release_matrix_blocks_missing_integration_engine_policy(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        include_integration_engine_policy=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks["default_promotion_acceptance_integration_engine_policy_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_pipeline_integration_engine_policy_passed"][
        "passed"
    ] is False
    assert payload["default_promotion_manifest"]["integration_engine_policy_ready"] is None
    assert checks["default_promotion_acceptance_integration_engine_policy_passed"][
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


def test_windows_release_matrix_blocks_failed_integration_engine_policy(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        acceptance_integration_engine_policy_ready=False,
        pipeline_integration_engine_policy_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_acceptance_integration_engine_policy_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_pipeline_integration_engine_policy_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_acceptance_integration_engine_policy_passed"][
        "evidence"
    ]["non_resident_count"] == 1
    assert checks["default_promotion_pipeline_integration_engine_policy_passed"][
        "evidence"
    ]["failed_items"][0]["failures"] == ["cuda_fast_path_not_explicit"]


def test_windows_release_matrix_blocks_missing_stack_engine_runtime_default(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        include_stack_engine_runtime_default=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks[
        "default_promotion_acceptance_stack_engine_runtime_default_passed"
    ]["passed"] is False
    assert checks["default_promotion_pipeline_stack_engine_runtime_default_passed"][
        "passed"
    ] is False
    assert payload["default_promotion_manifest"][
        "stack_engine_runtime_default_ready"
    ] is None
    assert checks[
        "default_promotion_acceptance_stack_engine_runtime_default_passed"
    ]["evidence"] == {
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


def test_windows_release_matrix_blocks_acceptance_runtime_default_drift(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        acceptance_stack_engine_runtime_default_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks[
        "default_promotion_acceptance_stack_engine_runtime_default_passed"
    ]["passed"] is False
    assert checks["default_promotion_pipeline_stack_engine_runtime_default_passed"][
        "passed"
    ] is True
    assert payload["default_promotion_manifest"][
        "acceptance_stack_engine_runtime_default_legacy_master_count"
    ] == 1
    assert checks[
        "default_promotion_acceptance_stack_engine_runtime_default_passed"
    ]["evidence"]["failed_masters"] == [
        {
            "group_id": "bias_0",
            "engine_family": "legacy",
            "reason": "legacy_master_accumulator",
        }
    ]


def test_windows_release_matrix_blocks_pipeline_runtime_default_drift(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        pipeline_stack_engine_runtime_default_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks[
        "default_promotion_acceptance_stack_engine_runtime_default_passed"
    ]["passed"] is True
    assert checks["default_promotion_pipeline_stack_engine_runtime_default_passed"][
        "passed"
    ] is False
    assert payload["default_promotion_manifest"][
        "pipeline_stack_engine_runtime_default_failed_output_count"
    ] == 1
    assert checks["default_promotion_pipeline_stack_engine_runtime_default_passed"][
        "evidence"
    ]["failed_outputs"] == [
        {
            "item": "H",
            "engine_family": "legacy",
            "reason": "legacy_or_unknown_engine",
        }
    ]


def test_windows_release_matrix_blocks_missing_direct_runtime_evidence(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_direct_runtime_evidence=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_manifest_ready"] is True
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"] is False
    assert checks["default_promotion_direct_pipeline_calibration_evidence"] is False
    assert "default_promotion_direct_acceptance_fastpath_evidence" in payload["failed_checks"]
    assert "default_promotion_direct_pipeline_calibration_evidence" in payload["failed_checks"]


def test_windows_release_matrix_blocks_stale_direct_fastpath_source(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        direct_acceptance_fastpath_source="gate303_handoff_bundle",
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks["default_promotion_direct_acceptance_fastpath_evidence"][
        "evidence"
    ]
    assert payload["passed"] is False
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"][
        "passed"
    ] is False
    assert evidence["source"] == "gate303_handoff_bundle"


def test_windows_release_matrix_blocks_missing_release_direct_publication_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision, include_direct_publication_guard=False)
    _default_promotion(default_promotion)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["release_decision_direct_runtime_publication_guard_passed"][
        "passed"
    ] is False
    assert "release_decision_direct_runtime_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert checks["release_decision_direct_runtime_publication_guard_passed"][
        "evidence"
    ]["present"] is False


def test_windows_release_matrix_blocks_missing_default_promotion_direct_publication_guard(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_release_direct_publication_guard=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["release_decision_direct_runtime_publication_guard_passed"][
        "passed"
    ] is True
    assert checks[
        "default_promotion_release_decision_direct_runtime_publication_guard_passed"
    ]["passed"] is False
    assert "default_promotion_release_decision_direct_runtime_publication_guard_passed" in payload[
        "failed_checks"
    ]
    assert checks[
        "default_promotion_release_decision_direct_runtime_publication_guard_passed"
    ]["evidence"]["present"] is None


def test_windows_release_matrix_blocks_stale_default_promotion_direct_publication_source(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        release_direct_publication_acceptance_source="glass_run_discovery",
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = checks[
        "default_promotion_release_decision_direct_runtime_publication_guard_passed"
    ]["evidence"]
    assert payload["passed"] is False
    assert checks[
        "default_promotion_release_decision_direct_runtime_publication_guard_passed"
    ]["passed"] is False
    assert evidence["acceptance_source"] == "glass_run_discovery"


def test_windows_release_matrix_blocks_missing_stack_engine_contract(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_stack_engine_contract=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks["default_promotion_stack_engine_contract_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"] == {
        "present": None,
        "ready": None,
        "phase2_check_passed": None,
        "status": None,
        "passed": None,
        "scope": None,
        "adoption_recommendation": None,
        "default_gap_count": None,
        "blocker_count": None,
        "blockers": [],
    }


def test_windows_release_matrix_blocks_stack_engine_contract_gap(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"][
        "default_gap_count"
    ] == 1
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"][
        "blocker_count"
    ] == 1


def test_windows_release_matrix_blocks_missing_resident_winsorized_sweep(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_resident_winsorized_sweep=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_required_frame_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_sweep_check_count"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"][
        "evidence"
    ] == {
        "present": None,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "failed_checks": [],
    }


def test_windows_release_matrix_blocks_failed_resident_winsorized_sweep(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        resident_winsorized_sweep_ready=False,
        resident_winsorized_sweep_required_frame_ready=False,
        resident_winsorized_sweep_check_count=26,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_required_frame_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_sweep_check_count"][
        "passed"
    ] is False
    assert checks["default_promotion_resident_winsorized_required_frame_passed"][
        "evidence"
    ] == {
        "actual_frame_count": 200,
        "required_frame_count": 200,
        "required_frame_count_passed": False,
        "required_frame_master_rms": 2.3e-05,
        "required_frame_master_max_abs": 6.1e-05,
    }


def test_windows_release_matrix_blocks_missing_stack_publication_audit(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, include_stack_publication_audit=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is True
    assert checks["default_promotion_stack_engine_publication_audit_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_stack_engine_publication_policy_chain_passed"][
        "passed"
    ] is False
    assert checks[
        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
    ]["passed"] is False
    assert checks["default_promotion_stack_engine_publication_audit_passed"][
        "evidence"
    ] == {
        "present": None,
        "ready": None,
        "status": None,
        "passed": None,
        "phase2_check_passed": None,
        "recommendation": None,
        "check_count": None,
        "failed_check_count": None,
        "failed_checks": [],
    }


def test_windows_release_matrix_blocks_failed_stack_publication_policy_chain(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion, stack_publication_policy_ready=False)

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_publication_audit_passed"][
        "passed"
    ] is False
    assert checks["default_promotion_stack_engine_publication_policy_chain_passed"][
        "passed"
    ] is False
    assert checks[
        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
    ]["passed"] is True
    assert checks["default_promotion_stack_engine_publication_policy_chain_passed"][
        "evidence"
    ] == {
        "phase2_check_passed": False,
        "publish_preflight_policy_ready": False,
        "phase2_policy_ready": False,
        "policy_agreement": False,
    }


def test_windows_release_matrix_blocks_failed_stack_publication_winsorized_chain(
    tmp_path: Path,
):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(
        default_promotion,
        stack_publication_resident_winsorized_ready=False,
    )

    payload = build_windows_release_matrix(
        doctor_json=doctor,
        release_decision_json=decision,
        default_promotion_manifest_json=default_promotion,
        expected_primary_package="cuda13",
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["default_promotion_manifest_ready"]["passed"] is False
    assert checks["default_promotion_stack_engine_publication_policy_chain_passed"][
        "passed"
    ] is True
    assert checks[
        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
    ]["passed"] is False
    assert checks[
        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
    ]["evidence"] == {
        "phase2_check_passed": False,
        "publish_preflight_resident_winsorized_ready": False,
        "phase2_resident_winsorized_ready": False,
        "resident_winsorized_agreement": False,
    }


def test_windows_release_matrix_cli_writes_json_and_markdown(tmp_path: Path):
    doctor = tmp_path / "doctor.json"
    decision = tmp_path / "decision.json"
    default_promotion = tmp_path / "default_promotion.json"
    out = tmp_path / "matrix.json"
    markdown = tmp_path / "matrix.md"
    _blackwell_doctor(doctor)
    _release_decision(decision)
    _default_promotion(default_promotion)

    result = main(
        [
            "windows-release-matrix",
            "--doctor-json",
            str(doctor),
            "--release-decision",
            str(decision),
            "--default-promotion-manifest",
            str(default_promotion),
            "--expected-primary-package",
            "cuda13",
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
    assert "GLASS Windows Release Matrix" in markdown_text
    assert "Default Promotion Manifest" in markdown_text
    assert "Default route contract/checks: `True`/`4`" in markdown_text
    assert "Rejection sample accounting: `passed` failed=`0`" in markdown_text
    assert "Quality metrics compare: present=`True` ready=`True`" in markdown_text
    assert "Sample accounting closure: `passed` present=`1` failed=`0`" in markdown_text
    assert (
        "Integration engine policy: ready=`True` acceptance=`passed` pipeline=`passed`"
        in markdown_text
    )
    assert (
        "StackEngine runtime default: ready=`True` "
        "acceptance=`passed` pipeline=`passed`"
    ) in markdown_text
    assert (
        "Runtime default counts: acceptance-legacy=`0` "
        "acceptance-failed-masters=`0` pipeline-failed-outputs=`0` "
        "explicit-cuda=`1`"
    ) in markdown_text
    assert (
        "Release decision direct publication guard: ready=`True` check=`True` "
        "source-ready=`True` count-ready=`True` lights=`200`"
    ) in markdown_text
    assert (
        "Release decision quality publication guard: ready=`True` check=`True` "
        "quality-present=`True` compatible-missing=`False`"
    ) in markdown_text
    assert (
        "Default promotion direct publication guard: ready=`True` check=`True` "
        "source-ready=`True` count-ready=`True` lights=`200`"
    ) in markdown_text
    assert (
        "Default promotion quality publication guard: ready=`True` check=`True` "
        "raw=`passed` phase2=`passed`"
    ) in markdown_text
    assert (
        "StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`"
        in markdown_text
    )
    assert (
        "Resident winsorized sweep: passed=`True` phase2-check=`True` "
        "required-frame=`200` required-pass=`True` checks=`27`"
    ) in markdown_text
    assert (
        "StackEngine publication audit: ready=`True` passed=`True` "
        "phase2-check=`True` failed=`0`"
    ) in markdown_text
    assert (
        "Publication policy chain: raw=`True` phase2=`True` "
        "agreement=`True` check=`True`"
    ) in markdown_text
    assert (
        "Publication resident winsorized chain: raw=`True` phase2=`True` "
        "agreement=`True` check=`True`"
    ) in markdown_text
