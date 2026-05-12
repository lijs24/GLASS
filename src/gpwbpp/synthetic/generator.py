from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from gpwbpp.io.json_io import write_json


def _base_header(frame_type: str, filt: str, exposure: float, gain: float, shape: tuple[int, int]):
    h = fits.Header()
    h["IMAGETYP"] = frame_type
    h["FILTER"] = filt
    h["EXPTIME"] = exposure
    h["GAIN"] = gain
    h["OFFSET"] = 20.0
    h["CCD-TEMP"] = -10.0
    h["XBINNING"] = 1
    h["YBINNING"] = 1
    h["INSTRUME"] = "GPWBPP-SYNTH"
    return h


def _write(path: Path, data: np.ndarray, header: fits.Header) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.PrimaryHDU(data.astype(np.float32), header=header).writeto(path, overwrite=True)


def _stars(width: int, height: int, seed: int, count: int = 24) -> np.ndarray:
    rng = np.random.default_rng(seed)
    xs = rng.uniform(10, width - 10, size=count)
    ys = rng.uniform(10, height - 10, size=count)
    flux = rng.uniform(500, 2500, size=count)
    return np.stack([xs, ys, flux], axis=1)


def render_star_field(
    width: int, height: int, stars: np.ndarray, dx: float = 0.0, dy: float = 0.0, sigma: float = 1.4
) -> np.ndarray:
    yy, xx = np.mgrid[0:height, 0:width]
    image = np.zeros((height, width), dtype=np.float32)
    for x, y, flux in stars:
        image += flux * np.exp(-((xx - (x + dx)) ** 2 + (yy - (y + dy)) ** 2) / (2 * sigma**2))
    return image.astype(np.float32)


def generate_synthetic_dataset(
    out_dir: str | Path,
    frames: int = 20,
    width: int = 512,
    height: int = 512,
    filt: str = "H",
    known_shift: bool = False,
    seed: int = 42,
) -> dict[str, object]:
    out = Path(out_dir)
    rng = np.random.default_rng(seed)
    shape = (height, width)
    bias_level = 1000.0
    dark_current = 0.4
    dark_exp = 60.0
    light_exp = 60.0
    gain = 100.0
    flat_y = np.linspace(0.95, 1.05, height, dtype=np.float32)[:, None]
    flat_x = np.linspace(0.98, 1.02, width, dtype=np.float32)[None, :]
    normalized_flat = (flat_y * flat_x).astype(np.float32)
    stars = _stars(width, height, seed)
    truth: dict[str, object] = {
        "width": width,
        "height": height,
        "filter": filt,
        "bias_level": bias_level,
        "dark_current": dark_current,
        "dark_exposure_s": dark_exp,
        "light_exposure_s": light_exp,
        "known_transforms": {},
    }
    hot_pixels = [(int(rng.integers(0, height)), int(rng.integers(0, width))) for _ in range(20)]
    for i in range(max(3, frames // 4)):
        data = bias_level + rng.normal(0, 3.0, size=shape)
        _write(out / "bias" / f"bias_{i:03d}.fits", data, _base_header("bias", filt, 0.0, gain, shape))
    for i in range(max(3, frames // 4)):
        data = bias_level + dark_current * dark_exp + rng.normal(0, 4.0, size=shape)
        for y, x in hot_pixels:
            data[y, x] += 500
        _write(out / "dark" / f"dark_{i:03d}.fits", data, _base_header("dark", filt, dark_exp, gain, shape))
    for i in range(max(3, frames // 4)):
        signal = 25000.0 * normalized_flat
        data = bias_level + dark_current * light_exp + signal + rng.normal(0, 20.0, size=shape)
        _write(out / "flat" / f"flat_{i:03d}.fits", data, _base_header("flat", filt, light_exp, gain, shape))
    for i in range(frames):
        dx = float((i % 5) - 2) if known_shift else 0.0
        dy = float(((i // 5) % 5) - 2) if known_shift else 0.0
        sky = 200.0 + np.linspace(0, 30, height, dtype=np.float32)[:, None]
        star_field = render_star_field(width, height, stars, dx=dx, dy=dy)
        clean = (sky + star_field) * normalized_flat
        data = bias_level + dark_current * light_exp + clean + rng.normal(0, 8.0, size=shape)
        for y, x in hot_pixels:
            data[y, x] += 500
        name = f"light_{i:03d}.fits"
        _write(out / "light" / name, data, _base_header("light", filt, light_exp, gain, shape))
        truth["known_transforms"][str(out / "light" / name)] = {"dx": dx, "dy": dy}
    truth["expected_master_statistics"] = {
        "master_bias_mean": bias_level,
        "master_dark_mean": bias_level + dark_current * dark_exp,
        "master_flat_median": 1.0,
    }
    write_json(out / "golden_truth.json", truth)
    return truth
