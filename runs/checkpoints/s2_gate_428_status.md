# S2 Gate 428 Status - Guarded Resident Translation Refinement

Date: 2026-06-19
Base commit: 11faf0a

## Gate Intent

Return to Phase 2 runtime substance after Gate427 identified resident
registration/warp input parity as the next blocker. This gate touches the
resident triangle-registration refinement path directly and keeps the
release/default-promotion/report-only chain paused.

## Implemented

- Refactored resident triangle translation refinement into explicit seed
  scoring, median-translation fitting, pair RMS measurement, and optional
  guarded post-median refinement.
- Preserved the Gate426 first median-translation behavior as the default output
  path. This keeps resident triangle registration on a pure translation matrix
  after catalog matching instead of silently falling back to a general
  similarity seed when the seed has lower catalog RMS but worse image output.
- Added policy/artifact fields:
  - `cuda_triangle_translation_refine_iterations`;
  - `cuda_triangle_translation_refine_iteration_max_step_px`;
  - `triangle_translation_refine_max_iterations_observed`;
  - per-frame `triangle_translation_refine_initial_rms_px`;
  - per-frame `triangle_translation_refine_iterations`.
- Added focused unit coverage for median translation refinement and iterative
  seed-RMS reduction.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "triangle_translation_refine"`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_428_iterative_refine_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_428_guarded_refine_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_428_guarded_median_refine_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli resident-warp-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_428_guarded_median_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_428_guarded_median_warp_input_audit.json --markdown runs\checkpoints\s2_gate_428_guarded_median_warp_input_audit.md`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_428_guarded_median_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_428_guarded_median_rejection_input_audit.json --markdown runs\checkpoints\s2_gate_428_guarded_median_rejection_input_audit.md --evaluation-region compare_region --max-same-pre-rejection-abs-delta 16`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_428_guarded_median_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --rejection-input-audit runs\checkpoints\s2_gate_428_guarded_median_rejection_input_audit.json --evaluation-region compare_region --max-pre-rejection-sample-delta 0 --max-same-pre-rejection-abs-delta 0 --max-rejected-sample-delta 0 --out runs\checkpoints\s2_gate_428_guarded_median_rejection_sample_attributed_audit.json --markdown runs\checkpoints\s2_gate_428_guarded_median_rejection_sample_attributed_audit.md`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_428_cuda_doctor.json`

## Results

- Focused tests: 3 passed.
- Ruff: passed for the modified resident CUDA and test files.
- Full pytest: 1007 passed in 37.99s.
- CUDA doctor: CUDA native extension loaded and CUDA available.
- Guarded 16-frame resident CUDA run completed through integration.
- Warp input audit: passed.
- Rejection input audit: passed.
- Attributed rejection sample audit: attention required, as expected, because
  resident output parity is still blocked upstream.

### Failed Experiment Retained For Diagnosis

The first unguarded multi-iteration attempt is intentionally preserved as a
negative result:

- Run: `runs/checkpoints/s2_gate_428_iterative_refine_refF16_cuda_hardened`
- Warp audit: `runs/checkpoints/s2_gate_428_iterative_refine_warp_input_audit.json`
- Rejection input audit:
  `runs/checkpoints/s2_gate_428_rejection_input_audit.json`
- Attributed sample audit:
  `runs/checkpoints/s2_gate_428_rejection_sample_attributed_audit.json`

It reduced one matrix-delta mean slightly but worsened resident output deltas:

- resident matrix RMS max worsened from Gate426 `0.1683000218` to
  `0.1963685782`;
- resident output master abs delta sum worsened from `7488.0132` to
  `12454.6893`;
- rejected sample abs delta worsened from `1131` to `1769`.

The cause was that seed-RMS gating could reject the first median-translation
candidate and keep a general triangle similarity seed for some frames. The
final code preserves the first median translation unconditionally and guards
only post-median iterations.

### Guarded Median Validation

Final accepted 16-frame run:
`runs/checkpoints/s2_gate_428_guarded_median_refine_refF16_cuda_hardened`

Warp input summary:

- CPU-matrix resident warp RMS max: `0.0002643936071558697`.
- Resident matrix warp RMS max: `0.16830002181892761`.
- Resident translation delta max: `0.009531948948220055`.
- Resident translation delta mean: `0.005459747234037016`.
- Recommendation: `target_resident_registration_matrix_precision`.

Rejection input summary:

- CPU registered-cache replay: passed.
- CUDA exact-input hardened winsorized replay: passed.
- Resident output attribution status:
  `resident_registration_warp_input_delta`.
- Resident output master abs delta sum: `7488.013198852539`.
- Coverage abs delta sum: `798`.
- Low/high rejection abs delta sums: `402` / `396`.

Attributed sample summary:

- Status: `attention_required`.
- Recommendation: `target_resident_registration_warp_input_parity`.
- Pre-rejection sample delta: `504`.
- Rejected sample delta: `15`.
- Same-pre rejected abs delta: `832`.

These values intentionally match the Gate426 median-centroid baseline instead
of claiming a false improvement. The value of this gate is the runtime guard
that prevents the attempted multi-iteration path from regressing future runs.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_428_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_428_status.md`
- `runs/checkpoints/s2_gate_428_cuda_doctor.json`
- `runs/checkpoints/s2_gate_428_guarded_median_refine_refF16_cuda_hardened/`
- `runs/checkpoints/s2_gate_428_guarded_median_warp_input_audit.json`
- `runs/checkpoints/s2_gate_428_guarded_median_warp_input_audit.md`
- `runs/checkpoints/s2_gate_428_guarded_median_rejection_input_audit.json`
- `runs/checkpoints/s2_gate_428_guarded_median_rejection_input_audit.md`
- `runs/checkpoints/s2_gate_428_guarded_median_rejection_sample_attributed_audit.json`
- `runs/checkpoints/s2_gate_428_guarded_median_rejection_sample_attributed_audit.md`
- Failed diagnostic artifacts listed above.

## Known Limitations

- This gate does not close resident matrix parity.
- It does not improve the 16-frame output deltas beyond Gate426; it prevents a
  newly discovered refinement regression and makes future iterations auditable.
- It does not run the real 200-light regression because the 16-frame synthetic
  gate did not improve beyond Gate426.
- Remaining blocker is resident star-catalog/transform precision, not CUDA warp
  kernel parity or winsorized exact-input rejection math.

## Next Substantive Gate

S2 Gate 429 should improve resident star-catalog/transform precision directly:

- compare resident GPU star catalogs against the CPU streaming detector for the
  same calibrated frames;
- identify whether flux ranking, centroid background, NMS/grid selection, or
  pair selection drives the remaining `~0.01 px` translation delta;
- implement the smallest catalog/transform change that lowers the 16-frame
  warp/rejection deltas below Gate426;
- only then rerun the real 200-light benchmark.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was
read or used. This gate uses GLASS code, GLASS-generated synthetic artifacts,
and generic star-catalog translation refinement logic only. Input image
directories were not modified.
