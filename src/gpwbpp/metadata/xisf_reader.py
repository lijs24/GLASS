from __future__ import annotations

import re
from pathlib import Path

from gpwbpp.metadata.header_map import as_float, as_int, normalize_frame_type
from gpwbpp.models import FrameRecord


_ATTR_RE = re.compile(r'name="([^"]+)"[^>]*value="([^"]*)"')
_GEOM_RE = re.compile(r'geometry="(\d+):(\d+):')


def read_xisf_metadata(path: str | Path, frame_id: str) -> FrameRecord:
    p = Path(path)
    warnings = ["xisf metadata parser is provisional and reads only the XML prefix"]
    raw = p.read_bytes()[:4 * 1024 * 1024]
    text = raw.decode("utf-8", errors="ignore")
    attrs = {name.upper(): value for name, value in _ATTR_RE.findall(text)}
    geom = _GEOM_RE.search(text)
    width = as_int(geom.group(1)) if geom else None
    height = as_int(geom.group(2)) if geom else None
    frame_type = normalize_frame_type(
        attrs.get("IMAGETYP") or attrs.get("FRAME") or attrs.get("OBSTYPE")
    )
    if frame_type == "unknown":
        warnings.append("unknown frame type")
    return FrameRecord(
        id=frame_id,
        path=str(p),
        file_format="xisf",
        frame_type=frame_type,  # type: ignore[arg-type]
        filter=attrs.get("FILTER"),
        exposure_s=as_float(attrs.get("EXPTIME") or attrs.get("EXPOSURE")),
        gain=as_float(attrs.get("GAIN")),
        offset=as_float(attrs.get("OFFSET")),
        temperature_c=as_float(attrs.get("CCD-TEMP") or attrs.get("SET-TEMP")),
        binning_x=as_int(attrs.get("XBINNING") or attrs.get("BINX")),
        binning_y=as_int(attrs.get("YBINNING") or attrs.get("BINY")),
        width=width,
        height=height,
        camera=attrs.get("INSTRUME") or attrs.get("CAMERA"),
        date_obs=attrs.get("DATE-OBS") or attrs.get("DATE"),
        object_name=attrs.get("OBJECT"),
        ra=attrs.get("RA"),
        dec=attrs.get("DEC"),
        header_summary=attrs,
        warnings=warnings,
    )

