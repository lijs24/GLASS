from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cpu.star_detect import detect_stars
from glass.cpu.metrics import measure_quality
from glass.engine.quality import measure_calibrated_quality, measure_quality_streaming
from glass.io.fits_io import write_fits_data
from glass.io.json_io import write_json
from glass.synthetic.generator import generate_synthetic_dataset, render_star_field


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


def test_streaming_quality_counts_saturation_threshold_by_tile(tmp_path: Path):
    image = np.zeros((16, 16), dtype=np.float32)
    image[2:4, 3:7] = 250.0
    path = tmp_path / "quality_threshold_sat.fits"
    write_fits_data(path, image)

    streaming = measure_quality_streaming(
        "F1",
        "H",
        path,
        tile_size=5,
        scratch_dir=tmp_path,
        saturation_level=200.0,
    )

    assert streaming["saturated_pixel_count"] == 8
    assert streaming["saturation_fraction"] == 8 / 256
    assert streaming["saturation_level"] == 200.0
    assert streaming["saturation_source"] == "threshold"
    assert streaming["weight_components"]["saturation_penalty"] < 1.0


def test_calibrated_quality_gate_excludes_saturated_reference(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    bad_stars = np.array(
        [[18.0, 18.0, 1200.0], [34.0, 28.0, 1000.0], [44.0, 42.0, 900.0]],
        dtype=np.float32,
    )
    good_stars = np.array([[18.0, 18.0, 1000.0], [42.0, 38.0, 900.0]], dtype=np.float32)
    bad_path = run / "bad.fits"
    good_path = run / "good.fits"
    write_fits_data(bad_path, render_star_field(64, 64, bad_stars))
    write_fits_data(good_path, render_star_field(64, 64, good_stars))
    write_json(
        run / "calibration_artifacts.json",
        {
            "calibrated_lights": [
                {"frame_id": "bad", "path": str(bad_path), "dq_summary": {"saturated": 200}},
                {"frame_id": "good", "path": str(good_path), "dq_summary": {"saturated": 0}},
            ]
        },
    )
    write_json(
        run / "processing_plan.json",
        {"registration_policy": {"min_stars": 2, "quality_max_saturation_fraction": 0.01}},
    )

    result = measure_calibrated_quality(run, tile_size=16)
    by_id = {item["frame_id"]: item for item in result["frame_quality"]}

    assert result["reference_frame_id"] == "good"
    assert result["reference_selection_fallback"] is False
    assert result["quality_gate_summary"]["accepted_count"] == 1
    assert result["quality_gate_summary"]["rejected_count"] == 1
    assert by_id["good"]["quality_gate_status"] == "accepted"
    assert by_id["good"]["reference_candidate"] is True
    assert by_id["bad"]["quality_gate_status"] == "rejected"
    assert by_id["bad"]["reference_candidate"] is False
    assert any("saturation_fraction" in warning for warning in by_id["bad"]["quality_gate_warnings"])


def test_calibrated_quality_gate_uses_saturation_threshold_policy(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    stars = np.array([[18.0, 18.0, 1000.0], [42.0, 38.0, 900.0]], dtype=np.float32)
    good = render_star_field(64, 64, stars)
    bad = good.copy()
    bad[2:8, 2:8] = 10000.0
    bad_path = run / "bad_threshold.fits"
    good_path = run / "good_threshold.fits"
    write_fits_data(bad_path, bad)
    write_fits_data(good_path, good)
    write_json(
        run / "calibration_artifacts.json",
        {
            "calibrated_lights": [
                {"frame_id": "bad", "path": str(bad_path), "dq_summary": {}},
                {"frame_id": "good", "path": str(good_path), "dq_summary": {}},
            ]
        },
    )
    write_json(
        run / "processing_plan.json",
        {
            "registration_policy": {
                "min_stars": 2,
                "quality_saturation_level": 5000.0,
                "quality_max_saturation_fraction": 0.005,
            }
        },
    )

    result = measure_calibrated_quality(run, tile_size=16)
    by_id = {item["frame_id"]: item for item in result["frame_quality"]}

    assert by_id["bad"]["saturated_pixel_count"] == 36
    assert by_id["bad"]["saturation_source"] == "threshold"
    assert by_id["bad"]["saturation_fraction"] == 36 / 4096
    assert by_id["bad"]["quality_gate_status"] == "rejected"
    assert any("saturation_fraction" in warning for warning in by_id["bad"]["quality_gate_warnings"])
    assert by_id["good"]["saturated_pixel_count"] == 0
    assert by_id["good"]["quality_gate_status"] == "accepted"
    assert result["reference_frame_id"] == "good"


def test_calibrated_quality_gate_scales_min_stars_for_tiny_synthetic_frames(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    run.mkdir()
    generate_synthetic_dataset(data, frames=1, width=24, height=24)
    light_path = sorted((data / "light").glob("*.fits"))[0]
    write_json(
        run / "calibration_artifacts.json",
        {"calibrated_lights": [{"frame_id": "tiny", "path": str(light_path), "dq_summary": {}}]},
    )

    result = measure_calibrated_quality(run, tile_size=8)
    quality = result["frame_quality"][0]

    assert quality["quality_gate_min_stars_configured"] == 8
    assert quality["quality_gate_min_stars_effective"] < quality["quality_gate_min_stars_configured"]
    assert quality["star_count"] >= quality["quality_gate_min_stars_effective"]
    assert quality["quality_gate_status"] == "accepted"
    assert result["quality_gate_summary"]["fallback_used"] is False
