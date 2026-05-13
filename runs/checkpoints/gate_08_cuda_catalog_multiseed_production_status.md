# Gate 08 CUDA Catalog Multi-Seed Production Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Promoted the benchmark-proven CUDA catalog top-k seed path into the production `glass.engine.registration` CUDA catalog preview backend.
- Added `registration_policy.cuda_catalog_similarity_top_k` support for `method="cuda_catalog"`.
- When top-k candidates are requested and pixel refinement is enabled, production registration now refines the primary fit plus top-k candidate matrices with `refine_matrix_translation_candidates_with_metrics_f32`.
- Registration artifacts now record `similarity_top_k`, `top_candidate_count`, `top_candidates`, and multi-seed `pixel_refine` diagnostics.
- Default behavior remains compatible: without `cuda_catalog_similarity_top_k`, the existing single-seed pixel refine path is used.

## Commands run
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_gpu_registration_search.py::test_register_calibrated_frames_can_use_cuda_catalog_backend tests/test_gpu_registration_search.py::test_gpu_estimate_similarity_from_catalogs_scores_pair_candidates`
- `.\\.venv\\Scripts\\python -m pytest -q`
- `@' ... '@ | .\\.venv\\Scripts\\python -` to query CUDA capability through `glass_cuda`.

## Test results
- Targeted CUDA registration tests: `2 passed in 0.14s`.
- Full test suite: `144 passed in 6.97s`.

## CUDA availability
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend loaded: yes.

## Known limitations
- This checkpoint productionizes top-k multi-seed refinement for the streaming preview registration stage, not yet a fully resident similarity/affine registration mode inside `ResidentCalibratedStack`.
- Resident CUDA integration can already consume these matrices through `--resident-registration external_matrix`.
- Selection is still based on bounded catalog similarity plus pixel metric refinement; descriptor-based wide-field matching and full affine/homography model selection remain future work.

## Next step
- Wire the produced `cuda_catalog` similarity matrices into a larger resident run as the default high-quality registration path, so full-VRAM calibration/integration no longer depends on external benchmark scripts for similarity matrix generation.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- The implementation uses GLASS code and open, general registration concepts already present in the project.
