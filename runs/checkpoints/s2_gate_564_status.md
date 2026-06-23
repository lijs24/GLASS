# S2-Gate 564 Status: Resident Registration Default Promotion

## Gate

S2-Gate 564 promotes resident CUDA registration from an implicit unregistered
default to an explicit `auto` default that resolves to
`similarity_cuda_triangle` for full resident CUDA integration.

## Completed

- Added `DEFAULT_RESIDENT_REGISTRATION=auto`.
- Added `DEFAULT_RESIDENT_REGISTRATION_EFFECTIVE=similarity_cuda_triangle`.
- Added `_resolve_resident_registration_default`.
- `glass run` and `glass audit` now resolve resident registration defaults
  before command capture and execution.
- Full resident CUDA integration resolves unspecified registration to
  `similarity_cuda_triangle`.
- Explicit `--resident-registration off` remains the unregistered escape hatch.
- Non-resident/tile execution resolves resident registration `auto` to `off`.
- `run_timing.json` now records `resident_registration_resolution`.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_run_defaults_promote_resident_cuda_when_available tests\test_cli_smoke.py::test_run_resident_registration_defaults_to_similarity_triangle tests\test_cli_smoke.py::test_run_resident_registration_explicit_off_is_preserved tests\test_cli_smoke.py::test_run_resident_registration_auto_keeps_tile_path_off tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate564_default_resident_registration\runs_20260623_182723\default_registration --local-normalization on --resident-local-normalization-mode grid_mean_std --resident-local-normalization-tile-size 256 --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused default-resolution and resident smoke tests: `6 passed in 0.75 s`.
- Full pytest: `1207 passed in 45.26 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate564_default_resident_registration\runs_20260623_182723\default_registration`
- Summary:
  `runs/checkpoints/s2_gate_564_default_resident_registration_summary.json`
- Shell elapsed: `7.2844874 s`.
- Run timing total: `6.929089199984446 s`.
- The run intentionally omitted `--backend`, `--memory-mode`, `--until-stage`,
  and `--resident-registration`.
- Execution default resolution: backend `auto -> cuda`, memory mode
  `resident -> resident`.
- Resident registration resolution: `auto -> similarity_cuda_triangle`.
- Pipeline contract: passed.
- Registration-quality decisions: `200`.
- Decision statuses: `192 accepted / 1 reference / 7 rejected`.
- Active/rejected frames: `193 / 7`.
- Output master, weight map, coverage map, low/high rejection maps, and DQ map
  have SHA256 hashes identical to S2-Gate 563.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `runs/checkpoints/s2_gate_564_real_run_path.json`
- `runs/checkpoints/s2_gate_564_default_resident_registration_summary.json`
- Real run `run_timing.json` with `resident_registration_resolution`.
- Real run `resident_registration_quality.json`.
- Real run `pipeline_contract.json`.
- Real run integration master/maps under `integration/`.

## Known Limitations

- This gate changes only the default registration dispatch. It does not promote
  star threshold, reference-frame selection, LN tile size, warp interpolation,
  or output-map policy defaults.
- Explicit `--resident-registration off` still allows an unregistered resident
  run for diagnostics.

## Next Step

Continue the default-path mainline by promoting the remaining real-run science
defaults one at a time: first reference/registration parameter defaults, then
LN defaults, then a zero-manual-registration 200-light A/B run against the
Phase 1/WBPP comparison baseline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned default policy, tests, and user-owned
200-light GLASS artifacts only. It does not inspect external proprietary source
code, copy external algorithms, or modify input image directories.
