from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.compare_frame_family import build_compare_frame_family_audit


def _matrix(tx: float, ty: float) -> list[list[float]]:
    return [[1.0, 0.0, tx], [0.0, 1.0, ty], [0.0, 0.0, 1.0]]


def _write_family_fixture(tmp_path: Path) -> tuple[Path, Path]:
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "frame_accounting.json",
        {
            "frames": [
                {
                    "frame_id": "F001",
                    "input_path": "light_001.fits",
                    "final_status": "integrated",
                    "integration_weight": 1.0,
                    "warnings": ["triangle_agreement_status=ok", "triangle_agreement_score=0.85"],
                },
                {
                    "frame_id": "F002",
                    "input_path": "light_002.fits",
                    "final_status": "integrated",
                    "integration_weight": 0.5,
                    "warnings": [
                        "triangle_agreement_status=downweighted",
                        "triangle_agreement_score=0.45",
                        "triangle_agreement_weight_multiplier=0.5",
                    ],
                },
                {
                    "frame_id": "F003",
                    "input_path": "light_003.fits",
                    "final_status": "integrated",
                    "integration_weight": 0.5,
                    "warnings": [
                        "triangle_agreement_status=downweighted",
                        "triangle_agreement_score=0.4",
                        "triangle_agreement_weight_multiplier=0.5",
                    ],
                },
                {
                    "frame_id": "F004",
                    "input_path": "light_004.fits",
                    "final_status": "integrated",
                    "integration_weight": 1.0,
                    "warnings": ["triangle_agreement_status=ok", "triangle_agreement_score=0.8"],
                },
            ]
        },
    )
    write_json(
        run / "registration_results.json",
        {
            "results": [
                {"frame_id": "F001", "status": "ok", "matrix": _matrix(0.0, 0.0), "rms_px": 0.1, "inliers": 20},
                {"frame_id": "F002", "status": "ok", "matrix": _matrix(12.0, 1.0), "rms_px": 0.4, "inliers": 17},
                {"frame_id": "F003", "status": "ok", "matrix": _matrix(14.0, 2.0), "rms_px": 0.5, "inliers": 16},
                {"frame_id": "F004", "status": "ok", "matrix": _matrix(2.0, 0.0), "rms_px": 0.2, "inliers": 22},
            ]
        },
    )
    replay = tmp_path / "tile_replay.json"
    write_json(
        replay,
        {
            "interpolation": "lanczos3",
            "tiles": [
                {
                    "index": 0,
                    "top_frames": [
                        {
                            "frame_id": "F002",
                            "weighted_delta_mean": 4.0,
                            "delta_to_master_stats": {"mean": 8.0, "p99": 15.0},
                            "sigma_proxy_high_pixels": 9,
                            "valid_pixels": 25,
                        },
                        {
                            "frame_id": "F003",
                            "weighted_delta_mean": 2.0,
                            "delta_to_master_stats": {"mean": 4.0, "p99": 9.0},
                            "sigma_proxy_high_pixels": 3,
                            "valid_pixels": 25,
                        },
                        {
                            "frame_id": "F001",
                            "weighted_delta_mean": 0.5,
                            "delta_to_master_stats": {"mean": 0.5, "p99": 1.0},
                            "valid_pixels": 25,
                        },
                    ],
                }
            ],
        },
    )
    return run, replay


def test_compare_frame_family_builds_focus_control_contrast(tmp_path: Path) -> None:
    run, replay = _write_family_fixture(tmp_path)

    payload = build_compare_frame_family_audit(
        replay,
        run,
        focus_range_start="F002",
        focus_range_end="F003",
        control_before=1,
        control_after=1,
    )

    assert payload["focus_ids"] == ["F002", "F003"]
    assert payload["control_ids"] == ["F001", "F004"]
    assert payload["replay_interpolation"] == "lanczos3"
    assert payload["interpretation"]["top_focus_frame"] == "F002"
    assert payload["focus_summary"]["agreement_status_counts"]["downweighted"] == 2
    assert payload["control_summary"]["agreement_status_counts"]["ok"] == 2
    assert payload["focus_vs_control"]["translation_x"]["focus_minus_control"] == 12.0
    assert payload["ranked_focus_rows"][0]["matrix_metrics"]["translation_x"] == 12.0
    assert payload["ranked_focus_rows"][0]["tile_summary"]["sigma_proxy_high_pixels"] == 9


def test_compare_frame_family_cli_writes_markdown(tmp_path: Path) -> None:
    run, replay = _write_family_fixture(tmp_path)
    out = tmp_path / "family.json"
    markdown = tmp_path / "family.md"

    assert (
        main(
            [
                "compare-frame-family",
                "--replay",
                str(replay),
                "--run",
                str(run),
                "--focus-range-start",
                "F002",
                "--focus-range-end",
                "F003",
                "--control-before",
                "1",
                "--control-after",
                "1",
                "--out",
                str(out),
                "--markdown",
                str(markdown),
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["focus_ids"] == ["F002", "F003"]
    assert markdown.exists()
    assert "Focus vs Control" in markdown.read_text(encoding="utf-8")
