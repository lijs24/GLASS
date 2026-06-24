from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from glass.cpu.calibration import calibrate_light
from glass.cli import _apply_resident_runtime_preset
from glass.cli import _resolve_execution_defaults
from glass.cli import _resolve_resident_integration_rejection_default
from glass.cli import _resolve_resident_fits_read_mode_default
from glass.cli import _resolve_resident_local_normalization_default
from glass.cli import _resolve_resident_registration_default
from glass.cli import _resolve_resident_warp_interpolation_default
from glass.cli import _write_resident_reference_admission
from glass.cli import ResidentReferenceAdmissionBlocked
from glass.cli import build_parser
from glass.cli import main
from glass.engine.contracts import DQFlag
from glass.engine.pipeline import initialize_run
from glass.engine.resident_reference_health import build_resident_reference_health
from glass.engine.resident_registration_health import build_resident_registration_health
from glass.engine.resident_reference_scout import write_resident_reference_scout
from glass.io.fits_io import write_fits_data
from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy
from tests.conftest import cuda_module_or_skip


def _parse_cli(argv: list[str]):
    parser = build_parser()
    args = parser.parse_args(argv)
    args._glass_argv = list(argv)
    return args


def _write_resident_registration_quality(
    run: Path,
    *,
    frame_count: int,
    accepted_count: int,
    registration_mode: str = "similarity_cuda_triangle",
) -> None:
    run.mkdir(parents=True, exist_ok=True)
    accepted_count = max(0, min(int(accepted_count), int(frame_count)))
    decisions = []
    for index in range(int(frame_count)):
        frame_id = f"F{index + 1:06d}"
        if index == 0 and accepted_count > 0:
            status = "reference"
            final_status = "reference"
            accepted = True
        elif index < accepted_count:
            status = "accepted"
            final_status = "ok"
            accepted = True
        else:
            status = "rejected"
            final_status = "excluded"
            accepted = False
        decisions.append(
            {
                "schema_version": 1,
                "frame_id": frame_id,
                "registration_mode": registration_mode,
                "requested_action": "auto",
                "effective_action": "exclude",
                "original_status": "reference" if status == "reference" else "ok",
                "final_status": final_status,
                "decision_status": status,
                "action_applied": "none" if accepted else "exclude",
                "accepted": accepted,
                "matched_stars": 8 if accepted else 3,
                "inliers": 8 if accepted else 3,
                "rms_px": 0.5 if accepted else 1.25,
                "thresholds": {
                    "min_inliers": 4,
                    "max_rms_px": None,
                    "max_rms_enabled": False,
                    "catalog_capacity_limited": False,
                },
                "diagnostics": {},
                "reasons": [] if accepted else ["registration_inliers_below_min:3<4"],
            }
        )
    rejected_ids = [item["frame_id"] for item in decisions if not item["accepted"]]
    write_json(
        run / "resident_registration_quality.json",
        {
            "schema_version": 1,
            "source_stage": "resident_calibrated_stack",
            "registration_mode": registration_mode,
            "requested_action": "auto",
            "min_inliers": 4,
            "max_rms_px": None,
            "summary": {
                "frame_count": int(frame_count),
                "decision_status_counts": {
                    "reference": 1 if accepted_count > 0 else 0,
                    "accepted": max(0, accepted_count - 1),
                    "rejected": max(0, int(frame_count) - accepted_count),
                },
                "final_status_counts": {
                    "reference": 1 if accepted_count > 0 else 0,
                    "ok": max(0, accepted_count - 1),
                    "excluded": max(0, int(frame_count) - accepted_count),
                },
                "action_counts": {
                    "none": accepted_count,
                    "exclude": max(0, int(frame_count) - accepted_count),
                },
                "rejected_frame_ids": rejected_ids,
                "warning_frame_ids": [],
            },
            "decisions": decisions,
        },
    )


def _light_frame_id_by_stem(plan_path: Path, stem: str) -> str:
    plan = read_json(plan_path)
    for frame in plan.get("frames", []):
        if frame.get("frame_type") == "light" and Path(str(frame.get("path"))).stem == stem:
            return str(frame["id"])
    raise AssertionError(f"missing light frame stem: {stem}")


def _write_minimal_cuda_reference_scout(run: Path, *, reference_frame_id: str) -> Path:
    run.mkdir(parents=True, exist_ok=True)
    scout = {
        "schema_version": 1,
        "artifact_type": "resident_reference_scout",
        "metric_source": "unit_test_cuda_reference_scout",
        "sample_stride": 1,
        "sample_side": 768,
        "max_frames": 0,
        "threshold_sigma": 5.0,
        "max_stars": 300,
        "catalog_backend_requested": "cuda",
        "catalog_backend": "cuda",
        "catalog_backend_resolution": {"requested": "cuda", "effective": "cuda", "cuda_status": "available"},
        "frame_count": 2,
        "scouted_frame_count": 2,
        "measured_frame_count": 2,
        "error_count": 0,
        "frame_quality": [
            {
                "frame_id": reference_frame_id,
                "reference_candidate": True,
                "catalog_backend": "cuda",
                "star_count": 16,
                "quality_score": 100.0,
            }
        ],
        "errors": [],
        "reference_frame_id": reference_frame_id,
    }
    scout_path = run / "resident_reference_scout.json"
    write_json(scout_path, scout)
    quality = dict(scout)
    quality["artifact_type"] = "frame_quality"
    quality["source_artifact"] = str(scout_path)
    write_json(run / "frame_quality.json", quality)
    return scout_path


def _write_cuda_reference_scout_from_cpu_scout(plan: Path, run: Path, *, reference_frame_id: str) -> Path:
    scout_path = write_resident_reference_scout(plan, run, sample_stride=1, max_frames=0, catalog_backend="cpu")
    scout = read_json(scout_path)
    scout["catalog_backend_requested"] = "cuda"
    scout["catalog_backend"] = "cuda"
    scout["catalog_backend_resolution"] = {"requested": "cuda", "effective": "cuda", "cuda_status": "unit_test"}
    scout["reference_frame_id"] = reference_frame_id
    for row in scout.get("frame_quality", []):
        row["catalog_backend"] = "cuda"
    write_json(scout_path, scout)
    quality = dict(scout)
    quality["artifact_type"] = "frame_quality"
    quality["source_artifact"] = str(scout_path)
    write_json(run / "frame_quality.json", quality)
    return scout_path


def _write_reference_health_master_cache(cache_dir: Path, *, shape: tuple[int, int] = (32, 32)) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = "H_32x32_bias-test_dark-test_flat-test_unit"
    np.save(cache_dir / f"{key}_master_bias.npy", np.full(shape, 100.0, dtype=np.float32))
    np.save(cache_dir / f"{key}_master_dark.npy", np.full(shape, 110.0, dtype=np.float32))
    np.save(cache_dir / f"{key}_master_flat.npy", np.ones(shape, dtype=np.float32))
    stats_path = cache_dir / f"{key}_master_stats.json"
    write_json(
        stats_path,
        {
            "cache_key": key,
            "cache_dir": str(cache_dir),
            "cache_fingerprint": "unit",
            "filter": "H",
            "shape": {"height": shape[0], "width": shape[1]},
            "bias_count": 1,
            "dark_count": 1,
            "flat_count": 1,
            "dark_exposure_s": 60.0,
            "master_dark_includes_bias": True,
            "flat_normalization": {"flat_floor": 0.05},
        },
    )
    return stats_path


def _write_uniform_no_star_dataset(root: Path) -> None:
    shape = (16, 20)
    specs = [
        ("bias", "bias_001.fits", 0.0, 100.0),
        ("dark", "dark_001.fits", 60.0, 110.0),
        ("flat", "flat_001.fits", 60.0, 1000.0),
        ("light", "light_001.fits", 60.0, 1200.0),
    ]
    for frame_type, name, exposure, value in specs:
        write_fits_data(
            root / frame_type / name,
            np.ones(shape, dtype=np.float32) * value,
            {
                "IMAGETYP": frame_type,
                "FILTER": "H",
                "EXPTIME": exposure,
                "GAIN": 100.0,
                "OFFSET": 20.0,
                "CCD-TEMP": -10.0,
                "XBINNING": 1,
                "YBINNING": 1,
            },
        )


def _write_two_light_reference_scout_dataset(root: Path) -> None:
    shape = (32, 32)
    specs = [
        ("bias", "bias_001.fits", 0.0, np.full(shape, 100.0, dtype=np.float32)),
        ("dark", "dark_001.fits", 60.0, np.full(shape, 110.0, dtype=np.float32)),
        ("flat", "flat_001.fits", 60.0, np.full(shape, 1000.0, dtype=np.float32)),
    ]
    yy, xx = np.indices(shape, dtype=np.float32)
    weak_light = np.full(shape, 1200.0, dtype=np.float32)
    star_light = np.full(shape, 1200.0, dtype=np.float32)
    for x, y, flux in [(8.0, 9.0, 5000.0), (16.0, 18.0, 7000.0), (24.0, 11.0, 6000.0)]:
        star_light += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 0.8**2)))
    specs.extend(
        [
            ("light", "light_001.fits", 60.0, weak_light),
            ("light", "light_002.fits", 60.0, star_light),
        ]
    )
    for frame_type, name, exposure, data in specs:
        write_fits_data(
            root / frame_type / name,
            data,
            {
                "IMAGETYP": frame_type,
                "FILTER": "H",
                "EXPTIME": exposure,
                "GAIN": 100.0,
                "OFFSET": 20.0,
                "CCD-TEMP": -10.0,
                "XBINNING": 1,
                "YBINNING": 1,
            },
        )


def _write_orientation_reference_scout_dataset(root: Path) -> None:
    shape = (40, 40)
    yy, xx = np.indices(shape, dtype=np.float32)

    def light(stars: list[tuple[float, float, float]]) -> np.ndarray:
        data = np.full(shape, 1200.0, dtype=np.float32)
        for x, y, flux in stars:
            data += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 0.8**2)))
        return data

    specs = [
        ("bias", "bias_001.fits", 0.0, "West", np.full(shape, 100.0, dtype=np.float32)),
        ("dark", "dark_001.fits", 60.0, "West", np.full(shape, 110.0, dtype=np.float32)),
        ("flat", "flat_001.fits", 60.0, "West", np.full(shape, 1000.0, dtype=np.float32)),
        ("light", "light_west_001.fits", 60.0, "West", light([(12.0, 12.0, 3000.0)])),
        ("light", "light_west_002.fits", 60.0, "West", light([(26.0, 24.0, 3500.0)])),
        (
            "light",
            "light_east_001.fits",
            60.0,
            "East",
            light([(8.0, 8.0, 8000.0), (20.0, 22.0, 8000.0), (32.0, 15.0, 8000.0)]),
        ),
    ]
    for frame_type, name, exposure, pierside, data in specs:
        write_fits_data(
            root / frame_type / name,
            data,
            {
                "IMAGETYP": frame_type,
                "FILTER": "H",
                "EXPTIME": exposure,
                "GAIN": 100.0,
                "OFFSET": 20.0,
                "CCD-TEMP": -10.0,
                "XBINNING": 1,
                "YBINNING": 1,
                "PIERSIDE": pierside,
                "OBJCTROT": 92.0,
            },
        )


def test_resident_runtime_preset_applies_gate158_values() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v1",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_prefetch_frames == 12
    assert args.resident_prefetch_workers == 7
    assert args.resident_prefetch_refill_mode == "queued"
    assert args.resident_h2d_mode == "pinned_ring"
    assert args.resident_calibration_batch_frames == 8
    assert args.resident_calibration_streams == 4
    assert args.resident_calibration_wave_frames == 2
    assert args.resident_calibration_release_mode == "callback_queue"
    assert args._resident_runtime_preset_effective["preset"] == "throughput-v1"


def test_resident_runtime_preset_throughput_v2_fused_applies_auto_dispatch() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v2-fused",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_prefetch_frames == 12
    assert args.resident_prefetch_workers == 7
    assert args.resident_h2d_mode == "pinned_ring"
    assert args.resident_calibration_release_mode == "callback_queue"
    assert args.resident_integration_dispatch == "auto"
    assert args._resident_runtime_preset_effective["preset"] == "throughput-v2-fused"
    assert args._resident_runtime_preset_effective["applied"]["resident_integration_dispatch"] == "auto"


def test_resident_runtime_preset_throughput_v3_io_applies_probe_values() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v3-io",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_prefetch_frames == 32
    assert args.resident_prefetch_workers == 16
    assert args.resident_prefetch_refill_mode == "queued"
    assert args.resident_h2d_mode == "pinned_ring"
    assert args.resident_calibration_batch_frames == 16
    assert args.resident_calibration_streams == 4
    assert args.resident_calibration_wave_frames == 4
    assert args.resident_calibration_release_mode == "callback_queue"
    assert args.resident_native_queue_read == "on"
    assert args.resident_native_queue_drain_mode == "thread"
    assert args.resident_warp_chunk_capacity_frames == 32
    assert args.resident_integration_dispatch == "stack"
    assert args._resident_runtime_preset_effective["preset"] == "throughput-v3-io"
    assert args._resident_runtime_preset_effective["applied"]["resident_native_queue_read"] == "on"
    assert args._resident_runtime_preset_effective["applied"]["resident_warp_chunk_capacity_frames"] == 32


def test_resident_runtime_preset_throughput_v4_native_completion_is_explicit_ab_route() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v4-native-completion",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_prefetch_frames == 32
    assert args.resident_prefetch_workers == 16
    assert args.resident_prefetch_refill_mode == "queued"
    assert args.resident_h2d_mode == "pinned_ring"
    assert args.resident_calibration_batch_frames == 16
    assert args.resident_calibration_streams == 4
    assert args.resident_calibration_wave_frames == 4
    assert args.resident_calibration_release_mode == "callback_queue"
    assert args.resident_native_completion_calibration == "on"
    assert args.resident_native_completion_wave_fill_us == 25
    assert args._resident_runtime_preset_effective["preset"] == "throughput-v4-native-completion"
    assert (
        args._resident_runtime_preset_effective["applied"]["resident_native_completion_calibration"]
        == "on"
    )


def test_resident_runtime_preset_defaults_to_throughput_v3_io() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    _apply_resident_runtime_preset(args)

    assert args.resident_runtime_preset == "throughput-v3-io"
    assert args.resident_prefetch_frames == 32
    assert args.resident_prefetch_workers == 16
    assert args.resident_h2d_mode == "pinned_ring"
    assert args.resident_calibration_batch_frames == 16
    assert args.resident_calibration_wave_frames == 4
    assert args.resident_calibration_release_mode == "callback_queue"
    assert args.resident_native_completion_calibration == "off"
    assert args.resident_native_completion_wave_fill_us == 0
    assert args.resident_native_queue_read == "on"
    assert args.resident_native_queue_drain_mode == "thread"
    assert args.resident_warp_chunk_capacity_frames == 32
    assert args.resident_integration_dispatch == "stack"
    assert args._resident_runtime_preset_effective["preset"] == "throughput-v3-io"


