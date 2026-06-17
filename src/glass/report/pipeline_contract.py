from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _positive_int(value: Any) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


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
    actual_int = None if actual is None else int(actual)
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
        dq_summary = payload.get("dq_summary") if isinstance(payload.get("dq_summary"), dict) else {}
        path_exists = _path_exists(payload.get("path"), run_root)
        dq_path_exists = _path_exists(payload.get("dq_mask_path"), run_root)
        rows.append(
            {
                "index": index,
                "frame_id": payload.get("frame_id"),
                "backend": payload.get("backend"),
                "path": payload.get("path"),
                "path_exists": path_exists,
                "dq_mask_path": payload.get("dq_mask_path"),
                "dq_mask_path_exists": dq_path_exists,
                "dq_summary_present": isinstance(payload.get("dq_summary"), dict),
                "dq_summary_has_valid": "valid" in dq_summary,
                "tile_count": payload.get("tile_count"),
                "tile_size": payload.get("tile_size"),
                "contract_ok": (
                    path_exists
                    and dq_path_exists
                    and isinstance(payload.get("dq_summary"), dict)
                    and "valid" in dq_summary
                    and _positive_int(payload.get("tile_count"))
                    and _positive_int(payload.get("tile_size"))
                ),
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
    return {
        "status": "verified",
        "verified": True,
        "ok": bool(match.get("passed")),
        "path": path_value,
        "required": required,
        "result": pixel_summary,
        "summary_match": {expected_dq_flag: match},
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
        rows.append(
            {
                "item": item,
                "dq": _verify_integration_dq_pixels(
                    output,
                    run_root=run_root,
                    tile_size=tile_size,
                    tolerance_pixels=tolerance_pixels,
                ),
                "count_maps": {
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
                },
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


def _integration_rows(integration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, output in enumerate(integration.get("outputs") or []):
        if not isinstance(output, dict):
            continue
        dq_summary = output.get("dq_summary")
        summary = output.get("dq_provenance_summary")
        item = str(output.get("filter") or index)
        dq_required = not _map_skipped(output, "dq")
        result_contract = _stack_result_contract_state(output)
        resident_contract = _resident_result_contract_state(
            output,
            integration=integration,
            run_root=run_root,
            index=index,
        )
        rows.append(
            {
                "item": item,
                "backend": output.get("backend"),
                "rejection": _integration_rejection_mode(integration, output),
                "frame_count": output.get("frame_count"),
                "tile_stack_mode": output.get("tile_stack_mode"),
                "stack_engine_enabled": bool(output.get("stack_engine_enabled")),
                "dq_map_path": output.get("dq_map_path"),
                "dq_map_exists": _path_exists(output.get("dq_map_path"), run_root),
                "dq_summary_present": isinstance(dq_summary, dict),
                "dq_summary_has_valid": isinstance(dq_summary, dict) and "valid" in dq_summary,
                "dq_provenance_summary_present": isinstance(summary, dict),
                "dq_provenance_engine": summary.get("engine") if isinstance(summary, dict) else None,
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
    return rows


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


def build_pipeline_contract_audit(
    run_dir: str | Path,
    *,
    pixel_verify: bool = False,
    pixel_verify_tile_size: int = 2048,
    pixel_tolerance: int = 0,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    calibration_path = run_root / "calibration_artifacts.json"
    warp_path = run_root / "warp_results.json"
    local_norm_path = run_root / "local_norm_results.json"
    integration_path = run_root / "integration_results.json"
    calibration = _load_json_object(calibration_path)
    warp = _load_json_object(warp_path)
    local_norm = _load_json_object(local_norm_path)
    integration = _load_json_object(integration_path)

    calibration_master_rows = _calibration_master_rows(calibration, run_root)
    calibrated_light_rows = _calibrated_light_rows(calibration, run_root)
    warp_rows = _warp_rows(warp, run_root)
    skipped_warp_rows = _skipped_warp_rows(warp)
    local_norm_rows = _local_norm_rows(local_norm, run_root)
    integration_rows = _integration_rows(integration, run_root)
    integration_map_rows = _integration_map_rows(integration, run_root)
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
    ]
    if calibration_path.exists():
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
                    "calibrated_lights_present",
                    bool(calibrated_light_rows),
                    {"actual": len(calibrated_light_rows), "required_min": 1},
                ),
                _check(
                    "calibrated_light_dq_contract",
                    bool(calibrated_light_rows)
                    and all(bool(row["contract_ok"]) for row in calibrated_light_rows),
                    {
                        "light_count": len(calibrated_light_rows),
                        "failed": [
                            row["frame_id"] or row["index"]
                            for row in calibrated_light_rows
                            if not row["contract_ok"]
                        ],
                    },
                    "Calibrated light records must carry a calibrated image path, DQ map path, DQ summary, and tile metadata.",
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
            "calibration": {"path": str(calibration_path), "exists": calibration_path.exists()},
            "warp": {"path": str(warp_path), "exists": warp_path.exists()},
            "local_norm": {"path": str(local_norm_path), "exists": local_norm_path.exists()},
            "integration": {"path": str(integration_path), "exists": integration_path.exists()},
        },
        "calibration": {
            "artifact_path": str(calibration_path),
            "exists": calibration_path.exists(),
            "master_count": len(calibration_master_rows),
            "calibrated_light_count": len(calibrated_light_rows),
            "masters": calibration_master_rows,
            "calibrated_lights": calibrated_light_rows,
        },
        "warp": {"outputs": warp_rows, "skipped_frames": skipped_warp_rows},
        "local_normalization": {
            "enabled": bool(local_norm.get("enabled")) if local_norm else None,
            "reference_frame_id": local_norm.get("reference_frame_id") if local_norm else None,
            "crop_box": local_norm.get("crop_box") if local_norm else None,
            "outputs": local_norm_rows,
        },
        "integration": {"outputs": integration_rows, "maps": integration_map_rows},
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
