# S2-Gate 347 Status - Frame Accounting Integration-Conflict Guard

- Status: green
- Timestamp: 2026-06-19 03:38:37 +08:00
- Scope: harden the per-light frame accounting ledger so a frame with positive integration weight cannot be reported as integrated when quality, registration, warp, or local-normalization artifacts already rejected, skipped, or missed it.

## Completed

- Added `integration_conflict` as an explicit final status in `src/glass/engine/frame_accounting.py`.
- Added per-frame `integration_conflict_count` and `integration_conflicts` rows with stage/reason detail.
- Added summary field `integration_conflict_frames`.
- Updated exception attribution so integration conflicts point back to the first conflicting upstream stage.
- Updated benchmark contract evidence to collect integration conflicts from `frame_accounting.json`.
- Added default `contract_frame_accounting_no_integration_conflicts` when frame accounting is required by an acceptance benchmark contract.
- Surfaced `integration_conflict_frames` and `integration_conflict_count` in HTML report tables.
- Added focused unit coverage for the ledger conflict path and acceptance-audit failure path.
- Documented the guard in the Phase 2 hardening plan and algorithm-source ledger.
- Generated a controlled conflict artifact whose acceptance audit fails only on `contract_frame_accounting_no_integration_conflicts`.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\engine\frame_accounting.py src\glass\report\benchmark_contract.py src\glass\report\html_report.py tests\test_frame_accounting.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py tests\test_acceptance_audit.py`
- Inline artifact-generation script writing `runs/checkpoints/s2_gate_347_*` controlled-conflict outputs.
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_347_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused ruff: passed.
- Focused pytest: `47 passed in 1.37s`.
- Full pytest: `793 passed in 32.50s`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_347_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_347_controlled_conflict_run/frame_accounting.json`
- `runs/checkpoints/s2_gate_347_frame_accounting_conflict.json`
- `runs/checkpoints/s2_gate_347_acceptance_audit_conflict.json`
- `runs/checkpoints/s2_gate_347_acceptance_audit_conflict.md`
- `runs/checkpoints/s2_gate_347_report_conflict.html`
- `runs/checkpoints/s2_gate_347_cuda_doctor.json`

## Known Limits

- This gate does not change registration, warp, LN, or integration math.
- The controlled conflict artifact is intentionally invalid and is expected to fail the no-conflict acceptance check.
- Real 200-light data was not rerun for this gate; this is a contract and accounting hardening gate.

## Next Step

- Continue Phase 2 by extending pipeline-contract coverage from ledger-level frame admission into runtime stage artifacts, especially resident registration/warp/LN admission consistency.

## Clean-Room Compliance

- Compliant. This gate used GLASS-owned code, synthetic/controlled JSON artifacts, and local test fixtures only.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
