from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.registration import (
    estimate_astroalign_transform,
    estimate_star_transform,
    estimate_translation_phase_correlation,
    translation_matrix,
)
from glass.gpu.registration import (
    refine_matrix_translation_candidates_with_metrics_f32,
    refine_matrix_translation_with_metrics_f32,
    register_triangle_descriptor_similarity_f32,
)
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.engine.quality import detect_stars_streaming
from glass.models import RegistrationResult, to_jsonable


def _registration_preview(
    path: str | Path,
    tile_size: int,
    max_dimension: int = 1024,
) -> tuple[np.ndarray, int, int]:
    with FitsImageReader(path) as reader:
        scale = max(1, int(np.ceil(max(reader.width, reader.height) / max_dimension)))
        preview_height = int(np.ceil(reader.height / scale))
        preview_width = int(np.ceil(reader.width / scale))
        sums = np.zeros((preview_height, preview_width), dtype=np.float64)
        counts = np.zeros((preview_height, preview_width), dtype=np.float32)
        tile_count = 0
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            data = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
            columns = np.arange(tile.x0, tile.x1, dtype=np.int64) // scale
            for local_y, source_y in enumerate(range(tile.y0, tile.y1)):
                row = data[local_y]
                finite = np.isfinite(row)
                if not np.any(finite):
                    continue
                preview_y = source_y // scale
                np.add.at(sums[preview_y], columns[finite], row[finite])
                np.add.at(counts[preview_y], columns[finite], 1.0)
            tile_count += 1
    preview = np.divide(
        sums,
        counts,
        out=np.zeros_like(sums, dtype=np.float64),
        where=counts > 0,
    ).astype(np.float32)
    return preview, scale, tile_count


def _frame_reference_tokens(frame_id: str, path: str | Path) -> set[str]:
    frame_path = Path(path)
    return {str(frame_id), frame_path.name, frame_path.stem}


def _select_reference_id(
    calibrated: dict[str, dict[str, Any]],
    quality_reference_id: str | None,
    requested_reference: str | None,
    plan_frames: dict[str, dict[str, Any]] | None = None,
) -> str | None:
    if requested_reference:
        for frame_id, item in calibrated.items():
            if str(requested_reference) in _frame_reference_tokens(frame_id, item["path"]):
                return str(frame_id)
            if plan_frames is not None and frame_id in plan_frames:
                plan_frame = plan_frames[frame_id]
                if str(requested_reference) in _frame_reference_tokens(frame_id, plan_frame["path"]):
                    return str(frame_id)
        raise ValueError(f"registration reference frame was not found: {requested_reference}")
    return quality_reference_id


def _adaptive_star_threshold(image: np.ndarray, sigma: float) -> float:
    finite = np.asarray(image[np.isfinite(image)], dtype=np.float32)
    if finite.size == 0:
        raise ValueError("cannot compute star threshold for an image with no finite pixels")
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    robust_sigma = 1.4826 * mad
    if robust_sigma <= 0.0:
        robust_sigma = float(np.std(finite))
    if robust_sigma <= 0.0:
        robust_sigma = 1.0
    return median + float(sigma) * robust_sigma


def _preview_matrix_to_source_pixels(matrix: Any, scale: int) -> list[list[float]]:
    source_matrix = np.asarray(matrix, dtype=np.float64).reshape(3, 3)
    source_matrix = np.array(source_matrix, copy=True)
    source_matrix[0, 2] *= float(scale)
    source_matrix[1, 2] *= float(scale)
    return [[float(value) for value in row] for row in source_matrix]


def _policy_int(policy: dict[str, Any], key: str, default: int) -> int:
    value = policy.get(key)
    if value is None:
        return int(default)
    return int(value)


def _policy_float(policy: dict[str, Any], key: str, default: float) -> float:
    value = policy.get(key)
    if value is None:
        return float(default)
    return float(value)


def _policy_bool(policy: dict[str, Any], key: str, default: bool) -> bool:
    value = policy.get(key)
    if value is None:
        return bool(default)
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _policy_optional_float(policy: dict[str, Any], key: str, default: float | None) -> float | None:
    value = policy.get(key)
    if value is None:
        return default
    return float(value)


