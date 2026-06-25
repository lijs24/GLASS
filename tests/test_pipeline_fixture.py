from __future__ import annotations

from pathlib import Path
import struct
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from glass.cli import main
from glass.engine.integration import integrate_registered_frames
from glass.engine.pipeline import (
    _exact_median_scratch,
    _mean_stack_tile,
    _normalization_scalar,
    _stack_mean_master,
    _stream_mean_master,
)
from glass.io.fits_io import read_fits_data, read_fits_header, write_fits_data
from glass.io.json_io import read_json, write_json
from glass.models import CalibrationPolicy
from glass.synthetic.generator import generate_synthetic_dataset


def _write_test_xisf_from_fits(path: Path, data, header: dict[str, object]) -> None:
    image = data.astype("<f4")
    height, width = image.shape
    payload = image.tobytes(order="C")
    offset = 4096
    keyword_names = ["IMAGETYP", "FILTER", "EXPTIME", "GAIN", "OFFSET", "CCD-TEMP", "XBINNING", "YBINNING"]
    keywords = "".join(
        f'<FITSKeyword name="{name}" value="{header[name]}"/>'
        for name in keyword_names
        if name in header and header[name] is not None
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<xisf version="1.0">'
        f'<Image geometry="{width}:{height}:1" sampleFormat="Float32" location="attachment:{offset}:{len(payload)}">'
        f"{keywords}</Image></xisf>"
    ).encode("utf-8")
    if 16 + len(xml) > offset:
        raise AssertionError("test XISF header exceeded fixed offset")
    path.write_bytes(b"XISF0100" + struct.pack("<Q", len(xml)) + xml + b"\0" * (offset - 16 - len(xml)) + payload)


def _write_registered_integration_fixture(
    tmp_path: Path,
    *,
    allow_cuda_fast_path: bool = False,
    output_variance_map: bool = True,
) -> tuple[Path, Path]:
    import numpy as np

    run = tmp_path / "run"
    registered = run / "registered"
    registered.mkdir(parents=True)
    frame_paths: list[Path] = []
    coverage_paths: list[Path] = []
    for index, value in enumerate([2.0, 6.0]):
        frame_path = registered / f"light_{index}.fits"
        coverage_path = registered / f"coverage_{index}.fits"
        write_fits_data(frame_path, np.full((4, 4), value, dtype=np.float32))
        write_fits_data(coverage_path, np.ones((4, 4), dtype=np.float32))
        frame_paths.append(frame_path)
        coverage_paths.append(coverage_path)
    write_json(
        run / "warp_results.json",
        {
            "warp_results": [
                {
                    "frame_id": f"light-{index}",
                    "registered_path": str(frame_paths[index]),
                    "coverage_path": str(coverage_paths[index]),
                }
                for index in range(2)
            ]
        },
    )
    plan = tmp_path / "processing_plan.json"
    write_json(
        plan,
        {
            "frames": [{"id": f"light-{index}", "filter": "H"} for index in range(2)],
            "integration_policy": {
                "combine": "mean",
                "weighting": "none",
                "rejection": "none",
                "output_variance_map": output_variance_map,
                "allow_cuda_streaming_accumulator_fast_path": allow_cuda_fast_path,
            },
        },
    )
    return run, plan


def _install_fake_integration_cuda(monkeypatch) -> None:
    def accumulate(frame_tile, weight_tile, sum_tile, weight_sum_tile):
        return sum_tile + frame_tile * weight_tile, weight_sum_tile + weight_tile

    monkeypatch.setitem(
        sys.modules,
        "glass_cuda",
        SimpleNamespace(
            cuda_available=lambda: True,
            integrate_accumulate_mean_tile_f32=accumulate,
        ),
    )


