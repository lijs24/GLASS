from __future__ import annotations

from importlib.util import find_spec


def _cuda_feature_flags() -> dict[str, bool]:
    try:
        import gpwbpp_cuda  # type: ignore
    except Exception:
        return {}
    stack = getattr(gpwbpp_cuda, "ResidentCalibratedStack", None)
    return {
        "smoke_add_f32": hasattr(gpwbpp_cuda, "smoke_add_f32"),
        "calibrate_tile_f32": hasattr(gpwbpp_cuda, "calibrate_tile_f32"),
        "warp_matrix_bilinear_f32": hasattr(gpwbpp_cuda, "warp_matrix_bilinear_f32"),
        "warp_matrix_lanczos3_f32": hasattr(gpwbpp_cuda, "warp_matrix_lanczos3_f32"),
        "local_norm_apply_grid_f32": hasattr(gpwbpp_cuda, "local_norm_apply_grid_f32"),
        "resident_stack": stack is not None,
        "resident_lanczos3_warp": bool(stack is not None and hasattr(stack, "apply_matrix_lanczos3_frame")),
        "resident_grid_local_norm_apply": bool(
            stack is not None and hasattr(stack, "apply_grid_normalization_frame")
        ),
        "resident_grid_local_norm_stats": bool(stack is not None and hasattr(stack, "frame_pair_grid_stats")),
        "resident_simple_snr_weighting": bool(stack is not None and hasattr(stack, "frame_global_stats")),
        "resident_sigma_rejection": bool(stack is not None and hasattr(stack, "integrate_sigma_clip")),
    }


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
    cuda_flags = _cuda_feature_flags()
    return {
        "metadata_scan": True,
        "planning": True,
        "html_report": True,
        "synthetic_data": True,
        "cpu_baseline": True,
        "cuda_extension_importable": find_spec("gpwbpp_cuda") is not None,
        "cuda_available": cuda_extension_available(),
        "cuda_features": cuda_flags,
        "out_of_core_design": True,
        "registration": {
            "cpu": "star catalog translation/similarity helpers",
            "cuda": "resident translation, catalog similarity, triangle descriptors, bilinear/Lanczos3 matrix warp",
            "status": "partial WBPP-like registration; not PixInsight-equivalent",
        },
        "local_normalization": {
            "cpu": "tile median/std baseline with coefficient artifacts",
            "cuda": "tile mean/std primitive, resident global/grid mean/std, resident grid apply",
            "status": "partial; full interpolated/windowed LN is not complete",
        },
        "weighted_integration": {
            "cpu": "mean, simple_snr, sigma/winsorized rejection maps",
            "cuda": "resident weighted mean, simple_snr weights, and sigma/winsorized rejection maps",
            "status": "partial WBPP-like integration",
        },
    }


def require_cuda() -> None:
    if not cuda_extension_available():
        raise RuntimeError(
            "CUDA backend is not available. Install/build the optional gpwbpp_cuda "
            "extension or choose --backend cpu/auto."
        )
