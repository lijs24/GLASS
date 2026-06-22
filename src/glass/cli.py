from __future__ import annotations

import argparse
import importlib.util
import platform
import subprocess
import sys
from time import perf_counter
from pathlib import Path
from typing import Any

from rich.console import Console

from glass.capabilities import capability_report
from glass.gpu.compatibility import recommend_windows_cuda_packages
from glass.engine.integration import integrate_registered_frames
from glass.engine.local_norm import local_normalize_registered_frames
from glass.engine.pipeline import initialize_run, run_calibration_stages
from glass.engine.quality import measure_calibrated_quality
from glass.engine.registration import register_calibrated_frames
from glass.engine.resident_calibration_artifacts import build_resident_calibration_artifacts
from glass.engine.resident_cuda import build_resident_memory_admission, run_resident_calibration_integration
from glass.engine.resident_source_dq_strategy import build_resident_source_dq_strategy
from glass.engine.warp import warp_registered_frames
from glass.engine.resume import resume_summary
from glass.engine.state import write_run_state
from glass.io.json_io import read_json, write_json
from glass.metadata.scanner import scan_tree
from glass.planner.plan_builder import build_processing_plan
from glass.planner.subset import build_subset_manifest
from glass.report.blackbox_package import create_blackbox_package, finalize_blackbox_package
from glass.report.compare_report import compare_fits, write_compare_report
from glass.report.compare_outliers import build_compare_outlier_audit, write_compare_outlier_audit
from glass.report.compare_frame_family import build_compare_frame_family_audit, write_compare_frame_family_audit
from glass.report.compare_tile_integration import (
    build_compare_tile_integration_audit,
    write_compare_tile_integration_audit,
)
from glass.report.compare_tile_attribution import build_compare_tile_attribution, write_compare_tile_attribution
from glass.report.compare_tile_pack import build_compare_tile_pack
from glass.report.compare_tile_replay import build_compare_tile_replay, write_compare_tile_replay
from glass.report.frame_weight_proposal import build_frame_weight_proposal, write_frame_weight_proposal
from glass.report.frame_weight_proposal_audit import (
    build_frame_weight_proposal_audit,
    write_frame_weight_proposal_audit,
)
from glass.report.benchmark_contract_profile import (
    RESIDENT_CUDA_DQ_PROFILE_NAME,
    build_resident_cuda_dq_benchmark_contract,
    write_resident_cuda_dq_benchmark_contract,
)
from glass.report.html_report import write_html_report
from glass.report.acceptance_audit import build_acceptance_audit, write_acceptance_audit
from glass.report.residual_tile_candidates import build_residual_tile_candidates, write_residual_tile_candidates
from glass.report.resident_determinism import (
    build_resident_determinism_audit,
    write_resident_determinism_audit,
)
from glass.report.resident_registration_audit import (
    build_resident_registration_audit,
    write_resident_registration_audit,
)
from glass.report.resident_registration_compare import (
    build_resident_registration_compare,
    write_resident_registration_compare,
)
from glass.report.resident_registration_matrix_compare import (
    build_resident_registration_matrix_compare,
    write_resident_registration_matrix_compare,
)
from glass.report.resident_registration_matrix_sweep import (
    build_resident_registration_matrix_sweep,
    write_resident_registration_matrix_sweep,
)
from glass.report.resident_runtime_compare import (
    build_resident_runtime_compare,
    write_resident_runtime_compare,
)
from glass.report.resident_fits_auto_regression import (
    build_resident_fits_auto_regression,
    write_resident_fits_auto_regression,
)
from glass.report.resident_fits_default_matrix import (
    build_resident_fits_default_matrix,
    write_resident_fits_default_matrix,
)
from glass.report.resident_parity_summary import (
    build_resident_parity_summary,
    write_resident_parity_summary,
)
from glass.report.resident_rejection_sample_audit import (
    build_resident_rejection_sample_audit,
    write_resident_rejection_sample_audit,
)
from glass.report.resident_rejection_input_audit import (
    build_resident_rejection_input_audit,
    write_resident_rejection_input_audit,
)
from glass.report.resident_warp_input_audit import (
    build_resident_warp_input_audit,
    write_resident_warp_input_audit,
)
from glass.report.resident_winsorized_benchmark import (
    build_resident_winsorized_benchmark,
    write_resident_winsorized_benchmark,
)
from glass.report.resident_winsorized_benchmark_contract import (
    DEFAULT_CONTRACT_PATH as DEFAULT_RESIDENT_WINSORIZED_BENCHMARK_CONTRACT,
)
from glass.report.resident_winsorized_benchmark_contract import (
    build_resident_winsorized_benchmark_audit,
    write_resident_winsorized_benchmark_audit,
)
from glass.report.resident_winsorized_sweep import (
    DEFAULT_FRAME_COUNTS as DEFAULT_RESIDENT_WINSORIZED_SWEEP_FRAME_COUNTS,
)
from glass.report.resident_winsorized_sweep import (
    build_resident_winsorized_frame_count_sweep,
    parse_frame_counts,
    write_resident_winsorized_frame_count_sweep,
)
from glass.report.resident_winsorized_sweep_contract import (
    DEFAULT_CONTRACT_PATH as DEFAULT_RESIDENT_WINSORIZED_SWEEP_CONTRACT,
)
from glass.report.resident_winsorized_sweep_contract import (
    build_resident_winsorized_sweep_audit,
    write_resident_winsorized_sweep_audit,
)
from glass.report.resident_runtime_repeat_plan import (
    build_resident_runtime_repeat_plan,
    write_resident_runtime_repeat_plan,
)
from glass.report.resident_runtime_repeat_execute import (
    build_resident_runtime_repeat_execution,
    write_resident_runtime_repeat_execution,
)
from glass.report.resident_runtime_repeat_preflight import (
    build_resident_runtime_repeat_preflight,
    write_resident_runtime_repeat_preflight,
)
from glass.report.resident_result_contract import (
    build_resident_result_contract,
    write_resident_result_contract,
)
from glass.report.resident_calibration_contract import (
    build_resident_calibration_contract,
    write_resident_calibration_contract,
)
from glass.report.release_promotion_decision import (
    build_release_promotion_decision,
    write_release_promotion_decision,
)
from glass.report.phase2_status import (
    build_phase2_status,
    build_phase2_status_compare,
    write_phase2_status,
    write_phase2_status_compare,
)
from glass.report.quality_metrics_compare import (
    build_quality_metrics_compare,
    write_quality_metrics_compare,
)
from glass.report.default_promotion_manifest import (
    build_default_promotion_manifest,
    write_default_promotion_manifest,
)
from glass.report.windows_release_matrix import (
    build_windows_release_matrix,
    write_windows_release_matrix,
)
from glass.report.windows_package_build_plan import (
    build_windows_package_build_plan,
    parse_toolkit_root_specs,
    write_windows_package_build_plan,
)
from glass.report.windows_package_suite import (
    build_windows_package_suite,
    parse_labeled_paths,
    write_windows_package_suite,
)
from glass.report.windows_release_manifest import (
    build_windows_release_manifest,
    parse_labeled_zip_paths,
    write_windows_release_manifest,
)
from glass.report.windows_github_release_plan import (
    build_windows_github_release_plan,
    write_windows_github_release_plan,
)
from glass.report.windows_publish_preflight import (
    build_windows_publish_preflight,
    write_windows_publish_preflight,
)
from glass.report.stack_engine_publication_audit import (
    build_stack_engine_publication_audit,
    write_stack_engine_publication_audit,
)
from glass.report.windows_package_smoke import (
    build_windows_package_smoke,
    write_windows_package_smoke,
)
from glass.report.resident_registration_triage import (
    build_resident_registration_triage,
    write_resident_registration_triage,
)
from glass.report.resident_tile_capture import build_resident_tile_capture, write_resident_tile_capture
from glass.report.resident_tile_contribution import (
    build_resident_tile_contribution,
    write_resident_tile_contribution,
)
from glass.report.pipeline_contract import build_pipeline_contract_audit, write_pipeline_contract_audit
from glass.report.local_norm_contract import build_local_norm_contract, write_local_norm_contract
from glass.report.registration_quality import (
    build_registration_quality_contract,
    write_registration_quality_contract,
)
from glass.report.warp_quality import build_warp_quality_contract, write_warp_quality_contract
from glass.report.tile_local_policy import build_tile_local_policy_proposal, write_tile_local_policy_proposal
from glass.report.tile_local_frame_family_search import (
    build_tile_local_frame_family_search,
    write_tile_local_frame_family_search,
)
from glass.report.tile_local_residual_source_audit import (
    build_tile_local_residual_source_audit,
    write_tile_local_residual_source_audit,
)
from glass.report.tile_local_rejection_registration_audit import (
    build_tile_local_rejection_registration_audit,
    write_tile_local_rejection_registration_audit,
)
from glass.report.tile_local_rejection_registration_plan import (
    build_tile_local_rejection_registration_plan,
    write_tile_local_rejection_registration_plan,
)
from glass.report.candidate_comparison import build_candidate_comparison, write_candidate_comparison
from glass.report.candidate_comparison_sweep import (
    build_candidate_comparison_sweep,
    write_candidate_comparison_sweep,
)
from glass.report.candidate_runtime_sweep_plan import (
    build_candidate_runtime_sweep_plan,
    write_candidate_runtime_sweep_plan,
)
from glass.report.candidate_runtime_sweep_execute import (
    build_candidate_runtime_sweep_execution,
    write_candidate_runtime_sweep_execution,
)
from glass.report.resident_ab_matrix_plan import (
    build_resident_ab_matrix_execution,
    build_resident_ab_matrix_plan,
    write_resident_ab_matrix_execution,
    write_resident_ab_matrix_plan,
)
from glass.report.tile_local_policy_replay import build_tile_local_policy_replay, write_tile_local_policy_replay
from glass.report.tile_local_policy_subset import build_tile_local_policy_subset, write_tile_local_policy_subset
from glass.report.tile_local_apply_experiment import (
    build_tile_local_apply_experiment,
    write_tile_local_apply_experiment,
)
from glass.report.tile_local_apply_verify import (
    build_tile_local_apply_verification,
    write_tile_local_apply_verification,
)
from glass.report.tile_local_policy_decision import (
    build_tile_local_policy_decision,
    write_tile_local_policy_decision,
)
from glass.report.tile_local_policy_sweep import build_tile_local_policy_sweep, write_tile_local_policy_sweep
from glass.report.tile_local_sweep_plan import build_tile_local_sweep_plan, write_tile_local_sweep_plan
from glass.report.speedup_report import summarize_wbpp_speedup, write_speedup_summary
from glass.report.stack_engine_contract import (
    build_stack_engine_contract_audit,
    write_stack_engine_contract_audit,
)
from glass.report.wbpp_history import read_fastintegration_history
from glass.synthetic.generator import generate_synthetic_dataset
from glass.models import PipelineArtifact, now_iso

console = Console()


class RegistrationAdmissionBlocked(RuntimeError):
    """Raised when registration policy blocks the selected reference frame."""


class ResidentMemoryAdmissionBlocked(RuntimeError):
    """Raised when resident VRAM admission rejects an explicit budget."""

    def __init__(self, message: str, *, admission: dict[str, Any], path: Path):
        super().__init__(message)
        self.admission = admission
        self.path = path


RESIDENT_RUNTIME_PRESETS: dict[str, dict[str, object]] = {
    "manual": {},
    "throughput-v1": {
        "resident_prefetch_frames": 12,
        "resident_prefetch_workers": 7,
        "resident_prefetch_refill_mode": "queued",
        "resident_h2d_mode": "pinned_ring",
        "resident_calibration_batch_frames": 8,
        "resident_calibration_streams": 4,
        "resident_calibration_wave_frames": 2,
        "resident_calibration_release_mode": "callback_queue",
    },
    "throughput-v2-fused": {
        "resident_prefetch_frames": 12,
        "resident_prefetch_workers": 7,
        "resident_prefetch_refill_mode": "queued",
        "resident_h2d_mode": "pinned_ring",
        "resident_calibration_batch_frames": 8,
        "resident_calibration_streams": 4,
        "resident_calibration_wave_frames": 2,
        "resident_calibration_release_mode": "callback_queue",
        "resident_integration_dispatch": "auto",
    },
    "throughput-v3-io": {
        "resident_prefetch_frames": 32,
        "resident_prefetch_workers": 12,
        "resident_prefetch_refill_mode": "queued",
        "resident_h2d_mode": "pinned_ring",
        "resident_calibration_batch_frames": 16,
        "resident_calibration_streams": 4,
        "resident_calibration_wave_frames": 4,
        "resident_calibration_release_mode": "callback_queue",
    },
}
DEFAULT_RESIDENT_RUNTIME_PRESET = "throughput-v1"
DEFAULT_MEMORY_MODE = "resident"
FALLBACK_MEMORY_MODE = "tile"
DEFAULT_UNTIL_STAGE = "integration"
DEFAULT_RESIDENT_FITS_READ_MODE = "auto"

RESIDENT_RUNTIME_PRESET_FLAGS = {
    "resident_prefetch_frames": "--resident-prefetch-frames",
    "resident_prefetch_workers": "--resident-prefetch-workers",
    "resident_prefetch_refill_mode": "--resident-prefetch-refill-mode",
    "resident_h2d_mode": "--resident-h2d-mode",
    "resident_calibration_batch_frames": "--resident-calibration-batch-frames",
    "resident_calibration_streams": "--resident-calibration-streams",
    "resident_calibration_wave_frames": "--resident-calibration-wave-frames",
    "resident_calibration_release_mode": "--resident-calibration-release-mode",
    "resident_integration_dispatch": "--resident-integration-dispatch",
}


def _read_json_if_exists(path: Path):
    return read_json(path) if path.exists() else None


def _read_report_json_if_exists(path: Path | None):
    if path is None or not path.exists():
        return None
    payload = read_json(path)
    if isinstance(payload, dict):
        payload["_report_source_path"] = str(path)
    return payload


def _newest_matching_json(run: Path, patterns: list[str]) -> Path | None:
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(path for path in run.glob(pattern) if path.is_file())
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name))


def _report_compare_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(run, ["*compare*.json"])


def _report_acceptance_audit_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(run, ["*acceptance_audit*.json"])


def _report_stack_engine_contract_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(run, ["*stack_engine_contract*.json", "*stack-engine-contract*.json"])


def _report_pipeline_contract_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(run, ["*pipeline_contract*.json", "*pipeline-contract*.json"])


def _report_local_norm_contract_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(run, ["*local_norm_contract*.json", "*local-norm-contract*.json"])


def _report_registration_quality_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(
        run,
        ["*registration_quality_contract*.json", "*registration-quality-contract*.json"],
    )


def _report_warp_quality_path(run: Path, explicit: str | Path | None = None) -> Path | None:
    if explicit:
        return Path(explicit)
    return _newest_matching_json(run, ["*warp_quality_contract*.json", "*warp-quality-contract*.json"])


def _local_norm_override_from_arg(value: str) -> bool | None:
    if value == "on":
        return True
    if value == "off":
        return False
    return None


def _argv_has_option(args: argparse.Namespace, flag: str) -> bool:
    argv = list(getattr(args, "_glass_argv", []) or [])
    return any(token == flag or token.startswith(f"{flag}=") for token in argv)


def _apply_resident_runtime_preset(args: argparse.Namespace) -> None:
    preset = getattr(args, "resident_runtime_preset", "manual")
    values = RESIDENT_RUNTIME_PRESETS[preset]
    applied: dict[str, object] = {}
    explicit: dict[str, object] = {}
    for attr, value in values.items():
        flag = RESIDENT_RUNTIME_PRESET_FLAGS[attr]
        if _argv_has_option(args, flag):
            explicit[attr] = getattr(args, attr)
            continue
        setattr(args, attr, value)
        applied[attr] = value
    args._resident_runtime_preset_effective = {
        "preset": preset,
        "applied": applied,
        "explicit_overrides": explicit,
    }


def _resolve_resident_fits_read_mode_default(args: argparse.Namespace, *, command: str) -> dict[str, object]:
    requested = getattr(args, "resident_fits_read_mode", None)
    explicit = _argv_has_option(args, "--resident-fits-read-mode")
    effective = requested
    source = "explicit" if explicit else "unused_non_resident"
    reason = ""
    if explicit:
        effective = requested
        reason = "user_explicit_resident_fits_read_mode"
    elif getattr(args, "memory_mode", None) == "resident" and getattr(args, "backend", None) == "cuda":
        effective = DEFAULT_RESIDENT_FITS_READ_MODE
        setattr(args, "resident_fits_read_mode", effective)
        source = "resident_cuda_guarded_auto_default"
        reason = "resident_cuda_default_uses_guarded_auto_reader"
    else:
        effective = requested or "astropy"
        setattr(args, "resident_fits_read_mode", effective)
        reason = "non_resident_path_keeps_compatible_placeholder"
    resolution = {
        "schema_version": 1,
        "command": command,
        "requested": requested,
        "effective": effective,
        "explicit": explicit,
        "source": source,
        "reason": reason,
        "default": DEFAULT_RESIDENT_FITS_READ_MODE,
        "fallback": "astropy",
        "escape_hatch": "--resident-fits-read-mode astropy",
    }
    args._resident_fits_read_mode_resolution = resolution
    return resolution


def _explicit_option(args: argparse.Namespace, flag: str) -> bool:
    return _argv_has_option(args, flag)


def _resident_default_blocker(args: argparse.Namespace) -> str | None:
    until_stage = getattr(args, "until_stage", DEFAULT_UNTIL_STAGE)
    if until_stage != "integration":
        return f"until_stage:{until_stage}"
    if getattr(args, "integration_rejection", "auto") not in {
        "auto",
        "none",
        "sigma_clip",
        "winsorized_sigma",
    }:
        return f"integration_rejection:{getattr(args, 'integration_rejection', None)}"
    if getattr(args, "integration_weighting", "auto") not in {"auto", "none", "simple_snr"}:
        return f"integration_weighting:{getattr(args, 'integration_weighting', None)}"
    if _explicit_option(args, "--registration-method") and getattr(args, "registration_method", "auto") != "auto":
        return f"tile_registration_method:{getattr(args, 'registration_method', None)}"
    return None


def _resolve_execution_defaults(
    args: argparse.Namespace,
    capabilities: dict[str, object],
    *,
    command: str,
) -> dict[str, object]:
    requested_backend = str(getattr(args, "backend", "auto"))
    requested_memory_mode = str(getattr(args, "memory_mode", FALLBACK_MEMORY_MODE))
    explicit_memory_mode = _explicit_option(args, "--memory-mode")
    explicit_backend = _explicit_option(args, "--backend")
    cuda_available = bool(capabilities.get("cuda_available"))
    blocker = _resident_default_blocker(args)

    reason = "explicit_configuration"
    if requested_memory_mode == "resident" and blocker is not None:
        if explicit_memory_mode:
            reason = "explicit_resident_unsupported_options"
        else:
            setattr(args, "memory_mode", FALLBACK_MEMORY_MODE)
            reason = "resident_default_fallback_unsupported_options"
    if getattr(args, "memory_mode", requested_memory_mode) == "resident":
        if requested_backend == "cuda":
            if not cuda_available:
                raise SystemExit("CUDA backend requested but native CUDA backend is unavailable.")
            reason = "resident_cuda_requested" if explicit_memory_mode or explicit_backend else "resident_cuda_default"
        elif requested_backend == "auto":
            if cuda_available:
                setattr(args, "backend", "cuda")
                reason = (
                    "resident_cuda_auto_backend"
                    if explicit_memory_mode
                    else "resident_cuda_default"
                )
            elif explicit_memory_mode:
                raise SystemExit(
                    "Resident memory mode requested but native CUDA backend is unavailable; "
                    "use --memory-mode tile or --backend cpu."
                )
            else:
                setattr(args, "memory_mode", FALLBACK_MEMORY_MODE)
                reason = "resident_default_fallback_cuda_unavailable"
        elif explicit_memory_mode:
            raise SystemExit("Resident memory mode currently requires --backend cuda or --backend auto.")
        else:
            setattr(args, "memory_mode", FALLBACK_MEMORY_MODE)
            reason = "resident_default_fallback_non_cuda_backend"

    resolution = {
        "schema_version": 1,
        "command": command,
        "requested_backend": requested_backend,
        "requested_memory_mode": requested_memory_mode,
        "effective_backend": getattr(args, "backend", requested_backend),
        "effective_memory_mode": getattr(args, "memory_mode", requested_memory_mode),
        "explicit_backend": explicit_backend,
        "explicit_memory_mode": explicit_memory_mode,
        "cuda_available": cuda_available,
        "resident_default_candidate": DEFAULT_MEMORY_MODE,
        "fallback_memory_mode": FALLBACK_MEMORY_MODE,
        "default_runtime_preset": DEFAULT_RESIDENT_RUNTIME_PRESET,
        "resident_default_blocker": blocker,
        "reason": reason,
    }
    args._execution_default_resolution = resolution
    return resolution


def _annotate_timing_execution_defaults(timing: dict, args: argparse.Namespace) -> None:
    resolution = getattr(args, "_execution_default_resolution", None)
    if isinstance(resolution, dict):
        timing["execution_default_resolution"] = resolution
        timing["backend_requested"] = resolution.get("requested_backend")
        timing["memory_mode_requested"] = resolution.get("requested_memory_mode")
    timing["backend"] = getattr(args, "backend", timing.get("backend"))
    timing["memory_mode"] = getattr(args, "memory_mode", timing.get("memory_mode"))
    timing["resident_runtime_preset"] = getattr(args, "resident_runtime_preset", None)
    timing["resident_source_dq_cache"] = getattr(args, "resident_source_dq_cache", "off")
    timing["resident_inline_source_dq"] = getattr(args, "resident_inline_source_dq", "off")
    preset = getattr(args, "_resident_runtime_preset_effective", None)
    if isinstance(preset, dict):
        timing["resident_runtime_preset_effective"] = preset
    fits_resolution = getattr(args, "_resident_fits_read_mode_resolution", None)
    if isinstance(fits_resolution, dict):
        timing["resident_fits_read_mode_resolution"] = fits_resolution


def _safe_platform_label() -> str:
    if sys.platform.startswith("win"):
        version = sys.getwindowsversion()
        return f"Windows-{version.major}.{version.minor}.{version.build}"
    try:
        return platform.platform()
    except Exception as exc:  # pragma: no cover - environment-specific diagnostic path
        return f"{sys.platform} ({exc})"


def _new_timing(command: str, backend: str | None = None, tile_size: int | None = None) -> dict:
    return {
        "schema_version": 1,
        "command": command,
        "created_at": now_iso(),
        "backend": backend,
        "tile_size": tile_size,
        "stages": [],
        "total_elapsed_s": 0.0,
    }


def _write_timing(run: Path, timing: dict) -> None:
    timing["total_elapsed_s"] = float(sum(float(item.get("elapsed_s") or 0.0) for item in timing["stages"]))
    write_json(run / "run_timing.json", timing)


def _write_run_command(run: Path, args: argparse.Namespace) -> None:
    argv = list(getattr(args, "_glass_argv", []) or sys.argv[1:])
    command = subprocess.list2cmdline(["glass", *argv])
    (run / "run_command.txt").write_text(command, encoding="utf-8")


def _resolve_route_sidecar_path(path: str | Path, *, artifact_root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return candidate if candidate.exists() else artifact_root / candidate


def _resident_source_dq_cache_preflight(
    plan_path: str | Path,
    run: Path,
    *,
    max_disk_fraction: float = 0.75,
    free_bytes: int | None = None,
) -> dict[str, Any]:
    return build_resident_source_dq_strategy(
        plan_path,
        run,
        max_disk_fraction=max_disk_fraction,
        free_bytes=free_bytes,
        artifact_type="resident_source_dq_cache_preflight",
    )


def _resident_source_dq_strategy_path(run: Path) -> Path:
    return run / "resident_source_dq_strategy.json"


def _resident_memory_admission_path(run: Path) -> Path:
    return run / "resident_memory_admission.json"


def _resident_memory_admission_message(admission: dict[str, Any]) -> str:
    return (
        "resident memory admission failed: "
        f"selected_estimated_peak_gib={float(admission.get('selected_estimated_peak_gib') or admission.get('estimated_peak_gib') or 0.0):.6f}, "
        f"budget_gib={float(admission.get('budget_gib') or 0.0):.6f}, "
        f"recommended_action={admission.get('recommended_action')}"
    )


def _apply_resident_memory_admission_selection(
    args: argparse.Namespace,
    admission: dict[str, Any],
) -> None:
    selected_dispatch = str(
        admission.get("selected_warp_batch_dispatch")
        or admission.get("effective_warp_batch_dispatch")
        or getattr(args, "resident_warp_batch_dispatch", "chunked")
    )
    if selected_dispatch in {"loop", "chunked"}:
        args.resident_warp_batch_dispatch = selected_dispatch
    selected_capacity = admission.get("selected_chunk_capacity_frames")
    capacity_value: int | None = None
    try:
        if (
            selected_capacity is not None
            and selected_dispatch == "chunked"
            and admission.get("recommended_action") == "resident_reduced_chunk_capacity"
        ):
            parsed = int(selected_capacity)
            if parsed > 0:
                capacity_value = parsed
    except (TypeError, ValueError):
        capacity_value = None
    args._resident_warp_chunk_capacity_frames = capacity_value


def _write_resident_memory_admission(
    run: Path,
    args: argparse.Namespace,
    *,
    plan_path: str | Path | None = None,
) -> Path:
    try:
        import glass_cuda  # type: ignore[import-not-found]
    except Exception:  # pragma: no cover - resident path already checks CUDA availability
        glass_cuda = None  # type: ignore[assignment]
    admission = build_resident_memory_admission(
        plan_path or args.plan,
        cuda_module=glass_cuda,
        resident_registration=getattr(args, "resident_registration", "off"),
        resident_warp_batch_dispatch=getattr(args, "resident_warp_batch_dispatch", "chunked"),
        resident_integration_dispatch=getattr(args, "resident_integration_dispatch", "stack"),
        resident_warp_interpolation=getattr(args, "resident_warp_interpolation", "bilinear"),
        local_normalization=getattr(args, "local_normalization", "auto"),
        integration_rejection=getattr(args, "integration_rejection", "auto"),
        resident_winsorized_mode=getattr(args, "resident_winsorized_mode", "fast_approx"),
        exclude_frame_ids=list(getattr(args, "exclude_frame_id", []) or []),
        vram_budget_gb=getattr(args, "vram_budget_gb", None),
        dispatch_explicit=_explicit_option(args, "--resident-warp-batch-dispatch"),
    )
    admission_path = _resident_memory_admission_path(run)
    write_json(admission_path, admission)
    args._resident_memory_admission = admission
    if admission.get("blocking"):
        raise ResidentMemoryAdmissionBlocked(
            _resident_memory_admission_message(admission),
            admission=admission,
            path=admission_path,
        )
    _apply_resident_memory_admission_selection(args, admission)
    return admission_path


def _write_resident_memory_admission_failed_state(
    run: Path,
    exc: ResidentMemoryAdmissionBlocked,
    *,
    completed_stages: list[str] | None = None,
) -> None:
    state = initialize_run(run)
    state.current_stage = "resident_memory_admission"
    state.failed_stage = "resident_memory_admission"
    state.completed_stages = list(completed_stages or [])
    state.errors.append(str(exc))
    state.artifacts.append(
        PipelineArtifact(
            stage="resident_memory_admission",
            path=str(exc.path),
            format="json",
            created_at=now_iso(),
            source_frames=[],
        )
    )
    write_run_state(run, state)


def _write_resident_source_dq_strategy(
    run: Path,
    args: argparse.Namespace,
    *,
    plan_path: str | Path | None = None,
) -> Path:
    memory_budget_bytes = None
    if getattr(args, "vram_budget_gb", None) is not None:
        memory_budget_bytes = int(float(args.vram_budget_gb) * (1024**3))
    strategy = build_resident_source_dq_strategy(
        plan_path or args.plan,
        run,
        max_disk_fraction=getattr(args, "resident_source_dq_cache_max_disk_fraction", 0.75),
        resident_mask_batch_frames=max(1, int(getattr(args, "resident_calibration_batch_frames", 1) or 1)),
        resident_memory_budget_bytes=memory_budget_bytes,
        resident_inline_source_dq=getattr(args, "resident_inline_source_dq", "off"),
        resident_inline_source_dq_hot_sigma=getattr(args, "resident_inline_source_dq_hot_sigma", 8.0),
        resident_inline_source_dq_cold_sigma=getattr(args, "resident_inline_source_dq_cold_sigma", 8.0),
    )
    strategy_path = _resident_source_dq_strategy_path(run)
    write_json(strategy_path, strategy)
    return strategy_path


def _write_resident_source_dq_cache_route(run: Path, args: argparse.Namespace) -> Path:
    artifact_path = run / "calibration_artifacts.json"
    preflight_path = run / "resident_source_dq_cache_preflight.json"
    preflight = read_json(preflight_path) if preflight_path.exists() else None
    payload: dict[str, Any] = {}
    if artifact_path.exists():
        payload = read_json(artifact_path)
    calibrated_lights = payload.get("calibrated_lights") if isinstance(payload, dict) else None
    calibrated_lights = calibrated_lights if isinstance(calibrated_lights, list) else []
    dq_sidecar_rows: list[dict[str, Any]] = []
    dq_summary_totals: dict[str, int] = {}
    cosmetic_enabled_count = 0
    for item in calibrated_lights:
        if not isinstance(item, dict):
            continue
        cosmetic = item.get("cosmetic_correction")
        if isinstance(cosmetic, dict) and cosmetic.get("enabled"):
            cosmetic_enabled_count += 1
        dq_summary = item.get("dq_summary")
        if isinstance(dq_summary, dict):
            for key, value in dq_summary.items():
                if isinstance(value, (int, float)):
                    dq_summary_totals[key] = dq_summary_totals.get(key, 0) + int(value)
        sidecar = item.get("dq_mask_path")
        if not sidecar:
            continue
        sidecar_path = _resolve_route_sidecar_path(str(sidecar), artifact_root=artifact_path.parent)
        dq_sidecar_rows.append(
            {
                "frame_id": item.get("frame_id"),
                "dq_mask_path": str(sidecar_path),
                "exists": sidecar_path.exists(),
            }
        )
    audit = {
        "schema_version": 1,
        "artifact_type": "resident_source_dq_cache_route",
        "created_at": now_iso(),
        "mode": args.resident_source_dq_cache,
        "status": "ready" if artifact_path.exists() else "missing_calibration_artifacts",
        "generated": args.resident_source_dq_cache == "generate-calibration",
        "calibration_backend": "cpu",
        "tile_size": args.tile_size,
        "flat_floor_override": args.flat_floor,
        "calibration_artifacts_path": str(artifact_path),
        "calibration_artifacts_exists": artifact_path.exists(),
        "calibrated_light_count": len(calibrated_lights),
        "dq_sidecar_count": len(dq_sidecar_rows),
        "existing_dq_sidecar_count": sum(1 for row in dq_sidecar_rows if row["exists"]),
        "missing_dq_sidecar_count": sum(1 for row in dq_sidecar_rows if not row["exists"]),
        "cosmetic_correction_enabled_frame_count": cosmetic_enabled_count,
        "dq_summary_totals": dq_summary_totals,
        "dq_sidecars": dq_sidecar_rows,
        "preflight": preflight,
        "resident_consumption": {
            "source": "calibration_artifacts.calibrated_lights.dq_mask_path",
            "consumer": "resident CUDA source-DQ sidecar index",
            "default_enabled": False,
        },
    }
    route_path = run / "resident_source_dq_cache_route.json"
    write_json(route_path, audit)
    return route_path


def _timed_stage(run: Path, timing: dict, stage: str, fn):
    record = {"stage": stage, "started_at": now_iso(), "status": "running"}
    start = perf_counter()
    try:
        result = fn()
    except Exception as exc:
        record["status"] = "failed"
        record["elapsed_s"] = perf_counter() - start
        record["error"] = str(exc)
        timing["stages"].append(record)
        _write_timing(run, timing)
        raise
    record["status"] = "ok"
    record["elapsed_s"] = perf_counter() - start
    timing["stages"].append(record)
    _write_timing(run, timing)
    return result


def _registration_admission_blocked_message(payload: dict[str, Any]) -> str | None:
    admission = payload.get("reference_admission")
    if not isinstance(admission, dict) or admission.get("status") != "blocked":
        return None
    reference_id = admission.get("reference_frame_id")
    reason = admission.get("reason") or "reference admission blocked"
    quality_status = admission.get("quality_gate_status")
    return (
        "registration reference admission blocked"
        f": reference={reference_id}, quality_gate_status={quality_status}, reason={reason}"
    )


def _register_calibrated_frames_or_fail(*args, **kwargs) -> dict[str, Any]:
    payload = register_calibrated_frames(*args, **kwargs)
    message = _registration_admission_blocked_message(payload)
    if message is not None:
        raise RegistrationAdmissionBlocked(message)
    return payload


def _write_failed_run_state(run: Path, state, stage: str, exc: Exception) -> None:
    state.current_stage = stage
    state.failed_stage = stage
    message = str(exc)
    if message not in state.errors:
        state.errors.append(message)
    write_run_state(run, state)


def _write_run_report(
    run: Path,
    report_path: Path,
    manifest_path: Path,
    plan_path: Path,
    *,
    compare_json: str | Path | None = None,
    acceptance_audit: str | Path | None = None,
    stack_engine_contract: str | Path | None = None,
    pipeline_contract: str | Path | None = None,
    local_norm_contract: str | Path | None = None,
    registration_quality: str | Path | None = None,
    warp_quality: str | Path | None = None,
) -> None:
    write_html_report(
        report_path,
        manifest=_read_json_if_exists(manifest_path),
        plan=_read_json_if_exists(plan_path),
        calibration=_read_json_if_exists(run / "calibration_artifacts.json"),
        quality=_read_json_if_exists(run / "frame_quality.json"),
        registration=_read_json_if_exists(run / "registration_results.json"),
        local_norm=_read_json_if_exists(run / "local_norm_results.json"),
        integration=_read_json_if_exists(run / "integration_results.json"),
        timing=_read_json_if_exists(run / "run_timing.json"),
        resident=_read_json_if_exists(run / "resident_artifacts.json"),
        frame_accounting=_read_json_if_exists(run / "frame_accounting.json"),
        compare=_read_report_json_if_exists(_report_compare_path(run, compare_json)),
        acceptance_audit=_read_report_json_if_exists(_report_acceptance_audit_path(run, acceptance_audit)),
        stack_engine_contract=_read_report_json_if_exists(
            _report_stack_engine_contract_path(run, stack_engine_contract)
        ),
        pipeline_contract=_read_report_json_if_exists(_report_pipeline_contract_path(run, pipeline_contract)),
        local_norm_contract=_read_report_json_if_exists(
            _report_local_norm_contract_path(run, local_norm_contract)
        ),
        registration_quality=_read_report_json_if_exists(
            _report_registration_quality_path(run, registration_quality)
        ),
        warp_quality=_read_report_json_if_exists(_report_warp_quality_path(run, warp_quality)),
        run_root=run,
    )


def _seed_run_inputs(run: Path, plan_path: str | Path) -> None:
    run.mkdir(parents=True, exist_ok=True)
    plan = read_json(plan_path)
    write_json(run / "processing_plan.json", plan)
    manifest_path = plan.get("manifest_path")
    if manifest_path and Path(manifest_path).exists():
        write_json(run / "manifest.json", read_json(manifest_path))


def _run_full_pipeline(
    plan_path: Path,
    out: Path,
    backend: str,
    tile_size: int,
    local_normalization: str,
    integration_weighting: str,
    integration_rejection: str,
    registration_method: str = "auto",
    warp_interpolation: str = "bilinear",
    timing: dict | None = None,
):
    timing = timing or _new_timing("run", backend, tile_size)
    state = initialize_run(out)
    try:
        state.current_stage = "calibration"
        state = _timed_stage(
            out,
            timing,
            "calibration",
            lambda: run_calibration_stages(plan_path, out, backend=backend, tile_size=tile_size),
        )
        state.current_stage = "quality"
        _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(out, tile_size=tile_size))
        state.completed_stages.append("quality")
        state.current_stage = "registration"
        _timed_stage(
            out,
            timing,
            "registration",
            lambda: _register_calibrated_frames_or_fail(out, tile_size=tile_size, method=registration_method),
        )
        state.completed_stages.append("registration")
        state.current_stage = "warp"
        _timed_stage(
            out,
            timing,
            "warp",
            lambda: warp_registered_frames(out, tile_size=tile_size, interpolation=warp_interpolation),
        )
        state.completed_stages.append("warp")
        state.current_stage = "local_normalization"
        _timed_stage(
            out,
            timing,
            "local_normalization",
            lambda: local_normalize_registered_frames(
                out,
                plan_path=plan_path,
                backend=backend,
                tile_size=tile_size,
                enabled_override=_local_norm_override_from_arg(local_normalization),
            ),
        )
        state.completed_stages.append("local_normalization")
        state.current_stage = "integration"
        _timed_stage(
            out,
            timing,
            "integration",
            lambda: integrate_registered_frames(
                out,
                plan_path=plan_path,
                backend=backend,
                tile_size=tile_size,
                weighting_override=integration_weighting,
                rejection_override=integration_rejection,
            ),
        )
        state.completed_stages.append("integration")
        state.current_stage = "integration"
    except RegistrationAdmissionBlocked as exc:
        _write_failed_run_state(out, state, "registration", exc)
        raise
    return state


