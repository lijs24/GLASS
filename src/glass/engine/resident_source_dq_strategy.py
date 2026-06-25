from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Mapping

from glass.io.json_io import read_json
from glass.models import now_iso


def existing_disk_usage_path(path: Path) -> Path:
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate if candidate.exists() else Path.cwd()


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _load_plan(plan: str | Path | Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    if isinstance(plan, Mapping):
        return dict(plan), None
    path = Path(plan)
    return read_json(path), str(path)


def _ready_light_frame_ids(plan: Mapping[str, Any]) -> list[str]:
    ready: list[str] = []
    light_plans = plan.get("light_plans", [])
    if isinstance(light_plans, list):
        for light_plan in light_plans:
            if not isinstance(light_plan, Mapping) or light_plan.get("calibration_status") != "ready":
                continue
            ready.extend(str(frame_id) for frame_id in light_plan.get("frames", []))
    if ready:
        return ready
    return [
        str(frame.get("id"))
        for frame in plan.get("frames", [])
        if isinstance(frame, Mapping)
        and str(frame.get("frame_type") or "").lower() == "light"
        and frame.get("id") is not None
    ]


def build_resident_source_dq_strategy(
    plan: str | Path | Mapping[str, Any],
    run: str | Path,
    *,
    max_disk_fraction: float = 0.75,
    free_bytes: int | None = None,
    resident_mask_batch_frames: int = 1,
    resident_memory_budget_bytes: int | None = None,
    resident_inline_source_dq: str = "off",
    resident_inline_source_dq_policy: str = "default",
    resident_inline_source_dq_hot_sigma: float = 8.0,
    resident_inline_source_dq_cold_sigma: float = 8.0,
    resident_inline_source_dq_max_invalid_fraction: float = 0.0001,
    resident_inline_source_dq_admission: str = "all",
    artifact_type: str = "resident_source_dq_strategy",
) -> dict[str, Any]:
    plan_payload, plan_path = _load_plan(plan)
    run_path = Path(run)
    frames = {
        str(frame.get("id")): frame
        for frame in plan_payload.get("frames", [])
        if isinstance(frame, Mapping) and frame.get("id") is not None
    }
    ready_frame_ids = _ready_light_frame_ids(plan_payload)
    calibrated_bytes_per_pixel = 4
    dq_bytes_per_pixel = 2
    invalid_mask_bytes_per_pixel = 1
    cache_bytes_per_pixel = calibrated_bytes_per_pixel + dq_bytes_per_pixel
    estimated_payload_bytes = 0
    estimated_resident_mask_all_frames_bytes = 0
    unknown_shape_frame_ids: list[str] = []
    frame_pixels: list[int] = []
    for frame_id in ready_frame_ids:
        frame = frames.get(frame_id)
        width = None if frame is None else _positive_int(frame.get("width"))
        height = None if frame is None else _positive_int(frame.get("height"))
        if width is None or height is None:
            unknown_shape_frame_ids.append(frame_id)
            continue
        pixels = int(width) * int(height)
        frame_pixels.append(pixels)
        estimated_payload_bytes += pixels * cache_bytes_per_pixel
        estimated_resident_mask_all_frames_bytes += pixels * invalid_mask_bytes_per_pixel

    estimated_output_bytes = int(estimated_payload_bytes * 1.05)
    disk_usage_path = existing_disk_usage_path(run_path)
    if free_bytes is None:
        free_bytes = int(shutil.disk_usage(disk_usage_path).free)
    max_disk_fraction_clamped = max(0.0, min(1.0, float(max_disk_fraction)))
    max_allowed_bytes = int(max_disk_fraction_clamped * int(free_bytes))
    cache_passed = not unknown_shape_frame_ids and estimated_output_bytes <= max_allowed_bytes
    cache_reason = "ok"
    if unknown_shape_frame_ids:
        cache_reason = "unknown_light_shapes"
    elif estimated_output_bytes > max_allowed_bytes:
        cache_reason = "estimated_cache_exceeds_disk_budget"

    batch_frames = max(1, int(resident_mask_batch_frames or 1))
    max_frame_pixels = max(frame_pixels, default=0)
    estimated_resident_mask_batch_bytes = int(max_frame_pixels * batch_frames * invalid_mask_bytes_per_pixel)
    if resident_memory_budget_bytes is None:
        resident_mask_budget_status = "not_provided"
        resident_mask_fits_budget = None
    else:
        resident_mask_fits_budget = estimated_resident_mask_batch_bytes <= int(resident_memory_budget_bytes)
        resident_mask_budget_status = "fits" if resident_mask_fits_budget else "exceeds"

    if unknown_shape_frame_ids:
        recommended_route = "blocked_unknown_shape"
    elif cache_passed:
        recommended_route = "generate_calibration_cache_allowed"
    else:
        recommended_route = "resident_in_vram_mask_streaming"

    disk_cache = {
        "passed": cache_passed,
        "reason": cache_reason,
        "estimated_payload_bytes": estimated_payload_bytes,
        "estimated_output_bytes": estimated_output_bytes,
        "calibrated_bytes_per_pixel": calibrated_bytes_per_pixel,
        "dq_bytes_per_pixel": dq_bytes_per_pixel,
        "safety_multiplier": 1.05,
        "free_bytes": int(free_bytes),
        "max_disk_fraction": float(max_disk_fraction),
        "max_allowed_bytes": max_allowed_bytes,
    }
    resident_mask_streaming = {
        "strategy": "stream_invalid_mask_to_resident_stack",
        "invalid_mask_bytes_per_pixel": invalid_mask_bytes_per_pixel,
        "batch_frames": batch_frames,
        "estimated_batch_bytes": estimated_resident_mask_batch_bytes,
        "estimated_all_frames_bytes": estimated_resident_mask_all_frames_bytes,
        "memory_budget_bytes": resident_memory_budget_bytes,
        "memory_budget_status": resident_mask_budget_status,
        "fits_memory_budget": resident_mask_fits_budget,
        "semantics": (
            "Apply source-DQ invalid samples to resident calibrated frames in memory, "
            "then let resident CUDA integration skip NaN samples without materializing "
            "a full calibrated+DQ cache on disk."
        ),
    }
    inline_source_dq = {
        "mode": str(resident_inline_source_dq),
        "enabled": str(resident_inline_source_dq) != "off",
        "policy": str(resident_inline_source_dq_policy),
        "detector": (
            "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
            if str(resident_inline_source_dq) == "cosmetic_cuda"
            else "glass.cpu.cosmetic.detect_isolated_cosmetic_defects"
            if str(resident_inline_source_dq) == "cosmetic"
            else None
        ),
        "threshold_source": (
            "cuda_resident_histogram_median_mad_scalar"
            if str(resident_inline_source_dq) == "cosmetic_cuda"
            else None
        ),
        "detector_execution": (
            "cuda_isolated_threshold_apply" if str(resident_inline_source_dq) == "cosmetic_cuda" else None
        ),
        "hot_sigma": float(resident_inline_source_dq_hot_sigma),
        "cold_sigma": float(resident_inline_source_dq_cold_sigma),
        "max_invalid_fraction": float(resident_inline_source_dq_max_invalid_fraction),
        "admission": str(resident_inline_source_dq_admission),
        "admission_semantics": (
            "all resident frames are eligible for inline cosmetic source-DQ"
            if str(resident_inline_source_dq_admission) == "all"
            else "deferred cosmetic CUDA source-DQ is applied only to frames still admitted "
            "by registration/current positive-weight frame state"
        ),
        "high_fraction_guard_enabled": bool(
            str(resident_inline_source_dq) == "cosmetic_cuda"
            and float(resident_inline_source_dq_max_invalid_fraction) > 0.0
        ),
        "count_only_preflight": (
            "ResidentCalibratedStack.count_cosmetic_threshold_mask_frame"
            if str(resident_inline_source_dq) == "cosmetic_cuda"
            else None
        ),
        "materializes_calibrated_dq_cache": False,
        "semantics": (
            "Inline source-DQ mode creates resident invalid masks while loading frames; "
            "it excludes flagged samples from integration instead of replacing pixels."
        ),
    }
    payload = {
        "schema_version": 1,
        "artifact_type": artifact_type,
        "created_at": now_iso(),
        "passed": cache_passed,
        "reason": cache_reason,
        "recommended_route": recommended_route,
        "run_dir": str(run_path),
        "disk_usage_path": str(disk_usage_path),
        "plan_path": plan_path,
        "ready_light_frame_count": len(ready_frame_ids),
        "unknown_shape_frame_count": len(unknown_shape_frame_ids),
        "unknown_shape_frame_ids": unknown_shape_frame_ids[:20],
        "estimated_payload_bytes": estimated_payload_bytes,
        "estimated_output_bytes": estimated_output_bytes,
        "calibrated_bytes_per_pixel": calibrated_bytes_per_pixel,
        "dq_bytes_per_pixel": dq_bytes_per_pixel,
        "safety_multiplier": 1.05,
        "free_bytes": int(free_bytes),
        "max_disk_fraction": float(max_disk_fraction),
        "max_allowed_bytes": max_allowed_bytes,
        "disk_cache": disk_cache,
        "resident_mask_streaming": resident_mask_streaming,
        "inline_source_dq": inline_source_dq,
    }
    return payload
