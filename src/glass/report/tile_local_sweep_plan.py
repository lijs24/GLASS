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


def _read_command_template(path: str | Path | None) -> list[str] | None:
    if path is None:
        return None
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"base run command is empty: {path}")
    return _tokenize_command(text)


def _replace_option(tokens: list[str], option: str, value: str | Path) -> list[str]:
    updated = list(tokens)
    try:
        index = updated.index(option)
    except ValueError as exc:
        raise ValueError(f"base run command is missing required option {option}") from exc
    if index + 1 >= len(updated):
        raise ValueError(f"base run command option {option} is missing a value")
    updated[index + 1] = str(value)
    return updated


def _append_option(tokens: list[str | Path | int | float], option: str, value: str | Path | int | float | None) -> None:
    if value is not None:
        tokens.extend([option, value])


def _replay_tile_count(replay: str | Path) -> int:
    payload = read_json(replay)
    if not isinstance(payload, dict) or payload.get("artifact_type") != "tile_local_policy_replay":
        raise ValueError("replay must be a tile_local_policy_replay artifact")
    tiles = payload.get("tiles")
    if not isinstance(tiles, list) or not tiles:
        raise ValueError("replay must contain at least one tile")
    return len(tiles)


def _candidate_id(prefix: str, strategy: str, max_tiles: int) -> str:
    clean_strategy = "".join(ch if ch.isalnum() else "_" for ch in strategy).strip("_")
    clean_prefix = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in prefix).strip("_")
    return f"{clean_prefix}_{clean_strategy}_tiles{max_tiles}"


