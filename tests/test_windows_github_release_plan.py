from __future__ import annotations

from pathlib import Path
import sys

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_github_release_plan import build_windows_github_release_plan


def _manifest(path: Path, *, zip_paths: dict[str, Path], source: str = "abc1234") -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_manifest",
            "status": "release_manifest_ready",
            "passed": True,
            "failed_checks": [],
            "packages": [
                {
                    "label": label,
                    "zip_path": str(zip_path),
                    "exists": True,
                    "size_bytes": zip_path.stat().st_size,
                    "sha256": f"{index:064x}",
                    "source_stamp": source,
                }
                for index, (label, zip_path) in enumerate(zip_paths.items(), start=1)
            ],
        },
    )


def test_windows_github_release_plan_records_assets(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cuda13.zip"
    zip_file.write_bytes(b"zip")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cuda13": zip_file})

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        title="Test Release",
        notes_file=tmp_path / "notes.md",
        require_same_source_stamp=True,
    )

    assert payload["passed"] is True
    assert payload["publication_ready"] is True
    assert payload["assets"][0]["label"] == "cuda13"
    assert "gh release create v0.1.0-test" in payload["release"]["command"]
    assert "--draft" in payload["release"]["command"]


def test_windows_github_release_plan_blocks_mixed_sources(tmp_path: Path):
    zip_a = tmp_path / "a.zip"
    zip_b = tmp_path / "b.zip"
    zip_a.write_bytes(b"a")
    zip_b.write_bytes(b"b")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cuda13": zip_a}, source="aaa1111")
    payload = read_json(manifest)
    payload["packages"].append(
        {
            "label": "cpu",
            "zip_path": str(zip_b),
            "exists": True,
            "size_bytes": zip_b.stat().st_size,
            "sha256": "2".zfill(64),
            "source_stamp": "bbb2222",
        }
    )
    write_json(manifest, payload)

    plan = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        require_same_source_stamp=True,
    )

    checks = {str(item["name"]): item["passed"] for item in plan["checks"]}
    assert plan["passed"] is False
    assert checks["same_source_stamp"] is False


def test_windows_github_release_plan_cli_writes_outputs(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cpu.zip"
    zip_file.write_bytes(b"cpu")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cpu": zip_file})
    out = tmp_path / "plan.json"
    markdown = tmp_path / "plan.md"
    notes = tmp_path / "notes.md"
    script = tmp_path / "publish_release.ps1"

    result = main(
        [
            "windows-github-release-plan",
            "--manifest",
            str(manifest),
            "--tag",
            "v0.1.0-test",
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--notes",
            str(notes),
            "--script",
            str(script),
            "--require-same-source-stamp",
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "release_plan_ready"
    assert payload["release"]["script_file"] == str(script.resolve())
    assert payload["release"]["script_default_mode"] == "dry_run_requires_publish_switch"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows GitHub Release Plan" in markdown_text
    assert "Publish script" in markdown_text
    assert "Recommended Install Order" in notes.read_text(encoding="utf-8")
    script_text = script.read_text(encoding="utf-8")
    assert "$ExpectedTag = 'v0.1.0-test'" in script_text
    assert "GitHub CLI authentication check failed" in script_text
    assert "Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256" in script_text
    assert "SizeBytes = 3" in script_text
    assert "Re-run this script with -Publish" in script_text
    assert "& $GhPath @releaseArgs" in script_text
    assert "GitHub release creation failed" in script_text


def test_windows_github_release_plan_auth_check_blocks_publication(tmp_path: Path):
    zip_file = tmp_path / "GLASS-Portable-win64-cpu.zip"
    zip_file.write_bytes(b"cpu")
    manifest = tmp_path / "manifest.json"
    _manifest(manifest, zip_paths={"cpu": zip_file})

    payload = build_windows_github_release_plan(
        manifest_artifact=manifest,
        tag="v0.1.0-test",
        gh_path=sys.executable,
        check_gh=True,
        check_gh_auth=True,
    )

    assert payload["passed"] is True
    assert payload["publication_ready"] is False
    assert payload["gh"]["available"] is True
    assert payload["gh"]["auth_ok"] is False
    assert payload["recommendation"] == "authenticate_github_cli_then_run_release_command"
