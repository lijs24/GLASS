# S2-Gate443 Status: Resident Guarded-Auto Default Path

## Gate

S2-Gate443

## Result

Passed. Resident CUDA `glass run` and `glass audit` now resolve an omitted
`--resident-fits-read-mode` to guarded `auto`. The default route is auditable in
`run_timing.json` and resident I/O artifacts, and explicit
`--resident-fits-read-mode astropy` remains the compatibility escape hatch.

## Completed Work

- Added CLI default-resolution helper for resident FITS read mode.
- Changed run/audit argparse default for `--resident-fits-read-mode` from
  hard-coded `astropy` to an explicit default-resolution step.
- Default resident CUDA behavior now resolves to:
  - `requested=null`;
  - `effective=auto`;
  - `source=resident_cuda_guarded_auto_default`;
  - `escape_hatch=--resident-fits-read-mode astropy`.
- Passed the FITS read-mode resolution into resident CUDA.
- Recorded `fits_read_mode_resolution` in:
  - `run_timing.json`;
  - `resident_io_overlap`;
  - `resident_light_pipeline_profile` input;
  - `resident_io_pipeline`.
- Extended `glass resident-fits-auto-regression` with
  `--expected-resolution-source`.
- Added tests proving default guarded-auto routing and explicit astropy
  preservation.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m py_compile src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\report\resident_fits_auto_regression.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\report\resident_fits_auto_regression.py tests\test_resident_cuda_run.py tests\test_resident_fits_auto_regression.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_fits_auto_regression.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto tests\test_resident_cuda_run.py::test_cli_resident_cuda_explicit_astropy_fits_read_mode_is_preserved tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953`
- `.\.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200 --out C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200\report.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_vs_gate440_explicit.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_vs_gate438_astropy.html`
- `.\.venv\Scripts\python.exe -m glass.cli resident-fits-auto-regression --run C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200 --explicit-run C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129 --control-run C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148 --compare-explicit C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_vs_gate440_explicit.json --compare-control C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_vs_gate438_astropy.json --out runs\checkpoints\s2_gate_443_default_guarded_auto_regression.json --markdown runs\checkpoints\s2_gate_443_default_guarded_auto_regression.md --min-lights 200 --expected-active 193 --expected-masked 7 --expected-unknown-zero-weight 0 --expected-resolution-source resident_cuda_guarded_auto_default --fail-on-failure`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_443_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests and CLI smoke: `41 passed in 5.55s`
- Ruff focused files: passed
- Full suite: `1047 passed in 39.28s`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension: loaded
- Doctor artifact: `runs/checkpoints/s2_gate_443_cuda_doctor.json`

## Real 200-Light Validation

Run:
`C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200`

Default route:

- Command omitted `--resident-fits-read-mode`.
- Resolution source: `resident_cuda_guarded_auto_default`
- Requested mode before resolution: `null`
- Effective requested mode after resolution: `auto`
- Effective resident group backend: `native_u16_gpu`
- Backend counts: `native_u16be_raw=200`
- Checked frames: 200
- Eligible frames: 200
- Raw H2D bytes: 24,660,480,000
- Avoided float32 host staging bytes: 49,320,960,000

Timing summary:

| Path | Total s | Light read/upload/calibrate s | Read wait s | Worker read cumulative s | Native H2D+cal s | Registration warp s | Integration s | Output write s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gate438 astropy control | 17.288 | 6.625 | 3.939 | 37.972 | 1.958 | 1.638 | 0.288 | 2.251 |
| Gate440 explicit native_u16_gpu | 13.939 | 3.502 | 2.268 | 20.659 | 0.732 | 1.641 | 0.292 | 2.218 |
| Gate443 default guarded auto | 14.196 | 3.529 | 2.260 | 20.742 | 0.755 | 1.634 | 0.288 | 2.433 |

Numerical agreement:

- Gate443 default vs Gate440 explicit native-u16-GPU:
  `rms_diff=0`, `relative_rms_diff=0`, `max_abs_diff=0`, `abs_diff_p999=0`.
- Gate443 default vs Gate438 astropy control:
  `rms_diff=0`, `relative_rms_diff=0`, `max_abs_diff=0`, `abs_diff_p999=0`.

DQ/mask contract:

- Active frames: 193
- Masked frames: 7
- Unknown zero-weight frames: 0
- DQ pixel closure: passed
- Regression audit: passed
- Failed checks: none

## Artifacts

- CUDA doctor JSON: `runs/checkpoints/s2_gate_443_cuda_doctor.json`
- Regression audit JSON:
  `runs/checkpoints/s2_gate_443_default_guarded_auto_regression.json`
- Regression audit Markdown:
  `runs/checkpoints/s2_gate_443_default_guarded_auto_regression.md`
- Run report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_guarded_auto_warm_20260619_235200\report.html`
- Compare vs Gate440 explicit:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_vs_gate440_explicit.html`
- Compare vs Gate438 astropy:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate443_default_vs_gate438_astropy.html`

## Known Limitations

- This gate changes resident CUDA CLI default routing, not image math.
- The default route is still guarded. Unsupported or mixed data should fall
  back through `auto`, and explicit `astropy` remains available.
- The default change applies to resident CUDA run/audit paths. CPU/tile paths
  do not use resident FITS read mode.
- The next gate should harden the fallback matrix so default behavior stays
  safe for incompatible FITS shapes and CPU/tile paths.

## Next Step

S2-Gate444 should validate the default fallback compatibility matrix with
small synthetic fixtures: default resident CUDA on compatible data should select
raw-u16 GPU, default resident CUDA on incompatible simple FITS should fall back
with reasons, explicit astropy should be preserved, and CPU/tile paths should
remain unaffected.

## Source Boundary

This gate used GLASS source code, GLASS-generated artifacts, public FITS/runtime
semantics, and user-owned real benchmark outputs. It did not read or derive code
from official PixInsight/WBPP/PJSR source.
