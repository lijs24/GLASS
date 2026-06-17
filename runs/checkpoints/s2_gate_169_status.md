# S2-Gate 169 Status: Resident CUDA Result Contract Audit

## Gate

S2-Gate 169: Resident CUDA Result Contract Audit

## Completed

- Added `glass resident-result-contract`.
- Added `src/glass/report/resident_result_contract.py`.
- Added focused tests in `tests/test_resident_result_contract.py`.
- Added CLI help coverage for `resident-result-contract`.
- Added JSON-only and optional tiled FITS pixel-verification contract paths.
- Ran the JSON-only contract audit on the real Gate160 `throughput-v1` resident
  run.
- Updated Phase 2 and algorithm-source documentation.

## Contract Checks

Per resident output, the contract validates:

- resident identity
- required output map paths
- DQ summary presence
- resident DQ provenance summary schema
- DQ summary/provenance agreement
- active-frame count validity
- coverage provenance presence
- required source terms
- geometric warp coverage frame-count agreement
- optional DQ/count-map pixel verification

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_result_contract.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe resident-result-contract --run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --out C:\glass_runs\phase2_s2_gate_169_resident_result_contract\resident_result_contract.json --markdown C:\glass_runs\phase2_s2_gate_169_resident_result_contract\resident_result_contract.md --fail-on-failed
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_169_doctor.json
```

## Test Results

- Focused tests: `4 passed in 0.82s`.
- Full tests: `295 passed, 127 skipped in 16.21s`.
- CUDA test skip reason: GPU busy at `100%` utilization with approximately
  `61193/97887 MiB` used.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_169_doctor.json`.

## Artifacts

- Resident result-contract JSON:
  `C:\glass_runs\phase2_s2_gate_169_resident_result_contract\resident_result_contract.json`
- Resident result-contract Markdown:
  `C:\glass_runs\phase2_s2_gate_169_resident_result_contract\resident_result_contract.md`

## Real Artifact Summary

- Contract status: `passed`.
- Resident outputs: `1`.
- Output filter: `H`.
- Active frame count: `193`.
- Input frame count: `200`.
- Per-output checks: `9`.
- Pixel verification: disabled for the large Gate160 maps in this gate.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- The real Gate160 audit was JSON-only to avoid heavy disk reads while the GPU
  was externally loaded.
- The command supports pixel verification and tests cover it on tiny FITS maps,
  but large-map pixel verification should be scheduled intentionally.
- This gate creates a standalone resident contract artifact; pipeline-contract
  enforcement remains the next integration step.

## Next Step

Expose resident result-contract status in `glass pipeline-contract`, analogous
to the CPU StackEngine result-contract path added in S2-Gate168.

## Clean-Room Compliance

Compliant. This gate consumes GLASS resident integration JSON and optional GLASS
output FITS maps only. It does not read proprietary source code, alter CUDA
kernels, rerun image processing, modify input data, or change defaults.
