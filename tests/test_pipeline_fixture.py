from __future__ import annotations

from pathlib import Path

from gpwbpp.cli import main
from gpwbpp.engine.pipeline import _exact_median_scratch, _mean_stack_tile, _normalization_scalar
from gpwbpp.io.fits_io import write_fits_data
from gpwbpp.synthetic.generator import generate_synthetic_dataset


def test_pipeline_fixture_audit(tmp_path: Path):
    import json

    data = tmp_path / "data"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (run / "run_state.json").exists()
    assert (run / "run_timing.json").exists()
    assert (run / "integration_results.json").exists()
    timing = json.loads((run / "run_timing.json").read_text(encoding="utf-8"))
    assert timing["command"] == "audit"
    assert timing["total_elapsed_s"] > 0
    assert {"scan", "plan", "calibration", "quality", "registration", "warp", "local_normalization", "integration"}.issubset(
        {item["stage"] for item in timing["stages"]}
    )
    integration = json.loads((run / "integration_results.json").read_text(encoding="utf-8"))
    assert integration["rejection"] == "none"
    assert all(output["tile_stack_mode"] == "streaming_accumulator" for output in integration["outputs"])
    assert list((run / "integration").glob("master_*.fits"))
    assert main(["resume", "--run", str(run)]) == 0


def test_pipeline_fixture_run_calibration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "calibration",
                "--tile-size",
                "9",
            ]
        )
        == 0
    )
    assert (run / "calibration_artifacts.json").exists()
    assert len(list((run / "calib_cache" / "masters").glob("*.fits"))) >= 3
    assert len(list((run / "calib_cache" / "calibrated").glob("*.fits"))) == 3
    import json

    artifacts = json.loads((run / "calibration_artifacts.json").read_text(encoding="utf-8"))
    assert all(master["streaming"] for master in artifacts["masters"].values())
    assert all(master["tile_size"] == 9 for master in artifacts["masters"].values())


def test_streaming_exact_median_scratch_matches_numpy(tmp_path: Path):
    import numpy as np

    path = tmp_path / "source.fits"
    scratch = tmp_path / "median.bin"
    data = np.array(
        [
            [9.0, 1.0, np.nan, 4.0],
            [2.0, 7.0, 6.0, 3.0],
            [8.0, 5.0, 11.0, 10.0],
        ],
        dtype=np.float32,
    )
    write_fits_data(path, data)

    assert _exact_median_scratch(path, tile_size=2, scratch_path=scratch) == float(np.nanmedian(data))
    assert not scratch.exists()


def test_flat_normalization_scalar_uses_scratch_for_small_images(tmp_path: Path, monkeypatch):
    import numpy as np
    from gpwbpp.engine.pipeline import FitsImageReader

    path = tmp_path / "flat.fits"
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    write_fits_data(path, data)

    def fail_read_full(self, dtype=np.float32):
        raise AssertionError("flat normalization should use scratch median, not read_full")

    monkeypatch.setattr(FitsImageReader, "read_full", fail_read_full)
    norm, method = _normalization_scalar(path, "median", tile_size=3)
    assert norm == float(np.median(data))
    assert method == "median_scratch_memmap"


def test_mean_stack_tile_uses_streaming_accumulator(monkeypatch):
    import numpy as np
    from types import SimpleNamespace

    class Reader:
        def __init__(self, data):
            self.data = np.asarray(data, dtype=np.float32)

        def read_tile(self, y0, y1, x0, x1):
            return self.data[y0:y1, x0:x1]

    tile = SimpleNamespace(y0=0, y1=2, x0=0, x1=2)
    readers = [
        Reader([[1, 2], [3, 4]]),
        Reader([[5, 6], [7, 8]]),
        Reader([[9, 10], [11, 12]]),
    ]
    expected = np.array([[5, 6], [7, 8]], dtype=np.float32)

    def fail_stack(*args, **kwargs):
        raise AssertionError("tile stacking should use an accumulator, not np.stack")

    monkeypatch.setattr(np, "stack", fail_stack)
    assert np.allclose(_mean_stack_tile(readers, tile), expected)


