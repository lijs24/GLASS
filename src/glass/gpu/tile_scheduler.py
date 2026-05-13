from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class Tile:
    y0: int
    y1: int
    x0: int
    x1: int


def iter_tiles(width: int, height: int, tile_size: int = 512) -> Iterator[Tile]:
    for y0 in range(0, height, tile_size):
        for x0 in range(0, width, tile_size):
            yield Tile(y0, min(height, y0 + tile_size), x0, min(width, x0 + tile_size))

