# S2-Gate 584 Status: Frame Accounting Resident DQ Contract

## Gate

- Gate: S2-Gate 584
- Title: Frame accounting resident DQ contract
- Status: green
- Date: 2026-06-23

## Completed Content

- Added `frame_accounting_resident_dq_ledger_contract` to
  `pipeline-contract`.
- The new contract compares resident calibrated-light DQ/mask rows against
  `frame_accounting.json` summary and per-frame rows:
  - resident DQ contract row count;
  - passed and failed resident DQ contract counts;
  - resident source-DQ contract row count;
  - resident frame-mask contract row count;
  - missing and extra frame ids;
  - per-frame pass/fail flags;
  - summary-level and per-frame contract sources;
  - summary-level and per-frame frame-mask sources.
- Added `frame_accounting_resident_dq_ledger` to pipeline-contract JSON output.
- Added a `Frame Accounting Resident DQ Ledger` section to pipeline-contract
  Markdown.
- Updated the default 200-light benchmark contracts to require
  `frame_accounting_resident_dq_ledger_contract`.
- Added passing and failing unit coverage for resident DQ ledger drift.
- Updated Phase 2 documentation and algorithm-source independence log.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "frame_accounting or resident_calibrated_light_dq or resident_native_calibration_artifacts or synthesizes_resident_calibration"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py -k "pipeline_contract or benchmark_contract or required_check"`
- `.venv\Scripts\python.exe -m py_compile src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --out C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.md --pixel-verify`
- `.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --out C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\stack_engine_contract.md --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3\resident_calibration_contract.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3\resident_result_contract.json --require-default-ready`
- `.venv\Scripts\glass.exe warp-quality-contract --run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --out C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\warp_quality_contract.json --markdown C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\warp_quality_contract.md --min-valid-fraction 0.90 --max-skipped-frames 7 --require-all-registered --fail-on-failed`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 8.19045490003191 --reference-time-seconds 1092.541 --glass-label "GLASS Gate582 default resident" --reference-label "WBPP black-box fastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3\manifest.json --glass-run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\compare_vs_wbpp_fastintegration_scaled_coverage190.json --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\warp_quality_contract.json --require-warp-quality-contract --out C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\acceptance_audit.md`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused pipeline-contract tests: `6 passed, 39 deselected`
- Full pipeline-contract tests: `45 passed in 1.64s`
- Focused acceptance-audit tests: `8 passed, 42 deselected`
- Ruff: `All checks passed!`
- Py compile: passed
- Full pytest: `1250 passed in 50.24s`

## Real 200-Light Validation

- Source run:
  `C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3`
- Evidence directory:
  `C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract`
- Pipeline contract:
  `C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\pipeline_contract.json`
- Pipeline-contract status: `passed`
- New check:
  `frame_accounting_resident_dq_ledger_contract`
- New check status: required `True`, passed `True`
- Expected/accounting resident DQ rows: `200 / 200`
- Expected passed/failed resident DQ rows: `200 / 0`
- Missing/extra/failed frame ids: none
- Contract sources: `resident_source_dq_execution`
- Frame-mask sources: `resident_frame_masks`
- StackEngine contract: passed and default-promotion ready
- Warp-quality contract: passed, `193` outputs and `7` skipped frames
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate584_frame_accounting_dq_contract\acceptance_audit.json`
- Acceptance status: `passed`
- Acceptance proof for new required check:
  `contract_pipeline_contract_check:frame_accounting_resident_dq_ledger_contract`
  passed
- Speedup versus WBPP black-box reference: `133.39198046200627x`

## CUDA Status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Driver version: 596.21
- VRAM: 97886 MiB

## Known Limitations

- This gate enforces a pipeline invariant over existing resident DQ artifacts.
- It does not add new DQ detection, change frame admission, change
  registration/warp/LN/rejection/integration math, or optimize runtime.
- The check is authoritative when resident calibrated-light DQ row contracts
  exist. Older artifacts without those rows remain reportable through earlier
  compatibility paths.

## Next Step

- Continue substantive Phase 2 work toward StackEngine default-path completion
  and resident CUDA numerical/performance hardening. The next gate should avoid
  release-only or report-only work unless it directly protects default-path
  science or DQ/mask invariants.

## Clean-Room Compliance

- Compliant. This gate uses only GLASS-generated resident calibration,
  source-DQ, frame-mask, frame-accounting, integration, pipeline-contract,
  StackEngine, warp-quality, compare, and acceptance artifacts.
- No external stacking implementation source was read, summarized, copied, or
  reworked.
- Input image directories were treated as read-only.
