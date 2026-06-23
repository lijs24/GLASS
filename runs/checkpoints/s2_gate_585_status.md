# S2-Gate 585 Status: StackEngine Default Guard Requires Resident DQ Ledger

## Gate

- Gate: `S2-Gate 585`
- Status: `green`
- Date: `2026-06-23`

## Completed

- Added pipeline-contract DQ ledger awareness to `glass stack-engine-contract`.
- Resident CUDA StackEngine surfaces can still pass the core StackEngine
  contract through resident calibration/result contracts, but
  `default_promotion.ready` now requires a passing pipeline-contract
  `frame_accounting_resident_dq_ledger_contract`.
- Added `--pipeline-contract-json` to `glass stack-engine-contract`; the command
  also auto-discovers `pipeline_contract.json` from the run directory.
- Added tests for:
  - resident default-ready with a passing pipeline DQ ledger;
  - resident default-ready blocked when the pipeline DQ ledger is missing;
  - resident default-ready blocked when the pipeline DQ ledger fails;
  - CLI explicit and run-default pipeline-contract discovery.
- Updated Phase 2 documentation and algorithm-source independence log.

## Real 200-Light Evidence

- Source GLASS run:
  `C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3`
- Pipeline DQ ledger evidence:
  `C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.json`
- Gate585 output directory:
  `C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard`
- StackEngine contract:
  `C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\stack_engine_contract.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\acceptance_audit.json`

## Real Validation Results

- StackEngine contract status: `passed`
- Default-promotion status: `ready`
- Pipeline DQ ledger ready: `true`
- Resident DQ ledger rows: `200 / 200`
- Ledger sources: `resident_source_dq_execution`
- Ledger frame-mask sources: `resident_frame_masks`
- Acceptance audit status: `passed`
- GLASS elapsed: `8.19045490003191 s`
- Speedup versus WBPP black-box reference: `133.39198046200627x`
- Coverage190 fraction: `0.905523489118409`
- RMS difference versus WBPP reference: `0.005340835487175878`
- p99 absolute difference versus WBPP reference: `0.002133606873685496`

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\stack_engine_contract.py src\glass\cli.py tests\test_stack_engine_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_contract.py -k "pipeline_dq_ledger or resident_calibration_for_default_ready or cli_uses_resident_calibration or auto_discovers_native_resident_calibration"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_contract.py`
- `.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --scope all --expected-integration-engine cuda_resident_stack --pipeline-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.json --out C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\stack_engine_contract.md --require-default-ready`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3\manifest.json --glass-run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\compare_vs_wbpp_fastintegration_scaled_coverage190.json --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\warp_quality_contract.json --require-warp-quality-contract --out C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate585_stackengine_dq_default_guard\acceptance_audit.md`
- `.venv\Scripts\python.exe - << capability_report probe`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused StackEngine/DQ tests: `5 passed, 12 deselected`
- Full StackEngine contract tests: `17 passed`
- Full pytest: `1252 passed in 52.38s`

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
- This gate does not optimize resident registration/warp or read/upload
  scheduling.
- The resident CUDA path remains a StackEngine-compatible resident surface; it
  is not strict native CPU StackEngine default according to
  `--require-native-stack-engine-default`.
- Real validation reuses the Gate582 run and Gate584 pipeline/compare evidence
  rather than rerunning the full 200-light CUDA pipeline from raw frames.

## Next Step

- Continue the Phase 2 mainline with a substantive gate on the actual runtime
  path: either make the default run emit this StackEngine/pipeline evidence
  bundle automatically during `glass run`, or advance resident registration/warp
  resident execution while preserving the now-required DQ/default-readiness
  contracts.

## Clean-Room

- Compliant. This gate consumes only GLASS-generated artifacts, user-owned GLASS
  run outputs, and user-generated WBPP black-box timing/reference outputs.
- No external implementation source was read or copied.
- Input image directories were not modified.