def _validate_registration_solution(
    *,
    status: str,
    matrix: list[list[float]],
    transform_model: str,
    inliers: int,
    rms_px: float,
    min_inliers: int,
    max_rms_px: float,
    solution_source: str,
) -> dict[str, Any]:
    warnings: list[str] = []
    accepted = status in {"ok", "reference"}
    matrix_array = np.asarray(matrix, dtype=np.float64)
    determinant: float | None = None
    if matrix_array.shape != (3, 3):
        accepted = False
        warnings.append(f"registration matrix shape is {matrix_array.shape}, expected 3x3")
    elif not np.all(np.isfinite(matrix_array)):
        accepted = False
        warnings.append("registration matrix contains non-finite values")
    else:
        if abs(float(matrix_array[2, 2])) <= 1.0e-12:
            accepted = False
            warnings.append("registration matrix has invalid homogeneous scale")
        if transform_model in {"translation", "similarity", "affine"} and not np.allclose(
            matrix_array[2], np.asarray([0.0, 0.0, 1.0]), atol=1.0e-6
        ):
            accepted = False
            warnings.append(f"{transform_model} registration matrix has non-affine projective row")
        determinant = float(np.linalg.det(matrix_array[:2, :2]))
        if transform_model in {"translation", "similarity", "affine"} and abs(determinant) <= 1.0e-10:
            accepted = False
            warnings.append("registration matrix linear part is singular")
    requires_star_inliers = solution_source != "streaming_preview_fallback"
    if status == "ok" and requires_star_inliers and inliers < min_inliers:
        accepted = False
        warnings.append(f"registration inliers {inliers} below min_inliers={min_inliers}")
    if status == "ok" and (not np.isfinite(rms_px) or rms_px > max_rms_px):
        accepted = False
        warnings.append(f"registration rms_px {rms_px} exceeds max_rms_px={max_rms_px}")
    return {
        "accepted": bool(accepted),
        "model": transform_model,
        "solution_source": solution_source,
        "requires_star_inliers": requires_star_inliers,
        "min_inliers": int(min_inliers),
        "max_rms_px": float(max_rms_px),
        "inliers": int(inliers),
        "rms_px": float(rms_px) if np.isfinite(rms_px) else None,
        "determinant": determinant,
        "warnings": warnings,
    }


def _cuda_catalog_backend() -> Any:
    import glass_cuda

    if not glass_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is required for registration method cuda_catalog")
    required = [
        "estimate_similarity_from_catalogs_f32",
        "star_grid_top_nms_candidates_f32",
        "star_top_nms_candidates_f32",
        "warp_matrix_bilinear_f32",
        "estimate_translation_search_f32",
    ]
    missing = [name for name in required if not hasattr(glass_cuda, name)]
    if missing:
        raise RuntimeError(f"native CUDA backend lacks registration primitive(s): {', '.join(missing)}")
    return glass_cuda


def _cuda_triangle_backend() -> Any:
    import glass_cuda

    if not glass_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is required for registration method cuda_triangle")
    required = [
        "estimate_similarity_from_triangle_descriptors_f32",
        "star_grid_top_nms_candidates_f32",
        "star_top_nms_candidates_f32",
        "triangle_asterism_descriptors_f32",
        "warp_matrix_bilinear_f32",
    ]
    missing = [name for name in required if not hasattr(glass_cuda, name)]
    if missing:
        raise RuntimeError(f"native CUDA backend lacks triangle registration primitive(s): {', '.join(missing)}")
    return glass_cuda


