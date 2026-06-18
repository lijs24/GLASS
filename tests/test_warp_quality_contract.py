from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.warp_quality import build_warp_quality_contract, write_warp_quality_contract


def _write_warp_run(tmp_path: Path, *, valid_pixels: int = 16, include_registered: bool = True) -> Path:
    run = tmp_path / "run"
    run.mkdir()
    registered = run / "registered.fits"
    coverage = run / "coverage.fits"
    dq = run / "dq.fits"
    image = np.ones((4, 4), dtype=np.float32)
    if include_registered:
        write_fits_data(registered, image)
    write_fits_data(coverage, image)
    write_fits_data(dq, np.zeros_like(image))
    write_json(
        run / "registration_results.json",
        {
            "schema_version": 1,
            "registration_results": [
                {"frame_id": "F1", "status": "reference", "registration_validation": {"accepted": True}},
                {"frame_id": "F2", "status": "failed", "registration_validation": {"accepted": False}},
            ],
        },
    )
    write_json(
        run / "warp_results.json",
        {
            "schema_version": 1,
            "interpolation": "bilinear",
            "interpolator_registry": ["nearest", "bilinear", "bicubic", "lanczos3"],
            "warp_results": [
                {
                    "frame_id": "F1",
                    "registered_path": str(registered),
                    "coverage_path": str(coverage),
                    "dq_mask_path": str(dq),
                    "dq_summary": {"valid": valid_pixels},
                    "registration_status": "reference",
                    "interpolation": "bilinear",
                    "warp_model": "integer_translation_nearest",
                    "tile_size": 4,
                    "tile_count": 1,
                    "valid_pixels": valid_pixels,
                }
            ],
            "skipped_frames": [
                {
                    "frame_id": "F2",
                    "status": "failed",
                    "reason": "registration did not produce an accepted transform",
                }
            ],
        },
    )
    return run


def test_warp_quality_contract_passes_artifact_and_registration_checks(tmp_path: Path):
    run = _write_warp_run(tmp_path)

    contract = build_warp_quality_contract(
        run,
        min_valid_fraction=1.0,
        max_skipped_frames=1,
        require_artifacts=True,
        require_all_registered=True,
        pixel_verify=True,
        pixel_verify_tile_size=2,
    )

    assert contract["artifact_type"] == "warp_quality_contract"
    assert contract["passed"] is True
    assert contract["summary"]["output_count"] == 1
    assert contract["summary"]["skipped_count"] == 1
    assert contract["summary"]["artifact_ready_count"] == 1
    assert contract["summary"]["min_valid_fraction"] == 1.0
    assert contract["summary"]["pixel_verified_output_count"] == 1
    assert contract["summary"]["pixel_failed_output_count"] == 0
    assert contract["outputs"][0]["pixel_verification"]["status"] == "passed"
    assert contract["summary"]["missing_warp_for_accepted_registration_count"] == 0
    assert contract["failed_checks"] == []


def test_warp_quality_contract_fails_missing_artifact_and_fraction(tmp_path: Path):
    run = _write_warp_run(tmp_path, valid_pixels=8, include_registered=False)

    contract = build_warp_quality_contract(
        run,
        min_valid_fraction=0.75,
        max_skipped_frames=0,
        require_artifacts=True,
        require_all_registered=True,
        pixel_verify=True,
        pixel_verify_tile_size=2,
    )

    assert contract["passed"] is False
    failed = set(contract["failed_checks"])
    assert "warp_output_artifacts_ready" in failed
    assert "warp_valid_fraction_meets_threshold" in failed
    assert "warp_skipped_frames_within_threshold" in failed
    assert "warp_pixel_verification_passed" in failed
    output = contract["outputs"][0]
    assert "registered_path_exists" in output["failed_checks"]
    assert "valid_fraction_meets_threshold" in output["failed_checks"]
    assert "pixel_verification_passed" in output["failed_checks"]


def test_write_warp_quality_contract_markdown(tmp_path: Path):
    run = _write_warp_run(tmp_path)
    contract = build_warp_quality_contract(run, require_artifacts=True)
    out = tmp_path / "warp_quality_contract.json"
    markdown = tmp_path / "warp_quality_contract.md"

    write_warp_quality_contract(out, contract, markdown=markdown)

    assert read_json(out)["artifact_type"] == "warp_quality_contract"
    text = markdown.read_text(encoding="utf-8")
    assert "Warp Quality Contract" in text
    assert "artifact_ready=True" in text
