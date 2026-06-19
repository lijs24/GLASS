from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_parity_summary import build_resident_parity_summary


def _write_run(
    path: Path,
    *,
    backend: str,
    memory_mode: str,
    elapsed_s: float,
    reference_frame_id: str = "F000016",
    frame_count: int = 16,
    rejected_samples: int = 14796,
    valid_pixels: int = 248399,
    contract_passed: bool = True,
) -> None:
    path.mkdir()
    write_json(
        path / "run_timing.json",
        {
            "backend": backend,
            "memory_mode": memory_mode,
            "total_elapsed_s": elapsed_s,
            "stages": [{"stage": "integration", "elapsed_s": elapsed_s / 2.0}],
        },
    )
    rows = [
        {
            "frame_id": f"F{index:06d}",
            "reference_frame_id": reference_frame_id,
            "status": "reference" if index == 16 else "ok",
            "transform_model": "translation",
            "matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        }
        for index in range(1, frame_count + 1)
    ]
    write_json(
        path / "registration_results.json",
        {
            "reference_frame_id": reference_frame_id,
            "registration_results": rows,
        },
    )
    write_json(
        path / "integration_results.json",
        {
            "outputs": [
                {
                    "backend": backend,
                    "frame_count": frame_count,
                    "master_path": str(path / "master_H.fits"),
                    "coverage_map_path": str(path / "coverage_H.fits"),
                    "dq_map_path": str(path / "dq_H.fits"),
                    "low_rejection_map_path": str(path / "low_H.fits"),
                    "high_rejection_map_path": str(path / "high_H.fits"),
                    "dq_provenance_summary": {
                        "valid_pixels": valid_pixels,
                        "rejected_samples": rejected_samples,
                        "low_rejected_pixels": rejected_samples // 2,
                        "high_rejected_pixels": rejected_samples - rejected_samples // 2,
                        "sample_accounting_closure": {"status": "passed"},
                    },
                    "integration_rejection": {
                        "mode": "winsorized_sigma",
                        "cpu_baseline_parity": True,
                    },
                }
            ]
        },
    )
    write_json(
        path / "resident_result_contract.json",
        {
            "status": "passed" if contract_passed else "failed",
            "passed": contract_passed,
            "checks": [
                {"name": "resident_outputs_present", "passed": True},
                {"name": "resident_outputs_pass_contract", "passed": contract_passed},
            ],
        },
    )


def _write_compare(path: Path, *, rms: float = 0.05, relative_rms: float = 0.0002) -> None:
    write_json(
        path,
        {
            "shape_match": True,
            "rms_diff": rms,
            "relative_rms_diff": relative_rms,
            "abs_diff_p90": 0.03,
            "abs_diff_p99": 0.09,
            "max_abs_diff": 0.2,
        },
    )


def test_resident_parity_summary_separates_parity_from_contract(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    _write_run(cpu, backend="cpu", memory_mode="tile", elapsed_s=40.0)
    _write_run(
        resident,
        backend="cuda_resident_stack",
        memory_mode="resident",
        elapsed_s=0.3,
        rejected_samples=14777,
        contract_passed=False,
    )
    _write_compare(compare)

    payload = build_resident_parity_summary(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["parity_passed"] is True
    assert payload["passed"] is False
    assert payload["recommendation"] == "fix_resident_result_contract"
    assert checks["compare_rms_within_limit"] is True
    assert checks["rejected_sample_delta_within_limit"] is True
    assert checks["resident_result_contract_passed"] is False
    assert payload["deltas"]["rejected_sample_delta"] == -19


def test_resident_parity_summary_blocks_reference_mismatch(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    _write_run(cpu, backend="cpu", memory_mode="tile", elapsed_s=40.0)
    _write_run(
        resident,
        backend="cuda_resident_stack",
        memory_mode="resident",
        elapsed_s=95.0,
        reference_frame_id="F000013",
    )
    _write_compare(compare, rms=41.0, relative_rms=0.18)

    payload = build_resident_parity_summary(
        cpu_run=cpu,
        resident_run=resident,
        compare_json=compare,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["parity_passed"] is False
    assert checks["registration_reference_match"] is False
    assert checks["compare_rms_within_limit"] is False
    assert payload["recommendation"] == "fix_resident_registration_or_dq_parity"


def test_resident_parity_summary_cli_writes_outputs(tmp_path: Path) -> None:
    cpu = tmp_path / "cpu"
    resident = tmp_path / "resident"
    compare = tmp_path / "compare.json"
    out = tmp_path / "parity.json"
    markdown = tmp_path / "parity.md"
    _write_run(cpu, backend="cpu", memory_mode="tile", elapsed_s=40.0)
    _write_run(
        resident,
        backend="cuda_resident_stack",
        memory_mode="resident",
        elapsed_s=0.3,
        rejected_samples=14777,
        contract_passed=False,
    )
    _write_compare(compare)

    result = main(
        [
            "resident-parity-summary",
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
            "--ignore-resident-contract",
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["artifact_type"] == "resident_parity_summary"
    assert payload["passed"] is True
    assert payload["parity_passed"] is True
    assert "Resident Parity Summary" in markdown.read_text(encoding="utf-8")
