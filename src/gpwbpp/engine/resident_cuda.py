from __future__ import annotations

import gc
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from gpwbpp.cpu.master_frames import image_stats, make_master_bias, make_master_dark, make_master_flat
from gpwbpp.io.fits_io import read_fits_data, write_fits_data
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import CalibrationPolicy, PipelineArtifact, RunState, now_iso


def _cuda_module_required():
    import gpwbpp_cuda

    if not gpwbpp_cuda.cuda_available() or not hasattr(gpwbpp_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("resident CUDA mode requires the native ResidentCalibratedStack backend")
    return gpwbpp_cuda


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
    return CalibrationPolicy(**{key: value for key, value in raw.items() if key in allowed})


def _frame_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {frame["id"]: frame for frame in plan.get("frames", [])}


def _frames_by_type(plan: dict[str, Any], frame_type: str) -> list[dict[str, Any]]:
    return [frame for frame in plan.get("frames", []) if frame.get("frame_type") == frame_type]


def _paths_for_records(records: list[dict[str, Any]]) -> list[Path]:
    return [Path(str(frame["path"])) for frame in records]


def _same_shape(frame: dict[str, Any], height: int, width: int) -> bool:
    return int(frame.get("height") or 0) == height and int(frame.get("width") or 0) == width


def _safe_filter_name(value: str | None) -> str:
    text = value or "unknown"
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)


def _memory_estimate(frame_count: int, height: int, width: int, master_count: int = 3) -> dict[str, Any]:
    frame_bytes = int(height) * int(width) * 4
    calibrated_stack = frame_count * frame_bytes
    reusable_raw = frame_bytes
    masters = master_count * frame_bytes
    integration_outputs = 2 * frame_bytes
    weights = frame_count * 4
    estimated_peak = calibrated_stack + reusable_raw + masters + integration_outputs + weights
    return {
        "frame_bytes": frame_bytes,
        "frame_mib": frame_bytes / (1024**2),
        "calibrated_stack_bytes": calibrated_stack,
        "calibrated_stack_gib": calibrated_stack / (1024**3),
        "resident_base_bytes": calibrated_stack + reusable_raw + masters,
        "resident_base_gib": (calibrated_stack + reusable_raw + masters) / (1024**3),
        "integration_temporary_bytes": integration_outputs + weights,
        "integration_temporary_gib": (integration_outputs + weights) / (1024**3),
        "estimated_peak_bytes": estimated_peak,
        "estimated_peak_gib": estimated_peak / (1024**3),
    }


