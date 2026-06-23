from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json
from glass.models import now_iso


DEFAULT_RESIDENT_REGISTRATION_HEALTH_GATE = "auto"
DEFAULT_RESIDENT_REGISTRATION_HEALTH_MIN_ACCEPTED_FRACTION = 0.75
DEFAULT_RESIDENT_REGISTRATION_HEALTH_MIN_ACCEPTED_FRAMES = 2

_SUPPORTED_ACTIONS = {"auto", "off", "warn", "fail"}
_AUTO_FAIL_MODES = {"similarity_cuda_triangle"}
_ACCEPTED_DECISION_STATUSES = {"accepted", "reference", "disabled"}
_ACCEPTED_FINAL_STATUSES = {"ok", "reference", "registered", "aligned"}


def resolve_resident_registration_health_action(
    requested_action: str,
    *,
    registration_mode: str,
) -> str:
    action = str(requested_action or DEFAULT_RESIDENT_REGISTRATION_HEALTH_GATE).lower()
    if action not in _SUPPORTED_ACTIONS:
        raise ValueError("resident registration health gate must be auto, off, warn, or fail")
    if action != "auto":
        return action
    return "fail" if str(registration_mode or "").lower() in _AUTO_FAIL_MODES else "off"


def _decision_is_accepted(row: dict[str, Any]) -> bool:
    if "accepted" in row:
        return bool(row.get("accepted"))
    decision_status = str(row.get("decision_status") or "").lower()
    final_status = str(row.get("final_status") or "").lower()
    return decision_status in _ACCEPTED_DECISION_STATUSES or final_status in _ACCEPTED_FINAL_STATUSES


def _count_from_summary_counts(counts: dict[str, Any], keys: set[str]) -> int:
    total = 0
    for key, value in counts.items():
        if str(key).lower() not in keys:
            continue
        try:
            total += int(value)
        except (TypeError, ValueError):
            continue
    return total


