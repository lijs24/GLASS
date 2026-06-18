# S2-Gate 338 Status

- Gate: 338
- Status: green
- Scope: Phase2 resident result-contract status/compare handoff
- Date: 2026-06-19

## Completed

- Added resident CUDA result-contract row summarization to `glass phase2-status`.
- Added `pipeline_resident_result_contract_passed` as a Phase2 hard check.
- Added resident result-contract status, check state, required count, failed
  count, and failed check names to Phase2 Markdown.
- Added `glass phase2-status-compare` regressions for dropped resident
  result-contract checks, failed resident result contracts, and increased
  resident result-contract failure counts.
- Added tests for direct pipeline resident result-contract failure and compare
  preservation/regression.
- Generated controlled Gate338 Phase2 status and compare artifacts.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\phase2_status.py tests\test_phase2_status.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py -k "resident_result_contract or pipeline_contract"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_phase2_status.py`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints\s2_gate_338_fixture\checkpoints --pipeline-contract runs\checkpoints\s2_gate_338_fixture\pipeline_contract_passed_resident_result.json --out runs\checkpoints\s2_gate_338_phase2_status_baseline.json --markdown runs\checkpoints\s2_gate_338_phase2_status_baseline.md --skip-cuda-probe`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints\s2_gate_338_fixture\checkpoints --pipeline-contract runs\checkpoints\s2_gate_338_fixture\pipeline_contract_failed_resident_result.json --out runs\checkpoints\s2_gate_338_phase2_status_candidate.json --markdown runs\checkpoints\s2_gate_338_phase2_status_candidate.md --skip-cuda-probe`
- `.venv\Scripts\python.exe -m glass.cli phase2-status-compare --baseline-status runs\checkpoints\s2_gate_338_phase2_status_baseline.json --candidate-status runs\checkpoints\s2_gate_338_phase2_status_candidate.json --out runs\checkpoints\s2_gate_338_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_338_phase2_status_compare.md`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_338_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused Phase2 status tests: `66 passed in 0.86s`
- Full suite: `776 passed in 38.61s`
- Ruff: passed

## CUDA

- CUDA available: yes
- CUDA native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/checkpoints/s2_gate_338_fixture/pipeline_contract_passed_resident_result.json`
- `runs/checkpoints/s2_gate_338_fixture/pipeline_contract_failed_resident_result.json`
- `runs/checkpoints/s2_gate_338_phase2_status_baseline.json`
- `runs/checkpoints/s2_gate_338_phase2_status_baseline.md`
- `runs/checkpoints/s2_gate_338_phase2_status_candidate.json`
- `runs/checkpoints/s2_gate_338_phase2_status_candidate.md`
- `runs/checkpoints/s2_gate_338_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_338_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_338_doctor.json`

## Known Limitations

- This gate is status/compare scoped. It does not change resident CUDA
  integration math, registration math, runtime defaults, package artifacts, or
  benchmark results.
- The generated status artifacts use controlled fixture pipeline-contract JSON
  rather than a new 200-light real-data rerun.

## Next Step

- Continue Phase2 hardening by carrying this resident result-contract failure
  evidence into the next release/default-promotion or publication guard layer,
  or return to CUDA runtime optimization gates when the audit chain is complete.

## Clean-Room

- Compliant. This gate consumes GLASS-owned pipeline-contract and Phase2 status
  artifacts only. It does not inspect PixInsight/WBPP/PJSR source, modify
  PixInsight, or read user image directories.
