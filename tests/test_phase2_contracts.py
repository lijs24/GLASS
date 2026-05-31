from __future__ import annotations

import numpy as np
import pytest

from glass.engine.contracts import (
    CombinePolicy,
    DQFlag,
    DQMask,
    IdentityTransform,
    ImageSource,
    OutputMapPolicy,
    RejectionPolicy,
    StackRequest,
    TileWindow,
)
from glass.engine.dq import dq_mask_from_coverage, dq_summary
from glass.io.image_source import FitsImageSource
from glass.models import to_jsonable


def test_tile_window_shape_and_overlap_clip():
    window = TileWindow(y0=10, y1=20, x0=5, x1=15, overlap=8)

    assert window.shape == (10, 10)
    assert window.as_slices() == (slice(10, 20), slice(5, 15))

    clipped = window.with_overlap_clipped(width=18, height=24)
    assert clipped.y0 == 2
    assert clipped.y1 == 24
    assert clipped.x0 == 0
    assert clipped.x1 == 18
    assert clipped.origin_y == 10
    assert clipped.origin_x == 5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"y0": -1, "y1": 1, "x0": 0, "x1": 1},
        {"y0": 1, "y1": 1, "x0": 0, "x1": 1},
        {"y0": 0, "y1": 1, "x0": 2, "x1": 1},
        {"y0": 0, "y1": 1, "x0": 0, "x1": 1, "overlap": -1},
    ],
)
def test_tile_window_rejects_invalid_bounds(kwargs):
    with pytest.raises(ValueError):
        TileWindow(**kwargs)


def test_dq_mask_marks_and_summarizes_flags():
    mask = DQMask.empty((3, 4))
    saturated = np.zeros((3, 4), dtype=bool)
    saturated[1, 2] = True

    mask.mark(DQFlag.SATURATED, saturated)
    mask.mark(DQFlag.WARP_EDGE, np.array([[True, False, False, False]] * 3))

    assert mask.count(DQFlag.SATURATED) == 1
    assert mask.count(DQFlag.WARP_EDGE) == 3
    assert mask.count(DQFlag.VALID) == 8
    assert mask.has_flag(DQFlag.SATURATED)[1, 2]
    assert mask.summary() == {"valid": 8, "saturated": 1, "warp_edge": 3}


def test_identity_transform_preserves_tile_and_copies_dq():
    tile = np.arange(6, dtype=np.float32).reshape(2, 3)
    dq = DQMask.empty(tile.shape).mark(DQFlag.HOT_PIXEL, tile > 4)
    transform = IdentityTransform()

    result = transform.apply_tile(tile, TileWindow(0, 2, 0, 3), state=None, dq=dq)

    assert np.array_equal(result.tile, tile)
    assert result.dq.count(DQFlag.HOT_PIXEL) == 1
    assert result.dq is not dq


def test_stack_request_defaults_are_jsonable():
    request = StackRequest(
        frame_ids=("light-001", "light-002"),
        source_kind="light",
        combine=CombinePolicy(method="weighted_mean", accumulator_dtype="float64"),
        rejection=RejectionPolicy(method="winsorized_sigma", iterations=2),
        output_maps=OutputMapPolicy(variance=True, dq=True),
        preprocess=("calibration", "warp"),
        weights={"light-001": 1.0, "light-002": 0.5},
        grouping_key="H_600s",
    )

    encoded = to_jsonable(request)

    assert encoded["combine"]["method"] == "weighted_mean"
    assert encoded["rejection"]["method"] == "winsorized_sigma"
    assert encoded["output_maps"]["variance"] is True
    assert encoded["frame_ids"] == ["light-001", "light-002"]


def test_stack_request_requires_frames():
    with pytest.raises(ValueError):
        StackRequest(frame_ids=(), source_kind="light")


def test_fits_image_source_reads_tile_and_mask(small_fits_dataset):
    path = small_fits_dataset / "light" / "light_001.fits"
    window = TileWindow(y0=2, y1=6, x0=3, x1=8)

    source = FitsImageSource(path)
    assert isinstance(source, ImageSource)
    assert source.width == 20
    assert source.height == 16

    with source:
        tile = source.read_tile(window)
        mask = source.read_mask_tile(window)

    assert tile.shape == window.shape
    assert np.allclose(tile, 1200.0)
    assert mask.summary() == {"valid": 20}


def test_dq_helper_builds_summary_from_coverage():
    coverage = np.array([[1.0, 0.0], [np.nan, 1.0]], dtype=np.float32)

    mask = dq_mask_from_coverage(coverage, DQFlag.WARP_EDGE)

    assert dq_summary(mask) == {"valid": 2, "warp_edge": 2}
