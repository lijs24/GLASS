from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


DEFAULT_RUNTIME_VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "retry_settings_control",
        "purpose": "rerun the accepted candidate settings as a warm control",
        "options": {},
    },
    {
        "variant_id": "prefetch12_workers6",
        "purpose": "reduce host decode concurrency to test whether retry slowdown was I/O contention",
        "options": {
            "--resident-prefetch-frames": 12,
            "--resident-prefetch-workers": 6,
        },
    },
    {
        "variant_id": "prefetch20_workers8",
        "purpose": "increase resident prefetch depth while keeping worker count fixed",
        "options": {
            "--resident-prefetch-frames": 20,
            "--resident-prefetch-workers": 8,
        },
    },
    {
        "variant_id": "batch16_wave4",
        "purpose": "increase calibration batch and wave size to reduce launch/orchestration overhead",
        "options": {
            "--resident-calibration-batch-frames": 16,
            "--resident-calibration-wave-frames": 4,
        },
    },
    {
        "variant_id": "streams2_batch8",
        "purpose": "reduce calibration stream fanout to test synchronization overhead",
        "options": {
            "--resident-calibration-streams": 2,
            "--resident-calibration-batch-frames": 8,
        },
    },
]


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


def _option_value(tokens: list[str], option: str) -> str | None:
    try:
        index = tokens.index(option)
    except ValueError:
        return None
    if index + 1 >= len(tokens):
        return None
    return tokens[index + 1]


def _selected_variants(variant_ids: list[str] | None) -> list[dict[str, Any]]:
    if not variant_ids:
        return [dict(item) for item in DEFAULT_RUNTIME_VARIANTS]
    by_id = {str(item["variant_id"]): item for item in DEFAULT_RUNTIME_VARIANTS}
    selected: list[dict[str, Any]] = []
    for variant_id in variant_ids:
        if variant_id not in by_id:
            raise ValueError(f"unknown runtime sweep variant: {variant_id}")
        selected.append(dict(by_id[variant_id]))
    return selected


def _prefetch_matrix_variants(prefetch_frames: list[int], prefetch_workers: list[int]) -> list[dict[str, Any]]:
    if not prefetch_frames or not prefetch_workers:
        return []
    variants: list[dict[str, Any]] = []
    seen: set[str] = set()
    for frames in prefetch_frames:
        if frames <= 0:
            raise ValueError("prefetch frame counts must be positive")
        for workers in prefetch_workers:
            if workers <= 0:
                raise ValueError("prefetch worker counts must be positive")
            variant_id = f"prefetch{frames}_workers{workers}"
            if variant_id in seen:
                continue
            seen.add(variant_id)
            variants.append(
                {
                    "variant_id": variant_id,
                    "purpose": "runtime confirmation sweep over resident prefetch depth and worker count",
                    "options": {
                        "--resident-prefetch-frames": int(frames),
                        "--resident-prefetch-workers": int(workers),
                    },
                }
            )
    return variants


def _runtime_variants(
    variant_ids: list[str] | None,
    *,
    prefetch_frames: list[int] | None,
    prefetch_workers: list[int] | None,
) -> list[dict[str, Any]]:
    matrix_requested = bool(prefetch_frames or prefetch_workers)
    if matrix_requested and not (prefetch_frames and prefetch_workers):
        raise ValueError("prefetch matrix requires at least one frame count and one worker count")
    selected = _selected_variants(variant_ids) if variant_ids else []
    selected.extend(_prefetch_matrix_variants(prefetch_frames or [], prefetch_workers or []))
    if selected:
        return selected
    return _selected_variants(None)


def _read_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _run_master_paths(run_dir: Path) -> tuple[Path, Path]:
    integration = run_dir / "integration"
    return integration / "resident_master_H.fits", integration / "resident_coverage_map_H.fits"


def _baseline_master_paths(baseline_run: str | Path) -> tuple[Path, Path]:
    root = Path(baseline_run)
    resident_path = root / "resident_artifacts.json"
    if resident_path.exists():
        payload = _read_object(resident_path)
        artifacts = payload.get("artifacts")
        if isinstance(artifacts, list) and artifacts and isinstance(artifacts[0], dict):
            master = artifacts[0].get("master_path")
            coverage = artifacts[0].get("coverage_map_path")
            if master and coverage:
                master_path = Path(str(master))
                coverage_path = Path(str(coverage))
                if not master_path.is_absolute():
                    master_path = root / master_path
                if not coverage_path.is_absolute():
                    coverage_path = root / coverage_path
                return master_path, coverage_path
    return _run_master_paths(root)


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


