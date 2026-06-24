# S2-Gate 592 Status: Budgeted Resident Warp Chunk Capacity Default

Status: passed
Date: 2026-06-24

## Completed

- Promoted the `throughput-v3-io` resident runtime preset to request
  `resident_warp_chunk_capacity_frames=32`.
- Added `resident_warp_chunk_capacity_frames` to runtime preset override
  tracking, so a user-provided `--resident-warp-chunk-capacity-frames` still
  wins over the preset.
- Updated resident memory-admission application so selected chunk capacity is
  forwarded for `explicit`, `native_preferred`, and `reduced_for_budget`
  selections.
- Added run timing visibility for the effective resident warp chunk capacity.
- Updated focused tests for preset defaults, explicit overrides, run-level
  resident kwargs, and the CUDA triangle registration path.
- Ran real 200-light 16/32/64 chunk-capacity probes and a fresh default
  regression.
- Updated Phase 2 hardening docs and the algorithm-source independence log.

## Commands Run

- Focused preset/admission tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests/test_cli_smoke.py::test_resident_runtime_preset_manual_keeps_legacy_values tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_native_queue_override tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_warp_chunk_capacity_override tests/test_cli_smoke.py::test_cli_resident_run_passes_reduced_chunk_capacity_from_admission tests/test_cli_smoke.py::test_cli_resident_run_passes_preset_chunk_capacity_from_admission tests/test_cli_smoke.py::test_cli_resident_run_passes_explicit_chunk_capacity_from_admission`
- Focused CUDA/CLI regression after full-suite failure fix:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests/test_cli_smoke.py::test_cli_resident_run_passes_preset_chunk_capacity_from_admission tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_warp_chunk_capacity_override`
- Lint:
  `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_cli_smoke.py tests\test_resident_cuda_run.py`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`
- Real 200-light A/B probes:
  `glass run ... --resident-warp-chunk-capacity-frames 16`,
  `glass run ... --resident-warp-chunk-capacity-frames 32`, and
  `glass run ... --resident-warp-chunk-capacity-frames 64` under
  `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_ab`.
- Fresh default resident CUDA run:
  `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Compare:
  `glass compare --glass C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 8.134743199916557 --reference-time-seconds 1092.541 --glass-label "GLASS Gate592 warp chunk capacity default" --reference-label "WBPP black-box fastIntegration" --glass-scale 8.7644349571156089E-06 --glass-offset 0.0006274500691899127 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\compare_diagnostics_scaled_coverage190`
- Acceptance audit:
  `glass acceptance-audit --manifest C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression\manifest.json --glass-run C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression\warp_quality_contract.json --require-warp-quality-contract`
- CUDA doctor:
  `glass doctor --json C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\doctor.json`

## Test Results

- Focused preset/admission tests: 8 passed in 0.64 s.
- Focused CUDA/CLI regression tests: 3 passed in 1.09 s.
- Ruff: all checks passed.
- Full pytest: 1263 passed in 55.71 s.

## Real 200-Light Validation

A/B probe summary:

- Summary path:
  `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_ab\chunk_capacity_probe_summary.json`
- Chunk 16:
  - total elapsed: 8.168635300011374 s
  - native capacity: 16
  - hash parity versus Gate591: 6 / 6
- Chunk 32:
  - total elapsed: 7.881816200213507 s
  - native capacity: 32
  - hash parity versus Gate591: 6 / 6
- Chunk 64:
  - total elapsed: 8.174020099802874 s
  - native capacity: 64
  - hash parity versus Gate591: 6 / 6

Fresh default regression:

- Run path:
  `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression`
- Validation summary:
  `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\gate592_validation_summary.json`
- Effective route:
  - preset chunk capacity: 32
  - admission selected chunk capacity: 32
  - native effective chunk capacity: 32
  - native capacity source: `resident_memory_admission`
  - selected estimated peak: 56.49848874285817 GiB
  - selected headroom: 29.5341284442693 GiB
- GLASS elapsed: 8.134743199916557 s.
- Speedup versus Gate591 default: 1.0037264606078005x.
- WBPP black-box reference elapsed: 1092.541 s.
- Speedup versus reference: 134.30553038370115x.
- Compare RMS: 0.005340835487175878.
- Compare abs diff p99: 0.002133606873685496.
- Coverage190 fraction: 0.905523489118409.
- Acceptance audit: passed.
- Hash parity versus Gate591: 6 / 6 integration FITS files matched.

## CUDA

- CUDA available to GLASS: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_ab\chunk_capacity_probe_summary.json`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\default_resident_regression`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\gate592_validation_summary.json`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\compare_diagnostics_scaled_coverage190`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\acceptance_audit.json`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\acceptance_audit.md`
- `C:\glass_runs\phase2_s2_gate592_warp_chunk_capacity_default\doctor.json`

## Known Limitations

- The default speed gain is small and close to warm-cache runtime variance.
- Chunk 64 preserved output parity but was slower in registration/warp timing,
  so the promoted default stays at 32.
- The preset currently records the selected capacity as an explicit runtime
  request; future docs can distinguish user-explicit and preset-explicit more
  finely if needed.
- This gate does not change registration, warp, local normalization, rejection,
  or integration math.

## Next Step

Move away from preset-level tuning. The next substantive gate should target
resident registration/LN orchestration or a deeper execution-path invariant for
StackEngine/DQ masks that changes runtime behavior rather than adding reports.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned runtime scheduling and memory-admission
logic, GLASS tests/artifacts, user-owned 200-light inputs, and user-generated
external black-box timing/output artifacts. It does not read, copy, summarize,
or rework proprietary source code.
