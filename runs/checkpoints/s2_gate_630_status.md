# S2-Gate 630 Status: Mask-Scan Repeat Rejection And Env Guard

## Gate

S2-Gate 630 closes the Gate629 mask-scan promotion question with real repeat
evidence and a small native runtime guard.

## Completed

- Ran three paired real 200-light default/mask-scan repeats with the same plan,
  resident master cache, audit-map policy, and CUDA backend.
- Ran resident regression gates for each pair.
- Rejected default promotion of `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN` because the
  hardened reducer itself was consistently slower even though total elapsed
  time was lower in the paired runs.
- Hardened the native C++ environment parser so
  `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN` enables the experiment only for explicit
  true values: `1`, `true`, `yes`, or `on`.
- Values such as `auto` now leave the default path active and record
  `unit_positive_weight_mask_reason=ignored_unrecognized_env_value`.
- Switched the mask-scan env read to the same Windows-safe `_dupenv_s` helper
  used by other native experiment flags.
- Added a focused CUDA test proving `auto` does not enable the unpromoted path.
- Updated Phase 2 documentation, integration model, known limitations, and
  algorithm source ledger.

## Code Changes

- `cpp/src/native_bindings.cpp`
- `tests/test_cuda_resident_stack.py`
- `docs/integration_model.md`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `docs/known_limitations.md`

## Commands Run

```powershell
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits

# Real 200-light repeat matrix, three default/mask-scan pairs.
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\<variant>_r<N> --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\default_r1 --candidate-run C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\mask_scan_r1 --out C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\regression_default_r1_vs_mask_r1.json --markdown C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\regression_default_r1_vs_mask_r1.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\default_r2 --candidate-run C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\mask_scan_r2 --out C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\regression_default_r2_vs_mask_r2.json --markdown C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\regression_default_r2_vs_mask_r2.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\default_r3 --candidate-run C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\mask_scan_r3 --out C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\regression_default_r3_vs_mask_r3.json --markdown C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\regression_default_r3_vs_mask_r3.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

cmd.exe /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8"
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_auto_is_not_enabled tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_default_off
git diff --check
.\.venv\Scripts\ruff.exe check cpp src tests docs --select E,F --ignore E501
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native build: passed.
- Focused CUDA env-guard tests: `3 passed`.
- Ruff: `All checks passed!`
- Full pytest: `1324 passed in 57.67s`.

## Real 200-Light Repeat Evidence

- Repeat batch:
  `C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142`
- Repeat summary:
  `C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\gate630_repeat_summary.json`
- Markdown summary:
  `C:\glass_runs\phase2_s2_gate630_mask_scan_repeat\runs_20260625_135142\gate630_repeat_summary.md`

Pairwise regression gates:

- r1: passed, elapsed ratio `0.9750897233280544`, zero output differences,
  zero numerical drift.
- r2: passed, elapsed ratio `0.9869597641504888`, zero output differences,
  zero numerical drift.
- r3: passed, elapsed ratio `0.8852464975146617`, zero output differences,
  zero numerical drift.

Repeat statistics:

- Pair count: `3`.
- Mask total-time wins: `3`.
- Hardened-total wins: `0`.
- Kernel-sync wins: `0`.
- Total elapsed mean ratio: `0.9467959733011961`.
- Total elapsed median ratio: `0.9761950500020543`.
- Hardened total mean ratio: `1.0079091197710124`.
- Hardened total median ratio: `1.0086009065859771`.
- Native kernel sync mean ratio: `1.0063806007728684`.
- Native kernel sync median ratio: `1.0066921331048393`.

Interpretation: mask-scan should not be promoted. Its total-time wins are not
supported by the measured reducer timings and are more plausibly from
surrounding runtime/I/O variance.

## CUDA Availability

- CUDA available to GLASS: yes.
- Native backend: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- SM count: `188`.

## Known Limits

- `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN` remains an opt-in diagnostic path.
- This gate does not improve the resident hot path; it prevents a misleading
  micro-optimization from becoming the default.
- The next performance target should be the measured bottleneck:
  - bounded hardened winsorized reducer kernel structure; or
  - resident read/H2D/calibration bandwidth, especially
    `native_h2d_calibrate_store`.

## Next Step

Start S2-Gate 631 on a substantive hot-path optimization. The recommended
direction is either a real kernel-side hardened reducer improvement that beats
the current quickselect/global-reread path, or a resident calibration bandwidth
experiment that reduces `native_h2d_calibrate_store` without changing output
pixels.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA runtime code, GLASS unit tests,
GLASS-generated repeat artifacts, and user-owned 200-light benchmark data. It
does not inspect external implementation source, use proprietary behavior,
modify input directories, or copy external algorithms.
