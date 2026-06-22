# S2-Gate 502 Status: Explicit Resident Warp Chunk Capacity

## Gate

S2-Gate 502

## Completed Content

- Returned from the C: drive cleanup check to the Phase 2 real 200-light A/B path.
- Checked C: free space before the gate:
  - C: free: about `433.36 GiB`
  - repository size before cleanup: about `2.401 GiB`
  - `C:\glass_runs`: about `88.621 GiB`
  - `C:\gpwbpp_runs`: about `83.686 GiB`
- Cleaned only regenerable repository artifacts:
  - `build`
  - `.pytest_cache`
  - non-venv, non-run `__pycache__` directories
- Repository size after cleanup: about `2.345 GiB`.
- Did not delete historical real-run evidence under `C:\glass_runs` or `C:\gpwbpp_runs`.
- Added `--resident-warp-chunk-capacity-frames` to `glass run`.
- Added `--resident-warp-chunk-capacity-frames` to `glass audit`.
- Routed explicit chunk capacity through resident memory admission.
- Added admission evidence fields:
  - `preferred_chunk_capacity_source`
  - `requested_chunk_capacity_frames`
  - `selected_chunk_capacity_source`
- Preserved existing reduced-capacity budget fallback behavior.
- Added tests for explicit capacity admission and CLI-to-runtime propagation.

## Files Changed

- `src/glass/cli.py`
- `src/glass/engine/resident_cuda.py`
- `tests/test_cli_smoke.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`

## Real 200-Light Validation

Run root:

`C:\glass_runs\phase2_s2_gate502_warp_chunk_capacity_ab_real\runs_20260623_051320`

Common run settings:

- plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- master cache: `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache`
- backend: `cuda`
- memory mode: `resident`
- resident registration: `similarity_cuda_triangle`
- reference frame: `LIGHT_H_0136`
- warp interpolation: `lanczos3`
- output maps: `minimal`
- rejection: `winsorized_sigma`
- weighting: `none`
- local normalization: `off`
- flat floor: `0.05`
- runtime preset: default `throughput-v3-io`

Timing:

| Variant | Selected chunk | Source | Run timing total | Shell wall | Estimated peak VRAM |
| --- | ---: | --- | ---: | ---: | ---: |
| `default_auto8` | 8 | `native_preferred` | `7.12994339998113 s` | `7.482222 s` | `49.60843022540212 GiB` |
| `chunk16` | 16 | `explicit` | `7.12517720006872 s` | `7.487104 s` | `51.90511639788747 GiB` |
| `chunk32` | 32 | `explicit` | `7.1467631999985315 s` | `7.502273 s` | `56.49848874285817 GiB` |
| `chunk64` | 64 | `explicit` | `7.218323500012048 s` | `7.573115 s` | `65.68523343279958 GiB` |

Selected default split timing:

- read/upload/calibrate bucket: `2.6453787999926135 s`
- read wait wall: `0.9849792996537872 s`
- H2D plus calibrate/store: `0.8478688998147845 s`
- native calibration batch total: `0.8417149999999999 s`
- resident registration component total: `2.0864001998257167 s`
- triangle moving catalog: `0.26584980014013126 s`
- triangle descriptors: `0.1319461001548916 s`
- triangle descriptor fit: `0.06393730000127107 s`
- triangle warp: `0.4901261000195518 s`
- native warp batch: `0.4796378 s`
- native warp sync: `0.46316 s`
- resident integration: `0.1740511999814771 s`
- output write: `0.5232929000048898 s`

## Numerical Results

Chunk variants versus `default_auto8`:

- `chunk16`: bitwise equal, RMS `0.0`, p99 `0.0`, max `0.0`
- `chunk32`: bitwise equal, RMS `0.0`, p99 `0.0`, max `0.0`
- `chunk64`: bitwise equal, RMS `0.0`, p99 `0.0`, max `0.0`

Gate502 default versus Gate501 default:

- bitwise equal: `true`
- RMS absolute difference: `0.0`
- p99 absolute difference: `0.0`
- max absolute difference: `0.0`

WBPP black-box timing retained for speed context:

- WBPP elapsed: `1092.541 s`
- Gate502 default speedup by GLASS run timing: about `153.232x`
- Gate502 default speedup by shell wall: about `146.025x`

## Interpretation

- Larger warp chunks are numerically safe for this dataset on this GPU.
- Larger warp chunks are not materially faster on the real 200-light benchmark.
- `chunk64` uses substantially more peak VRAM and regresses wall-clock timing.
- The default remains native-preferred chunk8.
- The next useful resident registration/warp optimization should target native warp kernel/sync time, catalog/descriptor residency, and batch scoring/orchestration, not simply larger warp chunks.

## Commands Run

- `Get-PSDrive -Name C`
- repository/run size checks for `C:\Users\ljs\WORK\astro\gpuwbpp`, `C:\glass_runs`, and `C:\gpwbpp_runs`
- safe cleanup of regenerable repository `build`, `.pytest_cache`, and non-run/non-venv `__pycache__`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_memory_admission_accepts_explicit_chunk_capacity tests/test_cli_smoke.py::test_cli_resident_run_passes_explicit_chunk_capacity_from_admission tests/test_cli_smoke.py::test_cli_resident_run_passes_reduced_chunk_capacity_from_admission`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate502_warp_chunk_capacity_ab_real\runs_20260623_051320\default_auto8 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache`
- the same command with `--resident-warp-chunk-capacity-frames 16`
- the same command with `--resident-warp-chunk-capacity-frames 32`
- the same command with `--resident-warp-chunk-capacity-frames 64`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: `3 passed in 1.20s`
- Full test suite: `1148 passed in 43.72s`

## CUDA Status

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Reported memory: `97886 MiB`
- Native backend: `true`
- Available to GLASS: `true`

## Known Limits

- This gate exposes and validates chunk capacity control but does not improve the default speed path.
- The gate intentionally rejects default promotion for larger chunks because measured benefit is noise-level and chunk64 regresses.
- The option is useful for memory experiments, admission/budget validation, and future hardware-specific sweeps.

## Next Step

Return to the real performance bottleneck: resident registration/warp internals. Prioritize native warp kernel/sync reduction and keeping catalog/descriptor/scoring data resident and batched, while preserving the 200-light bitwise output contract.

## Clean-Room Compliance

Compliant. This gate changes GLASS-owned scheduler, CLI, memory-admission, and test code only. Validation uses GLASS-generated artifacts, the user-staged M38 H-alpha 200-light data, and user-generated WBPP black-box timing/output references. It does not inspect external implementation source, copy proprietary behavior, modify input image directories, or change scientific formulas.
