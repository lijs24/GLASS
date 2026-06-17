from __future__ import annotations

from tests.conftest import _cuda_busy_reason_from_query


def test_cuda_busy_reason_skips_when_memory_free_is_too_low() -> None:
    reason = _cuda_busy_reason_from_query("97887, 94000, 10", min_free_mib=8192)

    assert reason is not None
    assert "GPU memory is free" in reason


def test_cuda_busy_reason_skips_when_gpu_is_saturated() -> None:
    reason = _cuda_busy_reason_from_query("97887, 77517, 100", min_free_mib=8192)

    assert reason is not None
    assert "GPU is busy" in reason


def test_cuda_busy_reason_allows_idle_gpu() -> None:
    assert _cuda_busy_reason_from_query("97887, 1024, 5", min_free_mib=8192) is None
