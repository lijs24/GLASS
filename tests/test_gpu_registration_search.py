from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from glass.cpu.registration import _local_triangle_descriptors
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


def _catalog_points() -> np.ndarray:
    return np.asarray(
        [
            (10.0, 10.0),
            (20.0, 11.0),
            (13.0, 24.0),
            (32.0, 31.0),
            (6.0, 38.0),
            (38.0, 7.0),
            (27.0, 19.0),
            (16.0, 34.0),
        ],
        dtype=np.float64,
    )


def test_gpu_triangle_asterism_descriptors_match_cpu_bridge():
    module = cuda_module_or_skip()
    if not hasattr(module, "triangle_asterism_descriptors_f32"):
        raise AssertionError("triangle_asterism_descriptors_f32 is missing from glass_cuda")

    points = _catalog_points()
    expected = _local_triangle_descriptors(points, max_points=8, neighbors=5, max_descriptors=64)
    result = module.triangle_asterism_descriptors_f32(
        points[:, 0].astype(np.float32),
        points[:, 1].astype(np.float32),
        max_stars=8,
        neighbors=5,
        max_descriptors=64,
    )

    assert result["model"] == "triangle_asterism_descriptors_cuda"
    assert result["count"] == len(expected)
    assert result["neighbors"] == 5
    assert result["raw_count"] == 80
    assert np.allclose(result["descriptors"], np.asarray([item[0] for item in expected], dtype=np.float32))
    assert np.array_equal(result["indices"], np.asarray([item[1] for item in expected], dtype=np.int32))
    assert np.allclose(result["areas"], np.asarray([item[2] for item in expected], dtype=np.float32))


def test_gpu_triangle_asterism_descriptor_batch_matches_single_catalogs():
    module = cuda_module_or_skip()
    if not hasattr(module, "triangle_asterism_descriptors_batch_f32"):
        raise AssertionError("triangle_asterism_descriptors_batch_f32 is missing from glass_cuda")

    reference = _catalog_points()
    moving = reference + np.asarray([1.25, -0.75], dtype=np.float64)
    sparse = reference[:4] + np.asarray([-2.0, 1.5], dtype=np.float64)
    catalogs = [reference, moving, sparse]

    batch = module.triangle_asterism_descriptors_batch_f32(
        [catalog[:, 0].astype(np.float32) for catalog in catalogs],
        [catalog[:, 1].astype(np.float32) for catalog in catalogs],
        max_stars=8,
        neighbors=5,
        max_descriptors=64,
    )
    singles = [
        module.triangle_asterism_descriptors_f32(
            catalog[:, 0].astype(np.float32),
            catalog[:, 1].astype(np.float32),
            max_stars=8,
            neighbors=5,
            max_descriptors=64,
        )
        for catalog in catalogs
    ]

    assert len(batch) == len(singles) == 3
    assert [item["batch_index"] for item in batch] == [0, 1, 2]
    assert [item["batch_count"] for item in batch] == [3, 3, 3]
    assert batch[0]["batch_model"] == "triangle_asterism_descriptors_cuda_batch_padded_one_sync"
    assert batch[0]["batch_timing_model"] == "padded_catalog_batch_one_kernel_one_sync"
    assert batch[0]["batch_upload_s"] >= 0.0
    assert batch[0]["batch_kernel_sync_s"] >= 0.0
    assert batch[0]["batch_output_download_s"] >= 0.0
    for batch_result, single_result in zip(batch, singles, strict=True):
        assert batch_result["count"] == single_result["count"]
        assert batch_result["raw_count"] == single_result["raw_count"]
        assert batch_result["max_stars"] == single_result["max_stars"]
        assert batch_result["neighbors"] == single_result["neighbors"]
        assert np.allclose(batch_result["descriptors"], single_result["descriptors"])
        assert np.array_equal(batch_result["indices"], single_result["indices"])
        assert np.allclose(batch_result["areas"], single_result["areas"])


def test_gpu_triangle_descriptor_similarity_recovers_catalog_transform():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_triangle_descriptors_f32"):
        raise AssertionError("estimate_similarity_from_triangle_descriptors_f32 is missing from glass_cuda")

    angle = np.deg2rad(6.0)
    scale = 1.015
    linear = scale * np.asarray(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float64,
    )
    translation = np.asarray([3.5, -2.25], dtype=np.float64)
    reference = _catalog_points()
    moving = (reference - translation) @ np.linalg.inv(linear).T
    reference_descriptors = module.triangle_asterism_descriptors_f32(
        reference[:, 0].astype(np.float32),
        reference[:, 1].astype(np.float32),
        max_stars=8,
        neighbors=5,
        max_descriptors=64,
    )
    moving_descriptors = module.triangle_asterism_descriptors_f32(
        moving[:, 0].astype(np.float32),
        moving[:, 1].astype(np.float32),
        max_stars=8,
        neighbors=5,
        max_descriptors=64,
    )

    result = module.estimate_similarity_from_triangle_descriptors_f32(
        reference[:, 0].astype(np.float32),
        reference[:, 1].astype(np.float32),
        moving[:, 0].astype(np.float32),
        moving[:, 1].astype(np.float32),
        reference_descriptors["descriptors"],
        reference_descriptors["indices"],
        moving_descriptors["descriptors"],
        moving_descriptors["indices"],
        tolerance_px=0.1,
        descriptor_radius=0.01,
    )

    matrix = np.asarray(result["matrix"], dtype=np.float64)
    assert result["model"] == "triangle_descriptor_similarity_cuda"
    assert result["status"] == "ok"
    assert result["inliers"] == len(reference)
    assert result["candidate_count"] == (
        reference_descriptors["count"] * moving_descriptors["count"] * 2
    )
    assert result["rms_px"] < 1.0e-3
    assert np.allclose(matrix[:2, :2], linear, atol=1.0e-4)
    assert np.allclose(matrix[:2, 2], translation, atol=1.0e-4)


