from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import glass_cuda


def _matrix_translation(dx: float, dy: float) -> np.ndarray:
    return np.array([[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]], dtype=np.float32)


def _synthetic_frames(frame_count: int, height: int, width: int, seed: int) -> tuple[list[np.ndarray], np.ndarray]:
    rng = np.random.default_rng(seed)
    yy, xx = np.indices((height, width), dtype=np.float32)
    base = (1000.0 + 0.05 * xx + 0.03 * yy).astype(np.float32)
    star_specs = [
        (0.14, 0.18, 5000.0, 1.8),
        (0.35, 0.62, 4200.0, 2.1),
        (0.62, 0.31, 3800.0, 1.7),
        (0.79, 0.74, 4500.0, 2.3),
        (0.51, 0.82, 3500.0, 2.0),
    ]
    for x_frac, y_frac, flux, sigma in star_specs:
        x0 = float(width - 1) * x_frac
        y0 = float(height - 1) * y_frac
        base += (flux * np.exp(-(((xx - x0) ** 2 + (yy - y0) ** 2) / (2.0 * sigma**2)))).astype(
            np.float32
        )

    frames: list[np.ndarray] = []
    matrices: list[np.ndarray] = []
    for index in range(frame_count):
        frames.append((base + rng.normal(0.0, 3.0, size=(height, width))).astype(np.float32))
        dx = float((index % 7) - 3) * 0.35
        dy = float((index % 5) - 2) * -0.28
        matrices.append(_matrix_translation(dx, dy))
    return frames, np.stack(matrices, axis=0).astype(np.float32)


def _load_stack(frames: list[np.ndarray]) -> Any:
    height, width = frames[0].shape
    stack = glass_cuda.ResidentCalibratedStack(len(frames), height, width)
    for index, frame in enumerate(frames):
        stack.upload_calibrated_frame(index, frame)
    return stack


def _run_stack_dispatch(
    frames: list[np.ndarray],
    matrices: np.ndarray,
    *,
    interpolation: str,
    max_chunk_capacity_frames: int,
    clamping_threshold: float,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], float]:
    stack = _load_stack(frames)
    start = time.perf_counter()
    if interpolation == "lanczos3":
        warp_timing = stack.apply_matrix_lanczos3_frames(
            list(range(len(frames))),
            matrices,
            np.nan,
            clamping_threshold,
            dispatch="chunked",
            max_chunk_capacity_frames=max_chunk_capacity_frames,
        )
    else:
        warp_timing = stack.apply_matrix_bilinear_frames(
            list(range(len(frames))),
            matrices,
            np.nan,
            dispatch="chunked",
            max_chunk_capacity_frames=max_chunk_capacity_frames,
        )
    master, weight_map = stack.integrate_mean(weights)
    return master, weight_map, warp_timing, time.perf_counter() - start


