from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from glass.engine.contracts import (
    CombinePolicy,
    DQFlag,
    DQMask,
    OutputMapPolicy,
    RejectionPolicy,
    StackRequest,
    TileWindow,
)
from glass.engine.dq import (
    add_summary_counts,
    dq_header,
    dq_mask_from_coverage,
    dq_provenance_summary_from_stack_engine,
    write_dq_tile,
)
from glass.engine.stack_engine import CPUStackEngine, StackEngineResult
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader, FitsTileWriter
from glass.io.json_io import read_json, write_json


def _cuda_module_if_requested(backend: str):
    if backend == "cpu":
        return None
    try:
        import glass_cuda
    except Exception:
        return None
    if glass_cuda.cuda_available() and hasattr(glass_cuda, "integrate_accumulate_mean_tile_f32"):
        return glass_cuda
    if backend == "cuda":
        raise RuntimeError("CUDA backend requested but integration CUDA backend is unavailable")
    return None


def _safe_filter_name(value: str | None) -> str:
    text = value or "unknown"
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)


def _plan_data(plan_path: str | Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if plan_path is None or not Path(plan_path).exists():
        return {}, {}
    plan = read_json(plan_path)
    frames = {frame["id"]: frame for frame in plan.get("frames", [])}
    policy = plan.get("integration_policy", {})
    return frames, policy if isinstance(policy, dict) else {}


def _source_records(run: Path) -> tuple[str, list[dict[str, Any]]]:
    local_norm_path = run / "local_norm_results.json"
    if local_norm_path.exists():
        local_norm = read_json(local_norm_path)
        records = []
        for item in local_norm.get("local_norm_results", []):
            records.append(
                {
                    "frame_id": item["frame_id"],
                    "path": item["normalized_path"],
                    "coverage_path": item["coverage_path"],
                }
            )
        return "local_normalization", records
    warp = read_json(run / "warp_results.json")
    records = []
    for item in warp.get("warp_results", []):
        records.append({"frame_id": item["frame_id"], "path": item["registered_path"], "coverage_path": item["coverage_path"]})
    return "warp", records


def _quality_weights(run: Path, records: list[dict[str, Any]], weighting: str) -> dict[str, float]:
    if weighting == "none":
        return {item["frame_id"]: 1.0 for item in records}
    if weighting not in {"simple_snr", "combined", "variance_aware"}:
        raise ValueError(f"unsupported integration weighting mode: {weighting}")
    quality_path = run / "frame_quality.json"
    quality = read_json(quality_path) if quality_path.exists() else {}
    quality_by_id = {item["frame_id"]: item for item in quality.get("frame_quality", [])}
    raw_weights: dict[str, float] = {}
    for item in records:
        q = quality_by_id.get(item["frame_id"], {})
        if weighting == "simple_snr":
            value = float(q.get("snr") or q.get("weight") or 1.0)
        elif weighting == "combined":
            value = float(q.get("quality_score") or q.get("weight") or 1.0)
        else:
            noise = q.get("noise_sigma") or q.get("background_rms")
            if noise is None:
                value = float(q.get("weight") or 1.0)
            else:
                variance = max(float(noise) ** 2, 1.0e-12)
                value = 1.0 / variance
        raw_weights[item["frame_id"]] = max(value, 1.0e-6)
    positive = np.asarray([value for value in raw_weights.values() if np.isfinite(value) and value > 0.0], dtype=np.float32)
    scale = float(np.median(positive)) if positive.size else 1.0
    scale = max(scale, 1.0e-6)
    return {frame_id: max(float(value) / scale, 1.0e-6) for frame_id, value in raw_weights.items()}


def _policy_value(policy: dict[str, Any], key: str, override: str | None, default: str) -> str:
    if override is not None and override != "auto":
        return override
    return str(policy.get(key) or default)


def _stack_engine_rejection_method(value: str) -> str:
    if value == "sigma_clip":
        return "sigma"
    return value


def _output_variance_map_enabled(policy: dict[str, Any]) -> bool:
    return bool(policy.get("output_variance_map", True))


def _bool_policy(policy: dict[str, Any], key: str, default: bool = False) -> bool:
    value = policy.get(key, default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _integration_engine_selection(
    *,
    backend: str,
    rejection: str,
    cuda_module: Any,
    policy: dict[str, Any],
) -> dict[str, Any]:
    cuda_available = cuda_module is not None
    cuda_fast_path_eligible = cuda_available and rejection == "none"
    allow_cuda_fast_path = _bool_policy(policy, "allow_cuda_streaming_accumulator_fast_path", False)
    explicit_cuda_fast_path = allow_cuda_fast_path
    use_cuda_fast_path = cuda_fast_path_eligible and explicit_cuda_fast_path
    if use_cuda_fast_path:
        reason = "explicit_cuda_fast_path_requested"
    elif cuda_available and rejection != "none":
        reason = "stack_engine_required_for_rejection"
    elif cuda_available and backend == "cuda" and not allow_cuda_fast_path:
        reason = "cuda_backend_stack_engine_default_requires_fast_path_policy"
    elif cuda_available and not explicit_cuda_fast_path:
        reason = "stack_engine_default_requires_explicit_cuda_fast_path"
    elif backend == "cuda":
        reason = "cuda_requested_but_unavailable"
    else:
        reason = "stack_engine_default"
    return {
        "default_engine": "stack_engine_cpu",
        "actual_backend": "cuda" if use_cuda_fast_path else "cpu",
        "use_stack_engine": not use_cuda_fast_path,
        "tile_stack_mode": (
            "cuda_streaming_accumulator_fast_path"
            if use_cuda_fast_path
            else "stack_engine_cpu"
        ),
        "backend": backend,
        "cuda_available": cuda_available,
        "cuda_fast_path_eligible": cuda_fast_path_eligible,
        "explicit_cuda_fast_path": explicit_cuda_fast_path,
        "allow_cuda_streaming_accumulator_fast_path": allow_cuda_fast_path,
        "cuda_fast_path_policy_required": bool(cuda_available and rejection == "none"),
        "rejection": rejection,
        "reason": reason,
    }


@dataclass(slots=True)
class _CoverageImageSource:
    path: str | Path
    coverage_path: str | Path
    metadata: dict[str, Any] = field(default_factory=dict)
    width: int = 0
    height: int = 0
    channels: int = 1
    dtype: str = "float32"
    _reader: FitsImageReader | None = field(default=None, init=False, repr=False)
    _coverage_reader: FitsImageReader | None = field(default=None, init=False, repr=False)

    def __enter__(self) -> "_CoverageImageSource":
        self._reader = FitsImageReader(self.path)
        self._coverage_reader = FitsImageReader(self.coverage_path)
        self._reader.__enter__()
        self._coverage_reader.__enter__()
        self.height, self.width = self._reader.shape
        if self._coverage_reader.shape != (self.height, self.width):
            raise ValueError("coverage shape does not match image shape")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._coverage_reader is not None:
            self._coverage_reader.__exit__(exc_type, exc, tb)
        if self._reader is not None:
            self._reader.__exit__(exc_type, exc, tb)
        self._reader = None
        self._coverage_reader = None

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        if self._reader is None:
            raise RuntimeError("coverage image source is not open")
        return self._reader.read_tile(window.y0, window.y1, window.x0, window.x1, dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        if self._reader is None or self._coverage_reader is None:
            raise RuntimeError("coverage image source is not open")
        data = self._reader.read_tile(window.y0, window.y1, window.x0, window.x1)
        coverage = self._coverage_reader.read_tile(window.y0, window.y1, window.x0, window.x1)
        mask = DQMask.empty(window.shape)
        invalid = (~np.isfinite(data)) | (~np.isfinite(coverage)) | (coverage <= 0.5)
        if np.any(invalid):
            mask.mark(DQFlag.NO_DATA, invalid)
        return mask


@dataclass(slots=True)
class _WindowedCoverageImageSource:
    parent: _CoverageImageSource
    base: TileWindow
    metadata: dict[str, Any] = field(default_factory=dict)
    channels: int = 1
    dtype: str = "float32"

    @property
    def path(self) -> str | Path:
        return self.parent.path

    @property
    def width(self) -> int:
        return self.base.width

    @property
    def height(self) -> int:
        return self.base.height

    def _global_window(self, window: TileWindow) -> TileWindow:
        if window.y0 < 0 or window.x0 < 0 or window.y1 > self.base.height or window.x1 > self.base.width:
            raise ValueError("local stack tile is outside the parent integration tile")
        return TileWindow(
            self.base.y0 + window.y0,
            self.base.y0 + window.y1,
            self.base.x0 + window.x0,
            self.base.x0 + window.x1,
        )

    def read_tile(self, window: TileWindow, dtype: Any = np.float32) -> np.ndarray:
        return self.parent.read_tile(self._global_window(window), dtype=dtype)

    def read_mask_tile(self, window: TileWindow) -> DQMask:
        return self.parent.read_mask_tile(self._global_window(window))


def _empty_dq_flag_counts() -> dict[str, int]:
    return {flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID}


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _add_int(target: dict[str, Any], key: str, value: Any) -> None:
    target[key] = _int_value(target.get(key)) + _int_value(value)


def _contract_check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _compact_tile_contract(tile: TileWindow, contract: dict[str, Any]) -> dict[str, Any]:
    checks = contract.get("checks") if isinstance(contract.get("checks"), list) else []
    failed = [
        str(item.get("name"))
        for item in checks
        if isinstance(item, dict) and not bool(item.get("passed"))
    ]
    return {
        "tile": {"y0": tile.y0, "y1": tile.y1, "x0": tile.x0, "x1": tile.x1},
        "passed": bool(contract.get("passed")),
        "status": contract.get("status"),
        "contract_type": contract.get("contract_type"),
        "failed_checks": failed,
    }


def _stack_engine_streaming_result_contract(
    *,
    width: int,
    height: int,
    request: StackRequest,
    requested_maps: dict[str, bool],
    output_paths: dict[str, Path | None],
    metrics: dict[str, Any],
    dq_provenance: dict[str, Any],
    tile_contracts: list[dict[str, Any]],
    tile_count: int,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failed_tile_contracts = [item for item in tile_contracts if not bool(item.get("passed"))]
    checks.append(
        _contract_check(
            "tile_stack_engine_contracts_passed",
            not failed_tile_contracts,
            {
                "tile_contract_count": len(tile_contracts),
                "failed_tile_contract_count": len(failed_tile_contracts),
                "failed_tiles": failed_tile_contracts[:8],
            },
        )
    )
    missing_requested_paths = {
        name: str(output_paths.get(name))
        for name, required in requested_maps.items()
        if required and (output_paths.get(name) is None or not Path(output_paths[name]).exists())
    }
    checks.append(
        _contract_check(
            "requested_maps_streamed",
            not missing_requested_paths,
            {
                "requested_maps": requested_maps,
                "missing_requested_paths": missing_requested_paths,
            },
        )
    )
    checks.append(
        _contract_check(
            "full_output_arrays_not_materialized",
            metrics.get("full_output_arrays_materialized") is False,
            {
                "execution_path": metrics.get("execution_path"),
                "full_output_arrays_materialized": metrics.get("full_output_arrays_materialized"),
            },
        )
    )
    expected_pixels = int(width) * int(height)
    checks.append(
        _contract_check(
            "streamed_tiles_cover_output_shape",
            _int_value(metrics.get("streamed_output_pixels")) == expected_pixels and tile_count == len(tile_contracts),
            {
                "streamed_output_pixels": metrics.get("streamed_output_pixels"),
                "expected_pixels": expected_pixels,
                "tile_count": tile_count,
                "tile_contract_count": len(tile_contracts),
            },
        )
    )
    input_samples = _int_value(dq_provenance.get("input_samples"))
    input_valid = _int_value(dq_provenance.get("input_valid_samples_before_rejection"))
    input_invalid = _int_value(dq_provenance.get("input_invalid_samples_before_rejection"))
    valid_after = _int_value(dq_provenance.get("valid_samples_after_rejection"))
    low_rejected = _int_value(dq_provenance.get("low_rejected_samples"))
    high_rejected = _int_value(dq_provenance.get("high_rejected_samples"))
    checks.append(
        _contract_check(
            "input_valid_invalid_samples_match_total",
            input_valid + input_invalid == input_samples,
            {
                "input_samples": input_samples,
                "input_valid_samples_before_rejection": input_valid,
                "input_invalid_samples_before_rejection": input_invalid,
            },
        )
    )
    checks.append(
        _contract_check(
            "input_valid_samples_close_after_rejection",
            input_valid == valid_after + low_rejected + high_rejected,
            {
                "input_valid_samples_before_rejection": input_valid,
                "valid_samples_after_rejection": valid_after,
                "low_rejected_samples": low_rejected,
                "high_rejected_samples": high_rejected,
                "accounted_samples": valid_after + low_rejected + high_rejected,
            },
        )
    )
    expected_input_samples = len(request.frame_ids) * expected_pixels
    checks.append(
        _contract_check(
            "input_samples_match_request_shape",
            input_samples == expected_input_samples,
            {
                "input_samples": input_samples,
                "expected_input_samples": expected_input_samples,
                "frame_count": len(request.frame_ids),
                "pixels_per_frame": expected_pixels,
            },
        )
    )
    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": 1,
        "contract_type": "stack_engine_streaming_result_contract",
        "compatible_contract_type": "stack_engine_result_contract",
        "passed": passed,
        "status": "passed" if passed else "failed",
        "master_shape": [int(height), int(width)],
        "requested_maps": requested_maps,
        "tile_count": int(tile_count),
        "tile_contract_count": len(tile_contracts),
        "failed_tile_contract_count": len(failed_tile_contracts),
        "checks": checks,
    }


def _write_stack_engine_result(
    result: StackEngineResult,
    master_path: Path,
    weight_path: Path,
    coverage_path: Path,
    variance_path: Path | None,
    low_path: Path,
    high_path: Path,
    dq_path: Path,
    tile_size: int,
) -> tuple[int, dict[str, int]]:
    height, width = result.master.shape
    tile_count = 0
    dq_summary: dict[str, int] = {}
    with ExitStack() as stack:
        master_writer = stack.enter_context(FitsTileWriter(master_path, width, height, {"IMAGETYP": "master"}))
        weight_writer = stack.enter_context(FitsTileWriter(weight_path, width, height, {"IMAGETYP": "weight"}))
        coverage_writer = stack.enter_context(FitsTileWriter(coverage_path, width, height, {"IMAGETYP": "coverage"}))
        variance_writer = (
            stack.enter_context(FitsTileWriter(variance_path, width, height, {"IMAGETYP": "variance"}))
            if variance_path is not None
            else None
        )
        low_writer = stack.enter_context(FitsTileWriter(low_path, width, height, {"IMAGETYP": "lowrej"}))
        high_writer = stack.enter_context(FitsTileWriter(high_path, width, height, {"IMAGETYP": "highrej"}))
        dq_writer = stack.enter_context(FitsTileWriter(dq_path, width, height, dq_header("integration")))
        weight_map = (
            result.weight_map if result.weight_map is not None else np.zeros_like(result.master, dtype=np.float32)
        )
        coverage_map = (
            result.coverage_map
            if result.coverage_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        low_map = (
            result.low_rejection_map
            if result.low_rejection_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        high_map = (
            result.high_rejection_map
            if result.high_rejection_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        variance_map = (
            result.variance_map
            if result.variance_map is not None
            else np.zeros_like(result.master, dtype=np.float32)
        )
        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
            y_slice = slice(tile.y0, tile.y1)
            x_slice = slice(tile.x0, tile.x1)
            master_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, result.master[y_slice, x_slice])
            weight_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, weight_map[y_slice, x_slice])
            coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage_map[y_slice, x_slice])
            if variance_writer is not None:
                variance_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, variance_map[y_slice, x_slice])
            low_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, low_map[y_slice, x_slice])
            high_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, high_map[y_slice, x_slice])
            if result.dq_mask is not None:
                dq_tile = DQMask(result.dq_mask.data[y_slice, x_slice].copy())
            else:
                dq_tile = dq_mask_from_coverage(coverage_map[y_slice, x_slice], DQFlag.NO_DATA)
            write_dq_tile(dq_writer, tile, dq_tile)
            add_summary_counts(dq_summary, dq_tile.summary())
            tile_count += 1
    return tile_count, dq_summary


