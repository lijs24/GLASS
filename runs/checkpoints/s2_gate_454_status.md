# S2-Gate 454 Status: Resident Source-DQ Execution Contract

## Gate

- Gate: S2-Gate 454
- Scope: Resident source-DQ/mask execution contract for in-memory mask streaming.
- Status: passed
- Date: 2026-06-20 local

## Completed Work

- Added resident source-DQ execution contract builders to
  `src/glass/engine/resident_source_dq.py`.
- Resident CUDA now writes `resident_source_dq_execution.json`.
- Resident CUDA validates the execution contract before writing final artifacts.
- Resident artifacts and integration outputs now include source-DQ execution
  summaries.
- `run_state.json` now records a `resident_source_dq_execution` artifact.
- Synthetic CPU-only source-DQ tests cover execution-route closure and memory
  estimates.
- Synthetic resident CUDA tests prove plan source-DQ sidecars still exclude
  finite flagged samples from the master/weight output and that the execution
  contract reports resident in-memory mask streaming.
- Real 200-light contract-parity run passed the full contract chain.

## Real 200-Light Results

- Run: `C:\glass_runs\phase2_s2_gate_454_200\contract_parity_20260620`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident source-DQ execution:
  - path: `C:\glass_runs\phase2_s2_gate_454_200\contract_parity_20260620\resident_source_dq_execution.json`
  - passed: true
  - execution route: `resident_in_memory_mask_streaming`
  - materializes calibrated+DQ cache: false
  - estimated peak batch mask bytes: 493,209,600
  - estimated all-frame mask bytes: 12,330,240,000
- Timing:
  - GLASS total elapsed: 20.921004 s
  - Gate452 contract-parity baseline: 30.900435 s
  - WBPP black-box elapsed: 1092.541 s
  - speedup vs WBPP: 52.222207x
- Frame accounting:
  - input light frames: 200
  - integrated frames: 193
  - zero-weight frames: 7
  - integration conflicts: 0
- Compare:
  - shape match: true
  - coverage fraction: 0.960863
  - RMS diff: 0.00170730
  - P99 absolute diff: 0.000457799
- Acceptance audit:
  - passed: true
  - failed checks: 0

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py tests\test_resident_cuda_run.py -k "source_dq_execution or applies_plan_source_dq_sidecar"`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_454_200\contract_parity_20260620 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration-quality-gate warn ...`
- `.venv\Scripts\python.exe -m glass.cli compare ... --out C:\glass_runs\phase2_s2_gate_454_200\contract_parity_20260620\s2_gate_454_compare.html ...`
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract ...`
- `.venv\Scripts\python.exe -m glass.cli resident-calibration-contract ...`
- `.venv\Scripts\python.exe -m glass.cli pipeline-contract ...`
- `.venv\Scripts\python.exe -m glass.cli stack-engine-contract ...`
- `.venv\Scripts\python.exe -m glass.cli acceptance-audit ...`

## Test Results

- Focused ruff: passed.
- Focused pytest: 2 passed, 67 deselected.
- Full pytest: 1079 passed in 40.94 s.

## Artifacts

- `runs/checkpoints/s2_gate_454_real_regression_summary.json`
- `runs/checkpoints/s2_gate_454_status.md`
- `C:\glass_runs\phase2_s2_gate_454_200\contract_parity_20260620\resident_source_dq_execution.json`
- `C:\glass_runs\phase2_s2_gate_454_200\contract_parity_20260620\phase2_contract_acceptance_audit_s2_gate_454.json`

## CUDA Status

- CUDA available: yes, verified by the real 200-light resident CUDA run.
- Local GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition from the
  Gate452 CUDA doctor artifact.

## Known Limitations

- The real 200-light dataset did not include source-DQ sidecars, so the real
  execution contract proves route/closure/no-cache semantics with zero invalid
  source samples. Synthetic resident CUDA tests prove finite source-DQ flagged
  samples are applied and excluded.
- This gate does not yet generate cosmetic/source-DQ masks entirely on GPU.
- The current default quality gate drift from Gate452 remains unresolved.
- Strict native StackEngine default readiness remains incomplete for resident
  CUDA; the resident path exposes StackEngine-shaped surfaces.

## Next Gate

- S2-Gate455 should move source-DQ generation closer to resident execution:
  - generate simple resident-side invalid masks for NaN/non-finite calibrated
    samples and optional cosmetic flags without large cache materialization;
  - keep CPU StackEngine source-DQ parity tests;
  - preserve the 200-light runtime/acceptance baseline.

## Clean-Room Compliance

- Compliant. This gate used only GLASS source, GLASS synthetic fixtures,
  GLASS-generated artifacts, and user-owned 200-light outputs.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
