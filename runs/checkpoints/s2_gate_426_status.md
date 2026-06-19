# S2 Gate 426 Status - Resident GPU Centroid Catalog Refinement

Date: 2026-06-19
Base commit: 33fad31

## Gate400-413 Core-Goal Value

Gates 400-413 mostly protected release/default-promotion/publication handoff
evidence for the resident CUDA benchmark profile. Their practical value was:

- preserving `resident_cuda_dq_v1` benchmark-profile evidence across release
  decision, Phase2 status, publication audit, Windows release matrix, publish
  preflight, and default-promotion artifacts;
- preventing release/report layers from silently dropping benchmark-profile
  evidence after it was generated;
- keeping clean-room and no-input-mutation boundaries auditable.

Their direct value to the Phase 2 scientific/runtime core was limited: they did
not change StackEngine execution, DQ/mask pixel semantics, CUDA kernels,
resident registration, winsorized rejection, 200-light runtime, or numerical
agreement. Gate426 returns to the core path.

## Gate Intent

Convert the previous resident triangle CPU tile-download centroid probe into a
true resident CUDA catalog-centroid default path, while keeping pixel NCC refine
disabled by default. This targets the Gate425 finding that resident matrix
precision, not the warp kernel itself, is the next upstream blocker.

## Implemented

- Added a CUDA `star_refine_centroids_kernel` for resident star catalogs.
- The kernel computes a bounded-window median background and applies positive
  flux-weighted centroid refinement in resident GPU memory.
- Added native binding support for:
  - `star_top_nms_candidates_centroid`;
  - `star_grid_top_nms_candidates_centroid`;
  - `star_grid_top_nms_candidates_deterministic_centroid`;
  - batched grid-NMS centroid variants.
- Added Python wrappers in `src/glass_cuda.py`.
- Changed resident triangle registration default so centroid refinement is
  enabled while pixel refine remains disabled unless explicitly requested.
- Added artifact fields for centroid mode, refined catalog count, refined star
  count, failed star count, and maximum centroid shift.
- Updated focused resident CUDA test coverage.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Validation Commands

- `cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native'`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine tests/test_gpu_registration_search.py`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_426_gpu_median_centroid_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli resident-warp-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_426_gpu_median_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_426_gpu_median_centroid_warp_input_audit.json --markdown runs\checkpoints\s2_gate_426_gpu_median_centroid_warp_input_audit.md`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_426_gpu_median_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --evaluation-region compare_region --max-pre-rejection-sample-delta 0 --max-same-pre-rejection-abs-delta 0 --max-rejected-sample-delta 0 --out runs\checkpoints\s2_gate_426_gpu_median_centroid_rejection_sample_audit.json --markdown runs\checkpoints\s2_gate_426_gpu_median_centroid_rejection_sample_audit.md`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine tests/test_gpu_registration_search.py tests/test_resident_warp_input_audit.py tests/test_resident_rejection_sample_audit.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_426_cuda_doctor.json`

## Results

- Native CUDA build: passed. CUDA header C4819 encoding warnings only.
- Focused resident CUDA tests: 34 passed in 0.53s.
- Focused Gate426/audit tests: 40 passed in 0.76s.
- Full pytest: 1004 passed in 38.13s.
- 16-frame resident CUDA run completed through integration.

### Resident GPU Centroid Artifact

- Registration mode: `similarity_cuda_triangle`.
- Pixel refine: `False`.
- Centroid refine: `True`.
- Centroid mode: `resident_gpu_window_centroid`.
- Centroid catalogs: `30`.
- Refined stars: `1778`.
- Failed centroid stars: `0`.
- Maximum centroid shift: `2.0328240394592285 px`.
- Translation refine applied frames: `15`.
- Max translation-refine correction: `0.08207019680050967 px`.
- Max translation-refine RMS: `0.20454880917869436 px`.

### Warp Input Audit

- Status: passed.
- Recommendation: `target_resident_registration_matrix_precision`.
- CPU-matrix resident warp RMS max: `0.0002643936071558697`.
- CPU-matrix resident warp RMS mean: `0.00019183110707193216`.
- Resident-matrix resident warp RMS max: `0.16830002181892761`.
- Resident-matrix resident warp RMS mean: `0.1065692309624858`.
- Matrix translation delta max: `0.009531948948220055 px`.
- Matrix translation delta mean: `0.005459747234037016 px`.
- Resident matrix warp parity: false.

Interpretation: the resident CUDA warp kernel still matches the CPU registered
cache when fed CPU matrices. The new median-window GPU centroid path improves
the min-background centroid probe and removes the CPU tile-download dependency,
but it does not fully solve resident registration-matrix precision.

### Rejection Sample Audit

The rejection audit was run as a diagnostic, not as this gate's hard acceptance
criterion.

- Status: `attention_required`.
- Recommendation: `fix_resident_winsorized_rejection_semantics`.
- Compare-region pre-rejection sample delta: `0`.
- Compare-region rejected sample delta: `-38`.
- Compare-region same-pre-rejection absolute rejected delta: `798`.
- Failed checks:
  - `rejected_sample_delta_within_limit`;
  - `same_pre_rejection_semantic_delta_within_limit`.

Interpretation: geometry/input-sample drift is controlled inside the common
footprint, but winsorized low/high rejection decisions still differ. This is
the next substantive blocker.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_426_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_426_status.md`
- `runs/checkpoints/s2_gate_426_cuda_doctor.json`
- `runs/checkpoints/s2_gate_426_gpu_median_centroid_warp_input_audit.json`
- `runs/checkpoints/s2_gate_426_gpu_median_centroid_warp_input_audit.md`
- `runs/checkpoints/s2_gate_426_gpu_median_centroid_rejection_sample_audit.json`
- `runs/checkpoints/s2_gate_426_gpu_median_centroid_rejection_sample_audit.md`
- `runs/checkpoints/s2_gate_426_gpu_median_centroid_refF16_cuda_hardened/`

## Known Limitations

- This gate is not the final registration-matrix parity fix.
- Resident-matrix warp RMS remains above CPU-matrix replay RMS.
- Winsorized rejection semantic parity remains blocked.
- The validation is the 16-frame synthetic checkpoint harness, not the
  required 200-light real-data regression.
- The centroid kernel clamps the usable centroid radius to a bounded small
  window for predictable local-memory use.
- Large-run performance optimization is not claimed by this gate.

## Next Substantive Gate

S2 Gate 427 should target the remaining runtime blockers directly:

- either fix resident winsorized rejection semantics now that compare-region
  pre-rejection sample delta is zero;
- or further reduce resident registration-matrix deltas below the current
  `0.00953 px` max before rerunning the 200-light regression.

No release/default-promotion/report-contract-only gates should be added unless
they directly block those runtime goals.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was
read or used. This gate uses GLASS code, GLASS-generated checkpoint artifacts,
and generic median-background/flux-centroid and matrix/warp comparison math
only. Input image directories were not modified.