def test_resident_runtime_preset_manual_keeps_legacy_values() -> None:
    args = _parse_cli(
        [
            "audit",
            "--root",
            "data",
            "--out",
            "run",
            "--resident-runtime-preset",
            "manual",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_runtime_preset == "manual"
    assert args.resident_prefetch_frames == 0
    assert args.resident_prefetch_workers == 1
    assert args.resident_h2d_mode == "pageable"
    assert args.resident_calibration_release_mode == "sync"
    assert args.resident_native_queue_read == "off"
    assert args.resident_native_queue_drain_mode is None
    assert args.resident_warp_chunk_capacity_frames is None
    assert args._resident_runtime_preset_effective["applied"] == {}


def test_resident_runtime_preset_respects_explicit_native_queue_override() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v3-io",
            "--resident-native-queue-read",
            "off",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_native_queue_read == "off"
    assert args.resident_native_queue_drain_mode == "thread"
    assert args.resident_warp_chunk_capacity_frames == 32
    explicit = args._resident_runtime_preset_effective["explicit_overrides"]
    assert explicit["resident_native_queue_read"] == "off"
    assert args._resident_runtime_preset_effective["applied"]["resident_native_queue_drain_mode"] == "thread"
    assert args._resident_runtime_preset_effective["applied"]["resident_warp_chunk_capacity_frames"] == 32


def test_resident_runtime_preset_respects_explicit_warp_chunk_capacity_override() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v3-io",
            "--resident-warp-chunk-capacity-frames",
            "16",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_warp_chunk_capacity_frames == 16
    explicit = args._resident_runtime_preset_effective["explicit_overrides"]
    assert explicit["resident_warp_chunk_capacity_frames"] == 16
    assert "resident_warp_chunk_capacity_frames" not in args._resident_runtime_preset_effective["applied"]


def test_resident_runtime_preset_respects_explicit_overrides() -> None:
    args = _parse_cli(
        [
            "audit",
            "--root",
            "data",
            "--out",
            "run",
            "--resident-runtime-preset",
            "throughput-v2-fused",
            "--resident-prefetch-frames",
            "4",
            "--resident-calibration-streams=2",
            "--resident-integration-dispatch",
            "stack",
        ]
    )

    _apply_resident_runtime_preset(args)

    assert args.resident_prefetch_frames == 4
    assert args.resident_prefetch_workers == 7
    assert args.resident_calibration_streams == 2
    explicit = args._resident_runtime_preset_effective["explicit_overrides"]
    assert explicit["resident_prefetch_frames"] == 4
    assert explicit["resident_calibration_streams"] == 2
    assert explicit["resident_integration_dispatch"] == "stack"
    assert "resident_integration_dispatch" not in args._resident_runtime_preset_effective["applied"]


def test_run_defaults_promote_resident_cuda_when_available() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    resolution = _resolve_execution_defaults(args, {"cuda_available": True}, command="run")

    assert args.backend == "cuda"
    assert args.memory_mode == "resident"
    assert args.until_stage == "integration"
    assert resolution["reason"] == "resident_cuda_default"
    assert resolution["requested_backend"] == "auto"
    assert resolution["requested_memory_mode"] == "resident"
    assert resolution["effective_backend"] == "cuda"


def test_run_resident_registration_defaults_to_similarity_triangle() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_registration_default(args, command="run")

    assert args.backend == "cuda"
    assert args.memory_mode == "resident"
    assert args.resident_registration == "similarity_cuda_triangle"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "similarity_cuda_triangle"
    assert resolution["source"] == "resident_cuda_default"
    assert resolution["escape_hatch"] == "--resident-registration off"


def test_run_resident_registration_explicit_off_is_preserved() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-registration",
            "off",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_registration_default(args, command="run")

    assert args.resident_registration == "off"
    assert resolution["requested"] == "off"
    assert resolution["effective"] == "off"
    assert resolution["explicit"] is True


def test_run_resident_registration_auto_keeps_tile_path_off() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run", "--backend", "cpu"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_registration_default(args, command="run")

    assert args.memory_mode == "tile"
    assert args.resident_registration == "off"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "off"
    assert resolution["source"] == "unused_non_resident"


def test_run_resident_rejection_defaults_to_winsorized_sigma() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_integration_rejection_default(args, command="run")

    assert args.backend == "cuda"
    assert args.memory_mode == "resident"
    assert args.integration_rejection == "winsorized_sigma"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "winsorized_sigma"
    assert resolution["source"] == "resident_cuda_default"
    assert resolution["escape_hatch"] == "--integration-rejection none"


def test_run_resident_rejection_explicit_none_is_preserved() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--integration-rejection",
            "none",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_integration_rejection_default(args, command="run")

    assert args.integration_rejection == "none"
    assert resolution["requested"] == "none"
    assert resolution["effective"] == "none"
    assert resolution["explicit"] is True


def test_run_resident_rejection_auto_keeps_tile_path_auto() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run", "--backend", "cpu"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_integration_rejection_default(args, command="run")

    assert args.memory_mode == "tile"
    assert args.integration_rejection == "auto"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "auto"
    assert resolution["source"] == "unused_non_resident"


def test_run_resident_local_normalization_defaults_to_grid_on() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_local_normalization_default(args, command="run")

    assert args.backend == "cuda"
    assert args.memory_mode == "resident"
    assert args.local_normalization == "on"
    assert args.resident_local_normalization_mode == "grid_mean_std"
    assert args.resident_local_normalization_tile_size == 256
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "on"
    assert resolution["source"] == "resident_cuda_default"
    assert resolution["escape_hatch"] == "--local-normalization off"
    assert resolution["mode"]["effective"] == "grid_mean_std"
    assert resolution["mode"]["source"] == "resident_cuda_default"
    assert resolution["tile_size"]["effective"] == 256
    assert resolution["tile_size"]["source"] == "resident_cuda_default"


def test_run_resident_local_normalization_explicit_off_is_preserved() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--local-normalization",
            "off",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_local_normalization_default(args, command="run")

    assert args.local_normalization == "off"
    assert args.resident_local_normalization_mode == "global_mean_std"
    assert args.resident_local_normalization_tile_size == 512
    assert resolution["requested"] == "off"
    assert resolution["effective"] == "off"
    assert resolution["explicit"] is True


def test_run_resident_local_normalization_explicit_mode_and_tile_are_preserved() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-local-normalization-mode",
            "global_mean_std",
            "--resident-local-normalization-tile-size",
            "1024",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_local_normalization_default(args, command="run")

    assert args.local_normalization == "on"
    assert args.resident_local_normalization_mode == "global_mean_std"
    assert args.resident_local_normalization_tile_size == 1024
    assert resolution["effective"] == "on"
    assert resolution["mode"]["explicit"] is True
    assert resolution["mode"]["source"] == "explicit"
    assert resolution["tile_size"]["explicit"] is True
    assert resolution["tile_size"]["source"] == "explicit"


def test_run_resident_local_normalization_auto_keeps_tile_path_auto() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run", "--backend", "cpu"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_local_normalization_default(args, command="run")

    assert args.memory_mode == "tile"
    assert args.local_normalization == "auto"
    assert args.resident_local_normalization_mode == "global_mean_std"
    assert args.resident_local_normalization_tile_size == 512
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "auto"
    assert resolution["source"] == "unused_non_resident"


def test_run_resident_warp_interpolation_defaults_to_lanczos3_for_matrix_warp() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    resolution = _resolve_resident_warp_interpolation_default(args, command="run")

    assert args.backend == "cuda"
    assert args.memory_mode == "resident"
    assert args.resident_registration == "similarity_cuda_triangle"
    assert args.resident_warp_interpolation == "lanczos3"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "lanczos3"
    assert resolution["source"] == "resident_cuda_default"
    assert resolution["matrix_registration"] is True
    assert resolution["escape_hatch"] == "--resident-warp-interpolation bilinear"


def test_run_resident_warp_interpolation_explicit_bilinear_is_preserved() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-warp-interpolation",
            "bilinear",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    resolution = _resolve_resident_warp_interpolation_default(args, command="run")

    assert args.resident_warp_interpolation == "bilinear"
    assert resolution["requested"] == "bilinear"
    assert resolution["effective"] == "bilinear"
    assert resolution["explicit"] is True
    assert resolution["source"] == "explicit"


def test_run_resident_warp_interpolation_auto_without_matrix_warp_uses_bilinear_fallback() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--resident-registration",
            "off",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    resolution = _resolve_resident_warp_interpolation_default(args, command="run")

    assert args.memory_mode == "resident"
    assert args.resident_registration == "off"
    assert args.resident_warp_interpolation == "bilinear"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "bilinear"
    assert resolution["matrix_registration"] is False


def test_run_resident_warp_interpolation_auto_keeps_tile_path_bilinear_placeholder() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run", "--backend", "cpu"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    resolution = _resolve_resident_warp_interpolation_default(args, command="run")

    assert args.memory_mode == "tile"
    assert args.resident_warp_interpolation == "bilinear"
    assert resolution["requested"] == "auto"
    assert resolution["effective"] == "bilinear"
    assert resolution["source"] == "unused_non_matrix"


def test_run_default_resident_matrix_registration_blocks_first_light_reference_fallback(tmp_path: Path) -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", str(tmp_path)])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")

    with pytest.raises(ResidentReferenceAdmissionBlocked) as excinfo:
        _write_resident_reference_admission(tmp_path, args)

    admission = read_json(tmp_path / "resident_reference_admission.json")
    assert args.resident_registration == "similarity_cuda_triangle"
    assert admission["blocking"] is True
    assert admission["reason"] == "default_matrix_registration_without_reference"
    assert admission["resident_registration_source"] == "resident_cuda_default"
    assert admission["quality_reference"]["status"] == "absent"
    assert "--reference-frame-id <frame-id-or-filename>" in admission["recommended_actions"]
    assert "first_light_fallback" in str(excinfo.value)


def test_run_explicit_resident_matrix_registration_keeps_first_light_diagnostic_escape_hatch(tmp_path: Path) -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            str(tmp_path),
            "--resident-registration",
            "similarity_cuda_triangle",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    path = _write_resident_reference_admission(tmp_path, args)

    admission = read_json(path)
    assert admission["blocking"] is False
    assert admission["reason"] == "explicit_registration_first_light_fallback_allowed"
    assert admission["resident_registration_source"] == "explicit"


def test_run_default_resident_matrix_registration_allows_quality_reference(tmp_path: Path) -> None:
    write_json(tmp_path / "frame_quality.json", {"schema_version": 1, "reference_frame_id": "F000123"})
    args = _parse_cli(["run", "--plan", "plan.json", "--out", str(tmp_path)])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    path = _write_resident_reference_admission(tmp_path, args)

    admission = read_json(path)
    assert admission["blocking"] is False
    assert admission["has_reference_source"] is True
    assert admission["quality_reference"]["available"] is True
    assert admission["quality_reference"]["reference_frame_id"] == "F000123"


def test_run_default_resident_matrix_registration_can_explicitly_allow_first_light_fallback(tmp_path: Path) -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            str(tmp_path),
            "--resident-reference-fallback",
            "allow-first-light",
        ]
    )

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    _resolve_resident_registration_default(args, command="run")
    path = _write_resident_reference_admission(tmp_path, args)

    admission = read_json(path)
    assert admission["blocking"] is False
    assert admission["reason"] == "explicit_first_light_fallback_allowed"
    assert admission["resident_registration_source"] == "resident_cuda_default"


def test_cli_resident_run_can_disable_reference_scout_and_block_first_light_fallback(
    small_fits_dataset,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_no_reference"
    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})

    def fail_if_resident_compute_starts(*_args, **_kwargs):
        raise AssertionError("resident CUDA compute should not start after reference admission failure")

    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fail_if_resident_compute_starts)

    assert main(["run", "--plan", str(plan), "--out", str(run), "--resident-reference-scout", "off"]) == 2
    admission = read_json(run / "resident_reference_admission.json")
    state = read_json(run / "run_state.json")
    timing = read_json(run / "run_timing.json")

    assert admission["blocking"] is True
    assert admission["reason"] == "default_matrix_registration_without_reference"
    assert admission["resident_registration_source"] == "resident_cuda_default"
    assert state["failed_stage"] == "resident_reference_admission"
    assert state["artifacts"][0]["stage"] == "resident_reference_admission"
    assert timing["stages"][0]["stage"] == "resident_reference_admission"
    assert timing["stages"][0]["status"] == "failed"
    assert not (run / "resident_reference_scout.json").exists()
    assert not (run / "resident_memory_admission.json").exists()


def test_cli_resident_run_auto_reference_scout_feeds_reference_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_auto_reference"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})

    def fake_memory_admission(run_dir, _args, *, plan_path=None):
        path = Path(run_dir) / "resident_memory_admission.json"
        write_json(path, {"schema_version": 1, "blocking": False, "plan_path": str(plan_path)})
        return path

    def fake_resident_run(_plan_path, out_dir, *_args, **_kwargs):
        state = initialize_run(Path(out_dir))
        state.current_stage = "integration"
        state.completed_stages.append("resident_calibration_integration")
        _write_resident_registration_quality(Path(out_dir), frame_count=2, accepted_count=2)
        return state

    monkeypatch.setattr("glass.cli._write_resident_memory_admission", fake_memory_admission)
    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fake_resident_run)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--resident-reference-scout-stride",
                "1",
                "--resident-reference-scout-backend",
                "cpu",
            ]
        )
        == 0
    )
    scout = read_json(run / "resident_reference_scout.json")
    quality = read_json(run / "frame_quality.json")
    admission = read_json(run / "resident_reference_admission.json")
    state = read_json(run / "run_state.json")
    timing = read_json(run / "run_timing.json")

    reference_row = next(row for row in scout["frame_quality"] if row["frame_id"] == scout["reference_frame_id"])
    assert Path(reference_row["source_path"]).name == "light_002.fits"
    assert scout["catalog_backend"] == "cpu"
    assert reference_row["catalog_backend"] == "cpu"
    assert quality["reference_frame_id"] == scout["reference_frame_id"]
    assert quality["source_artifact"] == str(run / "resident_reference_scout.json")
    assert admission["blocking"] is False
    assert admission["quality_reference"]["reference_frame_id"] == scout["reference_frame_id"]
    assert "resident_reference_scout" in state["completed_stages"]
    assert any(item["stage"] == "resident_reference_scout" for item in state["artifacts"])
    assert [item["stage"] for item in timing["stages"][:2]] == [
        "resident_reference_scout",
        "resident_reference_admission",
    ]
    assert (run / "resident_registration_health.json").exists()


def test_resident_registration_health_passes_healthy_quality(tmp_path: Path) -> None:
    run = tmp_path / "healthy"
    _write_resident_registration_quality(run, frame_count=200, accepted_count=193)

    health = build_resident_registration_health(run)

    assert health["effective_action"] == "fail"
    assert health["passed"] is True
    assert health["blocking"] is False
    assert health["summary"]["accepted_count"] == 193
    assert health["summary"]["accepted_fraction"] == pytest.approx(0.965)


def test_resident_registration_health_blocks_catastrophic_rejection(tmp_path: Path) -> None:
    run = tmp_path / "catastrophic"
    _write_resident_registration_quality(run, frame_count=200, accepted_count=6)

    health = build_resident_registration_health(run)

    assert health["effective_action"] == "fail"
    assert health["passed"] is False
    assert health["blocking"] is True
    assert health["summary"]["accepted_count"] == 6
    assert "resident_registration_min_accepted_fraction" in health["failed_checks"]


def test_cli_resident_run_blocks_catastrophic_registration_health(
    small_fits_dataset,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_bad_registration_health"
    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})

    def fake_resident_compute(*args, **kwargs):
        out_dir = Path(kwargs.get("out_dir") or args[1])
        state = initialize_run(out_dir)
        state.current_stage = "integration"
        state.completed_stages.append("resident_calibration_integration")
        _write_resident_registration_quality(out_dir, frame_count=200, accepted_count=6)
        return state

    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fake_resident_compute)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--resident-reference-fallback",
                "allow-first-light",
            ]
        )
        == 2
    )
    health = read_json(run / "resident_registration_health.json")
    state = read_json(run / "run_state.json")
    timing = read_json(run / "run_timing.json")

    assert health["blocking"] is True
    assert health["summary"]["accepted_count"] == 6
    assert state["failed_stage"] == "resident_registration_health"
    assert any(item["stage"] == "resident_registration_health" for item in state["artifacts"])
    assert timing["stages"][-1]["stage"] == "resident_registration_health"
    assert timing["stages"][-1]["status"] == "failed"


