from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from glass.cli import main
from glass.cpu.integration import weighted_integrate_stack
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.resident_rejection_input_audit import build_resident_rejection_input_audit


def _dq_from_rejection(low: np.ndarray, high: np.ndarray) -> np.ndarray:
    dq = np.zeros(low.shape, dtype=np.float32)
    dq[low > 0] += float(int(DQFlag.LOW_REJECTED))
    dq[high > 0] += float(int(DQFlag.HIGH_REJECTED))
    return dq


def _write_compare_json(path: Path, shape: tuple[int, int]) -> None:
    height, width = shape
    write_json(
        path,
        {
            "shape_match": True,
            "comparison_region": {
                "ignore_border_px": 0,
                "min_coverage": 1.0,
                "full_shape": [height, width],
                "compared_shape": [height, width],
            },
        },
    )


def _write_run(
    root: Path,
    *,
    frames: list[np.ndarray],
    coverage: list[np.ndarray],
    low_sigma: float = 3.0,
    high_sigma: float = 3.0,
    backend: str = "cpu",
    output_overrides: dict[str, np.ndarray] | None = None,
) -> dict[str, np.ndarray]:
    frame_ids = [f"F{i:06d}" for i in range(1, len(frames) + 1)]
    registered_dir = root / "registered_cache"
    coverage_dir = root / "coverage_cache"
    integration_dir = root / "integration"
    registered_dir.mkdir(parents=True)
    coverage_dir.mkdir(parents=True)
    integration_dir.mkdir(parents=True)
    for frame_id, frame, cov in zip(frame_ids, frames, coverage, strict=True):
        write_fits_data(registered_dir / f"registered_{frame_id}.fits", frame, dtype=np.float32)
        write_fits_data(coverage_dir / f"coverage_{frame_id}.fits", cov, dtype=np.float32)
    stack = np.stack(frames, axis=0).astype(np.float32)
    coverage_stack = np.stack(coverage, axis=0).astype(np.float32)
    master, weight, coverage_map, low, high = weighted_integrate_stack(
        stack,
        coverage=coverage_stack,
        rejection="winsorized_sigma",
        low_sigma=low_sigma,
        high_sigma=high_sigma,
    )
    maps = {
        "master": master,
        "weight": weight,
        "coverage": coverage_map,
        "low_rejection": low,
        "high_rejection": high,
    }
    if output_overrides:
        maps.update(output_overrides)
    paths = {
        "master": integration_dir / "master_H.fits",
        "coverage": integration_dir / "coverage_map_H.fits",
        "low_rejection": integration_dir / "low_rejection_H.fits",
        "high_rejection": integration_dir / "high_rejection_H.fits",
        "dq": integration_dir / "dq_map_H.fits",
    }
    write_fits_data(paths["master"], maps["master"], dtype=np.float32)
    write_fits_data(paths["coverage"], maps["coverage"], dtype=np.float32)
    write_fits_data(paths["low_rejection"], maps["low_rejection"], dtype=np.float32)
    write_fits_data(paths["high_rejection"], maps["high_rejection"], dtype=np.float32)
    write_fits_data(
        paths["dq"],
        _dq_from_rejection(maps["low_rejection"], maps["high_rejection"]),
        dtype=np.float32,
    )
    write_json(
        root / "integration_results.json",
        {
            "low_sigma": low_sigma,
            "high_sigma": high_sigma,
            "frame_weights": {frame_id: 1.0 for frame_id in frame_ids},
            "outputs": [
                {
                    "backend": backend,
                    "filter": "H",
                    "frame_count": len(frames),
                    "master_path": str(paths["master"]),
                    "coverage_map_path": str(paths["coverage"]),
                    "low_rejection_map_path": str(paths["low_rejection"]),
                    "high_rejection_map_path": str(paths["high_rejection"]),
                    "dq_map_path": str(paths["dq"]),
                }
            ],
        },
    )
    return maps


def _frames() -> tuple[list[np.ndarray], list[np.ndarray]]:
    frames = [
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        np.array([[12.0, 2.0], [3.0, 4.0]], dtype=np.float32),
    ]
    coverage = [np.ones((2, 2), dtype=np.float32) for _ in frames]
    return frames, coverage


def test_resident_rejection_input_audit_attributes_same_pre_delta(tmp_path: Path) -> None:
    frames, coverage = _frames()
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    cpu_maps = _write_run(cpu, frames=frames, coverage=coverage)
    resident_coverage = cpu_maps["coverage"].copy()
    resident_high = cpu_maps["high_rejection"].copy()
    resident_coverage[1, 1] -= 1.0
    resident_high[1, 1] += 1.0
    _write_run(
        resident,
        frames=frames,
        coverage=coverage,
        backend="cuda_resident_stack",
        output_overrides={"coverage": resident_coverage, "high_rejection": resident_high},
    )
    _write_compare_json(compare, (2, 2))

    payload = build_resident_rejection_input_audit(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
        run_cuda_exact_input=False,
        max_same_pre_rejection_abs_delta=0,
    )

    assert payload["artifact_type"] == "resident_rejection_input_audit"
    assert payload["status"] == "attention_required"
    assert payload["cpu_replay"]["delta_vs_cpu_output"]["passed"] is True
    assert payload["cuda_exact_input"]["status"] == "skipped_by_request"
    assert payload["resident_rejection_sample_audit"]["evaluation_deltas"][
        "same_pre_rejection_abs_rejected_sample_delta"
    ] == 1


def test_resident_rejection_input_audit_cli_writes_outputs(tmp_path: Path) -> None:
    frames, coverage = _frames()
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    out = tmp_path / "input_audit.json"
    markdown = tmp_path / "input_audit.md"
    _write_run(cpu, frames=frames, coverage=coverage)
    _write_run(resident, frames=frames, coverage=coverage, backend="cuda_resident_stack")
    _write_compare_json(compare, (2, 2))

    result = main(
        [
            "resident-rejection-input-audit",
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
            "--skip-cuda-exact-input",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "resident_rejection_input_audit"
    assert payload["cpu_replay"]["delta_vs_cpu_output"]["passed"] is True
    assert "Resident Rejection Input Audit" in markdown.read_text(encoding="utf-8")


def test_resident_rejection_input_audit_cuda_exact_input_matches_cpu(tmp_path: Path) -> None:
    import glass_cuda

    if not glass_cuda.cuda_available():
        pytest.skip("CUDA native backend is not available")
    frames, coverage = _frames()
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    _write_run(cpu, frames=frames, coverage=coverage)
    _write_run(resident, frames=frames, coverage=coverage, backend="cuda_resident_stack")
    _write_compare_json(compare, (2, 2))

    payload = build_resident_rejection_input_audit(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
        run_cuda_exact_input=True,
    )

    assert payload["status"] == "passed"
    assert payload["cuda_exact_input"]["status"] == "completed"
    assert payload["cuda_exact_input"]["delta_vs_cpu_output"]["passed"] is True
    assert payload["recommendation"] == "resident_rejection_input_semantics_ready"
