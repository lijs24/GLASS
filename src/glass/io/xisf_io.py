from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
from typing import Any

import numpy as np

from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import FitsTileWriter

__all__ = [
    "XisfImageReader",
    "XisfImageSpec",
    "cache_xisf_to_fits",
    "read_xisf_data",
    "read_xisf_header_prefix",
    "read_xisf_image_spec",
]


_MAGIC = b"XISF0100"
_LOCATION_RE = re.compile(r"attachment:(\d+):(\d+)")


@dataclass(frozen=True, slots=True)
class XisfImageSpec:
    width: int
    height: int
    channels: int
    sample_format: str
    dtype: np.dtype
    attachment_offset: int
    byte_count: int
    compression: str | None
    image_attributes: dict[str, str]
    fits_keywords: dict[str, str]
    properties: dict[str, str]
    xml_header_bytes: int | None = None

    @property
    def shape(self) -> tuple[int, int]:
        return self.height, self.width


def read_xisf_header_prefix(path: str | Path, max_bytes: int = 8 * 1024 * 1024) -> str:
    """Read only the XML header/prefix from an XISF file.

    Real XISF files begin with an 8-byte magic string and an unsigned 64-bit XML
    header length. Older tests in this repository used a plain XML prefix with
    the magic string embedded in the text; that form is still accepted for
    backwards-compatible fixtures.
    """

    p = Path(path)
    with p.open("rb") as f:
        prefix = f.read(16)
        if prefix.startswith(_MAGIC) and len(prefix) >= 16:
            header_length = struct.unpack("<Q", prefix[8:16])[0]
            file_size = p.stat().st_size
            if 0 < header_length <= file_size - 16:
                return f.read(header_length).decode("utf-8", errors="ignore")
        f.seek(0)
        return f.read(max_bytes).decode("utf-8", errors="ignore")