def test_pipeline_fixture_audit(tmp_path: Path):
    import json

    data = tmp_path / "data"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert (run / "run_state.json").exists()
    assert (run / "run_timing.json").exists()
    assert (run / "integration_results.json").exists()
    assert (run / "frame_accounting.json").exists()
    timing = json.loads((run / "run_timing.json").read_text(encoding="utf-8"))
    assert timing["command"] == "audit"
    assert timing["total_elapsed_s"] > 0
    assert {"scan", "plan", "calibration", "quality", "registration", "warp", "local_normalization", "integration"}.issubset(
        {item["stage"] for item in timing["stages"]}
    )
    integration = json.loads((run / "integration_results.json").read_text(encoding="utf-8"))
    assert integration["rejection"] == "none"
    assert all(output["tile_stack_mode"] == "stack_engine_cpu" for output in integration["outputs"])
    assert all(output["stack_engine_enabled"] for output in integration["outputs"])
    assert all(Path(output["dq_map_path"]).exists() for output in integration["outputs"])
    assert all(Path(output["variance_map_path"]).exists() for output in integration["outputs"])
    assert all(output["output_variance_map"] for output in integration["outputs"])
    assert all("valid" in output["dq_summary"] for output in integration["outputs"])
    assert all(output["stack_engine_dq_provenance"]["schema_version"] == 1 for output in integration["outputs"])
    assert all(output["stack_engine_dq_provenance"]["input_samples"] > 0 for output in integration["outputs"])
    assert all(
        output["stack_engine_metrics"]["execution_path"] == "stack_engine_streaming_tile_sink"
        for output in integration["outputs"]
    )
    assert all(
        output["stack_engine_metrics"]["full_output_arrays_materialized"] is False
        for output in integration["outputs"]
    )
    assert all(
        output["stack_engine_metrics"]["streaming_tile_contract_failed_count"] == 0
        for output in integration["outputs"]
    )
    assert all(
        output["stack_engine_dq_provenance"]["result_contract"]["contract_type"]
        == "stack_engine_streaming_result_contract"
        for output in integration["outputs"]
    )
    assert all(
        output["stack_engine_dq_provenance"]["result_contract"]["passed"]
        for output in integration["outputs"]
    )
    assert all(output["dq_provenance_summary"]["source_schema"] == "stack_engine_dq_provenance" for output in integration["outputs"])
    assert all(output["dq_provenance_summary"]["engine"] == "stack_engine_cpu" for output in integration["outputs"])
    assert list((run / "integration").glob("master_*.fits"))
    report_text = (run / "report.html").read_text(encoding="utf-8")
    assert "Stage coverage summary" in report_text
    assert "DQ/mask summary" in report_text
    assert "StackEngine DQ provenance" in report_text
    assert "DQ provenance contract" in report_text
    assert "flagged_samples" in report_text
    assert "Master frame statistics" in report_text
    assert "XISF input cache" in report_text
    assert "Integration output maps" in report_text
    assert "Frame accounting" in report_text
    assert "variance_map_" in report_text
    assert "winsorized_sigma" in report_text
    assert main(["resume", "--run", str(run)]) == 0


def test_integration_auto_keeps_stack_engine_default_when_cuda_is_available(
    tmp_path: Path,
    monkeypatch,
):
    _install_fake_integration_cuda(monkeypatch)
    run, plan = _write_registered_integration_fixture(tmp_path)

    payload = integrate_registered_frames(run, plan_path=plan, backend="auto", tile_size=2)

    assert payload["integration_engine_policy"]["default_engine"] == "stack_engine_cpu"
    assert payload["integration_engine_policy"]["cuda_available"] is True
    assert payload["integration_engine_policy"]["explicit_cuda_fast_path"] is False
    assert (
        payload["integration_engine_policy"]["reason"]
        == "stack_engine_default_requires_explicit_cuda_fast_path"
    )
    assert all(output["backend"] == "cpu" for output in payload["outputs"])
    assert all(output["tile_stack_mode"] == "stack_engine_cpu" for output in payload["outputs"])
    assert all(output["stack_engine_enabled"] for output in payload["outputs"])
    assert all(
        output["stack_engine_metrics"]["execution_path"] == "stack_engine_streaming_tile_sink"
        for output in payload["outputs"]
    )
    assert all(
        output["stack_engine_metrics"]["full_output_arrays_materialized"] is False
        for output in payload["outputs"]
    )
    assert all(output["stack_engine_metrics"]["streaming_tile_contract_count"] == 4 for output in payload["outputs"])
    assert all(
        output["stack_engine_dq_provenance"]["result_contract"]["passed"]
        for output in payload["outputs"]
    )
    assert np.allclose(read_fits_data(run / "integration" / "master_H.fits"), 4.0)


