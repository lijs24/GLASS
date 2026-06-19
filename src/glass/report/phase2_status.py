from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_CHECKPOINT_RE = re.compile(r"s2_gate_(\d+)_status\.md$")
_DEFAULT_ROUTE_CHECKS = {
    "memory_mode": "contract_required_command_token:--memory-mode resident",
    "backend": "contract_required_command_token:--backend cuda",
    "resident_registration": (
        "contract_required_command_token:--resident-registration similarity_cuda_triangle"
    ),
    "runtime_preset": "contract_required_command_token_group:resident_h2d_or_runtime_preset",
}

_QUALITY_METRIC_FIELDS = [
    ("star_count", "low"),
    ("fwhm_px", "high"),
    ("eccentricity", "high"),
    ("background_rms", "high"),
    ("snr", "low"),
    ("quality_score", "low"),
    ("weight", "low"),
]


def _read_json_optional(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    if not target.exists():
        return {"path": str(target), "exists": False}
    payload = read_json(target)
    if not isinstance(payload, dict):
        return {"path": str(target), "exists": True, "valid_json_object": False}
    payload = dict(payload)
    payload["_path"] = str(target)
    payload["_exists"] = True
    return payload


def _field_from_status(text: str, key: str) -> str | None:
    prefix = f"- {key}:"
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def _latest_checkpoint(checkpoint_dir: str | Path) -> dict[str, Any]:
    root = Path(checkpoint_dir)
    candidates: list[tuple[int, Path]] = []
    if root.exists():
        for path in root.glob("s2_gate_*_status.md"):
            match = _CHECKPOINT_RE.match(path.name)
            if match:
                candidates.append((int(match.group(1)), path))
    if not candidates:
        return {"exists": False, "checkpoint_dir": str(root), "gate": None, "status": "missing"}
    gate, path = max(candidates, key=lambda item: item[0])
    text = path.read_text(encoding="utf-8")
    status = _field_from_status(text, "Status")
    scope = _field_from_status(text, "Scope")
    date = _field_from_status(text, "Date")
    return {
        "exists": True,
        "checkpoint_dir": str(root),
        "gate": gate,
        "path": str(path),
        "status": status,
        "scope": scope,
        "date": date,
        "green": str(status).lower() == "green",
    }


def _acceptance_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
        }
    speedup = payload.get("speedup_summary") if isinstance(payload.get("speedup_summary"), dict) else {}
    comparison = speedup.get("comparison") if isinstance(speedup.get("comparison"), dict) else {}
    bundle_schema = (
        payload.get("contract_bundle_schema")
        if isinstance(payload.get("contract_bundle_schema"), dict)
        else {}
    )
    resident_contracts = (
        payload.get("resident_contracts") if isinstance(payload.get("resident_contracts"), dict) else {}
    )
    native_guardrails_bundle = _native_guardrails_summary(payload)
    registration_fastpath = _resident_registration_fastpath_summary(payload)
    integration_engine_policy = _acceptance_integration_engine_policy_summary(payload)
    runtime_default = _acceptance_stack_engine_runtime_default_summary(payload)
    warp_quality_contract = (
        payload.get("warp_quality_contract")
        if isinstance(payload.get("warp_quality_contract"), dict)
        else {}
    )
    benchmark_contract = (
        payload.get("benchmark_contract")
        if isinstance(payload.get("benchmark_contract"), dict)
        else {}
    )
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "benchmark_contract": benchmark_contract,
        "benchmark_contract_source": benchmark_contract.get("source"),
        "benchmark_contract_path": benchmark_contract.get("path"),
        "benchmark_contract_profile": benchmark_contract.get("profile"),
        "benchmark_contract_name": benchmark_contract.get("name"),
        "benchmark_contract_schema_version": benchmark_contract.get("schema_version"),
        "frame_type_counts": payload.get("frame_type_counts"),
        "speedup_vs_reference": speedup.get("speedup_vs_wbpp"),
        "active_frames": speedup.get("glass", {}).get("weighted_frame_count")
        if isinstance(speedup.get("glass"), dict)
        else None,
        "rms_diff": comparison.get("rms_diff"),
        "abs_diff_p99": comparison.get("abs_diff_p99"),
        "coverage_fraction": comparison.get("coverage_fraction"),
        "contract_bundle_schema_status": bundle_schema.get("status"),
        "native_guardrails_bundle": native_guardrails_bundle,
        "native_guardrails_bundle_status": native_guardrails_bundle.get("status")
        if native_guardrails_bundle
        else None,
        "resident_result_contract_source": native_guardrails_bundle.get("resident_result_contract_source")
        if native_guardrails_bundle
        else None,
        "resident_result_contract_run_default": native_guardrails_bundle.get(
            "resident_result_contract_run_default"
        )
        if native_guardrails_bundle
        else None,
        "resident_result_contract_json": native_guardrails_bundle.get("resident_result_contract_json")
        if native_guardrails_bundle
        else None,
        "resident_native_calibration_artifact": native_guardrails_bundle.get(
            "resident_native_calibration_artifact"
        )
        if native_guardrails_bundle
        else None,
        "resident_calibration_master_count": native_guardrails_bundle.get(
            "resident_calibration_master_count"
        )
        if native_guardrails_bundle
        else None,
        "resident_calibrated_light_count": native_guardrails_bundle.get(
            "resident_calibrated_light_count"
        )
        if native_guardrails_bundle
        else None,
        "resident_registration_fastpath": registration_fastpath,
        "resident_registration_fastpath_status": registration_fastpath.get("status")
        if registration_fastpath
        else None,
        "resident_registration_fastpath_contract_status": registration_fastpath.get("contract_status")
        if registration_fastpath
        else None,
        "resident_registration_fastpath_mode": registration_fastpath.get("mode")
        if registration_fastpath
        else None,
        "triangle_descriptor_fit_batch": registration_fastpath.get("triangle_descriptor_fit_batch")
        if registration_fastpath
        else None,
        "triangle_descriptor_fit_batch_mode": registration_fastpath.get(
            "triangle_descriptor_fit_batch_mode"
        )
        if registration_fastpath
        else None,
        "triangle_descriptor_fit_device_reuse": registration_fastpath.get(
            "triangle_descriptor_fit_device_reuse"
        )
        if registration_fastpath
        else None,
        "triangle_pixel_refine_batch": registration_fastpath.get("triangle_pixel_refine_batch")
        if registration_fastpath
        else None,
        "triangle_pixel_refine_batch_metric_mode": registration_fastpath.get(
            "triangle_pixel_refine_batch_metric_mode"
        )
        if registration_fastpath
        else None,
        "triangle_warp_batch": registration_fastpath.get("triangle_warp_batch")
        if registration_fastpath
        else None,
        "triangle_warp_batch_mode": registration_fastpath.get("triangle_warp_batch_mode")
        if registration_fastpath
        else None,
        "triangle_warp_batch_frame_count": registration_fastpath.get(
            "triangle_warp_batch_frame_count"
        )
        if registration_fastpath
        else None,
        "resident_warp_copy_mode": registration_fastpath.get("resident_warp_copy_mode")
        if registration_fastpath
        else None,
        "resident_warp_scratch_bytes": registration_fastpath.get("resident_warp_scratch_bytes")
        if registration_fastpath
        else None,
        "resident_registration_fastpath_contract_check_count": registration_fastpath.get(
            "contract_check_count"
        )
        if registration_fastpath
        else None,
        "resident_registration_fastpath_contract_failed_check_count": registration_fastpath.get(
            "contract_failed_check_count"
        )
        if registration_fastpath
        else None,
        "pipeline_integration_engine_policy": integration_engine_policy,
        "pipeline_integration_engine_policy_status": integration_engine_policy.get("status"),
        "pipeline_integration_engine_policy_check_present": integration_engine_policy.get(
            "check_present"
        ),
        "pipeline_integration_engine_policy_check_passed": integration_engine_policy.get(
            "check_passed"
        ),
        "pipeline_integration_engine_policy_non_resident_count": integration_engine_policy.get(
            "non_resident_count"
        ),
        "pipeline_integration_engine_policy_failed_count": integration_engine_policy.get(
            "failed_count"
        ),
        "pipeline_stack_engine_runtime_default": runtime_default,
        "pipeline_stack_engine_runtime_default_status": runtime_default.get("status"),
        "pipeline_stack_engine_runtime_default_check_present": runtime_default.get(
            "check_present"
        ),
        "pipeline_stack_engine_runtime_default_check_passed": runtime_default.get(
            "check_passed"
        ),
        "pipeline_stack_engine_runtime_default_master_count": runtime_default.get(
            "master_count"
        ),
        "pipeline_stack_engine_runtime_default_legacy_master_count": (
            runtime_default.get("legacy_master_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_master_count": (
            runtime_default.get("failed_master_count")
        ),
        "pipeline_stack_engine_runtime_default_failed_output_count": (
            runtime_default.get("failed_output_count")
        ),
        "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            runtime_default.get("explicit_cuda_fast_path_count")
        ),
        "resident_calibration_contract_passed": (resident_contracts.get("calibration") or {}).get("passed")
        if isinstance(resident_contracts.get("calibration"), dict)
        else None,
        "resident_result_contract_passed": (resident_contracts.get("result") or {}).get("passed")
        if isinstance(resident_contracts.get("result"), dict)
        else None,
        "warp_quality_contract": warp_quality_contract or None,
        "warp_quality_contract_status": warp_quality_contract.get("status"),
        "warp_quality_contract_passed": warp_quality_contract.get("passed"),
        "warp_quality_contract_output_count": warp_quality_contract.get("output_count"),
        "warp_quality_contract_check_count": warp_quality_contract.get("check_count"),
        "warp_quality_contract_failed_checks": warp_quality_contract.get("failed_checks")
        or [],
        "warp_quality_contract_path": warp_quality_contract.get("path"),
    }


def _registration_admission_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "blocked": False,
        }
    admission = payload.get("reference_admission")
    results = payload.get("registration_results") if isinstance(payload.get("registration_results"), list) else []
    if not isinstance(admission, dict):
        return {
            "path": payload.get("_path"),
            "exists": True,
            "status": "not_available",
            "passed": False,
            "blocked": False,
            "reason": "reference_admission missing",
            "registration_row_count": len(results),
        }
    status = str(admission.get("status") or "unknown")
    blocked = status == "blocked"
    passed = status in {"accepted", "allowed_quality_rejected_reference"}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": status,
        "passed": passed,
        "blocked": blocked,
        "reference_frame_id": admission.get("reference_frame_id"),
        "quality_gate_status": admission.get("quality_gate_status"),
        "quality_gate_enforced": admission.get("quality_gate_enforced"),
        "reference_selection_fallback": admission.get("reference_selection_fallback"),
        "allow_quality_rejected_reference": admission.get("allow_quality_rejected_reference"),
        "reason": admission.get("reason"),
        "quality_reference_frame_id": payload.get("quality_reference_frame_id"),
        "requested_reference_frame_id": payload.get("requested_reference_frame_id"),
        "registration_row_count": len(results),
        "quality_reference_admission_row_count": sum(
            1
            for item in results
            if isinstance(item, dict)
            and item.get("registration_solution_source") == "quality_reference_admission"
        ),
        "quality_rejected_row_count": sum(
            1
            for item in results
            if isinstance(item, dict) and item.get("quality_gate_status") == "rejected"
        ),
    }


def _quality_saturation_warning_text(item: dict[str, Any]) -> str:
    warnings = item.get("quality_gate_warnings")
    if warnings is None:
        warning_values: list[Any] = []
    elif isinstance(warnings, list):
        warning_values = warnings
    else:
        warning_values = [warnings]
    saturation_warnings = [
        str(warning) for warning in warning_values if "saturation" in str(warning).lower()
    ]
    return "; ".join(saturation_warnings)


def _quality_saturation_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "reason": "quality artifact missing",
        }
    frame_quality = payload.get("frame_quality")
    if not isinstance(frame_quality, list):
        return {
            "path": payload.get("_path"),
            "exists": True,
            "status": "invalid",
            "passed": False,
            "reason": "frame_quality list missing",
        }
    policy = payload.get("quality_gate_policy")
    if not isinstance(policy, dict):
        summary = payload.get("quality_gate_summary")
        policy = summary.get("policy") if isinstance(summary, dict) else {}
    if not isinstance(policy, dict):
        policy = {}
    fractions = [
        _float_or_none(item.get("saturation_fraction")) or 0.0
        for item in frame_quality
        if isinstance(item, dict)
    ]
    counts = [
        _float_or_none(item.get("saturated_pixel_count")) or 0.0
        for item in frame_quality
        if isinstance(item, dict)
    ]
    dict_rows = [item for item in frame_quality if isinstance(item, dict)]
    saturated_rows = [
        item
        for item in dict_rows
        if (_float_or_none(item.get("saturation_fraction")) or 0.0) > 0.0
        or (_float_or_none(item.get("saturated_pixel_count")) or 0.0) > 0.0
    ]
    rejected_rows = [
        item
        for item in dict_rows
        if str(item.get("quality_gate_status", "")).lower() == "rejected"
        and _quality_saturation_warning_text(item)
    ]
    sources = sorted({str(item.get("saturation_source")) for item in dict_rows if item.get("saturation_source")})
    row_levels = sorted(
        {
            str(item.get("saturation_level"))
            for item in dict_rows
            if item.get("saturation_level") is not None
        }
    )
    policy_level = policy.get("saturation_level", policy.get("quality_saturation_level"))
    saturation_level: Any
    if policy_level is not None:
        saturation_level = policy_level
    elif len(row_levels) == 1:
        saturation_level = row_levels[0]
    else:
        saturation_level = ", ".join(row_levels)
    worst_row: dict[str, Any] = {}
    if dict_rows:
        worst_row = max(
            dict_rows,
            key=lambda item: (
                _float_or_none(item.get("saturation_fraction")) or 0.0,
                _float_or_none(item.get("saturated_pixel_count")) or 0.0,
            ),
        )
    rejected_frame_ids = [str(item.get("frame_id")) for item in rejected_rows if item.get("frame_id")]
    passed = len(rejected_rows) == 0
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": "passed" if passed else "attention_required",
        "passed": passed,
        "reason": None if passed else "saturation quality-gate rejection present",
        "frame_count": len(dict_rows),
        "saturated_frame_count": len(saturated_rows),
        "quality_gate_saturation_rejected_count": len(rejected_rows),
        "max_saturation_fraction": round(max(fractions or [0.0]), 8),
        "mean_saturation_fraction": round(sum(fractions) / len(fractions), 8) if fractions else 0.0,
        "max_saturated_pixel_count": int(max(counts or [0.0])),
        "saturation_level": saturation_level,
        "max_saturation_fraction_policy": policy.get("max_saturation_fraction"),
        "saturation_sources": sources,
        "worst_frame_id": worst_row.get("frame_id"),
        "rejected_frame_ids": rejected_frame_ids,
    }


def _median_sorted(values: list[float]) -> float | None:
    if not values:
        return None
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _quality_metric_pairs(
    frame_quality: list[Any],
    metric: str,
) -> list[tuple[dict[str, Any], float]]:
    pairs: list[tuple[dict[str, Any], float]] = []
    for item in frame_quality:
        if not isinstance(item, dict):
            continue
        value = _float_or_none(item.get(metric))
        if value is None:
            continue
        pairs.append((item, value))
    return pairs


def _quality_metric_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "reason": "quality artifact missing",
        }
    frame_quality = payload.get("frame_quality")
    if not isinstance(frame_quality, list):
        return {
            "path": payload.get("_path"),
            "exists": True,
            "status": "invalid",
            "passed": False,
            "reason": "frame_quality list missing",
        }
    dict_rows = [item for item in frame_quality if isinstance(item, dict)]
    summaries: list[dict[str, Any]] = []
    for metric, bad_direction in _QUALITY_METRIC_FIELDS:
        pairs = _quality_metric_pairs(dict_rows, metric)
        if not pairs:
            continue
        values = sorted(value for _, value in pairs)
        worst_item, worst_value = (
            min(pairs, key=lambda pair: pair[1])
            if bad_direction == "low"
            else max(pairs, key=lambda pair: pair[1])
        )
        summaries.append(
            {
                "metric": metric,
                "bad_direction": bad_direction,
                "valid_frames": len(values),
                "min": _round_metric(values[0]),
                "median": _round_metric(_median_sorted(values)),
                "mean": _round_metric(sum(values) / len(values)),
                "max": _round_metric(values[-1]),
                "worst_frame_id": worst_item.get("frame_id"),
                "worst_value": _round_metric(worst_value),
            }
        )
    passed = bool(summaries)
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": "passed" if passed else "not_available",
        "passed": passed,
        "reason": None if passed else "no configured quality metric values present",
        "frame_count": len(dict_rows),
        "metric_count": len(summaries),
        "metrics": [item["metric"] for item in summaries],
        "summary_rows": summaries,
    }


def _quality_metrics_compare_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "reason": "quality metrics compare artifact missing",
        }
    if payload.get("artifact_type") != "quality_metrics_compare":
        return {
            "path": payload.get("_path"),
            "exists": True,
            "status": "invalid",
            "passed": False,
            "reason": "artifact_type is not quality_metrics_compare",
        }
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed_checks = [
        str(item.get("name"))
        for item in checks
        if isinstance(item, dict) and item.get("passed") is not True
    ]
    metric_rows = payload.get("metric_rows") if isinstance(payload.get("metric_rows"), list) else []
    baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    threshold_failures: list[dict[str, Any]] = []
    for item in checks:
        if not isinstance(item, dict) or item.get("passed") is True:
            continue
        if item.get("name") not in {"bad_median_ratio_within_limit", "bad_mean_ratio_within_limit"}:
            continue
        evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
        for failure in evidence.get("failing_metrics") or []:
            if isinstance(failure, dict):
                threshold_failures.append(dict(failure))
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True,
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "metric_row_count": len(metric_rows),
        "baseline_metric_count": baseline.get("metric_count"),
        "candidate_metric_count": candidate.get("metric_count"),
        "baseline_frame_count": baseline.get("frame_count"),
        "candidate_frame_count": candidate.get("frame_count"),
        "threshold_failure_count": len(threshold_failures),
        "threshold_failures": threshold_failures,
    }


def _resident_registration_fastpath_summary(payload: dict[str, Any]) -> dict[str, Any] | None:
    fastpath = (
        payload.get("resident_registration_fastpath")
        if isinstance(payload.get("resident_registration_fastpath"), dict)
        else None
    )
    if fastpath is None:
        return None
    registration = (
        fastpath.get("resident_registration")
        if isinstance(fastpath.get("resident_registration"), dict)
        else {}
    )
    artifact = fastpath.get("artifact") if isinstance(fastpath.get("artifact"), dict) else {}
    io_pipeline = (
        fastpath.get("resident_io_pipeline")
        if isinstance(fastpath.get("resident_io_pipeline"), dict)
        else {}
    )
    contract_checks = [
        item
        for item in payload.get("checks") or []
        if isinstance(item, dict)
        and str(item.get("name") or "").startswith("contract_resident_registration_fastpath")
    ]
    failed_checks = [str(item.get("name")) for item in contract_checks if not item.get("passed")]
    device_reuse = {
        "reference": registration.get("triangle_descriptor_fit_reference_device_reuse"),
        "moving": registration.get("triangle_descriptor_fit_moving_device_reuse"),
        "output": registration.get("triangle_descriptor_fit_output_device_reuse"),
    }
    contract_status = "not_requested"
    if contract_checks:
        contract_status = "passed" if not failed_checks else "failed"
    return {
        "schema_version": 1,
        "status": "present" if fastpath.get("exists") and fastpath.get("available") else "missing",
        "path": fastpath.get("path"),
        "exists": fastpath.get("exists"),
        "available": fastpath.get("available"),
        "artifact_count": fastpath.get("artifact_count"),
        "contract_status": contract_status,
        "contract_check_count": len(contract_checks),
        "contract_failed_check_count": len(failed_checks),
        "contract_failed_checks": failed_checks,
        "mode": registration.get("mode"),
        "triangle_descriptor_fit_batch": registration.get("triangle_descriptor_fit_batch"),
        "triangle_descriptor_fit_batch_mode": registration.get("triangle_descriptor_fit_batch_mode"),
        "triangle_descriptor_fit_device_reuse": device_reuse,
        "triangle_pixel_refine_batch": registration.get("triangle_pixel_refine_batch"),
        "triangle_pixel_refine_batch_mode": registration.get("triangle_pixel_refine_batch_mode"),
        "triangle_pixel_refine_batch_metric_mode": registration.get(
            "triangle_pixel_refine_batch_metric_mode"
        ),
        "triangle_warp_batch": registration.get("triangle_warp_batch"),
        "triangle_warp_batch_mode": registration.get("triangle_warp_batch_mode"),
        "triangle_warp_batch_frame_count": registration.get("triangle_warp_batch_frame_count"),
        "resident_warp_copy_mode": artifact.get("resident_warp_copy_mode"),
        "resident_io_pipeline_warp_copy_mode": io_pipeline.get("warp_copy_mode"),
        "resident_warp_scratch_bytes": artifact.get("resident_warp_scratch_bytes"),
        "resident_io_pipeline_warp_scratch_bytes": io_pipeline.get("warp_scratch_bytes"),
    }


def _check_by_name(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def _default_route_acceptance_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "route_contract_passed": False,
        }
    speedup = payload.get("speedup_summary") if isinstance(payload.get("speedup_summary"), dict) else {}
    comparison = speedup.get("comparison") if isinstance(speedup.get("comparison"), dict) else {}
    route_checks: dict[str, dict[str, Any]] = {}
    for key, check_name in _DEFAULT_ROUTE_CHECKS.items():
        check = _check_by_name(payload, check_name)
        route_checks[key] = {
            "name": check_name,
            "present": check is not None,
            "passed": check.get("passed") is True if isinstance(check, dict) else False,
            "evidence": check.get("evidence") if isinstance(check, dict) else None,
        }
    route_contract_passed = all(item["passed"] for item in route_checks.values())
    benchmark_contract = (
        payload.get("benchmark_contract")
        if isinstance(payload.get("benchmark_contract"), dict)
        else {}
    )
    return {
        "schema_version": 1,
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True and route_contract_passed,
        "acceptance_passed": payload.get("passed"),
        "benchmark_contract": benchmark_contract,
        "benchmark_contract_source": benchmark_contract.get("source"),
        "benchmark_contract_path": benchmark_contract.get("path"),
        "benchmark_contract_profile": benchmark_contract.get("profile"),
        "benchmark_contract_name": benchmark_contract.get("name"),
        "benchmark_contract_schema_version": benchmark_contract.get("schema_version"),
        "speedup_vs_reference": speedup.get("speedup_vs_wbpp"),
        "active_frames": speedup.get("glass", {}).get("weighted_frame_count")
        if isinstance(speedup.get("glass"), dict)
        else None,
        "rms_diff": comparison.get("rms_diff"),
        "abs_diff_p99": comparison.get("abs_diff_p99"),
        "coverage_fraction": comparison.get("coverage_fraction"),
        "route_contract_passed": route_contract_passed,
        "route_checks": route_checks,
        "route_check_count": len(route_checks),
        "route_failed_checks": [
            item["name"] for item in route_checks.values() if item["passed"] is not True
        ],
    }


