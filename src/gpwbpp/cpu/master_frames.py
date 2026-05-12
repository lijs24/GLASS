from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from gpwbpp.io.fits_io import read_fits_data


@dataclass(slots=True)
class MasterFrameResult:
    data: np.ndarray
    stats: dict[str, float]


def image_stats(data: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "std": float(np.std(data)),
    }


def mean_stack(paths: list[str | Path]) -> MasterFrameResult:
    if not paths:
        raise ValueError("cannot stack an empty frame list")
    acc: np.ndarray | None = None
    count = 0
    for path in paths:
        data = read_fits_data(path, dtype=np.float32)
        if acc is None:
            acc = np.zeros_like(data, dtype=np.float64)
        if data.shape != acc.shape:
            raise ValueError(f"shape mismatch while stacking {path}: {data.shape} != {acc.shape}")
        acc += data
        count += 1
    assert acc is not None
    master = (acc / count).astype(np.float32)
    return MasterFrameResult(master, image_stats(master))


def make_master_bias(paths: list[str | Path]) -> MasterFrameResult:
    return mean_stack(paths)


def make_master_dark(paths: list[str | Path], master_bias: np.ndarray | None = None) -> MasterFrameResult:
    result = mean_stack(paths)
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
) -> MasterFrameResult:
    result = mean_stack(paths)
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

