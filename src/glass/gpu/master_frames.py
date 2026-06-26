from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.master_frames import MasterFrameResult, image_stats
from glass.engine.contracts import DQFlag, DQMask, CombinePolicy, OutputMapPolicy, RejectionPolicy, StackRequest
from glass.engine.stack_contract import build_stack_engine_result_contract
from glass.engine.stack_engine import StackEngineResult
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader


def _native_module():
    try:
        import glass_cuda
    except Exception:
        return None
    if not glass_cuda.cuda_available():
        return None
    return glass_cuda


def _mean_stack_tile_accumulator(
    readers: list[FitsImageReader],
    tile,
    native,
    use_native: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    sum_tile = None
    weight_sum_tile = None
    cpu_acc = None
    cpu_weight = None
    count = 0
    input_samples = 0
    input_valid_samples = 0
    input_invalid_samples = 0
    input_nonfinite_samples = 0
    for reader in readers:
        frame_tile = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
        finite = np.isfinite(frame_tile)
        safe_frame = np.where(finite, frame_tile, np.float32(0.0)).astype(np.float32, copy=False)
        valid_weight = finite.astype(np.float32)
        if use_native:
            if sum_tile is None:
                sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
                weight_sum_tile = np.zeros_like(frame_tile, dtype=np.float32)
            sum_tile, weight_sum_tile = native.integrate_accumulate_mean_tile_f32(
                safe_frame, valid_weight, sum_tile, weight_sum_tile
            )
        else:
            if cpu_acc is None:
                cpu_acc = np.zeros_like(frame_tile, dtype=np.float64)
                cpu_weight = np.zeros_like(frame_tile, dtype=np.float64)
            cpu_acc += safe_frame.astype(np.float64) * valid_weight.astype(np.float64)
            cpu_weight += valid_weight.astype(np.float64)
        input_samples += int(frame_tile.size)
        input_valid_samples += int(np.count_nonzero(finite))
        input_invalid_samples += int(np.count_nonzero(~finite))
        input_nonfinite_samples += int(np.count_nonzero(~finite))
        count += 1
    if count == 0:
        raise ValueError("cannot stack an empty frame list")
    if sum_tile is not None and weight_sum_tile is not None:
        master = np.divide(
            sum_tile,
            weight_sum_tile,
            out=np.zeros_like(sum_tile, dtype=np.float32),
            where=weight_sum_tile > 0,
        ).astype(np.float32)
        coverage = weight_sum_tile.astype(np.float32)
        return master, coverage, {
            "input_samples": input_samples,
            "input_valid_samples": input_valid_samples,
            "input_invalid_samples": input_invalid_samples,
            "input_nonfinite_samples": input_nonfinite_samples,
        }
    if cpu_acc is None or cpu_weight is None:
        raise ValueError("cannot stack an empty frame list")
    master = np.divide(
        cpu_acc,
        cpu_weight,
        out=np.zeros_like(cpu_acc, dtype=np.float64),
        where=cpu_weight > 0,
    ).astype(np.float32)
    coverage = cpu_weight.astype(np.float32)
    return master, coverage, {
        "input_samples": input_samples,
        "input_valid_samples": input_valid_samples,
        "input_invalid_samples": input_invalid_samples,
        "input_nonfinite_samples": input_nonfinite_samples,
    }


def _mean_stack_dq_provenance(metrics: dict[str, Any], dq_summary: dict[str, int]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "engine": metrics["engine"],
        "execution_path": metrics["execution_path"],
        "input_samples": int(metrics["input_samples"]),
        "input_valid_samples_before_rejection": int(metrics["input_valid_samples"]),
        "input_invalid_samples_before_rejection": int(metrics["input_invalid_samples"]),
        "input_flagged_samples": 0,
        "input_nonfinite_samples": int(metrics["input_nonfinite_samples"]),
        "input_dq_flag_counts": {
            flag.name.lower(): 0 for flag in DQFlag if flag != DQFlag.VALID
        },
        "valid_samples_after_rejection": int(metrics["valid_samples"]),
        "low_rejected_samples": 0,
        "high_rejected_samples": 0,
        "rejected_samples": 0,
        "output_coverage_zero_pixels": int(metrics["coverage_zero_pixels"]),
        "output_low_rejected_pixels": 0,
        "output_high_rejected_pixels": 0,
        "output_dq_summary": dict(dq_summary),
        "semantics": (
            "The GPU master-frame helper is a tile-streaming mean accumulator "
            "used for CUDA-vs-CPU master-frame parity checks. Finite source "
            "samples have weight 1 and non-finite source samples have weight 0. "
            "The output DQ mask marks pixels with no finite input samples as "
            "NO_DATA; source DQ sidecars are not consumed by this helper."
        ),
    }


def mean_stack_paths_tile_streaming(
    paths: list[str | Path], tile_size: int = 512
) -> MasterFrameResult:
    if not paths:
        raise ValueError("cannot stack an empty frame list")
    native = _native_module()
    use_native = native is not None and hasattr(native, "integrate_accumulate_mean_tile_f32")

    with ExitStack() as stack:
        readers = [stack.enter_context(FitsImageReader(path)) for path in paths]
        height, width = readers[0].shape
        out = np.empty((height, width), dtype=np.float32)
        coverage_map = np.empty((height, width), dtype=np.float32)
        for reader in readers[1:]:
            if reader.shape != (height, width):
                raise ValueError(f"shape mismatch while stacking: {reader.shape} != {(height, width)}")
        tile_count = 0
        input_samples = 0
        input_valid_samples = 0
        input_invalid_samples = 0
        input_nonfinite_samples = 0
        for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
            tile_master, tile_coverage, tile_metrics = _mean_stack_tile_accumulator(
                readers,
                tile,
                native,
                use_native,
            )
            out[tile.y0 : tile.y1, tile.x0 : tile.x1] = tile_master
            coverage_map[tile.y0 : tile.y1, tile.x0 : tile.x1] = tile_coverage
            input_samples += tile_metrics["input_samples"]
            input_valid_samples += tile_metrics["input_valid_samples"]
            input_invalid_samples += tile_metrics["input_invalid_samples"]
            input_nonfinite_samples += tile_metrics["input_nonfinite_samples"]
            tile_count += 1
        engine = "cuda_tile_streaming_mean" if use_native else "cpu_tile_streaming_mean_fallback"
        dq_mask = DQMask.empty((height, width))
        dq_mask.mark(DQFlag.NO_DATA, coverage_map <= 0)
        dq_summary = dq_mask.summary()
        valid_samples = int(round(float(np.sum(coverage_map, dtype=np.float64))))
        coverage_zero_pixels = int(np.count_nonzero(coverage_map <= 0))
        metrics: dict[str, Any] = {
            "engine": engine,
            "execution_path": "gpu_master_tile_streaming_mean",
            "public_helper": "glass.gpu.master_frames.mean_stack_paths_tile_streaming",
            "frame_count": len(paths),
            "width": width,
            "height": height,
            "tile_size": int(tile_size),
            "tile_count": tile_count,
            "combine": "mean",
            "rejection": "none",
            "cuda_native_available": native is not None,
            "cuda_accumulator_used": use_native,
            "dq_mask_produced": True,
            "coverage_map_produced_for_contract": True,
            "input_samples": input_samples,
            "input_valid_samples": input_valid_samples,
            "input_invalid_samples": input_invalid_samples,
            "input_nonfinite_samples": input_nonfinite_samples,
            "valid_samples": valid_samples,
            "low_rejected": 0,
            "high_rejected": 0,
            "rejected_samples": 0,
            "coverage_zero_pixels": coverage_zero_pixels,
            "dq_summary": dict(dq_summary),
        }
        dq_provenance = _mean_stack_dq_provenance(metrics, dq_summary)
        request = StackRequest(
            frame_ids=tuple(f"frame-{index}" for index in range(len(paths))),
            source_kind="unknown",
            combine=CombinePolicy(method="mean", accumulator_dtype="float64"),
            rejection=RejectionPolicy(method="none", iterations=0),
            output_maps=OutputMapPolicy(
                coverage=True,
                weight=False,
                variance=False,
                low_rejection=False,
                high_rejection=False,
                dq=True,
            ),
            metadata={"stage": "gpu_master_frame_helper"},
        )
        contract_result = StackEngineResult(
            master=out,
            coverage_map=coverage_map,
            dq_mask=dq_mask,
            dq_provenance=dq_provenance,
            metrics=metrics,
        )
        result_contract = build_stack_engine_result_contract(contract_result, request=request)
        dq_provenance["result_contract"] = result_contract
        metrics["result_contract_passed"] = bool(result_contract["passed"])
        return MasterFrameResult(
            out,
            image_stats(out),
            engine=engine,
            metrics=metrics,
            dq_provenance=dq_provenance,
            dq_mask=dq_mask,
        )


def make_master_bias(paths: list[str | Path], tile_size: int = 512) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = "bias_mean"
    return MasterFrameResult(
        result.data,
        result.stats,
        engine=result.engine,
        metrics=metrics,
        dq_provenance=result.dq_provenance,
        dq_mask=result.dq_mask,
    )


def make_master_dark(
    paths: list[str | Path], master_bias: np.ndarray | None = None, tile_size: int = 512
) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    if master_bias is None:
        metrics = dict(result.metrics or {})
        metrics["master_postprocess_operation"] = "dark_mean"
        return MasterFrameResult(
            result.data,
            result.stats,
            engine=result.engine,
            metrics=metrics,
            dq_provenance=result.dq_provenance,
            dq_mask=result.dq_mask,
        )
    data = (result.data - master_bias).astype(np.float32)
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = "dark_mean_minus_master_bias"
    return MasterFrameResult(
        data,
        image_stats(data),
        engine=result.engine,
        metrics=metrics,
        dq_provenance=result.dq_provenance,
        dq_mask=result.dq_mask,
    )


def make_master_flat(
    paths: list[str | Path],
    master_bias: np.ndarray | None = None,
    master_flat_dark: np.ndarray | None = None,
    normalization: str = "median",
    flat_floor: float = 1.0e-6,
    tile_size: int = 512,
) -> MasterFrameResult:
    result = mean_stack_paths_tile_streaming(paths, tile_size=tile_size)
    data = result.data.astype(np.float32)
    if master_bias is not None:
        data = data - master_bias
    if master_flat_dark is not None:
        data = data - master_flat_dark
    norm = float(np.mean(data) if normalization == "mean" else np.median(data))
    if abs(norm) < flat_floor:
        raise ValueError("flat normalization is below flat_floor")
    data = np.maximum(data / norm, flat_floor).astype(np.float32)
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = "flat_mean_calibrated_normalized"
    metrics["flat_normalization"] = str(normalization)
    metrics["flat_normalization_scalar"] = norm
    metrics["flat_floor"] = float(flat_floor)
    metrics["flat_subtracted_master_bias"] = master_bias is not None
    metrics["flat_subtracted_master_dark"] = master_flat_dark is not None
    return MasterFrameResult(
        data,
        image_stats(data),
        engine=result.engine,
        metrics=metrics,
        dq_provenance=result.dq_provenance,
        dq_mask=result.dq_mask,
    )


__all__ = [
    "mean_stack_paths_tile_streaming",
    "make_master_bias",
    "make_master_dark",
    "make_master_flat",
]
