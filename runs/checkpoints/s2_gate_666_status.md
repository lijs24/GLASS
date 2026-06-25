# S2-Gate 666 Status: Default Deterministic Star CUDA Source-DQ Catalog

## Gate

S2-Gate 666 promotes deterministic star cataloging from a manual Gate665 flag
to the default source-DQ catalog policy for the opt-in
`--resident-inline-source-dq cosmetic_star_cuda` route.

## Completed Content

- Added a CLI source-DQ star-catalog policy resolver.
- `cosmetic_star_cuda` source-DQ now defaults to deterministic resident CUDA
  grid/NMS star catalogs without requiring
  `--resident-star-catalog-deterministic`.
- The global resident registration star-catalog determinism flag remains
  unchanged and is not implicitly promoted.
- Recorded the effective source-DQ catalog policy in `run_timing.json`.
- Recorded the source-DQ catalog policy source in `resident_artifacts.json`.
- Recorded the strategy policy source in `resident_source_dq_strategy.json`.
- Added tests for default policy, non-star non-promotion, strategy schema,
  explicit diagnostic override, and a CUDA resident smoke without the manual
  deterministic flag.
- Updated Phase 2 hardening docs, validation notes, and algorithm source log.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_cli_smoke.py::test_run_resident_inline_star_cuda_source_dq_defaults_to_deterministic_catalog `
  tests\test_cli_smoke.py::test_run_non_star_inline_source_dq_does_not_promote_catalog_determinism `
  tests\test_resident_source_dq_strategy.py::test_resident_source_dq_strategy_records_cuda_star_protected_inline_detector `
  tests\test_resident_source_dq_strategy.py::test_resident_source_dq_strategy_allows_explicit_nondeterministic_star_cuda_catalog `
  tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_accepts_inline_star_protected_cosmetic_cuda_source_dq
```

Result: `5 passed in 1.60 s`.

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
  --resident-inline-source-dq-admission active_registered `
  --resident-mainline-framework-gate strict `
  --resident-mainline-framework-scope inline_cosmetic_cuda_positive `
  --resident-mainline-min-lights 200 `
  --resident-mainline-min-active-frames 190 `
  --resident-mainline-max-masked-frames 10 `
  --resident-mainline-min-source-dq-invalid-samples 0 `
  --resident-mainline-min-source-dq-applied-samples 0 `
  --out C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\star_cuda_default_det
```

Result: completed through integration.

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate `
  --baseline-run C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_a `
  --candidate-run C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\star_cuda_default_det `
  --out C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\gate666_vs_gate665_regression.json `
  --markdown C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\gate666_vs_gate665_regression.md `
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

Result: `1405 passed in 61.22 s`.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\star_cuda_default_det`.
- The command intentionally omitted `--resident-star-catalog-deterministic`.
- Total elapsed: `19.5065466001397 s`.
- Speedup versus `1092.541 s` black-box reference: `56.00894009563822x`.
- Resident calibration/integration stage: `17.784652900067158 s`.
- Source-DQ catalog policy:
  - `source=cosmetic_star_cuda_default`;
  - `global_resident_star_catalog_deterministic=false`;
  - `resident_inline_source_dq_star_catalog_deterministic=true`;
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

## Regression Against Gate665

- Regression artifact:
  `C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\gate666_vs_gate665_regression.json`.
- Baseline:
  `C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_a`.
- Status: passed.
- Runtime elapsed ratio: `0.9818901907545167`.
- Artifact difference count: `0`.
- Frame-accounting difference count: `0`.
- Frame-signature difference count: `0`.
- Registration difference count: `0`.
- Output difference count: `0`.
- Output numerical drift count: `0`.
- Candidate pipeline contract: passed.
- Candidate StackEngine contract: passed.
- Candidate resident result contract: passed.
- Candidate source-DQ execution contract: passed.
- Candidate active/masked frames: `193 / 7`.

## CUDA

- CUDA available: yes.
- Native CUDA extension importable: yes.
- GPU observed in this environment:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: about `97886 MiB`.
- CUDA remains optional; CPU-only tests are covered by the full pytest run.

## Known Limits

- Default resident source-DQ is still `off`.
- This gate promotes deterministic catalog semantics only after the user
  explicitly selects `cosmetic_star_cuda`.
- It does not promote star-protected source-DQ to the default science route.
- It does not change registration star-catalog determinism defaults.
- It does not change calibration, warp, local normalization, rejection,
  StackEngine pixel math, or output-map formulas.

## Next Step

Evaluate whether the star-protected source-DQ policy is scientifically suitable
for broader promotion against the default route, or return to the larger
resident execution bottlenecks: integration/rejection and read/upload/calibrate
overlap.

## Clean-Room Compliance

This gate uses GLASS-owned CUDA/source-DQ/catalog wrappers, GLASS tests, GLASS
artifacts, and user-owned benchmark outputs. It does not inspect, copy,
summarize, or rework external/proprietary implementation source, and it does
not modify input image directories.
