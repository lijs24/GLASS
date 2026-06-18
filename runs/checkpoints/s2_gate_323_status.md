# S2-Gate 323 Status - Acceptance Audit Warp Quality Handoff

## Gate

S2-Gate 323: Acceptance-audit warp quality handoff.

## Completed

- Added `warp_quality_contract.json` handoff to `glass acceptance-audit`.
- The acceptance audit now resolves a warp-quality contract from:
  - `acceptance_contract_bundle.json` artifact map
  - `acceptance_audit_argument_map`
  - explicit `--warp-quality-contract-json`
- Added `--require-warp-quality-contract` so release or benchmark scripts can fail when warp quality evidence is missing, malformed, or failed.
- Preserved default compatibility: acceptance audits without warp evidence remain valid unless the new requirement is supplied or a contract path is attached.
- Surfaced warp-quality status, type, check count, output count, failed checks, and path in acceptance JSON and Markdown.
- Added focused tests for:
  - bundle handoff with required warp evidence
  - required-missing warp contract failure
  - failed supplied warp contract failure
  - CLI required-mode bundle handoff
- Documented S2-Gate 323 in `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\report\acceptance_audit.py src\glass\cli.py tests\test_acceptance_audit.py docs\phase2_algorithm_hardening.md

.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py -k "warp_quality_contract or cli_accepts_contract_bundle"

.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py

.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest runs\checkpoints\s2_gate_294_fixtures\acceptance\manifest.json --glass-run runs\checkpoints\s2_gate_294_fixtures\acceptance\gp --wbpp-result runs\checkpoints\s2_gate_294_fixtures\acceptance\wbpp.json --compare-json runs\checkpoints\s2_gate_294_fixtures\acceptance\compare.json --contract-bundle runs\checkpoints\s2_gate_321_guardrails\acceptance_contract_bundle.json --require-warp-quality-contract --out runs\checkpoints\s2_gate_323_acceptance_audit.json --markdown runs\checkpoints\s2_gate_323_acceptance_audit.md --min-active-frames 190

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_323_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 4 passed, 38 deselected.
- Acceptance audit pytest file: 42 passed.
- Full pytest: 754 passed in 33.33 s.
- Gate323 acceptance audit artifact: passed.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor recommendation: cuda.

## Artifacts

- `runs/checkpoints/s2_gate_323_acceptance_audit.json`
- `runs/checkpoints/s2_gate_323_acceptance_audit.md`
- `runs/checkpoints/s2_gate_323_doctor.json`

## Acceptance Handoff Result

- Acceptance status: passed.
- Warp quality contract status: passed.
- Warp quality contract output count: 1.
- `warp_quality_contract_present`: passed.
- `warp_quality_contract_type`: passed.
- `warp_quality_contract_passed`: passed.
- Warp contract source: `runs/checkpoints/s2_gate_321_guardrails/warp_quality_contract.json`.
- Contract bundle source: `runs/checkpoints/s2_gate_321_guardrails/acceptance_contract_bundle.json`.

## Known Limitations

- This gate only moves existing warp-quality evidence into the higher-level acceptance audit; it does not add new warp math.
- The checkpoint artifact reuses the small S2-Gate 294 acceptance fixture and S2-Gate 321 guardrails bundle; it is not a new 200-light real-data benchmark.
- The reused warp contract has one accepted output and two skipped rows, so it proves handoff plumbing and strict required-mode behavior rather than broad real-data warp distribution quality.
- This gate does not change CUDA kernels, runtime defaults, package builds, release artifacts, or real-data benchmark outputs.

## Next Step

- Add higher-level release/promotion consumption of the acceptance warp-quality evidence, or continue algorithm hardening with multi-frame warp residual fixtures.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated artifacts and user-owned checkpoint fixtures.
- Input image directories were not modified.
