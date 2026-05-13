from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from glass.cli import main
from glass.io.fits_io import write_fits_data
from glass.report.compare_report import compare_fits


def _write(path: Path, value: float) -> None:
    write_fits_data(path, np.ones((4, 4), dtype=np.float32) * value)


def test_compare_fits_records_timing_speedup(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    _write(gp, 1.0)
    _write(ref, 1.5)
    result = compare_fits(gp, ref, glass_time_seconds=10.0, reference_time_seconds=25.0)
    assert result["shape_match"] is True
    assert result["timing"]["speedup_vs_reference"] == 2.5
    assert result["timing"]["glass_faster"] is True


def test_compare_cli_writes_timing_json(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    out = tmp_path / "compare.html"
    _write(gp, 2.0)
    _write(ref, 2.0)
    assert (
        main(
            [
                "compare",
                "--glass",
                str(gp),
                "--reference",
                str(ref),
                "--out",
                str(out),
                "--glass-time-seconds",
                "12",
                "--reference-time-seconds",
                "36",
                "--reference-label",
                "PixInsight WBPP",
            ]
        )
        == 0
    )
    payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["timing"]["reference_label"] == "PixInsight WBPP"
    assert payload["timing"]["speedup_vs_reference"] == 3.0


def test_compare_cli_records_candidate_transform(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    out = tmp_path / "compare.html"
    _write(gp, 1000.0)
    _write(ref, 1.0)
    assert (
        main(
            [
                "compare",
                "--glass",
                str(gp),
                "--reference",
                str(ref),
                "--out",
                str(out),
                "--glass-scale",
                "0.001",
                "--glass-offset",
                "0",
                "--clip-low",
                "0",
                "--clip-high",
                "1",
            ]
        )
        == 0
    )
    payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["candidate_transform"]["applied"] is True
    assert payload["candidate_transform"]["scale"] == 0.001
    assert payload["rms_diff"] == 0.0


def test_compare_can_ignore_border_for_metrics(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    out = tmp_path / "compare.html"
    candidate = np.ones((8, 8), dtype=np.float32)
    reference = np.ones((8, 8), dtype=np.float32)
    candidate[0, :] = 10.0
    candidate[:, 0] = 10.0
    write_fits_data(gp, candidate)
    write_fits_data(ref, reference)

    assert main(["compare", "--glass", str(gp), "--reference", str(ref), "--out", str(out), "--ignore-border-px", "1"]) == 0

    payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["comparison_region"]["ignore_border_px"] == 1
    assert payload["comparison_region"]["compared_shape"] == [6, 6]
    assert payload["rms_diff"] == 0.0
    assert payload["full_frame_stats"]["rms_diff"] > 0.0


def test_compare_can_mask_by_glass_coverage_map(tmp_path: Path):
    gp = tmp_path / "gp.fits"
    ref = tmp_path / "ref.fits"
    coverage = tmp_path / "coverage.fits"
    out = tmp_path / "compare.html"
    candidate = np.ones((6, 6), dtype=np.float32)
    reference = np.ones((6, 6), dtype=np.float32)
    candidate[0, :] = 20.0
    candidate[:, 0] = 20.0
    coverage_data = np.ones((6, 6), dtype=np.float32) * 5.0
    coverage_data[0, :] = 1.0
    coverage_data[:, 0] = 1.0
    write_fits_data(gp, candidate)
    write_fits_data(ref, reference)
    write_fits_data(coverage, coverage_data)

    assert (
        main(
            [
                "compare",
                "--glass",
                str(gp),
                "--reference",
                str(ref),
                "--out",
                str(out),
                "--glass-coverage-map",
                str(coverage),
                "--min-coverage",
                "5",
            ]
        )
        == 0
    )

    payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["comparison_region"]["coverage_valid_pixels"] == 25
    assert payload["comparison_region"]["coverage_fraction"] == 25 / 36
    assert payload["rms_diff"] == 0.0
    assert payload["full_frame_stats"]["rms_diff"] > 0.0


def test_compare_writes_diagnostic_artifacts(tmp_path: Path):
    y, x = np.mgrid[:32, :40]
    reference = (x + y).astype(np.float32)
    candidate = reference.copy()
    candidate[8:12, 10:14] += 5.0
    candidate[20:24, 25:30] -= 3.0

    glass = tmp_path / "glass.fits"
    ref = tmp_path / "reference.fits"
    out = tmp_path / "compare.html"
    diagnostics = tmp_path / "diagnostics"
    write_fits_data(glass, candidate)
    write_fits_data(ref, reference)

    assert (
        main(
            [
                "compare",
                "--glass",
                str(glass),
                "--reference",
                str(ref),
                "--out",
                str(out),
                "--diagnostics-dir",
                str(diagnostics),
                "--diagnostic-max-size",
                "64",
                "--hotspot-tile-size",
                "8",
            ]
        )
        == 0
    )

    comparison = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert comparison["shape_match"] is True
    assert comparison["diagnostics"]["directory"] == str(diagnostics)
    for name in [
        "glass_preview.png",
        "reference_preview.png",
        "abs_diff_preview.png",
        "signed_diff_preview.png",
        "hotspots.json",
    ]:
        assert (diagnostics / name).exists()
        assert (diagnostics / name).stat().st_size > 0
    hotspots = json.loads((diagnostics / "hotspots.json").read_text(encoding="utf-8"))
    assert hotspots
    assert hotspots[0]["p99_abs_diff"] >= 3.0
    html = out.read_text(encoding="utf-8")
    assert "Diagnostic Images" in html
    assert "Residual Hotspots" in html
    assert "signed_diff_preview.png" in html
    assert "<img" in html
