from __future__ import annotations

import hashlib
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_release_manifest import build_windows_release_manifest


def _suite(path: Path, *, zip_paths: dict[str, Path], passed: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_package_suite",
            "status": "package_suite_ready" if passed else "blocked",
            "passed": passed,
            "recommendation": "publish_package_suite" if passed else "fix_package_suite_blockers",
            "failed_checks": [] if passed else ["smoke_passed:cuda13"],
            "rows": [
                {
                    "label": label,
                    "path": str(path.with_name(f"{label}_smoke.json")),
                    "passed": True,
                    "package_label": label,
                    "source_stamp": "abc1234",
                    "zip_path": str(zip_path),
                    "zip_size_bytes": zip_path.stat().st_size,
                    "require_cuda": label != "cpu",
                    "cuda_available": label != "cpu",
                    "native_extension_loaded": label != "cpu",
                }
                for label, zip_path in zip_paths.items()
            ],
        },
    )


def test_windows_release_manifest_records_sha256(tmp_path: Path):
    zip_paths: dict[str, Path] = {}
    for label in ("cuda13", "cpu"):
        zip_file = tmp_path / f"{label}.zip"
        zip_file.write_bytes(f"zip-{label}".encode("ascii"))
        zip_paths[label] = zip_file
    suite_path = tmp_path / "suite.json"
    _suite(suite_path, zip_paths=zip_paths)

    payload = build_windows_release_manifest(suite_artifact=suite_path)

    rows = {str(row["label"]): row for row in payload["packages"]}
    assert payload["passed"] is True
    assert rows["cuda13"]["sha256"] == hashlib.sha256(b"zip-cuda13").hexdigest()
    assert rows["cpu"]["size_bytes"] == len(b"zip-cpu")


def test_windows_release_manifest_blocks_failed_suite(tmp_path: Path):
    zip_file = tmp_path / "cuda13.zip"
    zip_file.write_bytes(b"package")
    suite_path = tmp_path / "suite.json"
    _suite(suite_path, zip_paths={"cuda13": zip_file}, passed=False)

    payload = build_windows_release_manifest(suite_artifact=suite_path)

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["suite_passed"] is False


def test_windows_release_manifest_cli_writes_outputs(tmp_path: Path):
    zip_file = tmp_path / "cpu.zip"
    zip_file.write_bytes(b"portable-cpu")
    suite_path = tmp_path / "suite.json"
    _suite(suite_path, zip_paths={"cpu": zip_file})
    out = tmp_path / "manifest.json"
    markdown = tmp_path / "manifest.md"

    result = main(
        [
            "windows-release-manifest",
            "--suite",
            str(suite_path),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failure",
        ]
    )

    assert result == 0
    assert read_json(out)["status"] == "release_manifest_ready"
    assert "GLASS Windows Release Manifest" in markdown.read_text(encoding="utf-8")
