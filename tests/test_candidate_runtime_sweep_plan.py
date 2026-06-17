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
    assert "guardrails" in payload["variants"][1]["commands"]
    assert "resident_calibration_contract" not in payload["variants"][1]["commands"]
    assert "resident_result_contract" not in payload["variants"][1]["commands"]
    assert "pipeline_contract" not in payload["variants"][1]["commands"]
    assert "stack_engine_contract" not in payload["variants"][1]["commands"]
    assert "guardrails" in payload["variants"][1]["commands"]["guardrails"]
    assert "--resident-result-contract-json" not in payload["variants"][1]["commands"]["guardrails"]
    assert "--contract-bundle" in payload["variants"][1]["commands"]["acceptance_audit"]
    assert "--pipeline-contract-json" not in payload["variants"][1]["commands"]["acceptance_audit"]
    assert "--stack-engine-contract-json" not in payload["variants"][1]["commands"]["acceptance_audit"]
    assert payload["variants"][1]["artifacts"]["resident_calibration_artifacts_json"].endswith(
        str(Path("runs") / "prefetch12_workers6" / "calibration_artifacts.json")
    )
    assert payload["variants"][1]["artifacts"]["resident_result_contract_json"].endswith(
        str(Path("runs") / "prefetch12_workers6" / "resident_result_contract.json")
    )
    assert payload["variants"][1]["artifacts"]["resident_result_contract_source"] == "run_default"
    assert payload["variants"][1]["artifacts"]["acceptance_contract_bundle_json"].endswith(
        str(Path("guardrails") / "prefetch12_workers6" / "acceptance_contract_bundle.json")
    )
    assert payload["variants"][1]["artifacts"]["pipeline_contract_json"].endswith(
        str(Path("guardrails") / "prefetch12_workers6" / "pipeline_contract.json")
    )
    assert payload["variants"][1]["artifacts"]["stack_engine_contract_json"].endswith(
        str(Path("guardrails") / "prefetch12_workers6" / "stack_engine_contract.json")
    )
    assert "--fail-on-failed" not in payload["variants"][1]["commands"]["candidate_comparison"]
    assert "candidate-comparison-sweep" in payload["sweep_command"]


def test_candidate_runtime_sweep_plan_generates_prefetch_matrix(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.json"
    command = tmp_path / "run_command.txt"
    baseline = tmp_path / "baseline"
    _write_source_comparison(comparison)
    _write_command(command)
    _write_baseline_run(baseline)

    payload = build_candidate_runtime_sweep_plan(
        comparison,
        root=tmp_path / "matrix",
        base_run_command=command,
        baseline_run=baseline,
        baseline_compare_json=tmp_path / "baseline_compare.json",
        reference=tmp_path / "reference.xisf",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        prefetch_frames=[10, 12],
        prefetch_workers=[5, 6],
    )

    assert payload["variant_count"] == 4
    assert [row["variant_id"] for row in payload["variants"]] == [
        "prefetch10_workers5",
        "prefetch10_workers6",
        "prefetch12_workers5",
        "prefetch12_workers6",
    ]
    last_command = payload["variants"][-1]["commands"]["run"]
    assert "--resident-prefetch-frames 12" in last_command
    assert "--resident-prefetch-workers 6" in last_command


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
                "--prefetch-frame",
                "10",
                "--prefetch-worker",
                "5",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["variant_count"] == 2
    assert payload["variants"][1]["variant_id"] == "prefetch10_workers5"
    assert "Candidate Runtime Sweep Plan" in markdown.read_text(encoding="utf-8")
