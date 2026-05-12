# Gate 08 Increment: Optional Astroalign Registration Backend

Date: 2026-05-13

## Gate

Gate 08 / registration increment.

## Completed Content

- Added an optional open-source `astroalign` registration backend for tile-mode GPWBPP runs.
- Added `gpwbpp.cpu.registration.estimate_astroalign_transform(...)`.
- Added `gpwbpp run --registration-method astroalign`.
- The backend:
  - calls `astroalign.find_transform` on GPWBPP streaming preview images;
  - records the resulting similarity matrix;
  - records matched control-point count and RMS;
  - records `registration_solution_source=open_source_astroalign_preview`;
  - records MIT-license provenance in `registration_results.json`.
- Added tests for:
  - direct astroalign similarity/translation recovery;
  - end-to-end registration stage output using `method="astroalign"`.
- Updated `docs/registration_model.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\cpu\registration.py src\gpwbpp\engine\registration.py src\gpwbpp\cli.py tests\test_cpu_registration.py
```

Result: `All checks passed!`

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_cli_smoke.py tests\test_pipeline_fixture.py
```

Result: `23 passed in 4.08s`

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `112 passed in 6.23s`

```powershell
.\.venv\Scripts\gpwbpp.exe run --help
```

Result: help includes `--registration-method {auto,star,astroalign}`.

## Open-Source Dependency

- Package: `astroalign`
- Installed version in this environment: `2.6.2`
- License reported by package metadata: `MIT License`
- `pyproject.toml` already exposes this as optional extra `gpwbpp[align]`.

## CUDA Availability

CUDA is available in the environment, but this increment is a CPU/open-source registration baseline.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB

## Known Limitations

- This is not yet the final GPU star/affine registration implementation.
- The tile-mode warp stage currently consumes only the translation terms from the registration matrix. Astroalign's non-translation similarity terms are recorded for audit, but are not yet fully used by integration.
- The backend depends on optional `astroalign`; CPU-only installs without `gpwbpp[align]` still work with `auto`/`star`.
- Resident high-VRAM mode still uses the existing resident NCC/star-catalog CUDA paths and does not call astroalign.

## Next Step

Add a general affine/similarity warp path, then port the useful star/asterism/descriptor pieces toward resident GPU execution so the resident pipeline can move beyond translation-only registration.

## Clean-Room Compliance

Compliant. This increment uses the public open-source `astroalign` package as an optional dependency and records provenance. It does not read, copy, summarize, or modify PixInsight/WBPP/PJSR source code.
