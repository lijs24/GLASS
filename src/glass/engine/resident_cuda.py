from __future__ import annotations

import copy
import gc
import hashlib
import json
import os
from contextlib import ExitStack
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Condition, RLock
from time import perf_counter
from typing import Any, Iterable

import numpy as np

from glass.cpu.registration import estimate_translation_phase_correlation, translation_matrix
from glass.cpu.master_frames import image_stats
from glass.engine.contracts import (
    CombinePolicy,
    DQFlag,
    DQMask,
    OutputMapPolicy,
    RejectionPolicy,
    StackRequest,
    TileWindow,
)
from glass.engine.dq import dq_provenance_summary_from_resident, dq_provenance_summary_from_stack_engine
from glass.engine.stack_contract import build_stack_engine_result_contract
from glass.engine.stack_engine import CPUStackEngine, StackEngineResult, _apply_rejection, _combine_tile
from glass.engine.rejection import (
    RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_FRAME_THRESHOLD,
    RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_MAX_FRACTION,
    RESIDENT_WINSORIZED_SIGMA_AUTO_HARDENED_FRAME_LIMIT,
    RESIDENT_WINSORIZED_SIGMA_AUTO_MODE,
    RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT,
    RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE,
    RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE,
    resident_rejection_descriptor,
    rejection_policy_provenance,
    rejection_scale_estimator,
)
from glass.engine.resident_calibration_artifacts import write_resident_calibration_artifacts
from glass.engine.resident_dq_pixel_closure import (
    build_resident_dq_pixel_closure_group,
    summarize_resident_dq_pixel_closure_groups,
    validate_resident_dq_pixel_closure_group,
)
from glass.engine.resident_dq_lifecycle import (
    build_resident_dq_lifecycle_group,
    summarize_resident_dq_lifecycle_groups,
    validate_resident_dq_lifecycle_group,
)
from glass.engine.resident_frame_mask import (
    build_resident_frame_mask_contract,
    summarize_resident_frame_mask_contracts,
    validate_resident_frame_mask_contract,
)
from glass.engine.resident_light_pipeline_profile import build_resident_light_pipeline_profile
from glass.engine.resident_master_cache import (
    build_resident_master_cache_group,
    summarize_resident_master_cache_groups,
    validate_resident_master_cache_payload,
)
from glass.engine.resident_source_dq import (
    apply_resident_inline_cosmetic_thresholds,
    apply_resident_inline_cosmetic_thresholds_batch,
    apply_resident_source_invalid_mask,
    build_skipped_resident_inline_cosmetic_threshold_row,
    build_resident_source_dq_execution_group,
    build_resident_source_dq_summary,
    combine_source_invalid_masks,
    inline_cosmetic_thresholds_batch_from_resident_stack,
    inline_cosmetic_thresholds_from_resident_stack,
    inline_star_protected_cosmetic_thresholds_from_resident_stack,
    source_invalid_mask_from_array,
    source_invalid_mask_from_inline_cosmetic,
    source_invalid_mask_from_star_protected_inline_cosmetic,
    source_invalid_mask_from_sidecar_path,
    summarize_resident_source_dq_execution_groups,
    validate_resident_source_dq_execution_group,
)
from glass.engine.resident_registration_quality import (
    DEFAULT_RESIDENT_REGISTRATION_QUALITY_MIN_INLIERS,
    evaluate_resident_registration_quality,
    resident_registration_quality_warning_fields,
    summarize_resident_registration_quality,
)
from glass.engine.resident_stack_surface import build_resident_integration_stack_surface_contract
from glass.io.fits_fast import (
    FastFitsUnsupported,
    SIMPLE_FITS_SPEC_SUMMARY_KEY,
    SimpleFitsImageSpec,
    native_u16_gpu_fits_eligibility_from_spec,
    native_u16_gpu_fits_eligibility_with_spec,
    read_simple_fits_image_native_direct_timed,
    read_simple_fits_image_timed,
    read_simple_fits_u16be_raw_batch_timed,
    read_simple_fits_u16be_raw_timed,
    simple_fits_spec_from_summary,
    simple_fits_image_spec,
)
from glass.io.fits_io import (
    FitsImageReader,
    fits_write_backend,
    fits_write_profile,
    read_fits_data,
    write_fits_data,
)
from glass.io.image_source import FitsImageSource
from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy, PipelineArtifact, RegistrationResult, RunState, now_iso
from glass.gpu.tile_scheduler import iter_tiles
from glass.report.resident_result_contract import (
    build_resident_result_contract,
    write_resident_result_contract,
)
from glass.report.resident_calibration_contract import (
    build_resident_calibration_contract,
    write_resident_calibration_contract,
)


_AUTO_STAR_THRESHOLD_SIGMAS = (0.75, 1.0, 1.25, 1.5, 2.0, 3.0)
_RESIDENT_OUTPUT_MAP_POLICIES = {"audit", "science", "minimal"}
_RESIDENT_WINSORIZED_MODES = {
    RESIDENT_WINSORIZED_SIGMA_AUTO_MODE,
    RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
    RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
}
_RESIDENT_RESULT_RUNTIME_NONFATAL_CHECKS = {
    "active_frame_count_not_degenerate",
}


def _validate_resident_result_contract_payload(contract: dict[str, Any]) -> None:
    """Keep resident integration from completing with fatal result-contract failures."""

    if contract.get("passed") is True:
        return
    top_checks = contract.get("checks") if isinstance(contract.get("checks"), list) else []
    failed_top_checks = [
        str(check.get("name") or "unknown")
        for check in top_checks
        if isinstance(check, dict)
        and check.get("passed") is not True
        and check.get("name") != "resident_outputs_pass_contract"
    ]
    if failed_top_checks:
        raise RuntimeError(
            "resident CUDA result contract failed: top-level:"
            + ",".join(failed_top_checks)
        )
    outputs = contract.get("outputs") if isinstance(contract.get("outputs"), list) else []
    failed_outputs: list[dict[str, Any]] = []
    for index, output in enumerate(outputs):
        if not isinstance(output, dict) or output.get("passed") is True:
            continue
        checks = output.get("checks") if isinstance(output.get("checks"), list) else []
        failed_checks = [
            str(check.get("name") or "unknown")
            for check in checks
            if isinstance(check, dict) and check.get("passed") is not True
        ]
        fatal_failed_checks = [
            name for name in failed_checks if name not in _RESIDENT_RESULT_RUNTIME_NONFATAL_CHECKS
        ]
        if not fatal_failed_checks:
            continue
        failed_outputs.append(
            {
                "index": output.get("index", index),
                "filter": output.get("filter"),
                "status": output.get("status"),
                "failed_checks": fatal_failed_checks,
            }
        )
    if not failed_outputs:
        return
    failed_text = "; ".join(
        f"{item['filter'] or item['index']}:{','.join(item['failed_checks']) or item['status'] or 'failed'}"
        for item in failed_outputs
    )
    raise RuntimeError(
        "resident CUDA result contract failed"
        + (f": {failed_text}" if failed_text else "")
    )
_DEFAULT_CUDA_TRIANGLE_PIXEL_REFINE = False
_RESIDENT_MASTER_STACK_TILE_SIZE = 512
_RESIDENT_MASTER_CACHE_BUILDER = "resident_stack_engine_resident_cuda_policy_master_cache_v2"
_RESIDENT_MASTER_RAW_U16_STREAM_COUNT = 4
_RESIDENT_MASTER_RAW_U16_WAVE_FRAMES = 4
_OUTPUT_DIAGNOSTICS_EXACT_PERCENTILE_MAX_PIXELS = 2_000_000
_OUTPUT_DIAGNOSTICS_PERCENTILE_SAMPLE_PIXELS = 1_000_000


def _cuda_module_required():
    import glass_cuda

    if not glass_cuda.cuda_available() or not hasattr(glass_cuda, "ResidentCalibratedStack"):
        raise RuntimeError("resident CUDA mode requires the native ResidentCalibratedStack backend")
    return glass_cuda


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


_BATCH_WARP_PREFERRED_FRAMES = 8
_FUSED_MATRIX_REGISTRATION_MODES = {"off", "external_matrix", "similarity_cuda_triangle"}


def _resident_local_norm_enabled_for_admission(
    plan: dict[str, Any],
    local_normalization: str,
) -> bool:
    local_norm_policy = plan.get("local_normalization_policy", {})
    return local_normalization == "on" or (
        local_normalization == "auto"
        and isinstance(local_norm_policy, dict)
        and bool(local_norm_policy.get("enabled", False))
    )


def _resolve_resident_integration_dispatch_for_admission(
    plan: dict[str, Any],
    *,
    resident_registration: str,
    resident_integration_dispatch: str = "stack",
    resident_warp_interpolation: str = "bilinear",
    local_normalization: str = "auto",
    integration_rejection: str = "auto",
    resident_winsorized_mode: str = RESIDENT_WINSORIZED_SIGMA_AUTO_MODE,
    resident_output_maps: str = "audit",
) -> dict[str, Any]:
    requested = str(resident_integration_dispatch or "stack")
    rejection_mode = "none" if integration_rejection == "auto" else str(integration_rejection or "none")
    local_norm_enabled = _resident_local_norm_enabled_for_admission(plan, str(local_normalization or "auto"))
    reason = f"explicit_{requested}"
    effective = requested
    valid = True

    if requested == "auto":
        if (
            rejection_mode == "winsorized_sigma"
            and resident_winsorized_mode
            in {RESIDENT_WINSORIZED_SIGMA_AUTO_MODE, RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE}
            and (
                resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                or resident_output_maps != "minimal"
            )
        ):
            effective = "stack"
            reason = (
                "auto_stack_winsorized_auto_may_select_hardened"
                if resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_AUTO_MODE
                else "auto_stack_hardened_winsorized_requires_stack"
            )
        elif local_norm_enabled:
            effective = "stack"
            reason = "auto_stack_local_normalization_enabled"
        elif resident_registration not in _FUSED_MATRIX_REGISTRATION_MODES:
            effective = "stack"
            reason = "auto_stack_registration_mode_not_fused_supported"
        elif resident_warp_interpolation != "bilinear":
            effective = "stack"
            reason = "auto_stack_non_bilinear_matrix_route"
        else:
            effective = "fused_matrix"
            reason = "auto_fused_bilinear_matrix_route"
    elif requested == "fused_matrix":
        if local_norm_enabled:
            effective = "stack"
            reason = "admission_stack_explicit_fused_local_normalization_enabled"
            valid = False
        elif resident_registration not in _FUSED_MATRIX_REGISTRATION_MODES:
            effective = "stack"
            reason = "admission_stack_explicit_fused_registration_mode_not_supported"
            valid = False
        elif (
            rejection_mode == "winsorized_sigma"
            and resident_winsorized_mode
            in {RESIDENT_WINSORIZED_SIGMA_AUTO_MODE, RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE}
            and (
                resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                or resident_output_maps != "minimal"
            )
        ):
            effective = "stack"
            reason = (
                "admission_stack_explicit_fused_winsorized_auto_may_select_hardened"
                if resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_AUTO_MODE
                else "admission_stack_explicit_fused_hardened_winsorized_requires_stack"
            )
            valid = False
    elif requested != "stack":
        effective = "stack"
        reason = "admission_stack_unknown_integration_dispatch"
        valid = False

    return {
        "requested_mode": requested,
        "effective_mode": effective,
        "selection_reason": reason,
        "valid": valid,
        "fused_matrix_admission": bool(effective == "fused_matrix"),
        "resident_registration": resident_registration,
        "resident_warp_interpolation": resident_warp_interpolation,
        "local_normalization": local_normalization,
        "local_normalization_enabled": local_norm_enabled,
        "integration_rejection": integration_rejection,
        "resolved_rejection_mode": rejection_mode,
        "resident_winsorized_mode": resident_winsorized_mode,
        "resident_output_maps": resident_output_maps,
    }


def _chunked_warp_workspace_estimate(
    *,
    frame_count: int,
    height: int,
    width: int,
    enabled: bool,
    planned_warp_frame_count: int | None = None,
    planned_capacity_frames: int | None = None,
    observed_chunk_frames: int = 0,
    observed_workspace_bytes: int = 0,
    observed_output_bytes: int = 0,
    observed_coverage_bytes: int = 0,
    observed_inverse_bytes: int = 0,
) -> dict[str, Any]:
    pixels = int(height) * int(width)
    frame_bytes = pixels * 4
    planned_frames = max(0, int(planned_warp_frame_count if planned_warp_frame_count is not None else frame_count - 1))
    if enabled and planned_capacity_frames is not None:
        planned_capacity = max(0, min(planned_frames, int(planned_capacity_frames)))
    else:
        planned_capacity = min(planned_frames, _BATCH_WARP_PREFERRED_FRAMES) if enabled else 0
    planned_output_bytes = planned_capacity * frame_bytes
    planned_coverage_bytes = planned_capacity * pixels
    planned_inverse_bytes = planned_frames * 9 * 4 if enabled else 0
    planned_index_bytes = planned_frames * 8 if enabled else 0
    planned_workspace_bytes = (
        planned_output_bytes
        + planned_coverage_bytes
        + planned_inverse_bytes
        + planned_index_bytes
    )
    observed_workspace = int(observed_workspace_bytes)
    if observed_workspace <= 0:
        observed_workspace = (
            int(observed_output_bytes)
            + int(observed_coverage_bytes)
            + int(observed_inverse_bytes)
        )
    return {
        "chunked_warp_enabled": bool(enabled),
        "chunked_warp_preferred_capacity_frames": _BATCH_WARP_PREFERRED_FRAMES,
        "chunked_warp_planned_frame_count": planned_frames if enabled else 0,
        "chunked_warp_planned_capacity_frames": planned_capacity,
        "chunked_warp_planned_output_bytes": planned_output_bytes,
        "chunked_warp_planned_coverage_bytes": planned_coverage_bytes,
        "chunked_warp_planned_inverse_bytes": planned_inverse_bytes,
        "chunked_warp_planned_index_bytes": planned_index_bytes,
        "chunked_warp_planned_workspace_bytes": planned_workspace_bytes,
        "chunked_warp_planned_workspace_gib": planned_workspace_bytes / (1024**3),
        "chunked_warp_observed_capacity_frames": max(0, int(observed_chunk_frames)),
        "chunked_warp_observed_workspace_bytes": observed_workspace,
        "chunked_warp_observed_workspace_gib": observed_workspace / (1024**3),
        "chunked_warp_observed_output_bytes": int(observed_output_bytes),
        "chunked_warp_observed_coverage_bytes": int(observed_coverage_bytes),
        "chunked_warp_observed_inverse_bytes": int(observed_inverse_bytes),
        "chunked_warp_workspace_model": (
            "native_preferred_min_frame_count_8_with_halving_fallback" if enabled else "off"
        ),
    }


def _memory_estimate(
    frame_count: int,
    height: int,
    width: int,
    master_count: int = 3,
    *,
    resident_registration: str | None = None,
    resident_warp_batch_dispatch: str = "loop",
    chunked_warp_frame_count: int | None = None,
    chunked_warp_capacity_frames: int | None = None,
    observed_chunked_warp_chunk_frames: int = 0,
    observed_chunked_warp_workspace_bytes: int = 0,
    observed_chunked_warp_output_bytes: int = 0,
    observed_chunked_warp_coverage_bytes: int = 0,
    observed_chunked_warp_inverse_bytes: int = 0,
) -> dict[str, Any]:
    frame_bytes = int(height) * int(width) * 4
    calibrated_stack = frame_count * frame_bytes
    reusable_raw = frame_bytes
    masters = master_count * frame_bytes
    integration_outputs = 2 * frame_bytes
    weights = frame_count * 4
    base_peak = calibrated_stack + reusable_raw + masters + integration_outputs + weights
    chunked_warp = _chunked_warp_workspace_estimate(
        frame_count=frame_count,
        height=height,
        width=width,
        enabled=bool(
            resident_registration == "similarity_cuda_triangle"
            and resident_warp_batch_dispatch in {"chunked", "pipelined"}
        ),
        planned_warp_frame_count=chunked_warp_frame_count,
        planned_capacity_frames=chunked_warp_capacity_frames,
        observed_chunk_frames=observed_chunked_warp_chunk_frames,
        observed_workspace_bytes=observed_chunked_warp_workspace_bytes,
        observed_output_bytes=observed_chunked_warp_output_bytes,
        observed_coverage_bytes=observed_chunked_warp_coverage_bytes,
        observed_inverse_bytes=observed_chunked_warp_inverse_bytes,
    )
    chunked_workspace = max(
        int(chunked_warp["chunked_warp_planned_workspace_bytes"]),
        int(chunked_warp["chunked_warp_observed_workspace_bytes"]),
    )
    estimated_peak = base_peak + chunked_workspace
    return {
        "frame_bytes": frame_bytes,
        "frame_mib": frame_bytes / (1024**2),
        "calibrated_stack_bytes": calibrated_stack,
        "calibrated_stack_gib": calibrated_stack / (1024**3),
        "resident_base_bytes": calibrated_stack + reusable_raw + masters,
        "resident_base_gib": (calibrated_stack + reusable_raw + masters) / (1024**3),
        "integration_temporary_bytes": integration_outputs + weights,
        "integration_temporary_gib": (integration_outputs + weights) / (1024**3),
        "estimated_peak_without_chunked_warp_bytes": base_peak,
        "estimated_peak_without_chunked_warp_gib": base_peak / (1024**3),
        "estimated_peak_includes_chunked_warp_workspace": bool(chunked_workspace > 0),
        **chunked_warp,
        "estimated_peak_bytes": estimated_peak,
        "estimated_peak_gib": estimated_peak / (1024**3),
    }


def _as_plan_payload(plan: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(plan, dict):
        return plan
    return read_json(plan)


def _resident_memory_light_groups(plan: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[tuple[str | None, int, int], list[dict[str, Any]]] = {}
    for frame in _frames_by_type(plan, "light"):
        height = int(frame.get("height") or 0)
        width = int(frame.get("width") or 0)
        groups.setdefault((frame.get("filter"), height, width), []).append(frame)
    return [
        {
            "filter": filter_name,
            "height": height,
            "width": width,
            "frames": frames,
        }
        for (filter_name, height, width), frames in sorted(
            groups.items(),
            key=lambda item: (str(item[0][0]), item[0][1], item[0][2]),
        )
    ]


def _resident_planned_active_frame_count(
    frames: list[dict[str, Any]],
    *,
    exclude_frame_ids: list[str] | None = None,
) -> int:
    excludes = {str(frame_id) for frame_id in (exclude_frame_ids or []) if str(frame_id)}
    return sum(1 for frame in frames if not _matches_any_token(frame, excludes))


def _resident_chunk_capacity_candidates(preferred_capacity: int) -> list[int]:
    capacity = max(0, int(preferred_capacity))
    values: list[int] = []
    while capacity > 0:
        values.append(capacity)
        capacity //= 2
    if 0 not in values:
        values.append(0)
    return values


def _resident_capacity_option_for(
    capacity_options: list[dict[str, Any]],
    capacity: int,
) -> dict[str, Any] | None:
    for option in capacity_options:
        if int(option.get("chunked_warp_capacity_frames", -1)) == int(capacity):
            return option
    return None


def _resident_memory_budget_from_device(
    *,
    device_info: dict[str, Any] | None,
    explicit_budget_bytes: int | None,
    safety_fraction: float,
) -> tuple[int | None, str, float | None]:
    if explicit_budget_bytes is not None:
        return int(explicit_budget_bytes), "explicit_vram_budget_gb", None
    if not isinstance(device_info, dict):
        return None, "unavailable", None
    total_mib = device_info.get("memory_total_mib", device_info.get("total_global_mem_mib"))
    try:
        total_bytes = int(float(total_mib) * 1024 * 1024)
    except (TypeError, ValueError):
        return None, "unavailable", None
    fraction = min(1.0, max(0.0, float(safety_fraction)))
    return int(total_bytes * fraction), "device_total_memory_safety_fraction", fraction


def _resident_memory_device_info(cuda_module: Any | None) -> dict[str, Any] | None:
    if cuda_module is None or not hasattr(cuda_module, "get_device_info"):
        return None
    try:
        return dict(cuda_module.get_device_info(0))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"error": f"{type(exc).__name__}: {exc}"}


def build_resident_memory_admission(
    plan: str | Path | dict[str, Any],
    *,
    cuda_module: Any | None = None,
    resident_registration: str = "off",
    resident_warp_batch_dispatch: str = "chunked",
    resident_warp_chunk_capacity_frames: int | None = None,
    resident_integration_dispatch: str = "stack",
    resident_warp_interpolation: str = "bilinear",
    local_normalization: str = "auto",
    integration_rejection: str = "auto",
    resident_winsorized_mode: str = RESIDENT_WINSORIZED_SIGMA_AUTO_MODE,
    resident_output_maps: str = "audit",
    exclude_frame_ids: list[str] | None = None,
    vram_budget_gb: float | None = None,
    enforce_explicit_budget: bool = True,
    dispatch_explicit: bool = False,
    safety_fraction: float = 0.90,
) -> dict[str, Any]:
    payload = _as_plan_payload(plan)
    explicit_budget_bytes = None
    if vram_budget_gb is not None:
        explicit_budget_bytes = int(float(vram_budget_gb) * (1024**3))
    device_info = _resident_memory_device_info(cuda_module)
    budget_bytes, budget_source, budget_fraction = _resident_memory_budget_from_device(
        device_info=device_info,
        explicit_budget_bytes=explicit_budget_bytes,
        safety_fraction=safety_fraction,
    )
    integration_dispatch = _resolve_resident_integration_dispatch_for_admission(
        payload,
        resident_registration=resident_registration,
        resident_integration_dispatch=resident_integration_dispatch,
        resident_warp_interpolation=resident_warp_interpolation,
        local_normalization=local_normalization,
        integration_rejection=integration_rejection,
        resident_winsorized_mode=resident_winsorized_mode,
        resident_output_maps=resident_output_maps,
    )
    chunked_enabled = bool(
        resident_registration == "similarity_cuda_triangle"
        and resident_warp_batch_dispatch in {"chunked", "pipelined"}
        and not integration_dispatch["fused_matrix_admission"]
    )
    explicit_chunk_capacity: int | None = None
    try:
        parsed_chunk_capacity = (
            int(resident_warp_chunk_capacity_frames)
            if resident_warp_chunk_capacity_frames is not None
            else 0
        )
    except (TypeError, ValueError):
        parsed_chunk_capacity = 0
    if parsed_chunk_capacity > 0:
        explicit_chunk_capacity = parsed_chunk_capacity
    group_rows: list[dict[str, Any]] = []
    peak_row: dict[str, Any] | None = None
    for group in _resident_memory_light_groups(payload):
        frames = list(group["frames"])
        frame_count = len(frames)
        active_count = _resident_planned_active_frame_count(frames, exclude_frame_ids=exclude_frame_ids)
        warp_frame_count = max(0, active_count - 1) if chunked_enabled else 0
        preferred_capacity = (
            min(warp_frame_count, explicit_chunk_capacity or _BATCH_WARP_PREFERRED_FRAMES)
            if chunked_enabled
            else 0
        )
        preferred_capacity_source = (
            "explicit"
            if chunked_enabled and explicit_chunk_capacity is not None
            else "native_preferred"
            if chunked_enabled
            else "off"
        )
        preferred_estimate = _memory_estimate(
            frame_count,
            int(group["height"]),
            int(group["width"]),
            resident_registration=resident_registration,
            resident_warp_batch_dispatch=resident_warp_batch_dispatch,
            chunked_warp_frame_count=warp_frame_count,
            chunked_warp_capacity_frames=preferred_capacity,
        )
        capacity_options = []
        for capacity in _resident_chunk_capacity_candidates(preferred_capacity):
            estimate = _memory_estimate(
                frame_count,
                int(group["height"]),
                int(group["width"]),
                resident_registration=resident_registration,
                resident_warp_batch_dispatch=resident_warp_batch_dispatch,
                chunked_warp_frame_count=warp_frame_count,
                chunked_warp_capacity_frames=capacity,
            )
            capacity_options.append(
                {
                    "chunked_warp_capacity_frames": capacity,
                    "estimated_peak_bytes": estimate["estimated_peak_bytes"],
                    "estimated_peak_gib": estimate["estimated_peak_gib"],
                    "fits_budget": bool(
                        budget_bytes is None or int(estimate["estimated_peak_bytes"]) <= int(budget_bytes)
                    ),
                }
            )
        row = {
            "filter": group["filter"],
            "height": int(group["height"]),
            "width": int(group["width"]),
            "frame_count": frame_count,
            "planned_active_frame_count": active_count,
            "planned_warp_frame_count": warp_frame_count,
            "preferred_chunk_capacity_frames": preferred_capacity,
            "preferred_chunk_capacity_source": preferred_capacity_source,
            "requested_chunk_capacity_frames": explicit_chunk_capacity,
            "estimated_peak_bytes": preferred_estimate["estimated_peak_bytes"],
            "estimated_peak_gib": preferred_estimate["estimated_peak_gib"],
            "estimated_peak_without_chunked_warp_bytes": preferred_estimate[
                "estimated_peak_without_chunked_warp_bytes"
            ],
            "estimated_peak_includes_chunked_warp_workspace": preferred_estimate[
                "estimated_peak_includes_chunked_warp_workspace"
            ],
            "chunked_warp_planned_workspace_bytes": preferred_estimate[
                "chunked_warp_planned_workspace_bytes"
            ],
            "resident_integration_dispatch_effective": integration_dispatch["effective_mode"],
            "fused_matrix_admission": integration_dispatch["fused_matrix_admission"],
            "capacity_options": capacity_options,
        }
        group_rows.append(row)
        if peak_row is None or int(row["estimated_peak_bytes"]) > int(peak_row["estimated_peak_bytes"]):
            peak_row = row
    estimated_peak_bytes = int(peak_row["estimated_peak_bytes"]) if peak_row is not None else 0
    preferred_fits_budget = budget_bytes is None or estimated_peak_bytes <= int(budget_bytes)
    selected_capacity = peak_row.get("preferred_chunk_capacity_frames") if isinstance(peak_row, dict) else 0
    selected_capacity_source = (
        str(peak_row.get("preferred_chunk_capacity_source", "off")) if isinstance(peak_row, dict) else "off"
    )
    selected_option = (
        _resident_capacity_option_for(peak_row.get("capacity_options", []), int(selected_capacity))
        if isinstance(peak_row, dict)
        else None
    )
    reduced_capacity = None
    if not preferred_fits_budget and peak_row is not None:
        for option in peak_row.get("capacity_options", []):
            if option["fits_budget"]:
                reduced_capacity = int(option["chunked_warp_capacity_frames"])
                selected_option = option
                break
    explicit_budget = explicit_budget_bytes is not None
    if preferred_fits_budget:
        recommended_action = "resident_full_frame"
        status = "passed"
    elif reduced_capacity is not None and reduced_capacity > 0:
        recommended_action = "resident_reduced_chunk_capacity"
        status = "passed_reduced_chunk"
        selected_capacity = reduced_capacity
        selected_capacity_source = "reduced_for_budget"
    elif reduced_capacity == 0:
        recommended_action = "resident_loop_dispatch_or_tile_fallback"
        status = "passed_without_chunked_workspace"
        selected_capacity = 0
        selected_capacity_source = "disabled_for_budget"
    else:
        recommended_action = "tile_fallback"
        status = "failed"
    selected_estimated_peak_bytes = (
        int(selected_option["estimated_peak_bytes"])
        if isinstance(selected_option, dict)
        else estimated_peak_bytes
    )
    selected_fits_budget = budget_bytes is None or selected_estimated_peak_bytes <= int(budget_bytes)
    selected_dispatch = (
        "loop"
        if (
            resident_warp_batch_dispatch in {"chunked", "pipelined"}
            and recommended_action == "resident_loop_dispatch_or_tile_fallback"
        )
        else resident_warp_batch_dispatch
    )
    blocking = bool(
        enforce_explicit_budget
        and explicit_budget
        and not selected_fits_budget
    )
    artifact_status = "failed" if blocking else status if selected_fits_budget else f"warning_{status}"
    return {
        "schema_version": 1,
        "artifact_type": "resident_memory_admission",
        "created_at": now_iso(),
        "status": artifact_status,
        "passed": bool(selected_fits_budget or not blocking),
        "blocking": blocking,
        "reason": (
            "estimated_peak_exceeds_explicit_vram_budget"
            if blocking
            else "estimated_peak_within_budget"
            if preferred_fits_budget
            else "selected_reduced_capacity_within_budget"
            if selected_fits_budget
            else "estimated_peak_exceeds_recorded_budget"
        ),
        "resident_registration": resident_registration,
        "resident_integration_dispatch_requested": integration_dispatch["requested_mode"],
        "resident_integration_dispatch_effective": integration_dispatch["effective_mode"],
        "resident_integration_dispatch_reason": integration_dispatch["selection_reason"],
        "resident_integration_dispatch_admission": integration_dispatch,
        "fused_matrix_admission": integration_dispatch["fused_matrix_admission"],
        "requested_warp_batch_dispatch": resident_warp_batch_dispatch,
        "effective_warp_batch_dispatch": selected_dispatch,
        "dispatch_explicit": bool(dispatch_explicit),
        "recommended_action": recommended_action,
        "recommended_chunk_capacity_frames": selected_capacity,
        "selected_chunk_capacity_frames": selected_capacity,
        "selected_chunk_capacity_source": selected_capacity_source,
        "selected_warp_batch_dispatch": selected_dispatch,
        "selected_estimated_peak_bytes": selected_estimated_peak_bytes,
        "selected_estimated_peak_gib": selected_estimated_peak_bytes / (1024**3),
        "selected_fits_budget": selected_fits_budget,
        "preferred_fits_budget": preferred_fits_budget,
        "budget_bytes": budget_bytes,
        "budget_gib": (budget_bytes / (1024**3)) if budget_bytes is not None else None,
        "budget_source": budget_source,
        "budget_safety_fraction": budget_fraction,
        "explicit_budget": explicit_budget,
        "estimated_peak_bytes": estimated_peak_bytes,
        "estimated_peak_gib": estimated_peak_bytes / (1024**3),
        "headroom_bytes": (int(budget_bytes) - estimated_peak_bytes) if budget_bytes is not None else None,
        "headroom_gib": ((int(budget_bytes) - estimated_peak_bytes) / (1024**3))
        if budget_bytes is not None
        else None,
        "selected_headroom_bytes": (
            int(budget_bytes) - selected_estimated_peak_bytes
        )
        if budget_bytes is not None
        else None,
        "selected_headroom_gib": (
            (int(budget_bytes) - selected_estimated_peak_bytes) / (1024**3)
        )
        if budget_bytes is not None
        else None,
        "peak_group": peak_row,
        "groups": group_rows,
        "device": device_info,
        "limitations": [
            "Pre-run admission uses metadata dimensions and planned frame admission; actual native fallback capacity is recorded after execution.",
            "Reduced chunk capacity is selected pre-run and passed to native chunked matrix-warp dispatch; native may still lower capacity through its OOM fallback.",
            "When no explicit --vram-budget-gb is supplied, the device-total safety budget is recorded as evidence and does not block the run.",
        ],
    }


def _timing_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"total": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
    data = np.asarray(values, dtype=np.float64)
    return {
        "total": float(np.sum(data)),
        "mean": float(np.mean(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
    }


def _add_elapsed(buckets: dict[str, float], key: str, elapsed: float) -> None:
    buckets[key] = float(buckets.get(key, 0.0) + float(elapsed))


def _value_counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


def _resident_local_norm_application_summary(
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    timing_keys = (
        "coefficient_alloc_s",
        "coefficient_upload_s",
        "device_to_device_copy_s",
        "kernel_enqueue_s",
        "sync_s",
        "total_s",
    )
    timings = {key: 0.0 for key in timing_keys}
    mode_counts: dict[str, int] = {}
    temporary_output_bytes = 0
    coefficient_bytes = 0
    frame_bytes = 0
    in_place_modes = {"in_place_device_update", "in_place_device_update_batch"}
    for profile in profiles:
        mode = str(profile.get("mode") or "unknown")
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        for key in timing_keys:
            value = profile.get(key)
            if value is None:
                continue
            try:
                timings[key] += float(value)
            except (TypeError, ValueError):
                continue
        for key, target in (
            ("temporary_output_bytes", "temporary_output_bytes"),
            ("coefficient_bytes", "coefficient_bytes"),
            ("frame_bytes", "frame_bytes"),
        ):
            value = profile.get(key)
            if value is None:
                continue
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                continue
            if target == "temporary_output_bytes":
                temporary_output_bytes += numeric
            elif target == "coefficient_bytes":
                coefficient_bytes += numeric
            else:
                frame_bytes += numeric
    return {
        "schema_version": 1,
        "applied_frame_count": len(profiles),
        "mode_counts": dict(sorted(mode_counts.items())),
        "in_place_device_update_count": int(sum(mode_counts.get(mode, 0) for mode in in_place_modes)),
        "batch_apply_frame_count": int(mode_counts.get("in_place_device_update_batch", 0)),
        "temporary_output_bytes": int(temporary_output_bytes),
        "coefficient_bytes": int(coefficient_bytes),
        "frame_bytes": int(frame_bytes),
        "timing_s": timings,
        "peak_temporary_output_bytes_per_frame": 0
        if int(sum(mode_counts.get(mode, 0) for mode in in_place_modes)) == len(profiles)
        else None,
    }


def _resident_local_norm_grid_stats_summary(profile: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(profile, dict) or not profile:
        return {
            "schema_version": 1,
            "available": False,
            "mode": "per_frame_or_disabled",
            "batched": False,
        }
    return {
        "schema_version": 1,
        "available": True,
        "batched": True,
        "mode": str(profile.get("model", "resident_grid_pair_mean_std_batch")),
        "batch_model": str(profile.get("batch_model", "single_kernel_source_frame_tile_grid")),
        "reference_index": int(profile.get("reference_index", 0) or 0),
        "source_count": int(profile.get("source_count", 0) or 0),
        "grid_rows": int(profile.get("grid_rows", 0) or 0),
        "grid_cols": int(profile.get("grid_cols", 0) or 0),
        "grid_count": int(profile.get("grid_count", 0) or 0),
        "download_bytes": int(profile.get("download_bytes", 0) or 0),
        "index_bytes": int(profile.get("index_bytes", 0) or 0),
        "timing_s": {
            "allocation_s": float(profile.get("allocation_s", 0.0) or 0.0),
            "index_upload_s": float(profile.get("index_upload_s", 0.0) or 0.0),
            "kernel_enqueue_s": float(profile.get("kernel_enqueue_s", 0.0) or 0.0),
            "sync_s": float(profile.get("sync_s", 0.0) or 0.0),
            "download_s": float(profile.get("download_s", 0.0) or 0.0),
            "total_s": float(profile.get("total_s", 0.0) or 0.0),
        },
    }


def _resident_fits_read_mode_selection(
    light_frames: list[dict[str, Any]],
    *,
    height: int,
    width: int,
    requested_mode: str,
    raw_u16_runtime_reason: str,
) -> tuple[str, dict[str, Any], dict[str, SimpleFitsImageSpec]]:
    def _collect_raw_u16_specs() -> tuple[
        dict[str, SimpleFitsImageSpec],
        int,
        dict[str, int],
        list[dict[str, Any]],
        dict[str, int],
    ]:
        collected_specs: dict[str, SimpleFitsImageSpec] = {}
        collected_source_counts: dict[str, int] = {}
        collected_reason_counts: dict[str, int] = {}
        collected_ineligible_samples: list[dict[str, Any]] = []
        collected_eligible_count = 0
        for frame in light_frames:
            spec = None
            spec_source = "file_header_probe"
            header_summary = frame.get("header_summary", {})
            cached_summary = (
                header_summary.get(SIMPLE_FITS_SPEC_SUMMARY_KEY)
                if isinstance(header_summary, dict)
                else None
            )
            if isinstance(cached_summary, dict):
                try:
                    spec = simple_fits_spec_from_summary(frame["path"], cached_summary)
                    probe = native_u16_gpu_fits_eligibility_from_spec(
                        spec,
                        expected_shape=(int(height), int(width)),
                    )
                    spec_source = "plan_header_summary"
                except (FastFitsUnsupported, TypeError, ValueError):
                    spec = None
            if spec is None:
                probe, spec = native_u16_gpu_fits_eligibility_with_spec(
                    frame["path"],
                    expected_shape=(int(height), int(width)),
                )
            collected_source_counts[spec_source] = collected_source_counts.get(spec_source, 0) + 1
            if probe["eligible"]:
                collected_eligible_count += 1
                if spec is not None:
                    collected_specs[str(frame["path"])] = spec
            else:
                reason = str(probe.get("reason") or "unknown")
                collected_reason_counts[reason] = collected_reason_counts.get(reason, 0) + 1
                if len(collected_ineligible_samples) < 8:
                    collected_ineligible_samples.append(
                        {
                            "frame_id": str(frame.get("id", "")),
                            "path": str(frame.get("path", "")),
                            "reason": reason,
                        }
                    )
        return (
            collected_specs,
            collected_eligible_count,
            collected_reason_counts,
            collected_ineligible_samples,
            collected_source_counts,
        )

    def _update_raw_selection(
        *,
        collected_specs: dict[str, SimpleFitsImageSpec],
        eligible_count: int,
        reason_counts: dict[str, int],
        ineligible_samples: list[dict[str, Any]],
        source_counts: dict[str, int],
    ) -> None:
        raw_selection.update(
            {
                "checked": True,
                "checked_frame_count": len(light_frames),
                "eligible_frame_count": int(eligible_count),
                "fallback_reason_counts": dict(sorted(reason_counts.items())),
                "ineligible_samples": ineligible_samples,
                "eligible": int(eligible_count) == len(light_frames),
                "spec_cache_frame_count": len(collected_specs),
                "spec_source_counts": dict(sorted(source_counts.items())),
                "plan_header_spec_count": int(source_counts.get("plan_header_summary", 0)),
                "file_header_probe_count": int(source_counts.get("file_header_probe", 0)),
            }
        )

    raw_selection: dict[str, Any] = {
        "checked": False,
        "runtime_eligible": raw_u16_runtime_reason == "",
        "runtime_reason": raw_u16_runtime_reason,
        "selected": False,
        "eligible": False,
        "checked_frame_count": 0,
        "eligible_frame_count": 0,
        "spec_cache_frame_count": 0,
        "spec_source_counts": {},
        "plan_header_spec_count": 0,
        "file_header_probe_count": 0,
        "fallback_reason_counts": {},
        "ineligible_samples": [],
    }
    selection: dict[str, Any] = {
        "schema_version": 1,
        "requested_mode": requested_mode,
        "effective_mode": requested_mode,
        "policy": "explicit" if requested_mode != "auto" else "guarded_auto",
        "fallback_mode": None,
        "fallback_reason": "",
        "raw_u16_gpu": raw_selection,
    }
    if requested_mode != "auto":
        raw_selection["selected"] = requested_mode == "native_u16_gpu"
        if requested_mode != "native_u16_gpu" or raw_u16_runtime_reason:
            return requested_mode, selection, {}
        (
            spec_cache,
            eligible_count,
            reason_counts,
            ineligible_samples,
            spec_source_counts,
        ) = _collect_raw_u16_specs()
        _update_raw_selection(
            collected_specs=spec_cache,
            eligible_count=eligible_count,
            reason_counts=reason_counts,
            ineligible_samples=ineligible_samples,
            source_counts=spec_source_counts,
        )
        return requested_mode, selection, spec_cache

    if raw_u16_runtime_reason:
        selection["effective_mode"] = "auto"
        selection["fallback_mode"] = "auto"
        selection["fallback_reason"] = raw_u16_runtime_reason
        return "auto", selection, {}

    (
        spec_cache,
        eligible_count,
        reason_counts,
        ineligible_samples,
        spec_source_counts,
    ) = _collect_raw_u16_specs()
    _update_raw_selection(
        collected_specs=spec_cache,
        eligible_count=eligible_count,
        reason_counts=reason_counts,
        ineligible_samples=ineligible_samples,
        source_counts=spec_source_counts,
    )
    if eligible_count == len(light_frames):
        raw_selection["selected"] = True
        selection["effective_mode"] = "native_u16_gpu"
        return "native_u16_gpu", selection, spec_cache
    selection["effective_mode"] = "auto"
    selection["fallback_mode"] = "auto"
    selection["fallback_reason"] = "raw_u16_gpu_group_ineligible"
    return "auto", selection, {}


def _read_light_timed(
    path: str | Path,
    output: np.ndarray | None = None,
    fits_read_mode: str = "astropy",
    fits_spec: SimpleFitsImageSpec | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    if fits_read_mode not in {"auto", "fast", "astropy", "native_direct", "native_u16_gpu"}:
        raise ValueError("fits_read_mode must be auto, fast, astropy, native_direct, or native_u16_gpu")
    total_start = perf_counter()
    fallback_reason = ""
    if fits_read_mode == "native_u16_gpu":
        data, profile = read_simple_fits_u16be_raw_timed(path, output=output, spec=fits_spec)
        profile["fits_read_mode_requested"] = fits_read_mode
        profile["fits_fast_fallback_reason"] = ""
        return data, profile
    if fits_read_mode == "native_direct":
        data, profile = read_simple_fits_image_native_direct_timed(path, dtype=np.float32, output=output)
        profile["fits_read_mode_requested"] = fits_read_mode
        profile["fits_fast_fallback_reason"] = ""
        return data, profile
    if fits_read_mode in {"auto", "fast"}:
        try:
            data, profile = read_simple_fits_image_timed(path, dtype=np.float32, output=output)
            profile["fits_read_mode_requested"] = fits_read_mode
            profile["fits_fast_fallback_reason"] = ""
            return data, profile
        except FastFitsUnsupported as exc:
            if fits_read_mode == "fast":
                raise
            fallback_reason = str(exc)
    open_start = perf_counter()
    with FitsImageReader(path) as reader:
        open_elapsed = perf_counter() - open_start
        materialize_start = perf_counter()
        if output is None:
            data = reader.read_full(dtype=np.float32)
        else:
            data = reader.read_full_into(output)
        materialize_elapsed = perf_counter() - materialize_start
    total_elapsed = perf_counter() - total_start
    return data, {
        "total": total_elapsed,
        "fits_open": open_elapsed,
        "fits_materialize_decode": materialize_elapsed,
        "fits_reader_backend": "astropy_scaled_memmap",
        "fits_read_mode_requested": fits_read_mode,
        "fits_fast_supported": False,
        "fits_fast_fallback_reason": fallback_reason,
    }


def _read_light_batch_timed(
    items: list[tuple[int, str | Path, np.ndarray, SimpleFitsImageSpec | None]],
    max_workers: int,
) -> tuple[dict[int, tuple[np.ndarray, dict[str, Any]]], dict[str, Any]]:
    paths = [item[1] for item in items]
    outputs = [item[2] for item in items]
    specs = [item[3] for item in items]
    _raw_outputs, profiles, batch_profile = read_simple_fits_u16be_raw_batch_timed(
        paths,
        outputs,
        specs=specs,
        max_workers=max_workers,
    )
    by_index: dict[int, tuple[np.ndarray, dict[str, Any]]] = {}
    for (index, _path, output, _spec), profile in zip(items, profiles, strict=True):
        profile["fits_read_mode_requested"] = "native_u16_gpu"
        by_index[int(index)] = (output, profile)
    return by_index, batch_profile


class _LightPrefetcher:
    def __init__(
        self,
        light_frames: list[dict[str, Any]],
        depth: int,
        workers: int = 1,
        pinned_ring: bool = False,
        height: int | None = None,
        width: int | None = None,
        release_refill_mode: str = "immediate",
        fits_read_mode: str = "astropy",
        fits_specs_by_path: dict[str, SimpleFitsImageSpec] | None = None,
        native_batch_read: str = "off",
        native_queue_read: str = "off",
        native_queue_drain_mode: str | None = None,
    ):
        self.light_frames = light_frames
        self.depth = max(0, int(depth))
        self.workers = max(1, int(workers))
        self.pinned_ring = bool(pinned_ring and self.depth > 0)
        self.native_batch_read_candidate = bool(self.pinned_ring and fits_read_mode == "native_u16_gpu")
        self.native_queue_read_candidate = bool(self.pinned_ring and fits_read_mode == "native_u16_gpu")
        if native_batch_read not in {"off", "on"}:
            raise ValueError("native_batch_read must be off or on")
        if native_queue_read not in {"off", "on"}:
            raise ValueError("native_queue_read must be off or on")
        if native_queue_drain_mode is not None and native_queue_drain_mode not in {"thread", "inline"}:
            raise ValueError("native_queue_drain_mode must be thread, inline, or None")
        native_queue_policy = str(os.environ.get("GLASS_RESIDENT_NATIVE_QUEUE_READ", "")).strip().lower()
        self.native_queue_read_policy = (
            "cli_enabled"
            if native_queue_read == "on" and self.native_queue_read_candidate
            else "cli_requested_not_candidate"
            if native_queue_read == "on"
            else "env_enabled"
            if native_queue_policy in {"1", "true", "yes", "on"} and self.native_queue_read_candidate
            else "env_requested_not_candidate"
            if native_queue_policy in {"1", "true", "yes", "on"}
            else "env_disabled_default"
            if self.native_queue_read_candidate
            else "not_candidate"
        )
        self.native_queue_read_requested = bool(
            self.native_queue_read_candidate and self.native_queue_read_policy in {"cli_enabled", "env_enabled"}
        )
        native_queue_drain_source = "cli" if native_queue_drain_mode is not None else "env_or_default"
        native_queue_drain_value = str(
            native_queue_drain_mode
            if native_queue_drain_mode is not None
            else os.environ.get("GLASS_RESIDENT_NATIVE_QUEUE_DRAIN_MODE", "thread")
        ).strip().lower()
        self.native_queue_read_drain_mode = (
            "inline"
            if native_queue_drain_value in {"inline", "main", "direct"}
            else "thread"
        )
        self.native_queue_read_drain_source = native_queue_drain_source
        native_batch_policy = str(os.environ.get("GLASS_RESIDENT_NATIVE_BATCH_READ", "")).strip().lower()
        native_batch_env_enabled = native_batch_policy in {"1", "true", "yes", "on"}
        if self.native_queue_read_requested and native_batch_read == "on":
            self.native_batch_read_policy = "cli_ignored_native_queue_enabled"
        elif self.native_queue_read_requested and native_batch_env_enabled:
            self.native_batch_read_policy = "env_ignored_native_queue_enabled"
        elif native_batch_read == "on" and self.native_batch_read_candidate:
            self.native_batch_read_policy = "cli_enabled"
        elif native_batch_read == "on":
            self.native_batch_read_policy = "cli_requested_not_candidate"
        elif native_batch_env_enabled and self.native_batch_read_candidate:
            self.native_batch_read_policy = "env_enabled"
        elif native_batch_env_enabled:
            self.native_batch_read_policy = "env_requested_not_candidate"
        elif self.native_batch_read_candidate:
            self.native_batch_read_policy = "env_disabled_default"
        else:
            self.native_batch_read_policy = "not_candidate"
        self.native_batch_read_requested = bool(
            self.native_batch_read_candidate
            and not self.native_queue_read_requested
            and self.native_batch_read_policy in {"cli_enabled", "env_enabled"}
        )
        self.native_batch_read_available = False
        self.native_batch_read_enabled = False
        self.native_batch_read_frames = max(1, min(4, self.workers)) if self.native_batch_read_requested else 1
        self.native_queue_read_available = False
        self.native_queue_read_enabled = False
        if release_refill_mode not in {"immediate", "queued", "deferred"}:
            raise ValueError("release_refill_mode must be immediate, queued, or deferred")
        if fits_read_mode not in {"auto", "fast", "astropy", "native_direct", "native_u16_gpu"}:
            raise ValueError("fits_read_mode must be auto, fast, astropy, native_direct, or native_u16_gpu")
        self.release_refill_mode = release_refill_mode
        self.fits_read_mode = fits_read_mode
        self.fits_specs_by_path = dict(fits_specs_by_path or {})
        self.height = height
        self.width = width
        self.executor: ThreadPoolExecutor | None = None
        self.refill_executor: ThreadPoolExecutor | None = None
        self.refill_future: Future[None] | None = None
        self.native_queue_executor: ThreadPoolExecutor | None = None
        self.native_queue_future: Future[None] | None = None
        self.native_read_queue: Any | None = None
        self.native_queue_stopping = False
        self.lock = RLock()
        self.pending: dict[int, Future[tuple[np.ndarray, dict[str, float]]] | None] = {}
        self.batch_result_cache: dict[int, tuple[np.ndarray, dict[str, Any]]] = {}
        self.native_queue_result_cache: dict[int, tuple[np.ndarray, dict[str, Any]]] = {}
        self.native_queue_pending_profiles: dict[int, dict[str, Any]] = {}
        self.pinned_slots: list[np.ndarray] = []
        self.pinned_slab: np.ndarray | None = None
        self.pinned_host_allocation_mode = "off"
        self.pinned_host_allocation_count = 0
        self.pinned_host_allocation_fallback_reason = ""
        self.free_slots: list[int] = []
        self.inflight_slots: dict[int, int] = {}
        self.next_submit = 0
        self.fill_blocked_no_slot_count = 0
        self.fill_call_count = 0
        self.fill_submit_count = 0
        self.release_count = 0
        self.release_batch_count = 0
        self.release_refill_request_count = 0
        self.release_refill_queued_submit_count = 0
        self.release_refill_queued_execute_count = 0
        self.release_refill_queued_coalesced_count = 0
        self.release_refill_deferred_count = 0
        self.release_refill_wait_s = 0.0
        self.max_inflight_slots = 0
        self.ready_indices: set[int] = set()
        self.ready_condition = Condition(self.lock)
        self.ready_queue_callback_count = 0
        self.ready_queue_wait_count = 0
        self.ready_queue_wait_s = 0.0
        self.ready_candidate_probe_mode = "ready_set_intersection"
        self.ready_index_candidate_set_reuse_count = 0
        ready_batch_policy = str(os.environ.get("GLASS_RESIDENT_READY_BATCH_SELECT", "")).strip().lower()
        self.ready_batch_select_policy = (
            "env_enabled"
            if ready_batch_policy in {"1", "true", "yes", "on"}
            else "env_disabled_default"
        )
        self.ready_batch_select_enabled = self.ready_batch_select_policy == "env_enabled"
        self.ready_batch_select_count = 0
        self.ready_batch_selected_count = 0
        self.native_batch_read_submit_count = 0
        self.native_batch_read_frame_count = 0
        self.native_batch_read_max_frame_count = 0
        self.native_batch_read_worker_count = 0
        self.native_batch_read_wall_s = 0.0
        self.native_batch_read_cumulative_s = 0.0
        self.native_queue_read_submit_count = 0
        self.native_queue_read_completion_count = 0
        self.native_queue_read_worker_count = 0
        self.native_queue_read_cumulative_s = 0.0
        self.native_queue_read_completion_wait_s = 0.0
        self.native_queue_read_inline_wait_count = 0
        self.native_queue_read_thread_wait_count = 0

    def __enter__(self) -> "_LightPrefetcher":
        if self.depth > 0:
            if self.pinned_ring:
                if self.height is None or self.width is None:
                    raise ValueError("pinned resident prefetch requires image height and width")
                glass_cuda = _cuda_module_required()
                self.native_batch_read_available = bool(
                    self.native_batch_read_candidate
                    and hasattr(glass_cuda, "read_simple_fits_raw_batch_into_u8_available")
                    and glass_cuda.read_simple_fits_raw_batch_into_u8_available()
                )
                self.native_queue_read_available = bool(
                    self.native_queue_read_candidate
                    and hasattr(glass_cuda, "raw_fits_read_queue_available")
                    and glass_cuda.raw_fits_read_queue_available()
                )
                self.native_queue_read_enabled = bool(
                    self.native_queue_read_requested and self.native_queue_read_available
                )
                self.native_batch_read_enabled = bool(
                    self.native_batch_read_requested
                    and self.native_batch_read_available
                    and not self.native_queue_read_enabled
                )
                try:
                    if self.fits_read_mode == "native_u16_gpu":
                        byte_count = int(self.height) * int(self.width) * 2
                        self.pinned_slab = glass_cuda.host_pinned_empty_u8(byte_count * self.depth)
                        self.pinned_slots = [
                            self.pinned_slab[index * byte_count : (index + 1) * byte_count]
                            for index in range(self.depth)
                        ]
                    else:
                        self.pinned_slab = glass_cuda.host_pinned_empty_f32(
                            int(self.height) * self.depth,
                            int(self.width),
                        )
                        self.pinned_slots = [
                            self.pinned_slab[
                                index * int(self.height) : (index + 1) * int(self.height),
                                :,
                            ]
                            for index in range(self.depth)
                        ]
                    self.pinned_host_allocation_mode = "single_slab"
                    self.pinned_host_allocation_count = 1
                except Exception as exc:
                    self.pinned_slab = None
                    self.pinned_host_allocation_mode = "per_slot_fallback"
                    self.pinned_host_allocation_fallback_reason = type(exc).__name__
                    if self.fits_read_mode == "native_u16_gpu":
                        byte_count = int(self.height) * int(self.width) * 2
                        self.pinned_slots = [
                            glass_cuda.host_pinned_empty_u8(byte_count)
                            for _ in range(self.depth)
                        ]
                    else:
                        self.pinned_slots = [
                            glass_cuda.host_pinned_empty_f32(int(self.height), int(self.width))
                            for _ in range(self.depth)
                        ]
                    self.pinned_host_allocation_count = len(self.pinned_slots)
                self.free_slots = list(range(len(self.pinned_slots)))
            else:
                self.pinned_host_allocation_mode = "disabled"
            if self.native_queue_read_enabled:
                glass_cuda = _cuda_module_required()
                self.native_read_queue = glass_cuda.create_raw_fits_read_queue(self.workers)
                self.native_queue_read_worker_count = self.workers
                if self.native_queue_read_drain_mode == "thread":
                    self.native_queue_executor = ThreadPoolExecutor(
                        max_workers=1,
                        thread_name_prefix="glass-native-read-queue",
                    )
                    self.native_queue_future = self.native_queue_executor.submit(self._drain_native_queue)
            else:
                executor_workers = (
                    max(1, self.workers // max(1, self.native_batch_read_frames))
                    if self.native_batch_read_enabled
                    else self.workers
                )
                self.executor = ThreadPoolExecutor(
                    max_workers=executor_workers,
                    thread_name_prefix="glass-light-prefetch",
                )
            if self.pinned_ring and self.release_refill_mode == "queued":
                self.refill_executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="glass-light-refill",
                )
            self._fill()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.flush_refill()
        self.native_queue_stopping = True
        if self.native_read_queue is not None:
            self.native_read_queue.close()
        if self.native_queue_future is not None:
            self.native_queue_future.result()
            self.native_queue_future = None
        if self.native_queue_executor is not None:
            self.native_queue_executor.shutdown(wait=True, cancel_futures=True)
            self.native_queue_executor = None
        self.native_read_queue = None
        if self.refill_executor is not None:
            self.refill_executor.shutdown(wait=True, cancel_futures=True)
            self.refill_executor = None
        if self.executor is not None:
            self.executor.shutdown(wait=True, cancel_futures=True)
            self.executor = None

    def _prepare_native_queue_item(
        self,
        index: int,
        path: str | Path,
        output: np.ndarray,
        spec: SimpleFitsImageSpec | None,
    ) -> tuple[SimpleFitsImageSpec, int, dict[str, Any]]:
        header_cache_hit = spec is not None
        header_start = perf_counter()
        if spec is None:
            spec = simple_fits_image_spec(path)
        header_elapsed = 0.0 if header_cache_hit else perf_counter() - header_start
        if spec.bitpix != 16:
            raise FastFitsUnsupported("native_u16_gpu queue requires BITPIX=16 simple primary FITS")
        if spec.bscale != 1.0 or spec.bzero != 32768.0 or spec.blank is not None:
            raise FastFitsUnsupported("native_u16_gpu queue requires BSCALE=1, BZERO=32768, and no BLANK")
        byte_count = int(spec.width * spec.height * 2)
        if output.dtype != np.uint8:
            raise ValueError("native_u16_gpu queue output buffer requires uint8")
        if output.ndim != 1 or output.shape[0] != byte_count:
            raise ValueError("native_u16_gpu queue output buffer must have height*width*2 bytes")
        if not output.flags.c_contiguous:
            raise ValueError("native_u16_gpu queue output buffer must be C-contiguous")
        base_profile = {
            "frame_index": int(index),
            "header_elapsed": float(header_elapsed),
            "header_cache_hit": bool(header_cache_hit),
            "fits_fast_bitpix": int(spec.bitpix),
            "fits_raw_byte_count": int(byte_count),
        }
        return spec, byte_count, base_profile

    def _queue_completion_profile(
        self,
        completion: dict[str, Any],
        base_profile: dict[str, Any],
    ) -> dict[str, Any]:
        native_open_s = float(completion.get("file_open_s", 0.0) or 0.0)
        native_read_s = float(completion.get("file_read_s", 0.0) or 0.0)
        native_total_s = float(completion.get("total_s", 0.0) or 0.0)
        return {
            "total": float(base_profile.get("header_elapsed", 0.0)) + native_total_s,
            "fits_open": float(base_profile.get("header_elapsed", 0.0)) + native_open_s,
            "fits_materialize_decode": native_read_s,
            "fits_reader_backend": "native_u16be_raw_queue",
            "fits_fast_supported": True,
            "fits_fast_bitpix": int(base_profile.get("fits_fast_bitpix", 16)),
            "fits_fast_scaled": True,
            "fits_native_file_open_s": native_open_s,
            "fits_native_file_read_s": native_read_s,
            "fits_native_decode_s": 0.0,
            "fits_native_total_s": native_total_s,
            "fits_native_bytes_read": int(completion.get("bytes_read", 0) or 0),
            "fits_native_backend": str(completion.get("backend", "native_u16be_raw_queue")),
            "fits_raw_byte_count": int(base_profile.get("fits_raw_byte_count", 0) or 0),
            "fits_gpu_decode_staging": "u16be_bzero32768",
            "fits_header_cache_hit": bool(base_profile.get("header_cache_hit", False)),
            "fits_native_queue_worker_count": int(completion.get("worker_count", 0) or 0),
            "fits_native_queue_completed_count": int(completion.get("completed_count", 0) or 0),
        }

    def _consume_native_queue_completion(self, timeout_s: float = 0.1) -> bool:
        queue = self.native_read_queue
        if queue is None:
            return False
        wait_start = perf_counter()
        completion = queue.wait_completed(float(timeout_s))
        wait_elapsed = perf_counter() - wait_start
        self.native_queue_read_completion_wait_s += wait_elapsed
        if self.native_queue_read_drain_mode == "thread":
            self.native_queue_read_thread_wait_count += 1
        else:
            self.native_queue_read_inline_wait_count += 1
        if completion is None:
            return False
        completion_dict = dict(completion)
        index = int(completion_dict["frame_index"])
        with self.ready_condition:
            base_profile = self.native_queue_pending_profiles.pop(index, {})
            slot_id = self.inflight_slots.get(index)
            if slot_id is None:
                return False
            profile = self._queue_completion_profile(completion_dict, base_profile)
            self.native_queue_result_cache[index] = (self.pinned_slots[slot_id], profile)
            self.native_queue_read_completion_count += 1
            self.native_queue_read_cumulative_s += float(profile.get("fits_native_total_s", 0.0) or 0.0)
            self.ready_indices.add(index)
            self.ready_queue_callback_count += 1
            self.ready_condition.notify_all()
        return True

    def _drain_native_queue(self) -> None:
        while True:
            try:
                consumed = self._consume_native_queue_completion(0.1)
            except Exception:
                with self.ready_condition:
                    self.ready_condition.notify_all()
                raise
            if not consumed:
                if self.native_queue_stopping:
                    return
                continue

    def _fill(self) -> None:
        with self.lock:
            self.fill_call_count += 1
            if self.executor is None and not self.native_queue_read_enabled:
                return
            while self.next_submit < len(self.light_frames) and (
                len(self.inflight_slots) if self.pinned_ring else len(self.pending)
            ) < self.depth:
                slot: np.ndarray | None = None
                slot_id: int | None = None
                if self.pinned_ring:
                    if not self.free_slots:
                        if self.next_submit < len(self.light_frames):
                            self.fill_blocked_no_slot_count += 1
                        return
                    slot_id = self.free_slots.pop()
                    slot = self.pinned_slots[slot_id]
                if self.native_queue_read_enabled:
                    if slot_id is None or slot is None or self.native_read_queue is None:
                        return
                    frame = self.light_frames[self.next_submit]
                    submit_index = int(self.next_submit)
                    try:
                        spec, byte_count, base_profile = self._prepare_native_queue_item(
                            submit_index,
                            frame["path"],
                            slot,
                            self.fits_specs_by_path.get(str(frame["path"])),
                        )
                        self.native_read_queue.submit(
                            submit_index,
                            str(spec.path),
                            int(spec.data_offset),
                            int(byte_count),
                            slot,
                        )
                    except Exception:
                        if slot_id is not None:
                            self.free_slots.append(slot_id)
                        raise
                    self.pending[submit_index] = None
                    self.native_queue_pending_profiles[submit_index] = base_profile
                    self.inflight_slots[submit_index] = slot_id
                    self.max_inflight_slots = max(self.max_inflight_slots, len(self.inflight_slots))
                    self.fill_submit_count += 1
                    self.native_queue_read_submit_count += 1
                    self.next_submit += 1
                    continue
                if self.native_batch_read_enabled:
                    batch_items: list[tuple[int, str | Path, np.ndarray, SimpleFitsImageSpec | None]] = []
                    batch_slot_ids: list[tuple[int, int]] = []
                    if slot_id is not None and slot is not None:
                        frame = self.light_frames[self.next_submit]
                        submit_index = int(self.next_submit)
                        batch_items.append(
                            (
                                submit_index,
                                frame["path"],
                                slot,
                                self.fits_specs_by_path.get(str(frame["path"])),
                            )
                        )
                        batch_slot_ids.append((submit_index, slot_id))
                        self.next_submit += 1
                    while (
                        self.next_submit < len(self.light_frames)
                        and len(batch_items) < self.native_batch_read_frames
                        and (
                            len(self.inflight_slots) + len(batch_items)
                            if self.pinned_ring
                            else len(self.pending) + len(batch_items)
                        )
                        < self.depth
                    ):
                        if not self.free_slots:
                            if self.next_submit < len(self.light_frames):
                                self.fill_blocked_no_slot_count += 1
                            break
                        next_slot_id = self.free_slots.pop()
                        next_slot = self.pinned_slots[next_slot_id]
                        frame = self.light_frames[self.next_submit]
                        submit_index = int(self.next_submit)
                        batch_items.append(
                            (
                                submit_index,
                                frame["path"],
                                next_slot,
                                self.fits_specs_by_path.get(str(frame["path"])),
                            )
                        )
                        batch_slot_ids.append((submit_index, next_slot_id))
                        self.next_submit += 1
                    if not batch_items:
                        return
                    future = self.executor.submit(
                        _read_light_batch_timed,
                        batch_items,
                        min(self.native_batch_read_frames, len(batch_items)),
                    )
                    for submit_index, used_slot_id in batch_slot_ids:
                        self.pending[submit_index] = future
                        self.inflight_slots[submit_index] = used_slot_id
                        future.add_done_callback(
                            lambda _future, index=submit_index: self._mark_ready(index)
                        )
                    self.max_inflight_slots = max(self.max_inflight_slots, len(self.inflight_slots))
                    self.fill_submit_count += len(batch_items)
                    self.native_batch_read_submit_count += 1
                    self.native_batch_read_frame_count += len(batch_items)
                    self.native_batch_read_max_frame_count = max(
                        self.native_batch_read_max_frame_count,
                        len(batch_items),
                    )
                    self.native_batch_read_worker_count = max(
                        self.native_batch_read_worker_count,
                        min(self.native_batch_read_frames, len(batch_items)),
                    )
                else:
                    frame = self.light_frames[self.next_submit]
                    fits_spec = self.fits_specs_by_path.get(str(frame["path"]))
                    submit_index = int(self.next_submit)
                    future = self.executor.submit(
                        _read_light_timed,
                        frame["path"],
                        slot,
                        self.fits_read_mode,
                        fits_spec,
                    )
                    self.pending[submit_index] = future
                    future.add_done_callback(
                        lambda _future, index=submit_index: self._mark_ready(index)
                    )
                    if slot_id is not None:
                        self.inflight_slots[submit_index] = slot_id
                        self.max_inflight_slots = max(self.max_inflight_slots, len(self.inflight_slots))
                    self.fill_submit_count += 1
                    self.next_submit += 1

    def _mark_ready(self, index: int) -> None:
        with self.ready_condition:
            if index not in self.pending:
                return
            self.ready_indices.add(index)
            self.ready_queue_callback_count += 1
            self.ready_condition.notify_all()

    def _queued_fill(self) -> None:
        self.release_refill_queued_execute_count += 1
        self._fill()

    def _request_fill_after_release(self) -> None:
        self.release_refill_request_count += 1
        if self.release_refill_mode == "deferred":
            self.release_refill_deferred_count += 1
            return
        if self.release_refill_mode != "queued" or self.refill_executor is None:
            self._fill()
            return
        with self.lock:
            if self.refill_future is not None and not self.refill_future.done():
                self.release_refill_queued_coalesced_count += 1
                return
            self.release_refill_queued_submit_count += 1
            self.refill_future = self.refill_executor.submit(self._queued_fill)

    def flush_refill(self) -> None:
        refill_future = self.refill_future
        if refill_future is not None:
            wait_start = perf_counter()
            refill_future.result()
            self.release_refill_wait_s += perf_counter() - wait_start
        if self.release_refill_mode == "deferred" and self.release_refill_deferred_count > 0:
            self._fill()
            self.release_refill_deferred_count = 0

    def result(self, index: int) -> tuple[np.ndarray, dict[str, Any], float]:
        if self.native_queue_read_enabled:
            wait_start = perf_counter()
            while True:
                with self.ready_condition:
                    cached = self.native_queue_result_cache.pop(index, None)
                    if cached is not None:
                        self.pending.pop(index, None)
                        self.ready_indices.discard(index)
                        return cached[0], cached[1], perf_counter() - wait_start
                    if index not in self.pending:
                        if self.next_submit < len(self.light_frames):
                            break
                        raise KeyError(f"native queue has no pending light frame {index}")
                    if self.native_queue_read_drain_mode == "thread":
                        self.ready_condition.wait(timeout=0.1)
                        continue
                self._consume_native_queue_completion(0.1)
            self._fill()
            return self.result(index)
        if self.executor is None:
            frame_path = self.light_frames[index]["path"]
            data, read_profile = _read_light_timed(
                frame_path,
                fits_read_mode=self.fits_read_mode,
                fits_spec=self.fits_specs_by_path.get(str(frame_path)),
            )
            return data, read_profile, read_profile["total"]
        cached = self.batch_result_cache.pop(index, None)
        if cached is not None:
            with self.lock:
                self.pending.pop(index, None)
                self.ready_indices.discard(index)
            return cached[0], cached[1], 0.0
        with self.lock:
            future = self.pending.pop(index, None)
            self.ready_indices.discard(index)
        if future is None:
            self.flush_refill()
            with self.lock:
                future = self.pending.pop(index, None)
                self.ready_indices.discard(index)
        if future is None:
            self._fill()
            with self.lock:
                future = self.pending.pop(index)
                self.ready_indices.discard(index)
        wait_start = perf_counter()
        payload = future.result()
        wait_elapsed = perf_counter() - wait_start
        if (
            isinstance(payload, tuple)
            and len(payload) == 2
            and isinstance(payload[0], dict)
            and "fits_native_batch_frame_count" not in payload[0]
        ):
            batch_results, batch_profile = payload
            self.native_batch_read_wall_s += float(batch_profile.get("fits_native_total_s", 0.0) or 0.0)
            self.native_batch_read_cumulative_s += float(
                batch_profile.get("fits_native_cumulative_total_s", 0.0) or 0.0
            )
            selected = batch_results.pop(index)
            self.batch_result_cache.update(batch_results)
            data, read_profile = selected
        else:
            data, read_profile = payload
        if not self.pinned_ring:
            self._fill()
        return data, read_profile, wait_elapsed

    def _ready_candidate_indices_locked(self, candidates: set[int]) -> list[int]:
        if not candidates or not self.ready_indices:
            return []
        if len(self.ready_indices) <= len(candidates):
            ready = self.ready_indices.intersection(candidates)
        else:
            ready = candidates.intersection(self.ready_indices)
        if ready:
            ready.intersection_update(self.pending.keys())
        return sorted(ready)

    def ready_index(self, indices: Iterable[int]) -> int | None:
        if isinstance(indices, set):
            candidates = indices
            self.ready_index_candidate_set_reuse_count += 1
        else:
            candidates = {int(index) for index in indices}
        if not candidates:
            return None
        if self.executor is None and not self.native_queue_read_enabled:
            return min(candidates)
        while True:
            with self.ready_condition:
                ready = self._ready_candidate_indices_locked(candidates)
                if ready:
                    return min(ready)
                has_pending_candidate = any(index in self.pending for index in candidates)
                if has_pending_candidate:
                    wait_start = perf_counter()
                    self.ready_queue_wait_count += 1
                    if self.native_queue_read_enabled and self.native_queue_read_drain_mode == "inline":
                        self.ready_condition.release()
                        try:
                            self._consume_native_queue_completion(0.1)
                        finally:
                            self.ready_condition.acquire()
                    else:
                        self.ready_condition.wait(timeout=0.1)
                    self.ready_queue_wait_s += perf_counter() - wait_start
                    continue
            self.flush_refill()
            self._fill()
            with self.lock:
                has_pending = any(index in candidates for index in self.pending)
            if not has_pending:
                return None

    def ready_indices_batch(self, indices: Iterable[int], limit: int) -> list[int]:
        candidates = {int(index) for index in indices}
        max_count = max(0, int(limit))
        if not candidates or max_count <= 0:
            return []
        self.ready_batch_select_count += 1
        if self.executor is None and not self.native_queue_read_enabled:
            selected = sorted(candidates)[:max_count]
            self.ready_batch_selected_count += len(selected)
            return selected

        selected: list[int] = []
        while candidates and len(selected) < max_count:
            with self.ready_condition:
                ready = self._ready_candidate_indices_locked(candidates)
                if ready:
                    take = ready[: max_count - len(selected)]
                    selected.extend(take)
                    for index in take:
                        candidates.discard(index)
                    self.ready_batch_selected_count += len(take)
                    if len(selected) >= max_count:
                        return selected
                has_pending_candidate = any(index in self.pending for index in candidates)
                if has_pending_candidate:
                    wait_start = perf_counter()
                    self.ready_queue_wait_count += 1
                    if self.native_queue_read_enabled and self.native_queue_read_drain_mode == "inline":
                        self.ready_condition.release()
                        try:
                            self._consume_native_queue_completion(0.1)
                        finally:
                            self.ready_condition.acquire()
                    else:
                        self.ready_condition.wait(timeout=0.1)
                    self.ready_queue_wait_s += perf_counter() - wait_start
                    continue
                if selected:
                    return selected
            self.flush_refill()
            self._fill()
            with self.lock:
                has_pending = any(index in candidates for index in self.pending)
            if not has_pending:
                return selected
        return selected

    def release(self, index: int) -> None:
        self.release_many([index])

    def release_many(self, indices: list[int]) -> None:
        if not self.pinned_ring:
            return
        released = 0
        with self.lock:
            for index in indices:
                slot_id = self.inflight_slots.pop(index, None)
                if slot_id is None:
                    continue
                self.free_slots.append(slot_id)
                released += 1
        if released == 0:
            return
        self.release_count += released
        self.release_batch_count += 1
        self._request_fill_after_release()

    @property
    def host_pinned_bytes(self) -> int:
        if not self.pinned_slots:
            return 0
        return int(sum(slot.nbytes for slot in self.pinned_slots))


def _grid_local_norm_coefficients(stats: dict[str, Any], eps: float = 1.0e-6) -> dict[str, Any]:
    source_mean = np.asarray(stats["source_mean"], dtype=np.float32)
    source_std = np.asarray(stats["source_std"], dtype=np.float32)
    reference_mean = np.asarray(stats["reference_mean"], dtype=np.float32)
    reference_std = np.asarray(stats["reference_std"], dtype=np.float32)
    valid_pixels = np.asarray(stats["valid_pixels"], dtype=np.uint64)
    scales = np.ones_like(source_mean, dtype=np.float32)
    offsets = np.zeros_like(source_mean, dtype=np.float32)
    statuses: list[list[str]] = []
    empty_tiles = 0
    offset_only_tiles = 0
    ok_tiles = 0
    for row in range(source_mean.shape[0]):
        status_row: list[str] = []
        for col in range(source_mean.shape[1]):
            if int(valid_pixels[row, col]) == 0:
                empty_tiles += 1
                status_row.append("empty")
                continue
            if float(source_std[row, col]) <= eps or float(reference_std[row, col]) <= eps:
                offset_only_tiles += 1
                offsets[row, col] = np.float32(reference_mean[row, col] - source_mean[row, col])
                status_row.append("offset_only")
                continue
            scale = np.float32(reference_std[row, col] / source_std[row, col])
            scales[row, col] = scale
            offsets[row, col] = np.float32(reference_mean[row, col] - source_mean[row, col] * scale)
            ok_tiles += 1
            status_row.append("ok")
        statuses.append(status_row)
    active = valid_pixels > 0
    active_scales = scales[active]
    active_offsets = offsets[active]
    return {
        "scales": scales,
        "offsets": offsets,
        "valid_pixels": valid_pixels,
        "statuses": statuses,
        "empty_tiles": empty_tiles,
        "offset_only_tiles": offset_only_tiles,
        "ok_tiles": ok_tiles,
        "scale_mean": float(np.mean(active_scales)) if active_scales.size else 1.0,
        "scale_min": float(np.min(active_scales)) if active_scales.size else 1.0,
        "scale_max": float(np.max(active_scales)) if active_scales.size else 1.0,
        "offset_mean": float(np.mean(active_offsets)) if active_offsets.size else 0.0,
        "offset_min": float(np.min(active_offsets)) if active_offsets.size else 0.0,
        "offset_max": float(np.max(active_offsets)) if active_offsets.size else 0.0,
        "valid_pixel_total": int(np.sum(valid_pixels, dtype=np.uint64)),
    }


def _simple_snr_weight_from_stats(stats: dict[str, Any], eps: float = 1.0e-6) -> float:
    if int(stats.get("valid_pixels") or 0) <= 0:
        return 0.0
    std = float(stats.get("std") or 0.0)
    mean = abs(float(stats.get("mean") or 0.0))
    if std <= eps:
        return 1.0 / eps
    return max(mean / std, eps)


def _preview_scale(height: int, width: int, target_max_dim: int = 1024) -> int:
    return max(1, (max(int(height), int(width)) + int(target_max_dim) - 1) // int(target_max_dim))


def _registration_preview(image: np.ndarray, scale: int) -> np.ndarray:
    preview = np.asarray(image, dtype=np.float32)[:: int(scale), :: int(scale)]
    return np.ascontiguousarray(np.nan_to_num(preview, nan=0.0, posinf=0.0, neginf=0.0), dtype=np.float32)


def _frame_reference_tokens(frame: dict[str, Any]) -> set[str]:
    path = Path(str(frame.get("path", "")))
    return {str(frame.get("id", "")), path.name, path.stem}


def _frame_header_value(
    frame: dict[str, Any],
    key: str,
    cache: dict[tuple[str, str], Any] | None = None,
) -> Any | None:
    key_upper = str(key).upper()
    summary = frame.get("header_summary", {})
    if isinstance(summary, dict):
        for candidate in (key, key_upper, key_upper.lower()):
            if candidate in summary:
                return summary[candidate]

    path = str(frame.get("path") or "")
    if not path:
        return None
    cache_key = (path, key_upper)
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    value = None
    try:
        from astropy.io import fits

        header = fits.getheader(path, 0)
        value = header.get(key_upper)
    except Exception:
        value = None
    if cache is not None:
        cache[cache_key] = value
    return value


def _normalize_pierside(value: Any | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in {"e", "east", "pier east", "east side", "east-of-pier"}:
        return "east"
    if text in {"w", "west", "pier west", "west side", "west-of-pier"}:
        return "west"
    return text


def _resident_similarity_frame_dispatch(
    resident_star_prior: str,
    reference_frame: dict[str, Any],
    moving_frame: dict[str, Any],
    header_cache: dict[tuple[str, str], Any] | None = None,
) -> dict[str, Any]:
    if resident_star_prior != "auto_pierside":
        return {
            "prior": resident_star_prior,
            "orientation_mode": "manual",
            "reference_pierside": None,
            "moving_pierside": None,
        }

    reference_pierside = _normalize_pierside(_frame_header_value(reference_frame, "PIERSIDE", header_cache))
    moving_pierside = _normalize_pierside(_frame_header_value(moving_frame, "PIERSIDE", header_cache))
    if reference_pierside and moving_pierside:
        if reference_pierside == moving_pierside:
            return {
                "prior": "ncc",
                "orientation_mode": "pierside_same",
                "reference_pierside": reference_pierside,
                "moving_pierside": moving_pierside,
            }
        return {
            "prior": "none",
            "orientation_mode": "pierside_flipped",
            "reference_pierside": reference_pierside,
            "moving_pierside": moving_pierside,
        }
    return {
        "prior": "ncc",
        "orientation_mode": "pierside_unknown",
        "reference_pierside": reference_pierside,
        "moving_pierside": moving_pierside,
    }


def _find_reference_frame(light_frames: list[dict[str, Any]], reference_frame_id: str | None) -> dict[str, Any]:
    if reference_frame_id:
        for frame in light_frames:
            if str(reference_frame_id) in _frame_reference_tokens(frame):
                return frame
        raise ValueError(f"reference frame was not found in resident light group: {reference_frame_id}")
    return light_frames[0]


def _quality_reference_frame_id(run: Path, light_frames: list[dict[str, Any]]) -> tuple[str | None, str, str | None]:
    quality_path = run / "frame_quality.json"
    if not quality_path.exists():
        return None, "absent", None
    try:
        quality = read_json(quality_path)
    except Exception as exc:
        return None, f"unreadable:{exc}", str(quality_path)
    reference = quality.get("reference_frame_id") if isinstance(quality, dict) else None
    if not reference:
        return None, "missing_reference_frame_id", str(quality_path)
    reference_text = str(reference)
    for frame in light_frames:
        if reference_text in _frame_reference_tokens(frame):
            return reference_text, "frame_quality", str(quality_path)
    return None, f"unmatched:{reference_text}", str(quality_path)


def _matches_any_token(frame: dict[str, Any], tokens: set[str]) -> bool:
    return bool(_frame_reference_tokens(frame) & tokens)


def _registration_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("registration_results")
    if rows is None:
        rows = payload.get("results", [])
    return [dict(row) for row in rows]


def _resident_registration_quality_decision(
    *,
    decisions_by_frame: dict[str, dict[str, Any]],
    frame_id: str,
    registration_mode: str,
    requested_action: str,
    status: str,
    matched_stars: int,
    inliers: int,
    rms_px: float,
    min_inliers: int,
    max_rms_px: float | None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision = evaluate_resident_registration_quality(
        frame_id=str(frame_id),
        registration_mode=registration_mode,
        requested_action=requested_action,
        status=status,
        matched_stars=int(matched_stars),
        inliers=int(inliers),
        rms_px=rms_px,
        min_inliers=int(min_inliers),
        max_rms_px=max_rms_px,
        diagnostics=diagnostics,
    )
    decisions_by_frame[str(frame_id)] = decision
    return decision


def _registration_matrix(row: dict[str, Any]) -> list[list[float]]:
    matrix = np.asarray(row.get("matrix"), dtype=np.float64)
    if matrix.shape != (3, 3):
        raise ValueError(f"external registration matrix for {row.get('frame_id')} must be 3x3")
    return [[float(value) for value in line] for line in matrix]


def _matrix_is_translation(matrix: list[list[float]], atol: float = 1.0e-6) -> bool:
    m = np.asarray(matrix, dtype=np.float64)
    if m.shape != (3, 3):
        return False
    return bool(
        np.allclose(m[:2, :2], np.eye(2), atol=atol)
        and np.allclose(m[2], np.asarray([0.0, 0.0, 1.0]), atol=atol)
    )


def _resident_triangle_translation_refine(
    reference_catalog: dict[str, Any] | None,
    moving_catalog: dict[str, Any] | None,
    seed_matrix: Any,
    *,
    tolerance_px: float,
    min_inliers: int,
    max_correction_px: float,
    iterations: int = 2,
    iteration_max_step_px: float | None = 0.005,
) -> dict[str, Any]:
    seed = np.asarray(seed_matrix, dtype=np.float64).reshape(3, 3)
    if reference_catalog is None or moving_catalog is None:
        return {"applied": False, "status": "missing_catalog", "matrix": seed.tolist()}
    reference_count = int(reference_catalog.get("stored_count", len(reference_catalog.get("x", []))) or 0)
    moving_count = int(moving_catalog.get("stored_count", len(moving_catalog.get("x", []))) or 0)
    if reference_count <= 0 or moving_count <= 0:
        return {"applied": False, "status": "empty_catalog", "matrix": seed.tolist()}

    reference = np.column_stack(
        [
            np.asarray(reference_catalog.get("x", []), dtype=np.float64)[:reference_count],
            np.asarray(reference_catalog.get("y", []), dtype=np.float64)[:reference_count],
        ]
    )
    moving = np.column_stack(
        [
            np.asarray(moving_catalog.get("x", []), dtype=np.float64)[:moving_count],
            np.asarray(moving_catalog.get("y", []), dtype=np.float64)[:moving_count],
        ]
    )
    if reference.shape[0] <= 0 or moving.shape[0] <= 0:
        return {"applied": False, "status": "empty_catalog", "matrix": seed.tolist()}

    tolerance = max(0.0, float(tolerance_px))
    max_iterations = max(0, int(iterations))
    max_iteration_step = None
    if iteration_max_step_px is not None:
        max_iteration_step = max(0.0, float(iteration_max_step_px))

    def project_points(matrix: np.ndarray) -> np.ndarray:
        ones = np.ones((moving.shape[0], 1), dtype=np.float64)
        projected_h = np.hstack([moving, ones]) @ matrix.T
        scale = projected_h[:, 2:3]
        return np.divide(
            projected_h[:, :2],
            scale,
            out=projected_h[:, :2].copy(),
            where=np.abs(scale) > 1.0e-12,
        )

    def score_matrix(matrix: np.ndarray) -> tuple[list[tuple[int, int]], float]:
        projected = project_points(matrix)
        distances = np.sqrt(np.sum((projected[:, None, :] - reference[None, :, :]) ** 2, axis=2))
        candidate_indices = np.argwhere(distances <= tolerance)
        if candidate_indices.size == 0:
            return [], float("inf")
        candidates = sorted(
            (
                (float(distances[int(moving_i), int(reference_i)]), int(moving_i), int(reference_i))
                for moving_i, reference_i in candidate_indices
            ),
            key=lambda item: item[0],
        )
        used_moving: set[int] = set()
        used_reference: set[int] = set()
        pairs: list[tuple[int, int]] = []
        residuals: list[float] = []
        for distance, moving_i, reference_i in candidates:
            if moving_i in used_moving or reference_i in used_reference:
                continue
            used_moving.add(moving_i)
            used_reference.add(reference_i)
            pairs.append((moving_i, reference_i))
            residuals.append(distance)
        rms = float(np.sqrt(np.mean(np.square(residuals)))) if residuals else float("inf")
        return pairs, rms

    def fit_translation(pairs: list[tuple[int, int]]) -> np.ndarray:
        moving_pairs = moving[[moving_i for moving_i, _reference_i in pairs]]
        reference_pairs = reference[[reference_i for _moving_i, reference_i in pairs]]
        dx, dy = np.median(reference_pairs - moving_pairs, axis=0)
        return np.asarray([[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]], dtype=np.float64)

    def pair_rms(matrix: np.ndarray, pairs: list[tuple[int, int]]) -> float:
        if not pairs:
            return float("inf")
        moving_pairs = moving[[moving_i for moving_i, _reference_i in pairs]]
        reference_pairs = reference[[reference_i for _moving_i, reference_i in pairs]]
        projected = np.column_stack([moving_pairs, np.ones(len(moving_pairs), dtype=np.float64)]) @ matrix.T
        scale = projected[:, 2:3]
        projected_xy = np.divide(
            projected[:, :2],
            scale,
            out=projected[:, :2].copy(),
            where=np.abs(scale) > 1.0e-12,
        )
        residuals = projected_xy - reference_pairs
        return float(np.sqrt(np.mean(np.sum(residuals * residuals, axis=1))))

    seed_pairs, seed_rms = score_matrix(seed)
    best_pairs = seed_pairs
    initial_inliers = len(best_pairs)
    initial_rms_px = float(seed_rms) if np.isfinite(seed_rms) else float("nan")
    if not best_pairs:
        return {
            "applied": False,
            "status": "no_pairs",
            "matrix": seed.tolist(),
            "inliers": 0,
            "rms_px": float("nan"),
            "initial_inliers": 0,
            "initial_rms_px": float("nan"),
            "iterations": 0,
        }

    inliers = len(best_pairs)
    if inliers < int(min_inliers):
        return {
            "applied": False,
            "status": "insufficient_inliers",
            "matrix": seed.tolist(),
            "candidate_matrix": seed.tolist(),
            "inliers": inliers,
            "rms_px": float("nan"),
            "initial_inliers": initial_inliers,
            "initial_rms_px": initial_rms_px,
            "iterations": 0,
        }
    if max_iterations <= 0:
        return {
            "applied": False,
            "status": "iterations_disabled",
            "matrix": seed.tolist(),
            "inliers": inliers,
            "rms_px": float("nan"),
            "initial_inliers": initial_inliers,
            "initial_rms_px": initial_rms_px,
            "iterations": 0,
        }

    best_matrix = fit_translation(best_pairs)
    best_rms = pair_rms(best_matrix, best_pairs)
    accepted_iterations = 1 if max_iterations > 0 else 0

    for _iteration in range(1, max_iterations):
        if not best_pairs:
            break
        scored_pairs, _scored_rms = score_matrix(best_matrix)
        if not scored_pairs:
            break
        candidate = fit_translation(scored_pairs)
        iteration_step_px = float(
            np.hypot(candidate[0, 2] - best_matrix[0, 2], candidate[1, 2] - best_matrix[1, 2])
        )
        if max_iteration_step is not None and iteration_step_px > max_iteration_step:
            break
        candidate_pairs, candidate_rms = score_matrix(candidate)
        if len(candidate_pairs) > len(best_pairs) or (
            len(candidate_pairs) == len(best_pairs) and candidate_rms <= best_rms
        ):
            best_matrix = candidate
            best_pairs = candidate_pairs
            best_rms = candidate_rms
            accepted_iterations += 1
        else:
            break

    inliers = len(best_pairs)
    dx = float(best_matrix[0, 2])
    dy = float(best_matrix[1, 2])
    correction_dx = float(dx - seed[0, 2])
    correction_dy = float(dy - seed[1, 2])
    correction_px = float(np.hypot(correction_dx, correction_dy))
    if correction_px > float(max_correction_px):
        return {
            "applied": False,
            "status": "correction_exceeds_limit",
            "matrix": seed.tolist(),
            "candidate_matrix": best_matrix.tolist(),
            "inliers": inliers,
            "rms_px": float("nan"),
            "correction_dx": correction_dx,
            "correction_dy": correction_dy,
            "correction_px": correction_px,
            "initial_inliers": initial_inliers,
            "initial_rms_px": initial_rms_px,
            "iterations": accepted_iterations,
        }

    rms_px = float(best_rms) if np.isfinite(best_rms) else float("nan")
    return {
        "applied": True,
        "status": "applied",
        "matrix": best_matrix.tolist(),
        "inliers": inliers,
        "rms_px": rms_px,
        "correction_dx": correction_dx,
        "correction_dy": correction_dy,
        "correction_px": correction_px,
        "initial_inliers": initial_inliers,
        "initial_rms_px": initial_rms_px,
        "iterations": accepted_iterations,
    }


def _resident_refine_catalog_centroids_from_stack(
    stack: Any,
    frame_index: int,
    catalog: dict[str, Any] | None,
    *,
    radius: int = 4,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if catalog is None:
        return None, {"enabled": False, "status": "missing_catalog", "refined_count": 0}
    stored_count = int(catalog.get("stored_count", len(catalog.get("x", []))) or 0)
    if stored_count <= 0:
        return catalog, {"enabled": True, "status": "empty_catalog", "refined_count": 0}
    output = dict(catalog)
    xs = np.asarray(catalog.get("x", []), dtype=np.float32).copy()
    ys = np.asarray(catalog.get("y", []), dtype=np.float32).copy()
    if xs.size < stored_count or ys.size < stored_count:
        return catalog, {"enabled": True, "status": "invalid_catalog_shape", "refined_count": 0}

    refined_count = 0
    failed_count = 0
    max_shift = 0.0
    window_radius = max(1, int(radius))
    for i in range(stored_count):
        x_center = int(round(float(xs[i])))
        y_center = int(round(float(ys[i])))
        x0 = max(0, x_center - window_radius)
        y0 = max(0, y_center - window_radius)
        x1 = min(int(stack.width), x_center + window_radius + 1)
        y1 = min(int(stack.height), y_center + window_radius + 1)
        if x0 >= x1 or y0 >= y1:
            failed_count += 1
            continue
        tile = np.asarray(stack.download_frame_tile(int(frame_index), x0, y0, x1, y1), dtype=np.float32)
        finite = np.isfinite(tile)
        if not np.any(finite):
            failed_count += 1
            continue
        background = float(np.median(tile[finite]))
        weights = np.where(finite, np.maximum(tile - np.float32(background), 0.0), 0.0)
        flux = float(np.sum(weights, dtype=np.float64))
        if flux <= 0.0:
            failed_count += 1
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        refined_x = float(np.sum(xx * weights, dtype=np.float64) / flux)
        refined_y = float(np.sum(yy * weights, dtype=np.float64) / flux)
        max_shift = max(max_shift, float(np.hypot(refined_x - float(xs[i]), refined_y - float(ys[i]))))
        xs[i] = refined_x
        ys[i] = refined_y
        refined_count += 1

    output["x"] = xs[:stored_count]
    output["y"] = ys[:stored_count]
    output["centroid_refine"] = {
        "enabled": True,
        "status": "ok" if refined_count > 0 else "no_refined_centroids",
        "frame_index": int(frame_index),
        "radius": int(window_radius),
        "stored_count": int(stored_count),
        "refined_count": int(refined_count),
        "failed_count": int(failed_count),
        "max_shift_px": float(max_shift),
        "mode": "resident_tile_download_cpu_centroid",
        "background_mode": "local_median",
    }
    return output, dict(output["centroid_refine"])


def _float_or_nan(value: Any) -> float:
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


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


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _array_sha256(value: Any, dtype: Any) -> str:
    array = np.ascontiguousarray(np.asarray(value, dtype=dtype))
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
    digest.update(array.tobytes())
    return digest.hexdigest()


def _resident_catalog_signature(catalog: dict[str, Any] | None) -> dict[str, Any]:
    if not catalog:
        return {"available": False, "sha256": None}
    stored_count = int(catalog.get("stored_count", len(catalog.get("x", []))) or 0)
    payload = {
        "available": True,
        "schema_version": 1,
        "count": int(catalog.get("count", stored_count) or 0),
        "stored_count": stored_count,
        "grid_cols": int(catalog.get("grid_cols", 0) or 0),
        "grid_rows": int(catalog.get("grid_rows", 0) or 0),
        "candidates_per_cell": int(catalog.get("candidates_per_cell", 0) or 0),
        "max_output_candidates": int(catalog.get("max_output_candidates", 0) or 0),
        "min_separation_px": _float_or_nan(catalog.get("min_separation_px")),
        "catalog_sort_mode": str(catalog.get("catalog_sort_mode", "unavailable")),
        "catalog_topk_mode": str(catalog.get("catalog_topk_mode", "unavailable")),
        "x_sha256": _array_sha256(np.asarray(catalog.get("x", []), dtype=np.float32)[:stored_count], np.float32),
        "y_sha256": _array_sha256(np.asarray(catalog.get("y", []), dtype=np.float32)[:stored_count], np.float32),
        "flux_sha256": _array_sha256(
            np.asarray(catalog.get("flux", []), dtype=np.float32)[:stored_count],
            np.float32,
        ),
    }
    return {**payload, "sha256": _json_sha256(payload)}


def _resident_descriptor_signature(descriptor: dict[str, Any] | None) -> dict[str, Any]:
    if not descriptor:
        return {"available": False, "sha256": None}
    count = int(descriptor.get("count", 0) or 0)
    payload = {
        "available": True,
        "schema_version": 1,
        "count": count,
        "raw_count": int(descriptor.get("raw_count", 0) or 0),
        "max_stars": int(descriptor.get("max_stars", 0) or 0),
        "neighbors": int(descriptor.get("neighbors", 0) or 0),
        "model": str(descriptor.get("model", "unavailable")),
        "descriptors_sha256": _array_sha256(
            np.asarray(descriptor.get("descriptors", []), dtype=np.float32).reshape(-1, 2)[:count],
            np.float32,
        ),
        "indices_sha256": _array_sha256(
            np.asarray(descriptor.get("indices", []), dtype=np.int32).reshape(-1, 3)[:count],
            np.int32,
        ),
        "areas_sha256": _array_sha256(
            np.asarray(descriptor.get("areas", []), dtype=np.float32).reshape(-1)[:count],
            np.float32,
        ),
    }
    return {**payload, "sha256": _json_sha256(payload)}


def _resident_fit_signature(fit: dict[str, Any] | None) -> dict[str, Any]:
    if not fit:
        return {"available": False, "sha256": None}
    matrix = np.asarray(fit.get("matrix", np.eye(3, dtype=np.float32)), dtype=np.float32).reshape(3, 3)
    payload = {
        "available": True,
        "schema_version": 1,
        "status": str(fit.get("status", "unknown")),
        "model": str(fit.get("model", "unavailable")),
        "batch_model": str(fit.get("batch_model", "")),
        "inliers": int(fit.get("inliers", 0) or 0),
        "rms_px": _float_or_nan(fit.get("rms_px")),
        "scale": _float_or_nan(fit.get("scale")),
        "rotation_rad": _float_or_nan(fit.get("rotation_rad")),
        "best_candidate_index": int(fit.get("best_candidate_index", -1) or -1),
        "candidate_count": int(fit.get("candidate_count", 0) or 0),
        "reference_descriptor_count": int(fit.get("reference_descriptor_count", 0) or 0),
        "moving_descriptor_count": int(fit.get("moving_descriptor_count", 0) or 0),
        "matrix_sha256": _array_sha256(matrix, np.float32),
    }
    return {**payload, "sha256": _json_sha256(payload)}


def _resident_trial_signature(trials: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {"schema_version": 1, "trials": trials}
    return {
        "schema_version": 1,
        "trial_count": len(trials),
        "sha256": _json_sha256(payload),
    }


def _resident_triangle_determinism_summary(signatures: dict[str, Any]) -> dict[str, Any]:
    moving = signatures.get("moving") or {}
    threshold_entries = signatures.get("thresholds") or {}
    moving_catalog_hashes = {
        frame_id: (item.get("moving_catalog") or {}).get("sha256")
        for frame_id, item in moving.items()
    }
    selected_fit_hashes = {
        frame_id: (item.get("selected_fit") or {}).get("sha256")
        for frame_id, item in moving.items()
    }
    trial_hashes = {
        frame_id: (item.get("trial_signature") or {}).get("sha256")
        for frame_id, item in moving.items()
    }
    reference_hashes = {
        threshold: {
            "catalog": (item.get("reference_catalog") or {}).get("sha256"),
            "descriptor": (item.get("reference_descriptor") or {}).get("sha256"),
        }
        for threshold, item in threshold_entries.items()
    }
    return {
        "schema_version": 1,
        "signature_mode": signatures.get("signature_mode"),
        "hash_algorithm": "sha256",
        "moving_frame_count": len(moving),
        "threshold_count": len(threshold_entries),
        "moving_catalog_combined_sha256": _json_sha256(moving_catalog_hashes),
        "selected_fit_combined_sha256": _json_sha256(selected_fit_hashes),
        "trial_combined_sha256": _json_sha256(trial_hashes),
        "reference_combined_sha256": _json_sha256(reference_hashes),
    }


def _policy_int(raw: dict[str, Any], key: str, default: int) -> int:
    value = raw.get(key)
    if value is None:
        return int(default)
    return int(value)


def _policy_float(raw: dict[str, Any], key: str, default: float) -> float:
    value = raw.get(key)
    if value is None:
        return float(default)
    return float(value)


def _policy_optional_float(raw: dict[str, Any], key: str, default: float | None) -> float | None:
    value = raw.get(key)
    if value is None:
        return default
    return float(value)


def _policy_bool(raw: dict[str, Any], key: str, default: bool) -> bool:
    value = raw.get(key)
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{key} must be a boolean-like value")


def _apply_resident_registration_matrix(
    stack: Any,
    index: int,
    matrix: list[list[float]],
    interpolation: str = "bilinear",
    clamping_threshold: float = -1.0,
) -> str:
    if _matrix_is_translation(matrix):
        if interpolation == "lanczos3" and hasattr(stack, "apply_matrix_lanczos3_frame"):
            stack.apply_matrix_lanczos3_frame(index, matrix, np.nan, float(clamping_threshold))
            return "matrix_lanczos3"
        stack.apply_translation_bilinear_frame(index, float(matrix[0][2]), float(matrix[1][2]), np.nan)
        return "translation_bilinear"
    if interpolation == "lanczos3":
        if not hasattr(stack, "apply_matrix_lanczos3_frame"):
            raise RuntimeError("resident CUDA backend does not expose matrix Lanczos3 warp")
        stack.apply_matrix_lanczos3_frame(index, matrix, np.nan, float(clamping_threshold))
        return "matrix_lanczos3"
    if not hasattr(stack, "apply_matrix_bilinear_frame"):
        raise RuntimeError("resident CUDA backend does not expose matrix bilinear warp")
    stack.apply_matrix_bilinear_frame(index, matrix, np.nan)
    return "matrix_bilinear"


def _combine_resident_matrix_batch_timings(
    timings: list[dict[str, Any]],
    *,
    total_items: int,
    chunk_capacity_frames: int | None,
) -> dict[str, Any]:
    if not timings:
        return {"batched": False, "frame_count": 0, "fallback_frame_count": total_items}
    sum_keys = {
        "frame_count",
        "fallback_frame_count",
        "inverse_prepare_s",
        "inverse_batch_alloc_s",
        "inverse_batch_bytes",
        "index_upload_s",
        "index_upload_count",
        "inverse_upload_s",
        "inverse_upload_count",
        "kernel_enqueue_s",
        "coverage_reduce_enqueue_s",
        "scatter_enqueue_s",
        "postprocess_enqueue_s",
        "device_copy_enqueue_s",
        "sync_s",
        "total_s",
        "batch_chunk_count",
        "warp_kernel_launches",
        "coverage_reduce_kernel_launches",
        "scatter_kernel_launches",
        "postprocess_kernel_launches",
    }
    max_keys = {
        "batch_chunk_frames",
        "batch_workspace_bytes",
        "batch_output_bytes",
        "batch_coverage_bytes",
    }
    combined: dict[str, Any] = {
        "batched": any(bool(timing.get("batched", False)) for timing in timings),
        "frame_count": 0,
        "fallback_frame_count": 0,
        "admission_chunk_capacity_frames": (
            int(chunk_capacity_frames) if chunk_capacity_frames is not None else None
        ),
        "admission_chunk_call_count": len(timings),
    }
    for timing in timings:
        for key in sum_keys:
            if key not in timing:
                continue
            value = timing.get(key)
            if isinstance(value, float):
                combined[key] = float(combined.get(key, 0.0)) + float(value)
            else:
                combined[key] = int(combined.get(key, 0) or 0) + int(value or 0)
        for key in max_keys:
            if key in timing:
                combined[key] = max(int(combined.get(key, 0) or 0), int(timing.get(key, 0) or 0))
    combined["frame_count"] = int(combined.get("frame_count", 0) or 0)
    combined["fallback_frame_count"] = total_items - int(combined["frame_count"])
    inverse_modes = {str(timing.get("inverse_upload_mode", "unavailable")) for timing in timings}
    combined["inverse_upload_mode"] = (
        next(iter(inverse_modes)) if len(inverse_modes) == 1 else "mixed"
    )
    metadata_modes = {
        str(timing.get("chunk_metadata_upload_mode", "unavailable")) for timing in timings
    }
    combined["chunk_metadata_upload_mode"] = (
        next(iter(metadata_modes)) if len(metadata_modes) == 1 else "mixed"
    )
    postprocess_modes = {
        str(timing.get("postprocess_mode", "unavailable")) for timing in timings
    }
    combined["postprocess_mode"] = (
        next(iter(postprocess_modes)) if len(postprocess_modes) == 1 else "mixed"
    )
    timing_models = [str(timing.get("timing_model", "unavailable")) for timing in timings]
    first_model = timing_models[0] if timing_models else "unavailable"
    combined["timing_model"] = (
        first_model
        if len(timings) == 1
        else f"{first_model}_admission_capacity_multi_call"
    )
    return combined


def _apply_resident_registration_matrix_batch(
    stack: Any,
    items: list[tuple[int, list[list[float]]]],
    interpolation: str = "bilinear",
    clamping_threshold: float = -1.0,
    batch_dispatch: str = "loop",
    chunk_capacity_frames: int | None = None,
    track_coverage: bool = True,
) -> tuple[list[str], dict[str, Any]]:
    if not items:
        return [], {"batched": False, "frame_count": 0}
    models: list[str | None] = [None] * len(items)
    matrix_positions: list[int] = []
    matrix_indices: list[int] = []
    matrix_values: list[list[list[float]]] = []
    matrix_batch_available = bool(
        (
            interpolation == "lanczos3"
            and hasattr(stack, "apply_matrix_lanczos3_frames")
        )
        or (
            interpolation == "bilinear"
            and hasattr(stack, "apply_matrix_bilinear_frames")
        )
    )
    for position, (index, matrix) in enumerate(items):
        if _matrix_is_translation(matrix) and not matrix_batch_available:
            if interpolation == "lanczos3" and hasattr(stack, "apply_matrix_lanczos3_frame"):
                stack.apply_matrix_lanczos3_frame(index, matrix, np.nan, float(clamping_threshold))
                models[position] = "matrix_lanczos3"
            else:
                stack.apply_translation_bilinear_frame(index, float(matrix[0][2]), float(matrix[1][2]), np.nan)
                models[position] = "translation_bilinear"
            continue
        matrix_positions.append(position)
        matrix_indices.append(index)
        matrix_values.append(matrix)

    timing: dict[str, Any] = {
        "batched": False,
        "frame_count": 0,
        "fallback_frame_count": len(items) - len(matrix_positions),
    }
    if matrix_positions:
        batch_kwargs: dict[str, Any] = {
            "dispatch": batch_dispatch,
            "track_coverage": bool(track_coverage),
        }
        if batch_dispatch in {"chunked", "pipelined"} and chunk_capacity_frames is not None:
            batch_kwargs["max_chunk_capacity_frames"] = int(chunk_capacity_frames)
        if interpolation == "lanczos3" and matrix_batch_available:
            timing = dict(
                stack.apply_matrix_lanczos3_frames(
                    matrix_indices,
                    np.asarray(matrix_values, dtype=np.float32),
                    np.nan,
                    float(clamping_threshold),
                    **batch_kwargs,
                )
            )
            for position in matrix_positions:
                models[position] = "matrix_lanczos3_batch"
        elif interpolation == "bilinear" and matrix_batch_available:
            timing = dict(
                stack.apply_matrix_bilinear_frames(
                    matrix_indices,
                    np.asarray(matrix_values, dtype=np.float32),
                    np.nan,
                    **batch_kwargs,
                )
            )
            for position in matrix_positions:
                models[position] = "matrix_bilinear_batch"
        else:
            for position in matrix_positions:
                index, matrix = items[position]
                models[position] = _apply_resident_registration_matrix(
                    stack,
                    index,
                    matrix,
                    interpolation,
                    clamping_threshold,
                )
            timing = {"batched": False, "frame_count": 0, "fallback_frame_count": len(items)}
        timing["batched"] = bool(timing.get("frame_count", 0))
        timing["fallback_frame_count"] = len(items) - int(timing.get("frame_count", 0) or 0)
    return [str(model or "unavailable") for model in models], timing


def _diagnostic_percentiles(
    finite_values: np.ndarray,
    quantiles: tuple[float, ...],
    *,
    exact_max_pixels: int = _OUTPUT_DIAGNOSTICS_EXACT_PERCENTILE_MAX_PIXELS,
    sample_pixels: int = _OUTPUT_DIAGNOSTICS_PERCENTILE_SAMPLE_PIXELS,
) -> tuple[np.ndarray, dict[str, Any]]:
    values = np.asarray(finite_values, dtype=np.float32).reshape(-1)
    value_count = int(values.size)
    if value_count <= int(exact_max_pixels):
        return np.percentile(values, quantiles), {
            "percentile_method": "exact",
            "percentile_approximation": False,
            "percentile_sample_pixels": value_count,
            "percentile_total_pixels": value_count,
            "percentile_stride": 1,
        }
    target = max(1, min(int(sample_pixels), value_count))
    stride = max(1, int(np.ceil(value_count / target)))
    sample = values[::stride]
    return np.percentile(sample, quantiles), {
        "percentile_method": "deterministic_stride_sample",
        "percentile_approximation": True,
        "percentile_sample_pixels": int(sample.size),
        "percentile_total_pixels": value_count,
        "percentile_stride": stride,
    }


def _output_diagnostics(data: np.ndarray, weight_map: np.ndarray | None = None) -> dict[str, Any]:
    values = np.asarray(data, dtype=np.float32)
    total_pixels = int(values.size)
    finite_mask = np.isfinite(values)
    finite_count = int(np.count_nonzero(finite_mask))
    nonfinite_count = total_pixels - finite_count
    if finite_count == 0:
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
    finite = values.reshape(-1) if finite_count == total_pixels else values[finite_mask]

    percentile_names = ("p001", "p01", "p1", "p50", "p99", "p999", "p9999")
    percentile_values, percentile_metadata = _diagnostic_percentiles(
        finite,
        (0.01, 0.1, 1.0, 50.0, 99.0, 99.9, 99.99),
    )
    percentiles = {
        name: float(value)
        for name, value in zip(percentile_names, percentile_values, strict=True)
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
    lt_0 = finite < 0.0
    gt_1 = finite > 1.0
    gt_65535 = finite > 65535.0
    lt_0_count = int(np.count_nonzero(lt_0))
    gt_1_count = int(np.count_nonzero(gt_1))
    gt_65535_count = int(np.count_nonzero(gt_65535))
    finite_size = int(finite.size)
    would_clip_low = finite < robust_low
    would_clip_high = finite > robust_high
    would_clip_low_count = int(np.count_nonzero(would_clip_low))
    would_clip_high_count = int(np.count_nonzero(would_clip_high))
    clipping = {
        "lt_0_count": lt_0_count,
        "lt_0_fraction": float(lt_0_count / finite_size),
        "gt_1_count": gt_1_count,
        "gt_1_fraction": float(gt_1_count / finite_size),
        "gt_65535_count": gt_65535_count,
        "gt_65535_fraction": float(gt_65535_count / finite_size),
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
            **percentile_metadata,
        },
        "normalization_probe": {
            "method": "diagnostic_only_p0_1_to_p99_9",
            "black": robust_low,
            "white": robust_high,
            "percentile_method": percentile_metadata["percentile_method"],
            "percentile_approximation": percentile_metadata["percentile_approximation"],
            "percentile_sample_pixels": percentile_metadata["percentile_sample_pixels"],
            "percentile_total_pixels": percentile_metadata["percentile_total_pixels"],
            "percentile_stride": percentile_metadata["percentile_stride"],
            "scale": float(1.0 / robust_span) if robust_span > 0 else 1.0,
            "offset": float(-robust_low),
            "would_clip_low_count": would_clip_low_count,
            "would_clip_high_count": would_clip_high_count,
            "would_clip_low_fraction": float(would_clip_low_count / finite_size),
            "would_clip_high_fraction": float(would_clip_high_count / finite_size),
        },
        "clipping_probe": clipping,
    }


def _count_map_dtype(frame_count: int) -> Any:
    return np.int16 if int(frame_count) <= np.iinfo(np.int16).max else np.int32


def _resident_coverage_array_stats_from_values(
    values: np.ndarray,
    finite_mask: np.ndarray | None = None,
) -> dict[str, float | int]:
    values = np.asarray(values, dtype=np.float32)
    total_pixels = int(values.size)
    finite = np.isfinite(values) if finite_mask is None else finite_mask
    finite_count = int(np.count_nonzero(finite))
    if finite_count == 0:
        return {
            "total_pixels": total_pixels,
            "finite_pixels": 0,
            "rounded_sum": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
        }
    finite_values = values.ravel() if finite_count == values.size else values[finite]
    rounded = np.rint(finite_values)
    return {
        "total_pixels": total_pixels,
        "finite_pixels": finite_count,
        "rounded_sum": int(round(float(np.sum(rounded, dtype=np.float64)))),
        "min": float(np.min(finite_values)),
        "max": float(np.max(finite_values)),
        "mean": float(np.mean(finite_values)),
    }


def _resident_finite_count_coverage_stats(values: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(values, dtype=np.float32)
    total_pixels = int(values.size)
    if total_pixels == 0:
        return {
            "total_pixels": 0,
            "finite_pixels": 0,
            "rounded_sum": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
        }
    return {
        "total_pixels": total_pixels,
        "finite_pixels": total_pixels,
        "rounded_sum": int(round(float(np.sum(values, dtype=np.float64)))),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
    }


def _resident_count_map_array_stats_from_values(
    values: np.ndarray,
    finite_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float32)
    finite = np.isfinite(values) if finite_mask is None else finite_mask
    finite_count = int(np.count_nonzero(finite))
    finite_values = values.ravel() if finite_count == values.size else values[finite]
    rounded = np.rint(finite_values)
    positive_count = int(np.count_nonzero(finite_values > 0.0))
    negative_count = int(np.count_nonzero(finite_values < 0.0))
    return {
        "present": True,
        "shape": list(values.shape),
        "dtype": str(values.dtype),
        "finite_pixels": finite_count,
        "nonfinite_pixels": int(values.size - finite_count),
        "min": None if finite_count == 0 else float(np.min(finite_values)),
        "max": None if finite_count == 0 else float(np.max(finite_values)),
        "rounded_sum": int(round(float(np.sum(np.maximum(rounded, 0.0), dtype=np.float64)))),
        "positive_pixels": positive_count,
        "zero_or_less_pixels": int(values.size - positive_count),
        "negative_pixels": negative_count,
        "fractional_pixels": int(np.count_nonzero(np.abs(finite_values - rounded) > 1.0e-3)),
        "stats_source": "resident_precomputed_count_map",
        "stats_profile": "count_map_contract_fields",
    }


def _resident_finite_count_map_array_stats_from_values(
    values: np.ndarray,
    *,
    positive_count: int | None = None,
    negative_count: int | None = None,
    assume_nonnegative: bool = False,
) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float32)
    total_pixels = int(values.size)
    if total_pixels == 0:
        minimum = None
        maximum = None
        rounded_sum = 0
        positive_pixels = 0
        negative_pixels = 0
    else:
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        rounded_sum = int(
            round(
                float(
                    np.sum(
                        values if assume_nonnegative else np.maximum(values, 0.0),
                        dtype=np.float64,
                    )
                )
            )
        )
        positive_pixels = (
            int(positive_count)
            if positive_count is not None
            else int(np.count_nonzero(values > 0.0))
        )
        negative_pixels = (
            0
            if assume_nonnegative
            else
            int(negative_count)
            if negative_count is not None
            else int(np.count_nonzero(values < 0.0))
        )
    return {
        "present": True,
        "shape": list(values.shape),
        "dtype": str(values.dtype),
        "finite_pixels": total_pixels,
        "nonfinite_pixels": 0,
        "min": minimum,
        "max": maximum,
        "rounded_sum": rounded_sum,
        "positive_pixels": positive_pixels,
        "zero_or_less_pixels": int(total_pixels - positive_pixels),
        "negative_pixels": negative_pixels,
        "fractional_pixels": 0,
        "stats_source": "resident_precomputed_count_map",
        "stats_profile": "resident_finite_integer_count_map_fast_path",
    }


def _resident_dq_flag_dtype(dtype: Any) -> np.dtype:
    target = np.dtype(dtype)
    if not np.issubdtype(target, np.integer):
        raise ValueError("resident DQ map dtype must be an integer type")
    max_flag = max(int(flag) for flag in DQFlag)
    if max_flag > np.iinfo(target).max:
        raise ValueError(f"resident DQ map dtype {target.name} cannot store DQFlag bits up to {max_flag}")
    return target


def _resident_dq_map_python(
    master: np.ndarray,
    weight_map: np.ndarray,
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    geometric_warp_coverage_map: np.ndarray | None = None,
    active_frame_count: int = 0,
    *,
    return_stats: bool = False,
    assume_finite_count_maps: bool = False,
    assume_nonnegative_count_maps: bool = False,
    assume_valid_master_weight: bool = False,
    dq_dtype: Any = np.uint32,
) -> tuple[np.ndarray, dict[str, int]] | tuple[np.ndarray, dict[str, int], dict[str, Any]]:
    dq_dtype = _resident_dq_flag_dtype(dq_dtype)
    no_data_bit = dq_dtype.type(int(DQFlag.NO_DATA))
    warp_edge_bit = dq_dtype.type(int(DQFlag.WARP_EDGE))
    low_rejected_bit = dq_dtype.type(int(DQFlag.LOW_REJECTED))
    high_rejected_bit = dq_dtype.type(int(DQFlag.HIGH_REJECTED))
    dq = np.zeros(np.asarray(master).shape, dtype=dq_dtype)
    master_values = np.asarray(master, dtype=np.float32)
    weights = np.asarray(weight_map, dtype=np.float32)
    invalid = (
        None
        if assume_valid_master_weight
        else (~np.isfinite(master_values)) | (~np.isfinite(weights)) | (weights <= 0.0)
    )
    stats: dict[str, Any] = {
        "schema_version": 1,
        "stats_source": "resident_dq_map_single_pass",
        "stats_profile": (
            "resident_valid_master_nonnegative_count_map_fast_path"
            if assume_valid_master_weight and assume_nonnegative_count_maps
            else "resident_general_dq_map_path"
        ),
        "post_rejection_coverage": None,
        "post_rejection_zero_pixels": None,
        "geometric_warp_coverage": None,
        "geometric_zero_pixels": None,
        "geometric_partial_pixels": None,
        "geometric_full_pixels": None,
        "low_rejection": {"present": False},
        "high_rejection": {"present": False},
        "rejection_reduced_pixels": None,
        "rejection_reduced_pixels_source": "unavailable",
    }
    if coverage_map is not None:
        coverage = np.asarray(coverage_map, dtype=np.float32)
        coverage_finite = None if assume_finite_count_maps else np.isfinite(coverage)
        coverage_stats = (
            _resident_finite_count_coverage_stats(coverage)
            if assume_finite_count_maps
            else _resident_coverage_array_stats_from_values(
                coverage,
                coverage_finite,
            )
        )
        stats["post_rejection_coverage"] = coverage_stats
        coverage_min = coverage_stats.get("min")
        if assume_finite_count_maps and coverage_min is not None and float(coverage_min) > 0.5:
            stats["post_rejection_zero_pixels"] = 0
        else:
            coverage_invalid = (
                coverage <= 0.5
                if assume_finite_count_maps
                else (~coverage_finite) | (coverage <= 0.5)
            )
            invalid = coverage_invalid.copy() if invalid is None else (invalid | coverage_invalid)
            dq[coverage_invalid] |= warp_edge_bit
            stats["post_rejection_zero_pixels"] = (
                int(np.count_nonzero(coverage_invalid))
                if assume_finite_count_maps
                else int(np.count_nonzero(coverage_finite & (coverage <= 0.5)))
            )
    if geometric_warp_coverage_map is not None:
        geometric = np.asarray(geometric_warp_coverage_map, dtype=np.float32)
        geometric_finite = None if assume_finite_count_maps else np.isfinite(geometric)
        geometric_stats = (
            _resident_finite_count_coverage_stats(geometric)
            if assume_finite_count_maps
            else _resident_coverage_array_stats_from_values(
                geometric,
                geometric_finite,
            )
        )
        stats["geometric_warp_coverage"] = geometric_stats
        geometric_min = geometric_stats.get("min")
        geometric_has_no_zero = assume_finite_count_maps and geometric_min is not None and float(geometric_min) > 0.5
        if geometric_has_no_zero:
            stats["geometric_zero_pixels"] = 0
        else:
            geometric_invalid = (
                geometric <= 0.5
                if assume_finite_count_maps
                else (~geometric_finite) | (geometric <= 0.5)
            )
            invalid = geometric_invalid.copy() if invalid is None else (invalid | geometric_invalid)
            dq[geometric_invalid] |= warp_edge_bit
            stats["geometric_zero_pixels"] = (
                int(np.count_nonzero(geometric_invalid))
                if assume_finite_count_maps
                else int(np.count_nonzero(geometric_finite & (geometric <= 0.5)))
            )
        expected_count = int(active_frame_count)
        if expected_count > 0:
            full_threshold = float(expected_count) - 0.5
            geometric_partial = geometric < full_threshold if geometric_has_no_zero else (
                (geometric > 0.5) & (geometric < full_threshold)
            )
            if not assume_finite_count_maps and not geometric_has_no_zero:
                geometric_partial &= geometric_finite
            dq[geometric_partial] |= warp_edge_bit
            partial_count = int(np.count_nonzero(geometric_partial))
            stats["geometric_partial_pixels"] = partial_count
            if geometric_has_no_zero:
                stats["geometric_full_pixels"] = int(geometric.size - partial_count)
            else:
                stats["geometric_full_pixels"] = int(
                    np.count_nonzero(geometric >= full_threshold)
                    if assume_finite_count_maps
                    else np.count_nonzero(geometric_finite & (geometric >= full_threshold))
                )
        else:
            stats["geometric_partial_pixels"] = 0
            stats["geometric_full_pixels"] = 0
    if invalid is not None:
        dq[invalid] |= no_data_bit
    low_rejected_count = 0
    low_rejected = None
    if low_rejection_map is not None:
        low = np.asarray(low_rejection_map, dtype=np.float32)
        low_finite = None if assume_finite_count_maps else np.isfinite(low)
        low_rejected = low > 0.0 if assume_finite_count_maps else low_finite & (low > 0.0)
        low_rejected_count = int(np.count_nonzero(low_rejected))
        dq[low_rejected] |= low_rejected_bit
        stats["low_rejection"] = (
            _resident_finite_count_map_array_stats_from_values(
                low,
                positive_count=low_rejected_count,
                negative_count=0 if assume_nonnegative_count_maps else None,
                assume_nonnegative=assume_nonnegative_count_maps,
            )
            if assume_finite_count_maps
            else _resident_count_map_array_stats_from_values(low, low_finite)
        )
    high_rejected_count = 0
    high_rejected = None
    if high_rejection_map is not None:
        high = np.asarray(high_rejection_map, dtype=np.float32)
        high_finite = None if assume_finite_count_maps else np.isfinite(high)
        high_rejected = high > 0.0 if assume_finite_count_maps else high_finite & (high > 0.0)
        high_rejected_count = int(np.count_nonzero(high_rejected))
        dq[high_rejected] |= high_rejected_bit
        stats["high_rejection"] = (
            _resident_finite_count_map_array_stats_from_values(
                high,
                positive_count=high_rejected_count,
                negative_count=0 if assume_nonnegative_count_maps else None,
                assume_nonnegative=assume_nonnegative_count_maps,
            )
            if assume_finite_count_maps
            else _resident_count_map_array_stats_from_values(high, high_finite)
        )
    if low_rejected is not None and high_rejected is not None:
        stats["rejection_reduced_pixels"] = int(np.count_nonzero(low_rejected | high_rejected))
        stats["rejection_reduced_pixels_source"] = "low_high_rejection_masks"
    elif low_rejected is not None:
        stats["rejection_reduced_pixels"] = low_rejected_count
        stats["rejection_reduced_pixels_source"] = "low_rejection_mask"
    elif high_rejected is not None:
        stats["rejection_reduced_pixels"] = high_rejected_count
        stats["rejection_reduced_pixels_source"] = "high_rejection_mask"
    summary = {"valid": int(np.count_nonzero(dq == 0))}
    no_data_count = 0 if invalid is None else int(np.count_nonzero(invalid))
    if no_data_count:
        summary["no_data"] = no_data_count
    warp_edge_count = int(np.count_nonzero((dq & warp_edge_bit) != 0))
    if warp_edge_count:
        summary["warp_edge"] = warp_edge_count
    if low_rejected_count:
        summary["low_rejected"] = low_rejected_count
    if high_rejected_count:
        summary["high_rejected"] = high_rejected_count
    if return_stats:
        return dq, summary, stats
    return dq, summary


def _resident_dq_map(
    master: np.ndarray,
    weight_map: np.ndarray,
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    geometric_warp_coverage_map: np.ndarray | None = None,
    active_frame_count: int = 0,
    *,
    return_stats: bool = False,
    assume_finite_count_maps: bool = False,
    assume_nonnegative_count_maps: bool = False,
    assume_valid_master_weight: bool = False,
    dq_dtype: Any = np.uint32,
) -> tuple[np.ndarray, dict[str, int]] | tuple[np.ndarray, dict[str, int], dict[str, Any]]:
    if return_stats:
        import glass_cuda

        if (
            assume_finite_count_maps
            and assume_nonnegative_count_maps
            and assume_valid_master_weight
            and np.dtype(dq_dtype) == np.dtype(np.int16)
            and glass_cuda.resident_dq_map_count_maps_i16_preferred()
        ):
            return glass_cuda.resident_dq_map_count_maps_i16(
                master,
                coverage_map,
                low_rejection_map,
                high_rejection_map,
                geometric_warp_coverage_map,
                active_frame_count,
            )
        if glass_cuda.resident_dq_map_host_f32_preferred():
            return glass_cuda.resident_dq_map_host_f32(
                master,
                weight_map,
                coverage_map,
                low_rejection_map,
                high_rejection_map,
                geometric_warp_coverage_map,
                active_frame_count,
            )
    return _resident_dq_map_python(
        master,
        weight_map,
        coverage_map,
        low_rejection_map,
        high_rejection_map,
        geometric_warp_coverage_map,
        active_frame_count,
        return_stats=return_stats,
        assume_finite_count_maps=assume_finite_count_maps,
        assume_nonnegative_count_maps=assume_nonnegative_count_maps,
        assume_valid_master_weight=assume_valid_master_weight,
        dq_dtype=dq_dtype,
    )


def _resident_coverage_array_stats(data: np.ndarray) -> dict[str, float | int]:
    return _resident_coverage_array_stats_from_values(data)


def _resident_count_map_array_stats(data: np.ndarray | None) -> dict[str, Any]:
    if data is None:
        return {"present": False}
    return _resident_count_map_array_stats_from_values(data)


def _resident_surface_contract_map_stats(
    *,
    master: np.ndarray,
    weight_map: np.ndarray | None,
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    dq_map: np.ndarray | None,
    output_diagnostics: dict[str, Any],
    dq_coverage_provenance: dict[str, Any],
    dq_summary: dict[str, Any] | None,
    rejection_map_stats: dict[str, Any],
) -> dict[str, Any]:
    master_shape = list(np.asarray(master).shape)
    total_pixels = int(np.asarray(master).size)
    output_stats = (
        output_diagnostics.get("statistics")
        if isinstance(output_diagnostics.get("statistics"), dict)
        else {}
    )
    clipping = (
        output_diagnostics.get("clipping_probe")
        if isinstance(output_diagnostics.get("clipping_probe"), dict)
        else {}
    )
    stats: dict[str, Any] = {
        "master": {
            "present": True,
            "shape": master_shape,
            "dtype": str(np.asarray(master).dtype),
            "finite_pixels": int(output_diagnostics.get("finite_pixels") or 0),
            "nonfinite_pixels": int(output_diagnostics.get("nonfinite_pixels") or 0),
            "min": output_stats.get("min"),
            "max": output_stats.get("max"),
            "mean": output_stats.get("mean"),
            "stats_source": "resident_output_diagnostics",
        },
    }
    if weight_map is not None:
        positive_weight = clipping.get("positive_weight_pixels")
        zero_weight = clipping.get("zero_weight_pixels")
        stats["weight"] = {
            "present": True,
            "shape": list(np.asarray(weight_map).shape),
            "dtype": str(np.asarray(weight_map).dtype),
            "finite_pixels": int(np.asarray(weight_map).size),
            "nonfinite_pixels": 0,
            "positive_pixels": None if positive_weight is None else int(positive_weight),
            "zero_or_less_pixels": None if zero_weight is None else int(zero_weight),
            "stats_source": "resident_output_diagnostics",
        }
    coverage_stats = dq_coverage_provenance.get("post_rejection_coverage")
    if coverage_map is not None and isinstance(coverage_stats, dict):
        finite_pixels = int(coverage_stats.get("finite_pixels") or 0)
        zero_pixels = int(dq_coverage_provenance.get("post_rejection_zero_pixels") or 0)
        stats["coverage"] = {
            **coverage_stats,
            "present": True,
            "shape": list(np.asarray(coverage_map).shape),
            "dtype": str(np.asarray(coverage_map).dtype),
            "nonfinite_pixels": int(total_pixels - finite_pixels),
            "positive_pixels": int(finite_pixels - zero_pixels),
            "zero_or_less_pixels": zero_pixels,
            "negative_pixels": 0,
            "fractional_pixels": 0,
            "stats_source": "resident_dq_coverage_provenance",
        }
    for key, value in (
        ("low_rejection", low_rejection_map),
        ("high_rejection", high_rejection_map),
    ):
        map_stats = rejection_map_stats.get(key)
        if value is not None and isinstance(map_stats, dict):
            stats[key] = dict(map_stats)
    if dq_map is not None:
        dq_payload = dq_summary if isinstance(dq_summary, dict) else {}
        valid_pixels = int(dq_payload.get("valid") or 0)
        stats["dq"] = {
            "present": True,
            "shape": list(np.asarray(dq_map).shape),
            "dtype": str(np.asarray(dq_map).dtype),
            "finite_pixels": int(np.asarray(dq_map).size),
            "nonfinite_pixels": 0,
            "positive_pixels": int(total_pixels - valid_pixels),
            "zero_or_less_pixels": valid_pixels,
            "negative_pixels": 0,
            "fractional_pixels": 0,
            "stats_source": "resident_dq_summary",
        }
    return stats


def _resident_rejection_map_sample_count(
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    *,
    rejection_map_stats: dict[str, Any] | None = None,
) -> int | None:
    if low_rejection_map is None and high_rejection_map is None:
        return None
    if isinstance(rejection_map_stats, dict):
        total_from_stats = 0
        found = False
        for key in ("low_rejection", "high_rejection"):
            stats = rejection_map_stats.get(key)
            if isinstance(stats, dict) and stats.get("present") is not False:
                value = stats.get("rounded_sum")
                if value is not None:
                    total_from_stats += int(round(float(value)))
                    found = True
        if found:
            return total_from_stats
    total = 0
    for rejection_map in (low_rejection_map, high_rejection_map):
        if rejection_map is None:
            continue
        values = np.nan_to_num(np.asarray(rejection_map, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
        rounded = np.rint(values)
        np.maximum(rounded, 0.0, out=rounded)
        total += int(round(float(np.sum(rounded, dtype=np.float64))))
    return total


def _resident_source_dq_provenance_fields(source_dq_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(source_dq_summary, dict) or not source_dq_summary:
        return {}
    fields: dict[str, Any] = {
        "source_dq_application": {
            "source_model": source_dq_summary.get("source_model"),
            "native_method": source_dq_summary.get("native_method"),
            "frame_count": source_dq_summary.get("frame_count"),
            "frame_with_invalid_count": source_dq_summary.get("frame_with_invalid_count"),
            "applied_frame_count": source_dq_summary.get("applied_frame_count"),
            "applied_invalid_samples": source_dq_summary.get("applied_invalid_samples"),
            "unsupported_frame_count": source_dq_summary.get("unsupported_frame_count"),
            "passed": source_dq_summary.get("passed"),
        },
    }
    for key in (
        "input_samples",
        "input_valid_samples_before_rejection",
        "input_invalid_samples_before_rejection",
        "input_flagged_samples",
        "input_nonfinite_samples",
        "source_dq_flag_counts",
    ):
        if key in source_dq_summary:
            fields[key] = source_dq_summary[key]
    return fields


def _resident_source_dq_changes_samples(source_dq_summary: dict[str, Any] | None) -> bool:
    if not isinstance(source_dq_summary, dict):
        return False
    for key in (
        "applied_invalid_samples",
        "input_invalid_samples_before_rejection",
        "input_flagged_samples",
        "input_nonfinite_samples",
        "frame_with_invalid_count",
    ):
        try:
            if int(source_dq_summary.get(key) or 0) > 0:
                return True
        except (TypeError, ValueError):
            return True
    return False


def _source_dq_row_application_order(row: dict[str, Any]) -> str:
    order = row.get("application_order")
    if order is not None and str(order):
        return str(order)
    source = str(row.get("source") or "")
    if source.startswith("resident_post_registration_pre_warp"):
        return "post_registration_pre_warp"
    if source.startswith("resident_calibrated"):
        return "calibration_pre_registration"
    return "unspecified"


def _source_dq_row_registration_catalog_visible(row: dict[str, Any]) -> bool:
    if row.get("registration_catalog_visible") is not None:
        return bool(row.get("registration_catalog_visible"))
    return _source_dq_row_application_order(row) == "calibration_pre_registration"


def _source_dq_row_registration_catalog_visibility_required(row: dict[str, Any]) -> bool:
    if row.get("registration_catalog_visibility_required") is not None:
        return bool(row.get("registration_catalog_visibility_required"))
    return not bool(row.get("inline_source_dq"))


def _empty_registration_source_dq_input(frame_id: str) -> dict[str, Any]:
    return {
        "frame_id": str(frame_id),
        "row_count": 0,
        "invalid_samples": 0,
        "applied_invalid_samples": 0,
        "pre_registration_catalog_visible_invalid_samples": 0,
        "post_registration_deferred_invalid_samples": 0,
        "required_invalid_samples_not_visible_to_registration_catalog": 0,
        "application_order_counts": {},
        "registration_catalog_visibility_counts": {},
        "status_counts": {},
        "source_counts": {},
        "sidecar_path_count": 0,
        "sidecar_paths": [],
        "catalog_input_semantics": "no_source_dq_rows_for_frame",
    }


def _merge_counter(target: dict[str, int], key: Any, increment: int = 1) -> None:
    key_text = str(key or "unknown")
    target[key_text] = int(target.get(key_text, 0)) + int(increment)


def _resident_registration_source_dq_input_audit(
    registration_rows: list[dict[str, Any]],
    resident_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attach source-DQ catalog-input provenance to registration result rows."""

    source_rows: list[dict[str, Any]] = []
    for artifact in resident_artifacts:
        summary = artifact.get("source_dq_summary") if isinstance(artifact, dict) else None
        rows = summary.get("rows") if isinstance(summary, dict) else None
        if isinstance(rows, list):
            source_rows.extend(row for row in rows if isinstance(row, dict))

    by_frame: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        frame_id = str(row.get("frame_id") or "")
        if not frame_id:
            continue
        frame_summary = by_frame.setdefault(frame_id, _empty_registration_source_dq_input(frame_id))
        frame_summary["row_count"] = int(frame_summary["row_count"]) + 1
        invalid = int(row.get("invalid_samples") or 0)
        applied_invalid = invalid if bool(row.get("applied")) else 0
        frame_summary["invalid_samples"] = int(frame_summary["invalid_samples"]) + invalid
        frame_summary["applied_invalid_samples"] = (
            int(frame_summary["applied_invalid_samples"]) + applied_invalid
        )
        application_order = _source_dq_row_application_order(row)
        registration_visible = _source_dq_row_registration_catalog_visible(row)
        visibility_key = (
            "pre_registration_catalog_visible" if registration_visible else "not_catalog_visible"
        )
        _merge_counter(frame_summary["application_order_counts"], application_order)
        _merge_counter(frame_summary["registration_catalog_visibility_counts"], visibility_key)
        _merge_counter(frame_summary["status_counts"], row.get("status"))
        _merge_counter(frame_summary["source_counts"], row.get("source"))
        if registration_visible:
            frame_summary["pre_registration_catalog_visible_invalid_samples"] = (
                int(frame_summary["pre_registration_catalog_visible_invalid_samples"]) + invalid
            )
        else:
            frame_summary["post_registration_deferred_invalid_samples"] = (
                int(frame_summary["post_registration_deferred_invalid_samples"]) + invalid
            )
        if (
            invalid > 0
            and _source_dq_row_registration_catalog_visibility_required(row)
            and not registration_visible
        ):
            frame_summary["required_invalid_samples_not_visible_to_registration_catalog"] = (
                int(frame_summary["required_invalid_samples_not_visible_to_registration_catalog"])
                + invalid
            )
        sidecar_paths = set(str(path) for path in frame_summary.get("sidecar_paths") or [])
        sidecar_paths.update(str(path) for path in list(row.get("sidecar_paths") or []))
        frame_summary["sidecar_paths"] = sorted(sidecar_paths)
        frame_summary["sidecar_path_count"] = len(sidecar_paths)
        frame_summary["catalog_input_semantics"] = (
            "source_dq_applied_before_registration_catalog"
            if registration_visible
            else "source_dq_not_visible_to_registration_catalog"
        )

    rows_with_audit = 0
    for registration_row in registration_rows:
        frame_id = str(registration_row.get("frame_id") or "")
        if not frame_id:
            continue
        frame_summary = by_frame.get(frame_id, _empty_registration_source_dq_input(frame_id))
        registration_row["source_dq_registration_input"] = frame_summary
        rows_with_audit += 1

    positive_frame_summaries = [
        summary for summary in by_frame.values() if int(summary.get("invalid_samples") or 0) > 0
    ]
    summary = {
        "schema_version": 1,
        "available": bool(source_rows),
        "source_dq_row_count": len(source_rows),
        "registration_row_count": len(registration_rows),
        "registration_rows_with_source_dq_input": rows_with_audit if source_rows else 0,
        "registration_rows_missing_source_dq_input": 0 if source_rows else len(registration_rows),
        "frames_with_source_dq_rows": len(by_frame),
        "frames_with_invalid_samples": len(positive_frame_summaries),
        "invalid_samples": sum(int(row.get("invalid_samples") or 0) for row in source_rows),
        "applied_invalid_samples": sum(
            int(row.get("invalid_samples") or 0) for row in source_rows if bool(row.get("applied"))
        ),
        "pre_registration_catalog_visible_invalid_samples": sum(
            int(summary.get("pre_registration_catalog_visible_invalid_samples") or 0)
            for summary in by_frame.values()
        ),
        "post_registration_deferred_invalid_samples": sum(
            int(summary.get("post_registration_deferred_invalid_samples") or 0)
            for summary in by_frame.values()
        ),
        "required_invalid_samples_not_visible_to_registration_catalog": sum(
            int(summary.get("required_invalid_samples_not_visible_to_registration_catalog") or 0)
            for summary in by_frame.values()
        ),
        "catalog_input_semantics": (
            "source_dq_rows_joined_to_registration_results"
            if source_rows
            else "no_source_dq_rows_available_for_registration_results"
        ),
    }
    return {"summary": summary, "rows_by_frame_id": by_frame}


def _resident_source_dq_calibration_artifact_candidates(
    plan: dict[str, Any],
    *,
    run: Path,
    plan_root: Path,
) -> list[Path]:
    raw_candidates: list[Path] = []
    for key in (
        "calibration_artifacts_path",
        "source_dq_calibration_artifacts_path",
        "input_dq_calibration_artifacts_path",
    ):
        if plan.get(key):
            path = Path(str(plan[key]))
            if not path.is_absolute():
                path = plan_root / path
            raw_candidates.append(path)
    raw_candidates.extend([run / "calibration_artifacts.json", plan_root / "calibration_artifacts.json"])

    candidates: list[Path] = []
    seen: set[str] = set()
    for path in raw_candidates:
        key = str(path.resolve()) if path.exists() else str(path.absolute())
        if key in seen:
            continue
        seen.add(key)
        candidates.append(path)
    return candidates


def _resident_source_dq_sidecars_from_calibration_artifacts(
    plan: dict[str, Any],
    *,
    run: Path,
    plan_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    sidecars: dict[str, dict[str, Any]] = {}
    candidates = _resident_source_dq_calibration_artifact_candidates(plan, run=run, plan_root=plan_root)
    checked: list[dict[str, Any]] = []
    for artifact_path in candidates:
        exists = artifact_path.exists()
        candidate_row: dict[str, Any] = {"path": str(artifact_path), "exists": exists}
        if not exists:
            checked.append(candidate_row)
            continue
        payload = read_json(artifact_path)
        calibrated_lights = payload.get("calibrated_lights", []) if isinstance(payload, dict) else []
        candidate_row["calibrated_light_count"] = len(calibrated_lights) if isinstance(calibrated_lights, list) else 0
        sidecar_count = 0
        if isinstance(calibrated_lights, list):
            for item in calibrated_lights:
                if not isinstance(item, dict):
                    continue
                frame_id = item.get("frame_id")
                dq_mask_path = item.get("dq_mask_path")
                if frame_id is None or dq_mask_path in {None, ""}:
                    continue
                sidecar = Path(str(dq_mask_path))
                if not sidecar.is_absolute():
                    sidecar = sidecar if sidecar.exists() else artifact_path.parent / sidecar
                frame_key = str(frame_id)
                if frame_key not in sidecars:
                    sidecars[frame_key] = {
                        "path": sidecar,
                        "source": "calibration_artifacts",
                        "artifact_path": artifact_path,
                        "artifact_frame_id": frame_key,
                        "dq_summary": item.get("dq_summary"),
                        "cosmetic_correction": item.get("cosmetic_correction"),
                    }
                    sidecar_count += 1
        candidate_row["sidecar_count"] = sidecar_count
        checked.append(candidate_row)

    return sidecars, {
        "schema_version": 1,
        "source_model": "calibration_artifacts_dq_sidecar_index",
        "candidate_count": len(candidates),
        "checked": checked,
        "sidecar_frame_count": len(sidecars),
        "available": bool(sidecars),
    }


def _resident_source_dq_sidecar_record(
    frame: dict[str, Any],
    plan_root: Path,
    calibration_dq_sidecars: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    for key in (
        "source_dq_mask_path",
        "dq_mask_path",
        "calibration_dq_mask_path",
        "input_dq_mask_path",
    ):
        raw_path = frame.get(key)
        if raw_path is None or str(raw_path) == "":
            continue
        sidecar = Path(str(raw_path))
        if not sidecar.is_absolute():
            sidecar = plan_root / sidecar
        return {
            "path": sidecar,
            "source": "plan_frame_record",
            "plan_key": key,
        }
    if calibration_dq_sidecars:
        record = calibration_dq_sidecars.get(str(frame.get("id")))
        if record is not None:
            return record
    return None


def _resident_source_invalid_mask_from_frame(
    frame: dict[str, Any],
    data: Any,
    *,
    height: int,
    width: int,
    plan_root: Path,
    calibration_dq_sidecars: dict[str, dict[str, Any]] | None = None,
    resident_inline_source_dq: str = "off",
    resident_inline_source_dq_hot_sigma: float = 8.0,
    resident_inline_source_dq_cold_sigma: float = 8.0,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    components: list[tuple[np.ndarray | None, dict[str, Any]]] = []
    if resident_inline_source_dq not in {"cosmetic_cuda", "cosmetic_star_cuda"}:
        components.append(source_invalid_mask_from_array(data, height=height, width=width))
    if resident_inline_source_dq == "cosmetic":
        components.append(
            source_invalid_mask_from_inline_cosmetic(
                data,
                height=height,
                width=width,
                hot_sigma=resident_inline_source_dq_hot_sigma,
                cold_sigma=resident_inline_source_dq_cold_sigma,
            )
        )
    elif resident_inline_source_dq == "cosmetic_star":
        components.append(
            source_invalid_mask_from_star_protected_inline_cosmetic(
                data,
                height=height,
                width=width,
                hot_sigma=resident_inline_source_dq_hot_sigma,
                cold_sigma=resident_inline_source_dq_cold_sigma,
            )
        )
    sidecar_record = _resident_source_dq_sidecar_record(frame, plan_root, calibration_dq_sidecars)
    if sidecar_record is not None:
        sidecar_path = Path(sidecar_record["path"])
        sidecar_mask, sidecar_info = source_invalid_mask_from_sidecar_path(
            sidecar_path,
            height=height,
            width=width,
        )
        sidecar_info.update(
            {
                "sidecar_source": str(sidecar_record.get("source") or "unknown"),
                "sidecar_plan_key": sidecar_record.get("plan_key"),
                "sidecar_artifact_path": None
                if sidecar_record.get("artifact_path") is None
                else str(sidecar_record["artifact_path"]),
                "sidecar_artifact_frame_id": sidecar_record.get("artifact_frame_id"),
                "sidecar_artifact_dq_summary": sidecar_record.get("dq_summary"),
                "sidecar_artifact_cosmetic_correction": sidecar_record.get("cosmetic_correction"),
            }
        )
        components.append(
            (
                sidecar_mask,
                sidecar_info,
            )
        )
    return combine_source_invalid_masks(components, height=height, width=width)


def _resident_source_inline_cosmetic_thresholds_from_resident_stack(
    stack: Any,
    *,
    frame_index: int,
    height: int,
    width: int,
    resident_inline_source_dq: str = "off",
    resident_inline_source_dq_hot_sigma: float = 8.0,
    resident_inline_source_dq_cold_sigma: float = 8.0,
) -> dict[str, Any] | None:
    if resident_inline_source_dq not in {"cosmetic_cuda", "cosmetic_star_cuda"}:
        return None
    if resident_inline_source_dq == "cosmetic_star_cuda":
        return inline_star_protected_cosmetic_thresholds_from_resident_stack(
            stack,
            frame_index=int(frame_index),
            height=height,
            width=width,
            hot_sigma=resident_inline_source_dq_hot_sigma,
            cold_sigma=resident_inline_source_dq_cold_sigma,
        )
    return inline_cosmetic_thresholds_from_resident_stack(
        stack,
        frame_index=int(frame_index),
        height=height,
        width=width,
        hot_sigma=resident_inline_source_dq_hot_sigma,
        cold_sigma=resident_inline_source_dq_cold_sigma,
    )


def _resident_source_inline_cosmetic_thresholds_batch_from_resident_stack(
    stack: Any,
    *,
    frame_indices: list[int],
    height: int,
    width: int,
    resident_inline_source_dq: str = "off",
    resident_inline_source_dq_hot_sigma: float = 8.0,
    resident_inline_source_dq_cold_sigma: float = 8.0,
) -> dict[int, dict[str, Any]]:
    if resident_inline_source_dq not in {"cosmetic_cuda", "cosmetic_star_cuda"}:
        return {}
    if resident_inline_source_dq == "cosmetic_star_cuda":
        return {
            int(index): inline_star_protected_cosmetic_thresholds_from_resident_stack(
                stack,
                frame_index=int(index),
                height=height,
                width=width,
                hot_sigma=resident_inline_source_dq_hot_sigma,
                cold_sigma=resident_inline_source_dq_cold_sigma,
            )
            for index in frame_indices
        }
    return inline_cosmetic_thresholds_batch_from_resident_stack(
        stack,
        frame_indices=[int(index) for index in frame_indices],
        height=height,
        width=width,
        hot_sigma=resident_inline_source_dq_hot_sigma,
        cold_sigma=resident_inline_source_dq_cold_sigma,
    )


def _resident_dq_coverage_provenance(
    coverage_map: np.ndarray | None,
    low_rejection_map: np.ndarray | None,
    high_rejection_map: np.ndarray | None,
    active_frame_count: int,
    geometric_warp_coverage_map: np.ndarray | None = None,
    geometric_warp_coverage_frame_count: int | None = None,
    source_dq_summary: dict[str, Any] | None = None,
    rejection_map_stats: dict[str, Any] | None = None,
    precomputed_dq_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_count = max(0, int(active_frame_count))
    source_dq_fields = _resident_source_dq_provenance_fields(source_dq_summary)
    dq_stats = precomputed_dq_stats if isinstance(precomputed_dq_stats, dict) else {}
    if coverage_map is None:
        provenance = {
            "available": False,
            "active_frame_count": active_count,
            "reason": "resident integration did not emit a coverage map",
            **source_dq_fields,
        }
        source_terms: list[str] = []
        if source_dq_fields:
            source_terms.append("source_dq")
        if geometric_warp_coverage_map is not None:
            geometric = np.asarray(geometric_warp_coverage_map, dtype=np.float32)
            geometric_count = (
                active_count
                if geometric_warp_coverage_frame_count is None
                else max(0, int(geometric_warp_coverage_frame_count))
            )
            finite_geometric = np.isfinite(geometric)
            provenance.update(
                {
                    "geometric_warp_coverage": _resident_coverage_array_stats(geometric),
                    "geometric_warp_coverage_frame_count": geometric_count,
                    "geometric_zero_pixels": int(np.count_nonzero(finite_geometric & (geometric <= 0.5))),
                    "geometric_partial_pixels": int(
                        np.count_nonzero(
                            finite_geometric
                            & (geometric > 0.5)
                            & (geometric < float(geometric_count) - 0.5)
                        )
                        if geometric_count > 0
                        else 0
                    ),
                    "partial_edge_inference": "available_from_geometric_warp_coverage",
                }
            )
            source_terms.append("geometric_warp_coverage")
        if source_terms:
            provenance["source_terms"] = source_terms
        return provenance

    post_rejection = np.asarray(coverage_map, dtype=np.float32)
    post_rejection_stats = (
        dict(dq_stats["post_rejection_coverage"])
        if isinstance(dq_stats.get("post_rejection_coverage"), dict)
        else _resident_coverage_array_stats(post_rejection)
    )
    source_terms = ["post_rejection_coverage"]
    if low_rejection_map is not None:
        source_terms.append("low_rejection")
    if high_rejection_map is not None:
        source_terms.append("high_rejection")
    if source_dq_fields:
        source_terms.append("source_dq")
    geometric = None
    geometric_stats = None
    geometric_count = 0
    if geometric_warp_coverage_map is not None:
        geometric = np.asarray(geometric_warp_coverage_map, dtype=np.float32)
        geometric_stats = (
            dict(dq_stats["geometric_warp_coverage"])
            if isinstance(dq_stats.get("geometric_warp_coverage"), dict)
            else _resident_coverage_array_stats(geometric)
        )
        geometric_count = (
            active_count
            if geometric_warp_coverage_frame_count is None
            else max(0, int(geometric_warp_coverage_frame_count))
        )
        source_terms.append("geometric_warp_coverage")

    source_dq_changes_samples = _resident_source_dq_changes_samples(source_dq_summary)
    if geometric is not None and not source_dq_changes_samples:
        finite_pre_rejection = geometric
        finite_pre_rejection_stats = dict(geometric_stats or {})
        finite_pre_rejection_source = "geometric_warp_coverage"
    else:
        finite_pre_rejection = post_rejection.copy()
        if low_rejection_map is not None:
            finite_pre_rejection += np.nan_to_num(np.asarray(low_rejection_map, dtype=np.float32), nan=0.0)
        if high_rejection_map is not None:
            finite_pre_rejection += np.nan_to_num(np.asarray(high_rejection_map, dtype=np.float32), nan=0.0)
        finite_pre_rejection_stats = _resident_coverage_array_stats(finite_pre_rejection)
        finite_pre_rejection_source = "post_rejection_coverage_plus_rejection_maps"

    rejection_map_sample_count = _resident_rejection_map_sample_count(
        low_rejection_map,
        high_rejection_map,
        rejection_map_stats=rejection_map_stats,
    )
    can_reuse_geometric_counts = bool(
        finite_pre_rejection_source == "geometric_warp_coverage"
        and geometric is not None
        and dq_stats.get("stats_source") == "resident_dq_map_single_pass"
    )
    if can_reuse_geometric_counts:
        zero_pre_rejection_pixels = int(dq_stats.get("geometric_zero_pixels") or 0)
        partial_pre_rejection_pixels = int(dq_stats.get("geometric_partial_pixels") or 0)
        post_rejection_zero_pixels = int(dq_stats.get("post_rejection_zero_pixels") or 0)
        if dq_stats.get("rejection_reduced_pixels") is None:
            finite_pre = np.isfinite(finite_pre_rejection)
            finite_post = np.isfinite(post_rejection)
            rejection_reduced_pixels = int(
                np.count_nonzero(finite_pre & finite_post & (post_rejection < finite_pre_rejection - 0.5))
            )
            rejection_reduced_pixels_source = "coverage_difference"
        else:
            rejection_reduced_pixels = int(dq_stats.get("rejection_reduced_pixels") or 0)
            rejection_reduced_pixels_source = str(
                dq_stats.get("rejection_reduced_pixels_source") or "resident_dq_map_single_pass"
            )
    else:
        finite_pre = np.isfinite(finite_pre_rejection)
        finite_post = np.isfinite(post_rejection)
        zero_pre = finite_pre & (finite_pre_rejection <= 0.5)
        partial_pre = (
            finite_pre
            & (finite_pre_rejection > 0.5)
            & (finite_pre_rejection < float(active_count) - 0.5)
            if active_count > 0
            else np.zeros_like(finite_pre, dtype=bool)
        )
        rejection_reduced = finite_pre & finite_post & (post_rejection < finite_pre_rejection - 0.5)
        zero_pre_rejection_pixels = int(np.count_nonzero(zero_pre))
        partial_pre_rejection_pixels = int(np.count_nonzero(partial_pre))
        post_rejection_zero_pixels = int(np.count_nonzero(finite_post & (post_rejection <= 0.5)))
        rejection_reduced_pixels = int(np.count_nonzero(rejection_reduced))
        rejection_reduced_pixels_source = "coverage_difference"
    if rejection_map_sample_count is None:
        rejected_samples = finite_pre_rejection - post_rejection
        np.maximum(rejected_samples, 0.0, out=rejected_samples)
        rejected_sample_count = float(np.nansum(rejected_samples))
        rejected_sample_count_source = "coverage_difference"
    else:
        rejected_sample_count = float(rejection_map_sample_count)
        rejected_sample_count_source = "low_high_rejection_maps"

    result: dict[str, Any] = {
        "available": True,
        "active_frame_count": active_count,
        "source_terms": source_terms,
        "post_rejection_coverage": post_rejection_stats,
        "finite_pre_rejection_coverage": finite_pre_rejection_stats,
        "finite_pre_rejection_source": finite_pre_rejection_source,
        "zero_pre_rejection_pixels": zero_pre_rejection_pixels,
        "partial_pre_rejection_pixels": partial_pre_rejection_pixels,
        "post_rejection_zero_pixels": post_rejection_zero_pixels,
        "rejection_reduced_pixels": rejection_reduced_pixels,
        "rejection_reduced_pixels_source": rejection_reduced_pixels_source,
        "rejected_sample_count": rejected_sample_count,
        "rejected_sample_count_source": rejected_sample_count_source,
        "precomputed_dq_stats_used": can_reuse_geometric_counts,
        "partial_edge_inference": "deferred",
        "note": (
            "finite_pre_rejection_coverage is coverage + low/high rejection counts. "
            "It separates rejection loss from finite contributing samples but is not yet "
            "a pure geometric warp-footprint map."
        ),
        **source_dq_fields,
    }
    if geometric is not None:
        if can_reuse_geometric_counts:
            geometric_zero_pixels = int(dq_stats.get("geometric_zero_pixels") or 0)
            geometric_partial_pixels = int(dq_stats.get("geometric_partial_pixels") or 0)
            geometric_full_pixels = int(dq_stats.get("geometric_full_pixels") or 0)
        else:
            finite_geometric = np.isfinite(geometric)
            zero_geometric = finite_geometric & (geometric <= 0.5)
            partial_geometric = (
                finite_geometric
                & (geometric > 0.5)
                & (geometric < float(geometric_count) - 0.5)
                if geometric_count > 0
                else np.zeros_like(finite_geometric, dtype=bool)
            )
            full_geometric = (
                finite_geometric & (geometric >= float(geometric_count) - 0.5)
                if geometric_count > 0
                else np.zeros_like(finite_geometric, dtype=bool)
            )
            geometric_zero_pixels = int(np.count_nonzero(zero_geometric))
            geometric_partial_pixels = int(np.count_nonzero(partial_geometric))
            geometric_full_pixels = int(np.count_nonzero(full_geometric))
        result.update(
            {
                "geometric_warp_coverage": dict(geometric_stats or {}),
                "geometric_warp_coverage_frame_count": geometric_count,
                "geometric_frame_count_matches_active": geometric_count == active_count,
                "geometric_zero_pixels": geometric_zero_pixels,
                "geometric_partial_pixels": geometric_partial_pixels,
                "geometric_full_pixels": geometric_full_pixels,
                "partial_edge_inference": "available_from_geometric_warp_coverage",
                "note": (
                    "geometric_warp_coverage is accumulated by the resident CUDA warp path before "
                    "sigma rejection. finite_pre_rejection_coverage remains coverage + low/high "
                    "rejection counts for rejection accounting."
                ),
            }
        )
    return result


def _resident_output_map_selection(policy: str) -> dict[str, bool]:
    if policy not in _RESIDENT_OUTPUT_MAP_POLICIES:
        raise ValueError("resident_output_maps must be audit, science, or minimal")
    return {
        "master": True,
        "weight": policy in {"audit", "science"},
        "coverage": policy in {"audit", "science"},
        "low_rejection": policy == "audit",
        "high_rejection": policy == "audit",
        "dq": policy in {"audit", "science"},
    }


def _resident_stack_hardened_winsorized_available(cuda_module: Any) -> tuple[bool, str | None]:
    stack_cls = getattr(cuda_module, "ResidentCalibratedStack", None)
    if stack_cls is None:
        return False, "resident_calibrated_stack_unavailable"
    if not hasattr(stack_cls, "integrate_hardened_winsorized_sigma"):
        return False, "integrate_hardened_winsorized_sigma_unavailable"
    if not hasattr(stack_cls, "integrate_hardened_winsorized_sigma_timed"):
        return False, "integrate_hardened_winsorized_sigma_timed_unavailable"
    return True, None


def _resident_radix_select_winsorized_enabled() -> bool:
    value = os.environ.get("GLASS_CUDA_RADIX_SELECT_WINSORIZED", "").strip().lower()
    return value in {"1", "true", "yes", "on", "force", "radix", "radix_select"}


def _resolve_resident_rejection_max_fraction(
    *,
    rejection_mode: str,
    requested_resident_winsorized_mode: str,
    frame_count: int,
    dispatch_mode: str,
    resident_output_maps: str,
    tile_local_policy_mode: str,
    base_max_reject_fraction: float,
    base_source: str,
) -> tuple[float, str, dict[str, Any]]:
    base_value = float(base_max_reject_fraction)
    source = str(base_source or "resolved_default")
    details: dict[str, Any] = {
        "schema_version": 1,
        "base_max_reject_fraction": base_value,
        "base_source": source,
        "effective_max_reject_fraction": base_value,
        "effective_source": source,
        "resident_auto_coverage_guard_applied": False,
        "resident_auto_coverage_guard_frame_threshold": (
            RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_FRAME_THRESHOLD
        ),
        "resident_auto_coverage_guard_max_fraction": (
            RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_MAX_FRACTION
        ),
    }
    if source not in {"implicit_default", "plan_default", "legacy_default"}:
        details["reason"] = "explicit_or_plan_rejection_guard_preserved"
        return base_value, source, details
    if rejection_mode != "winsorized_sigma":
        details["reason"] = "not_winsorized_sigma"
        return base_value, source, details
    if requested_resident_winsorized_mode != RESIDENT_WINSORIZED_SIGMA_AUTO_MODE:
        details["reason"] = "not_resident_winsorized_auto"
        return base_value, source, details
    if dispatch_mode != "stack":
        details["reason"] = "not_stack_dispatch"
        return base_value, source, details
    if resident_output_maps == "minimal":
        details["reason"] = "minimal_output_maps_keep_fast_approx_default"
        return base_value, source, details
    if tile_local_policy_mode in {"apply_mean", "apply"}:
        details["reason"] = "tile_local_policy_apply_unsupported"
        return base_value, source, details
    if int(frame_count) <= RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_FRAME_THRESHOLD:
        details["reason"] = "small_stack_keeps_cpu_parity_guard"
        return base_value, source, details

    effective = min(base_value, RESIDENT_WINSORIZED_SIGMA_AUTO_COVERAGE_GUARD_MAX_FRACTION)
    effective_source = "resident_auto_large_stack_coverage_guard"
    details.update(
        {
            "effective_max_reject_fraction": float(effective),
            "effective_source": effective_source,
            "resident_auto_coverage_guard_applied": bool(effective != base_value),
            "reason": "resident_auto_large_stack_coverage_guard",
        }
    )
    return float(effective), effective_source, details


def _resident_winsorized_runtime_contract(
    *,
    rejection_mode: str,
    resident_winsorized_mode: str,
    frame_count: int,
    dispatch_mode: str,
    min_samples: int = 3,
    max_reject_fraction: float = 0.5,
    max_reject_fraction_source: str = "resolved_default",
    max_reject_fraction_resolution: dict[str, Any] | None = None,
    hardened_available: bool = True,
    hardened_unavailable_reason: str | None = None,
    segmented_cpu_fallback_available: bool = True,
    segmented_cpu_fallback_unavailable_reason: str | None = None,
    tile_local_policy_mode: str = "record",
    resident_output_maps: str = "audit",
) -> dict[str, Any]:
    requested_mode = str(resident_winsorized_mode)
    effective_mode = requested_mode
    resolution_reason = "explicit_not_winsorized"
    native_frame_limit_ok = int(frame_count) <= RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT
    hardened_execution_route = "not_applicable"
    if rejection_mode == "winsorized_sigma":
        if requested_mode == RESIDENT_WINSORIZED_SIGMA_AUTO_MODE:
            if dispatch_mode != "stack":
                effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                resolution_reason = "auto_fast_dispatch_not_stack"
            elif tile_local_policy_mode in {"apply_mean", "apply"}:
                effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                resolution_reason = "auto_fast_tile_local_policy_apply_unsupported"
            elif resident_output_maps == "minimal":
                effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                resolution_reason = "auto_fast_minimal_output_maps_without_diagnostics"
            elif native_frame_limit_ok and hardened_available:
                effective_mode = RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                hardened_execution_route = RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE
                resolution_reason = "auto_hardened_frame_count_within_limit"
            elif segmented_cpu_fallback_available:
                effective_mode = RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                hardened_execution_route = RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
                if not native_frame_limit_ok:
                    resolution_reason = (
                        "auto_hardened_segmented_cpu_frame_count_exceeds_native_limit:"
                        f"{int(frame_count)}>{RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT}"
                    )
                else:
                    resolution_reason = (
                        "auto_hardened_segmented_cpu_native_unavailable:"
                        f"{hardened_unavailable_reason or 'unknown'}"
                    )
            elif int(frame_count) > RESIDENT_WINSORIZED_SIGMA_AUTO_HARDENED_FRAME_LIMIT:
                effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                resolution_reason = (
                    "auto_fast_frame_count_exceeds_default_hardened_limit:"
                    f"{int(frame_count)}>{RESIDENT_WINSORIZED_SIGMA_AUTO_HARDENED_FRAME_LIMIT}"
                )
            elif not native_frame_limit_ok:
                effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                resolution_reason = (
                    "auto_fast_frame_count_exceeds_hardened_limit:"
                    f"{int(frame_count)}>{RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT}"
                )
            elif not hardened_available:
                effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                resolution_reason = (
                    "auto_fast_hardened_winsorized_unavailable:"
                    f"{hardened_unavailable_reason or 'unknown'}"
                )
        elif requested_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE:
            effective_mode = RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
            if native_frame_limit_ok and hardened_available:
                hardened_execution_route = RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE
                resolution_reason = "explicit_hardened_cpu_parity"
            elif segmented_cpu_fallback_available:
                hardened_execution_route = RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
                resolution_reason = (
                    "explicit_hardened_cpu_parity_segmented_cpu"
                    if not native_frame_limit_ok
                    else "explicit_hardened_cpu_parity_segmented_cpu_native_unavailable"
                )
            else:
                hardened_execution_route = RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE
                resolution_reason = "explicit_hardened_cpu_parity"
        else:
            effective_mode = RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
            resolution_reason = "explicit_fast_approx"
    if (
        rejection_mode == "winsorized_sigma"
        and effective_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
        and hardened_execution_route == "not_applicable"
    ):
        hardened_execution_route = RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE

    hardened_requested = (
        rejection_mode == "winsorized_sigma"
        and effective_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
    )
    native_route = hardened_execution_route == RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE
    segmented_route = hardened_execution_route == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
    return {
        "schema_version": 1,
        "rejection": str(rejection_mode),
        "requested_resident_winsorized_mode": requested_mode,
        "resident_winsorized_mode": effective_mode,
        "resolution_reason": resolution_reason,
        "hardened_execution_route": hardened_execution_route,
        "dispatch_mode": str(dispatch_mode),
        "resident_output_maps": resident_output_maps,
        "min_samples": int(min_samples),
        "max_reject_fraction": float(max_reject_fraction),
        "max_reject_fraction_source": str(max_reject_fraction_source),
        "max_reject_fraction_resolution": max_reject_fraction_resolution,
        "default_mode": RESIDENT_WINSORIZED_SIGMA_AUTO_MODE,
        "fast_approx_mode": RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
        "auto_hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_AUTO_HARDENED_FRAME_LIMIT,
        "hardened_requested": hardened_requested,
        "hardened_available": bool(hardened_available),
        "hardened_unavailable_reason": hardened_unavailable_reason,
        "hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
        "hardened_native_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT,
        "segmented_cpu_fallback_available": bool(segmented_cpu_fallback_available),
        "segmented_cpu_fallback_unavailable_reason": segmented_cpu_fallback_unavailable_reason,
        "frame_count": int(frame_count),
        "frame_limit_applies": bool(hardened_requested and native_route),
        "frame_limit_ok": (not hardened_requested) or segmented_route or native_frame_limit_ok,
        "native_frame_limit_ok": native_frame_limit_ok,
        "segmented_cpu_fallback_used": bool(hardened_requested and segmented_route),
        "requires_stack_dispatch": hardened_requested,
        "dispatch_ok": (not hardened_requested) or dispatch_mode == "stack",
        "native_hardened_required": bool(hardened_requested and native_route),
        "implementation": (
            "median_iqr_hardened_cuda_resident_prototype"
            if hardened_requested and native_route
            else "median_iqr_hardened_cpu_stack_engine_resident_tile_download"
            if hardened_requested and segmented_route
            else "two_stage_mean_std_fast_approximation"
            if rejection_mode == "winsorized_sigma"
            else "not_winsorized"
        ),
    }


def _validate_resident_winsorized_runtime_contract(contract: dict[str, Any]) -> None:
    if not contract.get("hardened_requested"):
        return
    route = str(contract.get("hardened_execution_route") or RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE)
    if route == RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE and not contract.get("hardened_available", True):
        raise ValueError(
            "resident_winsorized_mode=hardened_cpu_parity requires native hardened winsorized CUDA support: "
            f"{contract.get('hardened_unavailable_reason') or 'unknown'}"
        )
    if route == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE and not contract.get(
        "segmented_cpu_fallback_available", False
    ):
        raise ValueError(
            "resident_winsorized_mode=hardened_cpu_parity requires segmented CPU StackEngine fallback "
            "when native hardened winsorized CUDA cannot cover this group: "
            f"{contract.get('segmented_cpu_fallback_unavailable_reason') or 'unknown'}"
        )
    if not contract.get("dispatch_ok"):
        raise ValueError(
            "resident_winsorized_mode=hardened_cpu_parity requires resident_integration_dispatch=stack"
        )
    if not contract.get("frame_limit_ok"):
        raise ValueError(
            "resident_winsorized_mode=hardened_cpu_parity currently supports at most "
            f"{contract['hardened_frame_limit']} resident frames per filter/shape group; "
            f"got {contract['frame_count']}"
        )


def _resident_winsorized_contract_with_active_count(
    contract: dict[str, Any],
    *,
    active_frame_count: int,
) -> dict[str, Any]:
    updated = dict(contract)
    active_count = int(active_frame_count)
    frame_count = int(updated.get("frame_count", 0))
    native_limit = int(
        updated.get(
            "hardened_native_frame_limit",
            RESIDENT_WINSORIZED_SIGMA_HARDENED_NATIVE_FRAME_LIMIT,
        )
    )
    active_limit_ok = 0 < active_count <= native_limit
    radix_select_enabled = _resident_radix_select_winsorized_enabled()
    radix_select_admission_ok = bool(radix_select_enabled and active_count > native_limit)
    can_promote = (
        updated.get("hardened_requested", False)
        and updated.get("hardened_available", True)
        and updated.get("hardened_execution_route")
        == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
        and frame_count > native_limit
        and (active_limit_ok or radix_select_admission_ok)
        and updated.get("dispatch_ok", True)
    )
    updated.update(
        {
            "active_frame_count": active_count,
            "native_active_frame_limit_ok": bool(active_limit_ok),
            "native_radix_select_winsorized_enabled": bool(radix_select_enabled),
            "native_radix_select_admission_ok": bool(radix_select_admission_ok),
            "native_active_count_admission_available": bool(can_promote),
            "late_native_active_count_promotion": bool(can_promote),
        }
    )
    if not can_promote:
        return updated

    if radix_select_admission_ok:
        resolution_reason = (
            "late_native_radix_select_active_count:"
            f"{active_count}>{native_limit};frame_count:{frame_count}"
        )
        implementation = "median_iqr_hardened_cuda_resident_radix_select_prototype"
    else:
        resolution_reason = (
            "late_native_active_count_within_limit:"
            f"{active_count}<={native_limit}<frame_count:{frame_count}"
        )
        implementation = "median_iqr_hardened_cuda_resident_prototype"
    updated.update(
        {
            "resolution_reason": resolution_reason,
            "hardened_execution_route": RESIDENT_WINSORIZED_SIGMA_NATIVE_CUDA_ROUTE,
            "frame_limit_applies": True,
            "frame_limit_ok": True,
            "segmented_cpu_fallback_used": False,
            "native_hardened_required": True,
            "implementation": implementation,
        }
    )
    return updated


class _ResidentStackFrameImageSource:
    path: Path | None = None
    channels = 1
    dtype = "float32"

    def __init__(self, stack: Any, frame_index: int, frame_id: str, width: int, height: int):
        self._stack = stack
        self._frame_index = int(frame_index)
        self.frame_id = str(frame_id)
        self.width = int(width)
        self.height = int(height)
        self.metadata = {
            "frame_index": self._frame_index,
            "frame_id": self.frame_id,
            "source": "resident_calibrated_stack",
            "mask_from_finite_only": True,
        }

    def read_tile(self, window: Any, dtype: Any = np.float32) -> np.ndarray:
        if not hasattr(self._stack, "download_frame_tile"):
            raise RuntimeError(
                "segmented resident CPU StackEngine fallback requires "
                "ResidentCalibratedStack.download_frame_tile"
            )
        tile = self._stack.download_frame_tile(
            self._frame_index,
            int(window.x0),
            int(window.y0),
            int(window.x1),
            int(window.y1),
        )
        return np.asarray(tile, dtype=dtype)

    def read_mask_tile(self, window: Any) -> DQMask:
        return DQMask.empty(window.shape)


def _integrate_resident_hardened_winsorized_with_cpu_stack_engine(
    stack: Any,
    frames: list[dict[str, Any]],
    weights: np.ndarray,
    *,
    width: int,
    height: int,
    low_sigma: float,
    high_sigma: float,
    min_samples: int,
    max_reject_fraction: float,
    tile_size: int = 256,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    frame_ids = tuple(str(frame["id"]) for frame in frames)
    if not frame_ids:
        raise ValueError("resident hardened CPU fallback requires at least one frame")
    tile_size = max(1, int(tile_size))
    frame_weights = np.asarray(weights, dtype=np.float32)
    if frame_weights.size != len(frame_ids):
        raise ValueError(
            "resident hardened CPU fallback weight count does not match frame count: "
            f"{frame_weights.size}!={len(frame_ids)}"
        )
    positive_weight_mask = np.isfinite(frame_weights) & (frame_weights > 0.0)
    frame_indices = np.flatnonzero(positive_weight_mask).astype(np.int64)
    if frame_indices.size == 0:
        raise ValueError("resident hardened CPU fallback requires at least one positive-weight frame")
    active_frame_ids = tuple(frame_ids[int(index)] for index in frame_indices)
    active_frame_weights = frame_weights[frame_indices]
    skipped_zero_weight_frame_count = int(len(frame_ids) - len(active_frame_ids))
    request = StackRequest(
        frame_ids=active_frame_ids,
        source_kind="light",
        combine=CombinePolicy(method="weighted_mean", accumulator_dtype="float32"),
        rejection=RejectionPolicy(
            method="winsorized_sigma",
            iterations=1,
            low_sigma=float(low_sigma),
            high_sigma=float(high_sigma),
            min_samples=int(min_samples),
            max_reject_fraction=float(max_reject_fraction),
        ),
        output_maps=OutputMapPolicy(
            coverage=True,
            weight=True,
            low_rejection=True,
            high_rejection=True,
            dq=False,
        ),
        weights={
            frame_id: float(active_frame_weights[index])
            for index, frame_id in enumerate(active_frame_ids)
        },
        metadata={
            "resident_hardened_cpu_stack_engine_fallback": True,
            "resident_download_tile_source": "ResidentCalibratedStack.download_frames_tile",
            "resident_download_tile_fallback_source": "ResidentCalibratedStack.download_frame_tile",
            "resident_frame_count": len(frame_ids),
            "resident_active_frame_count": len(active_frame_ids),
            "resident_zero_weight_skipped_frame_count": skipped_zero_weight_frame_count,
        },
    )
    master = np.zeros((int(height), int(width)), dtype=np.float32)
    weight_map = np.zeros_like(master, dtype=np.float32)
    coverage_map = np.zeros_like(master, dtype=np.float32)
    low_rejection_map = np.zeros_like(master, dtype=np.float32)
    high_rejection_map = np.zeros_like(master, dtype=np.float32)
    accumulator_dtype = np.float32

    input_sample_total = 0
    input_valid_sample_total = 0
    input_invalid_sample_total = 0
    input_nonfinite_sample_total = 0
    coverage_zero_pixel_total = 0
    low_rejected_pixel_total = 0
    high_rejected_pixel_total = 0
    rejected_low_total = 0
    rejected_high_total = 0
    valid_total = 0
    tile_count = 0
    batch_tile_download_used = False
    batch_tile_download_available = hasattr(stack, "download_frames_tile")
    batch_tile_download_native_available = bool(
        getattr(stack, "download_frames_tile_native_available", lambda: False)()
    )
    batch_tile_download_call_count = 0
    single_frame_tile_download_call_count = 0
    download_method_counts: dict[str, int] = {}

    start = perf_counter()
    for tile in iter_tiles(int(width), int(height), tile_size):
        tile_count += 1
        window = TileWindow(tile.y0, tile.y1, tile.x0, tile.x1)
        if batch_tile_download_available:
            stack_tile = np.asarray(
                stack.download_frames_tile(
                    frame_indices,
                    int(window.x0),
                    int(window.y0),
                    int(window.x1),
                    int(window.y1),
                ),
                dtype=np.float32,
            )
            download_method = "ResidentCalibratedStack.download_frames_tile"
            batch_tile_download_used = True
            batch_tile_download_call_count += 1
        else:
            if not hasattr(stack, "download_frame_tile"):
                raise RuntimeError(
                    "segmented resident CPU StackEngine fallback requires "
                    "ResidentCalibratedStack.download_frames_tile or download_frame_tile"
                )
            stack_tile = np.stack(
                [
                    np.asarray(
                        stack.download_frame_tile(
                            int(frame_index),
                            int(window.x0),
                            int(window.y0),
                            int(window.x1),
                            int(window.y1),
                        ),
                        dtype=np.float32,
                    )
                    for frame_index in frame_indices
                ],
                axis=0,
            )
            download_method = "ResidentCalibratedStack.download_frame_tile_loop"
            single_frame_tile_download_call_count += len(active_frame_ids)
        download_method_counts[download_method] = download_method_counts.get(download_method, 0) + 1
        expected_shape = (len(active_frame_ids), *window.shape)
        if stack_tile.shape != expected_shape:
            raise ValueError(
                "resident batch tile download returned shape "
                f"{stack_tile.shape}, expected {expected_shape}"
            )
        input_valid = np.isfinite(stack_tile)
        valid, low, high = _apply_rejection(stack_tile, input_valid, request.rejection)
        tile_master, tile_weight, tile_coverage, _tile_variance = _combine_tile(
            stack_tile,
            valid,
            active_frame_weights,
            method=request.combine.method,
            accumulator_dtype=accumulator_dtype,
        )
        y_slice, x_slice = window.as_slices()
        master[y_slice, x_slice] = tile_master
        weight_map[y_slice, x_slice] = tile_weight
        coverage_map[y_slice, x_slice] = tile_coverage
        low_rejection_map[y_slice, x_slice] = low
        high_rejection_map[y_slice, x_slice] = high

        input_sample_total += int(stack_tile.size)
        input_valid_sample_total += int(np.count_nonzero(input_valid))
        input_invalid_sample_total += int(np.count_nonzero(~input_valid))
        input_nonfinite_sample_total += int(np.count_nonzero(~np.isfinite(stack_tile)))
        coverage_zero_pixel_total += int(np.count_nonzero(tile_coverage <= 0))
        low_rejected_pixel_total += int(np.count_nonzero(low > 0))
        high_rejected_pixel_total += int(np.count_nonzero(high > 0))
        rejected_low_total += int(np.sum(low))
        rejected_high_total += int(np.sum(high))
        valid_total += int(np.sum(tile_coverage))
    total_s = perf_counter() - start
    metrics: dict[str, float | int | str] = {
        "frame_count": len(frame_ids),
        "active_frame_count": len(active_frame_ids),
        "zero_weight_skipped_frame_count": skipped_zero_weight_frame_count,
        "width": int(width),
        "height": int(height),
        "combine": request.combine.method,
        "rejection": request.rejection.method,
        "rejection_scale_estimator": rejection_scale_estimator(request.rejection),
        "valid_samples": valid_total,
        "input_valid_samples": input_valid_sample_total,
        "input_invalid_samples": input_invalid_sample_total,
        "low_rejected": rejected_low_total,
        "high_rejected": rejected_high_total,
        "rejected_samples": rejected_low_total + rejected_high_total,
    }
    dq_provenance: dict[str, Any] = {
        "schema_version": 1,
        "resident_frame_count": len(frame_ids),
        "resident_active_frame_count": len(active_frame_ids),
        "resident_zero_weight_skipped_frame_count": skipped_zero_weight_frame_count,
        "input_samples": input_sample_total,
        "input_valid_samples_before_rejection": input_valid_sample_total,
        "input_invalid_samples_before_rejection": input_invalid_sample_total,
        "input_flagged_samples": 0,
        "input_nonfinite_samples": input_nonfinite_sample_total,
        "input_dq_flag_counts": {flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID},
        "valid_samples_after_rejection": valid_total,
        "low_rejected_samples": rejected_low_total,
        "high_rejected_samples": rejected_high_total,
        "rejected_samples": rejected_low_total + rejected_high_total,
        "rejection_policy": rejection_policy_provenance(request.rejection),
        "output_coverage_zero_pixels": coverage_zero_pixel_total,
        "output_low_rejected_pixels": low_rejected_pixel_total,
        "output_high_rejected_pixels": high_rejected_pixel_total,
        "output_dq_summary": None,
        "resident_download_tile_source": (
            "ResidentCalibratedStack.download_frames_tile"
            if batch_tile_download_used
            else "ResidentCalibratedStack.download_frame_tile"
        ),
        "semantics": (
            "Resident calibrated samples are downloaded as stack tiles from VRAM and "
            "processed through the GLASS StackEngine rejection/combine rules after "
            "zero-weight resident frames have been excluded from the replay. Source-DQ "
            "invalid samples are already represented as non-finite resident samples."
        ),
    }
    result = StackEngineResult(
        master=master,
        weight_map=weight_map,
        coverage_map=coverage_map,
        low_rejection_map=low_rejection_map,
        high_rejection_map=high_rejection_map,
        variance_map=None,
        dq_mask=None,
        dq_provenance=dq_provenance,
        metrics=metrics,
    )
    result_contract = build_stack_engine_result_contract(result, request=request)
    result.dq_provenance["result_contract"] = result_contract
    result.metrics["result_contract_passed"] = bool(result_contract["passed"])
    timing = {
        "schema_version": 1,
        "native_method": "CPUStackEngine.batch_tile_replay_from_resident_download_tiles",
        "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
        "hardened_execution_route": RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE,
        "execution_path": "resident_cpu_stack_engine_batch_tile_download_hardened_winsorized",
        "frame_count": len(frame_ids),
        "active_frame_count": len(active_frame_ids),
        "zero_weight_skipped_frame_count": skipped_zero_weight_frame_count,
        "stack_engine_request_frame_count": len(active_frame_ids),
        "width": int(width),
        "height": int(height),
        "tile_size": int(tile_size),
        "tile_count_estimate": int(
            ((int(width) + tile_size - 1) // tile_size)
            * ((int(height) + tile_size - 1) // tile_size)
        ),
        "tile_count": int(tile_count),
        "batch_tile_download_available": bool(batch_tile_download_available),
        "batch_tile_download_native_available": bool(batch_tile_download_native_available),
        "batch_tile_download_used": bool(batch_tile_download_used),
        "batch_tile_download_call_count": int(batch_tile_download_call_count),
        "single_frame_tile_download_call_count": int(single_frame_tile_download_call_count),
        "download_method_counts": download_method_counts,
        "low_sigma": float(low_sigma),
        "high_sigma": float(high_sigma),
        "min_samples": int(min_samples),
        "max_reject_fraction": float(max_reject_fraction),
        "total_s": float(total_s),
        "result_contract_passed": bool(result.metrics.get("result_contract_passed", False)),
        "valid_samples": int(result.metrics.get("valid_samples", 0) or 0),
        "low_rejected": int(result.metrics.get("low_rejected", 0) or 0),
        "high_rejected": int(result.metrics.get("high_rejected", 0) or 0),
        "segmented_cpu_fallback": True,
        "limitations": [
            "CPU StackEngine fallback preserves median/IQR winsorized parity but downloads resident tiles to host.",
            "This route is a correctness fallback for groups outside the native 512-frame prototype limit.",
        ],
    }
    return (
        result.master,
        np.zeros_like(result.master, dtype=np.float32) if result.weight_map is None else result.weight_map,
        np.zeros_like(result.master, dtype=np.float32) if result.coverage_map is None else result.coverage_map,
        np.zeros_like(result.master, dtype=np.float32)
        if result.low_rejection_map is None
        else result.low_rejection_map,
        np.zeros_like(result.master, dtype=np.float32)
        if result.high_rejection_map is None
        else result.high_rejection_map,
        timing,
    )


def _count_map_for_write(data: np.ndarray, dtype: Any) -> np.ndarray:
    return np.rint(np.asarray(data)).astype(dtype, copy=False)


def _array_storage_bytes(data: np.ndarray, dtype: Any) -> int:
    return int(np.asarray(data).size * np.dtype(dtype).itemsize)


def _write_one_resident_output(spec: dict[str, Any]) -> tuple[str, float, dict[str, Any]]:
    name = str(spec["name"])
    dtype = spec.get("dtype", np.float32)
    data = spec["data"]
    if spec.get("round_counts"):
        data = _count_map_for_write(data, dtype)
    start = perf_counter()
    write_fits_data(spec["path"], data, spec.get("header"), dtype=dtype)
    elapsed = perf_counter() - start
    storage = {
        "dtype": np.dtype(dtype).name,
        "estimated_data_bytes": _array_storage_bytes(data, dtype),
        "writer_backend": fits_write_backend(data, dtype),
        "writer_profile": fits_write_profile(data, dtype),
    }
    return name, elapsed, storage


def _write_resident_outputs(
    specs: list[dict[str, Any]],
    *,
    max_workers: int | None = None,
) -> tuple[float, dict[str, float], dict[str, dict[str, Any]], int]:
    if not specs:
        return 0.0, {}, {}, 0
    worker_count = max(1, min(len(specs), int(max_workers or len(specs))))
    start = perf_counter()
    breakdown: dict[str, float] = {}
    storage: dict[str, dict[str, Any]] = {}
    if worker_count == 1:
        for spec in specs:
            name, elapsed, entry = _write_one_resident_output(spec)
            breakdown[name] = elapsed
            storage[name] = entry
    else:
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="glass-output") as executor:
            futures = [executor.submit(_write_one_resident_output, spec) for spec in specs]
            for future in futures:
                name, elapsed, entry = future.result()
                breakdown[name] = elapsed
                storage[name] = entry
    return perf_counter() - start, breakdown, storage, worker_count


def _resident_star_threshold_candidates(
    stack: Any,
    reference_index: int,
    moving_index: int,
    fixed_threshold: float,
) -> tuple[list[float], str]:
    if fixed_threshold > 0.0:
        return [float(fixed_threshold)], "fixed"
    if not hasattr(stack, "frame_global_stats"):
        raise RuntimeError("resident star auto-threshold requires frame_global_stats")

    reference_stats = stack.frame_global_stats(reference_index)
    moving_stats = stack.frame_global_stats(moving_index)
    candidates: list[float] = []
    for sigma in _AUTO_STAR_THRESHOLD_SIGMAS:
        frame_thresholds: list[float] = []
        for stats in (reference_stats, moving_stats):
            if int(stats.get("valid_pixels", 0)) <= 0:
                continue
            mean = float(stats["mean"])
            std = float(stats["std"])
            if np.isfinite(mean) and np.isfinite(std) and std > 0.0:
                frame_thresholds.append(max(0.0, mean + float(sigma) * std))
        if frame_thresholds:
            candidates.append(min(frame_thresholds))
    if not candidates:
        candidates.append(30.0)

    unique: list[float] = []
    seen: set[float] = set()
    for threshold in candidates:
        rounded = round(float(threshold), 6)
        if rounded in seen:
            continue
        seen.add(rounded)
        unique.append(float(threshold))
    return unique, "auto_mean_std"


def _resident_star_registration_score(result: dict[str, Any]) -> tuple[int, float, int]:
    inliers = int(result.get("mutual_inliers", 0))
    rms = float(result.get("rms_px", float("nan")))
    finite_rms = rms if np.isfinite(rms) else float("inf")
    support = min(int(result.get("reference_count", 0)), int(result.get("moving_count", 0)))
    return inliers, -finite_rms, support


def _resident_similarity_score(result: dict[str, Any]) -> tuple[int, float, int]:
    inliers = int(result.get("refined_inliers", result.get("inliers", 0)))
    rms = float(result.get("refit_rms_px", result.get("rms_px", float("nan"))))
    finite_rms = rms if np.isfinite(rms) else float("inf")
    support = min(int(result.get("reference_count", 0)), int(result.get("moving_count", 0)))
    return inliers, -finite_rms, support


def _resident_triangle_agreement_quality(
    pixel_ncc: float,
    pixel_rms_adu: float,
    fit_rms_px: float,
    rms_scale_adu: float,
    min_score: float | None = None,
) -> dict[str, Any]:
    rms_scale = float(rms_scale_adu)
    if rms_scale <= 0.0:
        raise ValueError("triangle agreement RMS scale must be positive")
    min_score_value = None if min_score is None else float(min_score)
    if min_score_value is not None and (min_score_value < 0.0 or min_score_value > 1.0):
        raise ValueError("triangle minimum agreement score must be in [0, 1]")

    ncc = _float_or_nan(pixel_ncc)
    pixel_rms = _float_or_nan(pixel_rms_adu)
    fit_rms = _float_or_nan(fit_rms_px)
    score = float("nan")
    reason = "ok"
    if not np.isfinite(ncc):
        reason = "pixel_ncc_unavailable"
    elif not np.isfinite(pixel_rms):
        reason = "pixel_rms_unavailable"
    else:
        score = float(ncc) / (1.0 + max(0.0, float(pixel_rms)) / rms_scale)

    if min_score_value is None:
        status = "audit_only" if np.isfinite(score) else "unavailable"
    elif not np.isfinite(score) or score < min_score_value:
        status = "failed"
        if reason == "ok":
            reason = "below_min_score"
    else:
        status = "ok"

    return {
        "score": score,
        "status": status,
        "reason": reason,
        "pixel_ncc": ncc,
        "pixel_rms_adu": pixel_rms,
        "fit_rms_px": fit_rms,
        "rms_scale_adu": rms_scale,
        "min_score": min_score_value,
    }


def _resident_triangle_agreement_policy(
    quality: dict[str, Any],
    action: str,
    min_weight: float = 0.0,
) -> dict[str, Any]:
    if action not in {"fail", "downweight", "flag"}:
        raise ValueError("triangle agreement action must be fail, downweight, or flag")
    floor = float(min_weight)
    if floor < 0.0 or floor > 1.0:
        raise ValueError("triangle agreement minimum weight must be in [0, 1]")

    status = str(quality.get("status") or "unavailable")
    result = {
        "action": action,
        "status": status,
        "hard_failure": False,
        "weight_multiplier": 1.0,
        "failure_message": None,
    }
    if status != "failed":
        return result

    score = _float_or_nan(quality.get("score"))
    min_score = quality.get("min_score")
    if min_score is None:
        min_score_value = float("nan")
    else:
        min_score_value = float(min_score)
    failure_message = "agreement_score " + f"{score:.6g} < {min_score_value:.6g}"
    if action == "fail":
        result["hard_failure"] = True
        result["failure_message"] = failure_message
        return result
    if action == "flag":
        result["status"] = "flagged"
        return result

    multiplier = 0.0
    if np.isfinite(score) and np.isfinite(min_score_value) and min_score_value > 0.0:
        multiplier = min(1.0, max(floor, max(0.0, score) / min_score_value))
    elif floor > 0.0:
        multiplier = floor
    result["weight_multiplier"] = float(multiplier)
    result["status"] = "downweighted" if multiplier > 0.0 else "failed"
    if multiplier <= 0.0:
        result["hard_failure"] = True
        result["failure_message"] = failure_message + "; downweight multiplier was zero"
    return result


def _resident_triangle_agreement_warnings(quality: dict[str, Any]) -> list[str]:
    warnings = [
        f"triangle_agreement_score={float(quality.get('score', float('nan'))):.6g}",
        f"triangle_agreement_status={quality.get('status', 'unavailable')}",
        f"triangle_agreement_reason={quality.get('reason', 'unavailable')}",
        f"triangle_agreement_rms_scale={float(quality.get('rms_scale_adu', float('nan'))):.6g}",
        f"triangle_min_agreement_score={quality.get('min_score')}",
    ]
    if "action" in quality:
        warnings.append(f"triangle_agreement_action={quality.get('action')}")
    if "weight_multiplier" in quality:
        warnings.append(
            f"triangle_agreement_weight_multiplier={float(quality.get('weight_multiplier', 1.0)):.6g}"
        )
    return warnings


def _registration_motion_translation(matrix: Any) -> tuple[float, float] | None:
    try:
        values = np.asarray(matrix, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if values.shape != (3, 3) or not np.all(np.isfinite(values[:2, 2])):
        return None
    return float(values[0, 2]), float(values[1, 2])


def _registration_motion_cluster(matrix: Any) -> str:
    try:
        values = np.asarray(matrix, dtype=np.float64)
    except (TypeError, ValueError):
        return "unavailable"
    if values.shape != (3, 3) or not np.all(np.isfinite(values[:2, :2])):
        return "unavailable"
    trace = float(values[0, 0] + values[1, 1])
    determinant = float(values[0, 0] * values[1, 1] - values[0, 1] * values[1, 0])
    trace_bucket = "trace_pos" if trace >= 0.0 else "trace_neg"
    det_bucket = "det_pos" if determinant >= 0.0 else "det_neg"
    return f"{trace_bucket}_{det_bucket}"


def _resident_registration_motion_weighting(
    frame_ids: list[str],
    matrices: list[Any],
    weights: list[float],
    *,
    mode: str = "off",
    threshold_sigma: float = 16.0,
    min_weight: float = 0.05,
    power: float = 2.0,
    scale_floor_px: float = 1.0,
) -> dict[str, Any]:
    if mode not in {"off", "translation_mad"}:
        raise ValueError("resident registration motion weighting must be off or translation_mad")
    if threshold_sigma <= 0.0:
        raise ValueError("resident registration motion threshold must be positive")
    if min_weight < 0.0 or min_weight > 1.0:
        raise ValueError("resident registration motion minimum weight must be in [0, 1]")
    if power <= 0.0:
        raise ValueError("resident registration motion power must be positive")
    if scale_floor_px <= 0.0:
        raise ValueError("resident registration motion scale floor must be positive")
    multipliers = [1.0 for _ in frame_ids]
    rows: list[dict[str, Any]] = []
    base = {
        "enabled": mode != "off",
        "mode": mode,
        "threshold_sigma": float(threshold_sigma),
        "min_weight": float(min_weight),
        "power": float(power),
        "scale_floor_px": float(scale_floor_px),
        "frame_count": len(frame_ids),
        "eligible_frame_count": 0,
        "downweighted_frame_count": 0,
        "center_translation": None,
        "clusters": [],
        "median_distance_px": None,
        "robust_scale_px": None,
        "multipliers": multipliers,
        "frame_results": rows,
    }
    translations_by_cluster: dict[str, list[tuple[int, float, float]]] = {}
    for index, (frame_id, matrix, weight) in enumerate(zip(frame_ids, matrices, weights, strict=True)):
        translation = _registration_motion_translation(matrix)
        cluster = _registration_motion_cluster(matrix)
        weight_value = float(weight)
        if translation is None or weight_value <= 0.0 or not np.isfinite(weight_value):
            rows.append(
                {
                    "frame_id": frame_id,
                    "eligible": False,
                    "reason": "zero_weight_or_missing_matrix",
                    "multiplier": 1.0,
                    "weight_before_motion": weight_value,
                    "weight_after_motion": weight_value,
                }
            )
            continue
        tx, ty = translation
        translations_by_cluster.setdefault(cluster, []).append((index, tx, ty))
        rows.append(
            {
                "frame_id": frame_id,
                "eligible": mode != "off",
                "motion_cluster": cluster,
                "translation_x": tx,
                "translation_y": ty,
                "multiplier": 1.0,
                "weight_before_motion": weight_value,
                "weight_after_motion": weight_value,
            }
        )
    base["eligible_frame_count"] = sum(len(items) for items in translations_by_cluster.values())
    if mode == "off" or base["eligible_frame_count"] < 3:
        if mode != "off" and base["eligible_frame_count"] < 3:
            base["reason"] = "fewer_than_three_eligible_frames"
        return base

    cluster_summaries: list[dict[str, Any]] = []
    for cluster, translations in sorted(translations_by_cluster.items()):
        if len(translations) < 3:
            cluster_summaries.append(
                {
                    "cluster": cluster,
                    "eligible_frame_count": len(translations),
                    "reason": "fewer_than_three_eligible_frames",
                }
            )
            continue
        tx_values = np.asarray([item[1] for item in translations], dtype=np.float64)
        ty_values = np.asarray([item[2] for item in translations], dtype=np.float64)
        center_x = float(np.median(tx_values))
        center_y = float(np.median(ty_values))
        distances = np.sqrt((tx_values - center_x) ** 2 + (ty_values - center_y) ** 2)
        median_distance = float(np.median(distances))
        mad = float(np.median(np.abs(distances - median_distance)) * 1.4826)
        robust_scale = max(mad, float(scale_floor_px))
        cluster_summaries.append(
            {
                "cluster": cluster,
                "eligible_frame_count": len(translations),
                "center_translation": {"x": center_x, "y": center_y},
                "median_distance_px": median_distance,
                "robust_scale_px": robust_scale,
            }
        )
        for local_index, (frame_index, _tx, _ty) in enumerate(translations):
            distance = float(distances[local_index])
            excess = max(0.0, distance - median_distance)
            score = excess / robust_scale
            multiplier = 1.0
            if score > float(threshold_sigma):
                multiplier = max(float(min_weight), (float(threshold_sigma) / score) ** float(power))
            multipliers[frame_index] = float(multiplier)
            rows[frame_index].update(
                {
                    "distance_px": distance,
                    "excess_distance_px": excess,
                    "score": float(score),
                    "threshold_sigma": float(threshold_sigma),
                    "threshold_exceeded": bool(score > float(threshold_sigma)),
                    "multiplier": float(multiplier),
                    "weight_after_motion": float(weights[frame_index]) * float(multiplier),
                }
            )
    base["clusters"] = cluster_summaries
    completed_clusters = [item for item in cluster_summaries if item.get("center_translation") is not None]
    if len(completed_clusters) == 1:
        base["center_translation"] = completed_clusters[0]["center_translation"]
        base["median_distance_px"] = completed_clusters[0]["median_distance_px"]
        base["robust_scale_px"] = completed_clusters[0]["robust_scale_px"]
    base["downweighted_frame_count"] = int(sum(1 for value in multipliers if value < 1.0))
    return base


def _registration_motion_warning(row: dict[str, Any]) -> list[str]:
    return [
        f"registration_motion_weight_multiplier={float(row.get('multiplier', 1.0)):.6g}",
        f"registration_motion_distance_px={float(row.get('distance_px', float('nan'))):.6g}",
        f"registration_motion_score={float(row.get('score', float('nan'))):.6g}",
        f"registration_motion_threshold_sigma={float(row.get('threshold_sigma', float('nan'))):.6g}",
    ]


def _load_frame_weight_proposal(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "enabled": False,
            "path": None,
            "frame_count": 0,
            "frame_multipliers": {},
            "rows": [],
        }
    source = Path(path)
    payload = read_json(source)
    rows_raw = payload.get("frame_multipliers")
    if isinstance(rows_raw, dict):
        rows = [
            {"frame_id": str(frame_id), "multiplier": multiplier}
            for frame_id, multiplier in rows_raw.items()
        ]
    elif isinstance(rows_raw, list):
        rows = [row for row in rows_raw if isinstance(row, dict)]
    else:
        raise ValueError("frame weight proposal must contain frame_multipliers list or object")
    multipliers: dict[str, float] = {}
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        frame_id = row.get("frame_id")
        if frame_id is None:
            raise ValueError("frame weight proposal row is missing frame_id")
        multiplier = float(row.get("multiplier"))
        if not np.isfinite(multiplier) or multiplier < 0.0 or multiplier > 1.0:
            raise ValueError("frame weight proposal multipliers must be finite values in [0, 1]")
        frame_id_text = str(frame_id)
        multipliers[frame_id_text] = multiplier
        normalized_rows.append({**row, "frame_id": frame_id_text, "multiplier": multiplier})
    return {
        "enabled": True,
        "path": str(source),
        "artifact_type": payload.get("artifact_type"),
        "method": payload.get("method"),
        "source_integration_audit": payload.get("source_integration_audit"),
        "frame_count": len(multipliers),
        "frame_multipliers": multipliers,
        "rows": normalized_rows,
    }


def _validated_tile_extent(extent: Any) -> dict[str, int]:
    if not isinstance(extent, dict):
        raise ValueError("tile-local policy row is missing extent")
    try:
        x0 = int(extent["x0"])
        y0 = int(extent["y0"])
        x1 = int(extent["x1"])
        y1 = int(extent["y1"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("tile-local policy extent must contain integer x0, y0, x1, y1") from exc
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
        raise ValueError("tile-local policy extent must be a positive rectangle")
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _load_tile_local_policy_replay(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "enabled": False,
            "path": None,
            "applied": False,
            "application_status": "disabled",
            "target_frame_ids": [],
            "tiles": [],
            "tile_count": 0,
            "target_frame_count": 0,
        }
    source = Path(path)
    payload = read_json(source)
    if payload.get("artifact_type") != "tile_local_policy_replay":
        raise ValueError("resident tile-local policy replay must be a tile_local_policy_replay artifact")
    target_group = str(payload.get("target_group") or "")
    if target_group not in {"focus", "control"}:
        raise ValueError("tile-local policy replay target_group must be focus or control")
    target_frame_ids_raw = payload.get("target_frame_ids")
    if not isinstance(target_frame_ids_raw, list):
        raise ValueError("tile-local policy replay must contain target_frame_ids")
    target_frame_ids = [str(value) for value in target_frame_ids_raw]
    tiles_raw = payload.get("tiles")
    if not isinstance(tiles_raw, list) or not tiles_raw:
        raise ValueError("tile-local policy replay must contain at least one tile")
    tiles: list[dict[str, Any]] = []
    for row in tiles_raw:
        if not isinstance(row, dict):
            continue
        tile_index = int(row.get("tile_index"))
        multiplier = float(row.get("multiplier", 1.0))
        if not np.isfinite(multiplier) or multiplier < 0.0:
            raise ValueError("tile-local policy replay multipliers must be finite non-negative values")
        extent = _validated_tile_extent(row.get("extent"))
        tiles.append(
            {
                "tile_index": tile_index,
                "extent": extent,
                "target_group": str(row.get("target_group") or target_group),
                "action": row.get("action"),
                "multiplier": multiplier,
                "clamped": bool(row.get("clamped")),
                "selected_frame_row_count": int(row.get("selected_frame_row_count") or 0),
                "canonical_delta_contribution_adu": _finite_float_or_none(
                    row.get("canonical_delta_contribution_adu")
                ),
                "signed_residual_reference_units_before": _finite_float_or_none(
                    row.get("signed_residual_reference_units_before")
                ),
                "signed_residual_reference_units_after": _finite_float_or_none(
                    row.get("signed_residual_reference_units_after")
                ),
                "moves_toward_reference": row.get("moves_toward_reference"),
            }
        )
    if not tiles:
        raise ValueError("tile-local policy replay contained no usable tile rows")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "enabled": True,
        "path": str(source),
        "artifact_type": payload.get("artifact_type"),
        "target_group": target_group,
        "residual_stat": payload.get("residual_stat"),
        "target_frame_ids": target_frame_ids,
        "target_frame_count": len(target_frame_ids),
        "tile_count": len(tiles),
        "tiles": tiles,
        "summary": {
            "recommendation": summary.get("recommendation"),
            "known_direction_tiles": int(summary.get("known_direction_tiles") or 0),
            "moves_toward_reference": int(summary.get("moves_toward_reference") or 0),
            "moves_away_from_reference": int(summary.get("moves_away_from_reference") or 0),
            "boost_tiles": int(summary.get("boost_tiles") or 0),
            "downweight_tiles": int(summary.get("downweight_tiles") or 0),
            "hold_tiles": int(summary.get("hold_tiles") or 0),
            "clamped_tiles": int(summary.get("clamped_tiles") or 0),
            "mean_abs_residual_before": _finite_float_or_none(summary.get("mean_abs_residual_before")),
            "mean_abs_residual_after": _finite_float_or_none(summary.get("mean_abs_residual_after")),
        },
        "applied": False,
        "application_status": "validated_not_applied",
        "native_requirement": "future resident tile-local integration kernel",
        "limitations": [
            "The replay is validated and recorded only; current resident integration weights remain unchanged.",
            "Boost multipliers are tile-local contribution modifiers, not frame-global weight multipliers.",
        ],
    }


def _tile_rectangles_overlap(left: dict[str, int], right: dict[str, int]) -> bool:
    return max(left["x0"], right["x0"]) < min(left["x1"], right["x1"]) and max(left["y0"], right["y0"]) < min(
        left["y1"],
        right["y1"],
    )


def _tile_local_policy_application_arrays(
    contract: dict[str, Any],
    light_frames: list[dict[str, Any]],
    width: int,
    height: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    if not contract.get("enabled"):
        raise ValueError("resident tile-local policy mode apply_mean requires a replay artifact")
    frame_index_by_id = {str(frame["id"]): index for index, frame in enumerate(light_frames)}
    target_frame_ids = [str(frame_id) for frame_id in contract.get("target_frame_ids", [])]
    missing_ids = [frame_id for frame_id in target_frame_ids if frame_id not in frame_index_by_id]
    present_target_ids = [frame_id for frame_id in target_frame_ids if frame_id in frame_index_by_id]
    if not present_target_ids:
        raise ValueError("resident tile-local policy has no target frame ids in this light group")
    target_mask = np.zeros(len(light_frames), dtype=np.uint8)
    for frame_id in present_target_ids:
        target_mask[frame_index_by_id[frame_id]] = 1
    if not np.any(target_mask):
        raise ValueError("resident tile-local policy must select at least one target frame in this light group")

    tile_rows: list[list[int]] = []
    multipliers: list[float] = []
    extents_seen: list[dict[str, int]] = []
    for tile in contract.get("tiles", []):
        extent = tile.get("extent") if isinstance(tile, dict) else None
        if not isinstance(extent, dict):
            raise ValueError("resident tile-local policy tiles must contain extent dictionaries")
        checked = _validated_tile_extent(extent)
        if checked["x1"] > width or checked["y1"] > height:
            raise ValueError("resident tile-local policy tile extent exceeds the current light group shape")
        for previous in extents_seen:
            if _tile_rectangles_overlap(previous, checked):
                raise ValueError("resident tile-local policy apply_mean requires non-overlapping tile extents")
        extents_seen.append(checked)
        multiplier = float(tile.get("multiplier", 1.0))
        if not np.isfinite(multiplier) or multiplier < 0.0:
            raise ValueError("resident tile-local policy multipliers must be finite non-negative values")
        tile_rows.append([checked["x0"], checked["y0"], checked["x1"], checked["y1"]])
        multipliers.append(multiplier)
    if not tile_rows:
        raise ValueError("resident tile-local policy apply_mean requires at least one tile")

    multiplier_array = np.asarray(multipliers, dtype=np.float32)
    return (
        target_mask,
        np.asarray(tile_rows, dtype=np.int32),
        multiplier_array,
        {
            "native_method": "ResidentCalibratedStack.integrate_tile_local_mean",
            "tile_extent_model": "half_open_xyxy",
            "target_frame_count_applied": int(np.count_nonzero(target_mask)),
            "target_frame_ids_missing": missing_ids,
            "tile_count_applied": int(len(tile_rows)),
            "multiplier_min": float(np.min(multiplier_array)),
            "multiplier_mean": float(np.mean(multiplier_array)),
            "multiplier_max": float(np.max(multiplier_array)),
            "rejection_scope": "stack_dispatch_none_sigma_winsorized",
        },
    )


def _frame_weight_proposal_warning(row: dict[str, Any], multiplier: float) -> list[str]:
    warnings = [
        f"frame_weight_proposal_multiplier={float(multiplier):.6g}",
    ]
    if row.get("method") is not None:
        warnings.append(f"frame_weight_proposal_method={row.get('method')}")
    if row.get("reason") is not None:
        warnings.append(f"frame_weight_proposal_reason={row.get('reason')}")
    return warnings


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
        if star_core_rms is not None:
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


def _annotate_resident_star_core_metrics(
    stack: Any,
    reference_index: int,
    moving_index: int,
    seed_metrics: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    matrices = np.asarray([seed["matrix"] for seed in seed_metrics], dtype=np.float32)
    t0 = perf_counter()
    result = stack.star_core_metrics_candidates_to_reference(reference_index, moving_index, matrices, float(threshold))
    elapsed = perf_counter() - t0
    candidate_metrics = list(result["candidate_metrics"])
    available_pixels = 0
    for item in candidate_metrics:
        local_seed_index = int(item["seed_index"])
        metrics = dict(item["metrics"])
        seed_metrics[local_seed_index]["star_core_metric"] = metrics
        available_pixels = max(available_pixels, int(metrics.get("valid_pixels", 0)))
    return {
        "elapsed_s": elapsed,
        "threshold": float(result["threshold"]),
        "available_pixels": int(available_pixels),
        "sampled_pixels": int(result["sampled_pixels"]),
        "candidate_count": int(result["candidate_count"]),
        "model": str(result["model"]),
    }


def _group_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(group["group_id"]): group for group in plan.get("groups", [])}


def _find_matching_bias_for_group(
    target_group: dict[str, Any] | None,
    groups: dict[str, dict[str, Any]],
) -> str | None:
    if target_group is None:
        return None
    for group_id, group in groups.items():
        if group.get("group_type") != "bias":
            continue
        if (
            group.get("gain") == target_group.get("gain")
            and group.get("offset") == target_group.get("offset")
            and group.get("binning") == target_group.get("binning")
            and group.get("shape") == target_group.get("shape")
        ):
            return group_id
    return None


def _records_for_group(
    group_id: str | None,
    frames: dict[str, dict[str, Any]],
    groups: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if group_id is None or group_id not in groups:
        return []
    return [frames[frame_id] for frame_id in groups[group_id].get("frames", []) if frame_id in frames]


def _light_calibration_groups(plan: dict[str, Any]) -> dict[str, dict[str, str | None]]:
    by_frame: dict[str, dict[str, str | None]] = {}
    for light_plan in plan.get("light_plans", []):
        for frame_id in light_plan.get("frames", []):
            by_frame[str(frame_id)] = {
                "bias_group": light_plan.get("matching_bias_group"),
                "dark_group": light_plan.get("matching_dark_group"),
                "flat_group": light_plan.get("matching_flat_group"),
            }
    return by_frame


def _master_set_cache_key(
    filter_name: str | None,
    height: int,
    width: int,
    bias_group: str | None,
    dark_group: str | None,
    flat_group: str | None,
) -> str:
    return (
        f"{_safe_filter_name(filter_name)}_{width}x{height}_"
        f"bias-{bias_group or 'none'}_dark-{dark_group or 'none'}_flat-{flat_group or 'none'}"
    )


def _record_cache_token(record: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(record.get("path") or ""))
    stat: dict[str, Any]
    try:
        info = path.stat()
        stat = {"size": int(info.st_size), "mtime_ns": int(info.st_mtime_ns)}
    except OSError:
        stat = {"missing": True}
    return {
        "id": record.get("id"),
        "path": str(path),
        "exposure_s": record.get("exposure_s"),
        "gain": record.get("gain"),
        "offset": record.get("offset"),
        "temperature_c": record.get("temperature_c"),
        "width": record.get("width"),
        "height": record.get("height"),
        **stat,
    }


def _master_cache_fingerprint(
    *,
    filter_name: str | None,
    height: int,
    width: int,
    bias_group: str | None,
    dark_group: str | None,
    flat_group: str | None,
    flat_bias_group: str | None,
    bias_records: list[dict[str, Any]],
    dark_records: list[dict[str, Any]],
    flat_records: list[dict[str, Any]],
    flat_bias_records: list[dict[str, Any]],
    policy: CalibrationPolicy,
) -> str:
    payload = {
        "schema_version": 2,
        "builder": _RESIDENT_MASTER_CACHE_BUILDER,
        "filter": filter_name,
        "shape": {"height": int(height), "width": int(width)},
        "groups": {
            "bias": bias_group,
            "dark": dark_group,
            "flat": flat_group,
            "flat_bias": flat_bias_group,
        },
        "policy": asdict(policy),
        "records": {
            "bias": [_record_cache_token(record) for record in bias_records],
            "dark": [_record_cache_token(record) for record in dark_records],
            "flat": [_record_cache_token(record) for record in flat_records],
            "flat_bias": [_record_cache_token(record) for record in flat_bias_records],
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _default_shared_resident_master_cache_dir(run: Path) -> Path:
    return run.parent / "resident_master_cache"


def _resolve_resident_master_cache_policy(
    run: Path,
    master_cache_dir: str | Path | None,
    policy: str,
) -> tuple[Path | None, dict[str, Any]]:
    if policy not in {"auto", "shared", "run"}:
        raise ValueError("resident_master_cache_policy must be auto, shared, or run")
    if master_cache_dir is not None:
        cache_dir = Path(master_cache_dir)
        return cache_dir, {
            "requested": policy,
            "effective": "shared",
            "source": "explicit_dir",
            "dir": str(cache_dir),
        }
    if policy in {"auto", "shared"}:
        cache_dir = _default_shared_resident_master_cache_dir(run)
        return cache_dir, {
            "requested": policy,
            "effective": "shared",
            "source": "output_parent_default",
            "dir": str(cache_dir),
        }
    return None, {
        "requested": policy,
        "effective": "run",
        "source": "policy_run",
        "dir": None,
    }


def _resident_master_cache_root(run: Path, master_cache_dir: str | Path | None) -> tuple[Path, str]:
    if master_cache_dir is None:
        return run / "calib_cache" / "resident_masters", "run"
    return Path(master_cache_dir), "shared"


def _master_cache_paths(cache: Path, key: str) -> dict[str, Path]:
    return {
        "bias": cache / f"{key}_master_bias.npy",
        "dark": cache / f"{key}_master_dark.npy",
        "flat": cache / f"{key}_master_flat.npy",
        "stats": cache / f"{key}_master_stats.json",
    }


def _load_cached_resident_master(path: Path) -> np.ndarray:
    return np.load(path, mmap_mode="r")


def _cached_master_files_complete(paths: dict[str, Path], stats: dict[str, Any]) -> bool:
    return (
        (int(stats.get("bias_count") or 0) <= 0 or paths["bias"].exists())
        and (int(stats.get("dark_count") or 0) <= 0 or paths["dark"].exists())
        and (int(stats.get("flat_count") or 0) <= 0 or paths["flat"].exists())
    )


def _resident_master_cache_write_files(
    paths: dict[str, Path],
    stats: dict[str, Any],
    master_bias: np.ndarray | None,
    master_dark: np.ndarray | None,
    master_flat: np.ndarray | None,
) -> dict[str, Any]:
    start = perf_counter()
    written_files: list[dict[str, Any]] = []
    for kind, array in (
        ("bias", master_bias),
        ("dark", master_dark),
        ("flat", master_flat),
    ):
        if array is None:
            continue
        path = paths[kind]
        np.save(path, array)
        written_files.append(
            {
                "kind": kind,
                "path": str(path),
                "size_bytes": int(path.stat().st_size) if path.exists() else 0,
            }
        )
    array_elapsed = perf_counter() - start
    stats_path = paths["stats"]
    stats_to_write = {
        **stats,
        "cache_write_mode": stats.get("cache_write_mode", "synchronous"),
        "cache_write_state": "completed",
        "cache_write_array_elapsed_s": float(array_elapsed),
        "cache_write_required_before_artifact": True,
        "cache_write_file_count": len(written_files) + 1,
        "cache_write_files": written_files,
    }
    write_json(stats_path, stats_to_write)
    elapsed = perf_counter() - start
    stats_size_bytes = int(stats_path.stat().st_size) if stats_path.exists() else 0
    total_bytes = stats_size_bytes + sum(int(item["size_bytes"]) for item in written_files)
    return {
        "cache_write_state": "completed",
        "cache_write_elapsed_s": float(elapsed),
        "cache_write_array_elapsed_s": float(array_elapsed),
        "cache_write_required_before_artifact": True,
        "cache_write_file_count": len(written_files) + 1,
        "cache_write_total_bytes": int(total_bytes),
        "cache_write_files": [
            *written_files,
            {
                "kind": "stats",
                "path": str(stats_path),
                "size_bytes": stats_size_bytes,
            },
        ],
    }


class _ResidentMasterCacheWriteQueue:
    """Single-writer queue for overlapping master-cache persistence with light work."""

    def __init__(self, *, max_workers: int = 1) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="glass-master-cache-writer",
        )
        self._pending: list[tuple[Future[dict[str, Any]], dict[str, Any]]] = []
        self._submitted_count = 0
        self._completed_count = 0
        self._failed_count = 0
        self._write_elapsed_s = 0.0
        self._written_bytes = 0
        self._shutdown = False

    def submit(
        self,
        *,
        paths: dict[str, Path],
        stats: dict[str, Any],
        master_bias: np.ndarray | None,
        master_dark: np.ndarray | None,
        master_flat: np.ndarray | None,
    ) -> None:
        if self._shutdown:
            raise RuntimeError("resident master-cache writer is already shut down")
        stats.update(
            {
                "cache_write_mode": "async_background",
                "cache_write_state": "scheduled",
                "cache_write_required_before_artifact": True,
            }
        )
        future = self._executor.submit(
            _resident_master_cache_write_files,
            dict(paths),
            dict(stats),
            master_bias,
            master_dark,
            master_flat,
        )
        self._pending.append((future, stats))
        self._submitted_count += 1

    def wait_all(self) -> dict[str, Any]:
        wait_start = perf_counter()
        errors: list[str] = []
        for future, stats in list(self._pending):
            try:
                result = future.result()
            except Exception as exc:  # pragma: no cover - exercised through raised run failure
                self._failed_count += 1
                stats.update(
                    {
                        "cache_write_state": "failed",
                        "cache_write_error": f"{type(exc).__name__}: {exc}",
                    }
                )
                errors.append(f"{type(exc).__name__}: {exc}")
            else:
                self._completed_count += 1
                self._write_elapsed_s += float(result.get("cache_write_elapsed_s") or 0.0)
                self._written_bytes += int(result.get("cache_write_total_bytes") or 0)
                stats.update(result)
        self._pending.clear()
        wait_elapsed = perf_counter() - wait_start
        summary = {
            "enabled": True,
            "mode": "async_background",
            "submitted_count": int(self._submitted_count),
            "completed_count": int(self._completed_count),
            "failed_count": int(self._failed_count),
            "pending_count": len(self._pending),
            "wait_elapsed_s": float(wait_elapsed),
            "write_elapsed_s_total": float(self._write_elapsed_s),
            "written_bytes": int(self._written_bytes),
        }
        if errors:
            raise RuntimeError("resident master-cache async write failed: " + "; ".join(errors))
        return summary

    def shutdown(self) -> None:
        if not self._shutdown:
            self._executor.shutdown(wait=True)
            self._shutdown = True


class _ResidentMasterFitsImageSource(FitsImageSource):
    __slots__ = ("_last_tile", "_last_window_key")
    mask_from_finite_only = True

    def __enter__(self) -> "_ResidentMasterFitsImageSource":
        super().__enter__()
        self._last_tile = None
        self._last_window_key = None
        return self

    @staticmethod
    def _window_key(window: Any) -> tuple[int, int, int, int]:
        return (int(window.y0), int(window.y1), int(window.x0), int(window.x1))

    def read_tile(self, window: Any, dtype: Any = np.float32) -> np.ndarray:
        tile = super().read_tile(window, dtype=dtype)
        self._last_window_key = self._window_key(window)
        self._last_tile = np.asarray(tile, dtype=np.float32)
        return tile

    def read_mask_tile(self, window: Any) -> DQMask:
        key = self._window_key(window)
        if getattr(self, "_last_window_key", None) == key and getattr(self, "_last_tile", None) is not None:
            tile = self._last_tile
        else:
            tile = super().read_tile(window, dtype=np.float32)
            self._last_window_key = key
            self._last_tile = np.asarray(tile, dtype=np.float32)
        mask = DQMask.empty(window.shape)
        invalid = ~np.isfinite(tile)
        if np.any(invalid):
            mask.mark(DQFlag.NO_DATA, invalid)
        return mask


def _resident_master_rejection_policy(policy: CalibrationPolicy) -> RejectionPolicy:
    return RejectionPolicy(
        method=policy.master_rejection,  # type: ignore[arg-type]
        iterations=policy.master_rejection_iterations,
        low_sigma=policy.master_rejection_low_sigma,
        high_sigma=policy.master_rejection_high_sigma,
        min_samples=policy.master_rejection_min_samples,
        max_reject_fraction=policy.master_rejection_max_fraction,
    )


def _resident_master_uses_rejection(policy: CalibrationPolicy) -> bool:
    rejection = _resident_master_rejection_policy(policy)
    return rejection.method != "none" and rejection.iterations > 0


def _resident_master_stack_request(
    frame_ids: tuple[str, ...],
    policy: CalibrationPolicy,
    *,
    source_kind: str,
    metadata: dict[str, Any] | None = None,
) -> StackRequest:
    request_metadata = {
        "stage": "resident_master_cache",
        "source_kind": source_kind,
    }
    if metadata:
        request_metadata.update(metadata)
    return StackRequest(
        frame_ids=frame_ids,
        source_kind=source_kind,
        combine=CombinePolicy(method="mean", accumulator_dtype="float64"),
        rejection=_resident_master_rejection_policy(policy),
        output_maps=OutputMapPolicy(
            coverage=False,
            weight=False,
            variance=False,
            low_rejection=False,
            high_rejection=False,
            dq=False,
        ),
        metadata=request_metadata,
    )


def _resident_master_cuda_mean_available() -> tuple[bool, str]:
    try:
        import glass_cuda
    except Exception as exc:
        return False, f"glass_cuda_import_failed:{type(exc).__name__}:{exc}"
    try:
        if not bool(glass_cuda.cuda_available()):
            return False, "glass_cuda_unavailable"
        glass_cuda.get_device_info(0)
    except Exception as exc:
        return False, f"glass_cuda_device_unavailable:{type(exc).__name__}:{exc}"
    if not hasattr(glass_cuda, "ResidentCalibratedStack"):
        return False, "resident_calibrated_stack_wrapper_unavailable"
    return True, ""


def _resident_master_cuda_hardened_winsorized_available() -> tuple[bool, str]:
    available, reason = _resident_master_cuda_mean_available()
    if not available:
        return available, reason
    try:
        import glass_cuda
    except Exception as exc:
        return False, f"glass_cuda_import_failed:{type(exc).__name__}:{exc}"
    stack_cls = getattr(glass_cuda, "ResidentCalibratedStack", None)
    if stack_cls is None:
        return False, "resident_calibrated_stack_wrapper_unavailable"
    if not hasattr(stack_cls, "integrate_hardened_winsorized_sigma_timed"):
        return False, "resident_hardened_winsorized_method_unavailable"
    return True, ""


def _resident_master_cuda_hardened_winsorized_eligible(
    policy: CalibrationPolicy,
    frame_count: int,
) -> tuple[bool, str]:
    rejection = _resident_master_rejection_policy(policy)
    if rejection.method != "winsorized_sigma" or rejection.iterations <= 0:
        return False, "resident_hardened_winsorized_requires_winsorized_sigma_rejection"
    if rejection.iterations != 1:
        return False, "resident_hardened_winsorized_supports_one_iteration_only"
    if frame_count > RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT:
        return False, (
            "resident_hardened_winsorized_frame_count_exceeds_limit:"
            f"{frame_count}>{RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT}"
        )
    if rejection.low_sigma <= 0.0 or rejection.high_sigma <= 0.0:
        return False, "resident_hardened_winsorized_requires_positive_sigma_thresholds"
    return True, ""


def _resident_master_raw_u16_eligible(specs: list[Any], stack: Any) -> tuple[bool, str]:
    method = "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed"
    if not hasattr(stack, method):
        return False, "resident_raw_u16_method_unavailable"
    for index, spec in enumerate(specs):
        if int(spec.bitpix) != 16:
            return False, f"frame_{index}_bitpix_not_16:{spec.bitpix}"
        if float(spec.bscale) != 1.0:
            return False, f"frame_{index}_bscale_not_1:{spec.bscale:g}"
        if float(spec.bzero) != 32768.0:
            return False, f"frame_{index}_bzero_not_32768:{spec.bzero:g}"
        if spec.blank is not None:
            return False, f"frame_{index}_blank_present"
    return True, ""


def _stack_engine_mean_no_rejection_provenance(
    *,
    input_sample_total: int,
    input_valid_sample_total: int,
    input_invalid_sample_total: int,
    input_nonfinite_sample_total: int,
    valid_total: int,
    coverage_zero_pixel_total: int,
    execution_path: str,
    rejection: RejectionPolicy,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "input_samples": int(input_sample_total),
        "input_valid_samples_before_rejection": int(input_valid_sample_total),
        "input_invalid_samples_before_rejection": int(input_invalid_sample_total),
        "input_flagged_samples": 0,
        "input_nonfinite_samples": int(input_nonfinite_sample_total),
        "input_dq_flag_counts": {flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID},
        "valid_samples_after_rejection": int(valid_total),
        "low_rejected_samples": 0,
        "high_rejected_samples": 0,
        "rejected_samples": 0,
        "rejection_policy": rejection_policy_provenance(rejection),
        "output_coverage_zero_pixels": int(coverage_zero_pixel_total),
        "output_low_rejected_pixels": 0,
        "output_high_rejected_pixels": 0,
        "output_dq_summary": None,
        "semantics": (
            "Resident master-cache mean construction treats non-finite source "
            "samples as invalid input samples before rejection. The resident CUDA "
            "mean kernel skips non-finite values and records sample-accounting "
            "closure through StackEngine-compatible provenance."
        ),
        "execution_path": execution_path,
    }


def _stack_resident_master_array_with_resident_cuda_mean(
    paths: list[Path],
    policy: CalibrationPolicy,
    *,
    source_kind: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not paths:
        raise ValueError("cannot stack an empty resident master frame list")
    import glass_cuda

    specs = [simple_fits_image_spec(path) for path in paths]
    height, width = specs[0].shape
    for spec in specs[1:]:
        if spec.shape != (height, width):
            raise ValueError(f"resident master {source_kind} shape mismatch: {spec.shape} != {(height, width)}")

    request = _resident_master_stack_request(
        tuple(f"{source_kind}-{index}" for index in range(len(paths))),
        policy,
        source_kind=source_kind,
        metadata={"resident_cuda_mean_fast_path": True},
    )
    total_start = perf_counter()
    allocate_start = perf_counter()
    stack = glass_cuda.ResidentCalibratedStack(len(paths), height, width)
    allocate_s = perf_counter() - allocate_start

    per_frame_read_s: list[float] = []
    per_frame_upload_s: list[float] = []
    per_frame_nonfinite: list[int] = []
    fits_backends: list[str] = []
    fits_native_file_read_s: list[float] = []
    fits_native_decode_s: list[float] = []
    fits_native_total_s: list[float] = []
    fits_native_bytes_read = 0
    input_nonfinite_sample_total = 0
    pixel_count = int(height) * int(width)
    raw_u16_enabled, raw_u16_fallback_reason = _resident_master_raw_u16_eligible(specs, stack)
    raw_u16_timing: dict[str, Any] | None = None
    raw_h2d_bytes = 0
    raw_float32_host_bytes_avoided = 0
    host_buffer_bytes = 0
    source_sample_format = "native_direct_float32_host"
    native_method = "ResidentCalibratedStack.upload_calibrated_frame + integrate_mean"

    if raw_u16_enabled:
        raw_buffers: list[np.ndarray | None] = []
        for path, spec in zip(paths, specs, strict=True):
            read_start = perf_counter()
            raw, profile = read_simple_fits_u16be_raw_timed(path, spec=spec)
            per_frame_read_s.append(perf_counter() - read_start)
            raw_buffers.append(raw)
            fits_backends.append(str(profile.get("fits_reader_backend") or "native_u16be_raw"))
            if "fits_native_file_read_s" in profile:
                fits_native_file_read_s.append(float(profile.get("fits_native_file_read_s", 0.0) or 0.0))
            if "fits_native_decode_s" in profile:
                fits_native_decode_s.append(float(profile.get("fits_native_decode_s", 0.0) or 0.0))
            if "fits_native_total_s" in profile:
                fits_native_total_s.append(float(profile.get("fits_native_total_s", 0.0) or 0.0))
            fits_native_bytes_read += int(profile.get("fits_native_bytes_read", 0) or 0)
            per_frame_nonfinite.append(0)

        released_indices: list[int] = []

        def _release_raw_buffers(indices: Any) -> None:
            for index in indices:
                idx = int(index)
                if 0 <= idx < len(raw_buffers):
                    raw_buffers[idx] = None
                    released_indices.append(idx)

        stream_count = min(_RESIDENT_MASTER_RAW_U16_STREAM_COUNT, len(paths))
        wave_frames = min(_RESIDENT_MASTER_RAW_U16_WAVE_FRAMES, stream_count)
        upload_start = perf_counter()
        raw_u16_timing = stack.calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed(
            list(range(len(paths))),
            raw_buffers,
            np.ones(len(paths), dtype=np.float32),
            np.full(len(paths), np.nan, dtype=np.float32),
            stream_count,
            wave_frames,
            _release_raw_buffers,
            None,
        )
        per_frame_upload_s.append(perf_counter() - upload_start)
        raw_h2d_bytes = int(raw_u16_timing.get("raw_h2d_bytes", 0) or 0)
        raw_float32_host_bytes_avoided = int(raw_u16_timing.get("float32_host_bytes_avoided", 0) or 0)
        host_buffer_bytes = raw_h2d_bytes
        source_sample_format = str(raw_u16_timing.get("source_sample_format", "fits_bitpix16_bzero32768_big_endian"))
        native_method = (
            "ResidentCalibratedStack."
            "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed + integrate_mean"
        )
    else:
        host_buffer = np.empty((height, width), dtype=np.float32)
        host_buffer_bytes = int(host_buffer.nbytes)
        for index, (path, spec) in enumerate(zip(paths, specs, strict=True)):
            read_start = perf_counter()
            frame, profile = read_simple_fits_image_native_direct_timed(path, dtype=np.float32, output=host_buffer)
            per_frame_read_s.append(perf_counter() - read_start)
            fits_backends.append(str(profile.get("fits_reader_backend") or "native_direct_simple"))
            if "fits_native_file_read_s" in profile:
                fits_native_file_read_s.append(float(profile.get("fits_native_file_read_s", 0.0) or 0.0))
            if "fits_native_decode_s" in profile:
                fits_native_decode_s.append(float(profile.get("fits_native_decode_s", 0.0) or 0.0))
            if "fits_native_total_s" in profile:
                fits_native_total_s.append(float(profile.get("fits_native_total_s", 0.0) or 0.0))
            fits_native_bytes_read += int(profile.get("fits_native_bytes_read", 0) or 0)
            if spec.bitpix > 0 and spec.blank is None:
                nonfinite_count = 0
            else:
                nonfinite_count = int(np.count_nonzero(~np.isfinite(frame)))
            per_frame_nonfinite.append(nonfinite_count)
            input_nonfinite_sample_total += nonfinite_count

            upload_start = perf_counter()
            stack.upload_calibrated_frame(index, frame)
            per_frame_upload_s.append(perf_counter() - upload_start)

    integrate_start = perf_counter()
    master, weight_map = stack.integrate_mean()
    integrate_s = perf_counter() - integrate_start
    total_s = perf_counter() - total_start

    valid_total = int(round(float(np.sum(weight_map, dtype=np.float64))))
    input_sample_total = int(len(paths) * pixel_count)
    input_valid_sample_total = input_sample_total - int(input_nonfinite_sample_total)
    coverage_zero_pixel_total = int(np.count_nonzero(np.asarray(weight_map, dtype=np.float32) <= 0.0))
    rejection = _resident_master_rejection_policy(policy)
    execution_path = "resident_cuda_mean_no_rejection"
    metrics: dict[str, Any] = {
        "frame_count": len(paths),
        "width": width,
        "height": height,
        "combine": "mean",
        "rejection": rejection.method,
        "rejection_scale_estimator": rejection_scale_estimator(rejection),
        "valid_samples": valid_total,
        "input_valid_samples": input_valid_sample_total,
        "input_invalid_samples": input_sample_total - input_valid_sample_total,
        "low_rejected": 0,
        "high_rejected": 0,
        "rejected_samples": 0,
        "execution_path": execution_path,
        "tile_size": 0,
        "tile_stack_mode": "stack_engine_cuda_mean",
        "resident_master_cache_builder": "ResidentCalibratedStack.integrate_mean",
        "resident_master_cache_builder_dispatch": "resident_cuda_raw_u16_mean"
        if raw_u16_enabled
        else "resident_cuda_native_direct_mean",
        "native_method": native_method,
        "master_rejection_requested": policy.master_rejection,
        "master_rejection_applied": "none",
        "master_rejection_dispatch_reason": (
            "resident_cuda_mean_builder_preserves_phase1_mean_builder_until_robust_master_stack_is_gpu_or_optimized"
        ),
        "timing_s": {
            "total": float(total_s),
            "resident_stack_allocate": float(allocate_s),
            "fits_read": float(sum(per_frame_read_s)),
            "resident_upload": float(sum(per_frame_upload_s)),
            "resident_raw_u16_h2d_decode_store": float(sum(per_frame_upload_s)) if raw_u16_enabled else 0.0,
            "resident_integrate_mean": float(integrate_s),
        },
        "fits_backend_counts": _value_counts(fits_backends),
        "fits_native_file_read_cumulative_s": _timing_summary(fits_native_file_read_s)["total"],
        "fits_native_decode_cumulative_s": _timing_summary(fits_native_decode_s)["total"],
        "fits_native_total_cumulative_s": _timing_summary(fits_native_total_s)["total"],
        "fits_native_bytes_read": int(fits_native_bytes_read),
        "per_frame_nonfinite_sample_counts": per_frame_nonfinite,
        "source_sample_format": source_sample_format,
        "raw_u16_gpu_decode_enabled": bool(raw_u16_enabled),
        "raw_u16_gpu_decode_fallback_reason": raw_u16_fallback_reason,
        "raw_u16_gpu_decode_timing": raw_u16_timing,
        "raw_h2d_bytes": int(raw_h2d_bytes),
        "raw_float32_host_bytes_avoided": int(raw_float32_host_bytes_avoided),
        "host_buffer_bytes": int(host_buffer_bytes),
        "resident_stack_required_bytes": int(len(paths) * pixel_count * 4),
    }
    provenance = _stack_engine_mean_no_rejection_provenance(
        input_sample_total=input_sample_total,
        input_valid_sample_total=input_valid_sample_total,
        input_invalid_sample_total=input_sample_total - input_valid_sample_total,
        input_nonfinite_sample_total=input_nonfinite_sample_total,
        valid_total=valid_total,
        coverage_zero_pixel_total=coverage_zero_pixel_total,
        execution_path=execution_path,
        rejection=rejection,
    )
    result = StackEngineResult(
        master=np.asarray(master, dtype=np.float32),
        dq_provenance=provenance,
        metrics=metrics,
    )
    result_contract = build_stack_engine_result_contract(result, request=request)
    result.dq_provenance["result_contract"] = result_contract
    result.metrics["result_contract_passed"] = bool(result_contract["passed"])
    result.metrics["dq_provenance"] = result.dq_provenance
    return result.master.astype(np.float32, copy=True), dict(result.metrics)


def _stack_resident_master_array_with_resident_cuda_hardened_winsorized(
    paths: list[Path],
    policy: CalibrationPolicy,
    *,
    source_kind: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not paths:
        raise ValueError("cannot stack an empty resident master frame list")
    eligible, reason = _resident_master_cuda_hardened_winsorized_eligible(policy, len(paths))
    if not eligible:
        raise RuntimeError(reason)
    import glass_cuda

    specs = [simple_fits_image_spec(path) for path in paths]
    height, width = specs[0].shape
    for spec in specs[1:]:
        if spec.shape != (height, width):
            raise ValueError(f"resident master {source_kind} shape mismatch: {spec.shape} != {(height, width)}")

    request = _resident_master_stack_request(
        tuple(f"{source_kind}-{index}" for index in range(len(paths))),
        policy,
        source_kind=source_kind,
        metadata={"resident_cuda_hardened_winsorized_fast_path": True},
    )
    rejection = _resident_master_rejection_policy(policy)
    total_start = perf_counter()
    allocate_start = perf_counter()
    stack = glass_cuda.ResidentCalibratedStack(len(paths), height, width)
    allocate_s = perf_counter() - allocate_start

    per_frame_read_s: list[float] = []
    per_frame_upload_s: list[float] = []
    per_frame_nonfinite: list[int] = []
    fits_backends: list[str] = []
    fits_native_file_read_s: list[float] = []
    fits_native_decode_s: list[float] = []
    fits_native_total_s: list[float] = []
    fits_native_bytes_read = 0
    input_nonfinite_sample_total = 0
    pixel_count = int(height) * int(width)
    raw_u16_enabled, raw_u16_fallback_reason = _resident_master_raw_u16_eligible(specs, stack)
    raw_u16_timing: dict[str, Any] | None = None
    raw_h2d_bytes = 0
    raw_float32_host_bytes_avoided = 0
    host_buffer_bytes = 0
    source_sample_format = "native_direct_float32_host"
    native_method = (
        "ResidentCalibratedStack.upload_calibrated_frame + "
        "integrate_hardened_winsorized_sigma"
    )

    if raw_u16_enabled:
        raw_buffers: list[np.ndarray | None] = []
        for path, spec in zip(paths, specs, strict=True):
            read_start = perf_counter()
            raw, profile = read_simple_fits_u16be_raw_timed(path, spec=spec)
            per_frame_read_s.append(perf_counter() - read_start)
            raw_buffers.append(raw)
            fits_backends.append(str(profile.get("fits_reader_backend") or "native_u16be_raw"))
            if "fits_native_file_read_s" in profile:
                fits_native_file_read_s.append(float(profile.get("fits_native_file_read_s", 0.0) or 0.0))
            if "fits_native_decode_s" in profile:
                fits_native_decode_s.append(float(profile.get("fits_native_decode_s", 0.0) or 0.0))
            if "fits_native_total_s" in profile:
                fits_native_total_s.append(float(profile.get("fits_native_total_s", 0.0) or 0.0))
            fits_native_bytes_read += int(profile.get("fits_native_bytes_read", 0) or 0)
            per_frame_nonfinite.append(0)

        released_indices: list[int] = []

        def _release_raw_buffers(indices: Any) -> None:
            for index in indices:
                idx = int(index)
                if 0 <= idx < len(raw_buffers):
                    raw_buffers[idx] = None
                    released_indices.append(idx)

        stream_count = min(_RESIDENT_MASTER_RAW_U16_STREAM_COUNT, len(paths))
        wave_frames = min(_RESIDENT_MASTER_RAW_U16_WAVE_FRAMES, stream_count)
        upload_start = perf_counter()
        raw_u16_timing = stack.calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed(
            list(range(len(paths))),
            raw_buffers,
            np.ones(len(paths), dtype=np.float32),
            np.full(len(paths), np.nan, dtype=np.float32),
            stream_count,
            wave_frames,
            _release_raw_buffers,
            None,
        )
        per_frame_upload_s.append(perf_counter() - upload_start)
        raw_h2d_bytes = int(raw_u16_timing.get("raw_h2d_bytes", 0) or 0)
        raw_float32_host_bytes_avoided = int(raw_u16_timing.get("float32_host_bytes_avoided", 0) or 0)
        host_buffer_bytes = raw_h2d_bytes
        source_sample_format = str(raw_u16_timing.get("source_sample_format", "fits_bitpix16_bzero32768_big_endian"))
        native_method = (
            "ResidentCalibratedStack."
            "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed + "
            "integrate_hardened_winsorized_sigma"
        )
    else:
        host_buffer = np.empty((height, width), dtype=np.float32)
        host_buffer_bytes = int(host_buffer.nbytes)
        for index, (path, spec) in enumerate(zip(paths, specs, strict=True)):
            read_start = perf_counter()
            frame, profile = read_simple_fits_image_native_direct_timed(path, dtype=np.float32, output=host_buffer)
            per_frame_read_s.append(perf_counter() - read_start)
            fits_backends.append(str(profile.get("fits_reader_backend") or "native_direct_simple"))
            if "fits_native_file_read_s" in profile:
                fits_native_file_read_s.append(float(profile.get("fits_native_file_read_s", 0.0) or 0.0))
            if "fits_native_decode_s" in profile:
                fits_native_decode_s.append(float(profile.get("fits_native_decode_s", 0.0) or 0.0))
            if "fits_native_total_s" in profile:
                fits_native_total_s.append(float(profile.get("fits_native_total_s", 0.0) or 0.0))
            fits_native_bytes_read += int(profile.get("fits_native_bytes_read", 0) or 0)
            if spec.bitpix > 0 and spec.blank is None:
                nonfinite_count = 0
            else:
                nonfinite_count = int(np.count_nonzero(~np.isfinite(frame)))
            per_frame_nonfinite.append(nonfinite_count)
            input_nonfinite_sample_total += nonfinite_count

            upload_start = perf_counter()
            stack.upload_calibrated_frame(index, frame)
            per_frame_upload_s.append(perf_counter() - upload_start)

    integrate_start = perf_counter()
    (
        master,
        weight_map,
        coverage_map,
        low_rejection_map,
        high_rejection_map,
        native_timing,
    ) = stack.integrate_hardened_winsorized_sigma_timed(
        None,
        policy.master_rejection_low_sigma,
        policy.master_rejection_high_sigma,
    )
    integrate_s = perf_counter() - integrate_start
    total_s = perf_counter() - total_start

    coverage_data = np.asarray(coverage_map, dtype=np.float32)
    low_data = np.asarray(low_rejection_map, dtype=np.float32)
    high_data = np.asarray(high_rejection_map, dtype=np.float32)
    input_valid_map = coverage_data + low_data + high_data
    rejected_map = low_data + high_data
    with np.errstate(divide="ignore", invalid="ignore"):
        rejected_fraction = np.divide(
            rejected_map,
            input_valid_map,
            out=np.zeros_like(rejected_map, dtype=np.float32),
            where=input_valid_map > 0.0,
        )
    policy_guard = (
        (input_valid_map > 0.0)
        & (
            (coverage_data < float(policy.master_rejection_min_samples))
            | (rejected_fraction > float(policy.master_rejection_max_fraction))
        )
    )
    policy_guard_pixel_count = int(np.count_nonzero(policy_guard))
    if policy_guard_pixel_count:
        raise RuntimeError(
            "resident_cuda_hardened_winsorized_policy_guard_triggered:"
            f"{policy_guard_pixel_count}_pixels_require_cpu_stack_engine"
        )

    input_sample_total = int(len(paths) * pixel_count)
    input_valid_sample_total = int(round(float(np.sum(input_valid_map, dtype=np.float64))))
    input_invalid_sample_total = max(0, input_sample_total - input_valid_sample_total)
    valid_total = int(round(float(np.sum(coverage_data, dtype=np.float64))))
    low_rejected_total = int(round(float(np.sum(low_data, dtype=np.float64))))
    high_rejected_total = int(round(float(np.sum(high_data, dtype=np.float64))))
    coverage_zero_pixel_total = int(np.count_nonzero(coverage_data <= 0.0))
    low_rejected_pixel_total = int(np.count_nonzero(low_data > 0.0))
    high_rejected_pixel_total = int(np.count_nonzero(high_data > 0.0))
    execution_path = "resident_cuda_hardened_winsorized_sigma"
    metrics: dict[str, Any] = {
        "frame_count": len(paths),
        "width": width,
        "height": height,
        "combine": "mean",
        "rejection": rejection.method,
        "rejection_scale_estimator": rejection_scale_estimator(rejection),
        "valid_samples": valid_total,
        "input_valid_samples": input_valid_sample_total,
        "input_invalid_samples": input_invalid_sample_total,
        "low_rejected": low_rejected_total,
        "high_rejected": high_rejected_total,
        "rejected_samples": low_rejected_total + high_rejected_total,
        "execution_path": execution_path,
        "tile_size": 0,
        "tile_stack_mode": "stack_engine_cuda_hardened_winsorized",
        "resident_master_cache_builder": "ResidentCalibratedStack.integrate_hardened_winsorized_sigma",
        "resident_master_cache_builder_dispatch": "resident_cuda_raw_u16_hardened_winsorized"
        if raw_u16_enabled
        else "resident_cuda_native_direct_hardened_winsorized",
        "native_method": native_method,
        "master_rejection_requested": policy.master_rejection,
        "master_rejection_applied": "winsorized_sigma",
        "master_rejection_dispatch_reason": (
            "resident_master_cache_applied_policy_with_resident_cuda_hardened_winsorized"
        ),
        "resident_winsorized_mode": RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
        "resident_hardened_frame_limit": RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
        "resident_hardened_policy_guard_pixel_count": policy_guard_pixel_count,
        "resident_hardened_policy_guard": {
            "min_samples": int(policy.master_rejection_min_samples),
            "max_reject_fraction": float(policy.master_rejection_max_fraction),
            "triggered_pixels": policy_guard_pixel_count,
        },
        "timing_s": {
            "total": float(total_s),
            "resident_stack_allocate": float(allocate_s),
            "fits_read": float(sum(per_frame_read_s)),
            "resident_upload": float(sum(per_frame_upload_s)),
            "resident_raw_u16_h2d_decode_store": float(sum(per_frame_upload_s)) if raw_u16_enabled else 0.0,
            "resident_integrate_hardened_winsorized": float(integrate_s),
        },
        "native_timing_s": native_timing,
        "fits_backend_counts": _value_counts(fits_backends),
        "fits_native_file_read_cumulative_s": _timing_summary(fits_native_file_read_s)["total"],
        "fits_native_decode_cumulative_s": _timing_summary(fits_native_decode_s)["total"],
        "fits_native_total_cumulative_s": _timing_summary(fits_native_total_s)["total"],
        "fits_native_bytes_read": int(fits_native_bytes_read),
        "per_frame_nonfinite_sample_counts": per_frame_nonfinite,
        "source_sample_format": source_sample_format,
        "raw_u16_gpu_decode_enabled": bool(raw_u16_enabled),
        "raw_u16_gpu_decode_fallback_reason": raw_u16_fallback_reason,
        "raw_u16_gpu_decode_timing": raw_u16_timing,
        "raw_h2d_bytes": int(raw_h2d_bytes),
        "raw_float32_host_bytes_avoided": int(raw_float32_host_bytes_avoided),
        "host_buffer_bytes": int(host_buffer_bytes),
        "resident_stack_required_bytes": int(len(paths) * pixel_count * 4),
    }
    provenance: dict[str, Any] = {
        "schema_version": 1,
        "input_samples": input_sample_total,
        "input_valid_samples_before_rejection": input_valid_sample_total,
        "input_invalid_samples_before_rejection": input_invalid_sample_total,
        "input_flagged_samples": 0,
        "input_nonfinite_samples": int(input_nonfinite_sample_total),
        "input_dq_flag_counts": {flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID},
        "valid_samples_after_rejection": valid_total,
        "low_rejected_samples": low_rejected_total,
        "high_rejected_samples": high_rejected_total,
        "rejected_samples": low_rejected_total + high_rejected_total,
        "rejection_policy": rejection_policy_provenance(rejection),
        "output_coverage_zero_pixels": coverage_zero_pixel_total,
        "output_low_rejected_pixels": low_rejected_pixel_total,
        "output_high_rejected_pixels": high_rejected_pixel_total,
        "output_dq_summary": None,
        "semantics": (
            "Resident master-cache hardened winsorized construction keeps calibration "
            "frames resident on the CUDA device, applies the GLASS winsorized sigma "
            "threshold kernel, and records StackEngine-compatible sample accounting. "
            "A policy guard falls back to CPUStackEngine when the native rejection "
            "maps would violate min-samples or max-reject-fraction constraints."
        ),
        "execution_path": execution_path,
    }
    result = StackEngineResult(
        master=np.asarray(master, dtype=np.float32),
        weight_map=np.asarray(weight_map, dtype=np.float32),
        coverage_map=coverage_data,
        low_rejection_map=low_data,
        high_rejection_map=high_data,
        dq_provenance=provenance,
        metrics=metrics,
    )
    result_contract = build_stack_engine_result_contract(result, request=request)
    result.dq_provenance["result_contract"] = result_contract
    result.metrics["result_contract_passed"] = bool(result_contract["passed"])
    result.metrics["dq_provenance"] = result.dq_provenance
    return result.master.astype(np.float32, copy=True), dict(result.metrics)


def _stack_resident_master_array_with_cpu_stack_engine(
    paths: list[Path],
    policy: CalibrationPolicy,
    *,
    source_kind: str,
    tile_size: int = _RESIDENT_MASTER_STACK_TILE_SIZE,
    fallback_reason: str | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not paths:
        raise ValueError("cannot stack an empty resident master frame list")
    with ExitStack() as stack:
        sources = {
            f"{source_kind}-{index}": stack.enter_context(_ResidentMasterFitsImageSource(path))
            for index, path in enumerate(paths)
        }
        request = _resident_master_stack_request(
            tuple(sources.keys()),
            policy,
            source_kind=source_kind,
            metadata={"full_frame_fast_path": True},
        )
        result = CPUStackEngine(tile_size=tile_size).stack(request, sources)
    metrics: dict[str, Any] = dict(result.metrics)
    metrics["dq_provenance"] = result.dq_provenance
    metrics["tile_size"] = int(tile_size)
    metrics["tile_stack_mode"] = "stack_engine_cpu"
    metrics["resident_master_cache_builder"] = "CPUStackEngine"
    metrics["master_rejection_requested"] = policy.master_rejection
    metrics["master_rejection_applied"] = result.metrics.get("rejection", policy.master_rejection)
    metrics["master_rejection_dispatch_reason"] = (
        "resident_master_cache_applied_policy_with_cpu_stack_engine"
        if _resident_master_uses_rejection(policy)
        else "resident_master_cache_no_rejection_policy_uses_cpu_stack_engine"
    )
    metrics["resident_master_cache_builder_dispatch"] = (
        "cpu_stack_engine_tiled_rejection"
        if _resident_master_uses_rejection(policy)
        else "cpu_stack_engine_full_frame"
    )
    metrics["stack_engine_fallback_reason"] = fallback_reason
    return result.master.astype(np.float32, copy=True), metrics


def _stack_resident_master_array_with_engine(
    paths: list[Path],
    policy: CalibrationPolicy,
    *,
    source_kind: str,
    tile_size: int = _RESIDENT_MASTER_STACK_TILE_SIZE,
) -> tuple[np.ndarray, dict[str, Any]]:
    fallback_reason: str | None = None
    if _resident_master_uses_rejection(policy):
        eligible, ineligible_reason = _resident_master_cuda_hardened_winsorized_eligible(policy, len(paths))
        if eligible:
            cuda_available, unavailable_reason = _resident_master_cuda_hardened_winsorized_available()
            if cuda_available:
                try:
                    return _stack_resident_master_array_with_resident_cuda_hardened_winsorized(
                        paths,
                        policy,
                        source_kind=source_kind,
                    )
                except (FastFitsUnsupported, RuntimeError, ValueError) as exc:
                    fallback_reason = (
                        "resident_cuda_hardened_winsorized_unavailable:"
                        f"{type(exc).__name__}:{exc}"
                    )
            else:
                fallback_reason = unavailable_reason
        else:
            fallback_reason = ineligible_reason
    else:
        cuda_available, unavailable_reason = _resident_master_cuda_mean_available()
        if cuda_available:
            try:
                return _stack_resident_master_array_with_resident_cuda_mean(
                    paths,
                    policy,
                    source_kind=source_kind,
                )
            except (FastFitsUnsupported, RuntimeError, ValueError) as exc:
                fallback_reason = f"resident_cuda_mean_unavailable:{type(exc).__name__}:{exc}"
        else:
            fallback_reason = unavailable_reason
    return _stack_resident_master_array_with_cpu_stack_engine(
        paths,
        policy,
        source_kind=source_kind,
        tile_size=tile_size,
        fallback_reason=fallback_reason,
    )


def _subtract_resident_master(
    data: np.ndarray,
    subtract: np.ndarray | None,
    *,
    source_kind: str,
) -> np.ndarray:
    if subtract is None:
        return np.asarray(data, dtype=np.float32)
    if data.shape != subtract.shape:
        raise ValueError(f"{source_kind} master subtraction shape mismatch: {data.shape} != {subtract.shape}")
    return (np.asarray(data, dtype=np.float32) - np.asarray(subtract, dtype=np.float32)).astype(np.float32)


def _normalize_resident_master_flat(
    raw_flat: np.ndarray,
    master_bias: np.ndarray | None,
    policy: CalibrationPolicy,
) -> tuple[np.ndarray, dict[str, Any]]:
    data = _subtract_resident_master(raw_flat, master_bias, source_kind="flat")
    norm = float(np.mean(data) if policy.flat_normalization == "mean" else np.median(data))
    if abs(norm) < policy.flat_floor:
        raise ValueError("flat normalization is below flat_floor")
    normalized = np.maximum(
        data / np.float32(norm),
        np.float32(policy.flat_floor),
    ).astype(np.float32)
    return normalized, {
        "normalization_stage": "master_after_stack",
        "normalization_method": policy.flat_normalization,
        "normalization_scalar": norm,
        "flat_floor": policy.flat_floor,
    }


def _resident_stack_engine_audit_fields(
    metrics: dict[str, dict[str, Any]],
    *,
    flat_normalization: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provenance = {
        key: value.get("dq_provenance")
        for key, value in metrics.items()
        if isinstance(value, dict) and isinstance(value.get("dq_provenance"), dict)
    }
    summaries = {
        key: dq_provenance_summary_from_stack_engine(
            value if isinstance(value, dict) else None,
            stage="master_calibration",
            item=f"resident_{key}",
            engine=str(metrics.get(key, {}).get("tile_stack_mode") or "stack_engine_cpu"),
        )
        for key, value in provenance.items()
    }
    tile_stack_modes = sorted(
        {
            str(value.get("tile_stack_mode") or "stack_engine_cpu")
            for value in metrics.values()
            if isinstance(value, dict)
        }
    )
    tile_sizes = sorted(
        {
            int(value.get("tile_size"))
            for value in metrics.values()
            if isinstance(value, dict) and value.get("tile_size") is not None
        }
    )
    fallback_reasons = sorted(
        {
            str(value.get("stack_engine_fallback_reason"))
            for value in metrics.values()
            if isinstance(value, dict) and value.get("stack_engine_fallback_reason")
        }
    )
    fields: dict[str, Any] = {
        "tile_stack_mode": tile_stack_modes[0] if len(tile_stack_modes) == 1 else "mixed_stack_engine",
        "tile_stack_modes": tile_stack_modes,
        "stack_engine_enabled": True,
        "stack_engine_fallback_reason": "; ".join(fallback_reasons) if fallback_reasons else None,
        "stack_engine_tile_size": tile_sizes[0] if len(tile_sizes) == 1 else _RESIDENT_MASTER_STACK_TILE_SIZE,
        "stack_engine_metrics": metrics,
        "stack_engine_dq_provenance": provenance,
        "dq_provenance_summary": summaries,
    }
    if flat_normalization is not None:
        fields["flat_normalization"] = flat_normalization
    return fields


def _resident_master_metric_summary(
    metrics: dict[str, dict[str, Any]],
    key: str,
    *,
    default: str,
) -> str:
    values = sorted(
        {
            str(value.get(key))
            for value in metrics.values()
            if isinstance(value, dict) and value.get(key) is not None
        }
    )
    if not values:
        return default
    if len(values) == 1:
        return values[0]
    return "; ".join(values)


def _load_or_build_matching_masters(
    run: Path,
    filter_name: str | None,
    height: int,
    width: int,
    frames: dict[str, dict[str, Any]],
    groups: dict[str, dict[str, Any]],
    bias_group: str | None,
    dark_group: str | None,
    flat_group: str | None,
    policy: CalibrationPolicy,
    master_cache_dir: str | Path | None = None,
    cache_write_queue: _ResidentMasterCacheWriteQueue | None = None,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any], float | None]:
    cache, cache_scope = _resident_master_cache_root(run, master_cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    base_key = _master_set_cache_key(filter_name, height, width, bias_group, dark_group, flat_group)
    bias_records = _records_for_group(bias_group, frames, groups)
    dark_records = _records_for_group(dark_group, frames, groups)
    flat_records = _records_for_group(flat_group, frames, groups)
    flat_group_record = groups.get(flat_group or "")
    flat_bias_group = _find_matching_bias_for_group(flat_group_record, groups)
    flat_bias_records = [] if flat_bias_group == bias_group else _records_for_group(flat_bias_group, frames, groups)
    source_frame_ids = {
        "bias_frame_ids": [str(record.get("id")) for record in bias_records],
        "dark_frame_ids": [str(record.get("id")) for record in dark_records],
        "flat_frame_ids": [str(record.get("id")) for record in flat_records],
        "flat_bias_frame_ids": [str(record.get("id")) for record in flat_bias_records],
    }
    fingerprint = _master_cache_fingerprint(
        filter_name=filter_name,
        height=height,
        width=width,
        bias_group=bias_group,
        dark_group=dark_group,
        flat_group=flat_group,
        flat_bias_group=flat_bias_group,
        bias_records=bias_records,
        dark_records=dark_records,
        flat_records=flat_records,
        flat_bias_records=flat_bias_records,
        policy=policy,
    )
    key = f"{base_key}_{fingerprint[:16]}"
    paths = _master_cache_paths(cache, key)
    stats_path = paths["stats"]
    if stats_path.exists():
        stats = read_json(stats_path)
        if stats.get("cache_fingerprint") == fingerprint and _cached_master_files_complete(paths, stats):
            stats = {
                **stats,
                **source_frame_ids,
                "cache_hit": True,
                "cache_scope": cache_scope,
                "cache_dir": str(cache),
                "cache_hit_load_mode": "npy_mmap_readonly",
            }
            master_bias = _load_cached_resident_master(paths["bias"]) if paths["bias"].exists() else None
            master_dark = _load_cached_resident_master(paths["dark"]) if paths["dark"].exists() else None
            master_flat = _load_cached_resident_master(paths["flat"]) if paths["flat"].exists() else None
            return master_bias, master_dark, master_flat, stats, stats.get("dark_exposure_s")

    master_bias = None
    master_metrics: dict[str, dict[str, Any]] = {}
    bias_paths = _paths_for_records(bias_records)
    if bias_paths:
        master_bias, master_metrics["bias"] = _stack_resident_master_array_with_engine(
            bias_paths,
            policy,
            source_kind="bias",
        )

    master_dark = None
    dark_paths = _paths_for_records(dark_records)
    if dark_paths:
        dark_bias = None if policy.master_dark_includes_bias else master_bias
        raw_dark, master_metrics["dark"] = _stack_resident_master_array_with_engine(
            dark_paths,
            policy,
            source_kind="dark",
        )
        master_dark = _subtract_resident_master(raw_dark, dark_bias, source_kind="dark")

    master_flat = None
    flat_normalization: dict[str, Any] | None = None
    flat_paths = _paths_for_records(flat_records)
    if flat_paths:
        flat_bias = master_bias
        if flat_bias_group != bias_group:
            flat_bias_paths = _paths_for_records(flat_bias_records)
            if flat_bias_paths:
                flat_bias, master_metrics["flat_bias"] = _stack_resident_master_array_with_engine(
                    flat_bias_paths,
                    policy,
                    source_kind="flat_bias",
                )
            else:
                flat_bias = None
        raw_flat, master_metrics["flat"] = _stack_resident_master_array_with_engine(
            flat_paths,
            policy,
            source_kind="flat",
        )
        master_flat, flat_normalization = _normalize_resident_master_flat(raw_flat, flat_bias, policy)

    dark_exposures = [
        float(frame["exposure_s"]) for frame in dark_records if frame.get("exposure_s") is not None
    ]
    dark_exposure = float(np.median(dark_exposures)) if dark_exposures else None
    stats = {
        "calibration_group_policy": "planner_matching_groups_per_light",
        "filter": filter_name,
        "shape": {"height": height, "width": width},
        "bias_group": bias_group,
        "dark_group": dark_group,
        "flat_group": flat_group,
        "flat_bias_group": flat_bias_group,
        "bias_count": len(bias_paths),
        "dark_count": len(dark_paths),
        "flat_count": len(flat_paths),
        **source_frame_ids,
        "dark_exposure_s": dark_exposure,
        "bias": None if master_bias is None else image_stats(master_bias),
        "dark": None if master_dark is None else image_stats(master_dark),
        "flat": None if master_flat is None else image_stats(master_flat),
        "master_dark_includes_bias": policy.master_dark_includes_bias,
        "cache_hit": False,
        "cache_scope": cache_scope,
        "cache_dir": str(cache),
        "cache_key": key,
        "cache_base_key": base_key,
        "cache_fingerprint": fingerprint,
        "cache_builder": _RESIDENT_MASTER_CACHE_BUILDER,
        "master_rejection_requested": policy.master_rejection,
        "master_rejection_applied": _resident_master_metric_summary(
            master_metrics,
            "master_rejection_applied",
            default="none" if not _resident_master_uses_rejection(policy) else policy.master_rejection,
        ),
        "master_rejection_dispatch_reason": _resident_master_metric_summary(
            master_metrics,
            "master_rejection_dispatch_reason",
            default=(
                "resident_master_cache_no_rejection_policy"
                if not _resident_master_uses_rejection(policy)
                else "resident_master_cache_applied_policy_with_cpu_stack_engine"
            ),
        ),
        **_resident_stack_engine_audit_fields(
            master_metrics,
            flat_normalization=flat_normalization,
        ),
    }
    if cache_write_queue is None:
        stats.update(
            {
                "cache_write_mode": "synchronous",
                "cache_write_state": "writing",
                "cache_write_required_before_artifact": True,
            }
        )
        stats.update(
            _resident_master_cache_write_files(
                paths,
                dict(stats),
                master_bias,
                master_dark,
                master_flat,
            )
        )
    else:
        cache_write_queue.submit(
            paths=paths,
            stats=stats,
            master_bias=master_bias,
            master_dark=master_dark,
            master_flat=master_flat,
        )
    return master_bias, master_dark, master_flat, stats, dark_exposure


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
        stats = read_json(stats_path)
        if stats.get("stack_engine_enabled") is True:
            stats = {**stats, "cache_hit_load_mode": "npy_mmap_readonly"}
            return (
                _load_cached_resident_master(bias_path),
                _load_cached_resident_master(dark_path),
                _load_cached_resident_master(flat_path),
                stats,
            )

    master_bias = None
    master_metrics: dict[str, dict[str, Any]] = {}
    bias_paths = _paths_for_records(bias_records)
    if bias_paths:
        master_bias, master_metrics["bias"] = _stack_resident_master_array_with_engine(
            bias_paths,
            policy,
            source_kind="bias",
        )

    master_dark = None
    dark_paths = _paths_for_records(dark_records)
    if dark_paths:
        dark_bias = None if policy.master_dark_includes_bias else master_bias
        raw_dark, master_metrics["dark"] = _stack_resident_master_array_with_engine(
            dark_paths,
            policy,
            source_kind="dark",
        )
        master_dark = _subtract_resident_master(raw_dark, dark_bias, source_kind="dark")

    master_flat = None
    flat_normalization: dict[str, Any] | None = None
    flat_paths = _paths_for_records(flat_records)
    if flat_paths:
        raw_flat, master_metrics["flat"] = _stack_resident_master_array_with_engine(
            flat_paths,
            policy,
            source_kind="flat",
        )
        master_flat, flat_normalization = _normalize_resident_master_flat(raw_flat, master_bias, policy)

    stats = {
        "calibration_group_policy": "aggregate_same_shape_filter_for_resident_mode",
        "filter": filter_name,
        "bias_count": len(bias_paths),
        "dark_count": len(dark_paths),
        "flat_count": len(flat_paths),
        "bias_frame_ids": [str(record.get("id")) for record in bias_records],
        "dark_frame_ids": [str(record.get("id")) for record in dark_records],
        "flat_frame_ids": [str(record.get("id")) for record in flat_records],
        "flat_bias_frame_ids": [],
        "bias": None if master_bias is None else image_stats(master_bias),
        "dark": None if master_dark is None else image_stats(master_dark),
        "flat": None if master_flat is None else image_stats(master_flat),
        "master_dark_includes_bias": policy.master_dark_includes_bias,
        "shape": {"height": height, "width": width},
        "cache_builder": _RESIDENT_MASTER_CACHE_BUILDER,
        "master_rejection_requested": policy.master_rejection,
        "master_rejection_applied": _resident_master_metric_summary(
            master_metrics,
            "master_rejection_applied",
            default="none" if not _resident_master_uses_rejection(policy) else policy.master_rejection,
        ),
        "master_rejection_dispatch_reason": _resident_master_metric_summary(
            master_metrics,
            "master_rejection_dispatch_reason",
            default=(
                "resident_master_cache_no_rejection_policy"
                if not _resident_master_uses_rejection(policy)
                else "resident_master_cache_applied_policy_with_cpu_stack_engine"
            ),
        ),
        **_resident_stack_engine_audit_fields(
            master_metrics,
            flat_normalization=flat_normalization,
        ),
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
    integration_rejection_min_samples: int | None = None,
    integration_rejection_max_fraction: float | None = None,
    flat_floor: float | None = None,
    resident_registration: str = "off",
    resident_registration_max_shift: int = 128,
    resident_ncc_sample_stride: int = 1,
    resident_ncc_fallback_score_threshold: float = 0.0,
    resident_subpixel_radius_steps: int = 4,
    resident_subpixel_step: float = 0.25,
    resident_star_threshold: float = 30.0,
    resident_star_max_candidates: int = 64,
    resident_star_tolerance_px: float = 1.0,
    resident_star_grid_cols: int = 0,
    resident_star_grid_rows: int = 0,
    resident_star_catalog_deterministic: bool = False,
    resident_star_prior: str = "none",
    resident_star_prior_radius_px: float = 4.0,
    resident_star_core_preselect_top_k: int = 0,
    resident_triangle_grid_top_per_cell: int | None = None,
    resident_triangle_nms_scan_candidates: int | None = None,
    resident_triangle_nms_min_separation_px: float | None = None,
    resident_triangle_pixel_refine: bool | None = None,
    resident_triangle_pixel_refine_coarse_stride: int | None = None,
    resident_triangle_pixel_refine_final_stride: int | None = None,
    resident_triangle_pixel_refine_fast_coarse: bool = False,
    resident_triangle_centroid_background: str | None = None,
    resident_triangle_min_agreement_score: float | None = None,
    resident_triangle_agreement_rms_scale: float | None = None,
    resident_triangle_agreement_action: str | None = None,
    resident_triangle_agreement_min_weight: float | None = None,
    resident_registration_motion_weighting: str = "off",
    resident_registration_motion_threshold_sigma: float = 16.0,
    resident_registration_motion_min_weight: float = 0.05,
    resident_registration_motion_power: float = 2.0,
    resident_registration_motion_scale_floor_px: float = 1.0,
    resident_registration_quality_gate: str = "auto",
    resident_registration_quality_min_inliers: int = DEFAULT_RESIDENT_REGISTRATION_QUALITY_MIN_INLIERS,
    resident_registration_quality_max_rms_px: float | None = None,
    resident_frame_weight_proposal: str | Path | None = None,
    resident_tile_local_policy_replay: str | Path | None = None,
    resident_tile_local_policy_mode: str = "record",
    resident_registration_results: str | Path | None = None,
    resident_warp_interpolation: str = "bilinear",
    resident_warp_clamping_threshold: float = -1.0,
    resident_warp_batch_dispatch: str = "chunked",
    resident_warp_chunk_capacity_frames: int | None = None,
    resident_integration_dispatch: str = "stack",
    reference_frame_id: str | None = None,
    exclude_frame_ids: list[str] | None = None,
    local_normalization: str = "off",
    resident_local_normalization_mode: str = "global_mean_std",
    resident_local_normalization_tile_size: int = 512,
    resident_prefetch_frames: int = 0,
    resident_prefetch_workers: int = 1,
    resident_prefetch_refill_mode: str = "immediate",
    resident_h2d_mode: str = "pageable",
    resident_calibration_batch_frames: int = 1,
    resident_calibration_streams: int = 1,
    resident_calibration_wave_frames: int = 0,
    resident_calibration_release_mode: str = "sync",
    resident_native_completion_calibration: str = "off",
    resident_native_completion_wave_fill_us: int = 0,
    resident_native_completion_wave_fill_mode: str = "multi_wait",
    resident_native_batch_read: str = "off",
    resident_native_queue_read: str = "off",
    resident_native_queue_drain_mode: str | None = None,
    resident_master_cache_dir: str | Path | None = None,
    resident_master_cache_policy: str = "auto",
    resident_output_maps: str = "audit",
    resident_inline_source_dq: str = "off",
    resident_inline_source_dq_policy: str = "default",
    resident_inline_source_dq_hot_sigma: float = 8.0,
    resident_inline_source_dq_cold_sigma: float = 8.0,
    resident_inline_source_dq_max_invalid_fraction: float = 0.0001,
    resident_inline_source_dq_admission: str = "all",
    resident_winsorized_mode: str = RESIDENT_WINSORIZED_SIGMA_AUTO_MODE,
    resident_fits_read_mode: str = "astropy",
    resident_fits_read_mode_resolution: dict[str, Any] | None = None,
) -> RunState:
    if integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
        raise ValueError("resident CUDA mode supports rejection=none, sigma_clip, or winsorized_sigma")
    if integration_weighting not in {"auto", "none", "simple_snr"}:
        raise ValueError("resident CUDA mode supports integration weighting=none or simple_snr")
    if integration_rejection_min_samples is not None and integration_rejection_min_samples < 1:
        raise ValueError("integration_rejection_min_samples must be at least 1")
    if integration_rejection_max_fraction is not None and (
        integration_rejection_max_fraction < 0.0 or integration_rejection_max_fraction > 1.0
    ):
        raise ValueError("integration_rejection_max_fraction must be between 0 and 1")
    if resident_output_maps not in _RESIDENT_OUTPUT_MAP_POLICIES:
        raise ValueError("resident_output_maps must be audit, science, or minimal")
    if resident_inline_source_dq not in {
        "off",
        "cosmetic",
        "cosmetic_star",
        "cosmetic_cuda",
        "cosmetic_star_cuda",
    }:
        raise ValueError(
            "resident_inline_source_dq must be off, cosmetic, cosmetic_star, "
            "cosmetic_cuda, or cosmetic_star_cuda"
        )
    if resident_inline_source_dq_hot_sigma <= 0.0:
        raise ValueError("resident_inline_source_dq_hot_sigma must be positive")
    if resident_inline_source_dq_cold_sigma <= 0.0:
        raise ValueError("resident_inline_source_dq_cold_sigma must be positive")
    if resident_inline_source_dq_max_invalid_fraction < 0.0:
        raise ValueError("resident_inline_source_dq_max_invalid_fraction must be non-negative")
    if resident_inline_source_dq_admission not in {"all", "active_registered"}:
        raise ValueError("resident_inline_source_dq_admission must be all or active_registered")
    if resident_winsorized_mode not in _RESIDENT_WINSORIZED_MODES:
        raise ValueError("resident_winsorized_mode must be auto, fast_approx, or hardened_cpu_parity")
    if resident_fits_read_mode not in {"auto", "fast", "astropy", "native_direct", "native_u16_gpu"}:
        raise ValueError("resident_fits_read_mode must be auto, fast, astropy, native_direct, or native_u16_gpu")
    if resident_master_cache_policy not in {"auto", "shared", "run"}:
        raise ValueError("resident_master_cache_policy must be auto, shared, or run")
    resident_fits_read_mode_resolution_payload = (
        copy.deepcopy(resident_fits_read_mode_resolution)
        if isinstance(resident_fits_read_mode_resolution, dict)
        else {
            "schema_version": 1,
            "requested": resident_fits_read_mode,
            "effective": resident_fits_read_mode,
            "explicit": True,
            "source": "engine_direct_argument",
            "reason": "resident engine called without CLI default-resolution metadata",
        }
    )
    if resident_registration not in {
        "off",
        "translation_preview",
        "translation_ncc_subpixel",
        "translation_star_catalog",
        "similarity_cuda_catalog",
        "similarity_cuda_triangle",
        "external_matrix",
    }:
        raise ValueError(
            "resident_registration must be off, translation_preview, translation_ncc_subpixel, "
            "translation_star_catalog, similarity_cuda_catalog, similarity_cuda_triangle, or external_matrix"
        )
    if local_normalization not in {"auto", "on", "off"}:
        raise ValueError("local_normalization must be auto, on, or off")
    if resident_local_normalization_mode not in {"global_mean_std", "grid_mean_std"}:
        raise ValueError("resident_local_normalization_mode must be global_mean_std or grid_mean_std")
    if resident_local_normalization_tile_size <= 0:
        raise ValueError("resident_local_normalization_tile_size must be positive")
    if resident_registration_max_shift < 0:
        raise ValueError("resident_registration_max_shift must be non-negative")
    if resident_warp_interpolation not in {"bilinear", "lanczos3"}:
        raise ValueError("resident_warp_interpolation must be bilinear or lanczos3")
    if resident_warp_batch_dispatch not in {"loop", "chunked", "pipelined"}:
        raise ValueError("resident_warp_batch_dispatch must be loop, chunked, or pipelined")
    if resident_warp_chunk_capacity_frames is not None and resident_warp_chunk_capacity_frames <= 0:
        raise ValueError("resident_warp_chunk_capacity_frames must be positive when provided")
    if resident_warp_batch_dispatch == "pipelined" and resident_output_maps != "minimal":
        raise ValueError(
            "resident_warp_batch_dispatch=pipelined is experimental and currently requires "
            "resident_output_maps=minimal; audit/science output maps use the deterministic chunked path"
        )
    if resident_integration_dispatch not in {"stack", "fused_matrix", "auto"}:
        raise ValueError("resident_integration_dispatch must be stack, fused_matrix, or auto")
    resident_warp_chunk_capacity_effective = (
        int(resident_warp_chunk_capacity_frames)
        if resident_warp_batch_dispatch in {"chunked", "pipelined"} and resident_warp_chunk_capacity_frames is not None
        else None
    )
    fused_matrix_registration_modes = _FUSED_MATRIX_REGISTRATION_MODES
    if (
        resident_integration_dispatch == "fused_matrix"
        and resident_registration not in fused_matrix_registration_modes
    ):
        raise ValueError(
            "resident fused_matrix integration currently supports registration=off, "
            "external_matrix, or similarity_cuda_triangle"
        )
    if resident_ncc_sample_stride <= 0:
        raise ValueError("resident_ncc_sample_stride must be positive")
    if resident_ncc_fallback_score_threshold < 0.0 or resident_ncc_fallback_score_threshold > 1.0:
        raise ValueError("resident_ncc_fallback_score_threshold must be in [0, 1]")
    if resident_subpixel_radius_steps < 0:
        raise ValueError("resident_subpixel_radius_steps must be non-negative")
    if resident_subpixel_step <= 0:
        raise ValueError("resident_subpixel_step must be positive")
    if resident_star_max_candidates <= 0:
        raise ValueError("resident_star_max_candidates must be positive")
    if resident_star_tolerance_px < 0:
        raise ValueError("resident_star_tolerance_px must be non-negative")
    if resident_star_prior not in {"none", "ncc", "auto_pierside"}:
        raise ValueError("resident_star_prior must be none, ncc, or auto_pierside")
    if resident_star_prior_radius_px < 0:
        raise ValueError("resident_star_prior_radius_px must be non-negative")
    if resident_star_core_preselect_top_k < 0:
        raise ValueError("resident_star_core_preselect_top_k must be non-negative")
    if resident_triangle_grid_top_per_cell is not None and resident_triangle_grid_top_per_cell <= 0:
        raise ValueError("resident_triangle_grid_top_per_cell must be positive when provided")
    if resident_triangle_nms_scan_candidates is not None and resident_triangle_nms_scan_candidates <= 0:
        raise ValueError("resident_triangle_nms_scan_candidates must be positive when provided")
    if resident_triangle_nms_min_separation_px is not None and resident_triangle_nms_min_separation_px < 0:
        raise ValueError("resident_triangle_nms_min_separation_px must be non-negative when provided")
    if resident_triangle_pixel_refine_coarse_stride is not None and resident_triangle_pixel_refine_coarse_stride <= 0:
        raise ValueError("resident_triangle_pixel_refine_coarse_stride must be positive when provided")
    if resident_triangle_pixel_refine_final_stride is not None and resident_triangle_pixel_refine_final_stride <= 0:
        raise ValueError("resident_triangle_pixel_refine_final_stride must be positive when provided")
    if resident_triangle_min_agreement_score is not None and (
        resident_triangle_min_agreement_score < 0.0 or resident_triangle_min_agreement_score > 1.0
    ):
        raise ValueError("resident_triangle_min_agreement_score must be in [0, 1] when provided")
    if resident_triangle_agreement_rms_scale is not None and resident_triangle_agreement_rms_scale <= 0.0:
        raise ValueError("resident_triangle_agreement_rms_scale must be positive when provided")
    if resident_triangle_agreement_action is not None and resident_triangle_agreement_action not in {
        "fail",
        "downweight",
        "flag",
    }:
        raise ValueError("resident_triangle_agreement_action must be fail, downweight, or flag")
    if resident_triangle_agreement_min_weight is not None and (
        resident_triangle_agreement_min_weight < 0.0 or resident_triangle_agreement_min_weight > 1.0
    ):
        raise ValueError("resident_triangle_agreement_min_weight must be in [0, 1] when provided")
    if resident_registration_motion_weighting not in {"off", "translation_mad"}:
        raise ValueError("resident_registration_motion_weighting must be off or translation_mad")
    if resident_registration_motion_threshold_sigma <= 0.0:
        raise ValueError("resident_registration_motion_threshold_sigma must be positive")
    if resident_registration_motion_min_weight < 0.0 or resident_registration_motion_min_weight > 1.0:
        raise ValueError("resident_registration_motion_min_weight must be in [0, 1]")
    if resident_registration_motion_power <= 0.0:
        raise ValueError("resident_registration_motion_power must be positive")
    if resident_registration_motion_scale_floor_px <= 0.0:
        raise ValueError("resident_registration_motion_scale_floor_px must be positive")
    if resident_registration_quality_gate not in {"auto", "off", "warn", "exclude"}:
        raise ValueError("resident_registration_quality_gate must be auto, off, warn, or exclude")
    if resident_registration_quality_min_inliers < 0:
        raise ValueError("resident_registration_quality_min_inliers must be non-negative")
    if resident_registration_quality_max_rms_px is not None and resident_registration_quality_max_rms_px <= 0.0:
        raise ValueError("resident_registration_quality_max_rms_px must be positive when provided")
    frame_weight_proposal = _load_frame_weight_proposal(resident_frame_weight_proposal)
    tile_local_policy_replay = _load_tile_local_policy_replay(resident_tile_local_policy_replay)
    if resident_tile_local_policy_mode not in {"record", "apply_mean", "apply"}:
        raise ValueError("resident_tile_local_policy_mode must be record, apply_mean, or apply")
    tile_local_policy_replay["requested_mode"] = resident_tile_local_policy_mode
    tile_local_policy_replay["effective_mode"] = "disabled" if not tile_local_policy_replay.get("enabled") else "record"
    if resident_prefetch_frames < 0:
        raise ValueError("resident_prefetch_frames must be non-negative")
    if resident_prefetch_workers <= 0:
        raise ValueError("resident_prefetch_workers must be positive")
    if resident_prefetch_refill_mode not in {"immediate", "queued", "deferred"}:
        raise ValueError("resident_prefetch_refill_mode must be immediate, queued, or deferred")
    if resident_h2d_mode not in {"pageable", "pinned_async", "pinned_ring"}:
        raise ValueError("resident_h2d_mode must be one of: pageable, pinned_async, pinned_ring")
    if resident_h2d_mode == "pinned_ring" and resident_prefetch_frames <= 0:
        raise ValueError("resident_h2d_mode=pinned_ring requires resident_prefetch_frames > 0")
    if resident_calibration_batch_frames <= 0:
        raise ValueError("resident_calibration_batch_frames must be positive")
    if resident_calibration_streams <= 0:
        raise ValueError("resident_calibration_streams must be positive")
    if resident_calibration_wave_frames < 0:
        raise ValueError("resident_calibration_wave_frames must be non-negative")
    if resident_calibration_release_mode not in {"sync", "h2d_event", "auto", "callback_queue"}:
        raise ValueError("resident_calibration_release_mode must be one of: sync, h2d_event, auto, callback_queue")
    if resident_native_completion_calibration not in {"off", "on"}:
        raise ValueError("resident_native_completion_calibration must be off or on")
    if resident_native_completion_wave_fill_us < 0 or resident_native_completion_wave_fill_us > 10000:
        raise ValueError("resident_native_completion_wave_fill_us must be between 0 and 10000")
    if resident_native_completion_wave_fill_mode not in {"multi_wait", "single_wait"}:
        raise ValueError("resident_native_completion_wave_fill_mode must be multi_wait or single_wait")
    if resident_native_batch_read not in {"off", "on"}:
        raise ValueError("resident_native_batch_read must be off or on")
    if resident_native_queue_read not in {"off", "on"}:
        raise ValueError("resident_native_queue_read must be off or on")
    if resident_native_queue_drain_mode is not None and resident_native_queue_drain_mode not in {"thread", "inline"}:
        raise ValueError("resident_native_queue_drain_mode must be thread, inline, or None")
    if (resident_star_grid_cols > 0 or resident_star_grid_rows > 0) and (
        resident_star_grid_cols <= 0 or resident_star_grid_rows <= 0
    ):
        raise ValueError("resident star grid dimensions must both be positive")
    resident_matrix_warp_method = (
        "apply_matrix_lanczos3_frame"
        if resident_warp_interpolation == "lanczos3"
        else "apply_matrix_bilinear_frame"
    )
    resident_track_warp_coverage = resident_output_maps != "minimal"

    cuda_module = _cuda_module_required()
    plan = read_json(plan_path)
    plan_root = Path(plan_path).parent
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    calibration_dq_sidecars, calibration_dq_sidecar_index = _resident_source_dq_sidecars_from_calibration_artifacts(
        plan,
        run=run,
        plan_root=plan_root,
    )
    shared_master_cache_dir, master_cache_policy_record = _resolve_resident_master_cache_policy(
        run,
        resident_master_cache_dir,
        resident_master_cache_policy,
    )
    if shared_master_cache_dir is not None:
        shared_master_cache_dir.mkdir(parents=True, exist_ok=True)
    state = RunState(run_id=run.name or "glass-run", created_at=now_iso(), current_stage="resident_calibration")

    frames = _frame_map(plan)
    groups = _group_map(plan)
    light_calibration_groups = _light_calibration_groups(plan)
    policy = _policy_from_plan(plan)
    if flat_floor is not None:
        if flat_floor <= 0:
            raise ValueError("flat_floor override must be positive")
        policy.flat_floor = float(flat_floor)
    integration_policy = plan.get("integration_policy", {})
    rejection_min_samples = int(
        integration_rejection_min_samples
        if integration_rejection_min_samples is not None
        else integration_policy.get("rejection_min_samples", integration_policy.get("min_samples", 3))
    )
    if integration_rejection_max_fraction is not None:
        rejection_max_fraction = float(integration_rejection_max_fraction)
        rejection_max_fraction_source = "cli_override"
    elif "rejection_max_fraction" in integration_policy:
        rejection_max_fraction = float(integration_policy["rejection_max_fraction"])
        rejection_max_fraction_source = "plan_integration_policy"
    elif "max_reject_fraction" in integration_policy:
        rejection_max_fraction = float(integration_policy["max_reject_fraction"])
        rejection_max_fraction_source = "plan_legacy_integration_policy"
    else:
        rejection_max_fraction = 0.5
        rejection_max_fraction_source = "implicit_default"
    if rejection_min_samples < 1:
        raise ValueError("resolved integration rejection min_samples must be at least 1")
    if rejection_max_fraction < 0.0 or rejection_max_fraction > 1.0:
        raise ValueError("resolved integration rejection max fraction must be between 0 and 1")
    registration_policy = dict(plan.get("registration_policy", {}))
    if resident_triangle_pixel_refine is not None:
        registration_policy["cuda_triangle_pixel_refine"] = bool(resident_triangle_pixel_refine)
    excluded_tokens = {str(item) for item in (exclude_frame_ids or []) if str(item)}
    weighting_mode = (
        str(integration_policy.get("weighting") or "none")
        if integration_weighting == "auto"
        else integration_weighting
    )
    if weighting_mode not in {"none", "simple_snr"}:
        raise ValueError("resident CUDA mode supports resolved integration weighting=none or simple_snr")
    rejection_mode = "none" if integration_rejection == "auto" else integration_rejection
    local_norm_policy = plan.get("local_normalization_policy", {})
    local_norm_enabled = local_normalization == "on" or (
        local_normalization == "auto" and bool(local_norm_policy.get("enabled", False))
    )
    resident_integration_dispatch_requested = resident_integration_dispatch
    resident_integration_dispatch_reason = f"explicit_{resident_integration_dispatch}"
    if resident_integration_dispatch == "auto":
        if (
            rejection_mode == "winsorized_sigma"
            and resident_winsorized_mode
            in {RESIDENT_WINSORIZED_SIGMA_AUTO_MODE, RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE}
            and (
                resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                or resident_output_maps != "minimal"
            )
        ):
            resident_integration_dispatch = "stack"
            resident_integration_dispatch_reason = (
                "auto_stack_winsorized_auto_may_select_hardened"
                if resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_AUTO_MODE
                else "auto_stack_hardened_winsorized_requires_stack"
            )
        elif local_norm_enabled:
            resident_integration_dispatch = "stack"
            resident_integration_dispatch_reason = "auto_stack_local_normalization_enabled"
        elif resident_registration not in fused_matrix_registration_modes:
            resident_integration_dispatch = "stack"
            resident_integration_dispatch_reason = "auto_stack_registration_mode_not_fused_supported"
        elif resident_warp_interpolation != "bilinear":
            resident_integration_dispatch = "stack"
            resident_integration_dispatch_reason = "auto_stack_non_bilinear_matrix_route"
        else:
            resident_integration_dispatch = "fused_matrix"
            resident_integration_dispatch_reason = "auto_fused_bilinear_matrix_route"
    if resident_tile_local_policy_mode in {"apply_mean", "apply"}:
        if not tile_local_policy_replay.get("enabled"):
            raise ValueError("resident_tile_local_policy_mode apply requires --resident-tile-local-policy-replay")
        if resident_tile_local_policy_mode == "apply_mean" and rejection_mode != "none":
            raise ValueError("resident_tile_local_policy_mode=apply_mean currently requires --integration-rejection none")
        if resident_integration_dispatch != "stack":
            raise ValueError("resident_tile_local_policy_mode apply currently requires resident stack integration")
        if (
            rejection_mode == "winsorized_sigma"
            and resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
        ):
            raise ValueError(
                "resident_winsorized_mode=hardened_cpu_parity currently does not support "
                "resident_tile_local_policy_mode apply"
            )
    if (
        rejection_mode == "winsorized_sigma"
        and resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
        and resident_integration_dispatch == "fused_matrix"
    ):
        raise ValueError(
            "resident_winsorized_mode=hardened_cpu_parity requires resident_integration_dispatch=stack"
        )
    low_sigma = float(integration_policy.get("low_sigma", 3.0))
    high_sigma = float(integration_policy.get("high_sigma", 3.0))
    external_registration_path: Path | None = None
    external_registration_by_frame: dict[str, dict[str, Any]] = {}
    external_reference_frame_id: str | None = None
    if resident_registration == "external_matrix":
        external_registration_path = (
            Path(resident_registration_results) if resident_registration_results is not None else run / "registration_results.json"
        )
        if not external_registration_path.exists():
            raise ValueError(f"external resident registration results not found: {external_registration_path}")
        external_registration_payload = read_json(external_registration_path)
        external_registration_by_frame = {
            str(row.get("frame_id")): row for row in _registration_rows(external_registration_payload)
        }
        if not external_registration_by_frame:
            raise ValueError("external resident registration results contain no frame rows")
        if external_registration_payload.get("reference_frame_id") is not None:
            external_reference_frame_id = str(external_registration_payload["reference_frame_id"])
    output_dir = run / "integration"
    output_dir.mkdir(parents=True, exist_ok=True)
    header_cache: dict[tuple[str, str], Any] = {}

    resident_artifacts: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    frame_weights: dict[str, float] = {}
    registration_results: list[RegistrationResult] = []
    registration_quality_decisions_by_frame: dict[str, dict[str, Any]] = {}
    resident_frame_mask_contract_groups: list[dict[str, Any]] = []
    resident_dq_pixel_closure_groups: list[dict[str, Any]] = []
    resident_dq_lifecycle_groups: list[dict[str, Any]] = []
    resident_source_dq_execution_groups: list[dict[str, Any]] = []
    resident_master_cache_groups: list[dict[str, Any]] = []
    resident_master_cache_write_queues: list[_ResidentMasterCacheWriteQueue] = []
    local_norm_groups: list[dict[str, Any]] = []
    tile_local_policy_any_enabled = False
    tile_local_policy_any_applied = False

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
            hardened_winsorized_available, hardened_winsorized_unavailable_reason = (
                _resident_stack_hardened_winsorized_available(cuda_module)
            )
            (
                group_rejection_max_fraction,
                group_rejection_max_fraction_source,
                group_rejection_max_fraction_resolution,
            ) = _resolve_resident_rejection_max_fraction(
                rejection_mode=rejection_mode,
                requested_resident_winsorized_mode=resident_winsorized_mode,
                frame_count=len(light_frames),
                dispatch_mode=resident_integration_dispatch,
                resident_output_maps=resident_output_maps,
                tile_local_policy_mode=resident_tile_local_policy_mode,
                base_max_reject_fraction=rejection_max_fraction,
                base_source=rejection_max_fraction_source,
            )
            resident_winsorized_contract = _resident_winsorized_runtime_contract(
                rejection_mode=rejection_mode,
                resident_winsorized_mode=resident_winsorized_mode,
                frame_count=len(light_frames),
                dispatch_mode=resident_integration_dispatch,
                min_samples=rejection_min_samples,
                max_reject_fraction=group_rejection_max_fraction,
                max_reject_fraction_source=group_rejection_max_fraction_source,
                max_reject_fraction_resolution=group_rejection_max_fraction_resolution,
                hardened_available=hardened_winsorized_available,
                hardened_unavailable_reason=hardened_winsorized_unavailable_reason,
                tile_local_policy_mode=resident_tile_local_policy_mode,
                resident_output_maps=resident_output_maps,
            )
            _validate_resident_winsorized_runtime_contract(resident_winsorized_contract)
            group_resident_winsorized_mode = str(
                resident_winsorized_contract["resident_winsorized_mode"]
            )
            group_tile_local_policy_replay = copy.deepcopy(tile_local_policy_replay)
            tile_local_policy_any_enabled = tile_local_policy_any_enabled or bool(
                group_tile_local_policy_replay.get("enabled")
            )
            master_elapsed = 0.0
            master_stats_sets: dict[str, Any] = {}
            master_cache_write_queue = _ResidentMasterCacheWriteQueue()
            resident_master_cache_write_queues.append(master_cache_write_queue)
            master_cache_async_write_summary: dict[str, Any] = {
                "enabled": True,
                "mode": "async_background",
                "submitted_count": 0,
                "completed_count": 0,
                "failed_count": 0,
                "pending_count": 0,
                "wait_elapsed_s": 0.0,
                "write_elapsed_s_total": 0.0,
                "written_bytes": 0,
            }

            allocate_start = perf_counter()
            stack = cuda_module.ResidentCalibratedStack(len(light_frames), height, width)
            resident_stack = stack
            allocate_elapsed = perf_counter() - allocate_start
            coverage_native_stack = getattr(stack, "_impl", stack)
            resident_warp_coverage_supported = all(
                hasattr(coverage_native_stack, name)
                for name in (
                    "reset_warp_coverage",
                    "accumulate_full_warp_coverage_frame",
                    "warp_coverage_map",
                )
            )
            warped_frame_indices: set[int] = set()
            fused_matrix_deferred_frame_indices: set[int] = set()
            integration_matrices = [translation_matrix(0.0, 0.0) for _ in light_frames]
            if resident_warp_coverage_supported:
                stack.reset_warp_coverage()

            registration_start = perf_counter()
            quality_reference_frame_id, quality_reference_status, quality_reference_path = _quality_reference_frame_id(
                run,
                light_frames,
            )
            use_quality_reference = resident_registration != "off" or local_norm_enabled
            if reference_frame_id:
                selected_reference_frame_id = reference_frame_id
                reference_selection_source = "explicit"
            elif external_reference_frame_id:
                selected_reference_frame_id = external_reference_frame_id
                reference_selection_source = "external_matrix"
            elif quality_reference_frame_id is not None and use_quality_reference:
                selected_reference_frame_id = quality_reference_frame_id
                reference_selection_source = "frame_quality"
            else:
                selected_reference_frame_id = None
                reference_selection_source = "first_light_fallback"
            reference_frame = _find_reference_frame(light_frames, selected_reference_frame_id)
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
            per_frame_read_s: list[float] = []
            per_frame_read_worker_s: list[float] = []
            per_frame_fits_open_s: list[float] = []
            per_frame_fits_materialize_decode_s: list[float] = []
            per_frame_fits_backend: list[str] = []
            per_frame_fits_fallback_reason: list[str] = []
            per_frame_fits_native_file_read_s: list[float] = []
            per_frame_fits_native_decode_s: list[float] = []
            per_frame_fits_native_total_s: list[float] = []
            per_frame_fits_native_bytes_read: list[int] = []
            per_frame_fits_header_cache_hits = 0
            per_frame_calibrate_s: list[float] = []
            per_frame_host_copy_s: list[float] = []
            per_frame_h2d_s: list[float] = []
            per_frame_calibrate_store_s: list[float] = []
            calibration_event_modes: list[str] = []
            per_frame_registration_s = []
            registration_component_s: dict[str, float] = {}
            source_dq_rows: list[dict[str, Any]] = []
            defer_inline_cosmetic_cuda_source_dq = bool(
                resident_inline_source_dq in {"cosmetic_cuda", "cosmetic_star_cuda"}
                and resident_registration != "off"
            )
            deferred_inline_cosmetic_cuda_by_index: dict[int, dict[str, Any]] = {}
            deferred_inline_cosmetic_cuda_stats: dict[str, float | int] = {
                "deferred_frame_count": 0,
                "candidate_frame_count": 0,
                "target_frame_count": 0,
                "applied_frame_count": 0,
                "skipped_admission_frame_count": 0,
                "apply_s": 0.0,
            }

            def _record_inline_cosmetic_cuda_source_dq_item(item: dict[str, Any]) -> None:
                frame_index = int(item["frame_index"])
                if frame_index not in deferred_inline_cosmetic_cuda_by_index:
                    deferred_inline_cosmetic_cuda_stats["deferred_frame_count"] = (
                        int(deferred_inline_cosmetic_cuda_stats["deferred_frame_count"]) + 1
                    )
                deferred_inline_cosmetic_cuda_by_index[frame_index] = {
                    **item,
                    "deferred_until_stage": "resident_registration_complete",
                }

            def _inline_cosmetic_cuda_admission(frame_index: int, frame_id: str) -> tuple[bool, str]:
                if resident_inline_source_dq_admission == "all":
                    return True, "all_frames"
                frame = light_frames[int(frame_index)]
                if _matches_any_token(frame, excluded_tokens):
                    return False, "manual_exclude"
                if int(frame_index) < len(frame_weight_values):
                    weight = float(frame_weight_values[int(frame_index)])
                    if not np.isfinite(weight) or weight <= 0.0:
                        return False, "non_positive_integration_weight"
                registration_status = None
                for result in reversed(registration_results):
                    if str(result.frame_id) == str(frame_id):
                        registration_status = str(result.status)
                        break
                if registration_status is not None and registration_status not in {"ok", "reference"}:
                    return False, f"registration_status:{registration_status}"
                return True, "registered_active"

            def _apply_deferred_inline_cosmetic_cuda_source_dq(
                stack_obj: Any,
                indices: Iterable[int],
                *,
                source: str,
            ) -> None:
                pending_items: list[dict[str, Any]] = []
                for raw_index in indices:
                    frame_index = int(raw_index)
                    item = deferred_inline_cosmetic_cuda_by_index.pop(frame_index, None)
                    if item is not None:
                        pending_items.append(item)
                if not pending_items:
                    return
                target_items: list[dict[str, Any]] = []
                skipped_rows: list[dict[str, Any]] = []
                for item in pending_items:
                    frame_index = int(item["frame_index"])
                    frame_id = str(item["frame_id"])
                    admitted, admission_reason = _inline_cosmetic_cuda_admission(frame_index, frame_id)
                    if admitted:
                        target_items.append(item)
                        continue
                    skipped_rows.append(
                        build_skipped_resident_inline_cosmetic_threshold_row(
                            frame_index=frame_index,
                            frame_id=frame_id,
                            threshold_info=dict(item["threshold_info"]),
                            source=source,
                            admission_policy=resident_inline_source_dq_admission,
                            admission_reason=admission_reason,
                        )
                    )
                deferred_inline_cosmetic_cuda_stats["candidate_frame_count"] = (
                    int(deferred_inline_cosmetic_cuda_stats["candidate_frame_count"]) + len(pending_items)
                )
                deferred_inline_cosmetic_cuda_stats["target_frame_count"] = (
                    int(deferred_inline_cosmetic_cuda_stats["target_frame_count"]) + len(target_items)
                )
                deferred_inline_cosmetic_cuda_stats["skipped_admission_frame_count"] = (
                    int(deferred_inline_cosmetic_cuda_stats["skipped_admission_frame_count"])
                    + len(skipped_rows)
                )
                apply_start = perf_counter()
                rows = (
                    apply_resident_inline_cosmetic_thresholds_batch(
                        stack_obj,
                        items=target_items,
                        source=source,
                        max_invalid_fraction=resident_inline_source_dq_max_invalid_fraction,
                    )
                    if target_items
                    else []
                )
                rows.extend(skipped_rows)
                deferred_inline_cosmetic_cuda_stats["apply_s"] = (
                    float(deferred_inline_cosmetic_cuda_stats["apply_s"]) + perf_counter() - apply_start
                )
                applied_row_count = sum(1 for row in rows if bool(row.get("applied")))
                deferred_inline_cosmetic_cuda_stats["applied_frame_count"] = (
                    int(deferred_inline_cosmetic_cuda_stats["applied_frame_count"]) + applied_row_count
                )
                for row in rows:
                    row["application_order"] = "post_registration_pre_warp"
                    row["registration_catalog_visibility"] = "post_registration_deferred_not_catalog_visible"
                    row["registration_catalog_visible"] = False
                    row["registration_catalog_visibility_required"] = False
                    row["deferred_until_stage"] = "resident_registration_complete"
                    row["deferred_source"] = f"resident_calibrated_input_{resident_inline_source_dq}"
                source_dq_rows.extend(rows)

            registration_during_load_elapsed = 0.0
            gc_elapsed = 0.0
            frame_weight_values: list[float] = []
            agreement_weight_multipliers = [1.0 for _ in light_frames]
            current_master_key: str | None = None
            current_dark_exposure: float | None = None
            prefetch_host_pinned_bytes = 0
            calibration_batch_supported = hasattr(stack, "calibrate_frames_host_async_timed")
            calibration_batch_multistream_supported = hasattr(
                stack, "calibrate_frames_host_async_multistream_timed"
            )
            calibration_h2d_release_supported = bool(
                hasattr(stack, "calibrate_frames_host_async_multistream_h2d_release_timed")
                and hasattr(stack, "finish_pending_calibration_timed")
            )
            calibration_callback_release_supported = bool(
                hasattr(stack, "calibrate_frames_host_async_multistream_callback_release_timed")
            )
            raw_u16_gpu_decode_supported = bool(
                hasattr(
                    stack,
                    "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed",
                )
            )
            calibration_batch_enabled = bool(
                resident_h2d_mode == "pinned_ring"
                and resident_registration != "translation_preview"
                and resident_calibration_batch_frames > 1
                and calibration_batch_supported
            )
            calibration_wave_requested_effective_frames = int(resident_calibration_batch_frames)
            calibration_wave_effective_source = "batch_frame_count"
            if calibration_batch_enabled and resident_calibration_wave_frames > 0:
                calibration_wave_requested_effective_frames = min(
                    int(resident_calibration_batch_frames),
                    int(resident_calibration_wave_frames),
                )
                calibration_wave_effective_source = "requested_wave_frames"
            calibration_wave_effective_frames = int(calibration_wave_requested_effective_frames)
            calibration_wave_lane_guard_applied = False
            if (
                calibration_batch_enabled
                and resident_calibration_streams > 0
                and calibration_wave_effective_frames > int(resident_calibration_streams)
            ):
                calibration_wave_effective_frames = int(resident_calibration_streams)
                calibration_wave_effective_source = f"{calibration_wave_effective_source}_clamped_to_stream_count"
                calibration_wave_lane_guard_applied = True
            calibration_wave_enabled = bool(
                calibration_batch_enabled
                and resident_calibration_wave_frames > 0
                and calibration_wave_effective_frames < int(resident_calibration_batch_frames)
            )
            calibration_batch_multistream_enabled = bool(
                calibration_batch_enabled
                and resident_calibration_streams > 1
                and calibration_batch_multistream_supported
            )
            calibration_h2d_release_capable = bool(
                calibration_batch_multistream_enabled
                and calibration_h2d_release_supported
                and calibration_wave_effective_frames <= resident_calibration_streams
            )
            calibration_callback_release_capable = bool(
                calibration_batch_multistream_enabled
                and calibration_callback_release_supported
                and calibration_wave_effective_frames <= resident_calibration_streams
            )
            if not calibration_batch_multistream_enabled:
                calibration_h2d_release_reason = "multistream_batch_disabled"
            elif not calibration_h2d_release_supported:
                calibration_h2d_release_reason = "native_h2d_release_unavailable"
            elif calibration_wave_effective_frames > resident_calibration_streams:
                calibration_h2d_release_reason = "wave_effective_exceeds_stream_count"
            elif calibration_wave_effective_frames == resident_calibration_streams:
                calibration_h2d_release_reason = "wave_effective_matches_stream_count"
            else:
                calibration_h2d_release_reason = "wave_effective_below_stream_count"
            calibration_h2d_release_recommended = bool(
                calibration_h2d_release_capable
                and calibration_wave_effective_frames == resident_calibration_streams
            )
            calibration_callback_release_recommended = bool(
                calibration_callback_release_capable
                and calibration_wave_effective_frames == resident_calibration_streams
            )
            calibration_release_mode_effective = "sync"
            if resident_calibration_release_mode == "callback_queue" and calibration_callback_release_capable:
                calibration_release_mode_effective = "callback_queue"
                calibration_h2d_release_reason = "explicit_callback_queue_requested"
            elif resident_calibration_release_mode == "callback_queue":
                calibration_h2d_release_reason = f"explicit_callback_queue_not_capable:{calibration_h2d_release_reason}"
            elif resident_calibration_release_mode == "h2d_event" and calibration_h2d_release_capable:
                calibration_release_mode_effective = "h2d_event"
                calibration_h2d_release_reason = "explicit_h2d_event_requested"
            elif resident_calibration_release_mode == "h2d_event":
                calibration_h2d_release_reason = f"explicit_h2d_event_not_capable:{calibration_h2d_release_reason}"
            elif resident_calibration_release_mode == "auto" and calibration_h2d_release_recommended:
                calibration_release_mode_effective = "h2d_event"
                calibration_h2d_release_reason = "auto_h2d_event_wave_effective_matches_stream_count"
            elif resident_calibration_release_mode == "auto":
                calibration_h2d_release_reason = f"auto_sync:{calibration_h2d_release_reason}"
            elif resident_calibration_release_mode == "sync":
                calibration_h2d_release_reason = "explicit_sync_requested"
            calibration_h2d_release_enabled = calibration_release_mode_effective == "h2d_event"
            calibration_callback_release_enabled = calibration_release_mode_effective == "callback_queue"
            raw_u16_runtime_reason = ""
            if not raw_u16_gpu_decode_supported:
                raw_u16_runtime_reason = "native_u16_gpu_method_unavailable"
            elif not calibration_batch_enabled:
                raw_u16_runtime_reason = "raw_u16_gpu_requires_batch_calibration"
            elif not calibration_callback_release_enabled:
                raw_u16_runtime_reason = "raw_u16_gpu_requires_callback_release"
            (
                resident_fits_read_mode_effective,
                resident_fits_auto_selection,
                resident_fits_spec_cache,
            ) = _resident_fits_read_mode_selection(
                light_frames,
                height=height,
                width=width,
                requested_mode=resident_fits_read_mode,
                raw_u16_runtime_reason=raw_u16_runtime_reason,
            )
            raw_u16_gpu_decode_enabled = resident_fits_read_mode_effective == "native_u16_gpu"
            if raw_u16_gpu_decode_enabled and raw_u16_runtime_reason:
                raise ValueError(
                    "resident-fits-read-mode native_u16_gpu is unavailable: "
                    f"{raw_u16_runtime_reason}; use --resident-runtime-preset throughput-v1 "
                    "on a build with the native raw-u16 GPU decode method"
                )
            source_dq_sidecar_records = [
                _resident_source_dq_sidecar_record(frame, plan_root, calibration_dq_sidecars)
                for frame in light_frames
            ]
            source_dq_sidecar_frame_count = sum(1 for record in source_dq_sidecar_records if record is not None)
            source_dq_fast_skip_enabled = bool(
                raw_u16_gpu_decode_enabled
                and resident_inline_source_dq == "off"
                and source_dq_sidecar_frame_count == 0
            )
            source_dq_fast_skip_reason = (
                "native_u16_gpu_integer_payload_without_inline_or_sidecar_source_dq"
                if source_dq_fast_skip_enabled
                else ""
            )
            source_dq_fast_skipped_frame_count = len(light_frames) if source_dq_fast_skip_enabled else 0
            native_path_calibration_supported = bool(
                hasattr(stack, "calibrate_frames_fits_u16be_bzero_paths_multistream_timed")
            )
            native_completion_calibration_supported = bool(
                hasattr(stack, "calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed")
            )
            native_path_calibration_env = str(
                os.environ.get("GLASS_RESIDENT_NATIVE_PATH_CALIBRATION", "")
            ).strip().lower()
            native_completion_calibration_env = str(
                os.environ.get("GLASS_RESIDENT_NATIVE_COMPLETION_CALIBRATION", "")
            ).strip().lower()
            native_completion_wave_fill_env = str(
                os.environ.get("GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_US", "")
            ).strip()
            native_completion_wave_fill_mode_env = str(
                os.environ.get("GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_MODE", "")
            ).strip().lower()
            native_completion_wave_fill_wait_us = int(resident_native_completion_wave_fill_us)
            native_completion_wave_fill_source = (
                "cli" if native_completion_wave_fill_wait_us > 0 else "default_disabled"
            )
            if native_completion_wave_fill_env and native_completion_wave_fill_wait_us <= 0:
                try:
                    native_completion_wave_fill_wait_us = int(native_completion_wave_fill_env)
                except ValueError as exc:
                    raise ValueError(
                        "GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_US must be an integer "
                        "number of microseconds between 0 and 10000"
                    ) from exc
                if native_completion_wave_fill_wait_us < 0 or native_completion_wave_fill_wait_us > 10000:
                    raise ValueError(
                        "GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_US must be between 0 and 10000"
                    )
                native_completion_wave_fill_source = "env"
            native_completion_wave_fill_mode = str(resident_native_completion_wave_fill_mode)
            native_completion_wave_fill_mode_source = "cli"
            if native_completion_wave_fill_mode_env:
                if native_completion_wave_fill_mode_env not in {"multi_wait", "single_wait"}:
                    raise ValueError(
                        "GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_MODE must be "
                        "multi_wait or single_wait"
                    )
                if native_completion_wave_fill_mode == "multi_wait":
                    native_completion_wave_fill_mode = native_completion_wave_fill_mode_env
                    native_completion_wave_fill_mode_source = "env"
            native_path_calibration_policy = (
                "env_enabled"
                if native_path_calibration_env in {"1", "true", "yes", "on"}
                else "env_disabled_default"
            )
            if resident_native_completion_calibration == "on":
                native_completion_calibration_policy = "cli_enabled"
            elif native_completion_calibration_env in {"1", "true", "yes", "on"}:
                native_completion_calibration_policy = "env_enabled"
            else:
                native_completion_calibration_policy = "env_disabled_default"
            native_path_calibration_candidate = bool(
                raw_u16_gpu_decode_enabled
                and calibration_batch_enabled
                and calibration_batch_multistream_enabled
                and source_dq_fast_skip_enabled
                and resident_fits_spec_cache
            )
            native_completion_calibration_candidate = bool(native_path_calibration_candidate)
            native_completion_calibration_requested = bool(
                native_completion_calibration_candidate
                and native_completion_calibration_policy in {"cli_enabled", "env_enabled"}
            )
            native_completion_calibration_available = bool(
                native_completion_calibration_candidate and native_completion_calibration_supported
            )
            native_path_calibration_requested = bool(
                native_path_calibration_candidate
                and native_path_calibration_policy == "env_enabled"
                and not native_completion_calibration_requested
            )
            native_path_calibration_available = bool(
                native_path_calibration_candidate and native_path_calibration_supported
            )
            if not native_path_calibration_candidate:
                if not raw_u16_gpu_decode_enabled:
                    native_path_calibration_reason = "requires_native_u16_gpu_read_mode"
                elif not calibration_batch_enabled:
                    native_path_calibration_reason = "requires_batch_calibration"
                elif not calibration_batch_multistream_enabled:
                    native_path_calibration_reason = "requires_multistream_batch_calibration"
                elif not source_dq_fast_skip_enabled:
                    native_path_calibration_reason = "requires_source_dq_fast_skip"
                else:
                    native_path_calibration_reason = "requires_fits_header_spec_cache"
            elif native_completion_calibration_requested:
                native_path_calibration_reason = "ignored_native_completion_enabled"
            elif not native_path_calibration_requested:
                native_path_calibration_reason = "env_disabled_default"
            elif not native_path_calibration_available:
                native_path_calibration_reason = "native_method_unavailable"
            else:
                native_path_calibration_reason = "env_enabled"
            native_path_calibration_enabled = bool(
                native_path_calibration_requested and native_path_calibration_available
            )
            if not native_completion_calibration_candidate:
                if not raw_u16_gpu_decode_enabled:
                    native_completion_calibration_reason = "requires_native_u16_gpu_read_mode"
                elif not calibration_batch_enabled:
                    native_completion_calibration_reason = "requires_batch_calibration"
                elif not calibration_batch_multistream_enabled:
                    native_completion_calibration_reason = "requires_multistream_batch_calibration"
                elif not source_dq_fast_skip_enabled:
                    native_completion_calibration_reason = "requires_source_dq_fast_skip"
                else:
                    native_completion_calibration_reason = "requires_fits_header_spec_cache"
            elif not native_completion_calibration_requested:
                native_completion_calibration_reason = "env_disabled_default"
            elif not native_completion_calibration_available:
                native_completion_calibration_reason = "native_method_unavailable"
            else:
                native_completion_calibration_reason = native_completion_calibration_policy
            native_completion_calibration_enabled = bool(
                native_completion_calibration_requested and native_completion_calibration_available
            )
            native_direct_calibration_enabled = bool(
                native_path_calibration_enabled or native_completion_calibration_enabled
            )
            calibration_fetch_batch_frames = (
                int(resident_calibration_batch_frames)
                if calibration_callback_release_enabled
                else int(calibration_wave_effective_frames)
            )
            calibration_fetch_batch_requested_frames = int(calibration_fetch_batch_frames)
            calibration_fetch_batch_limit_source = "requested"
            calibration_fetch_batch_clamped_to_prefetch_depth = False
            if (
                calibration_callback_release_enabled
                and resident_h2d_mode == "pinned_ring"
                and resident_prefetch_frames > 0
                and not native_direct_calibration_enabled
                and calibration_fetch_batch_frames > int(resident_prefetch_frames)
            ):
                calibration_fetch_batch_frames = int(resident_prefetch_frames)
                calibration_fetch_batch_limit_source = "pinned_ring_prefetch_depth"
                calibration_fetch_batch_clamped_to_prefetch_depth = True
            if native_completion_calibration_enabled:
                calibration_fetch_batch_frames = max(calibration_fetch_batch_frames, len(light_frames))
                calibration_fetch_batch_limit_source = "native_completion_calibration_all_available_frames"
            calibration_batch_count = 0
            calibration_batch_frame_count = 0
            calibration_batch_native_total_s = 0.0
            calibration_batch_stream_s = 0.0
            calibration_batch_sync_s = 0.0
            calibration_batch_lane_buffer_bytes = 0
            calibration_batch_actual_stream_count = 0
            calibration_h2d_release_count = 0
            calibration_h2d_release_s = 0.0
            calibration_h2d_event_sync_s = 0.0
            calibration_h2d_event_elapsed_s = 0.0
            calibration_pending_wait_sync_s = 0.0
            calibration_callback_release_count = 0
            calibration_callback_release_s = 0.0
            calibration_callback_wave_count = 0
            calibration_raw_h2d_bytes = 0
            calibration_float32_host_bytes_avoided = 0
            native_path_calibration_batch_count = 0
            native_path_calibration_frame_count = 0
            native_path_calibration_file_open_s = 0.0
            native_path_calibration_file_read_s = 0.0
            native_path_calibration_total_s = 0.0
            native_path_calibration_host_buffer_bytes = 0
            native_path_calibration_wave_h2d_elapsed_s = 0.0
            native_path_calibration_host_buffer_model: str | None = None
            native_path_calibration_host_buffer_pinned = False
            native_completion_calibration_submit_count = 0
            native_completion_calibration_completion_count = 0
            native_completion_calibration_out_of_order_count = 0
            native_completion_calibration_worker_count = 0
            native_completion_calibration_queue_buffer_count = 0
            native_completion_calibration_order_sample: list[int] = []
            native_completion_calibration_slot_release_mode: str | None = None
            native_completion_calibration_slot_reuse_count = 0
            native_completion_calibration_slot_reuse_query_count = 0
            native_completion_calibration_slot_reuse_ready_count = 0
            native_completion_calibration_slot_reuse_wait_count = 0
            native_completion_calibration_slot_reuse_wait_s = 0.0
            native_completion_calibration_final_h2d_collect_count = 0
            native_completion_calibration_consumer_schedule_mode: str | None = None
            native_completion_calibration_consumer_wave_fill_mode: str | None = None
            native_completion_calibration_consumer_wave_fill_policy: str | None = None
            native_completion_calibration_consumer_wave_fill_wait_us = 0
            native_completion_calibration_consumer_wave_fill_wait_count = 0
            native_completion_calibration_consumer_wave_fill_timeout_count = 0
            native_completion_calibration_consumer_wave_fill_wait_s = 0.0
            native_completion_calibration_consumer_wave_count = 0
            native_completion_calibration_consumer_max_wave_frames = 0
            native_completion_calibration_consumer_multi_frame_wave_count = 0
            prefetch_fill_blocked_no_slot_count = 0
            prefetch_release_count = 0
            prefetch_max_inflight_slots = 0
            light_master_selections: list[tuple[str, str | None, str | None, str | None]] = []
            for frame in light_frames:
                calibration_groups = light_calibration_groups.get(str(frame["id"]), {})
                bias_group = calibration_groups.get("bias_group")
                dark_group = calibration_groups.get("dark_group")
                flat_group = calibration_groups.get("flat_group")
                light_master_selections.append(
                    (
                        _master_set_cache_key(
                            filter_name,
                            height,
                            width,
                            bias_group,
                            dark_group,
                            flat_group,
                        ),
                        bias_group,
                        dark_group,
                        flat_group,
                    )
                )
            calibration_master_group_count = len({item[0] for item in light_master_selections})
            if native_completion_calibration_enabled:
                calibration_ready_order_reason = "native_completion_calibration_direct"
            elif native_path_calibration_enabled:
                calibration_ready_order_reason = "native_path_calibration_direct"
            elif not calibration_batch_enabled:
                calibration_ready_order_reason = "batch_calibration_disabled"
            elif int(resident_prefetch_frames) <= 0:
                calibration_ready_order_reason = "prefetch_disabled"
            elif calibration_master_group_count != 1:
                calibration_ready_order_reason = "multiple_master_sets"
            elif len(light_frames) <= 1:
                calibration_ready_order_reason = "single_frame_group"
            else:
                calibration_ready_order_reason = "single_master_set_prefetch_ready"
            calibration_ready_order_enabled = calibration_ready_order_reason == "single_master_set_prefetch_ready"
            calibration_order_mode = (
                "ready_first_single_master_group"
                if calibration_ready_order_enabled
                else "sequential_index"
            )
            calibration_ready_order_select_wait_s = 0.0
            calibration_ready_order_out_of_order_count = 0
            calibration_ready_order_sample: list[int] = []
            calibration_ready_order_expected_next = 0
            light_prefetch_depth = 0 if native_direct_calibration_enabled else int(resident_prefetch_frames)
            with _LightPrefetcher(
                light_frames,
                light_prefetch_depth,
                resident_prefetch_workers,
                pinned_ring=resident_h2d_mode == "pinned_ring",
                height=height,
                width=width,
                release_refill_mode=resident_prefetch_refill_mode,
                fits_read_mode=resident_fits_read_mode_effective,
                fits_specs_by_path=resident_fits_spec_cache,
                native_batch_read=resident_native_batch_read,
                native_queue_read=resident_native_queue_read,
                native_queue_drain_mode=resident_native_queue_drain_mode,
            ) as light_prefetch:
                prefetch_host_pinned_bytes = light_prefetch.host_pinned_bytes
                calibration_remaining_index_model = "set_with_sequential_cursor"
                calibration_remaining_index_set_discard_count = 0
                calibration_remaining_index_cursor_advance_count = 0
                if calibration_batch_enabled:
                    remaining_index_set = set(range(len(light_frames)))
                    remaining_index_cursor = 0
                    processed_count = 0
                    ready_batch_queue: list[tuple[int, float]] = []
                    while remaining_index_set:
                        batch_items: list[tuple[int, dict[str, Any], np.ndarray | None, float]] = []
                        batch_frame_starts: list[float] = []
                        while remaining_index_set and len(batch_items) < calibration_fetch_batch_frames:
                            ready_select_wait_s = 0.0
                            if calibration_ready_order_enabled and light_prefetch.ready_batch_select_enabled:
                                if not ready_batch_queue:
                                    ready_select_start = perf_counter()
                                    selected_indices = light_prefetch.ready_indices_batch(
                                        remaining_index_set,
                                        calibration_fetch_batch_frames - len(batch_items),
                                    )
                                    ready_select_wait_total_s = perf_counter() - ready_select_start
                                    calibration_ready_order_select_wait_s += ready_select_wait_total_s
                                    if selected_indices:
                                        ready_select_wait_share_s = (
                                            ready_select_wait_total_s / float(len(selected_indices))
                                        )
                                        ready_batch_queue = [
                                            (int(selected_index), ready_select_wait_share_s)
                                            for selected_index in selected_indices
                                        ]
                                if not ready_batch_queue:
                                    break
                                item_index, ready_select_wait_s = ready_batch_queue.pop(0)
                            elif calibration_ready_order_enabled:
                                ready_select_start = perf_counter()
                                selected_index = light_prefetch.ready_index(remaining_index_set)
                                ready_select_wait_s = perf_counter() - ready_select_start
                                calibration_ready_order_select_wait_s += ready_select_wait_s
                                if selected_index is None:
                                    break
                                item_index = int(selected_index)
                            else:
                                while (
                                    remaining_index_cursor < len(light_frames)
                                    and remaining_index_cursor not in remaining_index_set
                                ):
                                    remaining_index_cursor += 1
                                    calibration_remaining_index_cursor_advance_count += 1
                                if remaining_index_cursor >= len(light_frames):
                                    break
                                item_index = int(remaining_index_cursor)
                            frame = light_frames[item_index]
                            frame_start = perf_counter()
                            master_key, bias_group, dark_group, flat_group = light_master_selections[item_index]
                            if batch_items and master_key != current_master_key:
                                break
                            if master_key != current_master_key:
                                master_set_start = perf_counter()
                                master_bias, master_dark, master_flat, stats, dark_exposure = (
                                    _load_or_build_matching_masters(
                                        run,
                                        filter_name,
                                        height,
                                        width,
                                        frames,
                                        groups,
                                        bias_group,
                                        dark_group,
                                        flat_group,
                                        policy,
                                        master_cache_dir=shared_master_cache_dir,
                                        cache_write_queue=master_cache_write_queue,
                                    )
                                )
                                stack.set_calibration_masters(master_bias, master_dark, master_flat)
                                master_elapsed += perf_counter() - master_set_start
                                master_stats_sets[master_key] = stats
                                current_master_key = master_key
                                current_dark_exposure = None if dark_exposure is None else float(dark_exposure)
                                del master_bias, master_dark, master_flat
                                gc_start = perf_counter()
                                gc.collect()
                                gc_elapsed += perf_counter() - gc_start
                            if native_direct_calibration_enabled:
                                spec = resident_fits_spec_cache.get(str(frame["path"]))
                                header_cache_hit = spec is not None
                                if spec is None:
                                    spec = simple_fits_image_spec(frame["path"])
                                    resident_fits_spec_cache[str(frame["path"])] = spec
                                byte_count = int(spec.width) * int(spec.height) * 2
                                light = None
                                read_wait_elapsed = 0.0
                                read_profile = {
                                    "total": 0.0,
                                    "fits_open": 0.0,
                                    "fits_materialize_decode": 0.0,
                                    "fits_reader_backend": (
                                        "native_u16be_raw_completion_calibration"
                                        if native_completion_calibration_enabled
                                        else "native_u16be_raw_path_calibration"
                                    ),
                                    "fits_fast_supported": True,
                                    "fits_fast_bitpix": int(spec.bitpix),
                                    "fits_fast_scaled": True,
                                    "fits_fast_fallback_reason": "",
                                    "fits_header_cache_hit": bool(header_cache_hit),
                                    "fits_raw_byte_count": int(byte_count),
                                    "fits_gpu_decode_staging": "u16be_bzero32768",
                                }
                            else:
                                light, read_profile, read_wait_elapsed = light_prefetch.result(item_index)
                            per_frame_read_worker_s.append(float(read_profile.get("total", 0.0)))
                            per_frame_fits_open_s.append(float(read_profile.get("fits_open", 0.0)))
                            per_frame_fits_materialize_decode_s.append(
                                float(read_profile.get("fits_materialize_decode", 0.0))
                            )
                            per_frame_fits_backend.append(str(read_profile.get("fits_reader_backend", "unknown")))
                            fallback_reason = str(read_profile.get("fits_fast_fallback_reason", "") or "")
                            if fallback_reason:
                                per_frame_fits_fallback_reason.append(fallback_reason)
                            if "fits_native_file_read_s" in read_profile:
                                per_frame_fits_native_file_read_s.append(
                                    float(read_profile.get("fits_native_file_read_s", 0.0))
                                )
                            if "fits_native_decode_s" in read_profile:
                                per_frame_fits_native_decode_s.append(
                                    float(read_profile.get("fits_native_decode_s", 0.0))
                                )
                            if "fits_native_total_s" in read_profile:
                                per_frame_fits_native_total_s.append(
                                    float(read_profile.get("fits_native_total_s", 0.0))
                                )
                            if "fits_native_bytes_read" in read_profile:
                                per_frame_fits_native_bytes_read.append(
                                    int(read_profile.get("fits_native_bytes_read", 0) or 0)
                                )
                            if bool(read_profile.get("fits_header_cache_hit", False)):
                                per_frame_fits_header_cache_hits += 1
                            per_frame_read_s.append(read_wait_elapsed + ready_select_wait_s)
                            if item_index != calibration_ready_order_expected_next:
                                calibration_ready_order_out_of_order_count += 1
                            calibration_ready_order_expected_next += 1
                            if len(calibration_ready_order_sample) < 64:
                                calibration_ready_order_sample.append(int(item_index))
                            remaining_index_set.discard(item_index)
                            calibration_remaining_index_set_discard_count += 1
                            batch_items.append((item_index, frame, light, float(frame.get("exposure_s") or 0.0)))
                            batch_frame_starts.append(frame_start)
                        if not batch_items:
                            break

                        batch_calibrate_start = perf_counter()
                        batch_indices = [item[0] for item in batch_items]
                        batch_lights = [item[2] for item in batch_items]
                        source_dq_pending_by_index: dict[
                            int, tuple[str, np.ndarray | None, dict[str, Any]]
                        ] = {}
                        if not source_dq_fast_skip_enabled:
                            for item_index, frame, light, _exposure in batch_items:
                                invalid_mask, mask_info = _resident_source_invalid_mask_from_frame(
                                    frame,
                                    light,
                                    height=height,
                                    width=width,
                                    plan_root=plan_root,
                                    calibration_dq_sidecars=calibration_dq_sidecars,
                                    resident_inline_source_dq=resident_inline_source_dq,
                                    resident_inline_source_dq_hot_sigma=resident_inline_source_dq_hot_sigma,
                                    resident_inline_source_dq_cold_sigma=resident_inline_source_dq_cold_sigma,
                                )
                                if (
                                    resident_inline_source_dq not in {"cosmetic_cuda", "cosmetic_star_cuda"}
                                    or str(mask_info.get("source_model") or "") != "none"
                                    or int(mask_info.get("invalid_samples") or 0) > 0
                                ):
                                    source_dq_pending_by_index[int(item_index)] = (
                                        str(frame["id"]),
                                        invalid_mask,
                                        mask_info,
                                    )
                        batch_light_exposures = [item[3] for item in batch_items]
                        batch_dark_exposures = [
                            np.nan if current_dark_exposure is None else float(current_dark_exposure)
                            for _item in batch_items
                        ]
                        if native_direct_calibration_enabled:
                            batch_specs: list[SimpleFitsImageSpec] = []
                            for _item_index, frame, _light, _exposure in batch_items:
                                spec = resident_fits_spec_cache.get(str(frame["path"]))
                                if spec is None:
                                    spec = simple_fits_image_spec(frame["path"])
                                    resident_fits_spec_cache[str(frame["path"])] = spec
                                batch_specs.append(spec)
                            if native_completion_calibration_enabled:
                                native_completion_queue_buffers = max(
                                    int(resident_prefetch_frames),
                                    int(resident_calibration_batch_frames),
                                    int(resident_calibration_streams) * 2,
                                )
                                native_completion_workers = max(
                                    int(resident_prefetch_workers),
                                    int(resident_calibration_streams),
                                )
                                native_completion_policy = asdict(policy)
                                native_completion_policy[
                                    "native_completion_consumer_wave_fill_wait_us"
                                ] = int(native_completion_wave_fill_wait_us)
                                native_completion_policy[
                                    "native_completion_consumer_wave_fill_mode"
                                ] = str(native_completion_wave_fill_mode)
                                calibration_timing = (
                                    stack.calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed(
                                        batch_indices,
                                        [str(spec.path) for spec in batch_specs],
                                        [int(spec.data_offset) for spec in batch_specs],
                                        [int(spec.width) * int(spec.height) * 2 for spec in batch_specs],
                                        batch_light_exposures,
                                        batch_dark_exposures,
                                        resident_calibration_streams,
                                        native_completion_queue_buffers,
                                        native_completion_workers,
                                        native_completion_policy,
                                    )
                                )
                                native_completion_calibration_submit_count += int(
                                    calibration_timing.get("native_completion_submit_count", 0) or 0
                                )
                                native_completion_calibration_completion_count += int(
                                    calibration_timing.get("native_completion_count", 0) or 0
                                )
                                native_completion_calibration_out_of_order_count += int(
                                    calibration_timing.get("native_completion_out_of_order_count", 0) or 0
                                )
                                native_completion_calibration_worker_count = max(
                                    native_completion_calibration_worker_count,
                                    int(calibration_timing.get("worker_count", 0) or 0),
                                )
                                native_completion_calibration_queue_buffer_count = max(
                                    native_completion_calibration_queue_buffer_count,
                                    int(calibration_timing.get("queue_buffer_count", 0) or 0),
                                )
                                timing_slot_release_mode = str(
                                    calibration_timing.get("native_completion_slot_release_mode", "") or ""
                                )
                                if timing_slot_release_mode:
                                    native_completion_calibration_slot_release_mode = timing_slot_release_mode
                                native_completion_calibration_slot_reuse_count += int(
                                    calibration_timing.get("native_completion_slot_reuse_count", 0) or 0
                                )
                                native_completion_calibration_slot_reuse_query_count += int(
                                    calibration_timing.get("native_completion_slot_reuse_query_count", 0) or 0
                                )
                                native_completion_calibration_slot_reuse_ready_count += int(
                                    calibration_timing.get("native_completion_slot_reuse_ready_count", 0) or 0
                                )
                                native_completion_calibration_slot_reuse_wait_count += int(
                                    calibration_timing.get("native_completion_slot_reuse_wait_count", 0) or 0
                                )
                                native_completion_calibration_slot_reuse_wait_s += float(
                                    calibration_timing.get("native_completion_slot_reuse_wait_s", 0.0) or 0.0
                                )
                                native_completion_calibration_final_h2d_collect_count += int(
                                    calibration_timing.get("native_completion_final_h2d_collect_count", 0) or 0
                                )
                                timing_consumer_schedule_mode = str(
                                    calibration_timing.get("native_completion_consumer_schedule_mode", "") or ""
                                )
                                if timing_consumer_schedule_mode:
                                    native_completion_calibration_consumer_schedule_mode = (
                                        timing_consumer_schedule_mode
                                    )
                                timing_wave_fill_mode = str(
                                    calibration_timing.get(
                                        "native_completion_consumer_wave_fill_mode", ""
                                    )
                                    or ""
                                )
                                if timing_wave_fill_mode:
                                    native_completion_calibration_consumer_wave_fill_mode = (
                                        timing_wave_fill_mode
                                    )
                                timing_wave_fill_policy = str(
                                    calibration_timing.get(
                                        "native_completion_consumer_wave_fill_policy", ""
                                    )
                                    or ""
                                )
                                if timing_wave_fill_policy:
                                    native_completion_calibration_consumer_wave_fill_policy = (
                                        timing_wave_fill_policy
                                    )
                                native_completion_calibration_consumer_wave_fill_wait_us = max(
                                    native_completion_calibration_consumer_wave_fill_wait_us,
                                    int(
                                        calibration_timing.get(
                                            "native_completion_consumer_wave_fill_wait_us", 0
                                        )
                                        or 0
                                    ),
                                )
                                native_completion_calibration_consumer_wave_fill_wait_count += int(
                                    calibration_timing.get(
                                        "native_completion_consumer_wave_fill_wait_count", 0
                                    )
                                    or 0
                                )
                                native_completion_calibration_consumer_wave_fill_timeout_count += int(
                                    calibration_timing.get(
                                        "native_completion_consumer_wave_fill_timeout_count", 0
                                    )
                                    or 0
                                )
                                native_completion_calibration_consumer_wave_fill_wait_s += float(
                                    calibration_timing.get(
                                        "native_completion_consumer_wave_fill_wait_s", 0.0
                                    )
                                    or 0.0
                                )
                                native_completion_calibration_consumer_wave_count += int(
                                    calibration_timing.get("native_completion_consumer_wave_count", 0) or 0
                                )
                                native_completion_calibration_consumer_max_wave_frames = max(
                                    native_completion_calibration_consumer_max_wave_frames,
                                    int(calibration_timing.get("native_completion_consumer_max_wave_frames", 0) or 0),
                                )
                                native_completion_calibration_consumer_multi_frame_wave_count += int(
                                    calibration_timing.get(
                                        "native_completion_consumer_multi_frame_wave_count", 0
                                    )
                                    or 0
                                )
                                for sample_index in list(
                                    calibration_timing.get("native_completion_order_sample", []) or []
                                ):
                                    if len(native_completion_calibration_order_sample) < 64:
                                        native_completion_calibration_order_sample.append(int(sample_index))
                            else:
                                calibration_timing = (
                                    stack.calibrate_frames_fits_u16be_bzero_paths_multistream_timed(
                                        batch_indices,
                                        [str(spec.path) for spec in batch_specs],
                                        [int(spec.data_offset) for spec in batch_specs],
                                        [int(spec.width) * int(spec.height) * 2 for spec in batch_specs],
                                        batch_light_exposures,
                                        batch_dark_exposures,
                                        resident_calibration_streams,
                                        calibration_wave_effective_frames,
                                        asdict(policy),
                                    )
                                )
                            native_path_calibration_batch_count += 1
                            native_path_calibration_frame_count += len(batch_items)
                            native_path_calibration_file_open_s += float(
                                calibration_timing.get("native_path_read_file_open_s", 0.0) or 0.0
                            )
                            native_path_calibration_file_read_s += float(
                                calibration_timing.get("native_path_read_file_read_s", 0.0) or 0.0
                            )
                            native_path_calibration_total_s += float(
                                calibration_timing.get("native_path_read_total_s", 0.0) or 0.0
                            )
                            native_path_calibration_host_buffer_bytes = max(
                                native_path_calibration_host_buffer_bytes,
                                int(calibration_timing.get("native_path_host_buffer_bytes", 0) or 0),
                            )
                            timing_host_buffer_model = str(
                                calibration_timing.get("native_path_host_buffer_model", "") or ""
                            )
                            if timing_host_buffer_model:
                                native_path_calibration_host_buffer_model = timing_host_buffer_model
                            native_path_calibration_host_buffer_pinned = bool(
                                native_path_calibration_host_buffer_pinned
                                or calibration_timing.get("native_path_host_buffer_pinned", False)
                            )
                            wave_h2d_elapsed = calibration_timing.get("wave_h2d_elapsed_s", 0.0)
                            if isinstance(wave_h2d_elapsed, (list, tuple)):
                                native_path_calibration_wave_h2d_elapsed_s += sum(
                                    float(value) for value in wave_h2d_elapsed
                                )
                            else:
                                native_path_calibration_wave_h2d_elapsed_s += float(
                                    wave_h2d_elapsed or 0.0
                                )
                            frame_native_share = 1.0 / float(len(batch_items))
                            native_bytes = int(calibration_timing.get("native_path_read_bytes", 0) or 0)
                            native_bytes_share = int(native_bytes // max(1, len(batch_items)))
                            per_frame_fits_native_file_read_s.extend(
                                [
                                    float(
                                        calibration_timing.get("native_path_read_file_read_s", 0.0) or 0.0
                                    )
                                    * frame_native_share
                                ]
                                * len(batch_items)
                            )
                            per_frame_fits_native_decode_s.extend([0.0] * len(batch_items))
                            per_frame_fits_native_total_s.extend(
                                [
                                    float(calibration_timing.get("native_path_read_total_s", 0.0) or 0.0)
                                    * frame_native_share
                                ]
                                * len(batch_items)
                            )
                            per_frame_fits_native_bytes_read.extend(
                                [native_bytes_share] * len(batch_items)
                            )
                        elif calibration_callback_release_enabled:
                            released_batch_indices: set[int] = set()

                            def _release_h2d_completed_indices(released_indices: list[int]) -> None:
                                completed = [int(released_index) for released_index in released_indices]
                                light_prefetch.release_many(completed)
                                released_batch_indices.update(completed)

                            try:
                                if raw_u16_gpu_decode_enabled:
                                    calibration_timing = (
                                        stack.calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed(
                                            batch_indices,
                                            batch_lights,
                                            batch_light_exposures,
                                            batch_dark_exposures,
                                            resident_calibration_streams,
                                            calibration_wave_effective_frames,
                                            _release_h2d_completed_indices,
                                            asdict(policy),
                                        )
                                    )
                                else:
                                    calibration_timing = (
                                        stack.calibrate_frames_host_async_multistream_callback_release_timed(
                                            batch_indices,
                                            batch_lights,
                                            batch_light_exposures,
                                            batch_dark_exposures,
                                            resident_calibration_streams,
                                            calibration_wave_effective_frames,
                                            _release_h2d_completed_indices,
                                            asdict(policy),
                                        )
                                    )
                            finally:
                                unreleased_indices = [
                                    item_index for item_index in batch_indices if item_index not in released_batch_indices
                                ]
                                light_prefetch.release_many(unreleased_indices)
                            calibration_h2d_release_count += int(
                                calibration_timing.get("callback_release_count", 0) or 0
                            )
                            calibration_h2d_release_s += float(
                                calibration_timing.get("h2d_release_s", 0.0) or 0.0
                            )
                            calibration_h2d_event_sync_s += float(
                                calibration_timing.get("h2d_event_sync_s", 0.0) or 0.0
                            )
                            calibration_h2d_event_elapsed_s += float(
                                calibration_timing.get("h2d_event_elapsed_s", 0.0) or 0.0
                            )
                            calibration_callback_release_count += int(
                                calibration_timing.get("callback_release_count", 0) or 0
                            )
                            calibration_callback_release_s += float(
                                calibration_timing.get("callback_s", 0.0) or 0.0
                            )
                            calibration_callback_wave_count += int(calibration_timing.get("wave_count", 0) or 0)
                        elif calibration_h2d_release_enabled:
                            h2d_release_timing = stack.calibrate_frames_host_async_multistream_h2d_release_timed(
                                batch_indices,
                                batch_lights,
                                batch_light_exposures,
                                batch_dark_exposures,
                                resident_calibration_streams,
                                asdict(policy),
                            )
                            light_prefetch.release_many(batch_indices)
                            finish_timing = stack.finish_pending_calibration_timed()
                            calibration_timing = dict(finish_timing)
                            calibration_timing["h2d_mode"] = str(h2d_release_timing.get("h2d_mode", "unknown"))
                            calibration_timing["event_mode"] = str(h2d_release_timing.get("event_mode", "unknown"))
                            calibration_timing["timing_model"] = str(
                                h2d_release_timing.get("timing_model", "unknown")
                            )
                            calibration_timing["h2d_release_s"] = float(
                                h2d_release_timing.get("h2d_release_s", 0.0) or 0.0
                            )
                            calibration_timing["h2d_event_sync_s"] = float(
                                h2d_release_timing.get("h2d_event_sync_s", 0.0) or 0.0
                            )
                            calibration_timing["h2d_event_elapsed_s"] = float(
                                h2d_release_timing.get("h2d_event_elapsed_s", 0.0) or 0.0
                            )
                            calibration_timing["host_release_safe"] = bool(
                                h2d_release_timing.get("host_release_safe", False)
                            )
                            calibration_h2d_release_count += len(batch_items)
                            calibration_h2d_release_s += float(
                                h2d_release_timing.get("h2d_release_s", 0.0) or 0.0
                            )
                            calibration_h2d_event_sync_s += float(
                                h2d_release_timing.get("h2d_event_sync_s", 0.0) or 0.0
                            )
                            calibration_h2d_event_elapsed_s += float(
                                h2d_release_timing.get("h2d_event_elapsed_s", 0.0) or 0.0
                            )
                            calibration_pending_wait_sync_s += float(
                                finish_timing.get("wait_sync_s", 0.0) or 0.0
                            )
                        else:
                            try:
                                if calibration_batch_multistream_enabled:
                                    calibration_timing = stack.calibrate_frames_host_async_multistream_timed(
                                        batch_indices,
                                        batch_lights,
                                        batch_light_exposures,
                                        batch_dark_exposures,
                                        resident_calibration_streams,
                                        asdict(policy),
                                    )
                                else:
                                    calibration_timing = stack.calibrate_frames_host_async_timed(
                                        batch_indices,
                                        batch_lights,
                                        batch_light_exposures,
                                        batch_dark_exposures,
                                        asdict(policy),
                                    )
                            finally:
                                light_prefetch.release_many(batch_indices)
                        batch_calibrate_elapsed = perf_counter() - batch_calibrate_start
                        calibration_batch_count += 1
                        calibration_batch_frame_count += len(batch_items)
                        calibration_batch_native_total_s += float(calibration_timing.get("total_s", 0.0) or 0.0)
                        calibration_batch_stream_s += float(
                            calibration_timing.get("stream_h2d_calibrate_store_s", 0.0) or 0.0
                        )
                        calibration_batch_sync_s += float(calibration_timing.get("sync_s", 0.0) or 0.0)
                        calibration_batch_lane_buffer_bytes = max(
                            calibration_batch_lane_buffer_bytes,
                            int(calibration_timing.get("calibration_lane_buffer_bytes", 0) or 0),
                        )
                        calibration_batch_actual_stream_count = max(
                            calibration_batch_actual_stream_count,
                            int(calibration_timing.get("stream_count", 0) or 0),
                        )
                        calibration_raw_h2d_bytes += int(calibration_timing.get("raw_h2d_bytes", 0) or 0)
                        calibration_float32_host_bytes_avoided += int(
                            calibration_timing.get("float32_host_bytes_avoided", 0) or 0
                        )
                        batch_thresholds_by_index = (
                            _resident_source_inline_cosmetic_thresholds_batch_from_resident_stack(
                                stack,
                                frame_indices=[int(item[0]) for item in batch_items],
                                height=height,
                                width=width,
                                resident_inline_source_dq=resident_inline_source_dq,
                                resident_inline_source_dq_hot_sigma=resident_inline_source_dq_hot_sigma,
                                resident_inline_source_dq_cold_sigma=resident_inline_source_dq_cold_sigma,
                            )
                            if resident_inline_source_dq in {"cosmetic_cuda", "cosmetic_star_cuda"}
                            else {}
                        )
                        batch_threshold_apply_items: list[dict[str, Any]] = []
                        frame_share = 1.0 / float(len(batch_items))
                        for position, (item_index, frame, _light, _exposure) in enumerate(batch_items):
                            pending = source_dq_pending_by_index.get(int(item_index))
                            if pending is not None:
                                pending_frame_id, invalid_mask, mask_info = pending
                                source_dq_rows.append(
                                    apply_resident_source_invalid_mask(
                                        stack,
                                        frame_index=int(item_index),
                                        frame_id=pending_frame_id,
                                        invalid_mask=invalid_mask,
                                        mask_info=mask_info,
                                        source="resident_calibrated_batch_input",
                                    )
                                )
                            threshold_info = batch_thresholds_by_index.get(int(item_index))
                            if threshold_info is None:
                                threshold_info = _resident_source_inline_cosmetic_thresholds_from_resident_stack(
                                    stack,
                                    frame_index=int(item_index),
                                    height=height,
                                    width=width,
                                    resident_inline_source_dq=resident_inline_source_dq,
                                    resident_inline_source_dq_hot_sigma=resident_inline_source_dq_hot_sigma,
                                    resident_inline_source_dq_cold_sigma=resident_inline_source_dq_cold_sigma,
                                )
                            if threshold_info is not None:
                                threshold_item = {
                                    "frame_index": int(item_index),
                                    "frame_id": str(frame["id"]),
                                    "threshold_info": threshold_info,
                                }
                                if defer_inline_cosmetic_cuda_source_dq:
                                    _record_inline_cosmetic_cuda_source_dq_item(threshold_item)
                                else:
                                    batch_threshold_apply_items.append(threshold_item)
                            frame_weight = 0.0 if _matches_any_token(frame, excluded_tokens) else 1.0
                            frame_weights[str(frame["id"])] = frame_weight
                            frame_weight_values.append(frame_weight)
                            per_frame_calibrate_s.append(batch_calibrate_elapsed * frame_share)
                            per_frame_host_copy_s.append(float(calibration_timing.get("host_copy_s", 0.0)) * frame_share)
                            per_frame_h2d_s.append(float(calibration_timing.get("h2d_s", 0.0)) * frame_share)
                            per_frame_calibrate_store_s.append(
                                float(calibration_timing.get("calibrate_store_s", 0.0)) * frame_share
                            )
                            calibration_event_modes.append(str(calibration_timing.get("event_mode", "unknown")))
                        if batch_threshold_apply_items:
                            rows = apply_resident_inline_cosmetic_thresholds_batch(
                                stack,
                                items=batch_threshold_apply_items,
                                source=f"resident_calibrated_batch_input_{resident_inline_source_dq}",
                                max_invalid_fraction=resident_inline_source_dq_max_invalid_fraction,
                            )
                            for row in rows:
                                row["application_order"] = "calibration_pre_registration"
                            source_dq_rows.extend(rows)
                        for position, _item in enumerate(batch_items):
                            per_frame_s.append(perf_counter() - batch_frame_starts[position])
                        processed_count += len(batch_items)
                        del batch_items
                        if processed_count % 10 == 0:
                            gc_start = perf_counter()
                            gc.collect()
                            gc_elapsed += perf_counter() - gc_start
                else:
                    for index, frame in enumerate(light_frames):
                        frame_start = perf_counter()
                        calibration_groups = light_calibration_groups.get(str(frame["id"]), {})
                        bias_group = calibration_groups.get("bias_group")
                        dark_group = calibration_groups.get("dark_group")
                        flat_group = calibration_groups.get("flat_group")
                        master_key = _master_set_cache_key(
                            filter_name,
                            height,
                            width,
                            bias_group,
                            dark_group,
                            flat_group,
                        )
                        if master_key != current_master_key:
                            master_set_start = perf_counter()
                            master_bias, master_dark, master_flat, stats, dark_exposure = (
                                _load_or_build_matching_masters(
                                    run,
                                    filter_name,
                                    height,
                                    width,
                                    frames,
                                    groups,
                                    bias_group,
                                    dark_group,
                                    flat_group,
                                    policy,
                                    master_cache_dir=shared_master_cache_dir,
                                    cache_write_queue=master_cache_write_queue,
                                )
                            )
                            stack.set_calibration_masters(master_bias, master_dark, master_flat)
                            master_elapsed += perf_counter() - master_set_start
                            master_stats_sets[master_key] = stats
                            current_master_key = master_key
                            current_dark_exposure = None if dark_exposure is None else float(dark_exposure)
                            del master_bias, master_dark, master_flat
                            gc_start = perf_counter()
                            gc.collect()
                            gc_elapsed += perf_counter() - gc_start
                        light, read_profile, read_wait_elapsed = light_prefetch.result(index)
                        per_frame_read_worker_s.append(float(read_profile.get("total", 0.0)))
                        per_frame_fits_open_s.append(float(read_profile.get("fits_open", 0.0)))
                        per_frame_fits_materialize_decode_s.append(
                            float(read_profile.get("fits_materialize_decode", 0.0))
                        )
                        per_frame_fits_backend.append(str(read_profile.get("fits_reader_backend", "unknown")))
                        fallback_reason = str(read_profile.get("fits_fast_fallback_reason", "") or "")
                        if fallback_reason:
                            per_frame_fits_fallback_reason.append(fallback_reason)
                        if "fits_native_file_read_s" in read_profile:
                            per_frame_fits_native_file_read_s.append(
                                float(read_profile.get("fits_native_file_read_s", 0.0))
                            )
                        if "fits_native_decode_s" in read_profile:
                            per_frame_fits_native_decode_s.append(
                                float(read_profile.get("fits_native_decode_s", 0.0))
                            )
                        if "fits_native_total_s" in read_profile:
                            per_frame_fits_native_total_s.append(
                                float(read_profile.get("fits_native_total_s", 0.0))
                            )
                        if "fits_native_bytes_read" in read_profile:
                            per_frame_fits_native_bytes_read.append(
                                int(read_profile.get("fits_native_bytes_read", 0) or 0)
                            )
                        if bool(read_profile.get("fits_header_cache_hit", False)):
                            per_frame_fits_header_cache_hits += 1
                        per_frame_read_s.append(read_wait_elapsed)
                        invalid_mask = None
                        mask_info: dict[str, Any] = {}
                        if not source_dq_fast_skip_enabled:
                            invalid_mask, mask_info = _resident_source_invalid_mask_from_frame(
                                frame,
                                light,
                                height=height,
                                width=width,
                                plan_root=plan_root,
                                calibration_dq_sidecars=calibration_dq_sidecars,
                                resident_inline_source_dq=resident_inline_source_dq,
                                resident_inline_source_dq_hot_sigma=resident_inline_source_dq_hot_sigma,
                                resident_inline_source_dq_cold_sigma=resident_inline_source_dq_cold_sigma,
                            )
                        calibrate_start = perf_counter()
                        try:
                            if resident_h2d_mode == "pinned_async":
                                calibration_timing = stack.calibrate_frame_pinned_async_timed(
                                    index,
                                    light,
                                    float(frame.get("exposure_s") or 0.0),
                                    current_dark_exposure,
                                    asdict(policy),
                                )
                            elif resident_h2d_mode == "pinned_ring":
                                calibration_timing = stack.calibrate_frame_host_async_timed(
                                    index,
                                    light,
                                    float(frame.get("exposure_s") or 0.0),
                                    current_dark_exposure,
                                    asdict(policy),
                                )
                            else:
                                calibration_timing = stack.calibrate_frame_timed(
                                    index,
                                    light,
                                    float(frame.get("exposure_s") or 0.0),
                                    current_dark_exposure,
                                    asdict(policy),
                                )
                        finally:
                            light_prefetch.release(index)
                        if (
                            not source_dq_fast_skip_enabled
                            and (
                            resident_inline_source_dq not in {"cosmetic_cuda", "cosmetic_star_cuda"}
                            or str(mask_info.get("source_model") or "") != "none"
                            or int(mask_info.get("invalid_samples") or 0) > 0
                            )
                        ):
                            source_dq_rows.append(
                                apply_resident_source_invalid_mask(
                                    stack,
                                    frame_index=int(index),
                                    frame_id=str(frame["id"]),
                                    invalid_mask=invalid_mask,
                                    mask_info=mask_info,
                                    source="resident_calibrated_input",
                                )
                            )
                        threshold_info = _resident_source_inline_cosmetic_thresholds_from_resident_stack(
                            stack,
                            frame_index=int(index),
                            height=height,
                            width=width,
                            resident_inline_source_dq=resident_inline_source_dq,
                            resident_inline_source_dq_hot_sigma=resident_inline_source_dq_hot_sigma,
                            resident_inline_source_dq_cold_sigma=resident_inline_source_dq_cold_sigma,
                        )
                        if threshold_info is not None:
                            threshold_item = {
                                "frame_index": int(index),
                                "frame_id": str(frame["id"]),
                                "threshold_info": threshold_info,
                            }
                            if defer_inline_cosmetic_cuda_source_dq:
                                _record_inline_cosmetic_cuda_source_dq_item(threshold_item)
                            else:
                                row = apply_resident_inline_cosmetic_thresholds(
                                    stack,
                                    frame_index=int(index),
                                    frame_id=str(frame["id"]),
                                    threshold_info=threshold_info,
                                    source=f"resident_calibrated_input_{resident_inline_source_dq}",
                                    max_invalid_fraction=resident_inline_source_dq_max_invalid_fraction,
                                )
                                row["application_order"] = "calibration_pre_registration"
                                source_dq_rows.append(row)
                        per_frame_calibrate_s.append(perf_counter() - calibrate_start)
                        per_frame_host_copy_s.append(float(calibration_timing.get("host_copy_s", 0.0)))
                        per_frame_h2d_s.append(float(calibration_timing.get("h2d_s", 0.0)))
                        per_frame_calibrate_store_s.append(float(calibration_timing.get("calibrate_store_s", 0.0)))
                        calibration_event_modes.append(str(calibration_timing.get("event_mode", "unknown")))
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
                                    preview_dx, preview_dy = estimate_translation_phase_correlation(
                                        reference_preview, preview
                                    )
                                    dx = float(preview_dx * preview_scale)
                                    dy = float(preview_dy * preview_scale)
                                    _apply_deferred_inline_cosmetic_cuda_source_dq(
                                        stack,
                                        [index],
                                        source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                                    )
                                    stack.apply_translation_frame(index, int(round(dx)), int(round(dy)), np.nan)
                                    warped_frame_indices.add(index)
                                else:
                                    status = "reference"
                            except Exception as exc:
                                status = "failed"
                                frame_weight = 0.0
                                warnings.append(str(exc))
                            registration_elapsed = perf_counter() - registration_frame_start
                            registration_during_load_elapsed += registration_elapsed
                            per_frame_registration_s.append(registration_elapsed)
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
                            gc_start = perf_counter()
                            gc.collect()
                            gc_elapsed += perf_counter() - gc_start
                prefetch_fill_blocked_no_slot_count = int(light_prefetch.fill_blocked_no_slot_count)
                prefetch_release_count = int(light_prefetch.release_count)
                prefetch_max_inflight_slots = int(light_prefetch.max_inflight_slots)
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
                                resident_ncc_sample_stride,
                            )
                            refined = stack.estimate_translation_subpixel_to_reference(
                                reference_index,
                                index,
                                float(coarse["dx"]),
                                float(coarse["dy"]),
                                resident_subpixel_radius_steps,
                                resident_subpixel_step,
                                resident_ncc_sample_stride,
                            )
                            fallback_used = False
                            original_refined = refined
                            original_score = float(refined["score"])
                            if (
                                resident_ncc_sample_stride > 1
                                and resident_ncc_fallback_score_threshold > 0.0
                                and original_score <= resident_ncc_fallback_score_threshold
                            ):
                                coarse = stack.estimate_translation_to_reference(
                                    reference_index,
                                    index,
                                    resident_registration_max_shift,
                                    resident_registration_max_shift,
                                    1,
                                )
                                refined = stack.estimate_translation_subpixel_to_reference(
                                    reference_index,
                                    index,
                                    float(coarse["dx"]),
                                    float(coarse["dy"]),
                                    resident_subpixel_radius_steps,
                                    resident_subpixel_step,
                                    1,
                                )
                                fallback_used = True
                            dx = float(refined["dx"])
                            dy = float(refined["dy"])
                            score = float(refined["score"])
                            _apply_deferred_inline_cosmetic_cuda_source_dq(
                                stack,
                                [index],
                                source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                            )
                            stack.apply_translation_bilinear_frame(index, dx, dy, np.nan)
                            warped_frame_indices.add(index)
                            warnings.extend(
                                [
                                    f"coarse_dx={int(coarse['dx'])}",
                                    f"coarse_dy={int(coarse['dy'])}",
                                    f"coarse_score={float(coarse['score']):.6g}",
                                    f"subpixel_score={score:.6g}",
                                    f"ncc_sample_stride={resident_ncc_sample_stride}",
                                ]
                            )
                            if fallback_used:
                                warnings.extend(
                                    [
                                        "ncc_fallback_stride=1",
                                        (
                                            "ncc_fallback_reason="
                                            f"score_below_{resident_ncc_fallback_score_threshold:.6g}"
                                        ),
                                        f"ncc_original_dx={float(original_refined['dx']):.6g}",
                                        f"ncc_original_dy={float(original_refined['dy']):.6g}",
                                        f"ncc_original_score={original_score:.6g}",
                                        f"ncc_fallback_coarse_dx={int(coarse['dx'])}",
                                        f"ncc_fallback_coarse_dy={int(coarse['dy'])}",
                                        f"ncc_fallback_coarse_score={float(coarse['score']):.6g}",
                                        f"ncc_fallback_subpixel_score={score:.6g}",
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

            if resident_registration == "translation_star_catalog":
                if not hasattr(stack, "estimate_translation_from_stars_to_reference"):
                    raise RuntimeError("resident CUDA backend does not expose star-catalog registration")
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    dx = 0.0
                    dy = 0.0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                            inliers = 1
                            rms_px = 0.0
                        else:
                            prior_dx = 0.0
                            prior_dy = 0.0
                            prior_radius = -1.0
                            prior_warnings: list[str] = []
                            if resident_star_prior == "ncc":
                                if not hasattr(stack, "estimate_translation_to_reference") or not hasattr(
                                    stack,
                                    "estimate_translation_subpixel_to_reference",
                                ):
                                    raise RuntimeError("resident star NCC prior requires resident NCC registration")
                                coarse = stack.estimate_translation_to_reference(
                                    reference_index,
                                    index,
                                    resident_registration_max_shift,
                                    resident_registration_max_shift,
                                    resident_ncc_sample_stride,
                                )
                                refined_prior = stack.estimate_translation_subpixel_to_reference(
                                    reference_index,
                                    index,
                                    float(coarse["dx"]),
                                    float(coarse["dy"]),
                                    resident_subpixel_radius_steps,
                                    resident_subpixel_step,
                                    resident_ncc_sample_stride,
                                )
                                prior_dx = float(refined_prior["dx"])
                                prior_dy = float(refined_prior["dy"])
                                prior_radius = float(resident_star_prior_radius_px)
                                prior_warnings.extend(
                                    [
                                        "star_prior_model=ncc",
                                        f"star_prior_dx={prior_dx:.6g}",
                                        f"star_prior_dy={prior_dy:.6g}",
                                        f"star_prior_radius_px={prior_radius:.6g}",
                                        f"star_prior_coarse_score={float(coarse['score']):.6g}",
                                        f"star_prior_subpixel_score={float(refined_prior['score']):.6g}",
                                        f"star_prior_ncc_sample_stride={resident_ncc_sample_stride}",
                                    ]
                                )
                            threshold_candidates, threshold_mode = _resident_star_threshold_candidates(
                                stack,
                                reference_index,
                                index,
                                resident_star_threshold,
                            )
                            trial_results = []
                            result = None
                            for threshold in threshold_candidates:
                                trial = stack.estimate_translation_from_stars_to_reference(
                                    reference_index,
                                    index,
                                    threshold,
                                    resident_star_max_candidates,
                                    resident_star_tolerance_px,
                                    float(resident_registration_max_shift),
                                    float(resident_registration_max_shift),
                                    prior_dx,
                                    prior_dy,
                                    prior_radius,
                                    resident_star_grid_cols,
                                    resident_star_grid_rows,
                                )
                                trial_results.append(trial)
                                if result is None or _resident_star_registration_score(
                                    trial
                                ) > _resident_star_registration_score(result):
                                    result = trial
                            if result is None:
                                raise RuntimeError("resident star-catalog registration produced no threshold trials")
                            dx = float(result["refined_dx"])
                            dy = float(result["refined_dy"])
                            inliers = int(result["mutual_inliers"])
                            rms_px = float(result["rms_px"])
                            if inliers <= 0:
                                status = "failed"
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append("resident star-catalog registration found no mutual inliers")
                            else:
                                _apply_deferred_inline_cosmetic_cuda_source_dq(
                                    stack,
                                    [index],
                                    source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                                )
                                stack.apply_translation_bilinear_frame(index, dx, dy, np.nan)
                                warped_frame_indices.add(index)
                            warnings.extend(
                                [
                                    f"star_threshold_mode={threshold_mode}",
                                    f"selected_star_threshold={float(result['threshold']):.6g}",
                                    "star_threshold_candidates="
                                    + ",".join(f"{float(item):.6g}" for item in threshold_candidates),
                                    f"reference_stars={int(result['reference_count'])}",
                                    f"moving_stars={int(result['moving_count'])}",
                                    f"candidate_count={int(result['candidate_count'])}",
                                    f"candidate_selection={result['candidate_selection']}",
                                    f"raw_dx={float(result['dx']):.6g}",
                                    f"raw_dy={float(result['dy']):.6g}",
                                ]
                                + prior_warnings
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
                            transform_model="translation_star_catalog",
                            matrix=translation_matrix(dx, dy),
                            matched_stars=inliers,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"star_max_candidates={resident_star_max_candidates}",
                                f"star_tolerance_px={resident_star_tolerance_px}",
                                "resident GPU star-catalog translation; similarity/affine not yet implemented",
                            ],
                        )
                    )

            if resident_registration == "similarity_cuda_catalog":
                required_methods = [
                    "star_top_candidates",
                    "refine_matrix_translation_candidates_to_reference",
                    resident_matrix_warp_method,
                ]
                missing_methods = [name for name in required_methods if not hasattr(stack, name)]
                if missing_methods:
                    raise RuntimeError(
                        "resident CUDA backend lacks similarity registration primitive(s): "
                        + ", ".join(missing_methods)
                    )
                if not hasattr(cuda_module, "estimate_similarity_from_catalogs_f32"):
                    raise RuntimeError("CUDA backend lacks catalog similarity fitting")

                tolerance_px = _policy_float(
                    registration_policy,
                    "cuda_catalog_tolerance_px",
                    resident_star_tolerance_px,
                )
                default_min_pair_distance = max(8.0, float(min(height, width)) / 48.0)
                min_pair_distance = _policy_float(
                    registration_policy,
                    "cuda_catalog_min_pair_distance",
                    default_min_pair_distance,
                )
                similarity_top_k = max(0, _policy_int(registration_policy, "cuda_catalog_similarity_top_k", 8))
                min_scale = _policy_optional_float(registration_policy, "cuda_catalog_min_scale", 0.995)
                max_scale = _policy_optional_float(registration_policy, "cuda_catalog_max_scale", 1.005)
                max_abs_rotation_rad = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_max_abs_rotation_rad",
                    0.01,
                )
                pierside_same_similarity_top_k = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_pierside_same_similarity_top_k",
                        similarity_top_k,
                    ),
                )
                pierside_flip_similarity_top_k = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_pierside_flip_similarity_top_k",
                        max(similarity_top_k, 64),
                    ),
                )
                pierside_same_max_abs_rotation_rad = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_pierside_same_max_abs_rotation_rad",
                    max_abs_rotation_rad,
                )
                pierside_flip_max_abs_rotation_rad = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_pierside_flip_max_abs_rotation_rad",
                    3.2,
                )
                refine_kwargs = {
                    "search_radius_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_radius",
                        1.0,
                    ),
                    "coarse_step_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_coarse_step",
                        0.25,
                    ),
                    "fine_radius_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_fine_radius",
                        0.25,
                    ),
                    "fine_step_px": _policy_float(
                        registration_policy,
                        "cuda_catalog_pixel_refine_fine_step",
                        0.0625,
                    ),
                    "coarse_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_catalog_pixel_refine_coarse_stride",
                        resident_ncc_sample_stride,
                    ),
                    "final_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_catalog_pixel_refine_final_stride",
                        1,
                    ),
                }
                nms_min_separation_px = _policy_float(
                    registration_policy,
                    "cuda_catalog_nms_min_separation_px",
                    max(32.0, float(min(height, width)) / 100.0),
                )
                nms_scan_candidates = _policy_int(
                    registration_policy,
                    "cuda_catalog_nms_scan_candidates",
                    max(resident_star_max_candidates, resident_star_max_candidates * 4),
                )
                grid_top_candidates_per_cell = _policy_int(
                    registration_policy,
                    "cuda_catalog_grid_top_per_cell",
                    4,
                )
                native_stack = getattr(stack, "_impl", stack)
                has_top_nms_catalog = hasattr(native_stack, "star_top_nms_candidates")
                has_top_nms_catalog_centroid = hasattr(native_stack, "star_top_nms_candidates_centroid")
                has_grid_nms_catalog = hasattr(native_stack, "star_grid_top_nms_candidates")
                has_grid_nms_catalog_deterministic = hasattr(
                    native_stack,
                    "star_grid_top_nms_candidates_deterministic",
                )
                has_star_core_metrics = hasattr(native_stack, "star_core_metrics_candidates_to_reference")
                use_grid_catalog = (
                    resident_star_grid_cols > 0
                    and resident_star_grid_rows > 0
                    and has_grid_nms_catalog
                    and (not resident_star_catalog_deterministic or has_grid_nms_catalog_deterministic)
                )
                star_core_preselect_top_k = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_star_core_preselect_top_k",
                        resident_star_core_preselect_top_k,
                    ),
                )
                star_core_guard_enabled = _policy_bool(
                    registration_policy,
                    "cuda_catalog_star_core_guard",
                    star_core_preselect_top_k > 0,
                )
                min_pixel_ncc = _policy_optional_float(
                    registration_policy,
                    "cuda_catalog_min_pixel_ncc",
                    None,
                )
                min_selected_seed_inliers = max(
                    0,
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_min_selected_seed_inliers",
                        0,
                    ),
                )
                catalog_selector = (
                    "resident_grid_top_nms"
                    if use_grid_catalog
                    else "resident_top_nms"
                    if has_top_nms_catalog
                    else "resident_top_flux"
                )

                def detect_resident_catalog(
                    frame_index: int,
                    threshold: float,
                    _stack=stack,
                ) -> dict[str, Any]:
                    if use_grid_catalog:
                        return _stack.star_grid_top_nms_candidates(
                            frame_index,
                            threshold,
                            resident_star_grid_cols,
                            resident_star_grid_rows,
                            grid_top_candidates_per_cell,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                            deterministic=resident_star_catalog_deterministic,
                        )
                    if has_top_nms_catalog:
                        if triangle_centroid_refine_enabled and has_top_nms_catalog_centroid:
                            return _stack.star_top_nms_candidates_centroid(
                                frame_index,
                                threshold,
                                nms_scan_candidates,
                                resident_star_max_candidates,
                                nms_min_separation_px,
                                triangle_centroid_refine_radius,
                            )
                        return _stack.star_top_nms_candidates(
                            frame_index,
                            threshold,
                            nms_scan_candidates,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    return _stack.star_top_candidates(frame_index, threshold, resident_star_max_candidates)

                reference_catalogs: dict[float, dict[str, Any]] = {}
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                            matched = 1
                            inliers = 1
                            rms_px = 0.0
                        else:
                            dispatch = _resident_similarity_frame_dispatch(
                                resident_star_prior,
                                reference_frame,
                                frame,
                                header_cache,
                            )
                            frame_star_prior = str(dispatch["prior"])
                            orientation_mode = str(dispatch["orientation_mode"])
                            frame_similarity_top_k = similarity_top_k
                            frame_max_abs_rotation_rad = max_abs_rotation_rad
                            if resident_star_prior == "auto_pierside":
                                if orientation_mode == "pierside_flipped":
                                    frame_similarity_top_k = pierside_flip_similarity_top_k
                                    frame_max_abs_rotation_rad = pierside_flip_max_abs_rotation_rad
                                elif orientation_mode == "pierside_same":
                                    frame_similarity_top_k = pierside_same_similarity_top_k
                                    frame_max_abs_rotation_rad = pierside_same_max_abs_rotation_rad
                            prior_dx = 0.0
                            prior_dy = 0.0
                            prior_radius = -1.0
                            prior_warnings: list[str] = []
                            prior_warnings.extend(
                                [
                                    f"similarity_prior_requested={resident_star_prior}",
                                    f"similarity_prior_effective={frame_star_prior}",
                                    f"similarity_orientation_mode={orientation_mode}",
                                    "similarity_reference_pierside="
                                    + str(dispatch.get("reference_pierside") or "unknown"),
                                    "similarity_frame_pierside="
                                    + str(dispatch.get("moving_pierside") or "unknown"),
                                    f"similarity_frame_top_k={frame_similarity_top_k}",
                                    "similarity_frame_max_abs_rotation_rad="
                                    + str(frame_max_abs_rotation_rad),
                                ]
                            )
                            if frame_star_prior == "ncc":
                                if not hasattr(stack, "estimate_translation_to_reference") or not hasattr(
                                    stack,
                                    "estimate_translation_subpixel_to_reference",
                                ):
                                    raise RuntimeError("resident similarity NCC prior requires resident NCC registration")
                                coarse = stack.estimate_translation_to_reference(
                                    reference_index,
                                    index,
                                    resident_registration_max_shift,
                                    resident_registration_max_shift,
                                    resident_ncc_sample_stride,
                                )
                                refined_prior = stack.estimate_translation_subpixel_to_reference(
                                    reference_index,
                                    index,
                                    float(coarse["dx"]),
                                    float(coarse["dy"]),
                                    resident_subpixel_radius_steps,
                                    resident_subpixel_step,
                                    resident_ncc_sample_stride,
                                )
                                prior_dx = float(refined_prior["dx"])
                                prior_dy = float(refined_prior["dy"])
                                prior_radius = float(resident_star_prior_radius_px)
                                prior_warnings.extend(
                                    [
                                        "similarity_prior_model=ncc",
                                        f"similarity_prior_dx={prior_dx:.6g}",
                                        f"similarity_prior_dy={prior_dy:.6g}",
                                        f"similarity_prior_radius_px={prior_radius:.6g}",
                                        f"similarity_prior_coarse_score={float(coarse['score']):.6g}",
                                        f"similarity_prior_subpixel_score={float(refined_prior['score']):.6g}",
                                    ]
                                )
                            else:
                                prior_warnings.append("similarity_prior_model=none")

                            threshold_candidates, threshold_mode = _resident_star_threshold_candidates(
                                stack,
                                reference_index,
                                index,
                                resident_star_threshold,
                            )
                            trial_results = []
                            selected_fit = None
                            selected_threshold = None
                            selected_reference_catalog = None
                            selected_moving_catalog = None
                            for threshold in threshold_candidates:
                                threshold_key = round(float(threshold), 6)
                                reference_catalog = reference_catalogs.get(threshold_key)
                                if reference_catalog is None:
                                    reference_catalog = detect_resident_catalog(reference_index, threshold)
                                    reference_catalogs[threshold_key] = reference_catalog
                                moving_catalog = detect_resident_catalog(index, threshold)
                                if int(reference_catalog["stored_count"]) < 2 or int(moving_catalog["stored_count"]) < 2:
                                    trial_results.append(
                                        {
                                            "threshold": float(threshold),
                                            "status": "too_few_stars",
                                            "reference_stored": int(reference_catalog["stored_count"]),
                                            "moving_stored": int(moving_catalog["stored_count"]),
                                        }
                                    )
                                    continue
                                fit = cuda_module.estimate_similarity_from_catalogs_f32(
                                    reference_catalog["x"],
                                    reference_catalog["y"],
                                    moving_catalog["x"],
                                    moving_catalog["y"],
                                    tolerance_px=tolerance_px,
                                    min_pair_distance=min_pair_distance,
                                    prior_dx=prior_dx,
                                    prior_dy=prior_dy,
                                    prior_radius_px=prior_radius,
                                    min_scale=min_scale,
                                    max_scale=max_scale,
                                    max_abs_rotation_rad=frame_max_abs_rotation_rad,
                                    top_k=frame_similarity_top_k,
                                )
                                trial_results.append(
                                    {
                                        "threshold": float(threshold),
                                        "status": str(fit.get("status", "failed")),
                                        "inliers": int(fit.get("refined_inliers", fit.get("inliers", 0))),
                                        "rms_px": _float_or_nan(fit.get("refit_rms_px", fit.get("rms_px"))),
                                        "reference_stored": int(reference_catalog["stored_count"]),
                                        "moving_stored": int(moving_catalog["stored_count"]),
                                        "top_candidate_count": len(fit.get("top_candidates", [])),
                                    }
                                )
                                if str(fit.get("status")) != "ok":
                                    continue
                                if selected_fit is None or _resident_similarity_score(fit) > _resident_similarity_score(
                                    selected_fit
                                ):
                                    selected_fit = fit
                                    selected_threshold = float(threshold)
                                    selected_reference_catalog = reference_catalog
                                    selected_moving_catalog = moving_catalog

                            if selected_fit is None:
                                status = "failed"
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append("resident similarity catalog registration found no accepted fit")
                            else:
                                seeds: list[dict[str, Any]] = [
                                    {
                                        "seed_rank": 0,
                                        "seed_source": "catalog_similarity_refit",
                                        "candidate_index": None,
                                        "inliers": int(
                                            selected_fit.get(
                                                "refined_inliers",
                                                selected_fit.get("inliers", 0),
                                            )
                                        ),
                                        "rms_px": _finite_float_or_none(
                                            selected_fit.get("refit_rms_px", selected_fit.get("rms_px"))
                                        ),
                                        "matrix": np.asarray(selected_fit["matrix"], dtype=np.float32)
                                        .reshape(3, 3)
                                        .tolist(),
                                    }
                                ]
                                for seed_rank, candidate in enumerate(selected_fit.get("top_candidates", []), start=1):
                                    seeds.append(
                                        {
                                            "seed_rank": seed_rank,
                                            "seed_source": "catalog_similarity_top_candidate",
                                            "candidate_index": int(candidate.get("candidate_index", seed_rank - 1)),
                                            "inliers": int(candidate.get("inliers", 0)),
                                            "rms_px": _finite_float_or_none(candidate.get("rms_px")),
                                            "matrix": np.asarray(candidate["matrix"], dtype=np.float32)
                                            .reshape(3, 3)
                                            .tolist(),
                                        }
                                    )
                                selected_seed_indices = list(range(len(seeds)))
                                preselection: dict[str, Any] = {
                                    "enabled": False,
                                    "requested_top_k": int(star_core_preselect_top_k),
                                    "input_seed_count": len(seeds),
                                    "selected_seed_count": len(seeds),
                                    "selected_seed_indices": selected_seed_indices,
                                    "selection_key": "disabled",
                                }
                                pre_refine_metric_summary: dict[str, Any] | None = None
                                star_core_threshold = _policy_float(
                                    registration_policy,
                                    "cuda_catalog_star_core_threshold",
                                    float(selected_threshold or threshold_candidates[0]),
                                )
                                if 0 < star_core_preselect_top_k < len(seeds):
                                    if has_star_core_metrics:
                                        prescreen_seed_metrics = [
                                            {
                                                "seed_index": seed_index,
                                                "seed_rank": int(seed["seed_rank"]),
                                                "seed_source": str(seed["seed_source"]),
                                                "candidate_index": seed["candidate_index"],
                                                "seed_inliers": seed["inliers"],
                                                "seed_rms_px": seed["rms_px"],
                                                "matrix": np.asarray(seed["matrix"], dtype=np.float32)
                                                .reshape(3, 3)
                                                .tolist(),
                                            }
                                            for seed_index, seed in enumerate(seeds)
                                        ]
                                        pre_refine_metric_summary = _annotate_resident_star_core_metrics(
                                            stack,
                                            reference_index,
                                            index,
                                            prescreen_seed_metrics,
                                            star_core_threshold,
                                        )
                                        selected_seed_indices, preselection = _select_star_core_preselected_seed_indices(
                                            prescreen_seed_metrics,
                                            star_core_preselect_top_k,
                                        )
                                    else:
                                        preselection = {
                                            **preselection,
                                            "enabled": False,
                                            "selection_key": "native_star_core_metric_unavailable",
                                        }
                                seed_matrices = [
                                    np.asarray(seeds[seed_index]["matrix"], dtype=np.float32).reshape(3, 3)
                                    for seed_index in selected_seed_indices
                                ]
                                refinement = stack.refine_matrix_translation_candidates_to_reference(
                                    reference_index,
                                    index,
                                    np.asarray(seed_matrices, dtype=np.float32),
                                    **refine_kwargs,
                                )
                                seed_metrics: list[dict[str, Any]] = []
                                for seed_result in refinement.get("seed_results", []):
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
                                            "matrix": np.asarray(seed_result["matrix"], dtype=np.float32)
                                            .reshape(3, 3)
                                            .tolist(),
                                        }
                                    )
                                pixel_selected_index = int(refinement["selected_index"])
                                selected_metric_index = pixel_selected_index
                                star_guard = {
                                    "status": "disabled",
                                    "pixel_selected_index": pixel_selected_index,
                                    "selected_index": pixel_selected_index,
                                    "selection_key": "disabled",
                                }
                                star_core_metric_summary: dict[str, Any] | None = None
                                if star_core_guard_enabled and has_star_core_metrics and seed_metrics:
                                    star_core_metric_summary = _annotate_resident_star_core_metrics(
                                        stack,
                                        reference_index,
                                        index,
                                        seed_metrics,
                                        star_core_threshold,
                                    )
                                    selected_metric_index, star_guard = _select_star_guarded_seed(
                                        seed_metrics,
                                        pixel_selected_index,
                                    )
                                selected_seed_metric = (
                                    seed_metrics[selected_metric_index]
                                    if seed_metrics
                                    else {
                                        "seed_index": pixel_selected_index,
                                        "refine_seed_index": pixel_selected_index,
                                        "seed_rank": pixel_selected_index,
                                        "seed_source": "pixel_metric",
                                        "candidate_index": None,
                                        "seed_inliers": None,
                                        "seed_rms_px": None,
                                        "matrix": refinement["matrix"],
                                        "metrics": dict(refinement["metrics"]),
                                    }
                                )
                                matrix = np.asarray(selected_seed_metric["matrix"], dtype=np.float32).tolist()
                                matched = int(selected_fit.get("inliers", 0))
                                inliers = int(selected_fit.get("refined_inliers", matched))
                                rms_px = _float_or_nan(selected_fit.get("refit_rms_px", selected_fit.get("rms_px")))
                                selected_metrics = dict(selected_seed_metric["metrics"])
                                selected_pixel_ncc = _float_or_nan(selected_metrics.get("ncc"))
                                selected_pixel_rms = _float_or_nan(selected_metrics.get("rms"))
                                selected_seed_inliers = selected_seed_metric.get("seed_inliers")
                                quality_failures: list[str] = []
                                if min_pixel_ncc is not None and (
                                    not np.isfinite(selected_pixel_ncc) or selected_pixel_ncc < float(min_pixel_ncc)
                                ):
                                    quality_failures.append(
                                        f"pixel_ncc {selected_pixel_ncc:.6g} < {float(min_pixel_ncc):.6g}"
                                    )
                                if (
                                    min_selected_seed_inliers > 0
                                    and selected_seed_inliers is not None
                                    and int(selected_seed_inliers) < min_selected_seed_inliers
                                ):
                                    quality_failures.append(
                                        f"selected_seed_inliers {int(selected_seed_inliers)} < "
                                        f"{min_selected_seed_inliers}"
                                    )
                                if quality_failures:
                                    status = "failed"
                                    frame_weight_values[index] = 0.0
                                    frame_weights[frame["id"]] = 0.0
                                    warnings.append(
                                        "resident similarity registration failed quality gate: "
                                        + "; ".join(quality_failures)
                                    )
                                else:
                                    _apply_deferred_inline_cosmetic_cuda_source_dq(
                                        stack,
                                        [index],
                                        source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                                    )
                                    warp_model = _apply_resident_registration_matrix(
                                        stack,
                                        index,
                                        matrix,
                                        resident_warp_interpolation,
                                        resident_warp_clamping_threshold,
                                    )
                                    warped_frame_indices.add(index)
                                    warnings.append(f"resident_registration_application={warp_model}")
                                warnings.extend(
                                    [
                                        f"similarity_threshold_mode={threshold_mode}",
                                        f"selected_similarity_threshold={float(selected_threshold or 0.0):.6g}",
                                        "similarity_threshold_candidates="
                                        + ",".join(f"{float(item):.6g}" for item in threshold_candidates),
                                        f"reference_stars={int(selected_reference_catalog['stored_count'])}",
                                        f"moving_stars={int(selected_moving_catalog['stored_count'])}",
                                        f"similarity_top_k={int(selected_fit.get('top_k', frame_similarity_top_k))}",
                                        "similarity_max_abs_rotation_rad="
                                        + str(frame_max_abs_rotation_rad),
                                        f"similarity_top_candidate_count={len(selected_fit.get('top_candidates', []))}",
                                        f"similarity_seed_count={int(refinement['seed_count'])}",
                                        f"similarity_refined_seed_count={len(selected_seed_indices)}",
                                        f"similarity_selected_refine_seed={int(refinement['selected_index'])}",
                                        f"similarity_selected_seed={int(selected_seed_metric['seed_index'])}",
                                        f"similarity_selected_seed_rank={int(selected_seed_metric['seed_rank'])}",
                                        f"similarity_pixel_selected_seed={pixel_selected_index}",
                                        f"similarity_scale={float(selected_fit.get('scale', float('nan'))):.9g}",
                                        f"similarity_rotation_rad={float(selected_fit.get('rotation_rad', float('nan'))):.9g}",
                                        f"similarity_fit_rms_px={rms_px:.6g}",
                                        f"similarity_pixel_rms_adu={selected_pixel_rms:.6g}",
                                        f"similarity_pixel_ncc={selected_pixel_ncc:.6g}",
                                        "similarity_quality_gate_status="
                                        + ("failed" if quality_failures else "ok"),
                                        f"similarity_min_pixel_ncc={min_pixel_ncc}",
                                        f"similarity_min_selected_seed_inliers={min_selected_seed_inliers}",
                                        f"similarity_catalog_selector={catalog_selector}",
                                        f"similarity_nms_min_separation_px={nms_min_separation_px:.6g}",
                                        f"similarity_star_core_preselect_enabled={bool(preselection.get('enabled', False))}",
                                        f"similarity_star_core_preselect_requested_top_k={star_core_preselect_top_k}",
                                        f"similarity_star_core_preselect_selected_seed_count={int(preselection.get('selected_seed_count', len(selected_seed_indices)))}",
                                        "similarity_star_core_preselect_indices="
                                        + ",".join(str(int(item)) for item in preselection.get("selected_seed_indices", [])),
                                        f"similarity_star_core_guard_enabled={bool(star_core_guard_enabled and has_star_core_metrics)}",
                                        f"similarity_star_core_guard_status={star_guard['status']}",
                                        f"similarity_star_core_threshold={star_core_threshold:.6g}",
                                        "resident CUDA catalog similarity with multi-seed pixel refinement",
                                    ]
                                    + prior_warnings
                                )
                                if pre_refine_metric_summary is not None:
                                    warnings.append(
                                        "similarity_star_core_pre_refine_summary="
                                        + str(pre_refine_metric_summary)
                                    )
                                if star_core_metric_summary is not None:
                                    warnings.append(
                                        "similarity_star_core_guard_summary=" + str(star_core_metric_summary)
                                    )
                            warnings.append("similarity_trials=" + str(trial_results))
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
                            transform_model="similarity_cuda_catalog",
                            matrix=matrix,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"star_max_candidates={resident_star_max_candidates}",
                                f"star_tolerance_px={resident_star_tolerance_px}",
                                "resident GPU similarity catalog registration",
                            ],
                        )
                    )

            if resident_registration == "similarity_cuda_triangle":
                required_methods = [
                    "star_top_candidates",
                    resident_matrix_warp_method,
                ]
                missing_methods = [name for name in required_methods if not hasattr(stack, name)]
                if missing_methods:
                    raise RuntimeError(
                        "resident CUDA backend lacks triangle registration primitive(s): "
                        + ", ".join(missing_methods)
                    )
                required_cuda = [
                    "estimate_similarity_from_triangle_descriptors_f32",
                    "triangle_asterism_descriptors_f32",
                ]
                missing_cuda = [name for name in required_cuda if not hasattr(cuda_module, name)]
                if missing_cuda:
                    raise RuntimeError(
                        "CUDA backend lacks triangle descriptor primitive(s): "
                        + ", ".join(missing_cuda)
                    )

                tolerance_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_tolerance_px",
                    _policy_float(registration_policy, "cuda_catalog_tolerance_px", resident_star_tolerance_px),
                )
                descriptor_radius = _policy_float(registration_policy, "cuda_triangle_descriptor_radius", 0.1)
                descriptor_neighbors = _policy_int(registration_policy, "cuda_triangle_neighbors", 5)
                max_descriptors = _policy_int(registration_policy, "cuda_triangle_max_descriptors", 1200)
                nms_min_separation_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_nms_min_separation_px",
                    _policy_float(
                        registration_policy,
                        "cuda_catalog_nms_min_separation_px",
                        max(32.0, float(min(height, width)) / 100.0),
                    ),
                )
                nms_scan_candidates = _policy_int(
                    registration_policy,
                    "cuda_triangle_nms_scan_candidates",
                    _policy_int(
                        registration_policy,
                        "cuda_catalog_nms_scan_candidates",
                        max(resident_star_max_candidates, resident_star_max_candidates * 4),
                    ),
                )
                if resident_triangle_nms_scan_candidates is not None:
                    nms_scan_candidates = int(resident_triangle_nms_scan_candidates)
                grid_top_candidates_per_cell = _policy_int(
                    registration_policy,
                    "cuda_triangle_grid_top_per_cell",
                    _policy_int(registration_policy, "cuda_catalog_grid_top_per_cell", 4),
                )
                if resident_triangle_grid_top_per_cell is not None:
                    grid_top_candidates_per_cell = int(resident_triangle_grid_top_per_cell)
                if resident_triangle_nms_min_separation_px is not None:
                    nms_min_separation_px = float(resident_triangle_nms_min_separation_px)
                refine_kwargs = {
                    "search_radius_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_radius",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_radius", 1.0),
                    ),
                    "coarse_step_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_coarse_step",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_coarse_step", 0.25),
                    ),
                    "fine_radius_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_fine_radius",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_fine_radius", 0.25),
                    ),
                    "fine_step_px": _policy_float(
                        registration_policy,
                        "cuda_triangle_pixel_refine_fine_step",
                        _policy_float(registration_policy, "cuda_catalog_pixel_refine_fine_step", 0.0625),
                    ),
                    "coarse_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_triangle_pixel_refine_coarse_stride",
                        _policy_int(
                            registration_policy,
                            "cuda_catalog_pixel_refine_coarse_stride",
                            resident_ncc_sample_stride,
                        ),
                    ),
                    "final_sample_stride": _policy_int(
                        registration_policy,
                        "cuda_triangle_pixel_refine_final_stride",
                        _policy_int(registration_policy, "cuda_catalog_pixel_refine_final_stride", 1),
                    ),
                }
                if resident_triangle_pixel_refine_coarse_stride is not None:
                    refine_kwargs["coarse_sample_stride"] = int(resident_triangle_pixel_refine_coarse_stride)
                if resident_triangle_pixel_refine_final_stride is not None:
                    refine_kwargs["final_sample_stride"] = int(resident_triangle_pixel_refine_final_stride)
                triangle_pixel_refine_requested_coarse_stride = int(refine_kwargs["coarse_sample_stride"])
                triangle_pixel_refine_requested_final_stride = int(refine_kwargs["final_sample_stride"])
                triangle_pixel_refine_fast_coarse_enabled = bool(
                    resident_triangle_pixel_refine_fast_coarse
                    or _policy_bool(registration_policy, "cuda_triangle_pixel_refine_fast_coarse", False)
                )
                triangle_pixel_refine_fast_coarse_mode = "off"
                triangle_pixel_refine_coarse_stride_adjusted = False
                if triangle_pixel_refine_fast_coarse_enabled:
                    fast_coarse_stride = max(
                        triangle_pixel_refine_requested_coarse_stride,
                        triangle_pixel_refine_requested_final_stride,
                    )
                    triangle_pixel_refine_coarse_stride_adjusted = (
                        fast_coarse_stride != triangle_pixel_refine_requested_coarse_stride
                    )
                    refine_kwargs["coarse_sample_stride"] = fast_coarse_stride
                    triangle_pixel_refine_fast_coarse_mode = "coarse_stride_floor_to_final"
                min_pixel_ncc = _policy_optional_float(
                    registration_policy,
                    "cuda_triangle_min_pixel_ncc",
                    _policy_optional_float(registration_policy, "cuda_catalog_min_pixel_ncc", None),
                )
                min_agreement_score = _policy_optional_float(
                    registration_policy,
                    "cuda_triangle_min_agreement_score",
                    None,
                )
                if resident_triangle_min_agreement_score is not None:
                    min_agreement_score = float(resident_triangle_min_agreement_score)
                triangle_agreement_rms_scale = _policy_float(
                    registration_policy,
                    "cuda_triangle_agreement_rms_scale",
                    200.0,
                )
                if resident_triangle_agreement_rms_scale is not None:
                    triangle_agreement_rms_scale = float(resident_triangle_agreement_rms_scale)
                if triangle_agreement_rms_scale <= 0.0:
                    raise ValueError("cuda_triangle_agreement_rms_scale must be positive")
                if min_agreement_score is not None and (
                    min_agreement_score < 0.0 or min_agreement_score > 1.0
                ):
                    raise ValueError("cuda_triangle_min_agreement_score must be in [0, 1]")
                triangle_agreement_action = str(
                    registration_policy.get("cuda_triangle_agreement_action") or "fail"
                )
                if resident_triangle_agreement_action is not None:
                    triangle_agreement_action = str(resident_triangle_agreement_action)
                if triangle_agreement_action not in {"fail", "downweight", "flag"}:
                    raise ValueError("cuda_triangle_agreement_action must be fail, downweight, or flag")
                triangle_agreement_min_weight = _policy_float(
                    registration_policy,
                    "cuda_triangle_agreement_min_weight",
                    0.0,
                )
                if resident_triangle_agreement_min_weight is not None:
                    triangle_agreement_min_weight = float(resident_triangle_agreement_min_weight)
                if triangle_agreement_min_weight < 0.0 or triangle_agreement_min_weight > 1.0:
                    raise ValueError("cuda_triangle_agreement_min_weight must be in [0, 1]")
                pixel_refine_enabled = _policy_bool(
                    registration_policy,
                    "cuda_triangle_pixel_refine",
                    _DEFAULT_CUDA_TRIANGLE_PIXEL_REFINE,
                )
                plan_transform_model = str(registration_policy.get("transform_model") or "translation")
                triangle_translation_refine_policy_source = (
                    "plan"
                    if "cuda_triangle_translation_refine" in registration_policy
                    else "default_similarity_triangle_off"
                )
                triangle_translation_refine_enabled = _policy_bool(
                    registration_policy,
                    "cuda_triangle_translation_refine",
                    False,
                )
                triangle_translation_refine_tolerance_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_translation_refine_tolerance_px",
                    tolerance_px,
                )
                triangle_translation_refine_min_inliers = _policy_int(
                    registration_policy,
                    "cuda_triangle_translation_refine_min_inliers",
                    _policy_int(registration_policy, "min_inliers", 6),
                )
                triangle_translation_refine_max_correction_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_translation_refine_max_correction_px",
                    0.25,
                )
                triangle_translation_refine_iterations = _policy_int(
                    registration_policy,
                    "cuda_triangle_translation_refine_iterations",
                    2,
                )
                triangle_translation_refine_iteration_max_step_px = _policy_float(
                    registration_policy,
                    "cuda_triangle_translation_refine_iteration_max_step_px",
                    0.005,
                )
                triangle_centroid_refine_enabled = _policy_bool(
                    registration_policy,
                    "cuda_triangle_centroid_refine",
                    True,
                )
                triangle_centroid_refine_radius = _policy_int(
                    registration_policy,
                    "cuda_triangle_centroid_refine_radius",
                    4,
                )
                triangle_centroid_background_mode = str(
                    registration_policy.get("cuda_triangle_centroid_background") or "global_mean"
                )
                if resident_triangle_centroid_background is not None:
                    triangle_centroid_background_mode = str(resident_triangle_centroid_background)
                if triangle_translation_refine_tolerance_px <= 0.0:
                    raise ValueError("cuda_triangle_translation_refine_tolerance_px must be positive")
                if triangle_translation_refine_min_inliers <= 0:
                    raise ValueError("cuda_triangle_translation_refine_min_inliers must be positive")
                if triangle_translation_refine_max_correction_px <= 0.0:
                    raise ValueError("cuda_triangle_translation_refine_max_correction_px must be positive")
                if triangle_translation_refine_iterations < 0:
                    raise ValueError("cuda_triangle_translation_refine_iterations must be non-negative")
                if triangle_translation_refine_iteration_max_step_px < 0.0:
                    raise ValueError("cuda_triangle_translation_refine_iteration_max_step_px must be non-negative")
                if triangle_centroid_refine_radius <= 0:
                    raise ValueError("cuda_triangle_centroid_refine_radius must be positive")
                if triangle_centroid_background_mode not in {"local_median", "global_mean"}:
                    raise ValueError("cuda_triangle_centroid_background must be local_median or global_mean")
                native_stack = getattr(stack, "_impl", stack)
                has_top_nms_catalog = hasattr(native_stack, "star_top_nms_candidates")
                has_top_nms_catalog_centroid = hasattr(native_stack, "star_top_nms_candidates_centroid")
                has_grid_nms_catalog = hasattr(native_stack, "star_grid_top_nms_candidates")
                has_grid_nms_catalog_deterministic = hasattr(
                    native_stack,
                    "star_grid_top_nms_candidates_deterministic",
                )
                has_grid_nms_catalog_centroid = hasattr(native_stack, "star_grid_top_nms_candidates_centroid")
                has_grid_nms_catalog_deterministic_centroid = hasattr(
                    native_stack,
                    "star_grid_top_nms_candidates_deterministic_centroid",
                )
                triangle_star_grid_cols = int(resident_star_grid_cols)
                triangle_star_grid_rows = int(resident_star_grid_rows)
                triangle_star_catalog_deterministic = bool(resident_star_catalog_deterministic)
                triangle_catalog_grid_auto = False
                if (
                    triangle_star_grid_cols <= 0
                    and triangle_star_grid_rows <= 0
                    and has_grid_nms_catalog
                    and (
                        has_grid_nms_catalog_centroid
                        or has_grid_nms_catalog_deterministic_centroid
                        or not triangle_centroid_refine_enabled
                    )
                ):
                    triangle_star_grid_cols = _policy_int(
                        registration_policy,
                        "cuda_triangle_auto_grid_cols",
                        _policy_int(registration_policy, "cuda_catalog_auto_grid_cols", 8),
                    )
                    triangle_star_grid_rows = _policy_int(
                        registration_policy,
                        "cuda_triangle_auto_grid_rows",
                        _policy_int(registration_policy, "cuda_catalog_auto_grid_rows", 8),
                    )
                    if triangle_star_grid_cols <= 0 or triangle_star_grid_rows <= 0:
                        raise ValueError("cuda_triangle_auto_grid_cols/rows must be positive")
                    triangle_star_catalog_deterministic = _policy_bool(
                        registration_policy,
                        "cuda_triangle_auto_grid_deterministic",
                        _policy_bool(registration_policy, "cuda_catalog_auto_grid_deterministic", True),
                    )
                    triangle_catalog_grid_auto = True
                    if (
                        resident_triangle_grid_top_per_cell is None
                        and "cuda_triangle_grid_top_per_cell" not in registration_policy
                        and "cuda_catalog_grid_top_per_cell" not in registration_policy
                    ):
                        grid_top_candidates_per_cell = _policy_int(
                            registration_policy,
                            "cuda_triangle_auto_grid_top_per_cell",
                            _policy_int(registration_policy, "cuda_catalog_auto_grid_top_per_cell", 8),
                        )
                        if grid_top_candidates_per_cell <= 0:
                            raise ValueError("cuda_triangle_auto_grid_top_per_cell must be positive")
                use_grid_catalog = (
                    triangle_star_grid_cols > 0
                    and triangle_star_grid_rows > 0
                    and has_grid_nms_catalog
                    and (not triangle_star_catalog_deterministic or has_grid_nms_catalog_deterministic)
                )
                triangle_catalog_batch_enabled = bool(
                    use_grid_catalog
                    and resident_star_threshold > 0.0
                    and (
                        (
                            triangle_centroid_refine_enabled
                            and hasattr(native_stack, "star_grid_top_nms_candidates_batch_centroid")
                        )
                        or (
                            not triangle_centroid_refine_enabled
                            and hasattr(native_stack, "star_grid_top_nms_candidates_batch")
                        )
                    )
                    and (
                        not triangle_star_catalog_deterministic
                        or (
                            triangle_centroid_refine_enabled
                            and hasattr(native_stack, "star_grid_top_nms_candidates_batch_deterministic_centroid")
                        )
                        or (
                            not triangle_centroid_refine_enabled
                            and hasattr(native_stack, "star_grid_top_nms_candidates_batch_deterministic")
                        )
                    )
                )
                triangle_catalog_batch_mode = (
                    "grid_top_nms_fixed_threshold" if triangle_catalog_batch_enabled else "off"
                )
                triangle_catalog_timing_model = "off"
                triangle_catalog_native_enqueue_s = 0.0
                triangle_catalog_native_sync_s = 0.0
                triangle_catalog_native_count_download_s = 0.0
                triangle_catalog_native_output_download_s = 0.0
                triangle_catalog_native_centroid_refine_s = 0.0
                triangle_catalog_native_total_s = 0.0
                triangle_catalog_batch_size = 0
                triangle_catalog_stream_limit = 0
                triangle_catalog_stream_count = 0
                triangle_catalog_batch_sync_count = 0
                triangle_catalog_sync_phase_count = 0
                triangle_catalog_download_mode = "off"
                triangle_catalog_workspace_layout = "off"
                triangle_catalog_grid_workspace_allocation_count = 0
                triangle_catalog_output_workspace_allocation_count = 0
                triangle_catalog_output_download_copy_count = 0
                triangle_catalog_centroid_before_download_copy_count = 0
                triangle_catalog_output_download_bytes = 0
                triangle_catalog_centroid_mean_sync_mode = "off"
                triangle_catalog_centroid_mean_blocks = 0
                triangle_catalog_sort_mode = "off"
                triangle_catalog_topk_mode = "off"
                triangle_pixel_refine_batch_enabled = bool(
                    pixel_refine_enabled
                    and hasattr(native_stack, "refine_matrix_translation_candidates_batch_to_reference")
                )
                triangle_pixel_refine_batch_mode = (
                    "native_batch_one_seed_per_frame"
                    if triangle_pixel_refine_batch_enabled
                    else "per_frame"
                    if pixel_refine_enabled
                    else "off"
                )
                triangle_pixel_refine_workspace_mode = "off"
                triangle_pixel_refine_workspace_bytes = 0
                triangle_pixel_refine_workspace_candidate_capacity = 0
                triangle_pixel_refine_batch_metric_mode = "off"
                triangle_pixel_refine_batch_metric_kernel_launches = 0
                triangle_pixel_refine_coarse_total_candidates = 0
                triangle_pixel_refine_fine_total_candidates = 0
                triangle_pixel_refine_metric_workload_model = "off"
                triangle_pixel_refine_coarse_sampled_pixels_per_candidate = 0
                triangle_pixel_refine_fine_sampled_pixels_per_candidate = 0
                triangle_pixel_refine_coarse_metric_sample_evaluations = 0
                triangle_pixel_refine_fine_metric_sample_evaluations = 0
                triangle_pixel_refine_coarse_metric_megasamples_per_s = 0.0
                triangle_pixel_refine_fine_metric_megasamples_per_s = 0.0
                triangle_pixel_refine_native_coarse_s = 0.0
                triangle_pixel_refine_native_fine_s = 0.0
                triangle_translation_refine_applied_count = 0
                triangle_translation_refine_skipped_count = 0
                triangle_translation_refine_rejected_count = 0
                triangle_translation_refine_max_correction_px_observed = 0.0
                triangle_translation_refine_max_rms_px = 0.0
                triangle_translation_refine_max_iterations_observed = 0
                triangle_centroid_refine_catalog_count = 0
                triangle_centroid_refine_star_count = 0
                triangle_centroid_refine_failed_star_count = 0
                triangle_centroid_refine_max_shift_px = 0.0
                triangle_descriptor_fit_batch_enabled = bool(
                    triangle_catalog_batch_enabled
                    and hasattr(cuda_module, "estimate_similarity_from_triangle_descriptors_batch_f32")
                )
                triangle_descriptor_fit_batch_mode = (
                    "native_batch_shared_reference_device"
                    if triangle_descriptor_fit_batch_enabled
                    else "per_frame"
                )
                triangle_descriptor_fit_reference_device_reuse = False
                triangle_descriptor_fit_reference_device_bytes = 0
                triangle_descriptor_fit_moving_device_reuse = False
                triangle_descriptor_fit_moving_device_bytes = 0
                triangle_descriptor_fit_output_device_reuse = False
                triangle_descriptor_fit_output_device_bytes = 0
                triangle_descriptor_fit_best_reduction_mode = "off"
                triangle_descriptor_fit_batch_timing_model = "off"
                triangle_descriptor_fit_native_host_prepare_s = 0.0
                triangle_descriptor_fit_native_reference_alloc_s = 0.0
                triangle_descriptor_fit_native_reference_upload_s = 0.0
                triangle_descriptor_fit_native_workspace_alloc_s = 0.0
                triangle_descriptor_fit_native_moving_upload_s = 0.0
                triangle_descriptor_fit_native_kernel_sync_s = 0.0
                triangle_descriptor_fit_native_output_download_s = 0.0
                triangle_descriptor_fit_native_frame_total_s = 0.0
                triangle_descriptor_fit_native_total_s = 0.0
                triangle_descriptor_generation_batch_enabled = bool(
                    triangle_catalog_batch_enabled
                    and hasattr(cuda_module, "triangle_asterism_descriptors_batch_f32")
                )
                triangle_descriptor_generation_batch_mode = (
                    "native_batch_padded_catalog_one_sync"
                    if triangle_descriptor_generation_batch_enabled
                    else "per_frame"
                )
                triangle_descriptor_generation_batch_call_count = 0
                triangle_descriptor_generation_batch_size = 0
                triangle_descriptor_generation_batch_timing_model = "off"
                triangle_descriptor_generation_batch_upload_s = 0.0
                triangle_descriptor_generation_batch_kernel_sync_s = 0.0
                triangle_descriptor_generation_batch_output_download_s = 0.0
                triangle_fused_matrix_deferred_enabled = resident_integration_dispatch == "fused_matrix"
                triangle_fused_matrix_deferred_count = 0
                triangle_warp_batch_available = bool(
                    (
                        resident_warp_interpolation == "bilinear"
                        and hasattr(native_stack, "apply_matrix_bilinear_frames")
                    )
                    or (
                        resident_warp_interpolation == "lanczos3"
                        and hasattr(native_stack, "apply_matrix_lanczos3_frames")
                    )
                )
                triangle_warp_batch_enabled = bool(
                    triangle_warp_batch_available and not triangle_fused_matrix_deferred_enabled
                )
                if triangle_fused_matrix_deferred_enabled:
                    triangle_warp_batch_mode = "fused_matrix_deferred"
                    triangle_warp_batch_timing_model = "fused_integration_deferred"
                else:
                    triangle_warp_batch_mode = (
                        f"native_matrix_{resident_warp_interpolation}_frames"
                        if triangle_warp_batch_enabled
                        else "per_frame"
                    )
                    triangle_warp_batch_timing_model = "off"
                triangle_warp_batch_frame_count = 0
                triangle_warp_batch_fallback_frame_count = 0
                triangle_warp_batch_native_inverse_upload_mode = "off"
                triangle_warp_batch_native_inverse_prepare_s = 0.0
                triangle_warp_batch_native_inverse_batch_alloc_s = 0.0
                triangle_warp_batch_native_inverse_batch_bytes = 0
                triangle_warp_batch_native_index_upload_s = 0.0
                triangle_warp_batch_native_index_upload_count = 0
                triangle_warp_batch_native_inverse_upload_s = 0.0
                triangle_warp_batch_native_inverse_upload_count = 0
                triangle_warp_batch_native_chunk_metadata_upload_mode = "off"
                triangle_warp_batch_native_kernel_enqueue_s = 0.0
                triangle_warp_batch_native_coverage_reduce_enqueue_s = 0.0
                triangle_warp_batch_native_scatter_enqueue_s = 0.0
                triangle_warp_batch_native_postprocess_enqueue_s = 0.0
                triangle_warp_batch_native_postprocess_mode = "off"
                triangle_warp_batch_native_lanczos3_clamping_enabled: bool | None = None
                triangle_warp_batch_native_lanczos3_clamp_path = "off"
                triangle_warp_batch_native_device_copy_enqueue_s = 0.0
                triangle_warp_batch_native_sync_s = 0.0
                triangle_warp_batch_native_total_s = 0.0
                triangle_warp_batch_native_chunk_frames = 0
                triangle_warp_batch_native_chunk_count = 0
                triangle_warp_batch_native_workspace_bytes = 0
                triangle_warp_batch_native_output_bytes = 0
                triangle_warp_batch_native_coverage_bytes = 0
                triangle_warp_batch_native_max_chunk_capacity_frames = 0
                triangle_warp_batch_native_capacity_source = "off"
                triangle_warp_batch_native_warp_kernel_launches = 0
                triangle_warp_batch_native_coverage_reduce_kernel_launches = 0
                triangle_warp_batch_native_scatter_kernel_launches = 0
                triangle_warp_batch_native_postprocess_kernel_launches = 0
                triangle_warp_batch_capacity_source = (
                    "resident_memory_admission"
                    if resident_warp_chunk_capacity_effective is not None
                    else "native_preferred"
                )
                catalog_selector = (
                    "resident_grid_top_nms"
                    if use_grid_catalog
                    else "resident_top_nms"
                    if has_top_nms_catalog
                    else "resident_top_flux"
                )

                def detect_resident_triangle_catalog(
                    frame_index: int,
                    threshold: float,
                    _stack=stack,
                ) -> dict[str, Any]:
                    if use_grid_catalog:
                        if triangle_centroid_refine_enabled:
                            if triangle_star_catalog_deterministic and has_grid_nms_catalog_deterministic_centroid:
                                return _stack.star_grid_top_nms_candidates_deterministic_centroid(
                                    frame_index,
                                    threshold,
                                    triangle_star_grid_cols,
                                    triangle_star_grid_rows,
                                    grid_top_candidates_per_cell,
                                    resident_star_max_candidates,
                                    nms_min_separation_px,
                                    triangle_centroid_refine_radius,
                                    triangle_centroid_background_mode,
                                )
                            if (not triangle_star_catalog_deterministic) and has_grid_nms_catalog_centroid:
                                return _stack.star_grid_top_nms_candidates_centroid(
                                    frame_index,
                                    threshold,
                                    triangle_star_grid_cols,
                                    triangle_star_grid_rows,
                                    grid_top_candidates_per_cell,
                                    resident_star_max_candidates,
                                    nms_min_separation_px,
                                    triangle_centroid_refine_radius,
                                    triangle_centroid_background_mode,
                                )
                        return _stack.star_grid_top_nms_candidates(
                            frame_index,
                            threshold,
                            triangle_star_grid_cols,
                            triangle_star_grid_rows,
                            grid_top_candidates_per_cell,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                            deterministic=triangle_star_catalog_deterministic,
                        )
                    if has_top_nms_catalog:
                        if triangle_centroid_refine_enabled and has_top_nms_catalog_centroid:
                            return _stack.star_top_nms_candidates_centroid(
                                frame_index,
                                threshold,
                                nms_scan_candidates,
                                resident_star_max_candidates,
                                nms_min_separation_px,
                                triangle_centroid_refine_radius,
                                triangle_centroid_background_mode,
                            )
                        return _stack.star_top_nms_candidates(
                            frame_index,
                            threshold,
                            nms_scan_candidates,
                            resident_star_max_candidates,
                            nms_min_separation_px,
                        )
                    return _stack.star_top_candidates(frame_index, threshold, resident_star_max_candidates)

                def triangle_descriptors(catalog: dict[str, Any]) -> dict[str, Any]:
                    return cuda_module.triangle_asterism_descriptors_f32(
                        catalog["x"],
                        catalog["y"],
                        max_stars=resident_star_max_candidates,
                        neighbors=descriptor_neighbors,
                        max_descriptors=max_descriptors,
                    )

                reference_catalogs: dict[float, dict[str, Any]] = {}
                reference_descriptors: dict[float, dict[str, Any]] = {}
                moving_catalog_batch_cache: dict[float, dict[int, dict[str, Any]]] = {}
                moving_descriptor_batch_cache: dict[float, dict[int, dict[str, Any]]] = {}
                descriptor_fit_batch_cache: dict[float, dict[int, dict[str, Any]]] = {}
                centroid_refine_cache: dict[tuple[int, float], tuple[dict[str, Any] | None, dict[str, Any]]] = {}
                pending_triangle_pixel_refines: list[dict[str, Any]] = []
                triangle_determinism_signatures: dict[str, Any] = {
                    "schema_version": 1,
                    "signature_mode": "catalog_descriptor_fit_exact_float32_sha256",
                    "hash_algorithm": "sha256",
                    "thresholds": {},
                    "moving": {},
                }
                moving_catalog_batch_indices = [
                    frame_index
                    for frame_index, frame in enumerate(light_frames)
                    if frame_index != reference_index and not _matches_any_token(frame, excluded_tokens)
                ]

                def detect_resident_triangle_moving_catalog(
                    frame_index: int,
                    threshold: float,
                    _stack=stack,
                ) -> dict[str, Any]:
                    nonlocal triangle_catalog_native_count_download_s
                    nonlocal triangle_catalog_native_centroid_refine_s
                    nonlocal triangle_catalog_native_enqueue_s
                    nonlocal triangle_catalog_native_output_download_s
                    nonlocal triangle_catalog_native_sync_s
                    nonlocal triangle_catalog_native_total_s
                    nonlocal triangle_catalog_batch_size
                    nonlocal triangle_catalog_stream_limit
                    nonlocal triangle_catalog_stream_count
                    nonlocal triangle_catalog_batch_sync_count
                    nonlocal triangle_catalog_sync_phase_count
                    nonlocal triangle_catalog_download_mode
                    nonlocal triangle_catalog_workspace_layout
                    nonlocal triangle_catalog_grid_workspace_allocation_count
                    nonlocal triangle_catalog_output_workspace_allocation_count
                    nonlocal triangle_catalog_output_download_copy_count
                    nonlocal triangle_catalog_centroid_before_download_copy_count
                    nonlocal triangle_catalog_output_download_bytes
                    nonlocal triangle_catalog_centroid_mean_sync_mode
                    nonlocal triangle_catalog_centroid_mean_blocks
                    nonlocal triangle_catalog_sort_mode
                    nonlocal triangle_catalog_topk_mode
                    nonlocal triangle_catalog_timing_model
                    threshold_key = round(float(threshold), 6)
                    if triangle_catalog_batch_enabled:
                        cached_by_index = moving_catalog_batch_cache.get(threshold_key)
                        if cached_by_index is None:
                            batch_start = perf_counter()
                            if triangle_centroid_refine_enabled and triangle_star_catalog_deterministic:
                                batch_results = _stack.star_grid_top_nms_candidates_batch_deterministic_centroid(
                                    moving_catalog_batch_indices,
                                    threshold,
                                    triangle_star_grid_cols,
                                    triangle_star_grid_rows,
                                    grid_top_candidates_per_cell,
                                    resident_star_max_candidates,
                                    nms_min_separation_px,
                                    triangle_centroid_refine_radius,
                                    triangle_centroid_background_mode,
                                )
                            elif triangle_centroid_refine_enabled:
                                batch_results = _stack.star_grid_top_nms_candidates_batch_centroid(
                                    moving_catalog_batch_indices,
                                    threshold,
                                    triangle_star_grid_cols,
                                    triangle_star_grid_rows,
                                    grid_top_candidates_per_cell,
                                    resident_star_max_candidates,
                                    nms_min_separation_px,
                                    triangle_centroid_refine_radius,
                                    triangle_centroid_background_mode,
                                )
                            else:
                                batch_results = _stack.star_grid_top_nms_candidates_batch(
                                    moving_catalog_batch_indices,
                                    threshold,
                                    triangle_star_grid_cols,
                                    triangle_star_grid_rows,
                                    grid_top_candidates_per_cell,
                                    resident_star_max_candidates,
                                    nms_min_separation_px,
                                    deterministic=triangle_star_catalog_deterministic,
                                )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_moving_catalog_batch",
                                perf_counter() - batch_start,
                            )
                            if batch_results:
                                triangle_catalog_timing_model = str(
                                    batch_results[0].get("catalog_timing_model", "unavailable")
                                )
                                triangle_catalog_sort_mode = str(
                                    batch_results[0].get("catalog_sort_mode", "unavailable")
                                )
                                triangle_catalog_topk_mode = str(
                                    batch_results[0].get("catalog_topk_mode", "unavailable")
                                )
                                triangle_catalog_batch_size = max(
                                    int(item.get("catalog_batch_size", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_stream_limit = max(
                                    int(item.get("catalog_stream_limit", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_stream_count = max(
                                    int(item.get("catalog_stream_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_batch_sync_count = max(
                                    int(item.get("catalog_batch_sync_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_sync_phase_count = max(
                                    int(item.get("catalog_sync_phase_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_download_mode = str(
                                    batch_results[0].get("catalog_download_mode", "unavailable")
                                )
                                triangle_catalog_workspace_layout = str(
                                    batch_results[0].get("catalog_workspace_layout", "unavailable")
                                )
                                triangle_catalog_grid_workspace_allocation_count = max(
                                    int(item.get("catalog_grid_workspace_allocation_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_output_workspace_allocation_count = max(
                                    int(item.get("catalog_output_workspace_allocation_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_output_download_copy_count = max(
                                    int(item.get("catalog_output_download_copy_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_centroid_before_download_copy_count = max(
                                    int(item.get("catalog_centroid_before_download_copy_count", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_output_download_bytes = max(
                                    int(item.get("catalog_output_download_bytes", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_centroid_mean_sync_mode = str(
                                    batch_results[0].get("catalog_centroid_mean_sync_mode", "off")
                                )
                                triangle_catalog_centroid_mean_blocks = max(
                                    int(item.get("catalog_centroid_mean_blocks", 0) or 0)
                                    for item in batch_results
                                )
                                triangle_catalog_native_enqueue_s = sum(
                                    float(item.get("catalog_enqueue_s", 0.0) or 0.0)
                                    for item in batch_results
                                )
                                triangle_catalog_native_sync_s = sum(
                                    float(item.get("catalog_sync_s", 0.0) or 0.0)
                                    for item in batch_results
                                )
                                triangle_catalog_native_count_download_s = sum(
                                    float(item.get("catalog_count_download_s", 0.0) or 0.0)
                                    for item in batch_results
                                )
                                triangle_catalog_native_output_download_s = sum(
                                    float(item.get("catalog_output_download_s", 0.0) or 0.0)
                                    for item in batch_results
                                )
                                triangle_catalog_native_centroid_refine_s = sum(
                                    float(item.get("catalog_centroid_refine_s", 0.0) or 0.0)
                                    for item in batch_results
                                )
                                triangle_catalog_native_total_s = sum(
                                    float(item.get("catalog_native_s", 0.0) or 0.0)
                                    for item in batch_results
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog_native_enqueue",
                                    triangle_catalog_native_enqueue_s,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog_native_sync",
                                    triangle_catalog_native_sync_s,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog_native_count_download",
                                    triangle_catalog_native_count_download_s,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog_native_output_download",
                                    triangle_catalog_native_output_download_s,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog_native_centroid_refine",
                                    triangle_catalog_native_centroid_refine_s,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog_native_total",
                                    triangle_catalog_native_total_s,
                                )
                            cached_by_index = {int(item["frame_index"]): item for item in batch_results}
                            moving_catalog_batch_cache[threshold_key] = cached_by_index
                        cached_catalog = cached_by_index.get(frame_index)
                        if cached_catalog is not None:
                            return cached_catalog
                    return detect_resident_triangle_catalog(frame_index, threshold)

                def moving_triangle_descriptor(
                    frame_index: int,
                    threshold_key: float,
                    catalog: dict[str, Any],
                ) -> dict[str, Any]:
                    cached_by_index = moving_descriptor_batch_cache.get(threshold_key, {})
                    cached_descriptor = cached_by_index.get(frame_index)
                    if cached_descriptor is not None:
                        return cached_descriptor
                    moving_descriptor_start = perf_counter()
                    descriptor = triangle_descriptors(catalog)
                    _add_elapsed(
                        registration_component_s,
                        "triangle_moving_descriptors",
                        perf_counter() - moving_descriptor_start,
                    )
                    moving_descriptor_batch_cache.setdefault(threshold_key, {})[frame_index] = descriptor
                    return descriptor

                def centroid_refined_catalog(
                    frame_index: int,
                    threshold_key: float,
                    catalog: dict[str, Any] | None,
                ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
                    nonlocal triangle_centroid_refine_catalog_count
                    nonlocal triangle_centroid_refine_failed_star_count
                    nonlocal triangle_centroid_refine_max_shift_px
                    nonlocal triangle_centroid_refine_star_count
                    if not triangle_centroid_refine_enabled:
                        return catalog, {
                            "enabled": False,
                            "status": "disabled",
                            "refined_count": 0,
                            "failed_count": 0,
                            "max_shift_px": 0.0,
                        }
                    existing_summary = catalog.get("centroid_refine") if isinstance(catalog, dict) else None
                    if isinstance(existing_summary, dict) and existing_summary.get("enabled"):
                        summary = {
                            "enabled": True,
                            "status": "ok",
                            "refined_count": int(existing_summary.get("refined_count", 0) or 0),
                            "failed_count": int(existing_summary.get("failed_count", 0) or 0),
                            "max_shift_px": float(existing_summary.get("max_shift_px", 0.0) or 0.0),
                            "radius": int(existing_summary.get("radius", triangle_centroid_refine_radius) or 0),
                            "mode": str(existing_summary.get("mode", "resident_gpu_window_centroid")),
                            "background_mode": str(
                                existing_summary.get("background_mode", triangle_centroid_background_mode)
                            ),
                        }
                        triangle_centroid_refine_catalog_count += 1
                        triangle_centroid_refine_star_count += int(summary["refined_count"])
                        triangle_centroid_refine_failed_star_count += int(summary["failed_count"])
                        triangle_centroid_refine_max_shift_px = max(
                            triangle_centroid_refine_max_shift_px,
                            _float_or_nan(summary["max_shift_px"]),
                        )
                        return catalog, summary
                    cache_key = (int(frame_index), round(float(threshold_key), 6))
                    cached = centroid_refine_cache.get(cache_key)
                    if cached is not None:
                        return cached
                    centroid_start = perf_counter()
                    refined, summary = _resident_refine_catalog_centroids_from_stack(
                        resident_stack,
                        frame_index,
                        catalog,
                        radius=triangle_centroid_refine_radius,
                    )
                    _add_elapsed(
                        registration_component_s,
                        "triangle_centroid_refine",
                        perf_counter() - centroid_start,
                    )
                    triangle_centroid_refine_catalog_count += 1
                    triangle_centroid_refine_star_count += int(summary.get("refined_count", 0) or 0)
                    triangle_centroid_refine_failed_star_count += int(summary.get("failed_count", 0) or 0)
                    triangle_centroid_refine_max_shift_px = max(
                        triangle_centroid_refine_max_shift_px,
                        _float_or_nan(summary.get("max_shift_px")),
                    )
                    centroid_refine_cache[cache_key] = (refined, summary)
                    return refined, summary

                def triangle_descriptor_fit(
                    frame_index: int,
                    threshold: float,
                    reference_catalog: dict[str, Any],
                    reference_descriptor: dict[str, Any],
                    moving_catalog: dict[str, Any],
                    moving_descriptor: dict[str, Any],
                ) -> dict[str, Any]:
                    nonlocal triangle_descriptor_fit_reference_device_bytes
                    nonlocal triangle_descriptor_fit_reference_device_reuse
                    nonlocal triangle_descriptor_fit_moving_device_bytes
                    nonlocal triangle_descriptor_fit_moving_device_reuse
                    nonlocal triangle_descriptor_fit_output_device_bytes
                    nonlocal triangle_descriptor_fit_output_device_reuse
                    nonlocal triangle_descriptor_fit_best_reduction_mode
                    nonlocal triangle_descriptor_fit_batch_timing_model
                    nonlocal triangle_descriptor_fit_native_frame_total_s
                    nonlocal triangle_descriptor_fit_native_host_prepare_s
                    nonlocal triangle_descriptor_fit_native_kernel_sync_s
                    nonlocal triangle_descriptor_fit_native_moving_upload_s
                    nonlocal triangle_descriptor_fit_native_output_download_s
                    nonlocal triangle_descriptor_fit_native_reference_alloc_s
                    nonlocal triangle_descriptor_fit_native_reference_upload_s
                    nonlocal triangle_descriptor_fit_native_total_s
                    nonlocal triangle_descriptor_fit_native_workspace_alloc_s
                    nonlocal triangle_descriptor_generation_batch_call_count
                    nonlocal triangle_descriptor_generation_batch_kernel_sync_s
                    nonlocal triangle_descriptor_generation_batch_output_download_s
                    nonlocal triangle_descriptor_generation_batch_size
                    nonlocal triangle_descriptor_generation_batch_timing_model
                    nonlocal triangle_descriptor_generation_batch_upload_s
                    threshold_key = round(float(threshold), 6)
                    if triangle_descriptor_fit_batch_enabled:
                        cached_fits = descriptor_fit_batch_cache.get(threshold_key)
                        if cached_fits is None:
                            descriptor_by_index = moving_descriptor_batch_cache.setdefault(threshold_key, {})
                            catalogs_by_index: dict[int, dict[str, Any]] = {}
                            fit_indices: list[int] = []
                            moving_x_list: list[Any] = []
                            moving_y_list: list[Any] = []
                            moving_descriptors_list: list[Any] = []
                            moving_indices_list: list[Any] = []
                            descriptor_batch_elapsed = 0.0
                            descriptor_build_indices: list[int] = []
                            descriptor_x_list: list[Any] = []
                            descriptor_y_list: list[Any] = []
                            for moving_index in moving_catalog_batch_indices:
                                catalog = detect_resident_triangle_moving_catalog(moving_index, threshold)
                                if int(catalog["stored_count"]) < 3:
                                    continue
                                catalogs_by_index[int(moving_index)] = catalog
                                descriptor = descriptor_by_index.get(moving_index)
                                if descriptor is None:
                                    descriptor_build_indices.append(int(moving_index))
                                    descriptor_x_list.append(catalog["x"])
                                    descriptor_y_list.append(catalog["y"])
                            if descriptor_build_indices:
                                descriptor_start = perf_counter()
                                if triangle_descriptor_generation_batch_enabled:
                                    descriptor_results = cuda_module.triangle_asterism_descriptors_batch_f32(
                                        descriptor_x_list,
                                        descriptor_y_list,
                                        max_stars=resident_star_max_candidates,
                                        neighbors=descriptor_neighbors,
                                        max_descriptors=max_descriptors,
                                    )
                                else:
                                    descriptor_results = [
                                        triangle_descriptors(
                                            catalogs_by_index[int(moving_index)]
                                        )
                                        for moving_index in descriptor_build_indices
                                    ]
                                descriptor_batch_elapsed += perf_counter() - descriptor_start
                                for moving_index, descriptor in zip(
                                    descriptor_build_indices,
                                    descriptor_results,
                                    strict=True,
                                ):
                                    descriptor_by_index[int(moving_index)] = descriptor
                                triangle_descriptor_generation_batch_call_count += 1
                                triangle_descriptor_generation_batch_size = max(
                                    triangle_descriptor_generation_batch_size,
                                    len(descriptor_build_indices),
                                )
                                if descriptor_results:
                                    first_descriptor = descriptor_results[0]
                                    triangle_descriptor_generation_batch_timing_model = str(
                                        first_descriptor.get(
                                            "batch_timing_model",
                                            triangle_descriptor_generation_batch_mode,
                                        )
                                    )
                                    triangle_descriptor_generation_batch_upload_s += float(
                                        first_descriptor.get("batch_upload_s", 0.0) or 0.0
                                    )
                                    triangle_descriptor_generation_batch_kernel_sync_s += float(
                                        first_descriptor.get("batch_kernel_sync_s", 0.0) or 0.0
                                    )
                                    triangle_descriptor_generation_batch_output_download_s += float(
                                        first_descriptor.get(
                                            "batch_output_download_s",
                                            0.0,
                                        )
                                        or 0.0
                                    )
                            for moving_index in moving_catalog_batch_indices:
                                catalog = catalogs_by_index.get(int(moving_index))
                                if catalog is None:
                                    continue
                                descriptor = descriptor_by_index.get(moving_index)
                                if descriptor is None:
                                    continue
                                if int(descriptor["count"]) <= 0:
                                    continue
                                fit_indices.append(int(moving_index))
                                moving_x_list.append(catalog["x"])
                                moving_y_list.append(catalog["y"])
                                moving_descriptors_list.append(descriptor["descriptors"])
                                moving_indices_list.append(descriptor["indices"])
                            if descriptor_batch_elapsed > 0.0:
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_descriptors",
                                    descriptor_batch_elapsed,
                                )
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_descriptors_batch",
                                    descriptor_batch_elapsed,
                                )
                            fit_batch_start = perf_counter()
                            if fit_indices:
                                batch_fits = cuda_module.estimate_similarity_from_triangle_descriptors_batch_f32(
                                    reference_catalog["x"],
                                    reference_catalog["y"],
                                    reference_descriptor["descriptors"],
                                    reference_descriptor["indices"],
                                    moving_x_list,
                                    moving_y_list,
                                    moving_descriptors_list,
                                    moving_indices_list,
                                    tolerance_px=tolerance_px,
                                    descriptor_radius=descriptor_radius,
                                )
                            else:
                                batch_fits = []
                            if batch_fits:
                                triangle_descriptor_fit_best_reduction_mode = str(
                                    batch_fits[0].get("best_reduction_mode", "unavailable")
                                )
                                triangle_descriptor_fit_reference_device_reuse = bool(
                                    batch_fits[0].get("reference_device_reuse", False)
                                )
                                triangle_descriptor_fit_reference_device_bytes = int(
                                    batch_fits[0].get("reference_device_bytes", 0) or 0
                                )
                                triangle_descriptor_fit_moving_device_reuse = bool(
                                    batch_fits[0].get("moving_device_reuse", False)
                                )
                                triangle_descriptor_fit_moving_device_bytes = int(
                                    batch_fits[0].get("moving_device_bytes", 0) or 0
                                )
                                triangle_descriptor_fit_output_device_reuse = bool(
                                    batch_fits[0].get("output_device_reuse", False)
                                )
                                triangle_descriptor_fit_output_device_bytes = int(
                                    batch_fits[0].get("output_device_bytes", 0) or 0
                                )
                                triangle_descriptor_fit_batch_timing_model = str(
                                    batch_fits[0].get("batch_timing_model", "unavailable")
                                )
                                triangle_descriptor_fit_native_host_prepare_s = float(
                                    batch_fits[0].get("batch_host_prepare_s", 0.0) or 0.0
                                )
                                triangle_descriptor_fit_native_reference_alloc_s = float(
                                    batch_fits[0].get("batch_reference_alloc_s", 0.0) or 0.0
                                )
                                triangle_descriptor_fit_native_reference_upload_s = float(
                                    batch_fits[0].get("batch_reference_upload_s", 0.0) or 0.0
                                )
                                triangle_descriptor_fit_native_workspace_alloc_s = float(
                                    batch_fits[0].get("batch_workspace_alloc_s", 0.0) or 0.0
                                )
                                triangle_descriptor_fit_native_moving_upload_s = sum(
                                    float(fit.get("batch_frame_moving_upload_s", 0.0) or 0.0)
                                    for fit in batch_fits
                                )
                                triangle_descriptor_fit_native_kernel_sync_s = sum(
                                    float(fit.get("batch_frame_kernel_sync_s", 0.0) or 0.0)
                                    for fit in batch_fits
                                )
                                triangle_descriptor_fit_native_output_download_s = sum(
                                    float(fit.get("batch_frame_output_download_s", 0.0) or 0.0)
                                    for fit in batch_fits
                                )
                                triangle_descriptor_fit_native_frame_total_s = sum(
                                    float(fit.get("batch_frame_total_s", 0.0) or 0.0)
                                    for fit in batch_fits
                                )
                                triangle_descriptor_fit_native_total_s = (
                                    triangle_descriptor_fit_native_host_prepare_s
                                    + triangle_descriptor_fit_native_reference_alloc_s
                                    + triangle_descriptor_fit_native_reference_upload_s
                                    + triangle_descriptor_fit_native_workspace_alloc_s
                                    + triangle_descriptor_fit_native_frame_total_s
                                )
                            fit_batch_elapsed = perf_counter() - fit_batch_start
                            _add_elapsed(registration_component_s, "triangle_descriptor_fit", fit_batch_elapsed)
                            _add_elapsed(
                                registration_component_s,
                                "triangle_descriptor_fit_batch",
                                fit_batch_elapsed,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_descriptor_fit_native_moving_upload",
                                triangle_descriptor_fit_native_moving_upload_s,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_descriptor_fit_native_kernel_sync",
                                triangle_descriptor_fit_native_kernel_sync_s,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_descriptor_fit_native_output_download",
                                triangle_descriptor_fit_native_output_download_s,
                            )
                            cached_fits = {
                                int(index): dict(fit)
                                for index, fit in zip(fit_indices, batch_fits, strict=True)
                            }
                            descriptor_fit_batch_cache[threshold_key] = cached_fits
                        cached_fit = cached_fits.get(frame_index)
                        if cached_fit is not None:
                            return cached_fit
                    fit_start = perf_counter()
                    fit = cuda_module.estimate_similarity_from_triangle_descriptors_f32(
                        reference_catalog["x"],
                        reference_catalog["y"],
                        moving_catalog["x"],
                        moving_catalog["y"],
                        reference_descriptor["descriptors"],
                        reference_descriptor["indices"],
                        moving_descriptor["descriptors"],
                        moving_descriptor["indices"],
                        tolerance_px=tolerance_px,
                        descriptor_radius=descriptor_radius,
                    )
                    _add_elapsed(
                        registration_component_s,
                        "triangle_descriptor_fit",
                        perf_counter() - fit_start,
                    )
                    return fit

                pending_triangle_warps: list[dict[str, Any]] = []

                def apply_pending_triangle_warps(
                    items: list[dict[str, Any]],
                    _stack: Any = stack,
                ) -> None:
                    nonlocal triangle_warp_batch_fallback_frame_count
                    nonlocal triangle_warp_batch_frame_count
                    nonlocal triangle_warp_batch_native_chunk_count
                    nonlocal triangle_warp_batch_native_chunk_frames
                    nonlocal triangle_warp_batch_native_coverage_bytes
                    nonlocal triangle_warp_batch_native_coverage_reduce_enqueue_s
                    nonlocal triangle_warp_batch_native_coverage_reduce_kernel_launches
                    nonlocal triangle_warp_batch_native_device_copy_enqueue_s
                    nonlocal triangle_warp_batch_native_index_upload_s
                    nonlocal triangle_warp_batch_native_index_upload_count
                    nonlocal triangle_warp_batch_native_inverse_batch_alloc_s
                    nonlocal triangle_warp_batch_native_inverse_batch_bytes
                    nonlocal triangle_warp_batch_native_inverse_prepare_s
                    nonlocal triangle_warp_batch_native_inverse_upload_mode
                    nonlocal triangle_warp_batch_native_inverse_upload_s
                    nonlocal triangle_warp_batch_native_inverse_upload_count
                    nonlocal triangle_warp_batch_native_chunk_metadata_upload_mode
                    nonlocal triangle_warp_batch_native_kernel_enqueue_s
                    nonlocal triangle_warp_batch_native_postprocess_enqueue_s
                    nonlocal triangle_warp_batch_native_postprocess_kernel_launches
                    nonlocal triangle_warp_batch_native_postprocess_mode
                    nonlocal triangle_warp_batch_native_lanczos3_clamping_enabled
                    nonlocal triangle_warp_batch_native_lanczos3_clamp_path
                    nonlocal triangle_warp_batch_native_output_bytes
                    nonlocal triangle_warp_batch_native_capacity_source
                    nonlocal triangle_warp_batch_native_scatter_enqueue_s
                    nonlocal triangle_warp_batch_native_scatter_kernel_launches
                    nonlocal triangle_warp_batch_native_sync_s
                    nonlocal triangle_warp_batch_native_total_s
                    nonlocal triangle_warp_batch_native_max_chunk_capacity_frames
                    nonlocal triangle_warp_batch_native_warp_kernel_launches
                    nonlocal triangle_warp_batch_native_workspace_bytes
                    nonlocal triangle_warp_batch_timing_model
                    if not items:
                        return
                    _apply_deferred_inline_cosmetic_cuda_source_dq(
                        _stack,
                        [int(item["index"]) for item in items],
                        source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                    )
                    warp_start = perf_counter()
                    warp_models, warp_timing = _apply_resident_registration_matrix_batch(
                        _stack,
                        [
                            (int(item["index"]), item["matrix"])
                            for item in items
                        ],
                        resident_warp_interpolation,
                        resident_warp_clamping_threshold,
                        resident_warp_batch_dispatch,
                        resident_warp_chunk_capacity_effective,
                        resident_track_warp_coverage,
                    )
                    warp_elapsed = perf_counter() - warp_start
                    _add_elapsed(registration_component_s, "triangle_warp", warp_elapsed)
                    if bool(warp_timing.get("batched", False)):
                        triangle_warp_batch_timing_model = str(
                            warp_timing.get("timing_model", "unavailable")
                        )
                        triangle_warp_batch_frame_count += int(warp_timing.get("frame_count", 0) or 0)
                        triangle_warp_batch_fallback_frame_count += int(
                            warp_timing.get("fallback_frame_count", 0) or 0
                        )
                        triangle_warp_batch_native_inverse_upload_mode = str(
                            warp_timing.get("inverse_upload_mode", "unavailable")
                        )
                        triangle_warp_batch_native_inverse_prepare_s += float(
                            warp_timing.get("inverse_prepare_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_inverse_batch_alloc_s += float(
                            warp_timing.get("inverse_batch_alloc_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_inverse_batch_bytes += int(
                            warp_timing.get("inverse_batch_bytes", 0) or 0
                        )
                        if warp_timing.get("chunk_metadata_upload_mode") is not None:
                            triangle_warp_batch_native_chunk_metadata_upload_mode = str(
                                warp_timing.get("chunk_metadata_upload_mode")
                            )
                        triangle_warp_batch_native_index_upload_s += float(
                            warp_timing.get("index_upload_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_index_upload_count += int(
                            warp_timing.get("index_upload_count", 0) or 0
                        )
                        triangle_warp_batch_native_inverse_upload_s += float(
                            warp_timing.get("inverse_upload_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_inverse_upload_count += int(
                            warp_timing.get("inverse_upload_count", 0) or 0
                        )
                        triangle_warp_batch_native_kernel_enqueue_s += float(
                            warp_timing.get("kernel_enqueue_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_coverage_reduce_enqueue_s += float(
                            warp_timing.get("coverage_reduce_enqueue_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_scatter_enqueue_s += float(
                            warp_timing.get("scatter_enqueue_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_postprocess_enqueue_s += float(
                            warp_timing.get("postprocess_enqueue_s", 0.0) or 0.0
                        )
                        if warp_timing.get("postprocess_mode") is not None:
                            triangle_warp_batch_native_postprocess_mode = str(
                                warp_timing.get("postprocess_mode")
                            )
                        if warp_timing.get("lanczos3_clamping_enabled") is not None:
                            triangle_warp_batch_native_lanczos3_clamping_enabled = bool(
                                warp_timing.get("lanczos3_clamping_enabled")
                            )
                        if warp_timing.get("lanczos3_clamp_path") is not None:
                            triangle_warp_batch_native_lanczos3_clamp_path = str(
                                warp_timing.get("lanczos3_clamp_path")
                            )
                        triangle_warp_batch_native_device_copy_enqueue_s += float(
                            warp_timing.get("device_copy_enqueue_s", 0.0) or 0.0
                        )
                        triangle_warp_batch_native_sync_s += float(warp_timing.get("sync_s", 0.0) or 0.0)
                        triangle_warp_batch_native_total_s += float(warp_timing.get("total_s", 0.0) or 0.0)
                        triangle_warp_batch_native_chunk_frames = max(
                            triangle_warp_batch_native_chunk_frames,
                            int(warp_timing.get("batch_chunk_frames", 0) or 0),
                        )
                        triangle_warp_batch_native_chunk_count += int(
                            warp_timing.get("batch_chunk_count", 0) or 0
                        )
                        if warp_timing.get("batch_capacity_source") is not None:
                            triangle_warp_batch_native_capacity_source = str(
                                warp_timing.get("batch_capacity_source")
                            )
                        triangle_warp_batch_native_max_chunk_capacity_frames = max(
                            triangle_warp_batch_native_max_chunk_capacity_frames,
                            int(warp_timing.get("batch_max_chunk_capacity_frames", 0) or 0),
                        )
                        triangle_warp_batch_native_workspace_bytes = max(
                            triangle_warp_batch_native_workspace_bytes,
                            int(warp_timing.get("batch_workspace_bytes", 0) or 0),
                        )
                        triangle_warp_batch_native_output_bytes = max(
                            triangle_warp_batch_native_output_bytes,
                            int(warp_timing.get("batch_output_bytes", 0) or 0),
                        )
                        triangle_warp_batch_native_coverage_bytes = max(
                            triangle_warp_batch_native_coverage_bytes,
                            int(warp_timing.get("batch_coverage_bytes", 0) or 0),
                        )
                        triangle_warp_batch_native_warp_kernel_launches += int(
                            warp_timing.get("warp_kernel_launches", 0) or 0
                        )
                        triangle_warp_batch_native_coverage_reduce_kernel_launches += int(
                            warp_timing.get("coverage_reduce_kernel_launches", 0) or 0
                        )
                        triangle_warp_batch_native_scatter_kernel_launches += int(
                            warp_timing.get("scatter_kernel_launches", 0) or 0
                        )
                        triangle_warp_batch_native_postprocess_kernel_launches += int(
                            warp_timing.get("postprocess_kernel_launches", 0) or 0
                        )
                        _add_elapsed(
                            registration_component_s,
                            "triangle_warp_native_batch",
                            float(warp_timing.get("total_s", warp_elapsed) or 0.0),
                        )
                        _add_elapsed(
                            registration_component_s,
                            "triangle_warp_native_sync",
                            float(warp_timing.get("sync_s", 0.0) or 0.0),
                        )
                    else:
                        triangle_warp_batch_fallback_frame_count += int(
                            warp_timing.get("fallback_frame_count", len(items)) or 0
                        )
                    for item, warp_model in zip(items, warp_models, strict=True):
                        frame_index = int(item["index"])
                        warped_frame_indices.add(frame_index)
                        registration_results[int(item["result_index"])].warnings.extend(
                            [
                                f"resident_registration_application={warp_model}",
                                "triangle_warp_batch=" + str(bool(warp_timing.get("batched", False))).lower(),
                                f"triangle_warp_batch_mode={triangle_warp_batch_mode}",
                                f"triangle_warp_batch_dispatch={resident_warp_batch_dispatch}",
                                "triangle_warp_coverage_tracking="
                                + str(bool(resident_track_warp_coverage)).lower(),
                                "triangle_warp_batch_timing_model="
                                + str(warp_timing.get("timing_model", "per_frame")),
                                "triangle_warp_batch_inverse_upload_mode="
                                + str(warp_timing.get("inverse_upload_mode", "per_frame")),
                                "triangle_warp_batch_chunk_frames="
                                + str(int(warp_timing.get("batch_chunk_frames", 0) or 0)),
                            ]
                        )

                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    matrix = translation_matrix(0.0, 0.0)
                    matched = 0
                    inliers = 0
                    rms_px = float("nan")
                    deferred_triangle_refine: dict[str, Any] | None = None
                    pending_triangle_warp_matrix: list[list[float]] | None = None
                    quality_decision: dict[str, Any] | None = None
                    triangle_quality_diagnostics: dict[str, Any] = {}
                    try:
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif frame["id"] == reference_frame["id"]:
                            status = "reference"
                            matched = 1
                            inliers = 1
                            rms_px = 0.0
                        else:
                            threshold_start = perf_counter()
                            threshold_candidates, threshold_mode = _resident_star_threshold_candidates(
                                stack,
                                reference_index,
                                index,
                                resident_star_threshold,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_threshold_select",
                                perf_counter() - threshold_start,
                            )
                            trial_results = []
                            selected_fit = None
                            selected_threshold = None
                            selected_reference_catalog = None
                            selected_moving_catalog = None
                            selected_reference_descriptors = None
                            selected_moving_descriptors = None
                            for threshold in threshold_candidates:
                                threshold_key = round(float(threshold), 6)
                                reference_catalog = reference_catalogs.get(threshold_key)
                                if reference_catalog is None:
                                    reference_catalog_start = perf_counter()
                                    reference_catalog = detect_resident_triangle_catalog(reference_index, threshold)
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_reference_catalog",
                                        perf_counter() - reference_catalog_start,
                                    )
                                    reference_catalogs[threshold_key] = reference_catalog
                                moving_catalog_start = perf_counter()
                                moving_catalog = detect_resident_triangle_moving_catalog(index, threshold)
                                _add_elapsed(
                                    registration_component_s,
                                    "triangle_moving_catalog",
                                    perf_counter() - moving_catalog_start,
                                )
                                if int(reference_catalog["stored_count"]) < 3 or int(moving_catalog["stored_count"]) < 3:
                                    trial_results.append(
                                        {
                                            "threshold": float(threshold),
                                            "status": "too_few_stars",
                                            "reference_stored": int(reference_catalog["stored_count"]),
                                            "moving_stored": int(moving_catalog["stored_count"]),
                                        }
                                    )
                                    continue
                                reference_descriptor = reference_descriptors.get(threshold_key)
                                if reference_descriptor is None:
                                    reference_descriptor_start = perf_counter()
                                    reference_descriptor = triangle_descriptors(reference_catalog)
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_reference_descriptors",
                                        perf_counter() - reference_descriptor_start,
                                    )
                                    reference_descriptors[threshold_key] = reference_descriptor
                                threshold_signature = triangle_determinism_signatures["thresholds"].setdefault(
                                    f"{threshold_key:.6f}",
                                    {},
                                )
                                threshold_signature.setdefault(
                                    "reference_catalog",
                                    _resident_catalog_signature(reference_catalog),
                                )
                                threshold_signature.setdefault(
                                    "reference_descriptor",
                                    _resident_descriptor_signature(reference_descriptor),
                                )
                                moving_descriptor = moving_triangle_descriptor(
                                    index,
                                    threshold_key,
                                    moving_catalog,
                                )
                                if (
                                    int(reference_descriptor["count"]) <= 0
                                    or int(moving_descriptor["count"]) <= 0
                                ):
                                    trial_results.append(
                                        {
                                            "threshold": float(threshold),
                                            "status": "too_few_descriptors",
                                            "reference_descriptors": int(reference_descriptor["count"]),
                                            "moving_descriptors": int(moving_descriptor["count"]),
                                        }
                                    )
                                    continue
                                fit = triangle_descriptor_fit(
                                    index,
                                    threshold,
                                    reference_catalog,
                                    reference_descriptor,
                                    moving_catalog,
                                    moving_descriptor,
                                )
                                trial_results.append(
                                    {
                                        "threshold": float(threshold),
                                        "status": str(fit.get("status", "failed")),
                                        "inliers": int(fit.get("inliers", 0)),
                                        "rms_px": _float_or_nan(fit.get("rms_px")),
                                        "reference_stored": int(reference_catalog["stored_count"]),
                                        "moving_stored": int(moving_catalog["stored_count"]),
                                        "reference_descriptors": int(reference_descriptor["count"]),
                                        "moving_descriptors": int(moving_descriptor["count"]),
                                        "candidate_count": int(fit.get("candidate_count", 0)),
                                        "fit_batch_index": int(fit.get("batch_index", -1)),
                                        "fit_batch_count": int(fit.get("batch_count", 0)),
                                    }
                                )
                                if str(fit.get("status")) != "ok":
                                    continue
                                if selected_fit is None or _resident_similarity_score(fit) > _resident_similarity_score(
                                    selected_fit
                                ):
                                    selected_fit = fit
                                    selected_threshold = float(threshold)
                                    selected_reference_catalog = reference_catalog
                                    selected_moving_catalog = moving_catalog
                                    selected_reference_descriptors = reference_descriptor
                                    selected_moving_descriptors = moving_descriptor

                            frame_determinism = {
                                "schema_version": 1,
                                "frame_index": int(index),
                                "frame_id": str(frame["id"]),
                                "threshold_mode": threshold_mode,
                                "threshold_candidates": [float(item) for item in threshold_candidates],
                                "selected_threshold": None
                                if selected_threshold is None
                                else float(selected_threshold),
                                "trial_signature": _resident_trial_signature(trial_results),
                                "status": "failed" if selected_fit is None else "ok",
                            }
                            if selected_fit is not None:
                                frame_determinism.update(
                                    {
                                        "reference_catalog": _resident_catalog_signature(
                                            selected_reference_catalog
                                        ),
                                        "moving_catalog": _resident_catalog_signature(selected_moving_catalog),
                                        "reference_descriptor": _resident_descriptor_signature(
                                            selected_reference_descriptors
                                        ),
                                        "moving_descriptor": _resident_descriptor_signature(
                                            selected_moving_descriptors
                                        ),
                                        "selected_fit": _resident_fit_signature(selected_fit),
                                    }
                                )
                            triangle_determinism_signatures["moving"][str(frame["id"])] = frame_determinism

                            if selected_fit is None:
                                status = "failed"
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append("resident triangle descriptor registration found no accepted fit")
                                warnings.append(
                                    "triangle_determinism_trial_signature="
                                    + str(frame_determinism["trial_signature"]["sha256"])
                                )
                            else:
                                matrix_array = np.asarray(selected_fit["matrix"], dtype=np.float32).reshape(3, 3)
                                pixel_metrics: dict[str, Any] | None = None
                                if pixel_refine_enabled and hasattr(
                                    stack,
                                    "refine_matrix_translation_candidates_to_reference",
                                ):
                                    if triangle_pixel_refine_batch_enabled:
                                        deferred_triangle_refine = {
                                            "index": index,
                                            "frame_id": str(frame["id"]),
                                            "matrix": matrix_array.copy(),
                                        }
                                        warnings.append("triangle_pixel_refine_mode=native_batch_pending")
                                    else:
                                        pixel_refine_start = perf_counter()
                                        refinement = stack.refine_matrix_translation_candidates_to_reference(
                                            reference_index,
                                            index,
                                            np.asarray([matrix_array], dtype=np.float32),
                                            **refine_kwargs,
                                        )
                                        _add_elapsed(
                                            registration_component_s,
                                            "triangle_pixel_refine",
                                            perf_counter() - pixel_refine_start,
                                        )
                                        matrix_array = np.asarray(refinement["matrix"], dtype=np.float32).reshape(3, 3)
                                        pixel_metrics = dict(refinement.get("metrics", {}))
                                translation_refine: dict[str, Any] | None = None
                                reference_centroid_summary: dict[str, Any] | None = None
                                moving_centroid_summary: dict[str, Any] | None = None
                                if triangle_translation_refine_enabled and deferred_triangle_refine is None:
                                    threshold_key = round(float(selected_threshold or 0.0), 6)
                                    translation_reference_catalog, reference_centroid_summary = centroid_refined_catalog(
                                        reference_index,
                                        threshold_key,
                                        selected_reference_catalog,
                                    )
                                    translation_moving_catalog, moving_centroid_summary = centroid_refined_catalog(
                                        index,
                                        threshold_key,
                                        selected_moving_catalog,
                                    )
                                    translation_refine_start = perf_counter()
                                    translation_refine = _resident_triangle_translation_refine(
                                        translation_reference_catalog,
                                        translation_moving_catalog,
                                        matrix_array,
                                        tolerance_px=triangle_translation_refine_tolerance_px,
                                        min_inliers=triangle_translation_refine_min_inliers,
                                        max_correction_px=triangle_translation_refine_max_correction_px,
                                        iterations=triangle_translation_refine_iterations,
                                        iteration_max_step_px=triangle_translation_refine_iteration_max_step_px,
                                    )
                                    _add_elapsed(
                                        registration_component_s,
                                        "triangle_translation_refine",
                                        perf_counter() - translation_refine_start,
                                    )
                                    correction_px = _float_or_nan(translation_refine.get("correction_px"))
                                    if np.isfinite(correction_px):
                                        triangle_translation_refine_max_correction_px_observed = max(
                                            triangle_translation_refine_max_correction_px_observed,
                                            float(correction_px),
                                        )
                                    refine_rms = _float_or_nan(translation_refine.get("rms_px"))
                                    if np.isfinite(refine_rms):
                                        triangle_translation_refine_max_rms_px = max(
                                            triangle_translation_refine_max_rms_px,
                                            float(refine_rms),
                                        )
                                    refine_iterations = int(translation_refine.get("iterations", 0) or 0)
                                    triangle_translation_refine_max_iterations_observed = max(
                                        triangle_translation_refine_max_iterations_observed,
                                        refine_iterations,
                                    )
                                    if bool(translation_refine.get("applied", False)):
                                        triangle_translation_refine_applied_count += 1
                                        matrix_array = np.asarray(
                                            translation_refine["matrix"],
                                            dtype=np.float32,
                                        ).reshape(3, 3)
                                    elif str(translation_refine.get("status")) == "correction_exceeds_limit":
                                        triangle_translation_refine_rejected_count += 1
                                    else:
                                        triangle_translation_refine_skipped_count += 1
                                matrix = matrix_array.tolist()
                                matched = int(selected_fit.get("inliers", 0))
                                inliers = matched
                                rms_px = _float_or_nan(selected_fit.get("rms_px"))
                                selected_pixel_ncc = (
                                    float("nan")
                                    if pixel_metrics is None
                                    else _float_or_nan(pixel_metrics.get("ncc"))
                                )
                                selected_pixel_rms = (
                                    float("nan")
                                    if pixel_metrics is None
                                    else _float_or_nan(pixel_metrics.get("rms"))
                                )
                                if deferred_triangle_refine is None:
                                    agreement_quality = _resident_triangle_agreement_quality(
                                        selected_pixel_ncc,
                                        selected_pixel_rms,
                                        rms_px,
                                        triangle_agreement_rms_scale,
                                        min_agreement_score,
                                    )
                                else:
                                    agreement_quality = {
                                        "score": float("nan"),
                                        "status": "deferred_batch",
                                        "reason": "native_batch_pending",
                                        "pixel_ncc": selected_pixel_ncc,
                                        "pixel_rms_adu": selected_pixel_rms,
                                        "fit_rms_px": rms_px,
                                        "rms_scale_adu": triangle_agreement_rms_scale,
                                        "min_score": min_agreement_score,
                                    }
                                agreement_policy = _resident_triangle_agreement_policy(
                                    agreement_quality,
                                    triangle_agreement_action,
                                    triangle_agreement_min_weight,
                                )
                                agreement_quality = {
                                    **agreement_quality,
                                    "status": agreement_policy["status"],
                                    "action": agreement_policy["action"],
                                    "weight_multiplier": agreement_policy["weight_multiplier"],
                                }
                                quality_failures: list[str] = []
                                if deferred_triangle_refine is None and min_pixel_ncc is not None and (
                                    not np.isfinite(selected_pixel_ncc) or selected_pixel_ncc < float(min_pixel_ncc)
                                ):
                                    quality_failures.append(
                                        f"pixel_ncc {selected_pixel_ncc:.6g} < {float(min_pixel_ncc):.6g}"
                                    )
                                if deferred_triangle_refine is None and agreement_policy["hard_failure"]:
                                    quality_failures.append(str(agreement_policy["failure_message"]))
                                if not quality_failures:
                                    triangle_quality_diagnostics = {
                                        "triangle_translation_refine_status": (
                                            str(translation_refine.get("status"))
                                            if translation_refine is not None
                                            else "disabled"
                                        ),
                                        "triangle_translation_refine_inliers": (
                                            int(translation_refine.get("inliers", 0) or 0)
                                            if translation_refine is not None
                                            else 0
                                        ),
                                        "triangle_translation_refine_rms_px": (
                                            _finite_float_or_none(translation_refine.get("rms_px"))
                                            if translation_refine is not None
                                            else None
                                        ),
                                        "triangle_translation_refine_correction_px": (
                                            _finite_float_or_none(translation_refine.get("correction_px"))
                                            if translation_refine is not None
                                            else None
                                        ),
                                        "reference_stars": int(selected_reference_catalog["stored_count"]),
                                        "moving_stars": int(selected_moving_catalog["stored_count"]),
                                        "reference_descriptors": int(selected_reference_descriptors["count"]),
                                        "moving_descriptors": int(selected_moving_descriptors["count"]),
                                        "triangle_scale": _finite_float_or_none(selected_fit.get("scale")),
                                        "triangle_rotation_rad": _finite_float_or_none(
                                            selected_fit.get("rotation_rad")
                                        ),
                                        "triangle_threshold": selected_threshold,
                                        "triangle_pixel_refine_deferred": bool(deferred_triangle_refine is not None),
                                    }
                                    quality_decision = _resident_registration_quality_decision(
                                        decisions_by_frame=registration_quality_decisions_by_frame,
                                        frame_id=str(frame["id"]),
                                        registration_mode=resident_registration,
                                        requested_action=resident_registration_quality_gate,
                                        status=status,
                                        matched_stars=matched,
                                        inliers=inliers,
                                        rms_px=rms_px,
                                        min_inliers=resident_registration_quality_min_inliers,
                                        max_rms_px=resident_registration_quality_max_rms_px,
                                        diagnostics=triangle_quality_diagnostics,
                                    )
                                    warnings.extend(resident_registration_quality_warning_fields(quality_decision))
                                if quality_failures:
                                    status = "failed"
                                    frame_weight_values[index] = 0.0
                                    frame_weights[frame["id"]] = 0.0
                                    warnings.append(
                                        "resident triangle descriptor registration failed quality gate: "
                                        + "; ".join(quality_failures)
                                    )
                                elif quality_decision is not None and quality_decision["action_applied"] == "exclude":
                                    status = str(quality_decision["final_status"])
                                    frame_weight_values[index] = 0.0
                                    frame_weights[frame["id"]] = 0.0
                                    warnings.append(
                                        "resident registration quality gate excluded frame: "
                                        + "; ".join(str(item) for item in quality_decision.get("reasons", []))
                                    )
                                elif (
                                    deferred_triangle_refine is None
                                    and float(agreement_policy["weight_multiplier"]) < 1.0
                                ):
                                    multiplier = float(agreement_policy["weight_multiplier"])
                                    agreement_weight_multipliers[index] *= multiplier
                                    warnings.append(
                                        "resident triangle agreement downweighted frame by "
                                        + f"{multiplier:.6g}"
                                    )
                                elif deferred_triangle_refine is not None:
                                    warnings.append("triangle_pixel_refine_quality_gate=deferred_batch")
                                elif triangle_fused_matrix_deferred_enabled:
                                    integration_matrices[index] = matrix
                                    fused_matrix_deferred_frame_indices.add(index)
                                    triangle_fused_matrix_deferred_count += 1
                                    warnings.extend(
                                        [
                                            "resident_registration_application=fused_matrix_deferred",
                                            "triangle_warp_batch=false",
                                            f"triangle_warp_batch_mode={triangle_warp_batch_mode}",
                                            f"triangle_warp_batch_dispatch={resident_warp_batch_dispatch}",
                                            f"triangle_warp_batch_timing_model={triangle_warp_batch_timing_model}",
                                        ]
                                    )
                                else:
                                    integration_matrices[index] = matrix
                                    pending_triangle_warp_matrix = matrix
                                triangle_centroid_warning_mode = "disabled"
                                triangle_centroid_warning_background = "disabled"
                                triangle_centroid_warning_reference_status = "disabled"
                                triangle_centroid_warning_moving_status = "disabled"
                                if triangle_centroid_refine_enabled:
                                    triangle_centroid_warning_background = triangle_centroid_background_mode
                                    native_centroid_catalog = has_top_nms_catalog_centroid or (
                                        use_grid_catalog
                                        and (
                                            has_grid_nms_catalog_centroid
                                            or has_grid_nms_catalog_deterministic_centroid
                                        )
                                    )
                                    if moving_centroid_summary is not None:
                                        triangle_centroid_warning_mode = str(
                                            moving_centroid_summary.get("mode", "disabled")
                                        )
                                        triangle_centroid_warning_moving_status = str(
                                            moving_centroid_summary.get("status", "disabled")
                                        )
                                    elif native_centroid_catalog:
                                        triangle_centroid_warning_mode = (
                                            "resident_gpu_global_mean_centroid"
                                            if triangle_centroid_background_mode == "global_mean"
                                            else "resident_gpu_window_centroid"
                                        )
                                        triangle_centroid_warning_moving_status = "native_catalog"
                                    if reference_centroid_summary is not None:
                                        triangle_centroid_warning_reference_status = str(
                                            reference_centroid_summary.get("status", "disabled")
                                        )
                                    elif native_centroid_catalog:
                                        triangle_centroid_warning_reference_status = "native_catalog"
                                warnings.extend(
                                    [
                                        f"triangle_threshold_mode={threshold_mode}",
                                        f"selected_triangle_threshold={float(selected_threshold or 0.0):.6g}",
                                        "triangle_threshold_candidates="
                                        + ",".join(f"{float(item):.6g}" for item in threshold_candidates),
                                        f"reference_stars={int(selected_reference_catalog['stored_count'])}",
                                        f"moving_stars={int(selected_moving_catalog['stored_count'])}",
                                        f"reference_descriptors={int(selected_reference_descriptors['count'])}",
                                        f"moving_descriptors={int(selected_moving_descriptors['count'])}",
                                        f"triangle_neighbors={descriptor_neighbors}",
                                        f"triangle_max_descriptors={max_descriptors}",
                                        f"triangle_descriptor_radius={descriptor_radius:.6g}",
                                        f"triangle_candidate_count={int(selected_fit.get('candidate_count', 0))}",
                                        "triangle_descriptor_fit_best_reduction_mode="
                                        + str(selected_fit.get("best_reduction_mode", "unavailable")),
                                        "triangle_descriptor_fit_batch="
                                        + str(bool("batch_model" in selected_fit)).lower(),
                                        "triangle_descriptor_fit_batch_mode="
                                        + str(selected_fit.get("batch_model", triangle_descriptor_fit_batch_mode)),
                                        "triangle_descriptor_fit_batch_timing_model="
                                        + str(selected_fit.get("batch_timing_model", "unavailable")),
                                        "triangle_descriptor_fit_reference_device_reuse="
                                        + str(bool(selected_fit.get("reference_device_reuse", False))).lower(),
                                        "triangle_descriptor_fit_reference_device_bytes="
                                        + str(int(selected_fit.get("reference_device_bytes", 0) or 0)),
                                        "triangle_descriptor_fit_moving_device_reuse="
                                        + str(bool(selected_fit.get("moving_device_reuse", False))).lower(),
                                        "triangle_descriptor_fit_moving_device_bytes="
                                        + str(int(selected_fit.get("moving_device_bytes", 0) or 0)),
                                        "triangle_descriptor_fit_output_device_reuse="
                                        + str(bool(selected_fit.get("output_device_reuse", False))).lower(),
                                        "triangle_descriptor_fit_output_device_bytes="
                                        + str(int(selected_fit.get("output_device_bytes", 0) or 0)),
                                        "triangle_descriptor_fit_frame_kernel_sync_s="
                                        + f"{float(selected_fit.get('batch_frame_kernel_sync_s', 0.0) or 0.0):.6g}",
                                        "triangle_descriptor_fit_frame_moving_upload_s="
                                        + f"{float(selected_fit.get('batch_frame_moving_upload_s', 0.0) or 0.0):.6g}",
                                        "triangle_descriptor_fit_frame_output_download_s="
                                        + f"{float(selected_fit.get('batch_frame_output_download_s', 0.0) or 0.0):.6g}",
                                        "triangle_determinism_reference_catalog_signature="
                                        + str(frame_determinism["reference_catalog"]["sha256"]),
                                        "triangle_determinism_moving_catalog_signature="
                                        + str(frame_determinism["moving_catalog"]["sha256"]),
                                        "triangle_determinism_reference_descriptor_signature="
                                        + str(frame_determinism["reference_descriptor"]["sha256"]),
                                        "triangle_determinism_moving_descriptor_signature="
                                        + str(frame_determinism["moving_descriptor"]["sha256"]),
                                        "triangle_determinism_selected_fit_signature="
                                        + str(frame_determinism["selected_fit"]["sha256"]),
                                        "triangle_determinism_trial_signature="
                                        + str(frame_determinism["trial_signature"]["sha256"]),
                                        f"triangle_scale={float(selected_fit.get('scale', float('nan'))):.9g}",
                                        f"triangle_rotation_rad={float(selected_fit.get('rotation_rad', float('nan'))):.9g}",
                                        f"triangle_fit_rms_px={rms_px:.6g}",
                                        f"triangle_pixel_refine_enabled={pixel_refine_enabled}",
                                        "triangle_pixel_refine_fast_coarse="
                                        + str(bool(triangle_pixel_refine_fast_coarse_enabled)).lower(),
                                        "triangle_pixel_refine_fast_coarse_mode="
                                        + str(triangle_pixel_refine_fast_coarse_mode),
                                        "triangle_pixel_refine_coarse_stride_adjusted="
                                        + str(bool(triangle_pixel_refine_coarse_stride_adjusted)).lower(),
                                        "triangle_pixel_refine_requested_coarse_stride="
                                        + str(int(triangle_pixel_refine_requested_coarse_stride)),
                                        "triangle_pixel_refine_effective_coarse_stride="
                                        + str(int(refine_kwargs["coarse_sample_stride"])),
                                        "triangle_pixel_refine_requested_final_stride="
                                        + str(int(triangle_pixel_refine_requested_final_stride)),
                                        f"triangle_pixel_rms_adu={selected_pixel_rms:.6g}",
                                        f"triangle_pixel_ncc={selected_pixel_ncc:.6g}",
                                        "triangle_translation_refine_enabled="
                                        + str(bool(triangle_translation_refine_enabled)).lower(),
                                        "triangle_translation_refine_policy_source="
                                        + str(triangle_translation_refine_policy_source),
                                        "triangle_translation_refine_status="
                                        + (
                                            str(translation_refine.get("status"))
                                            if translation_refine is not None
                                            else "disabled"
                                        ),
                                        "triangle_translation_refine_inliers="
                                        + (
                                            str(int(translation_refine.get("inliers", 0) or 0))
                                            if translation_refine is not None
                                            else "0"
                                        ),
                                        "triangle_translation_refine_rms_px="
                                        + (
                                            f"{_float_or_nan(translation_refine.get('rms_px')):.6g}"
                                            if translation_refine is not None
                                            else "nan"
                                        ),
                                        "triangle_translation_refine_correction_px="
                                        + (
                                            f"{_float_or_nan(translation_refine.get('correction_px')):.6g}"
                                            if translation_refine is not None
                                            else "nan"
                                        ),
                                        "triangle_translation_refine_iterations="
                                        + (
                                            str(int(translation_refine.get("iterations", 0) or 0))
                                            if translation_refine is not None
                                            else "0"
                                        ),
                                        "triangle_translation_refine_iteration_max_step_px="
                                        + f"{float(triangle_translation_refine_iteration_max_step_px):.6g}",
                                        "triangle_translation_refine_initial_rms_px="
                                        + (
                                            f"{_float_or_nan(translation_refine.get('initial_rms_px')):.6g}"
                                            if translation_refine is not None
                                            else "nan"
                                        ),
                                        "triangle_centroid_refine_enabled="
                                        + str(bool(triangle_centroid_refine_enabled)).lower(),
                                        "triangle_centroid_refine_mode=" + triangle_centroid_warning_mode,
                                        "triangle_centroid_refine_background="
                                        + triangle_centroid_warning_background,
                                        "triangle_centroid_refine_reference_status="
                                        + triangle_centroid_warning_reference_status,
                                        "triangle_centroid_refine_moving_status="
                                        + triangle_centroid_warning_moving_status,
                                        "triangle_centroid_refine_reference_count="
                                        + str(int((reference_centroid_summary or {}).get("refined_count", 0) or 0)),
                                        "triangle_centroid_refine_moving_count="
                                        + str(int((moving_centroid_summary or {}).get("refined_count", 0) or 0)),
                                        "triangle_centroid_refine_moving_max_shift_px="
                                        + f"{_float_or_nan((moving_centroid_summary or {}).get('max_shift_px')):.6g}",
                                        "triangle_quality_gate_status="
                                        + ("failed" if quality_failures else "ok"),
                                        f"triangle_min_pixel_ncc={min_pixel_ncc}",
                                        f"triangle_catalog_selector={catalog_selector}",
                                        "triangle_catalog_grid_auto="
                                        + str(bool(triangle_catalog_grid_auto)).lower(),
                                        f"triangle_catalog_batch={triangle_catalog_batch_mode}",
                                        f"triangle_catalog_timing_model={triangle_catalog_timing_model}",
                                        f"triangle_catalog_batch_size={triangle_catalog_batch_size}",
                                        f"triangle_catalog_stream_count={triangle_catalog_stream_count}",
                                        f"triangle_catalog_batch_sync_count={triangle_catalog_batch_sync_count}",
                                        f"triangle_catalog_sync_phase_count={triangle_catalog_sync_phase_count}",
                                        f"triangle_catalog_download_mode={triangle_catalog_download_mode}",
                                        f"triangle_catalog_workspace_layout={triangle_catalog_workspace_layout}",
                                        "triangle_catalog_output_download_copy_count="
                                        + str(int(triangle_catalog_output_download_copy_count)),
                                        "triangle_catalog_centroid_before_download_copy_count="
                                        + str(int(triangle_catalog_centroid_before_download_copy_count)),
                                        "triangle_catalog_centroid_mean_sync_mode="
                                        + str(triangle_catalog_centroid_mean_sync_mode),
                                        f"triangle_catalog_sort_mode={triangle_catalog_sort_mode}",
                                        f"triangle_catalog_topk_mode={triangle_catalog_topk_mode}",
                                        f"triangle_star_grid_cols={triangle_star_grid_cols}",
                                        f"triangle_star_grid_rows={triangle_star_grid_rows}",
                                        f"triangle_grid_top_per_cell={grid_top_candidates_per_cell}",
                                        f"triangle_nms_scan_candidates={nms_scan_candidates}",
                                        f"triangle_nms_min_separation_px={nms_min_separation_px:.6g}",
                                        "resident CUDA triangle descriptor similarity",
                                    ]
                                )
                                warnings.extend(_resident_triangle_agreement_warnings(agreement_quality))
                            warnings.append("triangle_trials=" + str(trial_results))
                    except Exception as exc:
                        status = "failed"
                        frame_weight_values[index] = 0.0
                        frame_weights[frame["id"]] = 0.0
                        warnings.append(str(exc))
                    if quality_decision is None:
                        quality_decision = _resident_registration_quality_decision(
                            decisions_by_frame=registration_quality_decisions_by_frame,
                            frame_id=str(frame["id"]),
                            registration_mode=resident_registration,
                            requested_action=resident_registration_quality_gate,
                            status=status,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            min_inliers=resident_registration_quality_min_inliers,
                            max_rms_px=resident_registration_quality_max_rms_px,
                            diagnostics=triangle_quality_diagnostics,
                        )
                        warnings.extend(resident_registration_quality_warning_fields(quality_decision))
                    registration_elapsed = perf_counter() - registration_frame_start
                    if resident_registration == "similarity_cuda_triangle":
                        _add_elapsed(registration_component_s, "triangle_frame_total", registration_elapsed)
                    per_frame_registration_s.append(registration_elapsed)
                    result_index = len(registration_results)
                    registration_results.append(
                        RegistrationResult(
                            frame_id=str(frame["id"]),
                            reference_frame_id=str(reference_frame["id"]),
                            transform_model="similarity_cuda_triangle",
                            matrix=matrix,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                f"max_shift={resident_registration_max_shift}",
                                f"star_max_candidates={resident_star_max_candidates}",
                                f"star_tolerance_px={resident_star_tolerance_px}",
                                "resident CUDA triangle descriptor registration",
                            ],
                        )
                    )
                    if deferred_triangle_refine is not None and status == "ok":
                        deferred_triangle_refine["result_index"] = result_index
                        pending_triangle_pixel_refines.append(deferred_triangle_refine)
                    if pending_triangle_warp_matrix is not None and status == "ok":
                        pending_triangle_warps.append(
                            {
                                "index": index,
                                "matrix": pending_triangle_warp_matrix,
                                "result_index": result_index,
                            }
                        )

                apply_pending_triangle_warps(pending_triangle_warps)
                if pending_triangle_pixel_refines:
                    batch_post_start = perf_counter()
                    try:
                        batch_refine_start = perf_counter()
                        batch_refinements = stack.refine_matrix_translation_candidates_batch_to_reference(
                            reference_index,
                            [int(item["index"]) for item in pending_triangle_pixel_refines],
                            np.asarray([item["matrix"] for item in pending_triangle_pixel_refines], dtype=np.float32),
                            **refine_kwargs,
                        )
                        batch_refine_elapsed = perf_counter() - batch_refine_start
                        _add_elapsed(registration_component_s, "triangle_pixel_refine", batch_refine_elapsed)
                        _add_elapsed(registration_component_s, "triangle_pixel_refine_batch", batch_refine_elapsed)
                        if batch_refinements:
                            first_refinement = dict(batch_refinements[0])
                            triangle_pixel_refine_workspace_mode = str(
                                first_refinement.get("workspace_mode", "unavailable")
                            )
                            triangle_pixel_refine_workspace_bytes = int(
                                first_refinement.get("workspace_bytes", 0) or 0
                            )
                            triangle_pixel_refine_workspace_candidate_capacity = int(
                                first_refinement.get("workspace_candidate_capacity", 0) or 0
                            )
                            triangle_pixel_refine_batch_metric_mode = str(
                                first_refinement.get("batch_metric_mode", "unavailable")
                            )
                            triangle_pixel_refine_batch_metric_kernel_launches = int(
                                first_refinement.get("batch_metric_kernel_launches", 0) or 0
                            )
                            triangle_pixel_refine_coarse_total_candidates = int(
                                first_refinement.get("coarse_total_candidates", 0) or 0
                            )
                            triangle_pixel_refine_fine_total_candidates = int(
                                first_refinement.get("fine_total_candidates", 0) or 0
                            )
                            triangle_pixel_refine_metric_workload_model = str(
                                first_refinement.get("metric_workload_model", "unavailable")
                            )
                            triangle_pixel_refine_coarse_sampled_pixels_per_candidate = int(
                                first_refinement.get("coarse_sampled_pixels_per_candidate", 0) or 0
                            )
                            triangle_pixel_refine_fine_sampled_pixels_per_candidate = int(
                                first_refinement.get("fine_sampled_pixels_per_candidate", 0) or 0
                            )
                            triangle_pixel_refine_coarse_metric_sample_evaluations = int(
                                first_refinement.get("coarse_metric_sample_evaluations", 0) or 0
                            )
                            triangle_pixel_refine_fine_metric_sample_evaluations = int(
                                first_refinement.get("fine_metric_sample_evaluations", 0) or 0
                            )
                            triangle_pixel_refine_coarse_metric_megasamples_per_s = float(
                                first_refinement.get("coarse_metric_megasamples_per_s", 0.0) or 0.0
                            )
                            triangle_pixel_refine_fine_metric_megasamples_per_s = float(
                                first_refinement.get("fine_metric_megasamples_per_s", 0.0) or 0.0
                            )
                            triangle_pixel_refine_native_coarse_s = float(
                                first_refinement.get(
                                    "native_coarse_total_s",
                                    sum(
                                        float(item.get("coarse_metric_s", 0.0) or 0.0)
                                        for item in batch_refinements
                                    ),
                                )
                                or 0.0
                            )
                            triangle_pixel_refine_native_fine_s = float(
                                first_refinement.get(
                                    "native_fine_total_s",
                                    sum(
                                        float(item.get("fine_metric_s", 0.0) or 0.0)
                                        for item in batch_refinements
                                    ),
                                )
                                or 0.0
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_pixel_refine_native_coarse",
                                triangle_pixel_refine_native_coarse_s,
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_pixel_refine_native_fine",
                                triangle_pixel_refine_native_fine_s,
                            )
                    except Exception as exc:
                        batch_refinements = []
                        for item in pending_triangle_pixel_refines:
                            result = registration_results[int(item["result_index"])]
                            result.status = "failed"
                            frame_weight_values[int(item["index"])] = 0.0
                            frame_weights[str(item["frame_id"])] = 0.0
                            result.warnings.append(f"triangle_pixel_refine_batch_failed={exc}")
                    valid_triangle_batch_warps: list[tuple[dict[str, Any], RegistrationResult]] = []
                    for item, refinement in zip(pending_triangle_pixel_refines, batch_refinements, strict=True):
                        result = registration_results[int(item["result_index"])]
                        matrix_array = np.asarray(refinement["matrix"], dtype=np.float32).reshape(3, 3)
                        pixel_metrics = dict(refinement.get("metrics", {}))
                        selected_pixel_ncc = _float_or_nan(pixel_metrics.get("ncc"))
                        selected_pixel_rms = _float_or_nan(pixel_metrics.get("rms"))
                        agreement_quality = _resident_triangle_agreement_quality(
                            selected_pixel_ncc,
                            selected_pixel_rms,
                            _float_or_nan(result.rms_px),
                            triangle_agreement_rms_scale,
                            min_agreement_score,
                        )
                        agreement_policy = _resident_triangle_agreement_policy(
                            agreement_quality,
                            triangle_agreement_action,
                            triangle_agreement_min_weight,
                        )
                        agreement_quality = {
                            **agreement_quality,
                            "status": agreement_policy["status"],
                            "action": agreement_policy["action"],
                            "weight_multiplier": agreement_policy["weight_multiplier"],
                        }
                        result.matrix = matrix_array.tolist()
                        result.warnings.extend(
                            [
                                "triangle_pixel_refine_mode=native_batch",
                                "triangle_pixel_refine_fast_coarse="
                                + str(bool(triangle_pixel_refine_fast_coarse_enabled)).lower(),
                                "triangle_pixel_refine_fast_coarse_mode="
                                + str(triangle_pixel_refine_fast_coarse_mode),
                                "triangle_pixel_refine_coarse_stride_adjusted="
                                + str(bool(triangle_pixel_refine_coarse_stride_adjusted)).lower(),
                                "triangle_pixel_refine_requested_coarse_stride="
                                + str(int(triangle_pixel_refine_requested_coarse_stride)),
                                "triangle_pixel_refine_effective_coarse_stride="
                                + str(int(refine_kwargs["coarse_sample_stride"])),
                                "triangle_pixel_refine_requested_final_stride="
                                + str(int(triangle_pixel_refine_requested_final_stride)),
                                f"triangle_pixel_refine_batch_index={int(refinement.get('batch_index', -1))}",
                                f"triangle_pixel_refine_batch_count={int(refinement.get('batch_count', 0))}",
                                f"triangle_pixel_refine_batch_model={refinement.get('batch_model')}",
                                f"triangle_pixel_refine_batch_metric_mode={refinement.get('batch_metric_mode', 'unavailable')}",
                                "triangle_pixel_refine_batch_metric_kernel_launches="
                                + str(int(refinement.get("batch_metric_kernel_launches", 0) or 0)),
                                f"triangle_pixel_refine_coarse_total_candidates={int(refinement.get('coarse_total_candidates', 0) or 0)}",
                                f"triangle_pixel_refine_fine_total_candidates={int(refinement.get('fine_total_candidates', 0) or 0)}",
                                "triangle_pixel_refine_metric_workload_model="
                                + str(refinement.get("metric_workload_model", "unavailable")),
                                "triangle_pixel_refine_coarse_sampled_pixels_per_candidate="
                                + str(int(refinement.get("coarse_sampled_pixels_per_candidate", 0) or 0)),
                                "triangle_pixel_refine_fine_sampled_pixels_per_candidate="
                                + str(int(refinement.get("fine_sampled_pixels_per_candidate", 0) or 0)),
                                "triangle_pixel_refine_coarse_metric_sample_evaluations="
                                + str(int(refinement.get("coarse_metric_sample_evaluations", 0) or 0)),
                                "triangle_pixel_refine_fine_metric_sample_evaluations="
                                + str(int(refinement.get("fine_metric_sample_evaluations", 0) or 0)),
                                "triangle_pixel_refine_coarse_metric_megasamples_per_s="
                                + f"{float(refinement.get('coarse_metric_megasamples_per_s', 0.0) or 0.0):.6g}",
                                "triangle_pixel_refine_fine_metric_megasamples_per_s="
                                + f"{float(refinement.get('fine_metric_megasamples_per_s', 0.0) or 0.0):.6g}",
                                f"triangle_pixel_refine_workspace_mode={refinement.get('workspace_mode', 'unavailable')}",
                                f"triangle_pixel_refine_workspace_bytes={int(refinement.get('workspace_bytes', 0) or 0)}",
                                "triangle_pixel_refine_workspace_candidate_capacity="
                                + str(int(refinement.get("workspace_candidate_capacity", 0) or 0)),
                                f"triangle_pixel_refine_coarse_metric_s={float(refinement.get('coarse_metric_s', 0.0) or 0.0):.6g}",
                                f"triangle_pixel_refine_fine_metric_s={float(refinement.get('fine_metric_s', 0.0) or 0.0):.6g}",
                                f"triangle_pixel_rms_adu_batch={selected_pixel_rms:.6g}",
                                f"triangle_pixel_ncc_batch={selected_pixel_ncc:.6g}",
                            ]
                        )
                        result.warnings.extend(_resident_triangle_agreement_warnings(agreement_quality))
                        quality_failures: list[str] = []
                        if min_pixel_ncc is not None and (
                            not np.isfinite(selected_pixel_ncc) or selected_pixel_ncc < float(min_pixel_ncc)
                        ):
                            quality_failures.append(
                                f"pixel_ncc {selected_pixel_ncc:.6g} < {float(min_pixel_ncc):.6g}"
                            )
                        if agreement_policy["hard_failure"]:
                            quality_failures.append(str(agreement_policy["failure_message"]))
                        if quality_failures:
                            result.status = "failed"
                            frame_weight_values[int(item["index"])] = 0.0
                            frame_weights[str(item["frame_id"])] = 0.0
                            result.warnings.append(
                                "resident triangle descriptor registration failed batch quality gate: "
                                + "; ".join(quality_failures)
                            )
                            continue
                        if float(agreement_policy["weight_multiplier"]) < 1.0:
                            multiplier = float(agreement_policy["weight_multiplier"])
                            agreement_weight_multipliers[int(item["index"])] *= multiplier
                            result.warnings.append(
                                "resident triangle agreement downweighted frame by "
                                + f"{multiplier:.6g}"
                            )
                        integration_matrices[int(item["index"])] = result.matrix
                        if triangle_fused_matrix_deferred_enabled:
                            fused_matrix_deferred_frame_indices.add(int(item["index"]))
                            triangle_fused_matrix_deferred_count += 1
                            result.warnings.extend(
                                [
                                    "resident_registration_application=fused_matrix_deferred",
                                    "triangle_warp_batch=false",
                                    f"triangle_warp_batch_mode={triangle_warp_batch_mode}",
                                    f"triangle_warp_batch_dispatch={resident_warp_batch_dispatch}",
                                    f"triangle_warp_batch_timing_model={triangle_warp_batch_timing_model}",
                                ]
                            )
                            continue
                        valid_triangle_batch_warps.append((item, result))
                    if valid_triangle_batch_warps:
                        _apply_deferred_inline_cosmetic_cuda_source_dq(
                            stack,
                            [int(item["index"]) for item, _result in valid_triangle_batch_warps],
                            source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                        )
                        warp_start = perf_counter()
                        warp_models, warp_timing = _apply_resident_registration_matrix_batch(
                            stack,
                            [
                                (int(item["index"]), result.matrix)
                                for item, result in valid_triangle_batch_warps
                            ],
                            resident_warp_interpolation,
                            resident_warp_clamping_threshold,
                            resident_warp_batch_dispatch,
                            resident_warp_chunk_capacity_effective,
                            resident_track_warp_coverage,
                        )
                        warp_elapsed = perf_counter() - warp_start
                        _add_elapsed(registration_component_s, "triangle_warp", warp_elapsed)
                        if bool(warp_timing.get("batched", False)):
                            triangle_warp_batch_timing_model = str(
                                warp_timing.get("timing_model", "unavailable")
                            )
                            triangle_warp_batch_frame_count += int(warp_timing.get("frame_count", 0) or 0)
                            triangle_warp_batch_fallback_frame_count += int(
                                warp_timing.get("fallback_frame_count", 0) or 0
                            )
                            triangle_warp_batch_native_inverse_upload_mode = str(
                                warp_timing.get("inverse_upload_mode", "unavailable")
                            )
                            triangle_warp_batch_native_inverse_prepare_s += float(
                                warp_timing.get("inverse_prepare_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_inverse_batch_alloc_s += float(
                                warp_timing.get("inverse_batch_alloc_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_inverse_batch_bytes += int(
                                warp_timing.get("inverse_batch_bytes", 0) or 0
                            )
                            if warp_timing.get("chunk_metadata_upload_mode") is not None:
                                triangle_warp_batch_native_chunk_metadata_upload_mode = str(
                                    warp_timing.get("chunk_metadata_upload_mode")
                                )
                            triangle_warp_batch_native_index_upload_s += float(
                                warp_timing.get("index_upload_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_index_upload_count += int(
                                warp_timing.get("index_upload_count", 0) or 0
                            )
                            triangle_warp_batch_native_inverse_upload_s += float(
                                warp_timing.get("inverse_upload_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_inverse_upload_count += int(
                                warp_timing.get("inverse_upload_count", 0) or 0
                            )
                            triangle_warp_batch_native_kernel_enqueue_s += float(
                                warp_timing.get("kernel_enqueue_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_coverage_reduce_enqueue_s += float(
                                warp_timing.get("coverage_reduce_enqueue_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_scatter_enqueue_s += float(
                                warp_timing.get("scatter_enqueue_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_postprocess_enqueue_s += float(
                                warp_timing.get("postprocess_enqueue_s", 0.0) or 0.0
                            )
                            if warp_timing.get("postprocess_mode") is not None:
                                triangle_warp_batch_native_postprocess_mode = str(
                                    warp_timing.get("postprocess_mode")
                                )
                            if warp_timing.get("lanczos3_clamping_enabled") is not None:
                                triangle_warp_batch_native_lanczos3_clamping_enabled = bool(
                                    warp_timing.get("lanczos3_clamping_enabled")
                                )
                            if warp_timing.get("lanczos3_clamp_path") is not None:
                                triangle_warp_batch_native_lanczos3_clamp_path = str(
                                    warp_timing.get("lanczos3_clamp_path")
                                )
                            triangle_warp_batch_native_device_copy_enqueue_s += float(
                                warp_timing.get("device_copy_enqueue_s", 0.0) or 0.0
                            )
                            triangle_warp_batch_native_sync_s += float(warp_timing.get("sync_s", 0.0) or 0.0)
                            triangle_warp_batch_native_total_s += float(warp_timing.get("total_s", 0.0) or 0.0)
                            triangle_warp_batch_native_chunk_frames = max(
                                triangle_warp_batch_native_chunk_frames,
                                int(warp_timing.get("batch_chunk_frames", 0) or 0),
                            )
                            triangle_warp_batch_native_chunk_count += int(
                                warp_timing.get("batch_chunk_count", 0) or 0
                            )
                            if warp_timing.get("batch_capacity_source") is not None:
                                triangle_warp_batch_native_capacity_source = str(
                                    warp_timing.get("batch_capacity_source")
                                )
                            triangle_warp_batch_native_max_chunk_capacity_frames = max(
                                triangle_warp_batch_native_max_chunk_capacity_frames,
                                int(warp_timing.get("batch_max_chunk_capacity_frames", 0) or 0),
                            )
                            triangle_warp_batch_native_workspace_bytes = max(
                                triangle_warp_batch_native_workspace_bytes,
                                int(warp_timing.get("batch_workspace_bytes", 0) or 0),
                            )
                            triangle_warp_batch_native_output_bytes = max(
                                triangle_warp_batch_native_output_bytes,
                                int(warp_timing.get("batch_output_bytes", 0) or 0),
                            )
                            triangle_warp_batch_native_coverage_bytes = max(
                                triangle_warp_batch_native_coverage_bytes,
                                int(warp_timing.get("batch_coverage_bytes", 0) or 0),
                            )
                            triangle_warp_batch_native_warp_kernel_launches += int(
                                warp_timing.get("warp_kernel_launches", 0) or 0
                            )
                            triangle_warp_batch_native_coverage_reduce_kernel_launches += int(
                                warp_timing.get("coverage_reduce_kernel_launches", 0) or 0
                            )
                            triangle_warp_batch_native_scatter_kernel_launches += int(
                                warp_timing.get("scatter_kernel_launches", 0) or 0
                            )
                            triangle_warp_batch_native_postprocess_kernel_launches += int(
                                warp_timing.get("postprocess_kernel_launches", 0) or 0
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_warp_native_batch",
                                float(warp_timing.get("total_s", warp_elapsed) or 0.0),
                            )
                            _add_elapsed(
                                registration_component_s,
                                "triangle_warp_native_sync",
                                float(warp_timing.get("sync_s", 0.0) or 0.0),
                            )
                        else:
                            triangle_warp_batch_fallback_frame_count += int(
                                warp_timing.get("fallback_frame_count", len(valid_triangle_batch_warps)) or 0
                            )
                        for (item, result), warp_model in zip(
                            valid_triangle_batch_warps,
                            warp_models,
                            strict=True,
                        ):
                            warped_frame_indices.add(int(item["index"]))
                            result.warnings.extend(
                                [
                                    f"resident_registration_application={warp_model}",
                                    "triangle_warp_batch=" + str(bool(warp_timing.get("batched", False))).lower(),
                                    f"triangle_warp_batch_mode={triangle_warp_batch_mode}",
                                    f"triangle_warp_batch_dispatch={resident_warp_batch_dispatch}",
                                    "triangle_warp_batch_timing_model="
                                    + str(warp_timing.get("timing_model", "per_frame")),
                                    "triangle_warp_batch_inverse_upload_mode="
                                    + str(warp_timing.get("inverse_upload_mode", "per_frame")),
                                    "triangle_warp_batch_chunk_frames="
                                    + str(int(warp_timing.get("batch_chunk_frames", 0) or 0)),
                                    "triangle_warp_batch_lanczos3_clamp_path="
                                    + str(warp_timing.get("lanczos3_clamp_path", "off")),
                                ]
                            )
                    batch_post_elapsed = perf_counter() - batch_post_start
                    per_frame_registration_s.append(batch_post_elapsed)
                    _add_elapsed(registration_component_s, "triangle_frame_total", batch_post_elapsed)

            if resident_registration == "external_matrix":
                for index, frame in enumerate(light_frames):
                    registration_frame_start = perf_counter()
                    warnings = []
                    status = "excluded" if _matches_any_token(frame, excluded_tokens) else "ok"
                    matrix = translation_matrix(0.0, 0.0)
                    transform_model = "external_matrix"
                    matched = 0
                    inliers = 0
                    rms_px = float("nan")
                    try:
                        row = external_registration_by_frame.get(str(frame["id"]))
                        if status == "excluded":
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("excluded by resident frame mask")
                        elif row is None:
                            status = "failed"
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("missing external registration row")
                        else:
                            matrix = _registration_matrix(row)
                            integration_matrices[index] = matrix
                            transform_model = str(row.get("transform_model") or "external_matrix")
                            matched = int(row.get("matched_stars") or 0)
                            inliers = int(row.get("inliers") or 0)
                            rms_px = _float_or_nan(row.get("rms_px"))
                            source_status = str(row.get("status") or "failed")
                            warnings.extend(str(item) for item in row.get("warnings", []))
                            if frame["id"] == reference_frame["id"] or source_status == "reference":
                                status = "reference"
                                rms_px = 0.0 if not np.isfinite(rms_px) else rms_px
                            elif source_status != "ok":
                                status = source_status
                                frame_weight_values[index] = 0.0
                                frame_weights[frame["id"]] = 0.0
                                warnings.append(f"external registration status was {source_status}")
                            elif resident_integration_dispatch == "fused_matrix":
                                fused_matrix_deferred_frame_indices.add(index)
                                warnings.append(
                                    "external_registration_application=fused_matrix_deferred"
                                )
                            else:
                                _apply_deferred_inline_cosmetic_cuda_source_dq(
                                    stack,
                                    [index],
                                    source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}",
                                )
                                warp_model = _apply_resident_registration_matrix(
                                    stack,
                                    index,
                                    matrix,
                                    resident_warp_interpolation,
                                    resident_warp_clamping_threshold,
                                )
                                warped_frame_indices.add(index)
                                warnings.append(f"external_registration_application={warp_model}")
                            if external_registration_path is not None:
                                warnings.append(f"external_registration_results={external_registration_path}")
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
                            transform_model=transform_model,
                            matrix=matrix,
                            matched_stars=matched,
                            inliers=inliers,
                            rms_px=rms_px,
                            status=status,
                            warnings=warnings
                            + [
                                "resident CUDA external matrix registration; matrices come from a prior "
                                "registration_results.json artifact",
                            ],
                        )
                    )

            _apply_deferred_inline_cosmetic_cuda_source_dq(
                stack,
                range(len(light_frames)),
                source=f"resident_post_registration_pre_warp_{resident_inline_source_dq}_flush",
            )

            weighting_start = perf_counter()
            weighting_frame_results: list[dict[str, Any]] = []
            weighting_warnings: list[str] = []
            if weighting_mode == "simple_snr":
                if not hasattr(stack, "frame_global_stats"):
                    raise RuntimeError("resident CUDA backend does not expose frame_global_stats for simple_snr")
                for index, frame in enumerate(light_frames):
                    status = "ok"
                    stats: dict[str, Any] | None = None
                    weight = float(frame_weight_values[index])
                    if frame_weight_values[index] <= 0.0:
                        status = "skipped_zero_weight"
                        weight = 0.0
                    else:
                        stats = stack.frame_global_stats(index)
                        weight = _simple_snr_weight_from_stats(stats)
                        if weight <= 0.0:
                            status = "empty"
                            weight = 0.0
                        frame_weight_values[index] = float(weight)
                        frame_weights[frame["id"]] = float(weight)
                    weighting_frame_results.append(
                        {
                            "frame_id": str(frame["id"]),
                            "weight": float(weight),
                            "status": status,
                            "source_mean": None if stats is None else float(stats["mean"]),
                            "source_std": None if stats is None else float(stats["std"]),
                            "valid_pixels": None if stats is None else int(stats["valid_pixels"]),
                        }
                    )
            else:
                weighting_frame_results = [
                    {
                        "frame_id": str(frame["id"]),
                        "weight": float(frame_weight_values[index]),
                        "status": "zero_weight" if frame_weight_values[index] <= 0.0 else "unit",
                    }
                    for index, frame in enumerate(light_frames)
                ]
            agreement_downweighted_frames = 0
            for index, multiplier in enumerate(agreement_weight_multipliers):
                if frame_weight_values[index] > 0.0 and float(multiplier) < 1.0:
                    agreement_downweighted_frames += 1
                    frame_weight_values[index] = float(frame_weight_values[index]) * float(multiplier)
                    frame_weights[str(light_frames[index]["id"])] = float(frame_weight_values[index])
                    weighting_frame_results[index]["weight"] = float(frame_weight_values[index])
                    weighting_frame_results[index]["agreement_weight_multiplier"] = float(multiplier)
                    weighting_frame_results[index]["status"] = "agreement_downweighted"
                elif float(multiplier) != 1.0:
                    weighting_frame_results[index]["agreement_weight_multiplier"] = float(multiplier)
            if agreement_downweighted_frames:
                weighting_warnings.append(
                    f"resident triangle agreement downweighted {agreement_downweighted_frames} frame(s)"
                )
            motion_weighting_summary = _resident_registration_motion_weighting(
                [str(frame["id"]) for frame in light_frames],
                integration_matrices,
                frame_weight_values,
                mode=resident_registration_motion_weighting,
                threshold_sigma=float(resident_registration_motion_threshold_sigma),
                min_weight=float(resident_registration_motion_min_weight),
                power=float(resident_registration_motion_power),
                scale_floor_px=float(resident_registration_motion_scale_floor_px),
            )
            registration_by_frame_id = {str(result.frame_id): result for result in registration_results}
            motion_downweighted_frames = 0
            for index, row in enumerate(motion_weighting_summary.get("frame_results", [])):
                multiplier = float(row.get("multiplier", 1.0))
                if multiplier >= 1.0 or frame_weight_values[index] <= 0.0:
                    if multiplier != 1.0:
                        weighting_frame_results[index]["registration_motion_weight_multiplier"] = multiplier
                    continue
                motion_downweighted_frames += 1
                frame_weight_values[index] = float(frame_weight_values[index]) * multiplier
                frame_weights[str(light_frames[index]["id"])] = float(frame_weight_values[index])
                previous_status = str(weighting_frame_results[index].get("status") or "")
                weighting_frame_results[index]["weight"] = float(frame_weight_values[index])
                weighting_frame_results[index]["registration_motion_weight_multiplier"] = multiplier
                weighting_frame_results[index]["registration_motion_distance_px"] = row.get("distance_px")
                weighting_frame_results[index]["registration_motion_score"] = row.get("score")
                weighting_frame_results[index]["status"] = (
                    "agreement_and_motion_downweighted"
                    if previous_status == "agreement_downweighted"
                    else "registration_motion_downweighted"
                )
                registration_result = registration_by_frame_id.get(str(light_frames[index]["id"]))
                if registration_result is not None:
                    registration_result.warnings.extend(_registration_motion_warning(row))
            if motion_downweighted_frames:
                weighting_warnings.append(
                    f"resident registration motion downweighted {motion_downweighted_frames} frame(s)"
                )
            proposal_downweighted_frames = 0
            proposal_rows_by_id = {
                str(row.get("frame_id")): row
                for row in frame_weight_proposal.get("rows", [])
                if isinstance(row, dict) and row.get("frame_id") is not None
            }
            for index, frame in enumerate(light_frames):
                frame_id = str(frame["id"])
                row = proposal_rows_by_id.get(frame_id)
                if row is None:
                    continue
                multiplier = float(row.get("multiplier", 1.0))
                weighting_frame_results[index]["frame_weight_proposal_multiplier"] = multiplier
                weighting_frame_results[index]["frame_weight_proposal_path"] = frame_weight_proposal.get("path")
                if row.get("method") is not None:
                    weighting_frame_results[index]["frame_weight_proposal_method"] = row.get("method")
                if multiplier >= 1.0 or frame_weight_values[index] <= 0.0:
                    continue
                proposal_downweighted_frames += 1
                frame_weight_values[index] = float(frame_weight_values[index]) * multiplier
                frame_weights[frame_id] = float(frame_weight_values[index])
                previous_status = str(weighting_frame_results[index].get("status") or "")
                weighting_frame_results[index]["weight"] = float(frame_weight_values[index])
                weighting_frame_results[index]["status"] = (
                    "frame_weight_proposal_downweighted"
                    if previous_status in {"", "ok", "unit"}
                    else f"{previous_status}_and_frame_weight_proposal_downweighted"
                )
                registration_result = registration_by_frame_id.get(frame_id)
                if registration_result is not None:
                    registration_result.warnings.extend(_frame_weight_proposal_warning(row, multiplier))
            frame_weight_proposal_summary = {
                **frame_weight_proposal,
                "applied_downweighted_frame_count": int(proposal_downweighted_frames),
            }
            if proposal_downweighted_frames:
                weighting_warnings.append(
                    f"resident frame-weight proposal downweighted {proposal_downweighted_frames} frame(s)"
                )
            if group_tile_local_policy_replay.get("enabled"):
                if resident_tile_local_policy_mode in {"apply_mean", "apply"}:
                    weighting_warnings.append(
                        "resident tile-local policy replay validated for opt-in native integration"
                    )
                else:
                    weighting_warnings.append(
                        "resident tile-local policy replay validated but not applied; mode=record"
                    )
            weighting_elapsed = perf_counter() - weighting_start

            local_norm_start = perf_counter()
            if resident_integration_dispatch == "fused_matrix" and local_norm_enabled:
                raise RuntimeError("resident fused_matrix integration currently requires local_normalization=off")
            local_norm_mode = (
                f"resident_{resident_local_normalization_mode}" if local_norm_enabled else "off"
            )
            local_norm_frame_results: list[dict[str, Any]] = []
            local_norm_application_profiles: list[dict[str, Any]] = []
            local_norm_grid_stats_batch_profile: dict[str, Any] | None = None
            local_norm_grid_apply_batch_profile: dict[str, Any] | None = None
            local_norm_grid_stats_by_index: dict[int, dict[str, Any]] = {}
            pending_grid_apply: list[dict[str, Any]] = []
            local_norm_warnings: list[str] = []
            resident_grid_ln_batch_apply_supported = hasattr(stack, "apply_grid_normalization_frames")
            resident_grid_ln_batch_apply_enabled = os.environ.get(
                "GLASS_RESIDENT_LN_BATCH_APPLY", "1"
            ).strip().lower() not in {
                "0",
                "false",
                "off",
                "no",
            }
            if local_norm_enabled:
                if resident_local_normalization_mode == "global_mean_std":
                    if not hasattr(stack, "frame_global_stats") or not hasattr(stack, "apply_global_normalization_frame"):
                        raise RuntimeError("resident CUDA backend does not expose global local normalization")
                    reference_stats = stack.frame_global_stats(reference_index)
                    reference_mean = float(reference_stats["mean"])
                    reference_std = float(reference_stats["std"])
                else:
                    if not hasattr(stack, "apply_grid_normalization_frame") or not (
                        hasattr(stack, "frame_pair_grid_stats") or hasattr(stack, "frame_pair_grid_stats_batch")
                    ):
                        raise RuntimeError("resident CUDA backend does not expose grid local normalization")
                    batch_source_indices = [
                        index
                        for index, value in enumerate(frame_weight_values)
                        if float(value) > 0.0 and index != reference_index
                    ]
                    if batch_source_indices and hasattr(stack, "frame_pair_grid_stats_batch"):
                        batch_stats = stack.frame_pair_grid_stats_batch(
                            reference_index,
                            np.asarray(batch_source_indices, dtype=np.int32),
                            resident_local_normalization_tile_size,
                            resident_local_normalization_tile_size,
                        )
                        local_norm_grid_stats_batch_profile = {
                            key: value
                            for key, value in batch_stats.items()
                            if key not in {"frames", "source_indices"}
                        }
                        local_norm_grid_stats_by_index = {
                            int(item["source_index"]): item for item in batch_stats.get("frames", [])
                        }
                    reference_stats = None
                    reference_mean = 0.0
                    reference_std = 0.0
                eps = 1.0e-6
                if resident_local_normalization_mode == "global_mean_std":
                    local_norm_warnings.append(
                        "resident CUDA local normalization uses one global mean/std model per frame"
                    )
                for index, frame in enumerate(light_frames):
                    status = "ok"
                    warnings: list[str] = []
                    scale = 1.0
                    offset = 0.0
                    source_stats: dict[str, Any] | None = None
                    grid_coefficients: dict[str, Any] | None = None
                    application_profile: dict[str, Any] | None = None
                    if frame_weight_values[index] <= 0.0:
                        status = "skipped_zero_weight"
                        warnings.append("frame was excluded or failed registration before local normalization")
                    elif index == reference_index:
                        status = "reference"
                        source_stats = reference_stats
                    elif resident_local_normalization_mode == "global_mean_std":
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
                            application_profile = stack.apply_global_normalization_frame(index, scale, offset)
                        else:
                            scale = reference_std / source_std
                            offset = reference_mean - source_mean * scale
                            application_profile = stack.apply_global_normalization_frame(index, scale, offset)
                    else:
                        grid_stats = local_norm_grid_stats_by_index.get(index)
                        grid_stats_source = "batch" if grid_stats is not None else "per_frame"
                        if grid_stats is None:
                            grid_stats = stack.frame_pair_grid_stats(
                                reference_index,
                                index,
                                resident_local_normalization_tile_size,
                                resident_local_normalization_tile_size,
                            )
                        coeffs = _grid_local_norm_coefficients(grid_stats, eps=eps)
                        if coeffs["valid_pixel_total"] == 0:
                            status = "empty"
                            frame_weight_values[index] = 0.0
                            frame_weights[frame["id"]] = 0.0
                            warnings.append("frame had no finite paired pixels for resident grid LN")
                        else:
                            if (
                                resident_grid_ln_batch_apply_supported
                                and resident_grid_ln_batch_apply_enabled
                            ):
                                pending_grid_apply.append(
                                    {
                                        "frame_index": index,
                                        "result_index": len(local_norm_frame_results),
                                        "scales": coeffs["scales"],
                                        "offsets": coeffs["offsets"],
                                    }
                                )
                            else:
                                application_profile = stack.apply_grid_normalization_frame(
                                    index,
                                    coeffs["scales"],
                                    coeffs["offsets"],
                                    resident_local_normalization_tile_size,
                                    resident_local_normalization_tile_size,
                                )
                            if coeffs["empty_tiles"]:
                                status = "partial"
                                warnings.append(
                                    f"{coeffs['empty_tiles']} local-normalization tiles had no paired finite pixels"
                                )
                        scale = float(coeffs["scale_mean"])
                        offset = float(coeffs["offset_mean"])
                        grid_coefficients = {
                            "model": str(grid_stats["model"]),
                            "stats_source": grid_stats_source,
                            "tile_size": resident_local_normalization_tile_size,
                            "grid_rows": int(grid_stats["grid_rows"]),
                            "grid_cols": int(grid_stats["grid_cols"]),
                            "scale_mean": float(coeffs["scale_mean"]),
                            "scale_min": float(coeffs["scale_min"]),
                            "scale_max": float(coeffs["scale_max"]),
                            "offset_mean": float(coeffs["offset_mean"]),
                            "offset_min": float(coeffs["offset_min"]),
                            "offset_max": float(coeffs["offset_max"]),
                            "valid_pixel_total": int(coeffs["valid_pixel_total"]),
                            "empty_tiles": int(coeffs["empty_tiles"]),
                            "offset_only_tiles": int(coeffs["offset_only_tiles"]),
                            "ok_tiles": int(coeffs["ok_tiles"]),
                            "scales": coeffs["scales"].tolist(),
                            "offsets": coeffs["offsets"].tolist(),
                            "valid_pixels": coeffs["valid_pixels"].astype(np.uint64).tolist(),
                            "statuses": coeffs["statuses"],
                        }
                    if application_profile is not None:
                        local_norm_application_profiles.append(application_profile)
                    local_norm_frame_results.append(
                        {
                            "frame_id": str(frame["id"]),
                            "reference_frame_id": str(reference_frame["id"]),
                            "model": local_norm_mode,
                            "scale": float(scale),
                            "offset": float(offset),
                            "source_mean": None if source_stats is None else float(source_stats["mean"]),
                            "source_std": None if source_stats is None else float(source_stats["std"]),
                            "reference_mean": reference_mean,
                            "reference_std": reference_std,
                            "valid_pixels": None if source_stats is None else int(source_stats["valid_pixels"]),
                            "grid_coefficients": grid_coefficients,
                            "application_profile": application_profile,
                            "status": status,
                            "warnings": warnings,
                        }
                    )
                if pending_grid_apply:
                    batch_indices = np.asarray(
                        [int(item["frame_index"]) for item in pending_grid_apply],
                        dtype=np.int32,
                    )
                    batch_scales = np.stack(
                        [np.asarray(item["scales"], dtype=np.float32) for item in pending_grid_apply]
                    ).astype(np.float32, copy=False)
                    batch_offsets = np.stack(
                        [np.asarray(item["offsets"], dtype=np.float32) for item in pending_grid_apply]
                    ).astype(np.float32, copy=False)
                    batch_apply = stack.apply_grid_normalization_frames(
                        batch_indices,
                        batch_scales,
                        batch_offsets,
                        resident_local_normalization_tile_size,
                        resident_local_normalization_tile_size,
                    )
                    local_norm_grid_apply_batch_profile = {
                        key: value
                        for key, value in batch_apply.items()
                        if key not in {"frames", "frame_indices"}
                    }
                    frame_profiles = {
                        int(profile["frame_index"]): profile for profile in batch_apply.get("frames", [])
                    }
                    for item in pending_grid_apply:
                        result_index = int(item["result_index"])
                        frame_index = int(item["frame_index"])
                        application_profile = frame_profiles.get(frame_index)
                        if application_profile is None:
                            raise RuntimeError(
                                "resident grid local normalization batch apply did not return a frame profile"
                            )
                        local_norm_frame_results[result_index]["application_profile"] = application_profile
                        local_norm_application_profiles.append(application_profile)
            else:
                local_norm_warnings.append(
                    "resident CUDA local normalization disabled; use --local-normalization on to enable it"
                )
            local_norm_elapsed = perf_counter() - local_norm_start
            local_norm_groups.append(
                {
                    "filter": filter_name,
                    "enabled": local_norm_enabled,
                    "mode": local_norm_mode,
                    "tile_size": (
                        resident_local_normalization_tile_size
                        if resident_local_normalization_mode == "grid_mean_std" and local_norm_enabled
                        else None
                    ),
                    "reference_frame_id": str(reference_frame["id"]),
                    "reference_index": reference_index,
                    "crop_box": None,
                    "frame_results": local_norm_frame_results,
                    "grid_stats": _resident_local_norm_grid_stats_summary(local_norm_grid_stats_batch_profile),
                    "application": _resident_local_norm_application_summary(local_norm_application_profiles),
                    "grid_apply": {
                        "schema_version": 1,
                        "supported": bool(resident_grid_ln_batch_apply_supported),
                        "enabled": bool(resident_grid_ln_batch_apply_enabled),
                        "available": bool(local_norm_grid_apply_batch_profile),
                        "batched": bool(local_norm_grid_apply_batch_profile),
                        "profile": local_norm_grid_apply_batch_profile or {},
                    },
                    "timing_s": local_norm_elapsed,
                    "warnings": local_norm_warnings,
                }
            )

            group_frame_ids = [str(frame["id"]) for frame in light_frames]
            group_registration_results = [
                registration_by_frame_id[frame_id]
                for frame_id in group_frame_ids
                if frame_id in registration_by_frame_id
            ]
            group_registration_quality_decisions_for_mask = [
                registration_quality_decisions_by_frame[frame_id]
                for frame_id in group_frame_ids
                if frame_id in registration_quality_decisions_by_frame
            ]
            group_manual_excluded_frame_ids = [
                str(frame["id"]) for frame in light_frames if _matches_any_token(frame, excluded_tokens)
            ]
            group_frame_mask_contract = build_resident_frame_mask_contract(
                frame_ids=group_frame_ids,
                frame_weights=[float(value) for value in frame_weight_values],
                registration_results=group_registration_results,
                registration_quality_decisions=group_registration_quality_decisions_for_mask,
                manual_excluded_frame_ids=group_manual_excluded_frame_ids,
                weighting_frame_results=weighting_frame_results,
                local_norm_frame_results=local_norm_frame_results,
                filter_name=filter_name,
                registration_mode=resident_registration,
                integration_dispatch=resident_integration_dispatch,
            )
            validate_resident_frame_mask_contract(group_frame_mask_contract)
            resident_frame_mask_contract_groups.append(group_frame_mask_contract)

            coverage_map = None
            low_rejection_map = None
            high_rejection_map = None
            weights_array = np.asarray(frame_weight_values, dtype=np.float32)
            weights_arg = None if np.all(weights_array == 1.0) else weights_array
            active_frame_count = int(np.count_nonzero(np.isfinite(weights_array) & (weights_array > 0.0)))
            resident_winsorized_contract = _resident_winsorized_contract_with_active_count(
                resident_winsorized_contract,
                active_frame_count=active_frame_count,
            )
            _validate_resident_winsorized_runtime_contract(resident_winsorized_contract)
            group_resident_winsorized_mode = str(
                resident_winsorized_contract["resident_winsorized_mode"]
            )
            source_dq_summary = build_resident_source_dq_summary(
                source_dq_rows,
                frame_count=len(light_frames),
                height=height,
                width=width,
                active_frame_count=active_frame_count,
                active_frame_ids=group_frame_mask_contract["summary"]["active_frame_ids"],
                fast_skip_frame_count=source_dq_fast_skipped_frame_count,
                fast_skip_reason=source_dq_fast_skip_reason,
            )
            group_source_dq_execution = build_resident_source_dq_execution_group(
                source_dq_summary,
                filter_name=filter_name,
                frame_count=len(light_frames),
                height=height,
                width=width,
                resident_calibration_batch_frames=resident_calibration_batch_frames,
            )
            validate_resident_source_dq_execution_group(group_source_dq_execution)
            resident_source_dq_execution_groups.append(group_source_dq_execution)
            tile_local_apply_enabled = False
            tile_local_target_mask = None
            tile_local_extents = None
            tile_local_multipliers = None
            tile_local_application_summary: dict[str, Any] = {}
            if (
                resident_tile_local_policy_mode in {"apply_mean", "apply"}
                and group_tile_local_policy_replay.get("enabled")
            ):
                group_frame_ids = {str(frame["id"]) for frame in light_frames}
                target_ids = {
                    str(frame_id)
                    for frame_id in group_tile_local_policy_replay.get("target_frame_ids", [])
                }
                if group_frame_ids.isdisjoint(target_ids):
                    group_tile_local_policy_replay.update(
                        {
                            "applied": False,
                            "effective_mode": "record",
                            "application_status": "skipped_no_target_frames_in_group",
                        }
                    )
                else:
                    if not hasattr(stack, "integrate_tile_local_mean"):
                        raise RuntimeError("resident CUDA backend does not expose integrate_tile_local_mean")
                    (
                        tile_local_target_mask,
                        tile_local_extents,
                        tile_local_multipliers,
                        tile_local_application_summary,
                    ) = _tile_local_policy_application_arrays(
                        group_tile_local_policy_replay,
                        light_frames,
                        width,
                        height,
                    )
                    tile_local_apply_enabled = True
            geometric_warp_coverage_map = None
            geometric_warp_coverage_frame_count = 0
            fused_matrix_integration_used = resident_integration_dispatch == "fused_matrix"
            fused_matrix_integration_timing: dict[str, Any] = {}
            hardened_winsorized_timing: dict[str, Any] = {}
            fused_matrix_download_mode = "master_only" if resident_output_maps == "minimal" else "full"
            stack_integration_download_mode = "master_only" if resident_output_maps == "minimal" else "full"
            if fused_matrix_integration_used:
                stack_integration_native_map_workspace_mode = "not_applicable_fused_matrix_dispatch"
            elif tile_local_apply_enabled:
                stack_integration_native_map_workspace_mode = "not_applicable_tile_local_dispatch"
            elif rejection_mode == "none":
                stack_integration_native_map_workspace_mode = "not_applicable_mean_integration"
            elif (
                rejection_mode == "winsorized_sigma"
                and group_resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                and resident_winsorized_contract.get("hardened_execution_route")
                == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
            ):
                stack_integration_native_map_workspace_mode = "cpu_stack_engine_segmented_hardened_download_workspace"
            elif stack_integration_download_mode == "master_only":
                stack_integration_native_map_workspace_mode = (
                    "master_only_no_weight_or_diagnostic_device_maps"
                )
            elif (
                rejection_mode == "winsorized_sigma"
                and group_resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
            ):
                stack_integration_native_map_workspace_mode = "standard_hardened_winsorized_workspace"
            else:
                stack_integration_native_map_workspace_mode = "full_weight_and_diagnostic_device_maps"
            if (
                resident_warp_coverage_supported
                and not fused_matrix_integration_used
                and resident_output_maps != "minimal"
            ):
                for index, weight in enumerate(frame_weight_values):
                    if weight > 0.0 and index not in warped_frame_indices:
                        stack.accumulate_full_warp_coverage_frame()
                geometric_warp_coverage_frame_count = int(stack.warp_coverage_frame_count)
                geometric_warp_coverage_map = stack.warp_coverage_map()

            integrate_start = perf_counter()
            if fused_matrix_integration_used:
                integration_matrix_array = np.asarray(integration_matrices, dtype=np.float32)
                fused_weights_arg = weights_array
                if rejection_mode == "none":
                    if not hasattr(stack, "integrate_matrix_warped_mean"):
                        raise RuntimeError("resident CUDA backend does not expose integrate_matrix_warped_mean")
                    (
                        master,
                        weight_map,
                        coverage_map,
                        geometric_warp_coverage_map,
                        fused_matrix_integration_timing,
                    ) = stack.integrate_matrix_warped_mean(
                        integration_matrix_array,
                        fused_weights_arg,
                        interpolation=resident_warp_interpolation,
                        clamping_threshold=resident_warp_clamping_threshold,
                        download_mode=fused_matrix_download_mode,
                    )
                else:
                    if not hasattr(stack, "integrate_matrix_warped_sigma_clip"):
                        raise RuntimeError(
                            "resident CUDA backend does not expose integrate_matrix_warped_sigma_clip"
                        )
                    winsorize = rejection_mode == "winsorized_sigma"
                    (
                        master,
                        weight_map,
                        coverage_map,
                        low_rejection_map,
                        high_rejection_map,
                        geometric_warp_coverage_map,
                        fused_matrix_integration_timing,
                    ) = stack.integrate_matrix_warped_sigma_clip(
                        integration_matrix_array,
                        fused_weights_arg,
                        interpolation=resident_warp_interpolation,
                        clamping_threshold=resident_warp_clamping_threshold,
                        low_sigma=low_sigma,
                        high_sigma=high_sigma,
                        winsorize=winsorize,
                        download_mode=fused_matrix_download_mode,
                    )
                geometric_warp_coverage_frame_count = (
                    active_frame_count if geometric_warp_coverage_map is not None else 0
                )
            elif tile_local_apply_enabled:
                if rejection_mode == "none":
                    master, weight_map, tile_local_timing = stack.integrate_tile_local_mean(
                        tile_local_target_mask,
                        tile_local_extents,
                        tile_local_multipliers,
                        weights_arg,
                    )
                    tile_local_status = "applied_mean_rejection_none"
                    tile_local_native_method = "ResidentCalibratedStack.integrate_tile_local_mean"
                    tile_local_limitations = [
                        "This opt-in path applies tile-local multipliers to rejection=none weighted mean.",
                    ]
                else:
                    if not hasattr(stack, "integrate_tile_local_sigma_clip"):
                        raise RuntimeError("resident CUDA backend does not expose integrate_tile_local_sigma_clip")
                    winsorize = rejection_mode == "winsorized_sigma"
                    (
                        master,
                        weight_map,
                        coverage_map,
                        low_rejection_map,
                        high_rejection_map,
                        tile_local_timing,
                    ) = stack.integrate_tile_local_sigma_clip(
                        tile_local_target_mask,
                        tile_local_extents,
                        tile_local_multipliers,
                        weights_arg,
                        low_sigma,
                        high_sigma,
                        winsorize,
                    )
                    tile_local_status = f"applied_{rejection_mode}"
                    tile_local_native_method = "ResidentCalibratedStack.integrate_tile_local_sigma_clip"
                    tile_local_limitations = [
                        "This opt-in path applies tile-local multipliers before resident rejection accumulation.",
                        "Fused-matrix dispatch remains unsupported for tile-local policy application.",
                    ]
                group_tile_local_policy_replay.update(
                    {
                        **tile_local_application_summary,
                        "applied": True,
                        "effective_mode": resident_tile_local_policy_mode,
                        "application_status": tile_local_status,
                        "native_method": tile_local_native_method,
                        "native_timing_s": tile_local_timing,
                        "native_requirement": "satisfied",
                        "limitations": tile_local_limitations,
                    }
                )
                tile_local_policy_any_applied = True
            elif rejection_mode == "none":
                master, weight_map = stack.integrate_mean(weights_arg)
            elif (
                rejection_mode == "winsorized_sigma"
                and group_resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
                and resident_winsorized_contract.get("hardened_execution_route")
                == RESIDENT_WINSORIZED_SIGMA_SEGMENTED_CPU_ROUTE
            ):
                (
                    master,
                    weight_map,
                    coverage_map,
                    low_rejection_map,
                    high_rejection_map,
                    hardened_winsorized_timing,
                ) = _integrate_resident_hardened_winsorized_with_cpu_stack_engine(
                    stack,
                    light_frames,
                    weights_array,
                    width=width,
                    height=height,
                    low_sigma=low_sigma,
                    high_sigma=high_sigma,
                    min_samples=rejection_min_samples,
                    max_reject_fraction=group_rejection_max_fraction,
                    tile_size=min(_RESIDENT_MASTER_STACK_TILE_SIZE, 256),
                )
            elif (
                rejection_mode == "winsorized_sigma"
                and group_resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE
            ):
                if not hasattr(stack, "integrate_hardened_winsorized_sigma"):
                    raise RuntimeError(
                        "resident CUDA backend does not expose integrate_hardened_winsorized_sigma"
                    )
                (
                    master,
                    weight_map,
                    coverage_map,
                    low_rejection_map,
                    high_rejection_map,
                    hardened_winsorized_timing,
                ) = stack.integrate_hardened_winsorized_sigma_timed(
                    weights_arg,
                    low_sigma,
                    high_sigma,
                    min_samples=rejection_min_samples,
                    max_reject_fraction=group_rejection_max_fraction,
                    count_map_dtype="uint16",
                    download_mode=stack_integration_download_mode,
                )
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
                ) = stack.integrate_sigma_clip(
                    weights_arg,
                    low_sigma,
                    high_sigma,
                    winsorize,
                    download_mode=stack_integration_download_mode,
                )
            integrate_elapsed = perf_counter() - integrate_start
            output_diagnostics = _output_diagnostics(master, weight_map)
            output_map_selection = _resident_output_map_selection(resident_output_maps)
            master_path = output_dir / f"resident_master_{filt}.fits"
            weight_path = (
                output_dir / f"resident_weight_map_{filt}.fits" if output_map_selection["weight"] else None
            )
            coverage_path = (
                output_dir / f"resident_coverage_map_{filt}.fits"
                if coverage_map is not None and output_map_selection["coverage"]
                else None
            )
            low_rejection_path = (
                output_dir / f"resident_low_rejection_map_{filt}.fits"
                if low_rejection_map is not None and output_map_selection["low_rejection"]
                else None
            )
            high_rejection_path = (
                output_dir / f"resident_high_rejection_map_{filt}.fits"
                if high_rejection_map is not None and output_map_selection["high_rejection"]
                else None
            )
            dq_map = None
            dq_summary = None
            dq_map_stats: dict[str, Any] | None = None
            dq_path = output_dir / f"resident_dq_map_{filt}.fits" if output_map_selection["dq"] else None
            if output_map_selection["dq"]:
                clipping_probe = (
                    output_diagnostics.get("clipping_probe")
                    if isinstance(output_diagnostics.get("clipping_probe"), dict)
                    else {}
                )
                total_output_pixels = int(output_diagnostics.get("total_pixels", np.asarray(master).size) or 0)
                assume_valid_master_weight = bool(
                    total_output_pixels > 0
                    and int(output_diagnostics.get("nonfinite_pixels", -1) or 0) == 0
                    and int(clipping_probe.get("nonfinite_count", -1) or 0) == 0
                    and int(clipping_probe.get("zero_weight_pixels", -1) or 0) == 0
                    and int(clipping_probe.get("positive_weight_pixels", -1) or 0) == total_output_pixels
                )
                dq_map, dq_summary, dq_map_stats = _resident_dq_map(
                    master,
                    weight_map,
                    coverage_map,
                    low_rejection_map,
                    high_rejection_map,
                    geometric_warp_coverage_map=geometric_warp_coverage_map,
                    active_frame_count=active_frame_count,
                    return_stats=True,
                    assume_finite_count_maps=True,
                    assume_nonnegative_count_maps=True,
                    assume_valid_master_weight=assume_valid_master_weight,
                    dq_dtype=np.int16,
                )
            dq_map_stats_payload = dq_map_stats if isinstance(dq_map_stats, dict) else {}
            rejection_map_stats = {
                "low_rejection": dq_map_stats_payload.get("low_rejection")
                if isinstance(dq_map_stats_payload.get("low_rejection"), dict)
                else (
                    _resident_count_map_array_stats(low_rejection_map)
                    if low_rejection_map is not None
                    else {"present": False}
                ),
                "high_rejection": dq_map_stats_payload.get("high_rejection")
                if isinstance(dq_map_stats_payload.get("high_rejection"), dict)
                else (
                    _resident_count_map_array_stats(high_rejection_map)
                    if high_rejection_map is not None
                    else {"present": False}
                ),
            }
            dq_coverage_provenance = _resident_dq_coverage_provenance(
                coverage_map,
                low_rejection_map,
                high_rejection_map,
                active_frame_count,
                geometric_warp_coverage_map=geometric_warp_coverage_map,
                geometric_warp_coverage_frame_count=geometric_warp_coverage_frame_count,
                source_dq_summary=source_dq_summary,
                rejection_map_stats=rejection_map_stats,
                precomputed_dq_stats=dq_map_stats,
            )
            dq_provenance_summary = dq_provenance_summary_from_resident(
                dq_coverage_provenance,
                dq_summary,
                item=filt,
            )
            group_dq_pixel_closure = build_resident_dq_pixel_closure_group(
                output={
                    "filter": filt,
                    "frame_count": len(light_frames),
                    "rejection": rejection_mode,
                    "dq_summary": dq_summary,
                    "dq_coverage_provenance": dq_coverage_provenance,
                    "dq_provenance_summary": dq_provenance_summary,
                    "source_dq_summary": source_dq_summary,
                    "geometric_warp_coverage": {
                        "available": bool(geometric_warp_coverage_map is not None),
                        "frame_count": geometric_warp_coverage_frame_count,
                        "frame_count_matches_active": geometric_warp_coverage_frame_count == active_frame_count,
                    },
                    "resident_frame_mask_contract": {
                        "summary": group_frame_mask_contract["summary"],
                    },
                },
                frame_mask_contract=group_frame_mask_contract,
                filter_name=filter_name,
            )
            validate_resident_dq_pixel_closure_group(group_dq_pixel_closure)
            resident_dq_pixel_closure_groups.append(group_dq_pixel_closure)
            group_dq_lifecycle = build_resident_dq_lifecycle_group(
                source_dq_execution_group=group_source_dq_execution,
                frame_mask_group=group_frame_mask_contract,
                dq_pixel_closure_group=group_dq_pixel_closure,
                filter_name=filter_name,
            )
            validate_resident_dq_lifecycle_group(group_dq_lifecycle)
            resident_dq_lifecycle_groups.append(group_dq_lifecycle)
            count_dtype = _count_map_dtype(len(light_frames))
            available_output_maps = ["master"]
            if weight_map is not None:
                available_output_maps.append("weight")
            if dq_map is not None:
                available_output_maps.append("dq")
            if coverage_map is not None:
                available_output_maps.append("coverage")
            if low_rejection_map is not None:
                available_output_maps.append("low_rejection")
            if high_rejection_map is not None:
                available_output_maps.append("high_rejection")
            output_specs: list[dict[str, Any]] = [
                {
                    "name": "master",
                    "path": master_path,
                    "data": master,
                    "header": {"IMAGETYP": "master", "FILTER": filter_name},
                    "dtype": np.float32,
                },
            ]
            if weight_path is not None:
                output_specs.append(
                    {
                        "name": "weight",
                        "path": weight_path,
                        "data": weight_map,
                        "header": {"IMAGETYP": "weight", "FILTER": filter_name},
                        "dtype": np.float32,
                    }
                )
            if dq_map is not None and dq_path is not None:
                output_specs.append(
                    {
                        "name": "dq",
                        "path": dq_path,
                        "data": dq_map,
                        "header": {
                            "IMAGETYP": "dq_mask",
                            "FILTER": filter_name,
                            "DQSTAGE": "integration",
                            "DQFLAGS": "NO_DATA,WARP_EDGE,LOW_REJECTED,HIGH_REJECTED",
                        },
                        "dtype": np.int16,
                    }
                )
            if coverage_map is not None and coverage_path is not None:
                output_specs.append(
                    {
                        "name": "coverage",
                        "path": coverage_path,
                        "data": coverage_map,
                        "header": {"IMAGETYP": "coverage", "FILTER": filter_name, "DTYPE": np.dtype(count_dtype).name},
                        "dtype": count_dtype,
                        "round_counts": True,
                    }
                )
            if low_rejection_map is not None and low_rejection_path is not None:
                output_specs.append(
                    {
                        "name": "low_rejection",
                        "path": low_rejection_path,
                        "data": low_rejection_map,
                        "header": {"IMAGETYP": "rej_low", "FILTER": filter_name, "DTYPE": np.dtype(count_dtype).name},
                        "dtype": count_dtype,
                        "round_counts": True,
                    }
                )
            if high_rejection_map is not None and high_rejection_path is not None:
                output_specs.append(
                    {
                        "name": "high_rejection",
                        "path": high_rejection_path,
                        "data": high_rejection_map,
                        "header": {"IMAGETYP": "rej_high", "FILTER": filter_name, "DTYPE": np.dtype(count_dtype).name},
                        "dtype": count_dtype,
                        "round_counts": True,
                    }
                )
            written_output_maps = [str(spec["name"]) for spec in output_specs]
            skipped_output_maps = [
                name for name in available_output_maps if name not in set(written_output_maps)
            ]
            write_elapsed, write_breakdown, write_storage, output_write_workers = _write_resident_outputs(output_specs)

            try:
                master_cache_async_write_summary = master_cache_write_queue.wait_all()
            finally:
                master_cache_write_queue.shutdown()
                resident_master_cache_write_queues.remove(master_cache_write_queue)

            first_master_stats = next(iter(master_stats_sets.values()), {})
            master_stats = {
                "calibration_group_policy": "planner_matching_groups_per_light",
                "set_count": len(master_stats_sets),
                "bias_count": first_master_stats.get("bias_count"),
                "dark_count": first_master_stats.get("dark_count"),
                "flat_count": first_master_stats.get("flat_count"),
                "sets": master_stats_sets,
            }
            group_master_cache = build_resident_master_cache_group(
                filter_name=filter_name,
                master_stats=master_stats,
            )
            resident_master_cache_groups.append(group_master_cache)
            memory_estimate = _memory_estimate(
                len(light_frames),
                height,
                width,
                resident_registration=resident_registration,
                resident_warp_batch_dispatch=resident_warp_batch_dispatch,
                chunked_warp_frame_count=triangle_warp_batch_frame_count
                if resident_registration == "similarity_cuda_triangle"
                else None,
                chunked_warp_capacity_frames=resident_warp_chunk_capacity_effective
                if resident_registration == "similarity_cuda_triangle"
                else None,
                observed_chunked_warp_chunk_frames=triangle_warp_batch_native_chunk_frames
                if resident_registration == "similarity_cuda_triangle"
                else 0,
                observed_chunked_warp_workspace_bytes=triangle_warp_batch_native_workspace_bytes
                if resident_registration == "similarity_cuda_triangle"
                else 0,
                observed_chunked_warp_output_bytes=triangle_warp_batch_native_output_bytes
                if resident_registration == "similarity_cuda_triangle"
                else 0,
                observed_chunked_warp_coverage_bytes=triangle_warp_batch_native_coverage_bytes
                if resident_registration == "similarity_cuda_triangle"
                else 0,
                observed_chunked_warp_inverse_bytes=triangle_warp_batch_native_inverse_batch_bytes
                if resident_registration == "similarity_cuda_triangle"
                else 0,
            )
            read_timing = _timing_summary(per_frame_read_s)
            read_worker_timing = _timing_summary(per_frame_read_worker_s)
            fits_open_timing = _timing_summary(per_frame_fits_open_s)
            fits_materialize_decode_timing = _timing_summary(per_frame_fits_materialize_decode_s)
            fits_backend_counts = _value_counts(per_frame_fits_backend)
            fits_fallback_reason_counts = _value_counts(per_frame_fits_fallback_reason)
            fits_native_file_read_timing = _timing_summary(per_frame_fits_native_file_read_s)
            fits_native_decode_timing = _timing_summary(per_frame_fits_native_decode_s)
            fits_native_total_timing = _timing_summary(per_frame_fits_native_total_s)
            fits_native_bytes_read = int(sum(per_frame_fits_native_bytes_read))
            calibrate_timing = _timing_summary(per_frame_calibrate_s)
            host_copy_timing = _timing_summary(per_frame_host_copy_s)
            h2d_timing = _timing_summary(per_frame_h2d_s)
            calibrate_store_timing = _timing_summary(per_frame_calibrate_store_s)
            registration_timing = _timing_summary(per_frame_registration_s)
            unique_calibration_event_modes = sorted(set(calibration_event_modes))
            calibration_event_mode = (
                unique_calibration_event_modes[0]
                if len(unique_calibration_event_modes) == 1
                else "mixed"
            )
            native_path_calibration_report = {
                "native_path_calibration_candidate": bool(native_path_calibration_candidate),
                "native_path_calibration_policy": str(native_path_calibration_policy),
                "native_path_calibration_requested": bool(native_path_calibration_requested),
                "native_path_calibration_available": bool(native_path_calibration_available),
                "native_path_calibration_enabled": bool(native_path_calibration_enabled),
                "native_path_calibration_reason": str(native_path_calibration_reason),
                "native_path_calibration_batch_count": int(native_path_calibration_batch_count),
                "native_path_calibration_frame_count": int(native_path_calibration_frame_count),
                "native_path_calibration_file_open_s": float(native_path_calibration_file_open_s),
                "native_path_calibration_file_read_s": float(native_path_calibration_file_read_s),
                "native_path_calibration_total_s": float(native_path_calibration_total_s),
                "native_path_calibration_host_buffer_bytes": int(native_path_calibration_host_buffer_bytes),
                "native_path_calibration_wave_h2d_elapsed_s": float(
                    native_path_calibration_wave_h2d_elapsed_s
                ),
                "native_path_calibration_host_buffer_model": native_path_calibration_host_buffer_model,
                "native_path_calibration_host_buffer_pinned": bool(
                    native_path_calibration_host_buffer_pinned
                ),
                "native_completion_calibration_candidate": bool(native_completion_calibration_candidate),
                "native_completion_calibration_policy": str(native_completion_calibration_policy),
                "native_completion_calibration_requested": bool(native_completion_calibration_requested),
                "native_completion_calibration_available": bool(native_completion_calibration_available),
                "native_completion_calibration_enabled": bool(native_completion_calibration_enabled),
                "native_completion_calibration_reason": str(native_completion_calibration_reason),
                "native_completion_calibration_submit_count": int(
                    native_completion_calibration_submit_count
                ),
                "native_completion_calibration_completion_count": int(
                    native_completion_calibration_completion_count
                ),
                "native_completion_calibration_out_of_order_count": int(
                    native_completion_calibration_out_of_order_count
                ),
                "native_completion_calibration_worker_count": int(
                    native_completion_calibration_worker_count
                ),
                "native_completion_calibration_queue_buffer_count": int(
                    native_completion_calibration_queue_buffer_count
                ),
                "native_completion_calibration_order_sample": list(
                    native_completion_calibration_order_sample
                ),
                "native_completion_calibration_slot_release_mode": native_completion_calibration_slot_release_mode,
                "native_completion_calibration_slot_reuse_count": int(
                    native_completion_calibration_slot_reuse_count
                ),
                "native_completion_calibration_slot_reuse_query_count": int(
                    native_completion_calibration_slot_reuse_query_count
                ),
                "native_completion_calibration_slot_reuse_ready_count": int(
                    native_completion_calibration_slot_reuse_ready_count
                ),
                "native_completion_calibration_slot_reuse_wait_count": int(
                    native_completion_calibration_slot_reuse_wait_count
                ),
                "native_completion_calibration_slot_reuse_wait_s": float(
                    native_completion_calibration_slot_reuse_wait_s
                ),
                "native_completion_calibration_final_h2d_collect_count": int(
                    native_completion_calibration_final_h2d_collect_count
                ),
                "native_completion_calibration_consumer_schedule_mode": (
                    native_completion_calibration_consumer_schedule_mode
                ),
                "native_completion_calibration_consumer_wave_fill_mode": (
                    native_completion_calibration_consumer_wave_fill_mode
                ),
                "native_completion_calibration_consumer_wave_fill_mode_requested": (
                    native_completion_wave_fill_mode
                ),
                "native_completion_calibration_consumer_wave_fill_mode_source": (
                    native_completion_wave_fill_mode_source
                ),
                "native_completion_calibration_consumer_wave_fill_policy": (
                    native_completion_calibration_consumer_wave_fill_policy
                ),
                "native_completion_calibration_consumer_wave_fill_source": (
                    native_completion_wave_fill_source
                ),
                "native_completion_calibration_consumer_wave_fill_wait_us": int(
                    native_completion_calibration_consumer_wave_fill_wait_us
                ),
                "native_completion_calibration_consumer_wave_fill_requested_wait_us": int(
                    native_completion_wave_fill_wait_us
                ),
                "native_completion_calibration_consumer_wave_fill_wait_count": int(
                    native_completion_calibration_consumer_wave_fill_wait_count
                ),
                "native_completion_calibration_consumer_wave_fill_timeout_count": int(
                    native_completion_calibration_consumer_wave_fill_timeout_count
                ),
                "native_completion_calibration_consumer_wave_fill_wait_s": float(
                    native_completion_calibration_consumer_wave_fill_wait_s
                ),
                "native_completion_calibration_consumer_wave_count": int(
                    native_completion_calibration_consumer_wave_count
                ),
                "native_completion_calibration_consumer_max_wave_frames": int(
                    native_completion_calibration_consumer_max_wave_frames
                ),
                "native_completion_calibration_consumer_multi_frame_wave_count": int(
                    native_completion_calibration_consumer_multi_frame_wave_count
                ),
            }
            registration_total = registration_timing["total"]
            registration_component_total = float(
                sum(
                    value
                    for key, value in registration_component_s.items()
                    if not key.endswith("_frame_total") and not key.endswith("_batch")
                )
            )
            registration_orchestration_elapsed = max(0.0, registration_total - registration_component_total)
            registration_deferred_elapsed = max(0.0, registration_total - registration_during_load_elapsed)
            read_wait_total = read_timing["total"]
            read_worker_total = read_worker_timing["total"]
            read_overlap_saved = max(0.0, read_worker_total - read_wait_total)
            read_overlap_efficiency = (
                read_overlap_saved / read_worker_total if read_worker_total > 0.0 else None
            )
            read_wait_fraction_of_wall = (
                read_wait_total / load_calibrate_elapsed if load_calibrate_elapsed > 0.0 else None
            )
            read_worker_to_wall_ratio = (
                read_worker_total / load_calibrate_elapsed if load_calibrate_elapsed > 0.0 else None
            )
            resident_io_overlap = {
                "schema_version": 1,
                "wall_clock_stage_s": load_calibrate_elapsed,
                "consumer_read_wait_wall_s": read_wait_total,
                "worker_read_cumulative_s": read_worker_total,
                "worker_fits_open_cumulative_s": fits_open_timing["total"],
                "worker_fits_materialize_decode_cumulative_s": fits_materialize_decode_timing["total"],
                "overlap_saved_s": read_overlap_saved,
                "overlap_efficiency": read_overlap_efficiency,
                "consumer_wait_fraction_of_wall": read_wait_fraction_of_wall,
                "worker_cumulative_to_wall_ratio": read_worker_to_wall_ratio,
                "prefetch_enabled": bool(resident_prefetch_frames > 0),
                "prefetch_frames": int(resident_prefetch_frames),
                "prefetch_workers": int(resident_prefetch_workers) if resident_prefetch_frames > 0 else 0,
                "prefetch_host_allocation_mode": str(light_prefetch.pinned_host_allocation_mode),
                "prefetch_host_allocation_count": int(light_prefetch.pinned_host_allocation_count),
                "prefetch_host_allocation_fallback_reason": str(
                    light_prefetch.pinned_host_allocation_fallback_reason
                ),
                "fits_read_mode": resident_fits_read_mode,
                "fits_read_mode_requested": resident_fits_read_mode,
                "fits_read_mode_effective": resident_fits_read_mode_effective,
                "fits_read_mode_resolution": resident_fits_read_mode_resolution_payload,
                "resident_fits_auto_selection": resident_fits_auto_selection,
                "fits_header_spec_cache_enabled": bool(resident_fits_spec_cache),
                "fits_header_spec_cache_frame_count": int(len(resident_fits_spec_cache)),
                "fits_header_spec_cache_hit_count": int(per_frame_fits_header_cache_hits),
                "fits_backend_counts": fits_backend_counts,
                "fits_fast_fallback_reason_counts": fits_fallback_reason_counts,
                "fits_native_file_read_cumulative_s": fits_native_file_read_timing["total"],
                "fits_native_decode_cumulative_s": fits_native_decode_timing["total"],
                "fits_native_total_cumulative_s": fits_native_total_timing["total"],
                "fits_native_bytes_read": fits_native_bytes_read,
                "raw_gpu_decode_enabled": raw_u16_gpu_decode_enabled,
                "raw_gpu_h2d_bytes": int(calibration_raw_h2d_bytes),
                "raw_gpu_float32_host_bytes_avoided": int(calibration_float32_host_bytes_avoided),
                "source_dq_fast_skip_enabled": bool(source_dq_fast_skip_enabled),
                "source_dq_fast_skipped_frame_count": int(source_dq_fast_skipped_frame_count),
                "source_dq_fast_skip_reason": source_dq_fast_skip_reason,
                "source_dq_sidecar_frame_count": int(source_dq_sidecar_frame_count),
                "calibration_fetch_batch_requested_frames": int(calibration_fetch_batch_requested_frames),
                "calibration_fetch_batch_frames": int(calibration_fetch_batch_frames),
                "calibration_fetch_batch_limit_source": calibration_fetch_batch_limit_source,
                "calibration_fetch_batch_clamped_to_prefetch_depth": bool(
                    calibration_fetch_batch_clamped_to_prefetch_depth
                ),
                "calibration_order_mode": calibration_order_mode,
                "calibration_ready_order_enabled": bool(calibration_ready_order_enabled),
                "calibration_ready_order_reason": calibration_ready_order_reason,
                "calibration_ready_order_master_group_count": int(calibration_master_group_count),
                "calibration_ready_order_out_of_order_count": int(
                    calibration_ready_order_out_of_order_count
                ),
                "calibration_ready_order_select_wait_s": float(calibration_ready_order_select_wait_s),
                "calibration_remaining_index_model": str(calibration_remaining_index_model),
                "calibration_remaining_index_set_discard_count": int(
                    calibration_remaining_index_set_discard_count
                ),
                "calibration_remaining_index_cursor_advance_count": int(
                    calibration_remaining_index_cursor_advance_count
                ),
                "prefetch_ready_queue_callback_count": int(light_prefetch.ready_queue_callback_count),
                "prefetch_ready_queue_wait_count": int(light_prefetch.ready_queue_wait_count),
                "prefetch_ready_queue_wait_s": float(light_prefetch.ready_queue_wait_s),
                "prefetch_ready_candidate_probe_mode": str(light_prefetch.ready_candidate_probe_mode),
                "prefetch_ready_index_candidate_set_reuse_count": int(
                    light_prefetch.ready_index_candidate_set_reuse_count
                ),
                "prefetch_ready_batch_select_policy": str(light_prefetch.ready_batch_select_policy),
                "prefetch_ready_batch_select_enabled": bool(light_prefetch.ready_batch_select_enabled),
                "prefetch_ready_batch_select_count": int(light_prefetch.ready_batch_select_count),
                "prefetch_ready_batch_selected_count": int(light_prefetch.ready_batch_selected_count),
                "native_batch_read_candidate": bool(light_prefetch.native_batch_read_candidate),
                "native_batch_read_policy": str(light_prefetch.native_batch_read_policy),
                "native_batch_read_requested": bool(light_prefetch.native_batch_read_requested),
                "native_batch_read_available": bool(light_prefetch.native_batch_read_available),
                "native_batch_read_enabled": bool(light_prefetch.native_batch_read_enabled),
                "native_batch_read_submit_count": int(light_prefetch.native_batch_read_submit_count),
                "native_batch_read_frame_count": int(light_prefetch.native_batch_read_frame_count),
                "native_batch_read_max_frame_count": int(light_prefetch.native_batch_read_max_frame_count),
                "native_batch_read_worker_count": int(light_prefetch.native_batch_read_worker_count),
                "native_batch_read_wall_s": float(light_prefetch.native_batch_read_wall_s),
                "native_batch_read_cumulative_s": float(light_prefetch.native_batch_read_cumulative_s),
                "native_queue_read_candidate": bool(light_prefetch.native_queue_read_candidate),
                "native_queue_read_policy": str(light_prefetch.native_queue_read_policy),
                "native_queue_read_requested": bool(light_prefetch.native_queue_read_requested),
                "native_queue_read_available": bool(light_prefetch.native_queue_read_available),
                "native_queue_read_enabled": bool(light_prefetch.native_queue_read_enabled),
                "native_queue_read_drain_mode": str(light_prefetch.native_queue_read_drain_mode),
                "native_queue_read_drain_source": str(light_prefetch.native_queue_read_drain_source),
                "native_queue_read_submit_count": int(light_prefetch.native_queue_read_submit_count),
                "native_queue_read_completion_count": int(
                    light_prefetch.native_queue_read_completion_count
                ),
                "native_queue_read_worker_count": int(light_prefetch.native_queue_read_worker_count),
                "native_queue_read_cumulative_s": float(light_prefetch.native_queue_read_cumulative_s),
                "native_queue_read_completion_wait_s": float(
                    light_prefetch.native_queue_read_completion_wait_s
                ),
                "native_queue_read_inline_wait_count": int(
                    light_prefetch.native_queue_read_inline_wait_count
                ),
                "native_queue_read_thread_wait_count": int(
                    light_prefetch.native_queue_read_thread_wait_count
                ),
                **native_path_calibration_report,
                "master_cache_async_write": master_cache_async_write_summary,
                "note": (
                    "worker_* values are cumulative read-thread time and can exceed wall-clock time "
                    "when prefetch overlaps FITS decode with GPU upload/calibration."
                ),
            }
            light_loop_accounted_without_master = (
                read_wait_total
                + calibrate_timing["total"]
                + registration_during_load_elapsed
                + gc_elapsed
            )
            light_master_build_or_load_in_loop = float(master_elapsed)
            light_loop_accounted = light_loop_accounted_without_master + light_master_build_or_load_in_loop
            light_loop_unaccounted = max(0.0, load_calibrate_elapsed - light_loop_accounted)
            light_loop_unaccounted_without_master = max(
                0.0,
                load_calibrate_elapsed - light_loop_accounted_without_master,
            )
            light_pipeline_timing = {
                "light_read_upload_calibrate": load_calibrate_elapsed,
                "light_read_wait_wall": read_wait_total,
                "light_master_build_or_load_in_loop": light_master_build_or_load_in_loop,
                "light_calibration_batch_native_total": float(calibration_batch_native_total_s),
                "light_native_path_calibration_file_read": float(native_path_calibration_file_read_s),
                "light_native_path_calibration_total": float(native_path_calibration_total_s),
                "light_calibrate_store": calibrate_store_timing["total"],
                "light_calibration_batch_sync": float(calibration_batch_sync_s),
                "master_cache_async_write_wait": float(
                    master_cache_async_write_summary.get("wait_elapsed_s") or 0.0
                ),
                "master_cache_async_write_total": float(
                    master_cache_async_write_summary.get("write_elapsed_s_total") or 0.0
                ),
                "light_loop_unaccounted": light_loop_unaccounted,
                "light_loop_unaccounted_without_master": light_loop_unaccounted_without_master,
                "light_read_overlap_saved": read_overlap_saved,
            }
            light_pipeline_io = {
                "prefetch_frames": int(resident_prefetch_frames),
                "prefetch_workers": int(resident_prefetch_workers) if resident_prefetch_frames > 0 else 0,
                "prefetch_refill_mode": resident_prefetch_refill_mode,
                "h2d_mode": resident_h2d_mode,
                "prefetch_host_allocation_mode": str(light_prefetch.pinned_host_allocation_mode),
                "prefetch_host_allocation_count": int(light_prefetch.pinned_host_allocation_count),
                "prefetch_host_allocation_fallback_reason": str(
                    light_prefetch.pinned_host_allocation_fallback_reason
                ),
                "fits_read_mode": resident_fits_read_mode,
                "fits_read_mode_requested": resident_fits_read_mode,
                "fits_read_mode_effective": resident_fits_read_mode_effective,
                "fits_read_mode_resolution": resident_fits_read_mode_resolution_payload,
                "resident_fits_auto_selection": resident_fits_auto_selection,
                "fits_header_spec_cache_enabled": bool(resident_fits_spec_cache),
                "fits_header_spec_cache_frame_count": int(len(resident_fits_spec_cache)),
                "fits_header_spec_cache_hit_count": int(per_frame_fits_header_cache_hits),
                "fits_backend_counts": fits_backend_counts,
                "fits_fast_fallback_reason_counts": fits_fallback_reason_counts,
                "fits_native_file_read_cumulative_s": fits_native_file_read_timing["total"],
                "fits_native_decode_cumulative_s": fits_native_decode_timing["total"],
                "fits_native_total_cumulative_s": fits_native_total_timing["total"],
                "fits_native_bytes_read": fits_native_bytes_read,
                "raw_gpu_decode_enabled": raw_u16_gpu_decode_enabled,
                "raw_gpu_h2d_bytes": int(calibration_raw_h2d_bytes),
                "raw_gpu_float32_host_bytes_avoided": int(calibration_float32_host_bytes_avoided),
                "source_dq_fast_skip_enabled": bool(source_dq_fast_skip_enabled),
                "source_dq_fast_skipped_frame_count": int(source_dq_fast_skipped_frame_count),
                "source_dq_fast_skip_reason": source_dq_fast_skip_reason,
                "source_dq_sidecar_frame_count": int(source_dq_sidecar_frame_count),
                "calibration_batch_requested_frames": int(resident_calibration_batch_frames),
                "calibration_batch_requested_streams": int(resident_calibration_streams),
                "calibration_wave_requested_frames": int(resident_calibration_wave_frames),
                "calibration_wave_requested_effective_frames": int(calibration_wave_requested_effective_frames),
                "calibration_wave_effective_frames": int(calibration_wave_effective_frames),
                "calibration_wave_effective_source": calibration_wave_effective_source,
                "calibration_wave_lane_guard_applied": bool(calibration_wave_lane_guard_applied),
                "calibration_wave_stream_count_limit": int(resident_calibration_streams),
                "calibration_fetch_batch_requested_frames": int(calibration_fetch_batch_requested_frames),
                "calibration_fetch_batch_frames": int(calibration_fetch_batch_frames),
                "calibration_fetch_batch_limit_source": calibration_fetch_batch_limit_source,
                "calibration_fetch_batch_clamped_to_prefetch_depth": bool(
                    calibration_fetch_batch_clamped_to_prefetch_depth
                ),
                "calibration_order_mode": calibration_order_mode,
                "calibration_ready_order_enabled": bool(calibration_ready_order_enabled),
                "calibration_ready_order_reason": calibration_ready_order_reason,
                "calibration_ready_order_master_group_count": int(calibration_master_group_count),
                "calibration_ready_order_out_of_order_count": int(
                    calibration_ready_order_out_of_order_count
                ),
                "calibration_ready_order_select_wait_s": float(calibration_ready_order_select_wait_s),
                "calibration_release_mode_effective": calibration_release_mode_effective,
                "calibration_remaining_index_model": str(calibration_remaining_index_model),
                "calibration_remaining_index_set_discard_count": int(
                    calibration_remaining_index_set_discard_count
                ),
                "calibration_remaining_index_cursor_advance_count": int(
                    calibration_remaining_index_cursor_advance_count
                ),
                "prefetch_ready_queue_callback_count": int(light_prefetch.ready_queue_callback_count),
                "prefetch_ready_queue_wait_count": int(light_prefetch.ready_queue_wait_count),
                "prefetch_ready_queue_wait_s": float(light_prefetch.ready_queue_wait_s),
                "prefetch_ready_candidate_probe_mode": str(light_prefetch.ready_candidate_probe_mode),
                "prefetch_ready_index_candidate_set_reuse_count": int(
                    light_prefetch.ready_index_candidate_set_reuse_count
                ),
                "prefetch_ready_batch_select_policy": str(light_prefetch.ready_batch_select_policy),
                "prefetch_ready_batch_select_enabled": bool(light_prefetch.ready_batch_select_enabled),
                "prefetch_ready_batch_select_count": int(light_prefetch.ready_batch_select_count),
                "prefetch_ready_batch_selected_count": int(light_prefetch.ready_batch_selected_count),
                "native_batch_read_candidate": bool(light_prefetch.native_batch_read_candidate),
                "native_batch_read_policy": str(light_prefetch.native_batch_read_policy),
                "native_batch_read_requested": bool(light_prefetch.native_batch_read_requested),
                "native_batch_read_available": bool(light_prefetch.native_batch_read_available),
                "native_batch_read_enabled": bool(light_prefetch.native_batch_read_enabled),
                "native_batch_read_submit_count": int(light_prefetch.native_batch_read_submit_count),
                "native_batch_read_frame_count": int(light_prefetch.native_batch_read_frame_count),
                "native_batch_read_max_frame_count": int(light_prefetch.native_batch_read_max_frame_count),
                "native_batch_read_worker_count": int(light_prefetch.native_batch_read_worker_count),
                "native_batch_read_wall_s": float(light_prefetch.native_batch_read_wall_s),
                "native_batch_read_cumulative_s": float(light_prefetch.native_batch_read_cumulative_s),
                "native_queue_read_candidate": bool(light_prefetch.native_queue_read_candidate),
                "native_queue_read_policy": str(light_prefetch.native_queue_read_policy),
                "native_queue_read_requested": bool(light_prefetch.native_queue_read_requested),
                "native_queue_read_available": bool(light_prefetch.native_queue_read_available),
                "native_queue_read_enabled": bool(light_prefetch.native_queue_read_enabled),
                "native_queue_read_drain_mode": str(light_prefetch.native_queue_read_drain_mode),
                "native_queue_read_submit_count": int(light_prefetch.native_queue_read_submit_count),
                "native_queue_read_completion_count": int(
                    light_prefetch.native_queue_read_completion_count
                ),
                "native_queue_read_worker_count": int(light_prefetch.native_queue_read_worker_count),
                "native_queue_read_cumulative_s": float(light_prefetch.native_queue_read_cumulative_s),
                "native_queue_read_completion_wait_s": float(
                    light_prefetch.native_queue_read_completion_wait_s
                ),
                "native_queue_read_inline_wait_count": int(
                    light_prefetch.native_queue_read_inline_wait_count
                ),
                "native_queue_read_thread_wait_count": int(
                    light_prefetch.native_queue_read_thread_wait_count
                ),
                **native_path_calibration_report,
                "master_cache_async_write": master_cache_async_write_summary,
                "prefetch_fill_blocked_no_slot_count": int(prefetch_fill_blocked_no_slot_count),
                "host_pinned_bytes": int(
                    max(prefetch_host_pinned_bytes, int(getattr(stack, "host_pinned_bytes", 0)))
                ),
            }
            resident_light_pipeline_profile = build_resident_light_pipeline_profile(
                timing_s=light_pipeline_timing,
                resident_io_pipeline=light_pipeline_io,
                resident_io_overlap=resident_io_overlap,
            )
            fine_timing = {
                "schema_version": 1,
                "seconds": {
                    "light_loop_total": load_calibrate_elapsed,
                    "light_read_decode_total": read_wait_total,
                    "light_read_decode_worker_total": read_worker_total,
                    "light_fits_open_total": fits_open_timing["total"],
                    "light_fits_materialize_decode_total": fits_materialize_decode_timing["total"],
                    "light_fits_native_file_read_total": fits_native_file_read_timing["total"],
                    "light_fits_native_decode_total": fits_native_decode_timing["total"],
                    "light_fits_native_total": fits_native_total_timing["total"],
                    "light_read_overlap_saved": read_overlap_saved,
                    "light_master_build_or_load_in_loop": light_master_build_or_load_in_loop,
                    "light_host_copy_to_pinned_total": host_copy_timing["total"],
                    "light_h2d_total": h2d_timing["total"],
                    "light_calibrate_store_total": calibrate_store_timing["total"],
                    "light_h2d_calibrate_store_total": calibrate_timing["total"],
                    "light_calibration_batch_native_total": float(calibration_batch_native_total_s),
                    "light_native_path_calibration_file_read": float(native_path_calibration_file_read_s),
                    "light_native_path_calibration_total": float(native_path_calibration_total_s),
                    "light_calibration_batch_stream_h2d_calibrate_store": float(calibration_batch_stream_s),
                    "light_calibration_batch_sync": float(calibration_batch_sync_s),
                    "master_cache_async_write_wait": float(
                        master_cache_async_write_summary.get("wait_elapsed_s") or 0.0
                    ),
                    "master_cache_async_write_total": float(
                        master_cache_async_write_summary.get("write_elapsed_s_total") or 0.0
                    ),
                    "master_cache_async_write_written_bytes": int(
                        master_cache_async_write_summary.get("written_bytes") or 0
                    ),
                    "resident_registration_warp_total": registration_total,
                    "resident_registration_warp_during_load_total": registration_during_load_elapsed,
                    "resident_registration_warp_deferred_total": registration_deferred_elapsed,
                    "gc_total": gc_elapsed,
                    "light_loop_accounted_without_master": light_loop_accounted_without_master,
                    "light_loop_accounted": light_loop_accounted,
                    "light_loop_unaccounted": light_loop_unaccounted,
                    "light_loop_unaccounted_without_master": light_loop_unaccounted_without_master,
                },
                "per_frame_seconds": {
                    "total": _timing_summary(per_frame_s),
                    "read_decode": read_timing,
                    "read_decode_worker": read_worker_timing,
                    "fits_open": fits_open_timing,
                    "fits_materialize_decode": fits_materialize_decode_timing,
                    "fits_native_file_read": fits_native_file_read_timing,
                    "fits_native_decode": fits_native_decode_timing,
                    "fits_native_total": fits_native_total_timing,
                    "host_copy_to_pinned": host_copy_timing,
                    "h2d": h2d_timing,
                    "calibrate_store": calibrate_store_timing,
                    "h2d_calibrate_store": calibrate_timing,
                    "registration_warp": registration_timing,
                },
                "registration_component_seconds": {
                    **{key: float(value) for key, value in sorted(registration_component_s.items())},
                    "component_accounted_total": registration_component_total,
                    "python_orchestration_or_uninstrumented": registration_orchestration_elapsed,
                },
            }
            triangle_determinism = (
                triangle_determinism_signatures
                if resident_registration == "similarity_cuda_triangle"
                else {}
            )
            triangle_determinism_summary = (
                _resident_triangle_determinism_summary(triangle_determinism)
                if resident_registration == "similarity_cuda_triangle"
                else {}
            )
            integration_rejection_descriptor = resident_rejection_descriptor(
                rejection_mode,
                low_sigma,
                high_sigma,
                min_samples=rejection_min_samples,
                max_reject_fraction=group_rejection_max_fraction,
                max_reject_fraction_source=group_rejection_max_fraction_source,
                max_reject_fraction_resolution=group_rejection_max_fraction_resolution,
                resident_winsorized_mode=group_resident_winsorized_mode,
                requested_resident_winsorized_mode=resident_winsorized_mode,
                resident_winsorized_resolution_reason=resident_winsorized_contract.get(
                    "resolution_reason"
                ),
                hardened_execution_route=resident_winsorized_contract.get("hardened_execution_route"),
            )
            resident_output_map_policy = {
                "mode": resident_output_maps,
                "available": available_output_maps,
                "written": written_output_maps,
                "skipped": skipped_output_maps,
                "description": (
                    "audit writes all available diagnostic maps; science writes master, "
                    "weight, coverage, and DQ maps; minimal downloads and writes only master."
                ),
                "download_mode": (
                    fused_matrix_download_mode
                    if fused_matrix_integration_used
                    else stack_integration_download_mode
                ),
                "native_map_workspace_mode": stack_integration_native_map_workspace_mode,
                "weight_map_downloaded": bool(weight_map is not None),
                "diagnostic_maps_downloaded": bool(
                    any(
                        item is not None
                        for item in (
                            coverage_map,
                            low_rejection_map,
                            high_rejection_map,
                            geometric_warp_coverage_map,
                        )
                    )
                ),
            }
            surface_map_stats = _resident_surface_contract_map_stats(
                master=master,
                weight_map=weight_map,
                coverage_map=coverage_map,
                low_rejection_map=low_rejection_map,
                high_rejection_map=high_rejection_map,
                dq_map=dq_map,
                output_diagnostics=output_diagnostics,
                dq_coverage_provenance=dq_coverage_provenance,
                dq_summary=dq_summary,
                rejection_map_stats=rejection_map_stats,
            )
            stack_surface_contract = build_resident_integration_stack_surface_contract(
                filter_name=filter_name,
                frame_ids=[str(frame["id"]) for frame in light_frames],
                master=master,
                weight_map=weight_map,
                coverage_map=coverage_map,
                low_rejection_map=low_rejection_map,
                high_rejection_map=high_rejection_map,
                dq_map=dq_map,
                dq_summary=dq_summary,
                dq_provenance_summary=dq_provenance_summary,
                output_map_policy=resident_output_map_policy,
                rejection=rejection_mode,
                low_sigma=low_sigma,
                high_sigma=high_sigma,
                weights=weights_array.tolist(),
                grouping_key=filter_name,
                dispatch=resident_integration_dispatch,
                map_paths={
                    "master": str(master_path),
                    "weight": None if weight_path is None else str(weight_path),
                    "coverage": None if coverage_path is None else str(coverage_path),
                    "low_rejection": None if low_rejection_path is None else str(low_rejection_path),
                    "high_rejection": None if high_rejection_path is None else str(high_rejection_path),
                    "dq": None if dq_path is None else str(dq_path),
                },
                precomputed_map_stats=surface_map_stats,
                trust_precomputed_dq_summary=True,
            )
            group_registration_quality_decisions = [
                registration_quality_decisions_by_frame[str(frame["id"])]
                for frame in light_frames
                if str(frame["id"]) in registration_quality_decisions_by_frame
            ]
            group_registration_quality_summary = summarize_resident_registration_quality(
                group_registration_quality_decisions
            )
            resident_artifacts.append(
                {
                    "filter": filter_name,
                    "frame_ids": [str(frame["id"]) for frame in light_frames],
                    "shape": {"height": height, "width": width},
                    "master_stats": master_stats,
                    "output_diagnostics": output_diagnostics,
                    "output_map_policy": resident_output_map_policy,
                    "master_path": str(master_path),
                    "weight_map_path": None if weight_path is None else str(weight_path),
                    "coverage_map_path": None if coverage_path is None else str(coverage_path),
                    "low_rejection_map_path": None if low_rejection_path is None else str(low_rejection_path),
                    "high_rejection_map_path": None if high_rejection_path is None else str(high_rejection_path),
                    "dq_map_path": None if dq_path is None else str(dq_path),
                    "dq_map_runtime_dtype": None if dq_map is None else str(np.asarray(dq_map).dtype),
                    "dq_summary": dq_summary,
                    "dq_map_stats_backend": dq_map_stats_payload.get("stats_backend"),
                    "dq_map_stats_profile": dq_map_stats_payload.get("stats_profile"),
                    "dq_map_stats_native_method": dq_map_stats_payload.get("native_method"),
                    "dq_map_stats_native_thread_count": dq_map_stats_payload.get("native_thread_count"),
                    "dq_map_count_input_dtypes": dq_map_stats_payload.get("count_map_input_dtypes"),
                    "dq_coverage_provenance": dq_coverage_provenance,
                    "dq_provenance_summary": dq_provenance_summary,
                    "source_dq_summary": source_dq_summary,
                    "source_dq_execution": {
                        "path": str(run / "resident_source_dq_execution.json"),
                        "summary": {
                            "passed": group_source_dq_execution["passed"],
                            "status": group_source_dq_execution["status"],
                            "execution_route": group_source_dq_execution["execution_route"],
                            "materializes_calibrated_dq_cache": group_source_dq_execution[
                                "materializes_calibrated_dq_cache"
                            ],
                            "estimated_batch_mask_bytes": group_source_dq_execution[
                                "streaming_memory"
                            ]["estimated_batch_mask_bytes"],
                        },
                    },
                    "source_dq_calibration_artifact_index": calibration_dq_sidecar_index,
                    "stack_engine_surface_contract": stack_surface_contract,
                    "dq_flag_bits": {
                        "no_data": int(DQFlag.NO_DATA),
                        "warp_edge": int(DQFlag.WARP_EDGE),
                        "low_rejected": int(DQFlag.LOW_REJECTED),
                        "high_rejected": int(DQFlag.HIGH_REJECTED),
                    },
                    "resident_frame_mask_contract": {
                        "path": str(run / "resident_frame_masks.json"),
                        "summary": group_frame_mask_contract["summary"],
                        "semantics": group_frame_mask_contract["semantics"],
                    },
                    "resident_dq_pixel_closure": {
                        "path": str(run / "resident_dq_pixel_closure.json"),
                        "summary": {
                            "passed": group_dq_pixel_closure["passed"],
                            "status": group_dq_pixel_closure["status"],
                            "frame_mask_active_frame_count": group_dq_pixel_closure[
                                "frame_mask_active_frame_count"
                            ],
                            "geometric_warp_coverage_frame_count": group_dq_pixel_closure[
                                "geometric_warp_coverage_frame_count"
                            ],
                        },
                    },
                    "resident_dq_lifecycle": {
                        "path": str(run / "resident_dq_lifecycle.json"),
                        "summary": {
                            "passed": group_dq_lifecycle["passed"],
                            "status": group_dq_lifecycle["status"],
                            "active_frame_count": group_dq_lifecycle["active_frame_count"],
                            "masked_frame_count": group_dq_lifecycle["masked_frame_count"],
                            "source_input_samples": group_dq_lifecycle["source_input_samples"],
                        },
                    },
                    "resident_master_cache": {
                        "path": str(run / "resident_master_cache.json"),
                        "summary": {
                            "passed": group_master_cache["passed"],
                            "status": group_master_cache["status"],
                            "set_count": group_master_cache["set_count"],
                            "cache_hit_count": group_master_cache["cache_hit_count"],
                            "cache_miss_count": group_master_cache["cache_miss_count"],
                            "cache_scope_counts": group_master_cache["cache_scope_counts"],
                            "total_required_bytes": group_master_cache["total_required_bytes"],
                        },
                    },
                    "memory_estimate": memory_estimate,
                    "resident_bytes_allocated_after_master_upload": stack.bytes_allocated,
                    "resident_warp_scratch_bytes": int(getattr(stack, "warp_scratch_bytes", 0)),
                    "resident_warp_copy_mode": str(
                        getattr(stack, "warp_copy_mode", "legacy_synchronous_device_to_device")
                    ),
                    "timing_s": {
                        "master_build_or_load": master_elapsed,
                        "master_cache_async_write_wait": float(
                            master_cache_async_write_summary.get("wait_elapsed_s") or 0.0
                        ),
                        "master_cache_async_write_total": float(
                            master_cache_async_write_summary.get("write_elapsed_s_total") or 0.0
                        ),
                        "master_cache_async_write_written_bytes": int(
                            master_cache_async_write_summary.get("written_bytes") or 0
                        ),
                        "resident_allocate_and_master_upload": allocate_elapsed,
                        "registration_preview_setup": registration_setup_elapsed,
                        "light_read_upload_calibrate": load_calibrate_elapsed,
                        "light_read_decode": read_wait_total,
                        "light_read_wait_wall": read_wait_total,
                        "light_read_decode_worker": read_worker_total,
                        "light_read_worker_cumulative": read_worker_total,
                        "light_fits_open": fits_open_timing["total"],
                        "light_fits_open_worker_cumulative": fits_open_timing["total"],
                        "light_fits_materialize_decode": fits_materialize_decode_timing["total"],
                        "light_fits_materialize_decode_worker_cumulative": fits_materialize_decode_timing["total"],
                        "light_fits_native_file_read": fits_native_file_read_timing["total"],
                        "light_fits_native_decode": fits_native_decode_timing["total"],
                        "light_fits_native_total": fits_native_total_timing["total"],
                        "light_read_overlap_saved": read_overlap_saved,
                        "light_master_build_or_load_in_loop": light_master_build_or_load_in_loop,
                        "light_host_copy_to_pinned": host_copy_timing["total"],
                        "light_h2d": h2d_timing["total"],
                        "light_calibrate_store": calibrate_store_timing["total"],
                        "light_h2d_calibrate_store": calibrate_timing["total"],
                        "light_calibration_batch_native_total": float(calibration_batch_native_total_s),
                        "light_native_path_calibration_file_read": float(native_path_calibration_file_read_s),
                        "light_native_path_calibration_total": float(native_path_calibration_total_s),
                        "light_calibration_batch_stream_h2d_calibrate_store": float(calibration_batch_stream_s),
                        "light_calibration_batch_sync": float(calibration_batch_sync_s),
                        "resident_registration_warp": registration_total,
                        "resident_registration_warp_during_load": registration_during_load_elapsed,
                        "resident_registration_warp_deferred": registration_deferred_elapsed,
                        "resident_registration_component_accounted": registration_component_total,
                        "resident_registration_orchestration": registration_orchestration_elapsed,
                        "gc": gc_elapsed,
                        "resident_inline_source_dq_deferred_apply": float(
                            deferred_inline_cosmetic_cuda_stats["apply_s"]
                        ),
                        "light_loop_accounted_without_master": light_loop_accounted_without_master,
                        "light_loop_accounted": light_loop_accounted,
                        "light_loop_unaccounted": light_loop_unaccounted,
                        "light_loop_unaccounted_without_master": light_loop_unaccounted_without_master,
                        "resident_weighting": weighting_elapsed,
                        "resident_local_normalization": local_norm_elapsed,
                        "resident_integration": integrate_elapsed,
                        "resident_hardened_winsorized_native": float(
                            hardened_winsorized_timing.get("total_s", 0.0)
                        ),
                        "resident_fused_matrix_integration_native": float(
                            fused_matrix_integration_timing.get("total_s", 0.0)
                        ),
                        "output_write": write_elapsed,
                        "per_frame_mean": fine_timing["per_frame_seconds"]["total"]["mean"],
                        "per_frame_min": fine_timing["per_frame_seconds"]["total"]["min"],
                        "per_frame_max": fine_timing["per_frame_seconds"]["total"]["max"],
                        "per_frame_read_decode_mean": read_timing["mean"],
                        "per_frame_read_decode_worker_mean": read_worker_timing["mean"],
                        "per_frame_fits_open_mean": fits_open_timing["mean"],
                        "per_frame_fits_materialize_decode_mean": fits_materialize_decode_timing["mean"],
                        "per_frame_host_copy_to_pinned_mean": host_copy_timing["mean"],
                        "per_frame_h2d_mean": h2d_timing["mean"],
                        "per_frame_calibrate_store_mean": calibrate_store_timing["mean"],
                        "per_frame_h2d_calibrate_store_mean": calibrate_timing["mean"],
                        "per_frame_registration_mean": registration_timing["mean"],
                    },
                    "output_write": {
                        "mode": "threaded" if output_write_workers > 1 else "serial",
                        "workers": output_write_workers,
                        "breakdown_s": write_breakdown,
                        "storage": write_storage,
                    },
                    "output_write_storage": write_storage,
                    "resident_light_pipeline_profile": resident_light_pipeline_profile,
                    "fine_timing": fine_timing,
                    "resident_io_overlap": resident_io_overlap,
                    "resident_io_pipeline": {
                        "prefetch_frames": int(resident_prefetch_frames),
                        "prefetch_workers": int(resident_prefetch_workers) if resident_prefetch_frames > 0 else 0,
                        "prefetch_refill_mode": resident_prefetch_refill_mode,
                        "h2d_mode": resident_h2d_mode,
                        "fits_read_mode": resident_fits_read_mode,
                        "fits_read_mode_requested": resident_fits_read_mode,
                        "fits_read_mode_effective": resident_fits_read_mode_effective,
                        "fits_read_mode_resolution": resident_fits_read_mode_resolution_payload,
                        "resident_fits_auto_selection": resident_fits_auto_selection,
                        "fits_header_spec_cache_enabled": bool(resident_fits_spec_cache),
                        "fits_header_spec_cache_frame_count": int(len(resident_fits_spec_cache)),
                        "fits_header_spec_cache_hit_count": int(per_frame_fits_header_cache_hits),
                        "resident_inline_source_dq": resident_inline_source_dq,
                        "resident_inline_source_dq_policy": str(resident_inline_source_dq_policy),
                        "resident_inline_source_dq_admission": str(resident_inline_source_dq_admission),
                        "resident_inline_source_dq_deferred_target_scope": (
                            "registered_active_positive_weight"
                            if resident_inline_source_dq_admission == "active_registered"
                            else "all_deferred_frames"
                        ),
                        "resident_inline_source_dq_detector": (
                            "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame"
                            if resident_inline_source_dq == "cosmetic_star_cuda"
                            else
                            "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                            if resident_inline_source_dq == "cosmetic_cuda"
                            else "glass.cpu.cosmetic.detect_star_protected_cosmetic_defects"
                            if resident_inline_source_dq == "cosmetic_star"
                            else "glass.cpu.cosmetic.detect_isolated_cosmetic_defects"
                            if resident_inline_source_dq == "cosmetic"
                            else None
                        ),
                        "resident_inline_source_dq_threshold_source": (
                            "cuda_resident_histogram_median_mad_scalar"
                            if resident_inline_source_dq in {"cosmetic_cuda", "cosmetic_star_cuda"}
                            else None
                        ),
                        "resident_inline_source_dq_threshold_stats_domain": (
                            "resident_calibrated_frame"
                            if resident_inline_source_dq in {"cosmetic_cuda", "cosmetic_star_cuda"}
                            else None
                        ),
                        "resident_inline_source_dq_detector_execution": (
                            "cuda_star_catalog_protected_isolated_threshold_apply"
                            if resident_inline_source_dq == "cosmetic_star_cuda"
                            else "cuda_isolated_threshold_apply"
                            if resident_inline_source_dq == "cosmetic_cuda"
                            else None
                        ),
                        "resident_inline_source_dq_application_order": (
                            "post_registration_pre_warp"
                            if defer_inline_cosmetic_cuda_source_dq
                            else "calibration_pre_registration"
                            if resident_inline_source_dq in {"cosmetic_cuda", "cosmetic_star_cuda"}
                            else None
                        ),
                        "resident_inline_source_dq_deferred_until_stage": (
                            "resident_registration_complete"
                            if defer_inline_cosmetic_cuda_source_dq
                            else None
                        ),
                        "resident_inline_source_dq_deferred_frame_count": int(
                            deferred_inline_cosmetic_cuda_stats["deferred_frame_count"]
                        ),
                        "resident_inline_source_dq_deferred_candidate_frame_count": int(
                            deferred_inline_cosmetic_cuda_stats["candidate_frame_count"]
                        ),
                        "resident_inline_source_dq_deferred_target_frame_count": int(
                            deferred_inline_cosmetic_cuda_stats["target_frame_count"]
                        ),
                        "resident_inline_source_dq_deferred_applied_frame_count": int(
                            deferred_inline_cosmetic_cuda_stats["applied_frame_count"]
                        ),
                        "resident_inline_source_dq_deferred_skipped_admission_frame_count": int(
                            deferred_inline_cosmetic_cuda_stats["skipped_admission_frame_count"]
                        ),
                        "resident_inline_source_dq_deferred_pending_frame_count": len(
                            deferred_inline_cosmetic_cuda_by_index
                        ),
                        "resident_inline_source_dq_deferred_apply_s": float(
                            deferred_inline_cosmetic_cuda_stats["apply_s"]
                        ),
                        "resident_inline_source_dq_hot_sigma": float(resident_inline_source_dq_hot_sigma),
                        "resident_inline_source_dq_cold_sigma": float(resident_inline_source_dq_cold_sigma),
                        "resident_inline_source_dq_max_invalid_fraction": float(
                            resident_inline_source_dq_max_invalid_fraction
                        ),
                        "resident_inline_source_dq_high_fraction_guard_enabled": bool(
                            resident_inline_source_dq in {"cosmetic_cuda", "cosmetic_star_cuda"}
                            and resident_inline_source_dq_max_invalid_fraction > 0.0
                        ),
                        "resident_inline_source_dq_high_fraction_skipped_frame_count": int(
                            (source_dq_summary.get("status_counts") or {}).get(
                                "skipped_high_invalid_fraction",
                                0,
                            )
                        ),
                        "resident_inline_source_dq_high_fraction_would_invalid_samples": int(
                            sum(int(row.get("would_invalid_samples") or 0) for row in source_dq_rows)
                        ),
                        "resident_inline_source_dq_materializes_cache": False,
                        "fits_backend_counts": fits_backend_counts,
                        "fits_fast_fallback_reason_counts": fits_fallback_reason_counts,
                        "fits_native_file_read_cumulative_s": fits_native_file_read_timing["total"],
                        "fits_native_decode_cumulative_s": fits_native_decode_timing["total"],
                        "fits_native_total_cumulative_s": fits_native_total_timing["total"],
                        "fits_native_bytes_read": fits_native_bytes_read,
                        "raw_gpu_decode_enabled": raw_u16_gpu_decode_enabled,
                        "raw_gpu_h2d_bytes": int(calibration_raw_h2d_bytes),
                        "raw_gpu_float32_host_bytes_avoided": int(calibration_float32_host_bytes_avoided),
                        "source_dq_fast_skip_enabled": bool(source_dq_fast_skip_enabled),
                        "source_dq_fast_skipped_frame_count": int(source_dq_fast_skipped_frame_count),
                        "source_dq_fast_skip_reason": source_dq_fast_skip_reason,
                        "source_dq_sidecar_frame_count": int(source_dq_sidecar_frame_count),
                        "calibration_event_mode": calibration_event_mode,
                        "calibration_event_modes": unique_calibration_event_modes,
                        "calibration_event_reuse": bool(
                            {
                                "reused_stack_events",
                                "reused_stack_lane_events",
                                "reused_stack_lane_h2d_events",
                                "reused_stack_lane_h2d_callback_events",
                                "native_path_read_reused_stack_lane_events",
                                "native_completion_queue_reused_stack_lane_events",
                            }
                            & set(unique_calibration_event_modes)
                        ),
                        "calibration_release_mode_requested": resident_calibration_release_mode,
                        "calibration_release_mode_effective": calibration_release_mode_effective,
                        "calibration_h2d_release_supported": bool(calibration_h2d_release_supported),
                        "calibration_h2d_release_capable": bool(calibration_h2d_release_capable),
                        "calibration_h2d_release_recommended": bool(calibration_h2d_release_recommended),
                        "calibration_callback_release_supported": bool(calibration_callback_release_supported),
                        "calibration_callback_release_capable": bool(calibration_callback_release_capable),
                        "calibration_callback_release_enabled": bool(calibration_callback_release_enabled),
                        "calibration_callback_release_recommended": bool(calibration_callback_release_recommended),
                        "calibration_callback_release_count": int(calibration_callback_release_count),
                        "calibration_callback_release_s": float(calibration_callback_release_s),
                        "calibration_callback_wave_count": int(calibration_callback_wave_count),
                        "calibration_h2d_release_policy": (
                            "auto enables h2d_event only when wave_effective_frames equals stream_count; "
                            "callback_queue is an explicit native multi-wave experiment"
                        ),
                        "calibration_h2d_release_reason": calibration_h2d_release_reason,
                        "calibration_h2d_release_enabled": bool(calibration_h2d_release_enabled),
                        "calibration_h2d_release_count": int(calibration_h2d_release_count),
                        "calibration_h2d_release_s": float(calibration_h2d_release_s),
                        "calibration_h2d_event_sync_s": float(calibration_h2d_event_sync_s),
                        "calibration_h2d_event_elapsed_s": float(calibration_h2d_event_elapsed_s),
                        "calibration_pending_wait_sync_s": float(calibration_pending_wait_sync_s),
                        "calibration_batch_requested_frames": int(resident_calibration_batch_frames),
                        "calibration_batch_requested_streams": int(resident_calibration_streams),
                        "calibration_wave_requested_frames": int(resident_calibration_wave_frames),
                        "calibration_wave_requested_effective_frames": int(calibration_wave_requested_effective_frames),
                        "calibration_wave_effective_frames": int(calibration_wave_effective_frames),
                        "calibration_wave_effective_source": calibration_wave_effective_source,
                        "calibration_wave_lane_guard_applied": bool(calibration_wave_lane_guard_applied),
                        "calibration_wave_stream_count_limit": int(resident_calibration_streams),
                        "calibration_fetch_batch_requested_frames": int(calibration_fetch_batch_requested_frames),
                        "calibration_fetch_batch_frames": int(calibration_fetch_batch_frames),
                        "calibration_fetch_batch_limit_source": calibration_fetch_batch_limit_source,
                        "calibration_fetch_batch_clamped_to_prefetch_depth": bool(
                            calibration_fetch_batch_clamped_to_prefetch_depth
                        ),
                        "calibration_order_mode": calibration_order_mode,
                        "calibration_ready_order_enabled": bool(calibration_ready_order_enabled),
                        "calibration_ready_order_reason": calibration_ready_order_reason,
                        "calibration_ready_order_master_group_count": int(calibration_master_group_count),
                        "calibration_ready_order_out_of_order_count": int(
                            calibration_ready_order_out_of_order_count
                        ),
                        "calibration_ready_order_select_wait_s": float(calibration_ready_order_select_wait_s),
                        "calibration_ready_order_sample": list(calibration_ready_order_sample),
                        "calibration_remaining_index_model": str(calibration_remaining_index_model),
                        "calibration_remaining_index_set_discard_count": int(
                            calibration_remaining_index_set_discard_count
                        ),
                        "calibration_remaining_index_cursor_advance_count": int(
                            calibration_remaining_index_cursor_advance_count
                        ),
                        "calibration_wave_enabled": bool(calibration_wave_enabled),
                        "calibration_wave_release_mode": (
                            "native_completion_queue_event_gated_slot_reuse"
                            if native_completion_calibration_enabled
                            else "native_path_read_wave_sync"
                            if native_path_calibration_enabled
                            else "callback_after_h2d_event"
                            if calibration_callback_release_enabled
                            else ("after_wave_sync" if calibration_wave_enabled else "after_native_batch_sync")
                        ),
                        "calibration_batch_enabled": bool(calibration_batch_enabled),
                        "calibration_batch_supported": bool(calibration_batch_supported),
                        "calibration_batch_multistream_enabled": bool(calibration_batch_multistream_enabled),
                        "calibration_batch_multistream_supported": bool(calibration_batch_multistream_supported),
                        "calibration_batch_count": int(calibration_batch_count),
                        "calibration_batch_frame_count": int(calibration_batch_frame_count),
                        "calibration_batch_actual_stream_count": int(calibration_batch_actual_stream_count),
                        "calibration_batch_lane_buffer_bytes": int(calibration_batch_lane_buffer_bytes),
                        "calibration_batch_mode": (
                            "fits_u16be_bzero_native_completion_calibration_batch"
                            if native_completion_calibration_enabled
                            else
                            "fits_u16be_bzero_native_path_read_calibration_batch"
                            if native_path_calibration_enabled
                            else
                            "fits_u16be_bzero_gpu_decode_callback_release_batch"
                            if raw_u16_gpu_decode_enabled
                            else
                            "host_async_multistream_callback_release_batch"
                            if calibration_callback_release_enabled
                            else
                            "host_async_multistream_h2d_release_batch"
                            if calibration_h2d_release_enabled
                            else "host_async_multistream_batch"
                            if calibration_batch_multistream_enabled
                            else "host_async_batch"
                            if calibration_batch_enabled
                            else "per_frame"
                        ),
                        "calibration_batch_timing_model": (
                            "native_completion_queue_read_then_h2d_gpu_decode_calibration"
                            if native_completion_calibration_enabled
                            else
                            "native_path_read_wave_then_h2d_gpu_decode_calibration"
                            if native_path_calibration_enabled
                            else
                            "multi_stream_callback_release_waves_one_final_sync"
                            if calibration_callback_release_enabled
                            else
                            "multi_stream_one_frame_per_lane_h2d_release_then_wait"
                            if calibration_h2d_release_enabled
                            else "multi_stream_lanes_one_sync"
                            if calibration_batch_multistream_enabled
                            else "single_stream_sequential_h2d_kernel_one_sync"
                            if calibration_batch_enabled
                            else "per_frame_sync"
                        ),
                        "calibration_batch_native_total_s": float(calibration_batch_native_total_s),
                        "calibration_batch_stream_h2d_calibrate_store_s": float(calibration_batch_stream_s),
                        "calibration_batch_sync_s": float(calibration_batch_sync_s),
                        "prefetch_fill_blocked_no_slot_count": int(prefetch_fill_blocked_no_slot_count),
                        "prefetch_fill_call_count": int(light_prefetch.fill_call_count),
                        "prefetch_fill_submit_count": int(light_prefetch.fill_submit_count),
                        "prefetch_release_count": int(prefetch_release_count),
                        "prefetch_release_batch_count": int(light_prefetch.release_batch_count),
                        "prefetch_release_fill_model": (
                            "queued_release_refill"
                            if resident_prefetch_refill_mode == "queued"
                            else "deferred_release_refill"
                            if resident_prefetch_refill_mode == "deferred"
                            else "batched_release_single_fill"
                        ),
                        "prefetch_release_refill_request_count": int(
                            light_prefetch.release_refill_request_count
                        ),
                        "prefetch_release_refill_queued_submit_count": int(
                            light_prefetch.release_refill_queued_submit_count
                        ),
                        "prefetch_release_refill_queued_execute_count": int(
                            light_prefetch.release_refill_queued_execute_count
                        ),
                        "prefetch_release_refill_queued_coalesced_count": int(
                            light_prefetch.release_refill_queued_coalesced_count
                        ),
                        "prefetch_release_refill_wait_s": float(light_prefetch.release_refill_wait_s),
                        "prefetch_ready_queue_callback_count": int(
                            light_prefetch.ready_queue_callback_count
                        ),
                        "prefetch_ready_queue_wait_count": int(light_prefetch.ready_queue_wait_count),
                        "prefetch_ready_queue_wait_s": float(light_prefetch.ready_queue_wait_s),
                        "prefetch_ready_candidate_probe_mode": str(light_prefetch.ready_candidate_probe_mode),
                        "prefetch_ready_index_candidate_set_reuse_count": int(
                            light_prefetch.ready_index_candidate_set_reuse_count
                        ),
                        "prefetch_ready_batch_select_policy": str(light_prefetch.ready_batch_select_policy),
                        "prefetch_ready_batch_select_enabled": bool(light_prefetch.ready_batch_select_enabled),
                        "prefetch_ready_batch_select_count": int(light_prefetch.ready_batch_select_count),
                        "prefetch_ready_batch_selected_count": int(light_prefetch.ready_batch_selected_count),
                        "native_batch_read_candidate": bool(light_prefetch.native_batch_read_candidate),
                        "native_batch_read_policy": str(light_prefetch.native_batch_read_policy),
                        "native_batch_read_requested": bool(light_prefetch.native_batch_read_requested),
                        "native_batch_read_available": bool(light_prefetch.native_batch_read_available),
                        "native_batch_read_enabled": bool(light_prefetch.native_batch_read_enabled),
                        "native_batch_read_submit_count": int(light_prefetch.native_batch_read_submit_count),
                        "native_batch_read_frame_count": int(light_prefetch.native_batch_read_frame_count),
                        "native_batch_read_max_frame_count": int(
                            light_prefetch.native_batch_read_max_frame_count
                        ),
                        "native_batch_read_worker_count": int(light_prefetch.native_batch_read_worker_count),
                        "native_batch_read_wall_s": float(light_prefetch.native_batch_read_wall_s),
                        "native_batch_read_cumulative_s": float(light_prefetch.native_batch_read_cumulative_s),
                        "native_queue_read_candidate": bool(light_prefetch.native_queue_read_candidate),
                        "native_queue_read_policy": str(light_prefetch.native_queue_read_policy),
                        "native_queue_read_requested": bool(light_prefetch.native_queue_read_requested),
                        "native_queue_read_available": bool(light_prefetch.native_queue_read_available),
                        "native_queue_read_enabled": bool(light_prefetch.native_queue_read_enabled),
                        "native_queue_read_drain_mode": str(light_prefetch.native_queue_read_drain_mode),
                        "native_queue_read_drain_source": str(light_prefetch.native_queue_read_drain_source),
                        "native_queue_read_submit_count": int(light_prefetch.native_queue_read_submit_count),
                        "native_queue_read_completion_count": int(
                            light_prefetch.native_queue_read_completion_count
                        ),
                        "native_queue_read_worker_count": int(light_prefetch.native_queue_read_worker_count),
                        "native_queue_read_cumulative_s": float(
                            light_prefetch.native_queue_read_cumulative_s
                        ),
                        "native_queue_read_completion_wait_s": float(
                            light_prefetch.native_queue_read_completion_wait_s
                        ),
                        "native_queue_read_inline_wait_count": int(
                            light_prefetch.native_queue_read_inline_wait_count
                        ),
                        "native_queue_read_thread_wait_count": int(
                            light_prefetch.native_queue_read_thread_wait_count
                        ),
                        **native_path_calibration_report,
                        "prefetch_max_inflight_slots": int(prefetch_max_inflight_slots),
                        "prefetch_host_allocation_mode": str(light_prefetch.pinned_host_allocation_mode),
                        "prefetch_host_allocation_count": int(light_prefetch.pinned_host_allocation_count),
                        "prefetch_host_allocation_fallback_reason": str(
                            light_prefetch.pinned_host_allocation_fallback_reason
                        ),
                        "master_cache_dir": str(shared_master_cache_dir) if shared_master_cache_dir is not None else None,
                        "master_cache_scope": "shared" if shared_master_cache_dir is not None else "run",
                        "master_cache_policy_requested": master_cache_policy_record["requested"],
                        "master_cache_policy_effective": master_cache_policy_record["effective"],
                        "master_cache_policy_source": master_cache_policy_record["source"],
                        "master_cache_async_write": master_cache_async_write_summary,
                        "host_pinned_bytes": int(
                            max(prefetch_host_pinned_bytes, int(getattr(stack, "host_pinned_bytes", 0)))
                        ),
                        "prefetch_host_pinned_bytes": int(prefetch_host_pinned_bytes),
                        "stack_host_pinned_bytes": int(getattr(stack, "host_pinned_bytes", 0)),
                        "warp_scratch_bytes": int(getattr(stack, "warp_scratch_bytes", 0)),
                        "warp_copy_mode": str(
                            getattr(stack, "warp_copy_mode", "legacy_synchronous_device_to_device")
                        ),
                    },
                    "resident_registration": {
                        "mode": resident_registration,
                        "reference_frame_id": str(reference_frame["id"]),
                        "selected_reference_frame_id": str(reference_frame["id"]),
                        "reference_selection_source": reference_selection_source,
                        "quality_reference_frame_id": quality_reference_frame_id,
                        "quality_reference_status": quality_reference_status,
                        "quality_reference_path": quality_reference_path,
                        "preview_scale": preview_scale,
                        "warp_interpolation": resident_warp_interpolation,
                        "warp_clamping_threshold": resident_warp_clamping_threshold,
                        "warp_batch_dispatch": resident_warp_batch_dispatch,
                        "max_shift": resident_registration_max_shift,
                        "quality_gate": {
                            "requested_action": resident_registration_quality_gate,
                            "effective_action": (
                                ("exclude" if resident_registration == "similarity_cuda_triangle" else "off")
                                if resident_registration_quality_gate == "auto"
                                else resident_registration_quality_gate
                            ),
                            "min_inliers": int(resident_registration_quality_min_inliers),
                            "max_rms_px": None
                            if resident_registration_quality_max_rms_px is None
                            else float(resident_registration_quality_max_rms_px),
                            "summary": group_registration_quality_summary,
                            "decisions_path": str(run / "resident_registration_quality.json"),
                        },
                        "ncc_sample_stride": resident_ncc_sample_stride,
                        "ncc_fallback_score_threshold": resident_ncc_fallback_score_threshold,
                        "subpixel_radius_steps": resident_subpixel_radius_steps,
                        "subpixel_step": resident_subpixel_step,
                        "star_threshold": resident_star_threshold,
                        "star_threshold_mode": "fixed"
                        if resident_star_threshold > 0.0
                        else "auto_mean_std",
                        "star_threshold_auto_sigmas": list(_AUTO_STAR_THRESHOLD_SIGMAS),
                        "star_max_candidates": resident_star_max_candidates,
                        "star_tolerance_px": resident_star_tolerance_px,
                        "star_grid_cols": triangle_star_grid_cols
                        if resident_registration == "similarity_cuda_triangle"
                        else resident_star_grid_cols,
                        "star_grid_rows": triangle_star_grid_rows
                        if resident_registration == "similarity_cuda_triangle"
                        else resident_star_grid_rows,
                        "star_catalog_deterministic": (
                            bool(triangle_star_catalog_deterministic)
                            if resident_registration == "similarity_cuda_triangle"
                            else bool(resident_star_catalog_deterministic)
                        ),
                        "star_prior": resident_star_prior,
                        "star_prior_radius_px": resident_star_prior_radius_px,
                        "pierside_same_similarity_top_k": _policy_int(
                            registration_policy,
                            "cuda_catalog_pierside_same_similarity_top_k",
                            _policy_int(registration_policy, "cuda_catalog_similarity_top_k", 8),
                        ),
                        "pierside_flip_similarity_top_k": _policy_int(
                            registration_policy,
                            "cuda_catalog_pierside_flip_similarity_top_k",
                            max(_policy_int(registration_policy, "cuda_catalog_similarity_top_k", 8), 64),
                        ),
                        "pierside_same_max_abs_rotation_rad": _policy_optional_float(
                            registration_policy,
                            "cuda_catalog_pierside_same_max_abs_rotation_rad",
                            _policy_optional_float(
                                registration_policy,
                                "cuda_catalog_max_abs_rotation_rad",
                                0.01,
                            ),
                        ),
                        "pierside_flip_max_abs_rotation_rad": _policy_optional_float(
                            registration_policy,
                            "cuda_catalog_pierside_flip_max_abs_rotation_rad",
                            3.2,
                        ),
                        "star_core_preselect_top_k": _policy_int(
                            registration_policy,
                            "cuda_catalog_star_core_preselect_top_k",
                            resident_star_core_preselect_top_k,
                        ),
                        "star_core_guard": _policy_bool(
                            registration_policy,
                            "cuda_catalog_star_core_guard",
                            _policy_int(
                                registration_policy,
                                "cuda_catalog_star_core_preselect_top_k",
                                resident_star_core_preselect_top_k,
                            )
                            > 0,
                        ),
                        "min_pixel_ncc": _policy_optional_float(
                            registration_policy,
                            "cuda_catalog_min_pixel_ncc",
                            None,
                        ),
                        "min_selected_seed_inliers": _policy_int(
                            registration_policy,
                            "cuda_catalog_min_selected_seed_inliers",
                            0,
                        ),
                        "triangle_descriptor_radius": _policy_float(
                            registration_policy,
                            "cuda_triangle_descriptor_radius",
                            0.1,
                        ),
                        "triangle_neighbors": _policy_int(
                            registration_policy,
                            "cuda_triangle_neighbors",
                            5,
                        ),
                        "triangle_max_descriptors": _policy_int(
                            registration_policy,
                            "cuda_triangle_max_descriptors",
                            1200,
                        ),
                        "triangle_grid_top_per_cell": int(grid_top_candidates_per_cell)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_nms_scan_candidates": int(nms_scan_candidates)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_nms_min_separation_px": float(nms_min_separation_px)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_pixel_refine": _policy_bool(
                            registration_policy,
                            "cuda_triangle_pixel_refine",
                            _DEFAULT_CUDA_TRIANGLE_PIXEL_REFINE,
                        ),
                        "triangle_translation_refine": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_translation_refine_enabled
                        ),
                        "triangle_translation_refine_plan_transform_model": plan_transform_model
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_policy_source": triangle_translation_refine_policy_source
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_tolerance_px": float(
                            triangle_translation_refine_tolerance_px
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_min_inliers": int(
                            triangle_translation_refine_min_inliers
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_max_correction_px": float(
                            triangle_translation_refine_max_correction_px
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_iterations": int(
                            triangle_translation_refine_iterations
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_iteration_max_step_px": float(
                            triangle_translation_refine_iteration_max_step_px
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_translation_refine_applied_count": int(
                            triangle_translation_refine_applied_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_translation_refine_skipped_count": int(
                            triangle_translation_refine_skipped_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_translation_refine_rejected_count": int(
                            triangle_translation_refine_rejected_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_translation_refine_max_correction_px_observed": float(
                            triangle_translation_refine_max_correction_px_observed
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_translation_refine_max_rms_px": float(
                            triangle_translation_refine_max_rms_px
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_translation_refine_max_iterations_observed": int(
                            triangle_translation_refine_max_iterations_observed
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_centroid_refine": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_centroid_refine_enabled
                        ),
                        "triangle_centroid_refine_mode": (
                            (
                                "resident_gpu_global_mean_centroid"
                                if triangle_centroid_background_mode == "global_mean"
                                else "resident_gpu_window_centroid"
                            )
                            if resident_registration == "similarity_cuda_triangle"
                            and triangle_centroid_refine_enabled
                            and (
                                has_top_nms_catalog_centroid
                                or (
                                    use_grid_catalog
                                    and (
                                        has_grid_nms_catalog_centroid
                                        or has_grid_nms_catalog_deterministic_centroid
                                    )
                                )
                            )
                            else "resident_tile_download_cpu_centroid"
                            if resident_registration == "similarity_cuda_triangle"
                            and triangle_centroid_refine_enabled
                            else "off"
                        ),
                        "triangle_centroid_refine_background": triangle_centroid_background_mode
                        if resident_registration == "similarity_cuda_triangle"
                        and triangle_centroid_refine_enabled
                        else None,
                        "triangle_centroid_refine_radius": int(triangle_centroid_refine_radius)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_centroid_refine_catalog_count": int(triangle_centroid_refine_catalog_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_centroid_refine_star_count": int(triangle_centroid_refine_star_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_centroid_refine_failed_star_count": int(
                            triangle_centroid_refine_failed_star_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_centroid_refine_max_shift_px": float(triangle_centroid_refine_max_shift_px)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_catalog_batch": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_catalog_batch_enabled
                        ),
                        "triangle_catalog_grid_auto": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_catalog_grid_auto
                        ),
                        "triangle_catalog_selector": catalog_selector
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_batch_mode": triangle_catalog_batch_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_timing_model": triangle_catalog_timing_model
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_batch_size": int(triangle_catalog_batch_size)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_stream_limit": int(triangle_catalog_stream_limit)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_stream_count": int(triangle_catalog_stream_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_batch_sync_count": int(triangle_catalog_batch_sync_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_sync_phase_count": int(triangle_catalog_sync_phase_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_download_mode": triangle_catalog_download_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_workspace_layout": triangle_catalog_workspace_layout
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_grid_workspace_allocation_count": int(
                            triangle_catalog_grid_workspace_allocation_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_output_workspace_allocation_count": int(
                            triangle_catalog_output_workspace_allocation_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_output_download_copy_count": int(
                            triangle_catalog_output_download_copy_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_centroid_before_download_copy_count": int(
                            triangle_catalog_centroid_before_download_copy_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_output_download_bytes": int(
                            triangle_catalog_output_download_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_centroid_mean_sync_mode": triangle_catalog_centroid_mean_sync_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_centroid_mean_blocks": int(
                            triangle_catalog_centroid_mean_blocks
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_catalog_sort_mode": triangle_catalog_sort_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_topk_mode": triangle_catalog_topk_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_catalog_native_enqueue_s": float(triangle_catalog_native_enqueue_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_catalog_native_sync_s": float(triangle_catalog_native_sync_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_catalog_native_count_download_s": float(
                            triangle_catalog_native_count_download_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_catalog_native_output_download_s": float(
                            triangle_catalog_native_output_download_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_catalog_native_centroid_refine_s": float(
                            triangle_catalog_native_centroid_refine_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_catalog_native_total_s": float(triangle_catalog_native_total_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_generation_batch": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_descriptor_generation_batch_enabled
                        ),
                        "triangle_descriptor_generation_batch_mode": triangle_descriptor_generation_batch_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_descriptor_generation_batch_call_count": int(
                            triangle_descriptor_generation_batch_call_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_descriptor_generation_batch_size": int(
                            triangle_descriptor_generation_batch_size
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_descriptor_generation_batch_timing_model": (
                            triangle_descriptor_generation_batch_timing_model
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_descriptor_generation_batch_upload_s": float(
                            triangle_descriptor_generation_batch_upload_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_generation_batch_kernel_sync_s": float(
                            triangle_descriptor_generation_batch_kernel_sync_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_generation_batch_output_download_s": float(
                            triangle_descriptor_generation_batch_output_download_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_batch": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_descriptor_fit_batch_enabled
                        ),
                        "triangle_descriptor_fit_batch_mode": triangle_descriptor_fit_batch_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_descriptor_fit_best_reduction_mode": triangle_descriptor_fit_best_reduction_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_descriptor_fit_batch_timing_model": triangle_descriptor_fit_batch_timing_model
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_descriptor_fit_reference_device_reuse": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_descriptor_fit_reference_device_reuse
                        ),
                        "triangle_descriptor_fit_reference_device_bytes": int(
                            triangle_descriptor_fit_reference_device_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_descriptor_fit_moving_device_reuse": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_descriptor_fit_moving_device_reuse
                        ),
                        "triangle_descriptor_fit_moving_device_bytes": int(
                            triangle_descriptor_fit_moving_device_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_descriptor_fit_output_device_reuse": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_descriptor_fit_output_device_reuse
                        ),
                        "triangle_descriptor_fit_output_device_bytes": int(
                            triangle_descriptor_fit_output_device_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_descriptor_fit_native_host_prepare_s": float(
                            triangle_descriptor_fit_native_host_prepare_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_reference_alloc_s": float(
                            triangle_descriptor_fit_native_reference_alloc_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_reference_upload_s": float(
                            triangle_descriptor_fit_native_reference_upload_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_workspace_alloc_s": float(
                            triangle_descriptor_fit_native_workspace_alloc_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_moving_upload_s": float(
                            triangle_descriptor_fit_native_moving_upload_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_kernel_sync_s": float(
                            triangle_descriptor_fit_native_kernel_sync_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_output_download_s": float(
                            triangle_descriptor_fit_native_output_download_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_frame_total_s": float(
                            triangle_descriptor_fit_native_frame_total_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_descriptor_fit_native_total_s": float(triangle_descriptor_fit_native_total_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_warp_batch_enabled
                        ),
                        "triangle_warp_batch_mode": triangle_warp_batch_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_dispatch": resident_warp_batch_dispatch
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_track_coverage": bool(resident_track_warp_coverage)
                        if resident_registration == "similarity_cuda_triangle"
                        else False,
                        "triangle_warp_batch_coverage_accumulator_policy": (
                            "track_for_output_maps"
                            if resident_track_warp_coverage
                            else "skipped_by_minimal_output_policy"
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_requested_chunk_capacity_frames": (
                            int(resident_warp_chunk_capacity_frames)
                            if resident_warp_chunk_capacity_frames is not None
                            else None
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_warp_batch_effective_chunk_capacity_frames": (
                            int(resident_warp_chunk_capacity_effective)
                            if resident_warp_chunk_capacity_effective is not None
                            else None
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_warp_batch_capacity_source": triangle_warp_batch_capacity_source
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_native_capacity_source": (
                            triangle_warp_batch_native_capacity_source
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_native_max_chunk_capacity_frames": int(
                            triangle_warp_batch_native_max_chunk_capacity_frames
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_timing_model": triangle_warp_batch_timing_model
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_native_inverse_upload_mode": (
                            triangle_warp_batch_native_inverse_upload_mode
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_native_chunk_metadata_upload_mode": (
                            triangle_warp_batch_native_chunk_metadata_upload_mode
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_frame_count": int(triangle_warp_batch_frame_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_fallback_frame_count": int(
                            triangle_warp_batch_fallback_frame_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_inverse_prepare_s": float(
                            triangle_warp_batch_native_inverse_prepare_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_inverse_batch_alloc_s": float(
                            triangle_warp_batch_native_inverse_batch_alloc_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_inverse_batch_bytes": int(
                            triangle_warp_batch_native_inverse_batch_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_index_upload_s": float(
                            triangle_warp_batch_native_index_upload_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_index_upload_count": int(
                            triangle_warp_batch_native_index_upload_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_inverse_upload_s": float(
                            triangle_warp_batch_native_inverse_upload_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_inverse_upload_count": int(
                            triangle_warp_batch_native_inverse_upload_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_kernel_enqueue_s": float(
                            triangle_warp_batch_native_kernel_enqueue_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_coverage_reduce_enqueue_s": float(
                            triangle_warp_batch_native_coverage_reduce_enqueue_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_scatter_enqueue_s": float(
                            triangle_warp_batch_native_scatter_enqueue_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_postprocess_enqueue_s": float(
                            triangle_warp_batch_native_postprocess_enqueue_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_postprocess_mode": (
                            triangle_warp_batch_native_postprocess_mode
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_native_lanczos3_clamping_enabled": (
                            triangle_warp_batch_native_lanczos3_clamping_enabled
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_warp_batch_native_lanczos3_clamp_path": (
                            triangle_warp_batch_native_lanczos3_clamp_path
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_warp_batch_native_device_copy_enqueue_s": float(
                            triangle_warp_batch_native_device_copy_enqueue_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_sync_s": float(triangle_warp_batch_native_sync_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_total_s": float(triangle_warp_batch_native_total_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_warp_batch_native_chunk_frames": int(
                            triangle_warp_batch_native_chunk_frames
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_chunk_count": int(
                            triangle_warp_batch_native_chunk_count
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_workspace_bytes": int(
                            triangle_warp_batch_native_workspace_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_output_bytes": int(
                            triangle_warp_batch_native_output_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_coverage_bytes": int(
                            triangle_warp_batch_native_coverage_bytes
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_warp_kernel_launches": int(
                            triangle_warp_batch_native_warp_kernel_launches
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_coverage_reduce_kernel_launches": int(
                            triangle_warp_batch_native_coverage_reduce_kernel_launches
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_scatter_kernel_launches": int(
                            triangle_warp_batch_native_scatter_kernel_launches
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_warp_batch_native_postprocess_kernel_launches": int(
                            triangle_warp_batch_native_postprocess_kernel_launches
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_fused_matrix_deferred": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_fused_matrix_deferred_enabled
                        ),
                        "triangle_fused_matrix_deferred_count": int(triangle_fused_matrix_deferred_count)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_coarse_stride": int(refine_kwargs["coarse_sample_stride"])
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_pixel_refine_final_stride": int(refine_kwargs["final_sample_stride"])
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_pixel_refine_requested_coarse_stride": int(
                            triangle_pixel_refine_requested_coarse_stride
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_pixel_refine_requested_final_stride": int(
                            triangle_pixel_refine_requested_final_stride
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_pixel_refine_fast_coarse": bool(triangle_pixel_refine_fast_coarse_enabled)
                        if resident_registration == "similarity_cuda_triangle"
                        else False,
                        "triangle_pixel_refine_fast_coarse_mode": triangle_pixel_refine_fast_coarse_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_pixel_refine_coarse_stride_adjusted": bool(
                            triangle_pixel_refine_coarse_stride_adjusted
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else False,
                        "triangle_pixel_refine_batch": bool(
                            resident_registration == "similarity_cuda_triangle"
                            and triangle_pixel_refine_batch_enabled
                        ),
                        "triangle_pixel_refine_batch_mode": triangle_pixel_refine_batch_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_pixel_refine_workspace_mode": triangle_pixel_refine_workspace_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_pixel_refine_batch_metric_mode": triangle_pixel_refine_batch_metric_mode
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_pixel_refine_batch_metric_kernel_launches": int(
                            triangle_pixel_refine_batch_metric_kernel_launches
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_coarse_total_candidates": int(
                            triangle_pixel_refine_coarse_total_candidates
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_fine_total_candidates": int(
                            triangle_pixel_refine_fine_total_candidates
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_metric_workload_model": triangle_pixel_refine_metric_workload_model
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_pixel_refine_coarse_sampled_pixels_per_candidate": int(
                            triangle_pixel_refine_coarse_sampled_pixels_per_candidate
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_fine_sampled_pixels_per_candidate": int(
                            triangle_pixel_refine_fine_sampled_pixels_per_candidate
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_coarse_metric_sample_evaluations": int(
                            triangle_pixel_refine_coarse_metric_sample_evaluations
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_fine_metric_sample_evaluations": int(
                            triangle_pixel_refine_fine_metric_sample_evaluations
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_coarse_metric_megasamples_per_s": float(
                            triangle_pixel_refine_coarse_metric_megasamples_per_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_pixel_refine_fine_metric_megasamples_per_s": float(
                            triangle_pixel_refine_fine_metric_megasamples_per_s
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_pixel_refine_workspace_bytes": int(triangle_pixel_refine_workspace_bytes)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_workspace_candidate_capacity": int(
                            triangle_pixel_refine_workspace_candidate_capacity
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_pixel_refine_native_coarse_s": float(triangle_pixel_refine_native_coarse_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_pixel_refine_native_fine_s": float(triangle_pixel_refine_native_fine_s)
                        if resident_registration == "similarity_cuda_triangle"
                        else 0.0,
                        "triangle_determinism_signature_mode": triangle_determinism_summary.get(
                            "signature_mode",
                            "off",
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else "off",
                        "triangle_determinism_moving_frame_count": triangle_determinism_summary.get(
                            "moving_frame_count",
                            0,
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_determinism_threshold_count": triangle_determinism_summary.get(
                            "threshold_count",
                            0,
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else 0,
                        "triangle_determinism_reference_combined_sha256": triangle_determinism_summary.get(
                            "reference_combined_sha256"
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_determinism_moving_catalog_combined_sha256": triangle_determinism_summary.get(
                            "moving_catalog_combined_sha256"
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_determinism_selected_fit_combined_sha256": triangle_determinism_summary.get(
                            "selected_fit_combined_sha256"
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_determinism_trial_combined_sha256": triangle_determinism_summary.get(
                            "trial_combined_sha256"
                        )
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_determinism": triangle_determinism
                        if resident_registration == "similarity_cuda_triangle"
                        else {},
                        "triangle_min_pixel_ncc": _policy_optional_float(
                            registration_policy,
                            "cuda_triangle_min_pixel_ncc",
                            _policy_optional_float(registration_policy, "cuda_catalog_min_pixel_ncc", None),
                        ),
                        "triangle_min_agreement_score": min_agreement_score
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_agreement_rms_scale": float(triangle_agreement_rms_scale)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_agreement_action": triangle_agreement_action
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_agreement_min_weight": float(triangle_agreement_min_weight)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "triangle_agreement_downweighted_frame_count": int(agreement_downweighted_frames)
                        if resident_registration == "similarity_cuda_triangle"
                        else None,
                        "registration_motion_weighting_mode": resident_registration_motion_weighting,
                        "registration_motion_downweighted_frame_count": int(motion_downweighted_frames),
                        "frame_weight_proposal_path": frame_weight_proposal.get("path"),
                        "frame_weight_proposal_frame_count": int(frame_weight_proposal.get("frame_count") or 0),
                        "frame_weight_proposal_downweighted_frame_count": int(proposal_downweighted_frames),
                        "external_registration_results_path": None
                        if external_registration_path is None
                        else str(external_registration_path),
                        "failed_frame_count": int(np.count_nonzero(weights_array == 0.0)),
                        "excluded_frame_tokens": sorted(excluded_tokens),
                        "warp_coverage": {
                            "available": bool(geometric_warp_coverage_map is not None),
                            "supported": bool(resident_warp_coverage_supported),
                            "native_source": (
                                "ResidentCalibratedStack fused matrix integration geometric coverage"
                                if fused_matrix_integration_used
                                else "ResidentCalibratedStack warp coverage accumulator"
                            ),
                            "frame_count": geometric_warp_coverage_frame_count,
                            "warped_frame_count": len(warped_frame_indices),
                            "fused_deferred_frame_count": len(fused_matrix_deferred_frame_indices),
                            "full_frame_count": max(
                                0,
                                geometric_warp_coverage_frame_count
                                - len(warped_frame_indices)
                                - len(fused_matrix_deferred_frame_indices),
                            ),
                            "active_frame_count": active_frame_count,
                            "frame_count_matches_active": geometric_warp_coverage_frame_count == active_frame_count,
                            "statistics": None
                            if geometric_warp_coverage_map is None
                            else _resident_coverage_array_stats(geometric_warp_coverage_map),
                        },
                    },
                    "resident_local_normalization": {
                        "enabled": local_norm_enabled,
                        "mode": local_norm_mode,
                        "tile_size": (
                            resident_local_normalization_tile_size
                            if resident_local_normalization_mode == "grid_mean_std" and local_norm_enabled
                            else None
                        ),
                        "reference_frame_id": str(reference_frame["id"]),
                        "warning_count": len(local_norm_warnings),
                        "grid_stats": local_norm_groups[-1].get("grid_stats", {}),
                        "grid_apply": local_norm_groups[-1].get("grid_apply", {}),
                        "application": local_norm_groups[-1].get("application", {}),
                    },
                    "resident_integration_weighting": {
                        "mode": weighting_mode,
                        "frame_results": weighting_frame_results,
                        "registration_motion_weighting": motion_weighting_summary,
                        "frame_weight_proposal": frame_weight_proposal_summary,
                        "tile_local_policy_replay": group_tile_local_policy_replay,
                        "timing_s": weighting_elapsed,
                        "warnings": weighting_warnings,
                    },
                    "resident_integration_dispatch": {
                        "mode": resident_integration_dispatch,
                        "requested_mode": resident_integration_dispatch_requested,
                        "effective_mode": resident_integration_dispatch,
                        "selection_reason": resident_integration_dispatch_reason,
                        "rejection_max_fraction": group_rejection_max_fraction,
                        "rejection_max_fraction_source": group_rejection_max_fraction_source,
                        "rejection_max_fraction_resolution": group_rejection_max_fraction_resolution,
                        "auto_policy": {
                            "enabled": resident_integration_dispatch_requested == "auto",
                            "selected_mode": resident_integration_dispatch,
                            "reason": resident_integration_dispatch_reason,
                            "verified_fast_path": (
                                resident_integration_dispatch == "fused_matrix"
                                and resident_warp_interpolation == "bilinear"
                            ),
                            "conservative_stack_for_non_bilinear": (
                                resident_integration_dispatch_requested == "auto"
                                and resident_warp_interpolation != "bilinear"
                            ),
                        },
                        "used": bool(fused_matrix_integration_used),
                        "eligible_registration_modes": [
                            "off",
                            "external_matrix",
                            "similarity_cuda_triangle",
                        ],
                        "matrix_count": len(integration_matrices),
                        "deferred_matrix_frame_count": len(fused_matrix_deferred_frame_indices),
                        "interpolation": resident_warp_interpolation,
                        "clamping_threshold": resident_warp_clamping_threshold,
                        "requested_resident_winsorized_mode": resident_winsorized_mode,
                        "resident_winsorized_mode": group_resident_winsorized_mode,
                        "resident_winsorized_contract": resident_winsorized_contract,
                        "hardened_winsorized_timing_s": hardened_winsorized_timing,
                        "download_mode": (
                            fused_matrix_download_mode
                            if fused_matrix_integration_used
                            else stack_integration_download_mode
                        ),
                        "native_map_workspace_mode": stack_integration_native_map_workspace_mode,
                        "diagnostic_maps_downloaded": bool(
                            fused_matrix_integration_timing.get(
                                "diagnostic_maps_downloaded",
                                (
                                    fused_matrix_download_mode == "full"
                                    if fused_matrix_integration_used
                                    else any(
                                        item is not None
                                        for item in (
                                            coverage_map,
                                            low_rejection_map,
                                            high_rejection_map,
                                        )
                                    )
                                ),
                            )
                        ),
                        "weight_map_downloaded": bool(
                            fused_matrix_integration_timing.get(
                                "weight_map_downloaded",
                                weight_map is not None,
                            )
                        ),
                        "native_timing_s": fused_matrix_integration_timing,
                        "notes": (
                            "fused_matrix samples unwarped resident frames through the registration matrix during "
                            "integration and avoids writing registered full-frame intermediates"
                            if fused_matrix_integration_used
                            else "stack dispatch integrates frames already present in the resident stack"
                        ),
                    },
                    "integration_rejection": integration_rejection_descriptor,
                    "notes": [
                        "Raw light frames are uploaded one at a time into a reusable device buffer.",
                        "Calibrated frames remain resident in VRAM until integration completes.",
                        (
                            "Resident registration can consume external similarity/affine matrices and apply them "
                            f"with CUDA matrix {resident_warp_interpolation} warp."
                            if resident_registration == "external_matrix"
                            else "Resident registration estimated CUDA similarity matrices and applied resident matrix warp."
                            if resident_registration == "similarity_cuda_catalog"
                            else (
                                "Resident registration estimated CUDA triangle-descriptor similarity matrices and "
                                "deferred accepted matrices to fused integration."
                                if fused_matrix_integration_used
                                else "Resident registration estimated CUDA triangle-descriptor similarity matrices and "
                                "applied resident matrix warp."
                            )
                            if resident_registration == "similarity_cuda_triangle"
                            else "Resident registration is optional and currently limited to translation."
                        ),
                        (
                            f"Resident local normalization uses {local_norm_mode}."
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
                    "weight_map_path": None if weight_path is None else str(weight_path),
                    "coverage_map_path": None if coverage_path is None else str(coverage_path),
                    "low_rejection_map_path": None if low_rejection_path is None else str(low_rejection_path),
                    "high_rejection_map_path": None if high_rejection_path is None else str(high_rejection_path),
                    "dq_map_path": None if dq_path is None else str(dq_path),
                    "dq_map_runtime_dtype": None if dq_map is None else str(np.asarray(dq_map).dtype),
                    "dq_summary": dq_summary,
                    "dq_map_stats_backend": dq_map_stats_payload.get("stats_backend"),
                    "dq_map_stats_profile": dq_map_stats_payload.get("stats_profile"),
                    "dq_map_stats_native_method": dq_map_stats_payload.get("native_method"),
                    "dq_map_stats_native_thread_count": dq_map_stats_payload.get("native_thread_count"),
                    "dq_map_count_input_dtypes": dq_map_stats_payload.get("count_map_input_dtypes"),
                    "dq_coverage_provenance": dq_coverage_provenance,
                    "dq_provenance_summary": dq_provenance_summary,
                    "source_dq_summary": source_dq_summary,
                    "source_dq_execution": {
                        "path": str(run / "resident_source_dq_execution.json"),
                        "summary": {
                            "passed": group_source_dq_execution["passed"],
                            "status": group_source_dq_execution["status"],
                            "execution_route": group_source_dq_execution["execution_route"],
                            "materializes_calibrated_dq_cache": group_source_dq_execution[
                                "materializes_calibrated_dq_cache"
                            ],
                            "estimated_batch_mask_bytes": group_source_dq_execution[
                                "streaming_memory"
                            ]["estimated_batch_mask_bytes"],
                        },
                    },
                    "source_dq_calibration_artifact_index": calibration_dq_sidecar_index,
                    "stack_engine_surface_contract": stack_surface_contract,
                    "geometric_warp_coverage": {
                        "available": bool(geometric_warp_coverage_map is not None),
                        "frame_count": geometric_warp_coverage_frame_count,
                        "frame_count_matches_active": geometric_warp_coverage_frame_count == active_frame_count,
                    },
                    "output_map_policy": resident_output_map_policy,
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "rejection": rejection_mode,
                    "integration_rejection": integration_rejection_descriptor,
                    "weighting": weighting_mode,
                    "resident_registration": resident_registration,
                    "resident_integration_dispatch": resident_integration_dispatch,
                    "resident_integration_dispatch_requested": resident_integration_dispatch_requested,
                    "resident_integration_dispatch_reason": resident_integration_dispatch_reason,
                    "resident_winsorized_contract": resident_winsorized_contract,
                    "rejection_max_fraction_source": group_rejection_max_fraction_source,
                    "rejection_max_fraction_resolution": group_rejection_max_fraction_resolution,
                    "resident_frame_mask_contract": {
                        "path": str(run / "resident_frame_masks.json"),
                        "summary": group_frame_mask_contract["summary"],
                    },
                    "resident_dq_pixel_closure": {
                        "path": str(run / "resident_dq_pixel_closure.json"),
                        "summary": {
                            "passed": group_dq_pixel_closure["passed"],
                            "status": group_dq_pixel_closure["status"],
                            "frame_mask_active_frame_count": group_dq_pixel_closure[
                                "frame_mask_active_frame_count"
                            ],
                            "geometric_warp_coverage_frame_count": group_dq_pixel_closure[
                                "geometric_warp_coverage_frame_count"
                            ],
                        },
                    },
                    "resident_dq_lifecycle": {
                        "path": str(run / "resident_dq_lifecycle.json"),
                        "summary": {
                            "passed": group_dq_lifecycle["passed"],
                            "status": group_dq_lifecycle["status"],
                            "active_frame_count": group_dq_lifecycle["active_frame_count"],
                            "masked_frame_count": group_dq_lifecycle["masked_frame_count"],
                            "source_input_samples": group_dq_lifecycle["source_input_samples"],
                        },
                    },
                    "resident_master_cache": {
                        "path": str(run / "resident_master_cache.json"),
                        "summary": {
                            "passed": group_master_cache["passed"],
                            "status": group_master_cache["status"],
                            "set_count": group_master_cache["set_count"],
                            "cache_hit_count": group_master_cache["cache_hit_count"],
                            "cache_miss_count": group_master_cache["cache_miss_count"],
                            "cache_scope_counts": group_master_cache["cache_scope_counts"],
                            "total_required_bytes": group_master_cache["total_required_bytes"],
                        },
                    },
                    "hardened_winsorized_timing_s": hardened_winsorized_timing,
                    "resident_local_normalization": local_norm_mode,
                    "estimated_peak_gib": memory_estimate["estimated_peak_gib"],
                    "resident_integration_s": integrate_elapsed,
                    "output_write_storage": write_storage,
                    "output_diagnostics": output_diagnostics,
                    "resident_light_pipeline_profile": resident_light_pipeline_profile,
                }
            )
            del (
                stack,
                master,
                weight_map,
                coverage_map,
                low_rejection_map,
                high_rejection_map,
                dq_map,
                geometric_warp_coverage_map,
            )
            gc.collect()

        if not outputs:
            raise ValueError("resident mode found no executable light plans")

        resident_path = run / "resident_artifacts.json"
        registration_quality_path = run / "resident_registration_quality.json"
        resident_frame_masks_path = run / "resident_frame_masks.json"
        resident_dq_pixel_closure_path = run / "resident_dq_pixel_closure.json"
        resident_dq_lifecycle_path = run / "resident_dq_lifecycle.json"
        resident_source_dq_execution_path = run / "resident_source_dq_execution.json"
        resident_master_cache_path = run / "resident_master_cache.json"
        resident_frame_mask_payload = {
            "schema_version": 1,
            "artifact": "resident_frame_mask_contract",
            "source_stage": "resident_calibrated_stack",
            "backend": "cuda_resident_stack",
            "summary": summarize_resident_frame_mask_contracts(resident_frame_mask_contract_groups),
            "groups": resident_frame_mask_contract_groups,
            "pixel_mask_semantics": {
                "invalid_warp_footprint": "output DQFlag.WARP_EDGE and geometric warp coverage maps",
                "low_rejection": "output DQFlag.LOW_REJECTED and low rejection count maps",
                "high_rejection": "output DQFlag.HIGH_REJECTED and high rejection count maps",
                "no_data": "output DQFlag.NO_DATA where no valid weighted sample contributes",
            },
        }
        validate_resident_frame_mask_contract({"summary": resident_frame_mask_payload["summary"]})
        write_json(resident_frame_masks_path, resident_frame_mask_payload, compact=True)
        resident_dq_pixel_closure_payload = {
            "schema_version": 1,
            "artifact": "resident_dq_pixel_closure",
            "source_stage": "resident_calibrated_stack",
            "backend": "cuda_resident_stack",
            "summary": summarize_resident_dq_pixel_closure_groups(resident_dq_pixel_closure_groups),
            "groups": resident_dq_pixel_closure_groups,
        }
        if not resident_dq_pixel_closure_payload["summary"]["passed"]:
            failed = ", ".join(resident_dq_pixel_closure_payload["summary"].get("failed_groups") or [])
            raise RuntimeError(f"resident DQ pixel closure failed for group(s): {failed}")
        write_json(resident_dq_pixel_closure_path, resident_dq_pixel_closure_payload)
        resident_dq_lifecycle_payload = {
            "schema_version": 1,
            "artifact": "resident_dq_lifecycle",
            "source_stage": "resident_calibrated_stack",
            "backend": "cuda_resident_stack",
            "summary": summarize_resident_dq_lifecycle_groups(resident_dq_lifecycle_groups),
            "groups": resident_dq_lifecycle_groups,
        }
        if not resident_dq_lifecycle_payload["summary"]["passed"]:
            failed = ", ".join(resident_dq_lifecycle_payload["summary"].get("failed_groups") or [])
            raise RuntimeError(f"resident DQ lifecycle failed for group(s): {failed}")
        write_json(resident_dq_lifecycle_path, resident_dq_lifecycle_payload)
        resident_source_dq_execution_payload = {
            "schema_version": 1,
            "artifact": "resident_source_dq_execution",
            "source_stage": "resident_calibrated_stack",
            "backend": "cuda_resident_stack",
            "summary": summarize_resident_source_dq_execution_groups(resident_source_dq_execution_groups),
            "groups": resident_source_dq_execution_groups,
        }
        if not resident_source_dq_execution_payload["summary"]["passed"]:
            failed = ", ".join(resident_source_dq_execution_payload["summary"].get("failed_groups") or [])
            raise RuntimeError(f"resident source-DQ execution failed for group(s): {failed}")
        write_json(resident_source_dq_execution_path, resident_source_dq_execution_payload)
        resident_master_cache_payload = {
            "schema_version": 1,
            "artifact": "resident_master_cache",
            "source_stage": "resident_calibrated_stack",
            "backend": "cuda_resident_stack",
            "policy": master_cache_policy_record,
            "summary": summarize_resident_master_cache_groups(resident_master_cache_groups),
            "groups": resident_master_cache_groups,
        }
        validate_resident_master_cache_payload(resident_master_cache_payload)
        write_json(resident_master_cache_path, resident_master_cache_payload)
        registration_quality_decisions = list(registration_quality_decisions_by_frame.values())
        registration_quality_payload = {
            "schema_version": 1,
            "source_stage": "resident_calibrated_stack",
            "registration_mode": resident_registration,
            "requested_action": resident_registration_quality_gate,
            "min_inliers": int(resident_registration_quality_min_inliers),
            "max_rms_px": None
            if resident_registration_quality_max_rms_px is None
            else float(resident_registration_quality_max_rms_px),
            "summary": summarize_resident_registration_quality(registration_quality_decisions),
            "decisions": registration_quality_decisions,
        }
        write_json(registration_quality_path, registration_quality_payload, compact=True)
        resident_payload = {
            "schema_version": 1,
            "backend": "cuda_resident_stack",
            "policy": asdict(policy),
            "artifacts": resident_artifacts,
            "device": cuda_module.get_device_info(0),
        }
        write_json(
            resident_path,
            resident_payload,
            compact=True,
        )
        calibration_artifacts = write_resident_calibration_artifacts(
            run,
            resident_payload,
            compact_json=True,
        )
        resident_calibration_contract_path = run / "resident_calibration_contract.json"
        resident_calibration_contract = build_resident_calibration_contract(run)
        write_resident_calibration_contract(
            resident_calibration_contract_path,
            resident_calibration_contract,
        )
        if not resident_calibration_contract.get("passed"):
            raise RuntimeError("resident CUDA calibration contract failed")
        if registration_results:
            matrix_warp_description = f"CUDA matrix {resident_warp_interpolation} warp"
            reference_frame_ids = sorted(
                {
                    str(result.reference_frame_id)
                    for result in registration_results
                    if str(result.reference_frame_id)
                }
            )
            reference_row_ids = sorted(
                {
                    str(result.frame_id)
                    for result in registration_results
                    if result.status == "reference" and str(result.frame_id)
                }
            )
            selected_reference_frame_ids = reference_row_ids or reference_frame_ids
            resident_registration_artifacts = [
                item.get("resident_registration")
                for item in resident_artifacts
                if isinstance(item.get("resident_registration"), dict)
            ]
            reference_selection_sources = sorted(
                {
                    str(registration.get("reference_selection_source"))
                    for registration in resident_registration_artifacts
                    if registration.get("reference_selection_source") is not None
                }
            )
            quality_reference_frame_ids = sorted(
                {
                    str(registration.get("quality_reference_frame_id"))
                    for registration in resident_registration_artifacts
                    if registration.get("quality_reference_frame_id") is not None
                }
            )
            quality_reference_statuses = sorted(
                {
                    str(registration.get("quality_reference_status"))
                    for registration in resident_registration_artifacts
                    if registration.get("quality_reference_status") is not None
                }
            )
            registration_result_rows = [asdict(result) for result in registration_results]
            source_dq_registration_input = _resident_registration_source_dq_input_audit(
                registration_result_rows,
                resident_artifacts,
            )
            write_json(
                run / "registration_results.json",
                {
                    "schema_version": 1,
                    "source_stage": "resident_calibrated_stack",
                    "reference_frame_id": selected_reference_frame_ids[0]
                    if len(selected_reference_frame_ids) == 1
                    else None,
                    "reference_frame_ids": selected_reference_frame_ids,
                    "selected_reference_frame_id": selected_reference_frame_ids[0]
                    if len(selected_reference_frame_ids) == 1
                    else None,
                    "selected_reference_frame_ids": selected_reference_frame_ids,
                    "reference_selection_source": reference_selection_sources[0]
                    if len(reference_selection_sources) == 1
                    else None,
                    "reference_selection_sources": reference_selection_sources,
                    "quality_reference_frame_id": quality_reference_frame_ids[0]
                    if len(quality_reference_frame_ids) == 1
                    else None,
                    "quality_reference_frame_ids": quality_reference_frame_ids,
                    "quality_reference_status": quality_reference_statuses[0]
                    if len(quality_reference_statuses) == 1
                    else None,
                    "quality_reference_statuses": quality_reference_statuses,
                    "transform_model": resident_registration,
                    "source_dq_registration_input_summary": source_dq_registration_input["summary"],
                    "results": registration_result_rows,
                    "warnings": [
                        (
                            "resident registration consumed external matrices; non-translation matrices are applied "
                            f"with {matrix_warp_description}"
                            if resident_registration == "external_matrix"
                            else (
                                "resident registration estimated CUDA catalog similarity matrices and applied them "
                                f"with resident matrix {resident_warp_interpolation} warp"
                            )
                            if resident_registration == "similarity_cuda_catalog"
                            else (
                                "resident registration estimated CUDA triangle descriptor matrices and applied them "
                                "through fused matrix integration"
                                if resident_integration_dispatch == "fused_matrix"
                                else "resident registration estimated CUDA triangle descriptor matrices and applied them "
                                f"with resident matrix {resident_warp_interpolation} warp"
                            )
                            if resident_registration == "similarity_cuda_triangle"
                            else "resident registration is translation-only in the current gate"
                        ),
                        (
                            "similarity-catalog mode records CUDA fit/refine diagnostics in warnings"
                            if resident_registration == "similarity_cuda_catalog"
                            else "triangle-descriptor mode records CUDA descriptor fit/refine diagnostics in warnings"
                            if resident_registration == "similarity_cuda_triangle"
                            else "star-catalog mode records GPU mutual-inlier diagnostics; preview/NCC modes still use "
                            "placeholder matched_stars/inliers/rms"
                            if resident_registration == "translation_star_catalog"
                            else "external_matrix mode preserves matched_stars/inliers/rms from the source artifact"
                            if resident_registration == "external_matrix"
                            else "matched_stars/inliers/rms are placeholders until star-based registration is wired in"
                        ),
                    ],
                },
                compact=True,
            )
        local_norm_path = run / "local_norm_results.json"
        write_json(
            local_norm_path,
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "mode": next((group["mode"] for group in local_norm_groups if group["enabled"]), "off"),
                "enabled": any(group["enabled"] for group in local_norm_groups),
                "crop_box": None,
                "groups": local_norm_groups,
                "warnings": [
                    "resident local normalization runs before integration while frames remain in VRAM"
                ],
            },
        )
        output_rejection_descriptors = [
            output.get("integration_rejection")
            for output in outputs
            if isinstance(output.get("integration_rejection"), dict)
        ]
        resolved_resident_winsorized_modes = sorted(
            {
                str(descriptor.get("resident_winsorized_mode"))
                for descriptor in output_rejection_descriptors
                if descriptor.get("resident_winsorized_mode") is not None
            }
        )
        effective_resident_winsorized_mode = (
            resolved_resident_winsorized_modes[0]
            if len(resolved_resident_winsorized_modes) == 1
            else "mixed"
            if resolved_resident_winsorized_modes
            else resident_winsorized_mode
        )
        unique_rejection_descriptor_keys = {
            json.dumps(descriptor, sort_keys=True)
            for descriptor in output_rejection_descriptors
        }
        effective_rejection_max_fractions = sorted(
            {
                float(descriptor["max_reject_fraction"])
                for descriptor in output_rejection_descriptors
                if descriptor.get("max_reject_fraction") is not None
            }
        )
        effective_rejection_max_fraction = (
            effective_rejection_max_fractions[0]
            if len(effective_rejection_max_fractions) == 1
            else rejection_max_fraction
        )
        if output_rejection_descriptors and len(unique_rejection_descriptor_keys) == 1:
            top_level_rejection_semantics = output_rejection_descriptors[0]
        elif output_rejection_descriptors:
            top_level_rejection_semantics = {
                "mode": rejection_mode,
                "low_sigma": low_sigma,
                "high_sigma": high_sigma,
                "min_samples": rejection_min_samples,
                "max_reject_fraction": effective_rejection_max_fraction,
                "resident_winsorized_mode": effective_resident_winsorized_mode,
                "requested_resident_winsorized_mode": resident_winsorized_mode,
                "mixed_output_descriptors": True,
                "output_descriptor_count": len(output_rejection_descriptors),
                "cpu_baseline_parity": all(
                    bool(descriptor.get("cpu_baseline_parity"))
                    for descriptor in output_rejection_descriptors
                ),
                "approximation": any(
                    bool(descriptor.get("approximation"))
                    for descriptor in output_rejection_descriptors
                ),
            }
        else:
            top_level_rejection_semantics = resident_rejection_descriptor(
                rejection_mode,
                low_sigma,
                high_sigma,
                min_samples=rejection_min_samples,
                max_reject_fraction=rejection_max_fraction,
                resident_winsorized_mode=(
                    effective_resident_winsorized_mode
                    if effective_resident_winsorized_mode
                    in {
                        RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE,
                        RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE,
                    }
                    else RESIDENT_WINSORIZED_SIGMA_FAST_APPROX_MODE
                ),
                requested_resident_winsorized_mode=resident_winsorized_mode,
            )
        integration_warnings: list[str] = []
        if rejection_mode == "winsorized_sigma":
            if resolved_resident_winsorized_modes == [RESIDENT_WINSORIZED_SIGMA_HARDENED_MODE]:
                warning_prefix = (
                    "auto-selected"
                    if resident_winsorized_mode == RESIDENT_WINSORIZED_SIGMA_AUTO_MODE
                    else "used the opt-in"
                )
                integration_warnings.append(
                    "resident CUDA winsorized_sigma "
                    f"{warning_prefix} hardened median/IQR CPU-parity prototype"
                )
            elif len(resolved_resident_winsorized_modes) > 1:
                integration_warnings.append(
                    "resident CUDA winsorized_sigma used mixed per-group implementations: "
                    + ", ".join(resolved_resident_winsorized_modes)
                )
            else:
                integration_warnings.append(
                    "resident CUDA winsorized_sigma is currently a two-stage winsorized mean/std rejection approximation"
                )
        elif rejection_mode == "sigma_clip":
            integration_warnings.append("resident CUDA used two-pass mean/std sigma clipping")
        if weighting_mode == "simple_snr":
            integration_warnings.append("resident CUDA used frame-global mean/std simple_snr weights")
        if tile_local_policy_any_enabled:
            if tile_local_policy_any_applied:
                integration_warnings.append(
                    f"resident tile-local policy replay was applied to {rejection_mode} resident stack integration"
                )
            else:
                integration_warnings.append(
                    "resident tile-local policy replay was validated and recorded but not applied to integration output"
                )
        if any(group["enabled"] for group in local_norm_groups):
            mode = next((group["mode"] for group in local_norm_groups if group["enabled"]), "unknown")
            integration_warnings.append(f"resident CUDA used {mode} local normalization before integration")
        else:
            integration_warnings.append("resident CUDA mode skipped local normalization")
        write_json(
            run / "integration_results.json",
            {
                "schema_version": 1,
                "source_stage": "resident_calibrated_stack",
                "combine": "mean",
                "weighting": weighting_mode,
                "rejection": rejection_mode,
                "requested_resident_winsorized_mode": resident_winsorized_mode,
                "resident_winsorized_mode": effective_resident_winsorized_mode,
                "resident_winsorized_modes": resolved_resident_winsorized_modes,
                "low_sigma": low_sigma,
                "high_sigma": high_sigma,
                "rejection_min_samples": rejection_min_samples,
                "rejection_max_fraction": effective_rejection_max_fraction,
                "rejection_max_fraction_requested": rejection_max_fraction,
                "rejection_max_fraction_source": rejection_max_fraction_source,
                "rejection_semantics": top_level_rejection_semantics,
                "frame_weights": frame_weights,
                "outputs": outputs,
                "excluded_frame_tokens": sorted(excluded_tokens),
                "resident_frame_mask_contract_path": str(resident_frame_masks_path),
                "resident_frame_mask_contract_summary": resident_frame_mask_payload["summary"],
                "resident_dq_pixel_closure_path": str(resident_dq_pixel_closure_path),
                "resident_dq_pixel_closure_summary": resident_dq_pixel_closure_payload["summary"],
                "resident_dq_lifecycle_path": str(resident_dq_lifecycle_path),
                "resident_dq_lifecycle_summary": resident_dq_lifecycle_payload["summary"],
                "resident_source_dq_execution_path": str(resident_source_dq_execution_path),
                "resident_source_dq_execution_summary": resident_source_dq_execution_payload["summary"],
                "resident_master_cache_path": str(resident_master_cache_path),
                "resident_master_cache_summary": resident_master_cache_payload["summary"],
                "warnings": integration_warnings,
            },
            compact=True,
        )
        resident_result_contract_path = run / "resident_result_contract.json"
        resident_result_contract = build_resident_result_contract(run)
        write_resident_result_contract(resident_result_contract_path, resident_result_contract)
        _validate_resident_result_contract_payload(resident_result_contract)
        from glass.engine.frame_accounting import build_frame_accounting

        build_frame_accounting(run, compact_json=True)
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_calibration",
                path=str(run / "calibration_artifacts.json"),
                format="json",
                created_at=now_iso(),
                source_frames=[item.get("frame_id") for item in calibration_artifacts.get("calibrated_lights", [])],
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_calibration_contract",
                path=str(resident_calibration_contract_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
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
                stage="resident_result_contract",
                path=str(resident_result_contract_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_registration_quality",
                path=str(registration_quality_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_frame_masks",
                path=str(resident_frame_masks_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_dq_pixel_closure",
                path=str(resident_dq_pixel_closure_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_dq_lifecycle",
                path=str(resident_dq_lifecycle_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_source_dq_execution",
                path=str(resident_source_dq_execution_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_master_cache",
                path=str(resident_master_cache_path),
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
            + (
                "external registration matrices are applied with CUDA matrix warp when requested"
                if resident_registration == "external_matrix"
                else "resident CUDA catalog similarity matrices are estimated and applied in VRAM"
                if resident_registration == "similarity_cuda_catalog"
                else "resident CUDA triangle descriptor similarity matrices are estimated and applied in VRAM"
                if resident_registration == "similarity_cuda_triangle"
                else f"registration is translation only and local normalization is {resident_local_normalization_mode}"
                " when enabled"
            )
        )
        return state
    except Exception as exc:
        for writer in list(resident_master_cache_write_queues):
            try:
                writer.shutdown()
            except Exception:
                pass
        state.failed_stage = state.current_stage
        state.errors.append(str(exc))
        raise
