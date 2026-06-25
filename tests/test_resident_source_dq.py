from __future__ import annotations

import numpy as np
import pytest

from glass.cpu.cosmetic import (
    detect_isolated_cosmetic_defects,
    detect_star_protected_cosmetic_defects,
)
from glass.engine.contracts import DQFlag
from glass.engine.resident_source_dq import (
    apply_resident_inline_cosmetic_thresholds_batch,
    build_resident_source_dq_execution_group,
    build_resident_source_dq_summary,
    combine_source_invalid_masks,
    inline_cosmetic_thresholds_batch_from_resident_stack,
    inline_cosmetic_thresholds_from_array,
    inline_cosmetic_thresholds_from_resident_stack,
    source_invalid_mask_from_array,
    source_invalid_mask_from_dq_mask,
    source_invalid_mask_from_inline_cosmetic,
    source_invalid_mask_from_star_protected_inline_cosmetic,
    source_invalid_mask_from_sidecar_path,
    summarize_resident_source_dq_execution_groups,
)
from glass.io.fits_io import write_fits_data


def test_source_invalid_mask_from_array_accounts_nonfinite_samples_without_dq_flags():
    data = np.array([[1.0, np.nan], [np.inf, 4.0]], dtype=np.float32)

    mask, info = source_invalid_mask_from_array(data, height=2, width=2)

    assert mask is not None
    assert mask.tolist() == [[0, 1], [1, 0]]
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 0
    assert info["nonfinite_samples"] == 2
    assert info["flag_counts"] == {}


def test_source_invalid_mask_from_dq_mask_preserves_flag_counts():
    dq = np.zeros((2, 3), dtype=np.uint32)
    dq[0, 1] = np.uint32(int(DQFlag.HOT_PIXEL))
    dq[1, 2] = np.uint32(int(DQFlag.NO_DATA) | int(DQFlag.SATURATED))

    mask, info = source_invalid_mask_from_dq_mask(dq, height=2, width=3)

    assert mask is not None
    assert mask.tolist() == [[0, 1, 0], [0, 0, 1]]
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 2
    assert info["nonfinite_samples"] == 0
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["no_data"] == 1
    assert info["flag_counts"]["saturated"] == 1


def test_source_invalid_mask_from_inline_cosmetic_flags_hot_and_cold_samples_without_replacement():
    data = np.full((5, 5), 100.0, dtype=np.float32)
    data[1, 2] = 1000.0
    data[3, 4] = -1000.0

    mask, info = source_invalid_mask_from_inline_cosmetic(
        data,
        height=5,
        width=5,
        hot_sigma=2.0,
        cold_sigma=2.0,
    )

    assert mask is not None
    assert int(mask[1, 2]) == 1
    assert int(mask[3, 4]) == 1
    assert info["source_model"] == "inline_structure_cosmetic_source_dq"
    assert info["inline_source_dq"] is True
    assert info["inline_source_dq_applies_replacement"] is False
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 2
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["cold_pixel"] == 1
    assert info["flag_counts"]["cosmetic_corrected"] == 2
    assert info["cosmetic_metrics"]["hot_pixels"] == 1
    assert info["cosmetic_metrics"]["cold_pixels"] == 1
    assert info["inline_source_dq_detector"] == "glass.cpu.cosmetic.detect_isolated_cosmetic_defects"


def test_source_invalid_mask_from_inline_cosmetic_protects_star_like_structure():
    data = np.full((9, 9), 100.0, dtype=np.float32)
    data[1, 1] = 1000.0
    data[4, 4] = 1000.0
    for y in range(3, 6):
        for x in range(3, 6):
            if (y, x) != (4, 4):
                data[y, x] = 650.0

    mask, info = source_invalid_mask_from_inline_cosmetic(
        data,
        height=9,
        width=9,
        hot_sigma=2.0,
        cold_sigma=2.0,
    )

    assert mask is not None
    assert int(mask[1, 1]) == 1
    assert int(mask[4, 4]) == 0
    assert info["source_model"] == "inline_structure_cosmetic_source_dq"
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["cosmetic_corrected"] == 1
    assert info["cosmetic_metrics"]["candidate_hot_pixels"] >= 2
    assert info["cosmetic_metrics"]["protected_hot_pixels"] >= 1


