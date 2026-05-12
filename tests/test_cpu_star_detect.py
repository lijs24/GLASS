from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.cpu.star_detect import detect_stars
from gpwbpp.cpu.metrics import measure_quality
from gpwbpp.engine.quality import measure_quality_streaming
from gpwbpp.io.fits_io import write_fits_data
from gpwbpp.synthetic.generator import render_star_field


def test_cpu_star_detection_finds_synthetic_stars():
    stars = np.array([[16.0, 16.0, 1000.0], [8.0, 20.0, 800.0]], dtype=np.float32)
    image = render_star_field(32, 32, stars)
    detected = detect_stars(image, threshold_sigma=3.0)
    assert len(detected) >= 2
    assert abs(detected[0].x - 16.0) < 1.0
    assert abs(detected[0].y - 16.0) < 1.0


def test_cpu_quality_metrics_include_reference_inputs():
    stars = np.array([[16.0, 16.0, 1000.0], [8.0, 20.0, 800.0]], dtype=np.float32)
    image = render_star_field(32, 32, stars)
    quality = measure_quality("F1", "H", image)
    assert quality.star_count >= 2
    assert quality.fwhm_px is not None
    assert quality.eccentricity is not None
    assert quality.weight > 0


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
