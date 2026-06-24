from __future__ import annotations

from pathlib import Path

from glass.io.json_io import read_json
from glass.metadata.scanner import scan_tree
from glass.planner.plan_builder import build_processing_plan
from glass.synthetic.generator import generate_synthetic_dataset


def test_processing_plan_matches_calibration_groups(small_fits_dataset):
    manifest = scan_tree(small_fits_dataset)
    plan = build_processing_plan(manifest, small_fits_dataset / "manifest.json")
    assert plan.light_plans
    light_plan = plan.light_plans[0]
    assert light_plan.calibration_status == "ready"
    assert light_plan.matching_dark_group is not None
    assert light_plan.matching_flat_group is not None
    assert plan.executable is True


def test_processing_plan_binds_source_dq_manifest_to_light_frame(tmp_path: Path):
    dataset = tmp_path / "synthetic"
    generate_synthetic_dataset(dataset, frames=4, width=32, height=24, filt="H", source_dq_sidecars=True)
    manifest = scan_tree(dataset)
    source_dq_manifest_path = dataset / "source_dq_manifest.json"

    plan = build_processing_plan(
        manifest,
        tmp_path / "manifest.json",
        source_dq_manifest=read_json(source_dq_manifest_path),
        source_dq_manifest_path=source_dq_manifest_path,
    )

    bound = [frame for frame in plan.frames if frame.source_dq_mask_path]
    assert len(bound) == 1
    assert bound[0].frame_type == "light"
    assert Path(bound[0].source_dq_mask_path).is_absolute()
    assert Path(bound[0].source_dq_mask_path).exists()
