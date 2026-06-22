# S2-Gate 489 Status: Resident Runtime Default Stack Dispatch Proof

## Gate

- Gate: S2-Gate 489
- Status: passed
- Scope: make the default resident CUDA runtime path auditable by explicitly
  applying `resident_integration_dispatch=stack` in the default
  `throughput-v1` preset, then prove on the real 200-light benchmark that a
  command without runtime-default flags resolves to CUDA resident stack
  dispatch and passes result/contract checks.

## Completed

- Updated `RESIDENT_RUNTIME_PRESETS["throughput-v1"]` to include
  `resident_integration_dispatch=stack`.
- Updated CLI smoke coverage so the default preset must record stack dispatch
  in `resident_runtime_preset_effective.applied`.
- Ran the M38 H-alpha 200-light command without explicit `--backend`,
  `--memory-mode`, `--resident-runtime-preset`, or
  `--resident-integration-dispatch`.
- Generated GLASS-vs-Gate488 compare, WBPP compare, speedup summary,
  StackEngine contract, pixel-verifying pipeline contract, acceptance audit,
  HTML report, and a gate summary JSON.

## Commands Run

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v1 tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v2_fused_applies_auto_dispatch tests\test_cli_smoke.py::test_resident_runtime_preset_manual_keeps_legacy_values tests\test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_overrides tests\test_cli_smoke.py::test_run_defaults_promote_resident_cuda_when_available
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py
```

Real default-route run:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
```

Real compare, contracts, acceptance, and report:

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate488_catalog_multistream_ab_real\runs\warm_catalog_multistream\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_gate488_master.json --glass-coverage-map C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\stack_engine_contract.md --expected-integration-engine cuda_resident_stack --resident-result-contract-json C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack\resident_result_contract.json
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_wbpp_scaled_coverage190.json --glass-scale 0.000008764434957115609 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\speedup\default_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\speedup\default_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack\manifest.json --glass-run C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\acceptance\default_threshold_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\acceptance\default_threshold_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --pipeline-contract-json C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\stack_engine_contract.json
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\runs\default_runtime_stack --out C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\reports\default_runtime_report.html --compare-json C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\acceptance\default_threshold_acceptance_audit.json --stack-engine-contract C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\stack_engine_contract.json --pipeline-contract C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\pipeline_contract.json
```

Full validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader
git diff --check
```

Two operator mistakes were corrected during validation:

- An initial focused pytest command used an incorrect test node name and ran no
  tests; the corrected node command passed.
- An initial pipeline-contract command passed the resident result contract as a
  calibration contract and failed with `FileNotFoundError`; the corrected
  pipeline-contract command passed. A parallel speedup-summary attempt also
  raced the compare JSON creation and was rerun successfully after the compare
  JSON existed.

## Test Results

- Focused default/preset tests: `5 passed in 0.21s`.
- CLI smoke module: `35 passed in 4.98s`.
- Ruff: `All checks passed!`.
- Full pytest: `1127 passed in 42.49s`.
- `git diff --check`: passed; only CRLF conversion warnings were reported.

## Real 200-Light Results

- Dataset: M38 H-alpha benchmark, `200` lights, `20` bias, `20` dark, `20`
  flats, user-generated WBPP black-box reference output.
- Output root:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real`.
- Runtime command omitted explicit default-routing flags:
  `--backend`, `--memory-mode`, `--resident-runtime-preset`, and
  `--resident-integration-dispatch`.
- Execution default resolution:
  - requested backend: `auto`;
  - requested memory mode: `resident`;
  - effective backend: `cuda`;
  - effective memory mode: `resident`;
  - explicit backend: `false`;
  - explicit memory mode: `false`;
  - reason: `resident_cuda_default`.
- Runtime preset: `throughput-v1`.
- Applied preset dispatch: `resident_integration_dispatch=stack`.
- Resident dispatch artifact:
  - mode: `stack`;
  - requested mode: `stack`;
  - selection reason: `explicit_stack`;
  - fused matrix used: `false`;
  - interpolation: `lanczos3`.
- Total elapsed: `19.54827229998773 s`.
- Warm `master_build_or_load`: `0.2983022999833338 s`.
- Warm `light_read_upload_calibrate`: `3.526385199977085 s`.
- Warm `resident_registration_component_accounted`:
  `2.1170830003353207 s`.
- Warm `resident_registration_warp`: `0.5607255008653738 s`.
- Warm `resident_integration`: `0.2865610999870114 s`.
- Warm `output_write`: `2.2916056999820285 s`.
- Catalog timing model: `batch_multistream_bulk_download_centroid_multistream`.
- Catalog batch size: `199`.
- Catalog stream count: `4`.
- Catalog sync phase count: `3`.
- Catalog native total: `0.2604065 s`.
- Default-vs-Gate488 GLASS master difference: RMS/p99/max all `0.0`.
- Default-vs-WBPP scaled coverage>=190 compare:
  - coverage fraction: `0.960532609259836`;
  - RMS: `0.0017794216505176163`;
  - p99 absolute difference: `0.00042621337808668863`;
  - max absolute difference: `0.5499989986419678`.
- Default route speedup vs WBPP: `55.889389263351205x`.
- StackEngine contract: passed,
  `default_path.status=resident_cuda_stack_engine_surface`,
  `default_promotion.ready=true`,
  `strict_native_stack_engine_ready=false`.
- Pipeline contract: passed with pixel verification enabled and no failed
  checks.
- Acceptance audit with attached StackEngine and pipeline contracts: `passed`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97887 MiB`.
- Sampled VRAM after final check: `824 MiB` used, `95776 MiB` free.

## Disk / Cleanup Note

- C: free after the gate: about `26.00 GiB`.
- No cleanup was required.
- If C: fills again, old `C:\glass_runs\phase2_s2_gate*` directories remain
  the preferred cleanup candidates. The source tree and user-owned raw image
  directories were not modified.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\gate489_real_default_summary.json`.
- Warm report:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\reports\default_runtime_report.html`.
- StackEngine contract:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\stack_engine_contract.json`.
- Pipeline contract:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\contracts\pipeline_contract.json`.
- Acceptance:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\acceptance\default_threshold_acceptance_audit.json`.
- Speedup:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\speedup\default_vs_wbpp_speedup_with_compare.json`.
- WBPP compare:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_wbpp_scaled_coverage190.json`.
- Gate488 baseline compare:
  `C:\glass_runs\phase2_s2_gate489_runtime_default_stack_ab_real\compare\default_vs_gate488_master.json`.

## Known Limitations

- This gate hardens and proves the resident CUDA default route. It does not
  promote resident CUDA to strict native `stack_engine_cpu`; strict native
  readiness remains false by design for resident surfaces.
- The default route still requires explicit scientific knobs for the current
  WBPP-parity benchmark recipe, such as triangle registration, Lanczos3 warp,
  flat-floor, and rejection mode.
- No CUDA kernels or image math changed. Any future default-route science
  change still needs a fresh 200-light compare and contract audit.

## Next Step

- Continue on Phase 2 core work:
  - strengthen DQ/mask pipeline contract around resident source-DQ sidecars and
    real data;
  - reduce remaining FITS read/materialize throughput floor;
  - keep real 200-light default-route regression after any runtime default or
    image-math change.

## Clean-Room Compliance

- This gate used GLASS-owned source code, GLASS-generated artifacts,
  user-owned M38 FITS inputs, and user-generated WBPP black-box timing/output
  artifacts only.
- It did not inspect or copy official PixInsight/WBPP/PJSR source code.
- It did not modify input image directories.
- It changed default-route metadata/preset evidence only; no proprietary
  formulas or external implementation details were imported.