def test_integration_cuda_backend_keeps_stack_engine_default_without_policy(
    tmp_path: Path,
    monkeypatch,
):
    _install_fake_integration_cuda(monkeypatch)
    run, plan = _write_registered_integration_fixture(tmp_path)

    payload = integrate_registered_frames(run, plan_path=plan, backend="cuda", tile_size=2)

    assert payload["integration_engine_policy"]["default_engine"] == "stack_engine_cpu"
    assert payload["integration_engine_policy"]["backend"] == "cuda"
    assert payload["integration_engine_policy"]["cuda_available"] is True
    assert payload["integration_engine_policy"]["cuda_fast_path_eligible"] is True
    assert payload["integration_engine_policy"]["allow_cuda_streaming_accumulator_fast_path"] is False
    assert payload["integration_engine_policy"]["explicit_cuda_fast_path"] is False
    assert payload["integration_engine_policy"]["cuda_fast_path_policy_required"] is True
    assert (
        payload["integration_engine_policy"]["reason"]
        == "cuda_backend_stack_engine_default_requires_fast_path_policy"
    )
    assert all(output["backend"] == "cpu" for output in payload["outputs"])
    assert all(output["tile_stack_mode"] == "stack_engine_cpu" for output in payload["outputs"])
    assert all(output["stack_engine_enabled"] for output in payload["outputs"])
    assert np.allclose(read_fits_data(run / "integration" / "master_H.fits"), 4.0)


def test_stack_engine_streaming_sink_accepts_disabled_variance_map(tmp_path: Path):
    run, plan = _write_registered_integration_fixture(tmp_path, output_variance_map=False)

    payload = integrate_registered_frames(run, plan_path=plan, backend="cpu", tile_size=2)

    output = payload["outputs"][0]
    assert output["variance_map_path"] is None
    assert output["output_variance_map"] is False
    assert output["stack_engine_metrics"]["execution_path"] == "stack_engine_streaming_tile_sink"
    assert output["stack_engine_metrics"]["full_output_arrays_materialized"] is False
    contract = output["stack_engine_dq_provenance"]["result_contract"]
    assert contract["contract_type"] == "stack_engine_streaming_result_contract"
    assert contract["requested_maps"]["variance"] is False
    assert contract["passed"] is True
    assert np.allclose(read_fits_data(run / "integration" / "master_H.fits"), 4.0)


def test_integration_cuda_fast_path_requires_explicit_policy(
    tmp_path: Path,
    monkeypatch,
):
    _install_fake_integration_cuda(monkeypatch)
    run, plan = _write_registered_integration_fixture(
        tmp_path,
        allow_cuda_fast_path=True,
    )

    payload = integrate_registered_frames(run, plan_path=plan, backend="auto", tile_size=2)

    assert payload["integration_engine_policy"]["default_engine"] == "stack_engine_cpu"
    assert payload["integration_engine_policy"]["allow_cuda_streaming_accumulator_fast_path"] is True
    assert payload["integration_engine_policy"]["explicit_cuda_fast_path"] is True
    assert payload["integration_engine_policy"]["reason"] == "explicit_cuda_fast_path_requested"
    assert all(output["backend"] == "cuda" for output in payload["outputs"])
    assert all(
        output["tile_stack_mode"] == "cuda_streaming_accumulator_fast_path"
        for output in payload["outputs"]
    )
    assert all(not output["stack_engine_enabled"] for output in payload["outputs"])
    assert np.allclose(read_fits_data(run / "integration" / "master_H.fits"), 4.0)


def test_integration_cuda_backend_fast_path_still_requires_policy(
    tmp_path: Path,
    monkeypatch,
):
    _install_fake_integration_cuda(monkeypatch)
    run, plan = _write_registered_integration_fixture(
        tmp_path,
        allow_cuda_fast_path=True,
    )

    payload = integrate_registered_frames(run, plan_path=plan, backend="cuda", tile_size=2)

    assert payload["integration_engine_policy"]["backend"] == "cuda"
    assert payload["integration_engine_policy"]["allow_cuda_streaming_accumulator_fast_path"] is True
    assert payload["integration_engine_policy"]["explicit_cuda_fast_path"] is True
    assert payload["integration_engine_policy"]["reason"] == "explicit_cuda_fast_path_requested"
    assert all(output["backend"] == "cuda" for output in payload["outputs"])
    assert all(
        output["tile_stack_mode"] == "cuda_streaming_accumulator_fast_path"
        for output in payload["outputs"]
    )
    assert all(not output["stack_engine_enabled"] for output in payload["outputs"])
    assert np.allclose(read_fits_data(run / "integration" / "master_H.fits"), 4.0)


