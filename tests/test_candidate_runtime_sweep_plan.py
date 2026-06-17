from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.candidate_runtime_sweep_plan import build_candidate_runtime_sweep_plan


def _write_source_comparison(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "candidate_comparison",
            "candidate_id": "agreement_soft_downweight",
            "summary": {
                "status": "passed",
                "passed": True,
                "recommendation": "eligible_but_needs_runtime_sweep",
            },
        },
    )


def _write_baseline_run(path: Path) -> None:
    path.mkdir(parents=True)
    write_json(
        path / "resident_artifacts.json",
        {
            "artifacts": [
                {
                    "master_path": str(path / "integration" / "resident_master_H.fits"),
                    "coverage_map_path": str(path / "integration" / "resident_coverage_map_H.fits"),
                }
            ]
        },
    )


def _write_command(path: Path) -> None:
    path.write_text(
        "glass run --plan plan.json --out old_run --backend cuda --until-stage integration "
        "--memory-mode resident --resident-triangle-agreement-action downweight "
        "--resident-triangle-min-agreement-score 0.6 --resident-prefetch-frames 16 "
        "--resident-prefetch-workers 8 --resident-prefetch-refill-mode queued "
        "--resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 "
        "--resident-calibration-streams 4 --resident-calibration-wave-frames 2 "
        "--resident-calibration-release-mode callback_queue",
        encoding="utf-8",
    )


def test_candidate_runtime_sweep_plan_generates_runtime_only_variants(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.json"
    command = tmp_path / "run_command.txt"
    baseline = tmp_path / "baseline"
    _write_source_comparison(comparison)
    _write_command(command)
    _write_baseline_run(baseline)

    payload = build_candidate_runtime_sweep_plan(
        comparison,
        root=tmp_path / "plan",
        base_run_command=command,
        baseline_run=baseline,
        baseline_compare_json=tmp_path / "baseline_compare.json",
        reference=tmp_path / "reference.xisf",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        benchmark_contract=tmp_path / "contract.json",
        glass_scale=1.25,
        glass_offset=0.5,
        min_coverage=190,
        min_speedup_vs_reference=20,
        variants=["retry_settings_control", "prefetch12_workers6"],
    )

    assert payload["artifact_type"] == "candidate_runtime_sweep_plan"
    assert payload["variant_count"] == 2
    assert payload["variants"][0]["changed_options"] == {}
    assert payload["variants"][1]["changed_options"]["--resident-prefetch-frames"] == 12
    assert "--resident-triangle-min-agreement-score 0.6" in payload["variants"][1]["commands"]["run"]
    assert "--resident-prefetch-frames 12" in payload["variants"][1]["commands"]["run"]
    assert "--fail-on-failed" not in payload["variants"][1]["commands"]["candidate_comparison"]
    assert "candidate-comparison-sweep" in payload["sweep_command"]


def test_cli_candidate_runtime_sweep_plan_writes_outputs(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.json"
    command = tmp_path / "run_command.txt"
    baseline = tmp_path / "baseline"
    out = tmp_path / "runtime_plan.json"
    markdown = tmp_path / "runtime_plan.md"
    _write_source_comparison(comparison)
    _write_command(command)
    _write_baseline_run(baseline)

    assert (
        main(
            [
                "candidate-runtime-sweep-plan",
                "--comparison",
                str(comparison),
                "--root",
                str(tmp_path / "plan"),
                "--base-run-command",
                str(command),
                "--baseline-run",
                str(baseline),
                "--baseline-compare-json",
                str(tmp_path / "baseline_compare.json"),
                "--reference",
                str(tmp_path / "reference.xisf"),
                "--manifest",
                str(tmp_path / "manifest.json"),
                "--wbpp-result",
                str(tmp_path / "wbpp_result.json"),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--variant",
                "retry_settings_control",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["variant_count"] == 1
    assert "Candidate Runtime Sweep Plan" in markdown.read_text(encoding="utf-8")
