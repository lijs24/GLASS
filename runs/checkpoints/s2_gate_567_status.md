# S2-Gate 567 Status: Resident Warp Interpolation Default Promotion

## Gate

S2-Gate 567 promotes the full resident CUDA matrix-warp default from a parser-level
`bilinear` choice to an explicit `auto -> lanczos3` default policy for validated
matrix registration routes.

## Completed

- Added `DEFAULT_RESIDENT_WARP_INTERPOLATION=auto`.
- Added `DEFAULT_RESIDENT_WARP_INTERPOLATION_EFFECTIVE=lanczos3`.
- Added `DEFAULT_RESIDENT_WARP_INTERPOLATION_FALLBACK=bilinear`.
- Added `_resolve_resident_warp_interpolation_default`.
- `glass run` and `glass audit` now resolve resident warp interpolation before
  command capture, memory admission, timing annotation, and resident execution.
- Full resident CUDA integration with matrix registration resolves unspecified
  warp interpolation to `lanczos3`.
- Explicit `--resident-warp-interpolation bilinear` remains the speed and
  compatibility escape hatch.
- Non-matrix and non-resident routes resolve `auto` to `bilinear` before lower
  resident code is called.
- `run_timing.json` records `resident_warp_interpolation_resolution`.
- Updated resident CUDA tests that exercised the default similarity-triangle path
  to expect the new `native_matrix_lanczos3_frames` route.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py -k "resident_warp_interpolation or resident_registration_defaults or resident_local_normalization_defaults or resident_rejection_defaults"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate567_default_resident_warp\runs_20260623_184311\default_warp --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused default-resolution tests: `7 passed, 43 deselected in 0.36 s`.
- CLI smoke suite: `50 passed in 6.09 s`.
- Resident CUDA smoke: `1 passed in 0.67 s`.
- Resident triangle default-path focused test after expectation update:
  `1 passed in 0.82 s`.
- Full pytest: `1218 passed in 45.45 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate567_default_resident_warp\runs_20260623_184311\default_warp`
- Summary:
  `runs/checkpoints/s2_gate_567_default_resident_warp_summary.json`
- Shell elapsed: `7.348884699999999 s`.
- Run timing total: `6.99615249998169 s`.
- Gate566 baseline run timing total: `6.939177799969912 s`.
- WBPP black-box elapsed reference: `1092.541 s`.
- Speedup versus WBPP reference: `156.16311965796334x`.
- The run intentionally omitted `--backend`, `--memory-mode`, `--until-stage`,
  `--resident-registration`, `--integration-rejection`, `--local-normalization`,
  `--resident-local-normalization-mode`, `--resident-local-normalization-tile-size`,
  and `--resident-warp-interpolation`.
- Execution default resolution: backend `auto -> cuda`, memory mode
  `resident -> resident`.
- Resident registration resolution: `auto -> similarity_cuda_triangle`.
- Resident integration rejection resolution: `auto -> winsorized_sigma`.
- Resident local-normalization resolution: `auto -> on`, mode `grid_mean_std`,
  tile size `256`.
- Resident warp interpolation resolution: `auto -> lanczos3`.
- Resident artifact warp interpolation: `lanczos3`.
- Local-normalization contract: passed.
- Pipeline contract: passed.
- Active/rejected frames: `193 / 7`.
- Output master, weight map, coverage map, low/high rejection maps, and DQ map
  have SHA256 hashes identical to S2-Gate 566.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `runs/checkpoints/s2_gate_567_real_run_path.json`
- `runs/checkpoints/s2_gate_567_default_resident_warp_summary.json`
- Real run `run_timing.json` with `resident_warp_interpolation_resolution`.
- Real run `resident_artifacts.json` with `warp_interpolation=lanczos3`.
- Real run `local_norm_contract.json`.
- Real run `pipeline_contract.json`.
- Real run `resident_registration_quality.json`.
- Real run integration master/maps under `integration/`.

## Known Limitations

- This gate changes only resident CUDA default warp interpolation dispatch. It
  does not change the Lanczos3 kernel, registration transform estimator, or
  output-map policy.
- Explicit bilinear runs remain available with
  `--resident-warp-interpolation bilinear` for speed/compatibility diagnostics.
- Reference-frame selection, star thresholds, flat floor, and output-map policy
  still remain explicit science parameters in the 200-light command and should
  be reduced only after matching validation gates.

## Next Step

Continue default-path hardening on the remaining real-run science parameters:
reference-frame policy, star threshold/candidate policy, flat-floor handling, and
output-map profile. Each promotion should preserve 200-light contract health and
record any speed/numeric effect against the current Gate567 baseline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned default policy, tests, and user-owned
200-light GLASS artifacts only. It does not inspect external proprietary source
code, copy external algorithms, or modify input image directories.
