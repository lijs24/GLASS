from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _checks_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    return {
        str(item.get("name")): item
        for item in rows
        if isinstance(item, dict) and item.get("name")
    }


def _check_passed(payload: dict[str, Any], name: str) -> bool | None:
    check = _checks_by_name(payload).get(name)
    if check is None:
        return None
    return bool(check.get("passed"))


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: Any) -> int:
    return _int_or_none(value) or 0


def _raw_stack_contract_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("audit_type") == "stack_engine_default_contract"
        and summary.get("status") == "passed"
        and summary.get("passed") is True
        and summary.get("scope") == "all"
        and summary.get("default_promotion_ready") is True
        and summary.get("default_promotion_status") == "ready"
        and summary.get("adoption_recommendation") == "stack_engine_default_ready"
        and summary.get("default_promotion_recommendation") == "stack_engine_default_ready"
        and _int_or_zero(summary.get("gap_count")) == 0
        and _int_or_zero(summary.get("blocker_count")) == 0
    )


def _source_contract_summary(payload: dict[str, Any]) -> dict[str, Any]:
    adoption = payload.get("adoption") if isinstance(payload.get("adoption"), dict) else {}
    promotion = (
        payload.get("default_promotion")
        if isinstance(payload.get("default_promotion"), dict)
        else {}
    )
    gap_count = promotion.get("phase2_stack_engine_default_gap_count")
    if gap_count is None:
        gap_count = adoption.get("phase2_stack_engine_default_gap_count")
    blockers = (
        promotion.get("blockers") if isinstance(promotion.get("blockers"), list) else []
    )
    summary = {
        "artifact_type": payload.get("artifact_type"),
        "audit_type": payload.get("audit_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "scope": payload.get("scope"),
        "expected_integration_engine": payload.get("expected_integration_engine"),
        "default_promotion_ready": promotion.get("ready"),
        "default_promotion_status": promotion.get("status"),
        "adoption_recommendation": adoption.get("recommendation"),
        "default_promotion_recommendation": promotion.get("recommendation"),
        "gap_count": gap_count,
        "blocker_count": promotion.get("blocker_count", len(blockers)),
        "blockers": blockers,
    }
    summary["ready"] = _raw_stack_contract_ready(summary)
    return summary


def _phase2_direct_summary(payload: dict[str, Any]) -> dict[str, Any]:
    contract = (
        payload.get("stack_engine_contract")
        if isinstance(payload.get("stack_engine_contract"), dict)
        else {}
    )
    gap_count = contract.get("default_promotion_phase2_stack_engine_default_gap_count")
    if gap_count is None:
        gap_count = contract.get("adoption_phase2_stack_engine_default_gap_count")
    summary = {
        "artifact_type": payload.get("artifact_type"),
        "status": contract.get("status"),
        "passed": contract.get("passed"),
        "scope": contract.get("scope"),
        "expected_integration_engine": contract.get("expected_integration_engine"),
        "default_promotion_ready": contract.get("default_promotion_ready"),
        "default_promotion_status": contract.get("default_promotion_status"),
        "adoption_recommendation": contract.get("adoption_recommendation"),
        "default_promotion_recommendation": contract.get(
            "default_promotion_recommendation"
        ),
        "gap_count": gap_count,
        "blocker_count": contract.get("default_promotion_blocker_count"),
        "ready": _check_passed(payload, "stack_engine_default_contract_ready"),
    }
    return summary


def _contract_summary_from_default_promotion(payload: dict[str, Any]) -> dict[str, Any]:
    contract = (
        payload.get("stack_engine_contract")
        if isinstance(payload.get("stack_engine_contract"), dict)
        else {}
    )
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": contract.get("status"),
        "passed": contract.get("passed"),
        "scope": contract.get("scope"),
        "ready": contract.get("ready"),
        "phase2_check_passed": contract.get("phase2_check_passed"),
        "adoption_recommendation": contract.get("adoption_recommendation"),
        "gap_count": contract.get("default_promotion_phase2_stack_engine_default_gap_count"),
        "blocker_count": contract.get("default_promotion_blocker_count"),
        "blockers": contract.get("default_promotion_blockers") or [],
    }


def _contract_summary_from_release_matrix(payload: dict[str, Any]) -> dict[str, Any]:
    promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": promotion.get("stack_engine_contract_status"),
        "passed": promotion.get("stack_engine_contract_passed"),
        "scope": promotion.get("stack_engine_contract_scope"),
        "ready": promotion.get("stack_engine_contract_ready"),
        "phase2_check_passed": promotion.get("stack_engine_contract_phase2_check_passed"),
        "adoption_recommendation": promotion.get(
            "stack_engine_contract_adoption_recommendation"
        ),
        "gap_count": promotion.get("stack_engine_contract_default_gap_count"),
        "blocker_count": promotion.get("stack_engine_contract_blocker_count"),
        "blockers": promotion.get("stack_engine_contract_blockers") or [],
    }


def _github_plan_summary(payload: dict[str, Any]) -> dict[str, Any]:
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "publication_ready": payload.get("publication_ready"),
        "phase2_status": phase2_status.get("stack_engine_default_contract_status"),
        "phase2_ready": _check_passed(payload, "phase2_stack_engine_default_contract_ready"),
        "phase2_gap_count": phase2_status.get("stack_engine_default_contract_default_gap_count"),
        "phase2_blocker_count": phase2_status.get(
            "stack_engine_default_contract_blocker_count"
        ),
        "matrix_status": matrix.get("stack_engine_contract_status"),
        "matrix_ready": _check_passed(payload, "windows_release_matrix_stack_engine_contract_ready"),
        "matrix_gap_count": matrix.get("stack_engine_contract_default_gap_count"),
        "matrix_blocker_count": matrix.get("stack_engine_contract_blocker_count"),
        "agreement_passed": _check_passed(
            payload,
            "phase2_release_matrix_stack_engine_contract_agree",
        ),
    }


