from __future__ import annotations

import sys
from types import SimpleNamespace

from glass.cli import main
from glass.io.json_io import read_json
from glass.report.resident_winsorized_benchmark import build_resident_winsorized_benchmark
from glass.report.resident_winsorized_benchmark import write_resident_winsorized_benchmark
from tests.conftest import cuda_module_or_skip


def test_resident_winsorized_benchmark_records_cuda_unavailable(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "glass_cuda",
        SimpleNamespace(cuda_available=lambda: False),
    )

    payload = build_resident_winsorized_benchmark(frame_count=4, height=6, width=7)

    assert payload["status"] == "cuda_unavailable"
    assert payload["passed"] is False
    assert payload["failed_checks"] == ["cuda_available"]
    assert payload["timing_s"]["cpu_baseline"] >= 0.0


def test_resident_winsorized_benchmark_matches_cpu_and_writes_markdown(tmp_path):
    cuda_module_or_skip()
    payload = build_resident_winsorized_benchmark(frame_count=6, height=8, width=9, seed=7)
    out = tmp_path / "resident_winsorized_benchmark.json"
    markdown = tmp_path / "resident_winsorized_benchmark.md"

    write_resident_winsorized_benchmark(out, payload, markdown=markdown)

    saved = read_json(out)
    assert saved["passed"] is True
    assert saved["status"] == "passed"
    assert saved["config"]["frame_count"] == 6
    assert saved["timing_s"]["cuda_hardened"] >= 0.0
    assert saved["timing_s"]["cuda_fast_approx"] >= 0.0
    assert saved["comparisons"]["hardened_vs_cpu"]["master"]["rms"] <= saved["config"]["tolerance_rms"]
    assert saved["cuda_hardened_timing"]["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert "Resident Winsorized Benchmark" in markdown.read_text(encoding="utf-8")


def test_resident_winsorized_benchmark_cli_writes_artifacts(tmp_path):
    cuda_module_or_skip()
    out = tmp_path / "benchmark.json"
    markdown = tmp_path / "benchmark.md"

    assert (
        main(
            [
                "resident-winsorized-benchmark",
                "--frames",
                "5",
                "--height",
                "7",
                "--width",
                "8",
                "--seed",
                "11",
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
    assert payload["config"]["frame_count"] == 5
    assert payload["cuda_hardened_timing"]["pixel_count"] == 56
    assert markdown.exists()
