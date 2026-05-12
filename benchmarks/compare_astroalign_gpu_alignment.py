from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
from astropy.io import fits

import gpwbpp_cuda


def _shift_image(data: np.ndarray, dx: int, dy: int) -> np.ndarray:
    output = np.zeros_like(data, dtype=np.float32)
    h, w = data.shape
    src_x0 = max(0, -dx)
    src_x1 = min(w, w - dx)
    dst_x0 = max(0, dx)
    dst_x1 = min(w, w + dx)
    src_y0 = max(0, -dy)
    src_y1 = min(h, h - dy)
    dst_y0 = max(0, dy)
    dst_y1 = min(h, h + dy)
    if src_x0 < src_x1 and src_y0 < src_y1:
        output[dst_y0:dst_y1, dst_x0:dst_x1] = data[src_y0:src_y1, src_x0:src_x1]
    return output


def _synthetic_pair(width: int, height: int, dx: int, dy: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260513)
    yy, xx = np.indices((height, width), dtype=np.float32)
    reference = 20.0 + 0.01 * xx + 0.015 * yy
    margin = 24
    for _ in range(80):
        x = float(rng.uniform(margin, width - margin))
        y = float(rng.uniform(margin, height - margin))
        sigma = float(rng.uniform(1.0, 2.2))
        flux = float(rng.uniform(200.0, 1200.0))
        reference += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * sigma * sigma)))
    reference += rng.normal(0.0, 1.5, size=reference.shape).astype(np.float32)
    moving = _shift_image(reference.astype(np.float32), dx, dy)
    return reference.astype(np.float32), moving.astype(np.float32)


def _read_fits(path: Path) -> np.ndarray:
    with fits.open(path, memmap=False) as hdul:
        return np.asarray(hdul[0].data, dtype=np.float32)


def _center_crop(image: np.ndarray, size: int | None) -> np.ndarray:
    if size is None or size <= 0:
        return image
    h, w = image.shape
    crop_h = min(h, int(size))
    crop_w = min(w, int(size))
    y0 = (h - crop_h) // 2
    x0 = (w - crop_w) // 2
    return np.ascontiguousarray(image[y0 : y0 + crop_h, x0 : x0 + crop_w], dtype=np.float32)


def _rms(reference: np.ndarray, aligned: np.ndarray, valid: np.ndarray) -> float:
    mask = np.asarray(valid, dtype=bool) & np.isfinite(reference) & np.isfinite(aligned)
    if not np.any(mask):
        return float("nan")
    diff = aligned[mask].astype(np.float64) - reference[mask].astype(np.float64)
    return float(np.sqrt(np.mean(diff * diff)))


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


def _astroalign_run(reference: np.ndarray, moving: np.ndarray) -> dict[str, Any]:
    import astroalign as aa

    t0 = time.perf_counter()
    transform, control_points = aa.find_transform(moving, reference)
    find_elapsed = time.perf_counter() - t0
    t1 = time.perf_counter()
    aligned, footprint = aa.apply_transform(transform, moving, reference, fill_value=0.0)
    apply_elapsed = time.perf_counter() - t1
    params = np.asarray(transform.params, dtype=np.float64)
    invalid = np.asarray(footprint, dtype=bool)
    valid = ~invalid if invalid.shape == reference.shape else np.isfinite(aligned)
    return {
        "elapsed_s": find_elapsed + apply_elapsed,
        "find_elapsed_s": find_elapsed,
        "apply_elapsed_s": apply_elapsed,
        "dx": float(params[0, 2]),
        "dy": float(params[1, 2]),
        "matrix": params.tolist(),
        "rms": _rms(reference, np.asarray(aligned, dtype=np.float32), valid),
        "matched_control_points": int(len(control_points[0])) if control_points else 0,
    }


def _gpu_run(reference: np.ndarray, moving: np.ndarray, max_shift: int) -> dict[str, Any]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    t0 = time.perf_counter()
    estimate = gpwbpp_cuda.estimate_translation_search_f32(reference, moving, max_shift, max_shift)
    aligned, coverage = gpwbpp_cuda.warp_translation_f32(moving, estimate["dx"], estimate["dy"], 0.0)
    elapsed = time.perf_counter() - t0
    return {
        "elapsed_s": elapsed,
        "dx": int(estimate["dx"]),
        "dy": int(estimate["dy"]),
        "score": float(estimate["score"]),
        "search_count": int(estimate["search_count"]),
        "model": str(estimate["model"]),
        "rms": _rms(reference, aligned, coverage > 0.0),
    }