def _publish_preflight_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "phase2_status": summary.get("github_plan_phase2_stack_engine_contract_status"),
        "phase2_ready": _check_passed(
            payload,
            "github_plan_phase2_stack_engine_default_contract_ready",
        ),
        "plan_matrix_status": summary.get("github_plan_matrix_stack_engine_contract_status"),
        "plan_matrix_ready": _check_passed(
            payload,
            "github_plan_matrix_stack_engine_contract_ready",
        ),
        "agreement_passed": _check_passed(
            payload,
            "github_plan_stack_engine_contract_agreement_passed",
        ),
        "matrix_status": summary.get("matrix_stack_engine_contract_status"),
        "matrix_ready": _check_passed(payload, "matrix_stack_engine_contract_ready"),
        "default_promotion_status": summary.get(
            "default_promotion_stack_engine_contract_status"
        ),
        "default_promotion_ready": _check_passed(
            payload,
            "default_promotion_stack_engine_contract_ready",
        ),
        "plan_matrix_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_stack_engine_contract_matches_matrix",
        ),
        "matrix_matches_default_promotion": _check_passed(
            payload,
            "matrix_stack_engine_contract_matches_default_promotion",
        ),
        "matrix_gap_count": summary.get("matrix_stack_engine_contract_default_gap_count"),
        "default_promotion_gap_count": summary.get(
            "default_promotion_stack_engine_contract_default_gap_count"
        ),
    }


def _resident_winsorized_summary_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("matrix_status") == "passed"
        and summary.get("default_promotion_status") == "passed"
        and _all_true(
            [
                summary.get("matrix_audit_passed"),
                summary.get("matrix_required_frame_passed"),
                summary.get("matrix_check_count_passed"),
                summary.get("default_promotion_audit_passed"),
                summary.get("default_promotion_required_frame_passed"),
                summary.get("default_promotion_matches_matrix"),
            ]
        )
        and _int_or_zero(summary.get("matrix_required_frame_count")) >= 200
        and _int_or_zero(summary.get("default_promotion_required_frame_count")) >= 200
        and _int_or_zero(summary.get("matrix_check_count")) > 0
        and _int_or_zero(summary.get("default_promotion_check_count")) > 0
    )


def _publish_preflight_resident_winsorized_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "matrix_status": summary.get("matrix_resident_winsorized_sweep_status"),
        "matrix_required_frame_count": summary.get(
            "matrix_resident_winsorized_sweep_required_frame_count"
        ),
        "matrix_required_frame_count_passed": summary.get(
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ),
        "matrix_check_count": summary.get("matrix_resident_winsorized_sweep_check_count"),
        "default_promotion_status": summary.get(
            "default_promotion_resident_winsorized_sweep_status"
        ),
        "default_promotion_required_frame_count": summary.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count"
        ),
        "default_promotion_required_frame_count_passed": summary.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
        ),
        "default_promotion_check_count": summary.get(
            "default_promotion_resident_winsorized_sweep_check_count"
        ),
        "matrix_audit_passed": _check_passed(
            payload, "matrix_resident_winsorized_sweep_audit_passed"
        ),
        "matrix_required_frame_passed": _check_passed(
            payload, "matrix_resident_winsorized_required_frame_passed"
        ),
        "matrix_check_count_passed": _check_passed(
            payload, "matrix_resident_winsorized_sweep_check_count"
        ),
        "default_promotion_audit_passed": _check_passed(
            payload, "default_promotion_resident_winsorized_sweep_audit_passed"
        ),
        "default_promotion_required_frame_passed": _check_passed(
            payload, "default_promotion_resident_winsorized_required_frame_passed"
        ),
        "default_promotion_matches_matrix": _check_passed(
            payload, "default_promotion_resident_winsorized_sweep_matches_matrix"
        ),
    }
    result["ready"] = _resident_winsorized_summary_ready(result)
    return result


def _engine_policy_summary_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("matrix_ready") is True
        and summary.get("default_promotion_ready") is True
        and summary.get("matrix_acceptance_status") == "passed"
        and summary.get("matrix_pipeline_status") == "passed"
        and summary.get("default_promotion_acceptance_status") == "passed"
        and summary.get("default_promotion_pipeline_status") == "passed"
        and _all_true(
            [
                summary.get("matrix_acceptance_passed"),
                summary.get("matrix_pipeline_passed"),
                summary.get("default_promotion_acceptance_passed"),
                summary.get("default_promotion_pipeline_passed"),
                summary.get("matches_default_promotion"),
            ]
        )
    )


def _publish_preflight_engine_policy_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "matrix_ready": summary.get("matrix_integration_engine_policy_ready"),
        "matrix_acceptance_status": summary.get(
            "matrix_acceptance_integration_engine_policy_status"
        ),
        "matrix_pipeline_status": summary.get(
            "matrix_pipeline_integration_engine_policy_status"
        ),
        "default_promotion_ready": summary.get(
            "default_promotion_integration_engine_policy_ready"
        ),
        "default_promotion_acceptance_status": summary.get(
            "default_promotion_acceptance_integration_engine_policy_status"
        ),
        "default_promotion_pipeline_status": summary.get(
            "default_promotion_pipeline_integration_engine_policy_status"
        ),
        "matrix_acceptance_passed": _check_passed(
            payload,
            "windows_release_matrix_acceptance_integration_engine_policy_passed",
        ),
        "matrix_pipeline_passed": _check_passed(
            payload,
            "windows_release_matrix_pipeline_integration_engine_policy_passed",
        ),
        "default_promotion_acceptance_passed": _check_passed(
            payload,
            "default_promotion_acceptance_integration_engine_policy_passed",
        ),
        "default_promotion_pipeline_passed": _check_passed(
            payload,
            "default_promotion_pipeline_integration_engine_policy_passed",
        ),
        "matches_default_promotion": _check_passed(
            payload,
            "matrix_integration_engine_policy_matches_default_promotion",
        ),
    }
    result["ready"] = _engine_policy_summary_ready(result)
    return result


