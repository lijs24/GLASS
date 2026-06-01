from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_registration_triage import build_resident_registration_triage


def _frame(
    frame_id: str,
    *,
    status: str = "ok",
    agreement_status: str = "audit_only",
    agreement_score: float = 0.5,
    reference_signature: str = "ref-a",
    selected_fit_signature: str | None = None,
    failure_reasons: list[str] | None = None,
) -> dict:
    return {
        "frame_id": frame_id,
        "status": status,
        "is_triangle": True,
        "failure_reasons": failure_reasons or [],
        "agreement_status": agreement_status,
        "agreement_score": agreement_score,
        "agreement_reason": "below_min_score" if agreement_status == "failed" else "ok",
        "pixel_rms_adu": 200.0,
        "pixel_ncc": 0.9,
        "fit_rms_px": 0.6,
        "inliers": 6,
        "determinism": {
            "reference_catalog_signature": reference_signature,
            "reference_descriptor_signature": f"{reference_signature}-desc",
            "moving_catalog_signature": f"{frame_id}-moving",
            "moving_descriptor_signature": f"{frame_id}-desc",
            "selected_fit_signature": selected_fit_signature or f"{frame_id}-fit",
            "trial_signature": f"{frame_id}-trial",
        },
    }


def _write_audit(path: Path, variant_id: str, frames: list[dict]) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "resident_registration_candidate_audit",
            "variant_id": variant_id,
            "status": "passed",
            "summary": {"frame_count": len(frames)},
            "frames": frames,
        },
    )


def test_resident_registration_triage_reports_extra_rejections_and_signature_drift(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_candidate_audit.json"
    candidate = tmp_path / "candidate_candidate_audit.json"
    _write_audit(
        baseline,
        "baseline",
        [
            _frame("F001", agreement_score=0.42, reference_signature="ref-a"),
            _frame("F002", agreement_score=0.44, reference_signature="ref-a"),
        ],
    )
    _write_audit(
        candidate,
        "threshold_005",
        [
            _frame("F001", agreement_score=0.41, reference_signature="ref-b", selected_fit_signature="F001-fit-b"),
            _frame(
                "F002",
                status="failed",
                agreement_status="failed",
                agreement_score=0.03,
                reference_signature="ref-b",
                selected_fit_signature="F002-fit-b",
                failure_reasons=["registration_status_failed", "agreement_gate_failed"],
            ),
        ],
    )

    payload = build_resident_registration_triage(baseline, [candidate])

    assert payload["summary"]["extra_failed_variant_count"] == 1
    assert payload["summary"]["reference_catalog_drift_variant_count"] == 1
    assert payload["recommendation"]["status"] == "deterministic_catalog_required"
    row = payload["rows"][0]
    assert row["extra_failed_frame_ids"] == ["F002"]
    assert row["signature_change_counts"]["reference_catalog_signature"] == 2
    assert row["signature_change_counts"]["selected_fit_signature"] == 2
    assert row["extra_failed_frames"][0]["candidate_agreement_score"] == 0.03


def test_resident_registration_triage_cli_writes_outputs_and_can_fail_on_extra_rejections(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline_candidate_audit.json"
    candidate = tmp_path / "candidate_candidate_audit.json"
    out = tmp_path / "triage.json"
    markdown = tmp_path / "triage.md"
    _write_audit(baseline, "baseline", [_frame("F001")])
    _write_audit(
        candidate,
        "candidate",
        [
            _frame(
                "F001",
                status="failed",
                agreement_status="failed",
                agreement_score=0.02,
                failure_reasons=["agreement_gate_failed"],
            )
        ],
    )

    assert (
        main(
            [
                "resident-registration-triage",
                "--baseline-audit",
                str(baseline),
                "--candidate-audit",
                str(candidate),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-extra-rejections",
            ]
        )
        == 2
    )
    payload = read_json(out)
    assert payload["audit_type"] == "resident_registration_rejection_triage"
    assert payload["summary"]["extra_failed_variant_count"] == 1
    assert "Resident Registration Rejection Triage" in markdown.read_text(encoding="utf-8")
