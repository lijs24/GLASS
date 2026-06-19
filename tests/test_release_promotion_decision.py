from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.release_promotion_decision import build_release_promotion_decision


def _release_quality_final_evidence_fields(
    prefix: str,
    *,
    ready: bool,
    compatible_missing: bool = False,
) -> dict[str, object]:
    final_ready = True if compatible_missing else ready
    raw_ready = None if compatible_missing else ready
    phase2_ready = None if compatible_missing else ready
    return {
        f"{prefix}_final_checks_ready": final_ready,
        f"{prefix}_final_checks_match": True,
        f"{prefix}_raw_final_checks_ready": raw_ready,
        f"{prefix}_phase2_final_checks_ready": phase2_ready,
    }


def _write_acceptance(
    path: Path,
    *,
    passed: bool = True,
    warp_quality_passed: bool | None = None,
    resident_fastpath_passed: bool | None = None,
) -> None:
    accounting_status = "passed" if passed else "failed"
    sample_closure_status = "passed" if passed else "failed"
    payload = {
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
    }
    if warp_quality_passed is not None:
        failed_checks = [] if warp_quality_passed else ["warp_output_artifacts_ready"]
        payload["warp_quality_contract"] = {
            "path": "warp_quality_contract.json",
            "exists": True,
            "artifact_type": "warp_quality_contract",
            "status": "passed" if warp_quality_passed else "failed",
            "passed": warp_quality_passed,
            "output_count": 2,
            "check_count": 2,
            "failed_checks": failed_checks,
        }
        payload["checks"] = [
            {
                "name": "warp_quality_contract_present",
                "passed": True,
                "evidence": {"path": "warp_quality_contract.json", "exists": True},
            },
            {
                "name": "warp_quality_contract_type",
                "passed": True,
                "evidence": {"artifact_type": "warp_quality_contract"},
            },
            {
                "name": "warp_quality_contract_passed",
                "passed": warp_quality_passed,
                "evidence": {"failed_checks": failed_checks},
            },
        ]
    if resident_fastpath_passed is not None:
        failed_checks = (
            []
            if resident_fastpath_passed
            else ["contract_resident_registration_fastpath_descriptor_batch_mode"]
        )
        payload["resident_registration_fastpath"] = {
            "source": "explicit_resident_artifacts_json",
            "available": True,
            "exists": True,
            "path": "C:/glass_runs/default_resident/resident_artifacts.json",
            "resident_registration_mode": "resident_triangle_batch",
        }
        payload["release_contract_evidence"][
            "resident_registration_fastpath"
        ] = {
            "schema_version": 1,
            "status": "passed" if resident_fastpath_passed else "failed",
            "required_by_benchmark_contract": True,
            "source": "explicit_resident_artifacts_json",
            "path": "C:/glass_runs/default_resident/resident_artifacts.json",
            "exists": True,
            "available": True,
            "resident_registration_mode": "resident_triangle_batch",
            "descriptor_fit_batch_mode": "batch_gpu",
            "pixel_refine_batch_mode": "batch_gpu",
            "triangle_warp_batch_mode": "batched",
            "triangle_warp_batch_frame_count": 3,
            "warp_copy_mode": "device_to_device",
            "passed_check_count": 3 if resident_fastpath_passed else 2,
            "failed_check_count": 0 if resident_fastpath_passed else 1,
            "failed_checks": failed_checks,
        }
        checks = payload.setdefault("checks", [])
        checks.extend(
            [
                {
                    "name": "contract_resident_registration_fastpath_present",
                    "passed": True,
                    "evidence": {
                        "path": "C:/glass_runs/default_resident/resident_artifacts.json"
                    },
                },
                {
                    "name": "contract_resident_registration_fastpath_descriptor_batch_mode",
                    "passed": resident_fastpath_passed,
                    "evidence": {"actual": "batch_gpu", "required": "batch_gpu"},
                },
                {
                    "name": "contract_resident_registration_fastpath_triangle_warp_batch",
                    "passed": True,
                    "evidence": {"actual": "batched", "required": "batched"},
                },
            ]
        )
    write_json(path, payload)


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


def _write_pipeline_contract_with_resident_winsorized_semantics(path: Path) -> None:
    _write_pipeline_contract(path)
    payload = read_json(path)
    payload["integration"]["outputs"][0]["resident_result_contract"] = {
        "required": True,
        "passed": True,
        "contract": {
            "rejection_semantics": {
                "required": True,
                "present": True,
                "passed": True,
                "status": "passed",
                "rejection": "winsorized_sigma",
                "descriptor_source": "resident_artifacts.integration_rejection",
                "integration_results_descriptor_present": False,
                "resident_artifacts_descriptor_present": True,
                "legacy_completion_applied": True,
                "legacy_completion_source": "fast_approx_algorithm",
                "descriptor": {
                    "resident_winsorized_mode": "fast_approx",
                    "algorithm": "two_stage_winsorized_mean_std_rejection_approximation",
                    "scale_estimator": "mean_std_two_stage_winsorized",
                    "cpu_baseline_parity": False,
                    "parity_status": "known_non_parity_pending_cuda_update",
                    "approximation": True,
                },
            }
        },
    }
    write_json(path, payload)


