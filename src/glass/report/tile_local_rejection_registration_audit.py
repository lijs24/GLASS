from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_tile_attribution import _float_or_none, _stats


def _fraction(numerator: Any, denominator: Any) -> float | None:
    num = _float_or_none(numerator)
    den = _float_or_none(denominator)
    if num is None or den is None or den <= 0.0:
        return None
    return float(num / den)


def _finite(values: list[float | None]) -> np.ndarray:
    return np.asarray([value for value in values if value is not None], dtype=np.float64)


def _mean(values: list[float | None]) -> float | None:
    finite = _finite(values)
    if finite.size == 0:
        return None
    return float(np.mean(finite))


def _pearson(x_values: list[float | None], y_values: list[float | None]) -> float | None:
    pairs = [(float(x), float(y)) for x, y in zip(x_values, y_values, strict=False) if x is not None and y is not None]
    if len(pairs) < 2:
        return None
    x = np.asarray([pair[0] for pair in pairs], dtype=np.float64)
    y = np.asarray([pair[1] for pair in pairs], dtype=np.float64)
    if float(np.std(x)) <= 0.0 or float(np.std(y)) <= 0.0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _top_frame_family_ids(frame_family_search: dict[str, Any] | None) -> list[str]:
    if not isinstance(frame_family_search, dict):
        return []
    top = frame_family_search.get("top_candidate")
    if not isinstance(top, dict):
        return []
    frame_ids = top.get("frame_ids")
    if isinstance(frame_ids, list):
        return [str(frame_id) for frame_id in frame_ids]
    return []


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        status = row.get("triangle_agreement_status")
        if status is not None:
            counts[str(status)] += 1
    return dict(sorted(counts.items()))


def _frame_summary(frame_rows: list[dict[str, Any]]) -> dict[str, Any]:
    high = [_fraction(row.get("high_rejected_pixels"), row.get("valid_pixels")) for row in frame_rows]
    low = [_fraction(row.get("low_rejected_pixels"), row.get("valid_pixels")) for row in frame_rows]
    rejected = [_fraction(row.get("rejected_pixels"), row.get("valid_pixels")) for row in frame_rows]
    accepted = [_float_or_none(row.get("accepted_fraction")) for row in frame_rows]
    return {
        "tile_row_count": len(frame_rows),
        "high_rejected_fraction_stats": _stats(_finite(high)),
        "low_rejected_fraction_stats": _stats(_finite(low)),
        "rejected_fraction_stats": _stats(_finite(rejected)),
        "accepted_fraction_stats": _stats(_finite(accepted)),
        "triangle_agreement_score_stats": _stats(
            _finite([_float_or_none(row.get("triangle_agreement_score")) for row in frame_rows])
        ),
        "triangle_pixel_ncc_stats": _stats(
            _finite([_float_or_none(row.get("triangle_pixel_ncc_batch")) for row in frame_rows])
        ),
        "triangle_pixel_rms_adu_stats": _stats(
            _finite([_float_or_none(row.get("triangle_pixel_rms_adu_batch")) for row in frame_rows])
        ),
        "registration_rms_px_stats": _stats(_finite([_float_or_none(row.get("registration_rms_px")) for row in frame_rows])),
        "triangle_agreement_weight_multiplier_stats": _stats(
            _finite([_float_or_none(row.get("triangle_agreement_weight_multiplier")) for row in frame_rows])
        ),
        "normalized_delta_contribution_mean_stats": _stats(
            _finite([_float_or_none(row.get("normalized_delta_contribution_mean")) for row in frame_rows])
        ),
        "agreement_status_counts": _status_counts(frame_rows),
    }


def _group_mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [_float_or_none(row.get(key)) for row in rows]
    return _mean(values)


def _group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "frame_count": len(rows),
        "high_rejected_fraction_mean": _group_mean(rows, "high_rejected_fraction_mean"),
        "rejected_fraction_mean": _group_mean(rows, "rejected_fraction_mean"),
        "accepted_fraction_mean": _group_mean(rows, "accepted_fraction_mean"),
        "triangle_agreement_score_mean": _group_mean(rows, "triangle_agreement_score_mean"),
        "triangle_pixel_ncc_mean": _group_mean(rows, "triangle_pixel_ncc_mean"),
        "registration_rms_px_mean": _group_mean(rows, "registration_rms_px_mean"),
        "agreement_weight_multiplier_mean": _group_mean(rows, "triangle_agreement_weight_multiplier_mean"),
    }


