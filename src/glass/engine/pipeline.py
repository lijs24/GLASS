from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any

from glass.cpu.calibration import calibrate_light
from glass.cpu.cosmetic import correct_cosmetic_defects
from glass.engine.contracts import CombinePolicy, DQFlag, DQMask, OutputMapPolicy, RejectionPolicy, StackRequest, TileWindow
from glass.engine.dq import add_summary_counts, dq_header, dq_mask_from_invalid, write_dq_tile
from glass.engine.stack_engine import CPUStackEngine
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.image_source import FitsImageSource
from glass.io.fits_io import FitsImageReader, FitsTileWriter
from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy, PipelineArtifact, RunState, now_iso


def initialize_run(run_dir: str | Path) -> RunState:
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    return RunState(run_id=Path(run_dir).name or "glass-run", created_at=now_iso(), current_stage="created")


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    if isinstance(raw, dict):
        allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
        return CalibrationPolicy(**{key: value for key, value in raw.items() if key in allowed})
    return CalibrationPolicy()


def _frame_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {frame["id"]: frame for frame in plan.get("frames", [])}


def _group_map(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {group["group_id"]: group for group in plan.get("groups", [])}


def _paths_for_group(group: dict[str, Any], frames: dict[str, dict[str, Any]]) -> list[str]:
    return [str(frames[frame_id]["path"]) for frame_id in group.get("frames", [])]


def _find_matching_bias_for_group(
    target_group: dict[str, Any], groups: dict[str, dict[str, Any]]
) -> str | None:
    for group_id, group in groups.items():
        if group.get("group_type") != "bias":
            continue
        if (
            group.get("gain") == target_group.get("gain")
            and group.get("offset") == target_group.get("offset")
            and group.get("binning") == target_group.get("binning")
            and group.get("shape") == target_group.get("shape")
        ):
            return group_id
    return None


def _cuda_module_if_requested(backend: str):
    if backend == "cpu":
        return None
    try:
        import glass_cuda
    except Exception:
        return None
    if glass_cuda.cuda_available():
        return glass_cuda
    if backend == "cuda":
        raise RuntimeError("CUDA backend requested but native CUDA backend is unavailable")
    return None


class _StreamingStats:
    def __init__(self) -> None:
        self.count = 0
        self.total = 0.0
        self.total_sq = 0.0
        self.minimum: float | None = None
        self.maximum: float | None = None
        self.tile_median_total = 0.0
        self.tile_median_pixels = 0

    def update(self, tile: Any) -> None:
        import numpy as np

        values = np.asarray(tile, dtype=np.float64)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return
        self.count += int(finite.size)
        self.total += float(np.sum(finite))
        self.total_sq += float(np.sum(finite * finite))
        current_min = float(np.min(finite))
        current_max = float(np.max(finite))
        self.minimum = current_min if self.minimum is None else min(self.minimum, current_min)
        self.maximum = current_max if self.maximum is None else max(self.maximum, current_max)
        self.tile_median_total += float(np.median(finite)) * int(finite.size)
        self.tile_median_pixels += int(finite.size)

    def as_dict(self) -> dict[str, float]:
        import math

        if self.count == 0:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "std": 0.0}
        mean = self.total / self.count
        variance = max(self.total_sq / self.count - mean * mean, 0.0)
        median = self.tile_median_total / max(self.tile_median_pixels, 1)
        return {
            "min": float(self.minimum if self.minimum is not None else 0.0),
            "max": float(self.maximum if self.maximum is not None else 0.0),
            "mean": float(mean),
            "median": float(median),
            "std": float(math.sqrt(variance)),
        }


def _mean_stack_tile(readers: list[FitsImageReader], tile) -> Any:
    import numpy as np

    acc = None
    count = 0
    for reader in readers:
        data = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
        if acc is None:
            acc = np.zeros_like(data, dtype=np.float64)
        if data.shape != acc.shape:
            raise ValueError(f"shape mismatch while stacking tile: {data.shape} != {acc.shape}")
        acc += data
        count += 1
    if acc is None or count == 0:
        raise ValueError("cannot stack an empty frame list")
    return (acc / count).astype(np.float32)


