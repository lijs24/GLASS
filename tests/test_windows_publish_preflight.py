from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_publish_preflight import build_windows_publish_preflight


def _stack_engine_contract(*, ready: bool = True, gap_count: int = 0) -> dict[str, object]:
    contract_ready = ready and gap_count == 0
    recommendation = (
        "stack_engine_default_ready"
        if contract_ready
        else "stack_engine_contract_gaps_remain"
    )
    blockers = (
        []
        if contract_ready
        else [{"name": "phase2_stack_engine_default_gaps", "gap_count": gap_count}]
    )
    return {
        "present": True,
        "ready": contract_ready,
        "phase2_check_passed": contract_ready,
        "status": "passed" if contract_ready else "failed",
        "passed": contract_ready,
        "scope": "all",
        "adoption_recommendation": recommendation,
        "default_promotion_phase2_stack_engine_default_gap_count": gap_count,
        "default_promotion_blocker_count": 0 if contract_ready else 1,
        "default_promotion_blockers": blockers,
    }


def _resident_winsorized_sweep(
    *,
    ready: bool = True,
    required_frame_count: int = 200,
    check_count: int = 27,
) -> dict[str, object]:
    required_row_ready = ready and required_frame_count >= 200
    sweep_ready = ready and required_row_ready and check_count > 0
    failed_checks = [] if sweep_ready else [{"name": "resident_winsorized_sweep"}]
    failed_check_count = 0 if sweep_ready else 1
    audit = {
        "check_count": check_count,
        "contract_name": "s2_gate_269_default_resident_winsorized_sweep",
        "failed_check_count": failed_check_count,
        "failed_checks": failed_checks,
        "frame_counts": [8, 32, 128, required_frame_count],
        "max_hardened_master_rms": 2.3e-5,
        "passed": sweep_ready,
        "path": "runs/checkpoints/s2_gate_269_resident_winsorized_sweep_audit.json",
        "phase2_check_passed": sweep_ready,
        "present": True,
        "required_frame_count": required_frame_count,
        "required_frame_count_passed": required_row_ready,
        "required_frame_cuda_hardened_s": 0.0012,
        "required_frame_master_max_abs": 6.1e-5,
        "required_frame_master_rms": 2.3e-5,
        "run_count": 4,
        "status": "passed" if sweep_ready else "failed",
        "sweep_path": "runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json",
    }
    return {
        "resident_winsorized_sweep_audit": audit,
        "resident_winsorized_sweep_check_count": check_count,
        "resident_winsorized_sweep_failed_check_count": failed_check_count,
        "resident_winsorized_sweep_failed_checks": failed_checks,
        "resident_winsorized_sweep_passed": sweep_ready,
        "resident_winsorized_sweep_phase2_check_passed": sweep_ready,
        "resident_winsorized_sweep_present": True,
        "resident_winsorized_sweep_required_frame_count": required_frame_count,
        "resident_winsorized_sweep_required_frame_count_passed": required_row_ready,
        "resident_winsorized_sweep_required_frame_cuda_hardened_s": 0.0012,
        "resident_winsorized_sweep_required_frame_master_max_abs": 6.1e-5,
        "resident_winsorized_sweep_required_frame_master_rms": 2.3e-5,
        "resident_winsorized_sweep_status": "passed" if sweep_ready else "failed",
    }


def _resident_fastpath_release_handoff(
    *,
    ready: bool = True,
) -> dict[str, object]:
    handoff = {
        "present": True,
        "ready": ready,
        "raw_ready": ready,
        "phase2_ready": ready,
        "agreement": ready,
        "decision_check_passed": ready,
        "phase2_check_passed": ready,
        "raw_status": "passed" if ready else "failed",
        "phase2_status": "passed" if ready else "failed",
        "raw_required": True,
        "phase2_required": True,
        "raw_mode": "similarity_cuda_triangle",
        "phase2_mode": "similarity_cuda_triangle",
        "raw_passed_check_count": 23 if ready else 22,
        "phase2_passed_check_count": 23 if ready else 22,
        "raw_failed_check_count": 0 if ready else 1,
        "phase2_failed_check_count": 0 if ready else 1,
        "raw_failed_checks": []
        if ready
        else ["contract_resident_registration_fastpath_component:triangle_warp_batch"],
        "phase2_failed_checks": []
        if ready
        else ["release_decision_resident_fastpath_handoff_ready"],
    }
    return {
        "resident_registration_fastpath_release_handoff": handoff,
        "resident_registration_fastpath_release_handoff_present": True,
        "resident_registration_fastpath_release_handoff_ready": ready,
        "resident_registration_fastpath_release_handoff_raw_ready": ready,
        "resident_registration_fastpath_release_handoff_phase2_ready": ready,
        "resident_registration_fastpath_release_handoff_agreement": ready,
        "resident_registration_fastpath_release_handoff_decision_check_passed": ready,
        "resident_registration_fastpath_release_handoff_phase2_check_passed": ready,
        "resident_registration_fastpath_release_handoff_raw_status": (
            "passed" if ready else "failed"
        ),
        "resident_registration_fastpath_release_handoff_phase2_status": (
            "passed" if ready else "failed"
        ),
        "resident_registration_fastpath_release_handoff_raw_required": True,
        "resident_registration_fastpath_release_handoff_phase2_required": True,
        "resident_registration_fastpath_release_handoff_raw_mode": (
            "similarity_cuda_triangle"
        ),
        "resident_registration_fastpath_release_handoff_phase2_mode": (
            "similarity_cuda_triangle"
        ),
        "resident_registration_fastpath_release_handoff_raw_passed_check_count": (
            23 if ready else 22
        ),
        "resident_registration_fastpath_release_handoff_phase2_passed_check_count": (
            23 if ready else 22
        ),
        "resident_registration_fastpath_release_handoff_raw_failed_check_count": (
            0 if ready else 1
        ),
        "resident_registration_fastpath_release_handoff_phase2_failed_check_count": (
            0 if ready else 1
        ),
        "resident_registration_fastpath_release_handoff_raw_failed_checks": []
        if ready
        else ["contract_resident_registration_fastpath_component:triangle_warp_batch"],
        "resident_registration_fastpath_release_handoff_phase2_failed_checks": []
        if ready
        else ["release_decision_resident_fastpath_handoff_ready"],
    }


def _resident_result_contract(*, ready: bool = True) -> dict[str, object]:
    contract = {
        "present": True,
        "ready": ready,
        "status": "passed" if ready else "failed",
        "top_level_check": ready,
        "check_present": True,
        "check_passed": ready,
        "phase2_check_passed": ready,
        "required_count": 1,
        "failed_count": 0 if ready else 1,
        "failed_check_count": 0 if ready else 1,
        "failed_checks": [] if ready else ["source_terms_present"],
        "failed_items": []
        if ready
        else [{"output_id": "master_H", "reason": "source_terms_missing"}],
    }
    return {
        "resident_result_contract": contract,
        "resident_result_contract_present": True,
        "resident_result_contract_ready": ready,
        "resident_result_contract_status": contract["status"],
        "resident_result_contract_top_level_check": contract["top_level_check"],
        "resident_result_contract_check_present": contract["check_present"],
        "resident_result_contract_check_passed": contract["check_passed"],
        "resident_result_contract_phase2_check_passed": contract[
            "phase2_check_passed"
        ],
        "resident_result_contract_required_count": contract["required_count"],
        "resident_result_contract_failed_count": contract["failed_count"],
        "resident_result_contract_failed_check_count": contract[
            "failed_check_count"
        ],
        "resident_result_contract_failed_checks": contract["failed_checks"],
        "resident_result_contract_failed_items": contract["failed_items"],
    }


def _integration_engine_policy_flattened(
    *,
    acceptance_ready: bool = True,
    pipeline_ready: bool = True,
    pipeline_check_present: bool = True,
) -> dict[str, object]:
    pipeline_chain_ready = pipeline_ready and pipeline_check_present
    policy_ready = acceptance_ready and pipeline_chain_ready
    acceptance_failed_items = (
        []
        if acceptance_ready
        else [{"artifact": "phase2_status", "reason": "non_resident_engine"}]
    )
    pipeline_failed_items = (
        []
        if pipeline_chain_ready
        else [{"artifact": "pipeline_contract", "reason": "non_resident_engine"}]
    )
    return {
        "integration_engine_policy": {
            "ready": policy_ready,
            "acceptance_status": "passed" if acceptance_ready else "failed",
            "pipeline_status": "passed" if pipeline_chain_ready else "failed",
        },
        "integration_engine_policy_ready": policy_ready,
        "acceptance_integration_engine_policy_status": "passed"
        if acceptance_ready
        else "failed",
        "acceptance_integration_engine_policy_check_present": True,
        "acceptance_integration_engine_policy_check_passed": acceptance_ready,
        "acceptance_integration_engine_policy_phase2_check_passed": acceptance_ready,
        "acceptance_integration_engine_policy_non_resident_count": 0
        if acceptance_ready
        else 1,
        "acceptance_integration_engine_policy_failed_count": 0
        if acceptance_ready
        else 1,
        "acceptance_integration_engine_policy_failed_items": acceptance_failed_items,
        "pipeline_integration_engine_policy_status": "passed"
        if pipeline_chain_ready
        else "failed",
        "pipeline_integration_engine_policy_check_present": pipeline_check_present,
        "pipeline_integration_engine_policy_check_passed": pipeline_ready
        if pipeline_check_present
        else None,
        "pipeline_integration_engine_policy_phase2_check_passed": (
            pipeline_chain_ready
        ),
        "pipeline_integration_engine_policy_default_engine_policy": pipeline_ready
        if pipeline_check_present
        else None,
        "pipeline_integration_engine_policy_non_resident_count": 0
        if pipeline_chain_ready
        else 1,
        "pipeline_integration_engine_policy_failed_count": 0
        if pipeline_chain_ready
        else 1,
        "pipeline_integration_engine_policy_failed_items": pipeline_failed_items,
    }


def _integration_engine_policy_manifest(
    *,
    acceptance_ready: bool = True,
    pipeline_ready: bool = True,
    pipeline_check_present: bool = True,
) -> dict[str, object]:
    flattened = _integration_engine_policy_flattened(
        acceptance_ready=acceptance_ready,
        pipeline_ready=pipeline_ready,
        pipeline_check_present=pipeline_check_present,
    )
    return {
        "present": True,
        "ready": flattened["integration_engine_policy_ready"],
        "acceptance_status": flattened[
            "acceptance_integration_engine_policy_status"
        ],
        "acceptance_check_present": flattened[
            "acceptance_integration_engine_policy_check_present"
        ],
        "acceptance_check_passed": flattened[
            "acceptance_integration_engine_policy_check_passed"
        ],
        "acceptance_phase2_check_passed": flattened[
            "acceptance_integration_engine_policy_phase2_check_passed"
        ],
        "acceptance_non_resident_count": flattened[
            "acceptance_integration_engine_policy_non_resident_count"
        ],
        "acceptance_failed_count": flattened[
            "acceptance_integration_engine_policy_failed_count"
        ],
        "acceptance_failed_items": flattened[
            "acceptance_integration_engine_policy_failed_items"
        ],
        "pipeline_status": flattened["pipeline_integration_engine_policy_status"],
        "pipeline_check_present": flattened[
            "pipeline_integration_engine_policy_check_present"
        ],
        "pipeline_check_passed": flattened[
            "pipeline_integration_engine_policy_check_passed"
        ],
        "pipeline_phase2_check_passed": flattened[
            "pipeline_integration_engine_policy_phase2_check_passed"
        ],
        "pipeline_default_engine_policy": flattened[
            "pipeline_integration_engine_policy_default_engine_policy"
        ],
        "pipeline_non_resident_count": flattened[
            "pipeline_integration_engine_policy_non_resident_count"
        ],
        "pipeline_failed_count": flattened[
            "pipeline_integration_engine_policy_failed_count"
        ],
        "pipeline_failed_items": flattened[
            "pipeline_integration_engine_policy_failed_items"
        ],
    }


