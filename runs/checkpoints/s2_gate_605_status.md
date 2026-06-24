# S2-Gate 605 Status - Source-DQ Registration Visibility Contract

## Gate

- Gate: S2-Gate 605
- Status: PASS
- Date: 2026-06-24
- Scope: Promote resident source-DQ ordering from implicit integration behavior to an auditable registration-catalog visibility contract.

## Completed Work

- Added source-DQ row fields:
  - `application_order`
  - `registration_catalog_visibility`
  - `registration_catalog_visible`
  - `registration_catalog_visibility_required`
- Non-inline source-DQ invalid masks now declare `calibration_pre_registration` and must be visible to resident registration catalogs.
- Deferred inline `cosmetic_cuda` rows now declare `post_registration_pre_warp` and are explicitly not catalog-required.
- Extended resident source-DQ summaries with application-order and registration-visibility counts.
- Extended `resident_source_dq_execution.json` with hard checks:
  - `application_order_declared`
  - `non_inline_source_dq_visible_to_registration_catalog`
- Added focused contract tests, including a negative case proving required source-DQ samples fail if delayed after registration.
- Updated Phase 2 hardening notes and algorithm-source ledger.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq_contract.py tests\test_resident_source_dq.py tests\test_cuda_resident_stack.py -k "source_dq"
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "source_dq or cosmetic"
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused source-DQ contract/closure tests: 19 passed, 51 deselected
- Focused resident CUDA source-DQ/cosmetic tests: 11 passed, 101 deselected
- Ruff: passed
- Full pytest: 1283 passed in 52.36 s

## Synthetic CUDA Validation

Root:

- `C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract`

Commands:

```powershell
.\.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\synthetic_source_dq --frames 6 --width 96 --height 96 --filter H --known-shift --source-dq-sidecars --source-dq-light-index 1 --source-dq-y 48 --source-dq-x 48
.\.venv\Scripts\glass.exe scan --root C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\synthetic_source_dq --out C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\manifest.json
.\.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\manifest.json --source-dq-manifest C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\synthetic_source_dq\source_dq_manifest.json --out C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\processing_plan.json
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\processing_plan.json --out C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\resident_run --backend cuda --memory-mode resident --until-stage integration --resident-registration similarity_cuda_triangle --resident-star-threshold 30 --resident-star-max-candidates 24 --resident-star-tolerance-px 3 --resident-star-grid-cols 4 --resident-star-grid-rows 4 --resident-star-catalog-deterministic --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-scan-candidates 96 --resident-triangle-nms-min-separation-px 2 --local-normalization off --integration-rejection none --integration-weighting none --resident-output-maps audit --resident-runtime-preset manual --resident-prefetch-frames 4 --resident-prefetch-workers 2 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 3 --resident-calibration-streams 2 --reference-frame-id light_000
```

Synthetic results:

- Scan: 15 science/calibration frames, 1 source-DQ sidecar skipped by scanner policy.
- Registration: 5 ok frames and 1 reference frame.
- Source-DQ summary:
  - `passed=true`
  - `input_invalid_samples_before_rejection=1`
  - `applied_invalid_samples=1`
  - `application_order_counts={"calibration_pre_registration": 6}`
  - `registration_catalog_visibility_counts={"pre_registration_catalog_visible": 6}`
  - `pre_registration_catalog_visible_invalid_samples=1`
  - `post_registration_deferred_invalid_samples=0`
  - `required_invalid_samples_not_visible_to_registration_catalog=0`
- Source-DQ execution contract:
  - `status=passed`
  - `application_order_declared=true`
  - `non_inline_source_dq_visible_to_registration_catalog=true`

## Real 200-Light Regression

Command:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate605_source_dq_registration_contract\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
```

Real 200-light results:

- Runtime preset: `throughput-v4-native-completion`
- `total_elapsed_s=11.487467100145295`
- Source-DQ fast-skip frame count: 200
- `required_invalid_samples_not_visible_to_registration_catalog=0`
- All six integration FITS outputs were SHA256-identical to the Gate604 default v4 probe:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`

## CUDA Status

- CUDA available to GLASS: yes
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Native backend: true
- Driver version: 596.21

## Known Limitations

- This gate formalizes source-DQ timing and artifact checks; it does not add a new star detector or change registration fitting.
- It does not implement segmented hardened winsorized reductions above 256 frames.
- Inline `cosmetic_cuda` remains allowed to defer until after registration by explicit contract because it can otherwise suppress real stellar cores.
- The source-DQ synthetic validation is intentionally small; the real 200-light regression protects the no-source-DQ default route but does not include a 200-light source-DQ sidecar dataset.

## Next Step

- Continue with a substantive gate on resident registration/warp orchestration or segmented hardened winsorized reductions above the current 256-frame native limit.

## Clean-Room Compliance

- No official PixInsight WBPP/PJSR source code was read, copied, summarized, or reworked.
- Validation used GLASS synthetic artifacts, GLASS runtime artifacts, user-owned 200-light inputs, and user-generated black-box reference timing only.
- Input image directories were treated as read-only.
