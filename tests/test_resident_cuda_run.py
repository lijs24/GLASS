from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from gpwbpp.cli import main
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.engine.resident_cuda import (
    _matches_any_token,
    _resident_similarity_frame_dispatch,
    _select_star_core_preselected_seed_indices,
    _select_star_guarded_seed,
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
    assert integration["source_stage"] == "resident_calibrated_stack"
    assert integration["outputs"][0]["backend"] == "cuda_resident_stack"
    assert integration["outputs"][0]["resident_registration"] == "translation_preview"
    assert integration["excluded_frame_tokens"] == ["does_not_exist"]
    assert integration["outputs"][0]["output_diagnostics"]["normalization_probe"]["method"]
    assert registration["source_stage"] == "resident_calibrated_stack"
    assert registration["results"][0]["status"] == "reference"
    assert state["current_stage"] == "integration"
    assert "resident_registration" in state["completed_stages"]
    assert "resident_integration" in state["completed_stages"]
    assert resident["backend"] == "cuda_resident_stack"
    assert resident["policy"]["flat_floor"] == 0.05
    assert resident["artifacts"][0]["resident_registration"]["mode"] == "translation_preview"
    assert resident["artifacts"][0]["output_diagnostics"]["clipping_probe"]["nonfinite_count"] == 0


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
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert moving["matched_stars"] >= 3
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert any("reference_descriptors=" in warning for warning in moving["warnings"])
    assert any("moving_descriptors=" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_selector=resident_grid_top_nms" in warning for warning in moving["warnings"])
    assert any("triangle_quality_gate_status=ok" in warning for warning in moving["warnings"])
    assert any("resident CUDA triangle descriptor similarity" in warning for warning in moving["warnings"])


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
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["frame_id"] == moving_id][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]

    assert integration["outputs"][0]["resident_registration"] == "external_matrix"
    assert registration["transform_model"] == "external_matrix"
    assert registration["warnings"][0].startswith("resident registration consumed external matrices")
    assert "lanczos3" in registration["warnings"][0]
    assert resident_registration["mode"] == "external_matrix"
    assert resident_registration["warp_interpolation"] == "lanczos3"
    assert resident_registration["warp_clamping_threshold"] == 0.30
    assert resident_registration["external_registration_results_path"] == str(external_registration)
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity"
    assert moving["matched_stars"] == 12
    assert moving["inliers"] == 10
    assert np.allclose(np.asarray(moving["matrix"], dtype=np.float32), np.asarray(similarity_matrix, dtype=np.float32))
    assert any("external_registration_application=matrix_lanczos3" == item for item in moving["warnings"])


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


def test_resident_frame_exclusion_matches_id_name_or_stem():
    frame = {
        "id": "F000196",
        "path": r"C:\data\LIGHT_H_0136.fits",
    }

    assert _matches_any_token(frame, {"F000196"})
    assert _matches_any_token(frame, {"LIGHT_H_0136.fits"})
    assert _matches_any_token(frame, {"LIGHT_H_0136"})
    assert not _matches_any_token(frame, {"LIGHT_H_0137"})
