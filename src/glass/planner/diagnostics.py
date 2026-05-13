from __future__ import annotations

from glass.models import FrameRecord


def metadata_warnings(frames: list[FrameRecord]) -> list[str]:
    warnings: list[str] = []
    for frame in frames:
        for warning in frame.warnings:
            warnings.append(f"{frame.id}: {warning}")
    return warnings

