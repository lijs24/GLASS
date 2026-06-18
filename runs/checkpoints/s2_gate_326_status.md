# S2-Gate 326 Status - Phase2 Runtime Repeat Closure Guard

## Gate

S2-Gate 326: Phase2 runtime repeat closure guard.

## Completed

- Added `release_decision_runtime_repeat_closure` to `glass phase2-status`.
- Added `release_decision_runtime_repeat_evidence_ready` as a Phase2 check.
- If a release decision claims `default_change_ready`, Phase2 status now requires:
  - runtime repeat evidence present
  - at least two repeat runs
  - at least two considered runs after warmup filtering
  - slowest/best elapsed ratio within the recorded maximum
- Preserved release-candidate compatibility: if a release decision is not default-change ready, repeat runtime evidence is recorded as `not_required`.
- Added Markdown output for runtime-repeat closure state.
- Added focused tests for:
  - a passing default-change release decision with repeat evidence
  - a contradictory default-change decision without repeat evidence
- Documented S2-Gate 326 in `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\report\phase2_status.py tests\test_phase2_status.py docs\phase2_algorithm_hardening.md

.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py -k "runtime_repeat or summarizes_green_handoff"

.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py

.venv\Scripts\python.exe -m glass.cli resident-runtime-compare --run repeat01=runs\checkpoints\s2_gate_326_runtime_fixture\repeat01 --run repeat02=runs\checkpoints\s2_gate_326_runtime_fixture\repeat02 --run repeat03=runs\checkpoints\s2_gate_326_runtime_fixture\repeat03 --baseline-label repeat01 --out runs\checkpoints\s2_gate_326_runtime_compare.json --markdown runs\checkpoints\s2_gate_326_runtime_compare.md

.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_323_acceptance_audit.json --runtime-compare runs\checkpoints\s2_gate_326_runtime_compare.json --min-runtime-runs 3 --out runs\checkpoints\s2_gate_326_release_promotion_decision.json --markdown runs\checkpoints\s2_gate_326_release_promotion_decision.md

.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints\s2_gate_326_phase2_checkpoint_fixture --release-decision runs\checkpoints\s2_gate_326_release_promotion_decision.json --out runs\checkpoints\s2_gate_326_phase2_status.json --markdown runs\checkpoints\s2_gate_326_phase2_status.md

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_326_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 2 passed, 58 deselected.
- Phase2 status pytest file: 60 passed.
- Full pytest: 759 passed in 32.61 s.
- Gate326 release-promotion decision artifact: `default_change_ready`.
- Gate326 Phase2 status artifact: green.

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

- `runs/checkpoints/s2_gate_326_runtime_fixture/`
- `runs/checkpoints/s2_gate_326_runtime_compare.json`
- `runs/checkpoints/s2_gate_326_runtime_compare.md`
- `runs/checkpoints/s2_gate_326_release_promotion_decision.json`
- `runs/checkpoints/s2_gate_326_release_promotion_decision.md`
- `runs/checkpoints/s2_gate_326_phase2_checkpoint_fixture/s2_gate_326_status.md`
- `runs/checkpoints/s2_gate_326_phase2_status.json`
- `runs/checkpoints/s2_gate_326_phase2_status.md`
- `runs/checkpoints/s2_gate_326_doctor.json`

## Runtime Closure Result

- Runtime compare best label: `repeat03`.
- Best elapsed: 99.8 s.
- Slowest/best elapsed ratio: 1.0140280561122246.
- Maximum allowed ratio: 1.25.
- Release decision status: `default_change_ready`.
- Release recommendation: `promote_default_candidate`.
- Phase2 runtime repeat closure: passed.
- `release_decision_runtime_repeat_evidence_ready`: passed.

## Known Limitations

- The runtime repeat fixture is a small controlled checkpoint artifact, not a new 200-light real-data rerun.
- The Gate326 Phase2 status artifact intentionally supplies only the release decision to isolate runtime-repeat closure; adding the Gate323 acceptance artifact would currently expose the separate resident-registration fastpath contract gap.
- This gate does not change CUDA kernels, registration, warp, integration, runtime defaults, package builds, release artifacts, or real-data benchmark outputs.

## Next Step

- Close the resident-registration fastpath acceptance handoff gap so a default-ready release decision and acceptance audit can be supplied together to `glass phase2-status`.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated checkpoint fixtures and artifacts.
- Input image directories were not modified.
