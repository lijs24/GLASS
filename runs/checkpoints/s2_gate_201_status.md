# S2-Gate 201 Status: Resident Bundle Contract Enforcement

## Gate

- Gate: S2-Gate 201
- Scope: enforce resident CUDA calibration/result contracts carried by guardrails acceptance bundles.
- Status: green
- Date: 2026-06-18

## Completed

- Extended `glass acceptance-audit --contract-bundle` so bundle-declared resident CUDA contracts are audited, not only recorded.
- Added blocking checks for:
  - `resident_calibration_contract_present`
  - `resident_calibration_contract_type`
  - `resident_calibration_contract_passed`
  - `resident_result_contract_present`
  - `resident_result_contract_type`
  - `resident_result_contract_passed`
- Added `resident_contracts.calibration` and `resident_contracts.result` summaries to acceptance-audit JSON.
- Added `Resident Bundle Contracts` to acceptance-audit Markdown output.
- Documented S2-Gate 201 in `docs/phase2_algorithm_hardening.md`.
- Reran the real Gate200 200-light acceptance bundle as a read-only artifact audit.

## Commands

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\acceptance_audit.py tests\test_acceptance_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --contract-bundle runs\checkpoints\s2_gate_200_acceptance_contract_bundle.json --out runs\checkpoints\s2_gate_201_acceptance_real_bundle.json --markdown runs\checkpoints\s2_gate_201_acceptance_real_bundle.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only
```

## Test Results

- Focused ruff: passed.
- Focused acceptance-audit tests: `28 passed in 0.86s`.
- Full ruff: passed.
- Full pytest: `480 passed in 25.87s`.
- Real 200-light acceptance bundle: passed.

## Real 200-Light Artifact Audit

- Output JSON: `runs/checkpoints/s2_gate_201_acceptance_real_bundle.json`
- Output Markdown: `runs/checkpoints/s2_gate_201_acceptance_real_bundle.md`
- Acceptance status: `passed`
- Speedup vs WBPP black-box timing: `58.099101701945926x`
- Frame counts: `light=200`, `bias=20`, `dark=20`, `flat=20`
- Active frames: `193`
- Coverage fraction: `0.9577924192878646`
- Resident calibration contract: `resident_cuda_calibration_contract`, passed.
- Resident result contract: `resident_cuda_result_contract`, passed.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Known Limitations

- This gate hardens acceptance evidence only; it does not change resident CUDA image math or runtime scheduling.
- Resident contract attachment checks are enforced when a bundle declares those contracts. Older bundles without resident contract attachments remain backward-compatible.
- No new PixInsight/WBPP processing was launched in this gate; the external timing/result artifact was read as an existing user-generated black-box record.

## Clean-Room

- Compliant.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- Input image directories were not modified.

## Next Step

- S2-Gate 202 should add an acceptance-bundle schema/version audit so future guardrails bundles can reject missing required fields before real benchmark publication.
