# Gate 08 CUDA triangle pipeline entry status

Date: 2026-05-13 14:35:24 +08:00

## Gate

Gate 08: Registration

## Completed

- Added `--registration-method cuda_triangle` to tile-mode `glass run` and
  `glass audit`.
- Promoted the existing CUDA triangle descriptor registration helper into the
  formal streaming-preview registration pipeline.
- Added native CUDA primitive checks for triangle-descriptor registration.
- Wrote source-pixel similarity matrices and compact `cuda_triangle`
  diagnostics to `registration_results.json`.
- Added a CUDA regression test for `register_calibrated_frames(...,
  method="cuda_triangle")`.
- Updated registration and CUDA backend documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\registration.py src\glass\cli.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "import glass_cuda,json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, ensure_ascii=False, indent=2))"
.\.venv\Scripts\glass.exe run --help | Select-String -Pattern "cuda_triangle|registration-method"
.\.venv\Scripts\glass.exe audit --help | Select-String -Pattern "cuda_triangle|registration-method"
git diff --check
```

## Test Results

- Ruff: passed.
- Targeted GPU registration tests: `30 passed in 0.27s`.
- Full pytest suite: `158 passed in 7.37s`.
- CLI help confirms `cuda_triangle` is available for `run` and `audit`.
- `git diff --check`: no whitespace errors; Git reported only LF-to-CRLF
  working-copy warnings.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Known Limitations

- The new `cuda_triangle` method currently estimates a similarity matrix on
  bounded streaming previews, then lets the existing streaming warp consume the
  matrix. It is not yet the final all-resident, all-frame, high-VRAM execution
  mode.
- The path uses triangle similarity descriptors. Quad/polygon descriptors and
  homography/local-distortion models remain future work.
- Preview registration still uses bilinear matrix warp for diagnostics; final
  WBPP-like output matching will need GPU Lanczos/clamping support.
- This checkpoint does not run the final 200-light WBPP comparison.

## Next Step

Run a multi-frame registration subset with `--registration-method
cuda_triangle`, then bridge the descriptor path into the resident high-VRAM
pipeline so calibrated frames can remain in VRAM through warp/integration.

## Clean-room Compliance

Compliant. The implementation uses GLASS-owned CUDA/Python code and public
algorithmic behavior. No PixInsight/WBPP/PJSR source code was read, copied,
summarized, or modified.