def test_star_protected_cosmetic_detector_keeps_compact_star_but_flags_hot_pixel():
    data = np.full((15, 15), 100.0, dtype=np.float32)
    data[2, 2] = 900.0
    data[7, 7] = 700.0
    data[7, 6] = 180.0
    data[7, 8] = 180.0
    data[6, 7] = 180.0
    data[8, 7] = 180.0

    isolated = detect_isolated_cosmetic_defects(
        data,
        hot_sigma=2.0,
        cold_sigma=2.0,
        min_neighbor_support=6,
    )
    protected = detect_star_protected_cosmetic_defects(
        data,
        hot_sigma=2.0,
        cold_sigma=2.0,
        min_neighbor_support=6,
        star_threshold_sigma=2.0,
        star_protection_radius_px=2.2,
    )

    assert isolated.dq_mask.has_flag(DQFlag.HOT_PIXEL)[2, 2]
    assert isolated.dq_mask.has_flag(DQFlag.HOT_PIXEL)[7, 7]
    assert protected.dq_mask.has_flag(DQFlag.HOT_PIXEL)[2, 2]
    assert not protected.dq_mask.has_flag(DQFlag.HOT_PIXEL)[7, 7]
    assert protected.data[7, 7] == pytest.approx(700.0)
    assert protected.metrics["star_count"] >= 1
    assert protected.metrics["star_protected_hot_pixels"] >= 1
    assert protected.metrics["hot_pixels"] == 1


def test_source_invalid_mask_from_star_protected_inline_cosmetic_records_star_model():
    data = np.full((15, 15), 100.0, dtype=np.float32)
    data[2, 2] = 900.0
    data[7, 7] = 700.0
    data[7, 6] = 180.0
    data[7, 8] = 180.0
    data[6, 7] = 180.0
    data[8, 7] = 180.0

    mask, info = source_invalid_mask_from_star_protected_inline_cosmetic(
        data,
        height=15,
        width=15,
        hot_sigma=2.0,
        cold_sigma=2.0,
        star_threshold_sigma=2.0,
        star_protection_radius_px=2.2,
    )

    assert mask is not None
    assert int(mask[2, 2]) == 1
    assert int(mask[7, 7]) == 0
    assert info["source_model"] == "inline_star_protected_cosmetic_source_dq"
    assert info["inline_source_dq"] is True
    assert info["inline_source_dq_detector"] == (
        "glass.cpu.cosmetic.detect_star_protected_cosmetic_defects"
    )
    assert info["inline_source_dq_applies_replacement"] is False
    assert info["invalid_samples"] == 1
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["cosmetic_corrected"] == 1
    assert info["cosmetic_metrics"]["star_protection_enabled"] is True
    assert info["cosmetic_metrics"]["star_protected_hot_pixels"] >= 1


def test_inline_cosmetic_thresholds_match_cpu_baseline_scalar_thresholds():
    data = np.full((5, 5), 100.0, dtype=np.float32)
    data[1, 2] = 1000.0
    data[3, 4] = -1000.0

    _mask, cpu_info = source_invalid_mask_from_inline_cosmetic(
        data,
        height=5,
        width=5,
        hot_sigma=2.0,
        cold_sigma=2.0,
    )
    threshold_info = inline_cosmetic_thresholds_from_array(
        data,
        height=5,
        width=5,
        hot_sigma=2.0,
        cold_sigma=2.0,
    )

    median = float(cpu_info["cosmetic_metrics"]["median"])
    sigma = float(cpu_info["cosmetic_metrics"]["sigma"])
    assert threshold_info["source_model"] == "inline_structure_cosmetic_cuda_thresholds"
    assert threshold_info["inline_source_dq_detector"] == (
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
    )
    assert threshold_info["threshold_source"] == "cpu_median_mad_scalar"
    assert threshold_info["detector_execution"] == "cuda_isolated_threshold_apply"
    assert threshold_info["inline_source_dq_applies_replacement"] is False
    assert threshold_info["structure_sigma"] == pytest.approx(1.5)
    assert threshold_info["min_neighbor_support"] == 2
    assert threshold_info["low_threshold"] == pytest.approx(float(np.float32(median - 2.0 * sigma)))
    assert threshold_info["high_threshold"] == pytest.approx(float(np.float32(median + 2.0 * sigma)))


