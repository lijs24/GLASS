from __future__ import annotations

from pathlib import Path

import numpy as np

from gpwbpp.cpu.master_frames import make_master_bias as make_master_bias_cpu
from gpwbpp.gpu.master_frames import (
    make_master_bias,
    make_master_dark,
    make_master_flat,
    mean_stack_paths_tile_streaming,
)
from gpwbpp.synthetic.generator import generate_synthetic_dataset
from tests.conftest import cuda_module_or_skip


def test_gpu_mean_stack_matches_cpu(tmp_path: Path):
    cuda_module_or_skip()
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=4, width=32, height=24)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    cpu = make_master_bias_cpu(bias_paths)
    gpu = mean_stack_paths_tile_streaming(bias_paths, tile_size=11)
    assert np.allclose(gpu.data, cpu.data, rtol=1e-5, atol=1e-5)


def test_gpu_master_bias_dark_flat_match_cpu_shape_and_stats(tmp_path: Path):
    cuda_module_or_skip()
    out = tmp_path / "synthetic"
    generate_synthetic_dataset(out, frames=4, width=32, height=24)
    bias_paths = sorted((out / "bias").glob("*.fits"))
    dark_paths = sorted((out / "dark").glob("*.fits"))
    flat_paths = sorted((out / "flat").glob("*.fits"))
    bias = make_master_bias(bias_paths, tile_size=13)
    dark = make_master_dark(dark_paths, master_bias=bias.data, tile_size=13)
    flat = make_master_flat(flat_paths, master_bias=bias.data, tile_size=13)
    assert bias.data.shape == (24, 32)
    assert dark.data.shape == (24, 32)
    assert flat.data.shape == (24, 32)
    assert 0.98 < flat.stats["median"] < 1.02
