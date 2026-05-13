from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
from astropy.io import fits

from gpwbpp.gpu.registration import (
    refine_matrix_translation_candidates_with_metrics_f32,
    register_triangle_descriptor_similarity_f32,
)
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


def _diff_on_common_valid_pixels(
    candidate: np.ndarray,
    candidate_valid: np.ndarray,
    reference: np.ndarray,
    reference_valid: np.ndarray,
) -> dict[str, Any]:
    mask = (
        np.asarray(candidate_valid, dtype=bool)
        & np.asarray(reference_valid, dtype=bool)
        & np.isfinite(candidate)
        & np.isfinite(reference)
    )
    valid_pixels = int(np.sum(mask))
    if valid_pixels == 0:
        return {
            "valid_pixels": 0,
            "mean_diff": None,
            "median_abs_diff": None,
            "p95_abs_diff": None,
            "p99_abs_diff": None,
            "rms_diff": None,
            "max_abs_diff": None,
        }
    diff = np.asarray(candidate[mask], dtype=np.float64) - np.asarray(reference[mask], dtype=np.float64)
    abs_diff = np.abs(diff)
    return {
        "valid_pixels": valid_pixels,
        "mean_diff": float(np.mean(diff)),
        "median_abs_diff": float(np.median(abs_diff)),
        "p95_abs_diff": float(np.percentile(abs_diff, 95)),
        "p99_abs_diff": float(np.percentile(abs_diff, 99)),
        "rms_diff": float(np.sqrt(np.mean(diff * diff))),
        "max_abs_diff": float(np.max(abs_diff)),
    }


def _similarity_matrix_terms(matrix: np.ndarray) -> dict[str, float]:
    m = np.asarray(matrix, dtype=np.float64)
    return {
        "dx": float(m[0, 2]),
        "dy": float(m[1, 2]),
        "scale": float(np.sqrt(m[0, 0] * m[0, 0] + m[1, 0] * m[1, 0])),
        "rotation_rad": float(np.arctan2(m[1, 0], m[0, 0])),
    }


def _agreement_vs_astroalign(
    candidate_matrix: np.ndarray,
    astroalign_matrix: np.ndarray,
    output_diff: dict[str, Any],
) -> dict[str, Any]:
    candidate = _similarity_matrix_terms(candidate_matrix)
    reference = _similarity_matrix_terms(astroalign_matrix)
    translation_delta = float(
        np.hypot(candidate["dx"] - reference["dx"], candidate["dy"] - reference["dy"])
    )
    scale_delta = float(abs(candidate["scale"] - reference["scale"]))
    rotation_delta = float(abs(candidate["rotation_rad"] - reference["rotation_rad"]))
    matrix_max_abs_delta = float(
        np.max(np.abs(np.asarray(candidate_matrix, dtype=np.float64) - np.asarray(astroalign_matrix, dtype=np.float64)))
    )
    rms_diff = output_diff.get("rms_diff")
    median_abs_diff = output_diff.get("median_abs_diff")
    matrix_passed = (
        translation_delta <= 0.5
        and scale_delta <= 1.0e-3
        and rotation_delta <= 1.0e-3
    )
    output_passed = rms_diff is not None and float(rms_diff) <= 55.0
    passed = matrix_passed and output_passed
    return {
        "passed": bool(passed),
        "strict_matrix_passed": bool(matrix_passed),
        "output_passed": bool(output_passed),
        "translation_delta_px": translation_delta,
        "scale_delta": scale_delta,
        "rotation_delta_rad": rotation_delta,
        "matrix_max_abs_delta": matrix_max_abs_delta,
        "output_median_abs_diff": median_abs_diff,
        "output_rms_diff": rms_diff,
        "criteria": {
            "translation_delta_px_max": 0.5,
            "scale_delta_max": 1.0e-3,
            "rotation_delta_rad_max": 1.0e-3,
            "output_rms_diff_max": 55.0,
        },
    }


def _method_agreement_summary(
    payload: dict[str, Any],
    *,
    method_key: str,
    agreement_key: str,
    speedup_key: str,
    upload_speedup_key: str | None = None,
) -> dict[str, Any]:
    method = payload[method_key]
    agreement = payload[agreement_key]
    return {
        "method": method_key,
        "strict_matrix_and_output_passed": bool(agreement["passed"]),
        "strict_matrix_passed": bool(agreement["strict_matrix_passed"]),
        "output_passed": bool(agreement["output_passed"]),
        "speedup_vs_astroalign": payload.get(speedup_key),
        "upload_inclusive_speedup_vs_astroalign": None
        if upload_speedup_key is None
        else payload.get(upload_speedup_key),
        "elapsed_s": method.get("elapsed_s"),
        "device_elapsed_s": method.get("device_elapsed_s"),
        "selected_seed_rank": method.get("selected_seed_rank"),
        "selected_seed_inliers": method.get("selected_seed_inliers"),
        "translation_delta_px": agreement.get("translation_delta_px"),
        "output_rms_diff": agreement.get("output_rms_diff"),
    }


def _best_alignment_summary(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        _method_agreement_summary(
            payload,
            method_key="gpwbpp_cuda_catalog_similarity",
            agreement_key="catalog_similarity_agreement_vs_astroalign",
            speedup_key="catalog_similarity_speedup_vs_astroalign",
        ),
        _method_agreement_summary(
            payload,
            method_key="gpwbpp_cuda_catalog_similarity_pixel_refined",
            agreement_key="catalog_similarity_pixel_refined_agreement_vs_astroalign",
            speedup_key="catalog_similarity_pixel_refined_speedup_vs_astroalign",
        ),
        _method_agreement_summary(
            payload,
            method_key="gpwbpp_cuda_resident_catalog_similarity_pixel_refined",
            agreement_key="resident_catalog_similarity_pixel_refined_agreement_vs_astroalign",
            speedup_key="resident_catalog_similarity_pixel_refined_algorithm_speedup_vs_astroalign",
            upload_speedup_key="resident_catalog_similarity_pixel_refined_upload_plus_algorithm_speedup_vs_astroalign",
        ),
        _method_agreement_summary(
            payload,
            method_key="gpwbpp_cuda_triangle_descriptor_similarity",
            agreement_key="triangle_descriptor_similarity_agreement_vs_astroalign",
            speedup_key="triangle_descriptor_similarity_speedup_vs_astroalign",
        ),
    ]

    strict = [item for item in candidates if item["strict_matrix_and_output_passed"]]
    output_consistent = [item for item in candidates if item["output_passed"]]

    def speed_key(item: dict[str, Any]) -> float:
        speedup = item.get("speedup_vs_astroalign")
        return float(speedup) if speedup is not None and np.isfinite(float(speedup)) else -1.0

    return {
        "strict_matrix_and_output_best": max(strict, key=speed_key) if strict else None,
        "output_consistent_best": max(output_consistent, key=speed_key) if output_consistent else None,
        "candidates": candidates,
        "note": (
            "strict_matrix_and_output_passed requires <=0.5 px translation delta versus astroalign; "
            "output_passed only requires the aligned output RMS difference to stay within the benchmark tolerance."
        ),
    }


