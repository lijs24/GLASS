from __future__ import annotations

from pathlib import Path

from gpwbpp.cli import main
from gpwbpp.synthetic.generator import generate_synthetic_dataset


def test_pipeline_fixture_audit(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (run / "run_state.json").exists()
    assert (run / "integration_results.json").exists()
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
    assert main(["report", "--run", str(run), "--manifest", str(audit / "manifest.json"), "--plan", str(audit / "processing_plan.json"), "--out", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "Frame quality table" in text
    assert "Reference frame" in text


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
