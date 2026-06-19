from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_registration_matrix_sweep import build_resident_registration_matrix_sweep


def _matrix_compare(path: Path, *, passed: bool, max_delta: float, rms: float | None = None) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "resident_registration_matrix_compare",
            "status": "passed" if passed else "attention_required",
            "passed": passed,
            "failed_checks": [] if passed else ["translation_delta_within_limit"],
            "recommendation": {
                "status": "registration_matrices_ready" if passed else "fix_resident_transform_estimation",
                "next_target": "unit-test",
            },
            "summary": {
                "missing_frame_count": 0,
                "status_mismatch_count": 0,
                "reference_mismatch_count": 0,
                "translation_delta_px": {"count": 2, "max": max_delta, "mean": max_delta / 2.0, "p95": max_delta},
                "matrix_delta_frobenius": {"count": 2, "max": max_delta, "mean": max_delta / 2.0, "p95": max_delta},
            },
            "rows": [],
            "unit_test_rms": rms,
        },
    )


def _parity(path: Path, *, parity_passed: bool, rms: float, rejected_delta: int) -> None:
    write_json(
        path,
        {
            "artifact_type": "resident_parity_summary",
            "status": "passed" if parity_passed else "attention_required",
            "passed": parity_passed,
            "parity_passed": parity_passed,
            "compare": {"rms_diff": rms, "relative_rms_diff": rms / 100.0, "abs_diff_p99": rms * 2.0},
            "deltas": {"rejected_sample_delta": rejected_delta},
        },
    )


def test_resident_registration_matrix_sweep_ranks_matrix_and_parity(tmp_path: Path) -> None:
    bad = tmp_path / "bad_matrix.json"
    good = tmp_path / "good_matrix.json"
    bad_parity = tmp_path / "bad_parity.json"
    good_parity = tmp_path / "good_parity.json"
    _matrix_compare(bad, passed=False, max_delta=0.2)
    _matrix_compare(good, passed=True, max_delta=0.02)
    _parity(bad_parity, parity_passed=False, rms=2.0, rejected_delta=20)
    _parity(good_parity, parity_passed=True, rms=0.01, rejected_delta=0)

    payload = build_resident_registration_matrix_sweep(
        [f"bad={bad}", f"good={good}"],
        parity_entries=[f"bad={bad_parity}", f"good={good_parity}"],
    )

    assert payload["variant_count"] == 2
    assert payload["matrix_passed_count"] == 1
    assert payload["parity_passed_count"] == 1
    assert payload["best_variant"] == "good"
    assert payload["recommendation"]["status"] == "promote_candidate_for_benchmark_repeat"
    assert [row["label"] for row in payload["ranked_rows"]] == ["good", "bad"]


def test_resident_registration_matrix_sweep_cli_writes_outputs(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    parity = tmp_path / "parity.json"
    out = tmp_path / "sweep.json"
    markdown = tmp_path / "sweep.md"
    _matrix_compare(matrix, passed=False, max_delta=0.2)
    _parity(parity, parity_passed=False, rms=2.0, rejected_delta=20)

    assert (
        main(
            [
                "resident-registration-matrix-sweep",
                "--matrix-compare",
                f"candidate={matrix}",
                "--parity-summary",
                f"candidate={parity}",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )
    payload = read_json(out)
    assert payload["artifact_type"] == "resident_registration_matrix_sweep"
    assert payload["recommendation"]["status"] == "subpixel_refinement_still_blocked"
    assert "Resident Registration Matrix Sweep" in markdown.read_text(encoding="utf-8")
