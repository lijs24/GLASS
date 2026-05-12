from __future__ import annotations

from importlib.util import find_spec


def cuda_extension_available() -> bool:
    spec = find_spec("gpwbpp_cuda")
    if spec is None:
        return False
    try:
        import gpwbpp_cuda  # type: ignore
    except Exception:
        return False
    return bool(getattr(gpwbpp_cuda, "cuda_available", lambda: False)())


def capability_report() -> dict[str, object]:
    return {
        "metadata_scan": True,
        "planning": True,
        "html_report": True,
        "synthetic_data": True,
        "cpu_baseline": True,
        "cuda_extension_importable": find_spec("gpwbpp_cuda") is not None,
        "cuda_available": cuda_extension_available(),
        "out_of_core_design": True,
        "registration": "cpu-basic + optional cuda_catalog_preview",
        "local_normalization": "cpu-basic",
        "weighted_integration": "cpu-basic",
    }


def require_cuda() -> None:
    if not cuda_extension_available():
        raise RuntimeError(
            "CUDA backend is not available. Install/build the optional gpwbpp_cuda "
            "extension or choose --backend cpu/auto."
        )
