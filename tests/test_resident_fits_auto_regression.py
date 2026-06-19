from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_fits_auto_regression import (
    build_resident_fits_auto_regression,
    write_resident_fits_auto_regression,
)


def _write_run(
    root: Path,
    *,
    requested: str = "auto",
    effective: str = "native_u16_gpu",
    backend_count: int = 4,
    checked: int = 4,
    eligible: int = 4,
    selected: bool = True,
    active: int = 3,
    masked: int = 1,
    unknown_zero_weight: int = 0,
    total_s: float = 10.0,
    light_s: float = 4.0,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write_json(
        root / "resident_artifacts.json",
        {
            "schema_version": 1,
            "artifacts": [
                {
                    "frame_ids": [f"F{index:06d}" for index in range(backend_count)],
                    "timing_s": {
                        "light_read_upload_calibrate": light_s,
                        "light_h2d_calibrate_store": 0.5,
                        "output_write": 0.25,
                    },
                    "resident_io_pipeline": {
                        "fits_read_mode": requested,
                        "fits_read_mode_requested": requested,
                        "fits_read_mode_effective": effective,
                        "fits_backend_counts": {"native_u16be_raw": backend_count}
                        if backend_count
                        else {"astropy_scaled_memmap": checked},
                        "raw_gpu_decode_enabled": effective == "native_u16_gpu",
                        "resident_fits_auto_selection": {
                            "requested_mode": requested,
                            "effective_mode": effective,
                            "policy": "guarded_auto",
                            "raw_u16_gpu": {
                                "checked": True,
                                "runtime_eligible": True,
                                "selected": selected,
                                "checked_frame_count": checked,
                                "eligible_frame_count": eligible,
                                "fallback_reason_counts": {}
                                if eligible == checked
                                else {"bitpix_not_16:-32": checked - eligible},
                                "ineligible_samples": [],
                            },
                        },
                    },
                    "resident_frame_mask_contract": {
                        "summary": {
                            "active_frame_count": active,
                            "masked_frame_count": masked,
                            "unknown_zero_weight_frame_count": unknown_zero_weight,
                            "passed": True,
                        }
                    },
                }
            ],
        },
    )
    write_json(root / "run_timing.json", {"schema_version": 1, "total_elapsed_s": total_s})
    write_json(root / "resident_dq_pixel_closure.json", {"summary": {"passed": True}})


def _write_compare(path: Path, *, rms: float = 0.0, max_abs: float = 0.0) -> None:
    write_json(
        path,
        {
            "shape_match": True,
            "rms_diff": rms,
            "relative_rms_diff": rms,
            "max_abs_diff": max_abs,
            "abs_diff_p999": max_abs,
        },
    )


def _fixture(tmp_path: Path) -> dict[str, Path]:
    run = tmp_path / "auto"
    explicit = tmp_path / "explicit"
    control = tmp_path / "control"
    compare_explicit = tmp_path / "auto_vs_explicit.json"
    compare_control = tmp_path / "auto_vs_control.json"
    _write_run(run, total_s=10.0, light_s=4.0)
    _write_run(explicit, requested="native_u16_gpu", effective="native_u16_gpu", total_s=9.5, light_s=3.8)
    _write_run(control, requested="astropy", effective="astropy", total_s=14.0, light_s=8.0)
    _write_compare(compare_explicit)
    _write_compare(compare_control)
    return {
        "run": run,
        "explicit": explicit,
        "control": control,
        "compare_explicit": compare_explicit,
        "compare_control": compare_control,
    }


def _build(paths: dict[str, Path]) -> dict:
    return build_resident_fits_auto_regression(
        paths["run"],
        explicit_run=paths["explicit"],
        control_run=paths["control"],
        compare_explicit=paths["compare_explicit"],
        compare_control=paths["compare_control"],
        min_lights=4,
        expected_active=3,
        expected_masked=1,
        expected_unknown_zero_weight=0,
    )


def test_resident_fits_auto_regression_passes_guarded_auto_fixture(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)

    payload = _build(paths)

    assert payload["passed"] is True
    assert payload["status"] == "passed"
    assert payload["summary"]["effective_mode"] == "native_u16_gpu"
    assert payload["summary"]["eligible_frame_count"] == 4
    assert not payload["failed_checks"]


def test_resident_fits_auto_regression_detects_auto_fallback(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _write_run(
        paths["run"],
        effective="auto",
        backend_count=0,
        eligible=0,
        selected=False,
        total_s=10.0,
        light_s=4.0,
    )

    payload = _build(paths)

    assert payload["passed"] is False
    assert "fits_read_mode_effective_matches" in payload["failed_checks"]
    assert "raw_gpu_all_checked_frames_eligible" in payload["failed_checks"]


def test_resident_fits_auto_regression_detects_compare_drift(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _write_compare(paths["compare_control"], rms=1.0e-3, max_abs=2.0e-3)

    payload = _build(paths)

    assert payload["passed"] is False
    assert "auto_vs_control_rms_within_limit" in payload["failed_checks"]
    assert "auto_vs_control_max_abs_within_limit" in payload["failed_checks"]


def test_resident_fits_auto_regression_detects_timing_regression(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _write_run(paths["run"], total_s=13.0, light_s=6.5)

    payload = _build(paths)

    assert payload["passed"] is False
    assert "run_total_close_to_explicit_raw_gpu" in payload["failed_checks"]
    assert "light_bucket_faster_than_control" in payload["failed_checks"]


def test_resident_fits_auto_regression_writes_markdown(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"

    payload = _build(paths)
    write_resident_fits_auto_regression(out, payload, markdown=markdown)

    assert read_json(out)["passed"] is True
    assert "Resident FITS Auto Regression" in markdown.read_text(encoding="utf-8")


def test_resident_fits_auto_regression_cli_writes_artifacts(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    out = tmp_path / "audit.json"
    markdown = tmp_path / "audit.md"

    assert (
        main(
            [
                "resident-fits-auto-regression",
                "--run",
                str(paths["run"]),
                "--explicit-run",
                str(paths["explicit"]),
                "--control-run",
                str(paths["control"]),
                "--compare-explicit",
                str(paths["compare_explicit"]),
                "--compare-control",
                str(paths["compare_control"]),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--min-lights",
                "4",
                "--expected-active",
                "3",
                "--expected-masked",
                "1",
                "--expected-unknown-zero-weight",
                "0",
                "--fail-on-failure",
            ]
        )
        == 0
    )
    assert read_json(out)["passed"] is True
    assert markdown.exists()


def test_resident_fits_auto_regression_cli_fail_on_failure(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    failed = deepcopy(read_json(paths["compare_explicit"]))
    failed["max_abs_diff"] = 1.0
    write_json(paths["compare_explicit"], failed)
    out = tmp_path / "audit.json"

    assert (
        main(
            [
                "resident-fits-auto-regression",
                "--run",
                str(paths["run"]),
                "--compare-explicit",
                str(paths["compare_explicit"]),
                "--compare-control",
                str(paths["compare_control"]),
                "--out",
                str(out),
                "--min-lights",
                "4",
                "--expected-active",
                "3",
                "--expected-masked",
                "1",
                "--expected-unknown-zero-weight",
                "0",
                "--fail-on-failure",
            ]
        )
        == 2
    )
    assert read_json(out)["passed"] is False
