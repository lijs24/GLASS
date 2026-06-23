# S2-Gate 574 Status: Calibrated Resident Reference Health

## Gate

S2-Gate 574 - add calibrated-sample evidence to the early resident reference
health gate.

## Completed Content

- Extended `src/glass/engine/resident_reference_health.py` with an
  opportunistic calibrated cross-check.
- If `--resident-master-cache-dir` contains a matching resident master cache,
  GLASS now memory maps the cached master bias, dark, and flat arrays, reads the
  same bounded sampled light crops used by the scout, calibrates those samples
  with the GLASS calibration policy, and runs the CPU star detector on calibrated
  samples.
- The calibrated check runs before resident reference admission, resident memory
  admission, calibration, registration, warp, LN, or integration.
- Added CLI options:
  - `--resident-reference-health-calibrated-min-star-ratio`
  - `--resident-reference-health-calibrated-max-rank-fraction`
- Default calibrated thresholds:
  - minimum calibrated star ratio `0.75`
  - maximum calibrated rank fraction `0.25`
- If no matching resident master cache is available, the artifact records
  `calibrated_crosscheck.status = unavailable` and preserves the Gate573 raw
  reference-health decision.
- Updated `docs/registration_model.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_reference_health.py src\glass\cli.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_reference_health_records_calibrated_master_cache_crosscheck tests/test_cli_smoke.py::test_resident_reference_health_calibrated_crosscheck_can_block_when_raw_thresholds_are_loose tests/test_cli_smoke.py::test_cli_resident_run_blocks_bad_cuda_reference_before_compute
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate574_calibrated_reference_health\explicit_cuda_catalog_should_fail_calibrated_early --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --resident-reference-scout-backend cuda
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate574_calibrated_reference_health\default_safe_auto_should_pass --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\glass.exe doctor
```

## Test Result

- Focused calibrated reference-health tests: `3 passed in 0.61s`.
- CLI smoke: `68 passed in 6.79s`.
- Related CLI/resident subset: `69 passed in 7.33s`.
- Full pytest final result: `1237 passed in 51.08s`.

## Real 200-Light Validation

Bad explicit CUDA scout with resident master cache:

- Run:
  `C:\glass_runs\phase2_s2_gate574_calibrated_reference_health\explicit_cuda_catalog_should_fail_calibrated_early`
- Result: failed at `resident_reference_health`.
- Total internal elapsed: `1.2345054001780227 s`.
- Timing stages:
  - `resident_reference_scout`: `0.323 s`
  - `resident_reference_health`: `0.911 s`
- It did not run resident reference admission, resident memory admission,
  calibration, registration, warp, LN, or integration.
- CUDA-selected reference: `F000215`.
- Raw CPU cross-check reference: `F000225`.
- Raw selected star ratio: `40 / 51 = 0.7843137254901961`.
- Raw selected rank fraction: `0.5238095238095238`.
- Calibrated cross-check reference: `F000079`.
- Calibrated selected star ratio: `13 / 30 = 0.43333333333333335`.
- Calibrated selected rank: `54 / 64`.
- Calibrated selected rank fraction: `0.8412698412698413`.
- Failed checks:
  - `selected_reference_cpu_star_ratio`
  - `selected_reference_cpu_rank_fraction`
  - `selected_reference_calibrated_star_ratio`
  - `selected_reference_calibrated_rank_fraction`
- Compared with Gate572's post-run health failure time
  `4.675011499901302 s`, this rejects the same bad reference about
  `3.786951032556957x` earlier while adding calibrated evidence.

Safe default scout:

- Run:
  `C:\glass_runs\phase2_s2_gate574_calibrated_reference_health\default_safe_auto_should_pass`
- Result: passed through integration.
- `resident_reference_health.json`: not written, because the default scout is
  CPU-backed and the health gate resolves to `off`.
- Resident registration health: `193 / 200` accepted, `7 / 200` rejected.
- Internal elapsed: `7.6488029001047835 s`.
- WBPP reference time used for continuity: `1092.541 s`.
- Speedup versus WBPP timing: `142.8381688309726x`.
- Master SHA256:
  `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`.
- The master SHA256 matches Gate570 through Gate573 safe default runs.

## CUDA

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- The calibrated cross-check is sampled and CPU-measured; it is not yet a
  GPU-resident calibrated reference-selection proof.
- The check depends on an existing matching resident master cache. No-cache
  runs keep the Gate573 raw-light evidence.
- CUDA scout remains explicit opt-in and is not promoted to default.

## Next Step

S2-Gate 575 should move this calibrated evidence closer to the GPU resident
path: either compute the calibrated reference-health catalog with CUDA kernels
or reuse resident calibrated-frame buffers before full integration. The next
gate should keep the safe 200-light master hash fixed while reducing CPU
orchestration and strengthening the path toward eventual CUDA scout promotion.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned resident master cache arrays, GLASS
calibration policy, GLASS FITS reads, GLASS CPU star metrics, and user-generated
benchmark outputs only. It does not inspect external implementation source,
does not modify input image directories, and does not change full-frame image
processing math.
