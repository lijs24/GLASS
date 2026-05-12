# Real Data Audit 240430 Status

Scope:

- Read-only audit of `E:\摄影素材\天协远程台原始素材\远程台240430`.
- Output directory: `runs/local_audit_240430`.

Commands run:

- `.\\.venv\\Scripts\\gpwbpp audit --root "E:\\摄影素材\\天协远程台原始素材\\远程台240430" --out runs/local_audit_240430 --backend auto`
- `.\\.venv\\Scripts\\python -m pytest -q`

Audit result:

- Frames scanned: `857`
- Frame types: `bias=20`, `dark=200`, `flat=70`, `light=567`
- Filters: `Blue=39`, `Green=39`, `Ha=282`, `Lum=77`, `OIII=117`, `Red=53`, `SII=30`, `none=220`
- Scan warnings: `4`
- Plan executable: `true`
- Plan global warnings: `0`
- Light plans: `567`

Generated artifacts:

- `runs/local_audit_240430/manifest.json`
- `runs/local_audit_240430/processing_plan.json`
- `runs/local_audit_240430/report.html`
- `runs/local_audit_240430/run_state.json`

Test result after audit:

- `19 passed, 4 skipped`
- Skips are native CUDA tests because no native backend is built.

CUDA/toolchain note:

- `nvidia-smi` detects `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- `nvcc`, CMake, and MSVC `cl` were not found in PATH or common CUDA Toolkit location.

Clean-room compliance:

- The input directory was not modified.
- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.