def test_gpu_triangle_descriptor_similarity_batch_matches_single_fits():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_triangle_descriptors_batch_f32"):
        raise AssertionError(
            "estimate_similarity_from_triangle_descriptors_batch_f32 is missing from glass_cuda"
        )

    reference = _catalog_points()
    transforms = [
        (np.deg2rad(4.0), 1.01, np.asarray([2.5, -1.25], dtype=np.float64)),
        (np.deg2rad(-3.0), 0.992, np.asarray([-1.75, 3.0], dtype=np.float64)),
    ]
    reference_descriptors = module.triangle_asterism_descriptors_f32(
        reference[:, 0].astype(np.float32),
        reference[:, 1].astype(np.float32),
        max_stars=8,
        neighbors=5,
        max_descriptors=64,
    )
    moving_catalogs = []
    moving_descriptors = []
    for angle, scale, translation in transforms:
        linear = scale * np.asarray(
            [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
            dtype=np.float64,
        )
        moving = (reference - translation) @ np.linalg.inv(linear).T
        moving_catalogs.append(moving)
        moving_descriptors.append(
            module.triangle_asterism_descriptors_f32(
                moving[:, 0].astype(np.float32),
                moving[:, 1].astype(np.float32),
                max_stars=8,
                neighbors=5,
                max_descriptors=64,
            )
        )

    batch = module.estimate_similarity_from_triangle_descriptors_batch_f32(
        reference[:, 0].astype(np.float32),
        reference[:, 1].astype(np.float32),
        reference_descriptors["descriptors"],
        reference_descriptors["indices"],
        [moving[:, 0].astype(np.float32) for moving in moving_catalogs],
        [moving[:, 1].astype(np.float32) for moving in moving_catalogs],
        [item["descriptors"] for item in moving_descriptors],
        [item["indices"] for item in moving_descriptors],
        tolerance_px=0.1,
        descriptor_radius=0.01,
    )
    singles = [
        module.estimate_similarity_from_triangle_descriptors_f32(
            reference[:, 0].astype(np.float32),
            reference[:, 1].astype(np.float32),
            moving[:, 0].astype(np.float32),
            moving[:, 1].astype(np.float32),
            reference_descriptors["descriptors"],
            reference_descriptors["indices"],
            descriptor["descriptors"],
            descriptor["indices"],
            tolerance_px=0.1,
            descriptor_radius=0.01,
        )
        for moving, descriptor in zip(moving_catalogs, moving_descriptors, strict=True)
    ]

    assert len(batch) == len(singles) == 2
    assert batch[0]["batch_model"] == "triangle_descriptor_similarity_cuda_batch_shared_reference_device"
    assert [item["batch_index"] for item in batch] == [0, 1]
    assert [item["batch_count"] for item in batch] == [2, 2]
    for batch_result, single_result in zip(batch, singles, strict=True):
        assert batch_result["model"] == single_result["model"]
        assert batch_result["reference_device_reuse"] is True
        assert batch_result["reference_device_bytes"] > 0
        assert batch_result["moving_device_reuse"] is True
        assert batch_result["moving_device_bytes"] > 0
        assert batch_result["output_device_reuse"] is True
        assert batch_result["output_device_bytes"] > 0
        assert batch_result["best_reduction_mode"] == "single_block_parallel_score_rms_index"
        assert single_result["best_reduction_mode"] == "single_block_parallel_score_rms_index"
        assert batch_result["batch_timing_model"] == "per_frame_reused_buffers_sync_timed"
        assert batch_result["batch_host_prepare_s"] >= 0.0
        assert batch_result["batch_reference_alloc_s"] >= 0.0
        assert batch_result["batch_reference_upload_s"] >= 0.0
        assert batch_result["batch_workspace_alloc_s"] >= 0.0
        assert batch_result["batch_frame_moving_upload_s"] >= 0.0
        assert batch_result["batch_frame_kernel_sync_s"] >= 0.0
        assert batch_result["batch_frame_output_download_s"] >= 0.0
        assert batch_result["batch_frame_total_s"] + 1.0e-6 >= (
            batch_result["batch_frame_moving_upload_s"]
            + batch_result["batch_frame_kernel_sync_s"]
            + batch_result["batch_frame_output_download_s"]
        )
        assert batch_result["status"] == "ok"
        assert batch_result["inliers"] == single_result["inliers"]
        assert batch_result["best_candidate_index"] == single_result["best_candidate_index"]
        assert batch_result["candidate_count"] == single_result["candidate_count"]
        assert abs(batch_result["rms_px"] - single_result["rms_px"]) < 1.0e-6
        assert np.allclose(batch_result["matrix"], single_result["matrix"], rtol=1e-6, atol=1e-6)


def test_gpu_triangle_descriptor_image_registration_improves_alignment():
    cuda_module_or_skip()
    from glass.gpu.registration import register_triangle_descriptor_similarity_f32

    shape = (96, 112)
    stars = np.asarray(
        [
            (12.0, 17.0, 100.0),
            (30.0, 42.0, 220.0),
            (71.0, 15.0, 160.0),
            (88.0, 63.0, 180.0),
            (45.0, 79.0, 250.0),
            (19.0, 86.0, 130.0),
            (101.0, 33.0, 145.0),
            (53.0, 55.0, 190.0),
        ],
        dtype=np.float64,
    )
    angle = np.deg2rad(3.0)
    linear = np.asarray(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float64,
    )
    translation = np.asarray([2.0, -1.0], dtype=np.float64)
    moving_xy = (stars[:, :2] - translation) @ np.linalg.inv(linear).T
    reference = _render_catalog_field(shape, stars)
    moving = _render_catalog_field(shape, np.column_stack([moving_xy, stars[:, 2]]))

    aligned, coverage, diagnostics = register_triangle_descriptor_similarity_f32(
        reference,
        moving,
        threshold=25.0,
        max_candidates=32,
        neighbors=5,
        max_descriptors=256,
        tolerance_px=2.0,
        descriptor_radius=0.08,
        nms_scan_candidates=128,
        nms_min_separation_px=3.0,
    )

    valid = coverage > 0.0
    before_rms = float(np.sqrt(np.mean((moving[valid] - reference[valid]) ** 2)))
    after_rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))
    matrix = np.asarray(diagnostics["matrix"], dtype=np.float64)
    assert diagnostics["model"] == "gpu_triangle_descriptor_similarity_registration"
    assert diagnostics["status"] == "ok"
    assert diagnostics["similarity"]["inliers"] == len(stars)
    assert diagnostics["reference_descriptor_count"] > 0
    assert diagnostics["moving_descriptor_count"] > 0
    assert after_rms < before_rms * 0.5
    assert np.allclose(matrix[:2, :2], linear, atol=0.01)
    assert np.allclose(matrix[:2, 2], translation, atol=0.75)