def _stack_engine_runtime_default_flattened(
    *,
    acceptance_ready: bool = True,
    pipeline_ready: bool = True,
    pipeline_check_present: bool = True,
) -> dict[str, object]:
    pipeline_chain_ready = pipeline_ready and pipeline_check_present
    runtime_ready = acceptance_ready and pipeline_chain_ready
    acceptance_failed_masters = (
        []
        if acceptance_ready
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
        if pipeline_chain_ready
        else [
            {
                "item": "H",
                "engine_family": "legacy",
                "reason": "legacy_or_unknown_engine",
            }
        ]
    )
    return {
        "stack_engine_runtime_default": {
            "ready": runtime_ready,
            "acceptance_status": "passed" if acceptance_ready else "failed",
            "pipeline_status": "passed" if pipeline_chain_ready else "failed",
        },
        "stack_engine_runtime_default_ready": runtime_ready,
        "acceptance_stack_engine_runtime_default_status": "passed"
        if acceptance_ready
        else "failed",
        "acceptance_stack_engine_runtime_default_check_present": True,
        "acceptance_stack_engine_runtime_default_check_passed": acceptance_ready,
        "acceptance_stack_engine_runtime_default_phase2_check_passed": acceptance_ready,
        "acceptance_stack_engine_runtime_default_master_count": 3,
        "acceptance_stack_engine_runtime_default_legacy_master_count": 0
        if acceptance_ready
        else 1,
        "acceptance_stack_engine_runtime_default_failed_master_count": 0
        if acceptance_ready
        else 1,
        "acceptance_stack_engine_runtime_default_failed_output_count": 0,
        "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": 1,
        "acceptance_stack_engine_runtime_default_failed_masters": (
            acceptance_failed_masters
        ),
        "acceptance_stack_engine_runtime_default_failed_outputs": [],
        "pipeline_stack_engine_runtime_default_status": "passed"
        if pipeline_chain_ready
        else "failed",
        "pipeline_stack_engine_runtime_default_check_present": pipeline_check_present,
        "pipeline_stack_engine_runtime_default_check_passed": pipeline_ready
        if pipeline_check_present
        else None,
        "pipeline_stack_engine_runtime_default_phase2_check_passed": (
            pipeline_chain_ready
        ),
        "pipeline_stack_engine_runtime_default_master_count": 3,
        "pipeline_stack_engine_runtime_default_legacy_master_count": 0,
        "pipeline_stack_engine_runtime_default_failed_master_count": 0,
        "pipeline_stack_engine_runtime_default_failed_output_count": 0
        if pipeline_chain_ready
        else 1,
        "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": 1,
        "pipeline_stack_engine_runtime_default_failed_masters": [],
        "pipeline_stack_engine_runtime_default_failed_outputs": (
            pipeline_failed_outputs
        ),
    }


