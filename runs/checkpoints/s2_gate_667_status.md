# S2-Gate 667 Status: Active-Registered CUDA Source-DQ Admission Default

## Gate

S2-Gate 667 promotes `active_registered` as the default admission semantics for
opt-in CUDA inline source-DQ routes. This applies to `cosmetic_cuda` and
`cosmetic_star_cuda` only. Default resident source-DQ remains `off`.

## Completed Content

- Added a CLI resident inline source-DQ admission resolver.
- CUDA inline source-DQ modes now resolve from requested `all` to effective
  `active_registered` when no explicit admission flag is supplied.
- Explicit `--resident-inline-source-dq-admission all` is preserved.
- CPU/non-CUDA inline source-DQ modes keep legacy `all`.
- Recorded admission policy provenance in:
  - `run_timing.json`;
  - `resident_artifacts.json`;
  - `resident_source_dq_strategy.json`.
- Updated CLI help text for run/audit.
- Added focused tests for default admission, explicit escape hatch,
  non-CUDA legacy behavior, strategy schema, and resident CUDA artifact
  propagation.
- Updated Phase 2 hardening docs, validation notes, and algorithm source log.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_cli_smoke.py::test_run_inline_cuda_source_dq_defaults_to_active_registered_admission `
  tests\test_cli_smoke.py::test_run_inline_cuda_source_dq_explicit_all_admission_is_preserved `
  tests\test_cli_smoke.py::test_run_non_cuda_source_dq_keeps_legacy_all_admission_default `
  tests\test_resident_source_dq_strategy.py::test_resident_source_dq_strategy_records_cuda_star_protected_inline_detector `
  tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_accepts_inline_star_protected_cosmetic_cuda_source_dq
```

Result: `5 passed in 1.67 s`.

```powershell
.\.venv\Scripts\python.exe -m glass.cli run `
  --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json `
  --backend cuda `
  --memory-mode resident `
  --integration-weighting none `
  --flat-floor 0.05 `
  --resident-star-threshold 350 `
  --resident-star-max-candidates 48 `
  --resident-star-tolerance-px 3 `
  --resident-ncc-sample-stride 4 `
  --resident-output-maps audit `
  --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final `
  --resident-inline-source-dq cosmetic_star_cuda `
  --resident-inline-source-dq-policy conservative `
  --resident-mainline-framework-gate strict `
  --resident-mainline-framework-scope inline_cosmetic_cuda_positive `
  --resident-mainline-min-lights 200 `
  --resident-mainline-min-active-frames 190 `
  --resident-mainline-max-masked-frames 10 `
  --resident-mainline-min-source-dq-invalid-samples 0 `
  --resident-mainline-min-source-dq-applied-samples 0 `
  --out C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\star_cuda_default_admission
```

Result: completed through integration. The command intentionally omitted both
`--resident-star-catalog-deterministic` and
`--resident-inline-source-dq-admission`.

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate `
  --baseline-run C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\star_cuda_default_det `
  --candidate-run C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\star_cuda_default_admission `
  --out C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\gate667_vs_gate666_regression.json `
  --markdown C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\gate667_vs_gate666_regression.md `
  --max-elapsed-ratio 1.20 `
  --min-active-frame-count 190 `
  --max-masked-frame-count 10
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m ruff check `
  src\glass\cli.py `
  src\glass\engine\resident_cuda.py `
  src\glass\engine\resident_source_dq_strategy.py `
  tests\test_cli_smoke.py `
  tests\test_resident_cuda_run.py `
  tests\test_resident_source_dq_strategy.py
```

Result: `All checks passed!`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `1408 passed in 62.60 s`.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\star_cuda_default_admission`.
- Total elapsed: `19.542332700220868 s`.
- Speedup versus `1092.541 s` black-box reference: `55.906376007386875x`.
- Resident calibration/integration stage: `17.822304400033318 s`.
- Effective admission policy:
  - requested: `all`;
  - effective: `active_registered`;
  - explicit: `false`;
  - source: `cuda_inline_default`;
  - escape hatch: `--resident-inline-source-dq-admission all`.
- Gate666 catalog default remains active:
  - `resident_source_dq_star_catalog_policy.source=cosmetic_star_cuda_default`;
  - `global_resident_star_catalog_deterministic=false`;
  - `star_catalog_source=resident_cuda_star_grid_top_nms_candidates_deterministic`.
- Source-DQ status counts:
  - `applied=10`;
  - `skipped_high_invalid_fraction=183`;
  - `skipped_admission_policy=7`.
- Source-DQ invalid/applied samples:
  - active: `147013 / 147013`;
  - all-frame: `147013 / 147013`.
- Source counts:
  - `resident_post_registration_pre_warp_cosmetic_star_cuda=192`;
  - `resident_post_registration_pre_warp_cosmetic_star_cuda_flush=8`.

## Regression Against Gate666

- Regression artifact:
  `C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\gate667_vs_gate666_regression.json`.
- Baseline:
  `C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\star_cuda_default_det`.
- Status: passed.
- Runtime elapsed ratio: `1.001834568712481`.
- Artifact difference count: `0`.
- Frame-accounting difference count: `0`.
- Frame-signature difference count: `0`.
- Registration difference count: `0`.
- Output difference count: `0`.
- Output numerical drift count: `0`.
- Candidate active/masked frames: `193 / 7`.

## CUDA

- CUDA available: yes.
- Native CUDA extension importable: yes.
- GPU observed in this environment:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: about `97886 MiB`.
- Driver: `596.21`.
- CUDA remains optional; CPU-only paths are covered by the full pytest run.

## Known Limits

- Default resident source-DQ remains `off`.
- This gate changes admission only after the user explicitly selects a CUDA
  inline source-DQ detector.
- It does not promote source-DQ to the default science route.
- It does not change registration, calibration, warp, local normalization,
  rejection, StackEngine pixel math, or output-map formulas.

## Next Step

Either evaluate star-protected source-DQ science-policy promotion against the
default route, or return to the larger resident execution bottlenecks:
integration/rejection and read/upload/calibrate overlap.

## Clean-Room Compliance

This gate uses GLASS-owned DQ/mask admission logic, GLASS resident CUDA
artifacts, GLASS tests, and user-owned benchmark outputs. It does not inspect,
copy, summarize, or rework external/proprietary implementation source, and it
does not modify input image directories.
