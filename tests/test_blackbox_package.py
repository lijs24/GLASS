from __future__ import annotations

import json
from pathlib import Path

from glass.cli import main
from glass.synthetic.generator import generate_synthetic_dataset


def test_blackbox_package_writes_handoff_files(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    package = tmp_path / "package"
    generate_synthetic_dataset(data, frames=2, width=20, height=20, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu", "--tile-size", "10"]) == 0
    assert (
        main(
            [
                "blackbox-package",
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--glass-run",
                str(audit),
                "--glass-time-seconds",
                "12.5",
                "--out",
                str(package),
            ]
        )
        == 0
    )
    payload = json.loads((package / "blackbox_package.json").read_text(encoding="utf-8"))
    timing = json.loads((package / "timing_template.json").read_text(encoding="utf-8"))
    assert payload["frame_count"] > 0
    assert payload["glass_master_count"] == 1
    assert timing["glass_time_seconds"] == 12.5
    assert timing["glass_timing_source"] == "explicit_cli"
    assert (package / "input_frames.csv").exists()
    assert "Do not read or copy official WBPP" in (package / "wbpp_manual_run.md").read_text(encoding="utf-8")
    assert "glass compare" in (package / "compare_command.ps1").read_text(encoding="utf-8")


def test_blackbox_package_uses_run_timing_when_time_omitted(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    package = tmp_path / "package"
    generate_synthetic_dataset(data, frames=2, width=20, height=20, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu", "--tile-size", "10"]) == 0
    run_timing = json.loads((audit / "run_timing.json").read_text(encoding="utf-8"))
    assert (
        main(
            [
                "blackbox-package",
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--glass-run",
                str(audit),
                "--out",
                str(package),
            ]
        )
        == 0
    )
    timing = json.loads((package / "timing_template.json").read_text(encoding="utf-8"))
    assert timing["glass_time_seconds"] == run_timing["total_elapsed_s"]
    assert timing["glass_timing_source"] == "run_timing_json"
    assert timing["glass_stage_timings"]


def test_blackbox_finalize_uses_run_timing_and_reports_speedup(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    package = tmp_path / "package"
    final = tmp_path / "final"
    generate_synthetic_dataset(data, frames=2, width=20, height=20, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu", "--tile-size", "10"]) == 0
    assert (
        main(
            [
                "blackbox-package",
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--glass-run",
                str(audit),
                "--out",
                str(package),
            ]
        )
        == 0
    )
    timing_path = package / "timing_template.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    gp_time = float(timing["glass_time_seconds"])
    timing["glass_time_seconds"] = None
    timing["reference_time_seconds"] = gp_time * 2.0
    timing["reference_master_paths"] = timing["glass_master_paths"]
    timing_path.write_text(json.dumps(timing, indent=2), encoding="utf-8")

    assert main(["blackbox-finalize", "--timing", str(timing_path), "--out", str(final)]) == 0
    summary = json.loads((final / "blackbox_finalize_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["glass_timing_source"] == "run_timing_json"
    assert summary["speedup_observed"] is True
    assert summary["all_glass_faster"] is True
