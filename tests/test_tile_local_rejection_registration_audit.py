from __future__ import annotations

from pathlib import Path

import pytest

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.tile_local_rejection_registration_audit import build_tile_local_rejection_registration_audit


def _frame_row(frame_id: str, *, high: int, score: float, ncc: float, rms: float) -> dict:
    valid = 100
    rejected = high + 1
    return {
        "frame_id": frame_id,
        "valid_pixels": valid,
        "high_rejected_pixels": high,
        "low_rejected_pixels": 1,
        "rejected_pixels": rejected,
        "accepted_fraction": (valid - rejected) / valid,
        "triangle_agreement_score": score,
        "triangle_pixel_ncc_batch": ncc,
        "triangle_pixel_rms_adu_batch": 100.0,
        "registration_rms_px": rms,
        "triangle_agreement_weight_multiplier": score / 0.8,
        "triangle_agreement_status": "downweighted" if score < 0.8 else "ok",
        "normalized_delta_contribution_mean": 1.0,
    }


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    contribution = tmp_path / "contribution.json"
    frame_search = tmp_path / "frame_family_search.json"
    write_json(
        contribution,
        {
            "artifact_type": "resident_tile_contribution_capture",
            "focus_ids": ["F001", "F002"],
            "control_ids": ["F003"],
            "tiles": [
                {
                    "index": 0,
                    "top_frames": [
                        _frame_row("F001", high=8, score=0.4, ncc=0.7, rms=0.8),
                        _frame_row("F002", high=6, score=0.45, ncc=0.75, rms=0.7),
                        _frame_row("F003", high=0, score=0.9, ncc=0.95, rms=0.4),
                    ],
                },
                {
                    "index": 1,
                    "top_frames": [
                        _frame_row("F001", high=7, score=0.4, ncc=0.7, rms=0.8),
                        _frame_row("F002", high=5, score=0.45, ncc=0.75, rms=0.7),
                        _frame_row("F003", high=1, score=0.9, ncc=0.95, rms=0.4),
                    ],
                },
            ],
        },
    )
    write_json(
        frame_search,
        {
            "artifact_type": "tile_local_frame_family_search",
            "top_candidate": {"candidate_id": "F001-F002", "frame_ids": ["F001", "F002"]},
        },
    )
    return contribution, frame_search


def test_tile_local_rejection_registration_audit_flags_focus_hotspot(tmp_path: Path) -> None:
    contribution, frame_search = _write_inputs(tmp_path)

    payload = build_tile_local_rejection_registration_audit(
        contribution,
        frame_family_search=frame_search,
        high_rejection_threshold=0.01,
        low_agreement_score_threshold=0.5,
    )

    summary = payload["summary"]
    assert payload["artifact_type"] == "tile_local_rejection_registration_audit"
    assert summary["recommendation"] == "prioritize_registration_agreement_rejection_interaction"
    assert summary["focus_minus_control_high_rejected_fraction_mean"] == pytest.approx(0.06)
    assert summary["top_frame_family_high_rejection_excess_frame_count"] == 2
    assert summary["low_agreement_high_rejection_frame_count"] == 2
    assert summary["top_high_rejection_frames"][0]["frame_id"] == "F001"


def test_cli_tile_local_rejection_registration_audit_writes_json_and_markdown(tmp_path: Path) -> None:
    contribution, frame_search = _write_inputs(tmp_path)
    out = tmp_path / "rejection_registration_audit.json"
    markdown = tmp_path / "rejection_registration_audit.md"

    assert (
        main(
            [
                "tile-local-rejection-registration-audit",
                "--contribution",
                str(contribution),
                "--frame-family-search",
                str(frame_search),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["recommendation"] == "prioritize_registration_agreement_rejection_interaction"
    assert markdown.exists()
    assert "Tile-Local Rejection/Registration Audit" in markdown.read_text(encoding="utf-8")
