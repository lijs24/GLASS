from __future__ import annotations

from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag, StackRequest


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _shape(value: Any) -> tuple[int, ...] | None:
    if value is None:
        return None
    try:
        return tuple(int(part) for part in np.asarray(value).shape)
    except Exception:
        return None


def _summary_count(summary: dict[str, Any], key: str) -> int:
    try:
        return int(summary.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _summary_matches(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    keys = sorted({str(key) for key in actual} | {str(key) for key in expected})
    mismatches: dict[str, dict[str, int]] = {}
    for key in keys:
        actual_value = _summary_count(actual, key)
        expected_value = _summary_count(expected, key)
        if actual_value != expected_value:
            mismatches[key] = {"actual": actual_value, "expected": expected_value}
    return {
        "passed": not mismatches,
        "mismatches": mismatches,
    }


def _count_map_summary(value: np.ndarray) -> dict[str, int]:
    data = np.asarray(value, dtype=np.float32)
    finite = np.isfinite(data)
    finite_data = np.where(finite, data, 0.0)
    rounded = np.rint(finite_data)
    return {
        "positive_pixels": int(np.count_nonzero(finite_data > 0)),
        "rounded_sample_sum": int(round(float(np.sum(finite_data, dtype=np.float64)))),
        "nonfinite_pixels": int(np.count_nonzero(~finite)),
        "negative_pixels": int(np.count_nonzero(finite & (data < 0))),
        "fractional_pixels": int(np.count_nonzero(finite & (np.abs(data - rounded) > 1.0e-3))),
    }


def build_stack_engine_result_contract(
    result: Any,
    *,
    request: StackRequest | None = None,
) -> dict[str, Any]:
    """Build a compact invariant audit for a StackEngine result.

    This is intentionally in-memory and cheap: it validates map presence,
    shapes, DQ/provenance summaries, and simple count relationships before
    downstream code serializes the result into artifacts.
    """

    master = np.asarray(result.master)
    if master.ndim != 2:
        raise ValueError("StackEngine result master must be a 2D array")
    master_shape = tuple(int(part) for part in master.shape)
    pixel_count = int(master.size)
    maps = {
        "weight": result.weight_map,
        "coverage": result.coverage_map,
        "low_rejection": result.low_rejection_map,
        "high_rejection": result.high_rejection_map,
        "variance": result.variance_map,
        "dq": None if result.dq_mask is None else result.dq_mask.data,
    }
    requested = {
        "weight": bool(request.output_maps.weight) if request is not None else maps["weight"] is not None,
        "coverage": bool(request.output_maps.coverage) if request is not None else maps["coverage"] is not None,
        "low_rejection": bool(request.output_maps.low_rejection)
        if request is not None
        else maps["low_rejection"] is not None,
        "high_rejection": bool(request.output_maps.high_rejection)
        if request is not None
        else maps["high_rejection"] is not None,
        "variance": bool(request.output_maps.variance) if request is not None else maps["variance"] is not None,
        "dq": bool(request.output_maps.dq) if request is not None else maps["dq"] is not None,
    }

    checks: list[dict[str, Any]] = []
    missing_requested = sorted(name for name, required in requested.items() if required and maps[name] is None)
    checks.append(
        _check(
            "requested_maps_present",
            not missing_requested,
            {
                "requested": requested,
                "missing": missing_requested,
            },
        )
    )
    bad_shapes = {
        name: _shape(value)
        for name, value in maps.items()
        if value is not None and _shape(value) != master_shape
    }
    checks.append(
        _check(
            "maps_match_master_shape",
            not bad_shapes,
            {
                "master_shape": master_shape,
                "bad_shapes": bad_shapes,
            },
        )
    )
    checks.append(
        _check(
            "master_is_finite",
            bool(np.all(np.isfinite(master))),
            {
                "nonfinite_pixels": int(np.count_nonzero(~np.isfinite(master))),
                "total_pixels": pixel_count,
            },
        )
    )

    coverage = None if result.coverage_map is None else np.asarray(result.coverage_map, dtype=np.float32)
    dq_data = None if result.dq_mask is None else np.asarray(result.dq_mask.data, dtype=np.uint32)
    low = None if result.low_rejection_map is None else np.asarray(result.low_rejection_map, dtype=np.float32)
    high = None if result.high_rejection_map is None else np.asarray(result.high_rejection_map, dtype=np.float32)
    provenance = result.dq_provenance if isinstance(result.dq_provenance, dict) else {}
    provenance_summary = provenance.get("output_dq_summary") if isinstance(provenance.get("output_dq_summary"), dict) else {}
    dq_summary = result.dq_mask.summary() if result.dq_mask is not None else {}

    if coverage is not None and dq_data is not None:
        coverage_zero = int(np.count_nonzero((~np.isfinite(coverage)) | (coverage <= 0)))
        dq_no_data = int(np.count_nonzero((dq_data & np.uint32(int(DQFlag.NO_DATA))) != 0))
        checks.append(
            _check(
                "coverage_zero_matches_dq_no_data",
                coverage_zero == dq_no_data,
                {
                    "coverage_zero_pixels": coverage_zero,
                    "dq_no_data_pixels": dq_no_data,
                },
            )
        )
    if low is not None and dq_data is not None:
        low_pixels = int(np.count_nonzero(low > 0))
        dq_low = int(np.count_nonzero((dq_data & np.uint32(int(DQFlag.LOW_REJECTED))) != 0))
        checks.append(
            _check(
                "low_rejection_map_matches_dq",
                low_pixels == dq_low,
                {
                    "low_rejection_pixels": low_pixels,
                    "dq_low_rejected_pixels": dq_low,
                },
            )
        )
    if high is not None and dq_data is not None:
        high_pixels = int(np.count_nonzero(high > 0))
        dq_high = int(np.count_nonzero((dq_data & np.uint32(int(DQFlag.HIGH_REJECTED))) != 0))
        checks.append(
            _check(
                "high_rejection_map_matches_dq",
                high_pixels == dq_high,
                {
                    "high_rejection_pixels": high_pixels,
                    "dq_high_rejected_pixels": dq_high,
                },
            )
        )
    for label, rejection_map in (("low", low), ("high", high)):
        if rejection_map is None:
            continue
        summary = _count_map_summary(rejection_map)
        checks.append(
            _check(
                f"{label}_rejection_map_counts_are_valid",
                summary["nonfinite_pixels"] == 0
                and summary["negative_pixels"] == 0
                and summary["fractional_pixels"] == 0,
                summary,
                "Rejection maps are per-pixel rejected-sample counts.",
            )
        )
        metric_samples = _summary_count(result.metrics, f"{label}_rejected")
        checks.append(
            _check(
                f"{label}_rejection_sample_sum_matches_metrics",
                summary["rounded_sample_sum"] == metric_samples,
                {
                    "map_rejected_sample_sum": summary["rounded_sample_sum"],
                    "metrics_rejected_samples": metric_samples,
                },
            )
        )
        provenance_pixels = int(provenance.get(f"output_{label}_rejected_pixels") or 0)
        checks.append(
            _check(
                f"{label}_rejection_pixels_match_provenance",
                summary["positive_pixels"] == provenance_pixels,
                {
                    "map_positive_pixels": summary["positive_pixels"],
                    "provenance_rejected_pixels": provenance_pixels,
                },
                "Provenance records pixels touched by rejection, not rejected-sample totals.",
            )
        )

    summary_match = _summary_matches(dq_summary, provenance_summary)
    checks.append(
        _check(
            "dq_summary_matches_provenance",
            result.dq_mask is None or summary_match["passed"],
            {
                "dq_summary": dq_summary,
                "provenance_output_dq_summary": provenance_summary,
                "mismatches": summary_match["mismatches"],
            },
        )
    )
    if coverage is not None:
        coverage_sum = int(round(float(np.sum(coverage, dtype=np.float64))))
        metric_valid = int(result.metrics.get("valid_samples") or 0)
        checks.append(
            _check(
                "coverage_sum_matches_metrics",
                coverage_sum == metric_valid,
                {
                    "coverage_sum": coverage_sum,
                    "metrics_valid_samples": metric_valid,
                },
            )
        )
        provenance_zero = int(provenance.get("output_coverage_zero_pixels") or 0)
        coverage_zero = int(np.count_nonzero((~np.isfinite(coverage)) | (coverage <= 0)))
        checks.append(
            _check(
                "coverage_zero_matches_provenance",
                coverage_zero == provenance_zero,
                {
                    "coverage_zero_pixels": coverage_zero,
                    "provenance_zero_pixels": provenance_zero,
                },
            )
        )

    if request is not None:
        expected_samples = len(request.frame_ids) * pixel_count
        input_samples = int(provenance.get("input_samples") or 0)
        checks.append(
            _check(
                "input_samples_match_request_shape",
                expected_samples == input_samples,
                {
                    "expected_input_samples": expected_samples,
                    "provenance_input_samples": input_samples,
                    "frame_count": len(request.frame_ids),
                    "pixels_per_frame": pixel_count,
                },
            )
        )

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "contract_type": "stack_engine_result_contract",
        "passed": passed,
        "status": "passed" if passed else "failed",
        "master_shape": master_shape,
        "requested_maps": requested,
        "checks": checks,
    }
