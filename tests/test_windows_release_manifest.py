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


def _release_matrix(path: Path, *, labels: list[str], ready: bool = True) -> None:
    ordered_try_list = labels if "cpu" in labels else [*labels, "cpu"]
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_matrix",
            "status": "release_matrix_ready" if ready else "blocked",
            "passed": ready,
            "recommendation": "publish_windows_cuda_matrix"
            if ready
            else "fix_release_matrix_blockers",
            "current_machine": {
                "primary_package": labels[0] if labels else None,
                "ordered_try_list": ordered_try_list,
                "cuda_available": "cpu" not in labels[:1],
                "native_extension_loaded": "cpu" not in labels[:1],
            },
            "default_promotion_manifest": {
                "status": "default_promotion_ready" if ready else "blocked",
                "passed": ready,
                "default_change_ready": ready,
                "default_route_passed": ready,
                "default_route_route_contract_passed": ready,
                "default_route_route_check_count": 4 if ready else 2,
                "default_route_speedup_vs_reference": 28.75,
            },
            "packages": [
                {
                    "label": label,
                    "release_artifact": f"GLASS-Portable-win64-{label}.zip",
                    "compatible": True,
                }
                for label in labels
            ],
            "failed_checks": [] if ready else ["default_promotion_manifest_ready"],
        },
    )


def test_windows_release_manifest_records_sha256(tmp_path: Path):
    zip_paths: dict[str, Path] = {}
    for label in ("cuda13", "cpu"):
        zip_file = tmp_path / f"{label}.zip"
        zip_file.write_bytes(f"zip-{label}".encode("ascii"))
        zip_paths[label] = zip_file
    suite_path = tmp_path / "suite.json"
    matrix_path = tmp_path / "matrix.json"
    _suite(suite_path, zip_paths=zip_paths)
    _release_matrix(matrix_path, labels=["cuda13", "cpu"])

    payload = build_windows_release_manifest(
        suite_artifact=suite_path,
        windows_release_matrix=matrix_path,
    )

    rows = {str(row["label"]): row for row in payload["packages"]}
    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["windows_release_matrix"]["status"] == "release_matrix_ready"
    assert checks["windows_release_matrix_ready"] is True
    assert checks["windows_release_matrix_default_route_passed"] is True
    assert rows["cuda13"]["sha256"] == hashlib.sha256(b"zip-cuda13").hexdigest()
    assert rows["cpu"]["size_bytes"] == len(b"zip-cpu")


def test_windows_release_manifest_blocks_failed_suite(tmp_path: Path):
    zip_file = tmp_path / "cuda13.zip"
    zip_file.write_bytes(b"package")
    suite_path = tmp_path / "suite.json"
    matrix_path = tmp_path / "matrix.json"
    _suite(suite_path, zip_paths={"cuda13": zip_file}, passed=False)
    _release_matrix(matrix_path, labels=["cuda13"])

    payload = build_windows_release_manifest(
        suite_artifact=suite_path,
        windows_release_matrix=matrix_path,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["suite_passed"] is False


def test_windows_release_manifest_blocks_missing_windows_release_matrix(tmp_path: Path):
    zip_file = tmp_path / "cuda13.zip"
    zip_file.write_bytes(b"package")
    suite_path = tmp_path / "suite.json"
    _suite(suite_path, zip_paths={"cuda13": zip_file})

    payload = build_windows_release_manifest(suite_artifact=suite_path)

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_present"] is False
    assert checks["windows_release_matrix_ready"] is False
    assert "windows_release_matrix_present" in payload["failed_checks"]


def test_windows_release_manifest_blocks_failed_windows_release_matrix(tmp_path: Path):
    zip_file = tmp_path / "cuda13.zip"
    zip_file.write_bytes(b"package")
    suite_path = tmp_path / "suite.json"
    matrix_path = tmp_path / "matrix.json"
    _suite(suite_path, zip_paths={"cuda13": zip_file})
    _release_matrix(matrix_path, labels=["cuda13"], ready=False)

    payload = build_windows_release_manifest(
        suite_artifact=suite_path,
        windows_release_matrix=matrix_path,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_present"] is True
    assert checks["windows_release_matrix_ready"] is False
    assert checks["windows_release_matrix_default_promotion_ready"] is False


def test_windows_release_manifest_cli_writes_outputs(tmp_path: Path):
    zip_file = tmp_path / "cpu.zip"
    zip_file.write_bytes(b"portable-cpu")
    suite_path = tmp_path / "suite.json"
    matrix_path = tmp_path / "matrix.json"
    _suite(suite_path, zip_paths={"cpu": zip_file})
    _release_matrix(matrix_path, labels=["cpu"])
    out = tmp_path / "manifest.json"
    markdown = tmp_path / "manifest.md"

    result = main(
        [
            "windows-release-manifest",
            "--suite",
            str(suite_path),
            "--windows-release-matrix",
            str(matrix_path),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "release_manifest_ready"
    assert payload["windows_release_matrix"]["primary_package"] == "cpu"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows Release Manifest" in markdown_text
    assert "Windows Release Matrix" in markdown_text
    assert "Default route contract/checks: `True`/`4`" in markdown_text
