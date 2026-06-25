from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


RESIDENT_MEMORY_LIFECYCLE_SCHEMA_VERSION = 1

F32_BYTES = 4
I16_BYTES = 2
U32_BYTES = 4


def _json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _dtype_bytes(dtype: Any, default: int = F32_BYTES) -> int:
    text = str(dtype or "").strip().lower()
    if text in {"uint16", "int16", "i16", "u16"}:
        return I16_BYTES
    if text in {"uint32", "int32", "float32", "f32", "u32", "i32"}:
        return U32_BYTES
    if text in {"uint8", "int8", "u8", "i8", "bool"}:
        return 1
    return default


def _shape(artifact: dict[str, Any]) -> tuple[int, int]:
    shape = artifact.get("shape") if isinstance(artifact.get("shape"), dict) else {}
    height = _as_int(shape.get("height"))
    width = _as_int(shape.get("width"))
    if height > 0 and width > 0:
        return height, width
    memory = artifact.get("memory_estimate") if isinstance(artifact.get("memory_estimate"), dict) else {}
    return _as_int(memory.get("height")), _as_int(memory.get("width"))


def _frame_ids(artifact: dict[str, Any]) -> list[str]:
    values = artifact.get("frame_ids") if isinstance(artifact.get("frame_ids"), list) else []
    return [str(value) for value in values]


def _frame_count(artifact: dict[str, Any]) -> int:
    return _as_int(artifact.get("frame_count"), len(_frame_ids(artifact))) or len(_frame_ids(artifact))


def _active_frame_count(artifact: dict[str, Any]) -> int:
    lifecycle = (
        artifact.get("resident_dq_lifecycle")
        if isinstance(artifact.get("resident_dq_lifecycle"), dict)
        else {}
    )
    summary = lifecycle.get("summary") if isinstance(lifecycle.get("summary"), dict) else {}
    value = _as_int(summary.get("active_frame_count"))
    if value > 0:
        return value
    weights = artifact.get("frame_weights") if isinstance(artifact.get("frame_weights"), list) else []
    positive = 0
    for item in weights:
        if isinstance(item, dict) and _as_float(item.get("weight"), 0.0):
            positive += 1
    return positive or _frame_count(artifact)


def _prefetch_depth(artifact: dict[str, Any]) -> int:
    pipeline = (
        artifact.get("resident_io_pipeline")
        if isinstance(artifact.get("resident_io_pipeline"), dict)
        else {}
    )
    return max(1, _as_int(pipeline.get("prefetch_frames"), 1))


def _calibration_batch_frames(artifact: dict[str, Any]) -> int:
    pipeline = (
        artifact.get("resident_io_pipeline")
        if isinstance(artifact.get("resident_io_pipeline"), dict)
        else {}
    )
    return max(1, _as_int(pipeline.get("calibration_batch_frames"), 1))


def _host_pinned_bytes(artifact: dict[str, Any], fallback: int) -> int:
    pipeline = (
        artifact.get("resident_io_pipeline")
        if isinstance(artifact.get("resident_io_pipeline"), dict)
        else {}
    )
    values = [
        _as_int(pipeline.get("host_pinned_bytes")),
        _as_int(pipeline.get("prefetch_host_pinned_bytes")),
    ]
    return max([fallback, *values])


def _output_map_bytes(artifact: dict[str, Any], pixels: int) -> tuple[int, list[str]]:
    output_names: list[str] = []
    total = 0
    if artifact.get("master_path"):
        output_names.append("master")
        total += pixels * F32_BYTES
    if artifact.get("weight_map_path"):
        output_names.append("weight")
        total += pixels * F32_BYTES
    if artifact.get("coverage_map_path"):
        output_names.append("coverage")
        total += pixels * F32_BYTES
    if artifact.get("low_rejection_map_path"):
        output_names.append("low_rejection")
        total += pixels * F32_BYTES
    if artifact.get("high_rejection_map_path"):
        output_names.append("high_rejection")
        total += pixels * F32_BYTES
    if artifact.get("dq_map_path"):
        output_names.append("dq")
        total += pixels * _dtype_bytes(artifact.get("dq_map_runtime_dtype"), default=U32_BYTES)
    return total, output_names


