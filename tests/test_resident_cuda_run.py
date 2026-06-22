from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from glass.cli import _resident_source_dq_cache_preflight, main
from glass.cpu.integration import weighted_integrate_stack
from glass.engine.contracts import DQFlag
from glass.io.fits_io import read_fits_data, write_fits_data
from glass.io.json_io import read_json, write_json
from glass.engine.resident_cuda import (
    _apply_resident_registration_matrix_batch,
    build_resident_memory_admission,
    _load_frame_weight_proposal,
    _load_tile_local_policy_replay,
    _matches_any_token,
    _memory_estimate,
    _resident_dq_coverage_provenance,
    _resident_dq_map,
    _resident_catalog_signature,
    _resident_descriptor_signature,
    _resident_fit_signature,
    _resident_output_map_selection,
    _resident_source_dq_calibration_artifact_candidates,
    _resident_refine_catalog_centroids_from_stack,
    _resident_registration_motion_weighting,
    _resident_triangle_agreement_policy,
    _resident_triangle_agreement_quality,
    _resident_triangle_determinism_summary,
    _resident_triangle_translation_refine,
    _resident_similarity_frame_dispatch,
    _resident_winsorized_runtime_contract,
    _select_star_core_preselected_seed_indices,
    _select_star_guarded_seed,
    _tile_local_policy_application_arrays,
    _validate_resident_winsorized_runtime_contract,
)
from glass.cpu.registration import translation_matrix
from tests.conftest import cuda_module_or_skip


def test_resident_memory_estimate_includes_chunked_warp_workspace() -> None:
    frame_bytes = 72 * 80 * 4
    base_peak_bytes = (2 + 1 + 3 + 2) * frame_bytes + 2 * 4
    workspace_bytes = frame_bytes + (72 * 80) + 9 * 4 + 8

    memory = _memory_estimate(
        2,
        72,
        80,
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        chunked_warp_frame_count=1,
        observed_chunked_warp_chunk_frames=1,
        observed_chunked_warp_workspace_bytes=workspace_bytes,
        observed_chunked_warp_output_bytes=frame_bytes,
        observed_chunked_warp_coverage_bytes=72 * 80,
        observed_chunked_warp_inverse_bytes=9 * 4,
    )

    assert memory["estimated_peak_without_chunked_warp_bytes"] == base_peak_bytes
    assert memory["chunked_warp_planned_capacity_frames"] == 1
    assert memory["chunked_warp_planned_workspace_bytes"] == workspace_bytes
    assert memory["chunked_warp_observed_workspace_bytes"] == workspace_bytes
    assert memory["estimated_peak_includes_chunked_warp_workspace"] is True
    assert memory["estimated_peak_bytes"] == base_peak_bytes + workspace_bytes


def test_resident_memory_estimate_counts_full_chunk_metadata_workspace() -> None:
    frame_bytes = 10 * 12 * 4
    base_peak_bytes = (6 + 1 + 3 + 2) * frame_bytes + 6 * 4
    workspace_bytes = 2 * frame_bytes + 2 * (10 * 12) + 5 * 9 * 4 + 5 * 8

    memory = _memory_estimate(
        6,
        10,
        12,
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        chunked_warp_frame_count=5,
        chunked_warp_capacity_frames=2,
    )

    assert memory["estimated_peak_without_chunked_warp_bytes"] == base_peak_bytes
    assert memory["chunked_warp_planned_frame_count"] == 5
    assert memory["chunked_warp_planned_capacity_frames"] == 2
    assert memory["chunked_warp_planned_output_bytes"] == 2 * frame_bytes
    assert memory["chunked_warp_planned_coverage_bytes"] == 2 * (10 * 12)
    assert memory["chunked_warp_planned_inverse_bytes"] == 5 * 9 * 4
    assert memory["chunked_warp_planned_index_bytes"] == 5 * 8
    assert memory["chunked_warp_planned_workspace_bytes"] == workspace_bytes
    assert memory["estimated_peak_bytes"] == base_peak_bytes + workspace_bytes


def test_resident_memory_admission_recommends_reduced_chunk_capacity() -> None:
    frames = [
        {"id": f"L{index:03d}", "frame_type": "light", "filter": "H", "height": 72, "width": 80}
        for index in range(10)
    ]
    full = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        vram_budget_gb=1.0,
    )
    capacity4 = next(
        item
        for item in full["peak_group"]["capacity_options"]
        if item["chunked_warp_capacity_frames"] == 4
    )
    admission = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        vram_budget_gb=float(capacity4["estimated_peak_bytes"] + 1024) / (1024**3),
    )

    assert admission["passed"] is True
    assert admission["blocking"] is False
    assert admission["status"] == "passed_reduced_chunk"
    assert admission["recommended_action"] == "resident_reduced_chunk_capacity"
    assert admission["recommended_chunk_capacity_frames"] == 4
    assert admission["selected_chunk_capacity_frames"] == 4
    assert admission["selected_warp_batch_dispatch"] == "chunked"
    assert admission["selected_estimated_peak_bytes"] == capacity4["estimated_peak_bytes"]
    assert admission["selected_fits_budget"] is True
    assert admission["preferred_fits_budget"] is False
    assert admission["peak_group"]["preferred_chunk_capacity_frames"] == 8
    assert admission["peak_group"]["planned_warp_frame_count"] == 9
    assert any(
        "passed to native chunked matrix-warp dispatch" in limitation
        for limitation in admission["limitations"]
    )
    assert not any("allocator-driven" in limitation for limitation in admission["limitations"])


def test_resident_memory_admission_counts_stem_excludes() -> None:
    frames = [
        {
            "id": "F000160",
            "frame_type": "light",
            "filter": "H",
            "height": 72,
            "width": 80,
            "path": r"C:\data\LIGHT_H_0100.fits",
        },
        {
            "id": "F000161",
            "frame_type": "light",
            "filter": "H",
            "height": 72,
            "width": 80,
            "path": r"C:\data\LIGHT_H_0101.fits",
        },
        {
            "id": "F000162",
            "frame_type": "light",
            "filter": "H",
            "height": 72,
            "width": 80,
            "path": r"C:\data\LIGHT_H_0102.fits",
        },
    ]

    admission = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        exclude_frame_ids=["LIGHT_H_0100"],
        vram_budget_gb=1.0,
    )

    assert admission["peak_group"]["frame_count"] == 3
    assert admission["peak_group"]["planned_active_frame_count"] == 2
    assert admission["peak_group"]["planned_warp_frame_count"] == 1


def test_resident_memory_admission_auto_fused_skips_registered_stack_workspace() -> None:
    frames = [
        {"id": f"L{index:03d}", "frame_type": "light", "filter": "H", "height": 72, "width": 80}
        for index in range(10)
    ]
    stack = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        resident_integration_dispatch="stack",
        resident_warp_interpolation="bilinear",
        local_normalization="off",
        integration_rejection="none",
        vram_budget_gb=1.0,
    )
    fused = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        resident_integration_dispatch="auto",
        resident_warp_interpolation="bilinear",
        local_normalization="off",
        integration_rejection="none",
        vram_budget_gb=1.0,
    )

    assert fused["resident_integration_dispatch_requested"] == "auto"
    assert fused["resident_integration_dispatch_effective"] == "fused_matrix"
    assert fused["resident_integration_dispatch_reason"] == "auto_fused_bilinear_matrix_route"
    assert fused["fused_matrix_admission"] is True
    assert fused["peak_group"]["fused_matrix_admission"] is True
    assert fused["peak_group"]["planned_warp_frame_count"] == 0
    assert fused["peak_group"]["preferred_chunk_capacity_frames"] == 0
    assert fused["peak_group"]["chunked_warp_planned_workspace_bytes"] == 0
    assert fused["peak_group"]["estimated_peak_includes_chunked_warp_workspace"] is False
    assert fused["estimated_peak_bytes"] == fused["peak_group"]["estimated_peak_without_chunked_warp_bytes"]
    assert stack["peak_group"]["planned_warp_frame_count"] == 9
    assert stack["peak_group"]["chunked_warp_planned_workspace_bytes"] > 0
    assert fused["estimated_peak_bytes"] < stack["estimated_peak_bytes"]


def test_resident_memory_admission_auto_lanczos_keeps_stack_workspace() -> None:
    frames = [
        {"id": f"L{index:03d}", "frame_type": "light", "filter": "H", "height": 72, "width": 80}
        for index in range(10)
    ]

    admission = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        resident_integration_dispatch="auto",
        resident_warp_interpolation="lanczos3",
        local_normalization="off",
        integration_rejection="none",
        vram_budget_gb=1.0,
    )

    assert admission["resident_integration_dispatch_requested"] == "auto"
    assert admission["resident_integration_dispatch_effective"] == "stack"
    assert admission["resident_integration_dispatch_reason"] == "auto_stack_non_bilinear_matrix_route"
    assert admission["fused_matrix_admission"] is False
    assert admission["peak_group"]["planned_warp_frame_count"] == 9
    assert admission["peak_group"]["chunked_warp_planned_workspace_bytes"] > 0
    assert admission["peak_group"]["estimated_peak_includes_chunked_warp_workspace"] is True


def test_resident_memory_admission_blocks_explicit_budget() -> None:
    frames = [
        {"id": f"L{index:03d}", "frame_type": "light", "filter": "H", "height": 72, "width": 80}
        for index in range(2)
    ]

    admission = build_resident_memory_admission(
        {"frames": frames},
        resident_registration="similarity_cuda_triangle",
        resident_warp_batch_dispatch="chunked",
        vram_budget_gb=0.000001,
    )

    assert admission["passed"] is False
    assert admission["blocking"] is True
    assert admission["status"] == "failed"
    assert admission["reason"] == "estimated_peak_exceeds_explicit_vram_budget"
    assert admission["recommended_action"] in {
        "resident_reduced_chunk_capacity",
        "resident_loop_dispatch_or_tile_fallback",
        "tile_fallback",
    }


def _write_test_frame(path: Path, frame_type: str, data: np.ndarray, exposure: float = 60.0) -> None:
    header = fits.Header()
    header["IMAGETYP"] = frame_type
    header["FILTER"] = "H"
    header["EXPTIME"] = exposure
    header["GAIN"] = 100.0
    header["OFFSET"] = 20.0
    header["CCD-TEMP"] = -10.0
    header["XBINNING"] = 1
    header["YBINNING"] = 1
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.PrimaryHDU(np.asarray(data, dtype=np.float32), header=header).writeto(path)


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


def test_resident_registration_matrix_batch_keeps_translation_matrices_batched() -> None:
    class FakeStack:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def apply_matrix_lanczos3_frames(
            self,
            indices: list[int],
            matrices: np.ndarray,
            fill: float,
            clamping_threshold: float,
            dispatch: str = "loop",
            track_coverage: bool = True,
        ) -> dict[str, object]:
            self.calls.append(
                ("batch", (indices, matrices.copy(), fill, clamping_threshold, dispatch, track_coverage))
            )
            return {
                "frame_count": len(indices),
                "fallback_frame_count": 0,
                "timing_model": "fake_batch_one_sync",
                "inverse_upload_mode": "fake_device_batch",
                "track_coverage": track_coverage,
                "total_s": 0.01,
            }

        def apply_matrix_lanczos3_frame(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("translation-like matrices should not bypass native batch warp")

        def apply_translation_bilinear_frame(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("translation-like matrices should not use per-frame translation when batch is available")

    stack = FakeStack()
    models, timing = _apply_resident_registration_matrix_batch(
        stack,
        [
            (1, translation_matrix(2.5, -1.25)),
            (2, translation_matrix(-0.5, 3.0)),
        ],
        interpolation="lanczos3",
        clamping_threshold=0.3,
    )

    assert models == ["matrix_lanczos3_batch", "matrix_lanczos3_batch"]
    assert timing["batched"] is True
    assert timing["frame_count"] == 2
    assert timing["fallback_frame_count"] == 0
    assert len(stack.calls) == 1
    indices, matrices, fill, clamping_threshold, dispatch, track_coverage = stack.calls[0][1]
    assert indices == [1, 2]
    assert matrices.shape == (2, 3, 3)
    assert np.isnan(fill)
    assert clamping_threshold == pytest.approx(0.3)
    assert dispatch == "loop"
    assert track_coverage is True


def test_resident_registration_matrix_batch_honors_chunk_capacity() -> None:
    class FakeStack:
        def __init__(self) -> None:
            self.calls: list[list[int]] = []

        def apply_matrix_lanczos3_frames(
            self,
            indices: list[int],
            matrices: np.ndarray,
            fill: float,
            clamping_threshold: float,
            dispatch: str = "loop",
            max_chunk_capacity_frames: int | None = None,
            track_coverage: bool = True,
        ) -> dict[str, object]:
            self.calls.append(list(indices))
            assert dispatch == "chunked"
            assert max_chunk_capacity_frames == 2
            assert track_coverage is True
            assert matrices.shape[0] == len(indices)
            assert np.isnan(fill)
            assert clamping_threshold == pytest.approx(0.3)
            return {
                "batched": True,
                "frame_count": len(indices),
                "fallback_frame_count": 0,
                "timing_model": "fake_chunked_one_sync",
                "inverse_upload_mode": "chunked_device_batch",
                "inverse_prepare_s": 0.1,
                "inverse_batch_alloc_s": 0.2,
                "inverse_batch_bytes": len(indices) * 36,
                "index_upload_s": 0.3,
                "inverse_upload_s": 0.4,
                "kernel_enqueue_s": 0.5,
                "coverage_reduce_enqueue_s": 0.6,
                "scatter_enqueue_s": 0.7,
                "device_copy_enqueue_s": 0.8,
                "sync_s": 0.9,
                "total_s": 1.0,
                "batch_chunk_frames": 2,
                "batch_chunk_count": 3,
                "batch_max_chunk_capacity_frames": 2,
                "batch_capacity_source": "explicit_max_chunk_capacity",
                "batch_workspace_bytes": 200,
                "batch_output_bytes": 2000,
                "batch_coverage_bytes": 20,
                "warp_kernel_launches": 3,
                "coverage_reduce_kernel_launches": 3,
                "scatter_kernel_launches": 3,
                "track_coverage": track_coverage,
                "coverage_accumulator_updated": track_coverage,
            }

    stack = FakeStack()
    matrices = [
        (index, translation_matrix(float(index), -float(index)))
        for index in range(5)
    ]

    models, timing = _apply_resident_registration_matrix_batch(
        stack,
        matrices,
        interpolation="lanczos3",
        clamping_threshold=0.3,
        batch_dispatch="chunked",
        chunk_capacity_frames=2,
    )

    assert models == ["matrix_lanczos3_batch"] * 5
    assert stack.calls == [[0, 1, 2, 3, 4]]
    assert timing["batched"] is True
    assert timing["frame_count"] == 5
    assert timing["fallback_frame_count"] == 0
    assert timing["batch_max_chunk_capacity_frames"] == 2
    assert timing["batch_capacity_source"] == "explicit_max_chunk_capacity"
    assert timing["batch_chunk_frames"] == 2
    assert timing["batch_chunk_count"] == 3
    assert timing["batch_workspace_bytes"] == 200
    assert timing["batch_output_bytes"] == 2000
    assert timing["batch_coverage_bytes"] == 20
    assert timing["inverse_batch_bytes"] == 5 * 36
    assert timing["warp_kernel_launches"] == 3
    assert timing["coverage_reduce_kernel_launches"] == 3
    assert timing["scatter_kernel_launches"] == 3
    assert timing["total_s"] == pytest.approx(1.0)
    assert timing["timing_model"] == "fake_chunked_one_sync"


def test_resident_registration_matrix_batch_can_skip_warp_coverage_tracking() -> None:
    class FakeStack:
        def __init__(self) -> None:
            self.track_values: list[bool] = []

        def apply_matrix_bilinear_frames(
            self,
            indices: list[int],
            matrices: np.ndarray,
            fill: float,
            dispatch: str = "loop",
            max_chunk_capacity_frames: int | None = None,
            track_coverage: bool = True,
        ) -> dict[str, object]:
            self.track_values.append(track_coverage)
            assert dispatch == "chunked"
            assert max_chunk_capacity_frames == 4
            assert indices == [3, 4]
            assert matrices.shape == (2, 3, 3)
            assert np.isnan(fill)
            return {
                "batched": True,
                "frame_count": len(indices),
                "fallback_frame_count": 0,
                "timing_model": "fake_scatter_only",
                "inverse_upload_mode": "chunked_device_batch",
                "postprocess_mode": "scatter_only_no_coverage_accumulator",
                "track_coverage": track_coverage,
                "coverage_accumulator_updated": False,
                "warp_coverage_frame_count_delta": 0,
            }

    stack = FakeStack()
    models, timing = _apply_resident_registration_matrix_batch(
        stack,
        [
            (3, translation_matrix(1.0, 2.0)),
            (4, translation_matrix(-2.0, 0.5)),
        ],
        interpolation="bilinear",
        batch_dispatch="chunked",
        chunk_capacity_frames=4,
        track_coverage=False,
    )

    assert models == ["matrix_bilinear_batch", "matrix_bilinear_batch"]
    assert stack.track_values == [False]
    assert timing["track_coverage"] is False
    assert timing["coverage_accumulator_updated"] is False
    assert timing["warp_coverage_frame_count_delta"] == 0
    assert timing["postprocess_mode"] == "scatter_only_no_coverage_accumulator"


def _two_light_star_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "star_dataset"
    shape = (72, 80)
    yy, xx = np.indices(shape, dtype=np.float32)
    reference = np.full(shape, 10.0, dtype=np.float32) + 0.01 * xx + 0.02 * yy
    for x, y, flux in [
        (12, 16, 120.0),
        (27, 38, 220.0),
        (55, 18, 160.0),
        (66, 49, 190.0),
        (42, 61, 250.0),
        (18, 57, 140.0),
        (70, 28, 170.0),
        (35, 24, 150.0),
    ]:
        reference += flux * np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * 1.35**2)))
    moving = _shift_image(reference.astype(np.float32), 3, -2)

    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_001.fits", "light", reference, 60.0)
    _write_test_frame(root / "light" / "light_002.fits", "light", moving, 60.0)
    return root


def test_resident_dq_map_marks_no_data_and_rejections():
    master = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)
    weight = np.array([[2.0, 2.0], [0.0, 2.0]], dtype=np.float32)
    coverage = np.array([[2.0, 2.0], [2.0, 0.0]], dtype=np.float32)
    low = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.float32)
    high = np.array([[0.0, 0.0], [2.0, 0.0]], dtype=np.float32)

    dq, summary = _resident_dq_map(master, weight, coverage, low, high)

    assert dq[0, 0] == 0
    assert dq[0, 1] & int(DQFlag.NO_DATA)
    assert dq[0, 1] & int(DQFlag.LOW_REJECTED)
    assert dq[1, 0] & int(DQFlag.NO_DATA)
    assert dq[1, 0] & int(DQFlag.HIGH_REJECTED)
    assert dq[1, 1] & int(DQFlag.NO_DATA)
    assert dq[1, 1] & int(DQFlag.WARP_EDGE)
    assert summary["valid"] == 1
    assert summary["no_data"] == 3
    assert summary["warp_edge"] == 1
    assert summary["low_rejected"] == 1
    assert summary["high_rejected"] == 1