def _resident_winsorized_benchmark_audit_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "failed_checks": ["artifact_missing"],
            "check_count": 0,
            "failed_check_count": 1,
        }
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed_checks = payload.get("failed_checks") if isinstance(payload.get("failed_checks"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "schema_version": 1,
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True,
        "contract_name": payload.get("contract_name"),
        "contract_path": payload.get("contract_path"),
        "benchmark_path": payload.get("benchmark_path"),
        "failed_checks": [str(item) for item in failed_checks],
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "frame_count": summary.get("frame_count"),
        "shape": summary.get("shape"),
        "hardened_master_rms": summary.get("hardened_master_rms"),
        "hardened_master_max_abs": summary.get("hardened_master_max_abs"),
        "fast_approx_master_rms": summary.get("fast_approx_master_rms"),
        "cuda_hardened_s": summary.get("cuda_hardened_s"),
        "cuda_fast_approx_s": summary.get("cuda_fast_approx_s"),
        "cpu_baseline_s": summary.get("cpu_baseline_s"),
    }


def _resident_winsorized_sweep_audit_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "failed_checks": ["artifact_missing"],
            "check_count": 0,
            "failed_check_count": 1,
        }
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed_checks = payload.get("failed_checks") if isinstance(payload.get("failed_checks"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    required_master = (
        summary.get("required_frame_master")
        if isinstance(summary.get("required_frame_master"), dict)
        else {}
    )
    required_timing = (
        summary.get("required_frame_timing_s")
        if isinstance(summary.get("required_frame_timing_s"), dict)
        else {}
    )
    return {
        "schema_version": 1,
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed") is True,
        "contract_name": payload.get("contract_name"),
        "contract_path": payload.get("contract_path"),
        "sweep_path": payload.get("sweep_path"),
        "failed_checks": [str(item) for item in failed_checks],
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "frame_counts": summary.get("frame_counts"),
        "run_count": summary.get("run_count"),
        "required_frame_count": summary.get("required_frame_count"),
        "required_frame_count_passed": summary.get("required_frame_count_passed"),
        "required_frame_master_rms": required_master.get("rms"),
        "required_frame_master_max_abs": required_master.get("max_abs"),
        "max_hardened_master_rms": summary.get("max_hardened_master_rms"),
        "required_frame_cpu_baseline_s": required_timing.get("cpu_baseline"),
        "required_frame_cuda_fast_approx_s": required_timing.get("cuda_fast_approx"),
        "required_frame_cuda_hardened_s": required_timing.get("cuda_hardened"),
    }


def _native_guardrails_summary(payload: dict[str, Any]) -> dict[str, Any] | None:
    native_guardrails_bundle = (
        payload.get("native_guardrails_bundle")
        if isinstance(payload.get("native_guardrails_bundle"), dict)
        else None
    )
    if native_guardrails_bundle is not None:
        return dict(native_guardrails_bundle)

    contract_bundle = (
        payload.get("contract_bundle") if isinstance(payload.get("contract_bundle"), dict) else None
    )
    if contract_bundle is None:
        return None
    resident_native_calibration = (
        contract_bundle.get("resident_native_calibration")
        if isinstance(contract_bundle.get("resident_native_calibration"), dict)
        else {}
    )
    resident_result_source = contract_bundle.get("resident_result_contract_source")
    return {
        "schema_version": 1,
        "status": "present" if contract_bundle.get("exists") else "missing",
        "bundle_path": contract_bundle.get("path"),
        "bundle_status": contract_bundle.get("status"),
        "guardrails_summary_json": contract_bundle.get("guardrails_summary_json"),
        "resident_result_contract_json": contract_bundle.get("resident_result_contract_json"),
        "resident_result_contract_attached": bool(
            contract_bundle.get("resident_result_contract_attached")
        )
        or contract_bundle.get("resident_result_contract_json") is not None,
        "resident_result_contract_source": resident_result_source,
        "resident_result_contract_run_default": resident_result_source == "run_default",
        "resident_calibration_contract_json": contract_bundle.get("resident_calibration_contract_json"),
        "resident_calibration_contract_attached": bool(
            contract_bundle.get("resident_calibration_contract_attached")
        )
        or contract_bundle.get("resident_calibration_contract_json") is not None,
        "resident_native_calibration_artifact": bool(
            resident_native_calibration.get("artifact_present")
        ),
        "resident_calibration_master_count": resident_native_calibration.get("master_count"),
        "resident_calibrated_light_count": resident_native_calibration.get(
            "resident_calibrated_light_count"
        ),
    }


def _doctor_summary(doctor_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if doctor_payload is None:
        return None
    cuda = doctor_payload.get("cuda") if isinstance(doctor_payload.get("cuda"), dict) else {}
    devices = cuda.get("devices") if isinstance(cuda.get("devices"), list) else []
    first_device = devices[0] if devices and isinstance(devices[0], dict) else {}
    return {
        "recommendation": doctor_payload.get("recommendation"),
        "cuda_available": cuda.get("cuda_available"),
        "native_extension_loaded": cuda.get("native_extension_loaded"),
        "wrapper_importable": cuda.get("wrapper_importable"),
        "device_count": len(devices),
        "primary_gpu": first_device.get("name"),
        "compute_capability": first_device.get("compute_capability", first_device.get("major_minor")),
        "vram_mib": first_device.get("memory_total_mib", first_device.get("total_global_mem_mib")),
        "driver_version": first_device.get("driver_version"),
        "windows_cuda_packages": doctor_payload.get("windows_cuda_packages"),
    }


def _release_manifest_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}
    packages = payload.get("packages") if isinstance(payload.get("packages"), list) else []
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "package_count": payload.get("package_count", len(packages)),
        "source_stamp": payload.get("source_stamp"),
    }


def _github_release_plan_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "publication_ready": False}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    script = payload.get("script") if isinstance(payload.get("script"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "status": payload.get("status"),
        "tag": payload.get("tag"),
        "package_count": payload.get("package_count"),
        "publication_ready": payload.get("publication_ready"),
        "recommendation": payload.get("recommendation"),
        "gh_available": gh.get("available"),
        "gh_auth_ok": gh.get("auth_ok"),
        "script_path": script.get("path"),
        "script_publish_default": script.get("publish_default"),
    }


def _publish_preflight_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
        }
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    matrix_runtime_default = _publish_preflight_runtime_default_layer(
        payload,
        "windows_release_matrix",
        "matrix",
    )
    default_runtime_default = _publish_preflight_runtime_default_layer(
        payload,
        "default_promotion_manifest",
        "default_promotion",
    )
    return {
        "path": payload.get("_path"),
        "exists": True,
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "release_tag": summary.get("release_tag"),
        "asset_count": summary.get("asset_count"),
        "package_count": summary.get("package_count"),
        "primary_package": summary.get("primary_package"),
        "ordered_try_list": summary.get("ordered_try_list"),
        "source_stamps": summary.get("source_stamps"),
        "default_promotion_status": summary.get("default_promotion_status"),
        "default_route_check_count": summary.get("default_route_check_count"),
        "default_route_speedup_vs_reference": summary.get(
            "default_route_speedup_vs_reference"
        ),
        "github_plan_phase2_rejection_sample_accounting_status": summary.get(
            "github_plan_phase2_rejection_sample_accounting_status"
        ),
        "github_plan_matrix_rejection_sample_accounting_status": summary.get(
            "github_plan_matrix_rejection_sample_accounting_status"
        ),
        "matrix_rejection_sample_accounting_status": summary.get(
            "matrix_rejection_sample_accounting_status"
        ),
        "default_promotion_rejection_sample_accounting_status": summary.get(
            "default_promotion_rejection_sample_accounting_status"
        ),
        "github_plan_phase2_sample_accounting_closure_status": summary.get(
            "github_plan_phase2_sample_accounting_closure_status"
        ),
        "github_plan_matrix_sample_accounting_closure_status": summary.get(
            "github_plan_matrix_sample_accounting_closure_status"
        ),
        "matrix_sample_accounting_closure_status": summary.get(
            "matrix_sample_accounting_closure_status"
        ),
        "default_promotion_sample_accounting_closure_status": summary.get(
            "default_promotion_sample_accounting_closure_status"
        ),
        "matrix_integration_engine_policy_ready": summary.get(
            "matrix_integration_engine_policy_ready"
        ),
        "matrix_acceptance_integration_engine_policy_status": summary.get(
            "matrix_acceptance_integration_engine_policy_status"
        ),
        "matrix_pipeline_integration_engine_policy_status": summary.get(
            "matrix_pipeline_integration_engine_policy_status"
        ),
        "default_promotion_integration_engine_policy_ready": summary.get(
            "default_promotion_integration_engine_policy_ready"
        ),
        "default_promotion_acceptance_integration_engine_policy_status": summary.get(
            "default_promotion_acceptance_integration_engine_policy_status"
        ),
        "default_promotion_pipeline_integration_engine_policy_status": summary.get(
            "default_promotion_pipeline_integration_engine_policy_status"
        ),
        "github_plan_phase2_stack_engine_contract_status": summary.get(
            "github_plan_phase2_stack_engine_contract_status"
        ),
        "github_plan_matrix_stack_engine_contract_status": summary.get(
            "github_plan_matrix_stack_engine_contract_status"
        ),
        "matrix_stack_engine_contract_status": summary.get(
            "matrix_stack_engine_contract_status"
        ),
        "default_promotion_stack_engine_contract_status": summary.get(
            "default_promotion_stack_engine_contract_status"
        ),
        "matrix_stack_engine_contract_default_gap_count": summary.get(
            "matrix_stack_engine_contract_default_gap_count"
        ),
        "default_promotion_stack_engine_contract_default_gap_count": summary.get(
            "default_promotion_stack_engine_contract_default_gap_count"
        ),
        "matrix_resident_winsorized_sweep_status": summary.get(
            "matrix_resident_winsorized_sweep_status"
        ),
        "matrix_resident_winsorized_sweep_required_frame_count": summary.get(
            "matrix_resident_winsorized_sweep_required_frame_count"
        ),
        "matrix_resident_winsorized_sweep_required_frame_count_passed": summary.get(
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        ),
        "matrix_resident_winsorized_sweep_check_count": summary.get(
            "matrix_resident_winsorized_sweep_check_count"
        ),
        "default_promotion_resident_winsorized_sweep_status": summary.get(
            "default_promotion_resident_winsorized_sweep_status"
        ),
        "default_promotion_resident_winsorized_sweep_required_frame_count": summary.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count"
        ),
        "default_promotion_resident_winsorized_sweep_required_frame_count_passed": (
            summary.get(
                "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
            )
        ),
        "default_promotion_resident_winsorized_sweep_check_count": summary.get(
            "default_promotion_resident_winsorized_sweep_check_count"
        ),
        "matrix_stack_engine_publication_audit_status": summary.get(
            "matrix_stack_engine_publication_audit_status"
        ),
        "matrix_stack_engine_publication_audit_ready": summary.get(
            "matrix_stack_engine_publication_audit_ready"
        ),
        "matrix_stack_engine_publication_policy_agreement": summary.get(
            "matrix_stack_engine_publication_policy_agreement"
        ),
        "matrix_stack_engine_publication_resident_winsorized_agreement": summary.get(
            "matrix_stack_engine_publication_resident_winsorized_agreement"
        ),
        "default_promotion_stack_engine_publication_audit_status": summary.get(
            "default_promotion_stack_engine_publication_audit_status"
        ),
        "default_promotion_stack_engine_publication_audit_ready": summary.get(
            "default_promotion_stack_engine_publication_audit_ready"
        ),
        "default_promotion_stack_engine_publication_policy_agreement": summary.get(
            "default_promotion_stack_engine_publication_policy_agreement"
        ),
        "default_promotion_stack_engine_publication_resident_winsorized_agreement": (
            summary.get(
                "default_promotion_stack_engine_publication_resident_winsorized_agreement"
            )
        ),
        "matrix_quality_metrics_compare_present": summary.get(
            "matrix_quality_metrics_compare_present"
        ),
        "matrix_quality_metrics_compare_ready": summary.get(
            "matrix_quality_metrics_compare_ready"
        ),
        "matrix_quality_metrics_compare_status": summary.get(
            "matrix_quality_metrics_compare_status"
        ),
        "matrix_quality_metrics_compare_failed_check_count": summary.get(
            "matrix_quality_metrics_compare_failed_check_count"
        ),
        "default_promotion_quality_metrics_compare_present": summary.get(
            "default_promotion_quality_metrics_compare_present"
        ),
        "default_promotion_quality_metrics_compare_ready": summary.get(
            "default_promotion_quality_metrics_compare_ready"
        ),
        "default_promotion_quality_metrics_compare_status": summary.get(
            "default_promotion_quality_metrics_compare_status"
        ),
        "default_promotion_quality_metrics_compare_failed_check_count": summary.get(
            "default_promotion_quality_metrics_compare_failed_check_count"
        ),
        "github_plan_matrix_resident_result_contract_ready": summary.get(
            "github_plan_matrix_resident_result_contract_ready"
        ),
        "github_plan_matrix_resident_result_contract_status": summary.get(
            "github_plan_matrix_resident_result_contract_status"
        ),
        "github_plan_matrix_resident_result_contract_phase2_check_passed": (
            summary.get(
                "github_plan_matrix_resident_result_contract_phase2_check_passed"
            )
        ),
        "github_plan_matrix_resident_result_contract_required_count": summary.get(
            "github_plan_matrix_resident_result_contract_required_count"
        ),
        "github_plan_matrix_resident_result_contract_failed_count": summary.get(
            "github_plan_matrix_resident_result_contract_failed_count"
        ),
        "matrix_resident_result_contract_ready": summary.get(
            "matrix_resident_result_contract_ready"
        ),
        "matrix_resident_result_contract_status": summary.get(
            "matrix_resident_result_contract_status"
        ),
        "matrix_resident_result_contract_phase2_check_passed": summary.get(
            "matrix_resident_result_contract_phase2_check_passed"
        ),
        "matrix_resident_result_contract_required_count": summary.get(
            "matrix_resident_result_contract_required_count"
        ),
        "matrix_resident_result_contract_failed_count": summary.get(
            "matrix_resident_result_contract_failed_count"
        ),
        "default_promotion_resident_result_contract_ready": summary.get(
            "default_promotion_resident_result_contract_ready"
        ),
        "default_promotion_resident_result_contract_status": summary.get(
            "default_promotion_resident_result_contract_status"
        ),
        "default_promotion_resident_result_contract_phase2_check_passed": (
            summary.get(
                "default_promotion_resident_result_contract_phase2_check_passed"
            )
        ),
        "default_promotion_resident_result_contract_required_count": summary.get(
            "default_promotion_resident_result_contract_required_count"
        ),
        "default_promotion_resident_result_contract_failed_count": summary.get(
            "default_promotion_resident_result_contract_failed_count"
        ),
        "github_plan_phase2_rejection_sample_accounting_passed": _check_passed(
            payload,
            "github_plan_phase2_rejection_sample_accounting_passed",
        ),
        "github_plan_matrix_rejection_sample_accounting_passed": _check_passed(
            payload,
            "github_plan_matrix_rejection_sample_accounting_passed",
        ),
        "matrix_rejection_sample_accounting_passed": _check_passed(
            payload,
            "matrix_rejection_sample_accounting_passed",
        ),
        "default_promotion_rejection_sample_accounting_passed": _check_passed(
            payload,
            "default_promotion_rejection_sample_accounting_passed",
        ),
        "github_plan_matrix_rejection_accounting_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_rejection_accounting_matches_matrix",
        ),
        "github_plan_phase2_sample_accounting_closure_passed": _check_passed(
            payload,
            "github_plan_phase2_sample_accounting_closure_passed",
        ),
        "github_plan_matrix_sample_accounting_closure_passed": _check_passed(
            payload,
            "github_plan_matrix_sample_accounting_closure_passed",
        ),
        "matrix_sample_accounting_closure_passed": _check_passed(
            payload,
            "matrix_sample_accounting_closure_passed",
        ),
        "default_promotion_sample_accounting_closure_passed": _check_passed(
            payload,
            "default_promotion_sample_accounting_closure_passed",
        ),
        "github_plan_matrix_sample_closure_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_sample_closure_matches_matrix",
        ),
        "windows_release_matrix_acceptance_integration_engine_policy_passed": (
            _check_passed(
                payload,
                "windows_release_matrix_acceptance_integration_engine_policy_passed",
            )
        ),
        "windows_release_matrix_pipeline_integration_engine_policy_passed": (
            _check_passed(
                payload,
                "windows_release_matrix_pipeline_integration_engine_policy_passed",
            )
        ),
        "default_promotion_acceptance_integration_engine_policy_passed": (
            _check_passed(
                payload,
                "default_promotion_acceptance_integration_engine_policy_passed",
            )
        ),
        "default_promotion_pipeline_integration_engine_policy_passed": (
            _check_passed(
                payload,
                "default_promotion_pipeline_integration_engine_policy_passed",
            )
        ),
        "matrix_integration_engine_policy_matches_default_promotion": _check_passed(
            payload,
            "matrix_integration_engine_policy_matches_default_promotion",
        ),
        "github_plan_phase2_stack_engine_default_contract_ready": _check_passed(
            payload,
            "github_plan_phase2_stack_engine_default_contract_ready",
        ),
        "github_plan_matrix_stack_engine_contract_ready": _check_passed(
            payload,
            "github_plan_matrix_stack_engine_contract_ready",
        ),
        "github_plan_stack_engine_contract_agreement_passed": _check_passed(
            payload,
            "github_plan_stack_engine_contract_agreement_passed",
        ),
        "matrix_stack_engine_contract_ready": _check_passed(
            payload,
            "matrix_stack_engine_contract_ready",
        ),
        "default_promotion_stack_engine_contract_ready": _check_passed(
            payload,
            "default_promotion_stack_engine_contract_ready",
        ),
        "github_plan_matrix_stack_engine_contract_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_stack_engine_contract_matches_matrix",
        ),
        "matrix_stack_engine_contract_matches_default_promotion": _check_passed(
            payload,
            "matrix_stack_engine_contract_matches_default_promotion",
        ),
        "matrix_resident_winsorized_sweep_audit_passed": _check_passed(
            payload,
            "matrix_resident_winsorized_sweep_audit_passed",
        ),
        "matrix_resident_winsorized_required_frame_passed": _check_passed(
            payload,
            "matrix_resident_winsorized_required_frame_passed",
        ),
        "matrix_resident_winsorized_sweep_check_count_passed": _check_passed(
            payload,
            "matrix_resident_winsorized_sweep_check_count",
        ),
        "default_promotion_resident_winsorized_sweep_audit_passed": _check_passed(
            payload,
            "default_promotion_resident_winsorized_sweep_audit_passed",
        ),
        "default_promotion_resident_winsorized_required_frame_passed": _check_passed(
            payload,
            "default_promotion_resident_winsorized_required_frame_passed",
        ),
        "default_promotion_resident_winsorized_sweep_matches_matrix": _check_passed(
            payload,
            "default_promotion_resident_winsorized_sweep_matches_matrix",
        ),
        "matrix_stack_engine_publication_audit_passed": _check_passed(
            payload,
            "matrix_stack_engine_publication_audit_passed",
        ),
        "matrix_stack_engine_publication_policy_chain_passed": _check_passed(
            payload,
            "matrix_stack_engine_publication_policy_chain_passed",
        ),
        "matrix_stack_engine_publication_resident_winsorized_chain_passed": (
            _check_passed(
                payload,
                "matrix_stack_engine_publication_resident_winsorized_chain_passed",
            )
        ),
        "default_promotion_stack_engine_publication_audit_passed": _check_passed(
            payload,
            "default_promotion_stack_engine_publication_audit_passed",
        ),
        "default_promotion_stack_engine_publication_policy_chain_passed": (
            _check_passed(
                payload,
                "default_promotion_stack_engine_publication_policy_chain_passed",
            )
        ),
        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed": (
            _check_passed(
                payload,
                "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
            )
        ),
        "matrix_stack_engine_publication_audit_matches_default_promotion": (
            _check_passed(
                payload,
                "matrix_stack_engine_publication_audit_matches_default_promotion",
            )
        ),
        "windows_release_matrix_quality_metrics_compare_handoff_passed": (
            _check_passed(
                payload,
                "windows_release_matrix_quality_metrics_compare_handoff_passed",
            )
        ),
        "default_promotion_quality_metrics_compare_handoff_passed": (
            _check_passed(
                payload,
                "default_promotion_quality_metrics_compare_handoff_passed",
            )
        ),
        "matrix_quality_metrics_compare_matches_default_promotion": (
            _check_passed(
                payload,
                "matrix_quality_metrics_compare_matches_default_promotion",
            )
        ),
        "github_plan_matrix_resident_result_contract_handoff_passed": _check_passed(
            payload,
            "github_plan_matrix_resident_result_contract_handoff_passed",
        ),
        "matrix_resident_result_contract_handoff_passed": _check_passed(
            payload,
            "matrix_resident_result_contract_handoff_passed",
        ),
        "default_promotion_resident_result_contract_handoff_passed": _check_passed(
            payload,
            "default_promotion_resident_result_contract_handoff_passed",
        ),
        "github_plan_matrix_resident_result_contract_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_resident_result_contract_matches_matrix",
        ),
        "matrix_resident_result_contract_matches_default_promotion": _check_passed(
            payload,
            "matrix_resident_result_contract_matches_default_promotion",
        ),
        "matrix_stack_engine_runtime_default_ready": summary.get(
            "matrix_stack_engine_runtime_default_ready",
            matrix_runtime_default.get("matrix_stack_engine_runtime_default_ready"),
        ),
        "matrix_acceptance_stack_engine_runtime_default_status": summary.get(
            "matrix_acceptance_stack_engine_runtime_default_status",
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_status"
            ),
        ),
        "matrix_pipeline_stack_engine_runtime_default_status": summary.get(
            "matrix_pipeline_stack_engine_runtime_default_status",
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_status"
            ),
        ),
        "matrix_acceptance_stack_engine_runtime_default_check_present": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_check_present"
            )
        ),
        "matrix_acceptance_stack_engine_runtime_default_check_passed": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_check_passed"
            )
        ),
        "matrix_acceptance_stack_engine_runtime_default_phase2_check_passed": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_phase2_check_passed"
            )
        ),
        "matrix_acceptance_stack_engine_runtime_default_master_count": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_master_count"
            )
        ),
        "matrix_stack_engine_runtime_default_acceptance_legacy_master_count": (
            summary.get(
                "matrix_stack_engine_runtime_default_acceptance_legacy_master_count",
                matrix_runtime_default.get(
                    "matrix_acceptance_stack_engine_runtime_default_legacy_master_count"
                ),
            )
        ),
        "matrix_acceptance_stack_engine_runtime_default_failed_master_count": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_failed_master_count"
            )
        ),
        "matrix_acceptance_stack_engine_runtime_default_failed_output_count": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_failed_output_count"
            )
        ),
        "matrix_acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            matrix_runtime_default.get(
                "matrix_acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count"
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_check_present": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_check_present"
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_check_passed": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_check_passed"
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_phase2_check_passed": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_phase2_check_passed"
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_master_count": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_master_count"
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_legacy_master_count": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_legacy_master_count"
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_failed_master_count": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_failed_master_count"
            )
        ),
        "matrix_stack_engine_runtime_default_pipeline_failed_output_count": (
            summary.get(
                "matrix_stack_engine_runtime_default_pipeline_failed_output_count",
                matrix_runtime_default.get(
                    "matrix_pipeline_stack_engine_runtime_default_failed_output_count"
                ),
            )
        ),
        "matrix_pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            matrix_runtime_default.get(
                "matrix_pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
            )
        ),
        "default_promotion_stack_engine_runtime_default_ready": summary.get(
            "default_promotion_stack_engine_runtime_default_ready",
            default_runtime_default.get(
                "default_promotion_stack_engine_runtime_default_ready"
            ),
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_status": summary.get(
            "default_promotion_acceptance_stack_engine_runtime_default_status",
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_status"
            ),
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_status": summary.get(
            "default_promotion_pipeline_stack_engine_runtime_default_status",
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_status"
            ),
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_check_present": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_check_present"
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_check_passed": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_check_passed"
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_phase2_check_passed": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_phase2_check_passed"
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_master_count": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_master_count"
            )
        ),
        "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count": (
            summary.get(
                "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count",
                default_runtime_default.get(
                    "default_promotion_acceptance_stack_engine_runtime_default_legacy_master_count"
                ),
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_failed_master_count": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_failed_master_count"
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_failed_output_count": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_failed_output_count"
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            default_runtime_default.get(
                "default_promotion_acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count"
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_check_present": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_check_present"
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_check_passed": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_check_passed"
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_phase2_check_passed": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_phase2_check_passed"
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_master_count": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_master_count"
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_legacy_master_count": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_legacy_master_count"
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_failed_master_count": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_failed_master_count"
            )
        ),
        "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count": (
            summary.get(
                "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count",
                default_runtime_default.get(
                    "default_promotion_pipeline_stack_engine_runtime_default_failed_output_count"
                ),
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            default_runtime_default.get(
                "default_promotion_pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
            )
        ),
        "windows_release_matrix_acceptance_stack_engine_runtime_default_passed": (
            _check_passed(
                payload,
                "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
            )
        ),
        "windows_release_matrix_pipeline_stack_engine_runtime_default_passed": (
            _check_passed(
                payload,
                "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
            )
        ),
        "default_promotion_acceptance_stack_engine_runtime_default_passed": (
            _check_passed(
                payload,
                "default_promotion_acceptance_stack_engine_runtime_default_passed",
            )
        ),
        "default_promotion_pipeline_stack_engine_runtime_default_passed": (
            _check_passed(
                payload,
                "default_promotion_pipeline_stack_engine_runtime_default_passed",
            )
        ),
        "matrix_stack_engine_runtime_default_matches_default_promotion": (
            _check_passed(
                payload,
                "matrix_stack_engine_runtime_default_matches_default_promotion",
            )
        ),
        "matrix_direct_runtime_evidence_ready": summary.get(
            "matrix_direct_runtime_evidence_ready"
        ),
        "matrix_direct_runtime_acceptance_source": summary.get(
            "matrix_direct_runtime_acceptance_source"
        ),
        "matrix_direct_runtime_acceptance_check_count": summary.get(
            "matrix_direct_runtime_acceptance_check_count"
        ),
        "matrix_direct_runtime_pipeline_calibration_source": summary.get(
            "matrix_direct_runtime_pipeline_calibration_source"
        ),
        "matrix_direct_runtime_pipeline_resident_lights": summary.get(
            "matrix_direct_runtime_pipeline_resident_lights"
        ),
        "default_promotion_direct_runtime_evidence_ready": summary.get(
            "default_promotion_direct_runtime_evidence_ready"
        ),
        "default_promotion_direct_runtime_acceptance_source": summary.get(
            "default_promotion_direct_runtime_acceptance_source"
        ),
        "default_promotion_direct_runtime_acceptance_check_count": summary.get(
            "default_promotion_direct_runtime_acceptance_check_count"
        ),
        "default_promotion_direct_runtime_pipeline_calibration_source": summary.get(
            "default_promotion_direct_runtime_pipeline_calibration_source"
        ),
        "default_promotion_direct_runtime_pipeline_resident_lights": summary.get(
            "default_promotion_direct_runtime_pipeline_resident_lights"
        ),
        "windows_release_matrix_direct_acceptance_fastpath_evidence": _check_passed(
            payload,
            "windows_release_matrix_direct_acceptance_fastpath_evidence",
        ),
        "windows_release_matrix_direct_pipeline_calibration_evidence": _check_passed(
            payload,
            "windows_release_matrix_direct_pipeline_calibration_evidence",
        ),
        "default_promotion_direct_acceptance_fastpath_evidence": _check_passed(
            payload,
            "default_promotion_direct_acceptance_fastpath_evidence",
        ),
        "default_promotion_direct_pipeline_calibration_evidence": _check_passed(
            payload,
            "default_promotion_direct_pipeline_calibration_evidence",
        ),
        "matrix_direct_runtime_evidence_matches_default_promotion": _check_passed(
            payload,
            "matrix_direct_runtime_evidence_matches_default_promotion",
        ),
        "github_plan_matrix_release_direct_publication_guard_ready": summary.get(
            "github_plan_matrix_release_direct_publication_guard_ready"
        ),
        "github_plan_matrix_release_direct_publication_guard_lights": summary.get(
            "github_plan_matrix_release_direct_publication_guard_lights"
        ),
        "github_plan_matrix_default_promotion_release_direct_publication_guard_ready": (
            summary.get(
                "github_plan_matrix_default_promotion_release_direct_publication_guard_ready"
            )
        ),
        "github_plan_matrix_default_promotion_release_direct_publication_guard_lights": (
            summary.get(
                "github_plan_matrix_default_promotion_release_direct_publication_guard_lights"
            )
        ),
        "matrix_release_direct_publication_guard_ready": summary.get(
            "matrix_release_direct_publication_guard_ready"
        ),
        "matrix_release_direct_publication_guard_source_ready": summary.get(
            "matrix_release_direct_publication_guard_source_ready"
        ),
        "matrix_release_direct_publication_guard_count_ready": summary.get(
            "matrix_release_direct_publication_guard_count_ready"
        ),
        "matrix_release_direct_publication_guard_check_passed": summary.get(
            "matrix_release_direct_publication_guard_check_passed"
        ),
        "matrix_release_direct_publication_guard_lights": summary.get(
            "matrix_release_direct_publication_guard_lights"
        ),
        "matrix_default_promotion_release_direct_publication_guard_ready": summary.get(
            "matrix_default_promotion_release_direct_publication_guard_ready"
        ),
        "matrix_default_promotion_release_direct_publication_guard_lights": summary.get(
            "matrix_default_promotion_release_direct_publication_guard_lights"
        ),
        "default_promotion_release_direct_publication_guard_ready": summary.get(
            "default_promotion_release_direct_publication_guard_ready"
        ),
        "default_promotion_release_direct_publication_guard_lights": summary.get(
            "default_promotion_release_direct_publication_guard_lights"
        ),
        "matrix_release_quality_publication_guard_present": summary.get(
            "matrix_release_quality_publication_guard_present"
        ),
        "matrix_release_quality_publication_guard_ready": summary.get(
            "matrix_release_quality_publication_guard_ready"
        ),
        "matrix_release_quality_publication_guard_check_passed": summary.get(
            "matrix_release_quality_publication_guard_check_passed"
        ),
        "matrix_release_quality_publication_guard_layers_ready": summary.get(
            "matrix_release_quality_publication_guard_layers_ready"
        ),
        "matrix_release_quality_publication_guard_raw_status": summary.get(
            "matrix_release_quality_publication_guard_raw_status"
        ),
        "matrix_release_quality_publication_guard_phase2_status": summary.get(
            "matrix_release_quality_publication_guard_phase2_status"
        ),
        "matrix_default_promotion_release_quality_publication_guard_ready": (
            summary.get(
                "matrix_default_promotion_release_quality_publication_guard_ready"
            )
        ),
        "matrix_default_promotion_release_quality_publication_guard_raw_status": (
            summary.get(
                "matrix_default_promotion_release_quality_publication_guard_raw_status"
            )
        ),
        "matrix_default_promotion_release_quality_publication_guard_phase2_status": (
            summary.get(
                "matrix_default_promotion_release_quality_publication_guard_phase2_status"
            )
        ),
        "default_promotion_release_quality_publication_guard_present": summary.get(
            "default_promotion_release_quality_publication_guard_present"
        ),
        "default_promotion_release_quality_publication_guard_ready": summary.get(
            "default_promotion_release_quality_publication_guard_ready"
        ),
        "default_promotion_release_quality_publication_guard_check_passed": (
            summary.get(
                "default_promotion_release_quality_publication_guard_check_passed"
            )
        ),
        "default_promotion_release_quality_publication_guard_layers_ready": (
            summary.get(
                "default_promotion_release_quality_publication_guard_layers_ready"
            )
        ),
        "default_promotion_release_quality_publication_guard_raw_status": (
            summary.get(
                "default_promotion_release_quality_publication_guard_raw_status"
            )
        ),
        "default_promotion_release_quality_publication_guard_phase2_status": (
            summary.get(
                "default_promotion_release_quality_publication_guard_phase2_status"
            )
        ),
        "matrix_release_decision_quality_compare_publication_guard_passed": (
            _check_passed(
                payload,
                "matrix_release_decision_quality_compare_publication_guard_passed",
            )
        ),
        "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed": (
            _check_passed(
                payload,
                "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed",
            )
        ),
        "default_promotion_release_decision_quality_compare_publication_guard_passed": (
            _check_passed(
                payload,
                "default_promotion_release_decision_quality_compare_publication_guard_passed",
            )
        ),
        "matrix_release_decision_quality_publication_guard_matches_default_promotion": (
            _check_passed(
                payload,
                "matrix_release_decision_quality_publication_guard_matches_default_promotion",
            )
        ),
        "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest": (
            _check_passed(
                payload,
                "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest",
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_passed": (
            _check_passed(
                payload,
                "matrix_release_decision_release_quality_publication_guard_passed",
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_passed": (
            _check_passed(
                payload,
                "matrix_default_promotion_release_decision_release_quality_publication_guard_passed",
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_passed": (
            _check_passed(
                payload,
                "default_promotion_release_decision_release_quality_publication_guard_passed",
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_matches_default_promotion": (
            _check_passed(
                payload,
                "matrix_release_decision_release_quality_publication_guard_matches_default_promotion",
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest": (
            _check_passed(
                payload,
                "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest",
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_final_checks_ready": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_final_checks_ready"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_final_checks_match": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_final_checks_match"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_raw_final_checks_ready": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_raw_final_checks_ready"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_phase2_final_checks_ready": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_phase2_final_checks_ready"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_ready": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_ready"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_match": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_match"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_final_checks_ready": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_final_checks_ready"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_final_checks_match": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_final_checks_match"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_final_evidence_ready": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_final_evidence_ready"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_final_evidence_match": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_final_evidence_match"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_raw_final_evidence_ready": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_raw_final_evidence_ready"
            )
        ),
        "matrix_release_decision_release_quality_publication_guard_phase2_final_evidence_ready": (
            summary.get(
                "matrix_release_decision_release_quality_publication_guard_phase2_final_evidence_ready"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_match": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_match"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready"
            )
        ),
        "matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready": (
            summary.get(
                "matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_final_evidence_match": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_final_evidence_match"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready"
            )
        ),
        "default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready": (
            summary.get(
                "default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready"
            )
        ),
        "github_plan_matrix_resident_fastpath_handoff_ready": summary.get(
            "github_plan_matrix_resident_fastpath_handoff_ready"
        ),
        "github_plan_matrix_resident_fastpath_handoff_raw_status": summary.get(
            "github_plan_matrix_resident_fastpath_handoff_raw_status"
        ),
        "github_plan_matrix_resident_fastpath_handoff_phase2_status": summary.get(
            "github_plan_matrix_resident_fastpath_handoff_phase2_status"
        ),
        "github_plan_matrix_resident_fastpath_handoff_raw_check_count": summary.get(
            "github_plan_matrix_resident_fastpath_handoff_raw_check_count"
        ),
        "matrix_resident_fastpath_handoff_ready": summary.get(
            "matrix_resident_fastpath_handoff_ready"
        ),
        "matrix_resident_fastpath_handoff_raw_status": summary.get(
            "matrix_resident_fastpath_handoff_raw_status"
        ),
        "matrix_resident_fastpath_handoff_phase2_status": summary.get(
            "matrix_resident_fastpath_handoff_phase2_status"
        ),
        "matrix_resident_fastpath_handoff_raw_check_count": summary.get(
            "matrix_resident_fastpath_handoff_raw_check_count"
        ),
        "default_promotion_resident_fastpath_handoff_ready": summary.get(
            "default_promotion_resident_fastpath_handoff_ready"
        ),
        "default_promotion_resident_fastpath_handoff_raw_status": summary.get(
            "default_promotion_resident_fastpath_handoff_raw_status"
        ),
        "default_promotion_resident_fastpath_handoff_phase2_status": summary.get(
            "default_promotion_resident_fastpath_handoff_phase2_status"
        ),
        "default_promotion_resident_fastpath_handoff_raw_check_count": summary.get(
            "default_promotion_resident_fastpath_handoff_raw_check_count"
        ),
        "github_plan_matrix_release_decision_direct_publication_guard_passed": (
            _check_passed(
                payload,
                "github_plan_matrix_release_decision_direct_publication_guard_passed",
            )
        ),
        "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed": (
            _check_passed(
                payload,
                "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed",
            )
        ),
        "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix": (
            _check_passed(
                payload,
                "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix",
            )
        ),
        "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix": (
            _check_passed(
                payload,
                "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix",
            )
        ),
        "matrix_release_decision_direct_runtime_publication_guard_passed": (
            _check_passed(
                payload,
                "matrix_release_decision_direct_runtime_publication_guard_passed",
            )
        ),
        "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed": (
            _check_passed(
                payload,
                "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed",
            )
        ),
        "default_promotion_release_decision_direct_runtime_publication_guard_passed": (
            _check_passed(
                payload,
                "default_promotion_release_decision_direct_runtime_publication_guard_passed",
            )
        ),
        "matrix_release_decision_direct_publication_guard_matches_default_promotion": (
            _check_passed(
                payload,
                "matrix_release_decision_direct_publication_guard_matches_default_promotion",
            )
        ),
        "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest": (
            _check_passed(
                payload,
                "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest",
            )
        ),
        "github_plan_matrix_resident_fastpath_release_handoff_ready": _check_passed(
            payload,
            "github_plan_matrix_resident_fastpath_release_handoff_ready",
        ),
        "matrix_resident_fastpath_release_handoff_ready": _check_passed(
            payload,
            "matrix_resident_fastpath_release_handoff_ready",
        ),
        "default_promotion_resident_fastpath_release_handoff_ready": _check_passed(
            payload,
            "default_promotion_resident_fastpath_release_handoff_ready",
        ),
        "github_plan_matrix_resident_fastpath_handoff_matches_matrix": _check_passed(
            payload,
            "github_plan_matrix_resident_fastpath_handoff_matches_matrix",
        ),
        "matrix_resident_fastpath_handoff_matches_default_promotion": _check_passed(
            payload,
            "matrix_resident_fastpath_handoff_matches_default_promotion",
        ),
        "failed_checks": payload.get("failed_checks"),
    }


def _publish_preflight_runtime_default_layer(
    payload: dict[str, Any],
    layer_name: str,
    prefix: str,
) -> dict[str, Any]:
    layer = payload.get(layer_name) if isinstance(payload.get(layer_name), dict) else {}
    return {
        f"{prefix}_stack_engine_runtime_default_ready": layer.get(
            "stack_engine_runtime_default_ready"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_status": layer.get(
            "acceptance_stack_engine_runtime_default_status"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_check_present": layer.get(
            "acceptance_stack_engine_runtime_default_check_present"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_check_passed": layer.get(
            "acceptance_stack_engine_runtime_default_check_passed"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_phase2_check_passed": layer.get(
            "acceptance_stack_engine_runtime_default_phase2_check_passed"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_master_count": layer.get(
            "acceptance_stack_engine_runtime_default_master_count"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_legacy_master_count": layer.get(
            "acceptance_stack_engine_runtime_default_legacy_master_count"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_failed_master_count": layer.get(
            "acceptance_stack_engine_runtime_default_failed_master_count"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_failed_output_count": layer.get(
            "acceptance_stack_engine_runtime_default_failed_output_count"
        ),
        f"{prefix}_acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count": layer.get(
            "acceptance_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_status": layer.get(
            "pipeline_stack_engine_runtime_default_status"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_check_present": layer.get(
            "pipeline_stack_engine_runtime_default_check_present"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_check_passed": layer.get(
            "pipeline_stack_engine_runtime_default_check_passed"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_phase2_check_passed": layer.get(
            "pipeline_stack_engine_runtime_default_phase2_check_passed"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_master_count": layer.get(
            "pipeline_stack_engine_runtime_default_master_count"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_legacy_master_count": layer.get(
            "pipeline_stack_engine_runtime_default_legacy_master_count"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_failed_master_count": layer.get(
            "pipeline_stack_engine_runtime_default_failed_master_count"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_failed_output_count": layer.get(
            "pipeline_stack_engine_runtime_default_failed_output_count"
        ),
        f"{prefix}_pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count": layer.get(
            "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
        ),
    }


def _publication_audit_layer(payload: dict[str, Any], name: str) -> dict[str, Any]:
    layers = payload.get("layers") if isinstance(payload.get("layers"), dict) else {}
    layer = layers.get(name) if isinstance(layers.get(name), dict) else {}
    return {
        "status": layer.get("status"),
        "ready": layer.get("ready"),
        "gap_count": layer.get("gap_count"),
    }


def _publication_audit_check(payload: dict[str, Any], name: str) -> bool | None:
    return _check_passed(payload, name)


def _stack_engine_publication_audit_summary(
    path: str | Path | None,
) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "failed_checks": ["artifact_missing"],
            "check_count": 0,
            "failed_check_count": 1,
        }
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    failed_checks = payload.get("failed_checks")
    if not isinstance(failed_checks, list):
        failed_checks = [
            str(item.get("name"))
            for item in checks
            if isinstance(item, dict) and item.get("passed") is not True
        ]
    layers = payload.get("layers") if isinstance(payload.get("layers"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed") is True,
        "recommendation": payload.get("recommendation"),
        "layer_count": len(layers),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": [str(item) for item in failed_checks],
        "source_contract": _publication_audit_layer(payload, "source_contract"),
        "phase2_direct_contract": _publication_audit_layer(
            payload,
            "phase2_direct_contract",
        ),
        "publish_preflight": _publication_audit_layer(payload, "publish_preflight"),
        "phase2_publish_preflight": _publication_audit_layer(
            payload,
            "phase2_publish_preflight",
        ),
        "publish_preflight_resident_winsorized_sweep": _publication_audit_layer(
            payload,
            "publish_preflight_resident_winsorized_sweep",
        ),
        "phase2_publish_preflight_resident_winsorized_sweep": (
            _publication_audit_layer(
                payload,
                "phase2_publish_preflight_resident_winsorized_sweep",
            )
        ),
        "publish_preflight_resident_result_contract": _publication_audit_layer(
            payload,
            "publish_preflight_resident_result_contract",
        ),
        "phase2_publish_preflight_resident_result_contract": (
            _publication_audit_layer(
                payload,
                "phase2_publish_preflight_resident_result_contract",
            )
        ),
        "publish_preflight_integration_engine_policy": _publication_audit_layer(
            payload,
            "publish_preflight_integration_engine_policy",
        ),
        "phase2_publish_preflight_integration_engine_policy": (
            _publication_audit_layer(
                payload,
                "phase2_publish_preflight_integration_engine_policy",
            )
        ),
        "publish_preflight_direct_runtime_evidence": _publication_audit_layer(
            payload,
            "publish_preflight_direct_runtime_evidence",
        ),
        "phase2_publish_preflight_direct_runtime_evidence": (
            _publication_audit_layer(
                payload,
                "phase2_publish_preflight_direct_runtime_evidence",
            )
        ),
        "source_contract_ready": _publication_audit_check(
            payload,
            "source_contract_ready",
        ),
        "phase2_direct_contract_ready": _publication_audit_check(
            payload,
            "phase2_direct_contract_ready",
        ),
        "publish_preflight_stack_engine_ready": _publication_audit_check(
            payload,
            "publish_preflight_stack_engine_ready",
        ),
        "phase2_publish_preflight_stack_engine_ready": _publication_audit_check(
            payload,
            "phase2_publish_preflight_stack_engine_ready",
        ),
        "publish_preflight_resident_winsorized_sweep_ready": (
            _publication_audit_check(
                payload,
                "publish_preflight_resident_winsorized_sweep_ready",
            )
        ),
        "phase2_publish_preflight_resident_winsorized_sweep_ready": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_resident_winsorized_sweep_ready",
            )
        ),
        "phase2_publish_preflight_resident_winsorized_matches_publish_preflight": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_resident_winsorized_matches_publish_preflight",
            )
        ),
        "publish_preflight_resident_result_contract_ready": (
            _publication_audit_check(
                payload,
                "publish_preflight_resident_result_contract_ready",
            )
        ),
        "phase2_publish_preflight_resident_result_contract_ready": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_resident_result_contract_ready",
            )
        ),
        "phase2_publish_preflight_resident_result_contract_matches_publish_preflight": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_resident_result_contract_matches_publish_preflight",
            )
        ),
        "publish_preflight_integration_engine_policy_ready": (
            _publication_audit_check(
                payload,
                "publish_preflight_integration_engine_policy_ready",
            )
        ),
        "phase2_publish_preflight_integration_engine_policy_ready": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_integration_engine_policy_ready",
            )
        ),
        "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight",
            )
        ),
        "publish_preflight_direct_runtime_evidence_ready": (
            _publication_audit_check(
                payload,
                "publish_preflight_direct_runtime_evidence_ready",
            )
        ),
        "phase2_publish_preflight_direct_runtime_evidence_ready": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_direct_runtime_evidence_ready",
            )
        ),
        "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight": (
            _publication_audit_check(
                payload,
                "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight",
            )
        ),
    }


def _check_passed(payload: dict[str, Any], name: str) -> bool | None:
    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and item.get("name") == name:
            return bool(item.get("passed"))
    return None


