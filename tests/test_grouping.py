from __future__ import annotations

from glass.metadata.scanner import scan_tree
from glass.models import FrameRecord
from glass.planner.grouping import group_frames


def test_group_frames_by_calibration_keys(small_fits_dataset):
    manifest = scan_tree(small_fits_dataset)
    frames = [FrameRecord(**frame) for frame in manifest["frames"]]
    groups = group_frames(frames)
    assert {group.group_type for group in groups} == {"bias", "dark", "flat", "light"}
    assert all(group.frames for group in groups)

