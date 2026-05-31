from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cpu.star_detect import detect_stars
from glass.cpu.metrics import measure_quality
from glass.engine.quality import measure_quality_streaming
from glass.io.fits_io import write_fits_data
from glass.synthetic.generator import render_star_field


def test_cpu_star_detection_finds_synthetic_stars():
    stars = np.array([[16.0, 16.0, 1000.0], [8.0, 20.0, 800.0]], dtype=np.float32)
    image = render_star_field(32, 32, stars)
    detected = detect_stars(image, threshold_sigma=3.0)
    assert len(detected) >= 2
    assert abs(detected[0].x - 16.0) < 1.0
    assert abs(detected[0].y - 16.0) < 1.0
    assert 2.0 < (detected[0].fwhm_px or 0.0) < 5.0
    assert (detected[0].eccentricity or 0.0) < 0.4
    assert (detected[0].snr or 0.0) > 10.0


def test_cpu_star_detection_reports_ellipticity():
    yy, xx = np.mgrid[0:64, 0:64]
    image = (1000.0 * np.exp(-(((xx - 32.0) / 2.3) ** 2 + ((yy - 32.0) / 1.0) ** 2) / 2.0)).astype(
        np.float32
    )
    detected = detect_stars(image, threshold_sigma=3.0)
    assert len(detected) == 1
    assert detected[0].fwhm_px is not None
    assert detected[0].eccentricity is not None
    assert detected[0].eccentricity > 0.7


def test_cpu_quality_metrics_include_reference_inputs():
    stars = np.array([[16.0, 16.0, 1000.0], [8.0, 20.0, 800.0]], dtype=np.float32)
    image = render_star_field(32, 32, stars)
    quality = measure_quality("F1", "H", image)
    assert quality.star_count >= 2
    assert quality.fwhm_px is not None
    assert quality.eccentricity is not None
    assert quality.snr > 0
    assert quality.weight > 0
    assert quality.weight_source == "combined_psf_snr_v1"
    assert quality.star_metrics["star_snr_median"] is not None


def test_streaming_quality_matches_cpu_metrics(tmp_path: Path):
    stars = np.array([[16.0, 16.0, 1000.0], [8.0, 20.0, 800.0]], dtype=np.float32)
    image = render_star_field(32, 32, stars)
    path = tmp_path / "quality.fits"
    write_fits_data(path, image)

    cpu = measure_quality("F1", "H", image)
    streaming = measure_quality_streaming("F1", "H", path, tile_size=9, scratch_dir=tmp_path)

    assert streaming["metric_source"] == "streaming_tile_reader"
    assert streaming["median_method"] == "median_scratch_memmap"
    assert streaming["star_count"] == cpu.star_count
    assert streaming["background_median"] == cpu.background_median
    assert abs(streaming["background_rms"] - cpu.background_rms) < 1.0e-5
    assert streaming["star_detector"] == "robust_local_maximum_moments_v1"
    assert streaming["weight_source"] == "combined_psf_snr_v1"
    assert streaming["fwhm_px"] is not None
    assert streaming["star_metrics"]["star_snr_median"] is not None


def test_streaming_quality_uses_saturation_fraction(tmp_path: Path):
    image = np.zeros((16, 16), dtype=np.float32)
    image[8, 8] = 1000.0
    path = tmp_path / "quality_sat.fits"
    write_fits_data(path, image)

    streaming = measure_quality_streaming(
        "F1",
        "H",
        path,
        tile_size=8,
        scratch_dir=tmp_path,
        saturated_pixels=4,
    )

    assert streaming["saturation_fraction"] == 4 / 256
    assert streaming["weight_components"]["saturation_penalty"] < 1.0
