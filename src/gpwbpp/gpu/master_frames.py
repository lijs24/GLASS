from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from gpwbpp.cpu.master_frames import MasterFrameResult, image_stats
from gpwbpp.cpu.master_frames import make_master_bias as make_master_bias_cpu
from gpwbpp.cpu.master_frames import make_master_dark as make_master_dark_cpu
from gpwbpp.cpu.master_frames import make_master_flat as make_master_flat_cpu
from gpwbpp.gpu.tile_scheduler import iter_tiles


def _native_module():
    try:
        import gpwbpp_cuda
    except Exception:
        return None
    if not gpwbpp_cuda.cuda_available():
        return None
    return gpwbpp_cuda


def mean_stack_paths_tile_streaming(
    paths: list[str | Path], tile_size: int = 512
) -> MasterFrameResult:
    if not paths:
        raise ValueError("cannot stack an empty frame list")
    native = _native_module()
    if native is None:
        return make_master_bias_cpu(paths)

    hdus = [fits.open(path, memmap=True) for path in paths]
    try:
        first = hdus[0][0].data
        if first is None:
            raise ValueError(f"FITS file has no primary image data: {paths[0]}")
        height, width = first.shape
        out = np.empty((height, width), dtype=np.float32)
        for hdu in hdus[1:]:
            data = hdu[0].data
            if data is None:
                raise ValueError("FITS file has no primary image data")
            if data.shape != (height, width):
                raise ValueError(f"shape mismatch while stacking: {data.shape} != {(height, width)}")
        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
            stack = np.stack(
                [
                    np.asarray(hdu[0].data[tile.y0 : tile.y1, tile.x0 : tile.x1], dtype=np.float32)
                    for hdu in hdus
                ],
                axis=0,
            )
            out[tile.y0 : tile.y1, tile.x0 : tile.x1] = native.mean_stack_tiles_f32(stack)
        return MasterFrameResult(out, image_stats(out))
    finally:
        for hdu in hdus:
            hdu.close()


def make_master_bias(paths: list[str | Path], tile_size: int = 512) -> MasterFrameResult:
    return mean_stack_paths_tile_streaming(paths, tile_size=tile_size)


def make_master_dark(
    paths: list[str | Path], master_bias: np.ndarray | None = None, tile_size: int = 512
) -> MasterFrameResult:
    native = _native_module()
    if native is None:
        return make_master_dark_cpu(paths, master_bias=master_bias)
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
    native = _native_module()
    if native is None:
        return make_master_flat_cpu(
            paths,
            master_bias=master_bias,
            master_flat_dark=master_flat_dark,
            normalization=normalization,
            flat_floor=flat_floor,
        )
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