def _cuda_catalog_similarity_preview(
    reference_preview: np.ndarray,
    moving_preview: np.ndarray,
    registration_policy: dict[str, Any],
    reference_scale: int,
    min_inliers: int,
    max_rms_px: float,
) -> dict[str, Any]:
    glass_cuda = _cuda_catalog_backend()

    threshold_sigma = _policy_float(registration_policy, "cuda_catalog_threshold_sigma", 6.0)
    max_candidates = _policy_int(registration_policy, "cuda_catalog_max_stars", 64)
    tolerance_px = _policy_float(registration_policy, "cuda_catalog_tolerance_px", 3.0)
    h, w = reference_preview.shape
    default_min_pair_distance = max(8.0, float(min(h, w)) / 24.0)
    min_pair_distance = _policy_float(
        registration_policy,
        "cuda_catalog_min_pair_distance",
        default_min_pair_distance,
    )
    similarity_top_k = max(0, _policy_int(registration_policy, "cuda_catalog_similarity_top_k", 0))
    nms_min_separation_px = _policy_float(
        registration_policy,
        "cuda_catalog_nms_min_separation_px",
        max(4.0, float(min(h, w)) / 24.0),
    )
    candidates_per_cell = _policy_int(registration_policy, "cuda_catalog_grid_top_per_cell", 4)

    grid_top_cols = _policy_int(
        registration_policy,
        "cuda_catalog_grid_top_cols",
        0 if min(h, w) < 64 else max(2, min(24, int(np.ceil(w / 64.0)))),
    )
    grid_top_rows = _policy_int(
        registration_policy,
        "cuda_catalog_grid_top_rows",
        0 if min(h, w) < 64 else max(2, min(16, int(np.ceil(h / 64.0)))),
    )

    reference_threshold = _adaptive_star_threshold(reference_preview, threshold_sigma)
    moving_threshold = _adaptive_star_threshold(moving_preview, threshold_sigma)
    if grid_top_cols > 0 and grid_top_rows > 0:
        reference_catalog = glass_cuda.star_grid_top_nms_candidates_f32(
            reference_preview,
            reference_threshold,
            grid_top_cols,
            grid_top_rows,
            candidates_per_cell,
            max_candidates,
            nms_min_separation_px,
        )
        moving_catalog = glass_cuda.star_grid_top_nms_candidates_f32(
            moving_preview,
            moving_threshold,
            grid_top_cols,
            grid_top_rows,
            candidates_per_cell,
            max_candidates,
            nms_min_separation_px,
        )
        selection_model = "grid_topk_local_maximum_nms"
    else:
        nms_scan_candidates = _policy_int(registration_policy, "cuda_catalog_nms_scan_candidates", 4096)
        reference_catalog = glass_cuda.star_top_nms_candidates_f32(
            reference_preview,
            reference_threshold,
            nms_scan_candidates,
            max_candidates,
            nms_min_separation_px,
        )
        moving_catalog = glass_cuda.star_top_nms_candidates_f32(
            moving_preview,
            moving_threshold,
            nms_scan_candidates,
            max_candidates,
            nms_min_separation_px,
        )
        selection_model = "global_top_flux_local_maximum_nms"

    prior_mode = str(registration_policy.get("cuda_catalog_prior") or "ncc")
    prior_dx: float | None = None
    prior_dy: float | None = None
    prior_radius_px = _policy_optional_float(registration_policy, "cuda_catalog_prior_radius_px", 4.0)
    prior: dict[str, Any] | None = None
    if prior_mode == "ncc":
        max_shift = _policy_int(
            registration_policy,
            "cuda_catalog_prior_max_shift",
            max(4, min(64, int(np.ceil(max(h, w) * 0.08)))),
        )
        sample_stride = _policy_int(registration_policy, "cuda_catalog_prior_sample_stride", 1)
        prior = glass_cuda.estimate_translation_search_f32(
            reference_preview,
            moving_preview,
            max_shift,
            max_shift,
            sample_stride=sample_stride,
        )
        prior_dx = float(prior["dx"])
        prior_dy = float(prior["dy"])
        if hasattr(glass_cuda, "estimate_translation_subpixel_ncc_f32"):
            radius_steps = _policy_int(registration_policy, "cuda_catalog_prior_subpixel_radius_steps", 4)
            step = _policy_float(registration_policy, "cuda_catalog_prior_subpixel_step", 0.25)
            prior = glass_cuda.estimate_translation_subpixel_ncc_f32(
                reference_preview,
                moving_preview,
                prior_dx,
                prior_dy,
                radius_steps,
                step,
                sample_stride=sample_stride,
            )
            prior_dx = float(prior["dx"])
            prior_dy = float(prior["dy"])
    elif prior_mode != "none":
        raise ValueError("cuda_catalog_prior must be ncc or none")

    fit = glass_cuda.estimate_similarity_from_catalogs_f32(
        reference_catalog["x"],
        reference_catalog["y"],
        moving_catalog["x"],
        moving_catalog["y"],
        tolerance_px=tolerance_px,
        min_pair_distance=min_pair_distance,
        prior_dx=prior_dx,
        prior_dy=prior_dy,
        prior_radius_px=prior_radius_px,
        min_scale=_policy_optional_float(registration_policy, "cuda_catalog_min_scale", 0.995),
        max_scale=_policy_optional_float(registration_policy, "cuda_catalog_max_scale", 1.005),
        max_abs_rotation_rad=_policy_optional_float(
            registration_policy,
            "cuda_catalog_max_abs_rotation_rad",
            0.01,
        ),
        top_k=similarity_top_k,
    )
    preview_matrix = np.asarray(fit["matrix"], dtype=np.float32).reshape(3, 3)
    pixel_refine: dict[str, Any] | None = None
    if bool(registration_policy.get("cuda_catalog_pixel_refine", True)) and str(fit["status"]) == "ok":
        refine_kwargs = {
            "search_radius_px": _policy_float(registration_policy, "cuda_catalog_pixel_refine_radius", 1.0),
            "coarse_step_px": _policy_float(registration_policy, "cuda_catalog_pixel_refine_coarse_step", 0.25),
            "fine_radius_px": _policy_float(registration_policy, "cuda_catalog_pixel_refine_fine_radius", 0.25),
            "fine_step_px": _policy_float(registration_policy, "cuda_catalog_pixel_refine_fine_step", 0.0625),
            "coarse_sample_stride": _policy_int(
                registration_policy,
                "cuda_catalog_pixel_refine_coarse_stride",
                4,
            ),
            "final_sample_stride": _policy_int(registration_policy, "cuda_catalog_pixel_refine_final_stride", 1),
        }
        top_candidate_matrices = [
            np.asarray(candidate["matrix"], dtype=np.float32).reshape(3, 3)
            for candidate in fit.get("top_candidates", [])
        ]
        if top_candidate_matrices and bool(registration_policy.get("cuda_catalog_pixel_refine_multi_seed", True)):
            seed_matrices = np.stack([preview_matrix, *top_candidate_matrices], axis=0)
            pixel_refine = refine_matrix_translation_candidates_with_metrics_f32(
                reference_preview,
                moving_preview,
                seed_matrices,
                **refine_kwargs,
            )
        else:
            pixel_refine = refine_matrix_translation_with_metrics_f32(
                reference_preview,
                moving_preview,
                preview_matrix,
                **refine_kwargs,
            )
        preview_matrix = np.asarray(pixel_refine["matrix"], dtype=np.float32).reshape(3, 3)

    fit_rms_preview = float(fit.get("rms_px", float("nan")))
    rms_limit_preview = _policy_float(
        registration_policy,
        "cuda_catalog_max_rms_preview_px",
        max(tolerance_px, float(max_rms_px) / max(float(reference_scale), 1.0)),
    )
    inliers = int(fit.get("refined_inliers", fit.get("inliers", 0)))
    accepted = str(fit["status"]) == "ok" and inliers >= int(min_inliers)
    if np.isfinite(fit_rms_preview):
        accepted = accepted and fit_rms_preview <= rms_limit_preview

    warnings: list[str] = []
    if str(fit["status"]) != "ok":
        warnings.append(f"cuda catalog fit status: {fit['status']}")
    if inliers < int(min_inliers):
        warnings.append(f"cuda catalog inliers below {int(min_inliers)}")
    if np.isfinite(fit_rms_preview) and fit_rms_preview > rms_limit_preview:
        warnings.append(
            f"cuda catalog preview RMS {fit_rms_preview:.3f}px exceeds limit {rms_limit_preview:.3f}px"
        )
    warnings.append("cuda catalog similarity estimated on streaming preview")
    if pixel_refine is not None:
        if int(pixel_refine.get("seed_count", 1)) > 1:
            warnings.append("cuda pixel metrics refined catalog matrix translation from multiple top-k seeds")
        else:
            warnings.append("cuda pixel metrics refined catalog matrix translation")

    metrics = None if pixel_refine is None else pixel_refine.get("metrics")
    return {
        "status": "ok" if accepted else "failed",
        "matrix": _preview_matrix_to_source_pixels(preview_matrix, reference_scale),
        "matched_stars": int(fit.get("inliers", 0)),
        "inliers": inliers,
        "rms_px": fit_rms_preview * float(reference_scale) if np.isfinite(fit_rms_preview) else float("nan"),
        "warnings": warnings,
        "diagnostics": {
            "model": "cuda_catalog_similarity_preview",
            "selection_model": selection_model,
            "reference_detected": int(reference_catalog["count"]),
            "moving_detected": int(moving_catalog["count"]),
            "reference_stored": int(reference_catalog["stored_count"]),
            "moving_stored": int(moving_catalog["stored_count"]),
            "reference_threshold": float(reference_threshold),
            "moving_threshold": float(moving_threshold),
            "tolerance_px_preview": float(tolerance_px),
            "rms_px_preview": fit_rms_preview,
            "rms_limit_px_preview": float(rms_limit_preview),
            "min_pair_distance_px_preview": float(min_pair_distance),
            "grid_top_cols": int(grid_top_cols),
            "grid_top_rows": int(grid_top_rows),
            "nms_min_separation_px": float(nms_min_separation_px),
            "prior_mode": prior_mode,
            "prior": prior,
            "prior_radius_px": prior_radius_px,
            "scale": float(fit.get("scale", float("nan"))),
            "rotation_rad": float(fit.get("rotation_rad", float("nan"))),
            "candidate_count": int(fit.get("candidate_count", 0)),
            "best_candidate_index": int(fit.get("best_candidate_index", -1)),
            "similarity_top_k": int(fit.get("top_k", similarity_top_k)),
            "top_candidate_count": len(fit.get("top_candidates", [])),
            "top_candidates": fit.get("top_candidates", []),
            "refit_status": str(fit.get("refit_status", "not_run")),
            "refit_rms_px_preview": float(fit.get("refit_rms_px", fit_rms_preview)),
            "pixel_refine": pixel_refine,
            "pixel_metric_rms_adu": None if metrics is None else float(metrics.get("rms", float("nan"))),
            "pixel_metric_ncc": None if metrics is None else float(metrics.get("ncc", float("nan"))),
        },
    }