def test_resident_dq_coverage_provenance_separates_rejection_from_pre_rejection():
    coverage = np.array([[3.0, 0.0], [2.0, 1.0]], dtype=np.float32)
    low = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.float32)
    high = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    provenance = _resident_dq_coverage_provenance(coverage, low, high, active_frame_count=3)

    assert provenance["available"] is True
    assert provenance["active_frame_count"] == 3
    assert provenance["source_terms"] == [
        "post_rejection_coverage",
        "low_rejection",
        "high_rejection",
    ]
    assert provenance["post_rejection_zero_pixels"] == 1
    assert provenance["zero_pre_rejection_pixels"] == 1
    assert provenance["partial_pre_rejection_pixels"] == 1
    assert provenance["rejection_reduced_pixels"] == 2
    assert provenance["rejected_sample_count"] == 2.0
    assert provenance["rejected_sample_count_source"] == "low_high_rejection_maps"
    assert provenance["finite_pre_rejection_coverage"]["max"] == 3.0
    assert provenance["partial_edge_inference"] == "deferred"


def test_resident_dq_map_marks_geometric_warp_edges_without_no_data():
    master = np.ones((2, 2), dtype=np.float32)
    weight = np.full((2, 2), 2.0, dtype=np.float32)
    coverage = np.full((2, 2), 2.0, dtype=np.float32)
    geometric = np.array([[2.0, 1.0], [0.0, 2.0]], dtype=np.float32)

    dq, summary = _resident_dq_map(
        master,
        weight,
        coverage,
        None,
        None,
        geometric_warp_coverage_map=geometric,
        active_frame_count=2,
    )

    assert dq[0, 0] == 0
    assert dq[0, 1] & int(DQFlag.WARP_EDGE)
    assert not (dq[0, 1] & int(DQFlag.NO_DATA))
    assert dq[1, 0] & int(DQFlag.WARP_EDGE)
    assert dq[1, 0] & int(DQFlag.NO_DATA)
    assert summary["valid"] == 2
    assert summary["warp_edge"] == 2
    assert summary["no_data"] == 1


def test_resident_dq_coverage_provenance_includes_geometric_warp_coverage():
    coverage = np.full((2, 2), 2.0, dtype=np.float32)
    geometric = np.array([[2.0, 1.0], [0.0, 2.0]], dtype=np.float32)

    provenance = _resident_dq_coverage_provenance(
        coverage,
        None,
        None,
        active_frame_count=2,
        geometric_warp_coverage_map=geometric,
        geometric_warp_coverage_frame_count=2,
    )

    assert provenance["available"] is True
    assert provenance["source_terms"] == ["post_rejection_coverage", "geometric_warp_coverage"]
    assert provenance["geometric_warp_coverage_frame_count"] == 2
    assert provenance["geometric_frame_count_matches_active"] is True
    assert provenance["geometric_zero_pixels"] == 1
    assert provenance["geometric_partial_pixels"] == 1
    assert provenance["geometric_full_pixels"] == 2
    assert provenance["partial_edge_inference"] == "available_from_geometric_warp_coverage"


def test_resident_output_map_selection_modes():
    assert _resident_output_map_selection("audit") == {
        "master": True,
        "weight": True,
        "coverage": True,
        "low_rejection": True,
        "high_rejection": True,
        "dq": True,
    }
    assert _resident_output_map_selection("science") == {
        "master": True,
        "weight": True,
        "coverage": True,
        "low_rejection": False,
        "high_rejection": False,
        "dq": True,
    }
    assert _resident_output_map_selection("minimal") == {
        "master": True,
        "weight": False,
        "coverage": False,
        "low_rejection": False,
        "high_rejection": False,
        "dq": False,
    }


def test_resident_source_dq_calibration_artifact_candidates_keep_relative_run_path():
    candidates = _resident_source_dq_calibration_artifact_candidates(
        {},
        run=Path("runs/example"),
        plan_root=Path("runs/example_plan"),
    )

    assert candidates[0] == Path("runs/example") / "calibration_artifacts.json"
    assert candidates[1] == Path("runs/example_plan") / "calibration_artifacts.json"


def test_resident_hardened_winsorized_contract_rejects_over_limit():
    contract = _resident_winsorized_runtime_contract(
        rejection_mode="winsorized_sigma",
        resident_winsorized_mode="hardened_cpu_parity",
        frame_count=257,
        dispatch_mode="stack",
    )

    assert contract["hardened_requested"] is True
    assert contract["hardened_frame_limit"] == 256
    assert contract["frame_limit_ok"] is False
    with pytest.raises(ValueError, match="at most 256 resident frames"):
        _validate_resident_winsorized_runtime_contract(contract)


def test_resident_fast_winsorized_contract_does_not_apply_hardened_limit():
    contract = _resident_winsorized_runtime_contract(
        rejection_mode="winsorized_sigma",
        resident_winsorized_mode="fast_approx",
        frame_count=512,
        dispatch_mode="fused_matrix",
    )

    _validate_resident_winsorized_runtime_contract(contract)
    assert contract["hardened_requested"] is False
    assert contract["frame_limit_applies"] is False
    assert contract["frame_limit_ok"] is True


def test_resident_triangle_determinism_signatures_are_stable_and_sensitive():
    catalog = {
        "count": 3,
        "stored_count": 3,
        "grid_cols": 1,
        "grid_rows": 1,
        "candidates_per_cell": 3,
        "max_output_candidates": 3,
        "min_separation_px": 0.0,
        "catalog_sort_mode": "test_sort",
        "catalog_topk_mode": "test_topk",
        "x": np.array([1.0, 2.0, 3.0], dtype=np.float32),
        "y": np.array([4.0, 5.0, 6.0], dtype=np.float32),
        "flux": np.array([30.0, 20.0, 10.0], dtype=np.float32),
    }
    descriptor = {
        "count": 1,
        "raw_count": 1,
        "max_stars": 3,
        "neighbors": 3,
        "model": "test_descriptor",
        "descriptors": np.array([[0.1, 0.2]], dtype=np.float32),
        "indices": np.array([[0, 1, 2]], dtype=np.int32),
        "areas": np.array([4.0], dtype=np.float32),
    }
    fit = {
        "status": "ok",
        "model": "test_fit",
        "matrix": np.eye(3, dtype=np.float32),
        "inliers": 3,
        "rms_px": 0.25,
        "scale": 1.0,
        "rotation_rad": 0.0,
        "best_candidate_index": 7,
        "candidate_count": 11,
        "reference_descriptor_count": 1,
        "moving_descriptor_count": 1,
    }

    catalog_sig = _resident_catalog_signature(catalog)
    descriptor_sig = _resident_descriptor_signature(descriptor)
    fit_sig = _resident_fit_signature(fit)

    assert catalog_sig == _resident_catalog_signature(catalog)
    assert descriptor_sig == _resident_descriptor_signature(descriptor)
    assert fit_sig == _resident_fit_signature(fit)

    changed_catalog = dict(catalog)
    changed_catalog["flux"] = np.array([30.0, 19.0, 10.0], dtype=np.float32)
    assert catalog_sig["sha256"] != _resident_catalog_signature(changed_catalog)["sha256"]

    summary = _resident_triangle_determinism_summary(
        {
            "schema_version": 1,
            "signature_mode": "catalog_descriptor_fit_exact_float32_sha256",
            "thresholds": {
                "30.000000": {
                    "reference_catalog": catalog_sig,
                    "reference_descriptor": descriptor_sig,
                }
            },
            "moving": {
                "light_002": {
                    "moving_catalog": catalog_sig,
                    "selected_fit": fit_sig,
                    "trial_signature": {"sha256": "trial-a"},
                }
            },
        }
    )

    assert summary["signature_mode"] == "catalog_descriptor_fit_exact_float32_sha256"
    assert summary["moving_frame_count"] == 1
    assert summary["threshold_count"] == 1
    assert len(summary["moving_catalog_combined_sha256"]) == 64
    assert len(summary["selected_fit_combined_sha256"]) == 64


def test_resident_star_core_preselection_keeps_refit_seed_and_rejects_low_inlier_trap():
    seed_metrics = [
        {"seed_index": 0, "seed_inliers": 12, "seed_rms_px": 1.4, "star_core_metric": {"rms": 800.0}},
        {"seed_index": 1, "seed_inliers": 12, "seed_rms_px": 1.2, "star_core_metric": {"rms": 600.0}},
        {"seed_index": 2, "seed_inliers": 11, "seed_rms_px": 1.1, "star_core_metric": {"rms": 590.0}},
        {"seed_index": 3, "seed_inliers": 9, "seed_rms_px": 0.8, "star_core_metric": {"rms": 100.0}},
    ]

    selected, summary = _select_star_core_preselected_seed_indices(seed_metrics, max_count=3)

    assert selected == [0, 1, 2]
    assert summary["enabled"]
    assert summary["star_max_inliers"] == 12
    assert summary["star_min_inliers_for_core_metric"] == 10
    assert summary["selection_key"] == "pre_refine_star_core_rms_with_two_inlier_slack"


def test_resident_star_guarded_seed_prefers_star_core_metric_with_inlier_slack():
    seed_metrics = [
        {
            "seed_index": 0,
            "seed_rank": 0,
            "seed_inliers": 15,
            "seed_rms_px": 1.2,
            "metrics": {"rms": 82.0},
            "star_core_metric": {"rms": 640.0},
        },
        {
            "seed_index": 1,
            "seed_rank": 1,
            "seed_inliers": 13,
            "seed_rms_px": 1.3,
            "metrics": {"rms": 78.0},
            "star_core_metric": {"rms": 600.0},
        },
        {
            "seed_index": 2,
            "seed_rank": 2,
            "seed_inliers": 10,
            "seed_rms_px": 1.0,
            "metrics": {"rms": 76.0},
            "star_core_metric": {"rms": 590.0},
        },
    ]

    selected_index, guard = _select_star_guarded_seed(seed_metrics, pixel_selected_index=2)

    assert selected_index == 1
    assert guard["status"] == "replaced_pixel_metric_with_star_core_metric"
    assert guard["star_max_inliers"] == 15
    assert guard["star_min_inliers_for_core_metric"] == 13


def test_resident_similarity_auto_pierside_dispatches_prior_and_orientation():
    reference = {"path": "", "header_summary": {"PIERSIDE": "West"}}
    same_side = {"path": "", "header_summary": {"PIERSIDE": "W"}}
    flipped = {"path": "", "header_summary": {"PIERSIDE": "East"}}
    unknown = {"path": "", "header_summary": {}}

    same = _resident_similarity_frame_dispatch("auto_pierside", reference, same_side, {})
    flip = _resident_similarity_frame_dispatch("auto_pierside", reference, flipped, {})
    fallback = _resident_similarity_frame_dispatch("auto_pierside", reference, unknown, {})
    manual = _resident_similarity_frame_dispatch("ncc", reference, flipped, {})

    assert same["prior"] == "ncc"
    assert same["orientation_mode"] == "pierside_same"
    assert same["reference_pierside"] == "west"
    assert same["moving_pierside"] == "west"
    assert flip["prior"] == "none"
    assert flip["orientation_mode"] == "pierside_flipped"
    assert fallback["prior"] == "ncc"
    assert fallback["orientation_mode"] == "pierside_unknown"
    assert manual["prior"] == "ncc"
    assert manual["orientation_mode"] == "manual"


def test_resident_triangle_agreement_quality_scores_pixel_refinement():
    strong = _resident_triangle_agreement_quality(
        pixel_ncc=0.96,
        pixel_rms_adu=20.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=0.5,
    )
    weak = _resident_triangle_agreement_quality(
        pixel_ncc=0.96,
        pixel_rms_adu=400.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=0.5,
    )
    unavailable = _resident_triangle_agreement_quality(
        pixel_ncc=np.nan,
        pixel_rms_adu=20.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=None,
    )

    assert strong["status"] == "ok"
    assert strong["score"] > weak["score"]
    assert weak["status"] == "failed"
    assert weak["reason"] == "below_min_score"
    assert unavailable["status"] == "unavailable"
    assert unavailable["reason"] == "pixel_ncc_unavailable"


def test_resident_triangle_agreement_policy_can_downweight_without_hard_failure():
    weak = _resident_triangle_agreement_quality(
        pixel_ncc=0.96,
        pixel_rms_adu=400.0,
        fit_rms_px=0.3,
        rms_scale_adu=200.0,
        min_score=0.5,
    )

    hard_fail = _resident_triangle_agreement_policy(weak, "fail")
    downweight = _resident_triangle_agreement_policy(weak, "downweight")
    flagged = _resident_triangle_agreement_policy(weak, "flag")

    assert hard_fail["hard_failure"] is True
    assert hard_fail["weight_multiplier"] == 1.0
    assert downweight["hard_failure"] is False
    assert downweight["status"] == "downweighted"
    assert downweight["weight_multiplier"] == weak["score"] / weak["min_score"]
    assert flagged["hard_failure"] is False
    assert flagged["status"] == "flagged"
    assert flagged["weight_multiplier"] == 1.0


def test_resident_registration_motion_weighting_downweights_translation_outlier():
    matrices = [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 2.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 48.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    ]

    summary = _resident_registration_motion_weighting(
        ["F001", "F002", "F003", "F004"],
        matrices,
        [1.0, 1.0, 1.0, 1.0],
        mode="translation_mad",
        threshold_sigma=8.0,
        min_weight=0.05,
        power=2.0,
        scale_floor_px=1.0,
    )

    assert summary["enabled"] is True
    assert summary["eligible_frame_count"] == 4
    assert summary["downweighted_frame_count"] == 1
    assert summary["multipliers"][:3] == [1.0, 1.0, 1.0]
    assert 0.05 <= summary["multipliers"][3] < 1.0
    outlier = summary["frame_results"][3]
    assert outlier["threshold_exceeded"] is True
    assert outlier["weight_after_motion"] < outlier["weight_before_motion"]


