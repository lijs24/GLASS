# S2-Gate 588 Status: Non-Resident CUDA Fast Path Requires Policy Opt-In

## Gate

S2-Gate 588

## Completed

- Tightened non-resident light-integration engine selection so `--backend cuda`
  alone no longer bypasses `stack_engine_cpu`.
- Kept the older non-resident CUDA streaming accumulator available only when
  `IntegrationPolicy.allow_cuda_streaming_accumulator_fast_path=true`.
- Added `cuda_fast_path_policy_required` and a distinct reason
  `cuda_backend_stack_engine_default_requires_fast_path_policy` to
  `integration_engine_policy`.
- Added focused tests proving:
  - `backend=auto` keeps StackEngine when CUDA is available;
  - `backend=cuda` also keeps StackEngine without policy opt-in;
  - policy opt-in still enables the CUDA streaming accumulator for `backend=auto`
    and `backend=cuda`.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`, including the old Gate278 wording that had
  allowed explicit `--backend cuda` as a fast-path selector.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\integration.py tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py -k "integration_auto_keeps_stack_engine_default_when_cuda_is_available or integration_cuda_backend_keeps_stack_engine_default_without_policy or integration_cuda_fast_path_requires_explicit_policy or integration_cuda_backend_fast_path_still_requires_policy"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "nonresident_cuda_fast_path or integration_default_engine_policy or stack_engine_runtime_default"`
- Synthetic CLI validation:
  - `glass synthetic --out C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\synthetic_cuda_backend_stackengine\data --frames 4 --width 64 --height 64 --filter H --known-shift`
  - `glass scan --root ...\data --out ...\manifest.json`
  - `glass plan --manifest ...\manifest.json --out ...\processing_plan.json`
  - `glass run --plan ...\processing_plan.json --out ...\run --backend cuda --memory-mode tile --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --tile-size 16`
  - `glass pipeline-contract --run ...\run --out ...\pipeline_contract.json --markdown ...\pipeline_contract.md`
- Real 200-light resident regression:
  - `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\default_resident_regression --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
  - `glass compare` against the WBPP black-box fastIntegration master with the
    Gate588 output master and coverage map.
  - `glass acceptance-audit` with the Gate588 run-local
    `pipeline_contract.json`, `stack_engine_contract.json`, and
    `warp_quality_contract.json`.
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused integration tests: `4 passed, 18 deselected`.
- Focused pipeline-contract tests: `2 passed, 43 deselected`.
- Synthetic CLI pipeline contract: passed.
- Full pytest: `1254 passed in 53.57s`.

## Synthetic CLI Validation

- Run directory:
  `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\synthetic_cuda_backend_stackengine\run`
- Requested backend: `cuda`.
- Actual backend: `cpu`.
- `default_engine`: `stack_engine_cpu`.
- `tile_stack_mode`: `stack_engine_cpu`.
- `stack_engine_enabled`: `true`.
- `cuda_fast_path_policy_required`: `true`.
- Reason:
  `cuda_backend_stack_engine_default_requires_fast_path_policy`.
- DQ provenance schema: `stack_engine_dq_provenance`.
- Pipeline contract:
  `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\synthetic_cuda_backend_stackengine\pipeline_contract.json`
- Pipeline contract status: passed.

## Real 200-Light Validation

- Run directory:
  `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\default_resident_regression`
- Run failed stage: none.
- Stage timing sum: `7.859594299807213 s`.
- Pipeline contract: passed, `24` checks.
- StackEngine contract: passed, default promotion ready.
- Warp-quality contract: passed, `9` checks.
- Warp-quality active/masked frames: `193 / 7`.
- Hash parity versus Gate587: all six integration FITS artifacts matched.
- Compare versus WBPP black-box fastIntegration:
  - WBPP black-box reference elapsed: `1092.541 s`;
  - GLASS elapsed: `7.859594299807213 s`;
  - speedup: `139.00730219965664x`;
  - coverage190 fraction: `0.905523489118409`;
  - RMS difference: `0.005340835487175878`;
  - p99 absolute difference: `0.002133606873685496`.
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\acceptance_audit.json`
- Acceptance status: passed.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\synthetic_cuda_backend_stackengine\pipeline_contract.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\default_resident_regression\pipeline_contract.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\default_resident_regression\stack_engine_contract.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\default_resident_regression\warp_quality_contract.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\hash_parity_vs_gate587.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\acceptance_audit.json`
- `C:\glass_runs\phase2_s2_gate588_stackengine_fastpath_policy\acceptance_audit.md`

## Known Limitations

- This gate does not implement a CUDA-native non-resident StackEngine. It
  prevents the older non-resident CUDA streaming accumulator from silently
  replacing the StackEngine default.
- Users who need that old fast path for diagnostics must set
  `allow_cuda_streaming_accumulator_fast_path=true` in the integration policy.
- Resident CUDA all-VRAM execution is unchanged.

## Next Step

Continue substantive Phase 2 work on StackEngine default execution and DQ/mask
contract completeness. A useful next gate would move more master/integration
surfaces from full-frame in-memory StackEngine result materialization toward
true streaming StackEngine writes, or strengthen CPU/GPU StackEngine parity
around rejection/DQ maps.

## Clean-Room Compliance

Compliant. This gate uses only GLASS-owned source code, GLASS-generated
synthetic fixtures and run artifacts, user-owned 200-light outputs, and
user-generated WBPP black-box timing/reference outputs. It does not read,
copy, summarize, or rework external implementation source.