def _stream_mean_master(
    paths: list[str],
    out_path: Path,
    tile_size: int,
    header: dict[str, Any],
    subtract_path: str | None = None,
) -> dict[str, float]:
    import numpy as np

    if not paths:
        raise ValueError("cannot stack an empty frame list")
    stats = _StreamingStats()
    with ExitStack() as stack:
        readers = [stack.enter_context(FitsImageReader(path)) for path in paths]
        subtract_reader = stack.enter_context(FitsImageReader(subtract_path)) if subtract_path else None
        height, width = readers[0].shape
        with FitsTileWriter(out_path, width=width, height=height, header=header) as writer:
            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                mean_tile = _mean_stack_tile(readers, tile)
                if subtract_reader is not None:
                    mean_tile = (
                        mean_tile - subtract_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    ).astype(np.float32)
                writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, mean_tile)
                stats.update(mean_tile)
    return stats.as_dict()


def _master_rejection_policy(policy: CalibrationPolicy | None) -> RejectionPolicy:
    policy = policy or CalibrationPolicy()
    return RejectionPolicy(
        method=policy.master_rejection,  # type: ignore[arg-type]
        iterations=policy.master_rejection_iterations,
        low_sigma=policy.master_rejection_low_sigma,
        high_sigma=policy.master_rejection_high_sigma,
        min_samples=policy.master_rejection_min_samples,
        max_reject_fraction=policy.master_rejection_max_fraction,
    )


def _stack_mean_master_with_engine(
    paths: list[str],
    out_path: Path,
    tile_size: int,
    header: dict[str, Any],
    subtract_path: str | None = None,
) -> tuple[dict[str, float], dict[str, float | int | str]]:
    import numpy as np

    if not paths:
        raise ValueError("cannot stack an empty frame list")
    policy = header.pop("_calibration_policy", None)
    rejection = _master_rejection_policy(policy if isinstance(policy, CalibrationPolicy) else None)
    with ExitStack() as stack:
        sources = {
            f"frame-{index}": stack.enter_context(FitsImageSource(path))
            for index, path in enumerate(paths)
        }
        request = StackRequest(
            frame_ids=tuple(sources.keys()),
            source_kind="unknown",
            combine=CombinePolicy(method="mean", accumulator_dtype="float64"),
            rejection=rejection,
            output_maps=OutputMapPolicy(
                coverage=False,
                weight=False,
                variance=False,
                low_rejection=False,
                high_rejection=False,
                dq=False,
            ),
            metadata={"stage": "master_calibration"},
        )
        result = CPUStackEngine(tile_size=tile_size).stack(request, sources)
        subtract_reader = stack.enter_context(FitsImageReader(subtract_path)) if subtract_path else None
        height, width = result.master.shape
        stats = _StreamingStats()
        with FitsTileWriter(out_path, width=width, height=height, header=header) as writer:
            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                data = result.master[tile.y0 : tile.y1, tile.x0 : tile.x1]
                if subtract_reader is not None:
                    data = (
                        data - subtract_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                    ).astype(np.float32)
                writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, data)
                stats.update(data)
    return stats.as_dict(), result.metrics


def _stack_mean_master(
    paths: list[str],
    out_path: Path,
    tile_size: int,
    header: dict[str, Any],
    subtract_path: str | None = None,
    use_stack_engine: bool = True,
    policy: CalibrationPolicy | None = None,
) -> tuple[dict[str, float], str, str | None, dict[str, float | int | str]]:
    header = dict(header)
    if policy is not None:
        header["_calibration_policy"] = policy
    if use_stack_engine:
        try:
            stats, metrics = _stack_mean_master_with_engine(paths, out_path, tile_size, header, subtract_path)
            return (
                stats,
                "stack_engine_cpu",
                None,
                metrics,
            )
        except Exception as exc:
            fallback_stats = _stream_mean_master(paths, out_path, tile_size, header, subtract_path)
            return fallback_stats, "legacy_streaming_accumulator", str(exc), {
                "combine": "mean",
                "rejection": "none",
                "frame_count": len(paths),
            }
    return (
        _stream_mean_master(paths, out_path, tile_size, header, subtract_path),
        "legacy_streaming_accumulator",
        None,
        {"combine": "mean", "rejection": "none", "frame_count": len(paths)},
    )


