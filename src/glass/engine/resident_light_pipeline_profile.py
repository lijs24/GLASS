from __future__ import annotations

from typing import Any, Mapping


def _float_value(mapping: Mapping[str, Any], key: str) -> float:
    try:
        return float(mapping.get(key) or 0.0)
    except (TypeError, ValueError, OverflowError):
        return 0.0


def _int_value(mapping: Mapping[str, Any], key: str) -> int:
    try:
        return int(mapping.get(key) or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def _fraction(value: float, total: float) -> float:
    return float(value / total) if total > 0.0 else 0.0


def build_resident_light_pipeline_profile(
    *,
    timing_s: Mapping[str, Any],
    resident_io_pipeline: Mapping[str, Any],
    resident_io_overlap: Mapping[str, Any],
) -> dict[str, Any]:
    """Summarize the resident light read/upload/calibration wall-time profile."""

    wall = _float_value(timing_s, "light_read_upload_calibrate")
    read_wait = _float_value(timing_s, "light_read_wait_wall")
    master_build_or_load = _float_value(timing_s, "light_master_build_or_load_in_loop")
    native = _float_value(timing_s, "light_calibration_batch_native_total")
    calibrate_store = _float_value(timing_s, "light_calibrate_store")
    sync = _float_value(timing_s, "light_calibration_batch_sync")
    unaccounted = _float_value(timing_s, "light_loop_unaccounted")
    unaccounted_without_master = _float_value(timing_s, "light_loop_unaccounted_without_master")
    overlap_saved = _float_value(timing_s, "light_read_overlap_saved")
    components = {
        "master_build_or_load": master_build_or_load,
        "consumer_read_wait": read_wait,
        "native_h2d_calibrate_store": native,
        "native_calibrate_store": calibrate_store,
        "native_sync": sync,
        "python_orchestration_unaccounted": unaccounted,
    }
    ranked = sorted(
        (
            {
                "component": name,
                "seconds": seconds,
                "fraction_of_wall": _fraction(seconds, wall),
            }
            for name, seconds in components.items()
        ),
        key=lambda item: item["seconds"],
        reverse=True,
    )
    dominant = ranked[0]["component"] if ranked else "unknown"
    master_fraction = _fraction(master_build_or_load, wall)
    read_wait_fraction = _fraction(read_wait, wall)
    native_fraction = _fraction(native, wall)
    unaccounted_fraction = _fraction(unaccounted, wall)
    if master_fraction >= 0.45:
        recommendation = "reuse_or_prebuild_master_calibration_cache"
    elif read_wait_fraction >= 0.45 and native_fraction < 0.40:
        recommendation = "increase_prefetch_supply_or_reduce_decode_cost"
    elif read_wait_fraction >= 0.30 and native_fraction >= 0.30:
        recommendation = "balance_prefetch_supply_against_native_contention"
    elif native_fraction >= 0.45:
        recommendation = "optimize_native_h2d_calibration_or_memory_contention"
    elif unaccounted_fraction >= 0.20:
        recommendation = "profile_python_orchestration"
    else:
        recommendation = "balanced_pipeline_no_single_dominant_component"

    return {
        "schema_version": 1,
        "stage": "resident_light_read_upload_calibrate",
        "wall_s": wall,
        "dominant_component": dominant,
        "recommendation": recommendation,
        "components_s": components,
        "components_ranked": ranked,
        "fractions": {
            "master_build_or_load": master_fraction,
            "consumer_read_wait": read_wait_fraction,
            "native_h2d_calibrate_store": native_fraction,
            "python_orchestration_unaccounted": unaccounted_fraction,
            "python_orchestration_unaccounted_without_master": _fraction(
                unaccounted_without_master,
                wall,
            ),
        },
        "overlap": {
            "saved_s": overlap_saved,
            "efficiency": _float_value(resident_io_overlap, "overlap_efficiency"),
            "consumer_wait_fraction_of_wall": _float_value(
                resident_io_overlap,
                "consumer_wait_fraction_of_wall",
            ),
            "worker_cumulative_to_wall_ratio": _float_value(
                resident_io_overlap,
                "worker_cumulative_to_wall_ratio",
            ),
        },
        "knobs": {
            "prefetch_frames": _int_value(resident_io_pipeline, "prefetch_frames"),
            "prefetch_workers": _int_value(resident_io_pipeline, "prefetch_workers"),
            "prefetch_refill_mode": resident_io_pipeline.get("prefetch_refill_mode"),
            "h2d_mode": resident_io_pipeline.get("h2d_mode"),
            "calibration_batch_requested_frames": _int_value(
                resident_io_pipeline,
                "calibration_batch_requested_frames",
            ),
            "calibration_batch_requested_streams": _int_value(
                resident_io_pipeline,
                "calibration_batch_requested_streams",
            ),
            "calibration_wave_requested_frames": _int_value(
                resident_io_pipeline,
                "calibration_wave_requested_frames",
            ),
            "calibration_release_mode_effective": resident_io_pipeline.get(
                "calibration_release_mode_effective"
            ),
            "prefetch_fill_blocked_no_slot_count": _int_value(
                resident_io_pipeline,
                "prefetch_fill_blocked_no_slot_count",
            ),
            "host_pinned_bytes": _int_value(resident_io_pipeline, "host_pinned_bytes"),
        },
        "semantics": (
            "This profile decomposes resident light loading into consumer "
            "read/decode wait, master calibration build/load performed inside "
            "the light loop, native H2D+calibration/store time, and remaining "
            "Python orchestration. It is diagnostic only and does not change "
            "image math or scheduling by itself."
        ),
    }
