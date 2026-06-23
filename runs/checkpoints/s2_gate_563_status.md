# S2-Gate 563 Status: Resident Registration Quality Pipeline Contract

## Gate

S2-Gate 563 closes resident registration-quality decisions into the default
pipeline contract for resident CUDA integration outputs.

## Completed

- Added `resident_registration_quality.json` validation to
  `glass pipeline-contract`.
- Resident integration outputs now require the registration-quality artifact.
- For active quality-gated resident modes such as `similarity_cuda_triangle`,
  the contract verifies:
  - registration decision count equals input light frame count;
  - accepted/reference decision count equals integrated frame count;
  - rejected decision count equals zero-weight frame count;
  - rejected frame ids match `resident_frame_masks.json` masked frame ids.
- Preview/NCC diagnostic resident modes can keep an empty registration-quality
  ledger without failing the quality-closure checks.
- Added focused tests for missing artifact and mask/decision drift.
- Re-ran the real M38 H 200-light resident CUDA LN-on validation.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py::test_pipeline_contract_passes_resident_result_contract tests\test_pipeline_contract.py::test_pipeline_contract_requires_resident_registration_quality_for_resident_output tests\test_pipeline_contract.py::test_pipeline_contract_blocks_resident_registration_quality_mask_drift tests\test_pipeline_contract.py::test_default_resident_run_pipeline_contract_small_diagnostic_degenerate_is_nonblocking tests\test_cli_smoke.py::test_cli_guardrails_auto_discovers_run_resident_result_contract`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization on --resident-local-normalization-mode grid_mean_std --resident-local-normalization-tile-size 256 --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --out C:\glass_runs\phase2_s2_gate563_resident_registration_quality_contract\runs_20260623_181913\ln_on_registration_quality_contract`
- `.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate563_resident_registration_quality_contract\runs_20260623_181913\ln_on_registration_quality_contract --out C:\glass_runs\phase2_s2_gate563_resident_registration_quality_contract\runs_20260623_181913\ln_on_registration_quality_contract\pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate563_resident_registration_quality_contract\runs_20260623_181913\ln_on_registration_quality_contract\pipeline_contract.md`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused registration-quality pipeline tests: `5 passed in 0.25 s`.
- Wider pipeline/resident contract suite: `45 passed in 2.35 s`.
- Full pytest: `1204 passed in 45.44 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate563_resident_registration_quality_contract\runs_20260623_181913\ln_on_registration_quality_contract`
- Summary:
  `runs/checkpoints/s2_gate_563_resident_registration_quality_contract_summary.json`
- Shell elapsed: `7.4156317 s`.
- Run timing total: `7.059272500046063 s`.
- Pipeline contract: passed.
- Pipeline contract artifact was regenerated with the final S2-Gate 563 code.
- Registration mode: `similarity_cuda_triangle`.
- Registration-quality decisions: `200`.
- Decision statuses: `192 accepted / 1 reference / 7 rejected`.
- Active/rejected decisions: `193 / 7`.
- Rejected frame ids:
  `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`,
  `F000218`.
- Rejected frame ids match resident frame-mask masked ids exactly.
- Output master, weight map, coverage map, low/high rejection maps, and DQ
  map have SHA256 hashes identical to S2-Gate 562.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package try order reported by GLASS: `cuda13, cuda12, cuda11, cpu`.

## Artifacts

- `resident_registration_quality.json`
- `resident_frame_masks.json`
- `frame_accounting.json`
- `pipeline_contract.json`
- `pipeline_contract.md`
- `integration/resident_master_H.fits`
- `integration/resident_weight_map_H.fits`
- `integration/resident_coverage_map_H.fits`
- `integration/resident_low_rejection_map_H.fits`
- `integration/resident_high_rejection_map_H.fits`
- `integration/resident_dq_map_H.fits`

## Known Limitations

- This gate is a contract/completeness gate. It does not change star detection,
  registration fitting, warp, LN, rejection, integration math, CUDA kernels, DQ
  bit definitions, frame admission, or output pixels.
- Preview/NCC diagnostic resident modes intentionally record quality metadata
  without enforcing a nonempty registration-quality decision ledger.

## Next Step

Return to Phase 2 substantive mainline: StackEngine default path hardening,
resident DQ/mask pipeline execution, and real 200-light A/B performance and
result parity against the chosen comparison run.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned artifacts, tests, and user-owned real-run
outputs only. It does not read or depend on external proprietary source code,
does not modify input image directories, and does not copy external algorithms.
