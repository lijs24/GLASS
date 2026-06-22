# S2-Gate 473 Status: Fused Integration Memory Admission Model

- Gate: S2-Gate 473
- Status: passed
- Scope: make resident CUDA memory admission aware of effective fused
  integration dispatch so the `throughput-v2-fused` candidate is not charged
  for chunked registered-stack warp workspace it does not allocate.

## Completed

- Added a conservative resident integration dispatch resolver for admission.
- Extended `build_resident_memory_admission()` with:
  - `resident_integration_dispatch`
  - `resident_warp_interpolation`
  - `local_normalization`
  - `integration_rejection`
  - `resident_winsorized_mode`
- Updated `glass run` and `glass audit` admission preflight so
  `resident_memory_admission.json` records:
  - requested integration dispatch
  - effective integration dispatch
  - dispatch selection reason
  - fused admission flag
  - per-group planned warp frames and chunked workspace with fused accounted
- Added tests for:
  - auto bilinear fused admission skipping registered-stack warp workspace
  - auto Lanczos3 admission keeping stack/chunked workspace
  - CLI `throughput-v2-fused` CUDA smoke recording fused admission and zero
    planned chunked workspace.
- Ran a real-plan admission comparison on
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`.

## Commands

```powershell
python -m pytest -q tests\test_resident_cuda_run.py::test_resident_memory_admission_auto_fused_skips_registered_stack_workspace tests\test_resident_cuda_run.py::test_resident_memory_admission_auto_lanczos_keeps_stack_workspace tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path

ruff check src tests docs

python -m pytest -q tests\test_resident_cuda_run.py

python -m pytest -q
```

## Results

- Focused pytest: `3 passed in 0.96s`
- Ruff: passed
- Resident CUDA test file: `74 passed in 8.29s`
- Full pytest: `1107 passed in 48.30s`
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability
  `12.0`, total memory `97886 MiB`

## Real 200-Light Admission Compare

- Artifact:
  `runs/checkpoints/s2_gate_473_real_plan_admission_compare.json`
- Plan:
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Stack/Lanczos3 admission:
  - effective integration dispatch: `stack`
  - estimated peak: `49.60843022540212 GiB`
  - planned warp frames: `199`
  - planned chunked workspace: `2466056756` bytes
- Auto/Bilinear fused admission:
  - effective integration dispatch: `fused_matrix`
  - reason: `auto_fused_bilinear_matrix_route`
  - estimated peak: `47.3117358982563 GiB`
  - planned warp frames: `0`
  - planned chunked workspace: `0` bytes
- Peak reduction: `2.296694327145815 GiB`

## Known Limitations

- This gate changes memory admission and scheduling evidence only. It does not
  alter image math or runtime defaults.
- A clean idle-GPU 200-light timed run was not launched because another GPU
  compute process was active.
- Explicit invalid fused requests are conservatively counted as stack in
  admission, avoiding memory underestimation before the engine raises runtime
  validation.

## Next Step

- Run an idle-GPU 200-light A/B matrix:
  - `throughput-v1` Lanczos3 parity
  - `throughput-v2-fused` bilinear candidate
  - require frame accounting, DQ closure, compare agreement, and speed evidence
    before considering any runtime-default change.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS code, GLASS tests, GLASS-generated artifacts, and a
  user-staged real processing plan for metadata-only admission comparison.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Original image directories were not modified.
