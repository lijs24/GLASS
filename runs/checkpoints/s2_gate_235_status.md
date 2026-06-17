# S2-Gate 235 Status: Acceptance Rejection Sample Triage

## Gate

S2-Gate 235: Acceptance Rejection Sample Triage

## Completed

- Added compact rejection sample accounting triage to acceptance audit release evidence:
  `release_contract_evidence.pipeline_contract.rejection_sample_accounting`.
- Attached the same summary to the top-level `pipeline_contract.rejection_sample_accounting`
  record in acceptance audit JSON.
- Summarized the pipeline check `integration_rejection_sample_counts_match_maps`,
  pixel-verification state, accounted/required/verified/failed row counts,
  failed output items, rejection-map sample sums, provenance source counts, and failed
  source deltas.
- Added Markdown output for failed rejection sample accounting rows.
- Added an acceptance-audit test fixture for rejected-sample map/provenance drift.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_acceptance_audit.py tests\\test_pipeline_contract.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\acceptance_audit.py tests\\test_acceptance_audit.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -c "import json; import glass_cuda; available=bool(glass_cuda.cuda_available()); print(json.dumps({'cuda_available': available, 'devices': glass_cuda.list_devices() if available else []}, ensure_ascii=False))"`

## Test Results

- Targeted pytest: `69 passed in 4.12s`
- Targeted ruff: `All checks passed!`
- Full pytest: `540 passed in 25.89s`
- Full ruff: `All checks passed!`

## CUDA Availability

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Driver: 596.21
- Native backend available to GLASS: yes

## Artifacts

- Updated `src/glass/report/acceptance_audit.py`
- Updated `tests/test_acceptance_audit.py`
- Updated `docs/phase2_algorithm_hardening.md`
- Updated `docs/algorithm_sources.md`
- Checkpoint: `runs/checkpoints/s2_gate_235_status.md`

## Known Limitations

- This gate does not change integration math, CUDA kernels, runtime defaults, or package artifacts.
- This gate does not rerun the 200-light real benchmark.
- Acceptance triage summarizes existing pipeline-contract evidence; the pipeline contract remains the
  authoritative low-level pixel verification artifact.

## Next Step

- Continue hardening machine-readable status/report surfaces or move the rejection-accounting contract
  into the next measured candidate/benchmark acceptance workflow.

## Clean-Room Compliance

- Compliant. This gate consumes and summarizes GLASS-owned JSON artifacts only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No input image directory was modified.
