from __future__ import annotations

from pathlib import Path

from gpwbpp.cli import main
from gpwbpp.io.json_io import read_json, write_json
from tests.conftest import cuda_module_or_skip


def test_cli_scan_plan_report_audit_smoke(small_fits_dataset, tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    report = tmp_path / "report.html"
    audit = tmp_path / "audit"
    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert manifest.exists()
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert plan.exists()
    assert main(["report", "--run", str(tmp_path), "--out", str(report)]) == 0
    assert report.exists()
    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (audit / "manifest.json").exists()
    assert (audit / "processing_plan.json").exists()
    assert (audit / "report.html").exists()


def test_cli_audit_resident_cuda_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    audit = tmp_path / "resident_audit"

    assert main(
        [
            "audit",
            "--root",
            str(small_fits_dataset),
            "--out",
            str(audit),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--local-normalization",
            "off",
            "--integration-weighting",
            "none",
            "--integration-rejection",
            "none",
            "--resident-registration",
            "off",
        ]
    ) == 0

    state = read_json(audit / "run_state.json")
    timing = read_json(audit / "run_timing.json")
    integration = read_json(audit / "integration_results.json")
    assert (audit / "manifest.json").exists()
    assert (audit / "processing_plan.json").exists()
    assert (audit / "resident_artifacts.json").exists()
    assert (audit / "report.html").exists()
    assert state["current_stage"] == "report"
    assert "resident_integration" in state["completed_stages"]
    assert timing["memory_mode"] == "resident"
    assert integration["source_stage"] == "resident_calibrated_stack"


def test_cli_help_commands():
    for command in [
        "scan",
        "plan",
        "subset",
        "run",
        "resume",
        "audit",
        "compare",
        "blackbox-package",
        "blackbox-finalize",
        "blackbox-history",
        "synthetic",
    ]:
        try:
            main([command, "--help"])
        except SystemExit as exc:
            assert exc.code == 0


def test_cli_report_includes_resident_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "resident_artifacts.json",
        {
            "backend": "cuda_resident_stack",
            "device": {"name": "Test GPU"},
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["F1", "F2"],
                    "master_stats": {"bias_count": 1, "dark_count": 1, "flat_count": 1},
                    "memory_estimate": {"resident_base_gib": 1.25, "estimated_peak_gib": 1.75},
                    "resident_registration": {"mode": "similarity_cuda_triangle", "warp_interpolation": "lanczos3"},
                    "resident_local_normalization": {"mode": "resident_grid_mean_std"},
                    "resident_integration_weighting": {"mode": "simple_snr"},
                    "integration_rejection": {"mode": "winsorized_sigma"},
                    "timing_s": {
                        "light_read_upload_calibrate": 2.0,
                        "resident_weighting": 0.1,
                        "resident_local_normalization": 0.2,
                        "resident_integration": 0.25,
                        "output_write": 0.5,
                    },
                }
            ],
        },
    )
    report = tmp_path / "resident_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")
    assert "Resident CUDA summary" in html
    assert "cuda_resident_stack" in html
    assert "Test GPU" in html
    assert "estimated_peak_gib" in html
    assert "similarity_cuda_triangle" in html
    assert "lanczos3" in html
    assert "resident_grid_mean_std" in html
    assert "simple_snr" in html
    assert "winsorized_sigma" in html
