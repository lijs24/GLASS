from __future__ import annotations

import json
from pathlib import Path
import struct
import zlib

import numpy as np

from gpwbpp.io.fits_io import read_fits_data
from gpwbpp.io.xisf_io import read_xisf_data
from gpwbpp.report.html_report import write_html_report


def _read_image_data(path: str | Path) -> np.ndarray:
    suffix = Path(path).suffix.lower()
    if suffix == ".xisf":
        return read_xisf_data(path, dtype=np.float32)
    return read_fits_data(path)


def _apply_candidate_transform(
    values: np.ndarray,
    scale: float | None = None,
    offset: float | None = None,
    clip_low: float | None = None,
    clip_high: float | None = None,
) -> tuple[np.ndarray, dict[str, float | bool | None]]:
    transform = {
        "applied": any(value is not None for value in (scale, offset, clip_low, clip_high)),
        "scale": 1.0 if scale is None else float(scale),
        "offset": 0.0 if offset is None else float(offset),
        "clip_low": None if clip_low is None else float(clip_low),
        "clip_high": None if clip_high is None else float(clip_high),
    }
    if not transform["applied"]:
        return values, transform
    out = np.asarray(values, dtype=np.float32) * float(transform["scale"]) + float(transform["offset"])
    if clip_low is not None or clip_high is not None:
        out = np.clip(
            out,
            -np.inf if clip_low is None else float(clip_low),
            np.inf if clip_high is None else float(clip_high),
        )
    return np.asarray(out, dtype=np.float32), transform


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


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _write_png_gray(path: str | Path, image: np.ndarray) -> None:
    img = np.ascontiguousarray(image, dtype=np.uint8)
    if img.ndim != 2:
        raise ValueError("gray PNG image must be 2D")
    height, width = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(height))
    payload = [
        b"\x89PNG\r\n\x1a\n",
        _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)),
        _png_chunk(b"IDAT", zlib.compress(raw, level=6)),
        _png_chunk(b"IEND", b""),
    ]
    Path(path).write_bytes(b"".join(payload))


def _write_png_rgb(path: str | Path, image: np.ndarray) -> None:
    img = np.ascontiguousarray(image, dtype=np.uint8)
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("RGB PNG image must be HxWx3")
    height, width, _ = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(height))
    payload = [
        b"\x89PNG\r\n\x1a\n",
        _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        _png_chunk(b"IDAT", zlib.compress(raw, level=6)),
        _png_chunk(b"IEND", b""),
    ]
    Path(path).write_bytes(b"".join(payload))


def _preview_stride(shape: tuple[int, int], max_size: int) -> int:
    if max_size <= 0:
        raise ValueError("diagnostic max size must be positive")
    height, width = shape
    return max(1, int(np.ceil(max(height, width) / max_size)))


def _gray_preview(values: np.ndarray, max_size: int, low: float = 0.5, high: float = 99.5) -> np.ndarray:
    stride = _preview_stride(values.shape, max_size)
    sample = np.asarray(values[::stride, ::stride], dtype=np.float32)
    finite = sample[np.isfinite(sample)]
    if finite.size == 0:
        return np.zeros(sample.shape, dtype=np.uint8)
    lo, hi = np.percentile(finite, [low, high])
    if not np.isfinite(hi) or hi <= lo:
        hi = lo + 1.0
    scaled = np.clip((sample - lo) / (hi - lo), 0.0, 1.0)
    scaled[~np.isfinite(scaled)] = 0.0
    return np.asarray(np.rint(scaled * 255.0), dtype=np.uint8)


def _signed_diff_preview(diff: np.ndarray, max_size: int) -> np.ndarray:
    stride = _preview_stride(diff.shape, max_size)
    sample = np.asarray(diff[::stride, ::stride], dtype=np.float32)
    finite = sample[np.isfinite(sample)]
    rgb = np.zeros((*sample.shape, 3), dtype=np.uint8)
    if finite.size == 0:
        return rgb
    limit = float(np.percentile(np.abs(finite), 99.5))
    if not np.isfinite(limit) or limit <= 0:
        limit = 1.0
    mag = np.clip(np.abs(sample) / limit, 0.0, 1.0)
    mag[~np.isfinite(mag)] = 0.0
    positive = sample >= 0
    base = np.asarray(np.rint(32.0 * (1.0 - mag)), dtype=np.uint8)
    strong = np.asarray(np.rint(32.0 + 223.0 * mag), dtype=np.uint8)
    rgb[..., 0] = np.where(positive, strong, base)
    rgb[..., 1] = base
    rgb[..., 2] = np.where(positive, base, strong)
    return rgb


