from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.report.phase2_mainline_audit import build_phase2_mainline_audit


DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE = "warn"
DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE = "default"


def _int_or_none(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _source_dq_summary(run: Path) -> dict[str, Any]:
    path = run / "resident_source_dq_execution.json"
    payload = _json_if_exists(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "path": str(path),
        "exists": path.exists(),
        "status": summary.get("status") or payload.get("status"),
        "passed": summary.get("passed") if "passed" in summary else payload.get("passed"),
        "frame_count": _int_or_none(summary.get("frame_count")),
        "active_frame_count": _int_or_none(summary.get("active_frame_count")),
        "input_invalid_samples_before_rejection": _int_or_none(
            summary.get("input_invalid_samples_before_rejection")
        ),
        "applied_invalid_samples": _int_or_none(summary.get("applied_invalid_samples")),
        "all_frame_input_invalid_samples_before_frame_mask": _int_or_none(
            summary.get("all_frame_input_invalid_samples_before_frame_mask")
        ),
        "all_frame_applied_invalid_samples": _int_or_none(
            summary.get("all_frame_applied_invalid_samples")
        ),
        "input_flagged_samples": _int_or_none(summary.get("input_flagged_samples")),
        "input_nonfinite_samples": _int_or_none(summary.get("input_nonfinite_samples")),
        "source_dq_flag_counts": (
            dict(summary.get("source_dq_flag_counts"))
            if isinstance(summary.get("source_dq_flag_counts"), dict)
            else {}
        ),
        "sidecar_source_counts": (
            dict(summary.get("sidecar_source_counts"))
            if isinstance(summary.get("sidecar_source_counts"), dict)
            else {}
        ),
        "execution_routes": (
            list(summary.get("execution_routes"))
            if isinstance(summary.get("execution_routes"), list)
            else []
        ),
    }


def _threshold_met(value: int | None, minimum: int) -> bool:
    if int(minimum) <= 0:
        return True
    return value is not None and int(value) >= int(minimum)


def _source_dq_checks(
    source_dq: dict[str, Any],
    *,
    min_source_dq_invalid_samples: int,
    min_source_dq_applied_samples: int,
) -> list[dict[str, Any]]:
    source_dq_required = (
        int(min_source_dq_invalid_samples) > 0 or int(min_source_dq_applied_samples) > 0
    )
    return [
        _check(
            "resident_source_dq_present_when_required",
            bool(source_dq.get("exists")) or not source_dq_required,
            {
                "required": source_dq_required,
                "path": source_dq.get("path"),
                "exists": source_dq.get("exists"),
            },
        ),
        _check(
            "resident_source_dq_passed_when_required",
            source_dq.get("passed") is True or not source_dq_required,
            {
                "required": source_dq_required,
                "status": source_dq.get("status"),
                "passed": source_dq.get("passed"),
            },
        ),
        _check(
            "resident_source_dq_invalid_threshold_met",
            _threshold_met(
                source_dq.get("input_invalid_samples_before_rejection"),
                min_source_dq_invalid_samples,
            ),
            {
                "actual": source_dq.get("input_invalid_samples_before_rejection"),
                "required_min": int(min_source_dq_invalid_samples),
                "source": "resident_source_dq_execution.summary",
            },
        ),
        _check(
            "resident_source_dq_applied_threshold_met",
            _threshold_met(
                source_dq.get("applied_invalid_samples"),
                min_source_dq_applied_samples,
            ),
            {
                "actual": source_dq.get("applied_invalid_samples"),
                "required_min": int(min_source_dq_applied_samples),
                "source": "resident_source_dq_execution.summary",
            },
        ),
    ]


def build_resident_mainline_framework(
    run: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE,
    framework_scope: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE,
    min_lights: int = 1,
    min_active_frames: int = 1,
    max_masked_frames: int = 1_000_000,
    min_source_dq_invalid_samples: int = 0,
    min_source_dq_applied_samples: int = 0,
) -> dict[str, Any]:
    """Build a resident-run postcondition summary from the already written artifacts."""

    run_path = Path(run)
    action = str(requested_action or DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE)
    if action not in {"off", "warn", "strict"}:
        raise ValueError("requested_action must be off, warn, or strict")
    scope = str(framework_scope or DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE)
    if scope not in {"default", "source_dq_positive"}:
        raise ValueError("framework_scope must be default or source_dq_positive")
    audit = build_phase2_mainline_audit(
        run_path,
        min_lights=max(0, int(min_lights)),
        min_active_frames=max(0, int(min_active_frames)),
        max_masked_frames=max(0, int(max_masked_frames)),
        require_acceptance=False,
        require_compare=False,
    )
    source_dq = _source_dq_summary(run_path)
    extra_checks = _source_dq_checks(
        source_dq,
        min_source_dq_invalid_samples=max(0, int(min_source_dq_invalid_samples)),
        min_source_dq_applied_samples=max(0, int(min_source_dq_applied_samples)),
    )
    audit_checks = list(audit.get("checks") or [])
    if scope == "source_dq_positive":
        relaxed = {"default_resident_cuda_route", "resident_output_maps_present"}
        audit_checks = [
            check
            for check in audit_checks
            if not (isinstance(check, dict) and check.get("name") in relaxed)
        ]
    checks = audit_checks + extra_checks
    failed_checks = [
        str(check.get("name"))
        for check in checks
        if isinstance(check, dict) and not check.get("passed")
    ]
    passed = not failed_checks
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    summary = {**summary, "source_dq": source_dq}
    return {
        **audit,
        "artifact_type": "resident_mainline_framework",
        "source_artifact_type": audit.get("artifact_type"),
        "scope": "resident_run_postcondition",
        "framework_scope": scope,
        "policy": {
            "requested_action": action,
            "blocking": bool(action == "strict" and not passed),
            "framework_scope": scope,
            "min_lights": max(0, int(min_lights)),
            "min_active_frames": max(0, int(min_active_frames)),
            "max_masked_frames": max(0, int(max_masked_frames)),
            "min_source_dq_invalid_samples": max(0, int(min_source_dq_invalid_samples)),
            "min_source_dq_applied_samples": max(0, int(min_source_dq_applied_samples)),
            "acceptance_required": False,
            "compare_required": False,
        },
        "summary": summary,
        "checks": checks,
        "failed_checks": failed_checks,
        "source_dq": source_dq,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "blocking": bool(action == "strict" and not passed),
    }


def write_resident_mainline_framework(
    run: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE,
    framework_scope: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_SCOPE,
    min_lights: int = 1,
    min_active_frames: int = 1,
    max_masked_frames: int = 1_000_000,
    min_source_dq_invalid_samples: int = 0,
    min_source_dq_applied_samples: int = 0,
    path: str | Path | None = None,
) -> Path:
    run_path = Path(run)
    out = Path(path) if path is not None else run_path / "resident_mainline_framework.json"
    payload = build_resident_mainline_framework(
        run_path,
        requested_action=requested_action,
        framework_scope=framework_scope,
        min_lights=min_lights,
        min_active_frames=min_active_frames,
        max_masked_frames=max_masked_frames,
        min_source_dq_invalid_samples=min_source_dq_invalid_samples,
        min_source_dq_applied_samples=min_source_dq_applied_samples,
    )
    write_json(out, payload)
    return out