def _load_or_build_aggregate_masters(
    run: Path,
    filter_name: str | None,
    height: int,
    width: int,
    bias_records: list[dict[str, Any]],
    dark_records: list[dict[str, Any]],
    flat_records: list[dict[str, Any]],
    policy: CalibrationPolicy,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    cache = run / "calib_cache" / "resident_masters"
    cache.mkdir(parents=True, exist_ok=True)
    key = f"aggregate_{_safe_filter_name(filter_name)}_{width}x{height}"
    bias_path = cache / f"{key}_master_bias.npy"
    dark_path = cache / f"{key}_master_dark.npy"
    flat_path = cache / f"{key}_master_flat.npy"
    stats_path = cache / f"{key}_master_stats.json"
    if bias_path.exists() and dark_path.exists() and flat_path.exists() and stats_path.exists():
        return np.load(bias_path), np.load(dark_path), np.load(flat_path), read_json(stats_path)

    master_bias = None
    bias_paths = _paths_for_records(bias_records)
    if bias_paths:
        master_bias = make_master_bias(bias_paths).data

    master_dark = None
    dark_paths = _paths_for_records(dark_records)
    if dark_paths:
        dark_bias = None if policy.master_dark_includes_bias else master_bias
        master_dark = make_master_dark(dark_paths, dark_bias).data

    master_flat = None
    flat_paths = _paths_for_records(flat_records)
    if flat_paths:
        master_flat = make_master_flat(
            flat_paths,
            master_bias=master_bias,
            normalization=policy.flat_normalization,
            flat_floor=policy.flat_floor,
        ).data

    stats = {
        "calibration_group_policy": "aggregate_same_shape_filter_for_resident_mode",
        "filter": filter_name,
        "bias_count": len(bias_paths),
        "dark_count": len(dark_paths),
        "flat_count": len(flat_paths),
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


def run_resident_calibration_integration(
    plan_path: str | Path,
    run_dir: str | Path,
    integration_weighting: str = "auto",
    integration_rejection: str = "none",
) -> RunState:
    if integration_rejection not in {"auto", "none"}:
        raise ValueError("resident CUDA mode currently supports integration rejection=none only")
    if integration_weighting not in {"auto", "none"}:
        raise ValueError("resident CUDA mode currently supports integration weighting=none only")

    cuda_module = _cuda_module_required()
    plan = read_json(plan_path)
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    state = RunState(run_id=run.name or "gpwbpp-run", created_at=now_iso(), current_stage="resident_calibration")

    frames = _frame_map(plan)
    policy = _policy_from_plan(plan)
    output_dir = run / "integration"
    output_dir.mkdir(parents=True, exist_ok=True)

    resident_artifacts: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    frame_weights: dict[str, float] = {}

    try:
        all_lights = _frames_by_type(plan, "light")
        light_groups: dict[tuple[str | None, int, int], list[dict[str, Any]]] = {}
        for frame in all_lights:
            height = int(frame["height"])
            width = int(frame["width"])
            light_groups.setdefault((frame.get("filter"), height, width), []).append(frame)

        for (filter_name, height, width), light_frames in light_groups.items():
            height = int(light_frames[0]["height"])
            width = int(light_frames[0]["width"])
            filt = _safe_filter_name(filter_name)
            bias_records = [
                frame for frame in _frames_by_type(plan, "bias") if _same_shape(frame, height, width)
            ]
            dark_records = [
                frame for frame in _frames_by_type(plan, "dark") if _same_shape(frame, height, width)
            ]
            flat_records = [
                frame
                for frame in _frames_by_type(plan, "flat")
                if _same_shape(frame, height, width)
                and (frame.get("filter") == filter_name or frame.get("filter") in {None, ""})
            ]
            if not flat_records:
                flat_records = [
                    frame for frame in _frames_by_type(plan, "flat") if _same_shape(frame, height, width)
                ]
            dark_exposures = [
                float(frame["exposure_s"]) for frame in dark_records if frame.get("exposure_s") is not None
            ]
            dark_exposure = float(np.median(dark_exposures)) if dark_exposures else None

            master_start = perf_counter()
            master_bias, master_dark, master_flat, master_stats = _load_or_build_aggregate_masters(
                run,
                filter_name,
                height,
                width,
                bias_records,
                dark_records,
                flat_records,
                policy,
            )
            master_elapsed = perf_counter() - master_start

            allocate_start = perf_counter()
            stack = cuda_module.ResidentCalibratedStack(len(light_frames), height, width)
            stack.set_calibration_masters(master_bias, master_dark, master_flat)
            allocate_elapsed = perf_counter() - allocate_start
            del master_bias, master_dark, master_flat
            gc.collect()

            load_calibrate_start = perf_counter()
            per_frame_s = []
            for index, frame in enumerate(light_frames):
                frame_start = perf_counter()
                light = read_fits_data(frame["path"], dtype=np.float32)
                stack.calibrate_frame(
                    index,
                    light,
                    float(frame.get("exposure_s") or 0.0),
                    None if dark_exposure is None else float(dark_exposure),
                    asdict(policy),
                )
                per_frame_s.append(perf_counter() - frame_start)
                frame_weights[frame["id"]] = 1.0
                del light
                if index % 10 == 9:
                    gc.collect()
            load_calibrate_elapsed = perf_counter() - load_calibrate_start

            integrate_start = perf_counter()
            master, weight_map = stack.integrate_mean()
            integrate_elapsed = perf_counter() - integrate_start
            master_path = output_dir / f"resident_master_{filt}.fits"
            weight_path = output_dir / f"resident_weight_map_{filt}.fits"
            write_start = perf_counter()
            write_fits_data(master_path, master, {"IMAGETYP": "master", "FILTER": filter_name})
            write_fits_data(weight_path, weight_map, {"IMAGETYP": "weight", "FILTER": filter_name})
            write_elapsed = perf_counter() - write_start

            memory_estimate = _memory_estimate(len(light_frames), height, width)
            resident_artifacts.append(
                {
                    "filter": filter_name,
                    "frame_ids": [str(frame["id"]) for frame in light_frames],
                    "shape": {"height": height, "width": width},
                    "master_stats": master_stats,
                    "memory_estimate": memory_estimate,
                    "resident_bytes_allocated_after_master_upload": stack.bytes_allocated,
                    "timing_s": {
                        "master_build_or_load": master_elapsed,
                        "resident_allocate_and_master_upload": allocate_elapsed,
                        "light_read_upload_calibrate": load_calibrate_elapsed,
                        "resident_integration": integrate_elapsed,
                        "output_write": write_elapsed,
                        "per_frame_mean": float(np.mean(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_min": float(np.min(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_max": float(np.max(per_frame_s)) if per_frame_s else 0.0,
                    },
                    "notes": [
                        "Raw light frames are uploaded one at a time into a reusable device buffer.",
                        "Calibrated frames remain resident in VRAM until mean integration completes.",
                        "This mode intentionally skips registration, LN, and rejection in the current gate.",
                    ],
                }
            )
            outputs.append(
                {
                    "filter": filt,
                    "frame_count": len(light_frames),
                    "master_path": str(master_path),
                    "weight_map_path": str(weight_path),
                    "coverage_map_path": None,
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "rejection": "none",
                    "weighting": "none",
                    "estimated_peak_gib": memory_estimate["estimated_peak_gib"],
                    "resident_integration_s": integrate_elapsed,
                }
            )
            del stack, master, weight_map
            gc.collect()

        if not outputs:
            raise ValueError("resident mode found no executable light plans")

        resident_path = run / "resident_artifacts.json"
        write_json(
            resident_path,
            {
                "schema_version": 1,
                "backend": "cuda_resident_stack",
                "policy": asdict(policy),
                "artifacts": resident_artifacts,
                "device": cuda_module.get_device_info(0),
            },
        )
        write_json(
            run / "integration_results.json",
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "combine": "mean",
                "weighting": "none",
                "rejection": "none",
                "frame_weights": frame_weights,
                "outputs": outputs,
                "warnings": [
                    "resident CUDA mode currently skips registration, local normalization, and rejection"
                ],
            },
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_calibration_integration",
                path=str(resident_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.completed_stages.extend(
            ["master_calibration", "resident_light_calibration", "resident_integration"]
        )
        state.current_stage = "integration"
        state.warnings.append(
            "resident CUDA mode is a high-VRAM calibration plus mean-integration path; "
            "registration, LN, and rejection are not yet included"
        )
        return state
    except Exception as exc:
        state.failed_stage = state.current_stage
        state.errors.append(str(exc))
        raise