def test_resident_reference_scout_prefers_dominant_orientation(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_orientation_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "scout"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    scout_path = write_resident_reference_scout(plan, run, sample_stride=1, max_frames=0, catalog_backend="cpu")
    scout = read_json(scout_path)
    reference_row = next(row for row in scout["frame_quality"] if row["frame_id"] == scout["reference_frame_id"])

    assert scout["dominant_orientation_key"] == ["west", "92.0"]
    assert scout["orientation_constraint_applied"] is True
    assert Path(reference_row["source_path"]).name.startswith("light_west_")
    assert reference_row["orientation_key"] == ["west", "92.0"]


def test_resident_reference_scout_cuda_catalog_backend_records_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glass_cuda

    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "cuda_scout"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    def fake_grid_catalog(data, threshold, grid_cols, grid_rows, candidates_per_cell, max_output_candidates, min_separation_px):
        image = np.asarray(data, dtype=np.float32)
        ys, xs = np.nonzero(image > float(threshold))
        flux = image[ys, xs].astype(np.float32)
        order = np.argsort(-flux, kind="stable")[: int(max_output_candidates)]
        return {
            "count": int(len(xs)),
            "stored_count": int(len(order)),
            "grid_cols": int(grid_cols),
            "grid_rows": int(grid_rows),
            "candidates_per_cell": int(candidates_per_cell),
            "grid_capacity": int(grid_cols) * int(grid_rows) * int(candidates_per_cell),
            "max_output_candidates": int(max_output_candidates),
            "min_separation_px": float(min_separation_px),
            "catalog_sort_mode": "fake_cuda_test",
            "catalog_topk_mode": "fake_cuda_test",
            "x": xs[order].astype(np.float32),
            "y": ys[order].astype(np.float32),
            "flux": flux[order].astype(np.float32),
        }

    monkeypatch.setattr(glass_cuda, "cuda_available", lambda: True)
    monkeypatch.setattr(glass_cuda, "star_grid_top_nms_candidates_f32", fake_grid_catalog)

    scout_path = write_resident_reference_scout(
        plan,
        run,
        sample_stride=1,
        max_frames=0,
        catalog_backend="cuda",
    )
    scout = read_json(scout_path)
    reference_row = next(row for row in scout["frame_quality"] if row["frame_id"] == scout["reference_frame_id"])

    assert scout["catalog_backend_requested"] == "cuda"
    assert scout["catalog_backend"] == "cuda"
    assert scout["catalog_backend_resolution"]["cuda_status"] == "available"
    assert Path(reference_row["source_path"]).name == "light_002.fits"
    assert reference_row["catalog_backend"] == "cuda"
    assert reference_row["star_detector"] == "cuda_grid_top_nms_candidates_f32_sampled_raw"
    assert reference_row["catalog_diagnostics"]["catalog_model"] == "cuda_grid_top_nms_candidates_f32"
    assert reference_row["catalog_diagnostics"]["catalog_sort_mode"] == "fake_cuda_test"


def test_resident_reference_health_passes_cuda_reference_with_cpu_crosscheck(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "reference_health_pass"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    strong_id = _light_frame_id_by_stem(plan, "light_002")
    _write_minimal_cuda_reference_scout(run, reference_frame_id=strong_id)

    health = build_resident_reference_health(plan, run)

    assert health["effective_action"] == "fail"
    assert health["passed"] is True
    assert health["blocking"] is False
    assert health["summary"]["reference_frame_id"] == strong_id
    assert health["summary"]["cpu_reference_frame_id"] == strong_id
    assert health["summary"]["selected_cpu_rank"] == 1


def test_resident_reference_health_blocks_cuda_reference_cpu_crosscheck_miss(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "reference_health_fail"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    weak_id = _light_frame_id_by_stem(plan, "light_001")
    strong_id = _light_frame_id_by_stem(plan, "light_002")
    _write_minimal_cuda_reference_scout(run, reference_frame_id=weak_id)

    health = build_resident_reference_health(plan, run)

    assert health["effective_action"] == "fail"
    assert health["passed"] is False
    assert health["blocking"] is True
    assert health["summary"]["reference_frame_id"] == weak_id
    assert health["summary"]["cpu_reference_frame_id"] == strong_id
    assert "selected_reference_cpu_star_ratio" in health["failed_checks"]


def test_resident_reference_health_records_calibrated_master_cache_crosscheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glass_cuda

    monkeypatch.setattr(glass_cuda, "cuda_available", lambda: False)
    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "reference_health_calibrated"
    cache_dir = tmp_path / "resident_master_cache"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    strong_id = _light_frame_id_by_stem(plan, "light_002")
    _write_cuda_reference_scout_from_cpu_scout(plan, run, reference_frame_id=strong_id)
    _write_reference_health_master_cache(cache_dir)

    health = build_resident_reference_health(plan, run, master_cache_dir=cache_dir, flat_floor=0.05)

    calibrated = health["calibrated_crosscheck"]
    assert health["passed"] is True
    assert calibrated["available"] is True
    assert calibrated["status"] == "passed"
    assert calibrated["master_cache"]["cache_dir"] == str(cache_dir)
    assert calibrated["summary"]["reference_frame_id"] == strong_id
    assert calibrated["summary"]["calibrated_reference_frame_id"] == strong_id
    assert calibrated["summary"]["selected_calibrated_rank"] == 1


def test_resident_reference_health_cuda_calibrated_crosscheck_is_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glass_cuda

    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "reference_health_cuda_calibrated_diagnostic"
    cache_dir = tmp_path / "resident_master_cache"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    weak_id = _light_frame_id_by_stem(plan, "light_001")
    strong_id = _light_frame_id_by_stem(plan, "light_002")
    _write_cuda_reference_scout_from_cpu_scout(plan, run, reference_frame_id=weak_id)
    _write_reference_health_master_cache(cache_dir)

    def fake_calibrate_tile(light, bias, dark, flat, light_exposure_s, dark_exposure_s, policy_payload):
        policy = CalibrationPolicy()
        if isinstance(policy_payload, dict):
            for key, value in policy_payload.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
        return calibrate_light(light, bias, dark, flat, light_exposure_s, dark_exposure_s, policy)

    def fake_grid_catalog(
        data,
        threshold,
        grid_cols,
        grid_rows,
        candidates_per_cell,
        max_output_candidates,
        min_separation_px,
    ):
        image = np.asarray(data, dtype=np.float32)
        ys, xs = np.nonzero(image > float(threshold))
        flux = image[ys, xs].astype(np.float32)
        order = np.argsort(-flux, kind="stable")[: int(max_output_candidates)]
        return {
            "count": int(len(xs)),
            "stored_count": int(len(order)),
            "grid_cols": int(grid_cols),
            "grid_rows": int(grid_rows),
            "candidates_per_cell": int(candidates_per_cell),
            "grid_capacity": int(grid_cols) * int(grid_rows) * int(candidates_per_cell),
            "max_output_candidates": int(max_output_candidates),
            "min_separation_px": float(min_separation_px),
            "catalog_sort_mode": "fake_cuda_test",
            "catalog_topk_mode": "fake_cuda_test",
            "x": xs[order].astype(np.float32),
            "y": ys[order].astype(np.float32),
            "flux": flux[order].astype(np.float32),
        }

    monkeypatch.setattr(glass_cuda, "cuda_available", lambda: True)
    monkeypatch.setattr(glass_cuda, "calibrate_tile_f32", fake_calibrate_tile)
    monkeypatch.setattr(glass_cuda, "star_grid_top_nms_candidates_f32", fake_grid_catalog)

    health = build_resident_reference_health(
        plan,
        run,
        min_cpu_star_ratio=0.0,
        max_cpu_rank_fraction=1.0,
        calibrated_min_star_ratio=0.0,
        calibrated_max_rank_fraction=1.0,
        master_cache_dir=cache_dir,
        flat_floor=0.05,
    )

    cuda_calibrated = health["cuda_calibrated_crosscheck"]
    assert health["passed"] is True
    assert health["blocking"] is False
    assert health["summary"]["reference_frame_id"] == weak_id
    assert health["summary"]["calibrated_reference_frame_id"] == strong_id
    assert cuda_calibrated["available"] is True
    assert cuda_calibrated["enforced"] is False
    assert cuda_calibrated["status"] == "failed"
    assert cuda_calibrated["summary"]["reference_frame_id"] == weak_id
    assert cuda_calibrated["summary"]["cuda_calibrated_reference_frame_id"] == strong_id
    assert "selected_reference_cuda_calibrated_star_ratio" in cuda_calibrated["failed_checks"]
    assert "selected_reference_cuda_calibrated_star_ratio" not in health["failed_checks"]


def test_resident_reference_health_calibrated_crosscheck_can_block_when_raw_thresholds_are_loose(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glass_cuda

    monkeypatch.setattr(glass_cuda, "cuda_available", lambda: False)
    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "reference_health_calibrated_fail"
    cache_dir = tmp_path / "resident_master_cache"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    weak_id = _light_frame_id_by_stem(plan, "light_001")
    strong_id = _light_frame_id_by_stem(plan, "light_002")
    _write_cuda_reference_scout_from_cpu_scout(plan, run, reference_frame_id=weak_id)
    _write_reference_health_master_cache(cache_dir)

    health = build_resident_reference_health(
        plan,
        run,
        min_cpu_star_ratio=0.0,
        max_cpu_rank_fraction=1.0,
        calibrated_min_star_ratio=0.75,
        calibrated_max_rank_fraction=0.25,
        master_cache_dir=cache_dir,
        flat_floor=0.05,
    )

    calibrated = health["calibrated_crosscheck"]
    assert health["passed"] is False
    assert health["blocking"] is True
    assert calibrated["available"] is True
    assert calibrated["summary"]["reference_frame_id"] == weak_id
    assert calibrated["summary"]["calibrated_reference_frame_id"] == strong_id
    assert "selected_reference_calibrated_star_ratio" in health["failed_checks"]


def test_cli_resident_run_blocks_bad_cuda_reference_before_compute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "reference_health_cli_fail"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    weak_id = _light_frame_id_by_stem(plan, "light_001")

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})

    def write_bad_scout(run_dir, _args, *, plan_path=None):
        return _write_minimal_cuda_reference_scout(Path(run_dir), reference_frame_id=weak_id)

    def fail_if_memory_admission_starts(*_args, **_kwargs):
        raise AssertionError("resident memory admission should not start after reference health failure")

    def fail_if_resident_compute_starts(*_args, **_kwargs):
        raise AssertionError("resident CUDA compute should not start after reference health failure")

    monkeypatch.setattr("glass.cli._write_resident_reference_scout_if_needed", write_bad_scout)
    monkeypatch.setattr("glass.cli._write_resident_memory_admission", fail_if_memory_admission_starts)
    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fail_if_resident_compute_starts)

    assert main(["run", "--plan", str(plan), "--out", str(run), "--resident-reference-scout-backend", "cuda"]) == 2

    health = read_json(run / "resident_reference_health.json")
    state = read_json(run / "run_state.json")
    timing = read_json(run / "run_timing.json")

    assert health["blocking"] is True
    assert health["summary"]["reference_frame_id"] == weak_id
    assert state["failed_stage"] == "resident_reference_health"
    assert [item["stage"] for item in timing["stages"]] == [
        "resident_reference_scout",
        "resident_reference_health",
    ]
    assert timing["stages"][-1]["status"] == "failed"
    assert not (run / "resident_memory_admission.json").exists()


def test_resident_reference_scout_auto_keeps_cpu_until_cuda_reference_health_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glass_cuda

    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "auto_cpu_scout"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    monkeypatch.setattr(glass_cuda, "cuda_available", lambda: True)

    scout_path = write_resident_reference_scout(plan, run, sample_stride=1, max_frames=0, catalog_backend="auto")
    scout = read_json(scout_path)

    assert scout["catalog_backend_requested"] == "auto"
    assert scout["catalog_backend"] == "cpu"
    assert scout["catalog_backend_resolution"]["cuda_status"] == "available"
    assert scout["catalog_backend_resolution"]["reason"] == (
        "cuda_reference_scout_requires_explicit_backend_until_real_reference_health_passes"
    )


def test_resident_reference_scout_explicit_cuda_backend_reports_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import glass_cuda

    dataset = tmp_path / "dataset"
    _write_two_light_reference_scout_dataset(dataset)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "cuda_unavailable_scout"
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    monkeypatch.setattr(glass_cuda, "cuda_available", lambda: False)

    with pytest.raises(RuntimeError, match="CUDA backend requested but unavailable"):
        write_resident_reference_scout(plan, run, catalog_backend="cuda")


def test_run_defaults_fallback_to_tile_when_cuda_unavailable() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run"])

    resolution = _resolve_execution_defaults(args, {"cuda_available": False}, command="run")

    assert args.backend == "auto"
    assert args.memory_mode == "tile"
    assert resolution["reason"] == "resident_default_fallback_cuda_unavailable"
    assert resolution["effective_memory_mode"] == "tile"


def test_run_defaults_fallback_to_tile_for_partial_stage() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--backend",
            "auto",
            "--until-stage",
            "quality",
        ]
    )

    resolution = _resolve_execution_defaults(args, {"cuda_available": True}, command="run")

    assert args.backend == "auto"
    assert args.memory_mode == "tile"
    assert resolution["reason"] == "resident_default_fallback_unsupported_options"
    assert resolution["resident_default_blocker"] == "until_stage:quality"


def test_run_explicit_resident_requires_cuda() -> None:
    args = _parse_cli(
        [
            "run",
            "--plan",
            "plan.json",
            "--out",
            "run",
            "--memory-mode",
            "resident",
        ]
    )

    with pytest.raises(SystemExit, match="Resident memory mode requested"):
        _resolve_execution_defaults(args, {"cuda_available": False}, command="run")


def test_audit_backend_cpu_keeps_tile_fallback() -> None:
    args = _parse_cli(["audit", "--root", "data", "--out", "run", "--backend", "cpu"])

    resolution = _resolve_execution_defaults(args, {"cuda_available": True}, command="audit")

    assert args.backend == "cpu"
    assert args.memory_mode == "tile"
    assert resolution["reason"] == "resident_default_fallback_non_cuda_backend"
    assert resolution["requested_memory_mode"] == "resident"


def test_cpu_tile_path_keeps_resident_fits_default_unused() -> None:
    args = _parse_cli(["run", "--plan", "plan.json", "--out", "run", "--backend", "cpu"])

    _resolve_execution_defaults(args, {"cuda_available": True}, command="run")
    resolution = _resolve_resident_fits_read_mode_default(args, command="run")

    assert args.backend == "cpu"
    assert args.memory_mode == "tile"
    assert args.resident_fits_read_mode == "astropy"
    assert resolution["source"] == "unused_non_resident"
    assert resolution["effective"] == "astropy"


def test_audit_defaults_fallback_to_tile_for_unsupported_weighting() -> None:
    args = _parse_cli(
        [
            "audit",
            "--root",
            "data",
            "--out",
            "run",
            "--integration-weighting",
            "combined",
        ]
    )

    resolution = _resolve_execution_defaults(args, {"cuda_available": True}, command="audit")

    assert args.backend == "auto"
    assert args.memory_mode == "tile"
    assert resolution["reason"] == "resident_default_fallback_unsupported_options"
    assert resolution["resident_default_blocker"] == "integration_weighting:combined"