def test_gpu_triangle_descriptor_image_registration_supports_grid_top_selector():
    cuda_module_or_skip()
    from glass.gpu.registration import register_triangle_descriptor_similarity_f32

    shape = (96, 112)
    stars = np.asarray(
        [
            (12.0, 17.0, 100.0),
            (30.0, 42.0, 220.0),
            (71.0, 15.0, 160.0),
            (88.0, 63.0, 180.0),
            (45.0, 79.0, 250.0),
            (19.0, 86.0, 130.0),
            (101.0, 33.0, 145.0),
            (53.0, 55.0, 190.0),
        ],
        dtype=np.float64,
    )
    translation = np.asarray([2.0, -1.0], dtype=np.float64)
    reference = _render_catalog_field(shape, stars)
    moving = _render_catalog_field(shape, np.column_stack([stars[:, :2] - translation, stars[:, 2]]))

    aligned, coverage, diagnostics = register_triangle_descriptor_similarity_f32(
        reference,
        moving,
        threshold=25.0,
        max_candidates=32,
        neighbors=5,
        max_descriptors=256,
        tolerance_px=2.0,
        descriptor_radius=0.08,
        grid_top_cols=4,
        grid_top_rows=3,
        grid_top_candidates_per_cell=3,
        nms_min_separation_px=3.0,
    )

    valid = coverage > 0.0
    before_rms = float(np.sqrt(np.mean((moving[valid] - reference[valid]) ** 2)))
    after_rms = float(np.sqrt(np.mean((aligned[valid] - reference[valid]) ** 2)))
    matrix = np.asarray(diagnostics["matrix"], dtype=np.float64)
    assert diagnostics["catalog_selector"] == "grid_top_nms"
    assert diagnostics["status"] == "ok"
    assert diagnostics["reference_stored"] >= len(stars)
    assert diagnostics["moving_stored"] >= len(stars)
    assert diagnostics["similarity"]["inliers"] >= len(stars)
    assert after_rms < before_rms * 0.5
    assert np.allclose(matrix[:2, 2], translation, atol=0.75)