def _resume_pipeline(plan_path: Path, out: Path, backend: str = "auto", tile_size: int = 512, timing: dict | None = None):
    timing = timing or _new_timing("resume", backend, tile_size)
    state = initialize_run(out)
    try:
        if (out / "calibration_artifacts.json").exists():
            state.completed_stages.extend(["master_calibration", "light_calibration"])
            state.current_stage = "calibration"
        else:
            return _run_full_pipeline(plan_path, out, backend, tile_size, "auto", "auto", "auto", "auto", "bilinear", timing)

        if not (out / "frame_quality.json").exists():
            state.current_stage = "quality"
            _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(out, tile_size=tile_size))
        state.completed_stages.append("quality")
        state.current_stage = "quality"

        if not (out / "registration_results.json").exists():
            state.current_stage = "registration"
            _timed_stage(
                out,
                timing,
                "registration",
                lambda: _register_calibrated_frames_or_fail(out, tile_size=tile_size),
            )
        else:
            message = _registration_admission_blocked_message(read_json(out / "registration_results.json"))
            if message is not None:
                timing["stages"].append(
                    {
                        "stage": "registration",
                        "started_at": now_iso(),
                        "status": "failed",
                        "elapsed_s": 0.0,
                        "error": message,
                        "resume_existing_artifact": True,
                    }
                )
                _write_timing(out, timing)
                raise RegistrationAdmissionBlocked(message)
        state.completed_stages.append("registration")
        state.current_stage = "registration"

        if not (out / "warp_results.json").exists():
            state.current_stage = "warp"
            _timed_stage(out, timing, "warp", lambda: warp_registered_frames(out, tile_size=tile_size))
        state.completed_stages.append("warp")
        state.current_stage = "warp"

        if not (out / "local_norm_results.json").exists():
            state.current_stage = "local_normalization"
            _timed_stage(
                out,
                timing,
                "local_normalization",
                lambda: local_normalize_registered_frames(out, plan_path=plan_path, backend=backend, tile_size=tile_size),
            )
        state.completed_stages.append("local_normalization")
        state.current_stage = "local_normalization"

        if not (out / "integration_results.json").exists():
            state.current_stage = "integration"
            _timed_stage(
                out,
                timing,
                "integration",
                lambda: integrate_registered_frames(out, plan_path=plan_path, backend=backend, tile_size=tile_size),
            )
        state.completed_stages.append("integration")
        state.current_stage = "integration"
    except RegistrationAdmissionBlocked as exc:
        _write_failed_run_state(out, state, "registration", exc)
        raise
    return state


def _run_pipeline_until_stage(args: argparse.Namespace, out: Path, timing: dict):
    state = initialize_run(out)
    try:
        state.current_stage = "calibration"
        state = _timed_stage(
            out,
            timing,
            "calibration",
            lambda: run_calibration_stages(
                args.plan,
                args.out,
                backend=args.backend,
                tile_size=args.tile_size,
                flat_floor=args.flat_floor,
            ),
        )
        if args.until_stage in {"quality", "registration", "warp", "local_normalization", "integration"}:
            state.current_stage = "quality"
            _timed_stage(out, timing, "quality", lambda: measure_calibrated_quality(args.out, tile_size=args.tile_size))
            state.completed_stages.append("quality")
        if args.until_stage in {"registration", "warp", "local_normalization", "integration"}:
            state.current_stage = "registration"
            _timed_stage(
                out,
                timing,
                "registration",
                lambda: _register_calibrated_frames_or_fail(
                    args.out,
                    tile_size=args.tile_size,
                    preview_max_dimension=args.registration_preview_max_dimension,
                    method=args.registration_method,
                    reference_frame_id=args.reference_frame_id,
                ),
            )
            state.completed_stages.append("registration")
        if args.until_stage in {"warp", "local_normalization", "integration"}:
            state.current_stage = "warp"
            _timed_stage(
                out,
                timing,
                "warp",
                lambda: warp_registered_frames(
                    args.out,
                    tile_size=args.tile_size,
                    interpolation=args.warp_interpolation,
                ),
            )
            state.completed_stages.append("warp")
        if args.until_stage in {"local_normalization", "integration"}:
            state.current_stage = "local_normalization"
            _timed_stage(
                out,
                timing,
                "local_normalization",
                lambda: local_normalize_registered_frames(
                    args.out,
                    plan_path=args.plan,
                    backend=args.backend,
                    tile_size=args.tile_size,
                    enabled_override=_local_norm_override_from_arg(args.local_normalization),
                ),
            )
            state.completed_stages.append("local_normalization")
        if args.until_stage == "integration":
            state.current_stage = "integration"
            _timed_stage(
                out,
                timing,
                "integration",
                lambda: integrate_registered_frames(
                    args.out,
                    plan_path=args.plan,
                    backend=args.backend,
                    tile_size=args.tile_size,
                    weighting_override=args.integration_weighting,
                    rejection_override=args.integration_rejection,
                ),
            )
            state.completed_stages.append("integration")
    except RegistrationAdmissionBlocked as exc:
        _write_failed_run_state(out, state, "registration", exc)
        raise
    return state


def cmd_scan(args: argparse.Namespace) -> int:
    manifest = scan_tree(args.root)
    write_json(args.out, manifest)
    summary = manifest["summary"]
    console.print(f"Scanned {summary['count']} frame(s)")
    console.print(summary)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    plan = build_processing_plan(manifest, args.manifest)
    write_json(args.out, plan)
    console.print(f"Wrote processing plan: {args.out}")
    console.print({"executable": plan.executable, "warnings": len(plan.global_warnings)})
    return 0


def cmd_subset(args: argparse.Namespace) -> int:
    manifest = read_json(args.manifest)
    subset = build_subset_manifest(
        manifest,
        object_name=args.object,
        filter_name=args.filter,
        exposure_s=args.exposure_s,
        light_limit=args.light_limit,
        bias_limit=args.bias_limit,
        dark_limit=args.dark_limit,
        flat_limit=args.flat_limit,
        all_compatible_calibration=args.all_compatible_calibration,
    )
    write_json(args.out, subset)
    summary = subset["summary"]
    console.print(f"Wrote subset manifest: {args.out}")
    console.print(summary)
    if args.plan_out:
        plan = build_processing_plan(subset, args.out)
        write_json(args.plan_out, plan)
        console.print(f"Wrote subset processing plan: {args.plan_out}")
        console.print({"executable": plan.executable, "warnings": len(plan.global_warnings)})
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    run = Path(args.run)
    manifest_path = Path(args.manifest) if args.manifest else run / "manifest.json"
    plan_path = Path(args.plan) if args.plan else run / "processing_plan.json"
    manifest = _read_json_if_exists(manifest_path)
    plan = _read_json_if_exists(plan_path)
    quality_path = run / "frame_quality.json"
    calibration_path = run / "calibration_artifacts.json"
    registration_path = run / "registration_results.json"
    local_norm_path = run / "local_norm_results.json"
    integration_path = run / "integration_results.json"
    timing_path = run / "run_timing.json"
    resident_path = run / "resident_artifacts.json"
    frame_accounting_path = run / "frame_accounting.json"
    calibration = _read_json_if_exists(calibration_path)
    quality = _read_json_if_exists(quality_path)
    registration = _read_json_if_exists(registration_path)
    local_norm = _read_json_if_exists(local_norm_path)
    integration = _read_json_if_exists(integration_path)
    timing = _read_json_if_exists(timing_path)
    resident = _read_json_if_exists(resident_path)
    frame_accounting = _read_json_if_exists(frame_accounting_path)
    compare_payload = _read_report_json_if_exists(_report_compare_path(run, args.compare_json))
    acceptance_payload = _read_report_json_if_exists(_report_acceptance_audit_path(run, args.acceptance_audit))
    stack_contract_payload = _read_report_json_if_exists(
        _report_stack_engine_contract_path(run, args.stack_engine_contract)
    )
    pipeline_contract_payload = _read_report_json_if_exists(
        _report_pipeline_contract_path(run, args.pipeline_contract)
    )
    local_norm_contract_payload = _read_report_json_if_exists(
        _report_local_norm_contract_path(run, args.local_norm_contract)
    )
    registration_quality_payload = _read_report_json_if_exists(
        _report_registration_quality_path(run, args.registration_quality)
    )
    warp_quality_payload = _read_report_json_if_exists(_report_warp_quality_path(run, args.warp_quality))
    write_html_report(
        args.out,
        manifest=manifest,
        plan=plan,
        calibration=calibration,
        quality=quality,
        registration=registration,
        local_norm=local_norm,
        integration=integration,
        timing=timing,
        resident=resident,
        frame_accounting=frame_accounting,
        compare=compare_payload,
        acceptance_audit=acceptance_payload,
        stack_engine_contract=stack_contract_payload,
        pipeline_contract=pipeline_contract_payload,
        local_norm_contract=local_norm_contract_payload,
        registration_quality=registration_quality_payload,
        warp_quality=warp_quality_payload,
        run_root=run,
    )
    console.print(f"Wrote report: {args.out}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    capabilities = capability_report()
    _resolve_execution_defaults(args, capabilities, command="audit")
    _apply_resident_runtime_preset(args)
    _resolve_resident_fits_read_mode_default(args, command="audit")
    _write_run_command(out, args)
    if args.backend == "cuda" and not capabilities["cuda_available"]:
        raise SystemExit("CUDA backend requested but unavailable; use --backend auto or cpu.")
    if args.memory_mode == "resident" and args.backend != "cuda":
        raise SystemExit("Resident audit currently requires --backend cuda.")
    manifest_path = out / "manifest.json"
    plan_path = out / "processing_plan.json"
    report_path = out / "report.html"
    timing = _new_timing("audit", args.backend, args.tile_size)
    _annotate_timing_execution_defaults(timing, args)
    manifest = _timed_stage(out, timing, "scan", lambda: scan_tree(args.root))
    write_json(manifest_path, manifest)
    plan = _timed_stage(out, timing, "plan", lambda: build_processing_plan(manifest, manifest_path))
    write_json(plan_path, plan)
    if plan.executable and args.memory_mode == "resident":
        try:
            resident_memory_admission_path = _timed_stage(
                out,
                timing,
                "resident_memory_admission",
                lambda: _write_resident_memory_admission(out, args, plan_path=plan_path),
            )
        except ResidentMemoryAdmissionBlocked as exc:
            _write_resident_memory_admission_failed_state(out, exc, completed_stages=["scan", "plan"])
            console.print({"status": "failed", "stage": "resident_memory_admission", "error": str(exc)})
            return 2
        state = _timed_stage(
            out,
            timing,
            "resident_calibration_integration",
            lambda: run_resident_calibration_integration(
                plan_path,
                out,
                integration_weighting=args.integration_weighting,
                integration_rejection=args.integration_rejection,
                flat_floor=args.flat_floor,
                resident_registration=args.resident_registration,
                resident_registration_max_shift=args.resident_registration_max_shift,
                resident_ncc_sample_stride=args.resident_ncc_sample_stride,
                resident_ncc_fallback_score_threshold=args.resident_ncc_fallback_score_threshold,
                resident_subpixel_radius_steps=args.resident_subpixel_radius_steps,
                resident_subpixel_step=args.resident_subpixel_step,
                resident_star_threshold=args.resident_star_threshold,
                resident_star_max_candidates=args.resident_star_max_candidates,
                resident_star_tolerance_px=args.resident_star_tolerance_px,
                resident_star_grid_cols=args.resident_star_grid_cols,
                resident_star_grid_rows=args.resident_star_grid_rows,
                resident_star_catalog_deterministic=args.resident_star_catalog_deterministic,
                resident_star_prior=args.resident_star_prior,
                resident_star_prior_radius_px=args.resident_star_prior_radius_px,
                resident_star_core_preselect_top_k=args.resident_star_core_preselect_top_k,
                resident_triangle_grid_top_per_cell=args.resident_triangle_grid_top_per_cell,
                resident_triangle_nms_scan_candidates=args.resident_triangle_nms_scan_candidates,
                resident_triangle_nms_min_separation_px=args.resident_triangle_nms_min_separation_px,
                resident_triangle_pixel_refine=args.resident_triangle_pixel_refine,
                resident_triangle_pixel_refine_coarse_stride=args.resident_triangle_pixel_refine_coarse_stride,
                resident_triangle_pixel_refine_final_stride=args.resident_triangle_pixel_refine_final_stride,
                resident_triangle_pixel_refine_fast_coarse=args.resident_triangle_pixel_refine_fast_coarse,
                resident_triangle_centroid_background=args.resident_triangle_centroid_background,
                resident_triangle_min_agreement_score=args.resident_triangle_min_agreement_score,
                resident_triangle_agreement_rms_scale=args.resident_triangle_agreement_rms_scale,
                resident_triangle_agreement_action=args.resident_triangle_agreement_action,
                resident_triangle_agreement_min_weight=args.resident_triangle_agreement_min_weight,
                resident_registration_motion_weighting=args.resident_registration_motion_weighting,
                resident_registration_motion_threshold_sigma=args.resident_registration_motion_threshold_sigma,
                resident_registration_motion_min_weight=args.resident_registration_motion_min_weight,
                resident_registration_motion_power=args.resident_registration_motion_power,
                resident_registration_motion_scale_floor_px=args.resident_registration_motion_scale_floor_px,
                resident_registration_quality_gate=args.resident_registration_quality_gate,
                resident_registration_quality_min_inliers=args.resident_registration_quality_min_inliers,
                resident_registration_quality_max_rms_px=args.resident_registration_quality_max_rms_px,
                resident_frame_weight_proposal=args.resident_frame_weight_proposal,
                resident_tile_local_policy_replay=args.resident_tile_local_policy_replay,
                resident_tile_local_policy_mode=args.resident_tile_local_policy_mode,
                resident_registration_results=args.resident_registration_results,
                resident_warp_interpolation=args.resident_warp_interpolation,
                resident_warp_clamping_threshold=args.resident_warp_clamping_threshold,
                resident_warp_batch_dispatch=args.resident_warp_batch_dispatch,
                resident_warp_chunk_capacity_frames=getattr(
                    args,
                    "_resident_warp_chunk_capacity_frames",
                    None,
                ),
                resident_integration_dispatch=args.resident_integration_dispatch,
                reference_frame_id=args.reference_frame_id,
                exclude_frame_ids=args.exclude_frame_id,
                local_normalization=args.local_normalization,
                resident_local_normalization_mode=args.resident_local_normalization_mode,
                resident_local_normalization_tile_size=args.resident_local_normalization_tile_size,
                resident_prefetch_frames=args.resident_prefetch_frames,
                resident_prefetch_workers=args.resident_prefetch_workers,
                resident_prefetch_refill_mode=args.resident_prefetch_refill_mode,
                resident_h2d_mode=args.resident_h2d_mode,
                resident_calibration_batch_frames=args.resident_calibration_batch_frames,
                resident_calibration_streams=args.resident_calibration_streams,
                resident_calibration_wave_frames=args.resident_calibration_wave_frames,
                resident_calibration_release_mode=args.resident_calibration_release_mode,
                resident_master_cache_dir=args.resident_master_cache_dir,
                resident_output_maps=args.resident_output_maps,
                resident_inline_source_dq=args.resident_inline_source_dq,
                resident_inline_source_dq_hot_sigma=args.resident_inline_source_dq_hot_sigma,
                resident_inline_source_dq_cold_sigma=args.resident_inline_source_dq_cold_sigma,
                resident_winsorized_mode=args.resident_winsorized_mode,
                resident_fits_read_mode=args.resident_fits_read_mode,
                resident_fits_read_mode_resolution=args._resident_fits_read_mode_resolution,
            ),
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_memory_admission",
                path=str(resident_memory_admission_path),
                format="json",
                created_at=now_iso(),
                source_frames=[],
            )
        )
        if "resident_memory_admission" not in state.completed_stages:
            state.completed_stages.insert(0, "resident_memory_admission")
    elif plan.executable:
        try:
            state = _run_full_pipeline(
                plan_path,
                out,
                args.backend,
                args.tile_size,
                args.local_normalization,
                args.integration_weighting,
                args.integration_rejection,
                registration_method=args.registration_method,
                warp_interpolation=args.warp_interpolation,
                timing=timing,
            )
        except RegistrationAdmissionBlocked as exc:
            console.print({"status": "failed", "stage": "registration", "error": str(exc), "run": str(out)})
            return 2
    else:
        state = initialize_run(out)
        state.warnings.append("processing plan is not executable; audit stopped after scan and plan")
    state.completed_stages.insert(0, "plan")
    state.completed_stages.insert(0, "scan")
    state.completed_stages.append("report")
    state.current_stage = "report"
    write_run_state(out, state)
    _timed_stage(out, timing, "report", lambda: _write_run_report(out, report_path, manifest_path, plan_path))
    console.print(f"Audit complete: {out}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    capabilities = capability_report()
    _resolve_execution_defaults(args, capabilities, command="run")
    if args.backend == "cuda" and not capabilities["cuda_available"]:
        raise SystemExit("CUDA backend requested but native CUDA backend is unavailable.")
    _apply_resident_runtime_preset(args)
    _resolve_resident_fits_read_mode_default(args, command="run")
    _seed_run_inputs(Path(args.out), args.plan)
    _write_run_command(Path(args.out), args)
    if args.memory_mode == "resident":
        if args.backend != "cuda":
            raise SystemExit("Resident memory mode currently requires --backend cuda.")
        if args.until_stage != "integration":
            raise SystemExit("Resident memory mode currently supports --until-stage integration only.")
        if args.integration_rejection not in {"auto", "none", "sigma_clip", "winsorized_sigma"}:
            raise SystemExit(
                "Resident memory mode currently supports --integration-rejection none, "
                "sigma_clip, or winsorized_sigma."
            )
        if args.integration_weighting not in {"auto", "none", "simple_snr"}:
            raise SystemExit("Resident memory mode currently supports --integration-weighting none or simple_snr.")
        out = Path(args.out)
        timing = _new_timing("run", args.backend, None)
        _annotate_timing_execution_defaults(timing, args)
        try:
            resident_memory_admission_path = _timed_stage(
                out,
                timing,
                "resident_memory_admission",
                lambda: _write_resident_memory_admission(out, args),
            )
        except ResidentMemoryAdmissionBlocked as exc:
            _write_resident_memory_admission_failed_state(out, exc)
            console.print({"status": "failed", "stage": "resident_memory_admission", "error": str(exc)})
            return 2
        source_dq_strategy_path = _write_resident_source_dq_strategy(out, args)
        source_dq_cache_route_path: Path | None = None
        if args.resident_source_dq_cache == "generate-calibration":
            preflight = _resident_source_dq_cache_preflight(
                args.plan,
                out,
                max_disk_fraction=args.resident_source_dq_cache_max_disk_fraction,
            )
            write_json(out / "resident_source_dq_cache_preflight.json", preflight)
            if not preflight["passed"] and not args.allow_large_resident_source_dq_cache:
                raise SystemExit(
                    "resident source-DQ cache preflight failed: "
                    f"{preflight['reason']}; estimated_output_bytes={preflight['estimated_output_bytes']}, "
                    f"max_allowed_bytes={preflight['max_allowed_bytes']}. "
                    "Use --allow-large-resident-source-dq-cache to override."
                )
            _timed_stage(
                out,
                timing,
                "resident_source_dq_cache_calibration",
                lambda: run_calibration_stages(
                    args.plan,
                    args.out,
                    backend="cpu",
                    tile_size=args.tile_size,
                    flat_floor=args.flat_floor,
                ),
            )
            source_dq_cache_route_path = _write_resident_source_dq_cache_route(out, args)
        state = _timed_stage(
            out,
            timing,
            "resident_calibration_integration",
            lambda: run_resident_calibration_integration(
                args.plan,
                args.out,
                integration_weighting=args.integration_weighting,
                integration_rejection=args.integration_rejection,
                flat_floor=args.flat_floor,
                resident_registration=args.resident_registration,
                resident_registration_max_shift=args.resident_registration_max_shift,
                resident_ncc_sample_stride=args.resident_ncc_sample_stride,
                resident_ncc_fallback_score_threshold=args.resident_ncc_fallback_score_threshold,
                resident_subpixel_radius_steps=args.resident_subpixel_radius_steps,
                resident_subpixel_step=args.resident_subpixel_step,
                resident_star_threshold=args.resident_star_threshold,
                resident_star_max_candidates=args.resident_star_max_candidates,
                resident_star_tolerance_px=args.resident_star_tolerance_px,
                resident_star_grid_cols=args.resident_star_grid_cols,
                resident_star_grid_rows=args.resident_star_grid_rows,
                resident_star_catalog_deterministic=args.resident_star_catalog_deterministic,
                resident_star_prior=args.resident_star_prior,
                resident_star_prior_radius_px=args.resident_star_prior_radius_px,
                resident_star_core_preselect_top_k=args.resident_star_core_preselect_top_k,
                resident_triangle_grid_top_per_cell=args.resident_triangle_grid_top_per_cell,
                resident_triangle_nms_scan_candidates=args.resident_triangle_nms_scan_candidates,
                resident_triangle_nms_min_separation_px=args.resident_triangle_nms_min_separation_px,
                resident_triangle_pixel_refine=args.resident_triangle_pixel_refine,
                resident_triangle_pixel_refine_coarse_stride=args.resident_triangle_pixel_refine_coarse_stride,
                resident_triangle_pixel_refine_final_stride=args.resident_triangle_pixel_refine_final_stride,
                resident_triangle_pixel_refine_fast_coarse=args.resident_triangle_pixel_refine_fast_coarse,
                resident_triangle_centroid_background=args.resident_triangle_centroid_background,
                resident_triangle_min_agreement_score=args.resident_triangle_min_agreement_score,
                resident_triangle_agreement_rms_scale=args.resident_triangle_agreement_rms_scale,
                resident_triangle_agreement_action=args.resident_triangle_agreement_action,
                resident_triangle_agreement_min_weight=args.resident_triangle_agreement_min_weight,
                resident_registration_motion_weighting=args.resident_registration_motion_weighting,
                resident_registration_motion_threshold_sigma=args.resident_registration_motion_threshold_sigma,
                resident_registration_motion_min_weight=args.resident_registration_motion_min_weight,
                resident_registration_motion_power=args.resident_registration_motion_power,
                resident_registration_motion_scale_floor_px=args.resident_registration_motion_scale_floor_px,
                resident_registration_quality_gate=args.resident_registration_quality_gate,
                resident_registration_quality_min_inliers=args.resident_registration_quality_min_inliers,
                resident_registration_quality_max_rms_px=args.resident_registration_quality_max_rms_px,
                resident_frame_weight_proposal=args.resident_frame_weight_proposal,
                resident_tile_local_policy_replay=args.resident_tile_local_policy_replay,
                resident_tile_local_policy_mode=args.resident_tile_local_policy_mode,
                resident_registration_results=args.resident_registration_results,
                resident_warp_interpolation=args.resident_warp_interpolation,
                resident_warp_clamping_threshold=args.resident_warp_clamping_threshold,
                resident_warp_batch_dispatch=args.resident_warp_batch_dispatch,
                resident_warp_chunk_capacity_frames=getattr(
                    args,
                    "_resident_warp_chunk_capacity_frames",
                    None,
                ),
                resident_integration_dispatch=args.resident_integration_dispatch,
                reference_frame_id=args.reference_frame_id,
                exclude_frame_ids=args.exclude_frame_id,
                local_normalization=args.local_normalization,
                resident_local_normalization_mode=args.resident_local_normalization_mode,
                resident_local_normalization_tile_size=args.resident_local_normalization_tile_size,
                resident_prefetch_frames=args.resident_prefetch_frames,
                resident_prefetch_workers=args.resident_prefetch_workers,
                resident_prefetch_refill_mode=args.resident_prefetch_refill_mode,
                resident_h2d_mode=args.resident_h2d_mode,
                resident_calibration_batch_frames=args.resident_calibration_batch_frames,
                resident_calibration_streams=args.resident_calibration_streams,
                resident_calibration_wave_frames=args.resident_calibration_wave_frames,
                resident_calibration_release_mode=args.resident_calibration_release_mode,
                resident_master_cache_dir=args.resident_master_cache_dir,
                resident_output_maps=args.resident_output_maps,
                resident_inline_source_dq=args.resident_inline_source_dq,
                resident_inline_source_dq_hot_sigma=args.resident_inline_source_dq_hot_sigma,
                resident_inline_source_dq_cold_sigma=args.resident_inline_source_dq_cold_sigma,
                resident_winsorized_mode=args.resident_winsorized_mode,
                resident_fits_read_mode=args.resident_fits_read_mode,
                resident_fits_read_mode_resolution=args._resident_fits_read_mode_resolution,
            ),
        )
        if source_dq_cache_route_path is not None:
            if "resident_source_dq_cache_calibration" not in state.completed_stages:
                state.completed_stages.insert(0, "resident_source_dq_cache_calibration")
            state.artifacts.append(
                PipelineArtifact(
                    stage="resident_source_dq_cache",
                    path=str(source_dq_cache_route_path),
                    format="json",
                    created_at=now_iso(),
                    source_frames=[],
                )
            )
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_memory_admission",
                path=str(resident_memory_admission_path),
                format="json",
                created_at=now_iso(),
                source_frames=[],
            )
        )
        if "resident_memory_admission" not in state.completed_stages:
            state.completed_stages.insert(0, "resident_memory_admission")
        state.artifacts.append(
            PipelineArtifact(
                stage="resident_source_dq_strategy",
                path=str(source_dq_strategy_path),
                format="json",
                created_at=now_iso(),
                source_frames=[],
            )
        )
        write_run_state(args.out, state)
        console.print(f"Resident CUDA run complete through {state.current_stage}: {args.out}")
        return 0
    implemented_stages = {
        "master_calibration",
        "light_calibration",
        "calibration",
        "quality",
        "registration",
        "warp",
        "local_normalization",
        "integration",
    }
    if args.until_stage not in implemented_stages:
        if args.allow_partial:
            console.print("Only calibration stages are implemented; initializing partial run state.")
        else:
            raise SystemExit(
                "Current gated runner supports --until-stage calibration, quality, registration, warp, "
                "local_normalization, or integration only. "
                "Use --allow-partial to write a diagnostic run_state without executing later stages."
            )
    if args.until_stage in implemented_stages:
        out = Path(args.out)
        timing = _new_timing("run", args.backend, args.tile_size)
        _annotate_timing_execution_defaults(timing, args)
        try:
            state = _run_pipeline_until_stage(args, out, timing)
        except RegistrationAdmissionBlocked as exc:
            console.print({"status": "failed", "stage": "registration", "error": str(exc), "run": str(out)})
            return 2
        write_run_state(args.out, state)
        console.print(f"Run complete through {state.current_stage}: {args.out}")
        return 0
    out = Path(args.out)
    state = initialize_run(out)
    state.current_stage = args.until_stage or "created"
    state.warnings.append("full pipeline execution is gated; current implementation stops after planning")
    write_run_state(out, state)
    console.print("Run state initialized. Full execution is implemented in later gates.")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    run = Path(args.run)
    plan_path = run / "processing_plan.json"
    manifest_path = run / "manifest.json"
    if (run / "integration_results.json").exists():
        console.print(resume_summary(args.run))
        console.print("Run already has integration_results.json; no stages repeated.")
        return 0
    if plan_path.exists():
        plan = read_json(plan_path)
        if not plan.get("executable", False):
            console.print(resume_summary(args.run))
            console.print("Processing plan is not executable; nothing to resume.")
            return 0
        timing = _new_timing("resume", "auto", 512)
        try:
            state = _resume_pipeline(plan_path, run, "auto", 512, timing)
        except RegistrationAdmissionBlocked as exc:
            console.print({"status": "failed", "stage": "registration", "error": str(exc), "run": str(run)})
            return 2
        state.completed_stages.insert(0, "plan")
        if manifest_path.exists():
            state.completed_stages.insert(0, "scan")
        state.completed_stages.append("report")
        state.current_stage = "report"
        write_run_state(run, state)
        _write_run_report(run, run / "report.html", manifest_path, plan_path)
        console.print(f"Resume complete: {run}")
        return 0
    console.print(resume_summary(args.run))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    comparison = compare_fits(
        args.glass,
        args.reference,
        glass_time_seconds=args.glass_time_seconds,
        reference_time_seconds=args.reference_time_seconds,
        glass_label=args.glass_label,
        reference_label=args.reference_label,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        clip_low=args.clip_low,
        clip_high=args.clip_high,
        diagnostics_dir=args.diagnostics_dir,
        diagnostic_max_size=args.diagnostic_max_size,
        hotspot_tile_size=args.hotspot_tile_size,
        ignore_border_px=args.ignore_border_px,
        glass_coverage_map=args.glass_coverage_map,
        min_coverage=args.min_coverage,
    )
    write_json(Path(args.out).with_suffix(".json"), comparison)
    write_compare_report(args.out, comparison)
    console.print(f"Wrote compare report: {args.out}")
    return 0


def cmd_compare_outliers(args: argparse.Namespace) -> int:
    payload = build_compare_outlier_audit(
        args.glass,
        args.reference,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        clip_low=args.clip_low,
        clip_high=args.clip_high,
        glass_coverage_map=args.glass_coverage_map,
        min_coverage=args.min_coverage,
        ignore_border_px=args.ignore_border_px,
        tail_percentile=args.tail_percentile,
        target_abs_diff=args.target_abs_diff,
        tile_size=args.tile_size,
        top_tiles=args.top_tiles,
        top_pixels=args.top_pixels,
        edge_band_px=args.edge_band_px,
    )
    write_compare_outlier_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload.get("status"),
            "tail_pixels": (payload.get("tail") or {}).get("pixels") if isinstance(payload.get("tail"), dict) else None,
            "target_pixels": (payload.get("target_exceedance") or {}).get("pixels")
            if isinstance(payload.get("target_exceedance"), dict)
            else None,
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_compare_tile_pack(args: argparse.Namespace) -> int:
    manifest = build_compare_tile_pack(
        args.audit,
        args.out_dir,
        max_tiles=args.max_tiles,
        pad_px=args.pad_px,
        include_png=not args.no_png,
        preview_max_size=args.preview_max_size,
    )
    console.print(
        {
            "status": "completed",
            "tile_count": manifest.get("tile_count"),
            "manifest": str(Path(args.out_dir) / "tile_pack_manifest.json"),
        }
    )
    return 0


