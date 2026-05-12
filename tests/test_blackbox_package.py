from __future__ import annotations

import json
from pathlib import Path

from gpwbpp.cli import main
from gpwbpp.synthetic.generator import generate_synthetic_dataset


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
                "--gpwbpp-run",
                str(audit),
                "--gpwbpp-time-seconds",
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
    assert payload["gpwbpp_master_count"] == 1
    assert timing["gpwbpp_time_seconds"] == 12.5
    assert (package / "input_frames.csv").exists()
    assert "Do not read or copy official WBPP" in (package / "wbpp_manual_run.md").read_text(encoding="utf-8")
    assert "gpwbpp compare" in (package / "compare_command.ps1").read_text(encoding="utf-8")
