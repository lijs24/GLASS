from __future__ import annotations

import json
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.acceptance_audit import build_acceptance_audit


def _write_manifest(path: Path, *, light: int = 200, bias: int = 20, dark: int = 20, flat: int = 20) -> None:
    frames = []
    for frame_type, count in {"light": light, "bias": bias, "dark": dark, "flat": flat}.items():
        frames.extend({"id": f"{frame_type}_{idx}", "frame_type": frame_type} for idx in range(count))
    write_json(path, {"frames": frames, "summary": {"count": len(frames)}})


def _write_glass_run(
    path: Path,
    *,
    elapsed_s: float = 100.0,
    active: int = 193,
    zero: int = 7,
    command: str | None = None,
) -> None:
    path.mkdir()
    write_json(path / "run_timing.json", {"total_elapsed_s": elapsed_s, "memory_mode": "resident"})
    if command is not None:
        (path / "run_command.txt").write_text(command, encoding="utf-8")
    weights = {f"L{idx:04d}": 1.0 for idx in range(active)}
    weights.update({f"Z{idx:04d}": 0.0 for idx in range(zero)})
    write_json(
        path / "integration_results.json",
        {
            "frame_weights": weights,
            "weighting": "none",
            "rejection": "winsorized_sigma",
            "outputs": [
                {
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "frame_count": active + zero,
                    "master_path": "master.fits",
                }
            ],
        },
    )


def _write_wbpp_result(path: Path, *, elapsed_s: float = 1000.0) -> None:
    path.write_text(
        "\ufeff" + json.dumps({"elapsed_s": elapsed_s, "dataset": "fixture"}),
        encoding="utf-8",
    )


def _write_compare(
    path: Path,
    *,
    shape_match: bool = True,
    rms: float = 0.001,
    p99: float = 0.002,
    scale: float = 8.764434957115609e-06,
    offset: float = 0.0006274500691899127,
    min_coverage: float = 190.0,
    coverage_fraction: float = 0.97,
) -> None:
    write_json(
        path,
        {
            "shape_match": shape_match,
            "rms_diff": rms,
            "abs_diff_p99": p99,
            "candidate_transform": {
                "applied": True,
                "scale": scale,
                "offset": offset,
                "clip_low": None,
                "clip_high": None,
            },
            "comparison_region": {
                "coverage_fraction": coverage_fraction,
                "compared_pixels": 123,
                "min_coverage": min_coverage,
            },
        },
    )


def _write_contract(path: Path, *, max_runtime_factor: float = 1.3) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "name": "fixture_contract",
            "dataset_requirements": {
                "light": 200,
                "bias": 20,
                "dark": 20,
                "flat": 20,
                "active_light_frames": 190,
            },
            "runtime": {
                "release_baseline_elapsed_s": 30.0,
                "max_runtime_regression_factor": max_runtime_factor,
                "min_speedup_vs_reference": 20.0,
            },
            "comparison": {
                "required_scale": 8.764434957115609e-06,
                "required_offset": 0.0006274500691899127,
                "required_min_coverage": 190.0,
                "min_coverage_fraction": 0.95,
                "max_rms_diff": 0.01,
                "max_abs_diff_p99": 0.01,
            },
            "required_command_tokens": [
                "--memory-mode resident",
                "--resident-registration similarity_cuda_triangle",
                "--flat-floor 0.05",
            ],
        },
    )


def test_acceptance_audit_passes_real_benchmark_thresholds(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    _write_manifest(manifest)
    _write_glass_run(gp_run)
    _write_wbpp_result(wbpp)
    _write_compare(compare)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
    )

    assert audit["passed"] is True
    assert audit["frame_type_counts"] == {"light": 200, "bias": 20, "dark": 20, "flat": 20}
    assert audit["speedup_summary"]["speedup_vs_wbpp"] == 10.0


def test_acceptance_audit_applies_benchmark_contract(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=38.0,
        command=(
            "glass run --memory-mode resident --resident-registration similarity_cuda_triangle "
            "--flat-floor 0.05"
        ),
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare)
    _write_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is True
    assert audit["benchmark_contract"]["name"] == "fixture_contract"
    assert checks["contract_max_runtime_vs_release_baseline"] is True
    assert checks["contract_required_command_token:--flat-floor 0.05"] is True
    assert checks["contract_compare_scale"] is True
    assert checks["contract_compare_min_coverage"] is True


def test_acceptance_audit_contract_catches_missing_parameters(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    contract = tmp_path / "contract.json"
    _write_manifest(manifest)
    _write_glass_run(
        gp_run,
        elapsed_s=42.0,
        command="glass run --memory-mode resident --resident-registration similarity_cuda_triangle",
    )
    _write_wbpp_result(wbpp, elapsed_s=1092.541)
    _write_compare(compare, scale=1.0, min_coverage=99.0, coverage_fraction=0.5)
    _write_contract(contract)

    audit = build_acceptance_audit(
        manifest_path=manifest,
        glass_run=gp_run,
        wbpp_result=wbpp,
        compare_json=compare,
        min_active_frames=190,
        min_speedup=2.0,
        benchmark_contract=contract,
    )

    checks = {item["name"]: item["passed"] for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["contract_max_runtime_vs_release_baseline"] is False
    assert checks["contract_required_command_token:--flat-floor 0.05"] is False
    assert checks["contract_compare_scale"] is False
    assert checks["contract_compare_min_coverage"] is False
    assert checks["contract_min_coverage_fraction"] is False


def test_acceptance_audit_cli_writes_outputs_and_returns_failure(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    gp_run = tmp_path / "gp"
    wbpp = tmp_path / "wbpp.json"
    compare = tmp_path / "compare.json"
    out_json = tmp_path / "audit.json"
    out_md = tmp_path / "audit.md"
    _write_manifest(manifest, light=199)
    _write_glass_run(gp_run, elapsed_s=100.0)
    _write_wbpp_result(wbpp, elapsed_s=150.0)
    _write_compare(compare, rms=0.02)

    result = main(
        [
            "acceptance-audit",
            "--manifest",
            str(manifest),
            "--glass-run",
            str(gp_run),
            "--wbpp-result",
            str(wbpp),
            "--compare-json",
            str(compare),
            "--out",
            str(out_json),
            "--markdown",
            str(out_md),
            "--min-active-frames",
            "190",
        ]
    )

    assert result == 2
    payload = read_json(out_json)
    assert payload["passed"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["minimum_light_frames"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["minimum_speedup"] is False
    assert {item["name"]: item["passed"] for item in payload["checks"]}["maximum_rms_diff"] is False
    assert "FAIL: minimum_light_frames" in out_md.read_text(encoding="utf-8")