def test_inline_cosmetic_thresholds_from_resident_stack_records_histogram_native_stats():
    class FakeResidentStack:
        def frame_histogram_robust_stats(
            self,
            frame_index: int,
            bin_count: int,
            hot_sigma: float,
            cold_sigma: float,
        ) -> dict[str, object]:
            assert frame_index == 3
            assert bin_count == 4096
            assert hot_sigma == pytest.approx(2.0)
            assert cold_sigma == pytest.approx(3.0)
            return {
                "native_method": "ResidentCalibratedStack.frame_histogram_robust_stats",
                "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                "stats_domain": "resident_calibrated_frame",
                "robust_stats_execution": "cuda_histogram_quantile_then_host_bin_scan_scalar",
                "materializes_host_frame": False,
                "bin_count": 4096,
                "histogram_download_bytes": 65536,
                "histogram_approximation": True,
                "median": 100.0,
                "mad": 2.0,
                "sigma": 2.9652,
                "low_threshold": 91.1044,
                "high_threshold": 105.9304,
            }

    threshold_info = inline_cosmetic_thresholds_from_resident_stack(
        FakeResidentStack(),
        frame_index=3,
        height=8,
        width=9,
        hot_sigma=2.0,
        cold_sigma=3.0,
    )

    assert threshold_info["supported"] is True
    assert threshold_info["threshold_source"] == "cuda_resident_histogram_median_mad_scalar"
    assert threshold_info["threshold_stats_native_method"] == (
        "ResidentCalibratedStack.frame_histogram_robust_stats"
    )
    assert threshold_info["threshold_stats_domain"] == "resident_calibrated_frame"
    assert threshold_info["threshold_stats_execution"] == "cuda_histogram_quantile_then_host_bin_scan_scalar"
    assert threshold_info["threshold_stats_materializes_host_frame"] is False
    assert threshold_info["threshold_stats_bin_count"] == 4096
    assert threshold_info["threshold_stats_histogram_download_bytes"] == 65536
    assert threshold_info["threshold_stats_histogram_approximation"] is True
    assert threshold_info["low_threshold"] == pytest.approx(91.1044)
    assert threshold_info["high_threshold"] == pytest.approx(105.9304)


