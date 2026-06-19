from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np


class FastFitsUnsupported(ValueError):
    """Raised when the bounded fast FITS path should not read a file."""


@dataclass(frozen=True)
class SimpleFitsImageSpec:
    path: Path
    bitpix: int
    width: int
    height: int
    data_offset: int
    dtype: np.dtype
    bscale: float = 1.0
    bzero: float = 0.0
    blank: float | int | None = None

    @property
    def shape(self) -> tuple[int, int]:
        return self.height, self.width


_BITPIX_DTYPES: dict[int, str] = {
    8: "u1",
    16: ">i2",
    32: ">i4",
    64: ">i8",
    -32: ">f4",
    -64: ">f8",
}


def _split_value_comment(field: str) -> str:
    quoted = False
    result: list[str] = []
    index = 0
    while index < len(field):
        char = field[index]
        if char == "'":
            result.append(char)
            if quoted and index + 1 < len(field) and field[index + 1] == "'":
                result.append("'")
                index += 2
                continue
            quoted = not quoted
        elif char == "/" and not quoted:
            break
        else:
            result.append(char)
        index += 1
    return "".join(result).strip()


def _parse_card_value(card: str) -> Any:
    if len(card) < 10 or card[8] != "=":
        return None
    raw = _split_value_comment(card[10:])
    if not raw:
        return None
    if raw.startswith("'"):
        chars: list[str] = []
        index = 1
        while index < len(raw):
            char = raw[index]
            if char == "'":
                if index + 1 < len(raw) and raw[index + 1] == "'":
                    chars.append("'")
                    index += 2
                    continue
                break
            chars.append(char)
            index += 1
        return "".join(chars).rstrip()
    if raw == "T":
        return True
    if raw == "F":
        return False
    number = raw.replace("D", "E").replace("d", "e")
    try:
        if any(token in number for token in (".", "E", "e")):
            return float(number)
        return int(number)
    except ValueError:
        return raw


def _read_primary_header(path: Path) -> tuple[dict[str, Any], int]:
    header: dict[str, Any] = {}
    read_bytes = 0
    found_end = False
    with path.open("rb") as handle:
        while True:
            block = handle.read(2880)
            if not block:
                break
            if len(block) != 2880:
                raise FastFitsUnsupported("truncated FITS header block")
            read_bytes += len(block)
            for offset in range(0, len(block), 80):
                try:
                    card = block[offset : offset + 80].decode("ascii", errors="strict")
                except UnicodeDecodeError as exc:
                    raise FastFitsUnsupported("FITS primary header is not ASCII") from exc
                keyword = card[:8].strip()
                if keyword == "END":
                    found_end = True
                    break
                if keyword and keyword not in header:
                    value = _parse_card_value(card)
                    if value is not None:
                        header[keyword] = value
            if found_end:
                break
    if not found_end:
        raise FastFitsUnsupported("FITS primary header END card not found")
    return header, read_bytes


def simple_fits_image_spec(path: str | Path) -> SimpleFitsImageSpec:
    target = Path(path)
    header, data_offset = _read_primary_header(target)
    if header.get("SIMPLE") is not True:
        raise FastFitsUnsupported("not a simple primary FITS image")
    if int(header.get("NAXIS", -1)) != 2:
        raise FastFitsUnsupported("fast FITS reader supports only 2D primary images")
    bitpix = int(header.get("BITPIX", 0))
    dtype_name = _BITPIX_DTYPES.get(bitpix)
    if dtype_name is None:
        raise FastFitsUnsupported(f"unsupported BITPIX={bitpix}")
    width = int(header.get("NAXIS1", 0))
    height = int(header.get("NAXIS2", 0))
    if width <= 0 or height <= 0:
        raise FastFitsUnsupported("invalid NAXIS1/NAXIS2 dimensions")
    pcount = int(header.get("PCOUNT", 0) or 0)
    gcount = int(header.get("GCOUNT", 1) or 1)
    if pcount != 0 or gcount != 1:
        raise FastFitsUnsupported("random-groups FITS images are not supported by the fast reader")
    bscale = float(header.get("BSCALE", 1.0) or 1.0)
    bzero = float(header.get("BZERO", 0.0) or 0.0)
    blank = header.get("BLANK")
    data_bytes = width * height * np.dtype(dtype_name).itemsize
    if target.stat().st_size < data_offset + data_bytes:
        raise FastFitsUnsupported("FITS image data is truncated")
    return SimpleFitsImageSpec(
        path=target,
        bitpix=bitpix,
        width=width,
        height=height,
        data_offset=data_offset,
        dtype=np.dtype(dtype_name),
        bscale=bscale,
        bzero=bzero,
        blank=blank,
    )


def _materialize_spec(spec: SimpleFitsImageSpec, dtype: Any, output: np.ndarray | None) -> np.ndarray:
    raw = np.memmap(spec.path, dtype=spec.dtype, mode="r", offset=spec.data_offset, shape=spec.shape)
    if output is None:
        data = np.asarray(raw, dtype=np.float32)
    else:
        if output.shape != spec.shape:
            raise ValueError("output shape does not match FITS image shape")
        if output.dtype != np.float32:
            raise ValueError("fast FITS read into an output buffer requires float32")
        np.copyto(output, raw, casting="unsafe")
        data = output
    if spec.blank is not None:
        mask = np.asarray(raw == spec.blank)
        if np.any(mask):
            if data is not output:
                data = data.copy()
            data[mask] = np.nan
    if spec.bscale != 1.0 or spec.bzero != 0.0:
        data *= np.float32(spec.bscale)
        data += np.float32(spec.bzero)
    if output is not None:
        return output
    return np.asarray(data, dtype=np.dtype(dtype))


