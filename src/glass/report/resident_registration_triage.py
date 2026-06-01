from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json


_SIGNATURE_KEYS = (
    "reference_catalog_signature",
    "reference_descriptor_signature",
    "moving_catalog_signature",
    "moving_descriptor_signature",
    "selected_fit_signature",
    "trial_signature",
)


def _load_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _variant_id(payload: dict[str, Any], path: str | Path) -> str:
    value = payload.get("variant_id")
    if value:
        return str(value)
    name = Path(path).stem
    suffix = "_candidate_audit"
    return name[: -len(suffix)] if name.endswith(suffix) else name


def _frames_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    frames = payload.get("frames")
    if not isinstance(frames, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        frame_id = str(frame.get("frame_id") or "")
        if frame_id:
            result[frame_id] = frame
    return result


def _failure_reasons(frame: dict[str, Any] | None) -> list[str]:
    if not frame:
        return []
    reasons = frame.get("failure_reasons")
    return [str(item) for item in reasons] if isinstance(reasons, list) else []


def _is_failed(frame: dict[str, Any] | None) -> bool:
    if not frame:
        return False
    status = str(frame.get("status") or "")
    if status == "failed":
        return True
    if frame.get("agreement_status") == "failed":
        return True
    if frame.get("quality_gate_status") == "failed":
        return True
    return bool(_failure_reasons(frame))


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and number not in (float("inf"), float("-inf")) else None


def _determinism(frame: dict[str, Any] | None) -> dict[str, Any]:
    if not frame:
        return {}
    value = frame.get("determinism")
    return value if isinstance(value, dict) else {}


def _signature_value(frame: dict[str, Any] | None, key: str) -> str | None:
    value = _determinism(frame).get(key)
    return str(value) if value else None


def _reference_signature_set(frames: dict[str, dict[str, Any]], key: str) -> list[str]:
    values = {
        str(value)
        for frame in frames.values()
        if (value := _signature_value(frame, key)) and frame.get("is_triangle")
    }
    return sorted(values)


def _frame_row(frame_id: str, baseline: dict[str, Any] | None, candidate: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "frame_id": frame_id,
        "baseline_status": None if baseline is None else baseline.get("status"),
        "candidate_status": None if candidate is None else candidate.get("status"),
        "baseline_failure_reasons": _failure_reasons(baseline),
        "candidate_failure_reasons": _failure_reasons(candidate),
        "baseline_agreement_score": _float_or_none(None if baseline is None else baseline.get("agreement_score")),
        "candidate_agreement_score": _float_or_none(None if candidate is None else candidate.get("agreement_score")),
        "baseline_agreement_status": None if baseline is None else baseline.get("agreement_status"),
        "candidate_agreement_status": None if candidate is None else candidate.get("agreement_status"),
        "baseline_pixel_rms_adu": _float_or_none(None if baseline is None else baseline.get("pixel_rms_adu")),
        "candidate_pixel_rms_adu": _float_or_none(None if candidate is None else candidate.get("pixel_rms_adu")),
        "baseline_pixel_ncc": _float_or_none(None if baseline is None else baseline.get("pixel_ncc")),
        "candidate_pixel_ncc": _float_or_none(None if candidate is None else candidate.get("pixel_ncc")),
        "baseline_fit_rms_px": _float_or_none(None if baseline is None else baseline.get("fit_rms_px")),
        "candidate_fit_rms_px": _float_or_none(None if candidate is None else candidate.get("fit_rms_px")),
        "baseline_inliers": None if baseline is None else baseline.get("inliers"),
        "candidate_inliers": None if candidate is None else candidate.get("inliers"),
        "signature_changes": {
            key: _signature_value(baseline, key) != _signature_value(candidate, key) for key in _SIGNATURE_KEYS
        },
    }


def _candidate_row(
    baseline_id: str,
    baseline_frames: dict[str, dict[str, Any]],
    candidate_path: str | Path,
) -> dict[str, Any]:
    candidate = _load_json_object(candidate_path)
    candidate_id = _variant_id(candidate, candidate_path)
    candidate_frames = _frames_by_id(candidate)
    baseline_failed = {frame_id for frame_id, frame in baseline_frames.items() if _is_failed(frame)}
    candidate_failed = {frame_id for frame_id, frame in candidate_frames.items() if _is_failed(frame)}
    common_ids = sorted(set(baseline_frames) & set(candidate_frames))
    signature_change_counts = {
        key: sum(
            1
            for frame_id in common_ids
            if _signature_value(baseline_frames.get(frame_id), key) != _signature_value(candidate_frames.get(frame_id), key)
        )
        for key in _SIGNATURE_KEYS
    }
    extra_failed = sorted(candidate_failed - baseline_failed)
    recovered = sorted(baseline_failed - candidate_failed)
    reference_catalog_baseline = _reference_signature_set(baseline_frames, "reference_catalog_signature")
    reference_catalog_candidate = _reference_signature_set(candidate_frames, "reference_catalog_signature")
    reference_descriptor_baseline = _reference_signature_set(baseline_frames, "reference_descriptor_signature")
    reference_descriptor_candidate = _reference_signature_set(candidate_frames, "reference_descriptor_signature")
    return {
        "baseline_variant_id": baseline_id,
        "candidate_variant_id": candidate_id,
        "candidate_audit": str(candidate_path),
        "baseline_failed_frame_count": len(baseline_failed),
        "candidate_failed_frame_count": len(candidate_failed),
        "extra_failed_frame_count": len(extra_failed),
        "extra_failed_frame_ids": extra_failed,
        "recovered_frame_count": len(recovered),
        "recovered_frame_ids": recovered,
        "common_frame_count": len(common_ids),
        "signature_change_counts": signature_change_counts,
        "reference_catalog_signature_match": reference_catalog_baseline == reference_catalog_candidate,
        "reference_descriptor_signature_match": reference_descriptor_baseline == reference_descriptor_candidate,
        "reference_catalog_signatures": {
            "baseline": reference_catalog_baseline,
            "candidate": reference_catalog_candidate,
        },
        "reference_descriptor_signatures": {
            "baseline": reference_descriptor_baseline,
            "candidate": reference_descriptor_candidate,
        },
        "extra_failed_frames": [
            _frame_row(frame_id, baseline_frames.get(frame_id), candidate_frames.get(frame_id)) for frame_id in extra_failed
        ],
        "recovered_frames": [
            _frame_row(frame_id, baseline_frames.get(frame_id), candidate_frames.get(frame_id)) for frame_id in recovered
        ],
    }


def _recommendation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if any(not row["reference_catalog_signature_match"] for row in rows):
        return {
            "status": "deterministic_catalog_required",
            "reason": "at least one candidate changed the reference catalog signature versus baseline",
            "next_target": "stabilize resident catalog determinism before promoting agreement thresholds",
        }
    if any(row["extra_failed_frame_count"] for row in rows):
        return {
            "status": "threshold_rejects_required_frames",
            "reason": "agreement thresholding rejected frames that the baseline accepted",
            "next_target": "inspect rejected frames and replace scalar cutoff with a less blunt decision rule",
        }
    return {
        "status": "no_extra_rejection_detected",
        "reason": "candidate audits did not add registration failures versus baseline",
        "next_target": "validate image agreement and runtime before considering a threshold default",
    }


def build_resident_registration_triage(
    baseline_audit: str | Path,
    candidate_audits: list[str | Path],
) -> dict[str, Any]:
    baseline = _load_json_object(baseline_audit)
    baseline_id = _variant_id(baseline, baseline_audit)
    baseline_frames = _frames_by_id(baseline)
    rows = [_candidate_row(baseline_id, baseline_frames, path) for path in candidate_audits]
    return {
        "schema_version": 1,
        "audit_type": "resident_registration_rejection_triage",
        "baseline_audit": str(baseline_audit),
        "baseline_variant_id": baseline_id,
        "candidate_count": len(rows),
        "summary": {
            "extra_failed_variant_count": sum(1 for row in rows if row["extra_failed_frame_count"] > 0),
            "reference_catalog_drift_variant_count": sum(
                1 for row in rows if not row["reference_catalog_signature_match"]
            ),
            "reference_descriptor_drift_variant_count": sum(
                1 for row in rows if not row["reference_descriptor_signature_match"]
            ),
        },
        "recommendation": _recommendation(rows),
        "rows": rows,
    }


def write_resident_registration_triage_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resident Registration Rejection Triage",
        "",
        f"- Baseline audit: `{payload['baseline_audit']}`",
        f"- Baseline variant: `{payload['baseline_variant_id']}`",
        f"- Candidate count: `{payload['candidate_count']}`",
        f"- Recommendation: `{payload['recommendation']['status']}`",
        f"- Next target: `{payload['recommendation']['next_target']}`",
        "",
        "## Candidate Rows",
        "",
        "| Candidate | Extra failed | Recovered | Ref catalog match | Ref descriptor match | Selected fit changes | Extra failed frames |",
        "| --- | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in payload.get("rows", []):
        selected_fit_changes = row["signature_change_counts"].get("selected_fit_signature")
        extra_ids = ", ".join(row["extra_failed_frame_ids"])
        lines.append(
            "| "
            f"`{row['candidate_variant_id']}` | "
            f"{row['extra_failed_frame_count']} | "
            f"{row['recovered_frame_count']} | "
            f"{row['reference_catalog_signature_match']} | "
            f"{row['reference_descriptor_signature_match']} | "
            f"{selected_fit_changes} | "
            f"{extra_ids} |"
        )
    lines.extend(["", "## Extra Failed Frames", ""])
    for row in payload.get("rows", []):
        if not row["extra_failed_frames"]:
            continue
        lines.append(f"### {row['candidate_variant_id']}")
        lines.append("")
        lines.append("| Frame | Candidate score | Candidate reason | Baseline score | Candidate RMS ADU | Candidate NCC |")
        lines.append("| --- | ---: | --- | ---: | ---: | ---: |")
        for frame in row["extra_failed_frames"]:
            reason = ", ".join(frame["candidate_failure_reasons"])
            lines.append(
                "| "
                f"`{frame['frame_id']}` | "
                f"{frame['candidate_agreement_score']} | "
                f"{reason} | "
                f"{frame['baseline_agreement_score']} | "
                f"{frame['candidate_pixel_rms_adu']} | "
                f"{frame['candidate_pixel_ncc']} |"
            )
        lines.append("")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_registration_triage(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown:
        write_resident_registration_triage_markdown(markdown, payload)
