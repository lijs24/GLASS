from __future__ import annotations

import numpy as np
import pytest
from astropy.io import fits

from glass.io.fits_fast import (
    FastFitsUnsupported,
    native_u16_gpu_fits_eligibility,
    read_simple_fits_image,
    read_simple_fits_image_native_direct_timed,
    read_simple_fits_u16be_raw_batch_timed,
    read_simple_fits_u16be_raw_timed,
    simple_fits_image_spec,
)
from glass.engine.resident_cuda import _read_light_timed, _write_resident_outputs
from glass.io.fits_io import (
    FitsImageReader,
    _iter_direct_fits_data_chunks,
    fits_write_backend,
    fits_write_profile,
    read_fits_data,
    write_fits_data,
)
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
    cached_output = module.host_pinned_empty_u8(physical.size * 2)
    cached_raw, cached_profile = read_simple_fits_u16be_raw_timed(
        path,
        output=cached_output,
        spec=simple_fits_image_spec(path),
    )
    decoded = raw.reshape(physical.shape + (2,))
    bits = (decoded[..., 0].astype(np.uint16) << np.uint16(8)) | decoded[..., 1].astype(np.uint16)
    physical_from_raw = bits ^ np.uint16(0x8000)

    assert raw is output
    assert cached_raw is cached_output
    assert profile["fits_reader_backend"] == "native_u16be_raw"
    assert profile["fits_header_cache_hit"] is False
    assert cached_profile["fits_header_cache_hit"] is True
    assert cached_profile["fits_open"] >= 0.0
    assert profile["fits_gpu_decode_staging"] == "u16be_bzero32768"
    assert profile["fits_native_bytes_read"] == physical.size * 2
    assert cached_profile["fits_native_bytes_read"] == physical.size * 2
    assert np.array_equal(physical_from_raw, physical)
    assert np.array_equal(cached_raw, raw)
    assert np.allclose(read_fits_data(path), physical.astype(np.float32))


def test_native_u16_raw_fits_batch_reader_reads_into_pinned_outputs(tmp_path):
    module = cuda_module_or_skip()
    if (
        not module.native_extension_loaded()
        or not hasattr(module, "host_pinned_empty_u8")
        or not hasattr(module, "read_simple_fits_raw_batch_into_u8")
    ):
        pytest.skip("native uint8 batch FITS reader is not available")
    paths = []
    physical_frames = []
    outputs = []
    specs = []
    for frame_index in range(2):
        path = tmp_path / f"native_u16_raw_batch_{frame_index}.fits"
        physical = (
            np.arange(20, dtype=np.uint16).reshape(4, 5)
            + np.uint16(1000 + frame_index * 100)
        )
        stored = (physical.astype(np.int32) - 32768).astype(np.int16)
        hdu = fits.PrimaryHDU(stored)
        hdu.header["BSCALE"] = 1.0
        hdu.header["BZERO"] = 32768.0
        hdu.writeto(path)
        paths.append(path)
        physical_frames.append(physical)
        outputs.append(module.host_pinned_empty_u8(physical.size * 2))
        specs.append(simple_fits_image_spec(path))

    raw_outputs, profiles, batch_profile = read_simple_fits_u16be_raw_batch_timed(
        paths,
        outputs,
        specs=specs,
        max_workers=2,
    )

    assert raw_outputs == outputs
    assert batch_profile["fits_reader_backend"] == "native_u16be_raw_batch"
    assert batch_profile["fits_native_batch_frame_count"] == 2
    assert batch_profile["fits_native_batch_worker_count"] == 2
    assert batch_profile["fits_header_cache_hit_count"] == 2
    for raw, profile, physical in zip(raw_outputs, profiles, physical_frames, strict=True):
        decoded = raw.reshape(physical.shape + (2,))
        bits = (decoded[..., 0].astype(np.uint16) << np.uint16(8)) | decoded[..., 1].astype(np.uint16)
        physical_from_raw = bits ^ np.uint16(0x8000)
        assert profile["fits_reader_backend"] == "native_u16be_raw_batch"
        assert profile["fits_header_cache_hit"] is True
        assert profile["fits_native_batch_frame_count"] == 2
        assert np.array_equal(physical_from_raw, physical)


