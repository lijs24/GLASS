from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import now_iso


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


def _positive_int(value: Any) -> int | None:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric > 0 else None


def _nonnegative_int(value: Any) -> int | None:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric >= 0 else None


def _image_shape(path_value: Any, run_root: Path) -> tuple[int, int] | None:
    path = _resolve_path(path_value, run_root)
    if path is None or not path.exists():
        return None
    try:
        with FitsImageReader(path) as reader:
            return int(reader.width), int(reader.height)
    except Exception:
        return None


def _pixel_verification(
    item: dict[str, Any],
    run_root: Path,
    *,
    tile_size: int,
    tolerance: int,
) -> dict[str, Any]:
    coverage_path = _resolve_path(item.get("coverage_path"), run_root)
    dq_path = _resolve_path(item.get("dq_mask_path"), run_root)
    if coverage_path is None or not coverage_path.exists() or dq_path is None or not dq_path.exists():
        return {
            "verified": False,
            "status": "missing_artifact",
            "passed": False,
            "coverage_path": None if coverage_path is None else str(coverage_path),
            "dq_mask_path": None if dq_path is None else str(dq_path),
            "failed_checks": ["coverage_or_dq_missing"],
        }

    try:
        with FitsImageReader(coverage_path) as coverage_reader, FitsImageReader(dq_path) as dq_reader:
            if coverage_reader.shape != dq_reader.shape:
                return {
                    "verified": False,
                    "status": "shape_mismatch",
                    "passed": False,
                    "coverage_shape": list(coverage_reader.shape),
                    "dq_shape": list(dq_reader.shape),
                    "failed_checks": ["coverage_dq_shape_match"],
                }
            width = int(coverage_reader.width)
            height = int(coverage_reader.height)
            coverage_valid = 0
            coverage_invalid = 0
            dq_valid = 0
            dq_warp_edge = 0
            for tile in iter_tiles(width=width, height=height, tile_size=max(1, int(tile_size))):
                coverage = coverage_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                dq = dq_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1).astype(np.uint32, copy=False)
                valid = np.isfinite(coverage) & (coverage > 0.5)
                coverage_valid += int(np.count_nonzero(valid))
                coverage_invalid += int(valid.size - np.count_nonzero(valid))
                dq_valid += int(np.count_nonzero(dq == 0))
                dq_warp_edge += int(np.count_nonzero((dq & np.uint32(int(DQFlag.WARP_EDGE))) != 0))
    except Exception as exc:
        return {
            "verified": False,
            "status": "read_failed",
            "passed": False,
            "error": str(exc),
            "failed_checks": ["pixel_verification_read"],
        }

    reported_valid = _nonnegative_int(item.get("valid_pixels"))
    dq_summary = item.get("dq_summary") if isinstance(item.get("dq_summary"), dict) else {}
    summary_valid = _nonnegative_int(dq_summary.get("valid"))
    summary_warp_edge = _nonnegative_int(dq_summary.get("warp_edge"))
    expected_warp_edge = coverage_invalid
    valid_delta = None if reported_valid is None else abs(int(reported_valid) - coverage_valid)
    dq_valid_delta = abs(dq_valid - coverage_valid)
    summary_valid_delta = None if summary_valid is None else abs(int(summary_valid) - dq_valid)
    dq_warp_edge_delta = abs(dq_warp_edge - expected_warp_edge)
    summary_warp_edge_delta = None if summary_warp_edge is None else abs(int(summary_warp_edge) - dq_warp_edge)
    max_delta = max(
        value
        for value in (
            valid_delta,
            dq_valid_delta,
            summary_valid_delta,
            dq_warp_edge_delta,
            summary_warp_edge_delta,
        )
        if value is not None
    )
    allowed = max(0, int(tolerance))
    failed_checks: list[str] = []
    if valid_delta is None or valid_delta > allowed:
        failed_checks.append("reported_valid_matches_coverage")
    if dq_valid_delta > allowed:
        failed_checks.append("dq_valid_matches_coverage")
    if summary_valid_delta is None or summary_valid_delta > allowed:
        failed_checks.append("dq_summary_valid_matches_dq")
    if dq_warp_edge_delta > allowed:
        failed_checks.append("dq_warp_edge_matches_coverage_invalid")
    if summary_warp_edge is not None and summary_warp_edge_delta is not None and summary_warp_edge_delta > allowed:
        failed_checks.append("dq_summary_warp_edge_matches_dq")
    return {
        "verified": True,
        "status": "passed" if not failed_checks else "failed",
        "passed": not failed_checks,
        "tile_size": max(1, int(tile_size)),
        "tolerance": allowed,
        "coverage_valid_pixels": coverage_valid,
        "coverage_invalid_pixels": coverage_invalid,
        "reported_valid_pixels": reported_valid,
        "dq_valid_pixels": dq_valid,
        "dq_warp_edge_pixels": dq_warp_edge,
        "expected_warp_edge_pixels": expected_warp_edge,
        "dq_summary_valid": summary_valid,
        "dq_summary_warp_edge": summary_warp_edge,
        "valid_delta": valid_delta,
        "dq_valid_delta": dq_valid_delta,
        "summary_valid_delta": summary_valid_delta,
        "dq_warp_edge_delta": dq_warp_edge_delta,
        "summary_warp_edge_delta": summary_warp_edge_delta,
        "max_delta": max_delta,
        "failed_checks": failed_checks,
    }


