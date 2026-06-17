from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.candidate_comparison_sweep import build_candidate_comparison_sweep


def _write_candidate(
    path: Path,
    *,
    candidate_id: str,
    passed: bool,
    elapsed_s: float,
    speedup: float,
    rms: float,
    p99: float,
    recommendation: str,
) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "candidate_comparison",
            "candidate_id": candidate_id,
            "summary": {
                "status": "passed" if passed else "failed",
                "passed": passed,
                "recommendation": recommendation,
                "baseline_elapsed_s": 18.0,
                "candidate_elapsed_s": elapsed_s,
                "elapsed_ratio_candidate_over_baseline": elapsed_s / 18.0,
                "candidate_speedup_vs_reference": speedup,
            },
            "deltas": {
                "reference_rms_relative_delta": 0.001,
                "reference_abs_diff_p99_relative_delta": -0.01,
            },
            "comparisons": {
                "candidate_vs_reference": {
                    "rms_diff": rms,
                    "abs_diff_p99": p99,
                },
                "candidate_vs_baseline": {
                    "rms_diff": 0.7,
                    "abs_diff_p99": 0.72,
                },
            },
            "checks": [
                {
                    "name": "candidate_acceptance_passed",
                    "required": True,
                    "passed": passed,
                }
            ],
        },
    )


def test_candidate_comparison_sweep_ranks_passed_candidate(tmp_path: Path) -> None:
    failed = tmp_path / "failed.json"
    passed = tmp_path / "passed.json"
    _write_candidate(
        failed,
        candidate_id="agreement_soft_downweight_initial",
        passed=False,
        elapsed_s=480.0,
        speedup=2.2,
        rms=0.00149,
        p99=0.00043,
        recommendation="hold_candidate",
    )
    _write_candidate(
        passed,
        candidate_id="agreement_soft_downweight_retry",
        passed=True,
        elapsed_s=26.0,
        speedup=42.0,
        rms=0.00150,
        p99=0.00043,
        recommendation="eligible_but_needs_runtime_sweep",
    )

    payload = build_candidate_comparison_sweep([failed, passed])

    assert payload["summary"]["passed"] is True
    assert payload["summary"]["passed_candidate_count"] == 1
    assert payload["summary"]["top_candidate_id"] == "agreement_soft_downweight_retry"
    assert payload["summary"]["recommendation"] == "run_runtime_sweep_for_top_candidate"


def test_cli_candidate_comparison_sweep_writes_outputs(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "sweep.json"
    markdown = tmp_path / "sweep.md"
    _write_candidate(
        candidate,
        candidate_id="agreement_soft_downweight_retry",
        passed=True,
        elapsed_s=26.0,
        speedup=42.0,
        rms=0.00150,
        p99=0.00043,
        recommendation="eligible_but_needs_runtime_sweep",
    )

    assert (
        main(
            [
                "candidate-comparison-sweep",
                "--comparison",
                str(candidate),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-no-passed",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["status"] == "passed"
    assert "Candidate Comparison Sweep" in markdown.read_text(encoding="utf-8")