def test_pipeline_fixture_run_calibration_cuda_streaming(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=2, width=20, height=18)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    try:
        rc = main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--until-stage",
                "calibration",
                "--tile-size",
                "7",
            ]
        )
    except SystemExit as exc:
        if "unavailable" in str(exc):
            return
        raise
    assert rc == 0
    import json

    artifacts = json.loads((run / "calibration_artifacts.json").read_text(encoding="utf-8"))
    assert artifacts["calibrated_lights"]
    assert all(item["backend"] == "cuda" for item in artifacts["calibrated_lights"])
    assert all(item["tile_count"] > 1 for item in artifacts["calibrated_lights"])


def test_pipeline_fixture_run_quality_and_report(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=3, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "quality",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "frame_quality.json").exists()
    import json

    quality = json.loads((run / "frame_quality.json").read_text(encoding="utf-8"))
    assert quality["metric_source"] == "streaming_tile_reader"
    assert quality["tile_size"] == 8
    assert all(item["metric_source"] == "streaming_tile_reader" for item in quality["frame_quality"])
    assert not (run / "quality_scratch").exists()
    assert main(["report", "--run", str(run), "--manifest", str(audit / "manifest.json"), "--plan", str(audit / "processing_plan.json"), "--out", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "Frame quality table" in text
    assert "Reference frame" in text
    assert "Runtime summary" in text


def test_pipeline_fixture_run_registration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=4, width=40, height=40, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "registration",
                "--tile-size",
                "10",
            ]
        )
        == 0
    )
    assert (run / "registration_results.json").exists()
    import json

    registration = json.loads((run / "registration_results.json").read_text(encoding="utf-8"))
    assert registration["registration_image_source"] == "streaming_preview"
    assert registration["tile_size"] == 10
    assert all(item["registration_image_source"] == "streaming_preview" for item in registration["registration_results"])
    assert main(["report", "--run", str(run), "--manifest", str(audit / "manifest.json"), "--plan", str(audit / "processing_plan.json"), "--out", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "Registration table" in text
    assert "phase_correlation" in (run / "registration_results.json").read_text(encoding="utf-8")


def test_pipeline_fixture_run_warp(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "warp",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "warp_results.json").exists()
    assert list((run / "registered_cache").glob("registered_*.fits"))
    assert list((run / "coverage_cache").glob("coverage_*.fits"))


def test_pipeline_fixture_run_local_normalization(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=3, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "local_normalization",
                "--local-normalization",
                "on",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "local_norm_results.json").exists()
    assert list((run / "local_norm_cache").glob("local_norm_*.fits"))
    assert (
        main(
            [
                "report",
                "--run",
                str(run),
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(report),
            ]
        )
        == 0
    )
    assert "Local normalization summary" in report.read_text(encoding="utf-8")


def test_pipeline_fixture_run_integration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=4, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "integration",
                "--local-normalization",
                "on",
                "--integration-weighting",
                "simple_snr",
                "--integration-rejection",
                "winsorized_sigma",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "integration_results.json").exists()
    import json

    integration = json.loads((run / "integration_results.json").read_text(encoding="utf-8"))
    assert all(output["tile_stack_mode"] == "stack_for_rejection" for output in integration["outputs"])
    assert list((run / "integration").glob("master_*.fits"))
    assert list((run / "integration").glob("weight_map_*.fits"))
    assert list((run / "integration").glob("coverage_map_*.fits"))
    assert list((run / "integration").glob("low_rejection_*.fits"))
    assert list((run / "integration").glob("high_rejection_*.fits"))
    assert (
        main(
            [
                "report",
                "--run",
                str(run),
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(report),
            ]
        )
        == 0
    )
    assert "Integration summary" in report.read_text(encoding="utf-8")


def test_resume_continues_from_warp_without_repeating_calibration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "warp",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    calibration_artifacts = run / "calibration_artifacts.json"
    before = calibration_artifacts.stat().st_mtime_ns
    assert main(["resume", "--run", str(run)]) == 0
    assert (run / "integration_results.json").exists()
    assert calibration_artifacts.stat().st_mtime_ns == before
