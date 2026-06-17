from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_runtime_repeat_execute import build_resident_runtime_repeat_execution


def _write_plan(path: Path, root: Path) -> None:
    write_json(
        path,
        {
            "artifact_type": "resident_runtime_repeat_plan",
            "runs": [
                {
                    "run_id": "repeat01",
                    "run_dir": str(root / "repeat01"),
                    "command": f"glass run --out {root / 'repeat01'}",
                },
                {
                    "run_id": "repeat02",
                    "run_dir": str(root / "repeat02"),
                    "command": f"glass run --out {root / 'repeat02'}",
                },
            ],
            "compare_command": (
                f"glass resident-runtime-compare --run repeat01={root / 'repeat01'} "
                f"--run repeat02={root / 'repeat02'} --out {root / 'runtime_compare.json'}"
            ),
        },
    )


def test_resident_runtime_repeat_execute_dry_run_records_steps(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    _write_plan(plan, tmp_path / "runs")

    payload = build_resident_runtime_repeat_execution(plan, dry_run=True)

    assert payload["artifact_type"] == "resident_runtime_repeat_execution"
    assert payload["summary"]["status"] == "planned"
    assert payload["summary"]["recorded_run_count"] == 2
    assert payload["runs"][0]["step"]["status"] == "planned"
    assert payload["compare"]["status"] == "planned"


def test_resident_runtime_repeat_execute_skip_existing(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    run_root = tmp_path / "runs"
    _write_plan(plan, run_root)
    (run_root / "repeat01").mkdir(parents=True)
    write_json(run_root / "repeat01" / "run_timing.json", {"total_elapsed_s": 1.0})

    payload = build_resident_runtime_repeat_execution(plan, dry_run=True, skip_existing=True)

    assert payload["summary"]["skipped_existing_count"] == 1
    assert payload["runs"][0]["status"] == "skipped_existing"
    assert payload["runs"][1]["status"] == "planned"


def test_resident_runtime_repeat_execute_cli_writes_audit(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    out = tmp_path / "execution.json"
    _write_plan(plan, tmp_path / "runs")

    assert (
        main(
            [
                "resident-runtime-repeat-execute",
                "--plan",
                str(plan),
                "--out",
                str(out),
                "--dry-run",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["status"] == "planned"
    assert payload["summary"]["compare_status"] == "planned"
