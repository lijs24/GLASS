from __future__ import annotations

from glass.engine.resident_registration_quality import (
    evaluate_resident_registration_quality,
    resident_registration_quality_warning_fields,
    summarize_resident_registration_quality,
)


def test_auto_triangle_quality_gate_excludes_below_min_inliers() -> None:
    decision = evaluate_resident_registration_quality(
        frame_id="F000213",
        registration_mode="similarity_cuda_triangle",
        requested_action="auto",
        status="ok",
        matched_stars=3,
        inliers=3,
        rms_px=1.42,
        min_inliers=4,
        max_rms_px=None,
        diagnostics={"triangle_translation_refine_status": "insufficient_inliers"},
    )

    assert decision["effective_action"] == "exclude"
    assert decision["decision_status"] == "rejected"
    assert decision["final_status"] == "excluded"
    assert decision["accepted"] is False
    assert decision["thresholds"]["min_inliers"] == 4
    assert decision["thresholds"]["max_rms_enabled"] is False
    assert decision["reasons"] == ["registration_inliers_below_min:3<4"]
    warnings = resident_registration_quality_warning_fields(decision)
    assert "resident_registration_quality_gate_status=rejected" in warnings
    assert "resident_registration_quality_gate_applied=exclude" in warnings


def test_auto_triangle_quality_gate_accepts_redundant_fit() -> None:
    decision = evaluate_resident_registration_quality(
        frame_id="F000194",
        registration_mode="similarity_cuda_triangle",
        requested_action="auto",
        status="ok",
        matched_stars=5,
        inliers=5,
        rms_px=1.91,
        min_inliers=4,
        max_rms_px=None,
    )

    assert decision["decision_status"] == "accepted"
    assert decision["final_status"] == "ok"
    assert decision["accepted"] is True
    assert decision["reasons"] == []


def test_auto_quality_gate_is_off_for_non_triangle_modes() -> None:
    decision = evaluate_resident_registration_quality(
        frame_id="F001",
        registration_mode="translation_ncc_subpixel",
        requested_action="auto",
        status="ok",
        matched_stars=0,
        inliers=0,
        rms_px=float("nan"),
        min_inliers=4,
        max_rms_px=None,
    )

    assert decision["effective_action"] == "off"
    assert decision["decision_status"] == "disabled"
    assert decision["final_status"] == "ok"


def test_auto_triangle_quality_gate_does_not_reject_capacity_limited_catalog() -> None:
    decision = evaluate_resident_registration_quality(
        frame_id="tiny",
        registration_mode="similarity_cuda_triangle",
        requested_action="auto",
        status="ok",
        matched_stars=3,
        inliers=3,
        rms_px=0.4,
        min_inliers=4,
        max_rms_px=None,
        diagnostics={"reference_stars": 3, "moving_stars": 3},
    )

    assert decision["decision_status"] == "accepted"
    assert decision["final_status"] == "ok"
    assert decision["thresholds"]["catalog_capacity_limited"] is True
    assert decision["reasons"] == []


def test_warn_quality_gate_records_without_excluding() -> None:
    decision = evaluate_resident_registration_quality(
        frame_id="F002",
        registration_mode="similarity_cuda_triangle",
        requested_action="warn",
        status="ok",
        matched_stars=2,
        inliers=2,
        rms_px=0.8,
        min_inliers=4,
        max_rms_px=2.0,
    )

    assert decision["effective_action"] == "warn"
    assert decision["decision_status"] == "warning"
    assert decision["action_applied"] == "warn"
    assert decision["final_status"] == "ok"
    assert decision["accepted"] is True


def test_resident_registration_quality_summary_counts_decisions() -> None:
    decisions = [
        evaluate_resident_registration_quality(
            frame_id="F001",
            registration_mode="similarity_cuda_triangle",
            requested_action="auto",
            status="ok",
            matched_stars=3,
            inliers=3,
            rms_px=1.0,
            min_inliers=4,
            max_rms_px=None,
        ),
        evaluate_resident_registration_quality(
            frame_id="F002",
            registration_mode="similarity_cuda_triangle",
            requested_action="auto",
            status="reference",
            matched_stars=1,
            inliers=1,
            rms_px=0.0,
            min_inliers=4,
            max_rms_px=None,
        ),
    ]

    summary = summarize_resident_registration_quality(decisions)

    assert summary["frame_count"] == 2
    assert summary["decision_status_counts"] == {"rejected": 1, "reference": 1}
    assert summary["final_status_counts"] == {"excluded": 1, "reference": 1}
    assert summary["action_counts"] == {"exclude": 1, "none": 1}
    assert summary["rejected_frame_ids"] == ["F001"]
