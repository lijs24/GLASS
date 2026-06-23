# S2-Gate 560 Status: Resident Local Normalization Contract

## Gate

S2-Gate 560: make resident CUDA local-normalization evidence a first-class
run contract and default resident `glass run` artifact.

## Completed

- Extended `glass.report.local_norm_contract` with
  `contract_surface=resident_in_vram`.
- Added resident LN checks for:
  - top-level resident source stage, enabled state, mode, groups, and crop box;
  - per-frame `reference`, `ok`, `partial`, `empty`, and
    `skipped_zero_weight` states;
  - finite per-frame scale and offset values;
  - resident grid coefficient shape, tile size, valid-pixel totals, empty-tile
    counts, ok-tile counts, and status grids.
- Made resident `glass run` write `local_norm_contract.json` and
  `local_norm_contract.md` whenever `local_norm_results.json` exists.
- Passed the generated LN contract into default `pipeline_contract.json`.
- Added focused resident in-VRAM LN contract fixtures and resident CUDA smoke
  assertions.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\report\local_norm_contract.py src\glass\cli.py tests\test_local_norm_contract.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_local_norm_contract.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\python.exe -m pytest -q tests/test_local_norm_contract.py tests/test_pipeline_contract.py tests/test_resident_result_contract.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization on --resident-local-normalization-mode grid_mean_std --resident-local-normalization-tile-size 256 --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --out C:\glass_runs\phase2_s2_gate560_resident_ln_contract\runs_20260623_175507\ln_on_contract`

## Test Results

- Focused LN/resident tests:
  `11 passed in 1.43 s`.
- Pipeline/resident contract suite:
  `63 passed in 2.55 s`.
- Full pytest:
  `1197 passed in 45.00 s`.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate560_resident_ln_contract\runs_20260623_175507\ln_on_contract`.
- LN-off reference run:
  `C:\glass_runs\phase2_s2_gate559_pipeline_contract_default\runs_20260623_174914\default_contract`.
- Shell elapsed: `7.1932722 s`.
- Run timing total: `6.8284103000187315 s`.
- Resident calibration/integration/LN stage: `6.5044172999914736 s`.
- Local norm contract stage: `0.17231280001578853 s`.
- Pipeline contract stage: `0.1486287000006996 s`.
- LN mode: `resident_grid_mean_std`.
- LN contract status: `passed`.
- Pipeline contract status: `passed`.
- LN output rows: `200`.
- LN status counts: `109 ok`, `83 partial`, `1 reference`,
  `7 skipped_zero_weight`.
- Frame accounting: `200` input light frames, `193` integrated frames,
  `7` zero-weight frames.

## CUDA

- CUDA extension importable: yes.
- CUDA available: yes.
- Resident CUDA features used: resident stack, Lanczos3 warp, grid local
  normalization, winsorized sigma rejection, audit output maps.

## Known Limitations

- This gate does not change LN math or CUDA kernels; it promotes resident LN
  evidence into default contracts.
- LN-on output is expected to differ from LN-off output. The checkpoint summary
  records LN-on vs LN-off master-difference statistics for audit context.
- WBPP/LN parity remains a future algorithm-comparison task; this gate proves
  resident LN contract completeness and real 200-light execution.

## Next Step

Continue Phase 2 mainline by strengthening registration/LN numerical
validation against known synthetic transforms and the real 200-light benchmark,
then use those contracts to guide substantive resident CUDA performance work.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-generated resident LN artifacts and the
user-provided 200-light data through GLASS only. It does not read external
proprietary source, modify input directories, or copy external algorithms.
