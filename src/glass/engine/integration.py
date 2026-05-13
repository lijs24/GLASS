from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.integration import weighted_integrate_stack
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader, FitsTileWriter
from glass.io.json_io import read_json, write_json


def _cuda_module_if_requested(backend: str):
    if backend == "cpu":
        return None
    try:
        import glass_cuda
    except Exception:
        return None
    if glass_cuda.cuda_available() and hasattr(glass_cuda, "integrate_accumulate_mean_tile_f32"):
        return glass_cuda
    if backend == "cuda":
        raise RuntimeError("CUDA backend requested but integration CUDA backend is unavailable")
    return None


def _safe_filter_name(value: str | None) -> str:
    text = value or "unknown"
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)


def _plan_data(plan_path: str | Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if plan_path is None or not Path(plan_path).exists():
        return {}, {}
    plan = read_json(plan_path)
    frames = {frame["id"]: frame for frame in plan.get("frames", [])}
    policy = plan.get("integration_policy", {})
    return frames, policy if isinstance(policy, dict) else {}


def _source_records(run: Path) -> tuple[str, list[dict[str, Any]]]:
    local_norm_path = run / "local_norm_results.json"
    if local_norm_path.exists():
        local_norm = read_json(local_norm_path)
        records = []
        for item in local_norm.get("local_norm_results", []):
            records.append(
                {
                    "frame_id": item["frame_id"],
                    "path": item["normalized_path"],
                    "coverage_path": item["coverage_path"],
                }
            )
        return "local_normalization", records
    warp = read_json(run / "warp_results.json")
    records = []
    for item in warp.get("warp_results", []):
        records.append({"frame_id": item["frame_id"], "path": item["registered_path"], "coverage_path": item["coverage_path"]})
    return "warp", records


def _quality_weights(run: Path, records: list[dict[str, Any]], weighting: str) -> dict[str, float]:
    if weighting == "none":
        return {item["frame_id"]: 1.0 for item in records}
    quality_path = run / "frame_quality.json"
    quality = read_json(quality_path) if quality_path.exists() else {}
    quality_by_id = {item["frame_id"]: item for item in quality.get("frame_quality", [])}
    weights: dict[str, float] = {}
    for item in records:
        q = quality_by_id.get(item["frame_id"], {})
        if weighting == "simple_snr":
            value = float(q.get("snr") or q.get("weight") or 1.0)
        else:
            value = float(q.get("weight") or 1.0)
        weights[item["frame_id"]] = max(value, 1.0e-6)
    return weights


def _policy_value(policy: dict[str, Any], key: str, override: str | None, default: str) -> str:
    if override is not None and override != "auto":
        return override
    return str(policy.get(key) or default)


def integrate_registered_frames(
    run_dir: str | Path,
    plan_path: str | Path | None = None,
    backend: str = "auto",
    tile_size: int = 512,
    weighting_override: str | None = None,
    rejection_override: str | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    frames, policy = _plan_data(plan_path)
    source_stage, records = _source_records(run)
    if not records:
        raise ValueError("no registered or local-normalized frames are available for integration")

    combine = str(policy.get("combine") or "mean")
    if combine != "mean":
        raise ValueError(f"unsupported integration combine mode: {combine}")
    weighting = _policy_value(policy, "weighting", weighting_override, "none")
    rejection = _policy_value(policy, "rejection", rejection_override, "none")
    low_sigma = float(policy.get("low_sigma") or 3.0)
    high_sigma = float(policy.get("high_sigma") or 3.0)
    frame_weights = _quality_weights(run, records, weighting)
    cuda_module = _cuda_module_if_requested(backend)

    by_filter: dict[str, list[dict[str, Any]]] = {}
    for item in records:
        filt = frames.get(item["frame_id"], {}).get("filter")
        by_filter.setdefault(_safe_filter_name(None if filt is None else str(filt)), []).append(item)

    out_dir = run / "integration"
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, Any]] = []

    for filt, items in by_filter.items():
        with ExitStack() as stack:
            source_readers = [stack.enter_context(FitsImageReader(item["path"])) for item in items]
            coverage_readers = [stack.enter_context(FitsImageReader(item["coverage_path"])) for item in items]
            height, width = source_readers[0].shape
            master_path = out_dir / f"master_{filt}.fits"
            weight_path = out_dir / f"weight_map_{filt}.fits"
            coverage_path = out_dir / f"coverage_map_{filt}.fits"
            low_path = out_dir / f"low_rejection_{filt}.fits"
            high_path = out_dir / f"high_rejection_{filt}.fits"
            master_writer = stack.enter_context(FitsTileWriter(master_path, width, height, {"IMAGETYP": "master"}))
            weight_writer = stack.enter_context(FitsTileWriter(weight_path, width, height, {"IMAGETYP": "weight"}))
            coverage_writer = stack.enter_context(
                FitsTileWriter(coverage_path, width, height, {"IMAGETYP": "coverage"})
            )
            low_writer = stack.enter_context(FitsTileWriter(low_path, width, height, {"IMAGETYP": "lowrej"}))
            high_writer = stack.enter_context(FitsTileWriter(high_path, width, height, {"IMAGETYP": "highrej"}))
            tile_count = 0
            actual_backend = "cuda" if cuda_module is not None and rejection == "none" else "cpu"
            tile_stack_mode = "streaming_accumulator" if rejection == "none" else "stack_for_rejection"

            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                weights = np.asarray([frame_weights[item["frame_id"]] for item in items], dtype=np.float32)
                if rejection == "none":
                    sum_tile = None
                    weight_sum_tile = None
                    coverage_map = None
                    for src_reader, cov_reader, weight in zip(source_readers, coverage_readers, weights, strict=True):
                        frame_tile = src_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                        cov_tile = cov_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                        if sum_tile is None:
                            sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                            weight_sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                            coverage_map = np.zeros_like(frame_tile, dtype=np.float32)
                        weight_tile = np.where(cov_tile > 0.5, weight, 0.0).astype(np.float32)
                        if cuda_module is not None:
                            sum_tile, weight_sum_tile = cuda_module.integrate_accumulate_mean_tile_f32(
                                frame_tile, weight_tile, sum_tile, weight_sum_tile
                            )
                        else:
                            sum_tile += frame_tile * weight_tile
                            weight_sum_tile += weight_tile
                        coverage_map += (cov_tile > 0.5).astype(np.float32)
                    if sum_tile is None or weight_sum_tile is None or coverage_map is None:
                        raise ValueError("no frames available for integration tile")
                    master = np.divide(
                        sum_tile,
                        weight_sum_tile,
                        out=np.zeros_like(sum_tile, dtype=np.float32),
                        where=weight_sum_tile > 0,
                    )
                    weight_map = weight_sum_tile.astype(np.float32)
                    low_map = np.zeros_like(master, dtype=np.float32)
                    high_map = np.zeros_like(master, dtype=np.float32)
                else:
                    frame_tiles = []
                    coverage_tiles = []
                    for src_reader, cov_reader in zip(source_readers, coverage_readers, strict=True):
                        frame_tiles.append(src_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1))
                        coverage_tiles.append(cov_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1))
                    stack_tile = np.stack(frame_tiles, axis=0)
                    coverage_tile = np.stack(coverage_tiles, axis=0)
                    master, weight_map, coverage_map, low_map, high_map = weighted_integrate_stack(
                        stack_tile,
                        coverage=coverage_tile,
                        weights=weights,
                        rejection=rejection,
                        low_sigma=low_sigma,
                        high_sigma=high_sigma,
                    )
                master_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, master)
                weight_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, weight_map)
                coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage_map)
                low_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, low_map)
                high_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, high_map)
                tile_count += 1
        outputs.append(
            {
                "filter": filt,
                "frame_count": len(items),
                "master_path": str(master_path),
                "weight_map_path": str(weight_path),
                "coverage_map_path": str(coverage_path),
                "low_rejection_map_path": str(low_path),
                "high_rejection_map_path": str(high_path),
                "tile_size": tile_size,
                "tile_count": tile_count,
                "backend": actual_backend,
                "tile_stack_mode": tile_stack_mode,
            }
        )

    payload = {
        "schema_version": 1,
        "source_stage": source_stage,
        "combine": combine,
        "weighting": weighting,
        "rejection": rejection,
        "low_sigma": low_sigma,
        "high_sigma": high_sigma,
        "frame_weights": frame_weights,
        "outputs": outputs,
    }
    write_json(run / "integration_results.json", payload)
    return payload
