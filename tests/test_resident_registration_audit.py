from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_registration_audit import build_resident_registration_audit


def _write_resident_registration_fixture(run: Path) -> None:
    run.mkdir()
    write_json(
        run / "registration_results.json",
        {
            "schema_version": 1,
            "source_stage": "resident_calibrated_stack",
            "transform_model": "similarity_cuda_triangle",
            "results": [
                {
                    "frame_id": "light_001",
                    "reference_frame_id": "light_001",
                    "transform_model": "similarity_cuda_triangle",
                    "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    "matched_stars": 1,
                    "inliers": 1,
                    "rms_px": 0.0,
                    "status": "reference",
                    "warnings": ["resident CUDA triangle descriptor registration"],
                },
                {
                    "frame_id": "light_002",
                    "reference_frame_id": "light_001",
                    "transform_model": "similarity_cuda_triangle",
                    "matrix": [[1.0, 0.0, 3.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]],
                    "matched_stars": 42,
                    "inliers": 40,
                    "rms_px": 0.41,
                    "status": "ok",
                    "warnings": [
                        "triangle_threshold_mode=auto_mean_std",
                        "selected_triangle_threshold=42.0",
                        "reference_stars=64",
                        "moving_stars=61",
                        "reference_descriptors=310",
                        "moving_descriptors=298",
                        "triangle_candidate_count=128",
                        "triangle_descriptor_fit_best_reduction_mode=block_reduce",
                        "triangle_descriptor_fit_batch=true",
                        "triangle_pixel_refine_mode=native_batch",
                        "triangle_pixel_refine_fast_coarse=false",
                        "triangle_pixel_refine_effective_coarse_stride=4",
                        "triangle_pixel_refine_requested_final_stride=8",
                        "triangle_fit_rms_px=0.41",
                        "triangle_pixel_rms_adu_batch=12.5",
                        "triangle_pixel_ncc_batch=0.97",
                        "triangle_quality_gate_status=ok",
                        "triangle_catalog_selector=grid_top_nms",
                        "triangle_catalog_batch=native_batch",
                        "triangle_catalog_timing_model=batch",
                        "triangle_catalog_sort_mode=stable_flux",
                        "triangle_catalog_topk_mode=per_cell",
                        "triangle_grid_top_per_cell=2",
                        "triangle_nms_scan_candidates=96",
                        "triangle_nms_min_separation_px=48.0",
                        "triangle_determinism_selected_fit_signature=abc123",
                        "triangle_determinism_trial_signature=trial123",
                        "triangle_trials="
                        + str(
                            [
                                {
                                    "threshold": 42.0,
                                    "status": "ok",
                                    "inliers": 40,
                                    "rms_px": 0.41,
                                    "candidate_count": 128,
                                },
                                {
                                    "threshold": 50.0,
                                    "status": "failed",
                                    "inliers": 4,
                                    "rms_px": 3.5,
                                    "candidate_count": 7,
                                },
                            ]
                        ),
                    ],
                },
                {
                    "frame_id": "light_003",
                    "reference_frame_id": "light_001",
                    "transform_model": "similarity_cuda_triangle",
                    "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    "matched_stars": 0,
                    "inliers": 0,
                    "rms_px": 0.0,
                    "status": "failed",
                    "warnings": [
                        "resident triangle descriptor registration found no accepted fit",
                        "triangle_trials="
                        + str(
                            [
                                {
                                    "threshold": 42.0,
                                    "status": "too_few_stars",
                                    "reference_stored": 2,
                                    "moving_stored": 1,
                                }
                            ]
                        ),
                    ],
                },
            ],
        },
    )
    write_json(
        run / "resident_artifacts.json",
        {
            "schema_version": 1,
            "artifacts": [
                {
                    "resident_registration": {
                        "mode": "similarity_cuda_triangle",
                        "active_frame_count": 2,
                        "triangle_grid_top_per_cell": 2,
                        "triangle_nms_min_separation_px": 48.0,
                        "triangle_determinism_signature_mode": "catalog_descriptor_fit_exact_float32_sha256",
                        "triangle_determinism_moving_frame_count": 2,
                        "triangle_determinism_trial_combined_sha256": "combined",
                    },
                    "fine_timing": {
                        "registration_component_seconds": {
                            "triangle_moving_catalog": 0.75,
                            "triangle_descriptor_fit": 0.21,
                            "triangle_pixel_refine": 0.9,
                        }
                    },
                }
            ],
        },
    )


def test_resident_registration_audit_summarizes_triangle_candidates(tmp_path: Path):
    run = tmp_path / "run"
    _write_resident_registration_fixture(run)

    audit = build_resident_registration_audit(run)

    assert audit["passed"] is True
    assert audit["summary"]["frame_count"] == 3
    assert audit["summary"]["triangle_frame_count"] == 3
    assert audit["summary"]["failed_triangle_frame_count"] == 1
    assert audit["summary"]["failure_reason_counts"]["no_accepted_fit"] == 1
    assert audit["summary"]["candidate_count_stats"]["median"] == 128.0
    assert audit["summary"]["pixel_ncc_stats"]["median"] == 0.97
    assert audit["resident_registration"]["triangle_grid_top_per_cell"] == 2
    assert audit["registration_component_seconds"]["triangle_pixel_refine"] == 0.9
    frame = {item["frame_id"]: item for item in audit["frames"]}["light_002"]
    assert frame["trial_summary"]["ok_trial_count"] == 1
    assert frame["trial_summary"]["total_candidate_count"] == 135
    assert frame["determinism"]["selected_fit_signature"] == "abc123"


def test_resident_registration_audit_cli_writes_outputs_and_can_fail_on_registration_failures(tmp_path: Path):
    run = tmp_path / "run"
    out = tmp_path / "resident_registration_audit.json"
    markdown = tmp_path / "resident_registration_audit.md"
    _write_resident_registration_fixture(run)

    assert main(["resident-registration-audit", "--run", str(run), "--out", str(out), "--markdown", str(markdown)]) == 0
    payload = read_json(out)
    assert payload["audit_type"] == "resident_registration_candidate_audit"
    assert "Resident Registration Candidate Audit" in markdown.read_text(encoding="utf-8")

    failed = tmp_path / "resident_registration_audit_failed.json"
    assert (
        main(
            [
                "resident-registration-audit",
                "--run",
                str(run),
                "--out",
                str(failed),
                "--fail-on-registration-failures",
            ]
        )
        == 2
    )