def _row_by_frame_id(rows: list[dict[str, Any]], frame_id: str | None) -> dict[str, Any] | None:
    if frame_id is None:
        return None
    for row in rows:
        if str(row.get("frame_id")) == str(frame_id):
            return row
    return None


def _reference_row(rows: list[dict[str, Any]], reference_frame_id: str | None) -> dict[str, Any] | None:
    explicit = _row_by_frame_id(rows, reference_frame_id)
    if explicit is not None:
        return explicit
    for row in rows:
        if str(row.get("registration_status") or "").lower() == "reference":
            return row
    return rows[0] if rows else None


def _science_residual(
    item: dict[str, Any],
    reference: dict[str, Any],
    run_root: Path,
    *,
    tile_size: int,
    max_rms: float | None,
    max_abs: float | None,
) -> dict[str, Any]:
    registered_path = _resolve_path(item.get("registered_path"), run_root)
    coverage_path = _resolve_path(item.get("coverage_path"), run_root)
    reference_path = _resolve_path(reference.get("registered_path"), run_root)
    reference_coverage_path = _resolve_path(reference.get("coverage_path"), run_root)
    if (
        registered_path is None
        or not registered_path.exists()
        or coverage_path is None
        or not coverage_path.exists()
        or reference_path is None
        or not reference_path.exists()
        or reference_coverage_path is None
        or not reference_coverage_path.exists()
    ):
        return {
            "verified": False,
            "status": "missing_artifact",
            "passed": False,
            "reference_frame_id": reference.get("frame_id"),
            "failed_checks": ["registered_or_coverage_missing"],
        }
    try:
        with (
            FitsImageReader(registered_path) as source_reader,
            FitsImageReader(coverage_path) as source_coverage_reader,
            FitsImageReader(reference_path) as reference_reader,
            FitsImageReader(reference_coverage_path) as reference_coverage_reader,
        ):
            shapes = {
                "source": source_reader.shape,
                "source_coverage": source_coverage_reader.shape,
                "reference": reference_reader.shape,
                "reference_coverage": reference_coverage_reader.shape,
            }
            if len(set(shapes.values())) != 1:
                return {
                    "verified": False,
                    "status": "shape_mismatch",
                    "passed": False,
                    "reference_frame_id": reference.get("frame_id"),
                    "shapes": {key: list(value) for key, value in shapes.items()},
                    "failed_checks": ["registered_coverage_reference_shape_match"],
                }
            width = int(source_reader.width)
            height = int(source_reader.height)
            common_valid_pixels = 0
            sum_diff = 0.0
            sum_abs = 0.0
            sum_sq = 0.0
            max_abs_observed = 0.0
            for tile in iter_tiles(width=width, height=height, tile_size=max(1, int(tile_size))):
                source = source_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                reference_tile = reference_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                source_coverage = source_coverage_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                reference_coverage = reference_coverage_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                valid = (
                    np.isfinite(source)
                    & np.isfinite(reference_tile)
                    & np.isfinite(source_coverage)
                    & np.isfinite(reference_coverage)
                    & (source_coverage > 0.5)
                    & (reference_coverage > 0.5)
                )
                if not np.any(valid):
                    continue
                diff = np.asarray(source[valid] - reference_tile[valid], dtype=np.float64)
                abs_diff = np.abs(diff)
                common_valid_pixels += int(diff.size)
                sum_diff += float(np.sum(diff))
                sum_abs += float(np.sum(abs_diff))
                sum_sq += float(np.sum(diff * diff))
                max_abs_observed = max(max_abs_observed, float(np.max(abs_diff)))
    except Exception as exc:
        return {
            "verified": False,
            "status": "read_failed",
            "passed": False,
            "reference_frame_id": reference.get("frame_id"),
            "error": str(exc),
            "failed_checks": ["science_residual_read"],
        }

    failed_checks: list[str] = []
    if common_valid_pixels <= 0:
        failed_checks.append("common_valid_pixels_present")
        mean = None
        mean_abs = None
        rms = None
        max_abs_observed_value = None
    else:
        mean = sum_diff / float(common_valid_pixels)
        mean_abs = sum_abs / float(common_valid_pixels)
        rms = float(np.sqrt(sum_sq / float(common_valid_pixels)))
        max_abs_observed_value = max_abs_observed
        if max_rms is not None and rms > float(max_rms):
            failed_checks.append("science_residual_rms_within_threshold")
        if max_abs is not None and max_abs_observed > float(max_abs):
            failed_checks.append("science_residual_max_abs_within_threshold")
    return {
        "verified": True,
        "status": "passed" if not failed_checks else "failed",
        "passed": not failed_checks,
        "reference_frame_id": reference.get("frame_id"),
        "tile_size": max(1, int(tile_size)),
        "common_valid_pixels": common_valid_pixels,
        "mean": mean,
        "mean_abs": mean_abs,
        "rms": rms,
        "max_abs": max_abs_observed_value,
        "max_rms_threshold": max_rms,
        "max_abs_threshold": max_abs,
        "failed_checks": failed_checks,
    }