def test_pipeline_fixture_run_calibration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    audit.mkdir()
    assert main(["scan", "--root", str(data), "--out", str(audit / "manifest.json")]) == 0
    assert main(["plan", "--manifest", str(audit / "manifest.json"), "--out", str(audit / "processing_plan.json")]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "calibration",
                "--tile-size",
                "9",
                "--flat-floor",
                "0.05",
            ]
        )
        == 0
    )
    assert (run / "calibration_artifacts.json").exists()
    assert len(list((run / "calib_cache" / "masters").glob("*.fits"))) >= 3
    assert len(list((run / "calib_cache" / "calibrated").glob("*.fits"))) == 3
    assert len(list((run / "calib_cache" / "dq").glob("dq_calibrated_*.fits"))) == 3
    import json

    artifacts = json.loads((run / "calibration_artifacts.json").read_text(encoding="utf-8"))
    assert artifacts["policy"]["flat_floor"] == 0.05
    assert all(master["streaming"] for master in artifacts["masters"].values())
    assert all(master["stack_engine_enabled"] for master in artifacts["masters"].values())
    assert all(master["tile_stack_mode"].startswith("stack_engine_cpu") for master in artifacts["masters"].values())
    assert all(master["tile_size"] == 9 for master in artifacts["masters"].values())
    assert all(master["stack_engine_dq_provenance"]["schema_version"] == 1 for master in artifacts["masters"].values())
    assert all(master["stack_engine_dq_provenance"]["input_samples"] > 0 for master in artifacts["masters"].values())
    assert all(
        master["stack_engine_metrics"]["execution_path"] == "stack_engine_master_streaming_tile_sink"
        for master in artifacts["masters"].values()
    )
    assert all(
        master["stack_engine_metrics"]["full_output_arrays_materialized"] is False
        for master in artifacts["masters"].values()
    )
    assert all(
        master["stack_engine_metrics"]["streaming_tile_contract_failed_count"] == 0
        for master in artifacts["masters"].values()
    )
    assert all(
        master["stack_engine_dq_provenance"]["result_contract"]["contract_type"]
        == "stack_engine_master_streaming_result_contract"
        for master in artifacts["masters"].values()
    )
    assert all(
        master["stack_engine_dq_provenance"]["result_contract"]["passed"]
        for master in artifacts["masters"].values()
    )
    assert all(
        master["dq_provenance_summary"]["source_schema"] == "stack_engine_dq_provenance"
        for master in artifacts["masters"].values()
    )
    assert all(Path(item["dq_mask_path"]).exists() for item in artifacts["calibrated_lights"])
    assert all("valid" in item["dq_summary"] for item in artifacts["calibrated_lights"])
    flat_masters = [master for master in artifacts["masters"].values() if master["type"] == "flat"]
    assert flat_masters
    assert all(master["normalization_stage"] == "per_flat" for master in flat_masters)
    assert all(len(master["per_flat_normalization"]) >= 1 for master in flat_masters)
    assert all(master["master_rejection"] == "winsorized_sigma" for master in artifacts["masters"].values())


def test_pipeline_calibration_caches_xisf_light_input(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=1, width=24, height=24)
    light_fits = next((data / "light").glob("*.fits"))
    light_xisf = light_fits.with_suffix(".xisf")
    _write_test_xisf_from_fits(light_xisf, read_fits_data(light_fits), read_fits_header(light_fits))
    light_fits.unlink()

    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "calibration",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )

    artifacts = read_json(run / "calibration_artifacts.json")
    assert len(artifacts["input_cache"]) == 1
    cache_record = artifacts["input_cache"][0]
    assert cache_record["source_path"].endswith(".xisf")
    assert Path(cache_record["cache_path"]).exists()
    assert len(artifacts["calibrated_lights"]) == 1


def test_streaming_exact_median_scratch_matches_numpy(tmp_path: Path):
    import numpy as np

    path = tmp_path / "source.fits"
    scratch = tmp_path / "median.bin"
    data = np.array(
        [
            [9.0, 1.0, np.nan, 4.0],
            [2.0, 7.0, 6.0, 3.0],
            [8.0, 5.0, 11.0, 10.0],
        ],
        dtype=np.float32,
    )
    write_fits_data(path, data)

    assert _exact_median_scratch(path, tile_size=2, scratch_path=scratch) == float(np.nanmedian(data))
    assert not scratch.exists()


