from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.io.fits_io import read_fits_data
from gpwbpp.io.xisf_io import read_xisf_data
from gpwbpp.report.html_report import write_html_report


def _read_image_data(path: str | Path) -> np.ndarray:
    suffix = Path(path).suffix.lower()
    if suffix == ".xisf":
        return read_xisf_data(path, dtype=np.float32)
    return read_fits_data(path)


def _diff_stats(candidate: np.ndarray, reference: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(candidate) & np.isfinite(reference)
    if not np.any(mask):
        return {
            "mean_diff": float("nan"),
            "rms_diff": float("nan"),
            "max_abs_diff": float("nan"),
            "relative_rms_diff": float("nan"),
        }
    diff = np.asarray(candidate[mask], dtype=np.float64) - np.asarray(reference[mask], dtype=np.float64)
    reference_rms = float(np.sqrt(np.mean(np.asarray(reference[mask], dtype=np.float64) ** 2)))
    rms = float(np.sqrt(np.mean(diff * diff)))
    return {
        "mean_diff": float(np.mean(diff)),
        "rms_diff": rms,
        "max_abs_diff": float(np.max(np.abs(diff))),
        "abs_diff_p50": float(np.percentile(np.abs(diff), 50)),
        "abs_diff_p90": float(np.percentile(np.abs(diff), 90)),
        "abs_diff_p99": float(np.percentile(np.abs(diff), 99)),
        "abs_diff_p999": float(np.percentile(np.abs(diff), 99.9)),
        "relative_rms_diff": float(rms / reference_rms) if reference_rms > 0 else 0.0,
    }


def _linear_fit_to_reference(candidate: np.ndarray, reference: np.ndarray) -> dict[str, object]:
    mask = np.isfinite(candidate) & np.isfinite(reference)
    if np.count_nonzero(mask) < 2:
        return {"available": False}
    x = np.asarray(candidate[mask], dtype=np.float64)
    y = np.asarray(reference[mask], dtype=np.float64)
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    var = float(np.mean((x - x_mean) ** 2))
    if var == 0.0:
        return {"available": False}
    scale = float(np.mean((x - x_mean) * (y - y_mean)) / var)
    offset = float(y_mean - scale * x_mean)
    fitted = np.asarray(candidate, dtype=np.float64) * scale + offset
    stats = _diff_stats(fitted, np.asarray(reference, dtype=np.float64))
    return {"available": True, "scale": scale, "offset": offset, "stats": stats}


def _robust_linear_fit_to_reference(
    candidate: np.ndarray,
    reference: np.ndarray,
    low_percentile: float = 0.5,
    high_percentile: float = 99.5,
) -> dict[str, object]:
    mask = np.isfinite(candidate) & np.isfinite(reference)
    if np.count_nonzero(mask) < 2:
        return {"available": False}
    x_all = np.asarray(candidate[mask], dtype=np.float64)
    y_all = np.asarray(reference[mask], dtype=np.float64)
    x_low, x_high = np.percentile(x_all, [low_percentile, high_percentile])
    y_low, y_high = np.percentile(y_all, [low_percentile, high_percentile])
    robust_mask = mask & (candidate >= x_low) & (candidate <= x_high) & (reference >= y_low) & (reference <= y_high)
    if np.count_nonzero(robust_mask) < 2:
        return {"available": False}
    x = np.asarray(candidate[robust_mask], dtype=np.float64)
    y = np.asarray(reference[robust_mask], dtype=np.float64)
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    var = float(np.mean((x - x_mean) ** 2))
    if var == 0.0:
        return {"available": False}
    scale = float(np.mean((x - x_mean) * (y - y_mean)) / var)
    offset = float(y_mean - scale * x_mean)
    fitted = np.asarray(candidate, dtype=np.float64) * scale + offset
    fitted_robust = np.asarray(candidate[robust_mask], dtype=np.float64) * scale + offset
    return {
        "available": True,
        "scale": scale,
        "offset": offset,
        "fit_pixels": int(np.count_nonzero(robust_mask)),
        "fit_fraction": float(np.count_nonzero(robust_mask) / np.count_nonzero(mask)),
        "stats_all_pixels": _diff_stats(fitted, np.asarray(reference, dtype=np.float64)),
        "stats_fit_pixels": _diff_stats(fitted_robust, np.asarray(reference[robust_mask], dtype=np.float64)),
    }


def compare_fits(
    gpwbpp_path: str | Path,
    reference_path: str | Path,
    gpwbpp_time_seconds: float | None = None,
    reference_time_seconds: float | None = None,
    gpwbpp_label: str = "GPWBPP",
    reference_label: str = "reference",
) -> dict[str, object]:
    gp = _read_image_data(gpwbpp_path)
    ref = _read_image_data(reference_path)
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
    return {
        "shape_match": True,
        "gpwbpp_format": Path(gpwbpp_path).suffix.lower().lstrip("."),
        "reference_format": Path(reference_path).suffix.lower().lstrip("."),
        **_diff_stats(gp, ref),
        "linear_fit_to_reference": _linear_fit_to_reference(gp, ref),
        "robust_linear_fit_to_reference": _robust_linear_fit_to_reference(gp, ref),
        "timing": timing,
    }


def write_compare_report(out_path: str | Path, comparison: dict[str, object]) -> None:
    write_html_report(out_path, manifest={"summary": comparison, "frames": []}, plan=None, title="GPWBPP Compare")
