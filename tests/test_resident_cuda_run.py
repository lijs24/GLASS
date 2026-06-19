from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from glass.cli import main
from glass.cpu.integration import weighted_integrate_stack
from glass.engine.contracts import DQFlag
from glass.io.fits_io import read_fits_data
from glass.io.json_io import read_json, write_json
from glass.engine.resident_cuda import (
    _load_frame_weight_proposal,
    _load_tile_local_policy_replay,
    _matches_any_token,
    _resident_dq_coverage_provenance,
    _resident_dq_map,
    _resident_catalog_signature,
    _resident_descriptor_signature,
    _resident_fit_signature,
    _resident_output_map_selection,
    _resident_refine_catalog_centroids_from_stack,
    _resident_registration_motion_weighting,
    _resident_triangle_agreement_policy,
    _resident_triangle_agreement_quality,
    _resident_triangle_determinism_summary,
    _resident_triangle_translation_refine,
    _resident_similarity_frame_dispatch,
    _resident_winsorized_runtime_contract,
    _select_star_core_preselected_seed_indices,
    _select_star_guarded_seed,
    _tile_local_policy_application_arrays,
    _validate_resident_winsorized_runtime_contract,
)
from tests.conftest import cuda_module_or_skip


def _write_test_frame(path: Path, frame_type: str, data: np.ndarray, exposure: float = 60.0) -> None:
    header = fits.Header()
    header["IMAGETYP"] = frame_type
    header["FILTER"] = "H"
    header["EXPTIME"] = exposure
    header["GAIN"] = 100.0
    header["OFFSET"] = 20.0
    header["CCD-TEMP"] = -10.0
    header["XBINNING"] = 1
    header["YBINNING"] = 1
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.PrimaryHDU(np.asarray(data, dtype=np.float32), header=header).writeto(path)


def _shift_image(data: np.ndarray, dx: int, dy: int) -> np.ndarray:
    output = np.zeros_like(data, dtype=np.float32)
    h, w = data.shape
    src_x0 = max(0, -dx)
    src_x1 = min(w, w - dx)
    dst_x0 = max(0, dx)
    dst_x1 = min(w, w + dx)
    src_y0 = max(0, -dy)
    src_y1 = min(h, h - dy)
    dst_y0 = max(0, dy)
    dst_y1 = min(h, h + dy)
    if src_x0 < src_x1 and src_y0 < src_y1:
        output[dst_y0:dst_y1, dst_x0:dst_x1] = data[src_y0:src_y1, src_x0:src_x1]
    return output


def _two_light_star_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "star_dataset"
    shape = (72, 80)
    yy, xx = np.indices(shape, dtype=np.float32)
    reference = np.full(shape, 10.0, dtype=np.float32) + 0.01 * xx + 0.02 * yy
    for x, y, flux in [
        (12, 16, 120.0),
        (27, 38, 220.0),
        (55, 18, 160.0),
        (66, 49, 190.0),
        (42, 61, 250.0),
        (18, 57, 140.0),
        (70, 28, 170.0),
        (35, 24, 150.0),
    ]:
        reference += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.35**2)))
    moving = _shift_image(reference.astype(np.float32), 3, -2)

    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_001.fits", "light", reference, 60.0)
    _write_test_frame(root / "light" / "light_002.fits", "light", moving, 60.0)
    return root


def test_resident_dq_map_marks_no_data_and_rejections():
    master = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    weight = np.array([[2.0, 2.0], [0.0, 2.0]], dtype=np.float32)
    coverage = np.array([[2.0, 2.0], [2.0, 0.0]], dtype=np.float32)
    low = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.float32)
    high = np.array([[0.0, 0.0], [2.0, 0.0]], dtype=np.float32)

    dq, summary = _resident_dq_map(master, weight, coverage, low, high)

    assert dq[0, 0] == 0
    assert dq[0, 1] & int(DQFlag.NO_DATA)
    assert dq[0, 1] & int(DQFlag.LOW_REJECTED)
    assert dq[1, 0] & int(DQFlag.NO_DATA)
    assert dq[1, 0] & int(DQFlag.HIGH_REJECTED)
    assert dq[1, 1] & int(DQFlag.NO_DATA)
    assert dq[1, 1] & int(DQFlag.WARP_EDGE)
    assert summary["valid"] == 1
    assert summary["no_data"] == 3
    assert summary["warp_edge"] == 1
    assert summary["low_rejected"] == 1
    assert summary["high_rejected"] == 1


def test_resident_dq_coverage_provenance_separates_rejection_from_pre_rejection():
    coverage = np.array([[3.0, 0.0], [2.0, 1.0]], dtype=np.float32)
    low = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float32)
    high = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    provenance = _resident_dq_coverage_provenance(coverage, low, high, active_frame_count=3)

    assert provenance["available"] is True
    assert provenance["active_frame_count"] == 3
    assert provenance["source_terms"] == [
        "post_rejection_coverage",
        "low_rejection",
        "high_rejection",
    ]
    assert provenance["post_rejection_zero_pixels"] == 1
    assert provenance["zero_pre_rejection_pixels"] == 1
    assert provenance["partial_pre_rejection_pixels"] == 1
    assert provenance["rejection_reduced_pixels"] == 2
    assert provenance["rejected_sample_count"] == 2.0
    assert provenance["rejected_sample_count_source"] == "low_high_rejection_maps"
    assert provenance["finite_pre_rejection_coverage"]["max"] == 3.0
    assert provenance["partial_edge_inference"] == "deferred"


def test_resident_dq_map_marks_geometric_warp_edges_without_no_data():
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.full((2, 2), 2.0, dtype=np.float32)
    coverage = np.full((2, 2), 2.0, dtype=np.float32)
    geometric = np.array([[2.0, 1.0], [0.0, 2.0]], dtype=np.float32)

    dq, summary = _resident_dq_map(
        master,
        weight,
        coverage,
        None,
        None,
        geometric_warp_coverage_map=geometric,
        active_frame_count=2,
    )

    assert dq[0, 0] == 0
    assert dq[0, 1] & int(DQFlag.WARP_EDGE)
    assert not (dq[0, 1] & int(DQFlag.NO_DATA))
    assert dq[1, 0] & int(DQFlag.WARP_EDGE)
    assert dq[1, 0] & int(DQFlag.NO_DATA)
    assert summary["valid"] == 2
    assert summary["warp_edge"] == 2
    assert summary["no_data"] == 1


def test_resident_dq_coverage_provenance_includes_geometric_warp_coverage():
    coverage = np.full((2, 2), 2.0, dtype=np.float32)
    geometric = np.array([[2.0, 1.0], [0.0, 2.0]], dtype=np.float32)

    provenance = _resident_dq_coverage_provenance(
        coverage,
        None,
        None,
        active_frame_count=2,
        geometric_warp_coverage_map=geometric,
        geometric_warp_coverage_frame_count=2,
    )

    assert provenance["available"] is True
    assert provenance["source_terms"] == ["post_rejection_coverage", "geometric_warp_coverage"]
    assert provenance["geometric_warp_coverage_frame_count"] == 2
    assert provenance["geometric_frame_count_matches_active"] is True
    assert provenance["geometric_zero_pixels"] == 1
    assert provenance["geometric_partial_pixels"] == 1
    assert provenance["geometric_full_pixels"] == 2
    assert provenance["partial_edge_inference"] == "available_from_geometric_warp_coverage"


def test_resident_output_map_selection_modes():
    assert _resident_output_map_selection("audit") == {
        "master": True,
        "weight": True,
        "coverage": True,
        "low_rejection": True,
        "high_rejection": True,
        "dq": True,
    }
    assert _resident_output_map_selection("science") == {
        "master": True,
        "weight": True,
        "coverage": True,
        "low_rejection": False,
        "high_rejection": False,
        "dq": True,
    }
    assert _resident_output_map_selection("minimal") == {
        "master": True,
        "weight": False,
        "coverage": False,
        "low_rejection": False,
        "high_rejection": False,
        "dq": False,
    }


def test_resident_hardened_winsorized_contract_rejects_over_limit():
    contract = _resident_winsorized_runtime_contract(
        rejection_mode="winsorized_sigma",
        resident_winsorized_mode="hardened_cpu_parity",
        frame_count=257,
        dispatch_mode="stack",
    )

    assert contract["hardened_requested"] is True
    assert contract["hardened_frame_limit"] == 256
    assert contract["frame_limit_ok"] is False
    with pytest.raises(ValueError, match="at most 256 resident frames"):
        _validate_resident_winsorized_runtime_contract(contract)


def test_resident_fast_winsorized_contract_does_not_apply_hardened_limit():
    contract = _resident_winsorized_runtime_contract(
        rejection_mode="winsorized_sigma",
        resident_winsorized_mode="fast_approx",
        frame_count=512,
        dispatch_mode="fused_matrix",
    )

    _validate_resident_winsorized_runtime_contract(contract)
    assert contract["hardened_requested"] is False
    assert contract["frame_limit_applies"] is False
    assert contract["frame_limit_ok"] is True


def test_resident_triangle_determinism_signatures_are_stable_and_sensitive():
    catalog = {
        "count": 3,
        "stored_count": 3,
        "grid_cols": 1,
        "grid_rows": 1,
        "candidates_per_cell": 3,
        "max_output_candidates": 3,
        "min_separation_px": 0.0,
        "catalog_sort_mode": "test_sort",
        "catalog_topk_mode": "test_topk",
        "x": np.array([1.0, 2.0, 3.0], dtype=np.float32),
        "y": np.array([4.0, 5.0, 6.0], dtype=np.float32),
        "flux": np.array([30.0, 20.0, 10.0], dtype=np.float32),
    }
    descriptor = {
        "count": 1,
        "raw_count": 1,
        "max_stars": 3,
        "neighbors": 3,
        "model": "test_descriptor",
        "descriptors": np.array([[0.1, 0.2]], dtype=np.float32),
        "indices": np.array([[0, 1, 2]], dtype=np.int32),
        "areas": np.array([4.0], dtype=np.float32),
    }
    fit = {
        "status": "ok",
        "model": "test_fit",
        "matrix": np.eye(3, dtype=np.float32),
        "inliers": 3,
        "rms_px": 0.25,
        "scale": 1.0,
        "rotation_rad": 0.0,
        "best_candidate_index": 7,
        "candidate_count": 11,
        "reference_descriptor_count": 1,
        "moving_descriptor_count": 1,
    }

    catalog_sig = _resident_catalog_signature(catalog)
    descriptor_sig = _resident_descriptor_signature(descriptor)
    fit_sig = _resident_fit_signature(fit)

    assert catalog_sig == _resident_catalog_signature(catalog)
    assert descriptor_sig == _resident_descriptor_signature(descriptor)
    assert fit_sig == _resident_fit_signature(fit)

    changed_catalog = dict(catalog)
    changed_catalog["flux"] = np.array([30.0, 19.0, 10.0], dtype=np.float32)
    assert catalog_sig["sha256"] != _resident_catalog_signature(changed_catalog)["sha256"]

    summary = _resident_triangle_determinism_summary(
        {
            "schema_version": 1,
            "signature_mode": "catalog_descriptor_fit_exact_float32_sha256",
            "thresholds": {
                "30.000000": {
                    "reference_catalog": catalog_sig,
                    "reference_descriptor": descriptor_sig,
                }
            },
            "moving": {
                "light_002": {
                    "moving_catalog": catalog_sig,
                    "selected_fit": fit_sig,
                    "trial_signature": {"sha256": "trial-a"},
                }
            },
        }
    )

    assert summary["signature_mode"] == "catalog_descriptor_fit_exact_float32_sha256"
    assert summary["moving_frame_count"] == 1
    assert summary["threshold_count"] == 1
    assert len(summary["moving_catalog_combined_sha256"]) == 64
    assert len(summary["selected_fit_combined_sha256"]) == 64