def test_flat_normalization_scalar_uses_scratch_for_small_images(tmp_path: Path, monkeypatch):
    import numpy as np
    from glass.engine.pipeline import FitsImageReader

    path = tmp_path / "flat.fits"
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    write_fits_data(path, data)

    def fail_read_full(self, dtype=np.float32):
        raise AssertionError("flat normalization should use scratch median, not read_full")

    monkeypatch.setattr(FitsImageReader, "read_full", fail_read_full)
    norm, method = _normalization_scalar(path, "median", tile_size=3)
    assert norm == float(np.median(data))
    assert method == "median_scratch_memmap"


def test_mean_stack_tile_uses_streaming_accumulator(monkeypatch):
    import numpy as np
    from types import SimpleNamespace

    class Reader:
        def __init__(self, data):
            self.data = np.asarray(data, dtype=np.float32)

        def read_tile(self, y0, y1, x0, x1):
            return self.data[y0:y1, x0:x1]

    tile = SimpleNamespace(y0=0, y1=2, x0=0, x1=2)
    readers = [
        Reader([[1, 2], [3, 4]]),
        Reader([[5, 6], [7, 8]]),
        Reader([[9, 10], [11, 12]]),
    ]
    expected = np.array([[5, 6], [7, 8]], dtype=np.float32)

    def fail_stack(*args, **kwargs):
        raise AssertionError("tile stacking should use an accumulator, not np.stack")

    monkeypatch.setattr(np, "stack", fail_stack)
    assert np.allclose(_mean_stack_tile(readers, tile), expected)


def test_stack_engine_master_matches_legacy_streaming(tmp_path: Path):
    import numpy as np

    paths = []
    for index, value in enumerate([1.0, 3.0, 5.0]):
        path = tmp_path / f"frame_{index}.fits"
        write_fits_data(path, np.full((5, 7), value, dtype=np.float32))
        paths.append(str(path))
    subtract = tmp_path / "subtract.fits"
    write_fits_data(subtract, np.ones((5, 7), dtype=np.float32))
    legacy = tmp_path / "legacy.fits"
    stack_engine = tmp_path / "stack_engine.fits"

    legacy_stats = _stream_mean_master(paths, legacy, tile_size=3, header={}, subtract_path=str(subtract))
    stack_stats, mode, fallback_reason, metrics = _stack_mean_master(
        paths, stack_engine, tile_size=3, header={}, subtract_path=str(subtract)
    )

    assert mode == "stack_engine_cpu"
    assert fallback_reason is None
    assert metrics["combine"] == "mean"
    assert metrics["execution_path"] == "stack_engine_master_streaming_tile_sink"
    assert metrics["full_output_arrays_materialized"] is False
    assert metrics["streaming_tile_contract_count"] == 6
    assert metrics["streaming_tile_contract_failed_count"] == 0
    assert metrics["dq_provenance"]["result_contract"]["contract_type"] == "stack_engine_master_streaming_result_contract"
    assert metrics["dq_provenance"]["result_contract"]["passed"] is True
    assert np.allclose(read_fits_data(stack_engine), read_fits_data(legacy))
    assert stack_stats["mean"] == legacy_stats["mean"]


def test_stack_engine_master_rejection_removes_extreme_samples(tmp_path: Path):
    import numpy as np

    paths = []
    for index, value in enumerate([1.0, 2.0, 3.0, 100.0]):
        path = tmp_path / f"frame_{index}.fits"
        write_fits_data(path, np.full((4, 4), value, dtype=np.float32))
        paths.append(str(path))
    out = tmp_path / "robust_master.fits"
    policy = CalibrationPolicy(
        master_rejection="minmax",
        master_rejection_min_samples=2,
        master_rejection_max_fraction=0.5,
    )

    stats, mode, fallback_reason, metrics = _stack_mean_master(
        paths,
        out,
        tile_size=2,
        header={},
        policy=policy,
    )

    assert mode == "stack_engine_cpu"
    assert fallback_reason is None
    assert metrics["low_rejected"] == 16
    assert metrics["high_rejected"] == 16
    assert metrics["execution_path"] == "stack_engine_master_streaming_tile_sink"
    assert metrics["dq_provenance"]["result_contract"]["passed"] is True
    assert np.allclose(read_fits_data(out), 2.5)
    assert stats["mean"] == 2.5