def test_gpu_estimate_translation_search_aligns_shifted_pair():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_translation_search_f32"):
        raise AssertionError("estimate_translation_search_f32 is missing from glass_cuda")

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
        raise AssertionError("estimate_translation_subpixel_ncc_f32 is missing from glass_cuda")

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
        raise AssertionError("matrix_alignment_metrics_f32 is missing from glass_cuda")

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
        raise AssertionError("matrix_alignment_metrics_f32 is missing from glass_cuda")

    reference = _smooth_star_field()
    good_matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    bad_matrix = np.asarray([[1.0, 0.0, -1.0], [0.0, 1.0, 2.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(good_matrix).astype(np.float32), 0.0)

    good = module.matrix_alignment_metrics_f32(reference, moving, good_matrix, sample_stride=2)
    bad = module.matrix_alignment_metrics_f32(reference, moving, bad_matrix, sample_stride=2)

    assert good["sample_stride"] == 2
    assert good["rms"] < bad["rms"] * 0.5
    assert good["ncc"] > bad["ncc"]


def test_gpu_matrix_metric_translation_refine_improves_offset_matrix():
    module = cuda_module_or_skip()
    if not hasattr(module, "matrix_alignment_metrics_f32"):
        raise AssertionError("matrix_alignment_metrics_f32 is missing from glass_cuda")
    from glass.gpu.registration import refine_matrix_translation_with_metrics_f32

    reference = _smooth_star_field()
    good_matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(good_matrix).astype(np.float32), 0.0)
    offset_matrix = good_matrix.copy()
    offset_matrix[0, 2] += 0.5
    offset_matrix[1, 2] -= 0.375

    before = module.matrix_alignment_metrics_f32(reference, moving, offset_matrix, sample_stride=1)
    refined = refine_matrix_translation_with_metrics_f32(
        reference,
        moving,
        offset_matrix,
        search_radius_px=0.75,
        coarse_step_px=0.25,
        fine_radius_px=0.125,
        fine_step_px=0.125,
        coarse_sample_stride=1,
        final_sample_stride=1,
    )
    after = refined["metrics"]
    matrix = np.asarray(refined["matrix"], dtype=np.float32)

    assert after["rms"] < before["rms"] * 0.6
    assert after["ncc"] > before["ncc"]
    assert refined["model"] == "cuda_matrix_metric_translation_refine_grid"
    assert after["model"] == "matrix_alignment_metrics_cuda_candidate_grid"
    assert abs(matrix[0, 2] - good_matrix[0, 2]) <= 0.125
    assert abs(matrix[1, 2] - good_matrix[1, 2]) <= 0.125
    assert refined["coarse_candidates"] > 0
    assert refined["fine_candidates"] > 0


def test_gpu_matrix_metric_multi_seed_refine_selects_best_seed():
    module = cuda_module_or_skip()
    if not hasattr(module, "refine_matrix_translation_candidates_with_metrics_f32"):
        raise AssertionError("refine_matrix_translation_candidates_with_metrics_f32 is missing from glass_cuda")

    reference = _smooth_star_field()
    good_matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(good_matrix).astype(np.float32), 0.0)
    bad_seed = good_matrix.copy()
    bad_seed[0, 2] += 3.0
    bad_seed[1, 2] -= 3.0
    close_seed = good_matrix.copy()
    close_seed[0, 2] += 0.5
    close_seed[1, 2] -= 0.375

    result = module.refine_matrix_translation_candidates_with_metrics_f32(
        reference,
        moving,
        np.stack([bad_seed, close_seed]),
        search_radius_px=0.75,
        coarse_step_px=0.25,
        fine_radius_px=0.125,
        fine_step_px=0.125,
        coarse_sample_stride=1,
        final_sample_stride=1,
    )
    matrix = np.asarray(result["matrix"], dtype=np.float32)

    assert result["model"] == "cuda_matrix_metric_translation_multi_seed_refine_grid"
    assert result["seed_count"] == 2
    assert len(result["seed_results"]) == 2
    assert result["selected_index"] == 1
    assert result["coarse_candidates_per_seed"] > 0
    assert result["metrics"]["rms"] == result["seed_results"][1]["metrics"]["rms"]
    assert abs(matrix[0, 2] - good_matrix[0, 2]) <= 0.125
    assert abs(matrix[1, 2] - good_matrix[1, 2]) <= 0.125


def test_resident_stack_matrix_metric_multi_seed_refine_uses_loaded_frames():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    reference = _smooth_star_field()
    good_matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(good_matrix).astype(np.float32), 0.0)
    bad_seed = good_matrix.copy()
    bad_seed[0, 2] += 3.0
    bad_seed[1, 2] -= 3.0
    close_seed = good_matrix.copy()
    close_seed[0, 2] += 0.5
    close_seed[1, 2] -= 0.375

    stack = module.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    result = stack.refine_matrix_translation_candidates_to_reference(
        0,
        1,
        np.stack([bad_seed, close_seed]),
        search_radius_px=0.75,
        coarse_step_px=0.25,
        fine_radius_px=0.125,
        fine_step_px=0.125,
        coarse_sample_stride=1,
        final_sample_stride=1,
    )
    matrix = np.asarray(result["matrix"], dtype=np.float32)

    assert result["model"] == "resident_cuda_matrix_metric_translation_multi_seed_refine_grid"
    assert result["reference_index"] == 0
    assert result["moving_index"] == 1
    assert result["seed_count"] == 2
    assert result["selected_index"] == 1
    assert abs(matrix[0, 2] - good_matrix[0, 2]) <= 0.125
    assert abs(matrix[1, 2] - good_matrix[1, 2]) <= 0.125


