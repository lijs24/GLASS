from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.local_norm import (
    apply_coefficient_fields,
    fill_invalid_coefficient_grid,
    interpolate_coefficient_grid,
    interpolate_coefficient_grid_slice,
)
from glass.cpu.local_norm import estimate_tile_normalization_mean_std
from glass.engine.contracts import DQFlag
from glass.engine.dq import add_summary_counts, dq_header, dq_mask_from_invalid, write_dq_tile
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader, FitsTileWriter, write_fits_data
from glass.io.json_io import read_json, write_json


def _cuda_module_if_requested(backend: str):
    if backend == "cpu":
        return None
    try:
        import glass_cuda
    except Exception:
        return None
    if glass_cuda.cuda_available() and hasattr(glass_cuda, "local_norm_apply_f32"):
        return glass_cuda
    if backend == "cuda":
        raise RuntimeError("CUDA backend requested but local normalization CUDA backend is unavailable")
    return None


def _policy_from_plan(plan_path: str | Path | None) -> dict[str, Any]:
    if plan_path is None:
        return {"enabled": False}
    path = Path(plan_path)
    if not path.exists():
        return {"enabled": False}
    raw = read_json(path).get("local_normalization_policy", {})
    return raw if isinstance(raw, dict) else {"enabled": False}


def _local_norm_enabled(policy: dict[str, Any], enabled_override: bool | None) -> bool:
    if enabled_override is not None:
        return enabled_override
    return bool(policy.get("enabled", False))


def _full_field_map_max_pixels() -> int:
    raw = os.environ.get("GLASS_LN_FULL_FIELD_MAP_MAX_PIXELS")
    if raw is None:
        return 4_000_000
    try:
        return max(0, int(raw))
    except ValueError:
        return 4_000_000


def _write_full_field_maps(height: int, width: int) -> bool:
    return int(height) * int(width) <= _full_field_map_max_pixels()


def _valid_local_norm_mask(
    source_tile: np.ndarray,
    reference_tile: np.ndarray,
    source_coverage: np.ndarray,
    reference_coverage: np.ndarray,
) -> np.ndarray:
    return (
        (np.asarray(source_coverage, dtype=np.float32) > 0.5)
        & (np.asarray(reference_coverage, dtype=np.float32) > 0.5)
        & np.isfinite(source_tile)
        & np.isfinite(reference_tile)
    )


def _estimate_tile_stats(
    source_tile: np.ndarray,
    reference_tile: np.ndarray,
    valid_mask: np.ndarray,
    cuda_module: Any | None,
    eps: float = 1.0e-6,
) -> tuple[dict[str, Any], str]:
    if cuda_module is not None and hasattr(cuda_module, "local_norm_pair_stats_f32"):
        source_for_stats = np.asarray(source_tile, dtype=np.float32).copy()
        reference_for_stats = np.asarray(reference_tile, dtype=np.float32).copy()
        source_for_stats[~valid_mask] = np.nan
        reference_for_stats[~valid_mask] = np.nan
        stats = dict(cuda_module.local_norm_pair_stats_f32(source_for_stats, reference_for_stats))
        valid = int(stats.get("valid_pixels", 0))
        source_mean = stats.get("source_mean")
        reference_mean = stats.get("reference_mean")
        source_std = stats.get("source_std")
        reference_std = stats.get("reference_std")
        if valid == 0 or source_mean is None or reference_mean is None:
            stats.update({"scale": 1.0, "offset": 0.0, "status": "empty", "valid_pixels": valid})
        elif float(source_std or 0.0) <= eps or float(reference_std or 0.0) <= eps:
            stats.update(
                {
                    "scale": 1.0,
                    "offset": float(reference_mean) - float(source_mean),
                    "status": "offset_only",
                    "valid_pixels": valid,
                }
            )
        else:
            scale = float(reference_std) / float(source_std)
            stats.update(
                {
                    "scale": scale,
                    "offset": float(reference_mean) - float(source_mean) * scale,
                    "status": "ok",
                    "valid_pixels": valid,
                }
            )
        return stats, "cuda_stats_cpu_field"
    return (
        estimate_tile_normalization_mean_std(source_tile, reference_tile, valid_mask, eps=eps),
        "cpu_continuous_field",
    )


def _empty_residual_summary() -> dict[str, Any]:
    return {
        "valid_pixels": 0,
        "mean": None,
        "rms": None,
        "max_abs": None,
    }


