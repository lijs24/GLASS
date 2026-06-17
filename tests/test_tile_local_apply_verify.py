from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_apply_verify import build_tile_local_apply_verification


def _write_images(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    reference = np.full((8, 8), 10.0, dtype=np.float32)
    baseline = reference.copy()
    candidate = reference.copy()
    baseline[2:6, 2:6] += 4.0
    candidate[2:6, 2:6] += 1.0
    coverage = np.full((8, 8), 3.0, dtype=np.float32)

    baseline_path = tmp_path / "baseline.fits"
    candidate_path = tmp_path / "candidate.fits"
    reference_path = tmp_path / "reference.fits"
    coverage_path = tmp_path / "coverage.fits"
    replay_path = tmp_path / "replay.json"
    write_fits_data(baseline_path, baseline)
    write_fits_data(candidate_path, candidate)
    write_fits_data(reference_path, reference)
    write_fits_data(coverage_path, coverage)
    write_json(
        replay_path,
        {
            "schema_version": 1,
            "artifact_type": "tile_local_policy_replay",
            "target_frame_ids": ["F1"],
            "target_group": "focus",
            "tile_count": 1,
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 2, "y0": 2, "x1": 6, "y1": 6},
                    "signed_residual_reference_units_before": 0.4,
                    "signed_residual_reference_units_after": 0.1,
                    "moves_toward_reference": True,
                }
            ],
        },
    )
    return baseline_path, candidate_path, reference_path, coverage_path, replay_path


def test_tile_local_apply_verify_measures_improved_tile(tmp_path: Path) -> None:
    baseline, candidate, reference, coverage, replay = _write_images(tmp_path)

    payload = build_tile_local_apply_verification(
        baseline=baseline,
        candidate=candidate,
        reference=reference,
        replay=replay,
        coverage_map=coverage,
        min_coverage=2.0,
    )

    assert payload["summary"]["passed"] is True
    assert payload["summary"]["mean_abs_residual_before"] == 4.0
    assert payload["summary"]["mean_abs_residual_after"] == 1.0
    assert payload["summary"]["signed_mean_improved_tiles"] == 1
    assert payload["tiles"][0]["measured_mean_abs_improved"] is True
    assert payload["tiles"][0]["measured_signed_mean_improved"] is True
    assert payload["tiles"][0]["compared_pixels"] == 16


def test_cli_tile_local_apply_verify_writes_outputs(tmp_path: Path) -> None:
    baseline, candidate, reference, coverage, replay = _write_images(tmp_path)
    out = tmp_path / "verify.json"
    markdown = tmp_path / "verify.md"

    assert (
        main(
            [
                "tile-local-apply-verify",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--reference",
                str(reference),
                "--replay",
                str(replay),
                "--coverage-map",
                str(coverage),
                "--min-coverage",
                "2",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-failed",
            ]
        )
        == 0
    )
    payload = read_json(out)
    assert payload["summary"]["status"] == "passed"
    assert "Tile-Local Apply Verification" in markdown.read_text(encoding="utf-8")
