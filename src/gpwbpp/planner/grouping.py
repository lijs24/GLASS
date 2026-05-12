from __future__ import annotations

import hashlib
from collections import defaultdict

from gpwbpp.models import FrameGroup, FrameRecord


def _stable_group_id(parts: tuple[object, ...]) -> str:
    digest = hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:10]
    return f"G{digest}"


def group_frames(frames: list[FrameRecord]) -> list[FrameGroup]:
    buckets: dict[tuple[object, ...], list[FrameRecord]] = defaultdict(list)
    for frame in frames:
        if frame.frame_type == "unknown":
            continue
        key = (
            frame.frame_type,
            frame.filter if frame.frame_type in {"flat", "light"} else None,
            frame.exposure_s if frame.frame_type in {"dark", "light"} else None,
            frame.gain,
            frame.offset,
            frame.temperature_c,
            frame.binning_x,
            frame.binning_y,
            frame.width,
            frame.height,
        )
        buckets[key].append(frame)
    groups: list[FrameGroup] = []
    for key, bucket in sorted(buckets.items(), key=lambda item: str(item[0])):
        group_type, filt, exposure, gain, offset, temp, bin_x, bin_y, width, height = key
        groups.append(
            FrameGroup(
                group_id=_stable_group_id(key),
                group_type=str(group_type),
                filter=filt if filt is None else str(filt),
                exposure_s=exposure if isinstance(exposure, (float, int)) or exposure is None else None,
                gain=gain if isinstance(gain, (float, int)) or gain is None else None,
                offset=offset if isinstance(offset, (float, int)) or offset is None else None,
                temperature_c=temp if isinstance(temp, (float, int)) or temp is None else None,
                binning=(bin_x, bin_y),  # type: ignore[arg-type]
                shape=(width, height),  # type: ignore[arg-type]
                frames=[frame.id for frame in bucket],
            )
        )
    return groups