def _normalization_scalar(path: Path, normalization: str, tile_size: int) -> tuple[float, str]:
    with FitsImageReader(path) as reader:
        if normalization == "median":
            return _exact_median_scratch(path, tile_size), "median_scratch_memmap"
        stats = _StreamingStats()
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            stats.update(reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1))
    values = stats.as_dict()
    return float(values["mean"]), "mean"


def _normalization_scalar_for_frame(
    path: str | Path,
    subtract_path: str | Path | None,
    normalization: str,
    tile_size: int,
) -> tuple[float, str]:
    import gc
    import numpy as np

    source_path = Path(path)
    if normalization != "median":
        stats = _StreamingStats()
        with FitsImageReader(source_path) as reader, ExitStack() as stack:
            subtract_reader = stack.enter_context(FitsImageReader(subtract_path)) if subtract_path else None
            for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
                data = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                if subtract_reader is not None:
                    data = data - subtract_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                stats.update(data)
        return float(stats.as_dict()["mean"]), "mean_streaming"

    scratch_target = Path(str(source_path) + ".flat_norm_scratch.bin")
    scratch = None
    work = None
    try:
        with FitsImageReader(source_path) as reader, ExitStack() as stack:
            subtract_reader = stack.enter_context(FitsImageReader(subtract_path)) if subtract_path else None
            total_pixels = reader.width * reader.height
            scratch = np.memmap(scratch_target, dtype=np.float32, mode="w+", shape=(total_pixels,))
            finite_count = 0
            for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
                values = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                if subtract_reader is not None:
                    values = values - subtract_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                finite = values.ravel()[np.isfinite(values.ravel())]
                count = int(finite.size)
                if count:
                    scratch[finite_count : finite_count + count] = finite
                    finite_count += count
        if finite_count == 0:
            raise ValueError("cannot normalize flat frame: no finite pixels")
        work = scratch[:finite_count]
        mid = finite_count // 2
        work.partition(mid)
        upper = float(work[mid])
        if finite_count % 2 == 1:
            return upper, "median_scratch_memmap_per_flat"
        return (float(np.max(work[:mid])) + upper) / 2.0, "median_scratch_memmap_per_flat"
    finally:
        if scratch is not None:
            scratch.flush()
        del work
        del scratch
        gc.collect()
        scratch_target.unlink(missing_ok=True)


class _NormalizedFlatSource:
    def __init__(self, path: str | Path, normalization_scalar: float, subtract_path: str | Path | None = None):
        self.path = Path(path)
        self.normalization_scalar = float(normalization_scalar)
        self.subtract_path = None if subtract_path is None else Path(subtract_path)
        self.metadata: dict[str, Any] = {"normalization_scalar": self.normalization_scalar}
        self.channels = 1
        self.dtype = "float32"
        self.width = 0
        self.height = 0
        self._reader: FitsImageReader | None = None
        self._subtract_reader: FitsImageReader | None = None

    def __enter__(self) -> "_NormalizedFlatSource":
        self._reader = FitsImageReader(self.path)
        self._reader.__enter__()
        self.height, self.width = self._reader.shape
        if self.subtract_path is not None:
            self._subtract_reader = FitsImageReader(self.subtract_path)
            self._subtract_reader.__enter__()
            if self._subtract_reader.shape != (self.height, self.width):
                raise ValueError("flat bias/dark subtraction shape mismatch")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._subtract_reader is not None:
            self._subtract_reader.__exit__(exc_type, exc, tb)
        if self._reader is not None:
            self._reader.__exit__(exc_type, exc, tb)
        self._subtract_reader = None
        self._reader = None

    def read_tile(self, window: TileWindow, dtype: Any = None) -> Any:
        import numpy as np

        if self._reader is None:
            raise RuntimeError("normalized flat source is not open")
        data = self._reader.read_tile(window.y0, window.y1, window.x0, window.x1)
        if self._subtract_reader is not None:
            data = data - self._subtract_reader.read_tile(window.y0, window.y1, window.x0, window.x1)
        data = data / np.float32(self.normalization_scalar)
        return np.asarray(data, dtype=dtype or np.float32)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        tile = self.read_tile(window, dtype=None)
        return dq_mask_from_invalid(tile.shape, ~np.isfinite(tile), DQFlag.NO_DATA)


