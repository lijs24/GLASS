from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.candidate_runtime_sweep_execute import build_candidate_runtime_sweep_execution
from glass.report.candidate_runtime_sweep_execute import _command_tokens


def _commands(name: str) -> dict[str, str]:
    return {
        "run": f"glass run --out runs/{name}",
        "compare_reference": f"glass compare --glass runs/{name}/master.fits --reference ref.xisf --out compare/{name}.html",
        "compare_baseline": f"glass compare --glass runs/{name}/master.fits --reference base.fits --out compare/{name}_base.html",
        "acceptance_audit": f"glass acceptance-audit --glass-run runs/{name} --out acceptance/{name}.json",
        "candidate_comparison": f"glass candidate-comparison --candidate-run runs/{name} --out comparison/{name}.json",
    }


def _write_plan(path: Path, existing_comparison: Path | None = None) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "candidate_runtime_sweep_plan",
            "sweep_command": "glass candidate-comparison-sweep --comparison comparison/a.json --out sweep.json",
            "variants": [
                {
                    "variant_id": "prefetch10_workers5",
                    "artifacts": {
                        "candidate_comparison_json": str(existing_comparison or path.parent / "missing_a.json")
                    },
                    "commands": _commands("a"),
                },
                {
                    "variant_id": "prefetch12_workers6",
                    "artifacts": {"candidate_comparison_json": str(path.parent / "missing_b.json")},
                    "commands": _commands("b"),
                },
            ],
        },
    )


def test_candidate_runtime_sweep_execute_dry_run_records_steps(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    _write_plan(plan)

    payload = build_candidate_runtime_sweep_execution(plan, dry_run=True, variants=["prefetch12_workers6"])

    assert payload["summary"]["status"] == "planned"
    assert payload["selected_variant_count"] == 1
    assert payload["variants"][0]["variant_id"] == "prefetch12_workers6"
    assert [step["status"] for step in payload["variants"][0]["steps"]] == ["planned"] * 5
    assert payload["sweep_summary"]["status"] == "planned"


def test_candidate_runtime_sweep_execute_splits_windows_paths() -> None:
    tokens = _command_tokens(
        r'glass run --plan C:\gpwbpp_runs\final\processing_plan.json --root "C:\some path\data"',
        r"C:\Tools\glass.exe",
    )

    assert tokens == [
        r"C:\Tools\glass.exe",
        "run",
        "--plan",
        r"C:\gpwbpp_runs\final\processing_plan.json",
        "--root",
        r"C:\some path\data",
    ]


def test_candidate_runtime_sweep_execute_skip_existing(tmp_path: Path) -> None:
    existing = tmp_path / "existing.json"
    existing.write_text("{}", encoding="utf-8")
    plan = tmp_path / "plan.json"
    _write_plan(plan, existing_comparison=existing)

    payload = build_candidate_runtime_sweep_execution(plan, dry_run=True, skip_existing=True)

    assert payload["summary"]["skipped_existing_count"] == 1
    assert payload["variants"][0]["status"] == "skipped_existing"
    assert payload["variants"][1]["status"] == "planned"


def test_cli_candidate_runtime_sweep_execute_dry_run_writes_output(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    out = tmp_path / "execution.json"
    _write_plan(plan)

    assert (
        main(
            [
                "candidate-runtime-sweep-execute",
                "--plan",
                str(plan),
                "--out",
                str(out),
                "--variant",
                "prefetch10_workers5",
                "--dry-run",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "candidate_runtime_sweep_execution"
    assert payload["summary"]["status"] == "planned"
