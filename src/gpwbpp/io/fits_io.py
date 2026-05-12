from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from astropy.io import fits


def read_fits_data(path: str | Path, dtype=np.float32) -> np.ndarray:
    with fits.open(path, memmap=True) as hdul:
        data = hdul[0].data
        if data is None:
            raise ValueError(f"FITS file has no primary image data: {path}")
        return np.asarray(data, dtype=dtype)


def read_fits_header(path: str | Path) -> dict[str, Any]:
    header = fits.getheader(path, memmap=True)
    return {str(k): header[k] for k in header.keys()}


def write_fits_data(path: str | Path, data: np.ndarray, header: dict[str, Any] | None = None) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    hdu = fits.PrimaryHDU(np.asarray(data, dtype=np.float32))
    if header:
        for key, value in header.items():
            if value is not None and len(str(key)) <= 8:
                hdu.header[str(key)] = value
    hdu.writeto(target, overwrite=True)

