# S2-Gate 562 Status: Resident DQ/Mask Pipeline Contract Closure

## Gate

S2-Gate 562: make resident frame-level mask admission and resident pixel-level
DQ closure mandatory parts of the default resident pipeline contract.

## Completed

- Added `resident_frame_mask_admission_contract` to
  `glass pipeline-contract`.
- Resident integration outputs now require `resident_frame_masks.json`.
- Frame masks must:
  - pass their own group contracts;
  - have zero unaudited zero-weight frames;
  - close against `frame_accounting.json` when frame accounting is present.
- Added `resident_dq_pixel_closure_contract` to `glass pipeline-contract`.
- Resident integration outputs now require `resident_dq_pixel_closure.json`.
- Pixel closure must:
  - pass all group checks;
  - have zero failed groups;
  - match resident frame-mask active and masked frame counts.
- `pipeline_contract.md` now summarizes resident frame masks and resident DQ
  pixel closure.
- Updated guardrails and pipeline contract tests so resident fixtures carry the
  now-required DQ/mask artifacts.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py::test_pipeline_contract_passes_resident_result_contract tests\test_pipeline_contract.py::test_pipeline_contract_requires_resident_frame_masks_for_resident_output tests\test_pipeline_contract.py::test_pipeline_contract_blocks_resident_frame_mask_accounting_drift tests\test_pipeline_contract.py::test_pipeline_contract_blocks_resident_dq_pixel_closure_failure tests\test_pipeline_contract.py::test_default_resident_run_pipeline_contract_small_diagnostic_degenerate_is_nonblocking`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_auto_discovers_run_resident_result_contract tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization on --resident-local-normalization-mode grid_mean_std --resident-local-normalization-tile-size 256 --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --out C:\glass_runs\phase2_s2_gate562_resident_dq_mask_pipeline_contract\runs_20260623_181058\ln_on_dq_mask_contract`

## Test Results

- Focused new DQ/mask contract tests: `5 passed in 0.26 s`.
- Wider pipeline/resident contract suite: `43 passed in 2.26 s`.
- Guardrails resident fixture plus pipeline suite: `41 passed in 1.66 s`.
- Full pytest: `1202 passed in 45.09 s`.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate562_resident_dq_mask_pipeline_contract\runs_20260623_181058\ln_on_dq_mask_contract`.
- Baseline for output comparison:
  `C:\glass_runs\phase2_s2_gate561_resident_ln_frame_accounting\runs_20260623_180404\ln_on_closure`.
- Checkpoint summary:
  `runs/checkpoints/s2_gate_562_resident_dq_mask_pipeline_contract_summary.json`.
- Shell elapsed: `7.204561699999999 s`.
- Run timing total: `6.844856300042011 s`.
- Pipeline contract status: `passed`.
- Resident frame-mask admission contract: `passed`.
- Resident DQ pixel closure contract: `passed`.
- Resident source-DQ execution contract: `passed`.
- Local-normalization contract audit: `passed`.
- Frame accounting conflicts: `0`.
- Resident frame masks: `200` frames, `193` active, `7` masked,
  `0` unaudited zero-weight frames.
- Resident DQ pixel closure: `1` group, `0` failed groups.
- Output comparison to Gate561 LN-on:
  master, weight map, coverage map, low-rejection map, high-rejection map, and
  DQ map SHA256 hashes all match exactly.

## CUDA

- CUDA extension importable: yes.
- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- This gate is a default pipeline-contract hardening gate. It does not change
  calibration, registration, local normalization, warp, rejection, weighting,
  DQ bit definitions, frame admission, CUDA kernels, or output pixels.
- The gate proves resident DQ/mask artifacts are present and internally
  consistent; it does not improve the scientific choice of rejected frames.

## Next Step

Continue Phase 2 mainline with a substantive algorithm/runtime gate: use this
closed DQ/mask contract surface as the baseline for resident registration/warp
or StackEngine default-path improvements, and keep the 200-light run as the
numerical/performance guard.

## Clean-Room Compliance

Compliant. This gate consumes only GLASS-generated resident frame-mask,
resident DQ pixel-closure, frame-accounting, local-normalization, and pipeline
artifacts plus user-owned 200-light data through GLASS. It does not inspect
external proprietary source, modify input image directories, or copy external
algorithms.
