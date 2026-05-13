from __future__ import annotations

from pathlib import Path


def cache_dir(run_dir: str | Path, stage: str) -> Path:
    path = Path(run_dir) / "cache" / stage
    path.mkdir(parents=True, exist_ok=True)
    return path

