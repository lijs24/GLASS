from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _quote(value: str) -> str:
    return shlex.quote(value)


def _ps_literal(value: str | None) -> str:
    if value is None:
        return "$null"
    return "'" + str(value).replace("'", "''") + "'"


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _release_direct_publication_guard_fields(
    source: dict[str, Any],
    *,
    output_prefix: str,
) -> dict[str, Any]:
    guard = (
        source.get("release_decision_direct_runtime_publication_guard")
        if isinstance(
            source.get("release_decision_direct_runtime_publication_guard"),
            dict,
        )
        else {}
    )

    def field(flat_name: str, *guard_names: str) -> Any:
        flattened = source.get(
            f"release_decision_direct_runtime_publication_guard_{flat_name}"
        )
        if flattened is not None:
            return flattened
        for guard_name in guard_names:
            value = guard.get(guard_name)
            if value is not None:
                return value
        return None

    raw_leaf = guard.get("raw_leaf_checks_ready")
    phase2_leaf = guard.get("phase2_leaf_checks_ready")
    leaf_checks_ready = field("leaf_checks_ready", "leaf_checks_ready")
    if leaf_checks_ready is None and (raw_leaf is not None or phase2_leaf is not None):
        leaf_checks_ready = raw_leaf is True and phase2_leaf is True

    return {
        output_prefix: guard,
        f"{output_prefix}_present": field("present", "present"),
        f"{output_prefix}_ready": field("ready", "ready"),
        f"{output_prefix}_check_passed": field(
            "check_passed",
            "decision_check_passed",
        ),
        f"{output_prefix}_source_ready": field("source_ready", "source_ready"),
        f"{output_prefix}_count_ready": field("count_ready", "count_ready"),
        f"{output_prefix}_leaf_checks_ready": leaf_checks_ready,
        f"{output_prefix}_raw_acceptance_source": field(
            "raw_acceptance_source",
            "raw_acceptance_source",
            "raw_matrix_acceptance_source",
        ),
        f"{output_prefix}_raw_calibration_source": field(
            "raw_calibration_source",
            "raw_calibration_source",
            "raw_matrix_pipeline_calibration_source",
        ),
        f"{output_prefix}_raw_resident_lights": _int_or_zero(
            field(
                "raw_resident_lights",
                "raw_resident_lights",
                "raw_matrix_pipeline_resident_lights",
            )
        ),
    }


def _release_direct_publication_guard_ready(
    summary: dict[str, Any],
    *,
    prefix: str,
) -> bool:
    return (
        summary.get(f"{prefix}_present") is True
        and summary.get(f"{prefix}_ready") is True
        and summary.get(f"{prefix}_check_passed") is True
        and summary.get(f"{prefix}_source_ready") is True
        and summary.get(f"{prefix}_count_ready") is True
        and summary.get(f"{prefix}_leaf_checks_ready") is True
        and summary.get(f"{prefix}_raw_acceptance_source")
        == "explicit_resident_artifacts_json"
        and summary.get(f"{prefix}_raw_calibration_source")
        == "resident_artifacts_json_fallback"
        and _int_or_zero(summary.get(f"{prefix}_raw_resident_lights")) >= 200
    )


def _release_direct_publication_guard_evidence(
    summary: dict[str, Any],
    *,
    prefix: str,
) -> dict[str, Any]:
    return {
        "present": summary.get(f"{prefix}_present"),
        "ready": summary.get(f"{prefix}_ready"),
        "decision_check_passed": summary.get(f"{prefix}_check_passed"),
        "source_ready": summary.get(f"{prefix}_source_ready"),
        "count_ready": summary.get(f"{prefix}_count_ready"),
        "leaf_checks_ready": summary.get(f"{prefix}_leaf_checks_ready"),
        "acceptance_source": summary.get(f"{prefix}_raw_acceptance_source"),
        "calibration_source": summary.get(f"{prefix}_raw_calibration_source"),
        "resident_lights": summary.get(f"{prefix}_raw_resident_lights"),
    }


def _resident_fastpath_release_handoff_fields(
    source: dict[str, Any],
    *,
    output_prefix: str,
) -> dict[str, Any]:
    handoff = (
        source.get("resident_registration_fastpath_release_handoff")
        if isinstance(source.get("resident_registration_fastpath_release_handoff"), dict)
        else {}
    )

    def field(flat_name: str, *handoff_names: str) -> Any:
        flattened = source.get(f"resident_registration_fastpath_release_handoff_{flat_name}")
        if flattened is not None:
            return flattened
        for handoff_name in handoff_names:
            value = handoff.get(handoff_name)
            if value is not None:
                return value
        return None

    return {
        output_prefix: handoff,
        f"{output_prefix}_present": field("present", "present"),
        f"{output_prefix}_ready": field("ready", "ready"),
        f"{output_prefix}_raw_ready": field("raw_ready", "raw_ready"),
        f"{output_prefix}_phase2_ready": field("phase2_ready", "phase2_ready"),
        f"{output_prefix}_agreement": field("agreement", "agreement"),
        f"{output_prefix}_decision_check_passed": field(
            "decision_check_passed",
            "decision_check_passed",
        ),
        f"{output_prefix}_phase2_check_passed": field(
            "phase2_check_passed",
            "phase2_check_passed",
        ),
        f"{output_prefix}_raw_status": field("raw_status", "raw_status"),
        f"{output_prefix}_phase2_status": field("phase2_status", "phase2_status"),
        f"{output_prefix}_raw_required": field("raw_required", "raw_required"),
        f"{output_prefix}_phase2_required": field("phase2_required", "phase2_required"),
        f"{output_prefix}_raw_mode": field("raw_mode", "raw_mode"),
        f"{output_prefix}_phase2_mode": field("phase2_mode", "phase2_mode"),
        f"{output_prefix}_raw_passed_check_count": _int_or_zero(
            field("raw_passed_check_count", "raw_passed_check_count")
        ),
        f"{output_prefix}_phase2_passed_check_count": _int_or_zero(
            field("phase2_passed_check_count", "phase2_passed_check_count")
        ),
        f"{output_prefix}_raw_failed_check_count": _int_or_zero(
            field("raw_failed_check_count", "raw_failed_check_count")
        ),
        f"{output_prefix}_phase2_failed_check_count": _int_or_zero(
            field("phase2_failed_check_count", "phase2_failed_check_count")
        ),
        f"{output_prefix}_raw_failed_checks": field(
            "raw_failed_checks",
            "raw_failed_checks",
        )
        or [],
        f"{output_prefix}_phase2_failed_checks": field(
            "phase2_failed_checks",
            "phase2_failed_checks",
        )
        or [],
    }


def _resident_fastpath_release_handoff_ready(
    summary: dict[str, Any],
    *,
    prefix: str,
) -> bool:
    return (
        summary.get(f"{prefix}_present") is True
        and summary.get(f"{prefix}_ready") is True
        and summary.get(f"{prefix}_raw_ready") is True
        and summary.get(f"{prefix}_phase2_ready") is True
        and summary.get(f"{prefix}_agreement") is True
        and summary.get(f"{prefix}_decision_check_passed") is True
        and summary.get(f"{prefix}_phase2_check_passed") is True
        and summary.get(f"{prefix}_raw_status") == "passed"
        and summary.get(f"{prefix}_phase2_status") == "passed"
        and summary.get(f"{prefix}_raw_required") is True
        and summary.get(f"{prefix}_phase2_required") is True
        and _int_or_zero(summary.get(f"{prefix}_raw_passed_check_count")) > 0
        and _int_or_zero(summary.get(f"{prefix}_phase2_passed_check_count")) > 0
        and _int_or_zero(summary.get(f"{prefix}_raw_failed_check_count")) == 0
        and _int_or_zero(summary.get(f"{prefix}_phase2_failed_check_count")) == 0
    )


def _resident_fastpath_release_handoff_evidence(
    summary: dict[str, Any],
    *,
    prefix: str,
) -> dict[str, Any]:
    return {
        "present": summary.get(f"{prefix}_present"),
        "ready": summary.get(f"{prefix}_ready"),
        "raw_ready": summary.get(f"{prefix}_raw_ready"),
        "phase2_ready": summary.get(f"{prefix}_phase2_ready"),
        "agreement": summary.get(f"{prefix}_agreement"),
        "decision_check_passed": summary.get(f"{prefix}_decision_check_passed"),
        "phase2_check_passed": summary.get(f"{prefix}_phase2_check_passed"),
        "raw_status": summary.get(f"{prefix}_raw_status"),
        "phase2_status": summary.get(f"{prefix}_phase2_status"),
        "raw_required": summary.get(f"{prefix}_raw_required"),
        "phase2_required": summary.get(f"{prefix}_phase2_required"),
        "raw_mode": summary.get(f"{prefix}_raw_mode"),
        "phase2_mode": summary.get(f"{prefix}_phase2_mode"),
        "raw_passed_check_count": summary.get(f"{prefix}_raw_passed_check_count"),
        "phase2_passed_check_count": summary.get(
            f"{prefix}_phase2_passed_check_count"
        ),
        "raw_failed_check_count": summary.get(f"{prefix}_raw_failed_check_count"),
        "phase2_failed_check_count": summary.get(
            f"{prefix}_phase2_failed_check_count"
        ),
        "raw_failed_checks": summary.get(f"{prefix}_raw_failed_checks"),
        "phase2_failed_checks": summary.get(f"{prefix}_phase2_failed_checks"),
    }


def _resident_result_contract_ready(
    summary: dict[str, Any],
    *,
    prefix: str = "resident_result_contract",
) -> bool:
    return (
        summary.get(f"{prefix}_present") is True
        and summary.get(f"{prefix}_ready") is True
        and summary.get(f"{prefix}_status") == "passed"
        and summary.get(f"{prefix}_top_level_check") is True
        and summary.get(f"{prefix}_check_present") is True
        and summary.get(f"{prefix}_check_passed") is True
        and summary.get(f"{prefix}_phase2_check_passed") is True
        and _int_or_zero(summary.get(f"{prefix}_required_count")) > 0
        and _int_or_zero(summary.get(f"{prefix}_failed_count")) == 0
        and _int_or_zero(summary.get(f"{prefix}_failed_check_count")) == 0
    )


def _resident_result_contract_evidence(
    summary: dict[str, Any],
    *,
    prefix: str = "resident_result_contract",
) -> dict[str, Any]:
    return {
        "present": summary.get(f"{prefix}_present"),
        "ready": summary.get(f"{prefix}_ready"),
        "status": summary.get(f"{prefix}_status"),
        "top_level_check": summary.get(f"{prefix}_top_level_check"),
        "check_present": summary.get(f"{prefix}_check_present"),
        "check_passed": summary.get(f"{prefix}_check_passed"),
        "phase2_check_passed": summary.get(f"{prefix}_phase2_check_passed"),
        "required_count": summary.get(f"{prefix}_required_count"),
        "failed_count": summary.get(f"{prefix}_failed_count"),
        "failed_check_count": summary.get(f"{prefix}_failed_check_count"),
        "failed_checks": summary.get(f"{prefix}_failed_checks"),
        "failed_items": summary.get(f"{prefix}_failed_items"),
    }


