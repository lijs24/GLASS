from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from glass.engine.contracts import (
    CombinePolicy,
    DQFlag,
    DQMask,
    OutputMapPolicy,
    RejectionPolicy,
    StackRequest,
    TileWindow,
)
from glass.engine.dq import (
    add_summary_counts,
    dq_header,
    dq_mask_from_coverage,
    dq_provenance_summary_from_stack_engine,
    write_dq_tile,
)
from glass.engine.stack_engine import CPUStackEngine, StackEngineResult
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
    if weighting not in {"simple_snr", "combined", "variance_aware"}:
        raise ValueError(f"unsupported integration weighting mode: {weighting}")
    quality_path = run / "frame_quality.json"
    quality = read_json(quality_path) if quality_path.exists() else {}
    quality_by_id = {item["frame_id"]: item for item in quality.get("frame_quality", [])}
    raw_weights: dict[str, float] = {}
    for item in records:
        q = quality_by_id.get(item["frame_id"], {})
        if weighting == "simple_snr":
            value = float(q.get("snr") or q.get("weight") or 1.0)
        elif weighting == "combined":
            value = float(q.get("quality_score") or q.get("weight") or 1.0)
        else:
            noise = q.get("noise_sigma") or q.get("background_rms")
            if noise is None:
                value = float(q.get("weight") or 1.0)
            else:
                variance = max(float(noise) ** 2, 1.0e-12)
                value = 1.0 / variance
        raw_weights[item["frame_id"]] = max(value, 1.0e-6)
    positive = np.asarray([value for value in raw_weights.values() if np.isfinite(value) and value > 0.0], dtype=np.float32)
    scale = float(np.median(positive)) if positive.size else 1.0
    scale = max(scale, 1.0e-6)
    return {frame_id: max(float(value) / scale, 1.0e-6) for frame_id, value in raw_weights.items()}


def _policy_value(policy: dict[str, Any], key: str, override: str | None, default: str) -> str:
    if override is not None and override != "auto":
        return override
    return str(policy.get(key) or default)


def _stack_engine_rejection_method(value: str) -> str:
    if value == "sigma_clip":
        return "sigma"
    return value


def _output_variance_map_enabled(policy: dict[str, Any]) -> bool:
    return bool(policy.get("output_variance_map", True))


@dataclass(slots=True)
class _CoverageImageSource:
    path: str | Path
    coverage_path: str | Path
    metadata: dict[str, Any] = field(default_factory=dict)
    width: int = 0
    height: int = 0
    channels: int = 1
    dtype: str = "float32"
    _reader: FitsImageReader | None = field(default=None, init=False, repr=False)
    _coverage_reader: FitsImageReader | None = field(default=None, init=False, repr=False)

    def __enter__(self) -> "_CoverageImageSource":
        self._reader = FitsImageReader(self.path)
        self._coverage_reader = FitsImageReader(self.coverage_path)
        self._reader.__enter__()
        self._coverage_reader.__enter__()
        self.height, self.width = self._reader.shape
        if self._coverage_reader.shape != (self.height, self.width):
            raise ValueError("coverage shape does not match image shape")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._coverage_reader is not None:
            self._coverage_reader.__exit__(exc_type, exc, tb)
        if self._reader is not None:
            self._reader.__exit__(exc_type, exc, tb)
        self._reader = None
        self._coverage_reader = None

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        if self._reader is None:
            raise RuntimeError("coverage image source is not open")
        return self._reader.read_tile(window.y0, window.y1, window.x0, window.x1, dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        if self._reader is None or self._coverage_reader is None:
            raise RuntimeError("coverage image source is not open")
        data = self._reader.read_tile(window.y0, window.y1, window.x0, window.x1)
        coverage = self._coverage_reader.read_tile(window.y0, window.y1, window.x0, window.x1)
        mask = DQMask.empty(window.shape)
        invalid = (~np.isfinite(data)) | (~np.isfinite(coverage)) | (coverage <= 0.5)
        if np.any(invalid):
            mask.mark(DQFlag.NO_DATA, invalid)
        return mask


def _write_stack_engine_result(
    result: StackEngineResult,
    master_path: Path,
    weight_path: Path,
    coverage_path: Path,
    variance_path: Path | None,
    low_path: Path,
    high_path: Path,
    dq_path: Path,
    tile_size: int,
) -> tuple[int, dict[str, int]]:
    height, width = result.master.shape
    tile_count = 0
    dq_summary: dict[str, int] = {}
    with ExitStack() as stack:
        master_writer = stack.enter_context(FitsTileWriter(master_path, width, height, {"IMAGETYP": "master"}))
        weight_writer = stack.enter_context(FitsTileWriter(weight_path, width, height, {"IMAGETYP": "weight"}))
        coverage_writer = stack.enter_context(FitsTileWriter(coverage_path, width, height, {"IMAGETYP": "coverage"}))
        variance_writer = (
            stack.enter_context(FitsTileWriter(variance_path, width, height, {"IMAGETYP": "variance"}))
            if variance_path is not None
            else None
        )
        low_writer = stack.enter_context(FitsTileWriter(low_path, width, height, {"IMAGETYP": "lowrej"}))
        high_writer = stack.enter_context(FitsTileWriter(high_path, width, height, {"IMAGETYP": "highrej"}))
        dq_writer = stack.enter_context(FitsTileWriter(dq_path, width, height, dq_header("integration")))
        weight_map = (
            result.weight_map if result.weight_map is not None else np.zeros_like(result.master, dtype=np.float32)
        )
        coverage_map = (
            result.coverage_map
            if result.coverage_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        low_map = (
            result.low_rejection_map
            if result.low_rejection_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        high_map = (
            result.high_rejection_map
            if result.high_rejection_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        variance_map = (
            result.variance_map
            if result.variance_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
            y_slice = slice(tile.y0, tile.y1)
            x_slice = slice(tile.x0, tile.x1)
            master_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, result.master[y_slice, x_slice])
            weight_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, weight_map[y_slice, x_slice])
            coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage_map[y_slice, x_slice])
            if variance_writer is not None:
                variance_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, variance_map[y_slice, x_slice])
            low_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, low_map[y_slice, x_slice])
            high_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, high_map[y_slice, x_slice])
            if result.dq_mask is not None:
                dq_tile = DQMask(result.dq_mask.data[y_slice, x_slice].copy())
            else:
                dq_tile = dq_mask_from_coverage(coverage_map[y_slice, x_slice], DQFlag.NO_DATA)
            write_dq_tile(dq_writer, tile, dq_tile)
            add_summary_counts(dq_summary, dq_tile.summary())
            tile_count += 1
    return tile_count, dq_summary


