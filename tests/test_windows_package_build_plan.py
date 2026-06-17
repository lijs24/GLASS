from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json
from glass.report.windows_package_build_plan import (
    build_windows_package_build_plan,
    discover_cuda_toolkits,
    parse_toolkit_root_specs,
)


def _fake_cuda_root(base: Path, version: str) -> Path:
    root = base / f"v{version}"
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "nvcc.exe").write_text("fake nvcc\n", encoding="utf-8")
    return root


def _variant(payload: dict, label: str) -> dict:
    return {str(row["label"]): row for row in payload["variants"]}[label]


def test_windows_package_build_plan_marks_missing_cuda_variants(tmp_path: Path):
    cuda_base = tmp_path / "CUDA"
    cuda13 = _fake_cuda_root(cuda_base, "13.2")

    payload = build_windows_package_build_plan(
        release_root=tmp_path / "release",
        cuda_base=cuda_base,
        python=r".\.venv\Scripts\python.exe",
    )

    assert payload["passed"] is True
    assert payload["status"] == "partial_toolkits"
    assert payload["ready_variants"] == ["cuda13", "cpu"]
    assert payload["missing_cuda_variants"] == ["cuda12", "cuda11"]

    cuda13_row = _variant(payload, "cuda13")
    assert cuda13_row["build_ready"] is True
    assert cuda13_row["toolkit_root"] == str(cuda13)
    assert cuda13_row["toolkit_match"] == "major_compatible"
    assert "-PackageLabel cuda13" in cuda13_row["build_command_text"]
    assert "-CudaToolkitRoot" in cuda13_row["build_command_text"]

    cuda12_row = _variant(payload, "cuda12")
    assert cuda12_row["build_ready"] is False
    assert cuda12_row["skip_reason"] == "matching_cuda_toolkit_not_found"
    assert cuda12_row["build_command"] is None
    assert "install_cuda_toolkit_minimal.ps1" in cuda12_row["toolkit_download_command_text"]
    assert "-Download" in cuda12_row["toolkit_download_command_text"]
    assert "-Install" in cuda12_row["toolkit_install_command_text"]


def test_windows_package_build_plan_strict_requires_all_toolkits(tmp_path: Path):
    cuda_base = tmp_path / "CUDA"
    _fake_cuda_root(cuda_base, "13.2")

    payload = build_windows_package_build_plan(
        release_root=tmp_path / "release",
        cuda_base=cuda_base,
        require_all_toolkits=True,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert checks["all_requested_cuda_toolkits_ready"] is False


def test_windows_package_build_plan_cli_writes_json_and_markdown(tmp_path: Path):
    cuda_base = tmp_path / "CUDA"
    _fake_cuda_root(cuda_base, "13.2")
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"

    result = main(
        [
            "windows-package-build-plan",
            "--cuda-base",
            str(cuda_base),
            "--release-root",
            str(tmp_path / "release"),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["ready_variants"] == ["cuda13", "cpu"]
    assert "GLASS Windows Package Build Plan" in markdown.read_text(encoding="utf-8")


def test_windows_package_build_plan_cli_fail_on_missing(tmp_path: Path):
    cuda_base = tmp_path / "CUDA"
    _fake_cuda_root(cuda_base, "13.2")
    out = tmp_path / "plan.json"

    result = main(
        [
            "windows-package-build-plan",
            "--cuda-base",
            str(cuda_base),
            "--out",
            str(out),
            "--fail-on-missing",
        ]
    )

    assert result == 2
    assert read_json(out)["missing_cuda_variants"] == ["cuda12", "cuda11"]


def test_toolkit_discovery_and_override_parsing(tmp_path: Path):
    cuda_base = tmp_path / "CUDA"
    cuda12 = _fake_cuda_root(cuda_base, "12.4")

    discovered = discover_cuda_toolkits(cuda_base)
    assert discovered[0]["version"] == "12.4"
    assert discovered[0]["nvcc_exists"] is True
    assert parse_toolkit_root_specs([f"cuda12={cuda12}"]) == {"cuda12": str(cuda12)}