def build_tile_local_rejection_registration_audit(
    contribution: str | Path,
    *,
    frame_family_search: str | Path | None = None,
    high_rejection_threshold: float = 0.01,
    low_agreement_score_threshold: float = 0.5,
    top_n: int = 20,
) -> dict[str, Any]:
    if high_rejection_threshold < 0.0:
        raise ValueError("high_rejection_threshold must be non-negative")
    if top_n < 0:
        raise ValueError("top_n must be non-negative")
    contribution_payload = read_json(contribution)
    frame_search_payload = read_json(frame_family_search) if frame_family_search else None
    focus_ids = {str(frame_id) for frame_id in contribution_payload.get("focus_ids", [])}
    control_ids = {str(frame_id) for frame_id in contribution_payload.get("control_ids", [])}
    top_family_ids = set(_top_frame_family_ids(frame_search_payload))

    rows_by_frame: dict[str, list[dict[str, Any]]] = {}
    for tile in contribution_payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        for row in tile.get("top_frames", []):
            if not isinstance(row, dict):
                continue
            frame_id = row.get("frame_id")
            if frame_id is None:
                continue
            rows_by_frame.setdefault(str(frame_id), []).append(row)

    frame_rows: list[dict[str, Any]] = []
    for frame_id, rows in sorted(rows_by_frame.items()):
        summary = _frame_summary(rows)
        high_mean = _float_or_none(summary["high_rejected_fraction_stats"].get("mean"))
        score_mean = _float_or_none(summary["triangle_agreement_score_stats"].get("mean"))
        ncc_mean = _float_or_none(summary["triangle_pixel_ncc_stats"].get("mean"))
        rms_mean = _float_or_none(summary["registration_rms_px_stats"].get("mean"))
        weight_mean = _float_or_none(summary["triangle_agreement_weight_multiplier_stats"].get("mean"))
        accepted_mean = _float_or_none(summary["accepted_fraction_stats"].get("mean"))
        rejected_mean = _float_or_none(summary["rejected_fraction_stats"].get("mean"))
        frame_rows.append(
            {
                "frame_id": frame_id,
                "in_focus_group": frame_id in focus_ids,
                "in_control_group": frame_id in control_ids,
                "in_top_frame_family": frame_id in top_family_ids,
                "high_rejected_fraction_mean": high_mean,
                "rejected_fraction_mean": rejected_mean,
                "accepted_fraction_mean": accepted_mean,
                "triangle_agreement_score_mean": score_mean,
                "triangle_pixel_ncc_mean": ncc_mean,
                "registration_rms_px_mean": rms_mean,
                "triangle_agreement_weight_multiplier_mean": weight_mean,
                "high_rejection_excess": bool(high_mean is not None and high_mean >= high_rejection_threshold),
                "low_agreement_score": bool(score_mean is not None and score_mean <= low_agreement_score_threshold),
                **summary,
            }
        )

    ranked = sorted(
        frame_rows,
        key=lambda row: (
            float(row.get("high_rejected_fraction_mean") or 0.0),
            -float(row.get("triangle_agreement_score_mean") or 0.0),
        ),
        reverse=True,
    )
    focus_rows = [row for row in frame_rows if row.get("in_focus_group")]
    control_rows = [row for row in frame_rows if row.get("in_control_group")]
    other_rows = [row for row in frame_rows if not row.get("in_focus_group") and not row.get("in_control_group")]
    top_family_rows = [row for row in frame_rows if row.get("in_top_frame_family")]
    focus_high = _group_mean(focus_rows, "high_rejected_fraction_mean")
    control_high = _group_mean(control_rows, "high_rejected_fraction_mean")
    other_high = _group_mean(other_rows, "high_rejected_fraction_mean")
    focus_minus_control = None if focus_high is None or control_high is None else float(focus_high - control_high)
    focus_minus_other = None if focus_high is None or other_high is None else float(focus_high - other_high)
    top_high_frames = ranked if top_n == 0 else ranked[:top_n]
    high_excess_count = sum(1 for row in frame_rows if row.get("high_rejection_excess"))
    low_agreement_high_excess_count = sum(
        1 for row in frame_rows if row.get("high_rejection_excess") and row.get("low_agreement_score")
    )
    top_family_high_excess_count = sum(1 for row in top_family_rows if row.get("high_rejection_excess"))
    if (
        focus_minus_control is not None
        and focus_minus_control >= high_rejection_threshold
        and top_family_rows
        and top_family_high_excess_count >= max(1, len(top_family_rows) // 2)
    ):
        recommendation = "prioritize_registration_agreement_rejection_interaction"
    elif high_excess_count > 0:
        recommendation = "inspect_high_rejection_frames"
    else:
        recommendation = "no_frame_level_rejection_hotspot"

    return {
        "schema_version": 1,
        "artifact_type": "tile_local_rejection_registration_audit",
        "created_at": now_iso(),
        "contribution": str(contribution),
        "frame_family_search": str(frame_family_search) if frame_family_search else None,
        "frame_count": len(frame_rows),
        "thresholds": {
            "high_rejection_threshold": float(high_rejection_threshold),
            "low_agreement_score_threshold": float(low_agreement_score_threshold),
        },
        "summary": {
            "recommendation": recommendation,
            "focus_group": _group_summary(focus_rows),
            "control_group": _group_summary(control_rows),
            "other_group": _group_summary(other_rows),
            "top_frame_family_group": _group_summary(top_family_rows),
            "focus_minus_control_high_rejected_fraction_mean": focus_minus_control,
            "focus_minus_other_high_rejected_fraction_mean": focus_minus_other,
            "high_rejection_excess_frame_count": high_excess_count,
            "low_agreement_high_rejection_frame_count": low_agreement_high_excess_count,
            "top_frame_family_high_rejection_excess_frame_count": top_family_high_excess_count,
            "high_rejection_vs_triangle_agreement_score_corr": _pearson(
                [row.get("high_rejected_fraction_mean") for row in frame_rows],
                [row.get("triangle_agreement_score_mean") for row in frame_rows],
            ),
            "high_rejection_vs_triangle_ncc_corr": _pearson(
                [row.get("high_rejected_fraction_mean") for row in frame_rows],
                [row.get("triangle_pixel_ncc_mean") for row in frame_rows],
            ),
            "high_rejection_vs_registration_rms_corr": _pearson(
                [row.get("high_rejected_fraction_mean") for row in frame_rows],
                [row.get("registration_rms_px_mean") for row in frame_rows],
            ),
            "top_high_rejection_frames": [
                {
                    "frame_id": row.get("frame_id"),
                    "high_rejected_fraction_mean": row.get("high_rejected_fraction_mean"),
                    "triangle_agreement_score_mean": row.get("triangle_agreement_score_mean"),
                    "triangle_pixel_ncc_mean": row.get("triangle_pixel_ncc_mean"),
                    "registration_rms_px_mean": row.get("registration_rms_px_mean"),
                    "in_focus_group": row.get("in_focus_group"),
                    "in_top_frame_family": row.get("in_top_frame_family"),
                }
                for row in top_high_frames
            ],
        },
        "frames": frame_rows,
        "limitations": [
            "This audit consumes resident contribution JSON only and does not read image pixels.",
            "Correlations are diagnostic and do not prove causality.",
            "Registration metrics are the values recorded in the contribution artifact for the captured residual tiles.",
        ],
    }


def write_tile_local_rejection_registration_audit(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Tile-Local Rejection/Registration Audit",
        "",
        f"- Contribution: `{payload.get('contribution')}`",
        f"- Frame-family search: `{payload.get('frame_family_search')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Focus minus control high rejection: `{summary.get('focus_minus_control_high_rejected_fraction_mean')}`",
        f"- High-rejection excess frames: `{summary.get('high_rejection_excess_frame_count')}`",
        f"- Low-agreement high-rejection frames: `{summary.get('low_agreement_high_rejection_frame_count')}`",
        f"- High rejection vs agreement-score correlation: `{summary.get('high_rejection_vs_triangle_agreement_score_corr')}`",
        "",
        "| rank | frame | high rej | agreement | NCC | RMS px | focus | top family |",
        "| ---: | --- | ---: | ---: | ---: | ---: | :---: | :---: |",
    ]
    for rank, row in enumerate(summary.get("top_high_rejection_frames") or [], start=1):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {rank} | {frame} | {high} | {score} | {ncc} | {rms} | {focus} | {family} |".format(
                rank=rank,
                frame=row.get("frame_id"),
                high=row.get("high_rejected_fraction_mean"),
                score=row.get("triangle_agreement_score_mean"),
                ncc=row.get("triangle_pixel_ncc_mean"),
                rms=row.get("registration_rms_px_mean"),
                focus=row.get("in_focus_group"),
                family=row.get("in_top_frame_family"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
