from __future__ import annotations

from gpwbpp.models import FrameGroup, FrameRecord


def _same_shape(frame: FrameRecord, group: FrameGroup) -> bool:
    return (frame.width, frame.height) == group.shape


def _same_sensor(frame: FrameRecord, group: FrameGroup) -> bool:
    return (
        frame.gain == group.gain
        and frame.offset == group.offset
        and (frame.binning_x, frame.binning_y) == group.binning
        and _same_shape(frame, group)
    )


def find_bias_group(light: FrameRecord, groups: list[FrameGroup]) -> FrameGroup | None:
    candidates = [g for g in groups if g.group_type == "bias" and _same_sensor(light, g)]
    return candidates[0] if candidates else None


def find_dark_group(light: FrameRecord, groups: list[FrameGroup]) -> FrameGroup | None:
    candidates = [g for g in groups if g.group_type == "dark" and _same_sensor(light, g)]
    exact = [g for g in candidates if g.exposure_s == light.exposure_s]
    return (exact or candidates or [None])[0]


def find_flat_group(light: FrameRecord, groups: list[FrameGroup]) -> FrameGroup | None:
    candidates = [
        g
        for g in groups
        if g.group_type == "flat"
        and g.filter == light.filter
        and g.gain == light.gain
        and g.offset == light.offset
        and g.binning == (light.binning_x, light.binning_y)
        and g.shape == (light.width, light.height)
    ]
    return candidates[0] if candidates else None

