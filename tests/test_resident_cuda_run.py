from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from gpwbpp.cli import main
from gpwbpp.io.json_io import read_json
from gpwbpp.engine.resident_cuda import _matches_any_token
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


def test_cli_resident_cuda_run_ncc_subpixel_registration_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_ncc"

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
            "on",
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
    assert integration["outputs"][0]["resident_local_normalization"] == "resident_global_mean_std"
    assert registration["transform_model"] == "translation_ncc_subpixel"
    assert local_norm["source_stage"] == "resident_calibrated_stack"
    assert local_norm["enabled"] is True
    assert local_norm["mode"] == "resident_global_mean_std"
    assert local_norm["groups"][0]["frame_results"][0]["status"] == "reference"
    assert registration["results"][0]["status"] == "reference"
    assert resident_registration["mode"] == "translation_ncc_subpixel"
    assert resident["artifacts"][0]["resident_local_normalization"]["enabled"] is True
    assert resident["artifacts"][0]["resident_local_normalization"]["mode"] == "resident_global_mean_std"
    assert resident_registration["max_shift"] == 4
    assert resident_registration["ncc_sample_stride"] == 2
    assert resident_registration["subpixel_radius_steps"] == 2
    assert resident_registration["subpixel_step"] == 0.5


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


def test_resident_frame_exclusion_matches_id_name_or_stem():
    frame = {
        "id": "F000196",
        "path": r"C:\data\LIGHT_H_0136.fits",
    }

    assert _matches_any_token(frame, {"F000196"})
    assert _matches_any_token(frame, {"LIGHT_H_0136.fits"})
    assert _matches_any_token(frame, {"LIGHT_H_0136"})
    assert not _matches_any_token(frame, {"LIGHT_H_0137"})