def test_cli_scan_plan_report_audit_smoke(small_fits_dataset, tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    report = tmp_path / "report.html"
    audit = tmp_path / "audit"
    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert manifest.exists()
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert plan.exists()
    assert main(["report", "--run", str(tmp_path), "--out", str(report)]) == 0
    assert report.exists()
    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (audit / "manifest.json").exists()
    assert (audit / "processing_plan.json").exists()
    assert (audit / "report.html").exists()
    run_command = (audit / "run_command.txt").read_text(encoding="utf-8")
    assert "glass audit" in run_command
    assert "--backend cpu" in run_command


def test_cli_synthetic_source_dq_manifest_binds_into_plan(tmp_path: Path):
    dataset = tmp_path / "synthetic"
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"

    assert (
        main(
            [
                "synthetic",
                "--out",
                str(dataset),
                "--frames",
                "4",
                "--width",
                "32",
                "--height",
                "24",
                "--source-dq-sidecars",
                "--source-dq-light-index",
                "1",
                "--source-dq-y",
                "5",
                "--source-dq-x",
                "7",
            ]
        )
        == 0
    )
    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert (
        main(
            [
                "plan",
                "--manifest",
                str(manifest),
                "--out",
                str(plan),
                "--source-dq-manifest",
                str(dataset / "source_dq_manifest.json"),
            ]
        )
        == 0
    )

    plan_payload = read_json(plan)
    bound = [frame for frame in plan_payload["frames"] if frame.get("source_dq_mask_path")]
    assert len(bound) == 1
    assert bound[0]["frame_type"] == "light"
    assert Path(bound[0]["source_dq_mask_path"]).exists()
    assert Path(bound[0]["path"]).name == "light_001.fits"


def test_cli_report_surfaces_quality_saturation_summary(tmp_path: Path):
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    run.mkdir()
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "quality_gate_policy": {
                "max_saturation_fraction": 0.005,
                "saturation_level": 5000.0,
            },
            "frame_quality": [
                {
                    "frame_id": "bad_threshold",
                    "saturation_fraction": 36 / 4096,
                    "saturated_pixel_count": 36,
                    "saturation_level": 5000.0,
                    "saturation_source": "threshold",
                    "quality_gate_status": "rejected",
                    "quality_gate_warnings": [
                        "saturation_fraction 0.00879 exceeds max_saturation_fraction=0.005"
                    ],
                },
                {
                    "frame_id": "good_threshold",
                    "saturation_fraction": 0.0,
                    "saturated_pixel_count": 0,
                    "saturation_level": 5000.0,
                    "saturation_source": "threshold",
                    "quality_gate_status": "accepted",
                    "quality_gate_warnings": [],
                },
            ],
            "reference_frame_id": "good_threshold",
        },
    )

    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Quality saturation" in html
    assert "saturated_frame_count" in html
    assert "quality_gate_saturation_rejected_count" in html
    assert "bad_threshold" in html
    assert "threshold" in html


def test_cli_report_surfaces_quality_metric_summary(tmp_path: Path):
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    run.mkdir()
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "frame_quality": [
                {
                    "frame_id": "sharp_high_snr",
                    "star_count": 120,
                    "fwhm_px": 2.1,
                    "eccentricity": 0.31,
                    "background_rms": 18.0,
                    "snr": 55.0,
                    "quality_score": 1000.0,
                    "weight": 1.0,
                    "quality_gate_status": "accepted",
                },
                {
                    "frame_id": "soft_frame",
                    "star_count": 90,
                    "fwhm_px": 5.8,
                    "eccentricity": 0.44,
                    "background_rms": 24.0,
                    "snr": 33.0,
                    "quality_score": 420.0,
                    "weight": 0.42,
                    "quality_gate_status": "accepted",
                },
                {
                    "frame_id": "noisy_low_snr",
                    "star_count": 20,
                    "fwhm_px": 3.2,
                    "eccentricity": 0.72,
                    "background_rms": 88.0,
                    "snr": 7.0,
                    "quality_score": 80.0,
                    "weight": 0.08,
                    "quality_gate_status": "rejected",
                },
            ],
        },
    )

    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Quality metrics" in html
    assert "fwhm_px" in html
    assert "worst_frame_id" in html
    assert "soft_frame" in html
    assert "noisy_low_snr" in html


def test_cli_audit_and_run_write_state_for_registration_admission_block(tmp_path: Path):
    data = tmp_path / "uniform"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    _write_uniform_no_star_dataset(data)

    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu", "--tile-size", "8"]) == 2
    audit_state = read_json(audit / "run_state.json")
    audit_registration = read_json(audit / "registration_results.json")
    audit_timing = read_json(audit / "run_timing.json")

    assert audit_state["failed_stage"] == "registration"
    assert audit_state["current_stage"] == "registration"
    assert any("registration reference admission blocked" in error for error in audit_state["errors"])
    assert audit_registration["reference_admission"]["status"] == "blocked"
    assert not (audit / "integration_results.json").exists()
    timing_by_stage = {item["stage"]: item for item in audit_timing["stages"]}
    assert timing_by_stage["registration"]["status"] == "failed"
    assert main(["resume", "--run", str(audit)]) == 2
    resume_state = read_json(audit / "run_state.json")
    resume_timing = read_json(audit / "run_timing.json")
    assert resume_state["failed_stage"] == "registration"
    assert any("registration reference admission blocked" in error for error in resume_state["errors"])
    resume_timing_by_stage = {item["stage"]: item for item in resume_timing["stages"]}
    assert resume_timing_by_stage["registration"]["status"] == "failed"
    assert resume_timing_by_stage["registration"]["resume_existing_artifact"] is True
    admission_report = tmp_path / "registration_admission_report.html"
    assert main(["report", "--run", str(audit), "--out", str(admission_report)]) == 0
    admission_html = admission_report.read_text(encoding="utf-8")
    assert "Registration admission" in admission_html
    assert "blocked" in admission_html
    assert "quality_reference_admission" in admission_html
    assert "allow_quality_rejected_reference" in admission_html

    assert main(["scan", "--root", str(data), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "integration",
                "--tile-size",
                "8",
            ]
        )
        == 2
    )
    run_state = read_json(run / "run_state.json")
    assert run_state["failed_stage"] == "registration"
    assert any("registration reference admission blocked" in error for error in run_state["errors"])
    assert not (run / "integration_results.json").exists()


def test_cli_audit_resident_cuda_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    audit = tmp_path / "resident_audit"

    assert main(
        [
            "audit",
            "--root",
            str(small_fits_dataset),
            "--out",
            str(audit),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "throughput-v1",
            "--local-normalization",
            "off",
            "--integration-weighting",
            "none",
            "--integration-rejection",
            "none",
            "--resident-registration",
            "off",
            "--resident-registration-max-shift",
            "9",
            "--resident-ncc-sample-stride",
            "2",
            "--resident-ncc-fallback-score-threshold",
            "0.5",
            "--resident-subpixel-radius-steps",
            "3",
            "--resident-subpixel-step",
            "0.4",
            "--resident-star-threshold",
            "12",
            "--resident-star-max-candidates",
            "11",
            "--resident-star-tolerance-px",
            "1.25",
            "--resident-star-grid-cols",
            "2",
            "--resident-star-grid-rows",
            "3",
            "--resident-star-catalog-deterministic",
            "--resident-star-prior",
            "ncc",
            "--resident-star-prior-radius-px",
            "2.5",
            "--resident-star-core-preselect-top-k",
            "4",
        ]
    ) == 0

    state = read_json(audit / "run_state.json")
    timing = read_json(audit / "run_timing.json")
    integration = read_json(audit / "integration_results.json")
    resident = read_json(audit / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert (audit / "manifest.json").exists()
    assert (audit / "processing_plan.json").exists()
    assert (audit / "resident_artifacts.json").exists()
    assert (audit / "report.html").exists()
    assert state["current_stage"] == "report"
    assert "resident_integration" in state["completed_stages"]
    assert timing["memory_mode"] == "resident"
    assert integration["source_stage"] == "resident_calibrated_stack"
    assert resident_registration["max_shift"] == 9
    assert resident_registration["ncc_sample_stride"] == 2
    assert resident_registration["ncc_fallback_score_threshold"] == 0.5
    assert resident_registration["subpixel_radius_steps"] == 3
    assert resident_registration["subpixel_step"] == 0.4
    assert resident_registration["star_threshold"] == 12
    assert resident_registration["star_max_candidates"] == 11
    assert resident_registration["star_tolerance_px"] == 1.25
    assert resident_registration["star_grid_cols"] == 2
    assert resident_registration["star_grid_rows"] == 3
    assert resident_registration["star_catalog_deterministic"] is True
    assert resident_registration["star_prior"] == "ncc"
    assert resident_registration["star_prior_radius_px"] == 2.5
    assert resident_registration["star_core_preselect_top_k"] == 4
    assert io_pipeline["prefetch_frames"] == 12
    assert io_pipeline["prefetch_workers"] == 7
    assert io_pipeline["h2d_mode"] == "pinned_ring"
    assert io_pipeline["calibration_batch_requested_frames"] == 8
    assert io_pipeline["calibration_batch_requested_streams"] == 4
    assert io_pipeline["calibration_wave_requested_frames"] == 2
    assert io_pipeline["calibration_release_mode_requested"] == "callback_queue"
    assert io_pipeline["calibration_release_mode_effective"] == "callback_queue"


def test_cli_resident_run_blocks_explicit_low_vram_budget(
    small_fits_dataset,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_low_budget"
    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})

    def fail_if_resident_compute_starts(*_args, **_kwargs):
        raise AssertionError("resident CUDA compute should not start after memory admission failure")

    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fail_if_resident_compute_starts)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--resident-reference-fallback",
                "allow-first-light",
                "--vram-budget-gb",
                "0.000001",
            ]
        )
        == 2
    )
    admission = read_json(run / "resident_memory_admission.json")
    state = read_json(run / "run_state.json")
    timing = read_json(run / "run_timing.json")

    assert admission["artifact_type"] == "resident_memory_admission"
    assert admission["blocking"] is True
    assert admission["passed"] is False
    assert admission["reason"] == "estimated_peak_exceeds_explicit_vram_budget"
    assert state["failed_stage"] == "resident_memory_admission"
    assert state["artifacts"][0]["stage"] == "resident_memory_admission"
    assert [item["stage"] for item in timing["stages"]] == [
        "resident_reference_admission",
        "resident_memory_admission",
    ]
    assert timing["stages"][0]["status"] == "ok"
    assert timing["stages"][1]["status"] == "failed"


def test_cli_resident_run_passes_reduced_chunk_capacity_from_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    frames = [
        {
            "id": f"L{index:03d}",
            "path": str(tmp_path / f"light_{index:03d}.fits"),
            "frame_type": "light",
            "filter": "H",
            "height": 72,
            "width": 80,
        }
        for index in range(10)
    ]
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_reduced_budget"
    write_json(
        plan,
        {
            "frames": frames,
            "light_plans": [
                {
                    "filter": "H",
                    "frames": [str(frame["id"]) for frame in frames],
                    "calibration_status": "ready",
                }
            ],
            "executable": True,
        },
    )
    full = read_json(plan)
    from glass.engine.resident_cuda import build_resident_memory_admission

    capacity4 = next(
        item
        for item in build_resident_memory_admission(
            full,
            resident_registration="similarity_cuda_triangle",
            resident_warp_batch_dispatch="chunked",
            vram_budget_gb=1.0,
        )["peak_group"]["capacity_options"]
        if item["chunked_warp_capacity_frames"] == 4
    )
    captured: dict[str, object] = {}

    def fake_resident_compute(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        out_dir = Path(kwargs.get("out_dir") or args[1])
        _write_resident_registration_quality(out_dir, frame_count=20, accepted_count=20)
        return initialize_run(out_dir)

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})
    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fake_resident_compute)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--resident-registration",
                "similarity_cuda_triangle",
                "--resident-warp-batch-dispatch",
                "chunked",
                "--vram-budget-gb",
                str(float(capacity4["estimated_peak_bytes"] + 1024) / (1024**3)),
            ]
        )
        == 0
    )

    admission = read_json(run / "resident_memory_admission.json")
    assert admission["blocking"] is False
    assert admission["recommended_action"] == "resident_reduced_chunk_capacity"
    assert admission["selected_chunk_capacity_frames"] == 4
    assert admission["selected_warp_batch_dispatch"] == "chunked"
    assert captured["kwargs"]["resident_warp_batch_dispatch"] == "chunked"
    assert captured["kwargs"]["resident_warp_chunk_capacity_frames"] == 4


def test_cli_resident_run_passes_preset_chunk_capacity_from_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    frames = [
        {
            "id": f"L{index:03d}",
            "path": str(tmp_path / f"light_{index:03d}.fits"),
            "frame_type": "light",
            "filter": "H",
            "height": 72,
            "width": 80,
        }
        for index in range(40)
    ]
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_preset_chunk"
    write_json(
        plan,
        {
            "frames": frames,
            "light_plans": [
                {
                    "filter": "H",
                    "frames": [str(frame["id"]) for frame in frames],
                    "calibration_status": "ready",
                }
            ],
            "executable": True,
        },
    )
    captured: dict[str, object] = {}

    def fake_resident_compute(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        out_dir = Path(kwargs.get("out_dir") or args[1])
        _write_resident_registration_quality(out_dir, frame_count=40, accepted_count=40)
        return initialize_run(out_dir)

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})
    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fake_resident_compute)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--resident-runtime-preset",
                "throughput-v3-io",
                "--resident-registration",
                "similarity_cuda_triangle",
                "--resident-warp-batch-dispatch",
                "chunked",
                "--vram-budget-gb",
                "1.0",
            ]
        )
        == 0
    )

    admission = read_json(run / "resident_memory_admission.json")
    assert admission["blocking"] is False
    assert admission["recommended_action"] == "resident_full_frame"
    assert admission["selected_chunk_capacity_frames"] == 32
    assert admission["selected_warp_batch_dispatch"] == "chunked"
    assert captured["kwargs"]["resident_warp_batch_dispatch"] == "chunked"
    assert captured["kwargs"]["resident_warp_chunk_capacity_frames"] == 32


def test_cli_resident_run_passes_explicit_chunk_capacity_from_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    frames = [
        {
            "id": f"L{index:03d}",
            "path": str(tmp_path / f"light_{index:03d}.fits"),
            "frame_type": "light",
            "filter": "H",
            "height": 72,
            "width": 80,
        }
        for index in range(20)
    ]
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_explicit_chunk"
    write_json(
        plan,
        {
            "frames": frames,
            "light_plans": [
                {
                    "filter": "H",
                    "frames": [str(frame["id"]) for frame in frames],
                    "calibration_status": "ready",
                }
            ],
            "executable": True,
        },
    )
    captured: dict[str, object] = {}

    def fake_resident_compute(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        out_dir = Path(kwargs.get("out_dir") or args[1])
        _write_resident_registration_quality(out_dir, frame_count=20, accepted_count=20)
        return initialize_run(out_dir)

    monkeypatch.setattr("glass.cli.capability_report", lambda: {"cuda_available": True})
    monkeypatch.setattr("glass.cli.run_resident_calibration_integration", fake_resident_compute)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--resident-registration",
                "similarity_cuda_triangle",
                "--resident-warp-batch-dispatch",
                "chunked",
                "--resident-warp-chunk-capacity-frames",
                "16",
                "--vram-budget-gb",
                "1.0",
            ]
        )
        == 0
    )

    admission = read_json(run / "resident_memory_admission.json")
    assert admission["blocking"] is False
    assert admission["recommended_action"] == "resident_full_frame"
    assert admission["selected_chunk_capacity_frames"] == 16
    assert admission["selected_chunk_capacity_source"] == "explicit"
    assert captured["kwargs"]["resident_warp_batch_dispatch"] == "chunked"
    assert captured["kwargs"]["resident_warp_chunk_capacity_frames"] == 16


