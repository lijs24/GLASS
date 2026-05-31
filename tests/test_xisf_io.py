from __future__ import annotations

from pathlib import Path
import struct

import numpy as np

from glass.engine.contracts import ImageSource, TileWindow
from glass.io.fits_io import read_fits_data, write_fits_data
from glass.io.image_source import XisfImageSource
from glass.io.xisf_io import XisfImageReader, cache_xisf_to_fits, read_xisf_data
from glass.report.compare_report import compare_fits


def _write_minimal_xisf(path: Path, data: np.ndarray) -> None:
    image = np.asarray(data, dtype="<f4")
    height, width = image.shape
    payload = image.tobytes(order="C")
    offset = 4096
    xml = (
        'XISF0100<?xml version="1.0" encoding="UTF-8"?>'
        '<xisf version="1.0">'
        f'<Image geometry="{width}:{height}:1" sampleFormat="Float32" '
        f'location="attachment:{offset}:{len(payload)}" />'
        "</xisf>"
    ).encode("utf-8")
    if len(xml) > offset:
        raise AssertionError("test XISF header exceeded fixed offset")
    path.write_bytes(xml + b"\0" * (offset - len(xml)) + payload)


def _write_binary_header_xisf(path: Path, data: np.ndarray, fits_keywords: dict[str, str] | None = None) -> None:
    image = np.asarray(data, dtype="<f4")
    height, width = image.shape
    payload = image.tobytes(order="C")
    offset = 4096
    keywords = "".join(
        f'<FITSKeyword name="{name}" value="{value}"/>' for name, value in (fits_keywords or {}).items()
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<xisf version="1.0">'
        f'<Image geometry="{width}:{height}:1" sampleFormat="Float32" '
        f'location="attachment:{offset}:{len(payload)}">{keywords}</Image>'
        "</xisf>"
    ).encode("utf-8")
    if 16 + len(xml) > offset:
        raise AssertionError("test XISF header exceeded fixed offset")
    path.write_bytes(b"XISF0100" + struct.pack("<Q", len(xml)) + xml + b"\0" * (offset - 16 - len(xml)) + payload)


def test_read_uncompressed_float32_xisf(tmp_path: Path):
    path = tmp_path / "tiny.xisf"
    data = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
    _write_minimal_xisf(path, data)
    loaded = read_xisf_data(path)
    assert loaded.shape == (2, 2)
    assert loaded.dtype == np.float32
    assert np.allclose(loaded, data)


def test_read_binary_header_xisf_tile_and_cache(tmp_path: Path):
    path = tmp_path / "binary.xisf"
    cache = tmp_path / "cache.fits"
    data = np.arange(20, dtype=np.float32).reshape(4, 5)
    _write_binary_header_xisf(path, data, {"IMAGETYP": "Light", "FILTER": "'H'"})

    with XisfImageReader(path) as reader:
        tile = reader.read_tile(1, 4, 2, 5)

    cache_record = cache_xisf_to_fits(path, cache, tile_size=2)

    assert np.allclose(tile, data[1:4, 2:5])
    assert cache_record["tile_count"] == 6
    assert np.allclose(read_fits_data(cache), data)


def test_xisf_image_source_reads_tile_and_mask(tmp_path: Path):
    path = tmp_path / "source.xisf"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    data[1, 2] = np.nan
    _write_binary_header_xisf(path, data)
    window = TileWindow(y0=1, y1=3, x0=1, x1=4)

    source = XisfImageSource(path)
    assert isinstance(source, ImageSource)
    with source:
        tile = source.read_tile(window)
        mask = source.read_mask_tile(window)

    assert np.allclose(tile, data[1:3, 1:4], equal_nan=True)
    assert mask.summary() == {"valid": 5, "no_data": 1}


def test_compare_fits_to_xisf_with_linear_scale(tmp_path: Path):
    fits_path = tmp_path / "gp.fits"
    xisf_path = tmp_path / "ref.xisf"
    gp = np.array([[10, 20], [30, 40]], dtype=np.float32)
    ref = gp / np.float32(100.0)
    write_fits_data(fits_path, gp)
    _write_minimal_xisf(xisf_path, ref)

    comparison = compare_fits(fits_path, xisf_path)
    assert comparison["shape_match"] is True
    assert comparison["reference_format"] == "xisf"
    fit = comparison["linear_fit_to_reference"]
    assert fit["available"] is True
    assert abs(fit["scale"] - 0.01) < 1.0e-6
    assert fit["stats"]["max_abs_diff"] < 1.0e-6
