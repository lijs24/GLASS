from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag, DQMask


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _shape(value: Any) -> tuple[int, ...] | None:
    if value is None:
        return None
    try:
        return tuple(int(part) for part in np.asarray(value).shape)
    except Exception:
        return None


def _finite_stats(value: Any) -> dict[str, Any]:
    if value is None:
        return {"present": False}
    data = np.asarray(value, dtype=np.float32)
    finite = data[np.isfinite(data)]
    return {
        "present": True,
        "shape": list(data.shape),
        "dtype": str(data.dtype),
        "finite_pixels": int(finite.size),
        "nonfinite_pixels": int(data.size - finite.size),
        "min": None if finite.size == 0 else float(np.min(finite)),
        "max": None if finite.size == 0 else float(np.max(finite)),
        "mean": None if finite.size == 0 else float(np.mean(finite, dtype=np.float64)),
        "rounded_sum": int(round(float(np.sum(np.nan_to_num(data), dtype=np.float64)))),
        "positive_pixels": int(np.count_nonzero(np.isfinite(data) & (data > 0))),
        "zero_or_less_pixels": int(np.count_nonzero((~np.isfinite(data)) | (data <= 0))),
        "negative_pixels": int(np.count_nonzero(np.isfinite(data) & (data < 0))),
        "fractional_pixels": int(np.count_nonzero(np.isfinite(data) & (np.abs(data - np.rint(data)) > 1.0e-3))),
    }


def _stats_for_map(
    name: str,
    value: Any,
    precomputed_map_stats: dict[str, Any],
) -> dict[str, Any]:
    stats = precomputed_map_stats.get(name)
    if isinstance(stats, dict):
        payload = dict(stats)
        payload.setdefault("present", value is not None)
        payload.setdefault("shape", None if _shape(value) is None else list(_shape(value) or ()))
        if value is not None and "dtype" not in payload:
            payload["dtype"] = str(np.asarray(value).dtype)
        payload.setdefault("stats_source", "precomputed")
        return payload
    return _finite_stats(value)


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return int(round(numeric))


def _summary_count(summary: dict[str, Any], key: str) -> int:
    value = _int_value(summary.get(key))
    return 0 if value is None else value


def _optional_count(stats: dict[str, Any], key: str) -> int | None:
    value = _int_value(stats.get(key))
    return value


def _map_required(output_policy: dict[str, Any] | None, map_name: str, *, fallback_present: bool) -> bool:
    policy = output_policy if isinstance(output_policy, dict) else {}
    skipped = {str(item) for item in policy.get("skipped") or []}
    available = {str(item) for item in policy.get("available") or []}
    written = {str(item) for item in policy.get("written") or []}
    if map_name in skipped:
        return False
    if available:
        return map_name in available or map_name in written
    return fallback_present


def _request_payload(
    *,
    frame_ids: list[str],
    source_kind: str,
    grouping_key: str | None,
    combine: str,
    rejection: str,
    low_sigma: float,
    high_sigma: float,
    output_maps: dict[str, bool],
    weights: dict[str, float],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "contract_type": "stack_request_payload",
        "frame_ids": frame_ids,
        "frame_count": len(frame_ids),
        "source_kind": source_kind,
        "combine": {"method": combine, "accumulator_dtype": "float32"},
        "rejection": {
            "method": rejection,
            "iterations": 0 if rejection == "none" else 1,
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
        },
        "output_maps": output_maps,
        "preprocess": (),
        "normalization": metadata.get("normalization"),
        "weights": weights,
        "grouping_key": grouping_key,
        "metadata": metadata,
    }


def _weights_from_values(frame_ids: list[str], weights: Any) -> dict[str, float]:
    if isinstance(weights, dict):
        return {str(key): float(value) for key, value in weights.items()}
    values = list(weights or [])
    return {
        frame_id: float(values[index]) if index < len(values) else 1.0
        for index, frame_id in enumerate(frame_ids)
    }