def _runtime_default_summary_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("matrix_ready") is True
        and summary.get("default_promotion_ready") is True
        and summary.get("matrix_acceptance_status") == "passed"
        and summary.get("matrix_pipeline_status") == "passed"
        and summary.get("default_promotion_acceptance_status") == "passed"
        and summary.get("default_promotion_pipeline_status") == "passed"
        and _all_true(
            [
                summary.get("matrix_acceptance_passed"),
                summary.get("matrix_pipeline_passed"),
                summary.get("default_promotion_acceptance_passed"),
                summary.get("default_promotion_pipeline_passed"),
                summary.get("matches_default_promotion"),
            ]
        )
        and _all_zero(
            [
                summary.get("matrix_acceptance_legacy_master_count"),
                summary.get("matrix_pipeline_failed_output_count"),
                summary.get("default_promotion_acceptance_legacy_master_count"),
                summary.get("default_promotion_pipeline_failed_output_count"),
            ]
        )
    )


def _publish_preflight_runtime_default_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "matrix_ready": summary.get("matrix_stack_engine_runtime_default_ready"),
        "matrix_acceptance_status": summary.get(
            "matrix_acceptance_stack_engine_runtime_default_status"
        ),
        "matrix_pipeline_status": summary.get(
            "matrix_pipeline_stack_engine_runtime_default_status"
        ),
        "matrix_acceptance_legacy_master_count": summary.get(
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
        ),
        "matrix_pipeline_failed_output_count": summary.get(
            "matrix_stack_engine_runtime_default_pipeline_failed_output_count"
        ),
        "default_promotion_ready": summary.get(
            "default_promotion_stack_engine_runtime_default_ready"
        ),
        "default_promotion_acceptance_status": summary.get(
            "default_promotion_acceptance_stack_engine_runtime_default_status"
        ),
        "default_promotion_pipeline_status": summary.get(
            "default_promotion_pipeline_stack_engine_runtime_default_status"
        ),
        "default_promotion_acceptance_legacy_master_count": summary.get(
            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count"
        ),
        "default_promotion_pipeline_failed_output_count": summary.get(
            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count"
        ),
        "matrix_acceptance_passed": _check_passed(
            payload,
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
        ),
        "matrix_pipeline_passed": _check_passed(
            payload,
            "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
        ),
        "default_promotion_acceptance_passed": _check_passed(
            payload,
            "default_promotion_acceptance_stack_engine_runtime_default_passed",
        ),
        "default_promotion_pipeline_passed": _check_passed(
            payload,
            "default_promotion_pipeline_stack_engine_runtime_default_passed",
        ),
        "matches_default_promotion": _check_passed(
            payload,
            "matrix_stack_engine_runtime_default_matches_default_promotion",
        ),
    }
    result["ready"] = _runtime_default_summary_ready(result)
    return result


def _phase2_publish_preflight_summary(payload: dict[str, Any]) -> dict[str, Any]:
    preflight = (
        payload.get("publish_preflight")
        if isinstance(payload.get("publish_preflight"), dict)
        else {}
    )
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": preflight.get("status"),
        "phase2_status": preflight.get("github_plan_phase2_stack_engine_contract_status"),
        "phase2_ready": preflight.get(
            "github_plan_phase2_stack_engine_default_contract_ready"
        ),
        "plan_matrix_status": preflight.get(
            "github_plan_matrix_stack_engine_contract_status"
        ),
        "plan_matrix_ready": preflight.get(
            "github_plan_matrix_stack_engine_contract_ready"
        ),
        "agreement_passed": preflight.get(
            "github_plan_stack_engine_contract_agreement_passed"
        ),
        "matrix_status": preflight.get("matrix_stack_engine_contract_status"),
        "matrix_ready": preflight.get("matrix_stack_engine_contract_ready"),
        "default_promotion_status": preflight.get(
            "default_promotion_stack_engine_contract_status"
        ),
        "default_promotion_ready": preflight.get(
            "default_promotion_stack_engine_contract_ready"
        ),
        "plan_matrix_matches_matrix": preflight.get(
            "github_plan_matrix_stack_engine_contract_matches_matrix"
        ),
        "matrix_matches_default_promotion": preflight.get(
            "matrix_stack_engine_contract_matches_default_promotion"
        ),
        "matrix_gap_count": preflight.get("matrix_stack_engine_contract_default_gap_count"),
        "default_promotion_gap_count": preflight.get(
            "default_promotion_stack_engine_contract_default_gap_count"
        ),
        "phase2_check_passed": _check_passed(
            payload,
            "windows_publish_preflight_stack_engine_default_contract_ready",
        ),
    }


