from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.io.fits_io import read_fits_data
from gpwbpp.report.html_report import write_html_report


def compare_fits(
    gpwbpp_path: str | Path,
    reference_path: str | Path,
    gpwbpp_time_seconds: float | None = None,
    reference_time_seconds: float | None = None,
    gpwbpp_label: str = "GPWBPP",
    reference_label: str = "reference",
) -> dict[str, object]:
    gp = read_fits_data(gpwbpp_path)
    ref = read_fits_data(reference_path)
    timing: dict[str, object] = {
        "gpwbpp_label": gpwbpp_label,
        "reference_label": reference_label,
        "gpwbpp_time_seconds": gpwbpp_time_seconds,
        "reference_time_seconds": reference_time_seconds,
    }
    if gpwbpp_time_seconds is not None and reference_time_seconds is not None and gpwbpp_time_seconds > 0:
        timing["speedup_vs_reference"] = float(reference_time_seconds) / float(gpwbpp_time_seconds)
        timing["gpwbpp_faster"] = float(gpwbpp_time_seconds) < float(reference_time_seconds)
    if gp.shape != ref.shape:
        return {
            "shape_match": False,
            "gpwbpp_shape": gp.shape,
            "reference_shape": ref.shape,
            "timing": timing,
        }
    diff = gp - ref
    return {
        "shape_match": True,
        "mean_diff": float(np.mean(diff)),
        "rms_diff": float(np.std(diff)),
        "max_abs_diff": float(np.max(np.abs(diff))),
        "timing": timing,
    }


def write_compare_report(out_path: str | Path, comparison: dict[str, object]) -> None:
    write_html_report(out_path, manifest={"summary": comparison, "frames": []}, plan=None, title="GPWBPP Compare")
