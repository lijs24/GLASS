from __future__ import annotations


def zarr_available() -> bool:
    try:
        import zarr  # noqa: F401
    except Exception:
        return False
    return True