def _rejection_sample_accounting_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "integration_rejection_sample_counts_match_maps"
    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    check = next((item for item in checks if item.get("name") == check_name), None)
    pixel_verification = (
        payload.get("pixel_verification")
        if isinstance(payload.get("pixel_verification"), dict)
        else {}
    )
    integration_outputs = pixel_verification.get("integration_outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        accounting = output.get("rejection_sample_accounting")
        if not isinstance(accounting, dict):
            continue
        source_counts = accounting.get("source_counts")
        if not isinstance(source_counts, list):
            source_counts = []
        source_matches = accounting.get("source_matches")
        if not isinstance(source_matches, list):
            source_matches = []
        failed_matches = [
            {
                "source": match.get("source"),
                "actual": match.get("actual"),
                "summary": match.get("summary"),
                "delta": match.get("delta"),
            }
            for match in source_matches
            if isinstance(match, dict) and not match.get("passed")
        ]
        rows.append(
            {
                "item": output.get("item"),
                "status": accounting.get("status"),
                "required": bool(accounting.get("required")),
                "verified": bool(accounting.get("verified")),
                "ok": bool(accounting.get("ok")),
                "rejection": accounting.get("rejection"),
                "map_rejected_sample_sum": accounting.get("map_rejected_sample_sum"),
                "source_counts": source_counts,
                "failed_matches": failed_matches,
            }
        )

    failed_items = [row for row in rows if not row.get("ok")]
    check_present = isinstance(check, dict)
    check_passed = check.get("passed") is True if check_present else None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if not failed_items else "failed"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "pixel_verification_enabled": bool(pixel_verification.get("enabled")),
        "output_count": len(integration_outputs),
        "accounted_output_count": len(rows),
        "required_count": sum(1 for row in rows if row.get("required")),
        "verified_count": sum(1 for row in rows if row.get("verified")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
    }


def _sample_accounting_closure_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "integration_sample_accounting_closure"
    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    check = next((item for item in checks if item.get("name") == check_name), None)
    integration = payload.get("integration") if isinstance(payload.get("integration"), dict) else {}
    integration_outputs = integration.get("outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        closure = output.get("sample_accounting_closure")
        if not isinstance(closure, dict):
            continue
        rows.append(
            {
                "item": output.get("item"),
                "status": closure.get("status"),
                "present": bool(closure.get("present")),
                "required": bool(closure.get("required")),
                "passed": bool(closure.get("passed")),
                "input_total_match": closure.get("input_total_match"),
                "valid_rejection_match": closure.get("valid_rejection_match"),
                "input_samples": closure.get("input_samples"),
                "input_valid_samples_before_rejection": closure.get(
                    "input_valid_samples_before_rejection"
                ),
                "input_invalid_samples_before_rejection": closure.get(
                    "input_invalid_samples_before_rejection"
                ),
                "valid_samples_after_rejection": closure.get(
                    "valid_samples_after_rejection"
                ),
                "rejected_samples": closure.get("rejected_samples"),
                "semantics": closure.get("semantics"),
            }
        )

    failed_items = [row for row in rows if not row.get("passed")]
    check_present = isinstance(check, dict)
    check_passed = check.get("passed") is True if check_present else None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if not failed_items else "failed"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "output_count": len(integration_outputs),
        "present_count": sum(1 for row in rows if row.get("present")),
        "required_count": sum(1 for row in rows if row.get("required")),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "rows": rows,
    }


def _resident_result_contract_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "integration_resident_result_contract"
    check = _check_by_name(payload, check_name)
    integration = payload.get("integration") if isinstance(payload.get("integration"), dict) else {}
    integration_outputs = integration.get("outputs")
    if not isinstance(integration_outputs, list):
        integration_outputs = []

    rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    failed_check_names: set[str] = set()
    for output in integration_outputs:
        if not isinstance(output, dict):
            continue
        resident = output.get("resident_result_contract")
        if not isinstance(resident, dict):
            continue
        resident_contract = resident.get("contract")
        contract_checks = (
            resident_contract.get("checks")
            if isinstance(resident_contract, dict)
            else []
        )
        if not isinstance(contract_checks, list):
            contract_checks = []
        failed_checks = [
            item
            for item in contract_checks
            if isinstance(item, dict) and not item.get("passed")
        ]
        failed_check_names.update(str(item.get("name")) for item in failed_checks)
        row = {
            "item": output.get("item"),
            "backend": output.get("backend"),
            "memory_mode": output.get("memory_mode"),
            "status": resident.get("status"),
            "required": bool(resident.get("required")),
            "passed": resident.get("passed") is True,
            "contract_available": isinstance(resident_contract, dict),
            "check_count": len(contract_checks),
            "failed_check_count": len(failed_checks),
            "failed_checks": [
                {
                    "name": item.get("name"),
                    "note": item.get("note", ""),
                    "evidence": item.get("evidence")
                    if isinstance(item.get("evidence"), dict)
                    else {},
                }
                for item in failed_checks
            ],
        }
        rows.append(row)
        if failed_checks or (row["required"] and row["passed"] is not True):
            if not failed_checks:
                failed_check_names.add("resident_result_contract_missing_or_failed")
            failed_rows.append(row)

    check_present = isinstance(check, dict)
    check_passed = check.get("passed") is True if check_present else None
    if check_present:
        status = "passed" if check_passed else "failed"
    elif rows:
        status = "passed" if not failed_rows else "failed"
    else:
        status = "not_available"
    return {
        "schema_version": 1,
        "status": status,
        "check_name": check_name,
        "check_present": check_present,
        "check_passed": check_passed,
        "output_count": len(integration_outputs),
        "contract_count": len(rows),
        "required_count": sum(1 for row in rows if row.get("required")),
        "passed_count": sum(1 for row in rows if row.get("passed")),
        "failed_count": len(failed_rows),
        "failed_check_count": sum(
            int(row.get("failed_check_count") or 0) for row in failed_rows
        ),
        "failed_checks": sorted(failed_check_names),
        "failed_items": failed_rows,
        "rows": rows,
    }


def _integration_engine_policy_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "integration_default_engine_policy"
    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    check = next((item for item in checks if item.get("name") == check_name), None)
    integration = payload.get("integration") if isinstance(payload.get("integration"), dict) else {}
    engine_policy = (
        integration.get("engine_policy")
        if isinstance(integration.get("engine_policy"), dict)
        else {}
    )
    outputs = engine_policy.get("outputs")
    if not isinstance(outputs, list):
        outputs = []

    rows: list[dict[str, Any]] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        failures = output.get("failures")
        if not isinstance(failures, list):
            failures = []
        rows.append(
            {
                "item": output.get("item"),
                "status": output.get("status"),
                "required": bool(output.get("required")),
                "passed": bool(output.get("passed")),
                "backend": output.get("backend"),
                "memory_mode": output.get("memory_mode"),
                "tile_stack_mode": output.get("tile_stack_mode"),
                "failures": [str(item) for item in failures],
            }
        )

    failed_items = [row for row in rows if not row.get("passed")]
    if check is not None:
        check_passed = bool(check.get("passed"))
        status = "passed" if check_passed else "failed"
    elif engine_policy:
        check_passed = None
        status = "passed" if bool(engine_policy.get("passed")) and not failed_items else "failed"
    else:
        check_passed = None
        status = "not_available"
    return {
        "status": status,
        "check_name": check_name,
        "check_present": check is not None,
        "check_passed": check_passed,
        "top_level_present": engine_policy.get("top_level_present"),
        "top_level_default_ok": engine_policy.get("top_level_default_ok"),
        "output_count": int(engine_policy.get("output_count") or len(rows)),
        "non_resident_count": int(engine_policy.get("non_resident_count") or 0),
        "resident_count": int(engine_policy.get("resident_count") or 0),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "rows": rows,
    }


def _stack_engine_runtime_default_summary(payload: dict[str, Any]) -> dict[str, Any]:
    check_name = "stack_engine_runtime_default_path"
    runtime_default = (
        payload.get("stack_engine_runtime_default")
        if isinstance(payload.get("stack_engine_runtime_default"), dict)
        else {}
    )
    check = _check_by_name(payload, check_name)
    failed_masters = runtime_default.get("failed_masters")
    if not isinstance(failed_masters, list):
        failed_masters = []
    failed_outputs = runtime_default.get("failed_outputs")
    if not isinstance(failed_outputs, list):
        failed_outputs = []
    if check is not None:
        check_passed = bool(check.get("passed"))
        status = "passed" if check_passed else "failed"
    elif runtime_default:
        check_passed = None
        status = (
            "passed"
            if runtime_default.get("passed") is True
            and not failed_masters
            and not failed_outputs
            else "failed"
        )
    else:
        check_passed = None
        status = "not_available"
    return {
        "status": status,
        "check_name": check_name,
        "check_present": check is not None,
        "check_passed": check_passed,
        "passed": runtime_default.get("passed"),
        "master_count": runtime_default.get("master_count"),
        "master_stack_engine_count": runtime_default.get("master_stack_engine_count"),
        "master_resident_count": runtime_default.get("master_resident_count"),
        "legacy_master_count": runtime_default.get("legacy_master_count"),
        "integration_output_count": runtime_default.get("integration_output_count"),
        "integration_stack_engine_default_count": runtime_default.get(
            "integration_stack_engine_default_count"
        ),
        "integration_resident_count": runtime_default.get("integration_resident_count"),
        "explicit_cuda_fast_path_count": runtime_default.get(
            "explicit_cuda_fast_path_count"
        ),
        "failed_master_count": len(failed_masters),
        "failed_output_count": len(failed_outputs),
        "failed_masters": failed_masters,
        "failed_outputs": failed_outputs,
    }


def _acceptance_integration_engine_policy_summary(payload: dict[str, Any]) -> dict[str, Any]:
    release_evidence = (
        payload.get("release_contract_evidence")
        if isinstance(payload.get("release_contract_evidence"), dict)
        else {}
    )
    pipeline_evidence = (
        release_evidence.get("pipeline_contract")
        if isinstance(release_evidence.get("pipeline_contract"), dict)
        else {}
    )
    engine_policy = (
        pipeline_evidence.get("integration_engine_policy")
        if isinstance(pipeline_evidence.get("integration_engine_policy"), dict)
        else {}
    )
    rows = engine_policy.get("rows")
    if not isinstance(rows, list):
        rows = []
    failed_items = engine_policy.get("failed_items")
    if not isinstance(failed_items, list):
        failed_items = []
    check_present = engine_policy.get("check_present")
    check_passed = engine_policy.get("check_passed")
    if not engine_policy:
        status = "not_available"
    else:
        status = str(engine_policy.get("status") or "not_available")
    return {
        "status": status,
        "check_name": engine_policy.get("check_name") or "integration_default_engine_policy",
        "check_present": check_present,
        "check_passed": check_passed,
        "output_count": engine_policy.get("output_count"),
        "non_resident_count": engine_policy.get("non_resident_count"),
        "resident_count": engine_policy.get("resident_count"),
        "failed_count": engine_policy.get("failed_count", len(failed_items)),
        "failed_items": failed_items,
        "rows": rows,
    }


def _acceptance_stack_engine_runtime_default_summary(
    payload: dict[str, Any],
) -> dict[str, Any]:
    release_evidence = (
        payload.get("release_contract_evidence")
        if isinstance(payload.get("release_contract_evidence"), dict)
        else {}
    )
    pipeline_evidence = (
        release_evidence.get("pipeline_contract")
        if isinstance(release_evidence.get("pipeline_contract"), dict)
        else {}
    )
    runtime_default = (
        pipeline_evidence.get("runtime_default")
        if isinstance(pipeline_evidence.get("runtime_default"), dict)
        else {}
    )
    failed_masters = runtime_default.get("failed_masters")
    if not isinstance(failed_masters, list):
        failed_masters = []
    failed_outputs = runtime_default.get("failed_outputs")
    if not isinstance(failed_outputs, list):
        failed_outputs = []
    if not runtime_default:
        status = "not_available"
    else:
        status = str(runtime_default.get("status") or "not_available")
    return {
        "status": status,
        "check_name": runtime_default.get("check_name")
        or "stack_engine_runtime_default_path",
        "check_present": runtime_default.get("check_present"),
        "check_passed": runtime_default.get("check_passed"),
        "master_count": runtime_default.get("master_count"),
        "master_stack_engine_count": runtime_default.get("master_stack_engine_count"),
        "master_resident_count": runtime_default.get("master_resident_count"),
        "legacy_master_count": runtime_default.get("legacy_master_count"),
        "integration_output_count": runtime_default.get("integration_output_count"),
        "integration_stack_engine_default_count": runtime_default.get(
            "integration_stack_engine_default_count"
        ),
        "integration_resident_count": runtime_default.get("integration_resident_count"),
        "explicit_cuda_fast_path_count": runtime_default.get(
            "explicit_cuda_fast_path_count"
        ),
        "failed_master_count": runtime_default.get(
            "failed_master_count", len(failed_masters)
        ),
        "failed_output_count": runtime_default.get(
            "failed_output_count", len(failed_outputs)
        ),
        "failed_masters": failed_masters,
        "failed_outputs": failed_outputs,
    }


def _pipeline_contract_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}

    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    failed_checks = [str(item.get("name")) for item in checks if not item.get("passed")]
    integration = payload.get("integration") if isinstance(payload.get("integration"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    pixel_verification = (
        payload.get("pixel_verification")
        if isinstance(payload.get("pixel_verification"), dict)
        else {}
    )
    rejection_sample_accounting = _rejection_sample_accounting_summary(payload)
    sample_accounting_closure = _sample_accounting_closure_summary(payload)
    resident_result_contract = _resident_result_contract_summary(payload)
    integration_engine_policy = _integration_engine_policy_summary(payload)
    runtime_default = _stack_engine_runtime_default_summary(payload)
    return {
        "path": payload.get("_path"),
        "exists": True,
        "audit_type": payload.get("audit_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "integration_output_count": len(integration.get("outputs") or []),
        "integration_map_count": len(integration.get("maps") or []),
        "integration_output_maps_available": _check_passed(
            payload,
            "integration_output_maps_available",
        ),
        "integration_dq_contract": _check_passed(payload, "integration_dq_contract"),
        "integration_stack_result_contract": _check_passed(
            payload,
            "integration_stack_result_contract",
        ),
        "integration_resident_result_contract": _check_passed(
            payload,
            "integration_resident_result_contract",
        ),
        "resident_result_contract": resident_result_contract,
        "integration_resident_result_contract_status": (
            resident_result_contract.get("status")
        ),
        "integration_resident_result_contract_check_present": (
            resident_result_contract.get("check_present")
        ),
        "integration_resident_result_contract_check_passed": (
            resident_result_contract.get("check_passed")
        ),
        "integration_resident_result_contract_required_count": (
            resident_result_contract.get("required_count")
        ),
        "integration_resident_result_contract_failed_count": (
            resident_result_contract.get("failed_count")
        ),
        "integration_resident_result_contract_failed_check_count": (
            resident_result_contract.get("failed_check_count")
        ),
        "integration_resident_result_contract_failed_checks": (
            resident_result_contract.get("failed_checks")
        ),
        "integration_resident_result_contract_failed_items": (
            resident_result_contract.get("failed_items")
        ),
        "integration_dq_map_pixels_match_summary": _check_passed(
            payload,
            "integration_dq_map_pixels_match_summary",
        ),
        "integration_coverage_map_pixels_match_dq": _check_passed(
            payload,
            "integration_coverage_map_pixels_match_dq",
        ),
        "integration_rejection_map_pixels_match_dq": _check_passed(
            payload,
            "integration_rejection_map_pixels_match_dq",
        ),
        "integration_rejection_sample_counts_match_maps": _check_passed(
            payload,
            "integration_rejection_sample_counts_match_maps",
        ),
        "integration_sample_accounting_closure": _check_passed(
            payload,
            "integration_sample_accounting_closure",
        ),
        "integration_default_engine_policy": _check_passed(
            payload,
            "integration_default_engine_policy",
        ),
        "integration_engine_policy": integration_engine_policy,
        "integration_engine_policy_status": integration_engine_policy.get("status"),
        "integration_engine_policy_check_present": integration_engine_policy.get(
            "check_present"
        ),
        "integration_engine_policy_failed_count": integration_engine_policy.get(
            "failed_count"
        ),
        "integration_engine_policy_non_resident_count": integration_engine_policy.get(
            "non_resident_count"
        ),
        "stack_engine_runtime_default": runtime_default,
        "stack_engine_runtime_default_status": runtime_default.get("status"),
        "stack_engine_runtime_default_check_present": runtime_default.get(
            "check_present"
        ),
        "stack_engine_runtime_default_check_passed": runtime_default.get(
            "check_passed"
        ),
        "stack_engine_runtime_default_legacy_master_count": runtime_default.get(
            "legacy_master_count"
        ),
        "stack_engine_runtime_default_failed_master_count": runtime_default.get(
            "failed_master_count"
        ),
        "stack_engine_runtime_default_failed_output_count": runtime_default.get(
            "failed_output_count"
        ),
        "stack_engine_runtime_default_explicit_cuda_fast_path_count": (
            runtime_default.get("explicit_cuda_fast_path_count")
        ),
        "rejection_sample_accounting": rejection_sample_accounting,
        "rejection_sample_accounting_status": rejection_sample_accounting.get("status"),
        "rejection_sample_accounting_check_present": rejection_sample_accounting.get(
            "check_present"
        ),
        "rejection_sample_accounting_failed_count": rejection_sample_accounting.get(
            "failed_count"
        ),
        "sample_accounting_closure": sample_accounting_closure,
        "sample_accounting_closure_status": sample_accounting_closure.get("status"),
        "sample_accounting_closure_check_present": sample_accounting_closure.get(
            "check_present"
        ),
        "sample_accounting_closure_present_count": sample_accounting_closure.get(
            "present_count"
        ),
        "sample_accounting_closure_failed_count": sample_accounting_closure.get(
            "failed_count"
        ),
        "pixel_verification_enabled": pixel_verification.get("enabled"),
        "pixel_verification_tile_size": pixel_verification.get("tile_size"),
        "pixel_verification_tolerance_pixels": pixel_verification.get("tolerance_pixels"),
        "calibration_master_count": calibration.get("master_count"),
        "calibrated_light_count": calibration.get("calibrated_light_count"),
        "resident_native_calibration_artifact": calibration.get(
            "resident_native_calibration_artifact"
        ),
        "resident_calibrated_light_count": calibration.get("resident_calibrated_light_count"),
    }


def _stack_engine_contract_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {
            "path": str(path),
            "exists": False,
            "status": "missing",
            "passed": False,
            "default_promotion_ready": False,
        }

    checks = [item for item in payload.get("checks") or [] if isinstance(item, dict)]
    failed_checks = [str(item.get("name")) for item in checks if not item.get("passed")]
    adoption = payload.get("adoption") if isinstance(payload.get("adoption"), dict) else {}
    default_promotion = (
        payload.get("default_promotion")
        if isinstance(payload.get("default_promotion"), dict)
        else {}
    )
    gap_surfaces = adoption.get("gap_surfaces") if isinstance(adoption.get("gap_surfaces"), list) else []
    blockers = (
        default_promotion.get("blockers")
        if isinstance(default_promotion.get("blockers"), list)
        else []
    )
    return {
        "path": payload.get("_path"),
        "exists": True,
        "audit_type": payload.get("audit_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "scope": payload.get("scope"),
        "expected_integration_engine": payload.get("expected_integration_engine"),
        "resident_calibration_contract_attached": payload.get(
            "resident_calibration_contract_attached"
        ),
        "resident_result_contract_attached": payload.get("resident_result_contract_attached"),
        "check_count": len(checks),
        "failed_check_count": len(failed_checks),
        "failed_checks": failed_checks,
        "adoption_target_engine": adoption.get("target_engine"),
        "adoption_surface_count": adoption.get("surface_count"),
        "adoption_stack_engine_surface_count": adoption.get("stack_engine_surface_count"),
        "adoption_cuda_resident_surface_count": adoption.get("cuda_resident_surface_count"),
        "adoption_contract_ready_count": adoption.get("contract_ready_count"),
        "adoption_result_contract_passed_count": adoption.get(
            "result_contract_passed_count"
        ),
        "adoption_fallback_count": adoption.get("fallback_count"),
        "adoption_phase2_stack_engine_default_gap_count": adoption.get(
            "phase2_stack_engine_default_gap_count"
        ),
        "adoption_recommendation": adoption.get("recommendation"),
        "adoption_gap_surfaces": gap_surfaces,
        "default_promotion_ready": default_promotion.get("ready"),
        "default_promotion_status": default_promotion.get("status"),
        "default_promotion_required_scope": default_promotion.get("required_scope"),
        "default_promotion_actual_scope": default_promotion.get("actual_scope"),
        "default_promotion_surface_count": default_promotion.get("surface_count"),
        "default_promotion_calibration_surface_count": default_promotion.get(
            "calibration_surface_count"
        ),
        "default_promotion_integration_surface_count": default_promotion.get(
            "integration_surface_count"
        ),
        "default_promotion_phase2_stack_engine_default_gap_count": (
            default_promotion.get("phase2_stack_engine_default_gap_count")
        ),
        "default_promotion_recommendation": default_promotion.get("recommendation"),
        "default_promotion_blocker_count": default_promotion.get(
            "blocker_count",
            len(blockers),
        ),
        "default_promotion_blockers": blockers,
    }


def _release_decision_summary(path: str | Path | None) -> dict[str, Any] | None:
    payload = _read_json_optional(path)
    if payload is None:
        return None
    if not payload.get("_exists", payload.get("exists", False)):
        return {"path": str(path), "exists": False, "status": "missing", "passed": False}

    runtime_repeat = (
        payload.get("runtime_repeat")
        if isinstance(payload.get("runtime_repeat"), dict)
        else {}
    )
    pipeline_handoff = (
        payload.get("pipeline_handoff")
        if isinstance(payload.get("pipeline_handoff"), dict)
        else {}
    )
    warp_quality_handoff = (
        payload.get("warp_quality_handoff")
        if isinstance(payload.get("warp_quality_handoff"), dict)
        else {}
    )
    resident_fastpath_handoff = (
        payload.get("resident_registration_fastpath_handoff")
        if isinstance(payload.get("resident_registration_fastpath_handoff"), dict)
        else {}
    )
    speedup = payload.get("speedup") if isinstance(payload.get("speedup"), dict) else {}
    return {
        "path": payload.get("_path"),
        "exists": True,
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "release_candidate_ready": payload.get("release_candidate_ready"),
        "default_change_ready": payload.get("default_change_ready"),
        "recommendation": payload.get("recommendation"),
        "speedup_actual": speedup.get("actual"),
        "speedup_required_min": speedup.get("required_min"),
        "runtime_repeat_present": runtime_repeat.get("present"),
        "runtime_repeat_run_count": runtime_repeat.get("run_count"),
        "runtime_repeat_considered_run_count": runtime_repeat.get("considered_run_count"),
        "runtime_repeat_best_label": runtime_repeat.get("best_label"),
        "runtime_repeat_best_elapsed_s": runtime_repeat.get("best_elapsed_s"),
        "runtime_repeat_slowest_elapsed_s": runtime_repeat.get("slowest_elapsed_s"),
        "runtime_repeat_elapsed_ratio_vs_best": runtime_repeat.get("elapsed_ratio_vs_best"),
        "runtime_repeat_max_elapsed_ratio_vs_best": runtime_repeat.get(
            "max_elapsed_ratio_vs_best"
        ),
        "runtime_repeat_recommendation": runtime_repeat.get("recommendation"),
        "pipeline_handoff_source": pipeline_handoff.get("source"),
        "pipeline_handoff_status": pipeline_handoff.get("status"),
        "pipeline_handoff_passed": pipeline_handoff.get("passed"),
        "pipeline_handoff_pixel_verification_enabled": pipeline_handoff.get(
            "pixel_verification_enabled"
        ),
        "warp_quality_handoff": warp_quality_handoff or None,
        "warp_quality_handoff_present": warp_quality_handoff.get("present"),
        "warp_quality_handoff_status": warp_quality_handoff.get("status"),
        "warp_quality_handoff_ready": warp_quality_handoff.get("ready"),
        "warp_quality_handoff_contract_passed": warp_quality_handoff.get(
            "contract_passed"
        ),
        "warp_quality_handoff_output_count": warp_quality_handoff.get("output_count"),
        "warp_quality_handoff_failed_checks": warp_quality_handoff.get("failed_checks")
        or [],
        "warp_quality_handoff_failed_acceptance_checks": (
            warp_quality_handoff.get("failed_acceptance_checks") or []
        ),
        "warp_quality_handoff_path": warp_quality_handoff.get("path"),
        "resident_registration_fastpath_handoff": resident_fastpath_handoff or None,
        "resident_registration_fastpath_handoff_present": (
            resident_fastpath_handoff.get("present")
        ),
        "resident_registration_fastpath_handoff_status": (
            resident_fastpath_handoff.get("status")
        ),
        "resident_registration_fastpath_handoff_ready": (
            resident_fastpath_handoff.get("ready")
        ),
        "resident_registration_fastpath_handoff_required": (
            resident_fastpath_handoff.get("required_by_benchmark_contract")
        ),
        "resident_registration_fastpath_handoff_source": (
            resident_fastpath_handoff.get("source")
        ),
        "resident_registration_fastpath_handoff_path": (
            resident_fastpath_handoff.get("path")
        ),
        "resident_registration_fastpath_handoff_mode": (
            resident_fastpath_handoff.get("resident_registration_mode")
        ),
        "resident_registration_fastpath_handoff_descriptor_fit_batch_mode": (
            resident_fastpath_handoff.get("descriptor_fit_batch_mode")
        ),
        "resident_registration_fastpath_handoff_pixel_refine_batch_mode": (
            resident_fastpath_handoff.get("pixel_refine_batch_mode")
        ),
        "resident_registration_fastpath_handoff_triangle_warp_batch_mode": (
            resident_fastpath_handoff.get("triangle_warp_batch_mode")
        ),
        "resident_registration_fastpath_handoff_triangle_warp_batch_frame_count": (
            resident_fastpath_handoff.get("triangle_warp_batch_frame_count")
        ),
        "resident_registration_fastpath_handoff_warp_copy_mode": (
            resident_fastpath_handoff.get("warp_copy_mode")
        ),
        "resident_registration_fastpath_handoff_passed_check_count": (
            resident_fastpath_handoff.get("passed_check_count")
        ),
        "resident_registration_fastpath_handoff_failed_check_count": (
            resident_fastpath_handoff.get("failed_check_count")
        ),
        "resident_registration_fastpath_handoff_failed_checks": (
            resident_fastpath_handoff.get("failed_checks") or []
        ),
        "resident_registration_fastpath_handoff_failed_acceptance_checks": (
            resident_fastpath_handoff.get("failed_acceptance_checks") or []
        ),
    }


def _default_change_is_ready(decision: dict[str, Any] | None) -> bool:
    if not isinstance(decision, dict):
        return False
    return (
        decision.get("default_change_ready") is True
        and decision.get("recommendation") == "promote_default_candidate"
    )


def _runtime_repeat_closure(decision: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(decision, dict):
        return {
            "required": False,
            "ready": True,
            "status": "not_supplied",
            "reason": "release decision was not supplied",
        }
    required = _default_change_is_ready(decision)
    present = decision.get("runtime_repeat_present") is True
    run_count = _int_or_zero(decision.get("runtime_repeat_run_count"))
    considered_run_count = _int_or_zero(decision.get("runtime_repeat_considered_run_count"))
    ratio = _float_or_none(decision.get("runtime_repeat_elapsed_ratio_vs_best"))
    max_ratio = _float_or_none(decision.get("runtime_repeat_max_elapsed_ratio_vs_best"))
    if not required:
        return {
            "required": False,
            "ready": True,
            "status": "not_required",
            "reason": "release decision is not ready for a default change",
            "present": present,
            "run_count": run_count,
            "considered_run_count": considered_run_count,
            "elapsed_ratio_vs_best": ratio,
            "max_elapsed_ratio_vs_best": max_ratio,
            "recommendation": decision.get("runtime_repeat_recommendation"),
        }
    ready = (
        present
        and run_count >= 2
        and considered_run_count >= 2
        and ratio is not None
        and max_ratio is not None
        and ratio <= max_ratio
    )
    if ready:
        status = "passed"
        reason = "stable repeat-runtime evidence supports the default change"
    else:
        status = "failed"
        reason = "default-change decision lacks sufficient stable repeat-runtime evidence"
    return {
        "required": True,
        "ready": ready,
        "status": status,
        "reason": reason,
        "present": present,
        "run_count": run_count,
        "considered_run_count": considered_run_count,
        "elapsed_ratio_vs_best": ratio,
        "max_elapsed_ratio_vs_best": max_ratio,
        "recommendation": decision.get("runtime_repeat_recommendation"),
    }


def _resident_fastpath_contract_passed(acceptance: dict[str, Any] | None) -> bool:
    if not isinstance(acceptance, dict):
        return False
    return (
        acceptance.get("resident_registration_fastpath_contract_status") == "passed"
        and int(acceptance.get("resident_registration_fastpath_contract_check_count") or 0) > 0
    )


def _stack_engine_default_contract_ready(contract: dict[str, Any] | None) -> bool:
    if not isinstance(contract, dict):
        return False
    adoption_gap_count = int(contract.get("adoption_phase2_stack_engine_default_gap_count") or 0)
    promotion_gap_count = int(
        contract.get("default_promotion_phase2_stack_engine_default_gap_count") or 0
    )
    return (
        contract.get("audit_type") == "stack_engine_default_contract"
        and contract.get("status") == "passed"
        and contract.get("passed") is True
        and contract.get("default_promotion_ready") is True
        and contract.get("default_promotion_status") == "ready"
        and contract.get("adoption_recommendation") == "stack_engine_default_ready"
        and contract.get("default_promotion_recommendation") == "stack_engine_default_ready"
        and adoption_gap_count == 0
        and promotion_gap_count == 0
        and int(contract.get("default_promotion_blocker_count") or 0) == 0
    )


def build_phase2_status(
    *,
    checkpoint_dir: str | Path,
    acceptance_audit: str | Path | None = None,
    default_route_acceptance_audit: str | Path | None = None,
    release_manifest: str | Path | None = None,
    github_release_plan: str | Path | None = None,
    publish_preflight: str | Path | None = None,
    stack_engine_publication_audit: str | Path | None = None,
    pipeline_contract: str | Path | None = None,
    stack_engine_contract: str | Path | None = None,
    registration_results: str | Path | None = None,
    quality_results: str | Path | None = None,
    quality_metrics_compare: str | Path | None = None,
    resident_winsorized_benchmark_audit: str | Path | None = None,
    resident_winsorized_sweep_audit: str | Path | None = None,
    release_decision: str | Path | None = None,
    doctor_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint = _latest_checkpoint(checkpoint_dir)
    acceptance = _acceptance_summary(acceptance_audit)
    default_route_acceptance = _default_route_acceptance_summary(default_route_acceptance_audit)
    doctor = _doctor_summary(doctor_payload)
    release = _release_manifest_summary(release_manifest)
    github_plan = _github_release_plan_summary(github_release_plan)
    preflight = _publish_preflight_summary(publish_preflight)
    publication_audit = _stack_engine_publication_audit_summary(
        stack_engine_publication_audit
    )
    pipeline = _pipeline_contract_summary(pipeline_contract)
    stack_engine = _stack_engine_contract_summary(stack_engine_contract)
    registration_admission = _registration_admission_summary(registration_results)
    quality_saturation = _quality_saturation_summary(quality_results)
    quality_metrics = _quality_metric_summary(quality_results)
    quality_compare = _quality_metrics_compare_summary(quality_metrics_compare)
    winsorized_audit = _resident_winsorized_benchmark_audit_summary(
        resident_winsorized_benchmark_audit
    )
    winsorized_sweep_audit = _resident_winsorized_sweep_audit_summary(
        resident_winsorized_sweep_audit
    )
    decision = _release_decision_summary(release_decision)
    runtime_repeat_closure = _runtime_repeat_closure(decision)
    checks = [
        {
            "name": "latest_checkpoint_green",
            "passed": bool(checkpoint.get("green")),
            "evidence": {"gate": checkpoint.get("gate"), "status": checkpoint.get("status")},
        }
    ]
    if acceptance is not None:
        checks.append(
            {
                "name": "acceptance_audit_passed",
                "passed": acceptance.get("passed") is True,
                "evidence": {
                    "status": acceptance.get("status"),
                    "speedup_vs_reference": acceptance.get("speedup_vs_reference"),
                },
            }
        )
        checks.append(
            {
                "name": "acceptance_pipeline_integration_engine_policy_passed",
                "passed": (
                    acceptance.get("pipeline_integration_engine_policy_status") == "passed"
                    and acceptance.get("pipeline_integration_engine_policy_check_present") is True
                    and acceptance.get("pipeline_integration_engine_policy_check_passed") is True
                ),
                "evidence": {
                    "status": acceptance.get("pipeline_integration_engine_policy_status"),
                    "check_present": acceptance.get(
                        "pipeline_integration_engine_policy_check_present"
                    ),
                    "check_passed": acceptance.get(
                        "pipeline_integration_engine_policy_check_passed"
                    ),
                    "non_resident_count": acceptance.get(
                        "pipeline_integration_engine_policy_non_resident_count"
                    ),
                    "failed_count": acceptance.get(
                        "pipeline_integration_engine_policy_failed_count"
                    ),
                },
            }
        )
        checks.append(
            {
                "name": "acceptance_pipeline_stack_engine_runtime_default_passed",
                "passed": (
                    acceptance.get("pipeline_stack_engine_runtime_default_status")
                    == "passed"
                    and acceptance.get(
                        "pipeline_stack_engine_runtime_default_check_present"
                    )
                    is True
                    and acceptance.get(
                        "pipeline_stack_engine_runtime_default_check_passed"
                    )
                    is True
                    and _int_or_zero(
                        acceptance.get(
                            "pipeline_stack_engine_runtime_default_legacy_master_count"
                        )
                    )
                    == 0
                    and _int_or_zero(
                        acceptance.get(
                            "pipeline_stack_engine_runtime_default_failed_master_count"
                        )
                    )
                    == 0
                    and _int_or_zero(
                        acceptance.get(
                            "pipeline_stack_engine_runtime_default_failed_output_count"
                        )
                    )
                    == 0
                ),
                "evidence": {
                    "status": acceptance.get(
                        "pipeline_stack_engine_runtime_default_status"
                    ),
                    "check_present": acceptance.get(
                        "pipeline_stack_engine_runtime_default_check_present"
                    ),
                    "check_passed": acceptance.get(
                        "pipeline_stack_engine_runtime_default_check_passed"
                    ),
                    "master_count": acceptance.get(
                        "pipeline_stack_engine_runtime_default_master_count"
                    ),
                    "legacy_master_count": acceptance.get(
                        "pipeline_stack_engine_runtime_default_legacy_master_count"
                    ),
                    "failed_master_count": acceptance.get(
                        "pipeline_stack_engine_runtime_default_failed_master_count"
                    ),
                    "failed_output_count": acceptance.get(
                        "pipeline_stack_engine_runtime_default_failed_output_count"
                    ),
                    "explicit_cuda_fast_path_count": acceptance.get(
                        "pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count"
                    ),
                },
            }
        )
        if acceptance.get("warp_quality_contract_status") is not None:
            checks.append(
                {
                    "name": "acceptance_warp_quality_contract_passed",
                    "passed": (
                        acceptance.get("warp_quality_contract_status") == "passed"
                        and acceptance.get("warp_quality_contract_passed") is True
                    ),
                    "evidence": {
                        "status": acceptance.get("warp_quality_contract_status"),
                        "passed": acceptance.get("warp_quality_contract_passed"),
                        "output_count": acceptance.get(
                            "warp_quality_contract_output_count"
                        ),
                        "failed_checks": acceptance.get(
                            "warp_quality_contract_failed_checks"
                        ),
                        "path": acceptance.get("warp_quality_contract_path"),
                    },
                }
            )
    if default_route_acceptance is not None:
        checks.append(
            {
                "name": "default_route_acceptance_passed",
                "passed": default_route_acceptance.get("passed") is True,
                "evidence": {
                    "status": default_route_acceptance.get("status"),
                    "acceptance_passed": default_route_acceptance.get("acceptance_passed"),
                    "speedup_vs_reference": default_route_acceptance.get("speedup_vs_reference"),
                },
            }
        )
        checks.append(
            {
                "name": "default_route_acceptance_route_contract_passed",
                "passed": default_route_acceptance.get("route_contract_passed") is True,
                "evidence": {
                    "route_check_count": default_route_acceptance.get("route_check_count"),
                    "route_failed_checks": default_route_acceptance.get("route_failed_checks"),
                },
            }
        )
    if doctor is not None:
        checks.append(
            {
                "name": "cuda_doctor_available",
                "passed": doctor.get("cuda_available") is True,
                "evidence": {
                    "cuda_available": doctor.get("cuda_available"),
                    "primary_gpu": doctor.get("primary_gpu"),
                },
            }
        )
    if registration_admission is not None:
        checks.append(
            {
                "name": "registration_reference_admission_not_blocked",
                "passed": registration_admission.get("passed") is True,
                "evidence": {
                    "status": registration_admission.get("status"),
                    "blocked": registration_admission.get("blocked"),
                    "reference_frame_id": registration_admission.get("reference_frame_id"),
                    "quality_gate_status": registration_admission.get("quality_gate_status"),
                    "quality_gate_enforced": registration_admission.get("quality_gate_enforced"),
                    "reference_selection_fallback": registration_admission.get(
                        "reference_selection_fallback"
                    ),
                    "allow_quality_rejected_reference": registration_admission.get(
                        "allow_quality_rejected_reference"
                    ),
                    "reason": registration_admission.get("reason"),
                    "quality_reference_admission_row_count": registration_admission.get(
                        "quality_reference_admission_row_count"
                    ),
                    "path": registration_admission.get("path"),
                },
            }
        )
    if quality_saturation is not None:
        checks.append(
            {
                "name": "quality_saturation_no_rejections",
                "passed": quality_saturation.get("passed") is True,
                "evidence": {
                    "status": quality_saturation.get("status"),
                    "frame_count": quality_saturation.get("frame_count"),
                    "saturated_frame_count": quality_saturation.get("saturated_frame_count"),
                    "quality_gate_saturation_rejected_count": quality_saturation.get(
                        "quality_gate_saturation_rejected_count"
                    ),
                    "max_saturation_fraction": quality_saturation.get(
                        "max_saturation_fraction"
                    ),
                    "max_saturation_fraction_policy": quality_saturation.get(
                        "max_saturation_fraction_policy"
                    ),
                    "worst_frame_id": quality_saturation.get("worst_frame_id"),
                    "rejected_frame_ids": quality_saturation.get("rejected_frame_ids"),
                    "path": quality_saturation.get("path"),
                },
            }
        )
    if quality_metrics is not None:
        checks.append(
            {
                "name": "quality_metric_summary_available",
                "passed": quality_metrics.get("passed") is True,
                "evidence": {
                    "status": quality_metrics.get("status"),
                    "frame_count": quality_metrics.get("frame_count"),
                    "metric_count": quality_metrics.get("metric_count"),
                    "metrics": quality_metrics.get("metrics"),
                    "path": quality_metrics.get("path"),
                },
            }
        )
    if quality_compare is not None:
        checks.append(
            {
                "name": "quality_metrics_compare_passed",
                "passed": quality_compare.get("passed") is True,
                "evidence": {
                    "status": quality_compare.get("status"),
                    "check_count": quality_compare.get("check_count"),
                    "failed_check_count": quality_compare.get("failed_check_count"),
                    "failed_checks": quality_compare.get("failed_checks"),
                    "baseline_metric_count": quality_compare.get("baseline_metric_count"),
                    "candidate_metric_count": quality_compare.get("candidate_metric_count"),
                    "threshold_failure_count": quality_compare.get("threshold_failure_count"),
                    "path": quality_compare.get("path"),
                },
            }
        )
    if release is not None:
        checks.append(
            {
                "name": "release_manifest_ready",
                "passed": release.get("status") == "release_manifest_ready",
                "evidence": {
                    "status": release.get("status"),
                    "package_count": release.get("package_count"),
                },
            }
        )
    if github_plan is not None:
        checks.append(
            {
                "name": "github_release_plan_ready",
                "passed": github_plan.get("status") == "release_plan_ready",
                "evidence": {
                    "status": github_plan.get("status"),
                    "publication_ready": github_plan.get("publication_ready"),
                    "gh_auth_ok": github_plan.get("gh_auth_ok"),
                },
            }
        )
    if preflight is not None:
        checks.append(
            {
                "name": "windows_publish_preflight_ready",
                "passed": preflight.get("status") == "publish_preflight_ready"
                and preflight.get("passed") is True,
                "evidence": {
                    "status": preflight.get("status"),
                    "passed": preflight.get("passed"),
                    "asset_count": preflight.get("asset_count"),
                    "package_count": preflight.get("package_count"),
                    "primary_package": preflight.get("primary_package"),
                    "default_route_check_count": preflight.get("default_route_check_count"),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_rejection_sample_accounting_passed",
                "passed": (
                    preflight.get("github_plan_phase2_rejection_sample_accounting_passed")
                    is True
                    and preflight.get(
                        "github_plan_matrix_rejection_sample_accounting_passed"
                    )
                    is True
                    and preflight.get("matrix_rejection_sample_accounting_passed") is True
                    and preflight.get(
                        "default_promotion_rejection_sample_accounting_passed"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_rejection_accounting_matches_matrix"
                    )
                    is True
                ),
                "evidence": {
                    "phase2_status": preflight.get(
                        "github_plan_phase2_rejection_sample_accounting_status"
                    ),
                    "plan_matrix_status": preflight.get(
                        "github_plan_matrix_rejection_sample_accounting_status"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_rejection_sample_accounting_status"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_rejection_sample_accounting_status"
                    ),
                    "phase2_check": preflight.get(
                        "github_plan_phase2_rejection_sample_accounting_passed"
                    ),
                    "plan_matrix_check": preflight.get(
                        "github_plan_matrix_rejection_sample_accounting_passed"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_rejection_sample_accounting_passed"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_rejection_sample_accounting_passed"
                    ),
                    "matrix_match_check": preflight.get(
                        "github_plan_matrix_rejection_accounting_matches_matrix"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_sample_accounting_closure_passed",
                "passed": (
                    preflight.get("github_plan_phase2_sample_accounting_closure_passed")
                    is True
                    and preflight.get(
                        "github_plan_matrix_sample_accounting_closure_passed"
                    )
                    is True
                    and preflight.get("matrix_sample_accounting_closure_passed") is True
                    and preflight.get(
                        "default_promotion_sample_accounting_closure_passed"
                    )
                    is True
                    and preflight.get("github_plan_matrix_sample_closure_matches_matrix")
                    is True
                ),
                "evidence": {
                    "phase2_status": preflight.get(
                        "github_plan_phase2_sample_accounting_closure_status"
                    ),
                    "plan_matrix_status": preflight.get(
                        "github_plan_matrix_sample_accounting_closure_status"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_sample_accounting_closure_status"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_sample_accounting_closure_status"
                    ),
                    "phase2_check": preflight.get(
                        "github_plan_phase2_sample_accounting_closure_passed"
                    ),
                    "plan_matrix_check": preflight.get(
                        "github_plan_matrix_sample_accounting_closure_passed"
                    ),
                    "matrix_check": preflight.get("matrix_sample_accounting_closure_passed"),
                    "default_promotion_check": preflight.get(
                        "default_promotion_sample_accounting_closure_passed"
                    ),
                    "matrix_match_check": preflight.get(
                        "github_plan_matrix_sample_closure_matches_matrix"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_integration_engine_policy_passed",
                "passed": (
                    preflight.get(
                        "windows_release_matrix_acceptance_integration_engine_policy_passed"
                    )
                    is True
                    and preflight.get(
                        "windows_release_matrix_pipeline_integration_engine_policy_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_acceptance_integration_engine_policy_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_pipeline_integration_engine_policy_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_integration_engine_policy_matches_default_promotion"
                    )
                    is True
                    and preflight.get("matrix_integration_engine_policy_ready") is True
                    and preflight.get("default_promotion_integration_engine_policy_ready")
                    is True
                    and preflight.get(
                        "matrix_acceptance_integration_engine_policy_status"
                    )
                    == "passed"
                    and preflight.get("matrix_pipeline_integration_engine_policy_status")
                    == "passed"
                    and preflight.get(
                        "default_promotion_acceptance_integration_engine_policy_status"
                    )
                    == "passed"
                    and preflight.get(
                        "default_promotion_pipeline_integration_engine_policy_status"
                    )
                    == "passed"
                ),
                "evidence": {
                    "matrix_ready": preflight.get(
                        "matrix_integration_engine_policy_ready"
                    ),
                    "matrix_acceptance_status": preflight.get(
                        "matrix_acceptance_integration_engine_policy_status"
                    ),
                    "matrix_pipeline_status": preflight.get(
                        "matrix_pipeline_integration_engine_policy_status"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_integration_engine_policy_ready"
                    ),
                    "default_promotion_acceptance_status": preflight.get(
                        "default_promotion_acceptance_integration_engine_policy_status"
                    ),
                    "default_promotion_pipeline_status": preflight.get(
                        "default_promotion_pipeline_integration_engine_policy_status"
                    ),
                    "matrix_acceptance_check": preflight.get(
                        "windows_release_matrix_acceptance_integration_engine_policy_passed"
                    ),
                    "matrix_pipeline_check": preflight.get(
                        "windows_release_matrix_pipeline_integration_engine_policy_passed"
                    ),
                    "default_promotion_acceptance_check": preflight.get(
                        "default_promotion_acceptance_integration_engine_policy_passed"
                    ),
                    "default_promotion_pipeline_check": preflight.get(
                        "default_promotion_pipeline_integration_engine_policy_passed"
                    ),
                    "agreement_check": preflight.get(
                        "matrix_integration_engine_policy_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_stack_engine_default_contract_ready",
                "passed": (
                    preflight.get(
                        "github_plan_phase2_stack_engine_default_contract_ready"
                    )
                    is True
                    and preflight.get("github_plan_matrix_stack_engine_contract_ready")
                    is True
                    and preflight.get(
                        "github_plan_stack_engine_contract_agreement_passed"
                    )
                    is True
                    and preflight.get("matrix_stack_engine_contract_ready") is True
                    and preflight.get("default_promotion_stack_engine_contract_ready")
                    is True
                    and preflight.get(
                        "github_plan_matrix_stack_engine_contract_matches_matrix"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_contract_matches_default_promotion"
                    )
                    is True
                ),
                "evidence": {
                    "phase2_status": preflight.get(
                        "github_plan_phase2_stack_engine_contract_status"
                    ),
                    "plan_matrix_status": preflight.get(
                        "github_plan_matrix_stack_engine_contract_status"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_stack_engine_contract_status"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_stack_engine_contract_status"
                    ),
                    "matrix_default_gap_count": preflight.get(
                        "matrix_stack_engine_contract_default_gap_count"
                    ),
                    "default_promotion_default_gap_count": preflight.get(
                        "default_promotion_stack_engine_contract_default_gap_count"
                    ),
                    "phase2_check": preflight.get(
                        "github_plan_phase2_stack_engine_default_contract_ready"
                    ),
                    "plan_matrix_check": preflight.get(
                        "github_plan_matrix_stack_engine_contract_ready"
                    ),
                    "agreement_check": preflight.get(
                        "github_plan_stack_engine_contract_agreement_passed"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_stack_engine_contract_ready"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_stack_engine_contract_ready"
                    ),
                    "plan_matrix_match_check": preflight.get(
                        "github_plan_matrix_stack_engine_contract_matches_matrix"
                    ),
                    "default_promotion_match_check": preflight.get(
                        "matrix_stack_engine_contract_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_stack_engine_runtime_default_passed",
                "passed": (
                    preflight.get(
                        "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
                    )
                    is True
                    and preflight.get(
                        "windows_release_matrix_pipeline_stack_engine_runtime_default_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_acceptance_stack_engine_runtime_default_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_pipeline_stack_engine_runtime_default_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_runtime_default_matches_default_promotion"
                    )
                    is True
                    and preflight.get("matrix_stack_engine_runtime_default_ready")
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_runtime_default_ready"
                    )
                    is True
                    and preflight.get(
                        "matrix_acceptance_stack_engine_runtime_default_status"
                    )
                    == "passed"
                    and preflight.get(
                        "matrix_pipeline_stack_engine_runtime_default_status"
                    )
                    == "passed"
                    and preflight.get(
                        "default_promotion_acceptance_stack_engine_runtime_default_status"
                    )
                    == "passed"
                    and preflight.get(
                        "default_promotion_pipeline_stack_engine_runtime_default_status"
                    )
                    == "passed"
                    and _int_or_zero(
                        preflight.get(
                            "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
                        )
                    )
                    == 0
                    and _int_or_zero(
                        preflight.get(
                            "matrix_stack_engine_runtime_default_pipeline_failed_output_count"
                        )
                    )
                    == 0
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count"
                        )
                    )
                    == 0
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count"
                        )
                    )
                    == 0
                ),
                "evidence": {
                    "matrix_ready": preflight.get(
                        "matrix_stack_engine_runtime_default_ready"
                    ),
                    "matrix_acceptance_status": preflight.get(
                        "matrix_acceptance_stack_engine_runtime_default_status"
                    ),
                    "matrix_pipeline_status": preflight.get(
                        "matrix_pipeline_stack_engine_runtime_default_status"
                    ),
                    "matrix_acceptance_legacy_master_count": preflight.get(
                        "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
                    ),
                    "matrix_pipeline_failed_output_count": preflight.get(
                        "matrix_stack_engine_runtime_default_pipeline_failed_output_count"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_stack_engine_runtime_default_ready"
                    ),
                    "default_promotion_acceptance_status": preflight.get(
                        "default_promotion_acceptance_stack_engine_runtime_default_status"
                    ),
                    "default_promotion_pipeline_status": preflight.get(
                        "default_promotion_pipeline_stack_engine_runtime_default_status"
                    ),
                    "default_promotion_acceptance_legacy_master_count": (
                        preflight.get(
                            "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count"
                        )
                    ),
                    "default_promotion_pipeline_failed_output_count": (
                        preflight.get(
                            "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count"
                        )
                    ),
                    "matrix_acceptance_check": preflight.get(
                        "windows_release_matrix_acceptance_stack_engine_runtime_default_passed"
                    ),
                    "matrix_pipeline_check": preflight.get(
                        "windows_release_matrix_pipeline_stack_engine_runtime_default_passed"
                    ),
                    "default_promotion_acceptance_check": preflight.get(
                        "default_promotion_acceptance_stack_engine_runtime_default_passed"
                    ),
                    "default_promotion_pipeline_check": preflight.get(
                        "default_promotion_pipeline_stack_engine_runtime_default_passed"
                    ),
                    "agreement_check": preflight.get(
                        "matrix_stack_engine_runtime_default_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_direct_runtime_evidence_passed",
                "passed": (
                    preflight.get("windows_release_matrix_direct_acceptance_fastpath_evidence")
                    is True
                    and preflight.get("windows_release_matrix_direct_pipeline_calibration_evidence")
                    is True
                    and preflight.get("default_promotion_direct_acceptance_fastpath_evidence")
                    is True
                    and preflight.get("default_promotion_direct_pipeline_calibration_evidence")
                    is True
                    and preflight.get("matrix_direct_runtime_evidence_matches_default_promotion")
                    is True
                    and preflight.get("matrix_direct_runtime_evidence_ready") is True
                    and preflight.get("default_promotion_direct_runtime_evidence_ready")
                    is True
                    and preflight.get("matrix_direct_runtime_acceptance_source")
                    == "explicit_resident_artifacts_json"
                    and preflight.get("default_promotion_direct_runtime_acceptance_source")
                    == "explicit_resident_artifacts_json"
                    and _int_or_zero(
                        preflight.get("matrix_direct_runtime_acceptance_check_count")
                    )
                    > 0
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_direct_runtime_acceptance_check_count"
                        )
                    )
                    > 0
                    and preflight.get(
                        "matrix_direct_runtime_pipeline_calibration_source"
                    )
                    == "resident_artifacts_json_fallback"
                    and preflight.get(
                        "default_promotion_direct_runtime_pipeline_calibration_source"
                    )
                    == "resident_artifacts_json_fallback"
                    and _int_or_zero(
                        preflight.get(
                            "matrix_direct_runtime_pipeline_resident_lights"
                        )
                    )
                    >= 200
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_direct_runtime_pipeline_resident_lights"
                        )
                    )
                    >= 200
                ),
                "evidence": {
                    "matrix_ready": preflight.get(
                        "matrix_direct_runtime_evidence_ready"
                    ),
                    "matrix_acceptance_source": preflight.get(
                        "matrix_direct_runtime_acceptance_source"
                    ),
                    "matrix_acceptance_check_count": preflight.get(
                        "matrix_direct_runtime_acceptance_check_count"
                    ),
                    "matrix_pipeline_calibration_source": preflight.get(
                        "matrix_direct_runtime_pipeline_calibration_source"
                    ),
                    "matrix_pipeline_resident_lights": preflight.get(
                        "matrix_direct_runtime_pipeline_resident_lights"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_direct_runtime_evidence_ready"
                    ),
                    "default_promotion_acceptance_source": preflight.get(
                        "default_promotion_direct_runtime_acceptance_source"
                    ),
                    "default_promotion_acceptance_check_count": preflight.get(
                        "default_promotion_direct_runtime_acceptance_check_count"
                    ),
                    "default_promotion_pipeline_calibration_source": preflight.get(
                        "default_promotion_direct_runtime_pipeline_calibration_source"
                    ),
                    "default_promotion_pipeline_resident_lights": preflight.get(
                        "default_promotion_direct_runtime_pipeline_resident_lights"
                    ),
                    "matrix_acceptance_check": preflight.get(
                        "windows_release_matrix_direct_acceptance_fastpath_evidence"
                    ),
                    "matrix_pipeline_check": preflight.get(
                        "windows_release_matrix_direct_pipeline_calibration_evidence"
                    ),
                    "default_promotion_acceptance_check": preflight.get(
                        "default_promotion_direct_acceptance_fastpath_evidence"
                    ),
                    "default_promotion_pipeline_check": preflight.get(
                        "default_promotion_direct_pipeline_calibration_evidence"
                    ),
                    "agreement_check": preflight.get(
                        "matrix_direct_runtime_evidence_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_release_direct_publication_guard_passed",
                "passed": (
                    preflight.get(
                        "github_plan_matrix_release_decision_direct_publication_guard_passed"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix"
                    )
                    is True
                    and preflight.get(
                        "matrix_release_decision_direct_runtime_publication_guard_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_release_decision_direct_runtime_publication_guard_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_release_decision_direct_publication_guard_matches_default_promotion"
                    )
                    is True
                    and preflight.get(
                        "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_release_direct_publication_guard_ready"
                    )
                    is True
                    and _int_or_zero(
                        preflight.get(
                            "github_plan_matrix_release_direct_publication_guard_lights"
                        )
                    )
                    >= 200
                    and preflight.get(
                        "github_plan_matrix_default_promotion_release_direct_publication_guard_ready"
                    )
                    is True
                    and _int_or_zero(
                        preflight.get(
                            "github_plan_matrix_default_promotion_release_direct_publication_guard_lights"
                        )
                    )
                    >= 200
                    and preflight.get(
                        "matrix_release_direct_publication_guard_ready"
                    )
                    is True
                    and preflight.get(
                        "matrix_release_direct_publication_guard_source_ready"
                    )
                    is True
                    and preflight.get(
                        "matrix_release_direct_publication_guard_count_ready"
                    )
                    is True
                    and preflight.get(
                        "matrix_release_direct_publication_guard_check_passed"
                    )
                    is True
                    and _int_or_zero(
                        preflight.get("matrix_release_direct_publication_guard_lights")
                    )
                    >= 200
                    and preflight.get(
                        "matrix_default_promotion_release_direct_publication_guard_ready"
                    )
                    is True
                    and _int_or_zero(
                        preflight.get(
                            "matrix_default_promotion_release_direct_publication_guard_lights"
                        )
                    )
                    >= 200
                    and preflight.get(
                        "default_promotion_release_direct_publication_guard_ready"
                    )
                    is True
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_release_direct_publication_guard_lights"
                        )
                    )
                    >= 200
                ),
                "evidence": {
                    "github_plan_matrix_ready": preflight.get(
                        "github_plan_matrix_release_direct_publication_guard_ready"
                    ),
                    "github_plan_matrix_lights": preflight.get(
                        "github_plan_matrix_release_direct_publication_guard_lights"
                    ),
                    "github_plan_default_promotion_ready": preflight.get(
                        "github_plan_matrix_default_promotion_release_direct_publication_guard_ready"
                    ),
                    "github_plan_default_promotion_lights": preflight.get(
                        "github_plan_matrix_default_promotion_release_direct_publication_guard_lights"
                    ),
                    "matrix_ready": preflight.get(
                        "matrix_release_direct_publication_guard_ready"
                    ),
                    "matrix_source_ready": preflight.get(
                        "matrix_release_direct_publication_guard_source_ready"
                    ),
                    "matrix_count_ready": preflight.get(
                        "matrix_release_direct_publication_guard_count_ready"
                    ),
                    "matrix_check_passed": preflight.get(
                        "matrix_release_direct_publication_guard_check_passed"
                    ),
                    "matrix_lights": preflight.get(
                        "matrix_release_direct_publication_guard_lights"
                    ),
                    "matrix_default_promotion_ready": preflight.get(
                        "matrix_default_promotion_release_direct_publication_guard_ready"
                    ),
                    "matrix_default_promotion_lights": preflight.get(
                        "matrix_default_promotion_release_direct_publication_guard_lights"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_release_direct_publication_guard_ready"
                    ),
                    "default_promotion_lights": preflight.get(
                        "default_promotion_release_direct_publication_guard_lights"
                    ),
                    "github_plan_matrix_check": preflight.get(
                        "github_plan_matrix_release_decision_direct_publication_guard_passed"
                    ),
                    "github_plan_default_promotion_check": preflight.get(
                        "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed"
                    ),
                    "github_plan_matrix_match_check": preflight.get(
                        "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix"
                    ),
                    "github_plan_default_promotion_match_check": preflight.get(
                        "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix"
                    ),
                    "matrix_release_check": preflight.get(
                        "matrix_release_decision_direct_runtime_publication_guard_passed"
                    ),
                    "matrix_default_promotion_check": preflight.get(
                        "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_release_decision_direct_runtime_publication_guard_passed"
                    ),
                    "matrix_default_match_check": preflight.get(
                        "matrix_release_decision_direct_publication_guard_matches_default_promotion"
                    ),
                    "matrix_manifest_match_check": preflight.get(
                        "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        release_quality_guard_present = (
            preflight.get("matrix_release_quality_publication_guard_present")
            is not None
            or preflight.get(
                "default_promotion_release_quality_publication_guard_present"
            )
            is not None
            or preflight.get(
                "matrix_default_promotion_release_quality_publication_guard_ready"
            )
            is not None
        )
        release_quality_guard_final_checks_present = any(
            preflight.get(field) is not None
            for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_CHECK_FIELDS
        )
        preflight_status_payload = {"publish_preflight": preflight}
        release_quality_guard_final_evidence_present = (
            _publish_preflight_release_quality_publication_guard_final_evidence_present(
                preflight_status_payload
            )
        )
        release_quality_guard_final_evidence_detail_present = (
            _publish_preflight_release_quality_publication_guard_final_evidence_detail_present(
                preflight_status_payload
            )
        )
        release_quality_guard_final_evidence_passed = (
            not release_quality_guard_final_evidence_present
            or _publish_preflight_release_quality_publication_guard_final_evidence_passed(
                preflight_status_payload
            )
        )
        checks.append(
            {
                "name": "windows_publish_preflight_release_quality_publication_guard_passed",
                "passed": (
                    not release_quality_guard_present
                    or (
                        preflight.get(
                            "matrix_release_decision_quality_compare_publication_guard_passed"
                        )
                        is True
                        and preflight.get(
                            "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_release_decision_quality_compare_publication_guard_passed"
                        )
                        is True
                        and preflight.get(
                            "matrix_release_decision_quality_publication_guard_matches_default_promotion"
                        )
                        is True
                        and preflight.get(
                            "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest"
                        )
                        is True
                        and (
                            not release_quality_guard_final_checks_present
                            or all(
                                preflight.get(field) is True
                                for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_CHECK_FIELDS
                            )
                        )
                        and release_quality_guard_final_evidence_passed
                        and preflight.get(
                            "matrix_release_quality_publication_guard_present"
                        )
                        is True
                        and preflight.get(
                            "matrix_release_quality_publication_guard_ready"
                        )
                        is True
                        and preflight.get(
                            "matrix_release_quality_publication_guard_check_passed"
                        )
                        is True
                        and preflight.get(
                            "matrix_release_quality_publication_guard_layers_ready"
                        )
                        is True
                        and preflight.get(
                            "matrix_release_quality_publication_guard_raw_status"
                        )
                        == "passed"
                        and preflight.get(
                            "matrix_release_quality_publication_guard_phase2_status"
                        )
                        == "passed"
                        and preflight.get(
                            "matrix_default_promotion_release_quality_publication_guard_ready"
                        )
                        is True
                        and preflight.get(
                            "matrix_default_promotion_release_quality_publication_guard_raw_status"
                        )
                        == "passed"
                        and preflight.get(
                            "matrix_default_promotion_release_quality_publication_guard_phase2_status"
                        )
                        == "passed"
                        and preflight.get(
                            "default_promotion_release_quality_publication_guard_present"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_release_quality_publication_guard_ready"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_release_quality_publication_guard_check_passed"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_release_quality_publication_guard_layers_ready"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_release_quality_publication_guard_raw_status"
                        )
                        == "passed"
                        and preflight.get(
                            "default_promotion_release_quality_publication_guard_phase2_status"
                        )
                        == "passed"
                    )
                ),
                "evidence": {
                    "present": release_quality_guard_present,
                    "matrix_present": preflight.get(
                        "matrix_release_quality_publication_guard_present"
                    ),
                    "matrix_ready": preflight.get(
                        "matrix_release_quality_publication_guard_ready"
                    ),
                    "matrix_check_passed": preflight.get(
                        "matrix_release_quality_publication_guard_check_passed"
                    ),
                    "matrix_layers_ready": preflight.get(
                        "matrix_release_quality_publication_guard_layers_ready"
                    ),
                    "matrix_raw_status": preflight.get(
                        "matrix_release_quality_publication_guard_raw_status"
                    ),
                    "matrix_phase2_status": preflight.get(
                        "matrix_release_quality_publication_guard_phase2_status"
                    ),
                    "matrix_default_ready": preflight.get(
                        "matrix_default_promotion_release_quality_publication_guard_ready"
                    ),
                    "matrix_default_raw_status": preflight.get(
                        "matrix_default_promotion_release_quality_publication_guard_raw_status"
                    ),
                    "matrix_default_phase2_status": preflight.get(
                        "matrix_default_promotion_release_quality_publication_guard_phase2_status"
                    ),
                    "default_promotion_present": preflight.get(
                        "default_promotion_release_quality_publication_guard_present"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_release_quality_publication_guard_ready"
                    ),
                    "default_promotion_check_passed": preflight.get(
                        "default_promotion_release_quality_publication_guard_check_passed"
                    ),
                    "default_promotion_layers_ready": preflight.get(
                        "default_promotion_release_quality_publication_guard_layers_ready"
                    ),
                    "default_promotion_raw_status": preflight.get(
                        "default_promotion_release_quality_publication_guard_raw_status"
                    ),
                    "default_promotion_phase2_status": preflight.get(
                        "default_promotion_release_quality_publication_guard_phase2_status"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_release_decision_quality_compare_publication_guard_passed"
                    ),
                    "matrix_default_check": preflight.get(
                        "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_release_decision_quality_compare_publication_guard_passed"
                    ),
                    "matrix_default_match_check": preflight.get(
                        "matrix_release_decision_quality_publication_guard_matches_default_promotion"
                    ),
                    "matrix_manifest_match_check": preflight.get(
                        "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest"
                    ),
                    "final_checks_present": (
                        release_quality_guard_final_checks_present
                    ),
                    "final_evidence_present": (
                        release_quality_guard_final_evidence_present
                    ),
                    "final_evidence_detail_present": (
                        release_quality_guard_final_evidence_detail_present
                    ),
                    "final_evidence_passed": (
                        release_quality_guard_final_evidence_passed
                    ),
                    "release_matrix_check": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_passed"
                    ),
                    "release_matrix_default_check": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_passed"
                    ),
                    "release_default_promotion_check": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_passed"
                    ),
                    "release_matrix_default_match_check": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_matches_default_promotion"
                    ),
                    "release_matrix_manifest_match_check": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest"
                    ),
                    "matrix_final_checks_ready": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_final_checks_ready"
                    ),
                    "matrix_final_checks_match": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_final_checks_match"
                    ),
                    "matrix_raw_final_checks_ready": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_raw_final_checks_ready"
                    ),
                    "matrix_phase2_final_checks_ready": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_phase2_final_checks_ready"
                    ),
                    "matrix_default_final_checks_ready": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_ready"
                    ),
                    "matrix_default_final_checks_match": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_match"
                    ),
                    "matrix_default_raw_final_checks_ready": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready"
                    ),
                    "matrix_default_phase2_final_checks_ready": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready"
                    ),
                    "default_promotion_final_checks_ready": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_final_checks_ready"
                    ),
                    "default_promotion_final_checks_match": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_final_checks_match"
                    ),
                    "default_promotion_raw_final_checks_ready": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready"
                    ),
                    "default_promotion_phase2_final_checks_ready": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready"
                    ),
                    "matrix_final_evidence_ready": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_final_evidence_ready"
                    ),
                    "matrix_final_evidence_match": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_final_evidence_match"
                    ),
                    "matrix_raw_final_evidence_ready": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_raw_final_evidence_ready"
                    ),
                    "matrix_phase2_final_evidence_ready": preflight.get(
                        "matrix_release_decision_release_quality_publication_guard_phase2_final_evidence_ready"
                    ),
                    "matrix_default_final_evidence_ready": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready"
                    ),
                    "matrix_default_final_evidence_match": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_match"
                    ),
                    "matrix_default_raw_final_evidence_ready": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready"
                    ),
                    "matrix_default_phase2_final_evidence_ready": preflight.get(
                        "matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready"
                    ),
                    "default_promotion_final_evidence_ready": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready"
                    ),
                    "default_promotion_final_evidence_match": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_final_evidence_match"
                    ),
                    "default_promotion_raw_final_evidence_ready": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready"
                    ),
                    "default_promotion_phase2_final_evidence_ready": preflight.get(
                        "default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_resident_winsorized_sweep_passed",
                "passed": (
                    preflight.get("matrix_resident_winsorized_sweep_audit_passed")
                    is True
                    and preflight.get(
                        "matrix_resident_winsorized_required_frame_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_resident_winsorized_sweep_check_count_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_winsorized_sweep_audit_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_winsorized_required_frame_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_winsorized_sweep_matches_matrix"
                    )
                    is True
                ),
                "evidence": {
                    "matrix_status": preflight.get(
                        "matrix_resident_winsorized_sweep_status"
                    ),
                    "matrix_required_frame_count": preflight.get(
                        "matrix_resident_winsorized_sweep_required_frame_count"
                    ),
                    "matrix_required_frame_count_passed": preflight.get(
                        "matrix_resident_winsorized_sweep_required_frame_count_passed"
                    ),
                    "matrix_check_count": preflight.get(
                        "matrix_resident_winsorized_sweep_check_count"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_resident_winsorized_sweep_status"
                    ),
                    "default_promotion_required_frame_count": preflight.get(
                        "default_promotion_resident_winsorized_sweep_required_frame_count"
                    ),
                    "default_promotion_required_frame_count_passed": preflight.get(
                        "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
                    ),
                    "default_promotion_check_count": preflight.get(
                        "default_promotion_resident_winsorized_sweep_check_count"
                    ),
                    "matrix_audit_check": preflight.get(
                        "matrix_resident_winsorized_sweep_audit_passed"
                    ),
                    "matrix_required_frame_check": preflight.get(
                        "matrix_resident_winsorized_required_frame_passed"
                    ),
                    "matrix_check_count_check": preflight.get(
                        "matrix_resident_winsorized_sweep_check_count_passed"
                    ),
                    "default_promotion_audit_check": preflight.get(
                        "default_promotion_resident_winsorized_sweep_audit_passed"
                    ),
                    "default_promotion_required_frame_check": preflight.get(
                        "default_promotion_resident_winsorized_required_frame_passed"
                    ),
                    "default_promotion_match_check": preflight.get(
                        "default_promotion_resident_winsorized_sweep_matches_matrix"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_resident_fastpath_handoff_passed",
                "passed": (
                    preflight.get(
                        "github_plan_matrix_resident_fastpath_release_handoff_ready"
                    )
                    is True
                    and preflight.get("matrix_resident_fastpath_release_handoff_ready")
                    is True
                    and preflight.get(
                        "default_promotion_resident_fastpath_release_handoff_ready"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_matches_matrix"
                    )
                    is True
                    and preflight.get(
                        "matrix_resident_fastpath_handoff_matches_default_promotion"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_ready"
                    )
                    is True
                    and preflight.get("matrix_resident_fastpath_handoff_ready")
                    is True
                    and preflight.get(
                        "default_promotion_resident_fastpath_handoff_ready"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_raw_status"
                    )
                    == "passed"
                    and preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_phase2_status"
                    )
                    == "passed"
                    and preflight.get("matrix_resident_fastpath_handoff_raw_status")
                    == "passed"
                    and preflight.get("matrix_resident_fastpath_handoff_phase2_status")
                    == "passed"
                    and preflight.get(
                        "default_promotion_resident_fastpath_handoff_raw_status"
                    )
                    == "passed"
                    and preflight.get(
                        "default_promotion_resident_fastpath_handoff_phase2_status"
                    )
                    == "passed"
                    and _int_or_zero(
                        preflight.get(
                            "github_plan_matrix_resident_fastpath_handoff_raw_check_count"
                        )
                    )
                    > 0
                    and _int_or_zero(
                        preflight.get(
                            "matrix_resident_fastpath_handoff_raw_check_count"
                        )
                    )
                    > 0
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_resident_fastpath_handoff_raw_check_count"
                        )
                    )
                    > 0
                ),
                "evidence": {
                    "github_plan_matrix_ready": preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_ready"
                    ),
                    "github_plan_matrix_raw_status": preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_raw_status"
                    ),
                    "github_plan_matrix_phase2_status": preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_phase2_status"
                    ),
                    "github_plan_matrix_raw_check_count": preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_raw_check_count"
                    ),
                    "matrix_ready": preflight.get(
                        "matrix_resident_fastpath_handoff_ready"
                    ),
                    "matrix_raw_status": preflight.get(
                        "matrix_resident_fastpath_handoff_raw_status"
                    ),
                    "matrix_phase2_status": preflight.get(
                        "matrix_resident_fastpath_handoff_phase2_status"
                    ),
                    "matrix_raw_check_count": preflight.get(
                        "matrix_resident_fastpath_handoff_raw_check_count"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_resident_fastpath_handoff_ready"
                    ),
                    "default_promotion_raw_status": preflight.get(
                        "default_promotion_resident_fastpath_handoff_raw_status"
                    ),
                    "default_promotion_phase2_status": preflight.get(
                        "default_promotion_resident_fastpath_handoff_phase2_status"
                    ),
                    "default_promotion_raw_check_count": preflight.get(
                        "default_promotion_resident_fastpath_handoff_raw_check_count"
                    ),
                    "github_plan_matrix_check": preflight.get(
                        "github_plan_matrix_resident_fastpath_release_handoff_ready"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_resident_fastpath_release_handoff_ready"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_resident_fastpath_release_handoff_ready"
                    ),
                    "github_plan_matrix_match_check": preflight.get(
                        "github_plan_matrix_resident_fastpath_handoff_matches_matrix"
                    ),
                    "matrix_default_promotion_match_check": preflight.get(
                        "matrix_resident_fastpath_handoff_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_stack_engine_publication_audit_passed",
                "passed": (
                    preflight.get("matrix_stack_engine_publication_audit_passed")
                    is True
                    and preflight.get(
                        "matrix_stack_engine_publication_policy_chain_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_publication_resident_winsorized_chain_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_publication_audit_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_publication_policy_chain_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_publication_audit_matches_default_promotion"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_publication_audit_status"
                    )
                    == "passed"
                    and preflight.get(
                        "default_promotion_stack_engine_publication_audit_status"
                    )
                    == "passed"
                    and preflight.get("matrix_stack_engine_publication_audit_ready")
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_publication_audit_ready"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_publication_policy_agreement"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_publication_policy_agreement"
                    )
                    is True
                    and preflight.get(
                        "matrix_stack_engine_publication_resident_winsorized_agreement"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_stack_engine_publication_resident_winsorized_agreement"
                    )
                    is True
                ),
                "evidence": {
                    "matrix_status": preflight.get(
                        "matrix_stack_engine_publication_audit_status"
                    ),
                    "matrix_ready": preflight.get(
                        "matrix_stack_engine_publication_audit_ready"
                    ),
                    "matrix_policy_agreement": preflight.get(
                        "matrix_stack_engine_publication_policy_agreement"
                    ),
                    "matrix_resident_winsorized_agreement": preflight.get(
                        "matrix_stack_engine_publication_resident_winsorized_agreement"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_stack_engine_publication_audit_status"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_stack_engine_publication_audit_ready"
                    ),
                    "default_promotion_policy_agreement": preflight.get(
                        "default_promotion_stack_engine_publication_policy_agreement"
                    ),
                    "default_promotion_resident_winsorized_agreement": preflight.get(
                        "default_promotion_stack_engine_publication_resident_winsorized_agreement"
                    ),
                    "matrix_audit_check": preflight.get(
                        "matrix_stack_engine_publication_audit_passed"
                    ),
                    "matrix_policy_check": preflight.get(
                        "matrix_stack_engine_publication_policy_chain_passed"
                    ),
                    "matrix_resident_winsorized_check": preflight.get(
                        "matrix_stack_engine_publication_resident_winsorized_chain_passed"
                    ),
                    "default_promotion_audit_check": preflight.get(
                        "default_promotion_stack_engine_publication_audit_passed"
                    ),
                    "default_promotion_policy_check": preflight.get(
                        "default_promotion_stack_engine_publication_policy_chain_passed"
                    ),
                    "default_promotion_resident_winsorized_check": preflight.get(
                        "default_promotion_stack_engine_publication_resident_winsorized_chain_passed"
                    ),
                    "agreement_check": preflight.get(
                        "matrix_stack_engine_publication_audit_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        quality_compare_present = any(
            preflight.get(field) is not None
            for field in (
                "matrix_quality_metrics_compare_present",
                "matrix_quality_metrics_compare_ready",
                "matrix_quality_metrics_compare_status",
                "matrix_quality_metrics_compare_failed_check_count",
                "default_promotion_quality_metrics_compare_present",
                "default_promotion_quality_metrics_compare_ready",
                "default_promotion_quality_metrics_compare_status",
                "default_promotion_quality_metrics_compare_failed_check_count",
            )
        )
        checks.append(
            {
                "name": "windows_publish_preflight_quality_metrics_compare_passed",
                "passed": (
                    not quality_compare_present
                    or (
                        preflight.get(
                            "windows_release_matrix_quality_metrics_compare_handoff_passed"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_quality_metrics_compare_handoff_passed"
                        )
                        is True
                        and preflight.get(
                            "matrix_quality_metrics_compare_matches_default_promotion"
                        )
                        is True
                        and preflight.get("matrix_quality_metrics_compare_present")
                        is True
                        and preflight.get("matrix_quality_metrics_compare_ready")
                        is True
                        and preflight.get("matrix_quality_metrics_compare_status")
                        == "passed"
                        and _int_or_zero(
                            preflight.get(
                                "matrix_quality_metrics_compare_failed_check_count"
                            )
                        )
                        == 0
                        and preflight.get(
                            "default_promotion_quality_metrics_compare_present"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_quality_metrics_compare_ready"
                        )
                        is True
                        and preflight.get(
                            "default_promotion_quality_metrics_compare_status"
                        )
                        == "passed"
                        and _int_or_zero(
                            preflight.get(
                                "default_promotion_quality_metrics_compare_failed_check_count"
                            )
                        )
                        == 0
                    )
                ),
                "evidence": {
                    "present": quality_compare_present,
                    "matrix_present": preflight.get(
                        "matrix_quality_metrics_compare_present"
                    ),
                    "matrix_ready": preflight.get(
                        "matrix_quality_metrics_compare_ready"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_quality_metrics_compare_status"
                    ),
                    "matrix_failed_check_count": preflight.get(
                        "matrix_quality_metrics_compare_failed_check_count"
                    ),
                    "default_promotion_present": preflight.get(
                        "default_promotion_quality_metrics_compare_present"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_quality_metrics_compare_ready"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_quality_metrics_compare_status"
                    ),
                    "default_promotion_failed_check_count": preflight.get(
                        "default_promotion_quality_metrics_compare_failed_check_count"
                    ),
                    "matrix_check": preflight.get(
                        "windows_release_matrix_quality_metrics_compare_handoff_passed"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_quality_metrics_compare_handoff_passed"
                    ),
                    "agreement_check": preflight.get(
                        "matrix_quality_metrics_compare_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "windows_publish_preflight_resident_result_contract_handoff_passed",
                "passed": (
                    preflight.get(
                        "github_plan_matrix_resident_result_contract_handoff_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_resident_result_contract_handoff_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_result_contract_handoff_passed"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_resident_result_contract_matches_matrix"
                    )
                    is True
                    and preflight.get(
                        "matrix_resident_result_contract_matches_default_promotion"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_resident_result_contract_ready"
                    )
                    is True
                    and preflight.get("matrix_resident_result_contract_ready") is True
                    and preflight.get(
                        "default_promotion_resident_result_contract_ready"
                    )
                    is True
                    and preflight.get(
                        "github_plan_matrix_resident_result_contract_status"
                    )
                    == "passed"
                    and preflight.get("matrix_resident_result_contract_status")
                    == "passed"
                    and preflight.get(
                        "default_promotion_resident_result_contract_status"
                    )
                    == "passed"
                    and preflight.get(
                        "github_plan_matrix_resident_result_contract_phase2_check_passed"
                    )
                    is True
                    and preflight.get(
                        "matrix_resident_result_contract_phase2_check_passed"
                    )
                    is True
                    and preflight.get(
                        "default_promotion_resident_result_contract_phase2_check_passed"
                    )
                    is True
                    and _int_or_zero(
                        preflight.get(
                            "github_plan_matrix_resident_result_contract_required_count"
                        )
                    )
                    > 0
                    and _int_or_zero(
                        preflight.get("matrix_resident_result_contract_required_count")
                    )
                    > 0
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_resident_result_contract_required_count"
                        )
                    )
                    > 0
                    and _int_or_zero(
                        preflight.get(
                            "github_plan_matrix_resident_result_contract_failed_count"
                        )
                    )
                    == 0
                    and _int_or_zero(
                        preflight.get("matrix_resident_result_contract_failed_count")
                    )
                    == 0
                    and _int_or_zero(
                        preflight.get(
                            "default_promotion_resident_result_contract_failed_count"
                        )
                    )
                    == 0
                ),
                "evidence": {
                    "github_plan_matrix_ready": preflight.get(
                        "github_plan_matrix_resident_result_contract_ready"
                    ),
                    "github_plan_matrix_status": preflight.get(
                        "github_plan_matrix_resident_result_contract_status"
                    ),
                    "github_plan_matrix_phase2_check": preflight.get(
                        "github_plan_matrix_resident_result_contract_phase2_check_passed"
                    ),
                    "github_plan_matrix_required_count": preflight.get(
                        "github_plan_matrix_resident_result_contract_required_count"
                    ),
                    "github_plan_matrix_failed_count": preflight.get(
                        "github_plan_matrix_resident_result_contract_failed_count"
                    ),
                    "matrix_ready": preflight.get(
                        "matrix_resident_result_contract_ready"
                    ),
                    "matrix_status": preflight.get(
                        "matrix_resident_result_contract_status"
                    ),
                    "matrix_phase2_check": preflight.get(
                        "matrix_resident_result_contract_phase2_check_passed"
                    ),
                    "matrix_required_count": preflight.get(
                        "matrix_resident_result_contract_required_count"
                    ),
                    "matrix_failed_count": preflight.get(
                        "matrix_resident_result_contract_failed_count"
                    ),
                    "default_promotion_ready": preflight.get(
                        "default_promotion_resident_result_contract_ready"
                    ),
                    "default_promotion_status": preflight.get(
                        "default_promotion_resident_result_contract_status"
                    ),
                    "default_promotion_phase2_check": preflight.get(
                        "default_promotion_resident_result_contract_phase2_check_passed"
                    ),
                    "default_promotion_required_count": preflight.get(
                        "default_promotion_resident_result_contract_required_count"
                    ),
                    "default_promotion_failed_count": preflight.get(
                        "default_promotion_resident_result_contract_failed_count"
                    ),
                    "github_plan_matrix_check": preflight.get(
                        "github_plan_matrix_resident_result_contract_handoff_passed"
                    ),
                    "matrix_check": preflight.get(
                        "matrix_resident_result_contract_handoff_passed"
                    ),
                    "default_promotion_check": preflight.get(
                        "default_promotion_resident_result_contract_handoff_passed"
                    ),
                    "github_plan_matrix_match_check": preflight.get(
                        "github_plan_matrix_resident_result_contract_matches_matrix"
                    ),
                    "matrix_default_promotion_match_check": preflight.get(
                        "matrix_resident_result_contract_matches_default_promotion"
                    ),
                    "failed_checks": preflight.get("failed_checks"),
                },
            }
        )
    if publication_audit is not None:
        checks.append(
            {
                "name": "stack_engine_publication_audit_passed",
                "passed": publication_audit.get("passed") is True
                and publication_audit.get("status") == "passed",
                "evidence": {
                    "status": publication_audit.get("status"),
                    "passed": publication_audit.get("passed"),
                    "recommendation": publication_audit.get("recommendation"),
                    "check_count": publication_audit.get("check_count"),
                    "failed_check_count": publication_audit.get(
                        "failed_check_count"
                    ),
                    "failed_checks": publication_audit.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "stack_engine_publication_audit_policy_chain_passed",
                "passed": (
                    publication_audit.get(
                        "publish_preflight_integration_engine_policy_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_integration_engine_policy_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
                    )
                    is True
                ),
                "evidence": {
                    "raw_layer": publication_audit.get(
                        "publish_preflight_integration_engine_policy"
                    ),
                    "phase2_layer": publication_audit.get(
                        "phase2_publish_preflight_integration_engine_policy"
                    ),
                    "raw_ready_check": publication_audit.get(
                        "publish_preflight_integration_engine_policy_ready"
                    ),
                    "phase2_ready_check": publication_audit.get(
                        "phase2_publish_preflight_integration_engine_policy_ready"
                    ),
                    "agreement_check": publication_audit.get(
                        "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight"
                    ),
                    "failed_checks": publication_audit.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "stack_engine_publication_audit_resident_winsorized_chain_passed",
                "passed": (
                    publication_audit.get(
                        "publish_preflight_resident_winsorized_sweep_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_resident_winsorized_sweep_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
                    )
                    is True
                ),
                "evidence": {
                    "raw_layer": publication_audit.get(
                        "publish_preflight_resident_winsorized_sweep"
                    ),
                    "phase2_layer": publication_audit.get(
                        "phase2_publish_preflight_resident_winsorized_sweep"
                    ),
                    "raw_ready_check": publication_audit.get(
                        "publish_preflight_resident_winsorized_sweep_ready"
                    ),
                    "phase2_ready_check": publication_audit.get(
                        "phase2_publish_preflight_resident_winsorized_sweep_ready"
                    ),
                    "agreement_check": publication_audit.get(
                        "phase2_publish_preflight_resident_winsorized_matches_publish_preflight"
                    ),
                    "failed_checks": publication_audit.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "stack_engine_publication_audit_resident_result_contract_chain_passed",
                "passed": (
                    publication_audit.get(
                        "publish_preflight_resident_result_contract_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_resident_result_contract_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_resident_result_contract_matches_publish_preflight"
                    )
                    is True
                ),
                "evidence": {
                    "raw_layer": publication_audit.get(
                        "publish_preflight_resident_result_contract"
                    ),
                    "phase2_layer": publication_audit.get(
                        "phase2_publish_preflight_resident_result_contract"
                    ),
                    "raw_ready_check": publication_audit.get(
                        "publish_preflight_resident_result_contract_ready"
                    ),
                    "phase2_ready_check": publication_audit.get(
                        "phase2_publish_preflight_resident_result_contract_ready"
                    ),
                    "agreement_check": publication_audit.get(
                        "phase2_publish_preflight_resident_result_contract_matches_publish_preflight"
                    ),
                    "failed_checks": publication_audit.get("failed_checks"),
                },
            }
        )
        checks.append(
            {
                "name": "stack_engine_publication_audit_direct_runtime_chain_passed",
                "passed": (
                    publication_audit.get(
                        "publish_preflight_direct_runtime_evidence_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_direct_runtime_evidence_ready"
                    )
                    is True
                    and publication_audit.get(
                        "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
                    )
                    is True
                ),
                "evidence": {
                    "raw_layer": publication_audit.get(
                        "publish_preflight_direct_runtime_evidence"
                    ),
                    "phase2_layer": publication_audit.get(
                        "phase2_publish_preflight_direct_runtime_evidence"
                    ),
                    "raw_ready_check": publication_audit.get(
                        "publish_preflight_direct_runtime_evidence_ready"
                    ),
                    "phase2_ready_check": publication_audit.get(
                        "phase2_publish_preflight_direct_runtime_evidence_ready"
                    ),
                    "agreement_check": publication_audit.get(
                        "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight"
                    ),
                    "failed_checks": publication_audit.get("failed_checks"),
                },
            }
        )
    if pipeline is not None:
        checks.append(
            {
                "name": "pipeline_contract_passed",
                "passed": pipeline.get("passed") is True,
                "evidence": {
                    "status": pipeline.get("status"),
                    "failed_check_count": pipeline.get("failed_check_count"),
                    "integration_dq_contract": pipeline.get("integration_dq_contract"),
                    "pixel_verification_enabled": pipeline.get("pixel_verification_enabled"),
                },
            }
        )
        resident_result = (
            pipeline.get("resident_result_contract")
            if isinstance(pipeline.get("resident_result_contract"), dict)
            else {}
        )
        requires_resident_result = (
            pipeline.get("integration_resident_result_contract") is not None
            or resident_result.get("check_present") is True
            or _int_or_zero(resident_result.get("required_count")) > 0
        )
        resident_result_passed = (
            resident_result.get("status") == "passed"
            and _int_or_zero(resident_result.get("failed_count")) == 0
            and _int_or_zero(resident_result.get("failed_check_count")) == 0
        )
        checks.append(
            {
                "name": "pipeline_resident_result_contract_passed",
                "passed": (not requires_resident_result) or resident_result_passed,
                "evidence": {
                    "status": resident_result.get("status"),
                    "check_present": resident_result.get("check_present"),
                    "check_passed": resident_result.get("check_passed"),
                    "required_count": resident_result.get("required_count"),
                    "failed_count": resident_result.get("failed_count"),
                    "failed_check_count": resident_result.get("failed_check_count"),
                    "failed_checks": resident_result.get("failed_checks"),
                    "failed_items": resident_result.get("failed_items"),
                },
            }
        )
        engine_policy = (
            pipeline.get("integration_engine_policy")
            if isinstance(pipeline.get("integration_engine_policy"), dict)
            else {}
        )
        checks.append(
            {
                "name": "pipeline_integration_engine_policy_passed",
                "passed": (
                    engine_policy.get("status") == "passed"
                    and engine_policy.get("check_present") is True
                    and engine_policy.get("check_passed") is True
                ),
                "evidence": {
                    "status": engine_policy.get("status"),
                    "check_present": engine_policy.get("check_present"),
                    "check_passed": engine_policy.get("check_passed"),
                    "non_resident_count": engine_policy.get("non_resident_count"),
                    "failed_count": engine_policy.get("failed_count"),
                    "failed_items": engine_policy.get("failed_items"),
                },
            }
        )
        runtime_default = (
            pipeline.get("stack_engine_runtime_default")
            if isinstance(pipeline.get("stack_engine_runtime_default"), dict)
            else {}
        )
        checks.append(
            {
                "name": "pipeline_stack_engine_runtime_default_passed",
                "passed": (
                    runtime_default.get("status") == "passed"
                    and runtime_default.get("check_present") is True
                    and runtime_default.get("check_passed") is True
                    and _int_or_zero(runtime_default.get("legacy_master_count")) == 0
                    and _int_or_zero(runtime_default.get("failed_master_count")) == 0
                    and _int_or_zero(runtime_default.get("failed_output_count")) == 0
                ),
                "evidence": {
                    "status": runtime_default.get("status"),
                    "check_present": runtime_default.get("check_present"),
                    "check_passed": runtime_default.get("check_passed"),
                    "legacy_master_count": runtime_default.get("legacy_master_count"),
                    "failed_master_count": runtime_default.get("failed_master_count"),
                    "failed_output_count": runtime_default.get("failed_output_count"),
                    "explicit_cuda_fast_path_count": runtime_default.get(
                        "explicit_cuda_fast_path_count"
                    ),
                },
            }
        )
        rejection_accounting = (
            pipeline.get("rejection_sample_accounting")
            if isinstance(pipeline.get("rejection_sample_accounting"), dict)
            else {}
        )
        requires_rejection_accounting = (
            pipeline.get("pixel_verification_enabled") is True
            or rejection_accounting.get("check_present") is True
            or int(rejection_accounting.get("accounted_output_count") or 0) > 0
        )
        checks.append(
            {
                "name": "pipeline_rejection_sample_accounting_passed",
                "passed": (not requires_rejection_accounting)
                or rejection_accounting.get("status") == "passed",
                "evidence": {
                    "status": rejection_accounting.get("status"),
                    "check_present": rejection_accounting.get("check_present"),
                    "check_passed": rejection_accounting.get("check_passed"),
                    "pixel_verification_enabled": rejection_accounting.get(
                        "pixel_verification_enabled"
                    ),
                    "accounted_output_count": rejection_accounting.get(
                        "accounted_output_count"
                    ),
                    "failed_count": rejection_accounting.get("failed_count"),
                    "failed_items": rejection_accounting.get("failed_items"),
                },
            }
        )
        sample_closure = (
            pipeline.get("sample_accounting_closure")
            if isinstance(pipeline.get("sample_accounting_closure"), dict)
            else {}
        )
        requires_sample_closure = (
            sample_closure.get("check_present") is True
            or int(sample_closure.get("present_count") or 0) > 0
        )
        checks.append(
            {
                "name": "pipeline_sample_accounting_closure_passed",
                "passed": (not requires_sample_closure)
                or sample_closure.get("status") == "passed",
                "evidence": {
                    "status": sample_closure.get("status"),
                    "check_present": sample_closure.get("check_present"),
                    "check_passed": sample_closure.get("check_passed"),
                    "present_count": sample_closure.get("present_count"),
                    "required_count": sample_closure.get("required_count"),
                    "failed_count": sample_closure.get("failed_count"),
                    "failed_items": sample_closure.get("failed_items"),
                },
            }
        )
    if stack_engine is not None:
        checks.append(
            {
                "name": "stack_engine_default_contract_ready",
                "passed": _stack_engine_default_contract_ready(stack_engine),
                "evidence": {
                    "status": stack_engine.get("status"),
                    "passed": stack_engine.get("passed"),
                    "scope": stack_engine.get("scope"),
                    "expected_integration_engine": stack_engine.get(
                        "expected_integration_engine"
                    ),
                    "adoption_recommendation": stack_engine.get(
                        "adoption_recommendation"
                    ),
                    "adoption_gap_count": stack_engine.get(
                        "adoption_phase2_stack_engine_default_gap_count"
                    ),
                    "default_promotion_ready": stack_engine.get(
                        "default_promotion_ready"
                    ),
                    "default_promotion_status": stack_engine.get(
                        "default_promotion_status"
                    ),
                    "default_promotion_blocker_count": stack_engine.get(
                        "default_promotion_blocker_count"
                    ),
                    "failed_checks": stack_engine.get("failed_checks"),
                    "blockers": stack_engine.get("default_promotion_blockers"),
                },
            }
        )
    if winsorized_audit is not None:
        checks.append(
            {
                "name": "resident_winsorized_benchmark_audit_passed",
                "passed": winsorized_audit.get("passed") is True,
                "evidence": {
                    "status": winsorized_audit.get("status"),
                    "contract_name": winsorized_audit.get("contract_name"),
                    "check_count": winsorized_audit.get("check_count"),
                    "failed_check_count": winsorized_audit.get("failed_check_count"),
                    "failed_checks": winsorized_audit.get("failed_checks"),
                    "hardened_master_rms": winsorized_audit.get("hardened_master_rms"),
                    "hardened_master_max_abs": winsorized_audit.get(
                        "hardened_master_max_abs"
                    ),
                    "fast_approx_master_rms": winsorized_audit.get(
                        "fast_approx_master_rms"
                    ),
                },
            }
        )
    if winsorized_sweep_audit is not None:
        checks.append(
            {
                "name": "resident_winsorized_sweep_audit_passed",
                "passed": winsorized_sweep_audit.get("passed") is True,
                "evidence": {
                    "status": winsorized_sweep_audit.get("status"),
                    "contract_name": winsorized_sweep_audit.get("contract_name"),
                    "check_count": winsorized_sweep_audit.get("check_count"),
                    "failed_check_count": winsorized_sweep_audit.get("failed_check_count"),
                    "failed_checks": winsorized_sweep_audit.get("failed_checks"),
                    "required_frame_count": winsorized_sweep_audit.get("required_frame_count"),
                    "required_frame_count_passed": winsorized_sweep_audit.get(
                        "required_frame_count_passed"
                    ),
                    "required_frame_master_rms": winsorized_sweep_audit.get(
                        "required_frame_master_rms"
                    ),
                    "required_frame_master_max_abs": winsorized_sweep_audit.get(
                        "required_frame_master_max_abs"
                    ),
                    "max_hardened_master_rms": winsorized_sweep_audit.get(
                        "max_hardened_master_rms"
                    ),
                },
            }
        )
    if decision is not None:
        checks.append(
            {
                "name": "release_decision_default_change_ready",
                "passed": _default_change_is_ready(decision),
                "evidence": {
                    "status": decision.get("status"),
                    "release_candidate_ready": decision.get("release_candidate_ready"),
                    "default_change_ready": decision.get("default_change_ready"),
                    "recommendation": decision.get("recommendation"),
                    "runtime_repeat_elapsed_ratio_vs_best": decision.get(
                        "runtime_repeat_elapsed_ratio_vs_best"
                    ),
                },
            }
        )
        checks.append(
            {
                "name": "release_decision_warp_quality_handoff_ready",
                "passed": (
                    decision.get("warp_quality_handoff_status") in (None, "not_available")
                    or decision.get("warp_quality_handoff_ready") is True
                ),
                "evidence": {
                    "present": decision.get("warp_quality_handoff_present"),
                    "status": decision.get("warp_quality_handoff_status"),
                    "ready": decision.get("warp_quality_handoff_ready"),
                    "contract_passed": decision.get(
                        "warp_quality_handoff_contract_passed"
                    ),
                    "output_count": decision.get("warp_quality_handoff_output_count"),
                    "failed_checks": decision.get(
                        "warp_quality_handoff_failed_checks"
                    ),
                    "failed_acceptance_checks": decision.get(
                        "warp_quality_handoff_failed_acceptance_checks"
                    ),
                    "path": decision.get("warp_quality_handoff_path"),
                },
            }
        )
        checks.append(
            {
                "name": "release_decision_resident_fastpath_handoff_ready",
                "passed": (
                    decision.get("resident_registration_fastpath_handoff_status")
                    in (None, "not_available")
                    or decision.get("resident_registration_fastpath_handoff_ready")
                    is True
                ),
                "evidence": {
                    "present": decision.get(
                        "resident_registration_fastpath_handoff_present"
                    ),
                    "status": decision.get(
                        "resident_registration_fastpath_handoff_status"
                    ),
                    "ready": decision.get(
                        "resident_registration_fastpath_handoff_ready"
                    ),
                    "required": decision.get(
                        "resident_registration_fastpath_handoff_required"
                    ),
                    "source": decision.get(
                        "resident_registration_fastpath_handoff_source"
                    ),
                    "mode": decision.get(
                        "resident_registration_fastpath_handoff_mode"
                    ),
                    "descriptor_fit_batch_mode": decision.get(
                        "resident_registration_fastpath_handoff_descriptor_fit_batch_mode"
                    ),
                    "pixel_refine_batch_mode": decision.get(
                        "resident_registration_fastpath_handoff_pixel_refine_batch_mode"
                    ),
                    "triangle_warp_batch_mode": decision.get(
                        "resident_registration_fastpath_handoff_triangle_warp_batch_mode"
                    ),
                    "triangle_warp_batch_frame_count": decision.get(
                        "resident_registration_fastpath_handoff_triangle_warp_batch_frame_count"
                    ),
                    "warp_copy_mode": decision.get(
                        "resident_registration_fastpath_handoff_warp_copy_mode"
                    ),
                    "passed_check_count": decision.get(
                        "resident_registration_fastpath_handoff_passed_check_count"
                    ),
                    "failed_check_count": decision.get(
                        "resident_registration_fastpath_handoff_failed_check_count"
                    ),
                    "failed_checks": decision.get(
                        "resident_registration_fastpath_handoff_failed_checks"
                    ),
                    "failed_acceptance_checks": decision.get(
                        "resident_registration_fastpath_handoff_failed_acceptance_checks"
                    ),
                    "path": decision.get(
                        "resident_registration_fastpath_handoff_path"
                    ),
                },
            }
        )
        checks.append(
            {
                "name": "release_decision_runtime_repeat_evidence_ready",
                "passed": runtime_repeat_closure.get("ready") is True,
                "evidence": runtime_repeat_closure,
            }
        )
        if acceptance is not None and _default_change_is_ready(decision):
            checks.append(
                {
                    "name": "resident_registration_fastpath_contract_passed_for_default",
                    "passed": _resident_fastpath_contract_passed(acceptance),
                    "evidence": {
                        "status": acceptance.get(
                            "resident_registration_fastpath_contract_status"
                        ),
                        "check_count": acceptance.get(
                            "resident_registration_fastpath_contract_check_count"
                        ),
                        "failed_check_count": acceptance.get(
                            "resident_registration_fastpath_contract_failed_check_count"
                        ),
                        "fastpath_status": acceptance.get(
                            "resident_registration_fastpath_status"
                        ),
                        "mode": acceptance.get("resident_registration_fastpath_mode"),
                    },
                }
            )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status",
        "created_at": now_iso(),
        "status": "green" if passed else "attention_required",
        "passed": passed,
        "latest_checkpoint": checkpoint,
        "acceptance_audit": acceptance,
        "default_route_acceptance": default_route_acceptance,
        "doctor": doctor,
        "release_manifest": release,
        "github_release_plan": github_plan,
        "publish_preflight": preflight,
        "stack_engine_publication_audit": publication_audit,
        "pipeline_contract": pipeline,
        "stack_engine_contract": stack_engine,
        "registration_admission": registration_admission,
        "quality_saturation": quality_saturation,
        "quality_metrics": quality_metrics,
        "quality_metrics_compare": quality_compare,
        "resident_winsorized_benchmark_audit": winsorized_audit,
        "resident_winsorized_sweep_audit": winsorized_sweep_audit,
        "release_decision": decision,
        "release_decision_runtime_repeat_closure": runtime_repeat_closure,
        "checks": checks,
    }


def write_phase2_status_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    checkpoint = payload.get("latest_checkpoint") or {}
    acceptance = payload.get("acceptance_audit") or {}
    default_route_acceptance = payload.get("default_route_acceptance") or {}
    doctor = payload.get("doctor") or {}
    release = payload.get("release_manifest") or {}
    github_plan = payload.get("github_release_plan") or {}
    preflight = payload.get("publish_preflight") or {}
    publication_audit = payload.get("stack_engine_publication_audit") or {}
    pipeline = payload.get("pipeline_contract") or {}
    stack_engine = payload.get("stack_engine_contract") or {}
    registration_admission = payload.get("registration_admission") or {}
    quality_saturation = payload.get("quality_saturation") or {}
    quality_metrics = payload.get("quality_metrics") or {}
    quality_compare = payload.get("quality_metrics_compare") or {}
    winsorized_audit = payload.get("resident_winsorized_benchmark_audit") or {}
    winsorized_sweep_audit = payload.get("resident_winsorized_sweep_audit") or {}
    decision = payload.get("release_decision") or {}
    runtime_repeat_closure = payload.get("release_decision_runtime_repeat_closure") or {}
    lines = [
        "# GLASS Phase 2 Status",
        "",
        f"- Status: {payload.get('status')}",
        f"- Latest checkpoint: S2-Gate {checkpoint.get('gate')} ({checkpoint.get('status')})",
        f"- Checkpoint path: {checkpoint.get('path')}",
    ]
    if acceptance:
        lines.extend(
            [
                "",
                "## Acceptance",
                "",
                f"- Status: {acceptance.get('status')}",
                f"- Speedup vs reference: {acceptance.get('speedup_vs_reference')}",
                f"- Active frames: {acceptance.get('active_frames')}",
                f"- RMS diff: {acceptance.get('rms_diff')}",
                f"- Coverage fraction: {acceptance.get('coverage_fraction')}",
                (
                    "- Benchmark contract: "
                    f"{acceptance.get('benchmark_contract_name')} "
                    f"source={acceptance.get('benchmark_contract_source')} "
                    f"profile={acceptance.get('benchmark_contract_profile')}"
                ),
                f"- Contract bundle schema: {acceptance.get('contract_bundle_schema_status')}",
                f"- Resident calibration contract: {acceptance.get('resident_calibration_contract_passed')}",
                f"- Resident result contract: {acceptance.get('resident_result_contract_passed')}",
                f"- Native guardrails bundle: {acceptance.get('native_guardrails_bundle_status')}",
                f"- Native resident result source: {acceptance.get('resident_result_contract_source')}",
                f"- Native resident result run default: {acceptance.get('resident_result_contract_run_default')}",
                f"- Native resident result contract: {acceptance.get('resident_result_contract_json')}",
                f"- Native calibration artifact: {acceptance.get('resident_native_calibration_artifact')}",
                f"- Native calibration masters: {acceptance.get('resident_calibration_master_count')}",
                f"- Native calibrated lights: {acceptance.get('resident_calibrated_light_count')}",
                (
                    "- Warp quality contract: "
                    f"{acceptance.get('warp_quality_contract_status')} "
                    f"passed={acceptance.get('warp_quality_contract_passed')} "
                    f"outputs={acceptance.get('warp_quality_contract_output_count')} "
                    f"failed={acceptance.get('warp_quality_contract_failed_checks')}"
                ),
                f"- Registration fast path: {acceptance.get('resident_registration_fastpath_status')}",
                (
                    "- Registration fast path contract: "
                    f"{acceptance.get('resident_registration_fastpath_contract_status')} "
                    f"checks={acceptance.get('resident_registration_fastpath_contract_check_count')} "
                    f"failed={acceptance.get('resident_registration_fastpath_contract_failed_check_count')}"
                ),
                f"- Registration fast path mode: {acceptance.get('resident_registration_fastpath_mode')}",
                f"- Descriptor fit batch: {acceptance.get('triangle_descriptor_fit_batch')}",
                f"- Descriptor fit batch mode: {acceptance.get('triangle_descriptor_fit_batch_mode')}",
                f"- Descriptor device reuse: {acceptance.get('triangle_descriptor_fit_device_reuse')}",
                f"- Pixel refine batch: {acceptance.get('triangle_pixel_refine_batch')}",
                f"- Pixel refine metric mode: {acceptance.get('triangle_pixel_refine_batch_metric_mode')}",
                f"- Triangle warp batch: {acceptance.get('triangle_warp_batch')}",
                f"- Triangle warp batch mode: {acceptance.get('triangle_warp_batch_mode')}",
                f"- Triangle warp batch frames: {acceptance.get('triangle_warp_batch_frame_count')}",
                f"- Resident warp copy mode: {acceptance.get('resident_warp_copy_mode')}",
                f"- Resident warp scratch bytes: {acceptance.get('resident_warp_scratch_bytes')}",
                (
                    "- Pipeline integration engine policy: "
                    f"{acceptance.get('pipeline_integration_engine_policy_status')} "
                    f"check={acceptance.get('pipeline_integration_engine_policy_check_passed')} "
                    f"nonresident={acceptance.get('pipeline_integration_engine_policy_non_resident_count')} "
                    f"failed={acceptance.get('pipeline_integration_engine_policy_failed_count')}"
                ),
                (
                    "- Pipeline StackEngine runtime default: "
                    f"{acceptance.get('pipeline_stack_engine_runtime_default_status')} "
                    f"check={acceptance.get('pipeline_stack_engine_runtime_default_check_passed')} "
                    f"masters={acceptance.get('pipeline_stack_engine_runtime_default_master_count')} "
                    f"legacy={acceptance.get('pipeline_stack_engine_runtime_default_legacy_master_count')} "
                    f"failed_masters={acceptance.get('pipeline_stack_engine_runtime_default_failed_master_count')} "
                    f"failed_outputs={acceptance.get('pipeline_stack_engine_runtime_default_failed_output_count')} "
                    f"explicit_cuda={acceptance.get('pipeline_stack_engine_runtime_default_explicit_cuda_fast_path_count')}"
                ),
            ]
        )
    if default_route_acceptance:
        contract = default_route_acceptance.get("benchmark_contract") or {}
        lines.extend(
            [
                "",
                "## Default Route Acceptance",
                "",
                f"- Status: {default_route_acceptance.get('status')}",
                f"- Passed: {default_route_acceptance.get('passed')}",
                f"- Route contract passed: {default_route_acceptance.get('route_contract_passed')}",
                f"- Contract: {contract.get('name')}",
                f"- Contract source: {default_route_acceptance.get('benchmark_contract_source')}",
                f"- Contract profile: {default_route_acceptance.get('benchmark_contract_profile')}",
                f"- Speedup vs reference: {default_route_acceptance.get('speedup_vs_reference')}",
                f"- Active frames: {default_route_acceptance.get('active_frames')}",
                f"- Route check count: {default_route_acceptance.get('route_check_count')}",
                f"- Route failed checks: {default_route_acceptance.get('route_failed_checks')}",
            ]
        )
    if registration_admission:
        lines.extend(
            [
                "",
                "## Registration Admission",
                "",
                (
                    "- Registration admission: "
                    f"{registration_admission.get('status')} "
                    f"passed={registration_admission.get('passed')} "
                    f"blocked={registration_admission.get('blocked')}"
                ),
                f"- Reference frame: {registration_admission.get('reference_frame_id')}",
                f"- Quality gate status: {registration_admission.get('quality_gate_status')}",
                f"- Quality gate enforced: {registration_admission.get('quality_gate_enforced')}",
                (
                    "- Fallback/override: "
                    f"fallback={registration_admission.get('reference_selection_fallback')} "
                    "allow_quality_rejected_reference="
                    f"{registration_admission.get('allow_quality_rejected_reference')}"
                ),
                f"- Reason: {registration_admission.get('reason')}",
                (
                    "- Admission rows: "
                    f"total={registration_admission.get('registration_row_count')} "
                    "quality_reference_admission="
                    f"{registration_admission.get('quality_reference_admission_row_count')} "
                    f"quality_rejected={registration_admission.get('quality_rejected_row_count')}"
                ),
            ]
        )
    if quality_saturation:
        lines.extend(
            [
                "",
                "## Quality Saturation",
                "",
                (
                    "- Quality saturation: "
                    f"{quality_saturation.get('status')} "
                    f"passed={quality_saturation.get('passed')}"
                ),
                (
                    "- Frames: "
                    f"total={quality_saturation.get('frame_count')} "
                    f"saturated={quality_saturation.get('saturated_frame_count')} "
                    "saturation_rejected="
                    f"{quality_saturation.get('quality_gate_saturation_rejected_count')}"
                ),
                (
                    "- Saturation fraction: "
                    f"max={quality_saturation.get('max_saturation_fraction')} "
                    f"mean={quality_saturation.get('mean_saturation_fraction')} "
                    f"policy={quality_saturation.get('max_saturation_fraction_policy')}"
                ),
                (
                    "- Saturation threshold/source: "
                    f"level={quality_saturation.get('saturation_level')} "
                    f"sources={quality_saturation.get('saturation_sources')}"
                ),
                f"- Worst frame: {quality_saturation.get('worst_frame_id')}",
                f"- Rejected frames: {quality_saturation.get('rejected_frame_ids')}",
            ]
        )
    if quality_metrics:
        lines.extend(
            [
                "",
                "## Quality Metrics",
                "",
                (
                    "- Quality metrics: "
                    f"{quality_metrics.get('status')} "
                    f"metrics={quality_metrics.get('metric_count')} "
                    f"frames={quality_metrics.get('frame_count')}"
                ),
            ]
        )
        for item in quality_metrics.get("summary_rows") or []:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- "
                f"{item.get('metric')}: "
                f"median={item.get('median')} "
                f"mean={item.get('mean')} "
                f"worst={item.get('worst_frame_id')}({item.get('worst_value')}) "
                f"bad_direction={item.get('bad_direction')}"
            )
    if quality_compare:
        lines.extend(
            [
                "",
                "## Quality Metrics Compare",
                "",
                (
                    "- Quality metrics compare: "
                    f"{quality_compare.get('status')} "
                    f"passed={quality_compare.get('passed')}"
                ),
                (
                    "- Metric counts: "
                    f"baseline={quality_compare.get('baseline_metric_count')} "
                    f"candidate={quality_compare.get('candidate_metric_count')} "
                    f"rows={quality_compare.get('metric_row_count')}"
                ),
                (
                    "- Failed checks: "
                    f"count={quality_compare.get('failed_check_count')} "
                    f"names={quality_compare.get('failed_checks')}"
                ),
                (
                    "- Threshold failures: "
                    f"count={quality_compare.get('threshold_failure_count')} "
                    f"items={quality_compare.get('threshold_failures')}"
                ),
            ]
        )
    if doctor:
        lines.extend(
            [
                "",
                "## CUDA",
                "",
                f"- CUDA available: {doctor.get('cuda_available')}",
                f"- Native extension loaded: {doctor.get('native_extension_loaded')}",
                f"- Primary GPU: {doctor.get('primary_gpu')}",
                f"- Compute capability: {doctor.get('compute_capability')}",
                f"- VRAM MiB: {doctor.get('vram_mib')}",
                f"- Driver: {doctor.get('driver_version')}",
            ]
        )
    if release:
        lines.extend(
            [
                "",
                "## Windows Release",
                "",
                f"- Manifest status: {release.get('status')}",
                f"- Package count: {release.get('package_count')}",
                f"- Recommendation: {release.get('recommendation')}",
            ]
        )
    if github_plan:
        lines.extend(
            [
                "",
                "## GitHub Release Plan",
                "",
                f"- Plan status: {github_plan.get('status')}",
                f"- Tag: {github_plan.get('tag')}",
                f"- Publication ready: {github_plan.get('publication_ready')}",
                f"- GitHub auth OK: {github_plan.get('gh_auth_ok')}",
                f"- Script path: {github_plan.get('script_path')}",
            ]
        )
    if preflight:
        lines.extend(
            [
                "",
                "## Windows Publish Preflight",
                "",
                f"- Preflight status: {preflight.get('status')}",
                f"- Passed: {preflight.get('passed')}",
                f"- Recommendation: {preflight.get('recommendation')}",
                f"- Release tag: {preflight.get('release_tag')}",
                f"- Assets/packages: {preflight.get('asset_count')}/{preflight.get('package_count')}",
                f"- Primary package: {preflight.get('primary_package')}",
                f"- Try order: {preflight.get('ordered_try_list')}",
                f"- Default promotion: {preflight.get('default_promotion_status')}",
                f"- Default route checks: {preflight.get('default_route_check_count')}",
                (
                    "- Default route speedup vs reference: "
                    f"{preflight.get('default_route_speedup_vs_reference')}"
                ),
                (
                    "- Rejection sample accounting statuses: "
                    f"phase2={preflight.get('github_plan_phase2_rejection_sample_accounting_status')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_rejection_sample_accounting_status')}, "
                    f"matrix={preflight.get('matrix_rejection_sample_accounting_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_rejection_sample_accounting_status')}"
                ),
                (
                    "- Rejection sample accounting checks: "
                    f"phase2={preflight.get('github_plan_phase2_rejection_sample_accounting_passed')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_rejection_sample_accounting_passed')}, "
                    f"matrix={preflight.get('matrix_rejection_sample_accounting_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_rejection_sample_accounting_passed')}, "
                    "matrix-match="
                    f"{preflight.get('github_plan_matrix_rejection_accounting_matches_matrix')}"
                ),
                (
                    "- Sample accounting closure statuses: "
                    f"phase2={preflight.get('github_plan_phase2_sample_accounting_closure_status')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_sample_accounting_closure_status')}, "
                    f"matrix={preflight.get('matrix_sample_accounting_closure_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_sample_accounting_closure_status')}"
                ),
                (
                    "- Sample accounting closure checks: "
                    f"phase2={preflight.get('github_plan_phase2_sample_accounting_closure_passed')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_sample_accounting_closure_passed')}, "
                    f"matrix={preflight.get('matrix_sample_accounting_closure_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_sample_accounting_closure_passed')}, "
                    "matrix-match="
                    f"{preflight.get('github_plan_matrix_sample_closure_matches_matrix')}"
                ),
                (
                    "- Integration engine policy statuses: "
                    f"matrix-ready={preflight.get('matrix_integration_engine_policy_ready')}, "
                    "matrix-acceptance="
                    f"{preflight.get('matrix_acceptance_integration_engine_policy_status')}, "
                    "matrix-pipeline="
                    f"{preflight.get('matrix_pipeline_integration_engine_policy_status')}, "
                    "default-promotion-ready="
                    f"{preflight.get('default_promotion_integration_engine_policy_ready')}, "
                    "default-promotion-acceptance="
                    f"{preflight.get('default_promotion_acceptance_integration_engine_policy_status')}, "
                    "default-promotion-pipeline="
                    f"{preflight.get('default_promotion_pipeline_integration_engine_policy_status')}"
                ),
                (
                    "- Integration engine policy checks: "
                    "matrix-acceptance="
                    f"{preflight.get('windows_release_matrix_acceptance_integration_engine_policy_passed')}, "
                    "matrix-pipeline="
                    f"{preflight.get('windows_release_matrix_pipeline_integration_engine_policy_passed')}, "
                    "default-promotion-acceptance="
                    f"{preflight.get('default_promotion_acceptance_integration_engine_policy_passed')}, "
                    "default-promotion-pipeline="
                    f"{preflight.get('default_promotion_pipeline_integration_engine_policy_passed')}, "
                    "agreement="
                    f"{preflight.get('matrix_integration_engine_policy_matches_default_promotion')}"
                ),
                (
                    "- StackEngine default contract statuses: "
                    f"phase2={preflight.get('github_plan_phase2_stack_engine_contract_status')}, "
                    f"plan-matrix={preflight.get('github_plan_matrix_stack_engine_contract_status')}, "
                    f"matrix={preflight.get('matrix_stack_engine_contract_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_contract_status')}"
                ),
                (
                    "- StackEngine default contract checks: "
                    "phase2="
                    f"{preflight.get('github_plan_phase2_stack_engine_default_contract_ready')}, "
                    "plan-matrix="
                    f"{preflight.get('github_plan_matrix_stack_engine_contract_ready')}, "
                    "agreement="
                    f"{preflight.get('github_plan_stack_engine_contract_agreement_passed')}, "
                    f"matrix={preflight.get('matrix_stack_engine_contract_ready')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_contract_ready')}, "
                    "plan-matrix-match="
                    f"{preflight.get('github_plan_matrix_stack_engine_contract_matches_matrix')}, "
                    "default-promotion-match="
                    f"{preflight.get('matrix_stack_engine_contract_matches_default_promotion')}"
                ),
                (
                    "- StackEngine default gaps: "
                    f"matrix={preflight.get('matrix_stack_engine_contract_default_gap_count')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_contract_default_gap_count')}"
                ),
                (
                    "- StackEngine runtime default statuses: "
                    f"matrix-ready={preflight.get('matrix_stack_engine_runtime_default_ready')}, "
                    "matrix-acceptance="
                    f"{preflight.get('matrix_acceptance_stack_engine_runtime_default_status')}, "
                    "matrix-pipeline="
                    f"{preflight.get('matrix_pipeline_stack_engine_runtime_default_status')}, "
                    "default-promotion-ready="
                    f"{preflight.get('default_promotion_stack_engine_runtime_default_ready')}, "
                    "default-promotion-acceptance="
                    f"{preflight.get('default_promotion_acceptance_stack_engine_runtime_default_status')}, "
                    "default-promotion-pipeline="
                    f"{preflight.get('default_promotion_pipeline_stack_engine_runtime_default_status')}"
                ),
                (
                    "- StackEngine runtime default checks: "
                    "matrix-acceptance="
                    f"{preflight.get('windows_release_matrix_acceptance_stack_engine_runtime_default_passed')}, "
                    "matrix-pipeline="
                    f"{preflight.get('windows_release_matrix_pipeline_stack_engine_runtime_default_passed')}, "
                    "default-promotion-acceptance="
                    f"{preflight.get('default_promotion_acceptance_stack_engine_runtime_default_passed')}, "
                    "default-promotion-pipeline="
                    f"{preflight.get('default_promotion_pipeline_stack_engine_runtime_default_passed')}, "
                    "agreement="
                    f"{preflight.get('matrix_stack_engine_runtime_default_matches_default_promotion')}"
                ),
                (
                    "- StackEngine runtime default drift counters: "
                    "matrix-legacy="
                    f"{preflight.get('matrix_stack_engine_runtime_default_acceptance_legacy_master_count')}, "
                    "matrix-failed-outputs="
                    f"{preflight.get('matrix_stack_engine_runtime_default_pipeline_failed_output_count')}, "
                    "default-legacy="
                    f"{preflight.get('default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count')}, "
                    "default-failed-outputs="
                    f"{preflight.get('default_promotion_stack_engine_runtime_default_pipeline_failed_output_count')}"
                ),
                (
                    "- Direct runtime evidence: "
                    f"matrix-ready={preflight.get('matrix_direct_runtime_evidence_ready')} "
                    f"matrix-source={preflight.get('matrix_direct_runtime_acceptance_source')} "
                    f"matrix-calibration={preflight.get('matrix_direct_runtime_pipeline_calibration_source')} "
                    f"matrix-lights={preflight.get('matrix_direct_runtime_pipeline_resident_lights')} "
                    "default-ready="
                    f"{preflight.get('default_promotion_direct_runtime_evidence_ready')} "
                    "default-source="
                    f"{preflight.get('default_promotion_direct_runtime_acceptance_source')} "
                    "default-calibration="
                    f"{preflight.get('default_promotion_direct_runtime_pipeline_calibration_source')} "
                    "default-lights="
                    f"{preflight.get('default_promotion_direct_runtime_pipeline_resident_lights')}"
                ),
                (
                    "- Direct runtime checks: "
                    "matrix-acceptance="
                    f"{preflight.get('windows_release_matrix_direct_acceptance_fastpath_evidence')}, "
                    "matrix-calibration="
                    f"{preflight.get('windows_release_matrix_direct_pipeline_calibration_evidence')}, "
                    "default-acceptance="
                    f"{preflight.get('default_promotion_direct_acceptance_fastpath_evidence')}, "
                    "default-calibration="
                    f"{preflight.get('default_promotion_direct_pipeline_calibration_evidence')}, "
                    "agreement="
                    f"{preflight.get('matrix_direct_runtime_evidence_matches_default_promotion')}"
                ),
                (
                    "- Release direct publication guard evidence: "
                    "plan-matrix="
                    f"{preflight.get('github_plan_matrix_release_direct_publication_guard_ready')}/"
                    f"{preflight.get('github_plan_matrix_release_direct_publication_guard_lights')}, "
                    "plan-default="
                    f"{preflight.get('github_plan_matrix_default_promotion_release_direct_publication_guard_ready')}/"
                    f"{preflight.get('github_plan_matrix_default_promotion_release_direct_publication_guard_lights')}, "
                    "matrix="
                    f"{preflight.get('matrix_release_direct_publication_guard_ready')}/"
                    f"{preflight.get('matrix_release_direct_publication_guard_lights')} "
                    "source="
                    f"{preflight.get('matrix_release_direct_publication_guard_source_ready')} "
                    "count="
                    f"{preflight.get('matrix_release_direct_publication_guard_count_ready')} "
                    "check="
                    f"{preflight.get('matrix_release_direct_publication_guard_check_passed')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_direct_publication_guard_ready')}/"
                    f"{preflight.get('matrix_default_promotion_release_direct_publication_guard_lights')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_direct_publication_guard_ready')}/"
                    f"{preflight.get('default_promotion_release_direct_publication_guard_lights')}"
                ),
                (
                    "- Release direct publication guard checks: "
                    "plan-matrix="
                    f"{preflight.get('github_plan_matrix_release_decision_direct_publication_guard_passed')}, "
                    "plan-default="
                    f"{preflight.get('github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed')}, "
                    "plan-matrix-match="
                    f"{preflight.get('github_plan_matrix_release_decision_direct_publication_guard_matches_matrix')}, "
                    "plan-default-match="
                    f"{preflight.get('github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix')}, "
                    "matrix="
                    f"{preflight.get('matrix_release_decision_direct_runtime_publication_guard_passed')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_decision_direct_runtime_publication_guard_passed')}, "
                    "matrix-default-match="
                    f"{preflight.get('matrix_release_decision_direct_publication_guard_matches_default_promotion')}, "
                    "matrix-manifest-match="
                    f"{preflight.get('matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest')}"
                ),
                (
                    "- Release quality publication guard evidence: "
                    "matrix="
                    f"{preflight.get('matrix_release_quality_publication_guard_present')}/"
                    f"{preflight.get('matrix_release_quality_publication_guard_ready')}/"
                    f"{preflight.get('matrix_release_quality_publication_guard_raw_status')}/"
                    f"{preflight.get('matrix_release_quality_publication_guard_phase2_status')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_quality_publication_guard_ready')}/"
                    f"{preflight.get('matrix_default_promotion_release_quality_publication_guard_raw_status')}/"
                    f"{preflight.get('matrix_default_promotion_release_quality_publication_guard_phase2_status')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_quality_publication_guard_present')}/"
                    f"{preflight.get('default_promotion_release_quality_publication_guard_ready')}/"
                    f"{preflight.get('default_promotion_release_quality_publication_guard_raw_status')}/"
                    f"{preflight.get('default_promotion_release_quality_publication_guard_phase2_status')}"
                ),
                (
                    "- Release quality publication guard checks: "
                    "matrix="
                    f"{preflight.get('matrix_release_decision_quality_compare_publication_guard_passed')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_decision_quality_compare_publication_guard_passed')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_decision_quality_compare_publication_guard_passed')}, "
                    "matrix-default-match="
                    f"{preflight.get('matrix_release_decision_quality_publication_guard_matches_default_promotion')}, "
                    "matrix-manifest-match="
                    f"{preflight.get('matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest')}"
                ),
                (
                    "- Release quality publication guard final checks: "
                    "matrix="
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_passed')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_passed')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_passed')}, "
                    "matrix-default-match="
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_matches_default_promotion')}, "
                    "matrix-manifest-match="
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest')}"
                ),
                (
                    "- Release quality publication guard final evidence: "
                    "matrix="
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_final_checks_ready')}/"
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_final_checks_match')}/"
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_raw_final_checks_ready')}/"
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_phase2_final_checks_ready')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_ready')}/"
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_final_checks_match')}/"
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready')}/"
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_final_checks_ready')}/"
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_final_checks_match')}/"
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_raw_final_checks_ready')}/"
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_phase2_final_checks_ready')}"
                ),
                (
                    "- Release quality publication guard final evidence detail: "
                    "matrix="
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_final_evidence_ready')}/"
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_final_evidence_match')}/"
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_raw_final_evidence_ready')}/"
                    f"{preflight.get('matrix_release_decision_release_quality_publication_guard_phase2_final_evidence_ready')}, "
                    "matrix-default="
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready')}/"
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_final_evidence_match')}/"
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready')}/"
                    f"{preflight.get('matrix_default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready')}, "
                    "default="
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_final_evidence_ready')}/"
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_final_evidence_match')}/"
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_raw_final_evidence_ready')}/"
                    f"{preflight.get('default_promotion_release_decision_release_quality_publication_guard_phase2_final_evidence_ready')}"
                ),
                (
                    "- Resident winsorized sweep statuses: "
                    f"matrix={preflight.get('matrix_resident_winsorized_sweep_status')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_status')}"
                ),
                (
                    "- Resident winsorized sweep required frame: "
                    f"matrix={preflight.get('matrix_resident_winsorized_sweep_required_frame_count')}/"
                    f"{preflight.get('matrix_resident_winsorized_sweep_required_frame_count_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_required_frame_count')}/"
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_required_frame_count_passed')}"
                ),
                (
                    "- Resident winsorized sweep checks: "
                    f"matrix-count={preflight.get('matrix_resident_winsorized_sweep_check_count')}, "
                    "default-promotion-count="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_check_count')}, "
                    f"matrix-audit={preflight.get('matrix_resident_winsorized_sweep_audit_passed')}, "
                    "matrix-frame="
                    f"{preflight.get('matrix_resident_winsorized_required_frame_passed')}, "
                    "matrix-count-check="
                    f"{preflight.get('matrix_resident_winsorized_sweep_check_count_passed')}, "
                    "default-promotion-audit="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_audit_passed')}, "
                    "default-promotion-frame="
                    f"{preflight.get('default_promotion_resident_winsorized_required_frame_passed')}, "
                    "default-promotion-match="
                    f"{preflight.get('default_promotion_resident_winsorized_sweep_matches_matrix')}"
                ),
                (
                    "- Resident fastpath handoff: "
                    "plan-matrix="
                    f"{preflight.get('github_plan_matrix_resident_fastpath_handoff_ready')}/"
                    f"{preflight.get('github_plan_matrix_resident_fastpath_handoff_raw_status')}/"
                    f"{preflight.get('github_plan_matrix_resident_fastpath_handoff_raw_check_count')}, "
                    "matrix="
                    f"{preflight.get('matrix_resident_fastpath_handoff_ready')}/"
                    f"{preflight.get('matrix_resident_fastpath_handoff_raw_status')}/"
                    f"{preflight.get('matrix_resident_fastpath_handoff_raw_check_count')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_resident_fastpath_handoff_ready')}/"
                    f"{preflight.get('default_promotion_resident_fastpath_handoff_raw_status')}/"
                    f"{preflight.get('default_promotion_resident_fastpath_handoff_raw_check_count')}"
                ),
                (
                    "- Resident fastpath handoff checks: "
                    "plan-matrix="
                    f"{preflight.get('github_plan_matrix_resident_fastpath_release_handoff_ready')}, "
                    "matrix="
                    f"{preflight.get('matrix_resident_fastpath_release_handoff_ready')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_resident_fastpath_release_handoff_ready')}, "
                    "plan-matrix-match="
                    f"{preflight.get('github_plan_matrix_resident_fastpath_handoff_matches_matrix')}, "
                    "matrix-default-match="
                    f"{preflight.get('matrix_resident_fastpath_handoff_matches_default_promotion')}"
                ),
                (
                    "- StackEngine publication audit statuses: "
                    f"matrix={preflight.get('matrix_stack_engine_publication_audit_status')}/"
                    f"{preflight.get('matrix_stack_engine_publication_audit_ready')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_stack_engine_publication_audit_status')}/"
                    f"{preflight.get('default_promotion_stack_engine_publication_audit_ready')}"
                ),
                (
                    "- StackEngine publication audit chains: "
                    "matrix-policy="
                    f"{preflight.get('matrix_stack_engine_publication_policy_agreement')}, "
                    "matrix-resident-winsorized="
                    f"{preflight.get('matrix_stack_engine_publication_resident_winsorized_agreement')}, "
                    "default-policy="
                    f"{preflight.get('default_promotion_stack_engine_publication_policy_agreement')}, "
                    "default-resident-winsorized="
                    f"{preflight.get('default_promotion_stack_engine_publication_resident_winsorized_agreement')}"
                ),
                (
                    "- StackEngine publication audit checks: "
                    f"matrix-audit={preflight.get('matrix_stack_engine_publication_audit_passed')}, "
                    "matrix-policy="
                    f"{preflight.get('matrix_stack_engine_publication_policy_chain_passed')}, "
                    "matrix-resident-winsorized="
                    f"{preflight.get('matrix_stack_engine_publication_resident_winsorized_chain_passed')}, "
                    "default-audit="
                    f"{preflight.get('default_promotion_stack_engine_publication_audit_passed')}, "
                    "default-policy="
                    f"{preflight.get('default_promotion_stack_engine_publication_policy_chain_passed')}, "
                    "default-resident-winsorized="
                    f"{preflight.get('default_promotion_stack_engine_publication_resident_winsorized_chain_passed')}, "
                    "agreement="
                    f"{preflight.get('matrix_stack_engine_publication_audit_matches_default_promotion')}"
                ),
                (
                    "- Quality metrics compare handoff: "
                    f"matrix={preflight.get('matrix_quality_metrics_compare_status')}/"
                    f"{preflight.get('matrix_quality_metrics_compare_ready')}/"
                    f"{preflight.get('matrix_quality_metrics_compare_failed_check_count')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_quality_metrics_compare_status')}/"
                    f"{preflight.get('default_promotion_quality_metrics_compare_ready')}/"
                    f"{preflight.get('default_promotion_quality_metrics_compare_failed_check_count')}"
                ),
                (
                    "- Quality metrics compare checks: "
                    "matrix="
                    f"{preflight.get('windows_release_matrix_quality_metrics_compare_handoff_passed')}, "
                    "default-promotion="
                    f"{preflight.get('default_promotion_quality_metrics_compare_handoff_passed')}, "
                    "agreement="
                    f"{preflight.get('matrix_quality_metrics_compare_matches_default_promotion')}"
                ),
            ]
        )
    if publication_audit:
        lines.extend(
            [
                "",
                "## StackEngine Publication Audit",
                "",
                f"- Status: {publication_audit.get('status')}",
                f"- Passed: {publication_audit.get('passed')}",
                f"- Recommendation: {publication_audit.get('recommendation')}",
                f"- Layers/checks: {publication_audit.get('layer_count')}/{publication_audit.get('check_count')}",
                f"- Failed checks: {publication_audit.get('failed_checks')}",
                (
                    "- Publish-preflight policy layer: "
                    f"{publication_audit.get('publish_preflight_integration_engine_policy')}"
                ),
                (
                    "- Phase2 policy layer: "
                    f"{publication_audit.get('phase2_publish_preflight_integration_engine_policy')}"
                ),
                (
                    "- Policy checks: "
                    f"raw={publication_audit.get('publish_preflight_integration_engine_policy_ready')}, "
                    f"phase2={publication_audit.get('phase2_publish_preflight_integration_engine_policy_ready')}, "
                    "agreement="
                    f"{publication_audit.get('phase2_publish_preflight_integration_engine_policy_matches_publish_preflight')}"
                ),
                (
                    "- Direct runtime layers: "
                    f"raw={publication_audit.get('publish_preflight_direct_runtime_evidence')}, "
                    "phase2="
                    f"{publication_audit.get('phase2_publish_preflight_direct_runtime_evidence')}"
                ),
                (
                    "- Direct runtime checks: "
                    f"raw={publication_audit.get('publish_preflight_direct_runtime_evidence_ready')}, "
                    f"phase2={publication_audit.get('phase2_publish_preflight_direct_runtime_evidence_ready')}, "
                    "agreement="
                    f"{publication_audit.get('phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight')}"
                ),
                (
                    "- Resident winsorized layers: "
                    f"raw={publication_audit.get('publish_preflight_resident_winsorized_sweep')}, "
                    "phase2="
                    f"{publication_audit.get('phase2_publish_preflight_resident_winsorized_sweep')}"
                ),
                (
                    "- Resident winsorized checks: "
                    f"raw={publication_audit.get('publish_preflight_resident_winsorized_sweep_ready')}, "
                    f"phase2={publication_audit.get('phase2_publish_preflight_resident_winsorized_sweep_ready')}, "
                    "agreement="
                    f"{publication_audit.get('phase2_publish_preflight_resident_winsorized_matches_publish_preflight')}"
                ),
                (
                    "- Resident result-contract layers: "
                    f"raw={publication_audit.get('publish_preflight_resident_result_contract')}, "
                    "phase2="
                    f"{publication_audit.get('phase2_publish_preflight_resident_result_contract')}"
                ),
                (
                    "- Resident result-contract checks: "
                    f"raw={publication_audit.get('publish_preflight_resident_result_contract_ready')}, "
                    f"phase2={publication_audit.get('phase2_publish_preflight_resident_result_contract_ready')}, "
                    "agreement="
                    f"{publication_audit.get('phase2_publish_preflight_resident_result_contract_matches_publish_preflight')}"
                ),
            ]
        )
    if pipeline:
        lines.extend(
            [
                "",
                "## Pipeline Contract",
                "",
                f"- Status: {pipeline.get('status')}",
                f"- Passed: {pipeline.get('passed')}",
                f"- Check count: {pipeline.get('check_count')}",
                f"- Failed checks: {pipeline.get('failed_check_count')}",
                f"- Integration outputs: {pipeline.get('integration_output_count')}",
                f"- Integration maps: {pipeline.get('integration_map_count')}",
                f"- Integration DQ contract: {pipeline.get('integration_dq_contract')}",
                (
                    "- Integration StackEngine result contract: "
                    f"{pipeline.get('integration_stack_result_contract')}"
                ),
                (
                    "- Integration resident result contract: "
                    f"{pipeline.get('integration_resident_result_contract')}"
                ),
                (
                    "- Integration resident result detail: "
                    f"{pipeline.get('integration_resident_result_contract_status')} "
                    f"check={pipeline.get('integration_resident_result_contract_check_passed')} "
                    f"required={pipeline.get('integration_resident_result_contract_required_count')} "
                    f"failed={pipeline.get('integration_resident_result_contract_failed_count')} "
                    "failed_checks="
                    f"{pipeline.get('integration_resident_result_contract_failed_checks')}"
                ),
                (
                    "- Integration engine policy: "
                    f"{pipeline.get('integration_engine_policy_status')} "
                    f"check={pipeline.get('integration_default_engine_policy')} "
                    f"nonresident={pipeline.get('integration_engine_policy_non_resident_count')} "
                    f"failed={pipeline.get('integration_engine_policy_failed_count')}"
                ),
                (
                    "- StackEngine runtime default: "
                    f"{pipeline.get('stack_engine_runtime_default_status')} "
                    f"check={pipeline.get('stack_engine_runtime_default_check_passed')} "
                    f"legacy={pipeline.get('stack_engine_runtime_default_legacy_master_count')} "
                    f"failed_masters={pipeline.get('stack_engine_runtime_default_failed_master_count')} "
                    f"failed_outputs={pipeline.get('stack_engine_runtime_default_failed_output_count')} "
                    f"explicit_cuda={pipeline.get('stack_engine_runtime_default_explicit_cuda_fast_path_count')}"
                ),
                f"- Pixel verification enabled: {pipeline.get('pixel_verification_enabled')}",
                (
                    "- DQ pixels match summary: "
                    f"{pipeline.get('integration_dq_map_pixels_match_summary')}"
                ),
                (
                    "- Coverage pixels match DQ: "
                    f"{pipeline.get('integration_coverage_map_pixels_match_dq')}"
                ),
                (
                    "- Rejection pixels match DQ: "
                    f"{pipeline.get('integration_rejection_map_pixels_match_dq')}"
                ),
                (
                    "- Rejection sample counts match maps: "
                    f"{pipeline.get('integration_rejection_sample_counts_match_maps')}"
                ),
                (
                    "- Rejection sample accounting: "
                    f"{pipeline.get('rejection_sample_accounting_status')} "
                    f"failed={pipeline.get('rejection_sample_accounting_failed_count')}"
                ),
                (
                    "- Sample accounting closure: "
                    f"{pipeline.get('sample_accounting_closure_status')} "
                    f"present={pipeline.get('sample_accounting_closure_present_count')} "
                    f"failed={pipeline.get('sample_accounting_closure_failed_count')}"
                ),
            ]
        )
        accounting = pipeline.get("rejection_sample_accounting")
        if isinstance(accounting, dict):
            for row in accounting.get("failed_items") or []:
                if not isinstance(row, dict):
                    continue
                source_counts = ", ".join(
                    f"{source.get('name')}={source.get('count')}"
                    for source in row.get("source_counts") or []
                    if isinstance(source, dict)
                )
                failed_matches = "; ".join(
                    (
                        f"{match.get('source')}: actual={match.get('actual')} "
                        f"summary={match.get('summary')} delta={match.get('delta')}"
                    )
                    for match in row.get("failed_matches") or []
                    if isinstance(match, dict)
                )
                lines.append(
                    "- Rejection sample mismatch "
                    f"{row.get('item')}: map_rejected_sample_sum="
                    f"{row.get('map_rejected_sample_sum')} source_counts=[{source_counts}] "
                    f"failed_matches=[{failed_matches}]"
                )
        sample_closure = pipeline.get("sample_accounting_closure")
        if isinstance(sample_closure, dict):
            for row in sample_closure.get("failed_items") or []:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "- Sample closure mismatch "
                    f"{row.get('item')}: status={row.get('status')} "
                    "input_valid_samples_before_rejection="
                    f"{row.get('input_valid_samples_before_rejection')} "
                    "valid_samples_after_rejection="
                    f"{row.get('valid_samples_after_rejection')} "
                    f"rejected_samples={row.get('rejected_samples')} "
                    f"valid_rejection_match={row.get('valid_rejection_match')}"
                )
        runtime_default = pipeline.get("stack_engine_runtime_default")
        if isinstance(runtime_default, dict):
            for row in runtime_default.get("failed_masters") or []:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "- Runtime-default master mismatch "
                    f"{row.get('name')}: mode={row.get('tile_stack_mode')} "
                    f"status={row.get('status')} failures={row.get('failures')}"
                )
            for row in runtime_default.get("failed_outputs") or []:
                if not isinstance(row, dict):
                    continue
                lines.append(
                    "- Runtime-default integration mismatch "
                    f"{row.get('item')}: status={row.get('status')} "
                    f"backend={row.get('backend')} failures={row.get('failures')}"
                )
    if stack_engine:
        lines.extend(
            [
                "",
                "## StackEngine Default Contract",
                "",
                f"- Status: {stack_engine.get('status')}",
                f"- Passed: {stack_engine.get('passed')}",
                f"- Scope: {stack_engine.get('scope')}",
                (
                    "- Expected integration engine: "
                    f"{stack_engine.get('expected_integration_engine')}"
                ),
                (
                    "- Adoption recommendation: "
                    f"{stack_engine.get('adoption_recommendation')}"
                ),
                (
                    "- Adoption surfaces: "
                    f"{stack_engine.get('adoption_surface_count')} "
                    f"ready={stack_engine.get('adoption_contract_ready_count')}"
                ),
                (
                    "- StackEngine/resident surfaces: "
                    f"{stack_engine.get('adoption_stack_engine_surface_count')}/"
                    f"{stack_engine.get('adoption_cuda_resident_surface_count')}"
                ),
                (
                    "- Phase 2 default gaps: "
                    f"{stack_engine.get('adoption_phase2_stack_engine_default_gap_count')}"
                ),
                (
                    "- Default promotion: "
                    f"{stack_engine.get('default_promotion_status')} "
                    f"ready={stack_engine.get('default_promotion_ready')} "
                    f"blockers={stack_engine.get('default_promotion_blocker_count')}"
                ),
            ]
        )
        for blocker in stack_engine.get("default_promotion_blockers") or []:
            if not isinstance(blocker, dict):
                continue
            lines.append(
                f"- StackEngine default blocker {blocker.get('name')}: {blocker}"
            )
    if winsorized_audit:
        lines.extend(
            [
                "",
                "## Resident Winsorized Benchmark Audit",
                "",
                f"- Status: {winsorized_audit.get('status')}",
                f"- Passed: {winsorized_audit.get('passed')}",
                f"- Contract: {winsorized_audit.get('contract_name')}",
                f"- Benchmark: {winsorized_audit.get('benchmark_path')}",
                f"- Check count: {winsorized_audit.get('check_count')}",
                f"- Failed checks: {winsorized_audit.get('failed_checks')}",
                f"- Frame count: {winsorized_audit.get('frame_count')}",
                f"- Shape: {winsorized_audit.get('shape')}",
                f"- Hardened master RMS: {winsorized_audit.get('hardened_master_rms')}",
                (
                    "- Hardened master max abs: "
                    f"{winsorized_audit.get('hardened_master_max_abs')}"
                ),
                (
                    "- Fast approximation master RMS: "
                    f"{winsorized_audit.get('fast_approx_master_rms')}"
                ),
                f"- CUDA hardened seconds: {winsorized_audit.get('cuda_hardened_s')}",
            ]
        )
    if winsorized_sweep_audit:
        lines.extend(
            [
                "",
                "## Resident Winsorized Sweep Audit",
                "",
                f"- Status: {winsorized_sweep_audit.get('status')}",
                f"- Passed: {winsorized_sweep_audit.get('passed')}",
                f"- Contract: {winsorized_sweep_audit.get('contract_name')}",
                f"- Sweep: {winsorized_sweep_audit.get('sweep_path')}",
                f"- Check count: {winsorized_sweep_audit.get('check_count')}",
                f"- Failed checks: {winsorized_sweep_audit.get('failed_checks')}",
                f"- Frame counts: {winsorized_sweep_audit.get('frame_counts')}",
                f"- Run count: {winsorized_sweep_audit.get('run_count')}",
                f"- Required frame count: {winsorized_sweep_audit.get('required_frame_count')}",
                (
                    "- Required frame count passed: "
                    f"{winsorized_sweep_audit.get('required_frame_count_passed')}"
                ),
                (
                    "- Required frame master RMS: "
                    f"{winsorized_sweep_audit.get('required_frame_master_rms')}"
                ),
                (
                    "- Required frame master max abs: "
                    f"{winsorized_sweep_audit.get('required_frame_master_max_abs')}"
                ),
                (
                    "- Max hardened master RMS: "
                    f"{winsorized_sweep_audit.get('max_hardened_master_rms')}"
                ),
                (
                    "- Required frame hardened CUDA seconds: "
                    f"{winsorized_sweep_audit.get('required_frame_cuda_hardened_s')}"
                ),
            ]
        )
    if decision:
        lines.extend(
            [
                "",
                "## Release Decision",
                "",
                f"- Status: {decision.get('status')}",
                f"- Recommendation: {decision.get('recommendation')}",
                f"- Release candidate ready: {decision.get('release_candidate_ready')}",
                f"- Default change ready: {decision.get('default_change_ready')}",
                f"- Speedup: {decision.get('speedup_actual')}",
                f"- Runtime repeat runs: {decision.get('runtime_repeat_run_count')}",
                (
                    "- Runtime repeat ratio vs best: "
                    f"{decision.get('runtime_repeat_elapsed_ratio_vs_best')}"
                ),
                (
                    "- Runtime repeat closure: "
                    f"{runtime_repeat_closure.get('status')} "
                    f"required={runtime_repeat_closure.get('required')} "
                    f"ready={runtime_repeat_closure.get('ready')} "
                    f"runs={runtime_repeat_closure.get('run_count')} "
                    f"considered={runtime_repeat_closure.get('considered_run_count')}"
                ),
                (
                    "- Runtime repeat best: "
                    f"{decision.get('runtime_repeat_best_label')} "
                    f"{decision.get('runtime_repeat_best_elapsed_s')} s"
                ),
                f"- Pipeline handoff source: {decision.get('pipeline_handoff_source')}",
                (
                    "- Pipeline handoff pixel verification: "
                    f"{decision.get('pipeline_handoff_pixel_verification_enabled')}"
                ),
                (
                    "- Warp quality handoff: "
                    f"{decision.get('warp_quality_handoff_status')} "
                    f"ready={decision.get('warp_quality_handoff_ready')} "
                    f"outputs={decision.get('warp_quality_handoff_output_count')} "
                    f"failed={decision.get('warp_quality_handoff_failed_checks')}"
                ),
                (
                    "- Resident fastpath handoff: "
                    f"{decision.get('resident_registration_fastpath_handoff_status')} "
                    f"ready={decision.get('resident_registration_fastpath_handoff_ready')} "
                    f"required={decision.get('resident_registration_fastpath_handoff_required')} "
                    f"checks={decision.get('resident_registration_fastpath_handoff_passed_check_count')} "
                    f"failed={decision.get('resident_registration_fastpath_handoff_failed_check_count')}"
                ),
            ]
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_phase2_status(
    out_json: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, payload)
    if markdown is not None:
        write_phase2_status_markdown(markdown, payload)


def _load_phase2_status(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    payload = read_json(target)
    if not isinstance(payload, dict):
        raise ValueError(f"Phase 2 status artifact must be a JSON object: {target}")
    payload = dict(payload)
    payload["_path"] = str(target)
    return payload


def _status_value(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _int_status_value(payload: dict[str, Any], *keys: str) -> int | None:
    value = _status_value(payload, *keys)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compare_check(
    name: str,
    passed: bool,
    *,
    baseline: Any,
    candidate: Any,
    note: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": {"baseline": baseline, "candidate": candidate},
        "note": note,
    }


_PUBLISH_PREFLIGHT_REJECTION_CHECK_FIELDS = (
    "github_plan_phase2_rejection_sample_accounting_passed",
    "github_plan_matrix_rejection_sample_accounting_passed",
    "matrix_rejection_sample_accounting_passed",
    "default_promotion_rejection_sample_accounting_passed",
    "github_plan_matrix_rejection_accounting_matches_matrix",
)

_PUBLISH_PREFLIGHT_REJECTION_STATUS_FIELDS = (
    "github_plan_phase2_rejection_sample_accounting_status",
    "github_plan_matrix_rejection_sample_accounting_status",
    "matrix_rejection_sample_accounting_status",
    "default_promotion_rejection_sample_accounting_status",
)


_PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_CHECK_FIELDS = (
    "github_plan_phase2_sample_accounting_closure_passed",
    "github_plan_matrix_sample_accounting_closure_passed",
    "matrix_sample_accounting_closure_passed",
    "default_promotion_sample_accounting_closure_passed",
    "github_plan_matrix_sample_closure_matches_matrix",
)

_PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_STATUS_FIELDS = (
    "github_plan_phase2_sample_accounting_closure_status",
    "github_plan_matrix_sample_accounting_closure_status",
    "matrix_sample_accounting_closure_status",
    "default_promotion_sample_accounting_closure_status",
)


_PUBLISH_PREFLIGHT_ENGINE_POLICY_CHECK_FIELDS = (
    "windows_release_matrix_acceptance_integration_engine_policy_passed",
    "windows_release_matrix_pipeline_integration_engine_policy_passed",
    "default_promotion_acceptance_integration_engine_policy_passed",
    "default_promotion_pipeline_integration_engine_policy_passed",
    "matrix_integration_engine_policy_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_ENGINE_POLICY_STATUS_FIELDS = (
    "matrix_integration_engine_policy_ready",
    "matrix_acceptance_integration_engine_policy_status",
    "matrix_pipeline_integration_engine_policy_status",
    "default_promotion_integration_engine_policy_ready",
    "default_promotion_acceptance_integration_engine_policy_status",
    "default_promotion_pipeline_integration_engine_policy_status",
)


_PUBLISH_PREFLIGHT_STACK_ENGINE_CHECK_FIELDS = (
    "github_plan_phase2_stack_engine_default_contract_ready",
    "github_plan_matrix_stack_engine_contract_ready",
    "github_plan_stack_engine_contract_agreement_passed",
    "matrix_stack_engine_contract_ready",
    "default_promotion_stack_engine_contract_ready",
    "github_plan_matrix_stack_engine_contract_matches_matrix",
    "matrix_stack_engine_contract_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_STACK_ENGINE_STATUS_FIELDS = (
    "github_plan_phase2_stack_engine_contract_status",
    "github_plan_matrix_stack_engine_contract_status",
    "matrix_stack_engine_contract_status",
    "default_promotion_stack_engine_contract_status",
)

_PUBLISH_PREFLIGHT_RUNTIME_DEFAULT_CHECK_FIELDS = (
    "windows_release_matrix_acceptance_stack_engine_runtime_default_passed",
    "windows_release_matrix_pipeline_stack_engine_runtime_default_passed",
    "default_promotion_acceptance_stack_engine_runtime_default_passed",
    "default_promotion_pipeline_stack_engine_runtime_default_passed",
    "matrix_stack_engine_runtime_default_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_RUNTIME_DEFAULT_STATUS_FIELDS = (
    "matrix_stack_engine_runtime_default_ready",
    "matrix_acceptance_stack_engine_runtime_default_status",
    "matrix_pipeline_stack_engine_runtime_default_status",
    "matrix_stack_engine_runtime_default_acceptance_legacy_master_count",
    "matrix_stack_engine_runtime_default_pipeline_failed_output_count",
    "default_promotion_stack_engine_runtime_default_ready",
    "default_promotion_acceptance_stack_engine_runtime_default_status",
    "default_promotion_pipeline_stack_engine_runtime_default_status",
    "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count",
    "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count",
)

_PUBLISH_PREFLIGHT_DIRECT_RUNTIME_CHECK_FIELDS = (
    "windows_release_matrix_direct_acceptance_fastpath_evidence",
    "windows_release_matrix_direct_pipeline_calibration_evidence",
    "default_promotion_direct_acceptance_fastpath_evidence",
    "default_promotion_direct_pipeline_calibration_evidence",
    "matrix_direct_runtime_evidence_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_DIRECT_RUNTIME_STATUS_FIELDS = (
    "matrix_direct_runtime_evidence_ready",
    "matrix_direct_runtime_acceptance_source",
    "matrix_direct_runtime_acceptance_check_count",
    "matrix_direct_runtime_pipeline_calibration_source",
    "matrix_direct_runtime_pipeline_resident_lights",
    "default_promotion_direct_runtime_evidence_ready",
    "default_promotion_direct_runtime_acceptance_source",
    "default_promotion_direct_runtime_acceptance_check_count",
    "default_promotion_direct_runtime_pipeline_calibration_source",
    "default_promotion_direct_runtime_pipeline_resident_lights",
)

_PUBLISH_PREFLIGHT_RELEASE_DIRECT_PUBLICATION_GUARD_CHECK_FIELDS = (
    "github_plan_matrix_release_decision_direct_publication_guard_passed",
    "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_passed",
    "github_plan_matrix_release_decision_direct_publication_guard_matches_matrix",
    "github_plan_matrix_default_promotion_release_decision_direct_publication_guard_matches_matrix",
    "matrix_release_decision_direct_runtime_publication_guard_passed",
    "matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed",
    "default_promotion_release_decision_direct_runtime_publication_guard_passed",
    "matrix_release_decision_direct_publication_guard_matches_default_promotion",
    "matrix_default_promotion_release_decision_direct_publication_guard_matches_manifest",
)

_PUBLISH_PREFLIGHT_RELEASE_DIRECT_PUBLICATION_GUARD_STATUS_FIELDS = (
    "github_plan_matrix_release_direct_publication_guard_ready",
    "github_plan_matrix_release_direct_publication_guard_lights",
    "github_plan_matrix_default_promotion_release_direct_publication_guard_ready",
    "github_plan_matrix_default_promotion_release_direct_publication_guard_lights",
    "matrix_release_direct_publication_guard_ready",
    "matrix_release_direct_publication_guard_source_ready",
    "matrix_release_direct_publication_guard_count_ready",
    "matrix_release_direct_publication_guard_check_passed",
    "matrix_release_direct_publication_guard_lights",
    "matrix_default_promotion_release_direct_publication_guard_ready",
    "matrix_default_promotion_release_direct_publication_guard_lights",
    "default_promotion_release_direct_publication_guard_ready",
    "default_promotion_release_direct_publication_guard_lights",
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_CHECK_FIELDS = (
    "matrix_release_decision_quality_compare_publication_guard_passed",
    "matrix_default_promotion_release_decision_quality_compare_publication_guard_passed",
    "default_promotion_release_decision_quality_compare_publication_guard_passed",
    "matrix_release_decision_quality_publication_guard_matches_default_promotion",
    "matrix_default_promotion_release_decision_quality_publication_guard_matches_manifest",
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_CHECK_FIELDS = (
    "matrix_release_decision_release_quality_publication_guard_passed",
    "matrix_default_promotion_release_decision_release_quality_publication_guard_passed",
    "default_promotion_release_decision_release_quality_publication_guard_passed",
    "matrix_release_decision_release_quality_publication_guard_matches_default_promotion",
    "matrix_default_promotion_release_decision_release_quality_publication_guard_matches_manifest",
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_PREFIXES = (
    "matrix_release_decision_release_quality_publication_guard",
    "matrix_default_promotion_release_decision_release_quality_publication_guard",
    "default_promotion_release_decision_release_quality_publication_guard",
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_LEGACY_FINAL_EVIDENCE_SUFFIXES = (
    "final_checks_ready",
    "final_checks_match",
    "raw_final_checks_ready",
    "phase2_final_checks_ready",
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_LEGACY_FINAL_EVIDENCE_FIELDS = tuple(
    f"{prefix}_{suffix}"
    for prefix in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_PREFIXES
    for suffix in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_LEGACY_FINAL_EVIDENCE_SUFFIXES
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_DETAIL_SUFFIXES = (
    "final_evidence_ready",
    "final_evidence_match",
    "raw_final_evidence_ready",
    "phase2_final_evidence_ready",
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_DETAIL_FIELDS = tuple(
    f"{prefix}_{suffix}"
    for prefix in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_PREFIXES
    for suffix in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_DETAIL_SUFFIXES
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_FIELDS = (
    *_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_LEGACY_FINAL_EVIDENCE_FIELDS,
    *_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_DETAIL_FIELDS,
)

_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_STATUS_FIELDS = (
    "matrix_release_quality_publication_guard_present",
    "matrix_release_quality_publication_guard_ready",
    "matrix_release_quality_publication_guard_check_passed",
    "matrix_release_quality_publication_guard_layers_ready",
    "matrix_release_quality_publication_guard_raw_status",
    "matrix_release_quality_publication_guard_phase2_status",
    "matrix_default_promotion_release_quality_publication_guard_ready",
    "matrix_default_promotion_release_quality_publication_guard_raw_status",
    "matrix_default_promotion_release_quality_publication_guard_phase2_status",
    "default_promotion_release_quality_publication_guard_present",
    "default_promotion_release_quality_publication_guard_ready",
    "default_promotion_release_quality_publication_guard_check_passed",
    "default_promotion_release_quality_publication_guard_layers_ready",
    "default_promotion_release_quality_publication_guard_raw_status",
    "default_promotion_release_quality_publication_guard_phase2_status",
    *_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_CHECK_FIELDS,
    *_PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_FIELDS,
)

_PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_CHECK_FIELDS = (
    "matrix_resident_winsorized_sweep_audit_passed",
    "matrix_resident_winsorized_required_frame_passed",
    "matrix_resident_winsorized_sweep_check_count_passed",
    "default_promotion_resident_winsorized_sweep_audit_passed",
    "default_promotion_resident_winsorized_required_frame_passed",
    "default_promotion_resident_winsorized_sweep_matches_matrix",
)

_PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_STATUS_FIELDS = (
    "matrix_resident_winsorized_sweep_status",
    "matrix_resident_winsorized_sweep_required_frame_count",
    "matrix_resident_winsorized_sweep_required_frame_count_passed",
    "matrix_resident_winsorized_sweep_check_count",
    "default_promotion_resident_winsorized_sweep_status",
    "default_promotion_resident_winsorized_sweep_required_frame_count",
    "default_promotion_resident_winsorized_sweep_required_frame_count_passed",
    "default_promotion_resident_winsorized_sweep_check_count",
)


_PUBLISH_PREFLIGHT_RESIDENT_FASTPATH_HANDOFF_CHECK_FIELDS = (
    "github_plan_matrix_resident_fastpath_release_handoff_ready",
    "matrix_resident_fastpath_release_handoff_ready",
    "default_promotion_resident_fastpath_release_handoff_ready",
    "github_plan_matrix_resident_fastpath_handoff_matches_matrix",
    "matrix_resident_fastpath_handoff_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_RESIDENT_FASTPATH_HANDOFF_STATUS_FIELDS = (
    "github_plan_matrix_resident_fastpath_handoff_ready",
    "github_plan_matrix_resident_fastpath_handoff_raw_status",
    "github_plan_matrix_resident_fastpath_handoff_phase2_status",
    "github_plan_matrix_resident_fastpath_handoff_raw_check_count",
    "matrix_resident_fastpath_handoff_ready",
    "matrix_resident_fastpath_handoff_raw_status",
    "matrix_resident_fastpath_handoff_phase2_status",
    "matrix_resident_fastpath_handoff_raw_check_count",
    "default_promotion_resident_fastpath_handoff_ready",
    "default_promotion_resident_fastpath_handoff_raw_status",
    "default_promotion_resident_fastpath_handoff_phase2_status",
    "default_promotion_resident_fastpath_handoff_raw_check_count",
)


_PUBLISH_PREFLIGHT_RESIDENT_RESULT_CONTRACT_HANDOFF_CHECK_FIELDS = (
    "github_plan_matrix_resident_result_contract_handoff_passed",
    "matrix_resident_result_contract_handoff_passed",
    "default_promotion_resident_result_contract_handoff_passed",
    "github_plan_matrix_resident_result_contract_matches_matrix",
    "matrix_resident_result_contract_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_RESIDENT_RESULT_CONTRACT_STATUS_FIELDS = (
    "github_plan_matrix_resident_result_contract_ready",
    "github_plan_matrix_resident_result_contract_status",
    "github_plan_matrix_resident_result_contract_phase2_check_passed",
    "github_plan_matrix_resident_result_contract_required_count",
    "github_plan_matrix_resident_result_contract_failed_count",
    "matrix_resident_result_contract_ready",
    "matrix_resident_result_contract_status",
    "matrix_resident_result_contract_phase2_check_passed",
    "matrix_resident_result_contract_required_count",
    "matrix_resident_result_contract_failed_count",
    "default_promotion_resident_result_contract_ready",
    "default_promotion_resident_result_contract_status",
    "default_promotion_resident_result_contract_phase2_check_passed",
    "default_promotion_resident_result_contract_required_count",
    "default_promotion_resident_result_contract_failed_count",
)


_PUBLISH_PREFLIGHT_STACK_PUBLICATION_CHECK_FIELDS = (
    "matrix_stack_engine_publication_audit_passed",
    "matrix_stack_engine_publication_policy_chain_passed",
    "matrix_stack_engine_publication_resident_winsorized_chain_passed",
    "default_promotion_stack_engine_publication_audit_passed",
    "default_promotion_stack_engine_publication_policy_chain_passed",
    "default_promotion_stack_engine_publication_resident_winsorized_chain_passed",
    "matrix_stack_engine_publication_audit_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_STACK_PUBLICATION_STATUS_FIELDS = (
    "matrix_stack_engine_publication_audit_status",
    "matrix_stack_engine_publication_audit_ready",
    "matrix_stack_engine_publication_policy_agreement",
    "matrix_stack_engine_publication_resident_winsorized_agreement",
    "default_promotion_stack_engine_publication_audit_status",
    "default_promotion_stack_engine_publication_audit_ready",
    "default_promotion_stack_engine_publication_policy_agreement",
    "default_promotion_stack_engine_publication_resident_winsorized_agreement",
)


_PUBLISH_PREFLIGHT_QUALITY_COMPARE_CHECK_FIELDS = (
    "windows_release_matrix_quality_metrics_compare_handoff_passed",
    "default_promotion_quality_metrics_compare_handoff_passed",
    "matrix_quality_metrics_compare_matches_default_promotion",
)

_PUBLISH_PREFLIGHT_QUALITY_COMPARE_STATUS_FIELDS = (
    "matrix_quality_metrics_compare_present",
    "matrix_quality_metrics_compare_ready",
    "matrix_quality_metrics_compare_status",
    "matrix_quality_metrics_compare_failed_check_count",
    "default_promotion_quality_metrics_compare_present",
    "default_promotion_quality_metrics_compare_ready",
    "default_promotion_quality_metrics_compare_status",
    "default_promotion_quality_metrics_compare_failed_check_count",
)


def _publish_preflight_rejection_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_REJECTION_CHECK_FIELDS
    )


def _publish_preflight_rejection_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_REJECTION_STATUS_FIELDS
    }


def _publish_preflight_rejection_statuses_passed(payload: dict[str, Any]) -> bool:
    statuses = _publish_preflight_rejection_statuses(payload)
    return bool(statuses) and all(value == "passed" for value in statuses.values())


def _publish_preflight_sample_closure_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_CHECK_FIELDS
    )


def _publish_preflight_sample_closure_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_SAMPLE_CLOSURE_STATUS_FIELDS
    }


def _publish_preflight_sample_closure_statuses_passed(payload: dict[str, Any]) -> bool:
    statuses = _publish_preflight_sample_closure_statuses(payload)
    return bool(statuses) and all(value == "passed" for value in statuses.values())


def _publish_preflight_engine_policy_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_ENGINE_POLICY_CHECK_FIELDS
    )


def _publish_preflight_engine_policy_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_ENGINE_POLICY_STATUS_FIELDS
    }


def _publish_preflight_engine_policy_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_engine_policy_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("matrix_integration_engine_policy_ready") is True
        and statuses.get("default_promotion_integration_engine_policy_ready") is True
        and statuses.get("matrix_acceptance_integration_engine_policy_status")
        == "passed"
        and statuses.get("matrix_pipeline_integration_engine_policy_status")
        == "passed"
        and statuses.get(
            "default_promotion_acceptance_integration_engine_policy_status"
        )
        == "passed"
        and statuses.get("default_promotion_pipeline_integration_engine_policy_status")
        == "passed"
    )


def _publish_preflight_stack_engine_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_STACK_ENGINE_CHECK_FIELDS
    )


def _publish_preflight_stack_engine_statuses(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_STACK_ENGINE_STATUS_FIELDS
    }


def _publish_preflight_stack_engine_statuses_passed(payload: dict[str, Any]) -> bool:
    statuses = _publish_preflight_stack_engine_statuses(payload)
    return bool(statuses) and all(value == "passed" for value in statuses.values())


def _publish_preflight_runtime_default_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RUNTIME_DEFAULT_CHECK_FIELDS
    )


def _publish_preflight_runtime_default_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RUNTIME_DEFAULT_STATUS_FIELDS
    }


def _publish_preflight_runtime_default_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_runtime_default_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("matrix_stack_engine_runtime_default_ready") is True
        and statuses.get("default_promotion_stack_engine_runtime_default_ready")
        is True
        and statuses.get("matrix_acceptance_stack_engine_runtime_default_status")
        == "passed"
        and statuses.get("matrix_pipeline_stack_engine_runtime_default_status")
        == "passed"
        and statuses.get(
            "default_promotion_acceptance_stack_engine_runtime_default_status"
        )
        == "passed"
        and statuses.get(
            "default_promotion_pipeline_stack_engine_runtime_default_status"
        )
        == "passed"
        and _int_or_zero(
            statuses.get(
                "matrix_stack_engine_runtime_default_acceptance_legacy_master_count"
            )
        )
        == 0
        and _int_or_zero(
            statuses.get(
                "matrix_stack_engine_runtime_default_pipeline_failed_output_count"
            )
        )
        == 0
        and _int_or_zero(
            statuses.get(
                "default_promotion_stack_engine_runtime_default_acceptance_legacy_master_count"
            )
        )
        == 0
        and _int_or_zero(
            statuses.get(
                "default_promotion_stack_engine_runtime_default_pipeline_failed_output_count"
            )
        )
        == 0
    )


