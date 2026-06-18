# S2-Gate 328 Status: Release Decision Resident Fastpath Handoff

## Gate

- Gate: S2-Gate 328
- Name: Release Decision Resident Fastpath Handoff
- Status: green
- Date: 2026-06-18

## Completed Content

- Added `resident_registration_fastpath_handoff` to `glass release-promotion-decision`.
- The release decision now carries resident fastpath source, path, required state, availability, existence, registration mode, descriptor/pixel/warp batch modes, triangle warp batch frame count, warp copy mode, check counts, and failed checks.
- Added a release-blocking `resident_registration_fastpath_handoff` check when acceptance evidence or fastpath contract checks indicate that resident fastpath behavior was benchmark-required.
- Preserved compatibility for older acceptance artifacts: missing resident fastpath evidence is recorded as `not_available` and does not block release-candidate readiness.
- Added Markdown output for the resident fastpath handoff section.
- Added focused tests for passing handoff, failed required handoff, and CLI Markdown visibility.
- Documented S2-Gate 328 in the Phase 2 plan and algorithm-source ledger.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py
.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py -k "resident_fastpath or warp_quality or cli"
.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_327_acceptance_audit.json --runtime-compare runs\checkpoints\s2_gate_326_runtime_compare.json --min-runtime-runs 3 --out runs\checkpoints\s2_gate_328_release_promotion_decision.json --markdown runs\checkpoints\s2_gate_328_release_promotion_decision.md
.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py docs\phase2_algorithm_hardening.md docs\algorithm_sources.md
.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py
.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints\s2_gate_328_phase2_checkpoint_fixture --acceptance-audit runs\checkpoints\s2_gate_327_acceptance_audit.json --release-decision runs\checkpoints\s2_gate_328_release_promotion_decision.json --out runs\checkpoints\s2_gate_328_phase2_status.json --markdown runs\checkpoints\s2_gate_328_phase2_status.md
.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_328_doctor.json
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed
- Focused release-promotion subset: 5 passed, 16 deselected
- Release-promotion test file: 21 passed
- Full pytest: 761 passed in 32.09s
- Release decision artifact: `default_change_ready`
- Phase2 status artifact: green

## CUDA Status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/checkpoints/s2_gate_328_release_promotion_decision.json`
- `runs/checkpoints/s2_gate_328_release_promotion_decision.md`
- `runs/checkpoints/s2_gate_328_phase2_checkpoint_fixture/s2_gate_328_status.md`
- `runs/checkpoints/s2_gate_328_phase2_status.json`
- `runs/checkpoints/s2_gate_328_phase2_status.md`
- `runs/checkpoints/s2_gate_328_doctor.json`

## Evidence Summary

- Release decision status: `default_change_ready`
- Release recommendation: `promote_default_candidate`
- Resident fastpath handoff status: `passed`
- Resident fastpath handoff ready: true
- Resident fastpath required by benchmark contract: true
- Resident fastpath passed checks: 23
- Resident fastpath failed checks: 0
- Phase2 status: green

## Known Limitations

- This gate validates release-decision evidence handoff only; it does not rerun the full 200-light real-data benchmark.
- It uses Gate327 controlled acceptance evidence and Gate326 controlled repeat-runtime evidence.
- Phase2 status still summarizes the acceptance-side resident fastpath contract; a later gate can add explicit release-decision fastpath handoff visibility to Phase2 if needed.
- No registration math, CUDA kernel, runtime default, package artifact, or GitHub release behavior changed.

## Next Step

- Add Phase2 status visibility for `release_decision.resident_registration_fastpath_handoff`, then propagate the same guard into default-promotion, Windows release-matrix, and publish-preflight artifacts if release publication should require this chain.

## Clean-Room Compliance

- Compliant. This gate used GLASS-generated acceptance, runtime, release-decision, and status artifacts only.
- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- Input image directories were not modified.
