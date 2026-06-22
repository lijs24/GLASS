# S2-Gate 467 Status: Admission-to-Native Chunk-Capacity Artifact Contract

## Gate

- Gate: S2-Gate 467
- Scope: make resident memory-admission reduced chunk capacity auditable through
  the final resident registration artifact.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Updated resident memory-admission limitations:
  - reduced chunk capacity is now described as a selected runtime constraint
    passed to native chunked matrix-warp dispatch;
  - native OOM fallback remains recorded as the runtime boundary.
- Added resident registration artifact fields:
  - `triangle_warp_batch_native_capacity_source`
  - `triangle_warp_batch_native_max_chunk_capacity_frames`
- Preserved high-level artifact fields:
  - `triangle_warp_batch_capacity_source`
  - `triangle_warp_batch_requested_chunk_capacity_frames`
  - `triangle_warp_batch_effective_chunk_capacity_frames`
- Updated both resident triangle-warp aggregation paths to carry native
  `batch_capacity_source` and `batch_max_chunk_capacity_frames` from the
  timing payload into the artifact.
- Added focused tests for admission wording and native-preferred artifact
  evidence.
- Updated Phase 2 documentation and the algorithm-source matrix.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Multiprocessors: 188.
- Driver version from device list: 596.21.

## Validation

- Focused admission test:
  - reduced-capacity admission still selects chunk capacity `4` for the
    constrained fixture;
  - limitations include native matrix-warp dispatch wording;
  - obsolete `allocator-driven` wording is rejected.
- Focused CUDA CLI test:
  - default triangle warp batch remains chunked;
  - high-level capacity source is `native_preferred`;
  - native capacity source is `native_preferred`;
  - native max chunk capacity is `0` for the unforced default path.
- Resident/CLI regression passed.
- Full pytest passed.

## Real 200-Light Baseline

- A new 200-light run was not launched for this gate.
- Reason: C: had only about `0.369 GiB` free during validation.
- This gate changes artifact contract fields and admission wording only; it
  does not change CUDA pixel math, native allocation behavior, registration
  fitting, rejection, integration, or default dispatch.
- Applicable baseline remains S2-Gate465:
  - run:
    `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622`
  - input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat;
  - internal GLASS timing: `36.103794 s`;
  - outer PowerShell timing: `36.485266 s`;
  - WBPP black-box timing: `1092.541 s`;
  - speedup vs WBPP: `30.261113x`;
  - native chunk frames: `8`;
  - native chunk count: `24`;
  - capacity source: `native_preferred`;
  - compare RMS diff: `0.00170058`;
  - P99 absolute diff: `0.000459801`;
  - coverage fraction: `0.961043`.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_memory_admission_recommends_reduced_chunk_capacity tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused pytest: `2 passed in 0.92s`.
- Resident/CLI pytest: `104 passed in 14.02s`.
- Full pytest: `1101 passed in 47.37s`.

## Artifacts

- `runs/checkpoints/s2_gate_467_native_capacity_contract_summary.json`
- `runs/checkpoints/s2_gate_467_status.md`

## Known Limitations

- Gate467 makes native capacity evidence auditable, but does not reduce
  per-chunk launch overhead.
- A new 200-light output run was skipped because C: free space was too low.
- The next substantive gate should target resident registration/warp
  orchestration performance or DQ/mask default-path behavior.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, summarized, copied, or used.
- WBPP evidence remains limited to user-generated black-box timing/output
  artifacts from earlier accepted baselines.
- User image input directories were not modified.
