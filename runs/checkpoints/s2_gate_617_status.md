# S2-Gate 617 Status: Resident Pipelined Warp Guard

## Gate

- Gate: S2-Gate 617
- Status: green
- Branch: `main`
- Date: 2026-06-25

## Completed Contents

- Added explicit CUDA stream launch wrappers for resident batch matrix warp and
  scatter/scatter-reduce kernels.
- Added native/Python experimental `pipelined` resident batch matrix-warp
  dispatch.
- Added safety guards after real 200-light negative validation:
  - Python wrapper rejects `dispatch="pipelined"` with `track_coverage=True`;
  - resident engine rejects `resident_warp_batch_dispatch="pipelined"` unless
    `resident_output_maps="minimal"`;
  - default audit/science output maps remain on deterministic Gate616
    `chunked` dispatch.
- Updated CLI dispatch choices, memory admission, tests, and Phase 2 docs.
- Preserved default resident runtime behavior: default dispatch is still
  `chunked` with 8-frame warp chunks.

## Real 200-Light Evidence

Probe root:

- `C:\glass_runs\phase2_s2_gate617_pipelined_warp`

Rejected pipelined audit/science candidate:

- Run: `C:\glass_runs\phase2_s2_gate617_pipelined_warp\real_200_pipelined`
- Gate:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\resident_regression_gate_pipelined_vs_gate616.json`
- Result: failed `resident_determinism_passed`.
- Candidate/baseline elapsed ratio: `0.9381852285271229`.
- Determinism: artifact `0`, frame signatures `0`, registration `0`, frame
  accounting `0`, output groups `1`, numerical drift rows `5`.
- Max relative output RMS drift: `0.00045132060517754546`.
- Native warp total: `0.5054357 s`, slower than Gate616 chunked
  `0.4868301 s`.
- Native pipelined workspace: `4932096704` bytes, about 2x Gate616 chunked.

Rejected blocking-stream retry:

- Run:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\real_200_pipelined_blocking_stream`
- Gate:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\resident_regression_gate_pipelined_blocking_vs_gate616.json`
- Result: failed `resident_determinism_passed`.
- Candidate/baseline elapsed ratio: `0.9127089434621689`.
- Same output-map drift pattern as the first pipelined attempt.

Default same-build green validation:

- Baseline:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\real_200_default_guarded_chunked_direct_launch`
- Candidate:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\real_200_default_guarded_chunked_direct_launch_repeat`
- Gate:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\resident_regression_gate_default_same_build_repeat.json`
- Result: passed.
- Candidate/baseline elapsed ratio: `1.0284459040041496`.
- Determinism differences: artifact `0`, frame signatures `0`,
  registration `0`, frame accounting `0`, output pixels `0`, numerical drift
  `0`.
- Frame admission: `193 / 200` active, `7` masked.

Additional observation:

- Comparing the current rebuilt default chunked run to the older Gate616 binary
  produced the same tiny 5-row output drift seen in the pipelined negative
  probes. The same-build repeat passed exactly, so Gate617 uses same-build
  default validation as the green checkpoint and does not claim cross-binary
  bit identity.
- A `resident-output-maps minimal` real run with registration currently fails
  `warp_quality_contract` because geometric coverage closure is intentionally
  unavailable in that contract mode. This remains a separate contract gap.

## Commands Run

- Native rebuild through VS developer environment:
  - `cmake --build build --config Release --target _glass_cuda_native -j 8`
- Focused tests:
  - `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_fused_and_batch_lanczos3_unclamped_skip_nan_footprint`
  - `python -m pytest -q tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_honors_pipelined_dispatch tests/test_resident_cuda_run.py::test_resident_memory_admission_accepts_pipelined_dispatch tests/test_cli_smoke.py::test_cli_resident_run_accepts_pipelined_warp_dispatch`
  - `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_fused_and_batch_lanczos3_unclamped_skip_nan_footprint tests/test_resident_cuda_run.py::test_resident_run_rejects_pipelined_dispatch_with_audit_maps`
- Real 200-light runs:
  - `glass run ... --resident-warp-batch-dispatch pipelined`
  - `glass run ... --resident-warp-batch-dispatch pipelined` after blocking-stream retry
  - `glass run ...` default guarded chunked direct-launch candidate
  - `glass run ...` default guarded chunked direct-launch repeat
- Real 200-light A/B gates:
  - `glass resident-regression-gate ... resident_regression_gate_pipelined_vs_gate616.json`
  - `glass resident-regression-gate ... resident_regression_gate_pipelined_blocking_vs_gate616.json`
  - `glass resident-regression-gate ... resident_regression_gate_default_same_build_repeat.json`
- `python -m pytest -q`
- `git diff --check`

## Test Results

- Focused CUDA/engine/CLI tests: passed.
- Full pytest: `1299 passed in 53.09 s`.
- `git diff --check`: passed; only existing CRLF conversion warnings.

## CUDA

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Multiprocessors: `188`.
- Native backend: available.
- CUDA Toolkit used by the local CMake cache: `13.2`.

## Known Limits

- Pipelined resident matrix warp is not a default optimization.
- Audit/science output maps remain on `chunked`; pipelined dispatch is blocked
  when warp coverage tracking is required.
- The current pipelined implementation was useful as a negative real-data
  experiment, but future resident warp work needs a different design, likely
  immutable source/destination surfaces or explicit per-lane coverage reduction
  with a stronger contract.
- `resident-output-maps minimal` plus registration currently needs contract
  work before it can serve as a clean full-run benchmark route.

## Clean-Room Compliance

- Input image directories were read-only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- The implementation and rejection decision are based on GLASS-owned CUDA
  kernels/wrappers, GLASS artifact contracts, GLASS tests, and user-owned real
  benchmark outputs.

## Next Step

- Return to the main Phase 2 substance: StackEngine default path and DQ/mask
  pipeline contract completion, then revisit resident warp performance with a
  source/destination surface design rather than launching the current in-place
  scatter concurrently.
