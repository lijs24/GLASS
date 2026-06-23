# S2-Gate 561 Status: Resident LN Frame-Accounting Closure

## Gate

S2-Gate 561: make resident in-VRAM local-normalization rows close against
`frame_accounting.json` so default resident StackEngine/LN runs cannot pass
contracts with a mismatched normalized/integrated frame set.

## Completed

- Added `frame_accounting_closure` to resident `local_norm_contract.json`.
- Required LN-enabled resident contracts to validate:
  - LN output row count equals input light-frame count;
  - active LN statuses (`reference`, `ok`, `partial`, `offset_only`) equal
    integrated frame count;
  - zero-weight LN statuses (`empty`, `skipped_zero_weight`) equal zero-weight
    integration count;
  - LN frame ids are unique and present in `frame_accounting.json`;
  - per-frame LN status agrees with the frame-accounting integration status.
- Kept resident LN-off explicit and non-blocking as `not_required`.
- Added focused unit coverage for passing active rows, passing zero-weight rows,
  and a deliberate frame-count drift failure.
- Extended `local_norm_contract.md` with frame-accounting closure summary.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\report\local_norm_contract.py tests\test_local_norm_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py tests\test_pipeline_contract.py::test_pipeline_contract_accepts_resident_local_norm_group_rows tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization on --resident-local-normalization-mode grid_mean_std --resident-local-normalization-tile-size 256 --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --out C:\glass_runs\phase2_s2_gate561_resident_ln_frame_accounting\runs_20260623_180404\ln_on_closure`

## Test Results

- Focused LN contract tests: `10 passed in 0.26 s`.
- Focused resident LN/pipeline smoke tests: `13 passed in 0.78 s`.
- Full pytest: `1199 passed in 44.85 s`.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate561_resident_ln_frame_accounting\runs_20260623_180404\ln_on_closure`.
- Baseline for output comparison:
  `C:\glass_runs\phase2_s2_gate560_resident_ln_contract\runs_20260623_175507\ln_on_contract`.
- Checkpoint summary:
  `runs/checkpoints/s2_gate_561_resident_ln_frame_accounting_summary.json`.
- Shell elapsed: `7.1862375 s`.
- Run timing total: `6.819454700045753 s`.
- LN contract status: `passed`.
- Pipeline contract status: `passed`.
- Frame-accounting closure: `passed`.
- Frame counts: `200` input light frames, `193` integrated frames,
  `7` zero-weight frames.
- LN rows: `200` total, `193` active, `7` zero-weight.
- LN status counts: `109 ok`, `83 partial`, `1 reference`,
  `7 skipped_zero_weight`.
- Output comparison to Gate560 LN-on:
  master, weight map, coverage map, low-rejection map, high-rejection map, and
  DQ map SHA256 hashes all match exactly.

## CUDA

- CUDA extension importable: yes.
- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- This gate is an engineering-contract gate. It does not change LN formulas,
  CUDA kernels, calibration, registration, warp, rejection, weighting, DQ bit
  definitions, frame admission, or output pixels.
- The closure proves resident LN rows and integration frame accounting agree;
  it does not decide whether each rejected frame is scientifically optimal.

## Next Step

Return to the Phase 2 substantive mainline: use the now-closed default
resident contract surface to harden StackEngine default-path behavior and DQ
mask propagation on real 200-light regression runs, then target resident
registration/warp orchestration where the largest remaining runtime is.

## Clean-Room Compliance

Compliant. This gate consumes only GLASS-generated `local_norm_results.json`,
`frame_accounting.json`, pipeline contracts, unit fixtures, and user-owned
200-light run artifacts. It does not inspect external proprietary source,
modify input image directories, or copy external algorithms.
