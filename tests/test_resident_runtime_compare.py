from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_runtime_compare import build_resident_runtime_compare


def _write_run(path: Path, *, elapsed: float, read_wait: float, worker_read: float) -> None:
    path.mkdir()
    write_json(path / "run_timing.json", {"total_elapsed_s": elapsed})
    write_json(
        path / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "timing_s": {
                        "light_read_wait_wall": read_wait,
                        "light_read_worker_cumulative": worker_read,
                        "light_h2d_calibrate_store": 2.0,
                        "resident_registration_warp": 1.5,
                        "output_write": 2.5,
                    },
                    "resident_io_pipeline": {
                        "prefetch_frames": 12,
                        "prefetch_workers": 7,
                        "prefetch_refill_mode": "queued",
                        "h2d_mode": "pinned_ring",
                        "calibration_batch_requested_frames": 8,
                        "calibration_batch_requested_streams": 4,
                        "calibration_wave_requested_frames": 2,
                        "calibration_release_mode_requested": "callback_queue",
                        "calibration_release_mode_effective": "callback_queue",
                    },
                }
            ]
        },
    )


def test_resident_runtime_compare_flags_read_wait_variance(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed=17.1, read_wait=3.0, worker_read=35.0)
    _write_run(candidate, elapsed=23.3, read_wait=8.0, worker_read=72.0)

    payload = build_resident_runtime_compare(
        [("gate158", baseline), ("preset", candidate)],
        baseline_label="gate158",
    )

    assert payload["summary"]["best_label"] == "gate158"
    assert payload["summary"]["recommendation"] == "repeat_with_warm_cache_or_dedicated_io_window"
    comparison = payload["comparisons"][0]
    assert comparison["elapsed_ratio"] > 1.3
    assert comparison["timing_delta"]["light_read_wait_wall"]["ratio"] > 2.0


def test_resident_runtime_compare_cli_writes_outputs(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    out = tmp_path / "runtime_compare.json"
    markdown = tmp_path / "runtime_compare.md"
    _write_run(baseline, elapsed=17.1, read_wait=3.0, worker_read=35.0)
    _write_run(candidate, elapsed=17.0, read_wait=3.1, worker_read=36.0)

    assert (
        main(
            [
                "resident-runtime-compare",
                "--run",
                f"baseline={baseline}",
                "--run",
                f"candidate={candidate}",
                "--baseline-label",
                "baseline",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "resident_runtime_compare"
    assert payload["summary"]["best_label"] == "candidate"
    assert "Resident Runtime Compare" in markdown.read_text(encoding="utf-8")