def test_cli_help_commands():
    for command in [
        "doctor",
        "phase2-status",
        "phase2-status-compare",
        "scan",
        "plan",
        "subset",
        "run",
        "resume",
        "audit",
        "compare",
        "compare-outliers",
        "compare-tile-pack",
        "compare-tile-attribution",
        "compare-tile-replay",
        "compare-tile-integration",
        "residual-tile-candidates",
        "frame-weight-proposal",
        "frame-weight-proposal-audit",
        "compare-frame-family",
        "resident-tile-capture",
        "resident-tile-contribution",
        "tile-local-policy-proposal",
        "tile-local-frame-family-search",
        "tile-local-residual-source-audit",
        "tile-local-rejection-registration-audit",
        "tile-local-rejection-registration-plan",
        "candidate-comparison",
        "candidate-comparison-sweep",
        "candidate-runtime-sweep-plan",
        "candidate-runtime-sweep-execute",
        "resident-ab-matrix-plan",
        "resident-ab-matrix-execute",
        "tile-local-policy-replay",
        "tile-local-policy-subset",
        "tile-local-apply-experiment",
        "tile-local-apply-verify",
        "tile-local-policy-decision",
        "tile-local-policy-sweep",
        "tile-local-sweep-plan",
        "speedup-summary",
        "acceptance-audit",
        "release-promotion-decision",
        "default-promotion-manifest",
        "windows-release-matrix",
        "stack-engine-publication-audit",
        "windows-package-smoke",
        "resident-determinism",
        "resident-registration-audit",
        "resident-registration-compare",
        "resident-calibration-artifacts",
        "resident-calibration-contract",
        "resident-result-contract",
        "resident-runtime-compare",
        "resident-fits-auto-regression",
        "resident-winsorized-benchmark",
        "resident-winsorized-benchmark-audit",
        "resident-winsorized-sweep",
        "resident-winsorized-sweep-audit",
        "resident-runtime-repeat-execute",
        "resident-runtime-repeat-plan",
        "resident-runtime-repeat-preflight",
        "stack-engine-contract",
        "pipeline-contract",
        "local-norm-contract",
        "warp-quality-contract",
        "guardrails",
        "blackbox-package",
        "blackbox-finalize",
        "blackbox-history",
        "synthetic",
    ]:
        try:
            main([command, "--help"])
        except SystemExit as exc:
            assert exc.code == 0


def test_cli_guardrails_generates_contracts_and_report(small_fits_dataset, tmp_path: Path):
    run = tmp_path / "run"
    out_dir = tmp_path / "guardrails"
    resident_calibration = tmp_path / "resident_calibration_contract.json"
    resident_result = tmp_path / "resident_result_contract.json"
    write_json(resident_calibration, {"artifact_type": "resident_cuda_calibration_contract", "passed": True, "outputs": []})
    write_json(resident_result, {"artifact_type": "resident_cuda_result_contract", "passed": True, "outputs": []})
    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0

    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(out_dir),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--resident-calibration-contract-json",
                str(resident_calibration),
                "--resident-result-contract-json",
                str(resident_result),
                "--require-stack-default-ready",
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "8",
            ]
        )
        == 0
    )

    summary = read_json(out_dir / "guardrails_summary.json")
    bundle = read_json(out_dir / "acceptance_contract_bundle.json")
    stack_contract = read_json(out_dir / "stack_engine_contract.json")
    pipeline_contract = read_json(out_dir / "pipeline_contract.json")
    local_norm_contract = read_json(out_dir / "local_norm_contract.json")
    registration_quality = read_json(out_dir / "registration_quality_contract.json")
    warp_quality = read_json(out_dir / "warp_quality_contract.json")
    assert summary["passed"] is True
    assert summary["pixel_verify"] is True
    assert summary["require_stack_default_ready"] is True
    assert summary["require_local_normalization_enabled"] is False
    assert summary["local_norm_contract_required"] is True
    assert summary["local_norm_contract_attached"] is True
    assert summary["local_norm_contract_status"] == "passed"
    assert summary["local_norm_contract_enabled"] is False
    assert summary["registration_quality_required"] is False
    assert summary["registration_quality_status"] == "passed"
    assert summary["warp_quality_required"] is False
    assert summary["warp_quality_status"] == "passed"
    assert summary["resident_calibration_contract_json"] == str(resident_calibration)
    assert summary["resident_result_contract_json"] == str(resident_result)
    assert summary["artifacts"]["resident_calibration_contract"] == str(resident_calibration)
    assert summary["artifacts"]["resident_result_contract"] == str(resident_result)
    assert summary["artifacts"]["local_norm_contract"] == str(out_dir / "local_norm_contract.json")
    assert summary["artifacts"]["local_norm_contract_markdown"] == str(out_dir / "local_norm_contract.md")
    assert summary["artifacts"]["registration_quality_contract"] == str(out_dir / "registration_quality_contract.json")
    assert summary["artifacts"]["warp_quality_contract"] == str(out_dir / "warp_quality_contract.json")
    assert summary["artifacts"]["acceptance_contract_bundle"] == str(out_dir / "acceptance_contract_bundle.json")
    assert bundle["artifact_type"] == "glass_acceptance_contract_bundle"
    assert bundle["passed"] is True
    assert bundle["purpose"] == "acceptance_audit_contract_inputs"
    assert bundle["require_local_normalization_enabled"] is False
    assert bundle["local_norm_contract_required"] is True
    assert bundle["local_norm_contract_attached"] is True
    assert bundle["local_norm_contract_status"] == "passed"
    assert bundle["local_norm_contract_enabled"] is False
    assert bundle["registration_quality_required"] is False
    assert bundle["registration_quality_status"] == "passed"
    assert bundle["warp_quality_required"] is False
    assert bundle["warp_quality_status"] == "passed"
    assert bundle["resident_calibration_contract_json"] == str(resident_calibration)
    assert bundle["resident_result_contract_json"] == str(resident_result)
    assert bundle["artifacts"]["resident_calibration_contract"] == str(resident_calibration)
    assert bundle["artifacts"]["resident_result_contract"] == str(resident_result)
    assert bundle["artifacts"]["local_norm_contract"] == str(out_dir / "local_norm_contract.json")
    assert bundle["artifacts"]["local_norm_contract_markdown"] == str(out_dir / "local_norm_contract.md")
    assert bundle["artifacts"]["registration_quality_contract"] == str(out_dir / "registration_quality_contract.json")
    assert bundle["artifacts"]["warp_quality_contract"] == str(out_dir / "warp_quality_contract.json")
    assert bundle["acceptance_audit_arguments"] == [
        "--pipeline-contract-json",
        str(out_dir / "pipeline_contract.json"),
        "--stack-engine-contract-json",
        str(out_dir / "stack_engine_contract.json"),
    ]
    assert bundle["acceptance_audit_argument_map"] == {
        "pipeline_contract_json": str(out_dir / "pipeline_contract.json"),
        "stack_engine_contract_json": str(out_dir / "stack_engine_contract.json"),
    }
    assert bundle["artifacts"]["guardrails_summary"] == str(out_dir / "guardrails_summary.json")
    assert summary["stack_default_promotion"]["ready"] is True
    assert summary["checks"][2]["name"] == "stack_default_promotion"
    assert summary["checks"][2]["ready"] is True
    assert summary["checks"][3]["name"] == "local_norm_contract"
    assert summary["checks"][3]["passed"] is True
    assert summary["checks"][4]["name"] == "local_norm_enabled_requirement"
    assert summary["checks"][4]["passed"] is True
    assert summary["checks"][4]["required"] is False
    assert {item["name"] for item in summary["checks"]} >= {"registration_quality", "warp_quality"}
    assert stack_contract["passed"] is True
    assert stack_contract["default_promotion"]["ready"] is True
    assert stack_contract["pipeline_contract_attached"] is True
    assert stack_contract["pipeline_contract_source"] == "provided"
    assert stack_contract["default_promotion"]["pipeline_contract_dq_ledger_required"] is False
    assert pipeline_contract["passed"] is True
    pipeline_checks = {item["name"]: item for item in pipeline_contract["checks"]}
    assert pipeline_checks["local_normalization_continuous_contract_audit"]["passed"] is True
    assert pipeline_contract["artifacts"]["local_norm_contract"]["attached"] is True
    assert pipeline_contract["artifacts"]["local_norm_contract"]["passed"] is True
    assert local_norm_contract["artifact_type"] == "local_norm_contract"
    assert local_norm_contract["passed"] is True
    assert registration_quality["artifact_type"] == "registration_quality_contract"
    assert registration_quality["passed"] is True
    assert warp_quality["artifact_type"] == "warp_quality_contract"
    assert warp_quality["passed"] is True
    assert warp_quality["summary"]["output_count"] >= 1
    assert (out_dir / "stack_engine_contract.md").exists()
    assert (out_dir / "pipeline_contract.md").exists()
    assert (out_dir / "local_norm_contract.md").exists()
    assert (out_dir / "registration_quality_contract.md").exists()
    assert (out_dir / "warp_quality_contract.md").exists()
    assert (out_dir / "report.html").exists()
    html = (out_dir / "report.html").read_text(encoding="utf-8")
    assert "StackEngine contract audit" in html
    assert "Pipeline contract audit" in html
    assert "pixel_verification" in html
    assert "calibration_artifact" in html
    assert "stats_ok" in html
    assert "science_ok" in html
    assert "dq_summary_has_valid" in html
    assert "Local normalization contract" in html
    assert "local_norm_contract.json" in html
    assert "disabled_passthrough" in html
    assert "Registration quality contract" in html
    assert "registration_quality_contract.json" in html
    assert "Warp quality contract" in html
    assert "warp_quality_contract.json" in html


def test_cli_guardrails_require_enabled_local_normalization(small_fits_dataset, tmp_path: Path):
    disabled_run = tmp_path / "disabled_run"
    disabled_out = tmp_path / "disabled_guardrails"
    enabled_run = tmp_path / "enabled_run"
    enabled_out = tmp_path / "enabled_guardrails"

    assert (
        main(["audit", "--root", str(small_fits_dataset), "--out", str(disabled_run), "--backend", "cpu", "--tile-size", "8"])
        == 0
    )
    assert (
        main(
            [
                "guardrails",
                "--run",
                str(disabled_run),
                "--out-dir",
                str(disabled_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--require-local-normalization-enabled",
            ]
        )
        == 2
    )
    disabled_summary = read_json(disabled_out / "guardrails_summary.json")
    disabled_checks = {item["name"]: item for item in disabled_summary["checks"]}
    assert disabled_summary["passed"] is False
    assert disabled_summary["require_local_normalization_enabled"] is True
    assert disabled_summary["local_norm_contract_enabled"] is False
    assert disabled_checks["local_norm_enabled_requirement"]["passed"] is False
    assert disabled_checks["local_norm_enabled_requirement"]["status"] == "missing_or_disabled"

    assert (
        main(
            [
                "audit",
                "--root",
                str(small_fits_dataset),
                "--out",
                str(enabled_run),
                "--backend",
                "cpu",
                "--tile-size",
                "8",
                "--local-normalization",
                "on",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "guardrails",
                "--run",
                str(enabled_run),
                "--out-dir",
                str(enabled_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--require-local-normalization-enabled",
            ]
        )
        == 0
    )
    enabled_summary = read_json(enabled_out / "guardrails_summary.json")
    enabled_bundle = read_json(enabled_out / "acceptance_contract_bundle.json")
    enabled_contract = read_json(enabled_out / "local_norm_contract.json")
    enabled_checks = {item["name"]: item for item in enabled_summary["checks"]}
    html = (enabled_out / "report.html").read_text(encoding="utf-8")
    assert enabled_summary["passed"] is True
    assert enabled_summary["require_local_normalization_enabled"] is True
    assert enabled_summary["local_norm_contract_enabled"] is True
    assert enabled_bundle["require_local_normalization_enabled"] is True
    assert enabled_bundle["local_norm_contract_enabled"] is True
    assert enabled_checks["local_norm_enabled_requirement"]["passed"] is True
    assert enabled_contract["enabled"] is True
    assert enabled_contract["model"] == "continuous_grid_mean_std_v1"
    assert enabled_contract["coefficient_field_model"] == "bilinear_tile_center_v1"
    assert "continuous_grid_mean_std_v1" in html
    assert "bilinear_tile_center_v1" in html


def test_cli_guardrails_local_norm_residual_thresholds(small_fits_dataset, tmp_path: Path):
    run = tmp_path / "enabled_run"
    passing_out = tmp_path / "passing_guardrails"
    failing_out = tmp_path / "failing_guardrails"

    assert (
        main(
            [
                "audit",
                "--root",
                str(small_fits_dataset),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--tile-size",
                "8",
                "--local-normalization",
                "on",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(passing_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--require-local-normalization-enabled",
                "--max-local-normalization-rms",
                "100",
                "--max-local-normalization-max-abs",
                "100",
            ]
        )
        == 0
    )
    passing_summary = read_json(passing_out / "guardrails_summary.json")
    passing_checks = {item["name"]: item for item in passing_summary["checks"]}
    assert passing_summary["passed"] is True
    assert passing_summary["local_norm_residual_quality"]["output_count"] > 0
    assert passing_checks["local_norm_residual_quality"]["passed"] is True
    assert passing_checks["local_norm_residual_quality"]["required"] is True

    local_norm = read_json(run / "local_norm_results.json")
    for item in local_norm["local_norm_results"]:
        item["residual_summary"] = {
            "valid_pixels": 4,
            "mean": 0.0,
            "rms": 0.5,
            "max_abs": 2.0,
        }
    write_json(run / "local_norm_results.json", local_norm)

    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(failing_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--require-local-normalization-enabled",
                "--max-local-normalization-rms",
                "0.1",
                "--max-local-normalization-max-abs",
                "1.0",
            ]
        )
        == 2
    )
    failing_summary = read_json(failing_out / "guardrails_summary.json")
    failing_bundle = read_json(failing_out / "acceptance_contract_bundle.json")
    failing_checks = {item["name"]: item for item in failing_summary["checks"]}
    assert failing_summary["passed"] is False
    assert failing_bundle["passed"] is False
    assert failing_checks["local_norm_residual_quality"]["passed"] is False
    assert failing_checks["local_norm_residual_quality"]["max_rms"] == 0.5
    assert failing_checks["local_norm_residual_quality"]["max_abs"] == 2.0
    assert failing_checks["local_norm_residual_quality"]["status"] == "threshold_failed_or_missing"


def test_cli_guardrails_registration_quality_thresholds(small_fits_dataset, tmp_path: Path):
    run = tmp_path / "run"
    passing_out = tmp_path / "passing_guardrails"
    failing_out = tmp_path / "failing_guardrails"

    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(passing_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--max-registration-rms-px",
                "0.1",
                "--min-registration-inliers",
                "0",
            ]
        )
        == 0
    )
    passing_summary = read_json(passing_out / "guardrails_summary.json")
    passing_contract = read_json(passing_out / "registration_quality_contract.json")
    passing_checks = {item["name"]: item for item in passing_summary["checks"]}
    html = (passing_out / "report.html").read_text(encoding="utf-8")
    assert passing_summary["passed"] is True
    assert passing_summary["registration_quality_required"] is True
    assert passing_checks["registration_quality"]["passed"] is True
    assert passing_contract["required"] is True
    assert passing_contract["summary"]["accepted_count"] >= 1
    assert "Registration quality contract" in html
    assert "registration_quality_contract.json" in html

    registration = read_json(run / "registration_results.json")
    registration["registration_results"].append(
        {
            "frame_id": "F_REJECTED",
            "status": "quality_rejected",
            "inliers": 0,
            "matched_stars": 0,
            "rms_px": None,
            "reference_frame_id": registration.get("reference_frame_id"),
            "transform_model": "translation",
            "registration_validation": {"accepted": False, "rms_px": None, "inliers": 0},
            "warnings": ["fixture rejected row"],
        }
    )
    write_json(run / "registration_results.json", registration)

    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(failing_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--max-registration-rms-px",
                "0.1",
                "--min-registration-inliers",
                "1",
                "--require-registration-all-accepted",
            ]
        )
        == 2
    )
    failing_summary = read_json(failing_out / "guardrails_summary.json")
    failing_bundle = read_json(failing_out / "acceptance_contract_bundle.json")
    failing_contract = read_json(failing_out / "registration_quality_contract.json")
    failing_checks = {item["name"]: item for item in failing_summary["checks"]}
    contract_checks = {item["name"]: item for item in failing_contract["checks"]}
    assert failing_summary["passed"] is False
    assert failing_bundle["passed"] is False
    assert failing_checks["registration_quality"]["passed"] is False
    assert contract_checks["accepted_registration_inliers_meet_threshold"]["passed"] is True
    assert contract_checks["all_registration_outputs_accepted"]["passed"] is False
    assert failing_contract["summary"]["failed_count"] >= 1


