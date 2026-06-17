from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_package_suite import build_windows_package_suite


def _smoke(path: Path, *, label: str, source: str = "abc1234", passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_package_smoke",
            "status": "package_smoke_passed" if passed else "blocked",
            "passed": passed,
            "failed_checks": [] if passed else ["portable_cuda_requirement"],
            "package": {
                "source_stamp": source,
                "zip_path": str(path.with_suffix(".zip")),
                "zip_size_bytes": 100,
                "manifest": {
                    "package_label": label,
                    "build_cuda": label != "cpu",
                    "source_stamp": source,
                },
            },
            "requirements": {"require_cuda": label != "cpu"},
            "execution": {
                "doctor_json": {
                    "cuda": {
                        "cuda_available": label != "cpu",
                        "native_extension_loaded": label != "cpu",
                    }
                }
            },
        },
    )


def test_windows_package_suite_passes_mixed_source_by_default(tmp_path: Path):
    paths = {}
    for index, label in enumerate(("cuda13", "cuda12", "cuda11", "cpu")):
        path = tmp_path / f"{label}.json"
        _smoke(path, label=label, source=f"abc{index}")
        paths[label] = str(path)

    payload = build_windows_package_suite(smoke_artifacts=paths)

    assert payload["passed"] is True
    assert payload["status"] == "package_suite_ready"
    assert payload["source_stamps"] == ["abc0", "abc1", "abc2", "abc3"]


def test_windows_package_suite_strict_source_stamp_blocks(tmp_path: Path):
    paths = {}
    for index, label in enumerate(("cuda13", "cuda12", "cuda11", "cpu")):
        path = tmp_path / f"{label}.json"
        _smoke(path, label=label, source=f"abc{index}")
        paths[label] = str(path)

    payload = build_windows_package_suite(
        smoke_artifacts=paths,
        require_same_source_stamp=True,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["same_source_stamp"] is False


def test_windows_package_suite_cli_writes_outputs(tmp_path: Path):
    args = ["windows-package-suite"]
    for label in ("cuda13", "cuda12", "cuda11", "cpu"):
        path = tmp_path / f"{label}.json"
        _smoke(path, label=label, source="abc1234")
        args.extend(["--smoke", f"{label}={path}"])
    out = tmp_path / "suite.json"
    markdown = tmp_path / "suite.md"
    args.extend(["--out", str(out), "--markdown", str(markdown), "--require-same-source-stamp", "--fail-on-failure"])

    result = main(args)

    assert result == 0
    assert read_json(out)["passed"] is True
    assert "GLASS Windows Package Suite" in markdown.read_text(encoding="utf-8")
