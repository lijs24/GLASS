from __future__ import annotations

from typing import Any

import numpy as np

from gpwbpp.cpu.registration import estimate_translation
from gpwbpp_cuda import (
    estimate_similarity_from_catalogs_f32,
    estimate_similarity_from_pairs_f32,
    estimate_translation_from_catalogs_f32,
    estimate_translation_search_f32,
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

__all__ = [
    "estimate_translation",
    "estimate_similarity_from_catalogs_f32",
    "estimate_similarity_from_pairs_f32",
    "estimate_translation_from_catalogs_f32",
    "estimate_translation_search_f32",
    "register_similarity_from_star_catalogs_f32",
    "star_top_nms_candidates_f32",
]