def test_resident_registration_motion_weighting_off_preserves_weights():
    matrices = [
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        [[1.0, 0.0, 48.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    ]

    summary = _resident_registration_motion_weighting(
        ["F001", "F002"],
        matrices,
        [1.0, 1.0],
        mode="off",
    )

    assert summary["enabled"] is False
    assert summary["multipliers"] == [1.0, 1.0]
    assert summary["downweighted_frame_count"] == 0


def test_resident_triangle_translation_refine_uses_catalog_median_translation():
    reference = {
        "stored_count": 4,
        "x": np.asarray([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
        "y": np.asarray([11.0, 22.0, 33.0, 44.0], dtype=np.float32),
    }
    moving = {
        "stored_count": 4,
        "x": np.asarray([7.0001, 17.0002, 27.0003, 37.0004], dtype=np.float32),
        "y": np.asarray([11.008, 22.010, 33.012, 44.014], dtype=np.float32),
    }
    seed = [[1.0, 0.0, 3.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    result = _resident_triangle_translation_refine(
        reference,
        moving,
        seed,
        tolerance_px=0.1,
        min_inliers=3,
        max_correction_px=0.05,
    )

    assert result["applied"] is True
    assert result["status"] == "applied"
    assert result["inliers"] == 4
    assert abs(result["matrix"][0][2] - 2.99975) < 1e-4
    assert abs(result["matrix"][1][2] + 0.011) < 1e-4
    assert 0.010 < result["correction_px"] < 0.012
    assert result["rms_px"] < 0.003
    assert result["iterations"] >= 1
    assert result["initial_rms_px"] > result["rms_px"]


def test_resident_triangle_translation_refine_iterates_to_reduce_seed_rms():
    reference = {
        "stored_count": 4,
        "x": np.asarray([10.0, 20.0, 30.0, 40.0], dtype=np.float32),
        "y": np.asarray([12.0, 24.0, 36.0, 48.0], dtype=np.float32),
    }
    moving = {
        "stored_count": 4,
        "x": np.asarray([9.0, 19.0, 29.0, 39.0], dtype=np.float32),
        "y": np.asarray([12.0, 24.0, 36.0, 48.0], dtype=np.float32),
    }
    seed = [[1.0, 0.0, 0.72], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    result = _resident_triangle_translation_refine(
        reference,
        moving,
        seed,
        tolerance_px=0.31,
        min_inliers=4,
        max_correction_px=0.5,
        iterations=2,
    )

    assert result["applied"] is True
    assert result["inliers"] == 4
    assert result["iterations"] >= 1
    assert abs(result["matrix"][0][2] - 1.0) < 1e-6
    assert result["initial_rms_px"] > 0.25
    assert result["rms_px"] < 1e-6


def test_resident_triangle_translation_refine_rejects_large_correction():
    reference = {
        "stored_count": 3,
        "x": np.asarray([10.0, 20.0, 30.0], dtype=np.float32),
        "y": np.asarray([10.0, 20.0, 30.0], dtype=np.float32),
    }
    moving = {
        "stored_count": 3,
        "x": np.asarray([6.8, 16.8, 26.8], dtype=np.float32),
        "y": np.asarray([10.0, 20.0, 30.0], dtype=np.float32),
    }
    seed = [[1.0, 0.0, 3.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    result = _resident_triangle_translation_refine(
        reference,
        moving,
        seed,
        tolerance_px=0.5,
        min_inliers=3,
        max_correction_px=0.05,
    )

    assert result["applied"] is False
    assert result["status"] == "correction_exceeds_limit"
    assert result["matrix"] == seed
    assert abs(result["correction_px"] - 0.2) < 1e-5


def test_resident_refine_catalog_centroids_uses_resident_tiles():
    yy, xx = np.mgrid[0:21, 0:21]
    image = np.full((21, 21), 10.0, dtype=np.float32)
    image += 100.0 * np.exp(-(((xx - 9.35) ** 2 + (yy - 11.65) ** 2) / (2.0 * 1.2**2))).astype(np.float32)

    class FakeStack:
        width = image.shape[1]
        height = image.shape[0]

        def download_frame_tile(self, _index, x0, y0, x1, y1):
            return image[y0:y1, x0:x1]

    catalog = {
        "stored_count": 1,
        "x": np.asarray([9.0], dtype=np.float32),
        "y": np.asarray([12.0], dtype=np.float32),
        "flux": np.asarray([110.0], dtype=np.float32),
    }

    refined, summary = _resident_refine_catalog_centroids_from_stack(FakeStack(), 0, catalog, radius=4)

    assert summary["status"] == "ok"
    assert summary["refined_count"] == 1
    assert abs(float(refined["x"][0]) - 9.35) < 0.05
    assert abs(float(refined["y"][0]) - 11.65) < 0.05
    assert summary["max_shift_px"] > 0.4


def test_frame_weight_proposal_loader_accepts_list_and_object(tmp_path: Path):
    list_path = tmp_path / "proposal_list.json"
    write_json(
        list_path,
        {
            "artifact_type": "frame_weight_proposal",
            "method": "control_ratio",
            "source_integration_audit": "audit.json",
            "frame_multipliers": [
                {"frame_id": "F001", "multiplier": 0.25, "reason": "localized contribution"},
                {"frame_id": "F002", "multiplier": 1.0},
            ],
        },
    )
    proposal = _load_frame_weight_proposal(list_path)

    assert proposal["enabled"] is True
    assert proposal["path"] == str(list_path)
    assert proposal["frame_count"] == 2
    assert proposal["frame_multipliers"] == {"F001": 0.25, "F002": 1.0}
    assert proposal["rows"][0]["reason"] == "localized contribution"

    object_path = tmp_path / "proposal_object.json"
    write_json(object_path, {"frame_multipliers": {"F003": 0.5}})
    object_proposal = _load_frame_weight_proposal(object_path)

    assert object_proposal["frame_count"] == 1
    assert object_proposal["rows"][0]["frame_id"] == "F003"
    assert object_proposal["rows"][0]["multiplier"] == 0.5


def test_tile_local_policy_replay_loader_validates_contract(tmp_path: Path):
    replay_path = tmp_path / "tile_local_replay.json"
    write_json(
        replay_path,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": ["F001", "F002"],
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "boost_tiles": 1,
                "mean_abs_residual_before": 0.1,
                "mean_abs_residual_after": 0.02,
            },
            "tiles": [
                {
                    "tile_index": 3,
                    "extent": {"x0": 4, "y0": 5, "x1": 12, "y1": 16},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                    "clamped": True,
                    "selected_frame_row_count": 2,
                    "canonical_delta_contribution_adu": 5.0,
                    "signed_residual_reference_units_before": -0.1,
                    "signed_residual_reference_units_after": -0.02,
                    "moves_toward_reference": True,
                }
            ],
        },
    )

    contract = _load_tile_local_policy_replay(replay_path)

    assert contract["enabled"] is True
    assert contract["applied"] is False
    assert contract["application_status"] == "validated_not_applied"
    assert contract["target_group"] == "focus"
    assert contract["target_frame_count"] == 2
    assert contract["tile_count"] == 1
    assert contract["summary"]["recommendation"] == "tile_local_replay_promising"
    assert contract["tiles"][0]["extent"] == {"x0": 4, "y0": 5, "x1": 12, "y1": 16}
    assert contract["tiles"][0]["multiplier"] == 2.0


def test_tile_local_policy_application_arrays_build_apply_contract(tmp_path: Path):
    replay_path = tmp_path / "tile_local_replay.json"
    write_json(
        replay_path,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": ["F001", "F002"],
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 1, "y0": 2, "x1": 6, "y1": 7},
                    "multiplier": 1.75,
                }
            ],
        },
    )
    contract = _load_tile_local_policy_replay(replay_path)

    target_mask, tile_extents, tile_multipliers, summary = _tile_local_policy_application_arrays(
        contract,
        [{"id": "F001"}, {"id": "F003"}],
        width=8,
        height=8,
    )

    assert target_mask.tolist() == [1, 0]
    assert tile_extents.tolist() == [[1, 2, 6, 7]]
    assert tile_multipliers.tolist() == [1.75]
    assert summary["native_method"] == "ResidentCalibratedStack.integrate_tile_local_mean"
    assert summary["target_frame_count_applied"] == 1
    assert summary["target_frame_ids_missing"] == ["F002"]
    assert summary["tile_count_applied"] == 1


def _two_dark_group_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "two_dark_groups"
    shape = (24, 24)
    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_060.fits", "dark", np.full(shape, 10.0, dtype=np.float32), 60.0)
    _write_test_frame(root / "dark" / "dark_120.fits", "dark", np.full(shape, 20.0, dtype=np.float32), 120.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_060.fits", "light", np.full(shape, 100.0, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_120.fits", "light", np.full(shape, 200.0, dtype=np.float32), 120.0)
    return root


def _write_u16_bzero_test_frame(path: Path, frame_type: str, data: np.ndarray, exposure: float = 60.0) -> None:
    header = fits.Header()
    header["IMAGETYP"] = frame_type
    header["FILTER"] = "H"
    header["EXPTIME"] = exposure
    header["GAIN"] = 100.0
    header["OFFSET"] = 20.0
    header["CCD-TEMP"] = -10.0
    header["XBINNING"] = 1
    header["YBINNING"] = 1
    physical = np.asarray(data, dtype=np.uint16)
    stored = (physical.astype(np.int32) - 32768).astype(np.int16)
    hdu = fits.PrimaryHDU(stored, header=header)
    hdu.header["BSCALE"] = 1.0
    hdu.header["BZERO"] = 32768.0
    path.parent.mkdir(parents=True, exist_ok=True)
    hdu.writeto(path)


def _u16_gpu_decode_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "u16_gpu_decode"
    shape = (24, 24)
    yy, xx = np.indices(shape, dtype=np.uint16)
    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.full(shape, 10.0, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_u16_bzero_test_frame(root / "light" / "light_001.fits", "light", 1000 + xx + yy, 60.0)
    _write_u16_bzero_test_frame(root / "light" / "light_002.fits", "light", 1100 + xx + yy, 60.0)
    return root


def _two_light_weight_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "weight_dataset"
    shape = (16, 16)
    yy, xx = np.indices(shape, dtype=np.float32)
    low_noise = np.full(shape, 100.0, dtype=np.float32) + 0.05 * xx + 0.03 * yy
    high_noise = np.full(shape, 100.0, dtype=np.float32) + 3.0 * ((xx % 4) - 1.5) + 2.0 * ((yy % 4) - 1.5)
    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_low_noise.fits", "light", low_noise, 60.0)
    _write_test_frame(root / "light" / "light_high_noise.fits", "light", high_noise, 60.0)
    return root


def _two_light_cosmetic_cache_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "cosmetic_cache_dataset"
    shape = (16, 16)
    normal = np.full(shape, 100.0, dtype=np.float32)
    hot = normal.copy()
    hot[4, 5] = np.float32(10000.0)
    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "light" / "light_normal.fits", "light", normal, 60.0)
    _write_test_frame(root / "light" / "light_hot.fits", "light", hot, 60.0)
    return root


def _four_light_rejection_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "rejection_dataset"
    shape = (10, 12)
    yy, xx = np.indices(shape, dtype=np.float32)
    base = np.full(shape, 10.0, dtype=np.float32) + 0.05 * xx + 0.03 * yy
    frames = [
        base,
        base + np.float32(0.08),
        base - np.float32(0.06),
        base + np.float32(0.02),
    ]
    frames[3] = frames[3].copy()
    frames[3][2, 3] = 80.0
    frames[3][7, 8] = -120.0
    frames[2] = frames[2].copy()
    frames[2][1, 10] = 65.0

    _write_test_frame(root / "bias" / "bias_001.fits", "bias", np.zeros(shape, dtype=np.float32), 0.0)
    _write_test_frame(root / "dark" / "dark_001.fits", "dark", np.zeros(shape, dtype=np.float32), 60.0)
    _write_test_frame(root / "flat" / "flat_001.fits", "flat", np.ones(shape, dtype=np.float32), 60.0)
    for index, frame in enumerate(frames, start=1):
        _write_test_frame(root / "light" / f"light_{index:03d}.fits", "light", frame, 60.0)
    return root


def test_cli_resident_cuda_tile_local_policy_apply_mean_changes_target_tile(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    replay = tmp_path / "tile_local_replay.json"
    run = tmp_path / "resident_run_tile_local_apply"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    high_id = str(light_by_stem["light_high_noise"]["id"])
    write_json(
        replay,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": [high_id],
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "boost_tiles": 1,
            },
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 8, "y1": 8},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                    "selected_frame_row_count": 1,
                    "canonical_delta_contribution_adu": 1.0,
                    "signed_residual_reference_units_before": -0.2,
                    "signed_residual_reference_units_after": -0.1,
                    "moves_toward_reference": True,
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-tile-local-policy-replay",
            str(replay),
            "--resident-tile-local-policy-mode",
            "apply_mean",
        ]
    ) == 0

    low = read_fits_data(dataset / "light" / "light_low_noise.fits", dtype=np.float32)
    high = read_fits_data(dataset / "light" / "light_high_noise.fits", dtype=np.float32)
    expected = ((low + high) / 2.0).astype(np.float32)
    expected[:8, :8] = ((low[:8, :8] + 2.0 * high[:8, :8]) / 3.0).astype(np.float32)
    master = read_fits_data(run / "integration" / "resident_master_H.fits", dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    tile_local = resident["artifacts"][0]["resident_integration_weighting"]["tile_local_policy_replay"]

    assert tile_local["enabled"] is True
    assert tile_local["requested_mode"] == "apply_mean"
    assert tile_local["effective_mode"] == "apply_mean"
    assert tile_local["applied"] is True
    assert tile_local["application_status"] == "applied_mean_rejection_none"
    assert tile_local["target_frame_count_applied"] == 1
    assert tile_local["tile_count_applied"] == 1
    assert tile_local["native_timing_s"]["timing_model"] == "native_resident_tile_local_weighted_mean_one_sync"
    assert any("tile-local policy replay was applied" in warning for warning in integration["warnings"])
    assert np.allclose(master, expected, rtol=2e-5, atol=2e-5)


def test_cli_resident_cuda_tile_local_policy_apply_winsorized_sigma_records_rejection_maps(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    replay = tmp_path / "tile_local_replay.json"
    run = tmp_path / "resident_run_tile_local_apply_sigma"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    high_id = str(light_by_stem["light_high_noise"]["id"])
    write_json(
        replay,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": [high_id],
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 8, "y1": 8},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "winsorized_sigma",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-tile-local-policy-replay",
            str(replay),
            "--resident-tile-local-policy-mode",
            "apply",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    tile_local = resident["artifacts"][0]["resident_integration_weighting"]["tile_local_policy_replay"]

    assert tile_local["enabled"] is True
    assert tile_local["requested_mode"] == "apply"
    assert tile_local["effective_mode"] == "apply"
    assert tile_local["applied"] is True
    assert tile_local["application_status"] == "applied_winsorized_sigma"
    assert tile_local["native_method"] == "ResidentCalibratedStack.integrate_tile_local_sigma_clip"
    assert tile_local["native_timing_s"]["timing_model"] == "native_resident_tile_local_sigma_clip_one_sync"
    assert tile_local["native_timing_s"]["rejection"] == "winsorized_sigma"
    assert output["coverage_map_path"] is not None
    assert output["low_rejection_map_path"] is not None
    assert output["high_rejection_map_path"] is not None
    assert Path(output["coverage_map_path"]).exists()
    assert Path(output["low_rejection_map_path"]).exists()
    assert Path(output["high_rejection_map_path"]).exists()
    assert any("tile-local policy replay was applied to winsorized_sigma" in warning for warning in integration["warnings"])


def test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _four_light_rejection_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_hardened_winsorized"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "winsorized_sigma",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-integration-dispatch",
            "auto",
            "--resident-winsorized-mode",
            "hardened_cpu_parity",
        ]
    ) == 0

    light_frames = [
        read_fits_data(path, dtype=np.float32)
        for path in sorted((dataset / "light").glob("light_*.fits"))
    ]
    expected_master, expected_weight, expected_coverage, expected_low, expected_high = (
        weighted_integrate_stack(
            np.stack(light_frames, axis=0),
            rejection="winsorized_sigma",
            low_sigma=3.0,
            high_sigma=3.0,
        )
    )

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    contract = read_json(run / "resident_result_contract.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    descriptor = output["integration_rejection"]
    dispatch = artifact["resident_integration_dispatch"]
    winsorized_contract = output["resident_winsorized_contract"]
    hardened_timing = output["hardened_winsorized_timing_s"]

    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    coverage = read_fits_data(Path(output["coverage_map_path"]), dtype=np.float32)
    low_reject = read_fits_data(Path(output["low_rejection_map_path"]), dtype=np.float32)
    high_reject = read_fits_data(Path(output["high_rejection_map_path"]), dtype=np.float32)

    assert descriptor["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert descriptor["cpu_baseline_parity"] is True
    assert descriptor["approximation"] is False
    assert artifact["integration_rejection"] == descriptor
    assert integration["rejection_semantics"] == descriptor
    assert integration["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert dispatch["effective_mode"] == "stack"
    assert dispatch["selection_reason"] == "auto_stack_hardened_winsorized_requires_stack"
    assert dispatch["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert dispatch["resident_winsorized_contract"] == winsorized_contract
    assert winsorized_contract["hardened_requested"] is True
    assert winsorized_contract["frame_count"] == 4
    assert winsorized_contract["hardened_frame_limit"] == 256
    assert winsorized_contract["frame_limit_ok"] is True
    assert winsorized_contract["dispatch_ok"] is True
    assert winsorized_contract["requires_stack_dispatch"] is True
    assert dispatch["hardened_winsorized_timing_s"] == hardened_timing
    assert hardened_timing["native_method"] == "ResidentCalibratedStack.integrate_hardened_winsorized_sigma"
    assert hardened_timing["resident_winsorized_mode"] == "hardened_cpu_parity"
    assert hardened_timing["frame_count"] == 4
    assert hardened_timing["pixel_count"] == expected_master.size
    assert hardened_timing["total_s"] >= 0.0
    assert contract["passed"] is True
    assert any("hardened median/IQR" in warning for warning in integration["warnings"])
    assert np.allclose(master, expected_master, rtol=2e-5, atol=2e-5)
    assert np.allclose(weight, expected_weight, rtol=2e-5, atol=2e-5)
    assert np.allclose(coverage, expected_coverage, rtol=0.0, atol=0.0)
    assert np.allclose(low_reject, expected_low, rtol=0.0, atol=0.0)
    assert np.allclose(high_reject, expected_high, rtol=0.0, atol=0.0)
    assert float(np.max(high_reject)) > 0.0
    assert float(np.max(low_reject)) > 0.0


def test_cli_resident_cuda_run_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run"

    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--flat-floor",
            "0.05",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-registration",
            "translation_preview",
            "--reference-frame-id",
            "light_001",
            "--exclude-frame-id",
            "does_not_exist",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    state = read_json(run / "run_state.json")
    resident = read_json(run / "resident_artifacts.json")
    calibration = read_json(run / "calibration_artifacts.json")
    resident_result_contract = read_json(run / "resident_result_contract.json")
    assert integration["source_stage"] == "resident_calibrated_stack"
    assert integration["outputs"][0]["backend"] == "cuda_resident_stack"
    assert integration["outputs"][0]["resident_registration"] == "translation_preview"
    assert integration["excluded_frame_tokens"] == ["does_not_exist"]
    assert integration["outputs"][0]["output_diagnostics"]["normalization_probe"]["method"]
    assert Path(integration["outputs"][0]["dq_map_path"]).exists()
    assert integration["outputs"][0]["dq_map_path"] == resident["artifacts"][0]["dq_map_path"]
    assert integration["outputs"][0]["dq_summary"] == resident["artifacts"][0]["dq_summary"]
    assert integration["outputs"][0]["master_path"] == resident["artifacts"][0]["master_path"]
    assert integration["outputs"][0]["weight_map_path"] == resident["artifacts"][0]["weight_map_path"]
    assert integration["outputs"][0]["coverage_map_path"] == resident["artifacts"][0]["coverage_map_path"]
    assert integration["outputs"][0]["low_rejection_map_path"] == resident["artifacts"][0]["low_rejection_map_path"]
    assert integration["outputs"][0]["high_rejection_map_path"] == resident["artifacts"][0]["high_rejection_map_path"]
    assert integration["outputs"][0]["stack_engine_surface_contract"]["passed"] is True
    assert integration["outputs"][0]["stack_engine_surface_contract"] == resident["artifacts"][0][
        "stack_engine_surface_contract"
    ]
    assert integration["outputs"][0]["stack_engine_surface_contract"]["stack_request"]["frame_ids"] == resident[
        "artifacts"
    ][0]["frame_ids"]
    dq_data = read_fits_data(integration["outputs"][0]["dq_map_path"])
    shape = resident["artifacts"][0]["shape"]
    assert dq_data.shape == (shape["height"], shape["width"])
    assert np.all(np.isfinite(dq_data))
    assert np.nanmax(dq_data) <= int(
        DQFlag.NO_DATA | DQFlag.WARP_EDGE | DQFlag.LOW_REJECTED | DQFlag.HIGH_REJECTED
    )
    with fits.open(integration["outputs"][0]["dq_map_path"]) as hdul:
        assert "WARP_EDGE" in hdul[0].header["DQFLAGS"]
    assert resident["artifacts"][0]["dq_flag_bits"]["warp_edge"] == int(DQFlag.WARP_EDGE)
    assert "valid" in integration["outputs"][0]["dq_summary"]
    assert registration["source_stage"] == "resident_calibrated_stack"
    assert registration["results"][0]["status"] == "reference"
    assert state["current_stage"] == "integration"
    assert "resident_registration" in state["completed_stages"]
    assert "resident_integration" in state["completed_stages"]
    assert resident["backend"] == "cuda_resident_stack"
    assert resident["policy"]["flat_floor"] == 0.05
    assert calibration["artifact_type"] == "resident_cuda_calibration_artifacts"
    assert calibration["source_stage"] == "resident_calibrated_stack"
    assert calibration["backend"] == "cuda_resident_stack"
    assert len(calibration["masters"]) >= 3
    assert len(calibration["calibrated_lights"]) == len(resident["artifacts"][0]["frame_ids"])
    assert all(item["status"] == "resident_in_vram" for item in calibration["calibrated_lights"])
    assert all(item["resident_calibration_contract"]["passed"] for item in calibration["masters"].values())
    assert all(item["stack_engine_surface_contract"]["passed"] for item in calibration["masters"].values())
    assert all(item["stack_engine_surface_contract"]["stack_request"]["frame_ids"] for item in calibration["masters"].values())
    assert resident_result_contract["artifact_type"] == "resident_cuda_result_contract"
    assert resident_result_contract["passed"] is True
    assert resident_result_contract["outputs"][0]["filter"] == "H"
    assert resident_result_contract["outputs"][0]["backend"] == "cuda_resident_stack"
    assert resident["artifacts"][0]["resident_registration"]["mode"] == "translation_preview"
    assert resident["artifacts"][0]["output_diagnostics"]["clipping_probe"]["nonfinite_count"] == 0
    timing = resident["artifacts"][0]["timing_s"]
    fine_timing = resident["artifacts"][0]["fine_timing"]
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    io_overlap = resident["artifacts"][0]["resident_io_overlap"]
    assert fine_timing["schema_version"] == 1
    assert io_pipeline["prefetch_frames"] == 2
    assert io_pipeline["prefetch_workers"] == 2
    assert io_pipeline["h2d_mode"] == "pinned_ring"
    assert io_pipeline["calibration_event_mode"] == "reused_stack_events"
    assert io_pipeline["calibration_event_modes"] == ["reused_stack_events"]
    assert io_pipeline["calibration_event_reuse"] is True
    assert io_pipeline["host_pinned_bytes"] > 0
    assert io_pipeline["prefetch_host_pinned_bytes"] > 0
    assert io_pipeline["stack_host_pinned_bytes"] == 0
    assert resident["artifacts"][0]["resident_warp_scratch_bytes"] >= 0
    assert io_pipeline["warp_scratch_bytes"] == resident["artifacts"][0]["resident_warp_scratch_bytes"]
    assert resident["artifacts"][0]["resident_warp_copy_mode"] == "default_stream_async_device_to_device"
    assert io_pipeline["warp_copy_mode"] == "default_stream_async_device_to_device"
    assert timing["light_read_decode"] >= 0.0
    assert timing["light_read_wait_wall"] == timing["light_read_decode"]
    assert timing["light_read_decode_worker"] >= 0.0
    assert timing["light_read_worker_cumulative"] == timing["light_read_decode_worker"]
    assert timing["light_fits_open"] >= 0.0
    assert timing["light_fits_open_worker_cumulative"] == timing["light_fits_open"]
    assert timing["light_fits_materialize_decode"] >= 0.0
    assert (
        timing["light_fits_materialize_decode_worker_cumulative"]
        == timing["light_fits_materialize_decode"]
    )
    assert timing["light_read_overlap_saved"] >= 0.0
    assert timing["light_host_copy_to_pinned"] >= 0.0
    assert timing["light_host_copy_to_pinned"] == 0.0
    assert timing["light_h2d"] >= 0.0
    assert timing["light_calibrate_store"] >= 0.0
    assert timing["light_h2d_calibrate_store"] >= 0.0
    assert timing["light_master_build_or_load_in_loop"] == timing["master_build_or_load"]
    assert timing["resident_registration_warp"] >= 0.0
    assert timing["light_loop_unaccounted"] >= 0.0
    assert timing["light_loop_unaccounted_without_master"] >= timing["light_loop_unaccounted"]
    assert fine_timing["seconds"]["light_read_decode_total"] == timing["light_read_decode"]
    assert fine_timing["seconds"]["light_read_decode_worker_total"] == timing["light_read_decode_worker"]
    assert fine_timing["seconds"]["light_read_overlap_saved"] == timing["light_read_overlap_saved"]
    assert fine_timing["seconds"]["light_fits_open_total"] == timing["light_fits_open"]
    assert fine_timing["seconds"]["light_fits_materialize_decode_total"] == timing["light_fits_materialize_decode"]
    assert fine_timing["seconds"]["light_host_copy_to_pinned_total"] == timing["light_host_copy_to_pinned"]
    assert fine_timing["seconds"]["light_h2d_total"] == timing["light_h2d"]
    assert fine_timing["seconds"]["light_calibrate_store_total"] == timing["light_calibrate_store"]
    assert fine_timing["seconds"]["light_h2d_calibrate_store_total"] == timing["light_h2d_calibrate_store"]
    assert fine_timing["seconds"]["light_master_build_or_load_in_loop"] == timing[
        "light_master_build_or_load_in_loop"
    ]
    assert fine_timing["seconds"]["light_loop_accounted"] >= fine_timing["seconds"][
        "light_loop_accounted_without_master"
    ]
    assert fine_timing["seconds"]["light_loop_unaccounted_without_master"] >= fine_timing["seconds"][
        "light_loop_unaccounted"
    ]
    assert fine_timing["seconds"]["resident_registration_warp_total"] == timing["resident_registration_warp"]
    assert io_overlap["schema_version"] == 1
    assert io_overlap["prefetch_enabled"] is True
    assert io_overlap["wall_clock_stage_s"] == timing["light_read_upload_calibrate"]
    assert io_overlap["consumer_read_wait_wall_s"] == timing["light_read_wait_wall"]
    assert io_overlap["worker_read_cumulative_s"] == timing["light_read_worker_cumulative"]
    assert io_overlap["overlap_saved_s"] == timing["light_read_overlap_saved"]


def test_cli_resident_cuda_run_simple_snr_weighting(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_simple_snr"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "simple_snr",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    weights = integration["frame_weights"]
    assert integration["weighting"] == "simple_snr"
    assert integration["outputs"][0]["weighting"] == "simple_snr"
    assert not any("winsorized" in warning for warning in integration["warnings"])
    weighting = resident["artifacts"][0]["resident_integration_weighting"]
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_batch_enabled"] is True
    assert io_pipeline["calibration_batch_multistream_enabled"] is True
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_batch"
    assert io_pipeline["calibration_batch_requested_frames"] == 2
    assert io_pipeline["calibration_batch_requested_streams"] == 2
    assert io_pipeline["calibration_wave_requested_frames"] == 0
    assert io_pipeline["calibration_wave_effective_frames"] == 2
    assert io_pipeline["calibration_wave_enabled"] is False
    assert io_pipeline["calibration_wave_release_mode"] == "after_native_batch_sync"
    assert io_pipeline["calibration_batch_actual_stream_count"] == 2
    assert io_pipeline["calibration_batch_lane_buffer_bytes"] > 0
    assert io_pipeline["calibration_batch_frame_count"] == 2
    assert io_pipeline["calibration_batch_count"] == 1
    assert io_pipeline["calibration_batch_timing_model"] == "multi_stream_lanes_one_sync"
    assert io_pipeline["calibration_batch_native_total_s"] >= 0.0
    assert io_pipeline["calibration_batch_sync_s"] >= 0.0
    assert io_pipeline["calibration_event_mode"] == "reused_stack_lane_events"
    assert weighting["mode"] == "simple_snr"
    assert len(weighting["frame_results"]) == 2
    assert all(item["source_std"] is not None for item in weighting["frame_results"])
    by_std = sorted(weighting["frame_results"], key=lambda item: item["source_std"])
    assert by_std[0]["weight"] > by_std[-1]["weight"]
    assert max(weights.values()) > min(weights.values())


def test_cli_resident_cuda_run_applies_plan_source_dq_sidecar(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_source_dq_sidecar"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    sidecar = tmp_path / "source_dq" / "light_high_noise_dq.fits"
    dq = np.zeros((16, 16), dtype=np.float32)
    dq[4, 5] = float(int(DQFlag.HOT_PIXEL))
    write_fits_data(sidecar, dq)
    plan_payload = read_json(plan)
    for frame in plan_payload["frames"]:
        if frame.get("frame_type") == "light" and Path(str(frame["path"])).stem == "light_high_noise":
            frame["source_dq_mask_path"] = str(sidecar.relative_to(tmp_path))
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
        ]
    ) == 0

    low = read_fits_data(dataset / "light" / "light_low_noise.fits", dtype=np.float32)
    high = read_fits_data(dataset / "light" / "light_high_noise.fits", dtype=np.float32)
    expected = ((low + high) / 2.0).astype(np.float32)
    expected[4, 5] = low[4, 5]
    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    source_dq = resident["artifacts"][0]["source_dq_summary"]
    source_dq_execution = read_json(run / "resident_source_dq_execution.json")
    source_dq_execution_summary = source_dq_execution["summary"]

    assert np.allclose(master, expected, rtol=2e-5, atol=2e-5)
    assert weight[4, 5] == pytest.approx(1.0)
    assert weight[0, 0] == pytest.approx(2.0)
    assert output["dq_coverage_provenance"]["input_valid_samples_before_rejection"] == 511
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 1
    assert source_dq["input_flagged_samples"] == 1
    assert source_dq["source_dq_flag_counts"] == {"hot_pixel": 1}
    assert source_dq["status_counts"]["applied"] == 1
    assert source_dq["status_counts"]["no_invalid_samples"] == 1
    assert source_dq_execution_summary["passed"] is True
    assert source_dq_execution_summary["execution_routes"] == ["resident_in_memory_mask_streaming"]
    assert source_dq_execution_summary["materializes_calibrated_dq_cache"] is False
    assert source_dq_execution_summary["input_invalid_samples_before_rejection"] == 1
    assert source_dq_execution["groups"][0]["streaming_memory"]["estimated_batch_mask_bytes"] == 512
    assert integration["resident_source_dq_execution_summary"]["passed"] is True
    assert any(item["stage"] == "resident_source_dq_execution" for item in read_json(run / "run_state.json")["artifacts"])
    applied_rows = [row for row in source_dq["rows"] if row["status"] == "applied"]
    assert applied_rows[0]["sidecar_paths"] == [str(sidecar)]


def test_cli_resident_cuda_run_applies_calibration_artifact_dq_sidecar(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_art"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    high_frame_id = str(light_by_stem["light_high_noise"]["id"])
    sidecar_rel = Path("source_dq") / "light_high_noise_dq.fits"
    sidecar = run / sidecar_rel
    dq = np.zeros((16, 16), dtype=np.float32)
    dq[4, 5] = float(int(DQFlag.HOT_PIXEL))
    write_fits_data(sidecar, dq)
    run.mkdir(parents=True, exist_ok=True)
    write_json(
        run / "calibration_artifacts.json",
        {
            "artifact_type": "calibration_artifacts",
            "calibrated_lights": [
                {
                    "frame_id": high_frame_id,
                    "path": str(run / "calibrated" / f"calibrated_{high_frame_id}.fits"),
                    "dq_mask_path": str(sidecar_rel),
                    "dq_summary": {"hot_pixel": 1},
                    "cosmetic_correction": {"enabled": True, "hot_pixels": 1, "cold_pixels": 0},
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
        ]
    ) == 0

    low = read_fits_data(dataset / "light" / "light_low_noise.fits", dtype=np.float32)
    high = read_fits_data(dataset / "light" / "light_high_noise.fits", dtype=np.float32)
    expected = ((low + high) / 2.0).astype(np.float32)
    expected[4, 5] = low[4, 5]
    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]

    assert np.allclose(master, expected, rtol=2e-5, atol=2e-5)
    assert weight[4, 5] == pytest.approx(1.0)
    assert weight[0, 0] == pytest.approx(2.0)
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 1
    assert source_dq["input_flagged_samples"] == 1
    assert source_dq["source_dq_flag_counts"] == {"hot_pixel": 1}
    assert source_dq["sidecar_source_counts"] == {"calibration_artifacts": 1}
    assert source_dq["sidecar_artifact_paths"] == [str(run / "calibration_artifacts.json")]
    assert artifact["source_dq_calibration_artifact_index"]["available"] is True
    assert artifact["source_dq_calibration_artifact_index"]["sidecar_frame_count"] == 1
    applied_rows = [row for row in source_dq["rows"] if row["status"] == "applied"]
    assert applied_rows[0]["sidecar_paths"] == [str(sidecar)]
    assert applied_rows[0]["sidecar_sources"] == ["calibration_artifacts"]
    assert applied_rows[0]["sidecar_artifact_paths"] == [str(run / "calibration_artifacts.json")]


def test_cli_resident_cuda_run_applies_inline_cosmetic_source_dq_without_cache(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_inline_cosmetic"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-inline-source-dq",
            "cosmetic",
            "--resident-inline-source-dq-hot-sigma",
            "2.0",
            "--resident-inline-source-dq-cold-sigma",
            "8.0",
            "--resident-inline-source-dq-max-invalid-fraction",
            "0.01",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]
    strategy = read_json(run / "resident_source_dq_strategy.json")
    execution = read_json(run / "resident_source_dq_execution.json")
    timing = read_json(run / "run_timing.json")

    assert master[4, 5] == pytest.approx(100.0)
    assert weight[4, 5] == pytest.approx(1.0)
    assert weight[0, 0] == pytest.approx(2.0)
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 1
    assert source_dq["source_dq_flag_counts"] == {"cosmetic_corrected": 1, "hot_pixel": 1}
    assert source_dq["sidecar_source_counts"] == {}
    assert source_dq["status_counts"]["applied"] == 1
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq"] == "cosmetic"
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_materializes_cache"] is False
    assert strategy["inline_source_dq"]["enabled"] is True
    assert strategy["inline_source_dq"]["mode"] == "cosmetic"
    assert strategy["inline_source_dq"]["detector"] == "glass.cpu.cosmetic.detect_isolated_cosmetic_defects"
    assert execution["summary"]["passed"] is True
    assert execution["summary"]["materializes_calibrated_dq_cache"] is False
    assert timing["resident_inline_source_dq"] == "cosmetic"
    assert not (run / "resident_source_dq_cache_route.json").exists()
    applied_rows = [row for row in source_dq["rows"] if row["status"] == "applied"]
    assert applied_rows[0]["inline_source_dq"] is True
    assert any(
        item["source_model"] == "inline_structure_cosmetic_source_dq"
        for item in applied_rows[0]["component_summaries"]
    )
    assert applied_rows[0]["inline_source_dq_detector"] == (
        "glass.cpu.cosmetic.detect_isolated_cosmetic_defects"
    )


def test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_inline_cosmetic_cuda"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-inline-source-dq",
            "cosmetic_cuda",
            "--resident-inline-source-dq-hot-sigma",
            "2.0",
            "--resident-inline-source-dq-cold-sigma",
            "8.0",
            "--resident-inline-source-dq-max-invalid-fraction",
            "0.01",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]
    strategy = read_json(run / "resident_source_dq_strategy.json")
    timing = read_json(run / "run_timing.json")

    assert master[4, 5] == pytest.approx(100.0)
    assert weight[4, 5] == pytest.approx(1.0)
    assert weight[0, 0] == pytest.approx(2.0)
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 1
    assert source_dq["source_dq_flag_counts"] == {"cosmetic_corrected": 1, "hot_pixel": 1}
    assert source_dq["native_method"] == "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames"
    assert source_dq["native_methods"] == [
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames"
    ]
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq"] == "cosmetic_cuda"
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_detector"] == (
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
    )
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_threshold_source"] == (
        "cuda_resident_histogram_median_mad_scalar"
    )
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_threshold_stats_domain"] == (
        "resident_calibrated_frame"
    )
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_detector_execution"] == (
        "cuda_isolated_threshold_apply"
    )
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_max_invalid_fraction"] == pytest.approx(0.01)
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_high_fraction_guard_enabled"] is True
    assert strategy["inline_source_dq"]["mode"] == "cosmetic_cuda"
    assert strategy["inline_source_dq"]["detector"] == (
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
    )
    assert strategy["inline_source_dq"]["threshold_source"] == "cuda_resident_histogram_median_mad_scalar"
    assert strategy["inline_source_dq"]["max_invalid_fraction"] == pytest.approx(0.01)
    assert strategy["inline_source_dq"]["high_fraction_guard_enabled"] is True
    assert timing["resident_inline_source_dq"] == "cosmetic_cuda"
    assert timing["resident_inline_source_dq_max_invalid_fraction"] == pytest.approx(0.01)
    assert not (run / "resident_source_dq_cache_route.json").exists()
    applied_rows = [row for row in source_dq["rows"] if row["status"] == "applied"]
    assert len(applied_rows) == 1
    assert applied_rows[0]["native_method"] == (
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames"
    )
    assert applied_rows[0]["native"]["mask_upload_s"] == 0.0
    assert applied_rows[0]["native"]["batch_single_kernel_launch"] is True
    assert applied_rows[0]["native"]["batch_single_sync"] is True
    assert applied_rows[0]["detector_execution"] == "cuda_isolated_threshold_apply_batch"
    assert applied_rows[0]["threshold_source"] == "cuda_resident_histogram_median_mad_scalar"
    assert applied_rows[0]["threshold_stats_native_method"] == (
        "ResidentCalibratedStack.frames_histogram_robust_stats"
    )
    assert applied_rows[0]["threshold_stats_execution"] == (
        "cuda_histogram_quantile_batch_reused_buffers_then_host_bin_scan_scalar"
    )
    assert applied_rows[0]["threshold_stats_domain"] == "resident_calibrated_frame"
    assert applied_rows[0]["threshold_stats_materializes_host_frame"] is False
    assert applied_rows[0]["threshold_stats_bin_count"] == 4096
    assert applied_rows[0]["threshold_stats_histogram_download_bytes"] == 4096 * 8 * 2
    assert applied_rows[0]["threshold_stats_histogram_approximation"] is True
    assert applied_rows[0]["threshold_stats_batch_native_method"] == (
        "ResidentCalibratedStack.frames_histogram_robust_stats"
    )
    assert applied_rows[0]["threshold_stats_batch_frame_count"] == 2
    assert applied_rows[0]["threshold_stats_batch_reuses_device_work_buffers"] is True
    assert applied_rows[0]["threshold_stats_batch_histogram_download_bytes"] == 2 * 4096 * 8 * 2
    assert applied_rows[0]["component_summaries"][0]["source_model"] == (
        "inline_structure_cosmetic_cuda_thresholds"
    )
    assert applied_rows[0]["component_summaries"][0]["inline_source_dq_detector"] == (
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame"
    )
    assert applied_rows[0]["component_summaries"][0]["threshold_stats_batch_reuses_device_work_buffers"] is True
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_application_order"] == (
        "calibration_pre_registration"
    )
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_deferred_frame_count"] == 0
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_deferred_applied_frame_count"] == 0


def test_cli_resident_cuda_run_skips_inline_cosmetic_cuda_high_fraction_guard(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_inline_cosmetic_cuda_guard"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-inline-source-dq",
            "cosmetic_cuda",
            "--resident-inline-source-dq-hot-sigma",
            "2.0",
            "--resident-inline-source-dq-cold-sigma",
            "8.0",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]
    skipped_rows = [row for row in source_dq["rows"] if row["status"] == "skipped_high_invalid_fraction"]

    assert master[4, 5] == pytest.approx(5050.0)
    assert weight[4, 5] == pytest.approx(2.0)
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 0
    assert source_dq["input_would_invalid_samples_before_guard"] == 1
    assert source_dq["input_guarded_invalid_samples_skipped"] == 1
    assert source_dq["status_counts"]["skipped_high_invalid_fraction"] == 1
    assert len(skipped_rows) == 1
    assert skipped_rows[0]["would_invalid_samples"] == 1
    assert skipped_rows[0]["would_invalid_fraction"] == pytest.approx(1.0 / 256.0)
    assert skipped_rows[0]["threshold_guard"]["max_invalid_fraction"] == pytest.approx(0.0001)
    assert skipped_rows[0]["native_method"] == (
        "ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames"
    )
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_max_invalid_fraction"] == pytest.approx(0.0001)
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_high_fraction_guard_enabled"] is True
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_high_fraction_skipped_frame_count"] == 1
    assert artifact["resident_io_pipeline"]["resident_inline_source_dq_high_fraction_would_invalid_samples"] == 1


def test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration(
    tmp_path: Path,
):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_inline_cosmetic_cuda_deferred_registration"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-inline-source-dq",
            "cosmetic_cuda",
            "--resident-inline-source-dq-hot-sigma",
            "2.0",
            "--resident-inline-source-dq-cold-sigma",
            "8.0",
            "--resident-inline-source-dq-max-invalid-fraction",
            "0",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-grid-top-per-cell",
            "2",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-triangle-min-agreement-score",
            "0.01",
            "--resident-triangle-agreement-rms-scale",
            "200",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]
    pipeline = artifact["resident_io_pipeline"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]
    rows = [row for row in source_dq["rows"] if row.get("inline_source_dq")]

    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert source_dq["passed"] is True
    assert pipeline["resident_inline_source_dq_application_order"] == "post_registration_pre_warp"
    assert pipeline["resident_inline_source_dq_deferred_until_stage"] == "resident_registration_complete"
    assert pipeline["resident_inline_source_dq_deferred_frame_count"] == 2
    assert pipeline["resident_inline_source_dq_deferred_applied_frame_count"] == 0
    assert pipeline["resident_inline_source_dq_deferred_pending_frame_count"] == 0
    assert source_dq["input_invalid_samples_before_rejection"] == 0
    assert source_dq["status_counts"]["no_invalid_samples"] == 2
    assert rows
    assert {row["application_order"] for row in rows} == {"post_registration_pre_warp"}
    assert {row["deferred_until_stage"] for row in rows} == {"resident_registration_complete"}
    assert {row["status"] for row in rows} == {"no_invalid_samples"}
    assert {row["native_method"] for row in rows} == {
        "ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames"
    }
    assert {row["detector_execution"] for row in rows} == {"cuda_isolated_threshold_apply_batch"}
    assert all(str(row["source"]).startswith("resident_post_registration_pre_warp") for row in rows)