def _attach_science_residuals(
    rows: list[dict[str, Any]],
    run_root: Path,
    *,
    reference_frame_id: str | None,
    tile_size: int,
    max_rms: float | None,
    max_abs: float | None,
) -> dict[str, Any]:
    reference = _reference_row(rows, reference_frame_id)
    if reference is None:
        return {
            "reference_frame_id": reference_frame_id,
            "verified_count": 0,
            "failed_count": 0,
            "max_rms": None,
            "max_abs": None,
            "failed_rows": [],
        }
    residuals: list[dict[str, Any]] = []
    for row in rows:
        residual = _science_residual(
            row,
            reference,
            run_root,
            tile_size=tile_size,
            max_rms=max_rms,
            max_abs=max_abs,
        )
        row["science_residual"] = residual
        if not residual.get("passed"):
            row["failed_checks"].append("science_residual_passed")
        residuals.append(residual)
    verified = [item for item in residuals if item.get("verified")]
    failed = [row for row in rows if isinstance(row.get("science_residual"), dict) and not row["science_residual"].get("passed")]
    rms_values = [
        float(item["rms"])
        for item in residuals
        if item.get("rms") is not None
    ]
    max_abs_values = [
        float(item["max_abs"])
        for item in residuals
        if item.get("max_abs") is not None
    ]
    return {
        "reference_frame_id": reference.get("frame_id"),
        "verified_count": len(verified),
        "failed_count": len(failed),
        "max_rms": max(rms_values) if rms_values else None,
        "max_abs": max(max_abs_values) if max_abs_values else None,
        "failed_rows": failed,
    }


def _row_accepted_registration(item: dict[str, Any]) -> bool:
    validation = item.get("registration_validation") if isinstance(item.get("registration_validation"), dict) else {}
    if "accepted" in validation:
        return bool(validation.get("accepted"))
    return str(item.get("status") or "").lower() in {"reference", "registered", "aligned", "ok"}


def _registration_result_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if not isinstance(rows, list):
        rows = payload.get("results")
    return [item for item in rows or [] if isinstance(item, dict)]


def _accepted_registration_frame_ids(run_root: Path) -> set[str] | None:
    payload = _read_json_object(run_root / "registration_results.json")
    if payload is None:
        return None
    frame_ids: set[str] = set()
    for item in _registration_result_rows(payload):
        if isinstance(item, dict) and _row_accepted_registration(item) and item.get("frame_id") is not None:
            frame_ids.add(str(item["frame_id"]))
    return frame_ids


def _resident_artifact_payload(run_root: Path) -> dict[str, Any] | None:
    payload = _read_json_object(run_root / "resident_artifacts.json")
    if payload is None:
        return None
    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), list) else []
    artifact_rows = [item for item in artifacts if isinstance(item, dict)]
    if not artifact_rows:
        return None
    if payload.get("backend") == "cuda_resident_stack":
        return payload
    for artifact in artifact_rows:
        if artifact.get("backend") == "cuda_resident_stack":
            return payload
        if isinstance(artifact.get("dq_coverage_provenance"), dict):
            return payload
        if isinstance(artifact.get("resident_registration"), dict):
            return payload
    return None


def _resident_frame_mask_rows(run_root: Path) -> list[dict[str, Any]]:
    payload = _read_json_object(run_root / "resident_frame_masks.json") or {}
    rows: list[dict[str, Any]] = []
    for group in payload.get("groups") or []:
        if not isinstance(group, dict):
            continue
        for row in group.get("rows") or []:
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _resident_registration_quality_decisions(run_root: Path) -> list[dict[str, Any]]:
    payload = _read_json_object(run_root / "resident_registration_quality.json") or {}
    return [item for item in payload.get("decisions") or [] if isinstance(item, dict)]


def _resident_frame_accounting_rows(run_root: Path) -> list[dict[str, Any]]:
    payload = _read_json_object(run_root / "frame_accounting.json") or {}
    return [item for item in payload.get("frames") or [] if isinstance(item, dict)]