def _surface(
    *,
    group_index: int,
    filter_name: str | None,
    name: str,
    phase: str,
    memory_space: str,
    residence: str,
    estimated_bytes: int,
    frame_count: int | None,
    release_after: str,
    evidence: dict[str, Any] | None = None,
    status: str = "declared",
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "group_index": group_index,
        "filter": filter_name,
        "name": name,
        "phase": phase,
        "memory_space": memory_space,
        "residence": residence,
        "status": status,
        "estimated_bytes": int(max(0, estimated_bytes)),
        "estimated_mib": int(max(0, estimated_bytes)) / (1024**2),
        "frame_count": frame_count,
        "release_after": release_after,
        "evidence": evidence or {},
        "notes": notes or [],
    }


def _build_group_lifecycle(
    artifact: dict[str, Any],
    *,
    group_index: int,
    calibration_payload: dict[str, Any],
) -> dict[str, Any]:
    height, width = _shape(artifact)
    pixels = max(0, height * width)
    frame_count = _frame_count(artifact)
    active_frame_count = _active_frame_count(artifact)
    frame_bytes = pixels * F32_BYTES
    filter_name = artifact.get("filter")
    if filter_name is not None:
        filter_name = str(filter_name)
    memory_estimate = (
        artifact.get("memory_estimate")
        if isinstance(artifact.get("memory_estimate"), dict)
        else {}
    )
    master_count = 3
    masters = calibration_payload.get("masters")
    if isinstance(masters, dict) and masters:
        master_count = len(masters)
    output_bytes, output_names = _output_map_bytes(artifact, pixels)
    prefetch_depth = _prefetch_depth(artifact)
    calibration_batch_frames = _calibration_batch_frames(artifact)
    host_pinned_estimate = _host_pinned_bytes(artifact, frame_bytes * prefetch_depth)
    warp_scratch_bytes = _as_int(artifact.get("resident_warp_scratch_bytes"))
    dispatch = (
        artifact.get("resident_integration_dispatch")
        if isinstance(artifact.get("resident_integration_dispatch"), dict)
        else {}
    )
    dispatch_mode = str(
        dispatch.get("effective_mode")
        or artifact.get("resident_integration_dispatch")
        or "unknown"
    )
    local_norm = (
        artifact.get("resident_local_normalization")
        if isinstance(artifact.get("resident_local_normalization"), dict)
        else {}
    )
    local_norm_enabled = bool(local_norm.get("enabled"))

    surfaces = [
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="source_light_decode_host_prefetch",
            phase="raw_decode_prefetch",
            memory_space="host_pinned_or_pageable",
            residence="transient",
            estimated_bytes=host_pinned_estimate,
            frame_count=min(frame_count, prefetch_depth),
            release_after="device_upload_or_prefetch_slot_reuse",
            evidence={
                "prefetch_frames": prefetch_depth,
                "host_pinned_bytes": _as_int(
                    (
                        artifact.get("resident_io_pipeline")
                        if isinstance(artifact.get("resident_io_pipeline"), dict)
                        else {}
                    ).get("host_pinned_bytes")
                ),
            },
            notes=["Raw FITS data is staged transiently; all raw light frames are not retained together."],
        ),
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="raw_light_device_upload_buffer",
            phase="h2d_calibration",
            memory_space="device",
            residence="transient",
            estimated_bytes=frame_bytes * calibration_batch_frames,
            frame_count=min(frame_count, calibration_batch_frames),
            release_after="calibrated_frame_store",
            evidence={"calibration_batch_frames": calibration_batch_frames},
            notes=["Raw device input buffers are reusable staging surfaces before calibration."],
        ),
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="master_calibration_surfaces",
            phase="calibration",
            memory_space="device_or_cache_backed",
            residence="cached_transient",
            estimated_bytes=frame_bytes * master_count,
            frame_count=master_count,
            release_after="resident_light_calibration_complete_or_cache_reuse",
            evidence={
                "master_surface_count": master_count,
                "resident_master_cache": artifact.get("resident_master_cache"),
            },
            notes=["Master bias/dark/flat surfaces are used for calibration and represented by cache metadata."],
        ),
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="calibrated_resident_stack",
            phase="resident_light_calibration",
            memory_space="device",
            residence="resident_until_integration",
            estimated_bytes=frame_bytes * frame_count,
            frame_count=frame_count,
            release_after="resident_integration_complete",
            evidence={
                "resident_bytes_allocated_after_master_upload": _as_int(
                    artifact.get("resident_bytes_allocated_after_master_upload")
                ),
                "calibrated_light_status": "resident_in_vram",
            },
            notes=["Calibrated light frames are the primary resident stack consumed by later stages."],
        ),
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="registration_warp_workspace",
            phase="resident_registration_warp",
            memory_space="device",
            residence="transient_or_in_place",
            estimated_bytes=warp_scratch_bytes,
            frame_count=active_frame_count,
            release_after="registration_warp_complete_or_fused_integration_complete",
            evidence={
                "resident_warp_scratch_bytes": warp_scratch_bytes,
                "resident_warp_copy_mode": artifact.get("resident_warp_copy_mode"),
                "integration_dispatch": dispatch_mode,
            },
            status="not_allocated" if warp_scratch_bytes == 0 else "declared",
            notes=[
                "Fused matrix integration can avoid a separate registered full-frame stack.",
            ],
        ),
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="local_normalization_surface",
            phase="resident_local_normalization",
            memory_space="device",
            residence="in_place_or_disabled",
            estimated_bytes=0,
            frame_count=active_frame_count if local_norm_enabled else 0,
            release_after="normalization_apply_complete",
            evidence={
                "enabled": local_norm_enabled,
                "mode": local_norm.get("mode"),
                "application": local_norm.get("application"),
            },
            status="declared" if local_norm_enabled else "disabled",
            notes=["Current resident local normalization applies coefficients to resident frames rather than writing a disk cache."],
        ),
        _surface(
            group_index=group_index,
            filter_name=filter_name,
            name="integration_output_workspace",
            phase="resident_integration",
            memory_space="device_to_host_output",
            residence="transient_until_fits_write",
            estimated_bytes=output_bytes,
            frame_count=len(output_names),
            release_after="output_write_complete",
            evidence={"output_maps": output_names},
            notes=["Output maps are downloaded or materialized according to the resident output-map policy."],
        ),
    ]

    checks = [
        {
            "name": "shape_present",
            "passed": height > 0 and width > 0,
            "details": {"height": height, "width": width},
        },
        {
            "name": "frame_count_present",
            "passed": frame_count > 0,
            "details": {"frame_count": frame_count},
        },
        {
            "name": "raw_inputs_are_streamed_not_all_resident",
            "passed": prefetch_depth < frame_count if frame_count > 1 else True,
            "details": {"prefetch_frames": prefetch_depth, "frame_count": frame_count},
        },
        {
            "name": "calibrated_stack_resident_until_integration",
            "passed": frame_count > 0 and frame_bytes > 0,
            "details": {
                "estimated_bytes": frame_bytes * frame_count,
                "release_after": "resident_integration_complete",
            },
        },
        {
            "name": "memory_peak_estimate_present",
            "passed": _as_int(memory_estimate.get("estimated_peak_bytes")) > 0,
            "details": {
                "estimated_peak_bytes": memory_estimate.get("estimated_peak_bytes"),
                "estimated_peak_gib": memory_estimate.get("estimated_peak_gib"),
            },
        },
        {
            "name": "integration_outputs_declared",
            "passed": bool(output_names),
            "details": {"output_maps": output_names},
        },
    ]
    passed = all(bool(item["passed"]) for item in checks)
    return {
        "group_index": group_index,
        "filter": filter_name,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "shape": {"height": height, "width": width, "pixels": pixels},
        "frame_count": frame_count,
        "active_frame_count": active_frame_count,
        "masked_frame_count": max(0, frame_count - active_frame_count),
        "estimated_frame_bytes": frame_bytes,
        "estimated_calibrated_stack_bytes": frame_bytes * frame_count,
        "estimated_output_download_bytes": output_bytes,
        "estimated_peak_bytes": _as_int(memory_estimate.get("estimated_peak_bytes")),
        "estimated_peak_gib": _as_float(memory_estimate.get("estimated_peak_gib")),
        "surfaces": surfaces,
        "checks": checks,
        "limitations": [
            "Lifecycle byte counts are estimates derived from run-local artifacts, not allocator traces.",
            "Raw FITS frames are streamed through reusable host/device buffers in the current resident path.",
            "Calibrated frames remain resident; registration, local normalization, and integration consume that stack.",
        ],
    }


