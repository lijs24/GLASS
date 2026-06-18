# S2-Gate 271 Status

- Gate: S2-Gate 271
- Scope: Phase 2 resident winsorized sweep status-compare guard
- Status: green
- Date: 2026-06-18
- CUDA available: yes

## Completed

- Added `glass phase2-status-compare` regression checks for `resident_winsorized_sweep_audit`.
- Preserves a previously passing resident winsorized sweep audit in candidate status artifacts.
- Preserves the required 200-frame row pass status.
- Requires candidate sweep-audit check count to stay at least as high as the baseline check count.
- Carries resident winsorized sweep summaries into status-compare baseline/candidate outputs.
- Added focused regression tests for the compare guard.
- Updated Phase 2 gate documentation and algorithm source notes.

## Commands

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --resident-winsorized-benchmark-audit runs\\checkpoints\\s2_gate_266_resident_winsorized_benchmark_audit.json --resident-winsorized-sweep-audit runs\\checkpoints\\s2_gate_269_resident_winsorized_sweep_audit.json --out runs\\checkpoints\\s2_gate_271_phase2_status.json --markdown runs\\checkpoints\\s2_gate_271_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_270_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_271_phase2_status.json --out runs\\checkpoints\\s2_gate_271_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_271_phase2_status_compare.md --fail-on-regression`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py tests\\test_resident_winsorized_sweep_contract.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 28 passed.
- Related pytest: 54 passed.
- Full pytest: 622 passed.
- Phase 2 status artifact: green.
- Phase 2 status-compare artifact: passed.
- New compare checks: `resident_winsorized_sweep_audit_passed_preserved`, `resident_winsorized_sweep_required_frame_preserved`, and `resident_winsorized_sweep_check_count_not_decreased` all passed.
- Baseline/candidate required 200-frame row: passed to passed.
- Baseline/candidate sweep-audit check count: `27` to `27`.
- CUDA probe: native extension loaded on `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`, compute capability `12.0`, VRAM `97886 MiB`, driver `596.21`.

## Known Limitations

- This gate is a status-compare guard only.
- It does not change image math, CUDA kernels, runtime defaults, release artifacts, promotion policy, package artifacts, or real-data benchmark outputs.
- The protected sweep audit remains synthetic 200-frame sample-count evidence and does not replace the full 200-light real-data benchmark.

## Next Step

- Use the compare guard to protect hardened winsorized 200-frame sweep parity evidence while moving toward release/default promotion handoffs.

## Clean-Room

- Compliant. This gate consumes GLASS-owned Phase 2 status JSON only.
- It does not inspect or derive behavior from external proprietary implementation source.
