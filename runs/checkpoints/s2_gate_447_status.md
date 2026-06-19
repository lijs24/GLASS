# S2-Gate 447 Status: Resident Source-DQ Parity And Synthetic Regression

## Gate

- Gate: S2-Gate 447
- Date: 2026-06-20
- Scope: Phase 2 runtime-path hardening, not release/default-promotion/report handoff.

## Gate400-413 Value To Core Goals

Gate400 through Gate413 are retained as useful evidence-chain guardrails, but
they do not directly advance the Phase 2 runtime blockers. Their direct value is:

- Gate400 established the release evidence-chain fixture.
- Gate401 through Gate403 moved resident CUDA DQ provenance into acceptance and
  benchmark-contract profiles.
- Gate404 and Gate405 exposed runtime-sweep and Phase2 status surfaces.
- Gate406 through Gate413 handed benchmark/publication-audit profiles through
  release-promotion, default-promotion, Windows matrix, preflight, and
  publication-audit checks.

They did not change image math, CUDA kernels, StackEngine execution defaults,
DQ pixel/sample semantics, real 200-light output, or runtime performance. This
gate therefore returns to the substantive Phase 2 path: StackEngine/DQ parity,
resident CUDA semantics, numerical validation, and performance evidence.

## Completed Work

- Added resident CUDA invalid-mask kernel:
  `glass_apply_invalid_mask_f32_kernel`.
- Exposed `ResidentCalibratedStack.apply_invalid_mask_frame()` through native
  pybind and the Python `glass_cuda` wrapper.
- Added `src/glass/engine/resident_source_dq.py` to build invalid masks from
  nonfinite source arrays and explicit `DQMask` bitfields.
- Wired resident CUDA calibration/integration to apply source invalid masks
  after calibration upload and before registration/integration.
- Preserved source-DQ provenance in `resident_artifacts.json`,
  `integration_results.json`, and resident DQ summaries.
- Fixed resident DQ sample closure so raw source invalid counts do not get
  mixed with post-warp coverage closure.
- Added CPU StackEngine vs resident CUDA tests proving finite DQ flags are
  excluded identically.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\resident_source_dq.py src\\glass\\engine\\resident_cuda.py src\\glass\\engine\\dq.py src\\glass_cuda.py tests\\test_resident_source_dq.py tests\\test_cuda_resident_stack.py`
- `.\\.venv\\Scripts\\python.exe -m py_compile src\\glass\\engine\\resident_source_dq.py src\\glass\\engine\\resident_cuda.py src\\glass\\engine\\dq.py src\\glass_cuda.py tests\\test_resident_source_dq.py tests\\test_cuda_resident_stack.py`
- `.\\.venv\\Scripts\\python.exe -m pip install -e .[dev,report]`
- `.\\.venv\\Scripts\\cmake.exe --build build\\native-cuda-glass --config Release --target _glass_cuda_native --parallel`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_source_dq.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_resident_stack.py::test_resident_stack_apply_invalid_mask_frame_excludes_finite_source_dq_samples tests\\test_cuda_resident_stack.py::test_resident_stack_source_dq_mask_matches_cpu_stack_engine_for_finite_flags`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_source_dq.py tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py tests\\test_cuda_resident_stack.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_resident_dq_pixel_closure.py tests\\test_resident_result_contract.py tests\\test_resident_stack_surface.py tests\\test_resident_frame_mask_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_source_dq.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py tests\\test_resident_dq_pixel_closure.py tests\\test_resident_result_contract.py tests\\test_resident_stack_surface.py tests\\test_resident_frame_mask_contract.py`
- Synthetic CPU-vs-resident source-DQ performance validation script, output:
  `runs/checkpoints/s2_gate_447_perf/synthetic_source_dq_cpu_vs_resident.json`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Focused resident source-DQ helper tests: 3 passed.
- CUDA import/device tests: 2 passed.
- Focused resident invalid-mask CUDA tests: 2 passed.
- StackEngine/resident DQ contract tests: 57 passed.
- Resident run/result/DQ closure tests: 80 passed.
- Expanded resident source-DQ/runtime set: 119 passed.
- Full suite: 1065 passed in 40.07 s.

## Synthetic Performance And Numerical Validation

Artifact:
`runs/checkpoints/s2_gate_447_perf/synthetic_source_dq_cpu_vs_resident.json`

- Dataset: 48 frames, 384x384, 7,077,888 input samples.
- Injected finite DQ invalid samples: 8,588.
- CPU StackEngine time: 0.1466348000 s.
- Resident total time: 0.0940110000 s.
- Resident upload time: 0.0027641998 s.
- Resident source-DQ apply time: 0.0079226999 s.
- Resident integration time: 0.0003259999 s.
- CPU/resident total speedup: 1.56x.
- CPU/resident integration-only speedup: 449.8x.
- `master_max_abs`: 0.0.
- `master_rms`: 0.0.
- `weight_max_abs`: 0.0.
- CPU and resident input sample/DQ invalid counts match exactly.

## CUDA Availability

- CUDA available: yes.
- Native backend loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97,886 MiB.
- Build note: CMake needed the Visual Studio BuildTools developer environment
  (`VsDevCmd.bat`) so NVCC could find `cl.exe` and Windows SDK headers.

## Real 200-Light Status

The real M38 H 200-light regression was not rerun in this gate. This gate
changes source invalid/DQ sample handling and provenance; the known M38 resident
path does not currently supply explicit source DQ sidecar masks. A full 200-light
rerun should be part of the next substantive gate once StackEngine default
routing or resident DQ input plumbing changes real output semantics.

## Known Limitations

- Resident run path currently extracts nonfinite invalid samples from float
  arrays automatically. Explicit `DQMask` parity is implemented through the new
  resident source-DQ helper and direct native mask application, but FITS/XISF
  sidecar DQ masks are not yet plumbed from file inputs into resident runs.
- Compact raw FITS GPU-decode payloads cannot carry NaN/sidecar invalid samples
  at this layer; unsupported extraction is recorded with zero invalid samples.
- The synthetic performance validation is small and in-memory. It validates
  DQ parity and GPU integration potential, not the full 200-light I/O pipeline.

## Next Gate

S2-Gate 448 should stay on the Phase 2 main line:

- route explicit input-DQ/cosmetic/bad-pixel masks from file/cache layers into
  resident source-DQ masks;
- run a real or larger synthetic resident regression after that plumbing;
- if output semantics change, rerun the M38 H 200-light benchmark and compare
  timing/result deltas against Gate443/Gate447.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned DQMask/StackEngine contracts, CUDA kernels,
tests, and synthetic artifacts only. No official PixInsight/WBPP/PJSR source was
read, copied, summarized, or reworked. Input image directories were not modified.
