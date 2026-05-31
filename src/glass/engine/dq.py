from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag, DQMask
from glass.io.fits_io import FitsTileWriter


def dq_header(stage: str, frame_id: str | None = None) -> dict[str, Any]:
    header: dict[str, Any] = {"IMAGETYP": "dq_mask", "DQSTAGE": stage}
    if frame_id is not None:
        header["FRAMEID"] = frame_id
    return header


def dq_summary(mask: DQMask | np.ndarray) -> dict[str, int]:
    if isinstance(mask, DQMask):
        return mask.summary()
    return DQMask(np.asarray(mask, dtype=np.uint32)).summary()


def dq_mask_from_invalid(shape: tuple[int, int], invalid: np.ndarray, flag: DQFlag) -> DQMask:
    mask = DQMask.empty(shape)
    if np.any(invalid):
        mask.mark(flag, invalid)
    return mask


def dq_mask_from_coverage(coverage: np.ndarray, invalid_flag: DQFlag) -> DQMask:
    cov = np.asarray(coverage, dtype=np.float32)
    return dq_mask_from_invalid(cov.shape, (~np.isfinite(cov)) | (cov <= 0.5), invalid_flag)


def write_dq_tile(writer: FitsTileWriter, tile: Any, mask: DQMask | np.ndarray) -> None:
    data = mask.data if isinstance(mask, DQMask) else np.asarray(mask, dtype=np.uint32)
    writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, data.astype(np.float32))


def add_summary_counts(target: dict[str, int], summary: dict[str, int]) -> None:
    for key, value in summary.items():
        target[key] = int(target.get(key, 0) + int(value))


def write_full_dq_map(path: str | Path, mask: DQMask | np.ndarray, stage: str, frame_id: str | None = None) -> None:
    data = mask.data if isinstance(mask, DQMask) else np.asarray(mask, dtype=np.uint32)
    height, width = data.shape
    with FitsTileWriter(path, width=width, height=height, header=dq_header(stage, frame_id)) as writer:
        class FullTile:
            y0 = 0
            x0 = 0
            y1 = height
            x1 = width

        write_dq_tile(writer, FullTile, data)
