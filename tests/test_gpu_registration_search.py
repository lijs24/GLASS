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


def _smooth_star_field() -> np.ndarray:
    image = np.zeros((64, 64), dtype=np.float32)
    stars = [
        (12.25, 14.50, 150.0),
        (24.00, 20.75, 230.0),
        (41.50, 18.25, 180.0),
        (16.75, 42.00, 130.0),
        (49.25, 45.50, 210.0),
        (35.50, 33.25, 170.0),
    ]
    yy, xx = np.indices(image.shape, dtype=np.float32)
    for x, y, flux in stars:
        image += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.2**2)))
    image += 10.0 + 0.01 * xx + 0.02 * yy
    return image.astype(np.float32)


def _render_catalog_field(shape: tuple[int, int], stars: np.ndarray) -> np.ndarray:
    image = np.full(shape, 8.0, dtype=np.float32)
    yy, xx = np.indices(shape, dtype=np.float32)
    for x, y, flux in stars:
        image += float(flux) * np.exp(-(((xx - float(x)) ** 2 + (yy - float(y)) ** 2) / (2.0 * 1.15**2)))
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


def test_gpu_estimate_translation_search_supports_sample_stride():
    module = cuda_module_or_skip()
    reference = _star_field()
    moving = _shift_image(reference, 5, -4)

    result = module.estimate_translation_search_f32(reference, moving, 8, 8, sample_stride=2)

    assert result["dx"] == -5
    assert result["dy"] == 4
    assert result["sample_stride"] == 2
    assert result["score"] > 0.99


def test_gpu_estimate_translation_subpixel_ncc_refines_integer_shift():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_translation_subpixel_ncc_f32"):
        raise AssertionError("estimate_translation_subpixel_ncc_f32 is missing from gpwbpp_cuda")

    reference = _smooth_star_field()
    true_delta = np.array([2.25, -1.5], dtype=np.float32)
    moving, _coverage = module.warp_translation_bilinear_f32(
        reference,
        -float(true_delta[0]),
        -float(true_delta[1]),
        0.0,
    )

    result = module.estimate_translation_subpixel_ncc_f32(reference, moving, 2.0, -2.0, 3, 0.25)
    aligned, coverage = module.warp_translation_bilinear_f32(moving, result["dx"], result["dy"], 0.0)
    center_aligned, center_coverage = module.warp_translation_bilinear_f32(moving, 2.0, -2.0, 0.0)
    valid = coverage > 0.0
    yy, xx = np.indices(reference.shape)
    valid &= (xx >= 8) & (xx < reference.shape[1] - 8) & (yy >= 8) & (yy < reference.shape[0] - 8)
    rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))
    center_valid = center_coverage > 0.0
    center_valid &= (xx >= 8) & (xx < reference.shape[1] - 8) & (yy >= 8) & (yy < reference.shape[0] - 8)
    center_rms = float(np.sqrt(np.mean((center_aligned[center_valid] - reference[center_valid]) ** 2)))

    assert abs(result["dx"] - float(true_delta[0])) <= 0.25
    assert abs(result["dy"] - float(true_delta[1])) <= 0.25
    assert result["candidate_count"] == 49
    assert result["score"] > 0.98
    assert rms < center_rms
    assert rms < 4.0


def test_gpu_estimate_translation_subpixel_ncc_supports_sample_stride():
    module = cuda_module_or_skip()
    reference = _smooth_star_field()
    true_delta = np.array([2.25, -1.5], dtype=np.float32)
    moving, _coverage = module.warp_translation_bilinear_f32(
        reference,
        -float(true_delta[0]),
        -float(true_delta[1]),
        0.0,
    )

    result = module.estimate_translation_subpixel_ncc_f32(
        reference,
        moving,
        2.0,
        -2.0,
        3,
        0.25,
        sample_stride=2,
    )

    assert abs(result["dx"] - float(true_delta[0])) <= 0.25
    assert abs(result["dy"] - float(true_delta[1])) <= 0.25
    assert result["sample_stride"] == 2
    assert result["score"] > 0.98


def test_gpu_matrix_alignment_metrics_matches_matrix_warp_rms():
    module = cuda_module_or_skip()
    if not hasattr(module, "matrix_alignment_metrics_f32"):
        raise AssertionError("matrix_alignment_metrics_f32 is missing from gpwbpp_cuda")

    reference = _smooth_star_field()
    matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(matrix).astype(np.float32), 0.0)
    aligned, coverage = module.warp_matrix_bilinear_f32(moving, matrix, 0.0)
    metrics = module.matrix_alignment_metrics_f32(reference, moving, matrix, sample_stride=1)

    valid = coverage > 0.0
    expected_rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))
    expected_mean_abs = float(np.mean(np.abs(aligned[valid] - reference[valid])))

    assert metrics["model"] == "matrix_alignment_metrics_cuda"
    assert metrics["valid_pixels"] == int(np.sum(valid))
    assert metrics["sampled_pixels"] == reference.size
    assert abs(metrics["rms"] - expected_rms) < 1.0e-4
    assert abs(metrics["mean_abs_diff"] - expected_mean_abs) < 1.0e-4
    assert metrics["ncc"] > 0.98


