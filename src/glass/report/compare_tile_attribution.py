from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import numpy as np

from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json

_WARNING_KV_RE = re.compile(r"^(?P<key>[A-Za-z0-9_]+)=(?P<value>.+)$")


def _stats(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {
            "count": 0,
            "min": None,
            "p50": None,
            "p90": None,
            "p99": None,
            "max": None,
            "mean": None,
            "sum": None,
        }
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "p50": float(np.percentile(finite, 50)),
        "p90": float(np.percentile(finite, 90)),
        "p99": float(np.percentile(finite, 99)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "sum": float(np.sum(finite)),
    }


def _read_map_tile(path: str | Path | None, extent: dict[str, Any]) -> np.ndarray | None:
    if not path:
        return None
    source = Path(path)
    if not source.exists():
        return None
    with FitsImageReader(source) as reader:
        return reader.read_tile(
            int(extent["y0"]),
            int(extent["y1"]),
            int(extent["x0"]),
            int(extent["x1"]),
            dtype=np.float32,
        )


def _first_output(run_dir: Path, filter_name: str | None = None) -> dict[str, Any]:
    integration_path = run_dir / "integration_results.json"
    if not integration_path.exists():
        return {}
    payload = read_json(integration_path)
    outputs = payload.get("outputs")
    if not isinstance(outputs, list):
        return {}
    if filter_name:
        for output in outputs:
            if isinstance(output, dict) and output.get("filter") == filter_name:
                return output
    return outputs[0] if outputs and isinstance(outputs[0], dict) else {}


def _resident_artifact(run_dir: Path, filter_name: str | None = None) -> dict[str, Any]:
    artifacts_path = run_dir / "resident_artifacts.json"
    if not artifacts_path.exists():
        return {}
    payload = read_json(artifacts_path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return {}
    if filter_name:
        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("filter") == filter_name:
                return artifact
    return artifacts[0] if artifacts and isinstance(artifacts[0], dict) else {}


def _map_paths(run_dir: Path, filter_name: str | None = None) -> dict[str, str | None]:
    output = _first_output(run_dir, filter_name=filter_name)
    artifact = _resident_artifact(run_dir, filter_name=filter_name)
    paths: dict[str, str | None] = {}
    for key, json_key in [
        ("coverage", "coverage_map_path"),
        ("weight", "weight_map_path"),
        ("low_rejection", "low_rejection_map_path"),
        ("high_rejection", "high_rejection_map_path"),
        ("dq", "dq_map_path"),
    ]:
        value = output.get(json_key) or artifact.get(json_key)
        paths[key] = str(value) if value else None
    return paths


def _dq_flag_bits(run_dir: Path, filter_name: str | None = None) -> dict[str, int]:
    artifact = _resident_artifact(run_dir, filter_name=filter_name)
    bits = artifact.get("dq_flag_bits")
    if not isinstance(bits, dict):
        return {"no_data": 1, "warp_edge": 64, "low_rejected": 256, "high_rejected": 512}
    out: dict[str, int] = {}
    for key, default in [("no_data", 1), ("warp_edge", 64), ("low_rejected", 256), ("high_rejected", 512)]:
        try:
            out[key] = int(bits.get(key, default))
        except (TypeError, ValueError):
            out[key] = default
    return out


def _count_dq_bits(tile: np.ndarray | None, bits: dict[str, int]) -> dict[str, int] | None:
    if tile is None:
        return None
    values = np.asarray(tile, dtype=np.int64)
    return {key: int(np.count_nonzero((values & int(mask)) != 0)) for key, mask in bits.items()}


def _warning_values(warnings: list[Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for warning in warnings:
        if not isinstance(warning, str):
            continue
        match = _WARNING_KV_RE.match(warning)
        if match:
            values[match.group("key")] = match.group("value")
    return values


def _float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _frame_accounting_summary(run_dir: Path, *, frame_limit: int) -> dict[str, Any]:
    path = run_dir / "frame_accounting.json"
    if not path.exists():
        return {"available": False}
    payload = read_json(path)
    frames = payload.get("frames")
    if not isinstance(frames, list):
        return {"available": False}
    rows: list[dict[str, Any]] = []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        weight = _float_or_none(frame.get("integration_weight"))
        warning_values = _warning_values(frame.get("warnings") if isinstance(frame.get("warnings"), list) else [])
        multiplier = _float_or_none(warning_values.get("triangle_agreement_weight_multiplier"))
        score = _float_or_none(warning_values.get("triangle_agreement_score"))
        rows.append(
            {
                "frame_id": frame.get("frame_id"),
                "input_path": frame.get("input_path"),
                "final_status": frame.get("final_status"),
                "registration_status": frame.get("registration_status"),
                "integration_status": frame.get("integration_status"),
                "integration_weight": weight,
                "triangle_agreement_status": warning_values.get("triangle_agreement_status"),
                "triangle_agreement_score": score,
                "triangle_agreement_weight_multiplier": multiplier,
                "triangle_pixel_rms_adu_batch": _float_or_none(warning_values.get("triangle_pixel_rms_adu_batch")),
                "triangle_pixel_ncc_batch": _float_or_none(warning_values.get("triangle_pixel_ncc_batch")),
            }
        )
    weights = np.asarray(
        [row["integration_weight"] for row in rows if row.get("integration_weight") is not None],
        dtype=np.float64,
    )
    integrated = [row for row in rows if row.get("final_status") == "integrated"]
    zero_weight = [row for row in rows if row.get("integration_weight") == 0.0]
    downweighted = [
        row
        for row in rows
        if row.get("triangle_agreement_status") == "downweighted"
        or (
            row.get("triangle_agreement_weight_multiplier") is not None
            and float(row["triangle_agreement_weight_multiplier"]) < 1.0
        )
    ]
    low_weight = sorted(
        [row for row in rows if row.get("integration_weight") is not None],
        key=lambda item: (float(item["integration_weight"]), str(item.get("frame_id"))),
    )
    downweighted_sorted = sorted(
        downweighted,
        key=lambda item: (
            1.0
            if item.get("triangle_agreement_weight_multiplier") is None
            else float(item["triangle_agreement_weight_multiplier"]),
            str(item.get("frame_id")),
        ),
    )
    return {
        "available": True,
        "frame_count": len(rows),
        "integrated_count": len(integrated),
        "zero_weight_count": len(zero_weight),
        "downweighted_count": len(downweighted),
        "weight_stats": _stats(weights),
        "lowest_weight_frames": low_weight[: max(0, int(frame_limit))],
        "strongest_downweighted_frames": downweighted_sorted[: max(0, int(frame_limit))],
        "exception_summary": payload.get("exception_summary"),
    }


def _tile_map_summary(
    *,
    extent: dict[str, Any],
    map_paths: dict[str, str | None],
    dq_bits: dict[str, int],
) -> dict[str, Any]:
    coverage = _read_map_tile(map_paths.get("coverage"), extent)
    weight = _read_map_tile(map_paths.get("weight"), extent)
    low = _read_map_tile(map_paths.get("low_rejection"), extent)
    high = _read_map_tile(map_paths.get("high_rejection"), extent)
    dq = _read_map_tile(map_paths.get("dq"), extent)
    low_values = np.zeros_like(coverage, dtype=np.float32) if coverage is not None else None
    high_values = np.zeros_like(coverage, dtype=np.float32) if coverage is not None else None
    if low is not None:
        low_values = np.asarray(low, dtype=np.float32)
    if high is not None:
        high_values = np.asarray(high, dtype=np.float32)
    rejection = None
    pre_rejection = None
    if coverage is not None and low_values is not None and high_values is not None:
        rejection = np.asarray(low_values + high_values, dtype=np.float32)
        pre_rejection = np.asarray(coverage + rejection, dtype=np.float32)
    rejection_sum = float(np.sum(rejection, dtype=np.float64)) if rejection is not None else None
    pre_sum = float(np.sum(pre_rejection, dtype=np.float64)) if pre_rejection is not None else None
    coverage_sum = float(np.sum(coverage, dtype=np.float64)) if coverage is not None else None
    return {
        "extent": extent,
        "pixels": int((int(extent["y1"]) - int(extent["y0"])) * (int(extent["x1"]) - int(extent["x0"]))),
        "coverage": _stats(coverage) if coverage is not None else None,
        "weight": _stats(weight) if weight is not None else None,
        "low_rejection": _stats(low) if low is not None else None,
        "high_rejection": _stats(high) if high is not None else None,
        "total_rejection": _stats(rejection) if rejection is not None else None,
        "pre_rejection_coverage": _stats(pre_rejection) if pre_rejection is not None else None,
        "dq_flag_counts": _count_dq_bits(dq, dq_bits),
        "rejection_sample_fraction": None if not pre_sum else float((rejection_sum or 0.0) / pre_sum),
        "post_rejection_coverage_fraction": None if not pre_sum else float((coverage_sum or 0.0) / pre_sum),
    }


def _tile_recommendation(tile: dict[str, Any]) -> dict[str, Any]:
    rejection_fraction = tile.get("rejection_sample_fraction")
    coverage = tile.get("coverage") if isinstance(tile.get("coverage"), dict) else {}
    dq_counts = tile.get("dq_flag_counts") if isinstance(tile.get("dq_flag_counts"), dict) else {}
    if rejection_fraction is not None and float(rejection_fraction) >= 0.05:
        return {
            "status": "rejection_heavy_tile",
            "next_target": "inspect low/high rejection behavior and frame contribution inside this residual tile",
        }
    if dq_counts and int(dq_counts.get("warp_edge", 0)) > int(tile.get("pixels", 0)) * 0.25:
        return {
            "status": "warp_edge_heavy_tile",
            "next_target": "inspect registration footprint and crop/coverage policy for this tile",
        }
    if coverage and coverage.get("min") is not None and coverage.get("max") is not None:
        if float(coverage["max"]) - float(coverage["min"]) >= 2.0:
            return {
                "status": "coverage_variable_tile",
                "next_target": "inspect geometric coverage and rejected-frame distribution across this tile",
            }
    return {
        "status": "map_summary_not_explanatory",
        "next_target": "inspect per-frame contribution or local normalization/registration residuals",
    }


def build_compare_tile_attribution(
    tile_pack: str | Path,
    run_dir: str | Path,
    *,
    filter_name: str | None = None,
    frame_limit: int = 16,
) -> dict[str, Any]:
    pack = read_json(tile_pack)
    tiles = pack.get("tiles")
    if not isinstance(tiles, list) or not tiles:
        raise ValueError("tile pack manifest has no tiles")
    run = Path(run_dir)
    map_paths = _map_paths(run, filter_name=filter_name)
    dq_bits = _dq_flag_bits(run, filter_name=filter_name)
    tile_rows: list[dict[str, Any]] = []
    for tile in tiles:
        if not isinstance(tile, dict) or not isinstance(tile.get("extent"), dict):
            continue
        summary = _tile_map_summary(extent=tile["extent"], map_paths=map_paths, dq_bits=dq_bits)
        summary["index"] = tile.get("index")
        summary["source_tile"] = tile.get("source_top_tile")
        summary["tile_pack_paths"] = tile.get("paths")
        summary["diff_stats"] = {
            "signed": tile.get("signed_diff_stats"),
            "abs": tile.get("abs_diff_stats"),
        }
        summary["recommendation"] = _tile_recommendation(summary)
        tile_rows.append(summary)
    payload = {
        "schema_version": 1,
        "artifact_type": "compare_tile_attribution",
        "tile_pack": str(tile_pack),
        "run_dir": str(run),
        "filter": filter_name,
        "map_paths": map_paths,
        "dq_flag_bits": dq_bits,
        "tile_count": len(tile_rows),
        "tiles": tile_rows,
        "frame_accounting": _frame_accounting_summary(run, frame_limit=int(frame_limit)),
        "limitations": [
            "This artifact attributes localized residual tiles to available output maps and frame-accounting metadata.",
            "It does not replay per-frame registered samples because the resident run did not save per-frame registered caches.",
        ],
    }
    return payload


def write_compare_tile_attribution(
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
        "# Compare Tile Attribution",
        "",
        f"- Run: `{payload.get('run_dir')}`",
        f"- Tile pack: `{payload.get('tile_pack')}`",
        f"- Tile count: `{payload.get('tile_count')}`",
        "",
        "## Tiles",
        "",
        "| tile | coverage mean | rejection fraction | weight mean | dq warp edge | recommendation |",
        "| ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for tile in payload.get("tiles", []):
        if not isinstance(tile, dict):
            continue
        coverage = tile.get("coverage") if isinstance(tile.get("coverage"), dict) else {}
        weight = tile.get("weight") if isinstance(tile.get("weight"), dict) else {}
        dq = tile.get("dq_flag_counts") if isinstance(tile.get("dq_flag_counts"), dict) else {}
        recommendation = tile.get("recommendation") if isinstance(tile.get("recommendation"), dict) else {}
        lines.append(
            f"| {tile.get('index')} | {coverage.get('mean')} | {tile.get('rejection_sample_fraction')} | "
            f"{weight.get('mean')} | {dq.get('warp_edge')} | `{recommendation.get('status')}` |"
        )
    accounting = payload.get("frame_accounting") if isinstance(payload.get("frame_accounting"), dict) else {}
    lines.extend(
        [
            "",
            "## Frame Accounting",
            "",
            f"- Available: `{accounting.get('available')}`",
            f"- Frame count: `{accounting.get('frame_count')}`",
            f"- Integrated count: `{accounting.get('integrated_count')}`",
            f"- Zero-weight count: `{accounting.get('zero_weight_count')}`",
            f"- Downweighted count: `{accounting.get('downweighted_count')}`",
            "",
            "### Lowest Weight Frames",
            "",
            "| frame | weight | agreement status | multiplier | score |",
            "| --- | ---: | --- | ---: | ---: |",
        ]
    )
    for frame in accounting.get("lowest_weight_frames", [])[:16]:
        if not isinstance(frame, dict):
            continue
        lines.append(
            f"| {frame.get('frame_id')} | {frame.get('integration_weight')} | "
            f"{frame.get('triangle_agreement_status')} | "
            f"{frame.get('triangle_agreement_weight_multiplier')} | {frame.get('triangle_agreement_score')} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