def _integrate_with_stack_engine(
    items: list[dict[str, Any]],
    frame_weights: dict[str, float],
    rejection: str,
    low_sigma: float,
    high_sigma: float,
    tile_size: int,
    master_path: Path,
    weight_path: Path,
    coverage_path: Path,
    variance_path: Path,
    low_path: Path,
    high_path: Path,
    dq_path: Path,
    weighting: str,
    output_variance_map: bool,
) -> tuple[int, dict[str, Any], str, dict[str, int], dict[str, Any]]:
    method = _stack_engine_rejection_method(rejection)
    with ExitStack() as stack:
        sources = {
            item["frame_id"]: stack.enter_context(
                _CoverageImageSource(item["path"], item["coverage_path"])
            )
            for item in items
        }
        request = StackRequest(
            frame_ids=tuple(item["frame_id"] for item in items),
            source_kind="light",
            combine=CombinePolicy(
                method="weighted_mean" if weighting != "none" else "mean",
                accumulator_dtype="float32",
            ),
            rejection=RejectionPolicy(
                method=method, low_sigma=low_sigma, high_sigma=high_sigma, max_reject_fraction=0.5
            ),
            output_maps=OutputMapPolicy(
                coverage=True,
                weight=True,
                variance=output_variance_map,
                low_rejection=True,
                high_rejection=True,
                dq=True,
            ),
            weights={item["frame_id"]: frame_weights[item["frame_id"]] for item in items},
            metadata={"stage": "integration", "coverage_source": "coverage_fits"},
        )
        result = CPUStackEngine(tile_size=tile_size).stack(request, sources)
    stack_engine_metrics: dict[str, Any] = dict(result.metrics)
    stack_engine_metrics["dq_provenance"] = result.dq_provenance
    tile_count, dq_summary = _write_stack_engine_result(
        result,
        master_path,
        weight_path,
        coverage_path,
        variance_path if output_variance_map else None,
        low_path,
        high_path,
        dq_path,
        tile_size,
    )
    return tile_count, stack_engine_metrics, method, dq_summary, result.dq_provenance


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
    output_variance_map = _output_variance_map_enabled(policy)
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
            variance_path = out_dir / f"variance_map_{filt}.fits"
            low_path = out_dir / f"low_rejection_{filt}.fits"
            high_path = out_dir / f"high_rejection_{filt}.fits"
            dq_path = out_dir / f"dq_map_{filt}.fits"
            tile_count = 0
            actual_backend = "cuda" if cuda_module is not None and rejection == "none" else "cpu"
            use_stack_engine = actual_backend == "cpu"
            tile_stack_mode = (
                "stack_engine_cpu"
                if use_stack_engine
                else "cuda_streaming_accumulator_fast_path"
            )
            stack_engine_metrics: dict[str, Any] | None = None
            stack_engine_rejection_method: str | None = None
            stack_engine_dq_provenance: dict[str, Any] | None = None
            dq_summary: dict[str, int] = {}

            if use_stack_engine:
                (
                    tile_count,
                    stack_engine_metrics,
                    stack_engine_rejection_method,
                    dq_summary,
                    stack_engine_dq_provenance,
                ) = _integrate_with_stack_engine(
                    items,
                    frame_weights,
                    rejection,
                    low_sigma,
                    high_sigma,
                    tile_size,
                    master_path,
                    weight_path,
                    coverage_path,
                    variance_path,
                    low_path,
                    high_path,
                    dq_path,
                    weighting,
                    output_variance_map,
                )
            else:
                master_writer = stack.enter_context(
                    FitsTileWriter(master_path, width, height, {"IMAGETYP": "master"})
                )
                weight_writer = stack.enter_context(
                    FitsTileWriter(weight_path, width, height, {"IMAGETYP": "weight"})
                )
                coverage_writer = stack.enter_context(
                    FitsTileWriter(coverage_path, width, height, {"IMAGETYP": "coverage"})
                )
                variance_writer = (
                    stack.enter_context(FitsTileWriter(variance_path, width, height, {"IMAGETYP": "variance"}))
                    if output_variance_map
                    else None
                )
                low_writer = stack.enter_context(FitsTileWriter(low_path, width, height, {"IMAGETYP": "lowrej"}))
                high_writer = stack.enter_context(FitsTileWriter(high_path, width, height, {"IMAGETYP": "highrej"}))
                dq_writer = stack.enter_context(FitsTileWriter(dq_path, width, height, dq_header("integration")))
                for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                    weights = np.asarray([frame_weights[item["frame_id"]] for item in items], dtype=np.float32)
                    sum_tile = None
                    sumsq_tile = None
                    weight_sum_tile = None
                    coverage_map = None
                    for src_reader, cov_reader, weight in zip(source_readers, coverage_readers, weights, strict=True):
                        frame_tile = src_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                        cov_tile = cov_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                        if sum_tile is None:
                            sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                            sumsq_tile = np.zeros_like(frame_tile, dtype=np.float32)
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
                        sumsq_tile += frame_tile * frame_tile * weight_tile
                        coverage_map += (cov_tile > 0.5).astype(np.float32)
                    if sum_tile is None or sumsq_tile is None or weight_sum_tile is None or coverage_map is None:
                        raise ValueError("no frames available for integration tile")
                    master = np.divide(
                        sum_tile,
                        weight_sum_tile,
                        out=np.zeros_like(sum_tile, dtype=np.float32),
                        where=weight_sum_tile > 0,
                    )
                    weight_map = weight_sum_tile.astype(np.float32)
                    variance_map = np.divide(
                        sumsq_tile,
                        weight_sum_tile,
                        out=np.zeros_like(sumsq_tile, dtype=np.float32),
                        where=weight_sum_tile > 0,
                    ) - master * master
                    variance_map = np.maximum(variance_map, 0.0).astype(np.float32)
                    low_map = np.zeros_like(master, dtype=np.float32)
                    high_map = np.zeros_like(master, dtype=np.float32)
                    master_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, master)
                    weight_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, weight_map)
                    coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage_map)
                    if variance_writer is not None:
                        variance_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, variance_map)
                    low_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, low_map)
                    high_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, high_map)
                    tile_dq = dq_mask_from_coverage(coverage_map, DQFlag.NO_DATA)
                    write_dq_tile(dq_writer, tile, tile_dq)
                    add_summary_counts(dq_summary, tile_dq.summary())
                    tile_count += 1
        outputs.append(
            {
                "filter": filt,
                "frame_count": len(items),
                "master_path": str(master_path),
                "weight_map_path": str(weight_path),
                "coverage_map_path": str(coverage_path),
                "variance_map_path": str(variance_path) if output_variance_map else None,
                "low_rejection_map_path": str(low_path),
                "high_rejection_map_path": str(high_path),
                "dq_map_path": str(dq_path),
                "dq_summary": dq_summary,
                "tile_size": tile_size,
                "tile_count": tile_count,
                "backend": actual_backend,
                "tile_stack_mode": tile_stack_mode,
                "stack_engine_enabled": use_stack_engine,
                "stack_engine_metrics": stack_engine_metrics,
                "stack_engine_rejection_method": stack_engine_rejection_method,
                "stack_engine_dq_provenance": stack_engine_dq_provenance,
                "dq_provenance_summary": dq_provenance_summary_from_stack_engine(
                    stack_engine_dq_provenance,
                    stage="integration",
                    item=filt,
                )
                if stack_engine_dq_provenance
                else None,
                "output_variance_map": output_variance_map,
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
        "output_variance_map": output_variance_map,
        "outputs": outputs,
    }
    write_json(run / "integration_results.json", payload)
    from glass.engine.frame_accounting import build_frame_accounting

    build_frame_accounting(run)
    return payload
