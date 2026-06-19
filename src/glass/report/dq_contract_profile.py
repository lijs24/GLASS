from __future__ import annotations

from typing import Any

RESIDENT_DQ_REQUIRED_SOURCE_SCHEMAS = ("resident_dq_coverage_provenance",)
RESIDENT_DQ_REQUIRED_ENGINES = ("cuda_resident_stack",)
RESIDENT_DQ_REQUIRED_SUMMARY_FIELDS = (
    "zero_coverage_pixels",
    "partial_coverage_pixels",
)
RESIDENT_DQ_REQUIRED_OUTPUT_FLAGS = (
    "valid",
    "warp_edge",
    "low_rejected",
    "high_rejected",
)
RESIDENT_DQ_SUMMARY_MATCH_FLAGS = (
    "valid",
    "warp_edge",
    "low_rejected",
    "high_rejected",
)
RESIDENT_DQ_REQUIRED_ARTIFACT_MAP_PATHS = (
    "master",
    "weight",
    "coverage",
    "dq",
    "low_rejection",
    "high_rejection",
)
RESIDENT_DQ_POSITIVE_OUTPUT_FLAGS = ("valid", "warp_edge")
RESIDENT_DQ_REQUIRED_SOURCE_TERMS = ("geometric_warp_coverage",)


def resident_dq_provenance_contract(
    *,
    required: bool = True,
    min_records: int = 1,
    min_active_frame_count: int = 190,
    dq_map_verify_tile_size: int = 2048,
    count_map_verify_tile_size: int = 2048,
    summary_tolerance_pixels: int = 0,
    required_source_terms: tuple[str, ...] = RESIDENT_DQ_REQUIRED_SOURCE_TERMS,
) -> dict[str, Any]:
    """Return the resident CUDA DQ provenance benchmark-contract profile."""

    return {
        "required": required,
        "min_records": min_records,
        "required_source_schemas": list(RESIDENT_DQ_REQUIRED_SOURCE_SCHEMAS),
        "required_engines": list(RESIDENT_DQ_REQUIRED_ENGINES),
        "min_active_frame_count": min_active_frame_count,
        "require_dq_map_path": True,
        "require_existing_dq_map": True,
        "require_coverage_map_path": True,
        "required_summary_fields": list(RESIDENT_DQ_REQUIRED_SUMMARY_FIELDS),
        "required_output_dq_flags": list(RESIDENT_DQ_REQUIRED_OUTPUT_FLAGS),
        "verify_dq_map_pixels": True,
        "dq_map_verify_tile_size": dq_map_verify_tile_size,
        "dq_map_summary_tolerance_pixels": summary_tolerance_pixels,
        "dq_map_summary_match_flags": list(RESIDENT_DQ_SUMMARY_MATCH_FLAGS),
        "verify_output_count_maps": True,
        "count_map_verify_tile_size": count_map_verify_tile_size,
        "coverage_map_finite_pixels_match_provenance": True,
        "coverage_zero_pixels_match_no_data": True,
        "allow_missing_rejection_maps_if_skipped": True,
        "rejection_map_sum_matches_provenance": True,
        "required_resident_artifact_map_paths": list(
            RESIDENT_DQ_REQUIRED_ARTIFACT_MAP_PATHS
        ),
        "positive_output_dq_flags": list(RESIDENT_DQ_POSITIVE_OUTPUT_FLAGS),
        "required_source_terms": list(required_source_terms),
    }


def attach_resident_dq_provenance_contract(
    contract: dict[str, Any],
    **profile_kwargs: Any,
) -> dict[str, Any]:
    """Attach the resident CUDA DQ provenance profile to a benchmark contract."""

    contract["dq_provenance"] = resident_dq_provenance_contract(**profile_kwargs)
    return contract
