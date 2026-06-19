from __future__ import annotations

from glass.report.dq_contract_profile import (
    RESIDENT_DQ_REQUIRED_ARTIFACT_MAP_PATHS,
    RESIDENT_DQ_REQUIRED_OUTPUT_FLAGS,
    attach_resident_dq_provenance_contract,
    resident_dq_provenance_contract,
)


def test_resident_dq_provenance_contract_has_required_profile_fields():
    contract = resident_dq_provenance_contract()

    assert contract["required"] is True
    assert contract["min_records"] == 1
    assert contract["required_source_schemas"] == ["resident_dq_coverage_provenance"]
    assert contract["required_engines"] == ["cuda_resident_stack"]
    assert contract["min_active_frame_count"] == 190
    assert contract["require_existing_dq_map"] is True
    assert contract["verify_dq_map_pixels"] is True
    assert contract["verify_output_count_maps"] is True
    assert contract["dq_map_summary_tolerance_pixels"] == 0
    assert contract["coverage_map_finite_pixels_match_provenance"] is True
    assert contract["coverage_zero_pixels_match_no_data"] is True
    assert contract["rejection_map_sum_matches_provenance"] is True
    assert contract["required_source_terms"] == ["geometric_warp_coverage"]
    assert set(RESIDENT_DQ_REQUIRED_OUTPUT_FLAGS).issubset(
        contract["required_output_dq_flags"]
    )
    assert set(RESIDENT_DQ_REQUIRED_ARTIFACT_MAP_PATHS).issubset(
        contract["required_resident_artifact_map_paths"]
    )


def test_resident_dq_provenance_contract_honors_overrides():
    contract = resident_dq_provenance_contract(
        required=False,
        min_records=3,
        min_active_frame_count=200,
        dq_map_verify_tile_size=16,
        count_map_verify_tile_size=32,
        summary_tolerance_pixels=4,
        required_source_terms=("geometric_warp_coverage", "rejection_count_maps"),
    )

    assert contract["required"] is False
    assert contract["min_records"] == 3
    assert contract["min_active_frame_count"] == 200
    assert contract["dq_map_verify_tile_size"] == 16
    assert contract["count_map_verify_tile_size"] == 32
    assert contract["dq_map_summary_tolerance_pixels"] == 4
    assert contract["required_source_terms"] == [
        "geometric_warp_coverage",
        "rejection_count_maps",
    ]


def test_resident_dq_provenance_contract_returns_independent_lists():
    first = resident_dq_provenance_contract()
    second = resident_dq_provenance_contract()

    first["required_output_dq_flags"].append("mutated")
    first["required_resident_artifact_map_paths"].append("mutated")

    assert "mutated" not in second["required_output_dq_flags"]
    assert "mutated" not in second["required_resident_artifact_map_paths"]


def test_attach_resident_dq_provenance_contract_preserves_other_keys():
    benchmark_contract = {"minimum_speedup": 2.0}

    result = attach_resident_dq_provenance_contract(
        benchmark_contract,
        dq_map_verify_tile_size=8,
    )

    assert result is benchmark_contract
    assert result["minimum_speedup"] == 2.0
    assert result["dq_provenance"]["dq_map_verify_tile_size"] == 8
    assert result["dq_provenance"]["required_engines"] == ["cuda_resident_stack"]
