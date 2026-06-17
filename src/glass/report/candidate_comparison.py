from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.benchmark_contract import collect_frame_accounting_record


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(
    name: str,
    passed: bool,
    evidence: dict[str, Any],
    *,
    required: bool = True,
    note: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "required": bool(required),
        "evidence": evidence,
        "note": note,
    }


def _load_run_timing(run: Path) -> dict[str, Any]:
    path = run / "run_timing.json"
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _elapsed_from_timing(timing: dict[str, Any]) -> float | None:
    elapsed = _float_or_none(timing.get("total_elapsed_s"))
    if elapsed is not None:
        return elapsed
    stages = timing.get("stages")
    if not isinstance(stages, list):
        return None
    return float(sum(_float_or_none((stage or {}).get("elapsed_s")) or 0.0 for stage in stages if isinstance(stage, dict)))


def _first_resident_artifact(run: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = run / "resident_artifacts.json"
    if not path.exists():
        return {}, {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {}, {}
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts or not isinstance(artifacts[0], dict):
        return payload, {}
    return payload, artifacts[0]


def _frame_accounting_summary(run: Path) -> dict[str, Any]:
    accounting = collect_frame_accounting_record(run)
    summary = accounting.get("summary") if isinstance(accounting.get("summary"), dict) else {}
    return {
        "input_light_frames": summary.get("input_light_frames"),
        "integrated_frames": summary.get("integrated_frames"),
        "zero_weight_frames": summary.get("zero_weight_frames"),
        "registration_accepted_frames": summary.get("registration_accepted_frames"),
        "final_status_counts": summary.get("final_status_counts"),
        "integration_source_stage": accounting.get("integration_source_stage"),
    }


def _load_run_summary(run: str | Path) -> dict[str, Any]:
    root = Path(run)
    timing = _load_run_timing(root)
    resident, artifact = _first_resident_artifact(root)
    timing_s = artifact.get("timing_s") if isinstance(artifact.get("timing_s"), dict) else {}
    return {
        "path": str(root),
        "elapsed_s": _elapsed_from_timing(timing),
        "backend": timing.get("backend") or resident.get("backend"),
        "memory_mode": timing.get("memory_mode"),
        "device": resident.get("device") if isinstance(resident.get("device"), dict) else None,
        "master_path": artifact.get("master_path"),
        "coverage_map_path": artifact.get("coverage_map_path"),
        "high_rejection_map_path": artifact.get("high_rejection_map_path"),
        "low_rejection_map_path": artifact.get("low_rejection_map_path"),
        "frame_accounting": _frame_accounting_summary(root),
        "timing_s": {
            key: timing_s.get(key)
            for key in [
                "master_build_or_load",
                "light_read_upload_calibrate",
                "light_read_wait_wall",
                "light_h2d_calibrate_store",
                "resident_registration_warp",
                "resident_integration",
                "output_write",
                "gc",
            ]
            if key in timing_s
        },
    }


def _load_compare(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _read_object(path)
    region = payload.get("comparison_region") if isinstance(payload.get("comparison_region"), dict) else {}
    timing = payload.get("timing") if isinstance(payload.get("timing"), dict) else {}
    return {
        "path": str(path),
        "shape_match": payload.get("shape_match"),
        "mean_diff": _float_or_none(payload.get("mean_diff")),
        "rms_diff": _float_or_none(payload.get("rms_diff")),
        "abs_diff_p50": _float_or_none(payload.get("abs_diff_p50")),
        "abs_diff_p90": _float_or_none(payload.get("abs_diff_p90")),
        "abs_diff_p99": _float_or_none(payload.get("abs_diff_p99")),
        "abs_diff_p999": _float_or_none(payload.get("abs_diff_p999")),
        "relative_rms_diff": _float_or_none(payload.get("relative_rms_diff")),
        "coverage_fraction": _float_or_none(region.get("coverage_fraction")),
        "compared_pixels": region.get("compared_pixels"),
        "ignore_border_px": region.get("ignore_border_px"),
        "min_coverage": region.get("min_coverage"),
        "glass_coverage_map": region.get("glass_coverage_map"),
        "glass_time_seconds": _float_or_none(timing.get("glass_time_seconds")),
        "reference_time_seconds": _float_or_none(timing.get("reference_time_seconds")),
        "speedup_vs_reference": _float_or_none(timing.get("speedup_vs_reference")),
    }


def _load_acceptance(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _read_object(path)
    speedup = payload.get("speedup_summary") if isinstance(payload.get("speedup_summary"), dict) else {}
    glass = speedup.get("glass") if isinstance(speedup.get("glass"), dict) else {}
    return {
        "path": str(path),
        "status": payload.get("status"),
        "passed": bool(payload.get("passed")),
        "speedup_vs_wbpp": _float_or_none(speedup.get("speedup_vs_wbpp")),
        "glass_elapsed_s": _float_or_none(glass.get("elapsed_s")),
        "weighted_frame_count": glass.get("weighted_frame_count"),
        "zero_weight_frame_count": glass.get("zero_weight_frame_count"),
        "failed_checks": [
            item.get("name")
            for item in payload.get("checks", [])
            if isinstance(item, dict) and not item.get("passed")
        ],
    }


def _relative_delta(candidate: float | None, baseline: float | None) -> float | None:
    if candidate is None or baseline is None or baseline == 0.0:
        return None
    return float((candidate - baseline) / abs(baseline))


def _faster_than_reference(candidate: dict[str, Any], acceptance: dict[str, Any] | None) -> float | None:
    if acceptance is not None and acceptance.get("speedup_vs_wbpp") is not None:
        return _float_or_none(acceptance.get("speedup_vs_wbpp"))
    elapsed = _float_or_none(candidate.get("elapsed_s"))
    return None if not elapsed else None


def build_candidate_comparison(
    *,
    baseline_run: str | Path,
    candidate_run: str | Path,
    candidate_id: str = "candidate",
    baseline_compare_json: str | Path | None = None,
    candidate_compare_json: str | Path | None = None,
    candidate_vs_baseline_json: str | Path | None = None,
    candidate_acceptance_json: str | Path | None = None,
    baseline_acceptance_json: str | Path | None = None,
    max_reference_rms_growth: float = 1.05,
    max_reference_p99_growth: float = 1.05,
    max_candidate_vs_baseline_rms: float | None = None,
    min_speedup_vs_reference: float | None = None,
) -> dict[str, Any]:
    if max_reference_rms_growth < 1.0:
        raise ValueError("max_reference_rms_growth must be >= 1.0")
    if max_reference_p99_growth < 1.0:
        raise ValueError("max_reference_p99_growth must be >= 1.0")
    if max_candidate_vs_baseline_rms is not None and max_candidate_vs_baseline_rms < 0.0:
        raise ValueError("max_candidate_vs_baseline_rms must be non-negative")
    if min_speedup_vs_reference is not None and min_speedup_vs_reference < 0.0:
        raise ValueError("min_speedup_vs_reference must be non-negative")

    baseline = _load_run_summary(baseline_run)
    candidate = _load_run_summary(candidate_run)
    baseline_compare = _load_compare(baseline_compare_json)
    candidate_compare = _load_compare(candidate_compare_json)
    candidate_vs_baseline = _load_compare(candidate_vs_baseline_json)
    baseline_acceptance = _load_acceptance(baseline_acceptance_json)
    candidate_acceptance = _load_acceptance(candidate_acceptance_json)

    baseline_elapsed = _float_or_none(baseline.get("elapsed_s"))
    candidate_elapsed = _float_or_none(candidate.get("elapsed_s"))
    elapsed_delta = None
    elapsed_ratio = None
    if baseline_elapsed is not None and candidate_elapsed is not None and baseline_elapsed > 0.0:
        elapsed_delta = float(candidate_elapsed - baseline_elapsed)
        elapsed_ratio = float(candidate_elapsed / baseline_elapsed)

    checks: list[dict[str, Any]] = []
    if candidate_acceptance is None:
        checks.append(
            _check(
                "candidate_acceptance_available",
                False,
                {"path": None},
                note="A measured candidate should carry the same acceptance audit as the benchmark baseline.",
            )
        )
    else:
        checks.append(
            _check(
                "candidate_acceptance_passed",
                candidate_acceptance.get("passed") is True,
                {
                    "path": candidate_acceptance.get("path"),
                    "status": candidate_acceptance.get("status"),
                    "failed_checks": candidate_acceptance.get("failed_checks"),
                },
            )
        )
        if min_speedup_vs_reference is not None:
            speedup = _faster_than_reference(candidate, candidate_acceptance)
            checks.append(
                _check(
                    "candidate_minimum_speedup_vs_reference",
                    speedup is not None and speedup >= min_speedup_vs_reference,
                    {"actual": speedup, "required_min": min_speedup_vs_reference},
                )
            )

    if baseline_compare is None or candidate_compare is None:
        checks.append(
            _check(
                "reference_compares_available",
                False,
                {
                    "baseline_compare_json": None if baseline_compare_json is None else str(baseline_compare_json),
                    "candidate_compare_json": None if candidate_compare_json is None else str(candidate_compare_json),
                },
            )
        )
    else:
        baseline_rms = _float_or_none(baseline_compare.get("rms_diff"))
        candidate_rms = _float_or_none(candidate_compare.get("rms_diff"))
        baseline_p99 = _float_or_none(baseline_compare.get("abs_diff_p99"))
        candidate_p99 = _float_or_none(candidate_compare.get("abs_diff_p99"))
        checks.extend(
            [
                _check(
                    "reference_shape_matches",
                    baseline_compare.get("shape_match") is True and candidate_compare.get("shape_match") is True,
                    {
                        "baseline_shape_match": baseline_compare.get("shape_match"),
                        "candidate_shape_match": candidate_compare.get("shape_match"),
                    },
                ),
                _check(
                    "candidate_reference_rms_not_worse",
                    baseline_rms is not None
                    and candidate_rms is not None
                    and candidate_rms <= max(baseline_rms * max_reference_rms_growth, baseline_rms + 1e-12),
                    {
                        "baseline_rms_diff": baseline_rms,
                        "candidate_rms_diff": candidate_rms,
                        "allowed_growth_factor": max_reference_rms_growth,
                        "relative_delta": _relative_delta(candidate_rms, baseline_rms),
                    },
                ),
                _check(
                    "candidate_reference_p99_not_worse",
                    baseline_p99 is not None
                    and candidate_p99 is not None
                    and candidate_p99 <= max(baseline_p99 * max_reference_p99_growth, baseline_p99 + 1e-12),
                    {
                        "baseline_abs_diff_p99": baseline_p99,
                        "candidate_abs_diff_p99": candidate_p99,
                        "allowed_growth_factor": max_reference_p99_growth,
                        "relative_delta": _relative_delta(candidate_p99, baseline_p99),
                    },
                ),
            ]
        )

    if candidate_vs_baseline is not None:
        required = max_candidate_vs_baseline_rms is not None
        drift_rms = _float_or_none(candidate_vs_baseline.get("rms_diff"))
        checks.append(
            _check(
                "candidate_vs_baseline_shape_match",
                candidate_vs_baseline.get("shape_match") is True,
                {
                    "shape_match": candidate_vs_baseline.get("shape_match"),
                    "rms_diff": drift_rms,
                    "abs_diff_p99": candidate_vs_baseline.get("abs_diff_p99"),
                },
                required=required,
            )
        )
        if max_candidate_vs_baseline_rms is not None:
            checks.append(
                _check(
                    "candidate_vs_baseline_rms_within_limit",
                    drift_rms is not None and drift_rms <= max_candidate_vs_baseline_rms,
                    {"actual": drift_rms, "required_max": max_candidate_vs_baseline_rms},
                )
            )

    accounting_matches = baseline.get("frame_accounting") == candidate.get("frame_accounting")
    checks.append(
        _check(
            "frame_accounting_matches_baseline",
            accounting_matches,
            {"baseline": baseline.get("frame_accounting"), "candidate": candidate.get("frame_accounting")},
        )
    )

    required_checks = [item for item in checks if item.get("required")]
    required_passed = all(item.get("passed") for item in required_checks)
    candidate_slower_than_baseline = (
        elapsed_ratio is not None and elapsed_ratio > 1.0
    )
    recommendation = "eligible_for_broader_sweep" if required_passed else "hold_candidate"
    if required_passed and candidate_slower_than_baseline:
        recommendation = "eligible_but_needs_runtime_sweep"

    return {
        "schema_version": 1,
        "artifact_type": "candidate_comparison",
        "created_at": now_iso(),
        "candidate_id": candidate_id,
        "baseline": baseline,
        "candidate": candidate,
        "acceptance": {
            "baseline": baseline_acceptance,
            "candidate": candidate_acceptance,
        },
        "comparisons": {
            "baseline_vs_reference": baseline_compare,
            "candidate_vs_reference": candidate_compare,
            "candidate_vs_baseline": candidate_vs_baseline,
        },
        "deltas": {
            "elapsed_s": elapsed_delta,
            "elapsed_ratio_candidate_over_baseline": elapsed_ratio,
            "candidate_slower_than_baseline": candidate_slower_than_baseline,
            "reference_rms_relative_delta": _relative_delta(
                None if candidate_compare is None else candidate_compare.get("rms_diff"),
                None if baseline_compare is None else baseline_compare.get("rms_diff"),
            ),
            "reference_abs_diff_p99_relative_delta": _relative_delta(
                None if candidate_compare is None else candidate_compare.get("abs_diff_p99"),
                None if baseline_compare is None else baseline_compare.get("abs_diff_p99"),
            ),
        },
        "thresholds": {
            "max_reference_rms_growth": float(max_reference_rms_growth),
            "max_reference_p99_growth": float(max_reference_p99_growth),
            "max_candidate_vs_baseline_rms": max_candidate_vs_baseline_rms,
            "min_speedup_vs_reference": min_speedup_vs_reference,
        },
        "checks": checks,
        "summary": {
            "status": "passed" if required_passed else "failed",
            "passed": required_passed,
            "recommendation": recommendation,
            "required_check_count": len(required_checks),
            "required_failed_count": sum(1 for item in required_checks if not item.get("passed")),
            "diagnostic_failed_count": sum(1 for item in checks if not item.get("required") and not item.get("passed")),
            "baseline_elapsed_s": baseline_elapsed,
            "candidate_elapsed_s": candidate_elapsed,
            "elapsed_ratio_candidate_over_baseline": elapsed_ratio,
            "candidate_speedup_vs_reference": None
            if candidate_acceptance is None
            else candidate_acceptance.get("speedup_vs_wbpp"),
        },
        "limitations": [
            "This artifact compares already measured GLASS candidates and does not execute or mutate image processing.",
            "A passed candidate is eligible for broader sweeps; it is not promoted to a default policy by this command.",
            "Reference agreement is only as comparable as the supplied compare JSON normalization, coverage, and border settings.",
        ],
    }


def write_candidate_comparison(
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
    deltas = payload.get("deltas") if isinstance(payload.get("deltas"), dict) else {}
    comparisons = payload.get("comparisons") if isinstance(payload.get("comparisons"), dict) else {}
    candidate_ref = comparisons.get("candidate_vs_reference") if isinstance(comparisons.get("candidate_vs_reference"), dict) else {}
    baseline_ref = comparisons.get("baseline_vs_reference") if isinstance(comparisons.get("baseline_vs_reference"), dict) else {}
    candidate_baseline = (
        comparisons.get("candidate_vs_baseline")
        if isinstance(comparisons.get("candidate_vs_baseline"), dict)
        else {}
    )
    lines = [
        "# Candidate Comparison",
        "",
        f"- Candidate: `{payload.get('candidate_id')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Baseline elapsed: `{summary.get('baseline_elapsed_s')}` s",
        f"- Candidate elapsed: `{summary.get('candidate_elapsed_s')}` s",
        f"- Candidate / baseline elapsed ratio: `{summary.get('elapsed_ratio_candidate_over_baseline')}`",
        f"- Candidate speedup vs reference: `{summary.get('candidate_speedup_vs_reference')}`",
        f"- Reference RMS delta: `{deltas.get('reference_rms_relative_delta')}`",
        f"- Reference p99 delta: `{deltas.get('reference_abs_diff_p99_relative_delta')}`",
        "",
        "## Reference Metrics",
        "",
        "| metric | baseline | candidate |",
        "| --- | ---: | ---: |",
        f"| rms_diff | {baseline_ref.get('rms_diff')} | {candidate_ref.get('rms_diff')} |",
        f"| abs_diff_p99 | {baseline_ref.get('abs_diff_p99')} | {candidate_ref.get('abs_diff_p99')} |",
        f"| coverage_fraction | {baseline_ref.get('coverage_fraction')} | {candidate_ref.get('coverage_fraction')} |",
        f"| compared_pixels | {baseline_ref.get('compared_pixels')} | {candidate_ref.get('compared_pixels')} |",
        "",
        "## Candidate vs Baseline",
        "",
        f"- RMS diff: `{candidate_baseline.get('rms_diff')}`",
        f"- Abs diff p99: `{candidate_baseline.get('abs_diff_p99')}`",
        f"- Shape match: `{candidate_baseline.get('shape_match')}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks", []):
        if not isinstance(item, dict):
            continue
        marker = "PASS" if item.get("passed") else "FAIL"
        required = "required" if item.get("required") else "diagnostic"
        lines.append(f"- `{marker}` `{required}` {item.get('name')}: {item.get('evidence')}")
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
