from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.report.compare_frame_family import _select_control_ids, _select_focus_ids
from glass.report.compare_tile_attribution import _float_or_none, _stats, _warning_values
from glass.report.compare_tile_replay import (
    _REPLAY_INTERPOLATIONS,
    _WARP_INTERPOLATION_RE,
    _calibration_policy,
    _discover_master_cache,
    _discover_run_command_value,
    _frames_by_id,
    _integration_output,
    _load_master_set,
    _plan_frames_by_id,
    _read_master_tile,
    _registration_by_id,
    _replay_frame_tile,
    _resident_artifact,
    _select_frames,
)


_REJECTION_MODES = {"none", "sigma_clip", "winsorized_sigma"}


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    denominator = float(denominator)
    if denominator <= 0.0:
        return None
    return float(numerator) / denominator


def _mean_std(values: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    count = np.sum(valid, axis=0, dtype=np.float32)
    sums = np.sum(np.where(valid, values, 0.0), axis=0, dtype=np.float32)
    mean = np.divide(sums, count, out=np.zeros_like(sums, dtype=np.float32), where=count > 0)
    variance = np.sum(np.where(valid, (values - mean[None, :, :]) ** 2, 0.0), axis=0, dtype=np.float32)
    variance = np.divide(variance, count, out=np.zeros_like(variance, dtype=np.float32), where=count > 0)
    return mean.astype(np.float32), np.sqrt(variance).astype(np.float32)


def _resident_rejection_replay(
    stack: np.ndarray,
    valid_stack: np.ndarray,
    weights: np.ndarray,
    *,
    rejection: str,
    low_sigma: float,
    high_sigma: float,
) -> dict[str, Any]:
    if rejection not in _REJECTION_MODES:
        raise ValueError(f"unsupported rejection mode: {rejection}")
    positive_weights = np.isfinite(weights) & (weights > 0.0)
    valid = valid_stack & np.isfinite(stack) & positive_weights[:, None, None]
    low = np.zeros(valid.shape, dtype=bool)
    high = np.zeros(valid.shape, dtype=bool)
    low_threshold = np.zeros(stack.shape[1:], dtype=np.float32)
    high_threshold = np.zeros(stack.shape[1:], dtype=np.float32)

    if rejection in {"sigma_clip", "winsorized_sigma"}:
        center, scale = _mean_std(stack, valid)
        low_threshold = center - np.float32(low_sigma) * scale
        high_threshold = center + np.float32(high_sigma) * scale
        if rejection == "winsorized_sigma":
            clipped = np.clip(stack, low_threshold[None, :, :], high_threshold[None, :, :])
            center, scale = _mean_std(clipped.astype(np.float32), valid)
            low_threshold = center - np.float32(low_sigma) * scale
            high_threshold = center + np.float32(high_sigma) * scale
        low = valid & (stack < low_threshold[None, :, :])
        high = valid & (stack > high_threshold[None, :, :])

    accepted = valid & ~(low | high)
    effective_weights = np.where(accepted, weights[:, None, None], 0.0).astype(np.float64)
    weighted_sum = np.sum(np.where(accepted, stack, 0.0).astype(np.float64) * effective_weights, axis=0)
    weight_map = np.sum(effective_weights, axis=0)
    master = np.divide(weighted_sum, weight_map, out=np.zeros_like(weighted_sum), where=weight_map > 0)
    return {
        "master": master.astype(np.float32),
        "weight_map": weight_map.astype(np.float32),
        "coverage_map": np.sum(accepted, axis=0).astype(np.float32),
        "low_rejection_map": np.sum(low, axis=0).astype(np.float32),
        "high_rejection_map": np.sum(high, axis=0).astype(np.float32),
        "accepted": accepted,
        "low": low,
        "high": high,
        "valid": valid,
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
    }


def _frame_contribution_row(
    frame: dict[str, Any],
    registration: dict[str, Any],
    sample: np.ndarray,
    master_tile: np.ndarray,
    weight_map: np.ndarray,
    valid: np.ndarray,
    accepted: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
) -> dict[str, Any]:
    warnings = _warning_values(frame.get("warnings") if isinstance(frame.get("warnings"), list) else [])
    weight = _float_or_none(frame.get("integration_weight")) or 0.0
    delta = sample - np.asarray(master_tile, dtype=np.float32)
    finite_valid = valid & np.isfinite(delta)
    finite_accepted = accepted & np.isfinite(delta)
    contribution = np.divide(
        np.where(finite_accepted, delta * np.float32(weight), 0.0),
        weight_map,
        out=np.zeros_like(delta, dtype=np.float32),
        where=weight_map > 0,
    )
    weighted_delta = np.where(finite_accepted, delta * np.float32(weight), np.nan)
    valid_pixels = int(np.count_nonzero(finite_valid))
    accepted_pixels = int(np.count_nonzero(finite_accepted))
    low_pixels = int(np.count_nonzero(low & finite_valid))
    high_pixels = int(np.count_nonzero(high & finite_valid))
    return {
        "frame_id": frame.get("frame_id"),
        "input_path": frame.get("input_path"),
        "integration_weight": float(weight),
        "registration_status": registration.get("status"),
        "registration_rms_px": _float_or_none(registration.get("rms_px")),
        "valid_pixels": valid_pixels,
        "accepted_pixels": accepted_pixels,
        "low_rejected_pixels": low_pixels,
        "high_rejected_pixels": high_pixels,
        "rejected_pixels": low_pixels + high_pixels,
        "accepted_fraction": _ratio(accepted_pixels, valid_pixels),
        "rejected_fraction": _ratio(low_pixels + high_pixels, valid_pixels),
        "raw_delta_to_master_stats": _stats(delta[finite_valid]),
        "accepted_delta_to_master_stats": _stats(delta[finite_accepted]),
        "accepted_weighted_delta_stats": _stats(weighted_delta[np.isfinite(weighted_delta)]),
        "accepted_weighted_delta_mean": None
        if accepted_pixels == 0
        else float(np.nanmean(weighted_delta[finite_accepted])),
        "normalized_delta_contribution_stats": _stats(contribution[np.isfinite(contribution)]),
        "normalized_delta_contribution_mean": float(np.mean(contribution[np.isfinite(contribution)]))
        if np.any(np.isfinite(contribution))
        else None,
        "triangle_agreement_status": warnings.get("triangle_agreement_status"),
        "triangle_agreement_score": _float_or_none(warnings.get("triangle_agreement_score")),
        "triangle_agreement_weight_multiplier": _float_or_none(warnings.get("triangle_agreement_weight_multiplier")),
        "triangle_pixel_rms_adu_batch": _float_or_none(warnings.get("triangle_pixel_rms_adu_batch")),
        "triangle_pixel_ncc_batch": _float_or_none(warnings.get("triangle_pixel_ncc_batch")),
    }


def _group_summary(rows: list[dict[str, Any]], frame_ids: list[str]) -> dict[str, Any]:
    frame_set = set(frame_ids)
    selected = [row for row in rows if str(row.get("frame_id")) in frame_set]
    if not selected:
        return {"frame_count": len(frame_ids), "tile_frame_count": 0}
    valid = int(sum(int(row.get("valid_pixels") or 0) for row in selected))
    accepted = int(sum(int(row.get("accepted_pixels") or 0) for row in selected))
    low = int(sum(int(row.get("low_rejected_pixels") or 0) for row in selected))
    high = int(sum(int(row.get("high_rejected_pixels") or 0) for row in selected))
    tile_contribution_totals: dict[Any, float] = {}
    for row in selected:
        value = _float_or_none(row.get("normalized_delta_contribution_mean"))
        if value is None:
            continue
        tile_contribution_totals[row.get("tile_index")] = tile_contribution_totals.get(row.get("tile_index"), 0.0) + value
    return {
        "frame_count": len(frame_set),
        "tile_frame_count": len(selected),
        "valid_pixels": valid,
        "accepted_pixels": accepted,
        "low_rejected_pixels": low,
        "high_rejected_pixels": high,
        "rejected_pixels": low + high,
        "accepted_fraction": _ratio(accepted, valid),
        "rejected_fraction": _ratio(low + high, valid),
        "high_rejected_fraction": _ratio(high, valid),
        "integration_weight": _stats(
            np.asarray([row.get("integration_weight") for row in selected if row.get("integration_weight") is not None])
        ),
        "accepted_weighted_delta_mean": _stats(
            np.asarray(
                [
                    row.get("accepted_weighted_delta_mean")
                    for row in selected
                    if row.get("accepted_weighted_delta_mean") is not None
                ]
            )
        ),
        "normalized_delta_contribution_mean": _stats(
            np.asarray(
                [
                    row.get("normalized_delta_contribution_mean")
                    for row in selected
                    if row.get("normalized_delta_contribution_mean") is not None
                ]
            )
        ),
        "tile_normalized_delta_contribution_sum": _stats(np.asarray(list(tile_contribution_totals.values()))),
        "triangle_agreement_status_counts": {
            str(status): sum(1 for row in selected if row.get("triangle_agreement_status") == status)
            for status in sorted({row.get("triangle_agreement_status") for row in selected}, key=lambda item: str(item))
        },
    }


def _contrast(focus: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "accepted_fraction",
        "rejected_fraction",
        "high_rejected_fraction",
    ]
    result: dict[str, Any] = {}
    for key in keys:
        focus_value = _float_or_none(focus.get(key))
        control_value = _float_or_none(control.get(key))
        result[key] = {
            "focus": focus_value,
            "control": control_value,
            "focus_minus_control": None
            if focus_value is None or control_value is None
            else float(focus_value - control_value),
        }
    for key in ["accepted_weighted_delta_mean", "normalized_delta_contribution_mean", "tile_normalized_delta_contribution_sum"]:
        focus_mean = _float_or_none((focus.get(key) or {}).get("mean") if isinstance(focus.get(key), dict) else None)
        control_mean = _float_or_none((control.get(key) or {}).get("mean") if isinstance(control.get(key), dict) else None)
        result[key] = {
            "focus_mean": focus_mean,
            "control_mean": control_mean,
            "focus_minus_control": None
            if focus_mean is None or control_mean is None
            else float(focus_mean - control_mean),
        }
    return result


def _tile_integration_audit(
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
    rejection: str,
    low_sigma: float,
    high_sigma: float,
    replay_interpolation: str,
    focus_ids: list[str],
    control_ids: list[str],
) -> dict[str, Any]:
    extent = tile.get("extent")
    if not isinstance(extent, dict):
        raise ValueError("tile is missing extent")
    master_tile = _read_master_tile(output, extent)
    samples: list[np.ndarray] = []
    valids: list[np.ndarray] = []
    replay_frames: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for frame in selected_frames:
        frame_id = str(frame.get("frame_id"))
        registration = registrations.get(frame_id)
        if not registration or registration.get("status") not in {"ok", "reference"}:
            skipped.append({"frame_id": frame_id, "reason": "registration_not_ok"})
            continue
        try:
            sample, valid, _meta = _replay_frame_tile(
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
        replay_frames.append(frame)
    if not samples:
        return {"index": tile.get("index"), "extent": extent, "status": "no_replayed_frames", "skipped": skipped}

    stack = np.stack(samples).astype(np.float32)
    valid_stack = np.stack(valids)
    weights = np.asarray(
        [_float_or_none(frame.get("integration_weight")) or 0.0 for frame in replay_frames],
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
    diagnostic_master = replay["master"]
    diagnostic_delta = diagnostic_master - master_tile
    rows: list[dict[str, Any]] = []
    for index, frame in enumerate(replay_frames):
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
        "extent": extent,
        "status": "completed",
        "frame_selection_count": len(selected_frames),
        "replayed_frame_count": len(replay_frames),
        "skipped": skipped,
        "interpolation": replay_interpolation,
        "rejection": {
            "mode": rejection,
            "low_sigma": float(low_sigma),
            "high_sigma": float(high_sigma),
            "algorithm": "resident_cuda_two_stage_winsorized_mean_std_rejection_replay"
            if rejection == "winsorized_sigma"
            else "resident_cuda_two_pass_mean_std_clip_replay"
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


def build_compare_tile_integration_audit(
    tile_pack: str | Path,
    run_dir: str | Path,
    *,
    filter_name: str | None = None,
    master_cache_dir: str | Path | None = None,
    frame_strategy: str = "frame_id",
    max_frames: int = 0,
    max_tiles: int = 0,
    low_sigma: float | None = None,
    high_sigma: float | None = None,
    rejection: str | None = None,
    replay_interpolation: str = "lanczos3",
    focus_frames: list[str] | None = None,
    focus_range_start: str | None = None,
    focus_range_end: str | None = None,
    control_frames: list[str] | None = None,
    control_before: int = 5,
    control_after: int = 5,
) -> dict[str, Any]:
    if replay_interpolation not in _REPLAY_INTERPOLATIONS:
        raise ValueError(f"unsupported replay interpolation: {replay_interpolation}")
    run = Path(run_dir)
    pack = read_json(tile_pack)
    tiles = pack.get("tiles")
    if not isinstance(tiles, list) or not tiles:
        raise ValueError("tile pack manifest has no tiles")
    if int(max_tiles) > 0:
        tiles = tiles[: int(max_tiles)]
    frames = _frames_by_id(run)
    registrations = _registration_by_id(run)
    plan_frames = _plan_frames_by_id(run)
    selected_frames = _select_frames(frames, strategy=frame_strategy, max_frames=int(max_frames))
    output = _integration_output(run, filter_name=filter_name)
    resident_artifact = _resident_artifact(run, filter_name=filter_name)
    integration = read_json(run / "integration_results.json")
    rejection_mode = rejection or str(output.get("rejection") or integration.get("rejection") or "none")
    if rejection_mode not in _REJECTION_MODES:
        raise ValueError(f"unsupported rejection mode: {rejection_mode}")
    low = float(low_sigma if low_sigma is not None else integration.get("low_sigma", 3.0))
    high = float(high_sigma if high_sigma is not None else integration.get("high_sigma", 3.0))
    cache_dir = _discover_master_cache(run, explicit=master_cache_dir)
    bias, dark, flat, master_stats = _load_master_set(cache_dir)
    policy = _calibration_policy(run, master_stats)
    policy["masters_available"] = bool(master_stats.get("available"))
    policy["master_cache"] = master_stats
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
    tile_rows = [
        _tile_integration_audit(
            tile,
            selected_frames=selected_frames,
            registrations=registrations,
            plan_frames=plan_frames,
            output=output,
            bias=bias,
            dark=dark,
            flat=flat,
            policy=policy,
            rejection=rejection_mode,
            low_sigma=low,
            high_sigma=high,
            replay_interpolation=replay_interpolation,
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
        "artifact_type": "compare_tile_integration_audit",
        "tile_pack": str(tile_pack),
        "run_dir": str(run),
        "filter": filter_name,
        "frame_strategy": frame_strategy,
        "max_frames": int(max_frames),
        "max_tiles": int(max_tiles),
        "selected_frame_count": len(selected_frames),
        "selected_frame_ids": [frame.get("frame_id") for frame in selected_frames],
        "focus_ids": focus_ids,
        "control_ids": control_ids,
        "interpolation": replay_interpolation,
        "resident_run_interpolation": output.get("warp_interpolation")
        or resident_artifact.get("warp_interpolation")
        or _discover_run_command_value(run, _WARP_INTERPOLATION_RE),
        "rejection": {
            "mode": rejection_mode,
            "low_sigma": low,
            "high_sigma": high,
        },
        "calibration": {
            "mode": "bounded_raw_master_calibration" if policy.get("masters_available") else "raw_or_partial_calibration",
            "policy": policy,
        },
        "tile_count": len(tile_rows),
        "tiles": tile_rows,
        "focus_summary": focus_summary,
        "control_summary": control_summary,
        "focus_vs_control": _contrast(focus_summary, control_summary),
        "limitations": [
            "This is a bounded CPU diagnostic replay of the resident CUDA rejection semantics over selected tiles.",
            "It replays GLASS inputs, calibration masters, registration matrices, and final master tiles; it does not change pipeline defaults.",
            "Tiny numerical differences from native CUDA are expected because this path is an audit replay, not a kernel byte-for-byte trace.",
        ],
    }


def write_compare_tile_integration_audit(
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
    focus_summary = payload.get("focus_summary") if isinstance(payload.get("focus_summary"), dict) else {}
    control_summary = payload.get("control_summary") if isinstance(payload.get("control_summary"), dict) else {}
    lines = [
        "# Compare Tile Integration Audit",
        "",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Tile pack: `{payload.get('tile_pack')}`",
        f"- Selected frames: `{payload.get('selected_frame_count')}`",
        f"- Rejection: `{(payload.get('rejection') or {}).get('mode')}`",
        f"- Interpolation: `{payload.get('interpolation')}`",
        f"- Focus frames: `{', '.join(payload.get('focus_ids', []))}`",
        f"- Control frames: `{', '.join(payload.get('control_ids', []))}`",
        "",
        "## Group Summary",
        "",
        "| group | frames | tile rows | accepted % | rejected % | high rejected % | weighted delta mean | contribution sum mean |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, summary in [("focus", focus_summary), ("control", control_summary)]:
        lines.append(
            f"| {name} | {summary.get('frame_count')} | {summary.get('tile_frame_count')} | "
            f"{summary.get('accepted_fraction')} | {summary.get('rejected_fraction')} | "
            f"{summary.get('high_rejected_fraction')} | "
            f"{(summary.get('accepted_weighted_delta_mean') or {}).get('mean')} | "
            f"{(summary.get('tile_normalized_delta_contribution_sum') or {}).get('mean')} |"
        )
    lines.extend(
        [
            "",
            "## Tiles",
            "",
        ]
    )
    for tile in payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        lines.extend(
            [
                f"### Tile {tile.get('index')}",
                "",
                f"- Status: `{tile.get('status')}`",
                f"- Replayed frames: `{tile.get('replayed_frame_count')}`",
                f"- Diagnostic delta mean: `{(tile.get('diagnostic_master_delta_to_master') or {}).get('mean')}`",
                "",
                "| frame | weight | accepted % | high rejected | accepted weighted delta | contribution mean | agreement | rms px |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
            ]
        )
        for frame in tile.get("top_frames", [])[:16]:
            if not isinstance(frame, dict):
                continue
            lines.append(
                f"| {frame.get('frame_id')} | {frame.get('integration_weight')} | "
                f"{frame.get('accepted_fraction')} | {frame.get('high_rejected_pixels')} | "
                f"{frame.get('accepted_weighted_delta_mean')} | "
                f"{frame.get('normalized_delta_contribution_mean')} | "
                f"{frame.get('triangle_agreement_status')} | {frame.get('registration_rms_px')} |"
            )
        lines.append("")
    lines.extend(["## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