def _stack_engine_runtime_default_manifest(
    *,
    acceptance_ready: bool = True,
    pipeline_ready: bool = True,
    pipeline_check_present: bool = True,
) -> dict[str, object]:
    flattened = _stack_engine_runtime_default_flattened(
        acceptance_ready=acceptance_ready,
        pipeline_ready=pipeline_ready,
        pipeline_check_present=pipeline_check_present,
    )
    return {
        "present": True,
        "ready": flattened["stack_engine_runtime_default_ready"],
        "acceptance_status": flattened[
            "acceptance_stack_engine_runtime_default_status"
        ],
        "acceptance_check_present": flattened[
            "acceptance_stack_engine_runtime_default_check_present"
        ],
        "acceptance_check_passed": flattened[
            "acceptance_stack_engine_runtime_default_check_passed"
        ],
        "acceptance_phase2_check_passed": flattened[
            "acceptance_stack_engine_runtime_default_phase2_check_passed"
        ],
        "acceptance_master_count": flattened[
            "acceptance_stack_engine_runtime_default_master_count"
        ],
        "acceptance_legacy_master_count": flattened[
            "acceptance_stack_engine_runtime_default_legacy_master_count"
        ],
        "acceptance_failed_master_count": flattened[
            "acceptance_stack_engine_runtime_default_failed_master_count"
        ],
        "acceptance_failed_output_count": flattened[
            "acceptance_stack_engine_runtime_default_failed_output_count"
        ],
        "acceptance_explicit_cuda_fast_path_count": flattened[
            "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ],
        "acceptance_failed_masters": flattened[
            "acceptance_stack_engine_runtime_default_failed_masters"
        ],
        "acceptance_failed_outputs": flattened[
            "acceptance_stack_engine_runtime_default_failed_outputs"
        ],
        "pipeline_status": flattened["pipeline_stack_engine_runtime_default_status"],
        "pipeline_check_present": flattened[
            "pipeline_stack_engine_runtime_default_check_present"
        ],
        "pipeline_check_passed": flattened[
            "pipeline_stack_engine_runtime_default_check_passed"
        ],
        "pipeline_phase2_check_passed": flattened[
            "pipeline_stack_engine_runtime_default_phase2_check_passed"
        ],
        "pipeline_master_count": flattened[
            "pipeline_stack_engine_runtime_default_master_count"
        ],
        "pipeline_legacy_master_count": flattened[
            "pipeline_stack_engine_runtime_default_legacy_master_count"
        ],
        "pipeline_failed_master_count": flattened[
            "pipeline_stack_engine_runtime_default_failed_master_count"
        ],
        "pipeline_failed_output_count": flattened[
            "pipeline_stack_engine_runtime_default_failed_output_count"
        ],
        "pipeline_explicit_cuda_fast_path_count": flattened[
            "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ],
        "pipeline_failed_masters": flattened[
            "pipeline_stack_engine_runtime_default_failed_masters"
        ],
        "pipeline_failed_outputs": flattened[
            "pipeline_stack_engine_runtime_default_failed_outputs"
        ],
    }


def _direct_runtime_evidence_flattened(
    *,
    ready: bool = True,
    acceptance_ready: bool = True,
    acceptance_source: str = "explicit_resident_artifacts_json",
    pipeline_ready: bool = True,
    pipeline_source: str = "resident_artifacts_json_fallback",
) -> dict[str, object]:
    evidence_ready = ready and acceptance_ready and pipeline_ready
    return {
        "runtime_default_direct_evidence": {
            "present": True,
            "ready": evidence_ready,
            "acceptance_direct_fastpath": acceptance_ready,
            "acceptance_fastpath_source": acceptance_source,
            "acceptance_fastpath_check_count": 24,
            "acceptance_fastpath_failed_check_count": 0 if acceptance_ready else 1,
            "acceptance_fastpath_failed_checks": []
            if acceptance_ready
            else ["contract_resident_registration_fastpath_present"],
            "pipeline_direct_resident_calibration": pipeline_ready,
            "pipeline_calibration_artifact_source": pipeline_source,
            "pipeline_calibration_artifact_generated_for_contract": pipeline_ready,
            "pipeline_calibration_artifact_path_exists": False,
            "pipeline_resident_native_calibration_artifact": pipeline_ready,
            "pipeline_resident_calibrated_light_count": 200 if pipeline_ready else 0,
        },
        "runtime_default_direct_evidence_present": True,
        "runtime_default_direct_evidence_ready": evidence_ready,
        "runtime_default_direct_acceptance_fastpath": acceptance_ready,
        "runtime_default_direct_acceptance_fastpath_source": acceptance_source,
        "runtime_default_direct_acceptance_fastpath_check_count": 24,
        "runtime_default_direct_acceptance_fastpath_failed_check_count": 0
        if acceptance_ready
        else 1,
        "runtime_default_direct_acceptance_fastpath_failed_checks": []
        if acceptance_ready
        else ["contract_resident_registration_fastpath_present"],
        "runtime_default_direct_pipeline_calibration": pipeline_ready,
        "runtime_default_direct_pipeline_calibration_source": pipeline_source,
        "runtime_default_direct_pipeline_calibration_generated_for_contract": pipeline_ready,
        "runtime_default_direct_pipeline_calibration_path_exists": False,
        "runtime_default_direct_pipeline_resident_native_calibration_artifact": pipeline_ready,
        "runtime_default_direct_pipeline_resident_calibrated_light_count": 200
        if pipeline_ready
        else 0,
    }


def _direct_runtime_evidence_manifest(**kwargs: object) -> dict[str, object]:
    flattened = _direct_runtime_evidence_flattened(**kwargs)
    return {
        "present": flattened["runtime_default_direct_evidence_present"],
        "ready": flattened["runtime_default_direct_evidence_ready"],
        "acceptance_direct_fastpath": flattened[
            "runtime_default_direct_acceptance_fastpath"
        ],
        "acceptance_fastpath_source": flattened[
            "runtime_default_direct_acceptance_fastpath_source"
        ],
        "acceptance_fastpath_check_count": flattened[
            "runtime_default_direct_acceptance_fastpath_check_count"
        ],
        "acceptance_fastpath_failed_check_count": flattened[
            "runtime_default_direct_acceptance_fastpath_failed_check_count"
        ],
        "acceptance_fastpath_failed_checks": flattened[
            "runtime_default_direct_acceptance_fastpath_failed_checks"
        ],
        "pipeline_direct_resident_calibration": flattened[
            "runtime_default_direct_pipeline_calibration"
        ],
        "pipeline_calibration_artifact_source": flattened[
            "runtime_default_direct_pipeline_calibration_source"
        ],
        "pipeline_calibration_artifact_generated_for_contract": flattened[
            "runtime_default_direct_pipeline_calibration_generated_for_contract"
        ],
        "pipeline_calibration_artifact_path_exists": flattened[
            "runtime_default_direct_pipeline_calibration_path_exists"
        ],
        "pipeline_resident_native_calibration_artifact": flattened[
            "runtime_default_direct_pipeline_resident_native_calibration_artifact"
        ],
        "pipeline_resident_calibrated_light_count": flattened[
            "runtime_default_direct_pipeline_resident_calibrated_light_count"
        ],
    }


def _release_direct_publication_guard(
    *,
    ready: bool = True,
    top_level: bool = False,
    acceptance_source: str = "explicit_resident_artifacts_json",
    calibration_source: str = "resident_artifacts_json_fallback",
    resident_lights: int = 200,
) -> dict[str, object]:
    source_ready = (
        ready
        and acceptance_source == "explicit_resident_artifacts_json"
        and calibration_source == "resident_artifacts_json_fallback"
    )
    count_ready = ready and resident_lights >= 200
    if top_level:
        return {
            "present": True,
            "ready": ready and source_ready and count_ready,
            "decision_check_passed": ready,
            "checks_passed": ready,
            "source_ready": source_ready,
            "count_ready": count_ready,
            "raw_leaf_checks_ready": ready,
            "phase2_leaf_checks_ready": ready,
            "raw_acceptance_source": acceptance_source,
            "phase2_acceptance_source": acceptance_source,
            "raw_calibration_source": calibration_source,
            "phase2_calibration_source": calibration_source,
            "raw_resident_lights": resident_lights if ready else 0,
            "raw_default_promotion_resident_lights": resident_lights if ready else 0,
            "phase2_resident_lights": resident_lights if ready else 0,
            "phase2_default_promotion_resident_lights": resident_lights
            if ready
            else 0,
            "required_min_resident_lights": 200,
        }
    return {
        "present": True,
        "ready": ready and source_ready and count_ready,
        "decision_check_passed": ready,
        "checks_passed": ready,
        "source_ready": source_ready,
        "count_ready": count_ready,
        "leaf_checks_ready": ready,
        "raw_ready": ready,
        "phase2_ready": ready,
        "phase2_check_passed": ready,
        "raw_matrix_acceptance_source": acceptance_source,
        "raw_default_promotion_acceptance_source": acceptance_source,
        "phase2_matrix_acceptance_source": acceptance_source,
        "phase2_default_promotion_acceptance_source": acceptance_source,
        "raw_matrix_acceptance_check_count": 24 if ready else 0,
        "raw_default_promotion_acceptance_check_count": 24 if ready else 0,
        "phase2_matrix_acceptance_check_count": 24 if ready else 0,
        "phase2_default_promotion_acceptance_check_count": 24 if ready else 0,
        "raw_matrix_pipeline_calibration_source": calibration_source,
        "raw_default_promotion_pipeline_calibration_source": calibration_source,
        "phase2_matrix_pipeline_calibration_source": calibration_source,
        "phase2_default_promotion_pipeline_calibration_source": calibration_source,
        "raw_matrix_pipeline_resident_lights": resident_lights if ready else 0,
        "raw_default_promotion_pipeline_resident_lights": resident_lights
        if ready
        else 0,
        "phase2_matrix_pipeline_resident_lights": resident_lights if ready else 0,
        "phase2_default_promotion_pipeline_resident_lights": resident_lights
        if ready
        else 0,
        "required_min_resident_lights": 200,
    }


def _release_direct_publication_guard_flattened(
    guard: dict[str, object],
) -> dict[str, object]:
    return {
        "release_decision_direct_runtime_publication_guard": guard,
        "release_decision_direct_runtime_publication_guard_present": guard[
            "present"
        ],
        "release_decision_direct_runtime_publication_guard_ready": guard["ready"],
        "release_decision_direct_runtime_publication_guard_check_passed": guard[
            "decision_check_passed"
        ],
        "release_decision_direct_runtime_publication_guard_source_ready": guard[
            "source_ready"
        ],
        "release_decision_direct_runtime_publication_guard_count_ready": guard[
            "count_ready"
        ],
        "release_decision_direct_runtime_publication_guard_leaf_checks_ready": guard[
            "leaf_checks_ready"
        ],
        "release_decision_direct_runtime_publication_guard_raw_acceptance_source": guard[
            "raw_matrix_acceptance_source"
        ],
        "release_decision_direct_runtime_publication_guard_raw_calibration_source": guard[
            "raw_matrix_pipeline_calibration_source"
        ],
        "release_decision_direct_runtime_publication_guard_raw_resident_lights": guard[
            "raw_matrix_pipeline_resident_lights"
        ],
    }


def _stack_publication_audit(
    *,
    audit_ready: bool = True,
    policy_ready: bool = True,
    resident_winsorized_ready: bool = True,
    flattened: bool = False,
) -> dict[str, object]:
    failed_checks = []
    if not audit_ready:
        failed_checks.append("stack_engine_publication_audit_passed")
    if not policy_ready:
        failed_checks.append("stack_engine_publication_audit_policy_chain_passed")
    if not resident_winsorized_ready:
        failed_checks.append(
            "stack_engine_publication_audit_resident_winsorized_chain_passed"
        )
    publication_ready = audit_ready and policy_ready and resident_winsorized_ready
    audit = {
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
        "phase2_audit_check_passed": audit_ready,
        "policy_chain_phase2_check_passed": policy_ready,
        "resident_winsorized_chain_phase2_check_passed": resident_winsorized_ready,
        "publish_preflight_policy_ready": policy_ready,
        "phase2_policy_ready": policy_ready,
        "policy_agreement": policy_ready,
        "publish_preflight_resident_winsorized_ready": resident_winsorized_ready,
        "phase2_resident_winsorized_ready": resident_winsorized_ready,
        "resident_winsorized_agreement": resident_winsorized_ready,
    }
    payload: dict[str, object] = {"stack_engine_publication_audit": audit}
    if flattened:
        payload.update(
            {
                "stack_engine_publication_audit_present": audit["present"],
                "stack_engine_publication_audit_ready": audit["ready"],
                "stack_engine_publication_audit_status": audit["status"],
                "stack_engine_publication_audit_passed": audit["passed"],
                "stack_engine_publication_audit_phase2_check_passed": audit[
                    "phase2_audit_check_passed"
                ],
                "stack_engine_publication_audit_recommendation": audit[
                    "recommendation"
                ],
                "stack_engine_publication_audit_check_count": audit["check_count"],
                "stack_engine_publication_audit_failed_check_count": audit[
                    "failed_check_count"
                ],
                "stack_engine_publication_audit_failed_checks": audit[
                    "failed_checks"
                ],
                "stack_engine_publication_policy_chain_phase2_check_passed": audit[
                    "policy_chain_phase2_check_passed"
                ],
                "stack_engine_publication_publish_preflight_policy_ready": audit[
                    "publish_preflight_policy_ready"
                ],
                "stack_engine_publication_phase2_policy_ready": audit[
                    "phase2_policy_ready"
                ],
                "stack_engine_publication_policy_agreement": audit[
                    "policy_agreement"
                ],
                "stack_engine_publication_resident_winsorized_chain_phase2_check_passed": audit[
                    "resident_winsorized_chain_phase2_check_passed"
                ],
                "stack_engine_publication_publish_preflight_resident_winsorized_ready": audit[
                    "publish_preflight_resident_winsorized_ready"
                ],
                "stack_engine_publication_phase2_resident_winsorized_ready": audit[
                    "phase2_resident_winsorized_ready"
                ],
                "stack_engine_publication_resident_winsorized_agreement": audit[
                    "resident_winsorized_agreement"
                ],
            }
        )
    return payload


def _matrix(
    path: Path,
    *,
    labels: list[str],
    ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
    sample_accounting_closure_ready: bool = True,
    include_stack_engine_contract: bool = True,
    stack_engine_ready: bool = True,
    stack_engine_gap_count: int = 0,
    include_resident_winsorized_sweep: bool = True,
    resident_winsorized_sweep_ready: bool = True,
    resident_winsorized_required_frame_count: int = 200,
    resident_winsorized_check_count: int = 27,
    include_resident_fastpath_handoff: bool = True,
    resident_fastpath_handoff_ready: bool = True,
    include_resident_result_contract: bool = True,
    resident_result_contract_ready: bool = True,
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
    direct_runtime_evidence_ready: bool = True,
    direct_acceptance_fastpath_ready: bool = True,
    direct_acceptance_fastpath_source: str = "explicit_resident_artifacts_json",
    direct_pipeline_calibration_ready: bool = True,
    direct_pipeline_calibration_source: str = "resident_artifacts_json_fallback",
    include_release_direct_publication_guard: bool = True,
    release_direct_publication_guard_ready: bool = True,
    default_release_direct_publication_guard_ready: bool = True,
    release_direct_publication_guard_acceptance_source: str = "explicit_resident_artifacts_json",
) -> None:
    stack_contract = _stack_engine_contract(
        ready=stack_engine_ready,
        gap_count=stack_engine_gap_count,
    )
    resident_sweep = _resident_winsorized_sweep(
        ready=resident_winsorized_sweep_ready,
        required_frame_count=resident_winsorized_required_frame_count,
        check_count=resident_winsorized_check_count,
    )
    resident_sweep_ready = (
        bool(resident_sweep["resident_winsorized_sweep_passed"])
        and bool(resident_sweep["resident_winsorized_sweep_required_frame_count_passed"])
        and int(resident_sweep["resident_winsorized_sweep_check_count"]) > 0
        and int(resident_sweep["resident_winsorized_sweep_failed_check_count"]) == 0
    )
    resident_fastpath_handoff = _resident_fastpath_release_handoff(
        ready=resident_fastpath_handoff_ready
    )
    resident_result_contract = _resident_result_contract(
        ready=resident_result_contract_ready
    )
    integration_engine_policy = _integration_engine_policy_flattened(
        acceptance_ready=acceptance_integration_engine_policy_ready,
        pipeline_ready=pipeline_integration_engine_policy_ready,
        pipeline_check_present=pipeline_integration_engine_policy_check_present,
    )
    integration_engine_policy_ready = bool(
        integration_engine_policy["integration_engine_policy_ready"]
    )
    stack_engine_runtime_default = _stack_engine_runtime_default_flattened(
        acceptance_ready=acceptance_stack_engine_runtime_default_ready,
        pipeline_ready=pipeline_stack_engine_runtime_default_ready,
        pipeline_check_present=pipeline_stack_engine_runtime_default_check_present,
    )
    stack_engine_runtime_default_ready = bool(
        stack_engine_runtime_default["stack_engine_runtime_default_ready"]
    )
    publication_audit = _stack_publication_audit(
        audit_ready=stack_publication_audit_ready,
        policy_ready=stack_publication_policy_ready,
        resident_winsorized_ready=stack_publication_resident_winsorized_ready,
        flattened=True,
    )
    publication_audit_ready = bool(
        (
            publication_audit["stack_engine_publication_audit"]
            if isinstance(publication_audit["stack_engine_publication_audit"], dict)
            else {}
        ).get("ready")
    )
    direct_evidence = _direct_runtime_evidence_flattened(
        ready=direct_runtime_evidence_ready,
        acceptance_ready=direct_acceptance_fastpath_ready,
        acceptance_source=direct_acceptance_fastpath_source,
        pipeline_ready=direct_pipeline_calibration_ready,
        pipeline_source=direct_pipeline_calibration_source,
    )
    release_direct_guard = _release_direct_publication_guard(
        ready=release_direct_publication_guard_ready,
        top_level=True,
        acceptance_source=release_direct_publication_guard_acceptance_source,
    )
    default_release_direct_guard = _release_direct_publication_guard(
        ready=default_release_direct_publication_guard_ready,
        acceptance_source=release_direct_publication_guard_acceptance_source,
    )
    matrix_ready = (
        ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and (
            bool(stack_contract["ready"])
            if include_stack_engine_contract
            else True
        )
        and (resident_sweep_ready if include_resident_winsorized_sweep else True)
        and (
            integration_engine_policy_ready
            if include_integration_engine_policy
            else True
        )
        and (
            stack_engine_runtime_default_ready
            if include_stack_engine_runtime_default
            else True
        )
        and (publication_audit_ready if include_stack_publication_audit else True)
        and (
            resident_fastpath_handoff_ready
            if include_resident_fastpath_handoff
            else True
        )
        and (
            resident_result_contract_ready
            if include_resident_result_contract
            else True
        )
    )
    promotion = {
        "status": "default_promotion_ready" if matrix_ready else "blocked",
        "passed": matrix_ready,
        "default_change_ready": matrix_ready,
        "default_route_passed": ready,
        "default_route_route_contract_passed": ready,
        "default_route_route_check_count": 4 if ready else 2,
        "default_route_speedup_vs_reference": 28.75,
        "integration_rejection_sample_counts_match_maps": (
            rejection_sample_accounting_ready
        ),
        "rejection_sample_accounting_status": "passed"
        if rejection_sample_accounting_ready
        else "failed",
        "rejection_sample_accounting_failed_count": 0
        if rejection_sample_accounting_ready
        else 1,
        "integration_sample_accounting_closure": sample_accounting_closure_ready,
        "sample_accounting_closure": {
            "status": "passed" if sample_accounting_closure_ready else "failed",
            "check_present": True,
            "present_count": 1,
            "failed_count": 0 if sample_accounting_closure_ready else 1,
            "failed_items": []
            if sample_accounting_closure_ready
            else [{"item": "H", "reason": "sample_closure_drift"}],
        },
        "sample_accounting_closure_status": "passed"
        if sample_accounting_closure_ready
        else "failed",
        "sample_accounting_closure_present_count": 1,
        "sample_accounting_closure_failed_count": 0
        if sample_accounting_closure_ready
        else 1,
    }
    if include_stack_engine_contract:
        promotion.update(
            {
                "stack_engine_contract": stack_contract,
                "stack_engine_contract_present": True,
                "stack_engine_contract_ready": stack_contract["ready"],
                "stack_engine_contract_phase2_check_passed": stack_contract[
                    "phase2_check_passed"
                ],
                "stack_engine_contract_status": stack_contract["status"],
                "stack_engine_contract_passed": stack_contract["passed"],
                "stack_engine_contract_scope": stack_contract["scope"],
                "stack_engine_contract_adoption_recommendation": stack_contract[
                    "adoption_recommendation"
                ],
                "stack_engine_contract_default_gap_count": stack_contract[
                    "default_promotion_phase2_stack_engine_default_gap_count"
                ],
                "stack_engine_contract_blocker_count": stack_contract[
                    "default_promotion_blocker_count"
                ],
                "stack_engine_contract_blockers": stack_contract[
                    "default_promotion_blockers"
                ],
            }
        )
    if include_resident_winsorized_sweep:
        promotion.update(resident_sweep)
    if include_resident_fastpath_handoff:
        promotion.update(resident_fastpath_handoff)
    if include_resident_result_contract:
        promotion.update(resident_result_contract)
    if include_integration_engine_policy:
        promotion.update(integration_engine_policy)
    if include_stack_engine_runtime_default:
        promotion.update(stack_engine_runtime_default)
    if include_direct_runtime_evidence:
        promotion.update(direct_evidence)
    if include_release_direct_publication_guard:
        promotion.update(
            _release_direct_publication_guard_flattened(
                default_release_direct_guard
            )
        )
    if include_stack_publication_audit:
        promotion.update(publication_audit)
    payload = {
            "schema_version": 1,
            "artifact_type": "windows_release_matrix",
            "status": "release_matrix_ready" if matrix_ready else "blocked",
            "passed": matrix_ready,
            "current_machine": {
                "primary_package": labels[0],
                "ordered_try_list": labels if "cpu" in labels else [*labels, "cpu"],
            },
            "default_promotion_manifest": promotion,
            "packages": [{"label": label} for label in labels],
        }
    if include_release_direct_publication_guard:
        payload["release_decision_direct_runtime_publication_guard"] = (
            release_direct_guard
        )
    write_json(path, payload)


def _default_promotion(
    path: Path,
    *,
    ready: bool = True,
    rejection_sample_accounting_ready: bool = True,
    sample_accounting_closure_ready: bool = True,
    include_stack_engine_contract: bool = True,
    stack_engine_ready: bool = True,
    stack_engine_gap_count: int = 0,
    include_resident_winsorized_sweep: bool = True,
    resident_winsorized_sweep_ready: bool = True,
    resident_winsorized_required_frame_count: int = 200,
    resident_winsorized_check_count: int = 27,
    include_resident_fastpath_handoff: bool = True,
    resident_fastpath_handoff_ready: bool = True,
    include_resident_result_contract: bool = True,
    resident_result_contract_ready: bool = True,
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
    direct_runtime_evidence_ready: bool = True,
    direct_acceptance_fastpath_ready: bool = True,
    direct_acceptance_fastpath_source: str = "explicit_resident_artifacts_json",
    direct_pipeline_calibration_ready: bool = True,
    direct_pipeline_calibration_source: str = "resident_artifacts_json_fallback",
    include_release_direct_publication_guard: bool = True,
    release_direct_publication_guard_ready: bool = True,
    release_direct_publication_guard_acceptance_source: str = "explicit_resident_artifacts_json",
) -> None:
    stack_contract = _stack_engine_contract(
        ready=stack_engine_ready,
        gap_count=stack_engine_gap_count,
    )
    resident_sweep = _resident_winsorized_sweep(
        ready=resident_winsorized_sweep_ready,
        required_frame_count=resident_winsorized_required_frame_count,
        check_count=resident_winsorized_check_count,
    )
    resident_sweep_ready = (
        bool(resident_sweep["resident_winsorized_sweep_passed"])
        and bool(resident_sweep["resident_winsorized_sweep_required_frame_count_passed"])
        and int(resident_sweep["resident_winsorized_sweep_check_count"]) > 0
        and int(resident_sweep["resident_winsorized_sweep_failed_check_count"]) == 0
    )
    resident_fastpath_handoff = _resident_fastpath_release_handoff(
        ready=resident_fastpath_handoff_ready
    )
    resident_result_contract = _resident_result_contract(
        ready=resident_result_contract_ready
    )
    integration_engine_policy = _integration_engine_policy_manifest(
        acceptance_ready=acceptance_integration_engine_policy_ready,
        pipeline_ready=pipeline_integration_engine_policy_ready,
        pipeline_check_present=pipeline_integration_engine_policy_check_present,
    )
    integration_engine_policy_ready = bool(integration_engine_policy["ready"])
    stack_engine_runtime_default = _stack_engine_runtime_default_manifest(
        acceptance_ready=acceptance_stack_engine_runtime_default_ready,
        pipeline_ready=pipeline_stack_engine_runtime_default_ready,
        pipeline_check_present=pipeline_stack_engine_runtime_default_check_present,
    )
    stack_engine_runtime_default_ready = bool(
        stack_engine_runtime_default["ready"]
    )
    publication_audit = _stack_publication_audit(
        audit_ready=stack_publication_audit_ready,
        policy_ready=stack_publication_policy_ready,
        resident_winsorized_ready=stack_publication_resident_winsorized_ready,
    )
    publication_audit_ready = bool(
        (
            publication_audit["stack_engine_publication_audit"]
            if isinstance(publication_audit["stack_engine_publication_audit"], dict)
            else {}
        ).get("ready")
    )
    direct_evidence = _direct_runtime_evidence_manifest(
        ready=direct_runtime_evidence_ready,
        acceptance_ready=direct_acceptance_fastpath_ready,
        acceptance_source=direct_acceptance_fastpath_source,
        pipeline_ready=direct_pipeline_calibration_ready,
        pipeline_source=direct_pipeline_calibration_source,
    )
    release_direct_guard = _release_direct_publication_guard(
        ready=release_direct_publication_guard_ready,
        acceptance_source=release_direct_publication_guard_acceptance_source,
    )
    manifest_ready = (
        ready
        and rejection_sample_accounting_ready
        and sample_accounting_closure_ready
        and (
            bool(stack_contract["ready"])
            if include_stack_engine_contract
            else True
        )
        and (resident_sweep_ready if include_resident_winsorized_sweep else True)
        and (
            integration_engine_policy_ready
            if include_integration_engine_policy
            else True
        )
        and (
            stack_engine_runtime_default_ready
            if include_stack_engine_runtime_default
            else True
        )
        and (publication_audit_ready if include_stack_publication_audit else True)
        and (
            resident_fastpath_handoff_ready
            if include_resident_fastpath_handoff
            else True
        )
        and (
            resident_result_contract_ready
            if include_resident_result_contract
            else True
        )
    )
    payload = {
        "schema_version": 1,
        "artifact_type": "default_promotion_manifest",
        "status": "default_promotion_ready" if manifest_ready else "blocked",
        "passed": manifest_ready,
        "default_change_ready": manifest_ready,
        "recommendation": "promote_resident_cuda_default"
        if manifest_ready
        else "fix_blockers",
        "default_route_acceptance": {
            "status": "passed" if ready else "failed",
            "passed": ready,
            "route_contract_passed": ready,
            "route_check_count": 4 if ready else 2,
            "speedup_vs_reference": 28.75,
        },
        "pipeline_contract": {
            "status": "passed"
            if rejection_sample_accounting_ready and sample_accounting_closure_ready
            else "failed",
            "passed": rejection_sample_accounting_ready and sample_accounting_closure_ready,
            "integration_rejection_sample_counts_match_maps": (
                rejection_sample_accounting_ready
            ),
            "rejection_sample_accounting": {
                "status": "passed" if rejection_sample_accounting_ready else "failed",
                "check_present": True,
                "check_passed": rejection_sample_accounting_ready,
                "failed_count": 0 if rejection_sample_accounting_ready else 1,
                "failed_items": []
                if rejection_sample_accounting_ready
                else [{"item": "H", "map_rejected_sample_sum": 7}],
            },
            "rejection_sample_accounting_status": "passed"
            if rejection_sample_accounting_ready
            else "failed",
            "rejection_sample_accounting_failed_count": 0
            if rejection_sample_accounting_ready
            else 1,
            "integration_sample_accounting_closure": sample_accounting_closure_ready,
            "sample_accounting_closure": {
                "status": "passed" if sample_accounting_closure_ready else "failed",
                "check_present": True,
                "present_count": 1,
                "failed_count": 0 if sample_accounting_closure_ready else 1,
                "failed_items": []
                if sample_accounting_closure_ready
                else [{"item": "H", "reason": "sample_closure_drift"}],
            },
            "sample_accounting_closure_status": "passed"
            if sample_accounting_closure_ready
            else "failed",
            "sample_accounting_closure_present_count": 1,
            "sample_accounting_closure_failed_count": 0
            if sample_accounting_closure_ready
            else 1,
        },
    }
    if include_stack_engine_contract:
        payload["stack_engine_contract"] = stack_contract
    if include_resident_winsorized_sweep:
        payload.update(resident_sweep)
    if include_resident_fastpath_handoff:
        payload.update(resident_fastpath_handoff)
    if include_resident_result_contract:
        payload.update(resident_result_contract)
    if include_integration_engine_policy:
        payload["integration_engine_policy"] = integration_engine_policy
    if include_stack_engine_runtime_default:
        payload["stack_engine_runtime_default"] = stack_engine_runtime_default
    if include_direct_runtime_evidence:
        payload["runtime_default_direct_evidence"] = direct_evidence
    if include_release_direct_publication_guard:
        payload["release_decision_direct_runtime_publication_guard"] = (
            release_direct_guard
        )
    if include_stack_publication_audit:
        payload.update(publication_audit)
    write_json(
        path,
        payload,
    )


def _manifest(path: Path, *, matrix: Path, labels: list[str]) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_manifest",
            "status": "release_manifest_ready",
            "passed": True,
            "source_stamps": ["abc1234"],
            "windows_release_matrix": {
                "path": str(matrix),
                "status": "release_matrix_ready",
                "passed": True,
            },
            "packages": [
                {
                    "label": label,
                    "zip_path": str(path.with_name(f"{label}.zip")),
                    "size_bytes": 100 + index,
                    "sha256": f"{index:064x}",
                    "source_stamp": "abc1234",
                }
                for index, label in enumerate(labels, start=1)
            ],
        },
    )


