from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

from glass.io.json_io import read_json, write_json


_TRIANGLE_PREFIX = "triangle_"
_SIMILARITY_PREFIX = "similarity_"


def _json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _run_dir_from_input(run_or_file: str | Path) -> Path:
    path = Path(run_or_file)
    return path if path.is_dir() else path.parent


def _registration_path(run_or_file: str | Path) -> Path:
    path = Path(run_or_file)
    return path / "registration_results.json" if path.is_dir() else path


def _resident_artifacts_path(run_or_file: str | Path) -> Path:
    run = _run_dir_from_input(run_or_file)
    return run / "resident_artifacts.json"


def _registration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if rows is None:
        rows = payload.get("results")
    return [dict(row) for row in rows] if isinstance(rows, list) else []


def _literal_or_string(value: str) -> Any:
    text = value.strip()
    if text == "":
        return ""
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        pass
    try:
        if any(marker in text for marker in (".", "e", "E")):
            return float(text)
        return int(text)
    except ValueError:
        return text


def _warning_items(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    parsed: dict[str, Any] = {}
    raw = row.get("warnings") if isinstance(row.get("warnings"), list) else []
    malformed: list[str] = []
    for item in raw:
        text = str(item)
        if "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if not key.startswith((_TRIANGLE_PREFIX, _SIMILARITY_PREFIX)):
            continue
        try:
            parsed[key] = _literal_or_string(value)
        except Exception as exc:  # pragma: no cover - defensive for user artifacts
            malformed.append(f"{key}: {exc}")
    return parsed, malformed


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and number not in (float("inf"), float("-inf")) else None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _number_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "count": len(values),
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
    }


def _trial_summary(trials: Any) -> dict[str, Any]:
    if not isinstance(trials, list):
        return {
            "available": False,
            "trial_count": 0,
            "status_counts": {},
            "ok_trial_count": 0,
            "best_inliers": None,
            "best_rms_px": None,
            "total_candidate_count": 0,
        }
    status_counts: Counter[str] = Counter()
    inliers: list[int] = []
    rms_values: list[float] = []
    candidate_counts: list[int] = []
    for trial in trials:
        if not isinstance(trial, dict):
            continue
        status_counts[str(trial.get("status") or "unknown")] += 1
        trial_inliers = _int_or_none(trial.get("inliers"))
        if trial_inliers is not None:
            inliers.append(trial_inliers)
        trial_rms = _float_or_none(trial.get("rms_px"))
        if trial_rms is not None:
            rms_values.append(trial_rms)
        candidate_count = _int_or_none(trial.get("candidate_count"))
        if candidate_count is not None:
            candidate_counts.append(candidate_count)
    return {
        "available": True,
        "trial_count": len(trials),
        "status_counts": dict(status_counts),
        "ok_trial_count": int(status_counts.get("ok", 0)),
        "best_inliers": max(inliers, default=None),
        "best_rms_px": min(rms_values, default=None),
        "total_candidate_count": sum(candidate_counts),
        "max_candidate_count": max(candidate_counts, default=None),
    }


