from __future__ import annotations

import importlib
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from glass.io.fits_io import FitsImageReader, read_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.compare_frame_family import _select_control_ids, _select_focus_ids
from glass.report.compare_tile_attribution import _float_or_none, _stats
from glass.report.compare_tile_integration import (
    _contrast,
    _frame_contribution_row,
    _group_summary,
    _resident_rejection_replay,
)
from glass.report.compare_tile_replay import (
    _calibration_policy,
    _discover_master_cache,
    _discover_run_command_value,
    _frames_by_id,
    _integration_output,
    _load_master_set,
    _plan_frames_by_id,
    _registration_by_id,
    _resident_artifact,
    _select_frames,
)
from glass.report.resident_tile_capture import (
    _CLAMPING_RE,
    _WARP_INTERPOLATION_RE,
    _extent_shape,
    _frame_input_path,
    _read_master_tile,
    _tile_specs,
    _validate_extent,
)


def _cuda_module():
    try:
        return importlib.import_module("glass_cuda")
    except ImportError as exc:
        raise RuntimeError("glass_cuda is required for resident tile contribution capture") from exc


def _integration_rejection(run: Path, output: dict[str, Any], rejection: str | None) -> str:
    integration = read_json(run / "integration_results.json")
    mode = rejection or str(output.get("rejection") or integration.get("rejection") or "none")
    if mode not in {"none", "sigma_clip", "winsorized_sigma"}:
        raise ValueError(f"unsupported resident tile contribution rejection mode: {mode}")
    return mode


def _integration_sigma(run: Path, low_sigma: float | None, high_sigma: float | None) -> tuple[float, float]:
    integration = read_json(run / "integration_results.json")
    low = float(low_sigma if low_sigma is not None else integration.get("low_sigma", 3.0))
    high = float(high_sigma if high_sigma is not None else integration.get("high_sigma", 3.0))
    if low <= 0.0 or high <= 0.0:
        raise ValueError("sigma thresholds must be positive")
    return low, high


def _tile_rows_from_replay(
    *,
    tile: dict[str, Any],
    samples: list[np.ndarray],
    frames: list[dict[str, Any]],
    registrations: dict[str, dict[str, Any]],
    master_tile: np.ndarray,
    rejection: str,
    low_sigma: float,
    high_sigma: float,
    focus_ids: list[str],
    control_ids: list[str],
) -> dict[str, Any]:
    if not samples:
        return {"index": tile.get("index"), "extent": tile.get("extent"), "status": "no_captured_frames"}
    stack = np.stack(samples).astype(np.float32)
    valid_stack = np.isfinite(stack)
    weights = np.asarray(
        [_float_or_none(frame.get("integration_weight")) or 0.0 for frame in frames],
        dtype=np.float32,
    )
    replay = _resident_rejection_replay(
        stack,
        valid_stack,
        weights,
        rejection=rejection,
        low_sigma=low_sigma,
        high_sigma=high_sigma,
    )
    diagnostic_delta = replay["master"] - master_tile
    rows: list[dict[str, Any]] = []
    for index, frame in enumerate(frames):
        frame_id = str(frame.get("frame_id"))
        row = _frame_contribution_row(
            frame,
            registrations[frame_id],
            stack[index],
            master_tile,
            replay["weight_map"],
            replay["valid"][index],
            replay["accepted"][index],
            replay["low"][index],
            replay["high"][index],
        )
        row["tile_index"] = tile.get("index")
        row["sample_source"] = "resident_cuda_post_warp_tile_capture"
        rows.append(row)
    rows.sort(
        key=lambda row: abs(
            float(
                row.get("accepted_weighted_delta_mean")
                if row.get("accepted_weighted_delta_mean") is not None
                else row.get("normalized_delta_contribution_mean")
                or 0.0
            )
        ),
        reverse=True,
    )
    focus_summary = _group_summary(rows, focus_ids)
    control_summary = _group_summary(rows, control_ids)
    return {
        "index": tile.get("index"),
        "extent": tile.get("extent"),
        "status": "completed",
        "captured_frame_count": len(frames),
        "sample_source": "resident_cuda_post_warp_tile_capture",
        "rejection": {
            "mode": rejection,
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "algorithm": "resident_cuda_two_stage_winsorized_mean_std_rejection_on_captured_tiles"
            if rejection == "winsorized_sigma"
            else "resident_cuda_two_pass_mean_std_clip_on_captured_tiles"
            if rejection == "sigma_clip"
            else "none",
        },
        "master_tile_stats": _stats(master_tile),
        "diagnostic_master_delta_to_master": _stats(diagnostic_delta),
        "diagnostic_weight_map_stats": _stats(replay["weight_map"]),
        "diagnostic_coverage_map_stats": _stats(replay["coverage_map"]),
        "diagnostic_low_rejection_map_stats": _stats(replay["low_rejection_map"]),
        "diagnostic_high_rejection_map_stats": _stats(replay["high_rejection_map"]),
        "focus_summary": focus_summary,
        "control_summary": control_summary,
        "focus_vs_control": _contrast(focus_summary, control_summary),
        "top_frames": rows,
    }