def _phase2_publish_preflight_engine_policy_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    preflight = (
        payload.get("publish_preflight")
        if isinstance(payload.get("publish_preflight"), dict)
        else {}
    )
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": preflight.get("status"),
        "matrix_ready": preflight.get("matrix_integration_engine_policy_ready"),
        "matrix_acceptance_status": preflight.get(
            "matrix_acceptance_integration_engine_policy_status"
        ),
        "matrix_pipeline_status": preflight.get(
            "matrix_pipeline_integration_engine_policy_status"
        ),
        "default_promotion_ready": preflight.get(
            "default_promotion_integration_engine_policy_ready"
        ),
        "default_promotion_acceptance_status": preflight.get(
            "default_promotion_acceptance_integration_engine_policy_status"
        ),
        "default_promotion_pipeline_status": preflight.get(
            "default_promotion_pipeline_integration_engine_policy_status"
        ),
        "matrix_acceptance_passed": preflight.get(
            "windows_release_matrix_acceptance_integration_engine_policy_passed"
        ),
        "matrix_pipeline_passed": preflight.get(
            "windows_release_matrix_pipeline_integration_engine_policy_passed"
        ),
        "default_promotion_acceptance_passed": preflight.get(
            "default_promotion_acceptance_integration_engine_policy_passed"
        ),
        "default_promotion_pipeline_passed": preflight.get(
            "default_promotion_pipeline_integration_engine_policy_passed"
        ),
        "matches_default_promotion": preflight.get(
            "matrix_integration_engine_policy_matches_default_promotion"
        ),
        "phase2_check_passed": _check_passed(
            payload,
            "windows_publish_preflight_integration_engine_policy_passed",
        ),
    }
    result["ready"] = (
        _engine_policy_summary_ready(result)
        and result.get("phase2_check_passed") is True
    )
    return result


def _phase2_publish_preflight_runtime_default_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    preflight = (
        payload.get("publish_preflight")
        if isinstance(payload.get("publish_preflight"), dict)
        else {}
    )
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": preflight.get("status"),
        "matrix_ready": preflight.get("matrix_stack_engine_runtime_default_ready"),
        "matrix_acceptance_status": preflight.get(
            "matrix_acceptance_stack_engine_runtime_default_status"
        ),
        "matrix_pipeline_status": preflight.get(
            "matrix_pipeline_stack_engine_runtime_default_status"
        ),
        "matrix_acceptance_legacy_master_count": preflight.get(
            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
        ),
        "matrix_pipeline_failed_output_count": preflight.get(
            "matrix_stack_engine_runtime_default_pipeline_failed_output_count"
        ),
        "default_promotion_ready": preflight.get(
            "default_promotion_stack_engine_runtime_default_ready"
        ),
        "default_promotion_acceptance_status": preflight.get(
            "default_promotion_acceptance_stack_engine_runtime_default_status"
        ),
        "default_promotion_pipeline_status": preflight.get(
            "default_promotion_pipeline_stack_engine_runtime_default_status"
        ),
        "default_promotion_acceptance_legacy_master_count": preflight.get(
            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count"
        ),
        "default_promotion_pipeline_failed_output_count": preflight.get(
            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count"
        ),
        "matrix_acceptance_passed": preflight.get(
            "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
        ),
        "matrix_pipeline_passed": preflight.get(
            "windows_release_matrix_pipeline_stack_engine_runtime_default_passed"
        ),
        "default_promotion_acceptance_passed": preflight.get(
            "default_promotion_acceptance_stack_engine_runtime_default_passed"
        ),
        "default_promotion_pipeline_passed": preflight.get(
            "default_promotion_pipeline_stack_engine_runtime_default_passed"
        ),
        "matches_default_promotion": preflight.get(
            "matrix_stack_engine_runtime_default_matches_default_promotion"
        ),
        "phase2_check_passed": _check_passed(
            payload,
            "windows_publish_preflight_stack_engine_runtime_default_passed",
        ),
    }
    result["ready"] = (
        _runtime_default_summary_ready(result)
        and result.get("phase2_check_passed") is True
    )
    return result


def _phase2_publish_preflight_resident_winsorized_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    preflight = (
        payload.get("publish_preflight")
        if isinstance(payload.get("publish_preflight"), dict)
        else {}
    )
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": preflight.get("status"),
        "matrix_status": preflight.get("matrix_resident_winsorized_sweep_status"),
        "matrix_required_frame_count": preflight.get(
            "matrix_resident_winsorized_sweep_required_frame_count"
        ),
        "matrix_required_frame_count_passed": preflight.get(
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ),
        "matrix_check_count": preflight.get("matrix_resident_winsorized_sweep_check_count"),
        "default_promotion_status": preflight.get(
            "default_promotion_resident_winsorized_sweep_status"
        ),
        "default_promotion_required_frame_count": preflight.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count"
        ),
        "default_promotion_required_frame_count_passed": preflight.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
        ),
        "default_promotion_check_count": preflight.get(
            "default_promotion_resident_winsorized_sweep_check_count"
        ),
        "matrix_audit_passed": preflight.get(
            "matrix_resident_winsorized_sweep_audit_passed"
        ),
        "matrix_required_frame_passed": preflight.get(
            "matrix_resident_winsorized_required_frame_passed"
        ),
        "matrix_check_count_passed": preflight.get(
            "matrix_resident_winsorized_sweep_check_count_passed"
        ),
        "default_promotion_audit_passed": preflight.get(
            "default_promotion_resident_winsorized_sweep_audit_passed"
        ),
        "default_promotion_required_frame_passed": preflight.get(
            "default_promotion_resident_winsorized_required_frame_passed"
        ),
        "default_promotion_matches_matrix": preflight.get(
            "default_promotion_resident_winsorized_sweep_matches_matrix"
        ),
        "phase2_check_passed": _check_passed(
            payload,
            "windows_publish_preflight_resident_winsorized_sweep_passed",
        ),
    }
    result["ready"] = (
        _resident_winsorized_summary_ready(result)
        and result.get("phase2_check_passed") is True
    )
    return result


