from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.io.fits_io import read_fits_data
from gpwbpp.report.html_report import write_html_report


def compare_fits(gpwbpp_path: str | Path, reference_path: str | Path) -> dict[str, object]:
    gp = read_fits_data(gpwbpp_path)
    ref = read_fits_data(reference_path)
    if gp.shape != ref.shape:
        return {"shape_match": False, "gpwbpp_shape": gp.shape, "reference_shape": ref.shape}
    diff = gp - ref
    return {
        "shape_match": True,
        "mean_diff": float(np.mean(diff)),
        "rms_diff": float(np.std(diff)),
        "max_abs_diff": float(np.max(np.abs(diff))),
    }


def write_compare_report(out_path: str | Path, comparison: dict[str, object]) -> None:
    write_html_report(out_path, manifest={"summary": comparison, "frames": []}, plan=None, title="GPWBPP Compare")

