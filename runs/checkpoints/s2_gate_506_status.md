# S2-Gate 506 Status: Minimal Sigma Map Workspace Skip

## Gate

S2-Gate 506

## Completed Content

- Returned to the Phase 2 mainline performance path after the Gate505 timing
  review and a negative resident scheduling probe.
- Kept the current `throughput-v3-io` default because tested
  prefetch/worker/batch variants did not improve the real 200-light benchmark.
- Optimized the active real path: resident stack/native sigma or
  winsorized-sigma integration with `--resident-output-maps minimal`.
- Updated the CUDA resident sigma integration kernel to tolerate null output-map
  pointers.
- Updated native bindings so `download_mode=master_only` allocates no resident
  weight, coverage, low-rejection, or high-rejection device-map buffers.
- Added artifact reporting:
  `native_map_workspace_mode=master_only_no_weight_or_diagnostic_device_maps`.
- Added tests proving `master_only` and `full` download modes produce the same
  master while `master_only` returns no maps.
- Ran focused tests, full pytest, native build validation, CUDA doctor, and a
  real 200-light candidate/repeat A/B.
- Checked C-drive/project size before real A/B:
  C: had about `428.88 GB` free; the repo itself is small enough that no cleanup
  was needed. No generated data or historical checkpoint directories were
  deleted.

## Changed Files

- `cpp/cuda/integration_kernels.cu`
- `cpp/src/native_bindings.cpp`
- `src/glass/engine/resident_cuda.py`
- `tests/test_cuda_resident_stack.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `runs/checkpoints/s2_gate_506_status.md`

## Commands Run

- `python -m ruff check src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_winsorized_sigma_master_only_matches_full_master tests/test_cuda_resident_stack.py::test_resident_stack_winsorized_sigma_matches_mean_std_reference tests/test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads`
- `python -m pytest -q`
- `cmd /c "VsDevCmd.bat -arch=x64 && cmake --build build --config Release -j 1"`
- `glass doctor`
- Real 200-light run command, executed for `candidate` and `repeat`:

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --backend cuda --memory-mode resident --until-stage integration `
  --local-normalization off --integration-rejection winsorized_sigma `
  --integration-weighting none --flat-floor 0.05 `
  --resident-registration similarity_cuda_triangle `
  --resident-star-threshold 350 --resident-star-max-candidates 48 `
  --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 `
  --resident-warp-interpolation lanczos3 `
  --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal `
  --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache `
  --out <candidate-or-repeat>
```

- External-reference compare:

```powershell
glass compare `
  --glass C:\glass_runs\phase2_s2_gate506_sigma_master_only_maps_ab_real\runs_20260623_060330\repeat\integration\resident_master_H.fits `
  --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf `
  --out C:\glass_runs\phase2_s2_gate506_sigma_master_only_maps_ab_real\runs_20260623_060330\compare_vs_wbpp_fastintegration_scaled_coverage190.html `
  --glass-time-seconds 6.644183400028851 `
  --reference-time-seconds 1092.541 `
  --glass-label GLASS-Gate506-resident-minimal `
  --reference-label PixInsight-WBPP-fastIntegration `
  --glass-scale 8.764434957115609e-06 `
  --glass-offset 0.0006274500691899127 `
  --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits `
  --min-coverage 190
```

## Test Results

- Ruff: passed.
- Focused CUDA/resident tests: `3 passed in 1.48 s`.
- Full pytest: `1153 passed in 41.67 s`.
- Native build validation: `ninja: no work to do`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`.

## Real 200-Light Results

Run root:

`C:\glass_runs\phase2_s2_gate506_sigma_master_only_maps_ab_real\runs_20260623_060330`

Runtime:

- Gate506 candidate: `6.635181299992837 s`.
- Gate506 repeat: `6.644183400028851 s`.
- Gate505 repeat baseline: `6.707604100054596 s`.
- WBPP black-box fastIntegration reference: `1092.541 s`.

Artifact contract:

- Dispatch mode: `stack`.
- Download mode: `master_only`.
- Native map workspace mode:
  `master_only_no_weight_or_diagnostic_device_maps`.
- `weight_map_downloaded=false`.
- `diagnostic_maps_downloaded=false`.
- Output-map policy available maps: `["master"]`.

Component timing:

- Gate506 candidate `light_read_upload_calibrate`: `2.6411565999733284 s`.
- Gate506 repeat `light_read_upload_calibrate`: `2.642411299981177 s`.
- Gate506 candidate resident registration accounted:
  `1.9854616006272525 s`.
- Gate506 repeat resident registration accounted:
  `1.9805916002435655 s`.
- Gate506 candidate resident warp: `0.48518729978241026 s`.
- Gate506 repeat resident warp: `0.482397299609147 s`.
- Gate506 candidate resident integration: `0.16666499996790662 s`.
- Gate506 repeat resident integration: `0.16351149999536574 s`.
- Gate505 repeat resident integration baseline was about `0.1783 s`.

Numerical agreement:

- Gate506 candidate vs Gate506 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate506 candidate vs Gate505 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate506 repeat vs Gate505 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.

External-reference comparison:

- Report:
  `C:\glass_runs\phase2_s2_gate506_sigma_master_only_maps_ab_real\runs_20260623_060330\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate506_sigma_master_only_maps_ab_real\runs_20260623_060330\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Speedup vs external fastIntegration reference:
  `164.43570777941738x`.
- RMS difference: `0.0017794216505176163`.
- P99 absolute difference: `0.00042621337808668863`.
- Compared pixels with `min_coverage=190`: `59217988`.

## Schedule Probe

Negative schedule probe root:

`C:\glass_runs\phase2_s2_gate506_schedule_probe_real\runs_20260623_055700`

Observed variants:

- `v3_manual_32w12_b16_s4_w4`: `6.646391799964476 s`, bitwise equal.
- `pf48_w16_b16_s4_w4`: `6.991996800003108 s`, bitwise equal.
- `pf64_w16_b16_s4_w4`: `7.235546800016891 s`, bitwise equal.
- `pf64_w16_b32_s4_w4`: `7.040242400020361 s`, bitwise equal.
- `pf64_w16_b32_s4_w8`: `24.437550300033763 s`, bitwise equal, rejected.
- `pf64_w20_b32_s8_w8`: `6.857021400064696 s`, bitwise equal.

Conclusion: no runtime preset change is promoted.

## Known Limits

- This gate is a targeted resident integration workspace optimization, not a
  science change and not a large end-to-end speedup.
- The measured resident integration component gain is small and close to normal
  timing variance, although the artifact now proves the unnecessary map buffers
  are not allocated in the minimal-output path.
- The larger remaining bottlenecks are still read/decode/upload orchestration
  and resident registration/warp residency.
- `science` and `audit` output-map modes still allocate/write their requested
  maps by design.

## Next Step

Continue Phase 2 mainline work on a substantive gate:

- reduce resident registration/catalog native sync and output-download time;
- batch more registration state on the device;
- keep the 200-light Gate504/505/506 bitwise output baseline unless a deliberate
  algorithm gate changes science behavior with explicit evidence.

## Clean-Room Compliance

Compliant. This gate changed GLASS-owned CUDA kernel map-pointer handling,
native buffer allocation policy, artifact reporting, and tests. It used GLASS
unit tests, GLASS real-run artifacts, and a user-generated external reference
output for black-box comparison. No official PixInsight/WBPP/PJSR source code
was read, copied, summarized, or reworked.
