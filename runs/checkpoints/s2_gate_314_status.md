# S2-Gate 314 Status: Local Normalization Contract Guardrail Handoff

## Gate

S2-Gate 314

## Completed

- Added optional `local_norm_contract` attachment support to the pipeline
  invariant contract.
- Added the pipeline check
  `local_normalization_continuous_contract_audit` when an LN contract is
  attached.
- Extended `glass pipeline-contract` with `--local-norm-contract-json`.
- Extended `glass guardrails` to auto-generate `local_norm_contract.json` and
  `local_norm_contract.md` when `local_norm_results.json` exists in a run.
- Propagated LN contract status and artifact paths into
  `guardrails_summary.json` and `acceptance_contract_bundle.json`.
- Preserved integration-only/minimal run compatibility by marking the LN
  contract not required when no `local_norm_results.json` exists.
- Updated Phase 2 and Local Normalization documentation.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\report\pipeline_contract.py src\glass\cli.py tests\test_pipeline_contract.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py::test_pipeline_contract_passes_for_cpu_audit_run tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_guardrails_auto_discovers_run_resident_result_contract
.venv\Scripts\ruff.exe check src\glass\report\pipeline_contract.py src\glass\cli.py tests\test_pipeline_contract.py tests\test_cli_smoke.py docs\phase2_algorithm_hardening.md docs\local_normalization_model.md
.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py tests\test_pipeline_contract.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m glass.cli synthetic --out runs\checkpoints\s2_gate_314_synthetic_data --frames 3 --width 24 --height 24 --filter H --known-shift
.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_314_synthetic_data --out runs\checkpoints\s2_gate_314_cpu_run --backend cpu --tile-size 8
.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_314_cpu_run --out-dir runs\checkpoints\s2_gate_314_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 8
.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_314_doctor.json
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff checks: passed.
- Focused LN/pipeline/guardrails tests: `49 passed`.
- Full test suite: `739 passed in 35.43s`.

## Checkpoint Artifacts

- `runs/checkpoints/s2_gate_314_status.md`
- `runs/checkpoints/s2_gate_314_doctor.json`
- `runs/checkpoints/s2_gate_314_synthetic_data/`
- `runs/checkpoints/s2_gate_314_cpu_run/`
- `runs/checkpoints/s2_gate_314_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_314_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_314_guardrails/local_norm_contract.json`
- `runs/checkpoints/s2_gate_314_guardrails/local_norm_contract.md`
- `runs/checkpoints/s2_gate_314_guardrails/pipeline_contract.json`
- `runs/checkpoints/s2_gate_314_guardrails/pipeline_contract.md`
- `runs/checkpoints/s2_gate_314_guardrails/stack_engine_contract.json`
- `runs/checkpoints/s2_gate_314_guardrails/stack_engine_contract.md`
- `runs/checkpoints/s2_gate_314_guardrails/report.html`

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- This gate does not change local-normalization math or CUDA kernels.
- The checkpoint validation run is intentionally tiny and CPU-only; no
  200-light real-data benchmark was rerun for this metadata/guardrail handoff.
- The checkpoint run uses disabled local normalization passthrough output,
  which validates the handoff and disabled-contract path. Enabled continuous
  coefficient-field artifacts remain covered by the focused tests from
  S2-Gate 313 and the updated pipeline-contract explicit attachment test.

## Next Step

- Continue with the next Phase 2 gate by promoting additional algorithm
  contracts into guardrails or by strengthening the enabled continuous local
  normalization runtime path, depending on the next selected risk area.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No PixInsight installation directory was touched.
- This gate only consumes GLASS-generated run artifacts and metadata.
- Input image directories were treated as read-only.