def _stack_normalized_flat_master(
    paths: list[str],
    out_path: Path,
    tile_size: int,
    flat_floor: float,
    normalization: str,
    header: dict[str, Any],
    subtract_path: str | None,
    policy: CalibrationPolicy,
) -> tuple[dict[str, float], list[dict[str, Any]], str, str | None, dict[str, float | int | str]]:
    import numpy as np

    per_flat: list[dict[str, Any]] = []
    try:
        scalars: list[float] = []
        for index, path in enumerate(paths):
            scalar, method = _normalization_scalar_for_frame(path, subtract_path, normalization, tile_size)
            if abs(scalar) < flat_floor:
                raise ValueError(f"flat normalization is below flat_floor for {path}")
            scalars.append(scalar)
            per_flat.append({"path": str(path), "normalization_scalar": scalar, "normalization_method": method})
        with ExitStack() as stack:
            sources = {
                f"flat-{index}": stack.enter_context(_NormalizedFlatSource(path, scalars[index], subtract_path))
                for index, path in enumerate(paths)
            }
            request = StackRequest(
                frame_ids=tuple(sources.keys()),
                source_kind="flat",
                combine=CombinePolicy(method="mean", accumulator_dtype="float64"),
                rejection=_master_rejection_policy(policy),
                output_maps=OutputMapPolicy(
                    coverage=False,
                    weight=False,
                    variance=False,
                    low_rejection=False,
                    high_rejection=False,
                    dq=False,
                ),
                metadata={"stage": "master_flat", "normalization": "per_flat"},
            )
            result = CPUStackEngine(tile_size=tile_size).stack(request, sources)
        data = np.maximum(result.master, np.float32(flat_floor)).astype(np.float32)
        stats = _StreamingStats()
        height, width = data.shape
        with FitsTileWriter(out_path, width=width, height=height, header=header) as writer:
            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                tile_data = data[tile.y0 : tile.y1, tile.x0 : tile.x1]
                writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_data)
                stats.update(tile_data)
        return stats.as_dict(), per_flat, "stack_engine_cpu_per_flat_normalized", None, result.metrics
    except Exception as exc:
        raw_path = out_path.with_name(f"raw_{out_path.name}")
        _raw_stats, tile_stack_mode, fallback_reason, metrics = _stack_mean_master(
            paths,
            raw_path,
            tile_size,
            {"IMAGETYP": "raw_flat", "FILTER": header.get("FILTER")},
            subtract_path=subtract_path,
            policy=policy,
        )
        stats, norm, norm_method = _normalize_flat_master(
            raw_path, out_path, tile_size, flat_floor, normalization, header
        )
        raw_path.unlink(missing_ok=True)
        per_flat.append(
            {
                "path": "fallback_master_normalization",
                "normalization_scalar": norm,
                "normalization_method": norm_method,
            }
        )
        reason = f"{exc}; fallback={fallback_reason}" if fallback_reason else str(exc)
        return stats, per_flat, tile_stack_mode, reason, metrics


def _exact_median_scratch(path: Path, tile_size: int, scratch_path: Path | None = None) -> float:
    import gc
    import numpy as np

    scratch_target = scratch_path or Path(str(path) + ".median_scratch.bin")
    scratch_target.parent.mkdir(parents=True, exist_ok=True)
    scratch = None
    work = None
    try:
        with FitsImageReader(path) as reader:
            total_pixels = reader.width * reader.height
            scratch = np.memmap(scratch_target, dtype=np.float32, mode="w+", shape=(total_pixels,))
            finite_count = 0
            for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
                values = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1).ravel()
                finite = values[np.isfinite(values)]
                count = int(finite.size)
                if count:
                    scratch[finite_count : finite_count + count] = finite
                    finite_count += count
        if finite_count == 0:
            raise ValueError("cannot compute median: no finite pixels")
        work = scratch[:finite_count]
        mid = finite_count // 2
        work.partition(mid)
        upper = float(work[mid])
        if finite_count % 2 == 1:
            return upper
        return (float(np.max(work[:mid])) + upper) / 2.0
    finally:
        if scratch is not None:
            scratch.flush()
        del work
        del scratch
        gc.collect()
        scratch_target.unlink(missing_ok=True)


