from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.pipeline_contract import build_pipeline_contract_audit
from glass.synthetic.generator import generate_synthetic_dataset


def test_pipeline_contract_passes_for_cpu_audit_run(tmp_path: Path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    out = tmp_path / "pipeline_contract.json"
    markdown = tmp_path / "pipeline_contract.md"
    generate_synthetic_dataset(data, frames=3, width=24, height=24)

    assert main(["audit", "--root", str(data), "--out", str(run), "--backend", "cpu", "--tile-size", "8"]) == 0
    assert main(["pipeline-contract", "--run", str(run), "--out", str(out), "--markdown", str(markdown)]) == 0

    audit = read_json(out)
    assert audit["passed"] is True
    checks = {item["name"]: item for item in audit["checks"]}
    assert checks["integration_output_maps_available"]["passed"] is True
    assert checks["integration_dq_contract"]["passed"] is True
    assert checks["local_normalization_contract"]["passed"] is True
    assert checks["warp_outputs_have_dq_and_coverage"]["passed"] is True
    assert "GLASS Pipeline Invariant Contract Audit" in markdown.read_text(encoding="utf-8")


def test_pipeline_contract_fails_missing_maps_and_crop_records(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    write_json(
        run / "integration_results.json",
        {
            "rejection": "winsorized_sigma",
            "outputs": [
                {
                    "filter": "H",
                    "master_path": "integration/master_H.fits",
                    "weight_map_path": None,
                    "coverage_map_path": None,
                    "dq_map_path": None,
                    "low_rejection_map_path": None,
                    "high_rejection_map_path": None,
                    "dq_summary": {},
                }
            ],
        },
    )
    write_json(
        run / "local_norm_results.json",
        {
            "enabled": True,
            "reference_frame_id": "F1",
            "local_norm_results": [
                {
                    "frame_id": "F1",
                    "normalized_path": "local_norm_cache/local_norm_F1.fits",
                    "coverage_path": "registered_cache/coverage_F1.fits",
                    "dq_summary": {},
                }
            ],
        },
    )

    audit = build_pipeline_contract_audit(run)
    checks = {item["name"]: item for item in audit["checks"]}
    assert audit["passed"] is False
    assert checks["integration_output_maps_available"]["passed"] is False
    assert checks["integration_dq_contract"]["passed"] is False
    assert checks["local_normalization_contract"]["passed"] is False
