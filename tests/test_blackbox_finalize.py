from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from astropy.io import fits

from gpwbpp.cli import main


def _write(path: Path, value: float) -> None:
    fits.PrimaryHDU(np.ones((4, 4), dtype=np.float32) * value).writeto(path)


def test_blackbox_finalize_generates_compare_summary(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    timing = tmp_path / "timing_template.json"
    out = tmp_path / "final"
    _write(gp, 1.0)
    _write(ref, 1.0)
    timing.write_text(
        json.dumps(
            {
                "gpwbpp_time_seconds": 10.0,
                "reference_time_seconds": 30.0,
                "gpwbpp_master_paths": [str(gp)],
                "reference_master_paths": [str(ref)],
                "reference_label": "PixInsight WBPP",
            }
        ),
        encoding="utf-8",
    )
    assert main(["blackbox-finalize", "--timing", str(timing), "--out", str(out)]) == 0
    summary = json.loads((out / "blackbox_finalize_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["speedup_vs_reference"] == 3.0
    assert summary["all_gpwbpp_faster"] is True
    assert Path(summary["comparisons"][0]["html"]).exists()


def test_blackbox_finalize_reports_blocker(tmp_path: Path):
    timing = tmp_path / "timing_template.json"
    out = tmp_path / "final"
    timing.write_text(json.dumps({"gpwbpp_master_paths": [], "reference_master_paths": []}), encoding="utf-8")
    assert main(["blackbox-finalize", "--timing", str(timing), "--out", str(out)]) == 2
    summary = json.loads((out / "blackbox_finalize_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "blocked"
    assert summary["errors"]
