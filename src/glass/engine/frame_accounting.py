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


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _contract_sources(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _registration_rows(registration: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not registration:
        return []
    rows = registration.get("registration_results")
    if rows is None:
        rows = registration.get("results")
    return rows if isinstance(rows, list) else []


def _resident_frame_mask_rows(resident_frame_masks: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not resident_frame_masks:
        return []
    rows: list[dict[str, Any]] = []
    for group in resident_frame_masks.get("groups") or []:
        if not isinstance(group, dict):
            continue
        for row in group.get("rows") or []:
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _resident_dq_lifecycle_groups(
    resident_dq_lifecycle: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not resident_dq_lifecycle:
        return []
    groups = resident_dq_lifecycle.get("groups")
    if not isinstance(groups, list):
        return []
    return [group for group in groups if isinstance(group, dict)]


def _resident_dq_lifecycle_group_for_filter(
    groups: list[dict[str, Any]],
    filt: Any,
) -> dict[str, Any]:
    if not groups:
        return {}
    text = str(filt or "")
    for group in groups:
        if str(group.get("filter") or "") == text:
            return group
    return groups[0] if len(groups) == 1 else {}


def _local_norm_rows(local_norm: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not local_norm:
        return []
    rows: list[dict[str, Any]] = []
    for item in local_norm.get("local_norm_results") or []:
        if isinstance(item, dict):
            rows.append(item)
    for group in local_norm.get("groups") or []:
        if not isinstance(group, dict):
            continue
        for item in group.get("frame_results") or []:
            if isinstance(item, dict):
                rows.append(item)
    return rows


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
    for item in _local_norm_rows(local_norm):
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
    integration_conflicts: list[dict[str, str]] | None = None,
) -> str:
    if integration_status == "used" and integration_conflicts:
        return "integration_conflict"
    if integration_status == "used":
        return "integrated"
    if quality_gate_status == "rejected" or registration_status == "quality_rejected":
        return "quality_rejected"
    if registration_status in {"failed", "rejected", "missing", "excluded"}:
        return "registration_rejected"
    if warp_status == "skipped":
        return "warp_skipped"
    if local_norm_status in {"empty", "skipped_zero_weight"}:
        return "local_norm_rejected"
    if integration_status == "zero_weight":
        return "zero_weight"
    if has_integration:
        return "not_integrated"
    return "pending"


def _integration_conflicts(
    *,
    quality_gate_status: str,
    registration_status: str,
    warp_status: str,
    local_norm_status: str,
    integration_status: str,
) -> list[dict[str, str]]:
    if integration_status != "used":
        return []
    conflicts: list[dict[str, str]] = []
    if quality_gate_status == "rejected":
        conflicts.append(
            {
                "stage": "quality",
                "status": quality_gate_status,
                "reason": "positive integration weight for quality-rejected frame",
            }
        )
    if registration_status in {"quality_rejected", "failed", "rejected", "missing", "excluded"}:
        conflicts.append(
            {
                "stage": "registration",
                "status": registration_status,
                "reason": "positive integration weight for non-accepted registration frame",
            }
        )
    if warp_status in {"skipped", "missing"}:
        conflicts.append(
            {
                "stage": "warp",
                "status": warp_status,
                "reason": "positive integration weight for non-warped frame",
            }
        )
    if local_norm_status in {"empty", "skipped_zero_weight", "missing"}:
        conflicts.append(
            {
                "stage": "local_normalization",
                "status": local_norm_status,
                "reason": "positive integration weight for local-normalization rejected frame",
            }
        )
    return conflicts


def _status_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key) or "unknown") for row in rows))


def _primary_exception(row: dict[str, Any]) -> tuple[str, str]:
    final_status = str(row.get("final_status") or "unknown")
    reasons = row.get("reasons") if isinstance(row.get("reasons"), list) else []
    warnings = row.get("warnings") if isinstance(row.get("warnings"), list) else []
    if final_status == "zero_weight":
        return "integration", reasons[0] if reasons else "integration weight is zero"
    if final_status == "quality_rejected":
        return "quality", reasons[0] if reasons else "quality gate rejected frame"
    if final_status == "registration_rejected":
        return "registration", warnings[0] if warnings else "registration did not accept frame"
    if final_status == "warp_skipped":
        return "warp", str(row.get("warp_reason") or "warp skipped frame")
    if final_status == "local_norm_rejected":
        return "local_normalization", warnings[0] if warnings else "local normalization rejected frame"
    if final_status == "integration_conflict":
        conflicts = row.get("integration_conflicts")
        if isinstance(conflicts, list) and conflicts:
            first = conflicts[0]
            if isinstance(first, dict):
                stage = str(first.get("stage") or "integration")
                reason = str(
                    first.get("reason")
                    or "positive integration weight conflicts with upstream rejection"
                )
                return stage, reason
        return "integration", "positive integration weight conflicts with upstream rejection"
    if final_status == "not_integrated":
        return "integration", reasons[0] if reasons else "frame was not present in integration weights"
    return final_status, reasons[0] if reasons else (warnings[0] if warnings else final_status)


