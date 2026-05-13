# Gate 08 triangle descriptor benchmark wiring status

Date: 2026-05-13 14:23:51 +08:00

## Gate

Gate 08: Registration

## Completed

- Wired the CUDA triangle-descriptor image registration loop into
  `benchmarks/compare_astroalign_gpu_alignment.py`.
- Added benchmark CLI parameters:
  - `--triangle-descriptor-neighbors`
  - `--triangle-descriptor-max-descriptors`
  - `--triangle-descriptor-radius`
- Added JSON report sections for:
  - `gpwbpp_cuda_triangle_descriptor_similarity`
  - `triangle_descriptor_similarity_agreement_vs_astroalign`
  - `direct_output_diff_gpu_triangle_descriptor_similarity_minus_astroalign_apply_on_common_valid_pixels`
  - `triangle_descriptor_similarity_speedup_vs_astroalign`
  - triangle valid/common pixel counts
- Included the triangle-descriptor path in `best_gpwbpp_cuda_alignment_vs_astroalign`.
- Updated `docs/registration_model.md` and `docs/cuda_backend.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --width 128 --height 128 --catalog-stars 32 --catalog-threshold-sigma 4 --catalog-tolerance-px 3 --triangle-descriptor-max-descriptors 256 --out runs\benchmarks\triangle_descriptor_synthetic_smoke.json
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

## Test Results

- Ruff: passed.
- Synthetic benchmark smoke: passed; output artifact written to
  `runs/benchmarks/triangle_descriptor_synthetic_smoke.json` (ignored by Git).
- Targeted GPU registration tests: `28 passed in 0.19s`.
- Full pytest suite: `156 passed in 7.54s`.
- `git diff --check`: no whitespace errors; Git reported only LF-to-CRLF working-copy warnings.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Known Limitations

- The benchmark wiring is validated on the synthetic smoke pair in this checkpoint.
- The calibrated real M38 pair comparison still needs to be rerun with
  `gpwbpp_cuda_triangle_descriptor_similarity`.
- Triangle descriptors remain a bridge toward the stronger PixInsight-like
  polygonal descriptor model; quad/pentagon descriptors are not implemented yet.
- The helper currently uses a single effective threshold:
  `min(reference_threshold, moving_threshold)`.
- This benchmark path is standalone-array based, not yet resident-stack based.

## Next Step

Run the updated astroalign comparison benchmark on the calibrated M38 pair, then
promote the accepted descriptor path into the resident high-VRAM registration
pipeline or extend it toward quad/pentagon descriptors if the real pair exposes
triangle ambiguity.

## Clean-room Compliance

Compliant. This checkpoint uses GPWBPP-owned CUDA code, open-source astroalign as
an external reference, public PixInsight/StarAlignment behavior notes, and
user-generated benchmark outputs only. No PixInsight/WBPP/PJSR source code was
read, copied, summarized, or modified.
