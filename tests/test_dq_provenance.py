from __future__ import annotations

from glass.engine.dq import dq_provenance_summary_from_resident, dq_provenance_summary_from_stack_engine


def test_stack_engine_dq_provenance_summary_contract():
    summary = dq_provenance_summary_from_stack_engine(
        {
            "input_samples": 8,
            "input_flagged_samples": 2,
            "input_nonfinite_samples": 1,
            "input_dq_flag_counts": {"hot_pixel": 1, "no_data": 1},
            "output_coverage_zero_pixels": 3,
            "output_low_rejected_pixels": 4,
            "output_high_rejected_pixels": 5,
            "output_dq_summary": {"valid": 7, "no_data": 3, "high_rejected": 5},
        },
        stage="integration",
        item="H",
    )

    assert summary["schema_version"] == 1
    assert summary["source_schema"] == "stack_engine_dq_provenance"
    assert summary["engine"] == "stack_engine_cpu"
    assert summary["stage"] == "integration"
    assert summary["item"] == "H"
    assert summary["input_samples"] == 8
    assert summary["input_flagged_samples"] == 2
    assert summary["input_nonfinite_samples"] == 1
    assert summary["source_dq_flag_counts"]["hot_pixel"] == 1
    assert summary["zero_coverage_pixels"] == 3
    assert summary["partial_coverage_pixels"] is None
    assert summary["low_rejected_pixels"] == 4
    assert summary["high_rejected_pixels"] == 5
    assert summary["valid_pixels"] == 7
    assert summary["no_data_pixels"] == 3


def test_resident_dq_provenance_summary_contract():
    summary = dq_provenance_summary_from_resident(
        {
            "active_frame_count": 3,
            "source_terms": ["post_rejection_coverage", "geometric_warp_coverage"],
            "finite_pre_rejection_coverage": {"finite_pixels": 20},
            "post_rejection_coverage": {"finite_pixels": 18},
            "rejected_sample_count": 6,
            "geometric_zero_pixels": 1,
            "geometric_partial_pixels": 2,
        },
        {"valid": 15, "no_data": 1, "warp_edge": 2, "low_rejected": 3, "high_rejected": 4},
        item="H",
    )

    assert summary["schema_version"] == 1
    assert summary["source_schema"] == "resident_dq_coverage_provenance"
    assert summary["engine"] == "cuda_resident_stack"
    assert summary["active_frame_count"] == 3
    assert summary["source_terms"] == ["post_rejection_coverage", "geometric_warp_coverage"]
    assert summary["finite_pre_rejection_pixels"] == 20
    assert summary["post_rejection_pixels"] == 18
    assert summary["rejected_samples"] == 6
    assert summary["zero_coverage_pixels"] == 1
    assert summary["partial_coverage_pixels"] == 2
    assert summary["low_rejected_pixels"] == 3
    assert summary["high_rejected_pixels"] == 4
    assert summary["valid_pixels"] == 15
    assert summary["warp_edge_pixels"] == 2