def _frame_candidate_audit(row: dict[str, Any]) -> dict[str, Any]:
    warnings, malformed = _warning_items(row)
    raw_warnings = row.get("warnings") if isinstance(row.get("warnings"), list) else []
    is_triangle = any(key.startswith(_TRIANGLE_PREFIX) for key in warnings) or row.get("transform_model") == "similarity_cuda_triangle"
    trials = warnings.get("triangle_trials")
    trial_summary = _trial_summary(trials)
    candidate_count = _int_or_none(warnings.get("triangle_candidate_count"))
    pixel_rms = _float_or_none(warnings.get("triangle_pixel_rms_adu_batch", warnings.get("triangle_pixel_rms_adu")))
    pixel_ncc = _float_or_none(warnings.get("triangle_pixel_ncc_batch", warnings.get("triangle_pixel_ncc")))
    fit_rms = _float_or_none(warnings.get("triangle_fit_rms_px", row.get("rms_px")))
    agreement_score = _float_or_none(warnings.get("triangle_agreement_score"))
    agreement_status = warnings.get("triangle_agreement_status")
    agreement_reason = warnings.get("triangle_agreement_reason")
    agreement_rms_scale = _float_or_none(warnings.get("triangle_agreement_rms_scale"))
    agreement_min_score = _float_or_none(warnings.get("triangle_min_agreement_score"))
    status = str(row.get("status") or "unknown")
    failure_reasons: list[str] = []
    if status == "failed":
        failure_reasons.append("registration_status_failed")
    quality = warnings.get("triangle_quality_gate_status")
    if quality == "failed":
        failure_reasons.append("quality_gate_failed")
    if agreement_status == "failed":
        failure_reasons.append("agreement_gate_failed")
    if any("no accepted fit" in str(item).lower() for item in raw_warnings):
        failure_reasons.append("no_accepted_fit")
    if candidate_count is not None and candidate_count <= 0 and status not in {"reference", "excluded"}:
        failure_reasons.append("zero_descriptor_candidates")
    if malformed:
        failure_reasons.append("malformed_warning_values")
    return {
        "frame_id": str(row.get("frame_id")),
        "status": status,
        "is_triangle": bool(is_triangle),
        "matched_stars": _int_or_none(row.get("matched_stars")),
        "inliers": _int_or_none(row.get("inliers")),
        "rms_px": _float_or_none(row.get("rms_px")),
        "threshold_mode": warnings.get("triangle_threshold_mode"),
        "selected_threshold": _float_or_none(warnings.get("selected_triangle_threshold")),
        "reference_stars": _int_or_none(warnings.get("reference_stars")),
        "moving_stars": _int_or_none(warnings.get("moving_stars")),
        "reference_descriptors": _int_or_none(warnings.get("reference_descriptors")),
        "moving_descriptors": _int_or_none(warnings.get("moving_descriptors")),
        "candidate_count": candidate_count,
        "trial_summary": trial_summary,
        "descriptor_fit_best_reduction_mode": warnings.get("triangle_descriptor_fit_best_reduction_mode"),
        "descriptor_fit_batch": warnings.get("triangle_descriptor_fit_batch"),
        "pixel_refine_mode": warnings.get("triangle_pixel_refine_mode"),
        "pixel_refine_fast_coarse": warnings.get("triangle_pixel_refine_fast_coarse"),
        "pixel_refine_effective_coarse_stride": _int_or_none(
            warnings.get("triangle_pixel_refine_effective_coarse_stride")
        ),
        "pixel_refine_requested_final_stride": _int_or_none(
            warnings.get("triangle_pixel_refine_requested_final_stride")
        ),
        "fit_rms_px": fit_rms,
        "pixel_rms_adu": pixel_rms,
        "pixel_ncc": pixel_ncc,
        "quality_gate_status": quality,
        "agreement_score": agreement_score,
        "agreement_status": agreement_status,
        "agreement_reason": agreement_reason,
        "agreement_rms_scale": agreement_rms_scale,
        "agreement_min_score": agreement_min_score,
        "catalog_selector": warnings.get("triangle_catalog_selector"),
        "catalog_batch": warnings.get("triangle_catalog_batch"),
        "catalog_timing_model": warnings.get("triangle_catalog_timing_model"),
        "catalog_sort_mode": warnings.get("triangle_catalog_sort_mode"),
        "catalog_topk_mode": warnings.get("triangle_catalog_topk_mode"),
        "grid_top_per_cell": _int_or_none(warnings.get("triangle_grid_top_per_cell")),
        "nms_scan_candidates": _int_or_none(warnings.get("triangle_nms_scan_candidates")),
        "nms_min_separation_px": _float_or_none(warnings.get("triangle_nms_min_separation_px")),
        "determinism": {
            "reference_catalog_signature": warnings.get("triangle_determinism_reference_catalog_signature"),
            "moving_catalog_signature": warnings.get("triangle_determinism_moving_catalog_signature"),
            "reference_descriptor_signature": warnings.get("triangle_determinism_reference_descriptor_signature"),
            "moving_descriptor_signature": warnings.get("triangle_determinism_moving_descriptor_signature"),
            "selected_fit_signature": warnings.get("triangle_determinism_selected_fit_signature"),
            "trial_signature": warnings.get("triangle_determinism_trial_signature"),
        },
        "failure_reasons": failure_reasons,
        "parse_errors": malformed,
    }


