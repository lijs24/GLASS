from __future__ import annotations

from gpwbpp.gpu.tile_scheduler import iter_tiles


def test_iter_tiles_covers_shape():
    tiles = list(iter_tiles(width=10, height=9, tile_size=4))
    assert tiles[0].y0 == 0
    assert tiles[-1].y1 == 9
    assert tiles[-1].x1 == 10
    area = sum((tile.y1 - tile.y0) * (tile.x1 - tile.x0) for tile in tiles)
    assert area == 90

