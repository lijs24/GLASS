from __future__ import annotations

from pathlib import Path

import numpy as np

from glass.cpu.master_frames import make_master_bias, make_master_dark, make_master_flat, mean_stack
from glass.engine.contracts import DQFlag
from glass.io.fits_io import write_fits_data
from glass.synthetic.generator import generate_synthetic_dataset


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
    assert bias.engine == "stack_engine_cpu"
    assert bias.metrics is not None
    assert bias.metrics["public_helper"] == "glass.cpu.master_frames.mean_stack"
    assert bias.metrics["result_contract_passed"] is True
    assert bias.metrics["master_postprocess_operation"] == "bias_mean"
    assert bias.dq_provenance is not None
    assert bias.dq_provenance["result_contract"]["passed"] is True
    assert bias.dq_mask is not None
    assert bias.dq_mask.summary()["valid"] == 32 * 24


def test_cpu_master_mean_stack_uses_stack_engine_dq_semantics(tmp_path: Path):
    frame_a = np.array([[1.0, np.nan], [5.0, 7.0]], dtype=np.float32)
    frame_b = np.array([[3.0, 9.0], [np.nan, 11.0]], dtype=np.float32)
    paths = []
    for index, frame in enumerate([frame_a, frame_b]):
        path = tmp_path / f"frame_{index}.fits"
        write_fits_data(path, frame)
        paths.append(path)

    result = mean_stack(paths, tile_size=1)

    assert result.engine == "stack_engine_cpu"
    assert np.allclose(result.data, np.array([[2.0, 9.0], [5.0, 9.0]], dtype=np.float32))
    assert result.dq_provenance is not None
    assert result.metrics is not None
    assert result.dq_provenance["input_invalid_samples_before_rejection"] == 2
    assert result.dq_provenance["input_nonfinite_samples"] == 2
    assert result.dq_provenance["valid_samples_after_rejection"] == 6
    assert result.dq_provenance["result_contract"]["passed"] is True
    assert result.metrics["input_invalid_samples"] == 2
    assert result.metrics["result_contract_passed"] is True
    assert result.dq_mask is not None
    assert int(result.dq_mask.count(DQFlag.NO_DATA)) == 0