def _resident_registration_summary(resident: dict[str, Any]) -> dict[str, Any]:
    artifacts = resident.get("artifacts") if isinstance(resident.get("artifacts"), list) else []
    if not artifacts or not isinstance(artifacts[0], dict):
        return {}
    registration = artifacts[0].get("resident_registration")
    return registration if isinstance(registration, dict) else {}


def build_resident_registration_audit(run_or_file: str | Path) -> dict[str, Any]:
    run_dir = _run_dir_from_input(run_or_file)
    registration_path = _registration_path(run_or_file)
    resident_path = _resident_artifacts_path(run_or_file)
    registration = _json_if_exists(registration_path)
    resident = _json_if_exists(resident_path)
    rows = _registration_rows(registration)
    frames = [_frame_candidate_audit(row) for row in rows]
    triangle_frames = [frame for frame in frames if frame["is_triangle"]]
    failed_triangle_frames = [
        frame for frame in triangle_frames if frame["status"] == "failed" or frame["failure_reasons"]
    ]
    status_counts = Counter(frame["status"] for frame in frames)
    candidate_counts = [
        int(frame["candidate_count"]) for frame in triangle_frames if frame.get("candidate_count") is not None
    ]
    fit_rms_values = [float(frame["fit_rms_px"]) for frame in triangle_frames if frame.get("fit_rms_px") is not None]
    pixel_rms_values = [
        float(frame["pixel_rms_adu"]) for frame in triangle_frames if frame.get("pixel_rms_adu") is not None
    ]
    pixel_ncc_values = [float(frame["pixel_ncc"]) for frame in triangle_frames if frame.get("pixel_ncc") is not None]
    agreement_score_values = [
        float(frame["agreement_score"]) for frame in triangle_frames if frame.get("agreement_score") is not None
    ]
    agreement_status_counts = Counter(
        str(frame["agreement_status"]) for frame in triangle_frames if frame.get("agreement_status") is not None
    )
    failure_counts: Counter[str] = Counter()
    for frame in failed_triangle_frames:
        for reason in frame["failure_reasons"]:
            failure_counts[str(reason)] += 1
    resident_registration = _resident_registration_summary(resident)
    registration_component_seconds = {}
    artifacts = resident.get("artifacts") if isinstance(resident.get("artifacts"), list) else []
    if artifacts and isinstance(artifacts[0], dict):
        fine_timing = artifacts[0].get("fine_timing") if isinstance(artifacts[0].get("fine_timing"), dict) else {}
        components = fine_timing.get("registration_component_seconds")
        if isinstance(components, dict):
            registration_component_seconds = {str(key): value for key, value in components.items()}
    parse_error_count = sum(len(frame["parse_errors"]) for frame in frames)
    passed = bool(rows) and parse_error_count == 0
    return {
        "schema_version": 1,
        "audit_type": "resident_registration_candidate_audit",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "run": str(run_dir),
        "registration_results": str(registration_path),
        "resident_artifacts": str(resident_path) if resident_path.exists() else None,
        "summary": {
            "frame_count": len(frames),
            "triangle_frame_count": len(triangle_frames),
            "status_counts": dict(status_counts),
            "failed_triangle_frame_count": len(failed_triangle_frames),
            "failure_reason_counts": dict(failure_counts),
            "parse_error_count": parse_error_count,
            "candidate_count_stats": _number_stats([float(item) for item in candidate_counts]),
            "fit_rms_px_stats": _number_stats(fit_rms_values),
            "pixel_rms_adu_stats": _number_stats(pixel_rms_values),
            "pixel_ncc_stats": _number_stats(pixel_ncc_values),
            "agreement_score_stats": _number_stats(agreement_score_values),
            "agreement_status_counts": dict(agreement_status_counts),
            "triangle_trial_frame_count": sum(1 for frame in triangle_frames if frame["trial_summary"]["available"]),
            "quality_gate_failed_count": failure_counts.get("quality_gate_failed", 0),
            "agreement_gate_failed_count": failure_counts.get("agreement_gate_failed", 0),
            "no_accepted_fit_count": failure_counts.get("no_accepted_fit", 0),
        },
        "resident_registration": {
            "mode": resident_registration.get("mode"),
            "active_frame_count": resident_registration.get("active_frame_count"),
            "triangle_grid_top_per_cell": resident_registration.get("triangle_grid_top_per_cell"),
            "triangle_nms_min_separation_px": resident_registration.get("triangle_nms_min_separation_px"),
            "triangle_min_agreement_score": resident_registration.get("triangle_min_agreement_score"),
            "triangle_agreement_rms_scale": resident_registration.get("triangle_agreement_rms_scale"),
            "triangle_determinism_signature_mode": resident_registration.get("triangle_determinism_signature_mode"),
            "triangle_determinism_moving_frame_count": resident_registration.get(
                "triangle_determinism_moving_frame_count"
            ),
            "triangle_determinism_trial_combined_sha256": resident_registration.get(
                "triangle_determinism_trial_combined_sha256"
            ),
        },
        "registration_component_seconds": registration_component_seconds,
        "frames": frames,
        "ranked_frames": sorted(
            triangle_frames,
            key=lambda frame: (
                0 if frame["failure_reasons"] else 1,
                -(frame.get("candidate_count") or 0),
                -(frame.get("fit_rms_px") or 0.0),
                frame["frame_id"],
            ),
        )[:50],
    }


