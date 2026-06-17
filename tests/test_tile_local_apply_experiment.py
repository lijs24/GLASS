from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_apply_experiment import build_tile_local_apply_experiment


def _write_run(
    root: Path,
    *,
    elapsed_s: float,
    applied: bool,
    application_status: str,
) -> None:
    root.mkdir(parents=True)
    write_json(
        root / "run_timing.json",
        {
            "schema_version": 1,
            "command": "run",
            "backend": "cuda",
            "memory_mode": "resident",
            "total_elapsed_s": elapsed_s,
            "stages": [{"stage": "resident_calibration_integration", "elapsed_s": elapsed_s, "status": "ok"}],
        },
    )
    (root / "run_command.txt").write_text(
        "glass run --backend cuda --until-stage integration --memory-mode resident",
        encoding="utf-8",
    )
    write_json(
        root / "frame_accounting.json",
        {
            "schema_version": 1,
            "artifact": "frame_accounting",
            "integration_source_stage": "resident_calibrated_stack",
            "frames": [],
            "summary": {
                "input_light_frames": 200,
                "integrated_frames": 193,
                "zero_weight_frames": 7,
                "registration_accepted_frames": 193,
                "final_status_counts": {"integrated": 193, "zero_weight": 7},
            },
        },
    )
    write_json(
        root / "integration_results.json",
        {
            "source_stage": "resident_calibrated_stack",
            "frame_weights": {"F000100": 1.0, "F000101": 1.0, "F000160": 0.0},
        },
    )
    write_json(
        root / "resident_artifacts.json",
        {
            "schema_version": 1,
            "backend": "cuda_resident_stack",
            "device": {"name": "Fixture GPU"},
            "artifacts": [
                {
                    "filter": "H",
                    "master_path": str(root / "integration" / "resident_master_H.fits"),
                    "coverage_map_path": str(root / "integration" / "resident_coverage_map_H.fits"),
                    "shape": {"height": 16, "width": 16},
                    "memory_estimate": {"estimated_peak_gib": 1.25},
                    "timing_s": {
                        "light_read_upload_calibrate": 2.0,
                        "resident_registration_warp": 1.0,
                        "resident_integration": 0.25,
                        "output_write": 0.5,
                    },
                    "resident_integration_weighting": {
                        "mode": "none",
                        "tile_local_policy_replay": {
                            "enabled": True,
                            "requested_mode": "apply" if applied else "record",
                            "effective_mode": "apply" if applied else "record",
                            "applied": applied,
                            "application_status": application_status,
                            "native_method": "ResidentCalibratedStack.integrate_tile_local_sigma_clip",
                            "native_timing_s": {"total": 0.0125},
                            "target_group": "focus",
                            "target_frame_ids": ["F000100", "F000101"],
                            "target_frame_count_applied": 2 if applied else None,
                            "target_frame_ids_missing": [],
                            "tile_count": 1,
                            "tile_count_applied": 1 if applied else None,
                            "multiplier_min": 2.0,
                            "multiplier_mean": 2.0,
                            "multiplier_max": 2.0,
                            "summary": {
                                "recommendation": "tile_local_replay_promising",
                                "known_direction_tiles": 1,
                                "moves_toward_reference": 1,
                                "moves_away_from_reference": 0,
                                "mean_abs_residual_before": 0.2,
                                "mean_abs_residual_after": 0.1,
                            },
                        },
                    },
                }
            ],
        },
    )


def _write_contract(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "name": "fixture_contract",
            "runtime": {
                "release_baseline_elapsed_s": 10.0,
                "max_runtime_regression_factor": 1.5,
                "external_reference_elapsed_s": 300.0,
                "min_speedup_vs_reference": 20.0,
            },
            "comparison": {
                "min_coverage_fraction": 0.95,
                "max_rms_diff": 0.01,
                "max_abs_diff_p99": 0.01,
            },
            "frame_accounting": {
                "required_input_light_frames": 200,
                "required_integrated_frames": 193,
                "required_zero_weight_frames": 7,
                "required_registration_accepted_frames": 193,
                "required_final_status_counts": {"integrated": 193, "zero_weight": 7},
            },
        },
    )


def _write_compare(path: Path, *, elapsed_s: float) -> None:
    write_json(
        path,
        {
            "shape_match": True,
            "rms_diff": 0.001,
            "abs_diff_p99": 0.002,
            "relative_rms_diff": 0.2,
            "timing": {
                "glass_time_seconds": elapsed_s,
                "reference_time_seconds": 300.0,
                "speedup_vs_reference": 300.0 / elapsed_s,
            },
            "comparison_region": {"coverage_fraction": 0.97, "compared_pixels": 1000},
        },
    )


def _write_replay(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "target_frame_ids": ["F000100", "F000101"],
            "tile_count": 1,
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "moves_away_from_reference": 0,
                "mean_abs_residual_before": 0.2,
                "mean_abs_residual_after": 0.1,
            },
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 4, "y1": 4},
                    "multiplier": 2.0,
                }
            ],
        },
    )


def test_build_tile_local_apply_experiment_passes_fixture(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    replay = tmp_path / "replay.json"
    contract = tmp_path / "contract.json"
    baseline_compare = tmp_path / "baseline_compare.json"
    candidate_compare = tmp_path / "candidate_compare.json"
    _write_run(baseline, elapsed_s=10.0, applied=False, application_status="validated_not_applied")
    _write_run(candidate, elapsed_s=11.0, applied=True, application_status="applied_winsorized_sigma")
    _write_replay(replay)
    _write_contract(contract)
    _write_compare(baseline_compare, elapsed_s=10.0)
    _write_compare(candidate_compare, elapsed_s=11.0)

    payload = build_tile_local_apply_experiment(
        baseline_run=baseline,
        candidate_run=candidate,
        replay=replay,
        benchmark_contract=contract,
        baseline_compare_json=baseline_compare,
        candidate_compare_json=candidate_compare,
    )

    assert payload["summary"]["passed"] is True
    assert payload["summary"]["recommendation"] == "promote_to_bounded_policy_sweep"
    assert payload["candidate"]["tile_local_policy"]["application_status"] == "applied_winsorized_sigma"


def test_cli_tile_local_apply_experiment_writes_outputs(tmp_path: Path):
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    replay = tmp_path / "replay.json"
    contract = tmp_path / "contract.json"
    candidate_compare = tmp_path / "candidate_compare.json"
    out = tmp_path / "apply_experiment.json"
    markdown = tmp_path / "apply_experiment.md"
    _write_run(baseline, elapsed_s=10.0, applied=False, application_status="validated_not_applied")
    _write_run(candidate, elapsed_s=11.0, applied=True, application_status="applied_winsorized_sigma")
    _write_replay(replay)
    _write_contract(contract)
    _write_compare(candidate_compare, elapsed_s=11.0)

    assert (
        main(
            [
                "tile-local-apply-experiment",
                "--baseline-run",
                str(baseline),
                "--candidate-run",
                str(candidate),
                "--replay",
                str(replay),
                "--benchmark-contract",
                str(contract),
                "--candidate-compare-json",
                str(candidate_compare),
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
    assert payload["summary"]["passed"] is True
    assert "Tile-Local Apply Experiment" in markdown.read_text(encoding="utf-8")