def _github_plan(
    path: Path,
    *,
    manifest: Path,
    matrix: Path,
    labels: list[str],
    asset_sha_override: dict[str, str] | None = None,
    phase2_rejection_sample_accounting_ready: bool = True,
    matrix_rejection_sample_accounting_ready: bool = True,
    phase2_sample_accounting_closure_ready: bool = True,
    matrix_sample_accounting_closure_ready: bool = True,
    phase2_stack_engine_ready: bool = True,
    phase2_stack_engine_gap_count: int = 0,
    matrix_stack_engine_ready: bool = True,
    matrix_stack_engine_gap_count: int = 0,
    matrix_resident_fastpath_handoff_ready: bool = True,
    matrix_resident_result_contract_ready: bool = True,
) -> None:
    phase2_stack_ready = phase2_stack_engine_ready and phase2_stack_engine_gap_count == 0
    matrix_stack_ready = matrix_stack_engine_ready and matrix_stack_engine_gap_count == 0
    matrix_fastpath_handoff = _resident_fastpath_release_handoff(
        ready=matrix_resident_fastpath_handoff_ready
    )
    matrix_result_contract = _resident_result_contract(
        ready=matrix_resident_result_contract_ready
    )
    release_direct_guard = _release_direct_publication_guard(
        ready=True,
        top_level=True,
    )
    default_release_direct_guard = _release_direct_publication_guard(ready=True)
    release_direct_flat = _release_direct_publication_guard_flattened(
        default_release_direct_guard
    )
    plan_ready = (
        phase2_rejection_sample_accounting_ready
        and matrix_rejection_sample_accounting_ready
        and phase2_sample_accounting_closure_ready
        and matrix_sample_accounting_closure_ready
        and phase2_stack_ready
        and matrix_stack_ready
        and matrix_resident_fastpath_handoff_ready
        and matrix_resident_result_contract_ready
    )
    phase2_stack_recommendation = (
        "stack_engine_default_ready"
        if phase2_stack_ready
        else "stack_engine_contract_gaps_remain"
    )
    matrix_stack_recommendation = (
        "stack_engine_default_ready"
        if matrix_stack_ready
        else "stack_engine_contract_gaps_remain"
    )
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_github_release_plan",
            "status": "release_plan_ready" if plan_ready else "blocked",
            "passed": plan_ready,
            "publication_ready": plan_ready,
            "manifest_artifact": str(manifest),
            "release": {"tag": "v0.1.0-test"},
            "phase2": {
                "status": {
                    "path": str(path.with_name("phase2_status.json")),
                    "status": "green"
                    if (
                        phase2_rejection_sample_accounting_ready
                        and phase2_sample_accounting_closure_ready
                        and phase2_stack_ready
                    )
                    else "attention_required",
                    "passed": (
                        phase2_rejection_sample_accounting_ready
                        and phase2_sample_accounting_closure_ready
                        and phase2_stack_ready
                    ),
                    "pipeline_integration_rejection_sample_counts_match_maps": (
                        phase2_rejection_sample_accounting_ready
                    ),
                    "pipeline_rejection_sample_accounting_status": "passed"
                    if phase2_rejection_sample_accounting_ready
                    else "failed",
                    "pipeline_rejection_sample_accounting_failed_count": 0
                    if phase2_rejection_sample_accounting_ready
                    else 1,
                    "pipeline_integration_sample_accounting_closure": (
                        phase2_sample_accounting_closure_ready
                    ),
                    "pipeline_sample_accounting_closure_status": "passed"
                    if phase2_sample_accounting_closure_ready
                    else "failed",
                    "pipeline_sample_accounting_closure_present_count": 1,
                    "pipeline_sample_accounting_closure_failed_count": 0
                    if phase2_sample_accounting_closure_ready
                    else 1,
                    "stack_engine_default_contract_status": "passed"
                    if phase2_stack_ready
                    else "failed",
                    "stack_engine_default_contract_phase2_check_passed": (
                        phase2_stack_ready
                    ),
                    "stack_engine_default_contract_passed": phase2_stack_ready,
                    "stack_engine_default_contract_scope": "all",
                    "stack_engine_default_contract_adoption_recommendation": (
                        phase2_stack_recommendation
                    ),
                    "stack_engine_default_contract_default_promotion_recommendation": (
                        phase2_stack_recommendation
                    ),
                    "stack_engine_default_contract_default_gap_count": (
                        phase2_stack_engine_gap_count
                    ),
                    "stack_engine_default_contract_blocker_count": 0
                    if phase2_stack_ready
                    else 1,
                    "stack_engine_default_contract_blockers": []
                    if phase2_stack_ready
                    else [
                        {
                            "name": "phase2_stack_engine_default_gaps",
                            "gap_count": phase2_stack_engine_gap_count,
                        }
                    ],
                }
            },
            "release_matrix": {
                "path": str(matrix),
                "status": "release_matrix_ready"
                if (
                    matrix_rejection_sample_accounting_ready
                    and matrix_sample_accounting_closure_ready
                    and matrix_stack_ready
                    and matrix_resident_fastpath_handoff_ready
                    and matrix_resident_result_contract_ready
                )
                else "blocked",
                "passed": (
                    matrix_rejection_sample_accounting_ready
                    and matrix_sample_accounting_closure_ready
                    and matrix_stack_ready
                    and matrix_resident_fastpath_handoff_ready
                    and matrix_resident_result_contract_ready
                ),
                "integration_rejection_sample_counts_match_maps": (
                    matrix_rejection_sample_accounting_ready
                ),
                "rejection_sample_accounting_status": "passed"
                if matrix_rejection_sample_accounting_ready
                else "failed",
                "rejection_sample_accounting_failed_count": 0
                if matrix_rejection_sample_accounting_ready
                else 1,
                "integration_sample_accounting_closure": (
                    matrix_sample_accounting_closure_ready
                ),
                "sample_accounting_closure_status": "passed"
                if matrix_sample_accounting_closure_ready
                else "failed",
                "sample_accounting_closure_present_count": 1,
                "sample_accounting_closure_failed_count": 0
                if matrix_sample_accounting_closure_ready
                else 1,
                "stack_engine_contract_ready": matrix_stack_ready,
                "stack_engine_contract_phase2_check_passed": matrix_stack_ready,
                "stack_engine_contract_status": "passed"
                if matrix_stack_ready
                else "failed",
                "stack_engine_contract_passed": matrix_stack_ready,
                "stack_engine_contract_scope": "all",
                "stack_engine_contract_adoption_recommendation": (
                    matrix_stack_recommendation
                ),
                "stack_engine_contract_default_gap_count": matrix_stack_engine_gap_count,
                "stack_engine_contract_blocker_count": 0 if matrix_stack_ready else 1,
                "stack_engine_contract_blockers": []
                if matrix_stack_ready
                else [
                    {
                        "name": "phase2_stack_engine_default_gaps",
                        "gap_count": matrix_stack_engine_gap_count,
                    }
                ],
                "release_decision_direct_runtime_publication_guard": (
                    release_direct_guard
                ),
                "release_decision_direct_runtime_publication_guard_present": (
                    release_direct_guard["present"]
                ),
                "release_decision_direct_runtime_publication_guard_ready": (
                    release_direct_guard["ready"]
                ),
                "release_decision_direct_runtime_publication_guard_check_passed": (
                    release_direct_guard["decision_check_passed"]
                ),
                "release_decision_direct_runtime_publication_guard_source_ready": (
                    release_direct_guard["source_ready"]
                ),
                "release_decision_direct_runtime_publication_guard_count_ready": (
                    release_direct_guard["count_ready"]
                ),
                "release_decision_direct_runtime_publication_guard_leaf_checks_ready": (
                    release_direct_guard["raw_leaf_checks_ready"]
                    and release_direct_guard["phase2_leaf_checks_ready"]
                ),
                "release_decision_direct_runtime_publication_guard_raw_acceptance_source": (
                    release_direct_guard["raw_acceptance_source"]
                ),
                "release_decision_direct_runtime_publication_guard_raw_calibration_source": (
                    release_direct_guard["raw_calibration_source"]
                ),
                "release_decision_direct_runtime_publication_guard_raw_resident_lights": (
                    release_direct_guard["raw_resident_lights"]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard": (
                    default_release_direct_guard
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_present": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_present"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_ready": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_ready"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_check_passed": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_check_passed"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_source_ready": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_source_ready"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_count_ready": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_count_ready"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_leaf_checks_ready": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_leaf_checks_ready"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_raw_acceptance_source": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_raw_acceptance_source"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_raw_calibration_source": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_raw_calibration_source"
                    ]
                ),
                "default_promotion_release_decision_direct_runtime_publication_guard_raw_resident_lights": (
                    release_direct_flat[
                        "release_decision_direct_runtime_publication_guard_raw_resident_lights"
                    ]
                ),
                **matrix_fastpath_handoff,
                **matrix_result_contract,
            },
            "assets": [
                {
                    "label": label,
                    "zip_path": str(manifest.with_name(f"{label}.zip")),
                    "size_bytes": 100 + index,
                    "sha256": (asset_sha_override or {}).get(label, f"{index:064x}"),
                    "source_stamp": "abc1234",
                }
                for index, label in enumerate(labels, start=1)
            ],
            "checks": [
                {
                    "name": "phase2_pipeline_rejection_sample_accounting_passed",
                    "passed": phase2_rejection_sample_accounting_ready,
                    "evidence": {
                        "check": phase2_rejection_sample_accounting_ready,
                        "status": "passed"
                        if phase2_rejection_sample_accounting_ready
                        else "failed",
                        "failed_count": 0 if phase2_rejection_sample_accounting_ready else 1,
                    },
                },
                {
                    "name": "windows_release_matrix_rejection_sample_accounting_passed",
                    "passed": matrix_rejection_sample_accounting_ready,
                    "evidence": {
                        "check": matrix_rejection_sample_accounting_ready,
                        "status": "passed"
                        if matrix_rejection_sample_accounting_ready
                        else "failed",
                        "failed_count": 0 if matrix_rejection_sample_accounting_ready else 1,
                    },
                },
                {
                    "name": "phase2_pipeline_sample_accounting_closure_passed",
                    "passed": phase2_sample_accounting_closure_ready,
                    "evidence": {
                        "check": phase2_sample_accounting_closure_ready,
                        "status": "passed"
                        if phase2_sample_accounting_closure_ready
                        else "failed",
                        "present_count": 1,
                        "failed_count": 0 if phase2_sample_accounting_closure_ready else 1,
                    },
                },
                {
                    "name": "windows_release_matrix_sample_accounting_closure_passed",
                    "passed": matrix_sample_accounting_closure_ready,
                    "evidence": {
                        "check": matrix_sample_accounting_closure_ready,
                        "status": "passed"
                        if matrix_sample_accounting_closure_ready
                        else "failed",
                        "present_count": 1,
                        "failed_count": 0 if matrix_sample_accounting_closure_ready else 1,
                    },
                },
                {
                    "name": "phase2_stack_engine_default_contract_ready",
                    "passed": phase2_stack_ready,
                    "evidence": {
                        "status": "passed" if phase2_stack_ready else "failed",
                        "default_gap_count": phase2_stack_engine_gap_count,
                        "blocker_count": 0 if phase2_stack_ready else 1,
                    },
                },
                {
                    "name": "windows_release_matrix_stack_engine_contract_ready",
                    "passed": matrix_stack_ready,
                    "evidence": {
                        "status": "passed" if matrix_stack_ready else "failed",
                        "default_gap_count": matrix_stack_engine_gap_count,
                        "blocker_count": 0 if matrix_stack_ready else 1,
                    },
                },
                {
                    "name": "phase2_release_matrix_stack_engine_contract_agree",
                    "passed": (
                        phase2_stack_ready
                        and matrix_stack_ready
                        and phase2_stack_engine_gap_count == matrix_stack_engine_gap_count
                    ),
                    "evidence": {
                        "phase2_gap_count": phase2_stack_engine_gap_count,
                        "matrix_gap_count": matrix_stack_engine_gap_count,
                        "phase2_blocker_count": 0 if phase2_stack_ready else 1,
                        "matrix_blocker_count": 0 if matrix_stack_ready else 1,
                    },
                },
                {
                    "name": "windows_release_matrix_release_decision_direct_runtime_publication_guard_passed",
                    "passed": True,
                    "evidence": {
                        "ready": True,
                        "resident_lights": 200,
                    },
                },
                {
                    "name": "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed",
                    "passed": True,
                    "evidence": {
                        "ready": True,
                        "resident_lights": 200,
                    },
                },
                {
                    "name": "windows_release_matrix_resident_fastpath_release_handoff_ready",
                    "passed": matrix_resident_fastpath_handoff_ready,
                    "evidence": {
                        "ready": matrix_resident_fastpath_handoff_ready,
                        "raw_status": "passed"
                        if matrix_resident_fastpath_handoff_ready
                        else "failed",
                        "phase2_status": "passed"
                        if matrix_resident_fastpath_handoff_ready
                        else "failed",
                        "raw_failed_check_count": 0
                        if matrix_resident_fastpath_handoff_ready
                        else 1,
                        "phase2_failed_check_count": 0
                        if matrix_resident_fastpath_handoff_ready
                        else 1,
                    },
                },
                {
                    "name": "windows_release_matrix_resident_result_contract_handoff_passed",
                    "passed": matrix_resident_result_contract_ready,
                    "evidence": {
                        "present": True,
                        "ready": matrix_resident_result_contract_ready,
                        "status": "passed"
                        if matrix_resident_result_contract_ready
                        else "failed",
                        "phase2_check_passed": matrix_resident_result_contract_ready,
                        "required_count": 1,
                        "failed_count": 0
                        if matrix_resident_result_contract_ready
                        else 1,
                        "failed_check_count": 0
                        if matrix_resident_result_contract_ready
                        else 1,
                    },
                },
            ],
        },
    )


