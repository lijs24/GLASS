# S2-Gate 57 Status: Resident Determinism Audit

## Gate

S2-Gate 57: Resident Determinism Audit.

## Completed Content

- Added a `glass resident-determinism` command that compares two resident CUDA
  run directories or two `resident_artifacts.json` files.
- Added `src/glass/report/resident_determinism.py` to compare:
  - resident artifact combined SHA-256 signatures
  - per-frame catalog, descriptor, selected-fit, and trial signatures
  - registration result status, matrix, inliers, matched stars, and RMS
  - frame-accounting final, registration, and integration status
  - baseline and candidate total elapsed time
- Added JSON and Markdown outputs for repeat-run diagnostics.
- Added tests for matching runs, signature/status drift, CLI output, and help
  registration.
- Updated Phase 2 gate documentation and algorithm source tracking.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_determinism.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_57_200\determinism_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_57_200\determinism_b_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_57_200\determinism_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_57_200\determinism_b_20260601 --out C:\glass_runs\phase2_s2_gate_57_200\resident_determinism_a_vs_b.json --markdown C:\glass_runs\phase2_s2_gate_57_200\resident_determinism_a_vs_b.md`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_57_200\determinism_topn_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 0 --resident-star-grid-rows 0 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -c "import glass_cuda; print('cuda_available', glass_cuda.cuda_available()); print(glass_cuda.list_devices())"`

## Test Results

- Ruff: `All checks passed!`
- Focused tests: `4 passed in 0.19s`.
- Full pytest: `267 passed in 11.53s`.

## Real 200-Light Determinism Audit

- Baseline run:
  `C:\glass_runs\phase2_s2_gate_57_200\determinism_a_20260601`
- Candidate run:
  `C:\glass_runs\phase2_s2_gate_57_200\determinism_b_20260601`
- Audit JSON:
  `C:\glass_runs\phase2_s2_gate_57_200\resident_determinism_a_vs_b.json`
- Audit Markdown:
  `C:\glass_runs\phase2_s2_gate_57_200\resident_determinism_a_vs_b.md`
- Baseline elapsed: `13.99009760003537 s`.
- Candidate elapsed: `13.951187000144273 s`.
- Candidate/baseline ratio: `0.9972187041860953`.
- Frame accounting matched exactly: both runs reported `193` integrated frames
  and `7` zero-weight frames.
- Registration status counts matched exactly: both runs reported `192 ok`,
  `1 reference`, and `7 excluded`.
- Signature drift was detected:
  - artifact combined-signature differences: `1`
  - frame signature differences: `192`
  - registration row exact differences: `196`
  - frame accounting differences: `0`
- Frame signature drift type counts:
  - `reference_catalog_hash`: `192`
  - `moving_catalog_hash`: `192`
  - `reference_descriptor_hash`: `192`
  - `moving_descriptor_hash`: `192`
  - `selected_fit_hash`: `192`
  - `trial_signature_hash`: `192`
  - `reference_descriptor_count_count`: `192`
  - `moving_descriptor_count_count`: `187`

## Top-N Control Run

- A single control run with `--resident-star-grid-cols 0 --resident-star-grid-rows 0`
  completed at:
  `C:\glass_runs\phase2_s2_gate_57_200\determinism_topn_a_20260601`.
- Elapsed time: `507.2709077000618 s`.
- This is too slow to be a practical deterministic workaround. It supports the
  next-step conclusion that S2-Gate 58 should fix deterministic behavior inside
  the resident grid top-k catalog path rather than disabling grid cataloging.

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend loaded: yes.

## Regression Note

- This gate is diagnostic and does not change image math, registration
  decisions, CUDA kernels, or output pixels.
- The two repeated grid-catalog 200-light runs preserved accepted-frame counts
  and finished faster than the S2-Gate 55 audit-map baseline because this gate
  used `--resident-output-maps minimal`.
- The audit proves the previously suspected nondeterminism is catalog-level:
  even the reference catalog hash differs between repeated runs. Downstream
  descriptors, selected fits, trial signatures, and exact registration matrices
  consequently differ.
- The final integration frame accounting stayed stable in this pair of runs, so
  the observed drift is acceptance-sensitive but did not trigger a frame-count
  swing during this Gate57 repeat.

## Known Limitations

- The audit compares exact hashes and exact registration rows; it intentionally
  reports harmless float-level matrix drift as a registration difference.
- The audit does not yet classify numerical tolerances for registration rows.
- The audit does not fix the resident grid top-k nondeterminism; it makes it
  visible and localizes the next optimization/fix target.
- The top-N control run was executed only once because it took more than eight
  minutes; it was used as a performance sanity check, not as a determinism proof.

## Next Step

S2-Gate 58 should implement a deterministic resident grid top-k catalog mode.
The most likely approach is a deterministic per-cell candidate compaction path
or a two-pass grid candidate collection that avoids order-sensitive lock-free
prechecks while retaining enough parallelism to stay near the current
approximately 14 second 200-light runtime.

## Clean-Room Compliance

Compliant. This gate compares GLASS-owned JSON artifacts and signatures from
GLASS resident CUDA runs only. It does not read, copy, summarize, or derive
behavior from proprietary implementation source.