def _exception_frames(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exceptions: list[dict[str, Any]] = []
    for row in rows:
        if row.get("final_status") == "integrated":
            continue
        reasons = row.get("reasons") if isinstance(row.get("reasons"), list) else []
        warnings = row.get("warnings") if isinstance(row.get("warnings"), list) else []
        primary_stage, primary_reason = _primary_exception(row)
        exceptions.append(
            {
                "frame_id": row.get("frame_id"),
                "filter": row.get("filter"),
                "final_status": row.get("final_status"),
                "primary_stage": primary_stage,
                "primary_reason": primary_reason,
                "quality_gate_status": row.get("quality_gate_status"),
                "resident_frame_mask_status": row.get("resident_frame_mask_status"),
                "resident_frame_mask_categories": row.get("resident_frame_mask_categories"),
                "resident_dq_mask_contract_status": row.get("resident_dq_mask_contract_status"),
                "resident_dq_mask_contract_passed": row.get("resident_dq_mask_contract_passed"),
                "resident_dq_mask_contract_sources": row.get("resident_dq_mask_contract_sources"),
                "resident_dq_lifecycle_status": row.get("resident_dq_lifecycle_status"),
                "resident_dq_lifecycle_passed": row.get("resident_dq_lifecycle_passed"),
                "registration_status": row.get("registration_status"),
                "warp_status": row.get("warp_status"),
                "local_norm_status": row.get("local_norm_status"),
                "integration_status": row.get("integration_status"),
                "integration_weight": row.get("integration_weight"),
                "reason_count": len(reasons),
                "warning_count": len(warnings),
                "input_path": row.get("input_path"),
            }
        )
    return exceptions


def _exception_summary(exceptions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(exceptions),
        "final_status_counts": _status_counts(exceptions, "final_status"),
        "primary_stage_counts": _status_counts(exceptions, "primary_stage"),
    }


def build_frame_accounting(
    run_dir: str | Path,
    out_path: str | Path | None = None,
    *,
    compact_json: bool = False,
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
    resident_frame_masks = _read_optional_json(run / "resident_frame_masks.json")
    resident_dq_lifecycle = _read_optional_json(run / "resident_dq_lifecycle.json")

    quality_by_id = {
        str(item.get("frame_id")): item for item in (quality or {}).get("frame_quality", [])
    }
    calibration_by_id = {
        str(item.get("frame_id")): item for item in (calibration or {}).get("calibrated_lights", [])
    }
    calibration_artifact_type = (calibration or {}).get("artifact_type")
    resident_native_calibration = (
        calibration_artifact_type == "resident_cuda_calibration_artifacts"
        or (calibration or {}).get("source_stage") == "resident_calibrated_stack"
    )
    calibration_master_count = len((calibration or {}).get("masters") or {})
    resident_calibrated_light_ledger_count = sum(
        1
        for item in (calibration or {}).get("calibrated_lights", [])
        if item.get("status") == "resident_in_vram"
        or item.get("backend") == "cuda_resident_stack"
        or item.get("source_stage") == "resident_calibrated_stack"
    )
    registration_by_id = {str(item.get("frame_id")): item for item in _registration_rows(registration)}
    resident_frame_mask_by_id = {
        str(item.get("frame_id")): item
        for item in _resident_frame_mask_rows(resident_frame_masks)
        if item.get("frame_id") is not None
    }
    resident_dq_lifecycle_groups = _resident_dq_lifecycle_groups(resident_dq_lifecycle)
    resident_dq_lifecycle_summary = (
        resident_dq_lifecycle.get("summary")
        if isinstance((resident_dq_lifecycle or {}).get("summary"), dict)
        else {}
    )
    warp_by_id = {str(item.get("frame_id")): item for item in (warp or {}).get("warp_results", [])}
    warp_skipped_by_id = {
        str(item.get("frame_id")): item for item in (warp or {}).get("skipped_frames", [])
    }
    local_norm_by_id = {
        str(item.get("frame_id")): item
        for item in _local_norm_rows(local_norm)
        if item.get("frame_id") is not None
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
            calibration_source_stage = calibration_row.get("source_stage")
            calibration_backend = calibration_row.get("backend")
            resident_stack_index = calibration_row.get("resident_stack_index")
            resident_output_index = calibration_row.get("resident_output_index")
            resident_master_path = calibration_row.get("resident_master_path")
            resident_source_dq_contract = _dict_or_empty(calibration_row.get("source_dq_contract"))
            resident_calibrated_light_frame_mask_contract = _dict_or_empty(
                calibration_row.get("frame_mask_contract")
            )
            resident_dq_mask_contract = _dict_or_empty(
                calibration_row.get("resident_dq_mask_contract")
            )
            _extend_unique(warnings, calibration_row.get("warnings", []))
        elif has_resident_integration:
            calibration_status = "resident_in_vram"
            calibration_source_stage = "resident_calibrated_stack"
            calibration_backend = "cuda_resident_stack"
            resident_stack_index = None
            resident_output_index = None
            resident_master_path = None
            resident_source_dq_contract = {}
            resident_calibrated_light_frame_mask_contract = {}
            resident_dq_mask_contract = {}
        elif calibration:
            calibration_status = "missing"
            calibration_source_stage = None
            calibration_backend = None
            resident_stack_index = None
            resident_output_index = None
            resident_master_path = None
            resident_source_dq_contract = {}
            resident_calibrated_light_frame_mask_contract = {}
            resident_dq_mask_contract = {}
            _append_unique(reasons, "missing calibrated-light artifact")
        else:
            calibration_status = "not_run"
            calibration_source_stage = None
            calibration_backend = None
            resident_stack_index = None
            resident_output_index = None
            resident_master_path = None
            resident_source_dq_contract = {}
            resident_calibrated_light_frame_mask_contract = {}
            resident_dq_mask_contract = {}

        resident_source_dq_contract_available = bool(resident_source_dq_contract.get("available"))
        resident_calibrated_light_frame_mask_contract_available = bool(
            resident_calibrated_light_frame_mask_contract.get("available")
        )
        resident_dq_mask_contract_available = bool(
            resident_dq_mask_contract.get("contract_type")
            == "resident_calibrated_light_dq_mask_contract"
        )
        resident_dq_mask_contract_passed = (
            bool(resident_dq_mask_contract.get("passed"))
            if resident_dq_mask_contract_available
            else None
        )
        resident_dq_mask_contract_status = (
            resident_dq_mask_contract.get("status")
            if resident_dq_mask_contract_available
            else "missing"
            if resident_native_calibration
            else "not_applicable"
        )
        resident_dq_mask_contract_sources = _contract_sources(
            resident_dq_mask_contract.get("contract_sources")
        )
        resident_dq_frame_mask_sources = _contract_sources(
            resident_dq_mask_contract.get("frame_mask_sources")
        )

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

        resident_frame_mask_row = resident_frame_mask_by_id.get(frame_id)
        if resident_frame_mask_row:
            frame_mask_status = str(resident_frame_mask_row.get("mask_status") or "unknown")
            frame_mask_categories = [
                str(item) for item in (resident_frame_mask_row.get("mask_categories") or [])
            ]
            frame_mask_reasons = [
                str(item) for item in (resident_frame_mask_row.get("mask_reasons") or [])
            ]
            frame_mask_auditable = bool(resident_frame_mask_row.get("auditable"))
            if "registration_quality" in frame_mask_categories and quality_gate_status in {
                "missing",
                "not_run",
                "not_recorded",
            }:
                quality_gate_status = "rejected"
            _extend_unique(reasons, frame_mask_reasons)
        elif resident_frame_masks:
            frame_mask_status = "missing"
            frame_mask_categories = []
            frame_mask_reasons = []
            frame_mask_auditable = False
        else:
            frame_mask_status = "not_run"
            frame_mask_categories = []
            frame_mask_reasons = []
            frame_mask_auditable = None

        resident_dq_lifecycle_group = _resident_dq_lifecycle_group_for_filter(
            resident_dq_lifecycle_groups,
            base.get("filter"),
        )
        resident_dq_lifecycle_available = bool(resident_dq_lifecycle_group)
        resident_dq_lifecycle_passed = (
            bool(resident_dq_lifecycle_group.get("passed"))
            if resident_dq_lifecycle_available
            else None
        )
        resident_dq_lifecycle_status = (
            resident_dq_lifecycle_group.get("status")
            if resident_dq_lifecycle_available
            else "missing"
            if resident_dq_lifecycle
            else "not_applicable"
        )

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

        integration_conflicts = _integration_conflicts(
            quality_gate_status=quality_gate_status,
            registration_status=registration_status,
            warp_status=warp_status,
            local_norm_status=local_norm_status,
            integration_status=integration_status,
        )
        if integration_conflicts:
            _append_unique(
                reasons,
                "positive integration weight conflicts with upstream rejection",
            )

        final_status = _final_status(
            quality_gate_status=quality_gate_status,
            registration_status=registration_status,
            warp_status=warp_status,
            local_norm_status=local_norm_status,
            integration_status=integration_status,
            has_integration=bool(integration),
            integration_conflicts=integration_conflicts,
        )

        rows.append(
            {
                "frame_id": frame_id,
                "filter": base.get("filter"),
                "input_path": base.get("input_path"),
                "calibration_status": calibration_status,
                "calibration_source_stage": calibration_source_stage,
                "calibration_backend": calibration_backend,
                "resident_stack_index": resident_stack_index,
                "resident_output_index": resident_output_index,
                "resident_master_path": resident_master_path,
                "resident_source_dq_contract_available": resident_source_dq_contract_available,
                "resident_source_dq_contract_passed": (
                    bool(resident_source_dq_contract.get("passed"))
                    if resident_source_dq_contract_available
                    else None
                ),
                "resident_source_dq_contract_status": resident_source_dq_contract.get("status"),
                "resident_source_dq_execution_route": resident_source_dq_contract.get("execution_route"),
                "resident_dq_mask_contract_available": resident_dq_mask_contract_available,
                "resident_dq_mask_contract_status": resident_dq_mask_contract_status,
                "resident_dq_mask_contract_passed": resident_dq_mask_contract_passed,
                "resident_dq_mask_contract_sources": resident_dq_mask_contract_sources,
                "resident_dq_frame_mask_sources": resident_dq_frame_mask_sources,
                "resident_calibrated_light_frame_mask_contract_available": (
                    resident_calibrated_light_frame_mask_contract_available
                ),
                "resident_calibrated_light_frame_mask_contract_passed": (
                    bool(resident_calibrated_light_frame_mask_contract.get("passed"))
                    if resident_calibrated_light_frame_mask_contract_available
                    else None
                ),
                "quality_gate_status": quality_gate_status,
                "reference_candidate": reference_candidate,
                "quality_score": quality_score,
                "resident_frame_mask_status": frame_mask_status,
                "resident_frame_mask_categories": frame_mask_categories,
                "resident_frame_mask_reasons": frame_mask_reasons,
                "resident_frame_mask_auditable": frame_mask_auditable,
                "resident_dq_lifecycle_available": resident_dq_lifecycle_available,
                "resident_dq_lifecycle_status": resident_dq_lifecycle_status,
                "resident_dq_lifecycle_passed": resident_dq_lifecycle_passed,
                "resident_dq_lifecycle_filter": resident_dq_lifecycle_group.get("filter"),
                "resident_dq_lifecycle_active_frame_count": resident_dq_lifecycle_group.get(
                    "active_frame_count"
                ),
                "resident_dq_lifecycle_masked_frame_count": resident_dq_lifecycle_group.get(
                    "masked_frame_count"
                ),
                "resident_dq_lifecycle_source_input_samples": resident_dq_lifecycle_group.get(
                    "source_input_samples"
                ),
                "registration_status": registration_status,
                "registration_source": registration_source,
                "warp_status": warp_status,
                "warp_reason": warp_reason,
                "local_norm_status": local_norm_status,
                "integration_status": integration_status,
                "integration_weight": integration_weight,
                "integration_conflict_count": len(integration_conflicts),
                "integration_conflicts": integration_conflicts,
                "final_status": final_status,
                "reasons": reasons,
                "warnings": warnings,
            }
        )

    final_counts = _status_counts(rows, "final_status")
    integration_counts = _status_counts(rows, "integration_status")
    exceptions = _exception_frames(rows)
    resident_dq_mask_contract_rows = [
        row for row in rows if row.get("resident_dq_mask_contract_available") is True
    ]
    resident_dq_lifecycle_rows = [
        row for row in rows if row.get("resident_dq_lifecycle_available") is True
    ]
    resident_dq_lifecycle_failed_rows = [
        row for row in resident_dq_lifecycle_rows if row.get("resident_dq_lifecycle_passed") is not True
    ]
    summary = {
        "input_light_frames": len(rows),
        "calibrated_frames": sum(1 for row in rows if row["calibration_status"] == "calibrated"),
        "resident_calibrated_frames": sum(
            1 for row in rows if row["calibration_status"] == "resident_in_vram"
        ),
        "resident_native_calibration_artifact": resident_native_calibration,
        "calibration_artifact_type": calibration_artifact_type,
        "calibration_master_count": calibration_master_count,
        "resident_calibrated_light_ledger_rows": resident_calibrated_light_ledger_count,
        "resident_calibrated_light_dq_contract_rows": len(resident_dq_mask_contract_rows),
        "resident_calibrated_light_dq_contract_passed": sum(
            1 for row in resident_dq_mask_contract_rows if row["resident_dq_mask_contract_passed"] is True
        ),
        "resident_calibrated_light_dq_contract_failed": sum(
            1 for row in resident_dq_mask_contract_rows if row["resident_dq_mask_contract_passed"] is not True
        ),
        "resident_source_dq_contract_rows": sum(
            1 for row in rows if row["resident_source_dq_contract_available"] is True
        ),
        "resident_frame_mask_contract_rows": sum(
            1
            for row in rows
            if row["resident_calibrated_light_frame_mask_contract_available"] is True
        ),
        "resident_dq_mask_contract_sources": sorted(
            {
                source
                for row in resident_dq_mask_contract_rows
                for source in row["resident_dq_mask_contract_sources"]
            }
        ),
        "resident_dq_frame_mask_sources": sorted(
            {
                source
                for row in resident_dq_mask_contract_rows
                for source in row["resident_dq_frame_mask_sources"]
            }
        ),
        "resident_dq_lifecycle_present": bool(resident_dq_lifecycle),
        "resident_dq_lifecycle_status": (resident_dq_lifecycle_summary or {}).get("status"),
        "resident_dq_lifecycle_passed": (resident_dq_lifecycle_summary or {}).get("passed"),
        "resident_dq_lifecycle_group_count": len(resident_dq_lifecycle_groups),
        "resident_dq_lifecycle_rows": len(resident_dq_lifecycle_rows),
        "resident_dq_lifecycle_passed_rows": len(resident_dq_lifecycle_rows)
        - len(resident_dq_lifecycle_failed_rows),
        "resident_dq_lifecycle_failed_rows": len(resident_dq_lifecycle_failed_rows),
        "resident_dq_lifecycle_active_frames": (resident_dq_lifecycle_summary or {}).get(
            "active_frame_count"
        ),
        "resident_dq_lifecycle_masked_frames": (resident_dq_lifecycle_summary or {}).get(
            "masked_frame_count"
        ),
        "resident_dq_lifecycle_source_input_samples": sum(
            int(group.get("source_input_samples") or 0) for group in resident_dq_lifecycle_groups
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
        "zero_weight_frames": integration_counts.get("zero_weight", 0),
        "resident_frame_mask_active_frames": sum(
            1 for row in rows if row["resident_frame_mask_status"] == "active"
        ),
        "resident_frame_mask_masked_frames": sum(
            1 for row in rows if row["resident_frame_mask_status"] == "masked"
        ),
        "resident_frame_mask_unaudited_frames": sum(
            1
            for row in rows
            if row["resident_frame_mask_status"] == "masked"
            and row["resident_frame_mask_auditable"] is False
        ),
        "integration_conflict_frames": final_counts.get("integration_conflict", 0),
        "not_integrated_frames": final_counts.get("not_integrated", 0),
        "final_status_counts": final_counts,
        "integration_status_counts": integration_counts,
        "exception_frames": len(exceptions),
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
            "resident_frame_masks": bool(resident_frame_masks),
            "resident_dq_lifecycle": bool(resident_dq_lifecycle),
            "resident_calibrated_light_dq_ledger": bool(resident_dq_mask_contract_rows),
        },
        "calibration_artifact_type": calibration_artifact_type,
        "resident_native_calibration_artifact": resident_native_calibration,
        "integration_source_stage": (integration or {}).get("source_stage"),
        "summary": summary,
        "exception_summary": _exception_summary(exceptions),
        "exception_frames": exceptions,
        "frames": rows,
    }
    write_json(out_path or (run / "frame_accounting.json"), payload, compact=compact_json)
    return payload
