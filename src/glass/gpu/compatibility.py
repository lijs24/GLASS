from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class WindowsCudaPackage:
    label: str
    toolkit: str
    architectures: tuple[int, ...]
    audience: str
    driver_hint: str


WINDOWS_CUDA_PACKAGES: tuple[WindowsCudaPackage, ...] = (
    WindowsCudaPackage(
        label="cuda11",
        toolkit="11.8",
        architectures=(50, 52, 60, 61, 70, 75, 80, 86),
        audience="Maxwell through Ampere, and newer GPUs as a compatibility fallback",
        driver_hint="NVIDIA driver new enough for CUDA 11.8",
    ),
    WindowsCudaPackage(
        label="cuda12",
        toolkit="12.4",
        architectures=(75, 80, 86, 89, 90),
        audience="Turing, Ampere, Ada, Hopper, and newer GPUs as a compatibility fallback",
        driver_hint="NVIDIA driver new enough for CUDA 12.4",
    ),
    WindowsCudaPackage(
        label="cuda13",
        toolkit="13.0",
        architectures=(86, 89, 90, 100, 120),
        audience="Recent NVIDIA GPUs, including Blackwell targets",
        driver_hint="NVIDIA driver new enough for CUDA 13.x",
    ),
)


def parse_compute_capability(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        major = int(value)
        minor = int(round((value - major) * 10.0))
        return major * 10 + minor
    text = str(value).strip()
    if not text or text.lower() == "unknown":
        return None
    match = re.search(r"(\d+)(?:\.(\d+))?", text)
    if match is None:
        return None
    major = int(match.group(1))
    minor = int((match.group(2) or "0")[:1])
    if major >= 50 and "." not in text:
        return major
    return major * 10 + minor


def format_compute_capability(code: int | None) -> str:
    if code is None:
        return "unknown"
    return f"{code // 10}.{code % 10}"


def package_match_for_cc(package: WindowsCudaPackage, compute_capability: int | None) -> dict[str, Any]:
    architectures = list(package.architectures)
    architecture_labels = [format_compute_capability(arch) for arch in architectures]
    if compute_capability is None:
        return {
            "label": package.label,
            "toolkit": package.toolkit,
            "architectures": architecture_labels,
            "compatible": None,
            "match": "unknown_device",
            "driver_hint": package.driver_hint,
            "audience": package.audience,
            "note": "GPU compute capability is unknown; run glass-doctor on the target machine.",
        }
    if compute_capability in package.architectures:
        match = "native_cubin"
        compatible = True
        note = "This package contains native GPU code for this compute capability."
    elif compute_capability > min(package.architectures):
        match = "ptx_jit_forward"
        compatible = True
        note = (
            "This package is expected to run through CUDA PTX forward JIT when the installed "
            "NVIDIA driver supports the bundled CUDA runtime. First launch may be slower and "
            "performance can be below a native cubin build."
        )
    else:
        match = "unsupported_older_gpu"
        compatible = False
        note = "This GPU is older than the package target range."
    return {
        "label": package.label,
        "toolkit": package.toolkit,
        "architectures": architecture_labels,
        "compatible": compatible,
        "match": match,
        "driver_hint": package.driver_hint,
        "audience": package.audience,
        "note": note,
    }


def _preferred_label_for_cc(compute_capability: int | None) -> str:
    if compute_capability is None:
        return "cpu"
    if compute_capability >= 120:
        return "cuda13"
    if compute_capability >= 75:
        return "cuda12"
    if compute_capability >= 50:
        return "cuda11"
    return "cpu"


def recommend_windows_cuda_packages(devices: list[dict[str, Any]]) -> dict[str, Any]:
    parsed_devices: list[dict[str, Any]] = []
    for device in devices:
        cc = parse_compute_capability(
            device.get("compute_capability", device.get("major_minor", device.get("cc")))
        )
        parsed_devices.append(
            {
                "device_id": device.get("device_id"),
                "name": device.get("name", "unknown"),
                "compute_capability": format_compute_capability(cc),
                "compute_capability_code": cc,
                "driver_version": device.get("driver_version", "unknown"),
            }
        )
    selected = max(
        (device for device in parsed_devices if device["compute_capability_code"] is not None),
        key=lambda item: int(item["compute_capability_code"]),
        default=None,
    )
    selected_cc = None if selected is None else int(selected["compute_capability_code"])
    package_results = [package_match_for_cc(package, selected_cc) for package in WINDOWS_CUDA_PACKAGES]
    compatible_labels = [
        str(package["label"]) for package in package_results if package["compatible"] is True
    ]
    preferred = _preferred_label_for_cc(selected_cc)
    ordered = [preferred] if preferred in compatible_labels else []
    for package in ("cuda13", "cuda12", "cuda11"):
        if package in compatible_labels and package not in ordered:
            ordered.append(package)
    ordered.append("cpu")
    if selected_cc is None:
        guidance = "No NVIDIA compute capability was detected. Use the CPU package or run on the target GPU machine."
    elif preferred == "cpu":
        guidance = "This GPU is below the supported CUDA package range. Use the CPU package."
    else:
        fallbacks = [item for item in ordered if item != preferred]
        guidance = (
            f"Try {preferred} first for native performance; if it fails to load, "
            f"try {', '.join(fallbacks)}. Newer GPUs may run older CUDA packages through PTX JIT."
        )
    return {
        "selected_device": selected,
        "packages": package_results,
        "ordered_try_list": ordered,
        "primary": ordered[0],
        "fallbacks": ordered[1:],
        "guidance": guidance,
        "ptx_forward_compatibility": True,
    }