def build_resident_memory_lifecycle(
    run_dir: str | Path,
    *,
    timing: dict[str, Any] | None = None,
    resident_payload: dict[str, Any] | None = None,
    calibration_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    resident = (
        resident_payload
        if isinstance(resident_payload, dict)
        else _json_object(run / "resident_artifacts.json")
    )
    calibration = (
        calibration_payload
        if isinstance(calibration_payload, dict)
        else _json_object(run / "calibration_artifacts.json")
    )
    timing_payload = timing if isinstance(timing, dict) else _json_object(run / "run_timing.json")
    artifacts = resident.get("artifacts") if isinstance(resident.get("artifacts"), list) else []
    groups = [
        _build_group_lifecycle(
            artifact,
            group_index=index,
            calibration_payload=calibration,
        )
        for index, artifact in enumerate(artifacts)
        if isinstance(artifact, dict)
    ]
    group_failures = [
        {"group_index": group["group_index"], "status": group["status"]}
        for group in groups
        if not group["passed"]
    ]
    max_peak = max((_as_int(group.get("estimated_peak_bytes")) for group in groups), default=0)
    max_calibrated = max(
        (_as_int(group.get("estimated_calibrated_stack_bytes")) for group in groups),
        default=0,
    )
    total_output = sum(_as_int(group.get("estimated_output_download_bytes")) for group in groups)
    resident_stage_elapsed = None
    for row in timing_payload.get("stages") or []:
        if isinstance(row, dict) and row.get("stage") == "resident_calibration_integration":
            resident_stage_elapsed = _as_float(row.get("elapsed_s"))
            break
    passed = bool(groups) and not group_failures
    return {
        "schema_version": RESIDENT_MEMORY_LIFECYCLE_SCHEMA_VERSION,
        "artifact_type": "resident_memory_lifecycle",
        "created_at": now_iso(),
        "run": str(run),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "source": {
            "resident_artifacts_path": str(run / "resident_artifacts.json"),
            "calibration_artifacts_path": str(run / "calibration_artifacts.json"),
            "run_timing_path": str(run / "run_timing.json"),
            "resident_artifacts_exists": (run / "resident_artifacts.json").exists(),
            "calibration_artifacts_exists": (run / "calibration_artifacts.json").exists(),
            "run_timing_exists": (run / "run_timing.json").exists(),
        },
        "summary": {
            "group_count": len(groups),
            "passed_group_count": len(groups) - len(group_failures),
            "failed_group_count": len(group_failures),
            "max_estimated_peak_bytes": max_peak,
            "max_estimated_peak_gib": max_peak / (1024**3),
            "max_estimated_calibrated_stack_bytes": max_calibrated,
            "max_estimated_calibrated_stack_gib": max_calibrated / (1024**3),
            "total_estimated_output_download_bytes": total_output,
            "resident_calibration_integration_elapsed_s": resident_stage_elapsed,
            "raw_all_frames_resident": False,
            "calibrated_stack_resident": bool(groups),
            "registered_cache_materialized_on_disk": False,
            "lifecycle_model": "estimated_from_resident_runtime_artifacts_v1",
        },
        "groups": groups,
        "failed_groups": group_failures,
        "checks": [
            {
                "name": "resident_artifacts_present",
                "passed": bool(artifacts),
                "details": {"artifact_count": len(artifacts)},
            },
            {
                "name": "all_groups_pass_lifecycle_contract",
                "passed": not group_failures and bool(groups),
                "details": {"failed_groups": group_failures},
            },
            {
                "name": "raw_to_calibrated_to_integration_release_chain_declared",
                "passed": bool(groups),
                "details": {
                    "required_phases": [
                        "raw_decode_prefetch",
                        "h2d_calibration",
                        "resident_light_calibration",
                        "resident_integration",
                    ]
                },
            },
        ],
    }


def materialize_resident_memory_lifecycle(
    timing: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    timing["resident_memory_lifecycle_path"] = "resident_memory_lifecycle.json"
    summary = payload.get("summary")
    if isinstance(summary, dict):
        timing["resident_memory_lifecycle_summary"] = summary
    return timing


def write_resident_memory_lifecycle(
    run_dir: str | Path,
    *,
    timing: dict[str, Any] | None = None,
    resident_payload: dict[str, Any] | None = None,
    calibration_payload: dict[str, Any] | None = None,
) -> Path:
    run = Path(run_dir)
    path = run / "resident_memory_lifecycle.json"
    write_json(
        path,
        build_resident_memory_lifecycle(
            run,
            timing=timing,
            resident_payload=resident_payload,
            calibration_payload=calibration_payload,
        ),
    )
    return path
