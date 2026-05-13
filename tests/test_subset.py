from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json
from glass.metadata.scanner import scan_tree
from glass.planner.plan_builder import build_processing_plan
from glass.planner.subset import build_subset_manifest
from glass.synthetic.generator import generate_synthetic_dataset


def test_build_subset_manifest_keeps_matching_calibration(tmp_path: Path):
    data = tmp_path / "data"
    generate_synthetic_dataset(data, frames=4, width=24, height=20, filt="H")
    manifest = scan_tree(data)
    subset = build_subset_manifest(manifest, filter_name="H", light_limit=2)
    assert subset["summary"]["frame_type"]["light"] == 2
    assert subset["summary"]["frame_type"]["bias"] >= 1
    assert subset["summary"]["frame_type"]["dark"] >= 1
    assert subset["summary"]["frame_type"]["flat"] >= 1
    plan = build_processing_plan(subset, tmp_path / "subset_manifest.json")
    assert plan.executable is True


def test_build_subset_manifest_can_keep_all_compatible_calibration(tmp_path: Path):
    data = tmp_path / "data"
    generate_synthetic_dataset(data, frames=4, width=24, height=20, filt="H")
    manifest = scan_tree(data)
    manifest_summary = manifest["summary"]["frame_type"]
    subset = build_subset_manifest(
        manifest,
        filter_name="H",
        light_limit=2,
        all_compatible_calibration=True,
    )
    assert subset["summary"]["frame_type"]["light"] == 2
    assert subset["summary"]["frame_type"]["bias"] == manifest_summary["bias"]
    assert subset["summary"]["frame_type"]["dark"] == manifest_summary["dark"]
    assert subset["summary"]["frame_type"]["flat"] == manifest_summary["flat"]
    plan = build_processing_plan(subset, tmp_path / "subset_manifest.json")
    assert plan.executable is True


def test_subset_cli_writes_plan(tmp_path: Path):
    data = tmp_path / "data"
    manifest_path = tmp_path / "manifest.json"
    subset_path = tmp_path / "subset.json"
    plan_path = tmp_path / "plan.json"
    generate_synthetic_dataset(data, frames=3, width=16, height=16, filt="H")
    assert main(["scan", "--root", str(data), "--out", str(manifest_path)]) == 0
    assert (
        main(
            [
                "subset",
                "--manifest",
                str(manifest_path),
                "--out",
                str(subset_path),
                "--plan-out",
                str(plan_path),
                "--filter",
                "H",
                "--light-limit",
                "2",
            ]
        )
        == 0
    )
    subset = read_json(subset_path)
    plan = read_json(plan_path)
    assert subset["summary"]["count"] == 5
    assert plan["executable"] is True
