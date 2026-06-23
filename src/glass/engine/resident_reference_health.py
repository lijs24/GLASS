from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.resident_reference_scout import build_resident_reference_scout
from glass.io.json_io import read_json
from glass.models import now_iso


DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE = "auto"
DEFAULT_RESIDENT_REFERENCE_HEALTH_MIN_CPU_STAR_RATIO = 0.85
DEFAULT_RESIDENT_REFERENCE_HEALTH_MAX_CPU_RANK_FRACTION = 0.25

_SUPPORTED_ACTIONS = {"auto", "off", "warn", "fail"}


def resolve_resident_reference_health_action(
    requested_action: str,
    *,
    scout_backend: str,
) -> str:
    action = str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower()
    if action not in _SUPPORTED_ACTIONS:
        raise ValueError("resident reference health gate must be auto, off, warn, or fail")
    if action != "auto":
        return action
    return "fail" if str(scout_backend or "").lower() == "cuda" else "off"


def _selection_key(row: dict[str, Any]) -> tuple[int, float, float, float, float]:
    return (
        int(row.get("star_count") or 0),
        float(row.get("quality_score") or row.get("weight") or 0.0),
        -float(row.get("fwhm_px") if row.get("fwhm_px") is not None else 999.0),
        -float(row.get("eccentricity") if row.get("eccentricity") is not None else 1.0),
        -float(row.get("background_rms") or 0.0),
    )


