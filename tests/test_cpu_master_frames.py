from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.cpu.master_frames import make_master_bias, make_master_dark, make_master_flat
from gpwbpp.synthetic.generator import generate_synthetic_dataset


def test_cpu_master_frames(tmp_path: Path):
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=4, width=32, height=24)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    dark_paths = sorted((out / "dark").glob("*.fits"))
    flat_paths = sorted((out / "flat").glob("*.fits"))
    bias = make_master_bias(bias_paths)
    dark_raw = make_master_dark(dark_paths)
    dark_bias_subtracted = make_master_dark(dark_paths, master_bias=bias.data)
    flat = make_master_flat(flat_paths, master_bias=bias.data)
    assert 990 < bias.stats["mean"] < 1010
    assert dark_raw.stats["mean"] > bias.stats["mean"]
    assert np.mean(dark_bias_subtracted.data) < np.mean(dark_raw.data)
    assert 0.98 < flat.stats["median"] < 1.02