def _normalize_flat_master(
    raw_path: Path,
    out_path: Path,
    tile_size: int,
    flat_floor: float,
    normalization: str,
    header: dict[str, Any],
) -> tuple[dict[str, float], float, str]:
    import numpy as np

    norm, norm_method = _normalization_scalar(raw_path, normalization, tile_size)
    if abs(norm) < flat_floor:
        raise ValueError("flat normalization is below flat_floor")
    stats = _StreamingStats()
    with FitsImageReader(raw_path) as reader, FitsTileWriter(
        out_path, width=reader.width, height=reader.height, header=header
    ) as writer:
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            data = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
            normalized = np.maximum(data / np.float32(norm), np.float32(flat_floor)).astype(np.float32)
            writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, normalized)
            stats.update(normalized)
    return stats.as_dict(), norm, norm_method


def _calibrate_light_to_cache_streaming(
    frame: dict[str, Any],
    path: Path,
    bias_path: str | None,
    dark_path: str | None,
    flat_path: str | None,
    dark_exposure: float | None,
    policy: CalibrationPolicy,
    backend: str,
    tile_size: int,
) -> dict[str, Any]:
    import numpy as np

    cuda_module = _cuda_module_if_requested(backend)
    dq_dir = path.parent.parent / "dq"
    dq_dir.mkdir(parents=True, exist_ok=True)
    dq_path = dq_dir / f"dq_calibrated_{frame['id']}.fits"
    dq_summary: dict[str, int] = {}
    cosmetic_summary = {"hot_pixels": 0, "cold_pixels": 0}
    with ExitStack() as stack:
        light_reader = stack.enter_context(FitsImageReader(frame["path"]))
        bias_reader = stack.enter_context(FitsImageReader(bias_path)) if bias_path else None
        dark_reader = stack.enter_context(FitsImageReader(dark_path)) if dark_path else None
        flat_reader = stack.enter_context(FitsImageReader(flat_path)) if flat_path else None
        height, width = light_reader.shape
        with FitsTileWriter(
            path,
            width=width,
            height=height,
            header={
                "IMAGETYP": "calibrated_light",
                "FILTER": frame.get("filter"),
                "EXPTIME": frame.get("exposure_s"),
            },
        ) as writer, FitsTileWriter(
            dq_path,
            width=width,
            height=height,
            header=dq_header("calibration", frame["id"]),
        ) as dq_writer:
            tile_count = 0
            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                light_tile = light_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                bias_tile = (
                    None if bias_reader is None else bias_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                )
                dark_tile = (
                    None if dark_reader is None else dark_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                )
                flat_tile = (
                    None if flat_reader is None else flat_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                )
                if cuda_module is not None:
                    calibrated_tile = cuda_module.calibrate_tile_f32(
                        light_tile,
                        bias_tile,
                        dark_tile,
                        flat_tile,
                        float(frame.get("exposure_s") or 0.0),
                        dark_exposure,
                        {
                            "master_dark_includes_bias": policy.master_dark_includes_bias,
                            "dark_scaling_enabled": policy.dark_scaling_enabled,
                            "flat_floor": policy.flat_floor,
                            "pedestal": policy.pedestal,
                        },
                    )
                    actual_backend = "cuda"
                else:
                    calibrated_tile = calibrate_light(
                        light_tile,
                        bias_tile,
                        dark_tile,
                        flat_tile,
                        float(frame.get("exposure_s") or 0.0),
                        dark_exposure,
                        policy,
                    )
                    actual_backend = "cpu"
                tile_dq = DQMask.empty(calibrated_tile.shape)
                if policy.saturation_level is not None:
                    tile_dq.mark(DQFlag.SATURATED, light_tile >= np.float32(policy.saturation_level))
                if policy.cosmetic_correction_enabled:
                    cosmetic = correct_cosmetic_defects(
                        calibrated_tile,
                        hot_sigma=policy.cosmetic_hot_sigma,
                        cold_sigma=policy.cosmetic_cold_sigma,
                    )
                    calibrated_tile = cosmetic.data
                    tile_dq.data |= cosmetic.dq_mask.data
                    cosmetic_summary["hot_pixels"] += int(cosmetic.metrics["hot_pixels"])
                    cosmetic_summary["cold_pixels"] += int(cosmetic.metrics["cold_pixels"])
                writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, calibrated_tile)
                tile_dq.mark(DQFlag.NO_DATA, ~np.isfinite(calibrated_tile))
                write_dq_tile(dq_writer, tile, tile_dq)
                add_summary_counts(dq_summary, tile_dq.summary())
                tile_count += 1
    return {
        "frame_id": frame["id"],
        "path": str(path),
        "dq_mask_path": str(dq_path),
        "dq_summary": dq_summary,
        "cosmetic_correction": {
            "enabled": policy.cosmetic_correction_enabled,
            "hot_sigma": policy.cosmetic_hot_sigma,
            "cold_sigma": policy.cosmetic_cold_sigma,
            **cosmetic_summary,
        },
        "backend": actual_backend,
        "tile_size": tile_size,
        "tile_count": tile_count,
    }