def test_resident_stack_star_core_candidate_metrics_match_cpu():
    module = cuda_module_or_skip()
    if not hasattr(module, "ResidentCalibratedStack"):
        raise AssertionError("ResidentCalibratedStack is missing from glass_cuda")

    reference = _smooth_star_field()
    good_matrix = np.asarray([[1.0, 0.0, 2.25], [0.0, 1.0, -1.5], [0.0, 0.0, 1.0]], dtype=np.float32)
    moving, _ = module.warp_matrix_bilinear_f32(reference, np.linalg.inv(good_matrix).astype(np.float32), 0.0)
    bad_matrix = good_matrix.copy()
    bad_matrix[0, 2] += 2.0
    bad_matrix[1, 2] -= 2.0
    matrices = np.stack([good_matrix, bad_matrix]).astype(np.float32)
    threshold = float(np.median(reference) + 4.0 * np.std(reference))

    stack = module.ResidentCalibratedStack(2, reference.shape[0], reference.shape[1])
    stack.upload_calibrated_frame(0, reference)
    stack.upload_calibrated_frame(1, moving)
    result = stack.star_core_metrics_candidates_to_reference(0, 1, matrices, threshold)

    def cpu_star_core_rms(matrix: np.ndarray) -> float:
        inverse = np.linalg.inv(matrix.astype(np.float64))
        ys, xs = np.nonzero(reference > threshold)
        x = xs.astype(np.float64)
        y = ys.astype(np.float64)
        sx = inverse[0, 0] * x + inverse[0, 1] * y + inverse[0, 2]
        sy = inverse[1, 0] * x + inverse[1, 1] * y + inverse[1, 2]
        valid = (sx >= 0.0) & (sx <= reference.shape[1] - 1) & (sy >= 0.0) & (sy <= reference.shape[0] - 1)
        sx = sx[valid]
        sy = sy[valid]
        ref_values = reference[ys[valid], xs[valid]].astype(np.float64)
        x0 = np.floor(sx).astype(np.int64)
        y0 = np.floor(sy).astype(np.int64)
        x1 = np.minimum(x0 + 1, reference.shape[1] - 1)
        y1 = np.minimum(y0 + 1, reference.shape[0] - 1)
        tx = sx - x0
        ty = sy - y0
        sampled = (
            moving[y0, x0] * (1.0 - tx) * (1.0 - ty)
            + moving[y0, x1] * tx * (1.0 - ty)
            + moving[y1, x0] * (1.0 - tx) * ty
            + moving[y1, x1] * tx * ty
        )
        diff = sampled - ref_values
        return float(np.sqrt(np.mean(diff * diff)))

    metrics = [dict(item["metrics"]) for item in result["candidate_metrics"]]

    assert result["model"] == "resident_star_core_bilinear_metric_cuda"
    assert result["candidate_count"] == 2
    assert metrics[0]["valid_pixels"] > 0
    assert metrics[0]["rms"] < metrics[1]["rms"]
    assert metrics[0]["rms"] == pytest.approx(cpu_star_core_rms(good_matrix), rel=1e-5, abs=1e-4)
    assert metrics[1]["rms"] == pytest.approx(cpu_star_core_rms(bad_matrix), rel=1e-5, abs=1e-4)


def test_gpu_estimate_translation_from_catalogs_votes_pair_offsets():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_translation_from_catalogs_f32"):
        raise AssertionError("estimate_translation_from_catalogs_f32 is missing from glass_cuda")

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
        raise AssertionError("estimate_translation_from_catalogs_f32 is missing from glass_cuda")

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
        raise AssertionError("estimate_translation_from_catalogs_f32 is missing from glass_cuda")

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
        raise AssertionError("estimate_similarity_from_pairs_f32 is missing from glass_cuda")

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
        raise AssertionError("estimate_similarity_from_catalogs_f32 is missing from glass_cuda")

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
        top_k=4,
    )
    matrix = np.asarray(result["matrix"], dtype=np.float32)

    assert result["status"] == "ok"
    assert result["model"] == "catalog_pair_similarity_cuda"
    assert result["inliers"] >= len(moving)
    assert result["refined_inliers"] >= len(moving)
    assert result["refit_status"] in {"ok", "rejected"}
    assert result["top_k"] == 4
    assert len(result["top_candidates"]) == 4
    assert result["top_candidates"][0]["inliers"] >= result["top_candidates"][-1]["inliers"]
    assert np.asarray(result["top_candidates"][0]["matrix"], dtype=np.float32).shape == (3, 3)
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


