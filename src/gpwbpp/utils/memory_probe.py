from __future__ import annotations


def peak_ram_mb() -> float | None:
    try:
        import resource  # type: ignore

        return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0
    except Exception:
        return None