def test_stack_engine_master_failure_is_strict_by_default(tmp_path: Path, monkeypatch):
    import numpy as np
    import glass.engine.pipeline as pipeline_module

    paths = []
    for index, value in enumerate([2.0, 6.0]):
        path = tmp_path / f"frame_{index}.fits"
        write_fits_data(path, np.full((4, 4), value, dtype=np.float32))
        paths.append(str(path))
    out = tmp_path / "fallback.fits"

    def fail_stack_engine(*args, **kwargs):
        raise RuntimeError("forced stack engine failure")

    monkeypatch.setattr(pipeline_module, "_stack_mean_master_with_engine", fail_stack_engine)

    with pytest.raises(RuntimeError, match="legacy fallback is disabled by default") as excinfo:
        _stack_mean_master(paths, out, tile_size=2, header={})

    assert "forced stack engine failure" in str(excinfo.value.__cause__)
    assert not out.exists()


def test_stack_engine_master_explicit_fallback_preserves_legacy_streaming(
    tmp_path: Path,
    monkeypatch,
):
    import numpy as np
    import glass.engine.pipeline as pipeline_module

    paths = []
    for index, value in enumerate([2.0, 6.0]):
        path = tmp_path / f"frame_{index}.fits"
        write_fits_data(path, np.full((4, 4), value, dtype=np.float32))
        paths.append(str(path))
    out = tmp_path / "fallback.fits"

    def fail_stack_engine(*args, **kwargs):
        raise RuntimeError("forced stack engine failure")

    monkeypatch.setattr(pipeline_module, "_stack_mean_master_with_engine", fail_stack_engine)
    stats, mode, fallback_reason, metrics = _stack_mean_master(
        paths,
        out,
        tile_size=2,
        header={},
        policy=CalibrationPolicy(allow_legacy_stack_fallback=True),
    )

    assert mode == "legacy_streaming_accumulator"
    assert "forced stack engine failure" in str(fallback_reason)
    assert metrics["rejection"] == "none"
    assert metrics["legacy_fallback_explicitly_allowed"] is True
    assert np.allclose(read_fits_data(out), 4.0)
    assert stats["mean"] == 4.0


