from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.resident_registration_compare import build_resident_registration_compare


def _write_sweep_summary(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "runs": [
                {
                    "variant_id": "fast_noisy",
                    "variant": {"triangle_grid_top_per_cell": 2},
                    "status": "completed",
                    "total_elapsed_s": 10.0,
                    "resident_registration_warp_s": 2.1,
                    "registration_triangle_moving_catalog_s": 0.6,
                    "registration_triangle_pixel_refine_s": 0.8,
                    "compare": {
                        "status": "completed",
                        "rms_diff": 0.0020,
                        "abs_diff_p99": 0.0005,
                        "relative_rms_diff": 0.42,
                        "coverage_fraction": 0.97,
                        "speedup_vs_reference": 70.0,
                    },
                    "compare_gate": {
                        "status": "failed",
                        "passed": False,
                        "reasons": ["rms_diff 0.002 > 0.0016"],
                    },
                },
                {
                    "variant_id": "slower_cleaner",
                    "variant": {"triangle_grid_top_per_cell": 4},
                    "status": "completed",
                    "total_elapsed_s": 11.0,
                    "resident_registration_warp_s": 2.7,
                    "registration_triangle_moving_catalog_s": 0.9,
                    "registration_triangle_pixel_refine_s": 0.9,
                    "compare": {
                        "status": "completed",
                        "rms_diff": 0.0014,
                        "abs_diff_p99": 0.00035,
                        "relative_rms_diff": 0.32,
                        "coverage_fraction": 0.97,
                        "speedup_vs_reference": 63.0,
                    },
                    "compare_gate": {"status": "passed", "passed": True, "reasons": []},
                },
            ],
        },
    )


def _write_candidate_audit(
    path: Path,
    *,
    variant_id: str,
    candidate_median: float,
    pixel_ncc: float,
    agreement_score: float,
) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "audit_type": "resident_registration_candidate_audit",
            "variant_id": variant_id,
            "status": "passed",
            "summary": {
                "frame_count": 200,
                "triangle_frame_count": 200,
                "failed_triangle_frame_count": 0,
                "quality_gate_failed_count": 0,
                "no_accepted_fit_count": 0,
                "parse_error_count": 0,
                "candidate_count_stats": {
                    "count": 192,
                    "min": candidate_median - 5.0,
                    "median": candidate_median,
                    "mean": candidate_median + 1.0,
                    "max": candidate_median + 5.0,
                },
                "fit_rms_px_stats": {"count": 193, "median": 0.6, "mean": 0.61},
                "pixel_rms_adu_stats": {"count": 192, "median": 160.0, "mean": 165.0},
                "pixel_ncc_stats": {"count": 192, "median": pixel_ncc, "mean": pixel_ncc - 0.01},
                "agreement_score_stats": {
                    "count": 192,
                    "median": agreement_score,
                    "mean": agreement_score - 0.02,
                },
            },
        },
    )


def test_resident_registration_compare_joins_sweep_and_candidate_audits(tmp_path: Path):
    sweep = tmp_path / "resident_prefetch_sweep_summary.json"
    audit_root = tmp_path / "audits"
    audit_root.mkdir()
    _write_sweep_summary(sweep)
    _write_candidate_audit(
        audit_root / "fast_noisy_candidate_audit.json",
        variant_id="fast_noisy",
        candidate_median=150000,
        pixel_ncc=0.91,
        agreement_score=0.54,
    )
    _write_candidate_audit(
        audit_root / "slower_cleaner_candidate_audit.json",
        variant_id="slower_cleaner",
        candidate_median=170000,
        pixel_ncc=0.96,
        agreement_score=0.68,
    )

    payload = build_resident_registration_compare(sweep, audit_root=audit_root)

    assert payload["variant_count"] == 2
    assert payload["missing_audit_count"] == 0
    assert payload["summary"]["compare_failed_count"] == 1
    assert payload["summary"]["registration_hard_failure_variant_count"] == 0
    assert payload["recommendation"]["status"] == "compare_failures_without_registration_hard_failures"
    rows = {row["variant_id"]: row for row in payload["rows"]}
    assert rows["fast_noisy"]["candidate_count_median"] == 150000
    assert rows["fast_noisy"]["agreement_score_median"] == 0.54
    assert rows["slower_cleaner"]["compare_gate_status"] == "passed"
    assert any(item["metric"] == "pixel_ncc_median" for item in payload["top_correlations"])


def test_resident_registration_compare_cli_writes_outputs_and_missing_audit_failure(tmp_path: Path):
    sweep = tmp_path / "resident_prefetch_sweep_summary.json"
    audit_root = tmp_path / "audits"
    audit_root.mkdir()
    out = tmp_path / "resident_registration_compare.json"
    markdown = tmp_path / "resident_registration_compare.md"
    _write_sweep_summary(sweep)
    _write_candidate_audit(
        audit_root / "fast_noisy_candidate_audit.json",
        variant_id="fast_noisy",
        candidate_median=150000,
        pixel_ncc=0.91,
        agreement_score=0.54,
    )
    _write_candidate_audit(
        audit_root / "slower_cleaner_candidate_audit.json",
        variant_id="slower_cleaner",
        candidate_median=170000,
        pixel_ncc=0.96,
        agreement_score=0.68,
    )

    assert (
        main(
            [
                "resident-registration-compare",
                "--sweep-summary",
                str(sweep),
                "--audit-root",
                str(audit_root),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )
    payload = read_json(out)
    assert payload["audit_type"] == "resident_registration_candidate_compare"
    assert "Resident Registration Candidate Compare" in markdown.read_text(encoding="utf-8")

    missing = tmp_path / "missing.json"
    assert (
        main(
            [
                "resident-registration-compare",
                "--sweep-summary",
                str(sweep),
                "--audit-root",
                str(tmp_path / "empty"),
                "--out",
                str(missing),
                "--fail-on-missing-audits",
            ]
        )
        == 2
    )
