from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import struct
import zlib

import numpy as np

from glass.io.fits_io import read_fits_data
from glass.io.xisf_io import read_xisf_data


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
        "glass_preview_png": str(out / "glass_preview.png"),
        "reference_preview_png": str(out / "reference_preview.png"),
        "abs_diff_preview_png": str(out / "abs_diff_preview.png"),
        "signed_diff_preview_png": str(out / "signed_diff_preview.png"),
        "hotspots_json": str(out / "hotspots.json"),
    }
    _write_png_gray(out / "glass_preview.png", _gray_preview(candidate, max_size))
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
    glass_path: str | Path,
    reference_path: str | Path,
    glass_time_seconds: float | None = None,
    reference_time_seconds: float | None = None,
    glass_label: str = "GLASS",
    reference_label: str = "reference",
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    clip_low: float | None = None,
    clip_high: float | None = None,
    diagnostics_dir: str | Path | None = None,
    diagnostic_max_size: int = 1024,
    hotspot_tile_size: int = 512,
    ignore_border_px: int = 0,
    glass_coverage_map: str | Path | None = None,
    min_coverage: float | None = None,
) -> dict[str, object]:
    gp_raw = _read_image_data(glass_path)
    gp, transform = _apply_candidate_transform(gp_raw, glass_scale, glass_offset, clip_low, clip_high)
    ref = _read_image_data(reference_path)
    timing: dict[str, object] = {
        "glass_label": glass_label,
        "reference_label": reference_label,
        "glass_time_seconds": glass_time_seconds,
        "reference_time_seconds": reference_time_seconds,
    }
    if glass_time_seconds is not None and reference_time_seconds is not None and glass_time_seconds > 0:
        timing["speedup_vs_reference"] = float(reference_time_seconds) / float(glass_time_seconds)
        timing["glass_faster"] = float(glass_time_seconds) < float(reference_time_seconds)
    if gp.shape != ref.shape:
        return {
            "shape_match": False,
            "glass_shape": gp.shape,
            "reference_shape": ref.shape,
            "timing": timing,
            "candidate_transform": transform,
        }
    border = int(ignore_border_px)
    if border < 0:
        raise ValueError("ignore_border_px must be non-negative")
    if border > 0 and (border * 2 >= gp.shape[0] or border * 2 >= gp.shape[1]):
        raise ValueError("ignore_border_px is too large for the compared image shape")
    gp_region = gp[border : gp.shape[0] - border, border : gp.shape[1] - border] if border else gp
    ref_region = ref[border : ref.shape[0] - border, border : ref.shape[1] - border] if border else ref
    coverage_region = None
    coverage_mask = None
    if glass_coverage_map is not None:
        coverage = _read_image_data(glass_coverage_map)
        if coverage.shape != gp.shape:
            raise ValueError(f"coverage map shape mismatch: {coverage.shape} != {gp.shape}")
        coverage_region = (
            coverage[border : coverage.shape[0] - border, border : coverage.shape[1] - border]
            if border
            else coverage
        )
        threshold = 1.0 if min_coverage is None else float(min_coverage)
        coverage_mask = np.asarray(coverage_region, dtype=np.float32) >= np.float32(threshold)
        gp_region_for_stats = np.where(coverage_mask, gp_region, np.nan)
        ref_region_for_stats = np.where(coverage_mask, ref_region, np.nan)
    else:
        gp_region_for_stats = gp_region
        ref_region_for_stats = ref_region
    stats = _diff_stats(gp_region_for_stats, ref_region_for_stats)
    compared_pixels = int(
        np.count_nonzero(np.isfinite(gp_region_for_stats) & np.isfinite(ref_region_for_stats))
    )
    comparison_region = {
        "ignore_border_px": border,
        "full_shape": [int(gp.shape[0]), int(gp.shape[1])],
        "compared_shape": [int(gp_region.shape[0]), int(gp_region.shape[1])],
        "compared_pixels": compared_pixels,
    }
    if coverage_region is not None:
        comparison_region.update(
            {
                "glass_coverage_map": str(glass_coverage_map),
                "min_coverage": 1.0 if min_coverage is None else float(min_coverage),
                "coverage_valid_pixels": int(np.count_nonzero(coverage_mask)),
                "coverage_fraction": float(np.count_nonzero(coverage_mask) / coverage_mask.size),
                "coverage_min": float(np.nanmin(coverage_region)),
                "coverage_p1": float(np.nanpercentile(coverage_region, 1)),
                "coverage_median": float(np.nanmedian(coverage_region)),
                "coverage_max": float(np.nanmax(coverage_region)),
            }
        )
    comparison: dict[str, object] = {
        "shape_match": True,
        "glass_format": Path(glass_path).suffix.lower().lstrip("."),
        "reference_format": Path(reference_path).suffix.lower().lstrip("."),
        "candidate_transform": transform,
        "comparison_region": comparison_region,
        **stats,
        "linear_fit_to_reference": _linear_fit_to_reference(gp_region_for_stats, ref_region_for_stats),
        "robust_linear_fit_to_reference": _robust_linear_fit_to_reference(
            gp_region_for_stats, ref_region_for_stats
        ),
        "timing": timing,
    }
    if border or glass_coverage_map is not None:
        comparison["full_frame_stats"] = _diff_stats(gp, ref)
    if diagnostics_dir is not None:
        comparison["diagnostics"] = _write_diagnostic_artifacts(
            diagnostics_dir,
            gp,
            ref,
            max_size=diagnostic_max_size,
            hotspot_tile_size=hotspot_tile_size,
        )
    return comparison


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    if isinstance(value, (list, tuple)):
        return ", ".join(_format_value(item) for item in value)
    return str(value)


