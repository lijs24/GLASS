from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from astropy.io import fits

from gpwbpp.cli import main
from gpwbpp.report.compare_report import compare_fits


def _write(path: Path, value: float) -> None:
    fits.PrimaryHDU(np.ones((4, 4), dtype=np.float32) * value).writeto(path)


def test_compare_fits_records_timing_speedup(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    _write(gp, 1.0)
    _write(ref, 1.5)
    result = compare_fits(gp, ref, gpwbpp_time_seconds=10.0, reference_time_seconds=25.0)
    assert result["shape_match"] is True
    assert result["timing"]["speedup_vs_reference"] == 2.5
    assert result["timing"]["gpwbpp_faster"] is True


def test_compare_cli_writes_timing_json(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    out = tmp_path / "compare.html"
    _write(gp, 2.0)
    _write(ref, 2.0)
    assert (
        main(
            [
                "compare",
                "--gpwbpp",
                str(gp),
                "--reference",
                str(ref),
                "--out",
                str(out),
                "--gpwbpp-time-seconds",
                "12",
                "--reference-time-seconds",
                "36",
                "--reference-label",
                "PixInsight WBPP",
            ]
        )
        == 0
    )
    payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["timing"]["reference_label"] == "PixInsight WBPP"
    assert payload["timing"]["speedup_vs_reference"] == 3.0
