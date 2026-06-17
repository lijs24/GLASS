from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _contract_check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


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


def _resident_master_record(
    *,
    output_filter: str,
    set_key: str,
    master_type: str,
    calibration_set: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any] | None:
    stats = calibration_set.get(master_type)
    if not isinstance(stats, dict):
        return None
    component = _MASTER_COMPONENTS[master_type]
    path = _cache_component_path(calibration_set, component)
    source_count = calibration_set.get(f"{master_type}_count")
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
        "master_rejection": policy.get("master_rejection") or "none",
        "tile_size": _full_frame_tile_size(shape),
        "shape": shape,
        "source_frame_count": source_count,
        "calibration_set_key": set_key,
        "calibration_group_policy": calibration_set.get("calibration_group_policy"),
        "bias_group": calibration_set.get("bias_group"),
        "dark_group": calibration_set.get("dark_group"),
        "flat_group": calibration_set.get("flat_group"),
        "resident_calibration_contract": contract,
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
                    output_filter=set_filter,
                    set_key=str(set_key),
                    master_type=master_type,
                    calibration_set=calibration_set,
                    policy=policy,
                )
                if row is None:
                    warnings.append(f"resident calibration set {set_key} has no {master_type} stats")
                    continue
                masters.update(row)
        for stack_index, frame_id in enumerate(frame_ids):
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
) -> dict[str, Any]:
    payload = build_resident_calibration_artifacts(run_dir, resident_payload)
    write_json(Path(run_dir) / "calibration_artifacts.json", payload)
    return payload
