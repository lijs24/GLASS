# S2 Gate 595 Status: Winsorized Master-Cache Fast Path And Real A/B

## Gate

- Gate: S2-Gate 595
- Title: Winsorized Master-Cache Fast Path And Real A/B
- Date: 2026-06-24
- Status: passed

## Completed

- Added an all-valid finite fast path for `winsorized_sigma` StackEngine statistics.
- The fast path uses sorted frame-axis percentiles with linear interpolation and avoids nan-stat reductions when every tile sample is valid and finite.
- DQ-masked and non-finite tiles still use the previous nan-safe implementation.
- Added tests proving the fast path matches the previous nan-stat reference and that StackEngine still rejects an all-valid high outlier stack.
- Ran real 200-light cold/warm v2 master-cache A/B after Gate594's policy correction.
- Generated compare and acceptance artifacts against the WBPP black-box fastIntegration reference.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine.py::test_winsorized_sigma_all_valid_fast_path_matches_nan_reference tests\test_stack_engine.py::test_cpu_stack_engine_winsorized_all_valid_rejects_outlier tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\rejection.py tests\test_stack_engine.py`
- Synthetic microbenchmark script writing `C:\glass_runs\phase2_s2_gate595_real_master_rejection_ab\winsorized_all_valid_microbenchmark.json`
- Real 200-light `glass run` cold v2 with shared `resident_master_cache_v2_fast`
- Real 200-light `glass run` warm v2 using the same shared cache
- `glass compare` against the WBPP black-box fastIntegration reference for cold and warm v2 outputs
- `glass acceptance-audit` with `benchmarks\phase2_m38_h_200_ln_on_default_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused StackEngine/resident tests: `5 passed`
- Ruff: `All checks passed`
- Full pytest: `1266 passed in 52.15s`

## Synthetic Microbenchmark

- Artifact: `C:\glass_runs\phase2_s2_gate595_real_master_rejection_ab\winsorized_all_valid_microbenchmark.json`
- Stack shape: `20 x 512 x 512`
- Old nan-stat reference: `10.096058700000867 s`
- New all-valid fast path: `0.08853980002459139 s`
- Speedup: `114.02847868638453x`
- Center max abs diff: `3.0517578125e-05`
- Scale max abs diff: `9.5367431640625e-07`
- Status: passed

## Real 200-Light Results

- Root: `C:\glass_runs\phase2_s2_gate595_real_master_rejection_ab`
- Pre-fast-path probe:
  - run dir: `cold_default_v2`
  - stopped after about `10` minutes
  - cache files written: `0`
  - interpretation: existing CPUStackEngine winsorized path was too slow for real cold-cache default use
- Cold v2 fast-path run:
  - run dir: `cold_default_v2_fast`
  - total elapsed: `122.64545549999457 s`
  - resident calibration/integration: `121.80481859995052 s`
  - cache hits/misses: `0 / 1`
  - v2 cache bytes: `739860125`
  - speedup vs WBPP reference: `8.908124606378491x`
  - compare RMS: `0.005316389020057793`
  - compare p99 abs diff: `0.002127066696993994`
- Warm v2 fast-path run:
  - run dir: `warm_default_v2_fast`
  - total elapsed: `8.189881100086495 s`
  - resident calibration/integration: `7.356546199996956 s`
  - cache hits/misses: `1 / 0`
  - speedup vs WBPP reference: `133.40132617901637x`
  - compare RMS: `0.005316389020057793`
  - compare p99 abs diff: `0.002127066696993994`
  - acceptance audit: passed
- Cold/warm hash parity:
  - artifact: `C:\glass_runs\phase2_s2_gate595_real_master_rejection_ab\cold_warm_hash_parity.json`
  - result: `6 / 6` integration FITS outputs SHA256-identical
- Summary:
  - `C:\glass_runs\phase2_s2_gate595_real_master_rejection_ab\gate595_summary.json`

## CUDA

- CUDA available: yes
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Native backend: true

## Known Limitations

- Cold-cache corrected robust master construction is still too slow for the default benchmark performance contract: `8.908124606378491x` versus the `20x` requirement.
- Warm-cache v2 output passes acceptance at `133.40132617901637x`, and cold/warm outputs are bit-identical.
- The next performance-critical gap is a resident CUDA robust master-frame reduction or further optimized CPU tiled robust reduction.

## Next Step

- Implement CUDA resident robust master reductions for all-valid calibration stacks first, then extend DQ/non-finite handling.
- Re-run the real 200-light cold-cache benchmark and require it to pass the default speed contract while preserving the v2 warm-cache output.

## Clean-Room Compliance

- This gate uses GLASS-owned StackEngine/rejection code, GLASS synthetic arrays, GLASS-generated run artifacts, user-owned 200-light inputs, and user-generated WBPP black-box outputs.
- No proprietary or external implementation source was read, copied, summarized, or reworked.
- Input image directories remained read-only.
