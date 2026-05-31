from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    return payload if isinstance(payload, dict) else None


def _append_unique(values: list[str], value: Any) -> None:
    text = str(value)
    if text and text not in values:
        values.append(text)


def _extend_unique(values: list[str], items: Any) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        _append_unique(values, item)


def _as_weight(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _registration_rows(registration: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not registration:
        return []
    rows = registration.get("registration_results")
    if rows is None:
        rows = registration.get("results")
    return rows if isinstance(rows, list) else []


def _add_frame(
    frames: list[dict[str, Any]],
    seen: set[str],
    frame_id: Any,
    *,
    filt: Any = None,
    path: Any = None,
) -> None:
    if frame_id is None:
        return
    text = str(frame_id)
    if not text or text in seen:
        return
    seen.add(text)
    frames.append({"frame_id": text, "filter": filt, "input_path": path})


def _input_frames(
    plan: dict[str, Any] | None,
    calibration: dict[str, Any] | None,
    quality: dict[str, Any] | None,
    registration: dict[str, Any] | None,
    warp: dict[str, Any] | None,
    local_norm: dict[str, Any] | None,
    integration: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    seen: set[str] = set()

    for frame in (plan or {}).get("frames", []):
        if str(frame.get("frame_type") or "").lower() != "light":
            continue
        _add_frame(frames, seen, frame.get("id"), filt=frame.get("filter"), path=frame.get("path"))

    for item in (calibration or {}).get("calibrated_lights", []):
        _add_frame(frames, seen, item.get("frame_id"), path=item.get("source_path") or item.get("path"))
    for item in (quality or {}).get("frame_quality", []):
        _add_frame(frames, seen, item.get("frame_id"), filt=item.get("filter"))
    for item in _registration_rows(registration):
        _add_frame(frames, seen, item.get("frame_id"))
    for item in (warp or {}).get("warp_results", []):
        _add_frame(frames, seen, item.get("frame_id"))
    for item in (warp or {}).get("skipped_frames", []):
        _add_frame(frames, seen, item.get("frame_id"))
    for item in (local_norm or {}).get("local_norm_results", []):
        _add_frame(frames, seen, item.get("frame_id"))
    for frame_id in (integration or {}).get("frame_weights", {}):
        _add_frame(frames, seen, frame_id)

    return frames


def _final_status(
    *,
    quality_gate_status: str,
    registration_status: str,
    warp_status: str,
    local_norm_status: str,
    integration_status: str,
    has_integration: bool,
) -> str:
    if integration_status == "used":
        return "integrated"
    if integration_status == "zero_weight":
        return "zero_weight"
    if quality_gate_status == "rejected" or registration_status == "quality_rejected":
        return "quality_rejected"
    if registration_status in {"failed", "rejected", "missing", "excluded"}:
        return "registration_rejected"
    if warp_status == "skipped":
        return "warp_skipped"
    if local_norm_status in {"empty", "skipped_zero_weight"}:
        return "local_norm_rejected"
    if has_integration:
        return "not_integrated"
    return "pending"


def _status_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key) or "unknown") for row in rows))


