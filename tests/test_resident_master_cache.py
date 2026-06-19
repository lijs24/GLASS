from __future__ import annotations

from pathlib import Path

import pytest

from glass.engine.resident_master_cache import (
    build_resident_master_cache_group,
    summarize_resident_master_cache_groups,
    validate_resident_master_cache_payload,
)


def _stats(cache: Path, *, hit: bool = False, key: str = "H_16x16_abcd") -> dict:
    return {
        "filter": "H",
        "shape": {"height": 16, "width": 16},
        "bias_group": "bias",
        "dark_group": "dark",
        "flat_group": "flat",
        "flat_bias_group": "bias",
        "bias_count": 1,
        "dark_count": 1,
        "flat_count": 1,
        "cache_scope": "shared",
        "cache_dir": str(cache),
        "cache_key": key,
        "cache_base_key": "H_16x16",
        "cache_fingerprint": "abcd" * 16,
        "cache_hit": hit,
    }


def test_resident_master_cache_group_records_required_files(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    key = "H_16x16_abcd"
    for suffix in ["master_stats.json", "master_bias.npy", "master_dark.npy", "master_flat.npy"]:
        (cache / f"{key}_{suffix}").write_bytes(b"cache")

    group = build_resident_master_cache_group(
        filter_name="H",
        master_stats={"sets": {"set0": _stats(cache, hit=True, key=key)}},
    )

    assert group["passed"] is True
    assert group["cache_hit_count"] == 1
    assert group["cache_miss_count"] == 0
    assert group["complete_set_count"] == 1
    assert group["entries"][0]["required_file_count"] == 4
    assert group["entries"][0]["present_required_file_count"] == 4
    assert group["total_required_bytes"] > 0


def test_resident_master_cache_group_fails_missing_required_file(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    key = "H_16x16_abcd"
    (cache / f"{key}_master_stats.json").write_bytes(b"cache")

    group = build_resident_master_cache_group(
        filter_name="H",
        master_stats={"sets": {"set0": _stats(cache, key=key)}},
    )
    payload = {
        "summary": summarize_resident_master_cache_groups([group]),
        "groups": [group],
    }

    assert group["passed"] is False
    assert group["missing_required_files"]
    with pytest.raises(RuntimeError, match="resident master cache validation failed"):
        validate_resident_master_cache_payload(payload)


def test_resident_master_cache_summary_counts_hits_and_scopes(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    for key in ["a", "b"]:
        for suffix in ["master_stats.json", "master_bias.npy", "master_dark.npy", "master_flat.npy"]:
            (cache / f"{key}_{suffix}").write_bytes(b"cache")

    group_a = build_resident_master_cache_group(
        filter_name="H",
        master_stats={"sets": {"set0": _stats(cache, hit=True, key="a")}},
    )
    group_b = build_resident_master_cache_group(
        filter_name="O",
        master_stats={"sets": {"set0": _stats(cache, hit=False, key="b")}},
    )

    summary = summarize_resident_master_cache_groups([group_a, group_b])

    assert summary["passed"] is True
    assert summary["group_count"] == 2
    assert summary["set_count"] == 2
    assert summary["cache_hit_count"] == 1
    assert summary["cache_miss_count"] == 1
    assert summary["cache_scope_counts"] == {"shared": 2}