def _quality_counts(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    decisions_raw = payload.get("decisions") if isinstance(payload.get("decisions"), list) else []
    decisions = [item for item in decisions_raw if isinstance(item, dict)]
    if decisions:
        frame_count = len(decisions)
        accepted_count = sum(1 for item in decisions if _decision_is_accepted(item))
        rejected_frame_ids = [
            str(item.get("frame_id"))
            for item in decisions
            if item.get("frame_id") is not None and not _decision_is_accepted(item)
        ]
    else:
        try:
            frame_count = int(summary.get("frame_count") or 0)
        except (TypeError, ValueError):
            frame_count = 0
        decision_counts = summary.get("decision_status_counts")
        decision_counts = decision_counts if isinstance(decision_counts, dict) else {}
        accepted_count = _count_from_summary_counts(decision_counts, _ACCEPTED_DECISION_STATUSES)
        rejected_frame_ids = [str(item) for item in summary.get("rejected_frame_ids") or []]
    rejected_count = max(0, frame_count - accepted_count)
    accepted_fraction = (accepted_count / frame_count) if frame_count > 0 else 0.0
    rejected_fraction = (rejected_count / frame_count) if frame_count > 0 else 0.0
    return {
        "frame_count": frame_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "accepted_fraction": accepted_fraction,
        "rejected_fraction": rejected_fraction,
        "rejected_frame_ids": rejected_frame_ids,
    }


def build_resident_registration_health(
    run_dir: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_REGISTRATION_HEALTH_GATE,
    min_accepted_fraction: float = DEFAULT_RESIDENT_REGISTRATION_HEALTH_MIN_ACCEPTED_FRACTION,
    min_accepted_frames: int = DEFAULT_RESIDENT_REGISTRATION_HEALTH_MIN_ACCEPTED_FRAMES,
    registration_mode: str | None = None,
) -> dict[str, Any]:
    if not 0.0 <= float(min_accepted_fraction) <= 1.0:
        raise ValueError("resident registration health min accepted fraction must be in [0, 1]")
    if int(min_accepted_frames) < 0:
        raise ValueError("resident registration health min accepted frames must be non-negative")

    run_root = Path(run_dir)
    quality_path = run_root / "resident_registration_quality.json"
    payload: dict[str, Any] | None = None
    if quality_path.exists():
        loaded = read_json(quality_path)
        payload = loaded if isinstance(loaded, dict) else {}
    quality_registration_mode = (
        str(payload.get("registration_mode") or "") if isinstance(payload, dict) else ""
    )
    mode = str(registration_mode or quality_registration_mode or "").lower()
    action = resolve_resident_registration_health_action(requested_action, registration_mode=mode)
    enabled = action in {"warn", "fail"}
    created_at = now_iso()

    if payload is None:
        checks = [
            {
                "name": "resident_registration_quality_present",
                "passed": not enabled,
                "evidence": {"path": str(quality_path), "exists": False, "action": action},
            }
        ]
        passed = all(item["passed"] for item in checks)
        return {
            "schema_version": 1,
            "artifact_type": "resident_registration_health",
            "created_at": created_at,
            "run_dir": str(run_root),
            "quality_path": str(quality_path),
            "registration_mode": mode,
            "requested_action": str(requested_action or DEFAULT_RESIDENT_REGISTRATION_HEALTH_GATE).lower(),
            "effective_action": action,
            "status": "disabled" if action == "off" else ("passed" if passed else "failed"),
            "passed": passed,
            "blocking": action == "fail" and not passed,
            "thresholds": {
                "min_accepted_fraction": float(min_accepted_fraction),
                "min_accepted_frames": int(min_accepted_frames),
            },
            "summary": {
                "frame_count": 0,
                "accepted_count": 0,
                "rejected_count": 0,
                "accepted_fraction": 0.0,
                "rejected_fraction": 0.0,
            },
            "checks": checks,
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
            "recommended_actions": [
                "inspect resident_registration_quality.json",
                "choose a healthier reference frame or scout backend",
                "relax thresholds only for diagnostic runs",
            ],
        }

    counts = _quality_counts(payload)
    checks = [
        {
            "name": "resident_registration_quality_present",
            "passed": True,
            "evidence": {"path": str(quality_path), "exists": True, "action": action},
        },
        {
            "name": "resident_registration_decisions_present",
            "passed": not enabled or counts["frame_count"] > 0,
            "evidence": {"frame_count": counts["frame_count"], "enabled": enabled},
        },
        {
            "name": "resident_registration_min_accepted_frames",
            "passed": not enabled or counts["accepted_count"] >= int(min_accepted_frames),
            "evidence": {
                "accepted_count": counts["accepted_count"],
                "min_accepted_frames": int(min_accepted_frames),
            },
        },
        {
            "name": "resident_registration_min_accepted_fraction",
            "passed": not enabled or counts["accepted_fraction"] >= float(min_accepted_fraction),
            "evidence": {
                "accepted_fraction": counts["accepted_fraction"],
                "min_accepted_fraction": float(min_accepted_fraction),
                "accepted_count": counts["accepted_count"],
                "frame_count": counts["frame_count"],
            },
        },
    ]
    passed = all(item["passed"] for item in checks)
    failed_checks = [item["name"] for item in checks if not item["passed"]]
    status = "disabled" if action == "off" else ("passed" if passed else "warning" if action == "warn" else "failed")
    return {
        "schema_version": 1,
        "artifact_type": "resident_registration_health",
        "created_at": created_at,
        "run_dir": str(run_root),
        "quality_path": str(quality_path),
        "registration_mode": mode,
        "requested_action": str(requested_action or DEFAULT_RESIDENT_REGISTRATION_HEALTH_GATE).lower(),
        "effective_action": action,
        "status": status,
        "passed": passed or action == "warn",
        "blocking": action == "fail" and not passed,
        "thresholds": {
            "min_accepted_fraction": float(min_accepted_fraction),
            "min_accepted_frames": int(min_accepted_frames),
        },
        "summary": counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "rejected_frame_ids_sample": counts["rejected_frame_ids"][:25],
        "recommended_actions": [
            "inspect resident_reference_scout.json and resident_registration_quality.json",
            "use --reference-frame-id with a known good light frame",
            "switch --resident-reference-scout-backend cpu until CUDA scout passes real health gates",
            "relax --resident-registration-health-* only for diagnostic runs",
        ],
    }