def test_gpu_matrix_alignment_metrics_distinguishes_bad_transform():
    module = cuda_module_or_skip()
    if not hasattr(module, "matrix_alignment_metrics_f32"):
        raise AssertionError("matrix_alignment_metrics_f32 is missing from gpwbpp_cuda")

    reference = _smooth_star_field()
    good_matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    bad_matrix = np.asarray([[1.0, 0.0, -1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(good_matrix).astype(np.float32), 0.0)

    good = module.matrix_alignment_metrics_f32(reference, moving, good_matrix, sample_stride=2)
    bad = module.matrix_alignment_metrics_f32(reference, moving, bad_matrix, sample_stride=2)

    assert good["sample_stride"] == 2
    assert good["rms"] < bad["rms"] * 0.5
    assert good["ncc"] > bad["ncc"]


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
    assert result["refined_dx"] == 3.0
    assert result["refined_dy"] == -2.0
    assert result["mutual_inliers"] == len(reference)
    assert result["rms_px"] == 0.0
    assert result["candidate_count"] == len(reference) * len(moving)


def test_gpu_catalog_translation_respects_search_bounds():
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
    moving = np.vstack([moving, reference - np.array([80.0, 70.0], dtype=np.float32)])

    unbounded = module.estimate_translation_from_catalogs_f32(
        reference[:, 0],
        reference[:, 1],
        moving[:, 0],
        moving[:, 1],
        0.1,
    )
    bounded = module.estimate_translation_from_catalogs_f32(
        reference[:, 0],
        reference[:, 1],
        moving[:, 0],
        moving[:, 1],
        0.1,
        10.0,
        10.0,
    )

    assert unbounded["inliers"] >= len(reference)
    assert bounded["dx"] == 3.0
    assert bounded["dy"] == -2.0
    assert bounded["mutual_inliers"] == len(reference)
    assert bounded["max_abs_dx"] == 10.0
    assert bounded["max_abs_dy"] == 10.0


def test_gpu_catalog_translation_respects_ncc_prior_window():
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
    true_delta = np.array([3.25, -1.75], dtype=np.float32)
    distractor_delta = np.array([0.0, 0.0], dtype=np.float32)
    moving = np.vstack([reference - distractor_delta, reference - true_delta])

    result = module.estimate_translation_from_catalogs_f32(
        reference[:, 0],
        reference[:, 1],
        moving[:, 0],
        moving[:, 1],
        0.4,
        10.0,
        10.0,
        3.0,
        -2.0,
        1.0,
    )

    assert abs(result["refined_dx"] - float(true_delta[0])) < 1.0e-5
    assert abs(result["refined_dy"] - float(true_delta[1])) < 1.0e-5
    assert result["mutual_inliers"] == len(reference)
    assert result["prior_dx"] == 3.0
    assert result["prior_dy"] == -2.0
    assert result["prior_radius_px"] == 1.0


def test_gpu_catalog_translation_reports_no_match_when_prior_rejects_all_pairs():
    module = cuda_module_or_skip()
    reference = np.array([(10.0, 10.0), (25.0, 12.0), (18.0, 31.0)], dtype=np.float32)
    moving = reference.copy()

    result = module.estimate_translation_from_catalogs_f32(
        reference[:, 0],
        reference[:, 1],
        moving[:, 0],
        moving[:, 1],
        0.4,
        10.0,
        10.0,
        6.0,
        6.0,
        0.5,
    )

    assert result["inliers"] == 0
    assert result["mutual_inliers"] == 0
    assert np.isnan(result["dx"])
    assert np.isnan(result["dy"])
    assert np.isnan(result["rms_px"])


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
    assert abs(result["refined_dx"] + 4.0) < 1.0e-5
    assert abs(result["refined_dy"] - 3.0) < 1.0e-5
    assert result["mutual_inliers"] >= 6
    assert result["rms_px"] == 0.0


def test_gpu_catalog_translation_refines_mutual_inliers():
    module = cuda_module_or_skip()
    reference = np.array(
        [
            (11.0, 9.0),
            (25.0, 14.0),
            (18.0, 34.0),
            (41.0, 37.0),
            (53.0, 21.0),
            (63.0, 45.0),
        ],
        dtype=np.float32,
    )
    jitter = np.array(
        [
            (0.02, -0.01),
            (-0.03, 0.01),
            (0.01, 0.02),
            (-0.02, -0.02),
            (0.00, 0.03),
            (0.03, -0.03),
        ],
        dtype=np.float32,
    )
    true_delta = np.array([3.25, -1.75], dtype=np.float32)
    moving = reference - true_delta + jitter

    result = module.estimate_translation_from_catalogs_f32(
        reference[:, 0],
        reference[:, 1],
        moving[:, 0],
        moving[:, 1],
        0.4,
    )

    assert result["mutual_inliers"] == len(reference)
    assert abs(result["refined_dx"] - float(true_delta[0])) < 0.03
    assert abs(result["refined_dy"] - float(true_delta[1])) < 0.03
    assert result["rms_px"] < 0.05


def test_gpu_estimate_similarity_from_matched_pairs():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_pairs_f32"):
        raise AssertionError("estimate_similarity_from_pairs_f32 is missing from gpwbpp_cuda")

    moving = np.array(
        [
            (10.0, 11.0),
            (25.0, 14.0),
            (18.0, 34.0),
            (41.0, 37.0),
            (53.0, 21.0),
            (63.0, 45.0),
            (31.0, 58.0),
            (72.0, 18.0),
        ],
        dtype=np.float32,
    )
    angle = np.deg2rad(6.0)
    scale = 1.035
    linear = scale * np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float32,
    )
    translation = np.array([2.5, -3.25], dtype=np.float32)
    reference = moving @ linear.T + translation
    reference = np.vstack([reference, np.array([[np.nan, 1.0]], dtype=np.float32)])
    moving_with_nan = np.vstack([moving, np.array([[4.0, np.nan]], dtype=np.float32)])

    result = module.estimate_similarity_from_pairs_f32(
        reference[:, 0],
        reference[:, 1],
        moving_with_nan[:, 0],
        moving_with_nan[:, 1],
    )
    matrix = np.asarray(result["matrix"], dtype=np.float32)

    assert result["status"] == "ok"
    assert result["model"] == "matched_pair_similarity_cuda"
    assert result["valid_pairs"] == len(moving)
    assert result["input_pairs"] == len(moving) + 1
    assert abs(result["scale"] - scale) < 1.0e-5
    assert abs(result["rotation_rad"] - angle) < 1.0e-5
    assert result["rms_px"] < 1.0e-4
    assert np.allclose(matrix[:2, :2], linear, atol=1.0e-5)
    assert np.allclose(matrix[:2, 2], translation, atol=1.0e-4)


def test_gpu_estimate_similarity_from_catalogs_scores_pair_candidates():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_catalogs_f32"):
        raise AssertionError("estimate_similarity_from_catalogs_f32 is missing from gpwbpp_cuda")

    moving = np.array(
        [
            (10.0, 11.0),
            (25.0, 14.0),
            (18.0, 34.0),
            (41.0, 37.0),
            (53.0, 21.0),
            (63.0, 45.0),
            (31.0, 58.0),
            (72.0, 18.0),
        ],
        dtype=np.float32,
    )
    angle = np.deg2rad(-4.0)
    scale = 0.985
    linear = scale * np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float32,
    )
    translation = np.array([-1.75, 4.5], dtype=np.float32)
    reference = moving @ linear.T + translation
    moving_catalog = np.vstack([moving, np.array([[90.0, 90.0], [5.0, 70.0]], dtype=np.float32)])
    reference_catalog = np.vstack([reference, np.array([[4.0, 4.0], [80.0, 8.0]], dtype=np.float32)])

    result = module.estimate_similarity_from_catalogs_f32(
        reference_catalog[:, 0],
        reference_catalog[:, 1],
        moving_catalog[:, 0],
        moving_catalog[:, 1],
        tolerance_px=0.15,
        min_pair_distance=3.0,
        prior_dx=float(translation[0]),
        prior_dy=float(translation[1]),
        prior_radius_px=2.0,
        min_scale=0.95,
        max_scale=1.05,
        max_abs_rotation_rad=0.2,
    )
    matrix = np.asarray(result["matrix"], dtype=np.float32)

    assert result["status"] == "ok"
    assert result["model"] == "catalog_pair_similarity_cuda"
    assert result["inliers"] >= len(moving)
    assert result["candidate_count"] == len(reference_catalog) * (len(reference_catalog) - 1) * len(
        moving_catalog
    ) * (len(moving_catalog) - 1)
    assert result["prior_radius_px"] == 2.0
    assert abs(result["min_scale"] - 0.95) < 1.0e-6
    assert abs(result["max_scale"] - 1.05) < 1.0e-6
    assert abs(result["max_abs_rotation_rad"] - 0.2) < 1.0e-6
    assert abs(result["scale"] - scale) < 1.0e-4
    assert abs(result["rotation_rad"] - angle) < 1.0e-4
    assert result["rms_px"] < 1.0e-3
    assert np.allclose(matrix[:2, :2], linear, atol=1.0e-4)
    assert np.allclose(matrix[:2, 2], translation, atol=1.0e-3)


