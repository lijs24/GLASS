from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


QUALITY_METRIC_FIELDS = [
    ("star_count", "low"),
    ("fwhm_px", "high"),
    ("eccentricity", "high"),
    ("background_rms", "high"),
    ("snr", "low"),
    ("quality_score", "low"),
    ("weight", "low"),
]


def _float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _median_sorted(values: list[float]) -> float | None:
    if not values:
        return None
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _metric_pairs(rows: list[dict[str, Any]], metric: str) -> list[tuple[dict[str, Any], float]]:
    pairs: list[tuple[dict[str, Any], float]] = []
    for row in rows:
        value = _float_or_none(row.get(metric))
        if value is not None:
            pairs.append((row, value))
    return pairs


def _metric_summary(rows: list[dict[str, Any]], metric: str, bad_direction: str) -> dict[str, Any]:
    pairs = _metric_pairs(rows, metric)
    if not pairs:
        return {
            "metric": metric,
            "bad_direction": bad_direction,
            "valid_frames": 0,
            "available": False,
        }
    values = sorted(value for _, value in pairs)
    worst_item, worst_value = (
        min(pairs, key=lambda pair: pair[1])
        if bad_direction == "low"
        else max(pairs, key=lambda pair: pair[1])
    )
    return {
        "metric": metric,
        "bad_direction": bad_direction,
        "valid_frames": len(values),
        "available": True,
        "min": _round(values[0]),
        "median": _round(_median_sorted(values)),
        "mean": _round(sum(values) / len(values)),
        "max": _round(values[-1]),
        "worst_frame_id": worst_item.get("frame_id"),
        "worst_value": _round(worst_value),
    }