def build_frame_accounting(
    run_dir: str | Path,
    out_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a per-light audit ledger across quality, registration, warp, LN, and integration."""

    run = Path(run_dir)
    plan = _read_optional_json(run / "processing_plan.json")
    calibration = _read_optional_json(run / "calibration_artifacts.json")
    quality = _read_optional_json(run / "frame_quality.json")
    registration = _read_optional_json(run / "registration_results.json")
    warp = _read_optional_json(run / "warp_results.json")
    local_norm = _read_optional_json(run / "local_norm_results.json")
    integration = _read_optional_json(run / "integration_results.json")
    resident = _read_optional_json(run / "resident_artifacts.json")

    quality_by_id = {
        str(item.get("frame_id")): item for item in (quality or {}).get("frame_quality", [])
    }
    calibration_by_id = {
        str(item.get("frame_id")): item for item in (calibration or {}).get("calibrated_lights", [])
    }
    registration_by_id = {str(item.get("frame_id")): item for item in _registration_rows(registration)}
    warp_by_id = {str(item.get("frame_id")): item for item in (warp or {}).get("warp_results", [])}
    warp_skipped_by_id = {
        str(item.get("frame_id")): item for item in (warp or {}).get("skipped_frames", [])
    }
    local_norm_by_id = {
        str(item.get("frame_id")): item for item in (local_norm or {}).get("local_norm_results", [])
    }
    frame_weights = (integration or {}).get("frame_weights", {})
    has_resident_integration = (integration or {}).get("source_stage") == "resident_calibrated_stack"

    rows: list[dict[str, Any]] = []
    for base in _input_frames(plan, calibration, quality, registration, warp, local_norm, integration):
        frame_id = str(base["frame_id"])
        reasons: list[str] = []
        warnings: list[str] = []

        calibration_row = calibration_by_id.get(frame_id)
        if calibration_row:
            calibration_status = str(calibration_row.get("status") or "calibrated")
            _extend_unique(warnings, calibration_row.get("warnings", []))
        elif has_resident_integration:
            calibration_status = "resident_in_vram"
        elif calibration:
            calibration_status = "missing"
            _append_unique(reasons, "missing calibrated-light artifact")
        else:
            calibration_status = "not_run"

        quality_row = quality_by_id.get(frame_id)
        if quality_row:
            quality_gate_status = str(quality_row.get("quality_gate_status") or "not_recorded")
            reference_candidate = quality_row.get("reference_candidate")
            quality_score = quality_row.get("quality_score", quality_row.get("weight"))
            _extend_unique(reasons, quality_row.get("quality_gate_warnings", []))
            _extend_unique(warnings, quality_row.get("warnings", []))
        elif quality:
            quality_gate_status = "missing"
            reference_candidate = None
            quality_score = None
        else:
            quality_gate_status = "not_run"
            reference_candidate = None
            quality_score = None

        registration_row = registration_by_id.get(frame_id)
        if registration_row:
            registration_status = str(registration_row.get("status") or "unknown")
            registration_source = registration_row.get("registration_solution_source")
            _extend_unique(warnings, registration_row.get("warnings", []))
        elif registration:
            registration_status = "missing"
            registration_source = None
        else:
            registration_status = "not_run"
            registration_source = None

        if frame_id in warp_by_id:
            warp_status = "accepted"
            warp_reason = None
        elif frame_id in warp_skipped_by_id:
            warp_status = "skipped"
            warp_reason = warp_skipped_by_id[frame_id].get("reason")
            _append_unique(reasons, warp_reason)
            _extend_unique(warnings, warp_skipped_by_id[frame_id].get("warnings", []))
        elif has_resident_integration:
            warp_status = "resident_in_vram"
            warp_reason = None
        elif warp:
            warp_status = "not_requested" if registration_status not in {"ok", "reference"} else "missing"
            warp_reason = None
        else:
            warp_status = "not_run"
            warp_reason = None

        if frame_id in local_norm_by_id:
            local_norm_status = str(local_norm_by_id[frame_id].get("status") or "ok")
            _extend_unique(warnings, local_norm_by_id[frame_id].get("warnings", []))
        elif local_norm and local_norm.get("source_stage") == "resident_calibrated_stack":
            local_norm_status = "resident_applied" if local_norm.get("enabled") else "disabled"
        elif local_norm:
            local_norm_status = "missing"
        else:
            local_norm_status = "not_run"

        integration_weight = _as_weight(frame_weights.get(frame_id))
        if integration_weight is None:
            integration_status = "not_integrated" if integration else "not_run"
        elif integration_weight > 0.0:
            integration_status = "used"
        else:
            integration_status = "zero_weight"
            _append_unique(reasons, "integration weight is zero")

        final_status = _final_status(
            quality_gate_status=quality_gate_status,
            registration_status=registration_status,
            warp_status=warp_status,
            local_norm_status=local_norm_status,
            integration_status=integration_status,
            has_integration=bool(integration),
        )

        rows.append(
            {
                "frame_id": frame_id,
                "filter": base.get("filter"),
                "input_path": base.get("input_path"),
                "calibration_status": calibration_status,
                "quality_gate_status": quality_gate_status,
                "reference_candidate": reference_candidate,
                "quality_score": quality_score,
                "registration_status": registration_status,
                "registration_source": registration_source,
                "warp_status": warp_status,
                "warp_reason": warp_reason,
                "local_norm_status": local_norm_status,
                "integration_status": integration_status,
                "integration_weight": integration_weight,
                "final_status": final_status,
                "reasons": reasons,
                "warnings": warnings,
            }
        )

    final_counts = _status_counts(rows, "final_status")
    summary = {
        "input_light_frames": len(rows),
        "calibrated_frames": sum(1 for row in rows if row["calibration_status"] == "calibrated"),
        "resident_calibrated_frames": sum(
            1 for row in rows if row["calibration_status"] == "resident_in_vram"
        ),
        "quality_accepted_frames": sum(
            1 for row in rows if row["quality_gate_status"] == "accepted"
        ),
        "quality_rejected_frames": sum(
            1 for row in rows if row["quality_gate_status"] == "rejected"
        ),
        "registration_accepted_frames": sum(
            1 for row in rows if row["registration_status"] in {"ok", "reference"}
        ),
        "warp_accepted_frames": sum(1 for row in rows if row["warp_status"] == "accepted"),
        "warp_skipped_frames": sum(1 for row in rows if row["warp_status"] == "skipped"),
        "integrated_frames": final_counts.get("integrated", 0),
        "zero_weight_frames": final_counts.get("zero_weight", 0),
        "not_integrated_frames": final_counts.get("not_integrated", 0),
        "final_status_counts": final_counts,
    }
    payload = {
        "schema_version": 1,
        "artifact": "frame_accounting",
        "sources": {
            "plan": bool(plan),
            "calibration": bool(calibration),
            "quality": bool(quality),
            "registration": bool(registration),
            "warp": bool(warp),
            "local_norm": bool(local_norm),
            "integration": bool(integration),
            "resident": bool(resident),
        },
        "integration_source_stage": (integration or {}).get("source_stage"),
        "summary": summary,
        "frames": rows,
    }
    write_json(out_path or (run / "frame_accounting.json"), payload)
    return payload
