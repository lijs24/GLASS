# S2 Gate 423 Status - Resident Common-Footprint Coverage Parity

Date: 2026-06-19
Base commit: d167f87

## Gate Intent

Return Phase 2 work to the core execution path instead of adding more
release/default-promotion/report-only gates. Gate 423 targets resident CUDA
registration/warp coverage and numerical parity on the existing Gate 414/420
16-frame checkpoint harness, using an explicit common-footprint validation
contract before scaling back to the real 200-light regression.

## Gate 400-413 Core Value Summary

- Gate 400-413 improved auditability, command contracts, default-promotion
  evidence, report handoff, and release packaging surfaces.
- Their useful contribution to the core Phase 2 target is regression hygiene:
  they made it easier to compare artifacts, prove what path ran, and avoid
  silently publishing an unverified default.
- Their direct algorithmic value is limited: they did not materially advance
  StackEngine as the default computational path, DQ/mask semantics, resident
  CUDA registration/warp speed, numerical parity, or the real 200-light
  regression.
- Gate 423 therefore treats those gates as supporting infrastructure only and
  resumes substantive resident CUDA validation.

## Implemented

- Added `--evaluation-region {full_frame,compare_region}` to
  `glass resident-rejection-sample-audit`.
- Kept strict full-frame rejection-sample auditing as the default.
- Added compare-region threshold evaluation so the audit can validate the
  declared GLASS compare common footprint while still reporting global edge
  deltas.
- Added `evaluation_region` and `evaluation_deltas` to JSON/Markdown audit
  artifacts.
- Disabled the resident triangle CPU centroid-refinement probe by default. It
  remains opt-in because Gate 422 showed it is not a final pure-resident GPU
  algorithm and it regressed master-image RMS.
- Added tests for compare-region audit evaluation and the new default resident
  triangle behavior.
- Updated `docs/phase2_algorithm_hardening.md` with Gate 422 and Gate 423
  scope and acceptance criteria.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_rejection_sample_audit.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_skips_pixel_refine`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_423_common_footprint_compare.json --diagnostics-dir runs\checkpoints\s2_gate_423_common_footprint_compare_diagnostics --ignore-border-px 8 --glass-coverage-map runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened\integration\resident_coverage_map_H.fits --min-coverage 1`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_423_common_footprint_compare.html --diagnostics-dir runs\checkpoints\s2_gate_423_common_footprint_compare_diagnostics --ignore-border-px 8 --glass-coverage-map runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened\integration\resident_coverage_map_H.fits --min-coverage 1`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json --candidate-registration runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened\registration_results.json --out runs\checkpoints\s2_gate_423_common_footprint_matrix_compare.json --markdown runs\checkpoints\s2_gate_423_common_footprint_matrix_compare.md --max-translation-delta-px 0.05 --max-matrix-delta-frobenius 0.05`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_423_common_footprint_rejection_sample_audit.json --markdown runs\checkpoints\s2_gate_423_common_footprint_rejection_sample_audit.md --tile-size 64 --top-tiles 8 --max-rejected-sample-delta 64 --max-same-pre-rejection-abs-delta 1024 --evaluation-region compare_region`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_423_common_footprint_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_423_common_footprint_parity_summary.json --markdown runs\checkpoints\s2_gate_423_common_footprint_parity_summary.md --max-rejected-sample-delta 128`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_423_cuda_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`

## Results

- Targeted pytest: 5 passed in 0.82s.
- Full pytest: 999 passed in 37.39s.
- Resident CUDA run completed through integration in 80.37 s on the 16-frame
  checkpoint harness.
- Matrix compare: passed.
  - Maximum translation delta: 0.008781854250385976 px.
  - Mean translation delta: 0.0039021745376517994 px.
- Compare-region image parity: passed the Gate 420 tolerance family.
  - RMS diff: 0.0996942253107213.
  - Relative RMS diff: 0.00045330609093521205.
  - P99 abs diff: 0.22672576904296893.
  - Max abs diff: 3.08880615234375.
- Compare region:
  - Ignore border: 8 px.
  - Compared shape: 496 x 496.
  - Compared pixels: 246016.
  - Coverage fraction: 1.0.
  - Coverage min/median/max: 10 / 16 / 16.
- Rejection-sample audit with `evaluation_region=compare_region`: passed.
  - Pre-rejection sample delta: 0.
  - Rejected sample delta: -16.
  - Coverage sample delta: 16.
  - Same-pre-rejection abs rejected delta: 760.
- Global full-frame edge diagnostics remain visible:
  - Global pre-rejection sample delta: 10713.
  - Global rejected sample delta: 80.
  - Outside compare-region pre-rejection sample delta: 10713.
  - Outside compare-region rejected sample delta: 96.
- Resident parity summary: passed with recommendation
  `parity_and_contract_ready`.

## CUDA

CUDA is available. Doctor output reports:

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_423_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_423_common_footprint_refF16_cuda_hardened/`
- `runs/checkpoints/s2_gate_423_common_footprint_compare.json`
- `runs/checkpoints/s2_gate_423_common_footprint_compare.html`
- `runs/checkpoints/s2_gate_423_common_footprint_compare_diagnostics/`
- `runs/checkpoints/s2_gate_423_common_footprint_matrix_compare.json`
- `runs/checkpoints/s2_gate_423_common_footprint_matrix_compare.md`
- `runs/checkpoints/s2_gate_423_common_footprint_rejection_sample_audit.json`
- `runs/checkpoints/s2_gate_423_common_footprint_rejection_sample_audit.md`
- `runs/checkpoints/s2_gate_423_common_footprint_parity_summary.json`
- `runs/checkpoints/s2_gate_423_common_footprint_parity_summary.md`
- `runs/checkpoints/s2_gate_423_cuda_doctor.json`

## Known Limitations

- This gate used the 16-frame synthetic/checkpoint harness, not the real
  200-light regression. It is a parity-contract gate before the larger run.
- The resident path is slower than the CPU checkpoint on this small workload:
  80.37 s resident CUDA versus 41.94 s CPU tile. This does not represent the
  intended 200-light resident workload but confirms registration/warp
  orchestration is the next performance bottleneck.
- The common-footprint contract does not erase full-frame edge drift. It makes
  the crop/coverage assumption explicit and keeps full-frame deltas in the
  audit artifact.
- Same-pre-rejection rejected-sample semantics still differ inside the common
  footprint. The compare-region pre-rejection sample delta is zero, but the
  same-pre rejected-sample absolute delta is 760. This is a real next blocker,
  not a release evidence issue.
- A transient parallel compare JSON read/write race was observed while running
  commands in parallel. Serial reruns produced valid JSON and passing artifacts.

## Next Substantive Gate

S2 Gate 424 should target resident rejection semantic parity and then scale
back to performance:

- Compare CPU and resident winsorized sigma clipping decisions pixel-by-pixel
  inside the common footprint where pre-rejection samples already match.
- Close or explain the 760 same-pre rejected-sample absolute delta.
- Add a focused synthetic case for winsorized rejection decisions with known
  low/high outliers.
- After rejection semantics are green, run the real 200-light regression again
  and measure resident CUDA performance, especially the
  `resident_registration_warp` bottleneck.
- Start CUDA resident performance work where it matters: batch star catalogs,
  descriptor scoring, warp scheduling, and reduce Python/host-device
  orchestration.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was
read or used. This gate uses GLASS code, GLASS-generated artifacts,
synthetic/checkpoint data, and public CUDA/Numpy-style numerical methods only.
