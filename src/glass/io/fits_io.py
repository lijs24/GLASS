from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits

_DIRECT_FITS_DTYPES: dict[np.dtype, tuple[int, str]] = {
    np.dtype(np.uint8): (8, ">u1"),
    np.dtype(np.int16): (16, ">i2"),
    np.dtype(np.int32): (32, ">i4"),
    np.dtype(np.float32): (-32, ">f4"),
    np.dtype(np.float64): (-64, ">f8"),
}
_DIRECT_FITS_WRITE_CHUNK_BYTES = 16 * 1024 * 1024


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


def fits_write_backend(data: np.ndarray, dtype: Any = np.float32) -> str:
    array = np.asarray(data)
    target_dtype = np.dtype(dtype)
    if array.ndim == 2 and target_dtype in _DIRECT_FITS_DTYPES:
        return "direct_simple_primary"
    return "astropy_primary_hdu"


def _direct_fits_rows_per_chunk(width: int, dtype: Any, max_chunk_bytes: int) -> int:
    row_bytes = max(1, int(width) * np.dtype(dtype).itemsize)
    return max(1, int(max_chunk_bytes) // row_bytes)


def _direct_fits_chunk_count(height: int, rows_per_chunk: int) -> int:
    if int(height) <= 0:
        return 0
    return (int(height) + int(rows_per_chunk) - 1) // int(rows_per_chunk)


def fits_write_profile(
    data: np.ndarray,
    dtype: Any = np.float32,
    *,
    max_chunk_bytes: int = _DIRECT_FITS_WRITE_CHUNK_BYTES,
) -> dict[str, Any]:
    array = np.asarray(data)
    target_dtype = np.dtype(dtype)
    backend = fits_write_backend(array, target_dtype)
    profile: dict[str, Any] = {
        "writer_backend": backend,
        "source_dtype": array.dtype.name,
        "target_dtype": target_dtype.name,
        "source_c_contiguous": bool(array.flags.c_contiguous),
        "source_shape": [int(v) for v in array.shape],
    }
    if backend != "direct_simple_primary":
        profile["writer_strategy"] = "astropy_primary_hdu"
        return profile
    rows_per_chunk = _direct_fits_rows_per_chunk(array.shape[1], target_dtype, max_chunk_bytes)
    chunk_count = _direct_fits_chunk_count(array.shape[0], rows_per_chunk)
    profile.update(
        {
            "writer_strategy": "direct_simple_primary_chunked_big_endian",
            "direct_streaming": True,
            "max_chunk_bytes": int(max_chunk_bytes),
            "rows_per_chunk": int(rows_per_chunk),
            "chunk_count": int(chunk_count),
            "estimated_data_bytes": int(array.shape[0] * array.shape[1] * target_dtype.itemsize),
        }
    )
    return profile


def _iter_direct_fits_data_chunks(
    data: np.ndarray,
    dtype: Any,
    *,
    max_chunk_bytes: int = _DIRECT_FITS_WRITE_CHUNK_BYTES,
):
    target_dtype = np.dtype(dtype)
    _, storage_dtype = _DIRECT_FITS_DTYPES[target_dtype]
    array = np.asarray(data)
    if array.ndim != 2:
        raise ValueError("direct FITS writer supports only 2D primary images")
    rows_per_chunk = _direct_fits_rows_per_chunk(array.shape[1], target_dtype, max_chunk_bytes)
    big_endian_dtype = np.dtype(storage_dtype)
    for y0 in range(0, array.shape[0], rows_per_chunk):
        y1 = min(array.shape[0], y0 + rows_per_chunk)
        slab = np.asarray(array[y0:y1], dtype=target_dtype, order="C")
        stored = slab.astype(big_endian_dtype, copy=False)
        if not stored.flags.c_contiguous:
            stored = np.ascontiguousarray(stored)
        yield memoryview(stored).cast("B")


def _write_simple_fits_direct(
    path: Path,
    data: np.ndarray,
    header: dict[str, Any] | None,
    dtype: Any,
) -> None:
    target_dtype = np.dtype(dtype)
    bitpix, storage_dtype = _DIRECT_FITS_DTYPES[target_dtype]
    array = np.asarray(data)
    if array.ndim != 2:
        raise ValueError("direct FITS writer supports only 2D primary images")

    h = fits.Header()
    h["SIMPLE"] = True
    h["BITPIX"] = int(bitpix)
    h["NAXIS"] = 2
    h["NAXIS1"] = int(array.shape[1])
    h["NAXIS2"] = int(array.shape[0])
    if header:
        for key, value in header.items():
            if value is not None and len(str(key)) <= 8:
                h[str(key)] = value
    header_bytes = h.tostring(endcard=True, padding=True).encode("ascii")
    data_bytes = int(array.shape[0] * array.shape[1] * np.dtype(storage_dtype).itemsize)
    padding = (2880 - (data_bytes % 2880)) % 2880
    tmp = path.with_name(f"{path.name}.tmp")
    if tmp.exists():
        tmp.unlink()
    with tmp.open("wb") as f:
        f.write(header_bytes)
        for chunk in _iter_direct_fits_data_chunks(data, target_dtype):
            f.write(chunk)
        if padding:
            f.write(b"\0" * padding)
    tmp.replace(path)


def write_fits_data(
    path: str | Path,
    data: np.ndarray,
    header: dict[str, Any] | None = None,
    dtype: Any = np.float32,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if fits_write_backend(data, dtype) == "direct_simple_primary":
        _write_simple_fits_direct(target, data, header, dtype)
        return
    hdu = fits.PrimaryHDU(np.asarray(data, dtype=dtype))
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

    def read_sampled(self, stride: int = 1, dtype=np.float32) -> np.ndarray:
        if self._data is None:
            raise RuntimeError("FitsImageReader is not open")
        step = max(1, int(stride))
        raw = self._data[::step, ::step]
        out = np.asarray(raw, dtype=np.float32)
        if self.blank is not None:
            mask = np.asarray(raw == self.blank)
            if np.any(mask):
                out = out.copy()
                out[mask] = np.nan
        if self.bscale != 1.0 or self.bzero != 0.0:
            out = out * np.float32(self.bscale) + np.float32(self.bzero)
        return np.asarray(out, dtype=dtype)

    def read_full_into(self, output: np.ndarray) -> np.ndarray:
        if self._data is None:
            raise RuntimeError("FitsImageReader is not open")
        if output.shape != (self.height, self.width):
            raise ValueError("output shape does not match FITS image shape")
        if output.dtype != np.float32:
            raise ValueError("read_full_into currently requires a float32 output buffer")
        raw = self._data
        np.copyto(output, raw, casting="unsafe")
        if self.blank is not None:
            mask = np.asarray(raw == self.blank)
            if np.any(mask):
                output[mask] = np.nan
        if self.bscale != 1.0 or self.bzero != 0.0:
            output *= np.float32(self.bscale)
            output += np.float32(self.bzero)
        return output

    def read_full(self, dtype=np.float32) -> np.ndarray:
        return self.read_tile(0, self.height, 0, self.width, dtype=dtype)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._hdul is not None:
            self._hdul.close()
        self._hdul = None
        self._data = None
        self.header = None
