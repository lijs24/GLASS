# Gate 11 Resident Rejection Status

Gate: 11 (weighted integration + rejection, resident CUDA partial)

Completed:

- Added `ResidentCalibratedStack.integrate_sigma_clip(...)` to the native CUDA
  backend.
- Implemented two-pass per-pixel mean/std sigma clipping and winsorized
  sigma clipping for frames already resident in VRAM.
- Added output weight, coverage, low rejection, and high rejection maps.
- Wired resident CLI runs to accept `--integration-rejection sigma_clip` and
  `--integration-rejection winsorized_sigma`.
- Added resident CUDA unit tests against a CPU reference for sigma clipping and
  winsorized clipping.
- Ran a 200-light M38 H resident CUDA winsorized run.
- Ran a diagnostic 200-light M38 H resident CUDA winsorized run with
  `flat_floor=0.05`, matching the WBPP black-box log evidence for
  `flatScaleClippingFactor=0.05`.

Commands run:

```powershell
.\.venv\Scripts\cmake.exe --build build\native-cuda --config Release
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_gpu_integration_vs_cpu.py
.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_winsorized_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none
.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan_flatfloor005.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_winsorized_flatfloor005_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_winsorized_flatfloor005_run\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\gpwbpp_runs\final_m38_h_200\winsorized_flatfloor005_scaled_resident_vs_wbpp_compare.html --gpwbpp-time-seconds 64.94495560001815 --reference-time-seconds 1092.541 --gpwbpp-label GPWBPP-resident-winsorized-flatfloor005-scaled --reference-label PixInsight-WBPP-fastIntegration --gpwbpp-scale 0.000015259021896696421 --clip-low 0 --clip-high 1
.\.venv\Scripts\python.exe -m pytest -q
```

Test results:

- Targeted resident CUDA tests: 7 passed.
- Full test suite: 73 passed in 5.56 s.

CUDA availability:

- CUDA native backend available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.

Real-data results:

- M38 H 200-light + 20/20/20 calibration frames completed.
- Resident winsorized run with default `flat_floor=1e-6`: 64.0809652999742 s.
- Resident winsorized diagnostic run with `flat_floor=0.05`: 64.94495560001815 s.
- WBPP black-box reference: 1092.541 s.
- Speedup for the `flat_floor=0.05` diagnostic run: 16.82x.

Observed image behavior:

- Raising `flat_floor` to 0.05 removed `gt_65535` pixels in the resident
  integrated output and reduced the p999 output value from ~60013 ADU to
  ~621 ADU.
- Scaled GPWBPP-vs-WBPP comparison for the diagnostic run reached median
  absolute difference around `1.17e-4`, but RMS remains high due to missing
  WBPP-equivalent alignment, exact rejection, cosmetic correction, and WBPP's
  193/200 integrated-frame policy.

Known limitations:

- Rejection is mean/std based; it is not yet WBPP FastIntegration's exact
  robust rejection.
- Resident mode still lacks internal alignment/warp and failed-alignment frame
  rejection.
- The `flat_floor=0.05` run is a diagnostic plan copy, not yet a first-class
  CLI calibration policy override.

Next step:

- Add resident alignment/warp or a FastIntegration-compatible registration
  stage, then rerun the same M38 200-light comparison.

Clean-room status:

- Compliant. WBPP behavior was inferred only from user-generated logs and
  outputs.
