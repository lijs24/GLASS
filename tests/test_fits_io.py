from __future__ import annotations

import numpy as np
from astropy.io import fits

from glass.io.fits_io import FitsImageReader, read_fits_data, write_fits_data
from glass.engine.resident_cuda import _write_resident_outputs


def test_fits_image_reader_applies_bscale_bzero_per_tile(tmp_path):
    path = tmp_path / "scaled.fits"
    raw = np.arange(16, dtype=np.int16).reshape(4, 4)
    hdu = fits.PrimaryHDU(raw)
    hdu.header["BSCALE"] = 2.0
    hdu.header["BZERO"] = 10.0
    hdu.writeto(path)
    expected = raw.astype(np.float32) * 2.0 + 10.0
    with FitsImageReader(path) as reader:
        assert reader.scaled is True
        assert reader.shape == (4, 4)
        assert np.allclose(reader.read_tile(1, 3, 1, 4), expected[1:3, 1:4])
    assert np.allclose(read_fits_data(path), expected)


def test_fits_image_reader_maps_blank_to_nan(tmp_path):
    path = tmp_path / "blank.fits"
    raw = np.arange(9, dtype=np.int16).reshape(3, 3)
    raw[1, 1] = -999
    hdu = fits.PrimaryHDU(raw)
    hdu.header["BLANK"] = -999
    hdu.writeto(path)
    with FitsImageReader(path) as reader:
        tile = reader.read_tile(0, 3, 0, 3)
    assert np.isnan(tile[1, 1])
    assert tile[0, 0] == 0


def test_write_fits_data_can_preserve_integer_count_maps(tmp_path):
    path = tmp_path / "coverage.fits"
    counts = np.array([[0, 1, 2], [30, 200, 32767]], dtype=np.int16)

    write_fits_data(path, counts, {"IMAGETYP": "coverage"}, dtype=np.int16)

    with fits.open(path, do_not_scale_image_data=True) as hdul:
        assert hdul[0].header["BITPIX"] == 16
        assert hdul[0].data.dtype == np.dtype(">i2")
        assert np.array_equal(hdul[0].data, counts)


def test_write_resident_outputs_parallel_records_storage_and_timings(tmp_path):
    master = np.arange(9, dtype=np.float32).reshape(3, 3)
    counts = np.array([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0], [6.0, 7.0, 8.0]], dtype=np.float32)
    specs = [
        {
            "name": "master",
            "path": tmp_path / "master.fits",
            "data": master,
            "header": {"IMAGETYP": "master"},
            "dtype": np.float32,
        },
        {
            "name": "coverage",
            "path": tmp_path / "coverage.fits",
            "data": counts,
            "header": {"IMAGETYP": "coverage"},
            "dtype": np.int16,
            "round_counts": True,
        },
    ]

    elapsed, breakdown, storage, workers = _write_resident_outputs(specs, max_workers=2)

    assert elapsed >= 0.0
    assert workers == 2
    assert set(breakdown) == {"master", "coverage"}
    assert storage["master"]["dtype"] == "float32"
    assert storage["coverage"]["dtype"] == "int16"
    assert storage["coverage"]["estimated_data_bytes"] == counts.size * np.dtype(np.int16).itemsize
    with fits.open(tmp_path / "coverage.fits", do_not_scale_image_data=True) as hdul:
        assert hdul[0].header["BITPIX"] == 16
        assert np.array_equal(hdul[0].data, counts.astype(np.int16))
