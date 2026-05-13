from __future__ import annotations

from copy import deepcopy
from typing import Any

from glass.metadata.scanner import summarize_frames
from glass.models import FrameRecord, now_iso, to_jsonable
from glass.planner.grouping import group_frames
from glass.planner.matching import find_bias_group, find_dark_group, find_flat_group


def _frame_from_dict(value: dict[str, Any]) -> FrameRecord:
    return FrameRecord(**value)


def _text_match(value: str | None, expected: str | None) -> bool:
    if expected is None:
        return True
    return (value or "").casefold() == expected.casefold()


def _float_match(value: float | None, expected: float | None) -> bool:
    if expected is None:
        return True
    if value is None:
        return False
    return abs(float(value) - float(expected)) <= 1.0e-6


def _take_group_frames(
    group_id: str | None,
    group_by_id: dict[str, Any],
    frame_by_id: dict[str, FrameRecord],
    limit: int,
) -> list[FrameRecord]:
    if group_id is None or limit <= 0:
        return []
    group = group_by_id[group_id]
    return [frame_by_id[frame_id] for frame_id in sorted(group.frames)[:limit]]


def _same_camera_sampling(a: FrameRecord, b: FrameRecord) -> bool:
    return (
        a.width == b.width
        and a.height == b.height
        and a.binning_x == b.binning_x
        and a.binning_y == b.binning_y
        and a.gain == b.gain
        and a.offset == b.offset
    )


def _compatible_calibration_frames(frames: list[FrameRecord], lights: list[FrameRecord]) -> list[FrameRecord]:
    light_filters = {light.filter for light in lights if light.filter not in {None, ""}}
    light_exposures = {float(light.exposure_s) for light in lights if light.exposure_s is not None}

    def compatible(frame: FrameRecord) -> bool:
        if not any(_same_camera_sampling(frame, light) for light in lights):
            return False
        if frame.frame_type == "bias":
            return True
        if frame.frame_type == "dark":
            return frame.exposure_s is not None and any(
                abs(float(frame.exposure_s) - exposure) <= 1.0e-6 for exposure in light_exposures
            )
        if frame.frame_type == "flat":
            return frame.filter in light_filters
        return False

    return [frame for frame in frames if frame.frame_type in {"bias", "dark", "flat"} and compatible(frame)]


def _renumber(frames: list[FrameRecord]) -> list[FrameRecord]:
    out: list[FrameRecord] = []
    for index, frame in enumerate(frames, start=1):
        cloned = deepcopy(frame)
        original_id = cloned.id
        cloned.id = f"S{index:06d}"
        cloned.header_summary = dict(cloned.header_summary)
        cloned.header_summary["GLASS_SOURCE_ID"] = original_id
        out.append(cloned)
    return out


def build_subset_manifest(
    manifest: dict[str, Any],
    *,
    object_name: str | None = None,
    filter_name: str | None = None,
    exposure_s: float | None = None,
    light_limit: int = 2,
    bias_limit: int = 1,
    dark_limit: int = 1,
    flat_limit: int = 1,
    all_compatible_calibration: bool = False,
) -> dict[str, Any]:
    frames = [_frame_from_dict(frame) for frame in manifest.get("frames", [])]
    lights = [
        frame
        for frame in frames
        if frame.frame_type == "light"
        and _text_match(frame.object_name, object_name)
        and _text_match(frame.filter, filter_name)
        and _float_match(frame.exposure_s, exposure_s)
    ]
    lights = sorted(lights, key=lambda frame: frame.path)[: max(0, light_limit)]
    if not lights:
        raise ValueError("no light frames match the requested subset criteria")

    groups = group_frames(frames)
    group_by_id = {group.group_id: group for group in groups}
    frame_by_id = {frame.id: frame for frame in frames}
    selected_by_id: dict[str, FrameRecord] = {}
    warnings: list[str] = []

    def add_all(values: list[FrameRecord]) -> None:
        for value in values:
            selected_by_id[value.id] = value

    if all_compatible_calibration:
        add_all(_compatible_calibration_frames(frames, lights))

    for light in lights:
        bias = find_bias_group(light, groups)
        dark = find_dark_group(light, groups)
        flat = find_flat_group(light, groups)
        if bias is None:
            warnings.append(f"no matching bias group for {light.id}")
        if dark is None:
            warnings.append(f"no matching dark group for {light.id}")
        elif dark.exposure_s != light.exposure_s:
            warnings.append(
                f"dark group {dark.group_id} exposure {dark.exposure_s} differs from light {light.id} exposure {light.exposure_s}"
            )
        if flat is None:
            warnings.append(f"no matching flat group for {light.id}")
        add_all(_take_group_frames(None if bias is None else bias.group_id, group_by_id, frame_by_id, bias_limit))
        add_all(_take_group_frames(None if dark is None else dark.group_id, group_by_id, frame_by_id, dark_limit))
        add_all(_take_group_frames(None if flat is None else flat.group_id, group_by_id, frame_by_id, flat_limit))
        selected_by_id[light.id] = light

    ordered = sorted(
        selected_by_id.values(),
        key=lambda frame: ({"bias": 0, "dark": 1, "flat": 2, "light": 3}.get(frame.frame_type, 9), frame.path),
    )
    renumbered = _renumber(ordered)
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": manifest.get("root"),
        "source_manifest": manifest.get("root"),
        "subset_criteria": {
            "object_name": object_name,
            "filter": filter_name,
            "exposure_s": exposure_s,
            "light_limit": light_limit,
            "bias_limit": bias_limit,
            "dark_limit": dark_limit,
            "flat_limit": flat_limit,
            "all_compatible_calibration": all_compatible_calibration,
        },
        "frames": [to_jsonable(frame) for frame in renumbered],
        "warnings": warnings,
        "summary": summarize_frames(renumbered),
    }
