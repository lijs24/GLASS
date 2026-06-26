from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.master_frames import MasterFrameResult, image_stats
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader


def _native_module():
    try:
        import glass_cuda
    except Exception:
        return None
    if not glass_cuda.cuda_available():
        return None
    return glass_cuda


def _mean_stack_tile_accumulator(readers: list[FitsImageReader], tile, native, use_native: bool) -> np.ndarray:
    sum_tile = None
    weight_sum_tile = None
    cpu_acc = None
    count = 0
    for reader in readers:
        frame_tile = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
        if use_native:
            if sum_tile is None:
                sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                weight_sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
            weight_tile = np.ones_like(frame_tile, dtype=np.float32)
            sum_tile, weight_sum_tile = native.integrate_accumulate_mean_tile_f32(
                frame_tile, weight_tile, sum_tile, weight_sum_tile
            )
        else:
            if cpu_acc is None:
                cpu_acc = np.zeros_like(frame_tile, dtype=np.float64)
            cpu_acc += frame_tile
        count += 1
    if count == 0:
        raise ValueError("cannot stack an empty frame list")
    if sum_tile is not None and weight_sum_tile is not None:
        return np.divide(
            sum_tile,
            weight_sum_tile,
            out=np.zeros_like(sum_tile, dtype=np.float32),
            where=weight_sum_tile > 0,
        ).astype(np.float32)
    if cpu_acc is None:
        raise ValueError("cannot stack an empty frame list")
    return (cpu_acc / count).astype(np.float32)


def _mean_stack_dq_provenance(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "engine": metrics["engine"],
        "execution_path": metrics["execution_path"],
        "input_samples": int(metrics["frame_count"]) * int(metrics["width"]) * int(metrics["height"]),
        "input_valid_samples_before_rejection": None,
        "input_invalid_samples_before_rejection": None,
        "valid_samples_after_rejection": None,
        "low_rejected_samples": 0,
        "high_rejected_samples": 0,
        "rejected_samples": 0,
        "output_dq_summary": None,
        "semantics": (
            "The GPU master-frame helper is a tile-streaming mean accumulator "
            "used for CUDA-vs-CPU master-frame parity checks. It does not "
            "produce DQ masks; large-data CPU/tile pipeline master calibration "
            "uses the sink-oriented StackEngine path for full DQ provenance."
        ),
    }


def mean_stack_paths_tile_streaming(
    paths: list[str | Path], tile_size: int = 512
) -> MasterFrameResult:
    if not paths:
        raise ValueError("cannot stack an empty frame list")
    native = _native_module()
    use_native = native is not None and hasattr(native, "integrate_accumulate_mean_tile_f32")

    with ExitStack() as stack:
        readers = [stack.enter_context(FitsImageReader(path)) for path in paths]
        height, width = readers[0].shape
        out = np.empty((height, width), dtype=np.float32)
        for reader in readers[1:]:
            if reader.shape != (height, width):
                raise ValueError(f"shape mismatch while stacking: {reader.shape} != {(height, width)}")
        tile_count = 0
        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
            out[tile.y0 : tile.y1, tile.x0 : tile.x1] = _mean_stack_tile_accumulator(
                readers,
                tile,
                native,
                use_native,
            )
            tile_count += 1
        engine = "cuda_tile_streaming_mean" if use_native else "cpu_tile_streaming_mean_fallback"
        metrics: dict[str, Any] = {
            "engine": engine,
            "execution_path": "gpu_master_tile_streaming_mean",
            "public_helper": "glass.gpu.master_frames.mean_stack_paths_tile_streaming",
            "frame_count": len(paths),
            "width": width,
            "height": height,
            "tile_size": int(tile_size),
            "tile_count": tile_count,
            "combine": "mean",
            "rejection": "none",
            "cuda_native_available": native is not None,
            "cuda_accumulator_used": use_native,
            "dq_mask_produced": False,
            "result_contract_passed": None,
        }
        return MasterFrameResult(
            out,
            image_stats(out),
            engine=engine,
            metrics=metrics,
            dq_provenance=_mean_stack_dq_provenance(metrics),
            dq_mask=None,
        )


def make_master_bias(paths: list[str | Path], tile_size: int = 512) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = "bias_mean"
    return MasterFrameResult(
        result.data,
        result.stats,
        engine=result.engine,
        metrics=metrics,
        dq_provenance=result.dq_provenance,
        dq_mask=result.dq_mask,
    )


def make_master_dark(
    paths: list[str | Path], master_bias: np.ndarray | None = None, tile_size: int = 512
) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    if master_bias is None:
        metrics = dict(result.metrics or {})
        metrics["master_postprocess_operation"] = "dark_mean"
        return MasterFrameResult(
            result.data,
            result.stats,
            engine=result.engine,
            metrics=metrics,
            dq_provenance=result.dq_provenance,
            dq_mask=result.dq_mask,
        )
    data = (result.data - master_bias).astype(np.float32)
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = "dark_mean_minus_master_bias"
    return MasterFrameResult(
        data,
        image_stats(data),
        engine=result.engine,
        metrics=metrics,
        dq_provenance=result.dq_provenance,
        dq_mask=result.dq_mask,
    )


def make_master_flat(
    paths: list[str | Path],
    master_bias: np.ndarray | None = None,
    master_flat_dark: np.ndarray | None = None,
    normalization: str = "median",
    flat_floor: float = 1.0e-6,
    tile_size: int = 512,
) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    data = result.data.astype(np.float32)
    if master_bias is not None:
        data = data - master_bias
    if master_flat_dark is not None:
        data = data - master_flat_dark
    norm = float(np.mean(data) if normalization == "mean" else np.median(data))
    if abs(norm) < flat_floor:
        raise ValueError("flat normalization is below flat_floor")
    data = np.maximum(data / norm, flat_floor).astype(np.float32)
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = "flat_mean_calibrated_normalized"
    metrics["flat_normalization"] = str(normalization)
    metrics["flat_normalization_scalar"] = norm
    metrics["flat_floor"] = float(flat_floor)
    metrics["flat_subtracted_master_bias"] = master_bias is not None
    metrics["flat_subtracted_master_dark"] = master_flat_dark is not None
    return MasterFrameResult(
        data,
        image_stats(data),
        engine=result.engine,
        metrics=metrics,
        dq_provenance=result.dq_provenance,
        dq_mask=result.dq_mask,
    )


__all__ = [
    "mean_stack_paths_tile_streaming",
    "make_master_bias",
    "make_master_dark",
    "make_master_flat",
]
