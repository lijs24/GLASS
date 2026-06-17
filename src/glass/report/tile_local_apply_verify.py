from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.report.compare_report import _apply_candidate_transform, _read_image_data


def _tile_index(tile: dict[str, Any]) -> int:
    value = tile.get("tile_index", tile.get("index"))
    if value is None:
        raise ValueError("tile row is missing tile_index")
    return int(value)


def _extent(tile: dict[str, Any], *, shape: tuple[int, int], pad_px: int = 0) -> dict[str, int]:
    raw = tile.get("extent")
    if not isinstance(raw, dict):
        raise ValueError(f"tile {_tile_index(tile)} is missing extent")
    height, width = shape
    x0 = max(0, int(raw["x0"]) - int(pad_px))
    y0 = max(0, int(raw["y0"]) - int(pad_px))
    x1 = min(width, int(raw["x1"]) + int(pad_px))
    y1 = min(height, int(raw["y1"]) + int(pad_px))
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"tile {_tile_index(tile)} has an invalid bounded extent")
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _stats(diff: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(diff, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {
            "count": 0,
            "mean_signed": None,
            "mean_abs": None,
            "median_abs": None,
            "rms": None,
            "p90_abs": None,
            "p99_abs": None,
            "max_abs": None,
        }
    abs_values = np.abs(finite)
    return {
        "count": int(finite.size),
        "mean_signed": float(np.mean(finite)),
        "mean_abs": float(np.mean(abs_values)),
        "median_abs": float(np.percentile(abs_values, 50)),
        "rms": float(np.sqrt(np.mean(finite * finite))),
        "p90_abs": float(np.percentile(abs_values, 90)),
        "p99_abs": float(np.percentile(abs_values, 99)),
        "max_abs": float(np.max(abs_values)),
    }


def _finite_mean(values: list[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    if not finite:
        return None
    return float(np.mean(np.asarray(finite, dtype=np.float64)))


def build_tile_local_apply_verification(
    *,
    baseline: str | Path,
    candidate: str | Path,
    reference: str | Path,
    replay: str | Path,
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    clip_low: float | None = None,
    clip_high: float | None = None,
    coverage_map: str | Path | None = None,
    min_coverage: float | None = None,
    pad_px: int = 0,
) -> dict[str, Any]:
    replay_payload = read_json(replay)
    if not isinstance(replay_payload, dict) or replay_payload.get("artifact_type") != "tile_local_policy_replay":
        raise ValueError("replay must be a tile_local_policy_replay artifact")
    replay_tiles = replay_payload.get("tiles")
    if not isinstance(replay_tiles, list) or not replay_tiles:
        raise ValueError("replay must contain at least one tile")

    baseline_image, baseline_transform = _apply_candidate_transform(
        _read_image_data(baseline),
        scale=glass_scale,
        offset=glass_offset,
        clip_low=clip_low,
        clip_high=clip_high,
    )
    candidate_image, candidate_transform = _apply_candidate_transform(
        _read_image_data(candidate),
        scale=glass_scale,
        offset=glass_offset,
        clip_low=clip_low,
        clip_high=clip_high,
    )
    reference_image = _read_image_data(reference)
    if baseline_image.shape != candidate_image.shape or baseline_image.shape != reference_image.shape:
        raise ValueError(
            "image shape mismatch: "
            f"baseline={baseline_image.shape}, candidate={candidate_image.shape}, reference={reference_image.shape}"
        )

    coverage_image = None
    if coverage_map is not None:
        coverage_image = _read_image_data(coverage_map)
        if coverage_image.shape != baseline_image.shape:
            raise ValueError(f"coverage shape mismatch: {coverage_image.shape} != {baseline_image.shape}")

    rows: list[dict[str, Any]] = []
    for tile in replay_tiles:
        if not isinstance(tile, dict):
            continue
        bounded = _extent(tile, shape=baseline_image.shape, pad_px=int(pad_px))
        y0, y1 = bounded["y0"], bounded["y1"]
        x0, x1 = bounded["x0"], bounded["x1"]
        baseline_tile = np.asarray(baseline_image[y0:y1, x0:x1], dtype=np.float32)
        candidate_tile = np.asarray(candidate_image[y0:y1, x0:x1], dtype=np.float32)
        reference_tile = np.asarray(reference_image[y0:y1, x0:x1], dtype=np.float32)
        mask = np.isfinite(baseline_tile) & np.isfinite(candidate_tile) & np.isfinite(reference_tile)
        if coverage_image is not None and min_coverage is not None:
            coverage_tile = np.asarray(coverage_image[y0:y1, x0:x1], dtype=np.float32)
            mask &= np.isfinite(coverage_tile) & (coverage_tile >= float(min_coverage))
        baseline_diff = np.where(mask, baseline_tile - reference_tile, np.nan)
        candidate_diff = np.where(mask, candidate_tile - reference_tile, np.nan)
        before = _stats(baseline_diff)
        after = _stats(candidate_diff)
        before_mean_abs = before.get("mean_abs")
        after_mean_abs = after.get("mean_abs")
        before_rms = before.get("rms")
        after_rms = after.get("rms")
        before_signed = before.get("mean_signed")
        after_signed = after.get("mean_signed")
        mean_abs_delta = None if before_mean_abs is None or after_mean_abs is None else after_mean_abs - before_mean_abs
        rms_delta = None if before_rms is None or after_rms is None else after_rms - before_rms
        signed_abs_delta = None if before_signed is None or after_signed is None else abs(after_signed) - abs(before_signed)
        rows.append(
            {
                "tile_index": _tile_index(tile),
                "extent": bounded,
                "original_extent": tile.get("extent"),
                "pixel_count": int((y1 - y0) * (x1 - x0)),
                "compared_pixels": int(np.count_nonzero(mask)),
                "baseline_residual": before,
                "candidate_residual": after,
                "mean_abs_delta": mean_abs_delta,
                "rms_delta": rms_delta,
                "signed_mean_abs_delta": signed_abs_delta,
                "measured_mean_abs_improved": mean_abs_delta is not None and mean_abs_delta < 0.0,
                "measured_rms_improved": rms_delta is not None and rms_delta < 0.0,
                "measured_signed_mean_improved": signed_abs_delta is not None and signed_abs_delta < 0.0,
                "replay_predicted_before": tile.get("signed_residual_reference_units_before"),
                "replay_predicted_after": tile.get("signed_residual_reference_units_after"),
                "replay_moves_toward_reference": tile.get("moves_toward_reference"),
            }
        )

    before_mean_abs = _finite_mean(
        [
            (row.get("baseline_residual") or {}).get("mean_abs")
            for row in rows
            if isinstance(row.get("baseline_residual"), dict)
        ]
    )
    after_mean_abs = _finite_mean(
        [
            (row.get("candidate_residual") or {}).get("mean_abs")
            for row in rows
            if isinstance(row.get("candidate_residual"), dict)
        ]
    )
    before_rms = _finite_mean(
        [(row.get("baseline_residual") or {}).get("rms") for row in rows if isinstance(row.get("baseline_residual"), dict)]
    )
    after_rms = _finite_mean(
        [(row.get("candidate_residual") or {}).get("rms") for row in rows if isinstance(row.get("candidate_residual"), dict)]
    )
    improved_mean_abs = sum(1 for row in rows if row.get("measured_mean_abs_improved") is True)
    improved_rms = sum(1 for row in rows if row.get("measured_rms_improved") is True)
    improved_signed = sum(1 for row in rows if row.get("measured_signed_mean_improved") is True)
    passed = (
        bool(rows)
        and improved_signed == len(rows)
        and improved_rms == len(rows)
        and before_mean_abs is not None
        and after_mean_abs is not None
        and after_mean_abs < before_mean_abs
        and before_rms is not None
        and after_rms is not None
        and after_rms < before_rms
    )
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_apply_verification",
        "created_at": now_iso(),
        "baseline": str(baseline),
        "candidate": str(candidate),
        "reference": str(reference),
        "replay": str(replay),
        "coverage_map": None if coverage_map is None else str(coverage_map),
        "min_coverage": min_coverage,
        "pad_px": int(pad_px),
        "candidate_transform": candidate_transform,
        "baseline_transform": baseline_transform,
        "summary": {
            "passed": passed,
            "status": "passed" if passed else "failed",
            "tile_count": len(rows),
            "mean_abs_improved_tiles": improved_mean_abs,
            "rms_improved_tiles": improved_rms,
            "signed_mean_improved_tiles": improved_signed,
            "mean_abs_residual_before": before_mean_abs,
            "mean_abs_residual_after": after_mean_abs,
            "mean_abs_delta": None if before_mean_abs is None or after_mean_abs is None else after_mean_abs - before_mean_abs,
            "mean_rms_before": before_rms,
            "mean_rms_after": after_rms,
            "mean_rms_delta": None if before_rms is None or after_rms is None else after_rms - before_rms,
            "recommendation": "measured_local_improvement" if passed else "hold_for_localized_review",
        },
        "tiles": rows,
        "limitations": [
            "This verification reads bounded tile pixels from baseline, candidate, and reference outputs.",
            "It validates selected replay tiles only; it does not prove an unbounded global tile-local policy.",
        ],
    }


def write_tile_local_apply_verification(
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
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# Tile-Local Apply Verification",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Recommendation: `{summary.get('recommendation')}`",
        f"- Mean abs residual before / after: `{summary.get('mean_abs_residual_before')}` / `{summary.get('mean_abs_residual_after')}`",
        f"- Mean RMS before / after: `{summary.get('mean_rms_before')}` / `{summary.get('mean_rms_after')}`",
        "",
        "| tile | compared px | mean abs before | mean abs after | rms before | rms after | signed mean improved |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload.get("tiles", []):
        if not isinstance(row, dict):
            continue
        before = row.get("baseline_residual") if isinstance(row.get("baseline_residual"), dict) else {}
        after = row.get("candidate_residual") if isinstance(row.get("candidate_residual"), dict) else {}
        lines.append(
            "| {tile} | {pixels} | {before_abs} | {after_abs} | {before_rms} | {after_rms} | {improved} |".format(
                tile=row.get("tile_index"),
                pixels=row.get("compared_pixels"),
                before_abs=before.get("mean_abs"),
                after_abs=after.get("mean_abs"),
                before_rms=before.get("rms"),
                after_rms=after.get("rms"),
                improved=row.get("measured_signed_mean_improved"),
            )
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
