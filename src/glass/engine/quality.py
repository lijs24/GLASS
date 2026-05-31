from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.metrics import combined_quality_weight, summarize_stars
from glass.cpu.star_detect import Star, detect_stars
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import FrameQuality, to_jsonable


@dataclass(slots=True)
class _QualityScan:
    median: float
    mean: float
    rms: float
    mad: float
    noise_mad: float
    pixel_count: int
    tile_count: int
    median_method: str


def _quality_gate_policy(run: Path) -> dict[str, Any]:
    plan_path = run / "processing_plan.json"
    plan = read_json(plan_path) if plan_path.exists() else {}
    registration_policy = plan.get("registration_policy", {}) if isinstance(plan, dict) else {}
    return {
        "min_stars": int(registration_policy.get("min_stars") or 8),
        "max_saturation_fraction": float(
            registration_policy.get(
                "quality_max_saturation_fraction",
                registration_policy.get("max_saturation_fraction", 0.02),
            )
        ),
        "min_quality_score": float(registration_policy.get("quality_min_score") or 0.0),
        "require_fwhm": bool(registration_policy.get("quality_require_fwhm", True)),
    }


def _apply_quality_gate(quality: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    star_count = int(quality.get("star_count") or 0)
    min_stars = int(policy["min_stars"])
    if star_count < min_stars:
        warnings.append(f"star_count {star_count} below min_stars={min_stars}")
    if bool(policy["require_fwhm"]) and quality.get("fwhm_px") is None:
        warnings.append("fwhm_px is unavailable")
    saturation_fraction = float(quality.get("saturation_fraction") or 0.0)
    max_saturation_fraction = float(policy["max_saturation_fraction"])
    if saturation_fraction > max_saturation_fraction:
        warnings.append(
            f"saturation_fraction {saturation_fraction:.6g} exceeds max_saturation_fraction={max_saturation_fraction}"
        )
    quality_score = float(quality.get("quality_score") or quality.get("weight") or 0.0)
    min_quality_score = float(policy["min_quality_score"])
    if quality_score < min_quality_score:
        warnings.append(f"quality_score {quality_score:.6g} below min_quality_score={min_quality_score}")
    quality["quality_gate_status"] = "accepted" if not warnings else "rejected"
    quality["quality_gate_warnings"] = warnings
    quality["reference_candidate"] = not warnings
    return quality


def _quality_gate_summary(qualities: list[dict[str, Any]], policy: dict[str, Any], fallback_used: bool) -> dict[str, Any]:
    accepted = [item for item in qualities if item.get("quality_gate_status") == "accepted"]
    rejected = [item for item in qualities if item.get("quality_gate_status") == "rejected"]
    reason_counts: dict[str, int] = {}
    for item in rejected:
        for warning in item.get("quality_gate_warnings", []):
            reason = str(warning).split(" ", 1)[0]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "policy": policy,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "reference_candidate_count": len(accepted),
        "fallback_used": fallback_used,
        "rejection_reason_counts": reason_counts,
    }


def _scan_quality_stats(path: str | Path, tile_size: int, scratch_path: Path) -> _QualityScan:
    import gc

    scratch_path.parent.mkdir(parents=True, exist_ok=True)
    scratch = None
    work = None
    try:
        with FitsImageReader(path) as reader:
            scratch = np.memmap(
                scratch_path,
                dtype=np.float32,
                mode="w+",
                shape=(reader.width * reader.height,),
            )
            count = 0
            tile_count = 0
            total = 0.0
            total_sq = 0.0
            for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
                values = reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1).ravel()
                finite = values[np.isfinite(values)]
                n = int(finite.size)
                if n:
                    scratch[count : count + n] = finite
                    count += n
                    finite64 = finite.astype(np.float64, copy=False)
                    total += float(np.sum(finite64))
                    total_sq += float(np.sum(finite64 * finite64))
                tile_count += 1
        if count == 0:
            raise ValueError(f"cannot measure quality: no finite pixels in {path}")
        work = scratch[:count]
        mid = count // 2
        work.partition(mid)
        median = float(work[mid])
        if count % 2 == 0:
            median = (float(np.max(work[:mid])) + median) / 2.0
        np.subtract(work, np.float32(median), out=work)
        np.abs(work, out=work)
        work.partition(mid)
        mad = float(work[mid])
        if count % 2 == 0:
            mad = (float(np.max(work[:mid])) + mad) / 2.0
        mean = total / count
        variance = max(total_sq / count - mean * mean, 0.0)
        rms = float(np.sqrt(variance))
        noise_mad = float(1.4826 * mad)
        if noise_mad <= 0.0:
            noise_mad = rms
        return _QualityScan(
            median=median,
            mean=float(mean),
            rms=rms,
            mad=mad,
            noise_mad=noise_mad,
            pixel_count=count,
            tile_count=tile_count,
            median_method="median_scratch_memmap",
        )
    finally:
        if scratch is not None:
            scratch.flush()
        del work
        del scratch
        gc.collect()
        scratch_path.unlink(missing_ok=True)