def test_pipeline_calibration_cosmetic_writes_dq_flags(tmp_path: Path):
    import json
    import numpy as np
    from astropy.io import fits

    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)
    light_path = sorted((data / "light").glob("*.fits"))[0]
    with fits.open(light_path, mode="update", memmap=False) as hdul:
        hdul[0].data = np.asarray(hdul[0].data, dtype=np.float32)
        hdul[0].data[3, 4] = 65000.0
        hdul.flush()
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    plan_path = audit / "processing_plan.json"
    plan = read_json(plan_path)
    policy = plan["calibration_plan"]["calibration_policy"]
    policy["cosmetic_correction_enabled"] = True
    policy["cosmetic_hot_sigma"] = 2.0
    policy["cosmetic_cold_sigma"] = 8.0
    policy["saturation_level"] = 60000.0
    write_json(plan_path, plan)

    assert (
        main(
            [
                "run",
                "--plan",
                str(plan_path),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "calibration",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    artifacts = json.loads((run / "calibration_artifacts.json").read_text(encoding="utf-8"))
    summaries = [item["dq_summary"] for item in artifacts["calibrated_lights"]]
    assert any(summary.get("saturated", 0) > 0 for summary in summaries)
    assert any(summary.get("hot_pixel", 0) > 0 for summary in summaries)
    assert any(summary.get("cosmetic_corrected", 0) > 0 for summary in summaries)
    assert any(item["cosmetic_correction"]["enabled"] for item in artifacts["calibrated_lights"])


def test_pipeline_fixture_run_calibration_cuda_streaming(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=2, width=20, height=18)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    try:
        rc = main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cuda",
                "--until-stage",
                "calibration",
                "--tile-size",
                "7",
            ]
        )
    except SystemExit as exc:
        if "unavailable" in str(exc):
            return
        raise
    assert rc == 0
    import json

    artifacts = json.loads((run / "calibration_artifacts.json").read_text(encoding="utf-8"))
    assert artifacts["calibrated_lights"]
    assert all(item["backend"] == "cuda" for item in artifacts["calibrated_lights"])
    assert all(item["tile_count"] > 1 for item in artifacts["calibrated_lights"])


def test_pipeline_fixture_run_quality_and_report(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=3, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "quality",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "frame_quality.json").exists()
    import json

    quality = json.loads((run / "frame_quality.json").read_text(encoding="utf-8"))
    assert quality["metric_source"] == "streaming_tile_reader"
    assert quality["tile_size"] == 8
    assert quality["star_detector"] == "robust_local_maximum_moments_v1"
    assert quality["weight_source"] == "combined_psf_snr_v1"
    assert all(item["metric_source"] == "streaming_tile_reader" for item in quality["frame_quality"])
    assert all(item["fwhm_px"] is not None for item in quality["frame_quality"])
    assert all(item["star_metrics"]["star_snr_median"] is not None for item in quality["frame_quality"])
    assert all(item["weight_source"] == "combined_psf_snr_v1" for item in quality["frame_quality"])
    assert "quality_gate_policy" in quality
    assert "quality_gate_summary" in quality
    assert all(item["quality_gate_status"] in {"accepted", "rejected"} for item in quality["frame_quality"])
    assert all("reference_candidate" in item for item in quality["frame_quality"])
    assert not (run / "quality_scratch").exists()
    assert main(["report", "--run", str(run), "--manifest", str(audit / "manifest.json"), "--plan", str(audit / "processing_plan.json"), "--out", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "Frame quality table" in text
    assert "reference_candidates" in text
    assert "Reference frame" in text
    assert "Runtime summary" in text


def test_pipeline_fixture_run_registration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=4, width=40, height=40, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "registration",
                "--tile-size",
                "10",
            ]
        )
        == 0
    )
    assert (run / "registration_results.json").exists()
    import json

    registration = json.loads((run / "registration_results.json").read_text(encoding="utf-8"))
    assert registration["registration_image_source"] == "streaming_star_detector"
    assert registration["method"] == "auto"
    assert registration["tile_size"] == 10
    assert registration["quality_gate_enforced"] is True
    assert registration["quality_gate_rejected_frames"] >= 0
    assert all(item["registration_image_source"] == "streaming_preview" for item in registration["registration_results"])
    assert all(item["matched_stars"] >= 1 for item in registration["registration_results"])
    assert all(item["status"] in {"reference", "ok"} for item in registration["registration_results"])
    assert all(item["registration_validation"]["accepted"] for item in registration["registration_results"])
    assert main(["report", "--run", str(run), "--manifest", str(audit / "manifest.json"), "--plan", str(audit / "processing_plan.json"), "--out", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "Registration table" in text
    assert "star-based clean-room registration" in (run / "registration_results.json").read_text(encoding="utf-8")


def test_pipeline_fixture_run_warp(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "warp",
                "--tile-size",
                "8",
                "--warp-interpolation",
                "lanczos3",
            ]
        )
        == 0
    )
    assert (run / "warp_results.json").exists()
    assert list((run / "registered_cache").glob("registered_*.fits"))
    assert list((run / "coverage_cache").glob("coverage_*.fits"))
    import json

    warp = json.loads((run / "warp_results.json").read_text(encoding="utf-8"))
    assert all(Path(item["dq_mask_path"]).exists() for item in warp["warp_results"])
    assert all("valid" in item["dq_summary"] for item in warp["warp_results"])
    assert warp["interpolation"] == "lanczos3"
    assert all(item["interpolation"] == "lanczos3" for item in warp["warp_results"])


def test_pipeline_fixture_run_local_normalization(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=3, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "local_normalization",
                "--local-normalization",
                "on",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "local_norm_results.json").exists()
    assert list((run / "local_norm_cache").glob("local_norm_*.fits"))
    assert list((run / "dq_cache").glob("dq_local_norm_*.fits"))
    assert (
        main(
            [
                "report",
                "--run",
                str(run),
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(report),
            ]
        )
        == 0
    )
    assert "Local normalization summary" in report.read_text(encoding="utf-8")
    import json

    local_norm = json.loads((run / "local_norm_results.json").read_text(encoding="utf-8"))
    result = local_norm["local_norm_results"][0]
    assert Path(result["dq_mask_path"]).exists()
    assert "valid" in result["dq_summary"]
    assert result["grid_rows"] == 4
    assert result["grid_cols"] == 4
    assert result["tile_count"] == 16
    assert result["model"] == "continuous_grid_mean_std_v1"
    assert result["coefficient_field_model"] == "bilinear_tile_center_v1"
    assert result["full_field_map_status"] == "written"
    assert Path(result["scale_field_path"]).exists()
    assert Path(result["offset_field_path"]).exists()
    assert Path(result["residual_map_path"]).exists()
    assert result["crop_box"] is None
    assert result["residual_summary"]["valid_pixels"] > 0
    coefficients = json.loads(Path(result["coefficient_grid_path"]).read_text(encoding="utf-8"))
    assert coefficients["grid_rows"] == 4
    assert coefficients["grid_cols"] == 4
    assert coefficients["model"] == "continuous_grid_mean_std_v1"
    assert coefficients["coefficient_field_model"] == "bilinear_tile_center_v1"
    assert coefficients["full_field_map_status"] == "written"
    assert Path(coefficients["scale_field_path"]).exists()
    assert Path(coefficients["offset_field_path"]).exists()
    assert Path(coefficients["residual_map_path"]).exists()
    assert coefficients["crop_box"] is None
    assert len(coefficients["scales"]) == 4
    assert len(coefficients["scales"][0]) == 4
    assert len(coefficients["valid_pixels"][0]) == 4


