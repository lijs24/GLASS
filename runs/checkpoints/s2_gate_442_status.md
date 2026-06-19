# S2-Gate442 Status: Guarded Auto Real 200-Light Regression

## Gate

S2-Gate442

## Result

Passed. This gate adds a machine-readable regression audit for the resident
guarded FITS auto path and re-runs the real M38 H 200-light warm-cache benchmark
with `--resident-fits-read-mode auto`.

The audit proves that `auto` selected `native_u16_gpu`, all 200 light frames
were eligible for raw-u16 GPU decode, output remained bitwise identical to both
the explicit raw-u16 GPU path and the astropy control path, and the timing
envelope stayed clearly faster than the astropy control.

## Completed Work

- Added `src/glass/report/resident_fits_auto_regression.py`.
- Added CLI command `glass resident-fits-auto-regression`.
- Added regression checks for:
  - requested/effective FITS read mode;
  - raw-u16 GPU eligibility and backend selection;
  - DQ/frame-mask closure;
  - compare JSON numerical parity;
  - total runtime and light read/upload/calibrate timing envelopes.
- Added `tests/test_resident_fits_auto_regression.py`.
- Added CLI smoke coverage for the new command.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m py_compile src\glass\report\resident_fits_auto_regression.py src\glass\cli.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_fits_auto_regression.py src\glass\cli.py tests\test_resident_fits_auto_regression.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_fits_auto_regression.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953 --resident-fits-read-mode auto`
- `.\.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000 --out C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\report.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\gate442_auto_vs_gate440_explicit.html`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\gate442_auto_vs_gate438_astropy.html`
- `.\.venv\Scripts\python.exe -m glass.cli resident-fits-auto-regression --run C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000 --explicit-run C:\glass_runs\final_m38_h_200\glass_s2_gate440_native_u16_gpu_warm_20260619_223129 --control-run C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148 --compare-explicit C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\gate442_auto_vs_gate440_explicit.json --compare-control C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\gate442_auto_vs_gate438_astropy.json --out runs\checkpoints\s2_gate_442_guarded_auto_regression.json --markdown runs\checkpoints\s2_gate_442_guarded_auto_regression.md --min-lights 200 --expected-active 193 --expected-masked 7 --expected-unknown-zero-weight 0 --fail-on-failure`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_442_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests and CLI smoke: `37 passed in 5.15s`
- Ruff focused files: passed
- Full suite: `1044 passed in 38.80s`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- CUDA native extension: loaded
- Doctor artifact: `runs/checkpoints/s2_gate_442_cuda_doctor.json`

## Real 200-Light Validation

Run:
`C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000`

Guarded auto selection:

- Requested mode: `auto`
- Effective mode: `native_u16_gpu`
- Checked frames: 200
- Eligible frames: 200
- Backend counts: `native_u16be_raw=200`
- Raw H2D bytes: 24,660,480,000
- Avoided float32 host staging bytes: 49,320,960,000

Timing summary:

| Path | Total s | Light read/upload/calibrate s | Read wait s | Worker read cumulative s | Native H2D+cal s | Registration warp s | Integration s | Output write s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gate438 astropy control | 17.288 | 6.625 | 3.939 | 37.972 | 1.958 | 1.638 | 0.288 | 2.251 |
| Gate440 explicit native_u16_gpu | 13.939 | 3.502 | 2.268 | 20.659 | 0.732 | 1.641 | 0.292 | 2.218 |
| Gate442 auto -> native_u16_gpu | 14.171 | 3.519 | 2.273 | 20.704 | 0.745 | 1.636 | 0.296 | 2.406 |

Numerical agreement:

- Gate442 auto vs Gate440 explicit native-u16-GPU:
  `rms_diff=0`, `relative_rms_diff=0`, `max_abs_diff=0`, `abs_diff_p999=0`.
- Gate442 auto vs Gate438 astropy control:
  `rms_diff=0`, `relative_rms_diff=0`, `max_abs_diff=0`, `abs_diff_p999=0`.

DQ/mask contract:

- Active frames: 193
- Masked frames: 7
- Unknown zero-weight frames: 0
- DQ pixel closure: passed
- Sample accounting closure: passed

Regression audit:

- Artifact: `runs/checkpoints/s2_gate_442_guarded_auto_regression.json`
- Markdown: `runs/checkpoints/s2_gate_442_guarded_auto_regression.md`
- Status: passed
- Failed checks: none

## Artifacts

- CUDA doctor JSON: `runs/checkpoints/s2_gate_442_cuda_doctor.json`
- Regression audit JSON: `runs/checkpoints/s2_gate_442_guarded_auto_regression.json`
- Regression audit Markdown: `runs/checkpoints/s2_gate_442_guarded_auto_regression.md`
- Run report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\report.html`
- Compare vs Gate440 explicit:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\gate442_auto_vs_gate440_explicit.html`
- Compare vs Gate438 astropy:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate442_auto_u16_gpu_warm_20260619_232000\gate442_auto_vs_gate438_astropy.html`

## Known Limitations

- This gate adds a regression audit and does not change image math.
- The audit's default expected frame counts are tuned for the M38 H 200-light
  benchmark; other datasets should pass explicit expected counts.
- The guarded auto path still only promotes raw-u16 GPU decode for simple
  primary FITS lights matching `BITPIX=16`, `BSCALE=1`, `BZERO=32768`, and no
  `BLANK`.
- The public default read mode remains `astropy` in this gate.

## Next Step

S2-Gate443 should move from proven benchmark mode toward default runtime
behavior: make resident CUDA use guarded `auto` FITS reading by default when the
user does not explicitly choose a read mode, while preserving explicit
`astropy` and all other reader modes as escape hatches. It must re-run synthetic
fallback tests and the real 200-light benchmark.

## Source Boundary

This gate used GLASS source code, GLASS-generated artifacts, public FITS/runtime
semantics, and user-owned real benchmark outputs. It did not read or derive code
from official PixInsight/WBPP/PJSR source.
