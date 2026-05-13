from __future__ import annotations


def list_devices() -> list[dict[str, object]]:
    try:
        import glass_cuda  # type: ignore
    except Exception:
        return []
    if not getattr(glass_cuda, "cuda_available", lambda: False)():
        return []
    return list(glass_cuda.list_devices())

