# Gate 08 triangle descriptor grid-top real-pair status

Date: 2026-05-13 14:29:27 +08:00

## Gate

Gate 08: Registration

## Completed

- Fixed the triangle-descriptor registration helper so NMS does not scan only
  the first `max_candidates` bright structures when no explicit scan count is
  provided.
- Added grid-top NMS support to
  `glass.gpu.registration.register_triangle_descriptor_similarity_f32(...)`.
- Passed existing catalog grid-top parameters through
  `benchmarks/compare_astroalign_gpu_alignment.py` for the triangle descriptor
  path.
- Added a CUDA unit test covering `catalog_selector=grid_top_nms`.
- Reran the full calibrated M38 `S000061`/`S000062` pair benchmark.
- Updated `docs/registration_model.md` and `docs/cuda_backend.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\gpu\registration.py benchmarks\compare_astroalign_gpu_alignment.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --catalog-stars 64 --catalog-tolerance-px 3 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 32 --resident-star-core-preselect-top-k 16 --triangle-descriptor-max-descriptors 1200 --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v46_triangle_descriptor.json"
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --catalog-stars 64 --catalog-tolerance-px 3 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 32 --resident-star-core-preselect-top-k 16 --triangle-descriptor-max-descriptors 1200 --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v47_triangle_gridtop.json"
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

## Test Results

- Ruff: passed.
- Targeted GPU registration tests after adding grid-top coverage:
  `29 passed in 0.24s`.
- Full pytest suite: `157 passed in 7.47s`.
- `git diff --check`: no whitespace errors; Git reported only LF-to-CRLF working-copy warnings.

## Real Pair Benchmark

Artifact:

`C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v47_triangle_gridtop.json`

Summary:

- Astroalign elapsed: 9.722310599987395 s.
- `glass_cuda_triangle_descriptor_similarity` elapsed: 0.3269480000017211 s.
- Speedup versus astroalign: 29.736565447521368 x.
- Accepted by benchmark agreement gate: yes.
- Stored stars: 64 reference / 64 moving.
- Triangle descriptors: 341 reference / 335 moving.
- Inliers: 47.
- Translation delta versus astroalign: 0.2950585644029536 px.
- Output RMS difference versus astroalign apply: 38.265417569300666 ADU.
- `best_glass_cuda_alignment_vs_astroalign.strict_matrix_and_output_best`:
  `glass_cuda_triangle_descriptor_similarity`.

The preceding v46 artifact is retained as a diagnostic negative case: without
grid-top selection, the triangle descriptor path scanned too few candidates,
stored only 10/10 stars, and failed agreement.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Known Limitations

- This is still a two-frame registration benchmark, not the final 200-light
  end-to-end WBPP-like run.
- The accepted triangle path is standalone-array based; resident-stack
  triangle descriptor execution is still pending.
- Triangle descriptors can remain ambiguous on some fields. Quad/pentagon
  descriptors are still the planned stronger model.
- The benchmark checks agreement against astroalign, not PixInsight
  StarAlignment internals.

## Next Step

Promote the accepted grid-top triangle descriptor path into the resident
high-VRAM registration pipeline, then run a multi-frame registration subset
before the final 200-light integration benchmark.

## Clean-room Compliance

Compliant. This checkpoint uses GLASS-owned CUDA code, the MIT-licensed
astroalign package as an open-source comparison target, and user-generated local
M38 artifacts. No PixInsight/WBPP/PJSR source code was read, copied, summarized,
or modified.
