from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.io.fits_io import write_fits_data
from gpwbpp.io.xisf_io import read_xisf_data
from gpwbpp.report.compare_report import compare_fits


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


def test_read_uncompressed_float32_xisf(tmp_path: Path):
    path = tmp_path / "tiny.xisf"
    data = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
    _write_minimal_xisf(path, data)
    loaded = read_xisf_data(path)
    assert loaded.shape == (2, 2)
    assert loaded.dtype == np.float32
    assert np.allclose(loaded, data)


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
