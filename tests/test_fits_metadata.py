from __future__ import annotations

from glass.io.fits_fast import SIMPLE_FITS_SPEC_SUMMARY_KEY
from glass.metadata.scanner import scan_tree


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
