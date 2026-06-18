# S2-Gate 324 Status - Release Decision Warp Quality Handoff

## Gate

S2-Gate 324: Release-promotion decision warp quality handoff.

## Completed

- Added `warp_quality_handoff` to `glass release-promotion-decision`.
- The release decision now consumes acceptance-level `warp_quality_contract` evidence.
- Added release-blocking check `warp_quality_contract_handoff`:
  - passes when no warp evidence is present in older acceptance artifacts
  - passes when attached warp evidence is present, typed as `warp_quality_contract`, and passing
  - fails when attached warp evidence is missing, malformed, or failed
- Added Markdown output section `Warp Quality Handoff`.
- Added focused tests for:
  - passing warp-quality handoff
  - failed warp-quality handoff blocking release-candidate readiness
  - CLI Markdown handoff visibility
- Documented S2-Gate 324 in `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py docs\phase2_algorithm_hardening.md

.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py -k "warp_quality_handoff or cli_writes_outputs"

.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py

.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_323_acceptance_audit.json --out runs\checkpoints\s2_gate_324_release_promotion_decision.json --markdown runs\checkpoints\s2_gate_324_release_promotion_decision.md

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_324_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 3 passed, 16 deselected.
- Release-promotion pytest file: 19 passed.
- Full pytest: 756 passed in 32.69 s.
- Gate324 release-promotion decision artifact: release candidate ready.

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

- `runs/checkpoints/s2_gate_324_release_promotion_decision.json`
- `runs/checkpoints/s2_gate_324_release_promotion_decision.md`
- `runs/checkpoints/s2_gate_324_doctor.json`

## Release Handoff Result

- Release decision status: `release_candidate_ready`.
- Recommendation: `repeat_benchmark_before_default_change`.
- Release candidate ready: true.
- Default change ready: false.
- Warp-quality handoff status: passed.
- Warp-quality handoff ready: true.
- Warp-quality output count: 1.
- `warp_quality_contract_handoff`: passed.
- Runtime repeat evidence remains missing by design, so default-change readiness is false.

## Known Limitations

- This gate only propagates acceptance-level warp-quality evidence into release-promotion decisions; it does not add new warp math.
- Older acceptance audits without warp evidence remain non-blocking and are recorded as `not_available`.
- The checkpoint artifact reuses the S2-Gate 323 acceptance audit; it is not a new 200-light real-data benchmark.
- This gate does not change CUDA kernels, runtime defaults, package builds, release artifacts, or real-data benchmark outputs.

## Next Step

- Add a release/publication preflight layer that consumes `warp_quality_handoff`, or continue science hardening with a multi-frame warp residual fixture.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated checkpoint artifacts.
- Input image directories were not modified.