def read_simple_fits_image(
    path: str | Path,
    dtype: Any = np.float32,
    output: np.ndarray | None = None,
) -> np.ndarray:
    return _materialize_spec(simple_fits_image_spec(path), dtype, output)


def read_simple_fits_image_timed(
    path: str | Path,
    dtype: Any = np.float32,
    output: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    total_start = perf_counter()
    open_start = perf_counter()
    spec = simple_fits_image_spec(path)
    open_elapsed = perf_counter() - open_start
    materialize_start = perf_counter()
    data = _materialize_spec(spec, dtype, output)
    materialize_elapsed = perf_counter() - materialize_start
    return data, {
        "total": perf_counter() - total_start,
        "fits_open": open_elapsed,
        "fits_materialize_decode": materialize_elapsed,
        "fits_reader_backend": "fast_simple",
        "fits_fast_supported": True,
        "fits_fast_bitpix": int(spec.bitpix),
        "fits_fast_scaled": bool(spec.bscale != 1.0 or spec.bzero != 0.0 or spec.blank is not None),
    }


def read_simple_fits_image_native_direct_timed(
    path: str | Path,
    dtype: Any = np.float32,
    output: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    if np.dtype(dtype) != np.dtype(np.float32):
        raise ValueError("native direct FITS decode currently supports float32 output only")
    total_start = perf_counter()
    open_start = perf_counter()
    spec = simple_fits_image_spec(path)
    header_elapsed = perf_counter() - open_start
    if output is None:
        data = np.empty(spec.shape, dtype=np.float32)
    else:
        if output.shape != spec.shape:
            raise ValueError("output shape does not match FITS image shape")
        if output.dtype != np.float32:
            raise ValueError("native direct FITS read into an output buffer requires float32")
        if not output.flags.c_contiguous:
            raise ValueError("native direct FITS output buffer must be C-contiguous")
        data = output

    import glass_cuda

    native = glass_cuda.read_simple_fits_into_f32(
        spec.path,
        spec.data_offset,
        spec.height,
        spec.width,
        spec.bitpix,
        spec.bscale,
        spec.bzero,
        spec.blank,
        data,
    )
    native_read_s = float(native.get("file_read_s", 0.0) or 0.0)
    native_decode_s = float(native.get("decode_s", 0.0) or 0.0)
    native_open_s = float(native.get("file_open_s", 0.0) or 0.0)
    total_elapsed = perf_counter() - total_start
    return data, {
        "total": total_elapsed,
        "fits_open": header_elapsed + native_open_s,
        "fits_materialize_decode": native_read_s + native_decode_s,
        "fits_reader_backend": "native_direct_simple",
        "fits_fast_supported": True,
        "fits_fast_bitpix": int(spec.bitpix),
        "fits_fast_scaled": bool(spec.bscale != 1.0 or spec.bzero != 0.0 or spec.blank is not None),
        "fits_native_file_open_s": native_open_s,
        "fits_native_file_read_s": native_read_s,
        "fits_native_decode_s": native_decode_s,
        "fits_native_total_s": float(native.get("total_s", 0.0) or 0.0),
        "fits_native_bytes_read": int(native.get("bytes_read", 0) or 0),
        "fits_native_backend": str(native.get("backend", "native_direct_simple")),
    }


def read_simple_fits_u16be_raw_timed(
    path: str | Path,
    output: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    total_start = perf_counter()
    open_start = perf_counter()
    spec = simple_fits_image_spec(path)
    header_elapsed = perf_counter() - open_start
    if spec.bitpix != 16:
        raise FastFitsUnsupported("native_u16_gpu requires BITPIX=16 simple primary FITS")
    if spec.bscale != 1.0 or spec.bzero != 32768.0 or spec.blank is not None:
        raise FastFitsUnsupported("native_u16_gpu requires BSCALE=1, BZERO=32768, and no BLANK")
    byte_count = int(spec.width * spec.height * 2)
    if output is None:
        data = np.empty(byte_count, dtype=np.uint8)
    else:
        if output.dtype != np.uint8:
            raise ValueError("native_u16_gpu FITS raw output buffer requires uint8")
        if output.ndim != 1 or output.shape[0] != byte_count:
            raise ValueError("native_u16_gpu FITS raw output buffer must have height*width*2 bytes")
        if not output.flags.c_contiguous:
            raise ValueError("native_u16_gpu FITS raw output buffer must be C-contiguous")
        data = output

    import glass_cuda

    native = glass_cuda.read_simple_fits_raw_into_u8(
        spec.path,
        spec.data_offset,
        byte_count,
        data,
    )
    native_read_s = float(native.get("file_read_s", 0.0) or 0.0)
    native_decode_s = float(native.get("decode_s", 0.0) or 0.0)
    native_open_s = float(native.get("file_open_s", 0.0) or 0.0)
    total_elapsed = perf_counter() - total_start
    return data, {
        "total": total_elapsed,
        "fits_open": header_elapsed + native_open_s,
        "fits_materialize_decode": native_read_s + native_decode_s,
        "fits_reader_backend": "native_u16be_raw",
        "fits_fast_supported": True,
        "fits_fast_bitpix": int(spec.bitpix),
        "fits_fast_scaled": True,
        "fits_native_file_open_s": native_open_s,
        "fits_native_file_read_s": native_read_s,
        "fits_native_decode_s": native_decode_s,
        "fits_native_total_s": float(native.get("total_s", 0.0) or 0.0),
        "fits_native_bytes_read": int(native.get("bytes_read", 0) or 0),
        "fits_native_backend": str(native.get("backend", "native_u16be_raw")),
        "fits_raw_byte_count": byte_count,
        "fits_gpu_decode_staging": "u16be_bzero32768",
    }
