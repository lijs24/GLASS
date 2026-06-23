# S2-Gate 569 Status: Resident Reference Admission Guard

## Gate

S2-Gate 569 prevents the default resident CUDA matrix-registration science path
from silently using first-light fallback when no explicit, external, or quality
reference is available.

## Completed

- Added `resident_reference_admission.json` before resident memory admission.
- Added `--resident-reference-fallback` with policies:
  - `auto`
  - `allow-first-light`
  - `block-first-light`
- `auto` blocks first-light fallback when resident matrix registration was
  default-promoted or explicitly requested as `auto` and no reference evidence is
  available.
- Explicit concrete resident registration modes still allow first-light fallback
  for diagnostic compatibility.
- `allow-first-light` is the explicit diagnostic escape hatch.
- Reference-admission failures write:
  - `resident_reference_admission.json`
  - `run_state.json`
  - `run_timing.json`
- Successful resident runs attach the reference-admission artifact to
  `run_state.json`.
- Existing memory-admission and source-DQ tests were updated to account for the
  new pre-memory reference-admission stage.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py -k "resident_matrix_registration or first_light_reference_fallback or low_vram_budget"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate569_reference_admission\runs_20260623_190017\blocked_no_reference --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate569_reference_admission\runs_20260623_190027\explicit_reference --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused reference-admission tests: `6 passed, 49 deselected in 0.54 s`.
- CLI smoke suite: `54 passed in 5.42 s`.
- Resident CUDA reference/triangle smoke tests: `3 passed in 1.11 s`.
- Source-DQ cache route stage-order regression: `1 passed in 0.89 s`.
- Full pytest: `1223 passed in 45.64 s`.

## Real 200-Light Validation

### Blocked no-reference run

- Run root:
  `C:\glass_runs\phase2_s2_gate569_reference_admission\runs_20260623_190017\blocked_no_reference`
- Exit code: `2`.
- Shell elapsed: `0.3309163 s`.
- Failed stage: `resident_reference_admission`.
- Block reason: `default_matrix_registration_without_reference`.
- No resident memory admission or resident CUDA compute was started.

### Explicit-reference run

- Run root:
  `C:\glass_runs\phase2_s2_gate569_reference_admission\runs_20260623_190027\explicit_reference`
- Summary:
  `runs/checkpoints/s2_gate_569_reference_admission_summary.json`
- Shell elapsed: `7.2193194 s`.
- Run timing total: `6.866450699919369 s`.
- WBPP black-box elapsed reference: `1092.541 s`.
- Speedup versus WBPP reference: `159.11291695618368x`.
- Reference admission: passed, non-blocking.
- Local-normalization contract: passed.
- Pipeline contract: passed.
- Active/rejected frames: `193 / 7`.
- Output master, weight map, coverage map, low/high rejection maps, and DQ map
  have SHA256 hashes identical to S2-Gate 567.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `runs/checkpoints/s2_gate_569_blocked_no_reference_run_path.json`
- `runs/checkpoints/s2_gate_569_explicit_reference_run_path.json`
- `runs/checkpoints/s2_gate_569_reference_admission_summary.json`
- Blocked run `resident_reference_admission.json`.
- Blocked run `run_state.json`.
- Explicit-reference run `resident_reference_admission.json`.
- Explicit-reference run `pipeline_contract.json`.
- Explicit-reference run `local_norm_contract.json`.
- Explicit-reference run integration master/maps under `integration/`.

## Known Limitations

- This gate blocks unsafe fallback; it does not yet implement automatic in-VRAM
  quality-reference selection.
- Default resident CUDA matrix registration still requires an explicit reference,
  an external registration reference, or a pre-existing `frame_quality.json`.
- `--resident-reference-fallback allow-first-light` remains available for
  diagnostic runs and should not be treated as a science default.

## Next Step

Implement an automatic resident quality-reference path that does not require a
CPU calibrated cache or a second full disk pass. A practical next gate is to
select a reference from resident GPU star catalog/registration-quality evidence
before matrix registration, then validate against the Gate567 explicit-reference
baseline on the 200-light dataset.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned admission policy, tests, and user-owned
200-light GLASS artifacts only. It does not inspect external proprietary source
code, copy external algorithms, or modify input image directories.