def _astroalign_run_with_output(
    reference: np.ndarray,
    moving: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    import astroalign as aa

    t0 = time.perf_counter()
    transform, control_points = aa.find_transform(moving, reference)
    find_elapsed = time.perf_counter() - t0
    t1 = time.perf_counter()
    aligned, footprint = aa.apply_transform(transform, moving, reference, fill_value=0.0)
    apply_elapsed = time.perf_counter() - t1
    params = np.asarray(transform.params, dtype=np.float64)
    moving_points = np.asarray(control_points[0], dtype=np.float32) if control_points else np.empty((0, 2), dtype=np.float32)
    reference_points = (
        np.asarray(control_points[1], dtype=np.float32) if control_points else np.empty((0, 2), dtype=np.float32)
    )
    invalid = np.asarray(footprint, dtype=bool)
    aligned_f32 = np.asarray(aligned, dtype=np.float32)
    valid = ~invalid if invalid.shape == reference.shape else np.isfinite(aligned_f32)
    result = {
        "elapsed_s": find_elapsed + apply_elapsed,
        "find_elapsed_s": find_elapsed,
        "apply_elapsed_s": apply_elapsed,
        "dx": float(params[0, 2]),
        "dy": float(params[1, 2]),
        "matrix": params.tolist(),
        "rms": _rms(reference, aligned_f32, valid),
        "matched_control_points": int(len(control_points[0])) if control_points else 0,
    }
    return result, aligned_f32, valid, moving_points, reference_points


def _astroalign_run(reference: np.ndarray, moving: np.ndarray) -> dict[str, Any]:
    return _astroalign_run_with_output(reference, moving)[0]


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


def _gpu_matrix_warp_run_with_output(
    reference: np.ndarray,
    moving: np.ndarray,
    matrix: Any,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    t0 = time.perf_counter()
    aligned, coverage = gpwbpp_cuda.warp_matrix_bilinear_f32(moving, matrix, 0.0)
    elapsed = time.perf_counter() - t0
    valid = coverage > 0.0
    result = {
        "elapsed_s": elapsed,
        "matrix": np.asarray(matrix, dtype=np.float64).tolist(),
        "coverage_pixels": int(np.sum(valid)),
        "model": "cuda_matrix_bilinear_warp_from_external_transform",
        "rms": _rms(reference, aligned, valid),
    }
    return result, np.asarray(aligned, dtype=np.float32), valid


def _gpu_matrix_warp_run(reference: np.ndarray, moving: np.ndarray, matrix: Any) -> dict[str, Any]:
    return _gpu_matrix_warp_run_with_output(reference, moving, matrix)[0]


def _gpu_similarity_fit_from_pairs_run(
    reference: np.ndarray,
    moving: np.ndarray,
    moving_points: np.ndarray,
    reference_points: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    if not hasattr(gpwbpp_cuda, "estimate_similarity_from_pairs_f32"):
        raise RuntimeError("native CUDA backend lacks estimate_similarity_from_pairs_f32")
    if len(moving_points) == 0 or len(reference_points) == 0:
        raise RuntimeError("cannot fit GPU similarity transform without matched control points")

    t0 = time.perf_counter()
    fit = gpwbpp_cuda.estimate_similarity_from_pairs_f32(
        reference_points[:, 0],
        reference_points[:, 1],
        moving_points[:, 0],
        moving_points[:, 1],
    )
    fit_elapsed = time.perf_counter() - t0
    matrix = np.asarray(fit["matrix"], dtype=np.float64)
    t1 = time.perf_counter()
    aligned, coverage = gpwbpp_cuda.warp_matrix_bilinear_f32(moving, matrix, 0.0)
    warp_elapsed = time.perf_counter() - t1
    valid = coverage > 0.0
    result = {
        "elapsed_s": fit_elapsed + warp_elapsed,
        "fit_elapsed_s": fit_elapsed,
        "warp_elapsed_s": warp_elapsed,
        "matrix": matrix.tolist(),
        "scale": float(fit["scale"]),
        "rotation_rad": float(fit["rotation_rad"]),
        "fit_rms_px": float(fit["rms_px"]),
        "valid_pairs": int(fit["valid_pairs"]),
        "input_pairs": int(fit["input_pairs"]),
        "fit_status": str(fit["status"]),
        "fit_model": str(fit["model"]),
        "coverage_pixels": int(np.sum(valid)),
        "model": "cuda_similarity_fit_from_astroalign_matches_then_matrix_warp",
        "rms": _rms(reference, aligned, valid),
    }
    return result, np.asarray(aligned, dtype=np.float32), valid


def _gpu_matrix_metrics_run(
    reference: np.ndarray,
    moving: np.ndarray,
    matrix: Any,
    sample_stride: int,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    metrics = gpwbpp_cuda.matrix_alignment_metrics_f32(reference, moving, matrix, sample_stride)
    elapsed = time.perf_counter() - t0
    return {**metrics, "elapsed_s": elapsed}


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


def _gpu_resident_matrix_metrics_run(
    reference: np.ndarray,
    moving: np.ndarray,
    matrix: Any,
    sample_stride: int,
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
    metrics = stack.matrix_alignment_metrics_to_reference(0, 1, matrix, sample_stride)
    device_elapsed = time.perf_counter() - t1
    return {
        **metrics,
        "elapsed_s": device_elapsed,
        "upload_elapsed_s": upload_elapsed,
        "upload_plus_device_elapsed_s": upload_elapsed + device_elapsed,
        "bytes_allocated": int(stack.bytes_allocated),
    }


def _finite_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(result):
        return None
    return result


def _select_star_guarded_seed(
    seed_metrics: list[dict[str, Any]],
    pixel_selected_index: int,
) -> tuple[int, dict[str, Any]]:
    pixel_selected_index = int(pixel_selected_index)
    if pixel_selected_index < 0 or pixel_selected_index >= len(seed_metrics):
        pixel_selected_index = 0

    star_core_candidates: list[tuple[int, dict[str, Any]]] = []
    for index, seed in enumerate(seed_metrics):
        star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
        if star_core_rms is None:
            continue
        star_core_candidates.append((index, seed))

    if star_core_candidates:
        inlier_values = [
            int(seed["seed_inliers"])
            for _, seed in star_core_candidates
            if seed.get("seed_inliers") is not None
        ]
        if inlier_values:
            max_inliers = max(inlier_values)
            min_inliers = max(0, max_inliers - 2)
            eligible = [
                (index, seed)
                for index, seed in star_core_candidates
                if seed.get("seed_inliers") is None or int(seed["seed_inliers"]) >= min_inliers
            ]
        else:
            max_inliers = None
            min_inliers = None
            eligible = star_core_candidates

        def star_core_key(item: tuple[int, dict[str, Any]]) -> tuple[float, int, float, int]:
            index, seed = item
            star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
            inliers = int(seed["seed_inliers"]) if seed.get("seed_inliers") is not None else -1
            seed_rms = _finite_float_or_none(seed.get("seed_rms_px"))
            return (
                float("inf") if star_core_rms is None else star_core_rms,
                -inliers,
                float("inf") if seed_rms is None else seed_rms,
                index,
            )

        selected_index, _selected = min(eligible, key=star_core_key)
        pixel_seed = seed_metrics[pixel_selected_index]
        return selected_index, {
            "status": "kept_star_core_metric"
            if selected_index == pixel_selected_index
            else "replaced_pixel_metric_with_star_core_metric",
            "pixel_selected_index": pixel_selected_index,
            "pixel_selected_seed_rank": int(pixel_seed.get("seed_rank", pixel_selected_index)),
            "pixel_selected_seed_inliers": pixel_seed.get("seed_inliers"),
            "pixel_selected_seed_rms_px": pixel_seed.get("seed_rms_px"),
            "selected_index": selected_index,
            "star_max_inliers": None if max_inliers is None else int(max_inliers),
            "star_min_inliers_for_core_metric": None if min_inliers is None else int(min_inliers),
            "eligible_seed_count": len(eligible),
            "selection_key": "star_core_rms_with_two_inlier_slack",
        }

    star_candidates: list[tuple[int, dict[str, Any]]] = []
    for index, seed in enumerate(seed_metrics):
        inliers = seed.get("seed_inliers")
        rms_px = _finite_float_or_none(seed.get("seed_rms_px"))
        if inliers is None or rms_px is None:
            continue
        star_candidates.append((index, seed))

    if not star_candidates:
        return pixel_selected_index, {
            "status": "pixel_metric_only_no_star_metadata",
            "pixel_selected_index": pixel_selected_index,
            "selected_index": pixel_selected_index,
            "eligible_seed_count": 0,
            "selection_key": "pixel_metric_rms",
        }

    max_inliers = max(int(seed["seed_inliers"]) for _, seed in star_candidates)
    eligible = [(index, seed) for index, seed in star_candidates if int(seed["seed_inliers"]) == max_inliers]

    def key(item: tuple[int, dict[str, Any]]) -> tuple[float, float, int]:
        index, seed = item
        metric_rms = _finite_float_or_none(seed.get("metrics", {}).get("rms"))
        seed_rms = _finite_float_or_none(seed.get("seed_rms_px"))
        return (
            float("inf") if metric_rms is None else metric_rms,
            float("inf") if seed_rms is None else seed_rms,
            index,
        )

    selected_index, _selected = min(eligible, key=key)
    pixel_seed = seed_metrics[pixel_selected_index]
    return selected_index, {
        "status": "kept_pixel_metric" if selected_index == pixel_selected_index else "replaced_pixel_metric",
        "pixel_selected_index": pixel_selected_index,
        "pixel_selected_seed_rank": int(pixel_seed.get("seed_rank", pixel_selected_index)),
        "pixel_selected_seed_inliers": pixel_seed.get("seed_inliers"),
        "pixel_selected_seed_rms_px": pixel_seed.get("seed_rms_px"),
        "selected_index": selected_index,
        "star_max_inliers": int(max_inliers),
        "eligible_seed_count": len(eligible),
        "selection_key": "max_seed_inliers_then_pixel_rms_then_seed_rms",
    }


def _star_core_sample(reference: np.ndarray, threshold_sigma: float = 6.0, max_points: int = 200_000) -> dict[str, Any]:
    threshold = _adaptive_star_threshold(reference, threshold_sigma)
    mask = np.isfinite(reference) & (reference > threshold)
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return {
            "x": np.empty(0, dtype=np.float64),
            "y": np.empty(0, dtype=np.float64),
            "values": np.empty(0, dtype=np.float64),
            "threshold": float(threshold),
            "available_pixels": 0,
            "sampled_pixels": 0,
        }
    if xs.size > max_points:
        take = np.linspace(0, xs.size - 1, max_points, dtype=np.int64)
        xs = xs[take]
        ys = ys[take]
    values = reference[ys, xs].astype(np.float64, copy=False)
    return {
        "x": xs.astype(np.float64, copy=False),
        "y": ys.astype(np.float64, copy=False),
        "values": values,
        "threshold": float(threshold),
        "available_pixels": int(mask.sum()),
        "sampled_pixels": int(xs.size),
    }


def _matrix_star_core_metric(
    moving: np.ndarray,
    matrix: Any,
    sample: dict[str, Any],
) -> dict[str, Any]:
    x = np.asarray(sample["x"], dtype=np.float64)
    y = np.asarray(sample["y"], dtype=np.float64)
    reference_values = np.asarray(sample["values"], dtype=np.float64)
    if x.size == 0:
        return {"rms": None, "mean_abs_diff": None, "valid_pixels": 0}

    inverse = np.linalg.inv(np.asarray(matrix, dtype=np.float64).reshape(3, 3))
    sx = inverse[0, 0] * x + inverse[0, 1] * y + inverse[0, 2]
    sy = inverse[1, 0] * x + inverse[1, 1] * y + inverse[1, 2]
    height, width = moving.shape
    valid = (sx >= 0.0) & (sx < width - 1) & (sy >= 0.0) & (sy < height - 1)
    if not np.any(valid):
        return {"rms": None, "mean_abs_diff": None, "valid_pixels": 0}

    sxv = sx[valid]
    syv = sy[valid]
    x0 = np.floor(sxv).astype(np.int64)
    y0 = np.floor(syv).astype(np.int64)
    fx = sxv - x0
    fy = syv - y0
    moving64 = moving.astype(np.float64, copy=False)
    sampled = (
        moving64[y0, x0] * (1.0 - fx) * (1.0 - fy)
        + moving64[y0, x0 + 1] * fx * (1.0 - fy)
        + moving64[y0 + 1, x0] * (1.0 - fx) * fy
        + moving64[y0 + 1, x0 + 1] * fx * fy
    )
    diff = reference_values[valid] - sampled
    return {
        "rms": float(np.sqrt(np.mean(diff * diff))),
        "mean_abs_diff": float(np.mean(np.abs(diff))),
        "valid_pixels": int(diff.size),
    }


def _annotate_star_core_metrics(
    reference: np.ndarray,
    moving: np.ndarray,
    seed_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    t0 = time.perf_counter()
    sample = _star_core_sample(reference)
    for seed in seed_metrics:
        seed["star_core_metric"] = _matrix_star_core_metric(moving, seed["matrix"], sample)
    return {
        "elapsed_s": time.perf_counter() - t0,
        "threshold": float(sample["threshold"]),
        "available_pixels": int(sample["available_pixels"]),
        "sampled_pixels": int(sample["sampled_pixels"]),
        "model": "cpu_star_core_bilinear_metric_for_cuda_candidates",
    }


def _annotate_resident_star_core_metrics(
    stack: Any,
    reference: np.ndarray,
    seed_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    threshold = _adaptive_star_threshold(reference, 6.0)
    matrices = np.asarray([seed["matrix"] for seed in seed_metrics], dtype=np.float32)
    t0 = time.perf_counter()
    result = stack.star_core_metrics_candidates_to_reference(0, 1, matrices, float(threshold))
    elapsed = time.perf_counter() - t0
    candidate_metrics = list(result["candidate_metrics"])
    for item in candidate_metrics:
        local_seed_index = int(item["seed_index"])
        seed_metrics[local_seed_index]["star_core_metric"] = dict(item["metrics"])
    available_pixels = 0
    for item in candidate_metrics:
        metrics = dict(item["metrics"])
        available_pixels = max(available_pixels, int(metrics.get("valid_pixels", 0)))
    return {
        "elapsed_s": elapsed,
        "threshold": float(result["threshold"]),
        "available_pixels": int(available_pixels),
        "sampled_pixels": int(result["sampled_pixels"]),
        "model": str(result["model"]),
    }


def _select_star_core_preselected_seed_indices(
    seed_metrics: list[dict[str, Any]],
    max_count: int,
) -> tuple[list[int], dict[str, Any]]:
    max_count = int(max_count)
    if max_count <= 0 or max_count >= len(seed_metrics):
        return list(range(len(seed_metrics))), {
            "enabled": False,
            "requested_top_k": max_count,
            "input_seed_count": len(seed_metrics),
            "selected_seed_count": len(seed_metrics),
            "selected_seed_indices": list(range(len(seed_metrics))),
            "selection_key": "disabled",
        }

    star_core_candidates: list[tuple[int, dict[str, Any]]] = []
    for index, seed in enumerate(seed_metrics):
        star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
        if star_core_rms is not None:
            star_core_candidates.append((index, seed))

    if not star_core_candidates:
        selected = list(range(min(max_count, len(seed_metrics))))
        return selected, {
            "enabled": True,
            "requested_top_k": max_count,
            "input_seed_count": len(seed_metrics),
            "selected_seed_count": len(selected),
            "selected_seed_indices": selected,
            "selection_key": "first_n_no_star_core_metric",
        }

    inlier_values = [
        int(seed["seed_inliers"])
        for _, seed in star_core_candidates
        if seed.get("seed_inliers") is not None
    ]
    if inlier_values:
        max_inliers = max(inlier_values)
        min_inliers = max(0, max_inliers - 2)
        eligible = [
            (index, seed)
            for index, seed in star_core_candidates
            if seed.get("seed_inliers") is None or int(seed["seed_inliers"]) >= min_inliers
        ]
    else:
        max_inliers = None
        min_inliers = None
        eligible = star_core_candidates

    def key(item: tuple[int, dict[str, Any]]) -> tuple[float, int, float, int]:
        index, seed = item
        star_core_rms = _finite_float_or_none(seed.get("star_core_metric", {}).get("rms"))
        inliers = int(seed["seed_inliers"]) if seed.get("seed_inliers") is not None else -1
        seed_rms = _finite_float_or_none(seed.get("seed_rms_px"))
        return (
            float("inf") if star_core_rms is None else star_core_rms,
            -inliers,
            float("inf") if seed_rms is None else seed_rms,
            index,
        )

    selected_set: set[int] = {0}
    for index, _seed in sorted(eligible, key=key):
        selected_set.add(index)
        if len(selected_set) >= max_count:
            break
    if len(selected_set) < max_count:
        for index, _seed in sorted(star_core_candidates, key=key):
            selected_set.add(index)
            if len(selected_set) >= max_count:
                break

    selected = sorted(selected_set)
    return selected, {
        "enabled": True,
        "requested_top_k": max_count,
        "input_seed_count": len(seed_metrics),
        "selected_seed_count": len(selected),
        "selected_seed_indices": selected,
        "star_max_inliers": None if max_inliers is None else int(max_inliers),
        "star_min_inliers_for_core_metric": None if min_inliers is None else int(min_inliers),
        "eligible_seed_count": len(eligible),
        "selection_key": "pre_refine_star_core_rms_with_two_inlier_slack",
    }


def _gpu_catalog_similarity_pixel_refine_run(
    reference: np.ndarray,
    moving: np.ndarray,
    matrix: Any,
    seed_candidates: list[dict[str, Any]] | None,
    refit_inliers: int | None,
    refit_rms_px: float | None,
    search_radius_px: float,
    coarse_step_px: float,
    fine_radius_px: float,
    fine_step_px: float,
    coarse_sample_stride: int,
    final_sample_stride: int,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    seeds: list[dict[str, Any]] = [
        {
            "seed_rank": 0,
            "seed_source": "catalog_similarity_refit",
            "candidate_index": None,
            "inliers": None if refit_inliers is None else int(refit_inliers),
            "rms_px": _finite_float_or_none(refit_rms_px),
            "matrix": np.asarray(matrix, dtype=np.float64).tolist(),
        }
    ]
    for rank, candidate in enumerate(seed_candidates or [], start=1):
        seeds.append(
            {
                "seed_rank": rank,
                "seed_source": "catalog_similarity_top_candidate",
                "candidate_index": int(candidate["candidate_index"]),
                "inliers": int(candidate["inliers"]),
                "rms_px": float(candidate["rms_px"]),
                "matrix": np.asarray(candidate["matrix"], dtype=np.float64).tolist(),
            }
        )

    seed_matrices = [np.asarray(seed["matrix"], dtype=np.float32) for seed in seeds]
    t0 = time.perf_counter()
    refinement = refine_matrix_translation_candidates_with_metrics_f32(
        reference,
        moving,
        np.asarray(seed_matrices, dtype=np.float32),
        search_radius_px=search_radius_px,
        coarse_step_px=coarse_step_px,
        fine_radius_px=fine_radius_px,
        fine_step_px=fine_step_px,
        coarse_sample_stride=coarse_sample_stride,
        final_sample_stride=final_sample_stride,
    )
    refine_elapsed = time.perf_counter() - t0
    seed_metrics: list[dict[str, Any]] = []
    for seed_result in refinement["seed_results"]:
        seed_index = int(seed_result["seed_index"])
        seed = seeds[seed_index]
        seed_metrics.append(
            {
                "seed_index": seed_index,
                "seed_rank": int(seed["seed_rank"]),
                "seed_source": str(seed["seed_source"]),
                "candidate_index": seed["candidate_index"],
                "seed_inliers": seed["inliers"],
                "seed_rms_px": seed["rms_px"],
                "dx_correction": float(seed_result["dx_correction"]),
                "dy_correction": float(seed_result["dy_correction"]),
                "metrics": dict(seed_result["metrics"]),
                "matrix": np.asarray(seed_result["matrix"], dtype=np.float64).tolist(),
            }
        )
    star_core_metric_summary = _annotate_star_core_metrics(reference, moving, seed_metrics)
    pixel_selected_index = int(refinement["selected_index"])
    selected_metric_index, star_guard = _select_star_guarded_seed(seed_metrics, pixel_selected_index)
    selected_seed = seed_metrics[selected_metric_index]
    selected_matrix = np.asarray(selected_seed["matrix"], dtype=np.float32)
    selection_elapsed = float(star_core_metric_summary["elapsed_s"])
    refinement = {
        **refinement,
        "matrix": selected_matrix.tolist(),
        "metrics": dict(selected_seed["metrics"]),
        "selected_index": int(selected_seed["seed_index"]),
        "pixel_metric_selected_index": pixel_selected_index,
        "star_guard": star_guard,
    }
    t1 = time.perf_counter()
    aligned, valid = gpwbpp_cuda.warp_matrix_bilinear_f32(moving, refinement["matrix"], 0.0)
    warp_elapsed = time.perf_counter() - t1
    device_elapsed = refine_elapsed + warp_elapsed
    algorithm_elapsed = device_elapsed + selection_elapsed
    result = {
        **refinement,
        "elapsed_s": algorithm_elapsed,
        "device_elapsed_s": device_elapsed,
        "refine_elapsed_s": refine_elapsed,
        "selection_elapsed_s": selection_elapsed,
        "warp_elapsed_s": warp_elapsed,
        "seed_selection_model": "catalog_topk_star_guarded_pixel_metric",
        "seed_count": len(seeds),
        "selected_seed_index": int(selected_seed["seed_index"]),
        "selected_seed_rank": int(selected_seed["seed_rank"]),
        "selected_seed_source": str(selected_seed["seed_source"]),
        "selected_seed_candidate_index": selected_seed["candidate_index"],
        "selected_seed_inliers": selected_seed["seed_inliers"],
        "selected_seed_rms_px": selected_seed["seed_rms_px"],
        "pixel_metric_selected_index": pixel_selected_index,
        "star_guard": star_guard,
        "star_core_metric_summary": star_core_metric_summary,
        "seed_metrics": seed_metrics,
        "coverage_pixels": int(np.sum(valid > 0.0)),
        "rms": _rms(reference, aligned, valid > 0.0),
    }
    return result, np.asarray(aligned, dtype=np.float32), np.asarray(valid > 0.0, dtype=bool)


def _gpu_resident_catalog_similarity_pixel_refine_run(
    reference: np.ndarray,
    moving: np.ndarray,
    matrix: Any,
    seed_candidates: list[dict[str, Any]] | None,
    refit_inliers: int | None,
    refit_rms_px: float | None,
    search_radius_px: float,
    coarse_step_px: float,
    fine_radius_px: float,
    fine_step_px: float,
    coarse_sample_stride: int,
    final_sample_stride: int,
    star_core_preselect_top_k: int = 0,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    if not hasattr(gpwbpp_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("native CUDA backend lacks ResidentCalibratedStack")

    seeds: list[dict[str, Any]] = [
        {
            "seed_rank": 0,
            "seed_source": "catalog_similarity_refit",
            "candidate_index": None,
            "inliers": None if refit_inliers is None else int(refit_inliers),
            "rms_px": _finite_float_or_none(refit_rms_px),
            "matrix": np.asarray(matrix, dtype=np.float64).tolist(),
        }
    ]
    for rank, candidate in enumerate(seed_candidates or [], start=1):
        seeds.append(
            {
                "seed_rank": rank,
                "seed_source": "catalog_similarity_top_candidate",
                "candidate_index": int(candidate["candidate_index"]),
                "inliers": int(candidate["inliers"]),
                "rms_px": float(candidate["rms_px"]),
                "matrix": np.asarray(candidate["matrix"], dtype=np.float64).tolist(),
            }
        )
    t0 = time.perf_counter()
    stack = gpwbpp_cuda.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    upload_elapsed = time.perf_counter() - t0

    pre_refine_metric_summary: dict[str, Any] | None = None
    preselection: dict[str, Any] = {
        "enabled": False,
        "requested_top_k": int(star_core_preselect_top_k),
        "input_seed_count": len(seeds),
        "selected_seed_count": len(seeds),
        "selected_seed_indices": list(range(len(seeds))),
        "selection_key": "disabled",
    }
    selected_seed_indices = list(range(len(seeds)))
    if 0 < int(star_core_preselect_top_k) < len(seeds):
        prescreen_seed_metrics: list[dict[str, Any]] = [
            {
                "seed_index": index,
                "seed_rank": int(seed["seed_rank"]),
                "seed_source": str(seed["seed_source"]),
                "candidate_index": seed["candidate_index"],
                "seed_inliers": seed["inliers"],
                "seed_rms_px": seed["rms_px"],
                "matrix": np.asarray(seed["matrix"], dtype=np.float64).tolist(),
            }
            for index, seed in enumerate(seeds)
        ]
        pre_refine_metric_summary = _annotate_resident_star_core_metrics(
            stack,
            reference,
            prescreen_seed_metrics,
        )
        selected_seed_indices, preselection = _select_star_core_preselected_seed_indices(
            prescreen_seed_metrics,
            int(star_core_preselect_top_k),
        )
        preselection["pre_refine_metric_summary"] = pre_refine_metric_summary
        preselection["pre_refine_seed_metrics"] = prescreen_seed_metrics

    seed_matrices = [np.asarray(seeds[index]["matrix"], dtype=np.float32) for index in selected_seed_indices]

    t1 = time.perf_counter()
    refinement = stack.refine_matrix_translation_candidates_to_reference(
        0,
        1,
        np.asarray(seed_matrices, dtype=np.float32),
        search_radius_px=search_radius_px,
        coarse_step_px=coarse_step_px,
        fine_radius_px=fine_radius_px,
        fine_step_px=fine_step_px,
        coarse_sample_stride=coarse_sample_stride,
        final_sample_stride=final_sample_stride,
    )
    refine_elapsed = time.perf_counter() - t1

    seed_metrics: list[dict[str, Any]] = []
    for seed_result in refinement["seed_results"]:
        refine_seed_index = int(seed_result["seed_index"])
        seed_index = int(selected_seed_indices[refine_seed_index])
        seed = seeds[seed_index]
        seed_metrics.append(
            {
                "seed_index": seed_index,
                "refine_seed_index": refine_seed_index,
                "seed_rank": int(seed["seed_rank"]),
                "seed_source": str(seed["seed_source"]),
                "candidate_index": seed["candidate_index"],
                "seed_inliers": seed["inliers"],
                "seed_rms_px": seed["rms_px"],
                "dx_correction": float(seed_result["dx_correction"]),
                "dy_correction": float(seed_result["dy_correction"]),
                "metrics": dict(seed_result["metrics"]),
                "matrix": np.asarray(seed_result["matrix"], dtype=np.float64).tolist(),
            }
        )
    star_core_metric_summary = _annotate_resident_star_core_metrics(stack, reference, seed_metrics)
    pixel_selected_index = int(refinement["selected_index"])
    selected_metric_index, star_guard = _select_star_guarded_seed(seed_metrics, pixel_selected_index)
    selected_seed = seed_metrics[selected_metric_index]
    selected_matrix = np.asarray(selected_seed["matrix"], dtype=np.float32)
    selection_elapsed = float(star_core_metric_summary["elapsed_s"])
    refinement = {
        **refinement,
        "matrix": selected_matrix.tolist(),
        "metrics": dict(selected_seed["metrics"]),
        "selected_index": int(selected_seed["seed_index"]),
        "pixel_metric_selected_index": pixel_selected_index,
        "pixel_metric_selected_seed_index": int(seed_metrics[pixel_selected_index]["seed_index"]),
        "star_guard": star_guard,
    }

    t2 = time.perf_counter()
    stack.apply_matrix_bilinear_frame(1, refinement["matrix"], np.nan)
    warp_elapsed = time.perf_counter() - t2

    t3 = time.perf_counter()
    aligned, weight_map = stack.integrate_mean(np.array([0.0, 1.0], dtype=np.float32))
    inspection_elapsed = time.perf_counter() - t3
    valid = weight_map > 0.0
    device_elapsed = refine_elapsed + warp_elapsed
    algorithm_elapsed = device_elapsed + selection_elapsed
    result = {
        **refinement,
        "elapsed_s": algorithm_elapsed,
        "device_elapsed_s": device_elapsed,
        "upload_elapsed_s": upload_elapsed,
        "inspection_download_elapsed_s": inspection_elapsed,
        "upload_plus_device_elapsed_s": upload_elapsed + device_elapsed,
        "upload_plus_algorithm_elapsed_s": upload_elapsed + algorithm_elapsed,
        "refine_elapsed_s": refine_elapsed,
        "selection_elapsed_s": selection_elapsed,
        "warp_elapsed_s": warp_elapsed,
        "seed_selection_model": "resident_catalog_topk_star_guarded_pixel_metric",
        "seed_count": len(seeds),
        "refined_seed_count": len(selected_seed_indices),
        "seed_preselection": preselection,
        "selected_seed_index": int(selected_seed["seed_index"]),
        "selected_refine_seed_index": int(selected_seed["refine_seed_index"]),
        "selected_seed_rank": int(selected_seed["seed_rank"]),
        "selected_seed_source": str(selected_seed["seed_source"]),
        "selected_seed_candidate_index": selected_seed["candidate_index"],
        "selected_seed_inliers": selected_seed["seed_inliers"],
        "selected_seed_rms_px": selected_seed["seed_rms_px"],
        "pixel_metric_selected_index": pixel_selected_index,
        "pixel_metric_selected_seed_index": int(seed_metrics[pixel_selected_index]["seed_index"]),
        "star_guard": star_guard,
        "star_core_metric_summary": star_core_metric_summary,
        "seed_metrics": seed_metrics,
        "coverage_pixels": int(np.sum(valid)),
        "bytes_allocated": int(stack.bytes_allocated),
        "rms": _rms(reference, aligned, valid),
    }
    return result, np.asarray(aligned, dtype=np.float32), np.asarray(valid, dtype=bool)


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


def _gpu_catalog_similarity_run(
    reference: np.ndarray,
    moving: np.ndarray,
    max_stars: int,
    threshold_sigma: float,
    tolerance_px: float,
    min_pair_distance: float,
    min_inliers: int,
    grid_cols: int | None,
    grid_rows: int | None,
    grid_top_cols: int | None,
    grid_top_rows: int | None,
    grid_top_candidates_per_cell: int,
    nms_scan_candidates: int | None,
    nms_min_separation_px: float | None,
    prior_dx: float | None,
    prior_dy: float | None,
    prior_radius_px: float | None,
    min_scale: float | None,
    max_scale: float | None,
    max_abs_rotation_rad: float | None,
    top_k: int,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    if not hasattr(gpwbpp_cuda, "estimate_similarity_from_catalogs_f32"):
        raise RuntimeError("native CUDA backend lacks estimate_similarity_from_catalogs_f32")
    t0 = time.perf_counter()
    reference_threshold = _adaptive_star_threshold(reference, threshold_sigma)
    moving_threshold = _adaptive_star_threshold(moving, threshold_sigma)
    if grid_top_cols is not None and grid_top_rows is not None:
        reference_catalog = gpwbpp_cuda.star_grid_top_nms_candidates_f32(
            reference,
            reference_threshold,
            grid_top_cols,
            grid_top_rows,
            grid_top_candidates_per_cell,
            max_stars,
            32.0 if nms_min_separation_px is None else nms_min_separation_px,
        )
        moving_catalog = gpwbpp_cuda.star_grid_top_nms_candidates_f32(
            moving,
            moving_threshold,
            grid_top_cols,
            grid_top_rows,
            grid_top_candidates_per_cell,
            max_stars,
            32.0 if nms_min_separation_px is None else nms_min_separation_px,
        )
        selection_model = "grid_topk_local_maximum_nms"
    elif grid_cols is not None and grid_rows is not None:
        reference_catalog = gpwbpp_cuda.star_grid_candidates_f32(reference, reference_threshold, grid_cols, grid_rows)
        moving_catalog = gpwbpp_cuda.star_grid_candidates_f32(moving, moving_threshold, grid_cols, grid_rows)
        selection_model = "grid_brightest_local_maximum"
    elif nms_scan_candidates is not None or nms_min_separation_px is not None:
        reference_catalog = gpwbpp_cuda.star_top_nms_candidates_f32(
            reference,
            reference_threshold,
            4096 if nms_scan_candidates is None else nms_scan_candidates,
            max_stars,
            32.0 if nms_min_separation_px is None else nms_min_separation_px,
        )
        moving_catalog = gpwbpp_cuda.star_top_nms_candidates_f32(
            moving,
            moving_threshold,
            4096 if nms_scan_candidates is None else nms_scan_candidates,
            max_stars,
            32.0 if nms_min_separation_px is None else nms_min_separation_px,
        )
        selection_model = "global_top_flux_local_maximum_nms"
    else:
        reference_catalog = gpwbpp_cuda.star_top_candidates_f32(reference, reference_threshold, max_stars)
        moving_catalog = gpwbpp_cuda.star_top_candidates_f32(moving, moving_threshold, max_stars)
        selection_model = "global_top_flux_local_maximum"
    fit = gpwbpp_cuda.estimate_similarity_from_catalogs_f32(
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
        top_k=top_k,
    )
    matrix = np.asarray(fit["matrix"], dtype=np.float64)
    aligned, coverage = gpwbpp_cuda.warp_matrix_bilinear_f32(moving, matrix, 0.0)
    valid = coverage > 0.0
    elapsed = time.perf_counter() - t0
    accepted = fit["status"] == "ok" and int(fit["inliers"]) >= int(min_inliers)
    warnings = [] if accepted else [f"catalog similarity inliers below {int(min_inliers)}"]
    result = {
        "elapsed_s": elapsed,
        "matrix": matrix.tolist(),
        "scale": float(fit["scale"]),
        "rotation_rad": float(fit["rotation_rad"]),
        "rms_px": float(fit["rms_px"]),
        "inliers": int(fit["inliers"]),
        "refined_inliers": int(fit.get("refined_inliers", fit["inliers"])),
        "refit_status": str(fit.get("refit_status", "not_run")),
        "refit_rms_px": float(fit.get("refit_rms_px", fit["rms_px"])),
        "best_candidate_index": int(fit["best_candidate_index"]),
        "candidate_count": int(fit["candidate_count"]),
        "reference_count": int(fit["reference_count"]),
        "moving_count": int(fit["moving_count"]),
        "reference_detected": int(reference_catalog["count"]),
        "moving_detected": int(moving_catalog["count"]),
        "reference_stored": int(reference_catalog["stored_count"]),
        "moving_stored": int(moving_catalog["stored_count"]),
        "reference_threshold": reference_threshold,
        "moving_threshold": moving_threshold,
        "selection_model": selection_model,
        "grid_cols": grid_cols,
        "grid_rows": grid_rows,
        "grid_top_cols": grid_top_cols,
        "grid_top_rows": grid_top_rows,
        "grid_top_candidates_per_cell": grid_top_candidates_per_cell,
        "nms_scan_candidates": nms_scan_candidates,
        "nms_min_separation_px": nms_min_separation_px,
        "tolerance_px": float(tolerance_px),
        "min_pair_distance": float(min_pair_distance),
        "prior_dx": prior_dx,
        "prior_dy": prior_dy,
        "prior_radius_px": prior_radius_px,
        "min_scale": min_scale,
        "max_scale": max_scale,
        "max_abs_rotation_rad": max_abs_rotation_rad,
        "top_k": int(fit.get("top_k", top_k)),
        "top_candidates": list(fit.get("top_candidates", [])),
        "coverage_pixels": int(np.sum(valid)),
        "accepted": accepted,
        "warnings": warnings,
        "fit_status": str(fit["status"]),
        "fit_model": str(fit["model"]),
        "model": "pure_cuda_catalog_similarity_seed_then_matrix_warp",
        "rms": _rms(reference, aligned, valid),
    }
    return result, np.asarray(aligned, dtype=np.float32), valid


def _gpu_triangle_descriptor_similarity_run(
    reference: np.ndarray,
    moving: np.ndarray,
    max_stars: int,
    threshold_sigma: float,
    tolerance_px: float,
    descriptor_radius: float,
    neighbors: int,
    max_descriptors: int,
    min_inliers: int,
    grid_top_cols: int | None,
    grid_top_rows: int | None,
    grid_top_candidates_per_cell: int,
    nms_scan_candidates: int | None,
    nms_min_separation_px: float | None,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if not gpwbpp_cuda.cuda_available():
        raise RuntimeError("native CUDA backend is not available")
    if not hasattr(gpwbpp_cuda, "estimate_similarity_from_triangle_descriptors_f32"):
        raise RuntimeError("native CUDA backend lacks estimate_similarity_from_triangle_descriptors_f32")

    reference_threshold = _adaptive_star_threshold(reference, threshold_sigma)
    moving_threshold = _adaptive_star_threshold(moving, threshold_sigma)
    effective_threshold = min(reference_threshold, moving_threshold)
    t0 = time.perf_counter()
    aligned, coverage, diagnostics = register_triangle_descriptor_similarity_f32(
        reference,
        moving,
        threshold=effective_threshold,
        max_candidates=max_stars,
        neighbors=neighbors,
        max_descriptors=max_descriptors,
        tolerance_px=tolerance_px,
        descriptor_radius=descriptor_radius,
        grid_top_cols=grid_top_cols,
        grid_top_rows=grid_top_rows,
        grid_top_candidates_per_cell=grid_top_candidates_per_cell,
        nms_scan_candidates=nms_scan_candidates,
        nms_min_separation_px=nms_min_separation_px,
    )
    elapsed = time.perf_counter() - t0
    similarity = dict(diagnostics["similarity"])
    matrix = np.asarray(diagnostics["matrix"], dtype=np.float64)
    valid = coverage > 0.0
    accepted = diagnostics["status"] == "ok" and int(similarity["inliers"]) >= int(min_inliers)
    warnings = [] if accepted else [f"triangle descriptor similarity inliers below {int(min_inliers)}"]
    result = {
        "elapsed_s": elapsed,
        "matrix": matrix.tolist(),
        "scale": float(similarity["scale"]),
        "rotation_rad": float(similarity["rotation_rad"]),
        "rms_px": float(similarity["rms_px"]),
        "inliers": int(similarity["inliers"]),
        "best_candidate_index": int(similarity["best_candidate_index"]),
        "candidate_count": int(similarity["candidate_count"]),
        "reference_count": int(similarity["reference_count"]),
        "moving_count": int(similarity["moving_count"]),
        "reference_detected": int(diagnostics["reference_detected"]),
        "moving_detected": int(diagnostics["moving_detected"]),
        "reference_stored": int(diagnostics["reference_stored"]),
        "moving_stored": int(diagnostics["moving_stored"]),
        "reference_descriptor_count": int(diagnostics["reference_descriptor_count"]),
        "moving_descriptor_count": int(diagnostics["moving_descriptor_count"]),
        "reference_threshold": reference_threshold,
        "moving_threshold": moving_threshold,
        "effective_threshold": effective_threshold,
        "threshold_policy": "min(reference_threshold, moving_threshold)",
        "tolerance_px": float(tolerance_px),
        "descriptor_radius": float(descriptor_radius),
        "neighbors": int(neighbors),
        "max_descriptors": int(max_descriptors),
        "grid_top_cols": grid_top_cols,
        "grid_top_rows": grid_top_rows,
        "grid_top_candidates_per_cell": grid_top_candidates_per_cell,
        "nms_scan_candidates": nms_scan_candidates,
        "nms_min_separation_px": nms_min_separation_px,
        "catalog_selector": str(diagnostics["catalog_selector"]),
        "coverage_pixels": int(np.sum(valid)),
        "accepted": accepted,
        "warnings": warnings,
        "fit_status": str(similarity["status"]),
        "fit_model": str(similarity["model"]),
        "model": "pure_cuda_triangle_descriptor_similarity_seed_then_matrix_warp",
        "rms": _rms(reference, aligned, valid),
    }
    return result, np.asarray(aligned, dtype=np.float32), valid


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
    parser.add_argument("--catalog-grid-top-cols", type=int)
    parser.add_argument("--catalog-grid-top-rows", type=int)
    parser.add_argument("--catalog-grid-top-per-cell", type=int, default=4)
    parser.add_argument("--catalog-nms-scan-stars", type=int)
    parser.add_argument("--catalog-nms-min-separation", type=float)
    parser.add_argument("--catalog-prior-radius", type=float)
    parser.add_argument("--catalog-similarity-min-pair-distance", type=float, default=4.0)
    parser.add_argument("--catalog-similarity-min-scale", type=float, default=0.98)
    parser.add_argument("--catalog-similarity-max-scale", type=float, default=1.02)
    parser.add_argument("--catalog-similarity-max-rotation-rad", type=float, default=0.02)
    parser.add_argument(
        "--catalog-similarity-top-k",
        type=int,
        default=0,
        help="Return and pixel-score this many catalog similarity seed candidates in addition to the refit.",
    )
    parser.add_argument("--catalog-pixel-refine-radius", type=float, default=1.0)
    parser.add_argument("--catalog-pixel-refine-coarse-step", type=float, default=0.25)
    parser.add_argument("--catalog-pixel-refine-fine-radius", type=float, default=0.25)
    parser.add_argument("--catalog-pixel-refine-fine-step", type=float, default=0.0625)
    parser.add_argument("--catalog-pixel-refine-coarse-stride", type=int, default=4)
    parser.add_argument("--catalog-pixel-refine-final-stride", type=int, default=1)
    parser.add_argument("--triangle-descriptor-neighbors", type=int, default=5)
    parser.add_argument("--triangle-descriptor-max-descriptors", type=int, default=1200)
    parser.add_argument("--triangle-descriptor-radius", type=float, default=0.1)
    parser.add_argument(
        "--resident-star-core-preselect-top-k",
        type=int,
        default=0,
        help=(
            "Before resident full-frame pixel refinement, score all seed matrices on the GPU star-core metric "
            "and refine only this many candidates. Zero disables preselection."
        ),
    )
    parser.add_argument("--subpixel-radius-steps", type=int, default=4)
    parser.add_argument("--subpixel-step", type=float, default=0.25)
    parser.add_argument("--matrix-metric-sample-stride", type=int, default=1)
    args = parser.parse_args()
    if (args.catalog_grid_cols is None) != (args.catalog_grid_rows is None):
        raise ValueError("--catalog-grid-cols and --catalog-grid-rows must be provided together")
    if (args.catalog_grid_top_cols is None) != (args.catalog_grid_top_rows is None):
        raise ValueError("--catalog-grid-top-cols and --catalog-grid-top-rows must be provided together")
    if args.matrix_metric_sample_stride <= 0:
        raise ValueError("--matrix-metric-sample-stride must be positive")
    if args.catalog_pixel_refine_coarse_stride <= 0 or args.catalog_pixel_refine_final_stride <= 0:
        raise ValueError("catalog pixel-refine strides must be positive")
    if args.catalog_similarity_top_k < 0:
        raise ValueError("--catalog-similarity-top-k must be non-negative")
    if args.triangle_descriptor_neighbors < 3:
        raise ValueError("--triangle-descriptor-neighbors must be at least 3")
    if args.triangle_descriptor_max_descriptors <= 0:
        raise ValueError("--triangle-descriptor-max-descriptors must be positive")
    if args.triangle_descriptor_radius < 0.0:
        raise ValueError("--triangle-descriptor-radius must be non-negative")
    if args.resident_star_core_preselect_top_k < 0:
        raise ValueError("--resident-star-core-preselect-top-k must be non-negative")

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

    (
        astroalign_result,
        astroalign_aligned,
        astroalign_valid,
        astroalign_moving_points,
        astroalign_reference_points,
    ) = _astroalign_run_with_output(reference, moving)
    astroalign_matrix = np.asarray(astroalign_result["matrix"], dtype=np.float64)
    gpu_matrix_result, gpu_matrix_aligned, gpu_matrix_valid = _gpu_matrix_warp_run_with_output(
        reference,
        moving,
        astroalign_matrix,
    )
    gpu_similarity_result, gpu_similarity_aligned, gpu_similarity_valid = _gpu_similarity_fit_from_pairs_run(
        reference,
        moving,
        astroalign_moving_points,
        astroalign_reference_points,
    )
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
    gpu_resident_matrix_metrics = _gpu_resident_matrix_metrics_run(
        reference,
        moving,
        astroalign_matrix,
        args.matrix_metric_sample_stride,
    )
    gpu_matrix_metrics = _gpu_matrix_metrics_run(
        reference,
        moving,
        astroalign_matrix,
        args.matrix_metric_sample_stride,
    )
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
    gpu_catalog_similarity_result, gpu_catalog_similarity_aligned, gpu_catalog_similarity_valid = (
        _gpu_catalog_similarity_run(
            reference,
            moving,
            args.catalog_stars,
            args.catalog_threshold_sigma,
            args.catalog_tolerance_px,
            args.catalog_similarity_min_pair_distance,
            args.catalog_min_inliers,
            args.catalog_grid_cols,
            args.catalog_grid_rows,
            args.catalog_grid_top_cols,
            args.catalog_grid_top_rows,
            args.catalog_grid_top_per_cell,
            args.catalog_nms_scan_stars,
            args.catalog_nms_min_separation,
            prior_dx,
            prior_dy,
            args.catalog_prior_radius,
            args.catalog_similarity_min_scale,
            args.catalog_similarity_max_scale,
            args.catalog_similarity_max_rotation_rad,
            args.catalog_similarity_top_k,
        )
    )
    (
        gpu_triangle_descriptor_similarity_result,
        gpu_triangle_descriptor_similarity_aligned,
        gpu_triangle_descriptor_similarity_valid,
    ) = _gpu_triangle_descriptor_similarity_run(
        reference,
        moving,
        args.catalog_stars,
        args.catalog_threshold_sigma,
        args.catalog_tolerance_px,
        args.triangle_descriptor_radius,
        args.triangle_descriptor_neighbors,
        args.triangle_descriptor_max_descriptors,
        args.catalog_min_inliers,
        args.catalog_grid_top_cols,
        args.catalog_grid_top_rows,
        args.catalog_grid_top_per_cell,
        args.catalog_nms_scan_stars,
        args.catalog_nms_min_separation,
    )
    (
        gpu_catalog_similarity_pixel_refined_result,
        gpu_catalog_similarity_pixel_refined_aligned,
        gpu_catalog_similarity_pixel_refined_valid,
    ) = _gpu_catalog_similarity_pixel_refine_run(
        reference,
        moving,
        gpu_catalog_similarity_result["matrix"],
        gpu_catalog_similarity_result["top_candidates"],
        gpu_catalog_similarity_result.get("refined_inliers"),
        gpu_catalog_similarity_result.get("refit_rms_px"),
        args.catalog_pixel_refine_radius,
        args.catalog_pixel_refine_coarse_step,
        args.catalog_pixel_refine_fine_radius,
        args.catalog_pixel_refine_fine_step,
        args.catalog_pixel_refine_coarse_stride,
        args.catalog_pixel_refine_final_stride,
    )
    (
        gpu_resident_catalog_similarity_pixel_refined_result,
        gpu_resident_catalog_similarity_pixel_refined_aligned,
        gpu_resident_catalog_similarity_pixel_refined_valid,
    ) = _gpu_resident_catalog_similarity_pixel_refine_run(
        reference,
        moving,
        gpu_catalog_similarity_result["matrix"],
        gpu_catalog_similarity_result["top_candidates"],
        gpu_catalog_similarity_result.get("refined_inliers"),
        gpu_catalog_similarity_result.get("refit_rms_px"),
        args.catalog_pixel_refine_radius,
        args.catalog_pixel_refine_coarse_step,
        args.catalog_pixel_refine_fine_radius,
        args.catalog_pixel_refine_fine_step,
        args.catalog_pixel_refine_coarse_stride,
        args.catalog_pixel_refine_final_stride,
        args.resident_star_core_preselect_top_k,
    )
    if (
        gpu_catalog_result["accepted"]
        and np.isfinite(gpu_catalog_result["rms"])
        and np.isfinite(gpu_result["rms"])
        and gpu_catalog_result["rms"] > gpu_result["rms"] * 1.05
    ):
        gpu_catalog_result["accepted"] = False
        gpu_catalog_result["warnings"].append("catalog image RMS is worse than integer NCC by more than 5%")
    if (
        gpu_catalog_similarity_result["accepted"]
        and np.isfinite(gpu_catalog_similarity_result["rms"])
        and np.isfinite(gpu_subpixel_result["rms"])
        and gpu_catalog_similarity_result["rms"] > gpu_subpixel_result["rms"] * 1.10
    ):
        gpu_catalog_similarity_result["accepted"] = False
        gpu_catalog_similarity_result["warnings"].append(
            "catalog similarity image RMS is worse than subpixel NCC by more than 10%"
        )
    devices = gpwbpp_cuda.list_devices()
    gpu_matrix_diff = _diff_on_common_valid_pixels(
        gpu_matrix_aligned,
        gpu_matrix_valid,
        astroalign_aligned,
        astroalign_valid,
    )
    gpu_similarity_diff = _diff_on_common_valid_pixels(
        gpu_similarity_aligned,
        gpu_similarity_valid,
        astroalign_aligned,
        astroalign_valid,
    )
    gpu_catalog_similarity_diff = _diff_on_common_valid_pixels(
        gpu_catalog_similarity_aligned,
        gpu_catalog_similarity_valid,
        astroalign_aligned,
        astroalign_valid,
    )
    gpu_catalog_similarity_pixel_refined_diff = _diff_on_common_valid_pixels(
        gpu_catalog_similarity_pixel_refined_aligned,
        gpu_catalog_similarity_pixel_refined_valid,
        astroalign_aligned,
        astroalign_valid,
    )
    gpu_triangle_descriptor_similarity_diff = _diff_on_common_valid_pixels(
        gpu_triangle_descriptor_similarity_aligned,
        gpu_triangle_descriptor_similarity_valid,
        astroalign_aligned,
        astroalign_valid,
    )
    gpu_resident_catalog_similarity_pixel_refined_diff = _diff_on_common_valid_pixels(
        gpu_resident_catalog_similarity_pixel_refined_aligned,
        gpu_resident_catalog_similarity_pixel_refined_valid,
        astroalign_aligned,
        astroalign_valid,
    )
    catalog_similarity_agreement = _agreement_vs_astroalign(
        np.asarray(gpu_catalog_similarity_result["matrix"], dtype=np.float64),
        astroalign_matrix,
        gpu_catalog_similarity_diff,
    )
    catalog_similarity_pixel_refined_agreement = _agreement_vs_astroalign(
        np.asarray(gpu_catalog_similarity_pixel_refined_result["matrix"], dtype=np.float64),
        astroalign_matrix,
        gpu_catalog_similarity_pixel_refined_diff,
    )
    resident_catalog_similarity_pixel_refined_agreement = _agreement_vs_astroalign(
        np.asarray(gpu_resident_catalog_similarity_pixel_refined_result["matrix"], dtype=np.float64),
        astroalign_matrix,
        gpu_resident_catalog_similarity_pixel_refined_diff,
    )
    triangle_descriptor_similarity_agreement = _agreement_vs_astroalign(
        np.asarray(gpu_triangle_descriptor_similarity_result["matrix"], dtype=np.float64),
        astroalign_matrix,
        gpu_triangle_descriptor_similarity_diff,
    )
    gpu_catalog_similarity_result["benchmark_agreement"] = catalog_similarity_agreement
    gpu_catalog_similarity_result["output_consistent_with_astroalign"] = bool(
        catalog_similarity_agreement["output_passed"]
    )
    gpu_catalog_similarity_pixel_refined_result["benchmark_agreement"] = catalog_similarity_pixel_refined_agreement
    gpu_catalog_similarity_pixel_refined_result["output_consistent_with_astroalign"] = bool(
        catalog_similarity_pixel_refined_agreement["output_passed"]
    )
    gpu_resident_catalog_similarity_pixel_refined_result["benchmark_agreement"] = (
        resident_catalog_similarity_pixel_refined_agreement
    )
    gpu_resident_catalog_similarity_pixel_refined_result["output_consistent_with_astroalign"] = bool(
        resident_catalog_similarity_pixel_refined_agreement["output_passed"]
    )
    gpu_triangle_descriptor_similarity_result["benchmark_agreement"] = triangle_descriptor_similarity_agreement
    gpu_triangle_descriptor_similarity_result["output_consistent_with_astroalign"] = bool(
        triangle_descriptor_similarity_agreement["output_passed"]
    )
    gpu_catalog_similarity_pixel_refined_result["accepted"] = bool(
        catalog_similarity_pixel_refined_agreement["passed"]
    )
    gpu_catalog_similarity_pixel_refined_result["warnings"] = (
        [] if catalog_similarity_pixel_refined_agreement["passed"] else ["pixel-refined catalog similarity agreement failed"]
    )
    gpu_resident_catalog_similarity_pixel_refined_result["accepted"] = bool(
        resident_catalog_similarity_pixel_refined_agreement["passed"]
    )
    gpu_resident_catalog_similarity_pixel_refined_result["warnings"] = (
        []
        if resident_catalog_similarity_pixel_refined_agreement["passed"]
        else ["resident pixel-refined catalog similarity agreement failed"]
    )
    gpu_triangle_descriptor_similarity_result["accepted"] = bool(triangle_descriptor_similarity_agreement["passed"])
    gpu_triangle_descriptor_similarity_result["warnings"] = (
        []
        if triangle_descriptor_similarity_agreement["passed"]
        else ["triangle descriptor similarity agreement failed"]
    )
    gpu_catalog_similarity_matrix_metrics = _gpu_matrix_metrics_run(
        reference,
        moving,
        np.asarray(gpu_catalog_similarity_result["matrix"], dtype=np.float64),
        args.matrix_metric_sample_stride,
    )
    if not catalog_similarity_agreement["passed"]:
        gpu_catalog_similarity_result["accepted"] = False
        gpu_catalog_similarity_result["warnings"].append(
            "catalog similarity benchmark agreement with astroalign failed"
        )
    result = {
        "image_shape": list(reference.shape),
        "source_paths": source_paths,
        "center_crop": args.center_crop,
        "truth": truth,
        "astroalign": astroalign_result,
        "gpwbpp_cuda_matrix_warp_from_astroalign": gpu_matrix_result,
        "gpwbpp_cuda_matrix_metrics_from_astroalign": gpu_matrix_metrics,
        "gpwbpp_cuda_resident_matrix_metrics_from_astroalign": gpu_resident_matrix_metrics,
        "gpwbpp_cuda_similarity_fit_from_astroalign_matches": gpu_similarity_result,
        "direct_output_diff_gpu_matrix_minus_astroalign_apply_on_common_valid_pixels": gpu_matrix_diff,
        "direct_output_diff_gpu_similarity_fit_minus_astroalign_apply_on_common_valid_pixels": gpu_similarity_diff,
        "direct_output_diff_gpu_catalog_similarity_minus_astroalign_apply_on_common_valid_pixels": (
            gpu_catalog_similarity_diff
        ),
        "direct_output_diff_gpu_catalog_similarity_pixel_refined_minus_astroalign_apply_on_common_valid_pixels": (
            gpu_catalog_similarity_pixel_refined_diff
        ),
        "direct_output_diff_gpu_resident_catalog_similarity_pixel_refined_minus_astroalign_apply_on_common_valid_pixels": (
            gpu_resident_catalog_similarity_pixel_refined_diff
        ),
        "direct_output_diff_gpu_triangle_descriptor_similarity_minus_astroalign_apply_on_common_valid_pixels": (
            gpu_triangle_descriptor_similarity_diff
        ),
        "catalog_similarity_agreement_vs_astroalign": catalog_similarity_agreement,
        "catalog_similarity_pixel_refined_agreement_vs_astroalign": catalog_similarity_pixel_refined_agreement,
        "resident_catalog_similarity_pixel_refined_agreement_vs_astroalign": (
            resident_catalog_similarity_pixel_refined_agreement
        ),
        "triangle_descriptor_similarity_agreement_vs_astroalign": triangle_descriptor_similarity_agreement,
        "valid_pixels": {
            "astroalign": int(np.sum(astroalign_valid)),
            "gpwbpp_cuda_matrix": int(np.sum(gpu_matrix_valid)),
            "gpwbpp_cuda_similarity_fit": int(np.sum(gpu_similarity_valid)),
            "gpwbpp_cuda_catalog_similarity": int(np.sum(gpu_catalog_similarity_valid)),
            "gpwbpp_cuda_catalog_similarity_pixel_refined": int(
                np.sum(gpu_catalog_similarity_pixel_refined_valid)
            ),
            "gpwbpp_cuda_resident_catalog_similarity_pixel_refined": int(
                np.sum(gpu_resident_catalog_similarity_pixel_refined_valid)
            ),
            "gpwbpp_cuda_triangle_descriptor_similarity": int(np.sum(gpu_triangle_descriptor_similarity_valid)),
            "common": int(np.sum(np.asarray(astroalign_valid, dtype=bool) & np.asarray(gpu_matrix_valid, dtype=bool))),
            "common_similarity_fit": int(
                np.sum(np.asarray(astroalign_valid, dtype=bool) & np.asarray(gpu_similarity_valid, dtype=bool))
            ),
            "common_catalog_similarity": int(
                np.sum(
                    np.asarray(astroalign_valid, dtype=bool)
                    & np.asarray(gpu_catalog_similarity_valid, dtype=bool)
                )
            ),
            "common_catalog_similarity_pixel_refined": int(
                np.sum(
                    np.asarray(astroalign_valid, dtype=bool)
                    & np.asarray(gpu_catalog_similarity_pixel_refined_valid, dtype=bool)
                )
            ),
            "common_resident_catalog_similarity_pixel_refined": int(
                np.sum(
                    np.asarray(astroalign_valid, dtype=bool)
                    & np.asarray(gpu_resident_catalog_similarity_pixel_refined_valid, dtype=bool)
                )
            ),
            "common_triangle_descriptor_similarity": int(
                np.sum(
                    np.asarray(astroalign_valid, dtype=bool)
                    & np.asarray(gpu_triangle_descriptor_similarity_valid, dtype=bool)
                )
            ),
        },
        "gpwbpp_cuda": gpu_result,
        "gpwbpp_cuda_subpixel": gpu_subpixel_result,
        "gpwbpp_cuda_ncc_subpixel": gpu_ncc_subpixel_result,
        "gpwbpp_cuda_resident_ncc_subpixel": gpu_resident_result,
        "gpwbpp_cuda_resident_matrix_warp_from_astroalign": gpu_resident_matrix_result,
        "gpwbpp_cuda_catalog": gpu_catalog_result,
        "gpwbpp_cuda_catalog_similarity": gpu_catalog_similarity_result,
        "gpwbpp_cuda_catalog_similarity_pixel_refined": gpu_catalog_similarity_pixel_refined_result,
        "gpwbpp_cuda_resident_catalog_similarity_pixel_refined": (
            gpu_resident_catalog_similarity_pixel_refined_result
        ),
        "gpwbpp_cuda_triangle_descriptor_similarity": gpu_triangle_descriptor_similarity_result,
        "gpwbpp_cuda_catalog_similarity_matrix_metrics": gpu_catalog_similarity_matrix_metrics,
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
        "gpu_similarity_fit_plus_warp_speedup_vs_astroalign_apply_transform": astroalign_result["apply_elapsed_s"]
        / gpu_similarity_result["elapsed_s"]
        if gpu_similarity_result["elapsed_s"] > 0.0
        else None,
        "gpu_similarity_matrix_max_abs_delta_vs_astroalign": float(
            np.max(np.abs(np.asarray(gpu_similarity_result["matrix"], dtype=np.float64) - astroalign_matrix))
        ),
        "catalog_speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_catalog_result["elapsed_s"]
        if gpu_catalog_result["elapsed_s"] > 0.0
        else None,
        "catalog_similarity_speedup_vs_astroalign": astroalign_result["elapsed_s"]
        / gpu_catalog_similarity_result["elapsed_s"]
        if gpu_catalog_similarity_result["elapsed_s"] > 0.0
        else None,
        "catalog_similarity_pixel_refined_speedup_vs_astroalign": astroalign_result["elapsed_s"]
        / gpu_catalog_similarity_pixel_refined_result["elapsed_s"]
        if gpu_catalog_similarity_pixel_refined_result["elapsed_s"] > 0.0
        else None,
        "resident_catalog_similarity_pixel_refined_device_speedup_vs_astroalign": astroalign_result["elapsed_s"]
        / gpu_resident_catalog_similarity_pixel_refined_result["device_elapsed_s"]
        if gpu_resident_catalog_similarity_pixel_refined_result["device_elapsed_s"] > 0.0
        else None,
        "resident_catalog_similarity_pixel_refined_algorithm_speedup_vs_astroalign": astroalign_result[
            "elapsed_s"
        ]
        / gpu_resident_catalog_similarity_pixel_refined_result["elapsed_s"]
        if gpu_resident_catalog_similarity_pixel_refined_result["elapsed_s"] > 0.0
        else None,
        "resident_catalog_similarity_pixel_refined_upload_plus_device_speedup_vs_astroalign": astroalign_result[
            "elapsed_s"
        ]
        / gpu_resident_catalog_similarity_pixel_refined_result["upload_plus_device_elapsed_s"]
        if gpu_resident_catalog_similarity_pixel_refined_result["upload_plus_device_elapsed_s"] > 0.0
        else None,
        "resident_catalog_similarity_pixel_refined_upload_plus_algorithm_speedup_vs_astroalign": astroalign_result[
            "elapsed_s"
        ]
        / gpu_resident_catalog_similarity_pixel_refined_result["upload_plus_algorithm_elapsed_s"]
        if gpu_resident_catalog_similarity_pixel_refined_result["upload_plus_algorithm_elapsed_s"] > 0.0
        else None,
        "triangle_descriptor_similarity_speedup_vs_astroalign": astroalign_result["elapsed_s"]
        / gpu_triangle_descriptor_similarity_result["elapsed_s"]
        if gpu_triangle_descriptor_similarity_result["elapsed_s"] > 0.0
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
        "resident_matrix_metrics_device_speedup_vs_astroalign_apply_transform": astroalign_result["apply_elapsed_s"]
        / gpu_resident_matrix_metrics["elapsed_s"]
        if gpu_resident_matrix_metrics["elapsed_s"] > 0.0
        else None,
        "resident_matrix_metrics_upload_plus_device_speedup_vs_astroalign_apply_transform": astroalign_result[
            "apply_elapsed_s"
        ]
        / gpu_resident_matrix_metrics["upload_plus_device_elapsed_s"]
        if gpu_resident_matrix_metrics["upload_plus_device_elapsed_s"] > 0.0
        else None,
        "cuda_devices": devices,
    }
    result["best_gpwbpp_cuda_alignment_vs_astroalign"] = _best_alignment_summary(result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