def test_cli_guardrails_warp_quality_thresholds(small_fits_dataset, tmp_path: Path):
    run = tmp_path / "run"
    passing_out = tmp_path / "passing_guardrails"
    failing_out = tmp_path / "failing_guardrails"

    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(passing_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--min-warp-valid-fraction",
                "1.0",
                "--max-warp-skipped-frames",
                "2",
                "--require-warp-artifacts",
                "--require-warp-all-registered",
                "--warp-pixel-verify",
                "--warp-pixel-verify-tile-size",
                "8",
                "--warp-science-residual-verify",
                "--max-warp-science-rms",
                "0.0",
                "--max-warp-science-max-abs",
                "0.0",
                "--warp-science-residual-tile-size",
                "8",
            ]
        )
        == 0
    )
    passing_summary = read_json(passing_out / "guardrails_summary.json")
    passing_contract = read_json(passing_out / "warp_quality_contract.json")
    passing_checks = {item["name"]: item for item in passing_summary["checks"]}
    html = (passing_out / "report.html").read_text(encoding="utf-8")
    assert passing_summary["passed"] is True
    assert passing_summary["warp_quality_required"] is True
    assert passing_checks["warp_quality"]["passed"] is True
    assert passing_contract["required"] is True
    assert passing_contract["summary"]["output_count"] >= 1
    assert passing_contract["summary"]["min_valid_fraction"] == 1.0
    assert passing_contract["summary"]["pixel_verified_output_count"] >= 1
    assert passing_contract["summary"]["pixel_failed_output_count"] == 0
    assert passing_contract["summary"]["science_residual_verified_output_count"] >= 1
    assert passing_contract["summary"]["science_residual_failed_output_count"] == 0
    assert "Warp quality contract" in html
    assert "warp_quality_contract.json" in html

    warp_results = read_json(run / "warp_results.json")
    warp_results["warp_results"][0]["valid_pixels"] = 0
    write_json(run / "warp_results.json", warp_results)

    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(failing_out),
                "--expected-integration-engine",
                "stack_engine_cpu",
                "--min-warp-valid-fraction",
                "1.0",
                "--max-warp-skipped-frames",
                "99",
                "--require-warp-artifacts",
                "--require-warp-all-registered",
                "--warp-pixel-verify",
                "--warp-pixel-verify-tile-size",
                "8",
                "--warp-science-residual-verify",
                "--max-warp-science-rms",
                "0.0",
                "--max-warp-science-max-abs",
                "0.0",
                "--warp-science-residual-tile-size",
                "8",
            ]
        )
        == 2
    )
    failing_summary = read_json(failing_out / "guardrails_summary.json")
    failing_bundle = read_json(failing_out / "acceptance_contract_bundle.json")
    failing_contract = read_json(failing_out / "warp_quality_contract.json")
    failing_checks = {item["name"]: item for item in failing_summary["checks"]}
    assert failing_summary["passed"] is False
    assert failing_bundle["passed"] is False
    assert failing_checks["warp_quality"]["passed"] is False
    assert "warp_valid_fraction_meets_threshold" in failing_contract["failed_checks"]
    assert "warp_pixel_verification_passed" in failing_contract["failed_checks"]


