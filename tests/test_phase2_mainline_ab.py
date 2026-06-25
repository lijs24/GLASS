from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import write_json
from glass.report.phase2_mainline_ab import build_phase2_mainline_ab


def _write_run(
    root: Path,
    *,
    elapsed: float,
    master_bytes: bytes = b"same",
    frame_index_alignment: bool = True,
) -> None:
    integration = root / "integration"
    integration.mkdir(parents=True)
    (integration / "resident_master_H.fits").write_bytes(master_bytes)
    (integration / "resident_weight_map_H.fits").write_bytes(b"weight")
    (integration / "resident_coverage_map_H.fits").write_bytes(b"coverage")
    (integration / "resident_low_rejection_map_H.fits").write_bytes(b"low")
    (integration / "resident_high_rejection_map_H.fits").write_bytes(b"high")
    (integration / "resident_dq_map_H.fits").write_bytes(b"dq")
    write_json(
        root / "run_timing.json",
        {
            "schema_version": 1,
            "total_elapsed_s": elapsed,
            "stages": [{"stage": "resident_calibration_integration", "elapsed_s": elapsed}],
        },
    )
    write_json(root / "pipeline_contract.json", {"passed": True, "status": "passed"})
    write_json(root / "resident_result_contract.json", {"passed": True, "status": "passed"})
    write_json(
        root / "resident_component_timing.json",
        {
            "status": "passed",
            "components": [
                {
                    "component": "resident_light_read_upload_calibrate",
                    "elapsed_s": 3.0,
                    "required": True,
                    "status": "ok",
                },
                {
                    "component": "resident_integration",
                    "elapsed_s": 2.0,
                    "required": True,
                    "status": "ok",
                },
            ],
        },
    )
    write_json(
        root / "resident_artifacts.json",
        {
            "schema_version": 1,
            "artifacts": [
                {
                    "timing_s": {
                        "light_read_upload_calibrate": 3.0,
                        "resident_integration": 2.0,
                        "output_write": 0.1,
                    },
                    "dq_provenance_summary": {
                        "frame_count": 200,
                        "active_frame_count": 193,
                    },
                }
            ],
        },
    )
    if frame_index_alignment:
        write_json(
            root / "resident_frame_masks.json",
            {
                "artifact": "resident_frame_mask_contract",
                "summary": {
                    "frame_count": 200,
                    "active_frame_count": 193,
                    "masked_frame_count": 7,
                    "passed": True,
                    "frame_index_alignment_contract": {
                        "checked": True,
                        "passed": True,
                        "weight_mismatch_frame_count": 0,
                        "weight_missing_frame_count": 0,
                        "weight_mismatch_frame_ids": [],
                        "weight_missing_frame_ids": [],
                    },
                },
                "groups": [],
            },
        )


def test_phase2_mainline_ab_passes_for_matching_maps(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed=10.0)
    _write_run(candidate, elapsed=10.5)

    payload = build_phase2_mainline_ab(
        baseline,
        candidate,
        max_elapsed_ratio=1.1,
        min_active_frame_count=190,
    )

    assert payload["passed"] is True
    assert payload["summary"]["elapsed_ratio"] == 1.05
    assert payload["summary"]["largest_component"]["component"] == "resident_light_read_upload_calibrate"
    assert payload["map_comparison"]["all_hashes_match"] is True
    assert payload["summary"]["frame_index_alignment_passed"] is True


def test_phase2_mainline_ab_fails_without_candidate_frame_index_alignment(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed=10.0)
    _write_run(candidate, elapsed=10.5, frame_index_alignment=False)

    payload = build_phase2_mainline_ab(baseline, candidate)

    assert payload["passed"] is False
    assert "candidate_frame_index_alignment_contract_pass" in [
        check["name"] for check in payload["failed_checks"]
    ]
    assert payload["candidate_frame_index_alignment"]["status"] == "missing_resident_frame_masks"


def test_phase2_mainline_ab_fails_hash_drift_when_required(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed=10.0)
    _write_run(candidate, elapsed=10.5, master_bytes=b"different")

    payload = build_phase2_mainline_ab(baseline, candidate)

    assert payload["passed"] is False
    assert "tracked_integration_maps_hash_match" == payload["failed_checks"][0]["name"]
    assert payload["map_comparison"]["mismatch_count"] == 1


def test_phase2_mainline_ab_cli_writes_artifacts_and_exit_code(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    out = tmp_path / "ab.json"
    markdown = tmp_path / "ab.md"
    _write_run(baseline, elapsed=10.0)
    _write_run(candidate, elapsed=12.0, master_bytes=b"different")

    code = main(
        [
            "phase2-mainline-ab",
            "--baseline-run",
            str(baseline),
            "--candidate-run",
            str(candidate),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--max-elapsed-ratio",
            "1.1",
            "--fail-on-failed",
        ]
    )

    assert code == 2
    assert out.exists()
    assert markdown.exists()
