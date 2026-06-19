from __future__ import annotations

from pathlib import Path

import pytest

from glass.engine.frame_accounting import build_frame_accounting
from glass.engine.resident_frame_mask import (
    build_resident_frame_mask_contract,
    summarize_resident_frame_mask_contracts,
    validate_resident_frame_mask_contract,
)
from glass.io.json_io import read_json, write_json


def test_resident_frame_mask_contract_classifies_quality_and_manual_excludes() -> None:
    contract = build_resident_frame_mask_contract(
        frame_ids=["F001", "F002", "F003"],
        frame_weights=[1.0, 0.0, 0.0],
        registration_results=[
            {"frame_id": "F001", "status": "ok"},
            {"frame_id": "F002", "status": "excluded"},
            {"frame_id": "F003", "status": "excluded"},
        ],
        registration_quality_decisions=[
            {
                "frame_id": "F002",
                "decision_status": "rejected",
                "final_status": "excluded",
                "reasons": ["registration_inliers_below_min:3<4"],
            }
        ],
        manual_excluded_frame_ids=["F003"],
        weighting_frame_results=[
            {"frame_id": "F001", "status": "unit"},
            {"frame_id": "F002", "status": "zero_weight"},
            {"frame_id": "F003", "status": "zero_weight"},
        ],
        filter_name="H",
        registration_mode="similarity_cuda_triangle",
        integration_dispatch="stack",
    )

    validate_resident_frame_mask_contract(contract)
    rows = {row["frame_id"]: row for row in contract["rows"]}

    assert contract["summary"]["passed"] is True
    assert contract["summary"]["active_frame_ids"] == ["F001"]
    assert contract["summary"]["masked_frame_ids"] == ["F002", "F003"]
    assert rows["F002"]["mask_categories"] == ["registration_quality", "registration"]
    assert rows["F002"]["mask_reasons"][0].startswith("registration_quality:")
    assert rows["F003"]["mask_categories"] == ["manual_exclude", "registration"]


def test_resident_frame_mask_contract_rejects_unaudited_zero_weight() -> None:
    contract = build_resident_frame_mask_contract(
        frame_ids=["F001", "F002"],
        frame_weights=[1.0, 0.0],
        registration_results=[
            {"frame_id": "F001", "status": "ok"},
            {"frame_id": "F002", "status": "ok"},
        ],
        weighting_frame_results=[
            {"frame_id": "F001", "status": "unit"},
            {"frame_id": "F002", "status": "zero_weight"},
        ],
    )

    assert contract["summary"]["passed"] is False
    assert contract["summary"]["unknown_zero_weight_frame_ids"] == ["F002"]
    with pytest.raises(RuntimeError, match="F002"):
        validate_resident_frame_mask_contract(contract)


def test_resident_frame_mask_summary_merges_groups() -> None:
    first = build_resident_frame_mask_contract(
        frame_ids=["F001"],
        frame_weights=[1.0],
        registration_results=[{"frame_id": "F001", "status": "ok"}],
    )
    second = build_resident_frame_mask_contract(
        frame_ids=["F002"],
        frame_weights=[0.0],
        registration_results=[{"frame_id": "F002", "status": "failed"}],
    )

    summary = summarize_resident_frame_mask_contracts([first, second])

    assert summary["frame_count"] == 2
    assert summary["active_frame_count"] == 1
    assert summary["masked_frame_count"] == 1
    assert summary["mask_category_counts"] == {"registration": 1}
    assert summary["passed"] is True


def test_frame_accounting_promotes_resident_quality_mask_to_quality_rejected(tmp_path: Path) -> None:
    write_json(
        tmp_path / "processing_plan.json",
        {
            "frames": [
                {"id": "F001", "frame_type": "light", "filter": "H", "path": "light_1.fits"},
                {"id": "F002", "frame_type": "light", "filter": "H", "path": "light_2.fits"},
            ]
        },
    )
    write_json(
        tmp_path / "registration_results.json",
        {
            "results": [
                {"frame_id": "F001", "status": "ok", "warnings": []},
                {"frame_id": "F002", "status": "excluded", "warnings": []},
            ]
        },
    )
    write_json(
        tmp_path / "integration_results.json",
        {
            "source_stage": "resident_calibrated_stack",
            "frame_weights": {"F001": 1.0, "F002": 0.0},
        },
    )
    contract = build_resident_frame_mask_contract(
        frame_ids=["F001", "F002"],
        frame_weights=[1.0, 0.0],
        registration_results=[
            {"frame_id": "F001", "status": "ok"},
            {"frame_id": "F002", "status": "excluded"},
        ],
        registration_quality_decisions=[
            {
                "frame_id": "F002",
                "decision_status": "rejected",
                "final_status": "excluded",
                "reasons": ["registration_inliers_below_min:3<4"],
            }
        ],
    )
    write_json(
        tmp_path / "resident_frame_masks.json",
        {
            "schema_version": 1,
            "artifact": "resident_frame_mask_contract",
            "summary": summarize_resident_frame_mask_contracts([contract]),
            "groups": [contract],
        },
    )

    payload = build_frame_accounting(tmp_path)
    written = read_json(tmp_path / "frame_accounting.json")
    rows = {row["frame_id"]: row for row in payload["frames"]}

    assert written["sources"]["resident_frame_masks"] is True
    assert rows["F002"]["resident_frame_mask_status"] == "masked"
    assert rows["F002"]["resident_frame_mask_categories"] == ["registration_quality", "registration"]
    assert rows["F002"]["quality_gate_status"] == "rejected"
    assert rows["F002"]["final_status"] == "quality_rejected"
    assert payload["summary"]["resident_frame_mask_masked_frames"] == 1
    assert payload["summary"]["zero_weight_frames"] == 1
    assert payload["summary"]["integration_status_counts"]["zero_weight"] == 1