def _publish_preflight_direct_runtime_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_DIRECT_RUNTIME_CHECK_FIELDS
    )


def _publish_preflight_direct_runtime_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_DIRECT_RUNTIME_STATUS_FIELDS
    }


def _publish_preflight_direct_runtime_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_direct_runtime_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("matrix_direct_runtime_evidence_ready") is True
        and statuses.get("default_promotion_direct_runtime_evidence_ready") is True
        and statuses.get("matrix_direct_runtime_acceptance_source")
        == "explicit_resident_artifacts_json"
        and statuses.get("default_promotion_direct_runtime_acceptance_source")
        == "explicit_resident_artifacts_json"
        and _int_or_zero(statuses.get("matrix_direct_runtime_acceptance_check_count"))
        > 0
        and _int_or_zero(
            statuses.get("default_promotion_direct_runtime_acceptance_check_count")
        )
        > 0
        and statuses.get("matrix_direct_runtime_pipeline_calibration_source")
        == "resident_artifacts_json_fallback"
        and statuses.get(
            "default_promotion_direct_runtime_pipeline_calibration_source"
        )
        == "resident_artifacts_json_fallback"
        and _int_or_zero(
            statuses.get("matrix_direct_runtime_pipeline_resident_lights")
        )
        >= 200
        and _int_or_zero(
            statuses.get(
                "default_promotion_direct_runtime_pipeline_resident_lights"
            )
        )
        >= 200
    )


