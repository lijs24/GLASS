from __future__ import annotations

from pathlib import Path

from glass.engine.resident_memory_lifecycle import (
    build_resident_memory_lifecycle,
    write_resident_memory_lifecycle,
)
from glass.io.json_io import read_json, write_json


def _write_fixture_run(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    write_json(
        path / "resident_artifacts.json",
        {
            "artifact_type": "resident_cuda_artifacts",
            "backend": "cuda_resident_stack",
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["L1", "L2", "L3", "L4"],
                    "frame_count": 4,
                    "shape": {"height": 10, "width": 12},
                    "master_path": str(path / "integration" / "master_H.fits"),
                    "weight_map_path": str(path / "integration" / "weight_H.fits"),
                    "coverage_map_path": str(path / "integration" / "coverage_H.fits"),
                    "low_rejection_map_path": str(path / "integration" / "low_H.fits"),
                    "high_rejection_map_path": str(path / "integration" / "high_H.fits"),
                    "dq_map_path": str(path / "integration" / "dq_H.fits"),
                    "dq_map_runtime_dtype": "uint32",
                    "resident_dq_lifecycle": {
                        "summary": {
                            "passed": True,
                            "active_frame_count": 3,
                            "masked_frame_count": 1,
                        }
                    },
                    "resident_master_cache": {
                        "summary": {
                            "set_count": 1,
                            "total_required_bytes": 1440,
                        }
                    },
                    "resident_io_pipeline": {
                        "prefetch_frames": 2,
                        "host_pinned_bytes": 960,
                        "prefetch_host_pinned_bytes": 960,
                        "calibration_batch_frames": 2,
                    },
                    "resident_integration_dispatch": {"effective_mode": "stack"},
                    "resident_local_normalization": {
                        "enabled": True,
                        "mode": "grid_mean_std",
                        "application": {"mode_counts": {"in_place_device_update": 3}},
                    },
                    "resident_warp_scratch_bytes": 256,
                    "resident_warp_copy_mode": "default_stream_async_device_to_device",
                    "resident_bytes_allocated_after_master_upload": 1920,
                    "memory_estimate": {
                        "height": 10,
                        "width": 12,
                        "estimated_peak_bytes": 8192,
                        "estimated_peak_gib": 8192 / (1024**3),
                    },
                }
            ],
        },
    )
    write_json(
        path / "calibration_artifacts.json",
        {
            "artifact_type": "resident_cuda_calibration_artifacts",
            "masters": {
                "bias": {"status": "resident_cache"},
                "dark": {"status": "resident_cache"},
                "flat": {"status": "resident_cache"},
            },
        },
    )
    write_json(
        path / "run_timing.json",
        {
            "schema_version": 1,
            "stages": [
                {"stage": "resident_calibration_integration", "elapsed_s": 1.25},
            ],
        },
    )


def test_build_resident_memory_lifecycle_records_release_chain(tmp_path: Path) -> None:
    _write_fixture_run(tmp_path)

    payload = build_resident_memory_lifecycle(tmp_path)

    assert payload["artifact_type"] == "resident_memory_lifecycle"
    assert payload["passed"] is True
    assert payload["summary"]["group_count"] == 1
    assert payload["summary"]["raw_all_frames_resident"] is False
    assert payload["summary"]["calibrated_stack_resident"] is True
    assert payload["summary"]["max_estimated_peak_bytes"] == 8192
    assert payload["summary"]["resident_calibration_integration_elapsed_s"] == 1.25
    group = payload["groups"][0]
    assert group["frame_count"] == 4
    assert group["active_frame_count"] == 3
    assert group["estimated_calibrated_stack_bytes"] == 10 * 12 * 4 * 4
    surfaces = {row["name"]: row for row in group["surfaces"]}
    assert surfaces["source_light_decode_host_prefetch"]["residence"] == "transient"
    assert surfaces["source_light_decode_host_prefetch"]["release_after"] == (
        "device_upload_or_prefetch_slot_reuse"
    )
    assert surfaces["raw_light_device_upload_buffer"]["release_after"] == "calibrated_frame_store"
    assert surfaces["calibrated_resident_stack"]["residence"] == "resident_until_integration"
    assert surfaces["calibrated_resident_stack"]["release_after"] == "resident_integration_complete"
    assert surfaces["registration_warp_workspace"]["estimated_bytes"] == 256
    assert surfaces["local_normalization_surface"]["status"] == "declared"
    assert surfaces["integration_output_workspace"]["frame_count"] == 6
    checks = {item["name"]: item["passed"] for item in group["checks"]}
    assert checks["raw_inputs_are_streamed_not_all_resident"] is True
    assert checks["calibrated_stack_resident_until_integration"] is True


def test_write_resident_memory_lifecycle_outputs_json(tmp_path: Path) -> None:
    _write_fixture_run(tmp_path)

    out = write_resident_memory_lifecycle(tmp_path)
    payload = read_json(out)

    assert out == tmp_path / "resident_memory_lifecycle.json"
    assert payload["passed"] is True
    assert payload["source"]["resident_artifacts_exists"] is True


def test_build_resident_memory_lifecycle_fails_without_resident_artifacts(tmp_path: Path) -> None:
    payload = build_resident_memory_lifecycle(tmp_path)

    assert payload["passed"] is False
    assert payload["summary"]["group_count"] == 0
    assert payload["checks"][0]["name"] == "resident_artifacts_present"
    assert payload["checks"][0]["passed"] is False
