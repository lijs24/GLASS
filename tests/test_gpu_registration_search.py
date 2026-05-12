from __future__ import annotations

import numpy as np

from tests.conftest import cuda_module_or_skip


def _shift_image(data: np.ndarray, dx: int, dy: int) -> np.ndarray:
    output = np.zeros_like(data, dtype=np.float32)
    h, w = data.shape
    src_x0 = max(0, -dx)
    src_x1 = min(w, w - dx)
    dst_x0 = max(0, dx)
    dst_x1 = min(w, w + dx)
    src_y0 = max(0, -dy)
    src_y1 = min(h, h - dy)
    dst_y0 = max(0, dy)
    dst_y1 = min(h, h + dy)
    if src_x0 < src_x1 and src_y0 < src_y1:
        output[dst_y0:dst_y1, dst_x0:dst_x1] = data[src_y0:src_y1, src_x0:src_x1]
    return output


def _star_field() -> np.ndarray:
    image = np.zeros((96, 112), dtype=np.float32)
    stars = [
        (12, 17, 100.0),
        (30, 42, 220.0),
        (71, 15, 160.0),
        (88, 63, 180.0),
        (45, 79, 250.0),
        (19, 86, 130.0),
        (101, 33, 145.0),
    ]
    yy, xx = np.indices(image.shape, dtype=np.float32)
    for x, y, flux in stars:
        image += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.4**2)))
    image += 10.0 + 0.01 * xx + 0.02 * yy
    return image.astype(np.float32)


def test_gpu_estimate_translation_search_aligns_shifted_pair():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_translation_search_f32"):
        raise AssertionError("estimate_translation_search_f32 is missing from gpwbpp_cuda")

    reference = _star_field()
    moving = _shift_image(reference, 5, -4)

    result = module.estimate_translation_search_f32(reference, moving, 8, 8)
    aligned, coverage = module.warp_translation_f32(moving, result["dx"], result["dy"], 0.0)

    valid = coverage > 0.0
    rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))

    assert result["dx"] == -5
    assert result["dy"] == 4
    assert result["score"] > 0.99
    assert rms < 1.0e-4
