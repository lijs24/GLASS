from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json


_SUMMARY_STATS = (
    ("candidate_count_median", "candidate_count_stats", "median"),
    ("candidate_count_mean", "candidate_count_stats", "mean"),
    ("fit_rms_px_median", "fit_rms_px_stats", "median"),
    ("fit_rms_px_mean", "fit_rms_px_stats", "mean"),
    ("pixel_rms_adu_median", "pixel_rms_adu_stats", "median"),
    ("pixel_rms_adu_mean", "pixel_rms_adu_stats", "mean"),
    ("pixel_ncc_median", "pixel_ncc_stats", "median"),
    ("pixel_ncc_mean", "pixel_ncc_stats", "mean"),
)


def _load_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _variant_id_from_audit_path(path: Path) -> str:
    name = path.stem
    suffix = "_candidate_audit"
    return name[: -len(suffix)] if name.endswith(suffix) else name


def _audit_index(audit_root: str | Path | None, audit_jsons: list[str | Path] | None) -> dict[str, dict[str, Any]]:
    paths: list[Path] = []
    if audit_root:
        root = Path(audit_root)
        paths.extend(sorted(root.glob("*_candidate_audit.json")))
    if audit_jsons:
        paths.extend(Path(path) for path in audit_jsons)
    index: dict[str, dict[str, Any]] = {}
    for path in paths:
        payload = _load_json_object(path)
        variant_id = str(payload.get("variant_id") or _variant_id_from_audit_path(path))
        index[variant_id] = {**payload, "_audit_path": str(path)}
    return index


def _summary_value(audit: dict[str, Any], group: str, key: str) -> float | None:
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    stats = summary.get(group) if isinstance(summary.get(group), dict) else {}
    return _float_or_none(stats.get(key))


def _candidate_metrics(audit: dict[str, Any]) -> dict[str, Any]:
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    metrics: dict[str, Any] = {
        "audit_path": audit.get("_audit_path"),
        "audit_status": audit.get("status"),
        "frame_count": summary.get("frame_count"),
        "triangle_frame_count": summary.get("triangle_frame_count"),
        "failed_triangle_frame_count": summary.get("failed_triangle_frame_count"),
        "quality_gate_failed_count": summary.get("quality_gate_failed_count"),
        "no_accepted_fit_count": summary.get("no_accepted_fit_count"),
        "parse_error_count": summary.get("parse_error_count"),
    }
    for output_key, group, stat_key in _SUMMARY_STATS:
        metrics[output_key] = _summary_value(audit, group, stat_key)
    return metrics


def _compare_metrics(run: dict[str, Any]) -> dict[str, Any]:
    compare = run.get("compare") if isinstance(run.get("compare"), dict) else {}
    compare_gate = run.get("compare_gate") if isinstance(run.get("compare_gate"), dict) else {}
    return {
        "compare_status": compare.get("status"),
        "compare_gate_status": compare_gate.get("status"),
        "compare_gate_passed": compare_gate.get("passed"),
        "compare_gate_reasons": compare_gate.get("reasons") if isinstance(compare_gate.get("reasons"), list) else [],
        "rms_diff": _float_or_none(compare.get("rms_diff")),
        "abs_diff_p99": _float_or_none(compare.get("abs_diff_p99")),
        "relative_rms_diff": _float_or_none(compare.get("relative_rms_diff")),
        "coverage_fraction": _float_or_none(compare.get("coverage_fraction")),
        "speedup_vs_reference": _float_or_none(compare.get("speedup_vs_reference")),
        "total_elapsed_s": _float_or_none(run.get("total_elapsed_s")),
        "registration_warp_s": _float_or_none(run.get("resident_registration_warp_s")),
        "moving_catalog_s": _float_or_none(run.get("registration_triangle_moving_catalog_s")),
        "pixel_refine_s": _float_or_none(run.get("registration_triangle_pixel_refine_s")),
    }


