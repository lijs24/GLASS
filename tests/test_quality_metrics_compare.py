from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.quality_metrics_compare import build_quality_metrics_compare


def _write_quality(path: Path, *, include_metrics: bool = True, soft_scale: float = 1.0) -> None:
    frame_quality = []
    for frame_id, star_count, fwhm, background, snr, score, weight in [
        ("F001", 100, 2.0 * soft_scale, 20.0 * soft_scale, 50.0 / soft_scale, 900.0 / soft_scale, 0.9 / soft_scale),
        ("F002", 80, 3.0 * soft_scale, 30.0 * soft_scale, 40.0 / soft_scale, 700.0 / soft_scale, 0.7 / soft_scale),
    ]:
        row = {"frame_id": frame_id, "quality_gate_status": "accepted"}
        if include_metrics:
            row.update(
                {
                    "star_count": star_count,
                    "fwhm_px": fwhm,
                    "eccentricity": 0.4 * soft_scale,
                    "background_rms": background,
                    "snr": snr,
                    "quality_score": score,
                    "weight": weight,
                }
            )
        frame_quality.append(row)
    write_json(path, {"schema_version": 1, "frame_quality": frame_quality})


def test_quality_metrics_compare_preserves_metric_summary(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_frame_quality.json"
    candidate = tmp_path / "candidate_frame_quality.json"
    _write_quality(baseline)
    _write_quality(candidate, soft_scale=1.05)

    payload = build_quality_metrics_compare(baseline, candidate)

    checks = {item["name"]: item for item in payload["checks"]}
    rows = {item["metric"]: item for item in payload["metric_rows"]}
    assert payload["status"] == "passed"
    assert checks["candidate_metric_summary_preserved"]["passed"] is True
    assert payload["baseline"]["metric_count"] == 7
    assert payload["candidate"]["metric_count"] == 7
    assert rows["fwhm_px"]["bad_median_ratio"] == 1.05
    assert rows["snr"]["bad_median_ratio"] == 1.05


def test_quality_metrics_compare_fails_when_candidate_drops_metrics(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_frame_quality.json"
    candidate = tmp_path / "candidate_frame_quality.json"
    _write_quality(baseline)
    _write_quality(candidate, include_metrics=False)

    payload = build_quality_metrics_compare(baseline, candidate)

    checks = {item["name"]: item for item in payload["checks"]}
    assert payload["status"] == "failed"
    assert checks["candidate_metric_summary_preserved"]["passed"] is False
    assert "fwhm_px" in checks["candidate_metric_summary_preserved"]["evidence"]["missing_metrics"]


def test_quality_metrics_compare_optional_bad_ratio_threshold(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_frame_quality.json"
    candidate = tmp_path / "candidate_frame_quality.json"
    _write_quality(baseline)
    _write_quality(candidate, soft_scale=1.4)

    payload = build_quality_metrics_compare(
        baseline,
        candidate,
        max_bad_median_ratio=1.2,
    )

    checks = {item["name"]: item for item in payload["checks"]}
    failing = checks["bad_median_ratio_within_limit"]["evidence"]["failing_metrics"]
    failing_metrics = {item["metric"] for item in failing}
    assert payload["status"] == "failed"
    assert checks["bad_median_ratio_within_limit"]["passed"] is False
    assert {"fwhm_px", "background_rms", "snr"}.issubset(failing_metrics)


def test_cli_quality_metrics_compare_writes_outputs_and_fails_on_failed(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_frame_quality.json"
    candidate = tmp_path / "candidate_frame_quality.json"
    out = tmp_path / "quality_compare.json"
    markdown = tmp_path / "quality_compare.md"
    _write_quality(baseline)
    _write_quality(candidate, include_metrics=False)

    result = main(
        [
            "quality-metrics-compare",
            "--baseline",
            str(baseline),
            "--candidate",
            str(candidate),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failed",
        ]
    )

    payload = read_json(out)
    text = markdown.read_text(encoding="utf-8")
    assert result == 2
    assert payload["artifact_type"] == "quality_metrics_compare"
    assert payload["status"] == "failed"
    assert "GLASS Quality Metrics Compare" in text
    assert "FAIL: candidate_metric_summary_preserved" in text
