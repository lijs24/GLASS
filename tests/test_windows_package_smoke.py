from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json
from glass.report.windows_package_smoke import build_windows_package_smoke


def _write_fake_package(root: Path, *, with_zip: bool = True) -> Path:
    root.mkdir(parents=True)
    runtime = root / "runtime"
    runtime.mkdir()
    (runtime / "python.exe").write_text("fake", encoding="ascii")
    (root / "glass.cmd").write_text("@echo off\n", encoding="ascii")
    (root / "glass-doctor.cmd").write_text("@echo off\n", encoding="ascii")
    (root / "README.md").write_text("# GLASS\n", encoding="utf-8")
    (root / "LICENSE").write_text("license\n", encoding="utf-8")
    (root / "source").write_text("abc1234\n", encoding="ascii")
    docs = root / "docs"
    docs.mkdir()
    (docs / "windows_release.md").write_text("# Windows\n", encoding="utf-8")
    zip_path = root.parent / "GLASS-Portable-win64.zip"
    if with_zip:
        zip_path.write_bytes(b"zip")
    return zip_path


def test_windows_package_smoke_structure_only_passes(tmp_path: Path):
    root = tmp_path / "GLASS"
    zip_path = _write_fake_package(root)

    payload = build_windows_package_smoke(
        package_root=root,
        zip_path=zip_path,
        expected_source="abc1234",
        execute=False,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "package_smoke_passed"
    assert checks["portable_zip_nonempty"] is True
    assert checks["source_stamp_matches_expected"] is True
    assert payload["package"]["zip_size_bytes"] == 3


def test_windows_package_smoke_catches_missing_zip(tmp_path: Path):
    root = tmp_path / "GLASS"
    zip_path = _write_fake_package(root, with_zip=False)

    payload = build_windows_package_smoke(
        package_root=root,
        zip_path=zip_path,
        execute=False,
    )

    checks = {item["name"]: item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["portable_zip_exists"] is False
    assert "portable_zip_exists" in payload["failed_checks"]


def test_windows_package_smoke_cli_writes_outputs(tmp_path: Path):
    root = tmp_path / "GLASS"
    zip_path = _write_fake_package(root)
    out = tmp_path / "smoke.json"
    markdown = tmp_path / "smoke.md"

    result = main(
        [
            "windows-package-smoke",
            "--package-root",
            str(root),
            "--zip",
            str(zip_path),
            "--expected-source",
            "abc1234",
            "--skip-exec",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["passed"] is True
    assert "GLASS Windows Package Smoke" in markdown.read_text(encoding="utf-8")
