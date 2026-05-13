from __future__ import annotations

from pathlib import Path


IMAGE_SUFFIXES = {".fit", ".fits", ".fts", ".xisf"}


def iter_image_paths(root: str | Path):
    root_path = Path(root)
    for path in sorted(root_path.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            yield path

