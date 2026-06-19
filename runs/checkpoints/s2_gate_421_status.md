# S2-Gate 421 Status: Resident Rejection Sample Accounting Audit

## Gate

S2-Gate 421.

## Status

Green checkpoint for a substantive runtime-diagnostic gate. The produced audit
artifact is intentionally `attention_required` because it located the remaining
Gate420 parity blocker instead of hiding it.

## Gate400-413 Core-Goal Value Summary

- Gate400-405 established and surfaced resident CUDA DQ/profile evidence in
  quality evidence, contract profiles, acceptance audit, runtime sweep planning,
  and Phase2 status.
- Gate406-413 propagated that evidence through release-promotion,
  default-promotion, Windows release matrix, publish preflight, publication
  audit, Phase2 status, and default-promotion publication-audit layers.
- Direct value to Phase2 core runtime goals was limited: these gates protected
  evidence from being dropped, but they did not change StackEngine default
  execution, CUDA kernels, registration math, DQ pixel semantics, real 200-light
  regression behavior, or resident numerical parity.
- This gate stops that handoff chain and returns to the Gate420 runtime blocker:
  CUDA resident versus CPU tiled rejection/sample accounting.

## Completed Work

- Added `glass resident-rejection-sample-audit`.
- Implemented tiled FITS-map comparison for CPU tiled versus CUDA resident:
  coverage, low rejection, high rejection, and DQ maps.
- Decomposed rejected-sample differences into coverage delta, pre-rejection
  sample delta, same-pre-rejection rejection delta, compare-region split, DQ
  mismatch, warp-edge overlap, and top hotspot tiles.
- Added focused unit/CLI tests.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.
- Generated Gate421 audit artifacts from the Gate414 CPU run and Gate420
  no-pixel-refine resident CUDA run.

## Validation Findings

- Gate420 rejected-sample delta remains `117`, above the strict `64` threshold.
- Coverage-sample delta is `10085`.
- Pre-rejection sample delta is `10202`.
- Inside the formal compare region, pre-rejection sample delta is `0` and
  rejected-sample delta is `-16`.
- Outside the compare region, pre-rejection sample delta is `10202` and
  rejected-sample delta is `133`.
- Recommendation: `fix_resident_geometric_coverage_or_transform`.
- Interpretation: the global rejected-sample parity blocker is dominated by
  resident geometric/coverage/edge sample drift before rejection. A smaller
  same-pre-rejection residual remains for later winsorized rejection parity work.

## Artifacts

- `runs/checkpoints/s2_gate_421_rejection_sample_audit.json`
- `runs/checkpoints/s2_gate_421_rejection_sample_audit.md`
- `runs/checkpoints/s2_gate_421_cuda_doctor.json`
- `runs/checkpoints/s2_gate_421_status.md`

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_rejection_sample_audit.py tests\test_resident_rejection_sample_audit.py src\glass\cli.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_rejection_sample_audit.py`
- `.\.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_compare.json --out runs\checkpoints\s2_gate_421_rejection_sample_audit.json --markdown runs\checkpoints\s2_gate_421_rejection_sample_audit.md --tile-size 64 --top-tiles 12 --max-rejected-sample-delta 64`
- `.\.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --help`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_rejection_sample_audit.py tests\test_resident_parity_summary.py tests\test_resident_result_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_421_cuda_doctor.json --allow-cpu-only`

## Test Results

- Focused new test: `3 passed in 0.30s`.
- Focused regression tests: `20 passed in 0.59s`.
- Full pytest: `995 passed in 37.21s`.
- Ruff: passed.
- CLI help: passed.

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Known Limitations

- This gate does not fix resident coverage/edge parity.
- This gate does not change CUDA kernels, warp math, registration fitting,
  rejection math, runtime defaults, package artifacts, or release state.
- The Gate421 audit used the existing 16-frame synthetic Gate414/Gate420
  artifacts, not the 200-light real-data benchmark.

## Next Substantive Gate

S2-Gate 422 should fix resident coverage/edge or transform parity first. The
same Gate414/Gate420 validation should be rerun and should reduce the
pre-rejection sample delta before tightening same-pre-rejection winsorized
rejection semantics.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned source, tests, generated synthetic
run artifacts, and GLASS compare outputs. It did not read external proprietary
source, user image directories, or PixInsight/WBPP implementation files.