def _resident_warp_quality_contract(
    run_root: Path,
    *,
    min_valid_fraction: float | None,
    max_skipped_frames: int | None,
    require_artifacts: bool,
    require_all_registered: bool,
    pixel_verify: bool,
    thresholds: dict[str, Any],
    created_at: str,
) -> dict[str, Any] | None:
    resident_payload = _resident_artifact_payload(run_root)
    registration_payload = _read_json_object(run_root / "registration_results.json")
    if resident_payload is None or registration_payload is None:
        return None

    registration_rows = _registration_result_rows(registration_payload)
    registration_by_id = {str(row.get("frame_id")): row for row in registration_rows if row.get("frame_id") is not None}
    quality_rows = _resident_registration_quality_decisions(run_root)
    quality_by_id = {str(row.get("frame_id")): row for row in quality_rows if row.get("frame_id") is not None}
    mask_rows = _resident_frame_mask_rows(run_root)
    mask_by_id = {str(row.get("frame_id")): row for row in mask_rows if row.get("frame_id") is not None}
    accounting_rows = _resident_frame_accounting_rows(run_root)
    accounting_by_id = {str(row.get("frame_id")): row for row in accounting_rows if row.get("frame_id") is not None}

    active_ids = sorted(
        frame_id
        for frame_id, row in mask_by_id.items()
        if str(row.get("mask_status") or "").lower() == "active"
    )
    if not active_ids:
        active_ids = sorted(
            frame_id
            for frame_id, row in accounting_by_id.items()
            if str(row.get("integration_status") or "").lower() == "used"
            and str(row.get("warp_status") or "").lower() == "resident_in_vram"
        )
    masked_ids = sorted(
        frame_id
        for frame_id, row in mask_by_id.items()
        if str(row.get("mask_status") or "").lower() == "masked"
    )
    if not masked_ids:
        masked_ids = sorted(
            frame_id
            for frame_id, row in accounting_by_id.items()
            if str(row.get("integration_status") or "").lower() == "zero_weight"
        )

    accepted_quality_ids = sorted(
        frame_id
        for frame_id, row in quality_by_id.items()
        if bool(row.get("accepted"))
        and str(row.get("final_status") or "").lower() in {"ok", "reference"}
    )
    accepted_registration_ids = sorted(
        frame_id
        for frame_id, row in registration_by_id.items()
        if _row_accepted_registration(row)
    )
    expected_active_ids = accepted_quality_ids or accepted_registration_ids
    missing_active_ids = sorted(set(expected_active_ids) - set(active_ids)) if expected_active_ids else []
    extra_active_ids = sorted(set(active_ids) - set(expected_active_ids)) if expected_active_ids else []

    artifact_rows = [item for item in resident_payload.get("artifacts") or [] if isinstance(item, dict)]
    first_artifact = artifact_rows[0] if artifact_rows else {}
    provenance = (
        first_artifact.get("dq_coverage_provenance")
        if isinstance(first_artifact.get("dq_coverage_provenance"), dict)
        else {}
    )
    geometric = (
        provenance.get("geometric_warp_coverage")
        if isinstance(provenance.get("geometric_warp_coverage"), dict)
        else {}
    )
    total_pixels = _positive_int(geometric.get("total_pixels"))
    geometric_full = _nonnegative_int(provenance.get("geometric_full_pixels"))
    resident_valid_fraction = (
        None
        if total_pixels is None or total_pixels <= 0 or geometric_full is None
        else float(geometric_full) / float(total_pixels)
    )
    geometric_frame_count = _nonnegative_int(provenance.get("geometric_warp_coverage_frame_count"))
    active_frame_count = _nonnegative_int(provenance.get("active_frame_count"))
    map_paths = {
        "master": first_artifact.get("master_path"),
        "weight": first_artifact.get("weight_map_path"),
        "coverage": first_artifact.get("coverage_map_path"),
        "dq": first_artifact.get("dq_map_path"),
        "low_rejection": first_artifact.get("low_rejection_map_path"),
        "high_rejection": first_artifact.get("high_rejection_map_path"),
    }
    map_exists = {name: _path_exists(path, run_root) for name, path in map_paths.items()}

    rows: list[dict[str, Any]] = []
    for frame_id in active_ids:
        registration = registration_by_id.get(frame_id, {})
        quality = quality_by_id.get(frame_id, {})
        mask = mask_by_id.get(frame_id, {})
        accounting = accounting_by_id.get(frame_id, {})
        failed_checks: list[str] = []
        if not registration:
            failed_checks.append("registration_row_present")
        if str(accounting.get("warp_status") or mask.get("warp_status") or "resident_in_vram") != "resident_in_vram":
            failed_checks.append("warp_status_resident_in_vram")
        if str(mask.get("mask_status") or "active") != "active":
            failed_checks.append("frame_mask_active")
        if quality and not bool(quality.get("accepted")):
            failed_checks.append("registration_quality_accepted")
        rows.append(
            {
                "frame_id": frame_id,
                "resident": True,
                "resident_surface": "resident_in_vram",
                "registration_status": registration.get("status") or accounting.get("registration_status"),
                "registration_quality_status": quality.get("decision_status"),
                "frame_mask_status": mask.get("mask_status"),
                "warp_model": registration.get("transform_model"),
                "interpolation": first_artifact.get("warp_interpolation") or first_artifact.get("interpolation"),
                "tile_size": first_artifact.get("tile_size"),
                "tile_count": None,
                "valid_pixels": None,
                "pixel_count": total_pixels,
                "valid_fraction": resident_valid_fraction,
                "registered_path": None,
                "coverage_path": map_paths.get("coverage"),
                "dq_mask_path": map_paths.get("dq"),
                "registered_path_exists": False,
                "coverage_path_exists": map_exists.get("coverage"),
                "dq_mask_path_exists": map_exists.get("dq"),
                "dq_summary_present": isinstance(first_artifact.get("dq_summary"), dict),
                "dq_summary_has_valid": "valid" in (first_artifact.get("dq_summary") or {}),
                "artifact_ready": bool(map_exists.get("coverage")) and bool(map_exists.get("dq")),
                "pixel_verification": {
                    "verified": False,
                    "status": "resident_surface_not_per_frame",
                    "passed": not pixel_verify,
                    "reason": "resident warp is accumulated in VRAM and audited through integration DQ/pixel-closure contracts",
                }
                if pixel_verify
                else None,
                "passed": not failed_checks,
                "failed_checks": failed_checks,
            }
        )

    skipped_rows: list[dict[str, Any]] = []
    for frame_id in masked_ids:
        accounting = accounting_by_id.get(frame_id, {})
        quality = quality_by_id.get(frame_id, {})
        reasons = accounting.get("resident_frame_mask_reasons") or accounting.get("reasons") or quality.get("reasons") or []
        reason = "; ".join(str(item) for item in reasons) if reasons else "resident frame mask excluded frame"
        failed_checks: list[str] = []
        if not frame_id:
            failed_checks.append("frame_id_present")
        if not reason:
            failed_checks.append("reason_present")
        skipped_rows.append(
            {
                "frame_id": frame_id,
                "status": accounting.get("registration_status") or quality.get("final_status") or "masked",
                "reason": reason,
                "warnings": accounting.get("warnings") or [],
                "passed": not failed_checks,
                "failed_checks": failed_checks,
            }
        )

    artifact_failures: list[str] = []
    if require_artifacts:
        artifact_failures = [name for name, exists in map_exists.items() if not exists and name in {"coverage", "dq"}]
    valid_fraction_failed = min_valid_fraction is not None and (
        resident_valid_fraction is None or resident_valid_fraction < float(min_valid_fraction)
    )
    skipped_failed = max_skipped_frames is not None and len(skipped_rows) > int(max_skipped_frames)
    all_registered_failed = bool(require_all_registered) and bool(missing_active_ids or extra_active_ids)
    provenance_failed = (
        geometric_frame_count is None
        or active_frame_count is None
        or geometric_frame_count != len(active_ids)
        or active_frame_count != len(active_ids)
    )
    pixel_failed = bool(pixel_verify)

    checks = [
        _check(
            "resident_warp_surface_present",
            True,
            {
                "resident_artifacts": str(run_root / "resident_artifacts.json"),
                "registration_results": str(run_root / "registration_results.json"),
            },
        ),
        _check(
            "resident_warp_outputs_present",
            bool(active_ids),
            {"output_count": len(active_ids)},
        ),
        _check(
            "resident_warp_skipped_rows_have_reasons",
            all(row["passed"] for row in skipped_rows),
            {"failed": [row["frame_id"] for row in skipped_rows if not row["passed"]]},
        ),
        _check(
            "resident_warp_frame_masks_close",
            len(active_ids) + len(masked_ids) == len(mask_rows) and bool(mask_rows),
            {
                "active_count": len(active_ids),
                "masked_count": len(masked_ids),
                "frame_mask_rows": len(mask_rows),
            },
        ),
        _check(
            "resident_warp_geometric_coverage_closes",
            not provenance_failed,
            {
                "active_frame_count": len(active_ids),
                "provenance_active_frame_count": active_frame_count,
                "geometric_warp_coverage_frame_count": geometric_frame_count,
            },
        ),
    ]
    if require_artifacts:
        checks.append(
            _check(
                "resident_warp_output_maps_ready",
                not artifact_failures,
                {"map_exists": map_exists, "failed": artifact_failures},
            )
        )
    if min_valid_fraction is not None:
        checks.append(
            _check(
                "resident_warp_valid_fraction_meets_threshold",
                not valid_fraction_failed,
                {
                    "observed_valid_fraction": resident_valid_fraction,
                    "min_valid_fraction": min_valid_fraction,
                    "geometric_full_pixels": geometric_full,
                    "total_pixels": total_pixels,
                },
            )
        )
    if max_skipped_frames is not None:
        checks.append(
            _check(
                "resident_warp_skipped_frames_within_threshold",
                not skipped_failed,
                {"skipped_count": len(skipped_rows), "max_skipped_frames": max_skipped_frames},
            )
        )
    if require_all_registered:
        checks.append(
            _check(
                "resident_all_accepted_registration_frames_warped",
                not all_registered_failed,
                {
                    "accepted_registration_count": len(expected_active_ids),
                    "active_warp_count": len(active_ids),
                    "missing": missing_active_ids,
                    "extra": extra_active_ids,
                },
            )
        )
    if pixel_verify:
        checks.append(
            _check(
                "resident_warp_pixel_verification_not_supported",
                False,
                {
                    "reason": "resident warp has no per-frame registered/coverage/DQ cache; use pipeline-contract pixel verification",
                },
            )
        )

    failed_outputs = [row for row in rows if row["failed_checks"]]
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "artifact_type": "warp_quality_contract",
        "contract_surface": "resident_in_vram",
        "created_at": created_at,
        "run_dir": str(run_root),
        "warp_path": str(run_root / "warp_results.json"),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "required": True,
        "thresholds": thresholds,
        "summary": {
            "output_count": len(rows),
            "skipped_count": len(skipped_rows),
            "artifact_ready_count": sum(1 for row in rows if row["artifact_ready"]),
            "failed_output_count": len(failed_outputs),
            "min_valid_fraction": resident_valid_fraction,
            "max_valid_fraction": resident_valid_fraction,
            "total_valid_pixels": geometric_full,
            "accepted_registration_count": len(expected_active_ids),
            "missing_warp_for_accepted_registration_count": len(missing_active_ids),
            "resident_active_frame_count": len(active_ids),
            "resident_masked_frame_count": len(masked_ids),
            "geometric_warp_coverage_frame_count": geometric_frame_count,
            "pixel_verify": bool(pixel_verify),
            "pixel_verified_output_count": 0,
            "pixel_failed_output_count": len(rows) if pixel_verify else 0,
            "pixel_max_delta": None,
            "science_residual_verify": False,
            "science_residual_reference_frame_id": None,
            "science_residual_verified_output_count": 0,
            "science_residual_failed_output_count": 0,
            "science_residual_max_rms": None,
            "science_residual_max_abs": None,
            "registration_mode": (quality_rows[0].get("registration_mode") if quality_rows else None),
            "reference_frame_id": registration_payload.get("reference_frame_id"),
            "reference_selection_source": registration_payload.get("reference_selection_source"),
            "map_paths": map_paths,
            "map_exists": map_exists,
        },
        "checks": checks,
        "outputs": rows,
        "skipped_frames": skipped_rows,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "failed_outputs": failed_outputs,
        "missing_warp_for_accepted_registration": missing_active_ids,
    }


