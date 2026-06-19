# S2-Gate 430 Status: Resident Catalog Batch Default

## Gate

S2-Gate 430

## Scope

Substantive Phase 2 runtime gate. This gate targets the resident CUDA triangle
registration/catalog bottleneck identified in Gate429 and avoids
release/default-promotion/report-only work.

## Completed

- Found that the Gate429 16-frame command did not enable grid catalogs:
  - `triangle_catalog_batch=False`;
  - `triangle_moving_catalog` was about `75.212 s`;
  - `resident_registration_warp` was about `80.232 s`.
- Changed the resident `similarity_cuda_triangle` default so, when no star grid
  is explicitly provided, it auto-enables deterministic grid-batch catalogs:
  - `star_grid_cols=8`;
  - `star_grid_rows=8`;
  - `triangle_grid_top_per_cell=8`;
  - `star_catalog_deterministic=True`;
  - `triangle_catalog_grid_auto=True`;
  - `triangle_catalog_batch=True`.
- Preserved explicit user overrides for:
  - `--resident-star-grid-cols`;
  - `--resident-star-grid-rows`;
  - `--resident-star-catalog-deterministic`;
  - `--resident-triangle-grid-top-per-cell`.
- Added artifact/warning evidence for:
  - `triangle_catalog_grid_auto`;
  - `triangle_catalog_selector`;
  - `triangle_star_grid_cols`;
  - `triangle_star_grid_rows`.
- Updated resident CUDA tests to cover both default auto-grid and explicit
  grid override behavior.
- Updated Phase 2 planning docs and algorithm-source notes.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_430_grid_batch_probe_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit --resident-star-grid-cols 8 --resident-star-grid-rows 8 --resident-star-catalog-deterministic --resident-triangle-grid-top-per-cell 4
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_430_grid8_top8_probe_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit --resident-star-grid-cols 8 --resident-star-grid-rows 8 --resident-star-catalog-deterministic --resident-triangle-grid-top-per-cell 8
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_uses_gpu_centroid_without_pixel_refine tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "triangle or auto_dispatch or quality_reference"
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_430_auto_grid_top8_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-warp-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_430_auto_grid_top8_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_430_auto_grid_top8_warp_input_audit.json --markdown runs\checkpoints\s2_gate_430_auto_grid_top8_warp_input_audit.md
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-rejection-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_430_auto_grid_top8_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_430_auto_grid_top8_rejection_input_audit.json --markdown runs\checkpoints\s2_gate_430_auto_grid_top8_rejection_input_audit.md --evaluation-region compare_region --max-same-pre-rejection-abs-delta 16
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_430_auto_grid_top8_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --rejection-input-audit runs\checkpoints\s2_gate_430_auto_grid_top8_rejection_input_audit.json --evaluation-region compare_region --max-pre-rejection-sample-delta 0 --max-same-pre-rejection-abs-delta 0 --max-rejected-sample-delta 0 --out runs\checkpoints\s2_gate_430_auto_grid_top8_rejection_sample_attributed_audit.json --markdown runs\checkpoints\s2_gate_430_auto_grid_top8_rejection_sample_attributed_audit.md
```

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_430_cuda_doctor.json
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Default auto-grid and explicit override tests: `2 passed`.
- Focused resident CUDA tests: `12 passed, 38 deselected`.
- Ruff: passed.
- Full pytest: `1007 passed in 40.66s`.

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native extension loaded: yes

Doctor artifact:

- `runs/checkpoints/s2_gate_430_cuda_doctor.json`

## Validation Artifacts

- Formal Gate430 resident run:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_refF16_cuda_hardened/`
- Warp input audit:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_warp_input_audit.json`
- Warp input audit Markdown:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_warp_input_audit.md`
- Rejection input audit:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_rejection_input_audit.json`
- Rejection input audit Markdown:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_rejection_input_audit.md`
- Rejection sample audit:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_rejection_sample_attributed_audit.json`
- Rejection sample audit Markdown:
  `runs/checkpoints/s2_gate_430_auto_grid_top8_rejection_sample_attributed_audit.md`

## Runtime and Numerical Result

Formal default-path comparison against Gate429 on the same 16-frame checkpoint
harness:

| Metric | Gate429 | Gate430 |
| --- | ---: | ---: |
| Total resident run | 80.419519 s | 0.227297 s |
| resident_registration_warp | 80.232060 s | 0.047995 s |
| triangle_moving_catalog | 75.212454 s | 0.010105 s |
| triangle_moving_catalog_batch | n/a | 0.010073 s |
| triangle_catalog_batch | false | true |
| star grid | 0x0 | 8x8 |
| triangle_grid_top_per_cell | 4 | 8 |
| matrix translation delta max | 0.0077076656 px | 0.0077076656 px |
| resident-matrix warp RMS max | 0.1586616188 | 0.1586616188 |
| master abs delta sum | 6638.656708 | 6610.556580 |
| coverage abs delta sum | 706 | 700 |
| low rejection abs delta sum | 356 | 357 |
| high rejection abs delta sum | 350 | 343 |
| compare-region pre-rejection sample delta | 0 | 0 |
| same-pre rejected-sample abs delta | 706 | 700 |

Interpretation:

- The Gate429 registration/catalog hot path was a default-route miss: batch
  primitives already existed but were not selected by the default command.
- Gate430 makes the fast path default and records that choice in artifacts.
- Matrix and RMS parity did not regress.
- Output-map deltas are no worse overall and improve on master, coverage, high
  rejection, and same-pre rejected sample counts. Low rejection changes by +1
  sample relative to Gate429.
- `resident-rejection-input-audit` still passes, while strict zero-delta sample
  audit remains attention-required. The next blocker is resident
  warp/rejection value parity or a real 200-light regression using the now-fast
  default path.

## Known Limitations

- The real 200-light regression was not run in this gate.
- Local normalization remains disabled in this validation run.
- `resident-rejection-sample-audit` still reports attention required at strict
  zero-delta thresholds.
- Native batch catalog still reports `per_frame_launch_sync_download`; this
  gate changes default routing, not the deeper native batch implementation.

## Next Gate

S2-Gate 431 should either:

- target remaining resident warp/rejection value parity at strict sample-audit
  thresholds; or
- run the real 200-light regression with the Gate430 default resident triangle
  path to verify the speedup transfers beyond the 16-frame harness.

## Clean-Room Compliance

Compliant.

- No PixInsight or WBPP/PJSR source was read, copied, summarized, or reworked.
- Only GLASS source/tests and GLASS-generated checkpoint artifacts were used.
- No user input image directory was modified.
- No release or package publication action was performed.