def build_resident_tile_contribution(
    tile_pack_json: str | Path,
    run_dir: str | Path,
    *,
    filter_name: str | None = None,
    frame_strategy: str = "frame_id",
    max_frames: int = 0,
    max_tiles: int = 0,
    master_cache_dir: str | Path | None = None,
    interpolation: str | None = None,
    clamping_threshold: float | None = None,
    rejection: str | None = None,
    low_sigma: float | None = None,
    high_sigma: float | None = None,
    focus_frames: list[str] | None = None,
    focus_range_start: str | None = None,
    focus_range_end: str | None = None,
    control_frames: list[str] | None = None,
    control_before: int = 5,
    control_after: int = 5,
) -> dict[str, Any]:
    cuda_module = _cuda_module()
    if not bool(getattr(cuda_module, "cuda_available", lambda: False)()):
        raise RuntimeError("CUDA is not available for resident tile contribution capture")

    run = Path(run_dir)
    frames = _frames_by_id(run)
    registrations = _registration_by_id(run)
    plan_frames = _plan_frames_by_id(run)
    selected_frames = _select_frames(frames, strategy=frame_strategy, max_frames=int(max_frames))
    selected_frames = [
        frame
        for frame in selected_frames
        if (registrations.get(str(frame.get("frame_id"))) or {}).get("status") in {"ok", "reference"}
    ]
    if not selected_frames:
        raise ValueError("no registered positive-weight frames selected for resident tile contribution")
    tiles = _tile_specs(tile_pack_json, max_tiles=max_tiles)
    if not tiles:
        raise ValueError("tile pack contains no contribution tiles")

    output = _integration_output(run, filter_name=filter_name)
    resident = _resident_artifact(run, filter_name=filter_name)
    master_path = output.get("master_path") or resident.get("master_path")
    if not master_path:
        raise ValueError("run does not expose a resident master path")
    rejection_mode = _integration_rejection(run, output, rejection)
    low, high = _integration_sigma(run, low_sigma, high_sigma)
    cache_dir = _discover_master_cache(run, explicit=master_cache_dir)
    bias, dark, flat, master_stats = _load_master_set(cache_dir)
    policy = _calibration_policy(run, master_stats)
    command_interpolation = _discover_run_command_value(run, _WARP_INTERPOLATION_RE)
    capture_interpolation = str(interpolation or command_interpolation or "bilinear")
    if capture_interpolation not in {"bilinear", "lanczos3"}:
        raise ValueError("resident tile contribution interpolation must be bilinear or lanczos3")
    if clamping_threshold is None:
        raw_clamp = _discover_run_command_value(run, _CLAMPING_RE)
        clamping_threshold = -1.0 if raw_clamp is None else float(raw_clamp)

    first_frame = selected_frames[0]
    first_id = str(first_frame.get("frame_id"))
    with FitsImageReader(_frame_input_path(first_frame, plan_frames.get(first_id))) as reader:
        height, width = reader.shape
    for tile in tiles:
        _validate_extent(tile["extent"], width, height)

    focus_ids = _select_focus_ids(
        frames,
        focus_frames=focus_frames,
        focus_range_start=focus_range_start,
        focus_range_end=focus_range_end,
    )
    control_ids = _select_control_ids(
        frames,
        focus_ids,
        control_frames=control_frames,
        control_before=int(control_before),
        control_after=int(control_after),
    )
    stack = cuda_module.ResidentCalibratedStack(len(selected_frames), height, width)
    stack.set_calibration_masters(bias, dark, flat)
    master_tiles = {int(tile["index"]): _read_master_tile(master_path, tile["extent"]) for tile in tiles}
    samples_by_tile: dict[int, list[np.ndarray]] = {int(tile["index"]): [] for tile in tiles}
    frames_by_tile: dict[int, list[dict[str, Any]]] = {int(tile["index"]): [] for tile in tiles}
    per_frame_rows: list[dict[str, Any]] = []
    calibration_total_s = 0.0
    capture_start = perf_counter()
    for local_index, frame in enumerate(selected_frames):
        frame_id = str(frame.get("frame_id"))
        plan_frame = plan_frames.get(frame_id)
        raw = read_fits_data(_frame_input_path(frame, plan_frame), dtype=np.float32)
        if raw.shape != (height, width):
            raise ValueError(f"frame shape mismatch for {frame_id}: {raw.shape} != {(height, width)}")
        exposure = _float_or_none((plan_frame or {}).get("exposure_s")) or _float_or_none(frame.get("exposure_s")) or 0.0
        calibration_timing = stack.calibrate_frame_timed(
            local_index,
            raw,
            float(exposure),
            policy.get("dark_exposure_s"),
            policy,
        )
        calibration_total_s += float(calibration_timing.get("total_s", 0.0) or 0.0)
        matrix = (registrations.get(frame_id) or {}).get("matrix")
        if matrix is None:
            continue
        if capture_interpolation == "lanczos3":
            stack.apply_matrix_lanczos3_frame(local_index, matrix, np.nan, float(clamping_threshold))
        else:
            stack.apply_matrix_bilinear_frame(local_index, matrix, np.nan)
        frame_tile_summaries: list[dict[str, Any]] = []
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
            samples_by_tile[tile_index].append(captured)
            frames_by_tile[tile_index].append(frame)
            frame_tile_summaries.append(
                {
                    "tile_index": tile_index,
                    "valid_pixels": int(np.count_nonzero(np.isfinite(captured))),
                    "capture_stats": _stats(captured[np.isfinite(captured)]),
                }
            )
        per_frame_rows.append(
            {
                "frame_id": frame_id,
                "local_index": local_index,
                "integration_weight": _float_or_none(frame.get("integration_weight")) or 0.0,
                "registration_status": (registrations.get(frame_id) or {}).get("status"),
                "calibration_timing_s": calibration_timing,
                "tiles": frame_tile_summaries,
            }
        )
    capture_elapsed = perf_counter() - capture_start

    tile_rows = [
        _tile_rows_from_replay(
            tile=tile,
            samples=samples_by_tile[int(tile["index"])],
            frames=frames_by_tile[int(tile["index"])],
            registrations=registrations,
            master_tile=master_tiles[int(tile["index"])],
            rejection=rejection_mode,
            low_sigma=low,
            high_sigma=high,
            focus_ids=focus_ids,
            control_ids=control_ids,
        )
        for tile in tiles
    ]
    all_rows = [
        row
        for tile in tile_rows
        if isinstance(tile, dict)
        for row in tile.get("top_frames", [])
        if isinstance(row, dict)
    ]
    focus_summary = _group_summary(all_rows, focus_ids)
    control_summary = _group_summary(all_rows, control_ids)
    return {
        "schema_version": 1,
        "artifact_type": "resident_tile_contribution_capture",
        "tile_pack_json": str(tile_pack_json),
        "run_dir": str(run),
        "master_path": str(master_path),
        "master_cache_dir": None if cache_dir is None else str(cache_dir),
        "filter": filter_name,
        "frame_strategy": frame_strategy,
        "max_frames": int(max_frames),
        "max_tiles": int(max_tiles),
        "selected_frame_ids": [str(frame.get("frame_id")) for frame in selected_frames],
        "selected_frame_count": len(selected_frames),
        "focus_ids": focus_ids,
        "control_ids": control_ids,
        "tile_count": len(tile_rows),
        "shape": {"height": height, "width": width},
        "interpolation": capture_interpolation,
        "clamping_threshold": float(clamping_threshold),
        "rejection": {"mode": rejection_mode, "low_sigma": low, "high_sigma": high},
        "capture_elapsed_s": capture_elapsed,
        "calibration_total_s": calibration_total_s,
        "frames": per_frame_rows,
        "tiles": tile_rows,
        "focus_summary": focus_summary,
        "control_summary": control_summary,
        "focus_vs_control": _contrast(focus_summary, control_summary),
        "limitations": [
            "This diagnostic captures resident CUDA post-warp tile pixels, then replays rejection on the CPU.",
            "It avoids CPU image interpolation replay, but it is not a byte-level trace from inside the native integration kernel.",
            "Local normalization replay is not implemented in this diagnostic path.",
        ],
    }


