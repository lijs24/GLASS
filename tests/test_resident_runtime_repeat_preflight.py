from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_runtime_repeat_preflight import build_resident_runtime_repeat_preflight


READY_GPU = "NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97887, 1024, 5, 596.21"
BUSY_GPU = "NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97887, 55000, 100, 596.21"


def _write_plan(path: Path, root: Path) -> None:
    write_json(
        path,
        {
            "artifact_type": "resident_runtime_repeat_plan",
            "runs": [
                {
                    "run_id": "repeat01",
                    "run_dir": str(root / "repeat01"),
                    "command": f"glass run --backend cuda --memory-mode resident --out {root / 'repeat01'}",
                },
                {
                    "run_id": "repeat02",
                    "run_dir": str(root / "repeat02"),
                    "command": f"glass run --backend cuda --memory-mode resident --out {root / 'repeat02'}",
                },
            ],
            "compare_command": (
                f"glass resident-runtime-compare --run repeat01={root / 'repeat01'} "
                f"--run repeat02={root / 'repeat02'} --out {root / 'runtime_compare.json'}"
            ),
        },
    )


def test_resident_runtime_repeat_preflight_ready(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    _write_plan(plan, tmp_path / "runs")

    payload = build_resident_runtime_repeat_preflight(plan, gpu_query_text=READY_GPU)

    assert payload["ready_to_execute"] is True
    assert payload["recommendation"] == "execute_repeat_plan"
    assert payload["gpu"]["status"] == "ready"
    assert payload["summary"]["ready_run_count"] == 2


def test_resident_runtime_repeat_preflight_busy_gpu_waits(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    _write_plan(plan, tmp_path / "runs")

    payload = build_resident_runtime_repeat_preflight(plan, gpu_query_text=BUSY_GPU)

    assert payload["ready_to_execute"] is False
    assert payload["recommendation"] == "wait_for_controlled_window"
    assert payload["gpu"]["status"] == "busy"


def test_resident_runtime_repeat_preflight_detects_partial_output(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    run_root = tmp_path / "runs"
    _write_plan(plan, run_root)
    (run_root / "repeat01").mkdir(parents=True)

    payload = build_resident_runtime_repeat_preflight(plan, gpu_query_text=READY_GPU)

    assert payload["recommendation"] == "clean_outputs_or_use_skip_existing"
    assert payload["summary"]["conflict_run_count"] == 1


def test_resident_runtime_repeat_preflight_cli_writes_json(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    out = tmp_path / "preflight.json"
    _write_plan(plan, tmp_path / "runs")

    assert (
        main(
            [
                "resident-runtime-repeat-preflight",
                "--plan",
                str(plan),
                "--out",
                str(out),
                "--skip-gpu-probe",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "resident_runtime_repeat_preflight"
    assert payload["recommendation"] == "wait_for_controlled_window"