def _pipeline_contract_command(*, glass_run: Path, out: Path, markdown: Path) -> str:
    return _command(
        [
            "glass",
            "pipeline-contract",
            "--run",
            glass_run,
            "--out",
            out,
            "--markdown",
            markdown,
        ]
    )


def _acceptance_command(
    *,
    manifest: str | Path,
    glass_run: Path,
    wbpp_result: str | Path,
    compare_json: Path,
    out: Path,
    benchmark_contract: str | Path | None,
    pipeline_contract_json: str | Path | None,
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
    if pipeline_contract_json is not None:
        tokens.extend(["--pipeline-contract-json", pipeline_contract_json])
    return _command(tokens)


def _candidate_comparison_command(
    *,
    baseline_run: str | Path,
    candidate_run: Path,
    candidate_id: str,
    baseline_compare_json: str | Path,
    candidate_compare_json: Path,
    candidate_vs_baseline_json: Path,
    candidate_acceptance_json: Path,
    min_speedup_vs_reference: float | None,
    out: Path,
    markdown: Path,
) -> str:
    tokens: list[str | Path | int | float] = [
        "glass",
        "candidate-comparison",
        "--baseline-run",
        baseline_run,
        "--candidate-run",
        candidate_run,
        "--candidate-id",
        candidate_id,
        "--baseline-compare-json",
        baseline_compare_json,
        "--candidate-compare-json",
        candidate_compare_json,
        "--candidate-vs-baseline-json",
        candidate_vs_baseline_json,
        "--candidate-acceptance-json",
        candidate_acceptance_json,
        "--out",
        out,
        "--markdown",
        markdown,
    ]
    if min_speedup_vs_reference is not None:
        tokens.extend(["--min-speedup-vs-reference", min_speedup_vs_reference])
    return _command(tokens)


def build_candidate_runtime_sweep_plan(
    comparison: str | Path,
    *,
    root: str | Path,
    base_run_command: str | Path,
    baseline_run: str | Path,
    baseline_compare_json: str | Path,
    reference: str | Path,
    manifest: str | Path,
    wbpp_result: str | Path,
    benchmark_contract: str | Path | None = None,
    glass_scale: float | None = None,
    glass_offset: float | None = None,
    min_coverage: float | None = None,
    min_speedup_vs_reference: float | None = None,
    variants: list[str] | None = None,
    prefetch_frames: list[int] | None = None,
    prefetch_workers: list[int] | None = None,
) -> dict[str, Any]:
    comparison_payload = _read_object(comparison)
    if comparison_payload.get("artifact_type") != "candidate_comparison":
        raise ValueError("comparison must be a candidate_comparison artifact")
    root_path = Path(root)
    template = _read_command_template(base_run_command)
    selected = _runtime_variants(variants, prefetch_frames=prefetch_frames, prefetch_workers=prefetch_workers)
    baseline_master, _baseline_coverage = _baseline_master_paths(baseline_run)

    planned: list[dict[str, Any]] = []
    for spec in selected:
        variant_id = str(spec["variant_id"])
        run_dir = root_path / "runs" / variant_id
        master, coverage = _run_master_paths(run_dir)
        compare_reference_html = root_path / "compare" / f"{variant_id}_vs_reference.html"
        compare_baseline_html = root_path / "compare" / f"{variant_id}_vs_baseline.html"
        pipeline_contract_json = root_path / "pipeline_contract" / f"{variant_id}_pipeline_contract.json"
        pipeline_contract_md = root_path / "pipeline_contract" / f"{variant_id}_pipeline_contract.md"
        acceptance_json = root_path / "acceptance" / f"{variant_id}_acceptance.json"
        comparison_json = root_path / "comparison" / f"{variant_id}_candidate_comparison.json"
        comparison_md = root_path / "comparison" / f"{variant_id}_candidate_comparison.md"
        run_tokens = _set_option(template, "--out", run_dir)
        for option, value in (spec.get("options") or {}).items():
            run_tokens = _set_option(run_tokens, option, value)
        commands = {
            "run": _command(run_tokens),
            "compare_reference": _compare_command(
                master=master,
                reference=reference,
                out=compare_reference_html,
                coverage=coverage,
                glass_scale=glass_scale,
                glass_offset=glass_offset,
                min_coverage=min_coverage,
            ),
            "compare_baseline": _compare_command(
                master=master,
                reference=baseline_master,
                out=compare_baseline_html,
                coverage=coverage,
                glass_scale=None,
                glass_offset=None,
                min_coverage=min_coverage,
            ),
            "pipeline_contract": _pipeline_contract_command(
                glass_run=run_dir,
                out=pipeline_contract_json,
                markdown=pipeline_contract_md,
            ),
            "acceptance_audit": _acceptance_command(
                manifest=manifest,
                glass_run=run_dir,
                wbpp_result=wbpp_result,
                compare_json=compare_reference_html.with_suffix(".json"),
                out=acceptance_json,
                benchmark_contract=benchmark_contract,
                pipeline_contract_json=pipeline_contract_json,
            ),
            "candidate_comparison": _candidate_comparison_command(
                baseline_run=baseline_run,
                candidate_run=run_dir,
                candidate_id=variant_id,
                baseline_compare_json=baseline_compare_json,
                candidate_compare_json=compare_reference_html.with_suffix(".json"),
                candidate_vs_baseline_json=compare_baseline_html.with_suffix(".json"),
                candidate_acceptance_json=acceptance_json,
                min_speedup_vs_reference=min_speedup_vs_reference,
                out=comparison_json,
                markdown=comparison_md,
            ),
        }
        planned.append(
            {
                "variant_id": variant_id,
                "purpose": spec.get("purpose"),
                "run_dir": str(run_dir),
                "changed_options": spec.get("options") or {},
                "effective_runtime_options": {
                    option: _option_value(run_tokens, option)
                    for option in [
                        "--resident-prefetch-frames",
                        "--resident-prefetch-workers",
                        "--resident-prefetch-refill-mode",
                        "--resident-h2d-mode",
                        "--resident-calibration-batch-frames",
                        "--resident-calibration-streams",
                        "--resident-calibration-wave-frames",
                        "--resident-calibration-release-mode",
                    ]
                },
                "artifacts": {
                    "compare_reference_json": str(compare_reference_html.with_suffix(".json")),
                    "compare_baseline_json": str(compare_baseline_html.with_suffix(".json")),
                    "pipeline_contract_json": str(pipeline_contract_json),
                    "acceptance_json": str(acceptance_json),
                    "candidate_comparison_json": str(comparison_json),
                },
                "commands": commands,
            }
        )

    sweep_command = _command(
        [
            "glass",
            "candidate-comparison-sweep",
            *[
                item
                for variant in planned
                for item in ["--comparison", variant["artifacts"]["candidate_comparison_json"]]
            ],
            "--out",
            root_path / "candidate_runtime_sweep.json",
            "--markdown",
            root_path / "candidate_runtime_sweep.md",
            "--fail-on-no-passed",
        ]
    )
    summary = comparison_payload.get("summary") if isinstance(comparison_payload.get("summary"), dict) else {}
    return {
        "schema_version": 1,
        "artifact_type": "candidate_runtime_sweep_plan",
        "created_at": now_iso(),
        "source_comparison": str(comparison),
        "source_candidate_id": comparison_payload.get("candidate_id"),
        "source_recommendation": summary.get("recommendation"),
        "root": str(root_path),
        "base_run_command": str(base_run_command),
        "baseline_run": str(baseline_run),
        "baseline_compare_json": str(baseline_compare_json),
        "variant_count": len(planned),
        "variants": planned,
        "sweep_command": sweep_command,
        "recommendation": "execute_variants_sequentially_then_run_sweep_summary",
        "limitations": [
            "This plan only changes runtime orchestration options; science options are inherited from the accepted candidate command.",
            "The plan writes commands but does not execute integration or image comparison.",
            "Generated commands are specific to the supplied benchmark paths and should be regenerated if artifacts move.",
        ],
    }


def write_candidate_runtime_sweep_plan(
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
        "# Candidate Runtime Sweep Plan",
        "",
        f"- Source candidate: `{payload.get('source_candidate_id')}`",
        f"- Source recommendation: `{payload.get('source_recommendation')}`",
        f"- Variant count: `{payload.get('variant_count')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        "",
        "## Variants",
        "",
        "| variant | purpose | changed options |",
        "| --- | --- | --- |",
    ]
    for row in payload.get("variants") or []:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {variant} | {purpose} | `{options}` |".format(
                variant=row.get("variant_id"),
                purpose=row.get("purpose"),
                options=row.get("changed_options"),
            )
        )
    lines.extend(
        [
            "",
            "## Sweep Command",
            "",
            "```powershell",
            str(payload.get("sweep_command")),
            "```",
            "",
            "## Limitations",
            "",
        ]
    )
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
