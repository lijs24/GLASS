# S2-Gate 586 Status: Default Run Auto StackEngine DQ Contract

## Gate

- Gate: `S2-Gate 586`
- Status: `green`
- Date: `2026-06-23`

## Completed

- Resident CUDA `glass run` now emits `stack_engine_contract.json` and
  `stack_engine_contract.md` automatically after `pipeline_contract.json`.
- The automatic StackEngine contract uses
  `expected_integration_engine=cuda_resident_stack` and auto-discovers the
  run-local `pipeline_contract.json`, so Gate585's resident DQ ledger guard is
  enforced without a manual follow-up command.
- `run_state.json` records a `stack_engine_contract` artifact.
- Normal resident runs fail if the StackEngine contract or default-promotion DQ
  proof is missing, while tiny diagnostic runs keep the existing non-blocking
  small-frame allowance.
- `glass guardrails` now builds pipeline evidence before StackEngine evidence
  and passes the same pipeline payload into StackEngine contract construction.

## Real 200-Light Evidence

- Fresh run:
  `C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract`
- Hash parity:
  `C:\glass_runs\phase2_s2_gate586_auto_stack_contract\hash_parity_vs_gate582.json`
- Compare:
  `C:\glass_runs\phase2_s2_gate586_auto_stack_contract\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate586_auto_stack_contract\acceptance_audit.json`

## Real Validation Results

- Run current stage: `integration`
- Run failed stage: `None`
- Run artifact tail includes: `local_norm_contract`, `pipeline_contract`,
  `stack_engine_contract`
- Stage timing sum: `7.862576000043191 s`
- Automatic StackEngine contract stage timing: `0.026758700027130544 s`
- Pipeline contract: `passed`, `24` checks
- Resident DQ ledger rows: `200 / 200`
- Resident DQ ledger passed/failed rows: `200 / 0`
- Resident DQ ledger sources: `resident_source_dq_execution`
- Resident DQ frame-mask sources: `resident_frame_masks`
- StackEngine contract: `passed`
- StackEngine default promotion: `ready`
- StackEngine pipeline source: `run_default`
- Six integration FITS outputs match Gate582 SHA256 values: `true`
- Compare speedup versus WBPP black-box fastIntegration: `138.95458689289595x`
- Coverage190 fraction: `0.905523489118409`
- RMS difference versus WBPP reference: `0.005340835487175878`
- p99 absolute difference versus WBPP reference: `0.002133606873685496`
- Acceptance audit: `passed`

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_cuda_run_similarity_triangle_aligns_shifted_pair"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py -k "guardrails_generates_contracts_and_report"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- SHA256 parity script comparing Gate586 integration FITS outputs against Gate582.
- `.venv\Scripts\glass.exe compare ... --glass C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract\integration\resident_master_H.fits --glass-coverage-map C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract\manifest.json --glass-run C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate586_auto_stack_contract\compare_vs_wbpp_fastintegration_scaled_coverage190.json --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate586_auto_stack_contract\default_auto_contract\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\warp_quality_contract.json --require-warp-quality-contract --out C:\glass_runs\phase2_s2_gate586_auto_stack_contract\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate586_auto_stack_contract\acceptance_audit.md`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: `passed`
- Focused resident run test: `1 passed, 103 deselected`
- Focused guardrails test: `1 passed, 69 deselected`
- Full StackEngine contract tests: `17 passed`
- Source-DQ cache route regression: `1 passed`
- Full pytest: `1252 passed in 53.27s`

## CUDA

- CUDA available: `true`
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Total memory: `97886 MiB`
- Driver version: `596.21`
- CUDA extension importable: `true`

## Known Limitations

- This gate does not change calibration, registration, warp, LN, rejection, or
  integration pixel math.
- This gate does not optimize runtime; it adds a small automatic contract stage
  to make default-run evidence self-contained.
- The warp-quality contract used by acceptance is the existing Gate584
  resident in-VRAM warp-quality evidence because the automatic run contract
  work in this gate targets pipeline and StackEngine default-readiness, not
  warp-quality auto-emission.

## Next Step

- Continue Phase 2 on substantive runtime completeness: either auto-emit
  resident warp-quality evidence from default runs, or return to resident
  registration/warp GPU-resident throughput and numerical consistency while
  preserving the now self-contained pipeline/StackEngine DQ contract chain.

## Clean-Room

- Compliant. This gate consumes only GLASS-generated artifacts, user-owned
  200-light inputs/outputs, and user-generated WBPP black-box timing/reference
  outputs.
- No external implementation source was read or copied.
- Input image directories were not modified.