def _diff_hotspots(diff: np.ndarray, tile_size: int = 512, limit: int = 16) -> list[dict[str, float | int]]:
    if tile_size <= 0:
        raise ValueError("hotspot tile size must be positive")
    height, width = diff.shape
    hotspots: list[dict[str, float | int]] = []
    for y0 in range(0, height, tile_size):
        y1 = min(height, y0 + tile_size)
        for x0 in range(0, width, tile_size):
            x1 = min(width, x0 + tile_size)
            tile = np.asarray(diff[y0:y1, x0:x1], dtype=np.float64)
            finite = tile[np.isfinite(tile)]
            if finite.size == 0:
                continue
            abs_tile = np.abs(finite)
            hotspots.append(
                {
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "pixels": int(finite.size),
                    "mean_diff": float(np.mean(finite)),
                    "rms_diff": float(np.sqrt(np.mean(finite * finite))),
                    "p99_abs_diff": float(np.percentile(abs_tile, 99)),
                    "max_abs_diff": float(np.max(abs_tile)),
                }
            )
    return sorted(hotspots, key=lambda item: (float(item["p99_abs_diff"]), float(item["rms_diff"])), reverse=True)[
        :limit
    ]


def _write_diagnostic_artifacts(
    diagnostics_dir: str | Path,
    candidate: np.ndarray,
    reference: np.ndarray,
    max_size: int = 1024,
    hotspot_tile_size: int = 512,
) -> dict[str, object]:
    out = Path(diagnostics_dir)
    out.mkdir(parents=True, exist_ok=True)
    diff = np.asarray(candidate, dtype=np.float32) - np.asarray(reference, dtype=np.float32)
    artifacts = {
        "directory": str(out),
        "preview_max_size": int(max_size),
        "hotspot_tile_size": int(hotspot_tile_size),
        "gpwbpp_preview_png": str(out / "gpwbpp_preview.png"),
        "reference_preview_png": str(out / "reference_preview.png"),
        "abs_diff_preview_png": str(out / "abs_diff_preview.png"),
        "signed_diff_preview_png": str(out / "signed_diff_preview.png"),
        "hotspots_json": str(out / "hotspots.json"),
    }
    _write_png_gray(out / "gpwbpp_preview.png", _gray_preview(candidate, max_size))
    _write_png_gray(out / "reference_preview.png", _gray_preview(reference, max_size))
    _write_png_gray(out / "abs_diff_preview.png", _gray_preview(np.abs(diff), max_size, low=0.0, high=99.5))
    _write_png_rgb(out / "signed_diff_preview.png", _signed_diff_preview(diff, max_size))
    hotspots = _diff_hotspots(diff, tile_size=hotspot_tile_size)
    (out / "hotspots.json").write_text(json.dumps(hotspots, indent=2, sort_keys=True), encoding="utf-8")
    artifacts["hotspots"] = hotspots
    return artifacts


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
    gpwbpp_scale: float | None = None,
    gpwbpp_offset: float | None = None,
    clip_low: float | None = None,
    clip_high: float | None = None,
    diagnostics_dir: str | Path | None = None,
    diagnostic_max_size: int = 1024,
    hotspot_tile_size: int = 512,
) -> dict[str, object]:
    gp_raw = _read_image_data(gpwbpp_path)
    gp, transform = _apply_candidate_transform(gp_raw, gpwbpp_scale, gpwbpp_offset, clip_low, clip_high)
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
            "candidate_transform": transform,
        }
    comparison: dict[str, object] = {
        "shape_match": True,
        "gpwbpp_format": Path(gpwbpp_path).suffix.lower().lstrip("."),
        "reference_format": Path(reference_path).suffix.lower().lstrip("."),
        "candidate_transform": transform,
        **_diff_stats(gp, ref),
        "linear_fit_to_reference": _linear_fit_to_reference(gp, ref),
        "robust_linear_fit_to_reference": _robust_linear_fit_to_reference(gp, ref),
        "timing": timing,
    }
    if diagnostics_dir is not None:
        comparison["diagnostics"] = _write_diagnostic_artifacts(
            diagnostics_dir,
            gp,
            ref,
            max_size=diagnostic_max_size,
            hotspot_tile_size=hotspot_tile_size,
        )
    return comparison


def write_compare_report(out_path: str | Path, comparison: dict[str, object]) -> None:
    write_html_report(out_path, manifest={"summary": comparison, "frames": []}, plan=None, title="GPWBPP Compare")
