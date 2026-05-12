from __future__ import annotations

from pathlib import Path

from gpwbpp.cli import main
from gpwbpp.synthetic.generator import generate_synthetic_dataset


def test_pipeline_fixture_audit(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu"]) == 0
    assert (run / "run_state.json").exists()


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
            ]
        )
        == 0
    )
    assert (run / "calibration_artifacts.json").exists()
    assert len(list((run / "calib_cache" / "masters").glob("*.fits"))) >= 3
    assert len(list((run / "calib_cache" / "calibrated").glob("*.fits"))) == 3
