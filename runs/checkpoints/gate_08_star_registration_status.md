# Gate 8 Checkpoint: Clean-room Star Registration Baseline

Gate: 8

Completed content:
- Added a clean-room CPU star matching transform estimator in `src/glass/cpu/registration.py`.
- Supports translation, similarity, and affine model fitting from GLASS-detected stars.
- Scores candidate transforms by one-to-one inlier matching and records matched star count, inliers, RMS, status, warnings, and matrix.
- Wired pipeline registration to try star-based registration first in `method=auto`, with explicit phase-correlation preview fallback only when the star model cannot meet `min_inliers`.
- Updated warp so non-reference frames with failed registration status are written to `skipped_frames` and do not enter warp/LN/integration.
- Exposed streaming star detection for registration reuse.
- Updated registration model docs and tests.

Commands run:
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_pipeline_fixture.py tests\test_cpu_star_detect.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\cpu\registration.py src\glass\engine\registration.py src\glass\engine\quality.py src\glass\engine\warp.py tests\test_cpu_registration.py tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

Test results:
- Targeted tests: 21 passed.
- Ruff targeted check: passed.
- Full pytest: 79 passed in 5.63s.

CUDA availability:
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

Known limitations:
- Star detection is still a simple local-maxima baseline and does not yet estimate robust PSF, eccentricity, or saturated-star exclusion.
- Similarity/affine candidate generation uses simple triangle descriptors and is intended as a correct, auditable baseline, not a final high-performance matcher.
- Large real-data resident CUDA path still uses preview translation mode; wiring the new star transform into resident GPU warp is next.
- Warp currently applies rounded translation only in the tiled pipeline; similarity/affine warp support remains a later gate.

Next step:
- Use the new registration table on the M38 real subset and compare GLASS-derived transforms/status against WBPP black-box logs as diagnostics only.
- Add CPU/GPU affine or similarity warp so non-translation transforms can affect integration.

Clean-room compliance:
- Compliant. This gate uses GLASS code, synthetic tests, and generic image-registration techniques only.
- No PixInsight/WBPP/PJSR official source, class names, function names, comments, or UI code were read or copied.
