from __future__ import annotations

from typing import Any

import numpy as np

from gpwbpp.cpu.registration import estimate_translation
from gpwbpp_cuda import (
    estimate_similarity_from_catalogs_f32,
    estimate_similarity_from_pairs_f32,
    estimate_translation_from_catalogs_f32,
    estimate_translation_search_f32,
    matrix_alignment_metrics_f32,
    star_grid_top_nms_candidates_f32,
    star_grid_candidates_f32,
    star_top_nms_candidates_f32,
    star_top_candidates_f32,
    warp_matrix_bilinear_f32,
)


def register_similarity_from_star_catalogs_f32(
    reference: Any,
    moving: Any,
    threshold: float,
    max_candidates: int = 64,
    tolerance_px: float = 2.0,
    min_pair_distance: float = 4.0,
    fill: float = 0.0,
    grid_cols: int | None = None,
    grid_rows: int | None = None,
    grid_top_candidates_per_cell: int | None = None,
    nms_scan_candidates: int | None = None,
    nms_min_separation_px: float | None = None,
    prior_dx: float | None = None,
    prior_dy: float | None = None,
    prior_radius_px: float | None = None,
    min_scale: float | None = None,
    max_scale: float | None = None,
    max_abs_rotation_rad: float | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Estimate and apply a GPU similarity registration from image catalogs.

    This is a controlled bridge from GPU star detection to GPU transform
    estimation and GPU matrix warp. It is intended for compact catalogs and
    diagnostics while the full descriptor/RANSAC registration model is still
    under construction.
    """

    if (grid_cols is None) != (grid_rows is None):
        raise ValueError("grid_cols and grid_rows must be provided together")
    if grid_cols is not None and grid_rows is not None:
        if grid_top_candidates_per_cell is not None or nms_min_separation_px is not None:
            reference_catalog = star_grid_top_nms_candidates_f32(
                reference,
                threshold,
                int(grid_cols),
                int(grid_rows),
                int(1 if grid_top_candidates_per_cell is None else grid_top_candidates_per_cell),
                int(max_candidates),
                float(32.0 if nms_min_separation_px is None else nms_min_separation_px),
            )
            moving_catalog = star_grid_top_nms_candidates_f32(
                moving,
                threshold,
                int(grid_cols),
                int(grid_rows),
                int(1 if grid_top_candidates_per_cell is None else grid_top_candidates_per_cell),
                int(max_candidates),
                float(32.0 if nms_min_separation_px is None else nms_min_separation_px),
            )
            selector = "grid_top_nms"
        else:
            reference_catalog = star_grid_candidates_f32(reference, threshold, int(grid_cols), int(grid_rows))
            moving_catalog = star_grid_candidates_f32(moving, threshold, int(grid_cols), int(grid_rows))
            selector = "grid"
    else:
        if nms_scan_candidates is not None or nms_min_separation_px is not None:
            reference_catalog = star_top_nms_candidates_f32(
                reference,
                threshold,
                int(max_candidates if nms_scan_candidates is None else nms_scan_candidates),
                int(max_candidates),
                float(32.0 if nms_min_separation_px is None else nms_min_separation_px),
            )
            moving_catalog = star_top_nms_candidates_f32(
                moving,
                threshold,
                int(max_candidates if nms_scan_candidates is None else nms_scan_candidates),
                int(max_candidates),
                float(32.0 if nms_min_separation_px is None else nms_min_separation_px),
            )
            selector = "top_nms"
        else:
            reference_catalog = star_top_candidates_f32(reference, threshold, int(max_candidates))
            moving_catalog = star_top_candidates_f32(moving, threshold, int(max_candidates))
            selector = "top"

    fit = estimate_similarity_from_catalogs_f32(
        reference_catalog["x"],
        reference_catalog["y"],
        moving_catalog["x"],
        moving_catalog["y"],
        tolerance_px=float(tolerance_px),
        min_pair_distance=float(min_pair_distance),
        prior_dx=prior_dx,
        prior_dy=prior_dy,
        prior_radius_px=prior_radius_px,
        min_scale=min_scale,
        max_scale=max_scale,
        max_abs_rotation_rad=max_abs_rotation_rad,
    )
    aligned, coverage = warp_matrix_bilinear_f32(moving, fit["matrix"], float(fill))
    diagnostics = {
        "status": fit["status"],
        "model": "gpu_star_catalog_similarity_registration",
        "catalog_selector": selector,
        "reference_detected": int(reference_catalog["count"]),
        "moving_detected": int(moving_catalog["count"]),
        "reference_stored": int(reference_catalog["stored_count"]),
        "moving_stored": int(moving_catalog["stored_count"]),
        "similarity": fit,
        "matrix": fit["matrix"],
        "coverage_pixels": int(np.sum(coverage > 0.0)),
    }
    return aligned, coverage, diagnostics


def refine_matrix_translation_with_metrics_f32(
    reference: Any,
    moving: Any,
    matrix: Any,
    search_radius_px: float = 1.0,
    coarse_step_px: float = 0.25,
    fine_radius_px: float = 0.25,
    fine_step_px: float = 0.0625,
    coarse_sample_stride: int = 4,
    final_sample_stride: int = 1,
) -> dict[str, Any]:
    """Refine only the translation terms of a matrix with CUDA pixel metrics."""

    if search_radius_px < 0.0:
        raise ValueError("search_radius_px must be non-negative")
    if coarse_step_px <= 0.0:
        raise ValueError("coarse_step_px must be positive")
    if fine_radius_px < 0.0:
        raise ValueError("fine_radius_px must be non-negative")
    if fine_step_px <= 0.0:
        raise ValueError("fine_step_px must be positive")
    if coarse_sample_stride <= 0 or final_sample_stride <= 0:
        raise ValueError("sample strides must be positive")

    base = np.asarray(matrix, dtype=np.float32).reshape(3, 3)

    def score(dx: float, dy: float, stride: int) -> tuple[tuple[float, float], dict[str, Any], np.ndarray]:
        candidate = np.array(base, copy=True)
        candidate[0, 2] += np.float32(dx)
        candidate[1, 2] += np.float32(dy)
        metrics = matrix_alignment_metrics_f32(reference, moving, candidate, sample_stride=int(stride))
        return (float(metrics["rms"]), -float(metrics["ncc"])), metrics, candidate

    coarse_offsets = np.arange(
        -float(search_radius_px),
        float(search_radius_px) + float(coarse_step_px) * 0.5,
        float(coarse_step_px),
        dtype=np.float32,
    )
    best_key: tuple[float, float] | None = None
    best_dx = 0.0
    best_dy = 0.0
    best_metrics: dict[str, Any] | None = None
    best_matrix = np.array(base, copy=True)
    coarse_candidates = 0
    for dx in coarse_offsets:
        for dy in coarse_offsets:
            key, metrics, candidate = score(float(dx), float(dy), coarse_sample_stride)
            coarse_candidates += 1
            if best_key is None or key < best_key:
                best_key = key
                best_dx = float(dx)
                best_dy = float(dy)
                best_metrics = metrics
                best_matrix = candidate

    fine_candidates = 0
    if fine_radius_px > 0.0:
        fine_x = np.arange(
            best_dx - float(fine_radius_px),
            best_dx + float(fine_radius_px) + float(fine_step_px) * 0.5,
            float(fine_step_px),
            dtype=np.float32,
        )
        fine_y = np.arange(
            best_dy - float(fine_radius_px),
            best_dy + float(fine_radius_px) + float(fine_step_px) * 0.5,
            float(fine_step_px),
            dtype=np.float32,
        )
        best_key = None
        for dx in fine_x:
            for dy in fine_y:
                key, metrics, candidate = score(float(dx), float(dy), final_sample_stride)
                fine_candidates += 1
                if best_key is None or key < best_key:
                    best_key = key
                    best_dx = float(dx)
                    best_dy = float(dy)
                    best_metrics = metrics
                    best_matrix = candidate
    elif final_sample_stride != coarse_sample_stride:
        _key, best_metrics, best_matrix = score(best_dx, best_dy, final_sample_stride)

    assert best_metrics is not None
    return {
        "matrix": best_matrix.astype(np.float32).tolist(),
        "dx_correction": best_dx,
        "dy_correction": best_dy,
        "metrics": best_metrics,
        "coarse_candidates": coarse_candidates,
        "fine_candidates": fine_candidates,
        "search_radius_px": float(search_radius_px),
        "coarse_step_px": float(coarse_step_px),
        "fine_radius_px": float(fine_radius_px),
        "fine_step_px": float(fine_step_px),
        "coarse_sample_stride": int(coarse_sample_stride),
        "final_sample_stride": int(final_sample_stride),
        "model": "cuda_matrix_metric_translation_refine",
    }


__all__ = [
    "estimate_translation",
    "estimate_similarity_from_catalogs_f32",
    "estimate_similarity_from_pairs_f32",
    "estimate_translation_from_catalogs_f32",
    "estimate_translation_search_f32",
    "matrix_alignment_metrics_f32",
    "refine_matrix_translation_with_metrics_f32",
    "register_similarity_from_star_catalogs_f32",
    "star_grid_top_nms_candidates_f32",
    "star_top_nms_candidates_f32",
]
