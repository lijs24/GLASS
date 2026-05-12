# Gate 08 Increment: Resident NCC Registration Pipeline Mode

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Wired resident GPU NCC plus subpixel refinement into
  `gpwbpp run --memory-mode resident`.
- Added resident registration mode `translation_ncc_subpixel`.
- Added CLI controls:
  - `--resident-registration-max-shift`
  - `--resident-subpixel-radius-steps`
  - `--resident-subpixel-step`
- The resident run now calibrates all light frames into VRAM first, then uses
  `ResidentCalibratedStack.estimate_translation_to_reference(...)`,
  `estimate_translation_subpixel_to_reference(...)`, and
  `apply_translation_bilinear_frame(...)` before resident integration.
- Added CLI smoke coverage for the new resident registration mode.
- Ran an end-to-end synthetic command-chain with three light frames to verify
  non-reference frames are actually registered in the resident pipeline.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\cli.py src\gpwbpp\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py
.\.venv\Scripts\gpwbpp.exe synthetic --out runs\resident_ncc_smoke_data --frames 3 --width 64 --height 64 --filter H --known-shift
.\.venv\Scripts\gpwbpp.exe scan --root runs\resident_ncc_smoke_data --out runs\resident_ncc_smoke\manifest.json
.\.venv\Scripts\gpwbpp.exe plan --manifest runs\resident_ncc_smoke\manifest.json --out runs\resident_ncc_smoke\processing_plan.json
.\.venv\Scripts\gpwbpp.exe run --plan runs\resident_ncc_smoke\processing_plan.json --out runs\resident_ncc_smoke --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration translation_ncc_subpixel --resident-registration-max-shift 8 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Targeted resident CLI/native tests: 12 passed.
- Full pytest: 100 passed.
- Synthetic three-light resident command-chain:
  - scan: 12 frames.
  - plan: executable, 0 warnings.
  - resident run: completed through integration.
  - registration results: reference frame plus two non-reference frames.
  - measured resident translations: `dx=-1` and `dx=-2` for the shifted
    synthetic light frames.
  - failed frame count: 0.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/resident_ncc_smoke_data/`
- `runs/resident_ncc_smoke/manifest.json`
- `runs/resident_ncc_smoke/processing_plan.json`
- `runs/resident_ncc_smoke/registration_results.json`
- `runs/resident_ncc_smoke/integration_results.json`
- `runs/resident_ncc_smoke/resident_artifacts.json`

## Known Limitations

- `translation_ncc_subpixel` is still translation-only and does not provide
  star-match RMS.
- The resident pipeline still skips Local Normalization.
- Registration parameters are global per run; no adaptive per-frame search
  bounds or star-model verification is wired in yet.
- This is a small synthetic command-chain, not the final 200+ light M38
  benchmark.

## Next Step

- Run the resident pipeline on a carefully selected M38 subset with enough
  lights to exercise registration, warp, and integration timing before scaling
  to the final 200+ light comparison.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Original input data directories were not modified.