def _integrate_with_stack_engine(
    items: list[dict[str, Any]],
    frame_weights: dict[str, float],
    rejection: str,
    low_sigma: float,
    high_sigma: float,
    tile_size: int,
    master_path: Path,
    weight_path: Path,
    coverage_path: Path,
    variance_path: Path,
    low_path: Path,
    high_path: Path,
    dq_path: Path,
    weighting: str,
    output_variance_map: bool,
    rejection_min_samples: int,
    rejection_max_fraction: float,
) -> tuple[int, dict[str, Any], str, dict[str, int], dict[str, Any]]:
    method = _stack_engine_rejection_method(rejection)
    with ExitStack() as stack:
        sources = {
            item["frame_id"]: stack.enter_context(
                _CoverageImageSource(item["path"], item["coverage_path"])
            )
            for item in items
        }
        first_source = next(iter(sources.values()))
        width = int(first_source.width)
        height = int(first_source.height)
        request = StackRequest(
            frame_ids=tuple(item["frame_id"] for item in items),
            source_kind="light",
            combine=CombinePolicy(
                method="weighted_mean" if weighting != "none" else "mean",
                accumulator_dtype="float32",
            ),
            rejection=RejectionPolicy(
                method=method,
                low_sigma=low_sigma,
                high_sigma=high_sigma,
                min_samples=rejection_min_samples,
                max_reject_fraction=rejection_max_fraction,
            ),
            output_maps=OutputMapPolicy(
                coverage=True,
                weight=True,
                variance=output_variance_map,
                low_rejection=True,
                high_rejection=True,
                dq=True,
            ),
            weights={item["frame_id"]: frame_weights[item["frame_id"]] for item in items},
            metadata={"stage": "integration", "coverage_source": "coverage_fits"},
        )
        requested_maps = {
            "master": True,
            "weight": True,
            "coverage": True,
            "variance": bool(output_variance_map),
            "low_rejection": True,
            "high_rejection": True,
            "dq": True,
        }
        output_paths: dict[str, Path | None] = {
            "master": master_path,
            "weight": weight_path,
            "coverage": coverage_path,
            "variance": variance_path if output_variance_map else None,
            "low_rejection": low_path,
            "high_rejection": high_path,
            "dq": dq_path,
        }
        stack_engine_metrics: dict[str, Any] = {
            "frame_count": len(items),
            "width": width,
            "height": height,
            "combine": request.combine.method,
            "rejection": request.rejection.method,
            "rejection_scale_estimator": None,
            "valid_samples": 0,
            "input_valid_samples": 0,
            "input_invalid_samples": 0,
            "low_rejected": 0,
            "high_rejected": 0,
            "rejected_samples": 0,
            "execution_path": "stack_engine_streaming_tile_sink",
            "full_output_arrays_materialized": False,
            "streamed_output_pixels": 0,
            "streaming_tile_contract_count": 0,
            "streaming_tile_contract_failed_count": 0,
        }
        dq_provenance: dict[str, Any] = {
            "schema_version": 1,
            "input_samples": 0,
            "input_valid_samples_before_rejection": 0,
            "input_invalid_samples_before_rejection": 0,
            "input_flagged_samples": 0,
            "input_nonfinite_samples": 0,
            "input_dq_flag_counts": _empty_dq_flag_counts(),
            "valid_samples_after_rejection": 0,
            "low_rejected_samples": 0,
            "high_rejected_samples": 0,
            "rejected_samples": 0,
            "rejection_policy": None,
            "output_coverage_zero_pixels": 0,
            "output_low_rejected_pixels": 0,
            "output_high_rejected_pixels": 0,
            "output_dq_summary": {},
            "semantics": (
                "Source DQ flags and non-finite samples are consumed as invalid input stack "
                "samples before rejection. The integration sink executes StackEngine on one "
                "output tile at a time and writes maps immediately; only tile-sized StackEngine "
                "results are materialized."
            ),
            "execution_path": "stack_engine_streaming_tile_sink",
            "full_output_arrays_materialized": False,
        }
        dq_summary: dict[str, int] = {}
        tile_contracts: list[dict[str, Any]] = []
        tile_count = 0
        variance_sum = 0.0
        variance_count = 0
        variance_max = 0.0

        with ExitStack() as writer_stack:
            master_writer = writer_stack.enter_context(
                FitsTileWriter(master_path, width, height, {"IMAGETYP": "master"})
            )
            weight_writer = writer_stack.enter_context(
                FitsTileWriter(weight_path, width, height, {"IMAGETYP": "weight"})
            )
            coverage_writer = writer_stack.enter_context(
                FitsTileWriter(coverage_path, width, height, {"IMAGETYP": "coverage"})
            )
            variance_writer = (
                writer_stack.enter_context(FitsTileWriter(variance_path, width, height, {"IMAGETYP": "variance"}))
                if output_variance_map
                else None
            )
            low_writer = writer_stack.enter_context(FitsTileWriter(low_path, width, height, {"IMAGETYP": "lowrej"}))
            high_writer = writer_stack.enter_context(FitsTileWriter(high_path, width, height, {"IMAGETYP": "highrej"}))
            dq_writer = writer_stack.enter_context(FitsTileWriter(dq_path, width, height, dq_header("integration")))

            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                window = TileWindow(tile.y0, tile.y1, tile.x0, tile.x1)
                tile_sources = {
                    frame_id: _WindowedCoverageImageSource(parent=source, base=window)
                    for frame_id, source in sources.items()
                }
                tile_result = CPUStackEngine(tile_size=max(window.width, window.height)).stack(request, tile_sources)
                tile_master = np.asarray(tile_result.master, dtype=np.float32)
                tile_weight = (
                    np.asarray(tile_result.weight_map, dtype=np.float32)
                    if tile_result.weight_map is not None
                    else np.zeros_like(tile_master, dtype=np.float32)
                )
                tile_coverage = (
                    np.asarray(tile_result.coverage_map, dtype=np.float32)
                    if tile_result.coverage_map is not None
                    else np.zeros_like(tile_master, dtype=np.float32)
                )
                tile_low = (
                    np.asarray(tile_result.low_rejection_map, dtype=np.float32)
                    if tile_result.low_rejection_map is not None
                    else np.zeros_like(tile_master, dtype=np.float32)
                )
                tile_high = (
                    np.asarray(tile_result.high_rejection_map, dtype=np.float32)
                    if tile_result.high_rejection_map is not None
                    else np.zeros_like(tile_master, dtype=np.float32)
                )
                tile_variance = (
                    np.asarray(tile_result.variance_map, dtype=np.float32)
                    if tile_result.variance_map is not None
                    else np.zeros_like(tile_master, dtype=np.float32)
                )
                tile_dq = (
                    tile_result.dq_mask
                    if tile_result.dq_mask is not None
                    else dq_mask_from_coverage(tile_coverage, DQFlag.NO_DATA)
                )

                master_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_master)
                weight_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_weight)
                coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_coverage)
                if variance_writer is not None:
                    variance_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_variance)
                    finite_variance = tile_variance[np.isfinite(tile_variance)]
                    if finite_variance.size:
                        variance_sum += float(np.sum(finite_variance, dtype=np.float64))
                        variance_count += int(finite_variance.size)
                        variance_max = max(variance_max, float(np.max(finite_variance)))
                low_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_low)
                high_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, tile_high)
                write_dq_tile(dq_writer, tile, tile_dq)

                tile_summary = tile_dq.summary()
                add_summary_counts(dq_summary, tile_summary)
                tile_metrics = tile_result.metrics
                tile_provenance = tile_result.dq_provenance
                if stack_engine_metrics["rejection_scale_estimator"] is None:
                    stack_engine_metrics["rejection_scale_estimator"] = tile_metrics.get("rejection_scale_estimator")
                for key in (
                    "valid_samples",
                    "input_valid_samples",
                    "input_invalid_samples",
                    "low_rejected",
                    "high_rejected",
                    "rejected_samples",
                ):
                    _add_int(stack_engine_metrics, key, tile_metrics.get(key))
                _add_int(stack_engine_metrics, "streamed_output_pixels", window.width * window.height)
                for target_key, source_key in (
                    ("input_samples", "input_samples"),
                    ("input_valid_samples_before_rejection", "input_valid_samples_before_rejection"),
                    ("input_invalid_samples_before_rejection", "input_invalid_samples_before_rejection"),
                    ("input_flagged_samples", "input_flagged_samples"),
                    ("input_nonfinite_samples", "input_nonfinite_samples"),
                    ("valid_samples_after_rejection", "valid_samples_after_rejection"),
                    ("low_rejected_samples", "low_rejected_samples"),
                    ("high_rejected_samples", "high_rejected_samples"),
                    ("rejected_samples", "rejected_samples"),
                    ("output_coverage_zero_pixels", "output_coverage_zero_pixels"),
                    ("output_low_rejected_pixels", "output_low_rejected_pixels"),
                    ("output_high_rejected_pixels", "output_high_rejected_pixels"),
                ):
                    _add_int(dq_provenance, target_key, tile_provenance.get(source_key))
                if dq_provenance["rejection_policy"] is None:
                    dq_provenance["rejection_policy"] = tile_provenance.get("rejection_policy")
                source_flag_counts = tile_provenance.get("input_dq_flag_counts")
                if isinstance(source_flag_counts, dict):
                    for key, value in source_flag_counts.items():
                        dq_provenance["input_dq_flag_counts"][str(key)] = (
                            _int_value(dq_provenance["input_dq_flag_counts"].get(str(key))) + _int_value(value)
                        )
                tile_contract = tile_provenance.get("result_contract")
                if isinstance(tile_contract, dict):
                    tile_contracts.append(_compact_tile_contract(window, tile_contract))
                else:
                    tile_contracts.append(
                        {
                            "tile": {"y0": tile.y0, "y1": tile.y1, "x0": tile.x0, "x1": tile.x1},
                            "passed": False,
                            "status": "missing",
                            "contract_type": None,
                            "failed_checks": ["missing_result_contract"],
                        }
                    )
                tile_count += 1

        dq_provenance["output_dq_summary"] = dict(dq_summary)
        stack_engine_metrics["streaming_tile_contract_count"] = len(tile_contracts)
        stack_engine_metrics["streaming_tile_contract_failed_count"] = len(
            [item for item in tile_contracts if not bool(item.get("passed"))]
        )
        if variance_count:
            stack_engine_metrics["variance_mean"] = variance_sum / float(variance_count)
            stack_engine_metrics["variance_max"] = variance_max
        result_contract = _stack_engine_streaming_result_contract(
            width=width,
            height=height,
            request=request,
            requested_maps=requested_maps,
            output_paths=output_paths,
            metrics=stack_engine_metrics,
            dq_provenance=dq_provenance,
            tile_contracts=tile_contracts,
            tile_count=tile_count,
        )
        dq_provenance["result_contract"] = result_contract
        dq_provenance["streaming_tile_contracts"] = tile_contracts
        stack_engine_metrics["result_contract_passed"] = bool(result_contract["passed"])
        stack_engine_metrics["dq_provenance"] = dq_provenance
    return tile_count, stack_engine_metrics, method, dq_summary, dq_provenance


