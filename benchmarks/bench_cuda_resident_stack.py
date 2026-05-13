from __future__ import annotations

import argparse
import gc
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import glass_cuda
from glass.cpu.master_frames import image_stats, make_master_bias, make_master_dark, make_master_flat
from glass.io.fits_io import read_fits_data, write_fits_data
from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy


def _frames_by_type(plan: dict[str, Any], frame_type: str) -> list[dict[str, Any]]:
    return [frame for frame in plan["frames"] if frame.get("frame_type") == frame_type]


def _first_shape(frames: list[dict[str, Any]]) -> tuple[int, int]:
    if not frames:
        raise ValueError("cannot infer shape without frames")
    height = int(frames[0]["height"])
    width = int(frames[0]["width"])
    return height, width


def _paths(frames: list[dict[str, Any]]) -> list[Path]:
    return [Path(str(frame["path"])) for frame in frames]


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
    return CalibrationPolicy(**{key: value for key, value in raw.items() if key in allowed})


def _load_or_build_masters(
    out_dir: Path,
    bias_frames: list[dict[str, Any]],
    dark_frames: list[dict[str, Any]],
    flat_frames: list[dict[str, Any]],
    policy: CalibrationPolicy,
    reuse: bool,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    cache_dir = out_dir / "master_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    bias_path = cache_dir / "master_bias.npy"
    dark_path = cache_dir / "master_dark.npy"
    flat_path = cache_dir / "master_flat.npy"
    stats_path = cache_dir / "master_stats.json"

    if reuse and bias_path.exists() and dark_path.exists() and flat_path.exists() and stats_path.exists():
        return (
            np.load(bias_path),
            np.load(dark_path),
            np.load(flat_path),
            read_json(stats_path),
        )

    master_bias = make_master_bias(_paths(bias_frames)).data if bias_frames else None
    if dark_frames:
        dark_bias = None if policy.master_dark_includes_bias else master_bias
        master_dark = make_master_dark(_paths(dark_frames), dark_bias).data
    else:
        master_dark = None
    if flat_frames:
        master_flat = make_master_flat(
            _paths(flat_frames),
            master_bias=master_bias,
            normalization=policy.flat_normalization,
            flat_floor=policy.flat_floor,
        ).data
    else:
        master_flat = None

    stats = {
        "bias": None if master_bias is None else image_stats(master_bias),
        "dark": None if master_dark is None else image_stats(master_dark),
        "flat": None if master_flat is None else image_stats(master_flat),
        "master_dark_includes_bias": policy.master_dark_includes_bias,
    }
    if master_bias is not None:
        np.save(bias_path, master_bias)
    if master_dark is not None:
        np.save(dark_path, master_dark)
    if master_flat is not None:
        np.save(flat_path, master_flat)
    write_json(stats_path, stats)
    return master_bias, master_dark, master_flat, stats


def _memory_estimate(frame_count: int, height: int, width: int) -> dict[str, Any]:
    frame_bytes = int(height) * int(width) * 4
    calibrated_stack = frame_count * frame_bytes
    reusable_raw = frame_bytes
    masters = 3 * frame_bytes
    integration_outputs = 2 * frame_bytes
    weights = frame_count * 4
    return {
        "frame_bytes": frame_bytes,
        "frame_mib": frame_bytes / (1024**2),
        "calibrated_stack_bytes": calibrated_stack,
        "calibrated_stack_gib": calibrated_stack / (1024**3),
        "resident_base_bytes": calibrated_stack + reusable_raw + masters,
        "resident_base_gib": (calibrated_stack + reusable_raw + masters) / (1024**3),
        "integration_temporary_bytes": integration_outputs + weights,
        "integration_temporary_gib": (integration_outputs + weights) / (1024**3),
        "estimated_peak_bytes": calibrated_stack + reusable_raw + masters + integration_outputs + weights,
        "estimated_peak_gib": (calibrated_stack + reusable_raw + masters + integration_outputs + weights)
        / (1024**3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VRAM-resident CUDA calibration + mean integration benchmark.")
    parser.add_argument("--plan", required=True, help="processing_plan.json")
    parser.add_argument("--out", required=True, help="benchmark output directory")
    parser.add_argument("--limit", type=int, default=None, help="limit light frames for smoke runs")
    parser.add_argument("--reuse-masters", action="store_true", help="reuse cached .npy masters when present")
    parser.add_argument("--write-weight-map", action="store_true", help="write the weight map FITS output")
    args = parser.parse_args()

    if not glass_cuda.cuda_available() or not glass_cuda.native_extension_loaded():
        raise RuntimeError("native CUDA backend is required for resident benchmark")

    plan = read_json(args.plan)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_lights = _frames_by_type(plan, "light")
    lights = all_lights[: args.limit] if args.limit else all_lights
    bias_frames = _frames_by_type(plan, "bias")
    dark_frames = _frames_by_type(plan, "dark")
    flat_frames = _frames_by_type(plan, "flat")
    if not lights:
        raise ValueError("plan contains no light frames")

    height, width = _first_shape(lights)
    policy = _policy_from_plan(plan)
    dark_exposure = None
    if dark_frames:
        exposures = [float(frame["exposure_s"]) for frame in dark_frames if frame.get("exposure_s") is not None]
        dark_exposure = float(np.median(exposures)) if exposures else None

    total_start = time.perf_counter()
    master_start = time.perf_counter()
    master_bias, master_dark, master_flat, master_stats = _load_or_build_masters(
        out_dir, bias_frames, dark_frames, flat_frames, policy, args.reuse_masters
    )
    master_elapsed = time.perf_counter() - master_start

    stack_start = time.perf_counter()
    stack = glass_cuda.ResidentCalibratedStack(len(lights), height, width)
    stack.set_calibration_masters(master_bias, master_dark, master_flat)
    stack_elapsed = time.perf_counter() - stack_start

    del master_bias, master_dark, master_flat
    gc.collect()

    per_frame_s: list[float] = []
    load_calibrate_start = time.perf_counter()
    for index, frame in enumerate(lights):
        frame_start = time.perf_counter()
        light = read_fits_data(frame["path"], dtype=np.float32)
        stack.calibrate_frame(
            index,
            light,
            float(frame.get("exposure_s") or 0.0),
            dark_exposure,
            asdict(policy),
        )
        per_frame_s.append(time.perf_counter() - frame_start)
        del light
        if index % 10 == 9:
            gc.collect()
    load_calibrate_elapsed = time.perf_counter() - load_calibrate_start

    integration_start = time.perf_counter()
    master, weight_map = stack.integrate_mean()
    integration_elapsed = time.perf_counter() - integration_start

    write_start = time.perf_counter()
    master_path = out_dir / "resident_master_mean.fits"
    weight_map_path = out_dir / "resident_weight_map.fits"
    write_fits_data(master_path, master, {"GLASS": "RESCUDA", "NFRAMES": len(lights)})
    if args.write_weight_map:
        write_fits_data(weight_map_path, weight_map, {"GLASS": "RESCUDA", "NFRAMES": len(lights)})
    write_elapsed = time.perf_counter() - write_start
    total_elapsed = time.perf_counter() - total_start

    pixels = int(height) * int(width) * len(lights)
    result = {
        "status": "completed",
        "backend": "cuda_resident_stack",
        "device": glass_cuda.get_device_info(0),
        "plan": str(Path(args.plan).resolve()),
        "out_dir": str(out_dir.resolve()),
        "frame_count": len(lights),
        "calibration_counts": {
            "bias": len(bias_frames),
            "dark": len(dark_frames),
            "flat": len(flat_frames),
            "light_available": len(all_lights),
            "light_used": len(lights),
        },
        "shape": {"height": height, "width": width},
        "total_pixels": pixels,
        "memory_estimate": _memory_estimate(len(lights), height, width),
        "resident_bytes_allocated_after_master_upload": stack.bytes_allocated,
        "policy": asdict(policy),
        "dark_exposure_s": dark_exposure,
        "master_stats": master_stats,
        "timing_s": {
            "master_build_or_load": master_elapsed,
            "resident_allocate_and_master_upload": stack_elapsed,
            "light_read_upload_calibrate": load_calibrate_elapsed,
            "resident_integration": integration_elapsed,
            "output_write": write_elapsed,
            "total": total_elapsed,
            "per_frame_mean": float(np.mean(per_frame_s)) if per_frame_s else 0.0,
            "per_frame_min": float(np.min(per_frame_s)) if per_frame_s else 0.0,
            "per_frame_max": float(np.max(per_frame_s)) if per_frame_s else 0.0,
        },
        "throughput_mpix_s": {
            "light_read_upload_calibrate": (pixels / 1.0e6) / load_calibrate_elapsed,
            "resident_integration": (pixels / 1.0e6) / integration_elapsed,
            "total_without_master_build": (pixels / 1.0e6)
            / (stack_elapsed + load_calibrate_elapsed + integration_elapsed + write_elapsed),
        },
        "outputs": {
            "master": str(master_path.resolve()),
            "weight_map": str(weight_map_path.resolve()) if args.write_weight_map else None,
        },
        "notes": [
            "Raw light frames are uploaded one at a time into a reusable device buffer.",
            "Calibrated frames remain resident in VRAM until mean integration completes.",
            "No calibrated FITS cache is written in this benchmark path.",
        ],
    }
    write_json(out_dir / "resident_benchmark_result.json", result)
    print(f"resident benchmark completed: {out_dir / 'resident_benchmark_result.json'}")
    print(f"frames={len(lights)} total_s={total_elapsed:.3f} integration_s={integration_elapsed:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
