from __future__ import annotations

import pytest

from glass.cli import main
from glass.engine.rejection import RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT
from glass.io.json_io import read_json
from glass.report.resident_winsorized_benchmark import (
    build_resident_winsorized_overlimit_benchmark,
    write_resident_winsorized_overlimit_benchmark,
)
from tests.conftest import cuda_module_or_skip


def test_resident_winsorized_overlimit_benchmark_rejects_non_overlimit() -> None:
    with pytest.raises(ValueError, match="greater than"):
        build_resident_winsorized_overlimit_benchmark(
            frame_count=RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT,
            height=4,
            width=5,
        )


def test_resident_winsorized_overlimit_benchmark_matches_stack_engine(tmp_path):
    cuda_module_or_skip()
    payload = build_resident_winsorized_overlimit_benchmark(
        frame_count=RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT + 1,
        height=4,
        width=5,
        seed=627,
        tile_size=2,
        tolerance_rms=2.0e-5,
        tolerance_max_abs=2.0e-4,
    )
    out = tmp_path / "resident_winsorized_overlimit_benchmark.json"
    markdown = tmp_path / "resident_winsorized_overlimit_benchmark.md"

    write_resident_winsorized_overlimit_benchmark(out, payload, markdown=markdown)

    saved = read_json(out)
    assert saved["passed"] is True
    assert saved["status"] == "passed"
    assert saved["config"]["frame_count"] == RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT + 1
    assert saved["config"]["inject_nan"] is True
    assert saved["cuda_radix_timing"]["native_kernel_capacity_selector"] == (
        "radix_select_unbounded_positive_samples"
    )
    assert saved["cuda_radix_timing"]["native_profile"]["radix_select_enabled"] is True
    assert saved["cpu_stack_engine_baseline"]["metrics"]["rejection"] == "winsorized_sigma"
    assert saved["comparisons"]["radix_select_vs_cpu_stack_engine"]["master"]["rms"] <= (
        saved["config"]["tolerance_rms"]
    )
    assert "Resident Winsorized Over-Limit Benchmark" in markdown.read_text(encoding="utf-8")


def test_resident_winsorized_overlimit_benchmark_cli_writes_artifacts(tmp_path):
    cuda_module_or_skip()
    out = tmp_path / "benchmark.json"
    markdown = tmp_path / "benchmark.md"

    assert (
        main(
            [
                "resident-winsorized-overlimit-benchmark",
                "--frames",
                str(RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT + 1),
                "--height",
                "4",
                "--width",
                "5",
                "--tile-size",
                "2",
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
    assert payload["artifact_type"] == "resident_winsorized_overlimit_benchmark"
    assert payload["timing_s"]["cuda_radix_select"] >= 0.0
    assert payload["timing_s"]["cpu_stack_engine"] >= 0.0
    assert markdown.exists()