def _resident_winsorized_summaries_match(
    phase2_summary: dict[str, Any],
    preflight_summary: dict[str, Any],
) -> bool:
    fields = (
        "matrix_status",
        "matrix_required_frame_count",
        "matrix_required_frame_count_passed",
        "matrix_check_count",
        "default_promotion_status",
        "default_promotion_required_frame_count",
        "default_promotion_required_frame_count_passed",
        "default_promotion_check_count",
        "matrix_audit_passed",
        "matrix_required_frame_passed",
        "matrix_check_count_passed",
        "default_promotion_audit_passed",
        "default_promotion_required_frame_passed",
        "default_promotion_matches_matrix",
        "ready",
    )
    return all(phase2_summary.get(field) == preflight_summary.get(field) for field in fields)


def _engine_policy_summaries_match(
    phase2_summary: dict[str, Any],
    preflight_summary: dict[str, Any],
) -> bool:
    fields = (
        "matrix_ready",
        "matrix_acceptance_status",
        "matrix_pipeline_status",
        "default_promotion_ready",
        "default_promotion_acceptance_status",
        "default_promotion_pipeline_status",
        "matrix_acceptance_passed",
        "matrix_pipeline_passed",
        "default_promotion_acceptance_passed",
        "default_promotion_pipeline_passed",
        "matches_default_promotion",
        "ready",
    )
    return all(phase2_summary.get(field) == preflight_summary.get(field) for field in fields)


def _runtime_default_summaries_match(
    phase2_summary: dict[str, Any],
    preflight_summary: dict[str, Any],
) -> bool:
    fields = (
        "matrix_ready",
        "matrix_acceptance_status",
        "matrix_pipeline_status",
        "matrix_acceptance_legacy_master_count",
        "matrix_pipeline_failed_output_count",
        "default_promotion_ready",
        "default_promotion_acceptance_status",
        "default_promotion_pipeline_status",
        "default_promotion_acceptance_legacy_master_count",
        "default_promotion_pipeline_failed_output_count",
        "matrix_acceptance_passed",
        "matrix_pipeline_passed",
        "default_promotion_acceptance_passed",
        "default_promotion_pipeline_passed",
        "matches_default_promotion",
        "ready",
    )
    return all(phase2_summary.get(field) == preflight_summary.get(field) for field in fields)


def _publication_audit_summary_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("matrix_status") == "passed"
        and summary.get("default_promotion_status") == "passed"
        and summary.get("matrix_ready") is True
        and summary.get("default_promotion_ready") is True
        and summary.get("matrix_policy_agreement") is True
        and summary.get("matrix_resident_winsorized_agreement") is True
        and summary.get("default_promotion_policy_agreement") is True
        and summary.get("default_promotion_resident_winsorized_agreement") is True
        and _all_true(
            [
                summary.get("matrix_audit_passed"),
                summary.get("matrix_policy_chain_passed"),
                summary.get("matrix_resident_winsorized_chain_passed"),
                summary.get("default_promotion_audit_passed"),
                summary.get("default_promotion_policy_chain_passed"),
                summary.get("default_promotion_resident_winsorized_chain_passed"),
                summary.get("matches_default_promotion"),
            ]
        )
    )


def _publish_preflight_publication_audit_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "matrix_status": summary.get("matrix_stack_engine_publication_audit_status"),
        "matrix_ready": summary.get("matrix_stack_engine_publication_audit_ready"),
        "matrix_policy_agreement": summary.get(
            "matrix_stack_engine_publication_policy_agreement"
        ),
        "matrix_resident_winsorized_agreement": summary.get(
            "matrix_stack_engine_publication_resident_winsorized_agreement"
        ),
        "default_promotion_status": summary.get(
            "default_promotion_stack_engine_publication_audit_status"
        ),
        "default_promotion_ready": summary.get(
            "default_promotion_stack_engine_publication_audit_ready"
        ),
        "default_promotion_policy_agreement": summary.get(
            "default_promotion_stack_engine_publication_policy_agreement"
        ),
        "default_promotion_resident_winsorized_agreement": summary.get(
            "default_promotion_stack_engine_publication_resident_winsorized_agreement"
        ),
        "matrix_audit_passed": _check_passed(
            payload,
            "matrix_stack_engine_publication_audit_passed",
        ),
        "matrix_policy_chain_passed": _check_passed(
            payload,
            "matrix_stack_engine_publication_policy_chain_passed",
        ),
        "matrix_resident_winsorized_chain_passed": _check_passed(
            payload,
            "matrix_stack_engine_publication_resident_winsorized_chain_passed",
        ),
        "default_promotion_audit_passed": _check_passed(
            payload,
            "default_promotion_stack_engine_publication_audit_passed",
        ),
        "default_promotion_policy_chain_passed": _check_passed(
            payload,
            "default_promotion_stack_engine_publication_policy_chain_passed",
        ),
        "default_promotion_resident_winsorized_chain_passed": _check_passed(
            payload,
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
        ),
        "matches_default_promotion": _check_passed(
            payload,
            "matrix_stack_engine_publication_audit_matches_default_promotion",
        ),
    }
    result["ready"] = _publication_audit_summary_ready(result)
    return result


