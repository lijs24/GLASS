from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.windows_publish_preflight import build_windows_publish_preflight


def _matrix(path: Path, *, labels: list[str], ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_matrix",
            "status": "release_matrix_ready" if ready else "blocked",
            "passed": ready,
            "current_machine": {
                "primary_package": labels[0],
                "ordered_try_list": labels if "cpu" in labels else [*labels, "cpu"],
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
            "packages": [{"label": label} for label in labels],
        },
    )


def _default_promotion(path: Path, *, ready: bool = True) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "default_promotion_manifest",
            "status": "default_promotion_ready" if ready else "blocked",
            "passed": ready,
            "default_change_ready": ready,
            "recommendation": "promote_resident_cuda_default" if ready else "fix_blockers",
            "default_route_acceptance": {
                "status": "passed" if ready else "failed",
                "passed": ready,
                "route_contract_passed": ready,
                "route_check_count": 4 if ready else 2,
                "speedup_vs_reference": 28.75,
            },
        },
    )


def _manifest(path: Path, *, matrix: Path, labels: list[str]) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_release_manifest",
            "status": "release_manifest_ready",
            "passed": True,
            "source_stamps": ["abc1234"],
            "windows_release_matrix": {
                "path": str(matrix),
                "status": "release_matrix_ready",
                "passed": True,
            },
            "packages": [
                {
                    "label": label,
                    "zip_path": str(path.with_name(f"{label}.zip")),
                    "size_bytes": 100 + index,
                    "sha256": f"{index:064x}",
                    "source_stamp": "abc1234",
                }
                for index, label in enumerate(labels, start=1)
            ],
        },
    )


def _github_plan(
    path: Path,
    *,
    manifest: Path,
    matrix: Path,
    labels: list[str],
    asset_sha_override: dict[str, str] | None = None,
) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "artifact_type": "windows_github_release_plan",
            "status": "release_plan_ready",
            "passed": True,
            "publication_ready": True,
            "manifest_artifact": str(manifest),
            "release": {"tag": "v0.1.0-test"},
            "release_matrix": {
                "path": str(matrix),
                "status": "release_matrix_ready",
                "passed": True,
            },
            "assets": [
                {
                    "label": label,
                    "zip_path": str(manifest.with_name(f"{label}.zip")),
                    "size_bytes": 100 + index,
                    "sha256": (asset_sha_override or {}).get(label, f"{index:064x}"),
                    "source_stamp": "abc1234",
                }
                for index, label in enumerate(labels, start=1)
            ],
        },
    )


def _bundle(tmp_path: Path, *, labels: list[str] = ["cuda13", "cpu"], promotion_ready: bool = True):
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels, ready=promotion_ready)
    _default_promotion(promotion, ready=promotion_ready)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(plan, manifest=manifest, matrix=matrix, labels=labels)
    return manifest, plan, matrix, promotion


def test_windows_publish_preflight_passes_consistent_bundle(tmp_path: Path):
    manifest, plan, matrix, promotion = _bundle(tmp_path)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is True
    assert payload["status"] == "publish_preflight_ready"
    assert payload["summary"]["primary_package"] == "cuda13"
    assert checks["manifest_assets_match_github_plan"] is True
    assert checks["matrix_packages_match_manifest"] is True
    assert checks["cpu_fallback_preserved"] is True


def test_windows_publish_preflight_blocks_asset_mismatch(tmp_path: Path):
    labels = ["cuda13", "cpu"]
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "plan.json"
    matrix = tmp_path / "matrix.json"
    promotion = tmp_path / "promotion.json"
    _matrix(matrix, labels=labels)
    _default_promotion(promotion)
    _manifest(manifest, matrix=matrix, labels=labels)
    _github_plan(
        plan,
        manifest=manifest,
        matrix=matrix,
        labels=labels,
        asset_sha_override={"cuda13": "f" * 64},
    )

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["manifest_assets_match_github_plan"] is False


def test_windows_publish_preflight_blocks_failed_default_promotion(tmp_path: Path):
    manifest, plan, matrix, promotion = _bundle(tmp_path, promotion_ready=False)

    payload = build_windows_publish_preflight(
        release_manifest=manifest,
        github_release_plan=plan,
        windows_release_matrix=matrix,
        default_promotion_manifest=promotion,
    )

    checks = {str(item["name"]): item["passed"] for item in payload["checks"]}
    assert payload["passed"] is False
    assert checks["windows_release_matrix_ready"] is False
    assert checks["default_promotion_ready"] is False
    assert checks["default_route_contract_passed"] is False


def test_windows_publish_preflight_cli_writes_outputs(tmp_path: Path):
    manifest, plan, matrix, promotion = _bundle(tmp_path)
    out = tmp_path / "publish_preflight.json"
    markdown = tmp_path / "publish_preflight.md"

    result = main(
        [
            "windows-publish-preflight",
            "--release-manifest",
            str(manifest),
            "--github-release-plan",
            str(plan),
            "--windows-release-matrix",
            str(matrix),
            "--default-promotion-manifest",
            str(promotion),
            "--out",
            str(out),
            "--markdown",
            str(markdown),
            "--fail-on-failure",
        ]
    )

    assert result == 0
    payload = read_json(out)
    assert payload["status"] == "publish_preflight_ready"
    markdown_text = markdown.read_text(encoding="utf-8")
    assert "GLASS Windows Publish Preflight" in markdown_text
    assert "Default route checks/speedup: `4`/`28.75`" in markdown_text
    assert "manifest_assets_match_github_plan" in markdown_text
