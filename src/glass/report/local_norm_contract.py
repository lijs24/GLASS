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
RESIDENT_MODES = {"resident_global_mean_std", "resident_grid_mean_std", "off"}
RESIDENT_FRAME_STATUSES = {"reference", "ok", "partial", "offset_only", "empty", "skipped_zero_weight"}
RESIDENT_ACTIVE_FRAME_STATUSES = {"reference", "ok", "partial", "offset_only"}
RESIDENT_ZERO_WEIGHT_FRAME_STATUSES = {"empty", "skipped_zero_weight"}


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


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def _grid_list_shape_ok(value: Any, rows: int | None, cols: int | None) -> bool:
    return _grid_shape_ok(value, rows, cols)


def _resident_grid_contract(grid: Any, *, status: str) -> dict[str, Any]:
    if not isinstance(grid, dict):
        required = status not in {"reference", "skipped_zero_weight"}
        return {
            "present": False,
            "passed": not required,
            "required": required,
            "failed_checks": ["grid_coefficients_missing"] if required else [],
            "checks": [
                _check(
                    "grid_coefficients_present",
                    not required,
                    {"status": status, "required": required},
                )
            ],
        }
    rows = int(grid.get("grid_rows") or 0) if _positive_int(grid.get("grid_rows")) else None
    cols = int(grid.get("grid_cols") or 0) if _positive_int(grid.get("grid_cols")) else None
    valid_total = None
    if _nonnegative_int(grid.get("valid_pixel_total")):
        valid_total = int(grid.get("valid_pixel_total") or 0)
    checks = [
        _check("grid_coefficients_present", True, {"status": status}),
        _check("model_recorded", bool(grid.get("model")), {"model": grid.get("model")}),
        _check("tile_size_positive", _positive_int(grid.get("tile_size")), {"tile_size": grid.get("tile_size")}),
        _check("grid_rows_positive", rows is not None, {"grid_rows": grid.get("grid_rows")}),
        _check("grid_cols_positive", cols is not None, {"grid_cols": grid.get("grid_cols")}),
        _check(
            "scales_shape_matches_grid",
            _grid_list_shape_ok(grid.get("scales"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "offsets_shape_matches_grid",
            _grid_list_shape_ok(grid.get("offsets"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "valid_pixels_shape_matches_grid",
            _grid_list_shape_ok(grid.get("valid_pixels"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "statuses_shape_matches_grid",
            _grid_list_shape_ok(grid.get("statuses"), rows, cols),
            {"grid_rows": rows, "grid_cols": cols},
        ),
        _check(
            "valid_pixel_total_recorded",
            valid_total is not None,
            {"valid_pixel_total": grid.get("valid_pixel_total")},
        ),
        _check(
            "empty_tiles_recorded",
            _nonnegative_int(grid.get("empty_tiles")),
            {"empty_tiles": grid.get("empty_tiles")},
        ),
        _check("ok_tiles_recorded", _nonnegative_int(grid.get("ok_tiles")), {"ok_tiles": grid.get("ok_tiles")}),
        _check(
            "nonempty_status_has_valid_pixels",
            status in {"reference", "skipped_zero_weight", "empty"} or (valid_total is not None and valid_total > 0),
            {"status": status, "valid_pixel_total": valid_total},
        ),
    ]
    return {
        "present": True,
        "passed": all(item["passed"] for item in checks),
        "required": True,
        "model": grid.get("model"),
        "tile_size": grid.get("tile_size"),
        "grid_rows": grid.get("grid_rows"),
        "grid_cols": grid.get("grid_cols"),
        "valid_pixel_total": grid.get("valid_pixel_total"),
        "empty_tiles": grid.get("empty_tiles"),
        "ok_tiles": grid.get("ok_tiles"),
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "checks": checks,
    }


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


def _resident_frame_contract(
    item: dict[str, Any],
    *,
    index: int,
    group: dict[str, Any],
    group_index: int,
) -> dict[str, Any]:
    mode = str(item.get("model") or group.get("mode") or "")
    status = str(item.get("status") or "")
    grid_contract = _resident_grid_contract(item.get("grid_coefficients"), status=status)
    scale = _finite_float(item.get("scale"))
    offset = _finite_float(item.get("offset"))
    checks = [
        _check("frame_id_present", bool(item.get("frame_id")), {"frame_id": item.get("frame_id")}),
        _check(
            "reference_frame_id_present",
            bool(item.get("reference_frame_id") or group.get("reference_frame_id")),
            {
                "frame_reference_frame_id": item.get("reference_frame_id"),
                "group_reference_frame_id": group.get("reference_frame_id"),
            },
        ),
        _check("resident_model_recorded", mode in RESIDENT_MODES, {"model": mode, "allowed": sorted(RESIDENT_MODES)}),
        _check(
            "status_supported",
            status in RESIDENT_FRAME_STATUSES,
            {"status": status, "allowed": sorted(RESIDENT_FRAME_STATUSES)},
        ),
        _check("scale_finite", scale is not None, {"scale": item.get("scale")}),
        _check("offset_finite", offset is not None, {"offset": item.get("offset")}),
        _check(
            "grid_contract",
            bool(grid_contract.get("passed")),
            grid_contract,
            "Resident grid LN rows must carry in-VRAM coefficient grids when a non-reference frame was normalized.",
        ),
    ]
    return {
        "index": index,
        "group_index": group_index,
        "frame_id": item.get("frame_id"),
        "status": status,
        "enabled": bool(group.get("enabled")),
        "model": mode,
        "resident_in_vram": True,
        "reference_frame_id": item.get("reference_frame_id") or group.get("reference_frame_id"),
        "scale": item.get("scale"),
        "offset": item.get("offset"),
        "grid_contract": grid_contract,
        "passed": all(row["passed"] for row in checks),
        "failed_checks": [row["name"] for row in checks if not row["passed"]],
        "checks": checks,
    }


def _resident_group_contracts(local_norm: dict[str, Any]) -> list[dict[str, Any]]:
    output_contracts: list[dict[str, Any]] = []
    groups = local_norm.get("groups") if isinstance(local_norm.get("groups"), list) else []
    for group_index, group in enumerate(groups):
        if not isinstance(group, dict):
            continue
        frame_results = group.get("frame_results") if isinstance(group.get("frame_results"), list) else []
        for frame_index, item in enumerate(frame_results):
            if isinstance(item, dict):
                output_contracts.append(
                    _resident_frame_contract(
                        item,
                        index=len(output_contracts),
                        group=group,
                        group_index=group_index,
                    )
                )
    return output_contracts


def _duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _resident_frame_accounting_closure(
    output_contracts: list[dict[str, Any]],
    *,
    enabled: bool,
    run_root: Path,
    status_counts: dict[str, int],
) -> dict[str, Any]:
    if not enabled:
        return {
            "status": "not_required",
            "passed": True,
            "reason": "resident local normalization is disabled",
        }

    frame_accounting_path = run_root / "frame_accounting.json"
    frame_accounting = _read_json_object(frame_accounting_path)
    if frame_accounting is None:
        return {
            "status": "missing",
            "passed": False,
            "path": str(frame_accounting_path),
            "reason": "resident local normalization is enabled but frame_accounting.json is missing",
        }

    summary = frame_accounting.get("summary") if isinstance(frame_accounting.get("summary"), dict) else {}
    frames = frame_accounting.get("frames") if isinstance(frame_accounting.get("frames"), list) else []
    frame_rows = [row for row in frames if isinstance(row, dict)]
    accounting_by_id = {str(row.get("frame_id")): row for row in frame_rows if row.get("frame_id")}
    output_ids = [str(item.get("frame_id")) for item in output_contracts if item.get("frame_id")]
    duplicate_output_ids = _duplicate_values(output_ids)
    missing_accounting_ids = sorted(set(output_ids).difference(accounting_by_id))

    input_light_frames = _int_or_none(summary.get("input_light_frames"))
    if input_light_frames is None and frame_rows:
        input_light_frames = len(frame_rows)
    integrated_frames = _int_or_none(summary.get("integrated_frames"))
    if integrated_frames is None and frame_rows:
        integrated_frames = sum(
            1
            for row in frame_rows
            if row.get("integration_status") == "used" or row.get("final_status") == "integrated"
        )
    zero_weight_frames = _int_or_none(summary.get("zero_weight_frames"))
    if zero_weight_frames is None:
        integration_counts = summary.get("integration_status_counts")
        if isinstance(integration_counts, dict):
            zero_weight_frames = _int_or_none(integration_counts.get("zero_weight"))
    if zero_weight_frames is None and frame_rows:
        zero_weight_frames = sum(
            1
            for row in frame_rows
            if row.get("integration_status") == "zero_weight" or _finite_float(row.get("integration_weight")) == 0.0
        )

    active_output_count = sum(status_counts.get(status, 0) for status in RESIDENT_ACTIVE_FRAME_STATUSES)
    zero_weight_output_count = sum(status_counts.get(status, 0) for status in RESIDENT_ZERO_WEIGHT_FRAME_STATUSES)
    unknown_status_counts = {
        status: count
        for status, count in status_counts.items()
        if status not in RESIDENT_ACTIVE_FRAME_STATUSES and status not in RESIDENT_ZERO_WEIGHT_FRAME_STATUSES
    }

    row_mismatches: list[dict[str, Any]] = []
    for item in output_contracts:
        frame_id = item.get("frame_id")
        if not frame_id:
            continue
        status = str(item.get("status") or "")
        accounting_row = accounting_by_id.get(str(frame_id))
        if accounting_row is None:
            continue
        integration_status = str(accounting_row.get("integration_status") or "")
        integration_weight = _finite_float(accounting_row.get("integration_weight"))
        accounting_used = integration_status == "used" or accounting_row.get("final_status") == "integrated"
        accounting_zero = integration_status == "zero_weight" or integration_weight == 0.0
        if status in RESIDENT_ACTIVE_FRAME_STATUSES and not accounting_used:
            row_mismatches.append(
                {
                    "frame_id": frame_id,
                    "local_norm_status": status,
                    "integration_status": integration_status,
                    "integration_weight": accounting_row.get("integration_weight"),
                    "expected": "integration used",
                }
            )
        if status in RESIDENT_ZERO_WEIGHT_FRAME_STATUSES and not accounting_zero:
            row_mismatches.append(
                {
                    "frame_id": frame_id,
                    "local_norm_status": status,
                    "integration_status": integration_status,
                    "integration_weight": accounting_row.get("integration_weight"),
                    "expected": "zero-weight integration",
                }
            )

    checks = [
        _check(
            "frame_accounting_present",
            True,
            {"path": str(frame_accounting_path)},
        ),
        _check(
            "local_norm_output_count_matches_input_light_frames",
            input_light_frames == len(output_contracts),
            {
                "input_light_frames": input_light_frames,
                "local_norm_output_count": len(output_contracts),
            },
        ),
        _check(
            "active_local_norm_count_matches_integrated_frames",
            integrated_frames == active_output_count,
            {
                "integrated_frames": integrated_frames,
                "active_local_norm_output_count": active_output_count,
                "active_statuses": sorted(RESIDENT_ACTIVE_FRAME_STATUSES),
            },
        ),
        _check(
            "zero_weight_local_norm_count_matches_zero_weight_frames",
            zero_weight_frames == zero_weight_output_count,
            {
                "zero_weight_frames": zero_weight_frames,
                "zero_weight_local_norm_output_count": zero_weight_output_count,
                "zero_weight_statuses": sorted(RESIDENT_ZERO_WEIGHT_FRAME_STATUSES),
            },
        ),
        _check(
            "local_norm_statuses_are_accounted",
            not unknown_status_counts,
            {"unknown_status_counts": unknown_status_counts},
        ),
        _check(
            "local_norm_frame_ids_unique",
            not duplicate_output_ids,
            {"duplicate_frame_ids": duplicate_output_ids[:20]},
        ),
        _check(
            "local_norm_frame_ids_present_in_frame_accounting",
            not missing_accounting_ids,
            {
                "missing_count": len(missing_accounting_ids),
                "missing_frame_ids": missing_accounting_ids[:20],
            },
        ),
        _check(
            "per_frame_local_norm_status_matches_integration_status",
            not row_mismatches,
            {"mismatch_count": len(row_mismatches), "mismatches": row_mismatches[:20]},
        ),
    ]
    return {
        "status": "passed" if all(item["passed"] for item in checks) else "failed",
        "passed": all(item["passed"] for item in checks),
        "path": str(frame_accounting_path),
        "input_light_frames": input_light_frames,
        "integrated_frames": integrated_frames,
        "zero_weight_frames": zero_weight_frames,
        "local_norm_output_count": len(output_contracts),
        "active_local_norm_output_count": active_output_count,
        "zero_weight_local_norm_output_count": zero_weight_output_count,
        "status_counts": status_counts,
        "duplicate_frame_ids": duplicate_output_ids[:20],
        "missing_frame_ids": missing_accounting_ids[:20],
        "row_mismatches": row_mismatches[:20],
        "checks": checks,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
    }


def _resident_local_norm_contract(
    local_norm: dict[str, Any],
    *,
    run_root: Path,
    local_norm_path: Path,
    created_at: str,
) -> dict[str, Any]:
    enabled = bool(local_norm.get("enabled"))
    groups = local_norm.get("groups") if isinstance(local_norm.get("groups"), list) else []
    group_objects = [group for group in groups if isinstance(group, dict)]
    output_contracts = _resident_group_contracts(local_norm)
    mode = str(local_norm.get("mode") or ("off" if not enabled else ""))
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
            "source_stage_is_resident",
            local_norm.get("source_stage") == "resident_calibrated_stack",
            {"source_stage": local_norm.get("source_stage")},
        ),
        _check("resident_mode_recorded", mode in RESIDENT_MODES, {"mode": mode, "allowed": sorted(RESIDENT_MODES)}),
        _check("crop_box_recorded", "crop_box" in local_norm, {"crop_box": local_norm.get("crop_box") if "crop_box" in local_norm else "missing"}),
        _check(
            "groups_list_recorded",
            isinstance(groups, list) and len(group_objects) == len(groups),
            {"group_count": len(groups), "object_group_count": len(group_objects)},
        ),
    ]
    if enabled:
        top_checks.extend(
            [
                _check("enabled_groups_present", bool(group_objects), {"group_count": len(group_objects)}),
                _check("resident_outputs_present", bool(output_contracts), {"output_count": len(output_contracts)}),
            ]
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
    status_counts: dict[str, int] = {}
    for item in output_contracts:
        status = str(item.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    frame_accounting_closure = _resident_frame_accounting_closure(
        output_contracts,
        enabled=enabled,
        run_root=run_root,
        status_counts=status_counts,
    )
    top_checks.append(
        _check(
            "resident_frame_accounting_closure",
            bool(frame_accounting_closure.get("passed")),
            frame_accounting_closure,
            "Resident LN rows must close against frame_accounting.json so the normalized and integrated frame sets cannot drift.",
        )
    )
    passed = all(item["passed"] for item in top_checks)
    return {
        "schema_version": 1,
        "artifact_type": "local_norm_contract",
        "contract_surface": "resident_in_vram",
        "created_at": created_at,
        "run_dir": str(run_root),
        "local_norm_path": str(local_norm_path),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "enabled": enabled,
        "reference_frame_id": next((group.get("reference_frame_id") for group in group_objects if group.get("reference_frame_id")), None),
        "model": mode,
        "coefficient_field_model": "resident_in_vram_grid" if mode == "resident_grid_mean_std" else mode,
        "crop_box": local_norm.get("crop_box") if "crop_box" in local_norm else "missing",
        "summary": {
            "output_count": len(output_contracts),
            "failed_output_count": len(failed_outputs),
            "group_count": len(group_objects),
            "enabled": enabled,
            "mode": mode,
            "status_counts": status_counts,
            "frame_accounting_closure": frame_accounting_closure,
        },
        "frame_accounting_closure": frame_accounting_closure,
        "checks": top_checks,
        "outputs": output_contracts,
        "failed_checks": [item["name"] for item in top_checks if not item["passed"]],
        "failed_outputs": [
            {"frame_id": item["frame_id"], "index": item["index"], "failed_checks": item["failed_checks"]}
            for item in failed_outputs
        ],
    }


def _residual_quality_summary(output_contracts: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    rms_values: list[float] = []
    max_abs_values: list[float] = []
    total_valid_pixels = 0
    zero_valid_output_count = 0
    for item in output_contracts:
        if not item.get("enabled"):
            continue
        summary = item.get("residual_summary") if isinstance(item.get("residual_summary"), dict) else {}
        residual_contract = _residual_summary_contract(summary)
        valid_pixels = int(residual_contract.get("valid_pixels") or 0)
        rms = _finite_float(residual_contract.get("rms"))
        max_abs = _finite_float(residual_contract.get("max_abs"))
        if valid_pixels == 0:
            zero_valid_output_count += 1
        if valid_pixels > 0:
            total_valid_pixels += valid_pixels
        if rms is not None:
            rms_values.append(rms)
        if max_abs is not None:
            max_abs_values.append(max_abs)
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "valid_pixels": valid_pixels,
                "rms": rms,
                "max_abs": max_abs,
                "passed": bool(residual_contract.get("passed")),
                "failed_checks": residual_contract.get("failed_checks") or [],
            }
        )
    return {
        "output_count": len(rows),
        "valid_output_count": sum(1 for row in rows if row["valid_pixels"] > 0),
        "failed_output_count": sum(1 for row in rows if not row["passed"]),
        "zero_valid_output_count": zero_valid_output_count,
        "total_valid_pixels": total_valid_pixels,
        "max_rms": max(rms_values) if rms_values else None,
        "max_abs": max(max_abs_values) if max_abs_values else None,
        "outputs": rows,
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
    if local_norm.get("source_stage") == "resident_calibrated_stack" or isinstance(local_norm.get("groups"), list):
        return _resident_local_norm_contract(
            local_norm,
            run_root=run_root,
            local_norm_path=local_norm_path,
            created_at=created_at,
        )
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
    residual_quality = _residual_quality_summary(output_contracts)
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
            "residual_quality": residual_quality,
        },
        "residual_quality": residual_quality,
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
    summary = payload.get("summary") or {}
    frame_accounting_closure = summary.get("frame_accounting_closure") or payload.get("frame_accounting_closure") or {}
    lines = [
        "# Local Normalization Contract",
        "",
        f"- Status: {payload.get('status')}",
        f"- Passed: {payload.get('passed')}",
        f"- Enabled: {payload.get('enabled')}",
        f"- Reference frame: {payload.get('reference_frame_id')}",
        f"- Model: {payload.get('model')}",
        f"- Coefficient field model: {payload.get('coefficient_field_model')}",
        f"- Output count: {summary.get('output_count')}",
        f"- Failed output count: {summary.get('failed_output_count')}",
        f"- Residual max RMS: {(summary.get('residual_quality') or {}).get('max_rms')}",
        f"- Residual max abs: {(summary.get('residual_quality') or {}).get('max_abs')}",
    ]
    if frame_accounting_closure:
        lines.extend(
            [
                f"- Frame accounting closure: {frame_accounting_closure.get('status')}",
                f"- Frame accounting input/integrated/zero-weight: "
                f"{frame_accounting_closure.get('input_light_frames')} / "
                f"{frame_accounting_closure.get('integrated_frames')} / "
                f"{frame_accounting_closure.get('zero_weight_frames')}",
                f"- LN active/zero-weight rows: "
                f"{frame_accounting_closure.get('active_local_norm_output_count')} / "
                f"{frame_accounting_closure.get('zero_weight_local_norm_output_count')}",
            ]
        )
    lines.extend(["", "## Checks", ""])
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
