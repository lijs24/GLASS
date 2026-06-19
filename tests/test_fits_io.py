from __future__ import annotations

import numpy as np
import pytest
from astropy.io import fits

from glass.io.fits_fast import (
    FastFitsUnsupported,
    read_simple_fits_image,
    read_simple_fits_image_native_direct_timed,
    read_simple_fits_u16be_raw_timed,
    simple_fits_image_spec,
)
from glass.io.fits_io import FitsImageReader, read_fits_data, write_fits_data
from glass.engine.resident_cuda import _read_light_timed, _write_resident_outputs
from tests.conftest import cuda_module_or_skip


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


def test_fast_fits_reader_matches_astropy_scaled_primary_image(tmp_path):
    path = tmp_path / "scaled_fast.fits"
    raw = np.arange(20, dtype=np.int16).reshape(4, 5)
    hdu = fits.PrimaryHDU(raw)
    hdu.header["BSCALE"] = 1.5
    hdu.header["BZERO"] = 42.0
    hdu.writeto(path)

    spec = simple_fits_image_spec(path)
    fast = read_simple_fits_image(path)
    expected = read_fits_data(path)

    assert spec.shape == (4, 5)
    assert spec.bitpix == 16
    assert np.allclose(fast, expected)


def test_fast_fits_reader_maps_blank_to_nan(tmp_path):
    path = tmp_path / "blank_fast.fits"
    raw = np.arange(9, dtype=np.int16).reshape(3, 3)
    raw[1, 1] = -999
    hdu = fits.PrimaryHDU(raw)
    hdu.header["BLANK"] = -999
    hdu.writeto(path)

    fast = read_simple_fits_image(path)

    assert np.isnan(fast[1, 1])
    assert fast[0, 0] == 0


def test_fast_fits_reader_rejects_non_2d_primary(tmp_path):
    path = tmp_path / "cube.fits"
    fits.PrimaryHDU(np.zeros((2, 3, 4), dtype=np.float32)).writeto(path)

    with pytest.raises(FastFitsUnsupported, match="2D primary"):
        read_simple_fits_image(path)


def test_resident_light_timed_records_fast_or_legacy_backend(tmp_path):
    path = tmp_path / "light.fits"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    fits.PrimaryHDU(data).writeto(path)

    fast, fast_profile = _read_light_timed(path, fits_read_mode="auto")
    legacy, legacy_profile = _read_light_timed(path, fits_read_mode="astropy")

    assert np.allclose(fast, legacy)
    assert fast_profile["fits_reader_backend"] == "fast_simple"
    assert legacy_profile["fits_reader_backend"] == "astropy_scaled_memmap"
    assert fast_profile["fits_fast_fallback_reason"] == ""


def test_native_direct_fits_reader_decodes_into_pinned_output(tmp_path):
    module = cuda_module_or_skip()
    if not hasattr(module, "read_simple_fits_into_f32"):
        pytest.skip("native direct FITS decoder is not available")
    path = tmp_path / "native_direct_scaled_blank.fits"
    raw = np.arange(16, dtype=np.int16).reshape(4, 4)
    raw[2, 1] = -999
    hdu = fits.PrimaryHDU(raw)
    hdu.header["BSCALE"] = 2.5
    hdu.header["BZERO"] = 100.0
    hdu.header["BLANK"] = -999
    hdu.writeto(path)
    output = module.host_pinned_empty_f32(4, 4)

    decoded, profile = read_simple_fits_image_native_direct_timed(path, output=output)
    expected = read_fits_data(path)

    assert decoded is output
    assert profile["fits_reader_backend"] == "native_direct_simple"
    assert profile["fits_native_bytes_read"] == raw.size * raw.dtype.itemsize
    assert profile["fits_native_decode_s"] >= 0.0
    assert np.allclose(decoded, expected, equal_nan=True)


def test_native_u16_raw_fits_reader_reads_into_pinned_output(tmp_path):
    module = cuda_module_or_skip()
    if not module.native_extension_loaded() or not hasattr(module, "host_pinned_empty_u8"):
        pytest.skip("native uint8 pinned FITS reader is not available")
    path = tmp_path / "native_u16_raw.fits"
    physical = np.arange(20, dtype=np.uint16).reshape(4, 5) + np.uint16(1000)
    stored = (physical.astype(np.int32) - 32768).astype(np.int16)
    hdu = fits.PrimaryHDU(stored)
    hdu.header["BSCALE"] = 1.0
    hdu.header["BZERO"] = 32768.0
    hdu.writeto(path)
    output = module.host_pinned_empty_u8(physical.size * 2)

    raw, profile = read_simple_fits_u16be_raw_timed(path, output=output)
    decoded = raw.reshape(physical.shape + (2,))
    bits = (decoded[..., 0].astype(np.uint16) << np.uint16(8)) | decoded[..., 1].astype(np.uint16)
    physical_from_raw = bits ^ np.uint16(0x8000)

    assert raw is output
    assert profile["fits_reader_backend"] == "native_u16be_raw"
    assert profile["fits_gpu_decode_staging"] == "u16be_bzero32768"
    assert profile["fits_native_bytes_read"] == physical.size * 2
    assert np.array_equal(physical_from_raw, physical)
    assert np.allclose(read_fits_data(path), physical.astype(np.float32))


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
