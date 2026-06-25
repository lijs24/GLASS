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


def test_light_pipeline_profile_accounts_master_load_inside_light_loop() -> None:
    profile = build_resident_light_pipeline_profile(
        timing_s={
            "light_read_upload_calibrate": 14.0,
            "light_master_build_or_load_in_loop": 10.5,
            "light_read_wait_wall": 2.0,
            "light_calibration_batch_native_total": 0.8,
            "master_cache_async_write_wait": 0.25,
            "master_cache_async_write_total": 2.75,
            "light_loop_unaccounted": 0.2,
            "light_loop_unaccounted_without_master": 10.7,
        },
        resident_io_pipeline={
            "master_cache_async_write": {
                "mode": "async_background",
                "written_bytes": 739890139,
            },
        },
        resident_io_overlap={},
    )

    assert profile["dominant_component"] == "master_build_or_load"
    assert profile["recommendation"] == "reuse_or_prebuild_master_calibration_cache"
    assert profile["components_s"]["master_build_or_load"] == 10.5
    assert profile["components_s"]["python_orchestration_unaccounted"] == 0.2
    assert profile["background_cache_write"]["mode"] == "async_background"
    assert profile["background_cache_write"]["wait_s"] == 0.25
    assert profile["background_cache_write"]["hidden_write_s"] == 2.5
    assert profile["background_cache_write"]["written_bytes"] == 739890139
    assert profile["fractions"]["python_orchestration_unaccounted_without_master"] == 10.7 / 14.0


def test_light_pipeline_profile_exposes_native_completion_lane_fill() -> None:
    profile = build_resident_light_pipeline_profile(
        timing_s={
            "light_read_upload_calibrate": 4.0,
            "light_calibration_batch_native_total": 2.5,
            "light_calibrate_store": 2.3,
            "light_calibration_batch_sync": 0.1,
            "light_loop_unaccounted": 0.2,
        },
        resident_io_pipeline={
            "calibration_batch_requested_streams": 8,
            "native_path_calibration_total_s": 29.0,
            "native_path_calibration_file_open_s": 0.4,
            "native_path_calibration_file_read_s": 28.5,
            "native_completion_calibration_enabled": True,
            "native_completion_calibration_submit_count": 200,
            "native_completion_calibration_completion_count": 200,
            "native_completion_calibration_out_of_order_count": 3,
            "native_completion_calibration_worker_count": 16,
            "native_completion_calibration_queue_buffer_count": 32,
            "native_completion_calibration_slot_release_mode": "event_query_deferred_reuse",
            "native_completion_calibration_slot_reuse_count": 168,
            "native_completion_calibration_slot_reuse_wait_count": 0,
            "native_completion_calibration_slot_reuse_wait_s": 0.0,
            "native_completion_calibration_consumer_schedule_mode": "completion_lane_wave_drain",
            "native_completion_calibration_consumer_wave_count": 41,
            "native_completion_calibration_consumer_max_wave_frames": 8,
            "native_completion_calibration_consumer_multi_frame_wave_count": 33,
            "native_completion_calibration_consumer_wave_fill_mode": "single_wait",
            "native_completion_calibration_consumer_wave_fill_mode_requested": "single_wait",
            "native_completion_calibration_consumer_wave_fill_mode_source": "cli",
            "native_completion_calibration_consumer_wave_fill_policy": "timed_wait_25us",
            "native_completion_calibration_consumer_wave_fill_wait_strategy": "micro_poll_yield",
            "native_completion_calibration_consumer_wave_fill_source": "cli",
            "native_completion_calibration_consumer_wave_fill_wait_us": 25,
            "native_completion_calibration_consumer_wave_fill_requested_wait_us": 25,
            "native_completion_calibration_consumer_wave_fill_wait_count": 167,
            "native_completion_calibration_consumer_wave_fill_timeout_count": 38,
            "native_completion_calibration_consumer_wave_fill_wait_s": 0.288,
        },
        resident_io_overlap={
            "read_supply_model": "native_completion_calibration",
            "read_supply_worker_cumulative_s": 29.0,
            "read_supply_file_read_cumulative_s": 28.5,
            "read_supply_consumer_wait_wall_s": 0.288,
            "read_supply_overlap_saved_s": 25.0,
            "read_supply_overlap_efficiency": 25.0 / 29.0,
            "read_supply_worker_to_wall_ratio": 29.0 / 4.0,
            "native_completion_worker_cumulative_s": 29.0,
            "native_completion_file_open_cumulative_s": 0.4,
            "native_completion_file_read_cumulative_s": 28.5,
            "native_completion_consumer_wait_wall_s": 0.288,
            "native_completion_hidden_by_stage_s": 25.0,
            "native_completion_worker_to_wall_ratio": 29.0 / 4.0,
        },
    )

    native = profile["native_completion"]
    assert native["enabled"] is True
    assert profile["overlap"]["model"] == "native_completion_calibration"
    assert profile["overlap"]["worker_cumulative_s"] == 29.0
    assert profile["overlap"]["file_read_cumulative_s"] == 28.5
    assert profile["overlap"]["saved_s"] == 25.0
    assert profile["overlap"]["worker_cumulative_to_wall_ratio"] == 29.0 / 4.0
    assert native["worker_cumulative_s"] == 29.0
    assert native["file_open_cumulative_s"] == 0.4
    assert native["file_read_cumulative_s"] == 28.5
    assert native["consumer_wait_wall_s"] == 0.288
    assert native["hidden_by_stage_s"] == 25.0
    assert native["worker_to_wall_ratio"] == 29.0 / 4.0
    assert native["completion_count"] == 200
    assert native["worker_count"] == 16
    assert native["queue_buffer_count"] == 32
    assert native["queue_buffers_per_stream"] == 4.0
    assert native["consumer_lane_fill_ratio"] == 200 / (41 * 8)
    assert native["consumer_multi_frame_wave_fraction"] == 33 / 41
    assert native["consumer_wave_fill_mode"] == "single_wait"
    assert native["consumer_wave_fill_mode_requested"] == "single_wait"
    assert native["consumer_wave_fill_mode_source"] == "cli"
    assert native["consumer_wave_fill_wait_strategy"] == "micro_poll_yield"
    assert native["consumer_wave_fill_wait_s"] == 0.288
    assert profile["knobs"]["native_completion_calibration_enabled"] is True
    assert profile["knobs"]["native_completion_consumer_lane_fill_ratio"] == 200 / (41 * 8)
    assert profile["knobs"]["native_completion_consumer_wave_fill_mode"] == "single_wait"
    assert profile["recommendation"] == "improve_native_completion_wave_fill_before_adding_lanes"
