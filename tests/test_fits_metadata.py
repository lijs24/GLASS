from __future__ import annotations

from pathlib import Path

from glass.io.fits_fast import SIMPLE_FITS_SPEC_SUMMARY_KEY
from glass.metadata.scanner import scan_tree
from glass.synthetic.generator import generate_synthetic_dataset


def test_scan_fits_metadata_without_pixel_load(small_fits_dataset):
    manifest = scan_tree(small_fits_dataset)
    assert manifest["summary"]["count"] == 4
    frame_types = manifest["summary"]["frame_type"]
    assert frame_types["bias"] == 1
    assert frame_types["dark"] == 1
    assert frame_types["flat"] == 1
    assert frame_types["light"] == 1
    light = [f for f in manifest["frames"] if f["frame_type"] == "light"][0]
    assert light["width"] == 20
    assert light["height"] == 16
    assert light["filter"] == "H"
    assert light["header_summary"]["PIERSIDE"] == "West"
    assert light["header_summary"]["OBJCTROT"] == 92.0
    simple_spec = light["header_summary"][SIMPLE_FITS_SPEC_SUMMARY_KEY]
    assert simple_spec["schema_version"] == 1
    assert simple_spec["width"] == 20
    assert simple_spec["height"] == 16
    assert simple_spec["data_offset"] > 0


def test_scan_tree_skips_source_dq_sidecar_directory(tmp_path):
    dataset = tmp_path / "synthetic_source_dq"
    generate_synthetic_dataset(dataset, frames=4, width=32, height=24, filt="H", source_dq_sidecars=True)

    manifest = scan_tree(dataset)

    assert manifest["summary"]["count"] == 13
    assert manifest["summary"]["skipped_count"] == 1
    assert len(manifest["skipped"]) == 1
    skipped = manifest["skipped"][0]
    assert skipped["reason"] == "source_dq_sidecar_directory"
    assert skipped["path"].endswith("source_dq\\light_000_dq.fits") or skipped["path"].endswith(
        "source_dq/light_000_dq.fits"
    )
    assert "unknown" not in manifest["summary"]["frame_type"]
    assert not any("source_dq" in {part.lower() for part in Path(frame["path"]).parent.parts} for frame in manifest["frames"])
