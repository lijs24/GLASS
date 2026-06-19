# S2-Gate 452 Status: Real 200-Light Resident Regression And Frame-Accounting Closure

## Gate

- Gate: S2-Gate 452
- Scope: Return to Phase 2 core work after report/release handoff gates.
- Status: passed
- Date: 2026-06-20 local / 2026-06-19 UTC artifact timestamps

## Gate400-413 Core-Goal Value

- Gate400-403: useful acceptance-contract plumbing. They made the resident CUDA
  DQ benchmark profile reusable and less hand-authored, but did not improve
  image math or runtime.
- Gate404-413: mostly evidence-chain propagation through runtime sweep,
  Phase2 status, release promotion, default promotion, Windows matrix, publish
  preflight, and publication audit layers. Their practical value is preventing
  benchmark-profile evidence loss during publication workflows.
- Net value: audit robustness, not scientific or CUDA throughput progress.
  After Gate413, continuing pure release/default-promotion/report-only gates
  had diminishing value for the Phase 2 core target.
- Gate452 therefore intentionally returned to real 200-light execution,
  resident CUDA acceptance, frame accounting closure, and source-DQ cache
  preflight.

## Completed Work

- Ran the current resident CUDA path on the M38 H-alpha 200-light benchmark.
- Identified default-path drift: current default `auto` registration-quality
  behavior integrates 191/200 frames because it excludes F000080 and F000194
  for low inlier counts, while the Phase 1 contract-parity path integrates
  193/200 frames.
- Rebuilt the contract-parity run with shared resident master cache and
  `--resident-registration-quality-gate warn`.
- Fixed frame accounting so `zero_weight_frames` is counted from
  `integration_status_counts`, while final status can remain diagnostic, such
  as `quality_rejected`.
- Updated acceptance-audit contract compatibility so legacy
  `required_final_status_counts.zero_weight` can be satisfied by integration
  status when final status carries a more specific rejection reason.
- Added guarded source-DQ cache preflight for the resident
  `--resident-source-dq-cache generate-calibration` route.
- Fixed source-DQ cache preflight disk probing when the run directory does not
  yet exist.
- Reran pipeline, StackEngine, and acceptance contracts on the real 200-light
  contract-parity run.
- Documented Gate452 in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Real 200-Light Results

- Dataset: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat.
- WBPP black-box elapsed time: 1092.541 s.
- Current default resident run:
  - Path: `C:\glass_runs\phase2_s2_gate_452_200\default_resident_20260620_015127`
  - Elapsed: 40.697376 s.
  - Integrated frames: 191/200.
  - Speedup vs WBPP timing: 26.845490x.
  - Compare: shape matched, RMS diff 0.00173079, P99 abs diff 0.000442563.
  - Finding: stricter quality gate excludes F000080 and F000194 beyond the
    seven known masked/manual frames.
- Contract-parity resident run:
  - Path: `C:\glass_runs\phase2_s2_gate_452_200\contract_parity_20260620_015444`
  - Elapsed: 30.900435 s.
  - Integrated frames: 193/200.
  - Speedup vs WBPP timing: 35.356816x.
  - Compare: shape matched, coverage fraction 0.960818, RMS diff 0.00170183,
    P99 abs diff 0.000458048.
  - Acceptance audit: passed, failed checks 0.

## Source-DQ Cache Preflight

- Artifact: `runs/checkpoints/s2_gate_452_real_source_dq_cache_preflight.json`
- Ready light frames: 200.
- Estimated calibrated plus DQ output bytes: 77,680,512,000.
- Disk free at probe path: 39,561,777,152 bytes.
- Max allowed at 75% budget: 29,671,332,864 bytes.
- Result: blocked with `estimated_cache_exceeds_disk_budget`.
- Interpretation: for this real dataset, the next DQ/mask work should prefer
  resident/in-VRAM propagation before large on-disk calibrated+DQ cache
  materialization.

## Commands Run

- `.venv\Scripts\python.exe -m glass.cli run ... --memory-mode resident ...`
  for the default resident 200-light run.
- `.venv\Scripts\python.exe -m glass.cli compare ...`
  for the default resident comparison.
- `.venv\Scripts\python.exe -m glass.cli run ... --resident-master-cache-dir ... --resident-registration-quality-gate warn ...`
  for the contract-parity 200-light run.
- `.venv\Scripts\python.exe -m glass.cli compare ...`
  for the contract-parity comparison.
- `.venv\Scripts\python.exe -m glass.cli resident-result-contract ...`
- `.venv\Scripts\python.exe -m glass.cli resident-calibration-contract ...`
- `.venv\Scripts\python.exe -m glass.cli pipeline-contract ...`
- `.venv\Scripts\python.exe -m glass.cli stack-engine-contract ...`
- `.venv\Scripts\python.exe -m glass.cli acceptance-audit ...`
- `.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\frame_accounting.py src\glass\report\benchmark_contract.py tests\test_resident_cuda_run.py tests\test_resident_frame_mask_contract.py tests\test_acceptance_audit.py tests\test_frame_accounting.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "source_dq_cache_preflight or source_dq_cache_route"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_frame_mask_contract.py tests\test_frame_accounting.py tests\test_acceptance_audit.py -k "frame_accounting or resident_frame_mask"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py::test_acceptance_audit_accepts_zero_weight_as_orthogonal_integration_status`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused ruff: passed.
- Focused source-DQ cache tests: 3 passed, 60 deselected.
- Focused frame-accounting/acceptance tests: 11 passed, 41 deselected.
- New orthogonal zero-weight acceptance test: 1 passed.
- Full pytest: 1075 passed in 40.97 s.

## CUDA Status

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97,886 MiB.
- Driver: 596.21.
- Native extension loaded: yes.

## Artifacts

- `runs/checkpoints/s2_gate_452_real_regression_summary.json`
- `runs/checkpoints/s2_gate_452_real_source_dq_cache_preflight.json`
- `runs/checkpoints/s2_gate_452_cuda_doctor_probe.json`
- `C:\glass_runs\phase2_s2_gate_452_200\default_resident_20260620_015127`
- `C:\glass_runs\phase2_s2_gate_452_200\contract_parity_20260620_015444`

## Known Limitations

- The current default resident quality gate is stricter than the Phase 1
  contract-parity benchmark. This is potentially scientifically reasonable,
  but it changes the expected 193-frame contract unless explicitly accepted.
- Strict native StackEngine default readiness remains incomplete for resident
  CUDA; the contract currently records a resident CUDA StackEngine surface.
- Source-DQ cache generation is guarded but not default for the 200-light
  dataset because on-disk calibrated+DQ cache size exceeds the current disk
  budget.
- Local normalization remains disabled in this 200-light benchmark.

## Next Gate

- S2-Gate453 should be a substantive core gate:
  - decide and test the default registration-quality policy against the
    200-light contract;
  - implement resident/in-VRAM source-DQ mask propagation without requiring
    the oversized on-disk calibrated+DQ cache;
  - keep acceptance on the 200-light dataset green;
  - measure timing impact against the 30.900435 s contract-parity baseline.

## Clean-Room Compliance

- Compliant. This gate used only GLASS source code, GLASS-generated artifacts,
  user-owned real image outputs, and WBPP black-box timing/output artifacts.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized,
  or modified.
- Input image directories were treated as read-only.