def test_gpu_similarity_catalog_registration_aligns_synthetic_images():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_catalogs_f32"):
        raise AssertionError("estimate_similarity_from_catalogs_f32 is missing from gpwbpp_cuda")
    from gpwbpp.gpu.registration import register_similarity_from_star_catalogs_f32

    reference_stars = np.array(
        [
            (18.0, 20.0, 180.0),
            (35.0, 24.0, 260.0),
            (62.0, 18.0, 220.0),
            (26.0, 55.0, 210.0),
            (51.0, 48.0, 300.0),
            (78.0, 61.0, 240.0),
            (88.0, 30.0, 190.0),
            (44.0, 78.0, 230.0),
        ],
        dtype=np.float32,
    )
    angle = np.deg2rad(3.0)
    scale = 1.015
    linear = scale * np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float32,
    )
    translation = np.array([2.0, -1.5], dtype=np.float32)
    moving_xy = (reference_stars[:, :2] - translation) @ np.linalg.inv(linear).T
    moving_stars = np.column_stack([moving_xy, reference_stars[:, 2]]).astype(np.float32)

    reference = _render_catalog_field((104, 112), reference_stars)
    moving = _render_catalog_field((104, 112), moving_stars)
    aligned, coverage, diagnostics = register_similarity_from_star_catalogs_f32(
        reference,
        moving,
        threshold=50.0,
        max_candidates=12,
        tolerance_px=1.5,
        min_pair_distance=8.0,
    )

    matrix = np.asarray(diagnostics["matrix"], dtype=np.float32)
    valid = coverage > 0.0
    yy, xx = np.indices(reference.shape)
    valid &= (xx >= 8) & (xx < reference.shape[1] - 8) & (yy >= 8) & (yy < reference.shape[0] - 8)
    before = float(np.sqrt(np.mean((moving[valid] - reference[valid]) ** 2)))
    after = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))

    assert diagnostics["status"] == "ok"
    assert diagnostics["similarity"]["model"] == "catalog_pair_similarity_cuda"
    assert diagnostics["reference_stored"] >= len(reference_stars)
    assert diagnostics["moving_stored"] >= len(reference_stars)
    assert diagnostics["similarity"]["inliers"] >= len(reference_stars)
    assert diagnostics["coverage_pixels"] > 0
    assert after < before * 0.6
    assert np.allclose(matrix[:2, :2], linear, atol=0.04)
    assert np.allclose(matrix[:2, 2], translation, atol=2.0)


