from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    return payload if isinstance(payload, dict) else None


def _finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _row_accepted(item: dict[str, Any]) -> bool:
    validation = item.get("registration_validation") if isinstance(item.get("registration_validation"), dict) else {}
    if "accepted" in validation:
        return bool(validation.get("accepted"))
    return str(item.get("status") or "").lower() in {"reference", "registered", "aligned", "ok"}


def _registration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("registration_results") or []:
        if not isinstance(item, dict):
            continue
        validation = item.get("registration_validation") if isinstance(item.get("registration_validation"), dict) else {}
        rms = _finite_float(validation.get("rms_px"))
        if rms is None:
            rms = _finite_float(item.get("rms_px"))
        inliers = _optional_int(validation.get("inliers"))
        if inliers is None:
            inliers = _optional_int(item.get("inliers"))
        matched = _optional_int(item.get("matched_stars"))
        accepted = _row_accepted(item)
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "status": item.get("status"),
                "accepted": accepted,
                "reference_frame_id": item.get("reference_frame_id"),
                "transform_model": item.get("transform_model") or validation.get("model"),
                "solution_source": item.get("registration_solution_source")
                or validation.get("solution_source"),
                "quality_gate_status": item.get("quality_gate_status"),
                "rms_px": rms,
                "inliers": inliers,
                "matched_stars": matched,
                "warnings": item.get("warnings") or [],
            }
        )
    return rows


def build_registration_quality_contract(
    run_dir: str | Path,
    *,
    max_rms_px: float | None = None,
    min_inliers: int | None = None,
    require_all_accepted: bool = False,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    registration_path = run_root / "registration_results.json"
    payload = _read_json_object(registration_path)
    required = max_rms_px is not None or min_inliers is not None or bool(require_all_accepted)
    created_at = now_iso()
    if payload is None:
        checks = [
            _check(
                "registration_results_present",
                not required,
                {"path": str(registration_path), "exists": registration_path.exists(), "required": required},
            )
        ]
        return {
            "schema_version": 1,
            "artifact_type": "registration_quality_contract",
            "created_at": created_at,
            "run_dir": str(run_root),
            "registration_path": str(registration_path),
            "status": "passed" if not required else "failed",
            "passed": not required,
            "required": required,
            "thresholds": {
                "max_rms_px": max_rms_px,
                "min_inliers": min_inliers,
                "require_all_accepted": bool(require_all_accepted),
            },
            "summary": {
                "output_count": 0,
                "accepted_count": 0,
                "failed_count": 0,
                "max_rms_px": None,
                "min_inliers": None,
            },
            "checks": checks,
            "outputs": [],
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
        }

    rows = _registration_rows(payload)
    accepted_rows = [row for row in rows if row["accepted"]]
    failed_rows = [row for row in rows if not row["accepted"]]
    finite_rms_values = [row["rms_px"] for row in accepted_rows if row["rms_px"] is not None]
    inlier_values = [row["inliers"] for row in accepted_rows if row["inliers"] is not None]
    max_rms_observed = max(finite_rms_values) if finite_rms_values else None
    min_inliers_observed = min(inlier_values) if inlier_values else None
    rms_failures = [
        row
        for row in accepted_rows
        if max_rms_px is not None and (row["rms_px"] is None or row["rms_px"] > float(max_rms_px))
    ]
    inlier_failures = [
        row
        for row in accepted_rows
        if min_inliers is not None and (row["inliers"] is None or row["inliers"] < int(min_inliers))
    ]
    checks = [
        _check(
            "registration_results_present",
            True,
            {"path": str(registration_path), "required": required},
        ),
        _check(
            "registration_outputs_present",
            bool(rows),
            {"output_count": len(rows)},
        ),
        _check(
            "accepted_registration_outputs_present",
            not required or bool(accepted_rows),
            {"accepted_count": len(accepted_rows), "required": required},
        ),
    ]
    if max_rms_px is not None:
        checks.append(
            _check(
                "accepted_registration_rms_within_threshold",
                bool(accepted_rows) and not rms_failures,
                {
                    "max_observed_rms_px": max_rms_observed,
                    "max_rms_px": max_rms_px,
                    "failed": [row["frame_id"] for row in rms_failures],
                },
            )
        )
    if min_inliers is not None:
        checks.append(
            _check(
                "accepted_registration_inliers_meet_threshold",
                bool(accepted_rows) and not inlier_failures,
                {
                    "min_observed_inliers": min_inliers_observed,
                    "min_inliers": min_inliers,
                    "failed": [row["frame_id"] for row in inlier_failures],
                },
            )
        )
    if require_all_accepted:
        checks.append(
            _check(
                "all_registration_outputs_accepted",
                bool(rows) and not failed_rows,
                {
                    "output_count": len(rows),
                    "failed_count": len(failed_rows),
                    "failed": [row["frame_id"] for row in failed_rows],
                },
            )
        )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "registration_quality_contract",
        "created_at": created_at,
        "run_dir": str(run_root),
        "registration_path": str(registration_path),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "required": required,
        "thresholds": {
            "max_rms_px": max_rms_px,
            "min_inliers": min_inliers,
            "require_all_accepted": bool(require_all_accepted),
        },
        "summary": {
            "output_count": len(rows),
            "accepted_count": len(accepted_rows),
            "failed_count": len(failed_rows),
            "max_rms_px": max_rms_observed,
            "min_inliers": min_inliers_observed,
            "quality_gate_rejected_frames": payload.get("quality_gate_rejected_frames"),
            "reference_frame_id": payload.get("reference_frame_id"),
            "method": payload.get("method"),
            "transform_model": payload.get("transform_model"),
        },
        "checks": checks,
        "outputs": rows,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "failed_outputs": failed_rows,
    }


def write_registration_quality_contract(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is None:
        return
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    thresholds = payload.get("thresholds") if isinstance(payload.get("thresholds"), dict) else {}
    lines = [
        "# Registration Quality Contract",
        "",
        f"- Status: {payload.get('status')}",
        f"- Passed: {payload.get('passed')}",
        f"- Required: {payload.get('required')}",
        f"- Output count: {summary.get('output_count')}",
        f"- Accepted count: {summary.get('accepted_count')}",
        f"- Failed count: {summary.get('failed_count')}",
        f"- Max RMS px: {summary.get('max_rms_px')}",
        f"- Min inliers: {summary.get('min_inliers')}",
        f"- Threshold max RMS px: {thresholds.get('max_rms_px')}",
        f"- Threshold min inliers: {thresholds.get('min_inliers')}",
        f"- Require all accepted: {thresholds.get('require_all_accepted')}",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    lines.extend(["", "## Outputs", ""])
    for item in payload.get("outputs") or []:
        marker = "PASS" if item.get("accepted") else "FAIL"
        lines.append(
            f"- {marker}: {item.get('frame_id')} status={item.get('status')} "
            f"rms={item.get('rms_px')} inliers={item.get('inliers')}"
        )
    Path(markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