def test_gpu_estimate_similarity_from_catalogs_refits_seed_inliers():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_catalogs_f32"):
        raise AssertionError("estimate_similarity_from_catalogs_f32 is missing from glass_cuda")

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
            (84.0, 52.0),
            (48.0, 74.0),
        ],
        dtype=np.float32,
    )
    angle = np.deg2rad(2.5)
    scale = 1.01
    linear = scale * np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]],
        dtype=np.float32,
    )
    translation = np.array([3.5, -2.25], dtype=np.float32)
    jitter = np.array(
        [
            (0.04, -0.02),
            (-0.03, 0.02),
            (0.01, 0.03),
            (-0.02, -0.04),
            (0.03, 0.01),
            (-0.01, -0.03),
            (0.02, 0.04),
            (-0.04, 0.00),
            (0.01, -0.01),
            (0.00, 0.02),
        ],
        dtype=np.float32,
    )
    reference = moving @ linear.T + translation + jitter
    moving_catalog = np.vstack([moving, np.array([[2.0, 88.0], [95.0, 9.0]], dtype=np.float32)])
    reference_catalog = np.vstack([reference, np.array([[88.0, 4.0], [5.0, 92.0]], dtype=np.float32)])

    result = module.estimate_similarity_from_catalogs_f32(
        reference_catalog[:, 0],
        reference_catalog[:, 1],
        moving_catalog[:, 0],
        moving_catalog[:, 1],
        tolerance_px=0.25,
        min_pair_distance=5.0,
        prior_dx=float(translation[0]),
        prior_dy=float(translation[1]),
        prior_radius_px=2.0,
        min_scale=0.98,
        max_scale=1.04,
        max_abs_rotation_rad=0.1,
    )
    matrix = np.asarray(result["matrix"], dtype=np.float32)

    assert result["status"] == "ok"
    assert result["refit_status"] == "ok"
    assert result["refined_inliers"] >= len(moving)
    assert result["rms_px"] < 0.08
    assert np.allclose(matrix[:2, :2], linear, atol=0.003)
    assert np.allclose(matrix[:2, 2], translation, atol=0.12)


def test_gpu_similarity_catalog_registration_aligns_synthetic_images():
    module = cuda_module_or_skip()
    if not hasattr(module, "estimate_similarity_from_catalogs_f32"):
        raise AssertionError("estimate_similarity_from_catalogs_f32 is missing from glass_cuda")
    from glass.gpu.registration import register_similarity_from_star_catalogs_f32

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


def test_register_calibrated_frames_can_use_cuda_catalog_backend(tmp_path: Path):
    cuda_module_or_skip()
    from glass.engine.registration import register_calibrated_frames
    from glass.io.fits_io import write_fits_data
    from glass.io.json_io import write_json

    reference = _star_field()
    moving = _shift_image(reference, 4, -3)
    run = tmp_path / "run"
    cache = run / "calibrated_cache"
    cache.mkdir(parents=True)
    ref_path = cache / "ref.fits"
    moving_path = cache / "moving.fits"
    write_fits_data(ref_path, reference)
    write_fits_data(moving_path, moving)
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "calibrated_lights": [
                {"frame_id": "ref", "path": str(ref_path)},
                {"frame_id": "moving", "path": str(moving_path)},
            ],
        },
    )
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": "ref",
            "frame_quality": [
                {"frame_id": "ref", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
                {"frame_id": "moving", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
            ],
        },
    )
    write_json(
        run / "processing_plan.json",
        {
            "schema_version": 1,
            "registration_policy": {
                "transform_model": "similarity",
                "min_inliers": 6,
                "cuda_catalog_threshold_sigma": 3.0,
                "cuda_catalog_max_stars": 24,
                "cuda_catalog_tolerance_px": 1.5,
                "cuda_catalog_min_pair_distance": 8.0,
                "cuda_catalog_grid_top_cols": 0,
                "cuda_catalog_grid_top_rows": 0,
                "cuda_catalog_nms_scan_candidates": 128,
                "cuda_catalog_nms_min_separation_px": 4.0,
                "cuda_catalog_prior": "ncc",
                "cuda_catalog_prior_radius_px": 2.0,
                "cuda_catalog_min_scale": 0.99,
                "cuda_catalog_max_scale": 1.01,
                "cuda_catalog_max_abs_rotation_rad": 0.02,
                "cuda_catalog_similarity_top_k": 4,
                "cuda_catalog_pixel_refine_coarse_stride": 1,
                "cuda_catalog_pixel_refine_final_stride": 1,
            },
        },
    )

    payload = register_calibrated_frames(run, tile_size=64, preview_max_dimension=256, method="cuda_catalog")
    moving_result = next(item for item in payload["registration_results"] if item["frame_id"] == "moving")

    assert payload["method"] == "cuda_catalog"
    assert payload["transform_model"] == "similarity"
    assert payload["cuda_catalog"]["native_cuda_required"] is True
    assert moving_result["status"] == "ok"
    assert moving_result["registration_solution_source"] == "cuda_catalog_similarity_preview"
    assert moving_result["cuda_catalog"]["selection_model"] == "global_top_flux_local_maximum_nms"
    assert moving_result["cuda_catalog"]["similarity_top_k"] == 4
    assert moving_result["cuda_catalog"]["top_candidate_count"] == 4
    assert len(moving_result["cuda_catalog"]["top_candidates"]) == 4
    assert moving_result["cuda_catalog"]["pixel_refine"] is not None
    assert moving_result["cuda_catalog"]["pixel_refine"]["seed_count"] == 5
    assert moving_result["cuda_catalog"]["prior"]["model"].startswith("translation_")
    assert moving_result["inliers"] >= 6
    assert abs(moving_result["matrix"][0][2] + 4.0) < 0.75
    assert abs(moving_result["matrix"][1][2] - 3.0) < 0.75
    assert any("cuda catalog similarity" in warning for warning in moving_result["warnings"])