def _publish_preflight_release_direct_publication_guard_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RELEASE_DIRECT_PUBLICATION_GUARD_CHECK_FIELDS
    )


def _publish_preflight_release_direct_publication_guard_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RELEASE_DIRECT_PUBLICATION_GUARD_STATUS_FIELDS
    }


def _publish_preflight_release_direct_publication_guard_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_release_direct_publication_guard_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("github_plan_matrix_release_direct_publication_guard_ready")
        is True
        and _int_or_zero(
            statuses.get("github_plan_matrix_release_direct_publication_guard_lights")
        )
        >= 200
        and statuses.get(
            "github_plan_matrix_default_promotion_release_direct_publication_guard_ready"
        )
        is True
        and _int_or_zero(
            statuses.get(
                "github_plan_matrix_default_promotion_release_direct_publication_guard_lights"
            )
        )
        >= 200
        and statuses.get("matrix_release_direct_publication_guard_ready") is True
        and statuses.get("matrix_release_direct_publication_guard_source_ready")
        is True
        and statuses.get("matrix_release_direct_publication_guard_count_ready") is True
        and statuses.get("matrix_release_direct_publication_guard_check_passed")
        is True
        and _int_or_zero(
            statuses.get("matrix_release_direct_publication_guard_lights")
        )
        >= 200
        and statuses.get(
            "matrix_default_promotion_release_direct_publication_guard_ready"
        )
        is True
        and _int_or_zero(
            statuses.get(
                "matrix_default_promotion_release_direct_publication_guard_lights"
            )
        )
        >= 200
        and statuses.get("default_promotion_release_direct_publication_guard_ready")
        is True
        and _int_or_zero(
            statuses.get("default_promotion_release_direct_publication_guard_lights")
        )
        >= 200
    )


