from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_fits_default_matrix import (
    build_resident_fits_default_matrix,
    write_resident_fits_default_matrix,
)


def _write_resident_run(
    root: Path,
    *,
    requested: str = "auto",
    effective: str = "native_u16_gpu",
    resolution_source: str = "resident_cuda_guarded_auto_default",
    backend_counts: dict[str, int] | None = None,
    raw_selected: bool = True,
    raw_checked: bool = True,
    raw_eligible: bool = True,
    raw_decode: bool = True,
    checked: int = 2,
    eligible: int = 2,
    fallback_reason_counts: dict[str, int] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write_json(
        root / "resident_artifacts.json",
        {
            "schema_version": 1,
            "artifacts": [
                {
                    "resident_io_pipeline": {
                        "fits_read_mode": requested,
                        "fits_read_mode_requested": requested,
                        "fits_read_mode_effective": effective,
                        "fits_read_mode_resolution": {
                            "schema_version": 1,
                            "requested": None
                            if resolution_source == "resident_cuda_guarded_auto_default"
                            else requested,
                            "effective": requested,
                            "explicit": resolution_source == "explicit",
                            "source": resolution_source,
                        },
                        "fits_backend_counts": backend_counts or {"native_u16be_raw": checked},
                        "raw_gpu_decode_enabled": raw_decode,
                        "resident_fits_auto_selection": {
                            "requested_mode": requested,
                            "effective_mode": effective,
                            "policy": "explicit" if requested != "auto" else "guarded_auto",
                            "raw_u16_gpu": {
                                "checked": raw_checked,
                                "runtime_eligible": True,
                                "selected": raw_selected,
                                "eligible": raw_eligible,
                                "checked_frame_count": checked,
                                "eligible_frame_count": eligible,
                                "fallback_reason_counts": fallback_reason_counts or {},
                                "ineligible_samples": [],
                            },
                        },
                    }
                }
            ],
        },
    )
    write_json(
        root / "run_timing.json",
        {
            "resident_fits_read_mode_resolution": {
                "schema_version": 1,
                "requested": None if resolution_source == "resident_cuda_guarded_auto_default" else requested,
                "effective": requested,
                "explicit": resolution_source == "explicit",
                "source": resolution_source,
            }
        },
    )


def _write_cpu_tile_run(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write_json(
        root / "run_timing.json",
        {
            "backend": "cpu",
            "memory_mode": "tile",
            "resident_fits_read_mode_resolution": {
                "schema_version": 1,
                "requested": None,
                "effective": "astropy",
                "explicit": False,
                "source": "unused_non_resident",
            },
        },
    )


def _cases(tmp_path: Path) -> Path:
    compatible = tmp_path / "compatible"
    incompatible = tmp_path / "incompatible"
    explicit = tmp_path / "explicit_astropy"
    cpu_tile = tmp_path / "cpu_tile"
    _write_resident_run(compatible)
    _write_resident_run(
        incompatible,
        effective="auto",
        backend_counts={"fast_simple": 2},
        raw_selected=False,
        raw_eligible=False,
        raw_decode=False,
        eligible=0,
        fallback_reason_counts={"bitpix_not_16:-32": 2},
    )
    _write_resident_run(
        explicit,
        requested="astropy",
        effective="astropy",
        resolution_source="explicit",
        backend_counts={"astropy_scaled_memmap": 2},
        raw_selected=False,
        raw_checked=False,
        raw_eligible=False,
        raw_decode=False,
        checked=0,
        eligible=0,
    )
    _write_cpu_tile_run(cpu_tile)
    cases = tmp_path / "matrix_cases.json"
    write_json(
        cases,
        {
            "cases": [
                {
                    "name": "default_compatible_u16",
                    "run": str(compatible),
                    "expect": {
                        "resident": True,
                        "resolution_source": "resident_cuda_guarded_auto_default",
                        "fits_read_mode_requested": "auto",
                        "fits_read_mode_effective": "native_u16_gpu",
                        "raw_gpu_selected": True,
                        "raw_gpu_checked": True,
                        "raw_gpu_eligible": True,
                        "raw_gpu_decode_enabled": True,
                        "fallback_reason_counts": {},
                        "backend_count_min": {"native_u16be_raw": 2},
                    },
                },
                {
                    "name": "default_incompatible_float32",
                    "run": str(incompatible),
                    "expect": {
                        "resident": True,
                        "resolution_source": "resident_cuda_guarded_auto_default",
                        "fits_read_mode_requested": "auto",
                        "fits_read_mode_effective": "auto",
                        "raw_gpu_selected": False,
                        "raw_gpu_checked": True,
                        "raw_gpu_eligible": False,
                        "raw_gpu_decode_enabled": False,
                        "fallback_reason_min": {"bitpix_not_16:-32": 2},
                        "backend_count_min": {"fast_simple": 2},
                    },
                },
                {
                    "name": "explicit_astropy_escape_hatch",
                    "run": str(explicit),
                    "expect": {
                        "resident": True,
                        "resolution_source": "explicit",
                        "fits_read_mode_requested": "astropy",
                        "fits_read_mode_effective": "astropy",
                        "raw_gpu_selected": False,
                        "raw_gpu_checked": False,
                        "raw_gpu_decode_enabled": False,
                        "backend_count_min": {"astropy_scaled_memmap": 2},
                    },
                },
                {
                    "name": "cpu_tile_unaffected",
                    "run": str(cpu_tile),
                    "expect": {
                        "resident": False,
                        "resolution_source": "unused_non_resident",
                    },
                },
            ]
        },
    )
    return cases


def test_resident_fits_default_matrix_passes_expected_cases(tmp_path: Path) -> None:
    payload = build_resident_fits_default_matrix(_cases(tmp_path))

    assert payload["passed"] is True
    assert payload["case_count"] == 4
    assert payload["failed_cases"] == []
    rows = {row["name"]: row for row in payload["cases"]}
    assert rows["default_compatible_u16"]["summary"]["backend_counts"]["native_u16be_raw"] == 2
    assert rows["default_incompatible_float32"]["summary"]["raw_u16_gpu"]["fallback_reason_counts"] == {
        "bitpix_not_16:-32": 2
    }
    assert rows["cpu_tile_unaffected"]["summary"]["resident"] is False


def test_resident_fits_default_matrix_detects_bad_default_source(tmp_path: Path) -> None:
    cases = _cases(tmp_path)
    payload = read_json(cases)
    compatible = Path(payload["cases"][0]["run"])
    _write_resident_run(compatible, resolution_source="explicit")

    matrix = build_resident_fits_default_matrix(cases)

    assert matrix["passed"] is False
    assert matrix["failed_cases"] == ["default_compatible_u16"]
    failed = matrix["cases"][0]["failed_checks"]
    assert "resolution_source_matches" in failed


def test_resident_fits_default_matrix_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    cases = _cases(tmp_path)
    out = tmp_path / "matrix.json"
    markdown = tmp_path / "matrix.md"

    assert (
        main(
            [
                "resident-fits-default-matrix",
                "--cases",
                str(cases),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--fail-on-failure",
            ]
        )
        == 0
    )

    assert read_json(out)["passed"] is True
    assert "Resident FITS Default Compatibility Matrix" in markdown.read_text(encoding="utf-8")


def test_resident_fits_default_matrix_cli_fail_on_failure(tmp_path: Path) -> None:
    cases = _cases(tmp_path)
    payload = read_json(cases)
    payload["cases"][1]["expect"]["fits_read_mode_effective"] = "native_u16_gpu"
    write_json(cases, payload)

    assert (
        main(
            [
                "resident-fits-default-matrix",
                "--cases",
                str(cases),
                "--out",
                str(tmp_path / "failed.json"),
                "--fail-on-failure",
            ]
        )
        == 2
    )


def test_resident_fits_default_matrix_writes_markdown(tmp_path: Path) -> None:
    out = tmp_path / "matrix.json"
    markdown = tmp_path / "matrix.md"
    payload = build_resident_fits_default_matrix(_cases(tmp_path))

    write_resident_fits_default_matrix(out, payload, markdown=markdown)

    assert read_json(out)["passed"] is True
    text = markdown.read_text(encoding="utf-8")
    assert "default_compatible_u16" in text
    assert "native_u16be_raw=2" in text
