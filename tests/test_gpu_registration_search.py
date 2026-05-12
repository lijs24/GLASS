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


def test_gpu_estimate_translation_from_catalogs_votes_pair_offsets():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_translation_from_catalogs_f32"):
        raise AssertionError("estimate_translation_from_catalogs_f32 is missing from gpwbpp_cuda")

    reference = np.array(
        [
            (10.0, 10.0),
            (25.0, 12.0),
            (18.0, 31.0),
            (40.0, 35.0),
            (52.0, 18.0),
            (61.0, 44.0),
        ],
        dtype=np.float32,
    )
    moving = reference - np.array([3.0, -2.0], dtype=np.float32)
    moving = np.vstack([moving, np.array([[100.0, 100.0], [3.0, 80.0]], dtype=np.float32)])

    result = module.estimate_translation_from_catalogs_f32(
        reference[:, 0],
        reference[:, 1],
        moving[:, 0],
        moving[:, 1],
        0.1,
    )

    assert result["dx"] == 3.0
    assert result["dy"] == -2.0
    assert result["inliers"] >= len(reference)
    assert result["candidate_count"] == len(reference) * len(moving)


def test_gpu_catalog_translation_from_top_star_candidates():
    module = cuda_module_or_skip()
    reference = _star_field()
    moving = _shift_image(reference, 4, -3)

    ref_catalog = module.star_top_candidates_f32(reference, 30.0, 16)
    mov_catalog = module.star_top_candidates_f32(moving, 30.0, 16)
    result = module.estimate_translation_from_catalogs_f32(
        ref_catalog["x"],
        ref_catalog["y"],
        mov_catalog["x"],
        mov_catalog["y"],
        0.25,
    )

    assert result["dx"] == -4.0
    assert result["dy"] == 3.0
    assert result["inliers"] >= 6