def _publish_preflight_release_quality_publication_guard_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_STATUS_FIELDS
    }


def _publish_preflight_release_quality_publication_guard_present(
    payload: dict[str, Any],
) -> bool:
    return any(
        _status_value(payload, "publish_preflight", field) is not None
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_STATUS_FIELDS
    )


def _publish_preflight_release_quality_publication_guard_final_checks_present(
    payload: dict[str, Any],
) -> bool:
    return any(
        _status_value(payload, "publish_preflight", field) is not None
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_CHECK_FIELDS
    )


def _publish_preflight_release_quality_publication_guard_final_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return _publish_preflight_release_quality_publication_guard_final_checks_present(
        payload
    ) and all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_CHECK_FIELDS
    )


def _publish_preflight_release_quality_publication_guard_optional_final_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return (
        not _publish_preflight_release_quality_publication_guard_final_checks_present(
            payload
        )
        or _publish_preflight_release_quality_publication_guard_final_checks_passed(
            payload
        )
    )


def _publish_preflight_release_quality_publication_guard_final_evidence_present(
    payload: dict[str, Any],
) -> bool:
    return any(
        _status_value(payload, "publish_preflight", field) is not None
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_FIELDS
    )


def _publish_preflight_release_quality_publication_guard_legacy_final_evidence_present(
    payload: dict[str, Any],
) -> bool:
    return any(
        _status_value(payload, "publish_preflight", field) is not None
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_LEGACY_FINAL_EVIDENCE_FIELDS
    )


