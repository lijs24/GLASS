from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from glass.cli import main
from glass.report.compare_outliers import build_compare_outlier_audit
from glass.io.json_io import read_json


def _write_fits(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.writeto(path, np.asarray(data, dtype=np.float32), overwrite=True)


def test_compare_outlier_audit_localizes_tail_pixels(tmp_path: Path) -> None:
    reference = np.zeros((8, 8), dtype=np.float32)
    glass = np.zeros((8, 8), dtype=np.float32)
    glass[3, 4] = 0.5
    glass[5, 5] = -0.25
    coverage = np.full((8, 8), 10, dtype=np.float32)
    coverage[5, 5] = 2
    glass_path = tmp_path / "glass.fits"
    reference_path = tmp_path / "reference.fits"
    coverage_path = tmp_path / "coverage.fits"
    _write_fits(glass_path, glass)
    _write_fits(reference_path, reference)
    _write_fits(coverage_path, coverage)

    audit = build_compare_outlier_audit(
        glass_path,
        reference_path,
        glass_coverage_map=coverage_path,
        min_coverage=5,
        ignore_border_px=1,
        target_abs_diff=0.1,
        tile_size=4,
        top_pixels=4,
    )

    assert audit["status"] == "completed"
    assert audit["region"]["compared_shape"] == [6, 6]
    assert audit["region"]["compared_pixels"] == 35
    assert audit["target_exceedance"]["pixels"] == 1
    assert audit["top_pixels"][0]["x"] == 4
    assert audit["top_pixels"][0]["y"] == 3
    assert audit["top_tiles"][0]["tail_pixels"] >= 1


def test_compare_outlier_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    reference = np.zeros((6, 6), dtype=np.float32)
    glass = np.zeros((6, 6), dtype=np.float32)
    glass[2, 3] = 1.0
    glass_path = tmp_path / "glass.fits"
    reference_path = tmp_path / "reference.fits"
    out = tmp_path / "outliers.json"
    markdown = tmp_path / "outliers.md"
    _write_fits(glass_path, glass)
    _write_fits(reference_path, reference)

    assert (
        main(
            [
                "compare-outliers",
                "--glass",
                str(glass_path),
                "--reference",
                str(reference_path),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--tail-percentile",
                "95",
                "--target-abs-diff",
                "0.5",
                "--tile-size",
                "3",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["status"] == "completed"
    assert payload["target_exceedance"]["pixels"] == 1
    assert markdown.exists()
