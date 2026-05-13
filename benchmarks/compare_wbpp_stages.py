from __future__ import annotations

import argparse
import gc
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glass.cpu.calibration import calibrate_light
from glass.io.fits_io import read_fits_data
from glass.io.json_io import read_json, write_json
from glass.io.xisf_io import read_xisf_data, read_xisf_metadata
from glass.models import CalibrationPolicy
from glass.report.compare_report import _diff_stats, _robust_linear_fit_to_reference

UINT16_SCALE = 1.0 / 65535.0


def _glob_one(root: Path, pattern: str) -> Path:
    matches = sorted(root.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"no file matched {pattern} under {root}")
    return matches[0]


def _policy_from_plan(plan: dict[str, Any]) -> CalibrationPolicy:
    raw = plan.get("calibration_plan", {}).get("calibration_policy", {})
    allowed = set(CalibrationPolicy.__dataclass_fields__.keys())
    return CalibrationPolicy(**{key: value for key, value in raw.items() if key in allowed})


def _frames_by_type(plan: dict[str, Any], frame_type: str) -> list[dict[str, Any]]:
    return [frame for frame in plan.get("frames", []) if frame.get("frame_type") == frame_type]


def _stage_compare(candidate: np.ndarray, reference: np.ndarray) -> dict[str, Any]:
    return {
        "candidate_stats": _array_stats(candidate),
        "reference_stats": _array_stats(reference),
        "raw": _diff_stats(candidate, reference),
        "robust_linear_fit": _robust_linear_fit_to_reference(candidate, reference),
    }


def _transformed_compare(
    candidate: np.ndarray,
    reference: np.ndarray,
    scale: float,
    offset: float,
    clip_low: float | None = None,
    clip_high: float | None = None,
) -> dict[str, Any]:
    transformed = np.asarray(candidate, dtype=np.float32) * np.float32(scale) + np.float32(offset)
    if clip_low is not None or clip_high is not None:
        transformed = np.clip(
            transformed,
            -np.inf if clip_low is None else float(clip_low),
            np.inf if clip_high is None else float(clip_high),
        )
    return {
        "scale": float(scale),
        "offset": float(offset),
        "clip_low": clip_low,
        "clip_high": clip_high,
        "stats": _diff_stats(transformed, reference),
        "robust_linear_fit": _robust_linear_fit_to_reference(transformed, reference),
    }


def _array_stats(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values)[np.isfinite(values)]
    if finite.size == 0:
        return {"finite": 0}
    return {
        "finite": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite)),
        "p001": float(np.percentile(finite, 0.01)),
        "p01": float(np.percentile(finite, 0.1)),
        "p1": float(np.percentile(finite, 1)),
        "p50": float(np.percentile(finite, 50)),
        "p99": float(np.percentile(finite, 99)),
        "p999": float(np.percentile(finite, 99.9)),
        "p9999": float(np.percentile(finite, 99.99)),
    }