def test_gpu_star_top_nms_candidates_suppresses_close_peaks():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_top_nms_candidates_f32"):
        raise AssertionError("star_top_nms_candidates_f32 is missing from gpwbpp_cuda")

    image = np.zeros((48, 48), dtype=np.float32)
    image[10, 10] = 100.0
    image[11, 11] = 95.0
    image[30, 30] = 90.0
    image[40, 7] = 85.0

    result = module.star_top_nms_candidates_f32(
        image,
        threshold=10.0,
        scan_candidates=8,
        max_output_candidates=4,
        min_separation_px=4.0,
    )
    points = {(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)}

    assert result["count"] == 3
    assert result["stored_count"] == 3
    assert (10, 10) in points
    assert (11, 11) not in points
    assert (30, 30) in points
    assert (7, 40) in points


def test_gpu_star_grid_top_nms_candidates_keeps_spatial_candidates():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_grid_top_nms_candidates_f32"):
        raise AssertionError("star_grid_top_nms_candidates_f32 is missing from gpwbpp_cuda")

    image = np.zeros((64, 64), dtype=np.float32)
    image[8, 8] = 100.0
    image[10, 10] = 95.0
    image[8, 40] = 90.0
    image[40, 8] = 85.0
    image[40, 40] = 80.0

    result = module.star_grid_top_nms_candidates_f32(
        image,
        threshold=10.0,
        grid_cols=2,
        grid_rows=2,
        candidates_per_cell=2,
        max_output_candidates=8,
        min_separation_px=4.0,
    )
    points = {(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)}

    assert result["count"] == 5
    assert result["stored_count"] == 4
    assert result["grid_capacity"] == 8
    assert (8, 8) in points
    assert (10, 10) not in points
    assert (40, 8) in points
    assert (8, 40) in points
    assert (40, 40) in points
