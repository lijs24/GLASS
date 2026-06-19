from __future__ import annotations

import math
from collections import Counter
from typing import Any


DEFAULT_RESIDENT_REGISTRATION_QUALITY_MIN_INLIERS = 4
_SUPPORTED_ACTIONS = {"auto", "off", "warn", "exclude"}
_AUTO_EXCLUDE_MODES = {"similarity_cuda_triangle"}


def _finite_float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_resident_registration_quality_action(
    requested_action: str,
    *,
    registration_mode: str,
) -> str:
    action = str(requested_action or "auto").lower()
    if action not in _SUPPORTED_ACTIONS:
        raise ValueError("resident registration quality gate must be auto, off, warn, or exclude")
    if action != "auto":
        return action
    return "exclude" if registration_mode in _AUTO_EXCLUDE_MODES else "off"


def evaluate_resident_registration_quality(
    *,
    frame_id: str,
    registration_mode: str,
    requested_action: str,
    status: str,
    matched_stars: int,
    inliers: int,
    rms_px: float,
    min_inliers: int = DEFAULT_RESIDENT_REGISTRATION_QUALITY_MIN_INLIERS,
    max_rms_px: float | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if min_inliers < 0:
        raise ValueError("resident registration quality min inliers must be non-negative")
    if max_rms_px is not None and max_rms_px <= 0.0:
        raise ValueError("resident registration quality max RMS must be positive when provided")

    original_status = str(status or "unknown")
    effective_action = resolve_resident_registration_quality_action(
        requested_action,
        registration_mode=registration_mode,
    )
    finite_rms = _finite_float_or_none(rms_px)
    diagnostic_fields = dict(diagnostics or {})
    reference_stars = _int_or_none(diagnostic_fields.get("reference_stars"))
    moving_stars = _int_or_none(diagnostic_fields.get("moving_stars"))
    catalog_capacity = (
        min(reference_stars, moving_stars)
        if reference_stars is not None and moving_stars is not None
        else None
    )
    reasons: list[str] = []

    applies = effective_action in {"warn", "exclude"} and original_status == "ok"
    if applies and int(inliers) < int(min_inliers):
        if catalog_capacity is None or catalog_capacity >= int(min_inliers):
            reasons.append(f"registration_inliers_below_min:{int(inliers)}<{int(min_inliers)}")
    if applies and max_rms_px is not None:
        if finite_rms is None:
            reasons.append(f"registration_rms_non_finite:max={float(max_rms_px):.6g}")
        elif finite_rms > float(max_rms_px):
            reasons.append(f"registration_rms_above_max:{finite_rms:.6g}>{float(max_rms_px):.6g}")

    final_status = original_status
    decision_status = "accepted"
    action_applied = "none"
    if effective_action == "off":
        decision_status = "disabled"
    elif original_status == "reference":
        decision_status = "reference"
    elif original_status == "excluded":
        decision_status = "already_excluded"
    elif original_status == "failed":
        decision_status = "already_failed"
    elif original_status != "ok":
        decision_status = "not_applicable"
    elif reasons and effective_action == "exclude":
        final_status = "excluded"
        decision_status = "rejected"
        action_applied = "exclude"
    elif reasons:
        decision_status = "warning"
        action_applied = "warn"

    return {
        "schema_version": 1,
        "frame_id": str(frame_id),
        "registration_mode": str(registration_mode),
        "requested_action": str(requested_action or "auto").lower(),
        "effective_action": effective_action,
        "original_status": original_status,
        "final_status": final_status,
        "decision_status": decision_status,
        "action_applied": action_applied,
        "accepted": final_status in {"ok", "reference"},
        "matched_stars": int(matched_stars),
        "inliers": int(inliers),
        "rms_px": finite_rms,
        "thresholds": {
            "min_inliers": int(min_inliers),
            "max_rms_px": None if max_rms_px is None else float(max_rms_px),
            "max_rms_enabled": max_rms_px is not None,
            "catalog_capacity_limited": bool(
                catalog_capacity is not None
                and catalog_capacity < int(min_inliers)
                and int(inliers) < int(min_inliers)
            ),
        },
        "diagnostics": {
            key: value
            for key, value in diagnostic_fields.items()
            if value is not None
        },
        "reasons": reasons,
    }


def resident_registration_quality_warning_fields(decision: dict[str, Any]) -> list[str]:
    thresholds = decision.get("thresholds") if isinstance(decision.get("thresholds"), dict) else {}
    reasons = decision.get("reasons") if isinstance(decision.get("reasons"), list) else []
    return [
        "resident_registration_quality_gate_status=" + str(decision.get("decision_status", "unknown")),
        "resident_registration_quality_gate_action=" + str(decision.get("effective_action", "unknown")),
        "resident_registration_quality_gate_applied=" + str(decision.get("action_applied", "none")),
        "resident_registration_quality_gate_min_inliers=" + str(int(thresholds.get("min_inliers", 0) or 0)),
        "resident_registration_quality_gate_max_rms_px="
        + (
            "disabled"
            if thresholds.get("max_rms_px") is None
            else f"{float(thresholds['max_rms_px']):.6g}"
        ),
        "resident_registration_quality_gate_reasons=" + (";".join(str(item) for item in reasons) or "none"),
    ]


def summarize_resident_registration_quality(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(item.get("decision_status") or "unknown") for item in decisions)
    final_counts = Counter(str(item.get("final_status") or "unknown") for item in decisions)
    action_counts = Counter(str(item.get("action_applied") or "none") for item in decisions)
    rejected = [
        str(item.get("frame_id"))
        for item in decisions
        if str(item.get("decision_status")) == "rejected"
    ]
    warned = [
        str(item.get("frame_id"))
        for item in decisions
        if str(item.get("decision_status")) == "warning"
    ]
    return {
        "frame_count": len(decisions),
        "decision_status_counts": dict(status_counts),
        "final_status_counts": dict(final_counts),
        "action_counts": dict(action_counts),
        "rejected_frame_ids": rejected,
        "warning_frame_ids": warned,
    }
