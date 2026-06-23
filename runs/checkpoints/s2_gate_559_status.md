# S2-Gate 559 Status: Default Resident Pipeline Contract Artifact

## Gate

S2-Gate 559: make the GLASS-owned pipeline contract a default resident CUDA
`glass run` artifact.

## Completed

- Added default resident-run generation of `pipeline_contract.json` and
  `pipeline_contract.md` after real resident integration output exists.
- Attached the generated contract to `run_state.json` as a
  `pipeline_contract` artifact.
- Recorded `pipeline_contract` in `run_timing.json` as a real stage.
- Made blocking contract failures mark `failed_stage=pipeline_contract` and
  return a non-zero CLI status.
- Preserved non-blocking behavior for two-light diagnostic runs whose only
  failed resident-result check is `active_frame_count_not_degenerate`; those
  runs still write the failed contract and a `run_state` warning.
- Updated the run-level contract parser for resident minimal output-map policy
  and resident in-VRAM local-normalization `groups[].frame_results`.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\report\pipeline_contract.py src\glass\cli.py tests\test_pipeline_contract.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py::test_pipeline_contract_respects_resident_minimal_output_map_policy tests/test_pipeline_contract.py::test_pipeline_contract_accepts_resident_local_norm_group_rows tests/test_pipeline_contract.py::test_default_resident_run_pipeline_contract_small_diagnostic_degenerate_is_nonblocking tests/test_pipeline_contract.py::test_default_resident_run_pipeline_contract_failure_marks_state tests/test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_rejects_low_quality_matrix`
- `.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_resident_result_contract.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --out C:\glass_runs\phase2_s2_gate559_pipeline_contract_default\runs_20260623_174914\default_contract`

## Test Results

- Focused contract edge and resident CUDA regression tests:
  `10 passed in 1.59 s`.
- Pipeline/resident contract suite:
  `54 passed in 2.19 s`.
- Full pytest:
  `1194 passed in 44.43 s`.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate559_pipeline_contract_default\runs_20260623_174914\default_contract`.
- Baseline for bitwise comparison:
  `C:\glass_runs\phase2_s2_gate557_remaining_set\runs_20260623_171847\default_remaining_set`.
- Shell elapsed: `5.3690378 s`.
- Run timing total: `5.012140900071245 s`.
- Resident calibration/integration stage: `4.9870452000177465 s`.
- Pipeline contract stage: `0.021973300026729703 s`.
- Contract status: `passed`.
- Frame accounting: `200` input light frames, `193` integrated frames,
  `7` zero-weight frames.
- Master, weight, coverage, low-rejection, and high-rejection FITS outputs are
  bitwise identical to Gate557; max absolute numeric diff and RMS diff are both
  `0`.

## CUDA

- CUDA extension importable: yes.
- CUDA available: yes.
- Resident CUDA features used: resident stack, Lanczos3 warp, winsorized sigma
  rejection, audit output maps.

## Known Limitations

- This gate does not change registration, calibration, rejection, weighting,
  local-normalization math, or CUDA kernels.
- Two-light diagnostic active-frame degeneracy is non-blocking by design, but
  still visible as a failed pipeline contract and run warning.
- Full PixInsight/WBPP equivalence remains based on the previously generated
  Gate558 A/B comparison; this gate validates that the new contract artifact
  does not alter GLASS output pixels.

## Next Step

Return to Phase 2 mainline work: strengthen real-data DQ/mask and resident
registration/LN contracts where they affect 200-light correctness, then move
back to substantive resident CUDA performance and numerical parity gates.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-generated run artifacts and previously
generated GLASS baseline outputs only. It does not read external proprietary
source, modify input image directories, or copy external algorithms.
