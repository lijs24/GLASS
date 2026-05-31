# S2-Gate 24 Status: Fused Resident Warp Coverage Accumulation

## Gate

S2-Gate 24: Fused resident warp coverage accumulation.

## Completed Content

- Fused resident geometric warp coverage accumulation into the CUDA warp
  kernels for:
  - integer translation
  - bilinear translation
  - matrix bilinear warp
  - matrix Lanczos 3 warp
- Preserved standalone Python warp wrappers by passing a null accumulator.
- Kept full-frame coverage accounting for unwarped active resident frames on
  the existing native method.
- Removed the resident post-warp coverage accumulation launch from warped
  resident-frame methods.
- Preserved geometric coverage frame counts, DQ provenance, partial
  `WARP_EDGE` marking, and resident output-map semantics.
- Updated Phase 2 gate planning and algorithm source tracking.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "%CD%\.venv\Scripts\cmake.exe" --build build\native-cuda-glass --config Release'`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py tests/test_cuda_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps science --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\integration\resident_master_H.fits --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_compare.html --glass-time-seconds 30.949304700363427 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_24_FUSED_WARP_COVERAGE --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_compare.json --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_24.json --markdown C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_24.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531 --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_report.html`

## Test Results

- Native CUDA build: passed; build system reported `ninja: no work to do`
  after the already-built fused kernel objects.
- Ruff: `All checks passed`
- Focused resident/CUDA tests: `41 passed in 2.04s`
- Full pytest: `239 passed in 17.22s`
- 200-light resident CUDA benchmark: passed
- Compare report generation: passed
- Acceptance audit: passed
- HTML run report generation: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Artifact

- Run directory:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531`
- Master:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\integration\resident_master_H.fits`
- Coverage map:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\integration\resident_coverage_map_H.fits`
- DQ map:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\integration\resident_dq_map_H.fits`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_compare.html`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_24.md`
- HTML run report:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_report.html`

## Real-Data Metrics

- Total GLASS runtime: `30.949304700363427 s`
- External reference runtime: `1092.541 s`
- Speedup vs reference: `35.30098690673237x`
- Active frames: `193`
- Geometric warp coverage frame count: `193`
- Geometric frame-count match: `true`
- Geometric partial pixels: `5,396,832`
- Geometric zero pixels: `0`
- Geometric full pixels: `56,254,368`
- Comparison shape match: `true`
- Coverage fraction at min coverage 190: `0.9574613308418977`
- RMS difference after accepted scale/offset: `0.001558294284488301`
- P99 absolute difference after accepted scale/offset:
  `0.00043095467146486016`

## Performance Or Numerical Regression Note

The total runtime is within the Phase 2 benchmark contract:

- Release baseline: `30.361440100008622 s`
- Gate 24 runtime: `30.949304700363427 s`
- Regression factor: about `1.019x`
- Contract maximum: `39.46987213001121 s`

The acceptance audit passed all hard checks. Non-blocking performance
diagnostics still flag output writing, GC, resident integration,
light H2D/calibrate/store, and cumulative light decode timings as optimization
targets. The resident registration/warp timing was `12.356555198784918 s`,
about `1.133x` the release diagnostic baseline.

Numerical agreement is unchanged from the accepted S2-Gate 22 coverage run:
RMS `0.001558294284488301`, P99 absolute difference
`0.00043095467146486016`, and shape match `true`.

## Known Limitations

- Fused accumulation assumes one CUDA thread owns each output pixel for a warp
  launch. That is true for the current resident warp kernels.
- The geometric accumulator is per run, not per frame.
- Unwarped active frames still use a separate full-frame coverage method.
- Standalone warp wrappers do not expose a fused accumulator, by design.
- Output writing and some resident timing diagnostics remain above release
  diagnostic baselines even though total runtime passes the hard contract.

## Next Step

Proceed to a new compute-facing Phase 2 gate that reduces resident
registration/warp orchestration overhead or moves more DQ/mask semantics into
the formal StackEngine and resident pipeline contracts.

## Clean-Room Compliance

Compliant. This gate changed only GLASS-owned CUDA/native code, GLASS-owned
documents, and GLASS-generated artifacts. Validation used user-generated
reference outputs and timing metadata as a black-box comparison. No proprietary
source code was read, copied, summarized, or reworked.