def _write_pipeline_contract_not_required_sample_scopes(path: Path) -> None:
    write_json(
        path,
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "passed",
            "passed": True,
            "checks": [
                {"name": "integration_dq_contract", "passed": True},
                {"name": "integration_stack_result_contract", "passed": True},
                {"name": "integration_resident_result_contract", "passed": True},
                {"name": "integration_dq_map_pixels_match_summary", "passed": True},
                {"name": "integration_coverage_map_pixels_match_dq", "passed": True},
                {"name": "integration_rejection_map_pixels_match_dq", "passed": True},
                {
                    "name": "integration_rejection_sample_counts_match_maps",
                    "passed": True,
                },
                {"name": "integration_sample_accounting_closure", "passed": True},
            ],
            "rejection_sample_accounting": {
                "status": "not_required",
                "check_name": "integration_rejection_sample_counts_match_maps",
                "check_present": True,
                "check_passed": True,
                "output_count": 1,
                "accounted_output_count": 1,
                "required_count": 0,
                "verified_count": 0,
                "failed_count": 0,
                "failed_items": [],
            },
            "sample_accounting_closure": {
                "status": "not_required",
                "check_name": "integration_sample_accounting_closure",
                "check_present": True,
                "check_passed": True,
                "output_count": 1,
                "present_count": 0,
                "required_count": 0,
                "failed_count": 0,
                "failed_items": [],
            },
            "integration": {
                "outputs": [
                    {
                        "item": "H",
                        "rejection": "none",
                        "sample_accounting_closure": {
                            "present": False,
                            "required": False,
                            "status": "missing",
                            "passed": True,
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
                            "status": "not_required",
                            "verified": False,
                            "ok": True,
                            "required": False,
                            "source_counts": [],
                        },
                    }
                ],
            },
        },
    )