def test_cli_resident_cuda_run_consumes_two_phase_cosmetic_calibration_cache(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_two_phase"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    policy = plan_payload["calibration_plan"]["calibration_policy"]
    policy["cosmetic_correction_enabled"] = True
    policy["cosmetic_hot_sigma"] = 2.0
    policy["cosmetic_cold_sigma"] = 8.0
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cpu",
            "--memory-mode",
            "tile",
            "--until-stage",
            "calibration",
            "--tile-size",
            "16",
        ]
    ) == 0
    calibration = read_json(run / "calibration_artifacts.json")
    hot_rows = [
        item
        for item in calibration["calibrated_lights"]
        if int(item["dq_summary"].get("hot_pixel") or 0) > 0
    ]
    assert len(hot_rows) == 1
    assert hot_rows[0]["cosmetic_correction"]["enabled"] is True
    assert hot_rows[0]["cosmetic_correction"]["hot_pixels"] == 1
    assert Path(hot_rows[0]["dq_mask_path"]).exists()

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]

    assert master[4, 5] == pytest.approx(100.0)
    assert weight[4, 5] == pytest.approx(1.0)
    assert master[0, 0] == pytest.approx(100.0)
    assert weight[0, 0] == pytest.approx(2.0)
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 1
    assert source_dq["input_flagged_samples"] == 1
    assert source_dq["source_dq_flag_counts"] == {"cosmetic_corrected": 1, "hot_pixel": 1}
    assert source_dq["sidecar_source_counts"] == {"calibration_artifacts": 2}
    assert artifact["source_dq_calibration_artifact_index"]["available"] is True
    assert artifact["source_dq_calibration_artifact_index"]["sidecar_frame_count"] == 2
    applied_rows = [row for row in source_dq["rows"] if row["status"] == "applied"]
    assert len(applied_rows) == 1
    assert applied_rows[0]["sidecar_sources"] == ["calibration_artifacts"]
    assert applied_rows[0]["sidecar_artifact_paths"] == [str(run / "calibration_artifacts.json")]