def _gpu_subpixel_run(
    reference: np.ndarray,
    moving: np.ndarray,
    coarse: dict[str, Any],
    radius_steps: int,
    step: float,
) -> dict[str, Any]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    t0 = time.perf_counter()
    estimate = gpwbpp_cuda.estimate_translation_subpixel_ncc_f32(
        reference,
        moving,
        float(coarse["dx"]),
        float(coarse["dy"]),
        radius_steps,
        step,
    )
    aligned, coverage = gpwbpp_cuda.warp_translation_bilinear_f32(moving, estimate["dx"], estimate["dy"], 0.0)
    elapsed = time.perf_counter() - t0
    return {
        "elapsed_s": elapsed,
        "dx": float(estimate["dx"]),
        "dy": float(estimate["dy"]),
        "score": float(estimate["score"]),
        "candidate_count": int(estimate["candidate_count"]),
        "center_dx": float(estimate["center_dx"]),
        "center_dy": float(estimate["center_dy"]),
        "radius_steps": int(estimate["radius_steps"]),
        "step": float(estimate["step"]),
        "model": str(estimate["model"]),
        "rms": _rms(reference, aligned, coverage > 0.0),
    }


def _gpu_matrix_warp_run(reference: np.ndarray, moving: np.ndarray, matrix: Any) -> dict[str, Any]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    t0 = time.perf_counter()
    aligned, coverage = gpwbpp_cuda.warp_matrix_bilinear_f32(moving, matrix, 0.0)
    elapsed = time.perf_counter() - t0
    valid = coverage > 0.0
    return {
        "elapsed_s": elapsed,
        "matrix": np.asarray(matrix, dtype=np.float64).tolist(),
        "coverage_pixels": int(np.sum(valid)),
        "model": "cuda_matrix_bilinear_warp_from_external_transform",
        "rms": _rms(reference, aligned, valid),
    }


def _gpu_resident_ncc_subpixel_run(
    reference: np.ndarray,
    moving: np.ndarray,
    max_shift: int,
    radius_steps: int,
    step: float,
) -> dict[str, Any]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    if not hasattr(gpwbpp_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("native CUDA backend lacks ResidentCalibratedStack")
    t0 = time.perf_counter()
    stack = gpwbpp_cuda.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    upload_elapsed = time.perf_counter() - t0

    t1 = time.perf_counter()
    coarse = stack.estimate_translation_to_reference(0, 1, max_shift, max_shift)
    refined = stack.estimate_translation_subpixel_to_reference(
        0,
        1,
        float(coarse["dx"]),
        float(coarse["dy"]),
        radius_steps,
        step,
    )
    stack.apply_translation_bilinear_frame(1, refined["dx"], refined["dy"], np.nan)
    device_elapsed = time.perf_counter() - t1

    t2 = time.perf_counter()
    aligned, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))
    inspection_elapsed = time.perf_counter() - t2
    return {
        "elapsed_s": device_elapsed,
        "upload_elapsed_s": upload_elapsed,
        "inspection_download_elapsed_s": inspection_elapsed,
        "upload_plus_device_elapsed_s": upload_elapsed + device_elapsed,
        "dx": float(refined["dx"]),
        "dy": float(refined["dy"]),
        "score": float(refined["score"]),
        "candidate_count": int(refined["candidate_count"]),
        "coarse_dx": int(coarse["dx"]),
        "coarse_dy": int(coarse["dy"]),
        "coarse_score": float(coarse["score"]),
        "coarse_search_count": int(coarse["search_count"]),
        "radius_steps": int(refined["radius_steps"]),
        "step": float(refined["step"]),
        "bytes_allocated": int(stack.bytes_allocated),
        "model": "resident_translation_integer_ncc_then_subpixel_ncc",
        "rms": _rms(reference, aligned, weight_map > 0.0),
    }


