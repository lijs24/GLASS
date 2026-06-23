# S2-Gate 566 Status: Resident Local-Normalization Default Promotion

## Gate

S2-Gate 566 promotes resident CUDA local normalization from a plan-dependent
`auto` default to a resident science default: `auto -> on`, mode
`grid_mean_std`, tile size `256` for full resident CUDA integration.

## Completed

- Added `DEFAULT_RESIDENT_LOCAL_NORMALIZATION=auto`.
- Added `DEFAULT_RESIDENT_LOCAL_NORMALIZATION_EFFECTIVE=on`.
- Added `DEFAULT_RESIDENT_LOCAL_NORMALIZATION_MODE_EFFECTIVE=grid_mean_std`.
- Added `DEFAULT_RESIDENT_LOCAL_NORMALIZATION_TILE_SIZE_EFFECTIVE=256`.
- Added `_resolve_resident_local_normalization_default`.
- `glass run` and `glass audit` now resolve resident LN defaults before command
  capture, memory admission, and execution.
- Full resident CUDA integration resolves unspecified LN to
  `on / grid_mean_std / 256`.
- Explicit `--local-normalization off` remains the disabled-LN diagnostic
  escape hatch.
- Explicit `--resident-local-normalization-mode` and
  `--resident-local-normalization-tile-size` are preserved.
- Non-resident/tile execution keeps `local_normalization=auto`.
- `run_timing.json` now records `resident_local_normalization_resolution`.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_run_resident_local_normalization_defaults_to_grid_on tests\test_cli_smoke.py::test_run_resident_local_normalization_explicit_off_is_preserved tests\test_cli_smoke.py::test_run_resident_local_normalization_explicit_mode_and_tile_are_preserved tests\test_cli_smoke.py::test_run_resident_local_normalization_auto_keeps_tile_path_auto tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate566_default_resident_ln\runs_20260623_183648\default_ln --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused LN default-resolution and resident smoke tests: `6 passed in 0.77 s`.
- Full pytest: `1214 passed in 45.02 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate566_default_resident_ln\runs_20260623_183648\default_ln`
- Summary:
  `runs/checkpoints/s2_gate_566_default_resident_ln_summary.json`
- Shell elapsed: `7.2923174 s`.
- Run timing total: `6.939177799969912 s`.
- The run intentionally omitted `--backend`, `--memory-mode`, `--until-stage`,
  `--resident-registration`, `--integration-rejection`,
  `--local-normalization`, `--resident-local-normalization-mode`, and
  `--resident-local-normalization-tile-size`.
- Execution default resolution: backend `auto -> cuda`, memory mode
  `resident -> resident`.
- Resident registration resolution: `auto -> similarity_cuda_triangle`.
- Resident integration rejection resolution: `auto -> winsorized_sigma`.
- Resident local-normalization resolution:
  `auto -> on`, mode `grid_mean_std`, tile size `256`.
- Local-normalization contract: passed.
- Pipeline contract: passed.
- LN status counts:
  `109 ok / 83 partial / 1 reference / 7 skipped_zero_weight`.
- Registration-quality decisions: `200`.
- Active/rejected frames: `193 / 7`.
- Output master, weight map, coverage map, low/high rejection maps, and DQ map
  have SHA256 hashes identical to S2-Gate 565.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `runs/checkpoints/s2_gate_566_real_run_path.json`
- `runs/checkpoints/s2_gate_566_default_resident_ln_summary.json`
- Real run `run_timing.json` with `resident_local_normalization_resolution`.
- Real run `local_norm_results.json`.
- Real run `local_norm_contract.json`.
- Real run `resident_registration_quality.json`.
- Real run `pipeline_contract.json`.
- Real run integration master/maps under `integration/`.

## Known Limitations

- This gate changes only resident CUDA default LN dispatch. It does not alter
  the local-normalization coefficient formula, grid kernel, or contract rules.
- Explicit disabled-LN resident diagnostic runs remain available with
  `--local-normalization off`.
- Reference-frame selection, star thresholds, flat floor, warp interpolation,
  and output-map policy still require explicit real-run science defaults in
  later gates.

## Next Step

Continue reducing real-run manual science parameters: promote the validated
reference/registration parameter defaults, then run a lower-argument 200-light
A/B against the Phase 1/WBPP comparison baseline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned default policy, tests, and user-owned
200-light GLASS artifacts only. It does not inspect external proprietary source
code, copy external algorithms, or modify input image directories.
