# S2-Gate444 Status: Default Fallback Compatibility Matrix

## Gate

S2-Gate444

## Result

Passed. The resident CUDA guarded-auto default now has a compact compatibility
matrix audit proving that the fast raw-u16 path remains guarded and that the
conservative fallback and explicit escape hatch still work.

## Completed Work

- Added `glass resident-fits-default-matrix`.
- Added `src/glass/report/resident_fits_default_matrix.py`.
- Added tests for:
  - matrix pass/fail behavior;
  - matrix CLI JSON/Markdown output and fail-on-failure exit code;
  - actual resident CUDA default fallback on small float32 FITS lights;
  - actual resident CUDA default raw-u16 selection on compatible FITS lights;
  - explicit astropy preservation;
  - CPU/tile paths keeping resident FITS default resolution unused.
- Updated `docs/phase2_algorithm_hardening.md` with Gate444 completion and
  Gate445 StackEngine/DQ next-step scope.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m py_compile src\glass\report\resident_fits_default_matrix.py src\glass\cli.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_fits_default_matrix.py src\glass\cli.py tests\test_resident_fits_default_matrix.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_fits_default_matrix.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_fits_default_matrix.py src\glass\cli.py tests\test_resident_fits_default_matrix.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_fits_default_matrix.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto tests\test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_falls_back_for_float32_group tests\test_resident_cuda_run.py::test_cli_resident_cuda_explicit_astropy_fits_read_mode_is_preserved tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_444_cuda_doctor.json`
- Small synthetic FITS generation under
  `runs/checkpoints/s2_gate_444_matrix_work`.
- `.\.venv\Scripts\python.exe -m glass.cli scan --root runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\data --out runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\manifest.json`
- `.\.venv\Scripts\python.exe -m glass.cli plan --manifest runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\manifest.json --out runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\processing_plan.json`
- `.\.venv\Scripts\python.exe -m glass.cli scan --root runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\data --out runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\manifest.json`
- `.\.venv\Scripts\python.exe -m glass.cli plan --manifest runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\manifest.json --out runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\processing_plan.json`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\processing_plan.json --out runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\run_default --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration off --flat-floor 0.05`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\processing_plan.json --out runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\run_default --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration off --flat-floor 0.05`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\processing_plan.json --out runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\run_explicit_astropy --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration off --resident-fits-read-mode astropy --flat-floor 0.05`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_444_matrix_work\incompatible_float32\processing_plan.json --out runs\checkpoints\s2_gate_444_matrix_work\cpu_tile\run_calibration --backend cpu --memory-mode tile --until-stage calibration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05`
- `.\.venv\Scripts\python.exe -m glass.cli resident-fits-default-matrix --cases runs\checkpoints\s2_gate_444_default_fallback_matrix_cases.json --out runs\checkpoints\s2_gate_444_default_fallback_matrix.json --markdown runs\checkpoints\s2_gate_444_default_fallback_matrix.md --fail-on-failure`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused matrix tests: `5 passed in 0.26s`
- Focused resident/CLI/default tests: `40 passed in 5.74s`
- Full suite: `1054 passed in 40.08s`
- Ruff: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension: loaded
- Doctor artifact: `runs/checkpoints/s2_gate_444_cuda_doctor.json`

## Small Synthetic Validation

Artifact:
`runs/checkpoints/s2_gate_444_default_fallback_matrix.json`

Matrix cases:

| Case | Source | Requested | Effective | Backend | Result |
|---|---|---|---|---|---|
| default_compatible_u16 | resident_cuda_guarded_auto_default | auto | native_u16_gpu | native_u16be_raw=2 | passed |
| default_incompatible_float32 | resident_cuda_guarded_auto_default | auto | auto | fast_simple=2 | passed |
| explicit_astropy_escape_hatch | explicit | astropy | astropy | astropy_scaled_memmap=2 | passed |
| cpu_tile_unaffected | unused_non_resident | n/a | n/a | n/a | passed |

Fallback evidence:

- Compatible u16/BZERO lights: raw-u16 GPU selected, 2/2 eligible, no fallback
  reasons.
- Incompatible float32 lights: raw-u16 GPU not selected, 0/2 eligible,
  fallback reason `bitpix_not_16:-32=2`, bounded `fast_simple` reader used.
- Explicit astropy: raw-u16 GPU disabled and `astropy_scaled_memmap=2`.
- CPU/tile calibration run: no resident artifacts; run timing records
  `source=unused_non_resident`.

## 200-Light Benchmark Note

The 200-light benchmark was not rerun for Gate444. This gate adds an audit
artifact and compatibility tests around Gate443 default routing; it does not
change resident calibration math, registration, warp, rejection, integration,
frame admission, or output pixels. The current 200-light default-path baseline
remains Gate443:
`C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200`.

## Known Limitations

- The matrix audits existing GLASS run artifacts. It does not run image
  processing by itself.
- The raw-u16 GPU path remains deliberately narrow:
  `BITPIX=16`, `BSCALE=1`, `BZERO=32768`, no `BLANK`, shape-matched light
  groups, and compatible resident CUDA scheduling.
- The small matrix input run directories under
  `runs/checkpoints/s2_gate_444_matrix_work` are local diagnostic artifacts and
  are not intended as committed golden data.

## Next Step

S2-Gate445 should return to the core Phase 2 objective: audit and close
StackEngine default-path gaps for master frames and light integration while
preserving the DQ/mask contract and resident CUDA performance baseline.

## Source Boundary

This gate used GLASS source code, GLASS-generated synthetic FITS fixtures,
GLASS-generated run artifacts, and public FITS header semantics. It did not
read or derive code from official PixInsight/WBPP/PJSR source, did not modify
user image directories, and did not create release or publication artifacts.