def _detect_stars_streaming(
    path: str | Path,
    median: float,
    rms: float,
    tile_size: int,
    threshold_sigma: float = 5.0,
    max_stars: int = 500,
    window_radius: int = 4,
) -> list[Star]:
    stars: list[Star] = []
    with FitsImageReader(path) as reader:
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            y0 = max(tile.y0 - window_radius, 0)
            y1 = min(tile.y1 + window_radius, reader.height)
            x0 = max(tile.x0 - window_radius, 0)
            x1 = min(tile.x1 + window_radius, reader.width)
            data = reader.read_tile(y0, y1, x0, x1)
            source_y0 = max(tile.y0, 1)
            source_y1 = min(tile.y1, reader.height - 1)
            source_x0 = max(tile.x0, 1)
            source_x1 = min(tile.x1, reader.width - 1)
            if source_y0 >= source_y1 or source_x0 >= source_x1:
                continue
            tile_stars = detect_stars(
                data,
                threshold_sigma=threshold_sigma,
                max_stars=max_stars,
                background=median,
                noise=rms,
                window_radius=window_radius,
                origin_x=x0,
                origin_y=y0,
            )
            for star in tile_stars:
                if source_x0 <= star.x < source_x1 and source_y0 <= star.y < source_y1:
                    stars.append(star)
            if len(stars) > max_stars * 4:
                stars.sort(key=lambda star: star.flux, reverse=True)
                del stars[max_stars:]
    stars.sort(key=lambda star: star.flux, reverse=True)
    return stars[:max_stars]


def detect_stars_streaming(
    path: str | Path,
    median: float,
    rms: float,
    tile_size: int = 512,
    threshold_sigma: float = 5.0,
    max_stars: int = 500,
) -> list[Star]:
    return _detect_stars_streaming(
        path,
        median,
        rms,
        tile_size=tile_size,
        threshold_sigma=threshold_sigma,
        max_stars=max_stars,
    )


def measure_quality_streaming(
    frame_id: str,
    filt: str | None,
    path: str | Path,
    tile_size: int = 512,
    scratch_dir: str | Path | None = None,
    saturated_pixels: int = 0,
) -> dict[str, Any]:
    scratch_root = Path(scratch_dir) if scratch_dir is not None else Path(path).parent
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch_path = scratch_root / f".quality_{frame_id}.median_scratch.bin"
    stats = _scan_quality_stats(path, tile_size, scratch_path)
    stars = _detect_stars_streaming(path, stats.median, stats.noise_mad or stats.rms, tile_size)
    star_metrics = summarize_stars(stars)
    snr = float(star_metrics["star_snr_median"] or 0.0)
    saturation_fraction = 0.0 if stats.pixel_count == 0 else float(max(saturated_pixels, 0) / stats.pixel_count)
    weight, components = combined_quality_weight(
        star_count=len(stars),
        star_snr=snr,
        fwhm_px=star_metrics["fwhm_median_px"],
        eccentricity=star_metrics["eccentricity_median"],
        background_rms=stats.rms,
        saturation_fraction=saturation_fraction,
    )
    quality = FrameQuality(
        frame_id=frame_id,
        filter=filt,
        background_median=stats.median,
        background_rms=stats.rms,
        star_count=len(stars),
        fwhm_px=star_metrics["fwhm_median_px"],
        eccentricity=star_metrics["eccentricity_median"],
        snr=snr,
        weight=weight,
        warnings=[] if stars else ["no stars detected"],
        background_mean=stats.mean,
        background_mad=stats.mad,
        noise_mad=stats.noise_mad,
        saturation_fraction=saturation_fraction,
        quality_score=weight,
        weight_source="combined_psf_snr_v1",
        weight_components=components,
        star_metrics=star_metrics,
    )
    payload = to_jsonable(quality)
    payload.update(
        {
            "metric_source": "streaming_tile_reader",
            "tile_size": tile_size,
            "tile_count": stats.tile_count,
            "pixel_count": stats.pixel_count,
            "median_method": stats.median_method,
            "star_detector": "robust_local_maximum_moments_v1",
        }
    )
    return payload


def measure_calibrated_quality(
    run_dir: str | Path,
    out_path: str | Path | None = None,
    tile_size: int = 512,
) -> dict[str, Any]:
    run = Path(run_dir)
    artifacts = read_json(run / "calibration_artifacts.json")
    gate_policy = _quality_gate_policy(run)
    scratch_dir = run / "quality_scratch"
    qualities = []
    for item in artifacts.get("calibrated_lights", []):
        dq_summary = item.get("dq_summary", {}) if isinstance(item, dict) else {}
        quality = _apply_quality_gate(
            measure_quality_streaming(
                item["frame_id"],
                None,
                item["path"],
                tile_size=tile_size,
                scratch_dir=scratch_dir,
                saturated_pixels=int(dq_summary.get("saturated") or 0),
            ),
            gate_policy,
        )
        qualities.append(quality)
    if scratch_dir.exists() and not any(scratch_dir.iterdir()):
        scratch_dir.rmdir()
    reference = None
    fallback_used = False
    if qualities:
        reference_candidates = [item for item in qualities if item.get("reference_candidate")]
        if not reference_candidates:
            reference_candidates = qualities
            fallback_used = True
        reference = max(
            reference_candidates,
            key=lambda q: (
                int(q.get("star_count") or 0),
                float(q.get("quality_score") or q.get("weight") or 0.0),
                -float(q.get("fwhm_px") or 999.0),
                -float(q.get("eccentricity") or 1.0),
                -float(q.get("background_rms") or 0.0),
            ),
        )["frame_id"]
    result = {
        "schema_version": 1,
        "frame_quality": qualities,
        "reference_frame_id": reference,
        "reference_selection": (
            "quality_gate accepted frames, then max star_count, max combined quality, "
            "min FWHM/eccentricity/background_rms"
        ),
        "reference_selection_fallback": fallback_used,
        "quality_gate_policy": gate_policy,
        "quality_gate_summary": _quality_gate_summary(qualities, gate_policy, fallback_used),
        "metric_source": "streaming_tile_reader",
        "tile_size": tile_size,
        "star_detector": "robust_local_maximum_moments_v1",
        "weight_source": "combined_psf_snr_v1",
    }
    write_json(out_path or (run / "frame_quality.json"), result)
    return result
