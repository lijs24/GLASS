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


def _astroalign_run(reference: np.ndarray, moving: np.ndarray) -> dict[str, Any]:
    import astroalign as aa

    t0 = time.perf_counter()
    transform, control_points = aa.find_transform(moving, reference)
    aligned, footprint = aa.apply_transform(transform, moving, reference, fill_value=0.0)
    elapsed = time.perf_counter() - t0
    params = np.asarray(transform.params, dtype=np.float64)
    invalid = np.asarray(footprint, dtype=bool)
    valid = ~invalid if invalid.shape == reference.shape else np.isfinite(aligned)
    return {
        "elapsed_s": elapsed,
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
    args = parser.parse_args()

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
    gpu_result = _gpu_run(reference, moving, args.max_shift)
    devices = gpwbpp_cuda.list_devices()
    result = {
        "image_shape": list(reference.shape),
        "source_paths": source_paths,
        "center_crop": args.center_crop,
        "truth": truth,
        "astroalign": astroalign_result,
        "gpwbpp_cuda": gpu_result,
        "speedup_vs_astroalign": astroalign_result["elapsed_s"] / gpu_result["elapsed_s"]
        if gpu_result["elapsed_s"] > 0.0
        else None,
        "cuda_devices": devices,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
