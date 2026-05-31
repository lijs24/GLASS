# S2 Gate 84 Status: Opt-In Fused Resident Matrix Integration Route

## Gate

S2-Gate 84 - Opt-In Fused Resident Matrix Integration Route.

## Completed

- Added `--resident-integration-dispatch {stack,fused_matrix}` to `glass run`
  and `glass audit`.
- Wired resident CUDA integration dispatch through the Gate82/Gate83 fused
  matrix-warp mean and sigma/winsorized-sigma primitives.
- Kept the first fused route intentionally narrow:
  - `resident_registration=off` uses identity matrices.
  - `resident_registration=external_matrix` consumes an existing
    `registration_results.json` artifact and defers accepted moving-frame
    matrix application to the fused integration kernel.
  - local normalization must be off for fused dispatch.
- Added resident artifacts for dispatch mode, fused usage, deferred frame count,
  native fused timing, interpolation/clamping policy, and geometric coverage
  provenance.
- Added a CLI-level CUDA test comparing external-matrix stack dispatch against
  fused-matrix dispatch with winsorized sigma rejection.
- Updated Phase 2 gate planning and algorithm-source documentation.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_mean_bilinear_matches_warp_then_integrate tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_winsorized_lanczos3_matches_warp_then_integrate`
- `.\.venv\Scripts\glass.exe run --help`
- `.\.venv\Scripts\glass.exe audit --help`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_84_200\stack_external_bilinear_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration external_matrix --resident-registration-results C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601\registration_results.json --resident-warp-interpolation bilinear --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_84_200\fused_external_bilinear_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration external_matrix --resident-registration-results C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601\registration_results.json --resident-integration-dispatch fused_matrix --resident-warp-interpolation bilinear --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_84_200\fused_external_bilinear_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_84_200\stack_external_bilinear_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_84_200\compare_fused_vs_stack_external_bilinear.html --glass-time-seconds 11.035161800216883 --reference-time-seconds 11.254394300282001 --glass-label Gate84_fused_external_bilinear --reference-label Gate84_stack_external_bilinear --ignore-border-px 0`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Native CUDA build: passed (`ninja: no work to do`).
- Focused CUDA resident tests: 4 passed.
- Full ruff: passed.
- Full pytest: 288 passed in 12.37 s.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## 200-Light Real Data Result

Inputs were read-only. Both runs used the same 200-light M38 H-alpha processing
plan, the same shared resident master cache, the same external
`registration_results.json`, the same excluded-frame list, bilinear matrix
warp, no local normalization, no weighting, and winsorized sigma rejection.

- Stack external-matrix dispatch:
  `C:\glass_runs\phase2_s2_gate_84_200\stack_external_bilinear_20260601`
  - total: 11.254394300282001 s
  - light read/upload/calibrate: 6.254984499886632 s
  - registration warp/scatter: 0.23702649679034948 s
  - integration: 0.2959733996540308 s
- Fused external-matrix dispatch:
  `C:\glass_runs\phase2_s2_gate_84_200\fused_external_bilinear_20260601`
  - total: 11.035161800216883 s
  - light read/upload/calibrate: 6.239766499958932 s
  - registration warp/scatter: 0.00207020016387105 s
  - fused integration native total: 0.4273899 s
  - integration wall: 0.4277539001777768 s
- Compare report:
  `C:\glass_runs\phase2_s2_gate_84_200\compare_fused_vs_stack_external_bilinear.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_84_200\compare_fused_vs_stack_external_bilinear.json`
  - shape match: true
  - compared pixels: 61651200
  - RMS diff: 0.0
  - max abs diff: 0.0
  - speedup vs stack external route: 1.0198667227571425x

## Known Limitations

- `fused_matrix` is opt-in and not the default route.
- Fused routing currently supports only `resident_registration=off` and
  `resident_registration=external_matrix`.
- Fused routing requires local normalization to be off.
- Triangle registration still applies matrices into the resident stack before
  integration; it is not yet routed through fused matrix integration.
- The fused rejection kernel avoids warp scatter but is currently slower than
  stack integration itself on the 200-light bilinear A/B run. Net wall time is
  still slightly faster because registration warp/scatter time is mostly
  removed.
- Lanczos3 fused routing is covered by primitive tests. CLI-level A/B used
  bilinear because the current stack route leaves the reference frame unwarped,
  while fused Lanczos samples even the identity reference matrix and therefore
  has stricter edge-footprint semantics.

## Next Step

S2-Gate 85 should reduce fused matrix-warp rejection cost by reusing output and
inverse-matrix workspaces, reducing download/sync overhead, and then wiring the
triangle-registration matrix list into fused dispatch without writing registered
full-frame intermediates.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned CUDA kernels, GLASS-generated artifacts,
project-defined matrix routing, and user-generated registration results. It did
not read, copy, summarize, or rework proprietary implementation source. Input
image directories were treated as read-only.
