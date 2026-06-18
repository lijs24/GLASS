# S2-Gate 327 Status: Acceptance Resident Registration Fastpath Evidence

## Gate

- Gate: S2-Gate 327
- Name: Acceptance Resident Registration Fastpath Evidence
- Status: green
- Date: 2026-06-18

## Completed Content

- Added resident registration fast-path evidence to the acceptance audit release contract block.
- The audit now records explicit evidence for descriptor batch mode, pixel refine batch mode, triangle warp batch mode, warp copy mode, scratch allocation, and per-check pass/fail details.
- Added Markdown rendering for the resident registration fast-path evidence section.
- Extended acceptance audit regression tests for explicit evidence, inferred evidence, and failed fast-path contracts.
- Added a checkpoint fixture proving a passing resident fast-path contract can be combined with the default-ready release decision.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\report\acceptance_audit.py tests\test_acceptance_audit.py docs\phase2_algorithm_hardening.md
.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py -k "resident_registration_fastpath"
.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py
.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest runs\checkpoints\s2_gate_294_fixtures\acceptance\manifest.json --glass-run runs\checkpoints\s2_gate_294_fixtures\acceptance\gp --wbpp-result runs\checkpoints\s2_gate_294_fixtures\acceptance\wbpp.json --compare-json runs\checkpoints\s2_gate_294_fixtures\acceptance\compare.json --contract-bundle runs\checkpoints\s2_gate_321_guardrails\acceptance_contract_bundle.json --require-warp-quality-contract --benchmark-contract runs\checkpoints\s2_gate_327_fastpath_fixture\benchmark_contract.json --resident-registration-fastpath-json runs\checkpoints\s2_gate_327_fastpath_fixture\resident_artifacts.json --out runs\checkpoints\s2_gate_327_acceptance_audit.json --markdown runs\checkpoints\s2_gate_327_acceptance_audit.md --min-active-frames 190
.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints\s2_gate_327_phase2_checkpoint_fixture --acceptance-audit runs\checkpoints\s2_gate_327_acceptance_audit.json --release-decision runs\checkpoints\s2_gate_326_release_promotion_decision.json --out runs\checkpoints\s2_gate_327_phase2_status.json --markdown runs\checkpoints\s2_gate_327_phase2_status.md
.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_327_doctor.json
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed
- Resident fast-path acceptance tests: 3 passed, 39 deselected
- Acceptance audit tests: 42 passed
- Full pytest: 759 passed in 31.75s
- Acceptance audit: passed
- Phase2 status: green

## CUDA Status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/checkpoints/s2_gate_327_fastpath_fixture/resident_artifacts.json`
- `runs/checkpoints/s2_gate_327_fastpath_fixture/benchmark_contract.json`
- `runs/checkpoints/s2_gate_327_acceptance_audit.json`
- `runs/checkpoints/s2_gate_327_acceptance_audit.md`
- `runs/checkpoints/s2_gate_327_phase2_checkpoint_fixture/s2_gate_327_status.md`
- `runs/checkpoints/s2_gate_327_phase2_status.json`
- `runs/checkpoints/s2_gate_327_phase2_status.md`
- `runs/checkpoints/s2_gate_327_doctor.json`

## Evidence Summary

- Resident fast-path evidence status: passed
- Required by benchmark contract: yes
- Evidence source: explicit artifact
- Passed checks: 23
- Failed checks: 0
- Triangle warp batch frame count: 3
- Release decision runtime repeat evidence ready: true
- Resident registration fast-path contract passed for default: true

## Known Limitations

- This gate validates acceptance and release-decision evidence wiring; it does not rerun the full 200-light real-data benchmark.
- The fixture uses controlled resident fast-path evidence rather than a fresh heavy benchmark artifact.
- PixInsight/WBPP remains a black-box comparison source only; no official source code was read or used.

## Next Step

- Use the now-combined acceptance audit and default-ready release decision as the release preflight handoff, or rerun the real 200-light benchmark to refresh public timing and result-consistency evidence.

## Clean-Room Compliance

- Compliant. This gate used GLASS-generated fixtures, benchmark contracts, and black-box comparison artifacts only.
- No PixInsight installation directory, WBPP/PJSR source file, or official implementation detail was read, copied, summarized, or modified.