def _cuda_triangle_descriptor_preview(
    reference_preview: np.ndarray,
    moving_preview: np.ndarray,
    registration_policy: dict[str, Any],
    reference_scale: int,
    min_inliers: int,
    max_rms_px: float,
) -> dict[str, Any]:
    _cuda_triangle_backend()

    threshold_sigma = _policy_float(
        registration_policy,
        "cuda_triangle_threshold_sigma",
        _policy_float(registration_policy, "cuda_catalog_threshold_sigma", 6.0),
    )
    max_candidates = _policy_int(
        registration_policy,
        "cuda_triangle_max_stars",
        _policy_int(registration_policy, "cuda_catalog_max_stars", 64),
    )
    neighbors = _policy_int(registration_policy, "cuda_triangle_neighbors", 5)
    max_descriptors = _policy_int(registration_policy, "cuda_triangle_max_descriptors", 1200)
    tolerance_px = _policy_float(
        registration_policy,
        "cuda_triangle_tolerance_px",
        _policy_float(registration_policy, "cuda_catalog_tolerance_px", 3.0),
    )
    descriptor_radius = _policy_float(registration_policy, "cuda_triangle_descriptor_radius", 0.1)
    h, w = reference_preview.shape
    nms_min_separation_px = _policy_float(
        registration_policy,
        "cuda_triangle_nms_min_separation_px",
        _policy_float(
            registration_policy,
            "cuda_catalog_nms_min_separation_px",
            max(4.0, float(min(h, w)) / 24.0),
        ),
    )
    candidates_per_cell = _policy_int(
        registration_policy,
        "cuda_triangle_grid_top_per_cell",
        _policy_int(registration_policy, "cuda_catalog_grid_top_per_cell", 4),
    )
    grid_top_cols = _policy_int(
        registration_policy,
        "cuda_triangle_grid_top_cols",
        _policy_int(
            registration_policy,
            "cuda_catalog_grid_top_cols",
            0 if min(h, w) < 64 else max(2, min(24, int(np.ceil(w / 64.0)))),
        ),
    )
    grid_top_rows = _policy_int(
        registration_policy,
        "cuda_triangle_grid_top_rows",
        _policy_int(
            registration_policy,
            "cuda_catalog_grid_top_rows",
            0 if min(h, w) < 64 else max(2, min(16, int(np.ceil(h / 64.0)))),
        ),
    )

    reference_threshold = _adaptive_star_threshold(reference_preview, threshold_sigma)
    moving_threshold = _adaptive_star_threshold(moving_preview, threshold_sigma)
    threshold = min(reference_threshold, moving_threshold)
    if grid_top_cols > 0 and grid_top_rows > 0:
        selector_kwargs = {
            "grid_top_cols": grid_top_cols,
            "grid_top_rows": grid_top_rows,
            "grid_top_candidates_per_cell": candidates_per_cell,
            "nms_min_separation_px": nms_min_separation_px,
        }
        selection_model = "grid_topk_local_maximum_nms"
    else:
        nms_scan_candidates = _policy_int(
            registration_policy,
            "cuda_triangle_nms_scan_candidates",
            _policy_int(registration_policy, "cuda_catalog_nms_scan_candidates", 4096),
        )
        selector_kwargs = {
            "nms_scan_candidates": nms_scan_candidates,
            "nms_min_separation_px": nms_min_separation_px,
        }
        selection_model = "global_top_flux_local_maximum_nms"

    _, coverage, diagnostics = register_triangle_descriptor_similarity_f32(
        reference_preview,
        moving_preview,
        threshold,
        max_candidates=max_candidates,
        neighbors=neighbors,
        max_descriptors=max_descriptors,
        tolerance_px=tolerance_px,
        descriptor_radius=descriptor_radius,
        **selector_kwargs,
    )
    fit = diagnostics.get("similarity", {})
    preview_matrix = np.asarray(diagnostics["matrix"], dtype=np.float32).reshape(3, 3)
    fit_rms_preview = float(fit.get("rms_px", float("nan")))
    rms_limit_preview = _policy_float(
        registration_policy,
        "cuda_triangle_max_rms_preview_px",
        max(tolerance_px, float(max_rms_px) / max(float(reference_scale), 1.0)),
    )
    inliers = int(fit.get("inliers", 0))
    accepted = str(diagnostics.get("status")) == "ok" and inliers >= int(min_inliers)
    if np.isfinite(fit_rms_preview):
        accepted = accepted and fit_rms_preview <= rms_limit_preview

    warnings: list[str] = []
    if str(diagnostics.get("status")) != "ok":
        warnings.append(f"cuda triangle descriptor fit status: {diagnostics.get('status')}")
    if inliers < int(min_inliers):
        warnings.append(f"cuda triangle descriptor inliers below {int(min_inliers)}")
    if np.isfinite(fit_rms_preview) and fit_rms_preview > rms_limit_preview:
        warnings.append(
            f"cuda triangle descriptor preview RMS {fit_rms_preview:.3f}px exceeds "
            f"limit {rms_limit_preview:.3f}px"
        )
    warnings.append("cuda triangle descriptor similarity estimated on streaming preview")

    return {
        "status": "ok" if accepted else "failed",
        "matrix": _preview_matrix_to_source_pixels(preview_matrix, reference_scale),
        "matched_stars": int(fit.get("inliers", 0)),
        "inliers": inliers,
        "rms_px": fit_rms_preview * float(reference_scale) if np.isfinite(fit_rms_preview) else float("nan"),
        "warnings": warnings,
        "diagnostics": {
            "model": "cuda_triangle_descriptor_similarity_preview",
            "selection_model": selection_model,
            "catalog_selector": diagnostics.get("catalog_selector"),
            "reference_detected": int(diagnostics.get("reference_detected", 0)),
            "moving_detected": int(diagnostics.get("moving_detected", 0)),
            "reference_stored": int(diagnostics.get("reference_stored", 0)),
            "moving_stored": int(diagnostics.get("moving_stored", 0)),
            "reference_descriptor_count": int(diagnostics.get("reference_descriptor_count", 0)),
            "moving_descriptor_count": int(diagnostics.get("moving_descriptor_count", 0)),
            "reference_threshold": float(reference_threshold),
            "moving_threshold": float(moving_threshold),
            "threshold_used": float(threshold),
            "tolerance_px_preview": float(tolerance_px),
            "rms_px_preview": fit_rms_preview,
            "rms_limit_px_preview": float(rms_limit_preview),
            "descriptor_radius": float(descriptor_radius),
            "neighbors": int(neighbors),
            "max_descriptors": int(max_descriptors),
            "grid_top_cols": int(grid_top_cols),
            "grid_top_rows": int(grid_top_rows),
            "nms_min_separation_px": float(nms_min_separation_px),
            "candidate_count": int(fit.get("candidate_count", 0)),
            "coverage_pixels": int(np.sum(coverage > 0.0)),
            "similarity": fit,
        },
    }


