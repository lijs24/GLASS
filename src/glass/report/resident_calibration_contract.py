from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


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
    if path.exists():
        return path
    return run_root / path


def _path_exists(path_value: Any, run_root: Path) -> bool:
    path = _resolve_path(path_value, run_root)
    return bool(path and path.exists())


def _positive_int(value: Any) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _number_ge_zero(value: Any) -> bool:
    try:
        return float(value) >= 0.0
    except (TypeError, ValueError):
        return False


def _stats_present(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {"min", "max", "mean", "median", "std"}
    return required.issubset({str(key) for key in value})


def _cache_paths(set_payload: dict[str, Any], run_root: Path) -> dict[str, str | None]:
    cache_dir = _resolve_path(set_payload.get("cache_dir"), run_root)
    cache_key = set_payload.get("cache_key")
    if cache_dir is None or not cache_key:
        return {"bias": None, "dark": None, "flat": None, "stats": None}
    key = str(cache_key)
    return {
        "bias": str(cache_dir / f"{key}_master_bias.npy"),
        "dark": str(cache_dir / f"{key}_master_dark.npy"),
        "flat": str(cache_dir / f"{key}_master_flat.npy"),
        "stats": str(cache_dir / f"{key}_master_stats.json"),
    }


def _cache_path_rows(set_payload: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    paths = _cache_paths(set_payload, run_root)
    rows: list[dict[str, Any]] = []
    for master_type, path_value in paths.items():
        required = master_type == "stats" or _positive_int(set_payload.get(f"{master_type}_count"))
        rows.append(
            {
                "master_type": master_type,
                "path": path_value,
                "required": required,
                "exists": False if path_value is None else Path(path_value).exists(),
            }
        )
    return rows


def _master_set_contract(key: str, payload: dict[str, Any], run_root: Path) -> dict[str, Any]:
    cache_rows = _cache_path_rows(payload, run_root)
    checks = [
        _check(
            "source_counts_present",
            _positive_int(payload.get("bias_count"))
            and _positive_int(payload.get("dark_count"))
            and _positive_int(payload.get("flat_count")),
            {
                "bias_count": payload.get("bias_count"),
                "dark_count": payload.get("dark_count"),
                "flat_count": payload.get("flat_count"),
            },
        ),
        _check(
            "master_statistics_present",
            _stats_present(payload.get("bias"))
            and _stats_present(payload.get("dark"))
            and _stats_present(payload.get("flat")),
            {
                "bias_stats": _stats_present(payload.get("bias")),
                "dark_stats": _stats_present(payload.get("dark")),
                "flat_stats": _stats_present(payload.get("flat")),
            },
        ),
        _check(
            "cache_paths_present",
            all(row["path"] for row in cache_rows if row["required"]),
            {"missing": [row["master_type"] for row in cache_rows if row["required"] and not row["path"]]},
        ),
        _check(
            "cache_files_exist",
            all(row["exists"] for row in cache_rows if row["required"]),
            {
                "missing": [
                    {"master_type": row["master_type"], "path": row["path"]}
                    for row in cache_rows
                    if row["required"] and not row["exists"]
                ]
            },
        ),
        _check(
            "shape_present",
            isinstance(payload.get("shape"), dict)
            and _positive_int((payload.get("shape") or {}).get("height"))
            and _positive_int((payload.get("shape") or {}).get("width")),
            {"shape": payload.get("shape")},
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "key": key,
        "filter": payload.get("filter"),
        "bias_group": payload.get("bias_group"),
        "dark_group": payload.get("dark_group"),
        "flat_group": payload.get("flat_group"),
        "flat_bias_group": payload.get("flat_bias_group"),
        "bias_count": payload.get("bias_count"),
        "dark_count": payload.get("dark_count"),
        "flat_count": payload.get("flat_count"),
        "dark_exposure_s": payload.get("dark_exposure_s"),
        "master_dark_includes_bias": payload.get("master_dark_includes_bias"),
        "cache_scope": payload.get("cache_scope"),
        "cache_hit": payload.get("cache_hit"),
        "cache_key": payload.get("cache_key"),
        "cache_dir": payload.get("cache_dir"),
        "cache_files": cache_rows,
        "checks": checks,
        "passed": passed,
        "status": "passed" if passed else "failed",
    }


def _resident_calibration_output_contract(
    output: dict[str, Any],
    *,
    run_root: Path,
    index: int,
) -> dict[str, Any]:
    master_stats = output.get("master_stats") if isinstance(output.get("master_stats"), dict) else {}
    sets = master_stats.get("sets") if isinstance(master_stats.get("sets"), dict) else {}
    set_contracts = [
        _master_set_contract(str(key), payload, run_root)
        for key, payload in sets.items()
        if isinstance(payload, dict)
    ]
    timing = output.get("timing_s") if isinstance(output.get("timing_s"), dict) else {}
    fine_timing = output.get("fine_timing") if isinstance(output.get("fine_timing"), dict) else {}
    fine_seconds = fine_timing.get("seconds") if isinstance(fine_timing.get("seconds"), dict) else {}
    frame_ids = output.get("frame_ids") if isinstance(output.get("frame_ids"), list) else []
    checks = [
        _check(
            "resident_artifact_identity",
            bool(master_stats) and output.get("filter") is not None,
            {"filter": output.get("filter"), "master_stats_present": bool(master_stats)},
        ),
        _check(
            "master_set_records_present",
            bool(set_contracts),
            {"actual": len(set_contracts), "reported_set_count": master_stats.get("set_count")},
        ),
        _check(
            "master_set_contracts_passed",
            bool(set_contracts) and all(item["passed"] for item in set_contracts),
            {"failed": [item["key"] for item in set_contracts if not item["passed"]]},
        ),
        _check(
            "aggregate_source_counts_present",
            _positive_int(master_stats.get("bias_count"))
            and _positive_int(master_stats.get("dark_count"))
            and _positive_int(master_stats.get("flat_count")),
            {
                "bias_count": master_stats.get("bias_count"),
                "dark_count": master_stats.get("dark_count"),
                "flat_count": master_stats.get("flat_count"),
            },
        ),
        _check(
            "light_frame_ids_present",
            bool(frame_ids),
            {"frame_id_count": len(frame_ids)},
        ),
        _check(
            "resident_calibration_timing_present",
            _number_ge_zero(timing.get("master_build_or_load"))
            and (
                _number_ge_zero(timing.get("light_calibrate_store"))
                or _number_ge_zero(fine_seconds.get("light_calibrate_store_total"))
            ),
            {
                "master_build_or_load": timing.get("master_build_or_load"),
                "light_calibrate_store": timing.get("light_calibrate_store"),
                "fine_light_calibrate_store_total": fine_seconds.get("light_calibrate_store_total"),
            },
        ),
        _check(
            "resident_master_output_exists",
            _path_exists(output.get("master_path"), run_root),
            {"master_path": output.get("master_path")},
            "The resident calibration surface is accepted only when its downstream resident master artifact exists.",
        ),
    ]
    passed = all(item["passed"] for item in checks)
    return {
        "index": index,
        "filter": output.get("filter"),
        "contract_type": "resident_cuda_calibration_contract",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "master_path": output.get("master_path"),
        "master_path_exists": _path_exists(output.get("master_path"), run_root),
        "frame_count": len(frame_ids),
        "bias_count": master_stats.get("bias_count"),
        "dark_count": master_stats.get("dark_count"),
        "flat_count": master_stats.get("flat_count"),
        "set_count": len(set_contracts),
        "reported_set_count": master_stats.get("set_count"),
        "calibration_group_policy": master_stats.get("calibration_group_policy"),
        "resident_bytes_allocated_after_master_upload": output.get("resident_bytes_allocated_after_master_upload"),
        "timing_s": {
            "master_build_or_load": timing.get("master_build_or_load"),
            "light_calibrate_store": timing.get("light_calibrate_store"),
            "light_calibration_batch_native_total": timing.get("light_calibration_batch_native_total"),
            "resident_allocate_and_master_upload": timing.get("resident_allocate_and_master_upload"),
        },
        "sets": set_contracts,
        "checks": checks,
    }


def build_resident_calibration_contract(run_dir: str | Path) -> dict[str, Any]:
    run_root = Path(run_dir)
    artifact_path = run_root / "resident_artifacts.json"
    checks: list[dict[str, Any]] = [
        _check("resident_artifact_exists", artifact_path.exists(), {"path": str(artifact_path)})
    ]
    payload = _load_json_object(artifact_path) if artifact_path.exists() else {}
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    outputs = [
        _resident_calibration_output_contract(output, run_root=run_root, index=index)
        for index, output in enumerate(artifacts)
        if isinstance(output, dict)
    ]
    checks.extend(
        [
            _check(
                "resident_outputs_present",
                bool(outputs),
                {"actual": len(outputs), "required_min": 1},
            ),
            _check(
                "resident_output_contracts_passed",
                bool(outputs) and all(output["passed"] for output in outputs),
                {"failed": [output["index"] for output in outputs if not output["passed"]]},
            ),
        ]
    )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "resident_cuda_calibration_contract",
        "audit_type": "resident_cuda_calibration_contract",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "resident_artifact_path": str(artifact_path),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "output_count": len(outputs),
        "checks": checks,
        "outputs": outputs,
    }


def write_resident_calibration_contract_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GLASS Resident CUDA Calibration Contract",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Output count: `{payload.get('output_count')}`",
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
            "- "
            f"index={output.get('index')} filter={output.get('filter')} "
            f"status={output.get('status')} sets={output.get('set_count')} "
            f"frames={output.get('frame_count')}"
        )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_resident_calibration_contract(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        write_resident_calibration_contract_markdown(markdown, payload)
