from __future__ import annotations

from pathlib import Path
from typing import Any

from gpwbpp.cpu.calibration import calibrate_light
from gpwbpp.cpu.master_frames import make_master_bias, make_master_dark, make_master_flat
from gpwbpp.gpu.tile_scheduler import iter_tiles
from gpwbpp.io.fits_io import FitsTileWriter, open_fits_image, read_fits_data, write_fits_data
from gpwbpp.io.json_io import read_json, write_json
from gpwbpp.models import CalibrationPolicy, PipelineArtifact, RunState, now_iso


def initialize_run(run_dir: str | Path) -> RunState:
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    return RunState(run_id=Path(run_dir).name or "gpwbpp-run", created_at=now_iso(), current_stage="created")


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    if isinstance(raw, dict):
        return CalibrationPolicy(**raw)
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
        import gpwbpp_cuda
    except Exception:
        return None
    if gpwbpp_cuda.cuda_available():
        return gpwbpp_cuda
    if backend == "cuda":
        raise RuntimeError("CUDA backend requested but native CUDA backend is unavailable")
    return None


def _calibrate_light_to_cache_streaming(
    frame: dict[str, Any],
    path: Path,
    bias: Any,
    dark: Any,
    flat: Any,
    dark_exposure: float | None,
    policy: CalibrationPolicy,
    backend: str,
    tile_size: int,
) -> dict[str, Any]:
    cuda_module = _cuda_module_if_requested(backend)
    with open_fits_image(frame["path"], memmap=True) as hdul:
        light = hdul[0].data
        if light is None:
            raise ValueError(f"FITS file has no primary image data: {frame['path']}")
        height, width = light.shape
        with FitsTileWriter(
            path,
            width=width,
            height=height,
            header={
                "IMAGETYP": "calibrated_light",
                "FILTER": frame.get("filter"),
                "EXPTIME": frame.get("exposure_s"),
            },
        ) as writer:
            tile_count = 0
            for tile in iter_tiles(width=width, height=height, tile_size=tile_size):
                light_tile = light[tile.y0 : tile.y1, tile.x0 : tile.x1]
                bias_tile = None if bias is None else bias[tile.y0 : tile.y1, tile.x0 : tile.x1]
                dark_tile = None if dark is None else dark[tile.y0 : tile.y1, tile.x0 : tile.x1]
                flat_tile = None if flat is None else flat[tile.y0 : tile.y1, tile.x0 : tile.x1]
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
                writer.write_tile(tile.y0, tile.y1, tile.x0, tile.x1, calibrated_tile)
                tile_count += 1
    return {
        "frame_id": frame["id"],
        "path": str(path),
        "backend": actual_backend,
        "tile_size": tile_size,
        "tile_count": tile_count,
    }


def run_calibration_stages(
    plan_path: str | Path, run_dir: str | Path, backend: str = "auto", tile_size: int = 512
) -> RunState:
    plan = read_json(plan_path)
    out = Path(run_dir)
    out.mkdir(parents=True, exist_ok=True)
    state = initialize_run(out)
    state.current_stage = "master_calibration"

    frames = _frame_map(plan)
    groups = _group_map(plan)
    policy = _policy_from_plan(plan)
    master_dir = out / "calib_cache" / "masters"
    calibrated_dir = out / "calib_cache" / "calibrated"
    master_dir.mkdir(parents=True, exist_ok=True)
    calibrated_dir.mkdir(parents=True, exist_ok=True)

    master_data: dict[str, Any] = {}
    master_metadata: dict[str, Any] = {}

    try:
        for group_id, group in groups.items():
            group_type = group.get("group_type")
            if group_type != "bias":
                continue
            result = make_master_bias(_paths_for_group(group, frames))
            path = master_dir / f"master_bias_{group_id}.fits"
            write_fits_data(path, result.data, {"IMAGETYP": "master_bias"})
            master_data[group_id] = result.data
            master_metadata[group_id] = {"path": str(path), "stats": result.stats, "type": "bias"}

        for group_id, group in groups.items():
            group_type = group.get("group_type")
            if group_type != "dark":
                continue
            bias_group = None if policy.master_dark_includes_bias else _find_matching_bias_for_group(group, groups)
            result = make_master_dark(
                _paths_for_group(group, frames),
                master_bias=master_data.get(bias_group) if bias_group else None,
            )
            path = master_dir / f"master_dark_{group_id}.fits"
            write_fits_data(path, result.data, {"IMAGETYP": "master_dark", "EXPTIME": group.get("exposure_s")})
            master_data[group_id] = result.data
            master_metadata[group_id] = {
                "path": str(path),
                "stats": result.stats,
                "type": "dark",
                "exposure_s": group.get("exposure_s"),
                "master_dark_includes_bias": policy.master_dark_includes_bias,
            }

        for group_id, group in groups.items():
            group_type = group.get("group_type")
            if group_type != "flat":
                continue
            bias_group = _find_matching_bias_for_group(group, groups)
            result = make_master_flat(
                _paths_for_group(group, frames),
                master_bias=master_data.get(bias_group) if bias_group else None,
                normalization=policy.flat_normalization,
                flat_floor=policy.flat_floor,
            )
            path = master_dir / f"master_flat_{group_id}.fits"
            write_fits_data(path, result.data, {"IMAGETYP": "master_flat", "FILTER": group.get("filter")})
            master_data[group_id] = result.data
            master_metadata[group_id] = {
                "path": str(path),
                "stats": result.stats,
                "type": "flat",
                "filter": group.get("filter"),
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
            dark = master_data.get(dark_group)
            flat = master_data.get(flat_group)
            bias = master_data.get(bias_group) if bias_group else None
            dark_exposure = groups.get(dark_group, {}).get("exposure_s") if dark_group else None
            for frame_id in light_plan.get("frames", []):
                frame = frames[frame_id]
                path = calibrated_dir / f"calibrated_{frame_id}.fits"
                calibrated.append(
                    _calibrate_light_to_cache_streaming(
                        frame,
                        path,
                        bias,
                        dark,
                        flat,
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
