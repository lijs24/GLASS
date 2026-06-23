# S2-Gate 573 Status: Early Resident Reference Health Gate

## Gate

S2-Gate 573 - move the explicit CUDA reference-scout failure mode before
resident memory admission and resident CUDA compute.

## Completed Content

- Added `src/glass/engine/resident_reference_health.py`.
- Added early `resident_reference_health.json` artifact.
- Added CLI options:
  - `--resident-reference-health-gate {auto,off,warn,fail}`
  - `--resident-reference-health-min-cpu-star-ratio`
  - `--resident-reference-health-max-cpu-rank-fraction`
- Default `auto` resolves to `fail` only when the scout artifact records
  `catalog_backend = cuda`; CPU/default scout resolves to `off`.
- The gate reruns a bounded CPU raw-light scout over the same sampled frame set
  and checks whether the CUDA-selected reference is also plausible under the CPU
  detector.
- The gate runs after `resident_reference_scout` and before
  `resident_reference_admission`, `resident_memory_admission`, calibration,
  registration, warp, LN, and integration.
- Updated `docs/registration_model.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_reference_health.py src\glass\cli.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_reference_health_passes_cuda_reference_with_cpu_crosscheck tests/test_cli_smoke.py::test_resident_reference_health_blocks_cuda_reference_cpu_crosscheck_miss tests/test_cli_smoke.py::test_cli_resident_run_blocks_bad_cuda_reference_before_compute tests/test_cli_smoke.py::test_cli_resident_run_auto_reference_scout_feeds_reference_admission
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate573_reference_health\explicit_cuda_catalog_should_fail_early --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --resident-reference-scout-backend cuda
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate573_reference_health\default_safe_auto_should_pass --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\glass.exe doctor
```

## Test Result

- Focused reference-health/CLI tests: `4 passed in 0.61s`.
- CLI smoke: `66 passed in 7.04s`.
- Related CLI/resident subset: `67 passed in 7.35s`.
- Full pytest final result: `1235 passed in 51.31s`.

## Real 200-Light Validation

Bad explicit CUDA scout:

- Run:
  `C:\glass_runs\phase2_s2_gate573_reference_health\explicit_cuda_catalog_should_fail_early`
- Result: failed at `resident_reference_health`.
- Timing stages:
  - `resident_reference_scout`: `0.353 s`
  - `resident_reference_health`: `0.390 s`
- Total internal elapsed: `0.7426516999257728 s`.
- It did not run `resident_reference_admission`, `resident_memory_admission`,
  resident CUDA calibration, registration, warp, LN, or integration.
- CUDA-selected reference: `F000215`.
- CPU cross-check reference: `F000225`.
- Selected CPU star ratio: `40 / 51 = 0.7843137254901961`.
- Selected CPU rank: `34 / 64`.
- Selected CPU rank fraction: `0.5238095238095238`.
- Failed checks:
  - `selected_reference_cpu_star_ratio`
  - `selected_reference_cpu_rank_fraction`
- Compared with Gate572's post-run health failure time
  `4.675011499901302 s`, this rejects the same bad reference about
  `6.295025649801333x` earlier.

Safe default scout:

- Run:
  `C:\glass_runs\phase2_s2_gate573_reference_health\default_safe_auto_should_pass`
- Result: passed through integration.
- `resident_reference_health.json`: not written, because the default scout is
  CPU-backed and the health gate resolves to `off`.
- Resident registration health: `193 / 200` accepted, `7 / 200` rejected.
- Internal elapsed: `7.832895599771291 s`.
- WBPP reference time used for continuity: `1092.541 s`.
- Speedup versus WBPP timing: `139.48111347633696x`.
- Master SHA256:
  `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`.
- The master SHA256 matches Gate570, Gate571, and Gate572 safe default runs.

## CUDA

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- This is still a sampled raw-light cross-check, not a calibrated-frame
  registration proof.
- The CPU cross-check is deliberately default-enabled only for explicit CUDA
  scout artifacts; the safe CPU scout path remains unchanged.
- The CUDA scout is still not promoted to default.

## Next Step

S2-Gate 574 should move from raw-light cross-checking toward calibrated-frame or
GPU-resident reference-health evidence. The goal is to make CUDA reference
selection itself robust enough to consider future default promotion, while
preserving the safe 200-light master hash and resident registration health.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned scout artifacts, GLASS FITS reads,
GLASS CPU star metrics, and user-generated benchmark outputs only. It does not
inspect external implementation source, does not modify input image directories,
and does not change image-processing math.
