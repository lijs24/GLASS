from __future__ import annotations

from pathlib import Path
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


def _norm_path(value: str | Path | None) -> str | None:
    if value is None:
        return None
    return str(Path(str(value)).resolve(strict=False)).lower()


def _same_path(left: str | Path | None, right: str | Path | None) -> bool:
    left_norm = _norm_path(left)
    right_norm = _norm_path(right)
    return left_norm is not None and right_norm is not None and left_norm == right_norm


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _rows_by_label(rows: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = row.get("label")
        if label:
            result[str(label)] = row
    return result


def _checks_by_name(rows: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if name:
            result[str(name)] = row
    return result


def _resident_winsorized_sweep_summary(source: dict[str, Any]) -> dict[str, Any]:
    audit = (
        source.get("resident_winsorized_sweep_audit")
        if isinstance(source.get("resident_winsorized_sweep_audit"), dict)
        else {}
    )

    def field(name: str) -> Any:
        flattened = source.get(f"resident_winsorized_sweep_{name}")
        return flattened if flattened is not None else audit.get(name)

    return {
        "resident_winsorized_sweep_audit": audit,
        "resident_winsorized_sweep_present": field("present"),
        "resident_winsorized_sweep_status": field("status"),
        "resident_winsorized_sweep_passed": field("passed"),
        "resident_winsorized_sweep_phase2_check_passed": field(
            "phase2_check_passed"
        ),
        "resident_winsorized_sweep_check_count": field("check_count"),
        "resident_winsorized_sweep_failed_check_count": field("failed_check_count"),
        "resident_winsorized_sweep_failed_checks": field("failed_checks") or [],
        "resident_winsorized_sweep_required_frame_count": field(
            "required_frame_count"
        ),
        "resident_winsorized_sweep_required_frame_count_passed": field(
            "required_frame_count_passed"
        ),
        "resident_winsorized_sweep_required_frame_master_rms": field(
            "required_frame_master_rms"
        ),
        "resident_winsorized_sweep_required_frame_master_max_abs": field(
            "required_frame_master_max_abs"
        ),
        "resident_winsorized_sweep_required_frame_cuda_hardened_s": field(
            "required_frame_cuda_hardened_s"
        ),
        "resident_winsorized_sweep_path": audit.get("path"),
        "resident_winsorized_sweep_sweep_path": audit.get("sweep_path"),
    }


def _stack_engine_publication_audit_summary(source: dict[str, Any]) -> dict[str, Any]:
    audit = (
        source.get("stack_engine_publication_audit")
        if isinstance(source.get("stack_engine_publication_audit"), dict)
        else {}
    )

    def field(flattened_name: str, audit_name: str | None = None) -> Any:
        flattened = source.get(flattened_name)
        if flattened is not None:
            return flattened
        return audit.get(audit_name or flattened_name)

    return {
        "stack_engine_publication_audit": audit,
        "stack_engine_publication_audit_present": field(
            "stack_engine_publication_audit_present",
            "present",
        ),
        "stack_engine_publication_audit_ready": field(
            "stack_engine_publication_audit_ready",
            "ready",
        ),
        "stack_engine_publication_audit_status": field(
            "stack_engine_publication_audit_status",
            "status",
        ),
        "stack_engine_publication_audit_passed": field(
            "stack_engine_publication_audit_passed",
            "passed",
        ),
        "stack_engine_publication_audit_phase2_check_passed": field(
            "stack_engine_publication_audit_phase2_check_passed",
            "phase2_audit_check_passed",
        ),
        "stack_engine_publication_audit_recommendation": field(
            "stack_engine_publication_audit_recommendation",
            "recommendation",
        ),
        "stack_engine_publication_audit_check_count": field(
            "stack_engine_publication_audit_check_count",
            "check_count",
        ),
        "stack_engine_publication_audit_failed_check_count": field(
            "stack_engine_publication_audit_failed_check_count",
            "failed_check_count",
        ),
        "stack_engine_publication_audit_failed_checks": field(
            "stack_engine_publication_audit_failed_checks",
            "failed_checks",
        )
        or [],
        "stack_engine_publication_policy_chain_phase2_check_passed": field(
            "stack_engine_publication_policy_chain_phase2_check_passed",
            "policy_chain_phase2_check_passed",
        ),
        "stack_engine_publication_publish_preflight_policy_ready": field(
            "stack_engine_publication_publish_preflight_policy_ready",
            "publish_preflight_policy_ready",
        ),
        "stack_engine_publication_phase2_policy_ready": field(
            "stack_engine_publication_phase2_policy_ready",
            "phase2_policy_ready",
        ),
        "stack_engine_publication_policy_agreement": field(
            "stack_engine_publication_policy_agreement",
            "policy_agreement",
        ),
        "stack_engine_publication_resident_winsorized_chain_phase2_check_passed": field(
            "stack_engine_publication_resident_winsorized_chain_phase2_check_passed",
            "resident_winsorized_chain_phase2_check_passed",
        ),
        "stack_engine_publication_publish_preflight_resident_winsorized_ready": field(
            "stack_engine_publication_publish_preflight_resident_winsorized_ready",
            "publish_preflight_resident_winsorized_ready",
        ),
        "stack_engine_publication_phase2_resident_winsorized_ready": field(
            "stack_engine_publication_phase2_resident_winsorized_ready",
            "phase2_resident_winsorized_ready",
        ),
        "stack_engine_publication_resident_winsorized_agreement": field(
            "stack_engine_publication_resident_winsorized_agreement",
            "resident_winsorized_agreement",
        ),
    }


def _runtime_default_direct_evidence_summary(source: dict[str, Any]) -> dict[str, Any]:
    direct = (
        source.get("runtime_default_direct_evidence")
        if isinstance(source.get("runtime_default_direct_evidence"), dict)
        else {}
    )

    def field(flattened_name: str, direct_name: str | None = None) -> Any:
        flattened = source.get(flattened_name)
        if flattened is not None:
            return flattened
        return direct.get(direct_name or flattened_name)

    return {
        "runtime_default_direct_evidence": direct,
        "runtime_default_direct_evidence_present": field(
            "runtime_default_direct_evidence_present",
            "present",
        ),
        "runtime_default_direct_evidence_ready": field(
            "runtime_default_direct_evidence_ready",
            "ready",
        ),
        "runtime_default_direct_acceptance_fastpath": field(
            "runtime_default_direct_acceptance_fastpath",
            "acceptance_direct_fastpath",
        ),
        "runtime_default_direct_acceptance_fastpath_source": field(
            "runtime_default_direct_acceptance_fastpath_source",
            "acceptance_fastpath_source",
        ),
        "runtime_default_direct_acceptance_fastpath_check_count": field(
            "runtime_default_direct_acceptance_fastpath_check_count",
            "acceptance_fastpath_check_count",
        ),
        "runtime_default_direct_acceptance_fastpath_failed_check_count": field(
            "runtime_default_direct_acceptance_fastpath_failed_check_count",
            "acceptance_fastpath_failed_check_count",
        ),
        "runtime_default_direct_acceptance_fastpath_failed_checks": field(
            "runtime_default_direct_acceptance_fastpath_failed_checks",
            "acceptance_fastpath_failed_checks",
        )
        or [],
        "runtime_default_direct_pipeline_calibration": field(
            "runtime_default_direct_pipeline_calibration",
            "pipeline_direct_resident_calibration",
        ),
        "runtime_default_direct_pipeline_calibration_source": field(
            "runtime_default_direct_pipeline_calibration_source",
            "pipeline_calibration_artifact_source",
        ),
        "runtime_default_direct_pipeline_calibration_generated_for_contract": field(
            "runtime_default_direct_pipeline_calibration_generated_for_contract",
            "pipeline_calibration_artifact_generated_for_contract",
        ),
        "runtime_default_direct_pipeline_calibration_path_exists": field(
            "runtime_default_direct_pipeline_calibration_path_exists",
            "pipeline_calibration_artifact_path_exists",
        ),
        "runtime_default_direct_pipeline_resident_native_calibration_artifact": field(
            "runtime_default_direct_pipeline_resident_native_calibration_artifact",
            "pipeline_resident_native_calibration_artifact",
        ),
        "runtime_default_direct_pipeline_resident_calibrated_light_count": field(
            "runtime_default_direct_pipeline_resident_calibrated_light_count",
            "pipeline_resident_calibrated_light_count",
        ),
    }


_INTEGRATION_ENGINE_POLICY_FIELDS = (
    "integration_engine_policy_ready",
    "acceptance_integration_engine_policy_status",
    "acceptance_integration_engine_policy_check_present",
    "acceptance_integration_engine_policy_check_passed",
    "acceptance_integration_engine_policy_phase2_check_passed",
    "acceptance_integration_engine_policy_non_resident_count",
    "acceptance_integration_engine_policy_failed_count",
    "acceptance_integration_engine_policy_failed_items",
    "pipeline_integration_engine_policy_status",
    "pipeline_integration_engine_policy_check_present",
    "pipeline_integration_engine_policy_check_passed",
    "pipeline_integration_engine_policy_phase2_check_passed",
    "pipeline_integration_engine_policy_default_engine_policy",
    "pipeline_integration_engine_policy_non_resident_count",
    "pipeline_integration_engine_policy_failed_count",
    "pipeline_integration_engine_policy_failed_items",
)


def _integration_engine_policy_evidence(
    summary: dict[str, Any],
    prefix: str,
) -> dict[str, Any]:
    evidence = {
        "status": summary.get(f"{prefix}_integration_engine_policy_status"),
        "check_present": summary.get(
            f"{prefix}_integration_engine_policy_check_present"
        ),
        "check_passed": summary.get(
            f"{prefix}_integration_engine_policy_check_passed"
        ),
        "phase2_check_passed": summary.get(
            f"{prefix}_integration_engine_policy_phase2_check_passed"
        ),
        "non_resident_count": summary.get(
            f"{prefix}_integration_engine_policy_non_resident_count"
        ),
        "failed_count": summary.get(
            f"{prefix}_integration_engine_policy_failed_count"
        ),
        "failed_items": summary.get(
            f"{prefix}_integration_engine_policy_failed_items"
        )
        or [],
    }
    if prefix == "pipeline":
        evidence["default_engine_policy"] = summary.get(
            "pipeline_integration_engine_policy_default_engine_policy"
        )
    return evidence


def _integration_engine_policy_side_passed(
    summary: dict[str, Any],
    prefix: str,
) -> bool:
    evidence = _integration_engine_policy_evidence(summary, prefix)
    passed = (
        evidence.get("status") == "passed"
        and evidence.get("check_present") is True
        and evidence.get("check_passed") is True
        and evidence.get("phase2_check_passed") is True
        and _int_or_zero(evidence.get("non_resident_count")) == 0
        and _int_or_zero(evidence.get("failed_count")) == 0
        and not evidence.get("failed_items")
    )
    if prefix == "pipeline":
        passed = passed and evidence.get("default_engine_policy") is True
    return passed


def _integration_engine_policy_matches(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    return all(
        left.get(field) == right.get(field)
        for field in _INTEGRATION_ENGINE_POLICY_FIELDS
    )


_STACK_ENGINE_RUNTIME_DEFAULT_FIELDS = (
    "stack_engine_runtime_default_ready",
    "acceptance_stack_engine_runtime_default_status",
    "acceptance_stack_engine_runtime_default_check_present",
    "acceptance_stack_engine_runtime_default_check_passed",
    "acceptance_stack_engine_runtime_default_phase2_check_passed",
    "acceptance_stack_engine_runtime_default_master_count",
    "acceptance_stack_engine_runtime_default_legacy_master_count",
    "acceptance_stack_engine_runtime_default_failed_master_count",
    "acceptance_stack_engine_runtime_default_failed_output_count",
    "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count",
    "acceptance_stack_engine_runtime_default_failed_masters",
    "acceptance_stack_engine_runtime_default_failed_outputs",
    "pipeline_stack_engine_runtime_default_status",
    "pipeline_stack_engine_runtime_default_check_present",
    "pipeline_stack_engine_runtime_default_check_passed",
    "pipeline_stack_engine_runtime_default_phase2_check_passed",
    "pipeline_stack_engine_runtime_default_master_count",
    "pipeline_stack_engine_runtime_default_legacy_master_count",
    "pipeline_stack_engine_runtime_default_failed_master_count",
    "pipeline_stack_engine_runtime_default_failed_output_count",
    "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count",
    "pipeline_stack_engine_runtime_default_failed_masters",
    "pipeline_stack_engine_runtime_default_failed_outputs",
)


_RUNTIME_DEFAULT_DIRECT_EVIDENCE_FIELDS = (
    "runtime_default_direct_evidence_present",
    "runtime_default_direct_evidence_ready",
    "runtime_default_direct_acceptance_fastpath",
    "runtime_default_direct_acceptance_fastpath_source",
    "runtime_default_direct_acceptance_fastpath_check_count",
    "runtime_default_direct_acceptance_fastpath_failed_check_count",
    "runtime_default_direct_acceptance_fastpath_failed_checks",
    "runtime_default_direct_pipeline_calibration",
    "runtime_default_direct_pipeline_calibration_source",
    "runtime_default_direct_pipeline_calibration_generated_for_contract",
    "runtime_default_direct_pipeline_calibration_path_exists",
    "runtime_default_direct_pipeline_resident_native_calibration_artifact",
    "runtime_default_direct_pipeline_resident_calibrated_light_count",
)


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


def _release_direct_publication_guard_passed(
    summary: dict[str, Any],
    *,
    prefix: str,
) -> bool:
    evidence = _release_direct_publication_guard_evidence(summary, prefix=prefix)
    return (
        evidence.get("present") is True
        and evidence.get("ready") is True
        and evidence.get("decision_check_passed") is True
        and evidence.get("source_ready") is True
        and evidence.get("count_ready") is True
        and evidence.get("leaf_checks_ready") is True
        and evidence.get("acceptance_source") == "explicit_resident_artifacts_json"
        and evidence.get("calibration_source") == "resident_artifacts_json_fallback"
        and _int_or_zero(evidence.get("resident_lights")) >= 200
    )


_RELEASE_DIRECT_PUBLICATION_GUARD_MATCH_FIELDS = (
    "present",
    "ready",
    "decision_check_passed",
    "source_ready",
    "count_ready",
    "leaf_checks_ready",
    "acceptance_source",
    "calibration_source",
    "resident_lights",
)


def _release_direct_publication_guard_matches(
    left: dict[str, Any],
    *,
    left_prefix: str,
    right: dict[str, Any],
    right_prefix: str,
) -> bool:
    left_evidence = _release_direct_publication_guard_evidence(
        left,
        prefix=left_prefix,
    )
    right_evidence = _release_direct_publication_guard_evidence(
        right,
        prefix=right_prefix,
    )
    return all(
        left_evidence.get(field) == right_evidence.get(field)
        for field in _RELEASE_DIRECT_PUBLICATION_GUARD_MATCH_FIELDS
    )


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
        "raw_failed_checks": summary.get(f"{prefix}_raw_failed_checks") or [],
        "phase2_failed_checks": summary.get(f"{prefix}_phase2_failed_checks") or [],
    }


def _resident_fastpath_release_handoff_ready(
    summary: dict[str, Any],
    *,
    prefix: str,
) -> bool:
    evidence = _resident_fastpath_release_handoff_evidence(summary, prefix=prefix)
    return (
        evidence.get("present") is True
        and evidence.get("ready") is True
        and evidence.get("raw_ready") is True
        and evidence.get("phase2_ready") is True
        and evidence.get("agreement") is True
        and evidence.get("decision_check_passed") is True
        and evidence.get("phase2_check_passed") is True
        and evidence.get("raw_status") == "passed"
        and evidence.get("phase2_status") == "passed"
        and evidence.get("raw_required") is True
        and evidence.get("phase2_required") is True
        and _int_or_zero(evidence.get("raw_passed_check_count")) > 0
        and _int_or_zero(evidence.get("phase2_passed_check_count")) > 0
        and _int_or_zero(evidence.get("raw_failed_check_count")) == 0
        and _int_or_zero(evidence.get("phase2_failed_check_count")) == 0
    )


_RESIDENT_FASTPATH_RELEASE_HANDOFF_MATCH_FIELDS = (
    "present",
    "ready",
    "raw_ready",
    "phase2_ready",
    "agreement",
    "decision_check_passed",
    "phase2_check_passed",
    "raw_status",
    "phase2_status",
    "raw_required",
    "phase2_required",
    "raw_mode",
    "phase2_mode",
    "raw_passed_check_count",
    "phase2_passed_check_count",
    "raw_failed_check_count",
    "phase2_failed_check_count",
    "raw_failed_checks",
    "phase2_failed_checks",
)


def _resident_fastpath_release_handoff_matches(
    left: dict[str, Any],
    *,
    left_prefix: str,
    right: dict[str, Any],
    right_prefix: str,
) -> bool:
    left_evidence = _resident_fastpath_release_handoff_evidence(
        left,
        prefix=left_prefix,
    )
    right_evidence = _resident_fastpath_release_handoff_evidence(
        right,
        prefix=right_prefix,
    )
    return all(
        left_evidence.get(field) == right_evidence.get(field)
        for field in _RESIDENT_FASTPATH_RELEASE_HANDOFF_MATCH_FIELDS
    )


def _stack_engine_runtime_default_evidence(
    summary: dict[str, Any],
    prefix: str,
) -> dict[str, Any]:
    return {
        "status": summary.get(f"{prefix}_stack_engine_runtime_default_status"),
        "check_present": summary.get(
            f"{prefix}_stack_engine_runtime_default_check_present"
        ),
        "check_passed": summary.get(
            f"{prefix}_stack_engine_runtime_default_check_passed"
        ),
        "phase2_check_passed": summary.get(
            f"{prefix}_stack_engine_runtime_default_phase2_check_passed"
        ),
        "master_count": summary.get(
            f"{prefix}_stack_engine_runtime_default_master_count"
        ),
        "legacy_master_count": summary.get(
            f"{prefix}_stack_engine_runtime_default_legacy_master_count"
        ),
        "failed_master_count": summary.get(
            f"{prefix}_stack_engine_runtime_default_failed_master_count"
        ),
        "failed_output_count": summary.get(
            f"{prefix}_stack_engine_runtime_default_failed_output_count"
        ),
        "explicit_cuda_fast_path_count": summary.get(
            f"{prefix}_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ),
        "failed_masters": summary.get(
            f"{prefix}_stack_engine_runtime_default_failed_masters"
        )
        or [],
        "failed_outputs": summary.get(
            f"{prefix}_stack_engine_runtime_default_failed_outputs"
        )
        or [],
    }


def _stack_engine_runtime_default_side_passed(
    summary: dict[str, Any],
    prefix: str,
) -> bool:
    evidence = _stack_engine_runtime_default_evidence(summary, prefix)
    return (
        evidence.get("status") == "passed"
        and evidence.get("check_present") is True
        and evidence.get("check_passed") is True
        and evidence.get("phase2_check_passed") is True
        and _int_or_zero(evidence.get("legacy_master_count")) == 0
        and _int_or_zero(evidence.get("failed_master_count")) == 0
        and _int_or_zero(evidence.get("failed_output_count")) == 0
        and not evidence.get("failed_masters")
        and not evidence.get("failed_outputs")
    )


def _stack_engine_runtime_default_matches(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    return all(
        left.get(field) == right.get(field)
        for field in _STACK_ENGINE_RUNTIME_DEFAULT_FIELDS
    )


def _runtime_default_direct_acceptance_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("runtime_default_direct_evidence_present") is True
        and summary.get("runtime_default_direct_evidence_ready") is True
        and summary.get("runtime_default_direct_acceptance_fastpath") is True
        and summary.get("runtime_default_direct_acceptance_fastpath_source")
        == "explicit_resident_artifacts_json"
        and _int_or_zero(
            summary.get("runtime_default_direct_acceptance_fastpath_check_count")
        )
        > 0
        and _int_or_zero(
            summary.get(
                "runtime_default_direct_acceptance_fastpath_failed_check_count"
            )
        )
        == 0
        and not summary.get("runtime_default_direct_acceptance_fastpath_failed_checks")
    )


def _runtime_default_direct_pipeline_calibration_passed(
    summary: dict[str, Any],
) -> bool:
    return (
        summary.get("runtime_default_direct_evidence_present") is True
        and summary.get("runtime_default_direct_evidence_ready") is True
        and summary.get("runtime_default_direct_pipeline_calibration") is True
        and summary.get("runtime_default_direct_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
        and summary.get(
            "runtime_default_direct_pipeline_calibration_generated_for_contract"
        )
        is True
        and summary.get("runtime_default_direct_pipeline_calibration_path_exists")
        is False
        and summary.get(
            "runtime_default_direct_pipeline_resident_native_calibration_artifact"
        )
        is True
        and _int_or_zero(
            summary.get(
                "runtime_default_direct_pipeline_resident_calibrated_light_count"
            )
        )
        > 0
    )


def _runtime_default_direct_evidence_matches(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    return all(
        left.get(field) == right.get(field)
        for field in _RUNTIME_DEFAULT_DIRECT_EVIDENCE_FIELDS
    )


def _runtime_default_direct_evidence(
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "present": summary.get("runtime_default_direct_evidence_present"),
        "ready": summary.get("runtime_default_direct_evidence_ready"),
        "acceptance_direct_fastpath": summary.get(
            "runtime_default_direct_acceptance_fastpath"
        ),
        "acceptance_source": summary.get(
            "runtime_default_direct_acceptance_fastpath_source"
        ),
        "acceptance_check_count": summary.get(
            "runtime_default_direct_acceptance_fastpath_check_count"
        ),
        "acceptance_failed_check_count": summary.get(
            "runtime_default_direct_acceptance_fastpath_failed_check_count"
        ),
        "acceptance_failed_checks": summary.get(
            "runtime_default_direct_acceptance_fastpath_failed_checks"
        ),
        "pipeline_direct_calibration": summary.get(
            "runtime_default_direct_pipeline_calibration"
        ),
        "pipeline_calibration_source": summary.get(
            "runtime_default_direct_pipeline_calibration_source"
        ),
        "pipeline_generated_for_contract": summary.get(
            "runtime_default_direct_pipeline_calibration_generated_for_contract"
        ),
        "pipeline_path_exists": summary.get(
            "runtime_default_direct_pipeline_calibration_path_exists"
        ),
        "pipeline_resident_native_calibration_artifact": summary.get(
            "runtime_default_direct_pipeline_resident_native_calibration_artifact"
        ),
        "pipeline_resident_calibrated_light_count": summary.get(
            "runtime_default_direct_pipeline_resident_calibrated_light_count"
        ),
    }


def _matrix_summary(payload: dict[str, Any]) -> dict[str, Any]:
    machine = payload.get("current_machine") if isinstance(payload.get("current_machine"), dict) else {}
    promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    package_labels = [
        str(row.get("label"))
        for row in payload.get("packages") or []
        if isinstance(row, dict) and row.get("label")
    ]
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "primary_package": machine.get("primary_package"),
        "ordered_try_list": [str(item) for item in machine.get("ordered_try_list") or []],
        "package_labels": package_labels,
        "default_promotion_status": promotion.get("status"),
        "default_promotion_passed": promotion.get("passed"),
        "default_promotion_default_change_ready": promotion.get("default_change_ready"),
        "default_route_passed": promotion.get("default_route_passed"),
        "default_route_route_contract_passed": promotion.get(
            "default_route_route_contract_passed"
        ),
        "default_route_route_check_count": promotion.get("default_route_route_check_count"),
        "default_route_speedup_vs_reference": promotion.get(
            "default_route_speedup_vs_reference"
        ),
        "integration_rejection_sample_counts_match_maps": promotion.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "rejection_sample_accounting_status": promotion.get(
            "rejection_sample_accounting_status"
        ),
        "rejection_sample_accounting_failed_count": promotion.get(
            "rejection_sample_accounting_failed_count"
        ),
        "integration_sample_accounting_closure": promotion.get(
            "integration_sample_accounting_closure"
        ),
        "sample_accounting_closure": promotion.get("sample_accounting_closure"),
        "sample_accounting_closure_status": promotion.get(
            "sample_accounting_closure_status"
        ),
        "sample_accounting_closure_present_count": promotion.get(
            "sample_accounting_closure_present_count"
        ),
        "sample_accounting_closure_failed_count": promotion.get(
            "sample_accounting_closure_failed_count"
        ),
        "integration_engine_policy": promotion.get("integration_engine_policy"),
        "integration_engine_policy_ready": promotion.get(
            "integration_engine_policy_ready"
        ),
        "acceptance_integration_engine_policy_status": promotion.get(
            "acceptance_integration_engine_policy_status"
        ),
        "acceptance_integration_engine_policy_check_present": promotion.get(
            "acceptance_integration_engine_policy_check_present"
        ),
        "acceptance_integration_engine_policy_check_passed": promotion.get(
            "acceptance_integration_engine_policy_check_passed"
        ),
        "acceptance_integration_engine_policy_phase2_check_passed": promotion.get(
            "acceptance_integration_engine_policy_phase2_check_passed"
        ),
        "acceptance_integration_engine_policy_non_resident_count": promotion.get(
            "acceptance_integration_engine_policy_non_resident_count"
        ),
        "acceptance_integration_engine_policy_failed_count": promotion.get(
            "acceptance_integration_engine_policy_failed_count"
        ),
        "acceptance_integration_engine_policy_failed_items": promotion.get(
            "acceptance_integration_engine_policy_failed_items"
        )
        or [],
        "pipeline_integration_engine_policy_status": promotion.get(
            "pipeline_integration_engine_policy_status"
        ),
        "pipeline_integration_engine_policy_check_present": promotion.get(
            "pipeline_integration_engine_policy_check_present"
        ),
        "pipeline_integration_engine_policy_check_passed": promotion.get(
            "pipeline_integration_engine_policy_check_passed"
        ),
        "pipeline_integration_engine_policy_phase2_check_passed": promotion.get(
            "pipeline_integration_engine_policy_phase2_check_passed"
        ),
        "pipeline_integration_engine_policy_default_engine_policy": promotion.get(
            "pipeline_integration_engine_policy_default_engine_policy"
        ),
        "pipeline_integration_engine_policy_non_resident_count": promotion.get(
            "pipeline_integration_engine_policy_non_resident_count"
        ),
        "pipeline_integration_engine_policy_failed_count": promotion.get(
            "pipeline_integration_engine_policy_failed_count"
        ),
        "pipeline_integration_engine_policy_failed_items": promotion.get(
            "pipeline_integration_engine_policy_failed_items"
        )
        or [],
        "stack_engine_runtime_default": promotion.get("stack_engine_runtime_default"),
        "stack_engine_runtime_default_ready": promotion.get(
            "stack_engine_runtime_default_ready"
        ),
        "acceptance_stack_engine_runtime_default_status": promotion.get(
            "acceptance_stack_engine_runtime_default_status"
        ),
        "acceptance_stack_engine_runtime_default_check_present": promotion.get(
            "acceptance_stack_engine_runtime_default_check_present"
        ),
        "acceptance_stack_engine_runtime_default_check_passed": promotion.get(
            "acceptance_stack_engine_runtime_default_check_passed"
        ),
        "acceptance_stack_engine_runtime_default_phase2_check_passed": promotion.get(
            "acceptance_stack_engine_runtime_default_phase2_check_passed"
        ),
        "acceptance_stack_engine_runtime_default_master_count": promotion.get(
            "acceptance_stack_engine_runtime_default_master_count"
        ),
        "acceptance_stack_engine_runtime_default_legacy_master_count": promotion.get(
            "acceptance_stack_engine_runtime_default_legacy_master_count"
        ),
        "acceptance_stack_engine_runtime_default_failed_master_count": promotion.get(
            "acceptance_stack_engine_runtime_default_failed_master_count"
        ),
        "acceptance_stack_engine_runtime_default_failed_output_count": promotion.get(
            "acceptance_stack_engine_runtime_default_failed_output_count"
        ),
        "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": promotion.get(
            "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ),
        "acceptance_stack_engine_runtime_default_failed_masters": promotion.get(
            "acceptance_stack_engine_runtime_default_failed_masters"
        )
        or [],
        "acceptance_stack_engine_runtime_default_failed_outputs": promotion.get(
            "acceptance_stack_engine_runtime_default_failed_outputs"
        )
        or [],
        "pipeline_stack_engine_runtime_default_status": promotion.get(
            "pipeline_stack_engine_runtime_default_status"
        ),
        "pipeline_stack_engine_runtime_default_check_present": promotion.get(
            "pipeline_stack_engine_runtime_default_check_present"
        ),
        "pipeline_stack_engine_runtime_default_check_passed": promotion.get(
            "pipeline_stack_engine_runtime_default_check_passed"
        ),
        "pipeline_stack_engine_runtime_default_phase2_check_passed": promotion.get(
            "pipeline_stack_engine_runtime_default_phase2_check_passed"
        ),
        "pipeline_stack_engine_runtime_default_master_count": promotion.get(
            "pipeline_stack_engine_runtime_default_master_count"
        ),
        "pipeline_stack_engine_runtime_default_legacy_master_count": promotion.get(
            "pipeline_stack_engine_runtime_default_legacy_master_count"
        ),
        "pipeline_stack_engine_runtime_default_failed_master_count": promotion.get(
            "pipeline_stack_engine_runtime_default_failed_master_count"
        ),
        "pipeline_stack_engine_runtime_default_failed_output_count": promotion.get(
            "pipeline_stack_engine_runtime_default_failed_output_count"
        ),
        "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": promotion.get(
            "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ),
        "pipeline_stack_engine_runtime_default_failed_masters": promotion.get(
            "pipeline_stack_engine_runtime_default_failed_masters"
        )
        or [],
        "pipeline_stack_engine_runtime_default_failed_outputs": promotion.get(
            "pipeline_stack_engine_runtime_default_failed_outputs"
        )
        or [],
        "stack_engine_contract": promotion.get("stack_engine_contract"),
        "stack_engine_contract_present": promotion.get("stack_engine_contract_present"),
        "stack_engine_contract_ready": promotion.get("stack_engine_contract_ready"),
        "stack_engine_contract_phase2_check_passed": promotion.get(
            "stack_engine_contract_phase2_check_passed"
        ),
        "stack_engine_contract_status": promotion.get("stack_engine_contract_status"),
        "stack_engine_contract_passed": promotion.get("stack_engine_contract_passed"),
        "stack_engine_contract_scope": promotion.get("stack_engine_contract_scope"),
        "stack_engine_contract_adoption_recommendation": promotion.get(
            "stack_engine_contract_adoption_recommendation"
        ),
        "stack_engine_contract_default_gap_count": promotion.get(
            "stack_engine_contract_default_gap_count"
        ),
        "stack_engine_contract_blocker_count": promotion.get(
            "stack_engine_contract_blocker_count"
        ),
        "stack_engine_contract_blockers": promotion.get("stack_engine_contract_blockers")
        or [],
        **_resident_fastpath_release_handoff_fields(
            promotion,
            output_prefix="resident_registration_fastpath_release_handoff",
        ),
        **_release_direct_publication_guard_fields(
            payload,
            output_prefix="release_decision_direct_runtime_publication_guard",
        ),
        **_release_direct_publication_guard_fields(
            promotion,
            output_prefix=(
                "default_promotion_release_decision_direct_runtime_publication_guard"
            ),
        ),
        **_runtime_default_direct_evidence_summary(promotion),
        **_resident_winsorized_sweep_summary(promotion),
        **_stack_engine_publication_audit_summary(promotion),
    }


def _default_promotion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    route = (
        payload.get("default_route_acceptance")
        if isinstance(payload.get("default_route_acceptance"), dict)
        else {}
    )
    pipeline = (
        payload.get("pipeline_contract") if isinstance(payload.get("pipeline_contract"), dict) else {}
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
    stack_engine = (
        payload.get("stack_engine_contract")
        if isinstance(payload.get("stack_engine_contract"), dict)
        else {}
    )
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
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "default_change_ready": payload.get("default_change_ready"),
        "recommendation": payload.get("recommendation"),
        "default_route_status": route.get("status"),
        "default_route_passed": route.get("passed"),
        "default_route_route_contract_passed": route.get("route_contract_passed"),
        "default_route_route_check_count": route.get("route_check_count"),
        "default_route_speedup_vs_reference": route.get("speedup_vs_reference"),
        "pipeline_contract_status": pipeline.get("status"),
        "pipeline_contract_passed": pipeline.get("passed"),
        "integration_rejection_sample_counts_match_maps": pipeline.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "rejection_sample_accounting": rejection_sample_accounting,
        "rejection_sample_accounting_status": pipeline.get(
            "rejection_sample_accounting_status"
        ),
        "rejection_sample_accounting_failed_count": pipeline.get(
            "rejection_sample_accounting_failed_count"
        ),
        "integration_sample_accounting_closure": pipeline.get(
            "integration_sample_accounting_closure"
        ),
        "sample_accounting_closure": sample_accounting_closure,
        "sample_accounting_closure_status": pipeline.get(
            "sample_accounting_closure_status"
        ),
        "sample_accounting_closure_present_count": pipeline.get(
            "sample_accounting_closure_present_count"
        ),
        "sample_accounting_closure_failed_count": pipeline.get(
            "sample_accounting_closure_failed_count"
        ),
        "integration_engine_policy": integration_engine_policy,
        "integration_engine_policy_ready": integration_engine_policy.get("ready"),
        "acceptance_integration_engine_policy_status": integration_engine_policy.get(
            "acceptance_status"
        ),
        "acceptance_integration_engine_policy_check_present": (
            integration_engine_policy.get("acceptance_check_present")
        ),
        "acceptance_integration_engine_policy_check_passed": (
            integration_engine_policy.get("acceptance_check_passed")
        ),
        "acceptance_integration_engine_policy_phase2_check_passed": (
            integration_engine_policy.get("acceptance_phase2_check_passed")
        ),
        "acceptance_integration_engine_policy_non_resident_count": (
            integration_engine_policy.get("acceptance_non_resident_count")
        ),
        "acceptance_integration_engine_policy_failed_count": (
            integration_engine_policy.get("acceptance_failed_count")
        ),
        "acceptance_integration_engine_policy_failed_items": (
            integration_engine_policy.get("acceptance_failed_items") or []
        ),
        "pipeline_integration_engine_policy_status": integration_engine_policy.get(
            "pipeline_status"
        ),
        "pipeline_integration_engine_policy_check_present": (
            integration_engine_policy.get("pipeline_check_present")
        ),
        "pipeline_integration_engine_policy_check_passed": (
            integration_engine_policy.get("pipeline_check_passed")
        ),
        "pipeline_integration_engine_policy_phase2_check_passed": (
            integration_engine_policy.get("pipeline_phase2_check_passed")
        ),
        "pipeline_integration_engine_policy_default_engine_policy": (
            integration_engine_policy.get("pipeline_default_engine_policy")
        ),
        "pipeline_integration_engine_policy_non_resident_count": (
            integration_engine_policy.get("pipeline_non_resident_count")
        ),
        "pipeline_integration_engine_policy_failed_count": (
            integration_engine_policy.get("pipeline_failed_count")
        ),
        "pipeline_integration_engine_policy_failed_items": (
            integration_engine_policy.get("pipeline_failed_items") or []
        ),
        "stack_engine_runtime_default": stack_engine_runtime_default,
        "stack_engine_runtime_default_ready": stack_engine_runtime_default.get(
            "ready"
        ),
        "acceptance_stack_engine_runtime_default_status": (
            stack_engine_runtime_default.get("acceptance_status")
        ),
        "acceptance_stack_engine_runtime_default_check_present": (
            stack_engine_runtime_default.get("acceptance_check_present")
        ),
        "acceptance_stack_engine_runtime_default_check_passed": (
            stack_engine_runtime_default.get("acceptance_check_passed")
        ),
        "acceptance_stack_engine_runtime_default_phase2_check_passed": (
            stack_engine_runtime_default.get("acceptance_phase2_check_passed")
        ),
        "acceptance_stack_engine_runtime_default_master_count": (
            stack_engine_runtime_default.get("acceptance_master_count")
        ),
        "acceptance_stack_engine_runtime_default_legacy_master_count": (
            stack_engine_runtime_default.get("acceptance_legacy_master_count")
        ),
        "acceptance_stack_engine_runtime_default_failed_master_count": (
            stack_engine_runtime_default.get("acceptance_failed_master_count")
        ),
        "acceptance_stack_engine_runtime_default_failed_output_count": (
            stack_engine_runtime_default.get("acceptance_failed_output_count")
        ),
        "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            stack_engine_runtime_default.get("acceptance_explicit_cuda_fast_path_count")
        ),
        "acceptance_stack_engine_runtime_default_failed_masters": (
            stack_engine_runtime_default.get("acceptance_failed_masters") or []
        ),
        "acceptance_stack_engine_runtime_default_failed_outputs": (
            stack_engine_runtime_default.get("acceptance_failed_outputs") or []
        ),
        "pipeline_stack_engine_runtime_default_status": (
            stack_engine_runtime_default.get("pipeline_status")
        ),
        "pipeline_stack_engine_runtime_default_check_present": (
            stack_engine_runtime_default.get("pipeline_check_present")
        ),
        "pipeline_stack_engine_runtime_default_check_passed": (
            stack_engine_runtime_default.get("pipeline_check_passed")
        ),
        "pipeline_stack_engine_runtime_default_phase2_check_passed": (
            stack_engine_runtime_default.get("pipeline_phase2_check_passed")
        ),
        "pipeline_stack_engine_runtime_default_master_count": (
            stack_engine_runtime_default.get("pipeline_master_count")
        ),
        "pipeline_stack_engine_runtime_default_legacy_master_count": (
            stack_engine_runtime_default.get("pipeline_legacy_master_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_master_count": (
            stack_engine_runtime_default.get("pipeline_failed_master_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_output_count": (
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
        "stack_engine_contract_blockers": stack_engine.get("default_promotion_blockers")
        or [],
        **_resident_fastpath_release_handoff_fields(
            payload,
            output_prefix="resident_registration_fastpath_release_handoff",
        ),
        **_release_direct_publication_guard_fields(
            payload,
            output_prefix="release_decision_direct_runtime_publication_guard",
        ),
        **_runtime_default_direct_evidence_summary(payload),
        **_resident_winsorized_sweep_summary(payload),
        **_stack_engine_publication_audit_summary(payload),
    }


def _plan_rejection_sample_summary(payload: dict[str, Any]) -> dict[str, Any]:
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = (
        phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    )
    matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    checks = _checks_by_name(payload.get("checks") or [])
    phase2_check = checks.get("phase2_pipeline_rejection_sample_accounting_passed") or {}
    matrix_check = checks.get("windows_release_matrix_rejection_sample_accounting_passed") or {}
    return {
        "phase2_check_passed": phase2_check.get("passed"),
        "phase2_check_evidence": phase2_check.get("evidence"),
        "phase2_integration_rejection_sample_counts_match_maps": phase2_status.get(
            "pipeline_integration_rejection_sample_counts_match_maps"
        ),
        "phase2_rejection_sample_accounting_status": phase2_status.get(
            "pipeline_rejection_sample_accounting_status"
        ),
        "phase2_rejection_sample_accounting_failed_count": phase2_status.get(
            "pipeline_rejection_sample_accounting_failed_count"
        ),
        "release_matrix_check_passed": matrix_check.get("passed"),
        "release_matrix_check_evidence": matrix_check.get("evidence"),
        "release_matrix_integration_rejection_sample_counts_match_maps": matrix.get(
            "integration_rejection_sample_counts_match_maps"
        ),
        "release_matrix_rejection_sample_accounting_status": matrix.get(
            "rejection_sample_accounting_status"
        ),
        "release_matrix_rejection_sample_accounting_failed_count": matrix.get(
            "rejection_sample_accounting_failed_count"
        ),
    }


def _plan_sample_closure_summary(payload: dict[str, Any]) -> dict[str, Any]:
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = (
        phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    )
    matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    checks = _checks_by_name(payload.get("checks") or [])
    phase2_check = checks.get("phase2_pipeline_sample_accounting_closure_passed") or {}
    matrix_check = checks.get("windows_release_matrix_sample_accounting_closure_passed") or {}
    return {
        "phase2_check_passed": phase2_check.get("passed"),
        "phase2_check_evidence": phase2_check.get("evidence"),
        "phase2_integration_sample_accounting_closure": phase2_status.get(
            "pipeline_integration_sample_accounting_closure"
        ),
        "phase2_sample_accounting_closure_status": phase2_status.get(
            "pipeline_sample_accounting_closure_status"
        ),
        "phase2_sample_accounting_closure_present_count": phase2_status.get(
            "pipeline_sample_accounting_closure_present_count"
        ),
        "phase2_sample_accounting_closure_failed_count": phase2_status.get(
            "pipeline_sample_accounting_closure_failed_count"
        ),
        "release_matrix_check_passed": matrix_check.get("passed"),
        "release_matrix_check_evidence": matrix_check.get("evidence"),
        "release_matrix_integration_sample_accounting_closure": matrix.get(
            "integration_sample_accounting_closure"
        ),
        "release_matrix_sample_accounting_closure_status": matrix.get(
            "sample_accounting_closure_status"
        ),
        "release_matrix_sample_accounting_closure_present_count": matrix.get(
            "sample_accounting_closure_present_count"
        ),
        "release_matrix_sample_accounting_closure_failed_count": matrix.get(
            "sample_accounting_closure_failed_count"
        ),
    }


def _plan_stack_engine_summary(payload: dict[str, Any]) -> dict[str, Any]:
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = (
        phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    )
    matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    checks = _checks_by_name(payload.get("checks") or [])
    phase2_check = checks.get("phase2_stack_engine_default_contract_ready") or {}
    matrix_check = checks.get("windows_release_matrix_stack_engine_contract_ready") or {}
    agreement_check = checks.get("phase2_release_matrix_stack_engine_contract_agree") or {}
    return {
        "phase2_check_passed": phase2_check.get("passed"),
        "phase2_check_evidence": phase2_check.get("evidence"),
        "phase2_status": phase2_status.get("stack_engine_default_contract_status"),
        "phase2_phase2_check_passed": phase2_status.get(
            "stack_engine_default_contract_phase2_check_passed"
        ),
        "phase2_passed": phase2_status.get("stack_engine_default_contract_passed"),
        "phase2_scope": phase2_status.get("stack_engine_default_contract_scope"),
        "phase2_adoption_recommendation": phase2_status.get(
            "stack_engine_default_contract_adoption_recommendation"
        ),
        "phase2_default_promotion_recommendation": phase2_status.get(
            "stack_engine_default_contract_default_promotion_recommendation"
        ),
        "phase2_default_gap_count": phase2_status.get(
            "stack_engine_default_contract_default_gap_count"
        ),
        "phase2_blocker_count": phase2_status.get(
            "stack_engine_default_contract_blocker_count"
        ),
        "phase2_blockers": phase2_status.get("stack_engine_default_contract_blockers")
        or [],
        "release_matrix_check_passed": matrix_check.get("passed"),
        "release_matrix_check_evidence": matrix_check.get("evidence"),
        "release_matrix_ready": matrix.get("stack_engine_contract_ready"),
        "release_matrix_phase2_check_passed": matrix.get(
            "stack_engine_contract_phase2_check_passed"
        ),
        "release_matrix_status": matrix.get("stack_engine_contract_status"),
        "release_matrix_passed": matrix.get("stack_engine_contract_passed"),
        "release_matrix_scope": matrix.get("stack_engine_contract_scope"),
        "release_matrix_adoption_recommendation": matrix.get(
            "stack_engine_contract_adoption_recommendation"
        ),
        "release_matrix_default_gap_count": matrix.get(
            "stack_engine_contract_default_gap_count"
        ),
        "release_matrix_blocker_count": matrix.get("stack_engine_contract_blocker_count"),
        "release_matrix_blockers": matrix.get("stack_engine_contract_blockers") or [],
        "agreement_check_passed": agreement_check.get("passed"),
        "agreement_check_evidence": agreement_check.get("evidence"),
    }


def _plan_release_direct_publication_guard_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    matrix = (
        payload.get("release_matrix")
        if isinstance(payload.get("release_matrix"), dict)
        else {}
    )
    checks = _checks_by_name(payload.get("checks") or [])
    matrix_check = checks.get(
        "windows_release_matrix_release_decision_direct_runtime_publication_guard_passed"
    ) or {}
    default_check = checks.get(
        "windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
    ) or {}
    matrix_prefix = "release_decision_direct_runtime_publication_guard"
    default_prefix = (
        "default_promotion_release_decision_direct_runtime_publication_guard"
    )
    return {
        "release_matrix_check_passed": matrix_check.get("passed"),
        "release_matrix_check_evidence": matrix_check.get("evidence"),
        "release_matrix_present": matrix.get(f"{matrix_prefix}_present"),
        "release_matrix_ready": matrix.get(f"{matrix_prefix}_ready"),
        "release_matrix_decision_check_passed": matrix.get(
            f"{matrix_prefix}_check_passed"
        ),
        "release_matrix_source_ready": matrix.get(f"{matrix_prefix}_source_ready"),
        "release_matrix_count_ready": matrix.get(f"{matrix_prefix}_count_ready"),
        "release_matrix_leaf_checks_ready": matrix.get(
            f"{matrix_prefix}_leaf_checks_ready"
        ),
        "release_matrix_raw_acceptance_source": matrix.get(
            f"{matrix_prefix}_raw_acceptance_source"
        ),
        "release_matrix_raw_calibration_source": matrix.get(
            f"{matrix_prefix}_raw_calibration_source"
        ),
        "release_matrix_raw_resident_lights": matrix.get(
            f"{matrix_prefix}_raw_resident_lights"
        ),
        "release_matrix_default_promotion_check_passed": default_check.get("passed"),
        "release_matrix_default_promotion_check_evidence": default_check.get(
            "evidence"
        ),
        "release_matrix_default_promotion_present": matrix.get(
            f"{default_prefix}_present"
        ),
        "release_matrix_default_promotion_ready": matrix.get(
            f"{default_prefix}_ready"
        ),
        "release_matrix_default_promotion_decision_check_passed": matrix.get(
            f"{default_prefix}_check_passed"
        ),
        "release_matrix_default_promotion_source_ready": matrix.get(
            f"{default_prefix}_source_ready"
        ),
        "release_matrix_default_promotion_count_ready": matrix.get(
            f"{default_prefix}_count_ready"
        ),
        "release_matrix_default_promotion_leaf_checks_ready": matrix.get(
            f"{default_prefix}_leaf_checks_ready"
        ),
        "release_matrix_default_promotion_raw_acceptance_source": matrix.get(
            f"{default_prefix}_raw_acceptance_source"
        ),
        "release_matrix_default_promotion_raw_calibration_source": matrix.get(
            f"{default_prefix}_raw_calibration_source"
        ),
        "release_matrix_default_promotion_raw_resident_lights": matrix.get(
            f"{default_prefix}_raw_resident_lights"
        ),
    }


def _plan_resident_fastpath_release_handoff_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    matrix = (
        payload.get("release_matrix")
        if isinstance(payload.get("release_matrix"), dict)
        else {}
    )
    checks = _checks_by_name(payload.get("checks") or [])
    matrix_check = checks.get(
        "windows_release_matrix_resident_fastpath_release_handoff_ready"
    ) or {}
    prefix = "resident_registration_fastpath_release_handoff"
    return {
        "release_matrix_check_passed": matrix_check.get("passed"),
        "release_matrix_check_evidence": matrix_check.get("evidence"),
        "release_matrix_present": matrix.get(f"{prefix}_present"),
        "release_matrix_ready": matrix.get(f"{prefix}_ready"),
        "release_matrix_raw_ready": matrix.get(f"{prefix}_raw_ready"),
        "release_matrix_phase2_ready": matrix.get(f"{prefix}_phase2_ready"),
        "release_matrix_agreement": matrix.get(f"{prefix}_agreement"),
        "release_matrix_decision_check_passed": matrix.get(
            f"{prefix}_decision_check_passed"
        ),
        "release_matrix_phase2_check_passed": matrix.get(
            f"{prefix}_phase2_check_passed"
        ),
        "release_matrix_raw_status": matrix.get(f"{prefix}_raw_status"),
        "release_matrix_phase2_status": matrix.get(f"{prefix}_phase2_status"),
        "release_matrix_raw_required": matrix.get(f"{prefix}_raw_required"),
        "release_matrix_phase2_required": matrix.get(f"{prefix}_phase2_required"),
        "release_matrix_raw_mode": matrix.get(f"{prefix}_raw_mode"),
        "release_matrix_phase2_mode": matrix.get(f"{prefix}_phase2_mode"),
        "release_matrix_raw_passed_check_count": matrix.get(
            f"{prefix}_raw_passed_check_count"
        ),
        "release_matrix_phase2_passed_check_count": matrix.get(
            f"{prefix}_phase2_passed_check_count"
        ),
        "release_matrix_raw_failed_check_count": matrix.get(
            f"{prefix}_raw_failed_check_count"
        ),
        "release_matrix_phase2_failed_check_count": matrix.get(
            f"{prefix}_phase2_failed_check_count"
        ),
        "release_matrix_raw_failed_checks": matrix.get(f"{prefix}_raw_failed_checks")
        or [],
        "release_matrix_phase2_failed_checks": matrix.get(
            f"{prefix}_phase2_failed_checks"
        )
        or [],
    }


def _stack_engine_plan_phase2_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("phase2_check_passed") is True
        and summary.get("phase2_status") == "passed"
        and summary.get("phase2_phase2_check_passed") is True
        and summary.get("phase2_passed") is True
        and summary.get("phase2_scope") == "all"
        and summary.get("phase2_adoption_recommendation") == "stack_engine_default_ready"
        and summary.get("phase2_default_promotion_recommendation")
        == "stack_engine_default_ready"
        and _int_or_zero(summary.get("phase2_default_gap_count")) == 0
        and _int_or_zero(summary.get("phase2_blocker_count")) == 0
    )


def _stack_engine_matrix_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("stack_engine_contract_present") is True
        and summary.get("stack_engine_contract_ready") is True
        and summary.get("stack_engine_contract_phase2_check_passed") is True
        and summary.get("stack_engine_contract_status") == "passed"
        and summary.get("stack_engine_contract_passed") is True
        and summary.get("stack_engine_contract_scope") == "all"
        and summary.get("stack_engine_contract_adoption_recommendation")
        == "stack_engine_default_ready"
        and _int_or_zero(summary.get("stack_engine_contract_default_gap_count")) == 0
        and _int_or_zero(summary.get("stack_engine_contract_blocker_count")) == 0
    )


def _stack_engine_plan_matrix_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("release_matrix_check_passed") is True
        and summary.get("release_matrix_ready") is True
        and summary.get("release_matrix_phase2_check_passed") is True
        and summary.get("release_matrix_status") == "passed"
        and summary.get("release_matrix_passed") is True
        and summary.get("release_matrix_scope") == "all"
        and summary.get("release_matrix_adoption_recommendation")
        == "stack_engine_default_ready"
        and _int_or_zero(summary.get("release_matrix_default_gap_count")) == 0
        and _int_or_zero(summary.get("release_matrix_blocker_count")) == 0
    )


def _resident_winsorized_sweep_audit_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("resident_winsorized_sweep_present") is True
        and summary.get("resident_winsorized_sweep_status") == "passed"
        and summary.get("resident_winsorized_sweep_passed") is True
        and summary.get("resident_winsorized_sweep_phase2_check_passed") is True
        and _int_or_zero(summary.get("resident_winsorized_sweep_failed_check_count"))
        == 0
        and not summary.get("resident_winsorized_sweep_failed_checks")
    )


def _resident_winsorized_required_frame_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("resident_winsorized_sweep_required_frame_count_passed") is True
        and _int_or_zero(
            summary.get("resident_winsorized_sweep_required_frame_count")
        )
        >= 200
    )


def _resident_winsorized_check_count_ready(summary: dict[str, Any]) -> bool:
    return _int_or_zero(summary.get("resident_winsorized_sweep_check_count")) > 0


def _resident_winsorized_sweep_evidence(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "present": summary.get("resident_winsorized_sweep_present"),
        "status": summary.get("resident_winsorized_sweep_status"),
        "passed": summary.get("resident_winsorized_sweep_passed"),
        "phase2_check_passed": summary.get(
            "resident_winsorized_sweep_phase2_check_passed"
        ),
        "check_count": summary.get("resident_winsorized_sweep_check_count"),
        "failed_check_count": summary.get(
            "resident_winsorized_sweep_failed_check_count"
        ),
        "failed_checks": summary.get("resident_winsorized_sweep_failed_checks"),
        "required_frame_count": summary.get(
            "resident_winsorized_sweep_required_frame_count"
        ),
        "required_frame_count_passed": summary.get(
            "resident_winsorized_sweep_required_frame_count_passed"
        ),
        "required_frame_master_rms": summary.get(
            "resident_winsorized_sweep_required_frame_master_rms"
        ),
        "required_frame_master_max_abs": summary.get(
            "resident_winsorized_sweep_required_frame_master_max_abs"
        ),
        "required_frame_cuda_hardened_s": summary.get(
            "resident_winsorized_sweep_required_frame_cuda_hardened_s"
        ),
        "path": summary.get("resident_winsorized_sweep_path"),
        "sweep_path": summary.get("resident_winsorized_sweep_sweep_path"),
    }


def _stack_engine_publication_audit_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("stack_engine_publication_audit_present") is True
        and summary.get("stack_engine_publication_audit_ready") is True
        and summary.get("stack_engine_publication_audit_status") == "passed"
        and summary.get("stack_engine_publication_audit_passed") is True
        and summary.get("stack_engine_publication_audit_phase2_check_passed") is True
        and _int_or_zero(
            summary.get("stack_engine_publication_audit_failed_check_count")
        )
        == 0
        and not summary.get("stack_engine_publication_audit_failed_checks")
    )


def _stack_engine_publication_policy_chain_passed(summary: dict[str, Any]) -> bool:
    return (
        summary.get("stack_engine_publication_policy_chain_phase2_check_passed")
        is True
        and summary.get("stack_engine_publication_publish_preflight_policy_ready")
        is True
        and summary.get("stack_engine_publication_phase2_policy_ready") is True
        and summary.get("stack_engine_publication_policy_agreement") is True
    )


def _stack_engine_publication_resident_winsorized_chain_passed(
    summary: dict[str, Any],
) -> bool:
    return (
        summary.get(
            "stack_engine_publication_resident_winsorized_chain_phase2_check_passed"
        )
        is True
        and summary.get(
            "stack_engine_publication_publish_preflight_resident_winsorized_ready"
        )
        is True
        and summary.get("stack_engine_publication_phase2_resident_winsorized_ready")
        is True
        and summary.get("stack_engine_publication_resident_winsorized_agreement")
        is True
    )


def _stack_engine_publication_audit_evidence(
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "present": summary.get("stack_engine_publication_audit_present"),
        "ready": summary.get("stack_engine_publication_audit_ready"),
        "status": summary.get("stack_engine_publication_audit_status"),
        "passed": summary.get("stack_engine_publication_audit_passed"),
        "phase2_check_passed": summary.get(
            "stack_engine_publication_audit_phase2_check_passed"
        ),
        "recommendation": summary.get(
            "stack_engine_publication_audit_recommendation"
        ),
        "check_count": summary.get("stack_engine_publication_audit_check_count"),
        "failed_check_count": summary.get(
            "stack_engine_publication_audit_failed_check_count"
        ),
        "failed_checks": summary.get("stack_engine_publication_audit_failed_checks"),
    }


def _stack_engine_publication_policy_chain_evidence(
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase2_check_passed": summary.get(
            "stack_engine_publication_policy_chain_phase2_check_passed"
        ),
        "publish_preflight_policy_ready": summary.get(
            "stack_engine_publication_publish_preflight_policy_ready"
        ),
        "phase2_policy_ready": summary.get(
            "stack_engine_publication_phase2_policy_ready"
        ),
        "policy_agreement": summary.get("stack_engine_publication_policy_agreement"),
    }


def _stack_engine_publication_resident_winsorized_chain_evidence(
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase2_check_passed": summary.get(
            "stack_engine_publication_resident_winsorized_chain_phase2_check_passed"
        ),
        "publish_preflight_resident_winsorized_ready": summary.get(
            "stack_engine_publication_publish_preflight_resident_winsorized_ready"
        ),
        "phase2_resident_winsorized_ready": summary.get(
            "stack_engine_publication_phase2_resident_winsorized_ready"
        ),
        "resident_winsorized_agreement": summary.get(
            "stack_engine_publication_resident_winsorized_agreement"
        ),
    }


_STACK_ENGINE_PUBLICATION_AUDIT_MATCH_FIELDS = (
    "stack_engine_publication_audit_present",
    "stack_engine_publication_audit_ready",
    "stack_engine_publication_audit_status",
    "stack_engine_publication_audit_passed",
    "stack_engine_publication_audit_phase2_check_passed",
    "stack_engine_publication_audit_failed_check_count",
    "stack_engine_publication_policy_chain_phase2_check_passed",
    "stack_engine_publication_publish_preflight_policy_ready",
    "stack_engine_publication_phase2_policy_ready",
    "stack_engine_publication_policy_agreement",
    "stack_engine_publication_resident_winsorized_chain_phase2_check_passed",
    "stack_engine_publication_publish_preflight_resident_winsorized_ready",
    "stack_engine_publication_phase2_resident_winsorized_ready",
    "stack_engine_publication_resident_winsorized_agreement",
)


def _stack_engine_publication_audit_matches(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    return all(
        left.get(field) == right.get(field)
        for field in _STACK_ENGINE_PUBLICATION_AUDIT_MATCH_FIELDS
    ) and left.get("stack_engine_publication_audit_failed_checks") == right.get(
        "stack_engine_publication_audit_failed_checks"
    )


def build_windows_publish_preflight(
    *,
    release_manifest: str | Path,
    github_release_plan: str | Path,
    windows_release_matrix: str | Path,
    default_promotion_manifest: str | Path,
    require_publication_ready: bool = True,
) -> dict[str, Any]:
    manifest_path = Path(release_manifest)
    plan_path = Path(github_release_plan)
    matrix_path = Path(windows_release_matrix)
    promotion_path = Path(default_promotion_manifest)

    manifest = _read_json_object(manifest_path)
    plan = _read_json_object(plan_path)
    matrix = _read_json_object(matrix_path)
    promotion = _read_json_object(promotion_path)

    manifest_packages = _rows_by_label(manifest.get("packages") or [])
    plan_assets = _rows_by_label(plan.get("assets") or [])
    matrix_info = _matrix_summary(matrix)
    promotion_info = _default_promotion_summary(promotion)
    plan_rejection_sample = _plan_rejection_sample_summary(plan)
    plan_sample_closure = _plan_sample_closure_summary(plan)
    plan_stack_engine = _plan_stack_engine_summary(plan)
    plan_release_direct_publication_guard = (
        _plan_release_direct_publication_guard_summary(plan)
    )
    plan_resident_fastpath_handoff = (
        _plan_resident_fastpath_release_handoff_summary(plan)
    )
    manifest_matrix = (
        manifest.get("windows_release_matrix")
        if isinstance(manifest.get("windows_release_matrix"), dict)
        else {}
    )
    plan_matrix = (
        plan.get("release_matrix") if isinstance(plan.get("release_matrix"), dict) else {}
    )

    manifest_labels = sorted(manifest_packages)
    asset_labels = sorted(plan_assets)
    matrix_labels = sorted(matrix_info["package_labels"])
    missing_assets = [label for label in manifest_labels if label not in plan_assets]
    missing_manifest_rows = [label for label in matrix_labels if label not in manifest_packages]
    mismatched_assets: list[str] = []
    for label, row in manifest_packages.items():
        asset = plan_assets.get(label) or {}
        if (
            asset
            and (
                row.get("sha256") != asset.get("sha256")
                or row.get("size_bytes") != asset.get("size_bytes")
                or not _same_path(row.get("zip_path"), asset.get("zip_path"))
            )
        ):
            mismatched_assets.append(label)

    checks = [
        _check(
            "release_manifest_ready",
            manifest.get("artifact_type") == "windows_release_manifest"
            and manifest.get("status") == "release_manifest_ready"
            and manifest.get("passed") is True,
            {
                "artifact_type": manifest.get("artifact_type"),
                "status": manifest.get("status"),
                "passed": manifest.get("passed"),
            },
        ),
        _check(
            "github_release_plan_ready",
            plan.get("artifact_type") == "windows_github_release_plan"
            and plan.get("status") == "release_plan_ready"
            and plan.get("passed") is True,
            {
                "artifact_type": plan.get("artifact_type"),
                "status": plan.get("status"),
                "passed": plan.get("passed"),
            },
        ),
        _check(
            "github_release_plan_publication_ready",
            plan.get("publication_ready") is True if require_publication_ready else True,
            {
                "publication_ready": plan.get("publication_ready"),
                "required": bool(require_publication_ready),
            },
        ),
        _check(
            "windows_release_matrix_ready",
            matrix_info["artifact_type"] == "windows_release_matrix"
            and matrix_info["status"] == "release_matrix_ready"
            and matrix_info["passed"] is True,
            matrix_info,
        ),
        _check(
            "default_promotion_ready",
            promotion_info["artifact_type"] == "default_promotion_manifest"
            and promotion_info["status"] == "default_promotion_ready"
            and promotion_info["passed"] is True
            and promotion_info["default_change_ready"] is True,
            promotion_info,
        ),
        _check(
            "default_route_contract_passed",
            promotion_info["default_route_passed"] is True
            and promotion_info["default_route_route_contract_passed"] is True
            and int(promotion_info["default_route_route_check_count"] or 0) >= 4,
            {
                "default_route_passed": promotion_info["default_route_passed"],
                "route_contract_passed": promotion_info["default_route_route_contract_passed"],
                "route_check_count": promotion_info["default_route_route_check_count"],
            },
        ),
        _check(
            "manifest_references_matrix",
            _same_path(manifest_matrix.get("path"), matrix_path),
            {"manifest_matrix_path": manifest_matrix.get("path"), "matrix_path": str(matrix_path)},
        ),
        _check(
            "github_plan_references_manifest",
            _same_path(plan.get("manifest_artifact"), manifest_path),
            {
                "plan_manifest_artifact": plan.get("manifest_artifact"),
                "manifest_path": str(manifest_path),
            },
        ),
        _check(
            "github_plan_references_matrix",
            _same_path(plan_matrix.get("path"), matrix_path),
            {"plan_matrix_path": plan_matrix.get("path"), "matrix_path": str(matrix_path)},
        ),
        _check(
            "matrix_default_promotion_matches_manifest",
            matrix_info["default_promotion_status"] == promotion_info["status"]
            and matrix_info["default_promotion_passed"] == promotion_info["passed"]
            and matrix_info["default_promotion_default_change_ready"]
            == promotion_info["default_change_ready"],
            {"matrix": matrix_info, "default_promotion": promotion_info},
        ),
        _check(
            "matrix_default_route_matches_manifest",
            matrix_info["default_route_passed"] == promotion_info["default_route_passed"]
            and matrix_info["default_route_route_contract_passed"]
            == promotion_info["default_route_route_contract_passed"]
            and matrix_info["default_route_route_check_count"]
            == promotion_info["default_route_route_check_count"],
            {"matrix": matrix_info, "default_promotion": promotion_info},
        ),
        _check(
            "github_plan_phase2_rejection_sample_accounting_passed",
            plan_rejection_sample.get("phase2_check_passed") is True
            and plan_rejection_sample.get(
                "phase2_integration_rejection_sample_counts_match_maps"
            )
            is True
            and plan_rejection_sample.get("phase2_rejection_sample_accounting_status")
            == "passed"
            and int(
                plan_rejection_sample.get("phase2_rejection_sample_accounting_failed_count")
                or 0
            )
            == 0,
            {
                "check_passed": plan_rejection_sample.get("phase2_check_passed"),
                "check": plan_rejection_sample.get(
                    "phase2_integration_rejection_sample_counts_match_maps"
                ),
                "status": plan_rejection_sample.get(
                    "phase2_rejection_sample_accounting_status"
                ),
                "failed_count": plan_rejection_sample.get(
                    "phase2_rejection_sample_accounting_failed_count"
                ),
                "plan_check_evidence": plan_rejection_sample.get("phase2_check_evidence"),
            },
        ),
        _check(
            "github_plan_matrix_rejection_sample_accounting_passed",
            plan_rejection_sample.get("release_matrix_check_passed") is True
            and plan_rejection_sample.get(
                "release_matrix_integration_rejection_sample_counts_match_maps"
            )
            is True
            and plan_rejection_sample.get("release_matrix_rejection_sample_accounting_status")
            == "passed"
            and int(
                plan_rejection_sample.get(
                    "release_matrix_rejection_sample_accounting_failed_count"
                )
                or 0
            )
            == 0,
            {
                "check_passed": plan_rejection_sample.get("release_matrix_check_passed"),
                "check": plan_rejection_sample.get(
                    "release_matrix_integration_rejection_sample_counts_match_maps"
                ),
                "status": plan_rejection_sample.get(
                    "release_matrix_rejection_sample_accounting_status"
                ),
                "failed_count": plan_rejection_sample.get(
                    "release_matrix_rejection_sample_accounting_failed_count"
                ),
                "plan_check_evidence": plan_rejection_sample.get(
                    "release_matrix_check_evidence"
                ),
            },
        ),
        _check(
            "matrix_rejection_sample_accounting_passed",
            matrix_info.get("integration_rejection_sample_counts_match_maps") is True
            and matrix_info.get("rejection_sample_accounting_status") == "passed"
            and int(matrix_info.get("rejection_sample_accounting_failed_count") or 0) == 0,
            {
                "check": matrix_info.get("integration_rejection_sample_counts_match_maps"),
                "status": matrix_info.get("rejection_sample_accounting_status"),
                "failed_count": matrix_info.get("rejection_sample_accounting_failed_count"),
            },
        ),
        _check(
            "default_promotion_rejection_sample_accounting_passed",
            promotion_info.get("integration_rejection_sample_counts_match_maps") is True
            and promotion_info.get("rejection_sample_accounting_status") == "passed"
            and int(promotion_info.get("rejection_sample_accounting_failed_count") or 0) == 0,
            {
                "pipeline_contract_status": promotion_info.get("pipeline_contract_status"),
                "pipeline_contract_passed": promotion_info.get("pipeline_contract_passed"),
                "check": promotion_info.get("integration_rejection_sample_counts_match_maps"),
                "status": promotion_info.get("rejection_sample_accounting_status"),
                "failed_count": promotion_info.get("rejection_sample_accounting_failed_count"),
                "failed_items": (
                    promotion_info.get("rejection_sample_accounting") or {}
                ).get("failed_items"),
            },
        ),
        _check(
            "github_plan_matrix_rejection_accounting_matches_matrix",
            plan_rejection_sample.get(
                "release_matrix_integration_rejection_sample_counts_match_maps"
            )
            == matrix_info.get("integration_rejection_sample_counts_match_maps")
            and plan_rejection_sample.get("release_matrix_rejection_sample_accounting_status")
            == matrix_info.get("rejection_sample_accounting_status")
            and plan_rejection_sample.get(
                "release_matrix_rejection_sample_accounting_failed_count"
            )
            == matrix_info.get("rejection_sample_accounting_failed_count"),
            {
                "github_release_plan": {
                    "check": plan_rejection_sample.get(
                        "release_matrix_integration_rejection_sample_counts_match_maps"
                    ),
                    "status": plan_rejection_sample.get(
                        "release_matrix_rejection_sample_accounting_status"
                    ),
                    "failed_count": plan_rejection_sample.get(
                        "release_matrix_rejection_sample_accounting_failed_count"
                    ),
                },
                "windows_release_matrix": {
                    "check": matrix_info.get(
                        "integration_rejection_sample_counts_match_maps"
                    ),
                    "status": matrix_info.get("rejection_sample_accounting_status"),
                    "failed_count": matrix_info.get(
                        "rejection_sample_accounting_failed_count"
                    ),
                },
            },
        ),
        _check(
            "github_plan_phase2_sample_accounting_closure_passed",
            plan_sample_closure.get("phase2_check_passed") is True
            and plan_sample_closure.get("phase2_integration_sample_accounting_closure")
            is True
            and plan_sample_closure.get("phase2_sample_accounting_closure_status")
            == "passed"
            and int(
                plan_sample_closure.get("phase2_sample_accounting_closure_failed_count")
                or 0
            )
            == 0,
            {
                "check_passed": plan_sample_closure.get("phase2_check_passed"),
                "check": plan_sample_closure.get(
                    "phase2_integration_sample_accounting_closure"
                ),
                "status": plan_sample_closure.get(
                    "phase2_sample_accounting_closure_status"
                ),
                "present_count": plan_sample_closure.get(
                    "phase2_sample_accounting_closure_present_count"
                ),
                "failed_count": plan_sample_closure.get(
                    "phase2_sample_accounting_closure_failed_count"
                ),
                "plan_check_evidence": plan_sample_closure.get("phase2_check_evidence"),
            },
        ),
        _check(
            "github_plan_matrix_sample_accounting_closure_passed",
            plan_sample_closure.get("release_matrix_check_passed") is True
            and plan_sample_closure.get(
                "release_matrix_integration_sample_accounting_closure"
            )
            is True
            and plan_sample_closure.get("release_matrix_sample_accounting_closure_status")
            == "passed"
            and int(
                plan_sample_closure.get(
                    "release_matrix_sample_accounting_closure_failed_count"
                )
                or 0
            )
            == 0,
            {
                "check_passed": plan_sample_closure.get("release_matrix_check_passed"),
                "check": plan_sample_closure.get(
                    "release_matrix_integration_sample_accounting_closure"
                ),
                "status": plan_sample_closure.get(
                    "release_matrix_sample_accounting_closure_status"
                ),
                "present_count": plan_sample_closure.get(
                    "release_matrix_sample_accounting_closure_present_count"
                ),
                "failed_count": plan_sample_closure.get(
                    "release_matrix_sample_accounting_closure_failed_count"
                ),
                "plan_check_evidence": plan_sample_closure.get(
                    "release_matrix_check_evidence"
                ),
            },
        ),
        _check(
            "matrix_sample_accounting_closure_passed",
            matrix_info.get("integration_sample_accounting_closure") is True
            and matrix_info.get("sample_accounting_closure_status") == "passed"
            and int(matrix_info.get("sample_accounting_closure_failed_count") or 0) == 0,
            {
                "check": matrix_info.get("integration_sample_accounting_closure"),
                "status": matrix_info.get("sample_accounting_closure_status"),
                "present_count": matrix_info.get("sample_accounting_closure_present_count"),
                "failed_count": matrix_info.get("sample_accounting_closure_failed_count"),
                "failed_items": (matrix_info.get("sample_accounting_closure") or {}).get(
                    "failed_items"
                ),
            },
        ),
        _check(
            "default_promotion_sample_accounting_closure_passed",
            promotion_info.get("integration_sample_accounting_closure") is True
            and promotion_info.get("sample_accounting_closure_status") == "passed"
            and int(promotion_info.get("sample_accounting_closure_failed_count") or 0)
            == 0,
            {
                "pipeline_contract_status": promotion_info.get("pipeline_contract_status"),
                "pipeline_contract_passed": promotion_info.get("pipeline_contract_passed"),
                "check": promotion_info.get("integration_sample_accounting_closure"),
                "status": promotion_info.get("sample_accounting_closure_status"),
                "present_count": promotion_info.get(
                    "sample_accounting_closure_present_count"
                ),
                "failed_count": promotion_info.get(
                    "sample_accounting_closure_failed_count"
                ),
                "failed_items": (
                    promotion_info.get("sample_accounting_closure") or {}
                ).get("failed_items"),
            },
        ),
        _check(
            "github_plan_matrix_sample_closure_matches_matrix",
            plan_sample_closure.get(
                "release_matrix_integration_sample_accounting_closure"
            )
            == matrix_info.get("integration_sample_accounting_closure")
            and plan_sample_closure.get("release_matrix_sample_accounting_closure_status")
            == matrix_info.get("sample_accounting_closure_status")
            and plan_sample_closure.get(
                "release_matrix_sample_accounting_closure_failed_count"
            )
            == matrix_info.get("sample_accounting_closure_failed_count"),
            {
                "github_release_plan": {
                    "check": plan_sample_closure.get(
                        "release_matrix_integration_sample_accounting_closure"
                    ),
                    "status": plan_sample_closure.get(
                        "release_matrix_sample_accounting_closure_status"
                    ),
                    "failed_count": plan_sample_closure.get(
                        "release_matrix_sample_accounting_closure_failed_count"
                    ),
                },
                "windows_release_matrix": {
                    "check": matrix_info.get("integration_sample_accounting_closure"),
                    "status": matrix_info.get("sample_accounting_closure_status"),
                    "failed_count": matrix_info.get(
                        "sample_accounting_closure_failed_count"
                    ),
                },
            },
        ),
        _check(
            "windows_release_matrix_acceptance_integration_engine_policy_passed",
            matrix_info.get("integration_engine_policy_ready") is True
            and _integration_engine_policy_side_passed(matrix_info, "acceptance"),
            {
                "ready": matrix_info.get("integration_engine_policy_ready"),
                **_integration_engine_policy_evidence(matrix_info, "acceptance"),
            },
        ),
        _check(
            "windows_release_matrix_pipeline_integration_engine_policy_passed",
            matrix_info.get("integration_engine_policy_ready") is True
            and _integration_engine_policy_side_passed(matrix_info, "pipeline"),
            {
                "ready": matrix_info.get("integration_engine_policy_ready"),
                **_integration_engine_policy_evidence(matrix_info, "pipeline"),
            },
        ),
        _check(
            "default_promotion_acceptance_integration_engine_policy_passed",
            promotion_info.get("integration_engine_policy_ready") is True
            and _integration_engine_policy_side_passed(promotion_info, "acceptance"),
            {
                "ready": promotion_info.get("integration_engine_policy_ready"),
                **_integration_engine_policy_evidence(promotion_info, "acceptance"),
            },
        ),
        _check(
            "default_promotion_pipeline_integration_engine_policy_passed",
            promotion_info.get("integration_engine_policy_ready") is True
            and _integration_engine_policy_side_passed(promotion_info, "pipeline"),
            {
                "ready": promotion_info.get("integration_engine_policy_ready"),
                **_integration_engine_policy_evidence(promotion_info, "pipeline"),
            },
        ),
        _check(
            "matrix_integration_engine_policy_matches_default_promotion",
            _integration_engine_policy_matches(matrix_info, promotion_info),
            {
                "windows_release_matrix": {
                    "ready": matrix_info.get("integration_engine_policy_ready"),
                    "acceptance": _integration_engine_policy_evidence(
                        matrix_info,
                        "acceptance",
                    ),
                    "pipeline": _integration_engine_policy_evidence(
                        matrix_info,
                        "pipeline",
                    ),
                },
                "default_promotion": {
                    "ready": promotion_info.get("integration_engine_policy_ready"),
                    "acceptance": _integration_engine_policy_evidence(
                        promotion_info,
                        "acceptance",
                    ),
                    "pipeline": _integration_engine_policy_evidence(
                        promotion_info,
                        "pipeline",
                    ),
                },
            },
        ),
        _check(
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
            _stack_engine_runtime_default_side_passed(
                matrix_info,
                "acceptance",
            ),
            {
                "ready": matrix_info.get("stack_engine_runtime_default_ready"),
                **_stack_engine_runtime_default_evidence(
                    matrix_info,
                    "acceptance",
                ),
            },
        ),
        _check(
            "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
            _stack_engine_runtime_default_side_passed(
                matrix_info,
                "pipeline",
            ),
            {
                "ready": matrix_info.get("stack_engine_runtime_default_ready"),
                **_stack_engine_runtime_default_evidence(
                    matrix_info,
                    "pipeline",
                ),
            },
        ),
        _check(
            "default_promotion_acceptance_stack_engine_runtime_default_passed",
            _stack_engine_runtime_default_side_passed(
                promotion_info,
                "acceptance",
            ),
            {
                "ready": promotion_info.get("stack_engine_runtime_default_ready"),
                **_stack_engine_runtime_default_evidence(
                    promotion_info,
                    "acceptance",
                ),
            },
        ),
        _check(
            "default_promotion_pipeline_stack_engine_runtime_default_passed",
            _stack_engine_runtime_default_side_passed(
                promotion_info,
                "pipeline",
            ),
            {
                "ready": promotion_info.get("stack_engine_runtime_default_ready"),
                **_stack_engine_runtime_default_evidence(
                    promotion_info,
                    "pipeline",
                ),
            },
        ),
        _check(
            "matrix_stack_engine_runtime_default_matches_default_promotion",
            _stack_engine_runtime_default_matches(matrix_info, promotion_info),
            {
                "windows_release_matrix": {
                    "ready": matrix_info.get("stack_engine_runtime_default_ready"),
                    "acceptance": _stack_engine_runtime_default_evidence(
                        matrix_info,
                        "acceptance",
                    ),
                    "pipeline": _stack_engine_runtime_default_evidence(
                        matrix_info,
                        "pipeline",
                    ),
                },
                "default_promotion": {
                    "ready": promotion_info.get("stack_engine_runtime_default_ready"),
                    "acceptance": _stack_engine_runtime_default_evidence(
                        promotion_info,
                        "acceptance",
                    ),
                    "pipeline": _stack_engine_runtime_default_evidence(
                        promotion_info,
                        "pipeline",
                    ),
                },
            },
        ),
        _check(
            "windows_release_matrix_direct_acceptance_fastpath_evidence",
            _runtime_default_direct_acceptance_passed(matrix_info),
            _runtime_default_direct_evidence(matrix_info),
        ),
        _check(
            "windows_release_matrix_direct_pipeline_calibration_evidence",
            _runtime_default_direct_pipeline_calibration_passed(matrix_info),
            _runtime_default_direct_evidence(matrix_info),
        ),
        _check(
            "default_promotion_direct_acceptance_fastpath_evidence",
            _runtime_default_direct_acceptance_passed(promotion_info),
            _runtime_default_direct_evidence(promotion_info),
        ),
        _check(
            "default_promotion_direct_pipeline_calibration_evidence",
            _runtime_default_direct_pipeline_calibration_passed(promotion_info),
            _runtime_default_direct_evidence(promotion_info),
        ),
        _check(
            "matrix_direct_runtime_evidence_matches_default_promotion",
            _runtime_default_direct_evidence_matches(matrix_info, promotion_info),
            {
                "windows_release_matrix": _runtime_default_direct_evidence(
                    matrix_info
                ),
                "default_promotion": _runtime_default_direct_evidence(
                    promotion_info
                ),
            },
        ),
        _check(
            "github_plan_matrix_release_decision_direct_publication_guard_passed",
            plan_release_direct_publication_guard.get("release_matrix_check_passed")
            is True
            and plan_release_direct_publication_guard.get("release_matrix_present")
            is True
            and plan_release_direct_publication_guard.get("release_matrix_ready")
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_decision_check_passed"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_source_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_count_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_leaf_checks_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_raw_acceptance_source"
            )
            == "explicit_resident_artifacts_json"
            and plan_release_direct_publication_guard.get(
                "release_matrix_raw_calibration_source"
            )
            == "resident_artifacts_json_fallback"
            and _int_or_zero(
                plan_release_direct_publication_guard.get(
                    "release_matrix_raw_resident_lights"
                )
            )
            >= 200,
            {
                "plan_check_passed": plan_release_direct_publication_guard.get(
                    "release_matrix_check_passed"
                ),
                "plan_check_evidence": plan_release_direct_publication_guard.get(
                    "release_matrix_check_evidence"
                ),
                "present": plan_release_direct_publication_guard.get(
                    "release_matrix_present"
                ),
                "ready": plan_release_direct_publication_guard.get(
                    "release_matrix_ready"
                ),
                "decision_check_passed": plan_release_direct_publication_guard.get(
                    "release_matrix_decision_check_passed"
                ),
                "source_ready": plan_release_direct_publication_guard.get(
                    "release_matrix_source_ready"
                ),
                "count_ready": plan_release_direct_publication_guard.get(
                    "release_matrix_count_ready"
                ),
                "leaf_checks_ready": plan_release_direct_publication_guard.get(
                    "release_matrix_leaf_checks_ready"
                ),
                "acceptance_source": plan_release_direct_publication_guard.get(
                    "release_matrix_raw_acceptance_source"
                ),
                "calibration_source": plan_release_direct_publication_guard.get(
                    "release_matrix_raw_calibration_source"
                ),
                "resident_lights": plan_release_direct_publication_guard.get(
                    "release_matrix_raw_resident_lights"
                ),
            },
        ),
        _check(
            "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed",
            plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_check_passed"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_present"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_decision_check_passed"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_source_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_count_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_leaf_checks_ready"
            )
            is True
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_raw_acceptance_source"
            )
            == "explicit_resident_artifacts_json"
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_raw_calibration_source"
            )
            == "resident_artifacts_json_fallback"
            and _int_or_zero(
                plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_raw_resident_lights"
                )
            )
            >= 200,
            {
                "plan_check_passed": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_check_passed"
                ),
                "plan_check_evidence": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_check_evidence"
                ),
                "present": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_present"
                ),
                "ready": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_ready"
                ),
                "decision_check_passed": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_decision_check_passed"
                ),
                "source_ready": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_source_ready"
                ),
                "count_ready": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_count_ready"
                ),
                "leaf_checks_ready": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_leaf_checks_ready"
                ),
                "acceptance_source": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_raw_acceptance_source"
                ),
                "calibration_source": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_raw_calibration_source"
                ),
                "resident_lights": plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_raw_resident_lights"
                ),
            },
        ),
        _check(
            "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix",
            plan_release_direct_publication_guard.get("release_matrix_present")
            == matrix_info.get(
                "release_decision_direct_runtime_publication_guard_present"
            )
            and plan_release_direct_publication_guard.get("release_matrix_ready")
            == matrix_info.get(
                "release_decision_direct_runtime_publication_guard_ready"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_decision_check_passed"
            )
            == matrix_info.get(
                "release_decision_direct_runtime_publication_guard_check_passed"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_raw_acceptance_source"
            )
            == matrix_info.get(
                "release_decision_direct_runtime_publication_guard_raw_acceptance_source"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_raw_calibration_source"
            )
            == matrix_info.get(
                "release_decision_direct_runtime_publication_guard_raw_calibration_source"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_raw_resident_lights"
            )
            == matrix_info.get(
                "release_decision_direct_runtime_publication_guard_raw_resident_lights"
            ),
            {
                "github_release_plan": plan_release_direct_publication_guard,
                "windows_release_matrix": _release_direct_publication_guard_evidence(
                    matrix_info,
                    prefix="release_decision_direct_runtime_publication_guard",
                ),
            },
        ),
        _check(
            "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix",
            plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_present"
            )
            == matrix_info.get(
                "default_promotion_release_decision_direct_runtime_publication_guard_present"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_ready"
            )
            == matrix_info.get(
                "default_promotion_release_decision_direct_runtime_publication_guard_ready"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_decision_check_passed"
            )
            == matrix_info.get(
                "default_promotion_release_decision_direct_runtime_publication_guard_check_passed"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_raw_acceptance_source"
            )
            == matrix_info.get(
                "default_promotion_release_decision_direct_runtime_publication_guard_raw_acceptance_source"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_raw_calibration_source"
            )
            == matrix_info.get(
                "default_promotion_release_decision_direct_runtime_publication_guard_raw_calibration_source"
            )
            and plan_release_direct_publication_guard.get(
                "release_matrix_default_promotion_raw_resident_lights"
            )
            == matrix_info.get(
                "default_promotion_release_decision_direct_runtime_publication_guard_raw_resident_lights"
            ),
            {
                "github_release_plan": plan_release_direct_publication_guard,
                "windows_release_matrix": _release_direct_publication_guard_evidence(
                    matrix_info,
                    prefix=(
                        "default_promotion_release_decision_direct_runtime_publication_guard"
                    ),
                ),
            },
        ),
        _check(
            "matrix_release_decision_direct_runtime_publication_guard_passed",
            _release_direct_publication_guard_passed(
                matrix_info,
                prefix="release_decision_direct_runtime_publication_guard",
            ),
            _release_direct_publication_guard_evidence(
                matrix_info,
                prefix="release_decision_direct_runtime_publication_guard",
            ),
        ),
        _check(
            "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed",
            _release_direct_publication_guard_passed(
                matrix_info,
                prefix=(
                    "default_promotion_release_decision_direct_runtime_publication_guard"
                ),
            ),
            _release_direct_publication_guard_evidence(
                matrix_info,
                prefix=(
                    "default_promotion_release_decision_direct_runtime_publication_guard"
                ),
            ),
        ),
        _check(
            "default_promotion_release_decision_direct_runtime_publication_guard_passed",
            _release_direct_publication_guard_passed(
                promotion_info,
                prefix="release_decision_direct_runtime_publication_guard",
            ),
            _release_direct_publication_guard_evidence(
                promotion_info,
                prefix="release_decision_direct_runtime_publication_guard",
            ),
        ),
        _check(
            "matrix_release_decision_direct_publication_guard_matches_default_promotion",
            _release_direct_publication_guard_matches(
                matrix_info,
                left_prefix="release_decision_direct_runtime_publication_guard",
                right=promotion_info,
                right_prefix="release_decision_direct_runtime_publication_guard",
            ),
            {
                "windows_release_matrix": _release_direct_publication_guard_evidence(
                    matrix_info,
                    prefix="release_decision_direct_runtime_publication_guard",
                ),
                "default_promotion": _release_direct_publication_guard_evidence(
                    promotion_info,
                    prefix="release_decision_direct_runtime_publication_guard",
                ),
            },
        ),
        _check(
            "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest",
            _release_direct_publication_guard_matches(
                matrix_info,
                left_prefix=(
                    "default_promotion_release_decision_direct_runtime_publication_guard"
                ),
                right=promotion_info,
                right_prefix="release_decision_direct_runtime_publication_guard",
            ),
            {
                "windows_release_matrix_default_promotion": (
                    _release_direct_publication_guard_evidence(
                        matrix_info,
                        prefix=(
                            "default_promotion_release_decision_direct_runtime_publication_guard"
                        ),
                    )
                ),
                "default_promotion_manifest": (
                    _release_direct_publication_guard_evidence(
                        promotion_info,
                        prefix="release_decision_direct_runtime_publication_guard",
                    )
                ),
            },
        ),
        _check(
            "github_plan_matrix_resident_fastpath_release_handoff_ready",
            plan_resident_fastpath_handoff.get("release_matrix_check_passed") is True
            and _resident_fastpath_release_handoff_ready(
                plan_resident_fastpath_handoff,
                prefix="release_matrix",
            ),
            {
                "check_passed": plan_resident_fastpath_handoff.get(
                    "release_matrix_check_passed"
                ),
                "ready": plan_resident_fastpath_handoff.get(
                    "release_matrix_ready"
                ),
                "raw_ready": plan_resident_fastpath_handoff.get(
                    "release_matrix_raw_ready"
                ),
                "phase2_ready": plan_resident_fastpath_handoff.get(
                    "release_matrix_phase2_ready"
                ),
                "agreement": plan_resident_fastpath_handoff.get(
                    "release_matrix_agreement"
                ),
                "raw_status": plan_resident_fastpath_handoff.get(
                    "release_matrix_raw_status"
                ),
                "phase2_status": plan_resident_fastpath_handoff.get(
                    "release_matrix_phase2_status"
                ),
                "raw_passed_check_count": plan_resident_fastpath_handoff.get(
                    "release_matrix_raw_passed_check_count"
                ),
                "phase2_passed_check_count": plan_resident_fastpath_handoff.get(
                    "release_matrix_phase2_passed_check_count"
                ),
                "raw_failed_check_count": plan_resident_fastpath_handoff.get(
                    "release_matrix_raw_failed_check_count"
                ),
                "phase2_failed_check_count": plan_resident_fastpath_handoff.get(
                    "release_matrix_phase2_failed_check_count"
                ),
                "plan_check_evidence": plan_resident_fastpath_handoff.get(
                    "release_matrix_check_evidence"
                ),
            },
        ),
        _check(
            "matrix_resident_fastpath_release_handoff_ready",
            _resident_fastpath_release_handoff_ready(
                matrix_info,
                prefix="resident_registration_fastpath_release_handoff",
            ),
            _resident_fastpath_release_handoff_evidence(
                matrix_info,
                prefix="resident_registration_fastpath_release_handoff",
            ),
        ),
        _check(
            "default_promotion_resident_fastpath_release_handoff_ready",
            _resident_fastpath_release_handoff_ready(
                promotion_info,
                prefix="resident_registration_fastpath_release_handoff",
            ),
            _resident_fastpath_release_handoff_evidence(
                promotion_info,
                prefix="resident_registration_fastpath_release_handoff",
            ),
        ),
        _check(
            "github_plan_matrix_resident_fastpath_handoff_matches_matrix",
            _resident_fastpath_release_handoff_matches(
                plan_resident_fastpath_handoff,
                left_prefix="release_matrix",
                right=matrix_info,
                right_prefix="resident_registration_fastpath_release_handoff",
            ),
            {
                "github_release_plan": _resident_fastpath_release_handoff_evidence(
                    plan_resident_fastpath_handoff,
                    prefix="release_matrix",
                ),
                "windows_release_matrix": _resident_fastpath_release_handoff_evidence(
                    matrix_info,
                    prefix="resident_registration_fastpath_release_handoff",
                ),
            },
        ),
        _check(
            "matrix_resident_fastpath_handoff_matches_default_promotion",
            _resident_fastpath_release_handoff_matches(
                matrix_info,
                left_prefix="resident_registration_fastpath_release_handoff",
                right=promotion_info,
                right_prefix="resident_registration_fastpath_release_handoff",
            ),
            {
                "windows_release_matrix": _resident_fastpath_release_handoff_evidence(
                    matrix_info,
                    prefix="resident_registration_fastpath_release_handoff",
                ),
                "default_promotion_manifest": (
                    _resident_fastpath_release_handoff_evidence(
                        promotion_info,
                        prefix="resident_registration_fastpath_release_handoff",
                    )
                ),
            },
        ),
        _check(
            "github_plan_phase2_stack_engine_default_contract_ready",
            _stack_engine_plan_phase2_ready(plan_stack_engine),
            {
                "check_passed": plan_stack_engine.get("phase2_check_passed"),
                "status": plan_stack_engine.get("phase2_status"),
                "phase2_check_passed": plan_stack_engine.get(
                    "phase2_phase2_check_passed"
                ),
                "passed": plan_stack_engine.get("phase2_passed"),
                "scope": plan_stack_engine.get("phase2_scope"),
                "adoption_recommendation": plan_stack_engine.get(
                    "phase2_adoption_recommendation"
                ),
                "default_promotion_recommendation": plan_stack_engine.get(
                    "phase2_default_promotion_recommendation"
                ),
                "default_gap_count": plan_stack_engine.get("phase2_default_gap_count"),
                "blocker_count": plan_stack_engine.get("phase2_blocker_count"),
                "blockers": plan_stack_engine.get("phase2_blockers"),
                "plan_check_evidence": plan_stack_engine.get("phase2_check_evidence"),
            },
        ),
        _check(
            "github_plan_matrix_stack_engine_contract_ready",
            _stack_engine_plan_matrix_ready(plan_stack_engine),
            {
                "check_passed": plan_stack_engine.get("release_matrix_check_passed"),
                "ready": plan_stack_engine.get("release_matrix_ready"),
                "phase2_check_passed": plan_stack_engine.get(
                    "release_matrix_phase2_check_passed"
                ),
                "status": plan_stack_engine.get("release_matrix_status"),
                "passed": plan_stack_engine.get("release_matrix_passed"),
                "scope": plan_stack_engine.get("release_matrix_scope"),
                "adoption_recommendation": plan_stack_engine.get(
                    "release_matrix_adoption_recommendation"
                ),
                "default_gap_count": plan_stack_engine.get(
                    "release_matrix_default_gap_count"
                ),
                "blocker_count": plan_stack_engine.get("release_matrix_blocker_count"),
                "blockers": plan_stack_engine.get("release_matrix_blockers"),
                "plan_check_evidence": plan_stack_engine.get(
                    "release_matrix_check_evidence"
                ),
            },
        ),
        _check(
            "github_plan_stack_engine_contract_agreement_passed",
            plan_stack_engine.get("agreement_check_passed") is True
            and _int_or_zero(plan_stack_engine.get("phase2_default_gap_count")) == 0
            and _int_or_zero(plan_stack_engine.get("release_matrix_default_gap_count")) == 0
            and _int_or_zero(plan_stack_engine.get("phase2_blocker_count")) == 0
            and _int_or_zero(plan_stack_engine.get("release_matrix_blocker_count")) == 0,
            {
                "agreement_check_passed": plan_stack_engine.get(
                    "agreement_check_passed"
                ),
                "phase2_gap_count": plan_stack_engine.get("phase2_default_gap_count"),
                "matrix_gap_count": plan_stack_engine.get(
                    "release_matrix_default_gap_count"
                ),
                "phase2_blocker_count": plan_stack_engine.get("phase2_blocker_count"),
                "matrix_blocker_count": plan_stack_engine.get(
                    "release_matrix_blocker_count"
                ),
                "plan_check_evidence": plan_stack_engine.get(
                    "agreement_check_evidence"
                ),
            },
        ),
        _check(
            "matrix_stack_engine_contract_ready",
            _stack_engine_matrix_ready(matrix_info),
            {
                "present": matrix_info.get("stack_engine_contract_present"),
                "ready": matrix_info.get("stack_engine_contract_ready"),
                "phase2_check_passed": matrix_info.get(
                    "stack_engine_contract_phase2_check_passed"
                ),
                "status": matrix_info.get("stack_engine_contract_status"),
                "passed": matrix_info.get("stack_engine_contract_passed"),
                "scope": matrix_info.get("stack_engine_contract_scope"),
                "adoption_recommendation": matrix_info.get(
                    "stack_engine_contract_adoption_recommendation"
                ),
                "default_gap_count": matrix_info.get(
                    "stack_engine_contract_default_gap_count"
                ),
                "blocker_count": matrix_info.get("stack_engine_contract_blocker_count"),
                "blockers": matrix_info.get("stack_engine_contract_blockers"),
            },
        ),
        _check(
            "default_promotion_stack_engine_contract_ready",
            _stack_engine_matrix_ready(promotion_info),
            {
                "present": promotion_info.get("stack_engine_contract_present"),
                "ready": promotion_info.get("stack_engine_contract_ready"),
                "phase2_check_passed": promotion_info.get(
                    "stack_engine_contract_phase2_check_passed"
                ),
                "status": promotion_info.get("stack_engine_contract_status"),
                "passed": promotion_info.get("stack_engine_contract_passed"),
                "scope": promotion_info.get("stack_engine_contract_scope"),
                "adoption_recommendation": promotion_info.get(
                    "stack_engine_contract_adoption_recommendation"
                ),
                "default_gap_count": promotion_info.get(
                    "stack_engine_contract_default_gap_count"
                ),
                "blocker_count": promotion_info.get(
                    "stack_engine_contract_blocker_count"
                ),
                "blockers": promotion_info.get("stack_engine_contract_blockers"),
            },
        ),
        _check(
            "github_plan_matrix_stack_engine_contract_matches_matrix",
            plan_stack_engine.get("release_matrix_ready")
            == matrix_info.get("stack_engine_contract_ready")
            and plan_stack_engine.get("release_matrix_phase2_check_passed")
            == matrix_info.get("stack_engine_contract_phase2_check_passed")
            and plan_stack_engine.get("release_matrix_status")
            == matrix_info.get("stack_engine_contract_status")
            and plan_stack_engine.get("release_matrix_default_gap_count")
            == matrix_info.get("stack_engine_contract_default_gap_count")
            and plan_stack_engine.get("release_matrix_blocker_count")
            == matrix_info.get("stack_engine_contract_blocker_count"),
            {
                "github_release_plan": {
                    "ready": plan_stack_engine.get("release_matrix_ready"),
                    "phase2_check_passed": plan_stack_engine.get(
                        "release_matrix_phase2_check_passed"
                    ),
                    "status": plan_stack_engine.get("release_matrix_status"),
                    "default_gap_count": plan_stack_engine.get(
                        "release_matrix_default_gap_count"
                    ),
                    "blocker_count": plan_stack_engine.get(
                        "release_matrix_blocker_count"
                    ),
                },
                "windows_release_matrix": {
                    "ready": matrix_info.get("stack_engine_contract_ready"),
                    "phase2_check_passed": matrix_info.get(
                        "stack_engine_contract_phase2_check_passed"
                    ),
                    "status": matrix_info.get("stack_engine_contract_status"),
                    "default_gap_count": matrix_info.get(
                        "stack_engine_contract_default_gap_count"
                    ),
                    "blocker_count": matrix_info.get(
                        "stack_engine_contract_blocker_count"
                    ),
                },
            },
        ),
        _check(
            "matrix_stack_engine_contract_matches_default_promotion",
            matrix_info.get("stack_engine_contract_ready")
            == promotion_info.get("stack_engine_contract_ready")
            and matrix_info.get("stack_engine_contract_phase2_check_passed")
            == promotion_info.get("stack_engine_contract_phase2_check_passed")
            and matrix_info.get("stack_engine_contract_status")
            == promotion_info.get("stack_engine_contract_status")
            and matrix_info.get("stack_engine_contract_default_gap_count")
            == promotion_info.get("stack_engine_contract_default_gap_count")
            and matrix_info.get("stack_engine_contract_blocker_count")
            == promotion_info.get("stack_engine_contract_blocker_count"),
            {
                "windows_release_matrix": {
                    "ready": matrix_info.get("stack_engine_contract_ready"),
                    "phase2_check_passed": matrix_info.get(
                        "stack_engine_contract_phase2_check_passed"
                    ),
                    "status": matrix_info.get("stack_engine_contract_status"),
                    "default_gap_count": matrix_info.get(
                        "stack_engine_contract_default_gap_count"
                    ),
                    "blocker_count": matrix_info.get(
                        "stack_engine_contract_blocker_count"
                    ),
                },
                "default_promotion": {
                    "ready": promotion_info.get("stack_engine_contract_ready"),
                    "phase2_check_passed": promotion_info.get(
                        "stack_engine_contract_phase2_check_passed"
                    ),
                    "status": promotion_info.get("stack_engine_contract_status"),
                    "default_gap_count": promotion_info.get(
                        "stack_engine_contract_default_gap_count"
                    ),
                    "blocker_count": promotion_info.get(
                        "stack_engine_contract_blocker_count"
                    ),
                },
            },
        ),
        _check(
            "matrix_resident_winsorized_sweep_audit_passed",
            _resident_winsorized_sweep_audit_passed(matrix_info),
            _resident_winsorized_sweep_evidence(matrix_info),
        ),
        _check(
            "matrix_resident_winsorized_required_frame_passed",
            _resident_winsorized_required_frame_passed(matrix_info),
            {
                "required_frame_count": matrix_info.get(
                    "resident_winsorized_sweep_required_frame_count"
                ),
                "required_frame_count_passed": matrix_info.get(
                    "resident_winsorized_sweep_required_frame_count_passed"
                ),
                "required_frame_master_rms": matrix_info.get(
                    "resident_winsorized_sweep_required_frame_master_rms"
                ),
                "required_frame_master_max_abs": matrix_info.get(
                    "resident_winsorized_sweep_required_frame_master_max_abs"
                ),
                "required_frame_cuda_hardened_s": matrix_info.get(
                    "resident_winsorized_sweep_required_frame_cuda_hardened_s"
                ),
            },
        ),
        _check(
            "matrix_resident_winsorized_sweep_check_count",
            _resident_winsorized_check_count_ready(matrix_info),
            {
                "check_count": matrix_info.get(
                    "resident_winsorized_sweep_check_count"
                ),
                "failed_check_count": matrix_info.get(
                    "resident_winsorized_sweep_failed_check_count"
                ),
            },
        ),
        _check(
            "default_promotion_resident_winsorized_sweep_audit_passed",
            _resident_winsorized_sweep_audit_passed(promotion_info),
            _resident_winsorized_sweep_evidence(promotion_info),
        ),
        _check(
            "default_promotion_resident_winsorized_required_frame_passed",
            _resident_winsorized_required_frame_passed(promotion_info),
            {
                "required_frame_count": promotion_info.get(
                    "resident_winsorized_sweep_required_frame_count"
                ),
                "required_frame_count_passed": promotion_info.get(
                    "resident_winsorized_sweep_required_frame_count_passed"
                ),
                "required_frame_master_rms": promotion_info.get(
                    "resident_winsorized_sweep_required_frame_master_rms"
                ),
                "required_frame_master_max_abs": promotion_info.get(
                    "resident_winsorized_sweep_required_frame_master_max_abs"
                ),
                "required_frame_cuda_hardened_s": promotion_info.get(
                    "resident_winsorized_sweep_required_frame_cuda_hardened_s"
                ),
            },
        ),
        _check(
            "default_promotion_resident_winsorized_sweep_matches_matrix",
            matrix_info.get("resident_winsorized_sweep_present")
            == promotion_info.get("resident_winsorized_sweep_present")
            and matrix_info.get("resident_winsorized_sweep_status")
            == promotion_info.get("resident_winsorized_sweep_status")
            and matrix_info.get("resident_winsorized_sweep_passed")
            == promotion_info.get("resident_winsorized_sweep_passed")
            and matrix_info.get("resident_winsorized_sweep_phase2_check_passed")
            == promotion_info.get("resident_winsorized_sweep_phase2_check_passed")
            and matrix_info.get("resident_winsorized_sweep_check_count")
            == promotion_info.get("resident_winsorized_sweep_check_count")
            and matrix_info.get("resident_winsorized_sweep_failed_check_count")
            == promotion_info.get("resident_winsorized_sweep_failed_check_count")
            and matrix_info.get("resident_winsorized_sweep_required_frame_count")
            == promotion_info.get("resident_winsorized_sweep_required_frame_count")
            and matrix_info.get(
                "resident_winsorized_sweep_required_frame_count_passed"
            )
            == promotion_info.get(
                "resident_winsorized_sweep_required_frame_count_passed"
            ),
            {
                "windows_release_matrix": _resident_winsorized_sweep_evidence(
                    matrix_info
                ),
                "default_promotion": _resident_winsorized_sweep_evidence(
                    promotion_info
                ),
            },
        ),
        _check(
            "matrix_stack_engine_publication_audit_passed",
            _stack_engine_publication_audit_passed(matrix_info),
            _stack_engine_publication_audit_evidence(matrix_info),
        ),
        _check(
            "matrix_stack_engine_publication_policy_chain_passed",
            _stack_engine_publication_policy_chain_passed(matrix_info),
            _stack_engine_publication_policy_chain_evidence(matrix_info),
        ),
        _check(
            "matrix_stack_engine_publication_resident_winsorized_chain_passed",
            _stack_engine_publication_resident_winsorized_chain_passed(matrix_info),
            _stack_engine_publication_resident_winsorized_chain_evidence(matrix_info),
        ),
        _check(
            "default_promotion_stack_engine_publication_audit_passed",
            _stack_engine_publication_audit_passed(promotion_info),
            _stack_engine_publication_audit_evidence(promotion_info),
        ),
        _check(
            "default_promotion_stack_engine_publication_policy_chain_passed",
            _stack_engine_publication_policy_chain_passed(promotion_info),
            _stack_engine_publication_policy_chain_evidence(promotion_info),
        ),
        _check(
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
            _stack_engine_publication_resident_winsorized_chain_passed(
                promotion_info
            ),
            _stack_engine_publication_resident_winsorized_chain_evidence(
                promotion_info
            ),
        ),
        _check(
            "matrix_stack_engine_publication_audit_matches_default_promotion",
            _stack_engine_publication_audit_matches(matrix_info, promotion_info),
            {
                "windows_release_matrix": {
                    "audit": _stack_engine_publication_audit_evidence(matrix_info),
                    "policy_chain": (
                        _stack_engine_publication_policy_chain_evidence(matrix_info)
                    ),
                    "resident_winsorized_chain": (
                        _stack_engine_publication_resident_winsorized_chain_evidence(
                            matrix_info
                        )
                    ),
                },
                "default_promotion": {
                    "audit": _stack_engine_publication_audit_evidence(
                        promotion_info
                    ),
                    "policy_chain": (
                        _stack_engine_publication_policy_chain_evidence(
                            promotion_info
                        )
                    ),
                    "resident_winsorized_chain": (
                        _stack_engine_publication_resident_winsorized_chain_evidence(
                            promotion_info
                        )
                    ),
                },
            },
        ),
        _check(
            "manifest_assets_match_github_plan",
            not missing_assets and not mismatched_assets,
            {
                "manifest_labels": manifest_labels,
                "asset_labels": asset_labels,
                "missing_assets": missing_assets,
                "mismatched_assets": mismatched_assets,
            },
        ),
        _check(
            "matrix_packages_match_manifest",
            matrix_labels == manifest_labels and not missing_manifest_rows,
            {
                "matrix_labels": matrix_labels,
                "manifest_labels": manifest_labels,
                "missing_manifest_rows": missing_manifest_rows,
            },
        ),
        _check(
            "cpu_fallback_preserved",
            "cpu" in matrix_info["ordered_try_list"]
            and "cpu" in manifest_packages
            and "cpu" in plan_assets,
            {
                "ordered_try_list": matrix_info["ordered_try_list"],
                "manifest_labels": manifest_labels,
                "asset_labels": asset_labels,
            },
        ),
    ]
    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "windows_publish_preflight",
        "created_at": now_iso(),
        "status": "publish_preflight_ready" if not failed else "blocked",
        "passed": not failed,
        "recommendation": "publish_release_bundle" if not failed else "fix_publish_preflight_blockers",
        "inputs": {
            "release_manifest": str(manifest_path),
            "github_release_plan": str(plan_path),
            "windows_release_matrix": str(matrix_path),
            "default_promotion_manifest": str(promotion_path),
        },
        "requirements": {
            "require_publication_ready": bool(require_publication_ready),
        },
        "summary": {
            "release_tag": (plan.get("release") or {}).get("tag")
            if isinstance(plan.get("release"), dict)
            else None,
            "asset_count": len(plan_assets),
            "package_count": len(manifest_packages),
            "primary_package": matrix_info["primary_package"],
            "ordered_try_list": matrix_info["ordered_try_list"],
            "source_stamps": manifest.get("source_stamps") or [],
            "default_promotion_status": promotion_info["status"],
            "default_route_check_count": promotion_info["default_route_route_check_count"],
            "default_route_speedup_vs_reference": promotion_info[
                "default_route_speedup_vs_reference"
            ],
            "github_plan_phase2_rejection_sample_accounting_status": (
                plan_rejection_sample.get("phase2_rejection_sample_accounting_status")
            ),
            "github_plan_matrix_rejection_sample_accounting_status": (
                plan_rejection_sample.get("release_matrix_rejection_sample_accounting_status")
            ),
            "matrix_rejection_sample_accounting_status": matrix_info.get(
                "rejection_sample_accounting_status"
            ),
            "default_promotion_rejection_sample_accounting_status": promotion_info.get(
                "rejection_sample_accounting_status"
            ),
            "github_plan_phase2_sample_accounting_closure_status": (
                plan_sample_closure.get("phase2_sample_accounting_closure_status")
            ),
            "github_plan_matrix_sample_accounting_closure_status": (
                plan_sample_closure.get("release_matrix_sample_accounting_closure_status")
            ),
            "matrix_sample_accounting_closure_status": matrix_info.get(
                "sample_accounting_closure_status"
            ),
            "default_promotion_sample_accounting_closure_status": promotion_info.get(
                "sample_accounting_closure_status"
            ),
            "matrix_integration_engine_policy_ready": matrix_info.get(
                "integration_engine_policy_ready"
            ),
            "matrix_acceptance_integration_engine_policy_status": matrix_info.get(
                "acceptance_integration_engine_policy_status"
            ),
            "matrix_pipeline_integration_engine_policy_status": matrix_info.get(
                "pipeline_integration_engine_policy_status"
            ),
            "default_promotion_integration_engine_policy_ready": promotion_info.get(
                "integration_engine_policy_ready"
            ),
            "default_promotion_acceptance_integration_engine_policy_status": (
                promotion_info.get("acceptance_integration_engine_policy_status")
            ),
            "default_promotion_pipeline_integration_engine_policy_status": (
                promotion_info.get("pipeline_integration_engine_policy_status")
            ),
            "matrix_stack_engine_runtime_default_ready": matrix_info.get(
                "stack_engine_runtime_default_ready"
            ),
            "matrix_acceptance_stack_engine_runtime_default_status": matrix_info.get(
                "acceptance_stack_engine_runtime_default_status"
            ),
            "matrix_pipeline_stack_engine_runtime_default_status": matrix_info.get(
                "pipeline_stack_engine_runtime_default_status"
            ),
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count": (
                matrix_info.get(
                    "acceptance_stack_engine_runtime_default_legacy_master_count"
                )
            ),
            "matrix_stack_engine_runtime_default_pipeline_failed_output_count": (
                matrix_info.get(
                    "pipeline_stack_engine_runtime_default_failed_output_count"
                )
            ),
            "default_promotion_stack_engine_runtime_default_ready": (
                promotion_info.get("stack_engine_runtime_default_ready")
            ),
            "default_promotion_acceptance_stack_engine_runtime_default_status": (
                promotion_info.get("acceptance_stack_engine_runtime_default_status")
            ),
            "default_promotion_pipeline_stack_engine_runtime_default_status": (
                promotion_info.get("pipeline_stack_engine_runtime_default_status")
            ),
            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count": (
                promotion_info.get(
                    "acceptance_stack_engine_runtime_default_legacy_master_count"
                )
            ),
            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count": (
                promotion_info.get(
                    "pipeline_stack_engine_runtime_default_failed_output_count"
                )
            ),
            "matrix_direct_runtime_evidence_ready": matrix_info.get(
                "runtime_default_direct_evidence_ready"
            ),
            "matrix_direct_runtime_acceptance_source": matrix_info.get(
                "runtime_default_direct_acceptance_fastpath_source"
            ),
            "matrix_direct_runtime_acceptance_check_count": matrix_info.get(
                "runtime_default_direct_acceptance_fastpath_check_count"
            ),
            "matrix_direct_runtime_pipeline_calibration_source": matrix_info.get(
                "runtime_default_direct_pipeline_calibration_source"
            ),
            "matrix_direct_runtime_pipeline_resident_lights": matrix_info.get(
                "runtime_default_direct_pipeline_resident_calibrated_light_count"
            ),
            "default_promotion_direct_runtime_evidence_ready": promotion_info.get(
                "runtime_default_direct_evidence_ready"
            ),
            "default_promotion_direct_runtime_acceptance_source": promotion_info.get(
                "runtime_default_direct_acceptance_fastpath_source"
            ),
            "default_promotion_direct_runtime_acceptance_check_count": (
                promotion_info.get(
                    "runtime_default_direct_acceptance_fastpath_check_count"
                )
            ),
            "default_promotion_direct_runtime_pipeline_calibration_source": (
                promotion_info.get("runtime_default_direct_pipeline_calibration_source")
            ),
            "default_promotion_direct_runtime_pipeline_resident_lights": (
                promotion_info.get(
                    "runtime_default_direct_pipeline_resident_calibrated_light_count"
                )
            ),
            "github_plan_matrix_release_direct_publication_guard_ready": (
                plan_release_direct_publication_guard.get("release_matrix_ready")
            ),
            "github_plan_matrix_release_direct_publication_guard_lights": (
                plan_release_direct_publication_guard.get(
                    "release_matrix_raw_resident_lights"
                )
            ),
            "github_plan_matrix_default_promotion_release_direct_publication_guard_ready": (
                plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_ready"
                )
            ),
            "github_plan_matrix_default_promotion_release_direct_publication_guard_lights": (
                plan_release_direct_publication_guard.get(
                    "release_matrix_default_promotion_raw_resident_lights"
                )
            ),
            "matrix_release_direct_publication_guard_ready": matrix_info.get(
                "release_decision_direct_runtime_publication_guard_ready"
            ),
            "matrix_release_direct_publication_guard_check_passed": matrix_info.get(
                "release_decision_direct_runtime_publication_guard_check_passed"
            ),
            "matrix_release_direct_publication_guard_source_ready": matrix_info.get(
                "release_decision_direct_runtime_publication_guard_source_ready"
            ),
            "matrix_release_direct_publication_guard_count_ready": matrix_info.get(
                "release_decision_direct_runtime_publication_guard_count_ready"
            ),
            "matrix_release_direct_publication_guard_lights": matrix_info.get(
                "release_decision_direct_runtime_publication_guard_raw_resident_lights"
            ),
            "matrix_default_promotion_release_direct_publication_guard_ready": (
                matrix_info.get(
                    "default_promotion_release_decision_direct_runtime_publication_guard_ready"
                )
            ),
            "matrix_default_promotion_release_direct_publication_guard_lights": (
                matrix_info.get(
                    "default_promotion_release_decision_direct_runtime_publication_guard_raw_resident_lights"
                )
            ),
            "default_promotion_release_direct_publication_guard_ready": (
                promotion_info.get(
                    "release_decision_direct_runtime_publication_guard_ready"
                )
            ),
            "default_promotion_release_direct_publication_guard_lights": (
                promotion_info.get(
                    "release_decision_direct_runtime_publication_guard_raw_resident_lights"
                )
            ),
            "github_plan_matrix_resident_fastpath_handoff_ready": (
                plan_resident_fastpath_handoff.get("release_matrix_ready")
            ),
            "github_plan_matrix_resident_fastpath_handoff_raw_status": (
                plan_resident_fastpath_handoff.get("release_matrix_raw_status")
            ),
            "github_plan_matrix_resident_fastpath_handoff_phase2_status": (
                plan_resident_fastpath_handoff.get("release_matrix_phase2_status")
            ),
            "github_plan_matrix_resident_fastpath_handoff_raw_check_count": (
                plan_resident_fastpath_handoff.get(
                    "release_matrix_raw_passed_check_count"
                )
            ),
            "matrix_resident_fastpath_handoff_ready": matrix_info.get(
                "resident_registration_fastpath_release_handoff_ready"
            ),
            "matrix_resident_fastpath_handoff_raw_status": matrix_info.get(
                "resident_registration_fastpath_release_handoff_raw_status"
            ),
            "matrix_resident_fastpath_handoff_phase2_status": matrix_info.get(
                "resident_registration_fastpath_release_handoff_phase2_status"
            ),
            "matrix_resident_fastpath_handoff_raw_check_count": matrix_info.get(
                "resident_registration_fastpath_release_handoff_raw_passed_check_count"
            ),
            "default_promotion_resident_fastpath_handoff_ready": promotion_info.get(
                "resident_registration_fastpath_release_handoff_ready"
            ),
            "default_promotion_resident_fastpath_handoff_raw_status": (
                promotion_info.get(
                    "resident_registration_fastpath_release_handoff_raw_status"
                )
            ),
            "default_promotion_resident_fastpath_handoff_phase2_status": (
                promotion_info.get(
                    "resident_registration_fastpath_release_handoff_phase2_status"
                )
            ),
            "default_promotion_resident_fastpath_handoff_raw_check_count": (
                promotion_info.get(
                    "resident_registration_fastpath_release_handoff_raw_passed_check_count"
                )
            ),
            "github_plan_phase2_stack_engine_contract_status": (
                plan_stack_engine.get("phase2_status")
            ),
            "github_plan_matrix_stack_engine_contract_status": (
                plan_stack_engine.get("release_matrix_status")
            ),
            "matrix_stack_engine_contract_status": matrix_info.get(
                "stack_engine_contract_status"
            ),
            "default_promotion_stack_engine_contract_status": promotion_info.get(
                "stack_engine_contract_status"
            ),
            "matrix_stack_engine_contract_default_gap_count": matrix_info.get(
                "stack_engine_contract_default_gap_count"
            ),
            "default_promotion_stack_engine_contract_default_gap_count": (
                promotion_info.get("stack_engine_contract_default_gap_count")
            ),
            "matrix_resident_winsorized_sweep_status": matrix_info.get(
                "resident_winsorized_sweep_status"
            ),
            "matrix_resident_winsorized_sweep_required_frame_count": matrix_info.get(
                "resident_winsorized_sweep_required_frame_count"
            ),
            "matrix_resident_winsorized_sweep_required_frame_count_passed": (
                matrix_info.get(
                    "resident_winsorized_sweep_required_frame_count_passed"
                )
            ),
            "matrix_resident_winsorized_sweep_check_count": matrix_info.get(
                "resident_winsorized_sweep_check_count"
            ),
            "default_promotion_resident_winsorized_sweep_status": promotion_info.get(
                "resident_winsorized_sweep_status"
            ),
            "default_promotion_resident_winsorized_sweep_required_frame_count": (
                promotion_info.get("resident_winsorized_sweep_required_frame_count")
            ),
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
                promotion_info.get(
                    "resident_winsorized_sweep_required_frame_count_passed"
                )
            ),
            "default_promotion_resident_winsorized_sweep_check_count": (
                promotion_info.get("resident_winsorized_sweep_check_count")
            ),
            "matrix_stack_engine_publication_audit_status": matrix_info.get(
                "stack_engine_publication_audit_status"
            ),
            "matrix_stack_engine_publication_audit_ready": matrix_info.get(
                "stack_engine_publication_audit_ready"
            ),
            "matrix_stack_engine_publication_policy_agreement": matrix_info.get(
                "stack_engine_publication_policy_agreement"
            ),
            "matrix_stack_engine_publication_resident_winsorized_agreement": (
                matrix_info.get(
                    "stack_engine_publication_resident_winsorized_agreement"
                )
            ),
            "default_promotion_stack_engine_publication_audit_status": (
                promotion_info.get("stack_engine_publication_audit_status")
            ),
            "default_promotion_stack_engine_publication_audit_ready": (
                promotion_info.get("stack_engine_publication_audit_ready")
            ),
            "default_promotion_stack_engine_publication_policy_agreement": (
                promotion_info.get("stack_engine_publication_policy_agreement")
            ),
            "default_promotion_stack_engine_publication_resident_winsorized_agreement": (
                promotion_info.get(
                    "stack_engine_publication_resident_winsorized_agreement"
                )
            ),
        },
        "release_manifest": {
            "status": manifest.get("status"),
            "passed": manifest.get("passed"),
            "package_labels": manifest_labels,
        },
        "github_release_plan": {
            "status": plan.get("status"),
            "passed": plan.get("passed"),
            "publication_ready": plan.get("publication_ready"),
            "asset_labels": asset_labels,
            "rejection_sample_accounting": plan_rejection_sample,
            "sample_accounting_closure": plan_sample_closure,
            "stack_engine_contract": plan_stack_engine,
            "release_decision_direct_publication_guard": (
                plan_release_direct_publication_guard
            ),
            "resident_fastpath_release_handoff": plan_resident_fastpath_handoff,
        },
        "windows_release_matrix": matrix_info,
        "default_promotion_manifest": promotion_info,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This artifact verifies local release handoff evidence; it does not upload assets or create a GitHub release.",
            "ZIP checksums are trusted from the supplied release manifest and GitHub handoff artifacts.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# GLASS Windows Publish Preflight",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Release tag: `{summary.get('release_tag')}`",
        f"- Assets/packages: `{summary.get('asset_count')}`/`{summary.get('package_count')}`",
        f"- Primary package: `{summary.get('primary_package')}`",
        f"- Try order: `{', '.join(summary.get('ordered_try_list') or [])}`",
        f"- Source stamps: `{', '.join(summary.get('source_stamps') or [])}`",
        f"- Default promotion: `{summary.get('default_promotion_status')}`",
        (
            "- Default route checks/speedup: "
            f"`{summary.get('default_route_check_count')}`/"
            f"`{summary.get('default_route_speedup_vs_reference')}`"
        ),
        (
            "- Rejection sample accounting: "
            f"phase2 `{summary.get('github_plan_phase2_rejection_sample_accounting_status')}`, "
            f"plan-matrix `{summary.get('github_plan_matrix_rejection_sample_accounting_status')}`, "
            f"matrix `{summary.get('matrix_rejection_sample_accounting_status')}`, "
            f"default-promotion `{summary.get('default_promotion_rejection_sample_accounting_status')}`"
        ),
        (
            "- Sample accounting closure: "
            f"phase2 `{summary.get('github_plan_phase2_sample_accounting_closure_status')}`, "
            f"plan-matrix `{summary.get('github_plan_matrix_sample_accounting_closure_status')}`, "
            f"matrix `{summary.get('matrix_sample_accounting_closure_status')}`, "
            f"default-promotion `{summary.get('default_promotion_sample_accounting_closure_status')}`"
        ),
        (
            "- Integration engine policy: "
            f"matrix `{summary.get('matrix_integration_engine_policy_ready')}`/"
            f"`{summary.get('matrix_acceptance_integration_engine_policy_status')}`/"
            f"`{summary.get('matrix_pipeline_integration_engine_policy_status')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_integration_engine_policy_ready')}`/"
            f"`{summary.get('default_promotion_acceptance_integration_engine_policy_status')}`/"
            f"`{summary.get('default_promotion_pipeline_integration_engine_policy_status')}`"
        ),
        (
            "- StackEngine runtime default: "
            f"matrix `{summary.get('matrix_stack_engine_runtime_default_ready')}`/"
            f"`{summary.get('matrix_acceptance_stack_engine_runtime_default_status')}`/"
            f"`{summary.get('matrix_pipeline_stack_engine_runtime_default_status')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_stack_engine_runtime_default_ready')}`/"
            f"`{summary.get('default_promotion_acceptance_stack_engine_runtime_default_status')}`/"
            f"`{summary.get('default_promotion_pipeline_stack_engine_runtime_default_status')}`"
        ),
        (
            "- Runtime default drift counters: "
            "matrix acceptance-legacy "
            f"`{summary.get('matrix_stack_engine_runtime_default_acceptance_legacy_master_count')}`, "
            "matrix pipeline-failed-output "
            f"`{summary.get('matrix_stack_engine_runtime_default_pipeline_failed_output_count')}`, "
            "default-promotion acceptance-legacy "
            f"`{summary.get('default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count')}`, "
            "default-promotion pipeline-failed-output "
            f"`{summary.get('default_promotion_stack_engine_runtime_default_pipeline_failed_output_count')}`"
        ),
        (
            "- Direct runtime evidence: "
            f"matrix `{summary.get('matrix_direct_runtime_evidence_ready')}`/"
            f"`{summary.get('matrix_direct_runtime_acceptance_source')}`/"
            f"`{summary.get('matrix_direct_runtime_acceptance_check_count')}`/"
            f"`{summary.get('matrix_direct_runtime_pipeline_calibration_source')}`/"
            f"`{summary.get('matrix_direct_runtime_pipeline_resident_lights')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_direct_runtime_evidence_ready')}`/"
            f"`{summary.get('default_promotion_direct_runtime_acceptance_source')}`/"
            f"`{summary.get('default_promotion_direct_runtime_acceptance_check_count')}`/"
            f"`{summary.get('default_promotion_direct_runtime_pipeline_calibration_source')}`/"
            f"`{summary.get('default_promotion_direct_runtime_pipeline_resident_lights')}`"
        ),
        (
            "- Release direct publication guard: "
            f"plan-matrix `{summary.get('github_plan_matrix_release_direct_publication_guard_ready')}`/"
            f"`{summary.get('github_plan_matrix_release_direct_publication_guard_lights')}`, "
            "matrix "
            f"`{summary.get('matrix_release_direct_publication_guard_ready')}`/"
            f"`{summary.get('matrix_release_direct_publication_guard_check_passed')}`/"
            f"`{summary.get('matrix_release_direct_publication_guard_source_ready')}`/"
            f"`{summary.get('matrix_release_direct_publication_guard_count_ready')}`/"
            f"`{summary.get('matrix_release_direct_publication_guard_lights')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_release_direct_publication_guard_ready')}`/"
            f"`{summary.get('default_promotion_release_direct_publication_guard_lights')}`"
        ),
        (
            "- Resident fastpath release handoff: "
            f"plan-matrix `{summary.get('github_plan_matrix_resident_fastpath_handoff_ready')}`/"
            f"`{summary.get('github_plan_matrix_resident_fastpath_handoff_raw_status')}`/"
            f"`{summary.get('github_plan_matrix_resident_fastpath_handoff_phase2_status')}`/"
            f"`{summary.get('github_plan_matrix_resident_fastpath_handoff_raw_check_count')}`, "
            "matrix "
            f"`{summary.get('matrix_resident_fastpath_handoff_ready')}`/"
            f"`{summary.get('matrix_resident_fastpath_handoff_raw_status')}`/"
            f"`{summary.get('matrix_resident_fastpath_handoff_phase2_status')}`/"
            f"`{summary.get('matrix_resident_fastpath_handoff_raw_check_count')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_resident_fastpath_handoff_ready')}`/"
            f"`{summary.get('default_promotion_resident_fastpath_handoff_raw_status')}`/"
            f"`{summary.get('default_promotion_resident_fastpath_handoff_phase2_status')}`/"
            f"`{summary.get('default_promotion_resident_fastpath_handoff_raw_check_count')}`"
        ),
        (
            "- StackEngine default contract: "
            f"phase2 `{summary.get('github_plan_phase2_stack_engine_contract_status')}`, "
            f"plan-matrix `{summary.get('github_plan_matrix_stack_engine_contract_status')}`, "
            f"matrix `{summary.get('matrix_stack_engine_contract_status')}`, "
            f"default-promotion `{summary.get('default_promotion_stack_engine_contract_status')}`"
        ),
        (
            "- StackEngine default gaps: "
            f"matrix `{summary.get('matrix_stack_engine_contract_default_gap_count')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_stack_engine_contract_default_gap_count')}`"
        ),
        (
            "- Resident winsorized sweep: "
            f"matrix `{summary.get('matrix_resident_winsorized_sweep_status')}`/"
            f"`{summary.get('matrix_resident_winsorized_sweep_required_frame_count')}`/"
            f"`{summary.get('matrix_resident_winsorized_sweep_required_frame_count_passed')}`/"
            f"`{summary.get('matrix_resident_winsorized_sweep_check_count')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_resident_winsorized_sweep_status')}`/"
            f"`{summary.get('default_promotion_resident_winsorized_sweep_required_frame_count')}`/"
            f"`{summary.get('default_promotion_resident_winsorized_sweep_required_frame_count_passed')}`/"
            f"`{summary.get('default_promotion_resident_winsorized_sweep_check_count')}`"
        ),
        (
            "- StackEngine publication audit: "
            f"matrix `{summary.get('matrix_stack_engine_publication_audit_status')}`/"
            f"`{summary.get('matrix_stack_engine_publication_audit_ready')}`/"
            f"`{summary.get('matrix_stack_engine_publication_policy_agreement')}`/"
            f"`{summary.get('matrix_stack_engine_publication_resident_winsorized_agreement')}`, "
            "default-promotion "
            f"`{summary.get('default_promotion_stack_engine_publication_audit_status')}`/"
            f"`{summary.get('default_promotion_stack_engine_publication_audit_ready')}`/"
            f"`{summary.get('default_promotion_stack_engine_publication_policy_agreement')}`/"
            f"`{summary.get('default_promotion_stack_engine_publication_resident_winsorized_agreement')}`"
        ),
        "",
        "## Inputs",
        "",
    ]
    for key, value in (payload.get("inputs") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_publish_preflight(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