def write_resident_tile_contribution(
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
    focus = payload.get("focus_summary") if isinstance(payload.get("focus_summary"), dict) else {}
    control = payload.get("control_summary") if isinstance(payload.get("control_summary"), dict) else {}
    lines = [
        "# Resident Tile Contribution Capture",
        "",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Tile pack: `{payload.get('tile_pack_json')}`",
        f"- Frames: `{payload.get('selected_frame_count')}`",
        f"- Tiles: `{payload.get('tile_count')}`",
        f"- Interpolation: `{payload.get('interpolation')}`",
        f"- Rejection: `{(payload.get('rejection') or {}).get('mode') if isinstance(payload.get('rejection'), dict) else None}`",
        f"- Capture elapsed seconds: `{payload.get('capture_elapsed_s')}`",
        "",
        "## Group Summary",
        "",
        f"- Focus contribution mean: `{(focus.get('tile_normalized_delta_contribution_sum') or {}).get('mean') if isinstance(focus.get('tile_normalized_delta_contribution_sum'), dict) else None}`",
        f"- Control contribution mean: `{(control.get('tile_normalized_delta_contribution_sum') or {}).get('mean') if isinstance(control.get('tile_normalized_delta_contribution_sum'), dict) else None}`",
        "",
        "## Tiles",
        "",
        "| tile | frames | diagnostic master delta mean | focus contribution sum | control contribution sum |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("tiles", []):
        if not isinstance(row, dict):
            continue
        delta = row.get("diagnostic_master_delta_to_master") if isinstance(row.get("diagnostic_master_delta_to_master"), dict) else {}
        focus_row = row.get("focus_summary") if isinstance(row.get("focus_summary"), dict) else {}
        control_row = row.get("control_summary") if isinstance(row.get("control_summary"), dict) else {}
        focus_contrib = (
            focus_row.get("tile_normalized_delta_contribution_sum")
            if isinstance(focus_row.get("tile_normalized_delta_contribution_sum"), dict)
            else {}
        )
        control_contrib = (
            control_row.get("tile_normalized_delta_contribution_sum")
            if isinstance(control_row.get("tile_normalized_delta_contribution_sum"), dict)
            else {}
        )
        lines.append(
            f"| {row.get('index')} | {row.get('captured_frame_count')} | {delta.get('mean')} | "
            f"{focus_contrib.get('mean')} | {control_contrib.get('mean')} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
