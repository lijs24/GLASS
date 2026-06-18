# S2-Gate 339 Status

- Gate: 339
- Status: green
- Scope: Default promotion resident result-contract guard
- Date: 2026-06-19

## Completed

- Carried Phase2 resident result-contract evidence into
  `glass default-promotion-manifest`.
- Added `pipeline_resident_result_contract_handoff_passed` as a default
  promotion blocker.
- Required resident result-contract evidence to be present, passed,
  Phase2-checked, required by at least one output, and free of failed output
  rows or nested failed checks before resident CUDA default promotion can pass.
- Surfaced resident result-contract readiness, status, Phase2 check, required
  count, failed count, and failed nested check names in default-promotion
  Markdown.
- Added focused tests for ready default-promotion artifacts and failed resident
  result-contract drift.
- Generated controlled Gate339 default-promotion artifacts for passing and
  blocked resident result-contract scenarios.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py -k "resident_result_contract or passes_ready"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_339_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_339_fixture\release_decision.json --phase2-status runs\checkpoints\s2_gate_339_fixture\phase2_status_passed_resident_result.json --doctor-json runs\checkpoints\s2_gate_339_doctor.json --out runs\checkpoints\s2_gate_339_default_promotion_passed.json --markdown runs\checkpoints\s2_gate_339_default_promotion_passed.md --require-doctor --min-runtime-runs 3`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_339_fixture\release_decision.json --phase2-status runs\checkpoints\s2_gate_339_fixture\phase2_status_failed_resident_result.json --doctor-json runs\checkpoints\s2_gate_339_doctor.json --out runs\checkpoints\s2_gate_339_default_promotion_failed_resident_result.json --markdown runs\checkpoints\s2_gate_339_default_promotion_failed_resident_result.md --require-doctor --min-runtime-runs 3`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused default-promotion tests: `2 passed, 22 deselected in 0.16s`
- Default-promotion test file: `24 passed in 0.35s`
- Full suite: `777 passed in 37.68s`
- Ruff: passed

## CUDA

- CUDA available: yes
- CUDA native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/checkpoints/s2_gate_339_doctor.json`
- `runs/checkpoints/s2_gate_339_fixture/release_decision.json`
- `runs/checkpoints/s2_gate_339_fixture/phase2_status_passed_resident_result.json`
- `runs/checkpoints/s2_gate_339_fixture/phase2_status_failed_resident_result.json`
- `runs/checkpoints/s2_gate_339_default_promotion_passed.json`
- `runs/checkpoints/s2_gate_339_default_promotion_passed.md`
- `runs/checkpoints/s2_gate_339_default_promotion_failed_resident_result.json`
- `runs/checkpoints/s2_gate_339_default_promotion_failed_resident_result.md`

## Known Limitations

- This gate is default-promotion scoped. It does not change resident CUDA
  integration math, registration math, runtime defaults, package artifacts, or
  benchmark results.
- The generated artifacts use controlled Phase2/release-decision fixtures rather
  than a new 200-light real-data rerun.

## Next Step

- Carry the default-promotion resident result-contract guard into the Windows
  release matrix so package readiness cannot advance when default-promotion
  resident result-contract evidence is missing or failed.

## Clean-Room

- Compliant. This gate consumes GLASS-owned Phase2 status and release-decision
  artifacts only. It does not inspect PixInsight/WBPP/PJSR source, modify
  PixInsight, or read user image directories.
