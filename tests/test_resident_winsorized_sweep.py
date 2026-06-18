from __future__ import annotations

import sys
from types import SimpleNamespace

from glass.cli import main
from glass.io.json_io import read_json
from glass.report.resident_winsorized_sweep import build_resident_winsorized_frame_count_sweep
from glass.report.resident_winsorized_sweep import parse_frame_counts
from glass.report.resident_winsorized_sweep import write_resident_winsorized_frame_count_sweep
from tests.conftest import cuda_module_or_skip


def test_parse_frame_counts_accepts_commas_and_semicolons() -> None:
    assert parse_frame_counts("8, 32;200") == [8, 32, 200]


def test_resident_winsorized_sweep_records_cuda_unavailable(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "glass_cuda",
        SimpleNamespace(cuda_available=lambda: False),
    )

    payload = build_resident_winsorized_frame_count_sweep(
        frame_counts=[3, 5],
        height=6,
        width=7,
        required_frame_count=5,
    )

    assert payload["status"] == "cuda_unavailable"
    assert payload["passed"] is False
    assert payload["summary"]["required_frame_count_present"] is True
    assert payload["summary"]["required_frame_count_passed"] is False
    assert [run["status"] for run in payload["runs"]] == ["cuda_unavailable", "cuda_unavailable"]


def test_resident_winsorized_sweep_matches_cpu_and_writes_markdown(tmp_path) -> None:
    cuda_module_or_skip()
    payload = build_resident_winsorized_frame_count_sweep(
        frame_counts=[4, 6],
        height=7,
        width=8,
        seed_base=17,
        required_frame_count=6,
    )
    out = tmp_path / "sweep.json"
    markdown = tmp_path / "sweep.md"

    write_resident_winsorized_frame_count_sweep(out, payload, markdown=markdown)

    saved = read_json(out)
    assert saved["passed"] is True
    assert saved["summary"]["required_frame_count_passed"] is True
    assert saved["summary"]["max_hardened_master_rms"] <= saved["config"]["tolerance_rms"]
    assert [run["frame_count"] for run in saved["runs"]] == [4, 6]
    assert "Resident Winsorized Frame-Count Sweep" in markdown.read_text(encoding="utf-8")


def test_resident_winsorized_sweep_cli_writes_artifacts(tmp_path) -> None:
    cuda_module_or_skip()
    out = tmp_path / "sweep.json"
    markdown = tmp_path / "sweep.md"

    assert (
        main(
            [
                "resident-winsorized-sweep",
                "--frame-counts",
                "4,6",
                "--required-frame-count",
                "6",
                "--height",
                "7",
                "--width",
                "8",
                "--seed-base",
                "23",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-failure",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["passed"] is True
    assert payload["config"]["required_frame_count"] == 6
    assert markdown.exists()
