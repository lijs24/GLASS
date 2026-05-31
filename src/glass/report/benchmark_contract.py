from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.engine.dq import dq_provenance_summary_from_resident
from glass.report.dq_map_verify import summarize_count_map_pixels, summarize_dq_map_pixels
from glass.report.speedup_report import _read_json_lenient


def load_benchmark_contract(path: str | Path) -> dict[str, Any]:
    contract = _read_json_lenient(path)
    if not isinstance(contract, dict):
        raise ValueError(f"benchmark contract must be a JSON object: {path}")
    if int(contract.get("schema_version", 1)) != 1:
        raise ValueError(f"unsupported benchmark contract schema_version: {contract.get('schema_version')}")
    return contract


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "evidence": evidence,
        "note": note,
    }


def _close_enough(actual: Any, expected: Any, *, abs_tol: float, rel_tol: float) -> bool:
    actual_number = _numeric(actual)
    expected_number = _numeric(expected)
    if actual_number is None or expected_number is None:
        return False
    tolerance = max(float(abs_tol), abs(expected_number) * float(rel_tol))
    return abs(actual_number - expected_number) <= tolerance


def _read_run_command(glass_run: str | Path) -> str | None:
    path = Path(glass_run) / "run_command.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _load_resident_timing(glass_run: str | Path) -> dict[str, Any]:
    path = Path(glass_run) / "resident_artifacts.json"
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return {}
    first = artifacts[0]
    if not isinstance(first, dict):
        return {}
    timing = first.get("timing_s")
    return timing if isinstance(timing, dict) else {}


