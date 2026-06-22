from __future__ import annotations

from pathlib import Path

from glass.cli import main
from glass.io.json_io import read_json, write_json
from glass.report.benchmark_contract_profile import RESIDENT_CUDA_DQ_PROFILE_NAME
from glass.report.resident_ab_matrix_plan import build_resident_ab_matrix_execution, build_resident_ab_matrix_plan


def test_resident_ab_matrix_plan_builds_v1_v2_commands(tmp_path: Path) -> None:
    payload = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        glass_scale=1.25,
        glass_offset=0.5,
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
    )

    assert payload["artifact_type"] == "resident_ab_matrix_plan"
    assert payload["ready_to_execute"] is True
    assert payload["readiness"]["gpu"]["status"] == "ready"
    assert payload["comparison_policy"]["benchmark_contract_profile"] == RESIDENT_CUDA_DQ_PROFILE_NAME
    assert [row["variant_id"] for row in payload["variants"]] == [
        "throughput_v1_lanczos3_parity",
        "throughput_v2_fused_bilinear",
    ]

    baseline, candidate = payload["variants"]
    baseline_run = baseline["commands"]["run"]
    candidate_run = candidate["commands"]["run"]
    candidate_compare = candidate["commands"]["compare_baseline"]

    assert "--resident-runtime-preset throughput-v1" in baseline_run
    assert "--resident-warp-interpolation lanczos3" in baseline_run
    assert "--resident-integration-dispatch stack" in baseline_run
    assert "--resident-runtime-preset throughput-v2-fused" in candidate_run
    assert "--resident-warp-interpolation bilinear" in candidate_run
    assert "--resident-integration-dispatch" not in candidate_run
    assert "throughput_v2_fused_bilinear_vs_throughput_v1_lanczos3_parity" in candidate_compare
    assert "--glass-scale 1.25" in baseline["commands"]["compare_reference"]
    assert "--glass-offset 0.5" in baseline["commands"]["compare_reference"]
    assert "acceptance-audit" in candidate["commands"]["acceptance_audit"]
    assert "--benchmark-contract-profile resident_cuda_dq_v1" in candidate["commands"]["acceptance_audit"]
    assert "summarize_wbpp_speedup.py" in candidate["commands"]["speedup_summary"]


def test_resident_ab_matrix_plan_marks_busy_gpu_waiting(tmp_path: Path) -> None:
    payload = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 97, 596.21",
    )

    assert payload["ready_to_execute"] is False
    assert payload["recommendation"] == "wait_for_clean_gpu_or_disk_window"
    assert payload["readiness"]["gpu"]["status"] == "busy"
    assert payload["readiness"]["gpu"]["free_mib"] == 77886


def test_cli_resident_ab_matrix_plan_writes_outputs(tmp_path: Path) -> None:
    out = tmp_path / "ab_plan.json"
    markdown = tmp_path / "ab_plan.md"

    assert (
        main(
            [
                "resident-ab-matrix-plan",
                "--root",
                str(tmp_path / "ab"),
                "--plan",
                str(tmp_path / "processing_plan.json"),
                "--manifest",
                str(tmp_path / "manifest.json"),
                "--wbpp-result",
                str(tmp_path / "wbpp_result.json"),
                "--reference",
                str(tmp_path / "wbpp_master.xisf"),
                "--out",
                str(out),
                "--markdown",
                str(markdown),
                "--skip-gpu-probe",
            ]
        )
        == 0
    )

    payload = read_json(out)
    assert payload["artifact_type"] == "resident_ab_matrix_plan"
    assert payload["ready_to_execute"] is False
    assert payload["readiness"]["gpu"]["status"] == "unknown"
    assert "Resident 200-Light A/B Matrix Plan" in markdown.read_text(encoding="utf-8")


def test_resident_ab_matrix_execution_dry_run_records_steps(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
    )
    write_json(plan_path, plan)

    execution = build_resident_ab_matrix_execution(plan_path, dry_run=True)

    assert execution["artifact_type"] == "resident_ab_matrix_execution"
    assert execution["summary"]["status"] == "planned"
    assert execution["summary"]["planned_variant_count"] == 2
    baseline_steps = [step["step"] for step in execution["variants"][0]["steps"]]
    candidate_steps = [step["step"] for step in execution["variants"][1]["steps"]]
    assert baseline_steps == ["run", "compare_reference", "acceptance_audit", "speedup_summary", "report"]
    assert "compare_baseline" in candidate_steps
    assert all(step["status"] == "planned" for row in execution["variants"] for step in row["steps"])


