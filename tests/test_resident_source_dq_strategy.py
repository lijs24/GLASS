from __future__ import annotations

from pathlib import Path

from glass.engine.resident_source_dq_strategy import build_resident_source_dq_strategy


def _plan(width: int | None = 10, height: int | None = 5) -> dict[str, object]:
    frame: dict[str, object] = {
        "id": "L001",
        "frame_type": "light",
        "filter": "H",
    }
    if width is not None:
        frame["width"] = width
    if height is not None:
        frame["height"] = height
    return {
        "frames": [frame],
        "light_plans": [
            {
                "filter": "H",
                "frames": ["L001"],
                "calibration_status": "ready",
            }
        ],
    }


def test_resident_source_dq_strategy_allows_small_disk_cache(tmp_path: Path) -> None:
    strategy = build_resident_source_dq_strategy(
        _plan(),
        tmp_path / "run",
        free_bytes=10_000,
        max_disk_fraction=0.75,
        resident_mask_batch_frames=3,
        resident_memory_budget_bytes=1_000,
    )

    assert strategy["passed"] is True
    assert strategy["recommended_route"] == "generate_calibration_cache_allowed"
    assert strategy["estimated_output_bytes"] == 315
    assert strategy["disk_cache"]["max_allowed_bytes"] == 7_500
    assert strategy["resident_mask_streaming"]["estimated_batch_bytes"] == 150
    assert strategy["resident_mask_streaming"]["fits_memory_budget"] is True


def test_resident_source_dq_strategy_recommends_resident_streaming_when_cache_is_too_large(
    tmp_path: Path,
) -> None:
    strategy = build_resident_source_dq_strategy(
        _plan(width=100, height=100),
        tmp_path / "missing" / "run",
        free_bytes=1_000,
        max_disk_fraction=0.5,
        resident_mask_batch_frames=2,
        resident_memory_budget_bytes=50_000,
    )

    assert strategy["passed"] is False
    assert strategy["reason"] == "estimated_cache_exceeds_disk_budget"
    assert strategy["recommended_route"] == "resident_in_vram_mask_streaming"
    assert strategy["disk_usage_path"] == str(tmp_path)
    assert strategy["resident_mask_streaming"]["estimated_batch_bytes"] == 20_000
    assert strategy["resident_mask_streaming"]["fits_memory_budget"] is True


def test_resident_source_dq_strategy_blocks_unknown_shapes(tmp_path: Path) -> None:
    strategy = build_resident_source_dq_strategy(
        _plan(width=None, height=5),
        tmp_path / "run",
        free_bytes=1_000_000,
    )

    assert strategy["passed"] is False
    assert strategy["reason"] == "unknown_light_shapes"
    assert strategy["recommended_route"] == "blocked_unknown_shape"
    assert strategy["unknown_shape_frame_ids"] == ["L001"]


def test_resident_source_dq_strategy_records_star_protected_inline_detector(tmp_path: Path) -> None:
    strategy = build_resident_source_dq_strategy(
        _plan(),
        tmp_path / "run",
        free_bytes=10_000,
        resident_inline_source_dq="cosmetic_star",
    )

    inline = strategy["inline_source_dq"]
    assert inline["enabled"] is True
    assert inline["mode"] == "cosmetic_star"
    assert inline["detector"] == "glass.cpu.cosmetic.detect_star_protected_cosmetic_defects"
    assert inline["materializes_calibrated_dq_cache"] is False


def test_resident_source_dq_strategy_records_cuda_star_protected_inline_detector(
    tmp_path: Path,
) -> None:
    strategy = build_resident_source_dq_strategy(
        _plan(),
        tmp_path / "run",
        free_bytes=10_000,
        resident_inline_source_dq="cosmetic_star_cuda",
        resident_inline_source_dq_max_invalid_fraction=0.001,
        resident_inline_source_dq_admission="active_registered",
        resident_inline_source_dq_admission_policy_source="cuda_inline_default",
    )

    inline = strategy["inline_source_dq"]
    assert inline["enabled"] is True
    assert inline["mode"] == "cosmetic_star_cuda"
    assert inline["detector"] == (
        "ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame"
    )
    assert inline["threshold_source"] == "cuda_resident_histogram_median_mad_scalar"
    assert inline["detector_execution"] == "cuda_star_catalog_protected_isolated_threshold_apply"
    assert inline["star_catalog_deterministic"] is True
    assert inline["star_catalog_policy_source"] == "cosmetic_star_cuda_default"
    assert inline["star_catalog_source"] == (
        "resident_cuda_star_grid_top_nms_candidates_deterministic"
    )
    assert inline["high_fraction_guard_enabled"] is True
    assert inline["admission"] == "active_registered"
    assert inline["admission_policy_source"] == "cuda_inline_default"
    assert inline["count_only_preflight"] == (
        "ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frame"
    )
    assert inline["materializes_calibrated_dq_cache"] is False


def test_resident_source_dq_strategy_allows_explicit_nondeterministic_star_cuda_catalog(
    tmp_path: Path,
) -> None:
    strategy = build_resident_source_dq_strategy(
        _plan(),
        tmp_path / "run",
        free_bytes=10_000,
        resident_inline_source_dq="cosmetic_star_cuda",
        resident_star_catalog_deterministic=False,
        resident_star_catalog_policy_source="explicit_test_override",
    )

    inline = strategy["inline_source_dq"]
    assert inline["star_catalog_deterministic"] is False
    assert inline["star_catalog_policy_source"] == "explicit_test_override"
    assert inline["star_catalog_source"] == "resident_cuda_star_grid_top_nms_candidates"
