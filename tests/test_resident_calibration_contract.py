from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_calibration_contract import build_resident_calibration_contract


def _write_resident_calibration_run(run: Path) -> None:
    run.mkdir(parents=True)
    integration_dir = run / "integration"
    integration_dir.mkdir()
    master_path = integration_dir / "resident_master_H.fits"
    master_path.write_bytes(b"fixture")
    cache_dir = run / "calib_cache" / "resident_masters"
    cache_dir.mkdir(parents=True)
    cache_key = "H_24x24_bias-B_dark-D_flat-F_abc123"
    for suffix in ["master_bias.npy", "master_dark.npy", "master_flat.npy", "master_stats.json"]:
        (cache_dir / f"{cache_key}_{suffix}").write_bytes(b"fixture")
    stats = {"min": 1.0, "max": 2.0, "mean": 1.5, "median": 1.5, "std": 0.1}
    write_json(
        run / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["F1", "F2"],
                    "master_path": str(master_path),
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
                                "bias_count": 2,
                                "dark_count": 2,
                                "flat_count": 2,
                                "bias": stats,
                                "dark": stats,
                                "flat": stats,
                                "shape": {"height": 24, "width": 24},
                                "cache_dir": str(cache_dir),
                                "cache_key": cache_key,
                                "cache_scope": "run",
                                "cache_hit": True,
                                "master_dark_includes_bias": True,
                            }
                        },
                    },
                    "timing_s": {
                        "master_build_or_load": 0.01,
                        "light_calibrate_store": 0.02,
                        "light_calibration_batch_native_total": 0.03,
                        "resident_allocate_and_master_upload": 0.04,
                    },
                }
            ]
        },
    )


def test_resident_calibration_contract_passes_for_resident_artifacts(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_resident_calibration_run(run)

    payload = build_resident_calibration_contract(run)

    assert payload["passed"] is True
    assert payload["artifact_type"] == "resident_cuda_calibration_contract"
    assert payload["output_count"] == 1
    assert payload["outputs"][0]["set_count"] == 1
    assert payload["outputs"][0]["bias_count"] == 2
    assert all(item["passed"] for item in payload["outputs"][0]["checks"])


def test_resident_calibration_contract_cli_writes_markdown(tmp_path: Path) -> None:
    run = tmp_path / "run"
    out = tmp_path / "resident_calibration_contract.json"
    markdown = tmp_path / "resident_calibration_contract.md"
    _write_resident_calibration_run(run)

    assert (
        main(
            [
                "resident-calibration-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-failed",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["passed"] is True
    assert "Resident CUDA Calibration Contract" in markdown.read_text(encoding="utf-8")
