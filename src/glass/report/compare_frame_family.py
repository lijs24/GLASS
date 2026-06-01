from __future__ import annotations

from pathlib import Path
import math
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.report.compare_tile_attribution import _float_or_none, _stats, _warning_values


def _frame_number(frame_id: str) -> int | None:
    digits = "".join(ch for ch in str(frame_id) if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _ordered_frame_ids(frames: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(frames, key=lambda frame_id: (_frame_number(frame_id) is None, _frame_number(frame_id) or 0, frame_id))


def _frames_by_id(run_dir: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(run_dir / "frame_accounting.json")
    rows = payload.get("frames")
    if not isinstance(rows, list):
        return {}
    return {str(row.get("frame_id")): row for row in rows if isinstance(row, dict) and row.get("frame_id")}


def _registrations_by_id(run_dir: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(run_dir / "registration_results.json")
    rows = payload.get("results")
    if not isinstance(rows, list):
        return {}
    return {str(row.get("frame_id")): row for row in rows if isinstance(row, dict) and row.get("frame_id")}


def _select_focus_ids(
    frames: dict[str, dict[str, Any]],
    *,
    focus_frames: list[str] | None = None,
    focus_range_start: str | None = None,
    focus_range_end: str | None = None,
) -> list[str]:
    focus = {str(frame_id) for frame_id in (focus_frames or [])}
    if focus_range_start and focus_range_end:
        start = _frame_number(focus_range_start)
        end = _frame_number(focus_range_end)
        if start is None or end is None:
            raise ValueError("focus range frame ids must contain numeric suffixes")
        lo, hi = min(start, end), max(start, end)
        for frame_id in frames:
            number = _frame_number(frame_id)
            if number is not None and lo <= number <= hi:
                focus.add(frame_id)
    missing = sorted(frame_id for frame_id in focus if frame_id not in frames)
    if missing:
        raise ValueError(f"focus frames not found in frame accounting: {missing}")
    return [frame_id for frame_id in _ordered_frame_ids(frames) if frame_id in focus]


def _select_control_ids(
    frames: dict[str, dict[str, Any]],
    focus_ids: list[str],
    *,
    control_frames: list[str] | None = None,
    control_before: int = 5,
    control_after: int = 5,
) -> list[str]:
    explicit = [str(frame_id) for frame_id in (control_frames or [])]
    if explicit:
        missing = sorted(frame_id for frame_id in explicit if frame_id not in frames)
        if missing:
            raise ValueError(f"control frames not found in frame accounting: {missing}")
        return [frame_id for frame_id in _ordered_frame_ids(frames) if frame_id in set(explicit)]
    ordered = _ordered_frame_ids(frames)
    focus_positions = [ordered.index(frame_id) for frame_id in focus_ids if frame_id in ordered]
    if not focus_positions:
        return []
    start = min(focus_positions)
    end = max(focus_positions)
    control: list[str] = []
    for frame_id in ordered[max(0, start - int(control_before)) : start]:
        if _float_or_none(frames[frame_id].get("integration_weight")) not in (None, 0.0):
            control.append(frame_id)
    for frame_id in ordered[end + 1 : end + 1 + int(control_after)]:
        if _float_or_none(frames[frame_id].get("integration_weight")) not in (None, 0.0):
            control.append(frame_id)
    return control


def _matrix_metrics(matrix: Any) -> dict[str, Any]:
    try:
        values = np.asarray(matrix, dtype=np.float64)
    except (TypeError, ValueError):
        return {"available": False}
    if values.shape != (3, 3):
        return {"available": False}
    a = float(values[0, 0])
    b = float(values[0, 1])
    c = float(values[1, 0])
    d = float(values[1, 1])
    scale_x = math.sqrt(a * a + c * c)
    scale_y = math.sqrt(b * b + d * d)
    rotation_rad = math.atan2(c, a)
    return {
        "available": True,
        "translation_x": float(values[0, 2]),
        "translation_y": float(values[1, 2]),
        "translation_norm": float(math.hypot(float(values[0, 2]), float(values[1, 2]))),
        "scale_x": scale_x,
        "scale_y": scale_y,
        "scale_mean": float((scale_x + scale_y) * 0.5),
        "rotation_rad": rotation_rad,
        "rotation_deg": float(math.degrees(rotation_rad)),
        "linear_det": float(a * d - b * c),
    }


def _tile_frame_index(replay: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    tiles = replay.get("tiles")
    if not isinstance(tiles, list):
        return index
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        rows = tile.get("top_frames")
        if not isinstance(rows, list):
            continue
        for rank, row in enumerate(rows, start=1):
            if not isinstance(row, dict) or not row.get("frame_id"):
                continue
            frame_id = str(row["frame_id"])
            delta_stats = row.get("delta_to_master_stats") if isinstance(row.get("delta_to_master_stats"), dict) else {}
            index.setdefault(frame_id, []).append(
                {
                    "tile_index": tile.get("index"),
                    "rank": rank,
                    "weighted_delta_mean": _float_or_none(row.get("weighted_delta_mean")),
                    "delta_mean": _float_or_none(delta_stats.get("mean")),
                    "delta_p99": _float_or_none(delta_stats.get("p99")),
                    "sigma_proxy_low_pixels": int(row.get("sigma_proxy_low_pixels") or 0),
                    "sigma_proxy_high_pixels": int(row.get("sigma_proxy_high_pixels") or 0),
                    "valid_pixels": int(row.get("valid_pixels") or 0),
                }
            )
    return index


def _summarize_tile_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    weighted = np.asarray([row["weighted_delta_mean"] for row in rows if row.get("weighted_delta_mean") is not None], dtype=np.float64)
    delta = np.asarray([row["delta_mean"] for row in rows if row.get("delta_mean") is not None], dtype=np.float64)
    ranks = [int(row["rank"]) for row in rows if row.get("rank") is not None]
    positive = int(np.count_nonzero(weighted > 0.0)) if weighted.size else 0
    negative = int(np.count_nonzero(weighted < 0.0)) if weighted.size else 0
    return {
        "tile_count": len(rows),
        "rank_min": min(ranks) if ranks else None,
        "rank_mean": float(np.mean(ranks)) if ranks else None,
        "weighted_delta_mean_stats": _stats(weighted),
        "delta_mean_stats": _stats(delta),
        "positive_weighted_delta_tiles": positive,
        "negative_weighted_delta_tiles": negative,
        "sigma_proxy_low_pixels": int(sum(int(row.get("sigma_proxy_low_pixels") or 0) for row in rows)),
        "sigma_proxy_high_pixels": int(sum(int(row.get("sigma_proxy_high_pixels") or 0) for row in rows)),
    }


def _frame_row(
    frame_id: str,
    *,
    group: str,
    frames: dict[str, dict[str, Any]],
    registrations: dict[str, dict[str, Any]],
    replay_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    frame = frames.get(frame_id, {})
    registration = registrations.get(frame_id, {})
    warnings = _warning_values(frame.get("warnings") if isinstance(frame.get("warnings"), list) else [])
    tile_rows = replay_index.get(frame_id, [])
    return {
        "frame_id": frame_id,
        "group": group,
        "input_path": frame.get("input_path"),
        "final_status": frame.get("final_status"),
        "integration_weight": _float_or_none(frame.get("integration_weight")),
        "triangle_agreement_status": warnings.get("triangle_agreement_status"),
        "triangle_agreement_score": _float_or_none(warnings.get("triangle_agreement_score")),
        "triangle_agreement_weight_multiplier": _float_or_none(warnings.get("triangle_agreement_weight_multiplier")),
        "triangle_pixel_rms_adu_batch": _float_or_none(warnings.get("triangle_pixel_rms_adu_batch")),
        "triangle_pixel_ncc_batch": _float_or_none(warnings.get("triangle_pixel_ncc_batch")),
        "registration_status": registration.get("status"),
        "registration_rms_px": _float_or_none(registration.get("rms_px")),
        "inliers": registration.get("inliers"),
        "matched_stars": registration.get("matched_stars"),
        "matrix_metrics": _matrix_metrics(registration.get("matrix")),
        "tile_summary": _summarize_tile_rows(tile_rows),
        "tiles": tile_rows,
    }


def _group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"count": 0}
    statuses = sorted(
        {row.get("triangle_agreement_status") for row in rows},
        key=lambda value: "" if value is None else str(value),
    )
    return {
        "count": len(rows),
        "integration_weight": _stats(np.asarray([row.get("integration_weight") for row in rows if row.get("integration_weight") is not None], dtype=np.float64)),
        "agreement_score": _stats(np.asarray([row.get("triangle_agreement_score") for row in rows if row.get("triangle_agreement_score") is not None], dtype=np.float64)),
        "registration_rms_px": _stats(np.asarray([row.get("registration_rms_px") for row in rows if row.get("registration_rms_px") is not None], dtype=np.float64)),
        "translation_x": _stats(
            np.asarray(
                [
                    (row.get("matrix_metrics") or {}).get("translation_x")
                    for row in rows
                    if isinstance(row.get("matrix_metrics"), dict)
                    and (row.get("matrix_metrics") or {}).get("translation_x") is not None
                ],
                dtype=np.float64,
            )
        ),
        "translation_y": _stats(
            np.asarray(
                [
                    (row.get("matrix_metrics") or {}).get("translation_y")
                    for row in rows
                    if isinstance(row.get("matrix_metrics"), dict)
                    and (row.get("matrix_metrics") or {}).get("translation_y") is not None
                ],
                dtype=np.float64,
            )
        ),
        "rank_min": _stats(
            np.asarray(
                [
                    (row.get("tile_summary") or {}).get("rank_min")
                    for row in rows
                    if isinstance(row.get("tile_summary"), dict)
                    and (row.get("tile_summary") or {}).get("rank_min") is not None
                ],
                dtype=np.float64,
            )
        ),
        "weighted_delta_mean": _stats(
            np.asarray(
                [
                    ((row.get("tile_summary") or {}).get("weighted_delta_mean_stats") or {}).get("mean")
                    for row in rows
                    if isinstance(row.get("tile_summary"), dict)
                    and isinstance((row.get("tile_summary") or {}).get("weighted_delta_mean_stats"), dict)
                    and ((row.get("tile_summary") or {}).get("weighted_delta_mean_stats") or {}).get("mean") is not None
                ],
                dtype=np.float64,
            )
        ),
        "agreement_status_counts": {
            str(status): sum(1 for row in rows if row.get("triangle_agreement_status") == status)
            for status in statuses
        },
    }


def _mean(summary: dict[str, Any], key: str) -> float | None:
    item = summary.get(key)
    if not isinstance(item, dict):
        return None
    return _float_or_none(item.get("mean"))


def _summary_contrast(focus: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "integration_weight",
        "agreement_score",
        "registration_rms_px",
        "translation_x",
        "translation_y",
        "rank_min",
        "weighted_delta_mean",
    ]
    result: dict[str, Any] = {}
    for key in keys:
        focus_mean = _mean(focus, key)
        control_mean = _mean(control, key)
        result[key] = {
            "focus_mean": focus_mean,
            "control_mean": control_mean,
            "focus_minus_control": None
            if focus_mean is None or control_mean is None
            else float(focus_mean - control_mean),
        }
    return result


def build_compare_frame_family_audit(
    replay_json: str | Path,
    run_dir: str | Path,
    *,
    focus_frames: list[str] | None = None,
    focus_range_start: str | None = None,
    focus_range_end: str | None = None,
    control_frames: list[str] | None = None,
    control_before: int = 5,
    control_after: int = 5,
) -> dict[str, Any]:
    run = Path(run_dir)
    replay = read_json(replay_json)
    frames = _frames_by_id(run)
    registrations = _registrations_by_id(run)
    focus_ids = _select_focus_ids(
        frames,
        focus_frames=focus_frames,
        focus_range_start=focus_range_start,
        focus_range_end=focus_range_end,
    )
    if not focus_ids:
        raise ValueError("at least one focus frame or focus range is required")
    control_ids = _select_control_ids(
        frames,
        focus_ids,
        control_frames=control_frames,
        control_before=int(control_before),
        control_after=int(control_after),
    )
    replay_index = _tile_frame_index(replay)
    focus_rows = [
        _frame_row(frame_id, group="focus", frames=frames, registrations=registrations, replay_index=replay_index)
        for frame_id in focus_ids
    ]
    control_rows = [
        _frame_row(frame_id, group="control", frames=frames, registrations=registrations, replay_index=replay_index)
        for frame_id in control_ids
    ]
    ranked_focus = sorted(
        focus_rows,
        key=lambda row: (
            -abs(float(((row.get("tile_summary") or {}).get("weighted_delta_mean_stats") or {}).get("mean") or 0.0)),
            str(row.get("frame_id")),
        ),
    )
    focus_summary = _group_summary(focus_rows)
    control_summary = _group_summary(control_rows)
    return {
        "schema_version": 1,
        "artifact_type": "compare_frame_family_audit",
        "replay_json": str(replay_json),
        "run_dir": str(run),
        "replay_interpolation": replay.get("interpolation"),
        "resident_run_interpolation": replay.get("resident_run_interpolation"),
        "focus_ids": focus_ids,
        "control_ids": control_ids,
        "focus_summary": focus_summary,
        "control_summary": control_summary,
        "focus_vs_control": _summary_contrast(focus_summary, control_summary),
        "focus_rows": focus_rows,
        "control_rows": control_rows,
        "ranked_focus_rows": ranked_focus,
        "interpretation": {
            "top_focus_frame": None if not ranked_focus else ranked_focus[0].get("frame_id"),
            "focus_frame_count": len(focus_rows),
            "control_frame_count": len(control_rows),
        },
    }


def write_compare_frame_family_audit(
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
        "# Compare Frame Family Audit",
        "",
        f"- Replay: `{payload.get('replay_json')}`",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Focus frames: `{', '.join(payload.get('focus_ids', []))}`",
        f"- Control frames: `{', '.join(payload.get('control_ids', []))}`",
        f"- Replay interpolation: `{payload.get('replay_interpolation')}`",
        "",
        "## Group Summary",
        "",
        "| group | count | weight mean | agreement mean | RMS mean | tx mean | ty mean | weighted delta mean |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, summary in [("focus", focus_summary), ("control", control_summary)]:
        lines.append(
            f"| {name} | {summary.get('count')} | "
            f"{(summary.get('integration_weight') or {}).get('mean')} | "
            f"{(summary.get('agreement_score') or {}).get('mean')} | "
            f"{(summary.get('registration_rms_px') or {}).get('mean')} | "
            f"{(summary.get('translation_x') or {}).get('mean')} | "
            f"{(summary.get('translation_y') or {}).get('mean')} | "
            f"{(summary.get('weighted_delta_mean') or {}).get('mean')} |"
        )
    contrast = payload.get("focus_vs_control") if isinstance(payload.get("focus_vs_control"), dict) else {}
    lines.extend(
        [
            "",
            "## Focus vs Control",
            "",
            "| metric | focus mean | control mean | focus - control |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for key, item in contrast.items():
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| {key} | {item.get('focus_mean')} | {item.get('control_mean')} | "
            f"{item.get('focus_minus_control')} |"
        )
    lines.extend(
        [
            "",
            "## Ranked Focus Frames",
            "",
            "| frame | weight | agreement | rms | tx | ty | rank min | weighted delta mean | sigma high |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload.get("ranked_focus_rows", [])[:24]:
        if not isinstance(row, dict):
            continue
        matrix = row.get("matrix_metrics") if isinstance(row.get("matrix_metrics"), dict) else {}
        tile = row.get("tile_summary") if isinstance(row.get("tile_summary"), dict) else {}
        weighted = tile.get("weighted_delta_mean_stats") if isinstance(tile.get("weighted_delta_mean_stats"), dict) else {}
        lines.append(
            f"| {row.get('frame_id')} | {row.get('integration_weight')} | "
            f"{row.get('triangle_agreement_score')} | {row.get('registration_rms_px')} | "
            f"{matrix.get('translation_x')} | {matrix.get('translation_y')} | {tile.get('rank_min')} | "
            f"{weighted.get('mean')} | {tile.get('sigma_proxy_high_pixels')} |"
        )
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
