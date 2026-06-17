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


def _load_run_timing(glass_run: str | Path) -> dict[str, Any]:
    path = Path(glass_run) / "run_timing.json"
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    return payload if isinstance(payload, dict) else {}


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


def _load_resident_io_pipelines(glass_run: str | Path) -> list[dict[str, Any]]:
    path = Path(glass_run) / "resident_artifacts.json"
    if not path.exists():
        return []
    payload = _read_json_lenient(path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return []
    pipelines: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        pipeline = artifact.get("resident_io_pipeline")
        if isinstance(pipeline, dict):
            pipelines.append(pipeline)
    return pipelines


def collect_resident_registration_fastpath_record(glass_run: str | Path) -> dict[str, Any]:
    run_root = Path(glass_run)
    resident_path = run_root / "resident_artifacts.json"
    resident = _load_json_object_if_present(resident_path)
    artifacts = resident.get("artifacts") if isinstance(resident.get("artifacts"), list) else []
    artifact = artifacts[0] if artifacts and isinstance(artifacts[0], dict) else {}
    registration = (
        artifact.get("resident_registration")
        if isinstance(artifact.get("resident_registration"), dict)
        else {}
    )
    io_pipeline = (
        artifact.get("resident_io_pipeline")
        if isinstance(artifact.get("resident_io_pipeline"), dict)
        else {}
    )
    fine_timing = artifact.get("fine_timing") if isinstance(artifact.get("fine_timing"), dict) else {}
    components = (
        fine_timing.get("registration_component_seconds")
        if isinstance(fine_timing.get("registration_component_seconds"), dict)
        else {}
    )
    return {
        "schema_version": 1,
        "path": str(resident_path),
        "exists": resident_path.exists(),
        "artifact_count": len(artifacts),
        "artifact_index": 0 if artifact else None,
        "available": bool(registration),
        "resident_registration": registration,
        "resident_io_pipeline": io_pipeline,
        "artifact": {
            "resident_warp_scratch_bytes": artifact.get("resident_warp_scratch_bytes"),
            "resident_warp_copy_mode": artifact.get("resident_warp_copy_mode"),
        },
        "registration_component_seconds": {
            str(key): value for key, value in components.items()
        },
    }


def _fastpath_value(record: dict[str, Any], field_path: str) -> Any:
    if "." not in field_path:
        for section in (
            "resident_registration",
            "resident_io_pipeline",
            "artifact",
            "registration_component_seconds",
        ):
            section_payload = record.get(section)
            if isinstance(section_payload, dict) and field_path in section_payload:
                return section_payload.get(field_path)
        return None
    value: Any = record
    for part in field_path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _pipeline_expected_value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        actual_number = _numeric(actual)
        return actual_number is not None and actual_number == float(expected)
    return str(actual) == str(expected)


def _resident_pipeline_expectation_match(
    pipelines: list[dict[str, Any]],
    expectations: dict[str, Any],
) -> dict[str, Any] | None:
    for index, pipeline in enumerate(pipelines):
        observed: dict[str, Any] = {}
        missing: list[str] = []
        mismatched: dict[str, dict[str, Any]] = {}
        for key, expected in expectations.items():
            if key not in pipeline:
                missing.append(key)
                continue
            actual = pipeline.get(key)
            observed[key] = actual
            if not _pipeline_expected_value_matches(actual, expected):
                mismatched[key] = {"actual": actual, "required": expected}
        if not missing and not mismatched:
            return {
                "artifact": "resident_artifacts.json",
                "artifact_index": index,
                "resident_io_pipeline": observed,
            }
    return None


def _resident_runtime_preset_expectations(preset: str) -> dict[str, Any] | None:
    if preset == "throughput-v1":
        return {
            "h2d_mode": "pinned_ring",
            "prefetch_frames": 12,
            "prefetch_workers": 7,
            "calibration_batch_requested_frames": 8,
            "calibration_batch_requested_streams": 4,
            "calibration_wave_requested_frames": 2,
            "calibration_release_mode_requested": "callback_queue",
            "calibration_release_mode_effective": "callback_queue",
        }
    if preset == "manual":
        return {
            "h2d_mode": "pageable",
            "prefetch_frames": 0,
            "prefetch_workers": 1,
            "calibration_release_mode_requested": "sync",
            "calibration_release_mode_effective": "sync",
        }
    return None


def _resident_pipeline_match_for_command_token(
    token_text: str,
    pipelines: list[dict[str, Any]],
) -> dict[str, Any] | None:
    parts = token_text.split()
    if len(parts) != 2 or not pipelines:
        return None
    flag, value = parts
    if flag == "--resident-runtime-preset":
        expectations = _resident_runtime_preset_expectations(value)
        if expectations is None:
            return None
        match = _resident_pipeline_expectation_match(pipelines, expectations)
        if match is not None:
            match["token"] = token_text
            match["preset"] = value
        return match
    field_by_flag = {
        "--resident-h2d-mode": "h2d_mode",
        "--resident-prefetch-frames": "prefetch_frames",
        "--resident-prefetch-workers": "prefetch_workers",
        "--resident-calibration-batch-frames": "calibration_batch_requested_frames",
        "--resident-calibration-batch-streams": "calibration_batch_requested_streams",
        "--resident-calibration-wave-frames": "calibration_wave_requested_frames",
        "--resident-calibration-release-mode": "calibration_release_mode_requested",
    }
    field = field_by_flag.get(flag)
    if field is None:
        return None
    expected: Any = value
    if field in {
        "prefetch_frames",
        "prefetch_workers",
        "calibration_batch_requested_frames",
        "calibration_batch_requested_streams",
        "calibration_wave_requested_frames",
    }:
        try:
            expected = int(value)
        except ValueError:
            return None
    match = _resident_pipeline_expectation_match(pipelines, {field: expected})
    if match is not None:
        match["token"] = token_text
    return match


def _timing_value(run_timing: dict[str, Any], *keys: str) -> Any:
    current: Any = run_timing
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _route_match_for_command_token(
    token_text: str,
    *,
    run_timing: dict[str, Any],
    resident_io_pipelines: list[dict[str, Any]],
    resident_registration_fastpath: dict[str, Any] | None,
) -> dict[str, Any] | None:
    pipeline_match = _resident_pipeline_match_for_command_token(token_text, resident_io_pipelines)
    if pipeline_match is not None:
        pipeline_match["source"] = "resident_io_pipeline"
        return pipeline_match

    parts = token_text.split()
    if len(parts) != 2:
        return None
    flag, expected = parts
    resolution = (
        run_timing.get("execution_default_resolution")
        if isinstance(run_timing.get("execution_default_resolution"), dict)
        else {}
    )
    if flag == "--memory-mode":
        actual = run_timing.get("memory_mode") or resolution.get("effective_memory_mode")
        if str(actual) == expected:
            return {
                "token": token_text,
                "source": "run_timing",
                "field": "memory_mode",
                "actual": actual,
                "requested": run_timing.get("memory_mode_requested")
                or resolution.get("requested_memory_mode"),
                "reason": resolution.get("reason"),
            }
        return None
    if flag == "--backend":
        actual = run_timing.get("backend") or resolution.get("effective_backend")
        if str(actual) == expected:
            return {
                "token": token_text,
                "source": "run_timing",
                "field": "backend",
                "actual": actual,
                "requested": run_timing.get("backend_requested") or resolution.get("requested_backend"),
                "reason": resolution.get("reason"),
            }
        return None
    if flag == "--resident-runtime-preset":
        actual = (
            run_timing.get("resident_runtime_preset")
            or _timing_value(run_timing, "resident_runtime_preset_effective", "preset")
            or resolution.get("default_runtime_preset")
        )
        if str(actual) == expected:
            return {
                "token": token_text,
                "source": "run_timing",
                "field": "resident_runtime_preset",
                "actual": actual,
                "reason": resolution.get("reason"),
            }
        return None
    if flag == "--resident-registration":
        registration = (
            resident_registration_fastpath.get("resident_registration")
            if isinstance(resident_registration_fastpath, dict)
            and isinstance(resident_registration_fastpath.get("resident_registration"), dict)
            else {}
        )
        actual = registration.get("mode")
        if str(actual) == expected:
            return {
                "token": token_text,
                "source": "resident_artifacts",
                "field": "resident_registration.mode",
                "actual": actual,
                "artifact": resident_registration_fastpath.get("path")
                if isinstance(resident_registration_fastpath, dict)
                else None,
            }
        return None
    return None


def _build_resident_registration_fastpath_contract_checks(
    requirements: dict[str, Any],
    *,
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if requirements.get("required"):
        checks.append(
            _check(
                "contract_resident_registration_fastpath_present",
                bool(record.get("exists")) and bool(record.get("available")),
                {
                    "path": record.get("path"),
                    "exists": bool(record.get("exists")),
                    "available": bool(record.get("available")),
                    "artifact_count": record.get("artifact_count"),
                },
            )
        )

    required_values = requirements.get("required_values") or {}
    if isinstance(required_values, dict):
        for field_path, expected in required_values.items():
            field_text = str(field_path)
            actual = _fastpath_value(record, field_text)
            checks.append(
                _check(
                    f"contract_resident_registration_fastpath_value:{field_text}",
                    _pipeline_expected_value_matches(actual, expected),
                    {"field": field_text, "actual": actual, "required": expected},
                )
            )

    for field_path in requirements.get("required_true_fields") or []:
        field_text = str(field_path)
        actual = _fastpath_value(record, field_text)
        checks.append(
            _check(
                f"contract_resident_registration_fastpath_true:{field_text}",
                actual is True,
                {"field": field_text, "actual": actual, "required": True},
            )
        )

    for field_path in requirements.get("required_positive_fields") or []:
        field_text = str(field_path)
        actual = _numeric(_fastpath_value(record, field_text))
        checks.append(
            _check(
                f"contract_resident_registration_fastpath_positive:{field_text}",
                actual is not None and actual > 0.0,
                {"field": field_text, "actual": actual, "required": "> 0"},
            )
        )

    required_min_fields = requirements.get("required_min_fields") or {}
    if isinstance(required_min_fields, dict):
        for field_path, minimum in required_min_fields.items():
            field_text = str(field_path)
            actual = _numeric(_fastpath_value(record, field_text))
            required = _numeric(minimum)
            checks.append(
                _check(
                    f"contract_resident_registration_fastpath_min:{field_text}",
                    actual is not None and required is not None and actual >= required,
                    {"field": field_text, "actual": actual, "required_min": required},
                )
            )

    for component in requirements.get("required_component_seconds") or []:
        component_text = str(component)
        actual = _numeric(
            _fastpath_value(record, f"registration_component_seconds.{component_text}")
        )
        checks.append(
            _check(
                f"contract_resident_registration_fastpath_component:{component_text}",
                actual is not None and actual >= 0.0,
                {"component": component_text, "actual_s": actual},
            )
        )

    return checks


def _load_json_object_if_present(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = _read_json_lenient(path)
    return payload if isinstance(payload, dict) else {}


def _weight_count_summary(weights: Any) -> dict[str, int]:
    if not isinstance(weights, dict):
        return {"total": 0, "positive": 0, "zero": 0, "invalid": 0}
    positive = 0
    zero = 0
    invalid = 0
    for value in weights.values():
        try:
            weight = float(value)
        except (TypeError, ValueError):
            invalid += 1
            continue
        if weight > 0.0:
            positive += 1
        else:
            zero += 1
    return {
        "total": len(weights),
        "positive": positive,
        "zero": zero,
        "invalid": invalid,
    }


def _registration_rows(registration: dict[str, Any]) -> list[dict[str, Any]]:
    rows = registration.get("registration_results")
    if rows is None:
        rows = registration.get("results")
    return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []


def _registration_count_summary(registration: dict[str, Any]) -> dict[str, Any]:
    rows = _registration_rows(registration)
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "total": len(rows),
        "accepted": sum(status_counts.get(status, 0) for status in ("ok", "reference")),
        "zero_weight_statuses": sum(
            status_counts.get(status, 0) for status in ("excluded", "failed", "quality_rejected")
        ),
        "status_counts": status_counts,
    }


def collect_frame_accounting_record(glass_run: str | Path) -> dict[str, Any]:
    run_root = Path(glass_run)
    accounting_path = run_root / "frame_accounting.json"
    accounting = _load_json_object_if_present(accounting_path)
    integration = _load_json_object_if_present(run_root / "integration_results.json")
    registration = _load_json_object_if_present(run_root / "registration_results.json")
    frames = accounting.get("frames") if isinstance(accounting.get("frames"), list) else []
    calculated_final_counts: dict[str, int] = {}
    for row in frames:
        if not isinstance(row, dict):
            continue
        status = str(row.get("final_status") or "unknown")
        calculated_final_counts[status] = calculated_final_counts.get(status, 0) + 1
    return {
        "schema_version": 1,
        "path": str(accounting_path),
        "exists": accounting_path.exists(),
        "summary": accounting.get("summary") if isinstance(accounting.get("summary"), dict) else {},
        "exception_summary": accounting.get("exception_summary")
        if isinstance(accounting.get("exception_summary"), dict)
        else {},
        "exception_frames": accounting.get("exception_frames")
        if isinstance(accounting.get("exception_frames"), list)
        else [],
        "frame_count": len(frames),
        "calculated_final_status_counts": calculated_final_counts,
        "integration_source_stage": accounting.get("integration_source_stage"),
        "sources": accounting.get("sources") if isinstance(accounting.get("sources"), dict) else {},
        "integration_weight_counts": _weight_count_summary(integration.get("frame_weights")),
        "registration_counts": _registration_count_summary(registration),
    }


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
    master_path = payload.get("master_path")
    weight_map_path = payload.get("weight_map_path")
    coverage_map_path = payload.get("coverage_map_path")
    low_rejection_map_path = payload.get("low_rejection_map_path")
    high_rejection_map_path = payload.get("high_rejection_map_path")
    return {
        "source_file": source_file,
        "source_kind": source_kind,
        "index": index,
        "normalized_from_legacy": normalized_from_legacy,
        "master_path": master_path,
        "master_exists": _path_exists_maybe_relative(master_path, run_root),
        "weight_map_path": weight_map_path,
        "weight_map_exists": _path_exists_maybe_relative(weight_map_path, run_root),
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
            tolerance = int(dq_contract.get("rejection_map_sum_tolerance_samples") or 0)
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
                        "passed": delta is not None and abs(delta) <= tolerance,
                    }
                )
            if matches or not allow_skipped_rejection:
                checks.append(
                    _check(
                        "contract_rejection_map_sum_matches_provenance",
                        bool(matches) and all(bool(match.get("passed")) for match in matches),
                        {"matches": matches, "tolerance_samples": tolerance},
                    )
                )

    required_resident_paths = [str(item) for item in dq_contract.get("required_resident_artifact_map_paths") or []]
    if required_resident_paths:
        resident_records = [record for record in records if record.get("source_kind") == "resident_artifact"]
        map_path_keys = {
            "master": ("master_path", "master_exists"),
            "weight": ("weight_map_path", "weight_map_exists"),
            "coverage": ("coverage_map_path", "coverage_map_exists"),
            "dq": ("dq_map_path", "dq_map_exists"),
            "low_rejection": ("low_rejection_map_path", "low_rejection_map_exists"),
            "high_rejection": ("high_rejection_map_path", "high_rejection_map_exists"),
        }
        for map_name in required_resident_paths:
            path_key, exists_key = map_path_keys.get(map_name, (f"{map_name}_path", f"{map_name}_exists"))
            matches = [
                {
                    "path": record.get(path_key),
                    "exists": bool(record.get(exists_key)),
                }
                for record in resident_records
            ]
            checks.append(
                _check(
                    f"contract_resident_artifact_map_path:{map_name}",
                    bool(matches) and all(bool(match.get("path")) and bool(match.get("exists")) for match in matches),
                    {"resident_records": len(resident_records), "matches": matches},
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


def _frame_accounting_count(
    record: dict[str, Any],
    key: str,
) -> int | None:
    value = (record.get("summary") or {}).get(key)
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _build_frame_accounting_contract_checks(
    frame_contract: dict[str, Any],
    *,
    record: dict[str, Any],
    speedup_summary: dict[str, Any],
    dq_provenance_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if frame_contract.get("required"):
        checks.append(
            _check(
                "contract_frame_accounting_present",
                bool(record.get("exists")),
                {"path": record.get("path"), "exists": bool(record.get("exists"))},
            )
        )

    summary = record.get("summary") or {}
    if not isinstance(summary, dict):
        summary = {}
    required_counts = {
        "input_light_frames": "required_input_light_frames",
        "integrated_frames": "required_integrated_frames",
        "zero_weight_frames": "required_zero_weight_frames",
        "quality_rejected_frames": "required_quality_rejected_frames",
        "registration_accepted_frames": "required_registration_accepted_frames",
    }
    for summary_key, contract_key in required_counts.items():
        if contract_key not in frame_contract:
            continue
        actual = _frame_accounting_count(record, summary_key)
        required = int(frame_contract[contract_key])
        checks.append(
            _check(
                f"contract_frame_accounting_{summary_key}",
                actual == required,
                {"actual": actual, "required": required},
            )
        )

    min_integrated = frame_contract.get("min_integrated_frames")
    if min_integrated is not None:
        actual = _frame_accounting_count(record, "integrated_frames")
        checks.append(
            _check(
                "contract_frame_accounting_min_integrated_frames",
                actual is not None and actual >= int(min_integrated),
                {"actual": actual, "required_min": int(min_integrated)},
            )
        )

    expected_source_stage = frame_contract.get("required_integration_source_stage")
    if expected_source_stage is not None:
        checks.append(
            _check(
                "contract_frame_accounting_integration_source_stage",
                record.get("integration_source_stage") == str(expected_source_stage),
                {"actual": record.get("integration_source_stage"), "required": str(expected_source_stage)},
            )
        )

    required_final_counts = frame_contract.get("required_final_status_counts") or {}
    if isinstance(required_final_counts, dict):
        final_counts = summary.get("final_status_counts") if isinstance(summary.get("final_status_counts"), dict) else {}
        calculated_counts = record.get("calculated_final_status_counts") or {}
        for status, required in required_final_counts.items():
            status_text = str(status)
            actual = final_counts.get(status_text)
            calculated = calculated_counts.get(status_text)
            required_int = int(required)
            checks.append(
                _check(
                    f"contract_frame_accounting_final_status:{status_text}",
                    actual == required_int and calculated == required_int,
                    {
                        "actual": actual,
                        "calculated_from_rows": calculated,
                        "required": required_int,
                    },
                )
            )

    if frame_contract.get("match_integration_frame_weights"):
        weights = record.get("integration_weight_counts") or {}
        matches = [
            {
                "field": "input_light_frames",
                "accounting": _frame_accounting_count(record, "input_light_frames"),
                "weights": weights.get("total"),
            },
            {
                "field": "integrated_frames",
                "accounting": _frame_accounting_count(record, "integrated_frames"),
                "weights": weights.get("positive"),
            },
            {
                "field": "zero_weight_frames",
                "accounting": _frame_accounting_count(record, "zero_weight_frames"),
                "weights": weights.get("zero"),
            },
        ]
        checks.append(
            _check(
                "contract_frame_accounting_matches_integration_weights",
                bool(matches) and all(item["accounting"] == item["weights"] for item in matches),
                {"matches": matches, "invalid_weights": weights.get("invalid")},
            )
        )

    if frame_contract.get("match_speedup_summary"):
        glass = speedup_summary.get("glass") or {}
        matches = [
            {
                "field": "integrated_frames",
                "accounting": _frame_accounting_count(record, "integrated_frames"),
                "speedup_summary": glass.get("weighted_frame_count"),
            },
            {
                "field": "zero_weight_frames",
                "accounting": _frame_accounting_count(record, "zero_weight_frames"),
                "speedup_summary": glass.get("zero_weight_frame_count"),
            },
        ]
        checks.append(
            _check(
                "contract_frame_accounting_matches_speedup_summary",
                bool(matches) and all(item["accounting"] == item["speedup_summary"] for item in matches),
                {"matches": matches},
            )
        )

    if frame_contract.get("match_dq_active_frame_count"):
        active_counts = [
            _summary_number(record_item.get("summary") or {}, "active_frame_count")
            for record_item in dq_provenance_records
        ]
        active_counts = [item for item in active_counts if item is not None]
        actual = _frame_accounting_count(record, "integrated_frames")
        checks.append(
            _check(
                "contract_frame_accounting_matches_dq_active_frames",
                bool(active_counts) and all(int(item) == actual for item in active_counts),
                {"accounting_integrated_frames": actual, "dq_active_frame_counts": active_counts},
            )
        )

    if frame_contract.get("match_registration_accepted_frames"):
        registration = record.get("registration_counts") or {}
        actual = _frame_accounting_count(record, "registration_accepted_frames")
        checks.append(
            _check(
                "contract_frame_accounting_matches_registration",
                actual == registration.get("accepted"),
                {
                    "accounting_registration_accepted_frames": actual,
                    "registration_accepted_frames": registration.get("accepted"),
                    "registration_status_counts": registration.get("status_counts"),
                },
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


def _max_drift_metric(output_numerical_drifts: list[dict[str, Any]], metric: str) -> tuple[float | None, int]:
    values: list[float] = []
    missing = 0
    for item in output_numerical_drifts:
        drift = item.get("drift") if isinstance(item.get("drift"), dict) else {}
        value = _numeric(drift.get(metric))
        if value is None:
            missing += 1
            continue
        values.append(value)
    return (max(values) if values else None, missing)


def _build_resident_determinism_contract_checks(
    resident_contract: dict[str, Any],
    *,
    resident_determinism: dict[str, Any] | None,
    output_numerical_drifts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    present = bool(resident_determinism)
    if resident_contract.get("required"):
        checks.append(
            _check(
                "contract_resident_determinism_present",
                present,
                {"required": True, "present": present},
            )
        )

    if resident_contract.get("require_strict_passed"):
        strict_passed = (resident_determinism or {}).get("strict_passed")
        checks.append(
            _check(
                "contract_resident_determinism_strict_passed",
                strict_passed is True,
                {"actual": strict_passed, "required": True},
            )
        )

    drift_count = len(output_numerical_drifts)
    max_count = resident_contract.get("max_output_numerical_drift_count")
    if max_count is not None:
        required = int(max_count)
        checks.append(
            _check(
                "contract_output_numerical_drift_count",
                drift_count <= required,
                {"actual": drift_count, "required_max": required},
            )
        )

    metric_checks = [
        (
            "max_output_numerical_drift_relative_rms",
            "relative_rms_to_baseline_std",
            "contract_output_numerical_drift_relative_rms",
        ),
        ("max_output_numerical_drift_rms", "rms", "contract_output_numerical_drift_rms"),
        ("max_output_numerical_drift_mean_abs", "mean_abs", "contract_output_numerical_drift_mean_abs"),
    ]
    for contract_key, metric_key, check_name in metric_checks:
        if contract_key not in resident_contract:
            continue
        actual, missing_count = _max_drift_metric(output_numerical_drifts, metric_key)
        required = _numeric(resident_contract.get(contract_key))
        no_rows = drift_count == 0
        passed = required is not None and (no_rows or (actual is not None and missing_count == 0 and actual <= required))
        checks.append(
            _check(
                check_name,
                passed,
                {
                    "actual_max": 0.0 if no_rows else actual,
                    "required_max": required,
                    "metric": metric_key,
                    "drift_count": drift_count,
                    "missing_metric_count": missing_count,
                },
            )
        )

    return checks


def _build_pipeline_contract_checks(
    pipeline_contract_requirements: dict[str, Any],
    *,
    pipeline_contract: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    present = bool(pipeline_contract)
    contract = pipeline_contract or {}
    failed_checks = contract.get("failed_checks") if isinstance(contract.get("failed_checks"), list) else []
    check_names = contract.get("check_names") if isinstance(contract.get("check_names"), list) else []

    if pipeline_contract_requirements.get("required"):
        checks.append(
            _check(
                "contract_pipeline_contract_present",
                present,
                {
                    "required": True,
                    "present": present,
                    "path": contract.get("path"),
                },
            )
        )

    required_audit_type = pipeline_contract_requirements.get("required_audit_type")
    if required_audit_type is not None:
        checks.append(
            _check(
                "contract_pipeline_contract_audit_type",
                present and contract.get("audit_type") == str(required_audit_type),
                {
                    "actual": contract.get("audit_type"),
                    "required": str(required_audit_type),
                },
            )
        )

    if pipeline_contract_requirements.get("require_passed"):
        checks.append(
            _check(
                "contract_pipeline_contract_passed",
                contract.get("passed") is True,
                {
                    "actual": contract.get("passed"),
                    "status": contract.get("status"),
                    "failed_checks": failed_checks,
                },
            )
        )

    min_check_count = pipeline_contract_requirements.get("min_check_count")
    if min_check_count is not None:
        required = int(min_check_count)
        actual = int(contract.get("check_count") or 0)
        checks.append(
            _check(
                "contract_pipeline_contract_min_check_count",
                actual >= required,
                {"actual": actual, "required_min": required},
            )
        )

    for required_name in pipeline_contract_requirements.get("required_check_names") or []:
        name = str(required_name)
        checks.append(
            _check(
                f"contract_pipeline_contract_check:{name}",
                name in {str(item) for item in check_names},
                {"required": name, "available": [str(item) for item in check_names]},
            )
        )

    if pipeline_contract_requirements.get("allow_failed_checks") is False:
        checks.append(
            _check(
                "contract_pipeline_contract_no_failed_checks",
                present and not failed_checks,
                {"failed_checks": failed_checks},
            )
        )

    return checks


def _build_stack_engine_default_promotion_contract_checks(
    requirements: dict[str, Any],
    *,
    stack_engine_contract: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    present = bool(stack_engine_contract)
    contract = stack_engine_contract or {}
    failed_checks = contract.get("failed_checks") if isinstance(contract.get("failed_checks"), list) else []
    check_names = contract.get("check_names") if isinstance(contract.get("check_names"), list) else []
    promotion = contract.get("default_promotion") if isinstance(contract.get("default_promotion"), dict) else {}
    adoption = contract.get("adoption") if isinstance(contract.get("adoption"), dict) else {}

    if requirements.get("required"):
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_present",
                present,
                {
                    "required": True,
                    "present": present,
                    "path": contract.get("path"),
                },
            )
        )

    required_audit_type = requirements.get("required_audit_type")
    if required_audit_type is not None:
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_audit_type",
                present and contract.get("audit_type") == str(required_audit_type),
                {
                    "actual": contract.get("audit_type"),
                    "required": str(required_audit_type),
                },
            )
        )

    if requirements.get("require_passed"):
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_contract_passed",
                contract.get("passed") is True,
                {
                    "actual": contract.get("passed"),
                    "status": contract.get("status"),
                    "failed_checks": failed_checks,
                },
            )
        )

    if requirements.get("require_default_promotion_ready"):
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_ready",
                promotion.get("ready") is True,
                {
                    "actual": promotion.get("ready"),
                    "status": promotion.get("status"),
                    "blockers": promotion.get("blockers") or [],
                },
            )
        )

    required_scope = requirements.get("required_scope")
    if required_scope is not None:
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_scope",
                promotion.get("actual_scope") == str(required_scope),
                {
                    "actual": promotion.get("actual_scope"),
                    "required": str(required_scope),
                },
            )
        )

    required_recommendation = requirements.get("required_recommendation")
    if required_recommendation is not None:
        actual = promotion.get("recommendation") or adoption.get("recommendation")
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_recommendation",
                actual == str(required_recommendation),
                {
                    "actual": actual,
                    "required": str(required_recommendation),
                },
            )
        )

    max_gap_count = requirements.get("max_default_gap_count")
    if max_gap_count is not None:
        actual = int(promotion.get("phase2_stack_engine_default_gap_count") or 0)
        required = int(max_gap_count)
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_gap_count",
                actual <= required,
                {"actual": actual, "required_max": required},
            )
        )

    max_blocker_count = requirements.get("max_blocker_count")
    if max_blocker_count is not None:
        actual = int(promotion.get("blocker_count") or 0)
        required = int(max_blocker_count)
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_blocker_count",
                actual <= required,
                {"actual": actual, "required_max": required},
            )
        )

    for required_name in requirements.get("required_check_names") or []:
        name = str(required_name)
        checks.append(
            _check(
                f"contract_stack_engine_default_promotion_check:{name}",
                name in {str(item) for item in check_names},
                {"required": name, "available": [str(item) for item in check_names]},
            )
        )

    if requirements.get("allow_failed_checks") is False:
        checks.append(
            _check(
                "contract_stack_engine_default_promotion_no_failed_checks",
                present and not failed_checks,
                {"failed_checks": failed_checks},
            )
        )

    return checks


