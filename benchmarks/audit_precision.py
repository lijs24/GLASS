from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy
from glass.validation.precision import compare_precision_on_crops, read_xisf_sample_format


def _frames_by_type(plan: dict[str, Any], frame_type: str) -> list[dict[str, Any]]:
    return [frame for frame in plan["frames"] if frame.get("frame_type") == frame_type]


def _paths(frames: list[dict[str, Any]]) -> list[str]:
    return [str(frame["path"]) for frame in frames]


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
    return CalibrationPolicy(**{key: value for key, value in raw.items() if key in allowed})


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit CPU/CUDA floating-point precision on FITS crops.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--light-limit", type=int, default=16)
    parser.add_argument("--calib-limit", type=int, default=20)
    parser.add_argument("--crop-size", type=int, default=512)
    parser.add_argument("--x0", type=int, default=None)
    parser.add_argument("--y0", type=int, default=None)
    parser.add_argument("--wbpp-xisf", action="append", default=[])
    args = parser.parse_args()

    plan = read_json(args.plan)
    lights = _frames_by_type(plan, "light")[: args.light_limit]
    bias = _frames_by_type(plan, "bias")[: args.calib_limit]
    dark = _frames_by_type(plan, "dark")[: args.calib_limit]
    flat = _frames_by_type(plan, "flat")[: args.calib_limit]
    if not lights:
        raise ValueError("plan contains no light frames")

    height = int(lights[0]["height"])
    width = int(lights[0]["width"])
    crop_size = int(args.crop_size)
    x0 = int(args.x0) if args.x0 is not None else max((width - crop_size) // 2, 0)
    y0 = int(args.y0) if args.y0 is not None else max((height - crop_size) // 2, 0)
    dark_exposures = [float(frame["exposure_s"]) for frame in dark if frame.get("exposure_s") is not None]
    dark_exposure_s = float(np.median(dark_exposures)) if dark_exposures else None

    try:
        import glass_cuda

        cuda_module = glass_cuda if glass_cuda.cuda_available() else None
    except Exception:
        cuda_module = None

    result = compare_precision_on_crops(
        lights,
        _paths(bias),
        _paths(dark),
        _paths(flat),
        y0,
        x0,
        crop_size,
        crop_size,
        dark_exposure_s,
        _policy_from_plan(plan),
        cuda_module=cuda_module,
    )
    result["dataset"] = {
        "plan": str(Path(args.plan).resolve()),
        "light_count": len(lights),
        "bias_count": len(bias),
        "dark_count": len(dark),
        "flat_count": len(flat),
        "shape": {"height": height, "width": width},
    }
    result["cuda_available"] = cuda_module is not None
    result["wbpp_sample_formats"] = [
        {"path": str(Path(path).resolve()), "sample_format": read_xisf_sample_format(path)}
        for path in args.wbpp_xisf
    ]
    result["notes"] = [
        "CPU64 is the audit reference for arithmetic only; it is not assumed to be WBPP's internal implementation.",
        "WBPP precision evidence is taken from black-box XISF output headers, not official source code.",
    ]

    out = Path(args.out)
    write_json(out, result)
    print(f"precision audit written: {out}")
    print(result["integration_errors"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
