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


def _write_glass_run(path: Path, *, elapsed_s: float = 100.0, active: int = 193, zero: int = 7) -> None:
    path.mkdir()
    write_json(path / "run_timing.json", {"total_elapsed_s": elapsed_s, "memory_mode": "resident"})
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


def _write_compare(path: Path, *, shape_match: bool = True, rms: float = 0.001, p99: float = 0.002) -> None:
    write_json(
        path,
        {
            "shape_match": shape_match,
            "rms_diff": rms,
            "abs_diff_p99": p99,
            "comparison_region": {"coverage_fraction": 0.97, "compared_pixels": 123},
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