def test_cli_resident_cuda_run_generates_source_dq_cache_route(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rdq_cache_route"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    policy = plan_payload["calibration_plan"]["calibration_policy"]
    policy["cosmetic_correction_enabled"] = True
    policy["cosmetic_hot_sigma"] = 2.0
    policy["cosmetic_cold_sigma"] = 8.0
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-source-dq-cache",
            "generate-calibration",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-output-maps",
            "audit",
            "--tile-size",
            "16",
        ]
    ) == 0

    route = read_json(run / "resident_source_dq_cache_route.json")
    strategy = read_json(run / "resident_source_dq_strategy.json")
    timing = read_json(run / "run_timing.json")
    state = read_json(run / "run_state.json")
    integration = read_json(run / "integration_results.json")
    output = integration["outputs"][0]
    master = read_fits_data(Path(output["master_path"]), dtype=np.float32)
    weight = read_fits_data(Path(output["weight_map_path"]), dtype=np.float32)
    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    source_dq = artifact["source_dq_summary"]

    assert route["mode"] == "generate-calibration"
    assert route["preflight"]["passed"] is True
    assert route["preflight"]["ready_light_frame_count"] == 2
    assert route["preflight"]["estimated_output_bytes"] > 0
    assert strategy["recommended_route"] == "generate_calibration_cache_allowed"
    assert strategy["resident_mask_streaming"]["strategy"] == "stream_invalid_mask_to_resident_stack"
    assert strategy["resident_mask_streaming"]["estimated_batch_bytes"] > 0
    assert route["status"] == "ready"
    assert route["calibrated_light_count"] == 2
    assert route["dq_sidecar_count"] == 2
    assert route["existing_dq_sidecar_count"] == 2
    assert route["missing_dq_sidecar_count"] == 0
    assert route["cosmetic_correction_enabled_frame_count"] == 2
    assert route["dq_summary_totals"]["hot_pixel"] == 1
    assert route["dq_summary_totals"]["cosmetic_corrected"] == 1
    assert all(row["exists"] for row in route["dq_sidecars"])
    assert timing["resident_source_dq_cache"] == "generate-calibration"
    assert [row["stage"] for row in timing["stages"]] == [
        "resident_memory_admission",
        "resident_source_dq_cache_calibration",
        "resident_calibration_integration",
    ]
    assert "resident_source_dq_cache_calibration" in state["completed_stages"]
    assert any(item["stage"] == "resident_source_dq_strategy" for item in state["artifacts"])
    assert any(item["stage"] == "resident_source_dq_cache" for item in state["artifacts"])
    assert master[4, 5] == pytest.approx(100.0)
    assert weight[4, 5] == pytest.approx(1.0)
    assert master[0, 0] == pytest.approx(100.0)
    assert weight[0, 0] == pytest.approx(2.0)
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 1
    assert source_dq["sidecar_source_counts"] == {"calibration_artifacts": 2}
    assert artifact["source_dq_calibration_artifact_index"]["available"] is True
    assert artifact["source_dq_calibration_artifact_index"]["sidecar_frame_count"] == 2


def test_resident_source_dq_cache_preflight_blocks_oversized_cache(tmp_path: Path):
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "preflight_run"
    run.mkdir()

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    preflight = _resident_source_dq_cache_preflight(
        plan,
        run,
        max_disk_fraction=0.5,
        free_bytes=128,
    )

    assert preflight["passed"] is False
    assert preflight["reason"] == "estimated_cache_exceeds_disk_budget"
    assert preflight["recommended_route"] == "resident_in_vram_mask_streaming"
    assert preflight["ready_light_frame_count"] == 2
    assert preflight["estimated_output_bytes"] > preflight["max_allowed_bytes"]
    assert preflight["calibrated_bytes_per_pixel"] == 4
    assert preflight["dq_bytes_per_pixel"] == 2
    assert preflight["resident_mask_streaming"]["estimated_batch_bytes"] > 0


def test_resident_source_dq_cache_preflight_uses_parent_for_missing_run_dir(tmp_path: Path):
    dataset = _two_light_cosmetic_cache_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    missing_run = tmp_path / "missing" / "preflight_run"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    preflight = _resident_source_dq_cache_preflight(plan, missing_run, max_disk_fraction=1.0)

    assert preflight["ready_light_frame_count"] == 2
    assert preflight["disk_usage_path"] == str(tmp_path)
    assert preflight["free_bytes"] > 0


def test_cli_resident_cuda_batch_wave_releases_prefetch_slots(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_batch_wave"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "h2d_event",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_batch_enabled"] is True
    assert io_pipeline["calibration_batch_multistream_enabled"] is True
    assert io_pipeline["calibration_wave_enabled"] is True
    assert io_pipeline["calibration_wave_requested_frames"] == 1
    assert io_pipeline["calibration_wave_effective_frames"] == 1
    assert io_pipeline["calibration_wave_release_mode"] == "after_wave_sync"
    assert io_pipeline["calibration_release_mode_requested"] == "h2d_event"
    assert io_pipeline["calibration_release_mode_effective"] == "h2d_event"
    assert io_pipeline["calibration_h2d_release_supported"] is True
    assert io_pipeline["calibration_h2d_release_capable"] is True
    assert io_pipeline["calibration_h2d_release_enabled"] is True
    assert io_pipeline["calibration_h2d_release_recommended"] is False
    assert io_pipeline["calibration_h2d_release_reason"] == "explicit_h2d_event_requested"
    assert io_pipeline["calibration_h2d_release_count"] == 2
    assert io_pipeline["calibration_h2d_release_s"] >= 0.0
    assert io_pipeline["calibration_h2d_event_sync_s"] >= 0.0
    assert io_pipeline["calibration_h2d_event_elapsed_s"] >= 0.0
    assert io_pipeline["calibration_pending_wait_sync_s"] >= 0.0
    assert io_pipeline["calibration_batch_requested_frames"] == 2
    assert io_pipeline["calibration_batch_count"] == 2
    assert io_pipeline["calibration_batch_frame_count"] == 2
    assert io_pipeline["calibration_batch_actual_stream_count"] == 1
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_h2d_release_batch"
    assert io_pipeline["calibration_batch_timing_model"] == (
        "multi_stream_one_frame_per_lane_h2d_release_then_wait"
    )
    assert io_pipeline["calibration_event_mode"] == "reused_stack_lane_h2d_events"
    assert io_pipeline["prefetch_release_count"] == 2
    assert io_pipeline["prefetch_release_batch_count"] == 2
    assert io_pipeline["prefetch_fill_call_count"] == 3
    assert io_pipeline["prefetch_fill_submit_count"] == 2
    assert io_pipeline["prefetch_release_fill_model"] == "batched_release_single_fill"
    assert io_pipeline["prefetch_max_inflight_slots"] == 2


def test_cli_resident_cuda_auto_release_policy_prefers_full_lanes(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    run_full = tmp_path / "resident_run_auto_full_lanes"
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run_full),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "2",
            "--resident-calibration-release-mode",
            "auto",
        ]
    ) == 0
    resident = read_json(run_full / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_requested"] == "auto"
    assert io_pipeline["calibration_release_mode_effective"] == "h2d_event"
    assert io_pipeline["calibration_h2d_release_capable"] is True
    assert io_pipeline["calibration_h2d_release_recommended"] is True
    assert io_pipeline["calibration_h2d_release_reason"] == "auto_h2d_event_wave_effective_matches_stream_count"
    assert io_pipeline["calibration_h2d_release_enabled"] is True
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_h2d_release_batch"
    assert io_pipeline["calibration_h2d_release_count"] == 2

    run_underfilled = tmp_path / "resident_run_auto_underfilled_lanes"
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run_underfilled),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "auto",
        ]
    ) == 0
    resident = read_json(run_underfilled / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_requested"] == "auto"
    assert io_pipeline["calibration_release_mode_effective"] == "sync"
    assert io_pipeline["calibration_h2d_release_capable"] is True
    assert io_pipeline["calibration_h2d_release_recommended"] is False
    assert io_pipeline["calibration_h2d_release_reason"] == "auto_sync:wave_effective_below_stream_count"
    assert io_pipeline["calibration_h2d_release_enabled"] is False
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_batch"
    assert io_pipeline["calibration_h2d_release_count"] == 0


def test_cli_resident_cuda_callback_queue_releases_inside_native_batch(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_callback_queue"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "manual",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "callback_queue",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_requested"] == "callback_queue"
    assert io_pipeline["calibration_release_mode_effective"] == "callback_queue"
    assert io_pipeline["calibration_callback_release_supported"] is True
    assert io_pipeline["calibration_callback_release_capable"] is True
    assert io_pipeline["calibration_callback_release_enabled"] is True
    assert io_pipeline["calibration_callback_release_recommended"] is False
    assert io_pipeline["calibration_h2d_release_reason"] == "explicit_callback_queue_requested"
    assert io_pipeline["calibration_fetch_batch_frames"] == 2
    assert io_pipeline["calibration_wave_effective_frames"] == 1
    assert io_pipeline["calibration_wave_release_mode"] == "callback_after_h2d_event"
    assert io_pipeline["calibration_batch_count"] == 1
    assert io_pipeline["calibration_callback_wave_count"] == 2
    assert io_pipeline["calibration_callback_release_count"] == 2
    assert io_pipeline["calibration_h2d_release_count"] == 2
    assert io_pipeline["calibration_callback_release_s"] >= 0.0
    assert io_pipeline["calibration_batch_mode"] == "host_async_multistream_callback_release_batch"
    assert io_pipeline["calibration_batch_timing_model"] == "multi_stream_callback_release_waves_one_final_sync"
    assert io_pipeline["calibration_event_mode"] == "reused_stack_lane_h2d_callback_events"
    assert io_pipeline["prefetch_release_count"] == 2
    assert io_pipeline["prefetch_release_batch_count"] == 2
    assert io_pipeline["prefetch_fill_call_count"] == 3
    assert io_pipeline["prefetch_fill_submit_count"] == 2
    assert io_pipeline["prefetch_release_fill_model"] == "batched_release_single_fill"


def test_cli_resident_cuda_callback_queue_queued_prefetch_refill(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_callback_queue_queued_refill"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-prefetch-frames",
            "2",
            "--resident-prefetch-workers",
            "2",
            "--resident-prefetch-refill-mode",
            "queued",
            "--resident-h2d-mode",
            "pinned_ring",
            "--resident-calibration-batch-frames",
            "2",
            "--resident-calibration-streams",
            "2",
            "--resident-calibration-wave-frames",
            "1",
            "--resident-calibration-release-mode",
            "callback_queue",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    io_pipeline = resident["artifacts"][0]["resident_io_pipeline"]
    assert io_pipeline["calibration_release_mode_effective"] == "callback_queue"
    assert io_pipeline["prefetch_refill_mode"] == "queued"
    assert io_pipeline["prefetch_release_fill_model"] == "queued_release_refill"
    assert io_pipeline["prefetch_release_count"] == 2
    assert io_pipeline["prefetch_release_batch_count"] == 2
    assert io_pipeline["prefetch_release_refill_request_count"] == 2
    assert io_pipeline["prefetch_release_refill_queued_submit_count"] >= 1
    assert io_pipeline["prefetch_release_refill_queued_execute_count"] == (
        io_pipeline["prefetch_release_refill_queued_submit_count"]
    )
    assert (
        io_pipeline["prefetch_release_refill_queued_submit_count"]
        + io_pipeline["prefetch_release_refill_queued_coalesced_count"]
        == io_pipeline["prefetch_release_refill_request_count"]
    )
    assert io_pipeline["prefetch_fill_call_count"] == (
        1 + io_pipeline["prefetch_release_refill_queued_execute_count"]
    )
    assert io_pipeline["prefetch_fill_submit_count"] == 2


def test_cli_resident_cuda_science_output_maps_skip_rejection_count_files(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_science_maps"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--until-stage",
                "integration",
                "--local-normalization",
                "off",
                "--integration-rejection",
                "sigma_clip",
                "--integration-weighting",
                "none",
                "--resident-registration",
                "off",
                "--resident-output-maps",
                "science",
            ]
        )
        == 0
    )

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    dq_closure = read_json(run / "resident_dq_pixel_closure.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    assert output["output_map_policy"]["mode"] == "science"
    assert artifact["output_map_policy"]["mode"] == "science"
    assert Path(output["master_path"]).exists()
    assert Path(output["weight_map_path"]).exists()
    assert Path(output["coverage_map_path"]).exists()
    assert Path(output["dq_map_path"]).exists()
    assert output["master_path"] == artifact["master_path"]
    assert output["weight_map_path"] == artifact["weight_map_path"]
    assert output["coverage_map_path"] == artifact["coverage_map_path"]
    assert output["dq_map_path"] == artifact["dq_map_path"]
    assert output["output_write_storage"] == artifact["output_write_storage"]
    assert output["low_rejection_map_path"] is None
    assert output["high_rejection_map_path"] is None
    assert artifact["low_rejection_map_path"] is None
    assert artifact["high_rejection_map_path"] is None
    assert not list((run / "integration").glob("resident_low_rejection_map_*.fits"))
    assert not list((run / "integration").glob("resident_high_rejection_map_*.fits"))
    assert "low_rejection" in output["output_map_policy"]["skipped"]
    assert "high_rejection" in output["output_map_policy"]["skipped"]
    assert "dq" in output["output_map_policy"]["written"]
    assert "valid" in output["dq_summary"]
    assert output["dq_coverage_provenance"] == artifact["dq_coverage_provenance"]
    assert output["dq_provenance_summary"] == artifact["dq_provenance_summary"]
    assert output["resident_dq_pixel_closure"]["path"] == str(run / "resident_dq_pixel_closure.json")
    assert artifact["resident_dq_pixel_closure"]["path"] == str(run / "resident_dq_pixel_closure.json")
    assert dq_closure["summary"]["passed"] is True
    assert dq_closure["summary"]["group_count"] == 1
    assert dq_closure["groups"][0]["frame_mask_active_frame_count"] == 2
    assert dq_closure["groups"][0]["geometric_warp_coverage_frame_count"] == 2
    assert output["resident_light_pipeline_profile"] == artifact["resident_light_pipeline_profile"]
    assert output["resident_light_pipeline_profile"]["stage"] == "resident_light_read_upload_calibrate"
    assert (
        output["resident_light_pipeline_profile"]["knobs"]["prefetch_frames"]
        == artifact["resident_io_pipeline"]["prefetch_frames"]
    )
    assert output["resident_light_pipeline_profile"]["dominant_component"] in {
        "master_build_or_load",
        "consumer_read_wait",
        "native_h2d_calibrate_store",
        "native_calibrate_store",
        "native_sync",
        "python_orchestration_unaccounted",
    }
    assert output["dq_provenance_summary"]["source_schema"] == "resident_dq_coverage_provenance"
    assert output["dq_provenance_summary"]["engine"] == "cuda_resident_stack"
    assert output["dq_provenance_summary"]["active_frame_count"] == 2
    provenance = output["dq_coverage_provenance"]
    assert provenance["available"] is True
    assert provenance["source_terms"][:3] == ["post_rejection_coverage", "low_rejection", "high_rejection"]
    assert "geometric_warp_coverage" in provenance["source_terms"]
    assert provenance["active_frame_count"] == 2
    assert provenance["geometric_warp_coverage_frame_count"] == 2
    assert provenance["geometric_frame_count_matches_active"] is True
    assert "finite_pre_rejection_coverage" in provenance
    assert output["geometric_warp_coverage"]["available"] is True
    assert artifact["resident_registration"]["warp_coverage"]["available"] is True


def test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    stack_run = tmp_path / "resident_run_minimal_stack"
    fused_run = tmp_path / "resident_run_minimal_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    common_args = [
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "winsorized_sigma",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "off",
        "--resident-output-maps",
        "minimal",
    ]

    assert main(["run", "--out", str(stack_run), *common_args]) == 0
    assert main(
        [
            "run",
            "--out",
            str(fused_run),
            *common_args,
            "--resident-integration-dispatch",
            "fused_matrix",
        ]
    ) == 0

    stack_master = read_fits_data(stack_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_master = read_fits_data(fused_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    stack_integration = read_json(stack_run / "integration_results.json")
    stack_resident = read_json(stack_run / "resident_artifacts.json")
    integration = read_json(fused_run / "integration_results.json")
    resident = read_json(fused_run / "resident_artifacts.json")
    stack_output = stack_integration["outputs"][0]
    stack_artifact = stack_resident["artifacts"][0]
    stack_dispatch = stack_artifact["resident_integration_dispatch"]
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    dispatch = artifact["resident_integration_dispatch"]
    timing = dispatch["native_timing_s"]

    assert np.allclose(stack_master, fused_master, rtol=2e-5, atol=2e-4, equal_nan=True)
    assert stack_output["output_map_policy"]["mode"] == "minimal"
    assert Path(stack_output["master_path"]).exists()
    assert stack_output["weight_map_path"] is None
    assert stack_output["coverage_map_path"] is None
    assert stack_output["low_rejection_map_path"] is None
    assert stack_output["high_rejection_map_path"] is None
    assert stack_output["dq_map_path"] is None
    assert stack_output["dq_summary"] is None
    assert stack_output["dq_coverage_provenance"]["available"] is False
    assert stack_output["geometric_warp_coverage"]["available"] is False
    assert stack_dispatch["mode"] == "stack"
    assert stack_dispatch["download_mode"] == "master_only"
    assert stack_dispatch["diagnostic_maps_downloaded"] is False
    assert stack_dispatch["weight_map_downloaded"] is False
    assert stack_output["output_map_policy"]["download_mode"] == "master_only"
    assert stack_output["output_map_policy"]["weight_map_downloaded"] is False
    assert stack_output["output_map_policy"]["available"] == ["master"]
    assert output["output_map_policy"]["mode"] == "minimal"
    assert Path(output["master_path"]).exists()
    assert output["weight_map_path"] is None
    assert output["coverage_map_path"] is None
    assert output["low_rejection_map_path"] is None
    assert output["high_rejection_map_path"] is None
    assert output["dq_map_path"] is None
    assert output["dq_summary"] is None
    assert output["dq_coverage_provenance"]["available"] is False
    assert output["geometric_warp_coverage"]["available"] is False
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["download_mode"] == "master_only"
    assert dispatch["diagnostic_maps_downloaded"] is False
    assert dispatch["weight_map_downloaded"] is False
    assert output["output_map_policy"]["download_mode"] == "master_only"
    assert output["output_map_policy"]["weight_map_downloaded"] is False
    assert output["output_map_policy"]["available"] == ["master"]
    assert timing["download_mode"] == "master_only"
    assert timing["diagnostic_maps_downloaded"] is False
    assert timing["weight_map_downloaded"] is False
    assert timing["output_bytes"] == 16 * 16 * 4


def test_cli_resident_cuda_audit_output_maps_mirror_paths(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_weight_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_audit_maps"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(plan),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--memory-mode",
                "resident",
                "--until-stage",
                "integration",
                "--local-normalization",
                "off",
                "--integration-rejection",
                "sigma_clip",
                "--integration-weighting",
                "none",
                "--resident-registration",
                "off",
                "--resident-output-maps",
                "audit",
            ]
        )
        == 0
    )

    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    output = integration["outputs"][0]
    artifact = resident["artifacts"][0]
    for key in [
        "master_path",
        "weight_map_path",
        "coverage_map_path",
        "low_rejection_map_path",
        "high_rejection_map_path",
        "dq_map_path",
    ]:
        assert output[key] == artifact[key]
        assert Path(artifact[key]).exists()
    assert output["output_write_storage"] == artifact["output_write_storage"]
    assert output["output_map_policy"]["written"] == artifact["output_map_policy"]["written"]
    assert "low_rejection" in artifact["output_map_policy"]["written"]
    assert "high_rejection" in artifact["output_map_policy"]["written"]


