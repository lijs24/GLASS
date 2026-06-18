from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


EXPECTED_MODEL = "continuous_grid_mean_std_v1"
EXPECTED_COEFFICIENT_FIELD_MODEL = "bilinear_tile_center_v1"
EXPECTED_INTERPOLATION = "bilinear_tile_center"
DISABLED_MODEL = "disabled_passthrough"
FULL_FIELD_STATUSES = {"written", "omitted_due_to_size"}


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    return payload if isinstance(payload, dict) else None


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


def _nonnegative_int(value: Any) -> bool:
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def _finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _grid_shape_ok(value: Any, rows: int | None, cols: int | None) -> bool:
    if rows is None or cols is None or not isinstance(value, list):
        return False
    if len(value) != rows:
        return False
    return all(isinstance(row, list) and len(row) == cols for row in value)


def _residual_summary_contract(summary: Any) -> dict[str, Any]:
    if not isinstance(summary, dict):
        return {
            "passed": False,
            "valid_pixels": None,
            "failed_checks": ["residual_summary_missing"],
        }
    checks = [
        _check(
            "valid_pixels_recorded",
            _nonnegative_int(summary.get("valid_pixels")),
            {"valid_pixels": summary.get("valid_pixels")},
        )
    ]
    valid_pixels = int(summary.get("valid_pixels") or 0) if checks[0]["passed"] else 0
    if valid_pixels > 0:
        checks.extend(
            [
                _check(
                    "rms_finite",
                    _finite_float(summary.get("rms")) is not None
                    and float(summary.get("rms")) >= 0.0,
                    {"rms": summary.get("rms")},
                ),
                _check(
                    "max_abs_finite",
                    _finite_float(summary.get("max_abs")) is not None
                    and float(summary.get("max_abs")) >= 0.0,
                    {"max_abs": summary.get("max_abs")},
                ),
            ]
        )
    return {
        "passed": all(item["passed"] for item in checks),
        "valid_pixels": summary.get("valid_pixels"),
        "rms": summary.get("rms"),
        "max_abs": summary.get("max_abs"),
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "checks": checks,
    }