def test_cli_warp_quality_contract_command(small_fits_dataset, tmp_path: Path):
    run = tmp_path / "run"
    out = tmp_path / "warp_quality_contract.json"
    markdown = tmp_path / "warp_quality_contract.md"
    failing_out = tmp_path / "warp_quality_contract_failing.json"

    assert main(["audit", "--root", str(small_fits_dataset), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (
        main(
            [
                "warp-quality-contract",
                "--run",
                str(run),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--min-valid-fraction",
                "1.0",
                "--max-skipped-frames",
                "99",
                "--require-artifacts",
                "--require-all-registered",
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "8",
                "--science-residual-verify",
                "--max-science-rms",
                "0.0",
                "--max-science-max-abs",
                "0.0",
                "--science-residual-tile-size",
                "8",
                "--fail-on-failed",
            ]
        )
        == 0
    )
    contract = read_json(out)
    assert contract["artifact_type"] == "warp_quality_contract"
    assert contract["passed"] is True
    assert contract["summary"]["pixel_verified_output_count"] >= 1
    assert contract["summary"]["science_residual_verified_output_count"] >= 1
    assert markdown.exists()
    assert "Warp Quality Contract" in markdown.read_text(encoding="utf-8")

    warp_results = read_json(run / "warp_results.json")
    warp_results["warp_results"][0]["valid_pixels"] = 0
    write_json(run / "warp_results.json", warp_results)
    assert (
        main(
            [
                "warp-quality-contract",
                "--run",
                str(run),
                "--out",
                str(failing_out),
                "--min-valid-fraction",
                "1.0",
                "--pixel-verify",
                "--pixel-verify-tile-size",
                "8",
                "--fail-on-failed",
            ]
        )
        == 2
    )
    failing = read_json(failing_out)
    assert failing["passed"] is False
    assert "warp_valid_fraction_meets_threshold" in failing["failed_checks"]
    assert "warp_pixel_verification_passed" in failing["failed_checks"]


def test_cli_guardrails_auto_discovers_run_resident_result_contract(tmp_path: Path):
    run = tmp_path / "run"
    out_dir = tmp_path / "guardrails"
    integration = run / "integration"
    integration.mkdir(parents=True)
    for name, data in {
        "master_H.fits": np.ones((2, 2), dtype=np.float32),
        "weight_H.fits": np.ones((2, 2), dtype=np.float32),
        "coverage_H.fits": np.ones((2, 2), dtype=np.float32),
        "dq_H.fits": np.array([[0, 0], [0, int(DQFlag.NO_DATA)]], dtype=np.float32),
    }.items():
        write_fits_data(integration / name, data)
    write_json(
        run / "integration_results.json",
        {
            "rejection": "none",
            "outputs": [
                {
                    "filter": "H",
                    "backend": "cuda_resident_stack",
                    "memory_mode": "resident",
                    "frame_count": 3,
                    "master_path": str(integration / "master_H.fits"),
                    "weight_map_path": str(integration / "weight_H.fits"),
                    "coverage_map_path": str(integration / "coverage_H.fits"),
                    "dq_map_path": str(integration / "dq_H.fits"),
                    "dq_summary": {"valid": 3, "no_data": 1, "warp_edge": 0},
                    "dq_coverage_provenance": {
                        "available": True,
                        "active_frame_count": 3,
                        "geometric_frame_count_matches_active": True,
                        "source_terms": ["post_rejection_coverage", "geometric_warp_coverage"],
                    },
                    "dq_provenance_summary": {
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 3,
                        "source_terms": ["post_rejection_coverage", "geometric_warp_coverage"],
                        "output_dq_summary": {"valid": 3, "no_data": 1, "warp_edge": 0},
                    },
                    "geometric_warp_coverage": {
                        "available": True,
                        "frame_count": 3,
                        "frame_count_matches_active": True,
                    },
                    "output_map_policy": {
                        "available": ["master", "weight", "coverage", "dq"],
                        "written": ["master", "weight", "coverage", "dq"],
                        "skipped": ["low_rejection", "high_rejection"],
                    },
                }
            ],
        },
    )
    write_json(
        run / "resident_result_contract.json",
        {
            "artifact_type": "resident_cuda_result_contract",
            "passed": True,
            "outputs": [
                {
                    "index": 0,
                    "filter": "H",
                    "passed": True,
                    "status": "passed",
                    "contract_type": "resident_cuda_result_contract",
                    "active_frame_count": 3,
                    "frame_count": 3,
                    "checks": [
                        {"name": "resident_identity", "passed": True},
                        {"name": "required_maps_exist", "passed": True},
                    ],
                }
            ],
        },
    )
    write_json(
        run / "resident_frame_masks.json",
        {
            "schema_version": 1,
            "artifact": "resident_frame_mask_contract",
            "backend": "cuda_resident_stack",
            "source_stage": "resident_calibrated_stack",
            "summary": {
                "group_count": 1,
                "frame_count": 3,
                "active_frame_count": 3,
                "masked_frame_count": 0,
                "unknown_zero_weight_frame_count": 0,
                "active_frame_ids": ["F1", "F2", "F3"],
                "masked_frame_ids": [],
                "unknown_zero_weight_frame_ids": [],
                "mask_category_counts": {},
                "status_counts": {"active": 3},
                "passed": True,
            },
            "groups": [
                {
                    "schema_version": 1,
                    "artifact": "resident_frame_mask_contract_group",
                    "filter": "H",
                    "registration_mode": "similarity_cuda_triangle",
                    "integration_dispatch": "stack",
                    "summary": {
                        "frame_count": 3,
                        "active_frame_count": 3,
                        "masked_frame_count": 0,
                        "unknown_zero_weight_frame_count": 0,
                        "active_frame_ids": ["F1", "F2", "F3"],
                        "masked_frame_ids": [],
                        "unknown_zero_weight_frame_ids": [],
                        "mask_category_counts": {},
                        "status_counts": {"active": 3},
                        "passed": True,
                    },
                    "rows": [
                        {
                            "frame_id": frame_id,
                            "filter": "H",
                            "integration_weight": 1.0,
                            "mask_status": "active",
                            "auditable": True,
                            "mask_categories": [],
                            "mask_reasons": [],
                            "observed_zero_weight_statuses": [],
                            "registration_status": "ok",
                            "registration_quality_status": "accepted",
                            "registration_quality_final_status": "accepted",
                            "weighting_status": "unit",
                            "local_norm_status": "ok",
                        }
                        for frame_id in ["F1", "F2", "F3"]
                    ],
                }
            ],
        },
    )
    write_json(
        run / "resident_registration_quality.json",
        {
            "schema_version": 1,
            "source_stage": "resident_calibrated_stack",
            "registration_mode": "similarity_cuda_triangle",
            "requested_action": "auto",
            "min_inliers": 4,
            "max_rms_px": None,
            "summary": {
                "frame_count": 3,
                "decision_status_counts": {"reference": 1, "accepted": 2},
                "final_status_counts": {"reference": 1, "ok": 2},
                "action_counts": {"none": 3},
                "rejected_frame_ids": [],
                "warning_frame_ids": [],
            },
            "decisions": [
                {
                    "schema_version": 1,
                    "frame_id": frame_id,
                    "registration_mode": "similarity_cuda_triangle",
                    "requested_action": "auto",
                    "effective_action": "exclude",
                    "original_status": "reference" if index == 0 else "ok",
                    "final_status": "reference" if index == 0 else "ok",
                    "decision_status": "reference" if index == 0 else "accepted",
                    "action_applied": "none",
                    "accepted": True,
                    "matched_stars": 0 if index == 0 else 8,
                    "inliers": 0 if index == 0 else 8,
                    "rms_px": 0.0 if index == 0 else 0.5,
                    "thresholds": {
                        "min_inliers": 4,
                        "max_rms_px": None,
                        "max_rms_enabled": False,
                        "catalog_capacity_limited": False,
                    },
                    "diagnostics": {},
                    "reasons": [],
                }
                for index, frame_id in enumerate(["F1", "F2", "F3"])
            ],
        },
    )
    closure_checks = [
        "frame_mask_contract_passed",
        "frame_mask_active_matches_output_link",
        "active_frame_count_matches_provenance",
        "geometric_coverage_count_matches_active",
        "post_rejection_coverage_present",
        "geometric_coverage_present",
        "dq_summary_matches_provenance",
        "active_not_greater_than_input_frame_count",
    ]
    write_json(
        run / "resident_dq_pixel_closure.json",
        {
            "schema_version": 1,
            "artifact": "resident_dq_pixel_closure",
            "backend": "cuda_resident_stack",
            "source_stage": "resident_calibrated_stack",
            "summary": {
                "group_count": 1,
                "passed_group_count": 1,
                "failed_group_count": 0,
                "failed_groups": [],
                "passed": True,
                "check_counts": {name: 1 for name in closure_checks},
                "failed_check_counts": {},
            },
            "groups": [
                {
                    "schema_version": 1,
                    "artifact": "resident_dq_pixel_closure_group",
                    "filter": "H",
                    "status": "passed",
                    "passed": True,
                    "frame_mask_active_frame_count": 3,
                    "frame_mask_masked_frame_count": 0,
                    "geometric_warp_coverage_frame_count": 3,
                    "provenance_active_frame_count": 3,
                    "rejection": "none",
                    "source_terms": ["post_rejection_coverage", "geometric_warp_coverage"],
                    "sample_accounting_closure": {"status": "missing", "passed": True},
                    "checks": [{"name": name, "passed": True, "details": {}} for name in closure_checks],
                }
            ],
        },
    )

    assert (
        main(
            [
                "guardrails",
                "--run",
                str(run),
                "--out-dir",
                str(out_dir),
                "--stack-scope",
                "integration",
                "--expected-integration-engine",
                "cuda_resident_stack",
            ]
        )
        == 0
    )

    summary = read_json(out_dir / "guardrails_summary.json")
    bundle = read_json(out_dir / "acceptance_contract_bundle.json")
    stack_contract = read_json(out_dir / "stack_engine_contract.json")
    assert summary["passed"] is True
    assert summary["resident_result_contract_json"] == str(run / "resident_result_contract.json")
    assert summary["resident_result_contract_source"] == "run_default"
    assert summary["resident_result_contract_attached"] is True
    assert summary["artifacts"]["resident_result_contract"] == str(run / "resident_result_contract.json")
    assert bundle["resident_result_contract_json"] == str(run / "resident_result_contract.json")
    assert bundle["resident_result_contract_source"] == "run_default"
    assert bundle["resident_result_contract_attached"] is True
    assert bundle["artifacts"]["resident_result_contract"] == str(run / "resident_result_contract.json")
    assert stack_contract["resident_result_contract_attached"] is True
    assert stack_contract["resident_result_contract_source"] == "run_default"
    assert stack_contract["integration"]["outputs"][0]["resident_result_contract_passed"] is True


def test_cli_doctor_cpu_only_success(tmp_path: Path):
    out = tmp_path / "doctor.json"
    assert main(["doctor", "--allow-cpu-only", "--skip-cuda-probe", "--json", str(out)]) == 0
    payload = read_json(out)
    assert payload["product"] == "GLASS"
    assert payload["full_name"] == "GPU-Accelerated Lightframe Alignment and Stacking System"
    assert "cuda" in payload
    assert payload["cuda"]["probe_skipped"] is True
    assert "capabilities" in payload
    assert "windows_cuda_packages" in payload
    assert "ordered_try_list" in payload["windows_cuda_packages"]


def test_cli_report_includes_resident_artifacts(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    integration_dir = run / "integration"
    integration_dir.mkdir()
    for name in [
        "resident_master_H.fits",
        "resident_weight_map_H.fits",
        "resident_coverage_map_H.fits",
        "resident_dq_map_H.fits",
    ]:
        (integration_dir / name).write_text("placeholder", encoding="utf-8")
    write_json(
        run / "resident_artifacts.json",
        {
            "backend": "cuda_resident_stack",
            "device": {"name": "Test GPU"},
            "artifacts": [
                {
                    "filter": "H",
                    "frame_ids": ["F1", "F2"],
                    "master_stats": {"bias_count": 1, "dark_count": 1, "flat_count": 1},
                    "memory_estimate": {
                        "resident_base_gib": 1.25,
                        "estimated_peak_without_chunked_warp_gib": 1.75,
                        "estimated_peak_includes_chunked_warp_workspace": True,
                        "estimated_peak_gib": 2.5,
                        "chunked_warp_workspace_model": (
                            "native_preferred_min_frame_count_8_with_halving_fallback"
                        ),
                        "chunked_warp_planned_capacity_frames": 8,
                        "chunked_warp_observed_capacity_frames": 4,
                        "chunked_warp_planned_workspace_bytes": 1048576,
                        "chunked_warp_observed_workspace_bytes": 524288,
                    },
                    "resident_io_pipeline": {"prefetch_frames": 2, "prefetch_workers": 1},
                    "resident_registration": {
                        "mode": "similarity_cuda_triangle",
                        "warp_interpolation": "lanczos3",
                        "triangle_warp_batch_dispatch": "chunked",
                        "warp_coverage": {
                            "available": True,
                            "active_frame_count": 2,
                            "frame_count": 2,
                            "frame_count_matches_active": True,
                            "warped_frame_count": 1,
                            "full_frame_count": 1,
                            "native_source": "ResidentCalibratedStack warp coverage accumulator",
                            "statistics": {"min": 1.0, "max": 2.0, "mean": 1.75},
                        },
                    },
                    "resident_local_normalization": {"mode": "resident_grid_mean_std"},
                    "resident_integration_weighting": {"mode": "simple_snr"},
                    "integration_rejection": {"mode": "winsorized_sigma"},
                    "master_path": "integration/resident_master_H.fits",
                    "weight_map_path": "integration/resident_weight_map_H.fits",
                    "coverage_map_path": "integration/resident_coverage_map_H.fits",
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "dq_map_path": "integration/resident_dq_map_H.fits",
                    "output_map_policy": {
                        "mode": "science",
                        "available": ["master", "weight", "dq", "coverage", "low_rejection", "high_rejection"],
                        "written": ["master", "weight", "dq", "coverage"],
                        "skipped": ["low_rejection", "high_rejection"],
                        "description": "science keeps comparison maps and skips rejection count FITS files",
                    },
                    "output_write": {
                        "breakdown_s": {"master": 0.125, "weight": 0.25, "coverage": 0.375, "dq": 0.5},
                        "mode": "threaded",
                        "workers": 4,
                    },
                    "output_write_storage": {
                        "master": {"dtype": "float32", "estimated_data_bytes": 1048576},
                        "weight": {"dtype": "float32", "estimated_data_bytes": 2097152},
                        "coverage": {"dtype": "int16", "estimated_data_bytes": 524288},
                        "dq": {"dtype": "int16", "estimated_data_bytes": 524288},
                    },
                    "output_diagnostics": {
                        "total_pixels": 4,
                        "finite_pixels": 4,
                        "nonfinite_pixels": 0,
                        "statistics": {"mean": 0.25, "p50": 0.2, "std": 0.1, "min": 0.0, "max": 1.0},
                        "clipping_probe": {
                            "lt_0_count": 0,
                            "gt_1_count": 0,
                            "gt_65535_count": 0,
                            "positive_weight_pixels": 4,
                            "zero_weight_pixels": 0,
                        },
                        "normalization_probe": {
                            "method": "diagnostic_only_p0_1_to_p99_9",
                            "scale": 1.5,
                            "offset": -0.1,
                            "black": 0.0,
                            "white": 1.0,
                        },
                    },
                    "dq_provenance_summary": {
                        "schema_version": 1,
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 2,
                        "zero_coverage_pixels": 0,
                        "partial_coverage_pixels": 1,
                        "valid_pixels": 3,
                        "no_data_pixels": 0,
                        "warp_edge_pixels": 1,
                    },
                    "timing_s": {
                        "light_read_upload_calibrate": 2.0,
                        "light_read_decode": 1.0,
                        "light_read_decode_worker": 1.25,
                        "light_h2d_calibrate_store": 0.75,
                        "resident_registration_warp": 0.5,
                        "resident_registration_component_accounted": 0.4,
                        "resident_registration_orchestration": 0.1,
                        "light_loop_unaccounted": 0.25,
                        "resident_weighting": 0.1,
                        "resident_local_normalization": 0.2,
                        "resident_integration": 0.25,
                        "output_write": 0.5,
                    },
                }
            ],
        },
    )
    write_json(
        run / "calibration_artifacts.json",
        {
            "artifact_type": "resident_cuda_calibration_artifacts",
            "source_stage": "resident_calibrated_stack",
            "backend": "cuda_resident_stack",
            "memory_mode": "resident",
            "resident_artifacts_path": str(run / "resident_artifacts.json"),
            "policy": {
                "master_rejection": "winsorized_sigma",
                "flat_normalization": "median",
                "flat_floor": 0.05,
            },
            "masters": {
                "resident_bias_H": {
                    "type": "bias",
                    "filter": "H",
                    "path": "calib_cache/resident_masters/master_bias.npy",
                    "backend": "cuda_resident_stack",
                    "tile_stack_mode": "cuda_resident_stack",
                    "resident_surface_scope": "full_frame_vram",
                    "source_frame_count": 20,
                    "stats": {"mean": 100.0, "std": 2.0},
                    "resident_calibration_contract": {
                        "status": "passed",
                        "passed": True,
                    },
                },
                "resident_dark_H": {
                    "type": "dark",
                    "filter": "H",
                    "path": "calib_cache/resident_masters/master_dark.npy",
                    "backend": "cuda_resident_stack",
                    "tile_stack_mode": "cuda_resident_stack",
                    "resident_surface_scope": "full_frame_vram",
                    "source_frame_count": 20,
                    "master_dark_includes_bias": True,
                    "stats": {"mean": 110.0, "std": 3.0},
                    "resident_calibration_contract": {
                        "status": "passed",
                        "passed": True,
                    },
                },
                "resident_flat_H": {
                    "type": "flat",
                    "filter": "H",
                    "path": "calib_cache/resident_masters/master_flat.npy",
                    "backend": "cuda_resident_stack",
                    "tile_stack_mode": "cuda_resident_stack",
                    "resident_surface_scope": "full_frame_vram",
                    "source_frame_count": 20,
                    "flat_floor": 0.05,
                    "stats": {"mean": 1.0, "std": 0.05},
                    "resident_calibration_contract": {
                        "status": "passed",
                        "passed": True,
                    },
                },
            },
            "calibrated_lights": [
                {
                    "frame_id": "F1",
                    "filter": "H",
                    "status": "resident_in_vram",
                    "backend": "cuda_resident_stack",
                    "source_stage": "resident_calibrated_stack",
                    "resident_output_index": 0,
                    "resident_stack_index": 0,
                    "resident_master_path": "integration/resident_master_H.fits",
                },
                {
                    "frame_id": "F2",
                    "filter": "H",
                    "status": "resident_in_vram",
                    "backend": "cuda_resident_stack",
                    "source_stage": "resident_calibrated_stack",
                    "resident_output_index": 0,
                    "resident_stack_index": 1,
                    "resident_master_path": "integration/resident_master_H.fits",
                },
            ],
        },
    )
    write_json(
        run / "integration_results.json",
        {
            "source_stage": "resident_calibrated_stack",
            "outputs": [
                {
                    "filter": "H",
                    "dq_map_path": "dq.fits",
                    "dq_summary": {"valid": 3, "warp_edge": 1, "no_data": 0},
                    "geometric_warp_coverage": {
                        "available": True,
                        "frame_count": 2,
                        "frame_count_matches_active": True,
                    },
                    "dq_coverage_provenance": {
                        "available": True,
                        "active_frame_count": 2,
                        "source_terms": ["post_rejection_coverage", "geometric_warp_coverage"],
                        "geometric_warp_coverage_frame_count": 2,
                        "geometric_frame_count_matches_active": True,
                        "geometric_warp_coverage": {"min": 1.0, "max": 2.0, "mean": 1.75},
                        "geometric_zero_pixels": 0,
                        "geometric_partial_pixels": 1,
                        "geometric_full_pixels": 3,
                        "partial_edge_inference": "available_from_geometric_warp_coverage",
                    },
                    "dq_provenance_summary": {
                        "schema_version": 1,
                        "source_schema": "resident_dq_coverage_provenance",
                        "stage": "integration",
                        "item": "H",
                        "engine": "cuda_resident_stack",
                        "active_frame_count": 2,
                        "zero_coverage_pixels": 0,
                        "partial_coverage_pixels": 1,
                        "valid_pixels": 3,
                        "no_data_pixels": 0,
                        "warp_edge_pixels": 1,
                    },
                    "output_map_policy": {
                        "mode": "science",
                        "available": ["master", "weight", "dq", "coverage"],
                        "written": ["master", "weight", "dq", "coverage"],
                        "skipped": [],
                    },
                }
            ],
        },
    )
    write_json(
        run / "fixture_compare.json",
        {
            "shape_match": True,
            "rms_diff": 0.001,
            "abs_diff_p99": 0.004,
            "timing": {
                "glass_time_seconds": 10.0,
                "reference_time_seconds": 250.0,
                "speedup_vs_reference": 25.0,
            },
            "comparison_region": {"coverage_fraction": 0.97, "compared_pixels": 12345},
        },
    )
    write_json(
        run / "fixture_acceptance_audit.json",
        {
            "status": "passed",
            "passed": True,
            "benchmark_contract": {"name": "fixture_contract", "schema_version": 1},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "checks": [
                {"name": "minimum_speedup", "passed": True},
                {"name": "maximum_rms_diff", "passed": True},
                {
                    "name": "contract_pipeline_contract_passed",
                    "passed": True,
                    "evidence": {"actual": True, "status": "passed", "failed_checks": []},
                },
                {
                    "name": "contract_stack_engine_default_promotion_ready",
                    "passed": True,
                    "evidence": {"actual": True, "status": "ready", "blockers": []},
                },
            ],
            "release_contract_evidence": {
                "pipeline_contract": {
                    "status": "passed",
                    "required_by_benchmark_contract": True,
                    "pipeline_contract_path": "pipeline_contract.json",
                    "pipeline_contract_audit_type": "pipeline_invariant_contract",
                    "pipeline_contract_status": "passed",
                    "pipeline_contract_passed": True,
                    "pipeline_contract_check_count": 7,
                    "direct_check_count": 2,
                    "benchmark_check_count": 6,
                    "passed_check_count": 8,
                    "failed_check_count": 0,
                    "failed_checks": [],
                    "checks": [
                        {
                            "name": "contract_pipeline_contract_passed",
                            "passed": True,
                            "evidence": {"actual": True, "status": "passed", "failed_checks": []},
                            "note": "",
                        },
                        {
                            "name": "contract_pipeline_contract_check:integration_resident_result_contract",
                            "passed": True,
                            "evidence": {
                                "required": "integration_resident_result_contract",
                                "available": ["integration_resident_result_contract"],
                            },
                            "note": "",
                        },
                    ],
                },
                "stack_engine_default_promotion": {
                    "status": "passed",
                    "required_by_benchmark_contract": True,
                    "stack_engine_contract_path": "stack_engine_contract.json",
                    "stack_engine_contract_audit_type": "stack_engine_default_contract",
                    "stack_engine_contract_status": "passed",
                    "stack_engine_contract_passed": True,
                    "stack_engine_contract_scope": "all",
                    "default_promotion_ready": True,
                    "default_promotion_status": "ready",
                    "default_promotion_gap_count": 0,
                    "default_promotion_blocker_count": 0,
                    "adoption_recommendation": "stack_engine_default_ready",
                    "direct_check_count": 2,
                    "benchmark_check_count": 7,
                    "passed_check_count": 9,
                    "failed_check_count": 0,
                    "failed_checks": [],
                    "checks": [
                        {
                            "name": "contract_stack_engine_default_promotion_ready",
                            "passed": True,
                            "evidence": {"actual": True, "status": "ready", "blockers": []},
                            "note": "",
                        },
                        {
                            "name": "contract_stack_engine_default_promotion_gap_count",
                            "passed": True,
                            "evidence": {"actual": 0, "required_max": 0},
                            "note": "",
                        },
                    ],
                }
            },
            "speedup_summary": {
                "speedup_vs_wbpp": 25.0,
                "glass": {"elapsed_s": 10.0, "weighted_frame_count": 2, "zero_weight_frame_count": 0},
                "wbpp_blackbox": {"elapsed_s": 250.0},
                "comparison": {
                    "shape_match": True,
                    "rms_diff": 0.001,
                    "abs_diff_p99": 0.004,
                    "coverage_fraction": 0.97,
                    "compared_pixels": 12345,
                },
            },
            "summary": {
                "output_numerical_drift_count": 1,
                "output_numerical_drift_max_relative_rms": 0.011916,
            },
            "output_numerical_drifts": [
                {
                    "key": "H:200:F000061:F000260",
                    "field": "master_path",
                    "drift": {
                        "available": True,
                        "joint_finite_pixels": 61651200,
                        "nonfinite_mismatch_pixels": 0,
                        "mean_signed": 0.000111721,
                        "mean_abs": 0.642260,
                        "median_abs": 0.417107,
                        "rms": 3.751400,
                        "p95_abs": 1.489120,
                        "p99_abs": 3.408920,
                        "max_abs": 1836.101562,
                        "baseline_std": 314.820862,
                        "candidate_std": 314.730194,
                        "relative_rms_to_baseline_std": 0.011916,
                    },
                }
            ],
        },
    )
    report = tmp_path / "resident_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")
    assert "Report navigation" in html
    assert '<nav class="report-toc"' in html
    assert 'class="section-anchor"' in html
    assert 'href="#benchmark-comparison"' in html
    assert 'id="benchmark-comparison"' in html
    assert 'href="#release-contract-evidence"' in html
    assert 'id="release-contract-evidence"' in html
    assert 'href="#optimization-guidance"' in html
    assert 'id="optimization-guidance"' in html
    assert 'href="#resident-output-maps"' in html
    assert 'id="resident-output-maps"' in html
    assert 'href="#acceptance-check-failures"' in html
    assert 'id="acceptance-check-failures"' in html
    assert 'href="#output-numerical-drift"' in html
    assert 'id="output-numerical-drift"' in html
    assert "Benchmark comparison" in html
    assert "Release contract evidence" in html
    assert "contract_pipeline_contract_passed" in html
    assert "contract_pipeline_contract_check:integration_resident_result_contract" in html
    assert "pipeline_invariant_contract" in html
    assert "stack_engine_default_promotion" in html
    assert "contract_stack_engine_default_promotion_ready" in html
    assert "stack_engine_default_contract" in html
    assert "stack_engine_default_ready" in html
    assert "Optimization guidance" in html
    assert "I/O + upload + calibration overlap" in html
    assert "Resident registration/warp batching" in html
    assert "Acceptance check failures" in html
    assert "Output numerical drift" in html
    assert "H:200:F000061:F000260" in html
    assert "relative_rms_to_baseline_std" in html
    assert "0.011916" in html
    assert "3.7514" in html
    assert "Only failed acceptance-audit checks" in html
    assert "fixture_contract" in html
    assert "fixture_compare.json" in html
    assert "fixture_acceptance_audit.json" in html
    assert "25.0" in html
    assert "0.97" in html
    assert "12345" in html
    assert "Resident CUDA summary" in html
    assert "Resident calibration artifact" in html
    assert "resident_cuda_calibration_artifacts" in html
    assert "resident_light_ledger_rows" in html
    assert "resident_stack_index" in html
    assert "full_frame_vram" in html
    assert "cuda_resident_stack" in html
    assert "Test GPU" in html
    assert "estimated_peak_gib" in html
    assert "estimated_peak_without_chunked_warp_gib" in html
    assert "estimated_peak_includes_chunked_warp_workspace" in html
    assert "chunked_warp_workspace_model" in html
    assert "native_preferred_min_frame_count_8_with_halving_fallback" in html
    assert "chunked_warp_planned_workspace_mib" in html
    assert "chunked_warp_observed_workspace_mib" in html
    assert "prefetch_frames" in html
    assert "read_decode_s" in html
    assert "read_decode_worker_s" in html
    assert "h2d_calibrate_store_s" in html
    assert "registration_warp_s" in html
    assert "registration_accounted_s" in html
    assert "registration_orchestration_s" in html
    assert "similarity_cuda_triangle" in html
    assert "lanczos3" in html
    assert "warp_batch_dispatch" in html
    assert "chunked" in html
    assert "resident_grid_mean_std" in html
    assert "simple_snr" in html
    assert "winsorized_sigma" in html
    assert "Output map policy" in html
    assert "science" in html
    assert "master, weight, dq, coverage" in html
    assert "low_rejection, high_rejection" in html
    assert "Resident output maps" in html
    assert "integration/resident_master_H.fits" in html
    assert "resident_weight_map_H.fits" in html
    assert "estimated_mib" in html
    assert "float32" in html
    assert "int16" in html
    assert "0.125" in html
    assert "skipped" in html
    assert "Output diagnostics" in html
    assert "normalization_scale" in html
    assert "1.5" in html
    assert "gt_65535_count" in html
    assert "clipping_probe" not in html
    assert "output_diagnostics" not in html
    assert "Geometric warp coverage" in html
    assert "DQ provenance contract" in html
    assert "resident_dq_coverage_provenance" in html
    assert "available_from_geometric_warp_coverage" in html
    assert "geometric_partial_pixels" in html
    assert "ResidentCalibratedStack warp coverage accumulator" in html


def test_cli_report_lists_failed_acceptance_checks(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(run / "run_timing.json", {"command": "run", "backend": "cuda", "total_elapsed_s": 12.0, "stages": []})
    write_json(run / "integration_results.json", {"outputs": [], "frame_weights": {}})
    write_json(
        run / "failure_compare.json",
        {
            "shape_match": True,
            "rms_diff": 0.25,
            "abs_diff_p99": 0.5,
            "timing": {"glass_time_seconds": 12.0, "reference_time_seconds": 120.0, "speedup_vs_reference": 10.0},
            "comparison_region": {"coverage_fraction": 0.8, "compared_pixels": 99},
        },
    )
    write_json(
        run / "failure_acceptance_audit.json",
        {
            "status": "failed",
            "passed": False,
            "benchmark_contract": {"name": "failure_contract"},
            "frame_type_counts": {"light": 200, "bias": 20, "dark": 20, "flat": 20},
            "checks": [
                {
                    "name": "maximum_rms_diff",
                    "passed": False,
                    "evidence": {"actual": 0.25, "required_max": 0.01, "source": "compare"},
                    "note": "RMS exceeded benchmark contract",
                },
                {
                    "name": "minimum_speedup",
                    "passed": True,
                    "evidence": {"actual": 10.0, "required": 2.0},
                },
            ],
            "speedup_summary": {
                "speedup_vs_wbpp": 10.0,
                "glass": {"elapsed_s": 12.0, "weighted_frame_count": 190, "zero_weight_frame_count": 10},
                "wbpp_blackbox": {"elapsed_s": 120.0},
                "comparison": {"shape_match": True, "rms_diff": 0.25, "abs_diff_p99": 0.5, "coverage_fraction": 0.8},
            },
        },
    )

    report = tmp_path / "failure_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Benchmark comparison" in html
    assert "failure_contract" in html
    assert "checks_failed" in html
    assert "Acceptance check failures" in html
    assert "maximum_rms_diff" in html
    assert "RMS exceeded benchmark contract" in html
    assert "0.25" in html
    assert "0.01" in html
    assert "source=compare" in html
    assert "minimum_speedup" not in html


def test_cli_report_summarizes_stack_engine_contract(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "stack_engine_contract.json",
        {
            "audit_type": "stack_engine_default_contract",
            "status": "failed",
            "passed": False,
            "scope": "all",
            "expected_integration_engine": "stack_engine_cpu",
            "checks": [
                {
                    "name": "calibration_masters_use_stack_engine",
                    "passed": False,
                    "note": "fixture legacy fallback",
                    "evidence": {"master_count": 1, "failed": ["bias_bad"]},
                },
                {
                    "name": "integration_outputs_use:stack_engine_cpu",
                    "passed": True,
                    "evidence": {"output_count": 1, "failed": []},
                },
            ],
            "calibration": {
                "master_count": 1,
                "masters": [
                    {
                        "name": "bias_bad",
                        "type": "bias",
                        "tile_stack_mode": "legacy_streaming_accumulator",
                        "contract_ok": False,
                        "has_dq_provenance": False,
                        "summary_source_schema": None,
                        "fallback_reason": "fixture fallback",
                    }
                ],
            },
            "integration": {
                "output_count": 1,
                "outputs": [
                    {
                        "index": 0,
                        "filter": "H",
                        "tile_stack_mode": "stack_engine_cpu",
                        "summary_engine": "stack_engine_cpu",
                        "summary_source_schema": "stack_engine_dq_provenance",
                        "contract_ok": True,
                        "has_stack_engine_dq_provenance": True,
                        "expected_engine": "stack_engine_cpu",
                    }
                ],
            },
            "adoption": {
                "schema_version": 1,
                "target_engine": "stack_engine_cpu",
                "surface_count": 2,
                "stack_engine_surface_count": 1,
                "cuda_resident_surface_count": 0,
                "other_surface_count": 1,
                "engine_counts": {"legacy_streaming_accumulator": 1, "stack_engine_cpu": 1},
                "contract_ready_count": 1,
                "result_contract_passed_count": 1,
                "fallback_count": 1,
                "phase2_stack_engine_default_gap_count": 1,
                "recommendation": "stack_engine_contract_gaps_remain",
                "surfaces": [
                    {
                        "surface": "master_calibration",
                        "item": "bias_bad",
                        "type": "bias",
                        "engine_family": "legacy_streaming_accumulator",
                        "stack_engine_contract_ready": False,
                        "phase2_stack_engine_default_gap": True,
                        "gap_reason": "stack_engine_fallback",
                        "result_contract_passed": False,
                        "fallback_reason": "fixture fallback",
                    },
                    {
                        "surface": "integration",
                        "item": "H",
                        "type": "light",
                        "engine_family": "stack_engine_cpu",
                        "stack_engine_contract_ready": True,
                        "phase2_stack_engine_default_gap": False,
                        "gap_reason": "",
                        "result_contract_passed": True,
                    },
                ],
            },
            "default_promotion": {
                "schema_version": 1,
                "target_engine": "stack_engine_cpu",
                "ready": False,
                "status": "blocked",
                "required_scope": "all",
                "actual_scope": "all",
                "surface_count": 2,
                "calibration_surface_count": 1,
                "integration_surface_count": 1,
                "phase2_stack_engine_default_gap_count": 1,
                "recommendation": "stack_engine_contract_gaps_remain",
                "blocker_count": 2,
                "blockers": [
                    {
                        "name": "phase2_stack_engine_default_gaps",
                        "gap_count": 1,
                    },
                    {
                        "name": "adoption_recommendation_not_ready",
                        "actual": "stack_engine_contract_gaps_remain",
                        "required": "stack_engine_default_ready",
                    },
                ],
            },
        },
    )

    report = tmp_path / "stack_contract_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "StackEngine contract audit" in html
    assert "stack_engine_contract.json" in html
    assert "calibration_masters_use_stack_engine" in html
    assert "fixture legacy fallback" in html
    assert "phase2_stack_engine_default_gaps" in html
    assert "stack_engine_contract_gaps_remain" in html
    assert "stack_engine_fallback" in html
    assert "default_promotion_ready" in html
    assert "default_promotion_blockers" in html
    assert "adoption_recommendation_not_ready" in html
    assert "bias_bad" in html
    assert "legacy_streaming_accumulator" in html
    assert "integration_outputs_use:stack_engine_cpu" not in html


def test_cli_report_summarizes_pipeline_contract(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "pipeline_contract.json",
        {
            "audit_type": "pipeline_invariant_contract",
            "status": "failed",
            "passed": False,
            "artifacts": {
                "warp": {"exists": True, "path": "warp_results.json"},
                "local_norm": {"exists": True, "path": "local_norm_results.json"},
                "integration": {"exists": True, "path": "integration_results.json"},
            },
            "checks": [
                {
                    "name": "integration_output_maps_available",
                    "passed": False,
                    "note": "fixture missing coverage",
                    "evidence": {"map_count": 2, "failed": ["H:coverage"]},
                },
                {
                    "name": "integration_rejection_sample_counts_match_maps",
                    "passed": False,
                    "note": "fixture sample-count drift",
                    "evidence": {
                        "verified_records": 1,
                        "required_records": 1,
                        "failed": [
                            {
                                "item": "H",
                                "status": "verified",
                                "map_rejected_sample_sum": 7,
                                "source_counts": [
                                    {
                                        "name": "dq_coverage_provenance.rejected_sample_count",
                                        "count": 6,
                                    }
                                ],
                            }
                        ],
                    },
                },
                {
                    "name": "integration_artifact_exists",
                    "passed": True,
                    "evidence": {"path": "integration_results.json"},
                },
            ],
            "integration": {
                "maps": [
                    {
                        "surface": "integration",
                        "item": "H",
                        "map": "coverage",
                        "exists": False,
                        "required": True,
                        "policy_skipped": False,
                        "ok": False,
                        "path": None,
                    }
                ]
            },
            "pixel_verification": {
                "enabled": True,
                "tile_size": 32,
                "tolerance_pixels": 0,
                "integration_outputs": [
                    {
                        "item": "H",
                        "dq": {
                            "status": "verified",
                            "ok": False,
                            "path": "integration/dq_H.fits",
                            "summary_matches": {
                                "valid": {"actual": 41, "summary": 42, "delta": -1, "passed": False}
                            },
                        },
                        "count_maps": {
                            "coverage": {
                                "status": "verified",
                                "ok": False,
                                "summary_match": {
                                    "no_data": {"actual": 2, "summary": 1, "delta": 1, "passed": False}
                                },
                            },
                            "low_rejection": {
                                "status": "verified",
                                "ok": True,
                                "summary_match": {
                                    "low_rejected": {"actual": 5, "summary": 5, "delta": 0, "passed": True}
                                },
                            },
                            "high_rejection": {"status": "not_required", "ok": True},
                        },
                        "rejection_sample_accounting": {
                            "status": "verified",
                            "verified": True,
                            "ok": False,
                            "required": True,
                            "rejection": "winsorized_sigma",
                            "map_rejected_sample_sum": 7,
                            "source_counts": [
                                {"name": "dq_coverage_provenance.rejected_sample_count", "count": 6},
                                {"name": "dq_provenance_summary.rejected_samples", "count": 6},
                            ],
                            "source_matches": [
                                {
                                    "source": "dq_coverage_provenance.rejected_sample_count",
                                    "actual": 7,
                                    "summary": 6,
                                    "delta": 1,
                                    "passed": False,
                                },
                                {
                                    "source": "dq_provenance_summary.rejected_samples",
                                    "actual": 7,
                                    "summary": 6,
                                    "delta": 1,
                                    "passed": False,
                                },
                            ],
                            "semantics": (
                                "Low/high rejection count maps store rejected-sample counts; "
                                "DQ low/high flags store pixels touched by rejection."
                            ),
                        },
                    }
                ],
            },
            "local_normalization": {
                "outputs": [
                    {
                        "frame_id": "F1",
                        "enabled": True,
                        "status": "ok",
                        "crop_box_recorded": True,
                        "normalized_path_exists": True,
                        "coverage_path_exists": True,
                        "dq_mask_path_exists": True,
                        "coefficient_grid_exists": True,
                        "contract_ok": True,
                    }
                ]
            },
            "warp": {
                "outputs": [
                    {
                        "frame_id": "F1",
                        "interpolation": "bilinear",
                        "registered_path_exists": True,
                        "coverage_path_exists": True,
                        "dq_mask_path_exists": True,
                        "dq_summary_has_valid": True,
                        "contract_ok": True,
                    }
                ],
                "skipped_frames": [],
            },
        },
    )

    report = tmp_path / "pipeline_contract_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Pipeline contract audit" in html
    assert "pipeline_contract.json" in html
    assert "integration_output_maps_available" in html
    assert "fixture missing coverage" in html
    assert "H:coverage" in html
    assert "pixel_verification" in html
    assert "integration/dq_H.fits" in html
    assert "low_rejected" in html
    assert "<td>-1</td>" in html
    assert "<td>5</td><td>5</td><td>0</td><td>True</td>" in html
    assert "integration_rejection_sample_counts_match_maps" in html
    assert "fixture sample-count drift" in html
    assert "pipeline contract rejection sample accounting rows" in html
    assert "map_rejected_sample_sum" in html
    assert "dq_coverage_provenance.rejected_sample_count=6" in html
    assert "dq_provenance_summary.rejected_samples=6" in html
    assert "actual=7 summary=6 delta=1" in html
    assert "Low/high rejection count maps store rejected-sample counts" in html
    assert "local-normalization" in html
    assert "bilinear" in html
    assert "integration_artifact_exists" not in html


def test_cli_report_summarizes_local_norm_contract(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    contract = tmp_path / "custom_local_norm_contract.json"
    write_json(
        contract,
        {
            "schema_version": 1,
            "artifact_type": "local_norm_contract",
            "status": "failed",
            "passed": False,
            "enabled": True,
            "reference_frame_id": "F000001",
            "model": "continuous_grid_mean_std_v1",
            "coefficient_field_model": "bilinear_tile_center_v1",
            "crop_box": None,
            "summary": {
                "output_count": 1,
                "failed_output_count": 1,
                "residual_quality": {
                    "output_count": 1,
                    "failed_output_count": 0,
                    "total_valid_pixels": 4,
                    "max_rms": 0.5,
                    "max_abs": 2.0,
                },
            },
            "checks": [
                {
                    "name": "output_contracts_passed",
                    "passed": False,
                    "note": "fixture failed row",
                    "evidence": {"failed": ["F000002"]},
                }
            ],
            "outputs": [
                {
                    "frame_id": "F000002",
                    "enabled": True,
                    "status": "normalized",
                    "passed": False,
                    "model": "continuous_grid_mean_std_v1",
                    "coefficient_field_model": "bilinear_tile_center_v1",
                    "coefficient_grid_contract": {
                        "passed": False,
                        "grid_rows": 2,
                        "grid_cols": 3,
                        "full_field_map_status": "omitted_due_to_size",
                    },
                    "residual_summary": {"valid_pixels": 4, "rms": 0.5, "max_abs": 2.0},
                    "failed_checks": ["coefficient_grid_contract"],
                }
            ],
            "failed_outputs": [
                {
                    "frame_id": "F000002",
                    "index": 0,
                    "failed_checks": ["coefficient_grid_contract"],
                }
            ],
        },
    )

    report = tmp_path / "local_norm_contract_report.html"
    assert (
        main(
            [
                "report",
                "--run",
                str(run),
                "--out",
                str(report),
                "--local-norm-contract",
                str(contract),
            ]
        )
        == 0
    )
    html = report.read_text(encoding="utf-8")

    assert "Local normalization contract" in html
    assert "custom_local_norm_contract.json" in html
    assert "output_contracts_passed" in html
    assert "fixture failed row" in html
    assert "F000002" in html
    assert "coefficient_grid_contract" in html
    assert "omitted_due_to_size" in html
    assert "residual_max_rms" in html
    assert "residual_rms" in html
    assert "0.5" in html


def test_cli_report_limits_large_audit_tables(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    frames = [
        {
            "id": f"frame_{index:04d}",
            "path": f"lights/frame_{index:04d}.fits",
            "frame_type": "light",
        }
        for index in range(205)
    ]
    quality_rows = [
        {
            "frame_id": f"quality_{index:04d}",
            "star_count": 20,
            "background_rms": 1.0,
            "weight": 1.0,
        }
        for index in range(202)
    ]
    write_json(run / "manifest.json", {"frames": frames, "summary": {"count": len(frames)}})
    write_json(
        run / "frame_quality.json",
        {
            "frame_quality": quality_rows,
            "reference_frame_id": "quality_0000",
            "star_detector": "fixture_detector",
            "weight_source": "fixture_weight",
        },
    )

    report = tmp_path / "large_table_report.html"
    assert main(["report", "--run", str(run), "--out", str(report)]) == 0
    html = report.read_text(encoding="utf-8")

    assert "Showing first 200 of 205 input frames" in html
    assert "Full details remain in <code>manifest.json</code>" in html
    assert "frame_0199" in html
    assert "frame_0200" not in html
    assert "Showing first 200 of 202 frame quality rows" in html
    assert "Full details remain in <code>frame_quality.json</code>" in html
    assert "quality_0199" in html
    assert "quality_0200" not in html
