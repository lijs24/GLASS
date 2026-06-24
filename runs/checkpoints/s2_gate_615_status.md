# S2-Gate 615 Status: Resident Grid-LN Batch Apply

## Gate

- Gate: S2-Gate 615
- Status: green
- Branch: `main`
- Date: 2026-06-25

## Completed Contents

- Added native resident CUDA batch apply API:
  `ResidentCalibratedStack.apply_grid_normalization_frames(...)`.
- Added Python wrapper:
  `glass_cuda.ResidentCalibratedStack.apply_grid_normalization_frames(...)`.
- Updated the default resident `grid_mean_std` local-normalization path to batch
  all active non-reference frame apply calls when the native API is available.
- Preserved the existing per-tile formula: `value * scale + offset`.
- Added diagnostic fallback switch:
  `GLASS_RESIDENT_LN_BATCH_APPLY=0`.
- Added artifacts:
  - per-frame `application_profile.mode = in_place_device_update_batch`;
  - group `application.batch_apply_frame_count`;
  - group/resident `grid_apply.supported`, `enabled`, `available`,
    `batched`, and `profile`.
- Added/updated CUDA and CLI tests for batch apply and env-disabled fallback.
- Updated Phase 2 docs, algorithm-source log, local-normalization model, and
  known limitations.

## Real 200-Light Evidence

- Default batch run:
  `C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_default_regression`
- Same-build per-frame fallback run:
  `C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_per_frame_same_build`
- Passing regression gate:
  `C:\glass_runs\phase2_s2_gate615_ln_batch_apply\resident_regression_gate_batch_vs_per_frame_same_build.json`
- Markdown report:
  `C:\glass_runs\phase2_s2_gate615_ln_batch_apply\resident_regression_gate_batch_vs_per_frame_same_build.md`

Key results:

- Regression gate passed.
- Candidate/per-frame elapsed ratio: `0.9886661545335146`.
- Determinism differences: artifact `0`, frame signatures `0`,
  registration `0`, frame accounting `0`, output pixels `0`, numerical drift
  `0`.
- Frame admission: `193 / 200` active, `7` masked.
- Batch apply normalized `192` non-reference frames.
- Batch coefficient bytes: `1,517,568`.
- Resident frame-bytes touched by batch apply: `47,348,121,600`.
- LN apply profile:
  - per-frame same-build fallback: `0.11815519999999992 s`;
  - batch apply: `0.066252 s`.
- Whole resident LN timing:
  - per-frame same-build fallback: `0.4328185999765992 s`;
  - batch apply: `0.3605515999952331 s`.

The older Gate614 comparison is recorded at
`C:\glass_runs\phase2_s2_gate615_ln_batch_apply\resident_regression_gate_vs_gate614.json`.
It fails only `resident_determinism_passed` with the same sparse output-map
drift observed when the same-build per-frame fallback is compared to Gate614:
`output_difference_count=1`, `output_numerical_drift_count=5`, max relative RMS
`0.00045132056254550053`. Because the same-build batch-vs-per-frame comparison
has zero drift, this is attributed to the intervening native rebuild/runtime
environment rather than the Gate615 batch apply path.

## Commands Run

- Native CUDA rebuild:
  `cmake --build build\native-cuda --config Release --target _glass_cuda_native`
- CUDA capability probe:
  `python -c "import glass_cuda; ..."`
- Focused tests:
  - `python -m pytest -q tests\test_cuda_resident_stack.py -k "normalization or grid_stats"`
  - `python -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_grid_ln_batch_apply_can_be_disabled`
  - `python -m pytest -q tests\test_resident_cuda_run.py -k "ncc_subpixel_registration_smoke or grid_ln_batch_apply_can_be_disabled or resident_dq_map_count_maps_native or resident_dq_map_native"`
  - `python -m pytest -q tests\test_pipeline_contract.py tests\test_local_norm_contract.py`
- Lint:
  `python -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- Real default batch run:
  `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Same-build per-frame fallback run:
  `GLASS_RESIDENT_LN_BATCH_APPLY=0 glass run ... --out C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_per_frame_same_build ...`
- Passing A/B:
  `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_per_frame_same_build --candidate-run C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_default_regression --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full test suite:
  `python -m pytest -q`
- Diff hygiene:
  `git diff --check`

## Test Results

- `tests/test_cuda_resident_stack.py -k "normalization or grid_stats"`:
  `5 passed, 51 deselected`.
- Two focused resident CLI tests: `2 passed`.
- Broader resident CUDA focused set: `7 passed, 109 deselected`.
- Pipeline/local-normalization contracts: `57 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1295 passed in 53.27 s`.
- `git diff --check`: no whitespace errors; only CRLF conversion warnings.

## CUDA

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Multiprocessors: `188`.
- Driver: `596.21`.
- Native backend: available.

## Known Limits

- Gate615 reduces apply dispatch/upload/sync overhead but does not move
  coefficient construction out of Python yet.
- Remaining high-value Phase 2 targets are resident registration/warp batching,
  deeper coefficient/native scheduling, and larger-frame robust CUDA reduction.
- The older Gate614 A/B remains a diagnostic artifact, not the blocking
  Gate615 acceptance comparison, because it crosses a native rebuild boundary.

## Clean-Room Compliance

- Input image directories were read-only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- The implementation is derived from GLASS-owned CUDA/runtime code, GLASS
  artifact contracts, GLASS tests, and user-owned benchmark outputs.

## Next Step

- Return to the substantive Phase 2 mainline: resident registration/warp
  batching and reduced Python orchestration around star catalog, descriptor,
  transform, and warp scheduling.