def test_cli_resident_cuda_run_ncc_subpixel_registration_smoke(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_ncc"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "on",
            "--resident-local-normalization-mode",
            "grid_mean_std",
            "--resident-local-normalization-tile-size",
            "8",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "translation_ncc_subpixel",
            "--resident-registration-max-shift",
            "4",
            "--resident-ncc-sample-stride",
            "2",
            "--resident-ncc-fallback-score-threshold",
            "1.0",
            "--resident-subpixel-radius-steps",
            "2",
            "--resident-subpixel-step",
            "0.5",
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    local_norm = read_json(run / "local_norm_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    assert integration["outputs"][0]["resident_registration"] == "translation_ncc_subpixel"
    assert integration["outputs"][0]["resident_local_normalization"] == "resident_grid_mean_std"
    assert registration["transform_model"] == "translation_ncc_subpixel"
    assert local_norm["source_stage"] == "resident_calibrated_stack"
    assert local_norm["enabled"] is True
    assert local_norm["mode"] == "resident_grid_mean_std"
    assert local_norm["groups"][0]["frame_results"][0]["status"] == "reference"
    assert local_norm["groups"][0]["frame_results"][1]["grid_coefficients"]["tile_size"] == 8
    assert local_norm["groups"][0]["frame_results"][1]["grid_coefficients"]["valid_pixel_total"] > 0
    assert registration["results"][0]["status"] == "reference"
    assert resident_registration["mode"] == "translation_ncc_subpixel"
    assert resident["artifacts"][0]["resident_local_normalization"]["enabled"] is True
    assert resident["artifacts"][0]["resident_local_normalization"]["mode"] == "resident_grid_mean_std"
    assert resident["artifacts"][0]["resident_local_normalization"]["tile_size"] == 8
    assert resident_registration["max_shift"] == 4
    assert resident_registration["ncc_sample_stride"] == 2
    assert resident_registration["ncc_fallback_score_threshold"] == 1.0
    assert resident_registration["subpixel_radius_steps"] == 2
    assert resident_registration["subpixel_step"] == 0.5
    assert any("ncc_fallback_stride=1" == item for item in registration["results"][1]["warnings"])


def test_cli_resident_cuda_run_star_catalog_registration_smoke(small_fits_dataset, tmp_path: Path):
    cuda_module_or_skip()
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_star_catalog"

    assert main(["scan", "--root", str(small_fits_dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "translation_star_catalog",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "0.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]

    assert registration["transform_model"] == "translation_star_catalog"
    assert registration["results"][0]["status"] == "reference"
    assert resident_registration["mode"] == "translation_star_catalog"
    assert resident_registration["star_threshold"] == 30.0
    assert resident_registration["star_max_candidates"] == 16
    assert resident_registration["star_tolerance_px"] == 0.5
    assert resident_registration["star_grid_cols"] == 4
    assert resident_registration["star_grid_rows"] == 4
    assert resident_registration["star_threshold_mode"] == "fixed"
    assert resident_registration["star_prior"] == "none"


def test_cli_resident_cuda_run_star_catalog_auto_threshold_aligns_shifted_pair(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_star_catalog_auto"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "translation_star_catalog",
            "--resident-star-threshold",
            "0",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "0.5",
            "--resident-registration-max-shift",
            "8",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-prior",
            "ncc",
            "--resident-star-prior-radius-px",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert resident_registration["star_threshold_mode"] == "auto_mean_std"
    assert resident_registration["star_threshold"] == 0.0
    assert resident_registration["star_prior"] == "ncc"
    assert resident_registration["star_prior_radius_px"] == 2.0
    assert moving["status"] == "ok"
    assert moving["matched_stars"] >= 6
    assert abs(moving["matrix"][0][2] + 3.0) < 1.0e-5
    assert abs(moving["matrix"][1][2] - 2.0) < 1.0e-5
    assert any("selected_star_threshold=" in warning for warning in moving["warnings"])
    assert any("star_prior_model=ncc" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_similarity_catalog"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    for frame in plan_payload["frames"]:
        if frame["frame_type"] == "light":
            frame.setdefault("header_summary", {})["PIERSIDE"] = "West"
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_catalog_tolerance_px": 1.5,
            "cuda_catalog_min_pair_distance": 8.0,
            "cuda_catalog_similarity_top_k": 3,
            "cuda_catalog_min_scale": 0.99,
            "cuda_catalog_max_scale": 1.01,
            "cuda_catalog_max_abs_rotation_rad": 0.02,
            "cuda_catalog_pixel_refine_coarse_stride": 1,
            "cuda_catalog_pixel_refine_final_stride": 1,
            "cuda_catalog_min_pixel_ncc": 0.1,
            "cuda_catalog_min_selected_seed_inliers": 3,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_catalog",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-registration-max-shift",
            "8",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-prior",
            "auto_pierside",
            "--resident-star-prior-radius-px",
            "2",
            "--resident-star-core-preselect-top-k",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]

    assert registration["transform_model"] == "similarity_cuda_catalog"
    assert integration["outputs"][0]["resident_registration"] == "similarity_cuda_catalog"
    assert resident_registration["mode"] == "similarity_cuda_catalog"
    assert resident_registration["star_core_preselect_top_k"] == 2
    assert resident_registration["star_core_guard"] is True
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_catalog"
    assert moving["matched_stars"] >= 3
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert any("similarity_top_k=3" in warning for warning in moving["warnings"])
    assert any("similarity_prior_requested=auto_pierside" in warning for warning in moving["warnings"])
    assert any("similarity_prior_effective=ncc" in warning for warning in moving["warnings"])
    assert any("similarity_orientation_mode=pierside_same" in warning for warning in moving["warnings"])
    assert any("similarity_seed_count=2" in warning for warning in moving["warnings"])
    assert any("similarity_refined_seed_count=2" in warning for warning in moving["warnings"])
    assert any("similarity_catalog_selector=resident_grid_top_nms" in warning for warning in moving["warnings"])
    assert any("similarity_star_core_preselect_enabled=True" in warning for warning in moving["warnings"])
    assert any("similarity_star_core_guard_status=" in warning for warning in moving["warnings"])
    assert any("similarity_quality_gate_status=ok" in warning for warning in moving["warnings"])
    assert any("resident CUDA catalog similarity" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_similarity_triangle"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-grid-top-per-cell",
            "2",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-triangle-min-agreement-score",
            "0.01",
            "--resident-triangle-agreement-rms-scale",
            "200",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    integration = read_json(run / "integration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    memory_estimate = resident["artifacts"][0]["memory_estimate"]
    frame_bytes = 72 * 80 * 4
    base_peak_bytes = (2 + 1 + 3 + 2) * frame_bytes + 2 * 4
    expected_chunked_workspace_bytes = frame_bytes + (72 * 80) + 9 * 4 + 8

    assert registration["transform_model"] == "similarity_cuda_triangle"
    assert integration["outputs"][0]["resident_registration"] == "similarity_cuda_triangle"
    assert resident_registration["mode"] == "similarity_cuda_triangle"
    assert memory_estimate["chunked_warp_enabled"] is True
    assert memory_estimate["chunked_warp_workspace_model"] == (
        "native_preferred_min_frame_count_8_with_halving_fallback"
    )
    assert memory_estimate["chunked_warp_planned_frame_count"] == 1
    assert memory_estimate["chunked_warp_planned_capacity_frames"] == 1
    assert memory_estimate["chunked_warp_planned_workspace_bytes"] == expected_chunked_workspace_bytes
    assert memory_estimate["chunked_warp_observed_workspace_bytes"] == expected_chunked_workspace_bytes
    assert memory_estimate["estimated_peak_without_chunked_warp_bytes"] == base_peak_bytes
    assert memory_estimate["estimated_peak_includes_chunked_warp_workspace"] is True
    assert memory_estimate["estimated_peak_bytes"] == (
        base_peak_bytes + expected_chunked_workspace_bytes
    )
    assert integration["outputs"][0]["estimated_peak_gib"] == memory_estimate["estimated_peak_gib"]
    assert resident_registration["triangle_descriptor_radius"] == 0.08
    assert resident_registration["triangle_neighbors"] == 5
    assert resident_registration["triangle_max_descriptors"] == 256
    assert resident_registration["triangle_grid_top_per_cell"] == 2
    assert resident_registration["triangle_nms_scan_candidates"] == 96
    assert resident_registration["triangle_nms_min_separation_px"] == 2.0
    assert resident_registration["triangle_catalog_batch"] is True
    assert resident_registration["triangle_catalog_batch_mode"] == "grid_top_nms_fixed_threshold"
    assert resident_registration["triangle_catalog_timing_model"] == (
        "batch_multistream_bulk_download_centroid_multistream"
    )
    assert resident_registration["triangle_catalog_batch_size"] == 1
    assert resident_registration["triangle_catalog_stream_count"] == 1
    assert resident_registration["triangle_catalog_batch_sync_count"] == 1
    assert resident_registration["triangle_catalog_sync_phase_count"] >= 2
    assert resident_registration["triangle_catalog_download_mode"] == "bulk_full_capacity"
    assert resident_registration["triangle_catalog_sort_mode"] == "shared_bitonic_power2"
    assert resident_registration["star_catalog_deterministic"] is True
    assert resident_registration["triangle_catalog_topk_mode"] == "deterministic_parallel_per_cell"
    assert resident_registration["triangle_catalog_native_total_s"] >= 0.0
    assert resident_registration["triangle_catalog_native_sync_s"] >= 0.0
    assert resident_registration["triangle_catalog_native_output_download_s"] >= 0.0
    assert resident_registration["triangle_catalog_native_centroid_refine_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_batch"] is True
    assert resident_registration["triangle_descriptor_fit_batch_mode"] == (
        "native_batch_shared_reference_device"
    )
    assert resident_registration["triangle_descriptor_fit_reference_device_reuse"] is True
    assert resident_registration["triangle_descriptor_fit_reference_device_bytes"] > 0
    assert resident_registration["triangle_descriptor_fit_moving_device_reuse"] is True
    assert resident_registration["triangle_descriptor_fit_moving_device_bytes"] > 0
    assert resident_registration["triangle_descriptor_fit_output_device_reuse"] is True
    assert resident_registration["triangle_descriptor_fit_output_device_bytes"] > 0
    assert resident_registration["triangle_descriptor_fit_best_reduction_mode"] == (
        "single_block_parallel_score_rms_index"
    )
    assert resident_registration["triangle_descriptor_fit_batch_timing_model"] == (
        "per_frame_reused_buffers_sync_timed"
    )
    assert resident_registration["triangle_descriptor_fit_native_host_prepare_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_reference_alloc_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_reference_upload_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_workspace_alloc_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_moving_upload_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_kernel_sync_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_output_download_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_frame_total_s"] >= 0.0
    assert resident_registration["triangle_descriptor_fit_native_total_s"] >= (
        resident_registration["triangle_descriptor_fit_native_host_prepare_s"]
        + resident_registration["triangle_descriptor_fit_native_reference_alloc_s"]
        + resident_registration["triangle_descriptor_fit_native_reference_upload_s"]
        + resident_registration["triangle_descriptor_fit_native_workspace_alloc_s"]
    )
    assert resident_registration["triangle_warp_batch"] is True
    assert resident_registration["triangle_warp_batch_mode"] == "native_matrix_bilinear_frames"
    assert resident_registration["triangle_warp_batch_dispatch"] == "chunked"
    assert resident_registration["triangle_warp_batch_requested_chunk_capacity_frames"] is None
    assert resident_registration["triangle_warp_batch_effective_chunk_capacity_frames"] is None
    assert resident_registration["triangle_warp_batch_capacity_source"] == "native_preferred"
    assert resident_registration["triangle_warp_batch_native_capacity_source"] == "native_preferred"
    assert resident_registration["triangle_warp_batch_native_max_chunk_capacity_frames"] == 0
    assert resident_registration["triangle_warp_batch_timing_model"] == (
        "native_chunked_batch_warp_scatter_one_sync"
    )
    assert resident_registration["triangle_warp_batch_native_inverse_upload_mode"] == "chunked_device_batch"
    assert resident_registration["triangle_warp_batch_native_chunk_metadata_upload_mode"] == (
        "single_device_batch_reused_by_chunks"
    )
    assert resident_registration["triangle_warp_batch_frame_count"] == 1
    assert resident_registration["triangle_warp_batch_fallback_frame_count"] == 0
    assert resident_registration["triangle_warp_batch_native_inverse_prepare_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_inverse_batch_alloc_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_inverse_batch_bytes"] > 0
    assert resident_registration["triangle_warp_batch_native_index_upload_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_index_upload_count"] == 1
    assert resident_registration["triangle_warp_batch_native_inverse_upload_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_inverse_upload_count"] == 1
    assert resident_registration["triangle_warp_batch_native_kernel_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_coverage_reduce_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_scatter_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_postprocess_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_postprocess_mode"] == "fused_scatter_reduce"
    assert resident_registration["triangle_warp_batch_native_device_copy_enqueue_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_sync_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_total_s"] >= 0.0
    assert resident_registration["triangle_warp_batch_native_chunk_frames"] >= 1
    assert resident_registration["triangle_warp_batch_native_chunk_count"] == 1
    assert resident_registration["triangle_warp_batch_native_workspace_bytes"] > 0
    assert resident_registration["triangle_warp_batch_native_warp_kernel_launches"] == 1
    assert resident_registration["triangle_warp_batch_native_coverage_reduce_kernel_launches"] == 0
    assert resident_registration["triangle_warp_batch_native_scatter_kernel_launches"] == 0
    assert resident_registration["triangle_warp_batch_native_postprocess_kernel_launches"] == 1
    assert resident_registration["triangle_pixel_refine_requested_coarse_stride"] == 1
    assert resident_registration["triangle_pixel_refine_requested_final_stride"] == 2
    assert resident_registration["triangle_pixel_refine_fast_coarse"] is True
    assert resident_registration["triangle_pixel_refine_fast_coarse_mode"] == "coarse_stride_floor_to_final"
    assert resident_registration["triangle_pixel_refine_coarse_stride_adjusted"] is True
    assert resident_registration["triangle_pixel_refine_coarse_stride"] == 2
    assert resident_registration["triangle_pixel_refine_final_stride"] == 2
    assert resident_registration["triangle_min_agreement_score"] == 0.01
    assert resident_registration["triangle_agreement_rms_scale"] == 200.0
    assert resident_registration["triangle_pixel_refine_batch"] is True
    assert resident_registration["triangle_pixel_refine_batch_mode"] == "native_batch_one_seed_per_frame"
    assert resident_registration["triangle_pixel_refine_batch_metric_mode"] == "flattened_frame_candidate_grid"
    assert resident_registration["triangle_pixel_refine_batch_metric_kernel_launches"] == 2
    assert resident_registration["triangle_pixel_refine_coarse_total_candidates"] > 0
    assert resident_registration["triangle_pixel_refine_fine_total_candidates"] > 0
    assert resident_registration["triangle_pixel_refine_metric_workload_model"] == (
        "candidate_count_x_sampled_pixels"
    )
    assert resident_registration["triangle_pixel_refine_coarse_sampled_pixels_per_candidate"] > 0
    assert resident_registration["triangle_pixel_refine_fine_sampled_pixels_per_candidate"] > 0
    assert resident_registration["triangle_pixel_refine_coarse_metric_sample_evaluations"] == (
        resident_registration["triangle_pixel_refine_coarse_total_candidates"]
        * resident_registration["triangle_pixel_refine_coarse_sampled_pixels_per_candidate"]
    )
    assert resident_registration["triangle_pixel_refine_fine_metric_sample_evaluations"] == (
        resident_registration["triangle_pixel_refine_fine_total_candidates"]
        * resident_registration["triangle_pixel_refine_fine_sampled_pixels_per_candidate"]
    )
    assert resident_registration["triangle_pixel_refine_coarse_metric_megasamples_per_s"] >= 0.0
    assert resident_registration["triangle_pixel_refine_fine_metric_megasamples_per_s"] >= 0.0
    assert resident_registration["triangle_pixel_refine_workspace_mode"] == "shared_flattened_candidate_metric_buffers"
    assert resident_registration["triangle_pixel_refine_workspace_bytes"] > 0
    assert resident_registration["triangle_pixel_refine_workspace_candidate_capacity"] > 0
    assert resident_registration["triangle_determinism_signature_mode"] == (
        "catalog_descriptor_fit_exact_float32_sha256"
    )
    assert resident_registration["triangle_determinism_moving_frame_count"] == 1
    assert resident_registration["triangle_determinism_threshold_count"] == 1
    assert len(resident_registration["triangle_determinism_reference_combined_sha256"]) == 64
    assert len(resident_registration["triangle_determinism_moving_catalog_combined_sha256"]) == 64
    assert len(resident_registration["triangle_determinism_selected_fit_combined_sha256"]) == 64
    determinism = resident_registration["triangle_determinism"]
    assert determinism["signature_mode"] == "catalog_descriptor_fit_exact_float32_sha256"
    assert set(determinism["moving"]) == {moving["frame_id"]}
    moving_signature = determinism["moving"][moving["frame_id"]]
    assert moving_signature["moving_catalog"]["stored_count"] >= 3
    assert moving_signature["moving_descriptor"]["count"] > 0
    assert moving_signature["selected_fit"]["status"] == "ok"
    timing = resident["artifacts"][0]["timing_s"]
    registration_components = resident["artifacts"][0]["fine_timing"]["registration_component_seconds"]
    assert timing["resident_registration_component_accounted"] >= 0.0
    assert timing["resident_registration_orchestration"] >= 0.0
    assert registration_components["triangle_moving_catalog_batch"] >= 0.0
    assert registration_components["triangle_moving_catalog"] >= 0.0
    assert registration_components["triangle_moving_descriptors"] >= 0.0
    assert registration_components["triangle_descriptor_fit"] >= 0.0
    assert registration_components["triangle_descriptor_fit_batch"] >= 0.0
    assert registration_components["triangle_descriptor_fit_native_moving_upload"] >= 0.0
    assert registration_components["triangle_descriptor_fit_native_kernel_sync"] >= 0.0
    assert registration_components["triangle_descriptor_fit_native_output_download"] >= 0.0
    assert registration_components["triangle_moving_catalog_native_centroid_refine"] >= 0.0
    assert registration_components["triangle_warp"] >= 0.0
    assert registration_components["triangle_warp_native_batch"] >= 0.0
    assert registration_components["triangle_warp_native_sync"] >= 0.0
    assert registration_components["triangle_pixel_refine_batch"] >= 0.0
    assert registration_components["triangle_pixel_refine_native_coarse"] >= 0.0
    assert registration_components["triangle_pixel_refine_native_fine"] >= 0.0
    assert resident["artifacts"][0]["resident_warp_scratch_bytes"] == 0
    assert resident_registration["triangle_warp_batch_native_workspace_bytes"] > 0
    assert resident_registration["triangle_warp_batch_native_output_bytes"] > 0
    assert resident_registration["triangle_warp_batch_native_coverage_bytes"] > 0
    assert resident["artifacts"][0]["resident_io_pipeline"]["warp_scratch_bytes"] == 0
    assert resident["artifacts"][0]["resident_warp_copy_mode"] == "default_stream_async_device_to_device"
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert moving["matched_stars"] >= 3
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert any("reference_descriptors=" in warning for warning in moving["warnings"])
    assert any("moving_descriptors=" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_selector=resident_grid_top_nms" in warning for warning in moving["warnings"])
    assert any(
        "triangle_catalog_timing_model=batch_multistream_bulk_download_centroid_multistream"
        in warning
        for warning in moving["warnings"]
    )
    assert any("triangle_catalog_batch_size=1" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_stream_count=1" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_batch_sync_count=1" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_sync_phase_count=" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_download_mode=bulk_full_capacity" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_sort_mode=shared_bitonic_power2" in warning for warning in moving["warnings"])
    assert any("triangle_catalog_topk_mode=deterministic_parallel_per_cell" in warning for warning in moving["warnings"])
    assert any("triangle_grid_top_per_cell=2" in warning for warning in moving["warnings"])
    assert any("triangle_nms_scan_candidates=96" in warning for warning in moving["warnings"])
    assert any("triangle_nms_min_separation_px=2" in warning for warning in moving["warnings"])
    assert any("triangle_quality_gate_status=ok" in warning for warning in moving["warnings"])
    assert any("triangle_agreement_score=" in warning for warning in moving["warnings"])
    assert any("triangle_agreement_status=ok" in warning for warning in moving["warnings"])
    assert any("triangle_min_agreement_score=0.01" in warning for warning in moving["warnings"])
    assert any("triangle_descriptor_fit_batch=true" in warning for warning in moving["warnings"])
    assert any(
        "triangle_descriptor_fit_best_reduction_mode=single_block_parallel_score_rms_index" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_descriptor_fit_batch_timing_model=per_frame_reused_buffers_sync_timed" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_descriptor_fit_reference_device_reuse=true" in warning
        for warning in moving["warnings"]
    )
    assert any("triangle_descriptor_fit_frame_kernel_sync_s=" in warning for warning in moving["warnings"])
    assert any("triangle_determinism_moving_catalog_signature=" in warning for warning in moving["warnings"])
    assert any("triangle_determinism_selected_fit_signature=" in warning for warning in moving["warnings"])
    assert any("triangle_pixel_refine_mode=native_batch" in warning for warning in moving["warnings"])
    assert any("triangle_pixel_refine_fast_coarse=true" in warning for warning in moving["warnings"])
    assert any(
        "triangle_pixel_refine_fast_coarse_mode=coarse_stride_floor_to_final" in warning
        for warning in moving["warnings"]
    )
    assert any("triangle_pixel_refine_coarse_stride_adjusted=true" in warning for warning in moving["warnings"])
    assert any("triangle_pixel_refine_effective_coarse_stride=2" in warning for warning in moving["warnings"])
    assert any(
        "triangle_pixel_refine_batch_metric_mode=flattened_frame_candidate_grid" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_pixel_refine_metric_workload_model=candidate_count_x_sampled_pixels" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_pixel_refine_coarse_metric_sample_evaluations=" in warning
        for warning in moving["warnings"]
    )
    assert any(
        "triangle_pixel_refine_workspace_mode=shared_flattened_candidate_metric_buffers" in warning
        for warning in moving["warnings"]
    )
    assert any("resident_registration_application=matrix_bilinear_batch" in warning for warning in moving["warnings"])
    assert any("triangle_warp_batch=true" in warning for warning in moving["warnings"])
    assert any("triangle_warp_batch_mode=native_matrix_bilinear_frames" in warning for warning in moving["warnings"])
    assert any(
        "triangle_warp_batch_timing_model=native_chunked_batch_warp_scatter_one_sync" in warning
        for warning in moving["warnings"]
    )
    assert any("resident CUDA triangle descriptor similarity" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "tri_no_refine"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert resident_registration["triangle_pixel_refine"] is False
    assert resident_registration["triangle_pixel_refine_batch"] is False
    assert resident_registration["triangle_pixel_refine_batch_mode"] == "off"
    assert resident_registration["triangle_pixel_refine_metric_workload_model"] == "off"
    assert resident_registration["triangle_pixel_refine_workspace_bytes"] == 0
    assert resident_registration["triangle_translation_refine"] is True
    assert resident_registration["triangle_centroid_refine"] is True
    assert resident_registration["triangle_centroid_refine_mode"] == "resident_gpu_global_mean_centroid"
    assert resident_registration["triangle_centroid_refine_background"] == "global_mean"
    assert resident_registration["triangle_centroid_refine_catalog_count"] >= 2
    assert resident_registration["triangle_centroid_refine_star_count"] > 0
    assert resident_registration["triangle_catalog_grid_auto"] is True
    assert resident_registration["triangle_catalog_selector"] == "resident_grid_top_nms"
    assert resident_registration["triangle_catalog_batch"] is True
    assert resident_registration["triangle_catalog_batch_mode"] == "grid_top_nms_fixed_threshold"
    assert resident_registration["star_grid_cols"] == 8
    assert resident_registration["star_grid_rows"] == 8
    assert resident_registration["star_catalog_deterministic"] is True
    assert resident_registration["triangle_grid_top_per_cell"] == 8
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert "triangle_centroid_refine_enabled=true" in moving["warnings"]
    assert "triangle_centroid_refine_mode=resident_gpu_global_mean_centroid" in moving["warnings"]
    assert "triangle_centroid_refine_background=global_mean" in moving["warnings"]
    assert "triangle_catalog_grid_auto=true" in moving["warnings"]
    assert "triangle_star_grid_cols=8" in moving["warnings"]
    assert "triangle_star_grid_rows=8" in moving["warnings"]
    assert "triangle_grid_top_per_cell=8" in moving["warnings"]
    assert abs(moving["matrix"][0][2] + 3.0) < 0.5
    assert abs(moving["matrix"][1][2] - 2.0) < 0.5
    assert all("triangle_pixel_refine_mode=" not in warning for warning in moving["warnings"])
    assert any("resident CUDA triangle descriptor similarity" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "rq"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    quality_reference_id = str(light_by_stem["light_002"]["id"])
    moving_id = str(light_by_stem["light_001"]["id"])
    write_json(plan, plan_payload)
    run.mkdir(parents=True)
    (run / "calib_cache" / "resident_masters").mkdir(parents=True)
    write_json(
        run / "frame_quality.json",
        {
            "schema_version": 1,
            "reference_frame_id": quality_reference_id,
            "frame_quality": [
                {"frame_id": moving_id, "reference_candidate": True, "star_count": 8},
                {"frame_id": quality_reference_id, "reference_candidate": True, "star_count": 10},
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-grid-top-per-cell",
            "2",
            "--resident-triangle-nms-scan-candidates",
            "96",
            "--resident-triangle-nms-min-separation-px",
            "2.0",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-triangle-min-agreement-score",
            "0.01",
            "--resident-triangle-agreement-rms-scale",
            "200",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    resident_registration = resident["artifacts"][0]["resident_registration"]
    reference_rows = [item for item in registration["results"] if item["status"] == "reference"]
    moving = [item for item in registration["results"] if item["frame_id"] == moving_id][0]

    assert [item["frame_id"] for item in reference_rows] == [quality_reference_id]
    assert resident_registration["reference_frame_id"] == quality_reference_id
    assert resident_registration["selected_reference_frame_id"] == quality_reference_id
    assert resident_registration["reference_selection_source"] == "frame_quality"
    assert resident_registration["quality_reference_frame_id"] == quality_reference_id
    assert resident_registration["quality_reference_status"] == "frame_quality"
    assert resident_registration["quality_reference_path"] == str(run / "frame_quality.json")
    assert moving["status"] == "ok"
    assert abs(moving["matrix"][0][2] - 3.0) < 0.5
    assert abs(moving["matrix"][1][2] + 2.0) < 0.5


def test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    stack_run = tmp_path / "resident_run_similarity_triangle_stack"
    fused_run = tmp_path / "resident_run_similarity_triangle_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    common_args = [
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "none",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "similarity_cuda_triangle",
        "--resident-star-threshold",
        "30",
        "--resident-star-max-candidates",
        "16",
        "--resident-star-tolerance-px",
        "1.5",
        "--resident-star-grid-cols",
        "4",
        "--resident-star-grid-rows",
        "4",
        "--resident-star-catalog-deterministic",
        "--resident-triangle-pixel-refine-final-stride",
        "2",
        "--resident-triangle-pixel-refine-fast-coarse",
        "--resident-warp-interpolation",
        "bilinear",
        "--resident-output-maps",
        "minimal",
        "--reference-frame-id",
        "light_001",
    ]

    assert main(["run", "--out", str(stack_run), *common_args]) == 0
    assert main(
        [
            "run",
            "--out",
            str(fused_run),
            *common_args,
            "--resident-integration-dispatch",
            "fused_matrix",
        ]
    ) == 0

    stack_master = read_fits_data(stack_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_master = read_fits_data(fused_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_registration = read_json(fused_run / "registration_results.json")
    fused_resident = read_json(fused_run / "resident_artifacts.json")
    fused_integration = read_json(fused_run / "integration_results.json")
    moving = [item for item in fused_registration["results"] if item["status"] != "reference"][0]
    artifact = fused_resident["artifacts"][0]
    resident_registration = artifact["resident_registration"]
    dispatch = artifact["resident_integration_dispatch"]
    warp_coverage = resident_registration["warp_coverage"]

    assert np.allclose(stack_master, fused_master, rtol=2e-5, atol=2e-4, equal_nan=True)
    assert fused_integration["outputs"][0]["resident_integration_dispatch"] == "fused_matrix"
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["used"] is True
    assert "similarity_cuda_triangle" in dispatch["eligible_registration_modes"]
    assert dispatch["deferred_matrix_frame_count"] == 1
    assert dispatch["download_mode"] == "master_only"
    assert dispatch["diagnostic_maps_downloaded"] is False
    assert dispatch["weight_map_downloaded"] is False
    assert resident_registration["mode"] == "similarity_cuda_triangle"
    assert resident_registration["triangle_warp_batch"] is False
    assert resident_registration["triangle_warp_batch_mode"] == "fused_matrix_deferred"
    assert resident_registration["triangle_warp_batch_timing_model"] == "fused_integration_deferred"
    assert resident_registration["triangle_warp_batch_frame_count"] == 0
    assert resident_registration["triangle_warp_batch_fallback_frame_count"] == 0
    assert resident_registration["triangle_fused_matrix_deferred"] is True
    assert resident_registration["triangle_fused_matrix_deferred_count"] == 1
    assert warp_coverage["native_source"] == "ResidentCalibratedStack fused matrix integration geometric coverage"
    assert warp_coverage["fused_deferred_frame_count"] == 1
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity_cuda_triangle"
    assert any("resident_registration_application=fused_matrix_deferred" == warning for warning in moving["warnings"])
    assert any("triangle_warp_batch=false" == warning for warning in moving["warnings"])
    assert any("triangle_warp_batch_mode=fused_matrix_deferred" == warning for warning in moving["warnings"])
    assert all("resident_registration_application=translation_bilinear" != warning for warning in moving["warnings"])


def test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "auto_bilinear_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-runtime-preset",
            "throughput-v2-fused",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-warp-interpolation",
            "bilinear",
            "--resident-output-maps",
            "minimal",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    timing = read_json(run / "run_timing.json")
    admission = read_json(run / "resident_memory_admission.json")
    dispatch = resident["artifacts"][0]["resident_integration_dispatch"]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert timing["resident_runtime_preset"] == "throughput-v2-fused"
    assert timing["resident_runtime_preset_effective"]["applied"]["resident_integration_dispatch"] == "auto"
    assert dispatch["requested_mode"] == "auto"
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["effective_mode"] == "fused_matrix"
    assert dispatch["selection_reason"] == "auto_fused_bilinear_matrix_route"
    assert dispatch["auto_policy"]["enabled"] is True
    assert dispatch["auto_policy"]["verified_fast_path"] is True
    assert dispatch["used"] is True
    assert dispatch["deferred_matrix_frame_count"] == 1
    assert admission["resident_integration_dispatch_requested"] == "auto"
    assert admission["resident_integration_dispatch_effective"] == "fused_matrix"
    assert admission["resident_integration_dispatch_reason"] == "auto_fused_bilinear_matrix_route"
    assert admission["fused_matrix_admission"] is True
    assert admission["peak_group"]["planned_warp_frame_count"] == 0
    assert admission["peak_group"]["chunked_warp_planned_workspace_bytes"] == 0
    assert integration["outputs"][0]["resident_integration_dispatch"] == "fused_matrix"
    assert integration["outputs"][0]["resident_integration_dispatch_requested"] == "auto"
    assert resident_registration["triangle_fused_matrix_deferred"] is True
    assert resident_registration["triangle_fused_matrix_deferred_count"] == 1
    assert any("resident_registration_application=fused_matrix_deferred" == warning for warning in moving["warnings"])


def test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "auto_lanczos_stack"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_triangle_tolerance_px": 1.5,
            "cuda_triangle_descriptor_radius": 0.08,
            "cuda_triangle_neighbors": 5,
            "cuda_triangle_max_descriptors": 256,
            "cuda_triangle_pixel_refine": True,
            "cuda_triangle_pixel_refine_coarse_stride": 1,
            "cuda_triangle_pixel_refine_final_stride": 1,
            "cuda_triangle_min_pixel_ncc": 0.1,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "winsorized_sigma",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_triangle",
            "--resident-integration-dispatch",
            "auto",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-catalog-deterministic",
            "--resident-triangle-pixel-refine-final-stride",
            "2",
            "--resident-triangle-pixel-refine-fast-coarse",
            "--resident-warp-interpolation",
            "lanczos3",
            "--resident-output-maps",
            "minimal",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    dispatch = resident["artifacts"][0]["resident_integration_dispatch"]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert dispatch["requested_mode"] == "auto"
    assert dispatch["mode"] == "stack"
    assert dispatch["effective_mode"] == "stack"
    assert dispatch["selection_reason"] == "auto_stack_non_bilinear_matrix_route"
    assert dispatch["auto_policy"]["enabled"] is True
    assert dispatch["auto_policy"]["verified_fast_path"] is False
    assert dispatch["auto_policy"]["conservative_stack_for_non_bilinear"] is True
    assert dispatch["used"] is False
    assert dispatch["deferred_matrix_frame_count"] == 0
    assert integration["outputs"][0]["resident_integration_dispatch"] == "stack"
    assert integration["outputs"][0]["resident_integration_dispatch_requested"] == "auto"
    assert resident_registration["triangle_fused_matrix_deferred"] is False
    assert resident_registration["triangle_fused_matrix_deferred_count"] == 0
    assert resident_registration["triangle_warp_batch_mode"] == "native_matrix_lanczos3_frames"
    assert any("resident_registration_application=matrix_lanczos3_batch" == warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_similarity_catalog_rejects_low_quality_matrix(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_run_similarity_catalog_quality_gate"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    plan_payload = read_json(plan)
    plan_payload.setdefault("registration_policy", {}).update(
        {
            "cuda_catalog_tolerance_px": 1.5,
            "cuda_catalog_min_pair_distance": 8.0,
            "cuda_catalog_similarity_top_k": 3,
            "cuda_catalog_min_scale": 0.99,
            "cuda_catalog_max_scale": 1.01,
            "cuda_catalog_max_abs_rotation_rad": 0.02,
            "cuda_catalog_pixel_refine_coarse_stride": 1,
            "cuda_catalog_pixel_refine_final_stride": 1,
            "cuda_catalog_min_pixel_ncc": 1.01,
            "cuda_catalog_min_selected_seed_inliers": 3,
        }
    )
    write_json(plan, plan_payload)

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "similarity_cuda_catalog",
            "--resident-star-threshold",
            "30",
            "--resident-star-max-candidates",
            "16",
            "--resident-star-tolerance-px",
            "1.5",
            "--resident-registration-max-shift",
            "8",
            "--resident-star-grid-cols",
            "4",
            "--resident-star-grid-rows",
            "4",
            "--resident-star-prior",
            "ncc",
            "--resident-star-prior-radius-px",
            "2",
            "--resident-star-core-preselect-top-k",
            "2",
            "--reference-frame-id",
            "light_001",
        ]
    ) == 0

    registration = read_json(run / "registration_results.json")
    integration = read_json(run / "integration_results.json")
    moving = [item for item in registration["results"] if item["status"] != "reference"][0]

    assert moving["status"] == "failed"
    assert integration["frame_weights"][moving["frame_id"]] == 0.0
    assert any("failed quality gate" in warning for warning in moving["warnings"])
    assert any("similarity_quality_gate_status=failed" in warning for warning in moving["warnings"])


def test_cli_resident_cuda_run_external_matrix_registration(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    external_registration = tmp_path / "external_registration_results.json"
    frame_weight_proposal = tmp_path / "frame_weight_proposal.json"
    tile_local_policy_replay = tmp_path / "tile_local_policy_replay.json"
    run = tmp_path / "resident_run_external_matrix"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    reference_id = str(light_by_stem["light_001"]["id"])
    moving_id = str(light_by_stem["light_002"]["id"])
    similarity_matrix = [
        [1.0, 0.001, -3.0],
        [-0.001, 1.0, 2.0],
        [0.0, 0.0, 1.0],
    ]
    write_json(
        external_registration,
        {
            "schema_version": 1,
            "reference_frame_id": reference_id,
            "registration_results": [
                {
                    "frame_id": reference_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    "matched_stars": 8,
                    "inliers": 8,
                    "rms_px": 0.0,
                    "status": "reference",
                    "warnings": [],
                },
                {
                    "frame_id": moving_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": similarity_matrix,
                    "matched_stars": 12,
                    "inliers": 10,
                    "rms_px": 0.4,
                    "status": "ok",
                    "warnings": ["synthetic external similarity matrix"],
                },
            ],
        },
    )
    write_json(
        frame_weight_proposal,
        {
            "artifact_type": "frame_weight_proposal",
            "method": "control_ratio",
            "source_integration_audit": "localized_audit.json",
            "frame_multipliers": [
                {
                    "frame_id": moving_id,
                    "multiplier": 0.25,
                    "reason": "unit-test localized contribution proposal",
                }
            ],
        },
    )
    write_json(
        tile_local_policy_replay,
        {
            "artifact_type": "tile_local_policy_replay",
            "target_group": "focus",
            "residual_stat": "signed_mean",
            "target_frame_ids": [moving_id],
            "summary": {
                "recommendation": "tile_local_replay_promising",
                "known_direction_tiles": 1,
                "moves_toward_reference": 1,
                "boost_tiles": 1,
                "mean_abs_residual_before": 0.1,
                "mean_abs_residual_after": 0.02,
            },
            "tiles": [
                {
                    "tile_index": 0,
                    "extent": {"x0": 0, "y0": 0, "x1": 8, "y1": 8},
                    "target_group": "focus",
                    "action": "boost",
                    "multiplier": 2.0,
                    "clamped": True,
                    "selected_frame_row_count": 1,
                    "canonical_delta_contribution_adu": 1.0,
                    "signed_residual_reference_units_before": -0.1,
                    "signed_residual_reference_units_after": -0.02,
                    "moves_toward_reference": True,
                }
            ],
        },
    )

    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "external_matrix",
            "--resident-registration-results",
            str(external_registration),
            "--resident-warp-interpolation",
            "lanczos3",
            "--resident-warp-clamping-threshold",
            "0.30",
            "--resident-registration-motion-weighting",
            "translation_mad",
            "--resident-registration-motion-threshold-sigma",
            "8",
            "--resident-frame-weight-proposal",
            str(frame_weight_proposal),
            "--resident-tile-local-policy-replay",
            str(tile_local_policy_replay),
        ]
    ) == 0

    integration = read_json(run / "integration_results.json")
    registration = read_json(run / "registration_results.json")
    resident = read_json(run / "resident_artifacts.json")
    moving = [item for item in registration["results"] if item["frame_id"] == moving_id][0]
    resident_registration = resident["artifacts"][0]["resident_registration"]
    weighting = resident["artifacts"][0]["resident_integration_weighting"]
    motion = weighting["registration_motion_weighting"]
    proposal = weighting["frame_weight_proposal"]
    tile_local = weighting["tile_local_policy_replay"]
    moving_weighting = [item for item in weighting["frame_results"] if item["frame_id"] == moving_id][0]

    assert integration["outputs"][0]["resident_registration"] == "external_matrix"
    assert integration["frame_weights"][moving_id] == 0.25
    assert registration["transform_model"] == "external_matrix"
    assert registration["warnings"][0].startswith("resident registration consumed external matrices")
    assert "lanczos3" in registration["warnings"][0]
    assert resident_registration["mode"] == "external_matrix"
    assert resident_registration["warp_interpolation"] == "lanczos3"
    assert resident_registration["warp_clamping_threshold"] == 0.30
    assert resident_registration["registration_motion_weighting_mode"] == "translation_mad"
    assert resident_registration["registration_motion_downweighted_frame_count"] == 0
    assert resident_registration["frame_weight_proposal_path"] == str(frame_weight_proposal)
    assert resident_registration["frame_weight_proposal_frame_count"] == 1
    assert resident_registration["frame_weight_proposal_downweighted_frame_count"] == 1
    assert motion["enabled"] is True
    assert motion["mode"] == "translation_mad"
    assert motion["threshold_sigma"] == 8.0
    assert motion["reason"] == "fewer_than_three_eligible_frames"
    assert proposal["enabled"] is True
    assert proposal["path"] == str(frame_weight_proposal)
    assert proposal["applied_downweighted_frame_count"] == 1
    assert tile_local["enabled"] is True
    assert tile_local["path"] == str(tile_local_policy_replay)
    assert tile_local["applied"] is False
    assert tile_local["target_frame_ids"] == [moving_id]
    assert tile_local["tiles"][0]["multiplier"] == 2.0
    assert moving_weighting["frame_weight_proposal_multiplier"] == 0.25
    assert moving_weighting["status"] == "frame_weight_proposal_downweighted"
    assert resident_registration["external_registration_results_path"] == str(external_registration)
    assert moving["status"] == "ok"
    assert moving["transform_model"] == "similarity"
    assert moving["matched_stars"] == 12
    assert moving["inliers"] == 10
    assert np.allclose(np.asarray(moving["matrix"], dtype=np.float32), np.asarray(similarity_matrix, dtype=np.float32))
    assert any("external_registration_application=matrix_lanczos3" == item for item in moving["warnings"])
    assert any("frame_weight_proposal_multiplier=0.25" == item for item in moving["warnings"])


def test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_light_star_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    external_registration = tmp_path / "external_registration_results.json"
    stack_run = tmp_path / "resident_run_external_matrix_stack"
    fused_run = tmp_path / "resident_run_external_matrix_fused"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    plan_payload = read_json(plan)
    light_by_stem = {
        Path(frame["path"]).stem: frame for frame in plan_payload["frames"] if frame["frame_type"] == "light"
    }
    reference_id = str(light_by_stem["light_001"]["id"])
    moving_id = str(light_by_stem["light_002"]["id"])
    similarity_matrix = [
        [1.0, 0.001, -3.0],
        [-0.001, 1.0, 2.0],
        [0.0, 0.0, 1.0],
    ]
    write_json(
        external_registration,
        {
            "schema_version": 1,
            "reference_frame_id": reference_id,
            "registration_results": [
                {
                    "frame_id": reference_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    "matched_stars": 8,
                    "inliers": 8,
                    "rms_px": 0.0,
                    "status": "reference",
                    "warnings": [],
                },
                {
                    "frame_id": moving_id,
                    "reference_frame_id": reference_id,
                    "transform_model": "similarity",
                    "matrix": similarity_matrix,
                    "matched_stars": 12,
                    "inliers": 10,
                    "rms_px": 0.4,
                    "status": "ok",
                    "warnings": ["synthetic external similarity matrix"],
                },
            ],
        },
    )

    common_args = [
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "winsorized_sigma",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "external_matrix",
        "--resident-registration-results",
        str(external_registration),
        "--resident-warp-interpolation",
        "bilinear",
    ]

    assert main(["run", "--out", str(stack_run), *common_args]) == 0
    assert main(
        [
            "run",
            "--out",
            str(fused_run),
            *common_args,
            "--resident-integration-dispatch",
            "fused_matrix",
        ]
    ) == 0

    stack_master = read_fits_data(stack_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_master = read_fits_data(fused_run / "integration" / "resident_master_H.fits", dtype=np.float32)
    fused_registration = read_json(fused_run / "registration_results.json")
    fused_resident = read_json(fused_run / "resident_artifacts.json")
    fused_integration = read_json(fused_run / "integration_results.json")
    moving = [item for item in fused_registration["results"] if item["frame_id"] == moving_id][0]
    dispatch = fused_resident["artifacts"][0]["resident_integration_dispatch"]
    warp_coverage = fused_resident["artifacts"][0]["resident_registration"]["warp_coverage"]

    assert np.allclose(stack_master, fused_master, rtol=2e-5, atol=2e-4, equal_nan=True)
    assert fused_integration["outputs"][0]["resident_integration_dispatch"] == "fused_matrix"
    assert dispatch["mode"] == "fused_matrix"
    assert dispatch["used"] is True
    assert dispatch["deferred_matrix_frame_count"] == 1
    assert dispatch["native_timing_s"]["rejection"] == "winsorized_sigma"
    assert dispatch["native_timing_s"]["avoids_stack_scatter"] is True
    assert warp_coverage["native_source"] == "ResidentCalibratedStack fused matrix integration geometric coverage"
    assert warp_coverage["fused_deferred_frame_count"] == 1
    assert moving["status"] == "ok"
    assert any("external_registration_application=fused_matrix_deferred" == item for item in moving["warnings"])


def test_cli_resident_cuda_uses_planner_matching_master_sets(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_dark_group_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_matching_groups"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-fits-read-mode",
            "auto",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    resident = read_json(run / "resident_artifacts.json")
    artifact = resident["artifacts"][0]
    master_stats = artifact["master_stats"]
    io_pipeline = artifact["resident_io_pipeline"]

    assert master_stats["calibration_group_policy"] == "planner_matching_groups_per_light"
    assert master_stats["set_count"] == 2
    assert {item["dark_count"] for item in master_stats["sets"].values()} == {1}
    assert len({item["dark_group"] for item in master_stats["sets"].values()}) == 2
    assert io_pipeline["fits_read_mode"] == "auto"
    assert io_pipeline["fits_read_mode_requested"] == "auto"
    assert io_pipeline["fits_read_mode_effective"] == "auto"
    assert io_pipeline["resident_fits_auto_selection"]["raw_u16_gpu"]["selected"] is False
    assert io_pipeline["resident_fits_auto_selection"]["raw_u16_gpu"]["eligible_frame_count"] == 0
    assert io_pipeline["resident_fits_auto_selection"]["raw_u16_gpu"]["fallback_reason_counts"][
        "bitpix_not_16:-32"
    ] == 2
    assert io_pipeline["fits_backend_counts"]["fast_simple"] >= 1
    assert io_pipeline["fits_fast_fallback_reason_counts"] == {}


def test_cli_resident_cuda_records_native_direct_fits_backend(tmp_path: Path):
    module = cuda_module_or_skip()
    if not hasattr(module, "read_simple_fits_into_f32"):
        pytest.skip("native direct FITS decoder is not available")
    dataset = _two_dark_group_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_native_direct_fits"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-fits-read-mode",
            "native_direct",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    artifact = read_json(run / "resident_artifacts.json")["artifacts"][0]
    io_pipeline = artifact["resident_io_pipeline"]
    timing = artifact["timing_s"]

    assert io_pipeline["fits_read_mode"] == "native_direct"
    assert io_pipeline["fits_backend_counts"]["native_direct_simple"] >= 1
    assert io_pipeline["fits_native_bytes_read"] > 0
    assert io_pipeline["fits_native_decode_cumulative_s"] >= 0.0
    assert timing["light_fits_native_file_read"] >= 0.0
    assert timing["light_fits_native_decode"] >= 0.0


def test_cli_resident_cuda_records_native_u16_gpu_decode_backend(tmp_path: Path):
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed"):
        pytest.skip("native u16 GPU decode resident path is not available")
    dataset = _u16_gpu_decode_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_native_u16_gpu"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "throughput-v1",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-fits-read-mode",
            "native_u16_gpu",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    artifact = read_json(run / "resident_artifacts.json")["artifacts"][0]
    io_pipeline = artifact["resident_io_pipeline"]
    source_dq = artifact["source_dq_summary"]

    assert io_pipeline["fits_read_mode"] == "native_u16_gpu"
    assert io_pipeline["fits_backend_counts"]["native_u16be_raw"] == 2
    assert io_pipeline["raw_gpu_decode_enabled"] is True
    assert io_pipeline["raw_gpu_h2d_bytes"] == 2 * 24 * 24 * 2
    assert io_pipeline["raw_gpu_float32_host_bytes_avoided"] == 2 * 24 * 24 * 4
    assert io_pipeline["source_dq_fast_skip_enabled"] is True
    assert io_pipeline["source_dq_fast_skipped_frame_count"] == 2
    assert io_pipeline["source_dq_sidecar_frame_count"] == 0
    assert source_dq["passed"] is True
    assert source_dq["input_invalid_samples_before_rejection"] == 0
    assert source_dq["fast_skip_frame_count"] == 2
    assert source_dq["source_counts"] == {"no_source_dq_fast_skip": 2}
    assert source_dq["status_counts"] == {"no_source_dq_fast_skip": 2}
    assert source_dq["rows"] == []
    assert io_pipeline["calibration_batch_mode"] == "fits_u16be_bzero_gpu_decode_callback_release_batch"
    assert artifact["resident_frame_mask_contract"]["summary"]["unknown_zero_weight_frame_count"] == 0


def test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group(tmp_path: Path):
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed"):
        pytest.skip("native u16 GPU decode resident path is not available")
    dataset = _u16_gpu_decode_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_auto_u16_gpu"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "throughput-v1",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-fits-read-mode",
            "auto",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    artifact = read_json(run / "resident_artifacts.json")["artifacts"][0]
    io_pipeline = artifact["resident_io_pipeline"]
    selection = io_pipeline["resident_fits_auto_selection"]

    assert io_pipeline["fits_read_mode"] == "auto"
    assert io_pipeline["fits_read_mode_requested"] == "auto"
    assert io_pipeline["fits_read_mode_effective"] == "native_u16_gpu"
    assert io_pipeline["fits_backend_counts"]["native_u16be_raw"] == 2
    assert io_pipeline["raw_gpu_decode_enabled"] is True
    assert io_pipeline["raw_gpu_h2d_bytes"] == 2 * 24 * 24 * 2
    assert selection["policy"] == "guarded_auto"
    assert selection["raw_u16_gpu"]["checked"] is True
    assert selection["raw_u16_gpu"]["runtime_eligible"] is True
    assert selection["raw_u16_gpu"]["eligible"] is True
    assert selection["raw_u16_gpu"]["selected"] is True
    assert selection["raw_u16_gpu"]["eligible_frame_count"] == 2
    assert selection["raw_u16_gpu"]["fallback_reason_counts"] == {}
    assert artifact["resident_io_overlap"]["fits_read_mode_effective"] == "native_u16_gpu"


def test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto(tmp_path: Path):
    module = cuda_module_or_skip()
    if not hasattr(module.ResidentCalibratedStack, "calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed"):
        pytest.skip("native u16 GPU decode resident path is not available")
    dataset = _u16_gpu_decode_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_default_guarded_auto_u16_gpu"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "throughput-v1",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    artifact = read_json(run / "resident_artifacts.json")["artifacts"][0]
    io_pipeline = artifact["resident_io_pipeline"]
    run_timing = read_json(run / "run_timing.json")
    mode_resolution = io_pipeline["fits_read_mode_resolution"]

    assert io_pipeline["fits_read_mode"] == "auto"
    assert io_pipeline["fits_read_mode_requested"] == "auto"
    assert io_pipeline["fits_read_mode_effective"] == "native_u16_gpu"
    assert io_pipeline["fits_backend_counts"]["native_u16be_raw"] == 2
    assert mode_resolution["source"] == "resident_cuda_guarded_auto_default"
    assert mode_resolution["explicit"] is False
    assert mode_resolution["requested"] is None
    assert mode_resolution["effective"] == "auto"
    assert artifact["resident_io_overlap"]["fits_read_mode_resolution"]["source"] == "resident_cuda_guarded_auto_default"
    assert (
        run_timing["resident_fits_read_mode_resolution"]["source"]
        == "resident_cuda_guarded_auto_default"
    )


def test_cli_resident_cuda_default_fits_read_mode_falls_back_for_float32_group(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_dark_group_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_default_guarded_auto_float32"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "throughput-v1",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    artifact = read_json(run / "resident_artifacts.json")["artifacts"][0]
    io_pipeline = artifact["resident_io_pipeline"]
    selection = io_pipeline["resident_fits_auto_selection"]
    mode_resolution = io_pipeline["fits_read_mode_resolution"]

    assert io_pipeline["fits_read_mode"] == "auto"
    assert io_pipeline["fits_read_mode_requested"] == "auto"
    assert io_pipeline["fits_read_mode_effective"] == "auto"
    assert io_pipeline["fits_backend_counts"]["fast_simple"] >= 1
    assert io_pipeline["raw_gpu_decode_enabled"] is False
    assert mode_resolution["source"] == "resident_cuda_guarded_auto_default"
    assert selection["fallback_mode"] == "auto"
    assert selection["fallback_reason"] == "raw_u16_gpu_group_ineligible"
    assert selection["raw_u16_gpu"]["checked"] is True
    assert selection["raw_u16_gpu"]["selected"] is False
    assert selection["raw_u16_gpu"]["eligible"] is False
    assert selection["raw_u16_gpu"]["fallback_reason_counts"]["bitpix_not_16:-32"] == 2


def test_cli_resident_cuda_explicit_astropy_fits_read_mode_is_preserved(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _u16_gpu_decode_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    run = tmp_path / "resident_explicit_astropy"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0
    assert main(
        [
            "run",
            "--plan",
            str(plan),
            "--out",
            str(run),
            "--backend",
            "cuda",
            "--memory-mode",
            "resident",
            "--resident-runtime-preset",
            "throughput-v1",
            "--until-stage",
            "integration",
            "--local-normalization",
            "off",
            "--integration-rejection",
            "none",
            "--integration-weighting",
            "none",
            "--resident-registration",
            "off",
            "--resident-fits-read-mode",
            "astropy",
            "--flat-floor",
            "0.05",
        ]
    ) == 0

    artifact = read_json(run / "resident_artifacts.json")["artifacts"][0]
    io_pipeline = artifact["resident_io_pipeline"]
    mode_resolution = io_pipeline["fits_read_mode_resolution"]

    assert io_pipeline["fits_read_mode"] == "astropy"
    assert io_pipeline["fits_read_mode_requested"] == "astropy"
    assert io_pipeline["fits_read_mode_effective"] == "astropy"
    assert io_pipeline["fits_backend_counts"]["astropy_scaled_memmap"] == 2
    assert io_pipeline["raw_gpu_decode_enabled"] is False
    assert mode_resolution["source"] == "explicit"
    assert mode_resolution["explicit"] is True
    assert mode_resolution["effective"] == "astropy"


def test_cli_resident_cuda_shared_master_cache_reuses_across_runs(tmp_path: Path):
    cuda_module_or_skip()
    dataset = _two_dark_group_dataset(tmp_path)
    manifest = tmp_path / "manifest.json"
    plan = tmp_path / "processing_plan.json"
    cache = tmp_path / "shared_resident_master_cache"
    run_a = tmp_path / "resident_cache_first"
    run_b = tmp_path / "resident_cache_second"

    assert main(["scan", "--root", str(dataset), "--out", str(manifest)]) == 0
    assert main(["plan", "--manifest", str(manifest), "--out", str(plan)]) == 0

    base_args = [
        "run",
        "--plan",
        str(plan),
        "--backend",
        "cuda",
        "--memory-mode",
        "resident",
        "--until-stage",
        "integration",
        "--local-normalization",
        "off",
        "--integration-rejection",
        "none",
        "--integration-weighting",
        "none",
        "--resident-registration",
        "off",
        "--flat-floor",
        "0.05",
        "--resident-master-cache-dir",
        str(cache),
    ]

    assert main([*base_args, "--out", str(run_a)]) == 0
    assert main([*base_args, "--out", str(run_b)]) == 0

    first_resident = read_json(run_a / "resident_artifacts.json")
    second_resident = read_json(run_b / "resident_artifacts.json")
    first_cache = read_json(run_a / "resident_master_cache.json")
    second_cache = read_json(run_b / "resident_master_cache.json")
    second_integration = read_json(run_b / "integration_results.json")
    first_sets = first_resident["artifacts"][0]["master_stats"]["sets"]
    second_artifact = second_resident["artifacts"][0]
    second_sets = second_artifact["master_stats"]["sets"]

    assert cache.exists()
    assert list(cache.glob("*_master_stats.json"))
    assert {item["cache_scope"] for item in first_sets.values()} == {"shared"}
    assert {item["cache_scope"] for item in second_sets.values()} == {"shared"}
    assert {item["cache_hit"] for item in first_sets.values()} == {False}
    assert {item["cache_hit"] for item in second_sets.values()} == {True}
    assert second_artifact["resident_io_pipeline"]["master_cache_scope"] == "shared"
    assert second_artifact["resident_io_pipeline"]["master_cache_dir"] == str(cache)
    assert first_cache["summary"]["cache_miss_count"] == len(first_sets)
    assert first_cache["summary"]["cache_hit_count"] == 0
    assert second_cache["summary"]["cache_hit_count"] == len(second_sets)
    assert second_cache["summary"]["cache_miss_count"] == 0
    assert second_cache["summary"]["passed"] is True
    assert second_cache["summary"]["cache_scope_counts"] == {"shared": len(second_sets)}
    assert all(entry["complete"] for group in second_cache["groups"] for entry in group["entries"])
    assert second_artifact["resident_master_cache"]["path"] == str(run_b / "resident_master_cache.json")
    assert second_artifact["resident_master_cache"]["summary"]["cache_hit_count"] == len(second_sets)
    assert second_integration["resident_master_cache_path"] == str(run_b / "resident_master_cache.json")
    assert second_integration["resident_master_cache_summary"]["cache_hit_count"] == len(second_sets)
    assert "--resident-master-cache-dir" in (run_b / "run_command.txt").read_text(encoding="utf-8")


def test_resident_frame_exclusion_matches_id_name_or_stem():
    frame = {
        "id": "F000196",
        "path": r"C:\data\LIGHT_H_0136.fits",
    }

    assert _matches_any_token(frame, {"F000196"})
    assert _matches_any_token(frame, {"LIGHT_H_0136.fits"})
    assert _matches_any_token(frame, {"LIGHT_H_0136"})
    assert not _matches_any_token(frame, {"LIGHT_H_0137"})