def _bundle(tmp_path: Path, *, labels: list[str] = ["cuda13", "cpu"], promotion_ready: bool = True):
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, ready=promotion_ready)
    _default_promotion(promotion, ready=promotion_ready)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)
    return manifest, plan, matrix, promotion


def test_windows_publish_preflight_passes_consistent_bundle(tmp_path: Path):
    manifest, plan, matrix, promotion = _bundle(tmp_path)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "publish_preflight_ready"
    assert payload["summary"]["primary_package"] == "cuda13"
    assert payload["summary"]["github_plan_phase2_rejection_sample_accounting_status"] == "passed"
    assert payload["summary"]["github_plan_matrix_rejection_sample_accounting_status"] == "passed"
    assert payload["summary"]["matrix_rejection_sample_accounting_status"] == "passed"
    assert payload["summary"]["default_promotion_rejection_sample_accounting_status"] == "passed"
    assert payload["summary"]["github_plan_phase2_sample_accounting_closure_status"] == "passed"
    assert payload["summary"]["github_plan_matrix_sample_accounting_closure_status"] == "passed"
    assert payload["summary"]["matrix_sample_accounting_closure_status"] == "passed"
    assert payload["summary"]["default_promotion_sample_accounting_closure_status"] == "passed"
    assert payload["summary"]["matrix_integration_engine_policy_ready"] is True
    assert (
        payload["summary"]["matrix_acceptance_integration_engine_policy_status"]
        == "passed"
    )
    assert (
        payload["summary"]["matrix_pipeline_integration_engine_policy_status"]
        == "passed"
    )
    assert (
        payload["summary"]["default_promotion_integration_engine_policy_ready"]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_acceptance_integration_engine_policy_status"
        ]
        == "passed"
    )
    assert (
        payload["summary"][
            "default_promotion_pipeline_integration_engine_policy_status"
        ]
        == "passed"
    )
    assert payload["summary"]["github_plan_phase2_stack_engine_contract_status"] == "passed"
    assert payload["summary"]["github_plan_matrix_stack_engine_contract_status"] == "passed"
    assert payload["summary"]["matrix_stack_engine_contract_status"] == "passed"
    assert payload["summary"]["default_promotion_stack_engine_contract_status"] == "passed"
    assert payload["summary"]["matrix_resident_winsorized_sweep_status"] == "passed"
    assert (
        payload["summary"]["matrix_resident_winsorized_sweep_required_frame_count"]
        == 200
    )
    assert (
        payload["summary"][
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ]
        is True
    )
    assert payload["summary"]["matrix_resident_winsorized_sweep_check_count"] == 27
    assert (
        payload["summary"]["default_promotion_resident_winsorized_sweep_status"]
        == "passed"
    )
    assert (
        payload["summary"][
            "default_promotion_resident_winsorized_sweep_required_frame_count"
        ]
        == 200
    )
    assert (
        payload["summary"][
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
        ]
        is True
    )
    assert (
        payload["summary"]["default_promotion_resident_winsorized_sweep_check_count"]
        == 27
    )
    assert (
        payload["summary"]["matrix_stack_engine_publication_audit_status"]
        == "passed"
    )
    assert payload["summary"]["matrix_stack_engine_publication_audit_ready"] is True
    assert (
        payload["summary"]["matrix_stack_engine_publication_policy_agreement"]
        is True
    )
    assert (
        payload["summary"][
            "matrix_stack_engine_publication_resident_winsorized_agreement"
        ]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_stack_engine_publication_audit_status"
        ]
        == "passed"
    )
    assert (
        payload["summary"]["default_promotion_stack_engine_publication_audit_ready"]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_stack_engine_publication_policy_agreement"
        ]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_stack_engine_publication_resident_winsorized_agreement"
        ]
        is True
    )
    assert payload["summary"]["matrix_stack_engine_runtime_default_ready"] is True
    assert (
        payload["summary"]["matrix_acceptance_stack_engine_runtime_default_status"]
        == "passed"
    )
    assert (
        payload["summary"]["matrix_pipeline_stack_engine_runtime_default_status"]
        == "passed"
    )
    assert (
        payload["summary"][
            "default_promotion_stack_engine_runtime_default_ready"
        ]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_acceptance_stack_engine_runtime_default_status"
        ]
        == "passed"
    )
    assert (
        payload["summary"][
            "default_promotion_pipeline_stack_engine_runtime_default_status"
        ]
        == "passed"
    )
    assert payload["summary"]["matrix_direct_runtime_evidence_ready"] is True
    assert (
        payload["summary"]["matrix_direct_runtime_acceptance_source"]
        == "explicit_resident_artifacts_json"
    )
    assert payload["summary"]["matrix_direct_runtime_acceptance_check_count"] == 24
    assert (
        payload["summary"]["matrix_direct_runtime_pipeline_calibration_source"]
        == "resident_artifacts_json_fallback"
    )
    assert payload["summary"]["matrix_direct_runtime_pipeline_resident_lights"] == 200
    assert (
        payload["summary"]["default_promotion_direct_runtime_evidence_ready"]
        is True
    )
    assert (
        payload["summary"]["default_promotion_direct_runtime_acceptance_source"]
        == "explicit_resident_artifacts_json"
    )
    assert (
        payload["summary"][
            "default_promotion_direct_runtime_pipeline_calibration_source"
        ]
        == "resident_artifacts_json_fallback"
    )
    assert (
        payload["summary"]["matrix_release_direct_publication_guard_ready"]
        is True
    )
    assert payload["summary"]["matrix_release_direct_publication_guard_lights"] == 200
    assert (
        payload["summary"][
            "matrix_default_promotion_release_direct_publication_guard_ready"
        ]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_release_direct_publication_guard_ready"
        ]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_release_direct_publication_guard_lights"
        ]
        == 200
    )
    assert (
        payload["summary"]["github_plan_matrix_resident_fastpath_handoff_ready"]
        is True
    )
    assert (
        payload["summary"]["github_plan_matrix_resident_fastpath_handoff_raw_status"]
        == "passed"
    )
    assert payload["summary"]["matrix_resident_fastpath_handoff_ready"] is True
    assert (
        payload["summary"]["matrix_resident_fastpath_handoff_raw_check_count"]
        == 23
    )
    assert (
        payload["summary"]["default_promotion_resident_fastpath_handoff_ready"]
        is True
    )
    assert (
        payload["summary"][
            "default_promotion_resident_fastpath_handoff_phase2_status"
        ]
        == "passed"
    )
    assert (
        payload["summary"]["github_plan_matrix_resident_result_contract_ready"]
        is True
    )
    assert (
        payload["summary"]["github_plan_matrix_resident_result_contract_status"]
        == "passed"
    )
    assert payload["summary"]["matrix_resident_result_contract_ready"] is True
    assert payload["summary"]["matrix_resident_result_contract_required_count"] == 1
    assert (
        payload["summary"]["default_promotion_resident_result_contract_ready"]
        is True
    )
    assert (
        payload["summary"]["default_promotion_resident_result_contract_status"]
        == "passed"
    )
    assert checks["github_plan_phase2_rejection_sample_accounting_passed"] is True
    assert checks["github_plan_matrix_rejection_sample_accounting_passed"] is True
    assert checks["matrix_rejection_sample_accounting_passed"] is True
    assert checks["default_promotion_rejection_sample_accounting_passed"] is True
    assert checks["github_plan_matrix_rejection_accounting_matches_matrix"] is True
    assert checks["github_plan_phase2_sample_accounting_closure_passed"] is True
    assert checks["github_plan_matrix_sample_accounting_closure_passed"] is True
    assert checks["matrix_sample_accounting_closure_passed"] is True
    assert checks["default_promotion_sample_accounting_closure_passed"] is True
    assert checks["github_plan_matrix_sample_closure_matches_matrix"] is True
    assert (
        checks[
            "windows_release_matrix_acceptance_integration_engine_policy_passed"
        ]
        is True
    )
    assert (
        checks["windows_release_matrix_pipeline_integration_engine_policy_passed"]
        is True
    )
    assert (
        checks["default_promotion_acceptance_integration_engine_policy_passed"]
        is True
    )
    assert (
        checks["default_promotion_pipeline_integration_engine_policy_passed"]
        is True
    )
    assert checks["matrix_integration_engine_policy_matches_default_promotion"] is True
    assert (
        checks[
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        ]
        is True
    )
    assert (
        checks["windows_release_matrix_pipeline_stack_engine_runtime_default_passed"]
        is True
    )
    assert (
        checks[
            "default_promotion_acceptance_stack_engine_runtime_default_passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_pipeline_stack_engine_runtime_default_passed"]
        is True
    )
    assert (
        checks["matrix_stack_engine_runtime_default_matches_default_promotion"]
        is True
    )
    assert checks["windows_release_matrix_direct_acceptance_fastpath_evidence"] is True
    assert checks["windows_release_matrix_direct_pipeline_calibration_evidence"] is True
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"] is True
    assert checks["default_promotion_direct_pipeline_calibration_evidence"] is True
    assert checks["matrix_direct_runtime_evidence_matches_default_promotion"] is True
    assert (
        checks[
            "github_plan_matrix_release_decision_direct_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix"
        ]
        is True
    )
    assert (
        checks[
            "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix"
        ]
        is True
    )
    assert (
        checks["matrix_release_decision_direct_runtime_publication_guard_passed"]
        is True
    )
    assert (
        checks[
            "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]
        is True
    )
    assert (
        checks[
            "matrix_release_decision_direct_publication_guard_matches_default_promotion"
        ]
        is True
    )
    assert (
        checks[
            "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest"
        ]
        is True
    )
    assert checks["github_plan_matrix_resident_fastpath_release_handoff_ready"] is True
    assert checks["matrix_resident_fastpath_release_handoff_ready"] is True
    assert checks["default_promotion_resident_fastpath_release_handoff_ready"] is True
    assert checks["github_plan_matrix_resident_fastpath_handoff_matches_matrix"] is True
    assert checks["matrix_resident_fastpath_handoff_matches_default_promotion"] is True
    assert checks["github_plan_matrix_resident_result_contract_handoff_passed"] is True
    assert checks["matrix_resident_result_contract_handoff_passed"] is True
    assert checks["default_promotion_resident_result_contract_handoff_passed"] is True
    assert checks["github_plan_matrix_resident_result_contract_matches_matrix"] is True
    assert checks["matrix_resident_result_contract_matches_default_promotion"] is True
    assert checks["github_plan_phase2_stack_engine_default_contract_ready"] is True
    assert checks["github_plan_matrix_stack_engine_contract_ready"] is True
    assert checks["github_plan_stack_engine_contract_agreement_passed"] is True
    assert checks["matrix_stack_engine_contract_ready"] is True
    assert checks["default_promotion_stack_engine_contract_ready"] is True
    assert checks["github_plan_matrix_stack_engine_contract_matches_matrix"] is True
    assert checks["matrix_stack_engine_contract_matches_default_promotion"] is True
    assert checks["matrix_resident_winsorized_sweep_audit_passed"] is True
    assert checks["matrix_resident_winsorized_required_frame_passed"] is True
    assert checks["matrix_resident_winsorized_sweep_check_count"] is True
    assert checks["default_promotion_resident_winsorized_sweep_audit_passed"] is True
    assert checks["default_promotion_resident_winsorized_required_frame_passed"] is True
    assert (
        checks["default_promotion_resident_winsorized_sweep_matches_matrix"] is True
    )
    assert checks["matrix_stack_engine_publication_audit_passed"] is True
    assert checks["matrix_stack_engine_publication_policy_chain_passed"] is True
    assert (
        checks["matrix_stack_engine_publication_resident_winsorized_chain_passed"]
        is True
    )
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
    assert (
        checks["matrix_stack_engine_publication_audit_matches_default_promotion"]
        is True
    )
    assert checks["manifest_assets_match_github_plan"] is True
    assert checks["matrix_packages_match_manifest"] is True
    assert checks["cpu_fallback_preserved"] is True


def test_windows_publish_preflight_blocks_asset_mismatch(tmp_path: Path):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        asset_sha_override={"cuda13": "f" * 64},
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["manifest_assets_match_github_plan"] is False


def test_windows_publish_preflight_blocks_failed_default_promotion(tmp_path: Path):
    manifest, plan, matrix, promotion = _bundle(tmp_path, promotion_ready=False)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"] is False
    assert checks["default_promotion_ready"] is False
    assert checks["default_route_contract_passed"] is False


def test_windows_publish_preflight_blocks_phase2_rejection_sample_accounting_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        phase2_rejection_sample_accounting_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["github_release_plan"]["rejection_sample_accounting"][
        "phase2_rejection_sample_accounting_status"
    ] == "failed"
    assert checks["github_plan_phase2_rejection_sample_accounting_passed"][
        "passed"
    ] is False
    assert checks["github_plan_phase2_rejection_sample_accounting_passed"][
        "evidence"
    ]["failed_count"] == 1


def test_windows_publish_preflight_blocks_matrix_rejection_sample_accounting_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, rejection_sample_accounting_ready=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        matrix_rejection_sample_accounting_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["summary"]["matrix_rejection_sample_accounting_status"] == "failed"
    assert checks["github_plan_matrix_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["matrix_rejection_sample_accounting_passed"]["passed"] is False
    assert checks["github_plan_matrix_rejection_accounting_matches_matrix"]["passed"] is True


def test_windows_publish_preflight_blocks_phase2_sample_closure_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        phase2_sample_accounting_closure_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["github_release_plan"]["sample_accounting_closure"][
        "phase2_sample_accounting_closure_status"
    ] == "failed"
    assert checks["github_plan_phase2_sample_accounting_closure_passed"][
        "passed"
    ] is False
    assert checks["github_plan_phase2_sample_accounting_closure_passed"][
        "evidence"
    ]["failed_count"] == 1


def test_windows_publish_preflight_blocks_matrix_sample_closure_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, sample_accounting_closure_ready=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        matrix_sample_accounting_closure_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["matrix_sample_accounting_closure_status"] == "failed"
    assert checks["github_plan_matrix_sample_accounting_closure_passed"][
        "passed"
    ] is False
    assert checks["matrix_sample_accounting_closure_passed"]["passed"] is False
    assert checks["github_plan_matrix_sample_closure_matches_matrix"]["passed"] is True


def test_windows_publish_preflight_blocks_default_promotion_sample_closure_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion, sample_accounting_closure_ready=False)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["default_promotion_sample_accounting_closure_status"] == "failed"
    assert checks["default_promotion_sample_accounting_closure_passed"]["passed"] is False
    assert checks["default_promotion_sample_accounting_closure_passed"]["evidence"][
        "failed_items"
    ] == [{"item": "H", "reason": "sample_closure_drift"}]


def test_windows_publish_preflight_blocks_plan_matrix_sample_closure_mismatch(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        matrix_sample_accounting_closure_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["github_plan_matrix_sample_accounting_closure_passed"][
        "passed"
    ] is False
    assert checks["matrix_sample_accounting_closure_passed"]["passed"] is True
    assert checks["github_plan_matrix_sample_closure_matches_matrix"]["passed"] is False


def test_windows_publish_preflight_blocks_missing_matrix_integration_engine_policy(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_integration_engine_policy=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert (
        checks[
            "windows_release_matrix_acceptance_integration_engine_policy_passed"
        ]["passed"]
        is False
    )
    assert (
        checks["windows_release_matrix_pipeline_integration_engine_policy_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["default_promotion_acceptance_integration_engine_policy_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_pipeline_integration_engine_policy_passed"]["passed"]
        is True
    )
    assert (
        checks["matrix_integration_engine_policy_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks[
        "windows_release_matrix_acceptance_integration_engine_policy_passed"
    ]["evidence"] == {
        "ready": None,
        "status": None,
        "check_present": None,
        "check_passed": None,
        "phase2_check_passed": None,
        "non_resident_count": None,
        "failed_count": None,
        "failed_items": [],
    }


def test_windows_publish_preflight_blocks_failed_default_promotion_integration_engine_policy(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(
        promotion,
        acceptance_integration_engine_policy_ready=False,
        pipeline_integration_engine_policy_ready=False,
    )
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert checks["default_promotion_ready"]["passed"] is False
    assert (
        checks[
            "windows_release_matrix_acceptance_integration_engine_policy_passed"
        ]["passed"]
        is True
    )
    assert (
        checks["windows_release_matrix_pipeline_integration_engine_policy_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_acceptance_integration_engine_policy_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["default_promotion_pipeline_integration_engine_policy_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["matrix_integration_engine_policy_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert (
        checks["default_promotion_pipeline_integration_engine_policy_passed"][
            "evidence"
        ]["non_resident_count"]
        == 1
    )


def test_windows_publish_preflight_blocks_missing_matrix_runtime_default(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_stack_engine_runtime_default=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert (
        checks[
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        ]["passed"]
        is False
    )
    assert (
        checks["windows_release_matrix_pipeline_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["default_promotion_acceptance_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_pipeline_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["matrix_stack_engine_runtime_default_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks[
        "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
    ]["evidence"] == {
        "ready": None,
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


def test_windows_publish_preflight_blocks_failed_matrix_runtime_default(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(
        matrix,
        labels=labels,
        acceptance_stack_engine_runtime_default_ready=False,
    )
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is False
    assert (
        checks[
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        ]["passed"]
        is False
    )
    assert (
        checks["windows_release_matrix_pipeline_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_acceptance_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["matrix_stack_engine_runtime_default_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks[
        "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
    ]["evidence"]["failed_masters"] == [
        {
            "group_id": "bias_0",
            "engine_family": "legacy",
            "reason": "legacy_master_accumulator",
        }
    ]


def test_windows_publish_preflight_blocks_default_promotion_runtime_default_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(
        promotion,
        pipeline_stack_engine_runtime_default_ready=False,
    )
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_ready"]["passed"] is False
    assert (
        checks[
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        ]["passed"]
        is True
    )
    assert (
        checks["windows_release_matrix_pipeline_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_acceptance_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks["default_promotion_pipeline_stack_engine_runtime_default_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["matrix_stack_engine_runtime_default_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks[
        "default_promotion_pipeline_stack_engine_runtime_default_passed"
    ]["evidence"]["failed_outputs"] == [
        {
            "item": "H",
            "engine_family": "legacy",
            "reason": "legacy_or_unknown_engine",
        }
    ]


def test_windows_publish_preflight_blocks_missing_matrix_direct_runtime_evidence(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_direct_runtime_evidence=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert checks["default_promotion_ready"]["passed"] is True
    assert checks["windows_release_matrix_direct_acceptance_fastpath_evidence"][
        "passed"
    ] is False
    assert checks["windows_release_matrix_direct_pipeline_calibration_evidence"][
        "passed"
    ] is False
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"][
        "passed"
    ] is True
    assert checks["matrix_direct_runtime_evidence_matches_default_promotion"][
        "passed"
    ] is False
    assert checks["windows_release_matrix_direct_acceptance_fastpath_evidence"][
        "evidence"
    ] == {
        "present": None,
        "ready": None,
        "acceptance_direct_fastpath": None,
        "acceptance_source": None,
        "acceptance_check_count": None,
        "acceptance_failed_check_count": None,
        "acceptance_failed_checks": [],
        "pipeline_direct_calibration": None,
        "pipeline_calibration_source": None,
        "pipeline_generated_for_contract": None,
        "pipeline_path_exists": None,
        "pipeline_resident_native_calibration_artifact": None,
        "pipeline_resident_calibrated_light_count": None,
    }


def test_windows_publish_preflight_blocks_stale_default_direct_fastpath_source(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(
        promotion,
        direct_acceptance_fastpath_source="gate303_handoff_bundle",
    )
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_direct_acceptance_fastpath_evidence"][
        "passed"
    ] is True
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"][
        "passed"
    ] is False
    assert checks["matrix_direct_runtime_evidence_matches_default_promotion"][
        "passed"
    ] is False
    assert checks["default_promotion_direct_acceptance_fastpath_evidence"][
        "evidence"
    ]["acceptance_source"] == "gate303_handoff_bundle"


def test_windows_publish_preflight_blocks_missing_matrix_release_direct_publication_guard(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_release_direct_publication_guard=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert (
        checks["matrix_release_decision_direct_runtime_publication_guard_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks[
            "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is True
    )
    assert (
        checks[
            "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix"
        ]["passed"]
        is False
    )


def test_windows_publish_preflight_blocks_stale_default_release_direct_publication_guard(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(
        promotion,
        release_direct_publication_guard_acceptance_source="gate303_handoff_bundle",
    )
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        checks["matrix_release_decision_direct_runtime_publication_guard_passed"][
            "passed"
        ]
        is True
    )
    assert (
        checks[
            "default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "matrix_release_decision_direct_publication_guard_matches_default_promotion"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["evidence"]["acceptance_source"]
        == "gate303_handoff_bundle"
    )


def test_windows_publish_preflight_blocks_matrix_default_release_direct_guard_mismatch(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(
        matrix,
        labels=labels,
        default_release_direct_publication_guard_ready=False,
    )
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        checks[
            "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["passed"]
        is True
    )
    assert (
        checks[
            "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
        ]["evidence"]["resident_lights"]
        == 0
    )


def test_windows_publish_preflight_blocks_plan_matrix_resident_fastpath_handoff(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        matrix_resident_fastpath_handoff_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        payload["summary"]["github_plan_matrix_resident_fastpath_handoff_ready"]
        is False
    )
    assert (
        checks["github_plan_matrix_resident_fastpath_release_handoff_ready"][
            "passed"
        ]
        is False
    )
    assert checks["matrix_resident_fastpath_release_handoff_ready"]["passed"] is True
    assert (
        checks["github_plan_matrix_resident_fastpath_handoff_matches_matrix"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_matrix_resident_fastpath_handoff(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, resident_fastpath_handoff_ready=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["matrix_resident_fastpath_handoff_ready"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is False
    assert checks["matrix_resident_fastpath_release_handoff_ready"]["passed"] is False
    assert (
        checks["matrix_resident_fastpath_handoff_matches_default_promotion"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_default_promotion_resident_fastpath_handoff(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion, resident_fastpath_handoff_ready=False)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        payload["summary"]["default_promotion_resident_fastpath_handoff_ready"]
        is False
    )
    assert checks["default_promotion_ready"]["passed"] is False
    assert (
        checks["default_promotion_resident_fastpath_release_handoff_ready"][
            "passed"
        ]
        is False
    )
    assert (
        checks["matrix_resident_fastpath_handoff_matches_default_promotion"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_plan_matrix_resident_result_contract(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        matrix_resident_result_contract_ready=False,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        payload["summary"]["github_plan_matrix_resident_result_contract_ready"]
        is False
    )
    assert (
        checks["github_plan_matrix_resident_result_contract_handoff_passed"][
            "passed"
        ]
        is False
    )
    assert checks["matrix_resident_result_contract_handoff_passed"]["passed"] is True
    assert (
        checks["github_plan_matrix_resident_result_contract_matches_matrix"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_matrix_resident_result_contract(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, resident_result_contract_ready=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["matrix_resident_result_contract_ready"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is False
    assert checks["matrix_resident_result_contract_handoff_passed"]["passed"] is False
    assert (
        checks["github_plan_matrix_resident_result_contract_matches_matrix"][
            "passed"
        ]
        is False
    )
    assert (
        checks["matrix_resident_result_contract_matches_default_promotion"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_default_promotion_resident_result_contract(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion, resident_result_contract_ready=False)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        payload["summary"]["default_promotion_resident_result_contract_ready"]
        is False
    )
    assert checks["default_promotion_ready"]["passed"] is False
    assert (
        checks["default_promotion_resident_result_contract_handoff_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["matrix_resident_result_contract_matches_default_promotion"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_phase2_stack_engine_contract_gap(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        phase2_stack_engine_ready=False,
        phase2_stack_engine_gap_count=1,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["github_release_plan"]["stack_engine_contract"]["phase2_status"] == "failed"
    assert checks["github_plan_phase2_stack_engine_default_contract_ready"][
        "passed"
    ] is False
    assert checks["github_plan_stack_engine_contract_agreement_passed"]["passed"] is False
    assert checks["github_plan_phase2_stack_engine_default_contract_ready"]["evidence"][
        "default_gap_count"
    ] == 1


def test_windows_publish_preflight_blocks_plan_matrix_stack_engine_contract_gap(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        matrix_stack_engine_ready=False,
        matrix_stack_engine_gap_count=1,
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["github_plan_matrix_stack_engine_contract_status"] == "failed"
    assert checks["github_plan_matrix_stack_engine_contract_ready"]["passed"] is False
    assert checks["github_plan_matrix_stack_engine_contract_matches_matrix"][
        "passed"
    ] is False
    assert checks["matrix_stack_engine_contract_ready"]["passed"] is True


def test_windows_publish_preflight_blocks_missing_matrix_stack_engine_contract(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_stack_engine_contract=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert checks["matrix_stack_engine_contract_ready"]["passed"] is False
    assert checks["matrix_stack_engine_contract_ready"]["evidence"] == {
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
    assert checks["matrix_stack_engine_contract_matches_default_promotion"][
        "passed"
    ] is False


def test_windows_publish_preflight_blocks_default_promotion_stack_engine_contract_gap(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(
        promotion,
        stack_engine_ready=False,
        stack_engine_gap_count=1,
    )
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["default_promotion_stack_engine_contract_status"] == "failed"
    assert checks["default_promotion_stack_engine_contract_ready"]["passed"] is False
    assert checks["matrix_stack_engine_contract_matches_default_promotion"][
        "passed"
    ] is False
    assert checks["default_promotion_stack_engine_contract_ready"]["evidence"][
        "default_gap_count"
    ] == 1


def test_windows_publish_preflight_blocks_missing_matrix_resident_winsorized_sweep(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_resident_winsorized_sweep=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert checks["matrix_resident_winsorized_sweep_audit_passed"]["passed"] is False
    assert checks["matrix_resident_winsorized_required_frame_passed"]["passed"] is False
    assert checks["matrix_resident_winsorized_sweep_check_count"]["passed"] is False
    assert (
        checks["default_promotion_resident_winsorized_sweep_matches_matrix"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_failed_matrix_resident_winsorized_sweep(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, resident_winsorized_sweep_ready=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["summary"]["matrix_resident_winsorized_sweep_status"] == "failed"
    assert checks["windows_release_matrix_ready"]["passed"] is False
    assert checks["matrix_resident_winsorized_sweep_audit_passed"]["passed"] is False
    assert checks["matrix_resident_winsorized_required_frame_passed"]["passed"] is False
    assert checks["matrix_resident_winsorized_sweep_check_count"]["passed"] is True


def test_windows_publish_preflight_blocks_default_promotion_resident_winsorized_drift(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion, resident_winsorized_sweep_ready=False)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert (
        payload["summary"]["default_promotion_resident_winsorized_sweep_status"]
        == "failed"
    )
    assert checks["default_promotion_ready"]["passed"] is False
    assert (
        checks["default_promotion_resident_winsorized_sweep_audit_passed"]["passed"]
        is False
    )
    assert (
        checks["default_promotion_resident_winsorized_sweep_matches_matrix"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_resident_winsorized_check_count_mismatch(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, resident_winsorized_check_count=26)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["matrix_resident_winsorized_sweep_audit_passed"]["passed"] is True
    assert checks["matrix_resident_winsorized_sweep_check_count"]["passed"] is True
    assert (
        checks["default_promotion_resident_winsorized_sweep_matches_matrix"][
            "passed"
        ]
        is False
    )


def test_windows_publish_preflight_blocks_missing_matrix_stack_publication_audit(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, include_stack_publication_audit=False)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is True
    assert checks["matrix_stack_engine_publication_audit_passed"]["passed"] is False
    assert (
        checks["matrix_stack_engine_publication_policy_chain_passed"]["passed"]
        is False
    )
    assert (
        checks[
            "matrix_stack_engine_publication_resident_winsorized_chain_passed"
        ]["passed"]
        is False
    )
    assert (
        checks["default_promotion_stack_engine_publication_audit_passed"]["passed"]
        is True
    )
    assert (
        checks["matrix_stack_engine_publication_audit_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks["matrix_stack_engine_publication_audit_passed"]["evidence"] == {
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


def test_windows_publish_preflight_blocks_default_promotion_publication_policy_chain(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion, stack_publication_policy_ready=False)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["default_promotion_ready"]["passed"] is False
    assert checks["matrix_stack_engine_publication_audit_passed"]["passed"] is True
    assert (
        checks["default_promotion_stack_engine_publication_audit_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks["default_promotion_stack_engine_publication_policy_chain_passed"][
            "passed"
        ]
        is False
    )
    assert (
        checks[
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
        ]["passed"]
        is True
    )
    assert (
        checks["matrix_stack_engine_publication_audit_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks[
        "default_promotion_stack_engine_publication_policy_chain_passed"
    ]["evidence"] == {
        "phase2_check_passed": False,
        "publish_preflight_policy_ready": False,
        "phase2_policy_ready": False,
        "policy_agreement": False,
    }


def test_windows_publish_preflight_blocks_stack_publication_winsorized_mismatch(
    tmp_path: Path,
):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(
        matrix,
        labels=labels,
        stack_publication_resident_winsorized_ready=False,
    )
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"]["passed"] is False
    assert checks["matrix_stack_engine_publication_policy_chain_passed"]["passed"] is True
    assert (
        checks[
            "matrix_stack_engine_publication_resident_winsorized_chain_passed"
        ]["passed"]
        is False
    )
    assert (
        checks[
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
        ]["passed"]
        is True
    )
    assert (
        checks["matrix_stack_engine_publication_audit_matches_default_promotion"][
            "passed"
        ]
        is False
    )
    assert checks[
        "matrix_stack_engine_publication_resident_winsorized_chain_passed"
    ]["evidence"] == {
        "phase2_check_passed": False,
        "publish_preflight_resident_winsorized_ready": False,
        "phase2_resident_winsorized_ready": False,
        "resident_winsorized_agreement": False,
    }


def test_windows_publish_preflight_cli_writes_outputs(tmp_path: Path):
    manifest, plan, matrix, promotion = _bundle(tmp_path)
    out = tmp_path / "publish_preflight.json"
    markdown = tmp_path / "publish_preflight.md"

    result = main(
        [
            "windows-publish-preflight",
            "--release-manifest",
            str(manifest),
            "--github-release-plan",
            str(plan),
            "--windows-release-matrix",
            str(matrix),
            "--default-promotion-manifest",
            str(promotion),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "publish_preflight_ready"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows Publish Preflight" in markdown_text
    assert "Default route checks/speedup: `4`/`28.75`" in markdown_text
    assert "Rejection sample accounting: phase2 `passed`" in markdown_text
    assert "Sample accounting closure: phase2 `passed`" in markdown_text
    assert (
        "Integration engine policy: matrix `True`/`passed`/`passed`, "
        "default-promotion `True`/`passed`/`passed`"
    ) in markdown_text
    assert (
        "StackEngine runtime default: matrix `True`/`passed`/`passed`, "
        "default-promotion `True`/`passed`/`passed`"
    ) in markdown_text
    assert (
        "Runtime default drift counters: matrix acceptance-legacy `0`, "
        "matrix pipeline-failed-output `0`, default-promotion acceptance-legacy `0`, "
        "default-promotion pipeline-failed-output `0`"
    ) in markdown_text
    assert "Release direct publication guard: plan-matrix `True`/`200`" in markdown_text
    assert (
        "Resident result contract: plan-matrix `True`/`passed`/`True`/`1`/`0`, "
        "matrix `True`/`passed`/`True`/`1`/`0`, "
        "default-promotion `True`/`passed`/`True`/`1`/`0`"
    ) in markdown_text
    assert "StackEngine default contract: phase2 `passed`" in markdown_text
    assert "StackEngine default gaps: matrix `0`, default-promotion `0`" in markdown_text
    assert (
        "Resident winsorized sweep: matrix `passed`/`200`/`True`/`27`, "
        "default-promotion `passed`/`200`/`True`/`27`"
    ) in markdown_text
    assert (
        "StackEngine publication audit: matrix `passed`/`True`/`True`/`True`, "
        "default-promotion `passed`/`True`/`True`/`True`"
    ) in markdown_text
    assert "manifest_assets_match_github_plan" in markdown_text
    assert "github_plan_phase2_stack_engine_default_contract_ready" in markdown_text
    assert (
        "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        in markdown_text
    )
    assert "matrix_stack_engine_runtime_default_matches_default_promotion" in markdown_text
    assert "matrix_resident_winsorized_sweep_audit_passed" in markdown_text
    assert "matrix_stack_engine_publication_audit_passed" in markdown_text
    assert "matrix_resident_result_contract_handoff_passed" in markdown_text
