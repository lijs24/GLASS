# S2-Gate 346 Status

Gate: S2-Gate 346 - Phase2 compare failed-check evidence details

Status: green

- Status: green

## Completed

- Extended `glass phase2-status-compare` Markdown with a failed-check details
  section for regressed comparisons.
- Preserved the existing compare JSON schema and pass/fail logic.
- Added baseline/candidate evidence rows for failed compare checks.
- Added focused coverage proving StackEngine publication-audit resident
  result-contract regressions expose the failing candidate readiness and
  agreement fields in Markdown.
- Updated Phase 2 planning documentation and algorithm-source metadata.

## Commands Run

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\phase2_status.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --stack-engine-publication-audit runs\\checkpoints\\s2_gate_344_stack_engine_publication_audit_passed.json --out runs\\checkpoints\\s2_gate_346_phase2_status_publication_audit_passed.json --markdown runs\\checkpoints\\s2_gate_346_phase2_status_publication_audit_passed.md --fail-on-not-green`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status --checkpoint-dir runs\\checkpoints --stack-engine-publication-audit runs\\checkpoints\\s2_gate_344_stack_engine_publication_audit_failed_resident_result.json --out runs\\checkpoints\\s2_gate_346_phase2_status_publication_audit_failed_resident_result.json --markdown runs\\checkpoints\\s2_gate_346_phase2_status_publication_audit_failed_resident_result.md`
- `.\\.venv\\Scripts\\python.exe -m glass.cli phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_346_phase2_status_publication_audit_passed.json --candidate-status runs\\checkpoints\\s2_gate_346_phase2_status_publication_audit_failed_resident_result.json --out runs\\checkpoints\\s2_gate_346_phase2_status_compare_publication_resident_result.json --markdown runs\\checkpoints\\s2_gate_346_phase2_status_compare_publication_resident_result.md`
- `Select-String -Path runs\\checkpoints\\s2_gate_346_phase2_status_compare_publication_resident_result.md -Pattern "Failed Check Details|stack_engine_publication_resident_result_contract_chain_preserved|phase2_publish_preflight_resident_result_contract_matches_publish_preflight" -Context 0,2`
- `.\\.venv\\Scripts\\python.exe -m glass.cli doctor --json runs\\checkpoints\\s2_gate_346_cuda_doctor.json`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused pytest: 72 passed in 1.12 s.
- Full pytest: 791 passed in 32.82 s.

## CUDA Availability

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_346_cuda_doctor.json`
- `runs/checkpoints/s2_gate_346_phase2_status_publication_audit_passed.json`
- `runs/checkpoints/s2_gate_346_phase2_status_publication_audit_passed.md`
- `runs/checkpoints/s2_gate_346_phase2_status_publication_audit_failed_resident_result.json`
- `runs/checkpoints/s2_gate_346_phase2_status_publication_audit_failed_resident_result.md`
- `runs/checkpoints/s2_gate_346_phase2_status_compare_publication_resident_result.json`
- `runs/checkpoints/s2_gate_346_phase2_status_compare_publication_resident_result.md`

## Known Limitations

- This gate is Markdown report scoped. It does not change compare JSON
  semantics, image math, registration, CUDA kernels, runtime defaults, package
  builds, package upload, GitHub release creation, or real-data benchmark
  outputs.
- Gate346 artifacts are controlled status/compare fixtures, not real package
  builds or benchmark reruns.

## Next Step

- Continue with the next Phase 2 hardening gate, preferably another
  release-readiness or runtime-evidence handoff before changing CUDA math or
  defaults.

## Clean-Room Compliance

- This gate consumes only GLASS-owned Phase2 status/compare payloads.
- It does not read PixInsight/WBPP/PJSR source, external implementation source,
  user image directories, or proprietary behavior.
