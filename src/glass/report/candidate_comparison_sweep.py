from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_comparison(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"candidate comparison must be a JSON object: {path}")
    if payload.get("artifact_type") != "candidate_comparison":
        raise ValueError(f"expected candidate_comparison artifact at {path}, got {payload.get('artifact_type')}")
    return payload


def _row(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    deltas = payload.get("deltas") if isinstance(payload.get("deltas"), dict) else {}
    comparisons = payload.get("comparisons") if isinstance(payload.get("comparisons"), dict) else {}
    candidate_ref = comparisons.get("candidate_vs_reference") if isinstance(comparisons.get("candidate_vs_reference"), dict) else {}
    candidate_baseline = (
        comparisons.get("candidate_vs_baseline")
        if isinstance(comparisons.get("candidate_vs_baseline"), dict)
        else {}
    )
    failed_required = [
        item.get("name")
        for item in payload.get("checks", [])
        if isinstance(item, dict) and item.get("required") and not item.get("passed")
    ]
    passed = bool(summary.get("passed"))
    elapsed = _float_or_none(summary.get("candidate_elapsed_s"))
    rms = _float_or_none(candidate_ref.get("rms_diff"))
    p99 = _float_or_none(candidate_ref.get("abs_diff_p99"))
    speedup = _float_or_none(summary.get("candidate_speedup_vs_reference"))
    score = 0.0
    score += 1_000_000.0 if passed else 0.0
    score += float(speedup or 0.0) * 1000.0
    score -= float(elapsed or 1_000_000.0)
    score -= float(rms or 1.0) * 10_000.0
    score -= float(p99 or 1.0) * 1000.0
    return {
        "path": str(path),
        "candidate_id": payload.get("candidate_id"),
        "status": summary.get("status"),
        "passed": passed,
        "recommendation": summary.get("recommendation"),
        "candidate_elapsed_s": elapsed,
        "baseline_elapsed_s": _float_or_none(summary.get("baseline_elapsed_s")),
        "elapsed_ratio_candidate_over_baseline": _float_or_none(
            summary.get("elapsed_ratio_candidate_over_baseline")
        ),
        "candidate_speedup_vs_reference": speedup,
        "reference_rms_diff": rms,
        "reference_abs_diff_p99": p99,
        "reference_rms_relative_delta": _float_or_none(deltas.get("reference_rms_relative_delta")),
        "reference_abs_diff_p99_relative_delta": _float_or_none(
            deltas.get("reference_abs_diff_p99_relative_delta")
        ),
        "candidate_vs_baseline_rms": _float_or_none(candidate_baseline.get("rms_diff")),
        "candidate_vs_baseline_abs_diff_p99": _float_or_none(candidate_baseline.get("abs_diff_p99")),
        "failed_required_checks": failed_required,
        "score": score,
    }


def build_candidate_comparison_sweep(comparisons: list[str | Path]) -> dict[str, Any]:
    if not comparisons:
        raise ValueError("at least one candidate-comparison artifact is required")
    rows = [_row(path, _load_comparison(path)) for path in comparisons]
    rows.sort(
        key=lambda row: (
            bool(row.get("passed")),
            _float_or_none(row.get("candidate_speedup_vs_reference")) or 0.0,
            -(_float_or_none(row.get("candidate_elapsed_s")) or 1_000_000.0),
            -(_float_or_none(row.get("reference_rms_diff")) or 1.0),
            _float_or_none(row.get("score")) or 0.0,
        ),
        reverse=True,
    )
    passed_rows = [row for row in rows if row.get("passed")]
    top = rows[0]
    if not passed_rows:
        recommendation = "hold_all_candidates"
    elif str(top.get("recommendation")) == "eligible_but_needs_runtime_sweep":
        recommendation = "run_runtime_sweep_for_top_candidate"
    else:
        recommendation = "promote_top_candidate_to_broader_sweep"
    return {
        "schema_version": 1,
        "artifact_type": "candidate_comparison_sweep",
        "created_at": now_iso(),
        "candidate_count": len(rows),
        "summary": {
            "status": "passed" if passed_rows else "failed",
            "passed": bool(passed_rows),
            "candidate_count": len(rows),
            "passed_candidate_count": len(passed_rows),
            "top_candidate_id": top.get("candidate_id"),
            "top_candidate_status": top.get("status"),
            "top_candidate_recommendation": top.get("recommendation"),
            "recommendation": recommendation,
        },
        "candidates": rows,
        "limitations": [
            "This sweep ranks already measured candidate-comparison artifacts only.",
            "It does not execute integration, compare images, or change pipeline defaults.",
            "Ranking favors passed acceptance, speedup, runtime, and reference agreement for this benchmark only.",
        ],
    }


def write_candidate_comparison_sweep(
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
        "# Candidate Comparison Sweep",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Candidate count: `{summary.get('candidate_count')}`",
        f"- Passed candidates: `{summary.get('passed_candidate_count')}`",
        f"- Top candidate: `{summary.get('top_candidate_id')}`",
        "",
        "## Candidates",
        "",
        "| rank | candidate | passed | elapsed s | speedup | rms | p99 | recommendation |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for index, row in enumerate(payload.get("candidates") or [], start=1):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {rank} | {candidate} | {passed} | {elapsed} | {speedup} | {rms} | {p99} | {rec} |".format(
                rank=index,
                candidate=row.get("candidate_id"),
                passed=row.get("passed"),
                elapsed=row.get("candidate_elapsed_s"),
                speedup=row.get("candidate_speedup_vs_reference"),
                rms=row.get("reference_rms_diff"),
                p99=row.get("reference_abs_diff_p99"),
                rec=row.get("recommendation"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
