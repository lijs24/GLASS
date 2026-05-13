from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from glass.cpu.star_detect import Star
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsImageReader
from glass.io.json_io import read_json, write_json
from glass.models import FrameQuality, to_jsonable


@dataclass(slots=True)
class _QualityScan:
    median: float
    mean: float
    rms: float
    pixel_count: int
    tile_count: int
    median_method: str


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
        mean = total / count
        variance = max(total_sq / count - mean * mean, 0.0)
        return _QualityScan(
            median=median,
            mean=float(mean),
            rms=float(np.sqrt(variance)),
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
) -> list[Star]:
    threshold = median + threshold_sigma * max(rms, 1.0e-6)
    stars: list[Star] = []
    with FitsImageReader(path) as reader:
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            y0 = max(tile.y0 - 1, 0)
            y1 = min(tile.y1 + 1, reader.height)
            x0 = max(tile.x0 - 1, 0)
            x1 = min(tile.x1 + 1, reader.width)
            data = reader.read_tile(y0, y1, x0, x1)
            source_y0 = max(tile.y0, 1)
            source_y1 = min(tile.y1, reader.height - 1)
            source_x0 = max(tile.x0, 1)
            source_x1 = min(tile.x1, reader.width - 1)
            if source_y0 >= source_y1 or source_x0 >= source_x1:
                continue
            local_y0 = source_y0 - y0
            local_y1 = source_y1 - y0
            local_x0 = source_x0 - x0
            local_x1 = source_x1 - x0
            core = data[local_y0:local_y1, local_x0:local_x1]
            mask = np.isfinite(core) & (core > threshold)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = data[
                        local_y0 + dy : local_y1 + dy,
                        local_x0 + dx : local_x1 + dx,
                    ]
                    mask &= core >= neighbor
            ys, xs = np.nonzero(mask)
            for candidate_y, candidate_x in zip(ys, xs, strict=True):
                local_y = int(local_y0 + candidate_y)
                local_x = int(local_x0 + candidate_x)
                y = int(y0 + local_y)
                x = int(x0 + local_x)
                patch = data[local_y - 1 : local_y + 2, local_x - 1 : local_x + 2]
                yy, xx = np.mgrid[y - 1 : y + 2, x - 1 : x + 2]
                weights = np.maximum(patch - median, 0.0)
                total = float(np.sum(weights))
                if total <= 0:
                    continue
                stars.append(
                    Star(
                        x=float(np.sum(xx * weights) / total),
                        y=float(np.sum(yy * weights) / total),
                        flux=total,
                    )
                )
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
) -> dict[str, Any]:
    scratch_root = Path(scratch_dir) if scratch_dir is not None else Path(path).parent
    scratch_root.mkdir(parents=True, exist_ok=True)
    scratch_path = scratch_root / f".quality_{frame_id}.median_scratch.bin"
    stats = _scan_quality_stats(path, tile_size, scratch_path)
    stars = _detect_stars_streaming(path, stats.median, stats.rms, tile_size)
    snr = 0.0 if stats.rms == 0 else float(max((stats.mean - stats.median) / stats.rms, 0.0))
    quality = FrameQuality(
        frame_id=frame_id,
        filter=filt,
        background_median=stats.median,
        background_rms=stats.rms,
        star_count=len(stars),
        fwhm_px=3.0 if stars else None,
        eccentricity=0.0 if stars else None,
        snr=snr,
        weight=1.0 / max(stats.rms * stats.rms, 1.0e-6),
        warnings=[] if stars else ["no stars detected"],
    )
    payload = to_jsonable(quality)
    payload.update(
        {
            "metric_source": "streaming_tile_reader",
            "tile_size": tile_size,
            "tile_count": stats.tile_count,
            "pixel_count": stats.pixel_count,
            "median_method": stats.median_method,
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
    scratch_dir = run / "quality_scratch"
    qualities = []
    for item in artifacts.get("calibrated_lights", []):
        quality = measure_quality_streaming(
            item["frame_id"],
            None,
            item["path"],
            tile_size=tile_size,
            scratch_dir=scratch_dir,
        )
        qualities.append(quality)
    if scratch_dir.exists() and not any(scratch_dir.iterdir()):
        scratch_dir.rmdir()
    reference = None
    if qualities:
        reference = max(
            qualities,
            key=lambda q: (
                int(q.get("star_count") or 0),
                float(q.get("weight") or 0.0),
                -float(q.get("background_rms") or 0.0),
            ),
        )["frame_id"]
    result = {
        "schema_version": 1,
        "frame_quality": qualities,
        "reference_frame_id": reference,
        "reference_selection": "max star_count, then max weight, then min background_rms",
        "metric_source": "streaming_tile_reader",
        "tile_size": tile_size,
    }
    write_json(out_path or (run / "frame_quality.json"), result)
    return result
