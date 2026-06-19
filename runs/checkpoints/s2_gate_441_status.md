# S2-Gate441 Status: Guarded Compatible Raw-GPU FITS Auto Path

## Gate

S2-Gate441

## Result

Passed. Resident `--resident-fits-read-mode auto` now performs a per-light-group
header-only compatibility check and promotes the Gate440 compact raw-u16 GPU
decode path only when every light frame in the group is eligible and resident
runtime scheduling supports callback-release batch calibration.

The public conservative default remains `--resident-fits-read-mode astropy`.

## Completed Work

- Added `native_u16_gpu_fits_eligibility` in `src/glass/io/fits_fast.py`.
- Added resident group-level guarded selection before light prefetch.
- Preserved explicit `fast`, `native_direct`, and `native_u16_gpu` behavior.
- Added artifact fields:
  - `fits_read_mode_requested`
  - `fits_read_mode_effective`
  - `resident_fits_auto_selection`
- Added fallback reason counts and ineligible sample records for mixed or
  unsupported groups.
- Updated CLI help, Phase 2 hardening docs, and algorithm source ledger.
- Added synthetic tests for compatible auto promotion and incompatible fallback.

## Commands Run

- `.\.venv\Scripts\python.exe -m py_compile src\glass\io\fits_fast.py src\glass\engine\resident_cuda.py src\glass\cli.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_uses_planner_matching_master_sets tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_uses_planner_matching_master_sets tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_direct_fits_backend tests\test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\io\fits_fast.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_fits_io.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953 --resident-fits-read-mode auto`
- `.\.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900 --out C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\report.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\gate441_auto_vs_gate440_explicit.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\gate441_auto_vs_gate438_astropy.html`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_441_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

Corrected command attempts:

- `glass compare --gpwbpp ...` was rejected because the current CLI requires
  `--glass`.
- A compare attempt using `master_light_H.fits` was rejected because the
  resident output file is `resident_master_H.fits`.
- Both were corrected and the final compare commands passed.

## Test Results

- Initial focused set: `14 passed in 0.90s`
- Expanded focused set: `15 passed in 1.09s`
- CLI smoke: `30 passed in 5.31s`
- Ruff focused files: passed
- Full suite: `1037 passed in 38.68s`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension: loaded
- Doctor artifact: `runs/checkpoints/s2_gate_441_cuda_doctor.json`

## Real 200-Light Validation

Run:
`C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900`

Guarded auto selection:

- Requested mode: `auto`
- Effective mode: `native_u16_gpu`
- Checked frames: 200
- Eligible frames: 200
- Ineligible samples: none
- Backend counts: `native_u16be_raw=200`
- Raw GPU decode enabled: true
- Raw H2D bytes: 24,660,480,000
- Avoided float32 host staging bytes: 49,320,960,000

Timing summary:

| Path | Total s | Light read/upload/calibrate s | Read wait s | Worker read cumulative s | Native H2D+cal s | Registration warp s | Integration s | Output write s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gate438 astropy control | 17.288 | 6.625 | 3.939 | 37.972 | 1.958 | 1.638 | 0.288 | 2.251 |
| Gate440 explicit native_u16_gpu | 13.939 | 3.502 | 2.268 | 20.659 | 0.732 | 1.641 | 0.292 | 2.218 |
| Gate441 auto -> native_u16_gpu | 14.272 | 3.546 | 2.293 | 20.719 | 0.751 | 1.638 | 0.297 | 2.439 |

Numerical agreement:

- Gate441 auto vs Gate440 explicit native-u16-GPU:
  `rms_diff=0`, `relative_rms_diff=0`, `max_abs_diff=0`, `abs_diff_p999=0`.
- Gate441 auto vs Gate438 astropy control:
  `rms_diff=0`, `relative_rms_diff=0`, `max_abs_diff=0`, `abs_diff_p999=0`.

DQ/mask contract:

- Active frames: 193
- Masked frames: 7
- Unknown zero-weight frames: 0
- DQ pixel closure: passed
- Sample accounting closure: passed

## Artifacts

- Summary JSON: `runs/checkpoints/s2_gate_441_guarded_auto_u16_gpu_summary.json`
- CUDA doctor JSON: `runs/checkpoints/s2_gate_441_cuda_doctor.json`
- Run report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\report.html`
- Compare vs Gate440 explicit:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\gate441_auto_vs_gate440_explicit.html`
- Compare vs Gate438 astropy:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\gate441_auto_vs_gate438_astropy.html`
- Resident artifacts:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\resident_artifacts.json`
- DQ closure:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate441_auto_u16_gpu_warm_20260619_225900\resident_dq_pixel_closure.json`

## Known Limitations

- The auto promotion is intentionally narrow and applies only to simple
  primary FITS lights matching `BITPIX=16`, `BSCALE=1`, `BZERO=32768`, and no
  `BLANK`.
- The runtime guard requires callback-release batch calibration. If the runtime
  preset or CUDA build cannot support it, `auto` falls back to the previous
  compatible path.
- `astropy` remains the default. This gate does not promote raw-u16 GPU decode
  as the default for all users.
- The guard checks light frames only. Calibration masters still follow the
  existing resident master-cache and calibration paths.

## Next Step

S2-Gate442 should repeat or formalize the real guarded-auto benchmark envelope:

- keep `auto -> native_u16_gpu` on the 200-light dataset;
- enforce zero-diff against the explicit raw-u16 path;
- preserve DQ closure;
- decide whether the guarded auto path becomes the recommended benchmark mode
  for resident runs while keeping `astropy` available as a conservative
  compatibility default.

## Source Boundary

This gate used GLASS source code, public FITS header semantics, local synthetic
fixtures, and user-owned real benchmark outputs. It did not read or derive code
from official PixInsight/WBPP/PJSR source.
