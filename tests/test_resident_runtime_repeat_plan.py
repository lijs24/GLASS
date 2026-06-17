from __future__ import annotations

import subprocess
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json
from glass.report.resident_runtime_repeat_plan import build_resident_runtime_repeat_plan


def _base_command(path: Path) -> None:
    command = subprocess.list2cmdline(
        [
            "glass",
            "run",
            "--plan",
            r"C:\data with spaces\processing_plan.json",
            "--out",
            r"C:\old runs\throughput",
            "--backend",
            "cuda",
            "--resident-runtime-preset",
            "throughput-v1",
        ]
    )
    path.write_text(command, encoding="utf-8")


def test_resident_runtime_repeat_plan_replaces_out_and_adds_compare(tmp_path: Path) -> None:
    command_file = tmp_path / "run_command.txt"
    root = tmp_path / "repeat"
    _base_command(command_file)

    payload = build_resident_runtime_repeat_plan(
        base_run_command=command_file,
        root=root,
        label="throughput_v1",
        repeats=2,
        cache_state="warm",
    )

    assert payload["artifact_type"] == "resident_runtime_repeat_plan"
    assert payload["repeat_count"] == 2
    assert payload["runs"][0]["run_id"] == "throughput_v1_repeat01"
    assert str(root / "runs" / "throughput_v1_repeat01") in payload["runs"][0]["command"]
    assert r"C:\old runs\throughput" not in payload["runs"][0]["command"]
    assert "resident-runtime-compare" in payload["compare_command"]
    assert "throughput_v1_repeat02" in payload["compare_command"]


def test_resident_runtime_repeat_plan_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    command_file = tmp_path / "run_command.txt"
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"
    _base_command(command_file)

    assert (
        main(
            [
                "resident-runtime-repeat-plan",
                "--base-run-command",
                str(command_file),
                "--root",
                str(tmp_path / "planned"),
                "--label",
                "preset",
                "--repeats",
                "3",
                "--cache-state",
                "dedicated_io_window",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["cache_state"] == "dedicated_io_window"
    assert len(payload["runs"]) == 3
    assert "Resident Runtime Repeat Plan" in markdown.read_text(encoding="utf-8")
