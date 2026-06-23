# S2-Gate 525 Status: Resident Triangle Translation-Refine Default Bypass

## Gate

- Gate: S2-Gate 525
- Date: 2026-06-23
- Scope: resident `similarity_cuda_triangle` registration/warp performance

## Completed

- Changed resident triangle translation refinement from implicit-on to
  default-off for `similarity_cuda_triangle`.
- Preserved the old behavior when the processing plan explicitly sets
  `cuda_triangle_translation_refine: true`.
- Added `triangle_translation_refine_policy_source` to resident artifacts and
  per-frame warnings.
- Corrected per-frame centroid warnings so the default-bypass path still
  reports the native GPU centroid catalog mode.
- Performed a C: cleanup check before the real run:
  - C: free space was about 407.44 GiB.
  - Repository size was about 2.37 GiB.
  - `C:\glass_runs` was about 114.175 GiB.
  - `C:\gpwbpp_runs` was about 83.686 GiB.
  - No cleanup was needed; `C:\gpwbpp_runs\final_m38_h_200` was kept intact.

## Real 200-Light Validation

- Dataset/plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Shared master cache:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Probe root:
  `C:\glass_runs\phase2_s2_gate525_translation_refine_probe\runs_20260623_111012`
- Post-change default run:
  `C:\glass_runs\phase2_s2_gate525_translation_refine_default\runs_20260623_111012\default`

Measured results:

- Old default probe: shell `7.504382 s`,
  `triangle_translation_refine=true`, `191` rejected, `8` skipped, `0`
  applied.
- Explicit-off probe: shell `7.26101 s`,
  `triangle_translation_refine=false`.
- Post-change default: shell `6.75901 s`,
  `triangle_translation_refine=false`,
  `triangle_translation_refine_policy_source=default_similarity_triangle_off`.
- Registration fine component:
  - Gate524 warm-repeat: `1.9681131000539125 s`
  - Gate525 post-change default: `1.90622570034715 s`

Numerical results:

- Gate525 post-change default vs explicit-off probe:
  master, weight map, coverage map, low/high rejection maps, and DQ map were
  all bitwise identical.
- Gate525 post-change default vs Gate524 warm-repeat:
  master, weight map, coverage map, low/high rejection maps, and DQ map were
  all bitwise identical.
- Because Gate525 is bitwise identical to Gate524, the prior WBPP black-box
  comparison carries forward:
  - robust-fit RMS `0.0015009512947433384`
  - p99 absolute difference `0.00034034321741462114`
  - fit fraction `0.982980688129347`
  - warm-shell speedup reference `165.00201362863976x`

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "triangle_default_uses_gpu_centroid_without_pixel_refine or translation_refine"`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan ... --out ... --backend cuda --memory-mode resident --until-stage integration ...`
- `.\.venv\Scripts\python.exe -m json.tool runs\checkpoints\s2_gate_525_translation_refine_bypass_summary.json`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_525_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused resident CUDA tests: `4 passed, 85 deselected`.
- Full pytest: `1169 passed in 44.58s`.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- Checkpoint: `runs/checkpoints/s2_gate_525_status.md`
- Summary JSON:
  `runs/checkpoints/s2_gate_525_translation_refine_bypass_summary.json`
- Doctor JSON: `runs/checkpoints/s2_gate_525_doctor.json`
- Real run root:
  `C:\glass_runs\phase2_s2_gate525_translation_refine_default\runs_20260623_111012`

## Known Limitations

- This gate removes a default no-op for the current real 200-light path; it is
  not a new CUDA kernel optimization.
- The explicit plan key `cuda_triangle_translation_refine: true` remains
  available for diagnostics or datasets where translation-only refinement is
  intentionally desired.
- End-to-end shell timings still show normal run-to-run variance; the reliable
  improvement claim is the removal of the measured registration component.

## Next Step

- Continue Phase 2 on substantive resident registration/warp and light-pipeline
  optimization:
  - batch more resident registration orchestration on GPU;
  - reduce host/device round trips;
  - continue real 200-light A/B validation with bitwise or bounded numerical
    output checks.

## Clean-Room Compliance

- This gate used only GLASS code, GLASS-generated artifacts, the user-owned
  200-light benchmark data, and user-generated WBPP black-box comparison
  metrics from prior gates.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Input image directories were not modified.
