from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag
from glass.engine.dq import dq_header
from glass.engine.resident_stack_surface import build_resident_master_stack_surface_contract
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_MASTER_COMPONENTS = {
    "bias": "master_bias",
    "dark": "master_dark",
    "flat": "master_flat",
}


def _safe_name(value: Any) -> str:
    text = str(value or "unknown")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)


def _positive_int(value: Any) -> int | None:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric > 0 else None


def _full_frame_tile_size(shape: dict[str, Any]) -> int:
    height = _positive_int(shape.get("height")) or 1
    width = _positive_int(shape.get("width")) or 1
    return max(height, width)


def _cache_component_path(calibration_set: dict[str, Any], component: str) -> str | None:
    cache_dir = calibration_set.get("cache_dir")
    cache_key = calibration_set.get("cache_key") or calibration_set.get("cache_base_key")
    if not cache_dir or not cache_key:
        return None
    return str(Path(str(cache_dir)) / f"{cache_key}_{component}.npy")


def _resident_master_dq_path(run: Path, name: str) -> Path:
    return run / "calib_cache" / "dq" / f"dq_master_{_safe_name(name)}.fits"


def _contract_check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _resident_source_dq_contracts(run: Path) -> dict[str, dict[str, Any]]:
    path = run / "resident_source_dq_execution.json"
    payload = _load_optional_json(path)
    if not payload:
        return {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    summary_passed = bool(summary.get("passed") is True)
    contracts: dict[str, dict[str, Any]] = {}
    for group in payload.get("groups") or []:
        if not isinstance(group, dict):
            continue
        filter_name = str(group.get("filter") or "")
        checks = [item for item in group.get("checks") or [] if isinstance(item, dict)]
        failed_checks = [str(item.get("name")) for item in checks if item.get("passed") is not True]
        passed = summary_passed and group.get("passed") is True and not failed_checks
        execution_route = group.get("execution_route")
        execution_routes = [str(execution_route)] if execution_route else []
        contract = {
            "source": "resident_source_dq_execution",
            "artifact_path": str(path),
            "available": True,
            "passed": bool(passed),
            "status": group.get("status") or summary.get("status"),
            "summary_status": summary.get("status"),
            "filter": filter_name or None,
            "matching_group_count": 1,
            "execution_route": execution_route,
            "execution_routes": execution_routes,
            "materializes_calibrated_dq_cache": bool(group.get("materializes_calibrated_dq_cache")),
            "input_invalid_samples_before_rejection": group.get("input_invalid_samples_before_rejection"),
            "applied_invalid_samples": group.get("applied_invalid_samples"),
            "input_flagged_samples": group.get("input_flagged_samples"),
            "input_nonfinite_samples": group.get("input_nonfinite_samples"),
            "source_counts": group.get("source_counts") if isinstance(group.get("source_counts"), dict) else {},
            "status_counts": group.get("status_counts") if isinstance(group.get("status_counts"), dict) else {},
            "source_dq_flag_counts": (
                group.get("source_dq_flag_counts")
                if isinstance(group.get("source_dq_flag_counts"), dict)
                else {}
            ),
            "check_count": len(checks),
            "failed_checks": failed_checks,
            "reason": None if passed else "resident_source_dq_execution_group_failed",
            "contract_model": "filter_group_applies_to_resident_calibrated_lights",
        }
        contracts[filter_name] = contract
    return contracts


def _resident_frame_mask_contracts(run: Path) -> dict[str, dict[str, Any]]:
    path = run / "resident_frame_masks.json"
    payload = _load_optional_json(path)
    if not payload:
        return {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    top_passed = bool(summary.get("passed") is True)
    contracts: dict[str, dict[str, Any]] = {}
    for group in payload.get("groups") or []:
        if not isinstance(group, dict):
            continue
        group_summary = group.get("summary") if isinstance(group.get("summary"), dict) else {}
        group_passed = bool(group_summary.get("passed") is True)
        for row in group.get("rows") or []:
            if not isinstance(row, dict):
                continue
            frame_id = row.get("frame_id")
            if frame_id is None:
                continue
            passed = top_passed and group_passed and bool(row.get("auditable"))
            contracts[str(frame_id)] = {
                "source": "resident_frame_masks",
                "artifact_path": str(path),
                "available": True,
                "passed": bool(passed),
                "filter": row.get("filter") or group.get("filter"),
                "frame_id": str(frame_id),
                "mask_status": row.get("mask_status"),
                "integration_weight": row.get("integration_weight"),
                "auditable": bool(row.get("auditable")),
                "mask_categories": list(row.get("mask_categories") or []),
                "mask_reasons": list(row.get("mask_reasons") or []),
                "observed_zero_weight_statuses": list(row.get("observed_zero_weight_statuses") or []),
                "registration_status": row.get("registration_status"),
                "registration_quality_status": row.get("registration_quality_status"),
                "registration_quality_final_status": row.get("registration_quality_final_status"),
                "weighting_status": row.get("weighting_status"),
                "local_norm_status": row.get("local_norm_status"),
                "contract_model": "frame_level_resident_admission",
            }
    return contracts


def _unavailable_contract(source: str, reason: str) -> dict[str, Any]:
    return {
        "source": source,
        "available": False,
        "passed": True,
        "reason": reason,
    }


def _resident_master_contract(
    *,
    master_type: str,
    path: str | None,
    stats: dict[str, Any],
    frame_count: Any,
    set_key: str,
) -> dict[str, Any]:
    path_exists = bool(path and Path(path).exists())
    stats_present = isinstance(stats, dict) and all(
        key in stats for key in ("min", "max", "mean", "median", "std")
    )
    count = _positive_int(frame_count)
    checks = [
        _contract_check("resident_master_cache_path_exists", path_exists, {"path": path}),
        _contract_check(
            "resident_master_stats_present",
            stats_present,
            {"required": ["min", "max", "mean", "median", "std"], "present": sorted(stats)},
        ),
        _contract_check(
            "resident_master_source_frame_count_recorded",
            count is not None,
            {"frame_count": frame_count},
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "resident_cuda_calibration_master_contract",
        "contract_type": "resident_calibration_master_surface_contract",
        "master_type": master_type,
        "set_key": set_key,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "checks": checks,
    }


def _dq_summary_for_resident_master(
    *,
    name: str,
    master_type: str,
    contract: dict[str, Any],
    stats: dict[str, Any],
    frame_count: Any,
) -> dict[str, Any]:
    return {
        "source_schema": "resident_calibration_artifact",
        "engine": "cuda_resident_stack",
        "stage": "master_calibration",
        "item": name,
        "master_type": master_type,
        "input_samples": frame_count,
        "result_contract_passed": bool(contract.get("passed")),
        "stats": {key: stats.get(key) for key in ("min", "max", "mean", "median", "std")},
    }


def _materialize_resident_master_dq_sidecar(
    *,
    run: Path,
    name: str,
    master_path: str | None,
    shape: dict[str, Any],
) -> dict[str, Any]:
    dq_path = _resident_master_dq_path(run, name)
    expected_height = _positive_int(shape.get("height"))
    expected_width = _positive_int(shape.get("width"))
    checks: list[dict[str, Any]] = []
    if not master_path:
        checks.append(_contract_check("resident_master_path_present", False, {"path": master_path}))
        return {
            "path": str(dq_path),
            "summary": {},
            "contract": {
                "schema_version": 1,
                "contract_type": "resident_master_dq_sidecar_contract",
                "passed": False,
                "status": "failed",
                "checks": checks,
            },
        }

    source = Path(master_path)
    source_exists = source.exists()
    checks.append(_contract_check("resident_master_path_exists", source_exists, {"path": str(source)}))
    if not source_exists:
        return {
            "path": str(dq_path),
            "summary": {},
            "contract": {
                "schema_version": 1,
                "contract_type": "resident_master_dq_sidecar_contract",
                "passed": False,
                "status": "failed",
                "checks": checks,
            },
        }

    try:
        data = np.load(source, mmap_mode="r")
    except Exception as exc:
        checks.append(
            _contract_check(
                "resident_master_array_loadable",
                False,
                {"path": str(source), "error": f"{type(exc).__name__}: {exc}"},
            )
        )
        return {
            "path": str(dq_path),
            "summary": {},
            "contract": {
                "schema_version": 1,
                "contract_type": "resident_master_dq_sidecar_contract",
                "passed": False,
                "status": "failed",
                "checks": checks,
            },
        }
    checks.append(_contract_check("resident_master_array_loadable", True, {"path": str(source)}))
    checks.append(
        _contract_check(
            "resident_master_is_2d",
            getattr(data, "ndim", 0) == 2,
            {"shape": [int(value) for value in getattr(data, "shape", ())]},
        )
    )
    if getattr(data, "ndim", 0) != 2:
        return {
            "path": str(dq_path),
            "summary": {},
            "contract": {
                "schema_version": 1,
                "contract_type": "resident_master_dq_sidecar_contract",
                "passed": False,
                "status": "failed",
                "checks": checks,
            },
        }

    height, width = (int(data.shape[0]), int(data.shape[1]))
    expected_matches = (
        expected_height is None
        or expected_width is None
        or (height == expected_height and width == expected_width)
    )
    checks.append(
        _contract_check(
            "resident_master_shape_matches_record",
            expected_matches,
            {
                "actual": {"height": height, "width": width},
                "expected": {"height": expected_height, "width": expected_width},
            },
        )
    )

    dq = np.zeros((height, width), dtype=np.int16)
    no_data_count = 0
    rows_per_chunk = max(1, 64 * 1024 * 1024 // max(1, width * np.dtype(np.float32).itemsize))
    for y0 in range(0, height, rows_per_chunk):
        y1 = min(height, y0 + rows_per_chunk)
        invalid = ~np.isfinite(np.asarray(data[y0:y1], dtype=np.float32))
        if np.any(invalid):
            dq[y0:y1][invalid] = int(DQFlag.NO_DATA)
            no_data_count += int(np.count_nonzero(invalid))
    total_pixels = int(height * width)
    summary = {"valid": total_pixels - no_data_count}
    if no_data_count:
        summary["no_data"] = no_data_count
    dq_path.parent.mkdir(parents=True, exist_ok=True)
    write_fits_data(
        dq_path,
        dq,
        header=dq_header("master_calibration", name),
        dtype=np.int16,
    )
    path_exists = dq_path.exists()
    checks.extend(
        [
            _contract_check("resident_master_dq_path_exists", path_exists, {"path": str(dq_path)}),
            _contract_check(
                "resident_master_dq_summary_closes_pixels",
                int(summary.get("valid", 0)) + int(summary.get("no_data", 0)) == total_pixels,
                {"summary": dict(summary), "total_pixels": total_pixels},
            ),
        ]
    )
    passed = all(item["passed"] for item in checks)
    return {
        "path": str(dq_path),
        "summary": summary,
        "contract": {
            "schema_version": 1,
            "contract_type": "resident_master_dq_sidecar_contract",
            "passed": passed,
            "status": "passed" if passed else "failed",
            "checks": checks,
            "semantics": (
                "Resident master DQ sidecars mark output master pixels that are "
                "non-finite as NO_DATA. Master rejection sample accounting remains "
                "in resident DQ provenance; this sidecar does not claim to encode "
                "per-pixel low/high rejection touches for master construction."
            ),
        },
    }


def _resident_master_record(
    *,
    run: Path,
    output_filter: str,
    set_key: str,
    master_type: str,
    calibration_set: dict[str, Any],
    policy: dict[str, Any],
    materialize_master_dq: bool,
) -> dict[str, Any] | None:
    stats = calibration_set.get(master_type)
    if not isinstance(stats, dict):
        return None
    component = _MASTER_COMPONENTS[master_type]
    path = _cache_component_path(calibration_set, component)
    source_count = calibration_set.get(f"{master_type}_count")
    source_frame_ids = [
        str(frame_id) for frame_id in calibration_set.get(f"{master_type}_frame_ids") or []
    ]
    shape = calibration_set.get("shape") if isinstance(calibration_set.get("shape"), dict) else {}
    safe_filter = _safe_name(output_filter)
    safe_set = _safe_name(set_key)
    name = f"resident_{master_type}_{safe_filter}_{safe_set}"
    contract = _resident_master_contract(
        master_type=master_type,
        path=path,
        stats=stats,
        frame_count=source_count,
        set_key=set_key,
    )
    stack_surface_contract = build_resident_master_stack_surface_contract(
        name=name,
        master_type=master_type,
        path=path,
        stats=stats,
        frame_ids=source_frame_ids,
        frame_count=source_count,
        shape=shape,
        policy=policy,
    )
    dq_materialization: dict[str, Any] | None = None
    if materialize_master_dq:
        dq_materialization = _materialize_resident_master_dq_sidecar(
            run=run,
            name=name,
            master_path=path,
            shape=shape,
        )
    record: dict[str, Any] = {
        "type": master_type,
        "path": path,
        "stats": stats,
        "filter": output_filter,
        "source_stage": "resident_calibrated_stack",
        "backend": "cuda_resident_stack",
        "tile_stack_mode": "cuda_resident_stack",
        "stack_engine_enabled": True,
        "stack_engine_fallback_reason": None,
        "streaming": False,
        "resident": True,
        "resident_surface_scope": "full_frame_vram",
        "master_rejection": calibration_set.get("master_rejection_applied")
        or policy.get("master_rejection")
        or "none",
        "master_rejection_requested": calibration_set.get("master_rejection_requested")
        or policy.get("master_rejection")
        or "none",
        "master_rejection_dispatch_reason": calibration_set.get("master_rejection_dispatch_reason"),
        "tile_size": _full_frame_tile_size(shape),
        "shape": shape,
        "source_frame_count": source_count,
        "calibration_set_key": set_key,
        "calibration_group_policy": calibration_set.get("calibration_group_policy"),
        "bias_group": calibration_set.get("bias_group"),
        "dark_group": calibration_set.get("dark_group"),
        "flat_group": calibration_set.get("flat_group"),
        "resident_calibration_contract": contract,
        "stack_engine_surface_contract": stack_surface_contract,
        "stack_engine_dq_provenance": {
            "source_schema": "resident_calibration_provenance",
            "engine": "cuda_resident_stack",
            "stage": "master_calibration",
            "item": name,
            "input_samples": source_count,
            "result_contract": contract,
        },
        "dq_provenance_summary": _dq_summary_for_resident_master(
            name=name,
            master_type=master_type,
            contract=contract,
            stats=stats,
            frame_count=source_count,
        ),
    }
    if dq_materialization is not None:
        dq_summary = dict(dq_materialization.get("summary") or {})
        record.update(
            {
                "dq_mask_path": dq_materialization["path"],
                "dq_summary": dq_summary,
                "resident_master_dq_contract": dq_materialization["contract"],
            }
        )
        record["stack_engine_dq_provenance"]["output_dq_summary"] = dq_summary
        record["dq_provenance_summary"]["output_dq_summary"] = dq_summary
        record["dq_provenance_summary"]["valid_pixels"] = dq_summary.get("valid")
        record["dq_provenance_summary"]["no_data_pixels"] = dq_summary.get("no_data", 0)
    if master_type == "dark":
        includes_bias = calibration_set.get(
            "master_dark_includes_bias",
            policy.get("master_dark_includes_bias"),
        )
        record.update(
            {
                "exposure_s": calibration_set.get("dark_exposure_s"),
                "master_dark_includes_bias": bool(includes_bias),
                "bias_subtracted_from_source": not bool(includes_bias),
            }
        )
    elif master_type == "flat":
        flat_count = _positive_int(calibration_set.get("flat_count")) or 1
        record.update(
            {
                "bias_subtracted_from_source": bool(calibration_set.get("flat_bias_group")),
                "normalization": policy.get("flat_normalization") or "median",
                "normalization_stage": "per_flat",
                "flat_floor": policy.get("flat_floor"),
                "per_flat_normalization": [
                    {
                        "source": "resident_cuda_master_flat",
                        "normalization_method": policy.get("flat_normalization") or "median",
                        "normalization_scalar": 1.0,
                        "frame_count": flat_count,
                    }
                ],
                "normalization_scalar": 1.0,
                "normalization_method": policy.get("flat_normalization") or "median",
            }
        )
    return {name: record}


def build_resident_calibration_artifacts(
    run_dir: str | Path,
    resident_payload: dict[str, Any] | None = None,
    *,
    materialize_master_dq: bool = False,
) -> dict[str, Any]:
    """Build first-class calibration_artifacts.json content for resident CUDA runs."""

    run = Path(run_dir)
    if resident_payload is None:
        loaded = read_json(run / "resident_artifacts.json")
        resident_payload = loaded if isinstance(loaded, dict) else {}
    policy = resident_payload.get("policy") if isinstance(resident_payload.get("policy"), dict) else {}
    artifacts = (
        resident_payload.get("artifacts")
        if isinstance(resident_payload.get("artifacts"), list)
        else []
    )
    source_dq_contracts = _resident_source_dq_contracts(run)
    frame_mask_contracts = _resident_frame_mask_contracts(run)
    masters: dict[str, dict[str, Any]] = {}
    calibrated_lights: list[dict[str, Any]] = []
    warnings: list[str] = []
    for output_index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        output_filter = str(artifact.get("filter") or "unknown")
        frame_ids = [str(frame_id) for frame_id in artifact.get("frame_ids") or []]
        master_stats = (
            artifact.get("master_stats") if isinstance(artifact.get("master_stats"), dict) else {}
        )
        sets = master_stats.get("sets") if isinstance(master_stats.get("sets"), dict) else {}
        for set_key, calibration_set in sets.items():
            if not isinstance(calibration_set, dict):
                continue
            set_filter = str(calibration_set.get("filter") or output_filter)
            for master_type in ("bias", "dark", "flat"):
                row = _resident_master_record(
                    run=run,
                    output_filter=set_filter,
                    set_key=str(set_key),
                    master_type=master_type,
                    calibration_set=calibration_set,
                    policy=policy,
                    materialize_master_dq=materialize_master_dq,
                )
                if row is None:
                    warnings.append(f"resident calibration set {set_key} has no {master_type} stats")
                    continue
                masters.update(row)
        for stack_index, frame_id in enumerate(frame_ids):
            frame_id = str(frame_id)
            source_dq_contract = dict(
                source_dq_contracts.get(output_filter)
                or source_dq_contracts.get("")
                or _unavailable_contract(
                    "resident_source_dq_execution",
                    "resident_source_dq_execution_not_present",
                )
            )
            frame_mask_contract = dict(
                frame_mask_contracts.get(frame_id)
                or _unavailable_contract("resident_frame_masks", "resident_frame_masks_not_present")
            )
            dq_mask_contract_sources = [
                source_dq_contract["source"]
                for source_dq_contract in [source_dq_contract]
                if source_dq_contract.get("available")
            ]
            frame_mask_sources = [
                frame_mask_contract["source"]
                for frame_mask_contract in [frame_mask_contract]
                if frame_mask_contract.get("available")
            ]
            resident_dq_mask_contract = {
                "schema_version": 1,
                "contract_type": "resident_calibrated_light_dq_mask_contract",
                "passed": bool(source_dq_contract.get("passed") and frame_mask_contract.get("passed")),
                "status": "passed"
                if source_dq_contract.get("passed") and frame_mask_contract.get("passed")
                else "failed",
                "frame_id": frame_id,
                "source_dq_contract_available": bool(source_dq_contract.get("available")),
                "frame_mask_contract_available": bool(frame_mask_contract.get("available")),
                "contract_sources": dq_mask_contract_sources,
                "frame_mask_sources": frame_mask_sources,
                "materializes_calibrated_dq_cache": False,
                "calibrated_dq_cache_required": False,
                "semantics": (
                    "Resident calibrated lights stay in VRAM. Source-DQ invalid samples "
                    "are applied in memory when resident_source_dq_execution is present, "
                    "while frame-level admission and zero-weight decisions are carried by "
                    "resident_frame_masks. Pixel-level warp and rejection masks are emitted "
                    "through integration DQ/count maps."
                ),
            }
            calibrated_lights.append(
                {
                    "frame_id": frame_id,
                    "filter": output_filter,
                    "status": "resident_in_vram",
                    "source_stage": "resident_calibrated_stack",
                    "backend": "cuda_resident_stack",
                    "resident_output_index": output_index,
                    "resident_stack_index": stack_index,
                    "resident_master_path": artifact.get("master_path"),
                    "calibration_group_policy": master_stats.get("calibration_group_policy"),
                    "path": None,
                    "dq_mask_path": None,
                    "source_dq_contract": source_dq_contract,
                    "frame_mask_contract": frame_mask_contract,
                    "resident_dq_mask_contract": resident_dq_mask_contract,
                    "dq_contract_source": "resident_source_dq_execution"
                    if source_dq_contract.get("available")
                    else None,
                    "dq_contract_ok": bool(resident_dq_mask_contract["passed"]),
                    "warnings": [],
                }
            )
    return {
        "schema_version": 1,
        "artifact_type": "resident_cuda_calibration_artifacts",
        "source_stage": "resident_calibrated_stack",
        "created_at": now_iso(),
        "masters": masters,
        "calibrated_lights": calibrated_lights,
        "resident_artifacts_path": str(run / "resident_artifacts.json"),
        "policy": policy,
        "requested_backend": "cuda",
        "backend": "cuda_resident_stack",
        "memory_mode": "resident",
        "warnings": warnings,
    }


def write_resident_calibration_artifacts(
    run_dir: str | Path,
    resident_payload: dict[str, Any] | None = None,
    *,
    compact_json: bool = False,
) -> dict[str, Any]:
    payload = build_resident_calibration_artifacts(
        run_dir,
        resident_payload,
        materialize_master_dq=True,
    )
    write_json(Path(run_dir) / "calibration_artifacts.json", payload, compact=compact_json)
    return payload