def _phase2_publish_preflight_publication_audit_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    preflight = (
        payload.get("publish_preflight")
        if isinstance(payload.get("publish_preflight"), dict)
        else {}
    )
    result = {
        "artifact_type": payload.get("artifact_type"),
        "status": preflight.get("status"),
        "matrix_status": preflight.get("matrix_stack_engine_publication_audit_status"),
        "matrix_ready": preflight.get("matrix_stack_engine_publication_audit_ready"),
        "matrix_policy_agreement": preflight.get(
            "matrix_stack_engine_publication_policy_agreement"
        ),
        "matrix_resident_winsorized_agreement": preflight.get(
            "matrix_stack_engine_publication_resident_winsorized_agreement"
        ),
        "default_promotion_status": preflight.get(
            "default_promotion_stack_engine_publication_audit_status"
        ),
        "default_promotion_ready": preflight.get(
            "default_promotion_stack_engine_publication_audit_ready"
        ),
        "default_promotion_policy_agreement": preflight.get(
            "default_promotion_stack_engine_publication_policy_agreement"
        ),
        "default_promotion_resident_winsorized_agreement": preflight.get(
            "default_promotion_stack_engine_publication_resident_winsorized_agreement"
        ),
        "matrix_audit_passed": preflight.get(
            "matrix_stack_engine_publication_audit_passed"
        ),
        "matrix_policy_chain_passed": preflight.get(
            "matrix_stack_engine_publication_policy_chain_passed"
        ),
        "matrix_resident_winsorized_chain_passed": preflight.get(
            "matrix_stack_engine_publication_resident_winsorized_chain_passed"
        ),
        "default_promotion_audit_passed": preflight.get(
            "default_promotion_stack_engine_publication_audit_passed"
        ),
        "default_promotion_policy_chain_passed": preflight.get(
            "default_promotion_stack_engine_publication_policy_chain_passed"
        ),
        "default_promotion_resident_winsorized_chain_passed": preflight.get(
            "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
        ),
        "matches_default_promotion": preflight.get(
            "matrix_stack_engine_publication_audit_matches_default_promotion"
        ),
        "phase2_check_passed": _check_passed(
            payload,
            "windows_publish_preflight_stack_engine_publication_audit_passed",
        ),
    }
    result["ready"] = (
        _publication_audit_summary_ready(result)
        and result.get("phase2_check_passed") is True
    )
    return result


def _publication_audit_summaries_match(
    phase2_summary: dict[str, Any],
    preflight_summary: dict[str, Any],
) -> bool:
    fields = (
        "matrix_status",
        "matrix_ready",
        "matrix_policy_agreement",
        "matrix_resident_winsorized_agreement",
        "default_promotion_status",
        "default_promotion_ready",
        "default_promotion_policy_agreement",
        "default_promotion_resident_winsorized_agreement",
        "matrix_audit_passed",
        "matrix_policy_chain_passed",
        "matrix_resident_winsorized_chain_passed",
        "default_promotion_audit_passed",
        "default_promotion_policy_chain_passed",
        "default_promotion_resident_winsorized_chain_passed",
        "matches_default_promotion",
        "ready",
    )
    return all(phase2_summary.get(field) == preflight_summary.get(field) for field in fields)


def _all_true(values: list[Any]) -> bool:
    return all(value is True for value in values)


def _all_zero(values: list[Any]) -> bool:
    return all(_int_or_zero(value) == 0 for value in values)