def register_calibrated_frames(
    run_dir: str | Path,
    out_path: str | Path | None = None,
    tile_size: int = 512,
    preview_max_dimension: int = 1024,
    method: str = "auto",
    reference_frame_id: str | None = None,
) -> dict[str, Any]:
    if preview_max_dimension <= 0:
        raise ValueError("preview_max_dimension must be positive")
    run = Path(run_dir)
    artifacts = read_json(run / "calibration_artifacts.json")
    quality = read_json(run / "frame_quality.json")
    plan = read_json(run / "processing_plan.json") if (run / "processing_plan.json").exists() else {}
    registration_policy = plan.get("registration_policy", {})
    transform_model = str(registration_policy.get("transform_model") or "translation")
    min_inliers = int(registration_policy.get("min_inliers") or 6)
    max_rms_px = float(registration_policy.get("max_rms_px") or 2.0)
    astroalign_max_control_points = int(registration_policy.get("astroalign_max_control_points") or 50)
    astroalign_detection_sigma = float(registration_policy.get("astroalign_detection_sigma") or 5.0)
    astroalign_min_area = int(registration_policy.get("astroalign_min_area") or 5)
    if transform_model not in {"translation", "similarity", "affine", "homography"}:
        transform_model = "translation"
    if method in {"astroalign", "cuda_catalog", "cuda_triangle"}:
        transform_model = "similarity"
    if method not in {"auto", "star", "astroalign", "cuda_catalog", "cuda_triangle"}:
        raise ValueError("registration method must be auto, star, astroalign, cuda_catalog, or cuda_triangle")
    if method == "cuda_catalog":
        _cuda_catalog_backend()
    if method == "cuda_triangle":
        _cuda_triangle_backend()
    calibrated = {item["frame_id"]: item for item in artifacts.get("calibrated_lights", [])}
    plan_frames = {frame["id"]: frame for frame in plan.get("frames", [])}
    reference_id = _select_reference_id(
        calibrated,
        quality.get("reference_frame_id"),
        reference_frame_id,
        plan_frames,
    )
    if reference_id not in calibrated:
        raise ValueError("reference frame is missing from calibrated cache")
    reference_preview, reference_scale, reference_tile_count = _registration_preview(
        calibrated[reference_id]["path"],
        tile_size=tile_size,
        max_dimension=preview_max_dimension,
    )
    quality_by_id = {item["frame_id"]: item for item in quality.get("frame_quality", [])}
    reference_quality = quality_by_id.get(reference_id, {})
    reference_stars = detect_stars_streaming(
        calibrated[reference_id]["path"],
        float(reference_quality.get("background_median") or 0.0),
        float(reference_quality.get("noise_mad") or reference_quality.get("background_rms") or 0.0),
        tile_size=tile_size,
    )
    quality_gate_enforced = _policy_bool(registration_policy, "reject_quality_gate_failed_frames", True)
    quality_gate_rejected_frames = 0

    results = []
    for frame_id, item in calibrated.items():
        warnings: list[str] = []
        extra_fields: dict[str, Any] = {}
        tile_count = reference_tile_count
        row_source = "streaming_star_detector"
        quality_row = quality_by_id.get(frame_id, {})
        quality_gate_status = str(quality_row.get("quality_gate_status") or "unknown")
        quality_gate_warnings = [str(warning) for warning in quality_row.get("quality_gate_warnings", [])]
        if frame_id == reference_id:
            dx, dy = 0.0, 0.0
            status = "reference"
            rms = 0.0
            matrix = translation_matrix(dx, dy)
            matched = len(reference_stars)
            inliers = len(reference_stars)
            preview_scale = reference_scale
            preview_shape = list(reference_preview.shape)
            if quality_gate_enforced and quality_gate_status == "rejected":
                warnings.append("reference frame failed quality gate but is required as registration reference")
            if method == "cuda_catalog":
                row_source = "cuda_catalog_similarity_preview"
            elif method == "cuda_triangle":
                row_source = "cuda_triangle_descriptor_similarity_preview"
        elif quality_gate_enforced and quality_gate_status == "rejected":
            matrix = translation_matrix(0.0, 0.0)
            matched = 0
            inliers = 0
            rms = float("nan")
            status = "quality_rejected"
            preview_scale = reference_scale
            preview_shape = list(reference_preview.shape)
            tile_count = 0
            row_source = "quality_gate"
            quality_gate_rejected_frames += 1
            warnings.append("registration skipped because frame failed the quality gate")
            warnings.extend(quality_gate_warnings)
        else:
            moving_preview, moving_scale, tile_count = _registration_preview(
                item["path"],
                tile_size=tile_size,
                max_dimension=preview_max_dimension,
            )
            if moving_preview.shape != reference_preview.shape:
                raise ValueError(
                    f"registration preview shape mismatch: {moving_preview.shape} != {reference_preview.shape}"
                )
            if moving_scale != reference_scale:
                raise ValueError(f"registration preview scale mismatch: {moving_scale} != {reference_scale}")
            matrix = None
            matched = 0
            inliers = 0
            rms = float("nan")
            status = "failed"
            if method == "cuda_catalog":
                try:
                    cuda_catalog_result = _cuda_catalog_similarity_preview(
                        reference_preview,
                        moving_preview,
                        registration_policy,
                        reference_scale,
                        min_inliers,
                        max_rms_px,
                    )
                    matrix = cuda_catalog_result["matrix"]
                    matched = int(cuda_catalog_result["matched_stars"])
                    inliers = int(cuda_catalog_result["inliers"])
                    rms = float(cuda_catalog_result["rms_px"])
                    status = str(cuda_catalog_result["status"])
                    warnings.extend(cuda_catalog_result["warnings"])
                    extra_fields["cuda_catalog"] = cuda_catalog_result["diagnostics"]
                    row_source = "cuda_catalog_similarity_preview"
                except Exception as exc:
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms = float("nan")
                    status = "failed"
                    warnings.append(f"cuda catalog registration failed: {exc}")
                    row_source = "cuda_catalog_similarity_preview"
            if method == "cuda_triangle":
                try:
                    cuda_triangle_result = _cuda_triangle_descriptor_preview(
                        reference_preview,
                        moving_preview,
                        registration_policy,
                        reference_scale,
                        min_inliers,
                        max_rms_px,
                    )
                    matrix = cuda_triangle_result["matrix"]
                    matched = int(cuda_triangle_result["matched_stars"])
                    inliers = int(cuda_triangle_result["inliers"])
                    rms = float(cuda_triangle_result["rms_px"])
                    status = str(cuda_triangle_result["status"])
                    warnings.extend(cuda_triangle_result["warnings"])
                    extra_fields["cuda_triangle"] = cuda_triangle_result["diagnostics"]
                    row_source = "cuda_triangle_descriptor_similarity_preview"
                except Exception as exc:
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms = float("nan")
                    status = "failed"
                    warnings.append(f"cuda triangle descriptor registration failed: {exc}")
                    row_source = "cuda_triangle_descriptor_similarity_preview"
            if method == "astroalign":
                try:
                    astroalign_result = estimate_astroalign_transform(
                        reference_preview,
                        moving_preview,
                        max_control_points=astroalign_max_control_points,
                        detection_sigma=astroalign_detection_sigma,
                        min_area=astroalign_min_area,
                    )
                    matrix_array = np.asarray(astroalign_result.matrix, dtype=np.float64)
                    matrix_array[0, 2] *= reference_scale
                    matrix_array[1, 2] *= reference_scale
                    matrix = [[float(value) for value in row] for row in matrix_array]
                    matched = astroalign_result.matched_stars
                    inliers = astroalign_result.inliers
                    rms = float(astroalign_result.rms_px) * reference_scale
                    status = astroalign_result.status
                    warnings.extend(astroalign_result.warnings)
                    warnings.append("astroalign transform estimated on streaming preview")
                    row_source = "open_source_astroalign_preview"
                except Exception as exc:
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms = float("nan")
                    status = "failed"
                    warnings.append(f"astroalign registration failed: {exc}")
                    row_source = "open_source_astroalign_preview"
            if method in {"star", "auto"}:
                moving_quality = quality_by_id.get(frame_id, {})
                moving_stars = detect_stars_streaming(
                    item["path"],
                    float(moving_quality.get("background_median") or 0.0),
                    float(moving_quality.get("noise_mad") or moving_quality.get("background_rms") or 0.0),
                    tile_size=tile_size,
                )
                star_result = estimate_star_transform(
                    reference_stars,
                    moving_stars,
                    transform_model=transform_model,
                    min_inliers=min_inliers,
                    tolerance_px=max(max_rms_px * 1.5, 3.0),
                )
                matrix = star_result.matrix
                matched = star_result.matched_stars
                inliers = star_result.inliers
                rms = star_result.rms_px
                status = star_result.status
                warnings.extend(star_result.warnings)
                warnings.append("star-based clean-room registration")
            if status != "ok" and method == "auto":
                preview_dx, preview_dy = estimate_translation_phase_correlation(reference_preview, moving_preview)
                dx, dy = preview_dx * reference_scale, preview_dy * reference_scale
                matrix = translation_matrix(dx, dy)
                matched = min(
                    int(quality_by_id.get(frame_id, {}).get("star_count") or 0),
                    int(quality_by_id.get(reference_id, {}).get("star_count") or 0),
                )
                inliers = matched
                rms = 0.0
                status = "ok"
                warnings.append("fell back to phase-correlation preview registration")
                row_source = "streaming_preview_fallback"
            if matrix is None:
                matrix = translation_matrix(0.0, 0.0)
            preview_scale = moving_scale
            preview_shape = list(moving_preview.shape)
        if status == "ok" and matched == 0:
            warnings.append("registration estimated by phase correlation without detected star matches")
        validation = _validate_registration_solution(
            status=status,
            matrix=matrix,
            transform_model=transform_model,
            inliers=inliers,
            rms_px=rms,
            min_inliers=min_inliers,
            max_rms_px=max_rms_px,
            solution_source=row_source,
        )
        if status == "ok" and not validation["accepted"]:
            status = "failed"
            warnings.append("registration failed validation gate")
        warnings.extend(str(item) for item in validation["warnings"])
        extra_fields["registration_validation"] = validation
        row = to_jsonable(
            RegistrationResult(
                frame_id=frame_id,
                reference_frame_id=reference_id,
                transform_model=transform_model,
                matrix=matrix,
                matched_stars=matched,
                inliers=inliers,
                rms_px=rms,
                status=status,
                warnings=warnings,
            )
        )
        row.update(
            {
                "registration_image_source": "streaming_preview",
                "registration_solution_source": row_source,
                "preview_scale": preview_scale,
                "preview_shape": preview_shape,
                "tile_size": tile_size,
                "tile_count": tile_count,
                "quality_gate_status": quality_gate_status,
                "quality_gate_warnings": quality_gate_warnings,
                "quality_gate_enforced": quality_gate_enforced,
            }
        )
        row.update(to_jsonable(extra_fields))
        results.append(row)

    payload = {
        "schema_version": 1,
        "reference_frame_id": reference_id,
        "transform_model": transform_model,
        "method": method,
        "registration_image_source": "streaming_star_detector",
        "astroalign": {
            "available": method == "astroalign",
            "max_control_points": astroalign_max_control_points,
            "detection_sigma": astroalign_detection_sigma,
            "min_area": astroalign_min_area,
            "license": "MIT",
        },
        "cuda_catalog": {
            "available": method == "cuda_catalog",
            "native_cuda_required": True,
            "model": "cuda_catalog_similarity_preview",
            "pixel_refine_default": True,
        },
        "cuda_triangle": {
            "available": method == "cuda_triangle",
            "native_cuda_required": True,
            "model": "cuda_triangle_descriptor_similarity_preview",
            "descriptor": "triangle_similarity",
        },
        "min_inliers": min_inliers,
        "max_rms_px": max_rms_px,
        "preview_max_dimension": preview_max_dimension,
        "quality_reference_frame_id": quality.get("reference_frame_id"),
        "requested_reference_frame_id": reference_frame_id,
        "tile_size": tile_size,
        "quality_gate_enforced": quality_gate_enforced,
        "quality_gate_rejected_frames": quality_gate_rejected_frames,
        "quality_gate_summary": quality.get("quality_gate_summary"),
        "registration_results": results,
    }
    write_json(out_path or (run / "registration_results.json"), payload)
    return payload
