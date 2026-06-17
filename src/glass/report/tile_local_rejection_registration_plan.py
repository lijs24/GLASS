from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _tokenize_command(command: str) -> list[str]:
    return [part.strip('"') for part in shlex.split(command, posix=False)]


def _command(tokens: list[str | Path | int | float]) -> str:
    return subprocess.list2cmdline([str(token) for token in tokens])


def _read_command_template(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"base run command is empty: {path}")
    return _tokenize_command(text)


def _set_option(tokens: list[str], option: str, value: str | Path | int | float) -> list[str]:
    updated = list(tokens)
    try:
        index = updated.index(option)
    except ValueError:
        updated.extend([option, str(value)])
        return updated
    if index + 1 >= len(updated):
        raise ValueError(f"base run command option {option} is missing a value")
    updated[index + 1] = str(value)
    return updated


def _append_repeated_option(tokens: list[str], option: str, values: list[str]) -> list[str]:
    updated = list(tokens)
    for value in values:
        updated.extend([option, str(value)])
    return updated


def _top_hotspot_frames(audit: dict[str, Any], *, count: int) -> list[str]:
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    frames = summary.get("top_high_rejection_frames")
    if not isinstance(frames, list):
        return []
    selected: list[str] = []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        if not frame.get("in_top_frame_family") and not frame.get("in_focus_group"):
            continue
        frame_id = frame.get("frame_id")
        if frame_id is None:
            continue
        selected.append(str(frame_id))
        if count > 0 and len(selected) >= count:
            break
    return selected


def _candidate_run_command(
    template: list[str],
    *,
    run_dir: Path,
    options: dict[str, str | int | float],
    exclude_frames: list[str] | None = None,
) -> str:
    tokens = _set_option(template, "--out", run_dir)
    for option, value in options.items():
        tokens = _set_option(tokens, option, value)
    if exclude_frames:
        tokens = _append_repeated_option(tokens, "--exclude-frame-id", exclude_frames)
    return _command(tokens)


def _compare_command(
    *,
    master: Path,
    reference: str | Path,
    out: Path,
    coverage: Path,
    glass_scale: float | None,
    glass_offset: float | None,
    min_coverage: float | None,
) -> str:
    tokens: list[str | Path | int | float] = ["glass", "compare", "--glass", master, "--reference", reference, "--out", out]
    if glass_scale is not None:
        tokens.extend(["--glass-scale", glass_scale])
    if glass_offset is not None:
        tokens.extend(["--glass-offset", glass_offset])
    if min_coverage is not None:
        tokens.extend(["--glass-coverage-map", coverage, "--min-coverage", min_coverage])
    return _command(tokens)


def _acceptance_command(
    *,
    manifest: str | Path,
    glass_run: Path,
    wbpp_result: str | Path,
    compare_json: Path,
    out: Path,
    benchmark_contract: str | Path | None,
) -> str:
    tokens: list[str | Path | int | float] = [
        "glass",
        "acceptance-audit",
        "--manifest",
        manifest,
        "--glass-run",
        glass_run,
        "--wbpp-result",
        wbpp_result,
        "--compare-json",
        compare_json,
        "--out",
        out,
    ]
    if benchmark_contract is not None:
        tokens.extend(["--benchmark-contract", benchmark_contract])
    return _command(tokens)