def _run_fused_dispatch(
    frames: list[np.ndarray],
    matrices: np.ndarray,
    *,
    interpolation: str,
    clamping_threshold: float,
    weights: np.ndarray,
    download_mode: str,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], float]:
    stack = _load_stack(frames)
    start = time.perf_counter()
    master, weight_map, _coverage, _geometric, timing = stack.integrate_matrix_warped_mean(
        matrices,
        weights,
        interpolation=interpolation,
        clamping_threshold=clamping_threshold,
        download_mode=download_mode,
    )
    return master, weight_map, timing, time.perf_counter() - start


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "median": 0.0, "mean": 0.0, "max": 0.0}
    return {
        "min": float(min(values)),
        "median": float(statistics.median(values)),
        "mean": float(statistics.fmean(values)),
        "max": float(max(values)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare resident chunked matrix warp+stack integration with fused matrix integration."
    )
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--frames", type=int, default=32)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--seed", type=int, default=470)
    parser.add_argument("--interpolation", choices=["bilinear", "lanczos3"], default="bilinear")
    parser.add_argument("--max-chunk-capacity-frames", type=int, default=8)
    parser.add_argument("--clamping-threshold", type=float, default=-1.0)
    parser.add_argument("--download-mode", choices=["master_weight", "full"], default="master_weight")
    args = parser.parse_args()

    if args.frames <= 0 or args.width <= 0 or args.height <= 0:
        raise ValueError("frames, width, and height must be positive")
    if args.repeats <= 0 or args.warmup < 0:
        raise ValueError("repeats must be positive and warmup must be non-negative")
    if args.max_chunk_capacity_frames <= 0:
        raise ValueError("max chunk capacity must be positive")
    if not glass_cuda.cuda_available() or not glass_cuda.native_extension_loaded():
        raise RuntimeError("native CUDA backend is required for this benchmark")

    frames, matrices = _synthetic_frames(args.frames, args.height, args.width, args.seed)
    weights = np.ones(args.frames, dtype=np.float32)

    stack_times: list[float] = []
    fused_times: list[float] = []
    last_stack_timing: dict[str, Any] = {}
    last_fused_timing: dict[str, Any] = {}
    last_stack_master: np.ndarray | None = None
    last_stack_weight: np.ndarray | None = None
    last_fused_master: np.ndarray | None = None
    last_fused_weight: np.ndarray | None = None

    for run_index in range(args.warmup + args.repeats):
        stack_master, stack_weight, stack_timing, stack_elapsed = _run_stack_dispatch(
            frames,
            matrices,
            interpolation=args.interpolation,
            max_chunk_capacity_frames=args.max_chunk_capacity_frames,
            clamping_threshold=args.clamping_threshold,
            weights=weights,
        )
        fused_master, fused_weight, fused_timing, fused_elapsed = _run_fused_dispatch(
            frames,
            matrices,
            interpolation=args.interpolation,
            clamping_threshold=args.clamping_threshold,
            weights=weights,
            download_mode=args.download_mode,
        )
        if run_index >= args.warmup:
            stack_times.append(float(stack_elapsed))
            fused_times.append(float(fused_elapsed))
            last_stack_timing = dict(stack_timing)
            last_fused_timing = dict(fused_timing)
            last_stack_master = stack_master
            last_stack_weight = stack_weight
            last_fused_master = fused_master
            last_fused_weight = fused_weight

    if last_stack_master is None or last_fused_master is None or last_stack_weight is None or last_fused_weight is None:
        raise RuntimeError("benchmark did not produce comparison outputs")

    master_delta = np.asarray(last_stack_master - last_fused_master, dtype=np.float32)
    weight_delta = np.asarray(last_stack_weight - last_fused_weight, dtype=np.float32)
    stack_stats = _stats(stack_times)
    fused_stats = _stats(fused_times)
    fused_median = fused_stats["median"]
    speedup = None if fused_median <= 0.0 else stack_stats["median"] / fused_median
    total_pixels = int(args.frames) * int(args.width) * int(args.height)
    payload: dict[str, Any] = {
        "benchmark": "resident_fused_matrix_dispatch",
        "backend": "cuda_resident_stack",
        "device": glass_cuda.get_device_info(0),
        "frame_count": int(args.frames),
        "image_shape": [int(args.height), int(args.width)],
        "total_pixels": total_pixels,
        "interpolation": args.interpolation,
        "max_chunk_capacity_frames": int(args.max_chunk_capacity_frames),
        "download_mode": args.download_mode,
        "repeats": int(args.repeats),
        "warmup": int(args.warmup),
        "stack_dispatch_wall_s": stack_stats,
        "fused_matrix_dispatch_wall_s": fused_stats,
        "speedup_stack_over_fused_median": speedup,
        "throughput_mpix_s": {
            "stack_dispatch_median": None
            if stack_stats["median"] <= 0.0
            else float(total_pixels / stack_stats["median"] / 1_000_000.0),
            "fused_matrix_dispatch_median": None
            if fused_stats["median"] <= 0.0
            else float(total_pixels / fused_stats["median"] / 1_000_000.0),
        },
        "numerical_agreement": {
            "master_max_abs": float(np.max(np.abs(master_delta))),
            "master_rms": float(np.sqrt(np.mean(master_delta * master_delta, dtype=np.float64))),
            "weight_max_abs": float(np.max(np.abs(weight_delta))),
            "weight_rms": float(np.sqrt(np.mean(weight_delta * weight_delta, dtype=np.float64))),
            "passed": bool(
                np.max(np.abs(master_delta)) <= 1.0e-4 and np.max(np.abs(weight_delta)) <= 1.0e-5
            ),
        },
        "stack_native_timing_s": last_stack_timing,
        "fused_native_timing_s": last_fused_timing,
        "notes": [
            "Stack dispatch measures chunked matrix warp into the resident stack plus resident weighted mean.",
            "Fused dispatch samples resident calibrated frames through the matrices during integration.",
            "Host frame upload is intentionally outside the timed comparison.",
        ],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "resident fused matrix dispatch benchmark: "
        f"stack_median={stack_stats['median']:.6f}s "
        f"fused_median={fused_stats['median']:.6f}s "
        f"speedup={speedup if speedup is not None else float('nan'):.3f} "
        f"master_max_abs={payload['numerical_agreement']['master_max_abs']:.6g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
