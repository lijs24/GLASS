from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from glass.cli import main
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.resident_warp_input_audit import build_resident_warp_input_audit


def _cuda_or_skip() -> None:
    import glass_cuda

    if not glass_cuda.cuda_available():
        pytest.skip("CUDA native backend is not available")


def _write_compare(path: Path, shape: tuple[int, int]) -> None:
    height, width = shape
    write_json(
        path,
        {
            "shape_match": True,
            "comparison_region": {
                "ignore_border_px": 0,
                "full_shape": [height, width],
                "compared_shape": [height, width],
            },
        },
    )


def _write_runs(tmp_path: Path, *, resident_matrix: list[list[float]]) -> tuple[Path, Path, Path]:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    frame_id = "F000001"
    frame = np.arange(36, dtype=np.float32).reshape(6, 6)
    coverage = np.ones_like(frame, dtype=np.float32)
    for root in (cpu, resident):
        root.mkdir(parents=True)
    for sub in ("calib_cache/calibrated", "registered_cache", "coverage_cache"):
        (cpu / sub).mkdir(parents=True)
    calibrated_path = cpu / "calib_cache" / "calibrated" / f"calibrated_{frame_id}.fits"
    registered_path = cpu / "registered_cache" / f"registered_{frame_id}.fits"
    coverage_path = cpu / "coverage_cache" / f"coverage_{frame_id}.fits"
    write_fits_data(calibrated_path, frame, dtype=np.float32)
    write_fits_data(registered_path, frame, dtype=np.float32)
    write_fits_data(coverage_path, coverage, dtype=np.float32)
    write_json(
        cpu / "calibration_artifacts.json",
        {
            "calibrated_lights": [
                {
                    "frame_id": frame_id,
                    "path": str(calibrated_path),
                }
            ]
        },
    )
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    write_json(
        cpu / "registration_results.json",
        {
            "registration_results": [
                {
                    "frame_id": frame_id,
                    "reference_frame_id": frame_id,
                    "status": "reference",
                    "matrix": identity,
                }
            ]
        },
    )
    write_json(
        resident / "registration_results.json",
        {
            "results": [
                {
                    "frame_id": frame_id,
                    "reference_frame_id": frame_id,
                    "status": "ok",
                    "matrix": resident_matrix,
                }
            ]
        },
    )
    compare = tmp_path / "compare.json"
    _write_compare(compare, frame.shape)
    return cpu, resident, compare


def test_resident_warp_input_audit_attributes_resident_matrix_delta(tmp_path: Path) -> None:
    _cuda_or_skip()
    cpu, resident, compare = _write_runs(
        tmp_path,
        resident_matrix=[[1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )

    payload = build_resident_warp_input_audit(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
        max_frames=1,
        cpu_matrix_rms_tolerance=1.0e-6,
        resident_matrix_rms_tolerance=1.0e-6,
    )

    assert payload["artifact_type"] == "resident_warp_input_audit"
    assert payload["status"] == "passed"
    assert payload["recommendation"] == "target_resident_registration_matrix_precision"
    assert payload["summary"]["resident_matrix_warp_parity_passed"] is False
    frame = payload["frames"][0]
    assert frame["cpu_matrix"]["value_delta"]["max_abs"] == 0.0
    assert frame["resident_matrix"]["value_delta"]["rms"] > 0.0
    assert frame["matrix_delta"]["translation_delta_px"] == 1.0


def test_resident_warp_input_audit_cli_writes_outputs(tmp_path: Path) -> None:
    _cuda_or_skip()
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    cpu, resident, compare = _write_runs(tmp_path, resident_matrix=identity)
    out = tmp_path / "warp_input_audit.json"
    markdown = tmp_path / "warp_input_audit.md"

    result = main(
        [
            "resident-warp-input-audit",
            "--cpu-run",
            str(cpu),
            "--resident-run",
            str(resident),
            "--compare-json",
            str(compare),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--max-frames",
            "1",
            "--cpu-matrix-rms-tolerance",
            "1e-6",
            "--resident-matrix-rms-tolerance",
            "1e-6",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "passed"
    assert payload["recommendation"] == "resident_warp_input_parity_ready"
    assert "Resident Warp Input Audit" in markdown.read_text(encoding="utf-8")