def build_tile_local_rejection_registration_plan(
    audit: str | Path,
    *,
    root: str | Path,
    base_run_command: str | Path,
    reference: str | Path | None = None,
    manifest: str | Path | None = None,
    wbpp_result: str | Path | None = None,
    benchmark_contract: str | Path | None = None,
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    min_coverage: float | None = None,
    soft_agreement_score: float = 0.6,
    strict_agreement_score: float = 0.9,
    exclude_top_count: int = 6,
) -> dict[str, Any]:
    if soft_agreement_score < 0.0 or strict_agreement_score < 0.0:
        raise ValueError("agreement scores must be non-negative")
    if exclude_top_count < 0:
        raise ValueError("exclude_top_count must be non-negative")
    audit_payload = read_json(audit)
    if audit_payload.get("artifact_type") != "tile_local_rejection_registration_audit":
        raise ValueError("audit must be a tile_local_rejection_registration_audit artifact")
    root_path = Path(root)
    template = _read_command_template(base_run_command)
    hotspot_frames = _top_hotspot_frames(audit_payload, count=exclude_top_count)

    candidate_specs: list[dict[str, Any]] = [
        {
            "candidate_id": "agreement_flag_only",
            "purpose": "record low-agreement frames without agreement downweighting",
            "options": {"--resident-triangle-agreement-action": "flag"},
            "exclude_frames": [],
        },
        {
            "candidate_id": "agreement_soft_downweight",
            "purpose": "reduce downweight strength for low-agreement frames by lowering the threshold",
            "options": {
                "--resident-triangle-agreement-action": "downweight",
                "--resident-triangle-min-agreement-score": soft_agreement_score,
            },
            "exclude_frames": [],
        },
        {
            "candidate_id": "agreement_strict_downweight",
            "purpose": "increase downweight strength for low-agreement frames by raising the threshold",
            "options": {
                "--resident-triangle-agreement-action": "downweight",
                "--resident-triangle-min-agreement-score": strict_agreement_score,
            },
            "exclude_frames": [],
        },
    ]
    if hotspot_frames:
        candidate_specs.append(
            {
                "candidate_id": f"exclude_top{len(hotspot_frames)}_hotspot_frames",
                "purpose": "remove the highest-rejection focus/top-family frames to isolate their contribution",
                "options": {},
                "exclude_frames": hotspot_frames,
            }
        )

    candidates: list[dict[str, Any]] = []
    for spec in candidate_specs:
        candidate_id = str(spec["candidate_id"])
        run_dir = root_path / "runs" / candidate_id
        master = run_dir / "integration" / "resident_master_H.fits"
        coverage = run_dir / "integration" / "resident_coverage_map_H.fits"
        commands: dict[str, str] = {
            "run": _candidate_run_command(
                template,
                run_dir=run_dir,
                options=spec.get("options") or {},
                exclude_frames=spec.get("exclude_frames") or [],
            )
        }
        compare_json = None
        if reference is not None:
            compare_html = root_path / "compare" / f"{candidate_id}_vs_reference.html"
            compare_json = compare_html.with_suffix(".json")
            commands["compare_reference"] = _compare_command(
                master=master,
                reference=reference,
                out=compare_html,
                coverage=coverage,
                glass_scale=glass_scale,
                glass_offset=glass_offset,
                min_coverage=min_coverage,
            )
        if manifest is not None and wbpp_result is not None and compare_json is not None:
            acceptance = root_path / "acceptance" / f"{candidate_id}_acceptance.json"
            commands["acceptance_audit"] = _acceptance_command(
                manifest=manifest,
                glass_run=run_dir,
                wbpp_result=wbpp_result,
                compare_json=compare_json,
                out=acceptance,
                benchmark_contract=benchmark_contract,
            )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "purpose": spec.get("purpose"),
                "run_dir": str(run_dir),
                "changed_options": spec.get("options") or {},
                "exclude_frames": spec.get("exclude_frames") or [],
                "commands": commands,
            }
        )

    summary = audit_payload.get("summary") if isinstance(audit_payload.get("summary"), dict) else {}
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_rejection_registration_plan",
        "created_at": now_iso(),
        "audit": str(audit),
        "root": str(root_path),
        "base_run_command": str(base_run_command),
        "source_recommendation": summary.get("recommendation"),
        "source_focus_minus_control_high_rejection": summary.get(
            "focus_minus_control_high_rejected_fraction_mean"
        ),
        "hotspot_frames": hotspot_frames,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "recommendation": "run_soft_downweight_then_exclude_hotspot_control",
        "acceptance_notes": [
            "Run candidates one at a time and compare against the same reference and baseline contracts.",
            "Do not promote any candidate unless full-frame agreement, DQ maps, frame accounting, and runtime pass.",
            "The exclude-hotspot candidate is a diagnostic control, not a production policy proposal.",
        ],
    }


def write_tile_local_rejection_registration_plan(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is None:
        return
    target = Path(markdown)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tile-Local Rejection/Registration Experiment Plan",
        "",
        f"- Audit: `{payload.get('audit')}`",
        f"- Source recommendation: `{payload.get('source_recommendation')}`",
        f"- Hotspot frames: `{', '.join(payload.get('hotspot_frames') or [])}`",
        f"- Candidate count: `{payload.get('candidate_count')}`",
        "",
        "| candidate | purpose | excludes |",
        "| --- | --- | --- |",
    ]
    for candidate in payload.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        lines.append(
            "| {candidate} | {purpose} | {excludes} |".format(
                candidate=candidate.get("candidate_id"),
                purpose=candidate.get("purpose"),
                excludes=", ".join(candidate.get("exclude_frames") or []),
            )
        )
    lines.extend(["", "## Commands", ""])
    for candidate in payload.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        lines.append(f"### {candidate.get('candidate_id')}")
        lines.append("")
        commands = candidate.get("commands") if isinstance(candidate.get("commands"), dict) else {}
        for name, command in commands.items():
            lines.append(f"- `{name}`")
            lines.append("")
            lines.append("```powershell")
            lines.append(str(command))
            lines.append("```")
            lines.append("")
    lines.extend(["## Acceptance Notes", ""])
    for note in payload.get("acceptance_notes", []):
        lines.append(f"- {note}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