def _publish_preflight_release_quality_publication_guard_final_evidence_detail_present(
    payload: dict[str, Any],
) -> bool:
    return any(
        _status_value(payload, "publish_preflight", field) is not None
        for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_DETAIL_FIELDS
    )


def _publish_preflight_release_quality_publication_guard_final_evidence_layer_passed(
    payload: dict[str, Any],
    prefix: str,
    *,
    ready_suffix: str,
    match_suffix: str,
    raw_ready_suffix: str,
    phase2_ready_suffix: str,
) -> bool:
    final_ready = _status_value(
        payload,
        "publish_preflight",
        f"{prefix}_{ready_suffix}",
    )
    final_match = _status_value(
        payload,
        "publish_preflight",
        f"{prefix}_{match_suffix}",
    )
    raw_ready = _status_value(
        payload,
        "publish_preflight",
        f"{prefix}_{raw_ready_suffix}",
    )
    phase2_ready = _status_value(
        payload,
        "publish_preflight",
        f"{prefix}_{phase2_ready_suffix}",
    )
    if (
        final_ready is None
        and final_match is None
        and raw_ready is None
        and phase2_ready is None
    ):
        return False
    compatible_missing = (
        final_ready is True
        and final_match is True
        and raw_ready is None
        and phase2_ready is None
    )
    return compatible_missing or (
        final_ready is True
        and final_match is True
        and raw_ready is True
        and phase2_ready is True
    )


def _publish_preflight_release_quality_publication_guard_legacy_final_evidence_layer_passed(
    payload: dict[str, Any],
    prefix: str,
) -> bool:
    return _publish_preflight_release_quality_publication_guard_final_evidence_layer_passed(
        payload,
        prefix,
        ready_suffix="final_checks_ready",
        match_suffix="final_checks_match",
        raw_ready_suffix="raw_final_checks_ready",
        phase2_ready_suffix="phase2_final_checks_ready",
    )


def _publish_preflight_release_quality_publication_guard_final_evidence_detail_layer_passed(
    payload: dict[str, Any],
    prefix: str,
) -> bool:
    return _publish_preflight_release_quality_publication_guard_final_evidence_layer_passed(
        payload,
        prefix,
        ready_suffix="final_evidence_ready",
        match_suffix="final_evidence_match",
        raw_ready_suffix="raw_final_evidence_ready",
        phase2_ready_suffix="phase2_final_evidence_ready",
    )


def _publish_preflight_release_quality_publication_guard_final_evidence_detail_passed(
    payload: dict[str, Any],
) -> bool:
    return _publish_preflight_release_quality_publication_guard_final_evidence_detail_present(
        payload
    ) and all(
        _publish_preflight_release_quality_publication_guard_final_evidence_detail_layer_passed(
            payload,
            prefix,
        )
        for prefix in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_PREFIXES
    )


def _publish_preflight_release_quality_publication_guard_legacy_final_evidence_passed(
    payload: dict[str, Any],
) -> bool:
    return _publish_preflight_release_quality_publication_guard_legacy_final_evidence_present(
        payload
    ) and all(
        _publish_preflight_release_quality_publication_guard_legacy_final_evidence_layer_passed(
            payload,
            prefix,
        )
        for prefix in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_FINAL_EVIDENCE_PREFIXES
    )


def _publish_preflight_release_quality_publication_guard_final_evidence_passed(
    payload: dict[str, Any],
) -> bool:
    return (
        _publish_preflight_release_quality_publication_guard_final_evidence_detail_passed(
            payload
        )
        if _publish_preflight_release_quality_publication_guard_final_evidence_detail_present(
            payload
        )
        else _publish_preflight_release_quality_publication_guard_legacy_final_evidence_passed(
            payload
        )
    )


def _publish_preflight_release_quality_publication_guard_optional_final_evidence_passed(
    payload: dict[str, Any],
) -> bool:
    return (
        not _publish_preflight_release_quality_publication_guard_final_evidence_present(
            payload
        )
        or _publish_preflight_release_quality_publication_guard_final_evidence_passed(
            payload
        )
    )


def _publish_preflight_release_quality_publication_guard_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return (
        _publish_preflight_release_quality_publication_guard_present(payload)
        and all(
            _status_value(payload, "publish_preflight", field) is True
            for field in _PUBLISH_PREFLIGHT_RELEASE_QUALITY_PUBLICATION_GUARD_CHECK_FIELDS
        )
        and _publish_preflight_release_quality_publication_guard_optional_final_checks_passed(
            payload
        )
        and _publish_preflight_release_quality_publication_guard_optional_final_evidence_passed(
            payload
        )
    )


def _publish_preflight_release_quality_publication_guard_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_release_quality_publication_guard_statuses(payload)
    return (
        _publish_preflight_release_quality_publication_guard_present(payload)
        and statuses.get("matrix_release_quality_publication_guard_present") is True
        and statuses.get("matrix_release_quality_publication_guard_ready") is True
        and statuses.get("matrix_release_quality_publication_guard_check_passed")
        is True
        and statuses.get("matrix_release_quality_publication_guard_layers_ready")
        is True
        and statuses.get("matrix_release_quality_publication_guard_raw_status")
        == "passed"
        and statuses.get("matrix_release_quality_publication_guard_phase2_status")
        == "passed"
        and statuses.get(
            "matrix_default_promotion_release_quality_publication_guard_ready"
        )
        is True
        and statuses.get(
            "matrix_default_promotion_release_quality_publication_guard_raw_status"
        )
        == "passed"
        and statuses.get(
            "matrix_default_promotion_release_quality_publication_guard_phase2_status"
        )
        == "passed"
        and statuses.get("default_promotion_release_quality_publication_guard_present")
        is True
        and statuses.get("default_promotion_release_quality_publication_guard_ready")
        is True
        and statuses.get(
            "default_promotion_release_quality_publication_guard_check_passed"
        )
        is True
        and statuses.get(
            "default_promotion_release_quality_publication_guard_layers_ready"
        )
        is True
        and statuses.get(
            "default_promotion_release_quality_publication_guard_raw_status"
        )
        == "passed"
        and statuses.get(
            "default_promotion_release_quality_publication_guard_phase2_status"
        )
        == "passed"
    )


def _publish_preflight_resident_winsorized_checks_passed(payload: dict[str, Any]) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_CHECK_FIELDS
    )


def _publish_preflight_resident_winsorized_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RESIDENT_WINSORIZED_STATUS_FIELDS
    }


def _publish_preflight_resident_winsorized_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_resident_winsorized_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("matrix_resident_winsorized_sweep_status") == "passed"
        and statuses.get("default_promotion_resident_winsorized_sweep_status")
        == "passed"
        and statuses.get(
            "matrix_resident_winsorized_sweep_required_frame_count_passed"
        )
        is True
        and statuses.get(
            "default_promotion_resident_winsorized_sweep_required_frame_count_passed"
        )
        is True
        and _int_or_zero(
            statuses.get("matrix_resident_winsorized_sweep_required_frame_count")
        )
        >= 200
        and _int_or_zero(
            statuses.get(
                "default_promotion_resident_winsorized_sweep_required_frame_count"
            )
        )
        >= 200
        and _int_or_zero(statuses.get("matrix_resident_winsorized_sweep_check_count"))
        > 0
        and _int_or_zero(
            statuses.get("default_promotion_resident_winsorized_sweep_check_count")
        )
        > 0
    )


def _publish_preflight_resident_fastpath_handoff_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RESIDENT_FASTPATH_HANDOFF_CHECK_FIELDS
    )


def _publish_preflight_resident_fastpath_handoff_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RESIDENT_FASTPATH_HANDOFF_STATUS_FIELDS
    }


def _publish_preflight_resident_fastpath_handoff_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_resident_fastpath_handoff_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("github_plan_matrix_resident_fastpath_handoff_ready")
        is True
        and statuses.get("matrix_resident_fastpath_handoff_ready") is True
        and statuses.get("default_promotion_resident_fastpath_handoff_ready")
        is True
        and statuses.get(
            "github_plan_matrix_resident_fastpath_handoff_raw_status"
        )
        == "passed"
        and statuses.get("matrix_resident_fastpath_handoff_raw_status")
        == "passed"
        and statuses.get(
            "default_promotion_resident_fastpath_handoff_raw_status"
        )
        == "passed"
        and statuses.get(
            "github_plan_matrix_resident_fastpath_handoff_phase2_status"
        )
        == "passed"
        and statuses.get("matrix_resident_fastpath_handoff_phase2_status")
        == "passed"
        and statuses.get(
            "default_promotion_resident_fastpath_handoff_phase2_status"
        )
        == "passed"
        and _int_or_zero(
            statuses.get(
                "github_plan_matrix_resident_fastpath_handoff_raw_check_count"
            )
        )
        > 0
        and _int_or_zero(
            statuses.get("matrix_resident_fastpath_handoff_raw_check_count")
        )
        > 0
        and _int_or_zero(
            statuses.get(
                "default_promotion_resident_fastpath_handoff_raw_check_count"
            )
        )
        > 0
    )


def _publish_preflight_resident_result_contract_handoff_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_RESIDENT_RESULT_CONTRACT_HANDOFF_CHECK_FIELDS
    )


def _publish_preflight_resident_result_contract_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_RESIDENT_RESULT_CONTRACT_STATUS_FIELDS
    }


def _publish_preflight_resident_result_contract_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_resident_result_contract_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("github_plan_matrix_resident_result_contract_ready") is True
        and statuses.get("matrix_resident_result_contract_ready") is True
        and statuses.get("default_promotion_resident_result_contract_ready") is True
        and statuses.get("github_plan_matrix_resident_result_contract_status")
        == "passed"
        and statuses.get("matrix_resident_result_contract_status") == "passed"
        and statuses.get("default_promotion_resident_result_contract_status")
        == "passed"
        and statuses.get(
            "github_plan_matrix_resident_result_contract_phase2_check_passed"
        )
        is True
        and statuses.get("matrix_resident_result_contract_phase2_check_passed")
        is True
        and statuses.get(
            "default_promotion_resident_result_contract_phase2_check_passed"
        )
        is True
        and _int_or_zero(
            statuses.get("github_plan_matrix_resident_result_contract_required_count")
        )
        > 0
        and _int_or_zero(
            statuses.get("matrix_resident_result_contract_required_count")
        )
        > 0
        and _int_or_zero(
            statuses.get("default_promotion_resident_result_contract_required_count")
        )
        > 0
        and _int_or_zero(
            statuses.get("github_plan_matrix_resident_result_contract_failed_count")
        )
        == 0
        and _int_or_zero(statuses.get("matrix_resident_result_contract_failed_count"))
        == 0
        and _int_or_zero(
            statuses.get("default_promotion_resident_result_contract_failed_count")
        )
        == 0
    )


def _publish_preflight_stack_publication_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_STACK_PUBLICATION_CHECK_FIELDS
    )


def _publish_preflight_stack_publication_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_STACK_PUBLICATION_STATUS_FIELDS
    }


def _publish_preflight_stack_publication_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_stack_publication_statuses(payload)
    return (
        bool(statuses)
        and statuses.get("matrix_stack_engine_publication_audit_status") == "passed"
        and statuses.get("default_promotion_stack_engine_publication_audit_status")
        == "passed"
        and statuses.get("matrix_stack_engine_publication_audit_ready") is True
        and statuses.get("default_promotion_stack_engine_publication_audit_ready")
        is True
        and statuses.get("matrix_stack_engine_publication_policy_agreement") is True
        and statuses.get(
            "default_promotion_stack_engine_publication_policy_agreement"
        )
        is True
        and statuses.get(
            "matrix_stack_engine_publication_resident_winsorized_agreement"
        )
        is True
        and statuses.get(
            "default_promotion_stack_engine_publication_resident_winsorized_agreement"
        )
        is True
    )


def _publish_preflight_quality_compare_statuses(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        field: _status_value(payload, "publish_preflight", field)
        for field in _PUBLISH_PREFLIGHT_QUALITY_COMPARE_STATUS_FIELDS
    }


def _publish_preflight_quality_compare_present(payload: dict[str, Any]) -> bool:
    return any(
        _status_value(payload, "publish_preflight", field) is not None
        for field in _PUBLISH_PREFLIGHT_QUALITY_COMPARE_STATUS_FIELDS
    )


def _publish_preflight_quality_compare_checks_passed(
    payload: dict[str, Any],
) -> bool:
    return _publish_preflight_quality_compare_present(payload) and all(
        _status_value(payload, "publish_preflight", field) is True
        for field in _PUBLISH_PREFLIGHT_QUALITY_COMPARE_CHECK_FIELDS
    )


def _publish_preflight_quality_compare_statuses_passed(
    payload: dict[str, Any],
) -> bool:
    statuses = _publish_preflight_quality_compare_statuses(payload)
    return (
        _publish_preflight_quality_compare_present(payload)
        and statuses.get("matrix_quality_metrics_compare_present") is True
        and statuses.get("matrix_quality_metrics_compare_ready") is True
        and statuses.get("matrix_quality_metrics_compare_status") == "passed"
        and _int_or_zero(
            statuses.get("matrix_quality_metrics_compare_failed_check_count")
        )
        == 0
        and statuses.get("default_promotion_quality_metrics_compare_present")
        is True
        and statuses.get("default_promotion_quality_metrics_compare_ready") is True
        and statuses.get("default_promotion_quality_metrics_compare_status")
        == "passed"
        and _int_or_zero(
            statuses.get(
                "default_promotion_quality_metrics_compare_failed_check_count"
            )
        )
        == 0
    )


_STACK_PUBLICATION_POLICY_FIELDS = (
    "publish_preflight_integration_engine_policy_ready",
    "phase2_publish_preflight_integration_engine_policy_ready",
    "phase2_publish_preflight_integration_engine_policy_matches_publish_preflight",
)

_STACK_PUBLICATION_WINSORIZED_FIELDS = (
    "publish_preflight_resident_winsorized_sweep_ready",
    "phase2_publish_preflight_resident_winsorized_sweep_ready",
    "phase2_publish_preflight_resident_winsorized_matches_publish_preflight",
)

_STACK_PUBLICATION_RESIDENT_RESULT_FIELDS = (
    "publish_preflight_resident_result_contract_ready",
    "phase2_publish_preflight_resident_result_contract_ready",
    "phase2_publish_preflight_resident_result_contract_matches_publish_preflight",
)

_STACK_PUBLICATION_DIRECT_RUNTIME_FIELDS = (
    "publish_preflight_direct_runtime_evidence_ready",
    "phase2_publish_preflight_direct_runtime_evidence_ready",
    "phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight",
)


def _stack_publication_summary(payload: dict[str, Any]) -> dict[str, Any]:
    audit = _status_value(payload, "stack_engine_publication_audit")
    if not isinstance(audit, dict):
        return {
            "present": False,
            "passed": False,
            "status": None,
            "check_count": None,
            "failed_check_count": None,
            "policy_checks_passed": False,
            "resident_winsorized_checks_passed": False,
            "resident_result_contract_checks_passed": False,
            "direct_runtime_checks_passed": False,
        }
    policy = {
        field: audit.get(field)
        for field in _STACK_PUBLICATION_POLICY_FIELDS
    }
    resident_winsorized = {
        field: audit.get(field)
        for field in _STACK_PUBLICATION_WINSORIZED_FIELDS
    }
    resident_result_contract = {
        field: audit.get(field)
        for field in _STACK_PUBLICATION_RESIDENT_RESULT_FIELDS
    }
    direct_runtime = {
        field: audit.get(field)
        for field in _STACK_PUBLICATION_DIRECT_RUNTIME_FIELDS
    }
    return {
        "present": True,
        "passed": audit.get("passed") is True,
        "status": audit.get("status"),
        "recommendation": audit.get("recommendation"),
        "check_count": audit.get("check_count"),
        "failed_check_count": audit.get("failed_check_count"),
        "policy_checks": policy,
        "resident_winsorized_checks": resident_winsorized,
        "resident_result_contract_checks": resident_result_contract,
        "direct_runtime_checks": direct_runtime,
        "policy_checks_passed": all(value is True for value in policy.values()),
        "resident_winsorized_checks_passed": all(
            value is True for value in resident_winsorized.values()
        ),
        "resident_result_contract_checks_passed": all(
            value is True for value in resident_result_contract.values()
        ),
        "direct_runtime_checks_passed": all(
            value is True for value in direct_runtime.values()
        ),
    }


def _stack_engine_status_summary(payload: dict[str, Any]) -> dict[str, Any]:
    contract = _status_value(payload, "stack_engine_contract")
    if not isinstance(contract, dict):
        return {
            "present": False,
            "ready": False,
            "status": None,
            "default_promotion_status": None,
            "gap_count": None,
            "recommendation": None,
        }
    gap_count = contract.get("default_promotion_phase2_stack_engine_default_gap_count")
    if gap_count is None:
        gap_count = contract.get("adoption_phase2_stack_engine_default_gap_count")
    return {
        "present": True,
        "ready": _stack_engine_default_contract_ready(contract),
        "status": contract.get("status"),
        "passed": contract.get("passed"),
        "scope": contract.get("scope"),
        "expected_integration_engine": contract.get("expected_integration_engine"),
        "default_promotion_ready": contract.get("default_promotion_ready"),
        "default_promotion_status": contract.get("default_promotion_status"),
        "gap_count": gap_count,
        "blocker_count": contract.get("default_promotion_blocker_count"),
        "recommendation": contract.get("adoption_recommendation"),
    }


