from __future__ import annotations

import importlib.util
import importlib
from functools import lru_cache
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from astropy.io import fits


@pytest.fixture()
def small_fits_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "dataset"
    shape = (16, 20)
    specs = [
        ("bias", "bias_001.fits", 0.0, 100.0),
        ("dark", "dark_001.fits", 60.0, 110.0),
        ("flat", "flat_001.fits", 60.0, 1000.0),
        ("light", "light_001.fits", 60.0, 1200.0),
    ]
    for frame_type, name, exposure, value in specs:
        header = fits.Header()
        header["IMAGETYP"] = frame_type
        header["FILTER"] = "H"
        header["EXPTIME"] = exposure
        header["GAIN"] = 100.0
        header["OFFSET"] = 20.0
        header["CCD-TEMP"] = -10.0
        header["XBINNING"] = 1
        header["YBINNING"] = 1
        if frame_type == "light":
            header["PIERSIDE"] = "West"
            header["OBJCTROT"] = 92.0
        data = np.ones(shape, dtype=np.float32) * value
        if frame_type == "light":
            yy, xx = np.indices(shape, dtype=np.float32)
            for x, y, flux in [(3.0, 13.0, 5000.0), (11.0, 13.0, 4200.0), (17.0, 13.0, 4600.0)]:
                data += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 0.8**2)))
            data[2:6, 3:8] = value
        path = root / frame_type / name
        path.parent.mkdir(parents=True, exist_ok=True)
        fits.PrimaryHDU(data, header=header).writeto(path)
    return root


def cuda_module_or_skip():
    busy_reason = cuda_busy_skip_reason()
    if busy_reason is not None:
        pytest.skip(busy_reason)
    module = cuda_api_module()
    if not getattr(module, "cuda_available", lambda: False)():
        pytest.skip("CUDA native backend is not available")
    return module


def cuda_api_module():
    if importlib.util.find_spec("glass_cuda") is None:
        pytest.skip("glass_cuda extension is not built")
    return importlib.import_module("glass_cuda")


def astroalign_or_skip():
    reason = astroalign_skip_reason()
    if reason is not None:
        pytest.skip(reason)
    return importlib.import_module("astroalign")


@lru_cache(maxsize=1)
def astroalign_skip_reason() -> str | None:
    if importlib.util.find_spec("astroalign") is None:
        return "astroalign is not installed"
    code = r"""
import astroalign as aa
import numpy as np

image = np.full((96, 112), 10.0, dtype=np.float32)
yy, xx = np.indices(image.shape, dtype=np.float32)
for x, y, flux in [
    (12, 17, 100.0),
    (30, 42, 220.0),
    (71, 15, 160.0),
    (88, 63, 180.0),
    (45, 79, 250.0),
    (19, 86, 130.0),
    (101, 33, 145.0),
    (53, 55, 190.0),
]:
    image += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.4**2)))
moving = np.zeros_like(image, dtype=np.float32)
moving[0:93, 4:112] = image[3:96, 0:108]
aa.find_transform(moving, image)
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            capture_output=True,
            text=True,
            timeout=8.0,
        )
    except subprocess.TimeoutExpired:
        return "astroalign smoke test timed out; skipping astroalign-dependent tests"
    if result.returncode != 0:
        return "astroalign smoke test failed; skipping astroalign-dependent tests"
    return None


def _cuda_busy_reason_from_query(text: str, *, min_free_mib: int = 8192) -> str | None:
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first:
        return None
    parts = [part.strip() for part in first.split(",")]
    if len(parts) < 3:
        return None
    try:
        total_mib = int(parts[0])
        used_mib = int(parts[1])
        utilization = int(parts[2])
    except ValueError:
        return None
    free_mib = total_mib - used_mib
    used_fraction = used_mib / total_mib if total_mib > 0 else 0.0
    if free_mib < min_free_mib:
        return f"CUDA tests skipped: only {free_mib} MiB GPU memory is free"
    if utilization >= 95 and used_fraction >= 0.5:
        return (
            "CUDA tests skipped: GPU is busy "
            f"({utilization}% utilization, {used_mib}/{total_mib} MiB used)"
        )
    return None


@lru_cache(maxsize=1)
def cuda_busy_skip_reason() -> str | None:
    if os.environ.get("GLASS_TEST_IGNORE_GPU_BUSY") == "1":
        return None
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return _cuda_busy_reason_from_query(result.stdout)