def _warp_output_rows(
    payload: dict[str, Any],
    run_root: Path,
    *,
    min_valid_fraction: float | None,
    require_artifacts: bool,
    pixel_verify: bool,
    pixel_verify_tile_size: int,
    pixel_tolerance: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("warp_results") or []:
        if not isinstance(item, dict):
            continue
        registered_exists = _path_exists(item.get("registered_path"), run_root)
        coverage_exists = _path_exists(item.get("coverage_path"), run_root)
        dq_exists = _path_exists(item.get("dq_mask_path"), run_root)
        shape = _image_shape(item.get("registered_path"), run_root) or _image_shape(item.get("coverage_path"), run_root)
        pixel_count = None if shape is None else int(shape[0]) * int(shape[1])
        valid_pixels = _nonnegative_int(item.get("valid_pixels"))
        valid_fraction = (
            None
            if pixel_count is None or pixel_count <= 0 or valid_pixels is None
            else float(valid_pixels) / float(pixel_count)
        )
        dq_summary = item.get("dq_summary") if isinstance(item.get("dq_summary"), dict) else None
        failed_checks: list[str] = []
        if not item.get("frame_id"):
            failed_checks.append("frame_id_present")
        if require_artifacts and not registered_exists:
            failed_checks.append("registered_path_exists")
        if require_artifacts and not coverage_exists:
            failed_checks.append("coverage_path_exists")
        if require_artifacts and not dq_exists:
            failed_checks.append("dq_mask_path_exists")
        if require_artifacts and not (isinstance(dq_summary, dict) and "valid" in dq_summary):
            failed_checks.append("dq_summary_has_valid")
        if _positive_int(item.get("tile_count")) is None:
            failed_checks.append("tile_count_positive")
        if valid_pixels is None:
            failed_checks.append("valid_pixels_nonnegative")
        if pixel_count is not None and valid_pixels is not None and valid_pixels > pixel_count:
            failed_checks.append("valid_pixels_not_above_image_pixels")
        if min_valid_fraction is not None and (
            valid_fraction is None or valid_fraction < float(min_valid_fraction)
        ):
            failed_checks.append("valid_fraction_meets_threshold")
        pixel_verification = (
            _pixel_verification(
                item,
                run_root,
                tile_size=pixel_verify_tile_size,
                tolerance=pixel_tolerance,
            )
            if pixel_verify
            else None
        )
        if pixel_verify and (not isinstance(pixel_verification, dict) or not pixel_verification.get("passed")):
            failed_checks.append("pixel_verification_passed")
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "registration_status": item.get("registration_status"),
                "interpolation": item.get("interpolation"),
                "warp_model": item.get("warp_model"),
                "tile_size": item.get("tile_size"),
                "tile_count": item.get("tile_count"),
                "valid_pixels": valid_pixels,
                "pixel_count": pixel_count,
                "valid_fraction": valid_fraction,
                "registered_path": item.get("registered_path"),
                "coverage_path": item.get("coverage_path"),
                "dq_mask_path": item.get("dq_mask_path"),
                "registered_path_exists": registered_exists,
                "coverage_path_exists": coverage_exists,
                "dq_mask_path_exists": dq_exists,
                "dq_summary_present": isinstance(dq_summary, dict),
                "dq_summary_has_valid": isinstance(dq_summary, dict) and "valid" in dq_summary,
                "artifact_ready": (
                    registered_exists
                    and coverage_exists
                    and dq_exists
                    and isinstance(dq_summary, dict)
                    and "valid" in dq_summary
                ),
                "pixel_verification": pixel_verification,
                "passed": not failed_checks,
                "failed_checks": failed_checks,
            }
        )
    return rows


