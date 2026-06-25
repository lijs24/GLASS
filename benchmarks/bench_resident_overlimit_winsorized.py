from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glass.report.resident_winsorized_benchmark import (  # noqa: E402
    build_resident_winsorized_overlimit_benchmark,
    write_resident_winsorized_overlimit_benchmark,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resident CUDA over-limit winsorized-sigma benchmark against the "
            "tiled CPUStackEngine baseline."
        )
    )
    parser.add_argument("--out", required=True, help="output benchmark JSON")
    parser.add_argument("--markdown", help="optional output Markdown summary")
    parser.add_argument("--frames", type=int, default=545)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--seed", type=int, default=627)
    parser.add_argument("--low-sigma", type=float, default=3.0)
    parser.add_argument("--high-sigma", type=float, default=3.0)
    parser.add_argument("--min-samples", type=int, default=3)
    parser.add_argument("--max-reject-fraction", type=float, default=0.5)
    parser.add_argument("--tile-size", type=int, default=16)
    parser.add_argument("--tolerance-rms", type=float, default=2.0e-5)
    parser.add_argument("--tolerance-max-abs", type=float, default=2.0e-4)
    parser.add_argument("--no-nan", action="store_true", help="disable injected non-finite samples")
    parser.add_argument(
        "--fail-on-failure",
        action="store_true",
        help="return exit code 2 unless the benchmark passes",
    )
    args = parser.parse_args()

    payload = build_resident_winsorized_overlimit_benchmark(
        frame_count=args.frames,
        height=args.height,
        width=args.width,
        seed=args.seed,
        low_sigma=args.low_sigma,
        high_sigma=args.high_sigma,
        min_samples=args.min_samples,
        max_reject_fraction=args.max_reject_fraction,
        tile_size=args.tile_size,
        tolerance_rms=args.tolerance_rms,
        tolerance_max_abs=args.tolerance_max_abs,
        inject_nan=not args.no_nan,
    )
    write_resident_winsorized_overlimit_benchmark(args.out, payload, markdown=args.markdown)
    print(Path(args.out).resolve())
    if args.fail_on_failure and not payload.get("passed"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
