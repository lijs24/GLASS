from __future__ import annotations

from glass.gpu.compatibility import parse_compute_capability, recommend_windows_cuda_packages


def _package_by_label(recommendation: dict, label: str) -> dict:
    return {package["label"]: package for package in recommendation["packages"]}[label]


def test_parse_compute_capability_variants():
    assert parse_compute_capability("12.0") == 120
    assert parse_compute_capability("sm_86") == 86
    assert parse_compute_capability("86") == 86
    assert parse_compute_capability(8.9) == 89
    assert parse_compute_capability(None) is None


def test_blackwell_can_try_all_windows_cuda_packages():
    recommendation = recommend_windows_cuda_packages(
        [
            {
                "device_id": 0,
                "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
                "compute_capability": "12.0",
                "driver_version": "596.21",
            }
        ]
    )

    assert recommendation["primary"] == "cuda13"
    assert recommendation["ordered_try_list"][:3] == ["cuda13", "cuda12", "cuda11"]
    assert recommendation["selected_device"]["compute_capability"] == "12.0"

    cuda13 = _package_by_label(recommendation, "cuda13")
    cuda12 = _package_by_label(recommendation, "cuda12")
    cuda11 = _package_by_label(recommendation, "cuda11")
    assert cuda13["compatible"] is True
    assert cuda13["match"] == "native_cubin"
    assert cuda12["compatible"] is True
    assert cuda12["match"] == "ptx_jit_forward"
    assert cuda11["compatible"] is True
    assert cuda11["match"] == "ptx_jit_forward"


def test_no_gpu_recommends_cpu_package():
    recommendation = recommend_windows_cuda_packages([])
    assert recommendation["primary"] == "cpu"
    assert recommendation["ordered_try_list"] == ["cpu"]
    assert recommendation["selected_device"] is None

