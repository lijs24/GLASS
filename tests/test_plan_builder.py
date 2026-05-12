from __future__ import annotations

from gpwbpp.metadata.scanner import scan_tree
from gpwbpp.planner.plan_builder import build_processing_plan


def test_processing_plan_matches_calibration_groups(small_fits_dataset):
    manifest = scan_tree(small_fits_dataset)
    plan = build_processing_plan(manifest, small_fits_dataset / "manifest.json")
    assert plan.light_plans
    light_plan = plan.light_plans[0]
    assert light_plan.calibration_status == "ready"
    assert light_plan.matching_dark_group is not None
    assert light_plan.matching_flat_group is not None
    assert plan.executable is True

