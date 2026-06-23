from __future__ import annotations

import json
from pathlib import Path

from glass.cli import main
from glass.io.json_io import write_json
from glass.report.speedup_report import summarize_wbpp_speedup, write_speedup_summary


def test_speedup_summary_reads_glass_and_wbpp_blackbox_artifacts(tmp_path: Path):
    gp_run = tmp_path / "glass_run"
    gp_run.mkdir()
    write_json(
        gp_run / "run_timing.json",
        {
            "command": "run",
            "backend": "cuda",
            "memory_mode": "resident",
            "total_elapsed_s": 100.0,
            "stages": [{"stage": "resident_calibration_integration", "elapsed_s": 100.0}],
        },
    )
    write_json(
        gp_run / "integration_results.json",
        {
            "weighting": "none",
            "rejection": "winsorized_sigma",
            "frame_weights": {"F1": 1.0, "F2": 1.0, "F3": 0.0},
            "outputs": [
                {
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "frame_count": 193,
                    "master_path": "master.fits",
                }
            ],
        },
    )
    write_json(
        gp_run / "resident_artifacts.json",
        {
            "device": {"name": "Test GPU"},
            "artifacts": [
                {
                    "memory_estimate": {"estimated_peak_gib": 47.3},
                    "resident_io_pipeline": {
                        "fits_read_mode_effective": "native_u16_gpu",
                        "fits_header_spec_cache_frame_count": 3,
                        "fits_header_spec_cache_hit_count": 3,
                        "prefetch_frames": 32,
                        "prefetch_workers": 16,
                        "calibration_fetch_batch_frames": 16,
                        "calibration_fetch_batch_limit_source": "requested",
                    },
                    "resident_master_cache": {
                        "summary": {
                            "cache_hit_count": 1,
                            "cache_miss_count": 0,
                            "cache_scope_counts": {"shared": 1},
                            "set_count": 1,
                            "total_required_bytes": 1234,
                        }
                    },
                    "timing_s": {
                        "light_read_upload_calibrate": 2.5,
                        "resident_registration_warp": 0.4,
                        "resident_integration": 0.2,
                        "output_write": 0.1,
                    },
                }
            ],
        },
    )
    wbpp_result = tmp_path / "wbpp_result.json"
    wbpp_result.write_text(
        "\ufeff"
        + json.dumps(
            {
                "elapsed_s": 1000.0,
                "dataset": "M38_H",
                "reported_wbpp_time": "WeightedBatchPreprocessing: 16:40.00",
                "clean_room_note": "Black-box execution only",
            }
        ),
        encoding="utf-8",
    )
    compare = tmp_path / "compare.json"
    write_json(
        compare,
        {
            "shape_match": True,
            "rms_diff": 0.001,
            "abs_diff_p99": 0.01,
            "timing": {"speedup_vs_reference": 10.0},
            "comparison_region": {"coverage_fraction": 0.96, "compared_pixels": 123},
        },
    )

    summary = summarize_wbpp_speedup(gp_run, wbpp_result, compare_json=compare, min_speedup=5.0)

    assert summary["speedup_vs_wbpp"] == 10.0
    assert summary["meets_min_speedup"] is True
    assert summary["glass"]["backend"] == "cuda_resident_stack"
    assert summary["glass"]["resident_device"] == "Test GPU"
    assert summary["glass"]["resident_estimated_peak_gib"] == 47.3
    assert summary["glass"]["resident_master_cache"]["cache_hit_count"] == 1
    assert summary["glass"]["resident_io"]["fits_read_mode_effective"] == "native_u16_gpu"
    assert summary["glass"]["resident_timing_s"]["light_read_upload_calibrate"] == 2.5
    assert summary["glass"]["weighted_frame_count"] == 2
    assert summary["glass"]["zero_weight_frame_count"] == 1
    assert summary["wbpp_blackbox"]["dataset"] == "M38_H"
    assert summary["comparison"]["coverage_fraction"] == 0.96
    assert summary["comparison"]["compare_speedup_vs_reference"] == 10.0
    assert summary["clean_room"]["status"] == "compliant"


def test_write_speedup_summary_writes_json_and_markdown(tmp_path: Path):
    summary = {
        "glass": {
            "elapsed_s": 10.0,
            "backend": "cuda_resident_stack",
            "memory_mode": "resident",
            "frame_count": 2,
            "weighted_frame_count": 2,
            "zero_weight_frame_count": 0,
            "resident_device": "Test GPU",
            "resident_estimated_peak_gib": 47.3,
            "resident_master_cache": {"cache_hit_count": 1, "cache_miss_count": 0},
            "resident_io": {"fits_read_mode_effective": "native_u16_gpu"},
            "resident_timing_s": {
                "light_read_upload_calibrate": 2.5,
                "resident_registration_warp": 0.4,
                "resident_integration": 0.2,
                "output_write": 0.1,
            },
        },
        "wbpp_blackbox": {"elapsed_s": 20.0, "dataset": "fixture"},
        "speedup_vs_wbpp": 2.0,
        "min_speedup": 1.25,
        "meets_min_speedup": True,
        "comparison": {
            "shape_match": True,
            "rms_diff": 0.0,
            "abs_diff_p99": 0.0,
            "coverage_fraction": 1.0,
            "compared_pixels": 42,
            "compare_speedup_vs_reference": 1.9,
        },
        "clean_room": {"note": "clean-room note"},
    }
    out_json = tmp_path / "speedup.json"
    out_md = tmp_path / "speedup.md"

    write_speedup_summary(out_json, summary, markdown=out_md)

    assert json.loads(out_json.read_text(encoding="utf-8"))["speedup_vs_wbpp"] == 2.0
    markdown = out_md.read_text(encoding="utf-8")
    assert "Speedup: 2.000x" in markdown
    assert "Active weighted frames: 2" in markdown
    assert "Resident peak VRAM estimate: 47.3 GiB" in markdown
    assert "Master cache hits/misses: 1/0" in markdown
    assert "FITS read mode: native_u16_gpu" in markdown
    assert "Light read/upload/calibrate: 2.5 s" in markdown
    assert "compare timing speedup: 1.9" in markdown
    assert "clean-room note" in markdown


def test_speedup_summary_cli_writes_outputs(tmp_path: Path):
    gp_run = tmp_path / "glass_run"
    gp_run.mkdir()
    write_json(gp_run / "run_timing.json", {"total_elapsed_s": 5.0, "command": "run", "memory_mode": "resident"})
    write_json(
        gp_run / "integration_results.json",
        {
            "frame_weights": {"F1": 1.0},
            "outputs": [{"backend": "cuda_resident_stack", "memory_mode": "resident", "frame_count": 1}],
        },
    )
    wbpp_result = tmp_path / "wbpp_result.json"
    write_json(wbpp_result, {"elapsed_s": 20.0, "dataset": "fixture"})
    out_json = tmp_path / "summary.json"
    out_md = tmp_path / "summary.md"

    assert main(
        [
            "speedup-summary",
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp_result),
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-speedup",
            "2.0",
        ]
    ) == 0

    assert json.loads(out_json.read_text(encoding="utf-8"))["speedup_vs_wbpp"] == 4.0
    assert "Speedup: 4.000x" in out_md.read_text(encoding="utf-8")
