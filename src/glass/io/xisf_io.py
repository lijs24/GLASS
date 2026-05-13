from __future__ import annotations

from pathlib import Path
import re

import numpy as np

from glass.metadata.xisf_reader import read_xisf_metadata

__all__ = ["read_xisf_metadata", "read_xisf_data", "read_xisf_header_prefix"]


_GEOMETRY_RE = re.compile(r'geometry="(\d+):(\d+):(\d+)"')
_LOCATION_RE = re.compile(r'location="attachment:(\d+):(\d+)"')
_SAMPLE_FORMAT_RE = re.compile(r'sampleFormat="([^"]+)"')
_COMPRESSION_RE = re.compile(r'compression="([^"]+)"')


def read_xisf_header_prefix(path: str | Path, max_bytes: int = 8 * 1024 * 1024) -> str:
    data = Path(path).read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def _dtype_for_sample_format(sample_format: str) -> np.dtype:
    mapping = {
        "Float32": np.dtype("<f4"),
        "Float64": np.dtype("<f8"),
        "UInt16": np.dtype("<u2"),
        "UInt32": np.dtype("<u4"),
        "Int16": np.dtype("<i2"),
        "Int32": np.dtype("<i4"),
    }
    if sample_format not in mapping:
        raise ValueError(f"unsupported XISF sampleFormat: {sample_format}")
    return mapping[sample_format]


def read_xisf_data(path: str | Path, dtype=np.float32) -> np.ndarray:
    """Read an uncompressed attachment-backed XISF image.

    This intentionally implements the narrow subset needed for GLASS
    black-box validation: attachment-backed monochrome Float32/Float64/integer
    images. Compressed blocks and multi-image XISF containers are left for later
    gates and fail explicitly.
    """

    p = Path(path)
    text = read_xisf_header_prefix(p)
    geometry = _GEOMETRY_RE.search(text)
    location = _LOCATION_RE.search(text)
    sample = _SAMPLE_FORMAT_RE.search(text)
    if geometry is None or location is None or sample is None:
        raise ValueError(f"unsupported or incomplete XISF image metadata: {p}")
    compression = _COMPRESSION_RE.search(text)
    if compression is not None:
        raise ValueError(f"compressed XISF attachments are not supported yet: {compression.group(1)}")

    width = int(geometry.group(1))
    height = int(geometry.group(2))
    channels = int(geometry.group(3))
    offset = int(location.group(1))
    byte_count = int(location.group(2))
    source_dtype = _dtype_for_sample_format(sample.group(1))
    expected = width * height * channels * source_dtype.itemsize
    if byte_count != expected:
        raise ValueError(f"XISF attachment byte count mismatch: {byte_count} != {expected}")

    with p.open("rb") as f:
        f.seek(offset)
        payload = f.read(byte_count)
    if len(payload) != byte_count:
        raise ValueError(f"short XISF attachment read: {len(payload)} != {byte_count}")

    data = np.frombuffer(payload, dtype=source_dtype)
    if channels == 1:
        shaped = data.reshape((height, width))
    else:
        shaped = data.reshape((height, width, channels))
    return np.asarray(shaped, dtype=dtype)
