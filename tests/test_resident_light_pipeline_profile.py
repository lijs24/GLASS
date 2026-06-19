from __future__ import annotations

from glass.engine.resident_light_pipeline_profile import build_resident_light_pipeline_profile


def test_light_pipeline_profile_detects_read_wait_dominance() -> None:
    profile = build_resident_light_pipeline_profile(
        timing_s={
            "light_read_upload_calibrate": 10.0,
            "light_read_wait_wall": 6.0,
            "light_calibration_batch_native_total": 2.0,
            "light_calibrate_store": 1.9,
            "light_calibration_batch_sync": 0.1,
            "light_loop_unaccounted": 1.0,
            "light_read_overlap_saved": 20.0,
        },
        resident_io_pipeline={
            "prefetch_frames": 12,
            "prefetch_workers": 7,
            "prefetch_refill_mode": "queued",
            "h2d_mode": "pinned_ring",
            "calibration_batch_requested_frames": 8,
            "calibration_batch_requested_streams": 4,
            "calibration_wave_requested_frames": 2,
            "calibration_release_mode_effective": "callback_queue",
            "prefetch_fill_blocked_no_slot_count": 70,
            "host_pinned_bytes": 123,
        },
        resident_io_overlap={
            "overlap_efficiency": 0.9,
            "consumer_wait_fraction_of_wall": 0.6,
            "worker_cumulative_to_wall_ratio": 5.0,
        },
    )

    assert profile["dominant_component"] == "consumer_read_wait"
    assert profile["recommendation"] == "increase_prefetch_supply_or_reduce_decode_cost"
    assert profile["fractions"]["consumer_read_wait"] == 0.6
    assert profile["knobs"]["prefetch_frames"] == 12
    assert profile["knobs"]["calibration_release_mode_effective"] == "callback_queue"


def test_light_pipeline_profile_detects_balanced_prefetch_contention() -> None:
    profile = build_resident_light_pipeline_profile(
        timing_s={
            "light_read_upload_calibrate": 10.0,
            "light_read_wait_wall": 3.2,
            "light_calibration_batch_native_total": 3.6,
            "light_loop_unaccounted": 1.2,
        },
        resident_io_pipeline={},
        resident_io_overlap={},
    )

    assert profile["dominant_component"] == "native_h2d_calibrate_store"
    assert profile["recommendation"] == "balance_prefetch_supply_against_native_contention"