def write_resident_registration_audit_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = audit["summary"]
    lines = [
        "# Resident Registration Candidate Audit",
        "",
        f"- Result: `{audit['status']}`",
        f"- Run: `{audit['run']}`",
        f"- Registration results: `{audit['registration_results']}`",
        f"- Frames: `{summary['frame_count']}`",
        f"- Triangle frames: `{summary['triangle_frame_count']}`",
        f"- Failed triangle frames: `{summary['failed_triangle_frame_count']}`",
        f"- Parse errors: `{summary['parse_error_count']}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in sorted(summary["status_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    if summary.get("agreement_status_counts"):
        lines.extend(["", "## Agreement Status Counts", ""])
        for key, value in sorted(summary["agreement_status_counts"].items()):
            lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Failure Reasons", ""])
    if summary["failure_reason_counts"]:
        for key, value in sorted(summary["failure_reason_counts"].items()):
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Numeric Summary", ""])
    for key in (
        "candidate_count_stats",
        "fit_rms_px_stats",
        "pixel_rms_adu_stats",
        "pixel_ncc_stats",
        "agreement_score_stats",
    ):
        stats = summary[key]
        lines.append(
            f"- `{key}`: count=`{stats['count']}`, min=`{stats['min']}`, "
            f"median=`{stats['median']}`, mean=`{stats['mean']}`, max=`{stats['max']}`"
        )
    if audit.get("registration_component_seconds"):
        lines.extend(["", "## Registration Component Seconds", ""])
        for key, value in sorted(audit["registration_component_seconds"].items()):
            lines.append(f"- `{key}`: `{value}`")
    if audit["ranked_frames"]:
        lines.extend(
            [
                "",
                "## First Ranked Frames",
                "",
                "| Frame | Status | Reasons | Candidates | Fit RMS px | Pixel RMS ADU | Pixel NCC | Agreement |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for frame in audit["ranked_frames"][:20]:
            reasons = ",".join(frame["failure_reasons"]) if frame["failure_reasons"] else "-"
            lines.append(
                f"| `{frame['frame_id']}` | `{frame['status']}` | `{reasons}` | "
                f"`{frame.get('candidate_count')}` | `{frame.get('fit_rms_px')}` | "
                f"`{frame.get('pixel_rms_adu')}` | `{frame.get('pixel_ncc')}` | "
                f"`{frame.get('agreement_score')}` |"
            )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_registration_audit(
    out: str | Path,
    audit: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, audit)
    if markdown:
        write_resident_registration_audit_markdown(markdown, audit)
