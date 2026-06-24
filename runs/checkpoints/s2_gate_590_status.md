# S2-Gate 590 Status: Source-DQ CLI Manifest Binding

## Gate

- Gate: S2-Gate 590
- Title: Source-DQ CLI manifest binding into resident integration
- Status: passed
- Date: 2026-06-24

## Completed Content

- Added optional `FrameRecord.source_dq_mask_path`.
- Added `glass synthetic --source-dq-sidecars` plus sidecar location controls.
- Added `glass plan --source-dq-manifest` to bind explicit source-DQ sidecar manifests onto light frame records.
- Updated the resident CUDA source-DQ sidecar test so it uses the CLI manifest binding route instead of manually editing `processing_plan.json`.
- Added synthetic/planner/CLI tests for the new source-DQ manifest workflow.
- Updated Phase 2 hardening docs and algorithm independence log.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_synthetic_generator.py tests/test_plan_builder.py tests/test_cli_smoke.py::test_cli_synthetic_source_dq_manifest_binds_into_plan tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_plan_source_dq_sidecar`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\synthetic_data --frames 4 --width 64 --height 64 --filter H --known-shift --source-dq-sidecars --source-dq-light-index 1 --source-dq-y 12 --source-dq-x 17`
- `.venv\Scripts\glass.exe scan --root C:\glass_runs\phase2_s2_gate590_source_dq_cli\synthetic_data --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\manifest.json`
- `.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate590_source_dq_cli\manifest.json --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\processing_plan.json --source-dq-manifest C:\glass_runs\phase2_s2_gate590_source_dq_cli\synthetic_data\source_dq_manifest.json`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate590_source_dq_cli\processing_plan.json --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\resident_run --backend cuda --memory-mode resident --resident-runtime-preset manual --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration off --resident-prefetch-frames 2 --resident-prefetch-workers 2 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 2 --resident-calibration-streams 2 --resident-output-maps audit`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 8.27696210006252 --reference-time-seconds 1092.541 --glass-label "GLASS Gate590 source-DQ CLI binding" --reference-label "WBPP black-box fastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression\manifest.json --glass-run C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate590_source_dq_cli\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate590_source_dq_cli\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate590_source_dq_cli\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression\warp_quality_contract.json --require-warp-quality-contract`
- `.venv\Scripts\glass.exe doctor --json C:\glass_runs\phase2_s2_gate590_source_dq_cli\doctor.json`

## Test Results

- Focused tests: `7 passed in 1.03s`.
- Full pytest: `1259 passed in 55.75s`.

## Validation Results

- Synthetic source-DQ CLI run:
  - source-DQ applied frames: `1 / 4`;
  - applied invalid samples: `1`;
  - integration observed invalid samples: `1`;
  - `resident_source_dq_integration_effect_contract`: passed.
- Real 200-light run:
  - GLASS time: `8.27696210006252 s`;
  - WBPP black-box reference time: `1092.541 s`;
  - speedup: `131.9978256263548x`;
  - coverage190 fraction: `0.905523489118409`;
  - RMS difference: `0.005340835487175878`;
  - p99 absolute difference: `0.002133606873685496`;
  - pipeline contract: passed, `25` checks;
  - acceptance audit: passed;
  - SHA256 parity versus Gate589: `6 / 6` integration FITS matched.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Native extension loaded: yes.

## Artifacts

- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\gate590_validation_summary.json`
- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\resident_run`
- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\default_resident_regression`
- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\acceptance_audit.json`
- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\hash_parity_vs_gate589.json`
- `C:\glass_runs\phase2_s2_gate590_source_dq_cli\doctor.json`

## Known Limitations

- Source-DQ sidecars placed under the scan root are still scanned as `unknown` FITS frames. The explicit manifest prevents them from entering light/calibration grouping, but future scanner include/exclude policy should make this cleaner.
- Binding is explicit manifest-driven; automatic discovery of sidecars is not implemented.
- This gate does not optimize registration/warp throughput or change image math.

## Next Step

- Return to substantive Phase 2 performance work: resident registration/warp batching and/or default-path source-DQ/mask pipeline ergonomics without more report-only gates.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned DQ flags, GLASS synthetic data, GLASS resident CUDA artifacts, user-owned 200-light data, and user-generated WBPP black-box outputs/timing only.
- No official PixInsight/WBPP/PJSR source was read, summarized, copied, or modified.
