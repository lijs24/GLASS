# S2-Gate 654 Status: Resident Registration Runtime Contract

## Gate

- Gate: S2-Gate 654
- Theme: resident registration/warp runtime contract for the default CUDA path
- Status: passed

## Completed Content

- Added `src/glass/engine/resident_registration_runtime_contract.py`.
- Resident postconditions now write `resident_registration_runtime_contract.json`
  after `warp_quality_contract.json` and before
  `resident_mainline_framework.json`.
- The contract verifies:
  - registration row count matches resident frame-mask count;
  - active/masked registration statuses match resident frame masks;
  - resident triangle catalog and descriptor work is batched;
  - native batched matrix warp is used when the runtime selects native batch
    warp;
  - native warp fallback count is zero;
  - active/reference/warped frame accounting closes;
  - native chunk count and chunk size cover warped frames;
  - geometric warp coverage closes when the run writes a coverage surface;
  - resident registration/warp component timing is present.
- Updated `phase2-mainline-audit` so
  `resident_registration_runtime_contract.json` is a required core artifact and
  `resident_registration_runtime_contract_passed` is an explicit check.
- Updated `resident_stage_ledger.json` expectations so resume/audit can detect
  the missing contract.
- Updated focused tests and resident CUDA postcondition expectations.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_registration_runtime_contract.py src\glass\engine\resident_stage_ledger.py src\glass\report\phase2_mainline_audit.py src\glass\cli.py tests\test_resident_registration_runtime_contract.py tests\test_phase2_mainline_audit.py tests\test_resident_mainline_framework.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_runtime_contract.py tests\test_phase2_mainline_audit.py tests\test_resident_mainline_framework.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_runtime_contract.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route tests\test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack
```

Real 200-light final validation:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --out C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\default_strict_final
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\default_strict_final --out C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\gate654_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\gate654_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe resident-regression-gate --candidate-run C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\default_strict_final --baseline-run C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\default_25us --out C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\gate654_regression_vs_gate653.json --markdown C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\gate654_regression_vs_gate653.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe doctor
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff focused checks: passed.
- Focused registration/mainline tests: `20 passed`.
- Focused regression after small-run fix: `9 passed`.
- Full pytest: `1375 passed in 61.98s`.

## Real 200-Light Results

- Final run:
  `C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\default_strict_final`
- `resident_registration_runtime_contract.json`: passed.
- `resident_mainline_framework.json`: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- `resident-regression-gate` versus Gate653 default 25us: passed.
- Regression elapsed ratio: `1.027729761074061`.
- GLASS elapsed time: `11.564531499985605 s`.
- Input lights: `200`.
- Active/masked frames: `193 / 7`.
- Registration rows: `200`.
- Warped non-reference frames: `192`.
- Native warp chunks: `24` chunks of `8` frames.
- Native warp fallback frames: `0`.
- Registration/warp component time: `0.2624766997760162 s`.
- Native warp total time: `0.4868998 s`.
- Warp throughput: `731.4935008091869 frames/s`.

## CUDA Availability

- CUDA wrapper importable: true.
- Native extension loaded: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package recommendation: `cuda13`; fallback order `cuda13`,
  `cuda12`, `cuda11`, `cpu`.

## Known Limits

- The new gate hardens runtime proof and failure behavior; it does not change
  registration math, warp kernels, DQ semantics, output pixels, or frame
  admission.
- Minimal-output synthetic runs can legitimately lack geometric coverage
  surfaces, so coverage closure is required only when the runtime writes an
  available coverage surface.
- Fused deferred warp paths are recorded but are not forced to satisfy the
  native batch-warp checks; the Phase 2 default 200-light path still requires
  the applicable contract to pass through the mainline audit.
- A first real attempt failed because the contract initially read triangle
  runtime fields from the resident artifact top level. The real schema stores
  those fields under `resident_registration`; the contract was fixed and the
  final clean run passed.

## Next Step

- Use this contract as a guardrail for a real execution change: reduce resident
  registration/warp orchestration or run the next nonzero source-DQ DQ/mask
  pipeline gate.

## Clean-Room Compliance

- This gate used only GLASS-owned runtime artifacts, tests, code, and
  user-owned benchmark outputs.
- No proprietary or external implementation source was read, copied,
  summarized, or reworked.
- Original image directories were treated as read-only.
