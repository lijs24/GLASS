# Gate 09 Resident CUDA Lanczos3 Warp Status

## Gate

Gate 09 sub-checkpoint: resident CUDA warp interpolation support.

## Completed Content

- Added a clean-room CUDA Lanczos3 matrix warp kernel with optional local clamping threshold.
- Exposed `warp_matrix_lanczos3_f32` in the native `glass_cuda` binding.
- Exposed `ResidentCalibratedStack.apply_matrix_lanczos3_frame` for in-place resident GPU warping.
- Added resident pipeline CLI options:
  - `--resident-warp-interpolation {bilinear,lanczos3}`
  - `--resident-warp-clamping-threshold`
- Recorded resident warp interpolation and clamp threshold in resident artifacts.
- Added CPU fallback/reference Lanczos3 warp tests and resident stack tests.
- Documented the CUDA backend and registration model updates.

## Commands Run

```powershell
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "<repo>\.venv\Scripts\cmake.exe" --build "<repo>\build\native-cuda"'
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_gpu_warp_vs_cpu.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Targeted CUDA/resident tests: `20 passed in 3.01s`.
- Full test suite: `161 passed in 7.56s`.

## Real-data Subset Validation

Command:

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8_fixed350\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_fixed350" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_fixed350" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_fixed350\report.html"
```

Results:

- Output: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_fixed350`.
- Total elapsed: `17.932113399961963 s`.
- Registration statuses: 11 ok, 1 reference, 0 failed.
- Artifact records: `resident_registration.warp_interpolation = lanczos3`.
- Artifact records: `resident_registration.warp_clamping_threshold = 0.3`.
- Estimated peak memory: `4.134035155177116 GiB`.
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_fixed350\report.html`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Multiprocessors: 188.

## Known Limitations

- The Lanczos3 warp is implemented as a matrix warp primitive and resident frame operation. Full large-frame WBPP parity timing should still be rerun before replacing bilinear in the primary benchmark path.
- The clamping threshold is a clean-room local support clamp intended for WBPP-like comparison experiments, not a claim of PixInsight internal equivalence.
- The resident full-chain benchmark still uses GLASS's own registration and integration choices; PixInsight differences remain expected around star matching, rejection details, normalization, and output scaling.

## Next Step

- Run a small real-data resident Lanczos3 validation subset, then evaluate whether the 193-frame WBPP-failed-excluded benchmark should be repeated with `--resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30`.

## Clean-room Compliance

- Compliant. This change uses general public Lanczos resampling mathematics, native CUDA implementation, synthetic tests, and black-box WBPP output/log comparisons only.
- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or reimplemented.
