# Gate 08 Increment: CUDA Catalog Tile Registration Stage

Date: 2026-05-13

## Completed contents

- Added explicit tile-mode registration method `cuda_catalog`.
- Wired `gpwbpp run --registration-method cuda_catalog` and
  `gpwbpp audit --registration-method cuda_catalog`.
- The new method builds the existing streaming registration previews, requires
  the native CUDA backend, selects compact star catalogs on GPU, estimates a
  similarity transform with the CUDA mutual catalog scorer, optionally uses a
  CUDA NCC prior, and refines translation terms with CUDA pixel metrics.
- The preview transform is scaled back to source-image pixels before being
  written to `registration_results.json`, so the existing streaming matrix warp
  can consume it.
- Each moving-frame row records `cuda_catalog` diagnostics: thresholds,
  catalog counts, prior details, preview RMS, candidate/refit metadata, and
  pixel metric RMS/NCC.
- Updated registration documentation and capability reporting.

## Commands run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_cli_smoke.py tests\test_pipeline_fixture.py tests\test_cpu_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `.\.venv\Scripts\python.exe -m gpwbpp.cli synthetic --out runs\cuda_catalog_cli_smoke_data --frames 4 --width 96 --height 96 --known-shift`
- `.\.venv\Scripts\python.exe -m gpwbpp.cli scan --root runs\cuda_catalog_cli_smoke_data --out runs\cuda_catalog_cli_smoke_manifest.json`
- `.\.venv\Scripts\python.exe -m gpwbpp.cli plan --manifest runs\cuda_catalog_cli_smoke_manifest.json --out runs\cuda_catalog_cli_smoke_plan.json`
- `.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan runs\cuda_catalog_cli_smoke_plan.json --out runs\cuda_catalog_cli_smoke_run --backend cuda --until-stage registration --tile-size 32 --registration-method cuda_catalog --registration-preview-max-dimension 128`

## Test results

- CUDA registration tests: `20 passed in 0.28s`
- CLI smoke tests: `3 passed in 0.22s`
- Pipeline fixture tests: `12 passed in 3.77s`
- CPU registration tests: `10 passed in 0.44s`
- Combined targeted set: `45 passed in 4.12s`
- Full suite: `135 passed in 7.21s`
- `git diff --check`: passed, with only Windows LF-to-CRLF warnings.

## CLI smoke result

- Synthetic input: `runs\cuda_catalog_cli_smoke_data`
- Run output: `runs\cuda_catalog_cli_smoke_run`
- `registration_results.json` summary:
  - `method`: `cuda_catalog`
  - `transform_model`: `similarity`
  - `registration_solution_source`: `cuda_catalog_similarity_preview`
  - statuses: `ok`, `reference`
  - CUDA diagnostic rows: `3`

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97,886 MiB

## Known limitations

- This integrates the accepted GPU catalog path into the tile-mode registration
  stage, but the pixel-refinement loop is still CPU-orchestrated over CUDA
  metric kernels.
- The CLI smoke validates a small synthetic set; full 200-light real-data
  registration and integration still need a separate run.
- `cuda_catalog` is explicit opt-in. `auto` still uses the existing CPU
  clean-room star matcher and phase-correlation fallback.
- The method uses bounded previews in tile mode. The all-resident high-VRAM
  version remains a later optimization.

## Next step

- Run `cuda_catalog` registration across a larger real subset and then wire the
  accepted matrix path into the resident high-VRAM registration/integration
  flow for the 200-light benchmark.

## Clean-room compliance

- This increment used only GPWBPP code and open, generic image-registration
  techniques already present in the project.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- Original data directories were not modified.