def _summary_rows(comparison: dict[str, object]) -> list[tuple[str, object]]:
    timing = comparison.get("timing", {})
    region = comparison.get("comparison_region", {})
    rows: list[tuple[str, object]] = [
        ("shape_match", comparison.get("shape_match")),
        ("glass_format", comparison.get("glass_format")),
        ("reference_format", comparison.get("reference_format")),
        ("ignore_border_px", region.get("ignore_border_px") if isinstance(region, dict) else None),
        ("compared_shape", region.get("compared_shape") if isinstance(region, dict) else None),
        ("mean_diff", comparison.get("mean_diff")),
        ("rms_diff", comparison.get("rms_diff")),
        ("abs_diff_p50", comparison.get("abs_diff_p50")),
        ("abs_diff_p90", comparison.get("abs_diff_p90")),
        ("abs_diff_p99", comparison.get("abs_diff_p99")),
        ("abs_diff_p999", comparison.get("abs_diff_p999")),
        ("max_abs_diff", comparison.get("max_abs_diff")),
    ]
    if isinstance(timing, dict):
        rows.extend(
            [
                ("glass_time_seconds", timing.get("glass_time_seconds")),
                ("reference_time_seconds", timing.get("reference_time_seconds")),
                ("speedup_vs_reference", timing.get("speedup_vs_reference")),
                ("glass_faster", timing.get("glass_faster")),
            ]
        )
    return rows


def _rows_table(rows: list[tuple[str, object]]) -> str:
    body = []
    for key, value in rows:
        body.append(
            "<tr>"
            f"<th>{escape(str(key))}</th>"
            f"<td>{escape(_format_value(value))}</td>"
            "</tr>"
        )
    return f"<table><tbody>{''.join(body)}</tbody></table>"


def _path_href(path: str | Path, report_dir: Path) -> str:
    target = Path(path)
    try:
        href = os.path.relpath(target, report_dir)
    except ValueError:
        href = str(target)
    return href.replace("\\", "/")


def _diagnostic_images(comparison: dict[str, object], report_dir: Path) -> str:
    diagnostics = comparison.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return "<p>No diagnostic images were generated.</p>"
    keys = [
        ("glass_preview_png", "GLASS preview"),
        ("reference_preview_png", "Reference preview"),
        ("abs_diff_preview_png", "Absolute difference"),
        ("signed_diff_preview_png", "Signed difference"),
    ]
    cards = []
    for key, label in keys:
        path = diagnostics.get(key)
        if not path:
            continue
        href = _path_href(str(path), report_dir)
        cards.append(
            "<figure>"
            f'<a href="{escape(href)}"><img src="{escape(href)}" alt="{escape(label)}"></a>'
            f"<figcaption>{escape(label)}</figcaption>"
            "</figure>"
        )
    if not cards:
        return "<p>No diagnostic images were generated.</p>"
    return f"<div class=\"diagnostic-grid\">{''.join(cards)}</div>"


def _hotspot_table(comparison: dict[str, object]) -> str:
    diagnostics = comparison.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return "<p>No hotspot diagnostics.</p>"
    hotspots = diagnostics.get("hotspots")
    if not isinstance(hotspots, list) or not hotspots:
        return "<p>No hotspot diagnostics.</p>"
    keys = ["x0", "x1", "y0", "y1", "pixels", "p99_abs_diff", "rms_diff", "mean_diff", "max_abs_diff"]
    head = "".join(f"<th>{escape(key)}</th>" for key in keys)
    rows = []
    for item in hotspots[:16]:
        if not isinstance(item, dict):
            continue
        cells = "".join(f"<td>{escape(_format_value(item.get(key)))}</td>" for key in keys)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def write_compare_report(out_path: str | Path, comparison: dict[str, object]) -> None:
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    report_dir = target.parent
    transform = comparison.get("candidate_transform", {})
    full_frame_stats = comparison.get("full_frame_stats")
    linear_fit = comparison.get("linear_fit_to_reference", {})
    robust_fit = comparison.get("robust_linear_fit_to_reference", {})
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GLASS Compare</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.35rem 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code, pre {{ background: #f6f8fa; padding: 0.1rem 0.25rem; }}
    pre {{ overflow: auto; padding: 0.75rem; }}
    .diagnostic-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }}
    figure {{ margin: 0; border: 1px solid #d0d7de; padding: 0.5rem; }}
    img {{ display: block; max-width: 100%; height: auto; background: #111; }}
    figcaption {{ margin-top: 0.35rem; font-size: 0.9rem; color: #57606a; }}
  </style>
</head>
<body>
  <h1>GLASS Compare</h1>
  <h2>Summary</h2>
  {_rows_table(_summary_rows(comparison))}
  <h2>Candidate Transform</h2>
  <pre>{escape(json.dumps(transform, indent=2, sort_keys=True))}</pre>
  <h2>Diagnostic Images</h2>
  {_diagnostic_images(comparison, report_dir)}
  <h2>Residual Hotspots</h2>
  {_hotspot_table(comparison)}
  <h2>Linear Fit To Reference</h2>
  <pre>{escape(json.dumps(linear_fit, indent=2, sort_keys=True))}</pre>
  <h2>Robust Linear Fit To Reference</h2>
  <pre>{escape(json.dumps(robust_fit, indent=2, sort_keys=True))}</pre>
  <h2>Full Frame Stats</h2>
  <pre>{escape(json.dumps(full_frame_stats, indent=2, sort_keys=True))}</pre>
  <h2>Clean-room Note</h2>
  <p>This report compares GLASS output to a user-provided black-box reference artifact.
  It does not use or claim access to PixInsight/WBPP implementation source.</p>
</body>
</html>
"""
    target.write_text(html, encoding="utf-8")
