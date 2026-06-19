from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.report.resident_rejection_sample_audit import build_resident_rejection_sample_audit


def _dq_from_rejection(low: np.ndarray, high: np.ndarray) -> np.ndarray:
    dq = np.zeros(low.shape, dtype=np.float32)
    dq[low > 0] += float(int(DQFlag.LOW_REJECTED))
    dq[high > 0] += float(int(DQFlag.HIGH_REJECTED))
    return dq


def _write_map_set(
    run: Path,
    *,
    prefix: str,
    coverage: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    backend: str,
) -> None:
    integration = run / "integration"
    integration.mkdir(parents=True)
    coverage_path = integration / f"{prefix}_coverage.fits"
    low_path = integration / f"{prefix}_low.fits"
    high_path = integration / f"{prefix}_high.fits"
    dq_path = integration / f"{prefix}_dq.fits"
    write_fits_data(coverage_path, coverage, dtype=np.float32)
    write_fits_data(low_path, low, dtype=np.float32)
    write_fits_data(high_path, high, dtype=np.float32)
    write_fits_data(dq_path, _dq_from_rejection(low, high), dtype=np.float32)
    write_json(
        run / "integration_results.json",
        {
            "outputs": [
                {
                    "backend": backend,
                    "filter": "H",
                    "frame_count": 4,
                    "coverage_map_path": str(coverage_path),
                    "low_rejection_map_path": str(low_path),
                    "high_rejection_map_path": str(high_path),
                    "dq_map_path": str(dq_path),
                }
            ]
        },
    )


def _write_compare_json(path: Path, *, border: int = 1) -> None:
    write_json(
        path,
        {
            "shape_match": True,
            "comparison_region": {
                "ignore_border_px": border,
                "min_coverage": 1.0,
                "full_shape": [4, 4],
                "compared_shape": [4 - 2 * border, 4 - 2 * border],
            },
        },
    )


def test_audit_identifies_pre_rejection_coverage_drift(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    base = np.full((4, 4), 3.0, dtype=np.float32)
    zeros = np.zeros((4, 4), dtype=np.float32)
    resident_low = zeros.copy()
    resident_low[1, 1] = 1.0

    _write_map_set(cpu, prefix="cpu", coverage=base, low=zeros, high=zeros, backend="cpu")
    _write_map_set(
        resident,
        prefix="resident",
        coverage=base,
        low=resident_low,
        high=zeros,
        backend="cuda_resident_stack",
    )
    _write_compare_json(compare)

    payload = build_resident_rejection_sample_audit(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
        tile_size=2,
        max_rejected_sample_delta=0,
    )

    assert payload["status"] == "attention_required"
    assert payload["recommendation"] == "fix_resident_geometric_coverage_or_transform"
    assert payload["deltas"]["rejected_sample_delta"] == 1
    assert payload["deltas"]["pre_rejection_sample_delta"] == 1
    assert payload["deltas"]["same_post_coverage_abs_rejected_sample_delta"] == 1
    assert payload["region_deltas"]["inside_compare_region"]["rejected_sample_delta"] == 1
    assert payload["top_tiles"][0]["rejected_sample_delta"] == 1


def test_audit_can_evaluate_declared_compare_region(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    base = np.full((4, 4), 3.0, dtype=np.float32)
    zeros = np.zeros((4, 4), dtype=np.float32)
    resident_coverage = base.copy()
    resident_coverage[0, :] = 2.0

    _write_map_set(cpu, prefix="cpu", coverage=base, low=zeros, high=zeros, backend="cpu")
    _write_map_set(
        resident,
        prefix="resident",
        coverage=resident_coverage,
        low=zeros,
        high=zeros,
        backend="cuda_resident_stack",
    )
    _write_compare_json(compare, border=1)

    full = build_resident_rejection_sample_audit(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
        tile_size=2,
    )
    cropped = build_resident_rejection_sample_audit(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
        tile_size=2,
        evaluation_region="compare_region",
    )

    assert full["status"] == "attention_required"
    assert full["evaluation_region"] == "full_frame"
    assert full["deltas"]["pre_rejection_sample_delta"] == -4
    assert full["deltas"]["abs_pre_rejection_sample_delta"] == 4
    assert cropped["status"] == "passed"
    assert cropped["evaluation_region"] == "compare_region"
    assert cropped["evaluation_deltas"]["pre_rejection_sample_delta"] == 0
    assert cropped["evaluation_deltas"]["abs_pre_rejection_sample_delta"] == 0
    assert cropped["deltas"]["abs_pre_rejection_sample_delta"] == 4
    assert cropped["recommendation"] == "rejection_sample_accounting_ready"


def test_audit_identifies_same_pre_rejection_semantic_delta(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    base = np.full((4, 4), 3.0, dtype=np.float32)
    zeros = np.zeros((4, 4), dtype=np.float32)
    resident_coverage = base.copy()
    resident_coverage[2, 2] = 2.0
    resident_low = zeros.copy()
    resident_low[2, 2] = 1.0

    _write_map_set(cpu, prefix="cpu", coverage=base, low=zeros, high=zeros, backend="cpu")
    _write_map_set(
        resident,
        prefix="resident",
        coverage=resident_coverage,
        low=resident_low,
        high=zeros,
        backend="cuda_resident_stack",
    )

    payload = build_resident_rejection_sample_audit(
        cpu_run=cpu,
        resident_run=resident,
        tile_size=2,
        max_rejected_sample_delta=0,
        max_same_pre_rejection_abs_delta=0,
    )

    assert payload["recommendation"] == "fix_resident_winsorized_rejection_semantics"
    assert payload["deltas"]["pre_rejection_sample_delta"] == 0
    assert payload["deltas"]["same_pre_rejection_abs_rejected_sample_delta"] == 1
    assert payload["failed_checks"] == [
        "rejected_sample_delta_within_limit",
        "same_pre_rejection_semantic_delta_within_limit",
    ]


def test_resident_rejection_sample_audit_cli_writes_outputs(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"
    base = np.full((4, 4), 3.0, dtype=np.float32)
    zeros = np.zeros((4, 4), dtype=np.float32)
    resident_high = zeros.copy()
    resident_high[0, 0] = 1.0

    _write_map_set(cpu, prefix="cpu", coverage=base, low=zeros, high=zeros, backend="cpu")
    _write_map_set(
        resident,
        prefix="resident",
        coverage=base,
        low=zeros,
        high=resident_high,
        backend="cuda_resident_stack",
    )
    _write_compare_json(compare)

    result = main(
        [
            "resident-rejection-sample-audit",
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
            "--tile-size",
            "2",
            "--evaluation-region",
            "compare_region",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "resident_rejection_sample_audit"
    assert payload["evaluation_region"] == "compare_region"
    assert payload["deltas"]["high_rejected_sample_delta"] == 1
    assert "Resident Rejection Sample Audit" in markdown.read_text(encoding="utf-8")
