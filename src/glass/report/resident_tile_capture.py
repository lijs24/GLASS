from __future__ import annotations

import importlib
from pathlib import Path
import re
from time import perf_counter
from typing import Any

import numpy as np

from glass.io.fits_io import FitsImageReader, read_fits_data, write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.compare_frame_family import _frame_number, _ordered_frame_ids
from glass.report.compare_tile_attribution import _float_or_none, _stats
from glass.report.compare_tile_replay import (
    _calibration_policy,
    _discover_master_cache,
    _discover_run_command_value,
    _integration_output,
    _load_master_set,
    _plan_frames_by_id,
    _registration_by_id,
    _resident_artifact,
)

_CLAMPING_RE = re.compile(r"--resident-warp-clamping-threshold\s+(?P<value>\S+)")
_WARP_INTERPOLATION_RE = re.compile(r"--resident-warp-interpolation\s+(?P<name>\S+)")


def _cuda_module():
    try:
        return importlib.import_module("glass_cuda")
    except ImportError as exc:
        raise RuntimeError("glass_cuda is required for resident tile capture") from exc


def _frames_by_id(run_dir: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(run_dir / "frame_accounting.json")
    rows = payload.get("frames")
    if not isinstance(rows, list):
        return {}
    return {str(row.get("frame_id")): row for row in rows if isinstance(row, dict) and row.get("frame_id")}


def _select_capture_frame_ids(
    frames: dict[str, dict[str, Any]],
    *,
    frame_ids: list[str] | None = None,
    frame_range_start: str | None = None,
    frame_range_end: str | None = None,
    max_frames: int = 0,
) -> list[str]:
    selected = {str(frame_id) for frame_id in (frame_ids or [])}
    if frame_range_start and frame_range_end:
        start = _frame_number(frame_range_start)
        end = _frame_number(frame_range_end)
        if start is None or end is None:
            raise ValueError("frame range ids must contain numeric suffixes")
        lo, hi = min(start, end), max(start, end)
        for frame_id in frames:
            number = _frame_number(frame_id)
            if number is not None and lo <= number <= hi:
                selected.add(frame_id)
    missing = sorted(frame_id for frame_id in selected if frame_id not in frames)
    if missing:
        raise ValueError(f"capture frames not found in frame accounting: {missing}")
    ordered = [frame_id for frame_id in _ordered_frame_ids(frames) if frame_id in selected]
    ordered = [
        frame_id
        for frame_id in ordered
        if _float_or_none(frames[frame_id].get("integration_weight")) not in (None, 0.0)
    ]
    if max_frames > 0:
        ordered = ordered[: int(max_frames)]
    if not ordered:
        raise ValueError("no positive-weight frames selected for resident tile capture")
    return ordered


def _tile_specs(tile_pack_json: str | Path, max_tiles: int = 0) -> list[dict[str, Any]]:
    payload = read_json(tile_pack_json)
    tiles = payload.get("tiles")
    if not isinstance(tiles, list):
        return []
    specs: list[dict[str, Any]] = []
    for tile in tiles:
        if not isinstance(tile, dict) or not isinstance(tile.get("extent"), dict):
            continue
        extent = tile["extent"]
        specs.append(
            {
                "index": int(tile.get("index", len(specs))),
                "extent": {
                    "x0": int(extent["x0"]),
                    "y0": int(extent["y0"]),
                    "x1": int(extent["x1"]),
                    "y1": int(extent["y1"]),
                },
                "source_top_tile": tile.get("source_top_tile") if isinstance(tile.get("source_top_tile"), dict) else {},
            }
        )
    if max_tiles > 0:
        specs = specs[: int(max_tiles)]
    return specs


def _frame_input_path(frame: dict[str, Any], plan_frame: dict[str, Any] | None = None) -> Path:
    for key in ("input_path", "path"):
        value = frame.get(key)
        if value:
            return Path(str(value))
    if plan_frame:
        value = plan_frame.get("path")
        if value:
            return Path(str(value))
    raise ValueError(f"frame {frame.get('frame_id')} has no input path")


def _read_master_tile(master_path: str | Path, extent: dict[str, int]) -> np.ndarray:
    with FitsImageReader(master_path) as reader:
        return reader.read_tile(extent["y0"], extent["y1"], extent["x0"], extent["x1"], dtype=np.float32)


def _extent_shape(extent: dict[str, int]) -> tuple[int, int]:
    return int(extent["y1"] - extent["y0"]), int(extent["x1"] - extent["x0"])


def _validate_extent(extent: dict[str, int], width: int, height: int) -> None:
    if extent["x0"] < 0 or extent["y0"] < 0 or extent["x0"] >= extent["x1"] or extent["y0"] >= extent["y1"]:
        raise ValueError(f"invalid tile extent: {extent}")
    if extent["x1"] > width or extent["y1"] > height:
        raise ValueError(f"tile extent outside frame shape {width}x{height}: {extent}")


def _replay_index(replay_json: str | Path | None) -> dict[tuple[int, str], dict[str, Any]]:
    if replay_json is None:
        return {}
    payload = read_json(replay_json)
    index: dict[tuple[int, str], dict[str, Any]] = {}
    for tile in payload.get("tiles", []) if isinstance(payload.get("tiles"), list) else []:
        if not isinstance(tile, dict):
            continue
        tile_index = int(tile.get("index", -1))
        rows = tile.get("top_frames")
        if not isinstance(rows, list):
            continue
        for rank, row in enumerate(rows, start=1):
            if isinstance(row, dict) and row.get("frame_id"):
                index[(tile_index, str(row["frame_id"]))] = {**row, "rank": rank}
    return index


def _stats_delta(capture: np.ndarray, master: np.ndarray, weight: float) -> dict[str, Any]:
    delta = np.asarray(capture, dtype=np.float32) - np.asarray(master, dtype=np.float32)
    finite = np.isfinite(delta)
    weighted = delta[finite].astype(np.float64) * float(weight)
    return {
        "capture_stats": _stats(np.asarray(capture[np.isfinite(capture)], dtype=np.float64)),
        "delta_to_master_stats": _stats(np.asarray(delta[finite], dtype=np.float64)),
        "weighted_delta_mean": None if weighted.size == 0 else float(np.mean(weighted)),
        "valid_pixels": int(np.count_nonzero(finite)),
        "nan_pixels": int(delta.size - np.count_nonzero(finite)),
    }


def build_resident_tile_capture(
    tile_pack_json: str | Path,
    run_dir: str | Path,
    out_dir: str | Path,
    *,
    replay_json: str | Path | None = None,
    filter_name: str | None = None,
    frame_ids: list[str] | None = None,
    frame_range_start: str | None = None,
    frame_range_end: str | None = None,
    max_frames: int = 0,
    max_tiles: int = 0,
    master_cache_dir: str | Path | None = None,
    interpolation: str | None = None,
    clamping_threshold: float | None = None,
    write_tiles: bool = False,
) -> dict[str, Any]:
    cuda_module = _cuda_module()
    if not bool(getattr(cuda_module, "cuda_available", lambda: False)()):
        raise RuntimeError("CUDA is not available for resident tile capture")

    run = Path(run_dir)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    frames = _frames_by_id(run)
    plan_frames = _plan_frames_by_id(run)
    registrations = _registration_by_id(run)
    selected_ids = _select_capture_frame_ids(
        frames,
        frame_ids=frame_ids,
        frame_range_start=frame_range_start,
        frame_range_end=frame_range_end,
        max_frames=max_frames,
    )
    tiles = _tile_specs(tile_pack_json, max_tiles=max_tiles)
    if not tiles:
        raise ValueError("tile pack contains no capture tiles")

    cache_dir = _discover_master_cache(run, master_cache_dir)
    bias, dark, flat, master_stats = _load_master_set(cache_dir)
    policy = _calibration_policy(run, master_stats)
    resident = _resident_artifact(run, filter_name)
    integration = _integration_output(run, filter_name)
    master_path = integration.get("master_path") or resident.get("master_path")
    if not master_path:
        raise ValueError("run does not expose a resident master path")
    command_interpolation = _discover_run_command_value(run, _WARP_INTERPOLATION_RE)
    capture_interpolation = str(interpolation or command_interpolation or "bilinear")
    if capture_interpolation not in {"bilinear", "lanczos3"}:
        raise ValueError("resident tile capture interpolation must be bilinear or lanczos3")
    if clamping_threshold is None:
        raw_clamp = _discover_run_command_value(run, _CLAMPING_RE)
        clamping_threshold = -1.0 if raw_clamp is None else float(raw_clamp)

    first_frame = frames[selected_ids[0]]
    first_plan = plan_frames.get(selected_ids[0])
    first_path = _frame_input_path(first_frame, first_plan)
    with FitsImageReader(first_path) as reader:
        height, width = reader.shape
    for tile in tiles:
        _validate_extent(tile["extent"], width, height)

    stack = cuda_module.ResidentCalibratedStack(len(selected_ids), height, width)
    stack.set_calibration_masters(bias, dark, flat)
    replay_rows = _replay_index(replay_json)
    frame_rows: list[dict[str, Any]] = []
    tile_rows: dict[int, list[dict[str, Any]]] = {int(tile["index"]): [] for tile in tiles}
    timings: list[float] = []
    master_tiles = {int(tile["index"]): _read_master_tile(master_path, tile["extent"]) for tile in tiles}

    start = perf_counter()
    for local_index, frame_id in enumerate(selected_ids):
        frame = frames[frame_id]
        plan_frame = plan_frames.get(frame_id)
        input_path = _frame_input_path(frame, plan_frame)
        raw = read_fits_data(input_path, dtype=np.float32)
        if raw.shape != (height, width):
            raise ValueError(f"frame shape mismatch for {frame_id}: {raw.shape} != {(height, width)}")
        light_exposure = _float_or_none((plan_frame or {}).get("exposure_s")) or _float_or_none(frame.get("exposure_s")) or 0.0
        calibration_timing = stack.calibrate_frame_timed(
            local_index,
            raw,
            float(light_exposure),
            policy.get("dark_exposure_s"),
            policy,
        )
        matrix = (registrations.get(frame_id) or {}).get("matrix")
        if matrix is None:
            raise ValueError(f"registration matrix missing for {frame_id}")
        if capture_interpolation == "lanczos3":
            stack.apply_matrix_lanczos3_frame(local_index, matrix, np.nan, float(clamping_threshold))
        else:
            stack.apply_matrix_bilinear_frame(local_index, matrix, np.nan)
        weight = _float_or_none(frame.get("integration_weight")) or 0.0
        per_tile: list[dict[str, Any]] = []
        for tile in tiles:
            tile_index = int(tile["index"])
            extent = tile["extent"]
            captured = np.asarray(
                stack.download_frame_tile(
                    local_index,
                    int(extent["x0"]),
                    int(extent["y0"]),
                    int(extent["x1"]),
                    int(extent["y1"]),
                ),
                dtype=np.float32,
            )
            if captured.shape != _extent_shape(extent):
                raise RuntimeError(f"captured tile shape mismatch for {frame_id} tile {tile_index}")
            row = {
                "tile_index": tile_index,
                "frame_id": frame_id,
                "integration_weight": weight,
                "extent": extent,
                **_stats_delta(captured, master_tiles[tile_index], weight),
            }
            replay_row = replay_rows.get((tile_index, frame_id))
            if isinstance(replay_row, dict):
                replay_weighted = _float_or_none(replay_row.get("weighted_delta_mean"))
                row["cpu_replay_rank"] = replay_row.get("rank")
                row["cpu_replay_weighted_delta_mean"] = replay_weighted
                row["resident_minus_cpu_weighted_delta_mean"] = (
                    None if replay_weighted is None else float(row["weighted_delta_mean"] - replay_weighted)
                )
            if write_tiles:
                tile_path = target_dir / f"tile_{tile_index:03d}_{frame_id}_resident_capture.fits"
                write_fits_data(
                    tile_path,
                    captured,
                    header={"IMAGETYP": "capture", "FRAMEID": frame_id[:8], "TILE": tile_index},
                    dtype=np.float32,
                )
                row["capture_path"] = str(tile_path)
            per_tile.append(row)
            tile_rows[tile_index].append(row)
        frame_rows.append(
            {
                "frame_id": frame_id,
                "local_index": local_index,
                "input_path": str(input_path),
                "integration_weight": weight,
                "registration_status": (registrations.get(frame_id) or {}).get("status"),
                "registration_matrix": matrix,
                "calibration_timing_s": calibration_timing,
                "tiles": per_tile,
            }
        )
        timings.append(float(calibration_timing.get("total_s", 0.0) or 0.0))
    elapsed = perf_counter() - start

    summaries = []
    for tile in tiles:
        tile_index = int(tile["index"])
        rows = tile_rows[tile_index]
        resident_delta = np.asarray(
            [row["weighted_delta_mean"] for row in rows if row.get("weighted_delta_mean") is not None],
            dtype=np.float64,
        )
        cpu_delta = np.asarray(
            [row["resident_minus_cpu_weighted_delta_mean"] for row in rows if row.get("resident_minus_cpu_weighted_delta_mean") is not None],
            dtype=np.float64,
        )
        summaries.append(
            {
                "tile_index": tile_index,
                "extent": tile["extent"],
                "captured_frame_count": len(rows),
                "resident_weighted_delta_mean": _stats(resident_delta),
                "resident_minus_cpu_weighted_delta_mean": _stats(cpu_delta),
            }
        )

    return {
        "schema_version": 1,
        "artifact_type": "resident_tile_capture",
        "tile_pack_json": str(tile_pack_json),
        "replay_json": None if replay_json is None else str(replay_json),
        "run_dir": str(run),
        "out_dir": str(target_dir),
        "master_path": str(master_path),
        "master_cache_dir": None if cache_dir is None else str(cache_dir),
        "selected_frame_ids": selected_ids,
        "selected_frame_count": len(selected_ids),
        "tile_count": len(tiles),
        "shape": {"height": height, "width": width},
        "interpolation": capture_interpolation,
        "clamping_threshold": float(clamping_threshold),
        "write_tiles": bool(write_tiles),
        "elapsed_s": elapsed,
        "calibration_total_s": float(sum(timings)),
        "tile_summaries": summaries,
        "frames": frame_rows,
        "limitations": [
            "diagnostic capture replays selected frames only, not the full integration kernel",
            "captures post-calibration and post-warp resident frame tiles before rejection decisions",
            "local normalization replay is not implemented in this diagnostic path",
        ],
    }


def write_resident_tile_capture(out: str | Path, payload: dict[str, Any], *, markdown: str | Path | None = None) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Resident Tile Capture",
        "",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Tile pack: `{payload.get('tile_pack_json')}`",
        f"- Replay: `{payload.get('replay_json')}`",
        f"- Frames: `{payload.get('selected_frame_count')}`",
        f"- Tiles: `{payload.get('tile_count')}`",
        f"- Interpolation: `{payload.get('interpolation')}`",
        f"- Elapsed seconds: `{payload.get('elapsed_s')}`",
        "",
        "## Tile Summary",
        "",
        "| tile | frames | resident weighted delta mean | resident minus CPU mean |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("tile_summaries", []):
        if not isinstance(row, dict):
            continue
        resident = row.get("resident_weighted_delta_mean") if isinstance(row.get("resident_weighted_delta_mean"), dict) else {}
        diff = (
            row.get("resident_minus_cpu_weighted_delta_mean")
            if isinstance(row.get("resident_minus_cpu_weighted_delta_mean"), dict)
            else {}
        )
        lines.append(
            f"| {row.get('tile_index')} | {row.get('captured_frame_count')} | "
            f"{resident.get('mean')} | {diff.get('mean')} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