def test_register_calibrated_frames_can_use_cuda_triangle_backend(tmp_path: Path):
    cuda_module_or_skip()
    from glass.engine.registration import register_calibrated_frames
    from glass.io.fits_io import write_fits_data
    from glass.io.json_io import write_json

    reference = _star_field()
    moving = _shift_image(reference, 4, -3)
    run = tmp_path / "run"
    cache = run / "calibrated_cache"
    cache.mkdir(parents=True)
    ref_path = cache / "ref.fits"
    moving_path = cache / "moving.fits"
    write_fits_data(ref_path, reference)
    write_fits_data(moving_path, moving)
    write_json(
        run / "calibration_artifacts.json",
        {
            "schema_version": 1,
            "calibrated_lights": [
                {"frame_id": "ref", "path": str(ref_path)},
                {"frame_id": "moving", "path": str(moving_path)},
            ],
        },
    )
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": "ref",
            "frame_quality": [
                {"frame_id": "ref", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
                {"frame_id": "moving", "background_median": 10.0, "background_rms": 1.0, "star_count": 8},
            ],
        },
    )
    write_json(
        run / "processing_plan.json",
        {
            "schema_version": 1,
            "registration_policy": {
                "transform_model": "similarity",
                "min_inliers": 6,
                "cuda_triangle_threshold_sigma": 3.0,
                "cuda_triangle_max_stars": 32,
                "cuda_triangle_tolerance_px": 2.0,
                "cuda_triangle_descriptor_radius": 0.08,
                "cuda_triangle_neighbors": 5,
                "cuda_triangle_max_descriptors": 256,
                "cuda_triangle_grid_top_cols": 0,
                "cuda_triangle_grid_top_rows": 0,
                "cuda_triangle_nms_scan_candidates": 128,
                "cuda_triangle_nms_min_separation_px": 4.0,
            },
        },
    )

    payload = register_calibrated_frames(run, tile_size=64, preview_max_dimension=256, method="cuda_triangle")
    moving_result = next(item for item in payload["registration_results"] if item["frame_id"] == "moving")

    assert payload["method"] == "cuda_triangle"
    assert payload["transform_model"] == "similarity"
    assert payload["cuda_triangle"]["native_cuda_required"] is True
    assert payload["cuda_triangle"]["descriptor"] == "triangle_similarity"
    assert moving_result["status"] == "ok"
    assert moving_result["registration_solution_source"] == "cuda_triangle_descriptor_similarity_preview"
    assert moving_result["cuda_triangle"]["selection_model"] == "global_top_flux_local_maximum_nms"
    assert moving_result["cuda_triangle"]["reference_descriptor_count"] > 0
    assert moving_result["cuda_triangle"]["moving_descriptor_count"] > 0
    assert moving_result["cuda_triangle"]["similarity"]["model"] == "triangle_descriptor_similarity_cuda"
    assert moving_result["inliers"] >= 6
    assert abs(moving_result["matrix"][0][2] + 4.0) < 0.75
    assert abs(moving_result["matrix"][1][2] - 3.0) < 0.75
    assert any("cuda triangle descriptor similarity" in warning for warning in moving_result["warnings"])


def test_gpu_star_top_nms_candidates_suppresses_close_peaks():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_top_nms_candidates_f32"):
        raise AssertionError("star_top_nms_candidates_f32 is missing from glass_cuda")

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


