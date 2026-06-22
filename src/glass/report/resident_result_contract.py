from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.rejection import (
    CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
    RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
    RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_PARITY_STATUS,
    RESIDENT_WINSORIZED_SIGMA_PARITY_STATUS,
    RESIDENT_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
    resident_rejection_descriptor,
)
from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.dq_map_verify import summarize_count_map_pixels, summarize_dq_map_pixels


_CORE_MAPS = {
    "master": "master_path",
    "weight": "weight_map_path",
    "coverage": "coverage_map_path",
    "dq": "dq_map_path",
}

_REJECTION_MAPS = {
    "low_rejection": "low_rejection_map_path",
    "high_rejection": "high_rejection_map_path",
}


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _resolve_path(path_value: Any, run_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    if path.is_absolute():
        return path
    run_relative = run_root / path
    if run_relative.exists():
        return run_relative
    if path.exists():
        return path
    return run_relative


def _path_exists(path_value: Any, run_root: Path) -> bool:
    path = _resolve_path(path_value, run_root)
    return bool(path and path.exists())


def _policy_items(output: dict[str, Any], key: str) -> set[str]:
    policy = output.get("output_map_policy") if isinstance(output.get("output_map_policy"), dict) else {}
    value = policy.get(key)
    return {str(item) for item in value} if isinstance(value, list) else set()


def _map_required(output: dict[str, Any], map_name: str, *, rejection: str) -> bool:
    skipped = map_name in _policy_items(output, "skipped")
    available = _policy_items(output, "available")
    if skipped:
        return False
    if available and map_name not in available:
        return False
    if map_name in _REJECTION_MAPS:
        return rejection != "none"
    return map_name in {"master", "weight", "coverage", "dq"}


def _map_rows(output: dict[str, Any], run_root: Path, *, rejection: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for map_name, path_key in {**_CORE_MAPS, **_REJECTION_MAPS}.items():
        required = _map_required(output, map_name, rejection=rejection)
        path_value = output.get(path_key)
        exists = _path_exists(path_value, run_root)
        rows.append(
            {
                "map": map_name,
                "path_key": path_key,
                "path": path_value,
                "required": required,
                "exists": exists,
                "policy_skipped": map_name in _policy_items(output, "skipped"),
                "ok": bool(exists or not required),
            }
        )
    return rows


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _sample_match(actual: int | None, expected: int | None, tolerance: int) -> dict[str, Any]:
    delta = None if actual is None or expected is None else int(actual) - int(expected)
    return {
        "actual": actual,
        "expected": expected,
        "delta": delta,
        "passed": delta is not None and abs(delta) <= int(tolerance),
    }


def _summary_matches(dq_summary: dict[str, Any], provenance_summary: dict[str, Any]) -> dict[str, Any]:
    output_summary = provenance_summary.get("output_dq_summary")
    if not isinstance(output_summary, dict):
        return {
            "passed": False,
            "mismatches": {"output_dq_summary": {"actual": None, "expected": dict(dq_summary)}},
        }
    keys = sorted({str(key) for key in dq_summary} | {str(key) for key in output_summary})
    mismatches: dict[str, dict[str, int | None]] = {}
    for key in keys:
        actual = _int_value(output_summary.get(key))
        expected = _int_value(dq_summary.get(key))
        if actual != expected:
            mismatches[key] = {"actual": actual, "expected": expected}
    return {"passed": not mismatches, "mismatches": mismatches}


def _sample_accounting_closure_state(provenance_summary: dict[str, Any]) -> dict[str, Any]:
    closure = provenance_summary.get("sample_accounting_closure")
    if not isinstance(closure, dict):
        return {
            "present": False,
            "status": "missing",
            "passed": True,
            "required": False,
        }
    status = closure.get("status")
    present = status in {"passed", "failed"}
    return {
        "present": present,
        "status": status,
        "passed": (not present) or status == "passed",
        "required": present,
        "input_valid_samples_before_rejection": closure.get(
            "input_valid_samples_before_rejection"
        ),
        "valid_samples_after_rejection": closure.get("valid_samples_after_rejection"),
        "rejected_samples": closure.get("rejected_samples"),
        "valid_rejection_match": closure.get("valid_rejection_match"),
        "input_total_match": closure.get("input_total_match"),
    }


def _resident_artifact_rejection_descriptor(
    run_root: Path,
    output: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    resident_path = run_root / "resident_artifacts.json"
    if not resident_path.exists():
        return {}
    try:
        payload = read_json(resident_path)
    except Exception:
        return {}
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else []
    if not isinstance(artifacts, list):
        return {}
    output_filter = output.get("filter")
    fallback: dict[str, Any] = {}
    for artifact_index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        descriptor = artifact.get("integration_rejection")
        if not isinstance(descriptor, dict):
            continue
        if output_filter is not None and artifact.get("filter") == output_filter:
            return dict(descriptor)
        if artifact_index == index:
            fallback = dict(descriptor)
    return fallback


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _complete_legacy_winsorized_descriptor(
    raw_descriptor: dict[str, Any],
) -> tuple[dict[str, Any], bool, str | None]:
    if raw_descriptor.get("mode") != "winsorized_sigma":
        return dict(raw_descriptor), False, None
    low_sigma = _float_or_default(raw_descriptor.get("low_sigma"), 3.0)
    high_sigma = _float_or_default(raw_descriptor.get("high_sigma"), 3.0)
    algorithm = raw_descriptor.get("algorithm")
    if algorithm == RESIDENT_WINSORIZED_SIGMA_ALGORITHM:
        canonical = resident_rejection_descriptor(
            "winsorized_sigma",
            low_sigma,
            high_sigma,
            resident_winsorized_mode=RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
        )
        return {**canonical, **raw_descriptor}, True, "fast_approx_algorithm"
    if algorithm == RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM:
        canonical = resident_rejection_descriptor(
            "winsorized_sigma",
            low_sigma,
            high_sigma,
            resident_winsorized_mode=RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
        )
        return {**canonical, **raw_descriptor}, True, "hardened_algorithm"
    return dict(raw_descriptor), False, None


def _resident_rejection_semantics_state(
    output: dict[str, Any],
    rejection: str,
    *,
    resident_artifact_descriptor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_descriptor = (
        output.get("integration_rejection")
        if isinstance(output.get("integration_rejection"), dict)
        else {}
    )
    artifact_descriptor = resident_artifact_descriptor or {}
    raw_descriptor = output_descriptor or artifact_descriptor
    descriptor_source = (
        "integration_results.output.integration_rejection"
        if output_descriptor
        else "resident_artifacts.integration_rejection"
        if artifact_descriptor
        else "missing"
    )
    descriptor, legacy_completion, legacy_completion_source = _complete_legacy_winsorized_descriptor(
        raw_descriptor
    )
    required = rejection == "winsorized_sigma"
    expected_options = [
        {
            "mode": "winsorized_sigma",
            "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
            "algorithm": RESIDENT_WINSORIZED_SIGMA_ALGORITHM,
            "scale_estimator": RESIDENT_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
            "cpu_baseline_scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
            "cpu_baseline_parity": False,
            "parity_status": RESIDENT_WINSORIZED_SIGMA_PARITY_STATUS,
            "approximation": True,
        },
        {
            "mode": "winsorized_sigma",
            "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
            "algorithm": RESIDENT_WINSORIZED_SIGMA_HARDENED_ALGORITHM,
            "scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
            "cpu_baseline_scale_estimator": CPU_WINSORIZED_SIGMA_SCALE_ESTIMATOR,
            "cpu_baseline_parity": True,
            "parity_status": RESIDENT_WINSORIZED_SIGMA_HARDENED_PARITY_STATUS,
            "approximation": False,
        },
    ]
    if not required:
        return {
            "required": False,
            "present": bool(raw_descriptor),
            "passed": True,
            "status": "not_required",
            "rejection": rejection,
            "descriptor": descriptor,
            "raw_descriptor": raw_descriptor,
            "descriptor_source": descriptor_source,
            "integration_results_descriptor_present": bool(output_descriptor),
            "resident_artifacts_descriptor_present": bool(artifact_descriptor),
            "legacy_completion_applied": legacy_completion,
            "legacy_completion_source": legacy_completion_source,
            "expected": None,
        }
    mismatch_options = [
        {
            key: {"actual": descriptor.get(key), "expected": expected_value}
            for key, expected_value in expected.items()
            if descriptor.get(key) != expected_value
        }
        for expected in expected_options
    ]
    passed_option_index = next(
        (index for index, mismatches in enumerate(mismatch_options) if not mismatches),
        None,
    )
    matched_expected = (
        expected_options[passed_option_index]
        if passed_option_index is not None
        else expected_options[0]
    )
    present = bool(raw_descriptor)
    mismatches = {} if passed_option_index is not None else mismatch_options[0]
    return {
        "required": True,
        "present": present,
        "passed": present and passed_option_index is not None,
        "status": "passed" if present and passed_option_index is not None else "failed",
        "rejection": rejection,
        "descriptor": descriptor,
        "raw_descriptor": raw_descriptor,
        "descriptor_source": descriptor_source,
        "integration_results_descriptor_present": bool(output_descriptor),
        "resident_artifacts_descriptor_present": bool(artifact_descriptor),
        "legacy_completion_applied": legacy_completion,
        "legacy_completion_source": legacy_completion_source,
        "expected": matched_expected,
        "expected_options": expected_options,
        "matched_expected_index": passed_option_index,
        "mismatches": mismatches,
        "semantics": (
            "Resident CUDA winsorized_sigma must disclose whether it used the default "
            "mean/std approximation or the opt-in hardened median/IQR CPU-parity prototype."
        ),
    }


def _dq_flags(dq_summary: dict[str, Any]) -> list[str]:
    flags = ["valid", "no_data", "warp_edge", "low_rejected", "high_rejected"]
    for key in dq_summary:
        text = str(key).lower()
        if text not in flags:
            flags.append(text)
    return flags


def _pixel_verify(
    output: dict[str, Any],
    *,
    run_root: Path,
    rejection: str,
    tile_size: int,
    tolerance_pixels: int,
) -> dict[str, Any]:
    dq_summary = output.get("dq_summary") if isinstance(output.get("dq_summary"), dict) else {}
    result: dict[str, Any] = {"enabled": True, "tile_size": tile_size, "tolerance_pixels": tolerance_pixels}
    dq_required = _map_required(output, "dq", rejection=rejection)
    dq_path = _resolve_path(output.get("dq_map_path"), run_root)
    if dq_path is None:
        result["dq"] = {
            "ok": not dq_required,
            "status": "missing_path" if dq_required else "skipped_by_output_policy",
            "required": dq_required,
        }
    else:
        dq_pixels = summarize_dq_map_pixels(dq_path, flags=_dq_flags(dq_summary), tile_size=tile_size)
        matches = {}
        for flag, actual in (dq_pixels.get("counts") or {}).items():
            expected = _int_value(dq_summary.get(flag))
            if expected is None and flag in {"no_data", "warp_edge", "low_rejected", "high_rejected"}:
                expected = 0
            delta = None if expected is None else int(actual) - expected
            matches[flag] = {
                "actual": int(actual),
                "summary": expected,
                "delta": delta,
                "passed": delta is not None and abs(delta) <= tolerance_pixels,
            }
        result["dq"] = {"ok": all(match["passed"] for match in matches.values()), "result": dq_pixels, "matches": matches}

    count_maps: dict[str, Any] = {}
    rejection_sample_sum = 0
    rejection_sample_maps_present = False
    for map_name, path_key, flag in [
        ("coverage", "coverage_map_path", "no_data"),
        ("low_rejection", "low_rejection_map_path", "low_rejected"),
        ("high_rejection", "high_rejection_map_path", "high_rejected"),
    ]:
        required = _map_required(output, map_name, rejection=rejection)
        path = _resolve_path(output.get(path_key), run_root)
        if path is None:
            count_maps[map_name] = {"ok": not required, "status": "missing_path", "required": required}
            continue
        pixels = summarize_count_map_pixels(path, tile_size=tile_size)
        value = pixels.get("zero_or_less_pixels") if map_name == "coverage" else pixels.get("positive_pixels")
        expected = _int_value(dq_summary.get(flag))
        if expected is None and flag in {"no_data", "low_rejected", "high_rejected"}:
            expected = 0
        delta = None if expected is None else int(value) - expected
        count_integrity = {
            "passed": True,
            "nonfinite_pixels": pixels.get("nonfinite_pixels"),
            "negative_pixels": pixels.get("negative_pixels"),
            "fractional_pixels": pixels.get("fractional_pixels"),
        }
        if map_name in _REJECTION_MAPS:
            rejection_sample_maps_present = True
            rejection_sample_sum += int(pixels.get("rounded_sum") or 0)
            count_integrity["passed"] = (
                _int_value(pixels.get("nonfinite_pixels")) == 0
                and _int_value(pixels.get("negative_pixels")) == 0
                and _int_value(pixels.get("fractional_pixels")) == 0
            )
        count_maps[map_name] = {
            "ok": delta is not None and abs(delta) <= tolerance_pixels and bool(count_integrity["passed"]),
            "required": required,
            "result": pixels,
            "count_integrity": count_integrity,
            "summary_match": {
                flag: {
                    "actual": int(value),
                    "summary": expected,
                    "delta": delta,
                    "passed": delta is not None and abs(delta) <= tolerance_pixels,
                }
            },
        }
    result["count_maps"] = count_maps
    coverage_provenance = (
        output.get("dq_coverage_provenance") if isinstance(output.get("dq_coverage_provenance"), dict) else {}
    )
    provenance_summary = (
        output.get("dq_provenance_summary") if isinstance(output.get("dq_provenance_summary"), dict) else {}
    )
    coverage_rejected_samples = _int_value(coverage_provenance.get("rejected_sample_count"))
    summary_rejected_samples = _int_value(provenance_summary.get("rejected_samples"))
    map_vs_coverage = _sample_match(rejection_sample_sum, coverage_rejected_samples, tolerance_pixels)
    map_vs_summary = _sample_match(rejection_sample_sum, summary_rejected_samples, tolerance_pixels)
    coverage_vs_summary = _sample_match(coverage_rejected_samples, summary_rejected_samples, tolerance_pixels)
    expected_sample_accounting = rejection != "none" and rejection_sample_maps_present
    rejection_sample_accounting = {
        "ok": (not expected_sample_accounting)
        or (map_vs_coverage["passed"] and map_vs_summary["passed"] and coverage_vs_summary["passed"]),
        "expected": expected_sample_accounting,
        "map_rejected_sample_sum": rejection_sample_sum if rejection_sample_maps_present else None,
        "coverage_provenance_rejected_samples": coverage_rejected_samples,
        "provenance_summary_rejected_samples": summary_rejected_samples,
        "map_vs_coverage": map_vs_coverage,
        "map_vs_summary": map_vs_summary,
        "coverage_vs_summary": coverage_vs_summary,
        "semantics": (
            "Low/high rejection count maps store rejected-sample counts; DQ low/high flags "
            "store pixels touched by rejection."
        ),
    }
    result["rejection_sample_accounting"] = rejection_sample_accounting
    result["ok"] = (
        bool(result.get("dq", {}).get("ok"))
        and all(bool(row.get("ok")) for row in count_maps.values())
        and bool(rejection_sample_accounting["ok"])
    )
    return result


def _resident_output_contract(
    output: dict[str, Any],
    *,
    run_root: Path,
    index: int,
    parent_rejection: str,
    pixel_verify: bool,
    pixel_verify_tile_size: int,
    pixel_tolerance: int,
) -> dict[str, Any]:
    rejection = str(output.get("rejection") or parent_rejection or "none")
    dq_summary = output.get("dq_summary") if isinstance(output.get("dq_summary"), dict) else {}
    coverage_provenance = (
        output.get("dq_coverage_provenance") if isinstance(output.get("dq_coverage_provenance"), dict) else {}
    )
    provenance_summary = (
        output.get("dq_provenance_summary") if isinstance(output.get("dq_provenance_summary"), dict) else {}
    )
    active_frame_count = _int_value(provenance_summary.get("active_frame_count")) or _int_value(
        coverage_provenance.get("active_frame_count")
    )
    frame_count = _int_value(output.get("frame_count"))
    min_required_active_frame_count = 2 if frame_count is not None and frame_count > 1 else 1
    map_rows = _map_rows(output, run_root, rejection=rejection)
    dq_required = _map_required(output, "dq", rejection=rejection)
    coverage_required = _map_required(output, "coverage", rejection=rejection)
    coverage_available = bool(coverage_provenance) and bool(coverage_provenance.get("available", True))
    geometric_output = output.get("geometric_warp_coverage")
    geometric_available = (
        bool(geometric_output.get("available"))
        if isinstance(geometric_output, dict)
        else bool(coverage_provenance.get("geometric_frame_count_matches_active") is not None)
    )
    geometric_required = coverage_required or coverage_available or geometric_available
    if isinstance(geometric_output, dict):
        geometric_frame_count_matches = bool(coverage_provenance.get("geometric_frame_count_matches_active", True)) and bool(
            geometric_output.get("frame_count_matches_active", True)
        )
    else:
        geometric_frame_count_matches = bool(coverage_provenance.get("geometric_frame_count_matches_active", True))
    summary_match = _summary_matches(dq_summary, provenance_summary)
    dq_summary_match_required = dq_required or bool(dq_summary)
    source_terms = {str(item) for item in (provenance_summary.get("source_terms") or [])}
    source_terms_required = coverage_required or coverage_available
    coverage_rejected_samples = _int_value(coverage_provenance.get("rejected_sample_count"))
    summary_rejected_samples = _int_value(provenance_summary.get("rejected_samples"))
    rejection_sample_count_required = rejection != "none" and bool(
        source_terms & {"low_rejection", "high_rejection"}
    )
    rejection_sample_count_match = _sample_match(
        coverage_rejected_samples,
        summary_rejected_samples,
        0,
    )
    sample_closure = _sample_accounting_closure_state(provenance_summary)
    resident_artifact_descriptor = _resident_artifact_rejection_descriptor(
        run_root,
        output,
        index,
    )
    rejection_semantics = _resident_rejection_semantics_state(
        output,
        rejection,
        resident_artifact_descriptor=resident_artifact_descriptor,
    )
    checks = [
        _check(
            "resident_identity",
            output.get("backend") == "cuda_resident_stack" or output.get("memory_mode") == "resident",
            {"backend": output.get("backend"), "memory_mode": output.get("memory_mode")},
        ),
        _check(
            "required_maps_exist",
            all(row["ok"] for row in map_rows),
            {"failed": [row["map"] for row in map_rows if not row["ok"]], "map_count": len(map_rows)},
        ),
        _check(
            "dq_summary_present",
            (not dq_required) or (bool(dq_summary) and "valid" in dq_summary),
            {"keys": sorted(dq_summary.keys()), "required": dq_required},
        ),
        _check(
            "resident_provenance_summary",
            provenance_summary.get("source_schema") == "resident_dq_coverage_provenance"
            and provenance_summary.get("engine") == "cuda_resident_stack"
            and provenance_summary.get("stage") == "integration",
            {
                "source_schema": provenance_summary.get("source_schema"),
                "engine": provenance_summary.get("engine"),
                "stage": provenance_summary.get("stage"),
            },
        ),
        _check(
            "dq_summary_matches_provenance",
            (not dq_summary_match_required) or summary_match["passed"],
            {
                "mismatches": summary_match["mismatches"],
                "dq_summary": dq_summary,
                "provenance_output_dq_summary": provenance_summary.get("output_dq_summary"),
                "required": dq_summary_match_required,
            },
        ),
        _check(
            "active_frame_count_valid",
            active_frame_count is not None and active_frame_count > 0 and (frame_count is None or active_frame_count <= frame_count),
            {"active_frame_count": active_frame_count, "frame_count": frame_count},
        ),
        _check(
            "active_frame_count_not_degenerate",
            active_frame_count is not None and active_frame_count >= min_required_active_frame_count,
            {
                "active_frame_count": active_frame_count,
                "frame_count": frame_count,
                "min_required_active_frame_count": min_required_active_frame_count,
                "reason": (
                    "multi-frame resident integrations must not silently collapse to a single "
                    "active frame; use a one-frame input if a single-frame diagnostic output is intended"
                ),
            },
        ),
        _check(
            "coverage_provenance_present",
            (not coverage_required) or coverage_available,
            {"keys": sorted(coverage_provenance.keys()), "coverage_required": coverage_required},
        ),
        _check(
            "source_terms_present",
            (not source_terms_required)
            or (
                "post_rejection_coverage" in source_terms
                and "geometric_warp_coverage" in source_terms
            ),
            {"source_terms": sorted(source_terms), "required": source_terms_required},
        ),
        _check(
            "geometric_frame_count_matches_active",
            (not geometric_required) or geometric_frame_count_matches,
            {
                "coverage_provenance": coverage_provenance.get("geometric_frame_count_matches_active"),
                "output": (geometric_output or {}).get("frame_count_matches_active")
                if isinstance(geometric_output, dict)
                else None,
                "required": geometric_required,
            },
        ),
        _check(
            "rejection_sample_count_recorded",
            (not rejection_sample_count_required)
            or (coverage_rejected_samples is not None and summary_rejected_samples is not None),
            {
                "required": rejection_sample_count_required,
                "rejection": rejection,
                "source_terms": sorted(source_terms),
                "coverage_provenance_rejected_samples": coverage_rejected_samples,
                "provenance_summary_rejected_samples": summary_rejected_samples,
            },
            "Resident rejection provenance records rejected samples separately from DQ pixels.",
        ),
        _check(
            "rejection_sample_count_summary_matches_coverage",
            (not rejection_sample_count_required) or bool(rejection_sample_count_match["passed"]),
            rejection_sample_count_match,
        ),
        _check(
            "resident_winsorized_rejection_semantics_disclosed",
            bool(rejection_semantics["passed"]),
            rejection_semantics,
            "Resident winsorized rejection must disclose approximation and CPU-baseline parity status.",
        ),
        _check(
            "sample_accounting_closure_valid",
            bool(sample_closure["passed"]),
            sample_closure,
            "Optional resident sample closure verifies pre-rejection valid samples against post-rejection valid plus rejected samples.",
        ),
    ]
    pixel_result = None
    if pixel_verify:
        pixel_result = _pixel_verify(
            output,
            run_root=run_root,
            rejection=rejection,
            tile_size=max(1, int(pixel_verify_tile_size)),
            tolerance_pixels=max(0, int(pixel_tolerance)),
        )
        checks.append(
            _check(
                "pixel_maps_match_summaries",
                bool(pixel_result.get("ok")),
                {
                    "dq_ok": bool(pixel_result.get("dq", {}).get("ok")),
                    "count_maps": {
                        key: value.get("ok")
                        for key, value in (pixel_result.get("count_maps") or {}).items()
                    },
                },
            )
        )
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "contract_type": "resident_cuda_result_contract",
        "index": index,
        "filter": output.get("filter"),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "backend": output.get("backend"),
        "memory_mode": output.get("memory_mode"),
        "rejection": rejection,
        "rejection_semantics": rejection_semantics,
        "active_frame_count": active_frame_count,
        "frame_count": frame_count,
        "sample_accounting_closure": sample_closure,
        "maps": map_rows,
        "checks": checks,
        "pixel_verification": pixel_result or {
            "enabled": False,
            "tile_size": max(1, int(pixel_verify_tile_size)),
            "tolerance_pixels": max(0, int(pixel_tolerance)),
        },
    }


def build_resident_output_contract(
    output: dict[str, Any],
    *,
    run_root: str | Path,
    index: int = 0,
    parent_rejection: str = "none",
    pixel_verify: bool = False,
    pixel_verify_tile_size: int = 2048,
    pixel_tolerance: int = 0,
) -> dict[str, Any]:
    return _resident_output_contract(
        output,
        run_root=Path(run_root),
        index=index,
        parent_rejection=parent_rejection,
        pixel_verify=pixel_verify,
        pixel_verify_tile_size=pixel_verify_tile_size,
        pixel_tolerance=pixel_tolerance,
    )


def build_resident_result_contract(
    run_dir: str | Path,
    *,
    pixel_verify: bool = False,
    pixel_verify_tile_size: int = 2048,
    pixel_tolerance: int = 0,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    integration_path = run_root / "integration_results.json"
    integration = _load_json_object(integration_path)
    outputs = [row for row in integration.get("outputs", []) if isinstance(row, dict)]
    resident_outputs = [
        (index, row)
        for index, row in enumerate(outputs)
        if row.get("backend") == "cuda_resident_stack" or row.get("memory_mode") == "resident"
    ]
    parent_rejection = str(integration.get("rejection") or "none")
    contracts = [
        _resident_output_contract(
            output,
            run_root=run_root,
            index=index,
            parent_rejection=parent_rejection,
            pixel_verify=pixel_verify,
            pixel_verify_tile_size=pixel_verify_tile_size,
            pixel_tolerance=pixel_tolerance,
        )
        for index, output in resident_outputs
    ]
    checks = [
        _check("integration_artifact_exists", integration_path.exists(), {"path": str(integration_path)}),
        _check(
            "resident_outputs_present",
            bool(contracts),
            {"output_count": len(outputs), "resident_output_count": len(contracts)},
        ),
        _check(
            "resident_outputs_pass_contract",
            bool(contracts) and all(contract["passed"] for contract in contracts),
            {"failed": [contract["index"] for contract in contracts if not contract["passed"]]},
        ),
    ]
    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "artifact_type": "resident_cuda_result_contract",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "integration_path": str(integration_path),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "pixel_verify": bool(pixel_verify),
        "checks": checks,
        "outputs": contracts,
    }


def write_resident_result_contract_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GLASS Resident CUDA Result Contract",
        "",
        f"- Status: {payload['status']}",
        f"- Run: `{payload['run_dir']}`",
        f"- Pixel verify: `{payload['pixel_verify']}`",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.extend(["", "## Outputs", ""])
    for output in payload.get("outputs") or []:
        lines.append(
            f"- `{output.get('filter')}` index `{output.get('index')}`: "
            f"{output.get('status')} ({len(output.get('checks') or [])} checks)"
        )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_result_contract(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is not None:
        write_resident_result_contract_markdown(markdown, payload)