def test_inline_cosmetic_thresholds_batch_from_resident_stack_records_batch_histogram_stats():
    class FakeResidentStack:
        def frames_histogram_robust_stats(
            self,
            indices: list[int],
            bin_count: int,
            hot_sigma: float,
            cold_sigma: float,
        ) -> dict[str, object]:
            assert indices == [3, 5]
            assert bin_count == 4096
            assert hot_sigma == pytest.approx(2.0)
            assert cold_sigma == pytest.approx(3.0)
            return {
                "native_method": "ResidentCalibratedStack.frames_histogram_robust_stats",
                "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                "stats_domain": "resident_calibrated_frame",
                "robust_stats_execution": "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar",
                "materializes_host_frame": False,
                "batch_reuses_device_work_buffers": True,
                "frame_count": 2,
                "bin_count": 4096,
                "histogram_download_bytes": 131072,
                "minmax_partial_download_bytes": 512,
                "device_alloc_s": 0.001,
                "total_s": 0.01,
                "frames": [
                    {
                        "native_method": "ResidentCalibratedStack.frames_histogram_robust_stats",
                        "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                        "stats_domain": "resident_calibrated_frame",
                        "robust_stats_execution": (
                            "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar"
                        ),
                        "materializes_host_frame": False,
                        "batch_reuses_device_work_buffers": True,
                        "frame_index": 3,
                        "bin_count": 4096,
                        "histogram_download_bytes": 65536,
                        "histogram_approximation": True,
                        "median": 100.0,
                        "mad": 2.0,
                        "sigma": 2.9652,
                        "low_threshold": 91.1044,
                        "high_threshold": 105.9304,
                    },
                    {
                        "native_method": "ResidentCalibratedStack.frames_histogram_robust_stats",
                        "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                        "stats_domain": "resident_calibrated_frame",
                        "robust_stats_execution": (
                            "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar"
                        ),
                        "materializes_host_frame": False,
                        "batch_reuses_device_work_buffers": True,
                        "frame_index": 5,
                        "bin_count": 4096,
                        "histogram_download_bytes": 65536,
                        "histogram_approximation": True,
                        "median": 120.0,
                        "mad": 3.0,
                        "sigma": 4.4478,
                        "low_threshold": 106.6566,
                        "high_threshold": 128.8956,
                    },
                ],
            }

    threshold_infos = inline_cosmetic_thresholds_batch_from_resident_stack(
        FakeResidentStack(),
        frame_indices=[3, 5],
        height=8,
        width=9,
        hot_sigma=2.0,
        cold_sigma=3.0,
    )

    assert sorted(threshold_infos) == [3, 5]
    first = threshold_infos[3]
    assert first["threshold_stats_native_method"] == (
        "ResidentCalibratedStack.frames_histogram_robust_stats"
    )
    assert first["threshold_stats_execution"] == (
        "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar"
    )
    assert first["threshold_stats_batch_native_method"] == (
        "ResidentCalibratedStack.frames_histogram_robust_stats"
    )
    assert first["threshold_stats_batch_frame_count"] == 2
    assert first["threshold_stats_batch_reuses_device_work_buffers"] is True
    assert first["threshold_stats_batch_histogram_download_bytes"] == 131072
    assert first["threshold_stats_batch_minmax_partial_download_bytes"] == 512
    assert first["threshold_stats_batch_device_alloc_s"] == pytest.approx(0.001)
    assert first["low_threshold"] == pytest.approx(91.1044)
    assert threshold_infos[5]["high_threshold"] == pytest.approx(128.8956)


