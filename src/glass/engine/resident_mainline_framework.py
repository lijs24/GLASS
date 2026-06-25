from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import write_json
from glass.report.phase2_mainline_audit import build_phase2_mainline_audit


DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE = "warn"


def build_resident_mainline_framework(
    run: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE,
    min_lights: int = 1,
    min_active_frames: int = 1,
    max_masked_frames: int = 1_000_000,
) -> dict[str, Any]:
    """Build a resident-run postcondition summary from the already written artifacts."""

    action = str(requested_action or DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE)
    if action not in {"off", "warn", "strict"}:
        raise ValueError("requested_action must be off, warn, or strict")
    audit = build_phase2_mainline_audit(
        run,
        min_lights=max(0, int(min_lights)),
        min_active_frames=max(0, int(min_active_frames)),
        max_masked_frames=max(0, int(max_masked_frames)),
        require_acceptance=False,
        require_compare=False,
    )
    passed = bool(audit.get("passed"))
    return {
        **audit,
        "artifact_type": "resident_mainline_framework",
        "source_artifact_type": audit.get("artifact_type"),
        "scope": "resident_run_postcondition",
        "policy": {
            "requested_action": action,
            "blocking": bool(action == "strict" and not passed),
            "min_lights": max(0, int(min_lights)),
            "min_active_frames": max(0, int(min_active_frames)),
            "max_masked_frames": max(0, int(max_masked_frames)),
            "acceptance_required": False,
            "compare_required": False,
        },
        "status": "passed" if passed else "failed",
        "passed": passed,
        "blocking": bool(action == "strict" and not passed),
    }


def write_resident_mainline_framework(
    run: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_MAINLINE_FRAMEWORK_GATE,
    min_lights: int = 1,
    min_active_frames: int = 1,
    max_masked_frames: int = 1_000_000,
    path: str | Path | None = None,
) -> Path:
    run_path = Path(run)
    out = Path(path) if path is not None else run_path / "resident_mainline_framework.json"
    payload = build_resident_mainline_framework(
        run_path,
        requested_action=requested_action,
        min_lights=min_lights,
        min_active_frames=min_active_frames,
        max_masked_frames=max_masked_frames,
    )
    write_json(out, payload)
    return out