def test_resident_star_core_preselection_keeps_refit_seed_and_rejects_low_inlier_trap():
    seed_metrics = [
        {"seed_index": 0, "seed_inliers": 12, "seed_rms_px": 1.4, "star_core_metric": {"rms": 800.0}},
        {"seed_index": 1, "seed_inliers": 12, "seed_rms_px": 1.2, "star_core_metric": {"rms": 600.0}},
        {"seed_index": 2, "seed_inliers": 11, "seed_rms_px": 1.1, "star_core_metric": {"rms": 590.0}},
        {"seed_index": 3, "seed_inliers": 9, "seed_rms_px": 0.8, "star_core_metric": {"rms": 100.0}},
    ]

    selected, summary = _select_star_core_preselected_seed_indices(seed_metrics, max_count=3)

    assert selected == [0, 1, 2]
    assert summary["enabled"]
    assert summary["star_max_inliers"] == 12
    assert summary["star_min_inliers_for_core_metric"] == 10
    assert summary["selection_key"] == "pre_refine_star_core_rms_with_two_inlier_slack"


def test_resident_star_guarded_seed_prefers_star_core_metric_with_inlier_slack():
    seed_metrics = [
        {
            "seed_index": 0,
            "seed_rank": 0,
            "seed_inliers": 15,
            "seed_rms_px": 1.2,
            "metrics": {"rms": 82.0},
            "star_core_metric": {"rms": 640.0},
        },
        {
            "seed_index": 1,
            "seed_rank": 1,
            "seed_inliers": 13,
            "seed_rms_px": 1.3,
            "metrics": {"rms": 78.0},
            "star_core_metric": {"rms": 600.0},
        },
        {
            "seed_index": 2,
            "seed_rank": 2,
            "seed_inliers": 10,
            "seed_rms_px": 1.0,
            "metrics": {"rms": 76.0},
            "star_core_metric": {"rms": 590.0},
        },
    ]

    selected_index, guard = _select_star_guarded_seed(seed_metrics, pixel_selected_index=2)

    assert selected_index == 1
    assert guard["status"] == "replaced_pixel_metric_with_star_core_metric"
    assert guard["star_max_inliers"] == 15
    assert guard["star_min_inliers_for_core_metric"] == 13


def test_resident_similarity_auto_pierside_dispatches_prior_and_orientation():
    reference = {"path": "", "header_summary": {"PIERSIDE": "West"}}
    same_side = {"path": "", "header_summary": {"PIERSIDE": "W"}}
    flipped = {"path": "", "header_summary": {"PIERSIDE": "East"}}
    unknown = {"path": "", "header_summary": {}}

    same = _resident_similarity_frame_dispatch("auto_pierside", reference, same_side, {})
    flip = _resident_similarity_frame_dispatch("auto_pierside", reference, flipped, {})
    fallback = _resident_similarity_frame_dispatch("auto_pierside", reference, unknown, {})
    manual = _resident_similarity_frame_dispatch("ncc", reference, flipped, {})

    assert same["prior"] == "ncc"
    assert same["orientation_mode"] == "pierside_same"
    assert same["reference_pierside"] == "west"
    assert same["moving_pierside"] == "west"
    assert flip["prior"] == "none"
    assert flip["orientation_mode"] == "pierside_flipped"
    assert fallback["prior"] == "ncc"
    assert fallback["orientation_mode"] == "pierside_unknown"
    assert manual["prior"] == "ncc"
    assert manual["orientation_mode"] == "manual"


def test_resident_triangle_agreement_quality_scores_pixel_refinement():
    strong = _resident_triangle_agreement_quality(
        pixel_ncc=0.96,
        pixel_rms_adu=20.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=0.5,
    )
    weak = _resident_triangle_agreement_quality(
        pixel_ncc=0.96,
        pixel_rms_adu=400.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=0.5,
    )
    unavailable = _resident_triangle_agreement_quality(
        pixel_ncc=np.nan,
        pixel_rms_adu=20.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=None,
    )

    assert strong["status"] == "ok"
    assert strong["score"] > weak["score"]
    assert weak["status"] == "failed"
    assert weak["reason"] == "below_min_score"
    assert unavailable["status"] == "unavailable"
    assert unavailable["reason"] == "pixel_ncc_unavailable"


def test_resident_triangle_agreement_policy_can_downweight_without_hard_failure():
    weak = _resident_triangle_agreement_quality(
        pixel_ncc=0.96,
        pixel_rms_adu=400.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=0.5,
    )

    hard_fail = _resident_triangle_agreement_policy(weak, "fail")
    downweight = _resident_triangle_agreement_policy(weak, "downweight")
    flagged = _resident_triangle_agreement_policy(weak, "flag")

    assert hard_fail["hard_failure"] is True
    assert hard_fail["weight_multiplier"] == 1.0
    assert downweight["hard_failure"] is False
    assert downweight["status"] == "downweighted"
    assert downweight["weight_multiplier"] == weak["score"] / weak["min_score"]
    assert flagged["hard_failure"] is False
    assert flagged["status"] == "flagged"
    assert flagged["weight_multiplier"] == 1.0


def test_resident_registration_motion_weighting_downweights_translation_outlier():
    matrices = [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 2.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 48.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    ]

    summary = _resident_registration_motion_weighting(
        ["F001", "F002", "F003", "F004"],
        matrices,
        [1.0, 1.0, 1.0, 1.0],
        mode="translation_mad",
        threshold_sigma=8.0,
        min_weight=0.05,
        power=2.0,
        scale_floor_px=1.0,
    )

    assert summary["enabled"] is True
    assert summary["eligible_frame_count"] == 4
    assert summary["downweighted_frame_count"] == 1
    assert summary["multipliers"][:3] == [1.0, 1.0, 1.0]
    assert 0.05 <= summary["multipliers"][3] < 1.0
    outlier = summary["frame_results"][3]
    assert outlier["threshold_exceeded"] is True
    assert outlier["weight_after_motion"] < outlier["weight_before_motion"]


def test_resident_registration_motion_weighting_off_preserves_weights():
    matrices = [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 48.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    ]

    summary = _resident_registration_motion_weighting(
        ["F001", "F002"],
        matrices,
        [1.0, 1.0],
        mode="off",
    )

    assert summary["enabled"] is False
    assert summary["multipliers"] == [1.0, 1.0]
    assert summary["downweighted_frame_count"] == 0


