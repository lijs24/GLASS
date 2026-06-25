from __future__ import annotations

from pathlib import Path

import glass.cli as cli
from glass.engine.resident_reentry_boundary import build_resident_reentry_boundary
from glass.io.json_io import read_json, write_json


def _write_ready_calibration_boundary(run: Path) -> None:
    run.mkdir(parents=True, exist_ok=True)
    cache = run / "calib_cache" / "resident_masters"
    cache.mkdir(parents=True, exist_ok=True)
    cache_key = "H_24x24_bias-B_dark-D_flat-F_abc123"
    for suffix in ["master_stats.json", "master_bias.npy", "master_dark.npy", "master_flat.npy"]:
        (cache / f"{cache_key}_{suffix}").write_bytes(b"fixture")
    master_stats = {"min": 1.0, "max": 2.0, "mean": 1.5, "median": 1.5, "std": 0.1}
    write_json(
        run / "resident_master_cache.json",
        {
            "schema_version": 1,
            "artifact": "resident_master_cache",
            "summary": {
                "passed": True,
                "group_count": 1,
                "set_count": 1,
                "cache_hit_count": 1,
                "cache_miss_count": 0,
                "complete_set_count": 1,
                "incomplete_set_count": 0,
                "failed_group_count": 0,
                "total_required_bytes": 4,
            },
            "groups": [
                {
                    "filter": "H",
                    "passed": True,
                    "set_count": 1,
                    "complete_set_count": 1,
                    "incomplete_set_count": 0,
                    "missing_required_files": [],
                }
            ],
        },
    )
    write_json(
        run / "resident_calibration_contract.json",
        {
            "schema_version": 1,
            "artifact_type": "resident_cuda_calibration_contract",
            "status": "passed",
            "passed": True,
            "output_count": 1,
            "outputs": [{"index": 0, "passed": True, "frame_count": 2}],
        },
    )
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "artifact_type": "resident_cuda_calibration_artifacts",
            "backend": "cuda_resident_stack",
            "memory_mode": "resident",
            "masters": {
                "resident_bias_H": {
                    "path": str(cache / f"{cache_key}_master_bias.npy"),
                    "resident_calibration_contract": {"passed": True},
                    "stats": master_stats,
                },
                "resident_dark_H": {
                    "path": str(cache / f"{cache_key}_master_dark.npy"),
                    "resident_calibration_contract": {"passed": True},
                    "stats": master_stats,
                },
                "resident_flat_H": {
                    "path": str(cache / f"{cache_key}_master_flat.npy"),
                    "resident_calibration_contract": {"passed": True},
                    "stats": master_stats,
                },
            },
            "calibrated_lights": [
                {"frame_id": "L1", "status": "resident_in_vram", "dq_contract_ok": True},
                {"frame_id": "L2", "status": "resident_in_vram", "dq_contract_ok": True},
            ],
        },
    )


def _write_partial_resident_state(run: Path) -> None:
    write_json(
        run / "run_timing.json",
        {
            "schema_version": 1,
            "command": "run",
            "backend": "cuda",
            "memory_mode": "resident",
            "stages": [
                {"stage": "resident_calibration_integration", "status": "ok", "elapsed_s": 1.0}
            ],
        },
    )
    write_json(
        run / "run_state.json",
        {
            "run_id": run.name,
            "created_at": "2026-06-25T00:00:00+00:00",
            "current_stage": "resident_calibration_integration",
            "completed_stages": [],
            "failed_stage": None,
            "artifacts": [],
            "checksums": {},
            "warnings": [],
            "errors": [],
            "resume_supported": True,
        },
    )


def test_resident_reentry_boundary_detects_ready_calibration_boundary(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_ready_calibration_boundary(run)

    payload = build_resident_reentry_boundary(run)

    assert payload["artifact_type"] == "resident_reentry_boundary"
    assert payload["summary"]["master_cache_boundary_ready"] is True
    assert payload["summary"]["calibration_boundary_ready"] is True
    assert payload["summary"]["strongest_ready_boundary"] == "resident_calibration"
    assert payload["summary"]["calibration_boundary_resume_supported"] is False


def test_resident_reentry_boundary_rejects_invocation_for_other_out(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    _write_ready_calibration_boundary(run)
    write_json(
        run / "run_invocation.json",
        {
            "schema_version": 1,
            "artifact_type": "run_invocation",
            "subcommand": "run",
            "argv": ["run", "--out", str(tmp_path / "other")],
            "cwd": str(tmp_path),
        },
    )

    payload = build_resident_reentry_boundary(run)
    pre_integration = {
        row["name"]: row for row in payload["boundaries"]
    }["pre_integration_invocation"]

    assert pre_integration["ready"] is False
    assert pre_integration["resume_supported"] is False
    assert "run_invocation_out_mismatch" in pre_integration["reasons"]
    assert payload["summary"]["strongest_supported_boundary"] is None


def test_resident_resume_reports_ready_calibration_boundary_without_cpu_fallback(
    tmp_path: Path,
) -> None:
    run = tmp_path / "partial"
    _write_ready_calibration_boundary(run)
    _write_partial_resident_state(run)

    assert cli.main(["resume", "--run", str(run)]) == 2

    preflight = read_json(run / "resident_resume_preflight.json")
    assert preflight["passed"] is False
    assert preflight["resume_action"] == "blocked_calibration_boundary_reentry_not_implemented"
    assert preflight["summary"]["calibration_boundary_ready"] is True
    assert preflight["summary"]["strongest_ready_boundary"] == "resident_calibration"
    assert preflight["resident_reentry_boundary"]["summary"]["calibration_boundary_ready"] is True
    assert (run / "resident_reentry_boundary.json").exists()
    assert not (run / "calib_cache" / "master_bias").exists()
    state = read_json(run / "run_state.json")
    assert state["failed_stage"] == "resident_resume"
    assert any(artifact["stage"] == "resident_reentry_boundary" for artifact in state["artifacts"])


def test_resident_reentry_boundary_cli_writes_artifact(tmp_path: Path) -> None:
    run = tmp_path / "run"
    out = tmp_path / "boundary.json"
    _write_ready_calibration_boundary(run)

    assert (
        cli.main(
            [
                "resident-reentry-boundary",
                "--run",
                str(run),
                "--out",
                str(out),
                "--fail-on-missing",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["summary"]["calibration_boundary_ready"] is True
    assert payload["summary"]["strongest_ready_boundary"] == "resident_calibration"