def _update_residual_accumulator(
    accumulator: dict[str, float],
    normalized_tile: np.ndarray,
    reference_tile: np.ndarray,
    valid_mask: np.ndarray,
) -> None:
    residuals = np.asarray(normalized_tile, dtype=np.float32) - np.asarray(reference_tile, dtype=np.float32)
    mask = np.asarray(valid_mask, dtype=bool) & np.isfinite(residuals)
    if not np.any(mask):
        return
    values = residuals[mask].astype(np.float64)
    abs_values = np.abs(values)
    accumulator["count"] += float(values.size)
    accumulator["sum"] += float(np.sum(values))
    accumulator["sumsq"] += float(np.sum(values * values))
    accumulator["max_abs"] = max(float(accumulator["max_abs"]), float(np.max(abs_values)))


def _finalize_residual_accumulator(accumulator: dict[str, float]) -> dict[str, Any]:
    count = int(accumulator["count"])
    if count == 0:
        return _empty_residual_summary()
    return {
        "valid_pixels": count,
        "mean": float(accumulator["sum"] / count),
        "rms": float(np.sqrt(accumulator["sumsq"] / count)),
        "max_abs": float(accumulator["max_abs"]),
    }


def _disabled_payload(run: Path, policy: dict[str, Any], warp: dict[str, Any], reference_id: str | None) -> dict[str, Any]:
    outputs = []
    for item in warp.get("warp_results", []):
        outputs.append(
            {
                "frame_id": item["frame_id"],
                "input_path": item["registered_path"],
                "normalized_path": item["registered_path"],
                "coverage_path": item["coverage_path"],
                "dq_mask_path": item.get("dq_mask_path"),
                "dq_summary": item.get("dq_summary", {}),
                "coefficient_field_model": "disabled_passthrough",
                "crop_box": None,
                "backend": "passthrough",
                "tile_count": 0,
                "status": "disabled_passthrough",
                "warnings": [],
            }
        )
    return {
        "schema_version": 1,
        "enabled": False,
        "reference_frame_id": reference_id,
        "tile_radius": policy.get("tile_radius", 64),
        "background_mask_policy": policy.get("background_mask_policy", "sigma"),
        "outlier_policy": policy.get("outlier_policy", "clip"),
        "coefficient_field_model": "disabled_passthrough",
        "crop_box": None,
        "local_norm_results": outputs,
        "output_dir": str(run / "registered_cache"),
    }


