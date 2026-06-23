from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.resident_calibration_artifacts import build_resident_calibration_artifacts
from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.dq_map_verify import summarize_count_map_pixels, summarize_dq_map_pixels
from glass.report.resident_result_contract import build_resident_output_contract
from glass.report.stack_engine_contract import build_master_calibration_surface_contract


_CORE_INTEGRATION_MAPS = {
    "master": "master_path",
    "weight": "weight_map_path",
    "coverage": "coverage_map_path",
    "dq": "dq_map_path",
}

_REJECTION_MAPS = {
    "low_rejection": "low_rejection_map_path",
    "high_rejection": "high_rejection_map_path",
}

_DEFAULT_DQ_PIXEL_FLAGS = ["valid", "no_data", "warp_edge", "low_rejected", "high_rejected"]


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _resident_calibration_artifact_from_resident_artifacts(run_root: Path) -> dict[str, Any]:
    resident_path = run_root / "resident_artifacts.json"
    if not resident_path.exists():
        return {}
    resident_payload = _load_json_object(resident_path)
    if not resident_payload:
        return {}
    payload = build_resident_calibration_artifacts(run_root, resident_payload)
    masters = payload.get("masters") if isinstance(payload.get("masters"), dict) else {}
    lights = payload.get("calibrated_lights") if isinstance(payload.get("calibrated_lights"), list) else []
    if not masters and not lights:
        return {}
    payload["artifact_source"] = "resident_artifacts_json_fallback"
    payload["generated_for_pipeline_contract"] = True
    payload["write_back"] = False
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _resolve_path(path_value: Any, run_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return run_root / path


def _path_exists(path_value: Any, run_root: Path) -> bool:
    path = _resolve_path(path_value, run_root)
    return bool(path and path.exists())


def _summary_count(summary: dict[str, Any], key: str, *, default_zero: bool = True) -> int | None:
    value = summary.get(key)
    if value is None:
        return 0 if default_zero else None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_rounded_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _positive_int(value: Any) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _nonnegative_int(value: Any) -> bool:
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _stack_result_contract_state_from_provenance(
    provenance: Any,
    *,
    required: bool,
) -> dict[str, Any]:
    contract = provenance.get("result_contract") if isinstance(provenance, dict) else None
    present = isinstance(contract, dict)
    passed = bool(contract.get("passed")) if isinstance(contract, dict) else False
    check_count = len(contract.get("checks") or []) if isinstance(contract, dict) else 0
    return {
        "required": required,
        "present": present,
        "passed": passed,
        "check_count": check_count,
        "status": "not_required" if not required else ("passed" if passed else "missing_or_failed"),
        "contract_type": contract.get("contract_type") if isinstance(contract, dict) else None,
    }


def _count_match(actual: Any, expected: int | None, tolerance: int) -> dict[str, Any]:
    actual_int = _optional_rounded_int(actual)
    delta = None if actual_int is None or expected is None else actual_int - expected
    return {
        "actual": actual_int,
        "summary": expected,
        "delta": delta,
        "passed": delta is not None and abs(delta) <= tolerance,
    }


def _dq_flags_to_verify(summary: dict[str, Any]) -> list[str]:
    flags = list(_DEFAULT_DQ_PIXEL_FLAGS)
    for key in summary:
        name = str(key).lower()
        if name not in flags:
            flags.append(name)
    return flags


def _policy_items(payload: dict[str, Any], key: str) -> set[str]:
    policy = payload.get("output_map_policy") if isinstance(payload.get("output_map_policy"), dict) else {}
    return {str(item) for item in (policy.get(key) or [])}


def _map_skipped(payload: dict[str, Any], map_name: str) -> bool:
    return map_name in _policy_items(payload, "skipped")


def _map_available_policy(payload: dict[str, Any], map_name: str) -> bool | None:
    policy = payload.get("output_map_policy") if isinstance(payload.get("output_map_policy"), dict) else {}
    available = policy.get("available")
    if not isinstance(available, list):
        return None
    return map_name in {str(item) for item in available}


def _map_row(
    payload: dict[str, Any],
    *,
    run_root: Path,
    surface: str,
    item: str,
    map_name: str,
    path_key: str,
    required: bool,
) -> dict[str, Any]:
    path_value = payload.get(path_key)
    skipped = _map_skipped(payload, map_name)
    exists = _path_exists(path_value, run_root)
    ok = bool(exists or not required or (skipped and map_name != "master"))
    return {
        "surface": surface,
        "item": item,
        "map": map_name,
        "path_key": path_key,
        "path": path_value,
        "exists": exists,
        "required": required,
        "policy_skipped": skipped,
        "ok": ok,
    }


def _calibration_master_rows(calibration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    masters = calibration.get("masters") if isinstance(calibration.get("masters"), dict) else {}
    for name, payload in masters.items():
        if not isinstance(payload, dict):
            continue
        path_exists = _path_exists(payload.get("path"), run_root)
        science_contract = build_master_calibration_surface_contract(
            payload,
            path_exists=path_exists,
        )
        summary = payload.get("dq_provenance_summary")
        provenance = payload.get("stack_engine_dq_provenance")
        tile_mode = str(payload.get("tile_stack_mode") or "")
        stack_required = bool(payload.get("stack_engine_enabled")) or tile_mode.startswith("stack_engine_cpu")
        stack_result = _stack_result_contract_state_from_provenance(
            provenance,
            required=stack_required,
        )
        rows.append(
            {
                "name": str(name),
                "type": payload.get("type"),
                "path": payload.get("path"),
                "path_exists": path_exists,
                "tile_stack_mode": payload.get("tile_stack_mode"),
                "stack_engine_enabled": bool(payload.get("stack_engine_enabled")),
                "stats_present": isinstance(payload.get("stats"), dict),
                "dq_provenance_summary_present": isinstance(summary, dict),
                "dq_provenance_engine": summary.get("engine") if isinstance(summary, dict) else None,
                "stack_result_contract": stack_result,
                "science_contract": science_contract,
                "contract_ok": bool(science_contract.get("passed"))
                and (not stack_result["required"] or bool(stack_result["passed"])),
            }
        )
    return rows


def _calibrated_light_rows(calibration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lights = calibration.get("calibrated_lights") if isinstance(calibration.get("calibrated_lights"), list) else []
    for index, payload in enumerate(lights):
        if not isinstance(payload, dict):
            continue
        is_resident = (
            payload.get("backend") == "cuda_resident_stack"
            or payload.get("status") == "resident_in_vram"
            or payload.get("source_stage") == "resident_calibrated_stack"
        )
        dq_summary = payload.get("dq_summary") if isinstance(payload.get("dq_summary"), dict) else {}
        path_exists = _path_exists(payload.get("path"), run_root)
        dq_path_exists = _path_exists(payload.get("dq_mask_path"), run_root)
        resident_contract_ok = (
            is_resident
            and bool(payload.get("frame_id"))
            and payload.get("status") == "resident_in_vram"
            and payload.get("backend") == "cuda_resident_stack"
            and payload.get("source_stage") == "resident_calibrated_stack"
            and _nonnegative_int(payload.get("resident_stack_index"))
        )
        dq_contract_ok = (
            path_exists
            and dq_path_exists
            and isinstance(payload.get("dq_summary"), dict)
            and "valid" in dq_summary
            and _positive_int(payload.get("tile_count"))
            and _positive_int(payload.get("tile_size"))
        )
        rows.append(
            {
                "index": index,
                "frame_id": payload.get("frame_id"),
                "backend": payload.get("backend"),
                "status": payload.get("status"),
                "source_stage": payload.get("source_stage"),
                "resident": is_resident,
                "resident_stack_index": payload.get("resident_stack_index"),
                "resident_output_index": payload.get("resident_output_index"),
                "path": payload.get("path"),
                "path_exists": path_exists,
                "dq_mask_path": payload.get("dq_mask_path"),
                "dq_mask_path_exists": dq_path_exists,
                "dq_summary_present": isinstance(payload.get("dq_summary"), dict),
                "dq_summary_has_valid": "valid" in dq_summary,
                "tile_count": payload.get("tile_count"),
                "tile_size": payload.get("tile_size"),
                "resident_contract_ok": bool(resident_contract_ok),
                "dq_contract_ok": bool(dq_contract_ok),
                "contract_ok": bool(resident_contract_ok) or bool(dq_contract_ok),
            }
        )
    return rows


def _resident_calibration_rows(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("artifact_type") != "resident_cuda_calibration_contract":
        return []
    top_level_passed = payload.get("passed") is True
    rows: list[dict[str, Any]] = []
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), list) else []
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            continue
        checks = [item for item in output.get("checks") or [] if isinstance(item, dict)]
        failed_checks = [str(item.get("name")) for item in checks if not item.get("passed")]
        passed = top_level_passed and output.get("passed") is True and not failed_checks
        rows.append(
            {
                "name": f"resident_calibration_{output.get('filter') or output.get('index', index)}",
                "type": "resident_calibration",
                "path": output.get("master_path"),
                "path_exists": output.get("master_path_exists"),
                "tile_stack_mode": "cuda_resident_stack",
                "stack_engine_enabled": True,
                "stats_present": True,
                "dq_provenance_summary_present": True,
                "dq_provenance_engine": "cuda_resident_stack",
                "stack_result_contract": {
                    "required": False,
                    "present": False,
                    "passed": False,
                    "status": "not_required",
                    "check_count": 0,
                    "contract_type": None,
                },
                "science_contract": {
                    "schema_version": 1,
                    "contract_type": "resident_calibration_surface_contract",
                    "status": "passed" if passed else "failed",
                    "passed": passed,
                    "source": "resident_cuda_calibration_contract",
                    "resident_contract_status": output.get("status"),
                    "resident_contract_check_count": len(checks),
                    "failed_checks": failed_checks,
                    "frame_count": output.get("frame_count"),
                    "set_count": output.get("set_count"),
                    "bias_count": output.get("bias_count"),
                    "dark_count": output.get("dark_count"),
                    "flat_count": output.get("flat_count"),
                },
                "resident_calibration_contract": {
                    "required": True,
                    "present": True,
                    "passed": passed,
                    "status": output.get("status"),
                    "check_count": len(checks),
                    "failed_checks": failed_checks,
                },
                "contract_ok": passed,
            }
        )
    return rows


def _integration_rejection_mode(integration: dict[str, Any], output: dict[str, Any]) -> str:
    if isinstance(output.get("integration_rejection"), dict):
        return str((output.get("integration_rejection") or {}).get("mode") or "none")
    return str(output.get("rejection") or integration.get("rejection") or "none")


def _integration_map_rows(integration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, output in enumerate(integration.get("outputs") or []):
        if not isinstance(output, dict):
            continue
        item = str(output.get("filter") or index)
        for map_name, path_key in _CORE_INTEGRATION_MAPS.items():
            available = _map_available_policy(output, map_name)
            required = map_name == "master" or (available is not False and not _map_skipped(output, map_name))
            rows.append(
                _map_row(
                    output,
                    run_root=run_root,
                    surface="integration",
                    item=item,
                    map_name=map_name,
                    path_key=path_key,
                    required=required,
                )
            )
        rejection = _integration_rejection_mode(integration, output)
        for map_name, path_key in _REJECTION_MAPS.items():
            available = _map_available_policy(output, map_name)
            required = rejection != "none" and available is not False and not _map_skipped(output, map_name)
            rows.append(
                _map_row(
                    output,
                    run_root=run_root,
                    surface="integration",
                    item=item,
                    map_name=map_name,
                    path_key=path_key,
                    required=required,
                )
            )
    return rows


def _verify_integration_dq_pixels(
    output: dict[str, Any],
    *,
    run_root: Path,
    tile_size: int,
    tolerance_pixels: int,
) -> dict[str, Any]:
    path_value = output.get("dq_map_path")
    path = _resolve_path(path_value, run_root)
    available = _map_available_policy(output, "dq")
    required = available is not False and not _map_skipped(output, "dq")
    if path is None:
        status = "skipped_by_policy" if _map_skipped(output, "dq") else "not_required"
        if required:
            status = "missing_path"
        return {
            "status": status,
            "verified": False,
            "ok": not required,
            "path": path_value,
            "required": required,
        }

    summary = output.get("dq_summary") if isinstance(output.get("dq_summary"), dict) else {}
    if not summary:
        provenance = output.get("dq_provenance_summary")
        provenance_summary = provenance.get("output_dq_summary") if isinstance(provenance, dict) else None
        summary = provenance_summary if isinstance(provenance_summary, dict) else {}
    flags = _dq_flags_to_verify(summary)
    try:
        pixel_summary = summarize_dq_map_pixels(path, flags=flags, tile_size=tile_size)
    except Exception as exc:  # pragma: no cover - exercised by malformed user artifacts
        return {
            "status": "error",
            "verified": False,
            "ok": False,
            "path": path_value,
            "error": str(exc),
        }
    matches = {
        flag: _count_match(
            (pixel_summary.get("counts") or {}).get(flag),
            _summary_count(summary, flag),
            tolerance_pixels,
        )
        for flag in flags
    }
    return {
        "status": "verified",
        "verified": True,
        "ok": all(bool(match.get("passed")) for match in matches.values()),
        "path": path_value,
        "required": required,
        "result": pixel_summary,
        "summary_matches": matches,
    }


def _count_map_required(output: dict[str, Any], map_name: str, integration: dict[str, Any]) -> bool:
    available = _map_available_policy(output, map_name)
    if available is False or _map_skipped(output, map_name):
        return False
    if map_name == "coverage":
        return True
    return _integration_rejection_mode(integration, output) != "none"


def _verify_integration_count_map_pixels(
    output: dict[str, Any],
    *,
    integration: dict[str, Any],
    map_name: str,
    path_key: str,
    expected_dq_flag: str,
    run_root: Path,
    tile_size: int,
    tolerance_pixels: int,
) -> dict[str, Any]:
    path_value = output.get(path_key)
    path = _resolve_path(path_value, run_root)
    required = _count_map_required(output, map_name, integration)
    if path is None:
        status = "skipped_by_policy" if _map_skipped(output, map_name) else "not_required"
        if required:
            status = "missing_path"
        return {
            "status": status,
            "verified": False,
            "ok": not required,
            "path": path_value,
            "required": required,
        }

    try:
        pixel_summary = summarize_count_map_pixels(path, tile_size=tile_size)
    except Exception as exc:  # pragma: no cover - exercised by malformed user artifacts
        return {
            "status": "error",
            "verified": False,
            "ok": False,
            "path": path_value,
            "required": required,
            "error": str(exc),
        }

    dq_summary = output.get("dq_summary") if isinstance(output.get("dq_summary"), dict) else {}
    match_source = "zero_or_less_pixels" if map_name == "coverage" else "positive_pixels"
    match = _count_match(
        pixel_summary.get(match_source),
        _summary_count(dq_summary, expected_dq_flag),
        tolerance_pixels,
    )
    count_integrity = {
        "passed": True,
        "nonfinite_pixels": pixel_summary.get("nonfinite_pixels"),
        "negative_pixels": pixel_summary.get("negative_pixels"),
        "fractional_pixels": pixel_summary.get("fractional_pixels"),
    }
    if map_name in _REJECTION_MAPS:
        count_integrity["passed"] = (
            _optional_rounded_int(pixel_summary.get("nonfinite_pixels")) == 0
            and _optional_rounded_int(pixel_summary.get("negative_pixels")) == 0
            and _optional_rounded_int(pixel_summary.get("fractional_pixels")) == 0
        )
    return {
        "status": "verified",
        "verified": True,
        "ok": bool(match.get("passed")) and bool(count_integrity["passed"]),
        "path": path_value,
        "required": required,
        "result": pixel_summary,
        "count_integrity": count_integrity,
        "summary_match": {expected_dq_flag: match},
    }


def _rejection_sample_sources(output: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    coverage_provenance = (
        output.get("dq_coverage_provenance") if isinstance(output.get("dq_coverage_provenance"), dict) else {}
    )
    provenance_summary = (
        output.get("dq_provenance_summary") if isinstance(output.get("dq_provenance_summary"), dict) else {}
    )
    stack_metrics = output.get("stack_engine_metrics") if isinstance(output.get("stack_engine_metrics"), dict) else {}
    for name, value in [
        ("dq_coverage_provenance.rejected_sample_count", coverage_provenance.get("rejected_sample_count")),
        ("dq_provenance_summary.rejected_samples", provenance_summary.get("rejected_samples")),
    ]:
        count = _optional_rounded_int(value)
        if count is not None:
            sources.append({"name": name, "count": count})
    stack_low = _optional_rounded_int(stack_metrics.get("low_rejected"))
    stack_high = _optional_rounded_int(stack_metrics.get("high_rejected"))
    if stack_low is not None or stack_high is not None:
        sources.append(
            {
                "name": "stack_engine_metrics.low_high_rejected",
                "count": int(stack_low or 0) + int(stack_high or 0),
            }
        )
    return sources


def _sample_accounting_closure_state(output: dict[str, Any]) -> dict[str, Any]:
    summary = output.get("dq_provenance_summary")
    closure = (
        summary.get("sample_accounting_closure")
        if isinstance(summary, dict) and isinstance(summary.get("sample_accounting_closure"), dict)
        else {}
    )
    status = closure.get("status")
    present = status in {"passed", "failed"}
    return {
        "present": present,
        "required": present,
        "status": status or "missing",
        "passed": (not present) or status == "passed",
        "input_total_match": closure.get("input_total_match"),
        "valid_rejection_match": closure.get("valid_rejection_match"),
        "input_samples": closure.get("input_samples"),
        "input_valid_samples_before_rejection": closure.get(
            "input_valid_samples_before_rejection"
        ),
        "input_invalid_samples_before_rejection": closure.get(
            "input_invalid_samples_before_rejection"
        ),
        "valid_samples_after_rejection": closure.get("valid_samples_after_rejection"),
        "rejected_samples": closure.get("rejected_samples"),
        "semantics": closure.get("semantics"),
    }


def _verify_integration_rejection_sample_accounting(
    output: dict[str, Any],
    *,
    integration: dict[str, Any],
    count_maps: dict[str, Any],
    tolerance_pixels: int,
) -> dict[str, Any]:
    rejection = _integration_rejection_mode(integration, output)
    expected = rejection != "none" and any(
        _count_map_required(output, map_name, integration) for map_name in _REJECTION_MAPS
    )
    map_results = {
        map_name: count_maps.get(map_name) or {}
        for map_name in ("low_rejection", "high_rejection")
    }
    verified_results = {
        map_name: row
        for map_name, row in map_results.items()
        if row.get("verified") and isinstance(row.get("result"), dict)
    }
    map_sum = sum(
        int((row.get("result") or {}).get("rounded_sum") or 0)
        for row in verified_results.values()
    )
    integrity = {
        map_name: {
            "verified": bool(row.get("verified")),
            "required": bool(row.get("required")),
            "ok": bool(row.get("ok")),
            "rounded_sum": (row.get("result") or {}).get("rounded_sum")
            if isinstance(row.get("result"), dict)
            else None,
            "positive_pixels": (row.get("result") or {}).get("positive_pixels")
            if isinstance(row.get("result"), dict)
            else None,
            "count_integrity": row.get("count_integrity"),
        }
        for map_name, row in map_results.items()
    }
    sources = _rejection_sample_sources(output)
    matches = [
        {
            "source": source["name"],
            **_count_match(map_sum, source["count"], tolerance_pixels),
        }
        for source in sources
    ]
    required_maps_ok = all(
        (not row.get("required")) or bool(row.get("ok"))
        for row in map_results.values()
    )
    source_match_ok = (not expected) or (bool(matches) and all(bool(match["passed"]) for match in matches))
    ok = (not expected) or (required_maps_ok and source_match_ok)
    return {
        "status": "verified" if verified_results else ("required" if expected else "not_required"),
        "verified": bool(verified_results),
        "ok": ok,
        "required": expected,
        "rejection": rejection,
        "map_rejected_sample_sum": map_sum if verified_results else None,
        "source_counts": sources,
        "source_matches": matches,
        "map_integrity": integrity,
        "semantics": (
            "Low/high rejection count maps store rejected-sample counts; DQ low/high flags "
            "store pixels touched by rejection."
        ),
    }


def _integration_pixel_verification_rows(
    integration: dict[str, Any],
    run_root: Path,
    *,
    tile_size: int,
    tolerance_pixels: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, output in enumerate(integration.get("outputs") or []):
        if not isinstance(output, dict):
            continue
        item = str(output.get("filter") or index)
        count_maps = {
            "coverage": _verify_integration_count_map_pixels(
                output,
                integration=integration,
                map_name="coverage",
                path_key="coverage_map_path",
                expected_dq_flag="no_data",
                run_root=run_root,
                tile_size=tile_size,
                tolerance_pixels=tolerance_pixels,
            ),
            "low_rejection": _verify_integration_count_map_pixels(
                output,
                integration=integration,
                map_name="low_rejection",
                path_key="low_rejection_map_path",
                expected_dq_flag="low_rejected",
                run_root=run_root,
                tile_size=tile_size,
                tolerance_pixels=tolerance_pixels,
            ),
            "high_rejection": _verify_integration_count_map_pixels(
                output,
                integration=integration,
                map_name="high_rejection",
                path_key="high_rejection_map_path",
                expected_dq_flag="high_rejected",
                run_root=run_root,
                tile_size=tile_size,
                tolerance_pixels=tolerance_pixels,
            ),
        }
        rows.append(
            {
                "item": item,
                "dq": _verify_integration_dq_pixels(
                    output,
                    run_root=run_root,
                    tile_size=tile_size,
                    tolerance_pixels=tolerance_pixels,
                ),
                "count_maps": count_maps,
                "rejection_sample_accounting": _verify_integration_rejection_sample_accounting(
                    output,
                    integration=integration,
                    count_maps=count_maps,
                    tolerance_pixels=tolerance_pixels,
                ),
            }
        )
    return rows


def _stack_result_contract_state(output: dict[str, Any]) -> dict[str, Any]:
    provenance = output.get("stack_engine_dq_provenance")
    summary = output.get("dq_provenance_summary")
    tile_mode = str(output.get("tile_stack_mode") or "")
    summary_engine = summary.get("engine") if isinstance(summary, dict) else None
    required = (
        bool(output.get("stack_engine_enabled"))
        or tile_mode.startswith("stack_engine_cpu")
        or summary_engine == "stack_engine_cpu"
    )
    return _stack_result_contract_state_from_provenance(provenance, required=required)


def _resident_result_contract_state(
    output: dict[str, Any],
    *,
    integration: dict[str, Any],
    run_root: Path,
    index: int,
) -> dict[str, Any]:
    required = output.get("backend") == "cuda_resident_stack" or output.get("memory_mode") == "resident"
    if not required:
        return {
            "required": False,
            "present": False,
            "passed": False,
            "status": "not_required",
            "check_count": 0,
            "contract_type": None,
        }
    contract = build_resident_output_contract(
        output,
        run_root=run_root,
        index=index,
        parent_rejection=str(integration.get("rejection") or "none"),
        pixel_verify=False,
    )
    return {
        "required": True,
        "present": True,
        "passed": bool(contract.get("passed")),
        "status": contract.get("status"),
        "check_count": len(contract.get("checks") or []),
        "contract_type": contract.get("contract_type"),
        "contract": contract,
    }


def _is_resident_integration_row(row: dict[str, Any]) -> bool:
    return row.get("backend") == "cuda_resident_stack" or row.get("memory_mode") == "resident"


def _nonempty_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _integration_engine_policy_state(
    integration: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    top_level = _nonempty_dict(integration.get("integration_engine_policy"))
    top_level_present = isinstance(integration.get("integration_engine_policy"), dict)
    top_level_default_ok = top_level.get("default_engine") == "stack_engine_cpu"
    output_states: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for row in rows:
        selection = _nonempty_dict(row.get("engine_selection"))
        selection_present = isinstance(row.get("engine_selection"), dict)
        tile_mode = str(row.get("tile_stack_mode") or selection.get("tile_stack_mode") or "")
        backend = row.get("backend") or selection.get("actual_backend")
        state = {
            "item": row.get("item"),
            "backend": backend,
            "memory_mode": row.get("memory_mode"),
            "tile_stack_mode": tile_mode,
            "top_level_present": top_level_present,
            "top_level_default_engine": top_level.get("default_engine"),
            "top_level_default_ok": top_level_default_ok,
            "selection_present": selection_present,
            "selection_default_engine": selection.get("default_engine"),
            "selection_actual_backend": selection.get("actual_backend"),
            "selection_use_stack_engine": selection.get("use_stack_engine"),
            "selection_explicit_cuda_fast_path": selection.get("explicit_cuda_fast_path"),
            "selection_allow_cuda_fast_path": selection.get(
                "allow_cuda_streaming_accumulator_fast_path"
            ),
            "selection_backend": selection.get("backend"),
            "required": not _is_resident_integration_row(row),
            "passed": True,
            "status": "resident_not_required",
            "failures": [],
        }
        if not state["required"]:
            output_states.append(state)
            continue

        failures: list[str] = []
        if not top_level_present:
            failures.append("missing_top_level_integration_engine_policy")
        if top_level_present and not top_level_default_ok:
            failures.append("top_level_default_engine_not_stack_engine_cpu")
        if not selection_present:
            failures.append("missing_output_engine_selection")
        if selection_present and selection.get("default_engine") != "stack_engine_cpu":
            failures.append("output_default_engine_not_stack_engine_cpu")

        if tile_mode == "stack_engine_cpu":
            if selection_present and selection.get("use_stack_engine") is not True:
                failures.append("stack_engine_output_selection_not_enabled")
            if selection_present and selection.get("actual_backend") != "cpu":
                failures.append("stack_engine_output_actual_backend_not_cpu")
            status = "stack_engine_default"
        elif tile_mode == "cuda_streaming_accumulator_fast_path":
            explicit_flag = selection.get("explicit_cuda_fast_path") is True
            explicit_source = (
                selection.get("allow_cuda_streaming_accumulator_fast_path") is True
                or selection.get("backend") == "cuda"
            )
            if selection_present and selection.get("use_stack_engine") is not False:
                failures.append("cuda_fast_path_selection_still_uses_stack_engine")
            if selection_present and selection.get("actual_backend") != "cuda":
                failures.append("cuda_fast_path_actual_backend_not_cuda")
            if not explicit_flag:
                failures.append("cuda_fast_path_not_explicit")
            if explicit_flag and not explicit_source:
                failures.append("cuda_fast_path_explicit_source_missing")
            status = "explicit_cuda_fast_path" if explicit_flag and explicit_source else "implicit_cuda_fast_path"
        elif tile_mode:
            failures.append("unsupported_non_resident_tile_stack_mode")
            status = "unsupported_non_resident_tile_stack_mode"
        else:
            failures.append("missing_non_resident_tile_stack_mode")
            status = "missing_non_resident_tile_stack_mode"

        state["status"] = status
        state["failures"] = failures
        state["passed"] = not failures
        output_states.append(state)
        if failures:
            failed.append(
                {
                    "item": state["item"],
                    "status": status,
                    "backend": backend,
                    "tile_stack_mode": tile_mode,
                    "failures": failures,
                }
            )

    non_resident_count = sum(1 for state in output_states if state["required"])
    return {
        "top_level": top_level,
        "top_level_present": top_level_present,
        "top_level_default_ok": top_level_default_ok,
        "output_count": len(rows),
        "non_resident_count": non_resident_count,
        "resident_count": len(rows) - non_resident_count,
        "outputs": output_states,
        "failed": failed,
        "passed": bool(rows)
        and (
            non_resident_count == 0
            or (top_level_present and top_level_default_ok and not failed)
        ),
    }


def _stack_engine_runtime_default_state(
    *,
    calibration_master_rows: list[dict[str, Any]],
    integration_rows: list[dict[str, Any]],
    integration_engine_policy: dict[str, Any],
) -> dict[str, Any]:
    master_states: list[dict[str, Any]] = []
    failed_masters: list[dict[str, Any]] = []
    for row in calibration_master_rows:
        tile_mode = str(row.get("tile_stack_mode") or "")
        is_stack_engine = tile_mode.startswith("stack_engine_cpu")
        is_resident_stack = tile_mode == "cuda_resident_stack"
        result_contract = row.get("stack_result_contract") if isinstance(row.get("stack_result_contract"), dict) else {}
        failures: list[str] = []
        if not row.get("contract_ok"):
            failures.append("master_contract_failed")
        if not row.get("stack_engine_enabled"):
            failures.append("master_stack_engine_not_enabled")
        if tile_mode.startswith("legacy"):
            failures.append("legacy_master_stack_mode")
        elif is_stack_engine:
            if result_contract.get("passed") is not True:
                failures.append("stack_result_contract_missing_or_failed")
        elif is_resident_stack:
            pass
        else:
            failures.append("unsupported_master_stack_mode")
        state = {
            "name": row.get("name"),
            "type": row.get("type"),
            "tile_stack_mode": tile_mode,
            "path_exists": row.get("path_exists"),
            "stack_engine_enabled": row.get("stack_engine_enabled"),
            "contract_ok": row.get("contract_ok"),
            "status": "passed" if not failures else "failed",
            "failures": failures,
        }
        master_states.append(state)
        if failures:
            failed_masters.append(state)

    policy_rows = integration_engine_policy.get("outputs")
    policy_rows = policy_rows if isinstance(policy_rows, list) else []
    output_states: list[dict[str, Any]] = []
    failed_outputs: list[dict[str, Any]] = []
    for row in policy_rows:
        if not isinstance(row, dict):
            continue
        failures: list[str] = []
        status = str(row.get("status") or "")
        if row.get("passed") is not True:
            failures.append("integration_engine_policy_failed")
        if status in {"stack_engine_default", "resident_not_required", "explicit_cuda_fast_path"}:
            pass
        elif status:
            failures.append("unsupported_integration_runtime_status")
        else:
            failures.append("missing_integration_runtime_status")
        state = {
            "item": row.get("item"),
            "backend": row.get("backend"),
            "memory_mode": row.get("memory_mode"),
            "tile_stack_mode": row.get("tile_stack_mode"),
            "status": status,
            "passed": row.get("passed") is True and not failures,
            "required": row.get("required"),
            "failures": failures,
        }
        output_states.append(state)
        if failures:
            failed_outputs.append(state)

    stack_contract_failures: list[dict[str, Any]] = []
    resident_contract_failures: list[dict[str, Any]] = []
    for row in integration_rows:
        stack_contract = (
            row.get("stack_result_contract")
            if isinstance(row.get("stack_result_contract"), dict)
            else {}
        )
        resident_contract = (
            row.get("resident_result_contract")
            if isinstance(row.get("resident_result_contract"), dict)
            else {}
        )
        if stack_contract.get("required") and stack_contract.get("passed") is not True:
            stack_contract_failures.append(
                {
                    "item": row.get("item"),
                    "status": stack_contract.get("status"),
                    "tile_stack_mode": row.get("tile_stack_mode"),
                }
            )
        if resident_contract.get("required") and resident_contract.get("passed") is not True:
            resident_contract_failures.append(
                {
                    "item": row.get("item"),
                    "status": resident_contract.get("status"),
                    "tile_stack_mode": row.get("tile_stack_mode"),
                }
            )

    master_required = bool(calibration_master_rows)
    integration_required = bool(policy_rows)
    passed = (
        (not master_required or not failed_masters)
        and integration_required
        and bool(integration_engine_policy.get("passed"))
        and not failed_outputs
    )
    return {
        "passed": passed,
        "status": "passed" if passed else "failed",
        "master_required": master_required,
        "master_count": len(master_states),
        "master_stack_engine_count": sum(
            1 for row in master_states if str(row.get("tile_stack_mode") or "").startswith("stack_engine_cpu")
        ),
        "master_resident_count": sum(
            1 for row in master_states if row.get("tile_stack_mode") == "cuda_resident_stack"
        ),
        "legacy_master_count": sum(
            1 for row in master_states if str(row.get("tile_stack_mode") or "").startswith("legacy")
        ),
        "failed_masters": failed_masters,
        "integration_required": integration_required,
        "integration_output_count": len(output_states),
        "integration_stack_engine_default_count": sum(
            1 for row in output_states if row.get("status") == "stack_engine_default"
        ),
        "integration_resident_count": sum(
            1 for row in output_states if row.get("status") == "resident_not_required"
        ),
        "explicit_cuda_fast_path_count": sum(
            1 for row in output_states if row.get("status") == "explicit_cuda_fast_path"
        ),
        "failed_outputs": failed_outputs,
        "stack_result_contract_failures": stack_contract_failures,
        "resident_result_contract_failures": resident_contract_failures,
        "masters": master_states,
        "outputs": output_states,
        "semantics": (
            "Master calibration surfaces must use StackEngine CPU or resident CUDA "
            "calibration contracts. Non-resident integration defaults to StackEngine CPU; "
            "the older CUDA streaming accumulator remains acceptable only when explicitly "
            "requested and recorded by integration_engine_policy."
        ),
    }


def _integration_rows(integration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, output in enumerate(integration.get("outputs") or []):
        if not isinstance(output, dict):
            continue
        dq_summary = output.get("dq_summary")
        summary = output.get("dq_provenance_summary")
        item = str(output.get("filter") or index)
        dq_available = _map_available_policy(output, "dq")
        dq_required = dq_available is not False and not _map_skipped(output, "dq")
        result_contract = _stack_result_contract_state(output)
        resident_contract = _resident_result_contract_state(
            output,
            integration=integration,
            run_root=run_root,
            index=index,
        )
        sample_closure = _sample_accounting_closure_state(output)
        rows.append(
            {
                "item": item,
                "backend": output.get("backend"),
                "memory_mode": output.get("memory_mode"),
                "rejection": _integration_rejection_mode(integration, output),
                "frame_count": output.get("frame_count"),
                "tile_stack_mode": output.get("tile_stack_mode"),
                "stack_engine_enabled": bool(output.get("stack_engine_enabled")),
                "engine_selection": output.get("engine_selection")
                if isinstance(output.get("engine_selection"), dict)
                else {},
                "dq_map_path": output.get("dq_map_path"),
                "dq_map_exists": _path_exists(output.get("dq_map_path"), run_root),
                "dq_summary_present": isinstance(dq_summary, dict),
                "dq_summary_has_valid": isinstance(dq_summary, dict) and "valid" in dq_summary,
                "dq_provenance_summary_present": isinstance(summary, dict),
                "dq_provenance_engine": summary.get("engine") if isinstance(summary, dict) else None,
                "sample_accounting_closure": sample_closure,
                "stack_result_contract": result_contract,
                "resident_result_contract": resident_contract,
                "dq_contract_ok": (
                    (not dq_required)
                    or (
                        _path_exists(output.get("dq_map_path"), run_root)
                        and isinstance(dq_summary, dict)
                        and "valid" in dq_summary
                        and isinstance(summary, dict)
                    )
                ),
            }
        )
    return rows


def _local_norm_rows(local_norm: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    enabled = bool(local_norm.get("enabled"))
    for item in local_norm.get("local_norm_results") or []:
        if not isinstance(item, dict):
            continue
        has_crop = "crop_box" in item
        dq_path = item.get("dq_mask_path")
        coefficient_path = item.get("coefficient_grid_path")
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "enabled": enabled,
                "status": item.get("status"),
                "crop_box_recorded": has_crop,
                "crop_box": item.get("crop_box") if has_crop else "missing",
                "normalized_path_exists": _path_exists(item.get("normalized_path"), run_root),
                "coverage_path_exists": _path_exists(item.get("coverage_path"), run_root),
                "dq_mask_path_exists": _path_exists(dq_path, run_root) if dq_path else not enabled,
                "dq_summary_present": isinstance(item.get("dq_summary"), dict),
                "coefficient_grid_exists": _path_exists(coefficient_path, run_root) if enabled else True,
                "model": item.get("coefficient_field_model") or item.get("model"),
                "contract_ok": (
                    has_crop
                    and _path_exists(item.get("normalized_path"), run_root)
                    and _path_exists(item.get("coverage_path"), run_root)
                    and (not enabled or bool(item.get("coefficient_field_model") or item.get("model")))
                    and (not enabled or _path_exists(coefficient_path, run_root))
                    and (not dq_path or _path_exists(dq_path, run_root))
                    and isinstance(item.get("dq_summary"), dict)
                ),
            }
        )
    for group in local_norm.get("groups") or []:
        if not isinstance(group, dict):
            continue
        group_enabled = bool(group.get("enabled", enabled))
        group_crop_recorded = "crop_box" in group
        resident_mode = str(group.get("mode") or local_norm.get("mode") or "")
        for item in group.get("frame_results") or []:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "")
            grid_coefficients = item.get("grid_coefficients")
            model = item.get("model") or resident_mode
            coefficient_ok = True
            if group_enabled and "grid" in resident_mode and status not in {"reference", "skipped_zero_weight", "empty"}:
                coefficient_ok = isinstance(grid_coefficients, dict)
            rows.append(
                {
                    "frame_id": item.get("frame_id"),
                    "enabled": group_enabled,
                    "status": status,
                    "crop_box_recorded": group_crop_recorded,
                    "crop_box": group.get("crop_box") if group_crop_recorded else "missing",
                    "normalized_path_exists": True,
                    "coverage_path_exists": True,
                    "dq_mask_path_exists": True,
                    "dq_summary_present": True,
                    "coefficient_grid_exists": coefficient_ok,
                    "model": model,
                    "resident_in_vram": True,
                    "contract_ok": (
                        group_crop_recorded
                        and bool(model)
                        and bool(status)
                        and (not group_enabled or coefficient_ok)
                    ),
                }
            )
    return rows


def _local_norm_contract_state(
    payload: dict[str, Any] | None,
    *,
    local_norm: dict[str, Any],
    local_norm_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "attached": False,
            "passed": None,
            "status": "not_attached",
            "artifact_type": None,
            "enabled": None,
            "output_count": None,
            "failed_output_count": None,
            "summary": {},
            "failed_checks": [],
            "failed_outputs": [],
            "check_rows": [],
        }

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    output_count = _optional_rounded_int(summary.get("output_count"))
    failed_output_count = _optional_rounded_int(summary.get("failed_output_count"))
    failed_checks = [
        str(item.get("name"))
        for item in payload.get("checks") or []
        if isinstance(item, dict) and not item.get("passed")
    ]
    failed_outputs = payload.get("failed_outputs") if isinstance(payload.get("failed_outputs"), list) else []
    enabled_expected = bool(local_norm.get("enabled")) if local_norm else None
    top_level_model = local_norm.get("coefficient_field_model") if local_norm else None
    check_rows = [
        _check(
            "artifact_type_is_local_norm_contract",
            payload.get("artifact_type") == "local_norm_contract",
            {"artifact_type": payload.get("artifact_type")},
        ),
        _check(
            "contract_status_passed",
            payload.get("status") == "passed" and payload.get("passed") is True,
            {"status": payload.get("status"), "passed": payload.get("passed")},
        ),
        _check(
            "enabled_state_matches_run",
            enabled_expected is None or payload.get("enabled") == enabled_expected,
            {"contract_enabled": payload.get("enabled"), "run_enabled": enabled_expected},
        ),
        _check(
            "output_count_matches_pipeline_rows",
            output_count == len(local_norm_rows),
            {"contract_output_count": output_count, "pipeline_row_count": len(local_norm_rows)},
        ),
        _check(
            "failed_output_count_zero",
            failed_output_count == 0,
            {"failed_output_count": failed_output_count},
        ),
        _check(
            "top_level_failed_checks_empty",
            not failed_checks,
            {"failed_checks": failed_checks},
        ),
        _check(
            "coefficient_field_model_matches_run",
            top_level_model is None or payload.get("coefficient_field_model") == top_level_model,
            {
                "contract_coefficient_field_model": payload.get("coefficient_field_model"),
                "run_coefficient_field_model": top_level_model,
            },
        ),
    ]
    return {
        "attached": True,
        "passed": all(row["passed"] for row in check_rows),
        "status": payload.get("status"),
        "artifact_type": payload.get("artifact_type"),
        "enabled": payload.get("enabled"),
        "output_count": output_count,
        "failed_output_count": failed_output_count,
        "summary": summary,
        "failed_checks": failed_checks,
        "failed_outputs": failed_outputs,
        "check_rows": check_rows,
    }


def _warp_rows(warp: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in warp.get("warp_results") or []:
        if not isinstance(item, dict):
            continue
        dq_summary = item.get("dq_summary")
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "interpolation": item.get("interpolation"),
                "registered_path_exists": _path_exists(item.get("registered_path"), run_root),
                "coverage_path_exists": _path_exists(item.get("coverage_path"), run_root),
                "dq_mask_path_exists": _path_exists(item.get("dq_mask_path"), run_root),
                "dq_summary_present": isinstance(dq_summary, dict),
                "dq_summary_has_valid": isinstance(dq_summary, dict) and "valid" in dq_summary,
                "contract_ok": (
                    _path_exists(item.get("registered_path"), run_root)
                    and _path_exists(item.get("coverage_path"), run_root)
                    and _path_exists(item.get("dq_mask_path"), run_root)
                    and isinstance(dq_summary, dict)
                    and "valid" in dq_summary
                ),
            }
        )
    return rows


def _skipped_warp_rows(warp: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in warp.get("skipped_frames") or []:
        if isinstance(item, dict):
            rows.append(
                {
                    "frame_id": item.get("frame_id"),
                    "status": item.get("status"),
                    "has_reason": bool(item.get("reason")),
                    "contract_ok": bool(item.get("frame_id") and item.get("status") and item.get("reason")),
                }
            )
    return rows


def _frame_accounting_admission_state(frame_accounting: dict[str, Any]) -> dict[str, Any]:
    summary = frame_accounting.get("summary") if isinstance(frame_accounting.get("summary"), dict) else {}
    frames = frame_accounting.get("frames") if isinstance(frame_accounting.get("frames"), list) else []
    conflicts: list[dict[str, Any]] = []
    for row in frames:
        if not isinstance(row, dict):
            continue
        conflict_count = _optional_rounded_int(row.get("integration_conflict_count")) or 0
        if row.get("final_status") == "integration_conflict" or conflict_count > 0:
            conflicts.append(
                {
                    "frame_id": row.get("frame_id"),
                    "final_status": row.get("final_status"),
                    "integration_status": row.get("integration_status"),
                    "integration_weight": row.get("integration_weight"),
                    "quality_gate_status": row.get("quality_gate_status"),
                    "registration_status": row.get("registration_status"),
                    "warp_status": row.get("warp_status"),
                    "local_norm_status": row.get("local_norm_status"),
                    "integration_conflict_count": conflict_count,
                    "integration_conflicts": row.get("integration_conflicts")
                    if isinstance(row.get("integration_conflicts"), list)
                    else [],
                }
            )
    summary_conflicts = _summary_count(summary, "integration_conflict_frames")
    conflict_count = max(len(conflicts), int(summary_conflicts or 0))
    return {
        "present": bool(frame_accounting),
        "status": "not_present" if not frame_accounting else ("failed" if conflict_count else "passed"),
        "frame_count": len(frames),
        "input_light_frames": _summary_count(summary, "input_light_frames"),
        "integrated_frames": _summary_count(summary, "integrated_frames"),
        "zero_weight_frames": _summary_count(summary, "zero_weight_frames"),
        "exception_frames": _summary_count(summary, "exception_frames"),
        "integration_conflict_frames": conflict_count,
        "final_status_counts": summary.get("final_status_counts") if isinstance(summary.get("final_status_counts"), dict) else {},
        "integration_conflicts": conflicts,
        "passed": not frame_accounting or conflict_count == 0,
    }


def _resident_source_dq_execution_state(run_root: Path) -> dict[str, Any]:
    path = run_root / "resident_source_dq_execution.json"
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "required": False,
            "status": "not_present",
            "passed": True,
            "summary": {},
            "groups": [],
            "failed_groups": [],
            "check_count": 0,
            "failed_checks": [],
        }

    payload = _load_json_object(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    raw_groups = payload.get("groups") if isinstance(payload.get("groups"), list) else []
    groups = [group for group in raw_groups if isinstance(group, dict)]
    failed_groups: list[dict[str, Any]] = []
    failed_checks: list[dict[str, Any]] = []
    check_count = 0
    for group in groups:
        group_failures: list[str] = []
        for check in group.get("checks") or []:
            if not isinstance(check, dict):
                continue
            check_count += 1
            if not check.get("passed"):
                name = str(check.get("name") or "unknown")
                group_failures.append(name)
                failed_checks.append(
                    {
                        "filter": group.get("filter"),
                        "check": name,
                        "details": check.get("details") if isinstance(check.get("details"), dict) else {},
                    }
                )
        input_invalid = _optional_rounded_int(group.get("input_invalid_samples_before_rejection"))
        applied_invalid = _optional_rounded_int(group.get("applied_invalid_samples"))
        if input_invalid is not None and applied_invalid is not None and input_invalid != applied_invalid:
            group_failures.append("invalid_samples_not_fully_applied")
            failed_checks.append(
                {
                    "filter": group.get("filter"),
                    "check": "invalid_samples_not_fully_applied",
                    "details": {
                        "input_invalid_samples_before_rejection": input_invalid,
                        "applied_invalid_samples": applied_invalid,
                    },
                }
            )
        if group.get("materializes_calibrated_dq_cache") is True:
            group_failures.append("materializes_calibrated_dq_cache")
            failed_checks.append(
                {
                    "filter": group.get("filter"),
                    "check": "materializes_calibrated_dq_cache",
                    "details": {"materializes_calibrated_dq_cache": True},
                }
            )
        if group.get("passed") is not True or group_failures:
            failed_groups.append(
                {
                    "filter": group.get("filter"),
                    "status": group.get("status"),
                    "failures": group_failures,
                }
            )

    malformed = not payload or payload.get("artifact") != "resident_source_dq_execution"
    summary_passed = summary.get("passed") is True
    groups_present = bool(groups)
    passed = (not malformed) and summary_passed and groups_present and not failed_groups and not failed_checks
    return {
        "path": str(path),
        "exists": True,
        "required": True,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "artifact": payload.get("artifact"),
        "summary": summary,
        "groups": [
            {
                "filter": group.get("filter"),
                "status": group.get("status"),
                "passed": group.get("passed"),
                "execution_route": group.get("execution_route"),
                "native_method": group.get("native_method"),
                "native_methods": group.get("native_methods"),
                "frame_count": group.get("frame_count"),
                "frame_with_invalid_count": group.get("frame_with_invalid_count"),
                "applied_frame_count": group.get("applied_frame_count"),
                "input_invalid_samples_before_rejection": group.get("input_invalid_samples_before_rejection"),
                "applied_invalid_samples": group.get("applied_invalid_samples"),
                "input_flagged_samples": group.get("input_flagged_samples"),
                "input_nonfinite_samples": group.get("input_nonfinite_samples"),
                "source_dq_flag_counts": group.get("source_dq_flag_counts"),
                "source_counts": group.get("source_counts"),
                "status_counts": group.get("status_counts"),
                "materializes_calibrated_dq_cache": group.get("materializes_calibrated_dq_cache"),
                "streaming_memory": group.get("streaming_memory"),
                "check_count": len([item for item in group.get("checks") or [] if isinstance(item, dict)]),
            }
            for group in groups
        ],
        "failed_groups": failed_groups,
        "check_count": check_count,
        "failed_checks": failed_checks,
        "malformed": malformed,
        "summary_passed": summary_passed,
        "groups_present": groups_present,
    }


def _resident_frame_mask_state(
    run_root: Path,
    *,
    required: bool,
    frame_accounting: dict[str, Any],
) -> dict[str, Any]:
    path = run_root / "resident_frame_masks.json"
    if not path.exists():
        status = "missing" if required else "not_present"
        return {
            "path": str(path),
            "exists": False,
            "required": bool(required),
            "status": status,
            "passed": not required,
            "summary": {},
            "groups": [],
            "failed_groups": [],
            "failed_checks": ["resident_frame_masks_missing"] if required else [],
            "closure": {"status": "missing" if required else "not_required", "passed": not required},
        }

    payload = _load_json_object(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    raw_groups = payload.get("groups") if isinstance(payload.get("groups"), list) else []
    groups = [group for group in raw_groups if isinstance(group, dict)]
    accounting_summary = (
        frame_accounting.get("summary") if isinstance(frame_accounting.get("summary"), dict) else {}
    )
    frame_count = _optional_rounded_int(summary.get("frame_count"))
    active_count = _optional_rounded_int(summary.get("active_frame_count"))
    masked_count = _optional_rounded_int(summary.get("masked_frame_count"))
    unknown_count = _optional_rounded_int(summary.get("unknown_zero_weight_frame_count"))
    input_light_frames = _optional_rounded_int(accounting_summary.get("input_light_frames"))
    integrated_frames = _optional_rounded_int(accounting_summary.get("integrated_frames"))
    zero_weight_frames = _optional_rounded_int(accounting_summary.get("zero_weight_frames"))
    accounting_mask_active = _optional_rounded_int(accounting_summary.get("resident_frame_mask_active_frames"))
    accounting_masked = _optional_rounded_int(accounting_summary.get("resident_frame_mask_masked_frames"))
    accounting_unknown = _optional_rounded_int(accounting_summary.get("resident_frame_mask_unaudited_frames"))

    failed_groups: list[dict[str, Any]] = []
    for index, group in enumerate(groups):
        group_summary = group.get("summary") if isinstance(group.get("summary"), dict) else {}
        group_unknown = _optional_rounded_int(group_summary.get("unknown_zero_weight_frame_count"))
        if group.get("artifact") != "resident_frame_mask_contract_group" or group_summary.get("passed") is not True or group_unknown not in {0, None}:
            failed_groups.append(
                {
                    "index": index,
                    "filter": group.get("filter"),
                    "artifact": group.get("artifact"),
                    "passed": group_summary.get("passed"),
                    "unknown_zero_weight_frame_count": group_summary.get("unknown_zero_weight_frame_count"),
                }
            )

    checks = [
        _check(
            "resident_frame_masks_present",
            True,
            {"path": str(path), "required": bool(required)},
        ),
        _check(
            "artifact_type_is_resident_frame_mask_contract",
            payload.get("artifact") == "resident_frame_mask_contract",
            {"artifact": payload.get("artifact")},
        ),
        _check(
            "summary_passed",
            summary.get("passed") is True,
            {"passed": summary.get("passed")},
        ),
        _check(
            "groups_present",
            bool(groups),
            {"group_count": len(groups)},
        ),
        _check(
            "group_contracts_passed",
            not failed_groups,
            {"failed_groups": failed_groups},
        ),
        _check(
            "unknown_zero_weight_frames_zero",
            unknown_count == 0,
            {
                "unknown_zero_weight_frame_count": unknown_count,
                "unknown_zero_weight_frame_ids": (summary.get("unknown_zero_weight_frame_ids") or [])[:20],
            },
        ),
    ]
    if frame_accounting:
        checks.extend(
            [
                _check(
                    "frame_count_matches_frame_accounting_input",
                    frame_count == input_light_frames,
                    {
                        "frame_mask_frame_count": frame_count,
                        "frame_accounting_input_light_frames": input_light_frames,
                    },
                ),
                _check(
                    "active_count_matches_integrated_frames",
                    active_count == integrated_frames,
                    {
                        "frame_mask_active_frame_count": active_count,
                        "frame_accounting_integrated_frames": integrated_frames,
                    },
                ),
                _check(
                    "masked_count_matches_zero_weight_frames",
                    masked_count == zero_weight_frames,
                    {
                        "frame_mask_masked_frame_count": masked_count,
                        "frame_accounting_zero_weight_frames": zero_weight_frames,
                    },
                ),
                _check(
                    "frame_accounting_resident_mask_counts_match",
                    (
                        accounting_mask_active in {None, active_count}
                        and accounting_masked in {None, masked_count}
                        and accounting_unknown in {None, unknown_count}
                    ),
                    {
                        "frame_mask_active_frame_count": active_count,
                        "frame_mask_masked_frame_count": masked_count,
                        "frame_mask_unknown_zero_weight_frame_count": unknown_count,
                        "frame_accounting_resident_frame_mask_active_frames": accounting_mask_active,
                        "frame_accounting_resident_frame_mask_masked_frames": accounting_masked,
                        "frame_accounting_resident_frame_mask_unaudited_frames": accounting_unknown,
                    },
                ),
            ]
        )

    passed = all(item["passed"] for item in checks)
    return {
        "path": str(path),
        "exists": True,
        "required": bool(required),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "artifact": payload.get("artifact"),
        "summary": summary,
        "groups": [
            {
                "filter": group.get("filter"),
                "artifact": group.get("artifact"),
                "registration_mode": group.get("registration_mode"),
                "integration_dispatch": group.get("integration_dispatch"),
                "summary": group.get("summary") if isinstance(group.get("summary"), dict) else {},
            }
            for group in groups
        ],
        "failed_groups": failed_groups,
        "closure": {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "frame_count": frame_count,
            "active_frame_count": active_count,
            "masked_frame_count": masked_count,
            "unknown_zero_weight_frame_count": unknown_count,
            "input_light_frames": input_light_frames,
            "integrated_frames": integrated_frames,
            "zero_weight_frames": zero_weight_frames,
        },
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
    }


def _resident_registration_quality_state(
    run_root: Path,
    *,
    required: bool,
    frame_accounting: dict[str, Any],
    resident_frame_mask: dict[str, Any],
) -> dict[str, Any]:
    path = run_root / "resident_registration_quality.json"
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "required": bool(required),
            "status": "missing" if required else "not_present",
            "passed": not required,
            "summary": {},
            "groups": [],
            "failed_checks": ["resident_registration_quality_missing"] if required else [],
            "closure": {"status": "missing" if required else "not_required", "passed": not required},
        }

    payload = _load_json_object(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    decisions_raw = payload.get("decisions") if isinstance(payload.get("decisions"), list) else []
    decisions = [item for item in decisions_raw if isinstance(item, dict)]
    registration_mode = str(payload.get("registration_mode") or "")
    mode_off = registration_mode in {"off", "none", "disabled"}
    quality_closure_required = (
        required
        and not mode_off
        and (
            registration_mode == "similarity_cuda_triangle"
            or bool(decisions)
            or (_optional_rounded_int(summary.get("frame_count")) or 0) > 0
        )
    )
    accounting_summary = (
        frame_accounting.get("summary") if isinstance(frame_accounting.get("summary"), dict) else {}
    )
    frame_mask_summary = resident_frame_mask.get("summary") if isinstance(resident_frame_mask.get("summary"), dict) else {}
    input_light_frames = _optional_rounded_int(accounting_summary.get("input_light_frames"))
    integrated_frames = _optional_rounded_int(accounting_summary.get("integrated_frames"))
    zero_weight_frames = _optional_rounded_int(accounting_summary.get("zero_weight_frames"))
    frame_mask_active = _optional_rounded_int(frame_mask_summary.get("active_frame_count"))
    frame_mask_masked = _optional_rounded_int(frame_mask_summary.get("masked_frame_count"))
    summary_frame_count = _optional_rounded_int(summary.get("frame_count"))
    summary_rejected_ids = {str(item) for item in summary.get("rejected_frame_ids") or []}
    mask_masked_ids = {str(item) for item in frame_mask_summary.get("masked_frame_ids") or []}
    decision_frame_ids = [str(item.get("frame_id")) for item in decisions if item.get("frame_id")]
    decision_status_values = [str(item.get("decision_status") or "unknown") for item in decisions]
    decision_status_counts_from_rows = {
        status: decision_status_values.count(status) for status in set(decision_status_values)
    }
    duplicate_frame_ids = _duplicates(decision_frame_ids)
    rejected_decision_ids = {
        str(item.get("frame_id"))
        for item in decisions
        if item.get("frame_id")
        and (
            str(item.get("decision_status") or "") == "rejected"
            or str(item.get("final_status") or "") == "excluded"
            or str(item.get("action_applied") or "") == "exclude"
        )
    }
    active_decision_count = sum(
        int(decision_status_counts_from_rows.get(key) or 0)
        for key in ("accepted", "reference", "disabled")
    )
    rejected_decision_count = len(rejected_decision_ids)
    unsupported_statuses = sorted(
        set(decision_status_values).difference(
            {
                "accepted",
                "reference",
                "rejected",
                "warning",
                "disabled",
                "already_excluded",
                "already_failed",
                "not_applicable",
            }
        )
    )

    checks = [
        _check(
            "resident_registration_quality_present",
            True,
            {"path": str(path), "required": bool(required)},
        ),
        _check(
            "schema_version_recorded",
            _positive_int(payload.get("schema_version")),
            {"schema_version": payload.get("schema_version")},
        ),
        _check(
            "source_stage_is_resident",
            payload.get("source_stage") == "resident_calibrated_stack",
            {"source_stage": payload.get("source_stage")},
        ),
        _check(
            "registration_mode_recorded",
            bool(registration_mode),
            {"registration_mode": registration_mode},
        ),
        _check(
            "decisions_are_objects",
            len(decisions) == len(decisions_raw),
            {"decision_count": len(decisions_raw), "object_decision_count": len(decisions)},
        ),
        _check(
            "summary_frame_count_matches_decisions",
            summary_frame_count == len(decisions),
            {"summary_frame_count": summary_frame_count, "decision_count": len(decisions)},
        ),
        _check(
            "decision_frame_ids_unique",
            not duplicate_frame_ids,
            {"duplicate_frame_ids": duplicate_frame_ids[:20]},
        ),
        _check(
            "decision_statuses_supported",
            not unsupported_statuses,
            {"unsupported_statuses": unsupported_statuses},
        ),
        _check(
            "summary_rejected_ids_match_decisions",
            summary_rejected_ids == rejected_decision_ids,
            {
                "summary_rejected_frame_ids": sorted(summary_rejected_ids),
                "decision_rejected_frame_ids": sorted(rejected_decision_ids),
            },
        ),
    ]
    if quality_closure_required:
        checks.extend(
            [
                _check(
                    "decision_count_matches_input_light_frames",
                    input_light_frames is None or len(decisions) == input_light_frames,
                    {"decision_count": len(decisions), "input_light_frames": input_light_frames},
                ),
                _check(
                    "active_decision_count_matches_integrated_frames",
                    integrated_frames is None or active_decision_count == integrated_frames,
                    {
                        "active_decision_count": active_decision_count,
                        "integrated_frames": integrated_frames,
                    },
                ),
                _check(
                    "rejected_decision_count_matches_zero_weight_frames",
                    zero_weight_frames is None or rejected_decision_count == zero_weight_frames,
                    {
                        "rejected_decision_count": rejected_decision_count,
                        "zero_weight_frames": zero_weight_frames,
                    },
                ),
                _check(
                    "active_decision_count_matches_frame_masks",
                    frame_mask_active is None or active_decision_count == frame_mask_active,
                    {
                        "active_decision_count": active_decision_count,
                        "frame_mask_active_frame_count": frame_mask_active,
                    },
                ),
                _check(
                    "rejected_decisions_match_masked_frames",
                    (not mask_masked_ids and frame_mask_masked in {0, None})
                    or rejected_decision_ids == mask_masked_ids,
                    {
                        "rejected_decision_frame_ids": sorted(rejected_decision_ids),
                        "frame_mask_masked_frame_ids": sorted(mask_masked_ids),
                        "frame_mask_masked_frame_count": frame_mask_masked,
                    },
                ),
            ]
        )

    passed = all(item["passed"] for item in checks)
    return {
        "path": str(path),
        "exists": True,
        "required": bool(required),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "schema_version": payload.get("schema_version"),
        "source_stage": payload.get("source_stage"),
        "registration_mode": registration_mode,
        "requested_action": payload.get("requested_action"),
        "min_inliers": payload.get("min_inliers"),
        "max_rms_px": payload.get("max_rms_px"),
        "summary": summary,
        "closure": {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "mode_off": mode_off,
            "quality_closure_required": quality_closure_required,
            "decision_count": len(decisions),
            "summary_frame_count": summary_frame_count,
            "active_decision_count": active_decision_count,
            "rejected_decision_count": rejected_decision_count,
            "input_light_frames": input_light_frames,
            "integrated_frames": integrated_frames,
            "zero_weight_frames": zero_weight_frames,
            "frame_mask_active_frame_count": frame_mask_active,
            "frame_mask_masked_frame_count": frame_mask_masked,
            "rejected_decision_frame_ids": sorted(rejected_decision_ids),
            "frame_mask_masked_frame_ids": sorted(mask_masked_ids),
        },
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "checks": checks,
    }


def _resident_dq_pixel_closure_state(
    run_root: Path,
    *,
    required: bool,
    resident_frame_mask: dict[str, Any],
) -> dict[str, Any]:
    path = run_root / "resident_dq_pixel_closure.json"
    if not path.exists():
        status = "missing" if required else "not_present"
        return {
            "path": str(path),
            "exists": False,
            "required": bool(required),
            "status": status,
            "passed": not required,
            "summary": {},
            "groups": [],
            "failed_groups": [],
            "failed_checks": ["resident_dq_pixel_closure_missing"] if required else [],
            "group_failed_checks": [],
            "closure": {"status": "missing" if required else "not_required", "passed": not required},
        }

    payload = _load_json_object(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    raw_groups = payload.get("groups") if isinstance(payload.get("groups"), list) else []
    groups = [group for group in raw_groups if isinstance(group, dict)]
    frame_mask_summary = resident_frame_mask.get("summary") if isinstance(resident_frame_mask.get("summary"), dict) else {}
    frame_mask_active = _optional_rounded_int(frame_mask_summary.get("active_frame_count"))
    frame_mask_masked = _optional_rounded_int(frame_mask_summary.get("masked_frame_count"))

    failed_groups: list[dict[str, Any]] = []
    failed_checks: list[dict[str, Any]] = []
    active_counts: list[int] = []
    masked_counts: list[int] = []
    for index, group in enumerate(groups):
        group_failures: list[str] = []
        active = _optional_rounded_int(group.get("frame_mask_active_frame_count"))
        masked = _optional_rounded_int(group.get("frame_mask_masked_frame_count"))
        if active is not None:
            active_counts.append(active)
        if masked is not None:
            masked_counts.append(masked)
        if group.get("artifact") != "resident_dq_pixel_closure_group":
            group_failures.append("artifact_type")
        if group.get("passed") is not True or group.get("status") != "passed":
            group_failures.append("group_status")
        for check in group.get("checks") or []:
            if not isinstance(check, dict):
                continue
            if not check.get("passed"):
                name = str(check.get("name") or "unknown")
                group_failures.append(name)
                failed_checks.append(
                    {
                        "index": index,
                        "filter": group.get("filter"),
                        "check": name,
                        "details": check.get("details") if isinstance(check.get("details"), dict) else {},
                    }
                )
        if group_failures:
            failed_groups.append(
                {
                    "index": index,
                    "filter": group.get("filter"),
                    "status": group.get("status"),
                    "failures": group_failures,
                }
            )

    active_total = sum(active_counts) if active_counts else None
    masked_total = sum(masked_counts) if masked_counts else None
    checks = [
        _check(
            "resident_dq_pixel_closure_present",
            True,
            {"path": str(path), "required": bool(required)},
        ),
        _check(
            "artifact_type_is_resident_dq_pixel_closure",
            payload.get("artifact") == "resident_dq_pixel_closure",
            {"artifact": payload.get("artifact")},
        ),
        _check(
            "summary_passed",
            summary.get("passed") is True and _optional_rounded_int(summary.get("failed_group_count")) == 0,
            {
                "passed": summary.get("passed"),
                "failed_group_count": summary.get("failed_group_count"),
                "failed_check_counts": summary.get("failed_check_counts"),
            },
        ),
        _check("groups_present", bool(groups), {"group_count": len(groups)}),
        _check("group_closures_passed", not failed_groups and not failed_checks, {"failed_groups": failed_groups, "failed_checks": failed_checks}),
    ]
    if resident_frame_mask.get("exists"):
        checks.extend(
            [
                _check(
                    "active_count_matches_resident_frame_mask",
                    active_total == frame_mask_active,
                    {
                        "dq_closure_active_frame_count": active_total,
                        "frame_mask_active_frame_count": frame_mask_active,
                    },
                ),
                _check(
                    "masked_count_matches_resident_frame_mask",
                    masked_total == frame_mask_masked,
                    {
                        "dq_closure_masked_frame_count": masked_total,
                        "frame_mask_masked_frame_count": frame_mask_masked,
                    },
                ),
            ]
        )

    passed = all(item["passed"] for item in checks)
    return {
        "path": str(path),
        "exists": True,
        "required": bool(required),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "artifact": payload.get("artifact"),
        "summary": summary,
        "groups": [
            {
                "filter": group.get("filter"),
                "artifact": group.get("artifact"),
                "status": group.get("status"),
                "passed": group.get("passed"),
                "frame_mask_active_frame_count": group.get("frame_mask_active_frame_count"),
                "frame_mask_masked_frame_count": group.get("frame_mask_masked_frame_count"),
                "geometric_warp_coverage_frame_count": group.get("geometric_warp_coverage_frame_count"),
                "provenance_active_frame_count": group.get("provenance_active_frame_count"),
                "sample_accounting_closure": group.get("sample_accounting_closure"),
                "check_count": len([item for item in group.get("checks") or [] if isinstance(item, dict)]),
            }
            for group in groups
        ],
        "failed_groups": failed_groups,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "group_failed_checks": failed_checks,
        "closure": {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "active_frame_count": active_total,
            "masked_frame_count": masked_total,
            "frame_mask_active_frame_count": frame_mask_active,
            "frame_mask_masked_frame_count": frame_mask_masked,
        },
        "checks": checks,
    }


def build_pipeline_contract_audit(
    run_dir: str | Path,
    *,
    pixel_verify: bool = False,
    pixel_verify_tile_size: int = 2048,
    pixel_tolerance: int = 0,
    resident_calibration_contract: dict[str, Any] | None = None,
    local_norm_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    calibration_path = run_root / "calibration_artifacts.json"
    warp_path = run_root / "warp_results.json"
    local_norm_path = run_root / "local_norm_results.json"
    integration_path = run_root / "integration_results.json"
    frame_accounting_path = run_root / "frame_accounting.json"
    calibration = _load_json_object(calibration_path)
    calibration_path_exists = calibration_path.exists()
    if not calibration:
        calibration = _resident_calibration_artifact_from_resident_artifacts(run_root)
    calibration_artifact_present = bool(calibration)
    warp = _load_json_object(warp_path)
    local_norm = _load_json_object(local_norm_path)
    integration = _load_json_object(integration_path)
    frame_accounting = _load_json_object(frame_accounting_path)

    local_calibration_master_rows = _calibration_master_rows(calibration, run_root)
    resident_calibration_rows = _resident_calibration_rows(resident_calibration_contract)
    calibration_master_rows = [*local_calibration_master_rows, *resident_calibration_rows]
    calibrated_light_rows = _calibrated_light_rows(calibration, run_root)
    local_calibrated_light_rows = [row for row in calibrated_light_rows if not row.get("resident")]
    resident_calibrated_light_rows = [row for row in calibrated_light_rows if row.get("resident")]
    resident_native_calibration = (
        calibration.get("artifact_type") == "resident_cuda_calibration_artifacts"
        or calibration.get("source_stage") == "resident_calibrated_stack"
    )
    warp_rows = _warp_rows(warp, run_root)
    skipped_warp_rows = _skipped_warp_rows(warp)
    local_norm_rows = _local_norm_rows(local_norm, run_root)
    local_norm_contract_state = _local_norm_contract_state(
        local_norm_contract,
        local_norm=local_norm,
        local_norm_rows=local_norm_rows,
    )
    integration_rows = _integration_rows(integration, run_root)
    integration_map_rows = _integration_map_rows(integration, run_root)
    integration_engine_policy = _integration_engine_policy_state(integration, integration_rows)
    frame_accounting_admission = _frame_accounting_admission_state(frame_accounting)
    resident_source_dq_execution = _resident_source_dq_execution_state(run_root)
    resident_integration_required = any(_is_resident_integration_row(row) for row in integration_rows)
    resident_frame_mask = _resident_frame_mask_state(
        run_root,
        required=resident_integration_required,
        frame_accounting=frame_accounting,
    )
    resident_registration_quality = _resident_registration_quality_state(
        run_root,
        required=resident_integration_required,
        frame_accounting=frame_accounting,
        resident_frame_mask=resident_frame_mask,
    )
    resident_dq_pixel_closure = _resident_dq_pixel_closure_state(
        run_root,
        required=resident_integration_required,
        resident_frame_mask=resident_frame_mask,
    )
    stack_engine_runtime_default = _stack_engine_runtime_default_state(
        calibration_master_rows=calibration_master_rows,
        integration_rows=integration_rows,
        integration_engine_policy=integration_engine_policy,
    )
    pixel_verification_rows = (
        _integration_pixel_verification_rows(
            integration,
            run_root,
            tile_size=max(1, int(pixel_verify_tile_size)),
            tolerance_pixels=max(0, int(pixel_tolerance)),
        )
        if pixel_verify
        else []
    )

    checks = [
        _check("integration_artifact_exists", integration_path.exists(), {"path": str(integration_path)}),
        _check(
            "integration_outputs_present",
            bool(integration_rows),
            {"actual": len(integration_rows), "required_min": 1},
        ),
        _check(
            "integration_default_engine_policy",
            bool(integration_rows) and bool(integration_engine_policy["passed"]),
            {
                "output_count": integration_engine_policy["output_count"],
                "non_resident_count": integration_engine_policy["non_resident_count"],
                "resident_count": integration_engine_policy["resident_count"],
                "top_level_present": integration_engine_policy["top_level_present"],
                "top_level_default_ok": integration_engine_policy["top_level_default_ok"],
                "failed": integration_engine_policy["failed"],
            },
            "Non-resident integration must default to StackEngine unless the CUDA fast path is explicitly requested.",
        ),
        _check(
            "stack_engine_runtime_default_path",
            bool(stack_engine_runtime_default["passed"]),
            {
                "master_count": stack_engine_runtime_default["master_count"],
                "master_stack_engine_count": stack_engine_runtime_default[
                    "master_stack_engine_count"
                ],
                "master_resident_count": stack_engine_runtime_default[
                    "master_resident_count"
                ],
                "legacy_master_count": stack_engine_runtime_default["legacy_master_count"],
                "integration_output_count": stack_engine_runtime_default[
                    "integration_output_count"
                ],
                "integration_stack_engine_default_count": stack_engine_runtime_default[
                    "integration_stack_engine_default_count"
                ],
                "integration_resident_count": stack_engine_runtime_default[
                    "integration_resident_count"
                ],
                "explicit_cuda_fast_path_count": stack_engine_runtime_default[
                    "explicit_cuda_fast_path_count"
                ],
                "failed_masters": stack_engine_runtime_default["failed_masters"],
                "failed_outputs": stack_engine_runtime_default["failed_outputs"],
                "stack_result_contract_failures": stack_engine_runtime_default[
                    "stack_result_contract_failures"
                ],
                "resident_result_contract_failures": stack_engine_runtime_default[
                    "resident_result_contract_failures"
                ],
            },
            "Runtime artifacts must preserve StackEngine master calibration and StackEngine/resident integration defaults.",
        ),
        _check(
            "integration_output_maps_available",
            bool(integration_map_rows) and all(row["ok"] for row in integration_map_rows),
            {
                "map_count": len(integration_map_rows),
                "failed": [
                    f"{row['item']}:{row['map']}"
                    for row in integration_map_rows
                    if not row["ok"]
                ],
            },
        ),
        _check(
            "integration_dq_contract",
            bool(integration_rows) and all(row["dq_contract_ok"] for row in integration_rows),
            {
                "output_count": len(integration_rows),
                "failed": [row["item"] for row in integration_rows if not row["dq_contract_ok"]],
            },
        ),
        _check(
            "integration_stack_result_contract",
            bool(integration_rows)
            and all(
                (not row["stack_result_contract"]["required"]) or row["stack_result_contract"]["passed"]
                for row in integration_rows
            ),
            {
                "output_count": len(integration_rows),
                "required_count": sum(1 for row in integration_rows if row["stack_result_contract"]["required"]),
                "failed": [
                    row["item"]
                    for row in integration_rows
                    if row["stack_result_contract"]["required"] and not row["stack_result_contract"]["passed"]
                ],
            },
            "CPU StackEngine integration outputs must carry an embedded passing result contract.",
        ),
        _check(
            "integration_resident_result_contract",
            bool(integration_rows)
            and all(
                (not row["resident_result_contract"]["required"]) or row["resident_result_contract"]["passed"]
                for row in integration_rows
            ),
            {
                "output_count": len(integration_rows),
                "required_count": sum(1 for row in integration_rows if row["resident_result_contract"]["required"]),
                "failed": [
                    row["item"]
                    for row in integration_rows
                    if row["resident_result_contract"]["required"] and not row["resident_result_contract"]["passed"]
                ],
            },
            "Resident CUDA integration outputs must satisfy the resident result-contract audit.",
        ),
        _check(
            "resident_source_dq_execution_contract",
            bool(resident_source_dq_execution["passed"]),
            {
                "exists": resident_source_dq_execution["exists"],
                "required": resident_source_dq_execution["required"],
                "status": resident_source_dq_execution["status"],
                "summary_status": (resident_source_dq_execution["summary"] or {}).get("status"),
                "summary_passed": resident_source_dq_execution.get("summary_passed"),
                "group_count": len(resident_source_dq_execution["groups"]),
                "check_count": resident_source_dq_execution["check_count"],
                "failed_groups": resident_source_dq_execution["failed_groups"],
                "failed_checks": resident_source_dq_execution["failed_checks"],
                "materializes_calibrated_dq_cache": (
                    resident_source_dq_execution["summary"] or {}
                ).get("materializes_calibrated_dq_cache"),
            },
            "When resident source-DQ execution evidence is present, invalid samples must be applied in memory and the contract must pass.",
        ),
        _check(
            "resident_frame_mask_admission_contract",
            bool(resident_frame_mask["passed"]),
            {
                "exists": resident_frame_mask["exists"],
                "required": resident_frame_mask["required"],
                "status": resident_frame_mask["status"],
                "frame_count": resident_frame_mask["closure"].get("frame_count"),
                "active_frame_count": resident_frame_mask["closure"].get("active_frame_count"),
                "masked_frame_count": resident_frame_mask["closure"].get("masked_frame_count"),
                "unknown_zero_weight_frame_count": resident_frame_mask["closure"].get(
                    "unknown_zero_weight_frame_count"
                ),
                "input_light_frames": resident_frame_mask["closure"].get("input_light_frames"),
                "integrated_frames": resident_frame_mask["closure"].get("integrated_frames"),
                "zero_weight_frames": resident_frame_mask["closure"].get("zero_weight_frames"),
                "failed_checks": resident_frame_mask["failed_checks"],
                "failed_groups": resident_frame_mask["failed_groups"],
            },
            "Resident frame-level mask admission must explain every zero-weight resident frame and close against frame accounting when available.",
        ),
        _check(
            "resident_registration_quality_contract",
            bool(resident_registration_quality["passed"]),
            {
                "exists": resident_registration_quality["exists"],
                "required": resident_registration_quality["required"],
                "status": resident_registration_quality["status"],
                "registration_mode": resident_registration_quality.get("registration_mode"),
                "requested_action": resident_registration_quality.get("requested_action"),
                "decision_count": resident_registration_quality["closure"].get("decision_count"),
                "active_decision_count": resident_registration_quality["closure"].get("active_decision_count"),
                "rejected_decision_count": resident_registration_quality["closure"].get("rejected_decision_count"),
                "input_light_frames": resident_registration_quality["closure"].get("input_light_frames"),
                "integrated_frames": resident_registration_quality["closure"].get("integrated_frames"),
                "zero_weight_frames": resident_registration_quality["closure"].get("zero_weight_frames"),
                "frame_mask_active_frame_count": resident_registration_quality["closure"].get(
                    "frame_mask_active_frame_count"
                ),
                "frame_mask_masked_frame_count": resident_registration_quality["closure"].get(
                    "frame_mask_masked_frame_count"
                ),
                "failed_checks": resident_registration_quality["failed_checks"],
            },
            "Resident registration quality decisions must explain accepted and excluded frames before integration.",
        ),
        _check(
            "resident_dq_pixel_closure_contract",
            bool(resident_dq_pixel_closure["passed"]),
            {
                "exists": resident_dq_pixel_closure["exists"],
                "required": resident_dq_pixel_closure["required"],
                "status": resident_dq_pixel_closure["status"],
                "active_frame_count": resident_dq_pixel_closure["closure"].get("active_frame_count"),
                "masked_frame_count": resident_dq_pixel_closure["closure"].get("masked_frame_count"),
                "frame_mask_active_frame_count": resident_dq_pixel_closure["closure"].get(
                    "frame_mask_active_frame_count"
                ),
                "frame_mask_masked_frame_count": resident_dq_pixel_closure["closure"].get(
                    "frame_mask_masked_frame_count"
                ),
                "failed_checks": resident_dq_pixel_closure["failed_checks"],
                "failed_groups": resident_dq_pixel_closure["failed_groups"],
                "group_failed_checks": resident_dq_pixel_closure["group_failed_checks"],
            },
            "Resident pixel-level DQ closure must connect frame masks, geometric coverage, rejection maps, and DQ provenance.",
        ),
        _check(
            "integration_sample_accounting_closure",
            bool(integration_rows)
            and all(bool(row["sample_accounting_closure"]["passed"]) for row in integration_rows),
            {
                "output_count": len(integration_rows),
                "present_count": sum(
                    1 for row in integration_rows if row["sample_accounting_closure"]["present"]
                ),
                "failed": [
                    {
                        "item": row["item"],
                        "status": row["sample_accounting_closure"]["status"],
                        "input_valid_samples_before_rejection": row[
                            "sample_accounting_closure"
                        ].get("input_valid_samples_before_rejection"),
                        "valid_samples_after_rejection": row[
                            "sample_accounting_closure"
                        ].get("valid_samples_after_rejection"),
                        "rejected_samples": row["sample_accounting_closure"].get(
                            "rejected_samples"
                        ),
                    }
                    for row in integration_rows
                    if not row["sample_accounting_closure"]["passed"]
                ],
            },
            "Sample-closure evidence is optional for old artifacts, but explicit failed closure blocks the pipeline contract.",
        ),
        _check(
            "frame_accounting_no_integration_conflicts",
            bool(frame_accounting_admission["passed"]),
            {
                "present": frame_accounting_admission["present"],
                "status": frame_accounting_admission["status"],
                "frame_count": frame_accounting_admission["frame_count"],
                "integration_conflict_frames": frame_accounting_admission[
                    "integration_conflict_frames"
                ],
                "conflicts": frame_accounting_admission["integration_conflicts"],
            },
            "When frame_accounting.json is present, positive-weight integration rows must not conflict with upstream quality, registration, warp, or LN rejection state.",
        ),
    ]
    if calibration_artifact_present or resident_calibration_rows:
        checks.extend(
            [
                _check(
                    "calibration_master_surfaces_present",
                    bool(calibration_master_rows),
                    {"actual": len(calibration_master_rows), "required_min": 1},
                ),
                _check(
                    "calibration_master_surface_contract",
                    bool(calibration_master_rows)
                    and all(bool(row["contract_ok"]) for row in calibration_master_rows),
                    {
                        "master_count": len(calibration_master_rows),
                        "failed": [
                            row["name"]
                            for row in calibration_master_rows
                            if not row["contract_ok"]
                        ],
                    },
                    "Master calibration surfaces must expose stats, semantics, and StackEngine result contracts.",
                ),
                _check(
                    "resident_calibration_surface_contract",
                    not resident_calibration_rows
                    or all(bool(row["contract_ok"]) for row in resident_calibration_rows),
                    {
                        "required": bool(resident_calibration_rows),
                        "resident_surface_count": len(resident_calibration_rows),
                        "failed": [
                            row["name"]
                            for row in resident_calibration_rows
                            if not row["contract_ok"]
                        ],
                    },
                    "Resident CUDA calibration surfaces must pass their resident calibration contract.",
                ),
            ]
        )
    if calibration_artifact_present and not resident_native_calibration:
        checks.extend(
            [
                _check(
                    "calibrated_lights_present",
                    bool(local_calibrated_light_rows),
                    {"actual": len(local_calibrated_light_rows), "required_min": 1},
                ),
                _check(
                    "calibrated_light_dq_contract",
                    bool(local_calibrated_light_rows)
                    and all(bool(row["dq_contract_ok"]) for row in local_calibrated_light_rows),
                    {
                        "light_count": len(local_calibrated_light_rows),
                        "failed": [
                            row["frame_id"] or row["index"]
                            for row in local_calibrated_light_rows
                            if not row["dq_contract_ok"]
                        ],
                    },
                    "Calibrated light records must carry a calibrated image path, DQ map path, DQ summary, and tile metadata.",
                ),
            ]
        )
    if calibration_artifact_present and resident_native_calibration:
        checks.extend(
            [
                _check(
                    "resident_calibrated_lights_present",
                    bool(resident_calibrated_light_rows),
                    {"actual": len(resident_calibrated_light_rows), "required_min": 1},
                ),
                _check(
                    "resident_calibrated_light_contract",
                    bool(resident_calibrated_light_rows)
                    and all(bool(row["resident_contract_ok"]) for row in resident_calibrated_light_rows),
                    {
                        "light_count": len(resident_calibrated_light_rows),
                        "failed": [
                            row["frame_id"] or row["index"]
                            for row in resident_calibrated_light_rows
                            if not row["resident_contract_ok"]
                        ],
                    },
                    "Resident calibrated light records must carry frame id, stack index, backend, source stage, and in-VRAM status.",
                ),
            ]
        )
    if pixel_verify:
        dq_rows = [row.get("dq") or {} for row in pixel_verification_rows]
        coverage_rows = [(row.get("count_maps") or {}).get("coverage") or {} for row in pixel_verification_rows]
        rejection_rows = [
            (row.get("count_maps") or {}).get(map_name) or {}
            for row in pixel_verification_rows
            for map_name in ("low_rejection", "high_rejection")
        ]
        rejection_sample_rows = [
            row.get("rejection_sample_accounting") or {}
            for row in pixel_verification_rows
        ]
        checks.extend(
            [
                _check(
                    "integration_dq_map_pixels_match_summary",
                    bool(dq_rows) and all(bool(row.get("ok")) for row in dq_rows),
                    {
                        "verified_records": sum(1 for row in dq_rows if row.get("verified")),
                        "failed": [
                            pixel_verification_rows[index].get("item")
                            for index, row in enumerate(dq_rows)
                            if not row.get("ok")
                        ],
                        "tolerance_pixels": max(0, int(pixel_tolerance)),
                    },
                ),
                _check(
                    "integration_coverage_map_pixels_match_dq",
                    bool(coverage_rows) and all(bool(row.get("ok")) for row in coverage_rows),
                    {
                        "verified_records": sum(1 for row in coverage_rows if row.get("verified")),
                        "failed": [
                            pixel_verification_rows[index].get("item")
                            for index, row in enumerate(coverage_rows)
                            if not row.get("ok")
                        ],
                        "tolerance_pixels": max(0, int(pixel_tolerance)),
                    },
                ),
                _check(
                    "integration_rejection_map_pixels_match_dq",
                    bool(rejection_rows) and all(bool(row.get("ok")) for row in rejection_rows),
                    {
                        "verified_records": sum(1 for row in rejection_rows if row.get("verified")),
                        "failed": [
                            {
                                "item": pixel_verification_rows[index // 2].get("item"),
                                "map": "low_rejection" if index % 2 == 0 else "high_rejection",
                                "status": row.get("status"),
                            }
                            for index, row in enumerate(rejection_rows)
                            if not row.get("ok")
                        ],
                        "tolerance_pixels": max(0, int(pixel_tolerance)),
                    },
                ),
                _check(
                    "integration_rejection_sample_counts_match_maps",
                    bool(rejection_sample_rows)
                    and all(bool(row.get("ok")) for row in rejection_sample_rows),
                    {
                        "verified_records": sum(1 for row in rejection_sample_rows if row.get("verified")),
                        "required_records": sum(1 for row in rejection_sample_rows if row.get("required")),
                        "failed": [
                            {
                                "item": pixel_verification_rows[index].get("item"),
                                "status": row.get("status"),
                                "map_rejected_sample_sum": row.get("map_rejected_sample_sum"),
                                "source_counts": row.get("source_counts"),
                            }
                            for index, row in enumerate(rejection_sample_rows)
                            if not row.get("ok")
                        ],
                        "tolerance_pixels": max(0, int(pixel_tolerance)),
                    },
                    "Rejection maps count samples; DQ rejection flags count touched pixels.",
                ),
            ]
        )
    if warp_path.exists():
        checks.extend(
            [
                _check(
                    "warp_outputs_have_dq_and_coverage",
                    bool(warp_rows) and all(row["contract_ok"] for row in warp_rows),
                    {
                        "warp_output_count": len(warp_rows),
                        "failed": [row["frame_id"] for row in warp_rows if not row["contract_ok"]],
                    },
                ),
                _check(
                    "warp_skipped_frames_are_explained",
                    all(row["contract_ok"] for row in skipped_warp_rows),
                    {
                        "skipped_count": len(skipped_warp_rows),
                        "failed": [row["frame_id"] for row in skipped_warp_rows if not row["contract_ok"]],
                    },
                ),
            ]
        )
    if local_norm_path.exists():
        local_norm_contract_ok = (
            "crop_box" in local_norm
            if not local_norm.get("enabled") and not local_norm_rows
            else bool(local_norm_rows) and all(row["contract_ok"] for row in local_norm_rows)
        )
        checks.append(
            _check(
                "local_normalization_contract",
                local_norm_contract_ok,
                {
                    "enabled": bool(local_norm.get("enabled")),
                    "row_count": len(local_norm_rows),
                    "failed": [row["frame_id"] for row in local_norm_rows if not row["contract_ok"]],
                    "top_level_crop_box_recorded": "crop_box" in local_norm,
                },
                "LN rows must record crop_box and DQ state; enabled LN rows must record coefficient grids.",
            )
        )
    if local_norm_contract_state["attached"]:
        checks.append(
            _check(
                "local_normalization_continuous_contract_audit",
                bool(local_norm_contract_state["passed"]),
                {
                    "status": local_norm_contract_state["status"],
                    "artifact_type": local_norm_contract_state["artifact_type"],
                    "enabled": local_norm_contract_state["enabled"],
                    "output_count": local_norm_contract_state["output_count"],
                    "pipeline_row_count": len(local_norm_rows),
                    "failed_output_count": local_norm_contract_state["failed_output_count"],
                    "failed_checks": local_norm_contract_state["failed_checks"],
                    "failed_outputs": local_norm_contract_state["failed_outputs"],
                    "failed_contract_rows": [
                        row["name"]
                        for row in local_norm_contract_state["check_rows"]
                        if not row["passed"]
                    ],
                },
                "Attached LN continuous coefficient-field audit must pass before run-level acceptance.",
            )
        )

    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "audit_type": "pipeline_invariant_contract",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "checks": checks,
        "artifacts": {
            "calibration": {
                "path": str(calibration_path),
                "exists": calibration_artifact_present,
                "path_exists": calibration_path_exists,
                "source": calibration.get("artifact_source")
                or ("calibration_artifacts_json" if calibration_path_exists else None),
                "generated_for_pipeline_contract": bool(
                    calibration.get("generated_for_pipeline_contract")
                ),
            },
            "resident_calibration_contract": {
                "attached": bool(resident_calibration_rows),
                "artifact_type": resident_calibration_contract.get("artifact_type")
                if isinstance(resident_calibration_contract, dict)
                else None,
                "passed": resident_calibration_contract.get("passed")
                if isinstance(resident_calibration_contract, dict)
                else None,
            },
            "local_norm_contract": {
                "attached": bool(local_norm_contract_state["attached"]),
                "artifact_type": local_norm_contract_state["artifact_type"],
                "passed": local_norm_contract_state["passed"],
                "status": local_norm_contract_state["status"],
                "output_count": local_norm_contract_state["output_count"],
                "failed_output_count": local_norm_contract_state["failed_output_count"],
            },
            "warp": {"path": str(warp_path), "exists": warp_path.exists()},
            "local_norm": {"path": str(local_norm_path), "exists": local_norm_path.exists()},
            "integration": {"path": str(integration_path), "exists": integration_path.exists()},
            "frame_accounting": {
                "path": str(frame_accounting_path),
                "exists": frame_accounting_path.exists(),
            },
            "resident_source_dq_execution": {
                "path": resident_source_dq_execution["path"],
                "exists": resident_source_dq_execution["exists"],
                "status": resident_source_dq_execution["status"],
                "passed": resident_source_dq_execution["passed"],
            },
            "resident_frame_masks": {
                "path": resident_frame_mask["path"],
                "exists": resident_frame_mask["exists"],
                "required": resident_frame_mask["required"],
                "status": resident_frame_mask["status"],
                "passed": resident_frame_mask["passed"],
            },
            "resident_registration_quality": {
                "path": resident_registration_quality["path"],
                "exists": resident_registration_quality["exists"],
                "required": resident_registration_quality["required"],
                "status": resident_registration_quality["status"],
                "passed": resident_registration_quality["passed"],
            },
            "resident_dq_pixel_closure": {
                "path": resident_dq_pixel_closure["path"],
                "exists": resident_dq_pixel_closure["exists"],
                "required": resident_dq_pixel_closure["required"],
                "status": resident_dq_pixel_closure["status"],
                "passed": resident_dq_pixel_closure["passed"],
            },
        },
        "calibration": {
            "artifact_path": str(calibration_path),
            "exists": calibration_artifact_present,
            "path_exists": calibration_path_exists,
            "source": calibration.get("artifact_source")
            or ("calibration_artifacts_json" if calibration_path_exists else None),
            "generated_for_pipeline_contract": bool(
                calibration.get("generated_for_pipeline_contract")
            ),
            "write_back": calibration.get("write_back"),
            "resident_calibration_contract_attached": bool(resident_calibration_rows),
            "resident_native_calibration_artifact": bool(resident_native_calibration),
            "master_count": len(calibration_master_rows),
            "local_master_count": len(local_calibration_master_rows),
            "resident_master_count": len(resident_calibration_rows),
            "calibrated_light_count": len(calibrated_light_rows),
            "local_calibrated_light_count": len(local_calibrated_light_rows),
            "resident_calibrated_light_count": len(resident_calibrated_light_rows),
            "masters": calibration_master_rows,
            "resident_masters": resident_calibration_rows,
            "calibrated_lights": calibrated_light_rows,
            "resident_calibrated_lights": resident_calibrated_light_rows,
        },
        "warp": {"outputs": warp_rows, "skipped_frames": skipped_warp_rows},
        "local_normalization": {
            "enabled": bool(local_norm.get("enabled")) if local_norm else None,
            "reference_frame_id": local_norm.get("reference_frame_id") if local_norm else None,
            "crop_box": local_norm.get("crop_box") if local_norm else None,
            "contract_audit_attached": bool(local_norm_contract_state["attached"]),
            "contract_audit_status": local_norm_contract_state["status"],
            "contract_audit_passed": local_norm_contract_state["passed"],
            "contract_audit_summary": local_norm_contract_state["summary"],
            "outputs": local_norm_rows,
        },
        "integration": {
            "outputs": integration_rows,
            "maps": integration_map_rows,
            "engine_policy": integration_engine_policy,
        },
        "frame_accounting": frame_accounting_admission,
        "resident_source_dq_execution": resident_source_dq_execution,
        "resident_frame_masks": resident_frame_mask,
        "resident_registration_quality": resident_registration_quality,
        "resident_dq_pixel_closure": resident_dq_pixel_closure,
        "stack_engine_runtime_default": stack_engine_runtime_default,
        "pixel_verification": {
            "enabled": bool(pixel_verify),
            "tile_size": max(1, int(pixel_verify_tile_size)),
            "tolerance_pixels": max(0, int(pixel_tolerance)),
            "integration_outputs": pixel_verification_rows,
        },
    }


def write_pipeline_contract_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    lines = [
        "# GLASS Pipeline Invariant Contract Audit",
        "",
        f"- Status: {audit['status']}",
        f"- Run: `{audit['run_dir']}`",
        "",
        "## Checks",
        "",
    ]
    for item in audit.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.extend(["", "## Integration Engine Policy", ""])
    engine_policy = (audit.get("integration") or {}).get("engine_policy") or {}
    lines.append(
        "- "
        f"top-level present `{engine_policy.get('top_level_present')}`, "
        f"default `{(engine_policy.get('top_level') or {}).get('default_engine')}`, "
        f"non-resident outputs `{engine_policy.get('non_resident_count')}`, "
        f"passed `{engine_policy.get('passed')}`"
    )
    for row in engine_policy.get("outputs") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "- "
            f"{row.get('item')}: mode `{row.get('tile_stack_mode')}`, "
            f"backend `{row.get('backend')}`, "
            f"status `{row.get('status')}`, "
            f"passed `{row.get('passed')}`"
        )
    runtime_default = audit.get("stack_engine_runtime_default") or {}
    lines.extend(["", "## StackEngine Runtime Default Path", ""])
    lines.append(
        "- "
        f"status `{runtime_default.get('status')}`, "
        f"masters `{runtime_default.get('master_count')}`, "
        f"master StackEngine `{runtime_default.get('master_stack_engine_count')}`, "
        f"master resident `{runtime_default.get('master_resident_count')}`, "
        f"legacy masters `{runtime_default.get('legacy_master_count')}`, "
        f"integration outputs `{runtime_default.get('integration_output_count')}`, "
        f"integration StackEngine `{runtime_default.get('integration_stack_engine_default_count')}`, "
        f"resident outputs `{runtime_default.get('integration_resident_count')}`, "
        f"explicit CUDA fast paths `{runtime_default.get('explicit_cuda_fast_path_count')}`"
    )
    failed_masters = runtime_default.get("failed_masters") or []
    if failed_masters:
        lines.append(f"- failed masters: `{failed_masters}`")
    failed_outputs = runtime_default.get("failed_outputs") or []
    if failed_outputs:
        lines.append(f"- failed integration outputs: `{failed_outputs}`")
    lines.extend(["", "## Integration Sample Accounting Closure", ""])
    for row in ((audit.get("integration") or {}).get("outputs") or []):
        closure = row.get("sample_accounting_closure") if isinstance(row, dict) else {}
        if not isinstance(closure, dict):
            continue
        lines.append(
            "- "
            f"{row.get('item')}: status `{closure.get('status')}`, "
            f"input-valid `{closure.get('input_valid_samples_before_rejection')}`, "
            f"final-valid `{closure.get('valid_samples_after_rejection')}`, "
            f"rejected `{closure.get('rejected_samples')}`, "
            f"passed `{closure.get('passed')}`"
        )
    frame_accounting = audit.get("frame_accounting") or {}
    lines.extend(["", "## Frame Admission Accounting", ""])
    lines.append(
        "- "
        f"present `{frame_accounting.get('present')}`, "
        f"status `{frame_accounting.get('status')}`, "
        f"frames `{frame_accounting.get('frame_count')}`, "
        f"integrated `{frame_accounting.get('integrated_frames')}`, "
        f"zero-weight `{frame_accounting.get('zero_weight_frames')}`, "
        f"integration conflicts `{frame_accounting.get('integration_conflict_frames')}`"
    )
    for conflict in frame_accounting.get("integration_conflicts") or []:
        if not isinstance(conflict, dict):
            continue
        lines.append(
            "- "
            f"{conflict.get('frame_id')}: status `{conflict.get('final_status')}`, "
            f"weight `{conflict.get('integration_weight')}`, "
            f"conflicts `{conflict.get('integration_conflicts')}`"
        )
    source_dq = audit.get("resident_source_dq_execution") or {}
    summary = source_dq.get("summary") if isinstance(source_dq.get("summary"), dict) else {}
    lines.extend(["", "## Resident Source-DQ Execution", ""])
    lines.append(
        "- "
        f"exists `{source_dq.get('exists')}`, "
        f"status `{source_dq.get('status')}`, "
        f"passed `{source_dq.get('passed')}`, "
        f"groups `{len(source_dq.get('groups') or [])}`, "
        f"invalid `{summary.get('input_invalid_samples_before_rejection')}`, "
        f"applied `{summary.get('applied_invalid_samples')}`, "
        f"cache `{summary.get('materializes_calibrated_dq_cache')}`"
    )
    for group in source_dq.get("groups") or []:
        if not isinstance(group, dict):
            continue
        lines.append(
            "- "
            f"{group.get('filter')}: route `{group.get('execution_route')}`, "
            f"status `{group.get('status')}`, "
            f"invalid `{group.get('input_invalid_samples_before_rejection')}`, "
            f"applied `{group.get('applied_invalid_samples')}`, "
            f"cache `{group.get('materializes_calibrated_dq_cache')}`"
        )
    frame_masks = audit.get("resident_frame_masks") or {}
    mask_closure = frame_masks.get("closure") if isinstance(frame_masks.get("closure"), dict) else {}
    lines.extend(["", "## Resident Frame Masks", ""])
    lines.append(
        "- "
        f"exists `{frame_masks.get('exists')}`, "
        f"required `{frame_masks.get('required')}`, "
        f"status `{frame_masks.get('status')}`, "
        f"passed `{frame_masks.get('passed')}`, "
        f"frames `{mask_closure.get('frame_count')}`, "
        f"active `{mask_closure.get('active_frame_count')}`, "
        f"masked `{mask_closure.get('masked_frame_count')}`, "
        f"unknown `{mask_closure.get('unknown_zero_weight_frame_count')}`"
    )
    for group in frame_masks.get("groups") or []:
        if not isinstance(group, dict):
            continue
        group_summary = group.get("summary") if isinstance(group.get("summary"), dict) else {}
        lines.append(
            "- "
            f"{group.get('filter')}: active `{group_summary.get('active_frame_count')}`, "
            f"masked `{group_summary.get('masked_frame_count')}`, "
            f"unknown `{group_summary.get('unknown_zero_weight_frame_count')}`, "
            f"passed `{group_summary.get('passed')}`"
        )
    registration_quality = audit.get("resident_registration_quality") or {}
    registration_closure = (
        registration_quality.get("closure") if isinstance(registration_quality.get("closure"), dict) else {}
    )
    reg_summary = (
        registration_quality.get("summary") if isinstance(registration_quality.get("summary"), dict) else {}
    )
    lines.extend(["", "## Resident Registration Quality", ""])
    lines.append(
        "- "
        f"exists `{registration_quality.get('exists')}`, "
        f"required `{registration_quality.get('required')}`, "
        f"status `{registration_quality.get('status')}`, "
        f"passed `{registration_quality.get('passed')}`, "
        f"mode `{registration_quality.get('registration_mode')}`, "
        f"decisions `{registration_closure.get('decision_count')}`, "
        f"active `{registration_closure.get('active_decision_count')}`, "
        f"rejected `{registration_closure.get('rejected_decision_count')}`"
    )
    lines.append(
        "- "
        f"decision statuses `{reg_summary.get('decision_status_counts')}`, "
        f"final statuses `{reg_summary.get('final_status_counts')}`"
    )
    pixel_closure = audit.get("resident_dq_pixel_closure") or {}
    pixel_closure_summary = (
        pixel_closure.get("closure") if isinstance(pixel_closure.get("closure"), dict) else {}
    )
    lines.extend(["", "## Resident DQ Pixel Closure", ""])
    lines.append(
        "- "
        f"exists `{pixel_closure.get('exists')}`, "
        f"required `{pixel_closure.get('required')}`, "
        f"status `{pixel_closure.get('status')}`, "
        f"passed `{pixel_closure.get('passed')}`, "
        f"active `{pixel_closure_summary.get('active_frame_count')}`, "
        f"masked `{pixel_closure_summary.get('masked_frame_count')}`"
    )
    for group in pixel_closure.get("groups") or []:
        if not isinstance(group, dict):
            continue
        lines.append(
            "- "
            f"{group.get('filter')}: status `{group.get('status')}`, "
            f"active `{group.get('frame_mask_active_frame_count')}`, "
            f"geometric `{group.get('geometric_warp_coverage_frame_count')}`, "
            f"checks `{group.get('check_count')}`"
        )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pipeline_contract_audit(
    path: str | Path,
    audit: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, audit)
    if markdown is not None:
        write_pipeline_contract_markdown(markdown, audit)
