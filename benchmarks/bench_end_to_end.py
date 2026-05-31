from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.common import add_common_args, run_timed, write_result
from glass.cli import main as glass_main
from glass.io.json_io import read_json


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="auto")
    parser.add_argument("--memory-mode", choices=["tile", "resident"], default="tile")
    parser.add_argument(
        "--resident-registration",
        choices=[
            "off",
            "translation_preview",
            "translation_ncc_subpixel",
            "translation_star_catalog",
            "similarity_cuda_catalog",
            "similarity_cuda_triangle",
            "external_matrix",
        ],
        default="off",
    )
    parser.add_argument("--local-normalization", choices=["auto", "on", "off"], default="auto")
    parser.add_argument("--integration-weighting", choices=["auto", "none", "simple_snr"], default="auto")
    parser.add_argument(
        "--integration-rejection",
        choices=["auto", "none", "sigma_clip", "winsorized_sigma"],
        default="auto",
    )
    args = parser.parse_args()
    base = Path(args.out).with_suffix("")
    source = base / "source"
    audit = base / "audit"
    glass_main(
        [
            "synthetic",
            "--out",
            str(source),
            "--frames",
            str(args.frames),
            "--width",
            str(args.width),
            "--height",
            str(args.height),
            "--known-shift",
        ]
    )
    _, elapsed, peak_ram = run_timed(
        lambda: glass_main(
            [
                "audit",
                "--root",
                str(source),
                "--out",
                str(audit),
                "--backend",
                args.backend,
                "--tile-size",
                str(args.tile_size),
                "--memory-mode",
                args.memory_mode,
                "--local-normalization",
                args.local_normalization,
                "--integration-weighting",
                args.integration_weighting,
                "--integration-rejection",
                args.integration_rejection,
                "--resident-registration",
                args.resident_registration,
            ]
        )
    )
    integration = read_json(audit / "integration_results.json")
    registration = read_json(audit / "registration_results.json") if (audit / "registration_results.json").exists() else {}
    output = integration["outputs"][0]
    resident = read_json(audit / "resident_artifacts.json") if (audit / "resident_artifacts.json").exists() else {}
    quality_gate_rejected_frames = int(registration.get("quality_gate_rejected_frames") or 0)
    write_result(
        args.out,
        name="end_to_end",
        frame_count=int(output["frame_count"]),
        width=args.width,
        height=args.height,
        backend=str(output["backend"]),
        elapsed_s=elapsed,
        peak_ram_mb=peak_ram,
        output_path=audit,
        extra={
            "master_path": output["master_path"],
            "memory_mode": args.memory_mode,
            "resident_device": (resident.get("device") or {}).get("name"),
            "resident_estimated_peak_gib": (
                ((resident.get("artifacts") or [{}])[0].get("memory_estimate") or {}).get("estimated_peak_gib")
                if resident.get("artifacts")
                else None
            ),
            "integration_weighting": integration.get("weighting"),
            "integration_rejection": integration.get("rejection"),
            "input_light_frame_count": args.frames,
            "quality_gate_enforced": registration.get("quality_gate_enforced"),
            "quality_gate_rejected_frames": quality_gate_rejected_frames,
            "registration_reference_frame_id": registration.get("reference_frame_id"),
            "registered_or_integrated_frame_count": int(output["frame_count"]),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
