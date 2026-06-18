# S2-Gate 273 Status

- Gate: S2-Gate 273
- Scope: Windows release matrix resident winsorized sweep guard
- Status: green
- Date: 2026-06-18
- CUDA available: yes

## Completed

- Added resident winsorized sweep evidence to `glass windows-release-matrix` through the default-promotion manifest summary.
- Added release-matrix blockers for:
  - `default_promotion_resident_winsorized_sweep_audit_passed`
  - `default_promotion_resident_winsorized_required_frame_passed`
  - `default_promotion_resident_winsorized_sweep_check_count`
- Added CLI threshold controls for minimum sweep-audit check count and required sweep frame count.
- Added Windows release matrix JSON and Markdown output for resident winsorized sweep evidence.
- Added tests for ready, missing, and failed resident winsorized sweep evidence.
- Updated Phase 2 gate documentation and algorithm source notes.

## Commands

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\windows_release_matrix.py src\\glass\\cli.py tests\\test_windows_release_matrix.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_windows_release_matrix.py`
- `.\\.venv\\Scripts\\python.exe -m glass.cli windows-release-matrix --doctor-json runs\\checkpoints\\s2_gate_226_doctor.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --default-promotion-manifest runs\\checkpoints\\s2_gate_272_default_promotion_manifest.json --expected-primary-package cuda13 --out runs\\checkpoints\\s2_gate_273_windows_release_matrix.json --markdown runs\\checkpoints\\s2_gate_273_windows_release_matrix.md --fail-on-not-ready`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_windows_release_matrix.py tests\\test_default_promotion_manifest.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 11 passed.
- Related pytest: 43 passed.
- Full pytest: 626 passed.
- Windows release matrix: `release_matrix_ready`.
- New resident winsorized sweep matrix checks: all passed.
- Required 200-frame row: passed.
- Resident winsorized sweep audit check count: `27`.
- Required 200-frame hardened-vs-CPU RMS: `2.3066304440398834e-05`.
- Required 200-frame hardened-vs-CPU max abs: `6.103515625e-05`.
- Current machine/package evidence: CUDA available, native extension loaded, primary package `cuda13`, try order `cuda13,cuda12,cuda11,cpu`.

## Artifacts

- `runs/checkpoints/s2_gate_273_windows_release_matrix.json`
- `runs/checkpoints/s2_gate_273_windows_release_matrix.md`

## Known Limitations

- This gate is a Windows release-matrix policy guard only.
- It does not change image math, CUDA kernels, runtime defaults, package artifacts, GitHub release handoff, publish preflight, or real-data benchmark outputs.
- The protected resident winsorized sweep remains synthetic 200-frame sample-count evidence and does not replace the full 200-light real-data benchmark.

## Next Step

- Carry this Windows release-matrix guard into publish-preflight so the final publication preflight cannot ignore hardened winsorized 200-frame parity blockers.

## Clean-Room

- Compliant. This gate consumes GLASS-owned doctor, release-decision, default-promotion, and Windows release matrix artifacts only.
- It does not inspect or derive behavior from external proprietary implementation source.
