from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.local_norm_contract import (
    EXPECTED_COEFFICIENT_FIELD_MODEL,
    EXPECTED_INTERPOLATION,
    EXPECTED_MODEL,
    build_local_norm_contract,
)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fixture")


def _write_enabled_local_norm_run(
    run: Path,
    *,
    model: str = EXPECTED_MODEL,
    coefficient_field_model: str = EXPECTED_COEFFICIENT_FIELD_MODEL,
    coefficient_model: str | None = None,
    coefficient_field_status: str = "written",
) -> None:
    run.mkdir(parents=True)
    local_norm_dir = run / "local_norm_cache"
    dq_dir = run / "dq_cache"
    normalized = local_norm_dir / "local_norm_L1.fits"
    coverage = run / "registered_cache" / "coverage_L1.fits"
    dq_mask = dq_dir / "dq_local_norm_L1.fits"
    coefficient = local_norm_dir / "local_norm_L1_coefficients.json"
    scale = local_norm_dir / "local_norm_L1_scale_field.fits"
    offset = local_norm_dir / "local_norm_L1_offset_field.fits"
    residual = local_norm_dir / "local_norm_L1_residual.fits"
    for path in [normalized, coverage, dq_mask, scale, offset, residual]:
        _touch(path)
    residual_summary = {"valid_pixels": 4, "mean": 0.0, "rms": 0.01, "max_abs": 0.02}
    coefficient_payload = {
        "schema_version": 1,
        "frame_id": "L1",
        "reference_frame_id": "L1",
        "model": coefficient_model or model,
        "coefficient_field_model": coefficient_field_model,
        "interpolation": EXPECTED_INTERPOLATION,
        "formula": "output = scale_field * source + offset_field",
        "tile_size": 4,
        "grid_rows": 1,
        "grid_cols": 1,
        "raw_scales": [[1.0]],
        "raw_offsets": [[0.0]],
        "scales": [[1.0]],
        "offsets": [[0.0]],
        "valid_pixels": [[4]],
        "statuses": [["ok"]],
        "empty_tiles_filled": 0,
        "full_field_map_status": coefficient_field_status,
        "scale_field_path": str(scale),
        "offset_field_path": str(offset),
        "residual_map_path": str(residual),
        "residual_summary": residual_summary,
        "crop_box": None,
    }
    write_json(coefficient, coefficient_payload)
    write_json(
        run / "local_norm_results.json",
        {
            "schema_version": 1,
            "enabled": True,
            "reference_frame_id": "L1",
            "reference_path": str(normalized),
            "model": model,
            "coefficient_field_model": coefficient_field_model,
            "crop_box": None,
            "local_norm_results": [
                {
                    "frame_id": "L1",
                    "input_path": str(normalized),
                    "normalized_path": str(normalized),
                    "coverage_path": str(coverage),
                    "dq_mask_path": str(dq_mask),
                    "dq_summary": {"valid": 4},
                    "coefficient_grid_path": str(coefficient),
                    "scale_field_path": str(scale),
                    "offset_field_path": str(offset),
                    "residual_map_path": str(residual),
                    "full_field_map_status": coefficient_field_status,
                    "model": model,
                    "coefficient_field_model": coefficient_field_model,
                    "interpolation": EXPECTED_INTERPOLATION,
                    "tile_size": 4,
                    "grid_rows": 1,
                    "grid_cols": 1,
                    "valid_pixels": 4,
                    "empty_tiles_filled": 0,
                    "residual_summary": residual_summary,
                    "crop_box": None,
                    "status": "reference",
                    "warnings": [],
                }
            ],
        },
    )


def _write_disabled_local_norm_run(run: Path) -> None:
    run.mkdir(parents=True)
    registered = run / "registered_cache" / "registered_L1.fits"
    coverage = run / "registered_cache" / "coverage_L1.fits"
    for path in [registered, coverage]:
        _touch(path)
    write_json(
        run / "local_norm_results.json",
        {
            "schema_version": 1,
            "enabled": False,
            "reference_frame_id": "L1",
            "coefficient_field_model": "disabled_passthrough",
            "crop_box": None,
            "local_norm_results": [
                {
                    "frame_id": "L1",
                    "input_path": str(registered),
                    "normalized_path": str(registered),
                    "coverage_path": str(coverage),
                    "dq_mask_path": None,
                    "dq_summary": {},
                    "coefficient_field_model": "disabled_passthrough",
                    "crop_box": None,
                    "backend": "passthrough",
                    "tile_count": 0,
                    "status": "disabled_passthrough",
                    "warnings": [],
                }
            ],
        },
    )


def test_local_norm_contract_passes_for_continuous_field_artifact(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_enabled_local_norm_run(run)

    payload = build_local_norm_contract(run)

    assert payload["artifact_type"] == "local_norm_contract"
    assert payload["passed"] is True
    assert payload["enabled"] is True
    assert payload["summary"]["output_count"] == 1
    assert payload["outputs"][0]["coefficient_grid_contract"]["passed"] is True


def test_local_norm_contract_passes_for_disabled_passthrough(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_disabled_local_norm_run(run)

    payload = build_local_norm_contract(run)

    assert payload["passed"] is True
    assert payload["enabled"] is False
    assert payload["outputs"][0]["status"] == "disabled_passthrough"


def test_local_norm_contract_rejects_piecewise_enabled_model(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _write_enabled_local_norm_run(run, model="grid_mean_std_piecewise")

    payload = build_local_norm_contract(run)

    assert payload["passed"] is False
    failed_top = {item["name"] for item in payload["checks"] if not item["passed"]}
    failed_row = set(payload["outputs"][0]["failed_checks"])
    assert "model_is_continuous" in failed_top
    assert "model_is_continuous" in failed_row


def test_local_norm_contract_cli_writes_markdown(tmp_path: Path) -> None:
    run = tmp_path / "run"
    out = tmp_path / "local_norm_contract.json"
    markdown = tmp_path / "local_norm_contract.md"
    _write_enabled_local_norm_run(run)

    assert (
        main(
            [
                "local-norm-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-failed",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["passed"] is True
    assert "Local Normalization Contract" in markdown.read_text(encoding="utf-8")


def test_local_norm_contract_cli_fails_on_bad_enabled_model(tmp_path: Path) -> None:
    run = tmp_path / "run"
    out = tmp_path / "local_norm_contract.json"
    _write_enabled_local_norm_run(run, model="grid_mean_std_piecewise")

    assert (
        main(
            [
                "local-norm-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--fail-on-failed",
            ]
        )
        == 2
    )