def _load_json_object_if_present(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    return payload if isinstance(payload, dict) else {}


def _path_exists_maybe_relative(path_value: Any, run_root: Path) -> bool:
    if not path_value:
        return False
    path = Path(str(path_value))
    if path.is_absolute():
        return path.exists()
    return (run_root / path).exists()


def _resolve_path_maybe_relative(path_value: Any, run_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    return path if path.is_absolute() else run_root / path


def _dq_record_from_payload(
    payload: dict[str, Any],
    *,
    run_root: Path,
    source_file: str,
    source_kind: str,
    index: int,
) -> dict[str, Any] | None:
    summary = payload.get("dq_provenance_summary")
    normalized_from_legacy = False
    if not isinstance(summary, dict):
        provenance = payload.get("dq_coverage_provenance")
        dq_summary = payload.get("dq_summary")
        if isinstance(provenance, dict) or isinstance(dq_summary, dict):
            summary = dq_provenance_summary_from_resident(
                provenance if isinstance(provenance, dict) else None,
                dq_summary if isinstance(dq_summary, dict) else None,
                item=payload.get("filter"),
            )
            normalized_from_legacy = True
    if not isinstance(summary, dict):
        return None
    dq_map_path = payload.get("dq_map_path")
    coverage_map_path = payload.get("coverage_map_path")
    low_rejection_map_path = payload.get("low_rejection_map_path")
    high_rejection_map_path = payload.get("high_rejection_map_path")
    return {
        "source_file": source_file,
        "source_kind": source_kind,
        "index": index,
        "normalized_from_legacy": normalized_from_legacy,
        "dq_map_path": dq_map_path,
        "dq_map_exists": _path_exists_maybe_relative(dq_map_path, run_root),
        "coverage_map_path": coverage_map_path,
        "coverage_map_exists": _path_exists_maybe_relative(coverage_map_path, run_root),
        "low_rejection_map_path": low_rejection_map_path,
        "low_rejection_map_exists": _path_exists_maybe_relative(low_rejection_map_path, run_root),
        "high_rejection_map_path": high_rejection_map_path,
        "high_rejection_map_exists": _path_exists_maybe_relative(high_rejection_map_path, run_root),
        "output_map_policy": dict(payload.get("output_map_policy") or {}),
        "dq_flag_bits": dict(payload.get("dq_flag_bits") or {}),
        "source_provenance": dict(payload.get("dq_coverage_provenance") or {}),
        "summary": summary,
    }


def _dq_contract_flags(dq_contract: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    for key in (
        "dq_map_summary_match_flags",
        "required_output_dq_flags",
        "positive_output_dq_flags",
    ):
        for flag in dq_contract.get(key) or []:
            name = str(flag).lower()
            if name not in flags:
                flags.append(name)
    return flags or ["valid", "no_data", "warp_edge", "low_rejected", "high_rejected"]


def _attach_dq_map_pixel_verification(
    records: list[dict[str, Any]],
    *,
    run_root: Path,
    dq_contract: dict[str, Any],
) -> None:
    if not dq_contract.get("verify_dq_map_pixels"):
        return
    flags = _dq_contract_flags(dq_contract)
    tile_size = int(dq_contract.get("dq_map_verify_tile_size") or 2048)
    tolerance = int(dq_contract.get("dq_map_summary_tolerance_pixels") or 0)
    cache: dict[str, dict[str, Any]] = {}
    for record in records:
        dq_path = _resolve_path_maybe_relative(record.get("dq_map_path"), run_root)
        if dq_path is None:
            record["dq_map_pixel_verification"] = {
                "status": "missing_path",
                "verified": False,
                "error": "dq_map_path is missing",
            }
            continue
        cache_key = str(dq_path)
        try:
            verification = cache.get(cache_key)
            if verification is None:
                verification = summarize_dq_map_pixels(dq_path, flags=flags, tile_size=tile_size)
                cache[cache_key] = verification
            output_summary = (record.get("summary") or {}).get("output_dq_summary") or {}
            matches: dict[str, dict[str, Any]] = {}
            for flag in flags:
                actual = (verification.get("counts") or {}).get(flag)
                expected = output_summary.get(flag)
                actual_int = None if actual is None else int(actual)
                expected_int = None if expected is None else int(expected)
                delta = None if actual_int is None or expected_int is None else actual_int - expected_int
                matches[flag] = {
                    "actual": actual_int,
                    "summary": expected_int,
                    "delta": delta,
                    "passed": delta is not None and abs(delta) <= tolerance,
                }
            record["dq_map_pixel_verification"] = {
                "status": "verified",
                "verified": True,
                "summary_tolerance_pixels": tolerance,
                "result": verification,
                "summary_matches": matches,
            }
        except Exception as exc:  # pragma: no cover - exercised through audit failure path
            record["dq_map_pixel_verification"] = {
                "status": "error",
                "verified": False,
                "error": str(exc),
            }


def _map_skipped_by_policy(record: dict[str, Any], map_name: str) -> bool:
    policy = record.get("output_map_policy") or {}
    skipped = policy.get("skipped") or []
    return str(map_name) in {str(item) for item in skipped}


def _attach_output_count_map_verification(
    records: list[dict[str, Any]],
    *,
    run_root: Path,
    dq_contract: dict[str, Any],
) -> None:
    if not dq_contract.get("verify_output_count_maps"):
        return
    tile_size = int(dq_contract.get("count_map_verify_tile_size") or 2048)
    threshold = float(dq_contract.get("count_map_positive_threshold") or 0.0)
    cache: dict[str, dict[str, Any]] = {}
    map_fields = {
        "coverage": "coverage_map_path",
        "low_rejection": "low_rejection_map_path",
        "high_rejection": "high_rejection_map_path",
    }
    for record in records:
        output_verification: dict[str, Any] = {}
        for map_name, path_key in map_fields.items():
            path_value = record.get(path_key)
            map_path = _resolve_path_maybe_relative(path_value, run_root)
            if map_path is None:
                output_verification[map_name] = {
                    "status": "skipped" if _map_skipped_by_policy(record, map_name) else "missing_path",
                    "verified": False,
                    "path": path_value,
                }
                continue
            cache_key = str(map_path)
            try:
                summary = cache.get(cache_key)
                if summary is None:
                    summary = summarize_count_map_pixels(
                        map_path,
                        tile_size=tile_size,
                        positive_threshold=threshold,
                    )
                    cache[cache_key] = summary
                output_verification[map_name] = {
                    "status": "verified",
                    "verified": True,
                    "result": summary,
                }
            except Exception as exc:  # pragma: no cover - exercised through audit failure path
                output_verification[map_name] = {
                    "status": "error",
                    "verified": False,
                    "path": path_value,
                    "error": str(exc),
                }
        record["output_count_map_verification"] = output_verification


def collect_dq_provenance_records(
    glass_run: str | Path,
    *,
    dq_contract: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    run_root = Path(glass_run)
    records: list[dict[str, Any]] = []

    integration = _load_json_object_if_present(run_root / "integration_results.json")
    outputs = integration.get("outputs") or []
    if isinstance(outputs, list):
        for index, output in enumerate(outputs):
            if not isinstance(output, dict):
                continue
            record = _dq_record_from_payload(
                output,
                run_root=run_root,
                source_file="integration_results.json",
                source_kind="integration_output",
                index=index,
            )
            if record is not None:
                records.append(record)

    resident = _load_json_object_if_present(run_root / "resident_artifacts.json")
    artifacts = resident.get("artifacts") or []
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                continue
            record = _dq_record_from_payload(
                artifact,
                run_root=run_root,
                source_file="resident_artifacts.json",
                source_kind="resident_artifact",
                index=index,
            )
            if record is not None:
                records.append(record)

    if dq_contract:
        _attach_dq_map_pixel_verification(records, run_root=run_root, dq_contract=dq_contract)
        _attach_output_count_map_verification(records, run_root=run_root, dq_contract=dq_contract)
    return records


def _record_summaries(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record.get("summary") or {} for record in records]


def _summary_number(summary: dict[str, Any], key: str) -> float | None:
    value = summary.get(key)
    return _numeric(value)


def _summary_output_count(summary: dict[str, Any], key: str) -> float | None:
    output = summary.get("output_dq_summary")
    if not isinstance(output, dict):
        return None
    return _numeric(output.get(key))


def _summary_output_count_default_zero(summary: dict[str, Any], key: str) -> int:
    value = _summary_output_count(summary, key)
    return 0 if value is None else int(value)


def _provenance_nested_number(provenance: dict[str, Any], section: str, key: str) -> float | None:
    nested = provenance.get(section)
    if not isinstance(nested, dict):
        return None
    return _numeric(nested.get(key))


def _build_dq_provenance_contract_checks(
    dq_contract: dict[str, Any],
    *,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    summaries = _record_summaries(records)
    min_records = int(dq_contract.get("min_records") or (1 if dq_contract.get("required") else 0))
    if dq_contract.get("required") or min_records:
        checks.append(
            _check(
                "contract_dq_provenance_records",
                len(records) >= min_records,
                {"actual": len(records), "required_min": min_records},
            )
        )

    for schema in dq_contract.get("required_source_schemas") or []:
        schema_text = str(schema)
        checks.append(
            _check(
                f"contract_dq_source_schema:{schema_text}",
                any(summary.get("source_schema") == schema_text for summary in summaries),
                {"required": schema_text, "available": sorted({str(s.get("source_schema")) for s in summaries})},
            )
        )

    for engine in dq_contract.get("required_engines") or []:
        engine_text = str(engine)
        checks.append(
            _check(
                f"contract_dq_engine:{engine_text}",
                any(summary.get("engine") == engine_text for summary in summaries),
                {"required": engine_text, "available": sorted({str(s.get("engine")) for s in summaries})},
            )
        )

    min_active = _numeric(dq_contract.get("min_active_frame_count"))
    if min_active is not None:
        available = [
            _summary_number(summary, "active_frame_count")
            for summary in summaries
            if _summary_number(summary, "active_frame_count") is not None
        ]
        actual_max = max(available) if available else None
        checks.append(
            _check(
                "contract_dq_min_active_frame_count",
                actual_max is not None and actual_max >= min_active,
                {"actual_max": actual_max, "required_min": min_active},
            )
        )

    if dq_contract.get("require_dq_map_path"):
        checks.append(
            _check(
                "contract_dq_map_path_present",
                any(bool(record.get("dq_map_path")) for record in records),
                {"records_with_dq_map_path": sum(1 for record in records if record.get("dq_map_path"))},
            )
        )
    if dq_contract.get("require_existing_dq_map"):
        checks.append(
            _check(
                "contract_dq_map_exists",
                any(record.get("dq_map_exists") for record in records),
                {"records_with_existing_dq_map": sum(1 for record in records if record.get("dq_map_exists"))},
            )
        )
    if dq_contract.get("require_coverage_map_path"):
        checks.append(
            _check(
                "contract_dq_coverage_map_path_present",
                any(bool(record.get("coverage_map_path")) for record in records),
                {"records_with_coverage_map_path": sum(1 for record in records if record.get("coverage_map_path"))},
            )
        )

    for field in dq_contract.get("required_summary_fields") or []:
        field_text = str(field)
        checks.append(
            _check(
                f"contract_dq_summary_field:{field_text}",
                any(summary.get(field_text) is not None for summary in summaries),
                {"required": field_text},
            )
        )

    for flag in dq_contract.get("required_output_dq_flags") or []:
        flag_text = str(flag)
        values = [
            _summary_output_count(summary, flag_text)
            for summary in summaries
            if _summary_output_count(summary, flag_text) is not None
        ]
        checks.append(
            _check(
                f"contract_dq_output_flag:{flag_text}",
                bool(values),
                {"required": flag_text, "available_values": values},
            )
        )

    for flag in dq_contract.get("positive_output_dq_flags") or []:
        flag_text = str(flag)
        values = [
            _summary_output_count(summary, flag_text)
            for summary in summaries
            if _summary_output_count(summary, flag_text) is not None
        ]
        checks.append(
            _check(
                f"contract_dq_positive_output_flag:{flag_text}",
                any(value > 0 for value in values),
                {"required": flag_text, "available_values": values},
            )
        )

    if dq_contract.get("verify_dq_map_pixels"):
        verifications = [record.get("dq_map_pixel_verification") or {} for record in records]
        verified = [item for item in verifications if item.get("verified")]
        errors = [item for item in verifications if item and not item.get("verified")]
        checks.append(
            _check(
                "contract_dq_map_pixel_verification",
                bool(verified) and not errors,
                {
                    "verified_records": len(verified),
                    "error_records": len(errors),
                    "errors": [item.get("error") or item.get("status") for item in errors],
                },
            )
        )
        for flag in dq_contract.get("dq_map_summary_match_flags") or []:
            flag_text = str(flag).lower()
            matches = []
            for record in records:
                verification = record.get("dq_map_pixel_verification") or {}
                match = (verification.get("summary_matches") or {}).get(flag_text)
                if isinstance(match, dict):
                    matches.append(match)
            checks.append(
                _check(
                    f"contract_dq_map_summary_match:{flag_text}",
                    bool(matches) and all(bool(match.get("passed")) for match in matches),
                    {"matches": matches},
                )
            )

    if dq_contract.get("verify_output_count_maps"):
        count_map_verifications = [record.get("output_count_map_verification") or {} for record in records]
        coverage_items = [
            item.get("coverage") or {}
            for item in count_map_verifications
            if item.get("coverage")
        ]
        coverage_verified = [item for item in coverage_items if item.get("verified")]
        coverage_errors = [item for item in coverage_items if item.get("status") == "error"]
        checks.append(
            _check(
                "contract_coverage_map_pixel_verification",
                bool(coverage_verified) and not coverage_errors,
                {
                    "verified_records": len(coverage_verified),
                    "error_records": len(coverage_errors),
                    "errors": [item.get("error") for item in coverage_errors],
                },
            )
        )
        if dq_contract.get("coverage_map_finite_pixels_match_provenance"):
            matches = []
            for record in records:
                coverage = (record.get("output_count_map_verification") or {}).get("coverage") or {}
                result = coverage.get("result") or {}
                if not result:
                    continue
                expected = _provenance_nested_number(
                    record.get("source_provenance") or {},
                    "post_rejection_coverage",
                    "finite_pixels",
                )
                actual = result.get("finite_pixels")
                delta = None if actual is None or expected is None else int(actual) - int(expected)
                if actual is not None or expected is not None:
                    matches.append(
                        {
                            "actual": None if actual is None else int(actual),
                            "provenance": None if expected is None else int(expected),
                            "delta": delta,
                            "passed": delta == 0,
                        }
                    )
            checks.append(
                _check(
                    "contract_coverage_map_finite_pixels_match",
                    bool(matches) and all(bool(match.get("passed")) for match in matches),
                    {"matches": matches},
                )
            )
        if dq_contract.get("coverage_zero_pixels_match_no_data"):
            matches = []
            for record in records:
                coverage = (record.get("output_count_map_verification") or {}).get("coverage") or {}
                result = coverage.get("result") or {}
                if not result:
                    continue
                actual = result.get("zero_or_less_pixels")
                expected = _summary_output_count_default_zero(record.get("summary") or {}, "no_data")
                delta = None if actual is None else int(actual) - int(expected)
                if actual is not None:
                    matches.append(
                        {
                            "actual": int(actual),
                            "summary": expected,
                            "delta": delta,
                            "passed": delta == 0,
                        }
                    )
            checks.append(
                _check(
                    "contract_coverage_zero_pixels_match_no_data",
                    bool(matches) and all(bool(match.get("passed")) for match in matches),
                    {"matches": matches},
                )
            )

        allow_skipped_rejection = bool(dq_contract.get("allow_missing_rejection_maps_if_skipped"))
        for map_name, flag in [
            ("low_rejection", "low_rejected"),
            ("high_rejection", "high_rejected"),
        ]:
            map_items = [
                (record, (record.get("output_count_map_verification") or {}).get(map_name) or {})
                for record in records
            ]
            verified_items = [(record, item) for record, item in map_items if item.get("verified")]
            missing_items = [
                (record, item)
                for record, item in map_items
                if not item.get("verified") and item.get("status") in {"missing_path", "skipped"}
            ]
            skipped_ok = (
                allow_skipped_rejection
                and missing_items
                and all(_map_skipped_by_policy(record, map_name) for record, _item in missing_items)
            )
            checks.append(
                _check(
                    f"contract_{map_name}_map_available_or_skipped",
                    bool(verified_items) or bool(skipped_ok),
                    {
                        "verified_records": len(verified_items),
                        "missing_or_skipped_records": len(missing_items),
                        "allow_skipped_by_policy": allow_skipped_rejection,
                    },
                )
            )
            if verified_items:
                matches = []
                for record, item in verified_items:
                    result = item.get("result") or {}
                    actual = result.get("positive_pixels")
                    expected = _summary_output_count_default_zero(record.get("summary") or {}, flag)
                    delta = None if actual is None else int(actual) - int(expected)
                    matches.append(
                        {
                            "actual": None if actual is None else int(actual),
                            "summary": expected,
                            "delta": delta,
                            "passed": delta == 0,
                        }
                    )
                checks.append(
                    _check(
                        f"contract_{map_name}_map_positive_pixels_match:{flag}",
                        bool(matches) and all(bool(match.get("passed")) for match in matches),
                        {"matches": matches},
                    )
                )
        if dq_contract.get("rejection_map_sum_matches_provenance"):
            matches = []
            for record in records:
                verification = record.get("output_count_map_verification") or {}
                low = (verification.get("low_rejection") or {}).get("result") or {}
                high = (verification.get("high_rejection") or {}).get("result") or {}
                if not low or not high:
                    continue
                actual = int(low.get("rounded_sum") or 0) + int(high.get("rounded_sum") or 0)
                expected = _numeric((record.get("source_provenance") or {}).get("rejected_sample_count"))
                delta = None if expected is None else actual - int(round(expected))
                matches.append(
                    {
                        "actual": actual,
                        "provenance": None if expected is None else int(round(expected)),
                        "delta": delta,
                        "passed": delta == 0,
                    }
                )
            if matches or not allow_skipped_rejection:
                checks.append(
                    _check(
                        "contract_rejection_map_sum_matches_provenance",
                        bool(matches) and all(bool(match.get("passed")) for match in matches),
                        {"matches": matches},
                    )
                )

    for term in dq_contract.get("required_source_terms") or []:
        term_text = str(term)
        checks.append(
            _check(
                f"contract_dq_source_term:{term_text}",
                any(term_text in (summary.get("source_terms") or []) for summary in summaries),
                {"required": term_text},
            )
        )

    return checks


def build_benchmark_performance_diagnostics(
    contract: dict[str, Any],
    *,
    glass_run: str | Path,
) -> dict[str, Any] | None:
    baseline = contract.get("timing_baseline") or {}
    stage_baselines = baseline.get("stages_s") or {}
    if not isinstance(stage_baselines, dict) or not stage_baselines:
        return None

    warning_factor = _numeric(baseline.get("warning_regression_factor")) or 1.15
    current_timing = _load_resident_timing(glass_run)
    raw_cumulative_stages = baseline.get("cumulative_stages") or []
    cumulative_stages = {str(item) for item in raw_cumulative_stages}
    raw_stage_aliases = baseline.get("stage_aliases") or {}
    stage_aliases = raw_stage_aliases if isinstance(raw_stage_aliases, dict) else {}
    raw_stage_notes = baseline.get("stage_notes") or {}
    stage_notes = raw_stage_notes if isinstance(raw_stage_notes, dict) else {}
    items: list[dict[str, Any]] = []
    for stage, baseline_value in stage_baselines.items():
        stage_name = str(stage)
        actual_key = str(stage_aliases.get(stage_name, stage_name))
        baseline_s = _numeric(baseline_value)
        actual_s = _numeric(current_timing.get(actual_key))
        if baseline_s is None:
            continue
        factor = actual_s / baseline_s if actual_s is not None and baseline_s > 0.0 else None
        delta_s = actual_s - baseline_s if actual_s is not None else None
        is_cumulative = stage_name in cumulative_stages or actual_key in cumulative_stages
        status = "missing_current"
        if factor is not None:
            if is_cumulative:
                status = "informational_cumulative"
            else:
                status = "regressed" if factor > warning_factor else "ok"
        items.append(
            {
                "stage": stage_name,
                "actual_key": actual_key,
                "baseline_s": baseline_s,
                "actual_s": actual_s,
                "delta_s": delta_s,
                "factor": factor,
                "status": status,
                "timing_kind": "worker_cumulative" if is_cumulative else "wall_or_stage",
                "note": str(stage_notes.get(stage_name, "")),
            }
        )

    items.sort(
        key=lambda item: (
            item["factor"] is not None,
            float(item["factor"] or 0.0),
            float(item["delta_s"] or 0.0),
        ),
        reverse=True,
    )
    regressed = [item for item in items if item["status"] == "regressed"]
    missing = [item for item in items if item["status"] == "missing_current"]
    if regressed:
        status = "regressed"
    elif missing:
        status = "incomplete"
    else:
        status = "ok"
    return {
        "schema_version": 1,
        "status": status,
        "warning_regression_factor": warning_factor,
        "items": items,
        "regressed_count": len(regressed),
        "missing_count": len(missing),
        "worst_regression": regressed[0] if regressed else (items[0] if items else None),
    }


def build_benchmark_contract_checks(
    contract: dict[str, Any],
    *,
    glass_run: str | Path,
    speedup_summary: dict[str, Any],
    compare_payload: dict[str, Any],
    frame_type_counts: dict[str, int],
    dq_provenance_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    dataset = contract.get("dataset_requirements") or {}
    for frame_type in ("light", "bias", "dark", "flat"):
        required = dataset.get(frame_type)
        if required is None:
            continue
        actual = int(frame_type_counts.get(frame_type, 0))
        checks.append(
            _check(
                f"contract_minimum_{frame_type}_frames",
                actual >= int(required),
                {"actual": actual, "required": int(required)},
            )
        )

    active_required = dataset.get("active_light_frames")
    if active_required is not None:
        actual_active = int((speedup_summary.get("glass") or {}).get("weighted_frame_count") or 0)
        checks.append(
            _check(
                "contract_minimum_active_light_frames",
                actual_active >= int(active_required),
                {"actual": actual_active, "required": int(active_required)},
            )
        )

    runtime = contract.get("runtime") or {}
    glass_elapsed = _numeric((speedup_summary.get("glass") or {}).get("elapsed_s"))
    baseline_elapsed = _numeric(runtime.get("release_baseline_elapsed_s"))
    max_factor = _numeric(runtime.get("max_runtime_regression_factor"))
    if glass_elapsed is not None and baseline_elapsed is not None and max_factor is not None:
        required_max = baseline_elapsed * max_factor
        checks.append(
            _check(
                "contract_max_runtime_vs_release_baseline",
                glass_elapsed <= required_max,
                {
                    "actual_s": glass_elapsed,
                    "release_baseline_s": baseline_elapsed,
                    "max_regression_factor": max_factor,
                    "required_max_s": required_max,
                },
            )
        )

    min_speedup = _numeric(runtime.get("min_speedup_vs_reference"))
    speedup = _numeric(speedup_summary.get("speedup_vs_wbpp"))
    if min_speedup is not None:
        checks.append(
            _check(
                "contract_minimum_speedup_vs_reference",
                speedup is not None and speedup >= min_speedup,
                {"actual": speedup, "required": min_speedup},
            )
        )

    command_text = _read_run_command(glass_run)
    for token in contract.get("required_command_tokens") or []:
        token_text = str(token)
        checks.append(
            _check(
                f"contract_required_command_token:{token_text}",
                command_text is not None and token_text in command_text,
                {"token": token_text, "run_command_present": command_text is not None},
            )
        )

    compare_contract = contract.get("comparison") or {}
    transform = compare_payload.get("candidate_transform") or {}
    region = compare_payload.get("comparison_region") or {}
    abs_tol = float(compare_contract.get("numeric_abs_tolerance", 1.0e-12))
    rel_tol = float(compare_contract.get("numeric_rel_tolerance", 1.0e-9))
    for key, actual_key in [
        ("required_scale", "scale"),
        ("required_offset", "offset"),
    ]:
        if key not in compare_contract:
            continue
        expected = compare_contract[key]
        actual = transform.get(actual_key)
        checks.append(
            _check(
                f"contract_compare_{actual_key}",
                _close_enough(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol),
                {"actual": actual, "required": expected, "abs_tol": abs_tol, "rel_tol": rel_tol},
            )
        )
    if "required_min_coverage" in compare_contract:
        actual_min_coverage = _numeric(region.get("min_coverage"))
        expected_min_coverage = _numeric(compare_contract.get("required_min_coverage"))
        checks.append(
            _check(
                "contract_compare_min_coverage",
                actual_min_coverage == expected_min_coverage,
                {"actual": actual_min_coverage, "required": expected_min_coverage},
            )
        )
    if "max_rms_diff" in compare_contract:
        rms = _numeric(compare_payload.get("rms_diff"))
        required = _numeric(compare_contract.get("max_rms_diff"))
        checks.append(
            _check(
                "contract_max_rms_diff",
                rms is not None and required is not None and rms <= required,
                {"actual": rms, "required_max": required},
            )
        )
    if "max_abs_diff_p99" in compare_contract:
        p99 = _numeric(compare_payload.get("abs_diff_p99"))
        required = _numeric(compare_contract.get("max_abs_diff_p99"))
        checks.append(
            _check(
                "contract_max_abs_diff_p99",
                p99 is not None and required is not None and p99 <= required,
                {"actual": p99, "required_max": required},
            )
        )
    if "min_coverage_fraction" in compare_contract:
        coverage_fraction = _numeric(region.get("coverage_fraction"))
        required = _numeric(compare_contract.get("min_coverage_fraction"))
        checks.append(
            _check(
                "contract_min_coverage_fraction",
                coverage_fraction is not None and required is not None and coverage_fraction >= required,
                {"actual": coverage_fraction, "required": required},
            )
        )
    dq_contract = contract.get("dq_provenance") or {}
    if isinstance(dq_contract, dict) and dq_contract:
        records = (
            dq_provenance_records
            if dq_provenance_records is not None
            else collect_dq_provenance_records(glass_run, dq_contract=dq_contract)
        )
        checks.extend(
            _build_dq_provenance_contract_checks(
                dq_contract,
                records=records,
            )
        )
    return checks