def _asset_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in manifest.get("packages") or []:
        if not isinstance(row, dict):
            continue
        zip_path = row.get("zip_path")
        zip_file = Path(str(zip_path)).resolve() if zip_path else None
        rows.append(
            {
                "label": row.get("label"),
                "zip_path": None if zip_file is None else str(zip_file),
                "exists": bool(zip_file is not None and zip_file.exists() and zip_file.is_file()),
                "size_bytes": row.get("size_bytes"),
                "sha256": row.get("sha256"),
                "source_stamp": row.get("source_stamp"),
            }
        )
    return rows


def _phase2_artifact_summary(
    path: str | Path | None,
    *,
    expected_artifact_type: str,
) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    payload = _read_json_object(target) if target.exists() else {}
    latest_checkpoint = (
        payload.get("latest_checkpoint")
        if isinstance(payload.get("latest_checkpoint"), dict)
        else {}
    )
    acceptance = payload.get("acceptance_audit") if isinstance(payload.get("acceptance_audit"), dict) else {}
    native_guardrails_bundle = (
        acceptance.get("native_guardrails_bundle")
        if isinstance(acceptance.get("native_guardrails_bundle"), dict)
        else None
    )
    registration_fastpath = (
        acceptance.get("resident_registration_fastpath")
        if isinstance(acceptance.get("resident_registration_fastpath"), dict)
        else None
    )
    baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    pipeline_contract = (
        payload.get("pipeline_contract")
        if isinstance(payload.get("pipeline_contract"), dict)
        else None
    )
    stack_engine_contract = (
        payload.get("stack_engine_contract")
        if isinstance(payload.get("stack_engine_contract"), dict)
        else None
    )
    release_decision = (
        payload.get("release_decision")
        if isinstance(payload.get("release_decision"), dict)
        else None
    )
    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    check_states = {str(item.get("name")): item.get("passed") for item in checks}
    stack_gap_count = (stack_engine_contract or {}).get(
        "default_promotion_phase2_stack_engine_default_gap_count"
    )
    if stack_gap_count is None:
        stack_gap_count = (stack_engine_contract or {}).get(
            "adoption_phase2_stack_engine_default_gap_count"
        )
    return {
        "path": str(target),
        "exists": target.exists(),
        "artifact_type": payload.get("artifact_type"),
        "expected_artifact_type": expected_artifact_type,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "latest_gate": latest_checkpoint.get("gate"),
        "baseline_gate": baseline.get("latest_gate"),
        "candidate_gate": candidate.get("latest_gate"),
        "acceptance_status": acceptance.get("status"),
        "native_guardrails_bundle": native_guardrails_bundle,
        "native_guardrails_bundle_status": acceptance.get("native_guardrails_bundle_status")
        or (native_guardrails_bundle or {}).get("status"),
        "resident_result_contract_source": acceptance.get("resident_result_contract_source")
        or (native_guardrails_bundle or {}).get("resident_result_contract_source"),
        "resident_result_contract_run_default": acceptance.get("resident_result_contract_run_default")
        if acceptance.get("resident_result_contract_run_default") is not None
        else (native_guardrails_bundle or {}).get("resident_result_contract_run_default"),
        "resident_result_contract_json": acceptance.get("resident_result_contract_json")
        or (native_guardrails_bundle or {}).get("resident_result_contract_json"),
        "resident_native_calibration_artifact": acceptance.get("resident_native_calibration_artifact")
        if acceptance.get("resident_native_calibration_artifact") is not None
        else (native_guardrails_bundle or {}).get("resident_native_calibration_artifact"),
        "resident_calibration_master_count": acceptance.get("resident_calibration_master_count")
        or (native_guardrails_bundle or {}).get("resident_calibration_master_count"),
        "resident_calibrated_light_count": acceptance.get("resident_calibrated_light_count")
        or (native_guardrails_bundle or {}).get("resident_calibrated_light_count"),
        "resident_registration_fastpath": registration_fastpath,
        "resident_registration_fastpath_status": acceptance.get(
            "resident_registration_fastpath_status"
        )
        or (registration_fastpath or {}).get("status"),
        "resident_registration_fastpath_contract_status": acceptance.get(
            "resident_registration_fastpath_contract_status"
        )
        or (registration_fastpath or {}).get("contract_status"),
        "resident_registration_fastpath_mode": acceptance.get("resident_registration_fastpath_mode")
        or (registration_fastpath or {}).get("mode"),
        "triangle_descriptor_fit_batch": acceptance.get("triangle_descriptor_fit_batch")
        if acceptance.get("triangle_descriptor_fit_batch") is not None
        else (registration_fastpath or {}).get("triangle_descriptor_fit_batch"),
        "triangle_descriptor_fit_batch_mode": acceptance.get("triangle_descriptor_fit_batch_mode")
        or (registration_fastpath or {}).get("triangle_descriptor_fit_batch_mode"),
        "triangle_descriptor_fit_device_reuse": acceptance.get(
            "triangle_descriptor_fit_device_reuse"
        )
        or (registration_fastpath or {}).get("triangle_descriptor_fit_device_reuse"),
        "triangle_pixel_refine_batch": acceptance.get("triangle_pixel_refine_batch")
        if acceptance.get("triangle_pixel_refine_batch") is not None
        else (registration_fastpath or {}).get("triangle_pixel_refine_batch"),
        "triangle_pixel_refine_batch_metric_mode": acceptance.get(
            "triangle_pixel_refine_batch_metric_mode"
        )
        or (registration_fastpath or {}).get("triangle_pixel_refine_batch_metric_mode"),
        "triangle_warp_batch": acceptance.get("triangle_warp_batch")
        if acceptance.get("triangle_warp_batch") is not None
        else (registration_fastpath or {}).get("triangle_warp_batch"),
        "triangle_warp_batch_mode": acceptance.get("triangle_warp_batch_mode")
        or (registration_fastpath or {}).get("triangle_warp_batch_mode"),
        "triangle_warp_batch_frame_count": acceptance.get("triangle_warp_batch_frame_count")
        if acceptance.get("triangle_warp_batch_frame_count") is not None
        else (registration_fastpath or {}).get("triangle_warp_batch_frame_count"),
        "resident_warp_copy_mode": acceptance.get("resident_warp_copy_mode")
        or (registration_fastpath or {}).get("resident_warp_copy_mode"),
        "resident_warp_scratch_bytes": acceptance.get("resident_warp_scratch_bytes")
        if acceptance.get("resident_warp_scratch_bytes") is not None
        else (registration_fastpath or {}).get("resident_warp_scratch_bytes"),
        "resident_registration_fastpath_contract_check_count": acceptance.get(
            "resident_registration_fastpath_contract_check_count"
        )
        if acceptance.get("resident_registration_fastpath_contract_check_count") is not None
        else (registration_fastpath or {}).get("contract_check_count"),
        "resident_registration_fastpath_contract_failed_check_count": acceptance.get(
            "resident_registration_fastpath_contract_failed_check_count"
        )
        if acceptance.get("resident_registration_fastpath_contract_failed_check_count") is not None
        else (registration_fastpath or {}).get("contract_failed_check_count"),
        "pipeline_contract": pipeline_contract,
        "pipeline_contract_status": (pipeline_contract or {}).get("status"),
        "pipeline_contract_passed": (pipeline_contract or {}).get("passed"),
        "pipeline_contract_failed_check_count": (pipeline_contract or {}).get("failed_check_count"),
        "pipeline_integration_output_count": (pipeline_contract or {}).get("integration_output_count"),
        "pipeline_integration_map_count": (pipeline_contract or {}).get("integration_map_count"),
        "pipeline_integration_dq_contract": (pipeline_contract or {}).get("integration_dq_contract"),
        "pipeline_integration_stack_result_contract": (pipeline_contract or {}).get(
            "integration_stack_result_contract"
        ),
        "pipeline_integration_resident_result_contract": (pipeline_contract or {}).get(
            "integration_resident_result_contract"
        ),
        "pipeline_pixel_verification_enabled": (pipeline_contract or {}).get(
            "pixel_verification_enabled"
        ),
        "pipeline_integration_dq_map_pixels_match_summary": (pipeline_contract or {}).get(
            "integration_dq_map_pixels_match_summary"
        ),
        "pipeline_integration_coverage_map_pixels_match_dq": (pipeline_contract or {}).get(
            "integration_coverage_map_pixels_match_dq"
        ),
        "pipeline_integration_rejection_map_pixels_match_dq": (pipeline_contract or {}).get(
            "integration_rejection_map_pixels_match_dq"
        ),
        "pipeline_integration_rejection_sample_counts_match_maps": (
            pipeline_contract or {}
        ).get("integration_rejection_sample_counts_match_maps"),
        "pipeline_rejection_sample_accounting_status": (pipeline_contract or {}).get(
            "rejection_sample_accounting_status"
        ),
        "pipeline_rejection_sample_accounting_failed_count": (
            pipeline_contract or {}
        ).get("rejection_sample_accounting_failed_count"),
        "pipeline_integration_sample_accounting_closure": (
            pipeline_contract or {}
        ).get("integration_sample_accounting_closure"),
        "pipeline_sample_accounting_closure": (pipeline_contract or {}).get(
            "sample_accounting_closure"
        ),
        "pipeline_sample_accounting_closure_status": (pipeline_contract or {}).get(
            "sample_accounting_closure_status"
        ),
        "pipeline_sample_accounting_closure_present_count": (
            pipeline_contract or {}
        ).get("sample_accounting_closure_present_count"),
        "pipeline_sample_accounting_closure_failed_count": (
            pipeline_contract or {}
        ).get("sample_accounting_closure_failed_count"),
        "stack_engine_contract": stack_engine_contract,
        "stack_engine_default_contract_present": stack_engine_contract is not None,
        "stack_engine_default_contract_phase2_check_passed": check_states.get(
            "stack_engine_default_contract_ready"
        ),
        "stack_engine_default_contract_audit_type": (stack_engine_contract or {}).get(
            "audit_type"
        ),
        "stack_engine_default_contract_status": (stack_engine_contract or {}).get(
            "status"
        ),
        "stack_engine_default_contract_passed": (stack_engine_contract or {}).get(
            "passed"
        ),
        "stack_engine_default_contract_scope": (stack_engine_contract or {}).get(
            "scope"
        ),
        "stack_engine_default_contract_default_promotion_ready": (
            stack_engine_contract or {}
        ).get("default_promotion_ready"),
        "stack_engine_default_contract_default_promotion_status": (
            stack_engine_contract or {}
        ).get("default_promotion_status"),
        "stack_engine_default_contract_adoption_recommendation": (
            stack_engine_contract or {}
        ).get("adoption_recommendation"),
        "stack_engine_default_contract_default_promotion_recommendation": (
            stack_engine_contract or {}
        ).get("default_promotion_recommendation"),
        "stack_engine_default_contract_default_gap_count": stack_gap_count,
        "stack_engine_default_contract_blocker_count": (stack_engine_contract or {}).get(
            "default_promotion_blocker_count"
        ),
        "stack_engine_default_contract_blockers": (stack_engine_contract or {}).get(
            "default_promotion_blockers"
        )
        or [],
        "release_decision": release_decision,
        "release_decision_status": (release_decision or {}).get("status"),
        "release_decision_recommendation": (release_decision or {}).get("recommendation"),
        "release_decision_release_candidate_ready": (release_decision or {}).get(
            "release_candidate_ready"
        ),
        "release_decision_default_change_ready": (release_decision or {}).get(
            "default_change_ready"
        ),
        "release_decision_speedup_actual": (release_decision or {}).get("speedup_actual"),
        "release_runtime_repeat_run_count": (release_decision or {}).get(
            "runtime_repeat_run_count"
        ),
        "release_runtime_repeat_best_label": (release_decision or {}).get(
            "runtime_repeat_best_label"
        ),
        "release_runtime_repeat_best_elapsed_s": (release_decision or {}).get(
            "runtime_repeat_best_elapsed_s"
        ),
        "release_runtime_repeat_elapsed_ratio_vs_best": (release_decision or {}).get(
            "runtime_repeat_elapsed_ratio_vs_best"
        ),
        "release_runtime_repeat_max_elapsed_ratio_vs_best": (release_decision or {}).get(
            "runtime_repeat_max_elapsed_ratio_vs_best"
        ),
    }


