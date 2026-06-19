from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def _cache_file_entry(
    *,
    cache_dir: Path | None,
    cache_key: str,
    kind: str,
    suffix: str,
    required: bool,
) -> dict[str, Any]:
    path = None if cache_dir is None or not cache_key else cache_dir / f"{cache_key}_{suffix}"
    exists = bool(path is not None and path.exists())
    size_bytes = int(path.stat().st_size) if exists and path is not None else 0
    return {
        "kind": kind,
        "path": None if path is None else str(path),
        "required": bool(required),
        "exists": exists,
        "size_bytes": size_bytes,
    }


def _entry_from_master_set(set_id: str, stats: Mapping[str, Any]) -> dict[str, Any]:
    cache_dir_value = stats.get("cache_dir")
    cache_dir = Path(str(cache_dir_value)) if cache_dir_value else None
    cache_key = str(stats.get("cache_key") or "")
    bias_count = _int_or_zero(stats.get("bias_count"))
    dark_count = _int_or_zero(stats.get("dark_count"))
    flat_count = _int_or_zero(stats.get("flat_count"))
    files = [
        _cache_file_entry(
            cache_dir=cache_dir,
            cache_key=cache_key,
            kind="stats",
            suffix="master_stats.json",
            required=True,
        ),
        _cache_file_entry(
            cache_dir=cache_dir,
            cache_key=cache_key,
            kind="bias",
            suffix="master_bias.npy",
            required=bias_count > 0,
        ),
        _cache_file_entry(
            cache_dir=cache_dir,
            cache_key=cache_key,
            kind="dark",
            suffix="master_dark.npy",
            required=dark_count > 0,
        ),
        _cache_file_entry(
            cache_dir=cache_dir,
            cache_key=cache_key,
            kind="flat",
            suffix="master_flat.npy",
            required=flat_count > 0,
        ),
    ]
    missing_required = [
        {"kind": item["kind"], "path": item["path"]}
        for item in files
        if item["required"] and not item["exists"]
    ]
    required_bytes = sum(int(item["size_bytes"]) for item in files if item["required"] and item["exists"])
    return {
        "set_id": set_id,
        "filter": stats.get("filter"),
        "shape": stats.get("shape"),
        "groups": {
            "bias": stats.get("bias_group"),
            "dark": stats.get("dark_group"),
            "flat": stats.get("flat_group"),
            "flat_bias": stats.get("flat_bias_group"),
        },
        "counts": {
            "bias": bias_count,
            "dark": dark_count,
            "flat": flat_count,
        },
        "cache_scope": stats.get("cache_scope"),
        "cache_dir": None if cache_dir is None else str(cache_dir),
        "cache_key": cache_key,
        "cache_base_key": stats.get("cache_base_key"),
        "cache_fingerprint": stats.get("cache_fingerprint"),
        "cache_hit": bool(stats.get("cache_hit")),
        "files": files,
        "required_file_count": sum(1 for item in files if item["required"]),
        "present_required_file_count": sum(1 for item in files if item["required"] and item["exists"]),
        "missing_required_files": missing_required,
        "required_bytes": required_bytes,
        "complete": not missing_required and bool(cache_key) and bool(stats.get("cache_fingerprint")),
    }


def build_resident_master_cache_group(
    *,
    filter_name: str | None,
    master_stats: Mapping[str, Any],
) -> dict[str, Any]:
    """Build an auditable resident master-cache group from resident master stats."""

    sets = master_stats.get("sets") if isinstance(master_stats.get("sets"), Mapping) else {}
    entries = [
        _entry_from_master_set(str(set_id), stats)
        for set_id, stats in sorted(sets.items())
        if isinstance(stats, Mapping)
    ]
    scopes = Counter(str(entry.get("cache_scope") or "unknown") for entry in entries)
    hit_count = sum(1 for entry in entries if entry["cache_hit"])
    complete_count = sum(1 for entry in entries if entry["complete"])
    missing_required_files = [
        {"set_id": entry["set_id"], **missing}
        for entry in entries
        for missing in entry["missing_required_files"]
    ]
    return {
        "schema_version": 1,
        "artifact": "resident_master_cache_group",
        "filter": filter_name,
        "set_count": len(entries),
        "cache_hit_count": hit_count,
        "cache_miss_count": len(entries) - hit_count,
        "complete_set_count": complete_count,
        "incomplete_set_count": len(entries) - complete_count,
        "cache_scope_counts": dict(sorted(scopes.items())),
        "total_required_bytes": sum(int(entry["required_bytes"]) for entry in entries),
        "missing_required_files": missing_required_files,
        "passed": len(missing_required_files) == 0,
        "status": "passed" if len(missing_required_files) == 0 else "failed",
        "entries": entries,
        "semantics": (
            "Resident master-cache entries are content-addressed by calibration "
            "groups, input frame metadata/stat tokens, image shape, filter, and "
            "calibration policy. A cache hit means GLASS reused existing master "
            "arrays for this run; a miss means this run built and wrote them."
        ),
    }


def summarize_resident_master_cache_groups(groups: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    group_list = list(groups)
    scope_counts: Counter[str] = Counter()
    failed_groups: list[str] = []
    for index, group in enumerate(group_list):
        scope_counts.update({str(key): _int_or_zero(value) for key, value in dict(group.get("cache_scope_counts") or {}).items()})
        if not group.get("passed"):
            failed_groups.append(str(group.get("filter") or index))
    set_count = sum(_int_or_zero(group.get("set_count")) for group in group_list)
    hit_count = sum(_int_or_zero(group.get("cache_hit_count")) for group in group_list)
    complete_set_count = sum(_int_or_zero(group.get("complete_set_count")) for group in group_list)
    total_required_bytes = sum(_int_or_zero(group.get("total_required_bytes")) for group in group_list)
    return {
        "group_count": len(group_list),
        "set_count": set_count,
        "cache_hit_count": hit_count,
        "cache_miss_count": set_count - hit_count,
        "complete_set_count": complete_set_count,
        "incomplete_set_count": set_count - complete_set_count,
        "cache_scope_counts": dict(sorted(scope_counts.items())),
        "total_required_bytes": total_required_bytes,
        "failed_group_count": len(failed_groups),
        "failed_groups": failed_groups,
        "passed": not failed_groups,
    }


def validate_resident_master_cache_payload(payload: Mapping[str, Any]) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    if bool(summary.get("passed")):
        return
    failed = ", ".join(str(item) for item in summary.get("failed_groups") or [])
    raise RuntimeError(f"resident master cache validation failed for group(s): {failed}")
