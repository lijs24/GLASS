from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits


def open_fits_image(path: str | Path, memmap: bool = True) -> fits.HDUList:
    hdul = fits.open(path, memmap=memmap)
    try:
        _ = hdul[0].data
    except ValueError as exc:
        if memmap and "Cannot load a memory-mapped image" in str(exc):
            hdul.close()
            return fits.open(path, memmap=False)
        hdul.close()
        raise
    return hdul


def read_fits_data(path: str | Path, dtype=np.float32) -> np.ndarray:
    with FitsImageReader(path) as reader:
        return reader.read_full(dtype=dtype)


def read_fits_header(path: str | Path) -> dict[str, Any]:
    header = fits.getheader(path, memmap=True)
    return {str(k): header[k] for k in header.keys()}


def write_fits_data(path: str | Path, data: np.ndarray, header: dict[str, Any] | None = None) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    hdu = fits.PrimaryHDU(np.asarray(data, dtype=np.float32))
    if header:
        for key, value in header.items():
            if value is not None and len(str(key)) <= 8:
                hdu.header[str(key)] = value
    hdu.writeto(target, overwrite=True)


def create_empty_fits_image(
    path: str | Path, width: int, height: int, header: dict[str, Any] | None = None
) -> int:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    h = fits.Header()
    h["SIMPLE"] = True
    h["BITPIX"] = -32
    h["NAXIS"] = 2
    h["NAXIS1"] = int(width)
    h["NAXIS2"] = int(height)
    if header:
        for key, value in header.items():
            if value is not None and len(str(key)) <= 8:
                h[str(key)] = value
    header_bytes = h.tostring(endcard=True, padding=True).encode("ascii")
    data_bytes = int(width) * int(height) * 4
    padding = (2880 - (data_bytes % 2880)) % 2880
    with target.open("wb") as f:
        f.write(header_bytes)
        if data_bytes + padding:
            f.seek(len(header_bytes) + data_bytes + padding - 1)
            f.write(b"\0")
    return len(header_bytes)


class FitsTileWriter:
    def __init__(self, path: str | Path, width: int, height: int, header: dict[str, Any] | None = None):
        self.path = Path(path)
        self.width = int(width)
        self.height = int(height)
        self.header = header or {}
        self._offset: int | None = None
        self._map: np.memmap | None = None

    def __enter__(self) -> "FitsTileWriter":
        self._offset = create_empty_fits_image(self.path, self.width, self.height, self.header)
        self._map = np.memmap(
            self.path,
            dtype=">f4",
            mode="r+",
            offset=self._offset,
            shape=(self.height, self.width),
        )
        return self

    def write_tile(self, y0: int, y1: int, x0: int, x1: int, data: np.ndarray) -> None:
        if self._map is None:
            raise RuntimeError("FitsTileWriter is not open")
        self._map[y0:y1, x0:x1] = np.asarray(data, dtype=np.float32).astype(">f4", copy=False)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._map is not None:
            self._map.flush()
        self._map = None


class FitsImageReader:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._hdul: fits.HDUList | None = None
        self._data: np.ndarray | None = None
        self.header: fits.Header | None = None
        self.width = 0
        self.height = 0
        self.bscale = 1.0
        self.bzero = 0.0
        self.blank: float | int | None = None
        self.scaled = False

    def __enter__(self) -> "FitsImageReader":
        self._hdul = fits.open(self.path, memmap=True, do_not_scale_image_data=True)
        hdu = self._hdul[0]
        data = hdu.data
        if data is None:
            raise ValueError(f"FITS file has no primary image data: {self.path}")
        self._data = data
        self.header = hdu.header
        self.height, self.width = data.shape
        self.bscale = float(self.header.get("BSCALE", 1.0))
        self.bzero = float(self.header.get("BZERO", 0.0))
        self.blank = self.header.get("BLANK")
        self.scaled = self.bscale != 1.0 or self.bzero != 0.0 or self.blank is not None
        return self

    @property
    def shape(self) -> tuple[int, int]:
        return self.height, self.width

    def read_tile(self, y0: int, y1: int, x0: int, x1: int, dtype=np.float32) -> np.ndarray:
        if self._data is None:
            raise RuntimeError("FitsImageReader is not open")
        raw = self._data[y0:y1, x0:x1]
        out = np.asarray(raw, dtype=np.float32)
        if self.blank is not None:
            mask = np.asarray(raw == self.blank)
            if np.any(mask):
                out = out.copy()
                out[mask] = np.nan
        if self.bscale != 1.0 or self.bzero != 0.0:
            out = out * np.float32(self.bscale) + np.float32(self.bzero)
        return np.asarray(out, dtype=dtype)

    def read_full(self, dtype=np.float32) -> np.ndarray:
        return self.read_tile(0, self.height, 0, self.width, dtype=dtype)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._hdul is not None:
            self._hdul.close()
        self._hdul = None
        self._data = None
        self.header = None
