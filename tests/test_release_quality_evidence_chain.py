from __future__ import annotations

from typing import Any

from glass.report.release_quality_evidence import (
    FINAL_EVIDENCE_DETAIL_FIELDS,
    FINAL_EVIDENCE_DETAIL_PREFIXES,
    PUBLICATION_FINAL_EVIDENCE_DETAIL_FIELDS,
    PUBLICATION_FINAL_EVIDENCE_DETAIL_PREFIXES,
    ensure_final_evidence_detail_ready,
)


def _ready_publication_detail() -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for prefix in PUBLICATION_FINAL_EVIDENCE_DETAIL_PREFIXES:
        evidence[f"{prefix}_final_evidence_ready"] = True
        evidence[f"{prefix}_final_evidence_match"] = True
        evidence[f"{prefix}_raw_final_evidence_ready"] = True
        evidence[f"{prefix}_phase2_final_evidence_ready"] = True
    return evidence


def _evaluate_publication(evidence: dict[str, Any]) -> dict[str, Any]:
    payload = dict(evidence)
    ensure_final_evidence_detail_ready(
        payload,
        detail_fields=PUBLICATION_FINAL_EVIDENCE_DETAIL_FIELDS,
        prefixes=PUBLICATION_FINAL_EVIDENCE_DETAIL_PREFIXES,
        allow_partial_layer_ready=False,
    )
    return payload


def _evaluate_release_matrix(evidence: dict[str, Any]) -> dict[str, Any]:
    payload = dict(evidence)
    ensure_final_evidence_detail_ready(
        payload,
        detail_fields=FINAL_EVIDENCE_DETAIL_FIELDS,
        prefixes=FINAL_EVIDENCE_DETAIL_PREFIXES,
    )
    return payload


def _map_publication_to_release_matrix(
    publication: dict[str, Any],
) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    prefix_pairs = (
        ("raw_matrix", "matrix"),
        ("raw_matrix_default", "matrix_default"),
        ("raw_default_promotion", "default_promotion"),
        ("phase2_matrix", "matrix"),
        ("phase2_matrix_default", "matrix_default"),
        ("phase2_default_promotion", "default_promotion"),
    )
    suffixes = (
        "final_evidence_ready",
        "final_evidence_match",
        "raw_final_evidence_ready",
        "phase2_final_evidence_ready",
    )
    for target_prefix, source_prefix in prefix_pairs:
        for suffix in suffixes:
            evidence[f"{target_prefix}_{suffix}"] = publication[
                f"{source_prefix}_{suffix}"
            ]
    return evidence


def test_release_quality_evidence_chain_preserves_ready_detail_profile():
    publication = _evaluate_publication(_ready_publication_detail())
    matrix = _evaluate_release_matrix(_map_publication_to_release_matrix(publication))

    assert publication["final_evidence_detail_fields_present"] is True
    assert publication["final_evidence_detail_ready"] is True
    assert matrix["final_evidence_detail_fields_present"] is True
    assert matrix["final_evidence_detail_ready"] is True
    assert matrix["raw_matrix_final_evidence_ready"] is True
    assert matrix["phase2_default_promotion_phase2_final_evidence_ready"] is True


def test_release_quality_evidence_chain_detects_detail_loss():
    publication = _evaluate_publication(_ready_publication_detail())
    matrix = _evaluate_release_matrix({})

    assert publication["final_evidence_detail_fields_present"] is True
    assert publication["final_evidence_detail_ready"] is True
    assert matrix["final_evidence_detail_fields_present"] is False
    assert matrix["final_evidence_detail_compatible_missing"] is True
    assert (
        publication["final_evidence_detail_fields_present"]
        and not matrix["final_evidence_detail_fields_present"]
    )


def test_release_quality_evidence_chain_propagates_failed_detail():
    source = _ready_publication_detail()
    source["matrix_final_evidence_match"] = False
    publication = _evaluate_publication(source)
    matrix = _evaluate_release_matrix(_map_publication_to_release_matrix(publication))

    assert publication["final_evidence_detail_fields_present"] is True
    assert publication["final_evidence_detail_ready"] is False
    assert matrix["final_evidence_detail_fields_present"] is True
    assert matrix["final_evidence_detail_ready"] is False
    assert matrix["raw_matrix_final_evidence_match"] is False
    assert matrix["phase2_matrix_final_evidence_match"] is False