def test_native_u16_gpu_fits_eligibility_is_header_only(tmp_path):
    compatible = tmp_path / "compatible_u16.fits"
    incompatible = tmp_path / "incompatible_f32.fits"
    physical = np.arange(12, dtype=np.uint16).reshape(3, 4) + np.uint16(100)
    stored = (physical.astype(np.int32) - 32768).astype(np.int16)
    hdu = fits.PrimaryHDU(stored)
    hdu.header["BSCALE"] = 1.0
    hdu.header["BZERO"] = 32768.0
    hdu.writeto(compatible)
    fits.PrimaryHDU(np.asarray(physical, dtype=np.float32)).writeto(incompatible)

    compatible_probe = native_u16_gpu_fits_eligibility(compatible, expected_shape=(3, 4))
    incompatible_probe = native_u16_gpu_fits_eligibility(incompatible, expected_shape=(3, 4))
    shape_probe = native_u16_gpu_fits_eligibility(compatible, expected_shape=(4, 3))

    assert compatible_probe["eligible"] is True
    assert compatible_probe["reason"] == ""
    assert compatible_probe["bitpix"] == 16
    assert incompatible_probe["eligible"] is False
    assert incompatible_probe["reason"] == "bitpix_not_16:-32"
    assert shape_probe["eligible"] is False
    assert shape_probe["reason"] == "shape_mismatch"


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


def test_write_fits_data_direct_simple_primary_roundtrips_float32(tmp_path):
    path = tmp_path / "master.fits"
    data = np.array([[1.5, np.nan, -2.0], [0.0, 42.25, 8.0]], dtype=np.float32)

    assert fits_write_backend(data, np.float32) == "direct_simple_primary"
    write_fits_data(path, data, {"IMAGETYP": "master", "FILTER": "H"}, dtype=np.float32)

    assert path.stat().st_size % 2880 == 0
    with fits.open(path, memmap=True) as hdul:
        assert hdul[0].header["BITPIX"] == -32
        assert hdul[0].header["NAXIS1"] == 3
        assert hdul[0].header["NAXIS2"] == 2
        assert hdul[0].header["FILTER"] == "H"
        assert hdul[0].data.dtype == np.dtype(">f4")
        assert np.array_equal(hdul[0].data, data, equal_nan=True)


def test_direct_fits_writer_chunks_big_endian_payload():
    data = np.arange(30, dtype=np.float32).reshape(5, 6)
    chunk_bytes = 2 * data.shape[1] * data.dtype.itemsize

    chunks = [bytes(chunk) for chunk in _iter_direct_fits_data_chunks(data, np.float32, max_chunk_bytes=chunk_bytes)]
    decoded = np.frombuffer(b"".join(chunks), dtype=">f4").reshape(data.shape)

    assert len(chunks) == 3
    assert max(len(chunk) for chunk in chunks) <= chunk_bytes
    assert np.array_equal(decoded, data)


def test_fits_write_profile_records_chunked_direct_strategy():
    data = np.zeros((5, 6), dtype=np.float32)
    chunk_bytes = 2 * data.shape[1] * data.dtype.itemsize

    profile = fits_write_profile(data, np.float32, max_chunk_bytes=chunk_bytes)

    assert profile["writer_backend"] == "direct_simple_primary"
    assert profile["writer_strategy"] == "direct_simple_primary_chunked_big_endian"
    assert profile["direct_streaming"] is True
    assert profile["rows_per_chunk"] == 2
    assert profile["chunk_count"] == 3
    assert profile["estimated_data_bytes"] == data.nbytes


def test_write_fits_data_falls_back_for_non_2d_primary(tmp_path):
    path = tmp_path / "cube.fits"
    data = np.zeros((2, 3, 4), dtype=np.float32)

    assert fits_write_backend(data, np.float32) == "astropy_primary_hdu"
    write_fits_data(path, data, dtype=np.float32)

    with fits.open(path, memmap=True) as hdul:
        assert hdul[0].data.shape == (2, 3, 4)


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
    assert storage["master"]["writer_backend"] == "direct_simple_primary"
    assert storage["master"]["writer_profile"]["writer_strategy"] == "direct_simple_primary_chunked_big_endian"
    assert storage["coverage"]["dtype"] == "int16"
    assert storage["coverage"]["writer_backend"] == "direct_simple_primary"
    assert storage["coverage"]["writer_profile"]["writer_strategy"] == "direct_simple_primary_chunked_big_endian"
    assert storage["coverage"]["estimated_data_bytes"] == counts.size * np.dtype(np.int16).itemsize
    with fits.open(tmp_path / "coverage.fits", do_not_scale_image_data=True) as hdul:
        assert hdul[0].header["BITPIX"] == 16
        assert np.array_equal(hdul[0].data, counts.astype(np.int16))
