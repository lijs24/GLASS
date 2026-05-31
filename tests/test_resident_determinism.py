from __future__ import annotations

import math
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_determinism import build_resident_determinism_audit


def _write_run(
    path: Path,
    *,
    moving_catalog_hash: str = "mcat",
    selected_fit_hash: str = "fit",
    registration_status: str = "ok",
    final_status: str = "integrated",
    elapsed_s: float = 10.0,
    rms_px: float = 0.5,
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    write_json(
        path / "resident_artifacts.json",
        {
            "schema_version": 1,
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["F001", "F002"],
                    "resident_registration": {
                        "active_frame_count": 2,
                        "triangle_determinism_signature_mode": (
                            "catalog_descriptor_fit_exact_float32_sha256"
                        ),
                        "triangle_determinism_moving_frame_count": 1,
                        "triangle_determinism_threshold_count": 1,
                        "triangle_determinism_reference_combined_sha256": "ref-combined",
                        "triangle_determinism_moving_catalog_combined_sha256": moving_catalog_hash,
                        "triangle_determinism_selected_fit_combined_sha256": selected_fit_hash,
                        "triangle_determinism_trial_combined_sha256": "trial-combined",
                        "triangle_determinism": {
                            "moving": {
                                "F002": {
                                    "status": registration_status,
                                    "threshold_mode": "fixed",
                                    "selected_threshold": 350.0,
                                    "threshold_candidates": [350.0],
                                    "reference_catalog": {
                                        "sha256": "rcat",
                                        "stored_count": 48,
                                    },
                                    "moving_catalog": {
                                        "sha256": moving_catalog_hash,
                                        "stored_count": 48,
                                    },
                                    "reference_descriptor": {
                                        "sha256": "rdesc",
                                        "count": 282,
                                    },
                                    "moving_descriptor": {
                                        "sha256": "mdesc",
                                        "count": 256,
                                    },
                                    "selected_fit": {"sha256": selected_fit_hash},
                                    "trial_signature": {"sha256": "trial"},
                                }
                            }
                        },
                    },
                }
            ],
        },
    )
    write_json(
        path / "registration_results.json",
        {
            "results": [
                {
                    "frame_id": "F002",
                    "status": registration_status,
                    "matched_stars": 4,
                    "inliers": 4,
                    "rms_px": rms_px,
                    "matrix": [[1.0, 0.0, 1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]],
                }
            ]
        },
    )
    write_json(
        path / "frame_accounting.json",
        {
            "frames": [
                {
                    "frame_id": "F002",
                    "final_status": final_status,
                    "registration_status": registration_status,
                    "integration_status": "used" if final_status == "integrated" else "zero_weight",
                    "integration_weight": 1.0 if final_status == "integrated" else 0.0,
                }
            ]
        },
    )
    write_json(path / "run_timing.json", {"total_elapsed_s": elapsed_s})


def test_resident_determinism_audit_passes_identical_runs(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed_s=10.0)
    _write_run(candidate, elapsed_s=11.0)

    audit = build_resident_determinism_audit(baseline, candidate)

    assert audit["summary"]["passed"] is True
    assert audit["summary"]["frame_signature_difference_count"] == 0
    assert audit["timing"]["elapsed_delta_s"] == 1.0
    assert audit["baseline"]["registration_status_counts"] == {"ok": 1}


def test_resident_determinism_audit_reports_signature_and_status_drift(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline)
    _write_run(
        candidate,
        moving_catalog_hash="changed-catalog",
        selected_fit_hash="changed-fit",
        registration_status="failed",
        final_status="zero_weight",
    )

    audit = build_resident_determinism_audit(baseline, candidate)

    assert audit["summary"]["passed"] is False
    assert audit["summary"]["artifact_difference_count"] == 1
    assert audit["summary"]["frame_signature_difference_count"] == 1
    assert audit["summary"]["registration_difference_count"] == 1
    assert audit["summary"]["frame_accounting_difference_count"] == 1
    assert audit["summary"]["frame_signature_difference_type_counts"]["moving_catalog_hash"] == 1
    diff = audit["frame_signature_differences"][0]
    assert diff["frame_id"] == "F002"
    assert "moving_catalog_hash" in diff["difference_types"]
    assert "selected_fit_hash" in diff["difference_types"]


def test_resident_determinism_audit_treats_matching_nan_registration_values_as_equal(
    tmp_path: Path,
):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, registration_status="failed", final_status="zero_weight", rms_px=math.nan)
    _write_run(candidate, registration_status="failed", final_status="zero_weight", rms_px=math.nan)

    audit = build_resident_determinism_audit(baseline, candidate)

    assert audit["summary"]["passed"] is True
    assert audit["summary"]["registration_difference_count"] == 0


def test_resident_determinism_cli_writes_json_and_markdown(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"
    _write_run(baseline)
    _write_run(candidate)

    assert (
        main(
            [
                "resident-determinism",
                "--baseline-run",
                str(baseline),
                "--candidate-run",
                str(candidate),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-mismatch",
            ]
        )
        == 0
    )
    assert read_json(out)["summary"]["passed"] is True
    assert "Resident CUDA Determinism Audit" in markdown.read_text(encoding="utf-8")
