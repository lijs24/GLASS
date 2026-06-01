from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.compare_report import (
    _apply_candidate_transform,
    _gray_preview,
    _read_image_data,
    _signed_diff_preview,
    _write_png_gray,
    _write_png_rgb,
)


def _tile_stats(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {
            "count": 0,
            "min": None,
            "p50": None,
            "p90": None,
            "p99": None,
            "max": None,
            "mean": None,
            "rms": None,
        }
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "p50": float(np.percentile(finite, 50)),
        "p90": float(np.percentile(finite, 90)),
        "p99": float(np.percentile(finite, 99)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "rms": float(np.sqrt(np.mean(finite * finite))),
    }


def _bounded_extent(
    row: dict[str, Any],
    *,
    shape: tuple[int, int],
    pad_px: int,
) -> tuple[int, int, int, int]:
    if pad_px < 0:
        raise ValueError("pad_px must be non-negative")
    height, width = shape
    x0 = max(0, int(row["x0"]) - int(pad_px))
    y0 = max(0, int(row["y0"]) - int(pad_px))
    x1 = min(width, int(row["x1"]) + int(pad_px))
    y1 = min(height, int(row["y1"]) + int(pad_px))
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"invalid tile extent after padding: {row}")
    return x0, y0, x1, y1


def _transform_from_audit(payload: dict[str, Any]) -> dict[str, float | bool | None]:
    transform = payload.get("candidate_transform")
    if not isinstance(transform, dict):
        return {"applied": False, "scale": 1.0, "offset": 0.0, "clip_low": None, "clip_high": None}
    return {
        "applied": bool(transform.get("applied")),
        "scale": float(transform.get("scale", 1.0)),
        "offset": float(transform.get("offset", 0.0)),
        "clip_low": None if transform.get("clip_low") is None else float(transform["clip_low"]),
        "clip_high": None if transform.get("clip_high") is None else float(transform["clip_high"]),
    }


def _write_tile_pngs(
    tile_dir: Path,
    *,
    glass_tile: np.ndarray,
    reference_tile: np.ndarray,
    diff_tile: np.ndarray,
    preview_max_size: int,
) -> dict[str, str]:
    pngs = {
        "glass_png": str(tile_dir / "glass.png"),
        "reference_png": str(tile_dir / "reference.png"),
        "abs_diff_png": str(tile_dir / "abs_diff.png"),
        "signed_diff_png": str(tile_dir / "signed_diff.png"),
    }
    _write_png_gray(tile_dir / "glass.png", _gray_preview(glass_tile, preview_max_size))
    _write_png_gray(tile_dir / "reference.png", _gray_preview(reference_tile, preview_max_size))
    _write_png_gray(tile_dir / "abs_diff.png", _gray_preview(np.abs(diff_tile), preview_max_size, low=0.0, high=99.5))
    _write_png_rgb(tile_dir / "signed_diff.png", _signed_diff_preview(diff_tile, preview_max_size))
    return pngs