def _cpu_grid_top_nms_reference(
    image: np.ndarray,
    *,
    threshold: float,
    grid_cols: int,
    grid_rows: int,
    candidates_per_cell: int,
    max_output_candidates: int,
    min_separation_px: float,
) -> list[tuple[float, float, float]]:
    candidates: list[tuple[float, float, float]] = []
    height, width = image.shape
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            center = float(image[y, x])
            if not np.isfinite(center) or center <= threshold:
                continue
            patch = image[y - 1 : y + 2, x - 1 : x + 2]
            if np.any(center < patch):
                continue
            candidates.append((float(x), float(y), center))

    per_cell: list[list[tuple[float, float, float]]] = [[] for _ in range(grid_cols * grid_rows)]
    for x, y, flux in candidates:
        cell_x = min((int(x) * grid_cols) // width, grid_cols - 1)
        cell_y = min((int(y) * grid_rows) // height, grid_rows - 1)
        per_cell[cell_y * grid_cols + cell_x].append((x, y, flux))

    compact: list[tuple[float, float, float]] = []
    for cell in per_cell:
        cell.sort(key=lambda item: (-item[2], item[1], item[0]))
        compact.extend(cell[:candidates_per_cell])
    compact.sort(key=lambda item: (-item[2], item[1], item[0]))

    selected: list[tuple[float, float, float]] = []
    min_separation2 = min_separation_px * min_separation_px
    for x, y, flux in compact:
        if len(selected) >= max_output_candidates:
            break
        if all((x - kept_x) ** 2 + (y - kept_y) ** 2 >= min_separation2 for kept_x, kept_y, _ in selected):
            selected.append((x, y, flux))
    return selected


def test_gpu_star_grid_top_nms_candidates_keeps_spatial_candidates():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_grid_top_nms_candidates_f32"):
        raise AssertionError("star_grid_top_nms_candidates_f32 is missing from glass_cuda")

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
    assert result["catalog_sort_mode"] == "shared_bitonic_power2"
    assert result["catalog_topk_mode"] == "strict_flux_precheck_per_cell_lock"
    assert (8, 8) in points
    assert (10, 10) not in points
    assert (40, 8) in points
    assert (8, 40) in points
    assert (40, 40) in points


def test_gpu_star_grid_top_nms_candidates_matches_cpu_reference_for_non_power2_capacity():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_grid_top_nms_candidates_f32"):
        raise AssertionError("star_grid_top_nms_candidates_f32 is missing from glass_cuda")

    image = np.zeros((31, 37), dtype=np.float32)
    for x, y, flux in [
        (4, 4, 100.0),
        (6, 4, 99.0),
        (12, 8, 180.0),
        (25, 7, 150.0),
        (30, 14, 170.0),
        (7, 20, 160.0),
        (18, 21, 130.0),
        (31, 25, 140.0),
        (34, 27, 135.0),
    ]:
        image[y, x] = flux

    result = module.star_grid_top_nms_candidates_f32(
        image,
        threshold=10.0,
        grid_cols=5,
        grid_rows=3,
        candidates_per_cell=3,
        max_output_candidates=8,
        min_separation_px=3.0,
    )
    expected = _cpu_grid_top_nms_reference(
        image,
        threshold=10.0,
        grid_cols=5,
        grid_rows=3,
        candidates_per_cell=3,
        max_output_candidates=8,
        min_separation_px=3.0,
    )
    points = [
        (float(x), float(y), float(flux))
        for x, y, flux in zip(result["x"], result["y"], result["flux"], strict=True)
    ]

    assert result["grid_capacity"] == 45
    assert result["catalog_sort_mode"] == "shared_bitonic_power2"
    assert result["catalog_topk_mode"] == "strict_flux_precheck_per_cell_lock"
    assert result["stored_count"] == len(expected)
    assert points == expected


def test_gpu_star_grid_top_nms_candidates_precheck_preserves_tie_breaks():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_grid_top_nms_candidates_f32"):
        raise AssertionError("star_grid_top_nms_candidates_f32 is missing from glass_cuda")

    image = np.zeros((18, 18), dtype=np.float32)
    image[4, 4] = 100.0
    image[4, 7] = 100.0
    image[7, 4] = 100.0
    image[7, 7] = 100.0
    image[12, 12] = 10.0

    result = module.star_grid_top_nms_candidates_f32(
        image,
        threshold=1.0,
        grid_cols=1,
        grid_rows=1,
        candidates_per_cell=4,
        max_output_candidates=4,
        min_separation_px=0.0,
    )
    points = [(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)]

    assert result["catalog_topk_mode"] == "strict_flux_precheck_per_cell_lock"
    assert result["count"] == 5
    assert result["stored_count"] == 4
    assert points == [(4, 4), (7, 4), (4, 7), (7, 7)]


def test_gpu_star_top_candidates_tie_breaks_saturated_plateau_deterministically():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_top_candidates_f32"):
        raise AssertionError("star_top_candidates_f32 is missing from glass_cuda")

    image = np.zeros((12, 12), dtype=np.float32)
    image[4:6, 4:6] = 100.0

    expected = [(4, 4), (5, 4)]
    for _ in range(5):
        result = module.star_top_candidates_f32(image, threshold=10.0, max_candidates=2)
        points = [(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)]
        assert points == expected


def test_gpu_star_grid_top_nms_candidates_tie_breaks_saturated_plateau_deterministically():
    module = cuda_module_or_skip()
    if not hasattr(module, "star_grid_top_nms_candidates_f32"):
        raise AssertionError("star_grid_top_nms_candidates_f32 is missing from glass_cuda")

    image = np.zeros((12, 12), dtype=np.float32)
    image[4:6, 4:6] = 100.0

    expected = [(4, 4), (5, 4), (4, 5), (5, 5)]
    for _ in range(5):
        result = module.star_grid_top_nms_candidates_f32(
            image,
            threshold=10.0,
            grid_cols=1,
            grid_rows=1,
            candidates_per_cell=4,
            max_output_candidates=4,
            min_separation_px=0.0,
        )
        points = [(int(x), int(y)) for x, y in zip(result["x"], result["y"], strict=True)]
        assert points == expected
