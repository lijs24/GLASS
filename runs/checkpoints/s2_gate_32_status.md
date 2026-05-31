# S2-Gate 32 Status: Resident Artifact Output Path Completeness

## Gate

S2-Gate 32 makes resident CUDA artifact records self-contained for output map
provenance. `resident_artifacts.json` now mirrors the same output map paths and
write-storage metadata recorded by `integration_results.json`, and the strict
200-light audit-map contract verifies those resident artifact paths directly.

## Completed Content

- Mirrored resident output paths into `resident_artifacts.json`:
  - `master_path`
  - `weight_map_path`
  - `coverage_map_path`
  - `low_rejection_map_path`
  - `high_rejection_map_path`
  - `dq_map_path`
- Mirrored `output_write_storage` into resident artifacts.
- Extended DQ provenance audit records with master and weight map path/existence
  fields.
- Added `required_resident_artifact_map_paths` to the benchmark contract so
  acceptance audit can require resident artifact paths for master, weight,
  coverage, DQ, low-rejection, and high-rejection maps.
- Added resident CUDA and acceptance-audit tests for path mirroring.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`
  - `benchmarks/phase2_m38_h_200_audit_maps_contract.json`

## Real-Data Run

Command:

```powershell
.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
```

Result:

- Run directory:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`
- Runtime: `31.835984100122005 s`
- Run state current stage: `integration`
- Run errors: none
- Active light frames accepted by audit: `193`
- All resident artifact map paths match integration output paths and exist:
  master, weight, coverage, low rejection, high rejection, and DQ.
- `output_write_storage` matches between integration output and resident
  artifact records.

## Comparison

Compare command used the Phase 1 scale/offset and coverage threshold:

```powershell
.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\integration\resident_master_H.fits --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_32_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 31.835984100122005 --reference-time-seconds 1092.541 --glass-label GLASS-S2G32-resident-artifact-paths --reference-label WBPP-blackbox
```

Results:

- Speedup vs reference: `34.3178020369665x`
- RMS diff: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Shape match: `true`

## Acceptance Audit

Command:

```powershell
.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_32_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_32.json --markdown C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_32.md --min-active-frames 190 --min-speedup 2.0
```

Result: `passed`.

Key checks:

- `contract_resident_artifact_map_path:master`: PASS
- `contract_resident_artifact_map_path:weight`: PASS
- `contract_resident_artifact_map_path:coverage`: PASS
- `contract_resident_artifact_map_path:dq`: PASS
- `contract_resident_artifact_map_path:low_rejection`: PASS
- `contract_resident_artifact_map_path:high_rejection`: PASS
- Low rejection positive pixels: `13074085`, matching DQ low-rejected pixels
  with delta `0`.
- High rejection positive pixels: `32318219`, matching DQ high-rejected pixels
  with delta `0`.
- Combined rejection sample sum: `62484986`.
- Provenance `rejected_sample_count`: `62484984`.
- Sample-sum delta: `2`, accepted by explicit tolerance `4`.

## Commands Run

- real-data resident audit-map run
- compare against the external reference master
- strict audit-map acceptance audit
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_science_output_maps_skip_rejection_count_files tests\test_resident_cuda_run.py::test_cli_resident_cuda_audit_output_maps_mirror_paths`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\report\benchmark_contract.py tests\test_resident_cuda_run.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`

## Test Results

- Targeted tests: `9 passed in 0.69s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `248 passed in 11.67s`.
- `git diff --check`: no whitespace errors.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- This gate improves artifact self-containment and auditability; it does not
  change resident CUDA image math.
- The strict audit-map benchmark is intentionally heavier than the release
  science-mode benchmark because it writes low/high rejection count maps.
- Rejection sample-sum tolerance remains necessary because persisted integer
  count maps can differ by a few samples from floating in-memory provenance.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The next high-value direction is to use the now self-contained resident
artifacts to harden report and benchmark review paths without rejoining
integration and resident records by convention.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned outputs and user-generated reference
timing/output data only. No external implementation source was read or used.
