# S2-Gate 648 Status: Resident Calibration Reentry Boundary

## Gate

- Gate: S2-Gate 648
- Name: Resident calibration reentry boundary
- Status: green
- Completed at: 2026-06-25

## Completed

- Added `resident_reentry_boundary.json` as a runtime artifact for resident CUDA
  runs.
- Added `src/glass/engine/resident_reentry_boundary.py`.
- Added `glass resident-reentry-boundary`.
- `glass run --memory-mode resident` now writes the boundary as a timed
  postcondition stage.
- `glass resume` now writes and consumes the boundary before ledger/preflight.
- Partial resident runs that already entered `resident_calibration_integration`
  and have ready calibration evidence now report
  `blocked_calibration_boundary_reentry_not_implemented` instead of a generic
  incomplete resident block.
- The resident stage ledger now tracks the `resident_reentry_boundary` artifact.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_reentry_boundary.py tests\\test_resident_resume.py tests\\test_resident_stage_ledger.py tests\\test_resident_master_cache.py tests\\test_resident_calibration_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\resident_reentry_boundary.py src\\glass\\engine\\resident_resume.py src\\glass\\engine\\resident_stage_ledger.py src\\glass\\cli.py tests\\test_resident_reentry_boundary.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe resident-reentry-boundary --run C:\\glass_runs\\phase2_s2_gate647_resident_reentry\\runs_20260625_190000\\candidate_reentry_from_scout --out C:\\glass_runs\\phase2_s2_gate647_resident_reentry\\runs_20260625_190000\\candidate_reentry_from_scout\\resident_reentry_boundary_gate648_probe.json --fail-on-missing`
- `.\\.venv\\Scripts\\glass.exe run --plan C:\\glass_runs\\phase2_s2_gate540_plan_spec_cache\\runs_20260623_140314\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate597_async_master_cache\\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10`
- `.\\.venv\\Scripts\\glass.exe resident-regression-gate --baseline-run C:\\glass_runs\\phase2_s2_gate647_resident_reentry\\runs_20260625_190000\\candidate_reentry_from_scout --candidate-run C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict --out C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_vs_gate647_regression_gate.json --markdown C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_vs_gate647_regression_gate.md --max-elapsed-ratio 1.2 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict\\integration\\resident_master_H.fits --reference C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_vs_wbpp_compare.html --glass-time-seconds 11.602077399846166 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\glass_runs\\phase2_s2_gate540_plan_spec_cache\\runs_20260623_140314\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_vs_wbpp_compare.json --out C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_acceptance_audit.json --markdown C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.01 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict\\pipeline_contract.json --stack-engine-contract-json C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict\\stack_engine_contract.json --warp-quality-contract-json C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict\\warp_quality_contract.json --require-warp-quality-contract`
- `.\\.venv\\Scripts\\glass.exe phase2-mainline-audit --run C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict --acceptance-audit C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_acceptance_audit.json --compare-json C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_vs_wbpp_compare.json --out C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_mainline_audit.json --markdown C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.01 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe resume --run C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\candidate_boundary_strict`
- `.\\.venv\\Scripts\\glass.exe doctor --json C:\\glass_runs\\phase2_s2_gate648_reentry_boundary\\runs_20260625_200000\\gate648_doctor.json`

## Test Results

- Boundary-focused pytest: `14 passed in 0.71 s`.
- Updated resident source-DQ route postcondition test: `1 passed in 1.18 s`.
- Final resident boundary/resume focused pytest after invocation guard:
  `7 passed in 0.46 s`.
- Combined focused pytest after the source-DQ route update: `15 passed in 1.10 s`.
- Ruff: passed.
- Full pytest: `1359 passed in 60.11 s`.
- Real 200-light resident run: passed.
- Resident regression gate versus Gate647: passed, elapsed ratio
  `1.0335357209723688`.
- Acceptance audit: passed.
- Phase 2 mainline audit: passed.
- Completed-run resume: passed with `resume_action=noop_complete`.

## Real 200-Light Results

- Run directory:
  `C:\glass_runs\phase2_s2_gate648_reentry_boundary\runs_20260625_200000\candidate_boundary_strict`
- Total elapsed: `11.602077399846166 s`
- Resident calibration/integration stage: `9.60765929997433 s`
- Resident reentry-boundary stage: `0.01057750009931624 s`
- Active/masked frames: `193/7`
- New boundary summary:
  - `pre_integration_ready=true`
  - `master_cache_boundary_ready=true`
  - `calibration_boundary_ready=true`
  - `strongest_ready_boundary=resident_calibration`
  - `strongest_supported_boundary=pre_integration_invocation`
  - `calibration_boundary_resume_supported=false`
- Stage ledger:
  - started stages: `16`
  - complete stages: `16`
  - expected artifact rows: `24`
  - missing artifact rows: `0`
  - `can_noop_resume=true`

## WBPP Black-Box Compare

- Reference elapsed: `1092.541 s`
- Speedup: `94.16770482969594x`
- Shape match: `true`
- Coverage threshold: `>=190`
- Compared pixels: `60105814`
- Coverage fraction: `0.9749333995120938`
- RMS diff: `0.0056241382952344435`
- p99 absolute diff: `0.002143551869085057`

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`

## Known Limitations

- Gate648 does not yet resume from the resident calibration boundary.
- The new boundary is ready and consumed by preflight, but
  `calibration_boundary_resume_supported=false`.
- Actual reuse of completed resident calibration/master-cache state inside a
  partially completed `resident_calibration_integration` stage remains future
  work.

## Next Step

- Implement actual reentry from `resident_calibration`, or split the monolithic
  resident calibration/integration stage so calibration, registration/warp/LN,
  and integration become independently resumable resident stages.

## Clean-Room Compliance

- This gate uses GLASS-owned code, GLASS artifacts, user-owned 200-light data,
  and user-generated WBPP black-box timing/output metadata.
- No external or proprietary implementation source was inspected or used.
- Input image directories were not modified.
