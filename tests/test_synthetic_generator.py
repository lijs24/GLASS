from __future__ import annotations

from pathlib import Path

from gpwbpp.metadata.scanner import scan_tree
from gpwbpp.synthetic.generator import generate_synthetic_dataset


def test_synthetic_generator_writes_fits_and_truth(tmp_path: Path):
    out = tmp_path / "synthetic"
    truth = generate_synthetic_dataset(out, frames=5, width=32, height=24, filt="H", known_shift=True)
    assert (out / "golden_truth.json").exists()
    assert truth["width"] == 32
    manifest = scan_tree(out)
    assert manifest["summary"]["count"] >= 14
    assert manifest["summary"]["frame_type"]["light"] == 5

