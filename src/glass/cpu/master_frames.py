from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from glass.engine.contracts import DQMask, CombinePolicy, OutputMapPolicy, RejectionPolicy, StackRequest
from glass.engine.stack_engine import CPUStackEngine
from glass.io.image_source import image_source_for_path


@dataclass(slots=True)
class MasterFrameResult:
    data: np.ndarray
    stats: dict[str, float]
    engine: str = "stack_engine_cpu"
    metrics: dict[str, Any] | None = None
    dq_provenance: dict[str, Any] | None = None
    dq_mask: DQMask | None = None


def image_stats(data: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "std": float(np.std(data)),
    }


def _copy_result_metadata(result: MasterFrameResult, *, operation: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    metrics = dict(result.metrics or {})
    metrics["master_postprocess_operation"] = operation
    provenance = dict(result.dq_provenance or {}) if result.dq_provenance is not None else None
    return metrics, provenance


def mean_stack(
    paths: list[str | Path],
    *,
    tile_size: int = 512,
    output_dq: bool = True,
) -> MasterFrameResult:
    if not paths:
        raise ValueError("cannot stack an empty frame list")
    with ExitStack() as stack:
        sources = {
            f"frame-{index}": stack.enter_context(image_source_for_path(path))
            for index, path in enumerate(paths)
        }
        request = StackRequest(
            frame_ids=tuple(sources.keys()),
            source_kind="unknown",
            combine=CombinePolicy(method="mean", accumulator_dtype="float64"),
            rejection=RejectionPolicy(method="none", iterations=0),
            output_maps=OutputMapPolicy(
                coverage=output_dq,
                weight=False,
                variance=False,
                low_rejection=output_dq,
                high_rejection=output_dq,
                dq=output_dq,
            ),
            metadata={
                "stage": "cpu_master_frame_helper",
                "public_helper": "glass.cpu.master_frames.mean_stack",
            },
        )
        stack_result = CPUStackEngine(tile_size=tile_size).stack(request, sources)
    metrics = dict(stack_result.metrics)
    metrics["engine"] = "stack_engine_cpu"
    metrics["public_helper"] = "glass.cpu.master_frames.mean_stack"
    dq_provenance = dict(stack_result.dq_provenance)
    return MasterFrameResult(
        np.asarray(stack_result.master, dtype=np.float32),
        image_stats(stack_result.master),
        engine="stack_engine_cpu",
        metrics=metrics,
        dq_provenance=dq_provenance,
        dq_mask=stack_result.dq_mask,
    )


def make_master_bias(paths: list[str | Path], *, tile_size: int = 512, output_dq: bool = True) -> MasterFrameResult:
    result = mean_stack(paths, tile_size=tile_size, output_dq=output_dq)
    metrics, provenance = _copy_result_metadata(result, operation="bias_mean")
    return MasterFrameResult(
        result.data,
        result.stats,
        engine=result.engine,
        metrics=metrics,
        dq_provenance=provenance,
        dq_mask=result.dq_mask,
    )


def make_master_dark(
    paths: list[str | Path],
    master_bias: np.ndarray | None = None,
    *,
    tile_size: int = 512,
    output_dq: bool = True,
) -> MasterFrameResult:
    result = mean_stack(paths, tile_size=tile_size, output_dq=output_dq)
    operation = "dark_mean"
    if master_bias is None:
        metrics, provenance = _copy_result_metadata(result, operation=operation)
        return MasterFrameResult(
            result.data,
            result.stats,
            engine=result.engine,
            metrics=metrics,
            dq_provenance=provenance,
            dq_mask=result.dq_mask,
        )
    data = (result.data - master_bias).astype(np.float32)
    metrics, provenance = _copy_result_metadata(result, operation="dark_mean_minus_master_bias")
    return MasterFrameResult(
        data,
        image_stats(data),
        engine=result.engine,
        metrics=metrics,
        dq_provenance=provenance,
        dq_mask=result.dq_mask,
    )


def make_master_flat(
    paths: list[str | Path],
    master_bias: np.ndarray | None = None,
    master_flat_dark: np.ndarray | None = None,
    normalization: str = "median",
    flat_floor: float = 1.0e-6,
    *,
    tile_size: int = 512,
    output_dq: bool = True,
) -> MasterFrameResult:
    result = mean_stack(paths, tile_size=tile_size, output_dq=output_dq)
    data = result.data.astype(np.float32)
    if master_bias is not None:
        data = data - master_bias
    if master_flat_dark is not None:
        data = data - master_flat_dark
    norm = float(np.mean(data) if normalization == "mean" else np.median(data))
    if abs(norm) < flat_floor:
        raise ValueError("flat normalization is below flat_floor")
    data = np.maximum(data / norm, flat_floor).astype(np.float32)
    metrics, provenance = _copy_result_metadata(result, operation="flat_mean_calibrated_normalized")
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
        dq_provenance=provenance,
        dq_mask=result.dq_mask,
    )
