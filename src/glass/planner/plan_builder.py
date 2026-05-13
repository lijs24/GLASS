from __future__ import annotations

from pathlib import Path

from glass.models import (
    CalibrationPlan,
    CalibrationPolicy,
    FrameRecord,
    IntegrationPolicy,
    LightPlan,
    LocalNormalizationPolicy,
    ProcessingPlan,
    RegistrationPolicy,
    now_iso,
)
from glass.planner.diagnostics import metadata_warnings
from glass.planner.grouping import group_frames
from glass.planner.matching import find_bias_group, find_dark_group, find_flat_group


def _frame_from_dict(value: dict[str, object]) -> FrameRecord:
    return FrameRecord(**value)  # type: ignore[arg-type]


def build_processing_plan(manifest: dict[str, object], manifest_path: str | Path) -> ProcessingPlan:
    frames = [_frame_from_dict(frame) for frame in manifest.get("frames", [])]  # type: ignore[arg-type]
    groups = group_frames(frames)
    policy = CalibrationPolicy()
    calibration_plan = CalibrationPlan(
        master_bias_groups=[g.group_id for g in groups if g.group_type == "bias"],
        master_dark_groups=[g.group_id for g in groups if g.group_type == "dark"],
        master_flat_groups=[g.group_id for g in groups if g.group_type == "flat"],
        calibration_policy=policy,
        bias_dark_semantics_warning=(
            "Default policy treats master dark frames as including bias; override in later gates "
            "when darks are bias-subtracted."
        ),
    )
    light_plans: list[LightPlan] = []
    for light in [f for f in frames if f.frame_type == "light"]:
        bias = find_bias_group(light, groups)
        dark = find_dark_group(light, groups)
        flat = find_flat_group(light, groups)
        warnings: list[str] = []
        if dark is None:
            warnings.append("no matching dark group")
        if flat is None:
            warnings.append("no matching flat group")
        if bias is None:
            warnings.append("no matching bias group; allowed only if dark-includes-bias semantics hold")
        status = "ready" if dark is not None and flat is not None else "blocked"
        light_plans.append(
            LightPlan(
                filter=light.filter,
                frames=[light.id],
                matching_bias_group=bias.group_id if bias else None,
                matching_dark_group=dark.group_id if dark else None,
                matching_flat_group=flat.group_id if flat else None,
                calibration_status=status,
                warnings=warnings,
            )
        )
    global_warnings = metadata_warnings(frames)
    if not light_plans:
        global_warnings.append("no light frames found")
    executable = bool(light_plans) and all(lp.calibration_status == "ready" for lp in light_plans)
    next_steps = ["run calibration"] if executable else ["add or relabel missing calibration frames"]
    return ProcessingPlan(
        project_id="glass-project",
        created_at=now_iso(),
        manifest_path=str(manifest_path),
        frames=frames,
        groups=groups,
        calibration_plan=calibration_plan,
        registration_policy=RegistrationPolicy(),
        local_normalization_policy=LocalNormalizationPolicy(),
        integration_policy=IntegrationPolicy(),
        light_plans=light_plans,
        global_warnings=global_warnings,
        executable=executable,
        next_steps=next_steps,
    )

