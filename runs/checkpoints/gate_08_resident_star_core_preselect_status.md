# Gate 08 Resident Star-Core Preselection Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Added production resident CUDA star-core seed preselection for `similarity_cuda_catalog`.
- Added production resident CUDA star-core final seed guard after pixel refinement.
- Added CLI flag `--resident-star-core-preselect-top-k`.
- Recorded `star_core_preselect_top_k` and `star_core_guard` in `resident_artifacts.json`.
- Added direct tests for the production seed preselection and guarded seed selection helpers.
- Updated the resident similarity CUDA smoke test to exercise GPU star-core preselection and guard.
- Ran a real full-resolution two-light M38 validation with resident grid-top-NMS catalog matching plus star-core preselection.

## Commands run
- `.venv\Scripts\python -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair tests/test_gpu_registration_search.py::test_resident_stack_star_core_candidate_metrics_match_cpu`
- `.venv\Scripts\python -m pytest -q tests/test_resident_cuda_run.py tests/test_gpu_registration_search.py tests/test_gpu_star_detect.py`
- `.venv\Scripts\python -m pytest -q`
- `.venv\Scripts\gpwbpp.exe run --plan C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_pair_grid96\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_pair_grid96_starcore8_v2 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 0 --resident-star-max-candidates 96 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 24 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior ncc --resident-star-prior-radius-px 4 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id LIGHT_H_0001`

## Test results
- Targeted resident similarity + star-core metric tests: `2 passed in 0.26s`.
- Resident/CUDA registration affected suite: `45 passed in 0.83s`.
- Full test suite: `149 passed in 7.34s`.

## Real-data validation
- Input plan: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_pair_grid96\processing_plan.json`
- Output run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_similarity_catalog_pair_grid96_starcore8_v2`
- Frames: `S000021` reference and `S000022` moving, shape `6422x9600`.
- Resident registration mode: `similarity_cuda_catalog`.
- Catalog selector: `resident_grid_top_nms`.
- Star max candidates: `96`.
- Similarity top-k: `32`.
- Star-core preselect top-k: `8`.
- Moving frame result:
  - status: `ok`
  - inliers: `64`
  - fit RMS: `0.8003756403923035 px`
  - resident matrix translation: `(1.33740234375, -0.60546875)`
  - astroalign reference translation for this adjacent pair: `(1.2814144144840611, -0.28484174701270604)`
  - translation delta vs astroalign: `0.3254786064676171 px`
  - pixel NCC: `0.976692`
  - star-core pre-refine metric elapsed: `0.09353089996147901 s`
  - star-core guard metric elapsed: `0.09516560001065955 s`
  - total resident run elapsed: `50.35254420002457 s`

## CUDA availability
- CUDA available: yes.
- Native backend loaded: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

## Known limitations
- Star-core preselection now reduces candidate matrices before pixel refinement, but the catalog similarity fit and seed orchestration still return compact metadata through Python.
- This checkpoint validates the new path on a two-frame real pair; the next validation should use a 12-light subset, then 50-light, before returning to the 200-light benchmark.
- `registration_results.json` still stores detailed resident diagnostics as warning strings; a structured diagnostics object remains desirable before long production runs.
- Affine/homography resident fitting remains future work.

## Next step
- Run a 12-light real resident `similarity_cuda_catalog` subset with `--resident-star-core-preselect-top-k 8` and inspect failed/slow frames before scaling to the final 200-light comparison.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- The work uses GPWBPP's own CUDA kernels and clean-room catalog/pixel metric registration logic.