def build_stack_engine_publication_audit(
    *,
    stack_engine_contract: str | Path,
    phase2_status: str | Path,
    default_promotion_manifest: str | Path,
    windows_release_matrix: str | Path,
    github_release_plan: str | Path,
    publish_preflight: str | Path,
) -> dict[str, Any]:
    source_path = Path(stack_engine_contract)
    phase2_path = Path(phase2_status)
    promotion_path = Path(default_promotion_manifest)
    matrix_path = Path(windows_release_matrix)
    github_path = Path(github_release_plan)
    preflight_path = Path(publish_preflight)

    source = _source_contract_summary(_read_json_object(source_path))
    phase2_direct = _phase2_direct_summary(_read_json_object(phase2_path))
    default_promotion = _contract_summary_from_default_promotion(
        _read_json_object(promotion_path)
    )
    release_matrix = _contract_summary_from_release_matrix(_read_json_object(matrix_path))
    github_plan = _github_plan_summary(_read_json_object(github_path))
    preflight_payload = _read_json_object(preflight_path)
    phase2_payload = _read_json_object(phase2_path)
    preflight = _publish_preflight_summary(preflight_payload)
    phase2_publish = _phase2_publish_preflight_summary(phase2_payload)
    preflight_winsorized = _publish_preflight_resident_winsorized_summary(
        preflight_payload
    )
    phase2_preflight_winsorized = (
        _phase2_publish_preflight_resident_winsorized_summary(phase2_payload)
    )
    preflight_engine_policy = _publish_preflight_engine_policy_summary(
        preflight_payload
    )
    phase2_preflight_engine_policy = (
        _phase2_publish_preflight_engine_policy_summary(phase2_payload)
    )
    preflight_runtime_default = _publish_preflight_runtime_default_summary(
        preflight_payload
    )
    phase2_preflight_runtime_default = (
        _phase2_publish_preflight_runtime_default_summary(phase2_payload)
    )
    preflight_publication_audit = _publish_preflight_publication_audit_summary(
        preflight_payload
    )
    phase2_preflight_publication_audit = (
        _phase2_publish_preflight_publication_audit_summary(phase2_payload)
    )

    layers = {
        "source_contract": source,
        "phase2_direct_contract": phase2_direct,
        "default_promotion_manifest": default_promotion,
        "windows_release_matrix": release_matrix,
        "github_release_plan": github_plan,
        "publish_preflight": preflight,
        "phase2_publish_preflight": phase2_publish,
        "publish_preflight_resident_winsorized_sweep": preflight_winsorized,
        "phase2_publish_preflight_resident_winsorized_sweep": (
            phase2_preflight_winsorized
        ),
        "publish_preflight_integration_engine_policy": preflight_engine_policy,
        "phase2_publish_preflight_integration_engine_policy": (
            phase2_preflight_engine_policy
        ),
        "publish_preflight_stack_engine_runtime_default": preflight_runtime_default,
        "phase2_publish_preflight_stack_engine_runtime_default": (
            phase2_preflight_runtime_default
        ),
        "publish_preflight_publication_audit": preflight_publication_audit,
        "phase2_publish_preflight_publication_audit": (
            phase2_preflight_publication_audit
        ),
    }
    direct_gap_counts = [
        source.get("gap_count"),
        phase2_direct.get("gap_count"),
        default_promotion.get("gap_count"),
        release_matrix.get("gap_count"),
        github_plan.get("phase2_gap_count"),
        github_plan.get("matrix_gap_count"),
        preflight.get("matrix_gap_count"),
        preflight.get("default_promotion_gap_count"),
        phase2_publish.get("matrix_gap_count"),
        phase2_publish.get("default_promotion_gap_count"),
    ]
    direct_blocker_counts = [
        source.get("blocker_count"),
        phase2_direct.get("blocker_count"),
        default_promotion.get("blocker_count"),
        release_matrix.get("blocker_count"),
        github_plan.get("phase2_blocker_count"),
        github_plan.get("matrix_blocker_count"),
    ]
    checks = [
        _check("source_contract_ready", source.get("ready") is True, source),
        _check(
            "phase2_direct_contract_ready",
            phase2_direct.get("ready") is True,
            phase2_direct,
        ),
        _check(
            "default_promotion_stack_engine_ready",
            default_promotion.get("ready") is True
            and default_promotion.get("phase2_check_passed") is True,
            default_promotion,
        ),
        _check(
            "windows_release_matrix_stack_engine_ready",
            release_matrix.get("ready") is True
            and release_matrix.get("phase2_check_passed") is True,
            release_matrix,
        ),
        _check(
            "github_release_plan_stack_engine_ready",
            github_plan.get("phase2_ready") is True
            and github_plan.get("matrix_ready") is True
            and github_plan.get("agreement_passed") is True,
            github_plan,
        ),
        _check(
            "publish_preflight_stack_engine_ready",
            _all_true(
                [
                    preflight.get("phase2_ready"),
                    preflight.get("plan_matrix_ready"),
                    preflight.get("agreement_passed"),
                    preflight.get("matrix_ready"),
                    preflight.get("default_promotion_ready"),
                    preflight.get("plan_matrix_matches_matrix"),
                    preflight.get("matrix_matches_default_promotion"),
                ]
            ),
            preflight,
        ),
        _check(
            "phase2_publish_preflight_stack_engine_ready",
            _all_true(
                [
                    phase2_publish.get("phase2_ready"),
                    phase2_publish.get("plan_matrix_ready"),
                    phase2_publish.get("agreement_passed"),
                    phase2_publish.get("matrix_ready"),
                    phase2_publish.get("default_promotion_ready"),
                    phase2_publish.get("plan_matrix_matches_matrix"),
                    phase2_publish.get("matrix_matches_default_promotion"),
                    phase2_publish.get("phase2_check_passed"),
                ]
            ),
            phase2_publish,
        ),
        _check(
            "publish_preflight_resident_winsorized_sweep_ready",
            preflight_winsorized.get("ready") is True,
            preflight_winsorized,
        ),
        _check(
            "phase2_publish_preflight_resident_winsorized_sweep_ready",
            phase2_preflight_winsorized.get("ready") is True,
            phase2_preflight_winsorized,
        ),
        _check(
            "phase2_publish_preflight_resident_winsorized_matches_publish_preflight",
            _resident_winsorized_summaries_match(
                phase2_preflight_winsorized,
                preflight_winsorized,
            ),
            {
                "phase2_publish_preflight": phase2_preflight_winsorized,
                "publish_preflight": preflight_winsorized,
            },
        ),
        _check(
            "publish_preflight_integration_engine_policy_ready",
            preflight_engine_policy.get("ready") is True,
            preflight_engine_policy,
        ),
        _check(
            "phase2_publish_preflight_integration_engine_policy_ready",
            phase2_preflight_engine_policy.get("ready") is True,
            phase2_preflight_engine_policy,
        ),
        _check(
            "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight",
            _engine_policy_summaries_match(
                phase2_preflight_engine_policy,
                preflight_engine_policy,
            ),
            {
                "phase2_publish_preflight": phase2_preflight_engine_policy,
                "publish_preflight": preflight_engine_policy,
            },
        ),
        _check(
            "publish_preflight_stack_engine_runtime_default_ready",
            preflight_runtime_default.get("ready") is True,
            preflight_runtime_default,
        ),
        _check(
            "phase2_publish_preflight_stack_engine_runtime_default_ready",
            phase2_preflight_runtime_default.get("ready") is True,
            phase2_preflight_runtime_default,
        ),
        _check(
            "phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight",
            _runtime_default_summaries_match(
                phase2_preflight_runtime_default,
                preflight_runtime_default,
            ),
            {
                "phase2_publish_preflight": phase2_preflight_runtime_default,
                "publish_preflight": preflight_runtime_default,
            },
        ),
        _check(
            "publish_preflight_publication_audit_ready",
            preflight_publication_audit.get("ready") is True,
            preflight_publication_audit,
        ),
        _check(
            "phase2_publish_preflight_publication_audit_ready",
            phase2_preflight_publication_audit.get("ready") is True,
            phase2_preflight_publication_audit,
        ),
        _check(
            "phase2_publish_preflight_publication_audit_matches_publish_preflight",
            _publication_audit_summaries_match(
                phase2_preflight_publication_audit,
                preflight_publication_audit,
            ),
            {
                "phase2_publish_preflight": phase2_preflight_publication_audit,
                "publish_preflight": preflight_publication_audit,
            },
        ),
        _check(
            "stack_engine_gap_counts_zero",
            _all_zero(direct_gap_counts),
            {"gap_counts": direct_gap_counts},
        ),
        _check(
            "stack_engine_blocker_counts_zero",
            _all_zero(direct_blocker_counts),
            {"blocker_counts": direct_blocker_counts},
        ),
        _check(
            "phase2_direct_contract_matches_source",
            phase2_direct.get("status") == source.get("status")
            and _int_or_none(phase2_direct.get("gap_count"))
            == _int_or_none(source.get("gap_count"))
            and _int_or_none(phase2_direct.get("blocker_count"))
            == _int_or_none(source.get("blocker_count")),
            {"source": source, "phase2_direct": phase2_direct},
        ),
        _check(
            "default_promotion_matches_source",
            default_promotion.get("status") == source.get("status")
            and _int_or_none(default_promotion.get("gap_count"))
            == _int_or_none(source.get("gap_count"))
            and _int_or_none(default_promotion.get("blocker_count"))
            == _int_or_none(source.get("blocker_count")),
            {"source": source, "default_promotion": default_promotion},
        ),
        _check(
            "default_promotion_matches_phase2_direct_contract",
            default_promotion.get("status") == phase2_direct.get("status")
            and _int_or_none(default_promotion.get("gap_count"))
            == _int_or_none(phase2_direct.get("gap_count"))
            and _int_or_none(default_promotion.get("blocker_count"))
            == _int_or_none(phase2_direct.get("blocker_count")),
            {
                "phase2_direct": phase2_direct,
                "default_promotion": default_promotion,
            },
        ),
        _check(
            "release_matrix_matches_default_promotion",
            release_matrix.get("ready") == default_promotion.get("ready")
            and release_matrix.get("status") == default_promotion.get("status")
            and _int_or_none(release_matrix.get("gap_count"))
            == _int_or_none(default_promotion.get("gap_count"))
            and _int_or_none(release_matrix.get("blocker_count"))
            == _int_or_none(default_promotion.get("blocker_count")),
            {"release_matrix": release_matrix, "default_promotion": default_promotion},
        ),
        _check(
            "github_plan_matches_release_matrix",
            github_plan.get("matrix_ready") == release_matrix.get("ready")
            and github_plan.get("matrix_status") == release_matrix.get("status")
            and _int_or_none(github_plan.get("matrix_gap_count"))
            == _int_or_none(release_matrix.get("gap_count"))
            and _int_or_none(github_plan.get("matrix_blocker_count"))
            == _int_or_none(release_matrix.get("blocker_count")),
            {"github_release_plan": github_plan, "release_matrix": release_matrix},
        ),
        _check(
            "publish_preflight_matches_release_matrix",
            preflight.get("matrix_ready") == release_matrix.get("ready")
            and preflight.get("matrix_status") == release_matrix.get("status")
            and _int_or_none(preflight.get("matrix_gap_count"))
            == _int_or_none(release_matrix.get("gap_count")),
            {"publish_preflight": preflight, "release_matrix": release_matrix},
        ),
        _check(
            "phase2_publish_preflight_matches_publish_preflight",
            phase2_publish.get("matrix_ready") == preflight.get("matrix_ready")
            and phase2_publish.get("matrix_status") == preflight.get("matrix_status")
            and _int_or_none(phase2_publish.get("matrix_gap_count"))
            == _int_or_none(preflight.get("matrix_gap_count"))
            and phase2_publish.get("phase2_check_passed") is True,
            {"phase2_publish_preflight": phase2_publish, "publish_preflight": preflight},
        ),
    ]
    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "stack_engine_publication_audit",
        "created_at": now_iso(),
        "status": "passed" if not failed else "blocked",
        "passed": not failed,
        "recommendation": "publication_chain_ready"
        if not failed
        else "fix_stack_engine_publication_chain",
        "inputs": {
            "stack_engine_contract": str(source_path),
            "phase2_status": str(phase2_path),
            "default_promotion_manifest": str(promotion_path),
            "windows_release_matrix": str(matrix_path),
            "github_release_plan": str(github_path),
            "publish_preflight": str(preflight_path),
        },
        "layers": layers,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This audit validates GLASS publication evidence artifacts only; it does not regenerate them.",
            "No image pixels, FITS/XISF inputs, CUDA kernels, package uploads, or GitHub releases are touched.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GLASS StackEngine Publication Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        "",
        "## Inputs",
        "",
    ]
    for key, value in (payload.get("inputs") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Layers", ""])
    for name, row in (payload.get("layers") or {}).items():
        if not isinstance(row, dict):
            continue
        status = row.get("status") or row.get("matrix_status")
        ready = row.get("ready")
        if ready is None:
            ready = row.get("matrix_ready")
        gap = row.get("gap_count")
        if gap is None:
            gap = row.get("matrix_gap_count")
        lines.append(f"- {name}: status=`{status}` ready=`{ready}` gap=`{gap}`")
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_stack_engine_publication_audit(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        target = Path(markdown)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_markdown(payload), encoding="utf-8")
