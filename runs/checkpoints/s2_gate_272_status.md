# S2-Gate 272 Status

- Gate: S2-Gate 272
- Scope: Default promotion resident winsorized sweep guard
- Status: green
- Date: 2026-06-18
- CUDA available: yes

## Completed

- Added resident winsorized sweep evidence to `glass default-promotion-manifest`.
- Added default-promotion blockers for:
  - `resident_winsorized_sweep_audit_passed`
  - `resident_winsorized_sweep_required_frame_passed`
  - `resident_winsorized_sweep_check_count`
- Added CLI threshold controls for minimum sweep-audit check count and required sweep frame count.
- Added JSON and Markdown output for resident winsorized sweep evidence in the default promotion manifest.
- Added tests for ready, missing, and failed resident winsorized sweep evidence.
- Updated Phase 2 gate documentation and algorithm source notes.

## Commands

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\default_promotion_manifest.py src\\glass\\cli.py tests\\test_default_promotion_manifest.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_default_promotion_manifest.py`
- Generated `runs\\checkpoints\\s2_gate_272_phase2_status_fixture.json` from Gate271 sweep-audit evidence and a minimal default-promotion-ready Phase 2 fixture.
- `.\\.venv\\Scripts\\python.exe -m glass.cli default-promotion-manifest --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --phase2-status runs\\checkpoints\\s2_gate_272_phase2_status_fixture.json --doctor-json runs\\checkpoints\\s2_gate_226_doctor.json --require-doctor --min-runtime-runs 3 --out runs\\checkpoints\\s2_gate_272_default_promotion_manifest.json --markdown runs\\checkpoints\\s2_gate_272_default_promotion_manifest.md --fail-on-not-ready`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_default_promotion_manifest.py tests\\test_cli_smoke.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 11 passed.
- Related pytest: 60 passed.
- Full pytest: 624 passed.
- Default promotion manifest: `default_promotion_ready`.
- New resident winsorized sweep checks: all passed.
- Required 200-frame row: passed.
- Resident winsorized sweep audit check count: `27`.
- Required 200-frame hardened-vs-CPU RMS: `2.3066304440398834e-05`.
- Required 200-frame hardened-vs-CPU max abs: `6.103515625e-05`.
- Required 200-frame hardened CUDA time: `0.0012743999977828935 s`.
- CUDA/doctor fixture: native extension loaded on `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`, compute capability `12.0`, driver `596.21`, primary package `cuda13`, try order `cuda13,cuda12,cuda11,cpu`.

## Artifacts

- `runs/checkpoints/s2_gate_272_phase2_status_fixture.json`
- `runs/checkpoints/s2_gate_272_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_272_default_promotion_manifest.md`

## Known Limitations

- This gate is a default-promotion policy guard only.
- It does not change image math, CUDA kernels, runtime defaults, release artifacts, release-promotion decisions, package artifacts, or real-data benchmark outputs.
- The protected resident winsorized sweep remains synthetic 200-frame sample-count evidence and does not replace the full 200-light real-data benchmark.

## Next Step

- Carry this default-promotion guard forward into Windows release matrix and publish-preflight checks so publication cannot ignore the hardened winsorized 200-frame parity blocker.

## Clean-Room

- Compliant. This gate consumes GLASS-owned Phase 2 status, default-promotion, doctor, and release-decision artifacts only.
- It does not inspect or derive behavior from external proprietary implementation source.