def integrate_registered_frames(
    run_dir: str | Path,
    plan_path: str | Path | None = None,
    backend: str = "auto",
    tile_size: int = 512,
    weighting_override: str | None = None,
    rejection_override: str | None = None,
) -> dict[str, Any]:
    run = Path(run_dir)
    frames, policy = _plan_data(plan_path)
    source_stage, records = _source_records(run)
    if not records:
        raise ValueError("no registered or local-normalized frames are available for integration")

    combine = str(policy.get("combine") or "mean")
    if combine != "mean":
        raise ValueError(f"unsupported integration combine mode: {combine}")
    weighting = _policy_value(policy, "weighting", weighting_override, "none")
    rejection = _policy_value(policy, "rejection", rejection_override, "none")
    output_variance_map = _output_variance_map_enabled(policy)
    low_sigma = float(policy.get("low_sigma") or 3.0)
    high_sigma = float(policy.get("high_sigma") or 3.0)
    rejection_min_samples = int(policy.get("rejection_min_samples", policy.get("min_samples", 3)))
    rejection_max_fraction = float(
        policy.get("rejection_max_fraction", policy.get("max_reject_fraction", 0.5))
    )
    frame_weights = _quality_weights(run, records, weighting)
    cuda_module = _cuda_module_if_requested(backend)
    engine_selection = _integration_engine_selection(
        backend=backend,
        rejection=rejection,
        cuda_module=cuda_module,
        policy=policy,
    )

    by_filter: dict[str, list[dict[str, Any]]] = {}
    for item in records:
        filt = frames.get(item["frame_id"], {}).get("filter")
        by_filter.setdefault(_safe_filter_name(None if filt is None else str(filt)), []).append(item)

    out_dir = run / "integration"
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, Any]] = []

    for filt, items in by_filter.items():
        with ExitStack() as stack:
            source_readers = [stack.enter_context(FitsImageReader(item["path"])) for item in items]
            coverage_readers = [stack.enter_context(FitsImageReader(item["coverage_path"])) for item in items]
            height, width = source_readers[0].shape
            master_path = out_dir / f"master_{filt}.fits"
            weight_path = out_dir / f"weight_map_{filt}.fits"
            coverage_path = out_dir / f"coverage_map_{filt}.fits"
            variance_path = out_dir / f"variance_map_{filt}.fits"
            low_path = out_dir / f"low_rejection_{filt}.fits"
            high_path = out_dir / f"high_rejection_{filt}.fits"
            dq_path = out_dir / f"dq_map_{filt}.fits"
            tile_count = 0
            actual_backend = str(engine_selection["actual_backend"])
            use_stack_engine = bool(engine_selection["use_stack_engine"])
            tile_stack_mode = str(engine_selection["tile_stack_mode"])
            stack_engine_metrics: dict[str, Any] | None = None
            stack_engine_rejection_method: str | None = None
            stack_engine_dq_provenance: dict[str, Any] | None = None
            dq_summary: dict[str, int] = {}

            if use_stack_engine:
                (
                    tile_count,
                    stack_engine_metrics,
                    stack_engine_rejection_method,
                    dq_summary,
                    stack_engine_dq_provenance,
                ) = _integrate_with_stack_engine(
                    items,
                    frame_weights,
                    rejection,
                    low_sigma,
                    high_sigma,
                    tile_size,
                    master_path,
                    weight_path,
                    coverage_path,
                    variance_path,
                    low_path,
                    high_path,
                    dq_path,
                    weighting,
                    output_variance_map,
                    rejection_min_samples,
                    rejection_max_fraction,
                )
            else:
                master_writer = stack.enter_context(
                    FitsTileWriter(master_path, width, height, {"IMAGETYP": "master"})
                )
                weight_writer = stack.enter_context(
                    FitsTileWriter(weight_path, width, height, {"IMAGETYP": "weight"})
                )
                coverage_writer = stack.enter_context(
                    FitsTileWriter(coverage_path, width, height, {"IMAGETYP": "coverage"})
                )
                variance_writer = (
                    stack.enter_context(FitsTileWriter(variance_path, width, height, {"IMAGETYP": "variance"}))
                    if output_variance_map
                    else None
                )
                low_writer = stack.enter_context(FitsTileWriter(low_path, width, height, {"IMAGETYP": "lowrej"}))
                high_writer = stack.enter_context(FitsTileWriter(high_path, width, height, {"IMAGETYP": "highrej"}))
                dq_writer = stack.enter_context(FitsTileWriter(dq_path, width, height, dq_header("integration")))
                for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                    weights = np.asarray([frame_weights[item["frame_id"]] for item in items], dtype=np.float32)
                    sum_tile = None
                    sumsq_tile = None
                    weight_sum_tile = None
                    coverage_map = None
                    for src_reader, cov_reader, weight in zip(source_readers, coverage_readers, weights, strict=True):
                        frame_tile = src_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                        cov_tile = cov_reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
                        if sum_tile is None:
                            sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                            sumsq_tile = np.zeros_like(frame_tile, dtype=np.float32)
                            weight_sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                            coverage_map = np.zeros_like(frame_tile, dtype=np.float32)
                        weight_tile = np.where(cov_tile > 0.5, weight, 0.0).astype(np.float32)
                        if cuda_module is not None:
                            sum_tile, weight_sum_tile = cuda_module.integrate_accumulate_mean_tile_f32(
                                frame_tile, weight_tile, sum_tile, weight_sum_tile
                            )
                        else:
                            sum_tile += frame_tile * weight_tile
                            weight_sum_tile += weight_tile
                        sumsq_tile += frame_tile * frame_tile * weight_tile
                        coverage_map += (cov_tile > 0.5).astype(np.float32)
                    if sum_tile is None or sumsq_tile is None or weight_sum_tile is None or coverage_map is None:
                        raise ValueError("no frames available for integration tile")
                    master = np.divide(
                        sum_tile,
                        weight_sum_tile,
                        out=np.zeros_like(sum_tile, dtype=np.float32),
                        where=weight_sum_tile > 0,
                    )
                    weight_map = weight_sum_tile.astype(np.float32)
                    variance_map = np.divide(
                        sumsq_tile,
                        weight_sum_tile,
                        out=np.zeros_like(sumsq_tile, dtype=np.float32),
                        where=weight_sum_tile > 0,
                    ) - master * master
                    variance_map = np.maximum(variance_map, 0.0).astype(np.float32)
                    low_map = np.zeros_like(master, dtype=np.float32)
                    high_map = np.zeros_like(master, dtype=np.float32)
                    master_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, master)
                    weight_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, weight_map)
                    coverage_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, coverage_map)
                    if variance_writer is not None:
                        variance_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, variance_map)
                    low_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, low_map)
                    high_writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, high_map)
                    tile_dq = dq_mask_from_coverage(coverage_map, DQFlag.NO_DATA)
                    write_dq_tile(dq_writer, tile, tile_dq)
                    add_summary_counts(dq_summary, tile_dq.summary())
                    tile_count += 1
        outputs.append(
            {
                "filter": filt,
                "frame_count": len(items),
                "master_path": str(master_path),
                "weight_map_path": str(weight_path),
                "coverage_map_path": str(coverage_path),
                "variance_map_path": str(variance_path) if output_variance_map else None,
                "low_rejection_map_path": str(low_path),
                "high_rejection_map_path": str(high_path),
                "dq_map_path": str(dq_path),
                "dq_summary": dq_summary,
                "tile_size": tile_size,
                "tile_count": tile_count,
                "backend": actual_backend,
                "tile_stack_mode": tile_stack_mode,
                "stack_engine_enabled": use_stack_engine,
                "engine_selection": engine_selection,
                "stack_engine_metrics": stack_engine_metrics,
                "stack_engine_rejection_method": stack_engine_rejection_method,
                "stack_engine_dq_provenance": stack_engine_dq_provenance,
                "dq_provenance_summary": dq_provenance_summary_from_stack_engine(
                    stack_engine_dq_provenance,
                    stage="integration",
                    item=filt,
                )
                if stack_engine_dq_provenance
                else None,
                "output_variance_map": output_variance_map,
            }
        )

    payload = {
        "schema_version": 1,
        "source_stage": source_stage,
        "combine": combine,
        "weighting": weighting,
        "rejection": rejection,
        "low_sigma": low_sigma,
        "high_sigma": high_sigma,
        "frame_weights": frame_weights,
        "output_variance_map": output_variance_map,
        "integration_engine_policy": engine_selection,
        "outputs": outputs,
    }
    write_json(run / "integration_results.json", payload)
    from glass.engine.frame_accounting import build_frame_accounting

    build_frame_accounting(run)
    return payload
