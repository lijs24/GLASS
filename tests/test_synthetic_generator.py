from __future__ import annotations

from pathlib import Path

from glass.engine.quality import measure_quality_streaming
from glass.metadata.scanner import scan_tree
from glass.synthetic.generator import generate_synthetic_dataset


def test_synthetic_generator_writes_fits_and_truth(tmp_path: Path):
    out = tmp_path / "synthetic"
    truth = generate_synthetic_dataset(out, frames=5, width=32, height=24, filt="H", known_shift=True)
    assert (out / "golden_truth.json").exists()
    assert truth["width"] == 32
    manifest = scan_tree(out)
    assert manifest["summary"]["count"] >= 14
    assert manifest["summary"]["frame_type"]["light"] == 5


def test_synthetic_generator_small_frames_keep_detectable_stars(tmp_path: Path):
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=2, width=16, height=16, filt="H", known_shift=True)
    light_path = sorted((out / "light").glob("*.fits"))[0]

    quality = measure_quality_streaming("tiny", "H", light_path, tile_size=8, scratch_dir=tmp_path)

    assert quality["star_count"] >= 2
