# S2-Gate446 Status: Resident CUDA StackEngine Surface Closure

## Result

Passed.

Gate446 stops the previous release/default-promotion/report-only drift and closes a substantive Phase 2 contract gap: resident CUDA integration and resident master-calibration artifacts now emit auditable StackEngine-shaped surface contracts. This does not claim that resident CUDA is the native CPU StackEngine default path; it makes the resident fast path explicit, inspectable, and ready for DQ/mask parity work.

## Completed Work

- Added `src/glass/engine/resident_stack_surface.py`.
- Added resident integration surface contracts while calibrated/registered/integrated arrays are still in memory.
- Added resident master-calibration surface contracts for bias, dark, and flat masters.
- Recorded real source frame ids in resident master cache stats for bias, dark, flat, and flat-bias inputs.
- Taught `glass stack-engine-contract` to distinguish:
  - `native_stack_engine_default`
  - `resident_cuda_stack_engine_surface`
  - older `resident_cuda_contract_emulation`
- Added focused resident surface tests and strengthened the resident CUDA smoke test.
- Updated Phase 2 documentation and algorithm-source audit notes.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_stack_surface.py src\glass\engine\resident_cuda.py src\glass\engine\resident_calibration_artifacts.py src\glass\report\stack_engine_contract.py tests\test_resident_stack_surface.py tests\test_stack_engine_contract.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_stack_surface.py tests\test_stack_engine_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_stack_surface.py tests\test_stack_engine_contract.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads tests\test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_446_cuda_doctor.json`
- `.\.venv\Scripts\glass.exe audit --root runs\checkpoints\s2_gate_446_clean_surface_work\data --out runs\checkpoints\s2_gate_446_clean_surface_work\cpu_run --backend cpu --tile-size 8`
- `.\.venv\Scripts\glass.exe run --plan runs\checkpoints\s2_gate_446_clean_surface_work\resident_run\processing_plan.json --out runs\checkpoints\s2_gate_446_clean_surface_work\resident_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration off --resident-prefetch-frames 0 --resident-h2d-mode pageable`
- `.\.venv\Scripts\glass.exe compare --glass runs\checkpoints\s2_gate_446_clean_surface_work\resident_run\master_H.fits --reference runs\checkpoints\s2_gate_446_clean_surface_work\cpu_run\master_H.fits --out runs\checkpoints\s2_gate_446_cpu_vs_resident_compare.html --glass-label resident_cuda --reference-label cpu_stackengine`
- `.\.venv\Scripts\glass.exe stack-engine-contract --run runs\checkpoints\s2_gate_446_clean_surface_work\resident_run --out runs\checkpoints\s2_gate_446_stack_engine_contract.json --markdown runs\checkpoints\s2_gate_446_stack_engine_contract.md`

## Test Result

- Ruff: passed.
- Focused resident surface/contract tests: `16 passed in 0.85s`.
- Focused resident CUDA smoke contract tests: `17 passed in 0.90s`.
- Regression rerun after fixing minimal output-map `dq_summary=None` handling: `4 passed in 1.01s`.
- Full test suite: `1060 passed in 39.61s`.

## CUDA

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_446_cuda_doctor.json`

## Validation Evidence

- Numeric clean-star CPU vs resident CUDA:
  - Dataset: `clean_star_4x32x32`
  - Shape: `32 x 32`
  - `max_abs`: `0.0`
  - `mean_abs`: `0.0`
  - `rms`: `0.0`
  - `allclose_atol_1e_5`: `true`
  - Artifact: `runs/checkpoints/s2_gate_446_cpu_vs_resident_metrics.json`
- StackEngine contract:
  - `default_path.status`: `resident_cuda_stack_engine_surface`
  - `resident_cuda_stack_engine_surface_count`: `4`
  - `resident_cuda_contract_emulation_count`: `0`
  - `contract_gap_count`: `0`
  - `strict_native_stack_engine_ready`: `false`
  - Artifact: `runs/checkpoints/s2_gate_446_stack_engine_contract.json`
- Resident source-frame closure:
  - Bias masters include source bias frame ids.
  - Dark masters include source dark frame ids.
  - Flat masters include source flat frame ids.
  - Integration surface includes resident light frame ids.

## Artifacts

- `runs/checkpoints/s2_gate_446_cpu_vs_resident_metrics.json`
- `runs/checkpoints/s2_gate_446_cpu_vs_resident_compare.html`
- `runs/checkpoints/s2_gate_446_resident_result_contract.json`
- `runs/checkpoints/s2_gate_446_resident_result_contract.md`
- `runs/checkpoints/s2_gate_446_resident_calibration_contract.json`
- `runs/checkpoints/s2_gate_446_resident_calibration_contract.md`
- `runs/checkpoints/s2_gate_446_stack_engine_contract.json`
- `runs/checkpoints/s2_gate_446_stack_engine_contract.md`
- `runs/checkpoints/s2_gate_446_cuda_doctor.json`

## Known Limits

- Resident CUDA is now a StackEngine-shaped surface, not the native CPU StackEngine default implementation. The strict native-default audit correctly remains false for resident CUDA.
- The exploratory dirty synthetic run still shows source-DQ invalid-sample differences between CPU StackEngine and resident CUDA. This is the next substantive blocker.
- A small exploratory prefetch run with `--resident-prefetch-frames 2 --resident-prefetch-workers 2 --resident-h2d-mode pinned_ring` hit `_LightPrefetcher.result` `KeyError: 2` on a 4-light synthetic set. Official Gate446 validation used resident pageable/no-prefetch and passed.
- No 200-light regression was rerun in this gate because Gate446 changed runtime contracts and provenance, not pixel math. Gate447 should rerun the real/synthetic heavier regression after DQ/mask parity changes.

## Next Gate

S2-Gate447: Resident Source-DQ Parity And 200-Light Regression.

Gate447 should make resident CUDA consume the same source-DQ/mask model as the CPU StackEngine path, then run both dirty synthetic parity and a 200-light regression with resident CUDA timing/result evidence.

## Clean-Room Compliance

Compliant. Gate446 used only GLASS source, GLASS-generated synthetic data, GLASS runtime artifacts, FITS outputs, and GLASS contract JSON. It did not inspect official PixInsight/WBPP/PJSR source, did not modify user image directories, did not create package releases, and did not upload release assets.
