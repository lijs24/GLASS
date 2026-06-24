# S2-Gate 604 Status - Native-Completion Resident Runtime Default

## Gate

- Gate: S2-Gate 604
- Status: PASS
- Date: 2026-06-24
- Scope: Promote the real-data validated `throughput-v4-native-completion` resident runtime preset to the default resident runtime route.

## Completed Work

- Changed the default resident runtime preset from `throughput-v3-io` to `throughput-v4-native-completion`.
- Folded the v3 queue-read/drain/warp-chunk runtime defaults into the v4 native-completion preset.
- Updated CLI help text so `throughput-v4-native-completion` is described as the default route and v3 remains an explicit comparison route.
- Updated acceptance/release/default-promotion tests and contracts to require the v4 default token.
- Updated the Phase 2 algorithm hardening notes and algorithm-source ledger with the Gate604 promotion evidence.
- Preserved explicit v3 tests and artifact recognition so older evidence remains parseable.

## Real 200-Light Probe

Command:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe --backend cuda --memory-mode resident --resident-runtime-preset throughput-v4-native-completion --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
```

Result:

- Shell elapsed: 11.956485 s
- Run timing: 11.531422599917278 s
- Preset: `throughput-v4-native-completion`
- Native completion enabled: true
- Native completion policy: `cli_enabled`
- Native completion mode: `fits_u16be_bzero_native_completion_calibration_batch`
- Native completion count: 200 / 200
- Native completion workers: 16
- `light_read_upload_calibrate`: 3.076392799965106 s
- `light_calibration_batch_native_total`: 1.9265737 s
- Effective winsorized mode: `hardened_cpu_parity`
- Large-stack rejection coverage guard: 0.015 from `resident_auto_large_stack_coverage_guard`
- Hardened native total: 3.724918400053866 s

## Baseline Comparison

Gate603 baseline:

- Run: `C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened`
- Shell elapsed: 12.4060653 s
- Run timing: 11.991980199934915 s
- Acceptance speedup vs WBPP black-box timing: 91.10597097266134x

Gate604 v4 probe:

- Run: `C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe`
- Shell elapsed: 11.956485 s
- Run timing: 11.531422599917278 s
- Acceptance speedup vs WBPP black-box timing: 94.74468484121269x

Integration FITS hash/pixel comparison against Gate603:

- `resident_master_H.fits`: identical, max_abs 0.0, rms 0.0
- `resident_weight_map_H.fits`: identical, max_abs 0.0, rms 0.0
- `resident_coverage_map_H.fits`: identical, max_abs 0.0, rms 0.0
- `resident_low_rejection_map_H.fits`: identical, max_abs 0.0, rms 0.0
- `resident_high_rejection_map_H.fits`: identical, max_abs 0.0, rms 0.0
- `resident_dq_map_H.fits`: identical, max_abs 0.0, rms 0.0

## Compare And Acceptance Artifacts

Compare command:

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\compare_v4_completion_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 11.956485 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\compare_v4_completion_diagnostics_scaled_coverage190
```

Acceptance command:

```powershell
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe\manifest.json --glass-run C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\compare_v4_completion_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\acceptance_v4_completion_audit.json --markdown C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\acceptance_v4_completion_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\real_200_v4_completion_probe\warp_quality_contract.json
```

Acceptance result:

- Status: passed
- Speedup vs WBPP black-box timing: 94.74468484121269x
- Acceptance JSON: `C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\acceptance_v4_completion_audit.json`
- Acceptance Markdown: `C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\acceptance_v4_completion_audit.md`
- Compare HTML: `C:\glass_runs\phase2_s2_gate604_native_completion_default_probe\compare_v4_completion_vs_wbpp_fastintegration_scaled_coverage190.html`

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py -k "resident_runtime_preset" tests\test_acceptance_audit.py -k "runtime_preset_from_artifact or default_route_evidence_for_resident_tokens or native_completion_runtime_preset"
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_matrix.py::test_windows_release_matrix_passes_blackwell_default tests\test_windows_release_matrix.py::test_windows_release_matrix_blocks_failed_integration_engine_policy tests\test_default_promotion_manifest.py -k "default_runtime_preset or default_candidate or blackwell or ready"
.\.venv\Scripts\python.exe -m pytest -q
```

Test results:

- Ruff: passed
- Focused resident/default-promotion tests: passed
- Full pytest: 1280 passed in 52.30 s

## CUDA Status

- CUDA available to GLASS: yes
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Native backend: true
- Driver version: 596.21

## Known Limitations

- This gate promotes the already validated native-completion resident runtime route; it does not add a new registration or rejection algorithm.
- Native completion currently applies to the supported FITS `u16be`/`BZERO` resident calibration path and falls back according to the runtime policy outside that route.
- The real-data acceptance evidence uses the established M38 H 200-light dataset and the existing WBPP black-box fast-integration reference. The reference artifacts are external and are not checked into the repository.
- Segmented hardened winsorized processing for stacks larger than the current resident guard remains a follow-up item.

## Next Step

- Continue with a substantive Phase 2 gate focused on resident registration/warp orchestration, DQ propagation, or segmented hardened rejection beyond the current 200-light resident envelope.

## Clean-Room Compliance

- No official PixInsight WBPP/PJSR source code was read, copied, summarized, or reworked.
- PixInsight/WBPP was used only through user-generated black-box outputs and timing artifacts.
- Input image directories were treated as read-only.
