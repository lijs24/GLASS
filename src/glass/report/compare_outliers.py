from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import write_json
from glass.report.compare_report import _apply_candidate_transform, _read_image_data


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _number_stats(values: np.ndarray) -> dict[str, Any]:
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


def _crop_region(values: np.ndarray, border: int) -> np.ndarray:
    if border < 0:
        raise ValueError("ignore_border_px must be non-negative")
    if border == 0:
        return values
    if border * 2 >= values.shape[0] or border * 2 >= values.shape[1]:
        raise ValueError("ignore_border_px is too large for the image shape")
    return values[border : values.shape[0] - border, border : values.shape[1] - border]


def _top_pixel_rows(
    abs_diff: np.ndarray,
    diff: np.ndarray,
    mask: np.ndarray,
    *,
    border: int,
    limit: int,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    flat_indices = np.flatnonzero(mask)
    if flat_indices.size == 0:
        return []
    flat_abs = np.asarray(abs_diff, dtype=np.float64).ravel()[flat_indices]
    count = min(int(limit), int(flat_indices.size))
    selected_positions = np.argpartition(flat_abs, -count)[-count:]
    selected = flat_indices[selected_positions]
    selected_abs = flat_abs[selected_positions]
    order = np.argsort(selected_abs)[::-1]
    rows: list[dict[str, Any]] = []
    height, width = abs_diff.shape
    for flat_index in selected[order]:
        y_region = int(flat_index // width)
        x_region = int(flat_index % width)
        value = float(diff[y_region, x_region])
        rows.append(
            {
                "x": int(x_region + border),
                "y": int(y_region + border),
                "region_x": x_region,
                "region_y": y_region,
                "abs_diff": float(abs(value)),
                "signed_diff": value,
                "distance_to_region_edge_px": int(
                    min(x_region, y_region, width - 1 - x_region, height - 1 - y_region)
                ),
            }
        )
    return rows


def _tile_rows(
    abs_diff: np.ndarray,
    diff: np.ndarray,
    comparison_mask: np.ndarray,
    tail_mask: np.ndarray,
    *,
    border: int,
    tile_size: int,
    limit: int,
) -> list[dict[str, Any]]:
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")
    height, width = abs_diff.shape
    rows: list[dict[str, Any]] = []
    for y0 in range(0, height, tile_size):
        y1 = min(height, y0 + tile_size)
        for x0 in range(0, width, tile_size):
            x1 = min(width, x0 + tile_size)
            tile_valid = comparison_mask[y0:y1, x0:x1]
            valid_count = int(np.count_nonzero(tile_valid))
            if valid_count == 0:
                continue
            tile_tail = tail_mask[y0:y1, x0:x1]
            tail_count = int(np.count_nonzero(tile_tail))
            if tail_count == 0:
                continue
            tail_abs = abs_diff[y0:y1, x0:x1][tile_tail]
            tail_signed = diff[y0:y1, x0:x1][tile_tail]
            rows.append(
                {
                    "x0": int(x0 + border),
                    "y0": int(y0 + border),
                    "x1": int(x1 + border),
                    "y1": int(y1 + border),
                    "region_x0": int(x0),
                    "region_y0": int(y0),
                    "region_x1": int(x1),
                    "region_y1": int(y1),
                    "valid_pixels": valid_count,
                    "tail_pixels": tail_count,
                    "tail_fraction_of_valid": float(tail_count / valid_count),
                    "tail_abs_mean": float(np.mean(tail_abs)),
                    "tail_abs_max": float(np.max(tail_abs)),
                    "tail_signed_mean": float(np.mean(tail_signed)),
                    "positive_tail_pixels": int(np.count_nonzero(tail_signed > 0)),
                    "negative_tail_pixels": int(np.count_nonzero(tail_signed < 0)),
                }
            )
    rows.sort(
        key=lambda item: (
            int(item["tail_pixels"]),
            float(item["tail_abs_max"]),
            float(item["tail_fraction_of_valid"]),
        ),
        reverse=True,
    )
    return rows[: max(0, int(limit))]


def _outlier_recommendation(
    *,
    tail_pixels: int,
    negative_pixels: int,
    positive_pixels: int,
    edge_fraction: float,
    top_tiles: list[dict[str, Any]],
) -> dict[str, Any]:
    if tail_pixels <= 0:
        return {
            "status": "no_tail_pixels",
            "next_target": "inspect comparison inputs and masks",
        }
    negative_fraction = float(negative_pixels / tail_pixels)
    positive_fraction = float(positive_pixels / tail_pixels)
    top_tile = top_tiles[0] if top_tiles else {}
    top_tile_tail_pixels = int(top_tile.get("tail_pixels") or 0)
    top_tile_share = float(top_tile_tail_pixels / tail_pixels) if tail_pixels else 0.0
    top_tile_local_fraction = float(top_tile.get("tail_fraction_of_valid") or 0.0)
    if edge_fraction >= 0.5:
        status = "edge_dominated_tail"
        next_target = "inspect crop, warp footprint, and coverage edge policy"
    elif top_tile_share >= 0.1 or top_tile_local_fraction >= 0.1:
        status = "localized_tail"
        next_target = "inspect top residual tiles before changing global agreement weighting"
    elif negative_fraction >= 0.95 or positive_fraction >= 0.95:
        status = "signed_global_tail"
        next_target = "inspect normalization or scale offset before registration weighting"
    else:
        status = "diffuse_tail"
        next_target = "compare per-frame contribution and rejection maps across the tail"
    return {
        "status": status,
        "next_target": next_target,
        "negative_fraction": negative_fraction,
        "positive_fraction": positive_fraction,
        "edge_fraction": float(edge_fraction),
        "top_tile_tail_share": top_tile_share,
        "top_tile_local_fraction": top_tile_local_fraction,
    }


def build_compare_outlier_audit(
    glass_path: str | Path,
    reference_path: str | Path,
    *,
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    clip_low: float | None = None,
    clip_high: float | None = None,
    glass_coverage_map: str | Path | None = None,
    min_coverage: float | None = None,
    ignore_border_px: int = 0,
    tail_percentile: float = 99.0,
    target_abs_diff: float | None = None,
    tile_size: int = 512,
    top_tiles: int = 16,
    top_pixels: int = 32,
    edge_band_px: int = 64,
) -> dict[str, Any]:
    if tail_percentile <= 0.0 or tail_percentile >= 100.0:
        raise ValueError("tail_percentile must be between 0 and 100")
    if edge_band_px < 0:
        raise ValueError("edge_band_px must be non-negative")
    if target_abs_diff is not None and target_abs_diff < 0.0:
        raise ValueError("target_abs_diff must be non-negative")

    candidate_raw = _read_image_data(glass_path)
    candidate, transform = _apply_candidate_transform(
        candidate_raw,
        glass_scale,
        glass_offset,
        clip_low,
        clip_high,
    )
    reference = _read_image_data(reference_path)
    if candidate.shape != reference.shape:
        return {
            "schema_version": 1,
            "audit_type": "compare_outlier_audit",
            "passed": False,
            "status": "shape_mismatch",
            "glass": str(glass_path),
            "reference": str(reference_path),
            "glass_shape": [int(item) for item in candidate.shape],
            "reference_shape": [int(item) for item in reference.shape],
            "candidate_transform": transform,
        }

    border = int(ignore_border_px)
    candidate_region = _crop_region(np.asarray(candidate, dtype=np.float32), border)
    reference_region = _crop_region(np.asarray(reference, dtype=np.float32), border)
    comparison_mask = np.isfinite(candidate_region) & np.isfinite(reference_region)
    coverage_region = None
    if glass_coverage_map is not None:
        coverage = _read_image_data(glass_coverage_map)
        if coverage.shape != candidate.shape:
            raise ValueError(f"coverage map shape mismatch: {coverage.shape} != {candidate.shape}")
        coverage_region = _crop_region(np.asarray(coverage, dtype=np.float32), border)
        threshold = 1.0 if min_coverage is None else float(min_coverage)
        comparison_mask &= coverage_region >= np.float32(threshold)

    diff = np.asarray(candidate_region, dtype=np.float64) - np.asarray(reference_region, dtype=np.float64)
    abs_diff = np.abs(diff)
    valid_abs = abs_diff[comparison_mask]
    if valid_abs.size == 0:
        return {
            "schema_version": 1,
            "audit_type": "compare_outlier_audit",
            "passed": False,
            "status": "no_comparable_pixels",
            "glass": str(glass_path),
            "reference": str(reference_path),
            "candidate_transform": transform,
        }

    tail_threshold = float(np.percentile(valid_abs, float(tail_percentile)))
    tail_mask = comparison_mask & (abs_diff >= tail_threshold)
    target_value = _finite_float(target_abs_diff)
    target_mask = comparison_mask & (abs_diff > float(target_value)) if target_value is not None else None
    compared_pixels = int(valid_abs.size)
    tail_pixels = int(np.count_nonzero(tail_mask))
    sign_values = diff[tail_mask]
    tail_y, tail_x = np.nonzero(tail_mask)
    if tail_y.size:
        tail_edge_distances = np.minimum.reduce(
            [
                tail_x,
                tail_y,
                abs_diff.shape[1] - 1 - tail_x,
                abs_diff.shape[0] - 1 - tail_y,
            ]
        )
        tail_edge_pixels = int(np.count_nonzero(tail_edge_distances <= int(edge_band_px)))
    else:
        tail_edge_pixels = 0
    top_tiles_rows = _tile_rows(
        abs_diff,
        diff,
        comparison_mask,
        tail_mask,
        border=border,
        tile_size=int(tile_size),
        limit=int(top_tiles),
    )
    top_pixels_rows = _top_pixel_rows(
        abs_diff,
        diff,
        tail_mask,
        border=border,
        limit=int(top_pixels),
    )
    positive_tail_pixels = int(np.count_nonzero(sign_values > 0))
    negative_tail_pixels = int(np.count_nonzero(sign_values < 0))
    edge_fraction = float(tail_edge_pixels / tail_pixels) if tail_pixels else 0.0
    result: dict[str, Any] = {
        "schema_version": 1,
        "audit_type": "compare_outlier_audit",
        "passed": True,
        "status": "completed",
        "glass": str(glass_path),
        "reference": str(reference_path),
        "coverage_map": None if glass_coverage_map is None else str(glass_coverage_map),
        "candidate_transform": transform,
        "region": {
            "ignore_border_px": border,
            "full_shape": [int(candidate.shape[0]), int(candidate.shape[1])],
            "compared_shape": [int(candidate_region.shape[0]), int(candidate_region.shape[1])],
            "compared_pixels": compared_pixels,
            "coverage_fraction": float(compared_pixels / comparison_mask.size),
            "min_coverage": None if min_coverage is None else float(min_coverage),
            "coverage_stats": None if coverage_region is None else _number_stats(coverage_region[comparison_mask]),
        },
        "tail": {
            "percentile": float(tail_percentile),
            "threshold_abs_diff": tail_threshold,
            "pixels": tail_pixels,
            "fraction_of_compared": float(tail_pixels / compared_pixels),
            "stats": _number_stats(abs_diff[tail_mask]),
            "positive_pixels": positive_tail_pixels,
            "negative_pixels": negative_tail_pixels,
            "edge_band_px": int(edge_band_px),
            "edge_band_pixels": tail_edge_pixels,
            "edge_band_fraction": edge_fraction,
        },
        "target_exceedance": None,
        "recommendation": _outlier_recommendation(
            tail_pixels=tail_pixels,
            negative_pixels=negative_tail_pixels,
            positive_pixels=positive_tail_pixels,
            edge_fraction=edge_fraction,
            top_tiles=top_tiles_rows,
        ),
        "top_tiles": top_tiles_rows,
        "top_pixels": top_pixels_rows,
    }
    if target_mask is not None and target_value is not None:
        target_pixels = int(np.count_nonzero(target_mask))
        target_values = abs_diff[target_mask]
        result["target_exceedance"] = {
            "threshold_abs_diff": float(target_value),
            "pixels": target_pixels,
            "fraction_of_compared": float(target_pixels / compared_pixels),
            "stats": _number_stats(target_values),
            "top_tiles": _tile_rows(
                abs_diff,
                diff,
                comparison_mask,
                target_mask,
                border=border,
                tile_size=int(tile_size),
                limit=int(top_tiles),
            ),
            "top_pixels": _top_pixel_rows(
                abs_diff,
                diff,
                target_mask,
                border=border,
                limit=int(top_pixels),
            ),
        }
    return result


def write_compare_outlier_audit(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    tail = payload.get("tail") if isinstance(payload.get("tail"), dict) else {}
    recommendation = (
        payload.get("recommendation") if isinstance(payload.get("recommendation"), dict) else {}
    )
    target_exceedance = (
        payload.get("target_exceedance") if isinstance(payload.get("target_exceedance"), dict) else None
    )
    lines = [
        "# Compare Outlier Audit",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- GLASS: `{payload.get('glass')}`",
        f"- Reference: `{payload.get('reference')}`",
        f"- Coverage map: `{payload.get('coverage_map')}`",
        f"- Tail percentile: `{tail.get('percentile')}`",
        f"- Tail threshold abs diff: `{tail.get('threshold_abs_diff')}`",
        f"- Tail pixels: `{tail.get('pixels')}`",
        f"- Tail fraction: `{tail.get('fraction_of_compared')}`",
        f"- Tail edge-band fraction: `{tail.get('edge_band_fraction')}`",
        f"- Recommendation status: `{recommendation.get('status')}`",
        f"- Next target: `{recommendation.get('next_target')}`",
        f"- Top tile tail share: `{recommendation.get('top_tile_tail_share')}`",
        "",
    ]
    if target_exceedance is not None:
        lines.extend(
            [
                "## Target Exceedance",
                "",
                f"- Threshold abs diff: `{target_exceedance.get('threshold_abs_diff')}`",
                f"- Pixels: `{target_exceedance.get('pixels')}`",
                f"- Fraction: `{target_exceedance.get('fraction_of_compared')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Top Tail Tiles",
            "",
            "| x0 | y0 | x1 | y1 | tail pixels | tail fraction | max abs | signed mean |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload.get("top_tiles", [])[:16]:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| {row.get('x0')} | {row.get('y0')} | {row.get('x1')} | {row.get('y1')} | "
            f"{row.get('tail_pixels')} | {row.get('tail_fraction_of_valid')} | "
            f"{row.get('tail_abs_max')} | {row.get('tail_signed_mean')} |"
        )
    lines.extend(
        [
            "",
            "## Top Tail Pixels",
            "",
            "| x | y | abs diff | signed diff | edge distance px |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload.get("top_pixels", [])[:32]:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| {row.get('x')} | {row.get('y')} | {row.get('abs_diff')} | "
            f"{row.get('signed_diff')} | {row.get('distance_to_region_edge_px')} |"
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