def _clean_xml_text(text: str) -> str:
    cleaned = text.replace("\x00", "")
    if cleaned.startswith(_MAGIC.decode("ascii")):
        cleaned = cleaned[len(_MAGIC) :]
    start = cleaned.find("<?xml")
    if start < 0:
        start = cleaned.find("<xisf")
    if start > 0:
        cleaned = cleaned[start:]
    end = cleaned.rfind("</xisf>")
    if end >= 0:
        cleaned = cleaned[: end + len("</xisf>")]
    return cleaned.strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _strip_fits_string(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _xml_header_length(path: Path) -> int | None:
    with path.open("rb") as f:
        prefix = f.read(16)
    if prefix.startswith(_MAGIC) and len(prefix) >= 16:
        return int(struct.unpack("<Q", prefix[8:16])[0])
    return None


def _parse_xisf_xml(path: str | Path) -> tuple[ET.Element, int | None]:
    p = Path(path)
    text = _clean_xml_text(read_xisf_header_prefix(p))
    if not text:
        raise ValueError(f"empty XISF XML header: {p}")
    return ET.fromstring(text), _xml_header_length(p)


def _first_image_element(root: ET.Element) -> ET.Element:
    for element in root.iter():
        if _local_name(str(element.tag)) == "Image":
            return element
    raise ValueError("XISF header has no Image element")


def _collect_fits_keywords(root: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for element in root.iter():
        if _local_name(str(element.tag)) != "FITSKeyword":
            continue
        name = element.attrib.get("name")
        if not name:
            continue
        value = _strip_fits_string(element.attrib.get("value"))
        if value is not None and name.upper() not in values:
            values[name.upper()] = value
    return values


def _collect_properties(root: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for element in root.iter():
        if _local_name(str(element.tag)) != "Property":
            continue
        prop_id = element.attrib.get("id")
        if not prop_id:
            continue
        value = element.attrib.get("value")
        if value is None:
            value = element.text
        if value is not None:
            values[prop_id] = _strip_fits_string(value) or ""
    return values


def _dtype_for_sample_format(sample_format: str) -> np.dtype:
    mapping = {
        "Float32": np.dtype("<f4"),
        "Float64": np.dtype("<f8"),
        "UInt8": np.dtype("<u1"),
        "UInt16": np.dtype("<u2"),
        "UInt32": np.dtype("<u4"),
        "Int16": np.dtype("<i2"),
        "Int32": np.dtype("<i4"),
    }
    if sample_format not in mapping:
        raise ValueError(f"unsupported XISF sampleFormat: {sample_format}")
    return mapping[sample_format]


def read_xisf_image_spec(path: str | Path) -> XisfImageSpec:
    root, header_bytes = _parse_xisf_xml(path)
    image = _first_image_element(root)
    geometry = str(image.attrib.get("geometry") or "")
    parts = geometry.split(":")
    if len(parts) < 3:
        raise ValueError(f"unsupported XISF geometry: {geometry!r}")
    width, height, channels = (int(parts[0]), int(parts[1]), int(parts[2]))
    sample_format = str(image.attrib.get("sampleFormat") or "")
    dtype = _dtype_for_sample_format(sample_format)
    location = str(image.attrib.get("location") or "")
    match = _LOCATION_RE.fullmatch(location)
    if match is None:
        raise ValueError(f"unsupported XISF location: {location!r}")
    compression = image.attrib.get("compression")
    byte_count = int(match.group(2))
    expected = width * height * channels * dtype.itemsize
    if byte_count != expected:
        raise ValueError(f"XISF attachment byte count mismatch: {byte_count} != {expected}")
    return XisfImageSpec(
        width=width,
        height=height,
        channels=channels,
        sample_format=sample_format,
        dtype=dtype,
        attachment_offset=int(match.group(1)),
        byte_count=byte_count,
        compression=compression,
        image_attributes={str(k): str(v) for k, v in image.attrib.items()},
        fits_keywords=_collect_fits_keywords(root),
        properties=_collect_properties(root),
        xml_header_bytes=header_bytes,
    )


class XisfImageReader:
    """Tile reader for uncompressed attachment-backed monochrome XISF images."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.spec: XisfImageSpec | None = None
        self.width = 0
        self.height = 0
        self.channels = 0
        self._file: Any | None = None

    def __enter__(self) -> "XisfImageReader":
        self.spec = read_xisf_image_spec(self.path)
        if self.spec.compression is not None:
            raise ValueError(f"compressed XISF attachments are not supported yet: {self.spec.compression}")
        if self.spec.channels != 1:
            raise ValueError(f"only monochrome XISF images are supported by the tile reader: {self.spec.channels}")
        self.width = self.spec.width
        self.height = self.spec.height
        self.channels = self.spec.channels
        self._file = self.path.open("rb")
        return self

    @property
    def shape(self) -> tuple[int, int]:
        return self.height, self.width

    def read_tile(self, y0: int, y1: int, x0: int, x1: int, dtype=np.float32) -> np.ndarray:
        if self.spec is None or self._file is None:
            raise RuntimeError("XisfImageReader is not open")
        if not (0 <= y0 < y1 <= self.height and 0 <= x0 < x1 <= self.width):
            raise ValueError("tile bounds exceed XISF image dimensions")
        itemsize = self.spec.dtype.itemsize
        row_bytes = self.width * itemsize
        tile_width = x1 - x0
        out = np.empty((y1 - y0, tile_width), dtype=self.spec.dtype)
        for row_index, y in enumerate(range(y0, y1)):
            offset = self.spec.attachment_offset + y * row_bytes + x0 * itemsize
            self._file.seek(offset)
            payload = self._file.read(tile_width * itemsize)
            if len(payload) != tile_width * itemsize:
                raise ValueError(f"short XISF tile read from {self.path}")
            out[row_index, :] = np.frombuffer(payload, dtype=self.spec.dtype, count=tile_width)
        return np.asarray(out, dtype=dtype)

    def read_full_into(self, output: np.ndarray) -> np.ndarray:
        if output.shape != self.shape:
            raise ValueError("output shape does not match XISF image shape")
        if output.dtype != np.float32:
            raise ValueError("read_full_into currently requires a float32 output buffer")
        for tile in iter_tiles(width=self.width, height=self.height, tile_size=512):
            output[tile.y0 : tile.y1, tile.x0 : tile.x1] = self.read_tile(tile.y0, tile.y1, tile.x0, tile.x1)
        return output

    def read_full(self, dtype=np.float32) -> np.ndarray:
        return self.read_tile(0, self.height, 0, self.width, dtype=dtype)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._file is not None:
            self._file.close()
        self._file = None
        self.spec = None


def read_xisf_data(path: str | Path, dtype=np.float32) -> np.ndarray:
    """Read an uncompressed attachment-backed monochrome XISF image."""

    with XisfImageReader(path) as reader:
        return reader.read_full(dtype=dtype)


def cache_xisf_to_fits(
    xisf_path: str | Path,
    fits_path: str | Path,
    tile_size: int = 512,
    header: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stream a supported XISF image into a GLASS-owned FITS cache file."""

    source = Path(xisf_path)
    target = Path(fits_path)
    with XisfImageReader(source) as reader, FitsTileWriter(
        target,
        width=reader.width,
        height=reader.height,
        header={"IMAGETYP": "xisf_cache", **(header or {})},
    ) as writer:
        tile_count = 0
        for tile in iter_tiles(width=reader.width, height=reader.height, tile_size=tile_size):
            writer.write_tile(
                tile.y0,
                tile.y1,
                tile.x0,
                tile.x1,
                reader.read_tile(tile.y0, tile.y1, tile.x0, tile.x1),
            )
            tile_count += 1
    spec = read_xisf_image_spec(source)
    return {
        "source_path": str(source),
        "cache_path": str(target),
        "width": spec.width,
        "height": spec.height,
        "channels": spec.channels,
        "sample_format": spec.sample_format,
        "tile_size": int(tile_size),
        "tile_count": tile_count,
        "compression": spec.compression,
    }