def _frame_quality_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("frame_quality") if isinstance(payload.get("frame_quality"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def build_resident_reference_health(
    plan_path: str | Path,
    run_dir: str | Path,
    *,
    requested_action: str = DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE,
    min_cpu_star_ratio: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_MIN_CPU_STAR_RATIO,
    max_cpu_rank_fraction: float = DEFAULT_RESIDENT_REFERENCE_HEALTH_MAX_CPU_RANK_FRACTION,
) -> dict[str, Any]:
    if float(min_cpu_star_ratio) < 0.0:
        raise ValueError("resident reference health min CPU star ratio must be non-negative")
    if not 0.0 <= float(max_cpu_rank_fraction) <= 1.0:
        raise ValueError("resident reference health max CPU rank fraction must be in [0, 1]")

    run = Path(run_dir)
    scout_path = run / "resident_reference_scout.json"
    created_at = now_iso()
    if not scout_path.exists():
        action = resolve_resident_reference_health_action(requested_action, scout_backend="")
        passed = action == "off"
        checks = [
            {
                "name": "resident_reference_scout_present",
                "passed": passed,
                "evidence": {"path": str(scout_path), "exists": False, "action": action},
            }
        ]
        return {
            "schema_version": 1,
            "artifact_type": "resident_reference_health",
            "created_at": created_at,
            "run_dir": str(run),
            "scout_path": str(scout_path),
            "status": "disabled" if action == "off" else "failed",
            "passed": passed,
            "blocking": action == "fail" and not passed,
            "requested_action": str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower(),
            "effective_action": action,
            "checks": checks,
            "failed_checks": [item["name"] for item in checks if not item["passed"]],
            "summary": {},
        }

    scout = read_json(scout_path)
    if not isinstance(scout, dict):
        raise ValueError(f"resident reference scout is not a JSON object: {scout_path}")
    scout_backend = str(scout.get("catalog_backend") or "")
    action = resolve_resident_reference_health_action(requested_action, scout_backend=scout_backend)
    enabled = action in {"warn", "fail"}
    reference_frame_id = str(scout.get("reference_frame_id") or "")
    cpu_crosscheck = build_resident_reference_scout(
        plan_path,
        run,
        sample_stride=int(scout.get("sample_stride") or 1),
        sample_side=int(scout.get("sample_side") or 1),
        max_frames=int(scout.get("max_frames") or 0),
        threshold_sigma=float(scout.get("threshold_sigma") or 5.0),
        max_stars=int(scout.get("max_stars") or 300),
        catalog_backend="cpu",
    )
    cpu_rows = _frame_quality_rows(cpu_crosscheck)
    ranked = sorted(cpu_rows, key=_selection_key, reverse=True)
    cpu_reference_frame_id = str(cpu_crosscheck.get("reference_frame_id") or "")
    selected_cpu_row = next((row for row in ranked if str(row.get("frame_id")) == reference_frame_id), None)
    cpu_reference_row = next((row for row in ranked if str(row.get("frame_id")) == cpu_reference_frame_id), None)
    selected_rank = ranked.index(selected_cpu_row) + 1 if selected_cpu_row in ranked else None
    rank_fraction = (
        (float(selected_rank) - 1.0) / float(max(len(ranked) - 1, 1))
        if selected_rank is not None and ranked
        else None
    )
    selected_star_count = int(selected_cpu_row.get("star_count") or 0) if selected_cpu_row is not None else 0
    cpu_reference_star_count = int(cpu_reference_row.get("star_count") or 0) if cpu_reference_row is not None else 0
    star_ratio = (
        float(selected_star_count) / float(cpu_reference_star_count)
        if cpu_reference_star_count > 0
        else (1.0 if selected_star_count > 0 else 0.0)
    )

    checks = [
        {
            "name": "resident_reference_scout_present",
            "passed": True,
            "evidence": {"path": str(scout_path), "exists": True, "scout_backend": scout_backend},
        },
        {
            "name": "reference_frame_id_recorded",
            "passed": bool(reference_frame_id),
            "evidence": {"reference_frame_id": reference_frame_id},
        },
        {
            "name": "cpu_crosscheck_measured_frames",
            "passed": bool(cpu_rows),
            "evidence": {"measured_frame_count": len(cpu_rows)},
        },
        {
            "name": "selected_reference_present_in_cpu_crosscheck",
            "passed": selected_cpu_row is not None,
            "evidence": {"reference_frame_id": reference_frame_id, "present": selected_cpu_row is not None},
        },
        {
            "name": "selected_reference_cpu_star_ratio",
            "passed": not enabled or star_ratio >= float(min_cpu_star_ratio),
            "evidence": {
                "selected_cpu_star_count": selected_star_count,
                "cpu_reference_star_count": cpu_reference_star_count,
                "star_ratio": star_ratio,
                "min_cpu_star_ratio": float(min_cpu_star_ratio),
            },
        },
        {
            "name": "selected_reference_cpu_rank_fraction",
            "passed": not enabled
            or (rank_fraction is not None and rank_fraction <= float(max_cpu_rank_fraction)),
            "evidence": {
                "selected_cpu_rank": selected_rank,
                "cpu_measured_frame_count": len(ranked),
                "rank_fraction": rank_fraction,
                "max_cpu_rank_fraction": float(max_cpu_rank_fraction),
            },
        },
    ]
    raw_passed = all(item["passed"] for item in checks)
    passed = raw_passed or action == "warn"
    status = "disabled" if action == "off" else ("passed" if raw_passed else "warning" if action == "warn" else "failed")
    failed_checks = [item["name"] for item in checks if not item["passed"]]
    return {
        "schema_version": 1,
        "artifact_type": "resident_reference_health",
        "created_at": created_at,
        "run_dir": str(run),
        "scout_path": str(scout_path),
        "scout_backend": scout_backend,
        "requested_action": str(requested_action or DEFAULT_RESIDENT_REFERENCE_HEALTH_GATE).lower(),
        "effective_action": action,
        "status": status,
        "passed": passed,
        "blocking": action == "fail" and not raw_passed,
        "thresholds": {
            "min_cpu_star_ratio": float(min_cpu_star_ratio),
            "max_cpu_rank_fraction": float(max_cpu_rank_fraction),
        },
        "summary": {
            "reference_frame_id": reference_frame_id,
            "cpu_reference_frame_id": cpu_reference_frame_id,
            "selected_cpu_rank": selected_rank,
            "cpu_measured_frame_count": len(ranked),
            "selected_cpu_star_count": selected_star_count,
            "cpu_reference_star_count": cpu_reference_star_count,
            "selected_cpu_star_ratio": star_ratio,
            "selected_cpu_rank_fraction": rank_fraction,
        },
        "cpu_crosscheck": {
            "artifact_type": cpu_crosscheck.get("artifact_type"),
            "catalog_backend": cpu_crosscheck.get("catalog_backend"),
            "reference_frame_id": cpu_reference_frame_id,
            "dominant_orientation_key": cpu_crosscheck.get("dominant_orientation_key"),
            "orientation_constraint_applied": cpu_crosscheck.get("orientation_constraint_applied"),
            "measured_frame_count": len(cpu_rows),
            "top_reference_candidates": [
                {
                    "frame_id": row.get("frame_id"),
                    "star_count": row.get("star_count"),
                    "quality_score": row.get("quality_score"),
                    "fwhm_px": row.get("fwhm_px"),
                    "eccentricity": row.get("eccentricity"),
                    "background_rms": row.get("background_rms"),
                }
                for row in ranked[:10]
            ],
        },
        "checks": checks,
        "failed_checks": failed_checks,
        "recommended_actions": [
            "use the default CPU resident reference scout",
            "choose an explicit --reference-frame-id that passes CPU cross-check",
            "keep --resident-reference-health-gate warn/off only for diagnostic CUDA scout experiments",
        ],
        "clean_room_note": (
            "Project-defined cross-check over GLASS raw-light scout artifacts and GLASS CPU star metrics; "
            "it does not inspect external implementation source."
        ),
    }
