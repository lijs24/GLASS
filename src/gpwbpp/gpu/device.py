from __future__ import annotations


def list_devices() -> list[dict[str, object]]:
    try:
        import gpwbpp_cuda  # type: ignore
    except Exception:
        return []
    if not getattr(gpwbpp_cuda, "cuda_available", lambda: False)():
        return []
    return list(gpwbpp_cuda.list_devices())

