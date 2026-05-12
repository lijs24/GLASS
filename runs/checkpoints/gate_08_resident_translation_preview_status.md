# Gate 08 Partial Status: Resident Translation Preview

Gate: 08 partial, with Gate 11 resident integration support.

Completed content:
- Added optional resident CUDA preview registration mode:
  `--resident-registration translation_preview`.
- Added `--reference-frame-id` for resident runs. The value can match a frame id,
  file name, or file stem.
- Added native `ResidentCalibratedStack.apply_translation_frame()` to apply an
  integer translation warp in VRAM after calibration.
- Resident integration now skips NaN pixels and zero/non-finite frame weights.
  This lets translated edge fill stay out of weight/coverage accounting.
- Resident registration writes `registration_results.json` with diagnostic
  translation matrices and explicit warnings that this is not star-model RMS.
- The resident `winsorized_sigma` mode is now documented as a two-pass mean/std
  winsorized approximation, not a PixInsight-equivalent robust implementation.

Commands run:
- Rebuilt native CUDA extension with CMake/Ninja, Visual Studio Build Tools, and
  CUDA Toolkit 13.2.
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_resident_stack.py tests\\test_cuda_smoke.py tests\\test_gpu_warp_vs_cpu.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli run --help`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

Test results:
- Targeted resident/CUDA tests: 10 passed in 0.81 s.
- Resident CLI smoke test: 1 passed in 0.22 s.
- Full test suite: 76 passed in 5.61 s.

CUDA availability:
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

Known limitations:
- This is preview-scale phase correlation plus integer-pixel CUDA translation.
  It is not the full Gate 08 star-based translation/similarity/affine
  registration model.
- It does not yet implement Lanczos interpolation, similarity/affine/homography
  warp, star matching, inlier RMS, or WBPP FastIntegration-equivalent internal
  alignment behavior.
- Local Normalization remains outside the resident path.
- `winsorized_sigma` remains a baseline approximation and needs a true robust
  per-pixel Winsorized Sigma Clipping implementation for closer WBPP parity.

Next step:
- Run the M38 200-light resident CUDA comparison with
  `--resident-registration translation_preview`, WBPP's observed reference
  frame, `--flat-floor 0.05`, and `--integration-rejection winsorized_sigma`;
  then compare against the WBPP master to quantify how much alignment improves
  the current parity gap.

Clean-room compliance:
- Compliant. No official WBPP/PJSR source was read or copied. The behavior is
  based on project-owned code, public algorithm concepts, and user-generated
  WBPP black-box logs/outputs.