def _dq_summary_from_map(dq_map: Any) -> dict[str, int]:
    if dq_map is None:
        return {}
    return DQMask(np.asarray(dq_map, dtype=np.uint32)).summary()


def _sample_match(actual: int | None, expected: int | None, tolerance: int = 0) -> dict[str, Any]:
    delta = None if actual is None or expected is None else int(actual) - int(expected)
    return {
        "actual": actual,
        "expected": expected,
        "delta": delta,
        "passed": delta is not None and abs(delta) <= int(tolerance),
    }


def _positive_weight_count(weights_by_frame: dict[str, float]) -> int:
    count = 0
    for value in weights_by_frame.values():
        try:
            weight = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(weight) and weight > 0.0:
            count += 1
    return count


def _optional_float(stats: dict[str, Any], key: str) -> float | None:
    value = stats.get(key)
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(numeric):
        return None
    return numeric


def build_resident_integration_stack_surface_contract(
    *,
    filter_name: str,
    frame_ids: list[str],
    master: np.ndarray,
    weight_map: np.ndarray | None,
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    dq_map: np.ndarray | None,
    dq_summary: dict[str, Any],
    dq_provenance_summary: dict[str, Any],
    output_map_policy: dict[str, Any] | None,
    rejection: str,
    low_sigma: float,
    high_sigma: float,
    weights: Any,
    grouping_key: str | None = None,
    dispatch: str | None = None,
    map_paths: dict[str, str | None] | None = None,
    precomputed_map_stats: dict[str, Any] | None = None,
    trust_precomputed_dq_summary: bool = False,
) -> dict[str, Any]:
    """Build a StackRequest/StackResult-shaped contract for resident integration.

    The resident path still executes through the CUDA resident backend, but this
    contract is emitted while the result arrays are in memory so DQ, coverage,
    weight, and rejection semantics are checked at the same surface boundary as
    the CPU StackEngine.
    """

    frame_id_list = [str(frame_id) for frame_id in frame_ids]
    weights_by_frame = _weights_from_values(frame_id_list, weights)
    dq_summary_payload = dq_summary if isinstance(dq_summary, dict) else {}
    dq_provenance_payload = (
        dq_provenance_summary if isinstance(dq_provenance_summary, dict) else {}
    )
    maps = {
        "master": master,
        "weight": weight_map,
        "coverage": coverage_map,
        "low_rejection": low_rejection_map,
        "high_rejection": high_rejection_map,
        "dq": dq_map,
    }
    output_maps = {
        name: _map_required(output_map_policy, name, fallback_present=value is not None)
        for name, value in maps.items()
        if name != "master"
    }
    request = _request_payload(
        frame_ids=frame_id_list,
        source_kind="light",
        grouping_key=grouping_key or filter_name,
        combine="mean",
        rejection=str(rejection),
        low_sigma=float(low_sigma),
        high_sigma=float(high_sigma),
        output_maps=output_maps,
        weights=weights_by_frame,
        metadata={
            "engine": "cuda_resident_stack",
            "memory_mode": "resident",
            "filter": filter_name,
            "dispatch": dispatch,
            "normalization": None,
        },
    )

    master_shape = _shape(master)
    map_paths = map_paths or {}
    stats_by_map: dict[str, dict[str, Any]] = {}
    precomputed_map_stats = precomputed_map_stats or {}
    map_rows = []
    for name, value in maps.items():
        stats = _stats_for_map(name, value, precomputed_map_stats)
        stats_by_map[name] = stats
        map_rows.append(
            {
                "map": name,
                "required": True if name == "master" else bool(output_maps.get(name)),
                "present": value is not None,
                "shape": None if _shape(value) is None else list(_shape(value) or ()),
                "path": map_paths.get(name),
                "stats": stats,
            }
        )

    missing_required = [
        row["map"] for row in map_rows if row["required"] and not row["present"]
    ]
    bad_shapes = {
        row["map"]: row["shape"]
        for row in map_rows
        if row["present"] and tuple(row["shape"] or ()) != master_shape
    }
    master_nonfinite = _optional_count(stats_by_map.get("master", {}), "nonfinite_pixels")
    if master_nonfinite is None:
        master_nonfinite = int(np.count_nonzero(~np.isfinite(np.asarray(master, dtype=np.float32))))
    checks = [
        _check("request_has_frame_ids", bool(frame_id_list), {"frame_count": len(frame_id_list)}),
        _check(
            "request_weights_match_frames",
            set(weights_by_frame) == set(frame_id_list),
            {"frame_count": len(frame_id_list), "weight_count": len(weights_by_frame)},
        ),
        _check("requested_maps_present", not missing_required, {"missing": missing_required}),
        _check("maps_match_master_shape", not bad_shapes, {"master_shape": master_shape, "bad_shapes": bad_shapes}),
        _check(
            "master_is_finite",
            master_nonfinite == 0,
            {
                "nonfinite_pixels": master_nonfinite,
                "source": stats_by_map.get("master", {}).get("stats_source", "array_scan"),
            },
        ),
    ]

    if dq_map is not None:
        if trust_precomputed_dq_summary:
            actual_dq_summary = dict(dq_summary_payload)
            checks.append(
                _check(
                    "dq_summary_matches_dq_map",
                    True,
                    {
                        "mismatches": {},
                        "source": "trusted_precomputed_dq_summary",
                    },
                    note=(
                        "DQ summary was produced when the resident DQ map was built; "
                        "the resident result-contract pixel verifier remains the full disk-backed audit."
                    ),
                )
            )
        else:
            actual_dq_summary = _dq_summary_from_map(dq_map)
            mismatches = {
                key: {
                    "actual": _summary_count(actual_dq_summary, key),
                    "expected": _summary_count(dq_summary_payload, key),
                }
                for key in sorted(set(actual_dq_summary) | {str(item) for item in dq_summary_payload})
                if _summary_count(actual_dq_summary, key) != _summary_count(dq_summary_payload, key)
            }
            checks.append(_check("dq_summary_matches_dq_map", not mismatches, {"mismatches": mismatches}))

    if coverage_map is not None:
        coverage_stats = stats_by_map.get("coverage", {})
        coverage_zero = _optional_count(coverage_stats, "zero_or_less_pixels")
        valid_samples = _optional_count(coverage_stats, "rounded_sum")
        coverage_positive_pixels = _optional_count(coverage_stats, "positive_pixels")
        coverage_max = _optional_float(coverage_stats, "max")
        if coverage_zero is None or valid_samples is None:
            coverage = np.asarray(coverage_map, dtype=np.float32)
            coverage_zero = int(np.count_nonzero((~np.isfinite(coverage)) | (coverage <= 0.0)))
            valid_samples = int(round(float(np.nansum(coverage, dtype=np.float64))))
            coverage_positive_pixels = int(np.count_nonzero(np.isfinite(coverage) & (coverage > 0.0)))
            finite_coverage = coverage[np.isfinite(coverage)]
            coverage_max = None if finite_coverage.size == 0 else float(np.max(finite_coverage))
        expected_valid = _int_value(dq_provenance_payload.get("valid_samples_after_rejection"))
        active_frame_count = _int_value(dq_provenance_payload.get("active_frame_count"))
        post_rejection_pixels = _int_value(dq_provenance_payload.get("post_rejection_pixels"))
        positive_weight_count = _positive_weight_count(weights_by_frame)
        checks.append(
            _check(
                "active_frame_count_matches_positive_weights",
                active_frame_count is not None and active_frame_count == positive_weight_count,
                {
                    "active_frame_count": active_frame_count,
                    "positive_weight_frame_count": positive_weight_count,
                    "frame_count": len(frame_id_list),
                },
                "Resident active frame count must close against StackRequest positive frame weights.",
            )
        )
        checks.append(
            _check(
                "coverage_max_within_active_frame_count",
                active_frame_count is not None
                and coverage_max is not None
                and coverage_max <= float(active_frame_count) + 1.0e-3,
                {
                    "coverage_max": coverage_max,
                    "active_frame_count": active_frame_count,
                },
                "Post-rejection coverage cannot exceed the active positive-weight frame count.",
            )
        )
        if post_rejection_pixels is not None:
            checks.append(
                _check(
                    "coverage_positive_pixels_match_post_rejection_pixels",
                    coverage_positive_pixels == post_rejection_pixels,
                    {
                        "coverage_positive_pixels": coverage_positive_pixels,
                        "post_rejection_pixels": post_rejection_pixels,
                    },
                    "Post-rejection pixel count and positive coverage pixels describe the same output support.",
                )
            )
        if dq_map is not None:
            if trust_precomputed_dq_summary:
                dq_no_data = _summary_count(dq_summary_payload, "no_data")
            else:
                dq_data = np.asarray(dq_map, dtype=np.uint32)
                dq_no_data = int(np.count_nonzero((dq_data & np.uint32(int(DQFlag.NO_DATA))) != 0))
            checks.append(
                _check(
                    "coverage_zero_matches_dq_no_data",
                    coverage_zero == dq_no_data,
                    {"coverage_zero_pixels": coverage_zero, "dq_no_data_pixels": dq_no_data},
                )
            )
        if expected_valid is not None:
            checks.append(
                _check(
                    "coverage_sum_matches_provenance",
                    valid_samples == expected_valid,
                    {"coverage_sum": valid_samples, "provenance_valid_samples": expected_valid},
                )
            )

    if weight_map is not None:
        weight_stats = stats_by_map.get("weight", {})
        weight_positive_pixels = _optional_count(weight_stats, "positive_pixels")
        if weight_positive_pixels is None:
            weight = np.asarray(weight_map, dtype=np.float32)
            weight_positive_pixels = int(np.count_nonzero(np.isfinite(weight) & (weight > 0.0)))
        post_rejection_pixels = _int_value(dq_provenance_payload.get("post_rejection_pixels"))
        if post_rejection_pixels is not None:
            checks.append(
                _check(
                    "weight_positive_pixels_match_post_rejection_pixels",
                    weight_positive_pixels == post_rejection_pixels,
                    {
                        "weight_positive_pixels": weight_positive_pixels,
                        "post_rejection_pixels": post_rejection_pixels,
                    },
                    "Resident weight support must match the post-rejection output support.",
                )
            )

    low_samples = None
    high_samples = None
    if low_rejection_map is not None:
        low_stats = stats_by_map.get("low_rejection", {})
        if not low_stats:
            low_stats = _finite_stats(low_rejection_map)
        low_samples = int(low_stats["rounded_sum"])
        checks.append(
            _check(
                "low_rejection_map_counts_are_valid",
                low_stats["nonfinite_pixels"] == 0
                and low_stats["negative_pixels"] == 0
                and low_stats["fractional_pixels"] == 0,
                low_stats,
            )
        )
        if dq_map is not None:
            if trust_precomputed_dq_summary:
                dq_low = _summary_count(dq_summary_payload, "low_rejected")
            else:
                dq_low = int(np.count_nonzero((np.asarray(dq_map, dtype=np.uint32) & np.uint32(int(DQFlag.LOW_REJECTED))) != 0))
            checks.append(
                _check(
                    "low_rejection_pixels_match_dq",
                    int(low_stats["positive_pixels"]) == dq_low,
                    {"map_positive_pixels": low_stats["positive_pixels"], "dq_low_rejected_pixels": dq_low},
                )
            )
    if high_rejection_map is not None:
        high_stats = stats_by_map.get("high_rejection", {})
        if not high_stats:
            high_stats = _finite_stats(high_rejection_map)
        high_samples = int(high_stats["rounded_sum"])
        checks.append(
            _check(
                "high_rejection_map_counts_are_valid",
                high_stats["nonfinite_pixels"] == 0
                and high_stats["negative_pixels"] == 0
                and high_stats["fractional_pixels"] == 0,
                high_stats,
            )
        )
        if dq_map is not None:
            if trust_precomputed_dq_summary:
                dq_high = _summary_count(dq_summary_payload, "high_rejected")
            else:
                dq_high = int(np.count_nonzero((np.asarray(dq_map, dtype=np.uint32) & np.uint32(int(DQFlag.HIGH_REJECTED))) != 0))
            checks.append(
                _check(
                    "high_rejection_pixels_match_dq",
                    int(high_stats["positive_pixels"]) == dq_high,
                    {"map_positive_pixels": high_stats["positive_pixels"], "dq_high_rejected_pixels": dq_high},
                )
            )
    if low_samples is not None or high_samples is not None:
        actual_rejected = int(low_samples or 0) + int(high_samples or 0)
        expected_rejected = _int_value(dq_provenance_payload.get("rejected_samples"))
        checks.append(
            _check(
                "rejection_sample_sum_matches_provenance",
                bool(_sample_match(actual_rejected, expected_rejected)["passed"]),
                _sample_match(actual_rejected, expected_rejected),
            )
        )

    closure = dq_provenance_payload.get("sample_accounting_closure")
    if isinstance(closure, dict) and closure.get("status") in {"passed", "failed"}:
        checks.append(
            _check(
                "sample_accounting_closure_valid",
                closure.get("status") == "passed",
                closure,
            )
        )

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "contract_type": "resident_stack_engine_surface_contract",
        "surface": "integration",
        "engine_family": "cuda_resident_stack",
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "stack_request": request,
        "stack_result": {
            "master_shape": None if master_shape is None else list(master_shape),
            "maps": map_rows,
            "dq_summary": dict(dq_summary_payload),
            "dq_provenance_summary": dict(dq_provenance_payload),
        },
        "checks": checks,
    }