def _gpu_resident_matrix_warp_run(reference: np.ndarray, moving: np.ndarray, matrix: Any) -> dict[str, Any]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    if not hasattr(gpwbpp_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("native CUDA backend lacks ResidentCalibratedStack")
    t0 = time.perf_counter()
    stack = gpwbpp_cuda.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    upload_elapsed = time.perf_counter() - t0

    t1 = time.perf_counter()
    stack.apply_matrix_bilinear_frame(1, matrix, np.nan)
    device_elapsed = time.perf_counter() - t1

    t2 = time.perf_counter()
    aligned, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))
    inspection_elapsed = time.perf_counter() - t2
    valid = weight_map > 0.0
    return {
        "elapsed_s": device_elapsed,
        "upload_elapsed_s": upload_elapsed,
        "inspection_download_elapsed_s": inspection_elapsed,
        "upload_plus_device_elapsed_s": upload_elapsed + device_elapsed,
        "matrix": np.asarray(matrix, dtype=np.float64).tolist(),
        "coverage_pixels": int(np.sum(valid)),
        "bytes_allocated": int(stack.bytes_allocated),
        "model": "resident_cuda_matrix_bilinear_warp_from_external_transform",
        "rms": _rms(reference, aligned, valid),
    }


def _gpu_catalog_run(
    reference: np.ndarray,
    moving: np.ndarray,
    max_stars: int,
    threshold_sigma: float,
    tolerance_px: float,
    max_shift: int | None = None,
    min_inliers: int = 6,
    grid_cols: int | None = None,
    grid_rows: int | None = None,
    prior_dx: float | None = None,
    prior_dy: float | None = None,
    prior_radius_px: float | None = None,
) -> dict[str, Any]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    t0 = time.perf_counter()
    reference_threshold = _adaptive_star_threshold(reference, threshold_sigma)
    moving_threshold = _adaptive_star_threshold(moving, threshold_sigma)
    if grid_cols is not None and grid_rows is not None:
        reference_catalog = gpwbpp_cuda.star_grid_candidates_f32(reference, reference_threshold, grid_cols, grid_rows)
        moving_catalog = gpwbpp_cuda.star_grid_candidates_f32(moving, moving_threshold, grid_cols, grid_rows)
        selection_model = "grid_brightest_local_maximum"
    else:
        reference_catalog = gpwbpp_cuda.star_top_candidates_f32(reference, reference_threshold, max_stars)
        moving_catalog = gpwbpp_cuda.star_top_candidates_f32(moving, moving_threshold, max_stars)
        selection_model = "global_top_flux_local_maximum"
    if reference_catalog["stored_count"] == 0 or moving_catalog["stored_count"] == 0:
        raise RuntimeError(
            "GPU catalog alignment found no stars "
            f"(reference={reference_catalog['stored_count']}, moving={moving_catalog['stored_count']})"
        )
    estimate = gpwbpp_cuda.estimate_translation_from_catalogs_f32(
        reference_catalog["x"],
        reference_catalog["y"],
        moving_catalog["x"],
        moving_catalog["y"],
        tolerance_px,
        None if max_shift is None else float(max_shift),
        None if max_shift is None else float(max_shift),
        prior_dx,
        prior_dy,
        prior_radius_px,
    )
    dx = float(estimate["refined_dx"])
    dy = float(estimate["refined_dy"])
    aligned, coverage = gpwbpp_cuda.warp_translation_bilinear_f32(moving, dx, dy, 0.0)
    elapsed = time.perf_counter() - t0
    accepted = int(estimate["mutual_inliers"]) >= int(min_inliers)
    warnings = [] if accepted else [f"catalog mutual inliers below {int(min_inliers)}"]
    return {
        "elapsed_s": elapsed,
        "dx": dx,
        "dy": dy,
        "vote_dx": float(estimate["dx"]),
        "vote_dy": float(estimate["dy"]),
        "inliers": int(estimate["inliers"]),
        "mutual_inliers": int(estimate["mutual_inliers"]),
        "rms_px": float(estimate["rms_px"]),
        "candidate_count": int(estimate["candidate_count"]),
        "reference_count": int(estimate["reference_count"]),
        "moving_count": int(estimate["moving_count"]),
        "reference_detected": int(reference_catalog["count"]),
        "moving_detected": int(moving_catalog["count"]),
        "reference_stored": int(reference_catalog["stored_count"]),
        "moving_stored": int(moving_catalog["stored_count"]),
        "reference_threshold": reference_threshold,
        "moving_threshold": moving_threshold,
        "selection_model": selection_model,
        "grid_cols": grid_cols,
        "grid_rows": grid_rows,
        "tolerance_px": float(tolerance_px),
        "max_shift": None if max_shift is None else int(max_shift),
        "prior_dx": prior_dx,
        "prior_dy": prior_dy,
        "prior_radius_px": prior_radius_px,
        "min_inliers": int(min_inliers),
        "accepted": accepted,
        "warnings": warnings,
        "model": "catalog_pair_offset_translation_refined_bilinear_warp",
        "rms": _rms(reference, aligned, coverage > 0.0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare astroalign with GPWBPP CUDA translation alignment.")
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--moving", type=Path)
    parser.add_argument("--out", type=Path, default=Path("runs/alignment_compare/astroalign_vs_gpu_alignment.json"))
    parser.add_argument("--max-shift", type=int, default=16)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--synthetic-dx", type=int, default=7)
    parser.add_argument("--synthetic-dy", type=int, default=-5)
    parser.add_argument("--center-crop", type=int, help="Center-crop both FITS inputs to this square size.")
    parser.add_argument("--catalog-stars", type=int, default=64)
    parser.add_argument("--catalog-threshold-sigma", type=float, default=6.0)
    parser.add_argument("--catalog-tolerance-px", type=float, default=3.0)
    parser.add_argument("--catalog-max-shift", type=int)
    parser.add_argument("--catalog-min-inliers", type=int, default=6)
    parser.add_argument("--catalog-grid-cols", type=int)
    parser.add_argument("--catalog-grid-rows", type=int)
    parser.add_argument("--catalog-prior-radius", type=float)
    parser.add_argument("--subpixel-radius-steps", type=int, default=4)
    parser.add_argument("--subpixel-step", type=float, default=0.25)
    args = parser.parse_args()
    if (args.catalog_grid_cols is None) != (args.catalog_grid_rows is None):
        raise ValueError("--catalog-grid-cols and --catalog-grid-rows must be provided together")

    if args.reference and args.moving:
        reference = _center_crop(_read_fits(args.reference), args.center_crop)
        moving = _center_crop(_read_fits(args.moving), args.center_crop)
        truth: dict[str, Any] | None = None
        source_paths = {"reference": str(args.reference), "moving": str(args.moving)}
    else:
        reference, moving = _synthetic_pair(args.width, args.height, args.synthetic_dx, args.synthetic_dy)
        truth = {"moving_shift_dx": args.synthetic_dx, "moving_shift_dy": args.synthetic_dy}
        source_paths = None

    if reference.shape != moving.shape:
        raise ValueError(f"shape mismatch: reference={reference.shape}, moving={moving.shape}")

    astroalign_result = _astroalign_run(reference, moving)
    astroalign_matrix = np.asarray(astroalign_result["matrix"], dtype=np.float64)
    gpu_matrix_result = _gpu_matrix_warp_run(reference, moving, astroalign_matrix)
    gpu_result = _gpu_run(reference, moving, args.max_shift)
    gpu_subpixel_result = _gpu_subpixel_run(
        reference,
        moving,
        gpu_result,
        args.subpixel_radius_steps,
        args.subpixel_step,
    )
    gpu_ncc_subpixel_result = {
        **gpu_subpixel_result,
        "elapsed_s": float(gpu_result["elapsed_s"] + gpu_subpixel_result["elapsed_s"]),
        "coarse_elapsed_s": float(gpu_result["elapsed_s"]),
        "refinement_elapsed_s": float(gpu_subpixel_result["elapsed_s"]),
        "coarse_dx": int(gpu_result["dx"]),
        "coarse_dy": int(gpu_result["dy"]),
        "coarse_score": float(gpu_result["score"]),
        "model": "translation_integer_ncc_then_subpixel_ncc",
    }
    gpu_resident_result = _gpu_resident_ncc_subpixel_run(
        reference,
        moving,
        args.max_shift,
        args.subpixel_radius_steps,
        args.subpixel_step,
    )
    gpu_resident_matrix_result = _gpu_resident_matrix_warp_run(reference, moving, astroalign_matrix)
    catalog_max_shift = args.max_shift if args.catalog_max_shift is None else args.catalog_max_shift
    prior_dx = float(gpu_result["dx"]) if args.catalog_prior_radius is not None else None
    prior_dy = float(gpu_result["dy"]) if args.catalog_prior_radius is not None else None
    gpu_catalog_result = _gpu_catalog_run(
        reference,
        moving,
        args.catalog_stars,
        args.catalog_threshold_sigma,
        args.catalog_tolerance_px,
        catalog_max_shift,
        args.catalog_min_inliers,
        args.catalog_grid_cols,
        args.catalog_grid_rows,
        prior_dx,
        prior_dy,
        args.catalog_prior_radius,
    )
    if (
        gpu_catalog_result["accepted"]
        and np.isfinite(gpu_catalog_result["rms"])
        and np.isfinite(gpu_result["rms"])
        and gpu_catalog_result["rms"] > gpu_result["rms"] * 1.05
    ):
        gpu_catalog_result["accepted"] = False
        gpu_catalog_result["warnings"].append("catalog image RMS is worse than integer NCC by more than 5%")
    devices = gpwbpp_cuda.list_devices()
    result = {
        "image_shape": list(reference.shape),
        "source_paths": source_paths,
        "center_crop": args.center_crop,
        "truth": truth,
        "astroalign": astroalign_result,
        "gpwbpp_cuda_matrix_warp_from_astroalign": gpu_matrix_result,
        "gpwbpp_cuda": gpu_result,
        "gpwbpp_cuda_subpixel": gpu_subpixel_result,
        "gpwbpp_cuda_ncc_subpixel": gpu_ncc_subpixel_result,
        "gpwbpp_cuda_resident_ncc_subpixel": gpu_resident_result,
        "gpwbpp_cuda_resident_matrix_warp_from_astroalign": gpu_resident_matrix_result,
        "gpwbpp_cuda_catalog": gpu_catalog_result,
        "speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_result["elapsed_s"]
        if gpu_result["elapsed_s"] > 0.0
        else None,
        "matrix_warp_speedup_vs_astroalign_apply_transform": astroalign_result["apply_elapsed_s"]
        / gpu_matrix_result["elapsed_s"]
        if gpu_matrix_result["elapsed_s"] > 0.0
        else None,
        "astroalign_find_plus_gpu_matrix_warp_elapsed_s": astroalign_result["find_elapsed_s"]
        + gpu_matrix_result["elapsed_s"],
        "astroalign_find_plus_gpu_matrix_warp_speedup_vs_astroalign": astroalign_result["elapsed_s"]
        / (astroalign_result["find_elapsed_s"] + gpu_matrix_result["elapsed_s"])
        if (astroalign_result["find_elapsed_s"] + gpu_matrix_result["elapsed_s"]) > 0.0
        else None,
        "catalog_speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_catalog_result["elapsed_s"]
        if gpu_catalog_result["elapsed_s"] > 0.0
        else None,
        "subpixel_speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_subpixel_result["elapsed_s"]
        if gpu_subpixel_result["elapsed_s"] > 0.0
        else None,
        "ncc_subpixel_speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_ncc_subpixel_result["elapsed_s"]
        if gpu_ncc_subpixel_result["elapsed_s"] > 0.0
        else None,
        "resident_device_speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_resident_result["elapsed_s"]
        if gpu_resident_result["elapsed_s"] > 0.0
        else None,
        "resident_upload_plus_device_speedup_vs_astroalign": astroalign_result["elapsed_s"]
        / gpu_resident_result["upload_plus_device_elapsed_s"]
        if gpu_resident_result["upload_plus_device_elapsed_s"] > 0.0
        else None,
        "resident_matrix_device_speedup_vs_astroalign_apply_transform": astroalign_result["apply_elapsed_s"]
        / gpu_resident_matrix_result["elapsed_s"]
        if gpu_resident_matrix_result["elapsed_s"] > 0.0
        else None,
        "resident_matrix_upload_plus_device_speedup_vs_astroalign_apply_transform": astroalign_result[
            "apply_elapsed_s"
        ]
        / gpu_resident_matrix_result["upload_plus_device_elapsed_s"]
        if gpu_resident_matrix_result["upload_plus_device_elapsed_s"] > 0.0
        else None,
        "cuda_devices": devices,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
