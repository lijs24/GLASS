# S2-Gate 657 Status: Real 200-Light Source-DQ Probe Manifest

## Gate

S2-Gate 657.

## Completed Content

- Added `glass source-dq-probe-manifest`.
- The command reads an existing `processing_plan.json`, selects a light frame by
  `--frame-id`, `--frame-path`, or `--light-index`, and writes a diagnostic
  source-DQ sidecar FITS plus `source_dq_manifest.json` under the requested
  output directory only.
- The generated manifest can be fed back into
  `glass plan --source-dq-manifest`, so positive source-DQ real-data tests use
  the same normal planning boundary as user-provided sidecars.
- Added a CLI smoke test proving the generated probe sidecar binds to the
  selected light frame and contains exactly one DQ-invalid sample.
- Updated Phase 2 hardening, validation, and algorithm source documentation.
- Ran a real 200-light resident CUDA source-DQ positive validation using the
  existing M38 benchmark plan.

## Commands Run

```powershell
.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_source_dq_probe_manifest_binds_into_plan tests/test_cli_smoke.py::test_cli_synthetic_source_dq_manifest_binds_into_plan tests/test_plan_builder.py::test_processing_plan_binds_source_dq_manifest_to_light_frame
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_source_dq_probe_manifest_binds_into_plan

.venv\Scripts\glass.exe source-dq-probe-manifest --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_probe --frame-id F000061 --y 3211 --x 4800
.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --out C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\processing_plan_source_dq_probe.json --source-dq-manifest C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_probe\source_dq_manifest.json
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\processing_plan_source_dq_probe.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-framework-scope source_dq_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_positive_strict
.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_positive_strict --out C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\gate657_source_dq_positive_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\gate657_source_dq_positive_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_positive_strict\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\gate657_source_dq_positive_vs_gate656_default.json --glass-label "Gate657 source-DQ positive" --reference-label "Gate656 default" --glass-coverage-map C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_positive_strict\integration\resident_coverage_map_H.fits --min-coverage 190

.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
```

## Test Results

- Ruff over touched CLI/test files: passed.
- Focused source-DQ probe/planner tests: passed.
- Full pytest: `1380 passed in 61.70s`.
- Real 200-light source-DQ positive resident CUDA run: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- GLASS-vs-GLASS compare completed.

## CUDA Availability

- CUDA was available for this gate.
- GPU reported by `nvidia-smi`: NVIDIA RTX PRO 6000 Blackwell Workstation
  Edition, 97887 MiB, driver 596.21.

## Real 200-Light Evidence

- Evidence root:
  `C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204`.
- Probe manifest:
  `C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_probe\source_dq_manifest.json`.
- Probe sidecar:
  `C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_probe\source_dq\F000061_dq_probe.fits`.
- Source-DQ positive run:
  `C:\glass_runs\phase2_s2_gate657_real_source_dq_probe\runs_20260625_213204\source_dq_positive_strict`.
- Frame accounting: `200` lights, `193` active frames, `7` masked frames.
- Probe binding: frame `F000061`, pixel `[3211, 4800]`, flag `hot_pixel`.
- `resident_source_dq_execution.json` recorded
  `input_invalid_samples_before_rejection=1` and `applied_invalid_samples=1`.
- `registration_results.json` recorded
  `source_dq_registration_input_summary.invalid_samples=1`, with the
  `F000061` row carrying `source_dq_registration_input.invalid_samples=1`.
- `resident_registration_runtime_contract.json` passed, including:
  `source_dq_registration_visibility_closes`,
  `registration_results_carry_source_dq_input_if_positive`, and
  `registration_source_dq_input_matches_execution`.
- `integration_results.json` recorded
  `dq_coverage_provenance.input_invalid_samples_before_rejection=1`.

## Runtime and Comparison

- GLASS elapsed time: `14.132218099897727 s`.
- Reference black-box elapsed time: `1092.541 s`.
- Speedup: about `77.31x`.
- Native warp evidence:
  `triangle_warp_batch_native_total_s=0.4878145`,
  `triangle_warp_batch_fallback_frame_count=0`,
  `triangle_warp_batch_native_chunk_count=24`,
  `triangle_warp_batch_native_chunk_frames=8`.
- Component timing:
  - `resident_light_read_upload_calibrate=4.175479300087318 s`
  - `resident_registration_warp=0.26504389953333884 s`
  - `resident_local_normalization=0.34960509999655187 s`
  - `resident_integration=3.360753999906592 s`
  - `resident_output_write=0.34624189999885857 s`
- Gate657 source-DQ positive master compared against Gate656 default master:
  shape match true, compared pixels `50339858`, coverage fraction
  `0.8165268153742344`, p50/p90/p99 absolute difference
  `0.0` / `1.0081672668457031` / `5.743577690124511`, RMS difference
  `2.1730066333730473`, relative RMS difference `0.008350306636239585`.

## Known Limitations

- The probe manifest is a diagnostic input generator, not an astrophysical
  bad-pixel detector.
- The Gate657-vs-Gate656 master comparison is expected to differ because this
  gate intentionally changes one source frame before registration, local
  normalization, and integration.
- Default zero-source-DQ planning and resident CUDA execution are unchanged.
- Broader real DQ sources such as user bad-pixel maps, cosmetic correction
  outputs, and camera defect maps remain future work.

## Next Step

Return to Phase 2 mainline implementation work. The best next substantive gate
is to turn the controlled source-DQ sidecar boundary into a formal DQ/mask
pipeline input contract for real bad-pixel/cosmetic maps, or to attack the
measured resident CUDA hot path in light read/upload/calibrate plus integration
while preserving the Gate654-657 runtime contracts.

## Clean-Room Compliance

This gate is derived from GLASS-owned DQ flags, GLASS source-DQ manifest
binding, GLASS FITS writing, GLASS resident artifacts/tests, and user-owned
benchmark outputs. It did not inspect, copy, summarize, or rework external or
proprietary implementation source, and it did not modify original input image
directories.