def _write_pipeline_contract_missing_required_rejection_scope(path: Path) -> None:
    write_json(
        path,
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "passed",
            "passed": True,
            "checks": [
                {"name": "integration_dq_contract", "passed": True},
                {"name": "integration_stack_result_contract", "passed": True},
                {"name": "integration_resident_result_contract", "passed": True},
                {"name": "integration_dq_map_pixels_match_summary", "passed": True},
                {"name": "integration_coverage_map_pixels_match_dq", "passed": True},
                {"name": "integration_rejection_map_pixels_match_dq", "passed": True},
                {"name": "integration_sample_accounting_closure", "passed": True},
            ],
            "sample_accounting_closure": {
                "status": "not_required",
                "check_name": "integration_sample_accounting_closure",
                "check_present": True,
                "check_passed": True,
                "output_count": 1,
                "present_count": 0,
                "required_count": 0,
                "failed_count": 0,
                "failed_items": [],
            },
            "integration": {
                "outputs": [
                    {
                        "item": "H",
                        "rejection": "winsorized_sigma",
                        "sample_accounting_closure": {
                            "present": False,
                            "required": False,
                            "status": "missing",
                            "passed": True,
                        },
                    }
                ],
                "maps": [
                    {"item": "H", "map": "master"},
                    {"item": "H", "map": "coverage"},
                    {"item": "H", "map": "dq"},
                    {"item": "H", "map": "low_rejection"},
                    {"item": "H", "map": "high_rejection"},
                ],
            },
            "pixel_verification": {
                "enabled": True,
                "tile_size": 2048,
                "integration_outputs": [
                    {
                        "item": "H",
                        "count_maps": {
                            "low_rejection": {
                                "required": True,
                                "verified": True,
                                "ok": True,
                            },
                            "high_rejection": {
                                "required": True,
                                "verified": True,
                                "ok": True,
                            },
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


def _write_publication_audit(
    path: Path,
    *,
    passed: bool = True,
    include_runtime_default: bool = True,
    include_direct_runtime: bool = True,
    raw_ready: bool = True,
    phase2_ready: bool = True,
    direct_runtime_ready: bool = True,
    phase2_direct_runtime_ready: bool | None = None,
    direct_acceptance_source: str = "explicit_resident_artifacts_json",
    direct_pipeline_source: str = "resident_artifacts_json_fallback",
    direct_resident_lights: int = 200,
    include_quality_compare: bool = True,
    quality_compare_ready: bool = True,
    phase2_quality_compare_ready: bool | None = None,
    include_release_quality_guard: bool = True,
    release_quality_guard_ready: bool = True,
    phase2_release_quality_guard_ready: bool | None = None,
    release_quality_guard_final_checks_ready: bool | None = None,
    phase2_release_quality_guard_final_checks_ready: bool | None = None,
    include_release_quality_guard_final_checks: bool = True,
    include_phase2_release_quality_guard_final_checks: bool = True,
    release_quality_guard_final_evidence_ready: bool | None = None,
    phase2_release_quality_guard_final_evidence_ready: bool | None = None,
    include_release_quality_guard_final_evidence: bool = True,
    include_phase2_release_quality_guard_final_evidence: bool = True,
    release_quality_guard_final_evidence_compatible_missing: bool = False,
    phase2_release_quality_guard_final_evidence_compatible_missing: bool = False,
) -> None:
    phase2_direct_runtime_ready = (
        direct_runtime_ready
        if phase2_direct_runtime_ready is None
        else phase2_direct_runtime_ready
    )
    phase2_quality_compare_ready = (
        quality_compare_ready
        if phase2_quality_compare_ready is None
        else phase2_quality_compare_ready
    )
    phase2_release_quality_guard_ready = (
        release_quality_guard_ready
        if phase2_release_quality_guard_ready is None
        else phase2_release_quality_guard_ready
    )
    release_quality_final_checks_ready = (
        release_quality_guard_ready
        if release_quality_guard_final_checks_ready is None
        else release_quality_guard_final_checks_ready
    )
    phase2_release_quality_final_checks_ready = (
        phase2_release_quality_guard_ready
        if phase2_release_quality_guard_final_checks_ready is None
        else phase2_release_quality_guard_final_checks_ready
    )
    release_quality_final_evidence_ready = (
        release_quality_final_checks_ready
        if release_quality_guard_final_evidence_ready is None
        else release_quality_guard_final_evidence_ready
    )
    phase2_release_quality_final_evidence_ready = (
        phase2_release_quality_final_checks_ready
        if phase2_release_quality_guard_final_evidence_ready is None
        else phase2_release_quality_guard_final_evidence_ready
    )
    release_quality_final_checks_passed = (
        release_quality_final_checks_ready
        or not include_release_quality_guard_final_checks
    )
    phase2_release_quality_final_checks_passed = (
        phase2_release_quality_final_checks_ready
        or not include_phase2_release_quality_guard_final_checks
    )
    release_quality_final_evidence_passed = (
        release_quality_final_evidence_ready
        or release_quality_guard_final_evidence_compatible_missing
        or not include_release_quality_guard_final_evidence
    )
    phase2_release_quality_final_evidence_passed = (
        phase2_release_quality_final_evidence_ready
        or phase2_release_quality_guard_final_evidence_compatible_missing
        or not include_phase2_release_quality_guard_final_evidence
    )
    release_quality_chain_ready = (
        release_quality_guard_ready
        and release_quality_final_checks_passed
        and release_quality_final_evidence_passed
    )
    phase2_release_quality_chain_ready = (
        phase2_release_quality_guard_ready
        and phase2_release_quality_final_checks_passed
        and phase2_release_quality_final_evidence_passed
    )
    artifact_passed = (
        passed
        and (raw_ready and phase2_ready if include_runtime_default else True)
        and (
            quality_compare_ready and phase2_quality_compare_ready
            if include_quality_compare
            else True
        )
        and (
            release_quality_chain_ready and phase2_release_quality_chain_ready
            if include_release_quality_guard
            else True
        )
    )
    runtime_status = "passed" if raw_ready else "failed"
    phase2_status = "passed" if phase2_ready else "failed"
    quality_compare_status = "passed" if quality_compare_ready else "failed"
    phase2_quality_compare_status = (
        "passed" if phase2_quality_compare_ready else "failed"
    )
    release_quality_guard_raw_status = (
        "passed" if release_quality_guard_ready else "failed"
    )
    release_quality_guard_phase2_status = (
        "passed" if release_quality_guard_ready else "attention_required"
    )
    phase2_release_quality_guard_raw_status = (
        "passed" if phase2_release_quality_guard_ready else "failed"
    )
    phase2_release_quality_guard_phase2_status = (
        "passed" if phase2_release_quality_guard_ready else "attention_required"
    )
    layers = {}
    checks = []
    if include_runtime_default:
        layers = {
            "publish_preflight_stack_engine_runtime_default": {
                "status": "publish_preflight_ready" if raw_ready else "blocked",
                "ready": raw_ready,
                "matrix_acceptance_status": runtime_status,
                "matrix_pipeline_status": runtime_status,
                "matrix_acceptance_legacy_master_count": 0 if raw_ready else 1,
                "matrix_pipeline_failed_output_count": 0 if raw_ready else 1,
            },
            "phase2_publish_preflight_stack_engine_runtime_default": {
                "status": "publish_preflight_ready" if phase2_ready else "blocked",
                "ready": phase2_ready,
                "phase2_check_passed": phase2_ready,
                "matrix_acceptance_status": phase2_status,
                "matrix_pipeline_status": phase2_status,
                "matrix_acceptance_legacy_master_count": 0 if phase2_ready else 1,
                "matrix_pipeline_failed_output_count": 0 if phase2_ready else 1,
            },
        }
        checks = [
            {
                "name": "publish_preflight_stack_engine_runtime_default_ready",
                "passed": raw_ready,
            },
            {
                "name": "phase2_publish_preflight_stack_engine_runtime_default_ready",
                "passed": phase2_ready,
            },
            {
                "name": (
                    "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight"
                ),
                "passed": raw_ready and phase2_ready,
            },
        ]
    if include_direct_runtime:
        layers.update(
            {
                "publish_preflight_direct_runtime_evidence": {
                    "artifact_type": "windows_publish_preflight",
                    "status": "publish_preflight_ready"
                    if direct_runtime_ready
                    else "blocked",
                    "passed": direct_runtime_ready,
                    "ready": direct_runtime_ready,
                    "matrix_ready": direct_runtime_ready,
                    "matrix_acceptance_source": direct_acceptance_source,
                    "matrix_acceptance_check_count": 24,
                    "matrix_pipeline_calibration_source": direct_pipeline_source,
                    "matrix_pipeline_resident_lights": direct_resident_lights,
                    "default_promotion_ready": direct_runtime_ready,
                    "default_promotion_acceptance_source": direct_acceptance_source,
                    "default_promotion_acceptance_check_count": 24,
                    "default_promotion_pipeline_calibration_source": (
                        direct_pipeline_source
                    ),
                    "default_promotion_pipeline_resident_lights": (
                        direct_resident_lights
                    ),
                    "matrix_acceptance_passed": direct_runtime_ready,
                    "matrix_pipeline_passed": direct_runtime_ready,
                    "default_promotion_acceptance_passed": direct_runtime_ready,
                    "default_promotion_pipeline_passed": direct_runtime_ready,
                    "matches_default_promotion": direct_runtime_ready,
                },
                "phase2_publish_preflight_direct_runtime_evidence": {
                    "artifact_type": "glass_phase2_status",
                    "status": "publish_preflight_ready"
                    if phase2_direct_runtime_ready
                    else "blocked",
                    "ready": phase2_direct_runtime_ready,
                    "matrix_ready": phase2_direct_runtime_ready,
                    "matrix_acceptance_source": direct_acceptance_source,
                    "matrix_acceptance_check_count": 24,
                    "matrix_pipeline_calibration_source": direct_pipeline_source,
                    "matrix_pipeline_resident_lights": direct_resident_lights,
                    "default_promotion_ready": phase2_direct_runtime_ready,
                    "default_promotion_acceptance_source": direct_acceptance_source,
                    "default_promotion_acceptance_check_count": 24,
                    "default_promotion_pipeline_calibration_source": (
                        direct_pipeline_source
                    ),
                    "default_promotion_pipeline_resident_lights": (
                        direct_resident_lights
                    ),
                    "matrix_acceptance_passed": phase2_direct_runtime_ready,
                    "matrix_pipeline_passed": phase2_direct_runtime_ready,
                    "default_promotion_acceptance_passed": (
                        phase2_direct_runtime_ready
                    ),
                    "default_promotion_pipeline_passed": phase2_direct_runtime_ready,
                    "matches_default_promotion": phase2_direct_runtime_ready,
                    "phase2_check_passed": phase2_direct_runtime_ready,
                },
            }
        )
        checks.extend(
            [
                {
                    "name": "publish_preflight_direct_runtime_evidence_ready",
                    "passed": direct_runtime_ready,
                },
                {
                    "name": (
                        "phase2_publish_preflight_direct_runtime_evidence_ready"
                    ),
                    "passed": phase2_direct_runtime_ready,
                },
                {
                    "name": (
                        "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
                    ),
                    "passed": direct_runtime_ready and phase2_direct_runtime_ready,
                },
            ]
        )
    if include_quality_compare:
        quality_failed_count = 0 if quality_compare_ready else 1
        phase2_quality_failed_count = 0 if phase2_quality_compare_ready else 1
        layers.update(
            {
                "publish_preflight_quality_metrics_compare": {
                    "artifact_type": "windows_publish_preflight",
                    "status": "publish_preflight_ready"
                    if quality_compare_ready
                    else "blocked",
                    "passed": quality_compare_ready,
                    "present": True,
                    "ready": quality_compare_ready,
                    "matrix_present": True,
                    "matrix_ready": quality_compare_ready,
                    "matrix_status": quality_compare_status,
                    "matrix_failed_check_count": quality_failed_count,
                    "default_promotion_present": True,
                    "default_promotion_ready": quality_compare_ready,
                    "default_promotion_status": quality_compare_status,
                    "default_promotion_failed_check_count": quality_failed_count,
                    "matrix_handoff_passed": quality_compare_ready,
                    "default_promotion_handoff_passed": quality_compare_ready,
                    "matches_default_promotion": quality_compare_ready,
                },
                "phase2_publish_preflight_quality_metrics_compare": {
                    "artifact_type": "glass_phase2_status",
                    "status": "publish_preflight_ready"
                    if phase2_quality_compare_ready
                    else "blocked",
                    "present": True,
                    "ready": phase2_quality_compare_ready,
                    "phase2_check_passed": phase2_quality_compare_ready,
                    "matrix_present": True,
                    "matrix_ready": phase2_quality_compare_ready,
                    "matrix_status": phase2_quality_compare_status,
                    "matrix_failed_check_count": phase2_quality_failed_count,
                    "default_promotion_present": True,
                    "default_promotion_ready": phase2_quality_compare_ready,
                    "default_promotion_status": phase2_quality_compare_status,
                    "default_promotion_failed_check_count": (
                        phase2_quality_failed_count
                    ),
                    "matrix_handoff_passed": phase2_quality_compare_ready,
                    "default_promotion_handoff_passed": (
                        phase2_quality_compare_ready
                    ),
                    "matches_default_promotion": phase2_quality_compare_ready,
                },
            }
        )
        checks.extend(
            [
                {
                    "name": "publish_preflight_quality_metrics_compare_ready",
                    "passed": quality_compare_ready,
                },
                {
                    "name": "phase2_publish_preflight_quality_metrics_compare_ready",
                    "passed": phase2_quality_compare_ready,
                },
                {
                    "name": (
                        "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight"
                    ),
                    "passed": (
                        quality_compare_ready and phase2_quality_compare_ready
                    ),
                },
            ]
        )
    if include_release_quality_guard:
        layers.update(
            {
                "publish_preflight_release_quality_publication_guard": {
                    "artifact_type": "windows_publish_preflight",
                    "status": "publish_preflight_ready"
                    if release_quality_chain_ready
                    else "blocked",
                    "passed": release_quality_chain_ready,
                    "present": True,
                    "ready": release_quality_chain_ready,
                    "matrix_present": True,
                    "matrix_ready": release_quality_guard_ready,
                    "matrix_check_passed": release_quality_guard_ready,
                    "matrix_layers_ready": release_quality_guard_ready,
                    "matrix_raw_status": release_quality_guard_raw_status,
                    "matrix_phase2_status": release_quality_guard_phase2_status,
                    "matrix_default_ready": release_quality_guard_ready,
                    "matrix_default_raw_status": release_quality_guard_raw_status,
                    "matrix_default_phase2_status": (
                        release_quality_guard_phase2_status
                    ),
                    "default_promotion_present": True,
                    "default_promotion_ready": release_quality_guard_ready,
                    "default_promotion_check_passed": release_quality_guard_ready,
                    "default_promotion_layers_ready": release_quality_guard_ready,
                    "default_promotion_raw_status": release_quality_guard_raw_status,
                    "default_promotion_phase2_status": (
                        release_quality_guard_phase2_status
                    ),
                    "matrix_check": release_quality_guard_ready,
                    "matrix_default_check": release_quality_guard_ready,
                    "default_promotion_check": release_quality_guard_ready,
                    "matrix_default_match_check": release_quality_guard_ready,
                    "matrix_manifest_match_check": release_quality_guard_ready,
                },
                "phase2_publish_preflight_release_quality_publication_guard": {
                    "artifact_type": "glass_phase2_status",
                    "status": "publish_preflight_ready"
                    if phase2_release_quality_chain_ready
                    else "blocked",
                    "present": True,
                    "ready": phase2_release_quality_chain_ready,
                    "phase2_check_passed": phase2_release_quality_chain_ready,
                    "matrix_present": True,
                    "matrix_ready": phase2_release_quality_guard_ready,
                    "matrix_check_passed": phase2_release_quality_guard_ready,
                    "matrix_layers_ready": phase2_release_quality_guard_ready,
                    "matrix_raw_status": phase2_release_quality_guard_raw_status,
                    "matrix_phase2_status": (
                        phase2_release_quality_guard_phase2_status
                    ),
                    "matrix_default_ready": phase2_release_quality_guard_ready,
                    "matrix_default_raw_status": (
                        phase2_release_quality_guard_raw_status
                    ),
                    "matrix_default_phase2_status": (
                        phase2_release_quality_guard_phase2_status
                    ),
                    "default_promotion_present": True,
                    "default_promotion_ready": phase2_release_quality_guard_ready,
                    "default_promotion_check_passed": (
                        phase2_release_quality_guard_ready
                    ),
                    "default_promotion_layers_ready": (
                        phase2_release_quality_guard_ready
                    ),
                    "default_promotion_raw_status": (
                        phase2_release_quality_guard_raw_status
                    ),
                    "default_promotion_phase2_status": (
                        phase2_release_quality_guard_phase2_status
                    ),
                    "matrix_check": phase2_release_quality_guard_ready,
                    "matrix_default_check": phase2_release_quality_guard_ready,
                    "default_promotion_check": phase2_release_quality_guard_ready,
                    "matrix_default_match_check": phase2_release_quality_guard_ready,
                    "matrix_manifest_match_check": phase2_release_quality_guard_ready,
                },
            }
        )
        if include_release_quality_guard_final_checks:
            layers["publish_preflight_release_quality_publication_guard"].update(
                {
                    "release_matrix_check": release_quality_final_checks_ready,
                    "release_matrix_default_check": (
                        release_quality_final_checks_ready
                    ),
                    "release_default_promotion_check": (
                        release_quality_final_checks_ready
                    ),
                    "release_matrix_default_match_check": (
                        release_quality_final_checks_ready
                    ),
                    "release_matrix_manifest_match_check": (
                        release_quality_final_checks_ready
                    ),
                }
            )
        if include_release_quality_guard_final_evidence:
            for prefix in ("matrix", "matrix_default", "default_promotion"):
                layers["publish_preflight_release_quality_publication_guard"].update(
                    _release_quality_final_evidence_fields(
                        prefix,
                        ready=release_quality_final_evidence_ready,
                        compatible_missing=release_quality_guard_final_evidence_compatible_missing,
                    )
                )
        if include_phase2_release_quality_guard_final_checks:
            layers[
                "phase2_publish_preflight_release_quality_publication_guard"
            ].update(
                {
                    "release_matrix_check": (
                        phase2_release_quality_final_checks_ready
                    ),
                    "release_matrix_default_check": (
                        phase2_release_quality_final_checks_ready
                    ),
                    "release_default_promotion_check": (
                        phase2_release_quality_final_checks_ready
                    ),
                    "release_matrix_default_match_check": (
                        phase2_release_quality_final_checks_ready
                    ),
                    "release_matrix_manifest_match_check": (
                        phase2_release_quality_final_checks_ready
                    ),
                }
            )
        if include_phase2_release_quality_guard_final_evidence:
            for prefix in ("matrix", "matrix_default", "default_promotion"):
                layers[
                    "phase2_publish_preflight_release_quality_publication_guard"
                ].update(
                    _release_quality_final_evidence_fields(
                        prefix,
                        ready=phase2_release_quality_final_evidence_ready,
                        compatible_missing=phase2_release_quality_guard_final_evidence_compatible_missing,
                    )
                )
        checks.extend(
            [
                {
                    "name": "publish_preflight_release_quality_publication_guard_ready",
                    "passed": release_quality_chain_ready,
                },
                {
                    "name": (
                        "phase2_publish_preflight_release_quality_publication_guard_ready"
                    ),
                    "passed": phase2_release_quality_chain_ready,
                },
                {
                    "name": (
                        "phase2_publish_preflight_release_quality_publication_guard_"
                        "matches_publish_preflight"
                    ),
                    "passed": (
                        release_quality_chain_ready
                        and phase2_release_quality_chain_ready
                        and (
                            include_release_quality_guard_final_checks
                            == include_phase2_release_quality_guard_final_checks
                        )
                        and (
                            include_release_quality_guard_final_evidence
                            == include_phase2_release_quality_guard_final_evidence
                        )
                    ),
                },
            ]
        )
    write_json(
        path,
        {
            "artifact_type": "stack_engine_publication_audit",
            "status": "passed" if artifact_passed else "blocked",
            "passed": artifact_passed,
            "recommendation": "publication_chain_ready"
            if artifact_passed
            else "fix_stack_engine_publication_chain",
            "layers": layers,
            "checks": checks,
            "failed_checks": [
                str(item["name"]) for item in checks if item.get("passed") is not True
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


def test_release_promotion_decision_surfaces_warp_quality_handoff(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance, warp_quality_passed=True)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["warp_quality_handoff"]
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert checks["warp_quality_contract_handoff"]["passed"] is True
    assert evidence["status"] == "passed"
    assert evidence["ready"] is True
    assert evidence["present"] is True
    assert evidence["contract_passed"] is True
    assert evidence["output_count"] == 2
    assert evidence["acceptance_checks"] == {
        "warp_quality_contract_present": True,
        "warp_quality_contract_type": True,
        "warp_quality_contract_passed": True,
    }


def test_release_promotion_decision_blocks_failed_warp_quality_handoff(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance, warp_quality_passed=False)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["warp_quality_handoff"]
    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert checks["warp_quality_contract_handoff"]["passed"] is False
    assert evidence["status"] == "failed"
    assert evidence["ready"] is False
    assert evidence["failed_checks"] == ["warp_output_artifacts_ready"]
    assert evidence["failed_acceptance_checks"] == ["warp_quality_contract_passed"]


def test_release_promotion_decision_surfaces_resident_fastpath_handoff(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance, resident_fastpath_passed=True)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["resident_registration_fastpath_handoff"]
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert checks["resident_registration_fastpath_handoff"]["passed"] is True
    assert evidence["status"] == "passed"
    assert evidence["ready"] is True
    assert evidence["present"] is True
    assert evidence["required_by_benchmark_contract"] is True
    assert evidence["source"] == "explicit_resident_artifacts_json"
    assert evidence["resident_registration_mode"] == "resident_triangle_batch"
    assert evidence["descriptor_fit_batch_mode"] == "batch_gpu"
    assert evidence["triangle_warp_batch_mode"] == "batched"
    assert evidence["triangle_warp_batch_frame_count"] == 3
    assert evidence["warp_copy_mode"] == "device_to_device"
    assert evidence["passed_check_count"] == 3
    assert evidence["failed_check_count"] == 0
    assert evidence["failed_acceptance_checks"] == []


def test_release_promotion_decision_blocks_failed_resident_fastpath_handoff(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance, resident_fastpath_passed=False)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["resident_registration_fastpath_handoff"]
    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert checks["resident_registration_fastpath_handoff"]["passed"] is False
    assert evidence["status"] == "failed"
    assert evidence["ready"] is False
    assert evidence["failed_check_count"] == 1
    assert evidence["failed_checks"] == [
        "contract_resident_registration_fastpath_descriptor_batch_mode"
    ]
    assert evidence["failed_acceptance_checks"] == [
        "contract_resident_registration_fastpath_descriptor_batch_mode"
    ]


def test_release_promotion_decision_accepts_publication_runtime_default(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["stack_engine_publication_runtime_default"]
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert checks["stack_engine_publication_runtime_default_passed"]["passed"] is True
    assert evidence["checks_passed"] is True
    assert evidence["raw_ready"] is True
    assert evidence["phase2_ready"] is True
    assert evidence["phase2_check_passed"] is True
    direct = payload["stack_engine_publication_direct_runtime_evidence"]
    assert checks["stack_engine_publication_direct_runtime_evidence_passed"][
        "passed"
    ] is True
    assert direct["ready"] is True
    assert direct["raw_matrix_acceptance_source"] == "explicit_resident_artifacts_json"
    assert direct["raw_matrix_pipeline_calibration_source"] == (
        "resident_artifacts_json_fallback"
    )
    assert direct["raw_matrix_pipeline_resident_lights"] == 200
    quality = payload["stack_engine_publication_quality_metrics_compare"]
    assert checks["stack_engine_publication_quality_metrics_compare_passed"][
        "passed"
    ] is True
    assert quality["ready"] is True
    assert quality["checks_passed"] is True
    assert quality["quality_compare_present"] is True
    assert quality["raw_matrix_status"] == "passed"
    assert quality["phase2_matrix_status"] == "passed"
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is True
    assert release_quality["ready"] is True
    assert release_quality["checks_passed"] is True
    assert release_quality["release_quality_guard_present"] is True
    assert release_quality["raw_matrix_raw_status"] == "passed"
    assert release_quality["phase2_matrix_raw_status"] == "passed"
    assert release_quality["final_evidence_ready"] is True
    assert release_quality["final_evidence_match"] is True
    assert release_quality["raw_final_evidence_present"] is True
    assert release_quality["phase2_final_evidence_present"] is True
    assert release_quality["raw_matrix_final_checks_ready"] is True
    assert release_quality["raw_matrix_raw_final_checks_ready"] is True
    assert release_quality["raw_matrix_phase2_final_checks_ready"] is True
    assert release_quality["phase2_matrix_final_checks_ready"] is True
    assert release_quality["phase2_matrix_phase2_final_checks_ready"] is True


def test_release_promotion_decision_blocks_failed_publication_runtime_default(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, raw_ready=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["stack_engine_publication_runtime_default"]
    assert payload["passed"] is False
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert checks["stack_engine_publication_runtime_default_passed"]["passed"] is False
    assert evidence["checks"]["publish_preflight_stack_engine_runtime_default_ready"] is False
    assert evidence["raw_ready"] is False
    assert evidence["raw_legacy_master_count"] == 1
    assert evidence["raw_failed_output_count"] == 1


def test_release_promotion_decision_blocks_stale_publication_runtime_default(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, include_runtime_default=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["stack_engine_publication_runtime_default"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_runtime_default_passed"]["passed"] is False
    assert evidence["status"] == "passed"
    assert evidence["checks_passed"] is False
    assert evidence["checks"] == {
        "publish_preflight_stack_engine_runtime_default_ready": None,
        "phase2_publish_preflight_stack_engine_runtime_default_ready": None,
        "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight": None,
    }


def test_release_promotion_decision_allows_missing_publication_quality_compare(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, include_quality_compare=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    quality = payload["stack_engine_publication_quality_metrics_compare"]
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert checks["stack_engine_publication_quality_metrics_compare_passed"][
        "passed"
    ] is True
    assert quality["ready"] is True
    assert quality["compatible_missing"] is True
    assert quality["quality_compare_present"] is False
    assert quality["checks"] == {
        "publish_preflight_quality_metrics_compare_ready": None,
        "phase2_publish_preflight_quality_metrics_compare_ready": None,
        "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight": None,
    }


def test_release_promotion_decision_blocks_failed_publication_quality_compare(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, quality_compare_ready=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    quality = payload["stack_engine_publication_quality_metrics_compare"]
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert checks["stack_engine_publication_quality_metrics_compare_passed"][
        "passed"
    ] is False
    assert quality["ready"] is False
    assert quality["checks"]["publish_preflight_quality_metrics_compare_ready"] is False
    assert quality["raw_matrix_status"] == "failed"
    assert quality["raw_matrix_failed_check_count"] == 1


def test_release_promotion_decision_blocks_phase2_publication_quality_mismatch(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        quality_compare_ready=True,
        phase2_quality_compare_ready=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    quality = payload["stack_engine_publication_quality_metrics_compare"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_quality_metrics_compare_passed"][
        "passed"
    ] is False
    assert quality["checks"]["publish_preflight_quality_metrics_compare_ready"] is True
    assert (
        quality["checks"]["phase2_publish_preflight_quality_metrics_compare_ready"]
        is False
    )
    assert quality["phase2_matrix_status"] == "failed"


def test_release_promotion_decision_allows_missing_publication_release_quality_guard(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, include_release_quality_guard=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is True
    assert release_quality["ready"] is True
    assert release_quality["compatible_missing"] is True
    assert release_quality["release_quality_guard_present"] is False
    assert release_quality["checks"] == {
        "publish_preflight_release_quality_publication_guard_ready": None,
        "phase2_publish_preflight_release_quality_publication_guard_ready": None,
        "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight": None,
    }


def test_release_promotion_decision_allows_legacy_publication_release_quality_guard_without_final_checks(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        include_release_quality_guard_final_checks=False,
        include_phase2_release_quality_guard_final_checks=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is True
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is True
    assert release_quality["ready"] is True
    assert release_quality["final_checks_compatible_missing"] is True
    assert release_quality["final_checks_ready"] is True
    assert release_quality["raw_final_checks_present"] is False
    assert release_quality["phase2_final_checks_present"] is False
    assert release_quality["raw_release_matrix_check"] is None
    assert release_quality["phase2_release_matrix_check"] is None


def test_release_promotion_decision_allows_compatible_missing_publication_release_quality_final_evidence(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        release_quality_guard_final_evidence_compatible_missing=True,
        phase2_release_quality_guard_final_evidence_compatible_missing=True,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is True
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is True
    assert release_quality["ready"] is True
    assert release_quality["final_evidence_ready"] is True
    assert release_quality["final_evidence_match"] is True
    assert release_quality["raw_matrix_final_checks_ready"] is True
    assert release_quality["raw_matrix_final_checks_match"] is True
    assert release_quality["raw_matrix_raw_final_checks_ready"] is None
    assert release_quality["raw_matrix_phase2_final_checks_ready"] is None
    assert release_quality["phase2_matrix_raw_final_checks_ready"] is None


def test_release_promotion_decision_allows_legacy_publication_release_quality_without_final_evidence(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        include_release_quality_guard_final_evidence=False,
        include_phase2_release_quality_guard_final_evidence=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is True
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is True
    assert release_quality["final_evidence_compatible_missing"] is True
    assert release_quality["final_evidence_ready"] is True
    assert release_quality["raw_final_evidence_present"] is False
    assert release_quality["phase2_final_evidence_present"] is False
    assert release_quality["raw_matrix_final_checks_ready"] is None
    assert release_quality["phase2_matrix_final_checks_ready"] is None


def test_release_promotion_decision_blocks_failed_publication_release_quality_final_evidence(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        release_quality_guard_final_checks_ready=True,
        release_quality_guard_final_evidence_ready=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert release_quality["ready"] is False
    assert release_quality["raw_final_evidence_present"] is True
    assert release_quality["raw_final_evidence_ready"] is False
    assert release_quality["final_evidence_ready"] is False
    assert release_quality["raw_matrix_final_checks_ready"] is False
    assert release_quality["raw_matrix_raw_final_checks_ready"] is False
    assert release_quality["raw_matrix_phase2_final_checks_ready"] is False


def test_release_promotion_decision_blocks_failed_phase2_publication_release_quality_final_evidence(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        phase2_release_quality_guard_final_checks_ready=True,
        phase2_release_quality_guard_final_evidence_ready=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert release_quality["raw_final_evidence_ready"] is True
    assert release_quality["phase2_final_evidence_ready"] is False
    assert release_quality["final_evidence_ready"] is False
    assert release_quality["phase2_matrix_final_checks_ready"] is False
    assert release_quality["phase2_matrix_raw_final_checks_ready"] is False


def test_release_promotion_decision_blocks_missing_phase2_publication_release_quality_final_evidence(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        include_phase2_release_quality_guard_final_evidence=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert release_quality["raw_final_evidence_present"] is True
    assert release_quality["phase2_final_evidence_present"] is False
    assert release_quality["final_evidence_match"] is False
    assert release_quality["final_evidence_ready"] is False
    assert release_quality["raw_matrix_final_checks_ready"] is True
    assert release_quality["phase2_matrix_final_checks_ready"] is None
    assert (
        release_quality["checks"][
            "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight"
        ]
        is False
    )


def test_release_promotion_decision_blocks_failed_publication_release_quality_guard(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, release_quality_guard_ready=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert release_quality["ready"] is False
    assert (
        release_quality["checks"][
            "publish_preflight_release_quality_publication_guard_ready"
        ]
        is False
    )
    assert release_quality["raw_matrix_raw_status"] == "failed"
    assert release_quality["raw_matrix_phase2_status"] == "attention_required"


def test_release_promotion_decision_blocks_failed_publication_release_quality_final_checks(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        release_quality_guard_final_checks_ready=False,
        phase2_release_quality_guard_final_checks_ready=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert release_quality["ready"] is False
    assert release_quality["raw_matrix_ready"] is True
    assert release_quality["phase2_matrix_ready"] is True
    assert release_quality["raw_final_checks_present"] is True
    assert release_quality["phase2_final_checks_present"] is True
    assert release_quality["raw_final_checks_ready"] is False
    assert release_quality["phase2_final_checks_ready"] is False
    assert release_quality["final_checks_ready"] is False
    assert release_quality["raw_release_matrix_check"] is False
    assert release_quality["phase2_release_matrix_check"] is False


def test_release_promotion_decision_blocks_phase2_publication_release_quality_mismatch(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        release_quality_guard_ready=True,
        phase2_release_quality_guard_ready=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert (
        release_quality["checks"][
            "publish_preflight_release_quality_publication_guard_ready"
        ]
        is True
    )
    assert (
        release_quality["checks"][
            "phase2_publish_preflight_release_quality_publication_guard_ready"
        ]
        is False
    )
    assert release_quality["phase2_matrix_raw_status"] == "failed"


def test_release_promotion_decision_blocks_missing_phase2_publication_release_quality_final_checks(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        include_phase2_release_quality_guard_final_checks=False,
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    release_quality = payload["stack_engine_publication_release_quality_guard"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_release_quality_guard_passed"][
        "passed"
    ] is False
    assert release_quality["raw_final_checks_present"] is True
    assert release_quality["phase2_final_checks_present"] is False
    assert release_quality["final_checks_match"] is False
    assert release_quality["final_checks_ready"] is False
    assert release_quality["raw_release_matrix_check"] is True
    assert release_quality["phase2_release_matrix_check"] is None
    assert (
        release_quality["checks"][
            "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight"
        ]
        is False
    )


def test_release_promotion_decision_blocks_missing_publication_direct_runtime(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, include_direct_runtime=False)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    direct = payload["stack_engine_publication_direct_runtime_evidence"]
    assert payload["release_candidate_ready"] is False
    assert payload["default_change_ready"] is False
    assert checks["stack_engine_publication_runtime_default_passed"]["passed"] is True
    assert checks["stack_engine_publication_direct_runtime_evidence_passed"][
        "passed"
    ] is False
    assert direct["checks_passed"] is False
    assert direct["raw_ready"] is None
    assert direct["phase2_ready"] is None


def test_release_promotion_decision_blocks_stale_publication_direct_source(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(
        publication,
        direct_acceptance_source="glass_run_discovery",
    )

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    direct = payload["stack_engine_publication_direct_runtime_evidence"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_direct_runtime_evidence_passed"][
        "passed"
    ] is False
    assert direct["checks_passed"] is True
    assert direct["raw_source_ready"] is False
    assert direct["phase2_source_ready"] is False
    assert direct["raw_matrix_acceptance_source"] == "glass_run_discovery"


def test_release_promotion_decision_blocks_short_publication_direct_runtime(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    runtime = tmp_path / "runtime_compare.json"
    publication = tmp_path / "publication_audit.json"
    _write_acceptance(acceptance)
    _write_runtime_compare(runtime)
    _write_publication_audit(publication, direct_resident_lights=199)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        runtime_compare=runtime,
        stack_engine_publication_audit=publication,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    direct = payload["stack_engine_publication_direct_runtime_evidence"]
    assert payload["release_candidate_ready"] is False
    assert checks["stack_engine_publication_direct_runtime_evidence_passed"][
        "passed"
    ] is False
    assert direct["raw_count_ready"] is False
    assert direct["phase2_count_ready"] is False
    assert direct["raw_matrix_pipeline_resident_lights"] == 199


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
    evidence = checks["pipeline_sample_accounting_closure_passed"]["evidence"]
    assert evidence["ready"] is False
    assert evidence["check"] is False
    assert evidence["status"] == "failed"
    assert evidence["scope"] == "required"
    assert evidence["present_count"] == 1
    assert evidence["required_count"] == 1
    assert evidence["failed_count"] == 1
    assert evidence["failed_items"] == [
        {
            "item": "H",
            "input_valid_samples_before_rejection": 9,
            "valid_samples_after_rejection": 6,
            "rejected_samples": 2,
        }
    ]


def test_release_promotion_decision_accepts_not_required_sample_scopes(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    stack = tmp_path / "stack.json"
    pipeline = tmp_path / "pipeline.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_stack_contract(stack)
    _write_pipeline_contract_not_required_sample_scopes(pipeline)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        stack_engine_contract=stack,
        pipeline_contract=pipeline,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["release_candidate_ready"] is True
    assert payload["default_change_ready"] is True
    assert payload["pipeline_rejection_sample_release"] == {
        "ready": True,
        "check": True,
        "status": "not_required",
        "check_present": True,
        "required_count": 0,
        "verified_count": 0,
        "accounted_output_count": 1,
        "failed_count": 0,
        "failed_items": [],
        "scope": "not_required",
    }
    assert payload["pipeline_sample_closure_release"]["ready"] is True
    assert payload["pipeline_sample_closure_release"]["scope"] == "not_required"
    assert checks["pipeline_rejection_sample_accounting_passed"]["passed"] is True
    assert checks["pipeline_sample_accounting_closure_passed"]["passed"] is True


def test_release_promotion_decision_surfaces_resident_winsorized_semantics(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    stack = tmp_path / "stack.json"
    pipeline = tmp_path / "pipeline.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_stack_contract(stack)
    _write_pipeline_contract_with_resident_winsorized_semantics(pipeline)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        stack_engine_contract=stack,
        pipeline_contract=pipeline,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    evidence = payload["pipeline_resident_winsorized_semantics_release"]
    assert payload["default_change_ready"] is True
    assert checks["pipeline_resident_winsorized_semantics_handoff"]["passed"] is True
    assert evidence["status"] == "passed"
    assert evidence["ready"] is True
    assert evidence["required_count"] == 1
    assert evidence["legacy_completion_count"] == 1
    assert evidence["descriptor_sources"] == [
        "resident_artifacts.integration_rejection"
    ]
    row = evidence["rows"][0]
    assert row["resident_winsorized_mode"] == "fast_approx"
    assert row["legacy_completion_source"] == "fast_approx_algorithm"
    assert row["parity_status"] == "known_non_parity_pending_cuda_update"
    assert row["resident_artifacts_descriptor_present"] is True


def test_release_promotion_decision_blocks_missing_required_rejection_sample_scope(
    tmp_path: Path,
) -> None:
    acceptance = tmp_path / "acceptance.json"
    stack = tmp_path / "stack.json"
    pipeline = tmp_path / "pipeline.json"
    runtime = tmp_path / "runtime_compare.json"
    _write_acceptance(acceptance)
    _write_stack_contract(stack)
    _write_pipeline_contract_missing_required_rejection_scope(pipeline)
    _write_runtime_compare(runtime)

    payload = build_release_promotion_decision(
        acceptance_audit=acceptance,
        stack_engine_contract=stack,
        pipeline_contract=pipeline,
        runtime_compare=runtime,
        min_runtime_runs=3,
    )

    evidence = payload["pipeline_rejection_sample_release"]
    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["release_candidate_ready"] is False
    assert payload["recommendation"] == "fix_release_blockers"
    assert evidence["ready"] is False
    assert evidence["check"] is None
    assert evidence["status"] == "failed"
    assert evidence["required_count"] == 1
    assert evidence["failed_count"] == 1
    assert evidence["failed_items"][0]["status"] == "missing_required"
    assert evidence["failed_items"][0]["required_maps"] == [
        "low_rejection",
        "high_rejection",
    ]
    assert checks["pipeline_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["pipeline_sample_accounting_closure_passed"]["passed"] is True


def test_release_promotion_decision_cli_writes_outputs_and_strict_status(tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"
    publication = tmp_path / "publication_audit.json"
    out = tmp_path / "decision.json"
    markdown = tmp_path / "decision.md"
    _write_acceptance(acceptance)
    _write_publication_audit(publication)

    assert (
        main(
            [
                "release-promotion-decision",
                "--acceptance-audit",
                str(acceptance),
                "--stack-engine-publication-audit",
                str(publication),
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
    assert "Warp Quality Handoff" in markdown_text
    assert "Resident Registration Fastpath Handoff" in markdown_text
    assert "StackEngine Publication Runtime Default" in markdown_text
    assert "Quality compare ready" in markdown_text

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
