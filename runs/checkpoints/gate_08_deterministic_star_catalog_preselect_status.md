# Gate 08 Incremental Status: Deterministic CUDA Star Catalog and Resident Preselection

Date: 2026-05-13

## Gate

Gate 8: Registration, incremental checkpoint for stable GPU star-catalog candidate generation and faster resident CUDA alignment refinement.

## Completed

- Fixed nondeterministic CUDA star-candidate selectors by adding a device memory fence before releasing global-memory spin locks in:
  - `star_candidate_topn_kernel`
  - `star_candidate_grid_kernel`
  - `star_candidate_grid_topk_kernel`
- Verified repeated calls to the same real FITS frame now return identical star catalogs for:
  - `star_top_candidates_f32`
  - `star_top_nms_candidates_f32`
  - `star_grid_top_nms_candidates_f32`
- Added resident GPU star-core preselection before expensive full-frame candidate refinement in the astroalign comparison benchmark.
- Added tests for:
  - repeatability under high star-catalog lock contention;
  - star-core preselection preserving the refit seed and rejecting a low-inlier false candidate.

## Commands

```powershell
cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release"

.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py tests\test_gpu_registration_search.py tests\test_benchmarks.py

.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v45_fenced_top32_preselect16.json" --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 32 --resident-star-core-preselect-top-k 16 --catalog-pixel-refine-radius 1.0 --catalog-pixel-refine-coarse-step 0.25 --catalog-pixel-refine-fine-radius 0.25 --catalog-pixel-refine-fine-step 0.0625 --catalog-pixel-refine-coarse-stride 4 --catalog-pixel-refine-final-stride 1

git diff --check
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `39 passed in 1.65s`
- Full suite: `144 passed in 7.23s`
- `git diff --check`: passed; only Windows CRLF normalization warnings.
- Native CUDA build: passed; CUDA Toolkit emitted Windows codepage warnings from CUDA headers only.

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: available

## Benchmark Result

Artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v45_fenced_top32_preselect16.json`

Input pair:

- reference: `calibrated_S000061.fits`
- moving: `calibrated_S000062.fits`
- shape: `6422 x 9600`

astroalign:

- total: `9.641944 s`

GLASS resident CUDA, `catalog_similarity_top_k=32`, `resident_star_core_preselect_top_k=16`:

- strict matrix + output agreement: passed
- resident algorithm time: `3.249815 s`
- resident device time: `3.153870 s`
- speedup vs astroalign total: `2.967x`
- upload-inclusive speedup vs astroalign total: `2.931x`
- translation delta vs astroalign: `0.248870 px`
- output RMS diff vs astroalign output: `21.902715 ADU`
- selected seed rank: `2`
- selected seed inliers: `47`
- seed count: `33`
- refined seed count after preselection: `16`

## Known Limitations

- This remains a two-frame alignment benchmark, not the final 200-light end-to-end WBPP/GLASS comparison.
- The preselection logic currently lives in the benchmark path; it should be promoted into the production resident registration path after one more synthetic/fixture coverage pass.
- Candidate scoring still uses full-frame metric scans for selected seeds. Further speedup should come from tile/ROI scoring around star cores before final whole-frame validation.

## Next Step

- Move deterministic star-catalog + resident preselected similarity alignment into the production registration stage.
- Add a pipeline fixture that writes `registration_results.json` with per-frame matrix/inlier/RMS/status data using this CUDA path.

## Clean-Room Compliance

Compliant. This work inspected and modified only GLASS project code and used user-provided FITS artifacts plus astroalign as an open-source comparison target. No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
