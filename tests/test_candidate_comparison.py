from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.candidate_comparison import build_candidate_comparison


def _write_run(path: Path, *, elapsed_s: float) -> None:
    path.mkdir(parents=True)
    write_json(
        path / "run_timing.json",
        {
            "schema_version": 1,
            "backend": "cuda",
            "memory_mode": "resident",
            "total_elapsed_s": elapsed_s,
        },
    )
    write_json(
        path / "resident_artifacts.json",
        {
            "schema_version": 1,
            "backend": "cuda_resident_stack",
            "device": {"name": "Test GPU", "memory_total_mib": 96_000},
            "artifacts": [
                {
                    "master_path": str(path / "integration" / "resident_master_H.fits"),
                    "coverage_map_path": str(path / "integration" / "resident_coverage_map_H.fits"),
                    "timing_s": {
                        "master_build_or_load": 1.0,
                        "light_read_upload_calibrate": 10.0,
                        "resident_registration_warp": 2.0,
                        "resident_integration": 0.5,
                        "output_write": 1.0,
                    },
                }
            ],
        },
    )
    write_json(
        path / "frame_accounting.json",
        {
            "integration_source_stage": "resident_calibrated_stack",
            "summary": {
                "input_light_frames": 200,
                "integrated_frames": 193,
                "zero_weight_frames": 7,
                "registration_accepted_frames": 193,
                "final_status_counts": {"integrated": 193, "zero_weight": 7},
            },
            "frames": [],
        },
    )


def _write_compare(path: Path, *, rms: float, p99: float) -> None:
    write_json(
        path,
        {
            "shape_match": True,
            "mean_diff": 0.0,
            "rms_diff": rms,
            "abs_diff_p50": 0.00005,
            "abs_diff_p90": 0.0001,
            "abs_diff_p99": p99,
            "abs_diff_p999": 0.001,
            "relative_rms_diff": 0.2,
            "comparison_region": {
                "compared_pixels": 1234,
                "coverage_fraction": 0.96,
                "ignore_border_px": 0,
                "min_coverage": 190,
            },
            "timing": {},
        },
    )


def _write_acceptance(path: Path, *, passed: bool = True) -> None:
    write_json(
        path,
        {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "checks": [{"name": "minimum_speedup", "passed": passed}],
            "speedup_summary": {
                "speedup_vs_wbpp": 42.0,
                "glass": {
                    "elapsed_s": 26.0,
                    "weighted_frame_count": 193,
                    "zero_weight_frame_count": 7,
                },
            },
        },
    )


def test_candidate_comparison_accepts_candidate_but_flags_slowdown(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed_s=18.0)
    _write_run(candidate, elapsed_s=26.0)
    baseline_compare = tmp_path / "baseline_compare.json"
    candidate_compare = tmp_path / "candidate_compare.json"
    candidate_vs_baseline = tmp_path / "candidate_vs_baseline.json"
    acceptance = tmp_path / "candidate_acceptance.json"
    _write_compare(baseline_compare, rms=0.00149, p99=0.00044)
    _write_compare(candidate_compare, rms=0.00150, p99=0.00043)
    _write_compare(candidate_vs_baseline, rms=0.0002, p99=0.0008)
    _write_acceptance(acceptance)

    payload = build_candidate_comparison(
        baseline_run=baseline,
        candidate_run=candidate,
        candidate_id="agreement_soft_downweight",
        baseline_compare_json=baseline_compare,
        candidate_compare_json=candidate_compare,
        candidate_vs_baseline_json=candidate_vs_baseline,
        candidate_acceptance_json=acceptance,
        min_speedup_vs_reference=20.0,
    )

    assert payload["summary"]["passed"] is True
    assert payload["summary"]["recommendation"] == "eligible_but_needs_runtime_sweep"
    assert payload["deltas"]["candidate_slower_than_baseline"] is True
    assert payload["checks"][0]["name"] == "candidate_acceptance_passed"


def test_cli_candidate_comparison_writes_outputs(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_run(baseline, elapsed_s=20.0)
    _write_run(candidate, elapsed_s=19.0)
    baseline_compare = tmp_path / "baseline_compare.json"
    candidate_compare = tmp_path / "candidate_compare.json"
    acceptance = tmp_path / "candidate_acceptance.json"
    out = tmp_path / "candidate_comparison.json"
    markdown = tmp_path / "candidate_comparison.md"
    _write_compare(baseline_compare, rms=0.0015, p99=0.00044)
    _write_compare(candidate_compare, rms=0.00149, p99=0.00043)
    _write_acceptance(acceptance)

    assert (
        main(
            [
                "candidate-comparison",
                "--baseline-run",
                str(baseline),
                "--candidate-run",
                str(candidate),
                "--candidate-id",
                "agreement_soft_downweight",
                "--baseline-compare-json",
                str(baseline_compare),
                "--candidate-compare-json",
                str(candidate_compare),
                "--candidate-acceptance-json",
                str(acceptance),
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
    assert payload["summary"]["recommendation"] == "eligible_for_broader_sweep"
    assert "Candidate Comparison" in markdown.read_text(encoding="utf-8")