def build_tile_local_sweep_plan(
    replay: str | Path,
    *,
    root: str | Path,
    max_tiles: list[int],
    strategy: str = "canonical_delta_abs",
    candidate_prefix: str = "tile_local",
    base_run_command: str | Path | None = None,
    reference: str | Path | None = None,
    baseline_run: str | Path | None = None,
    baseline_master: str | Path | None = None,
    baseline_compare_json: str | Path | None = None,
    wbpp_result: str | Path | None = None,
    benchmark_contract: str | Path | None = None,
    manifest: str | Path | None = None,
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    min_coverage: float | None = None,
    existing_decisions: list[str | Path] | None = None,
) -> dict[str, Any]:
    if not max_tiles:
        raise ValueError("at least one max_tiles value is required")
    tile_count = _replay_tile_count(replay)
    planned_tile_counts = sorted({count for count in (int(value) for value in max_tiles) if count > 0})
    if not planned_tile_counts:
        raise ValueError("max_tiles values must be positive")
    for count in planned_tile_counts:
        if count > tile_count:
            raise ValueError(f"max_tiles {count} exceeds replay tile count {tile_count}")

    root_path = Path(root)
    template_tokens = _read_command_template(base_run_command)
    candidates: list[dict[str, Any]] = []
    for count in planned_tile_counts:
        cid = _candidate_id(candidate_prefix, strategy, count)
        replay_path = root_path / "replays" / f"{cid}.json"
        replay_md = root_path / "replays" / f"{cid}.md"
        run_dir = root_path / "runs" / cid
        master = run_dir / "integration" / "resident_master_H.fits"
        coverage = run_dir / "integration" / "resident_coverage_map_H.fits"
        compare_reference_html = run_dir / f"compare_vs_reference_scaled_coverage{int(min_coverage or 0)}.html"
        compare_reference_json = compare_reference_html.with_suffix(".json")
        compare_baseline_html = run_dir / f"compare_vs_baseline_coverage{int(min_coverage or 0)}.html"
        compare_baseline_json = compare_baseline_html.with_suffix(".json")
        verification = root_path / "verification" / f"{cid}_verify.json"
        verification_md = root_path / "verification" / f"{cid}_verify.md"
        decision = root_path / "decisions" / f"{cid}_decision.json"
        decision_md = root_path / "decisions" / f"{cid}_decision.md"
        apply_experiment = run_dir / "tile_local_apply_experiment.json"
        apply_experiment_md = run_dir / "tile_local_apply_experiment.md"
        acceptance = run_dir / "acceptance_audit.json"
        acceptance_md = run_dir / "acceptance_audit.md"

        commands: dict[str, str] = {
            "subset": _command(
                [
                    "glass",
                    "tile-local-policy-subset",
                    "--replay",
                    replay,
                    "--out",
                    replay_path,
                    "--markdown",
                    replay_md,
                    "--strategy",
                    strategy,
                    "--max-tiles",
                    count,
                ]
            )
        }
        if template_tokens is not None:
            run_tokens = _replace_option(template_tokens, "--out", run_dir)
            run_tokens = _replace_option(run_tokens, "--resident-tile-local-policy-replay", replay_path)
            commands["run"] = _command(run_tokens)
        if reference is not None:
            compare_reference_tokens: list[str | Path | int | float] = [
                "glass",
                "compare",
                "--glass",
                master,
                "--reference",
                reference,
                "--out",
                compare_reference_html,
            ]
            _append_option(compare_reference_tokens, "--glass-scale", glass_scale)
            _append_option(compare_reference_tokens, "--glass-offset", glass_offset)
            _append_option(compare_reference_tokens, "--glass-coverage-map", coverage)
            _append_option(compare_reference_tokens, "--min-coverage", min_coverage)
            commands["compare_reference"] = _command(compare_reference_tokens)
        if baseline_master is not None:
            compare_baseline_tokens: list[str | Path | int | float] = [
                "glass",
                "compare",
                "--glass",
                master,
                "--reference",
                baseline_master,
                "--out",
                compare_baseline_html,
            ]
            _append_option(compare_baseline_tokens, "--glass-coverage-map", coverage)
            _append_option(compare_baseline_tokens, "--min-coverage", min_coverage)
            commands["compare_baseline"] = _command(compare_baseline_tokens)
        if baseline_run is not None and benchmark_contract is not None:
            apply_tokens: list[str | Path | int | float] = [
                "glass",
                "tile-local-apply-experiment",
                "--baseline-run",
                baseline_run,
                "--candidate-run",
                run_dir,
                "--replay",
                replay_path,
                "--benchmark-contract",
                benchmark_contract,
            ]
            _append_option(apply_tokens, "--baseline-compare-json", baseline_compare_json)
            _append_option(
                apply_tokens,
                "--candidate-compare-json",
                compare_reference_json if reference is not None else None,
            )
            _append_option(
                apply_tokens,
                "--candidate-vs-baseline-json",
                compare_baseline_json if baseline_master is not None else None,
            )
            apply_tokens.extend(["--out", apply_experiment, "--markdown", apply_experiment_md, "--fail-on-failed"])
            commands["apply_experiment"] = _command(apply_tokens)
        if manifest is not None and wbpp_result is not None and benchmark_contract is not None and reference is not None:
            commands["acceptance_audit"] = _command(
                [
                    "glass",
                    "acceptance-audit",
                    "--manifest",
                    manifest,
                    "--glass-run",
                    run_dir,
                    "--wbpp-result",
                    wbpp_result,
                    "--compare-json",
                    compare_reference_json,
                    "--out",
                    acceptance,
                    "--markdown",
                    acceptance_md,
                    "--benchmark-contract",
                    benchmark_contract,
                ]
            )
        if baseline_master is not None and reference is not None:
            verify_tokens: list[str | Path | int | float] = [
                "glass",
                "tile-local-apply-verify",
                "--baseline",
                baseline_master,
                "--candidate",
                master,
                "--reference",
                reference,
                "--replay",
                replay_path,
            ]
            _append_option(verify_tokens, "--coverage-map", coverage)
            _append_option(verify_tokens, "--min-coverage", min_coverage)
            _append_option(verify_tokens, "--glass-scale", glass_scale)
            _append_option(verify_tokens, "--glass-offset", glass_offset)
            verify_tokens.extend(["--out", verification, "--markdown", verification_md, "--fail-on-failed"])
            commands["verify"] = _command(verify_tokens)
        commands["decision"] = _command(
            [
                "glass",
                "tile-local-policy-decision",
                "--verification",
                verification,
                "--apply-experiment",
                apply_experiment,
                "--acceptance-audit",
                acceptance,
                "--out",
                decision,
                "--markdown",
                decision_md,
                "--fail-on-rejected",
            ]
        )
        candidates.append(
            {
                "candidate_id": cid,
                "strategy": strategy,
                "max_tiles": count,
                "subset_replay": str(replay_path),
                "run_dir": str(run_dir),
                "verification": str(verification),
                "decision": str(decision),
                "commands": commands,
            }
        )

    decision_inputs = [str(path) for path in (existing_decisions or [])]
    decision_inputs.extend(row["decision"] for row in candidates)
    sweep_command_tokens: list[str | Path] = ["glass", "tile-local-policy-sweep"]
    for decision in decision_inputs:
        sweep_command_tokens.extend(["--decision", decision])
    sweep_json = root_path / "policy_sweep.json"
    sweep_md = root_path / "policy_sweep.md"
    sweep_command_tokens.extend(["--out", sweep_json, "--markdown", sweep_md, "--fail-on-no-accepted"])
    return {
        "schema_version": 1,
        "artifact_type": "tile_local_sweep_plan",
        "created_at": now_iso(),
        "source_replay": str(replay),
        "source_tile_count": tile_count,
        "root": str(root_path),
        "strategy": strategy,
        "candidate_count": len(candidates),
        "existing_decisions": decision_inputs[: len(existing_decisions or [])],
        "planned_decisions": [row["decision"] for row in candidates],
        "final_sweep": {
            "out": str(sweep_json),
            "markdown": str(sweep_md),
            "command": _command(sweep_command_tokens),
        },
        "candidates": candidates,
        "limitations": [
            "This artifact plans commands for measured tile-local policy sweeps.",
            "It does not execute image processing and does not promote any policy by default.",
        ],
    }


def write_tile_local_sweep_plan(
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
        "# Tile-Local Sweep Plan",
        "",
        f"- Source replay: `{payload.get('source_replay')}`",
        f"- Source tile count: `{payload.get('source_tile_count')}`",
        f"- Strategy: `{payload.get('strategy')}`",
        f"- Candidate count: `{payload.get('candidate_count')}`",
        f"- Final sweep: `{(payload.get('final_sweep') or {}).get('out')}`",
        "",
        "| candidate | max tiles | replay | run | decision |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in payload.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {candidate} | {tiles} | {replay} | {run} | {decision} |".format(
                candidate=row.get("candidate_id"),
                tiles=row.get("max_tiles"),
                replay=row.get("subset_replay"),
                run=row.get("run_dir"),
                decision=row.get("decision"),
            )
        )
    lines.extend(["", "## Commands", ""])
    for row in payload.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        lines.append(f"### {row.get('candidate_id')}")
        lines.append("")
        commands = row.get("commands") if isinstance(row.get("commands"), dict) else {}
        for name, command in commands.items():
            lines.append(f"- `{name}`")
            lines.append("")
            lines.append("```powershell")
            lines.append(str(command))
            lines.append("```")
            lines.append("")
    lines.append("## Final Sweep")
    lines.append("")
    lines.append("```powershell")
    lines.append(str((payload.get("final_sweep") or {}).get("command")))
    lines.append("```")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
