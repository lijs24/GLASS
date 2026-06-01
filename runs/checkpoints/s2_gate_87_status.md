# S2 Gate 87 Status: Resident Integration Auto Dispatch Policy

## Gate

S2-Gate 87 - add an auditable resident integration `auto` dispatch policy that
selects verified fast fused routes while keeping unverified routes on stack
dispatch.

## Completed

- Added `--resident-integration-dispatch auto` for `glass run` and
  `glass audit`.
- Resolved `auto` inside the resident CUDA engine before registration:
  - `bilinear` matrix routes with local normalization off select
    `fused_matrix`.
  - non-bilinear routes, local-normalization routes, and unsupported
    registration modes stay on `stack`.
- Preserved explicit `stack` and explicit `fused_matrix` behavior.
- Added resident artifact fields for requested mode, effective mode, selection
  reason, and auto policy flags.
- Added integration output fields for requested mode and selection reason.
- Added CUDA CLI coverage for both auto branches:
  - bilinear triangle auto selects fused dispatch;
  - Lanczos3+winsorized triangle auto stays on stack dispatch.
- Updated Phase 2 hardening notes and algorithm-source documentation.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --help`
- `.\.venv\Scripts\glass.exe audit --help`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-integration-dispatch auto --resident-warp-interpolation bilinear --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_bilinear_tuned_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_87_200\compare_auto_triangle_bilinear_vs_gate86_fused.html --glass-time-seconds 10.39124449994415 --reference-time-seconds 10.383039500098675 --glass-label Gate87_auto_triangle_bilinear --reference-label Gate86_explicit_fused_triangle_bilinear --ignore-border-px 0`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_86_200\stack_triangle_bilinear_tuned_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_87_200\compare_auto_triangle_bilinear_vs_gate86_stack.html --glass-time-seconds 10.39124449994415 --reference-time-seconds 12.168695699889213 --glass-label Gate87_auto_triangle_bilinear --reference-label Gate86_stack_triangle_bilinear --ignore-border-px 0`

## Test Result

- Native CUDA build: passed; target was already up to date.
- Focused auto-dispatch CUDA CLI tests: 2 passed.
- Full ruff: passed.
- Full pytest: 292 passed in 12.99 s.
- `glass run --help` and `glass audit --help` expose
  `{stack,fused_matrix,auto}`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## 200-Light Real Data Result

Inputs were read-only. Gate87 used the existing M38 H-alpha 200-light plan,
shared resident master cache, seven known excluded light frames, no local
normalization, no weighting, bilinear resident matrix sampling, and winsorized
sigma rejection.

Auto triangle bilinear:

- Run:
  `C:\glass_runs\phase2_s2_gate_87_200\auto_triangle_bilinear_tuned_20260601`
- Total elapsed: 10.39124449994415 s.
- Light read/upload/calibrate: 6.269452900160104 s.
- Resident registration/warp: 1.020270602311939 s.
- Resident integration: 0.29416369972750545 s.
- Fused native total: 0.2937922 s.
- Fused native sync: 0.2222845 s.
- Dispatch requested: `auto`.
- Dispatch effective: `fused_matrix`.
- Selection reason: `auto_fused_bilinear_matrix_route`.
- Deferred triangle matrices: 192.

Comparison against Gate86 explicit fused triangle bilinear:

- Report:
  `C:\glass_runs\phase2_s2_gate_87_200\compare_auto_triangle_bilinear_vs_gate86_fused.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate_87_200\compare_auto_triangle_bilinear_vs_gate86_fused.json`
- Shape match: true.
- RMS diff: 0.0.
- Max abs diff: 0.0.
- Speed ratio vs explicit fused: 0.9992103929567321x.

Comparison against Gate86 stack triangle bilinear:

- Report:
  `C:\glass_runs\phase2_s2_gate_87_200\compare_auto_triangle_bilinear_vs_gate86_stack.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate_87_200\compare_auto_triangle_bilinear_vs_gate86_stack.json`
- Shape match: true.
- RMS diff: 0.0.
- Max abs diff: 0.0.
- Speedup vs stack triangle bilinear: 1.171052774280753x.

## Known Limitations

- `auto` is intentionally conservative and does not change the default explicit
  `stack` mode.
- Non-bilinear resident matrix routes remain on stack dispatch until a future
  gate proves fused speed and numerical parity.
- Local normalization still prevents fused dispatch because resident LN mutates
  registered stack frames.
- This gate is a routing hardening gate, not a new CUDA kernel optimization.

## Next Step

S2-Gate 88 should either optimize fused Lanczos3 winsorized-sigma multi-pass
sampling or continue reducing resident registration orchestration costs. A
separate promotion gate can later make `auto` the recommended resident
high-speed preset once more routes are verified.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned routing policy and GLASS-generated
benchmark evidence only. It did not read, copy, summarize, or rework
proprietary implementation source. Input image directories were treated as
read-only.