def test_apply_resident_inline_cosmetic_thresholds_batch_records_batch_native_route():
    class FakeResidentStack:
        def apply_isolated_cosmetic_threshold_mask_frames(
            self,
            indices: list[int],
            low_thresholds: list[float],
            high_thresholds: list[float],
            medians: list[float],
            sigmas: list[float],
            structure_sigma: float,
            min_neighbor_support: int,
        ) -> dict[str, object]:
            assert indices == [3, 5]
            assert low_thresholds == [1.0, 2.0]
            assert high_thresholds == [10.0, 20.0]
            assert medians == [100.0, 120.0]
            assert sigmas == [1.5, 2.5]
            assert structure_sigma == pytest.approx(1.5)
            assert min_neighbor_support == 2
            return {
                "native_method": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
                "frame_count": 2,
                "total_s": 0.02,
                "frames": [
                    {
                        "native_method": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
                        "per_frame_native_method": (
                            "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                        ),
                        "frame_index": 3,
                        "hot_samples": 2,
                        "cold_samples": 1,
                        "nonfinite_samples": 0,
                        "candidate_hot_samples": 3,
                        "candidate_cold_samples": 1,
                        "protected_hot_samples": 1,
                        "protected_cold_samples": 0,
                        "cosmetic_corrected_samples": 3,
                        "invalid_samples": 3,
                        "applied": True,
                        "mask_upload_s": 0.0,
                        "batch_single_kernel_launch": True,
                        "batch_single_sync": True,
                        "detector_execution": "cuda_isolated_threshold_apply_batch",
                    },
                    {
                        "native_method": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
                        "per_frame_native_method": (
                            "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                        ),
                        "frame_index": 5,
                        "hot_samples": 0,
                        "cold_samples": 0,
                        "nonfinite_samples": 0,
                        "candidate_hot_samples": 0,
                        "candidate_cold_samples": 0,
                        "protected_hot_samples": 0,
                        "protected_cold_samples": 0,
                        "cosmetic_corrected_samples": 0,
                        "invalid_samples": 0,
                        "applied": False,
                        "mask_upload_s": 0.0,
                        "batch_single_kernel_launch": True,
                        "batch_single_sync": True,
                        "detector_execution": "cuda_isolated_threshold_apply_batch",
                    },
                ],
            }

    rows = apply_resident_inline_cosmetic_thresholds_batch(
        FakeResidentStack(),
        items=[
            {
                "frame_index": 3,
                "frame_id": "F3",
                "threshold_info": {
                    "supported": True,
                    "inline_source_dq": True,
                    "source_model": "inline_structure_cosmetic_cuda_thresholds",
                    "inline_source_dq_detector": (
                        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                    ),
                    "detector_execution": "cuda_isolated_threshold_apply",
                    "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                    "low_threshold": 1.0,
                    "high_threshold": 10.0,
                    "hot_sigma": 2.0,
                    "cold_sigma": 3.0,
                    "cosmetic_metrics": {"median": 100.0, "sigma": 1.5},
                    "structure_sigma": 1.5,
                    "min_neighbor_support": 2,
                },
            },
            {
                "frame_index": 5,
                "frame_id": "F5",
                "threshold_info": {
                    "supported": True,
                    "inline_source_dq": True,
                    "source_model": "inline_structure_cosmetic_cuda_thresholds",
                    "inline_source_dq_detector": (
                        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                    ),
                    "detector_execution": "cuda_isolated_threshold_apply",
                    "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                    "low_threshold": 2.0,
                    "high_threshold": 20.0,
                    "hot_sigma": 2.0,
                    "cold_sigma": 3.0,
                    "cosmetic_metrics": {"median": 120.0, "sigma": 2.5},
                    "structure_sigma": 1.5,
                    "min_neighbor_support": 2,
                },
            },
        ],
        source="resident_calibrated_batch_input_cosmetic_cuda",
    )

    assert [row["frame_id"] for row in rows] == ["F3", "F5"]
    assert rows[0]["status"] == "applied"
    assert rows[0]["native_method"] == "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames"
    assert rows[0]["detector_execution"] == "cuda_isolated_threshold_apply_batch"
    assert rows[0]["native"]["batch_single_kernel_launch"] is True
    assert rows[0]["flag_counts"] == {"hot_pixel": 2, "cold_pixel": 1, "cosmetic_corrected": 3}
    assert rows[0]["cosmetic_metrics"]["candidate_hot_pixels"] == 3
    assert rows[0]["cosmetic_metrics"]["protected_hot_pixels"] == 1
    assert rows[1]["status"] == "no_invalid_samples"
    assert rows[1]["native_method"] == "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames"
    assert rows[1]["native"]["batch_frame_count"] == 2


def test_apply_resident_inline_cosmetic_thresholds_batch_skips_high_invalid_fraction():
    class FakeResidentStack:
        def count_isolated_cosmetic_threshold_mask_frames(
            self,
            indices: list[int],
            low_thresholds: list[float],
            high_thresholds: list[float],
            medians: list[float],
            sigmas: list[float],
            structure_sigma: float,
            min_neighbor_support: int,
        ) -> dict[str, object]:
            assert indices == [3, 5]
            assert low_thresholds == [1.0, 2.0]
            assert high_thresholds == [10.0, 20.0]
            assert medians == [100.0, 120.0]
            assert sigmas == [1.5, 2.5]
            assert structure_sigma == pytest.approx(1.5)
            assert min_neighbor_support == 2
            return {
                "native_method": "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames",
                "frame_count": 2,
                "total_s": 0.01,
                "frames": [
                    {
                        "native_method": "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames",
                        "per_frame_native_method": (
                            "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame"
                        ),
                        "frame_index": 3,
                        "total_pixels": 1000,
                        "hot_samples": 50,
                        "cold_samples": 0,
                        "nonfinite_samples": 0,
                        "cosmetic_corrected_samples": 50,
                        "invalid_samples": 50,
                        "applied": False,
                        "detector_execution": "cuda_isolated_threshold_count_batch",
                    },
                    {
                        "native_method": "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames",
                        "per_frame_native_method": (
                            "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame"
                        ),
                        "frame_index": 5,
                        "total_pixels": 1000,
                        "hot_samples": 1,
                        "cold_samples": 0,
                        "nonfinite_samples": 0,
                        "cosmetic_corrected_samples": 1,
                        "invalid_samples": 1,
                        "applied": False,
                        "detector_execution": "cuda_isolated_threshold_count_batch",
                    },
                ],
            }

        def apply_isolated_cosmetic_threshold_mask_frames(
            self,
            indices: list[int],
            low_thresholds: list[float],
            high_thresholds: list[float],
            medians: list[float],
            sigmas: list[float],
            structure_sigma: float,
            min_neighbor_support: int,
        ) -> dict[str, object]:
            assert indices == [5]
            assert low_thresholds == [2.0]
            assert high_thresholds == [20.0]
            assert medians == [120.0]
            assert sigmas == [2.5]
            return {
                "native_method": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
                "frame_count": 1,
                "total_s": 0.02,
                "frames": [
                    {
                        "native_method": "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames",
                        "per_frame_native_method": (
                            "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                        ),
                        "frame_index": 5,
                        "hot_samples": 1,
                        "cold_samples": 0,
                        "nonfinite_samples": 0,
                        "cosmetic_corrected_samples": 1,
                        "invalid_samples": 1,
                        "applied": True,
                        "mask_upload_s": 0.0,
                        "detector_execution": "cuda_isolated_threshold_apply_batch",
                    }
                ],
            }

    items = [
        {
            "frame_index": 3,
            "frame_id": "F3",
                "threshold_info": {
                    "supported": True,
                    "inline_source_dq": True,
                    "source_model": "inline_structure_cosmetic_cuda_thresholds",
                    "inline_source_dq_detector": (
                        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                    ),
                    "detector_execution": "cuda_isolated_threshold_apply",
                    "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                    "low_threshold": 1.0,
                    "high_threshold": 10.0,
                    "hot_sigma": 2.0,
                    "cold_sigma": 3.0,
                    "cosmetic_metrics": {"median": 100.0, "sigma": 1.5},
                    "structure_sigma": 1.5,
                    "min_neighbor_support": 2,
                },
            },
            {
            "frame_index": 5,
            "frame_id": "F5",
                "threshold_info": {
                    "supported": True,
                    "inline_source_dq": True,
                    "source_model": "inline_structure_cosmetic_cuda_thresholds",
                    "inline_source_dq_detector": (
                        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
                    ),
                    "detector_execution": "cuda_isolated_threshold_apply",
                    "threshold_source": "cuda_resident_histogram_median_mad_scalar",
                    "low_threshold": 2.0,
                    "high_threshold": 20.0,
                    "hot_sigma": 2.0,
                    "cold_sigma": 3.0,
                    "cosmetic_metrics": {"median": 120.0, "sigma": 2.5},
                    "structure_sigma": 1.5,
                    "min_neighbor_support": 2,
                },
            },
    ]

    rows = apply_resident_inline_cosmetic_thresholds_batch(
        FakeResidentStack(),
        items=items,
        source="resident_calibrated_batch_input_cosmetic_cuda",
        max_invalid_fraction=0.002,
    )

    assert [row["frame_id"] for row in rows] == ["F3", "F5"]
    assert rows[0]["status"] == "skipped_high_invalid_fraction"
    assert rows[0]["applied"] is False
    assert rows[0]["invalid_samples"] == 0
    assert rows[0]["would_invalid_samples"] == 50
    assert rows[0]["would_invalid_fraction"] == pytest.approx(0.05)
    assert rows[0]["threshold_guard"]["max_invalid_fraction"] == pytest.approx(0.002)
    assert rows[0]["native_method"] == "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames"
    assert rows[1]["status"] == "applied"
    assert rows[1]["invalid_samples"] == 1
    assert rows[1]["threshold_guard"]["would_invalid_fraction"] == pytest.approx(0.001)


def test_source_invalid_mask_from_sidecar_path_reads_fits_dq_bits(tmp_path):
    dq = np.zeros((2, 3), dtype=np.float32)
    dq[0, 1] = float(int(DQFlag.HOT_PIXEL))
    dq[1, 0] = float(int(DQFlag.NO_DATA) | int(DQFlag.SATURATED))
    dq[1, 2] = np.nan
    sidecar = tmp_path / "source_dq.fits"
    write_fits_data(sidecar, dq)

    mask, info = source_invalid_mask_from_sidecar_path(sidecar, height=2, width=3)

    assert mask is not None
    assert mask.tolist() == [[0, 1, 0], [1, 0, 1]]
    assert info["source_model"] == "dq_sidecar_fits"
    assert info["sidecar_path"] == str(sidecar)
    assert info["invalid_samples"] == 3
    assert info["flagged_samples"] == 3
    assert info["nonfinite_samples"] == 0
    assert info["flag_counts"]["hot_pixel"] == 1
    assert info["flag_counts"]["saturated"] == 1
    assert info["flag_counts"]["no_data"] == 2


def test_combine_source_invalid_masks_uses_union_without_double_counting():
    data = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    dq = np.zeros((2, 2), dtype=np.uint32)
    dq[0, 1] = np.uint32(int(DQFlag.NO_DATA))
    dq[1, 0] = np.uint32(int(DQFlag.HOT_PIXEL))

    mask, info = combine_source_invalid_masks(
        [
            source_invalid_mask_from_array(data, height=2, width=2),
            source_invalid_mask_from_dq_mask(dq, height=2, width=2),
        ],
        height=2,
        width=2,
    )

    assert mask is not None
    assert mask.tolist() == [[0, 1], [1, 0]]
    assert info["invalid_samples"] == 2
    assert info["flagged_samples"] == 2
    assert info["nonfinite_samples"] == 1
    assert info["flag_counts"]["no_data"] == 1
    assert info["flag_counts"]["hot_pixel"] == 1


def test_resident_source_dq_summary_matches_stackengine_input_sample_closure():
    rows = [
        {
            "frame_id": "f0",
            "status": "no_invalid_samples",
            "source": "test",
            "application_order": "calibration_pre_registration",
            "registration_catalog_visible": True,
            "registration_catalog_visibility_required": True,
            "invalid_samples": 0,
            "flagged_samples": 0,
            "nonfinite_samples": 0,
            "flag_counts": {},
            "applied": False,
        },
        {
            "frame_id": "f1",
            "status": "applied",
            "source": "test",
            "application_order": "calibration_pre_registration",
            "registration_catalog_visible": True,
            "registration_catalog_visibility_required": True,
            "invalid_samples": 2,
            "flagged_samples": 2,
            "nonfinite_samples": 0,
            "flag_counts": {"hot_pixel": 1, "no_data": 1},
            "applied": True,
        },
    ]

    summary = build_resident_source_dq_summary(rows, frame_count=2, height=2, width=3)

    assert summary["input_samples"] == 12
    assert summary["input_valid_samples_before_rejection"] == 10
    assert summary["input_invalid_samples_before_rejection"] == 2
    assert summary["input_flagged_samples"] == 2
    assert summary["input_nonfinite_samples"] == 0
    assert summary["source_dq_flag_counts"] == {"hot_pixel": 1, "no_data": 1}
    assert summary["passed"] is True


def test_resident_source_dq_summary_records_no_source_dq_fast_skip():
    summary = build_resident_source_dq_summary(
        [],
        frame_count=3,
        height=4,
        width=5,
        fast_skip_frame_count=3,
        fast_skip_reason="native_u16_gpu_integer_payload_without_inline_or_sidecar_source_dq",
    )

    assert summary["passed"] is True
    assert summary["frame_count"] == 3
    assert summary["input_samples"] == 60
    assert summary["input_valid_samples_before_rejection"] == 60
    assert summary["input_invalid_samples_before_rejection"] == 0
    assert summary["fast_skip_frame_count"] == 3
    assert summary["fast_skip_reason"] == "native_u16_gpu_integer_payload_without_inline_or_sidecar_source_dq"
    assert summary["source_counts"] == {"no_source_dq_fast_skip": 3}
    assert summary["status_counts"] == {"no_source_dq_fast_skip": 3}
    assert summary["rows"] == []


def test_resident_source_dq_summary_uses_active_frame_ids_for_integration_samples():
    rows = [
        {
            "frame_id": "f0",
            "status": "applied",
            "source": "test",
            "application_order": "calibration_pre_registration",
            "registration_catalog_visible": True,
            "registration_catalog_visibility_required": True,
            "invalid_samples": 1,
            "flagged_samples": 1,
            "nonfinite_samples": 0,
            "flag_counts": {"hot_pixel": 1},
            "applied": True,
        },
        {
            "frame_id": "f1",
            "status": "applied",
            "source": "test",
            "application_order": "calibration_pre_registration",
            "registration_catalog_visible": True,
            "registration_catalog_visibility_required": True,
            "invalid_samples": 2,
            "flagged_samples": 2,
            "nonfinite_samples": 0,
            "flag_counts": {"hot_pixel": 2},
            "applied": True,
        },
    ]

    summary = build_resident_source_dq_summary(
        rows,
        frame_count=2,
        active_frame_count=1,
        active_frame_ids=["f0"],
        height=2,
        width=3,
    )
    group = build_resident_source_dq_execution_group(
        summary,
        filter_name="H",
        frame_count=2,
        height=2,
        width=3,
    )
    aggregate = summarize_resident_source_dq_execution_groups([group])

    assert summary["active_frame_count"] == 1
    assert summary["input_samples"] == 6
    assert summary["input_invalid_samples_before_rejection"] == 1
    assert summary["all_frame_input_invalid_samples_before_frame_mask"] == 3
    assert summary["inactive_frame_input_invalid_samples_before_frame_mask"] == 2
    assert summary["source_dq_flag_counts"] == {"hot_pixel": 1}
    assert summary["passed"] is True
    assert group["active_frame_count"] == 1
    assert group["input_samples"] == 6
    assert group["all_frame_input_invalid_samples_before_frame_mask"] == 3
    assert any(
        check["name"] == "all_frame_invalid_samples_applied" and check["passed"] is True
        for check in group["checks"]
    )
    assert aggregate["active_frame_count"] == 1
    assert aggregate["input_samples"] == 6
    assert aggregate["all_frame_input_invalid_samples_before_frame_mask"] == 3


def test_resident_source_dq_execution_group_proves_streaming_route_without_cache():
    summary = build_resident_source_dq_summary(
        [
            {
                "frame_id": "f0",
                "status": "no_invalid_samples",
                "source": "test",
                "application_order": "calibration_pre_registration",
                "registration_catalog_visible": True,
                "registration_catalog_visibility_required": True,
                "invalid_samples": 0,
                "flagged_samples": 0,
                "nonfinite_samples": 0,
                "flag_counts": {},
                "applied": False,
            },
            {
                "frame_id": "f1",
                "status": "applied",
                "source": "test",
                "application_order": "calibration_pre_registration",
                "registration_catalog_visible": True,
                "registration_catalog_visibility_required": True,
                "invalid_samples": 2,
                "flagged_samples": 2,
                "nonfinite_samples": 0,
                "flag_counts": {"hot_pixel": 2},
                "applied": True,
            },
        ],
        frame_count=2,
        height=4,
        width=5,
    )

    group = build_resident_source_dq_execution_group(
        summary,
        filter_name="H",
        frame_count=2,
        height=4,
        width=5,
        resident_calibration_batch_frames=3,
    )
    aggregate = summarize_resident_source_dq_execution_groups([group])

    assert group["passed"] is True
    assert group["execution_route"] == "resident_in_memory_mask_streaming"
    assert group["materializes_calibrated_dq_cache"] is False
    assert group["streaming_memory"]["estimated_per_frame_mask_bytes"] == 20
    assert group["streaming_memory"]["estimated_batch_mask_bytes"] == 60
    assert aggregate["passed"] is True
    assert aggregate["materializes_calibrated_dq_cache"] is False
    assert aggregate["estimated_peak_batch_mask_bytes"] == 60
