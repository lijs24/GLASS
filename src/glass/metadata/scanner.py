from __future__ import annotations

from collections import Counter
from pathlib import Path

from glass.io.paths import iter_image_paths
from glass.metadata.fits_reader import read_fits_metadata
from glass.metadata.xisf_reader import read_xisf_metadata
from glass.models import FrameRecord, now_iso, to_jsonable


def scan_file(path: str | Path, frame_id: str) -> FrameRecord:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".fit", ".fits", ".fts"}:
        return read_fits_metadata(p, frame_id)
    if suffix == ".xisf":
        return read_xisf_metadata(p, frame_id)
    raise ValueError(f"unsupported image format: {p.suffix}")


def scan_tree(root: str | Path) -> dict[str, object]:
    frames: list[FrameRecord] = []
    warnings: list[dict[str, str]] = []
    for index, path in enumerate(iter_image_paths(root), start=1):
        frame_id = f"F{index:06d}"
        try:
            frames.append(scan_file(path, frame_id))
        except Exception as exc:
            warnings.append({"path": str(path), "warning": str(exc)})
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": str(Path(root)),
        "frames": [to_jsonable(frame) for frame in frames],
        "warnings": warnings,
        "summary": summarize_frames(frames),
    }


def summarize_frames(frames: list[FrameRecord]) -> dict[str, object]:
    return {
        "count": len(frames),
        "frame_type": dict(Counter(frame.frame_type for frame in frames)),
        "filter": dict(Counter(frame.filter or "none" for frame in frames)),
        "exposure_s": dict(Counter(str(frame.exposure_s) for frame in frames)),
        "gain": dict(Counter(str(frame.gain) for frame in frames)),
        "temperature_c": dict(Counter(str(frame.temperature_c) for frame in frames)),
        "shape": dict(Counter(f"{frame.width}x{frame.height}" for frame in frames)),
    }

