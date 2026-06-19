from __future__ import annotations

from typing import Any

from glass.report.release_quality_evidence import (
    FINAL_EVIDENCE_DETAIL_FIELDS,
    FINAL_EVIDENCE_DETAIL_PREFIXES,
    FINAL_EVIDENCE_DETAIL_SUMMARY_FIELDS,
    FINAL_EVIDENCE_FIELDS,
    FINAL_EVIDENCE_LEGACY_FIELDS,
    ensure_final_evidence_detail_ready,
    final_evidence_detail_prefix_ready,
)


def _ready_detail_evidence() -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for prefix in FINAL_EVIDENCE_DETAIL_PREFIXES:
        evidence[f"{prefix}_final_evidence_ready"] = True
        evidence[f"{prefix}_final_evidence_match"] = True
        evidence[f"{prefix}_raw_final_evidence_ready"] = True
        evidence[f"{prefix}_phase2_final_evidence_ready"] = True
    return evidence


def test_release_quality_final_evidence_field_contract_has_no_duplicates():
    assert len(FINAL_EVIDENCE_FIELDS) == len(set(FINAL_EVIDENCE_FIELDS))
    assert set(FINAL_EVIDENCE_LEGACY_FIELDS).issubset(FINAL_EVIDENCE_FIELDS)
    assert set(FINAL_EVIDENCE_DETAIL_SUMMARY_FIELDS).issubset(FINAL_EVIDENCE_FIELDS)
    assert set(FINAL_EVIDENCE_DETAIL_FIELDS).issubset(FINAL_EVIDENCE_FIELDS)
    assert "raw_matrix_final_evidence_ready" in FINAL_EVIDENCE_FIELDS
    assert "phase2_default_promotion_phase2_final_evidence_ready" in (
        FINAL_EVIDENCE_FIELDS
    )


def test_release_quality_final_evidence_detail_compatible_missing_is_ready():
    evidence: dict[str, Any] = {}

    assert ensure_final_evidence_detail_ready(evidence) is True

    assert evidence["final_evidence_detail_fields_present"] is False
    assert evidence["final_evidence_detail_compatible_missing"] is True
    assert evidence["final_evidence_detail_ready"] is True


def test_release_quality_final_evidence_detail_ready_for_all_prefixes():
    evidence = _ready_detail_evidence()

    assert ensure_final_evidence_detail_ready(evidence) is True

    assert evidence["final_evidence_detail_fields_present"] is True
    assert evidence["final_evidence_detail_compatible_missing"] is False
    assert evidence["final_evidence_detail_ready"] is True
    for prefix in FINAL_EVIDENCE_DETAIL_PREFIXES:
        assert final_evidence_detail_prefix_ready(evidence, prefix=prefix) is True


def test_release_quality_final_evidence_detail_blocks_missing_prefix():
    evidence = _ready_detail_evidence()
    for suffix in (
        "final_evidence_ready",
        "final_evidence_match",
        "raw_final_evidence_ready",
        "phase2_final_evidence_ready",
    ):
        evidence.pop(f"phase2_default_promotion_{suffix}")

    assert ensure_final_evidence_detail_ready(evidence) is False

    assert evidence["final_evidence_detail_fields_present"] is True
    assert evidence["final_evidence_detail_compatible_missing"] is False
    assert evidence["final_evidence_detail_ready"] is False


def test_release_quality_final_evidence_detail_blocks_explicit_false():
    evidence = _ready_detail_evidence()
    evidence["raw_matrix_final_evidence_match"] = False

    assert ensure_final_evidence_detail_ready(evidence) is False

    assert final_evidence_detail_prefix_ready(evidence, prefix="raw_matrix") is False
    assert evidence["final_evidence_detail_ready"] is False


def test_release_quality_final_evidence_detail_strict_mode_blocks_partial_layers():
    evidence = _ready_detail_evidence()
    evidence["raw_matrix_raw_final_evidence_ready"] = None

    assert ensure_final_evidence_detail_ready(
        evidence,
        allow_partial_layer_ready=False,
    ) is False

    assert final_evidence_detail_prefix_ready(
        evidence,
        prefix="raw_matrix",
        allow_partial_layer_ready=True,
    ) is True
    assert final_evidence_detail_prefix_ready(
        evidence,
        prefix="raw_matrix",
        allow_partial_layer_ready=False,
    ) is False


def test_release_quality_final_evidence_detail_honors_existing_false_summary():
    evidence = _ready_detail_evidence()
    evidence["final_evidence_detail_ready"] = False

    assert ensure_final_evidence_detail_ready(evidence) is False

    assert evidence["final_evidence_detail_fields_present"] is True
    assert evidence["final_evidence_detail_compatible_missing"] is False
    assert evidence["final_evidence_detail_ready"] is False