def _skipped_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in payload.get("skipped_frames") or []:
        if not isinstance(item, dict):
            continue
        failed_checks: list[str] = []
        if not item.get("frame_id"):
            failed_checks.append("frame_id_present")
        if not item.get("status"):
            failed_checks.append("status_present")
        if not item.get("reason"):
            failed_checks.append("reason_present")
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "warnings": item.get("warnings") or [],
                "passed": not failed_checks,
                "failed_checks": failed_checks,
            }
        )
    return rows


def build_warp_quality_contract(
    run_dir: str | Path,
    *,
    min_valid_fraction: float | None = None,
    max_skipped_frames: int | None = None,
    require_artifacts: bool = False,
    require_all_registered: bool = False,
    pixel_verify: bool = False,
    pixel_verify_tile_size: int = 2048,
    pixel_tolerance: int = 0,
    science_residual_verify: bool = False,
    science_reference_frame_id: str | None = None,
    max_science_rms: float | None = None,
    max_science_max_abs: float | None = None,
    science_residual_tile_size: int = 2048,
) -> dict[str, Any]:
    run_root = Path(run_dir)
    warp_path = run_root / "warp_results.json"
    payload = _read_json_object(warp_path)
    required = (
        min_valid_fraction is not None
        or max_skipped_frames is not None
        or bool(require_artifacts)
        or bool(require_all_registered)
        or bool(pixel_verify)
        or bool(science_residual_verify)
        or max_science_rms is not None
        or max_science_max_abs is not None
    )
    science_residual_required = (
        bool(science_residual_verify)
        or max_science_rms is not None
        or max_science_max_abs is not None
    )
    created_at = now_iso()
    thresholds = {
        "min_valid_fraction": min_valid_fraction,
        "max_skipped_frames": max_skipped_frames,
        "require_artifacts": bool(require_artifacts),
        "require_all_registered": bool(require_all_registered),
        "pixel_verify": bool(pixel_verify),
        "pixel_verify_tile_size": max(1, int(pixel_verify_tile_size)),
        "pixel_tolerance": max(0, int(pixel_tolerance)),
        "science_residual_verify": bool(science_residual_required),
        "science_reference_frame_id": science_reference_frame_id,
        "max_science_rms": max_science_rms,
        "max_science_max_abs": max_science_max_abs,
        "science_residual_tile_size": max(1, int(science_residual_tile_size)),
    }
    if payload is None:
        resident_contract = _resident_warp_quality_contract(
            run_root,
            min_valid_fraction=min_valid_fraction,
            max_skipped_frames=max_skipped_frames,
            require_artifacts=require_artifacts,
            require_all_registered=require_all_registered,
            pixel_verify=pixel_verify,
            thresholds=thresholds,
            created_at=created_at,
        )
        if resident_contract is not None:
            return resident_contract
        checks = [
            _check(
                "warp_results_present",
                not required,
                {"path": str(warp_path), "exists": warp_path.exists(), "required": required},
            )
        ]
        return {
            "schema_version": 1,
            "artifact_type": "warp_quality_contract",
            "contract_surface": "warp_results_json",
            "created_at": created_at,
            "run_dir": str(run_root),
            "warp_path": str(warp_path),
            "status": "passed" if not required else "failed",
            "passed": not required,
            "required": required,
            "thresholds": thresholds,
            "summary": {
                "output_count": 0,
                "skipped_count": 0,
                "artifact_ready_count": 0,
                "min_valid_fraction": None,
                "accepted_registration_count": None,
                "missing_warp_for_accepted_registration_count": None,
                "science_residual_verify": bool(science_residual_required),
                "science_residual_verified_output_count": 0,
                "science_residual_failed_output_count": 0,
                "science_residual_max_rms": None,
                "science_residual_max_abs": None,
            },
            "checks": checks,
            "outputs": [],
            "skipped_frames": [],
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
            "failed_outputs": [],
        }

    rows = _warp_output_rows(
        payload,
        run_root,
        min_valid_fraction=min_valid_fraction,
        require_artifacts=require_artifacts,
        pixel_verify=pixel_verify,
        pixel_verify_tile_size=max(1, int(pixel_verify_tile_size)),
        pixel_tolerance=max(0, int(pixel_tolerance)),
    )
    skipped = _skipped_rows(payload)
    artifact_failures = [row for row in rows if require_artifacts and not row["artifact_ready"]]
    valid_fraction_failures = [
        row
        for row in rows
        if min_valid_fraction is not None
        and (row["valid_fraction"] is None or row["valid_fraction"] < float(min_valid_fraction))
    ]
    skipped_contract_failures = [row for row in skipped if not row["passed"]]
    science_residual_state = (
        _attach_science_residuals(
            rows,
            run_root,
            reference_frame_id=science_reference_frame_id,
            tile_size=max(1, int(science_residual_tile_size)),
            max_rms=max_science_rms,
            max_abs=max_science_max_abs,
        )
        if science_residual_required
        else {
            "reference_frame_id": None,
            "verified_count": 0,
            "failed_count": 0,
            "max_rms": None,
            "max_abs": None,
            "failed_rows": [],
        }
    )
    pixel_failures = [
        row
        for row in rows
        if pixel_verify
        and (
            not isinstance(row.get("pixel_verification"), dict)
            or not row["pixel_verification"].get("passed")
        )
    ]
    accepted_registration_ids = _accepted_registration_frame_ids(run_root)
    output_ids = {str(row["frame_id"]) for row in rows if row.get("frame_id") is not None}
    missing_registered_ids = (
        None
        if accepted_registration_ids is None
        else sorted(frame_id for frame_id in accepted_registration_ids if frame_id not in output_ids)
    )
    valid_fractions = [row["valid_fraction"] for row in rows if row["valid_fraction"] is not None]
    checks = [
        _check("warp_results_present", True, {"path": str(warp_path), "required": required}),
        _check("warp_outputs_present", bool(rows), {"output_count": len(rows)}),
        _check(
            "skipped_warp_rows_have_reasons",
            not skipped_contract_failures,
            {"failed": [row["frame_id"] for row in skipped_contract_failures]},
        ),
    ]
    if require_artifacts:
        checks.append(
            _check(
                "warp_output_artifacts_ready",
                bool(rows) and not artifact_failures,
                {"failed": [row["frame_id"] for row in artifact_failures]},
            )
        )
    if min_valid_fraction is not None:
        checks.append(
            _check(
                "warp_valid_fraction_meets_threshold",
                bool(rows) and not valid_fraction_failures,
                {
                    "min_observed_valid_fraction": min(valid_fractions) if valid_fractions else None,
                    "min_valid_fraction": min_valid_fraction,
                    "failed": [row["frame_id"] for row in valid_fraction_failures],
                },
            )
        )
    if max_skipped_frames is not None:
        checks.append(
            _check(
                "warp_skipped_frames_within_threshold",
                len(skipped) <= int(max_skipped_frames),
                {"skipped_count": len(skipped), "max_skipped_frames": max_skipped_frames},
            )
        )
    if require_all_registered:
        checks.append(
            _check(
                "all_accepted_registration_frames_warped",
                accepted_registration_ids is not None and not missing_registered_ids,
                {
                    "accepted_registration_count": None
                    if accepted_registration_ids is None
                    else len(accepted_registration_ids),
                    "missing": missing_registered_ids,
                    "registration_results_present": accepted_registration_ids is not None,
                },
            )
        )
    if pixel_verify:
        checks.append(
            _check(
                "warp_pixel_verification_passed",
                bool(rows) and not pixel_failures,
                {"failed": [row["frame_id"] for row in pixel_failures]},
            )
        )
    if science_residual_required:
        checks.append(
            _check(
                "warp_science_residual_verification_passed",
                bool(rows) and not science_residual_state["failed_rows"],
                {
                    "reference_frame_id": science_residual_state["reference_frame_id"],
                    "verified_count": science_residual_state["verified_count"],
                    "failed": [row["frame_id"] for row in science_residual_state["failed_rows"]],
                    "max_rms": science_residual_state["max_rms"],
                    "max_abs": science_residual_state["max_abs"],
                    "max_rms_threshold": max_science_rms,
                    "max_abs_threshold": max_science_max_abs,
                },
            )
        )
    failed_outputs = [row for row in rows if row["failed_checks"]]
    passed = all(item["passed"] for item in checks)
    pixel_payloads = [
        row["pixel_verification"]
        for row in rows
        if isinstance(row.get("pixel_verification"), dict)
    ]
    pixel_failed_count = len([item for item in pixel_payloads if not item.get("passed")])
    pixel_verified_count = len([item for item in pixel_payloads if item.get("verified")])
    pixel_max_delta = max(
        [int(item.get("max_delta") or 0) for item in pixel_payloads if item.get("max_delta") is not None],
        default=None,
    )
    return {
        "schema_version": 1,
        "artifact_type": "warp_quality_contract",
        "contract_surface": "warp_results_json",
        "created_at": created_at,
        "run_dir": str(run_root),
        "warp_path": str(warp_path),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "required": required,
        "thresholds": thresholds,
        "summary": {
            "output_count": len(rows),
            "skipped_count": len(skipped),
            "artifact_ready_count": sum(1 for row in rows if row["artifact_ready"]),
            "failed_output_count": len(failed_outputs),
            "min_valid_fraction": min(valid_fractions) if valid_fractions else None,
            "max_valid_fraction": max(valid_fractions) if valid_fractions else None,
            "total_valid_pixels": sum(int(row["valid_pixels"] or 0) for row in rows),
            "accepted_registration_count": None
            if accepted_registration_ids is None
            else len(accepted_registration_ids),
            "missing_warp_for_accepted_registration_count": None
            if missing_registered_ids is None
            else len(missing_registered_ids),
            "pixel_verify": bool(pixel_verify),
            "pixel_verified_output_count": pixel_verified_count,
            "pixel_failed_output_count": pixel_failed_count,
            "pixel_max_delta": pixel_max_delta,
            "science_residual_verify": bool(science_residual_required),
            "science_residual_reference_frame_id": science_residual_state["reference_frame_id"],
            "science_residual_verified_output_count": science_residual_state["verified_count"],
            "science_residual_failed_output_count": science_residual_state["failed_count"],
            "science_residual_max_rms": science_residual_state["max_rms"],
            "science_residual_max_abs": science_residual_state["max_abs"],
            "interpolation": payload.get("interpolation"),
            "interpolator_registry": payload.get("interpolator_registry"),
        },
        "checks": checks,
        "outputs": rows,
        "skipped_frames": skipped,
        "failed_checks": [item["name"] for item in checks if not item["passed"]],
        "failed_outputs": failed_outputs,
        "missing_warp_for_accepted_registration": missing_registered_ids,
    }


