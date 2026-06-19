from __future__ import annotations

from typing import Any

FINAL_EVIDENCE_LEGACY_FIELDS = (
    "final_evidence_compatible_missing",
    "final_evidence_ready",
    "final_evidence_match",
    "raw_final_evidence_present",
    "raw_final_evidence_ready",
    "phase2_final_evidence_present",
    "phase2_final_evidence_ready",
    "raw_matrix_final_checks_ready",
    "raw_matrix_final_checks_match",
    "raw_matrix_raw_final_checks_ready",
    "raw_matrix_phase2_final_checks_ready",
    "raw_matrix_default_final_checks_ready",
    "raw_matrix_default_final_checks_match",
    "raw_matrix_default_raw_final_checks_ready",
    "raw_matrix_default_phase2_final_checks_ready",
    "raw_default_promotion_final_checks_ready",
    "raw_default_promotion_final_checks_match",
    "raw_default_promotion_raw_final_checks_ready",
    "raw_default_promotion_phase2_final_checks_ready",
    "phase2_matrix_final_checks_ready",
    "phase2_matrix_final_checks_match",
    "phase2_matrix_raw_final_checks_ready",
    "phase2_matrix_phase2_final_checks_ready",
    "phase2_matrix_default_final_checks_ready",
    "phase2_matrix_default_final_checks_match",
    "phase2_matrix_default_raw_final_checks_ready",
    "phase2_matrix_default_phase2_final_checks_ready",
    "phase2_default_promotion_final_checks_ready",
    "phase2_default_promotion_final_checks_match",
    "phase2_default_promotion_raw_final_checks_ready",
    "phase2_default_promotion_phase2_final_checks_ready",
)

FINAL_EVIDENCE_DETAIL_FIELDS = (
    "raw_matrix_final_evidence_ready",
    "raw_matrix_final_evidence_match",
    "raw_matrix_raw_final_evidence_ready",
    "raw_matrix_phase2_final_evidence_ready",
    "raw_matrix_default_final_evidence_ready",
    "raw_matrix_default_final_evidence_match",
    "raw_matrix_default_raw_final_evidence_ready",
    "raw_matrix_default_phase2_final_evidence_ready",
    "raw_default_promotion_final_evidence_ready",
    "raw_default_promotion_final_evidence_match",
    "raw_default_promotion_raw_final_evidence_ready",
    "raw_default_promotion_phase2_final_evidence_ready",
    "phase2_matrix_final_evidence_ready",
    "phase2_matrix_final_evidence_match",
    "phase2_matrix_raw_final_evidence_ready",
    "phase2_matrix_phase2_final_evidence_ready",
    "phase2_matrix_default_final_evidence_ready",
    "phase2_matrix_default_final_evidence_match",
    "phase2_matrix_default_raw_final_evidence_ready",
    "phase2_matrix_default_phase2_final_evidence_ready",
    "phase2_default_promotion_final_evidence_ready",
    "phase2_default_promotion_final_evidence_match",
    "phase2_default_promotion_raw_final_evidence_ready",
    "phase2_default_promotion_phase2_final_evidence_ready",
)

FINAL_EVIDENCE_DETAIL_SUMMARY_FIELDS = (
    "final_evidence_detail_fields_present",
    "final_evidence_detail_compatible_missing",
    "final_evidence_detail_ready",
)

FINAL_EVIDENCE_FIELDS = (
    *FINAL_EVIDENCE_LEGACY_FIELDS,
    *FINAL_EVIDENCE_DETAIL_SUMMARY_FIELDS,
    *FINAL_EVIDENCE_DETAIL_FIELDS,
)

FINAL_EVIDENCE_DETAIL_PREFIXES = (
    "raw_matrix",
    "raw_matrix_default",
    "raw_default_promotion",
    "phase2_matrix",
    "phase2_matrix_default",
    "phase2_default_promotion",
)

