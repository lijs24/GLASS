from __future__ import annotations

import importlib.util
import importlib
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits


@pytest.fixture()
def small_fits_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    shape = (16, 20)
    specs = [
        ("bias", "bias_001.fits", 0.0),
        ("dark", "dark_001.fits", 60.0),
        ("flat", "flat_001.fits", 60.0),
        ("light", "light_001.fits", 60.0),
    ]
    for frame_type, name, exposure in specs:
        header = fits.Header()
        header["IMAGETYP"] = frame_type
        header["FILTER"] = "H"
        header["EXPTIME"] = exposure
        header["GAIN"] = 100.0
        header["OFFSET"] = 20.0
        header["CCD-TEMP"] = -10.0
        header["XBINNING"] = 1
        header["YBINNING"] = 1
        path = root / frame_type / name
        path.parent.mkdir(parents=True, exist_ok=True)
        fits.PrimaryHDU(np.ones(shape, dtype=np.float32), header=header).writeto(path)
    return root


def cuda_module_or_skip():
    module = cuda_api_module()
    if not getattr(module, "cuda_available", lambda: False)():
        pytest.skip("CUDA native backend is not available")
    return module


def cuda_api_module():
    if importlib.util.find_spec("gpwbpp_cuda") is None:
        pytest.skip("gpwbpp_cuda extension is not built")
    return importlib.import_module("gpwbpp_cuda")