def write_warp_quality_contract(
    path: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, payload)
    if markdown is None:
        return
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    thresholds = payload.get("thresholds") if isinstance(payload.get("thresholds"), dict) else {}
    lines = [
        "# Warp Quality Contract",
        "",
        f"- Status: {payload.get('status')}",
        f"- Passed: {payload.get('passed')}",
        f"- Required: {payload.get('required')}",
        f"- Contract surface: {payload.get('contract_surface')}",
        f"- Output count: {summary.get('output_count')}",
        f"- Skipped count: {summary.get('skipped_count')}",
        f"- Artifact-ready count: {summary.get('artifact_ready_count')}",
        f"- Resident active frames: {summary.get('resident_active_frame_count')}",
        f"- Resident masked frames: {summary.get('resident_masked_frame_count')}",
        f"- Geometric warp coverage frames: {summary.get('geometric_warp_coverage_frame_count')}",
        f"- Min valid fraction: {summary.get('min_valid_fraction')}",
        f"- Threshold min valid fraction: {thresholds.get('min_valid_fraction')}",
        f"- Max skipped frames: {thresholds.get('max_skipped_frames')}",
        f"- Require artifacts: {thresholds.get('require_artifacts')}",
        f"- Require all registered: {thresholds.get('require_all_registered')}",
        f"- Pixel verify: {thresholds.get('pixel_verify')}",
        f"- Pixel tolerance: {thresholds.get('pixel_tolerance')}",
        f"- Science residual verify: {thresholds.get('science_residual_verify')}",
        f"- Science residual reference: {thresholds.get('science_reference_frame_id')}",
        f"- Max science RMS: {thresholds.get('max_science_rms')}",
        f"- Max science max abs: {thresholds.get('max_science_max_abs')}",
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
            f"- {marker}: {item.get('frame_id')} model={item.get('warp_model')} "
            f"valid_fraction={item.get('valid_fraction')} artifact_ready={item.get('artifact_ready')} "
            f"pixel={item.get('pixel_verification')} science={item.get('science_residual')}"
        )
    if payload.get("skipped_frames"):
        lines.extend(["", "## Skipped Frames", ""])
        for item in payload.get("skipped_frames") or []:
            marker = "PASS" if item.get("passed") else "FAIL"
            lines.append(
                f"- {marker}: {item.get('frame_id')} status={item.get('status')} "
                f"reason={item.get('reason')}"
            )
    Path(markdown).parent.mkdir(parents=True, exist_ok=True)
    Path(markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
