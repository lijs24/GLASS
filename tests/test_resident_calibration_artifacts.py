from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.resident_calibration_artifacts import (
    build_resident_calibration_artifacts,
    write_resident_calibration_artifacts,
)
from glass.io.fits_io import read_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.stack_engine_contract import build_stack_engine_contract_audit


def _write_resident_run(path: Path) -> None:
    cache_dir = path / "calib_cache" / "resident_masters"
    cache_dir.mkdir(parents=True)
    cache_key = "H_24x24_bias-B_dark-D_flat-F_abc123"
    np.save(cache_dir / f"{cache_key}_master_bias.npy", np.ones((24, 24), dtype=np.float32))
    np.save(cache_dir / f"{cache_key}_master_dark.npy", np.full((24, 24), 2.0, dtype=np.float32))
    np.save(cache_dir / f"{cache_key}_master_flat.npy", np.full((24, 24), 1.0, dtype=np.float32))
    write_json(cache_dir / f"{cache_key}_master_stats.json", {"fixture": True})
    stats = {"min": 1.0, "max": 2.0, "mean": 1.5, "median": 1.5, "std": 0.1}
    write_json(
        path / "resident_artifacts.json",
        {
            "schema_version": 1,
            "backend": "cuda_resident_stack",
            "policy": {
                "flat_floor": 0.05,
                "flat_normalization": "median",
                "master_dark_includes_bias": True,
                "master_rejection": "winsorized_sigma",
            },
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["light_001", "light_002"],
                    "master_path": str(path / "integration" / "resident_master_H.fits"),
                    "master_stats": {
                        "bias_count": 2,
                        "dark_count": 2,
                        "flat_count": 2,
                        "set_count": 1,
                        "calibration_group_policy": "planner_matching_groups_per_light",
                        "sets": {
                            "set-H": {
                                "filter": "H",
                                "bias_group": "B",
                                "dark_group": "D",
                                "flat_group": "F",
                                "flat_bias_group": "B",
                                "bias_count": 2,
                                "dark_count": 2,
                                "flat_count": 2,
                                "dark_exposure_s": 60.0,
                                "master_dark_includes_bias": True,
                                "bias": stats,
                                "dark": stats,
                                "flat": stats,
                                "shape": {"height": 24, "width": 24},
                                "cache_dir": str(cache_dir),
                                "cache_key": cache_key,
                                "cache_scope": "run",
                                "cache_hit": True,
                            }
                        },
                    },
                }
            ],
        },
    )


def test_build_resident_calibration_artifacts_records_masters_and_lights(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    _write_resident_run(run)

    payload = build_resident_calibration_artifacts(run)

    assert payload["artifact_type"] == "resident_cuda_calibration_artifacts"
    assert payload["source_stage"] == "resident_calibrated_stack"
    assert len(payload["masters"]) == 3
    assert len(payload["calibrated_lights"]) == 2
    assert all(item["tile_stack_mode"] == "cuda_resident_stack" for item in payload["masters"].values())
    assert all(item["resident_calibration_contract"]["passed"] for item in payload["masters"].values())
    flat = next(item for item in payload["masters"].values() if item["type"] == "flat")
    assert flat["normalization_stage"] == "per_flat"
    assert flat["flat_floor"] == 0.05
    assert payload["calibrated_lights"][0]["status"] == "resident_in_vram"
    assert payload["calibrated_lights"][0]["resident_stack_index"] == 0


def test_resident_calibration_artifacts_pass_stack_engine_calibration_scope(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    _write_resident_run(run)
    write_resident_calibration_artifacts(run)

    audit = build_stack_engine_contract_audit(
        run,
        scope="calibration",
        expected_integration_engine="cuda_resident_stack",
    )

    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is True
    assert checks["calibration_masters_use_stack_engine"]["passed"] is True
    assert checks["calibration_masters_science_auditable"]["passed"] is True
    assert audit["adoption"]["cuda_resident_surface_count"] == 3
    assert all(item["resident_calibration_contract_passed"] for item in audit["calibration"]["masters"])
    assert read_json(run / "calibration_artifacts.json")["memory_mode"] == "resident"


def test_write_resident_calibration_artifacts_materializes_master_dq_sidecars(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    _write_resident_run(run)

    payload = write_resident_calibration_artifacts(run)

    assert (run / "calib_cache" / "dq").exists()
    for master in payload["masters"].values():
        dq_path = Path(master["dq_mask_path"])
        assert dq_path.exists()
        assert master["dq_summary"] == {"valid": 24 * 24}
        assert master["resident_master_dq_contract"]["passed"] is True
        assert master["stack_engine_dq_provenance"]["output_dq_summary"] == master["dq_summary"]
        assert master["dq_provenance_summary"]["output_dq_summary"] == master["dq_summary"]
        assert master["dq_provenance_summary"]["valid_pixels"] == 24 * 24
        dq_data = read_fits_data(dq_path)
        assert dq_data.shape == (24, 24)
        assert np.count_nonzero(dq_data) == 0


def test_resident_calibration_artifacts_cli_writes_default_artifact(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    _write_resident_run(run)

    assert main(["resident-calibration-artifacts", "--run", str(run)]) == 0

    payload = read_json(run / "calibration_artifacts.json")
    assert payload["artifact_type"] == "resident_cuda_calibration_artifacts"
    assert len(payload["masters"]) == 3
    assert len(payload["calibrated_lights"]) == 2
    assert all(Path(item["dq_mask_path"]).exists() for item in payload["masters"].values())
