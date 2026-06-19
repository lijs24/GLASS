from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_registration_matrix_compare import build_resident_registration_matrix_compare


def _row(
    frame_id: str,
    *,
    reference_frame_id: str = "F001",
    status: str = "ok",
    tx: float = 0.0,
    ty: float = 0.0,
    model: str = "similarity",
) -> dict:
    return {
        "frame_id": frame_id,
        "reference_frame_id": reference_frame_id,
        "transform_model": model,
        "matrix": [[1.0, 0.0, tx], [0.0, 1.0, ty], [0.0, 0.0, 1.0]],
        "matched_stars": 12,
        "inliers": 10,
        "rms_px": 0.25,
        "status": status,
        "warnings": [],
    }


def _write_registration(path: Path, rows: list[dict], *, model: str = "similarity") -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "source_stage": "unit_test",
            "transform_model": model,
            "results": rows,
        },
    )


def test_resident_registration_matrix_compare_passes_for_matching_matrices(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_registration_results.json"
    candidate = tmp_path / "candidate_registration_results.json"
    rows = [_row("F001", status="reference"), _row("F002", tx=-3.0, ty=2.0)]
    _write_registration(baseline, rows)
    _write_registration(
        candidate,
        [_row("F001", status="reference"), _row("F002", tx=-3.02, ty=2.01, model="external_matrix")],
        model="external_matrix",
    )

    payload = build_resident_registration_matrix_compare(
        baseline,
        candidate,
        max_translation_delta_px=0.05,
        max_matrix_delta_frobenius=0.05,
    )

    assert payload["passed"] is True
    assert payload["status"] == "passed"
    assert payload["recommendation"]["status"] == "registration_matrices_ready"
    assert payload["summary"]["common_row_count"] == 2
    assert payload["summary"]["translation_delta_px"]["max"] < 0.05
    assert payload["failed_checks"] == []


def test_resident_registration_matrix_compare_flags_transform_delta(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_registration_results.json"
    candidate = tmp_path / "candidate_registration_results.json"
    _write_registration(baseline, [_row("F001", status="reference"), _row("F002", tx=-3.0, ty=2.0)])
    _write_registration(
        candidate,
        [_row("F001", status="reference"), _row("F002", tx=4.0, ty=-1.0, model="similarity_cuda_triangle")],
        model="similarity_cuda_triangle",
    )

    payload = build_resident_registration_matrix_compare(
        baseline,
        candidate,
        max_translation_delta_px=0.5,
        max_matrix_delta_frobenius=0.5,
    )

    assert payload["passed"] is False
    assert payload["status"] == "attention_required"
    assert payload["recommendation"]["status"] == "fix_resident_transform_estimation"
    assert "translation_delta_within_limit" in payload["failed_checks"]
    assert "matrix_delta_within_limit" in payload["failed_checks"]
    assert payload["worst_translation_rows"][0]["frame_id"] == "F002"
    assert payload["worst_translation_rows"][0]["translation_delta_px"] > 7.0


def test_resident_registration_matrix_compare_cli_writes_outputs_and_can_fail(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_registration_results.json"
    candidate = tmp_path / "candidate_registration_results.json"
    out = tmp_path / "matrix_compare.json"
    markdown = tmp_path / "matrix_compare.md"
    _write_registration(baseline, [_row("F001", status="reference"), _row("F002", tx=-3.0, ty=2.0)])
    _write_registration(
        candidate,
        [_row("F001", status="reference"), _row("F002", tx=4.0, ty=-1.0)],
    )

    assert (
        main(
            [
                "resident-registration-matrix-compare",
                "--baseline-registration",
                str(baseline),
                "--candidate-registration",
                str(candidate),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--max-translation-delta-px",
                "0.5",
                "--max-matrix-delta-frobenius",
                "0.5",
                "--fail-on-failure",
            ]
        )
        == 2
    )
    payload = read_json(out)
    assert payload["artifact_type"] == "resident_registration_matrix_compare"
    assert payload["passed"] is False
    assert "Resident Registration Matrix Compare" in markdown.read_text(encoding="utf-8")