def _coefficient_grid_contract(
    coefficient_path: Path | None,
    *,
    run_root: Path,
    item: dict[str, Any],
    reference_frame_id: Any,
) -> dict[str, Any]:
    if coefficient_path is None or not coefficient_path.exists():
        return {
            "path": str(coefficient_path) if coefficient_path else None,
            "present": False,
            "passed": False,
            "failed_checks": ["coefficient_grid_missing"],
            "checks": [
                _check(
                    "coefficient_grid_exists",
                    False,
                    {"path": str(coefficient_path) if coefficient_path else None},
                )
            ],
        }
    payload = _read_json_object(coefficient_path) or {}
    rows = None
    cols = None
    if _positive_int(payload.get("grid_rows")):
        rows = int(payload["grid_rows"])
    if _positive_int(payload.get("grid_cols")):
        cols = int(payload["grid_cols"])
    full_field_status = payload.get("full_field_map_status")
    scale_path = payload.get("scale_field_path") or item.get("scale_field_path")
    offset_path = payload.get("offset_field_path") or item.get("offset_field_path")
    residual_path = payload.get("residual_map_path") or item.get("residual_map_path")
    residual_contract = _residual_summary_contract(payload.get("residual_summary"))
    checks = [
        _check("coefficient_grid_exists", True, {"path": str(coefficient_path)}),
        _check(
            "frame_id_matches",
            payload.get("frame_id") == item.get("frame_id"),
            {"coefficient_frame_id": payload.get("frame_id"), "row_frame_id": item.get("frame_id")},
        ),
        _check(
            "reference_frame_id_matches",
            payload.get("reference_frame_id") == reference_frame_id,
            {
                "coefficient_reference_frame_id": payload.get("reference_frame_id"),
                "reference_frame_id": reference_frame_id,
            },
        ),
        _check("model_is_continuous", payload.get("model") == EXPECTED_MODEL, {"model": payload.get("model")}),
        _check(
            "coefficient_field_model_is_bilinear",
            payload.get("coefficient_field_model") == EXPECTED_COEFFICIENT_FIELD_MODEL,
            {"coefficient_field_model": payload.get("coefficient_field_model")},
        ),
        _check(
            "interpolation_recorded",
            payload.get("interpolation") == EXPECTED_INTERPOLATION,
            {"interpolation": payload.get("interpolation")},
        ),
        _check("tile_size_positive", _positive_int(payload.get("tile_size")), {"tile_size": payload.get("tile_size")}),
        _check("grid_rows_positive", rows is not None, {"grid_rows": payload.get("grid_rows")}),
        _check("grid_cols_positive", cols is not None, {"grid_cols": payload.get("grid_cols")}),
        _check(
            "raw_scale_grid_shape",
            _grid_shape_ok(payload.get("raw_scales"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "raw_offset_grid_shape",
            _grid_shape_ok(payload.get("raw_offsets"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "repaired_scale_grid_shape",
            _grid_shape_ok(payload.get("scales"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "repaired_offset_grid_shape",
            _grid_shape_ok(payload.get("offsets"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "valid_pixel_grid_shape",
            _grid_shape_ok(payload.get("valid_pixels"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "status_grid_shape",
            _grid_shape_ok(payload.get("statuses"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "empty_tile_repair_recorded",
            _nonnegative_int(payload.get("empty_tiles_filled")),
            {"empty_tiles_filled": payload.get("empty_tiles_filled")},
        ),
        _check(
            "crop_box_recorded",
            "crop_box" in payload,
            {"crop_box": payload.get("crop_box") if "crop_box" in payload else "missing"},
        ),
        _check(
            "full_field_map_status_recorded",
            full_field_status in FULL_FIELD_STATUSES,
            {"full_field_map_status": full_field_status, "allowed": sorted(FULL_FIELD_STATUSES)},
        ),
        _check(
            "full_field_maps_exist_when_written",
            full_field_status != "written"
            or (
                _path_exists(scale_path, run_root)
                and _path_exists(offset_path, run_root)
                and _path_exists(residual_path, run_root)
            ),
            {
                "full_field_map_status": full_field_status,
                "scale_field_path": scale_path,
                "offset_field_path": offset_path,
                "residual_map_path": residual_path,
            },
        ),
        _check(
            "residual_summary_contract",
            bool(residual_contract.get("passed")),
            residual_contract,
        ),
    ]
    return {
        "path": str(coefficient_path),
        "present": True,
        "passed": all(item["passed"] for item in checks),
        "frame_id": payload.get("frame_id"),
        "model": payload.get("model"),
        "coefficient_field_model": payload.get("coefficient_field_model"),
        "grid_rows": payload.get("grid_rows"),
        "grid_cols": payload.get("grid_cols"),
        "full_field_map_status": full_field_status,
        "residual_summary": payload.get("residual_summary"),
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "checks": checks,
    }


def _enabled_row_contract(
    item: dict[str, Any],
    *,
    index: int,
    run_root: Path,
    reference_frame_id: Any,
) -> dict[str, Any]:
    coefficient_path = _resolve_path(item.get("coefficient_grid_path"), run_root)
    coefficient_contract = _coefficient_grid_contract(
        coefficient_path,
        run_root=run_root,
        item=item,
        reference_frame_id=reference_frame_id,
    )
    residual_contract = _residual_summary_contract(item.get("residual_summary"))
    checks = [
        _check("frame_id_present", bool(item.get("frame_id")), {"frame_id": item.get("frame_id")}),
        _check(
            "normalized_path_exists",
            _path_exists(item.get("normalized_path"), run_root),
            {"normalized_path": item.get("normalized_path")},
        ),
        _check(
            "coverage_path_exists",
            _path_exists(item.get("coverage_path"), run_root),
            {"coverage_path": item.get("coverage_path")},
        ),
        _check(
            "dq_mask_path_exists",
            _path_exists(item.get("dq_mask_path"), run_root),
            {"dq_mask_path": item.get("dq_mask_path")},
        ),
        _check(
            "dq_summary_present",
            isinstance(item.get("dq_summary"), dict),
            {"dq_summary": item.get("dq_summary")},
        ),
        _check("crop_box_recorded", "crop_box" in item, {"crop_box": item.get("crop_box") if "crop_box" in item else "missing"}),
        _check("model_is_continuous", item.get("model") == EXPECTED_MODEL, {"model": item.get("model")}),
        _check(
            "coefficient_field_model_is_bilinear",
            item.get("coefficient_field_model") == EXPECTED_COEFFICIENT_FIELD_MODEL,
            {"coefficient_field_model": item.get("coefficient_field_model")},
        ),
        _check(
            "interpolation_recorded",
            item.get("interpolation") == EXPECTED_INTERPOLATION,
            {"interpolation": item.get("interpolation")},
        ),
        _check("tile_size_positive", _positive_int(item.get("tile_size")), {"tile_size": item.get("tile_size")}),
        _check("grid_rows_positive", _positive_int(item.get("grid_rows")), {"grid_rows": item.get("grid_rows")}),
        _check("grid_cols_positive", _positive_int(item.get("grid_cols")), {"grid_cols": item.get("grid_cols")}),
        _check(
            "valid_pixels_recorded",
            _nonnegative_int(item.get("valid_pixels")),
            {"valid_pixels": item.get("valid_pixels")},
        ),
        _check(
            "empty_tile_repair_recorded",
            _nonnegative_int(item.get("empty_tiles_filled")),
            {"empty_tiles_filled": item.get("empty_tiles_filled")},
        ),
        _check(
            "full_field_map_status_recorded",
            item.get("full_field_map_status") in FULL_FIELD_STATUSES,
            {"full_field_map_status": item.get("full_field_map_status")},
        ),
        _check(
            "residual_summary_contract",
            bool(residual_contract.get("passed")),
            residual_contract,
        ),
        _check(
            "coefficient_grid_contract",
            bool(coefficient_contract.get("passed")),
            coefficient_contract,
        ),
    ]
    return {
        "index": index,
        "frame_id": item.get("frame_id"),
        "status": item.get("status"),
        "enabled": True,
        "model": item.get("model"),
        "coefficient_field_model": item.get("coefficient_field_model"),
        "coefficient_grid_path": item.get("coefficient_grid_path"),
        "full_field_map_status": item.get("full_field_map_status"),
        "residual_summary": item.get("residual_summary"),
        "coefficient_grid_contract": coefficient_contract,
        "passed": all(row["passed"] for row in checks),
        "failed_checks": [row["name"] for row in checks if not row["passed"]],
        "checks": checks,
    }


def _disabled_row_contract(item: dict[str, Any], *, index: int, run_root: Path) -> dict[str, Any]:
    dq_path = item.get("dq_mask_path")
    checks = [
        _check("frame_id_present", bool(item.get("frame_id")), {"frame_id": item.get("frame_id")}),
        _check(
            "passthrough_status_recorded",
            item.get("status") == DISABLED_MODEL,
            {"status": item.get("status"), "expected": DISABLED_MODEL},
        ),
        _check("crop_box_recorded", "crop_box" in item, {"crop_box": item.get("crop_box") if "crop_box" in item else "missing"}),
        _check(
            "normalized_path_exists",
            _path_exists(item.get("normalized_path"), run_root),
            {"normalized_path": item.get("normalized_path")},
        ),
        _check(
            "coverage_path_exists",
            _path_exists(item.get("coverage_path"), run_root),
            {"coverage_path": item.get("coverage_path")},
        ),
        _check(
            "dq_mask_path_optional_exists",
            not dq_path or _path_exists(dq_path, run_root),
            {"dq_mask_path": dq_path},
        ),
        _check(
            "dq_summary_present",
            isinstance(item.get("dq_summary"), dict),
            {"dq_summary": item.get("dq_summary")},
        ),
    ]
    return {
        "index": index,
        "frame_id": item.get("frame_id"),
        "status": item.get("status"),
        "enabled": False,
        "passed": all(row["passed"] for row in checks),
        "failed_checks": [row["name"] for row in checks if not row["passed"]],
        "checks": checks,
    }


def build_local_norm_contract(run_dir: str | Path) -> dict[str, Any]:
    run_root = Path(run_dir)
    local_norm_path = run_root / "local_norm_results.json"
    local_norm = _read_json_object(local_norm_path)
    created_at = now_iso()
    if local_norm is None:
        checks = [
            _check(
                "local_norm_results_present",
                False,
                {"path": str(local_norm_path), "exists": local_norm_path.exists()},
            )
        ]
        return {
            "schema_version": 1,
            "artifact_type": "local_norm_contract",
            "created_at": created_at,
            "run_dir": str(run_root),
            "local_norm_path": str(local_norm_path),
            "status": "failed",
            "passed": False,
            "enabled": None,
            "checks": checks,
            "outputs": [],
            "failed_checks": [item["name"] for item in checks],
            "summary": {"output_count": 0, "failed_output_count": 0},
        }

    enabled = bool(local_norm.get("enabled"))
    outputs = local_norm.get("local_norm_results") if isinstance(local_norm.get("local_norm_results"), list) else []
    top_checks = [
        _check("local_norm_results_present", True, {"path": str(local_norm_path)}),
        _check(
            "schema_version_recorded",
            _positive_int(local_norm.get("schema_version")),
            {"schema_version": local_norm.get("schema_version")},
        ),
        _check(
            "enabled_state_recorded",
            isinstance(local_norm.get("enabled"), bool),
            {"enabled": local_norm.get("enabled")},
        ),
        _check(
            "crop_box_recorded",
            "crop_box" in local_norm,
            {"crop_box": local_norm.get("crop_box") if "crop_box" in local_norm else "missing"},
        ),
        _check(
            "outputs_list_recorded",
            isinstance(outputs, list),
            {"output_count": len(outputs) if isinstance(outputs, list) else None},
        ),
    ]
    if enabled:
        top_checks.extend(
            [
                _check(
                    "reference_frame_id_recorded",
                    bool(local_norm.get("reference_frame_id")),
                    {"reference_frame_id": local_norm.get("reference_frame_id")},
                ),
                _check("model_is_continuous", local_norm.get("model") == EXPECTED_MODEL, {"model": local_norm.get("model")}),
                _check(
                    "coefficient_field_model_is_bilinear",
                    local_norm.get("coefficient_field_model") == EXPECTED_COEFFICIENT_FIELD_MODEL,
                    {"coefficient_field_model": local_norm.get("coefficient_field_model")},
                ),
                _check("enabled_outputs_present", bool(outputs), {"output_count": len(outputs)}),
            ]
        )
    else:
        top_checks.append(
            _check(
                "disabled_model_recorded",
                local_norm.get("coefficient_field_model") == DISABLED_MODEL,
                {"coefficient_field_model": local_norm.get("coefficient_field_model")},
            )
        )

    output_contracts = [
        _enabled_row_contract(
            item,
            index=index,
            run_root=run_root,
            reference_frame_id=local_norm.get("reference_frame_id"),
        )
        if enabled
        else _disabled_row_contract(item, index=index, run_root=run_root)
        for index, item in enumerate(outputs)
        if isinstance(item, dict)
    ]
    row_count_match = len(output_contracts) == len(outputs)
    top_checks.append(
        _check(
            "all_outputs_are_objects",
            row_count_match,
            {"output_count": len(outputs), "object_output_count": len(output_contracts)},
        )
    )
    top_checks.append(
        _check(
            "output_contracts_passed",
            all(item["passed"] for item in output_contracts),
            {
                "output_count": len(output_contracts),
                "failed": [item["frame_id"] or item["index"] for item in output_contracts if not item["passed"]],
            },
        )
    )
    passed = all(item["passed"] for item in top_checks)
    failed_outputs = [item for item in output_contracts if not item["passed"]]
    return {
        "schema_version": 1,
        "artifact_type": "local_norm_contract",
        "created_at": created_at,
        "run_dir": str(run_root),
        "local_norm_path": str(local_norm_path),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "enabled": enabled,
        "reference_frame_id": local_norm.get("reference_frame_id"),
        "model": local_norm.get("model"),
        "coefficient_field_model": local_norm.get("coefficient_field_model"),
        "crop_box": local_norm.get("crop_box") if "crop_box" in local_norm else "missing",
        "summary": {
            "output_count": len(output_contracts),
            "failed_output_count": len(failed_outputs),
            "coefficient_field_model": local_norm.get("coefficient_field_model"),
            "enabled": enabled,
            "reference_frame_id": local_norm.get("reference_frame_id"),
        },
        "checks": top_checks,
        "outputs": output_contracts,
        "failed_checks": [item["name"] for item in top_checks if not item["passed"]],
        "failed_outputs": [
            {"frame_id": item["frame_id"], "index": item["index"], "failed_checks": item["failed_checks"]}
            for item in failed_outputs
        ],
    }


def write_local_norm_contract(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is None:
        return
    lines = [
        "# Local Normalization Contract",
        "",
        f"- Status: {payload.get('status')}",
        f"- Passed: {payload.get('passed')}",
        f"- Enabled: {payload.get('enabled')}",
        f"- Reference frame: {payload.get('reference_frame_id')}",
        f"- Model: {payload.get('model')}",
        f"- Coefficient field model: {payload.get('coefficient_field_model')}",
        f"- Output count: {(payload.get('summary') or {}).get('output_count')}",
        f"- Failed output count: {(payload.get('summary') or {}).get('failed_output_count')}",
        "",
        "## Checks",
        "",
    ]
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: {item.get('name')} - {item.get('evidence')}")
    lines.extend(["", "## Outputs", ""])
    for item in payload.get("outputs") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(
            f"- {marker}: {item.get('frame_id')} status={item.get('status')} "
            f"model={item.get('model')} failed={item.get('failed_checks')}"
        )
    Path(markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
