from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _path_match_keys(path: str | Path, *, root: Path | None = None) -> set[str]:
    raw = Path(str(path))
    candidates = [raw]
    if root is not None and not raw.is_absolute():
        candidates.append(root / raw)
    keys: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate).replace("\\", "/").lower()
        keys.add(normalized)
        keys.add(candidate.name.lower())
        keys.add(candidate.stem.lower())
        parts = [part.lower() for part in candidate.parts]
        for tail_len in (2, 3, 4):
            if len(parts) >= tail_len:
                keys.add("/".join(parts[-tail_len:]))
        try:
            keys.add(str(candidate.resolve(strict=False)).replace("\\", "/").lower())
        except OSError:
            pass
    return keys


def _resolve_sidecar_path(raw_path: object, source_manifest_root: Path) -> str:
    sidecar = Path(str(raw_path))
    if not sidecar.is_absolute():
        sidecar = source_manifest_root / sidecar
    return str(sidecar.resolve(strict=False))


def bind_source_dq_manifest_to_plan(
    plan: ProcessingPlan,
    source_dq_manifest: dict[str, Any],
    source_dq_manifest_path: str | Path,
) -> dict[str, Any]:
    source_manifest_root = Path(source_dq_manifest_path).parent
    frame_keys: dict[str, list[FrameRecord]] = {}
    frame_by_id = {frame.id: frame for frame in plan.frames if frame.frame_type == "light"}
    for frame in plan.frames:
        if frame.frame_type != "light":
            continue
        for key in _path_match_keys(frame.path):
            frame_keys.setdefault(key, []).append(frame)

    bindings = source_dq_manifest.get("bindings") or source_dq_manifest.get("source_dq_bindings") or []
    rows: list[dict[str, Any]] = []
    applied_count = 0
    unmatched_count = 0
    ambiguous_count = 0
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            unmatched_count += 1
            rows.append({"index": index, "status": "skipped", "reason": "binding_not_object"})
            continue
        dq_mask_path = binding.get("dq_mask_path") or binding.get("source_dq_mask_path") or binding.get("path")
        if not dq_mask_path:
            unmatched_count += 1
            rows.append({"index": index, "status": "skipped", "reason": "missing_dq_mask_path"})
            continue
        matches: list[FrameRecord] = []
        frame_id = binding.get("frame_id")
        if frame_id is not None and str(frame_id) in frame_by_id:
            matches = [frame_by_id[str(frame_id)]]
        frame_path = binding.get("frame_path") or binding.get("light_path") or binding.get("path")
        if not matches and frame_path:
            seen: set[str] = set()
            for key in _path_match_keys(str(frame_path), root=source_manifest_root):
                for frame in frame_keys.get(key, []):
                    if frame.id not in seen:
                        matches.append(frame)
                        seen.add(frame.id)
        if not matches:
            unmatched_count += 1
            rows.append(
                {
                    "index": index,
                    "status": "unmatched",
                    "frame_id": frame_id,
                    "frame_path": frame_path,
                    "dq_mask_path": dq_mask_path,
                }
            )
            continue
        if len(matches) > 1:
            ambiguous_count += 1
            rows.append(
                {
                    "index": index,
                    "status": "ambiguous",
                    "frame_id": frame_id,
                    "frame_path": frame_path,
                    "matches": [frame.id for frame in matches],
                    "dq_mask_path": dq_mask_path,
                }
            )
            continue
        frame = matches[0]
        frame.source_dq_mask_path = _resolve_sidecar_path(dq_mask_path, source_manifest_root)
        applied_count += 1
        rows.append(
            {
                "index": index,
                "status": "bound",
                "frame_id": frame.id,
                "frame_path": frame.path,
                "dq_mask_path": frame.source_dq_mask_path,
            }
        )

    summary = {
        "schema_version": 1,
        "artifact_type": "source_dq_plan_binding_summary",
        "source_manifest_path": str(source_dq_manifest_path),
        "binding_count": len(bindings),
        "applied_count": applied_count,
        "unmatched_count": unmatched_count,
        "ambiguous_count": ambiguous_count,
        "rows": rows,
    }
    if unmatched_count or ambiguous_count:
        plan.global_warnings.append(
            "source-DQ manifest binding incomplete: "
            f"{applied_count} bound, {unmatched_count} unmatched, {ambiguous_count} ambiguous"
        )
    return summary


def build_processing_plan(
    manifest: dict[str, object],
    manifest_path: str | Path,
    *,
    source_dq_manifest: dict[str, Any] | None = None,
    source_dq_manifest_path: str | Path | None = None,
) -> ProcessingPlan:
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
    plan = ProcessingPlan(
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
    if source_dq_manifest is not None:
        bind_source_dq_manifest_to_plan(
            plan,
            source_dq_manifest,
            source_dq_manifest_path or manifest_path,
        )
    return plan
