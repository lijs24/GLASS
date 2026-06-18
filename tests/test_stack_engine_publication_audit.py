from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.stack_engine_publication_audit import (
    build_stack_engine_publication_audit,
)


def _stack_fields(*, ready: bool = True, gap_count: int = 0) -> dict[str, object]:
    chain_ready = ready and gap_count == 0
    recommendation = (
        "stack_engine_default_ready"
        if chain_ready
        else "stack_engine_contract_gaps_remain"
    )
    return {
        "status": "passed" if chain_ready else "failed",
        "passed": chain_ready,
        "ready": chain_ready,
        "scope": "all",
        "phase2_check_passed": chain_ready,
        "adoption_recommendation": recommendation,
        "default_promotion_recommendation": recommendation,
        "gap_count": gap_count,
        "blocker_count": 0 if chain_ready else 1,
    }


def _write_chain(
    tmp_path: Path,
    *,
    source_ready: bool = True,
    matrix_ready: bool = True,
    matrix_gap_count: int = 0,
    resident_winsorized_ready: bool = True,
    phase2_resident_winsorized_ready: bool | None = None,
    resident_result_contract_ready: bool = True,
    phase2_resident_result_contract_ready: bool | None = None,
    include_resident_result_contract: bool = True,
    include_phase2_resident_result_contract: bool = True,
    integration_engine_policy_ready: bool = True,
    phase2_integration_engine_policy_ready: bool | None = None,
    include_integration_engine_policy: bool = True,
    include_phase2_integration_engine_policy: bool = True,
    runtime_default_ready: bool = True,
    phase2_runtime_default_ready: bool | None = None,
    include_runtime_default: bool = True,
    include_phase2_runtime_default: bool = True,
    direct_runtime_ready: bool = True,
    phase2_direct_runtime_ready: bool | None = None,
    include_direct_runtime: bool = True,
    include_phase2_direct_runtime: bool = True,
    publication_audit_ready: bool = True,
    phase2_publication_audit_ready: bool | None = None,
    include_publication_audit: bool = True,
    include_phase2_publication_audit: bool = True,
    quality_metrics_compare_ready: bool = True,
    phase2_quality_metrics_compare_ready: bool | None = None,
    include_quality_metrics_compare: bool = True,
    include_phase2_quality_metrics_compare: bool = True,
    release_quality_publication_guard_ready: bool = True,
    phase2_release_quality_publication_guard_ready: bool | None = None,
    include_release_quality_publication_guard: bool = True,
    include_phase2_release_quality_publication_guard: bool = True,
) -> dict[str, Path]:
    source_fields = _stack_fields(ready=source_ready)
    matrix_fields = _stack_fields(ready=matrix_ready, gap_count=matrix_gap_count)
    phase2_winsorized_ready = (
        resident_winsorized_ready
        if phase2_resident_winsorized_ready is None
        else phase2_resident_winsorized_ready
    )
    phase2_result_contract_ready = (
        resident_result_contract_ready
        if phase2_resident_result_contract_ready is None
        else phase2_resident_result_contract_ready
    )
    phase2_engine_policy_ready = (
        integration_engine_policy_ready
        if phase2_integration_engine_policy_ready is None
        else phase2_integration_engine_policy_ready
    )
    phase2_runtime_ready = (
        runtime_default_ready
        if phase2_runtime_default_ready is None
        else phase2_runtime_default_ready
    )
    phase2_direct_ready = (
        direct_runtime_ready
        if phase2_direct_runtime_ready is None
        else phase2_direct_runtime_ready
    )
    phase2_publication_ready = (
        publication_audit_ready
        if phase2_publication_audit_ready is None
        else phase2_publication_audit_ready
    )
    phase2_quality_compare_ready = (
        quality_metrics_compare_ready
        if phase2_quality_metrics_compare_ready is None
        else phase2_quality_metrics_compare_ready
    )
    phase2_release_quality_guard_ready = (
        release_quality_publication_guard_ready
        if phase2_release_quality_publication_guard_ready is None
        else phase2_release_quality_publication_guard_ready
    )
    resident_status = "passed" if resident_winsorized_ready else "failed"
    phase2_resident_status = "passed" if phase2_winsorized_ready else "failed"
    resident_result_status = "passed" if resident_result_contract_ready else "failed"
    phase2_resident_result_status = (
        "passed" if phase2_result_contract_ready else "failed"
    )
    engine_policy_status = "passed" if integration_engine_policy_ready else "failed"
    phase2_engine_policy_status = (
        "passed" if phase2_engine_policy_ready else "failed"
    )
    runtime_default_status = "passed" if runtime_default_ready else "failed"
    phase2_runtime_status = "passed" if phase2_runtime_ready else "failed"
    direct_runtime_source = (
        "explicit_resident_artifacts_json"
        if direct_runtime_ready
        else "phase2_status_handoff"
    )
    phase2_direct_runtime_source = (
        "explicit_resident_artifacts_json"
        if phase2_direct_ready
        else "phase2_status_handoff"
    )
    publication_audit_status = "passed" if publication_audit_ready else "failed"
    phase2_publication_audit_status = (
        "passed" if phase2_publication_ready else "failed"
    )
    quality_compare_status = "passed" if quality_metrics_compare_ready else "failed"
    phase2_quality_compare_status = (
        "passed" if phase2_quality_compare_ready else "failed"
    )
    release_quality_guard_raw_status = (
        "passed" if release_quality_publication_guard_ready else "failed"
    )
    release_quality_guard_phase2_status = (
        "passed"
        if release_quality_publication_guard_ready
        else "attention_required"
    )
    phase2_release_quality_guard_raw_status = (
        "passed" if phase2_release_quality_guard_ready else "failed"
    )
    phase2_release_quality_guard_phase2_status = (
        "passed" if phase2_release_quality_guard_ready else "attention_required"
    )
    phase2_status_ready = (
        source_fields["ready"]
        and matrix_fields["ready"]
        and phase2_winsorized_ready
        and (
            phase2_result_contract_ready
            if include_phase2_resident_result_contract
            else True
        )
        and (phase2_engine_policy_ready if include_phase2_integration_engine_policy else True)
        and (phase2_runtime_ready if include_phase2_runtime_default else True)
        and (phase2_direct_ready if include_phase2_direct_runtime else True)
        and (phase2_publication_ready if include_phase2_publication_audit else True)
        and (
            phase2_quality_compare_ready
            if include_phase2_quality_metrics_compare
            else True
        )
        and (
            phase2_release_quality_guard_ready
            if include_phase2_release_quality_publication_guard
            else True
        )
    )
    paths = {
        "stack": tmp_path / "stack_engine_contract.json",
        "phase2": tmp_path / "phase2_status.json",
        "promotion": tmp_path / "default_promotion.json",
        "matrix": tmp_path / "matrix.json",
        "github": tmp_path / "github_plan.json",
        "preflight": tmp_path / "publish_preflight.json",
    }
    write_json(
        paths["stack"],
        {
            "audit_type": "stack_engine_default_contract",
            "status": source_fields["status"],
            "passed": source_fields["passed"],
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "adoption": {
                "recommendation": source_fields["adoption_recommendation"],
                "phase2_stack_engine_default_gap_count": source_fields["gap_count"],
            },
            "default_promotion": {
                "ready": source_fields["ready"],
                "status": "ready" if source_fields["ready"] else "blocked",
                "recommendation": source_fields["default_promotion_recommendation"],
                "phase2_stack_engine_default_gap_count": source_fields["gap_count"],
                "blocker_count": source_fields["blocker_count"],
                "blockers": []
                if source_fields["ready"]
                else [{"name": "phase2_stack_engine_default_gaps"}],
            },
        },
    )
    write_json(
        paths["phase2"],
        {
            "artifact_type": "glass_phase2_status",
            "status": "green" if phase2_status_ready else "attention_required",
            "passed": phase2_status_ready,
            "stack_engine_contract": {
                "status": source_fields["status"],
                "passed": source_fields["passed"],
                "scope": "all",
                "expected_integration_engine": "stack_engine_cpu",
                "default_promotion_ready": source_fields["ready"],
                "default_promotion_status": "ready"
                if source_fields["ready"]
                else "blocked",
                "adoption_recommendation": source_fields["adoption_recommendation"],
                "default_promotion_recommendation": source_fields[
                    "default_promotion_recommendation"
                ],
                "adoption_phase2_stack_engine_default_gap_count": source_fields[
                    "gap_count"
                ],
                "default_promotion_phase2_stack_engine_default_gap_count": (
                    source_fields["gap_count"]
                ),
                "default_promotion_blocker_count": source_fields["blocker_count"],
            },
            "publish_preflight": {
                "status": "publish_preflight_ready"
                if matrix_fields["ready"]
                else "blocked",
                "github_plan_phase2_stack_engine_contract_status": source_fields[
                    "status"
                ],
                "github_plan_matrix_stack_engine_contract_status": matrix_fields[
                    "status"
                ],
                "matrix_stack_engine_contract_status": matrix_fields["status"],
                "default_promotion_stack_engine_contract_status": source_fields[
                    "status"
                ],
                "matrix_stack_engine_contract_default_gap_count": matrix_fields[
                    "gap_count"
                ],
                "default_promotion_stack_engine_contract_default_gap_count": (
                    source_fields["gap_count"]
                ),
                "github_plan_phase2_stack_engine_default_contract_ready": (
                    source_fields["ready"]
                ),
                "github_plan_matrix_stack_engine_contract_ready": matrix_fields[
                    "ready"
                ],
                "github_plan_stack_engine_contract_agreement_passed": (
                    source_fields["ready"] and matrix_fields["ready"]
                ),
                "matrix_stack_engine_contract_ready": matrix_fields["ready"],
                "default_promotion_stack_engine_contract_ready": source_fields["ready"],
                "github_plan_matrix_stack_engine_contract_matches_matrix": True,
                "matrix_stack_engine_contract_matches_default_promotion": (
                    source_fields["ready"] and matrix_fields["ready"]
                ),
                "matrix_resident_winsorized_sweep_status": phase2_resident_status,
                "matrix_resident_winsorized_sweep_required_frame_count": 200,
                "matrix_resident_winsorized_sweep_required_frame_count_passed": (
                    phase2_winsorized_ready
                ),
                "matrix_resident_winsorized_sweep_check_count": 27,
                "default_promotion_resident_winsorized_sweep_status": (
                    phase2_resident_status
                ),
                "default_promotion_resident_winsorized_sweep_required_frame_count": (
                    200
                ),
                "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
                    phase2_winsorized_ready
                ),
                "default_promotion_resident_winsorized_sweep_check_count": 27,
                "matrix_resident_winsorized_sweep_audit_passed": (
                    phase2_winsorized_ready
                ),
                "matrix_resident_winsorized_required_frame_passed": (
                    phase2_winsorized_ready
                ),
                "matrix_resident_winsorized_sweep_check_count_passed": (
                    phase2_winsorized_ready
                ),
                "default_promotion_resident_winsorized_sweep_audit_passed": (
                    phase2_winsorized_ready
                ),
                "default_promotion_resident_winsorized_required_frame_passed": (
                    phase2_winsorized_ready
                ),
                "default_promotion_resident_winsorized_sweep_matches_matrix": (
                    phase2_winsorized_ready
                ),
            },
            "checks": [
                {
                    "name": "stack_engine_default_contract_ready",
                    "passed": source_fields["ready"],
                },
                {
                    "name": "windows_publish_preflight_stack_engine_default_contract_ready",
                    "passed": source_fields["ready"] and matrix_fields["ready"],
                },
                {
                    "name": "windows_publish_preflight_resident_winsorized_sweep_passed",
                    "passed": phase2_winsorized_ready,
                },
            ],
        },
    )
    phase2_payload = read_json(paths["phase2"])
    if include_phase2_resident_result_contract:
        failed_count = 0 if phase2_result_contract_ready else 1
        phase2_payload["publish_preflight"].update(
            {
                "github_plan_matrix_resident_result_contract_ready": (
                    phase2_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_status": (
                    phase2_resident_result_status
                ),
                "github_plan_matrix_resident_result_contract_phase2_check_passed": (
                    phase2_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_required_count": 1,
                "github_plan_matrix_resident_result_contract_failed_count": (
                    failed_count
                ),
                "matrix_resident_result_contract_ready": (
                    phase2_result_contract_ready
                ),
                "matrix_resident_result_contract_status": (
                    phase2_resident_result_status
                ),
                "matrix_resident_result_contract_phase2_check_passed": (
                    phase2_result_contract_ready
                ),
                "matrix_resident_result_contract_required_count": 1,
                "matrix_resident_result_contract_failed_count": failed_count,
                "default_promotion_resident_result_contract_ready": (
                    phase2_result_contract_ready
                ),
                "default_promotion_resident_result_contract_status": (
                    phase2_resident_result_status
                ),
                "default_promotion_resident_result_contract_phase2_check_passed": (
                    phase2_result_contract_ready
                ),
                "default_promotion_resident_result_contract_required_count": 1,
                "default_promotion_resident_result_contract_failed_count": (
                    failed_count
                ),
                "github_plan_matrix_resident_result_contract_handoff_passed": (
                    phase2_result_contract_ready
                ),
                "matrix_resident_result_contract_handoff_passed": (
                    phase2_result_contract_ready
                ),
                "default_promotion_resident_result_contract_handoff_passed": (
                    phase2_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_matches_matrix": (
                    phase2_result_contract_ready
                ),
                "matrix_resident_result_contract_matches_default_promotion": (
                    phase2_result_contract_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_resident_result_contract_handoff_passed",
                "passed": phase2_result_contract_ready,
            }
        )
    if include_phase2_integration_engine_policy:
        phase2_payload["publish_preflight"].update(
            {
                "matrix_integration_engine_policy_ready": phase2_engine_policy_ready,
                "matrix_acceptance_integration_engine_policy_status": (
                    phase2_engine_policy_status
                ),
                "matrix_pipeline_integration_engine_policy_status": (
                    phase2_engine_policy_status
                ),
                "default_promotion_integration_engine_policy_ready": (
                    phase2_engine_policy_ready
                ),
                "default_promotion_acceptance_integration_engine_policy_status": (
                    phase2_engine_policy_status
                ),
                "default_promotion_pipeline_integration_engine_policy_status": (
                    phase2_engine_policy_status
                ),
                "windows_release_matrix_acceptance_integration_engine_policy_passed": (
                    phase2_engine_policy_ready
                ),
                "windows_release_matrix_pipeline_integration_engine_policy_passed": (
                    phase2_engine_policy_ready
                ),
                "default_promotion_acceptance_integration_engine_policy_passed": (
                    phase2_engine_policy_ready
                ),
                "default_promotion_pipeline_integration_engine_policy_passed": (
                    phase2_engine_policy_ready
                ),
                "matrix_integration_engine_policy_matches_default_promotion": (
                    phase2_engine_policy_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_integration_engine_policy_passed",
                "passed": phase2_engine_policy_ready,
            }
        )
    if include_phase2_runtime_default:
        phase2_payload["publish_preflight"].update(
            {
                "matrix_stack_engine_runtime_default_ready": phase2_runtime_ready,
                "matrix_acceptance_stack_engine_runtime_default_status": (
                    phase2_runtime_status
                ),
                "matrix_pipeline_stack_engine_runtime_default_status": (
                    phase2_runtime_status
                ),
                "matrix_stack_engine_runtime_default_acceptance_legacy_master_count": (
                    0 if phase2_runtime_ready else 1
                ),
                "matrix_stack_engine_runtime_default_pipeline_failed_output_count": (
                    0 if phase2_runtime_ready else 1
                ),
                "default_promotion_stack_engine_runtime_default_ready": (
                    phase2_runtime_ready
                ),
                "default_promotion_acceptance_stack_engine_runtime_default_status": (
                    phase2_runtime_status
                ),
                "default_promotion_pipeline_stack_engine_runtime_default_status": (
                    phase2_runtime_status
                ),
                "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count": (
                    0 if phase2_runtime_ready else 1
                ),
                "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count": (
                    0 if phase2_runtime_ready else 1
                ),
                "windows_release_matrix_acceptance_stack_engine_runtime_default_passed": (
                    phase2_runtime_ready
                ),
                "windows_release_matrix_pipeline_stack_engine_runtime_default_passed": (
                    phase2_runtime_ready
                ),
                "default_promotion_acceptance_stack_engine_runtime_default_passed": (
                    phase2_runtime_ready
                ),
                "default_promotion_pipeline_stack_engine_runtime_default_passed": (
                    phase2_runtime_ready
                ),
                "matrix_stack_engine_runtime_default_matches_default_promotion": (
                    phase2_runtime_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_stack_engine_runtime_default_passed",
                "passed": phase2_runtime_ready,
            }
        )
    if include_phase2_direct_runtime:
        phase2_payload["publish_preflight"].update(
            {
                "matrix_direct_runtime_evidence_ready": phase2_direct_ready,
                "matrix_direct_runtime_acceptance_source": phase2_direct_runtime_source,
                "matrix_direct_runtime_acceptance_check_count": (
                    24 if phase2_direct_ready else 0
                ),
                "matrix_direct_runtime_pipeline_calibration_source": (
                    "resident_artifacts_json_fallback"
                ),
                "matrix_direct_runtime_pipeline_resident_lights": (
                    200 if phase2_direct_ready else 0
                ),
                "default_promotion_direct_runtime_evidence_ready": (
                    phase2_direct_ready
                ),
                "default_promotion_direct_runtime_acceptance_source": (
                    phase2_direct_runtime_source
                ),
                "default_promotion_direct_runtime_acceptance_check_count": (
                    24 if phase2_direct_ready else 0
                ),
                "default_promotion_direct_runtime_pipeline_calibration_source": (
                    "resident_artifacts_json_fallback"
                ),
                "default_promotion_direct_runtime_pipeline_resident_lights": (
                    200 if phase2_direct_ready else 0
                ),
                "windows_release_matrix_direct_acceptance_fastpath_evidence": (
                    phase2_direct_ready
                ),
                "windows_release_matrix_direct_pipeline_calibration_evidence": (
                    phase2_direct_ready
                ),
                "default_promotion_direct_acceptance_fastpath_evidence": (
                    phase2_direct_ready
                ),
                "default_promotion_direct_pipeline_calibration_evidence": (
                    phase2_direct_ready
                ),
                "matrix_direct_runtime_evidence_matches_default_promotion": (
                    phase2_direct_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_direct_runtime_evidence_passed",
                "passed": phase2_direct_ready,
            }
        )
    if include_phase2_publication_audit:
        phase2_payload["publish_preflight"].update(
            {
                "matrix_stack_engine_publication_audit_status": (
                    phase2_publication_audit_status
                ),
                "matrix_stack_engine_publication_audit_ready": (
                    phase2_publication_ready
                ),
                "matrix_stack_engine_publication_policy_agreement": (
                    phase2_publication_ready
                ),
                "matrix_stack_engine_publication_resident_winsorized_agreement": (
                    phase2_publication_ready
                ),
                "default_promotion_stack_engine_publication_audit_status": (
                    phase2_publication_audit_status
                ),
                "default_promotion_stack_engine_publication_audit_ready": (
                    phase2_publication_ready
                ),
                "default_promotion_stack_engine_publication_policy_agreement": (
                    phase2_publication_ready
                ),
                "default_promotion_stack_engine_publication_resident_winsorized_agreement": (
                    phase2_publication_ready
                ),
                "matrix_stack_engine_publication_audit_passed": (
                    phase2_publication_ready
                ),
                "matrix_stack_engine_publication_policy_chain_passed": (
                    phase2_publication_ready
                ),
                "matrix_stack_engine_publication_resident_winsorized_chain_passed": (
                    phase2_publication_ready
                ),
                "default_promotion_stack_engine_publication_audit_passed": (
                    phase2_publication_ready
                ),
                "default_promotion_stack_engine_publication_policy_chain_passed": (
                    phase2_publication_ready
                ),
                "default_promotion_stack_engine_publication_resident_winsorized_chain_passed": (
                    phase2_publication_ready
                ),
                "matrix_stack_engine_publication_audit_matches_default_promotion": (
                    phase2_publication_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_stack_engine_publication_audit_passed",
                "passed": phase2_publication_ready,
            }
        )
    if include_phase2_quality_metrics_compare:
        failed_count = 0 if phase2_quality_compare_ready else 1
        phase2_payload["publish_preflight"].update(
            {
                "matrix_quality_metrics_compare_present": True,
                "matrix_quality_metrics_compare_ready": phase2_quality_compare_ready,
                "matrix_quality_metrics_compare_status": phase2_quality_compare_status,
                "matrix_quality_metrics_compare_failed_check_count": failed_count,
                "default_promotion_quality_metrics_compare_present": True,
                "default_promotion_quality_metrics_compare_ready": (
                    phase2_quality_compare_ready
                ),
                "default_promotion_quality_metrics_compare_status": (
                    phase2_quality_compare_status
                ),
                "default_promotion_quality_metrics_compare_failed_check_count": (
                    failed_count
                ),
                "windows_release_matrix_quality_metrics_compare_handoff_passed": (
                    phase2_quality_compare_ready
                ),
                "default_promotion_quality_metrics_compare_handoff_passed": (
                    phase2_quality_compare_ready
                ),
                "matrix_quality_metrics_compare_matches_default_promotion": (
                    phase2_quality_compare_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_quality_metrics_compare_passed",
                "passed": phase2_quality_compare_ready,
            }
        )
    if include_phase2_release_quality_publication_guard:
        phase2_payload["publish_preflight"].update(
            {
                "matrix_release_quality_publication_guard_present": True,
                "matrix_release_quality_publication_guard_ready": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_release_quality_publication_guard_check_passed": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_release_quality_publication_guard_layers_ready": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_release_quality_publication_guard_raw_status": (
                    phase2_release_quality_guard_raw_status
                ),
                "matrix_release_quality_publication_guard_phase2_status": (
                    phase2_release_quality_guard_phase2_status
                ),
                "matrix_default_promotion_release_quality_publication_guard_ready": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_default_promotion_release_quality_publication_guard_raw_status": (
                    phase2_release_quality_guard_raw_status
                ),
                "matrix_default_promotion_release_quality_publication_guard_phase2_status": (
                    phase2_release_quality_guard_phase2_status
                ),
                "default_promotion_release_quality_publication_guard_present": True,
                "default_promotion_release_quality_publication_guard_ready": (
                    phase2_release_quality_guard_ready
                ),
                "default_promotion_release_quality_publication_guard_check_passed": (
                    phase2_release_quality_guard_ready
                ),
                "default_promotion_release_quality_publication_guard_layers_ready": (
                    phase2_release_quality_guard_ready
                ),
                "default_promotion_release_quality_publication_guard_raw_status": (
                    phase2_release_quality_guard_raw_status
                ),
                "default_promotion_release_quality_publication_guard_phase2_status": (
                    phase2_release_quality_guard_phase2_status
                ),
                "matrix_release_decision_quality_compare_publication_guard_passed": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed": (
                    phase2_release_quality_guard_ready
                ),
                "default_promotion_release_decision_quality_compare_publication_guard_passed": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_release_decision_quality_publication_guard_matches_default_promotion": (
                    phase2_release_quality_guard_ready
                ),
                "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest": (
                    phase2_release_quality_guard_ready
                ),
            }
        )
        phase2_payload["checks"].append(
            {
                "name": "windows_publish_preflight_release_quality_publication_guard_passed",
                "passed": phase2_release_quality_guard_ready,
            }
        )
    write_json(paths["phase2"], phase2_payload)
    write_json(
        paths["promotion"],
        {
            "artifact_type": "default_promotion_manifest",
            "stack_engine_contract": {
                "present": True,
                "ready": source_fields["ready"],
                "phase2_check_passed": source_fields["ready"],
                "status": source_fields["status"],
                "passed": source_fields["passed"],
                "scope": "all",
                "adoption_recommendation": source_fields["adoption_recommendation"],
                "default_promotion_phase2_stack_engine_default_gap_count": (
                    source_fields["gap_count"]
                ),
                "default_promotion_blocker_count": source_fields["blocker_count"],
                "default_promotion_blockers": [],
            },
        },
    )
    write_json(
        paths["matrix"],
        {
            "artifact_type": "windows_release_matrix",
            "default_promotion_manifest": {
                "stack_engine_contract_present": True,
                "stack_engine_contract_ready": matrix_fields["ready"],
                "stack_engine_contract_phase2_check_passed": matrix_fields["ready"],
                "stack_engine_contract_status": matrix_fields["status"],
                "stack_engine_contract_passed": matrix_fields["passed"],
                "stack_engine_contract_scope": "all",
                "stack_engine_contract_adoption_recommendation": matrix_fields[
                    "adoption_recommendation"
                ],
                "stack_engine_contract_default_gap_count": matrix_fields["gap_count"],
                "stack_engine_contract_blocker_count": matrix_fields["blocker_count"],
                "stack_engine_contract_blockers": [],
            },
        },
    )
    write_json(
        paths["github"],
        {
            "artifact_type": "windows_github_release_plan",
            "status": "release_plan_ready" if matrix_fields["ready"] else "blocked",
            "passed": matrix_fields["ready"],
            "publication_ready": matrix_fields["ready"],
            "phase2": {
                "status": {
                    "stack_engine_default_contract_status": source_fields["status"],
                    "stack_engine_default_contract_default_gap_count": source_fields[
                        "gap_count"
                    ],
                    "stack_engine_default_contract_blocker_count": source_fields[
                        "blocker_count"
                    ],
                }
            },
            "release_matrix": {
                "stack_engine_contract_status": matrix_fields["status"],
                "stack_engine_contract_ready": matrix_fields["ready"],
                "stack_engine_contract_default_gap_count": matrix_fields["gap_count"],
                "stack_engine_contract_blocker_count": matrix_fields["blocker_count"],
            },
            "checks": [
                {
                    "name": "phase2_stack_engine_default_contract_ready",
                    "passed": source_fields["ready"],
                },
                {
                    "name": "windows_release_matrix_stack_engine_contract_ready",
                    "passed": matrix_fields["ready"],
                },
                {
                    "name": "phase2_release_matrix_stack_engine_contract_agree",
                    "passed": source_fields["ready"] and matrix_fields["ready"],
                },
            ],
        },
    )
    write_json(
        paths["preflight"],
        {
            "artifact_type": "windows_publish_preflight",
            "status": "publish_preflight_ready"
            if (
                matrix_fields["ready"]
                and resident_winsorized_ready
                and (
                    resident_result_contract_ready
                    if include_resident_result_contract
                    else True
                )
                and (
                    integration_engine_policy_ready
                    if include_integration_engine_policy
                    else True
                )
                and (runtime_default_ready if include_runtime_default else True)
                and (direct_runtime_ready if include_direct_runtime else True)
                and (publication_audit_ready if include_publication_audit else True)
                and (
                    quality_metrics_compare_ready
                    if include_quality_metrics_compare
                    else True
                )
                and (
                    release_quality_publication_guard_ready
                    if include_release_quality_publication_guard
                    else True
                )
            )
            else "blocked",
            "passed": (
                matrix_fields["ready"]
                and resident_winsorized_ready
                and (
                    resident_result_contract_ready
                    if include_resident_result_contract
                    else True
                )
                and (
                    integration_engine_policy_ready
                    if include_integration_engine_policy
                    else True
                )
                and (runtime_default_ready if include_runtime_default else True)
                and (direct_runtime_ready if include_direct_runtime else True)
                and (publication_audit_ready if include_publication_audit else True)
                and (
                    quality_metrics_compare_ready
                    if include_quality_metrics_compare
                    else True
                )
                and (
                    release_quality_publication_guard_ready
                    if include_release_quality_publication_guard
                    else True
                )
            ),
            "summary": {
                "github_plan_phase2_stack_engine_contract_status": source_fields[
                    "status"
                ],
                "github_plan_matrix_stack_engine_contract_status": matrix_fields[
                    "status"
                ],
                "matrix_stack_engine_contract_status": matrix_fields["status"],
                "default_promotion_stack_engine_contract_status": source_fields[
                    "status"
                ],
                "matrix_stack_engine_contract_default_gap_count": matrix_fields[
                    "gap_count"
                ],
                "default_promotion_stack_engine_contract_default_gap_count": (
                    source_fields["gap_count"]
                ),
                "matrix_stack_engine_runtime_default_ready": runtime_default_ready,
                "matrix_acceptance_stack_engine_runtime_default_status": (
                    runtime_default_status
                ),
                "matrix_pipeline_stack_engine_runtime_default_status": (
                    runtime_default_status
                ),
                "matrix_stack_engine_runtime_default_acceptance_legacy_master_count": (
                    0 if runtime_default_ready else 1
                ),
                "matrix_stack_engine_runtime_default_pipeline_failed_output_count": (
                    0 if runtime_default_ready else 1
                ),
                "default_promotion_stack_engine_runtime_default_ready": (
                    runtime_default_ready
                ),
                "default_promotion_acceptance_stack_engine_runtime_default_status": (
                    runtime_default_status
                ),
                "default_promotion_pipeline_stack_engine_runtime_default_status": (
                    runtime_default_status
                ),
                "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count": (
                    0 if runtime_default_ready else 1
                ),
                "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count": (
                    0 if runtime_default_ready else 1
                ),
                "matrix_direct_runtime_evidence_ready": direct_runtime_ready,
                "matrix_direct_runtime_acceptance_source": direct_runtime_source,
                "matrix_direct_runtime_acceptance_check_count": (
                    24 if direct_runtime_ready else 0
                ),
                "matrix_direct_runtime_pipeline_calibration_source": (
                    "resident_artifacts_json_fallback"
                ),
                "matrix_direct_runtime_pipeline_resident_lights": (
                    200 if direct_runtime_ready else 0
                ),
                "default_promotion_direct_runtime_evidence_ready": (
                    direct_runtime_ready
                ),
                "default_promotion_direct_runtime_acceptance_source": (
                    direct_runtime_source
                ),
                "default_promotion_direct_runtime_acceptance_check_count": (
                    24 if direct_runtime_ready else 0
                ),
                "default_promotion_direct_runtime_pipeline_calibration_source": (
                    "resident_artifacts_json_fallback"
                ),
                "default_promotion_direct_runtime_pipeline_resident_lights": (
                    200 if direct_runtime_ready else 0
                ),
                "matrix_resident_winsorized_sweep_status": resident_status,
                "matrix_resident_winsorized_sweep_required_frame_count": 200,
                "matrix_resident_winsorized_sweep_required_frame_count_passed": (
                    resident_winsorized_ready
                ),
                "matrix_resident_winsorized_sweep_check_count": 27,
                "default_promotion_resident_winsorized_sweep_status": resident_status,
                "default_promotion_resident_winsorized_sweep_required_frame_count": 200,
                "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
                    resident_winsorized_ready
                ),
                "default_promotion_resident_winsorized_sweep_check_count": 27,
            },
            "checks": [
                {
                    "name": "github_plan_phase2_stack_engine_default_contract_ready",
                    "passed": source_fields["ready"],
                },
                {
                    "name": "github_plan_matrix_stack_engine_contract_ready",
                    "passed": matrix_fields["ready"],
                },
                {
                    "name": "github_plan_stack_engine_contract_agreement_passed",
                    "passed": source_fields["ready"] and matrix_fields["ready"],
                },
                {
                    "name": "matrix_stack_engine_contract_ready",
                    "passed": matrix_fields["ready"],
                },
                {
                    "name": "default_promotion_stack_engine_contract_ready",
                    "passed": source_fields["ready"],
                },
                {
                    "name": "github_plan_matrix_stack_engine_contract_matches_matrix",
                    "passed": True,
                },
                {
                    "name": "matrix_stack_engine_contract_matches_default_promotion",
                    "passed": source_fields["ready"] and matrix_fields["ready"],
                },
                {
                    "name": "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
                    "passed": runtime_default_ready,
                },
                {
                    "name": "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
                    "passed": runtime_default_ready,
                },
                {
                    "name": "default_promotion_acceptance_stack_engine_runtime_default_passed",
                    "passed": runtime_default_ready,
                },
                {
                    "name": "default_promotion_pipeline_stack_engine_runtime_default_passed",
                    "passed": runtime_default_ready,
                },
                {
                    "name": "matrix_stack_engine_runtime_default_matches_default_promotion",
                    "passed": runtime_default_ready,
                },
                {
                    "name": "windows_release_matrix_direct_acceptance_fastpath_evidence",
                    "passed": direct_runtime_ready,
                },
                {
                    "name": "windows_release_matrix_direct_pipeline_calibration_evidence",
                    "passed": direct_runtime_ready,
                },
                {
                    "name": "default_promotion_direct_acceptance_fastpath_evidence",
                    "passed": direct_runtime_ready,
                },
                {
                    "name": "default_promotion_direct_pipeline_calibration_evidence",
                    "passed": direct_runtime_ready,
                },
                {
                    "name": "matrix_direct_runtime_evidence_matches_default_promotion",
                    "passed": direct_runtime_ready,
                },
                {
                    "name": "matrix_resident_winsorized_sweep_audit_passed",
                    "passed": resident_winsorized_ready,
                },
                {
                    "name": "matrix_resident_winsorized_required_frame_passed",
                    "passed": resident_winsorized_ready,
                },
                {
                    "name": "matrix_resident_winsorized_sweep_check_count",
                    "passed": resident_winsorized_ready,
                },
                {
                    "name": "default_promotion_resident_winsorized_sweep_audit_passed",
                    "passed": resident_winsorized_ready,
                },
                {
                    "name": "default_promotion_resident_winsorized_required_frame_passed",
                    "passed": resident_winsorized_ready,
                },
                {
                    "name": "default_promotion_resident_winsorized_sweep_matches_matrix",
                    "passed": resident_winsorized_ready,
                },
            ],
        },
    )
    preflight_payload = read_json(paths["preflight"])
    if include_resident_result_contract:
        failed_count = 0 if resident_result_contract_ready else 1
        preflight_payload["summary"].update(
            {
                "github_plan_matrix_resident_result_contract_ready": (
                    resident_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_status": (
                    resident_result_status
                ),
                "github_plan_matrix_resident_result_contract_phase2_check_passed": (
                    resident_result_contract_ready
                ),
                "github_plan_matrix_resident_result_contract_required_count": 1,
                "github_plan_matrix_resident_result_contract_failed_count": (
                    failed_count
                ),
                "matrix_resident_result_contract_ready": (
                    resident_result_contract_ready
                ),
                "matrix_resident_result_contract_status": resident_result_status,
                "matrix_resident_result_contract_phase2_check_passed": (
                    resident_result_contract_ready
                ),
                "matrix_resident_result_contract_required_count": 1,
                "matrix_resident_result_contract_failed_count": failed_count,
                "default_promotion_resident_result_contract_ready": (
                    resident_result_contract_ready
                ),
                "default_promotion_resident_result_contract_status": (
                    resident_result_status
                ),
                "default_promotion_resident_result_contract_phase2_check_passed": (
                    resident_result_contract_ready
                ),
                "default_promotion_resident_result_contract_required_count": 1,
                "default_promotion_resident_result_contract_failed_count": (
                    failed_count
                ),
            }
        )
        preflight_payload["checks"].extend(
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
        write_json(paths["preflight"], preflight_payload)
    if not include_runtime_default:
        for key in (
            "matrix_stack_engine_runtime_default_ready",
            "matrix_acceptance_stack_engine_runtime_default_status",
            "matrix_pipeline_stack_engine_runtime_default_status",
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count",
            "matrix_stack_engine_runtime_default_pipeline_failed_output_count",
            "default_promotion_stack_engine_runtime_default_ready",
            "default_promotion_acceptance_stack_engine_runtime_default_status",
            "default_promotion_pipeline_stack_engine_runtime_default_status",
            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count",
            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count",
        ):
            preflight_payload["summary"].pop(key, None)
        preflight_payload["checks"] = [
            item
            for item in preflight_payload["checks"]
            if item.get("name")
            not in {
                "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
                "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
                "default_promotion_acceptance_stack_engine_runtime_default_passed",
                "default_promotion_pipeline_stack_engine_runtime_default_passed",
                "matrix_stack_engine_runtime_default_matches_default_promotion",
            }
        ]
        write_json(paths["preflight"], preflight_payload)
    if not include_direct_runtime:
        for key in (
            "matrix_direct_runtime_evidence_ready",
            "matrix_direct_runtime_acceptance_source",
            "matrix_direct_runtime_acceptance_check_count",
            "matrix_direct_runtime_pipeline_calibration_source",
            "matrix_direct_runtime_pipeline_resident_lights",
            "default_promotion_direct_runtime_evidence_ready",
            "default_promotion_direct_runtime_acceptance_source",
            "default_promotion_direct_runtime_acceptance_check_count",
            "default_promotion_direct_runtime_pipeline_calibration_source",
            "default_promotion_direct_runtime_pipeline_resident_lights",
        ):
            preflight_payload["summary"].pop(key, None)
        preflight_payload["checks"] = [
            item
            for item in preflight_payload["checks"]
            if item.get("name")
            not in {
                "windows_release_matrix_direct_acceptance_fastpath_evidence",
                "windows_release_matrix_direct_pipeline_calibration_evidence",
                "default_promotion_direct_acceptance_fastpath_evidence",
                "default_promotion_direct_pipeline_calibration_evidence",
                "matrix_direct_runtime_evidence_matches_default_promotion",
            }
        ]
        write_json(paths["preflight"], preflight_payload)
    if include_integration_engine_policy:
        preflight_payload["summary"].update(
            {
                "matrix_integration_engine_policy_ready": integration_engine_policy_ready,
                "matrix_acceptance_integration_engine_policy_status": (
                    engine_policy_status
                ),
                "matrix_pipeline_integration_engine_policy_status": (
                    engine_policy_status
                ),
                "default_promotion_integration_engine_policy_ready": (
                    integration_engine_policy_ready
                ),
                "default_promotion_acceptance_integration_engine_policy_status": (
                    engine_policy_status
                ),
                "default_promotion_pipeline_integration_engine_policy_status": (
                    engine_policy_status
                ),
            }
        )
        preflight_payload["checks"].extend(
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
        write_json(paths["preflight"], preflight_payload)
    if include_publication_audit:
        preflight_payload["summary"].update(
            {
                "matrix_stack_engine_publication_audit_status": (
                    publication_audit_status
                ),
                "matrix_stack_engine_publication_audit_ready": (
                    publication_audit_ready
                ),
                "matrix_stack_engine_publication_policy_agreement": (
                    publication_audit_ready
                ),
                "matrix_stack_engine_publication_resident_winsorized_agreement": (
                    publication_audit_ready
                ),
                "default_promotion_stack_engine_publication_audit_status": (
                    publication_audit_status
                ),
                "default_promotion_stack_engine_publication_audit_ready": (
                    publication_audit_ready
                ),
                "default_promotion_stack_engine_publication_policy_agreement": (
                    publication_audit_ready
                ),
                "default_promotion_stack_engine_publication_resident_winsorized_agreement": (
                    publication_audit_ready
                ),
            }
        )
        preflight_payload["checks"].extend(
            [
                {
                    "name": "matrix_stack_engine_publication_audit_passed",
                    "passed": publication_audit_ready,
                },
                {
                    "name": "matrix_stack_engine_publication_policy_chain_passed",
                    "passed": publication_audit_ready,
                },
                {
                    "name": "matrix_stack_engine_publication_resident_winsorized_chain_passed",
                    "passed": publication_audit_ready,
                },
                {
                    "name": "default_promotion_stack_engine_publication_audit_passed",
                    "passed": publication_audit_ready,
                },
                {
                    "name": "default_promotion_stack_engine_publication_policy_chain_passed",
                    "passed": publication_audit_ready,
                },
                {
                    "name": "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
                    "passed": publication_audit_ready,
                },
                {
                    "name": "matrix_stack_engine_publication_audit_matches_default_promotion",
                    "passed": publication_audit_ready,
                },
            ]
        )
        write_json(paths["preflight"], preflight_payload)
    if include_quality_metrics_compare:
        failed_count = 0 if quality_metrics_compare_ready else 1
        preflight_payload["summary"].update(
            {
                "matrix_quality_metrics_compare_present": True,
                "matrix_quality_metrics_compare_ready": quality_metrics_compare_ready,
                "matrix_quality_metrics_compare_status": quality_compare_status,
                "matrix_quality_metrics_compare_failed_check_count": failed_count,
                "default_promotion_quality_metrics_compare_present": True,
                "default_promotion_quality_metrics_compare_ready": (
                    quality_metrics_compare_ready
                ),
                "default_promotion_quality_metrics_compare_status": (
                    quality_compare_status
                ),
                "default_promotion_quality_metrics_compare_failed_check_count": (
                    failed_count
                ),
            }
        )
        preflight_payload["checks"].extend(
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
        write_json(paths["preflight"], preflight_payload)
    if include_release_quality_publication_guard:
        preflight_payload["summary"].update(
            {
                "matrix_release_quality_publication_guard_present": True,
                "matrix_release_quality_publication_guard_ready": (
                    release_quality_publication_guard_ready
                ),
                "matrix_release_quality_publication_guard_check_passed": (
                    release_quality_publication_guard_ready
                ),
                "matrix_release_quality_publication_guard_layers_ready": (
                    release_quality_publication_guard_ready
                ),
                "matrix_release_quality_publication_guard_raw_status": (
                    release_quality_guard_raw_status
                ),
                "matrix_release_quality_publication_guard_phase2_status": (
                    release_quality_guard_phase2_status
                ),
                "matrix_default_promotion_release_quality_publication_guard_ready": (
                    release_quality_publication_guard_ready
                ),
                "matrix_default_promotion_release_quality_publication_guard_raw_status": (
                    release_quality_guard_raw_status
                ),
                "matrix_default_promotion_release_quality_publication_guard_phase2_status": (
                    release_quality_guard_phase2_status
                ),
                "default_promotion_release_quality_publication_guard_present": True,
                "default_promotion_release_quality_publication_guard_ready": (
                    release_quality_publication_guard_ready
                ),
                "default_promotion_release_quality_publication_guard_check_passed": (
                    release_quality_publication_guard_ready
                ),
                "default_promotion_release_quality_publication_guard_layers_ready": (
                    release_quality_publication_guard_ready
                ),
                "default_promotion_release_quality_publication_guard_raw_status": (
                    release_quality_guard_raw_status
                ),
                "default_promotion_release_quality_publication_guard_phase2_status": (
                    release_quality_guard_phase2_status
                ),
            }
        )
        preflight_payload["checks"].extend(
            [
                {
                    "name": "matrix_release_decision_quality_compare_publication_guard_passed",
                    "passed": release_quality_publication_guard_ready,
                },
                {
                    "name": "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed",
                    "passed": release_quality_publication_guard_ready,
                },
                {
                    "name": "default_promotion_release_decision_quality_compare_publication_guard_passed",
                    "passed": release_quality_publication_guard_ready,
                },
                {
                    "name": "matrix_release_decision_quality_publication_guard_matches_default_promotion",
                    "passed": release_quality_publication_guard_ready,
                },
                {
                    "name": "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest",
                    "passed": release_quality_publication_guard_ready,
                },
            ]
        )
        write_json(paths["preflight"], preflight_payload)
    return paths


def test_stack_engine_publication_audit_passes_ready_chain(tmp_path: Path):
    paths = _write_chain(tmp_path)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["status"] == "passed"
    assert payload["passed"] is True
    assert checks["source_contract_ready"] is True
    assert checks["phase2_publish_preflight_stack_engine_ready"] is True
    assert checks["publish_preflight_resident_winsorized_sweep_ready"] is True
    assert checks["phase2_publish_preflight_resident_winsorized_sweep_ready"] is True
    assert checks["publish_preflight_resident_result_contract_ready"] is True
    assert checks["phase2_publish_preflight_resident_result_contract_ready"] is True
    assert (
        checks[
            "phase2_publish_preflight_resident_result_contract_matches_publish_preflight"
        ]
        is True
    )
    assert checks["publish_preflight_integration_engine_policy_ready"] is True
    assert checks["phase2_publish_preflight_integration_engine_policy_ready"] is True
    assert checks["publish_preflight_stack_engine_runtime_default_ready"] is True
    assert (
        checks["phase2_publish_preflight_stack_engine_runtime_default_ready"]
        is True
    )
    assert checks["publish_preflight_direct_runtime_evidence_ready"] is True
    assert checks["phase2_publish_preflight_direct_runtime_evidence_ready"] is True
    assert (
        checks[
            "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
        ]
        is True
    )
    assert checks["publish_preflight_publication_audit_ready"] is True
    assert checks["phase2_publish_preflight_publication_audit_ready"] is True
    assert checks["publish_preflight_quality_metrics_compare_ready"] is True
    assert checks["phase2_publish_preflight_quality_metrics_compare_ready"] is True
    assert (
        checks[
            "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight"
        ]
        is True
    )
    assert checks["publish_preflight_release_quality_publication_guard_ready"] is True
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_ready"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_publication_audit_matches_publish_preflight"
        ]
        is True
    )
    assert checks["phase2_publish_preflight_matches_publish_preflight"] is True
    assert checks["stack_engine_gap_counts_zero"] is True


def test_stack_engine_publication_audit_blocks_missing_publish_preflight_publication_audit(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_publication_audit=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_stack_engine_ready"]["passed"] is True
    assert checks["publish_preflight_publication_audit_ready"]["passed"] is False
    assert (
        checks[
            "phase2_publish_preflight_publication_audit_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks["publish_preflight_publication_audit_ready"]["evidence"][
        "matrix_ready"
    ] is None


def test_stack_engine_publication_audit_blocks_failed_phase2_publication_audit(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        publication_audit_ready=True,
        phase2_publication_audit_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_publication_audit_ready"]["passed"] is True
    assert checks["phase2_publish_preflight_publication_audit_ready"]["passed"] is False
    assert (
        checks[
            "phase2_publish_preflight_publication_audit_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks["phase2_publish_preflight_publication_audit_ready"]["evidence"][
        "matrix_status"
    ] == "failed"


def test_stack_engine_publication_audit_allows_missing_quality_compare_chain(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        include_quality_metrics_compare=False,
        include_phase2_quality_metrics_compare=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "passed"
    assert checks["publish_preflight_quality_metrics_compare_ready"]["passed"] is True
    assert (
        checks["phase2_publish_preflight_quality_metrics_compare_ready"]["passed"]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight"
        ]["passed"]
        is True
    )
    assert checks["publish_preflight_quality_metrics_compare_ready"]["evidence"][
        "present"
    ] is False


def test_stack_engine_publication_audit_blocks_failed_quality_compare_chain(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, quality_metrics_compare_ready=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_quality_metrics_compare_ready"]["passed"] is False
    assert (
        checks["phase2_publish_preflight_quality_metrics_compare_ready"]["passed"]
        is False
    )
    assert checks["publish_preflight_quality_metrics_compare_ready"]["evidence"][
        "matrix_status"
    ] == "failed"
    assert checks["publish_preflight_quality_metrics_compare_ready"]["evidence"][
        "matrix_failed_check_count"
    ] == 1


def test_stack_engine_publication_audit_blocks_phase2_quality_compare_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        quality_metrics_compare_ready=True,
        phase2_quality_metrics_compare_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_quality_metrics_compare_ready"]["passed"] is True
    assert (
        checks["phase2_publish_preflight_quality_metrics_compare_ready"]["passed"]
        is False
    )
    match_check = checks[
        "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight"
    ]
    assert match_check["passed"] is False
    assert match_check["evidence"]["phase2_publish_preflight"]["matrix_status"] == "failed"


def test_stack_engine_publication_audit_blocks_missing_phase2_quality_compare(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_phase2_quality_metrics_compare=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_quality_metrics_compare_ready"]["passed"] is True
    assert (
        checks["phase2_publish_preflight_quality_metrics_compare_ready"]["passed"]
        is True
    )
    match_check = checks[
        "phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight"
    ]
    assert match_check["passed"] is False
    assert match_check["evidence"]["phase2_publish_preflight"]["present"] is False


def test_stack_engine_publication_audit_allows_missing_release_quality_guard_chain(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        include_release_quality_publication_guard=False,
        include_phase2_release_quality_publication_guard=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "passed"
    assert (
        checks["publish_preflight_release_quality_publication_guard_ready"][
            "passed"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_ready"
        ]["passed"]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight"
        ]["passed"]
        is True
    )
    assert checks[
        "publish_preflight_release_quality_publication_guard_ready"
    ]["evidence"]["present"] is False


def test_stack_engine_publication_audit_blocks_failed_release_quality_guard_chain(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        release_quality_publication_guard_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert (
        checks["publish_preflight_release_quality_publication_guard_ready"][
            "passed"
        ]
        is False
    )
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_ready"
        ]["passed"]
        is False
    )
    evidence = checks[
        "publish_preflight_release_quality_publication_guard_ready"
    ]["evidence"]
    assert evidence["matrix_raw_status"] == "failed"
    assert evidence["matrix_phase2_status"] == "attention_required"
    assert evidence["matrix_check"] is False


def test_stack_engine_publication_audit_blocks_phase2_release_quality_guard_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        release_quality_publication_guard_ready=True,
        phase2_release_quality_publication_guard_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert (
        checks["publish_preflight_release_quality_publication_guard_ready"][
            "passed"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_ready"
        ]["passed"]
        is False
    )
    match_check = checks[
        "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight"
    ]
    assert match_check["passed"] is False
    assert (
        match_check["evidence"]["phase2_publish_preflight"]["matrix_raw_status"]
        == "failed"
    )


def test_stack_engine_publication_audit_blocks_missing_phase2_release_quality_guard(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        include_phase2_release_quality_publication_guard=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert (
        checks["publish_preflight_release_quality_publication_guard_ready"][
            "passed"
        ]
        is True
    )
    assert (
        checks[
            "phase2_publish_preflight_release_quality_publication_guard_ready"
        ]["passed"]
        is True
    )
    match_check = checks[
        "phase2_publish_preflight_release_quality_publication_guard_matches_publish_preflight"
    ]
    assert match_check["passed"] is False
    assert match_check["evidence"]["phase2_publish_preflight"]["present"] is False


def test_stack_engine_publication_audit_blocks_missing_publish_preflight_engine_policy(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_integration_engine_policy=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_stack_engine_ready"]["passed"] is True
    assert checks["publish_preflight_integration_engine_policy_ready"]["passed"] is False
    assert (
        checks[
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks["publish_preflight_integration_engine_policy_ready"]["evidence"][
        "matrix_ready"
    ] is None


def test_stack_engine_publication_audit_blocks_failed_publish_preflight_engine_policy(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, integration_engine_policy_ready=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_integration_engine_policy_ready"]["passed"] is False
    assert (
        checks["phase2_publish_preflight_integration_engine_policy_ready"]["passed"]
        is False
    )
    assert checks["publish_preflight_integration_engine_policy_ready"]["evidence"][
        "matrix_acceptance_status"
    ] == "failed"


def test_stack_engine_publication_audit_blocks_missing_publish_preflight_runtime_default(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_runtime_default=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_stack_engine_ready"]["passed"] is True
    assert (
        checks["publish_preflight_stack_engine_runtime_default_ready"]["passed"]
        is False
    )
    assert (
        checks[
            "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks["publish_preflight_stack_engine_runtime_default_ready"][
        "evidence"
    ]["matrix_ready"] is None


def test_stack_engine_publication_audit_blocks_failed_publish_preflight_runtime_default(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, runtime_default_ready=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    runtime_check = checks["publish_preflight_stack_engine_runtime_default_ready"]
    phase2_check = checks["phase2_publish_preflight_stack_engine_runtime_default_ready"]
    assert runtime_check["passed"] is False
    assert phase2_check["passed"] is False
    assert runtime_check["evidence"]["matrix_acceptance_status"] == "failed"
    assert runtime_check["evidence"]["matrix_acceptance_legacy_master_count"] == 1
    assert runtime_check["evidence"]["matrix_pipeline_failed_output_count"] == 1


def test_stack_engine_publication_audit_blocks_phase2_runtime_default_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        runtime_default_ready=True,
        phase2_runtime_default_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_stack_engine_runtime_default_ready"][
        "passed"
    ] is True
    assert checks["phase2_publish_preflight_stack_engine_runtime_default_ready"][
        "passed"
    ] is False
    assert (
        checks[
            "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight"
        ]["passed"]
        is False
    )
    evidence = checks[
        "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight"
    ]["evidence"]["phase2_publish_preflight"]
    assert evidence["matrix_acceptance_status"] == "failed"
    assert evidence["matrix_acceptance_legacy_master_count"] == 1


def test_stack_engine_publication_audit_blocks_missing_phase2_runtime_default(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_phase2_runtime_default=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_stack_engine_runtime_default_ready"][
        "passed"
    ] is True
    assert checks["phase2_publish_preflight_stack_engine_runtime_default_ready"][
        "passed"
    ] is False
    assert checks["phase2_publish_preflight_stack_engine_runtime_default_ready"][
        "evidence"
    ]["phase2_check_passed"] is None
    assert (
        checks[
            "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight"
        ]["passed"]
        is False
    )


def test_stack_engine_publication_audit_blocks_missing_publish_preflight_direct_runtime(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_direct_runtime=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_direct_runtime_evidence_ready"]["passed"] is False
    assert (
        checks[
            "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks["publish_preflight_direct_runtime_evidence_ready"]["evidence"][
        "matrix_ready"
    ] is None


def test_stack_engine_publication_audit_blocks_phase2_direct_runtime_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        direct_runtime_ready=True,
        phase2_direct_runtime_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_direct_runtime_evidence_ready"]["passed"] is True
    assert checks["phase2_publish_preflight_direct_runtime_evidence_ready"]["passed"] is False
    assert (
        checks[
            "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks["phase2_publish_preflight_direct_runtime_evidence_ready"][
        "evidence"
    ]["matrix_acceptance_source"] == "phase2_status_handoff"


def test_stack_engine_publication_audit_blocks_missing_phase2_direct_runtime(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_phase2_direct_runtime=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_direct_runtime_evidence_ready"]["passed"] is True
    assert checks["phase2_publish_preflight_direct_runtime_evidence_ready"]["passed"] is False
    assert checks["phase2_publish_preflight_direct_runtime_evidence_ready"][
        "evidence"
    ]["phase2_check_passed"] is None


def test_stack_engine_publication_audit_blocks_matrix_gap(tmp_path: Path):
    paths = _write_chain(tmp_path, matrix_ready=False, matrix_gap_count=1)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["windows_release_matrix_stack_engine_ready"]["passed"] is False
    assert checks["stack_engine_gap_counts_zero"]["passed"] is False
    assert checks["stack_engine_gap_counts_zero"]["evidence"]["gap_counts"][3] == 1


def test_stack_engine_publication_audit_blocks_resident_winsorized_failure(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, resident_winsorized_ready=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_resident_winsorized_sweep_ready"]["passed"] is False
    assert checks["phase2_publish_preflight_resident_winsorized_sweep_ready"][
        "passed"
    ] is False
    assert checks["publish_preflight_resident_winsorized_sweep_ready"]["evidence"][
        "matrix_status"
    ] == "failed"


def test_stack_engine_publication_audit_blocks_phase2_resident_winsorized_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        resident_winsorized_ready=True,
        phase2_resident_winsorized_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_resident_winsorized_sweep_ready"]["passed"] is True
    assert checks["phase2_publish_preflight_resident_winsorized_sweep_ready"][
        "passed"
    ] is False
    assert checks[
        "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
    ]["passed"] is False
    assert checks[
        "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
    ]["evidence"]["phase2_publish_preflight"]["matrix_status"] == "failed"


def test_stack_engine_publication_audit_blocks_resident_result_contract_failure(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, resident_result_contract_ready=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert payload["passed"] is False
    assert checks["publish_preflight_resident_result_contract_ready"][
        "passed"
    ] is False
    assert checks["phase2_publish_preflight_resident_result_contract_ready"][
        "passed"
    ] is False
    assert checks["publish_preflight_resident_result_contract_ready"]["evidence"][
        "matrix_status"
    ] == "failed"
    assert checks["publish_preflight_resident_result_contract_ready"]["evidence"][
        "matrix_failed_count"
    ] == 1


def test_stack_engine_publication_audit_blocks_phase2_resident_result_contract_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        resident_result_contract_ready=True,
        phase2_resident_result_contract_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_resident_result_contract_ready"][
        "passed"
    ] is True
    assert checks["phase2_publish_preflight_resident_result_contract_ready"][
        "passed"
    ] is False
    assert checks[
        "phase2_publish_preflight_resident_result_contract_matches_publish_preflight"
    ]["passed"] is False
    assert checks[
        "phase2_publish_preflight_resident_result_contract_matches_publish_preflight"
    ]["evidence"]["phase2_publish_preflight"]["matrix_status"] == "failed"


def test_stack_engine_publication_audit_blocks_missing_phase2_resident_result_contract(
    tmp_path: Path,
):
    paths = _write_chain(tmp_path, include_phase2_resident_result_contract=False)

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_resident_result_contract_ready"][
        "passed"
    ] is True
    assert checks["phase2_publish_preflight_resident_result_contract_ready"][
        "passed"
    ] is False
    assert checks["phase2_publish_preflight_resident_result_contract_ready"][
        "evidence"
    ]["phase2_check_passed"] is None


def test_stack_engine_publication_audit_blocks_phase2_engine_policy_mismatch(
    tmp_path: Path,
):
    paths = _write_chain(
        tmp_path,
        integration_engine_policy_ready=True,
        phase2_integration_engine_policy_ready=False,
    )

    payload = build_stack_engine_publication_audit(
        stack_engine_contract=paths["stack"],
        phase2_status=paths["phase2"],
        default_promotion_manifest=paths["promotion"],
        windows_release_matrix=paths["matrix"],
        github_release_plan=paths["github"],
        publish_preflight=paths["preflight"],
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["status"] == "blocked"
    assert checks["publish_preflight_integration_engine_policy_ready"]["passed"] is True
    assert (
        checks["phase2_publish_preflight_integration_engine_policy_ready"]["passed"]
        is False
    )
    assert (
        checks[
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
        ]["passed"]
        is False
    )
    assert checks[
        "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
    ]["evidence"]["phase2_publish_preflight"]["matrix_acceptance_status"] == "failed"


def test_stack_engine_publication_audit_cli_writes_outputs(tmp_path: Path):
    paths = _write_chain(tmp_path)
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"

    result = main(
        [
            "stack-engine-publication-audit",
            "--stack-engine-contract",
            str(paths["stack"]),
            "--phase2-status",
            str(paths["phase2"]),
            "--default-promotion-manifest",
            str(paths["promotion"]),
            "--windows-release-matrix",
            str(paths["matrix"]),
            "--github-release-plan",
            str(paths["github"]),
            "--publish-preflight",
            str(paths["preflight"]),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "stack_engine_publication_audit"
    assert payload["status"] == "passed"
    text = markdown.read_text(encoding="utf-8")
    assert "GLASS StackEngine Publication Audit" in text
    assert "phase2_publish_preflight_stack_engine_ready" in text
    assert "publish_preflight_resident_winsorized_sweep_ready" in text
    assert "publish_preflight_resident_result_contract_ready" in text
    assert "publish_preflight_integration_engine_policy_ready" in text
    assert "publish_preflight_stack_engine_runtime_default_ready" in text
    assert "publish_preflight_publication_audit_ready" in text
    assert "publish_preflight_quality_metrics_compare_ready" in text
    assert "publish_preflight_release_quality_publication_guard_ready" in text
