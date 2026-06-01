from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.compare_tile_pack import build_compare_tile_pack


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def _write_audit(tmp_path: Path, *, glass: Path, reference: Path, coverage: Path | None = None) -> Path:
    audit_path = tmp_path / "outliers.json"
    write_json(
        audit_path,
        {
            "schema_version": 1,
            "audit_type": "compare_outlier_audit",
            "status": "completed",
            "glass": str(glass),
            "reference": str(reference),
            "coverage_map": None if coverage is None else str(coverage),
            "candidate_transform": {"applied": False, "scale": 1.0, "offset": 0.0},
            "top_tiles": [
                {
                    "x0": 1,
                    "y0": 1,
                    "x1": 4,
                    "y1": 4,
                    "tail_pixels": 3,
                    "tail_fraction_of_valid": 0.3,
                    "tail_abs_max": 2.0,
                    "tail_signed_mean": -0.5,
                }
            ],
        },
    )
    return audit_path


def test_compare_tile_pack_exports_cutouts_and_previews(tmp_path: Path) -> None:
    reference = np.zeros((6, 6), dtype=np.float32)
    glass = np.zeros((6, 6), dtype=np.float32)
    glass[2, 3] = -2.0
    coverage = np.full((6, 6), 9, dtype=np.float32)
    glass_path = tmp_path / "glass.fits"
    reference_path = tmp_path / "reference.fits"
    coverage_path = tmp_path / "coverage.fits"
    _write_fits(glass_path, glass)
    _write_fits(reference_path, reference)
    _write_fits(coverage_path, coverage)
    audit_path = _write_audit(tmp_path, glass=glass_path, reference=reference_path, coverage=coverage_path)

    manifest = build_compare_tile_pack(audit_path, tmp_path / "tiles", max_tiles=1, pad_px=1)

    assert manifest["tile_count"] == 1
    tile = manifest["tiles"][0]
    assert tile["extent"] == {"x0": 0, "y0": 0, "x1": 5, "y1": 5, "pad_px": 1}
    assert Path(tile["paths"]["signed_diff_fits"]).exists()
    assert Path(tile["paths"]["signed_diff_png"]).exists()
    signed = fits.getdata(tile["paths"]["signed_diff_fits"])
    assert signed[2, 3] == np.float32(-2.0)


def test_compare_tile_pack_cli_writes_manifest(tmp_path: Path) -> None:
    glass_path = tmp_path / "glass.fits"
    reference_path = tmp_path / "reference.fits"
    _write_fits(glass_path, np.ones((5, 5), dtype=np.float32))
    _write_fits(reference_path, np.zeros((5, 5), dtype=np.float32))
    audit_path = _write_audit(tmp_path, glass=glass_path, reference=reference_path)
    out_dir = tmp_path / "tiles_cli"

    assert (
        main(
            [
                "compare-tile-pack",
                "--audit",
                str(audit_path),
                "--out-dir",
                str(out_dir),
                "--max-tiles",
                "1",
                "--no-png",
            ]
        )
        == 0
    )

    manifest = read_json(out_dir / "tile_pack_manifest.json")
    assert manifest["tile_count"] == 1
    assert "signed_diff_png" not in manifest["tiles"][0]["paths"]
