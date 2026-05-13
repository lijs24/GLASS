from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.common import add_common_args, run_timed, write_result
from glass.gpu.tile_scheduler import iter_tiles
from glass.io.fits_io import open_fits_image
from glass.synthetic.generator import generate_synthetic_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args()
    root = Path(args.out).with_suffix("") / "source"
    generate_synthetic_dataset(root, frames=args.frames, width=args.width, height=args.height)
    path = next(root.rglob("light_*.fits"))

    def read_tiles() -> float:
        total = 0.0
        with open_fits_image(path, memmap=True) as hdul:
            data = hdul[0].data
            for tile in iter_tiles(width=args.width, height=args.height, tile_size=args.tile_size):
                total += float(np.sum(data[tile.y0 : tile.y1, tile.x0 : tile.x1]))
        return total

    _, elapsed, peak_ram = run_timed(read_tiles)
    write_result(
        args.out,
        name="io_streaming",
        frame_count=1,
        width=args.width,
        height=args.height,
        backend="fits_memmap",
        elapsed_s=elapsed,
        peak_ram_mb=peak_ram,
        output_path=path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