def _stack_engine_gap_count(payload: dict[str, Any]) -> int | None:
    summary = _stack_engine_status_summary(payload)
    value = summary.get("gap_count")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_phase2_status_compare(
    *,
    baseline_status: str | Path,
    candidate_status: str | Path,
) -> dict[str, Any]:
    baseline = _load_phase2_status(baseline_status)
    candidate = _load_phase2_status(candidate_status)
    baseline_gate = _status_value(baseline, "latest_checkpoint", "gate")
    candidate_gate = _status_value(candidate, "latest_checkpoint", "gate")
    baseline_stack_engine = _stack_engine_status_summary(baseline)
    candidate_stack_engine = _stack_engine_status_summary(candidate)
    baseline_publication = _stack_publication_summary(baseline)
    candidate_publication = _stack_publication_summary(candidate)
    baseline_stack_gap_count = _stack_engine_gap_count(baseline)
    candidate_stack_gap_count = _stack_engine_gap_count(candidate)
    baseline_sweep_check_count = _int_status_value(
        baseline,
        "resident_winsorized_sweep_audit",
        "check_count",
    )
    candidate_sweep_check_count = _int_status_value(
        candidate,
        "resident_winsorized_sweep_audit",
        "check_count",
    )
    baseline_sweep_required_frame_count = _int_status_value(
        baseline,
        "resident_winsorized_sweep_audit",
        "required_frame_count",
    )
    candidate_sweep_required_frame_count = _int_status_value(
        candidate,
        "resident_winsorized_sweep_audit",
        "required_frame_count",
    )
    baseline_resident_result_status = _status_value(
        baseline,
        "pipeline_contract",
        "resident_result_contract",
        "status",
    )
    candidate_resident_result_status = _status_value(
        candidate,
        "pipeline_contract",
        "resident_result_contract",
        "status",
    )
    baseline_resident_result_check_present = _status_value(
        baseline,
        "pipeline_contract",
        "resident_result_contract",
        "check_present",
    )
    candidate_resident_result_check_present = _status_value(
        candidate,
        "pipeline_contract",
        "resident_result_contract",
        "check_present",
    )
    baseline_resident_result_passed = (
        baseline_resident_result_status == "passed"
        or _status_value(
            baseline,
            "pipeline_contract",
            "integration_resident_result_contract",
        )
        is True
    )
    candidate_resident_result_passed = (
        candidate_resident_result_status == "passed"
        or _status_value(
            candidate,
            "pipeline_contract",
            "integration_resident_result_contract",
        )
        is True
    )
    baseline_resident_result_failed_count = _int_status_value(
        baseline,
        "pipeline_contract",
        "resident_result_contract",
        "failed_count",
    )
    candidate_resident_result_failed_count = _int_status_value(
        candidate,
        "pipeline_contract",
        "resident_result_contract",
        "failed_count",
    )
    checks = [
        _compare_check(
            "baseline_artifact_type",
            baseline.get("artifact_type") == "glass_phase2_status",
            baseline=baseline.get("artifact_type"),
            candidate="glass_phase2_status",
        ),
        _compare_check(
            "candidate_artifact_type",
            candidate.get("artifact_type") == "glass_phase2_status",
            baseline="glass_phase2_status",
            candidate=candidate.get("artifact_type"),
        ),
        _compare_check(
            "latest_checkpoint_gate_not_decreased",
            candidate_gate is not None and baseline_gate is not None and int(candidate_gate) >= int(baseline_gate),
            baseline=baseline_gate,
            candidate=candidate_gate,
        ),
        _compare_check(
            "overall_status_green_preserved",
            baseline.get("status") != "green" or candidate.get("status") == "green",
            baseline=baseline.get("status"),
            candidate=candidate.get("status"),
        ),
        _compare_check(
            "latest_checkpoint_green_preserved",
            _status_value(baseline, "latest_checkpoint", "green") is not True
            or _status_value(candidate, "latest_checkpoint", "green") is True,
            baseline=_status_value(baseline, "latest_checkpoint", "green"),
            candidate=_status_value(candidate, "latest_checkpoint", "green"),
        ),
        _compare_check(
            "acceptance_audit_passed_preserved",
            _status_value(baseline, "acceptance_audit", "passed") is not True
            or _status_value(candidate, "acceptance_audit", "passed") is True,
            baseline=_status_value(baseline, "acceptance_audit", "passed"),
            candidate=_status_value(candidate, "acceptance_audit", "passed"),
        ),
        _compare_check(
            "acceptance_status_preserved",
            _status_value(baseline, "acceptance_audit", "status") != "passed"
            or _status_value(candidate, "acceptance_audit", "status") == "passed",
            baseline=_status_value(baseline, "acceptance_audit", "status"),
            candidate=_status_value(candidate, "acceptance_audit", "status"),
        ),
        _compare_check(
            "acceptance_benchmark_contract_profile_preserved",
            _status_value(baseline, "acceptance_audit", "benchmark_contract_profile")
            is None
            or _status_value(
                baseline,
                "acceptance_audit",
                "benchmark_contract_profile",
            )
            == _status_value(
                candidate,
                "acceptance_audit",
                "benchmark_contract_profile",
            ),
            baseline={
                "source": _status_value(
                    baseline,
                    "acceptance_audit",
                    "benchmark_contract_source",
                ),
                "profile": _status_value(
                    baseline,
                    "acceptance_audit",
                    "benchmark_contract_profile",
                ),
                "name": _status_value(
                    baseline,
                    "acceptance_audit",
                    "benchmark_contract_name",
                ),
            },
            candidate={
                "source": _status_value(
                    candidate,
                    "acceptance_audit",
                    "benchmark_contract_source",
                ),
                "profile": _status_value(
                    candidate,
                    "acceptance_audit",
                    "benchmark_contract_profile",
                ),
                "name": _status_value(
                    candidate,
                    "acceptance_audit",
                    "benchmark_contract_name",
                ),
            },
        ),
        _compare_check(
            "acceptance_pipeline_integration_engine_policy_preserved",
            _status_value(
                baseline,
                "acceptance_audit",
                "pipeline_integration_engine_policy_status",
            )
            != "passed"
            or _status_value(
                candidate,
                "acceptance_audit",
                "pipeline_integration_engine_policy_status",
            )
            == "passed",
            baseline={
                "status": _status_value(
                    baseline,
                    "acceptance_audit",
                    "pipeline_integration_engine_policy_status",
                ),
                "check_present": _status_value(
                    baseline,
                    "acceptance_audit",
                    "pipeline_integration_engine_policy_check_present",
                ),
                "check_passed": _status_value(
                    baseline,
                    "acceptance_audit",
                    "pipeline_integration_engine_policy_check_passed",
                ),
            },
            candidate={
                "status": _status_value(
                    candidate,
                    "acceptance_audit",
                    "pipeline_integration_engine_policy_status",
                ),
                "check_present": _status_value(
                    candidate,
                    "acceptance_audit",
                    "pipeline_integration_engine_policy_check_present",
                ),
                "check_passed": _status_value(
                    candidate,
                    "acceptance_audit",
                    "pipeline_integration_engine_policy_check_passed",
                ),
            },
        ),
        _compare_check(
            "acceptance_pipeline_stack_engine_runtime_default_check_preserved",
            _status_value(
                baseline,
                "acceptance_audit",
                "pipeline_stack_engine_runtime_default_check_present",
            )
            is not True
            or _status_value(
                candidate,
                "acceptance_audit",
                "pipeline_stack_engine_runtime_default_check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "acceptance_audit",
                "pipeline_stack_engine_runtime_default_check_present",
            ),
            candidate=_status_value(
                candidate,
                "acceptance_audit",
                "pipeline_stack_engine_runtime_default_check_present",
            ),
        ),
        _compare_check(
            "acceptance_pipeline_stack_engine_runtime_default_passed_preserved",
            _status_value(
                baseline,
                "acceptance_audit",
                "pipeline_stack_engine_runtime_default_status",
            )
            != "passed"
            or _status_value(
                candidate,
                "acceptance_audit",
                "pipeline_stack_engine_runtime_default_status",
            )
            == "passed",
            baseline={
                "status": _status_value(
                    baseline,
                    "acceptance_audit",
                    "pipeline_stack_engine_runtime_default_status",
                ),
                "check_passed": _status_value(
                    baseline,
                    "acceptance_audit",
                    "pipeline_stack_engine_runtime_default_check_passed",
                ),
                "legacy_master_count": _status_value(
                    baseline,
                    "acceptance_audit",
                    "pipeline_stack_engine_runtime_default_legacy_master_count",
                ),
            },
            candidate={
                "status": _status_value(
                    candidate,
                    "acceptance_audit",
                    "pipeline_stack_engine_runtime_default_status",
                ),
                "check_passed": _status_value(
                    candidate,
                    "acceptance_audit",
                    "pipeline_stack_engine_runtime_default_check_passed",
                ),
                "legacy_master_count": _status_value(
                    candidate,
                    "acceptance_audit",
                    "pipeline_stack_engine_runtime_default_legacy_master_count",
                ),
            },
        ),
        _compare_check(
            "default_route_acceptance_passed_preserved",
            _status_value(baseline, "default_route_acceptance", "passed") is not True
            or _status_value(candidate, "default_route_acceptance", "passed") is True,
            baseline=_status_value(baseline, "default_route_acceptance", "passed"),
            candidate=_status_value(candidate, "default_route_acceptance", "passed"),
        ),
        _compare_check(
            "default_route_acceptance_route_contract_preserved",
            _status_value(baseline, "default_route_acceptance", "route_contract_passed")
            is not True
            or _status_value(candidate, "default_route_acceptance", "route_contract_passed")
            is True,
            baseline=_status_value(
                baseline,
                "default_route_acceptance",
                "route_contract_passed",
            ),
            candidate=_status_value(
                candidate,
                "default_route_acceptance",
                "route_contract_passed",
            ),
        ),
        _compare_check(
            "resident_registration_fastpath_contract_passed_preserved",
            _status_value(
                baseline,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            )
            != "passed"
            or _status_value(
                candidate,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            ),
            candidate=_status_value(
                candidate,
                "acceptance_audit",
                "resident_registration_fastpath_contract_status",
            ),
        ),
        _compare_check(
            "resident_registration_fastpath_contract_check_count_preserved",
            int(
                _status_value(
                    baseline,
                    "acceptance_audit",
                    "resident_registration_fastpath_contract_check_count",
                )
                or 0
            )
            <= 0
            or int(
                _status_value(
                    candidate,
                    "acceptance_audit",
                    "resident_registration_fastpath_contract_check_count",
                )
                or 0
            )
            >= int(
                _status_value(
                    baseline,
                    "acceptance_audit",
                    "resident_registration_fastpath_contract_check_count",
                )
                or 0
            ),
            baseline=_status_value(
                baseline,
                "acceptance_audit",
                "resident_registration_fastpath_contract_check_count",
            ),
            candidate=_status_value(
                candidate,
                "acceptance_audit",
                "resident_registration_fastpath_contract_check_count",
            ),
        ),
        _compare_check(
            "registration_reference_admission_not_blocked_preserved",
            _status_value(baseline, "registration_admission", "passed") is not True
            or _status_value(candidate, "registration_admission", "passed") is True,
            baseline={
                "status": _status_value(baseline, "registration_admission", "status"),
                "passed": _status_value(baseline, "registration_admission", "passed"),
                "blocked": _status_value(baseline, "registration_admission", "blocked"),
                "reference_frame_id": _status_value(
                    baseline,
                    "registration_admission",
                    "reference_frame_id",
                ),
                "reason": _status_value(baseline, "registration_admission", "reason"),
            },
            candidate={
                "status": _status_value(candidate, "registration_admission", "status"),
                "passed": _status_value(candidate, "registration_admission", "passed"),
                "blocked": _status_value(candidate, "registration_admission", "blocked"),
                "reference_frame_id": _status_value(
                    candidate,
                    "registration_admission",
                    "reference_frame_id",
                ),
                "reason": _status_value(candidate, "registration_admission", "reason"),
            },
        ),
        _compare_check(
            "quality_saturation_no_rejections_preserved",
            _status_value(baseline, "quality_saturation", "passed") is not True
            or _status_value(candidate, "quality_saturation", "passed") is True,
            baseline={
                "status": _status_value(baseline, "quality_saturation", "status"),
                "passed": _status_value(baseline, "quality_saturation", "passed"),
                "frame_count": _status_value(baseline, "quality_saturation", "frame_count"),
                "saturated_frame_count": _status_value(
                    baseline,
                    "quality_saturation",
                    "saturated_frame_count",
                ),
                "quality_gate_saturation_rejected_count": _status_value(
                    baseline,
                    "quality_saturation",
                    "quality_gate_saturation_rejected_count",
                ),
                "max_saturation_fraction": _status_value(
                    baseline,
                    "quality_saturation",
                    "max_saturation_fraction",
                ),
                "worst_frame_id": _status_value(
                    baseline,
                    "quality_saturation",
                    "worst_frame_id",
                ),
            },
            candidate={
                "status": _status_value(candidate, "quality_saturation", "status"),
                "passed": _status_value(candidate, "quality_saturation", "passed"),
                "frame_count": _status_value(candidate, "quality_saturation", "frame_count"),
                "saturated_frame_count": _status_value(
                    candidate,
                    "quality_saturation",
                    "saturated_frame_count",
                ),
                "quality_gate_saturation_rejected_count": _status_value(
                    candidate,
                    "quality_saturation",
                    "quality_gate_saturation_rejected_count",
                ),
                "max_saturation_fraction": _status_value(
                    candidate,
                    "quality_saturation",
                    "max_saturation_fraction",
                ),
                "worst_frame_id": _status_value(
                    candidate,
                    "quality_saturation",
                    "worst_frame_id",
                ),
            },
        ),
        _compare_check(
            "quality_metric_summary_available_preserved",
            _int_status_value(baseline, "quality_metrics", "metric_count") in {None, 0}
            or (
                _int_status_value(candidate, "quality_metrics", "metric_count") or 0
            )
            >= (_int_status_value(baseline, "quality_metrics", "metric_count") or 0),
            baseline={
                "status": _status_value(baseline, "quality_metrics", "status"),
                "passed": _status_value(baseline, "quality_metrics", "passed"),
                "frame_count": _status_value(baseline, "quality_metrics", "frame_count"),
                "metric_count": _status_value(baseline, "quality_metrics", "metric_count"),
                "metrics": _status_value(baseline, "quality_metrics", "metrics"),
            },
            candidate={
                "status": _status_value(candidate, "quality_metrics", "status"),
                "passed": _status_value(candidate, "quality_metrics", "passed"),
                "frame_count": _status_value(candidate, "quality_metrics", "frame_count"),
                "metric_count": _status_value(candidate, "quality_metrics", "metric_count"),
                "metrics": _status_value(candidate, "quality_metrics", "metrics"),
            },
        ),
        _compare_check(
            "quality_metrics_compare_passed_preserved",
            _status_value(baseline, "quality_metrics_compare", "passed") is not True
            or _status_value(candidate, "quality_metrics_compare", "passed") is True,
            baseline={
                "status": _status_value(baseline, "quality_metrics_compare", "status"),
                "passed": _status_value(baseline, "quality_metrics_compare", "passed"),
                "failed_check_count": _status_value(
                    baseline,
                    "quality_metrics_compare",
                    "failed_check_count",
                ),
                "failed_checks": _status_value(
                    baseline,
                    "quality_metrics_compare",
                    "failed_checks",
                ),
                "threshold_failure_count": _status_value(
                    baseline,
                    "quality_metrics_compare",
                    "threshold_failure_count",
                ),
            },
            candidate={
                "status": _status_value(candidate, "quality_metrics_compare", "status"),
                "passed": _status_value(candidate, "quality_metrics_compare", "passed"),
                "failed_check_count": _status_value(
                    candidate,
                    "quality_metrics_compare",
                    "failed_check_count",
                ),
                "failed_checks": _status_value(
                    candidate,
                    "quality_metrics_compare",
                    "failed_checks",
                ),
                "threshold_failure_count": _status_value(
                    candidate,
                    "quality_metrics_compare",
                    "threshold_failure_count",
                ),
            },
        ),
        _compare_check(
            "cuda_available_preserved",
            _status_value(baseline, "doctor", "cuda_available") is not True
            or _status_value(candidate, "doctor", "cuda_available") is True,
            baseline=_status_value(baseline, "doctor", "cuda_available"),
            candidate=_status_value(candidate, "doctor", "cuda_available"),
        ),
        _compare_check(
            "release_manifest_ready_preserved",
            _status_value(baseline, "release_manifest", "status") != "release_manifest_ready"
            or _status_value(candidate, "release_manifest", "status") == "release_manifest_ready",
            baseline=_status_value(baseline, "release_manifest", "status"),
            candidate=_status_value(candidate, "release_manifest", "status"),
        ),
        _compare_check(
            "github_release_plan_ready_preserved",
            _status_value(baseline, "github_release_plan", "status") != "release_plan_ready"
            or _status_value(candidate, "github_release_plan", "status") == "release_plan_ready",
            baseline=_status_value(baseline, "github_release_plan", "status"),
            candidate=_status_value(candidate, "github_release_plan", "status"),
        ),
        _compare_check(
            "windows_publish_preflight_ready_preserved",
            _status_value(baseline, "publish_preflight", "status") != "publish_preflight_ready"
            or _status_value(candidate, "publish_preflight", "status") == "publish_preflight_ready",
            baseline=_status_value(baseline, "publish_preflight", "status"),
            candidate=_status_value(candidate, "publish_preflight", "status"),
        ),
        _compare_check(
            "windows_publish_preflight_rejection_sample_accounting_preserved",
            not _publish_preflight_rejection_checks_passed(baseline)
            or _publish_preflight_rejection_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_rejection_checks_passed(baseline),
                "statuses": _publish_preflight_rejection_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_rejection_checks_passed(candidate),
                "statuses": _publish_preflight_rejection_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_rejection_sample_status_preserved",
            not _publish_preflight_rejection_statuses_passed(baseline)
            or _publish_preflight_rejection_statuses_passed(candidate),
            baseline=_publish_preflight_rejection_statuses(baseline),
            candidate=_publish_preflight_rejection_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_sample_accounting_closure_preserved",
            not _publish_preflight_sample_closure_checks_passed(baseline)
            or _publish_preflight_sample_closure_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_sample_closure_checks_passed(baseline),
                "statuses": _publish_preflight_sample_closure_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_sample_closure_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_sample_closure_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_sample_closure_status_preserved",
            not _publish_preflight_sample_closure_statuses_passed(baseline)
            or _publish_preflight_sample_closure_statuses_passed(candidate),
            baseline=_publish_preflight_sample_closure_statuses(baseline),
            candidate=_publish_preflight_sample_closure_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_integration_engine_policy_preserved",
            not _publish_preflight_engine_policy_checks_passed(baseline)
            or _publish_preflight_engine_policy_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_engine_policy_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_engine_policy_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_engine_policy_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_engine_policy_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_integration_engine_policy_status_preserved",
            not _publish_preflight_engine_policy_statuses_passed(baseline)
            or _publish_preflight_engine_policy_statuses_passed(candidate),
            baseline=_publish_preflight_engine_policy_statuses(baseline),
            candidate=_publish_preflight_engine_policy_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_stack_engine_contract_preserved",
            not _publish_preflight_stack_engine_checks_passed(baseline)
            or _publish_preflight_stack_engine_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_stack_engine_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_stack_engine_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_stack_engine_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_stack_engine_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_stack_engine_status_preserved",
            not _publish_preflight_stack_engine_statuses_passed(baseline)
            or _publish_preflight_stack_engine_statuses_passed(candidate),
            baseline=_publish_preflight_stack_engine_statuses(baseline),
            candidate=_publish_preflight_stack_engine_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_stack_engine_runtime_default_preserved",
            not _publish_preflight_runtime_default_checks_passed(baseline)
            or _publish_preflight_runtime_default_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_runtime_default_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_runtime_default_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_runtime_default_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_runtime_default_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_stack_engine_runtime_default_status_preserved",
            not _publish_preflight_runtime_default_statuses_passed(baseline)
            or _publish_preflight_runtime_default_statuses_passed(candidate),
            baseline=_publish_preflight_runtime_default_statuses(baseline),
            candidate=_publish_preflight_runtime_default_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_direct_runtime_evidence_preserved",
            not _publish_preflight_direct_runtime_checks_passed(baseline)
            or _publish_preflight_direct_runtime_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_direct_runtime_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_direct_runtime_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_direct_runtime_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_direct_runtime_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_direct_runtime_status_preserved",
            not _publish_preflight_direct_runtime_statuses_passed(baseline)
            or _publish_preflight_direct_runtime_statuses_passed(candidate),
            baseline=_publish_preflight_direct_runtime_statuses(baseline),
            candidate=_publish_preflight_direct_runtime_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_release_direct_publication_guard_preserved",
            not _publish_preflight_release_direct_publication_guard_checks_passed(
                baseline
            )
            or _publish_preflight_release_direct_publication_guard_checks_passed(
                candidate
            ),
            baseline={
                "checks_passed": (
                    _publish_preflight_release_direct_publication_guard_checks_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_release_direct_publication_guard_statuses(
                        baseline
                    )
                ),
            },
            candidate={
                "checks_passed": (
                    _publish_preflight_release_direct_publication_guard_checks_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_release_direct_publication_guard_statuses(
                        candidate
                    )
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_release_direct_publication_guard_status_preserved",
            not _publish_preflight_release_direct_publication_guard_statuses_passed(
                baseline
            )
            or _publish_preflight_release_direct_publication_guard_statuses_passed(
                candidate
            ),
            baseline=_publish_preflight_release_direct_publication_guard_statuses(
                baseline
            ),
            candidate=_publish_preflight_release_direct_publication_guard_statuses(
                candidate
            ),
        ),
        _compare_check(
            "windows_publish_preflight_release_quality_publication_guard_preserved",
            not _publish_preflight_release_quality_publication_guard_checks_passed(
                baseline
            )
            or _publish_preflight_release_quality_publication_guard_checks_passed(
                candidate
            ),
            baseline={
                "checks_passed": (
                    _publish_preflight_release_quality_publication_guard_checks_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        baseline
                    )
                ),
            },
            candidate={
                "checks_passed": (
                    _publish_preflight_release_quality_publication_guard_checks_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        candidate
                    )
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_release_quality_publication_guard_final_checks_preserved",
            not _publish_preflight_release_quality_publication_guard_final_checks_passed(
                baseline
            )
            or _publish_preflight_release_quality_publication_guard_final_checks_passed(
                candidate
            ),
            baseline={
                "final_checks_present": (
                    _publish_preflight_release_quality_publication_guard_final_checks_present(
                        baseline
                    )
                ),
                "final_checks_passed": (
                    _publish_preflight_release_quality_publication_guard_final_checks_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        baseline
                    )
                ),
            },
            candidate={
                "final_checks_present": (
                    _publish_preflight_release_quality_publication_guard_final_checks_present(
                        candidate
                    )
                ),
                "final_checks_passed": (
                    _publish_preflight_release_quality_publication_guard_final_checks_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        candidate
                    )
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_release_quality_publication_guard_final_evidence_preserved",
            not _publish_preflight_release_quality_publication_guard_final_evidence_passed(
                baseline
            )
            or _publish_preflight_release_quality_publication_guard_final_evidence_passed(
                candidate
            ),
            baseline={
                "final_evidence_present": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_present(
                        baseline
                    )
                ),
                "final_evidence_passed": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        baseline
                    )
                ),
            },
            candidate={
                "final_evidence_present": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_present(
                        candidate
                    )
                ),
                "final_evidence_passed": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        candidate
                    )
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_release_quality_publication_guard_final_evidence_detail_preserved",
            not _publish_preflight_release_quality_publication_guard_final_evidence_detail_passed(
                baseline
            )
            or _publish_preflight_release_quality_publication_guard_final_evidence_detail_passed(
                candidate
            ),
            baseline={
                "final_evidence_detail_present": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_detail_present(
                        baseline
                    )
                ),
                "final_evidence_detail_passed": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_detail_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        baseline
                    )
                ),
            },
            candidate={
                "final_evidence_detail_present": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_detail_present(
                        candidate
                    )
                ),
                "final_evidence_detail_passed": (
                    _publish_preflight_release_quality_publication_guard_final_evidence_detail_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_release_quality_publication_guard_statuses(
                        candidate
                    )
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_release_quality_publication_guard_status_preserved",
            not _publish_preflight_release_quality_publication_guard_statuses_passed(
                baseline
            )
            or _publish_preflight_release_quality_publication_guard_statuses_passed(
                candidate
            ),
            baseline=(
                _publish_preflight_release_quality_publication_guard_statuses(
                    baseline
                )
            ),
            candidate=(
                _publish_preflight_release_quality_publication_guard_statuses(
                    candidate
                )
            ),
        ),
        _compare_check(
            "windows_publish_preflight_resident_winsorized_sweep_preserved",
            not _publish_preflight_resident_winsorized_checks_passed(baseline)
            or _publish_preflight_resident_winsorized_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_resident_winsorized_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_resident_winsorized_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_resident_winsorized_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_resident_winsorized_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_resident_winsorized_status_preserved",
            not _publish_preflight_resident_winsorized_statuses_passed(baseline)
            or _publish_preflight_resident_winsorized_statuses_passed(candidate),
            baseline=_publish_preflight_resident_winsorized_statuses(baseline),
            candidate=_publish_preflight_resident_winsorized_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_resident_fastpath_handoff_preserved",
            not _publish_preflight_resident_fastpath_handoff_checks_passed(baseline)
            or _publish_preflight_resident_fastpath_handoff_checks_passed(candidate),
            baseline={
                "checks_passed": (
                    _publish_preflight_resident_fastpath_handoff_checks_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_resident_fastpath_handoff_statuses(baseline)
                ),
            },
            candidate={
                "checks_passed": (
                    _publish_preflight_resident_fastpath_handoff_checks_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_resident_fastpath_handoff_statuses(candidate)
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_resident_fastpath_handoff_status_preserved",
            not _publish_preflight_resident_fastpath_handoff_statuses_passed(baseline)
            or _publish_preflight_resident_fastpath_handoff_statuses_passed(candidate),
            baseline=_publish_preflight_resident_fastpath_handoff_statuses(baseline),
            candidate=_publish_preflight_resident_fastpath_handoff_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_resident_result_contract_handoff_preserved",
            not _publish_preflight_resident_result_contract_handoff_checks_passed(
                baseline
            )
            or _publish_preflight_resident_result_contract_handoff_checks_passed(
                candidate
            ),
            baseline={
                "checks_passed": (
                    _publish_preflight_resident_result_contract_handoff_checks_passed(
                        baseline
                    )
                ),
                "statuses": (
                    _publish_preflight_resident_result_contract_statuses(baseline)
                ),
            },
            candidate={
                "checks_passed": (
                    _publish_preflight_resident_result_contract_handoff_checks_passed(
                        candidate
                    )
                ),
                "statuses": (
                    _publish_preflight_resident_result_contract_statuses(candidate)
                ),
            },
        ),
        _compare_check(
            "windows_publish_preflight_resident_result_contract_status_preserved",
            not _publish_preflight_resident_result_contract_statuses_passed(baseline)
            or _publish_preflight_resident_result_contract_statuses_passed(candidate),
            baseline=_publish_preflight_resident_result_contract_statuses(baseline),
            candidate=_publish_preflight_resident_result_contract_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_stack_publication_audit_preserved",
            not _publish_preflight_stack_publication_checks_passed(baseline)
            or _publish_preflight_stack_publication_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_stack_publication_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_stack_publication_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_stack_publication_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_stack_publication_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_stack_publication_status_preserved",
            not _publish_preflight_stack_publication_statuses_passed(baseline)
            or _publish_preflight_stack_publication_statuses_passed(candidate),
            baseline=_publish_preflight_stack_publication_statuses(baseline),
            candidate=_publish_preflight_stack_publication_statuses(candidate),
        ),
        _compare_check(
            "windows_publish_preflight_quality_metrics_compare_preserved",
            not _publish_preflight_quality_compare_checks_passed(baseline)
            or _publish_preflight_quality_compare_checks_passed(candidate),
            baseline={
                "checks_passed": _publish_preflight_quality_compare_checks_passed(
                    baseline
                ),
                "statuses": _publish_preflight_quality_compare_statuses(baseline),
            },
            candidate={
                "checks_passed": _publish_preflight_quality_compare_checks_passed(
                    candidate
                ),
                "statuses": _publish_preflight_quality_compare_statuses(candidate),
            },
        ),
        _compare_check(
            "windows_publish_preflight_quality_metrics_compare_status_preserved",
            not _publish_preflight_quality_compare_statuses_passed(baseline)
            or _publish_preflight_quality_compare_statuses_passed(candidate),
            baseline=_publish_preflight_quality_compare_statuses(baseline),
            candidate=_publish_preflight_quality_compare_statuses(candidate),
        ),
        _compare_check(
            "stack_engine_publication_audit_passed_preserved",
            baseline_publication.get("passed") is not True
            or candidate_publication.get("passed") is True,
            baseline=baseline_publication,
            candidate=candidate_publication,
        ),
        _compare_check(
            "stack_engine_publication_policy_chain_preserved",
            baseline_publication.get("policy_checks_passed") is not True
            or candidate_publication.get("policy_checks_passed") is True,
            baseline=baseline_publication.get("policy_checks"),
            candidate=candidate_publication.get("policy_checks"),
        ),
        _compare_check(
            "stack_engine_publication_resident_winsorized_chain_preserved",
            baseline_publication.get("resident_winsorized_checks_passed") is not True
            or candidate_publication.get("resident_winsorized_checks_passed") is True,
            baseline=baseline_publication.get("resident_winsorized_checks"),
            candidate=candidate_publication.get("resident_winsorized_checks"),
        ),
        _compare_check(
            "stack_engine_publication_resident_result_contract_chain_preserved",
            baseline_publication.get("resident_result_contract_checks_passed")
            is not True
            or candidate_publication.get("resident_result_contract_checks_passed")
            is True,
            baseline=baseline_publication.get("resident_result_contract_checks"),
            candidate=candidate_publication.get("resident_result_contract_checks"),
        ),
        _compare_check(
            "stack_engine_publication_direct_runtime_chain_preserved",
            baseline_publication.get("direct_runtime_checks_passed") is not True
            or candidate_publication.get("direct_runtime_checks_passed") is True,
            baseline=baseline_publication.get("direct_runtime_checks"),
            candidate=candidate_publication.get("direct_runtime_checks"),
        ),
        _compare_check(
            "pipeline_contract_passed_preserved",
            _status_value(baseline, "pipeline_contract", "passed") is not True
            or _status_value(candidate, "pipeline_contract", "passed") is True,
            baseline=_status_value(baseline, "pipeline_contract", "passed"),
            candidate=_status_value(candidate, "pipeline_contract", "passed"),
        ),
        _compare_check(
            "pipeline_resident_result_contract_check_preserved",
            baseline_resident_result_check_present is not True
            or candidate_resident_result_check_present is True,
            baseline=baseline_resident_result_check_present,
            candidate=candidate_resident_result_check_present,
        ),
        _compare_check(
            "pipeline_resident_result_contract_passed_preserved",
            not baseline_resident_result_passed or candidate_resident_result_passed,
            baseline={
                "status": baseline_resident_result_status,
                "check_present": baseline_resident_result_check_present,
                "failed_count": baseline_resident_result_failed_count,
                "failed_checks": _status_value(
                    baseline,
                    "pipeline_contract",
                    "resident_result_contract",
                    "failed_checks",
                ),
            },
            candidate={
                "status": candidate_resident_result_status,
                "check_present": candidate_resident_result_check_present,
                "failed_count": candidate_resident_result_failed_count,
                "failed_checks": _status_value(
                    candidate,
                    "pipeline_contract",
                    "resident_result_contract",
                    "failed_checks",
                ),
            },
        ),
        _compare_check(
            "pipeline_resident_result_contract_failure_count_not_increased",
            baseline_resident_result_failed_count is None
            or (
                candidate_resident_result_failed_count is not None
                and candidate_resident_result_failed_count
                <= baseline_resident_result_failed_count
            ),
            baseline=baseline_resident_result_failed_count,
            candidate=candidate_resident_result_failed_count,
        ),
        _compare_check(
            "pipeline_integration_dq_contract_preserved",
            _status_value(baseline, "pipeline_contract", "integration_dq_contract") is not True
            or _status_value(candidate, "pipeline_contract", "integration_dq_contract") is True,
            baseline=_status_value(baseline, "pipeline_contract", "integration_dq_contract"),
            candidate=_status_value(candidate, "pipeline_contract", "integration_dq_contract"),
        ),
        _compare_check(
            "pipeline_integration_engine_policy_check_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "integration_engine_policy",
                "check_present",
            )
            is not True
            or _status_value(
                candidate,
                "pipeline_contract",
                "integration_engine_policy",
                "check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "integration_engine_policy",
                "check_present",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "integration_engine_policy",
                "check_present",
            ),
        ),
        _compare_check(
            "pipeline_integration_engine_policy_passed_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "integration_engine_policy",
                "status",
            )
            != "passed"
            or _status_value(
                candidate,
                "pipeline_contract",
                "integration_engine_policy",
                "status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "integration_engine_policy",
                "status",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "integration_engine_policy",
                "status",
            ),
        ),
        _compare_check(
            "pipeline_stack_engine_runtime_default_check_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "stack_engine_runtime_default",
                "check_present",
            )
            is not True
            or _status_value(
                candidate,
                "pipeline_contract",
                "stack_engine_runtime_default",
                "check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "stack_engine_runtime_default",
                "check_present",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "stack_engine_runtime_default",
                "check_present",
            ),
        ),
        _compare_check(
            "pipeline_stack_engine_runtime_default_passed_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "stack_engine_runtime_default",
                "status",
            )
            != "passed"
            or _status_value(
                candidate,
                "pipeline_contract",
                "stack_engine_runtime_default",
                "status",
            )
            == "passed",
            baseline={
                "status": _status_value(
                    baseline,
                    "pipeline_contract",
                    "stack_engine_runtime_default",
                    "status",
                ),
                "check_passed": _status_value(
                    baseline,
                    "pipeline_contract",
                    "stack_engine_runtime_default",
                    "check_passed",
                ),
                "legacy_master_count": _status_value(
                    baseline,
                    "pipeline_contract",
                    "stack_engine_runtime_default",
                    "legacy_master_count",
                ),
            },
            candidate={
                "status": _status_value(
                    candidate,
                    "pipeline_contract",
                    "stack_engine_runtime_default",
                    "status",
                ),
                "check_passed": _status_value(
                    candidate,
                    "pipeline_contract",
                    "stack_engine_runtime_default",
                    "check_passed",
                ),
                "legacy_master_count": _status_value(
                    candidate,
                    "pipeline_contract",
                    "stack_engine_runtime_default",
                    "legacy_master_count",
                ),
            },
        ),
        _compare_check(
            "pipeline_pixel_verification_preserved",
            _status_value(baseline, "pipeline_contract", "pixel_verification_enabled") is not True
            or _status_value(candidate, "pipeline_contract", "pixel_verification_enabled") is True,
            baseline=_status_value(baseline, "pipeline_contract", "pixel_verification_enabled"),
            candidate=_status_value(candidate, "pipeline_contract", "pixel_verification_enabled"),
        ),
        _compare_check(
            "pipeline_rejection_sample_accounting_check_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            )
            is not True
            or _status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "check_present",
            ),
        ),
        _compare_check(
            "pipeline_rejection_sample_accounting_passed_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            )
            != "passed"
            or _status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "rejection_sample_accounting",
                "status",
            ),
        ),
        _compare_check(
            "pipeline_sample_accounting_closure_check_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            )
            is not True
            or _status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            )
            is True,
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "check_present",
            ),
        ),
        _compare_check(
            "pipeline_sample_accounting_closure_passed_preserved",
            _status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            )
            != "passed"
            or _status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            )
            == "passed",
            baseline=_status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
            candidate=_status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
        ),
        _compare_check(
            "resident_winsorized_sweep_audit_passed_preserved",
            _status_value(baseline, "resident_winsorized_sweep_audit", "passed")
            is not True
            or _status_value(candidate, "resident_winsorized_sweep_audit", "passed")
            is True,
            baseline=_status_value(baseline, "resident_winsorized_sweep_audit", "passed"),
            candidate=_status_value(candidate, "resident_winsorized_sweep_audit", "passed"),
        ),
        _compare_check(
            "resident_winsorized_sweep_required_frame_preserved",
            _status_value(
                baseline,
                "resident_winsorized_sweep_audit",
                "required_frame_count_passed",
            )
            is not True
            or _status_value(
                candidate,
                "resident_winsorized_sweep_audit",
                "required_frame_count_passed",
            )
            is True,
            baseline={
                "required_frame_count": baseline_sweep_required_frame_count,
                "required_frame_count_passed": _status_value(
                    baseline,
                    "resident_winsorized_sweep_audit",
                    "required_frame_count_passed",
                ),
            },
            candidate={
                "required_frame_count": candidate_sweep_required_frame_count,
                "required_frame_count_passed": _status_value(
                    candidate,
                    "resident_winsorized_sweep_audit",
                    "required_frame_count_passed",
                ),
            },
        ),
        _compare_check(
            "resident_winsorized_sweep_check_count_not_decreased",
            baseline_sweep_check_count is None
            or (
                candidate_sweep_check_count is not None
                and candidate_sweep_check_count >= baseline_sweep_check_count
            ),
            baseline=baseline_sweep_check_count,
            candidate=candidate_sweep_check_count,
        ),
        _compare_check(
            "stack_engine_default_contract_ready_preserved",
            not baseline_stack_engine.get("ready") or candidate_stack_engine.get("ready") is True,
            baseline=baseline_stack_engine,
            candidate=candidate_stack_engine,
        ),
        _compare_check(
            "stack_engine_default_gap_count_not_increased",
            baseline_stack_gap_count is None
            or (
                candidate_stack_gap_count is not None
                and candidate_stack_gap_count <= baseline_stack_gap_count
            ),
            baseline=baseline_stack_gap_count,
            candidate=candidate_stack_gap_count,
        ),
        _compare_check(
            "release_decision_default_change_ready_preserved",
            _status_value(baseline, "release_decision", "default_change_ready") is not True
            or _status_value(candidate, "release_decision", "default_change_ready") is True,
            baseline=_status_value(baseline, "release_decision", "default_change_ready"),
            candidate=_status_value(candidate, "release_decision", "default_change_ready"),
        ),
        _compare_check(
            "release_decision_promote_recommendation_preserved",
            _status_value(baseline, "release_decision", "recommendation")
            != "promote_default_candidate"
            or _status_value(candidate, "release_decision", "recommendation")
            == "promote_default_candidate",
            baseline=_status_value(baseline, "release_decision", "recommendation"),
            candidate=_status_value(candidate, "release_decision", "recommendation"),
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "glass_phase2_status_compare",
        "created_at": now_iso(),
        "status": "passed" if passed else "regressed",
        "passed": passed,
        "baseline_path": str(baseline_status),
        "candidate_path": str(candidate_status),
        "baseline": {
            "status": baseline.get("status"),
            "latest_gate": baseline_gate,
            "acceptance_status": _status_value(baseline, "acceptance_audit", "status"),
            "default_route_acceptance_status": _status_value(
                baseline,
                "default_route_acceptance",
                "status",
            ),
            "default_route_acceptance_passed": _status_value(
                baseline,
                "default_route_acceptance",
                "passed",
            ),
            "cuda_available": _status_value(baseline, "doctor", "cuda_available"),
            "release_manifest_status": _status_value(baseline, "release_manifest", "status"),
            "github_release_plan_status": _status_value(baseline, "github_release_plan", "status"),
            "publish_preflight_status": _status_value(baseline, "publish_preflight", "status"),
            "publish_preflight_rejection_sample_accounting": (
                _publish_preflight_rejection_statuses(baseline)
            ),
            "publish_preflight_sample_accounting_closure": (
                _publish_preflight_sample_closure_statuses(baseline)
            ),
            "publish_preflight_integration_engine_policy": (
                _publish_preflight_engine_policy_statuses(baseline)
            ),
            "publish_preflight_stack_engine_contract": (
                _publish_preflight_stack_engine_statuses(baseline)
            ),
            "publish_preflight_stack_engine_runtime_default": (
                _publish_preflight_runtime_default_statuses(baseline)
            ),
            "publish_preflight_resident_winsorized_sweep": (
                _publish_preflight_resident_winsorized_statuses(baseline)
            ),
            "publish_preflight_resident_fastpath_handoff": (
                _publish_preflight_resident_fastpath_handoff_statuses(baseline)
            ),
            "publish_preflight_resident_result_contract": (
                _publish_preflight_resident_result_contract_statuses(baseline)
            ),
            "publish_preflight_stack_publication_audit": (
                _publish_preflight_stack_publication_statuses(baseline)
            ),
            "publish_preflight_quality_metrics_compare": (
                _publish_preflight_quality_compare_statuses(baseline)
            ),
            "publish_preflight_release_quality_publication_guard": (
                _publish_preflight_release_quality_publication_guard_statuses(
                    baseline
                )
            ),
            "stack_engine_publication_audit": baseline_publication,
            "registration_admission": _status_value(baseline, "registration_admission"),
            "quality_saturation": _status_value(baseline, "quality_saturation"),
            "quality_metrics": _status_value(baseline, "quality_metrics"),
            "quality_metrics_compare": _status_value(
                baseline,
                "quality_metrics_compare",
            ),
            "pipeline_contract_status": _status_value(baseline, "pipeline_contract", "status"),
            "pipeline_contract_passed": _status_value(baseline, "pipeline_contract", "passed"),
            "acceptance_pipeline_integration_engine_policy": _status_value(
                baseline,
                "acceptance_audit",
                "pipeline_integration_engine_policy_status",
            ),
            "pipeline_integration_engine_policy": _status_value(
                baseline,
                "pipeline_contract",
                "integration_engine_policy",
                "status",
            ),
            "pipeline_sample_accounting_closure": _status_value(
                baseline,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
            "resident_winsorized_sweep_audit": _status_value(
                baseline,
                "resident_winsorized_sweep_audit",
            ),
            "stack_engine_default_contract": baseline_stack_engine,
            "release_decision_status": _status_value(baseline, "release_decision", "status"),
            "default_change_ready": _status_value(
                baseline,
                "release_decision",
                "default_change_ready",
            ),
        },
        "candidate": {
            "status": candidate.get("status"),
            "latest_gate": candidate_gate,
            "acceptance_status": _status_value(candidate, "acceptance_audit", "status"),
            "default_route_acceptance_status": _status_value(
                candidate,
                "default_route_acceptance",
                "status",
            ),
            "default_route_acceptance_passed": _status_value(
                candidate,
                "default_route_acceptance",
                "passed",
            ),
            "cuda_available": _status_value(candidate, "doctor", "cuda_available"),
            "release_manifest_status": _status_value(candidate, "release_manifest", "status"),
            "github_release_plan_status": _status_value(candidate, "github_release_plan", "status"),
            "publish_preflight_status": _status_value(candidate, "publish_preflight", "status"),
            "publish_preflight_rejection_sample_accounting": (
                _publish_preflight_rejection_statuses(candidate)
            ),
            "publish_preflight_sample_accounting_closure": (
                _publish_preflight_sample_closure_statuses(candidate)
            ),
            "publish_preflight_integration_engine_policy": (
                _publish_preflight_engine_policy_statuses(candidate)
            ),
            "publish_preflight_stack_engine_contract": (
                _publish_preflight_stack_engine_statuses(candidate)
            ),
            "publish_preflight_stack_engine_runtime_default": (
                _publish_preflight_runtime_default_statuses(candidate)
            ),
            "publish_preflight_resident_winsorized_sweep": (
                _publish_preflight_resident_winsorized_statuses(candidate)
            ),
            "publish_preflight_resident_fastpath_handoff": (
                _publish_preflight_resident_fastpath_handoff_statuses(candidate)
            ),
            "publish_preflight_resident_result_contract": (
                _publish_preflight_resident_result_contract_statuses(candidate)
            ),
            "publish_preflight_stack_publication_audit": (
                _publish_preflight_stack_publication_statuses(candidate)
            ),
            "publish_preflight_quality_metrics_compare": (
                _publish_preflight_quality_compare_statuses(candidate)
            ),
            "publish_preflight_release_quality_publication_guard": (
                _publish_preflight_release_quality_publication_guard_statuses(
                    candidate
                )
            ),
            "stack_engine_publication_audit": candidate_publication,
            "registration_admission": _status_value(candidate, "registration_admission"),
            "quality_saturation": _status_value(candidate, "quality_saturation"),
            "quality_metrics": _status_value(candidate, "quality_metrics"),
            "quality_metrics_compare": _status_value(
                candidate,
                "quality_metrics_compare",
            ),
            "pipeline_contract_status": _status_value(candidate, "pipeline_contract", "status"),
            "pipeline_contract_passed": _status_value(candidate, "pipeline_contract", "passed"),
            "acceptance_pipeline_integration_engine_policy": _status_value(
                candidate,
                "acceptance_audit",
                "pipeline_integration_engine_policy_status",
            ),
            "pipeline_integration_engine_policy": _status_value(
                candidate,
                "pipeline_contract",
                "integration_engine_policy",
                "status",
            ),
            "pipeline_sample_accounting_closure": _status_value(
                candidate,
                "pipeline_contract",
                "sample_accounting_closure",
                "status",
            ),
            "resident_winsorized_sweep_audit": _status_value(
                candidate,
                "resident_winsorized_sweep_audit",
            ),
            "stack_engine_default_contract": candidate_stack_engine,
            "release_decision_status": _status_value(candidate, "release_decision", "status"),
            "default_change_ready": _status_value(
                candidate,
                "release_decision",
                "default_change_ready",
            ),
        },
        "checks": checks,
    }


def _markdown_detail_value(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def write_phase2_status_compare_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GLASS Phase 2 Status Compare",
        "",
        f"- Status: {payload.get('status')}",
        f"- Baseline: {payload.get('baseline_path')}",
        f"- Candidate: {payload.get('candidate_path')}",
        "",
        "## Summary",
        "",
        f"- Baseline: {payload.get('baseline')}",
        f"- Candidate: {payload.get('candidate')}",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    failed = [
        item
        for item in payload.get("checks") or []
        if isinstance(item, dict) and item.get("passed") is not True
    ]
    if failed:
        lines.extend(["", "## Failed Check Details", ""])
        for item in failed:
            evidence = item.get("evidence")
            lines.extend([f"### {item.get('name')}", ""])
            if isinstance(evidence, dict):
                for key in ("baseline", "candidate"):
                    if key in evidence:
                        value = _markdown_detail_value(evidence.get(key))
                        lines.append(f"- {key.title()}: `{value}`")
                extra = {
                    key: value
                    for key, value in evidence.items()
                    if key not in {"baseline", "candidate"}
                }
                if extra:
                    lines.append(f"- Evidence: `{_markdown_detail_value(extra)}`")
            else:
                lines.append(f"- Evidence: `{_markdown_detail_value(evidence)}`")
            lines.append("")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_phase2_status_compare(
    out_json: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out_json, payload)
    if markdown is not None:
        write_phase2_status_compare_markdown(markdown, payload)