def test_resident_ab_matrix_execution_blocks_non_dry_run_when_not_ready(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 97, 596.21",
    )
    write_json(plan_path, plan)

    execution = build_resident_ab_matrix_execution(
        plan_path,
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 97, 596.21",
    )

    assert execution["summary"]["status"] == "blocked_by_readiness"
    assert execution["summary"]["blocked"] is True
    assert execution["execution_readiness"]["source"] == "live_recheck"
    assert execution["variants"] == []


def test_resident_ab_matrix_execution_rechecks_stale_ready_plan(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
    )
    write_json(plan_path, plan)

    execution = build_resident_ab_matrix_execution(
        plan_path,
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 95, 596.21",
    )

    assert plan["ready_to_execute"] is True
    assert execution["summary"]["status"] == "blocked_by_readiness"
    assert execution["execution_readiness"]["gpu"]["status"] == "busy"
    assert execution["variants"] == []


def test_resident_ab_matrix_execution_waits_until_ready(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 95, 596.21",
    )
    for variant in plan["variants"]:
        acceptance = Path(variant["artifacts"]["acceptance_json"])
        acceptance.parent.mkdir(parents=True, exist_ok=True)
        acceptance.write_text("{}", encoding="utf-8")
    write_json(plan_path, plan)

    execution = build_resident_ab_matrix_execution(
        plan_path,
        skip_existing=True,
        wait_ready_timeout_s=10,
        wait_ready_interval_s=0,
        wait_ready_consecutive_samples=2,
        gpu_query_texts=[
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 95, 596.21",
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
        ],
    )

    assert execution["summary"]["status"] == "completed"
    assert execution["summary"]["skipped_existing_count"] == 2
    assert execution["execution_readiness"]["gpu"]["status"] == "ready"
    assert execution["execution_readiness"]["wait_ready_satisfied"] is True
    assert [attempt["gpu_status"] for attempt in execution["readiness_attempts"]] == ["busy", "ready", "ready"]
    assert [attempt["consecutive_ready"] for attempt in execution["readiness_attempts"]] == [0, 1, 2]


def test_resident_ab_matrix_execution_blocks_without_required_consecutive_ready(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 20000, 95, 596.21",
    )
    write_json(plan_path, plan)

    execution = build_resident_ab_matrix_execution(
        plan_path,
        wait_ready_timeout_s=0,
        wait_ready_consecutive_samples=2,
        gpu_query_texts=[
            "NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
        ],
    )

    assert execution["summary"]["status"] == "blocked_by_readiness"
    assert execution["execution_readiness"]["wait_ready_satisfied"] is False
    assert execution["execution_readiness"]["wait_ready_consecutive_observed"] == 1
    assert execution["variants"] == []


def test_resident_ab_matrix_execution_records_launch_errors(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
    )
    plan["variants"][0]["commands"]["run"] = "definitely_missing_glass_executable_476 --version"
    write_json(plan_path, plan)

    execution = build_resident_ab_matrix_execution(
        plan_path,
        variants=["throughput_v1_lanczos3_parity"],
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
    )

    assert execution["summary"]["status"] == "failed"
    assert execution["summary"]["failed"] is True
    step = execution["variants"][0]["steps"][0]
    assert step["status"] == "failed"
    assert step["error"]


def test_cli_resident_ab_matrix_execute_writes_dry_run(tmp_path: Path) -> None:
    plan_path = tmp_path / "ab_plan.json"
    out = tmp_path / "ab_execution.json"
    plan = build_resident_ab_matrix_plan(
        root=tmp_path / "ab",
        plan=tmp_path / "processing_plan.json",
        manifest=tmp_path / "manifest.json",
        wbpp_result=tmp_path / "wbpp_result.json",
        reference=tmp_path / "wbpp_master.xisf",
        gpu_query_text="NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97886, 1000, 5, 596.21",
    )
    write_json(plan_path, plan)

    assert main(["resident-ab-matrix-execute", "--plan", str(plan_path), "--out", str(out), "--dry-run"]) == 0

    payload = read_json(out)
    assert payload["artifact_type"] == "resident_ab_matrix_execution"
    assert payload["dry_run"] is True
    assert payload["summary"]["status"] == "planned"