def test_pipeline_fixture_run_integration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    report = tmp_path / "report.html"
    generate_synthetic_dataset(data, frames=4, width=32, height=32, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "auto",
                "--until-stage",
                "integration",
                "--local-normalization",
                "on",
                "--integration-weighting",
                "combined",
                "--integration-rejection",
                "winsorized_sigma",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    assert (run / "integration_results.json").exists()
    assert (run / "frame_accounting.json").exists()
    import json

    integration = json.loads((run / "integration_results.json").read_text(encoding="utf-8"))
    accounting = json.loads((run / "frame_accounting.json").read_text(encoding="utf-8"))
    assert integration["weighting"] == "combined"
    assert accounting["summary"]["integrated_frames"] >= 1
    assert accounting["summary"]["input_light_frames"] == 4
    assert len(set(round(float(weight), 6) for weight in integration["frame_weights"].values())) > 1
    assert all(output["tile_stack_mode"] == "stack_engine_cpu" for output in integration["outputs"])
    assert all(output["stack_engine_enabled"] for output in integration["outputs"])
    assert all(output["stack_engine_rejection_method"] == "winsorized_sigma" for output in integration["outputs"])
    assert all(output["stack_engine_dq_provenance"]["schema_version"] == 1 for output in integration["outputs"])
    assert all(output["dq_provenance_summary"]["stage"] == "integration" for output in integration["outputs"])
    assert all(
        output["stack_engine_dq_provenance"]["output_high_rejected_pixels"] >= 0
        for output in integration["outputs"]
    )
    assert all(Path(output["dq_map_path"]).exists() for output in integration["outputs"])
    assert all("high_rejected" in output["dq_summary"] or "valid" in output["dq_summary"] for output in integration["outputs"])
    assert list((run / "integration").glob("master_*.fits"))
    assert list((run / "integration").glob("weight_map_*.fits"))
    assert list((run / "integration").glob("coverage_map_*.fits"))
    assert list((run / "integration").glob("variance_map_*.fits"))
    assert list((run / "integration").glob("low_rejection_*.fits"))
    assert list((run / "integration").glob("high_rejection_*.fits"))
    assert (
        main(
            [
                "report",
                "--run",
                str(run),
                "--manifest",
                str(audit / "manifest.json"),
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(report),
            ]
        )
        == 0
    )
    report_text = report.read_text(encoding="utf-8")
    assert "Integration summary" in report_text
    assert "Frame accounting" in report_text
    assert "Rejected/zero-weight frames" in report_text
    assert "StackEngine DQ provenance" in report_text
    assert "DQ provenance contract" in report_text


def test_resume_continues_from_warp_without_repeating_calibration(tmp_path: Path):
    data = tmp_path / "data"
    audit = tmp_path / "audit"
    run = tmp_path / "run"
    generate_synthetic_dataset(data, frames=3, width=24, height=24, known_shift=True)
    assert main(["audit", "--root", str(data), "--out", str(audit), "--backend", "cpu"]) == 0
    assert (
        main(
            [
                "run",
                "--plan",
                str(audit / "processing_plan.json"),
                "--out",
                str(run),
                "--backend",
                "cpu",
                "--until-stage",
                "warp",
                "--tile-size",
                "8",
            ]
        )
        == 0
    )
    calibration_artifacts = run / "calibration_artifacts.json"
    before = calibration_artifacts.stat().st_mtime_ns
    assert main(["resume", "--run", str(run)]) == 0
    assert (run / "integration_results.json").exists()
    assert calibration_artifacts.stat().st_mtime_ns == before