def cmd_compare_tile_attribution(args: argparse.Namespace) -> int:
    payload = build_compare_tile_attribution(
        args.tile_pack,
        args.run,
        filter_name=args.filter,
        frame_limit=args.frame_limit,
    )
    write_compare_tile_attribution(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": "completed",
            "tile_count": payload.get("tile_count"),
            "downweighted_count": (payload.get("frame_accounting") or {}).get("downweighted_count")
            if isinstance(payload.get("frame_accounting"), dict)
            else None,
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_compare_tile_replay(args: argparse.Namespace) -> int:
    payload = build_compare_tile_replay(
        args.tile_pack,
        args.run,
        filter_name=args.filter,
        master_cache_dir=args.master_cache_dir,
        frame_strategy=args.frame_strategy,
        max_frames=args.max_frames,
        low_sigma=args.low_sigma,
        high_sigma=args.high_sigma,
        replay_interpolation=args.replay_interpolation,
    )
    write_compare_tile_replay(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": "completed",
            "tile_count": payload.get("tile_count"),
            "selected_frame_count": payload.get("selected_frame_count"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_compare_tile_integration(args: argparse.Namespace) -> int:
    payload = build_compare_tile_integration_audit(
        args.tile_pack,
        args.run,
        filter_name=args.filter,
        master_cache_dir=args.master_cache_dir,
        frame_strategy=args.frame_strategy,
        max_frames=args.max_frames,
        max_tiles=args.max_tiles,
        low_sigma=args.low_sigma,
        high_sigma=args.high_sigma,
        rejection=args.rejection,
        replay_interpolation=args.replay_interpolation,
        focus_frames=args.focus_frame or None,
        focus_range_start=args.focus_range_start,
        focus_range_end=args.focus_range_end,
        control_frames=args.control_frame or None,
        control_before=args.control_before,
        control_after=args.control_after,
    )
    write_compare_tile_integration_audit(args.out, payload, markdown=args.markdown)
    contrast = payload.get("focus_vs_control") if isinstance(payload.get("focus_vs_control"), dict) else {}
    contribution = (
        contrast.get("tile_normalized_delta_contribution_sum")
        if isinstance(contrast.get("tile_normalized_delta_contribution_sum"), dict)
        else {}
    )
    console.print(
        {
            "status": "completed",
            "tile_count": payload.get("tile_count"),
            "selected_frame_count": payload.get("selected_frame_count"),
            "focus_frame_count": len(payload.get("focus_ids") or []),
            "focus_minus_control_contribution_mean": contribution.get("focus_minus_control"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_residual_tile_candidates(args: argparse.Namespace) -> int:
    payload = build_residual_tile_candidates(
        args.outlier_audit,
        known_tile_packs=args.known_tile_pack,
        max_tiles=args.max_tiles,
        min_tail_pixels=args.min_tail_pixels,
        min_tail_fraction=args.min_tail_fraction,
        prefer=args.prefer,
        drop_overlaps=not args.allow_overlaps,
        known_overlap_mode=args.known_overlap_mode,
    )
    write_residual_tile_candidates(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "selected_tiles": summary.get("selected_tile_count"),
            "new_regions": summary.get("selected_new_region_count"),
            "known_overlaps": summary.get("selected_known_overlap_count"),
            "recommendation": summary.get("recommendation"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_frame_weight_proposal(args: argparse.Namespace) -> int:
    payload = build_frame_weight_proposal(
        args.integration_audit,
        method=args.method,
        min_multiplier=args.min_multiplier,
        max_multiplier=args.max_multiplier,
        reason=args.reason,
    )
    write_frame_weight_proposal(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload.get("status"),
            "frame_count": len(payload.get("frame_multipliers") or []),
            "proposed_multiplier": payload.get("proposed_multiplier"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_frame_weight_proposal_audit(args: argparse.Namespace) -> int:
    payload = build_frame_weight_proposal_audit(
        args.integration_audit,
        args.proposal,
        tile_pack=args.tile_pack,
        glass_scale=args.glass_scale,
    )
    write_frame_weight_proposal_audit(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "recommendation": summary.get("recommendation"),
            "mean_toward": summary.get("mean_moves_toward_reference"),
            "mean_away": summary.get("mean_moves_away_from_reference"),
            "tail_toward": summary.get("tail_moves_toward_reference"),
            "tail_away": summary.get("tail_moves_away_from_reference"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_compare_frame_family(args: argparse.Namespace) -> int:
    payload = build_compare_frame_family_audit(
        args.replay,
        args.run,
        focus_frames=args.focus_frame or None,
        focus_range_start=args.focus_range_start,
        focus_range_end=args.focus_range_end,
        control_frames=args.control_frame or None,
        control_before=args.control_before,
        control_after=args.control_after,
    )
    write_compare_frame_family_audit(args.out, payload, markdown=args.markdown)
    contrast = payload.get("focus_vs_control") if isinstance(payload.get("focus_vs_control"), dict) else {}
    weighted_delta = contrast.get("weighted_delta_mean") if isinstance(contrast.get("weighted_delta_mean"), dict) else {}
    console.print(
        {
            "status": "completed",
            "focus_frame_count": len(payload.get("focus_ids") or []),
            "control_frame_count": len(payload.get("control_ids") or []),
            "top_focus_frame": (payload.get("interpretation") or {}).get("top_focus_frame")
            if isinstance(payload.get("interpretation"), dict)
            else None,
            "weighted_delta_focus_minus_control": weighted_delta.get("focus_minus_control"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_resident_tile_capture(args: argparse.Namespace) -> int:
    payload = build_resident_tile_capture(
        args.tile_pack,
        args.run,
        args.out_dir,
        replay_json=args.replay,
        filter_name=args.filter,
        frame_ids=args.frame_id or None,
        frame_range_start=args.frame_range_start,
        frame_range_end=args.frame_range_end,
        max_frames=args.max_frames,
        max_tiles=args.max_tiles,
        master_cache_dir=args.master_cache_dir,
        interpolation=args.interpolation,
        clamping_threshold=args.clamping_threshold,
        write_tiles=args.write_tiles,
    )
    write_resident_tile_capture(args.out, payload, markdown=args.markdown)
    first_summary = payload.get("tile_summaries", [{}])[0] if payload.get("tile_summaries") else {}
    resident = (
        first_summary.get("resident_weighted_delta_mean")
        if isinstance(first_summary, dict)
        and isinstance(first_summary.get("resident_weighted_delta_mean"), dict)
        else {}
    )
    diff = (
        first_summary.get("resident_minus_cpu_weighted_delta_mean")
        if isinstance(first_summary, dict)
        and isinstance(first_summary.get("resident_minus_cpu_weighted_delta_mean"), dict)
        else {}
    )
    console.print(
        {
            "status": "completed",
            "selected_frame_count": payload.get("selected_frame_count"),
            "tile_count": payload.get("tile_count"),
            "first_tile_resident_weighted_delta_mean": resident.get("mean"),
            "first_tile_resident_minus_cpu_mean": diff.get("mean"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_resident_tile_contribution(args: argparse.Namespace) -> int:
    payload = build_resident_tile_contribution(
        args.tile_pack,
        args.run,
        filter_name=args.filter,
        frame_strategy=args.frame_strategy,
        max_frames=args.max_frames,
        max_tiles=args.max_tiles,
        master_cache_dir=args.master_cache_dir,
        interpolation=args.interpolation,
        clamping_threshold=args.clamping_threshold,
        rejection=args.rejection,
        low_sigma=args.low_sigma,
        high_sigma=args.high_sigma,
        focus_frames=args.focus_frame or None,
        focus_range_start=args.focus_range_start,
        focus_range_end=args.focus_range_end,
        control_frames=args.control_frame or None,
        control_before=args.control_before,
        control_after=args.control_after,
    )
    write_resident_tile_contribution(args.out, payload, markdown=args.markdown)
    focus = payload.get("focus_summary") if isinstance(payload.get("focus_summary"), dict) else {}
    contribution = (
        focus.get("tile_normalized_delta_contribution_sum")
        if isinstance(focus.get("tile_normalized_delta_contribution_sum"), dict)
        else {}
    )
    console.print(
        {
            "status": "completed",
            "selected_frame_count": payload.get("selected_frame_count"),
            "tile_count": payload.get("tile_count"),
            "focus_contribution_mean": contribution.get("mean"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_policy_proposal(args: argparse.Namespace) -> int:
    payload = build_tile_local_policy_proposal(
        args.contribution,
        tile_pack=args.tile_pack,
        target_group=args.target_group,
        residual_stat=args.residual_stat,
        min_multiplier=args.min_multiplier,
        max_multiplier=args.max_multiplier,
        glass_scale=args.glass_scale,
    )
    write_tile_local_policy_proposal(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "recommendation": summary.get("recommendation"),
            "toward": summary.get("moves_toward_reference"),
            "away": summary.get("moves_away_from_reference"),
            "boost_tiles": summary.get("boost_tiles"),
            "clamped_tiles": summary.get("clamped_tiles"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_frame_family_search(args: argparse.Namespace) -> int:
    payload = build_tile_local_frame_family_search(
        args.contribution,
        tile_pack=args.tile_pack,
        residual_stat=args.residual_stat,
        min_multiplier=args.min_multiplier,
        max_multiplier=args.max_multiplier,
        glass_scale=args.glass_scale,
        window_sizes=args.window_size or [1, 3, 5, 11],
        stride=args.stride,
        top_n=args.top_n,
    )
    write_tile_local_frame_family_search(args.out, payload, markdown=args.markdown)
    top = payload.get("top_candidate") if isinstance(payload.get("top_candidate"), dict) else {}
    top_summary = top.get("summary") if isinstance(top.get("summary"), dict) else {}
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "candidate_count": payload.get("candidate_count"),
            "top_candidate": top.get("candidate_id"),
            "top_reduction": top_summary.get("total_abs_residual_reduction"),
            "top_mean_abs_after": top_summary.get("mean_abs_residual_after"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_residual_source_audit(args: argparse.Namespace) -> int:
    payload = build_tile_local_residual_source_audit(
        args.contribution,
        tile_pack=args.tile_pack,
        frame_family_search=args.frame_family_search,
        residual_stat=args.residual_stat,
        high_rejection_excess_threshold=args.high_rejection_excess_threshold,
        min_coverage_fraction=args.min_coverage_fraction,
    )
    write_tile_local_residual_source_audit(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "recommendation": summary.get("recommendation"),
            "coverage_below_threshold_tiles": summary.get("coverage_below_threshold_tiles"),
            "focus_high_rejection_excess_tiles": summary.get("focus_high_rejection_excess_tiles"),
            "top_frame_family_explained_fraction": summary.get("top_frame_family_explained_fraction"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_rejection_registration_audit(args: argparse.Namespace) -> int:
    payload = build_tile_local_rejection_registration_audit(
        args.contribution,
        frame_family_search=args.frame_family_search,
        high_rejection_threshold=args.high_rejection_threshold,
        low_agreement_score_threshold=args.low_agreement_score_threshold,
        top_n=args.top_n,
    )
    write_tile_local_rejection_registration_audit(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "recommendation": summary.get("recommendation"),
            "focus_minus_control_high_rejection": summary.get("focus_minus_control_high_rejected_fraction_mean"),
            "high_rejection_excess_frames": summary.get("high_rejection_excess_frame_count"),
            "low_agreement_high_rejection_frames": summary.get("low_agreement_high_rejection_frame_count"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_rejection_registration_plan(args: argparse.Namespace) -> int:
    payload = build_tile_local_rejection_registration_plan(
        args.audit,
        root=args.root,
        base_run_command=args.base_run_command,
        reference=args.reference,
        manifest=args.manifest,
        wbpp_result=args.wbpp_result,
        benchmark_contract=args.benchmark_contract,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        min_coverage=args.min_coverage,
        soft_agreement_score=args.soft_agreement_score,
        strict_agreement_score=args.strict_agreement_score,
        exclude_top_count=args.exclude_top_count,
    )
    write_tile_local_rejection_registration_plan(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "candidate_count": payload.get("candidate_count"),
            "hotspot_frames": payload.get("hotspot_frames"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_candidate_comparison(args: argparse.Namespace) -> int:
    payload = build_candidate_comparison(
        baseline_run=args.baseline_run,
        candidate_run=args.candidate_run,
        candidate_id=args.candidate_id,
        baseline_compare_json=args.baseline_compare_json,
        candidate_compare_json=args.candidate_compare_json,
        candidate_vs_baseline_json=args.candidate_vs_baseline_json,
        baseline_acceptance_json=args.baseline_acceptance_json,
        candidate_acceptance_json=args.candidate_acceptance_json,
        max_reference_rms_growth=args.max_reference_rms_growth,
        max_reference_p99_growth=args.max_reference_p99_growth,
        max_candidate_vs_baseline_rms=args.max_candidate_vs_baseline_rms,
        min_speedup_vs_reference=args.min_speedup_vs_reference,
    )
    write_candidate_comparison(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": summary.get("status"),
            "recommendation": summary.get("recommendation"),
            "candidate_elapsed_s": summary.get("candidate_elapsed_s"),
            "elapsed_ratio_candidate_over_baseline": summary.get("elapsed_ratio_candidate_over_baseline"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failed and not summary.get("passed") else 0


def cmd_candidate_comparison_sweep(args: argparse.Namespace) -> int:
    payload = build_candidate_comparison_sweep(args.comparison)
    write_candidate_comparison_sweep(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": summary.get("status"),
            "recommendation": summary.get("recommendation"),
            "candidate_count": summary.get("candidate_count"),
            "passed_candidate_count": summary.get("passed_candidate_count"),
            "top_candidate_id": summary.get("top_candidate_id"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_no_passed and not summary.get("passed") else 0


def cmd_candidate_runtime_sweep_plan(args: argparse.Namespace) -> int:
    payload = build_candidate_runtime_sweep_plan(
        args.comparison,
        root=args.root,
        base_run_command=args.base_run_command,
        baseline_run=args.baseline_run,
        baseline_compare_json=args.baseline_compare_json,
        reference=args.reference,
        manifest=args.manifest,
        wbpp_result=args.wbpp_result,
        benchmark_contract=args.benchmark_contract,
        benchmark_contract_profile=args.benchmark_contract_profile,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        min_coverage=args.min_coverage,
        min_speedup_vs_reference=args.min_speedup_vs_reference,
        variants=args.variant,
        prefetch_frames=args.prefetch_frame,
        prefetch_workers=args.prefetch_worker,
    )
    write_candidate_runtime_sweep_plan(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "variant_count": payload.get("variant_count"),
            "source_candidate_id": payload.get("source_candidate_id"),
            "recommendation": payload.get("recommendation"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_resident_ab_matrix_plan(args: argparse.Namespace) -> int:
    payload = build_resident_ab_matrix_plan(
        root=args.root,
        plan=args.plan,
        manifest=args.manifest,
        wbpp_result=args.wbpp_result,
        reference=args.reference,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        min_coverage=args.min_coverage,
        min_speedup=args.min_speedup,
        reference_frame_id=args.reference_frame_id,
        output_maps=args.resident_output_maps,
        min_gpu_free_mib=args.min_gpu_free_mib,
        max_gpu_utilization=args.max_gpu_utilization,
        min_disk_free_gib=args.min_disk_free_gib,
        benchmark_contract_profile=args.benchmark_contract_profile,
        probe_gpu=not args.skip_gpu_probe,
    )
    write_resident_ab_matrix_plan(args.out, payload, markdown=args.markdown)
    readiness = payload.get("readiness") if isinstance(payload.get("readiness"), dict) else {}
    gpu = readiness.get("gpu") if isinstance(readiness.get("gpu"), dict) else {}
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "variant_count": payload.get("variant_count"),
            "ready_to_execute": payload.get("ready_to_execute"),
            "recommendation": payload.get("recommendation"),
            "gpu_status": gpu.get("status"),
            "gpu_utilization": gpu.get("utilization_percent"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_resident_ab_matrix_execute(args: argparse.Namespace) -> int:
    current_glass_executable = sys.argv[0] if Path(sys.argv[0]).name.lower().startswith("glass") else None
    payload = build_resident_ab_matrix_execution(
        args.plan,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
        variants=args.variant,
        ignore_readiness=args.ignore_readiness,
        recheck_readiness=not args.no_readiness_recheck,
        wait_ready_timeout_s=args.wait_ready_timeout_s,
        wait_ready_interval_s=args.wait_ready_interval_s,
        wait_ready_consecutive_samples=args.wait_ready_consecutive_samples,
        glass_executable=args.glass_executable or current_glass_executable,
        python_executable=args.python_executable or sys.executable,
        cwd=args.cwd,
    )
    write_resident_ab_matrix_execution(args.out, payload)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": summary.get("status"),
            "blocked": summary.get("blocked"),
            "failed": summary.get("failed"),
            "recorded_variant_count": summary.get("recorded_variant_count"),
            "out": args.out,
        }
    )
    if args.fail_on_failed and summary.get("failed"):
        return 2
    if args.fail_on_blocked and summary.get("blocked"):
        return 3
    return 0


def cmd_candidate_runtime_sweep_execute(args: argparse.Namespace) -> int:
    payload = build_candidate_runtime_sweep_execution(
        args.plan,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
        variants=args.variant,
        start_at=args.start_at,
        stop_after=args.stop_after,
        run_sweep_summary=not args.no_sweep_summary,
        glass_executable=args.glass_executable,
        cwd=args.cwd,
    )
    write_candidate_runtime_sweep_execution(args.out, payload)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": summary.get("status"),
            "completed_variant_count": summary.get("completed_variant_count"),
            "skipped_existing_count": summary.get("skipped_existing_count"),
            "out": args.out,
        }
    )
    return 2 if args.fail_on_failed and summary.get("failed") else 0


def cmd_tile_local_policy_replay(args: argparse.Namespace) -> int:
    payload = build_tile_local_policy_replay(args.contribution, args.proposal)
    write_tile_local_policy_replay(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "recommendation": summary.get("recommendation"),
            "toward": summary.get("moves_toward_reference"),
            "away": summary.get("moves_away_from_reference"),
            "mean_abs_residual_before": summary.get("mean_abs_residual_before"),
            "mean_abs_residual_after": summary.get("mean_abs_residual_after"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_policy_subset(args: argparse.Namespace) -> int:
    payload = build_tile_local_policy_subset(
        args.replay,
        strategy=args.strategy,
        max_tiles=args.max_tiles,
    )
    write_tile_local_policy_subset(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "selected_tiles": payload.get("tile_count"),
            "dropped_overlap_tiles": len(payload.get("dropped_overlap_tiles") or []),
            "recommendation": summary.get("recommendation"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_tile_local_apply_experiment(args: argparse.Namespace) -> int:
    payload = build_tile_local_apply_experiment(
        baseline_run=args.baseline_run,
        candidate_run=args.candidate_run,
        replay=args.replay,
        benchmark_contract=args.benchmark_contract,
        baseline_compare_json=args.baseline_compare_json,
        candidate_compare_json=args.candidate_compare_json,
        candidate_vs_baseline_json=args.candidate_vs_baseline_json,
    )
    write_tile_local_apply_experiment(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": summary.get("status"),
            "recommendation": summary.get("recommendation"),
            "required_failed_count": summary.get("required_failed_count"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failed and not summary.get("passed") else 0


def cmd_tile_local_apply_verify(args: argparse.Namespace) -> int:
    payload = build_tile_local_apply_verification(
        baseline=args.baseline,
        candidate=args.candidate,
        reference=args.reference,
        replay=args.replay,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        clip_low=args.clip_low,
        clip_high=args.clip_high,
        coverage_map=args.coverage_map,
        min_coverage=args.min_coverage,
        pad_px=args.pad_px,
    )
    write_tile_local_apply_verification(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": summary.get("status"),
            "recommendation": summary.get("recommendation"),
            "mean_abs_delta": summary.get("mean_abs_delta"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failed and not summary.get("passed") else 0


def cmd_tile_local_policy_decision(args: argparse.Namespace) -> int:
    payload = build_tile_local_policy_decision(
        args.verification,
        apply_experiment=args.apply_experiment,
        acceptance_audit=args.acceptance_audit,
        min_signed_fraction=args.min_signed_fraction,
        min_rms_fraction=args.min_rms_fraction,
        min_mean_abs_fraction=args.min_mean_abs_fraction,
        require_aggregate_mean_abs=not args.allow_aggregate_mean_abs_regression,
        require_aggregate_rms=not args.allow_aggregate_rms_regression,
    )
    write_tile_local_policy_decision(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": summary.get("status"),
            "recommendation": summary.get("recommendation"),
            "top_score": summary.get("top_score"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_rejected and not summary.get("accepted") else 0


def cmd_tile_local_policy_sweep(args: argparse.Namespace) -> int:
    payload = build_tile_local_policy_sweep(args.decision)
    write_tile_local_policy_sweep(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": summary.get("status"),
            "recommendation": summary.get("recommendation"),
            "accepted_decisions": summary.get("accepted_decision_count"),
            "top_score": summary.get("top_score"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_no_accepted and not summary.get("accepted_decision_count") else 0


def cmd_tile_local_sweep_plan(args: argparse.Namespace) -> int:
    payload = build_tile_local_sweep_plan(
        args.replay,
        root=args.root,
        max_tiles=args.max_tiles,
        strategy=args.strategy,
        candidate_prefix=args.candidate_prefix,
        base_run_command=args.base_run_command,
        reference=args.reference,
        baseline_run=args.baseline_run,
        baseline_master=args.baseline_master,
        baseline_compare_json=args.baseline_compare_json,
        wbpp_result=args.wbpp_result,
        benchmark_contract=args.benchmark_contract,
        manifest=args.manifest,
        glass_scale=args.glass_scale,
        glass_offset=args.glass_offset,
        min_coverage=args.min_coverage,
        existing_decisions=args.existing_decision,
    )
    write_tile_local_sweep_plan(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "candidate_count": payload.get("candidate_count"),
            "source_tile_count": payload.get("source_tile_count"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_speedup_summary(args: argparse.Namespace) -> int:
    summary = summarize_wbpp_speedup(
        args.glass_run,
        args.wbpp_result,
        compare_json=args.compare_json,
        min_speedup=args.min_speedup,
    )
    write_speedup_summary(args.out, summary, markdown=args.markdown)
    console.print(
        {
            "speedup_vs_wbpp": summary["speedup_vs_wbpp"],
            "meets_min_speedup": summary["meets_min_speedup"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_benchmark_contract_profile(args: argparse.Namespace) -> int:
    contract = build_resident_cuda_dq_benchmark_contract(
        name=args.name,
        min_lights=args.min_lights,
        min_bias=args.min_bias,
        min_dark=args.min_dark,
        min_flat=args.min_flat,
        min_active_frames=args.min_active_frames,
        min_speedup_vs_reference=args.min_speedup_vs_reference,
        release_baseline_elapsed_s=args.release_baseline_elapsed_s,
        max_runtime_regression_factor=args.max_runtime_regression_factor,
        min_coverage_fraction=args.min_coverage_fraction,
        max_rms_diff=args.max_rms_diff,
        max_abs_diff_p99=args.max_abs_diff_p99,
        require_resident_route=not args.no_resident_route,
        require_throughput_route=not args.no_throughput_route,
        dq_map_verify_tile_size=args.dq_map_verify_tile_size,
        count_map_verify_tile_size=args.count_map_verify_tile_size,
    )
    write_resident_cuda_dq_benchmark_contract(args.out, contract)
    console.print(
        {
            "profile": contract["profile"]["name"],
            "name": contract["name"],
            "out": args.out,
            "dq_provenance": "dq_provenance" in contract,
        }
    )
    return 0


def cmd_acceptance_audit(args: argparse.Namespace) -> int:
    if args.benchmark_contract and args.benchmark_contract_profile:
        raise SystemExit("--benchmark-contract and --benchmark-contract-profile are mutually exclusive")
    audit = build_acceptance_audit(
        manifest_path=args.manifest,
        glass_run=args.glass_run,
        wbpp_result=args.wbpp_result,
        compare_json=args.compare_json,
        min_lights=args.min_lights,
        min_bias=args.min_bias,
        min_dark=args.min_dark,
        min_flat=args.min_flat,
        min_active_frames=args.min_active_frames,
        min_speedup=args.min_speedup,
        min_coverage_fraction=args.min_coverage_fraction,
        max_rms_diff=args.max_rms_diff,
        max_abs_diff_p99=args.max_abs_diff_p99,
        benchmark_contract=args.benchmark_contract,
        benchmark_contract_profile=args.benchmark_contract_profile,
        resident_determinism_json=args.resident_determinism_json,
        resident_registration_fastpath_json=args.resident_registration_fastpath_json,
        contract_bundle_json=args.contract_bundle,
        pipeline_contract_json=args.pipeline_contract_json,
        stack_engine_contract_json=args.stack_engine_contract_json,
        warp_quality_contract_json=args.warp_quality_contract_json,
        require_warp_quality_contract=args.require_warp_quality_contract,
    )
    write_acceptance_audit(args.out, audit, markdown=args.markdown)
    console.print(
        {
            "status": audit["status"],
            "speedup_vs_wbpp": audit["speedup_summary"]["speedup_vs_wbpp"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if audit["passed"] else 2


def cmd_release_promotion_decision(args: argparse.Namespace) -> int:
    payload = build_release_promotion_decision(
        acceptance_audit=args.acceptance_audit,
        stack_engine_contract=args.stack_engine_contract,
        pipeline_contract=args.pipeline_contract,
        runtime_compare=args.runtime_compare,
        repeat_preflight=args.repeat_preflight,
        stack_engine_publication_audit=args.stack_engine_publication_audit,
        min_speedup=args.min_speedup,
        min_runtime_runs=args.min_runtime_runs,
        max_elapsed_ratio_vs_best=args.max_elapsed_ratio_vs_best,
        ignore_warmup_runs=args.ignore_warmup_runs,
    )
    write_release_promotion_decision(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "recommendation": payload["recommendation"],
            "release_candidate_ready": payload["release_candidate_ready"],
            "default_change_ready": payload["default_change_ready"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_not_ready) and not payload.get("default_change_ready"):
        return 2
    return 0 if payload.get("release_candidate_ready") else 2


def cmd_default_promotion_manifest(args: argparse.Namespace) -> int:
    payload = build_default_promotion_manifest(
        release_decision_json=args.release_decision,
        phase2_status_json=args.phase2_status,
        doctor_json=args.doctor_json,
        default_memory_mode=args.default_memory_mode,
        fallback_memory_mode=args.fallback_memory_mode,
        default_runtime_preset=args.default_runtime_preset,
        integration_engine=args.integration_engine,
        min_runtime_runs=args.min_runtime_runs,
        max_runtime_ratio=args.max_runtime_ratio,
        min_resident_lights=args.min_resident_lights,
        min_resident_winsorized_sweep_checks=args.min_resident_winsorized_sweep_checks,
        required_resident_winsorized_sweep_frame_count=(
            args.required_resident_winsorized_sweep_frame_count
        ),
        require_doctor=args.require_doctor,
    )
    write_default_promotion_manifest(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "recommendation": payload["recommendation"],
            "passed": payload["passed"],
            "default_memory_mode": payload["default_candidate"]["memory_mode"],
            "runtime_ratio": payload["runtime_repeat"]["elapsed_ratio_vs_best"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_not_ready) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_release_matrix(args: argparse.Namespace) -> int:
    payload = build_windows_release_matrix(
        doctor_json=args.doctor_json,
        release_decision_json=args.release_decision,
        acceptance_audit_json=args.acceptance_audit,
        default_promotion_manifest_json=args.default_promotion_manifest,
        default_runtime_preset=args.default_runtime_preset,
        require_cuda=not args.allow_cpu_only,
        require_default_change_ready=not args.allow_not_default_ready,
        require_default_promotion_ready=not args.allow_missing_default_promotion,
        expected_primary_package=args.expected_primary_package,
        max_runtime_ratio=args.max_runtime_ratio,
        min_resident_winsorized_sweep_checks=args.min_resident_winsorized_sweep_checks,
        required_resident_winsorized_sweep_frame_count=(
            args.required_resident_winsorized_sweep_frame_count
        ),
        require_direct_runtime_evidence=not args.allow_missing_direct_runtime_evidence,
    )
    write_windows_release_matrix(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "recommendation": payload["recommendation"],
            "passed": payload["passed"],
            "primary_package": payload["current_machine"]["primary_package"],
            "default_promotion_status": (
                payload.get("default_promotion_manifest") or {}
            ).get("status"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_not_ready) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_package_smoke(args: argparse.Namespace) -> int:
    payload = build_windows_package_smoke(
        package_root=args.package_root,
        zip_path=args.zip,
        expected_source=args.expected_source,
        expected_package_label=args.expected_package_label,
        require_cuda=args.require_cuda,
        execute=not args.skip_exec,
        timeout_s=args.timeout,
    )
    write_windows_package_smoke(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "recommendation": payload["recommendation"],
            "zip_size_bytes": payload["package"]["zip_size_bytes"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_package_build_plan(args: argparse.Namespace) -> int:
    package_labels = tuple(
        item.strip() for item in str(args.packages).split(",") if item.strip()
    )
    payload = build_windows_package_build_plan(
        release_root=args.release_root,
        cuda_base=args.cuda_base,
        package_labels=package_labels,
        toolkit_roots=parse_toolkit_root_specs(args.toolkit_root),
        python=args.python,
        configuration=args.configuration,
        static_cuda_runtime=not args.shared_cuda_runtime,
        require_all_toolkits=args.require_all_toolkits,
    )
    write_windows_package_build_plan(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "recommendation": payload["recommendation"],
            "ready_variants": payload["ready_variants"],
            "missing_cuda_variants": payload["missing_cuda_variants"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_missing) and payload.get("missing_cuda_variants"):
        return 2
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_package_suite(args: argparse.Namespace) -> int:
    required_labels = tuple(
        item.strip() for item in str(args.required_labels).split(",") if item.strip()
    )
    payload = build_windows_package_suite(
        smoke_artifacts=parse_labeled_paths(args.smoke),
        required_labels=required_labels,
        require_same_source_stamp=args.require_same_source_stamp,
    )
    write_windows_package_suite(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "recommendation": payload["recommendation"],
            "source_stamps": payload["source_stamps"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_release_manifest(args: argparse.Namespace) -> int:
    payload = build_windows_release_manifest(
        suite_artifact=args.suite,
        zip_overrides=parse_labeled_zip_paths(args.zip),
        require_same_source_stamp=args.require_same_source_stamp,
        windows_release_matrix=args.windows_release_matrix,
        require_windows_release_matrix=not args.allow_missing_windows_release_matrix,
    )
    write_windows_release_manifest(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "recommendation": payload["recommendation"],
            "packages": len(payload["packages"]),
            "windows_release_matrix_status": (
                payload.get("windows_release_matrix") or {}
            ).get("status"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_github_release_plan(args: argparse.Namespace) -> int:
    payload = build_windows_github_release_plan(
        manifest_artifact=args.manifest,
        tag=args.tag,
        title=args.title,
        notes_file=args.notes,
        draft=not args.no_draft,
        prerelease=args.prerelease,
        require_same_source_stamp=args.require_same_source_stamp,
        check_gh=args.check_gh,
        check_gh_auth=args.check_gh_auth,
        gh_path=args.gh_path,
        phase2_status=args.phase2_status,
        phase2_status_compare=args.phase2_status_compare,
        windows_release_matrix=args.windows_release_matrix,
        require_windows_release_matrix=not args.allow_missing_windows_release_matrix,
    )
    write_windows_github_release_plan(
        args.out,
        payload,
        markdown=args.markdown,
        notes=args.notes,
        script=args.script,
    )
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "publication_ready": payload["publication_ready"],
            "recommendation": payload["recommendation"],
            "tag": payload["release"]["tag"],
            "assets": len(payload["assets"]),
            "windows_release_matrix_status": (
                payload.get("release_matrix") or {}
            ).get("status"),
            "out": args.out,
            "markdown": args.markdown,
            "notes": args.notes,
            "script": args.script,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_windows_publish_preflight(args: argparse.Namespace) -> int:
    payload = build_windows_publish_preflight(
        release_manifest=args.release_manifest,
        github_release_plan=args.github_release_plan,
        windows_release_matrix=args.windows_release_matrix,
        default_promotion_manifest=args.default_promotion_manifest,
        require_publication_ready=not args.allow_not_publication_ready,
    )
    write_windows_publish_preflight(args.out, payload, markdown=args.markdown)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "recommendation": payload["recommendation"],
            "release_tag": summary.get("release_tag"),
            "asset_count": summary.get("asset_count"),
            "primary_package": summary.get("primary_package"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_stack_engine_publication_audit(args: argparse.Namespace) -> int:
    payload = build_stack_engine_publication_audit(
        stack_engine_contract=args.stack_engine_contract,
        phase2_status=args.phase2_status,
        default_promotion_manifest=args.default_promotion_manifest,
        windows_release_matrix=args.windows_release_matrix,
        github_release_plan=args.github_release_plan,
        publish_preflight=args.publish_preflight,
    )
    write_stack_engine_publication_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload["status"],
            "passed": payload["passed"],
            "recommendation": payload["recommendation"],
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_resident_determinism(args: argparse.Namespace) -> int:
    audit = build_resident_determinism_audit(args.baseline_run, args.candidate_run)
    write_resident_determinism_audit(args.out, audit, markdown=args.markdown)
    console.print(
        {
            "passed": audit["summary"]["passed"],
            "frame_signature_differences": audit["summary"]["frame_signature_difference_count"],
            "registration_differences": audit["summary"]["registration_difference_count"],
            "frame_accounting_differences": audit["summary"]["frame_accounting_difference_count"],
            "output_differences": audit["summary"]["output_difference_count"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_mismatch and not audit["summary"]["passed"] else 0


def cmd_resident_registration_audit(args: argparse.Namespace) -> int:
    audit = build_resident_registration_audit(args.run)
    write_resident_registration_audit(args.out, audit, markdown=args.markdown)
    console.print(
        {
            "status": audit["status"],
            "triangle_frames": audit["summary"]["triangle_frame_count"],
            "failed_triangle_frames": audit["summary"]["failed_triangle_frame_count"],
            "parse_errors": audit["summary"]["parse_error_count"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if args.fail_on_registration_failures and audit["summary"]["failed_triangle_frame_count"]:
        return 2
    return 0 if audit["passed"] else 2


def cmd_resident_registration_compare(args: argparse.Namespace) -> int:
    payload = build_resident_registration_compare(
        args.sweep_summary,
        audit_root=args.audit_root,
        audit_jsons=args.audit_json,
    )
    write_resident_registration_compare(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "variants": payload["variant_count"],
            "missing_audits": payload["missing_audit_count"],
            "compare_failed": payload["summary"]["compare_failed_count"],
            "recommendation": payload["recommendation"]["status"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_missing_audits and payload["missing_audit_count"] else 0


def cmd_resident_registration_matrix_compare(args: argparse.Namespace) -> int:
    payload = build_resident_registration_matrix_compare(
        args.baseline_registration,
        args.candidate_registration,
        baseline_label=args.baseline_label,
        candidate_label=args.candidate_label,
        max_translation_delta_px=args.max_translation_delta_px,
        max_matrix_delta_frobenius=args.max_matrix_delta_frobenius,
    )
    write_resident_registration_matrix_compare(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload["artifact_type"],
            "status": payload["status"],
            "passed": payload["passed"],
            "failed_checks": payload["failed_checks"],
            "recommendation": payload["recommendation"]["status"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload["passed"] else 0


def cmd_resident_registration_matrix_sweep(args: argparse.Namespace) -> int:
    payload = build_resident_registration_matrix_sweep(
        args.matrix_compare,
        parity_entries=args.parity_summary,
    )
    write_resident_registration_matrix_sweep(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload["artifact_type"],
            "variant_count": payload["variant_count"],
            "matrix_passed_count": payload["matrix_passed_count"],
            "parity_passed_count": payload["parity_passed_count"],
            "best_variant": payload["best_variant"],
            "recommendation": payload["recommendation"]["status"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def _label_path_pairs(values: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"run entries must use label=path format: {value}")
        label, path = value.split("=", 1)
        if not label:
            raise ValueError(f"run label is empty: {value}")
        if not path:
            raise ValueError(f"run path is empty: {value}")
        pairs.append((label, path))
    return pairs


def cmd_resident_runtime_compare(args: argparse.Namespace) -> int:
    payload = build_resident_runtime_compare(
        _label_path_pairs(args.run),
        baseline_label=args.baseline_label,
    )
    write_resident_runtime_compare(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "best_label": payload.get("summary", {}).get("best_label"),
            "best_elapsed_s": payload.get("summary", {}).get("best_elapsed_s"),
            "recommendation": payload.get("summary", {}).get("recommendation"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_resident_fits_auto_regression(args: argparse.Namespace) -> int:
    payload = build_resident_fits_auto_regression(
        args.run,
        compare_explicit=args.compare_explicit,
        compare_control=args.compare_control,
        explicit_run=args.explicit_run,
        control_run=args.control_run,
        min_lights=args.min_lights,
        expected_active=args.expected_active,
        expected_masked=args.expected_masked,
        expected_unknown_zero_weight=args.expected_unknown_zero_weight,
        expected_requested_mode=args.expected_requested_mode,
        expected_effective_mode=args.expected_effective_mode,
        expected_backend=args.expected_backend,
        expected_resolution_source=args.expected_resolution_source,
        max_rms_diff=args.max_rms_diff,
        max_abs_diff=args.max_abs_diff,
        max_total_vs_explicit_ratio=args.max_total_vs_explicit_ratio,
        max_total_vs_control_ratio=args.max_total_vs_control_ratio,
        max_light_bucket_vs_control_ratio=args.max_light_bucket_vs_control_ratio,
    )
    write_resident_fits_auto_regression(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload.get("passed") else 0


def cmd_resident_fits_default_matrix(args: argparse.Namespace) -> int:
    payload = build_resident_fits_default_matrix(args.cases)
    write_resident_fits_default_matrix(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "failed_cases": payload.get("failed_cases"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload.get("passed") else 0


def cmd_resident_parity_summary(args: argparse.Namespace) -> int:
    payload = build_resident_parity_summary(
        cpu_run=args.cpu_run,
        resident_run=args.resident_run,
        compare_json=args.compare_json,
        cpu_label=args.cpu_label,
        resident_label=args.resident_label,
        max_rms_diff=args.max_rms_diff,
        max_relative_rms_diff=args.max_relative_rms_diff,
        max_rejected_sample_delta=args.max_rejected_sample_delta,
        require_resident_contract=not args.ignore_resident_contract,
    )
    write_resident_parity_summary(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "parity_passed": payload.get("parity_passed"),
            "recommendation": payload.get("recommendation"),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload.get("passed") else 0


def cmd_resident_rejection_sample_audit(args: argparse.Namespace) -> int:
    payload = build_resident_rejection_sample_audit(
        cpu_run=args.cpu_run,
        resident_run=args.resident_run,
        compare_json=args.compare_json,
        tile_size=args.tile_size,
        top_tiles=args.top_tiles,
        max_rejected_sample_delta=args.max_rejected_sample_delta,
        max_pre_rejection_sample_delta=args.max_pre_rejection_sample_delta,
        max_same_pre_rejection_abs_delta=args.max_same_pre_rejection_abs_delta,
        evaluation_region=args.evaluation_region,
        rejection_input_audit=args.rejection_input_audit,
    )
    write_resident_rejection_sample_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "recommendation": payload.get("recommendation"),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload.get("passed") else 0


def cmd_resident_rejection_input_audit(args: argparse.Namespace) -> int:
    payload = build_resident_rejection_input_audit(
        cpu_run=args.cpu_run,
        resident_run=args.resident_run,
        compare_json=args.compare_json,
        evaluation_region=args.evaluation_region,
        run_cuda_exact_input=not args.skip_cuda_exact_input,
        master_tolerance=args.master_tolerance,
        max_same_pre_rejection_abs_delta=args.max_same_pre_rejection_abs_delta,
    )
    write_resident_rejection_input_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "recommendation": payload.get("recommendation"),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload.get("passed") else 0


def cmd_resident_warp_input_audit(args: argparse.Namespace) -> int:
    payload = build_resident_warp_input_audit(
        cpu_run=args.cpu_run,
        resident_run=args.resident_run,
        compare_json=args.compare_json,
        frame_ids=args.frame_id,
        max_frames=args.max_frames,
        interpolation=args.interpolation,
        cpu_matrix_rms_tolerance=args.cpu_matrix_rms_tolerance,
        resident_matrix_rms_tolerance=args.resident_matrix_rms_tolerance,
    )
    write_resident_warp_input_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "recommendation": payload.get("recommendation"),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 2 if args.fail_on_failure and not payload.get("passed") else 0


def cmd_resident_winsorized_benchmark(args: argparse.Namespace) -> int:
    payload = build_resident_winsorized_benchmark(
        frame_count=args.frames,
        height=args.height,
        width=args.width,
        seed=args.seed,
        low_sigma=args.low_sigma,
        high_sigma=args.high_sigma,
        tolerance_rms=args.tolerance_rms,
        tolerance_max_abs=args.tolerance_max_abs,
    )
    write_resident_winsorized_benchmark(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "timing_s": payload.get("timing_s"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_resident_winsorized_benchmark_audit(args: argparse.Namespace) -> int:
    payload = build_resident_winsorized_benchmark_audit(
        args.artifact,
        contract=args.contract,
    )
    write_resident_winsorized_benchmark_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "contract": payload.get("contract_path"),
            "benchmark": payload.get("benchmark_path"),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_resident_winsorized_sweep(args: argparse.Namespace) -> int:
    payload = build_resident_winsorized_frame_count_sweep(
        frame_counts=parse_frame_counts(args.frame_counts),
        height=args.height,
        width=args.width,
        seed_base=args.seed_base,
        low_sigma=args.low_sigma,
        high_sigma=args.high_sigma,
        tolerance_rms=args.tolerance_rms,
        tolerance_max_abs=args.tolerance_max_abs,
        required_frame_count=args.required_frame_count,
    )
    write_resident_winsorized_frame_count_sweep(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "frame_counts": payload.get("config", {}).get("frame_counts"),
            "required_frame_count_passed": payload.get("summary", {}).get(
                "required_frame_count_passed"
            ),
            "max_hardened_master_rms": payload.get("summary", {}).get(
                "max_hardened_master_rms"
            ),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_resident_winsorized_sweep_audit(args: argparse.Namespace) -> int:
    payload = build_resident_winsorized_sweep_audit(
        args.artifact,
        contract=args.contract,
    )
    write_resident_winsorized_sweep_audit(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "passed": payload.get("passed"),
            "contract": payload.get("contract_path"),
            "sweep": payload.get("sweep_path"),
            "required_frame_count": payload.get("summary", {}).get("required_frame_count"),
            "required_frame_master": payload.get("summary", {}).get(
                "required_frame_master"
            ),
            "failed_checks": payload.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if bool(args.fail_on_failure) and not payload.get("passed"):
        return 2
    return 0


def cmd_resident_runtime_repeat_plan(args: argparse.Namespace) -> int:
    payload = build_resident_runtime_repeat_plan(
        base_run_command=args.base_run_command,
        root=args.root,
        label=args.label,
        repeats=args.repeats,
        cache_state=args.cache_state,
        baseline_repeat=args.baseline_repeat,
    )
    write_resident_runtime_repeat_plan(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "label": payload.get("label"),
            "repeat_count": payload.get("repeat_count"),
            "cache_state": payload.get("cache_state"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0


def cmd_resident_runtime_repeat_execute(args: argparse.Namespace) -> int:
    payload = build_resident_runtime_repeat_execution(
        args.plan,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
        run_compare=not args.no_run_compare,
        glass_executable=args.glass_executable,
        cwd=args.cwd,
        require_preflight_ready=args.require_preflight_ready,
        min_free_mib=args.min_free_mib,
        max_busy_utilization=args.max_busy_utilization,
        allow_existing_preflight=args.allow_existing_preflight,
        probe_gpu=not args.skip_gpu_probe,
    )
    write_resident_runtime_repeat_execution(args.out, payload)
    if args.preflight_out and isinstance(payload.get("preflight"), dict):
        write_resident_runtime_repeat_preflight(args.preflight_out, payload["preflight"])
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("summary", {}).get("status"),
            "recorded_run_count": payload.get("summary", {}).get("recorded_run_count"),
            "skipped_existing_count": payload.get("summary", {}).get("skipped_existing_count"),
            "compare_status": payload.get("summary", {}).get("compare_status"),
            "preflight_recommendation": (
                payload.get("preflight", {}).get("recommendation")
                if isinstance(payload.get("preflight"), dict)
                else None
            ),
            "out": args.out,
        }
    )
    if args.fail_on_failed and (
        payload.get("summary", {}).get("failed") or payload.get("summary", {}).get("status") == "preflight_blocked"
    ):
        return 2
    return 0


def cmd_resident_runtime_repeat_preflight(args: argparse.Namespace) -> int:
    payload = build_resident_runtime_repeat_preflight(
        args.plan,
        min_free_mib=args.min_free_mib,
        max_busy_utilization=args.max_busy_utilization,
        allow_existing=args.allow_existing,
        probe_gpu=not args.skip_gpu_probe,
    )
    write_resident_runtime_repeat_preflight(args.out, payload)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "ready_to_execute": payload.get("ready_to_execute"),
            "recommendation": payload.get("recommendation"),
            "gpu_status": payload.get("gpu", {}).get("status"),
            "repeat_count": payload.get("repeat_count"),
            "out": args.out,
        }
    )
    if args.fail_when_not_ready and not payload.get("ready_to_execute"):
        return 2
    return 0


def cmd_resident_result_contract(args: argparse.Namespace) -> int:
    payload = build_resident_result_contract(
        args.run,
        pixel_verify=args.pixel_verify,
        pixel_verify_tile_size=args.pixel_verify_tile_size,
        pixel_tolerance=args.pixel_tolerance,
    )
    write_resident_result_contract(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "output_count": len(payload.get("outputs") or []),
            "pixel_verify": payload.get("pixel_verify"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if payload.get("passed") or not args.fail_on_failed else 2


def cmd_resident_calibration_contract(args: argparse.Namespace) -> int:
    payload = build_resident_calibration_contract(args.run)
    write_resident_calibration_contract(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "status": payload.get("status"),
            "output_count": payload.get("output_count"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if payload.get("passed") or not args.fail_on_failed else 2


def cmd_resident_calibration_artifacts(args: argparse.Namespace) -> int:
    payload = build_resident_calibration_artifacts(args.run)
    out = Path(args.out) if args.out else Path(args.run) / "calibration_artifacts.json"
    write_json(out, payload)
    console.print(
        {
            "artifact_type": payload.get("artifact_type"),
            "master_count": len(payload.get("masters") or {}),
            "calibrated_light_count": len(payload.get("calibrated_lights") or []),
            "out": str(out),
        }
    )
    return 0


def cmd_resident_registration_triage(args: argparse.Namespace) -> int:
    payload = build_resident_registration_triage(args.baseline_audit, args.candidate_audit)
    write_resident_registration_triage(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "baseline": payload["baseline_variant_id"],
            "candidates": payload["candidate_count"],
            "extra_failed_variants": payload["summary"]["extra_failed_variant_count"],
            "reference_catalog_drift_variants": payload["summary"]["reference_catalog_drift_variant_count"],
            "recommendation": payload["recommendation"]["status"],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if args.fail_on_extra_rejections and payload["summary"]["extra_failed_variant_count"]:
        return 2
    return 0


def _load_optional_run_contract(
    *,
    explicit_path: str | None,
    run: str | Path,
    default_name: str,
) -> tuple[dict[str, Any] | None, str | None, str]:
    if explicit_path:
        payload = read_json(explicit_path)
        return (payload if isinstance(payload, dict) else None), str(explicit_path), "explicit"
    default_path = Path(run) / default_name
    if default_path.exists():
        payload = read_json(default_path)
        return (payload if isinstance(payload, dict) else None), str(default_path), "run_default"
    return None, None, "missing"


def cmd_stack_engine_contract(args: argparse.Namespace) -> int:
    resident_calibration_contract = (
        read_json(args.resident_calibration_contract_json)
        if getattr(args, "resident_calibration_contract_json", None)
        else None
    )
    resident_result_contract, resident_result_contract_path, resident_result_contract_source = (
        _load_optional_run_contract(
            explicit_path=getattr(args, "resident_result_contract_json", None),
            run=args.run,
            default_name="resident_result_contract.json",
        )
    )
    audit = build_stack_engine_contract_audit(
        args.run,
        scope=args.scope,
        expected_integration_engine=args.expected_integration_engine,
        resident_calibration_contract=resident_calibration_contract
        if isinstance(resident_calibration_contract, dict)
        else None,
        resident_result_contract=resident_result_contract
        if resident_result_contract_source == "explicit" and isinstance(resident_result_contract, dict)
        else None,
    )
    write_stack_engine_contract_audit(args.out, audit, markdown=args.markdown)
    default_promotion = audit.get("default_promotion") if isinstance(audit.get("default_promotion"), dict) else {}
    default_path = audit.get("default_path") if isinstance(audit.get("default_path"), dict) else {}
    console.print(
        {
            "status": audit["status"],
            "scope": audit["scope"],
            "expected_integration_engine": audit["expected_integration_engine"],
            "resident_calibration_contract_attached": audit.get("resident_calibration_contract_attached"),
            "resident_result_contract_attached": audit.get("resident_result_contract_attached"),
            "resident_result_contract_json": resident_result_contract_path,
            "resident_result_contract_source": resident_result_contract_source,
            "default_path_status": default_path.get("status"),
            "strict_native_stack_engine_ready": default_path.get("strict_native_stack_engine_ready"),
            "default_promotion_ready": default_promotion.get("ready"),
            "default_promotion_status": default_promotion.get("status"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    if not audit["passed"]:
        return 2
    if bool(getattr(args, "require_native_stack_engine_default", False)) and not default_path.get(
        "strict_native_stack_engine_ready"
    ):
        return 4
    if bool(getattr(args, "require_default_ready", False)) and not default_promotion.get("ready"):
        return 3
    return 0


def cmd_pipeline_contract(args: argparse.Namespace) -> int:
    resident_calibration_contract = (
        read_json(args.resident_calibration_contract_json)
        if getattr(args, "resident_calibration_contract_json", None)
        else None
    )
    local_norm_contract = (
        read_json(args.local_norm_contract_json)
        if getattr(args, "local_norm_contract_json", None)
        else None
    )
    audit = build_pipeline_contract_audit(
        args.run,
        pixel_verify=args.pixel_verify,
        pixel_verify_tile_size=args.pixel_verify_tile_size,
        pixel_tolerance=args.pixel_tolerance,
        resident_calibration_contract=resident_calibration_contract
        if isinstance(resident_calibration_contract, dict)
        else None,
        local_norm_contract=local_norm_contract if isinstance(local_norm_contract, dict) else None,
    )
    write_pipeline_contract_audit(args.out, audit, markdown=args.markdown)
    console.print(
        {
            "status": audit["status"],
            "out": args.out,
            "markdown": args.markdown,
            "pixel_verify": args.pixel_verify,
            "local_norm_contract_attached": (audit.get("artifacts") or {})
            .get("local_norm_contract", {})
            .get("attached"),
        }
    )
    return 0 if audit["passed"] else 2


def cmd_local_norm_contract(args: argparse.Namespace) -> int:
    audit = build_local_norm_contract(args.run)
    write_local_norm_contract(args.out, audit, markdown=args.markdown)
    console.print(
        {
            "artifact_type": audit.get("artifact_type"),
            "status": audit.get("status"),
            "enabled": audit.get("enabled"),
            "output_count": (audit.get("summary") or {}).get("output_count"),
            "failed_output_count": (audit.get("summary") or {}).get("failed_output_count"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if audit.get("passed") or not args.fail_on_failed else 2


def cmd_warp_quality_contract(args: argparse.Namespace) -> int:
    audit = build_warp_quality_contract(
        args.run,
        min_valid_fraction=args.min_valid_fraction,
        max_skipped_frames=args.max_skipped_frames,
        require_artifacts=args.require_artifacts,
        require_all_registered=args.require_all_registered,
        pixel_verify=args.pixel_verify,
        pixel_verify_tile_size=args.pixel_verify_tile_size,
        pixel_tolerance=args.pixel_tolerance,
        science_residual_verify=args.science_residual_verify,
        science_reference_frame_id=args.science_reference_frame_id,
        max_science_rms=args.max_science_rms,
        max_science_max_abs=args.max_science_max_abs,
        science_residual_tile_size=args.science_residual_tile_size,
    )
    write_warp_quality_contract(args.out, audit, markdown=args.markdown)
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    console.print(
        {
            "artifact_type": audit.get("artifact_type"),
            "status": audit.get("status"),
            "required": audit.get("required"),
            "output_count": summary.get("output_count"),
            "skipped_count": summary.get("skipped_count"),
            "artifact_ready_count": summary.get("artifact_ready_count"),
            "pixel_verified_output_count": summary.get("pixel_verified_output_count"),
            "science_residual_verified_output_count": summary.get(
                "science_residual_verified_output_count"
            ),
            "failed_checks": audit.get("failed_checks"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if audit.get("passed") or not args.fail_on_failed else 2


def cmd_guardrails(args: argparse.Namespace) -> int:
    run = Path(args.run)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stack_path = out_dir / "stack_engine_contract.json"
    stack_markdown = out_dir / "stack_engine_contract.md"
    pipeline_path = out_dir / "pipeline_contract.json"
    pipeline_markdown = out_dir / "pipeline_contract.md"
    local_norm_contract_path = out_dir / "local_norm_contract.json"
    local_norm_contract_markdown = out_dir / "local_norm_contract.md"
    registration_quality_path = out_dir / "registration_quality_contract.json"
    registration_quality_markdown = out_dir / "registration_quality_contract.md"
    warp_quality_path = out_dir / "warp_quality_contract.json"
    warp_quality_markdown = out_dir / "warp_quality_contract.md"
    report_path = Path(args.report) if args.report else out_dir / "report.html"
    bundle_path = out_dir / "acceptance_contract_bundle.json"
    summary_path = out_dir / "guardrails_summary.json"
    resident_calibration_contract = (
        read_json(args.resident_calibration_contract_json)
        if getattr(args, "resident_calibration_contract_json", None)
        else None
    )
    resident_result_contract, resident_result_contract_path, resident_result_contract_source = (
        _load_optional_run_contract(
            explicit_path=getattr(args, "resident_result_contract_json", None),
            run=run,
            default_name="resident_result_contract.json",
        )
    )
    local_norm_results_present = (run / "local_norm_results.json").exists()
    local_norm_contract = None
    if local_norm_results_present:
        local_norm_contract = build_local_norm_contract(run)
        write_local_norm_contract(
            local_norm_contract_path,
            local_norm_contract,
            markdown=local_norm_contract_markdown,
        )
    max_registration_rms_px = getattr(args, "max_registration_rms_px", None)
    min_registration_inliers = getattr(args, "min_registration_inliers", None)
    require_registration_all_accepted = bool(getattr(args, "require_registration_all_accepted", False))
    registration_quality_required = (
        max_registration_rms_px is not None
        or min_registration_inliers is not None
        or require_registration_all_accepted
    )
    registration_quality_present = (run / "registration_results.json").exists() or registration_quality_required
    registration_quality_contract = None
    if registration_quality_present:
        registration_quality_contract = build_registration_quality_contract(
            run,
            max_rms_px=max_registration_rms_px,
            min_inliers=min_registration_inliers,
            require_all_accepted=require_registration_all_accepted,
        )
        write_registration_quality_contract(
            registration_quality_path,
            registration_quality_contract,
            markdown=registration_quality_markdown,
        )
    min_warp_valid_fraction = getattr(args, "min_warp_valid_fraction", None)
    max_warp_skipped_frames = getattr(args, "max_warp_skipped_frames", None)
    require_warp_artifacts = bool(getattr(args, "require_warp_artifacts", False))
    require_warp_all_registered = bool(getattr(args, "require_warp_all_registered", False))
    warp_pixel_verify = bool(getattr(args, "warp_pixel_verify", False))
    warp_pixel_verify_tile_size = int(getattr(args, "warp_pixel_verify_tile_size", 2048))
    warp_pixel_tolerance = int(getattr(args, "warp_pixel_tolerance", 0))
    warp_science_residual_verify = bool(getattr(args, "warp_science_residual_verify", False))
    warp_science_reference_frame_id = getattr(args, "warp_science_reference_frame_id", None)
    max_warp_science_rms = getattr(args, "max_warp_science_rms", None)
    max_warp_science_max_abs = getattr(args, "max_warp_science_max_abs", None)
    warp_science_residual_tile_size = int(getattr(args, "warp_science_residual_tile_size", 2048))
    warp_quality_required = (
        min_warp_valid_fraction is not None
        or max_warp_skipped_frames is not None
        or require_warp_artifacts
        or require_warp_all_registered
        or warp_pixel_verify
        or warp_science_residual_verify
        or max_warp_science_rms is not None
        or max_warp_science_max_abs is not None
    )
    warp_quality_present = (run / "warp_results.json").exists() or warp_quality_required
    warp_quality_contract = None
    if warp_quality_present:
        warp_quality_contract = build_warp_quality_contract(
            run,
            min_valid_fraction=min_warp_valid_fraction,
            max_skipped_frames=max_warp_skipped_frames,
            require_artifacts=require_warp_artifacts,
            require_all_registered=require_warp_all_registered,
            pixel_verify=warp_pixel_verify,
            pixel_verify_tile_size=warp_pixel_verify_tile_size,
            pixel_tolerance=warp_pixel_tolerance,
            science_residual_verify=warp_science_residual_verify,
            science_reference_frame_id=warp_science_reference_frame_id,
            max_science_rms=max_warp_science_rms,
            max_science_max_abs=max_warp_science_max_abs,
            science_residual_tile_size=warp_science_residual_tile_size,
        )
        write_warp_quality_contract(
            warp_quality_path,
            warp_quality_contract,
            markdown=warp_quality_markdown,
        )

    stack_audit = build_stack_engine_contract_audit(
        run,
        scope=args.stack_scope,
        expected_integration_engine=args.expected_integration_engine,
        resident_calibration_contract=resident_calibration_contract
        if isinstance(resident_calibration_contract, dict)
        else None,
        resident_result_contract=resident_result_contract
        if resident_result_contract_source == "explicit" and isinstance(resident_result_contract, dict)
        else None,
    )
    write_stack_engine_contract_audit(stack_path, stack_audit, markdown=stack_markdown)
    pipeline_audit = build_pipeline_contract_audit(
        run,
        pixel_verify=args.pixel_verify,
        pixel_verify_tile_size=args.pixel_verify_tile_size,
        pixel_tolerance=args.pixel_tolerance,
        resident_calibration_contract=resident_calibration_contract
        if isinstance(resident_calibration_contract, dict)
        else None,
        local_norm_contract=local_norm_contract if isinstance(local_norm_contract, dict) else None,
    )
    write_pipeline_contract_audit(pipeline_path, pipeline_audit, markdown=pipeline_markdown)
    _write_run_report(
        run,
        report_path,
        run / "manifest.json",
        run / "processing_plan.json",
        stack_engine_contract=stack_path,
        pipeline_contract=pipeline_path,
        local_norm_contract=local_norm_contract_path if local_norm_results_present else None,
        registration_quality=registration_quality_path if registration_quality_present else None,
        warp_quality=warp_quality_path if warp_quality_present else None,
    )
    stack_default_promotion = (
        stack_audit.get("default_promotion") if isinstance(stack_audit.get("default_promotion"), dict) else {}
    )
    stack_default_ready = bool(stack_default_promotion.get("ready"))
    stack_default_required = bool(getattr(args, "require_stack_default_ready", False))
    stack_default_condition = (not stack_default_required) or stack_default_ready
    local_norm_contract_condition = (
        not local_norm_results_present
        or (isinstance(local_norm_contract, dict) and bool(local_norm_contract.get("passed")))
    )
    local_norm_contract_status = (
        local_norm_contract.get("status") if isinstance(local_norm_contract, dict) else "not_present"
    )
    local_norm_enabled_required = bool(getattr(args, "require_local_normalization_enabled", False))
    local_norm_contract_enabled = (
        local_norm_contract.get("enabled") if isinstance(local_norm_contract, dict) else None
    )
    local_norm_enabled_condition = (
        not local_norm_enabled_required
        or (
            local_norm_results_present
            and local_norm_contract_enabled is True
            and local_norm_contract_condition
        )
    )
    local_norm_summary = local_norm_contract.get("summary") if isinstance(local_norm_contract, dict) else {}
    local_norm_residual_quality = (
        local_norm_summary.get("residual_quality") if isinstance(local_norm_summary, dict) else {}
    )
    if not isinstance(local_norm_residual_quality, dict):
        local_norm_residual_quality = {}
    max_local_norm_rms = getattr(args, "max_local_normalization_rms", None)
    max_local_norm_max_abs = getattr(args, "max_local_normalization_max_abs", None)
    local_norm_residual_required = max_local_norm_rms is not None or max_local_norm_max_abs is not None
    local_norm_residual_rms = local_norm_residual_quality.get("max_rms")
    local_norm_residual_max_abs = local_norm_residual_quality.get("max_abs")
    local_norm_residual_failed_count = int(local_norm_residual_quality.get("failed_output_count") or 0)
    local_norm_residual_output_count = int(local_norm_residual_quality.get("output_count") or 0)
    local_norm_residual_rms_condition = (
        max_local_norm_rms is None
        or (local_norm_residual_rms is not None and float(local_norm_residual_rms) <= float(max_local_norm_rms))
    )
    local_norm_residual_max_abs_condition = (
        max_local_norm_max_abs is None
        or (
            local_norm_residual_max_abs is not None
            and float(local_norm_residual_max_abs) <= float(max_local_norm_max_abs)
        )
    )
    local_norm_residual_condition = (
        not local_norm_residual_required
        or (
            local_norm_contract_condition
            and local_norm_contract_enabled is True
            and local_norm_residual_output_count > 0
            and local_norm_residual_failed_count == 0
            and local_norm_residual_rms_condition
            and local_norm_residual_max_abs_condition
        )
    )
    registration_quality_condition = (
        not registration_quality_required
        or (
            isinstance(registration_quality_contract, dict)
            and bool(registration_quality_contract.get("passed"))
        )
    )
    registration_quality_summary = (
        registration_quality_contract.get("summary")
        if isinstance(registration_quality_contract, dict)
        else {}
    )
    registration_quality_status = (
        registration_quality_contract.get("status")
        if isinstance(registration_quality_contract, dict)
        else "not_present"
    )
    warp_quality_condition = (
        not warp_quality_required
        or (
            isinstance(warp_quality_contract, dict)
            and bool(warp_quality_contract.get("passed"))
        )
    )
    warp_quality_summary = (
        warp_quality_contract.get("summary") if isinstance(warp_quality_contract, dict) else {}
    )
    warp_quality_status = (
        warp_quality_contract.get("status") if isinstance(warp_quality_contract, dict) else "not_present"
    )
    pipeline_calibration = (
        pipeline_audit.get("calibration") if isinstance(pipeline_audit.get("calibration"), dict) else {}
    )
    resident_native_calibration = {
        "artifact_present": bool(pipeline_calibration.get("resident_native_calibration_artifact")),
        "master_count": pipeline_calibration.get("local_master_count"),
        "resident_calibrated_light_count": pipeline_calibration.get("resident_calibrated_light_count"),
        "resident_calibration_contract_attached": bool(
            pipeline_calibration.get("resident_calibration_contract_attached")
        ),
    }
    passed = (
        bool(stack_audit.get("passed"))
        and bool(pipeline_audit.get("passed"))
        and stack_default_condition
        and local_norm_contract_condition
        and local_norm_enabled_condition
        and local_norm_residual_condition
        and registration_quality_condition
        and warp_quality_condition
    )
    summary = {
        "schema_version": 1,
        "created_at": now_iso(),
        "audit_type": "glass_guardrails",
        "run_dir": str(run),
        "out_dir": str(out_dir),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "pixel_verify": bool(args.pixel_verify),
        "stack_scope": args.stack_scope,
        "expected_integration_engine": args.expected_integration_engine,
        "require_stack_default_ready": stack_default_required,
        "require_local_normalization_enabled": local_norm_enabled_required,
        "max_local_normalization_rms": max_local_norm_rms,
        "max_local_normalization_max_abs": max_local_norm_max_abs,
        "max_registration_rms_px": max_registration_rms_px,
        "min_registration_inliers": min_registration_inliers,
        "require_registration_all_accepted": require_registration_all_accepted,
        "min_warp_valid_fraction": min_warp_valid_fraction,
        "max_warp_skipped_frames": max_warp_skipped_frames,
        "require_warp_artifacts": require_warp_artifacts,
        "require_warp_all_registered": require_warp_all_registered,
        "warp_pixel_verify": warp_pixel_verify,
        "warp_pixel_verify_tile_size": warp_pixel_verify_tile_size,
        "warp_pixel_tolerance": warp_pixel_tolerance,
        "warp_science_residual_verify": warp_science_residual_verify,
        "warp_science_reference_frame_id": warp_science_reference_frame_id,
        "max_warp_science_rms": max_warp_science_rms,
        "max_warp_science_max_abs": max_warp_science_max_abs,
        "warp_science_residual_tile_size": warp_science_residual_tile_size,
        "resident_calibration_contract_json": args.resident_calibration_contract_json,
        "resident_result_contract_json": resident_result_contract_path,
        "resident_result_contract_source": resident_result_contract_source,
        "resident_calibration_contract_attached": stack_audit.get("resident_calibration_contract_attached"),
        "resident_result_contract_attached": stack_audit.get("resident_result_contract_attached"),
        "local_norm_contract_required": local_norm_results_present,
        "local_norm_contract_attached": isinstance(local_norm_contract, dict),
        "local_norm_contract_status": local_norm_contract_status,
        "local_norm_contract_enabled": local_norm_contract_enabled,
        "local_norm_residual_quality": local_norm_residual_quality,
        "registration_quality_required": registration_quality_required,
        "registration_quality_status": registration_quality_status,
        "registration_quality": registration_quality_summary,
        "warp_quality_required": warp_quality_required,
        "warp_quality_status": warp_quality_status,
        "warp_quality": warp_quality_summary,
        "resident_native_calibration": resident_native_calibration,
        "stack_default_promotion": stack_default_promotion,
        "artifacts": {
            "stack_engine_contract": str(stack_path),
            "stack_engine_contract_markdown": str(stack_markdown),
            "pipeline_contract": str(pipeline_path),
            "pipeline_contract_markdown": str(pipeline_markdown),
            "local_norm_contract": str(local_norm_contract_path) if local_norm_results_present else None,
            "local_norm_contract_markdown": str(local_norm_contract_markdown)
            if local_norm_results_present
            else None,
            "registration_quality_contract": str(registration_quality_path)
            if registration_quality_present
            else None,
            "registration_quality_contract_markdown": str(registration_quality_markdown)
            if registration_quality_present
            else None,
            "warp_quality_contract": str(warp_quality_path) if warp_quality_present else None,
            "warp_quality_contract_markdown": str(warp_quality_markdown)
            if warp_quality_present
            else None,
            "acceptance_contract_bundle": str(bundle_path),
            "report": str(report_path),
            "resident_calibration_contract": args.resident_calibration_contract_json,
            "resident_result_contract": resident_result_contract_path,
        },
        "checks": [
            {
                "name": "stack_engine_contract",
                "passed": bool(stack_audit.get("passed")),
                "status": stack_audit.get("status"),
                "failed": [
                    check.get("name")
                    for check in stack_audit.get("checks") or []
                    if not check.get("passed")
                ],
            },
            {
                "name": "pipeline_contract",
                "passed": bool(pipeline_audit.get("passed")),
                "status": pipeline_audit.get("status"),
                "failed": [
                    check.get("name")
                    for check in pipeline_audit.get("checks") or []
                    if not check.get("passed")
                ],
            },
            {
                "name": "stack_default_promotion",
                "passed": stack_default_condition,
                "required": stack_default_required,
                "ready": stack_default_ready,
                "status": stack_default_promotion.get("status"),
                "blockers": stack_default_promotion.get("blockers") or [],
            },
        ],
    }
    summary["checks"].append(
        {
            "name": "local_norm_contract",
            "passed": local_norm_contract_condition,
            "required": local_norm_results_present,
            "status": local_norm_contract_status,
            "failed": [
                item.get("name")
                for item in (local_norm_contract or {}).get("checks", [])
                if isinstance(item, dict) and not item.get("passed")
            ],
            "failed_outputs": (local_norm_contract or {}).get("failed_outputs", [])
            if isinstance(local_norm_contract, dict)
            else [],
        }
    )
    summary["checks"].append(
        {
            "name": "local_norm_enabled_requirement",
            "passed": local_norm_enabled_condition,
            "required": local_norm_enabled_required,
            "enabled": local_norm_contract_enabled,
            "local_norm_results_present": local_norm_results_present,
            "contract_passed": local_norm_contract_condition,
            "status": "passed" if local_norm_enabled_condition else "missing_or_disabled",
        }
    )
    summary["checks"].append(
        {
            "name": "local_norm_residual_quality",
            "passed": local_norm_residual_condition,
            "required": local_norm_residual_required,
            "max_rms": local_norm_residual_rms,
            "max_abs": local_norm_residual_max_abs,
            "max_rms_threshold": max_local_norm_rms,
            "max_abs_threshold": max_local_norm_max_abs,
            "output_count": local_norm_residual_output_count,
            "failed_output_count": local_norm_residual_failed_count,
            "status": "passed" if local_norm_residual_condition else "threshold_failed_or_missing",
        }
    )
    summary["checks"].append(
        {
            "name": "registration_quality",
            "passed": registration_quality_condition,
            "required": registration_quality_required,
            "status": registration_quality_status,
            "output_count": registration_quality_summary.get("output_count")
            if isinstance(registration_quality_summary, dict)
            else None,
            "accepted_count": registration_quality_summary.get("accepted_count")
            if isinstance(registration_quality_summary, dict)
            else None,
            "failed_count": registration_quality_summary.get("failed_count")
            if isinstance(registration_quality_summary, dict)
            else None,
            "max_rms_px": registration_quality_summary.get("max_rms_px")
            if isinstance(registration_quality_summary, dict)
            else None,
            "min_inliers": registration_quality_summary.get("min_inliers")
            if isinstance(registration_quality_summary, dict)
            else None,
            "failed": (registration_quality_contract or {}).get("failed_checks", [])
            if isinstance(registration_quality_contract, dict)
            else [],
        }
    )
    summary["checks"].append(
        {
            "name": "warp_quality",
            "passed": warp_quality_condition,
            "required": warp_quality_required,
            "status": warp_quality_status,
            "output_count": warp_quality_summary.get("output_count")
            if isinstance(warp_quality_summary, dict)
            else None,
            "skipped_count": warp_quality_summary.get("skipped_count")
            if isinstance(warp_quality_summary, dict)
            else None,
            "artifact_ready_count": warp_quality_summary.get("artifact_ready_count")
            if isinstance(warp_quality_summary, dict)
            else None,
            "min_valid_fraction": warp_quality_summary.get("min_valid_fraction")
            if isinstance(warp_quality_summary, dict)
            else None,
            "missing_warp_for_accepted_registration_count": warp_quality_summary.get(
                "missing_warp_for_accepted_registration_count"
            )
            if isinstance(warp_quality_summary, dict)
            else None,
            "failed": (warp_quality_contract or {}).get("failed_checks", [])
            if isinstance(warp_quality_contract, dict)
            else [],
        }
    )
    bundle = {
        "schema_version": 1,
        "created_at": now_iso(),
        "artifact_type": "glass_acceptance_contract_bundle",
        "run_dir": str(run),
        "out_dir": str(out_dir),
        "status": summary["status"],
        "passed": passed,
        "purpose": "acceptance_audit_contract_inputs",
        "pixel_verify": bool(args.pixel_verify),
        "stack_scope": args.stack_scope,
        "expected_integration_engine": args.expected_integration_engine,
        "require_stack_default_ready": stack_default_required,
        "require_local_normalization_enabled": local_norm_enabled_required,
        "max_local_normalization_rms": max_local_norm_rms,
        "max_local_normalization_max_abs": max_local_norm_max_abs,
        "max_registration_rms_px": max_registration_rms_px,
        "min_registration_inliers": min_registration_inliers,
        "require_registration_all_accepted": require_registration_all_accepted,
        "min_warp_valid_fraction": min_warp_valid_fraction,
        "max_warp_skipped_frames": max_warp_skipped_frames,
        "require_warp_artifacts": require_warp_artifacts,
        "require_warp_all_registered": require_warp_all_registered,
        "warp_pixel_verify": warp_pixel_verify,
        "warp_pixel_verify_tile_size": warp_pixel_verify_tile_size,
        "warp_pixel_tolerance": warp_pixel_tolerance,
        "warp_science_residual_verify": warp_science_residual_verify,
        "warp_science_reference_frame_id": warp_science_reference_frame_id,
        "max_warp_science_rms": max_warp_science_rms,
        "max_warp_science_max_abs": max_warp_science_max_abs,
        "warp_science_residual_tile_size": warp_science_residual_tile_size,
        "resident_calibration_contract_json": args.resident_calibration_contract_json,
        "resident_result_contract_json": resident_result_contract_path,
        "resident_result_contract_source": resident_result_contract_source,
        "resident_calibration_contract_attached": stack_audit.get("resident_calibration_contract_attached"),
        "resident_result_contract_attached": stack_audit.get("resident_result_contract_attached"),
        "local_norm_contract_required": local_norm_results_present,
        "local_norm_contract_attached": isinstance(local_norm_contract, dict),
        "local_norm_contract_status": local_norm_contract_status,
        "local_norm_contract_enabled": local_norm_contract_enabled,
        "local_norm_residual_quality": local_norm_residual_quality,
        "registration_quality_required": registration_quality_required,
        "registration_quality_status": registration_quality_status,
        "registration_quality": registration_quality_summary,
        "warp_quality_required": warp_quality_required,
        "warp_quality_status": warp_quality_status,
        "warp_quality": warp_quality_summary,
        "resident_native_calibration": resident_native_calibration,
        "stack_default_promotion": stack_default_promotion,
        "artifacts": {
            "guardrails_summary": str(summary_path),
            "stack_engine_contract": str(stack_path),
            "stack_engine_contract_markdown": str(stack_markdown),
            "pipeline_contract": str(pipeline_path),
            "pipeline_contract_markdown": str(pipeline_markdown),
            "local_norm_contract": str(local_norm_contract_path) if local_norm_results_present else None,
            "local_norm_contract_markdown": str(local_norm_contract_markdown)
            if local_norm_results_present
            else None,
            "registration_quality_contract": str(registration_quality_path)
            if registration_quality_present
            else None,
            "registration_quality_contract_markdown": str(registration_quality_markdown)
            if registration_quality_present
            else None,
            "warp_quality_contract": str(warp_quality_path) if warp_quality_present else None,
            "warp_quality_contract_markdown": str(warp_quality_markdown)
            if warp_quality_present
            else None,
            "report": str(report_path),
            "resident_calibration_contract": args.resident_calibration_contract_json,
            "resident_result_contract": resident_result_contract_path,
        },
        "acceptance_audit_arguments": [
            "--pipeline-contract-json",
            str(pipeline_path),
            "--stack-engine-contract-json",
            str(stack_path),
        ],
        "acceptance_audit_argument_map": {
            "pipeline_contract_json": str(pipeline_path),
            "stack_engine_contract_json": str(stack_path),
        },
        "checks": summary["checks"],
    }
    write_json(bundle_path, bundle)
    write_json(summary_path, summary)
    console.print(
        {
            "status": summary["status"],
            "summary": str(summary_path),
            "acceptance_contract_bundle": str(bundle_path),
            "report": str(report_path),
            "pixel_verify": args.pixel_verify,
            "stack_default_promotion_ready": stack_default_ready,
            "require_stack_default_ready": stack_default_required,
            "require_local_normalization_enabled": local_norm_enabled_required,
            "max_local_normalization_rms": max_local_norm_rms,
            "max_local_normalization_max_abs": max_local_norm_max_abs,
            "max_registration_rms_px": max_registration_rms_px,
            "min_registration_inliers": min_registration_inliers,
            "require_registration_all_accepted": require_registration_all_accepted,
            "min_warp_valid_fraction": min_warp_valid_fraction,
            "max_warp_skipped_frames": max_warp_skipped_frames,
            "require_warp_artifacts": require_warp_artifacts,
            "require_warp_all_registered": require_warp_all_registered,
            "warp_pixel_verify": warp_pixel_verify,
            "warp_pixel_verify_tile_size": warp_pixel_verify_tile_size,
            "warp_pixel_tolerance": warp_pixel_tolerance,
            "warp_science_residual_verify": warp_science_residual_verify,
            "warp_science_reference_frame_id": warp_science_reference_frame_id,
            "max_warp_science_rms": max_warp_science_rms,
            "max_warp_science_max_abs": max_warp_science_max_abs,
            "warp_science_residual_tile_size": warp_science_residual_tile_size,
            "resident_calibration_contract_attached": stack_audit.get("resident_calibration_contract_attached"),
            "resident_result_contract_attached": stack_audit.get("resident_result_contract_attached"),
            "resident_result_contract_json": resident_result_contract_path,
            "resident_result_contract_source": resident_result_contract_source,
            "local_norm_contract_status": local_norm_contract_status,
            "local_norm_contract_required": local_norm_results_present,
            "local_norm_contract_enabled": local_norm_contract_enabled,
            "local_norm_residual_quality": local_norm_residual_quality,
            "registration_quality_status": registration_quality_status,
            "registration_quality_required": registration_quality_required,
            "warp_quality_status": warp_quality_status,
            "warp_quality_required": warp_quality_required,
            "resident_native_calibration": resident_native_calibration,
        }
    )
    return 0 if passed else 2


def cmd_blackbox_package(args: argparse.Namespace) -> int:
    payload = create_blackbox_package(
        args.manifest,
        args.plan,
        args.out,
        glass_run=args.glass_run,
        glass_time_seconds=args.glass_time_seconds,
        reference_label=args.reference_label,
    )
    console.print(f"Wrote black-box package: {args.out}")
    console.print(payload)
    return 0


def cmd_blackbox_finalize(args: argparse.Namespace) -> int:
    payload = finalize_blackbox_package(args.timing, args.out)
    console.print(f"Wrote black-box finalize summary: {args.out or Path(args.timing).parent}")
    console.print(payload)
    return 0 if payload.get("status") == "complete" else 2


def cmd_blackbox_history(args: argparse.Namespace) -> int:
    payload = read_fastintegration_history(args.master, max_bytes=args.max_bytes)
    write_json(args.out, payload)
    console.print(f"Wrote WBPP FastIntegration history: {args.out}")
    console.print(payload["summary"])
    return 0


def cmd_synthetic(args: argparse.Namespace) -> int:
    generate_synthetic_dataset(
        args.out,
        frames=args.frames,
        width=args.width,
        height=args.height,
        filt=args.filter,
        known_shift=args.known_shift,
    )
    console.print(f"Wrote synthetic dataset: {args.out}")
    return 0


def _doctor_payload(*, skip_cuda_probe: bool = False) -> dict:
    cuda_importable = importlib.util.find_spec("glass_cuda") is not None
    cuda_info: dict = {
        "wrapper_importable": cuda_importable,
        "native_extension_loaded": False,
        "cuda_available": False,
        "devices": [],
        "error": None,
        "probe_skipped": bool(skip_cuda_probe),
    }
    if cuda_importable and not skip_cuda_probe:
        try:
            import glass_cuda  # type: ignore

            cuda_info["native_extension_loaded"] = bool(
                getattr(glass_cuda, "native_extension_loaded", lambda: False)()
            )
            cuda_info["cuda_available"] = bool(getattr(glass_cuda, "cuda_available", lambda: False)())
            cuda_info["devices"] = list(getattr(glass_cuda, "list_devices", lambda: [])())
            cuda_info["error"] = getattr(glass_cuda, "native_import_error", lambda: None)()
        except Exception as exc:  # pragma: no cover - environment-specific diagnostic path
            cuda_info["error"] = str(exc)
    return {
        "schema_version": 1,
        "product": "GLASS",
        "full_name": "GPU-Accelerated Lightframe Alignment and Stacking System",
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "platform": _safe_platform_label(),
        },
        "capabilities": capability_report(probe_cuda=not skip_cuda_probe),
        "cuda": cuda_info,
        "windows_cuda_packages": recommend_windows_cuda_packages(cuda_info["devices"]),
        "recommendation": (
            "cuda"
            if cuda_info["cuda_available"]
            else "cpu; install a GLASS CUDA wheel and update the NVIDIA driver to enable GPU acceleration"
        ),
    }


def cmd_doctor(args: argparse.Namespace) -> int:
    payload = _doctor_payload(skip_cuda_probe=args.skip_cuda_probe)
    if args.json:
        write_json(args.json, payload)
        console.print(f"Wrote GLASS doctor report: {args.json}")
    console.print("GLASS Doctor")
    console.print(f"Python: {payload['python']['version']} ({payload['python']['platform']})")
    cuda = payload["cuda"]
    console.print(f"CUDA wrapper importable: {cuda['wrapper_importable']}")
    if cuda.get("probe_skipped"):
        console.print("CUDA probe skipped: True")
    console.print(f"CUDA native extension loaded: {cuda['native_extension_loaded']}")
    console.print(f"CUDA available: {cuda['cuda_available']}")
    if cuda.get("error"):
        console.print(f"CUDA error: {cuda['error']}")
    devices = cuda.get("devices") or []
    if devices:
        for device in devices:
            name = device.get("name", "unknown")
            cc = device.get("compute_capability", device.get("major_minor", "unknown"))
            memory = device.get("memory_total_mib", device.get("total_global_mem_mib", "unknown"))
            driver = device.get("driver_version", "unknown")
            console.print(f"GPU {device.get('device_id', '?')}: {name}, cc={cc}, VRAM={memory} MiB, driver={driver}")
    else:
        console.print("GPU: none detected by GLASS")
    package_recommendation = payload["windows_cuda_packages"]
    console.print(f"Windows package try order: {', '.join(package_recommendation['ordered_try_list'])}")
    console.print(f"Package guidance: {package_recommendation['guidance']}")
    console.print(f"Recommendation: {payload['recommendation']}")
    return 0 if cuda["cuda_available"] or args.allow_cpu_only else 2


def cmd_phase2_status(args: argparse.Namespace) -> int:
    payload = build_phase2_status(
        checkpoint_dir=args.checkpoint_dir,
        acceptance_audit=args.acceptance_audit,
        default_route_acceptance_audit=args.default_route_acceptance_audit,
        release_manifest=args.release_manifest,
        github_release_plan=args.github_release_plan,
        publish_preflight=args.publish_preflight,
        stack_engine_publication_audit=args.stack_engine_publication_audit,
        pipeline_contract=args.pipeline_contract,
        stack_engine_contract=args.stack_engine_contract,
        registration_results=args.registration_results,
        quality_results=args.quality_results,
        quality_metrics_compare=args.quality_metrics_compare,
        resident_winsorized_benchmark_audit=args.resident_winsorized_benchmark_audit,
        resident_winsorized_sweep_audit=args.resident_winsorized_sweep_audit,
        release_decision=args.release_decision,
        doctor_payload=_doctor_payload(skip_cuda_probe=args.skip_cuda_probe),
    )
    write_phase2_status(args.out, payload, markdown=args.markdown)
    latest = payload.get("latest_checkpoint") if isinstance(payload.get("latest_checkpoint"), dict) else {}
    acceptance = payload.get("acceptance_audit") if isinstance(payload.get("acceptance_audit"), dict) else {}
    default_route = (
        payload.get("default_route_acceptance")
        if isinstance(payload.get("default_route_acceptance"), dict)
        else {}
    )
    pipeline = payload.get("pipeline_contract") if isinstance(payload.get("pipeline_contract"), dict) else {}
    registration_admission = (
        payload.get("registration_admission")
        if isinstance(payload.get("registration_admission"), dict)
        else {}
    )
    quality_saturation = (
        payload.get("quality_saturation")
        if isinstance(payload.get("quality_saturation"), dict)
        else {}
    )
    quality_metrics = (
        payload.get("quality_metrics")
        if isinstance(payload.get("quality_metrics"), dict)
        else {}
    )
    quality_compare = (
        payload.get("quality_metrics_compare")
        if isinstance(payload.get("quality_metrics_compare"), dict)
        else {}
    )
    winsorized_audit = (
        payload.get("resident_winsorized_benchmark_audit")
        if isinstance(payload.get("resident_winsorized_benchmark_audit"), dict)
        else {}
    )
    winsorized_sweep_audit = (
        payload.get("resident_winsorized_sweep_audit")
        if isinstance(payload.get("resident_winsorized_sweep_audit"), dict)
        else {}
    )
    decision = payload.get("release_decision") if isinstance(payload.get("release_decision"), dict) else {}
    preflight = payload.get("publish_preflight") if isinstance(payload.get("publish_preflight"), dict) else {}
    console.print(
        {
            "status": payload.get("status"),
            "latest_gate": latest.get("gate"),
            "latest_checkpoint_status": latest.get("status"),
            "acceptance_status": acceptance.get("status"),
            "speedup_vs_reference": acceptance.get("speedup_vs_reference"),
            "default_route_acceptance_status": default_route.get("status"),
            "default_route_acceptance_passed": default_route.get("passed"),
            "publish_preflight_status": preflight.get("status"),
            "publish_preflight_passed": preflight.get("passed"),
            "pipeline_contract_status": pipeline.get("status"),
            "registration_admission_status": registration_admission.get("status"),
            "quality_saturation_status": quality_saturation.get("status"),
            "quality_saturation_rejected": quality_saturation.get(
                "quality_gate_saturation_rejected_count"
            ),
            "quality_metrics_status": quality_metrics.get("status"),
            "quality_metrics_count": quality_metrics.get("metric_count"),
            "quality_metrics_compare_status": quality_compare.get("status"),
            "quality_metrics_compare_failed_checks": quality_compare.get("failed_check_count"),
            "resident_winsorized_benchmark_audit_status": winsorized_audit.get("status"),
            "resident_winsorized_benchmark_audit_passed": winsorized_audit.get("passed"),
            "resident_winsorized_sweep_audit_status": winsorized_sweep_audit.get("status"),
            "resident_winsorized_sweep_audit_passed": winsorized_sweep_audit.get("passed"),
            "release_decision_status": decision.get("status"),
            "default_change_ready": decision.get("default_change_ready"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if payload.get("passed") or not args.fail_on_not_green else 2


def cmd_phase2_status_compare(args: argparse.Namespace) -> int:
    payload = build_phase2_status_compare(
        baseline_status=args.baseline_status,
        candidate_status=args.candidate_status,
    )
    write_phase2_status_compare(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload.get("status"),
            "baseline_gate": (payload.get("baseline") or {}).get("latest_gate"),
            "candidate_gate": (payload.get("candidate") or {}).get("latest_gate"),
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if payload.get("passed") or not args.fail_on_regression else 2


def cmd_quality_metrics_compare(args: argparse.Namespace) -> int:
    payload = build_quality_metrics_compare(
        args.baseline,
        args.candidate,
        max_bad_median_ratio=args.max_bad_median_ratio,
        max_bad_mean_ratio=args.max_bad_mean_ratio,
    )
    write_quality_metrics_compare(args.out, payload, markdown=args.markdown)
    console.print(
        {
            "status": payload.get("status"),
            "baseline_metric_count": (payload.get("baseline") or {}).get("metric_count"),
            "candidate_metric_count": (payload.get("candidate") or {}).get("metric_count"),
            "failed_checks": [
                item.get("name")
                for item in payload.get("checks") or []
                if isinstance(item, dict) and item.get("passed") is not True
            ],
            "out": args.out,
            "markdown": args.markdown,
        }
    )
    return 0 if payload.get("passed") or not args.fail_on_failed else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="glass")
    parser.add_argument("--version", action="version", version="glass 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="diagnose GLASS CPU/CUDA runtime availability")
    doctor.add_argument("--json", help="optional output JSON report")
    doctor.add_argument("--allow-cpu-only", action="store_true", help="return success when CUDA is unavailable")
    doctor.add_argument(
        "--skip-cuda-probe",
        action="store_true",
        help="avoid importing/probing the CUDA backend; useful for CPU-only diagnostics when the GPU is busy",
    )
    doctor.set_defaults(func=cmd_doctor)

    phase2_status = sub.add_parser(
        "phase2-status",
        help="summarize the latest Phase 2 checkpoint, acceptance audit, CUDA state, and release handoff artifacts",
    )
    phase2_status.add_argument("--checkpoint-dir", default="runs/checkpoints")
    phase2_status.add_argument("--acceptance-audit", help="optional acceptance-audit JSON artifact")
    phase2_status.add_argument(
        "--default-route-acceptance-audit",
        help="optional acceptance-audit JSON artifact proving the guarded default route",
    )
    phase2_status.add_argument("--release-manifest", help="optional Windows release-manifest JSON artifact")
    phase2_status.add_argument("--github-release-plan", help="optional Windows GitHub release-plan JSON artifact")
    phase2_status.add_argument("--publish-preflight", help="optional Windows publish-preflight JSON artifact")
    phase2_status.add_argument(
        "--stack-engine-publication-audit",
        help="optional StackEngine publication-audit JSON artifact",
    )
    phase2_status.add_argument("--pipeline-contract", help="optional pipeline-contract JSON artifact")
    phase2_status.add_argument(
        "--stack-engine-contract",
        help="optional StackEngine default-contract JSON artifact",
    )
    phase2_status.add_argument(
        "--registration-results",
        help="optional registration_results.json artifact used to summarize reference admission",
    )
    phase2_status.add_argument(
        "--quality-results",
        help="optional frame_quality.json artifact used to summarize saturation quality evidence",
    )
    phase2_status.add_argument(
        "--quality-metrics-compare",
        help="optional quality-metrics-compare JSON artifact used to summarize quality regression evidence",
    )
    phase2_status.add_argument(
        "--resident-winsorized-benchmark-audit",
        help="optional resident-winsorized-benchmark-audit JSON artifact",
    )
    phase2_status.add_argument(
        "--resident-winsorized-sweep-audit",
        help="optional resident-winsorized-sweep-audit JSON artifact",
    )
    phase2_status.add_argument("--release-decision", help="optional release-promotion-decision JSON artifact")
    phase2_status.add_argument("--out", required=True, help="output Phase 2 status JSON")
    phase2_status.add_argument("--markdown", help="optional output Markdown summary")
    phase2_status.add_argument(
        "--skip-cuda-probe",
        action="store_true",
        help="avoid importing/probing CUDA while still summarizing available artifacts",
    )
    phase2_status.add_argument(
        "--fail-on-not-green",
        action="store_true",
        help="return exit code 2 unless all supplied status checks pass",
    )
    phase2_status.set_defaults(func=cmd_phase2_status)

    phase2_status_compare = sub.add_parser(
        "phase2-status-compare",
        help="compare two Phase 2 status artifacts and flag handoff regressions",
    )
    phase2_status_compare.add_argument("--baseline-status", required=True, help="baseline glass_phase2_status JSON")
    phase2_status_compare.add_argument("--candidate-status", required=True, help="candidate glass_phase2_status JSON")
    phase2_status_compare.add_argument("--out", required=True, help="output comparison JSON")
    phase2_status_compare.add_argument("--markdown", help="optional output Markdown summary")
    phase2_status_compare.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="return exit code 2 if the candidate regresses relative to the baseline",
    )
    phase2_status_compare.set_defaults(func=cmd_phase2_status_compare)

    quality_metrics_compare = sub.add_parser(
        "quality-metrics-compare",
        help="compare baseline and candidate frame_quality.json metric distributions",
    )
    quality_metrics_compare.add_argument("--baseline", required=True, help="baseline frame_quality.json")
    quality_metrics_compare.add_argument("--candidate", required=True, help="candidate frame_quality.json")
    quality_metrics_compare.add_argument("--out", required=True, help="output quality metrics compare JSON")
    quality_metrics_compare.add_argument("--markdown", help="optional Markdown summary")
    quality_metrics_compare.add_argument(
        "--max-bad-median-ratio",
        type=float,
        help="optional limit for worse-direction median ratio; disabled by default",
    )
    quality_metrics_compare.add_argument(
        "--max-bad-mean-ratio",
        type=float,
        help="optional limit for worse-direction mean ratio; disabled by default",
    )
    quality_metrics_compare.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when compare checks fail",
    )
    quality_metrics_compare.set_defaults(func=cmd_quality_metrics_compare)

    scan = sub.add_parser("scan", help="scan FITS/FIT/XISF metadata")
    scan.add_argument("--root", required=True)
    scan.add_argument("--out", required=True)
    scan.set_defaults(func=cmd_scan)

    plan = sub.add_parser("plan", help="build processing_plan.json from a manifest")
    plan.add_argument("--manifest", required=True)
    plan.add_argument("--out", required=True)
    plan.set_defaults(func=cmd_plan)

    subset = sub.add_parser("subset", help="select a small executable subset from a manifest")
    subset.add_argument("--manifest", required=True)
    subset.add_argument("--out", required=True)
    subset.add_argument("--plan-out")
    subset.add_argument("--object")
    subset.add_argument("--filter")
    subset.add_argument("--exposure-s", type=float)
    subset.add_argument("--light-limit", type=int, default=2)
    subset.add_argument("--bias-limit", type=int, default=1)
    subset.add_argument("--dark-limit", type=int, default=1)
    subset.add_argument("--flat-limit", type=int, default=1)
    subset.add_argument(
        "--all-compatible-calibration",
        action="store_true",
        help="include all compatible calibration frames, not only the planner-selected matching groups",
    )
    subset.set_defaults(func=cmd_subset)

    run = sub.add_parser("run", help="execute the gated pipeline")
    run.add_argument("--plan", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="auto")
    run.add_argument("--vram-budget-gb", type=float)
    run.add_argument("--ram-budget-gb", type=float)
    run.add_argument("--until-stage", default=DEFAULT_UNTIL_STAGE)
    run.add_argument("--tile-size", type=int, default=512)
    run.add_argument(
        "--registration-method",
        choices=["auto", "star", "astroalign", "cuda_catalog", "cuda_triangle"],
        default="auto",
        help=(
            "tile-mode registration method; astroalign uses the optional open-source glass[align] backend, "
            "cuda_catalog and cuda_triangle require the native CUDA backend"
        ),
    )
    run.add_argument(
        "--registration-preview-max-dimension",
        type=int,
        default=1024,
        help="maximum preview width/height used by tile-mode streaming registration",
    )
    run.add_argument(
        "--warp-interpolation",
        choices=["nearest", "bilinear", "bicubic", "lanczos3"],
        default="bilinear",
        help="tile-mode warp interpolator registry entry",
    )
    run.add_argument(
        "--memory-mode",
        choices=["tile", "resident"],
        default=DEFAULT_MEMORY_MODE,
        help=(
            "execution memory strategy; default resident promotes CUDA full-frame StackEngine when "
            "backend auto can use CUDA, with tile fallback for CPU or unsupported partial stages"
        ),
    )
    run.add_argument(
        "--resident-runtime-preset",
        choices=sorted(RESIDENT_RUNTIME_PRESETS),
        default=DEFAULT_RESIDENT_RUNTIME_PRESET,
        help=(
            "resident runtime scheduling preset; throughput-v1 is the default promoted by Gate180 and "
            "applies prefetch/H2D/calibration settings unless an individual option is explicitly provided; "
            "throughput-v2-fused adds resident integration auto dispatch as a non-default A/B candidate; "
            "use manual for the legacy conservative schedule"
        ),
    )
    run.add_argument(
        "--resident-prefetch-frames",
        type=int,
        default=0,
        help="number of light frames to prefetch into CPU RAM ahead of resident CUDA calibration",
    )
    run.add_argument(
        "--resident-prefetch-workers",
        type=int,
        default=1,
        help="worker threads used for resident light-frame CPU RAM prefetch",
    )
    run.add_argument(
        "--resident-prefetch-refill-mode",
        choices=["immediate", "queued", "deferred"],
        default="immediate",
        help=(
            "resident pinned-ring slot refill policy after host-buffer release; queued moves refill "
            "submission out of native callback timing for tuning runs"
        ),
    )
    run.add_argument(
        "--resident-h2d-mode",
        choices=["pageable", "pinned_async", "pinned_ring"],
        default="pageable",
        help=(
            "resident light upload mode: pageable cudaMemcpy, native pinned staging plus async H2D, "
            "or prefetch-ring pinned slots plus async H2D"
        ),
    )
    run.add_argument(
        "--resident-calibration-batch-frames",
        type=int,
        default=1,
        help=(
            "opt-in resident pinned-ring calibration batch size; values above 1 enqueue a "
            "small native batch before synchronizing"
        ),
    )
    run.add_argument(
        "--resident-calibration-streams",
        type=int,
        default=1,
        help=(
            "opt-in resident calibration stream count used inside native batch calibration; "
            "values above 1 allocate multiple raw device buffers and CUDA streams"
        ),
    )
    run.add_argument(
        "--resident-calibration-wave-frames",
        type=int,
        default=0,
        help=(
            "optional wave size for resident batch calibration; values above 0 process smaller "
            "native waves and release pinned prefetch slots more frequently"
        ),
    )
    run.add_argument(
        "--resident-calibration-release-mode",
        choices=["sync", "h2d_event", "auto", "callback_queue"],
        default="sync",
        help=(
            "resident batch host-slot release mode; auto enables h2d_event only when the calibration "
            "wave fills all native stream lanes; callback_queue is an explicit native multi-wave experiment"
        ),
    )
    run.add_argument(
        "--resident-master-cache-dir",
        help="optional shared resident master-frame cache directory reused across output directories",
    )
    run.add_argument(
        "--resident-source-dq-cache",
        choices=["off", "generate-calibration"],
        default="off",
        help=(
            "resident source-DQ cache route; generate-calibration runs CPU/tile calibration first so "
            "resident CUDA can consume GLASS-generated DQ sidecars from calibration_artifacts.json"
        ),
    )
    run.add_argument(
        "--resident-source-dq-cache-max-disk-fraction",
        type=float,
        default=0.75,
        help=(
            "maximum fraction of current free disk space that the generated resident source-DQ cache "
            "may consume before the route is blocked"
        ),
    )
    run.add_argument(
        "--allow-large-resident-source-dq-cache",
        action="store_true",
        help="override resident source-DQ cache disk preflight failures",
    )
    run.add_argument(
        "--resident-inline-source-dq",
        choices=["off", "cosmetic", "cosmetic_cuda"],
        default="off",
        help=(
            "resident source-DQ in-memory detector; cosmetic uses the CPU baseline mask, while cosmetic_cuda "
            "uses resident histogram robust stats plus CUDA threshold application without a calibrated cache"
        ),
    )
    run.add_argument(
        "--resident-inline-source-dq-hot-sigma",
        type=float,
        default=8.0,
        help="hot-pixel sigma threshold for --resident-inline-source-dq cosmetic/cosmetic_cuda",
    )
    run.add_argument(
        "--resident-inline-source-dq-cold-sigma",
        type=float,
        default=8.0,
        help="cold-pixel sigma threshold for --resident-inline-source-dq cosmetic/cosmetic_cuda",
    )
    run.add_argument(
        "--resident-output-maps",
        choices=["audit", "science", "minimal"],
        default="audit",
        help=(
            "resident output map set: audit writes all diagnostic maps, science keeps coverage and DQ, "
            "minimal writes only the master"
        ),
    )
    run.add_argument(
        "--resident-winsorized-mode",
        choices=["fast_approx", "hardened_cpu_parity"],
        default="fast_approx",
        help=(
            "resident CUDA winsorized_sigma implementation: fast_approx keeps the current optimized "
            "mean/std approximation, hardened_cpu_parity opts into the Gate261 median/IQR parity prototype"
        ),
    )
    run.add_argument(
        "--resident-fits-read-mode",
        choices=["auto", "fast", "astropy", "native_direct", "native_u16_gpu"],
        default=None,
        help=(
            "resident light FITS reader: default resident CUDA runs use guarded auto; explicit astropy remains "
            "the conservative compatibility escape hatch. auto promotes compatible "
            "BITPIX=16/BZERO=32768 light groups to guarded GPU raw decode when resident scheduling supports it, "
            "otherwise tries the bounded simple-primary fast path and falls back to astropy; fast requires the bounded path; "
            "native_direct decodes simple FITS directly into the resident host buffer; "
            "native_u16_gpu uploads compact BITPIX=16/BZERO=32768 payloads and decodes on GPU"
        ),
    )
    run.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    run.add_argument(
        "--integration-weighting",
        choices=["auto", "none", "simple_snr", "combined", "variance_aware"],
        default="auto",
    )
    run.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma", "minmax", "percentile", "mad", "median_sigma"],
        default="auto",
    )
    run.add_argument("--allow-partial", action="store_true")
    run.add_argument("--flat-floor", type=float, help="override calibration flat floor for this run")
    run.add_argument(
        "--resident-registration",
        choices=[
            "off",
            "translation_preview",
            "translation_ncc_subpixel",
            "translation_star_catalog",
            "similarity_cuda_catalog",
            "similarity_cuda_triangle",
            "external_matrix",
        ],
        default="off",
        help=(
            "resident CUDA registration mode; translation_preview uses downsampled phase correlation, "
            "translation_ncc_subpixel uses resident GPU NCC plus subpixel refinement, "
            "translation_star_catalog uses GPU star candidates plus pair-offset voting, "
            "similarity_cuda_catalog uses resident GPU star catalogs plus CUDA similarity refinement, "
            "similarity_cuda_triangle uses resident GPU star catalogs plus CUDA triangle descriptors, "
            "external_matrix applies matrices from a prior registration_results.json"
        ),
    )
    run.add_argument(
        "--resident-registration-results",
        help="registration_results.json to consume when --resident-registration external_matrix is selected",
    )
    run.add_argument(
        "--resident-warp-interpolation",
        choices=["bilinear", "lanczos3"],
        default="bilinear",
        help="resident CUDA matrix warp interpolation for similarity/external registration",
    )
    run.add_argument(
        "--resident-warp-clamping-threshold",
        type=float,
        default=-1.0,
        help="Lanczos3 local overshoot clamp threshold; negative disables clamping",
    )
    run.add_argument(
        "--resident-warp-batch-dispatch",
        choices=["loop", "chunked"],
        default="chunked",
        help="resident matrix batch warp dispatch mode",
    )
    run.add_argument(
        "--resident-integration-dispatch",
        choices=["stack", "fused_matrix", "auto"],
        default="stack",
        help=(
            "resident integration dispatch mode; auto selects the verified fused bilinear matrix route "
            "and keeps conservative stack routing for unverified routes"
        ),
    )
    run.add_argument("--resident-registration-max-shift", type=int, default=128)
    run.add_argument(
        "--resident-ncc-sample-stride",
        type=int,
        default=1,
        help="sample every Nth pixel in resident GPU NCC registration; 1 keeps full-resolution scoring",
    )
    run.add_argument(
        "--resident-ncc-fallback-score-threshold",
        type=float,
        default=0.0,
        help=(
            "when resident NCC sample stride is greater than 1, rerun low-score frames at full stride 1; "
            "0 disables fallback"
        ),
    )
    run.add_argument("--resident-subpixel-radius-steps", type=int, default=4)
    run.add_argument("--resident-subpixel-step", type=float, default=0.25)
    run.add_argument(
        "--resident-star-threshold",
        type=float,
        default=30.0,
        help="fixed resident star threshold; use 0 or a negative value for GPU mean/std auto-threshold trials",
    )
    run.add_argument("--resident-star-max-candidates", type=int, default=64)
    run.add_argument("--resident-star-tolerance-px", type=float, default=1.0)
    run.add_argument("--resident-star-grid-cols", type=int, default=0)
    run.add_argument("--resident-star-grid-rows", type=int, default=0)
    run.add_argument(
        "--resident-star-catalog-deterministic",
        action="store_true",
        help="use deterministic resident CUDA grid star cataloging when grid cataloging is enabled",
    )
    run.add_argument(
        "--resident-star-prior",
        choices=["none", "ncc", "auto_pierside"],
        default="none",
        help=(
            "optional prior for resident star-catalog voting: none, ncc, or auto_pierside "
            "to use PIERSIDE metadata for same-side NCC and flipped-side wide rotation search"
        ),
    )
    run.add_argument("--resident-star-prior-radius-px", type=float, default=4.0)
    run.add_argument(
        "--resident-local-normalization-mode",
        choices=["global_mean_std", "grid_mean_std"],
        default="global_mean_std",
        help="resident CUDA LN coefficient model used when --local-normalization enables LN",
    )
    run.add_argument(
        "--resident-local-normalization-tile-size",
        type=int,
        default=512,
        help="tile size for resident grid_mean_std local normalization",
    )
    run.add_argument(
        "--resident-star-core-preselect-top-k",
        type=int,
        default=0,
        help=(
            "for resident similarity_cuda_catalog, use GPU star-core metrics to preselect this many "
            "candidate matrices before pixel refinement; 0 disables preselection"
        ),
    )
    run.add_argument(
        "--resident-triangle-grid-top-per-cell",
        type=int,
        help="override resident triangle grid catalog top candidates retained per grid cell",
    )
    run.add_argument(
        "--resident-triangle-nms-scan-candidates",
        type=int,
        help="override resident triangle top-NMS scan candidate count for non-grid fallback cataloging",
    )
    run.add_argument(
        "--resident-triangle-nms-min-separation-px",
        type=float,
        help="override resident triangle catalog NMS minimum star separation in pixels",
    )
    run.add_argument(
        "--resident-triangle-pixel-refine",
        action="store_true",
        default=None,
        help="opt in to resident triangle pixel-refine; default is off unless enabled in the processing plan",
    )
    run.add_argument(
        "--resident-triangle-pixel-refine-coarse-stride",
        type=int,
        help="override resident triangle pixel-refine coarse sample stride",
    )
    run.add_argument(
        "--resident-triangle-pixel-refine-final-stride",
        type=int,
        help="override resident triangle pixel-refine final sample stride",
    )
    run.add_argument(
        "--resident-triangle-pixel-refine-fast-coarse",
        action="store_true",
        help=(
            "explicit fast mode: raise resident triangle pixel-refine coarse sample stride to at least "
            "the final stride; changes sampling and is recorded in artifacts"
        ),
    )
    run.add_argument(
        "--resident-triangle-centroid-background",
        choices=["global_mean", "local_median"],
        help="resident triangle centroid background model; default global_mean improves CPU detector parity",
    )
    run.add_argument(
        "--resident-triangle-min-agreement-score",
        type=float,
        help=(
            "optional resident triangle pixel-agreement gate; values in [0, 1] mark low-NCC/high-RMS "
            "refinements as failed"
        ),
    )
    run.add_argument(
        "--resident-triangle-agreement-rms-scale",
        type=float,
        help="ADU RMS scale used to normalize resident triangle pixel-agreement scores; default comes from the plan",
    )
    run.add_argument(
        "--resident-triangle-agreement-action",
        choices=["fail", "downweight", "flag"],
        help=(
            "action when --resident-triangle-min-agreement-score is missed; "
            "fail preserves the hard gate, downweight keeps the frame with a score/threshold multiplier, "
            "flag records the miss without changing the frame weight"
        ),
    )
    run.add_argument(
        "--resident-triangle-agreement-min-weight",
        type=float,
        help="minimum multiplier for agreement downweight action; must be in [0, 1], default comes from the plan",
    )
    run.add_argument(
        "--resident-registration-motion-weighting",
        choices=["off", "translation_mad"],
        default="off",
        help="optional registration-motion robust outlier downweighting; default off",
    )
    run.add_argument(
        "--resident-registration-motion-threshold-sigma",
        type=float,
        default=16.0,
        help="robust motion score threshold for registration-motion downweighting",
    )
    run.add_argument(
        "--resident-registration-motion-min-weight",
        type=float,
        default=0.05,
        help="minimum multiplier for registration-motion downweighting; must be in [0, 1]",
    )
    run.add_argument(
        "--resident-registration-motion-power",
        type=float,
        default=2.0,
        help="power used by the smooth registration-motion multiplier falloff",
    )
    run.add_argument(
        "--resident-registration-motion-scale-floor-px",
        type=float,
        default=1.0,
        help="minimum robust motion scale in pixels to avoid divide-by-zero on tight dithers",
    )
    run.add_argument(
        "--resident-registration-quality-gate",
        choices=["auto", "off", "warn", "exclude"],
        default="auto",
        help=(
            "resident registration admission action; auto excludes low-confidence triangle fits, "
            "warn records decisions without changing weights, off disables the gate"
        ),
    )
    run.add_argument(
        "--resident-registration-quality-min-inliers",
        type=int,
        default=4,
        help="minimum inlier count for resident registration admission; Gate433 default is 4",
    )
    run.add_argument(
        "--resident-registration-quality-max-rms-px",
        type=float,
        help="optional maximum registration RMS for resident admission; omitted records RMS without gating on it",
    )
    run.add_argument(
        "--resident-frame-weight-proposal",
        help="optional frame-weight proposal JSON produced by frame-weight-proposal; default disabled",
    )
    run.add_argument(
        "--resident-tile-local-policy-replay",
        help=(
            "optional tile-local-policy-replay JSON; recorded by default and applied only with "
            "--resident-tile-local-policy-mode apply_mean"
        ),
    )
    run.add_argument(
        "--resident-tile-local-policy-mode",
        choices=["record", "apply_mean", "apply"],
        default="record",
        help=(
            "how to consume --resident-tile-local-policy-replay; record preserves current output, "
            "apply_mean enables the opt-in resident stack weighted-mean path for rejection=none, "
            "apply enables the matching stack path for none/sigma/winsorized rejection"
        ),
    )
    run.add_argument(
        "--reference-frame-id",
        help="reference frame id, file name, or stem for registration",
    )
    run.add_argument(
        "--exclude-frame-id",
        action="append",
        default=[],
        help="frame id, file name, or stem to exclude from resident integration; can be repeated",
    )
    run.set_defaults(func=cmd_run)

    resume = sub.add_parser("resume", help="resume a run directory")
    resume.add_argument("--run", required=True)
    resume.set_defaults(func=cmd_resume)

    report = sub.add_parser("report", help="write an HTML report")
    report.add_argument("--run", required=True)
    report.add_argument("--out", required=True)
    report.add_argument("--manifest")
    report.add_argument("--plan")
    report.add_argument("--compare-json", help="optional compare JSON to summarize in the report")
    report.add_argument("--acceptance-audit", help="optional acceptance-audit JSON to summarize in the report")
    report.add_argument("--stack-engine-contract", help="optional StackEngine contract audit JSON to summarize")
    report.add_argument("--pipeline-contract", help="optional pipeline invariant contract audit JSON to summarize")
    report.add_argument("--local-norm-contract", help="optional local-normalization contract JSON to summarize")
    report.add_argument("--registration-quality", help="optional registration quality contract JSON to summarize")
    report.add_argument("--warp-quality", help="optional warp quality contract JSON to summarize")
    report.set_defaults(func=cmd_report)

    audit = sub.add_parser("audit", help="scan, plan, and report in one command")
    audit.add_argument("--root", required=True)
    audit.add_argument("--out", required=True)
    audit.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="auto")
    audit.add_argument("--vram-budget-gb", type=float)
    audit.add_argument("--ram-budget-gb", type=float)
    audit.add_argument("--tile-size", type=int, default=512)
    audit.add_argument(
        "--memory-mode",
        choices=["tile", "resident"],
        default=DEFAULT_MEMORY_MODE,
        help=(
            "execution memory strategy for the run portion of audit; default resident uses CUDA when "
            "available and falls back to tile for CPU"
        ),
    )
    audit.add_argument(
        "--resident-runtime-preset",
        choices=sorted(RESIDENT_RUNTIME_PRESETS),
        default=DEFAULT_RESIDENT_RUNTIME_PRESET,
        help=(
            "resident runtime scheduling preset for the audit run; throughput-v1 is the default promoted by "
            "Gate180 and applies prefetch/H2D/calibration settings unless an individual option is explicitly "
            "provided; throughput-v2-fused adds resident integration auto dispatch as a non-default A/B "
            "candidate; use manual for the legacy conservative schedule"
        ),
    )
    audit.add_argument(
        "--resident-prefetch-frames",
        type=int,
        default=0,
        help="number of light frames to prefetch into CPU RAM ahead of resident CUDA calibration",
    )
    audit.add_argument(
        "--resident-prefetch-workers",
        type=int,
        default=1,
        help="worker threads used for resident light-frame CPU RAM prefetch",
    )
    audit.add_argument(
        "--resident-prefetch-refill-mode",
        choices=["immediate", "queued", "deferred"],
        default="immediate",
        help="resident pinned-ring slot refill policy for resident audit",
    )
    audit.add_argument(
        "--resident-h2d-mode",
        choices=["pageable", "pinned_async", "pinned_ring"],
        default="pageable",
        help="resident light upload mode for resident audit",
    )
    audit.add_argument(
        "--resident-calibration-batch-frames",
        type=int,
        default=1,
        help="opt-in resident pinned-ring calibration batch size for resident audit",
    )
    audit.add_argument(
        "--resident-calibration-streams",
        type=int,
        default=1,
        help="opt-in resident calibration stream count for resident audit batch calibration",
    )
    audit.add_argument(
        "--resident-calibration-wave-frames",
        type=int,
        default=0,
        help="optional wave size for resident audit batch calibration",
    )
    audit.add_argument(
        "--resident-calibration-release-mode",
        choices=["sync", "h2d_event", "auto", "callback_queue"],
        default="sync",
        help="resident audit batch host-slot release mode",
    )
    audit.add_argument(
        "--resident-master-cache-dir",
        help="optional shared resident master-frame cache directory reused across audit output directories",
    )
    audit.add_argument(
        "--resident-output-maps",
        choices=["audit", "science", "minimal"],
        default="audit",
        help=(
            "resident output map set for audit: audit writes all diagnostic maps, science keeps coverage "
            "and DQ, minimal writes only the master"
        ),
    )
    audit.add_argument(
        "--resident-inline-source-dq",
        choices=["off", "cosmetic", "cosmetic_cuda"],
        default="off",
        help=(
            "resident source-DQ in-memory detector for audit; cosmetic uses the CPU baseline mask, while "
            "cosmetic_cuda uses resident histogram robust stats plus CUDA threshold application without materializing "
            "a calibrated cache"
        ),
    )
    audit.add_argument(
        "--resident-inline-source-dq-hot-sigma",
        type=float,
        default=8.0,
        help="hot-pixel sigma threshold for resident audit inline source-DQ cosmetic/cosmetic_cuda mode",
    )
    audit.add_argument(
        "--resident-inline-source-dq-cold-sigma",
        type=float,
        default=8.0,
        help="cold-pixel sigma threshold for resident audit inline source-DQ cosmetic/cosmetic_cuda mode",
    )
    audit.add_argument(
        "--resident-winsorized-mode",
        choices=["fast_approx", "hardened_cpu_parity"],
        default="fast_approx",
        help=(
            "resident CUDA winsorized_sigma implementation for audit: fast_approx keeps the current "
            "optimized approximation, hardened_cpu_parity opts into the Gate261 median/IQR parity prototype"
        ),
    )
    audit.add_argument(
        "--resident-fits-read-mode",
        choices=["auto", "fast", "astropy", "native_direct", "native_u16_gpu"],
        default=None,
        help=(
            "resident audit light FITS reader; default resident CUDA audits use guarded auto and explicit astropy "
            "remains the compatibility escape hatch. auto promotes guarded "
            "BITPIX=16/BZERO=32768 groups to GPU raw decode when resident scheduling supports it and otherwise "
            "tries bounded fast primary-image reading with astropy fallback, native_direct decodes into the resident host buffer, "
            "and native_u16_gpu uploads compact BITPIX=16/BZERO=32768 payloads for GPU decode"
        ),
    )
    audit.add_argument(
        "--registration-method",
        choices=["auto", "star", "astroalign", "cuda_catalog", "cuda_triangle"],
        default="auto",
        help="registration method passed to the gated run portion of audit",
    )
    audit.add_argument(
        "--warp-interpolation",
        choices=["nearest", "bilinear", "bicubic", "lanczos3"],
        default="bilinear",
        help="tile-mode warp interpolator registry entry",
    )
    audit.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    audit.add_argument(
        "--integration-weighting",
        choices=["auto", "none", "simple_snr", "combined", "variance_aware"],
        default="auto",
    )
    audit.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma", "minmax", "percentile", "mad", "median_sigma"],
        default="auto",
    )
    audit.add_argument("--flat-floor", type=float, help="override calibration flat floor for resident audit")
    audit.add_argument(
        "--resident-registration",
        choices=[
            "off",
            "translation_preview",
            "translation_ncc_subpixel",
            "translation_star_catalog",
            "similarity_cuda_catalog",
            "similarity_cuda_triangle",
            "external_matrix",
        ],
        default="off",
        help="resident CUDA registration mode for --memory-mode resident",
    )
    audit.add_argument(
        "--resident-registration-results",
        help="registration_results.json consumed by resident external_matrix audit",
    )
    audit.add_argument(
        "--resident-warp-interpolation",
        choices=["bilinear", "lanczos3"],
        default="bilinear",
        help="resident CUDA matrix warp interpolation for resident audit",
    )
    audit.add_argument("--resident-warp-clamping-threshold", type=float, default=-1.0)
    audit.add_argument(
        "--resident-warp-batch-dispatch",
        choices=["loop", "chunked"],
        default="chunked",
        help="resident matrix batch warp dispatch mode",
    )
    audit.add_argument(
        "--resident-integration-dispatch",
        choices=["stack", "fused_matrix", "auto"],
        default="stack",
        help=(
            "resident integration dispatch mode; auto selects the verified fused bilinear matrix route "
            "and keeps conservative stack routing for unverified routes"
        ),
    )
    audit.add_argument("--resident-registration-max-shift", type=int, default=128)
    audit.add_argument("--resident-ncc-sample-stride", type=int, default=1)
    audit.add_argument("--resident-ncc-fallback-score-threshold", type=float, default=0.0)
    audit.add_argument("--resident-subpixel-radius-steps", type=int, default=4)
    audit.add_argument("--resident-subpixel-step", type=float, default=0.25)
    audit.add_argument(
        "--resident-star-threshold",
        type=float,
        default=30.0,
        help="fixed resident star threshold; use 0 or negative for GPU mean/std auto-threshold trials",
    )
    audit.add_argument("--resident-star-max-candidates", type=int, default=64)
    audit.add_argument("--resident-star-tolerance-px", type=float, default=1.0)
    audit.add_argument("--resident-star-grid-cols", type=int, default=0)
    audit.add_argument("--resident-star-grid-rows", type=int, default=0)
    audit.add_argument(
        "--resident-star-catalog-deterministic",
        action="store_true",
        help="use deterministic resident CUDA grid star cataloging when grid cataloging is enabled",
    )
    audit.add_argument(
        "--resident-star-prior",
        choices=["none", "ncc", "auto_pierside"],
        default="none",
        help="optional prior for resident star-catalog voting in resident audit",
    )
    audit.add_argument("--resident-star-prior-radius-px", type=float, default=4.0)
    audit.add_argument(
        "--resident-star-core-preselect-top-k",
        type=int,
        default=0,
        help="preselect resident similarity candidates with GPU star-core metrics before pixel refinement",
    )
    audit.add_argument(
        "--resident-triangle-grid-top-per-cell",
        type=int,
        help="override resident triangle grid catalog top candidates retained per grid cell for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-nms-scan-candidates",
        type=int,
        help="override resident triangle top-NMS scan candidate count for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-nms-min-separation-px",
        type=float,
        help="override resident triangle catalog NMS minimum star separation in pixels for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-pixel-refine",
        action="store_true",
        default=None,
        help="opt in to resident triangle pixel-refine for resident audit; default is off unless enabled in the plan",
    )
    audit.add_argument(
        "--resident-triangle-pixel-refine-coarse-stride",
        type=int,
        help="override resident triangle pixel-refine coarse sample stride for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-pixel-refine-final-stride",
        type=int,
        help="override resident triangle pixel-refine final sample stride for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-pixel-refine-fast-coarse",
        action="store_true",
        help=(
            "explicit fast mode: raise resident triangle pixel-refine coarse sample stride to at least "
            "the final stride for resident audit"
        ),
    )
    audit.add_argument(
        "--resident-triangle-centroid-background",
        choices=["global_mean", "local_median"],
        help="resident triangle centroid background model for resident audit",
    )
    audit.add_argument(
        "--resident-triangle-min-agreement-score",
        type=float,
        help=(
            "optional resident triangle pixel-agreement gate for audit runs; values in [0, 1] "
            "mark low-NCC/high-RMS refinements as failed"
        ),
    )
    audit.add_argument(
        "--resident-triangle-agreement-rms-scale",
        type=float,
        help="ADU RMS scale used to normalize resident triangle pixel-agreement scores for audit runs",
    )
    audit.add_argument(
        "--resident-triangle-agreement-action",
        choices=["fail", "downweight", "flag"],
        help=(
            "audit-run action when --resident-triangle-min-agreement-score is missed; "
            "fail preserves the hard gate, downweight keeps the frame with a score/threshold multiplier, "
            "flag records the miss without changing the frame weight"
        ),
    )
    audit.add_argument(
        "--resident-triangle-agreement-min-weight",
        type=float,
        help="minimum multiplier for audit-run agreement downweight action; must be in [0, 1]",
    )
    audit.add_argument(
        "--resident-registration-motion-weighting",
        choices=["off", "translation_mad"],
        default="off",
        help="optional registration-motion robust outlier downweighting for resident audit; default off",
    )
    audit.add_argument("--resident-registration-motion-threshold-sigma", type=float, default=16.0)
    audit.add_argument("--resident-registration-motion-min-weight", type=float, default=0.05)
    audit.add_argument("--resident-registration-motion-power", type=float, default=2.0)
    audit.add_argument("--resident-registration-motion-scale-floor-px", type=float, default=1.0)
    audit.add_argument(
        "--resident-registration-quality-gate",
        choices=["auto", "off", "warn", "exclude"],
        default="auto",
        help="resident registration admission action for resident audit runs",
    )
    audit.add_argument("--resident-registration-quality-min-inliers", type=int, default=4)
    audit.add_argument("--resident-registration-quality-max-rms-px", type=float)
    audit.add_argument(
        "--resident-frame-weight-proposal",
        help="optional frame-weight proposal JSON produced by frame-weight-proposal for resident audit",
    )
    audit.add_argument(
        "--resident-tile-local-policy-replay",
        help=(
            "optional tile-local-policy-replay JSON for resident audit; recorded by default and applied only with "
            "--resident-tile-local-policy-mode apply_mean"
        ),
    )
    audit.add_argument(
        "--resident-tile-local-policy-mode",
        choices=["record", "apply_mean", "apply"],
        default="record",
        help=(
            "how to consume --resident-tile-local-policy-replay in resident audit; record preserves current "
            "output, apply_mean enables the opt-in stack weighted-mean path for rejection=none, "
            "apply enables the matching stack path for none/sigma/winsorized rejection"
        ),
    )
    audit.add_argument(
        "--resident-local-normalization-mode",
        choices=["global_mean_std", "grid_mean_std"],
        default="global_mean_std",
        help="resident CUDA LN coefficient model used when audit enables LN",
    )
    audit.add_argument("--resident-local-normalization-tile-size", type=int, default=512)
    audit.add_argument("--reference-frame-id")
    audit.add_argument("--exclude-frame-id", action="append", default=[])
    audit.set_defaults(func=cmd_audit)

    compare = sub.add_parser("compare", help="compare GLASS output to a black-box reference")
    compare.add_argument("--glass", required=True)
    compare.add_argument("--reference", required=True)
    compare.add_argument("--out", required=True)
    compare.add_argument("--glass-time-seconds", type=float)
    compare.add_argument("--reference-time-seconds", type=float)
    compare.add_argument("--glass-label", default="GLASS")
    compare.add_argument("--reference-label", default="reference")
    compare.add_argument("--glass-scale", type=float, help="scale GLASS pixels before comparison")
    compare.add_argument("--glass-offset", type=float, help="offset GLASS pixels before comparison")
    compare.add_argument("--clip-low", type=float, help="clip transformed GLASS pixels to this lower bound")
    compare.add_argument("--clip-high", type=float, help="clip transformed GLASS pixels to this upper bound")
    compare.add_argument("--diagnostics-dir", help="optional directory for compare preview PNGs and residual hotspots")
    compare.add_argument("--diagnostic-max-size", type=int, default=1024, help="maximum preview PNG width or height")
    compare.add_argument("--hotspot-tile-size", type=int, default=512, help="tile size for residual hotspot ranking")
    compare.add_argument("--ignore-border-px", type=int, default=0, help="ignore this many pixels on each edge for metrics")
    compare.add_argument("--glass-coverage-map", help="optional GLASS coverage map used to mask comparison metrics")
    compare.add_argument("--min-coverage", type=float, help="minimum GLASS coverage required for comparison metrics")
    compare.set_defaults(func=cmd_compare)

    compare_outliers = sub.add_parser(
        "compare-outliers",
        help="audit spatial locations of comparison tail/outlier residuals",
    )
    compare_outliers.add_argument("--glass", required=True)
    compare_outliers.add_argument("--reference", required=True)
    compare_outliers.add_argument("--out", required=True, help="output outlier audit JSON")
    compare_outliers.add_argument("--markdown", help="optional output Markdown summary")
    compare_outliers.add_argument("--glass-scale", type=float, help="scale GLASS pixels before comparison")
    compare_outliers.add_argument("--glass-offset", type=float, help="offset GLASS pixels before comparison")
    compare_outliers.add_argument("--clip-low", type=float, help="clip transformed GLASS pixels to this lower bound")
    compare_outliers.add_argument("--clip-high", type=float, help="clip transformed GLASS pixels to this upper bound")
    compare_outliers.add_argument(
        "--glass-coverage-map",
        help="optional GLASS coverage map used to mask comparison metrics",
    )
    compare_outliers.add_argument(
        "--min-coverage",
        type=float,
        help="minimum GLASS coverage required for comparison metrics",
    )
    compare_outliers.add_argument(
        "--ignore-border-px",
        type=int,
        default=0,
        help="ignore this many pixels on each edge for metrics",
    )
    compare_outliers.add_argument(
        "--tail-percentile",
        type=float,
        default=99.0,
        help="absolute-difference percentile used to define the tail mask",
    )
    compare_outliers.add_argument(
        "--target-abs-diff",
        type=float,
        help="optional strict target threshold; exceedance pixels are reported separately",
    )
    compare_outliers.add_argument("--tile-size", type=int, default=512, help="tile size for outlier localization")
    compare_outliers.add_argument("--top-tiles", type=int, default=16, help="number of top outlier tiles to report")
    compare_outliers.add_argument("--top-pixels", type=int, default=32, help="number of top pixels to report")
    compare_outliers.add_argument(
        "--edge-band-px",
        type=int,
        default=64,
        help="distance from compared-region edge considered an edge-band tail pixel",
    )
    compare_outliers.set_defaults(func=cmd_compare_outliers)

    tile_pack = sub.add_parser(
        "compare-tile-pack",
        help="export FITS/PNG cutouts for top compare outlier tiles",
    )
    tile_pack.add_argument("--audit", required=True, help="compare-outliers JSON artifact")
    tile_pack.add_argument("--out-dir", required=True, help="output directory for tile cutout package")
    tile_pack.add_argument("--max-tiles", type=int, default=4, help="number of top tiles to export")
    tile_pack.add_argument("--pad-px", type=int, default=0, help="padding around each top tile")
    tile_pack.add_argument(
        "--preview-max-size",
        type=int,
        default=768,
        help="maximum preview PNG dimension",
    )
    tile_pack.add_argument("--no-png", action="store_true", help="write FITS cutouts only")
    tile_pack.set_defaults(func=cmd_compare_tile_pack)

    tile_attr = sub.add_parser(
        "compare-tile-attribution",
        help="join compare residual tiles with GLASS output maps and frame accounting",
    )
    tile_attr.add_argument("--tile-pack", required=True, help="tile_pack_manifest.json from compare-tile-pack")
    tile_attr.add_argument("--run", required=True, help="GLASS run directory containing integration/frame artifacts")
    tile_attr.add_argument("--out", required=True, help="output attribution JSON")
    tile_attr.add_argument("--markdown", help="optional output Markdown summary")
    tile_attr.add_argument("--filter", help="optional filter name used to select integration output maps")
    tile_attr.add_argument("--frame-limit", type=int, default=16, help="number of frame-accounting rows to include")
    tile_attr.set_defaults(func=cmd_compare_tile_attribution)

    tile_replay = sub.add_parser(
        "compare-tile-replay",
        help="bounded per-frame replay of localized compare residual tiles",
    )
    tile_replay.add_argument("--tile-pack", required=True, help="tile_pack_manifest.json from compare-tile-pack")
    tile_replay.add_argument("--run", required=True, help="GLASS run directory containing integration/frame artifacts")
    tile_replay.add_argument("--out", required=True, help="output replay JSON")
    tile_replay.add_argument("--markdown", help="optional output Markdown summary")
    tile_replay.add_argument("--filter", help="optional filter name used to select integration output maps")
    tile_replay.add_argument("--master-cache-dir", help="resident master cache directory; defaults to run_command discovery")
    tile_replay.add_argument(
        "--frame-strategy",
        choices=["lowest_weight", "downweighted", "frame_id"],
        default="lowest_weight",
        help="which frames to replay first",
    )
    tile_replay.add_argument("--max-frames", type=int, default=32, help="maximum frames to replay; use 0 for all selected")
    tile_replay.add_argument("--low-sigma", type=float, help="override low sigma for diagnostic proxy rejection")
    tile_replay.add_argument("--high-sigma", type=float, help="override high sigma for diagnostic proxy rejection")
    tile_replay.add_argument(
        "--replay-interpolation",
        choices=["bilinear", "lanczos3"],
        default="bilinear",
        help="CPU interpolation used for bounded diagnostic replay",
    )
    tile_replay.set_defaults(func=cmd_compare_tile_replay)

    tile_integration = sub.add_parser(
        "compare-tile-integration",
        help="replay localized residual tiles through integration rejection diagnostics",
    )
    tile_integration.add_argument("--tile-pack", required=True, help="tile_pack_manifest.json from compare-tile-pack")
    tile_integration.add_argument("--run", required=True, help="GLASS run directory containing integration/frame artifacts")
    tile_integration.add_argument("--out", required=True, help="output integration audit JSON")
    tile_integration.add_argument("--markdown", help="optional output Markdown summary")
    tile_integration.add_argument("--filter", help="optional filter name used to select integration output maps")
    tile_integration.add_argument(
        "--master-cache-dir",
        help="resident master cache directory; defaults to run_command discovery",
    )
    tile_integration.add_argument(
        "--frame-strategy",
        choices=["lowest_weight", "downweighted", "frame_id"],
        default="frame_id",
        help="which positive-weight frames to replay",
    )
    tile_integration.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="maximum frames to replay; use 0 for all selected positive-weight frames",
    )
    tile_integration.add_argument("--max-tiles", type=int, default=0, help="maximum tiles from tile pack; 0 audits all")
    tile_integration.add_argument("--low-sigma", type=float, help="override low sigma for rejection replay")
    tile_integration.add_argument("--high-sigma", type=float, help="override high sigma for rejection replay")
    tile_integration.add_argument(
        "--rejection",
        choices=["none", "sigma_clip", "winsorized_sigma"],
        help="override rejection mode; defaults to integration_results.json",
    )
    tile_integration.add_argument(
        "--replay-interpolation",
        choices=["bilinear", "lanczos3"],
        default="lanczos3",
        help="CPU interpolation used for bounded diagnostic replay",
    )
    tile_integration.add_argument("--focus-frame", action="append", default=[], help="focus frame id; may be repeated")
    tile_integration.add_argument("--focus-range-start", help="first focus frame id, for example F000100")
    tile_integration.add_argument("--focus-range-end", help="last focus frame id, for example F000110")
    tile_integration.add_argument("--control-frame", action="append", default=[], help="control frame id; may be repeated")
    tile_integration.add_argument(
        "--control-before",
        type=int,
        default=5,
        help="number of positive-weight frames before the focus range used as controls",
    )
    tile_integration.add_argument(
        "--control-after",
        type=int,
        default=5,
        help="number of positive-weight frames after the focus range used as controls",
    )
    tile_integration.set_defaults(func=cmd_compare_tile_integration)

    residual_tiles = sub.add_parser(
        "residual-tile-candidates",
        help="merge compare-outlier audits into a non-overlapping residual tile candidate manifest",
    )
    residual_tiles.add_argument(
        "--outlier-audit",
        action="append",
        required=True,
        help="compare-outliers JSON artifact; may be repeated",
    )
    residual_tiles.add_argument(
        "--known-tile-pack",
        action="append",
        default=[],
        help="existing tile_pack_manifest.json used only to flag known-region overlaps",
    )
    residual_tiles.add_argument("--out", required=True, help="output residual tile candidate JSON")
    residual_tiles.add_argument("--markdown", help="optional output Markdown summary")
    residual_tiles.add_argument("--max-tiles", type=int, default=16, help="maximum selected candidate tiles")
    residual_tiles.add_argument("--min-tail-pixels", type=int, default=1, help="minimum tail pixels per source tile")
    residual_tiles.add_argument(
        "--min-tail-fraction",
        type=float,
        default=0.0,
        help="minimum tail fraction per source tile",
    )
    residual_tiles.add_argument(
        "--prefer",
        choices=["tail_pixels", "tail_fraction", "tail_abs_mean", "tail_abs_max"],
        default="tail_pixels",
        help="ranking metric for candidate selection",
    )
    residual_tiles.add_argument(
        "--known-overlap-mode",
        choices=["include", "exclude", "only"],
        default="include",
        help="whether to include, exclude, or keep only candidates overlapping known tile packs",
    )
    residual_tiles.add_argument(
        "--allow-overlaps",
        action="store_true",
        help="keep overlapping selected candidates instead of greedy non-overlap filtering",
    )
    residual_tiles.set_defaults(func=cmd_residual_tile_candidates)

    frame_weight_proposal = sub.add_parser(
        "frame-weight-proposal",
        help="derive an explicit frame multiplier proposal from localized integration diagnostics",
    )
    frame_weight_proposal.add_argument(
        "--integration-audit",
        required=True,
        help="compare-tile-integration JSON artifact containing focus/control contribution summaries",
    )
    frame_weight_proposal.add_argument("--out", required=True, help="output frame-weight proposal JSON")
    frame_weight_proposal.add_argument("--markdown", help="optional output Markdown summary")
    frame_weight_proposal.add_argument(
        "--method",
        choices=["control_ratio"],
        default="control_ratio",
        help="proposal method; control_ratio scales focus frames by control/focus contribution mean",
    )
    frame_weight_proposal.add_argument("--min-multiplier", type=float, default=0.05)
    frame_weight_proposal.add_argument("--max-multiplier", type=float, default=1.0)
    frame_weight_proposal.add_argument("--reason", help="optional reason recorded on every proposed frame row")
    frame_weight_proposal.set_defaults(func=cmd_frame_weight_proposal)

    frame_weight_proposal_audit = sub.add_parser(
        "frame-weight-proposal-audit",
        help="check whether a frame-weight proposal moves localized residual tiles in the right direction",
    )
    frame_weight_proposal_audit.add_argument(
        "--integration-audit",
        required=True,
        help="compare-tile-integration JSON artifact containing focus contribution summaries",
    )
    frame_weight_proposal_audit.add_argument("--proposal", required=True, help="frame-weight proposal JSON")
    frame_weight_proposal_audit.add_argument(
        "--tile-pack",
        help="optional tile_pack_manifest.json; defaults to the path recorded in the integration audit",
    )
    frame_weight_proposal_audit.add_argument("--out", required=True, help="output direction-audit JSON")
    frame_weight_proposal_audit.add_argument("--markdown", help="optional output Markdown summary")
    frame_weight_proposal_audit.add_argument(
        "--glass-scale",
        type=float,
        help="optional GLASS-to-reference scale; defaults to tile-pack candidate_transform.scale",
    )
    frame_weight_proposal_audit.set_defaults(func=cmd_frame_weight_proposal_audit)

    frame_family = sub.add_parser(
        "compare-frame-family",
        help="compare a focused frame-id family against neighboring control frames",
    )
    frame_family.add_argument("--replay", required=True, help="compare-tile-replay JSON artifact")
    frame_family.add_argument("--run", required=True, help="GLASS run directory containing frame artifacts")
    frame_family.add_argument("--out", required=True, help="output frame-family audit JSON")
    frame_family.add_argument("--markdown", help="optional output Markdown summary")
    frame_family.add_argument("--focus-frame", action="append", default=[], help="focus frame id; may be repeated")
    frame_family.add_argument("--focus-range-start", help="first focus frame id, for example F000100")
    frame_family.add_argument("--focus-range-end", help="last focus frame id, for example F000110")
    frame_family.add_argument("--control-frame", action="append", default=[], help="control frame id; may be repeated")
    frame_family.add_argument(
        "--control-before",
        type=int,
        default=5,
        help="number of positive-weight frames before the focus range used as controls",
    )
    frame_family.add_argument(
        "--control-after",
        type=int,
        default=5,
        help="number of positive-weight frames after the focus range used as controls",
    )
    frame_family.set_defaults(func=cmd_compare_frame_family)

    resident_capture = sub.add_parser(
        "resident-tile-capture",
        help="capture selected post-warp resident CUDA frame tiles for residual diagnostics",
    )
    resident_capture.add_argument("--tile-pack", required=True, help="tile_pack_manifest.json from compare-tile-pack")
    resident_capture.add_argument("--run", required=True, help="GLASS run directory containing frame artifacts")
    resident_capture.add_argument("--out-dir", required=True, help="directory for optional captured tile FITS files")
    resident_capture.add_argument("--out", required=True, help="output resident tile capture JSON")
    resident_capture.add_argument("--markdown", help="optional output Markdown summary")
    resident_capture.add_argument("--replay", help="optional compare-tile-replay JSON used for CPU replay comparison")
    resident_capture.add_argument("--filter", help="optional filter name used to select integration outputs")
    resident_capture.add_argument("--frame-id", action="append", default=[], help="frame id to capture; may be repeated")
    resident_capture.add_argument("--frame-range-start", help="first frame id in a capture range, for example F000100")
    resident_capture.add_argument("--frame-range-end", help="last frame id in a capture range, for example F000110")
    resident_capture.add_argument("--max-frames", type=int, default=0, help="maximum selected frames; 0 captures all")
    resident_capture.add_argument("--max-tiles", type=int, default=0, help="maximum tiles from tile pack; 0 captures all")
    resident_capture.add_argument("--master-cache-dir", help="resident master cache directory; defaults to run command discovery")
    resident_capture.add_argument(
        "--interpolation",
        choices=["bilinear", "lanczos3"],
        help="resident matrix warp interpolation; defaults to run command discovery",
    )
    resident_capture.add_argument(
        "--clamping-threshold",
        type=float,
        help="Lanczos3 clamping threshold; defaults to run command discovery",
    )
    resident_capture.add_argument("--write-tiles", action="store_true", help="write captured FITS tile artifacts")
    resident_capture.set_defaults(func=cmd_resident_tile_capture)

    resident_contribution = sub.add_parser(
        "resident-tile-contribution",
        help="capture resident CUDA post-warp tiles and replay contribution/rejection diagnostics",
    )
    resident_contribution.add_argument("--tile-pack", required=True, help="tile_pack_manifest.json from compare-tile-pack")
    resident_contribution.add_argument("--run", required=True, help="GLASS run directory containing frame artifacts")
    resident_contribution.add_argument("--out", required=True, help="output resident tile contribution JSON")
    resident_contribution.add_argument("--markdown", help="optional output Markdown summary")
    resident_contribution.add_argument("--filter", help="optional filter name used to select integration outputs")
    resident_contribution.add_argument(
        "--frame-strategy",
        choices=["lowest_weight", "downweighted", "frame_id"],
        default="frame_id",
        help="which positive-weight frames to capture",
    )
    resident_contribution.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="maximum frames to capture; use 0 for all selected positive-weight frames",
    )
    resident_contribution.add_argument("--max-tiles", type=int, default=0, help="maximum tiles from tile pack; 0 captures all")
    resident_contribution.add_argument("--master-cache-dir", help="resident master cache directory; defaults to run command discovery")
    resident_contribution.add_argument(
        "--interpolation",
        choices=["bilinear", "lanczos3"],
        help="resident matrix warp interpolation; defaults to run command discovery",
    )
    resident_contribution.add_argument(
        "--clamping-threshold",
        type=float,
        help="Lanczos3 clamping threshold; defaults to run command discovery",
    )
    resident_contribution.add_argument(
        "--rejection",
        choices=["none", "sigma_clip", "winsorized_sigma"],
        help="override rejection mode; defaults to integration_results.json",
    )
    resident_contribution.add_argument("--low-sigma", type=float, help="override low sigma for contribution replay")
    resident_contribution.add_argument("--high-sigma", type=float, help="override high sigma for contribution replay")
    resident_contribution.add_argument("--focus-frame", action="append", default=[], help="focus frame id; may be repeated")
    resident_contribution.add_argument("--focus-range-start", help="first focus frame id, for example F000100")
    resident_contribution.add_argument("--focus-range-end", help="last focus frame id, for example F000110")
    resident_contribution.add_argument("--control-frame", action="append", default=[], help="control frame id; may be repeated")
    resident_contribution.add_argument("--control-before", type=int, default=5)
    resident_contribution.add_argument("--control-after", type=int, default=5)
    resident_contribution.set_defaults(func=cmd_resident_tile_contribution)

    tile_local_policy = sub.add_parser(
        "tile-local-policy-proposal",
        help="derive a tile-local multiplier proposal from resident contribution and residual direction",
    )
    tile_local_policy.add_argument(
        "--contribution",
        required=True,
        help="resident-tile-contribution JSON artifact",
    )
    tile_local_policy.add_argument(
        "--tile-pack",
        help="optional tile_pack_manifest.json; defaults to the path recorded in the contribution artifact",
    )
    tile_local_policy.add_argument("--out", required=True, help="output tile-local policy proposal JSON")
    tile_local_policy.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_policy.add_argument("--target-group", choices=["focus", "control"], default="focus")
    tile_local_policy.add_argument(
        "--residual-stat",
        choices=["signed_mean", "tail_signed_mean"],
        default="signed_mean",
        help="residual summary used to solve the proposed tile-local multiplier",
    )
    tile_local_policy.add_argument("--min-multiplier", type=float, default=0.0)
    tile_local_policy.add_argument("--max-multiplier", type=float, default=2.0)
    tile_local_policy.add_argument(
        "--glass-scale",
        type=float,
        help="optional GLASS-to-reference scale; defaults to tile-pack candidate_transform.scale",
    )
    tile_local_policy.set_defaults(func=cmd_tile_local_policy_proposal)

    tile_local_frame_family = sub.add_parser(
        "tile-local-frame-family-search",
        help="rank frame windows by tile-local residual correction potential",
    )
    tile_local_frame_family.add_argument(
        "--contribution",
        required=True,
        help="resident-tile-contribution JSON artifact",
    )
    tile_local_frame_family.add_argument(
        "--tile-pack",
        help="optional tile_pack_manifest.json; defaults to the path recorded in the contribution artifact",
    )
    tile_local_frame_family.add_argument("--out", required=True, help="output frame-family search JSON")
    tile_local_frame_family.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_frame_family.add_argument(
        "--residual-stat",
        choices=["signed_mean", "tail_signed_mean"],
        default="tail_signed_mean",
        help="residual summary used to score frame windows",
    )
    tile_local_frame_family.add_argument("--min-multiplier", type=float, default=0.0)
    tile_local_frame_family.add_argument("--max-multiplier", type=float, default=2.0)
    tile_local_frame_family.add_argument(
        "--glass-scale",
        type=float,
        help="optional GLASS-to-reference scale; defaults to tile-pack candidate_transform.scale",
    )
    tile_local_frame_family.add_argument(
        "--window-size",
        action="append",
        type=int,
        default=None,
        help="contiguous sorted frame-window size to scan; may be repeated",
    )
    tile_local_frame_family.add_argument("--stride", type=int, default=1, help="frame-window stride")
    tile_local_frame_family.add_argument("--top-n", type=int, default=20, help="number of ranked candidates to retain")
    tile_local_frame_family.set_defaults(func=cmd_tile_local_frame_family_search)

    tile_local_residual_source = sub.add_parser(
        "tile-local-residual-source-audit",
        help="summarize coverage, rejection, and frame-family clues for tile-local residuals",
    )
    tile_local_residual_source.add_argument(
        "--contribution",
        required=True,
        help="resident-tile-contribution JSON artifact",
    )
    tile_local_residual_source.add_argument(
        "--tile-pack",
        help="optional tile_pack_manifest.json; defaults to the path recorded in the contribution artifact",
    )
    tile_local_residual_source.add_argument(
        "--frame-family-search",
        help="optional tile-local-frame-family-search JSON artifact",
    )
    tile_local_residual_source.add_argument("--out", required=True, help="output residual-source audit JSON")
    tile_local_residual_source.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_residual_source.add_argument(
        "--residual-stat",
        choices=["signed_mean", "tail_signed_mean"],
        default="tail_signed_mean",
        help="residual summary used to score audited tiles",
    )
    tile_local_residual_source.add_argument(
        "--high-rejection-excess-threshold",
        type=float,
        default=0.01,
        help="focus-minus-control high rejection fraction treated as excess",
    )
    tile_local_residual_source.add_argument(
        "--min-coverage-fraction",
        type=float,
        default=0.95,
        help="minimum mean coverage fraction before coverage is flagged",
    )
    tile_local_residual_source.set_defaults(func=cmd_tile_local_residual_source_audit)

    tile_local_rejection_registration = sub.add_parser(
        "tile-local-rejection-registration-audit",
        help="rank residual-tile frames by rejection and registration agreement diagnostics",
    )
    tile_local_rejection_registration.add_argument(
        "--contribution",
        required=True,
        help="resident-tile-contribution JSON artifact",
    )
    tile_local_rejection_registration.add_argument(
        "--frame-family-search",
        help="optional tile-local-frame-family-search JSON artifact used to mark top-family frames",
    )
    tile_local_rejection_registration.add_argument("--out", required=True, help="output rejection/registration audit JSON")
    tile_local_rejection_registration.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_rejection_registration.add_argument(
        "--high-rejection-threshold",
        type=float,
        default=0.01,
        help="mean high rejection fraction treated as frame-level excess",
    )
    tile_local_rejection_registration.add_argument(
        "--low-agreement-score-threshold",
        type=float,
        default=0.5,
        help="triangle agreement score treated as low agreement",
    )
    tile_local_rejection_registration.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="number of high-rejection frames to summarize; 0 keeps all",
    )
    tile_local_rejection_registration.set_defaults(func=cmd_tile_local_rejection_registration_audit)

    tile_local_rejection_registration_plan = sub.add_parser(
        "tile-local-rejection-registration-plan",
        help="plan measured experiments for tile-local rejection/registration findings",
    )
    tile_local_rejection_registration_plan.add_argument(
        "--audit",
        required=True,
        help="tile-local-rejection-registration-audit JSON artifact",
    )
    tile_local_rejection_registration_plan.add_argument("--root", required=True, help="root directory for planned artifacts")
    tile_local_rejection_registration_plan.add_argument(
        "--base-run-command",
        required=True,
        help="run_command.txt from the baseline resident run",
    )
    tile_local_rejection_registration_plan.add_argument("--out", required=True, help="output experiment plan JSON")
    tile_local_rejection_registration_plan.add_argument("--markdown", help="optional output Markdown plan")
    tile_local_rejection_registration_plan.add_argument("--reference", help="optional reference master for compare commands")
    tile_local_rejection_registration_plan.add_argument("--manifest", help="optional manifest for acceptance-audit commands")
    tile_local_rejection_registration_plan.add_argument("--wbpp-result", help="optional WBPP result bundle for acceptance-audit")
    tile_local_rejection_registration_plan.add_argument(
        "--benchmark-contract",
        help="optional benchmark contract passed to acceptance-audit",
    )
    tile_local_rejection_registration_plan.add_argument("--glass-scale", type=float)
    tile_local_rejection_registration_plan.add_argument("--glass-offset", type=float)
    tile_local_rejection_registration_plan.add_argument("--min-coverage", type=float)
    tile_local_rejection_registration_plan.add_argument("--soft-agreement-score", type=float, default=0.6)
    tile_local_rejection_registration_plan.add_argument("--strict-agreement-score", type=float, default=0.9)
    tile_local_rejection_registration_plan.add_argument("--exclude-top-count", type=int, default=6)
    tile_local_rejection_registration_plan.set_defaults(func=cmd_tile_local_rejection_registration_plan)

    candidate_comparison = sub.add_parser(
        "candidate-comparison",
        help="compare a measured candidate run against a baseline run and reference metrics",
    )
    candidate_comparison.add_argument("--baseline-run", required=True, help="baseline GLASS run directory")
    candidate_comparison.add_argument("--candidate-run", required=True, help="candidate GLASS run directory")
    candidate_comparison.add_argument("--candidate-id", default="candidate", help="human-readable candidate id")
    candidate_comparison.add_argument("--out", required=True, help="output candidate comparison JSON")
    candidate_comparison.add_argument("--markdown", help="optional output Markdown summary")
    candidate_comparison.add_argument("--baseline-compare-json", help="baseline-vs-reference compare JSON")
    candidate_comparison.add_argument("--candidate-compare-json", help="candidate-vs-reference compare JSON")
    candidate_comparison.add_argument("--candidate-vs-baseline-json", help="candidate-vs-baseline compare JSON")
    candidate_comparison.add_argument("--baseline-acceptance-json", help="optional baseline acceptance-audit JSON")
    candidate_comparison.add_argument("--candidate-acceptance-json", help="candidate acceptance-audit JSON")
    candidate_comparison.add_argument("--max-reference-rms-growth", type=float, default=1.05)
    candidate_comparison.add_argument("--max-reference-p99-growth", type=float, default=1.05)
    candidate_comparison.add_argument("--max-candidate-vs-baseline-rms", type=float)
    candidate_comparison.add_argument("--min-speedup-vs-reference", type=float)
    candidate_comparison.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when required candidate-comparison checks fail",
    )
    candidate_comparison.set_defaults(func=cmd_candidate_comparison)

    candidate_comparison_sweep = sub.add_parser(
        "candidate-comparison-sweep",
        help="rank multiple candidate-comparison artifacts for a measured sweep",
    )
    candidate_comparison_sweep.add_argument(
        "--comparison",
        action="append",
        required=True,
        help="candidate-comparison JSON artifact; may be repeated",
    )
    candidate_comparison_sweep.add_argument("--out", required=True, help="output candidate sweep JSON")
    candidate_comparison_sweep.add_argument("--markdown", help="optional output Markdown summary")
    candidate_comparison_sweep.add_argument(
        "--fail-on-no-passed",
        action="store_true",
        help="return exit code 2 when no candidate comparison passed",
    )
    candidate_comparison_sweep.set_defaults(func=cmd_candidate_comparison_sweep)

    candidate_runtime_sweep_plan = sub.add_parser(
        "candidate-runtime-sweep-plan",
        help="plan runtime-only sweep variants for an accepted candidate comparison",
    )
    candidate_runtime_sweep_plan.add_argument("--comparison", required=True, help="source candidate-comparison JSON")
    candidate_runtime_sweep_plan.add_argument("--root", required=True, help="root directory for planned artifacts")
    candidate_runtime_sweep_plan.add_argument(
        "--base-run-command",
        required=True,
        help="run_command.txt from the accepted candidate run",
    )
    candidate_runtime_sweep_plan.add_argument("--baseline-run", required=True, help="baseline GLASS run directory")
    candidate_runtime_sweep_plan.add_argument("--baseline-compare-json", required=True)
    candidate_runtime_sweep_plan.add_argument("--reference", required=True, help="reference master for compare commands")
    candidate_runtime_sweep_plan.add_argument("--manifest", required=True, help="manifest for acceptance-audit commands")
    candidate_runtime_sweep_plan.add_argument("--wbpp-result", required=True, help="black-box result bundle")
    candidate_runtime_sweep_plan.add_argument("--out", required=True, help="output runtime sweep plan JSON")
    candidate_runtime_sweep_plan.add_argument("--markdown", help="optional output Markdown plan")
    candidate_runtime_sweep_plan.add_argument("--benchmark-contract", help="optional benchmark contract")
    candidate_runtime_sweep_plan.add_argument(
        "--benchmark-contract-profile",
        choices=[RESIDENT_CUDA_DQ_PROFILE_NAME],
        default=RESIDENT_CUDA_DQ_PROFILE_NAME,
        help="benchmark contract profile used for planned acceptance-audit commands when --benchmark-contract is absent",
    )
    candidate_runtime_sweep_plan.add_argument("--glass-scale", type=float)
    candidate_runtime_sweep_plan.add_argument("--glass-offset", type=float)
    candidate_runtime_sweep_plan.add_argument("--min-coverage", type=float)
    candidate_runtime_sweep_plan.add_argument("--min-speedup-vs-reference", type=float)
    candidate_runtime_sweep_plan.add_argument(
        "--variant",
        action="append",
        help="runtime variant id to include; may be repeated, defaults to all built-in variants",
    )
    candidate_runtime_sweep_plan.add_argument(
        "--prefetch-frame",
        action="append",
        type=int,
        help="resident prefetch frame count for a generated matrix variant; may be repeated",
    )
    candidate_runtime_sweep_plan.add_argument(
        "--prefetch-worker",
        action="append",
        type=int,
        help="resident prefetch worker count for a generated matrix variant; may be repeated",
    )
    candidate_runtime_sweep_plan.set_defaults(func=cmd_candidate_runtime_sweep_plan)

    resident_ab_matrix_plan = sub.add_parser(
        "resident-ab-matrix-plan",
        help="plan the real 200-light resident throughput-v1 versus throughput-v2-fused A/B matrix",
    )
    resident_ab_matrix_plan.add_argument("--root", required=True, help="root directory for planned A/B artifacts")
    resident_ab_matrix_plan.add_argument("--plan", required=True, help="processing_plan.json for the real dataset")
    resident_ab_matrix_plan.add_argument("--manifest", required=True, help="manifest.json for acceptance-audit")
    resident_ab_matrix_plan.add_argument("--wbpp-result", required=True, help="user-generated WBPP black-box result JSON")
    resident_ab_matrix_plan.add_argument("--reference", required=True, help="WBPP reference master image")
    resident_ab_matrix_plan.add_argument("--out", required=True, help="output A/B matrix plan JSON")
    resident_ab_matrix_plan.add_argument("--markdown", help="optional output Markdown plan")
    resident_ab_matrix_plan.add_argument("--glass-scale", type=float)
    resident_ab_matrix_plan.add_argument("--glass-offset", type=float)
    resident_ab_matrix_plan.add_argument("--min-coverage", type=float, default=190.0)
    resident_ab_matrix_plan.add_argument("--min-speedup", type=float, default=2.0)
    resident_ab_matrix_plan.add_argument("--reference-frame-id", default="LIGHT_H_0136")
    resident_ab_matrix_plan.add_argument(
        "--resident-output-maps",
        choices=["minimal", "science", "audit"],
        default="audit",
        help="output-map policy for planned validation runs",
    )
    resident_ab_matrix_plan.add_argument("--min-gpu-free-mib", type=int, default=65000)
    resident_ab_matrix_plan.add_argument("--max-gpu-utilization", type=int, default=20)
    resident_ab_matrix_plan.add_argument("--min-disk-free-gib", type=float, default=8.0)
    resident_ab_matrix_plan.add_argument(
        "--benchmark-contract-profile",
        choices=[RESIDENT_CUDA_DQ_PROFILE_NAME],
        default=RESIDENT_CUDA_DQ_PROFILE_NAME,
    )
    resident_ab_matrix_plan.add_argument(
        "--skip-gpu-probe",
        action="store_true",
        help="record GPU readiness as unknown instead of invoking nvidia-smi",
    )
    resident_ab_matrix_plan.set_defaults(func=cmd_resident_ab_matrix_plan)

    resident_ab_matrix_execute = sub.add_parser(
        "resident-ab-matrix-execute",
        help="execute or dry-run a resident 200-light A/B matrix plan",
    )
    resident_ab_matrix_execute.add_argument("--plan", required=True, help="resident A/B matrix plan JSON")
    resident_ab_matrix_execute.add_argument("--out", required=True, help="output execution audit JSON")
    resident_ab_matrix_execute.add_argument(
        "--variant",
        action="append",
        help="variant id to execute; may be repeated, defaults to every variant in the plan",
    )
    resident_ab_matrix_execute.add_argument(
        "--dry-run",
        action="store_true",
        help="record planned subprocesses without executing them",
    )
    resident_ab_matrix_execute.add_argument(
        "--skip-existing",
        action="store_true",
        help="skip variants whose acceptance JSON already exists",
    )
    resident_ab_matrix_execute.add_argument(
        "--ignore-readiness",
        action="store_true",
        help="allow non-dry-run execution even when the plan readiness sample is not ready",
    )
    resident_ab_matrix_execute.add_argument(
        "--no-readiness-recheck",
        action="store_true",
        help="use the readiness state recorded in the plan instead of live GPU/disk rechecking",
    )
    resident_ab_matrix_execute.add_argument(
        "--wait-ready-timeout-s",
        type=float,
        default=0.0,
        help="seconds to keep rechecking readiness before blocking non-dry-run execution",
    )
    resident_ab_matrix_execute.add_argument(
        "--wait-ready-interval-s",
        type=float,
        default=30.0,
        help="seconds between readiness samples while waiting",
    )
    resident_ab_matrix_execute.add_argument(
        "--wait-ready-consecutive-samples",
        type=int,
        default=1,
        help="number of consecutive ready samples required before non-dry-run execution starts",
    )
    resident_ab_matrix_execute.add_argument(
        "--glass-executable",
        help="replace leading 'glass' commands with this executable path",
    )
    resident_ab_matrix_execute.add_argument(
        "--python-executable",
        help="replace leading 'python' commands with this executable path; defaults to the current interpreter",
    )
    resident_ab_matrix_execute.add_argument("--cwd", help="working directory for subprocess execution")
    resident_ab_matrix_execute.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when any executed step fails",
    )
    resident_ab_matrix_execute.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="return exit code 3 when non-dry-run execution is blocked by readiness",
    )
    resident_ab_matrix_execute.set_defaults(func=cmd_resident_ab_matrix_execute)

    candidate_runtime_sweep_execute = sub.add_parser(
        "candidate-runtime-sweep-execute",
        help="execute or dry-run a candidate-runtime-sweep-plan with resume-friendly skipping",
    )
    candidate_runtime_sweep_execute.add_argument("--plan", required=True, help="candidate runtime sweep plan JSON")
    candidate_runtime_sweep_execute.add_argument("--out", required=True, help="output execution audit JSON")
    candidate_runtime_sweep_execute.add_argument(
        "--variant",
        action="append",
        help="variant id to execute; may be repeated, defaults to every variant in the plan",
    )
    candidate_runtime_sweep_execute.add_argument("--start-at", help="start at this selected variant id")
    candidate_runtime_sweep_execute.add_argument("--stop-after", help="stop after this selected variant id")
    candidate_runtime_sweep_execute.add_argument("--dry-run", action="store_true", help="record commands without executing")
    candidate_runtime_sweep_execute.add_argument(
        "--skip-existing",
        action="store_true",
        help="skip variants whose candidate-comparison artifact already exists",
    )
    candidate_runtime_sweep_execute.add_argument(
        "--no-sweep-summary",
        action="store_true",
        help="do not execute the final candidate-comparison-sweep command",
    )
    candidate_runtime_sweep_execute.add_argument(
        "--glass-executable",
        help="optional executable path used to replace command tokens that start with glass",
    )
    candidate_runtime_sweep_execute.add_argument("--cwd", help="working directory for executed commands")
    candidate_runtime_sweep_execute.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when an executed step fails",
    )
    candidate_runtime_sweep_execute.set_defaults(func=cmd_candidate_runtime_sweep_execute)

    tile_local_replay = sub.add_parser(
        "tile-local-policy-replay",
        help="replay a tile-local proposal against resident contribution summaries",
    )
    tile_local_replay.add_argument(
        "--contribution",
        required=True,
        help="resident-tile-contribution JSON artifact",
    )
    tile_local_replay.add_argument(
        "--proposal",
        required=True,
        help="tile-local-policy-proposal JSON artifact",
    )
    tile_local_replay.add_argument("--out", required=True, help="output tile-local policy replay JSON")
    tile_local_replay.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_replay.set_defaults(func=cmd_tile_local_policy_replay)

    tile_local_subset = sub.add_parser(
        "tile-local-policy-subset",
        help="select a non-overlapping subset from a tile-local policy replay",
    )
    tile_local_subset.add_argument("--replay", required=True, help="tile-local-policy-replay JSON artifact")
    tile_local_subset.add_argument("--out", required=True, help="output subset replay JSON")
    tile_local_subset.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_subset.add_argument(
        "--strategy",
        choices=["canonical_delta_abs", "residual_reduction", "tile_index"],
        default="canonical_delta_abs",
        help="greedy priority used when selecting non-overlapping tiles",
    )
    tile_local_subset.add_argument(
        "--max-tiles",
        type=int,
        default=0,
        help="maximum selected tiles; 0 keeps all non-overlapping tiles selected by strategy",
    )
    tile_local_subset.set_defaults(func=cmd_tile_local_policy_subset)

    tile_local_apply = sub.add_parser(
        "tile-local-apply-experiment",
        help="audit a bounded resident CUDA tile-local apply experiment",
    )
    tile_local_apply.add_argument("--baseline-run", required=True, help="baseline GLASS run directory")
    tile_local_apply.add_argument("--candidate-run", required=True, help="candidate GLASS run directory")
    tile_local_apply.add_argument("--replay", required=True, help="tile-local-policy-replay JSON used by candidate")
    tile_local_apply.add_argument("--out", required=True, help="output tile-local apply experiment JSON")
    tile_local_apply.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_apply.add_argument(
        "--benchmark-contract",
        help="optional benchmark contract that pins frame accounting, runtime, and compare thresholds",
    )
    tile_local_apply.add_argument("--baseline-compare-json", help="optional baseline-vs-reference compare JSON")
    tile_local_apply.add_argument("--candidate-compare-json", help="candidate-vs-reference compare JSON")
    tile_local_apply.add_argument("--candidate-vs-baseline-json", help="optional candidate-vs-baseline compare JSON")
    tile_local_apply.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when required checks fail",
    )
    tile_local_apply.set_defaults(func=cmd_tile_local_apply_experiment)

    tile_local_verify = sub.add_parser(
        "tile-local-apply-verify",
        help="measure selected tile-local apply residuals against a reference image",
    )
    tile_local_verify.add_argument("--baseline", required=True, help="baseline GLASS master image")
    tile_local_verify.add_argument("--candidate", required=True, help="candidate GLASS master image")
    tile_local_verify.add_argument("--reference", required=True, help="reference master image")
    tile_local_verify.add_argument("--replay", required=True, help="tile-local replay or subset JSON")
    tile_local_verify.add_argument("--out", required=True, help="output verification JSON")
    tile_local_verify.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_verify.add_argument("--glass-scale", type=float, help="scale GLASS pixels before comparison")
    tile_local_verify.add_argument("--glass-offset", type=float, help="offset GLASS pixels before comparison")
    tile_local_verify.add_argument("--clip-low", type=float, help="clip transformed GLASS pixels to this lower bound")
    tile_local_verify.add_argument("--clip-high", type=float, help="clip transformed GLASS pixels to this upper bound")
    tile_local_verify.add_argument("--coverage-map", help="optional coverage map used to mask compared tile pixels")
    tile_local_verify.add_argument("--min-coverage", type=float, help="minimum coverage required for tile pixels")
    tile_local_verify.add_argument("--pad-px", type=int, default=0, help="optional padding around replay tile extents")
    tile_local_verify.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when measured tile residuals fail to improve",
    )
    tile_local_verify.set_defaults(func=cmd_tile_local_apply_verify)

    tile_local_decision = sub.add_parser(
        "tile-local-policy-decision",
        help="rank and accept/reject measured tile-local policy candidates",
    )
    tile_local_decision.add_argument(
        "--verification",
        action="append",
        required=True,
        help="tile-local-apply-verify JSON artifact; may be repeated",
    )
    tile_local_decision.add_argument("--apply-experiment", help="optional tile-local-apply-experiment JSON")
    tile_local_decision.add_argument("--acceptance-audit", help="optional acceptance-audit JSON")
    tile_local_decision.add_argument("--out", required=True, help="output policy decision JSON")
    tile_local_decision.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_decision.add_argument("--min-signed-fraction", type=float, default=1.0)
    tile_local_decision.add_argument("--min-rms-fraction", type=float, default=1.0)
    tile_local_decision.add_argument("--min-mean-abs-fraction", type=float, default=0.0)
    tile_local_decision.add_argument(
        "--allow-aggregate-mean-abs-regression",
        action="store_true",
        help="do not require aggregate mean-absolute residual improvement",
    )
    tile_local_decision.add_argument(
        "--allow-aggregate-rms-regression",
        action="store_true",
        help="do not require aggregate RMS improvement",
    )
    tile_local_decision.add_argument(
        "--fail-on-rejected",
        action="store_true",
        help="return exit code 2 when the top measured candidate is rejected",
    )
    tile_local_decision.set_defaults(func=cmd_tile_local_policy_decision)

    tile_local_sweep = sub.add_parser(
        "tile-local-policy-sweep",
        help="rank multiple measured tile-local policy decision artifacts",
    )
    tile_local_sweep.add_argument(
        "--decision",
        action="append",
        required=True,
        help="tile-local-policy-decision JSON artifact; may be repeated",
    )
    tile_local_sweep.add_argument("--out", required=True, help="output sweep summary JSON")
    tile_local_sweep.add_argument("--markdown", help="optional output Markdown summary")
    tile_local_sweep.add_argument(
        "--fail-on-no-accepted",
        action="store_true",
        help="return exit code 2 if no accepted decision is present",
    )
    tile_local_sweep.set_defaults(func=cmd_tile_local_policy_sweep)

    tile_local_sweep_plan = sub.add_parser(
        "tile-local-sweep-plan",
        help="plan a measured tile-local policy sweep command queue",
    )
    tile_local_sweep_plan.add_argument("--replay", required=True, help="source tile-local-policy-replay JSON")
    tile_local_sweep_plan.add_argument("--root", required=True, help="root directory for planned artifacts")
    tile_local_sweep_plan.add_argument("--out", required=True, help="output sweep plan JSON")
    tile_local_sweep_plan.add_argument("--markdown", help="optional output Markdown plan")
    tile_local_sweep_plan.add_argument(
        "--max-tiles",
        action="append",
        type=int,
        required=True,
        help="planned non-overlapping subset size; may be repeated",
    )
    tile_local_sweep_plan.add_argument(
        "--strategy",
        default="canonical_delta_abs",
        choices=["canonical_delta_abs", "residual_reduction", "tile_index"],
        help="subset selection strategy",
    )
    tile_local_sweep_plan.add_argument("--candidate-prefix", default="tile_local", help="candidate id prefix")
    tile_local_sweep_plan.add_argument("--base-run-command", help="run_command.txt used as a GLASS run template")
    tile_local_sweep_plan.add_argument("--reference", help="black-box reference master image for compare/verify")
    tile_local_sweep_plan.add_argument("--baseline-run", help="baseline GLASS run directory")
    tile_local_sweep_plan.add_argument("--baseline-master", help="baseline GLASS master image for verify/baseline compare")
    tile_local_sweep_plan.add_argument("--baseline-compare-json", help="baseline-vs-reference compare JSON")
    tile_local_sweep_plan.add_argument("--wbpp-result", help="user-generated black-box timing/result JSON")
    tile_local_sweep_plan.add_argument("--benchmark-contract", help="benchmark contract JSON")
    tile_local_sweep_plan.add_argument("--manifest", help="manifest JSON used by acceptance-audit")
    tile_local_sweep_plan.add_argument("--glass-scale", type=float, help="scale GLASS pixels before reference compare")
    tile_local_sweep_plan.add_argument("--glass-offset", type=float, help="offset GLASS pixels before reference compare")
    tile_local_sweep_plan.add_argument("--min-coverage", type=float, help="minimum coverage for compare/verify")
    tile_local_sweep_plan.add_argument(
        "--existing-decision",
        action="append",
        default=[],
        help="existing decision JSON to include in the final sweep command; may be repeated",
    )
    tile_local_sweep_plan.set_defaults(func=cmd_tile_local_sweep_plan)

    speedup = sub.add_parser("speedup-summary", help="summarize GLASS timing against WBPP black-box timing")
    speedup.add_argument("--glass-run", required=True, help="GLASS run directory containing run_timing.json")
    speedup.add_argument("--wbpp-result", required=True, help="user-generated PixInsight/WBPP black-box result JSON")
    speedup.add_argument("--compare-json", help="optional GLASS compare JSON with image-difference metrics")
    speedup.add_argument("--out", required=True, help="output summary JSON")
    speedup.add_argument("--markdown", help="optional output Markdown summary")
    speedup.add_argument("--min-speedup", type=float, default=1.25)
    speedup.set_defaults(func=cmd_speedup_summary)

    benchmark_contract_profile = sub.add_parser(
        "benchmark-contract-profile",
        help="write a reusable benchmark contract profile for acceptance-audit",
    )
    benchmark_contract_profile.add_argument("--out", required=True, help="output benchmark contract JSON")
    benchmark_contract_profile.add_argument(
        "--profile",
        choices=[RESIDENT_CUDA_DQ_PROFILE_NAME],
        default=RESIDENT_CUDA_DQ_PROFILE_NAME,
        help="benchmark contract profile to write",
    )
    benchmark_contract_profile.add_argument("--name", default="glass_resident_cuda_dq_contract_v1")
    benchmark_contract_profile.add_argument("--min-lights", type=int, default=200)
    benchmark_contract_profile.add_argument("--min-bias", type=int, default=20)
    benchmark_contract_profile.add_argument("--min-dark", type=int, default=20)
    benchmark_contract_profile.add_argument("--min-flat", type=int, default=20)
    benchmark_contract_profile.add_argument("--min-active-frames", type=int, default=190)
    benchmark_contract_profile.add_argument("--min-speedup-vs-reference", type=float, default=2.0)
    benchmark_contract_profile.add_argument("--release-baseline-elapsed-s", type=float)
    benchmark_contract_profile.add_argument("--max-runtime-regression-factor", type=float)
    benchmark_contract_profile.add_argument("--min-coverage-fraction", type=float, default=0.95)
    benchmark_contract_profile.add_argument("--max-rms-diff", type=float, default=0.01)
    benchmark_contract_profile.add_argument("--max-abs-diff-p99", type=float, default=0.01)
    benchmark_contract_profile.add_argument("--dq-map-verify-tile-size", type=int, default=2048)
    benchmark_contract_profile.add_argument("--count-map-verify-tile-size", type=int, default=2048)
    benchmark_contract_profile.add_argument(
        "--no-resident-route",
        action="store_true",
        help="omit the resident memory-mode command-token requirement",
    )
    benchmark_contract_profile.add_argument(
        "--no-throughput-route",
        action="store_true",
        help="omit the throughput resident pipeline command-token group",
    )
    benchmark_contract_profile.set_defaults(func=cmd_benchmark_contract_profile)

    acceptance = sub.add_parser(
        "acceptance-audit",
        help="verify a real GLASS/WBPP acceptance benchmark from existing artifacts",
    )
    acceptance.add_argument("--manifest", required=True, help="manifest.json used for the benchmark")
    acceptance.add_argument("--glass-run", required=True, help="GLASS run directory")
    acceptance.add_argument("--wbpp-result", required=True, help="user-generated WBPP black-box result JSON")
    acceptance.add_argument("--compare-json", required=True, help="coverage-masked or full compare JSON")
    acceptance.add_argument("--out", required=True, help="output acceptance audit JSON")
    acceptance.add_argument("--markdown", help="optional output Markdown summary")
    acceptance.add_argument("--min-lights", type=int, default=200)
    acceptance.add_argument("--min-bias", type=int, default=20)
    acceptance.add_argument("--min-dark", type=int, default=20)
    acceptance.add_argument("--min-flat", type=int, default=20)
    acceptance.add_argument("--min-active-frames", type=int, default=1)
    acceptance.add_argument("--min-speedup", type=float, default=2.0)
    acceptance.add_argument("--min-coverage-fraction", type=float, default=0.95)
    acceptance.add_argument("--max-rms-diff", type=float, default=0.01)
    acceptance.add_argument("--max-abs-diff-p99", type=float, default=0.01)
    acceptance.add_argument(
        "--benchmark-contract",
        help="optional JSON contract that pins real-data benchmark parameters and regression limits",
    )
    acceptance.add_argument(
        "--benchmark-contract-profile",
        choices=[RESIDENT_CUDA_DQ_PROFILE_NAME],
        help="generate and apply a built-in benchmark contract profile in memory",
    )
    acceptance.add_argument(
        "--resident-determinism-json",
        help=(
            "optional resident-determinism JSON; copied into the acceptance audit so reports can "
            "show strict drift status and numerical output-drift magnitude"
        ),
    )
    acceptance.add_argument(
        "--resident-registration-fastpath-json",
        help=(
            "optional resident registration fastpath record or resident_artifacts.json; "
            "overrides the fastpath record collected from --glass-run"
        ),
    )
    acceptance.add_argument(
        "--contract-bundle",
        help=(
            "optional glass guardrails acceptance_contract_bundle.json; supplies pipeline and "
            "StackEngine contract paths unless explicit contract paths are also provided"
        ),
    )
    acceptance.add_argument(
        "--pipeline-contract-json",
        help="optional pipeline-contract JSON; required to pass when supplied",
    )
    acceptance.add_argument(
        "--stack-engine-contract-json",
        help="optional StackEngine contract JSON; benchmark contracts may require default-promotion readiness",
    )
    acceptance.add_argument(
        "--warp-quality-contract-json",
        help="optional warp-quality contract JSON; required to pass when supplied",
    )
    acceptance.add_argument(
        "--require-warp-quality-contract",
        action="store_true",
        help="fail acceptance unless a passing warp-quality contract is attached or supplied",
    )
    acceptance.set_defaults(func=cmd_acceptance_audit)

    release_promotion_decision = sub.add_parser(
        "release-promotion-decision",
        help="decide whether release/default promotion evidence is ready or needs controlled repeat benchmarking",
    )
    release_promotion_decision.add_argument(
        "--acceptance-audit",
        required=True,
        help="acceptance-audit JSON artifact",
    )
    release_promotion_decision.add_argument(
        "--stack-engine-contract",
        help="optional StackEngine contract JSON; supplements acceptance release evidence",
    )
    release_promotion_decision.add_argument(
        "--pipeline-contract",
        help="optional pipeline-contract JSON; supplements acceptance release evidence",
    )
    release_promotion_decision.add_argument(
        "--runtime-compare",
        help="optional resident-runtime-compare JSON used to prove stable repeated timing",
    )
    release_promotion_decision.add_argument(
        "--repeat-preflight",
        help="optional resident-runtime-repeat-preflight JSON used to explain why repeat benchmarking should wait",
    )
    release_promotion_decision.add_argument(
        "--stack-engine-publication-audit",
        help="optional stack-engine-publication-audit JSON used to prove final runtime-default publication handoff",
    )
    release_promotion_decision.add_argument("--out", required=True, help="output release promotion decision JSON")
    release_promotion_decision.add_argument("--markdown", help="optional output Markdown summary")
    release_promotion_decision.add_argument("--min-speedup", type=float, help="override required speedup threshold")
    release_promotion_decision.add_argument(
        "--min-runtime-runs",
        type=int,
        default=2,
        help="minimum completed runtime observations before default changes are considered ready",
    )
    release_promotion_decision.add_argument(
        "--max-elapsed-ratio-vs-best",
        type=float,
        default=1.25,
        help="maximum slowest/best elapsed ratio accepted as stable repeat evidence",
    )
    release_promotion_decision.add_argument(
        "--ignore-warmup-runs",
        type=int,
        default=0,
        help="ignore this many leading runtime observations when evaluating repeat stability",
    )
    release_promotion_decision.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        help="return exit code 2 unless default_change_ready is true",
    )
    release_promotion_decision.set_defaults(func=cmd_release_promotion_decision)

    default_promotion_manifest = sub.add_parser(
        "default-promotion-manifest",
        help="audit whether resident CUDA evidence is ready to become the default path",
    )
    default_promotion_manifest.add_argument(
        "--release-decision",
        required=True,
        help="release-promotion-decision JSON artifact with stable runtime repeat evidence",
    )
    default_promotion_manifest.add_argument(
        "--phase2-status",
        required=True,
        help="Phase 2 status JSON artifact embedding the release decision and pipeline contract",
    )
    default_promotion_manifest.add_argument(
        "--doctor-json",
        help="optional glass doctor JSON artifact used to audit CUDA/package fallback evidence",
    )
    default_promotion_manifest.add_argument("--out", required=True, help="output manifest JSON")
    default_promotion_manifest.add_argument("--markdown", help="optional output Markdown summary")
    default_promotion_manifest.add_argument(
        "--default-memory-mode",
        default="resident",
        help="memory mode proposed for the promoted default",
    )
    default_promotion_manifest.add_argument(
        "--fallback-memory-mode",
        default="tile",
        help="fallback memory mode that must remain available after promotion",
    )
    default_promotion_manifest.add_argument(
        "--default-runtime-preset",
        default=DEFAULT_RESIDENT_RUNTIME_PRESET,
        help="resident runtime preset proposed for the promoted default",
    )
    default_promotion_manifest.add_argument(
        "--integration-engine",
        default="cuda_resident_stack",
        help="integration engine proposed for the promoted default",
    )
    default_promotion_manifest.add_argument(
        "--min-runtime-runs",
        type=int,
        default=2,
        help="minimum stable runtime observations required for promotion",
    )
    default_promotion_manifest.add_argument(
        "--max-runtime-ratio",
        type=float,
        default=1.25,
        help="maximum accepted slowest/best runtime repeat ratio",
    )
    default_promotion_manifest.add_argument(
        "--min-resident-lights",
        type=int,
        default=200,
        help="minimum resident calibrated light count required in the pipeline contract",
    )
    default_promotion_manifest.add_argument(
        "--min-resident-winsorized-sweep-checks",
        type=int,
        default=27,
        help="minimum passed resident winsorized sweep audit check count required for promotion",
    )
    default_promotion_manifest.add_argument(
        "--required-resident-winsorized-sweep-frame-count",
        type=int,
        default=200,
        help="required resident winsorized sweep frame-count row for default promotion",
    )
    default_promotion_manifest.add_argument(
        "--require-doctor",
        action="store_true",
        help="fail unless a doctor JSON artifact is supplied and passes CUDA/package checks",
    )
    default_promotion_manifest.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        help="return exit code 2 unless the default promotion manifest passes",
    )
    default_promotion_manifest.set_defaults(func=cmd_default_promotion_manifest)

    windows_release_matrix = sub.add_parser(
        "windows-release-matrix",
        help="audit Windows CPU/CUDA package matrix readiness from doctor and release decision artifacts",
    )
    windows_release_matrix.add_argument("--doctor-json", required=True, help="glass doctor JSON artifact")
    windows_release_matrix.add_argument(
        "--release-decision",
        required=True,
        help="release-promotion-decision JSON artifact",
    )
    windows_release_matrix.add_argument(
        "--acceptance-audit",
        help="optional acceptance-audit JSON; when supplied it must have passed",
    )
    windows_release_matrix.add_argument(
        "--default-promotion-manifest",
        help="default-promotion-manifest JSON proving default-route promotion provenance",
    )
    windows_release_matrix.add_argument("--out", required=True, help="output Windows release matrix JSON")
    windows_release_matrix.add_argument("--markdown", help="optional output Markdown summary")
    windows_release_matrix.add_argument(
        "--default-runtime-preset",
        default=DEFAULT_RESIDENT_RUNTIME_PRESET,
        help="resident runtime preset expected in the release default",
    )
    windows_release_matrix.add_argument(
        "--expected-primary-package",
        help="expected first package for the current machine, e.g. cuda13 on Blackwell",
    )
    windows_release_matrix.add_argument(
        "--max-runtime-ratio",
        type=float,
        default=1.25,
        help="maximum accepted slowest/best runtime repeat ratio from release decision evidence",
    )
    windows_release_matrix.add_argument(
        "--min-resident-winsorized-sweep-checks",
        type=int,
        default=27,
        help="minimum resident winsorized sweep audit check count required in default-promotion evidence",
    )
    windows_release_matrix.add_argument(
        "--required-resident-winsorized-sweep-frame-count",
        type=int,
        default=200,
        help="required resident winsorized sweep frame-count row in default-promotion evidence",
    )
    windows_release_matrix.add_argument(
        "--allow-cpu-only",
        action="store_true",
        help="do not fail the matrix solely because CUDA is unavailable on this machine",
    )
    windows_release_matrix.add_argument(
        "--allow-not-default-ready",
        action="store_true",
        help="do not require release-decision default_change_ready=true",
    )
    windows_release_matrix.add_argument(
        "--allow-missing-default-promotion",
        action="store_true",
        help="do not require a default-promotion-manifest artifact",
    )
    windows_release_matrix.add_argument(
        "--allow-missing-direct-runtime-evidence",
        action="store_true",
        help="do not require direct acceptance fastpath and pipeline calibration evidence in the default-promotion manifest",
    )
    windows_release_matrix.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        help="return exit code 2 unless the Windows release matrix passes",
    )
    windows_release_matrix.set_defaults(func=cmd_windows_release_matrix)

    windows_package_build_plan = sub.add_parser(
        "windows-package-build-plan",
        help="plan Windows CPU/CUDA portable package builds from local Toolkit availability",
    )
    windows_package_build_plan.add_argument("--out", required=True, help="output package build plan JSON")
    windows_package_build_plan.add_argument("--markdown", help="optional output Markdown summary")
    windows_package_build_plan.add_argument(
        "--release-root",
        default=".release/windows",
        help="portable package release root used by build_portable.ps1",
    )
    windows_package_build_plan.add_argument(
        "--cuda-base",
        default="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA",
        help="directory containing CUDA Toolkit version folders",
    )
    windows_package_build_plan.add_argument(
        "--packages",
        default="cuda13,cuda12,cuda11,cpu",
        help="comma-separated package labels to plan",
    )
    windows_package_build_plan.add_argument(
        "--toolkit-root",
        action="append",
        default=[],
        help="override Toolkit root in LABEL=PATH form; may be repeated",
    )
    windows_package_build_plan.add_argument(
        "--python",
        default=r".\.venv\Scripts\python.exe",
        help="Python executable passed to build_portable.ps1",
    )
    windows_package_build_plan.add_argument(
        "--configuration",
        default="Release",
        help="CMake configuration passed to build_portable.ps1",
    )
    windows_package_build_plan.add_argument(
        "--shared-cuda-runtime",
        action="store_true",
        help="plan CUDA builds without -StaticCudaRuntime",
    )
    windows_package_build_plan.add_argument(
        "--require-all-toolkits",
        action="store_true",
        help="make the plan fail unless every requested CUDA package has a matching Toolkit",
    )
    windows_package_build_plan.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="return exit code 2 when any requested CUDA package is missing a matching Toolkit",
    )
    windows_package_build_plan.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the build-plan checks pass",
    )
    windows_package_build_plan.set_defaults(func=cmd_windows_package_build_plan)

    windows_package_suite = sub.add_parser(
        "windows-package-suite",
        help="aggregate Windows portable package smoke artifacts into a release-suite readiness report",
    )
    windows_package_suite.add_argument(
        "--smoke",
        action="append",
        default=[],
        required=True,
        help="package smoke artifact in LABEL=PATH form; repeat for every package",
    )
    windows_package_suite.add_argument("--out", required=True, help="output package suite JSON")
    windows_package_suite.add_argument("--markdown", help="optional output Markdown summary")
    windows_package_suite.add_argument(
        "--required-labels",
        default="cuda13,cuda12,cuda11,cpu",
        help="comma-separated labels required in the package suite",
    )
    windows_package_suite.add_argument(
        "--require-same-source-stamp",
        action="store_true",
        help="fail unless every package smoke artifact reports the same source stamp",
    )
    windows_package_suite.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the package suite passes",
    )
    windows_package_suite.set_defaults(func=cmd_windows_package_suite)

    windows_release_manifest = sub.add_parser(
        "windows-release-manifest",
        help="record Windows release zip sizes and SHA256 checksums from a package suite",
    )
    windows_release_manifest.add_argument(
        "--suite",
        required=True,
        help="windows-package-suite JSON artifact",
    )
    windows_release_manifest.add_argument(
        "--zip",
        action="append",
        default=[],
        help="optional package zip override in LABEL=PATH form; repeat as needed",
    )
    windows_release_manifest.add_argument("--out", required=True, help="output release manifest JSON")
    windows_release_manifest.add_argument("--markdown", help="optional output Markdown summary")
    windows_release_manifest.add_argument(
        "--windows-release-matrix",
        help="optional Windows release-matrix JSON artifact required for strict release manifests",
    )
    windows_release_manifest.add_argument(
        "--require-same-source-stamp",
        action="store_true",
        help="fail unless every package in the manifest reports the same source stamp",
    )
    windows_release_manifest.add_argument(
        "--allow-missing-windows-release-matrix",
        action="store_true",
        help="do not require a Windows release-matrix artifact in the release manifest",
    )
    windows_release_manifest.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the release manifest checks pass",
    )
    windows_release_manifest.set_defaults(func=cmd_windows_release_manifest)

    windows_github_release_plan = sub.add_parser(
        "windows-github-release-plan",
        help="prepare GitHub release notes and upload commands for Windows packages",
    )
    windows_github_release_plan.add_argument(
        "--manifest",
        required=True,
        help="windows-release-manifest JSON artifact",
    )
    windows_github_release_plan.add_argument("--tag", required=True, help="GitHub release tag")
    windows_github_release_plan.add_argument("--title", help="GitHub release title")
    windows_github_release_plan.add_argument("--out", required=True, help="output release plan JSON")
    windows_github_release_plan.add_argument("--markdown", help="optional output Markdown plan")
    windows_github_release_plan.add_argument("--notes", help="optional output Markdown release notes")
    windows_github_release_plan.add_argument(
        "--script",
        help="optional output PowerShell script that verifies assets before publishing with gh",
    )
    windows_github_release_plan.add_argument(
        "--no-draft",
        action="store_true",
        help="plan a non-draft GitHub release command",
    )
    windows_github_release_plan.add_argument(
        "--prerelease",
        action="store_true",
        help="plan a prerelease GitHub release command",
    )
    windows_github_release_plan.add_argument(
        "--require-same-source-stamp",
        action="store_true",
        help="fail unless every asset reports the same source stamp",
    )
    windows_github_release_plan.add_argument(
        "--check-gh",
        action="store_true",
        help="record whether GitHub CLI is available on PATH",
    )
    windows_github_release_plan.add_argument(
        "--check-gh-auth",
        action="store_true",
        help="run gh auth status and require authenticated CLI for publication readiness",
    )
    windows_github_release_plan.add_argument(
        "--gh-path",
        help="explicit path to gh executable for CLI/auth checks",
    )
    windows_github_release_plan.add_argument(
        "--phase2-status",
        help="optional glass phase2-status JSON artifact required to be green before release handoff",
    )
    windows_github_release_plan.add_argument(
        "--phase2-status-compare",
        help="optional glass phase2-status-compare JSON artifact required to pass before release handoff",
    )
    windows_github_release_plan.add_argument(
        "--windows-release-matrix",
        help="optional Windows release-matrix JSON artifact required for strict release handoff",
    )
    windows_github_release_plan.add_argument(
        "--allow-missing-windows-release-matrix",
        action="store_true",
        help="do not require a Windows release-matrix artifact in the release handoff plan",
    )
    windows_github_release_plan.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the release plan checks pass",
    )
    windows_github_release_plan.set_defaults(func=cmd_windows_github_release_plan)

    windows_publish_preflight = sub.add_parser(
        "windows-publish-preflight",
        help="verify manifest, GitHub handoff, matrix, and default-promotion artifacts before publishing",
    )
    windows_publish_preflight.add_argument(
        "--release-manifest",
        required=True,
        help="windows-release-manifest JSON artifact",
    )
    windows_publish_preflight.add_argument(
        "--github-release-plan",
        required=True,
        help="windows-github-release-plan JSON artifact",
    )
    windows_publish_preflight.add_argument(
        "--windows-release-matrix",
        required=True,
        help="windows-release-matrix JSON artifact",
    )
    windows_publish_preflight.add_argument(
        "--default-promotion-manifest",
        required=True,
        help="default-promotion-manifest JSON artifact",
    )
    windows_publish_preflight.add_argument("--out", required=True, help="output publish-preflight JSON")
    windows_publish_preflight.add_argument("--markdown", help="optional output Markdown summary")
    windows_publish_preflight.add_argument(
        "--allow-not-publication-ready",
        action="store_true",
        help="do not require github-release-plan publication_ready=true",
    )
    windows_publish_preflight.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the publish preflight passes",
    )
    windows_publish_preflight.set_defaults(func=cmd_windows_publish_preflight)

    stack_publication_audit = sub.add_parser(
        "stack-engine-publication-audit",
        help="audit StackEngine default-contract evidence across release publication artifacts",
    )
    stack_publication_audit.add_argument(
        "--stack-engine-contract",
        required=True,
        help="stack-engine-contract JSON artifact",
    )
    stack_publication_audit.add_argument(
        "--phase2-status",
        required=True,
        help="phase2-status JSON artifact containing direct and publish-preflight evidence",
    )
    stack_publication_audit.add_argument(
        "--default-promotion-manifest",
        required=True,
        help="default-promotion-manifest JSON artifact",
    )
    stack_publication_audit.add_argument(
        "--windows-release-matrix",
        required=True,
        help="windows-release-matrix JSON artifact",
    )
    stack_publication_audit.add_argument(
        "--github-release-plan",
        required=True,
        help="windows-github-release-plan JSON artifact",
    )
    stack_publication_audit.add_argument(
        "--publish-preflight",
        required=True,
        help="windows-publish-preflight JSON artifact",
    )
    stack_publication_audit.add_argument("--out", required=True, help="output audit JSON")
    stack_publication_audit.add_argument("--markdown", help="optional output Markdown summary")
    stack_publication_audit.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the publication evidence audit passes",
    )
    stack_publication_audit.set_defaults(func=cmd_stack_engine_publication_audit)

    windows_package_smoke = sub.add_parser(
        "windows-package-smoke",
        help="smoke-test a Windows portable package folder and optional zip artifact",
    )
    windows_package_smoke.add_argument("--package-root", required=True, help="portable GLASS package root")
    windows_package_smoke.add_argument("--zip", help="optional portable zip path; defaults beside package root")
    windows_package_smoke.add_argument("--out", required=True, help="output package smoke JSON")
    windows_package_smoke.add_argument("--markdown", help="optional output Markdown summary")
    windows_package_smoke.add_argument("--expected-source", help="expected source stamp value")
    windows_package_smoke.add_argument("--expected-package-label", help="expected package_manifest.json package_label")
    windows_package_smoke.add_argument(
        "--require-cuda",
        action="store_true",
        help="require portable doctor to report CUDA available",
    )
    windows_package_smoke.add_argument(
        "--skip-exec",
        action="store_true",
        help="only validate package files; do not execute glass-doctor.cmd or glass.cmd",
    )
    windows_package_smoke.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="per-command timeout in seconds for package execution smoke",
    )
    windows_package_smoke.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless package smoke passes",
    )
    windows_package_smoke.set_defaults(func=cmd_windows_package_smoke)

    resident_det = sub.add_parser(
        "resident-determinism",
        help="compare resident CUDA registration signatures from two GLASS runs",
    )
    resident_det.add_argument("--baseline-run", required=True, help="baseline run directory or resident_artifacts.json")
    resident_det.add_argument("--candidate-run", required=True, help="candidate run directory or resident_artifacts.json")
    resident_det.add_argument("--out", required=True, help="output determinism audit JSON")
    resident_det.add_argument("--markdown", help="optional output Markdown summary")
    resident_det.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="return exit code 2 when signatures, registration, frame accounting, or output pixels differ",
    )
    resident_det.set_defaults(func=cmd_resident_determinism)

    resident_reg = sub.add_parser(
        "resident-registration-audit",
        help="summarize resident CUDA triangle registration candidate and pixel-refine diagnostics",
    )
    resident_reg.add_argument("--run", required=True, help="GLASS run directory or registration_results.json")
    resident_reg.add_argument("--out", required=True, help="output candidate audit JSON")
    resident_reg.add_argument("--markdown", help="optional output Markdown summary")
    resident_reg.add_argument(
        "--fail-on-registration-failures",
        action="store_true",
        help="return exit code 2 when any triangle registration frame failed or was quality-gated",
    )
    resident_reg.set_defaults(func=cmd_resident_registration_audit)

    resident_reg_compare = sub.add_parser(
        "resident-registration-compare",
        help="join resident sweep compare results with resident registration candidate audits",
    )
    resident_reg_compare.add_argument("--sweep-summary", required=True, help="resident_prefetch_sweep_summary.json")
    resident_reg_compare.add_argument("--audit-root", help="directory containing *_candidate_audit.json files")
    resident_reg_compare.add_argument(
        "--audit-json",
        action="append",
        default=[],
        help="explicit resident-registration-audit JSON; can be repeated",
    )
    resident_reg_compare.add_argument("--out", required=True, help="output candidate/compare JSON")
    resident_reg_compare.add_argument("--markdown", help="optional output Markdown summary")
    resident_reg_compare.add_argument(
        "--fail-on-missing-audits",
        action="store_true",
        help="return exit code 2 if any sweep variant is missing a candidate audit",
    )
    resident_reg_compare.set_defaults(func=cmd_resident_registration_compare)

    resident_reg_matrix = sub.add_parser(
        "resident-registration-matrix-compare",
        help="compare CPU/external registration matrices against resident CUDA registration matrices",
    )
    resident_reg_matrix.add_argument(
        "--baseline-registration",
        required=True,
        help="baseline registration_results.json or run directory",
    )
    resident_reg_matrix.add_argument(
        "--candidate-registration",
        required=True,
        help="candidate registration_results.json or run directory",
    )
    resident_reg_matrix.add_argument("--out", required=True, help="output matrix-compare JSON")
    resident_reg_matrix.add_argument("--markdown", help="optional output Markdown summary")
    resident_reg_matrix.add_argument("--baseline-label", default="baseline", help="label for baseline rows")
    resident_reg_matrix.add_argument("--candidate-label", default="candidate", help="label for candidate rows")
    resident_reg_matrix.add_argument(
        "--max-translation-delta-px",
        type=float,
        default=0.5,
        help="maximum allowed per-frame translation-vector delta",
    )
    resident_reg_matrix.add_argument(
        "--max-matrix-delta-frobenius",
        type=float,
        default=0.05,
        help="maximum allowed per-frame 3x3 matrix Frobenius delta",
    )
    resident_reg_matrix.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 if any matrix-compare check fails",
    )
    resident_reg_matrix.set_defaults(func=cmd_resident_registration_matrix_compare)

    resident_reg_matrix_sweep = sub.add_parser(
        "resident-registration-matrix-sweep",
        help="rank resident registration matrix-compare variants and optional parity summaries",
    )
    resident_reg_matrix_sweep.add_argument(
        "--matrix-compare",
        action="append",
        required=True,
        help="matrix compare entry in label=path form; repeat for multiple variants",
    )
    resident_reg_matrix_sweep.add_argument(
        "--parity-summary",
        action="append",
        default=[],
        help="optional parity summary entry in label=path form; labels should match matrix entries",
    )
    resident_reg_matrix_sweep.add_argument("--out", required=True, help="output matrix sweep JSON")
    resident_reg_matrix_sweep.add_argument("--markdown", help="optional output Markdown summary")
    resident_reg_matrix_sweep.set_defaults(func=cmd_resident_registration_matrix_sweep)

    resident_runtime_compare = sub.add_parser(
        "resident-runtime-compare",
        help="compare resident CUDA timing and I/O pipeline artifacts from GLASS runs",
    )
    resident_runtime_compare.add_argument(
        "--run",
        action="append",
        required=True,
        help="run entry in label=path format; can be repeated",
    )
    resident_runtime_compare.add_argument(
        "--baseline-label",
        help="label to use as the timing baseline; defaults to the first --run entry",
    )
    resident_runtime_compare.add_argument("--out", required=True, help="output runtime comparison JSON")
    resident_runtime_compare.add_argument("--markdown", help="optional output Markdown summary")
    resident_runtime_compare.set_defaults(func=cmd_resident_runtime_compare)

    resident_fits_auto_regression = sub.add_parser(
        "resident-fits-auto-regression",
        help="audit a resident auto FITS run against raw-u16 GPU selection, DQ, compare, and timing constraints",
    )
    resident_fits_auto_regression.add_argument("--run", required=True, help="candidate GLASS run directory")
    resident_fits_auto_regression.add_argument(
        "--explicit-run",
        help="explicit native_u16_gpu baseline run directory used for timing closeness",
    )
    resident_fits_auto_regression.add_argument(
        "--control-run",
        help="astropy/control baseline run directory used for timing speedup",
    )
    resident_fits_auto_regression.add_argument(
        "--compare-explicit",
        required=True,
        help="compare JSON for candidate auto run against explicit native_u16_gpu output",
    )
    resident_fits_auto_regression.add_argument(
        "--compare-control",
        required=True,
        help="compare JSON for candidate auto run against astropy/control output",
    )
    resident_fits_auto_regression.add_argument("--out", required=True, help="output regression audit JSON")
    resident_fits_auto_regression.add_argument("--markdown", help="optional Markdown summary")
    resident_fits_auto_regression.add_argument("--min-lights", type=int, default=200)
    resident_fits_auto_regression.add_argument("--expected-active", type=int, default=193)
    resident_fits_auto_regression.add_argument("--expected-masked", type=int, default=7)
    resident_fits_auto_regression.add_argument("--expected-unknown-zero-weight", type=int, default=0)
    resident_fits_auto_regression.add_argument("--expected-requested-mode", default="auto")
    resident_fits_auto_regression.add_argument("--expected-effective-mode", default="native_u16_gpu")
    resident_fits_auto_regression.add_argument("--expected-backend", default="native_u16be_raw")
    resident_fits_auto_regression.add_argument("--expected-resolution-source")
    resident_fits_auto_regression.add_argument("--max-rms-diff", type=float, default=0.0)
    resident_fits_auto_regression.add_argument("--max-abs-diff", type=float, default=0.0)
    resident_fits_auto_regression.add_argument("--max-total-vs-explicit-ratio", type=float, default=1.10)
    resident_fits_auto_regression.add_argument("--max-total-vs-control-ratio", type=float, default=0.90)
    resident_fits_auto_regression.add_argument("--max-light-bucket-vs-control-ratio", type=float, default=0.70)
    resident_fits_auto_regression.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 when the guarded-auto regression contract fails",
    )
    resident_fits_auto_regression.set_defaults(func=cmd_resident_fits_auto_regression)

    resident_fits_default_matrix = sub.add_parser(
        "resident-fits-default-matrix",
        help="audit resident FITS default/fallback compatibility across run artifacts",
    )
    resident_fits_default_matrix.add_argument("--cases", required=True, help="matrix case JSON")
    resident_fits_default_matrix.add_argument("--out", required=True, help="output matrix JSON")
    resident_fits_default_matrix.add_argument("--markdown", help="optional Markdown summary")
    resident_fits_default_matrix.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 when any compatibility matrix case fails",
    )
    resident_fits_default_matrix.set_defaults(func=cmd_resident_fits_default_matrix)

    resident_parity = sub.add_parser(
        "resident-parity-summary",
        help="summarize CPU tiled vs CUDA resident parity from run and compare artifacts",
    )
    resident_parity.add_argument("--cpu-run", required=True, help="CPU tiled GLASS run directory")
    resident_parity.add_argument("--resident-run", required=True, help="CUDA resident GLASS run directory")
    resident_parity.add_argument("--compare-json", required=True, help="GLASS compare JSON for resident vs CPU master")
    resident_parity.add_argument("--out", required=True, help="output resident parity JSON")
    resident_parity.add_argument("--markdown", help="optional output Markdown summary")
    resident_parity.add_argument("--cpu-label", default="cpu_tile")
    resident_parity.add_argument("--resident-label", default="cuda_resident")
    resident_parity.add_argument("--max-rms-diff", type=float, default=0.1)
    resident_parity.add_argument("--max-relative-rms-diff", type=float, default=0.001)
    resident_parity.add_argument("--max-rejected-sample-delta", type=int, default=64)
    resident_parity.add_argument(
        "--ignore-resident-contract",
        action="store_true",
        help="report resident_result_contract failures without making the summary fail",
    )
    resident_parity.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless parity and required contracts pass",
    )
    resident_parity.set_defaults(func=cmd_resident_parity_summary)

    rejection_audit = sub.add_parser(
        "resident-rejection-sample-audit",
        help="compare CPU tiled and CUDA resident coverage/rejection/DQ sample accounting",
    )
    rejection_audit.add_argument("--cpu-run", required=True, help="CPU tiled GLASS run directory")
    rejection_audit.add_argument(
        "--resident-run",
        required=True,
        help="CUDA resident GLASS run directory",
    )
    rejection_audit.add_argument(
        "--compare-json",
        help="optional GLASS compare JSON; its comparison_region is reused for region splits",
    )
    rejection_audit.add_argument(
        "--rejection-input-audit",
        help=(
            "optional resident-rejection-input-audit JSON; when exact-input CPU/CUDA parity is proven, "
            "sample deltas are attributed to resident registration/warp input instead of the rejection kernel"
        ),
    )
    rejection_audit.add_argument("--out", required=True, help="output rejection sample audit JSON")
    rejection_audit.add_argument("--markdown", help="optional output Markdown summary")
    rejection_audit.add_argument("--tile-size", type=int, default=2048)
    rejection_audit.add_argument("--top-tiles", type=int, default=10)
    rejection_audit.add_argument("--max-rejected-sample-delta", type=int, default=64)
    rejection_audit.add_argument("--max-pre-rejection-sample-delta", type=int, default=0)
    rejection_audit.add_argument("--max-same-pre-rejection-abs-delta", type=int, default=16)
    rejection_audit.add_argument(
        "--evaluation-region",
        choices=["full_frame", "compare_region"],
        default="full_frame",
        help=(
            "threshold evaluation region: full_frame keeps strict global accounting; "
            "compare_region evaluates only the GLASS compare common footprint while still reporting global deltas"
        ),
    )
    rejection_audit.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the audit passes all thresholds",
    )
    rejection_audit.set_defaults(func=cmd_resident_rejection_sample_audit)

    rejection_input_audit = sub.add_parser(
        "resident-rejection-input-audit",
        help=(
            "attribute resident rejection-map drift to the hardened winsorized kernel "
            "or to upstream resident registration/warp input differences"
        ),
    )
    rejection_input_audit.add_argument("--cpu-run", required=True, help="CPU tiled GLASS run directory")
    rejection_input_audit.add_argument(
        "--resident-run",
        required=True,
        help="CUDA resident GLASS run directory",
    )
    rejection_input_audit.add_argument(
        "--compare-json",
        help="GLASS compare JSON; required for --evaluation-region compare_region",
    )
    rejection_input_audit.add_argument("--out", required=True, help="output rejection input audit JSON")
    rejection_input_audit.add_argument("--markdown", help="optional output Markdown summary")
    rejection_input_audit.add_argument(
        "--evaluation-region",
        choices=["full_frame", "compare_region"],
        default="compare_region",
        help="evaluate resident output deltas globally or inside the declared compare common footprint",
    )
    rejection_input_audit.add_argument(
        "--skip-cuda-exact-input",
        action="store_true",
        help="skip the exact-input ResidentCalibratedStack replay; useful for CPU-only smoke tests",
    )
    rejection_input_audit.add_argument("--master-tolerance", type=float, default=5.0e-4)
    rejection_input_audit.add_argument("--max-same-pre-rejection-abs-delta", type=int, default=16)
    rejection_input_audit.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless exact-input parity and resident output thresholds pass",
    )
    rejection_input_audit.set_defaults(func=cmd_resident_rejection_input_audit)

    warp_input_audit = sub.add_parser(
        "resident-warp-input-audit",
        help=(
            "compare resident CUDA warped samples against CPU registered_cache "
            "under CPU and resident registration matrices"
        ),
    )
    warp_input_audit.add_argument("--cpu-run", required=True, help="CPU tiled GLASS run directory")
    warp_input_audit.add_argument("--resident-run", required=True, help="CUDA resident GLASS run directory")
    warp_input_audit.add_argument("--compare-json", help="optional GLASS compare JSON for border crop")
    warp_input_audit.add_argument("--out", required=True, help="output warp input audit JSON")
    warp_input_audit.add_argument("--markdown", help="optional output Markdown summary")
    warp_input_audit.add_argument(
        "--frame-id",
        action="append",
        help="frame id to audit; may be repeated. Defaults to common frames up to --max-frames",
    )
    warp_input_audit.add_argument("--max-frames", type=int, default=8)
    warp_input_audit.add_argument("--interpolation", choices=["bilinear"], default="bilinear")
    warp_input_audit.add_argument("--cpu-matrix-rms-tolerance", type=float, default=5.0e-4)
    warp_input_audit.add_argument("--resident-matrix-rms-tolerance", type=float, default=0.1)
    warp_input_audit.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the warp-input attribution audit passes",
    )
    warp_input_audit.set_defaults(func=cmd_resident_warp_input_audit)

    resident_winsorized_benchmark = sub.add_parser(
        "resident-winsorized-benchmark",
        help="run a synthetic resident CUDA winsorized benchmark against the CPU baseline",
    )
    resident_winsorized_benchmark.add_argument("--out", required=True, help="output benchmark JSON")
    resident_winsorized_benchmark.add_argument("--markdown", help="optional output Markdown summary")
    resident_winsorized_benchmark.add_argument("--frames", type=int, default=16, help="synthetic frame count")
    resident_winsorized_benchmark.add_argument("--height", type=int, default=32, help="synthetic image height")
    resident_winsorized_benchmark.add_argument("--width", type=int, default=32, help="synthetic image width")
    resident_winsorized_benchmark.add_argument("--seed", type=int, default=12345, help="deterministic RNG seed")
    resident_winsorized_benchmark.add_argument("--low-sigma", type=float, default=3.0)
    resident_winsorized_benchmark.add_argument("--high-sigma", type=float, default=3.0)
    resident_winsorized_benchmark.add_argument("--tolerance-rms", type=float, default=2.0e-5)
    resident_winsorized_benchmark.add_argument("--tolerance-max-abs", type=float, default=2.0e-4)
    resident_winsorized_benchmark.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless CUDA is available and hardened parity checks pass",
    )
    resident_winsorized_benchmark.set_defaults(func=cmd_resident_winsorized_benchmark)

    resident_winsorized_benchmark_audit = sub.add_parser(
        "resident-winsorized-benchmark-audit",
        help="audit a resident winsorized benchmark artifact against a machine-readable contract",
    )
    resident_winsorized_benchmark_audit.add_argument(
        "--artifact",
        required=True,
        help="resident-winsorized-benchmark JSON artifact",
    )
    resident_winsorized_benchmark_audit.add_argument(
        "--contract",
        default=str(DEFAULT_RESIDENT_WINSORIZED_BENCHMARK_CONTRACT),
        help="resident winsorized benchmark contract JSON",
    )
    resident_winsorized_benchmark_audit.add_argument("--out", required=True, help="output audit JSON")
    resident_winsorized_benchmark_audit.add_argument("--markdown", help="optional output Markdown summary")
    resident_winsorized_benchmark_audit.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 when the benchmark artifact fails the contract",
    )
    resident_winsorized_benchmark_audit.set_defaults(func=cmd_resident_winsorized_benchmark_audit)

    resident_winsorized_sweep = sub.add_parser(
        "resident-winsorized-sweep",
        help="run resident CUDA winsorized parity microbenchmarks across frame counts",
    )
    resident_winsorized_sweep.add_argument("--out", required=True, help="output sweep JSON")
    resident_winsorized_sweep.add_argument("--markdown", help="optional output Markdown summary")
    resident_winsorized_sweep.add_argument(
        "--frame-counts",
        default=",".join(str(item) for item in DEFAULT_RESIDENT_WINSORIZED_SWEEP_FRAME_COUNTS),
        help="comma-separated synthetic frame counts; default includes 200",
    )
    resident_winsorized_sweep.add_argument(
        "--required-frame-count",
        type=int,
        default=200,
        help="frame count that must be present and pass, matching the 200-light scale target",
    )
    resident_winsorized_sweep.add_argument("--height", type=int, default=16, help="synthetic image height")
    resident_winsorized_sweep.add_argument("--width", type=int, default=16, help="synthetic image width")
    resident_winsorized_sweep.add_argument("--seed-base", type=int, default=268, help="deterministic RNG seed base")
    resident_winsorized_sweep.add_argument("--low-sigma", type=float, default=3.0)
    resident_winsorized_sweep.add_argument("--high-sigma", type=float, default=3.0)
    resident_winsorized_sweep.add_argument("--tolerance-rms", type=float, default=5.0e-5)
    resident_winsorized_sweep.add_argument("--tolerance-max-abs", type=float, default=2.0e-4)
    resident_winsorized_sweep.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless every frame-count row passes",
    )
    resident_winsorized_sweep.set_defaults(func=cmd_resident_winsorized_sweep)

    resident_winsorized_sweep_audit = sub.add_parser(
        "resident-winsorized-sweep-audit",
        help="audit a resident winsorized frame-count sweep against a machine-readable contract",
    )
    resident_winsorized_sweep_audit.add_argument(
        "--artifact",
        required=True,
        help="resident-winsorized-sweep JSON artifact",
    )
    resident_winsorized_sweep_audit.add_argument(
        "--contract",
        default=str(DEFAULT_RESIDENT_WINSORIZED_SWEEP_CONTRACT),
        help="resident winsorized sweep contract JSON",
    )
    resident_winsorized_sweep_audit.add_argument("--out", required=True, help="output audit JSON")
    resident_winsorized_sweep_audit.add_argument("--markdown", help="optional output Markdown summary")
    resident_winsorized_sweep_audit.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 when the sweep artifact fails the contract",
    )
    resident_winsorized_sweep_audit.set_defaults(func=cmd_resident_winsorized_sweep_audit)

    resident_runtime_repeat_plan = sub.add_parser(
        "resident-runtime-repeat-plan",
        help="plan repeated resident CUDA runs for cache and I/O variance checks",
    )
    resident_runtime_repeat_plan.add_argument(
        "--base-run-command",
        required=True,
        help="run_command.txt from the resident configuration to repeat",
    )
    resident_runtime_repeat_plan.add_argument("--root", required=True, help="root directory for planned repeat artifacts")
    resident_runtime_repeat_plan.add_argument("--label", required=True, help="short label for repeat run ids")
    resident_runtime_repeat_plan.add_argument("--repeats", type=int, default=3, help="number of repeated runs to plan")
    resident_runtime_repeat_plan.add_argument(
        "--cache-state",
        default="warm",
        choices=["warm", "cold", "unknown", "dedicated_io_window"],
        help="operator label for the intended cache/I/O state",
    )
    resident_runtime_repeat_plan.add_argument(
        "--baseline-repeat",
        type=int,
        default=1,
        help="repeat index to use as resident-runtime-compare baseline",
    )
    resident_runtime_repeat_plan.add_argument("--out", required=True, help="output repeat plan JSON")
    resident_runtime_repeat_plan.add_argument("--markdown", help="optional output Markdown plan")
    resident_runtime_repeat_plan.set_defaults(func=cmd_resident_runtime_repeat_plan)

    resident_runtime_repeat_execute = sub.add_parser(
        "resident-runtime-repeat-execute",
        help="execute or dry-run a resident-runtime-repeat-plan",
    )
    resident_runtime_repeat_execute.add_argument("--plan", required=True, help="resident runtime repeat plan JSON")
    resident_runtime_repeat_execute.add_argument("--out", required=True, help="output execution audit JSON")
    resident_runtime_repeat_execute.add_argument(
        "--dry-run",
        action="store_true",
        help="record planned commands without executing them",
    )
    resident_runtime_repeat_execute.add_argument(
        "--skip-existing",
        action="store_true",
        help="skip repeat runs that already contain run_timing.json",
    )
    resident_runtime_repeat_execute.add_argument(
        "--no-run-compare",
        action="store_true",
        help="do not run the final resident-runtime-compare step",
    )
    resident_runtime_repeat_execute.add_argument(
        "--glass-executable",
        help="replace leading 'glass' token with this executable while executing",
    )
    resident_runtime_repeat_execute.add_argument("--cwd", help="working directory for executed commands")
    resident_runtime_repeat_execute.add_argument(
        "--require-preflight-ready",
        action="store_true",
        help="run preflight first and block execution unless it recommends execution",
    )
    resident_runtime_repeat_execute.add_argument(
        "--preflight-out",
        help="optional output path for the preflight JSON embedded in the execution audit",
    )
    resident_runtime_repeat_execute.add_argument(
        "--min-free-mib",
        type=int,
        default=8192,
        help="minimum free GPU memory required by preflight",
    )
    resident_runtime_repeat_execute.add_argument(
        "--max-busy-utilization",
        type=int,
        default=95,
        help="GPU utilization threshold used by preflight",
    )
    resident_runtime_repeat_execute.add_argument(
        "--allow-existing-preflight",
        action="store_true",
        help="allow repeat output directories that exist without run_timing.json during preflight",
    )
    resident_runtime_repeat_execute.add_argument(
        "--skip-gpu-probe",
        action="store_true",
        help="skip nvidia-smi probing during preflight",
    )
    resident_runtime_repeat_execute.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when an executed step fails",
    )
    resident_runtime_repeat_execute.set_defaults(func=cmd_resident_runtime_repeat_execute)

    resident_runtime_repeat_preflight = sub.add_parser(
        "resident-runtime-repeat-preflight",
        help="check whether a resident-runtime-repeat-plan is ready to execute",
    )
    resident_runtime_repeat_preflight.add_argument("--plan", required=True, help="resident runtime repeat plan JSON")
    resident_runtime_repeat_preflight.add_argument("--out", required=True, help="output preflight JSON")
    resident_runtime_repeat_preflight.add_argument(
        "--min-free-mib",
        type=int,
        default=8192,
        help="minimum free GPU memory required before recommending execution",
    )
    resident_runtime_repeat_preflight.add_argument(
        "--max-busy-utilization",
        type=int,
        default=95,
        help="utilization threshold at or above which a loaded GPU is considered busy",
    )
    resident_runtime_repeat_preflight.add_argument(
        "--allow-existing",
        action="store_true",
        help="allow repeat output directories that already exist without run_timing.json",
    )
    resident_runtime_repeat_preflight.add_argument(
        "--skip-gpu-probe",
        action="store_true",
        help="skip nvidia-smi probing and record GPU status as unknown",
    )
    resident_runtime_repeat_preflight.add_argument(
        "--fail-when-not-ready",
        action="store_true",
        help="return exit code 2 unless the preflight recommends execution",
    )
    resident_runtime_repeat_preflight.set_defaults(func=cmd_resident_runtime_repeat_preflight)

    resident_calibration_contract = sub.add_parser(
        "resident-calibration-contract",
        help="audit resident CUDA master-calibration evidence from resident_artifacts.json",
    )
    resident_calibration_contract.add_argument(
        "--run",
        required=True,
        help="GLASS run directory with resident_artifacts.json",
    )
    resident_calibration_contract.add_argument(
        "--out",
        required=True,
        help="output resident calibration-contract JSON",
    )
    resident_calibration_contract.add_argument("--markdown", help="optional output Markdown summary")
    resident_calibration_contract.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 if the contract fails",
    )
    resident_calibration_contract.set_defaults(func=cmd_resident_calibration_contract)

    resident_calibration_artifacts = sub.add_parser(
        "resident-calibration-artifacts",
        help="write resident CUDA calibration_artifacts.json from resident_artifacts.json",
    )
    resident_calibration_artifacts.add_argument(
        "--run",
        required=True,
        help="GLASS run directory with resident_artifacts.json",
    )
    resident_calibration_artifacts.add_argument(
        "--out",
        help="output calibration_artifacts JSON; defaults to RUN/calibration_artifacts.json",
    )
    resident_calibration_artifacts.set_defaults(func=cmd_resident_calibration_artifacts)

    resident_result_contract = sub.add_parser(
        "resident-result-contract",
        help="audit resident CUDA integration outputs for result-contract invariants",
    )
    resident_result_contract.add_argument("--run", required=True, help="GLASS run directory with integration_results.json")
    resident_result_contract.add_argument("--out", required=True, help="output resident result-contract JSON")
    resident_result_contract.add_argument("--markdown", help="optional output Markdown summary")
    resident_result_contract.add_argument(
        "--pixel-verify",
        action="store_true",
        help="verify DQ/count maps by tiled FITS reads",
    )
    resident_result_contract.add_argument(
        "--pixel-verify-tile-size",
        type=int,
        default=2048,
        help="tile size for optional pixel verification",
    )
    resident_result_contract.add_argument(
        "--pixel-tolerance",
        type=int,
        default=0,
        help="allowed pixel-count delta during optional pixel verification",
    )
    resident_result_contract.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 if the contract fails",
    )
    resident_result_contract.set_defaults(func=cmd_resident_result_contract)

    resident_reg_triage = sub.add_parser(
        "resident-registration-triage",
        help="triage resident registration failures and determinism drift between candidate audits",
    )
    resident_reg_triage.add_argument("--baseline-audit", required=True, help="baseline candidate audit JSON")
    resident_reg_triage.add_argument(
        "--candidate-audit",
        action="append",
        required=True,
        help="candidate audit JSON; repeat for multiple variants",
    )
    resident_reg_triage.add_argument("--out", required=True, help="output triage JSON")
    resident_reg_triage.add_argument("--markdown", help="optional output Markdown summary")
    resident_reg_triage.add_argument(
        "--fail-on-extra-rejections",
        action="store_true",
        help="return exit code 2 when any candidate rejects frames accepted by the baseline",
    )
    resident_reg_triage.set_defaults(func=cmd_resident_registration_triage)

    stack_contract = sub.add_parser(
        "stack-engine-contract",
        help="audit StackEngine default routing and DQ provenance from a GLASS run",
    )
    stack_contract.add_argument("--run", required=True, help="GLASS run directory to audit")
    stack_contract.add_argument("--out", required=True, help="output audit JSON")
    stack_contract.add_argument("--markdown", help="optional output Markdown summary")
    stack_contract.add_argument(
        "--scope",
        choices=["all", "calibration", "integration"],
        default="all",
        help="which StackEngine contract surface to audit",
    )
    stack_contract.add_argument(
        "--expected-integration-engine",
        choices=["stack_engine_cpu", "cuda_resident_stack", "any"],
        default="stack_engine_cpu",
        help="expected integration engine for the selected run type",
    )
    stack_contract.add_argument(
        "--resident-calibration-contract-json",
        help="optional resident-calibration-contract JSON used to prove resident CUDA master-calibration parity",
    )
    stack_contract.add_argument(
        "--resident-result-contract-json",
        help="optional resident-result-contract JSON used to prove resident CUDA result-contract parity",
    )
    stack_contract.add_argument(
        "--require-default-ready",
        action="store_true",
        help="return a nonzero status unless the audit is ready for full StackEngine default promotion",
    )
    stack_contract.add_argument(
        "--require-native-stack-engine-default",
        action="store_true",
        help=(
            "return exit code 4 unless every audited surface is a native stack_engine_cpu default path; "
            "resident CUDA contract-emulation surfaces remain explicit gaps"
        ),
    )
    stack_contract.set_defaults(func=cmd_stack_engine_contract)

    pipeline_contract = sub.add_parser(
        "pipeline-contract",
        help="audit DQ, LN, rejection, crop, and output-map invariants from a GLASS run",
    )
    pipeline_contract.add_argument("--run", required=True, help="GLASS run directory to audit")
    pipeline_contract.add_argument("--out", required=True, help="output audit JSON")
    pipeline_contract.add_argument("--markdown", help="optional output Markdown summary")
    pipeline_contract.add_argument(
        "--pixel-verify",
        action="store_true",
        help="read integration DQ and count maps in tiles and compare pixel counts to JSON summaries",
    )
    pipeline_contract.add_argument(
        "--pixel-verify-tile-size",
        type=int,
        default=2048,
        help="tile size for optional pipeline-contract FITS pixel verification",
    )
    pipeline_contract.add_argument(
        "--pixel-tolerance",
        type=int,
        default=0,
        help="allowed pixel-count delta for optional pipeline-contract FITS pixel verification",
    )
    pipeline_contract.add_argument(
        "--resident-calibration-contract-json",
        help="optional resident CUDA calibration contract JSON used to prove resident calibration surface invariants",
    )
    pipeline_contract.add_argument(
        "--local-norm-contract-json",
        help="optional local-normalization contract JSON used to prove continuous LN coefficient-field invariants",
    )
    pipeline_contract.set_defaults(func=cmd_pipeline_contract)

    local_norm_contract = sub.add_parser(
        "local-norm-contract",
        help="audit continuous local-normalization coefficient-field artifacts from a GLASS run",
    )
    local_norm_contract.add_argument("--run", required=True, help="GLASS run directory to audit")
    local_norm_contract.add_argument("--out", required=True, help="output audit JSON")
    local_norm_contract.add_argument("--markdown", help="optional output Markdown summary")
    local_norm_contract.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when the local-normalization contract fails",
    )
    local_norm_contract.set_defaults(func=cmd_local_norm_contract)

    warp_quality_contract = sub.add_parser(
        "warp-quality-contract",
        help="audit warp registered, coverage, DQ, and optional residual artifacts from a GLASS run",
    )
    warp_quality_contract.add_argument("--run", required=True, help="GLASS run directory to audit")
    warp_quality_contract.add_argument("--out", required=True, help="output audit JSON")
    warp_quality_contract.add_argument("--markdown", help="optional output Markdown summary")
    warp_quality_contract.add_argument(
        "--min-valid-fraction",
        type=float,
        help="fail when accepted warp outputs have a lower valid-pixel fraction",
    )
    warp_quality_contract.add_argument(
        "--max-skipped-frames",
        type=int,
        help="fail when warp skipped-frame count exceeds this threshold",
    )
    warp_quality_contract.add_argument(
        "--require-artifacts",
        action="store_true",
        help="fail unless warp registered, coverage, and DQ artifacts are present",
    )
    warp_quality_contract.add_argument(
        "--require-all-registered",
        action="store_true",
        help="fail unless every accepted registration frame has a warp output",
    )
    warp_quality_contract.add_argument(
        "--pixel-verify",
        action="store_true",
        help="scan warp coverage/DQ FITS pixels and fail when counts disagree with summaries",
    )
    warp_quality_contract.add_argument(
        "--pixel-verify-tile-size",
        type=int,
        default=2048,
        help="tile size for optional warp coverage/DQ pixel verification",
    )
    warp_quality_contract.add_argument(
        "--pixel-tolerance",
        type=int,
        default=0,
        help="allowed count delta for optional warp coverage/DQ pixel verification",
    )
    warp_quality_contract.add_argument(
        "--science-residual-verify",
        action="store_true",
        help="stream registered warp outputs and compare science pixels against the reference warp output",
    )
    warp_quality_contract.add_argument(
        "--science-reference-frame-id",
        help="reference frame id for optional warp science residual verification; defaults to reference output",
    )
    warp_quality_contract.add_argument(
        "--max-science-rms",
        type=float,
        help="fail when warp science residual RMS exceeds this threshold",
    )
    warp_quality_contract.add_argument(
        "--max-science-max-abs",
        type=float,
        help="fail when warp science residual maximum absolute difference exceeds this threshold",
    )
    warp_quality_contract.add_argument(
        "--science-residual-tile-size",
        type=int,
        default=2048,
        help="tile size for optional warp registered-image residual verification",
    )
    warp_quality_contract.add_argument(
        "--fail-on-failed",
        action="store_true",
        help="return exit code 2 when the warp quality contract fails",
    )
    warp_quality_contract.set_defaults(func=cmd_warp_quality_contract)

    guardrails = sub.add_parser(
        "guardrails",
        help="generate StackEngine, pipeline, optional pixel, and HTML guardrail artifacts for a run",
    )
    guardrails.add_argument("--run", required=True, help="existing GLASS run directory to audit")
    guardrails.add_argument("--out-dir", required=True, help="directory for guardrail JSON/Markdown/report outputs")
    guardrails.add_argument("--report", help="optional HTML report path; defaults to OUT_DIR/report.html")
    guardrails.add_argument(
        "--stack-scope",
        choices=["all", "calibration", "integration"],
        default="all",
        help="StackEngine contract scope",
    )
    guardrails.add_argument(
        "--expected-integration-engine",
        choices=["stack_engine_cpu", "cuda_resident_stack", "any"],
        default="any",
        help="expected integration engine for the StackEngine contract",
    )
    guardrails.add_argument(
        "--resident-calibration-contract-json",
        help="optional resident CUDA calibration contract JSON to attach to the StackEngine contract audit",
    )
    guardrails.add_argument(
        "--resident-result-contract-json",
        help="optional resident CUDA result contract JSON to attach to the StackEngine contract audit",
    )
    guardrails.add_argument(
        "--require-stack-default-ready",
        action="store_true",
        help="fail guardrails unless the StackEngine contract is ready for full default promotion",
    )
    guardrails.add_argument(
        "--require-local-normalization-enabled",
        action="store_true",
        help="fail guardrails unless local normalization is present, enabled, and passes its contract",
    )
    guardrails.add_argument(
        "--max-local-normalization-rms",
        type=float,
        help="fail guardrails when enabled local-normalization residual max RMS exceeds this threshold",
    )
    guardrails.add_argument(
        "--max-local-normalization-max-abs",
        type=float,
        help="fail guardrails when enabled local-normalization residual max absolute error exceeds this threshold",
    )
    guardrails.add_argument(
        "--max-registration-rms-px",
        type=float,
        help="fail guardrails when accepted registration outputs exceed this RMS threshold",
    )
    guardrails.add_argument(
        "--min-registration-inliers",
        type=int,
        help="fail guardrails when accepted registration outputs have fewer inliers than this threshold",
    )
    guardrails.add_argument(
        "--require-registration-all-accepted",
        action="store_true",
        help="fail guardrails when any registration output is rejected or skipped",
    )
    guardrails.add_argument(
        "--min-warp-valid-fraction",
        type=float,
        help="fail guardrails when accepted warp outputs have a lower valid-pixel fraction",
    )
    guardrails.add_argument(
        "--max-warp-skipped-frames",
        type=int,
        help="fail guardrails when warp skipped-frame count exceeds this threshold",
    )
    guardrails.add_argument(
        "--require-warp-artifacts",
        action="store_true",
        help="fail guardrails unless warp registered, coverage, and DQ artifacts are present",
    )
    guardrails.add_argument(
        "--require-warp-all-registered",
        action="store_true",
        help="fail guardrails unless every accepted registration frame has a warp output",
    )
    guardrails.add_argument(
        "--warp-pixel-verify",
        action="store_true",
        help="scan warp coverage/DQ FITS pixels and fail when counts disagree with summaries",
    )
    guardrails.add_argument(
        "--warp-pixel-verify-tile-size",
        type=int,
        default=2048,
        help="tile size for optional warp coverage/DQ pixel verification",
    )
    guardrails.add_argument(
        "--warp-pixel-tolerance",
        type=int,
        default=0,
        help="allowed count delta for optional warp coverage/DQ pixel verification",
    )
    guardrails.add_argument(
        "--warp-science-residual-verify",
        action="store_true",
        help="stream registered warp outputs and compare science pixels against the reference warp output",
    )
    guardrails.add_argument(
        "--warp-science-reference-frame-id",
        help="reference frame id for optional warp science residual verification; defaults to reference output",
    )
    guardrails.add_argument(
        "--max-warp-science-rms",
        type=float,
        help="fail guardrails when warp science residual RMS exceeds this threshold",
    )
    guardrails.add_argument(
        "--max-warp-science-max-abs",
        type=float,
        help="fail guardrails when warp science residual maximum absolute difference exceeds this threshold",
    )
    guardrails.add_argument(
        "--warp-science-residual-tile-size",
        type=int,
        default=2048,
        help="tile size for optional warp registered-image residual verification",
    )
    guardrails.add_argument(
        "--pixel-verify",
        action="store_true",
        help="enable tiled FITS pixel verification in the pipeline contract",
    )
    guardrails.add_argument(
        "--pixel-verify-tile-size",
        type=int,
        default=2048,
        help="tile size for optional pipeline-contract FITS pixel verification",
    )
    guardrails.add_argument(
        "--pixel-tolerance",
        type=int,
        default=0,
        help="allowed pixel-count delta for optional pipeline-contract FITS pixel verification",
    )
    guardrails.set_defaults(func=cmd_guardrails)

    blackbox = sub.add_parser("blackbox-package", help="write a PixInsight/WBPP black-box handoff package")
    blackbox.add_argument("--manifest", required=True)
    blackbox.add_argument("--out", required=True)
    blackbox.add_argument("--plan")
    blackbox.add_argument("--glass-run")
    blackbox.add_argument("--glass-time-seconds", type=float)
    blackbox.add_argument("--reference-label", default="PixInsight WBPP")
    blackbox.set_defaults(func=cmd_blackbox_package)

    finalize = sub.add_parser("blackbox-finalize", help="finalize a PixInsight/WBPP black-box timing package")
    finalize.add_argument("--timing", required=True)
    finalize.add_argument("--out")
    finalize.set_defaults(func=cmd_blackbox_finalize)

    history = sub.add_parser(
        "blackbox-history",
        help="extract user-generated WBPP FastIntegration ProcessingHistory from a XISF master",
    )
    history.add_argument("--master", required=True)
    history.add_argument("--out", required=True)
    history.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    history.set_defaults(func=cmd_blackbox_history)

    synthetic = sub.add_parser("synthetic", help="generate synthetic FITS data")
    synthetic.add_argument("--out", required=True)
    synthetic.add_argument("--frames", type=int, default=20)
    synthetic.add_argument("--width", type=int, default=512)
    synthetic.add_argument("--height", type=int, default=512)
    synthetic.add_argument("--filter", default="H")
    synthetic.add_argument("--known-shift", action="store_true")
    synthetic.set_defaults(func=cmd_synthetic)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args._glass_argv = list(sys.argv[1:] if argv is None else argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