def _windows_release_matrix_summary(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    payload = _read_json_object(target) if target.exists() else {}
    current_machine = (
        payload.get("current_machine") if isinstance(payload.get("current_machine"), dict) else {}
    )
    default_promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    package_rows = [row for row in payload.get("packages") or [] if isinstance(row, dict)]
    package_labels = [str(row.get("label")) for row in package_rows if row.get("label")]
    return {
        "path": str(target),
        "exists": target.exists(),
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "primary_package": current_machine.get("primary_package"),
        "ordered_try_list": [str(item) for item in current_machine.get("ordered_try_list") or []],
        "cuda_available": current_machine.get("cuda_available"),
        "native_extension_loaded": current_machine.get("native_extension_loaded"),
        "package_labels": package_labels,
        "package_count": len(package_labels),
        "default_promotion_status": default_promotion.get("status"),
        "default_promotion_passed": default_promotion.get("passed"),
        "default_promotion_default_change_ready": default_promotion.get("default_change_ready"),
        "default_route_passed": default_promotion.get("default_route_passed"),
        "default_route_route_contract_passed": default_promotion.get(
            "default_route_route_contract_passed"
        ),
        "default_route_route_check_count": default_promotion.get("default_route_route_check_count"),
        "default_route_speedup_vs_reference": default_promotion.get(
            "default_route_speedup_vs_reference"
        ),
        "rejection_sample_accounting_status": default_promotion.get(
            "rejection_sample_accounting_status"
        ),
        "rejection_sample_accounting_failed_count": default_promotion.get(
            "rejection_sample_accounting_failed_count"
        ),
        "integration_rejection_sample_counts_match_maps": default_promotion.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "integration_sample_accounting_closure": default_promotion.get(
            "integration_sample_accounting_closure"
        ),
        "sample_accounting_closure": default_promotion.get("sample_accounting_closure"),
        "sample_accounting_closure_status": default_promotion.get(
            "sample_accounting_closure_status"
        ),
        "sample_accounting_closure_present_count": default_promotion.get(
            "sample_accounting_closure_present_count"
        ),
        "sample_accounting_closure_failed_count": default_promotion.get(
            "sample_accounting_closure_failed_count"
        ),
        "resident_result_contract": default_promotion.get("resident_result_contract"),
        "resident_result_contract_present": default_promotion.get(
            "resident_result_contract_present"
        ),
        "resident_result_contract_ready": default_promotion.get(
            "resident_result_contract_ready"
        ),
        "resident_result_contract_status": default_promotion.get(
            "resident_result_contract_status"
        ),
        "resident_result_contract_top_level_check": default_promotion.get(
            "resident_result_contract_top_level_check"
        ),
        "resident_result_contract_check_present": default_promotion.get(
            "resident_result_contract_check_present"
        ),
        "resident_result_contract_check_passed": default_promotion.get(
            "resident_result_contract_check_passed"
        ),
        "resident_result_contract_phase2_check_passed": default_promotion.get(
            "resident_result_contract_phase2_check_passed"
        ),
        "resident_result_contract_required_count": default_promotion.get(
            "resident_result_contract_required_count"
        ),
        "resident_result_contract_failed_count": default_promotion.get(
            "resident_result_contract_failed_count"
        ),
        "resident_result_contract_failed_check_count": default_promotion.get(
            "resident_result_contract_failed_check_count"
        ),
        "resident_result_contract_failed_checks": default_promotion.get(
            "resident_result_contract_failed_checks"
        )
        or [],
        "resident_result_contract_failed_items": default_promotion.get(
            "resident_result_contract_failed_items"
        )
        or [],
        "stack_engine_contract": default_promotion.get("stack_engine_contract"),
        "stack_engine_contract_present": default_promotion.get(
            "stack_engine_contract_present"
        ),
        "stack_engine_contract_ready": default_promotion.get("stack_engine_contract_ready"),
        "stack_engine_contract_phase2_check_passed": default_promotion.get(
            "stack_engine_contract_phase2_check_passed"
        ),
        "stack_engine_contract_status": default_promotion.get("stack_engine_contract_status"),
        "stack_engine_contract_passed": default_promotion.get("stack_engine_contract_passed"),
        "stack_engine_contract_scope": default_promotion.get("stack_engine_contract_scope"),
        "stack_engine_contract_adoption_recommendation": default_promotion.get(
            "stack_engine_contract_adoption_recommendation"
        ),
        "stack_engine_contract_default_gap_count": default_promotion.get(
            "stack_engine_contract_default_gap_count"
        ),
        "stack_engine_contract_blocker_count": default_promotion.get(
            "stack_engine_contract_blocker_count"
        ),
        "stack_engine_contract_blockers": default_promotion.get(
            "stack_engine_contract_blockers"
        )
        or [],
        **_resident_fastpath_release_handoff_fields(
            default_promotion,
            output_prefix="resident_registration_fastpath_release_handoff",
        ),
        **_release_direct_publication_guard_fields(
            payload,
            output_prefix="release_decision_direct_runtime_publication_guard",
        ),
        **_release_direct_publication_guard_fields(
            default_promotion,
            output_prefix=(
                "default_promotion_release_decision_direct_runtime_publication_guard"
            ),
        ),
    }


def _run_gh(command: list[str], *, timeout_s: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_s,
        )
    except Exception as exc:  # pragma: no cover - environment-specific diagnostics
        return {
            "command": command,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "exception": type(exc).__name__,
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "exception": None,
    }


def _has_native_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "native_guardrails_bundle_status",
            "resident_result_contract_source",
            "resident_result_contract_run_default",
            "resident_result_contract_json",
            "resident_native_calibration_artifact",
            "resident_calibration_master_count",
            "resident_calibrated_light_count",
        )
    )


def _has_registration_fastpath_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "resident_registration_fastpath_status",
            "resident_registration_fastpath_contract_status",
            "resident_registration_fastpath_mode",
            "triangle_descriptor_fit_batch",
            "triangle_descriptor_fit_batch_mode",
            "triangle_descriptor_fit_device_reuse",
            "triangle_pixel_refine_batch",
            "triangle_pixel_refine_batch_metric_mode",
            "triangle_warp_batch",
            "triangle_warp_batch_mode",
            "triangle_warp_batch_frame_count",
            "resident_warp_copy_mode",
            "resident_warp_scratch_bytes",
            "resident_registration_fastpath_contract_check_count",
            "resident_registration_fastpath_contract_failed_check_count",
        )
    )


def _has_pipeline_contract_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "pipeline_contract_status",
            "pipeline_contract_passed",
            "pipeline_integration_dq_contract",
            "pipeline_integration_stack_result_contract",
            "pipeline_integration_resident_result_contract",
            "pipeline_pixel_verification_enabled",
            "pipeline_integration_dq_map_pixels_match_summary",
            "pipeline_integration_coverage_map_pixels_match_dq",
            "pipeline_integration_rejection_map_pixels_match_dq",
            "pipeline_integration_rejection_sample_counts_match_maps",
            "pipeline_rejection_sample_accounting_status",
            "pipeline_rejection_sample_accounting_failed_count",
            "pipeline_integration_sample_accounting_closure",
            "pipeline_sample_accounting_closure_status",
            "pipeline_sample_accounting_closure_present_count",
            "pipeline_sample_accounting_closure_failed_count",
        )
    )


def _has_stack_engine_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "stack_engine_default_contract_present",
            "stack_engine_default_contract_phase2_check_passed",
            "stack_engine_default_contract_status",
            "stack_engine_default_contract_scope",
            "stack_engine_default_contract_default_gap_count",
            "stack_engine_default_contract_blocker_count",
        )
    )


def _phase2_stack_engine_default_contract_ready(phase2_status: dict[str, Any]) -> bool:
    return (
        phase2_status.get("stack_engine_default_contract_present") is True
        and phase2_status.get("stack_engine_default_contract_phase2_check_passed") is True
        and phase2_status.get("stack_engine_default_contract_audit_type")
        == "stack_engine_default_contract"
        and phase2_status.get("stack_engine_default_contract_status") == "passed"
        and phase2_status.get("stack_engine_default_contract_passed") is True
        and phase2_status.get("stack_engine_default_contract_default_promotion_ready") is True
        and phase2_status.get("stack_engine_default_contract_default_promotion_status") == "ready"
        and phase2_status.get("stack_engine_default_contract_adoption_recommendation")
        == "stack_engine_default_ready"
        and phase2_status.get("stack_engine_default_contract_default_promotion_recommendation")
        == "stack_engine_default_ready"
        and _int_or_zero(phase2_status.get("stack_engine_default_contract_default_gap_count"))
        == 0
        and _int_or_zero(phase2_status.get("stack_engine_default_contract_blocker_count"))
        == 0
    )


def _windows_release_matrix_stack_engine_contract_ready(
    release_matrix: dict[str, Any],
) -> bool:
    return (
        release_matrix.get("stack_engine_contract_present") is True
        and release_matrix.get("stack_engine_contract_ready") is True
        and release_matrix.get("stack_engine_contract_phase2_check_passed") is True
        and release_matrix.get("stack_engine_contract_status") == "passed"
        and release_matrix.get("stack_engine_contract_passed") is True
        and release_matrix.get("stack_engine_contract_scope") == "all"
        and release_matrix.get("stack_engine_contract_adoption_recommendation")
        == "stack_engine_default_ready"
        and _int_or_zero(release_matrix.get("stack_engine_contract_default_gap_count")) == 0
        and _int_or_zero(release_matrix.get("stack_engine_contract_blocker_count")) == 0
    )


def _has_release_decision_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "release_decision_status",
            "release_decision_recommendation",
            "release_decision_default_change_ready",
            "release_runtime_repeat_run_count",
            "release_runtime_repeat_elapsed_ratio_vs_best",
        )
    )