def test_resident_triangle_translation_refine_uses_catalog_median_translation():
    reference = {
        "stored_count": 4,
        "x": np.asarray([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
        "y": np.asarray([11.0, 22.0, 33.0, 44.0], dtype=np.float32),
    }
    moving = {
        "stored_count": 4,
        "x": np.asarray([7.0001, 17.0002, 27.0003, 37.0004], dtype=np.float32),
        "y": np.asarray([11.008, 22.010, 33.012, 44.014], dtype=np.float32),
    }
    seed = [[1.0, 0.0, 3.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    result = _resident_triangle_translation_refine(
        reference,
        moving,
        seed,
        tolerance_px=0.1,
        min_inliers=3,
        max_correction_px=0.05,
    )

    assert result["applied"] is True
    assert result["status"] == "applied"
    assert result["inliers"] == 4
    assert abs(result["matrix"][0][2] - 2.99975) < 1e-4
    assert abs(result["matrix"][1][2] + 0.011) < 1e-4
    assert 0.010 < result["correction_px"] < 0.012
    assert result["rms_px"] < 0.003
    assert result["iterations"] >= 1
    assert result["initial_rms_px"] > result["rms_px"]


def test_resident_triangle_translation_refine_iterates_to_reduce_seed_rms():
    reference = {
        "stored_count": 4,
        "x": np.asarray([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
        "y": np.asarray([12.0, 24.0, 36.0, 48.0], dtype=np.float32),
    }
    moving = {
        "stored_count": 4,
        "x": np.asarray([9.0, 19.0, 29.0, 39.0], dtype=np.float32),
        "y": np.asarray([12.0, 24.0, 36.0, 48.0], dtype=np.float32),
    }
    seed = [[1.0, 0.0, 0.72], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    result = _resident_triangle_translation_refine(
        reference,
        moving,
        seed,
        tolerance_px=0.31,
        min_inliers=4,
        max_correction_px=0.5,
        iterations=2,
    )

    assert result["applied"] is True
    assert result["inliers"] == 4
    assert result["iterations"] >= 1
    assert abs(result["matrix"][0][2] - 1.0) < 1e-6
    assert result["initial_rms_px"] > 0.25
    assert result["rms_px"] < 1e-6


def test_resident_triangle_translation_refine_rejects_large_correction():
    reference = {
        "stored_count": 3,
        "x": np.asarray([10.0, 20.0, 30.0], dtype=np.float32),
        "y": np.asarray([10.0, 20.0, 30.0], dtype=np.float32),
    }
    moving = {
        "stored_count": 3,
        "x": np.asarray([6.8, 16.8, 26.8], dtype=np.float32),
        "y": np.asarray([10.0, 20.0, 30.0], dtype=np.float32),
    }
    seed = [[1.0, 0.0, 3.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    result = _resident_triangle_translation_refine(
        reference,
        moving,
        seed,
        tolerance_px=0.5,
        min_inliers=3,
        max_correction_px=0.05,
    )

    assert result["applied"] is False
    assert result["status"] == "correction_exceeds_limit"
    assert result["matrix"] == seed
    assert abs(result["correction_px"] - 0.2) < 1e-5


def test_resident_refine_catalog_centroids_uses_resident_tiles():
    yy, xx = np.mgrid[0:21, 0:21]
    image = np.full((21, 21), 10.0, dtype=np.float32)
    image += 100.0 * np.exp(-(((xx - 9.35) ** 2 + (yy - 11.65) ** 2) / (2.0 * 1.2**2))).astype(np.float32)

    class FakeStack:
        width = image.shape[1]
        height = image.shape[0]

        def download_frame_tile(self, _index, x0, y0, x1, y1):
            return image[y0:y1, x0:x1]

    catalog = {
        "stored_count": 1,
        "x": np.asarray([9.0], dtype=np.float32),
        "y": np.asarray([12.0], dtype=np.float32),
        "flux": np.asarray([110.0], dtype=np.float32),
    }

    refined, summary = _resident_refine_catalog_centroids_from_stack(FakeStack(), 0, catalog, radius=4)

    assert summary["status"] == "ok"
    assert summary["refined_count"] == 1
    assert abs(float(refined["x"][0]) - 9.35) < 0.05
    assert abs(float(refined["y"][0]) - 11.65) < 0.05
    assert summary["max_shift_px"] > 0.4


def test_frame_weight_proposal_loader_accepts_list_and_object(tmp_path: Path):
    list_path = tmp_path / "proposal_list.json"
    write_json(
        list_path,
        {
            "artifact_type": "frame_weight_proposal",
            "method": "control_ratio",
            "source_integration_audit": "audit.json",
            "frame_multipliers": [
                {"frame_id": "F001", "multiplier": 0.25, "reason": "localized contribution"},
                {"frame_id": "F002", "multiplier": 1.0},
            ],
        },
    )
    proposal = _load_frame_weight_proposal(list_path)

    assert proposal["enabled"] is True
    assert proposal["path"] == str(list_path)
    assert proposal["frame_count"] == 2
    assert proposal["frame_multipliers"] == {"F001": 0.25, "F002": 1.0}
    assert proposal["rows"][0]["reason"] == "localized contribution"

    object_path = tmp_path / "proposal_object.json"
    write_json(object_path, {"frame_multipliers": {"F003": 0.5}})
    object_proposal = _load_frame_weight_proposal(object_path)

    assert object_proposal["frame_count"] == 1
    assert object_proposal["rows"][0]["frame_id"] == "F003"
    assert object_proposal["rows"][0]["multiplier"] == 0.5


def test_tile_local_policy_replay_loader_validates_contract(tmp_path: Path):
    replay_path = tmp_path / "tile_local_replay.json"
    write_json(
        replay_path,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": ["F001", "F002"],
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "boost_tiles": 1,
                "mean_abs_residual_before": 0.1,
                "mean_abs_residual_after": 0.02,
            },
            "tiles": [
                {
                    "tile_index": 3,
                    "extent": {"x0": 4, "y0": 5, "x1": 12, "y1": 16},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                    "clamped": True,
                    "selected_frame_row_count": 2,
                    "canonical_delta_contribution_adu": 5.0,
                    "signed_residual_reference_units_before": -0.1,
                    "signed_residual_reference_units_after": -0.02,
                    "moves_toward_reference": True,
                }
            ],
        },
    )

    contract = _load_tile_local_policy_replay(replay_path)

    assert contract["enabled"] is True
    assert contract["applied"] is False
    assert contract["application_status"] == "validated_not_applied"
    assert contract["target_group"] == "focus"
    assert contract["target_frame_count"] == 2
    assert contract["tile_count"] == 1
    assert contract["summary"]["recommendation"] == "tile_local_replay_promising"
    assert contract["tiles"][0]["extent"] == {"x0": 4, "y0": 5, "x1": 12, "y1": 16}
    assert contract["tiles"][0]["multiplier"] == 2.0


def test_tile_local_policy_application_arrays_build_apply_contract(tmp_path: Path):
    replay_path = tmp_path / "tile_local_replay.json"
    write_json(
        replay_path,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": ["F001", "F002"],
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 1, "y0": 2, "x1": 6, "y1": 7},
                    "multiplier": 1.75,
                }
            ],
        },
    )
    contract = _load_tile_local_policy_replay(replay_path)

    target_mask, tile_extents, tile_multipliers, summary = _tile_local_policy_application_arrays(
        contract,
        [{"id": "F001"}, {"id": "F003"}],
        width=8,
        height=8,
    )

    assert target_mask.tolist() == [1, 0]
    assert tile_extents.tolist() == [[1, 2, 6, 7]]
    assert tile_multipliers.tolist() == [1.75]
    assert summary["native_method"] == "ResidentCalibratedStack.integrate_tile_local_mean"
    assert summary["target_frame_count_applied"] == 1
    assert summary["target_frame_ids_missing"] == ["F002"]
    assert summary["tile_count_applied"] == 1


def _two_dark_group_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "two_dark_groups"
    shape = (24, 24)
    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_060.fits", "dark", np.full(shape, 10.0, dtype=np.float32), 60.0)
    _write_test_frame(root / "dark" / "dark_120.fits", "dark", np.full(shape, 20.0, dtype=np.float32), 120.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_060.fits", "light", np.full(shape, 100.0, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_120.fits", "light", np.full(shape, 200.0, dtype=np.float32), 120.0)
    return root


def _two_light_weight_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "weight_dataset"
    shape = (16, 16)
    yy, xx = np.indices(shape, dtype=np.float32)
    low_noise = np.full(shape, 100.0, dtype=np.float32) + 0.05 * xx + 0.03 * yy
    high_noise = np.full(shape, 100.0, dtype=np.float32) + 3.0 * ((xx % 4) - 1.5) + 2.0 * ((yy % 4) - 1.5)
    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_low_noise.fits", "light", low_noise, 60.0)
    _write_test_frame(root / "light" / "light_high_noise.fits", "light", high_noise, 60.0)
    return root


def _four_light_rejection_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "rejection_dataset"
    shape = (10, 12)
    yy, xx = np.indices(shape, dtype=np.float32)
    base = np.full(shape, 10.0, dtype=np.float32) + 0.05 * xx + 0.03 * yy
    frames = [
        base,
        base + np.float32(0.08),
        base - np.float32(0.06),
        base + np.float32(0.02),
    ]
    frames[3] = frames[3].copy()
    frames[3][2, 3] = 80.0
    frames[3][7, 8] = -120.0
    frames[2] = frames[2].copy()
    frames[2][1, 10] = 65.0

    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    for index, frame in enumerate(frames, start=1):
        _write_test_frame(root / "light" / f"light_{index:03d}.fits", "light", frame, 60.0)
    return root


def test_cli_resident_cuda_tile_local_policy_apply_mean_changes_target_tile(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    replay = tmp_path / "tile_local_replay.json"
    run = tmp_path / "resident_run_tile_local_apply"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    high_id = str(light_by_stem["light_high_noise"]["id"])
    write_json(
        replay,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": [high_id],
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "boost_tiles": 1,
            },
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 8, "y1": 8},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                    "selected_frame_row_count": 1,
                    "canonical_delta_contribution_adu": 1.0,
                    "signed_residual_reference_units_before": -0.2,
                    "signed_residual_reference_units_after": -0.1,
                    "moves_toward_reference": True,
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-tile-local-policy-replay",
            str(replay),
            "--resident-tile-local-policy-mode",
            "apply_mean",
        ]
    ) == 0

    low = read_fits_data(dataset / "light" / "light_low_noise.fits", dtype=np.float32)
    high = read_fits_data(dataset / "light" / "light_high_noise.fits", dtype=np.float32)
    expected = ((low + high) / 2.0).astype(np.float32)
    expected[:8, :8] = ((low[:8, :8] + 2.0 * high[:8, :8]) / 3.0).astype(np.float32)
    master = read_fits_data(run / "integration" / "resident_master_H.fits", dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    tile_local = resident["artifacts"][0]["resident_integration_weighting"]["tile_local_policy_replay"]

    assert tile_local["enabled"] is True
    assert tile_local["requested_mode"] == "apply_mean"
    assert tile_local["effective_mode"] == "apply_mean"
    assert tile_local["applied"] is True
    assert tile_local["application_status"] == "applied_mean_rejection_none"
    assert tile_local["target_frame_count_applied"] == 1
    assert tile_local["tile_count_applied"] == 1
    assert tile_local["native_timing_s"]["timing_model"] == "native_resident_tile_local_weighted_mean_one_sync"
    assert any("tile-local policy replay was applied" in warning for warning in integration["warnings"])
    assert np.allclose(master, expected, rtol=2e-5, atol=2e-5)


def test_cli_resident_cuda_tile_local_policy_apply_winsorized_sigma_records_rejection_maps(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    replay = tmp_path / "tile_local_replay.json"
    run = tmp_path / "resident_run_tile_local_apply_sigma"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    high_id = str(light_by_stem["light_high_noise"]["id"])
    write_json(
        replay,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": [high_id],
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 8, "y1": 8},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "winsorized_sigma",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-tile-local-policy-replay",
            str(replay),
            "--resident-tile-local-policy-mode",
            "apply",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    tile_local = resident["artifacts"][0]["resident_integration_weighting"]["tile_local_policy_replay"]

    assert tile_local["enabled"] is True
    assert tile_local["requested_mode"] == "apply"
    assert tile_local["effective_mode"] == "apply"
    assert tile_local["applied"] is True
    assert tile_local["application_status"] == "applied_winsorized_sigma"
    assert tile_local["native_method"] == "ResidentCalibratedStack.integrate_tile_local_sigma_clip"
    assert tile_local["native_timing_s"]["timing_model"] == "native_resident_tile_local_sigma_clip_one_sync"
    assert tile_local["native_timing_s"]["rejection"] == "winsorized_sigma"
    assert output["coverage_map_path"] is not None
    assert output["low_rejection_map_path"] is not None
    assert output["high_rejection_map_path"] is not None
    assert Path(output["coverage_map_path"]).exists()
    assert Path(output["low_rejection_map_path"]).exists()
    assert Path(output["high_rejection_map_path"]).exists()
    assert any("tile-local policy replay was applied to winsorized_sigma" in warning for warning in integration["warnings"])


def test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _four_light_rejection_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_hardened_winsorized"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "winsorized_sigma",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-integration-dispatch",
            "auto",
            "--resident-winsorized-mode",
            "hardened_cpu_parity",
        ]
    ) == 0

    light_frames = [
        read_fits_data(path, dtype=np.float32)
        for path in sorted((dataset / "light").glob("light_*.fits"))
    ]
    expected_master, expected_weight, expected_coverage, expected_low, expected_high = (
        weighted_integrate_stack(
            np.stack(light_frames, axis=0),
            rejection="winsorized_sigma",
            low_sigma=3.0,
            high_sigma=3.0,
        )
    )

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    contract = read_json(run / "resident_result_contract.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    descriptor = output["integration_rejection"]
    dispatch = artifact["resident_integration_dispatch"]
    winsorized_contract = output["resident_winsorized_contract"]
    hardened_timing = output["hardened_winsorized_timing_s"]

    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    coverage = read_fits_data(Path(output["coverage_map_path"]), dtype=np.float32)
    low_reject = read_fits_data(Path(output["low_rejection_map_path"]), dtype=np.float32)
    high_reject = read_fits_data(Path(output["high_rejection_map_path"]), dtype=np.float32)

    assert descriptor["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert descriptor["cpu_baseline_parity"] is True
    assert descriptor["approximation"] is False
    assert artifact["integration_rejection"] == descriptor
    assert integration["rejection_semantics"] == descriptor
    assert integration["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert dispatch["effective_mode"] == "stack"
    assert dispatch["selection_reason"] == "auto_stack_hardened_winsorized_requires_stack"
    assert dispatch["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert dispatch["resident_winsorized_contract"] == winsorized_contract
    assert winsorized_contract["hardened_requested"] is True
    assert winsorized_contract["frame_count"] == 4
    assert winsorized_contract["hardened_frame_limit"] == 256
    assert winsorized_contract["frame_limit_ok"] is True
    assert winsorized_contract["dispatch_ok"] is True
    assert winsorized_contract["requires_stack_dispatch"] is True
    assert dispatch["hardened_winsorized_timing_s"] == hardened_timing
    assert hardened_timing["native_method"] == "ResidentCalibratedStack.integrate_hardened_winsorized_sigma"
    assert hardened_timing["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert hardened_timing["frame_count"] == 4
    assert hardened_timing["pixel_count"] == expected_master.size
    assert hardened_timing["total_s"] >= 0.0
    assert contract["passed"] is True
    assert any("hardened median/IQR" in warning for warning in integration["warnings"])
    assert np.allclose(master, expected_master, rtol=2e-5, atol=2e-5)
    assert np.allclose(weight, expected_weight, rtol=2e-5, atol=2e-5)
    assert np.allclose(coverage, expected_coverage, rtol=0.0, atol=0.0)
    assert np.allclose(low_reject, expected_low, rtol=0.0, atol=0.0)
    assert np.allclose(high_reject, expected_high, rtol=0.0, atol=0.0)
    assert float(np.max(high_reject)) > 0.0
    assert float(np.max(low_reject)) > 0.0


def test_cli_resident_cuda_run_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run"

    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--flat-floor",
            "0.05",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-registration",
            "translation_preview",
            "--reference-frame-id",
            "light_001",
            "--exclude-frame-id",
            "does_not_exist",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    state = read_json(run / "run_state.json")
    resident = read_json(run / "resident_artifacts.json")
    calibration = read_json(run / "calibration_artifacts.json")
    resident_result_contract = read_json(run / "resident_result_contract.json")
    assert integration["source_stage"] == "resident_calibrated_stack"
    assert integration["outputs"][0]["backend"] == "cuda_resident_stack"
    assert integration["outputs"][0]["resident_registration"] == "translation_preview"
    assert integration["excluded_frame_tokens"] == ["does_not_exist"]
    assert integration["outputs"][0]["output_diagnostics"]["normalization_probe"]["method"]
    assert Path(integration["outputs"][0]["dq_map_path"]).exists()
    assert integration["outputs"][0]["dq_map_path"] == resident["artifacts"][0]["dq_map_path"]
    assert integration["outputs"][0]["dq_summary"] == resident["artifacts"][0]["dq_summary"]
    assert integration["outputs"][0]["master_path"] == resident["artifacts"][0]["master_path"]
    assert integration["outputs"][0]["weight_map_path"] == resident["artifacts"][0]["weight_map_path"]
    assert integration["outputs"][0]["coverage_map_path"] == resident["artifacts"][0]["coverage_map_path"]
    assert integration["outputs"][0]["low_rejection_map_path"] == resident["artifacts"][0]["low_rejection_map_path"]
    assert integration["outputs"][0]["high_rejection_map_path"] == resident["artifacts"][0]["high_rejection_map_path"]
    dq_data = read_fits_data(integration["outputs"][0]["dq_map_path"])
    shape = resident["artifacts"][0]["shape"]
    assert dq_data.shape == (shape["height"], shape["width"])
    assert np.all(np.isfinite(dq_data))
    assert np.nanmax(dq_data) <= int(
        DQFlag.NO_DATA | DQFlag.WARP_EDGE | DQFlag.LOW_REJECTED | DQFlag.HIGH_REJECTED
    )
    with fits.open(integration["outputs"][0]["dq_map_path"]) as hdul:
        assert "WARP_EDGE" in hdul[0].header["DQFLAGS"]
    assert resident["artifacts"][0]["dq_flag_bits"]["warp_edge"] == int(DQFlag.WARP_EDGE)
    assert "valid" in integration["outputs"][0]["dq_summary"]
    assert registration["source_stage"] == "resident_calibrated_stack"
    assert registration["results"][0]["status"] == "reference"
    assert state["current_stage"] == "integration"
    assert "resident_registration" in state["completed_stages"]
    assert "resident_integration" in state["completed_stages"]
    assert resident["backend"] == "cuda_resident_stack"
    assert resident["policy"]["flat_floor"] == 0.05
    assert calibration["artifact_type"] == "resident_cuda_calibration_artifacts"
    assert calibration["source_stage"] == "resident_calibrated_stack"
    assert calibration["backend"] == "cuda_resident_stack"
    assert len(calibration["masters"]) >= 3
    assert len(calibration["calibrated_lights"]) == len(resident["artifacts"][0]["frame_ids"])
    assert all(item["status"] == "resident_in_vram" for item in calibration["calibrated_lights"])
    assert all(item["resident_calibration_contract"]["passed"] for item in calibration["masters"].values())
    assert resident_result_contract["artifact_type"] == "resident_cuda_result_contract"
    assert resident_result_contract["passed"] is True
    assert resident_result_contract["outputs"][0]["filter"] == "H"
    assert resident_result_contract["outputs"][0]["backend"] == "cuda_resident_stack"
    assert resident["artifacts"][0]["resident_registration"]["mode"] == "translation_preview"
    assert resident["artifacts"][0]["output_diagnostics"]["clipping_probe"]["nonfinite_count"] == 0
    timing = resident["artifacts"][0]["timing_s"]
    fine_timing = resident["artifacts"][0]["fine_timing"]
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    io_overlap = resident["artifacts"][0]["resident_io_overlap"]
    assert fine_timing["schema_version"] == 1
    assert io_pipeline["prefetch_frames"] == 2
    assert io_pipeline["prefetch_workers"] == 2
    assert io_pipeline["h2d_mode"] == "pinned_ring"
    assert io_pipeline["calibration_event_mode"] == "reused_stack_events"
    assert io_pipeline["calibration_event_modes"] == ["reused_stack_events"]
    assert io_pipeline["calibration_event_reuse"] is True
    assert io_pipeline["host_pinned_bytes"] > 0
    assert io_pipeline["prefetch_host_pinned_bytes"] > 0
    assert io_pipeline["stack_host_pinned_bytes"] == 0
    assert resident["artifacts"][0]["resident_warp_scratch_bytes"] >= 0
    assert io_pipeline["warp_scratch_bytes"] == resident["artifacts"][0]["resident_warp_scratch_bytes"]
    assert resident["artifacts"][0]["resident_warp_copy_mode"] == "default_stream_async_device_to_device"
    assert io_pipeline["warp_copy_mode"] == "default_stream_async_device_to_device"
    assert timing["light_read_decode"] >= 0.0
    assert timing["light_read_wait_wall"] == timing["light_read_decode"]
    assert timing["light_read_decode_worker"] >= 0.0
    assert timing["light_read_worker_cumulative"] == timing["light_read_decode_worker"]
    assert timing["light_fits_open"] >= 0.0
    assert timing["light_fits_open_worker_cumulative"] == timing["light_fits_open"]
    assert timing["light_fits_materialize_decode"] >= 0.0
    assert (
        timing["light_fits_materialize_decode_worker_cumulative"]
        == timing["light_fits_materialize_decode"]
    )
    assert timing["light_read_overlap_saved"] >= 0.0
    assert timing["light_host_copy_to_pinned"] >= 0.0
    assert timing["light_host_copy_to_pinned"] == 0.0
    assert timing["light_h2d"] >= 0.0
    assert timing["light_calibrate_store"] >= 0.0
    assert timing["light_h2d_calibrate_store"] >= 0.0
    assert timing["resident_registration_warp"] >= 0.0
    assert timing["light_loop_unaccounted"] >= 0.0
    assert fine_timing["seconds"]["light_read_decode_total"] == timing["light_read_decode"]
    assert fine_timing["seconds"]["light_read_decode_worker_total"] == timing["light_read_decode_worker"]
    assert fine_timing["seconds"]["light_read_overlap_saved"] == timing["light_read_overlap_saved"]
    assert fine_timing["seconds"]["light_fits_open_total"] == timing["light_fits_open"]
    assert fine_timing["seconds"]["light_fits_materialize_decode_total"] == timing["light_fits_materialize_decode"]
    assert fine_timing["seconds"]["light_host_copy_to_pinned_total"] == timing["light_host_copy_to_pinned"]
    assert fine_timing["seconds"]["light_h2d_total"] == timing["light_h2d"]
    assert fine_timing["seconds"]["light_calibrate_store_total"] == timing["light_calibrate_store"]
    assert fine_timing["seconds"]["light_h2d_calibrate_store_total"] == timing["light_h2d_calibrate_store"]
    assert fine_timing["seconds"]["resident_registration_warp_total"] == timing["resident_registration_warp"]
    assert io_overlap["schema_version"] == 1
    assert io_overlap["prefetch_enabled"] is True
    assert io_overlap["wall_clock_stage_s"] == timing["light_read_upload_calibrate"]
    assert io_overlap["consumer_read_wait_wall_s"] == timing["light_read_wait_wall"]
    assert io_overlap["worker_read_cumulative_s"] == timing["light_read_worker_cumulative"]
    assert io_overlap["overlap_saved_s"] == timing["light_read_overlap_saved"]


def test_cli_resident_cuda_run_simple_snr_weighting(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_simple_snr"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "simple_snr",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    weights = integration["frame_weights"]
    assert integration["weighting"] == "simple_snr"
    assert integration["outputs"][0]["weighting"] == "simple_snr"
    assert not any("winsorized" in warning for warning in integration["warnings"])
    weighting = resident["artifacts"][0]["resident_integration_weighting"]
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_batch_enabled"] is True
    assert io_pipeline["calibration_batch_multistream_enabled"] is True
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_batch"
    assert io_pipeline["calibration_batch_requested_frames"] == 2
    assert io_pipeline["calibration_batch_requested_streams"] == 2
    assert io_pipeline["calibration_wave_requested_frames"] == 0
    assert io_pipeline["calibration_wave_effective_frames"] == 2
    assert io_pipeline["calibration_wave_enabled"] is False
    assert io_pipeline["calibration_wave_release_mode"] == "after_native_batch_sync"
    assert io_pipeline["calibration_batch_actual_stream_count"] == 2
    assert io_pipeline["calibration_batch_lane_buffer_bytes"] > 0
    assert io_pipeline["calibration_batch_frame_count"] == 2
    assert io_pipeline["calibration_batch_count"] == 1
    assert io_pipeline["calibration_batch_timing_model"] == "multi_stream_lanes_one_sync"
    assert io_pipeline["calibration_batch_native_total_s"] >= 0.0
    assert io_pipeline["calibration_batch_sync_s"] >= 0.0
    assert io_pipeline["calibration_event_mode"] == "reused_stack_lane_events"
    assert weighting["mode"] == "simple_snr"
    assert len(weighting["frame_results"]) == 2
    assert all(item["source_std"] is not None for item in weighting["frame_results"])
    by_std = sorted(weighting["frame_results"], key=lambda item: item["source_std"])
    assert by_std[0]["weight"] > by_std[-1]["weight"]
    assert max(weights.values()) > min(weights.values())


def test_cli_resident_cuda_batch_wave_releases_prefetch_slots(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_batch_wave"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "h2d_event",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_batch_enabled"] is True
    assert io_pipeline["calibration_batch_multistream_enabled"] is True
    assert io_pipeline["calibration_wave_enabled"] is True
    assert io_pipeline["calibration_wave_requested_frames"] == 1
    assert io_pipeline["calibration_wave_effective_frames"] == 1
    assert io_pipeline["calibration_wave_release_mode"] == "after_wave_sync"
    assert io_pipeline["calibration_release_mode_requested"] == "h2d_event"
    assert io_pipeline["calibration_release_mode_effective"] == "h2d_event"
    assert io_pipeline["calibration_h2d_release_supported"] is True
    assert io_pipeline["calibration_h2d_release_capable"] is True
    assert io_pipeline["calibration_h2d_release_enabled"] is True
    assert io_pipeline["calibration_h2d_release_recommended"] is False
    assert io_pipeline["calibration_h2d_release_reason"] == "explicit_h2d_event_requested"
    assert io_pipeline["calibration_h2d_release_count"] == 2
    assert io_pipeline["calibration_h2d_release_s"] >= 0.0
    assert io_pipeline["calibration_h2d_event_sync_s"] >= 0.0
    assert io_pipeline["calibration_h2d_event_elapsed_s"] >= 0.0
    assert io_pipeline["calibration_pending_wait_sync_s"] >= 0.0
    assert io_pipeline["calibration_batch_requested_frames"] == 2
    assert io_pipeline["calibration_batch_count"] == 2
    assert io_pipeline["calibration_batch_frame_count"] == 2
    assert io_pipeline["calibration_batch_actual_stream_count"] == 1
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_h2d_release_batch"
    assert io_pipeline["calibration_batch_timing_model"] == (
        "multi_stream_one_frame_per_lane_h2d_release_then_wait"
    )
    assert io_pipeline["calibration_event_mode"] == "reused_stack_lane_h2d_events"
    assert io_pipeline["prefetch_release_count"] == 2
    assert io_pipeline["prefetch_release_batch_count"] == 2
    assert io_pipeline["prefetch_fill_call_count"] == 3
    assert io_pipeline["prefetch_fill_submit_count"] == 2
    assert io_pipeline["prefetch_release_fill_model"] == "batched_release_single_fill"
    assert io_pipeline["prefetch_max_inflight_slots"] == 2


def test_cli_resident_cuda_auto_release_policy_prefers_full_lanes(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    run_full = tmp_path / "resident_run_auto_full_lanes"
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run_full),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "2",
            "--resident-calibration-release-mode",
            "auto",
        ]
    ) == 0
    resident = read_json(run_full / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_requested"] == "auto"
    assert io_pipeline["calibration_release_mode_effective"] == "h2d_event"
    assert io_pipeline["calibration_h2d_release_capable"] is True
    assert io_pipeline["calibration_h2d_release_recommended"] is True
    assert io_pipeline["calibration_h2d_release_reason"] == "auto_h2d_event_wave_effective_matches_stream_count"
    assert io_pipeline["calibration_h2d_release_enabled"] is True
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_h2d_release_batch"
    assert io_pipeline["calibration_h2d_release_count"] == 2

    run_underfilled = tmp_path / "resident_run_auto_underfilled_lanes"
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run_underfilled),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "auto",
        ]
    ) == 0
    resident = read_json(run_underfilled / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_requested"] == "auto"
    assert io_pipeline["calibration_release_mode_effective"] == "sync"
    assert io_pipeline["calibration_h2d_release_capable"] is True
    assert io_pipeline["calibration_h2d_release_recommended"] is False
    assert io_pipeline["calibration_h2d_release_reason"] == "auto_sync:wave_effective_below_stream_count"
    assert io_pipeline["calibration_h2d_release_enabled"] is False
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_batch"
    assert io_pipeline["calibration_h2d_release_count"] == 0


def test_cli_resident_cuda_callback_queue_releases_inside_native_batch(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_callback_queue"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "callback_queue",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_requested"] == "callback_queue"
    assert io_pipeline["calibration_release_mode_effective"] == "callback_queue"
    assert io_pipeline["calibration_callback_release_supported"] is True
    assert io_pipeline["calibration_callback_release_capable"] is True
    assert io_pipeline["calibration_callback_release_enabled"] is True
    assert io_pipeline["calibration_callback_release_recommended"] is False
    assert io_pipeline["calibration_h2d_release_reason"] == "explicit_callback_queue_requested"
    assert io_pipeline["calibration_fetch_batch_frames"] == 2
    assert io_pipeline["calibration_wave_effective_frames"] == 1
    assert io_pipeline["calibration_wave_release_mode"] == "callback_after_h2d_event"
    assert io_pipeline["calibration_batch_count"] == 1
    assert io_pipeline["calibration_callback_wave_count"] == 2
    assert io_pipeline["calibration_callback_release_count"] == 2
    assert io_pipeline["calibration_h2d_release_count"] == 2
    assert io_pipeline["calibration_callback_release_s"] >= 0.0
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_callback_release_batch"
    assert io_pipeline["calibration_batch_timing_model"] == "multi_stream_callback_release_waves_one_final_sync"
    assert io_pipeline["calibration_event_mode"] == "reused_stack_lane_h2d_callback_events"
    assert io_pipeline["prefetch_release_count"] == 2
    assert io_pipeline["prefetch_release_batch_count"] == 2
    assert io_pipeline["prefetch_fill_call_count"] == 3
    assert io_pipeline["prefetch_fill_submit_count"] == 2
    assert io_pipeline["prefetch_release_fill_model"] == "batched_release_single_fill"


def test_cli_resident_cuda_callback_queue_queued_prefetch_refill(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_callback_queue_queued_refill"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-prefetch-refill-mode",
            "queued",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "callback_queue",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_effective"] == "callback_queue"
    assert io_pipeline["prefetch_refill_mode"] == "queued"
    assert io_pipeline["prefetch_release_fill_model"] == "queued_release_refill"
    assert io_pipeline["prefetch_release_count"] == 2
    assert io_pipeline["prefetch_release_batch_count"] == 2
    assert io_pipeline["prefetch_release_refill_request_count"] == 2
    assert io_pipeline["prefetch_release_refill_queued_submit_count"] >= 1
    assert io_pipeline["prefetch_release_refill_queued_execute_count"] == (
        io_pipeline["prefetch_release_refill_queued_submit_count"]
    )
    assert (
        io_pipeline["prefetch_release_refill_queued_submit_count"]
        + io_pipeline["prefetch_release_refill_queued_coalesced_count"]
        == io_pipeline["prefetch_release_refill_request_count"]
    )
    assert io_pipeline["prefetch_fill_call_count"] == (
        1 + io_pipeline["prefetch_release_refill_queued_execute_count"]
    )
    assert io_pipeline["prefetch_fill_submit_count"] == 2


def test_cli_resident_cuda_science_output_maps_skip_rejection_count_files(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_science_maps"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--until-stage",
                "integration",
                "--local-normalization",
                "off",
                "--integration-rejection",
                "sigma_clip",
                "--integration-weighting",
                "none",
                "--resident-registration",
                "off",
                "--resident-output-maps",
                "science",
            ]
        )
        == 0
    )

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    assert output["output_map_policy"]["mode"] == "science"
    assert artifact["output_map_policy"]["mode"] == "science"
    assert Path(output["master_path"]).exists()
    assert Path(output["weight_map_path"]).exists()
    assert Path(output["coverage_map_path"]).exists()
    assert Path(output["dq_map_path"]).exists()
    assert output["master_path"] == artifact["master_path"]
    assert output["weight_map_path"] == artifact["weight_map_path"]
    assert output["coverage_map_path"] == artifact["coverage_map_path"]
    assert output["dq_map_path"] == artifact["dq_map_path"]
    assert output["output_write_storage"] == artifact["output_write_storage"]
    assert output["low_rejection_map_path"] is None
    assert output["high_rejection_map_path"] is None
    assert artifact["low_rejection_map_path"] is None
    assert artifact["high_rejection_map_path"] is None
    assert not list((run / "integration").glob("resident_low_rejection_map_*.fits"))
    assert not list((run / "integration").glob("resident_high_rejection_map_*.fits"))
    assert "low_rejection" in output["output_map_policy"]["skipped"]
    assert "high_rejection" in output["output_map_policy"]["skipped"]
    assert "dq" in output["output_map_policy"]["written"]
    assert "valid" in output["dq_summary"]
    assert output["dq_coverage_provenance"] == artifact["dq_coverage_provenance"]
    assert output["dq_provenance_summary"] == artifact["dq_provenance_summary"]
    assert output["dq_provenance_summary"]["source_schema"] == "resident_dq_coverage_provenance"
    assert output["dq_provenance_summary"]["engine"] == "cuda_resident_stack"
    assert output["dq_provenance_summary"]["active_frame_count"] == 2
    provenance = output["dq_coverage_provenance"]
    assert provenance["available"] is True
    assert provenance["source_terms"][:3] == ["post_rejection_coverage", "low_rejection", "high_rejection"]
    assert "geometric_warp_coverage" in provenance["source_terms"]
    assert provenance["active_frame_count"] == 2
    assert provenance["geometric_warp_coverage_frame_count"] == 2
    assert provenance["geometric_frame_count_matches_active"] is True
    assert "finite_pre_rejection_coverage" in provenance
    assert output["geometric_warp_coverage"]["available"] is True
    assert artifact["resident_registration"]["warp_coverage"]["available"] is True


def test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    stack_run = tmp_path / "resident_run_minimal_stack"
    fused_run = tmp_path / "resident_run_minimal_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    common_args = [
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "winsorized_sigma",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "off",
        "--resident-output-maps",
        "minimal",
    ]

    assert main(["run", "--out", str(stack_run), *common_args]) == 0
    assert main(
        [
            "run",
            "--out",
            str(fused_run),
            *common_args,
            "--resident-integration-dispatch",
            "fused_matrix",
        ]
    ) == 0

    stack_master = read_fits_data(stack_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_master = read_fits_data(fused_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    integration = read_json(fused_run / "integration_results.json")
    resident = read_json(fused_run / "resident_artifacts.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    dispatch = artifact["resident_integration_dispatch"]
    timing = dispatch["native_timing_s"]

    assert np.allclose(stack_master, fused_master, rtol=2e-5, atol=2e-4, equal_nan=True)
    assert output["output_map_policy"]["mode"] == "minimal"
    assert Path(output["master_path"]).exists()
    assert output["weight_map_path"] is None
    assert output["coverage_map_path"] is None
    assert output["low_rejection_map_path"] is None
    assert output["high_rejection_map_path"] is None
    assert output["dq_map_path"] is None
    assert output["dq_summary"] is None
    assert output["dq_coverage_provenance"]["available"] is False
    assert output["geometric_warp_coverage"]["available"] is False
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["download_mode"] == "master_weight"
    assert dispatch["diagnostic_maps_downloaded"] is False
    assert timing["download_mode"] == "master_weight"
    assert timing["diagnostic_maps_downloaded"] is False
    assert timing["output_bytes"] == 16 * 16 * 4 * 2


def test_cli_resident_cuda_audit_output_maps_mirror_paths(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_audit_maps"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--until-stage",
                "integration",
                "--local-normalization",
                "off",
                "--integration-rejection",
                "sigma_clip",
                "--integration-weighting",
                "none",
                "--resident-registration",
                "off",
                "--resident-output-maps",
                "audit",
            ]
        )
        == 0
    )

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    for key in [
        "master_path",
        "weight_map_path",
        "coverage_map_path",
        "low_rejection_map_path",
        "high_rejection_map_path",
        "dq_map_path",
    ]:
        assert output[key] == artifact[key]
        assert Path(artifact[key]).exists()
    assert output["output_write_storage"] == artifact["output_write_storage"]
    assert output["output_map_policy"]["written"] == artifact["output_map_policy"]["written"]
    assert "low_rejection" in artifact["output_map_policy"]["written"]
    assert "high_rejection" in artifact["output_map_policy"]["written"]


def test_cli_resident_cuda_run_ncc_subpixel_registration_smoke(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_ncc"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "on",
            "--resident-local-normalization-mode",
            "grid_mean_std",
            "--resident-local-normalization-tile-size",
            "8",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "translation_ncc_subpixel",
            "--resident-registration-max-shift",
            "4",
            "--resident-ncc-sample-stride",
            "2",
            "--resident-ncc-fallback-score-threshold",
            "1.0",
            "--resident-subpixel-radius-steps",
            "2",
            "--resident-subpixel-step",
            "0.5",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    local_norm = read_json(run / "local_norm_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    assert integration["outputs"][0]["resident_registration"] == "translation_ncc_subpixel"
    assert integration["outputs"][0]["resident_local_normalization"] == "resident_grid_mean_std"
    assert registration["transform_model"] == "translation_ncc_subpixel"
    assert local_norm["source_stage"] == "resident_calibrated_stack"
    assert local_norm["enabled"] is True
    assert local_norm["mode"] == "resident_grid_mean_std"
    assert local_norm["groups"][0]["frame_results"][0]["status"] == "reference"
    assert local_norm["groups"][0]["frame_results"][1]["grid_coefficients"]["tile_size"] == 8
    assert local_norm["groups"][0]["frame_results"][1]["grid_coefficients"]["valid_pixel_total"] > 0
    assert registration["results"][0]["status"] == "reference"
    assert resident_registration["mode"] == "translation_ncc_subpixel"
    assert resident["artifacts"][0]["resident_local_normalization"]["enabled"] is True
    assert resident["artifacts"][0]["resident_local_normalization"]["mode"] == "resident_grid_mean_std"
    assert resident["artifacts"][0]["resident_local_normalization"]["tile_size"] == 8
    assert resident_registration["max_shift"] == 4
    assert resident_registration["ncc_sample_stride"] == 2
    assert resident_registration["ncc_fallback_score_threshold"] == 1.0
    assert resident_registration["subpixel_radius_steps"] == 2
    assert resident_registration["subpixel_step"] == 0.5
    assert any("ncc_fallback_stride=1" == item for item in registration["results"][1]["warnings"])


def test_cli_resident_cuda_run_star_catalog_registration_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_star_catalog"

    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "translation_star_catalog",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "0.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]

    assert registration["transform_model"] == "translation_star_catalog"
    assert registration["results"][0]["status"] == "reference"
    assert resident_registration["mode"] == "translation_star_catalog"
    assert resident_registration["star_threshold"] == 30.0
    assert resident_registration["star_max_candidates"] == 16
    assert resident_registration["star_tolerance_px"] == 0.5
    assert resident_registration["star_grid_cols"] == 4
    assert resident_registration["star_grid_rows"] == 4
    assert resident_registration["star_threshold_mode"] == "fixed"
    assert resident_registration["star_prior"] == "none"


def test_cli_resident_cuda_run_star_catalog_auto_threshold_aligns_shifted_pair(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_star_catalog_auto"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "translation_star_catalog",
            "--resident-star-threshold",
            "0",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "0.5",
            "--resident-registration-max-shift",
            "8",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-prior",
            "ncc",
            "--resident-star-prior-radius-px",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert resident_registration["star_threshold_mode"] == "auto_mean_std"
    assert resident_registration["star_threshold"] == 0.0
    assert resident_registration["star_prior"] == "ncc"
    assert resident_registration["star_prior_radius_px"] == 2.0
    assert moving["status"] == "ok"
    assert moving["matched_stars"] >= 6
    assert abs(moving["matrix"][0][2] + 3.0) < 1.0e-5
    assert abs(moving["matrix"][1][2] - 2.0) < 1.0e-5
    assert any("selected_star_threshold=" in warning for warning in moving["warnings"])
    assert any("star_prior_model=ncc" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_similarity_catalog"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    for frame in plan_payload["frames"]:
        if frame["frame_type"] == "light":
            frame.setdefault("header_summary", {})["PIERSIDE"] = "West"
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_catalog_tolerance_px": 1.5,
            "cuda_catalog_min_pair_distance": 8.0,
            "cuda_catalog_similarity_top_k": 3,
            "cuda_catalog_min_scale": 0.99,
            "cuda_catalog_max_scale": 1.01,
            "cuda_catalog_max_abs_rotation_rad": 0.02,
            "cuda_catalog_pixel_refine_coarse_stride": 1,
            "cuda_catalog_pixel_refine_final_stride": 1,
            "cuda_catalog_min_pixel_ncc": 0.1,
            "cuda_catalog_min_selected_seed_inliers": 3,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_catalog",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-registration-max-shift",
            "8",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-prior",
            "auto_pierside",
            "--resident-star-prior-radius-px",
            "2",
            "--resident-star-core-preselect-top-k",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]

    assert registration["transform_model"] == "similarity_cuda_catalog"
    assert integration["outputs"][0]["resident_registration"] == "similarity_cuda_catalog"
    assert resident_registration["mode"] == "similarity_cuda_catalog"
    assert resident_registration["star_core_preselect_top_k"] == 2
    assert resident_registration["star_core_guard"] is True
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_catalog"
    assert moving["matched_stars"] >= 3
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert any("similarity_top_k=3" in warning for warning in moving["warnings"])
    assert any("similarity_prior_requested=auto_pierside" in warning for warning in moving["warnings"])
    assert any("similarity_prior_effective=ncc" in warning for warning in moving["warnings"])
    assert any("similarity_orientation_mode=pierside_same" in warning for warning in moving["warnings"])
    assert any("similarity_seed_count=2" in warning for warning in moving["warnings"])
    assert any("similarity_refined_seed_count=2" in warning for warning in moving["warnings"])
    assert any("similarity_catalog_selector=resident_grid_top_nms" in warning for warning in moving["warnings"])
    assert any("similarity_star_core_preselect_enabled=True" in warning for warning in moving["warnings"])
    assert any("similarity_star_core_guard_status=" in warning for warning in moving["warnings"])
    assert any("similarity_quality_gate_status=ok" in warning for warning in moving["warnings"])
    assert any("resident CUDA catalog similarity" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_similarity_triangle"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-grid-top-per-cell",
            "2",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-triangle-min-agreement-score",
            "0.01",
            "--resident-triangle-agreement-rms-scale",
            "200",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]

    assert registration["transform_model"] == "similarity_cuda_triangle"
    assert integration["outputs"][0]["resident_registration"] == "similarity_cuda_triangle"
    assert resident_registration["mode"] == "similarity_cuda_triangle"
    assert resident_registration["triangle_descriptor_radius"] == 0.08
    assert resident_registration["triangle_neighbors"] == 5
    assert resident_registration["triangle_max_descriptors"] == 256
    assert resident_registration["triangle_grid_top_per_cell"] == 2
    assert resident_registration["triangle_nms_scan_candidates"] == 96
    assert resident_registration["triangle_nms_min_separation_px"] == 2.0
    assert resident_registration["triangle_catalog_batch"] is True
    assert resident_registration["triangle_catalog_batch_mode"] == "grid_top_nms_fixed_threshold"
    assert resident_registration["triangle_catalog_timing_model"] == "per_frame_launch_sync_download"
    assert resident_registration["triangle_catalog_sort_mode"] == "shared_bitonic_power2"
    assert resident_registration["star_catalog_deterministic"] is True
    assert resident_registration["triangle_catalog_topk_mode"] == "deterministic_parallel_per_cell"
    assert resident_registration["triangle_catalog_native_total_s"] >= 0.0
    assert resident_registration["triangle_catalog_native_sync_s"] >= 0.0
    assert resident_registration["triangle_catalog_native_output_download_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_batch"] is True
    assert resident_registration["triangle_descriptor_fit_batch_mode"] == (
        "native_batch_shared_reference_device"
    )
    assert resident_registration["triangle_descriptor_fit_reference_device_reuse"] is True
    assert resident_registration["triangle_descriptor_fit_reference_device_bytes"] > 0
    assert resident_registration["triangle_descriptor_fit_moving_device_reuse"] is True
    assert resident_registration["triangle_descriptor_fit_moving_device_bytes"] > 0
    assert resident_registration["triangle_descriptor_fit_output_device_reuse"] is True
    assert resident_registration["triangle_descriptor_fit_output_device_bytes"] > 0
    assert resident_registration["triangle_descriptor_fit_best_reduction_mode"] == (
        "single_block_parallel_score_rms_index"
    )
    assert resident_registration["triangle_descriptor_fit_batch_timing_model"] == (
        "per_frame_reused_buffers_sync_timed"
    )
    assert resident_registration["triangle_descriptor_fit_native_host_prepare_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_reference_alloc_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_reference_upload_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_workspace_alloc_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_moving_upload_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_kernel_sync_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_output_download_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_frame_total_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_total_s"] >= (
        resident_registration["triangle_descriptor_fit_native_host_prepare_s"]
        + resident_registration["triangle_descriptor_fit_native_reference_alloc_s"]
        + resident_registration["triangle_descriptor_fit_native_reference_upload_s"]
        + resident_registration["triangle_descriptor_fit_native_workspace_alloc_s"]
    )
    assert resident_registration["triangle_warp_batch"] is True
    assert resident_registration["triangle_warp_batch_mode"] == "native_matrix_bilinear_frames"
    assert resident_registration["triangle_warp_batch_timing_model"] == "off"
    assert resident_registration["triangle_warp_batch_native_inverse_upload_mode"] == "off"
    assert resident_registration["triangle_warp_batch_frame_count"] == 0
    assert resident_registration["triangle_warp_batch_fallback_frame_count"] == 1
    assert resident_registration["triangle_warp_batch_native_inverse_prepare_s"] == 0.0
    assert resident_registration["triangle_warp_batch_native_inverse_batch_alloc_s"] == 0.0
    assert resident_registration["triangle_warp_batch_native_inverse_batch_bytes"] == 0
    assert resident_registration["triangle_warp_batch_native_index_upload_s"] == 0.0
    assert resident_registration["triangle_warp_batch_native_inverse_upload_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_kernel_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_coverage_reduce_enqueue_s"] == 0.0
    assert resident_registration["triangle_warp_batch_native_scatter_enqueue_s"] == 0.0
    assert resident_registration["triangle_warp_batch_native_device_copy_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_sync_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_total_s"] == 0.0
    assert resident_registration["triangle_warp_batch_native_chunk_frames"] == 0
    assert resident_registration["triangle_warp_batch_native_chunk_count"] == 0
    assert resident_registration["triangle_warp_batch_native_workspace_bytes"] == 0
    assert resident_registration["triangle_warp_batch_native_warp_kernel_launches"] == 0
    assert resident_registration["triangle_warp_batch_native_scatter_kernel_launches"] == 0
    assert resident_registration["triangle_pixel_refine_requested_coarse_stride"] == 1
    assert resident_registration["triangle_pixel_refine_requested_final_stride"] == 2
    assert resident_registration["triangle_pixel_refine_fast_coarse"] is True
    assert resident_registration["triangle_pixel_refine_fast_coarse_mode"] == "coarse_stride_floor_to_final"
    assert resident_registration["triangle_pixel_refine_coarse_stride_adjusted"] is True
    assert resident_registration["triangle_pixel_refine_coarse_stride"] == 2
    assert resident_registration["triangle_pixel_refine_final_stride"] == 2
    assert resident_registration["triangle_min_agreement_score"] == 0.01
    assert resident_registration["triangle_agreement_rms_scale"] == 200.0
    assert resident_registration["triangle_pixel_refine_batch"] is True
    assert resident_registration["triangle_pixel_refine_batch_mode"] == "native_batch_one_seed_per_frame"
    assert resident_registration["triangle_pixel_refine_batch_metric_mode"] == "flattened_frame_candidate_grid"
    assert resident_registration["triangle_pixel_refine_batch_metric_kernel_launches"] == 2
    assert resident_registration["triangle_pixel_refine_coarse_total_candidates"] > 0
    assert resident_registration["triangle_pixel_refine_fine_total_candidates"] > 0
    assert resident_registration["triangle_pixel_refine_metric_workload_model"] == (
        "candidate_count_x_sampled_pixels"
    )
    assert resident_registration["triangle_pixel_refine_coarse_sampled_pixels_per_candidate"] > 0
    assert resident_registration["triangle_pixel_refine_fine_sampled_pixels_per_candidate"] > 0
    assert resident_registration["triangle_pixel_refine_coarse_metric_sample_evaluations"] == (
        resident_registration["triangle_pixel_refine_coarse_total_candidates"]
        * resident_registration["triangle_pixel_refine_coarse_sampled_pixels_per_candidate"]
    )
    assert resident_registration["triangle_pixel_refine_fine_metric_sample_evaluations"] == (
        resident_registration["triangle_pixel_refine_fine_total_candidates"]
        * resident_registration["triangle_pixel_refine_fine_sampled_pixels_per_candidate"]
    )
    assert resident_registration["triangle_pixel_refine_coarse_metric_megasamples_per_s"] >= 0.0
    assert resident_registration["triangle_pixel_refine_fine_metric_megasamples_per_s"] >= 0.0
    assert resident_registration["triangle_pixel_refine_workspace_mode"] == "shared_flattened_candidate_metric_buffers"
    assert resident_registration["triangle_pixel_refine_workspace_bytes"] > 0
    assert resident_registration["triangle_pixel_refine_workspace_candidate_capacity"] > 0
    assert resident_registration["triangle_determinism_signature_mode"] == (
        "catalog_descriptor_fit_exact_float32_sha256"
    )
    assert resident_registration["triangle_determinism_moving_frame_count"] == 1
    assert resident_registration["triangle_determinism_threshold_count"] == 1
    assert len(resident_registration["triangle_determinism_reference_combined_sha256"]) == 64
    assert len(resident_registration["triangle_determinism_moving_catalog_combined_sha256"]) == 64
    assert len(resident_registration["triangle_determinism_selected_fit_combined_sha256"]) == 64
    determinism = resident_registration["triangle_determinism"]
    assert determinism["signature_mode"] == "catalog_descriptor_fit_exact_float32_sha256"
    assert set(determinism["moving"]) == {moving["frame_id"]}
    moving_signature = determinism["moving"][moving["frame_id"]]
    assert moving_signature["moving_catalog"]["stored_count"] >= 3
    assert moving_signature["moving_descriptor"]["count"] > 0
    assert moving_signature["selected_fit"]["status"] == "ok"
    timing = resident["artifacts"][0]["timing_s"]
    registration_components = resident["artifacts"][0]["fine_timing"]["registration_component_seconds"]
    assert timing["resident_registration_component_accounted"] >= 0.0
    assert timing["resident_registration_orchestration"] >= 0.0
    assert registration_components["triangle_moving_catalog_batch"] >= 0.0
    assert registration_components["triangle_moving_catalog"] >= 0.0
    assert registration_components["triangle_moving_descriptors"] >= 0.0
    assert registration_components["triangle_descriptor_fit"] >= 0.0
    assert registration_components["triangle_descriptor_fit_batch"] >= 0.0
    assert registration_components["triangle_descriptor_fit_native_moving_upload"] >= 0.0
    assert registration_components["triangle_descriptor_fit_native_kernel_sync"] >= 0.0
    assert registration_components["triangle_descriptor_fit_native_output_download"] >= 0.0
    assert registration_components["triangle_warp"] >= 0.0
    assert "triangle_warp_native_batch" not in registration_components
    assert "triangle_warp_native_sync" not in registration_components
    assert registration_components["triangle_pixel_refine_batch"] >= 0.0
    assert registration_components["triangle_pixel_refine_native_coarse"] >= 0.0
    assert registration_components["triangle_pixel_refine_native_fine"] >= 0.0
    assert resident["artifacts"][0]["resident_warp_scratch_bytes"] > 0
    assert resident["artifacts"][0]["resident_io_pipeline"]["warp_scratch_bytes"] > 0
    assert resident["artifacts"][0]["resident_warp_copy_mode"] == "default_stream_async_device_to_device"
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert moving["matched_stars"] >= 3
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert any("reference_descriptors=" in warning for warning in moving["warnings"])
    assert any("moving_descriptors=" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_selector=resident_grid_top_nms" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_timing_model=per_frame_launch_sync_download" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_sort_mode=shared_bitonic_power2" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_topk_mode=deterministic_parallel_per_cell" in warning for warning in moving["warnings"])
    assert any("triangle_grid_top_per_cell=2" in warning for warning in moving["warnings"])
    assert any("triangle_nms_scan_candidates=96" in warning for warning in moving["warnings"])
    assert any("triangle_nms_min_separation_px=2" in warning for warning in moving["warnings"])
    assert any("triangle_quality_gate_status=ok" in warning for warning in moving["warnings"])
    assert any("triangle_agreement_score=" in warning for warning in moving["warnings"])
    assert any("triangle_agreement_status=ok" in warning for warning in moving["warnings"])
    assert any("triangle_min_agreement_score=0.01" in warning for warning in moving["warnings"])
    assert any("triangle_descriptor_fit_batch=true" in warning for warning in moving["warnings"])
    assert any(
        "triangle_descriptor_fit_best_reduction_mode=single_block_parallel_score_rms_index" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_descriptor_fit_batch_timing_model=per_frame_reused_buffers_sync_timed" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_descriptor_fit_reference_device_reuse=true" in warning
        for warning in moving["warnings"]
    )
    assert any("triangle_descriptor_fit_frame_kernel_sync_s=" in warning for warning in moving["warnings"])
    assert any("triangle_determinism_moving_catalog_signature=" in warning for warning in moving["warnings"])
    assert any("triangle_determinism_selected_fit_signature=" in warning for warning in moving["warnings"])
    assert any("triangle_pixel_refine_mode=native_batch" in warning for warning in moving["warnings"])
    assert any("triangle_pixel_refine_fast_coarse=true" in warning for warning in moving["warnings"])
    assert any(
        "triangle_pixel_refine_fast_coarse_mode=coarse_stride_floor_to_final" in warning
        for warning in moving["warnings"]
    )
    assert any("triangle_pixel_refine_coarse_stride_adjusted=true" in warning for warning in moving["warnings"])
    assert any("triangle_pixel_refine_effective_coarse_stride=2" in warning for warning in moving["warnings"])
    assert any(
        "triangle_pixel_refine_batch_metric_mode=flattened_frame_candidate_grid" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_pixel_refine_metric_workload_model=candidate_count_x_sampled_pixels" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_pixel_refine_coarse_metric_sample_evaluations=" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_pixel_refine_workspace_mode=shared_flattened_candidate_metric_buffers" in warning
        for warning in moving["warnings"]
    )
    assert any("resident_registration_application=translation_bilinear" in warning for warning in moving["warnings"])
    assert any("triangle_warp_batch=false" in warning for warning in moving["warnings"])
    assert any("triangle_warp_batch_mode=native_matrix_bilinear_frames" in warning for warning in moving["warnings"])
    assert any(
        "triangle_warp_batch_timing_model=per_frame" in warning
        for warning in moving["warnings"]
    )
    assert any("resident CUDA triangle descriptor similarity" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "tri_no_refine"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-grid-top-per-cell",
            "2",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert resident_registration["triangle_pixel_refine"] is False
    assert resident_registration["triangle_pixel_refine_batch"] is False
    assert resident_registration["triangle_pixel_refine_batch_mode"] == "off"
    assert resident_registration["triangle_pixel_refine_metric_workload_model"] == "off"
    assert resident_registration["triangle_pixel_refine_workspace_bytes"] == 0
    assert resident_registration["triangle_translation_refine"] is True
    assert resident_registration["triangle_centroid_refine"] is True
    assert resident_registration["triangle_centroid_refine_mode"] == "resident_gpu_window_centroid"
    assert resident_registration["triangle_centroid_refine_catalog_count"] >= 2
    assert resident_registration["triangle_centroid_refine_star_count"] > 0
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert "triangle_centroid_refine_enabled=true" in moving["warnings"]
    assert "triangle_centroid_refine_mode=resident_gpu_window_centroid" in moving["warnings"]
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert all("triangle_pixel_refine_mode=" not in warning for warning in moving["warnings"])
    assert any("resident CUDA triangle descriptor similarity" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rq"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    quality_reference_id = str(light_by_stem["light_002"]["id"])
    moving_id = str(light_by_stem["light_001"]["id"])
    write_json(plan, plan_payload)
    run.mkdir(parents=True)
    (run / "calib_cache" / "resident_masters").mkdir(parents=True)
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": quality_reference_id,
            "frame_quality": [
                {"frame_id": moving_id, "reference_candidate": True, "star_count": 8},
                {"frame_id": quality_reference_id, "reference_candidate": True, "star_count": 10},
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-grid-top-per-cell",
            "2",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-triangle-min-agreement-score",
            "0.01",
            "--resident-triangle-agreement-rms-scale",
            "200",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    reference_rows = [item for item in registration["results"] if item["status"] == "reference"]
    moving = [item for item in registration["results"] if item["frame_id"] == moving_id][0]

    assert [item["frame_id"] for item in reference_rows] == [quality_reference_id]
    assert resident_registration["reference_frame_id"] == quality_reference_id
    assert resident_registration["selected_reference_frame_id"] == quality_reference_id
    assert resident_registration["reference_selection_source"] == "frame_quality"
    assert resident_registration["quality_reference_frame_id"] == quality_reference_id
    assert resident_registration["quality_reference_status"] == "frame_quality"
    assert resident_registration["quality_reference_path"] == str(run / "frame_quality.json")
    assert moving["status"] == "ok"
    assert abs(moving["matrix"][0][2] - 3.0) < 0.5
    assert abs(moving["matrix"][1][2] + 2.0) < 0.5


def test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    stack_run = tmp_path / "resident_run_similarity_triangle_stack"
    fused_run = tmp_path / "resident_run_similarity_triangle_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    common_args = [
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "none",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "similarity_cuda_triangle",
        "--resident-star-threshold",
        "30",
        "--resident-star-max-candidates",
        "16",
        "--resident-star-tolerance-px",
        "1.5",
        "--resident-star-grid-cols",
        "4",
        "--resident-star-grid-rows",
        "4",
        "--resident-star-catalog-deterministic",
        "--resident-triangle-pixel-refine-final-stride",
        "2",
        "--resident-triangle-pixel-refine-fast-coarse",
        "--resident-warp-interpolation",
        "bilinear",
        "--resident-output-maps",
        "minimal",
        "--reference-frame-id",
        "light_001",
    ]

    assert main(["run", "--out", str(stack_run), *common_args]) == 0
    assert main(
        [
            "run",
            "--out",
            str(fused_run),
            *common_args,
            "--resident-integration-dispatch",
            "fused_matrix",
        ]
    ) == 0

    stack_master = read_fits_data(stack_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_master = read_fits_data(fused_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_registration = read_json(fused_run / "registration_results.json")
    fused_resident = read_json(fused_run / "resident_artifacts.json")
    fused_integration = read_json(fused_run / "integration_results.json")
    moving = [item for item in fused_registration["results"] if item["status"] != "reference"][0]
    artifact = fused_resident["artifacts"][0]
    resident_registration = artifact["resident_registration"]
    dispatch = artifact["resident_integration_dispatch"]
    warp_coverage = resident_registration["warp_coverage"]

    assert np.allclose(stack_master, fused_master, rtol=2e-5, atol=2e-4, equal_nan=True)
    assert fused_integration["outputs"][0]["resident_integration_dispatch"] == "fused_matrix"
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["used"] is True
    assert "similarity_cuda_triangle" in dispatch["eligible_registration_modes"]
    assert dispatch["deferred_matrix_frame_count"] == 1
    assert dispatch["download_mode"] == "master_weight"
    assert dispatch["diagnostic_maps_downloaded"] is False
    assert resident_registration["mode"] == "similarity_cuda_triangle"
    assert resident_registration["triangle_warp_batch"] is False
    assert resident_registration["triangle_warp_batch_mode"] == "fused_matrix_deferred"
    assert resident_registration["triangle_warp_batch_timing_model"] == "fused_integration_deferred"
    assert resident_registration["triangle_warp_batch_frame_count"] == 0
    assert resident_registration["triangle_warp_batch_fallback_frame_count"] == 0
    assert resident_registration["triangle_fused_matrix_deferred"] is True
    assert resident_registration["triangle_fused_matrix_deferred_count"] == 1
    assert warp_coverage["native_source"] == "ResidentCalibratedStack fused matrix integration geometric coverage"
    assert warp_coverage["fused_deferred_frame_count"] == 1
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert any("resident_registration_application=fused_matrix_deferred" == warning for warning in moving["warnings"])
    assert any("triangle_warp_batch=false" == warning for warning in moving["warnings"])
    assert any("triangle_warp_batch_mode=fused_matrix_deferred" == warning for warning in moving["warnings"])
    assert all("resident_registration_application=translation_bilinear" != warning for warning in moving["warnings"])


def test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "auto_bilinear_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-integration-dispatch",
            "auto",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-warp-interpolation",
            "bilinear",
            "--resident-output-maps",
            "minimal",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    dispatch = resident["artifacts"][0]["resident_integration_dispatch"]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert dispatch["requested_mode"] == "auto"
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["effective_mode"] == "fused_matrix"
    assert dispatch["selection_reason"] == "auto_fused_bilinear_matrix_route"
    assert dispatch["auto_policy"]["enabled"] is True
    assert dispatch["auto_policy"]["verified_fast_path"] is True
    assert dispatch["used"] is True
    assert dispatch["deferred_matrix_frame_count"] == 1
    assert integration["outputs"][0]["resident_integration_dispatch"] == "fused_matrix"
    assert integration["outputs"][0]["resident_integration_dispatch_requested"] == "auto"
    assert resident_registration["triangle_fused_matrix_deferred"] is True
    assert resident_registration["triangle_fused_matrix_deferred_count"] == 1
    assert any("resident_registration_application=fused_matrix_deferred" == warning for warning in moving["warnings"])


def test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "auto_lanczos_stack"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "winsorized_sigma",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-integration-dispatch",
            "auto",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-warp-interpolation",
            "lanczos3",
            "--resident-output-maps",
            "minimal",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    dispatch = resident["artifacts"][0]["resident_integration_dispatch"]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert dispatch["requested_mode"] == "auto"
    assert dispatch["mode"] == "stack"
    assert dispatch["effective_mode"] == "stack"
    assert dispatch["selection_reason"] == "auto_stack_non_bilinear_matrix_route"
    assert dispatch["auto_policy"]["enabled"] is True
    assert dispatch["auto_policy"]["verified_fast_path"] is False
    assert dispatch["auto_policy"]["conservative_stack_for_non_bilinear"] is True
    assert dispatch["used"] is False
    assert dispatch["deferred_matrix_frame_count"] == 0
    assert integration["outputs"][0]["resident_integration_dispatch"] == "stack"
    assert integration["outputs"][0]["resident_integration_dispatch_requested"] == "auto"
    assert resident_registration["triangle_fused_matrix_deferred"] is False
    assert resident_registration["triangle_fused_matrix_deferred_count"] == 0
    assert resident_registration["triangle_warp_batch_mode"] == "native_matrix_lanczos3_frames"
    assert any("resident_registration_application=matrix_lanczos3" == warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_catalog_rejects_low_quality_matrix(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_similarity_catalog_quality_gate"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_catalog_tolerance_px": 1.5,
            "cuda_catalog_min_pair_distance": 8.0,
            "cuda_catalog_similarity_top_k": 3,
            "cuda_catalog_min_scale": 0.99,
            "cuda_catalog_max_scale": 1.01,
            "cuda_catalog_max_abs_rotation_rad": 0.02,
            "cuda_catalog_pixel_refine_coarse_stride": 1,
            "cuda_catalog_pixel_refine_final_stride": 1,
            "cuda_catalog_min_pixel_ncc": 1.01,
            "cuda_catalog_min_selected_seed_inliers": 3,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_catalog",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-registration-max-shift",
            "8",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-prior",
            "ncc",
            "--resident-star-prior-radius-px",
            "2",
            "--resident-star-core-preselect-top-k",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    integration = read_json(run / "integration_results.json")
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert moving["status"] == "failed"
    assert integration["frame_weights"][moving["frame_id"]] == 0.0
    assert any("failed quality gate" in warning for warning in moving["warnings"])
    assert any("similarity_quality_gate_status=failed" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_external_matrix_registration(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    external_registration = tmp_path / "external_registration_results.json"
    frame_weight_proposal = tmp_path / "frame_weight_proposal.json"
    tile_local_policy_replay = tmp_path / "tile_local_policy_replay.json"
    run = tmp_path / "resident_run_external_matrix"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    reference_id = str(light_by_stem["light_001"]["id"])
    moving_id = str(light_by_stem["light_002"]["id"])
    similarity_matrix = [
        [1.0, 0.001, -3.0],
        [-0.001, 1.0, 2.0],
        [0.0, 0.0, 1.0],
    ]
    write_json(
        external_registration,
        {
            "schema_version": 1,
            "reference_frame_id": reference_id,
            "registration_results": [
                {
                    "frame_id": reference_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    "matched_stars": 8,
                    "inliers": 8,
                    "rms_px": 0.0,
                    "status": "reference",
                    "warnings": [],
                },
                {
                    "frame_id": moving_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": similarity_matrix,
                    "matched_stars": 12,
                    "inliers": 10,
                    "rms_px": 0.4,
                    "status": "ok",
                    "warnings": ["synthetic external similarity matrix"],
                },
            ],
        },
    )
    write_json(
        frame_weight_proposal,
        {
            "artifact_type": "frame_weight_proposal",
            "method": "control_ratio",
            "source_integration_audit": "localized_audit.json",
            "frame_multipliers": [
                {
                    "frame_id": moving_id,
                    "multiplier": 0.25,
                    "reason": "unit-test localized contribution proposal",
                }
            ],
        },
    )
    write_json(
        tile_local_policy_replay,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": [moving_id],
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "boost_tiles": 1,
                "mean_abs_residual_before": 0.1,
                "mean_abs_residual_after": 0.02,
            },
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 8, "y1": 8},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                    "clamped": True,
                    "selected_frame_row_count": 1,
                    "canonical_delta_contribution_adu": 1.0,
                    "signed_residual_reference_units_before": -0.1,
                    "signed_residual_reference_units_after": -0.02,
                    "moves_toward_reference": True,
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "external_matrix",
            "--resident-registration-results",
            str(external_registration),
            "--resident-warp-interpolation",
            "lanczos3",
            "--resident-warp-clamping-threshold",
            "0.30",
            "--resident-registration-motion-weighting",
            "translation_mad",
            "--resident-registration-motion-threshold-sigma",
            "8",
            "--resident-frame-weight-proposal",
            str(frame_weight_proposal),
            "--resident-tile-local-policy-replay",
            str(tile_local_policy_replay),
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["frame_id"] == moving_id][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    weighting = resident["artifacts"][0]["resident_integration_weighting"]
    motion = weighting["registration_motion_weighting"]
    proposal = weighting["frame_weight_proposal"]
    tile_local = weighting["tile_local_policy_replay"]
    moving_weighting = [item for item in weighting["frame_results"] if item["frame_id"] == moving_id][0]

    assert integration["outputs"][0]["resident_registration"] == "external_matrix"
    assert integration["frame_weights"][moving_id] == 0.25
    assert registration["transform_model"] == "external_matrix"
    assert registration["warnings"][0].startswith("resident registration consumed external matrices")
    assert "lanczos3" in registration["warnings"][0]
    assert resident_registration["mode"] == "external_matrix"
    assert resident_registration["warp_interpolation"] == "lanczos3"
    assert resident_registration["warp_clamping_threshold"] == 0.30
    assert resident_registration["registration_motion_weighting_mode"] == "translation_mad"
    assert resident_registration["registration_motion_downweighted_frame_count"] == 0
    assert resident_registration["frame_weight_proposal_path"] == str(frame_weight_proposal)
    assert resident_registration["frame_weight_proposal_frame_count"] == 1
    assert resident_registration["frame_weight_proposal_downweighted_frame_count"] == 1
    assert motion["enabled"] is True
    assert motion["mode"] == "translation_mad"
    assert motion["threshold_sigma"] == 8.0
    assert motion["reason"] == "fewer_than_three_eligible_frames"
    assert proposal["enabled"] is True
    assert proposal["path"] == str(frame_weight_proposal)
    assert proposal["applied_downweighted_frame_count"] == 1
    assert tile_local["enabled"] is True
    assert tile_local["path"] == str(tile_local_policy_replay)
    assert tile_local["applied"] is False
    assert tile_local["target_frame_ids"] == [moving_id]
    assert tile_local["tiles"][0]["multiplier"] == 2.0
    assert moving_weighting["frame_weight_proposal_multiplier"] == 0.25
    assert moving_weighting["status"] == "frame_weight_proposal_downweighted"
    assert resident_registration["external_registration_results_path"] == str(external_registration)
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity"
    assert moving["matched_stars"] == 12
    assert moving["inliers"] == 10
    assert np.allclose(np.asarray(moving["matrix"], dtype=np.float32), np.asarray(similarity_matrix, dtype=np.float32))
    assert any("external_registration_application=matrix_lanczos3" == item for item in moving["warnings"])
    assert any("frame_weight_proposal_multiplier=0.25" == item for item in moving["warnings"])


def test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    external_registration = tmp_path / "external_registration_results.json"
    stack_run = tmp_path / "resident_run_external_matrix_stack"
    fused_run = tmp_path / "resident_run_external_matrix_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    reference_id = str(light_by_stem["light_001"]["id"])
    moving_id = str(light_by_stem["light_002"]["id"])
    similarity_matrix = [
        [1.0, 0.001, -3.0],
        [-0.001, 1.0, 2.0],
        [0.0, 0.0, 1.0],
    ]
    write_json(
        external_registration,
        {
            "schema_version": 1,
            "reference_frame_id": reference_id,
            "registration_results": [
                {
                    "frame_id": reference_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    "matched_stars": 8,
                    "inliers": 8,
                    "rms_px": 0.0,
                    "status": "reference",
                    "warnings": [],
                },
                {
                    "frame_id": moving_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": similarity_matrix,
                    "matched_stars": 12,
                    "inliers": 10,
                    "rms_px": 0.4,
                    "status": "ok",
                    "warnings": ["synthetic external similarity matrix"],
                },
            ],
        },
    )

    common_args = [
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "winsorized_sigma",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "external_matrix",
        "--resident-registration-results",
        str(external_registration),
        "--resident-warp-interpolation",
        "bilinear",
    ]

    assert main(["run", "--out", str(stack_run), *common_args]) == 0
    assert main(
        [
            "run",
            "--out",
            str(fused_run),
            *common_args,
            "--resident-integration-dispatch",
            "fused_matrix",
        ]
    ) == 0

    stack_master = read_fits_data(stack_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_master = read_fits_data(fused_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_registration = read_json(fused_run / "registration_results.json")
    fused_resident = read_json(fused_run / "resident_artifacts.json")
    fused_integration = read_json(fused_run / "integration_results.json")
    moving = [item for item in fused_registration["results"] if item["frame_id"] == moving_id][0]
    dispatch = fused_resident["artifacts"][0]["resident_integration_dispatch"]
    warp_coverage = fused_resident["artifacts"][0]["resident_registration"]["warp_coverage"]

    assert np.allclose(stack_master, fused_master, rtol=2e-5, atol=2e-4, equal_nan=True)
    assert fused_integration["outputs"][0]["resident_integration_dispatch"] == "fused_matrix"
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["used"] is True
    assert dispatch["deferred_matrix_frame_count"] == 1
    assert dispatch["native_timing_s"]["rejection"] == "winsorized_sigma"
    assert dispatch["native_timing_s"]["avoids_stack_scatter"] is True
    assert warp_coverage["native_source"] == "ResidentCalibratedStack fused matrix integration geometric coverage"
    assert warp_coverage["fused_deferred_frame_count"] == 1
    assert moving["status"] == "ok"
    assert any("external_registration_application=fused_matrix_deferred" == item for item in moving["warnings"])


def test_cli_resident_cuda_uses_planner_matching_master_sets(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_dark_group_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_matching_groups"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    master_stats = resident["artifacts"][0]["master_stats"]

    assert master_stats["calibration_group_policy"] == "planner_matching_groups_per_light"
    assert master_stats["set_count"] == 2
    assert {item["dark_count"] for item in master_stats["sets"].values()} == {1}
    assert len({item["dark_group"] for item in master_stats["sets"].values()}) == 2


def test_cli_resident_cuda_shared_master_cache_reuses_across_runs(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_dark_group_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    cache = tmp_path / "shared_resident_master_cache"
    run_a = tmp_path / "resident_cache_first"
    run_b = tmp_path / "resident_cache_second"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    base_args = [
        "run",
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "none",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "off",
        "--flat-floor",
        "0.05",
        "--resident-master-cache-dir",
        str(cache),
    ]

    assert main([*base_args, "--out", str(run_a)]) == 0
    assert main([*base_args, "--out", str(run_b)]) == 0

    first_sets = read_json(run_a / "resident_artifacts.json")["artifacts"][0]["master_stats"]["sets"]
    second_artifact = read_json(run_b / "resident_artifacts.json")["artifacts"][0]
    second_sets = second_artifact["master_stats"]["sets"]

    assert cache.exists()
    assert list(cache.glob("*_master_stats.json"))
    assert {item["cache_scope"] for item in first_sets.values()} == {"shared"}
    assert {item["cache_scope"] for item in second_sets.values()} == {"shared"}
    assert {item["cache_hit"] for item in first_sets.values()} == {False}
    assert {item["cache_hit"] for item in second_sets.values()} == {True}
    assert second_artifact["resident_io_pipeline"]["master_cache_scope"] == "shared"
    assert second_artifact["resident_io_pipeline"]["master_cache_dir"] == str(cache)
    assert "--resident-master-cache-dir" in (run_b / "run_command.txt").read_text(encoding="utf-8")


def test_resident_frame_exclusion_matches_id_name_or_stem():
    frame = {
        "id": "F000196",
        "path": r"C:\data\LIGHT_H_0136.fits",
    }

    assert _matches_any_token(frame, {"F000196"})
    assert _matches_any_token(frame, {"LIGHT_H_0136.fits"})
    assert _matches_any_token(frame, {"LIGHT_H_0136"})
    assert not _matches_any_token(frame, {"LIGHT_H_0137"})