def run_calibration_stages(
    plan_path: str | Path,
    run_dir: str | Path,
    backend: str = "auto",
    tile_size: int = 512,
    flat_floor: float | None = None,
) -> RunState:
    plan = read_json(plan_path)
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    state = initialize_run(out)
    state.current_stage = "master_calibration"

    frames = _frame_map(plan)
    groups = _group_map(plan)
    policy = _policy_from_plan(plan)
    if flat_floor is not None:
        if flat_floor <= 0:
            raise ValueError("flat_floor override must be positive")
        policy.flat_floor = float(flat_floor)
    master_dir = out / "calib_cache" / "masters"
    calibrated_dir = out / "calib_cache" / "calibrated"
    master_dir.mkdir(parents=True, exist_ok=True)
    calibrated_dir.mkdir(parents=True, exist_ok=True)

    master_metadata: dict[str, Any] = {}

    try:
        for group_id, group in groups.items():
            group_type = group.get("group_type")
            if group_type != "bias":
                continue
            path = master_dir / f"master_bias_{group_id}.fits"
            stats, tile_stack_mode, fallback_reason, stack_metrics = _stack_mean_master(
                _paths_for_group(group, frames),
                path,
                tile_size,
                {"IMAGETYP": "master_bias"},
                policy=policy,
            )
            master_metadata[group_id] = {
                "path": str(path),
                "stats": stats,
                "type": "bias",
                "streaming": True,
                "tile_stack_mode": tile_stack_mode,
                "stack_engine_enabled": tile_stack_mode == "stack_engine_cpu",
                "stack_engine_fallback_reason": fallback_reason,
                "stack_engine_metrics": stack_metrics,
                "master_rejection": policy.master_rejection,
                "tile_size": tile_size,
            }

        for group_id, group in groups.items():
            group_type = group.get("group_type")
            if group_type != "dark":
                continue
            bias_group = None if policy.master_dark_includes_bias else _find_matching_bias_for_group(group, groups)
            bias_path = (
                master_metadata.get(bias_group, {}).get("path")
                if bias_group is not None
                else None
            )
            path = master_dir / f"master_dark_{group_id}.fits"
            stats, tile_stack_mode, fallback_reason, stack_metrics = _stack_mean_master(
                _paths_for_group(group, frames),
                path,
                tile_size,
                {"IMAGETYP": "master_dark", "EXPTIME": group.get("exposure_s")},
                subtract_path=bias_path,
                policy=policy,
            )
            master_metadata[group_id] = {
                "path": str(path),
                "stats": stats,
                "type": "dark",
                "exposure_s": group.get("exposure_s"),
                "master_dark_includes_bias": policy.master_dark_includes_bias,
                "bias_group": bias_group,
                "bias_subtracted_from_source": bias_path is not None,
                "streaming": True,
                "tile_stack_mode": tile_stack_mode,
                "stack_engine_enabled": tile_stack_mode == "stack_engine_cpu",
                "stack_engine_fallback_reason": fallback_reason,
                "stack_engine_metrics": stack_metrics,
                "master_rejection": policy.master_rejection,
                "tile_size": tile_size,
            }

        for group_id, group in groups.items():
            group_type = group.get("group_type")
            if group_type != "flat":
                continue
            bias_group = _find_matching_bias_for_group(group, groups)
            bias_path = (
                master_metadata.get(bias_group, {}).get("path")
                if bias_group is not None
                else None
            )
            path = master_dir / f"master_flat_{group_id}.fits"
            stats, per_flat_normalization, raw_tile_stack_mode, raw_fallback_reason, raw_stack_metrics = _stack_normalized_flat_master(
                _paths_for_group(group, frames),
                path,
                tile_size,
                policy.flat_floor,
                policy.flat_normalization,
                {"IMAGETYP": "master_flat", "FILTER": group.get("filter")},
                subtract_path=bias_path,
                policy=policy,
            )
            master_metadata[group_id] = {
                "path": str(path),
                "stats": stats,
                "type": "flat",
                "filter": group.get("filter"),
                "bias_group": bias_group,
                "bias_subtracted_from_source": bias_path is not None,
                "normalization": policy.flat_normalization,
                "normalization_stage": "per_flat",
                "per_flat_normalization": per_flat_normalization,
                "normalization_scalar": per_flat_normalization[0]["normalization_scalar"] if per_flat_normalization else None,
                "normalization_method": per_flat_normalization[0]["normalization_method"] if per_flat_normalization else None,
                "flat_floor": policy.flat_floor,
                "streaming": True,
                "tile_stack_mode": raw_tile_stack_mode,
                "stack_engine_enabled": raw_tile_stack_mode == "stack_engine_cpu",
                "stack_engine_fallback_reason": raw_fallback_reason,
                "stack_engine_metrics": raw_stack_metrics,
                "master_rejection": policy.master_rejection,
                "tile_size": tile_size,
            }

        state.completed_stages.append("master_calibration")
        state.current_stage = "light_calibration"

        calibrated: list[dict[str, Any]] = []
        for light_plan in plan.get("light_plans", []):
            if light_plan.get("calibration_status") != "ready":
                warning = f"light plan skipped because it is not ready: {light_plan}"
                state.warnings.append(warning)
                continue
            dark_group = light_plan.get("matching_dark_group")
            flat_group = light_plan.get("matching_flat_group")
            bias_group = light_plan.get("matching_bias_group")
            dark_path = master_metadata.get(dark_group, {}).get("path") if dark_group else None
            flat_path = master_metadata.get(flat_group, {}).get("path") if flat_group else None
            bias_path = master_metadata.get(bias_group, {}).get("path") if bias_group else None
            dark_exposure = groups.get(dark_group, {}).get("exposure_s") if dark_group else None
            for frame_id in light_plan.get("frames", []):
                frame = frames[frame_id]
                path = calibrated_dir / f"calibrated_{frame_id}.fits"
                calibrated.append(
                    _calibrate_light_to_cache_streaming(
                        frame,
                        path,
                        bias_path,
                        dark_path,
                        flat_path,
                        None if dark_exposure is None else float(dark_exposure),
                        policy,
                        backend,
                        tile_size,
                    )
                )

        artifacts_path = out / "calibration_artifacts.json"
        write_json(
            artifacts_path,
            {
                "masters": master_metadata,
                "calibrated_lights": calibrated,
                "policy": policy,
                "tile_size": tile_size,
                "requested_backend": backend,
            },
        )
        state.artifacts.append(
            PipelineArtifact(
                stage="calibration",
                path=str(artifacts_path),
                format="json",
                created_at=now_iso(),
                source_frames=list(frames.keys()),
            )
        )
        state.completed_stages.append("light_calibration")
        state.current_stage = "calibration"
        return state
    except Exception as exc:
        state.failed_stage = state.current_stage
        state.errors.append(str(exc))
        raise