def build_benchmark_contract_checks(
    contract: dict[str, Any],
    *,
    glass_run: str | Path,
    speedup_summary: dict[str, Any],
    compare_payload: dict[str, Any],
    frame_type_counts: dict[str, int],
    dq_provenance_records: list[dict[str, Any]] | None = None,
    frame_accounting_record: dict[str, Any] | None = None,
    resident_determinism: dict[str, Any] | None = None,
    resident_registration_fastpath: dict[str, Any] | None = None,
    output_numerical_drifts: list[dict[str, Any]] | None = None,
    pipeline_contract: dict[str, Any] | None = None,
    stack_engine_contract: dict[str, Any] | None = None,
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
    run_timing = _load_run_timing(glass_run)
    resident_io_pipelines = _load_resident_io_pipelines(glass_run)
    for token in contract.get("required_command_tokens") or []:
        token_text = str(token)
        command_match = command_text is not None and token_text in command_text
        artifact_match = _route_match_for_command_token(
            token_text,
            run_timing=run_timing,
            resident_io_pipelines=resident_io_pipelines,
            resident_registration_fastpath=resident_registration_fastpath,
        )
        checks.append(
            _check(
                f"contract_required_command_token:{token_text}",
                command_match or artifact_match is not None,
                {
                    "token": token_text,
                    "command_match": command_match,
                    "artifact_match": artifact_match,
                    "run_command_present": command_text is not None,
                    "run_timing_present": bool(run_timing),
                },
            )
        )
    for index, group in enumerate(contract.get("required_command_token_groups") or []):
        if isinstance(group, dict):
            tokens = [str(token) for token in group.get("any_of") or []]
            group_name = str(group.get("name") or f"group_{index}")
        elif isinstance(group, str):
            tokens = [group]
            group_name = f"group_{index}"
        else:
            tokens = [str(token) for token in group]
            group_name = f"group_{index}"
        matched = [token for token in tokens if command_text is not None and token in command_text]
        artifact_matches = []
        for token in tokens:
            match = _route_match_for_command_token(
                token,
                run_timing=run_timing,
                resident_io_pipelines=resident_io_pipelines,
                resident_registration_fastpath=resident_registration_fastpath,
            )
            if match is not None:
                artifact_matches.append(match)
        checks.append(
            _check(
                f"contract_required_command_token_group:{group_name}",
                bool(matched) or bool(artifact_matches),
                {
                    "any_of": tokens,
                    "matched": matched,
                    "artifact_matches": artifact_matches,
                    "resident_io_pipeline_records": len(resident_io_pipelines),
                    "run_command_present": command_text is not None,
                    "run_timing_present": bool(run_timing),
                },
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
    else:
        records = dq_provenance_records or []
    frame_contract = contract.get("frame_accounting") or {}
    if isinstance(frame_contract, dict) and frame_contract:
        checks.extend(
            _build_frame_accounting_contract_checks(
                frame_contract,
                record=frame_accounting_record or collect_frame_accounting_record(glass_run),
                speedup_summary=speedup_summary,
                dq_provenance_records=records,
            )
        )
    resident_contract = contract.get("resident_determinism") or {}
    if isinstance(resident_contract, dict) and resident_contract:
        checks.extend(
            _build_resident_determinism_contract_checks(
                resident_contract,
                resident_determinism=resident_determinism,
                output_numerical_drifts=output_numerical_drifts or [],
            )
        )
    registration_fastpath_contract = contract.get("resident_registration_fastpath") or {}
    if isinstance(registration_fastpath_contract, dict) and registration_fastpath_contract:
        checks.extend(
            _build_resident_registration_fastpath_contract_checks(
                registration_fastpath_contract,
                record=resident_registration_fastpath
                or collect_resident_registration_fastpath_record(glass_run),
            )
        )
    pipeline_contract_requirements = contract.get("pipeline_contract") or {}
    if isinstance(pipeline_contract_requirements, dict) and pipeline_contract_requirements:
        checks.extend(
            _build_pipeline_contract_checks(
                pipeline_contract_requirements,
                pipeline_contract=pipeline_contract,
            )
        )
    stack_default_requirements = contract.get("stack_engine_default_promotion") or {}
    if isinstance(stack_default_requirements, dict) and stack_default_requirements:
        checks.extend(
            _build_stack_engine_default_promotion_contract_checks(
                stack_default_requirements,
                stack_engine_contract=stack_engine_contract,
            )
        )
    return checks