def _load_quality_artifact(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {
            "path": str(target),
            "exists": False,
            "status": "missing",
            "frame_count": 0,
            "metrics": {},
            "quality_gate_status_counts": {},
            "frame_ids": [],
        }
    payload = read_json(target)
    if not isinstance(payload, dict):
        return {
            "path": str(target),
            "exists": True,
            "status": "invalid",
            "reason": "artifact is not a JSON object",
            "frame_count": 0,
            "metrics": {},
            "quality_gate_status_counts": {},
            "frame_ids": [],
        }
    frame_quality = payload.get("frame_quality")
    if not isinstance(frame_quality, list):
        return {
            "path": str(target),
            "exists": True,
            "status": "invalid",
            "reason": "frame_quality list missing",
            "frame_count": 0,
            "metrics": {},
            "quality_gate_status_counts": {},
            "frame_ids": [],
        }
    rows = [row for row in frame_quality if isinstance(row, dict)]
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("quality_gate_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    metric_summaries = {
        metric: _metric_summary(rows, metric, bad_direction)
        for metric, bad_direction in QUALITY_METRIC_FIELDS
    }
    available_metrics = [
        metric for metric, summary in metric_summaries.items() if summary.get("available")
    ]
    return {
        "path": str(target),
        "exists": True,
        "status": "passed" if available_metrics else "not_available",
        "frame_count": len(rows),
        "metrics": metric_summaries,
        "metric_count": len(available_metrics),
        "available_metrics": available_metrics,
        "quality_gate_status_counts": status_counts,
        "frame_ids": [str(row.get("frame_id")) for row in rows if row.get("frame_id")],
    }


def _badness_ratio(
    baseline_value: float | None,
    candidate_value: float | None,
    *,
    bad_direction: str,
) -> float | None:
    if baseline_value is None or candidate_value is None:
        return None
    if bad_direction == "high":
        if baseline_value <= 0:
            return None
        return candidate_value / baseline_value
    if candidate_value <= 0:
        return None
    return baseline_value / candidate_value


def _metric_compare_row(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    metric: str,
    bad_direction: str,
) -> dict[str, Any]:
    baseline_metric = baseline.get("metrics", {}).get(metric, {})
    candidate_metric = candidate.get("metrics", {}).get(metric, {})
    baseline_available = bool(baseline_metric.get("available"))
    candidate_available = bool(candidate_metric.get("available"))
    baseline_median = _float_or_none(baseline_metric.get("median"))
    candidate_median = _float_or_none(candidate_metric.get("median"))
    baseline_mean = _float_or_none(baseline_metric.get("mean"))
    candidate_mean = _float_or_none(candidate_metric.get("mean"))
    median_delta = (
        candidate_median - baseline_median
        if baseline_median is not None and candidate_median is not None
        else None
    )
    mean_delta = (
        candidate_mean - baseline_mean
        if baseline_mean is not None and candidate_mean is not None
        else None
    )
    return {
        "metric": metric,
        "bad_direction": bad_direction,
        "baseline_available": baseline_available,
        "candidate_available": candidate_available,
        "baseline_valid_frames": baseline_metric.get("valid_frames", 0),
        "candidate_valid_frames": candidate_metric.get("valid_frames", 0),
        "baseline_median": baseline_metric.get("median"),
        "candidate_median": candidate_metric.get("median"),
        "median_delta": _round(median_delta),
        "bad_median_ratio": _round(
            _badness_ratio(baseline_median, candidate_median, bad_direction=bad_direction)
        ),
        "baseline_mean": baseline_metric.get("mean"),
        "candidate_mean": candidate_metric.get("mean"),
        "mean_delta": _round(mean_delta),
        "bad_mean_ratio": _round(
            _badness_ratio(baseline_mean, candidate_mean, bad_direction=bad_direction)
        ),
        "baseline_worst_frame_id": baseline_metric.get("worst_frame_id"),
        "candidate_worst_frame_id": candidate_metric.get("worst_frame_id"),
        "baseline_worst_value": baseline_metric.get("worst_value"),
        "candidate_worst_value": candidate_metric.get("worst_value"),
    }


def _check(name: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def build_quality_metrics_compare(
    baseline: str | Path,
    candidate: str | Path,
    *,
    max_bad_median_ratio: float | None = None,
    max_bad_mean_ratio: float | None = None,
) -> dict[str, Any]:
    baseline_summary = _load_quality_artifact(baseline)
    candidate_summary = _load_quality_artifact(candidate)
    metric_rows = [
        _metric_compare_row(baseline_summary, candidate_summary, metric, bad_direction)
        for metric, bad_direction in QUALITY_METRIC_FIELDS
    ]
    missing_metrics = [
        row["metric"]
        for row in metric_rows
        if row["baseline_available"] and not row["candidate_available"]
    ]
    checks = [
        _check(
            "baseline_frame_quality_available",
            baseline_summary.get("exists") is True and baseline_summary.get("status") != "invalid",
            {
                "path": baseline_summary.get("path"),
                "status": baseline_summary.get("status"),
                "frame_count": baseline_summary.get("frame_count"),
                "metric_count": baseline_summary.get("metric_count"),
            },
        ),
        _check(
            "candidate_frame_quality_available",
            candidate_summary.get("exists") is True and candidate_summary.get("status") != "invalid",
            {
                "path": candidate_summary.get("path"),
                "status": candidate_summary.get("status"),
                "frame_count": candidate_summary.get("frame_count"),
                "metric_count": candidate_summary.get("metric_count"),
            },
        ),
        _check(
            "candidate_metric_summary_preserved",
            not missing_metrics,
            {
                "missing_metrics": missing_metrics,
                "baseline_metrics": baseline_summary.get("available_metrics"),
                "candidate_metrics": candidate_summary.get("available_metrics"),
            },
        ),
    ]
    if max_bad_median_ratio is not None:
        failing = [
            row
            for row in metric_rows
            if row["baseline_available"]
            and row["candidate_available"]
            and row.get("bad_median_ratio") is not None
            and float(row["bad_median_ratio"]) > float(max_bad_median_ratio)
        ]
        checks.append(
            _check(
                "bad_median_ratio_within_limit",
                not failing,
                {
                    "max_bad_median_ratio": max_bad_median_ratio,
                    "failing_metrics": [
                        {
                            "metric": row["metric"],
                            "bad_median_ratio": row["bad_median_ratio"],
                            "baseline_median": row["baseline_median"],
                            "candidate_median": row["candidate_median"],
                        }
                        for row in failing
                    ],
                },
            )
        )
    if max_bad_mean_ratio is not None:
        failing = [
            row
            for row in metric_rows
            if row["baseline_available"]
            and row["candidate_available"]
            and row.get("bad_mean_ratio") is not None
            and float(row["bad_mean_ratio"]) > float(max_bad_mean_ratio)
        ]
        checks.append(
            _check(
                "bad_mean_ratio_within_limit",
                not failing,
                {
                    "max_bad_mean_ratio": max_bad_mean_ratio,
                    "failing_metrics": [
                        {
                            "metric": row["metric"],
                            "bad_mean_ratio": row["bad_mean_ratio"],
                            "baseline_mean": row["baseline_mean"],
                            "candidate_mean": row["candidate_mean"],
                        }
                        for row in failing
                    ],
                },
            )
        )
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "artifact_type": "quality_metrics_compare",
        "created_at": now_iso(),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "baseline": baseline_summary,
        "candidate": candidate_summary,
        "metric_rows": metric_rows,
        "checks": checks,
    }


def write_quality_metrics_compare_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GLASS Quality Metrics Compare",
        "",
        f"- Status: {payload.get('status')}",
        f"- Baseline: {(payload.get('baseline') or {}).get('path')}",
        f"- Candidate: {(payload.get('candidate') or {}).get('path')}",
        f"- Baseline metrics: {(payload.get('baseline') or {}).get('available_metrics')}",
        f"- Candidate metrics: {(payload.get('candidate') or {}).get('available_metrics')}",
        "",
        "## Checks",
        "",
    ]
    for check in payload.get("checks") or []:
        marker = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {marker}: {check.get('name')} - {check.get('evidence')}")
    lines.extend(["", "## Metrics", ""])
    for row in payload.get("metric_rows") or []:
        lines.append(
            "- "
            f"{row.get('metric')}: "
            f"baseline_median={row.get('baseline_median')} "
            f"candidate_median={row.get('candidate_median')} "
            f"bad_median_ratio={row.get('bad_median_ratio')} "
            f"baseline_mean={row.get('baseline_mean')} "
            f"candidate_mean={row.get('candidate_mean')} "
            f"bad_mean_ratio={row.get('bad_mean_ratio')}"
        )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_quality_metrics_compare(
    out_json: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, payload)
    if markdown is not None:
        write_quality_metrics_compare_markdown(markdown, payload)