def build_resident_master_stack_surface_contract(
    *,
    name: str,
    master_type: str,
    path: str | None,
    stats: dict[str, Any],
    frame_ids: list[str],
    frame_count: Any,
    shape: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    frame_id_list = [str(frame_id) for frame_id in frame_ids]
    count = _int_value(frame_count)
    stats_present = all(key in stats for key in ("min", "max", "mean", "median", "std"))
    path_exists = bool(path and Path(path).exists())
    request = _request_payload(
        frame_ids=frame_id_list,
        source_kind=str(master_type),
        grouping_key=name,
        combine="mean",
        rejection=str(policy.get("master_rejection") or "none"),
        low_sigma=0.0,
        high_sigma=0.0,
        output_maps={
            "coverage": False,
            "weight": False,
            "low_rejection": False,
            "high_rejection": False,
            "dq": False,
        },
        weights={frame_id: 1.0 for frame_id in frame_id_list},
        metadata={
            "engine": "cuda_resident_stack",
            "memory_mode": "resident",
            "master_type": master_type,
            "normalization": policy.get("flat_normalization") if master_type == "flat" else None,
        },
    )
    checks = [
        _check(
            "request_frame_ids_recorded",
            bool(frame_id_list) and (count is None or len(frame_id_list) == count),
            {"frame_ids": frame_id_list, "frame_count": count},
        ),
        _check("master_path_exists", path_exists, {"path": path}),
        _check(
            "master_stats_present",
            stats_present,
            {"required": ["min", "max", "mean", "median", "std"], "present": sorted(stats)},
        ),
        _check(
            "master_shape_recorded",
            _int_value(shape.get("height")) is not None and _int_value(shape.get("width")) is not None,
            {"shape": shape},
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "contract_type": "resident_stack_engine_surface_contract",
        "surface": "master_calibration",
        "engine_family": "cuda_resident_stack",
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "stack_request": request,
        "stack_result": {
            "master_shape": [int(shape.get("height") or 0), int(shape.get("width") or 0)],
            "path": path,
            "stats": {key: stats.get(key) for key in ("min", "max", "mean", "median", "std")},
        },
        "checks": checks,
    }
