from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.gpu.compatibility import WINDOWS_CUDA_PACKAGES
from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_json_object_optional(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return _read_json_object(path)


def _check_passed(payload: dict[str, Any], name: str) -> bool | None:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return item.get("passed") is True
    return None


def _direct_publication_guard_from_decision(
    decision: dict[str, Any],
    *,
    min_resident_lights: int = 200,
) -> dict[str, Any]:
    direct = (
        decision.get("stack_engine_publication_direct_runtime_evidence")
        if isinstance(
            decision.get("stack_engine_publication_direct_runtime_evidence"),
            dict,
        )
        else {}
    )
    raw_lights = _int_value(direct.get("raw_matrix_pipeline_resident_lights"))
    default_lights = _int_value(
        direct.get("raw_default_promotion_pipeline_resident_lights")
    )
    phase2_lights = _int_value(direct.get("phase2_matrix_pipeline_resident_lights"))
    phase2_default_lights = _int_value(
        direct.get("phase2_default_promotion_pipeline_resident_lights")
    )
    check_passed = _check_passed(
        decision,
        "stack_engine_publication_direct_runtime_evidence_passed",
    )
    source_ready = (
        direct.get("raw_source_ready") is True
        and direct.get("phase2_source_ready") is True
        and direct.get("raw_matrix_acceptance_source")
        == "explicit_resident_artifacts_json"
        and direct.get("phase2_matrix_acceptance_source")
        == "explicit_resident_artifacts_json"
        and direct.get("raw_matrix_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
        and direct.get("phase2_matrix_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
    )
    count_ready = (
        direct.get("raw_count_ready") is True
        and direct.get("phase2_count_ready") is True
        and raw_lights is not None
        and raw_lights >= int(min_resident_lights)
        and default_lights is not None
        and default_lights >= int(min_resident_lights)
        and phase2_lights is not None
        and phase2_lights >= int(min_resident_lights)
        and phase2_default_lights is not None
        and phase2_default_lights >= int(min_resident_lights)
    )
    ready = (
        bool(direct)
        and check_passed is True
        and direct.get("ready") is True
        and direct.get("checks_passed") is True
        and source_ready
        and count_ready
        and direct.get("raw_leaf_checks_ready") is True
        and direct.get("phase2_leaf_checks_ready") is True
    )
    return {
        "present": bool(direct),
        "ready": ready,
        "decision_check_passed": check_passed,
        "checks_passed": direct.get("checks_passed"),
        "source_ready": source_ready,
        "count_ready": count_ready,
        "raw_leaf_checks_ready": direct.get("raw_leaf_checks_ready"),
        "phase2_leaf_checks_ready": direct.get("phase2_leaf_checks_ready"),
        "raw_acceptance_source": direct.get("raw_matrix_acceptance_source"),
        "phase2_acceptance_source": direct.get("phase2_matrix_acceptance_source"),
        "raw_calibration_source": direct.get(
            "raw_matrix_pipeline_calibration_source"
        ),
        "phase2_calibration_source": direct.get(
            "phase2_matrix_pipeline_calibration_source"
        ),
        "raw_resident_lights": raw_lights,
        "raw_default_promotion_resident_lights": default_lights,
        "phase2_resident_lights": phase2_lights,
        "phase2_default_promotion_resident_lights": phase2_default_lights,
        "required_min_resident_lights": int(min_resident_lights),
    }


def _quality_publication_guard_from_decision(decision: dict[str, Any]) -> dict[str, Any]:
    quality = (
        decision.get("stack_engine_publication_quality_metrics_compare")
        if isinstance(
            decision.get("stack_engine_publication_quality_metrics_compare"),
            dict,
        )
        else {}
    )
    check_passed = _check_passed(
        decision,
        "stack_engine_publication_quality_metrics_compare_passed",
    )
    present = bool(quality)
    compatible_missing = not present or quality.get("compatible_missing") is True
    quality_compare_present = quality.get("quality_compare_present") is True
    decision_check_ready = check_passed is True or (
        check_passed is None and compatible_missing and not quality_compare_present
    )
    checks_ready = quality.get("checks_passed") is True or compatible_missing
    layers_ready = (
        not quality_compare_present
        or (
            quality.get("raw_present") is True
            and quality.get("phase2_present") is True
            and quality.get("raw_ready") is True
            and quality.get("phase2_ready") is True
        )
    )
    ready = not present or (
        quality.get("ready") is True
        and decision_check_ready
        and checks_ready
        and layers_ready
    )
    return {
        "present": present,
        "ready": ready,
        "decision_check_passed": check_passed,
        "status": quality.get("status"),
        "passed": quality.get("passed"),
        "checks_passed": quality.get("checks_passed"),
        "compatible_missing": compatible_missing,
        "quality_compare_present": quality_compare_present,
        "decision_check_ready": decision_check_ready,
        "checks_ready": checks_ready,
        "layers_ready": layers_ready,
        "raw_present": quality.get("raw_present"),
        "raw_ready": quality.get("raw_ready"),
        "raw_matrix_status": quality.get("raw_matrix_status"),
        "raw_matrix_failed_check_count": _int_value(
            quality.get("raw_matrix_failed_check_count")
        ),
        "phase2_present": quality.get("phase2_present"),
        "phase2_ready": quality.get("phase2_ready"),
        "phase2_check_passed": quality.get("phase2_check_passed"),
        "phase2_matrix_status": quality.get("phase2_matrix_status"),
        "phase2_matrix_failed_check_count": _int_value(
            quality.get("phase2_matrix_failed_check_count")
        ),
        "failed_checks": quality.get("failed_checks") or [],
    }


def _release_quality_publication_guard_from_decision(
    decision: dict[str, Any],
) -> dict[str, Any]:
    guard = (
        decision.get("stack_engine_publication_release_quality_guard")
        if isinstance(
            decision.get("stack_engine_publication_release_quality_guard"),
            dict,
        )
        else {}
    )
    check_passed = _check_passed(
        decision,
        "stack_engine_publication_release_quality_guard_passed",
    )
    present = bool(guard)
    compatible_missing = not present or guard.get("compatible_missing") is True
    release_quality_guard_present = guard.get("release_quality_guard_present") is True
    final_field_names = (
        "final_checks_compatible_missing",
        "final_checks_ready",
        "final_checks_match",
        "raw_final_checks_present",
        "raw_final_checks_ready",
        "phase2_final_checks_present",
        "phase2_final_checks_ready",
        "raw_release_matrix_check",
        "raw_release_matrix_default_check",
        "raw_release_default_promotion_check",
        "raw_release_matrix_default_match_check",
        "raw_release_matrix_manifest_match_check",
        "phase2_release_matrix_check",
        "phase2_release_matrix_default_check",
        "phase2_release_default_promotion_check",
        "phase2_release_matrix_default_match_check",
        "phase2_release_matrix_manifest_match_check",
    )
    final_fields_present = any(guard.get(field) is not None for field in final_field_names)
    final_checks_compatible_missing = (
        guard.get("final_checks_compatible_missing") is True
        or not final_fields_present
    )
    final_checks_ready = (
        guard.get("final_checks_ready") is True
        or final_checks_compatible_missing
    )
    final_checks_match = (
        guard.get("final_checks_match") is True
        or final_checks_compatible_missing
    )
    raw_final_checks_ready = (
        guard.get("raw_final_checks_ready") is True
        or final_checks_compatible_missing
    )
    phase2_final_checks_ready = (
        guard.get("phase2_final_checks_ready") is True
        or final_checks_compatible_missing
    )
    decision_check_ready = check_passed is True or (
        check_passed is None and compatible_missing and not release_quality_guard_present
    )
    checks_ready = guard.get("checks_passed") is True or compatible_missing
    layers_ready = (
        not release_quality_guard_present
        or (
            guard.get("raw_present") is True
            and guard.get("phase2_present") is True
            and guard.get("raw_ready") is True
            and guard.get("phase2_ready") is True
            and final_checks_ready
            and final_checks_match
            and raw_final_checks_ready
            and phase2_final_checks_ready
        )
    )
    ready = not present or (
        guard.get("ready") is True
        and decision_check_ready
        and checks_ready
        and layers_ready
    )
    return {
        "present": present,
        "ready": ready,
        "decision_check_passed": check_passed,
        "status": guard.get("status"),
        "passed": guard.get("passed"),
        "checks_passed": guard.get("checks_passed"),
        "compatible_missing": compatible_missing,
        "release_quality_guard_present": release_quality_guard_present,
        "final_fields_present": final_fields_present,
        "final_checks_compatible_missing": final_checks_compatible_missing,
        "final_checks_ready": final_checks_ready,
        "final_checks_match": final_checks_match,
        "raw_final_checks_present": guard.get("raw_final_checks_present"),
        "raw_final_checks_ready": guard.get("raw_final_checks_ready"),
        "phase2_final_checks_present": guard.get("phase2_final_checks_present"),
        "phase2_final_checks_ready": guard.get("phase2_final_checks_ready"),
        "decision_check_ready": decision_check_ready,
        "checks_ready": checks_ready,
        "layers_ready": layers_ready,
        "raw_present": guard.get("raw_present"),
        "raw_ready": guard.get("raw_ready"),
        "raw_matrix_raw_status": guard.get("raw_matrix_raw_status"),
        "raw_matrix_phase2_status": guard.get("raw_matrix_phase2_status"),
        "raw_matrix_check_passed": guard.get("raw_matrix_check_passed"),
        "raw_matrix_layers_ready": guard.get("raw_matrix_layers_ready"),
        "raw_default_promotion_raw_status": guard.get(
            "raw_default_promotion_raw_status"
        ),
        "raw_default_promotion_phase2_status": guard.get(
            "raw_default_promotion_phase2_status"
        ),
        "raw_default_promotion_check_passed": guard.get(
            "raw_default_promotion_check_passed"
        ),
        "raw_default_promotion_layers_ready": guard.get(
            "raw_default_promotion_layers_ready"
        ),
        "raw_matrix_check": guard.get("raw_matrix_check"),
        "raw_matrix_default_check": guard.get("raw_matrix_default_check"),
        "raw_default_promotion_check": guard.get("raw_default_promotion_check"),
        "raw_matrix_default_match_check": guard.get(
            "raw_matrix_default_match_check"
        ),
        "raw_matrix_manifest_match_check": guard.get(
            "raw_matrix_manifest_match_check"
        ),
        "raw_release_matrix_check": guard.get("raw_release_matrix_check"),
        "raw_release_matrix_default_check": guard.get(
            "raw_release_matrix_default_check"
        ),
        "raw_release_default_promotion_check": guard.get(
            "raw_release_default_promotion_check"
        ),
        "raw_release_matrix_default_match_check": guard.get(
            "raw_release_matrix_default_match_check"
        ),
        "raw_release_matrix_manifest_match_check": guard.get(
            "raw_release_matrix_manifest_match_check"
        ),
        "phase2_present": guard.get("phase2_present"),
        "phase2_ready": guard.get("phase2_ready"),
        "phase2_check_passed": guard.get("phase2_check_passed"),
        "phase2_matrix_raw_status": guard.get("phase2_matrix_raw_status"),
        "phase2_matrix_phase2_status": guard.get("phase2_matrix_phase2_status"),
        "phase2_matrix_check_passed": guard.get("phase2_matrix_check_passed"),
        "phase2_matrix_layers_ready": guard.get("phase2_matrix_layers_ready"),
        "phase2_default_promotion_raw_status": guard.get(
            "phase2_default_promotion_raw_status"
        ),
        "phase2_default_promotion_phase2_status": guard.get(
            "phase2_default_promotion_phase2_status"
        ),
        "phase2_default_promotion_check_passed": guard.get(
            "phase2_default_promotion_check_passed"
        ),
        "phase2_default_promotion_layers_ready": guard.get(
            "phase2_default_promotion_layers_ready"
        ),
        "phase2_matrix_check": guard.get("phase2_matrix_check"),
        "phase2_matrix_default_check": guard.get("phase2_matrix_default_check"),
        "phase2_default_promotion_check": guard.get("phase2_default_promotion_check"),
        "phase2_matrix_default_match_check": guard.get(
            "phase2_matrix_default_match_check"
        ),
        "phase2_matrix_manifest_match_check": guard.get(
            "phase2_matrix_manifest_match_check"
        ),
        "phase2_release_matrix_check": guard.get("phase2_release_matrix_check"),
        "phase2_release_matrix_default_check": guard.get(
            "phase2_release_matrix_default_check"
        ),
        "phase2_release_default_promotion_check": guard.get(
            "phase2_release_default_promotion_check"
        ),
        "phase2_release_matrix_default_match_check": guard.get(
            "phase2_release_matrix_default_match_check"
        ),
        "phase2_release_matrix_manifest_match_check": guard.get(
            "phase2_release_matrix_manifest_match_check"
        ),
        "failed_checks": guard.get("failed_checks") or [],
    }


def _default_promotion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return {"present": False}
    default_route = (
        payload.get("default_route_acceptance")
        if isinstance(payload.get("default_route_acceptance"), dict)
        else {}
    )
    default_candidate = (
        payload.get("default_candidate") if isinstance(payload.get("default_candidate"), dict) else {}
    )
    pipeline = payload.get("pipeline_contract") if isinstance(payload.get("pipeline_contract"), dict) else {}
    integration_engine_policy = (
        payload.get("integration_engine_policy")
        if isinstance(payload.get("integration_engine_policy"), dict)
        else {}
    )
    stack_engine_runtime_default = (
        payload.get("stack_engine_runtime_default")
        if isinstance(payload.get("stack_engine_runtime_default"), dict)
        else {}
    )
    rejection_sample_accounting = (
        pipeline.get("rejection_sample_accounting")
        if isinstance(pipeline.get("rejection_sample_accounting"), dict)
        else {}
    )
    sample_accounting_closure = (
        pipeline.get("sample_accounting_closure")
        if isinstance(pipeline.get("sample_accounting_closure"), dict)
        else {}
    )
    resident_result_contract = (
        payload.get("resident_result_contract")
        if isinstance(payload.get("resident_result_contract"), dict)
        else {}
    )
    stack_engine = (
        payload.get("stack_engine_contract")
        if isinstance(payload.get("stack_engine_contract"), dict)
        else {}
    )
    resident_winsorized_sweep = (
        payload.get("resident_winsorized_sweep_audit")
        if isinstance(payload.get("resident_winsorized_sweep_audit"), dict)
        else {}
    )
    publication_audit = (
        payload.get("stack_engine_publication_audit")
        if isinstance(payload.get("stack_engine_publication_audit"), dict)
        else {}
    )
    direct_evidence = (
        payload.get("runtime_default_direct_evidence")
        if isinstance(payload.get("runtime_default_direct_evidence"), dict)
        else {}
    )
    release_direct_publication_guard = (
        payload.get("release_decision_direct_runtime_publication_guard")
        if isinstance(
            payload.get("release_decision_direct_runtime_publication_guard"),
            dict,
        )
        else {}
    )
    release_quality_publication_guard = (
        payload.get("release_decision_quality_compare_publication_guard")
        if isinstance(
            payload.get("release_decision_quality_compare_publication_guard"),
            dict,
        )
        else {}
    )
    release_quality_guard_publication_guard = (
        payload.get("release_decision_release_quality_publication_guard")
        if isinstance(
            payload.get("release_decision_release_quality_publication_guard"),
            dict,
        )
        else {}
    )
    quality_metrics_compare = (
        payload.get("quality_metrics_compare")
        if isinstance(payload.get("quality_metrics_compare"), dict)
        else {}
    )
    resident_fastpath_handoff = (
        payload.get("resident_registration_fastpath_release_handoff")
        if isinstance(
            payload.get("resident_registration_fastpath_release_handoff"),
            dict,
        )
        else {}
    )
    return {
        "present": True,
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "default_change_ready": payload.get("default_change_ready"),
        "recommendation": payload.get("recommendation"),
        "default_memory_mode": default_candidate.get("memory_mode"),
        "fallback_memory_mode": default_candidate.get("fallback_memory_mode"),
        "resident_runtime_preset": default_candidate.get("resident_runtime_preset"),
        "integration_engine": default_candidate.get("integration_engine"),
        "default_route_present": default_route.get("present"),
        "default_route_passed": default_route.get("passed"),
        "default_route_route_contract_passed": default_route.get("route_contract_passed"),
        "default_route_route_check_count": default_route.get("route_check_count"),
        "default_route_speedup_vs_reference": default_route.get("speedup_vs_reference"),
        "quality_metrics_compare": quality_metrics_compare,
        "quality_metrics_compare_present": quality_metrics_compare.get("present"),
        "quality_metrics_compare_ready": quality_metrics_compare.get("ready"),
        "quality_metrics_compare_status": quality_metrics_compare.get("status"),
        "quality_metrics_compare_passed": quality_metrics_compare.get("passed"),
        "quality_metrics_compare_phase2_check_passed": quality_metrics_compare.get(
            "phase2_check_passed"
        ),
        "quality_metrics_compare_failed_check_count": _int_value(
            quality_metrics_compare.get("failed_check_count")
        ),
        "quality_metrics_compare_failed_checks": (
            quality_metrics_compare.get("failed_checks") or []
        ),
        "quality_metrics_compare_threshold_failure_count": _int_value(
            quality_metrics_compare.get("threshold_failure_count")
        ),
        "quality_metrics_compare_threshold_failures": (
            quality_metrics_compare.get("threshold_failures") or []
        ),
        "pipeline_contract_status": pipeline.get("status"),
        "pipeline_contract_passed": pipeline.get("passed"),
        "integration_rejection_sample_counts_match_maps": pipeline.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "integration_sample_accounting_closure": pipeline.get(
            "integration_sample_accounting_closure"
        ),
        "resident_result_contract": resident_result_contract,
        "resident_result_contract_present": resident_result_contract.get("present"),
        "resident_result_contract_ready": resident_result_contract.get("ready"),
        "resident_result_contract_status": resident_result_contract.get("status"),
        "resident_result_contract_top_level_check": resident_result_contract.get(
            "top_level_check"
        ),
        "resident_result_contract_check_present": resident_result_contract.get(
            "check_present"
        ),
        "resident_result_contract_check_passed": resident_result_contract.get(
            "check_passed"
        ),
        "resident_result_contract_phase2_check_passed": resident_result_contract.get(
            "phase2_check_passed"
        ),
        "resident_result_contract_required_count": _int_value(
            resident_result_contract.get("required_count")
        ),
        "resident_result_contract_failed_count": _int_value(
            resident_result_contract.get("failed_count")
        ),
        "resident_result_contract_failed_check_count": _int_value(
            resident_result_contract.get("failed_check_count")
        ),
        "resident_result_contract_failed_checks": (
            resident_result_contract.get("failed_checks") or []
        ),
        "resident_result_contract_failed_items": (
            resident_result_contract.get("failed_items") or []
        ),
        "integration_engine_policy": integration_engine_policy,
        "integration_engine_policy_ready": integration_engine_policy.get("ready"),
        "acceptance_integration_engine_policy_status": integration_engine_policy.get(
            "acceptance_status"
        ),
        "acceptance_integration_engine_policy_check_present": integration_engine_policy.get(
            "acceptance_check_present"
        ),
        "acceptance_integration_engine_policy_check_passed": integration_engine_policy.get(
            "acceptance_check_passed"
        ),
        "acceptance_integration_engine_policy_phase2_check_passed": integration_engine_policy.get(
            "acceptance_phase2_check_passed"
        ),
        "acceptance_integration_engine_policy_non_resident_count": integration_engine_policy.get(
            "acceptance_non_resident_count"
        ),
        "acceptance_integration_engine_policy_failed_count": integration_engine_policy.get(
            "acceptance_failed_count"
        ),
        "acceptance_integration_engine_policy_failed_items": integration_engine_policy.get(
            "acceptance_failed_items"
        )
        or [],
        "pipeline_integration_engine_policy_status": integration_engine_policy.get(
            "pipeline_status"
        ),
        "pipeline_integration_engine_policy_check_present": integration_engine_policy.get(
            "pipeline_check_present"
        ),
        "pipeline_integration_engine_policy_check_passed": integration_engine_policy.get(
            "pipeline_check_passed"
        ),
        "pipeline_integration_engine_policy_phase2_check_passed": integration_engine_policy.get(
            "pipeline_phase2_check_passed"
        ),
        "pipeline_integration_engine_policy_default_engine_policy": integration_engine_policy.get(
            "pipeline_default_engine_policy"
        ),
        "pipeline_integration_engine_policy_non_resident_count": integration_engine_policy.get(
            "pipeline_non_resident_count"
        ),
        "pipeline_integration_engine_policy_failed_count": integration_engine_policy.get(
            "pipeline_failed_count"
        ),
        "pipeline_integration_engine_policy_failed_items": integration_engine_policy.get(
            "pipeline_failed_items"
        )
        or [],
        "stack_engine_runtime_default": stack_engine_runtime_default,
        "stack_engine_runtime_default_ready": stack_engine_runtime_default.get("ready"),
        "acceptance_stack_engine_runtime_default_status": stack_engine_runtime_default.get(
            "acceptance_status"
        ),
        "acceptance_stack_engine_runtime_default_check_present": stack_engine_runtime_default.get(
            "acceptance_check_present"
        ),
        "acceptance_stack_engine_runtime_default_check_passed": stack_engine_runtime_default.get(
            "acceptance_check_passed"
        ),
        "acceptance_stack_engine_runtime_default_phase2_check_passed": stack_engine_runtime_default.get(
            "acceptance_phase2_check_passed"
        ),
        "acceptance_stack_engine_runtime_default_master_count": stack_engine_runtime_default.get(
            "acceptance_master_count"
        ),
        "acceptance_stack_engine_runtime_default_legacy_master_count": _int_value(
            stack_engine_runtime_default.get("acceptance_legacy_master_count")
        ),
        "acceptance_stack_engine_runtime_default_failed_master_count": _int_value(
            stack_engine_runtime_default.get("acceptance_failed_master_count")
        ),
        "acceptance_stack_engine_runtime_default_failed_output_count": _int_value(
            stack_engine_runtime_default.get("acceptance_failed_output_count")
        ),
        "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            stack_engine_runtime_default.get(
                "acceptance_explicit_cuda_fast_path_count"
            )
        ),
        "acceptance_stack_engine_runtime_default_failed_masters": (
            stack_engine_runtime_default.get("acceptance_failed_masters") or []
        ),
        "acceptance_stack_engine_runtime_default_failed_outputs": (
            stack_engine_runtime_default.get("acceptance_failed_outputs") or []
        ),
        "pipeline_stack_engine_runtime_default_status": stack_engine_runtime_default.get(
            "pipeline_status"
        ),
        "pipeline_stack_engine_runtime_default_check_present": stack_engine_runtime_default.get(
            "pipeline_check_present"
        ),
        "pipeline_stack_engine_runtime_default_check_passed": stack_engine_runtime_default.get(
            "pipeline_check_passed"
        ),
        "pipeline_stack_engine_runtime_default_phase2_check_passed": stack_engine_runtime_default.get(
            "pipeline_phase2_check_passed"
        ),
        "pipeline_stack_engine_runtime_default_master_count": stack_engine_runtime_default.get(
            "pipeline_master_count"
        ),
        "pipeline_stack_engine_runtime_default_legacy_master_count": _int_value(
            stack_engine_runtime_default.get("pipeline_legacy_master_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_master_count": _int_value(
            stack_engine_runtime_default.get("pipeline_failed_master_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_output_count": _int_value(
            stack_engine_runtime_default.get("pipeline_failed_output_count")
        ),
        "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            stack_engine_runtime_default.get("pipeline_explicit_cuda_fast_path_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_masters": (
            stack_engine_runtime_default.get("pipeline_failed_masters") or []
        ),
        "pipeline_stack_engine_runtime_default_failed_outputs": (
            stack_engine_runtime_default.get("pipeline_failed_outputs") or []
        ),
        "runtime_default_direct_evidence": direct_evidence,
        "runtime_default_direct_evidence_present": direct_evidence.get("present"),
        "runtime_default_direct_evidence_ready": direct_evidence.get("ready"),
        "runtime_default_direct_acceptance_fastpath": direct_evidence.get(
            "acceptance_direct_fastpath"
        ),
        "runtime_default_direct_acceptance_fastpath_source": direct_evidence.get(
            "acceptance_fastpath_source"
        ),
        "runtime_default_direct_acceptance_fastpath_check_count": _int_value(
            direct_evidence.get("acceptance_fastpath_check_count")
        ),
        "runtime_default_direct_acceptance_fastpath_failed_check_count": _int_value(
            direct_evidence.get("acceptance_fastpath_failed_check_count")
        ),
        "runtime_default_direct_acceptance_fastpath_failed_checks": (
            direct_evidence.get("acceptance_fastpath_failed_checks") or []
        ),
        "runtime_default_direct_pipeline_calibration": direct_evidence.get(
            "pipeline_direct_resident_calibration"
        ),
        "runtime_default_direct_pipeline_calibration_source": direct_evidence.get(
            "pipeline_calibration_artifact_source"
        ),
        "runtime_default_direct_pipeline_calibration_generated_for_contract": (
            direct_evidence.get("pipeline_calibration_artifact_generated_for_contract")
        ),
        "runtime_default_direct_pipeline_calibration_path_exists": (
            direct_evidence.get("pipeline_calibration_artifact_path_exists")
        ),
        "runtime_default_direct_pipeline_resident_native_calibration_artifact": (
            direct_evidence.get("pipeline_resident_native_calibration_artifact")
        ),
        "runtime_default_direct_pipeline_resident_calibrated_light_count": (
            _int_value(direct_evidence.get("pipeline_resident_calibrated_light_count"))
        ),
        "release_decision_direct_runtime_publication_guard": (
            release_direct_publication_guard
        ),
        "release_decision_direct_runtime_publication_guard_present": (
            release_direct_publication_guard.get("present")
        ),
        "release_decision_direct_runtime_publication_guard_ready": (
            release_direct_publication_guard.get("ready")
        ),
        "release_decision_direct_runtime_publication_guard_check_passed": (
            release_direct_publication_guard.get("decision_check_passed")
        ),
        "release_decision_direct_runtime_publication_guard_source_ready": (
            release_direct_publication_guard.get("source_ready")
        ),
        "release_decision_direct_runtime_publication_guard_count_ready": (
            release_direct_publication_guard.get("count_ready")
        ),
        "release_decision_direct_runtime_publication_guard_leaf_checks_ready": (
            release_direct_publication_guard.get("leaf_checks_ready")
        ),
        "release_decision_direct_runtime_publication_guard_raw_acceptance_source": (
            release_direct_publication_guard.get("raw_matrix_acceptance_source")
        ),
        "release_decision_direct_runtime_publication_guard_raw_calibration_source": (
            release_direct_publication_guard.get(
                "raw_matrix_pipeline_calibration_source"
            )
        ),
        "release_decision_direct_runtime_publication_guard_raw_resident_lights": (
            _int_value(
                release_direct_publication_guard.get(
                    "raw_matrix_pipeline_resident_lights"
                )
            )
        ),
        "release_decision_quality_compare_publication_guard": (
            release_quality_publication_guard
        ),
        "release_decision_quality_compare_publication_guard_present": (
            release_quality_publication_guard.get("present")
        ),
        "release_decision_quality_compare_publication_guard_ready": (
            release_quality_publication_guard.get("ready")
        ),
        "release_decision_quality_compare_publication_guard_check_passed": (
            release_quality_publication_guard.get("decision_check_passed")
        ),
        "release_decision_quality_compare_publication_guard_quality_present": (
            release_quality_publication_guard.get("quality_compare_present")
        ),
        "release_decision_quality_compare_publication_guard_compatible_missing": (
            release_quality_publication_guard.get("compatible_missing")
        ),
        "release_decision_quality_compare_publication_guard_layers_ready": (
            release_quality_publication_guard.get("layers_ready")
        ),
        "release_decision_quality_compare_publication_guard_raw_status": (
            release_quality_publication_guard.get("raw_matrix_status")
        ),
        "release_decision_quality_compare_publication_guard_raw_failed_count": (
            _int_value(
                release_quality_publication_guard.get(
                    "raw_matrix_failed_check_count"
                )
            )
        ),
        "release_decision_quality_compare_publication_guard_phase2_status": (
            release_quality_publication_guard.get("phase2_matrix_status")
        ),
        "release_decision_quality_compare_publication_guard_phase2_failed_count": (
            _int_value(
                release_quality_publication_guard.get(
                    "phase2_matrix_failed_check_count"
                )
            )
        ),
        "release_decision_release_quality_publication_guard": (
            release_quality_guard_publication_guard
        ),
        "release_decision_release_quality_publication_guard_present": (
            release_quality_guard_publication_guard.get("present")
        ),
        "release_decision_release_quality_publication_guard_ready": (
            release_quality_guard_publication_guard.get("ready")
        ),
        "release_decision_release_quality_publication_guard_check_passed": (
            release_quality_guard_publication_guard.get("decision_check_passed")
        ),
        "release_decision_release_quality_publication_guard_status": (
            release_quality_guard_publication_guard.get("status")
        ),
        "release_decision_release_quality_publication_guard_passed": (
            release_quality_guard_publication_guard.get("passed")
        ),
        "release_decision_release_quality_publication_guard_checks_passed": (
            release_quality_guard_publication_guard.get("checks_passed")
        ),
        "release_decision_release_quality_publication_guard_compatible_missing": (
            release_quality_guard_publication_guard.get("compatible_missing")
        ),
        "release_decision_release_quality_publication_guard_release_quality_present": (
            release_quality_guard_publication_guard.get(
                "release_quality_guard_present"
            )
        ),
        "release_decision_release_quality_publication_guard_decision_check_ready": (
            release_quality_guard_publication_guard.get("decision_check_ready")
        ),
        "release_decision_release_quality_publication_guard_checks_ready": (
            release_quality_guard_publication_guard.get("checks_ready")
        ),
        "release_decision_release_quality_publication_guard_layers_ready": (
            release_quality_guard_publication_guard.get("layers_ready")
        ),
        "release_decision_release_quality_publication_guard_raw_present": (
            release_quality_guard_publication_guard.get("raw_present")
        ),
        "release_decision_release_quality_publication_guard_raw_ready": (
            release_quality_guard_publication_guard.get("raw_ready")
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_raw_status": (
            release_quality_guard_publication_guard.get("raw_matrix_raw_status")
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_phase2_status": (
            release_quality_guard_publication_guard.get("raw_matrix_phase2_status")
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_check_passed": (
            release_quality_guard_publication_guard.get("raw_matrix_check_passed")
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_layers_ready": (
            release_quality_guard_publication_guard.get("raw_matrix_layers_ready")
        ),
        "release_decision_release_quality_publication_guard_raw_default_promotion_raw_status": (
            release_quality_guard_publication_guard.get(
                "raw_default_promotion_raw_status"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_default_promotion_phase2_status": (
            release_quality_guard_publication_guard.get(
                "raw_default_promotion_phase2_status"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_default_promotion_check_passed": (
            release_quality_guard_publication_guard.get(
                "raw_default_promotion_check_passed"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_default_promotion_layers_ready": (
            release_quality_guard_publication_guard.get(
                "raw_default_promotion_layers_ready"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_check": (
            release_quality_guard_publication_guard.get("raw_matrix_check")
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_default_check": (
            release_quality_guard_publication_guard.get("raw_matrix_default_check")
        ),
        "release_decision_release_quality_publication_guard_raw_default_promotion_check": (
            release_quality_guard_publication_guard.get(
                "raw_default_promotion_check"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_default_match_check": (
            release_quality_guard_publication_guard.get(
                "raw_matrix_default_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_matrix_manifest_match_check": (
            release_quality_guard_publication_guard.get(
                "raw_matrix_manifest_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_final_fields_present": (
            release_quality_guard_publication_guard.get("final_fields_present")
        ),
        "release_decision_release_quality_publication_guard_final_checks_compatible_missing": (
            release_quality_guard_publication_guard.get(
                "final_checks_compatible_missing"
            )
        ),
        "release_decision_release_quality_publication_guard_final_checks_ready": (
            release_quality_guard_publication_guard.get("final_checks_ready")
        ),
        "release_decision_release_quality_publication_guard_final_checks_match": (
            release_quality_guard_publication_guard.get("final_checks_match")
        ),
        "release_decision_release_quality_publication_guard_raw_final_checks_present": (
            release_quality_guard_publication_guard.get("raw_final_checks_present")
        ),
        "release_decision_release_quality_publication_guard_raw_final_checks_ready": (
            release_quality_guard_publication_guard.get("raw_final_checks_ready")
        ),
        "release_decision_release_quality_publication_guard_phase2_final_checks_present": (
            release_quality_guard_publication_guard.get("phase2_final_checks_present")
        ),
        "release_decision_release_quality_publication_guard_phase2_final_checks_ready": (
            release_quality_guard_publication_guard.get("phase2_final_checks_ready")
        ),
        "release_decision_release_quality_publication_guard_raw_release_matrix_check": (
            release_quality_guard_publication_guard.get("raw_release_matrix_check")
        ),
        "release_decision_release_quality_publication_guard_raw_release_matrix_default_check": (
            release_quality_guard_publication_guard.get(
                "raw_release_matrix_default_check"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_release_default_promotion_check": (
            release_quality_guard_publication_guard.get(
                "raw_release_default_promotion_check"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_release_matrix_default_match_check": (
            release_quality_guard_publication_guard.get(
                "raw_release_matrix_default_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_raw_release_matrix_manifest_match_check": (
            release_quality_guard_publication_guard.get(
                "raw_release_matrix_manifest_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_present": (
            release_quality_guard_publication_guard.get("phase2_present")
        ),
        "release_decision_release_quality_publication_guard_phase2_ready": (
            release_quality_guard_publication_guard.get("phase2_ready")
        ),
        "release_decision_release_quality_publication_guard_phase2_check_passed": (
            release_quality_guard_publication_guard.get("phase2_check_passed")
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_raw_status": (
            release_quality_guard_publication_guard.get("phase2_matrix_raw_status")
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_phase2_status": (
            release_quality_guard_publication_guard.get(
                "phase2_matrix_phase2_status"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_check_passed": (
            release_quality_guard_publication_guard.get(
                "phase2_matrix_check_passed"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_layers_ready": (
            release_quality_guard_publication_guard.get(
                "phase2_matrix_layers_ready"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_default_promotion_raw_status": (
            release_quality_guard_publication_guard.get(
                "phase2_default_promotion_raw_status"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_default_promotion_phase2_status": (
            release_quality_guard_publication_guard.get(
                "phase2_default_promotion_phase2_status"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_default_promotion_check_passed": (
            release_quality_guard_publication_guard.get(
                "phase2_default_promotion_check_passed"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_default_promotion_layers_ready": (
            release_quality_guard_publication_guard.get(
                "phase2_default_promotion_layers_ready"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_check": (
            release_quality_guard_publication_guard.get("phase2_matrix_check")
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_default_check": (
            release_quality_guard_publication_guard.get(
                "phase2_matrix_default_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_default_promotion_check": (
            release_quality_guard_publication_guard.get(
                "phase2_default_promotion_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_default_match_check": (
            release_quality_guard_publication_guard.get(
                "phase2_matrix_default_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_matrix_manifest_match_check": (
            release_quality_guard_publication_guard.get(
                "phase2_matrix_manifest_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_release_matrix_check": (
            release_quality_guard_publication_guard.get("phase2_release_matrix_check")
        ),
        "release_decision_release_quality_publication_guard_phase2_release_matrix_default_check": (
            release_quality_guard_publication_guard.get(
                "phase2_release_matrix_default_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_release_default_promotion_check": (
            release_quality_guard_publication_guard.get(
                "phase2_release_default_promotion_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_release_matrix_default_match_check": (
            release_quality_guard_publication_guard.get(
                "phase2_release_matrix_default_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_phase2_release_matrix_manifest_match_check": (
            release_quality_guard_publication_guard.get(
                "phase2_release_matrix_manifest_match_check"
            )
        ),
        "release_decision_release_quality_publication_guard_failed_checks": (
            release_quality_guard_publication_guard.get("failed_checks") or []
        ),
        "resident_registration_fastpath_release_handoff": resident_fastpath_handoff,
        "resident_registration_fastpath_release_handoff_present": (
            resident_fastpath_handoff.get("present")
        ),
        "resident_registration_fastpath_release_handoff_ready": (
            resident_fastpath_handoff.get("ready")
        ),
        "resident_registration_fastpath_release_handoff_raw_ready": (
            resident_fastpath_handoff.get("raw_ready")
        ),
        "resident_registration_fastpath_release_handoff_phase2_ready": (
            resident_fastpath_handoff.get("phase2_ready")
        ),
        "resident_registration_fastpath_release_handoff_agreement": (
            resident_fastpath_handoff.get("agreement")
        ),
        "resident_registration_fastpath_release_handoff_decision_check_passed": (
            resident_fastpath_handoff.get("decision_check_passed")
        ),
        "resident_registration_fastpath_release_handoff_phase2_check_passed": (
            resident_fastpath_handoff.get("phase2_check_passed")
        ),
        "resident_registration_fastpath_release_handoff_raw_status": (
            resident_fastpath_handoff.get("raw_status")
        ),
        "resident_registration_fastpath_release_handoff_phase2_status": (
            resident_fastpath_handoff.get("phase2_status")
        ),
        "resident_registration_fastpath_release_handoff_raw_required": (
            resident_fastpath_handoff.get("raw_required")
        ),
        "resident_registration_fastpath_release_handoff_phase2_required": (
            resident_fastpath_handoff.get("phase2_required")
        ),
        "resident_registration_fastpath_release_handoff_raw_mode": (
            resident_fastpath_handoff.get("raw_mode")
        ),
        "resident_registration_fastpath_release_handoff_phase2_mode": (
            resident_fastpath_handoff.get("phase2_mode")
        ),
        "resident_registration_fastpath_release_handoff_raw_passed_check_count": (
            _int_value(resident_fastpath_handoff.get("raw_passed_check_count"))
        ),
        "resident_registration_fastpath_release_handoff_phase2_passed_check_count": (
            _int_value(resident_fastpath_handoff.get("phase2_passed_check_count"))
        ),
        "resident_registration_fastpath_release_handoff_raw_failed_check_count": (
            _int_value(resident_fastpath_handoff.get("raw_failed_check_count"))
        ),
        "resident_registration_fastpath_release_handoff_phase2_failed_check_count": (
            _int_value(resident_fastpath_handoff.get("phase2_failed_check_count"))
        ),
        "resident_registration_fastpath_release_handoff_raw_failed_checks": (
            resident_fastpath_handoff.get("raw_failed_checks") or []
        ),
        "resident_registration_fastpath_release_handoff_phase2_failed_checks": (
            resident_fastpath_handoff.get("phase2_failed_checks") or []
        ),
        "rejection_sample_accounting": rejection_sample_accounting,
        "rejection_sample_accounting_status": pipeline.get("rejection_sample_accounting_status"),
        "rejection_sample_accounting_failed_count": pipeline.get(
            "rejection_sample_accounting_failed_count"
        ),
        "sample_accounting_closure": sample_accounting_closure,
        "sample_accounting_closure_status": pipeline.get("sample_accounting_closure_status"),
        "sample_accounting_closure_present_count": pipeline.get(
            "sample_accounting_closure_present_count"
        ),
        "sample_accounting_closure_failed_count": pipeline.get(
            "sample_accounting_closure_failed_count"
        ),
        "stack_engine_contract": stack_engine,
        "stack_engine_contract_present": stack_engine.get("present"),
        "stack_engine_contract_ready": stack_engine.get("ready"),
        "stack_engine_contract_phase2_check_passed": stack_engine.get(
            "phase2_check_passed"
        ),
        "stack_engine_contract_status": stack_engine.get("status"),
        "stack_engine_contract_passed": stack_engine.get("passed"),
        "stack_engine_contract_scope": stack_engine.get("scope"),
        "stack_engine_contract_adoption_recommendation": stack_engine.get(
            "adoption_recommendation"
        ),
        "stack_engine_contract_default_gap_count": stack_engine.get(
            "default_promotion_phase2_stack_engine_default_gap_count"
        ),
        "stack_engine_contract_blocker_count": stack_engine.get(
            "default_promotion_blocker_count"
        ),
        "stack_engine_contract_blockers": stack_engine.get(
            "default_promotion_blockers"
        )
        or [],
        "resident_winsorized_sweep_audit": resident_winsorized_sweep,
        "resident_winsorized_sweep_present": resident_winsorized_sweep.get("present"),
        "resident_winsorized_sweep_status": resident_winsorized_sweep.get("status"),
        "resident_winsorized_sweep_passed": resident_winsorized_sweep.get("passed"),
        "resident_winsorized_sweep_phase2_check_passed": resident_winsorized_sweep.get(
            "phase2_check_passed"
        ),
        "resident_winsorized_sweep_check_count": _int_value(
            resident_winsorized_sweep.get("check_count")
        ),
        "resident_winsorized_sweep_failed_check_count": _int_value(
            resident_winsorized_sweep.get("failed_check_count")
        ),
        "resident_winsorized_sweep_failed_checks": resident_winsorized_sweep.get(
            "failed_checks"
        )
        or [],
        "resident_winsorized_sweep_required_frame_count": _int_value(
            resident_winsorized_sweep.get("required_frame_count")
        ),
        "resident_winsorized_sweep_required_frame_count_passed": resident_winsorized_sweep.get(
            "required_frame_count_passed"
        ),
        "resident_winsorized_sweep_required_frame_master_rms": _number(
            resident_winsorized_sweep.get("required_frame_master_rms")
        ),
        "resident_winsorized_sweep_required_frame_master_max_abs": _number(
            resident_winsorized_sweep.get("required_frame_master_max_abs")
        ),
        "resident_winsorized_sweep_required_frame_cuda_hardened_s": _number(
            resident_winsorized_sweep.get("required_frame_cuda_hardened_s")
        ),
        "stack_engine_publication_audit": publication_audit,
        "stack_engine_publication_audit_present": publication_audit.get("present"),
        "stack_engine_publication_audit_ready": publication_audit.get("ready"),
        "stack_engine_publication_audit_status": publication_audit.get("status"),
        "stack_engine_publication_audit_passed": publication_audit.get("passed"),
        "stack_engine_publication_audit_phase2_check_passed": publication_audit.get(
            "phase2_audit_check_passed"
        ),
        "stack_engine_publication_audit_recommendation": publication_audit.get(
            "recommendation"
        ),
        "stack_engine_publication_audit_check_count": _int_value(
            publication_audit.get("check_count")
        ),
        "stack_engine_publication_audit_failed_check_count": _int_value(
            publication_audit.get("failed_check_count")
        ),
        "stack_engine_publication_audit_failed_checks": publication_audit.get(
            "failed_checks"
        )
        or [],
        "stack_engine_publication_policy_chain_phase2_check_passed": publication_audit.get(
            "policy_chain_phase2_check_passed"
        ),
        "stack_engine_publication_publish_preflight_policy_ready": publication_audit.get(
            "publish_preflight_policy_ready"
        ),
        "stack_engine_publication_phase2_policy_ready": publication_audit.get(
            "phase2_policy_ready"
        ),
        "stack_engine_publication_policy_agreement": publication_audit.get(
            "policy_agreement"
        ),
        "stack_engine_publication_resident_winsorized_chain_phase2_check_passed": publication_audit.get(
            "resident_winsorized_chain_phase2_check_passed"
        ),
        "stack_engine_publication_publish_preflight_resident_winsorized_ready": publication_audit.get(
            "publish_preflight_resident_winsorized_ready"
        ),
        "stack_engine_publication_phase2_resident_winsorized_ready": publication_audit.get(
            "phase2_resident_winsorized_ready"
        ),
        "stack_engine_publication_resident_winsorized_agreement": publication_audit.get(
            "resident_winsorized_agreement"
        ),
    }


def _package_rows(recommendation: dict[str, Any]) -> list[dict[str, Any]]:
    ordered_try_list = [str(item) for item in recommendation.get("ordered_try_list") or []]
    recommendation_rows = {
        str(item.get("label")): item
        for item in recommendation.get("packages") or []
        if isinstance(item, dict) and item.get("label") is not None
    }
    rows: list[dict[str, Any]] = []
    for package in WINDOWS_CUDA_PACKAGES:
        row = dict(recommendation_rows.get(package.label) or {})
        row.setdefault("label", package.label)
        row.setdefault("toolkit", package.toolkit)
        row.setdefault("architectures", [f"{arch // 10}.{arch % 10}" for arch in package.architectures])
        row.setdefault("compatible", None)
        row.setdefault("match", "not_evaluated")
        row["release_artifact"] = f"GLASS-Portable-win64-{package.label}.zip"
        row["recommended_order"] = (
            ordered_try_list.index(package.label) + 1 if package.label in ordered_try_list else None
        )
        row["release_role"] = (
            "primary_cuda_package"
            if recommendation.get("primary") == package.label
            else "cuda_fallback_candidate"
            if row.get("compatible") is True
            else "cuda_planned_package"
        )
        rows.append(row)
    rows.append(
        {
            "label": "cpu",
            "toolkit": None,
            "architectures": [],
            "compatible": True,
            "match": "cpu_fallback",
            "release_artifact": "GLASS-Portable-win64-cpu.zip",
            "recommended_order": ordered_try_list.index("cpu") + 1 if "cpu" in ordered_try_list else None,
            "release_role": "universal_cpu_fallback",
            "note": "CPU package remains the fallback and does not require CUDA.",
        }
    )
    return rows


def build_windows_release_matrix(
    *,
    doctor_json: str | Path,
    release_decision_json: str | Path,
    acceptance_audit_json: str | Path | None = None,
    default_promotion_manifest_json: str | Path | None = None,
    default_runtime_preset: str = "throughput-v1",
    required_cuda_packages: tuple[str, ...] = ("cuda13", "cuda12", "cuda11"),
    require_cuda: bool = True,
    require_default_change_ready: bool = True,
    require_default_promotion_ready: bool = True,
    expected_primary_package: str | None = None,
    max_runtime_ratio: float = 1.25,
    min_resident_winsorized_sweep_checks: int = 27,
    required_resident_winsorized_sweep_frame_count: int = 200,
    require_direct_runtime_evidence: bool = True,
) -> dict[str, Any]:
    doctor = _read_json_object(doctor_json)
    decision = _read_json_object(release_decision_json)
    acceptance = _read_json_object(acceptance_audit_json) if acceptance_audit_json is not None else {}
    default_promotion = _default_promotion_summary(
        _read_json_object_optional(default_promotion_manifest_json)
    )
    cuda = doctor.get("cuda") if isinstance(doctor.get("cuda"), dict) else {}
    recommendation = (
        doctor.get("windows_cuda_packages")
        if isinstance(doctor.get("windows_cuda_packages"), dict)
        else {}
    )
    package_rows = _package_rows(recommendation)
    package_by_label = {str(row.get("label")): row for row in package_rows}
    ordered_try_list = [str(item) for item in recommendation.get("ordered_try_list") or []]
    primary = str(recommendation.get("primary") or "")
    expected_primary = expected_primary_package or primary
    runtime_repeat = decision.get("runtime_repeat") if isinstance(decision.get("runtime_repeat"), dict) else {}
    runtime_ratio = _number(runtime_repeat.get("elapsed_ratio_vs_best"))
    release_direct_publication_guard = _direct_publication_guard_from_decision(
        decision,
        min_resident_lights=200,
    )
    release_quality_publication_guard = _quality_publication_guard_from_decision(
        decision
    )
    release_quality_guard_publication_guard = (
        _release_quality_publication_guard_from_decision(decision)
    )

    checks = [
        _check(
            "doctor_schema_version",
            doctor.get("schema_version") == 1,
            {"actual": doctor.get("schema_version"), "required": 1, "path": str(doctor_json)},
        ),
        _check(
            "cuda_probe_completed",
            not bool(cuda.get("probe_skipped")),
            {"probe_skipped": cuda.get("probe_skipped")},
        ),
        _check(
            "cuda_available_for_release_machine",
            bool(cuda.get("cuda_available")) if require_cuda else True,
            {
                "actual": cuda.get("cuda_available"),
                "required": bool(require_cuda),
                "wrapper_importable": cuda.get("wrapper_importable"),
                "native_extension_loaded": cuda.get("native_extension_loaded"),
            },
        ),
        _check(
            "windows_package_recommendation_present",
            bool(recommendation.get("ordered_try_list")) and bool(recommendation.get("packages")),
            {
                "ordered_try_list": ordered_try_list,
                "package_count": len(recommendation.get("packages") or []),
            },
        ),
        _check(
            "ordered_try_list_has_cpu_fallback",
            "cpu" in ordered_try_list,
            {"ordered_try_list": ordered_try_list},
        ),
        _check(
            "primary_package_matches_expected",
            not expected_primary or primary == expected_primary,
            {"actual": primary, "required": expected_primary},
        ),
        _check(
            "release_decision_default_change_ready",
            bool(decision.get("default_change_ready")) if require_default_change_ready else True,
            {
                "actual": decision.get("default_change_ready"),
                "required": bool(require_default_change_ready),
                "status": decision.get("status"),
                "recommendation": decision.get("recommendation"),
            },
        ),
        _check(
            "release_decision_recommends_promotion",
            decision.get("recommendation") == "promote_default_candidate",
            {"actual": decision.get("recommendation"), "required": "promote_default_candidate"},
        ),
        _check(
            "release_decision_direct_runtime_publication_guard_passed",
            release_direct_publication_guard.get("ready") is True,
            release_direct_publication_guard,
        ),
        _check(
            "release_decision_quality_compare_publication_guard_passed",
            release_quality_publication_guard.get("ready") is True,
            release_quality_publication_guard,
            note="Required when release-decision supplies StackEngine publication quality compare evidence.",
        ),
        _check(
            "release_decision_release_quality_publication_guard_passed",
            release_quality_guard_publication_guard.get("ready") is True,
            release_quality_guard_publication_guard,
            note="Required when release-decision supplies StackEngine release-quality publication evidence.",
        ),
        _check(
            "default_promotion_manifest_present",
            bool(default_promotion.get("present")) if require_default_promotion_ready else True,
            {
                "present": default_promotion.get("present"),
                "required": bool(require_default_promotion_ready),
            },
        ),
        _check(
            "default_promotion_manifest_ready",
            (
                default_promotion.get("artifact_type") == "default_promotion_manifest"
                and default_promotion.get("status") == "default_promotion_ready"
                and default_promotion.get("passed") is True
                and default_promotion.get("default_change_ready") is True
            )
            if require_default_promotion_ready
            else True,
            {
                "artifact_type": default_promotion.get("artifact_type"),
                "status": default_promotion.get("status"),
                "passed": default_promotion.get("passed"),
                "default_change_ready": default_promotion.get("default_change_ready"),
            },
        ),
        _check(
            "default_promotion_default_route_passed",
            (
                default_promotion.get("default_route_passed") is True
                and default_promotion.get("default_route_route_contract_passed") is True
                and int(default_promotion.get("default_route_route_check_count") or 0) >= 4
            )
            if require_default_promotion_ready
            else True,
            {
                "default_route_passed": default_promotion.get("default_route_passed"),
                "route_contract_passed": default_promotion.get(
                    "default_route_route_contract_passed"
                ),
                "route_check_count": default_promotion.get("default_route_route_check_count"),
            },
        ),
        _check(
            "default_promotion_quality_metrics_compare_handoff_passed",
            (
                default_promotion.get("quality_metrics_compare_present") is not True
                or default_promotion.get("quality_metrics_compare_ready") is True
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get("quality_metrics_compare_present"),
                "ready": default_promotion.get("quality_metrics_compare_ready"),
                "status": default_promotion.get("quality_metrics_compare_status"),
                "passed": default_promotion.get("quality_metrics_compare_passed"),
                "phase2_check_passed": default_promotion.get(
                    "quality_metrics_compare_phase2_check_passed"
                ),
                "failed_check_count": default_promotion.get(
                    "quality_metrics_compare_failed_check_count"
                ),
                "failed_checks": default_promotion.get(
                    "quality_metrics_compare_failed_checks"
                ),
                "threshold_failure_count": default_promotion.get(
                    "quality_metrics_compare_threshold_failure_count"
                ),
                "threshold_failures": default_promotion.get(
                    "quality_metrics_compare_threshold_failures"
                ),
            },
            note="Required only when default-promotion supplies quality-metrics-compare evidence.",
        ),
        _check(
            "default_promotion_rejection_sample_accounting_passed",
            (
                default_promotion.get("integration_rejection_sample_counts_match_maps") is True
                and default_promotion.get("rejection_sample_accounting_status") == "passed"
                and int(default_promotion.get("rejection_sample_accounting_failed_count") or 0) == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "pipeline_contract_status": default_promotion.get("pipeline_contract_status"),
                "pipeline_contract_passed": default_promotion.get("pipeline_contract_passed"),
                "check": default_promotion.get("integration_rejection_sample_counts_match_maps"),
                "status": default_promotion.get("rejection_sample_accounting_status"),
                "failed_count": default_promotion.get("rejection_sample_accounting_failed_count"),
                "failed_items": (
                    default_promotion.get("rejection_sample_accounting") or {}
                ).get("failed_items"),
            },
        ),
        _check(
            "default_promotion_sample_accounting_closure_passed",
            (
                default_promotion.get("integration_sample_accounting_closure") is True
                and default_promotion.get("sample_accounting_closure_status") == "passed"
                and int(default_promotion.get("sample_accounting_closure_failed_count") or 0)
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "pipeline_contract_status": default_promotion.get("pipeline_contract_status"),
                "pipeline_contract_passed": default_promotion.get("pipeline_contract_passed"),
                "check": default_promotion.get("integration_sample_accounting_closure"),
                "status": default_promotion.get("sample_accounting_closure_status"),
                "present_count": default_promotion.get("sample_accounting_closure_present_count"),
                "failed_count": default_promotion.get("sample_accounting_closure_failed_count"),
                "failed_items": (
                    default_promotion.get("sample_accounting_closure") or {}
                ).get("failed_items"),
            },
        ),
        _check(
            "default_promotion_resident_result_contract_handoff_passed",
            (
                default_promotion.get("resident_result_contract_present") is True
                and default_promotion.get("resident_result_contract_ready") is True
                and default_promotion.get("resident_result_contract_status")
                == "passed"
                and default_promotion.get("resident_result_contract_top_level_check")
                is True
                and default_promotion.get("resident_result_contract_check_present")
                is True
                and default_promotion.get("resident_result_contract_check_passed")
                is True
                and default_promotion.get(
                    "resident_result_contract_phase2_check_passed"
                )
                is True
                and int(
                    default_promotion.get(
                        "resident_result_contract_required_count"
                    )
                    or 0
                )
                > 0
                and int(
                    default_promotion.get("resident_result_contract_failed_count")
                    or 0
                )
                == 0
                and int(
                    default_promotion.get(
                        "resident_result_contract_failed_check_count"
                    )
                    or 0
                )
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get("resident_result_contract_present"),
                "ready": default_promotion.get("resident_result_contract_ready"),
                "status": default_promotion.get("resident_result_contract_status"),
                "top_level_check": default_promotion.get(
                    "resident_result_contract_top_level_check"
                ),
                "check_present": default_promotion.get(
                    "resident_result_contract_check_present"
                ),
                "check_passed": default_promotion.get(
                    "resident_result_contract_check_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "resident_result_contract_phase2_check_passed"
                ),
                "required_count": default_promotion.get(
                    "resident_result_contract_required_count"
                ),
                "failed_count": default_promotion.get(
                    "resident_result_contract_failed_count"
                ),
                "failed_check_count": default_promotion.get(
                    "resident_result_contract_failed_check_count"
                ),
                "failed_checks": default_promotion.get(
                    "resident_result_contract_failed_checks"
                ),
                "failed_items": default_promotion.get(
                    "resident_result_contract_failed_items"
                ),
            },
        ),
        _check(
            "default_promotion_acceptance_integration_engine_policy_passed",
            (
                default_promotion.get("acceptance_integration_engine_policy_status")
                == "passed"
                and default_promotion.get(
                    "acceptance_integration_engine_policy_check_present"
                )
                is True
                and default_promotion.get(
                    "acceptance_integration_engine_policy_check_passed"
                )
                is True
                and default_promotion.get(
                    "acceptance_integration_engine_policy_phase2_check_passed"
                )
                is True
            )
            if require_default_promotion_ready
            else True,
            {
                "status": default_promotion.get(
                    "acceptance_integration_engine_policy_status"
                ),
                "check_present": default_promotion.get(
                    "acceptance_integration_engine_policy_check_present"
                ),
                "check_passed": default_promotion.get(
                    "acceptance_integration_engine_policy_check_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "acceptance_integration_engine_policy_phase2_check_passed"
                ),
                "non_resident_count": default_promotion.get(
                    "acceptance_integration_engine_policy_non_resident_count"
                ),
                "failed_count": default_promotion.get(
                    "acceptance_integration_engine_policy_failed_count"
                ),
                "failed_items": default_promotion.get(
                    "acceptance_integration_engine_policy_failed_items"
                ),
            },
        ),
        _check(
            "default_promotion_pipeline_integration_engine_policy_passed",
            (
                default_promotion.get("pipeline_integration_engine_policy_status")
                == "passed"
                and default_promotion.get(
                    "pipeline_integration_engine_policy_check_present"
                )
                is True
                and default_promotion.get(
                    "pipeline_integration_engine_policy_check_passed"
                )
                is True
                and default_promotion.get(
                    "pipeline_integration_engine_policy_phase2_check_passed"
                )
                is True
            )
            if require_default_promotion_ready
            else True,
            {
                "status": default_promotion.get(
                    "pipeline_integration_engine_policy_status"
                ),
                "check_present": default_promotion.get(
                    "pipeline_integration_engine_policy_check_present"
                ),
                "check_passed": default_promotion.get(
                    "pipeline_integration_engine_policy_check_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "pipeline_integration_engine_policy_phase2_check_passed"
                ),
                "default_engine_policy": default_promotion.get(
                    "pipeline_integration_engine_policy_default_engine_policy"
                ),
                "non_resident_count": default_promotion.get(
                    "pipeline_integration_engine_policy_non_resident_count"
                ),
                "failed_count": default_promotion.get(
                    "pipeline_integration_engine_policy_failed_count"
                ),
                "failed_items": default_promotion.get(
                    "pipeline_integration_engine_policy_failed_items"
                ),
            },
        ),
        _check(
            "default_promotion_acceptance_stack_engine_runtime_default_passed",
            (
                default_promotion.get(
                    "acceptance_stack_engine_runtime_default_status"
                )
                == "passed"
                and default_promotion.get(
                    "acceptance_stack_engine_runtime_default_check_present"
                )
                is True
                and default_promotion.get(
                    "acceptance_stack_engine_runtime_default_check_passed"
                )
                is True
                and default_promotion.get(
                    "acceptance_stack_engine_runtime_default_phase2_check_passed"
                )
                is True
                and default_promotion.get(
                    "acceptance_stack_engine_runtime_default_legacy_master_count"
                )
                == 0
                and default_promotion.get(
                    "acceptance_stack_engine_runtime_default_failed_master_count"
                )
                == 0
                and default_promotion.get(
                    "acceptance_stack_engine_runtime_default_failed_output_count"
                )
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "status": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_status"
                ),
                "check_present": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_check_present"
                ),
                "check_passed": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_check_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_phase2_check_passed"
                ),
                "master_count": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_master_count"
                ),
                "legacy_master_count": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_legacy_master_count"
                ),
                "failed_master_count": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_failed_master_count"
                ),
                "failed_output_count": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_failed_output_count"
                ),
                "explicit_cuda_fast_path_count": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count"
                ),
                "failed_masters": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_failed_masters"
                ),
                "failed_outputs": default_promotion.get(
                    "acceptance_stack_engine_runtime_default_failed_outputs"
                ),
            },
        ),
        _check(
            "default_promotion_pipeline_stack_engine_runtime_default_passed",
            (
                default_promotion.get("pipeline_stack_engine_runtime_default_status")
                == "passed"
                and default_promotion.get(
                    "pipeline_stack_engine_runtime_default_check_present"
                )
                is True
                and default_promotion.get(
                    "pipeline_stack_engine_runtime_default_check_passed"
                )
                is True
                and default_promotion.get(
                    "pipeline_stack_engine_runtime_default_phase2_check_passed"
                )
                is True
                and default_promotion.get(
                    "pipeline_stack_engine_runtime_default_legacy_master_count"
                )
                == 0
                and default_promotion.get(
                    "pipeline_stack_engine_runtime_default_failed_master_count"
                )
                == 0
                and default_promotion.get(
                    "pipeline_stack_engine_runtime_default_failed_output_count"
                )
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "status": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_status"
                ),
                "check_present": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_check_present"
                ),
                "check_passed": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_check_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_phase2_check_passed"
                ),
                "master_count": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_master_count"
                ),
                "legacy_master_count": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_legacy_master_count"
                ),
                "failed_master_count": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_failed_master_count"
                ),
                "failed_output_count": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_failed_output_count"
                ),
                "explicit_cuda_fast_path_count": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
                ),
                "failed_masters": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_failed_masters"
                ),
                "failed_outputs": default_promotion.get(
                    "pipeline_stack_engine_runtime_default_failed_outputs"
                ),
            },
        ),
        _check(
            "default_promotion_direct_acceptance_fastpath_evidence",
            (
                default_promotion.get("runtime_default_direct_evidence_present")
                is True
                and default_promotion.get("runtime_default_direct_acceptance_fastpath")
                is True
                and default_promotion.get(
                    "runtime_default_direct_acceptance_fastpath_source"
                )
                == "explicit_resident_artifacts_json"
                and int(
                    default_promotion.get(
                        "runtime_default_direct_acceptance_fastpath_check_count"
                    )
                    or 0
                )
                > 0
                and int(
                    default_promotion.get(
                        "runtime_default_direct_acceptance_fastpath_failed_check_count"
                    )
                    or 0
                )
                == 0
            )
            if require_default_promotion_ready and require_direct_runtime_evidence
            else True,
            {
                "present": default_promotion.get(
                    "runtime_default_direct_evidence_present"
                ),
                "ready": default_promotion.get(
                    "runtime_default_direct_evidence_ready"
                ),
                "direct_fastpath": default_promotion.get(
                    "runtime_default_direct_acceptance_fastpath"
                ),
                "source": default_promotion.get(
                    "runtime_default_direct_acceptance_fastpath_source"
                ),
                "check_count": default_promotion.get(
                    "runtime_default_direct_acceptance_fastpath_check_count"
                ),
                "failed_check_count": default_promotion.get(
                    "runtime_default_direct_acceptance_fastpath_failed_check_count"
                ),
                "failed_checks": default_promotion.get(
                    "runtime_default_direct_acceptance_fastpath_failed_checks"
                ),
                "required": bool(require_direct_runtime_evidence),
            },
        ),
        _check(
            "default_promotion_direct_pipeline_calibration_evidence",
            (
                default_promotion.get("runtime_default_direct_evidence_present")
                is True
                and default_promotion.get(
                    "runtime_default_direct_pipeline_calibration"
                )
                is True
                and default_promotion.get(
                    "runtime_default_direct_pipeline_calibration_source"
                )
                == "resident_artifacts_json_fallback"
                and default_promotion.get(
                    "runtime_default_direct_pipeline_calibration_generated_for_contract"
                )
                is True
                and default_promotion.get(
                    "runtime_default_direct_pipeline_calibration_path_exists"
                )
                is False
                and default_promotion.get(
                    "runtime_default_direct_pipeline_resident_native_calibration_artifact"
                )
                is True
                and int(
                    default_promotion.get(
                        "runtime_default_direct_pipeline_resident_calibrated_light_count"
                    )
                    or 0
                )
                > 0
            )
            if require_default_promotion_ready and require_direct_runtime_evidence
            else True,
            {
                "present": default_promotion.get(
                    "runtime_default_direct_evidence_present"
                ),
                "ready": default_promotion.get(
                    "runtime_default_direct_evidence_ready"
                ),
                "direct_pipeline_calibration": default_promotion.get(
                    "runtime_default_direct_pipeline_calibration"
                ),
                "source": default_promotion.get(
                    "runtime_default_direct_pipeline_calibration_source"
                ),
                "generated_for_contract": default_promotion.get(
                    "runtime_default_direct_pipeline_calibration_generated_for_contract"
                ),
                "path_exists": default_promotion.get(
                    "runtime_default_direct_pipeline_calibration_path_exists"
                ),
                "resident_native_calibration_artifact": default_promotion.get(
                    "runtime_default_direct_pipeline_resident_native_calibration_artifact"
                ),
                "resident_calibrated_light_count": default_promotion.get(
                    "runtime_default_direct_pipeline_resident_calibrated_light_count"
                ),
                "required": bool(require_direct_runtime_evidence),
            },
        ),
        _check(
            "default_promotion_release_decision_direct_runtime_publication_guard_passed",
            (
                default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_present"
                )
                is True
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_ready"
                )
                is True
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_check_passed"
                )
                is True
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_source_ready"
                )
                is True
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_count_ready"
                )
                is True
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_leaf_checks_ready"
                )
                is True
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_raw_acceptance_source"
                )
                == "explicit_resident_artifacts_json"
                and default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_raw_calibration_source"
                )
                == "resident_artifacts_json_fallback"
                and int(
                    default_promotion.get(
                        "release_decision_direct_runtime_publication_guard_raw_resident_lights"
                    )
                    or 0
                )
                >= 200
            )
            if require_default_promotion_ready and require_direct_runtime_evidence
            else True,
            {
                "present": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_present"
                ),
                "ready": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_ready"
                ),
                "decision_check_passed": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_check_passed"
                ),
                "source_ready": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_source_ready"
                ),
                "count_ready": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_count_ready"
                ),
                "leaf_checks_ready": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_leaf_checks_ready"
                ),
                "acceptance_source": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_raw_acceptance_source"
                ),
                "calibration_source": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_raw_calibration_source"
                ),
                "resident_lights": default_promotion.get(
                    "release_decision_direct_runtime_publication_guard_raw_resident_lights"
                ),
                "required": bool(require_direct_runtime_evidence),
            },
        ),
        _check(
            "default_promotion_release_decision_quality_compare_publication_guard_passed",
            (
                default_promotion.get(
                    "release_decision_quality_compare_publication_guard_present"
                )
                is not True
                or (
                    default_promotion.get(
                        "release_decision_quality_compare_publication_guard_ready"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_quality_compare_publication_guard_check_passed"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_quality_compare_publication_guard_layers_ready"
                    )
                    is True
                )
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_present"
                ),
                "ready": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_ready"
                ),
                "decision_check_passed": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_check_passed"
                ),
                "quality_present": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_quality_present"
                ),
                "compatible_missing": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_compatible_missing"
                ),
                "layers_ready": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_layers_ready"
                ),
                "raw_status": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_raw_status"
                ),
                "raw_failed_count": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_raw_failed_count"
                ),
                "phase2_status": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_phase2_status"
                ),
                "phase2_failed_count": default_promotion.get(
                    "release_decision_quality_compare_publication_guard_phase2_failed_count"
                ),
            },
            note="Required when default-promotion carries release-decision quality compare evidence.",
        ),
        _check(
            "default_promotion_release_decision_release_quality_publication_guard_passed",
            (
                (
                    default_promotion.get(
                        "release_decision_release_quality_publication_guard_present"
                    )
                    is False
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_ready"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_compatible_missing"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_release_quality_present"
                    )
                    is False
                )
                or (
                    default_promotion.get(
                        "release_decision_release_quality_publication_guard_present"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_ready"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_decision_check_ready"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_checks_ready"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_layers_ready"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_raw_matrix_check_passed"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_raw_default_promotion_check_passed"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_raw_matrix_default_match_check"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_raw_matrix_manifest_match_check"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_phase2_matrix_check_passed"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_phase2_default_promotion_check_passed"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_phase2_matrix_default_match_check"
                    )
                    is True
                    and default_promotion.get(
                        "release_decision_release_quality_publication_guard_phase2_matrix_manifest_match_check"
                    )
                    is True
                    and (
                        (
                            not release_quality_guard_publication_guard.get(
                                "final_fields_present"
                            )
                            and not default_promotion.get(
                                "release_decision_release_quality_publication_guard_final_fields_present"
                            )
                        )
                        or (
                            not release_quality_guard_publication_guard.get(
                                "final_fields_present"
                            )
                            and default_promotion.get(
                                "release_decision_release_quality_publication_guard_final_checks_compatible_missing"
                            )
                            is True
                        )
                        or (
                            default_promotion.get(
                                "release_decision_release_quality_publication_guard_final_checks_compatible_missing"
                            )
                            is True
                            and release_quality_guard_publication_guard.get(
                                "raw_final_checks_present"
                            )
                            is not True
                            and release_quality_guard_publication_guard.get(
                                "phase2_final_checks_present"
                            )
                            is not True
                        )
                        or (
                            default_promotion.get(
                                "release_decision_release_quality_publication_guard_final_checks_ready"
                            )
                            is True
                            and default_promotion.get(
                                "release_decision_release_quality_publication_guard_final_checks_match"
                            )
                            is True
                            and default_promotion.get(
                                "release_decision_release_quality_publication_guard_raw_final_checks_ready"
                            )
                            is True
                            and default_promotion.get(
                                "release_decision_release_quality_publication_guard_phase2_final_checks_ready"
                            )
                            is True
                        )
                    )
                )
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get(
                    "release_decision_release_quality_publication_guard_present"
                ),
                "ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_ready"
                ),
                "decision_check_passed": default_promotion.get(
                    "release_decision_release_quality_publication_guard_check_passed"
                ),
                "decision_check_ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_decision_check_ready"
                ),
                "checks_ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_checks_ready"
                ),
                "layers_ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_layers_ready"
                ),
                "compatible_missing": default_promotion.get(
                    "release_decision_release_quality_publication_guard_compatible_missing"
                ),
                "release_quality_present": default_promotion.get(
                    "release_decision_release_quality_publication_guard_release_quality_present"
                ),
                "raw_matrix_raw_status": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_matrix_raw_status"
                ),
                "raw_matrix_phase2_status": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_matrix_phase2_status"
                ),
                "raw_matrix_check_passed": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_matrix_check_passed"
                ),
                "raw_default_promotion_check_passed": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_default_promotion_check_passed"
                ),
                "raw_matrix_default_match_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_matrix_default_match_check"
                ),
                "raw_matrix_manifest_match_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_matrix_manifest_match_check"
                ),
                "phase2_matrix_raw_status": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_matrix_raw_status"
                ),
                "phase2_matrix_phase2_status": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_matrix_phase2_status"
                ),
                "phase2_matrix_check_passed": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_matrix_check_passed"
                ),
                "phase2_default_promotion_check_passed": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_default_promotion_check_passed"
                ),
                "phase2_matrix_default_match_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_matrix_default_match_check"
                ),
                "phase2_matrix_manifest_match_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_matrix_manifest_match_check"
                ),
                "direct_final_fields_present": (
                    release_quality_guard_publication_guard.get(
                        "final_fields_present"
                    )
                ),
                "final_fields_present": default_promotion.get(
                    "release_decision_release_quality_publication_guard_final_fields_present"
                ),
                "final_checks_compatible_missing": default_promotion.get(
                    "release_decision_release_quality_publication_guard_final_checks_compatible_missing"
                ),
                "final_checks_ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_final_checks_ready"
                ),
                "final_checks_match": default_promotion.get(
                    "release_decision_release_quality_publication_guard_final_checks_match"
                ),
                "raw_final_checks_present": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_final_checks_present"
                ),
                "raw_final_checks_ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_final_checks_ready"
                ),
                "phase2_final_checks_present": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_final_checks_present"
                ),
                "phase2_final_checks_ready": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_final_checks_ready"
                ),
                "raw_release_matrix_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_release_matrix_check"
                ),
                "raw_release_matrix_manifest_match_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_raw_release_matrix_manifest_match_check"
                ),
                "phase2_release_matrix_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_release_matrix_check"
                ),
                "phase2_release_matrix_manifest_match_check": default_promotion.get(
                    "release_decision_release_quality_publication_guard_phase2_release_matrix_manifest_match_check"
                ),
                "failed_checks": default_promotion.get(
                    "release_decision_release_quality_publication_guard_failed_checks"
                ),
            },
            note="Required when default-promotion carries release-quality publication guard evidence.",
        ),
        _check(
            "default_promotion_resident_fastpath_release_handoff_ready",
            (
                default_promotion.get(
                    "resident_registration_fastpath_release_handoff_present"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_ready"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_ready"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_ready"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_agreement"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_decision_check_passed"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_check_passed"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_status"
                )
                == "passed"
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_status"
                )
                == "passed"
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_required"
                )
                is True
                and default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_required"
                )
                is True
                and int(
                    default_promotion.get(
                        "resident_registration_fastpath_release_handoff_raw_passed_check_count"
                    )
                    or 0
                )
                > 0
                and int(
                    default_promotion.get(
                        "resident_registration_fastpath_release_handoff_phase2_passed_check_count"
                    )
                    or 0
                )
                > 0
                and int(
                    default_promotion.get(
                        "resident_registration_fastpath_release_handoff_raw_failed_check_count"
                    )
                    or 0
                )
                == 0
                and int(
                    default_promotion.get(
                        "resident_registration_fastpath_release_handoff_phase2_failed_check_count"
                    )
                    or 0
                )
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_present"
                ),
                "ready": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_ready"
                ),
                "raw_ready": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_ready"
                ),
                "phase2_ready": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_ready"
                ),
                "agreement": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_agreement"
                ),
                "decision_check_passed": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_decision_check_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_check_passed"
                ),
                "raw_status": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_status"
                ),
                "phase2_status": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_status"
                ),
                "raw_required": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_required"
                ),
                "phase2_required": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_required"
                ),
                "raw_mode": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_mode"
                ),
                "phase2_mode": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_mode"
                ),
                "raw_passed_check_count": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_passed_check_count"
                ),
                "phase2_passed_check_count": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_passed_check_count"
                ),
                "raw_failed_check_count": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_failed_check_count"
                ),
                "phase2_failed_check_count": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_failed_check_count"
                ),
                "raw_failed_checks": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_raw_failed_checks"
                ),
                "phase2_failed_checks": default_promotion.get(
                    "resident_registration_fastpath_release_handoff_phase2_failed_checks"
                ),
            },
        ),
        _check(
            "default_promotion_stack_engine_contract_ready",
            (
                default_promotion.get("stack_engine_contract_present") is True
                and default_promotion.get("stack_engine_contract_ready") is True
                and default_promotion.get("stack_engine_contract_phase2_check_passed")
                is True
                and default_promotion.get("stack_engine_contract_status") == "passed"
                and default_promotion.get("stack_engine_contract_passed") is True
                and default_promotion.get("stack_engine_contract_scope") == "all"
                and default_promotion.get(
                    "stack_engine_contract_adoption_recommendation"
                )
                == "stack_engine_default_ready"
                and int(default_promotion.get("stack_engine_contract_default_gap_count") or 0)
                == 0
                and int(default_promotion.get("stack_engine_contract_blocker_count") or 0)
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get("stack_engine_contract_present"),
                "ready": default_promotion.get("stack_engine_contract_ready"),
                "phase2_check_passed": default_promotion.get(
                    "stack_engine_contract_phase2_check_passed"
                ),
                "status": default_promotion.get("stack_engine_contract_status"),
                "passed": default_promotion.get("stack_engine_contract_passed"),
                "scope": default_promotion.get("stack_engine_contract_scope"),
                "adoption_recommendation": default_promotion.get(
                    "stack_engine_contract_adoption_recommendation"
                ),
                "default_gap_count": default_promotion.get(
                    "stack_engine_contract_default_gap_count"
                ),
                "blocker_count": default_promotion.get(
                    "stack_engine_contract_blocker_count"
                ),
                "blockers": default_promotion.get("stack_engine_contract_blockers"),
            },
        ),
        _check(
            "default_promotion_resident_winsorized_sweep_audit_passed",
            (
                default_promotion.get("resident_winsorized_sweep_present") is True
                and default_promotion.get("resident_winsorized_sweep_status") == "passed"
                and default_promotion.get("resident_winsorized_sweep_passed") is True
                and default_promotion.get(
                    "resident_winsorized_sweep_phase2_check_passed"
                )
                is True
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get("resident_winsorized_sweep_present"),
                "status": default_promotion.get("resident_winsorized_sweep_status"),
                "passed": default_promotion.get("resident_winsorized_sweep_passed"),
                "phase2_check_passed": default_promotion.get(
                    "resident_winsorized_sweep_phase2_check_passed"
                ),
                "failed_checks": default_promotion.get(
                    "resident_winsorized_sweep_failed_checks"
                ),
            },
        ),
        _check(
            "default_promotion_resident_winsorized_required_frame_passed",
            (
                default_promotion.get(
                    "resident_winsorized_sweep_required_frame_count"
                )
                == int(required_resident_winsorized_sweep_frame_count)
                and default_promotion.get(
                    "resident_winsorized_sweep_required_frame_count_passed"
                )
                is True
            )
            if require_default_promotion_ready
            else True,
            {
                "actual_frame_count": default_promotion.get(
                    "resident_winsorized_sweep_required_frame_count"
                ),
                "required_frame_count": int(
                    required_resident_winsorized_sweep_frame_count
                ),
                "required_frame_count_passed": default_promotion.get(
                    "resident_winsorized_sweep_required_frame_count_passed"
                ),
                "required_frame_master_rms": default_promotion.get(
                    "resident_winsorized_sweep_required_frame_master_rms"
                ),
                "required_frame_master_max_abs": default_promotion.get(
                    "resident_winsorized_sweep_required_frame_master_max_abs"
                ),
            },
        ),
        _check(
            "default_promotion_resident_winsorized_sweep_check_count",
            (
                default_promotion.get("resident_winsorized_sweep_check_count")
                is not None
                and default_promotion.get("resident_winsorized_sweep_check_count")
                >= int(min_resident_winsorized_sweep_checks)
            )
            if require_default_promotion_ready
            else True,
            {
                "actual": default_promotion.get(
                    "resident_winsorized_sweep_check_count"
                ),
                "required_min": int(min_resident_winsorized_sweep_checks),
                "failed_check_count": default_promotion.get(
                    "resident_winsorized_sweep_failed_check_count"
                ),
            },
        ),
        _check(
            "default_promotion_stack_engine_publication_audit_passed",
            (
                default_promotion.get("stack_engine_publication_audit_present") is True
                and default_promotion.get("stack_engine_publication_audit_ready") is True
                and default_promotion.get("stack_engine_publication_audit_status")
                == "passed"
                and default_promotion.get("stack_engine_publication_audit_passed") is True
                and default_promotion.get(
                    "stack_engine_publication_audit_phase2_check_passed"
                )
                is True
                and int(
                    default_promotion.get(
                        "stack_engine_publication_audit_failed_check_count"
                    )
                    or 0
                )
                == 0
            )
            if require_default_promotion_ready
            else True,
            {
                "present": default_promotion.get(
                    "stack_engine_publication_audit_present"
                ),
                "ready": default_promotion.get(
                    "stack_engine_publication_audit_ready"
                ),
                "status": default_promotion.get(
                    "stack_engine_publication_audit_status"
                ),
                "passed": default_promotion.get(
                    "stack_engine_publication_audit_passed"
                ),
                "phase2_check_passed": default_promotion.get(
                    "stack_engine_publication_audit_phase2_check_passed"
                ),
                "recommendation": default_promotion.get(
                    "stack_engine_publication_audit_recommendation"
                ),
                "check_count": default_promotion.get(
                    "stack_engine_publication_audit_check_count"
                ),
                "failed_check_count": default_promotion.get(
                    "stack_engine_publication_audit_failed_check_count"
                ),
                "failed_checks": default_promotion.get(
                    "stack_engine_publication_audit_failed_checks"
                ),
            },
        ),
        _check(
            "default_promotion_stack_engine_publication_policy_chain_passed",
            (
                default_promotion.get(
                    "stack_engine_publication_policy_chain_phase2_check_passed"
                )
                is True
                and default_promotion.get(
                    "stack_engine_publication_publish_preflight_policy_ready"
                )
                is True
                and default_promotion.get(
                    "stack_engine_publication_phase2_policy_ready"
                )
                is True
                and default_promotion.get(
                    "stack_engine_publication_policy_agreement"
                )
                is True
            )
            if require_default_promotion_ready
            else True,
            {
                "phase2_check_passed": default_promotion.get(
                    "stack_engine_publication_policy_chain_phase2_check_passed"
                ),
                "publish_preflight_policy_ready": default_promotion.get(
                    "stack_engine_publication_publish_preflight_policy_ready"
                ),
                "phase2_policy_ready": default_promotion.get(
                    "stack_engine_publication_phase2_policy_ready"
                ),
                "policy_agreement": default_promotion.get(
                    "stack_engine_publication_policy_agreement"
                ),
            },
        ),
        _check(
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
            (
                default_promotion.get(
                    "stack_engine_publication_resident_winsorized_chain_phase2_check_passed"
                )
                is True
                and default_promotion.get(
                    "stack_engine_publication_publish_preflight_resident_winsorized_ready"
                )
                is True
                and default_promotion.get(
                    "stack_engine_publication_phase2_resident_winsorized_ready"
                )
                is True
                and default_promotion.get(
                    "stack_engine_publication_resident_winsorized_agreement"
                )
                is True
            )
            if require_default_promotion_ready
            else True,
            {
                "phase2_check_passed": default_promotion.get(
                    "stack_engine_publication_resident_winsorized_chain_phase2_check_passed"
                ),
                "publish_preflight_resident_winsorized_ready": default_promotion.get(
                    "stack_engine_publication_publish_preflight_resident_winsorized_ready"
                ),
                "phase2_resident_winsorized_ready": default_promotion.get(
                    "stack_engine_publication_phase2_resident_winsorized_ready"
                ),
                "resident_winsorized_agreement": default_promotion.get(
                    "stack_engine_publication_resident_winsorized_agreement"
                ),
            },
        ),
        _check(
            "default_runtime_preset",
            default_runtime_preset == "throughput-v1",
            {"actual": default_runtime_preset, "required": "throughput-v1"},
        ),
        _check(
            "runtime_repeat_ratio_within_release_bound",
            runtime_ratio is not None and runtime_ratio <= float(max_runtime_ratio),
            {"actual": runtime_ratio, "required_max": float(max_runtime_ratio)},
        ),
    ]
    if acceptance_audit_json is not None:
        checks.append(
            _check(
                "acceptance_audit_passed",
                acceptance.get("passed") is True,
                {"status": acceptance.get("status"), "path": str(acceptance_audit_json)},
            )
        )
    for label in required_cuda_packages:
        row = package_by_label.get(label)
        checks.append(
            _check(
                f"required_cuda_package_present:{label}",
                row is not None,
                {"label": label, "available": sorted(package_by_label)},
            )
        )
        checks.append(
            _check(
                f"required_cuda_package_compatible:{label}",
                row is not None and row.get("compatible") is True,
                {
                    "label": label,
                    "compatible": None if row is None else row.get("compatible"),
                    "match": None if row is None else row.get("match"),
                },
            )
        )

    failed = [item for item in checks if not item.get("passed")]
    current_device = recommendation.get("selected_device")
    payload = {
        "schema_version": 1,
        "artifact_type": "windows_release_matrix",
        "created_at": now_iso(),
        "status": "release_matrix_ready" if not failed else "blocked",
        "passed": not failed,
        "recommendation": "publish_windows_cuda_matrix" if not failed else "fix_release_matrix_blockers",
        "inputs": {
            "doctor_json": str(doctor_json),
            "release_decision_json": str(release_decision_json),
            "acceptance_audit_json": None if acceptance_audit_json is None else str(acceptance_audit_json),
            "default_promotion_manifest_json": None
            if default_promotion_manifest_json is None
            else str(default_promotion_manifest_json),
        },
        "default_runtime": {
            "resident_runtime_preset": default_runtime_preset,
            "source": "Gate181 promoted default",
            "release_decision_status": decision.get("status"),
            "default_change_ready": decision.get("default_change_ready"),
        },
        "release_decision_direct_runtime_publication_guard": (
            release_direct_publication_guard
        ),
        "release_decision_quality_compare_publication_guard": (
            release_quality_publication_guard
        ),
        "release_decision_release_quality_publication_guard": (
            release_quality_guard_publication_guard
        ),
        "default_promotion_manifest": default_promotion,
        "current_machine": {
            "cuda_available": cuda.get("cuda_available"),
            "native_extension_loaded": cuda.get("native_extension_loaded"),
            "device": current_device,
            "ordered_try_list": ordered_try_list,
            "primary_package": primary,
            "guidance": recommendation.get("guidance"),
        },
        "packages": package_rows,
        "runtime_repeat": runtime_repeat,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This artifact audits release readiness from existing GLASS artifacts; it does not build packages.",
            "CUDA package compatibility is based on detected compute capability and planned package targets.",
            "Older CUDA packages on newer GPUs may use PTX JIT and can be slower than the native package.",
        ],
    }
    return payload


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GLASS Windows Release Matrix",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Default resident runtime preset: `{(payload.get('default_runtime') or {}).get('resident_runtime_preset')}`",
        "",
        "## Current Machine",
        "",
    ]
    machine = payload.get("current_machine") if isinstance(payload.get("current_machine"), dict) else {}
    default_promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    release_guard = (
        payload.get("release_decision_direct_runtime_publication_guard")
        if isinstance(
            payload.get("release_decision_direct_runtime_publication_guard"),
            dict,
        )
        else {}
    )
    release_quality_guard = (
        payload.get("release_decision_quality_compare_publication_guard")
        if isinstance(
            payload.get("release_decision_quality_compare_publication_guard"),
            dict,
        )
        else {}
    )
    release_quality_publication_guard = (
        payload.get("release_decision_release_quality_publication_guard")
        if isinstance(
            payload.get("release_decision_release_quality_publication_guard"),
            dict,
        )
        else {}
    )
    lines.extend(
        [
            f"- CUDA available: `{machine.get('cuda_available')}`",
            f"- Native extension loaded: `{machine.get('native_extension_loaded')}`",
            f"- Primary package: `{machine.get('primary_package')}`",
            f"- Try order: `{', '.join(machine.get('ordered_try_list') or [])}`",
            f"- Guidance: {machine.get('guidance')}",
            "",
            "## Default Promotion Manifest",
            "",
            f"- Present: `{default_promotion.get('present')}`",
            f"- Status: `{default_promotion.get('status')}`",
            f"- Passed: `{default_promotion.get('passed')}`",
            f"- Default route passed: `{default_promotion.get('default_route_passed')}`",
            (
                "- Default route contract/checks: "
                f"`{default_promotion.get('default_route_route_contract_passed')}`/"
                f"`{default_promotion.get('default_route_route_check_count')}`"
            ),
            (
                "- Rejection sample accounting: "
                f"`{default_promotion.get('rejection_sample_accounting_status')}` "
                f"failed=`{default_promotion.get('rejection_sample_accounting_failed_count')}`"
            ),
            (
                "- Quality metrics compare: "
                f"present=`{default_promotion.get('quality_metrics_compare_present')}` "
                f"ready=`{default_promotion.get('quality_metrics_compare_ready')}` "
                f"status=`{default_promotion.get('quality_metrics_compare_status')}` "
                "failed-checks="
                f"`{default_promotion.get('quality_metrics_compare_failed_checks')}`"
            ),
            (
                "- Sample accounting closure: "
                f"`{default_promotion.get('sample_accounting_closure_status')}` "
                f"present=`{default_promotion.get('sample_accounting_closure_present_count')}` "
                f"failed=`{default_promotion.get('sample_accounting_closure_failed_count')}`"
            ),
            (
                "- Resident result contract: "
                f"ready=`{default_promotion.get('resident_result_contract_ready')}` "
                f"status=`{default_promotion.get('resident_result_contract_status')}` "
                f"check=`{default_promotion.get('resident_result_contract_check_passed')}` "
                "phase2="
                f"`{default_promotion.get('resident_result_contract_phase2_check_passed')}` "
                f"required=`{default_promotion.get('resident_result_contract_required_count')}` "
                f"failed=`{default_promotion.get('resident_result_contract_failed_count')}` "
                "failed-checks="
                f"`{default_promotion.get('resident_result_contract_failed_checks')}`"
            ),
            (
                "- Integration engine policy: "
                f"ready=`{default_promotion.get('integration_engine_policy_ready')}` "
                f"acceptance=`{default_promotion.get('acceptance_integration_engine_policy_status')}` "
                f"pipeline=`{default_promotion.get('pipeline_integration_engine_policy_status')}`"
            ),
            (
                "- StackEngine runtime default: "
                f"ready=`{default_promotion.get('stack_engine_runtime_default_ready')}` "
                "acceptance="
                f"`{default_promotion.get('acceptance_stack_engine_runtime_default_status')}` "
                "pipeline="
                f"`{default_promotion.get('pipeline_stack_engine_runtime_default_status')}`"
            ),
            (
                "- Runtime default counts: "
                "acceptance-legacy="
                f"`{default_promotion.get('acceptance_stack_engine_runtime_default_legacy_master_count')}` "
                "acceptance-failed-masters="
                f"`{default_promotion.get('acceptance_stack_engine_runtime_default_failed_master_count')}` "
                "pipeline-failed-outputs="
                f"`{default_promotion.get('pipeline_stack_engine_runtime_default_failed_output_count')}` "
                "explicit-cuda="
                f"`{default_promotion.get('pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count')}`"
            ),
            (
                "- Direct runtime evidence: "
                f"ready=`{default_promotion.get('runtime_default_direct_evidence_ready')}` "
                "acceptance-source="
                f"`{default_promotion.get('runtime_default_direct_acceptance_fastpath_source')}` "
                "acceptance-checks="
                f"`{default_promotion.get('runtime_default_direct_acceptance_fastpath_check_count')}` "
                "pipeline-calibration-source="
                f"`{default_promotion.get('runtime_default_direct_pipeline_calibration_source')}` "
                "resident-lights="
                f"`{default_promotion.get('runtime_default_direct_pipeline_resident_calibrated_light_count')}`"
            ),
            (
                "- Release decision direct publication guard: "
                f"ready=`{release_guard.get('ready')}` "
                f"check=`{release_guard.get('decision_check_passed')}` "
                f"source-ready=`{release_guard.get('source_ready')}` "
                f"count-ready=`{release_guard.get('count_ready')}` "
                f"lights=`{release_guard.get('raw_resident_lights')}`"
            ),
            (
                "- Release decision quality publication guard: "
                f"ready=`{release_quality_guard.get('ready')}` "
                f"check=`{release_quality_guard.get('decision_check_passed')}` "
                f"quality-present=`{release_quality_guard.get('quality_compare_present')}` "
                f"compatible-missing=`{release_quality_guard.get('compatible_missing')}`"
            ),
            (
                "- Release decision release-quality publication guard: "
                f"ready=`{release_quality_publication_guard.get('ready')}` "
                f"check=`{release_quality_publication_guard.get('decision_check_passed')}` "
                f"guard-present=`{release_quality_publication_guard.get('release_quality_guard_present')}` "
                f"compatible-missing=`{release_quality_publication_guard.get('compatible_missing')}`"
            ),
            (
                "- Release quality publication final checks: "
                f"ready=`{release_quality_publication_guard.get('final_checks_ready')}` "
                f"match=`{release_quality_publication_guard.get('final_checks_match')}` "
                f"raw=`{release_quality_publication_guard.get('raw_final_checks_ready')}` "
                f"phase2=`{release_quality_publication_guard.get('phase2_final_checks_ready')}`"
            ),
            (
                "- Default promotion direct publication guard: "
                "ready="
                f"`{default_promotion.get('release_decision_direct_runtime_publication_guard_ready')}` "
                "check="
                f"`{default_promotion.get('release_decision_direct_runtime_publication_guard_check_passed')}` "
                "source-ready="
                f"`{default_promotion.get('release_decision_direct_runtime_publication_guard_source_ready')}` "
                "count-ready="
                f"`{default_promotion.get('release_decision_direct_runtime_publication_guard_count_ready')}` "
                "lights="
                f"`{default_promotion.get('release_decision_direct_runtime_publication_guard_raw_resident_lights')}`"
            ),
            (
                "- Default promotion quality publication guard: "
                "ready="
                f"`{default_promotion.get('release_decision_quality_compare_publication_guard_ready')}` "
                "check="
                f"`{default_promotion.get('release_decision_quality_compare_publication_guard_check_passed')}` "
                "raw="
                f"`{default_promotion.get('release_decision_quality_compare_publication_guard_raw_status')}` "
                "phase2="
                f"`{default_promotion.get('release_decision_quality_compare_publication_guard_phase2_status')}`"
            ),
            (
                "- Default promotion release-quality publication guard: "
                "ready="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_ready')}` "
                "check="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_check_passed')}` "
                "raw="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_raw_matrix_raw_status')}` "
                "phase2="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_phase2_matrix_raw_status')}`"
            ),
            (
                "- Default promotion release quality final checks: "
                "ready="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_final_checks_ready')}` "
                "match="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_final_checks_match')}` "
                "raw="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_raw_final_checks_ready')}` "
                "phase2="
                f"`{default_promotion.get('release_decision_release_quality_publication_guard_phase2_final_checks_ready')}`"
            ),
            (
                "- Resident fastpath release handoff: "
                f"ready=`{default_promotion.get('resident_registration_fastpath_release_handoff_ready')}` "
                f"raw=`{default_promotion.get('resident_registration_fastpath_release_handoff_raw_status')}` "
                f"phase2=`{default_promotion.get('resident_registration_fastpath_release_handoff_phase2_status')}` "
                f"agreement=`{default_promotion.get('resident_registration_fastpath_release_handoff_agreement')}` "
                f"checks=`{default_promotion.get('resident_registration_fastpath_release_handoff_raw_passed_check_count')}`"
            ),
            (
                "- StackEngine default contract: "
                f"ready=`{default_promotion.get('stack_engine_contract_ready')}` "
                f"phase2-check=`{default_promotion.get('stack_engine_contract_phase2_check_passed')}` "
                f"gaps=`{default_promotion.get('stack_engine_contract_default_gap_count')}` "
                f"blockers=`{default_promotion.get('stack_engine_contract_blocker_count')}`"
            ),
            (
                "- Resident winsorized sweep: "
                f"passed=`{default_promotion.get('resident_winsorized_sweep_passed')}` "
                f"phase2-check=`{default_promotion.get('resident_winsorized_sweep_phase2_check_passed')}` "
                f"required-frame=`{default_promotion.get('resident_winsorized_sweep_required_frame_count')}` "
                f"required-pass=`{default_promotion.get('resident_winsorized_sweep_required_frame_count_passed')}` "
                f"checks=`{default_promotion.get('resident_winsorized_sweep_check_count')}`"
            ),
            (
                "- StackEngine publication audit: "
                f"ready=`{default_promotion.get('stack_engine_publication_audit_ready')}` "
                f"passed=`{default_promotion.get('stack_engine_publication_audit_passed')}` "
                f"phase2-check=`{default_promotion.get('stack_engine_publication_audit_phase2_check_passed')}` "
                f"failed=`{default_promotion.get('stack_engine_publication_audit_failed_check_count')}`"
            ),
            (
                "- Publication policy chain: "
                f"raw=`{default_promotion.get('stack_engine_publication_publish_preflight_policy_ready')}` "
                f"phase2=`{default_promotion.get('stack_engine_publication_phase2_policy_ready')}` "
                f"agreement=`{default_promotion.get('stack_engine_publication_policy_agreement')}` "
                f"check=`{default_promotion.get('stack_engine_publication_policy_chain_phase2_check_passed')}`"
            ),
            (
                "- Publication resident winsorized chain: "
                f"raw=`{default_promotion.get('stack_engine_publication_publish_preflight_resident_winsorized_ready')}` "
                f"phase2=`{default_promotion.get('stack_engine_publication_phase2_resident_winsorized_ready')}` "
                f"agreement=`{default_promotion.get('stack_engine_publication_resident_winsorized_agreement')}` "
                f"check=`{default_promotion.get('stack_engine_publication_resident_winsorized_chain_phase2_check_passed')}`"
            ),
            "",
            "## Packages",
            "",
            "| Package | Artifact | Compatible | Match | Role |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload.get("packages") or []:
        lines.append(
            "| "
            f"{row.get('label')} | {row.get('release_artifact')} | {row.get('compatible')} | "
            f"{row.get('match')} | {row.get('release_role')} |"
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_release_matrix(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
