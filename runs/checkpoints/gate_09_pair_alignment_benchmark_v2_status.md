# Gate 09 pair alignment benchmark v2 checkpoint

Date: 2026-05-13

Status: completed incremental Gate 09/registration-warp diagnostic capability. This does not complete the owned GPU star/asterism matcher; it makes the astroalign-vs-GLASS CUDA pair benchmark self-contained for both speed and image-consistency evidence.

## Completed work

- Extended `benchmarks/compare_astroalign_gpu_alignment.py` to retain astroalign's aligned output and valid mask during a run.
- Added direct common-valid-pixel metrics between:
  - astroalign `apply_transform` output
  - GLASS standalone CUDA matrix bilinear warp output using the same astroalign similarity matrix
- Added valid-pixel counts to the benchmark JSON:
  - astroalign valid pixels
  - GLASS CUDA matrix valid pixels
  - common valid pixels
- Added a CUDA/astroalign gated pytest that runs the benchmark on a small synthetic pair and verifies the new direct-difference fields.
- Updated `docs/registration_model.md` with the refreshed full-frame M38 pair benchmark artifact and key numbers.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_compare_astroalign_gpu_alignment_records_direct_diff
```

Result: 1 passed in 0.59 s.

```powershell
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v2.json --max-shift 16 --catalog-grid-cols 4 --catalog-grid-rows 4 --catalog-prior-radius 4
```

Result artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v2.json`

Observed key metrics:

- Image shape: 6422 x 9600.
- Astroalign total: 9.5876 s.
- Astroalign find transform: 6.7791 s.
- Astroalign apply transform: 2.8085 s.
- GLASS standalone CUDA matrix warp from the same matrix: 0.1435 s.
- GLASS resident CUDA matrix warp device-only from the same matrix: 0.0071 s.
- Standalone CUDA matrix warp speedup vs astroalign apply: 19.58x.
- Resident device-only matrix warp speedup vs astroalign apply: 397.44x.
- Common valid pixels: 61,632,460.
- GPU matrix output minus astroalign apply median absolute difference: 3.9833 ADU.
- GPU matrix output minus astroalign apply p99 absolute difference: 22.9403 ADU.
- GPU matrix output minus astroalign apply RMS difference: 12.0167 ADU.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 124 passed in 7.04 s.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GLASS: 97,886 MiB.

## Known limitations

- The benchmark still uses open-source astroalign for the similarity transform search. This is clean-room and useful as an external baseline, but it is not yet GLASS's owned GPU star/asterism matcher.
- GLASS's pure GPU NCC/catalog paths in this benchmark remain translation-only diagnostics.
- Pixel differences include interpolation implementation differences and valid-mask edge differences; the benchmark records them explicitly instead of treating the outputs as bit-identical.
- This checkpoint proves the CUDA matrix warp speed and output agreement for one calibrated M38 pair, not the full 200-frame registration solution.

## Next step

Move from externally supplied similarity matrices toward an owned GPU descriptor/matching path: either integrate a suitable open-source registration algorithm as a reference and port its pixel/catalog-heavy pieces to CUDA, or implement a clean-room GPU descriptor scorer with similarity/affine matrix estimation and acceptance diagnostics.

## Clean-room compliance

Compliant. This work uses GLASS code, the open-source astroalign package as an external reference/backend, and user-generated calibrated data/artifacts. No official WBPP/PJSR source was read or copied.
