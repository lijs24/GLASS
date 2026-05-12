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