def _release_notes(payload: dict[str, Any]) -> str:
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    phase2_compare = phase2.get("status_compare") if isinstance(phase2.get("status_compare"), dict) else {}
    release_matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    install_order = release_matrix.get("ordered_try_list") or ["cuda13", "cuda12", "cuda11", "cpu"]
    lines = [
        f"# {payload['release']['title']}",
        "",
        "Windows portable packages for GLASS.",
        "",
        f"- Source stamp: `{', '.join(payload.get('source_stamps') or [])}`",
        f"- Package count: `{len(payload.get('assets') or [])}`",
        "",
        "## Assets",
        "",
        "| Label | Size bytes | SHA256 |",
        "| --- | ---: | --- |",
    ]
    for asset in payload.get("assets") or []:
        lines.append(
            f"| {asset.get('label')} | {asset.get('size_bytes')} | `{asset.get('sha256')}` |"
        )
    lines.extend(
        [
            "",
            "## Recommended Install Order",
            "",
            "Try " + ", then ".join(f"`{item}`" for item in install_order) + ".",
            "",
        ]
    )
    if release_matrix:
        lines.extend(
            [
                "## Windows Release Matrix Evidence",
                "",
                (
                    "- Windows release matrix: "
                    f"`{release_matrix.get('status')}` passed `{release_matrix.get('passed')}`"
                ),
                (
                    "- Primary package: "
                    f"`{release_matrix.get('primary_package')}` "
                    f"packages `{', '.join(release_matrix.get('package_labels') or [])}`"
                ),
                (
                    "- Default promotion: "
                    f"`{release_matrix.get('default_promotion_status')}` "
                    f"passed `{release_matrix.get('default_promotion_passed')}`"
                ),
                (
                    "- Default route contract: "
                    f"`{release_matrix.get('default_route_route_contract_passed')}` "
                    f"checks `{release_matrix.get('default_route_route_check_count')}` "
                    f"speedup `{release_matrix.get('default_route_speedup_vs_reference')}`"
                ),
                (
                    "- Release direct publication guard: "
                    f"ready `{release_matrix.get('release_decision_direct_runtime_publication_guard_ready')}` "
                    "check "
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_check_passed')}` "
                    "source "
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_raw_acceptance_source')}`/"
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_raw_calibration_source')}` "
                    "lights "
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_raw_resident_lights')}`"
                ),
                (
                    "- Default-promotion release direct guard: "
                    f"ready `{release_matrix.get('default_promotion_release_decision_direct_runtime_publication_guard_ready')}` "
                    "check "
                    f"`{release_matrix.get('default_promotion_release_decision_direct_runtime_publication_guard_check_passed')}` "
                    "lights "
                    f"`{release_matrix.get('default_promotion_release_decision_direct_runtime_publication_guard_raw_resident_lights')}`"
                ),
                (
                    "- StackEngine default contract: "
                    f"ready `{release_matrix.get('stack_engine_contract_ready')}` "
                    "phase2-check "
                    f"`{release_matrix.get('stack_engine_contract_phase2_check_passed')}` "
                    f"gaps `{release_matrix.get('stack_engine_contract_default_gap_count')}` "
                    f"blockers `{release_matrix.get('stack_engine_contract_blocker_count')}`"
                ),
                (
                    "- Resident fastpath release handoff: "
                    f"ready `{release_matrix.get('resident_registration_fastpath_release_handoff_ready')}` "
                    f"raw `{release_matrix.get('resident_registration_fastpath_release_handoff_raw_status')}` "
                    f"phase2 `{release_matrix.get('resident_registration_fastpath_release_handoff_phase2_status')}` "
                    f"agreement `{release_matrix.get('resident_registration_fastpath_release_handoff_agreement')}` "
                    f"checks `{release_matrix.get('resident_registration_fastpath_release_handoff_raw_passed_check_count')}`"
                ),
                (
                    "- Resident result contract: "
                    f"ready `{release_matrix.get('resident_result_contract_ready')}` "
                    f"status `{release_matrix.get('resident_result_contract_status')}` "
                    f"phase2 `{release_matrix.get('resident_result_contract_phase2_check_passed')}` "
                    f"required `{release_matrix.get('resident_result_contract_required_count')}` "
                    f"failed `{release_matrix.get('resident_result_contract_failed_count')}`"
                ),
                (
                    "- Rejection sample accounting: "
                    f"`{release_matrix.get('rejection_sample_accounting_status')}` "
                    f"failed `{release_matrix.get('rejection_sample_accounting_failed_count')}`"
                ),
                (
                    "- Sample accounting closure: "
                    f"`{release_matrix.get('sample_accounting_closure_status')}` "
                    f"present `{release_matrix.get('sample_accounting_closure_present_count')}` "
                    f"failed `{release_matrix.get('sample_accounting_closure_failed_count')}`"
                ),
                "",
            ]
        )
    if phase2_status or phase2_compare:
        lines.extend(
            [
                "## Phase 2 Handoff Evidence",
                "",
                f"- Phase 2 status: `{phase2_status.get('status')}` gate `{phase2_status.get('latest_gate')}`",
            ]
        )
        if _has_native_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Native resident contract source: "
                        f"`{phase2_status.get('resident_result_contract_source')}` "
                        f"run-default `{phase2_status.get('resident_result_contract_run_default')}`"
                    ),
                    (
                        "- Native calibration artifact: "
                        f"`{phase2_status.get('resident_native_calibration_artifact')}` "
                        f"masters `{phase2_status.get('resident_calibration_master_count')}` "
                        f"calibrated lights `{phase2_status.get('resident_calibrated_light_count')}`"
                    ),
                ]
            )
        if _has_registration_fastpath_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Resident registration fast path: "
                        f"`{phase2_status.get('resident_registration_fastpath_status')}` "
                        "contract "
                        f"`{phase2_status.get('resident_registration_fastpath_contract_status')}` "
                        f"mode `{phase2_status.get('resident_registration_fastpath_mode')}`"
                    ),
                    (
                        "- Fast path details: descriptor batch "
                        f"`{phase2_status.get('triangle_descriptor_fit_batch')}`, "
                        f"pixel refine batch `{phase2_status.get('triangle_pixel_refine_batch')}`, "
                        f"warp batch `{phase2_status.get('triangle_warp_batch')}` "
                        f"frames `{phase2_status.get('triangle_warp_batch_frame_count')}`, "
                        f"copy `{phase2_status.get('resident_warp_copy_mode')}`"
                    ),
                ]
            )
        if _has_pipeline_contract_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Pipeline DQ contract: "
                        f"`{phase2_status.get('pipeline_contract_status')}` "
                        f"passed `{phase2_status.get('pipeline_contract_passed')}` "
                        f"DQ `{phase2_status.get('pipeline_integration_dq_contract')}`"
                    ),
                    (
                        "- Pipeline pixel verification: "
                        f"`{phase2_status.get('pipeline_pixel_verification_enabled')}` "
                        "DQ pixels "
                        f"`{phase2_status.get('pipeline_integration_dq_map_pixels_match_summary')}` "
                        "coverage "
                        f"`{phase2_status.get('pipeline_integration_coverage_map_pixels_match_dq')}` "
                        "rejection "
                        f"`{phase2_status.get('pipeline_integration_rejection_map_pixels_match_dq')}`"
                    ),
                    (
                        "- Pipeline rejection sample accounting: "
                        f"`{phase2_status.get('pipeline_rejection_sample_accounting_status')}` "
                        "check "
                        f"`{phase2_status.get('pipeline_integration_rejection_sample_counts_match_maps')}` "
                        f"failed `{phase2_status.get('pipeline_rejection_sample_accounting_failed_count')}`"
                    ),
                    (
                        "- Pipeline sample accounting closure: "
                        f"`{phase2_status.get('pipeline_sample_accounting_closure_status')}` "
                        "check "
                        f"`{phase2_status.get('pipeline_integration_sample_accounting_closure')}` "
                        f"failed `{phase2_status.get('pipeline_sample_accounting_closure_failed_count')}`"
                    ),
                ]
            )
        if _has_stack_engine_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- StackEngine default contract: "
                        f"`{phase2_status.get('stack_engine_default_contract_status')}` "
                        "check "
                        f"`{phase2_status.get('stack_engine_default_contract_phase2_check_passed')}` "
                        f"gaps `{phase2_status.get('stack_engine_default_contract_default_gap_count')}` "
                        "blockers "
                        f"`{phase2_status.get('stack_engine_default_contract_blocker_count')}`"
                    ),
                    (
                        "- StackEngine default recommendation: "
                        f"`{phase2_status.get('stack_engine_default_contract_adoption_recommendation')}` "
                        "promotion "
                        f"`{phase2_status.get('stack_engine_default_contract_default_promotion_recommendation')}`"
                    ),
                ]
            )
        if _has_release_decision_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Default-change decision: "
                        f"`{phase2_status.get('release_decision_status')}` "
                        f"ready `{phase2_status.get('release_decision_default_change_ready')}` "
                        f"recommendation `{phase2_status.get('release_decision_recommendation')}`"
                    ),
                    (
                        "- Runtime repeat evidence: runs "
                        f"`{phase2_status.get('release_runtime_repeat_run_count')}`, "
                        f"best `{phase2_status.get('release_runtime_repeat_best_label')}` "
                        f"`{phase2_status.get('release_runtime_repeat_best_elapsed_s')}` s, "
                        "ratio "
                        f"`{phase2_status.get('release_runtime_repeat_elapsed_ratio_vs_best')}`"
                    ),
                ]
            )
        lines.extend(
            [
                (
                    "- Phase 2 status compare: "
                    f"`{phase2_compare.get('status')}` "
                    f"baseline `{phase2_compare.get('baseline_gate')}` "
                    f"candidate `{phase2_compare.get('candidate_gate')}`"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _powershell_release_script(payload: dict[str, Any]) -> str:
    release = payload.get("release") if isinstance(payload.get("release"), dict) else {}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    phase2_compare = phase2.get("status_compare") if isinstance(phase2.get("status_compare"), dict) else {}
    release_matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    gh_path = gh.get("path") or "gh"
    notes_file = release.get("notes_file")
    assets = payload.get("assets") if isinstance(payload.get("assets"), list) else []

    lines = [
        "param(",
        f"    [string]$GhPath = {_ps_literal(str(gh_path))},",
        "    [switch]$Publish",
        ")",
        "",
        "$ErrorActionPreference = 'Stop'",
        f"$ExpectedTag = {_ps_literal(str(release.get('tag') or ''))}",
        f"$ReleaseTitle = {_ps_literal(str(release.get('title') or ''))}",
        f"$NotesFile = {_ps_literal(str(notes_file) if notes_file else None)}",
        f"$WindowsReleaseMatrixFile = {_ps_literal(release_matrix.get('path'))}",
        f"$Phase2StatusFile = {_ps_literal(phase2_status.get('path'))}",
        f"$Phase2StatusCompareFile = {_ps_literal(phase2_compare.get('path'))}",
        "$Assets = @(",
    ]
    for index, asset in enumerate(assets):
        suffix = "," if index + 1 < len(assets) else ""
        lines.append(
            "    @{"
            f" Label = {_ps_literal(str(asset.get('label') or ''))};"
            f" Path = {_ps_literal(str(asset.get('zip_path') or ''))};"
            f" Sha256 = {_ps_literal(str(asset.get('sha256') or ''))};"
            f" SizeBytes = {int(asset.get('size_bytes') or 0)}"
            f" }}{suffix}"
        )
    lines.extend(
        [
            ")",
            "",
            "if (-not (Get-Command $GhPath -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $GhPath -PathType Leaf)) {",
            "    throw \"GitHub CLI not found: $GhPath\"",
            "}",
            "& $GhPath auth status | Out-Host",
            "if ($LASTEXITCODE -ne 0) {",
            "    throw 'GitHub CLI authentication check failed. Run gh auth login, then retry.'",
            "}",
            "",
            "foreach ($asset in $Assets) {",
            "    if (-not (Test-Path -LiteralPath $asset.Path -PathType Leaf)) {",
            "        throw \"Missing release asset: $($asset.Path)\"",
            "    }",
            "    $actualSize = (Get-Item -LiteralPath $asset.Path).Length",
            "    if ($actualSize -ne [int64]$asset.SizeBytes) {",
            "        throw \"Asset size mismatch for $($asset.Label): expected $($asset.SizeBytes), got $actualSize\"",
            "    }",
            "    $actualSha = (Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256).Hash.ToLowerInvariant()",
            "    if ($actualSha -ne $asset.Sha256.ToLowerInvariant()) {",
            "        throw \"Asset SHA256 mismatch for $($asset.Label): expected $($asset.Sha256), got $actualSha\"",
            "    }",
            "}",
            "if ($NotesFile -and -not (Test-Path -LiteralPath $NotesFile -PathType Leaf)) {",
            "    throw \"Missing release notes file: $NotesFile\"",
            "}",
            "if ($WindowsReleaseMatrixFile) {",
            "    if (-not (Test-Path -LiteralPath $WindowsReleaseMatrixFile -PathType Leaf)) {",
            "        throw \"Missing Windows release matrix artifact: $WindowsReleaseMatrixFile\"",
            "    }",
            "    $matrix = Get-Content -LiteralPath $WindowsReleaseMatrixFile -Raw | ConvertFrom-Json",
            "    if ($matrix.artifact_type -ne 'windows_release_matrix' -or $matrix.status -ne 'release_matrix_ready' -or $matrix.passed -ne $true) {",
            "        throw \"Windows release matrix check failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    if (-not $matrix.default_promotion_manifest -or $matrix.default_promotion_manifest.status -ne 'default_promotion_ready' -or $matrix.default_promotion_manifest.passed -ne $true -or $matrix.default_promotion_manifest.default_route_passed -ne $true) {",
            "        throw \"Windows release matrix default-promotion evidence failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    if ($matrix.default_promotion_manifest.integration_rejection_sample_counts_match_maps -ne $true -or $matrix.default_promotion_manifest.rejection_sample_accounting_status -ne 'passed' -or [int]$matrix.default_promotion_manifest.rejection_sample_accounting_failed_count -ne 0) {",
            "        throw \"Windows release matrix rejection sample accounting failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    if ($matrix.default_promotion_manifest.integration_sample_accounting_closure -ne $true -or $matrix.default_promotion_manifest.sample_accounting_closure_status -ne 'passed' -or [int]$matrix.default_promotion_manifest.sample_accounting_closure_failed_count -ne 0) {",
            "        throw \"Windows release matrix sample accounting closure failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    $residentResultContract = $matrix.default_promotion_manifest.resident_result_contract",
            "    if (-not $residentResultContract -or $matrix.default_promotion_manifest.resident_result_contract_ready -ne $true -or $matrix.default_promotion_manifest.resident_result_contract_status -ne 'passed' -or $matrix.default_promotion_manifest.resident_result_contract_top_level_check -ne $true -or $matrix.default_promotion_manifest.resident_result_contract_check_present -ne $true -or $matrix.default_promotion_manifest.resident_result_contract_check_passed -ne $true -or $matrix.default_promotion_manifest.resident_result_contract_phase2_check_passed -ne $true -or [int]$matrix.default_promotion_manifest.resident_result_contract_required_count -le 0 -or [int]$matrix.default_promotion_manifest.resident_result_contract_failed_count -ne 0 -or [int]$matrix.default_promotion_manifest.resident_result_contract_failed_check_count -ne 0) {",
            "        throw \"Windows release matrix resident result contract failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    if ($matrix.default_promotion_manifest.stack_engine_contract_present -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_ready -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_phase2_check_passed -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_status -ne 'passed' -or $matrix.default_promotion_manifest.stack_engine_contract_passed -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_scope -ne 'all' -or $matrix.default_promotion_manifest.stack_engine_contract_adoption_recommendation -ne 'stack_engine_default_ready' -or [int]$matrix.default_promotion_manifest.stack_engine_contract_default_gap_count -ne 0 -or [int]$matrix.default_promotion_manifest.stack_engine_contract_blocker_count -ne 0) {",
            "        throw \"Windows release matrix StackEngine default contract failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    $residentFastpathHandoff = $matrix.default_promotion_manifest.resident_registration_fastpath_release_handoff",
            "    if (-not $residentFastpathHandoff -or $residentFastpathHandoff.present -ne $true -or $residentFastpathHandoff.ready -ne $true -or $residentFastpathHandoff.raw_ready -ne $true -or $residentFastpathHandoff.phase2_ready -ne $true -or $residentFastpathHandoff.agreement -ne $true -or $residentFastpathHandoff.decision_check_passed -ne $true -or $residentFastpathHandoff.phase2_check_passed -ne $true -or $residentFastpathHandoff.raw_status -ne 'passed' -or $residentFastpathHandoff.phase2_status -ne 'passed' -or $residentFastpathHandoff.raw_required -ne $true -or $residentFastpathHandoff.phase2_required -ne $true -or [int]$residentFastpathHandoff.raw_passed_check_count -le 0 -or [int]$residentFastpathHandoff.phase2_passed_check_count -le 0 -or [int]$residentFastpathHandoff.raw_failed_check_count -ne 0 -or [int]$residentFastpathHandoff.phase2_failed_check_count -ne 0) {",
            "        throw \"Windows release matrix resident fastpath release handoff failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    $releaseGuard = $matrix.release_decision_direct_runtime_publication_guard",
            "    if (-not $releaseGuard -or $releaseGuard.present -ne $true -or $releaseGuard.ready -ne $true -or $releaseGuard.decision_check_passed -ne $true -or $releaseGuard.source_ready -ne $true -or $releaseGuard.count_ready -ne $true -or $releaseGuard.raw_leaf_checks_ready -ne $true -or $releaseGuard.phase2_leaf_checks_ready -ne $true -or $releaseGuard.raw_acceptance_source -ne 'explicit_resident_artifacts_json' -or $releaseGuard.raw_calibration_source -ne 'resident_artifacts_json_fallback' -or [int]$releaseGuard.raw_resident_lights -lt 200) {",
            "        throw \"Windows release matrix release-decision direct publication guard failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    $defaultPromotionReleaseGuard = $matrix.default_promotion_manifest.release_decision_direct_runtime_publication_guard",
            "    if (-not $defaultPromotionReleaseGuard -or $defaultPromotionReleaseGuard.present -ne $true -or $defaultPromotionReleaseGuard.ready -ne $true -or $defaultPromotionReleaseGuard.decision_check_passed -ne $true -or $defaultPromotionReleaseGuard.source_ready -ne $true -or $defaultPromotionReleaseGuard.count_ready -ne $true -or $defaultPromotionReleaseGuard.leaf_checks_ready -ne $true -or $defaultPromotionReleaseGuard.raw_matrix_acceptance_source -ne 'explicit_resident_artifacts_json' -or $defaultPromotionReleaseGuard.raw_matrix_pipeline_calibration_source -ne 'resident_artifacts_json_fallback' -or [int]$defaultPromotionReleaseGuard.raw_matrix_pipeline_resident_lights -lt 200) {",
            "        throw \"Windows release matrix default-promotion direct publication guard failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "}",
            "if ($Phase2StatusFile) {",
            "    if (-not (Test-Path -LiteralPath $Phase2StatusFile -PathType Leaf)) {",
            "        throw \"Missing Phase 2 status artifact: $Phase2StatusFile\"",
            "    }",
            "    $phase2Status = Get-Content -LiteralPath $Phase2StatusFile -Raw | ConvertFrom-Json",
            "    if ($phase2Status.artifact_type -ne 'glass_phase2_status' -or $phase2Status.status -ne 'green' -or $phase2Status.passed -ne $true) {",
            "        throw \"Phase 2 status check failed: $Phase2StatusFile\"",
            "    }",
            "    if (-not $phase2Status.pipeline_contract -or $phase2Status.pipeline_contract.integration_sample_accounting_closure -ne $true -or $phase2Status.pipeline_contract.sample_accounting_closure_status -ne 'passed' -or [int]$phase2Status.pipeline_contract.sample_accounting_closure_failed_count -ne 0) {",
            "        throw \"Phase 2 sample accounting closure failed: $Phase2StatusFile\"",
            "    }",
            "    $phase2StackCheck = $phase2Status.checks | Where-Object { $_.name -eq 'stack_engine_default_contract_ready' } | Select-Object -First 1",
            "    if (-not $phase2StackCheck -or $phase2StackCheck.passed -ne $true -or -not $phase2Status.stack_engine_contract -or $phase2Status.stack_engine_contract.audit_type -ne 'stack_engine_default_contract' -or $phase2Status.stack_engine_contract.status -ne 'passed' -or $phase2Status.stack_engine_contract.passed -ne $true -or $phase2Status.stack_engine_contract.default_promotion_ready -ne $true -or $phase2Status.stack_engine_contract.default_promotion_status -ne 'ready' -or $phase2Status.stack_engine_contract.adoption_recommendation -ne 'stack_engine_default_ready' -or $phase2Status.stack_engine_contract.default_promotion_recommendation -ne 'stack_engine_default_ready' -or [int]$phase2Status.stack_engine_contract.default_promotion_phase2_stack_engine_default_gap_count -ne 0 -or [int]$phase2Status.stack_engine_contract.default_promotion_blocker_count -ne 0) {",
            "        throw \"Phase 2 StackEngine default contract failed: $Phase2StatusFile\"",
            "    }",
            "}",
            "if ($Phase2StatusCompareFile) {",
            "    if (-not (Test-Path -LiteralPath $Phase2StatusCompareFile -PathType Leaf)) {",
            "        throw \"Missing Phase 2 status compare artifact: $Phase2StatusCompareFile\"",
            "    }",
            "    $phase2Compare = Get-Content -LiteralPath $Phase2StatusCompareFile -Raw | ConvertFrom-Json",
            "    if ($phase2Compare.artifact_type -ne 'glass_phase2_status_compare' -or $phase2Compare.status -ne 'passed' -or $phase2Compare.passed -ne $true) {",
            "        throw \"Phase 2 status compare check failed: $Phase2StatusCompareFile\"",
            "    }",
            "}",
            "",
            "$releaseArgs = @('release', 'create', $ExpectedTag)",
            "$releaseArgs += @($Assets | ForEach-Object { $_.Path })",
            "$releaseArgs += @('--title', $ReleaseTitle)",
            "if ($NotesFile) {",
            "    $releaseArgs += @('--notes-file', $NotesFile)",
            "}",
        ]
    )
    if release.get("draft") is True:
        lines.append("$releaseArgs += '--draft'")
    if release.get("prerelease") is True:
        lines.append("$releaseArgs += '--prerelease'")
    lines.extend(
        [
            "",
            "Write-Host 'GLASS release assets verified.'",
            "Write-Host 'Dry-run complete. Re-run this script with -Publish to create the GitHub release.'",
            "if (-not $Publish) {",
            "    exit 0",
            "}",
            "& $GhPath @releaseArgs",
            "if ($LASTEXITCODE -ne 0) {",
            "    throw \"GitHub release creation failed with exit code $LASTEXITCODE\"",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def build_windows_github_release_plan(
    *,
    manifest_artifact: str | Path,
    tag: str,
    title: str | None = None,
    notes_file: str | Path | None = None,
    draft: bool = True,
    prerelease: bool = False,
    require_same_source_stamp: bool = False,
    check_gh: bool = False,
    check_gh_auth: bool = False,
    gh_path: str | Path | None = None,
    phase2_status: str | Path | None = None,
    phase2_status_compare: str | Path | None = None,
    windows_release_matrix: str | Path | None = None,
    require_windows_release_matrix: bool = True,
) -> dict[str, Any]:
    manifest_path = Path(manifest_artifact)
    manifest = _read_json_object(manifest_path)
    assets = _asset_rows(manifest)
    phase2_status_summary = _phase2_artifact_summary(
        phase2_status,
        expected_artifact_type="glass_phase2_status",
    )
    phase2_compare_summary = _phase2_artifact_summary(
        phase2_status_compare,
        expected_artifact_type="glass_phase2_status_compare",
    )
    release_matrix_summary = _windows_release_matrix_summary(windows_release_matrix)
    source_stamps = sorted({str(row["source_stamp"]) for row in assets if row.get("source_stamp")})
    release_title = title or f"GLASS {tag} Windows packages"
    notes_path = str(Path(notes_file).resolve()) if notes_file is not None else None
    gh_exe = str(gh_path) if gh_path is not None else shutil.which("gh")
    if gh_exe is not None and not Path(gh_exe).exists() and Path(gh_exe).is_absolute():
        gh_exe = None
    gh_version = _run_gh([gh_exe, "--version"]) if check_gh and gh_exe else None
    gh_auth = _run_gh([gh_exe, "auth", "status"]) if check_gh_auth and gh_exe else None
    gh_auth_ok = gh_auth is not None and gh_auth.get("returncode") == 0

    checks: list[dict[str, Any]] = [
        _check(
            "manifest_passed",
            manifest.get("passed") is True,
            {"manifest_status": manifest.get("status"), "failed_checks": manifest.get("failed_checks")},
        ),
        _check("assets_present", bool(assets), {"asset_count": len(assets)}),
    ]
    for asset in assets:
        label = str(asset.get("label"))
        checks.extend(
            [
                _check(f"asset_exists:{label}", bool(asset.get("exists")), {"path": asset.get("zip_path")}),
                _check(
                    f"asset_has_sha256:{label}",
                    isinstance(asset.get("sha256"), str) and len(str(asset["sha256"])) == 64,
                    {"sha256": asset.get("sha256")},
                ),
                _check(
                    f"asset_nonempty:{label}",
                    isinstance(asset.get("size_bytes"), int) and int(asset["size_bytes"]) > 0,
                    {"size_bytes": asset.get("size_bytes")},
                ),
            ]
        )
    if require_same_source_stamp:
        checks.append(
            _check(
                "same_source_stamp",
                len(source_stamps) == 1,
                {"source_stamps": source_stamps},
            )
        )
    if phase2_status_summary is not None:
        checks.extend(
            [
                _check(
                    "phase2_status_present",
                    bool(phase2_status_summary.get("exists")),
                    {"path": phase2_status_summary.get("path")},
                ),
                _check(
                    "phase2_status_type",
                    phase2_status_summary.get("artifact_type") == "glass_phase2_status",
                    {
                        "artifact_type": phase2_status_summary.get("artifact_type"),
                        "required": "glass_phase2_status",
                    },
                ),
                _check(
                    "phase2_status_green",
                    phase2_status_summary.get("status") == "green"
                    and phase2_status_summary.get("passed") is True,
                    {
                        "status": phase2_status_summary.get("status"),
                        "passed": phase2_status_summary.get("passed"),
                        "latest_gate": phase2_status_summary.get("latest_gate"),
                    },
                ),
                _check(
                    "phase2_pipeline_rejection_sample_accounting_passed",
                    phase2_status_summary.get(
                        "pipeline_integration_rejection_sample_counts_match_maps"
                    )
                    is True
                    and phase2_status_summary.get("pipeline_rejection_sample_accounting_status")
                    == "passed"
                    and int(
                        phase2_status_summary.get(
                            "pipeline_rejection_sample_accounting_failed_count"
                        )
                        or 0
                    )
                    == 0,
                    {
                        "check": phase2_status_summary.get(
                            "pipeline_integration_rejection_sample_counts_match_maps"
                        ),
                        "status": phase2_status_summary.get(
                            "pipeline_rejection_sample_accounting_status"
                        ),
                        "failed_count": phase2_status_summary.get(
                            "pipeline_rejection_sample_accounting_failed_count"
                        ),
                    },
                ),
                _check(
                    "phase2_pipeline_sample_accounting_closure_passed",
                    phase2_status_summary.get("pipeline_integration_sample_accounting_closure")
                    is True
                    and phase2_status_summary.get("pipeline_sample_accounting_closure_status")
                    == "passed"
                    and int(
                        phase2_status_summary.get(
                            "pipeline_sample_accounting_closure_failed_count"
                        )
                        or 0
                    )
                    == 0,
                    {
                        "check": phase2_status_summary.get(
                            "pipeline_integration_sample_accounting_closure"
                        ),
                        "status": phase2_status_summary.get(
                            "pipeline_sample_accounting_closure_status"
                        ),
                        "present_count": phase2_status_summary.get(
                            "pipeline_sample_accounting_closure_present_count"
                        ),
                        "failed_count": phase2_status_summary.get(
                            "pipeline_sample_accounting_closure_failed_count"
                        ),
                        "failed_items": (
                            phase2_status_summary.get("pipeline_sample_accounting_closure")
                            or {}
                        ).get("failed_items"),
                    },
                ),
                _check(
                    "phase2_stack_engine_default_contract_ready",
                    _phase2_stack_engine_default_contract_ready(phase2_status_summary),
                    {
                        "present": phase2_status_summary.get(
                            "stack_engine_default_contract_present"
                        ),
                        "phase2_check_passed": phase2_status_summary.get(
                            "stack_engine_default_contract_phase2_check_passed"
                        ),
                        "audit_type": phase2_status_summary.get(
                            "stack_engine_default_contract_audit_type"
                        ),
                        "status": phase2_status_summary.get(
                            "stack_engine_default_contract_status"
                        ),
                        "passed": phase2_status_summary.get(
                            "stack_engine_default_contract_passed"
                        ),
                        "scope": phase2_status_summary.get(
                            "stack_engine_default_contract_scope"
                        ),
                        "default_promotion_ready": phase2_status_summary.get(
                            "stack_engine_default_contract_default_promotion_ready"
                        ),
                        "default_promotion_status": phase2_status_summary.get(
                            "stack_engine_default_contract_default_promotion_status"
                        ),
                        "adoption_recommendation": phase2_status_summary.get(
                            "stack_engine_default_contract_adoption_recommendation"
                        ),
                        "default_promotion_recommendation": phase2_status_summary.get(
                            "stack_engine_default_contract_default_promotion_recommendation"
                        ),
                        "default_gap_count": phase2_status_summary.get(
                            "stack_engine_default_contract_default_gap_count"
                        ),
                        "blocker_count": phase2_status_summary.get(
                            "stack_engine_default_contract_blocker_count"
                        ),
                        "blockers": phase2_status_summary.get(
                            "stack_engine_default_contract_blockers"
                        ),
                    },
                ),
            ]
        )
    if phase2_compare_summary is not None:
        checks.extend(
            [
                _check(
                    "phase2_status_compare_present",
                    bool(phase2_compare_summary.get("exists")),
                    {"path": phase2_compare_summary.get("path")},
                ),
                _check(
                    "phase2_status_compare_type",
                    phase2_compare_summary.get("artifact_type") == "glass_phase2_status_compare",
                    {
                        "artifact_type": phase2_compare_summary.get("artifact_type"),
                        "required": "glass_phase2_status_compare",
                    },
                ),
                _check(
                    "phase2_status_compare_passed",
                    phase2_compare_summary.get("status") == "passed"
                    and phase2_compare_summary.get("passed") is True,
                    {
                        "status": phase2_compare_summary.get("status"),
                        "passed": phase2_compare_summary.get("passed"),
                        "baseline_gate": phase2_compare_summary.get("baseline_gate"),
                        "candidate_gate": phase2_compare_summary.get("candidate_gate"),
                    },
                ),
            ]
        )
    release_matrix_for_checks = release_matrix_summary or {}
    if require_windows_release_matrix or release_matrix_summary is not None:
        asset_labels = {str(asset.get("label")) for asset in assets if asset.get("label")}
        matrix_labels = [
            str(label) for label in release_matrix_for_checks.get("package_labels") or []
        ]
        missing_matrix_assets = [label for label in matrix_labels if label not in asset_labels]
        checks.extend(
            [
                _check(
                    "windows_release_matrix_present",
                    bool(release_matrix_summary and release_matrix_summary.get("exists")),
                    {
                        "path": release_matrix_for_checks.get("path"),
                        "required": bool(require_windows_release_matrix),
                    },
                ),
                _check(
                    "windows_release_matrix_type",
                    release_matrix_for_checks.get("artifact_type") == "windows_release_matrix",
                    {
                        "artifact_type": release_matrix_for_checks.get("artifact_type"),
                        "required": "windows_release_matrix",
                    },
                ),
                _check(
                    "windows_release_matrix_ready",
                    release_matrix_for_checks.get("status") == "release_matrix_ready"
                    and release_matrix_for_checks.get("passed") is True,
                    {
                        "status": release_matrix_for_checks.get("status"),
                        "passed": release_matrix_for_checks.get("passed"),
                    },
                ),
                _check(
                    "windows_release_matrix_default_promotion_ready",
                    release_matrix_for_checks.get("default_promotion_status")
                    == "default_promotion_ready"
                    and release_matrix_for_checks.get("default_promotion_passed") is True
                    and release_matrix_for_checks.get("default_promotion_default_change_ready")
                    is True,
                    {
                        "status": release_matrix_for_checks.get("default_promotion_status"),
                        "passed": release_matrix_for_checks.get("default_promotion_passed"),
                        "default_change_ready": release_matrix_for_checks.get(
                            "default_promotion_default_change_ready"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_default_route_passed",
                    release_matrix_for_checks.get("default_route_passed") is True
                    and release_matrix_for_checks.get("default_route_route_contract_passed") is True
                    and int(release_matrix_for_checks.get("default_route_route_check_count") or 0)
                    >= 4,
                    {
                        "default_route_passed": release_matrix_for_checks.get(
                            "default_route_passed"
                        ),
                        "route_contract_passed": release_matrix_for_checks.get(
                            "default_route_route_contract_passed"
                        ),
                        "route_check_count": release_matrix_for_checks.get(
                            "default_route_route_check_count"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_rejection_sample_accounting_passed",
                    release_matrix_for_checks.get("integration_rejection_sample_counts_match_maps")
                    is True
                    and release_matrix_for_checks.get("rejection_sample_accounting_status")
                    == "passed"
                    and int(
                        release_matrix_for_checks.get("rejection_sample_accounting_failed_count")
                        or 0
                    )
                    == 0,
                    {
                        "check": release_matrix_for_checks.get(
                            "integration_rejection_sample_counts_match_maps"
                        ),
                        "status": release_matrix_for_checks.get(
                            "rejection_sample_accounting_status"
                        ),
                        "failed_count": release_matrix_for_checks.get(
                            "rejection_sample_accounting_failed_count"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_sample_accounting_closure_passed",
                    release_matrix_for_checks.get("integration_sample_accounting_closure")
                    is True
                    and release_matrix_for_checks.get("sample_accounting_closure_status")
                    == "passed"
                    and int(
                        release_matrix_for_checks.get("sample_accounting_closure_failed_count")
                        or 0
                    )
                    == 0,
                    {
                        "check": release_matrix_for_checks.get(
                            "integration_sample_accounting_closure"
                        ),
                        "status": release_matrix_for_checks.get(
                            "sample_accounting_closure_status"
                        ),
                        "present_count": release_matrix_for_checks.get(
                            "sample_accounting_closure_present_count"
                        ),
                        "failed_count": release_matrix_for_checks.get(
                            "sample_accounting_closure_failed_count"
                        ),
                        "failed_items": (
                            release_matrix_for_checks.get("sample_accounting_closure") or {}
                        ).get("failed_items"),
                    },
                ),
                _check(
                    "windows_release_matrix_resident_result_contract_handoff_passed",
                    _resident_result_contract_ready(release_matrix_for_checks),
                    _resident_result_contract_evidence(release_matrix_for_checks),
                ),
                _check(
                    "windows_release_matrix_stack_engine_contract_ready",
                    _windows_release_matrix_stack_engine_contract_ready(
                        release_matrix_for_checks
                    ),
                    {
                        "present": release_matrix_for_checks.get(
                            "stack_engine_contract_present"
                        ),
                        "ready": release_matrix_for_checks.get("stack_engine_contract_ready"),
                        "phase2_check_passed": release_matrix_for_checks.get(
                            "stack_engine_contract_phase2_check_passed"
                        ),
                        "status": release_matrix_for_checks.get(
                            "stack_engine_contract_status"
                        ),
                        "passed": release_matrix_for_checks.get(
                            "stack_engine_contract_passed"
                        ),
                        "scope": release_matrix_for_checks.get("stack_engine_contract_scope"),
                        "adoption_recommendation": release_matrix_for_checks.get(
                            "stack_engine_contract_adoption_recommendation"
                        ),
                        "default_gap_count": release_matrix_for_checks.get(
                            "stack_engine_contract_default_gap_count"
                        ),
                        "blocker_count": release_matrix_for_checks.get(
                            "stack_engine_contract_blocker_count"
                        ),
                        "blockers": release_matrix_for_checks.get(
                            "stack_engine_contract_blockers"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_resident_fastpath_release_handoff_ready",
                    _resident_fastpath_release_handoff_ready(
                        release_matrix_for_checks,
                        prefix="resident_registration_fastpath_release_handoff",
                    ),
                    _resident_fastpath_release_handoff_evidence(
                        release_matrix_for_checks,
                        prefix="resident_registration_fastpath_release_handoff",
                    ),
                ),
                _check(
                    "windows_release_matrix_release_decision_direct_runtime_publication_guard_passed",
                    _release_direct_publication_guard_ready(
                        release_matrix_for_checks,
                        prefix="release_decision_direct_runtime_publication_guard",
                    ),
                    _release_direct_publication_guard_evidence(
                        release_matrix_for_checks,
                        prefix="release_decision_direct_runtime_publication_guard",
                    ),
                ),
                _check(
                    "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed",
                    _release_direct_publication_guard_ready(
                        release_matrix_for_checks,
                        prefix=(
                            "default_promotion_release_decision_direct_runtime_publication_guard"
                        ),
                    ),
                    _release_direct_publication_guard_evidence(
                        release_matrix_for_checks,
                        prefix=(
                            "default_promotion_release_decision_direct_runtime_publication_guard"
                        ),
                    ),
                ),
                _check(
                    "windows_release_matrix_assets_present",
                    bool(matrix_labels) and not missing_matrix_assets,
                    {
                        "matrix_labels": matrix_labels,
                        "asset_labels": sorted(asset_labels),
                        "missing": missing_matrix_assets,
                    },
                ),
                _check(
                    "windows_release_matrix_try_order_has_cpu_fallback",
                    "cpu" in (release_matrix_for_checks.get("ordered_try_list") or []),
                    {"ordered_try_list": release_matrix_for_checks.get("ordered_try_list")},
                ),
            ]
        )
    if phase2_status_summary is not None and release_matrix_summary is not None:
        checks.append(
            _check(
                "phase2_release_matrix_stack_engine_contract_agree",
                _phase2_stack_engine_default_contract_ready(phase2_status_summary)
                and _windows_release_matrix_stack_engine_contract_ready(
                    release_matrix_for_checks
                )
                and _int_or_zero(
                    phase2_status_summary.get(
                        "stack_engine_default_contract_default_gap_count"
                    )
                )
                == _int_or_zero(
                    release_matrix_for_checks.get(
                        "stack_engine_contract_default_gap_count"
                    )
                )
                and _int_or_zero(
                    phase2_status_summary.get(
                        "stack_engine_default_contract_blocker_count"
                    )
                )
                == _int_or_zero(
                    release_matrix_for_checks.get("stack_engine_contract_blocker_count")
                ),
                {
                    "phase2_ready": _phase2_stack_engine_default_contract_ready(
                        phase2_status_summary
                    ),
                    "matrix_ready": _windows_release_matrix_stack_engine_contract_ready(
                        release_matrix_for_checks
                    ),
                    "phase2_gap_count": phase2_status_summary.get(
                        "stack_engine_default_contract_default_gap_count"
                    ),
                    "matrix_gap_count": release_matrix_for_checks.get(
                        "stack_engine_contract_default_gap_count"
                    ),
                    "phase2_blocker_count": phase2_status_summary.get(
                        "stack_engine_default_contract_blocker_count"
                    ),
                    "matrix_blocker_count": release_matrix_for_checks.get(
                        "stack_engine_contract_blocker_count"
                    ),
                },
            )
        )

    failed = [item for item in checks if not item.get("passed")]
    command_parts = [
        "gh",
        "release",
        "create",
        _quote(tag),
    ]
    command_parts.extend(_quote(str(asset["zip_path"])) for asset in assets if asset.get("zip_path"))
    command_parts.extend(
        [
            "--title",
            _quote(release_title),
        ]
    )
    if notes_path is not None:
        command_parts.extend(["--notes-file", _quote(notes_path)])
    if draft:
        command_parts.append("--draft")
    if prerelease:
        command_parts.append("--prerelease")
    release_command = " ".join(str(part) for part in command_parts if str(part).strip())
    gh_cli_ready = not check_gh or gh_exe is not None
    gh_auth_ready = not check_gh_auth or gh_auth_ok
    publication_ready = not failed and gh_cli_ready and gh_auth_ready
    recommendation = "run_release_command"
    if failed:
        recommendation = "fix_release_plan_blockers"
    elif check_gh and gh_exe is None:
        recommendation = "install_github_cli_then_run_release_command"
    elif check_gh_auth and not gh_auth_ok:
        recommendation = "authenticate_github_cli_then_run_release_command"

    return {
        "schema_version": 1,
        "artifact_type": "windows_github_release_plan",
        "created_at": now_iso(),
        "status": "release_plan_ready" if not failed else "blocked",
        "passed": not failed,
        "publication_ready": publication_ready,
        "recommendation": recommendation,
        "manifest_artifact": str(manifest_path),
        "release": {
            "tag": tag,
            "title": release_title,
            "draft": bool(draft),
            "prerelease": bool(prerelease),
            "notes_file": notes_path,
            "command": release_command,
        },
        "gh": {
            "checked": bool(check_gh),
            "auth_checked": bool(check_gh_auth),
            "available": gh_exe is not None,
            "path": gh_exe,
            "version": gh_version,
            "auth_status": gh_auth,
            "auth_ok": gh_auth_ok,
        },
        "phase2": {
            "status": phase2_status_summary,
            "status_compare": phase2_compare_summary,
        },
        "release_matrix": release_matrix_summary,
        "requirements": {
            "require_windows_release_matrix": bool(require_windows_release_matrix),
        },
        "source_stamps": source_stamps,
        "assets": assets,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This is a release handoff plan; it does not create a GitHub release or upload assets.",
            "Install and authenticate GitHub CLI before running the generated command.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    release = payload.get("release") if isinstance(payload.get("release"), dict) else {}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    phase2_compare = phase2.get("status_compare") if isinstance(phase2.get("status_compare"), dict) else {}
    release_matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    lines = [
        "# GLASS Windows GitHub Release Plan",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Publication ready: `{payload.get('publication_ready')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Tag: `{release.get('tag')}`",
        f"- Title: `{release.get('title')}`",
        f"- Source stamps: `{', '.join(payload.get('source_stamps') or [])}`",
        f"- GitHub CLI available: `{gh.get('available')}`",
        f"- GitHub CLI auth OK: `{gh.get('auth_ok')}`",
            f"- Publish script: `{release.get('script_file')}`",
            f"- Publish script mode: `{release.get('script_default_mode')}`",
            f"- Windows release matrix: `{release_matrix.get('status')}`",
            "",
        "## Assets",
        "",
        "| Label | Size bytes | SHA256 | Path |",
        "| --- | ---: | --- | --- |",
    ]
    for asset in payload.get("assets") or []:
        lines.append(
            "| "
            f"{asset.get('label')} | {asset.get('size_bytes')} | `{asset.get('sha256')}` | "
            f"`{asset.get('zip_path')}` |"
        )
    if release_matrix:
        lines.extend(
            [
                "",
                "## Windows Release Matrix Handoff",
                "",
                f"- Matrix path: `{release_matrix.get('path')}`",
                f"- Matrix status: `{release_matrix.get('status')}`",
                f"- Matrix passed: `{release_matrix.get('passed')}`",
                f"- Primary package: `{release_matrix.get('primary_package')}`",
                f"- Try order: `{', '.join(release_matrix.get('ordered_try_list') or [])}`",
                (
                    "- Default promotion: "
                    f"`{release_matrix.get('default_promotion_status')}` "
                    f"passed `{release_matrix.get('default_promotion_passed')}`"
                ),
                (
                    "- Default route contract/checks: "
                    f"`{release_matrix.get('default_route_route_contract_passed')}`/"
                    f"`{release_matrix.get('default_route_route_check_count')}`"
                ),
                (
                    "- Release direct publication guard: "
                    f"ready=`{release_matrix.get('release_decision_direct_runtime_publication_guard_ready')}` "
                    "check="
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_check_passed')}` "
                    "source="
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_raw_acceptance_source')}`/"
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_raw_calibration_source')}` "
                    "lights="
                    f"`{release_matrix.get('release_decision_direct_runtime_publication_guard_raw_resident_lights')}`"
                ),
                (
                    "- Default-promotion release direct guard: "
                    f"ready=`{release_matrix.get('default_promotion_release_decision_direct_runtime_publication_guard_ready')}` "
                    "check="
                    f"`{release_matrix.get('default_promotion_release_decision_direct_runtime_publication_guard_check_passed')}` "
                    "lights="
                    f"`{release_matrix.get('default_promotion_release_decision_direct_runtime_publication_guard_raw_resident_lights')}`"
                ),
                (
                    "- StackEngine default contract: "
                    f"ready=`{release_matrix.get('stack_engine_contract_ready')}` "
                    "phase2-check="
                    f"`{release_matrix.get('stack_engine_contract_phase2_check_passed')}` "
                    f"gaps=`{release_matrix.get('stack_engine_contract_default_gap_count')}` "
                    f"blockers=`{release_matrix.get('stack_engine_contract_blocker_count')}`"
                ),
                (
                    "- Resident fastpath release handoff: "
                    f"ready=`{release_matrix.get('resident_registration_fastpath_release_handoff_ready')}` "
                    f"raw=`{release_matrix.get('resident_registration_fastpath_release_handoff_raw_status')}` "
                    f"phase2=`{release_matrix.get('resident_registration_fastpath_release_handoff_phase2_status')}` "
                    f"agreement=`{release_matrix.get('resident_registration_fastpath_release_handoff_agreement')}` "
                    f"checks=`{release_matrix.get('resident_registration_fastpath_release_handoff_raw_passed_check_count')}`"
                ),
                (
                    "- Resident result contract: "
                    f"ready=`{release_matrix.get('resident_result_contract_ready')}` "
                    f"status=`{release_matrix.get('resident_result_contract_status')}` "
                    f"phase2=`{release_matrix.get('resident_result_contract_phase2_check_passed')}` "
                    f"required=`{release_matrix.get('resident_result_contract_required_count')}` "
                    f"failed=`{release_matrix.get('resident_result_contract_failed_count')}`"
                ),
                (
                    "- Rejection sample accounting: "
                    f"`{release_matrix.get('rejection_sample_accounting_status')}` "
                    f"failed `{release_matrix.get('rejection_sample_accounting_failed_count')}`"
                ),
                (
                    "- Sample accounting closure: "
                    f"`{release_matrix.get('sample_accounting_closure_status')}` "
                    f"present=`{release_matrix.get('sample_accounting_closure_present_count')}` "
                    f"failed=`{release_matrix.get('sample_accounting_closure_failed_count')}`"
                ),
            ]
        )
    if phase2_status or phase2_compare:
        lines.extend(
            [
                "",
                "## Phase 2 Handoff Preflight",
                "",
                f"- Phase 2 status path: `{phase2_status.get('path')}`",
                f"- Phase 2 status: `{phase2_status.get('status')}`",
                f"- Phase 2 latest gate: `{phase2_status.get('latest_gate')}`",
            ]
        )
        if _has_native_phase2_provenance(phase2_status):
            lines.extend(
                [
                    f"- Native guardrails bundle: `{phase2_status.get('native_guardrails_bundle_status')}`",
                    f"- Native resident contract source: `{phase2_status.get('resident_result_contract_source')}`",
                    (
                        "- Native resident result run default: "
                        f"`{phase2_status.get('resident_result_contract_run_default')}`"
                    ),
                    f"- Native resident result contract: `{phase2_status.get('resident_result_contract_json')}`",
                    (
                        "- Native calibration artifact: "
                        f"`{phase2_status.get('resident_native_calibration_artifact')}`"
                    ),
                    f"- Native calibration masters: `{phase2_status.get('resident_calibration_master_count')}`",
                    f"- Native calibrated lights: `{phase2_status.get('resident_calibrated_light_count')}`",
                ]
            )
        if _has_registration_fastpath_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Resident registration fast path: "
                        f"`{phase2_status.get('resident_registration_fastpath_status')}`"
                    ),
                    (
                        "- Resident registration fast path contract: "
                        f"`{phase2_status.get('resident_registration_fastpath_contract_status')}` "
                        f"checks `{phase2_status.get('resident_registration_fastpath_contract_check_count')}` "
                        "failed "
                        f"`{phase2_status.get('resident_registration_fastpath_contract_failed_check_count')}`"
                    ),
                    (
                        "- Resident registration fast path mode: "
                        f"`{phase2_status.get('resident_registration_fastpath_mode')}`"
                    ),
                    (
                        "- Descriptor fit batch: "
                        f"`{phase2_status.get('triangle_descriptor_fit_batch')}` "
                        f"mode `{phase2_status.get('triangle_descriptor_fit_batch_mode')}`"
                    ),
                    (
                        "- Descriptor device reuse: "
                        f"`{phase2_status.get('triangle_descriptor_fit_device_reuse')}`"
                    ),
                    (
                        "- Pixel refine batch: "
                        f"`{phase2_status.get('triangle_pixel_refine_batch')}` "
                        f"metric `{phase2_status.get('triangle_pixel_refine_batch_metric_mode')}`"
                    ),
                    (
                        "- Triangle warp batch: "
                        f"`{phase2_status.get('triangle_warp_batch')}` "
                        f"mode `{phase2_status.get('triangle_warp_batch_mode')}` "
                        f"frames `{phase2_status.get('triangle_warp_batch_frame_count')}`"
                    ),
                    f"- Resident warp copy mode: `{phase2_status.get('resident_warp_copy_mode')}`",
                    f"- Resident warp scratch bytes: `{phase2_status.get('resident_warp_scratch_bytes')}`",
                ]
            )
        if _has_pipeline_contract_phase2_provenance(phase2_status):
            lines.extend(
                [
                    f"- Pipeline contract: `{phase2_status.get('pipeline_contract_status')}`",
                    f"- Pipeline contract passed: `{phase2_status.get('pipeline_contract_passed')}`",
                    (
                        "- Pipeline contract failed checks: "
                        f"`{phase2_status.get('pipeline_contract_failed_check_count')}`"
                    ),
                    (
                        "- Pipeline integration outputs/maps: "
                        f"`{phase2_status.get('pipeline_integration_output_count')}`/"
                        f"`{phase2_status.get('pipeline_integration_map_count')}`"
                    ),
                    (
                        "- Pipeline integration DQ contract: "
                        f"`{phase2_status.get('pipeline_integration_dq_contract')}`"
                    ),
                    (
                        "- Pipeline StackEngine result contract: "
                        f"`{phase2_status.get('pipeline_integration_stack_result_contract')}`"
                    ),
                    (
                        "- Pipeline resident result contract: "
                        f"`{phase2_status.get('pipeline_integration_resident_result_contract')}`"
                    ),
                    (
                        "- Pipeline pixel verification: "
                        f"`{phase2_status.get('pipeline_pixel_verification_enabled')}`"
                    ),
                    (
                        "- Pipeline DQ pixels match summary: "
                        f"`{phase2_status.get('pipeline_integration_dq_map_pixels_match_summary')}`"
                    ),
                    (
                        "- Pipeline coverage pixels match DQ: "
                        f"`{phase2_status.get('pipeline_integration_coverage_map_pixels_match_dq')}`"
                    ),
                    (
                        "- Pipeline rejection pixels match DQ: "
                        f"`{phase2_status.get('pipeline_integration_rejection_map_pixels_match_dq')}`"
                    ),
                    (
                        "- Pipeline rejection sample accounting: "
                        f"`{phase2_status.get('pipeline_rejection_sample_accounting_status')}` "
                        "check "
                        f"`{phase2_status.get('pipeline_integration_rejection_sample_counts_match_maps')}` "
                        f"failed `{phase2_status.get('pipeline_rejection_sample_accounting_failed_count')}`"
                    ),
                    (
                        "- Pipeline sample accounting closure: "
                        f"`{phase2_status.get('pipeline_sample_accounting_closure_status')}` "
                        "check "
                        f"`{phase2_status.get('pipeline_integration_sample_accounting_closure')}` "
                        f"failed `{phase2_status.get('pipeline_sample_accounting_closure_failed_count')}`"
                    ),
                ]
            )
        if _has_stack_engine_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- StackEngine default contract: "
                        f"`{phase2_status.get('stack_engine_default_contract_status')}` "
                        "check "
                        f"`{phase2_status.get('stack_engine_default_contract_phase2_check_passed')}` "
                        f"gaps `{phase2_status.get('stack_engine_default_contract_default_gap_count')}` "
                        "blockers "
                        f"`{phase2_status.get('stack_engine_default_contract_blocker_count')}`"
                    ),
                    (
                        "- StackEngine default recommendations: "
                        f"`{phase2_status.get('stack_engine_default_contract_adoption_recommendation')}`/"
                        f"`{phase2_status.get('stack_engine_default_contract_default_promotion_recommendation')}`"
                    ),
                ]
            )
        if _has_release_decision_phase2_provenance(phase2_status):
            lines.extend(
                [
                    f"- Release decision: `{phase2_status.get('release_decision_status')}`",
                    (
                        "- Release recommendation: "
                        f"`{phase2_status.get('release_decision_recommendation')}`"
                    ),
                    (
                        "- Default change ready: "
                        f"`{phase2_status.get('release_decision_default_change_ready')}`"
                    ),
                    (
                        "- Runtime repeat runs: "
                        f"`{phase2_status.get('release_runtime_repeat_run_count')}`"
                    ),
                    (
                        "- Runtime repeat best: "
                        f"`{phase2_status.get('release_runtime_repeat_best_label')}` "
                        f"`{phase2_status.get('release_runtime_repeat_best_elapsed_s')}` s"
                    ),
                    (
                        "- Runtime repeat ratio vs best: "
                        f"`{phase2_status.get('release_runtime_repeat_elapsed_ratio_vs_best')}`"
                    ),
                ]
            )
        lines.extend(
            [
                f"- Phase 2 status compare path: `{phase2_compare.get('path')}`",
                f"- Phase 2 status compare: `{phase2_compare.get('status')}`",
                f"- Phase 2 compare baseline gate: `{phase2_compare.get('baseline_gate')}`",
                f"- Phase 2 compare candidate gate: `{phase2_compare.get('candidate_gate')}`",
            ]
        )
    lines.extend(["", "## Command", "", "```powershell", str(release.get("command") or ""), "```", ""])
    lines.extend(["## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_github_release_plan(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
    notes: str | Path | None = None,
    script: str | Path | None = None,
) -> None:
    if script is not None:
        release = payload.get("release")
        if isinstance(release, dict):
            release["script_file"] = str(Path(script).resolve())
            release["script_default_mode"] = "dry_run_requires_publish_switch"
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
    if notes is not None:
        Path(notes).parent.mkdir(parents=True, exist_ok=True)
        Path(notes).write_text(_release_notes(payload), encoding="utf-8")
    if script is not None:
        Path(script).parent.mkdir(parents=True, exist_ok=True)
        Path(script).write_text(_powershell_release_script(payload), encoding="utf-8")