def _flat_diagnostics(flat: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(flat)[np.isfinite(flat)]
    return {
        "fraction_le_1e_6": float(np.mean(finite <= 1.0e-6)),
        "fraction_le_1e_3": float(np.mean(finite <= 1.0e-3)),
        "fraction_le_1e_2": float(np.mean(finite <= 1.0e-2)),
        "fraction_le_0_1": float(np.mean(finite <= 0.1)),
        "fraction_le_0_2": float(np.mean(finite <= 0.2)),
    }


def _xisf_pedestal(path: Path) -> float | None:
    metadata = read_xisf_metadata(path, path.stem)
    raw = metadata.header_summary.get("PEDESTAL")
    if raw is None:
        return None
    try:
        return float(str(raw).strip("'\""))
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare GLASS stage outputs to WBPP black-box XISF outputs.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--glass-run", required=True)
    parser.add_argument("--wbpp-run", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--light-index", type=int, default=1)
    args = parser.parse_args()

    plan = read_json(args.plan)
    gp_run = Path(args.glass_run)
    wbpp_run = Path(args.wbpp_run)
    cache = gp_run / "calib_cache" / "resident_masters"
    policy = _policy_from_plan(plan)

    gp_bias = np.load(_glob_one(cache, "*master_bias.npy"))
    gp_dark = np.load(_glob_one(cache, "*master_dark.npy"))
    gp_flat = np.load(_glob_one(cache, "*master_flat.npy"))
    wbpp_bias = read_xisf_data(_glob_one(wbpp_run / "master", "masterBias*.xisf"))
    wbpp_dark = read_xisf_data(_glob_one(wbpp_run / "master", "masterDark*.xisf"))
    wbpp_flat = read_xisf_data(_glob_one(wbpp_run / "master", "masterFlat*FILTER-H*.xisf"))

    result: dict[str, Any] = {
        "schema_version": 1,
        "plan": str(Path(args.plan).resolve()),
        "glass_run": str(gp_run.resolve()),
        "wbpp_run": str(wbpp_run.resolve()),
        "policy": asdict(policy),
        "masters": {
            "bias": _stage_compare(gp_bias, wbpp_bias),
            "dark": _stage_compare(gp_dark, wbpp_dark),
            "flat": _stage_compare(gp_flat, wbpp_flat),
        },
        "flat_diagnostics": _flat_diagnostics(gp_flat),
    }

    lights = _frames_by_type(plan, "light")
    if not 1 <= args.light_index <= len(lights):
        raise ValueError(f"--light-index must be between 1 and {len(lights)}")
    light_record = lights[args.light_index - 1]
    darks = _frames_by_type(plan, "dark")
    dark_exposures = [float(frame["exposure_s"]) for frame in darks if frame.get("exposure_s") is not None]
    dark_exposure_s = float(np.median(dark_exposures)) if dark_exposures else None
    raw_light = read_fits_data(light_record["path"], dtype=np.float32)
    gp_calibrated = calibrate_light(
        raw_light,
        gp_bias,
        gp_dark,
        gp_flat,
        float(light_record.get("exposure_s") or 0.0),
        dark_exposure_s,
        policy,
    )
    wbpp_calibrated_path = _glob_one(
        wbpp_run / "calibrated" / "Light_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono",
        f"LIGHT_H_{args.light_index:04d}_c.xisf",
    )
    wbpp_calibrated = read_xisf_data(wbpp_calibrated_path)
    wbpp_pedestal_adu = _xisf_pedestal(wbpp_calibrated_path) or 0.0
    result["calibrated_light"] = {
        "light_index": args.light_index,
        "frame_id": light_record["id"],
        "glass_source": str(Path(light_record["path"]).resolve()),
        "wbpp_source": str(wbpp_calibrated_path.resolve()),
        "wbpp_pedestal_adu": wbpp_pedestal_adu,
        "comparison": _stage_compare(gp_calibrated, wbpp_calibrated),
        "candidate_with_wbpp_uint16_pedestal": _transformed_compare(
            gp_calibrated,
            wbpp_calibrated,
            scale=UINT16_SCALE,
            offset=wbpp_pedestal_adu * UINT16_SCALE,
            clip_low=0.0,
            clip_high=1.0,
        ),
        "extreme_candidate_fraction": {
            "lt_0": float(np.mean(gp_calibrated < 0)),
            "gt_65535": float(np.mean(gp_calibrated > 65535)),
            "gt_1e5": float(np.mean(gp_calibrated > 1.0e5)),
            "abs_gt_1e5": float(np.mean(np.abs(gp_calibrated) > 1.0e5)),
        },
    }
    del raw_light, gp_calibrated
    gc.collect()

    out = Path(args.out)
    write_json(out, result)
    print(f"stage comparison written: {out}")
    for stage in ["bias", "dark", "flat"]:
        fit = result["masters"][stage]["robust_linear_fit"]
        print(stage, fit.get("stats_fit_pixels", {}))
    print("calibrated", result["calibrated_light"]["comparison"]["robust_linear_fit"].get("stats_fit_pixels", {}))
    print("calibrated_wbpp_pedestal", result["calibrated_light"]["candidate_with_wbpp_uint16_pedestal"]["stats"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
