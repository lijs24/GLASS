# S2 Gate 427 Status - Resident Rejection Attribution Contract Correction

Date: 2026-06-19
Base commit: 2c7429e

## Gate Intent

Return to the Phase 2 runtime/DQ mainline and correct the attribution contract
that decides the next optimization target. Gate424 proved that CPU replay and
CUDA hardened winsorized integration match exactly when they receive the same
registered input samples. Gate426 still showed same-pre rejection-map deltas
because resident registration/warp input values differ before rejection. The
sample audit alone was still recommending a winsorized-kernel fix, which would
send the next gate in the wrong direction.

This gate is runtime-attribution scoped. It does not add release/default
promotion/report-only handoff evidence and does not modify input data.

## Implemented

- Extended `resident-rejection-sample-audit` with optional
  `--rejection-input-audit`.
- The sample audit now records `attribution_evidence` from a
  `resident-rejection-input-audit` artifact.
- When exact-input CPU/CUDA parity is proven and the input audit attributes the
  remaining resident delta upstream, the sample audit recommendation changes
  from `fix_resident_winsorized_rejection_semantics` to
  `target_resident_registration_warp_input_parity`.
- Raw sample deltas, failed threshold checks, and the original rejection-map
  failures remain visible.
- Fixed the sample-audit ready condition so `rejection_sample_accounting_ready`
  requires all three thresholds to pass:
  - rejected-sample delta;
  - pre-rejection sample delta;
  - same-pre-rejection rejected-sample delta.
- Updated the nested sample summary emitted by `resident-rejection-input-audit`
  so it preserves `raw_recommendation` and also reports the exact-input
  attributed recommendation.
- Added focused regression tests.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_rejection_sample_audit.py tests/test_resident_rejection_input_audit.py`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_426_gpu_median_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_427_rejection_input_audit.json --markdown runs\checkpoints\s2_gate_427_rejection_input_audit.md --evaluation-region compare_region --max-same-pre-rejection-abs-delta 16`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_426_gpu_median_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --rejection-input-audit runs\checkpoints\s2_gate_427_rejection_input_audit.json --evaluation-region compare_region --max-pre-rejection-sample-delta 0 --max-same-pre-rejection-abs-delta 0 --max-rejected-sample-delta 0 --out runs\checkpoints\s2_gate_427_rejection_sample_attributed_audit.json --markdown runs\checkpoints\s2_gate_427_rejection_sample_attributed_audit.md`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_427_cuda_doctor.json`

## Results

- Focused tests: 9 passed in 0.61s.
- Full pytest: 1006 passed in 38.03s.
- Gate427 input audit: passed.
- Gate427 attributed sample audit: attention required, as expected, because
  resident output parity is still not closed.

### Exact-Input Audit

- Status: `passed`.
- Recommendation: `target_resident_registration_warp_input_parity`.
- CPU registered-cache replay: passed.
- CUDA exact-input hardened winsorized replay: passed.
- Resident output parity: false.
- Resident output attribution status: `resident_registration_warp_input_delta`.
- Compare-region pre-rejection abs delta: `0`.
- Compare-region same-pre rejected abs delta: `798`.

### Attributed Sample Audit

- Status: `attention_required`.
- Recommendation: `target_resident_registration_warp_input_parity`.
- Exact-input parity proven: true.
- CUDA exact-input status: `completed`.
- CUDA exact-input passed: true.
- Resident input delta attributed: true.
- Compare-region rejected sample delta: `-38`.
- Compare-region coverage sample delta: `38`.
- Compare-region pre-rejection sample delta: `0`.
- Compare-region same-pre rejected abs delta: `798`.
- Failed checks remain:
  - `rejected_sample_delta_within_limit`;
  - `same_pre_rejection_semantic_delta_within_limit`.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_427_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_427_status.md`
- `runs/checkpoints/s2_gate_427_cuda_doctor.json`
- `runs/checkpoints/s2_gate_427_rejection_input_audit.json`
- `runs/checkpoints/s2_gate_427_rejection_input_audit.md`
- `runs/checkpoints/s2_gate_427_rejection_sample_attributed_audit.json`
- `runs/checkpoints/s2_gate_427_rejection_sample_attributed_audit.md`

## Known Limitations

- This gate does not change CUDA rejection math, registration matrices, warp
  kernels, or output pixels.
- Resident output parity remains blocked by registration/warp input value
  differences.
- The proof uses the 16-frame synthetic checkpoint harness, not the real
  200-light regression.
- The sample audit still shows same-pre rejection-map deltas; Gate427 only
  fixes attribution using stronger exact-input evidence.

## Next Substantive Gate

S2 Gate 428 should target resident registration/warp input parity directly:

- reduce resident matrix/value deltas below the current Gate426/Gate427
  checkpoint levels;
- rerun `resident-warp-input-audit`, `resident-rejection-input-audit`, and the
  attributed sample audit;
- only after the 16-frame checkpoint improves, rerun the 200-light real-data
  performance and numerical regression.

No release/default-promotion/report-contract-only gates should be added unless
they directly block those runtime goals.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was
read or used. This gate uses GLASS code, GLASS-generated checkpoint artifacts,
and generic count-map/exact-input attribution math only. Input image
directories were not modified.