PUBLICATION_FINAL_EVIDENCE_LEGACY_FIELDS = (
    "matrix_final_checks_ready",
    "matrix_final_checks_match",
    "matrix_raw_final_checks_ready",
    "matrix_phase2_final_checks_ready",
    "matrix_default_final_checks_ready",
    "matrix_default_final_checks_match",
    "matrix_default_raw_final_checks_ready",
    "matrix_default_phase2_final_checks_ready",
    "default_promotion_final_checks_ready",
    "default_promotion_final_checks_match",
    "default_promotion_raw_final_checks_ready",
    "default_promotion_phase2_final_checks_ready",
)

PUBLICATION_FINAL_EVIDENCE_DETAIL_FIELDS = (
    "matrix_final_evidence_ready",
    "matrix_final_evidence_match",
    "matrix_raw_final_evidence_ready",
    "matrix_phase2_final_evidence_ready",
    "matrix_default_final_evidence_ready",
    "matrix_default_final_evidence_match",
    "matrix_default_raw_final_evidence_ready",
    "matrix_default_phase2_final_evidence_ready",
    "default_promotion_final_evidence_ready",
    "default_promotion_final_evidence_match",
    "default_promotion_raw_final_evidence_ready",
    "default_promotion_phase2_final_evidence_ready",
)

PUBLICATION_FINAL_EVIDENCE_FIELDS = (
    *PUBLICATION_FINAL_EVIDENCE_LEGACY_FIELDS,
    *PUBLICATION_FINAL_EVIDENCE_DETAIL_FIELDS,
)

PUBLICATION_FINAL_EVIDENCE_DETAIL_PREFIXES = (
    "matrix",
    "matrix_default",
    "default_promotion",
)


def final_evidence_detail_prefix_ready(
    evidence: dict[str, Any],
    *,
    prefix: str,
    allow_partial_layer_ready: bool = True,
) -> bool:
    final_ready = evidence.get(f"{prefix}_final_evidence_ready")
    final_match = evidence.get(f"{prefix}_final_evidence_match")
    raw_ready = evidence.get(f"{prefix}_raw_final_evidence_ready")
    phase2_ready = evidence.get(f"{prefix}_phase2_final_evidence_ready")
    if (
        final_ready is None
        and final_match is None
        and raw_ready is None
        and phase2_ready is None
    ):
        return False
    if not allow_partial_layer_ready:
        return (
            final_ready is True
            and final_match is True
            and (
                (raw_ready is None and phase2_ready is None)
                or (raw_ready is True and phase2_ready is True)
            )
        )
    return (
        final_ready is True
        and final_match is True
        and (raw_ready is None or raw_ready is True)
        and (phase2_ready is None or phase2_ready is True)
    )


def ensure_final_evidence_detail_ready(
    evidence: dict[str, Any],
    *,
    detail_fields: tuple[str, ...] = FINAL_EVIDENCE_DETAIL_FIELDS,
    prefixes: tuple[str, ...] = FINAL_EVIDENCE_DETAIL_PREFIXES,
    allow_partial_layer_ready: bool = True,
) -> bool:
    detail_fields_present = any(evidence.get(field) is not None for field in detail_fields)
    if evidence.get("final_evidence_detail_fields_present") is None:
        evidence["final_evidence_detail_fields_present"] = detail_fields_present
    if evidence.get("final_evidence_detail_fields_present") is not True:
        evidence["final_evidence_detail_compatible_missing"] = True
        evidence["final_evidence_detail_ready"] = True
        return True
    ready = all(
        final_evidence_detail_prefix_ready(
            evidence,
            prefix=prefix,
            allow_partial_layer_ready=allow_partial_layer_ready,
        )
        for prefix in prefixes
    )
    if evidence.get("final_evidence_detail_ready") is not None:
        ready = ready and evidence.get("final_evidence_detail_ready") is True
    evidence["final_evidence_detail_ready"] = ready
    evidence["final_evidence_detail_compatible_missing"] = False
    return ready