def build_compare_tile_pack(
    audit_path: str | Path,
    out_dir: str | Path,
    *,
    max_tiles: int = 4,
    pad_px: int = 0,
    include_png: bool = True,
    preview_max_size: int = 768,
) -> dict[str, Any]:
    if max_tiles <= 0:
        raise ValueError("max_tiles must be positive")
    if preview_max_size <= 0:
        raise ValueError("preview_max_size must be positive")
    audit = read_json(audit_path)
    if audit.get("status") != "completed":
        raise ValueError(f"compare outlier audit is not completed: {audit.get('status')}")
    top_tiles = audit.get("top_tiles")
    if not isinstance(top_tiles, list) or not top_tiles:
        raise ValueError("compare outlier audit has no top_tiles")
    glass_path = audit.get("glass")
    reference_path = audit.get("reference")
    if not glass_path or not reference_path:
        raise ValueError("compare outlier audit is missing image paths")

    transform = _transform_from_audit(audit)
    glass_raw = _read_image_data(glass_path)
    if transform["applied"]:
        scale_arg = float(transform["scale"])
        offset_arg = float(transform["offset"])
        clip_low_arg = None if transform["clip_low"] is None else float(transform["clip_low"])
        clip_high_arg = None if transform["clip_high"] is None else float(transform["clip_high"])
    else:
        scale_arg = None
        offset_arg = None
        clip_low_arg = None
        clip_high_arg = None
    glass_image, applied_transform = _apply_candidate_transform(
        glass_raw,
        scale_arg,
        offset_arg,
        clip_low_arg,
        clip_high_arg,
    )
    reference_image = _read_image_data(reference_path)
    if glass_image.shape != reference_image.shape:
        raise ValueError(f"image shape mismatch: {glass_image.shape} != {reference_image.shape}")

    coverage_path = audit.get("coverage_map")
    coverage_image = None
    if coverage_path:
        coverage_image = _read_image_data(coverage_path)
        if coverage_image.shape != glass_image.shape:
            raise ValueError(f"coverage shape mismatch: {coverage_image.shape} != {glass_image.shape}")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tiles: list[dict[str, Any]] = []
    for index, row_value in enumerate(top_tiles[: int(max_tiles)]):
        if not isinstance(row_value, dict):
            continue
        x0, y0, x1, y1 = _bounded_extent(row_value, shape=glass_image.shape, pad_px=int(pad_px))
        tile_dir = out / f"tile_{index:03d}_x{x0}_y{y0}"
        tile_dir.mkdir(parents=True, exist_ok=True)
        glass_tile = np.asarray(glass_image[y0:y1, x0:x1], dtype=np.float32)
        reference_tile = np.asarray(reference_image[y0:y1, x0:x1], dtype=np.float32)
        diff_tile = np.asarray(glass_tile - reference_tile, dtype=np.float32)
        abs_diff_tile = np.abs(diff_tile)
        header = {"X0": x0, "Y0": y0, "X1": x1, "Y1": y1}
        paths = {
            "glass_fits": str(tile_dir / "glass.fits"),
            "reference_fits": str(tile_dir / "reference.fits"),
            "signed_diff_fits": str(tile_dir / "signed_diff.fits"),
            "abs_diff_fits": str(tile_dir / "abs_diff.fits"),
        }
        write_fits_data(tile_dir / "glass.fits", glass_tile, header=header)
        write_fits_data(tile_dir / "reference.fits", reference_tile, header=header)
        write_fits_data(tile_dir / "signed_diff.fits", diff_tile, header=header)
        write_fits_data(tile_dir / "abs_diff.fits", abs_diff_tile, header=header)
        if coverage_image is not None:
            coverage_tile = np.asarray(coverage_image[y0:y1, x0:x1], dtype=np.float32)
            paths["coverage_fits"] = str(tile_dir / "coverage.fits")
            write_fits_data(tile_dir / "coverage.fits", coverage_tile, header=header)
        if include_png:
            paths.update(
                _write_tile_pngs(
                    tile_dir,
                    glass_tile=glass_tile,
                    reference_tile=reference_tile,
                    diff_tile=diff_tile,
                    preview_max_size=int(preview_max_size),
                )
            )
        tiles.append(
            {
                "index": index,
                "source_top_tile": row_value,
                "extent": {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "pad_px": int(pad_px)},
                "shape": [int(y1 - y0), int(x1 - x0)],
                "paths": paths,
                "signed_diff_stats": _tile_stats(diff_tile),
                "abs_diff_stats": _tile_stats(abs_diff_tile),
            }
        )

    manifest = {
        "schema_version": 1,
        "artifact_type": "compare_tile_pack",
        "audit_path": str(audit_path),
        "out_dir": str(out),
        "glass": str(glass_path),
        "reference": str(reference_path),
        "coverage_map": None if coverage_path is None else str(coverage_path),
        "candidate_transform": applied_transform,
        "max_tiles": int(max_tiles),
        "pad_px": int(pad_px),
        "include_png": bool(include_png),
        "preview_max_size": int(preview_max_size),
        "tile_count": len(tiles),
        "tiles": tiles,
    }
    write_json(out / "tile_pack_manifest.json", manifest)
    return manifest
