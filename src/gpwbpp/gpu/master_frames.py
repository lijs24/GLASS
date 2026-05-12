from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

import numpy as np

from gpwbpp.cpu.master_frames import MasterFrameResult, image_stats
from gpwbpp.gpu.tile_scheduler import iter_tiles
from gpwbpp.io.fits_io import FitsImageReader


def _native_module():
    try:
        import gpwbpp_cuda
    except Exception:
        return None
    if not gpwbpp_cuda.cuda_available():
        return None
    return gpwbpp_cuda


def _mean_stack_tile_accumulator(readers: list[FitsImageReader], tile, native) -> np.ndarray:
    sum_tile = None
    weight_sum_tile = None
    cpu_acc = None
    count = 0
    for reader in readers:
        frame_tile = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
        if native is not None and hasattr(native, "integrate_accumulate_mean_tile_f32"):
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


def mean_stack_paths_tile_streaming(
    paths: list[str | Path], tile_size: int = 512
) -> MasterFrameResult:
    if not paths:
        raise ValueError("cannot stack an empty frame list")
    native = _native_module()

    with ExitStack() as stack:
        readers = [stack.enter_context(FitsImageReader(path)) for path in paths]
        height, width = readers[0].shape
        out = np.empty((height, width), dtype=np.float32)
        for reader in readers[1:]:
            if reader.shape != (height, width):
                raise ValueError(f"shape mismatch while stacking: {reader.shape} != {(height, width)}")
        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
            out[tile.y0 : tile.y1, tile.x0 : tile.x1] = _mean_stack_tile_accumulator(readers, tile, native)
        return MasterFrameResult(out, image_stats(out))


def make_master_bias(paths: list[str | Path], tile_size: int = 512) -> MasterFrameResult:
    return mean_stack_paths_tile_streaming(paths, tile_size=tile_size)


def make_master_dark(
    paths: list[str | Path], master_bias: np.ndarray | None = None, tile_size: int = 512
) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    if master_bias is None:
        return result
    data = (result.data - master_bias).astype(np.float32)
    return MasterFrameResult(data, image_stats(data))


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
    return MasterFrameResult(data, image_stats(data))


__all__ = [
    "mean_stack_paths_tile_streaming",
    "make_master_bias",
    "make_master_dark",
    "make_master_flat",
]
