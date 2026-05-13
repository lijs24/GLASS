# Gate 08 resident CUDA triangle status

Date: 2026-05-13 14:44:41 +08:00

## Gate

Gate 08: Registration

## Completed

- Added resident CUDA registration mode `similarity_cuda_triangle`.
- Added CLI support through `gpwbpp run --memory-mode resident
  --resident-registration similarity_cuda_triangle`.
- Reused resident GPU star-catalog detection, CUDA triangle descriptor
  construction/matching, optional resident pixel-metric translation refinement,
  and resident in-place matrix bilinear warp.
- Recorded triangle descriptor diagnostics in registration row warnings and
  resident artifact summaries.
- Added a resident CUDA smoke test on a shifted two-light star dataset.
- Updated registration and CUDA backend documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\gpwbpp.exe run --help | Select-String -Pattern "similarity_cuda_triangle|resident-registration"
.\.venv\Scripts\python.exe -c "import gpwbpp_cuda,json; print(json.dumps({'cuda_available': gpwbpp_cuda.cuda_available(), 'devices': gpwbpp_cuda.list_devices()}, ensure_ascii=False, indent=2))"
git diff --check
```

## Test Results

- Ruff: passed.
- Targeted resident CUDA tests: `13 passed in 0.84s`.
- Full pytest suite: `159 passed in 7.67s`.
- CLI help confirms `similarity_cuda_triangle` is exposed for resident runs.
- `git diff --check`: no whitespace errors; Git reported only LF-to-CRLF
  working-copy warnings.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Known Limitations

- This is a bridge mode: resident calibrated frames stay in VRAM and matrix
  application is resident, but compact star catalogs/descriptors still pass
  through Python orchestration.
- The mode currently estimates similarity transforms from triangle descriptors;
  polygon descriptors, homography, local distortion, and Lanczos/clamping warp
  remain future work.
- The validation is a two-light shifted synthetic test plus the full pytest
  suite, not the final 200-light real-data comparison.

## Next Step

Run resident `similarity_cuda_triangle` on a modest real-data calibrated subset,
then promote the strongest registration path into the final high-VRAM
200-light benchmark plan.

## Clean-room Compliance

Compliant. The implementation uses GPWBPP-owned code and public algorithmic
behavior only. No PixInsight/WBPP/PJSR source code was read, copied,
summarized, or modified.
