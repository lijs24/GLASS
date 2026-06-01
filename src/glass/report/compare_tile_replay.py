from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import numpy as np

from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.report.compare_tile_attribution import _float_or_none, _stats, _warning_values

_CACHE_DIR_RE = re.compile(r"--resident-master-cache-dir\s+(?P<path>\S+)")
_WARP_INTERPOLATION_RE = re.compile(r"--resident-warp-interpolation\s+(?P<name>\S+)")
_REPLAY_INTERPOLATIONS = {"bilinear", "lanczos3"}


def _load_json_if_exists(path: Path) -> Any:
    return read_json(path) if path.exists() else None


def _discover_master_cache(run_dir: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit is not None:
        path = Path(explicit)
        return path if path.exists() else None
    command_path = run_dir / "run_command.txt"
    if not command_path.exists():
        return None
    match = _CACHE_DIR_RE.search(command_path.read_text(encoding="utf-8"))
    if not match:
        return None
    path = Path(match.group("path"))
    return path if path.exists() else None


def _discover_run_command_value(run_dir: Path, pattern: re.Pattern[str]) -> str | None:
    command_path = run_dir / "run_command.txt"
    if not command_path.exists():
        return None
    match = pattern.search(command_path.read_text(encoding="utf-8"))
    return None if not match else str(match.group(1))


def _load_master_set(cache_dir: Path | None) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    if cache_dir is None:
        return None, None, None, {"available": False, "reason": "master cache not found"}
    stats_paths = sorted(cache_dir.glob("*_master_stats.json"))
    if not stats_paths:
        return None, None, None, {"available": False, "cache_dir": str(cache_dir), "reason": "master stats not found"}
    stats_path = stats_paths[0]
    stem = stats_path.name[: -len("_master_stats.json")]
    bias_path = cache_dir / f"{stem}_master_bias.npy"
    dark_path = cache_dir / f"{stem}_master_dark.npy"
    flat_path = cache_dir / f"{stem}_master_flat.npy"
    stats = read_json(stats_path)
    stats = {**stats, "available": True, "cache_dir": str(cache_dir), "stats_path": str(stats_path)}
    bias = np.load(bias_path, mmap_mode="r") if bias_path.exists() else None
    dark = np.load(dark_path, mmap_mode="r") if dark_path.exists() else None
    flat = np.load(flat_path, mmap_mode="r") if flat_path.exists() else None
    stats["paths"] = {
        "bias": None if bias is None else str(bias_path),
        "dark": None if dark is None else str(dark_path),
        "flat": None if flat is None else str(flat_path),
    }
    return bias, dark, flat, stats


def _frames_by_id(run_dir: Path) -> dict[str, dict[str, Any]]:
    accounting = read_json(run_dir / "frame_accounting.json")
    rows = accounting.get("frames")
    if not isinstance(rows, list):
        return {}
    return {str(row.get("frame_id")): row for row in rows if isinstance(row, dict) and row.get("frame_id")}


def _registration_by_id(run_dir: Path) -> dict[str, dict[str, Any]]:
    registration = read_json(run_dir / "registration_results.json")
    rows = registration.get("results")
    if not isinstance(rows, list):
        return {}
    return {str(row.get("frame_id")): row for row in rows if isinstance(row, dict) and row.get("frame_id")}


def _plan_frames_by_id(run_dir: Path) -> dict[str, dict[str, Any]]:
    plan = _load_json_if_exists(run_dir / "processing_plan.json") or {}
    rows = plan.get("frames")
    if not isinstance(rows, list):
        return {}
    return {str(row.get("id")): row for row in rows if isinstance(row, dict) and row.get("id")}


def _integration_output(run_dir: Path, filter_name: str | None = None) -> dict[str, Any]:
    payload = read_json(run_dir / "integration_results.json")
    outputs = payload.get("outputs")
    if not isinstance(outputs, list):
        return {}
    if filter_name:
        for output in outputs:
            if isinstance(output, dict) and output.get("filter") == filter_name:
                return output
    return outputs[0] if outputs and isinstance(outputs[0], dict) else {}


def _resident_artifact(run_dir: Path, filter_name: str | None = None) -> dict[str, Any]:
    payload = _load_json_if_exists(run_dir / "resident_artifacts.json") or {}
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return {}
    if filter_name:
        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("filter") == filter_name:
                return artifact
    return artifacts[0] if artifacts and isinstance(artifacts[0], dict) else {}


def _calibration_policy(run_dir: Path, master_stats: dict[str, Any]) -> dict[str, Any]:
    resident = _load_json_if_exists(run_dir / "resident_artifacts.json") or {}
    policy = resident.get("policy")
    if not isinstance(policy, dict):
        plan = _load_json_if_exists(run_dir / "processing_plan.json") or {}
        calibration_plan = plan.get("calibration_plan") if isinstance(plan.get("calibration_plan"), dict) else {}
        policy = calibration_plan.get("calibration_policy") if isinstance(calibration_plan.get("calibration_policy"), dict) else {}
    return {
        "dark_scaling_enabled": bool(policy.get("dark_scaling_enabled", True)),
        "flat_floor": float(policy.get("flat_floor", 1.0e-6)),
        "master_dark_includes_bias": bool(policy.get("master_dark_includes_bias", master_stats.get("master_dark_includes_bias", True))),
        "pedestal": float(policy.get("pedestal", 0.0)),
        "dark_exposure_s": _float_or_none(master_stats.get("dark_exposure_s")),
    }


def _select_frames(
    frames: dict[str, dict[str, Any]],
    *,
    strategy: str,
    max_frames: int,
) -> list[dict[str, Any]]:
    rows = [row for row in frames.values() if _float_or_none(row.get("integration_weight")) not in (None, 0.0)]
    if strategy == "downweighted":
        rows = [
            row
            for row in rows
            if _warning_values(row.get("warnings") if isinstance(row.get("warnings"), list) else []).get(
                "triangle_agreement_status"
            )
            == "downweighted"
        ]
    if strategy in {"lowest_weight", "downweighted"}:
        rows.sort(key=lambda row: (_float_or_none(row.get("integration_weight")) or 0.0, str(row.get("frame_id"))))
    elif strategy == "frame_id":
        rows.sort(key=lambda row: str(row.get("frame_id")))
    else:
        raise ValueError(f"unsupported frame selection strategy: {strategy}")
    if max_frames > 0:
        rows = rows[: int(max_frames)]
    return rows


def _source_grid(
    extent: dict[str, Any],
    matrix: list[list[float]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    transform = np.asarray(matrix, dtype=np.float64)
    if transform.shape != (3, 3):
        raise ValueError(f"registration matrix must be 3x3, got {transform.shape}")
    inverse = np.linalg.inv(transform)
    ys, xs = np.mgrid[int(extent["y0"]) : int(extent["y1"]), int(extent["x0"]) : int(extent["x1"])].astype(np.float64)
    denom = inverse[2, 0] * xs + inverse[2, 1] * ys + inverse[2, 2]
    valid_denominator = np.abs(denom) > 1.0e-12
    src_x = np.divide(
        inverse[0, 0] * xs + inverse[0, 1] * ys + inverse[0, 2],
        denom,
        out=np.full_like(xs, np.nan),
        where=valid_denominator,
    )
    src_y = np.divide(
        inverse[1, 0] * xs + inverse[1, 1] * ys + inverse[1, 2],
        denom,
        out=np.full_like(ys, np.nan),
        where=valid_denominator,
    )
    return src_x, src_y, valid_denominator


def _calibrate_source_tile(
    raw: np.ndarray,
    *,
    x0: int,
    y0: int,
    bias: np.ndarray | None,
    dark: np.ndarray | None,
    flat: np.ndarray | None,
    light_exposure_s: float | None,
    policy: dict[str, Any],
) -> np.ndarray:
    out = np.asarray(raw, dtype=np.float32).copy()
    height, width = out.shape
    if dark is not None:
        scale = 1.0
        dark_exposure = _float_or_none(policy.get("dark_exposure_s"))
        if policy.get("dark_scaling_enabled") and light_exposure_s not in (None, 0.0) and dark_exposure not in (None, 0.0):
            scale = float(light_exposure_s) / float(dark_exposure)
        out -= np.asarray(dark[y0 : y0 + height, x0 : x0 + width], dtype=np.float32) * np.float32(scale)
        if not policy.get("master_dark_includes_bias", True) and bias is not None:
            out -= np.asarray(bias[y0 : y0 + height, x0 : x0 + width], dtype=np.float32)
    elif bias is not None:
        out -= np.asarray(bias[y0 : y0 + height, x0 : x0 + width], dtype=np.float32)
    if flat is not None:
        flat_tile = np.maximum(
            np.asarray(flat[y0 : y0 + height, x0 : x0 + width], dtype=np.float32),
            np.float32(policy.get("flat_floor", 1.0e-6)),
        )
        out /= flat_tile
    pedestal = float(policy.get("pedestal", 0.0))
    if pedestal:
        out += np.float32(pedestal)
    return out


def _sample_bilinear_from_tile(
    source: np.ndarray,
    src_x: np.ndarray,
    src_y: np.ndarray,
    valid: np.ndarray,
    read_x0: int,
    read_y0: int,
) -> np.ndarray:
    out = np.full(src_x.shape, np.nan, dtype=np.float32)
    if not np.any(valid):
        return out
    vx = src_x[valid]
    vy = src_y[valid]
    x0 = np.floor(vx).astype(np.int64)
    y0 = np.floor(vy).astype(np.int64)
    x1 = np.minimum(x0 + 1, read_x0 + source.shape[1] - 1)
    y1 = np.minimum(y0 + 1, read_y0 + source.shape[0] - 1)
    tx = (vx - x0).astype(np.float32)
    ty = (vy - y0).astype(np.float32)
    lx0 = x0 - int(read_x0)
    lx1 = x1 - int(read_x0)
    ly0 = y0 - int(read_y0)
    ly1 = y1 - int(read_y0)
    top = source[ly0, lx0] * (1.0 - tx) + source[ly0, lx1] * tx
    bottom = source[ly1, lx0] * (1.0 - tx) + source[ly1, lx1] * tx
    out[valid] = np.asarray(top * (1.0 - ty) + bottom * ty, dtype=np.float32)
    return out


def _sinc_array(values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    out = np.ones(x.shape, dtype=np.float64)
    mask = np.abs(x) >= 1.0e-8
    pix = np.pi * x[mask]
    out[mask] = np.sin(pix) / pix
    return out


def _lanczos3_weight_array(values: np.ndarray) -> np.ndarray:
    x = np.abs(np.asarray(values, dtype=np.float64))
    out = _sinc_array(x) * _sinc_array(x / 3.0)
    out[x >= 3.0] = 0.0
    return out


def _sample_lanczos3_from_tile(
    source: np.ndarray,
    src_x: np.ndarray,
    src_y: np.ndarray,
    valid: np.ndarray,
    read_x0: int,
    read_y0: int,
) -> np.ndarray:
    out = np.full(src_x.shape, np.nan, dtype=np.float32)
    if not np.any(valid):
        return out
    vx = src_x[valid]
    vy = src_y[valid]
    base_x = np.floor(vx).astype(np.int64)
    base_y = np.floor(vy).astype(np.int64)
    weighted_sum = np.zeros(vx.shape, dtype=np.float64)
    weight_sum = np.zeros(vx.shape, dtype=np.float64)
    for oy in range(-2, 4):
        sy = base_y + oy
        wy = _lanczos3_weight_array(vy - sy)
        ly = sy - int(read_y0)
        for ox in range(-2, 4):
            sx = base_x + ox
            wx = _lanczos3_weight_array(vx - sx)
            weights = wx * wy
            lx = sx - int(read_x0)
            weighted_sum += np.asarray(source[ly, lx], dtype=np.float64) * weights
            weight_sum += weights
    sampled = np.divide(
        weighted_sum,
        weight_sum,
        out=np.zeros_like(weighted_sum),
        where=np.abs(weight_sum) > 1.0e-12,
    )
    out[valid] = np.asarray(sampled, dtype=np.float32)
    return out


def _interpolation_radius(interpolation: str) -> int:
    if interpolation == "bilinear":
        return 1
    if interpolation == "lanczos3":
        return 3
    raise ValueError(f"unsupported replay interpolation: {interpolation}")


def _valid_for_interpolation(
    src_x: np.ndarray,
    src_y: np.ndarray,
    *,
    width: int,
    height: int,
    interpolation: str,
) -> np.ndarray:
    if interpolation == "bilinear":
        return (src_x >= 0.0) & (src_x <= float(width - 1)) & (src_y >= 0.0) & (src_y <= float(height - 1))
    radius = _interpolation_radius(interpolation)
    return (
        (src_x >= float(radius - 1))
        & (src_x < float(width - radius))
        & (src_y >= float(radius - 1))
        & (src_y < float(height - radius))
    )


def _replay_frame_tile(
    frame: dict[str, Any],
    registration: dict[str, Any],
    plan_frame: dict[str, Any] | None,
    extent: dict[str, Any],
    *,
    bias: np.ndarray | None,
    dark: np.ndarray | None,
    flat: np.ndarray | None,
    policy: dict[str, Any],
    interpolation: str,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if interpolation not in _REPLAY_INTERPOLATIONS:
        raise ValueError(f"unsupported replay interpolation: {interpolation}")
    path = frame.get("input_path")
    if not path:
        raise ValueError(f"frame has no input_path: {frame.get('frame_id')}")
    matrix = registration.get("matrix")
    if not isinstance(matrix, list):
        raise ValueError(f"frame has no registration matrix: {frame.get('frame_id')}")
    with FitsImageReader(path) as reader:
        height, width = reader.shape
        src_x, src_y, valid = _source_grid(extent, matrix)
        valid &= _valid_for_interpolation(
            src_x,
            src_y,
            width=width,
            height=height,
            interpolation=interpolation,
        )
        if not np.any(valid):
            return np.full(src_x.shape, np.nan, dtype=np.float32), valid, {"status": "no_overlap"}
        radius = _interpolation_radius(interpolation)
        read_x0 = max(0, int(np.floor(float(np.nanmin(src_x[valid])))) - radius)
        read_y0 = max(0, int(np.floor(float(np.nanmin(src_y[valid])))) - radius)
        read_x1 = min(width, int(np.ceil(float(np.nanmax(src_x[valid])))) + radius + 1)
        read_y1 = min(height, int(np.ceil(float(np.nanmax(src_y[valid])))) + radius + 1)
        raw = reader.read_tile(read_y0, read_y1, read_x0, read_x1, dtype=np.float32)
    exposure = _float_or_none((plan_frame or {}).get("exposure_s"))
    calibrated = _calibrate_source_tile(
        raw,
        x0=read_x0,
        y0=read_y0,
        bias=bias,
        dark=dark,
        flat=flat,
        light_exposure_s=exposure,
        policy=policy,
    )
    if interpolation == "bilinear":
        sample = _sample_bilinear_from_tile(calibrated, src_x, src_y, valid, read_x0, read_y0)
    else:
        sample = _sample_lanczos3_from_tile(calibrated, src_x, src_y, valid, read_x0, read_y0)
    return sample, valid, {"status": "replayed", "source_bbox": [read_x0, read_y0, read_x1, read_y1], "interpolation": interpolation}


def _frame_row_stats(
    frame: dict[str, Any],
    registration: dict[str, Any],
    sample: np.ndarray,
    valid: np.ndarray,
    master_tile: np.ndarray,
    proxy_low: np.ndarray | None,
    proxy_high: np.ndarray | None,
) -> dict[str, Any]:
    warnings = _warning_values(frame.get("warnings") if isinstance(frame.get("warnings"), list) else [])
    valid_sample = sample[np.isfinite(sample) & valid]
    delta = sample - np.asarray(master_tile, dtype=np.float32)
    valid_delta = delta[np.isfinite(delta) & valid]
    weight = _float_or_none(frame.get("integration_weight")) or 0.0
    row = {
        "frame_id": frame.get("frame_id"),
        "input_path": frame.get("input_path"),
        "integration_weight": weight,
        "registration_status": registration.get("status"),
        "registration_rms_px": registration.get("rms_px"),
        "valid_pixels": int(np.count_nonzero(np.isfinite(sample) & valid)),
        "sample_stats": _stats(valid_sample),
        "delta_to_master_stats": _stats(valid_delta),
        "weighted_delta_mean": None if valid_delta.size == 0 else float(weight * np.mean(valid_delta)),
        "triangle_agreement_status": warnings.get("triangle_agreement_status"),
        "triangle_agreement_score": _float_or_none(warnings.get("triangle_agreement_score")),
        "triangle_agreement_weight_multiplier": _float_or_none(warnings.get("triangle_agreement_weight_multiplier")),
        "triangle_pixel_rms_adu_batch": _float_or_none(warnings.get("triangle_pixel_rms_adu_batch")),
        "triangle_pixel_ncc_batch": _float_or_none(warnings.get("triangle_pixel_ncc_batch")),
    }
    if proxy_low is not None and proxy_high is not None:
        finite = np.isfinite(sample) & valid
        row["sigma_proxy_low_pixels"] = int(np.count_nonzero(finite & (sample < proxy_low)))
        row["sigma_proxy_high_pixels"] = int(np.count_nonzero(finite & (sample > proxy_high)))
    return row


def _read_master_tile(output: dict[str, Any], extent: dict[str, Any]) -> np.ndarray:
    master_path = output.get("master_path")
    if not master_path:
        raise ValueError("integration output has no master_path")
    with FitsImageReader(master_path) as reader:
        return reader.read_tile(
            int(extent["y0"]),
            int(extent["y1"]),
            int(extent["x0"]),
            int(extent["x1"]),
            dtype=np.float32,
        )


def _tile_replay(
    tile: dict[str, Any],
    *,
    selected_frames: list[dict[str, Any]],
    registrations: dict[str, dict[str, Any]],
    plan_frames: dict[str, dict[str, Any]],
    output: dict[str, Any],
    bias: np.ndarray | None,
    dark: np.ndarray | None,
    flat: np.ndarray | None,
    policy: dict[str, Any],
    low_sigma: float,
    high_sigma: float,
    replay_interpolation: str,
) -> dict[str, Any]:
    extent = tile.get("extent")
    if not isinstance(extent, dict):
        raise ValueError("tile is missing extent")
    master_tile = _read_master_tile(output, extent)
    samples: list[np.ndarray] = []
    valids: list[np.ndarray] = []
    replay_meta: list[dict[str, Any]] = []
    replay_frames: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for frame in selected_frames:
        frame_id = str(frame.get("frame_id"))
        registration = registrations.get(frame_id)
        if not registration or registration.get("status") not in {"ok", "reference"}:
            skipped.append({"frame_id": frame_id, "reason": "registration_not_ok"})
            continue
        try:
            sample, valid, meta = _replay_frame_tile(
                frame,
                registration,
                plan_frames.get(frame_id),
                extent,
                bias=bias,
                dark=dark,
                flat=flat,
                policy=policy,
                interpolation=replay_interpolation,
            )
        except (OSError, ValueError, np.linalg.LinAlgError) as exc:
            skipped.append({"frame_id": frame_id, "reason": str(exc)})
            continue
        samples.append(sample)
        valids.append(valid)
        replay_meta.append(meta)
        replay_frames.append(frame)
    if not samples:
        return {"index": tile.get("index"), "extent": extent, "status": "no_replayed_frames", "skipped": skipped}

    stack = np.stack(samples).astype(np.float32)
    valid_stack = np.stack(valids)
    stack = np.where(valid_stack, stack, np.nan)
    weights = np.asarray([_float_or_none(frame.get("integration_weight")) or 0.0 for frame in replay_frames], dtype=np.float32)
    weighted = stack * weights[:, None, None]
    weight_sum = np.nansum(np.where(np.isfinite(stack), weights[:, None, None], np.nan), axis=0)
    proxy_mean = np.divide(
        np.nansum(weighted, axis=0),
        weight_sum,
        out=np.full(master_tile.shape, np.nan, dtype=np.float32),
        where=weight_sum > 0,
    )
    proxy_std = np.nanstd(stack, axis=0)
    proxy_low = proxy_mean - np.float32(low_sigma) * proxy_std
    proxy_high = proxy_mean + np.float32(high_sigma) * proxy_std
    rows = []
    for frame, registration, sample in zip(
        replay_frames,
        [registrations[str(frame.get("frame_id"))] for frame in replay_frames],
        samples,
        strict=True,
    ):
        rows.append(_frame_row_stats(frame, registration, sample, np.isfinite(sample), master_tile, proxy_low, proxy_high))
    rows.sort(
        key=lambda row: abs(float(row.get("weighted_delta_mean") or 0.0)),
        reverse=True,
    )
    return {
        "index": tile.get("index"),
        "extent": extent,
        "status": "completed",
        "frame_selection_count": len(selected_frames),
        "replayed_frame_count": len(replay_frames),
        "skipped": skipped,
        "interpolation": replay_interpolation,
        "calibration": {
            "mode": "bounded_raw_master_calibration" if policy.get("masters_available") else "raw_or_partial_calibration",
            "policy": policy,
        },
        "master_tile_stats": _stats(master_tile),
        "proxy_weighted_mean_delta_to_master": _stats(proxy_mean - master_tile),
        "proxy_sigma": {"low_sigma": float(low_sigma), "high_sigma": float(high_sigma), "mode": "diagnostic_mean_std_proxy"},
        "top_frames": rows,
        "replay_source_bboxes": replay_meta,
    }


def build_compare_tile_replay(
    tile_pack: str | Path,
    run_dir: str | Path,
    *,
    filter_name: str | None = None,
    master_cache_dir: str | Path | None = None,
    frame_strategy: str = "lowest_weight",
    max_frames: int = 32,
    low_sigma: float | None = None,
    high_sigma: float | None = None,
    replay_interpolation: str = "bilinear",
) -> dict[str, Any]:
    if replay_interpolation not in _REPLAY_INTERPOLATIONS:
        raise ValueError(f"unsupported replay interpolation: {replay_interpolation}")
    run = Path(run_dir)
    pack = read_json(tile_pack)
    tiles = pack.get("tiles")
    if not isinstance(tiles, list) or not tiles:
        raise ValueError("tile pack manifest has no tiles")
    frames = _frames_by_id(run)
    registrations = _registration_by_id(run)
    plan_frames = _plan_frames_by_id(run)
    selected_frames = _select_frames(frames, strategy=frame_strategy, max_frames=int(max_frames))
    output = _integration_output(run, filter_name=filter_name)
    resident_artifact = _resident_artifact(run, filter_name=filter_name)
    integration = read_json(run / "integration_results.json")
    low = float(low_sigma if low_sigma is not None else integration.get("low_sigma", 3.0))
    high = float(high_sigma if high_sigma is not None else integration.get("high_sigma", 3.0))
    cache_dir = _discover_master_cache(run, explicit=master_cache_dir)
    bias, dark, flat, master_stats = _load_master_set(cache_dir)
    policy = _calibration_policy(run, master_stats)
    policy["masters_available"] = bool(master_stats.get("available"))
    policy["master_cache"] = master_stats
    tile_rows = [
        _tile_replay(
            tile,
            selected_frames=selected_frames,
            registrations=registrations,
            plan_frames=plan_frames,
            output=output,
            bias=bias,
            dark=dark,
            flat=flat,
            policy=policy,
            low_sigma=low,
            high_sigma=high,
            replay_interpolation=replay_interpolation,
        )
        for tile in tiles
    ]
    return {
        "schema_version": 1,
        "artifact_type": "compare_tile_replay",
        "tile_pack": str(tile_pack),
        "run_dir": str(run),
        "filter": filter_name,
        "frame_strategy": frame_strategy,
        "max_frames": int(max_frames),
        "selected_frame_count": len(selected_frames),
        "selected_frame_ids": [frame.get("frame_id") for frame in selected_frames],
        "interpolation": replay_interpolation,
        "resident_run_interpolation": output.get("warp_interpolation")
        or resident_artifact.get("warp_interpolation")
        or _discover_run_command_value(run, _WARP_INTERPOLATION_RE),
        "tile_count": len(tile_rows),
        "tiles": tile_rows,
        "limitations": [
            "Replay is a bounded CPU diagnostic path; interpolation is selected explicitly and may still differ from native CUDA details.",
            "Sigma proxy is recomputed from replayed frames and is not a byte-exact replay of resident winsorized rejection.",
        ],
    }


def write_compare_tile_replay(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Compare Tile Replay",
        "",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Tile pack: `{payload.get('tile_pack')}`",
        f"- Frame strategy: `{payload.get('frame_strategy')}`",
        f"- Selected frames: `{payload.get('selected_frame_count')}`",
        f"- Interpolation: `{payload.get('interpolation')}`",
        "",
    ]
    for tile in payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        lines.extend(
            [
                f"## Tile {tile.get('index')}",
                "",
                f"- Status: `{tile.get('status')}`",
                f"- Replayed frames: `{tile.get('replayed_frame_count')}`",
                f"- Proxy delta-to-master mean: `{(tile.get('proxy_weighted_mean_delta_to_master') or {}).get('mean')}`",
                "",
                "| frame | weight | weighted delta mean | delta mean | proxy low | proxy high | agreement | score | rms px |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
            ]
        )
        for frame in tile.get("top_frames", [])[:16]:
            if not isinstance(frame, dict):
                continue
            delta_stats = frame.get("delta_to_master_stats") if isinstance(frame.get("delta_to_master_stats"), dict) else {}
            lines.append(
                f"| {frame.get('frame_id')} | {frame.get('integration_weight')} | "
                f"{frame.get('weighted_delta_mean')} | {delta_stats.get('mean')} | "
                f"{frame.get('sigma_proxy_low_pixels')} | {frame.get('sigma_proxy_high_pixels')} | "
                f"{frame.get('triangle_agreement_status')} | {frame.get('triangle_agreement_score')} | "
                f"{frame.get('registration_rms_px')} |"
            )
        lines.append("")
    lines.extend(["## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