def local_normalize_registered_frames(
    run_dir: str | Path,
    plan_path: str | Path | None = None,
    backend: str = "auto",
    tile_size: int = 512,
    enabled_override: bool | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    registration = read_json(run / "registration_results.json")
    warp = read_json(run / "warp_results.json")
    policy = _policy_from_plan(plan_path)
    reference_id = registration.get("reference_frame_id")
    if not _local_norm_enabled(policy, enabled_override):
        payload = _disabled_payload(run, policy, warp, reference_id)
        write_json(run / "local_norm_results.json", payload)
        return payload

    by_frame = {item["frame_id"]: item for item in warp.get("warp_results", [])}
    if reference_id not in by_frame:
        raise ValueError("local normalization reference frame is missing from warp results")
    reference = by_frame[reference_id]
    output_dir = run / "local_norm_cache"
    dq_dir = run / "dq_cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    dq_dir.mkdir(parents=True, exist_ok=True)
    cuda_module = _cuda_module_if_requested(backend)
    outputs: list[dict[str, Any]] = []

    with FitsImageReader(reference["registered_path"]) as reference_data, FitsImageReader(
        reference["coverage_path"]
    ) as reference_coverage:
        height, width = reference_data.shape
        grid_rows = int(np.ceil(height / tile_size))
        grid_cols = int(np.ceil(width / tile_size))
        full_field_maps_enabled = _write_full_field_maps(height, width)
        full_field_map_status = "written" if full_field_maps_enabled else "omitted_due_to_size"
        for item in warp.get("warp_results", []):
            frame_id = item["frame_id"]
            out_path = output_dir / f"local_norm_{frame_id}.fits"
            dq_path = dq_dir / f"dq_local_norm_{frame_id}.fits"
            coefficient_path = output_dir / f"local_norm_{frame_id}_coefficients.json"
            scale_field_path = output_dir / f"local_norm_{frame_id}_scale_field.fits"
            offset_field_path = output_dir / f"local_norm_{frame_id}_offset_field.fits"
            residual_map_path = output_dir / f"local_norm_{frame_id}_residual.fits"
            warnings: list[str] = []
            valid_counts: list[int] = []
            scale_grid = np.ones((grid_rows, grid_cols), dtype=np.float32)
            offset_grid = np.zeros((grid_rows, grid_cols), dtype=np.float32)
            valid_grid = np.zeros((grid_rows, grid_cols), dtype=np.int64)
            status_grid: list[list[str]] = [["pending" for _ in range(grid_cols)] for _ in range(grid_rows)]
            with FitsImageReader(item["registered_path"]) as source_data, FitsImageReader(
                item["coverage_path"]
            ) as source_coverage:
                tile_count = 0
                for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                    src_tile = source_data.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    ref_tile = reference_data.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    src_cov = source_coverage.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    ref_cov = reference_coverage.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    valid_mask = _valid_local_norm_mask(src_tile, ref_tile, src_cov, ref_cov)
                    stats, actual_backend = _estimate_tile_stats(src_tile, ref_tile, valid_mask, cuda_module)
                    if stats["status"] == "empty":
                        warnings.append(
                            f"empty normalization tile y={tile.y0}:{tile.y1} x={tile.x0}:{tile.x1}"
                        )
                    scale = float(stats["scale"])
                    offset = float(stats["offset"])
                    grid_y = tile.y0 // tile_size
                    grid_x = tile.x0 // tile_size
                    scale_grid[grid_y, grid_x] = np.float32(scale)
                    offset_grid[grid_y, grid_x] = np.float32(offset)
                    valid_grid[grid_y, grid_x] = int(stats["valid_pixels"])
                    status_grid[grid_y][grid_x] = str(stats["status"])
                    tile_count += 1
                    valid_counts.append(int(stats["valid_pixels"]))

                valid_coefficient_grid = valid_grid > 0
                repaired_scale_grid = fill_invalid_coefficient_grid(scale_grid, valid_coefficient_grid, 1.0)
                repaired_offset_grid = fill_invalid_coefficient_grid(offset_grid, valid_coefficient_grid, 0.0)
                empty_tiles_filled = int(np.count_nonzero(~valid_coefficient_grid))
                if empty_tiles_filled:
                    warnings.append(f"filled {empty_tiles_filled} empty coefficient tiles from nearest valid tile")
                if full_field_maps_enabled:
                    scale_field = interpolate_coefficient_grid(
                        repaired_scale_grid,
                        height,
                        width,
                        tile_size,
                        tile_size,
                    )
                    offset_field = interpolate_coefficient_grid(
                        repaired_offset_grid,
                        height,
                        width,
                        tile_size,
                        tile_size,
                    )
                    write_fits_data(
                        scale_field_path,
                        scale_field,
                        {"IMAGETYP": "ln_scale", "FRAMEID": frame_id},
                    )
                    write_fits_data(
                        offset_field_path,
                        offset_field,
                        {"IMAGETYP": "ln_offset", "FRAMEID": frame_id},
                    )

                residual_accumulator = {"count": 0.0, "sum": 0.0, "sumsq": 0.0, "max_abs": 0.0}
                dq_summary: dict[str, int] = {}
                residual_writer = (
                    FitsTileWriter(
                        residual_map_path,
                        width=width,
                        height=height,
                        header={"IMAGETYP": "ln_resid", "FRAMEID": frame_id},
                    )
                    if full_field_maps_enabled
                    else None
                )
                with FitsTileWriter(
                    out_path,
                    width=width,
                    height=height,
                    header={"IMAGETYP": "local_norm", "FRAMEID": frame_id},
                ) as writer, FitsTileWriter(
                    dq_path,
                    width=width,
                    height=height,
                    header=dq_header("local_norm", frame_id),
                ) as dq_writer:
                    if residual_writer is not None:
                        residual_writer.__enter__()
                    try:
                        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                            src_tile = source_data.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                            ref_tile = reference_data.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                            src_cov = source_coverage.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                            ref_cov = reference_coverage.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                            valid_mask = _valid_local_norm_mask(src_tile, ref_tile, src_cov, ref_cov)
                            scale_tile = interpolate_coefficient_grid_slice(
                                repaired_scale_grid,
                                height,
                                width,
                                tile_size,
                                tile_size,
                                tile.y0,
                                tile.y1,
                                tile.x0,
                                tile.x1,
                            )
                            offset_tile = interpolate_coefficient_grid_slice(
                                repaired_offset_grid,
                                height,
                                width,
                                tile_size,
                                tile_size,
                                tile.y0,
                                tile.y1,
                                tile.x0,
                                tile.x1,
                            )
                            normalized = apply_coefficient_fields(src_tile, scale_tile, offset_tile, valid_mask)
                            writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, normalized)
                            if residual_writer is not None:
                                residual = np.full_like(normalized, np.nan, dtype=np.float32)
                                residual[valid_mask] = normalized[valid_mask] - ref_tile[valid_mask]
                                residual_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, residual)
                            _update_residual_accumulator(
                                residual_accumulator,
                                normalized,
                                ref_tile,
                                valid_mask,
                            )
                            tile_dq = dq_mask_from_invalid(
                                valid_mask.shape,
                                ~valid_mask,
                                DQFlag.LOCAL_NORMALIZATION_EXCLUDED,
                            )
                            write_dq_tile(dq_writer, tile, tile_dq)
                            add_summary_counts(dq_summary, tile_dq.summary())
                    finally:
                        if residual_writer is not None:
                            residual_writer.__exit__(None, None, None)
                residual_summary = _finalize_residual_accumulator(residual_accumulator)
            scale_field_artifact = str(scale_field_path) if full_field_maps_enabled else None
            offset_field_artifact = str(offset_field_path) if full_field_maps_enabled else None
            residual_map_artifact = str(residual_map_path) if full_field_maps_enabled else None
            write_json(
                coefficient_path,
                {
                    "schema_version": 1,
                    "frame_id": frame_id,
                    "reference_frame_id": reference_id,
                    "model": "continuous_grid_mean_std_v1",
                    "coefficient_field_model": "bilinear_tile_center_v1",
                    "interpolation": "bilinear_tile_center",
                    "formula": "output = scale_field * source + offset_field",
                    "tile_size": tile_size,
                    "grid_rows": grid_rows,
                    "grid_cols": grid_cols,
                    "raw_scales": scale_grid.tolist(),
                    "raw_offsets": offset_grid.tolist(),
                    "scales": repaired_scale_grid.tolist(),
                    "offsets": repaired_offset_grid.tolist(),
                    "valid_pixels": valid_grid.tolist(),
                    "statuses": status_grid,
                    "empty_tiles_filled": empty_tiles_filled,
                    "full_field_map_status": full_field_map_status,
                    "scale_field_path": scale_field_artifact,
                    "offset_field_path": offset_field_artifact,
                    "residual_map_path": residual_map_artifact,
                    "residual_summary": residual_summary,
                    "crop_box": None,
                },
            )
            outputs.append(
                {
                    "frame_id": frame_id,
                    "input_path": item["registered_path"],
                    "normalized_path": str(out_path),
                    "coverage_path": item["coverage_path"],
                    "dq_mask_path": str(dq_path),
                    "dq_summary": dq_summary,
                    "coefficient_grid_path": str(coefficient_path),
                    "scale_field_path": scale_field_artifact,
                    "offset_field_path": offset_field_artifact,
                    "residual_map_path": residual_map_artifact,
                    "full_field_map_status": full_field_map_status,
                    "backend": actual_backend,
                    "model": "continuous_grid_mean_std_v1",
                    "coefficient_field_model": "bilinear_tile_center_v1",
                    "interpolation": "bilinear_tile_center",
                    "tile_size": tile_size,
                    "grid_rows": grid_rows,
                    "grid_cols": grid_cols,
                    "tile_count": tile_count,
                    "mean_scale": float(np.mean(repaired_scale_grid)) if repaired_scale_grid.size else 1.0,
                    "mean_offset": float(np.mean(repaired_offset_grid)) if repaired_offset_grid.size else 0.0,
                    "valid_pixels": int(np.sum(valid_counts)) if valid_counts else 0,
                    "empty_tiles_filled": empty_tiles_filled,
                    "residual_summary": residual_summary,
                    "crop_box": None,
                    "status": "reference" if frame_id == reference_id else "ok",
                    "warnings": warnings,
                }
            )

    payload = {
        "schema_version": 1,
        "enabled": True,
        "reference_frame_id": reference_id,
        "reference_path": reference["registered_path"],
        "tile_radius": policy.get("tile_radius", 64),
        "background_mask_policy": policy.get("background_mask_policy", "sigma"),
        "outlier_policy": policy.get("outlier_policy", "clip"),
        "coefficient_field_model": "bilinear_tile_center_v1",
        "model": "continuous_grid_mean_std_v1",
        "full_field_map_max_pixels": _full_field_map_max_pixels(),
        "crop_box": None,
        "local_norm_results": outputs,
        "output_dir": str(output_dir),
    }
    write_json(run / "local_norm_results.json", payload)
    return payload
