from __future__ import annotations

from typing import Any


def first_header_value(header: dict[str, Any], names: list[str]) -> Any:
    upper = {str(k).upper(): v for k, v in header.items()}
    for name in names:
        if name.upper() in upper:
            return upper[name.upper()]
    return None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def normalize_frame_type(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    if "bias" in text or "zero" in text:
        return "bias"
    if "dark" in text:
        return "dark"
    if "flat" in text:
        return "flat"
    if "light" in text or "object" in text or "science" in text:
        return "light"
    return "unknown"

