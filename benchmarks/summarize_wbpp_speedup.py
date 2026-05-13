from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glass.report.speedup_report import summarize_wbpp_speedup, write_speedup_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize GLASS timing against a WBPP black-box result JSON.")
    parser.add_argument("--glass-run", required=True, help="GLASS run directory containing run_timing.json")
    parser.add_argument("--wbpp-result", required=True, help="PixInsight/WBPP black-box result JSON")
    parser.add_argument("--compare-json", help="optional GLASS compare JSON")
    parser.add_argument("--out", required=True, help="output summary JSON")
    parser.add_argument("--markdown", help="optional output Markdown summary")
    parser.add_argument("--min-speedup", type=float, default=1.25)
    args = parser.parse_args()

    summary = summarize_wbpp_speedup(
        args.glass_run,
        args.wbpp_result,
        compare_json=args.compare_json,
        min_speedup=args.min_speedup,
    )
    write_speedup_summary(args.out, summary, markdown=args.markdown)
    print(
        "speedup summary written: "
        f"{args.out} speedup={summary['speedup_vs_wbpp']:.3f}x "
        f"meets_min_speedup={summary['meets_min_speedup']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