def _pearson(pairs: list[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    xs = [item[0] for item in pairs]
    ys = [item[1] for item in pairs]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    dx = [value - x_mean for value in xs]
    dy = [value - y_mean for value in ys]
    denom = sqrt(sum(value * value for value in dx) * sum(value * value for value in dy))
    if denom == 0.0:
        return None
    return sum(left * right for left, right in zip(dx, dy, strict=True)) / denom


def _correlation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target_keys = ("rms_diff", "abs_diff_p99", "relative_rms_diff")
    metric_keys = tuple(key for key, _group, _stat in _SUMMARY_STATS) + (
        "failed_triangle_frame_count",
        "quality_gate_failed_count",
        "moving_catalog_s",
        "pixel_refine_s",
    )
    correlations: list[dict[str, Any]] = []
    for target in target_keys:
        for metric in metric_keys:
            pairs: list[tuple[float, float]] = []
            for row in rows:
                x = _float_or_none(row.get(metric))
                y = _float_or_none(row.get(target))
                if x is not None and y is not None:
                    pairs.append((x, y))
            correlations.append(
                {
                    "metric": metric,
                    "target": target,
                    "pair_count": len(pairs),
                    "pearson": _pearson(pairs),
                }
            )
    return correlations


def _recommendation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [row for row in rows if row.get("compare_status") == "completed"]
    compare_failures = [row for row in completed if row.get("compare_gate_passed") is False]
    hard_failures = [
        row
        for row in completed
        if int(row.get("failed_triangle_frame_count") or 0) > 0
        or int(row.get("quality_gate_failed_count") or 0) > 0
        or int(row.get("parse_error_count") or 0) > 0
    ]
    if compare_failures and not hard_failures:
        return {
            "status": "compare_failures_without_registration_hard_failures",
            "reason": (
                "strict compare failures remain even though candidate audits found no triangle "
                "registration failures, quality-gate failures, or parse errors"
            ),
            "next_target": "descriptor scoring or pixel-refine agreement",
        }
    if hard_failures:
        return {
            "status": "registration_hard_failures_present",
            "reason": "one or more variants have failed/quality-gated triangle registration frames",
            "next_target": "registration failure triage before scoring optimization",
        }
    return {
        "status": "no_compare_failure_evidence",
        "reason": "no completed compare-gated failure rows were available",
        "next_target": "collect compare-gated resident sweep evidence",
    }


def build_resident_registration_compare(
    sweep_summary: str | Path,
    *,
    audit_root: str | Path | None = None,
    audit_jsons: list[str | Path] | None = None,
) -> dict[str, Any]:
    summary = _load_json_object(sweep_summary)
    audits = _audit_index(audit_root, audit_jsons)
    runs = summary.get("runs") if isinstance(summary.get("runs"), list) else []
    rows: list[dict[str, Any]] = []
    missing_audits: list[str] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        variant_id = str(run.get("variant_id") or (run.get("variant") or {}).get("variant_id") or "")
        if not variant_id:
            continue
        audit = audits.get(variant_id)
        if audit is None:
            missing_audits.append(variant_id)
            candidate = {"audit_status": "missing", "audit_path": None}
        else:
            candidate = _candidate_metrics(audit)
        rows.append(
            {
                "variant_id": variant_id,
                "variant": run.get("variant") if isinstance(run.get("variant"), dict) else {},
                **_compare_metrics(run),
                **candidate,
            }
        )
    correlations = _correlation_rows(rows)
    correlations_ranked = sorted(
        [item for item in correlations if item["pearson"] is not None],
        key=lambda item: abs(float(item["pearson"])),
        reverse=True,
    )
    return {
        "schema_version": 1,
        "audit_type": "resident_registration_candidate_compare",
        "sweep_summary": str(sweep_summary),
        "audit_root": None if audit_root is None else str(audit_root),
        "variant_count": len(rows),
        "missing_audit_count": len(missing_audits),
        "missing_audits": missing_audits,
        "summary": {
            "compare_failed_count": sum(1 for row in rows if row.get("compare_gate_passed") is False),
            "compare_passed_count": sum(1 for row in rows if row.get("compare_gate_passed") is True),
            "registration_hard_failure_variant_count": sum(
                1
                for row in rows
                if int(row.get("failed_triangle_frame_count") or 0) > 0
                or int(row.get("quality_gate_failed_count") or 0) > 0
                or int(row.get("parse_error_count") or 0) > 0
            ),
        },
        "recommendation": _recommendation(rows),
        "rows": rows,
        "correlations": correlations,
        "top_correlations": correlations_ranked[:12],
    }


def write_resident_registration_compare_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resident Registration Candidate Compare",
        "",
        f"- Sweep summary: `{payload['sweep_summary']}`",
        f"- Audit root: `{payload['audit_root']}`",
        f"- Variants: `{payload['variant_count']}`",
        f"- Missing audits: `{payload['missing_audit_count']}`",
        f"- Recommendation: `{payload['recommendation']['status']}`",
        f"- Next target: `{payload['recommendation']['next_target']}`",
        "",
        "## Rows",
        "",
        "| Variant | Compare | RMS | P99 | Failed Reg | Cand Median | Fit RMS Median | Pixel RMS Median | Pixel NCC Median |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['variant_id']}` | `{row.get('compare_gate_status')}` | "
            f"`{row.get('rms_diff')}` | `{row.get('abs_diff_p99')}` | "
            f"`{row.get('failed_triangle_frame_count')}` | `{row.get('candidate_count_median')}` | "
            f"`{row.get('fit_rms_px_median')}` | `{row.get('pixel_rms_adu_median')}` | "
            f"`{row.get('pixel_ncc_median')}` |"
        )
    if payload["top_correlations"]:
        lines.extend(["", "## Top Correlations", ""])
        for item in payload["top_correlations"]:
            lines.append(
                f"- `{item['metric']}` vs `{item['target']}`: "
                f"pearson=`{item['pearson']}`, pairs=`{item['pair_count']}`"
            )
    if payload["missing_audits"]:
        lines.extend(["", "## Missing Audits", ""])
        for variant_id in payload["missing_audits"]:
            lines.append(f"- `{variant_id}`")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_registration_compare(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown:
        write_resident_registration_compare_markdown(markdown, payload)
