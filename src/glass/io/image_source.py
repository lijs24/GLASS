from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQFlag, DQMask, TileWindow
from glass.io.fits_io import FitsImageReader, read_fits_header


@dataclass(slots=True)
class FitsImageSource:
    """FITS-backed ImageSource adapter for Phase 2 contracts."""

    path: str | Path
    metadata: dict[str, Any] = field(default_factory=dict)
    width: int = 0
    height: int = 0
    channels: int = 1
    dtype: str = "float32"
    _reader: FitsImageReader | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        header = read_fits_header(self.path)
        self.metadata = dict(header)
        self.width = int(header.get("NAXIS1", self.width or 0))
        self.height = int(header.get("NAXIS2", self.height or 0))

    def __enter__(self) -> "FitsImageSource":
        self._reader = FitsImageReader(self.path)
        self._reader.__enter__()
        self.width = self._reader.width
        self.height = self._reader.height
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._reader is not None:
            self._reader.__exit__(exc_type, exc, tb)
        self._reader = None

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        self._validate_window(window)
        if self._reader is not None:
            return self._reader.read_tile(window.y0, window.y1, window.x0, window.x1, dtype=dtype)
        with FitsImageReader(self.path) as reader:
            return reader.read_tile(window.y0, window.y1, window.x0, window.x1, dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        tile = self.read_tile(window, dtype=np.float32)
        mask = DQMask.empty(window.shape)
        invalid = ~np.isfinite(tile)
        if np.any(invalid):
            mask.mark(DQFlag.NO_DATA, invalid)
        return mask

    def _validate_window(self, window: TileWindow) -> None:
        if window.x1 > self.width or window.y1 > self.height:
            raise ValueError("tile window exceeds image bounds")
