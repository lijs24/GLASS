from __future__ import annotations

import gc
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from gpwbpp.cpu.registration import estimate_translation_phase_correlation, translation_matrix
from gpwbpp.cpu.master_frames import image_stats, make_master_bias, make_master_dark, make_master_flat
from gpwbpp.io.fits_io import read_fits_data, write_fits_data
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import CalibrationPolicy, PipelineArtifact, RegistrationResult, RunState, now_iso


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


def _preview_scale(height: int, width: int, target_max_dim: int = 1024) -> int:
    return max(1, (max(int(height), int(width)) + int(target_max_dim) - 1) // int(target_max_dim))


def _registration_preview(image: np.ndarray, scale: int) -> np.ndarray:
    preview = np.asarray(image, dtype=np.float32)[:: int(scale), :: int(scale)]
    return np.ascontiguousarray(np.nan_to_num(preview, nan=0.0, posinf=0.0, neginf=0.0), dtype=np.float32)


def _frame_reference_tokens(frame: dict[str, Any]) -> set[str]:
    path = Path(str(frame.get("path", "")))
    return {str(frame.get("id", "")), path.name, path.stem}


def _find_reference_frame(light_frames: list[dict[str, Any]], reference_frame_id: str | None) -> dict[str, Any]:
    if reference_frame_id:
        for frame in light_frames:
            if str(reference_frame_id) in _frame_reference_tokens(frame):
                return frame
        raise ValueError(f"reference frame was not found in resident light group: {reference_frame_id}")
    return light_frames[0]


def _matches_any_token(frame: dict[str, Any], tokens: set[str]) -> bool:
    return bool(_frame_reference_tokens(frame) & tokens)


def _output_diagnostics(data: np.ndarray, weight_map: np.ndarray | None = None) -> dict[str, Any]:
    values = np.asarray(data, dtype=np.float32)
    total_pixels = int(values.size)
    finite_mask = np.isfinite(values)
    finite = values[finite_mask]
    nonfinite_count = total_pixels - int(finite.size)
    if finite.size == 0:
        return {
            "total_pixels": total_pixels,
            "finite_pixels": 0,
            "nonfinite_pixels": nonfinite_count,
            "statistics": None,
            "normalization_probe": None,
            "clipping_probe": {
                "lt_0_count": 0,
                "gt_1_count": 0,
                "gt_65535_count": 0,
                "nonfinite_count": nonfinite_count,
            },
        }

    percentiles = {
        "p001": float(np.percentile(finite, 0.01)),
        "p01": float(np.percentile(finite, 0.1)),
        "p1": float(np.percentile(finite, 1.0)),
        "p50": float(np.percentile(finite, 50.0)),
        "p99": float(np.percentile(finite, 99.0)),
        "p999": float(np.percentile(finite, 99.9)),
        "p9999": float(np.percentile(finite, 99.99)),
    }
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    robust_low = percentiles["p01"]
    robust_high = percentiles["p999"]
    robust_span = robust_high - robust_low
    positive_weight_count = None
    zero_weight_count = None
    if weight_map is not None:
        weights = np.asarray(weight_map, dtype=np.float32)
        positive_weight_count = int(np.count_nonzero(weights > 0))
        zero_weight_count = int(weights.size - positive_weight_count)
    clipping = {
        "lt_0_count": int(np.count_nonzero(finite < 0.0)),
        "lt_0_fraction": float(np.mean(finite < 0.0)),
        "gt_1_count": int(np.count_nonzero(finite > 1.0)),
        "gt_1_fraction": float(np.mean(finite > 1.0)),
        "gt_65535_count": int(np.count_nonzero(finite > 65535.0)),
        "gt_65535_fraction": float(np.mean(finite > 65535.0)),
        "nonfinite_count": nonfinite_count,
        "positive_weight_pixels": positive_weight_count,
        "zero_weight_pixels": zero_weight_count,
    }
    return {
        "total_pixels": total_pixels,
        "finite_pixels": int(finite.size),
        "nonfinite_pixels": nonfinite_count,
        "statistics": {
            "min": minimum,
            "max": maximum,
            "mean": float(np.mean(finite)),
            "std": float(np.std(finite)),
            **percentiles,
        },
        "normalization_probe": {
            "method": "diagnostic_only_p0_1_to_p99_9",
            "black": robust_low,
            "white": robust_high,
            "scale": float(1.0 / robust_span) if robust_span > 0 else 1.0,
            "offset": float(-robust_low),
            "would_clip_low_count": int(np.count_nonzero(finite < robust_low)),
            "would_clip_high_count": int(np.count_nonzero(finite > robust_high)),
            "would_clip_low_fraction": float(np.mean(finite < robust_low)),
            "would_clip_high_fraction": float(np.mean(finite > robust_high)),
        },
        "clipping_probe": clipping,
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
    flat_floor: float | None = None,
    resident_registration: str = "off",
    resident_registration_max_shift: int = 128,
    resident_subpixel_radius_steps: int = 4,
    resident_subpixel_step: float = 0.25,
    reference_frame_id: str | None = None,
    exclude_frame_ids: list[str] | None = None,
    local_normalization: str = "off",
) -> RunState:
    if integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
        raise ValueError("resident CUDA mode supports rejection=none, sigma_clip, or winsorized_sigma")
    if integration_weighting not in {"auto", "none"}:
        raise ValueError("resident CUDA mode currently supports integration weighting=none only")
    if resident_registration not in {"off", "translation_preview", "translation_ncc_subpixel"}:
        raise ValueError("resident_registration must be off, translation_preview, or translation_ncc_subpixel")
    if local_normalization not in {"auto", "on", "off"}:
        raise ValueError("local_normalization must be auto, on, or off")
    if resident_registration_max_shift < 0:
        raise ValueError("resident_registration_max_shift must be non-negative")
    if resident_subpixel_radius_steps < 0:
        raise ValueError("resident_subpixel_radius_steps must be non-negative")
    if resident_subpixel_step <= 0:
        raise ValueError("resident_subpixel_step must be positive")

    cuda_module = _cuda_module_required()
    plan = read_json(plan_path)
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    state = RunState(run_id=run.name or "gpwbpp-run", created_at=now_iso(), current_stage="resident_calibration")

    frames = _frame_map(plan)
    policy = _policy_from_plan(plan)
    if flat_floor is not None:
        if flat_floor <= 0:
            raise ValueError("flat_floor override must be positive")
        policy.flat_floor = float(flat_floor)
    integration_policy = plan.get("integration_policy", {})
    excluded_tokens = {str(item) for item in (exclude_frame_ids or []) if str(item)}
    rejection_mode = "none" if integration_rejection == "auto" else integration_rejection
    low_sigma = float(integration_policy.get("low_sigma", 3.0))
    high_sigma = float(integration_policy.get("high_sigma", 3.0))
    output_dir = run / "integration"
    output_dir.mkdir(parents=True, exist_ok=True)

    resident_artifacts: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    frame_weights: dict[str, float] = {}
    registration_results: list[RegistrationResult] = []
    local_norm_groups: list[dict[str, Any]] = []

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

            registration_start = perf_counter()
            reference_frame = _find_reference_frame(light_frames, reference_frame_id)
            reference_index = next(
                index for index, frame in enumerate(light_frames) if frame["id"] == reference_frame["id"]
            )
            reference_preview = None
            preview_scale = 1
            if resident_registration == "translation_preview":
                preview_scale = _preview_scale(height, width)
                reference_image = read_fits_data(reference_frame["path"], dtype=np.float32)
                reference_preview = _registration_preview(reference_image, preview_scale)
                del reference_image
                gc.collect()
            registration_setup_elapsed = perf_counter() - registration_start

            load_calibrate_start = perf_counter()
            per_frame_s = []
            per_frame_registration_s = []
            frame_weight_values: list[float] = []
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
                frame_weight = 1.0
                if resident_registration == "translation_preview":
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    dx = 0.0
                    dy = 0.0
                    try:
                        if status == "excluded":
                            frame_weight = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] != reference_frame["id"]:
                            preview = _registration_preview(light, preview_scale)
                            if reference_preview is None:
                                raise RuntimeError("reference preview is not available")
                            preview_dx, preview_dy = estimate_translation_phase_correlation(reference_preview, preview)
                            dx = float(preview_dx * preview_scale)
                            dy = float(preview_dy * preview_scale)
                            stack.apply_translation_frame(index, int(round(dx)), int(round(dy)), np.nan)
                        else:
                            status = "reference"
                    except Exception as exc:
                        status = "failed"
                        frame_weight = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="translation_preview",
                            matrix=translation_matrix(dx, dy),
                            matched_stars=0,
                            inliers=0 if status in {"failed", "excluded"} else 1,
                            rms_px=0.0 if status not in {"failed", "excluded"} else float("nan"),
                            status=status,
                            warnings=warnings
                            + [
                                f"preview_scale={preview_scale}",
                                "phase-correlation preview registration; no star-model RMS yet",
                            ],
                        )
                    )
                per_frame_s.append(perf_counter() - frame_start)
                if resident_registration == "off" and _matches_any_token(frame, excluded_tokens):
                    frame_weight = 0.0
                frame_weights[frame["id"]] = frame_weight
                frame_weight_values.append(frame_weight)
                del light
                if index % 10 == 9:
                    gc.collect()
            load_calibrate_elapsed = perf_counter() - load_calibrate_start

            if resident_registration == "translation_ncc_subpixel":
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    dx = 0.0
                    dy = 0.0
                    score = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                        else:
                            coarse = stack.estimate_translation_to_reference(
                                reference_index,
                                index,
                                resident_registration_max_shift,
                                resident_registration_max_shift,
                            )
                            refined = stack.estimate_translation_subpixel_to_reference(
                                reference_index,
                                index,
                                float(coarse["dx"]),
                                float(coarse["dy"]),
                                resident_subpixel_radius_steps,
                                resident_subpixel_step,
                            )
                            dx = float(refined["dx"])
                            dy = float(refined["dy"])
                            score = float(refined["score"])
                            stack.apply_translation_bilinear_frame(index, dx, dy, np.nan)
                            warnings.extend(
                                [
                                    f"coarse_dx={int(coarse['dx'])}",
                                    f"coarse_dy={int(coarse['dy'])}",
                                    f"coarse_score={float(coarse['score']):.6g}",
                                    f"subpixel_score={score:.6g}",
                                ]
                            )
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    per_frame_registration_s.append(perf_counter() - registration_frame_start)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="translation_ncc_subpixel",
                            matrix=translation_matrix(dx, dy),
                            matched_stars=0,
                            inliers=0 if status in {"failed", "excluded"} else 1,
                            rms_px=0.0 if status not in {"failed", "excluded"} else float("nan"),
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"subpixel_radius_steps={resident_subpixel_radius_steps}",
                                f"subpixel_step={resident_subpixel_step}",
                                "resident GPU NCC registration; no star-model RMS yet",
                            ],
                        )
                    )

            local_norm_start = perf_counter()
            local_norm_policy = plan.get("local_normalization_policy", {})
            local_norm_enabled = local_normalization == "on" or (
                local_normalization == "auto" and bool(local_norm_policy.get("enabled", False))
            )
            local_norm_mode = "resident_global_mean_std" if local_norm_enabled else "off"
            local_norm_frame_results: list[dict[str, Any]] = []
            local_norm_warnings: list[str] = []
            if local_norm_enabled:
                if not hasattr(stack, "frame_global_stats") or not hasattr(stack, "apply_global_normalization_frame"):
                    raise RuntimeError("resident CUDA backend does not expose global local normalization")
                reference_stats = stack.frame_global_stats(reference_index)
                reference_mean = float(reference_stats["mean"])
                reference_std = float(reference_stats["std"])
                eps = 1.0e-6
                local_norm_warnings.append(
                    "resident CUDA local normalization currently uses one global mean/std model per frame; "
                    "full tile/window LN remains a later gate"
                )
                for index, frame in enumerate(light_frames):
                    status = "ok"
                    warnings: list[str] = []
                    scale = 1.0
                    offset = 0.0
                    source_stats: dict[str, Any] | None = None
                    if frame_weight_values[index] <= 0.0:
                        status = "skipped_zero_weight"
                        warnings.append("frame was excluded or failed registration before local normalization")
                    elif index == reference_index:
                        status = "reference"
                        source_stats = reference_stats
                    else:
                        source_stats = stack.frame_global_stats(index)
                        source_mean = float(source_stats["mean"])
                        source_std = float(source_stats["std"])
                        if int(source_stats["valid_pixels"]) == 0:
                            status = "empty"
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("frame had no finite pixels for resident global LN")
                        elif source_std <= eps or reference_std <= eps:
                            status = "offset_only"
                            scale = 1.0
                            offset = reference_mean - source_mean
                            stack.apply_global_normalization_frame(index, scale, offset)
                        else:
                            scale = reference_std / source_std
                            offset = reference_mean - source_mean * scale
                            stack.apply_global_normalization_frame(index, scale, offset)
                    local_norm_frame_results.append(
                        {
                            "frame_id": str(frame["id"]),
                            "reference_frame_id": str(reference_frame["id"]),
                            "scale": float(scale),
                            "offset": float(offset),
                            "source_mean": None if source_stats is None else float(source_stats["mean"]),
                            "source_std": None if source_stats is None else float(source_stats["std"]),
                            "reference_mean": reference_mean,
                            "reference_std": reference_std,
                            "valid_pixels": None if source_stats is None else int(source_stats["valid_pixels"]),
                            "status": status,
                            "warnings": warnings,
                        }
                    )
            else:
                local_norm_warnings.append(
                    "resident CUDA local normalization disabled; use --local-normalization on for global LN"
                )
            local_norm_elapsed = perf_counter() - local_norm_start
            local_norm_groups.append(
                {
                    "filter": filter_name,
                    "enabled": local_norm_enabled,
                    "mode": local_norm_mode,
                    "reference_frame_id": str(reference_frame["id"]),
                    "reference_index": reference_index,
                    "crop_box": None,
                    "frame_results": local_norm_frame_results,
                    "timing_s": local_norm_elapsed,
                    "warnings": local_norm_warnings,
                }
            )

            integrate_start = perf_counter()
            coverage_map = None
            low_rejection_map = None
            high_rejection_map = None
            weights_array = np.asarray(frame_weight_values, dtype=np.float32)
            weights_arg = None if np.all(weights_array == 1.0) else weights_array
            if rejection_mode == "none":
                master, weight_map = stack.integrate_mean(weights_arg)
            else:
                if not hasattr(stack, "integrate_sigma_clip"):
                    raise RuntimeError("resident CUDA backend does not expose integrate_sigma_clip")
                winsorize = rejection_mode == "winsorized_sigma"
                (
                    master,
                    weight_map,
                    coverage_map,
                    low_rejection_map,
                    high_rejection_map,
                ) = stack.integrate_sigma_clip(weights_arg, low_sigma, high_sigma, winsorize)
            integrate_elapsed = perf_counter() - integrate_start
            output_diagnostics = _output_diagnostics(master, weight_map)
            master_path = output_dir / f"resident_master_{filt}.fits"
            weight_path = output_dir / f"resident_weight_map_{filt}.fits"
            coverage_path = output_dir / f"resident_coverage_map_{filt}.fits" if coverage_map is not None else None
            low_rejection_path = (
                output_dir / f"resident_low_rejection_map_{filt}.fits" if low_rejection_map is not None else None
            )
            high_rejection_path = (
                output_dir / f"resident_high_rejection_map_{filt}.fits" if high_rejection_map is not None else None
            )
            write_start = perf_counter()
            write_fits_data(master_path, master, {"IMAGETYP": "master", "FILTER": filter_name})
            write_fits_data(weight_path, weight_map, {"IMAGETYP": "weight", "FILTER": filter_name})
            if coverage_map is not None and coverage_path is not None:
                write_fits_data(coverage_path, coverage_map, {"IMAGETYP": "coverage", "FILTER": filter_name})
            if low_rejection_map is not None and low_rejection_path is not None:
                write_fits_data(low_rejection_path, low_rejection_map, {"IMAGETYP": "rej_low", "FILTER": filter_name})
            if high_rejection_map is not None and high_rejection_path is not None:
                write_fits_data(high_rejection_path, high_rejection_map, {"IMAGETYP": "rej_high", "FILTER": filter_name})
            write_elapsed = perf_counter() - write_start

            memory_estimate = _memory_estimate(len(light_frames), height, width)
            resident_artifacts.append(
                {
                    "filter": filter_name,
                    "frame_ids": [str(frame["id"]) for frame in light_frames],
                    "shape": {"height": height, "width": width},
                    "master_stats": master_stats,
                    "output_diagnostics": output_diagnostics,
                    "memory_estimate": memory_estimate,
                    "resident_bytes_allocated_after_master_upload": stack.bytes_allocated,
                    "timing_s": {
                        "master_build_or_load": master_elapsed,
                        "resident_allocate_and_master_upload": allocate_elapsed,
                        "registration_preview_setup": registration_setup_elapsed,
                        "light_read_upload_calibrate": load_calibrate_elapsed,
                        "resident_local_normalization": local_norm_elapsed,
                        "resident_integration": integrate_elapsed,
                        "output_write": write_elapsed,
                        "per_frame_mean": float(np.mean(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_min": float(np.min(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_max": float(np.max(per_frame_s)) if per_frame_s else 0.0,
                        "per_frame_registration_mean": (
                            float(np.mean(per_frame_registration_s)) if per_frame_registration_s else 0.0
                        ),
                    },
                    "resident_registration": {
                        "mode": resident_registration,
                        "reference_frame_id": str(reference_frame["id"]),
                        "preview_scale": preview_scale,
                        "max_shift": resident_registration_max_shift,
                        "subpixel_radius_steps": resident_subpixel_radius_steps,
                        "subpixel_step": resident_subpixel_step,
                        "failed_frame_count": int(np.count_nonzero(weights_array == 0.0)),
                        "excluded_frame_tokens": sorted(excluded_tokens),
                    },
                    "resident_local_normalization": {
                        "enabled": local_norm_enabled,
                        "mode": local_norm_mode,
                        "reference_frame_id": str(reference_frame["id"]),
                        "warning_count": len(local_norm_warnings),
                    },
                    "integration_rejection": {
                        "mode": rejection_mode,
                        "low_sigma": low_sigma,
                        "high_sigma": high_sigma,
                        "algorithm": (
                            "two_stage_winsorized_mean_std_rejection_approximation"
                            if rejection_mode == "winsorized_sigma"
                            else "two_pass_mean_std_clip"
                            if rejection_mode == "sigma_clip"
                            else "none"
                        ),
                    },
                    "notes": [
                        "Raw light frames are uploaded one at a time into a reusable device buffer.",
                        "Calibrated frames remain resident in VRAM until integration completes.",
                        "Resident registration is optional and currently limited to translation.",
                        (
                            "Resident local normalization uses a global mean/std model per frame."
                            if local_norm_enabled
                            else "Local normalization was disabled for this resident run."
                        ),
                    ],
                }
            )
            outputs.append(
                {
                    "filter": filt,
                    "frame_count": len(light_frames),
                    "master_path": str(master_path),
                    "weight_map_path": str(weight_path),
                    "coverage_map_path": None if coverage_path is None else str(coverage_path),
                    "low_rejection_map_path": None if low_rejection_path is None else str(low_rejection_path),
                    "high_rejection_map_path": None if high_rejection_path is None else str(high_rejection_path),
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "rejection": rejection_mode,
                    "weighting": "none",
                    "resident_registration": resident_registration,
                    "resident_local_normalization": local_norm_mode,
                    "estimated_peak_gib": memory_estimate["estimated_peak_gib"],
                    "resident_integration_s": integrate_elapsed,
                    "output_diagnostics": output_diagnostics,
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
        if registration_results:
            write_json(
                run / "registration_results.json",
                {
                    "schema_version": 1,
                    "source_stage": "resident_calibrated_stack",
                    "transform_model": resident_registration,
                    "results": registration_results,
                    "warnings": [
                        "resident registration is translation-only in the current gate",
                        "matched_stars/inliers/rms are placeholders until star-based registration is wired in",
                    ],
                },
            )
        local_norm_path = run / "local_norm_results.json"
        write_json(
            local_norm_path,
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "mode": "resident_global_mean_std"
                if any(group["enabled"] for group in local_norm_groups)
                else "off",
                "enabled": any(group["enabled"] for group in local_norm_groups),
                "crop_box": None,
                "groups": local_norm_groups,
                "warnings": [
                    "resident global LN is an early high-VRAM capability; full tile/window LN is not claimed here"
                ],
            },
        )
        integration_warnings = [
            "resident CUDA winsorized_sigma is currently a two-stage winsorized mean/std rejection approximation",
        ]
        if any(group["enabled"] for group in local_norm_groups):
            integration_warnings.append("resident CUDA used global mean/std local normalization before integration")
        else:
            integration_warnings.append("resident CUDA mode skipped local normalization")
        write_json(
            run / "integration_results.json",
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "combine": "mean",
                "weighting": "none",
                "rejection": rejection_mode,
                "low_sigma": low_sigma,
                "high_sigma": high_sigma,
                "frame_weights": frame_weights,
                "outputs": outputs,
                "excluded_frame_tokens": sorted(excluded_tokens),
                "warnings": integration_warnings,
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
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_local_normalization",
                path=str(local_norm_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.completed_stages.extend(
            [
                "master_calibration",
                "resident_light_calibration",
                *(["resident_registration"] if resident_registration != "off" else []),
                *(["resident_local_normalization"] if any(group["enabled"] for group in local_norm_groups) else []),
                "resident_integration",
            ]
        )
        state.current_stage = "integration"
        state.warnings.append(
            "resident CUDA mode is a high-VRAM calibration plus integration path; "
            "registration is translation only and local normalization is global mean/std when enabled"
        )
        return state
    except Exception as exc:
        state.failed_stage = state.current_stage
        state.errors.append(str(exc))
        raise
