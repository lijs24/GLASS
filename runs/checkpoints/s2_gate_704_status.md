# S2 Gate 704 Status: Default Compact Unit-Weight Active Indices

## Gate

- Gate: S2-Gate 704
- Date: 2026-06-26
- Status: green
- Branch: `main`
- Goal area: resident CUDA hardened winsorized integration performance on the
  real 200-light mainline route.

## Completed Content

- Promoted compact active-frame indices as the default native resident
  hardened winsorized path for unit-positive `0/1` integration weights when at
  least one frame is inactive and no explicit unit-positive reuse environment
  branch is requested.
- Preserved explicit diagnostics and rollback:
  - `GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=1` still explicitly enables the active
    index path.
  - `GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=0` disables the new default and
    restores the previous frame-mask default.
  - Explicit mask, selected-reuse, and index-select probe variables keep
    precedence.
- Added native profile fields distinguishing default admission from explicit
  environment admission:
  - `unit_positive_active_index_default_enabled`
  - `unit_positive_active_index_env_present`
  - `unit_positive_active_index_env_enabled`
  - `unit_positive_active_index_reason`
- Updated CUDA resident stack tests for the new default route and the explicit
  env-disable fallback.
- Updated documentation:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/integration_model.md`
  - `docs/algorithm_sources.md`

## Commands Run

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8'
```

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py -k "hardened_winsorized or resident_cuda_hardened_winsorized or unit_weight"
```

```powershell
.venv\Scripts\python.exe -m ruff check tests/test_cuda_resident_stack.py
```

```powershell
.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\active_index_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
```

```powershell
.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\active_index_candidate --out C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\gate704_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\gate704_mainline_audit.md --fail-on-not-green
```

```powershell
.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\post_reference_health_candidate --candidate-run C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\active_index_candidate --out C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\gate704_vs_gate703_regression.json --markdown C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\gate704_vs_gate703_regression.md --max-elapsed-ratio 1.05 --fail-on-failure
```

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native CUDA target rebuild: passed.
- Focused resident hardened winsorized tests: `31 passed, 192 deselected in 1.42 s`.
- Ruff over touched Python tests: passed.
- Full pytest: `1451 passed in 72.77 s`.
- Phase 2 mainline audit: passed.
- Resident regression gate versus Gate703: passed.
- Regression determinism summary:
  - `artifact_difference_count=0`
  - `frame_accounting_difference_count=0`
  - `frame_signature_difference_count=0`
  - `output_difference_count=0`
  - `output_numerical_drift_count=0`
  - `registration_difference_count=0`

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver version: `596.21`
- Native backend loaded: yes.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\active_index_candidate`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\post_reference_health_candidate`
- Input lights: `200`
- Active frames: `193`
- Masked frames: `7`

| Metric | Gate703 mask default | Gate704 active-index default |
| --- | ---: | ---: |
| Total elapsed | `11.912095099687576 s` | `11.090906699886546 s` |
| Resident calibration + integration | `10.474013799917884 s` | `9.755395399988629 s` |
| Light read/upload/calibrate | `3.161170899984427 s` | `3.101156600052491 s` |
| Resident integration | `3.2807693999493495 s` | `2.6184026999399066 s` |
| Native hardened kernel sync | `3.1383918 s` | `2.4904286 s` |
| Resident registration/warp | `0.27185329992789775 s` | `0.2694594005588442 s` |
| Resident local normalization | `0.3781815000111237 s` | `0.37058149999938905 s` |

Gate704 profile highlights:

- `sample_reuse_strategy=active_index_global_reread_unit_positive_weights`
- `unit_positive_weights_fast_path=true`
- `unit_positive_active_index_default_enabled=true`
- `unit_positive_active_index_reason=default_compacted_unit_positive_weight_indices`
- `unit_positive_active_frame_count=193`
- `unit_positive_weight_frame_count=193`
- `unit_positive_weight_mask_enabled=false`
- `unit_positive_weight_mask_bytes=0`

## Known Limitations

- The new default applies only to resident hardened winsorized integration with
  unit-positive `0/1` weights and a strict inactive-frame subset.
- Non-unit weighting, over-512 cooperative selection, calibration I/O/H2D
  overlap, registration batching, and broader StackEngine unification are not
  solved by this gate.
- The real-data timing is a single warm 200-light validation and should be kept
  under future A/B monitoring because Windows file-cache and GPU scheduling
  variance can still affect totals.

## Next Step

- Use Gate704 as the new resident integration baseline.
- The next substantive gate should target either:
  - resident light read/upload/calibrate overlap with pinned-memory double or
    multi-buffer scheduling, or
  - a larger cooperative resident winsorized reducer that reduces repeated
    per-pixel order-statistic/statistics work.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA wrapper logic, GLASS CPU/GPU parity tests,
  synthetic probes, and user-owned real benchmark artifacts.
- No external proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
