# S2-Gate 662 Status: Resident CUDA Star-Protected Cosmetic Source-DQ

## Gate

S2-Gate 662

## Completed

- Added resident CUDA star-protected isolated cosmetic source-DQ count/apply kernels.
- Added native methods:
  - `ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frame`
  - `ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame`
- Added Python wrappers in `glass_cuda.ResidentCalibratedStack`.
- Added `inline_star_protected_cosmetic_thresholds_from_resident_stack`, which combines resident histogram median/MAD thresholds with a compact resident CUDA star catalog.
- Added opt-in CLI mode `--resident-inline-source-dq cosmetic_star_cuda` for `glass run` and `glass audit`.
- Updated resident source-DQ strategy/runtime artifacts to record the star-protected CUDA detector, execution mode, threshold source, star catalog source, and protection radius.
- Kept star-protected batch application on a per-frame native route until a true batched star-catalog API exists.
- Updated Phase 2 docs and algorithm-source ledger.

## Commands Run

- `cmd.exe /d /s /c "\"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 -host_arch=x64 && \".venv\Scripts\python.exe\" -m cmake --build build --config Release --target _glass_cuda_native"`
- `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_source_dq_strategy.py src\glass\cli.py src\glass_cuda.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_run_resident_inline_source_dq_accepts_star_protected_cuda_mode tests\test_resident_source_dq_strategy.py::test_resident_source_dq_strategy_records_cuda_star_protected_inline_detector tests\test_resident_source_dq.py::test_inline_star_protected_cosmetic_thresholds_from_resident_stack_records_catalog tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_keeps_star_protected_per_frame`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_count_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_apply_keeps_star_core tests\test_resident_source_dq.py::test_star_protected_cosmetic_detector_keeps_compact_star_but_flags_hot_pixel tests\test_resident_source_dq.py::test_source_invalid_mask_from_star_protected_inline_cosmetic_records_star_model`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_run_resident_inline_source_dq_accepts_star_protected_cuda_mode tests\test_resident_source_dq_strategy.py::test_resident_source_dq_strategy_records_cuda_star_protected_inline_detector tests\test_resident_source_dq.py::test_inline_star_protected_cosmetic_thresholds_from_resident_stack_records_catalog tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_keeps_star_protected_per_frame tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_count_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_apply_keeps_star_core tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_accepts_inline_star_protected_cosmetic_cuda_source_dq`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli synthetic --out runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\data --frames 4 --width 64 --height 64 --filter H --known-shift`
- `.venv\Scripts\python.exe -m glass.cli scan --root runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\data --out runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\manifest.json`
- `.venv\Scripts\python.exe -m glass.cli plan --manifest runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\manifest.json --out runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\processing_plan.json`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\processing_plan.json --out runs\checkpoints\s2_gate_662_cosmetic_star_cuda_smoke\run --backend cuda --memory-mode resident --resident-inline-source-dq cosmetic_star_cuda --resident-inline-source-dq-hot-sigma 2.0 --resident-inline-source-dq-cold-sigma 8.0 --resident-inline-source-dq-max-invalid-fraction 0.01 --resident-runtime-preset manual --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration off --resident-prefetch-frames 2 --resident-prefetch-workers 2 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 2 --resident-calibration-streams 2 --resident-output-maps audit`

## Test Results

- Native rebuild: passed; `ninja: no work to do`.
- Focused Python source-DQ/CLI/strategy tests: `4 passed`.
- Focused native CUDA star-protected tests: `4 passed`.
- Focused integrated gate suite: `7 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1398 passed in 61.89s`.
- Synthetic resident CUDA smoke:
  - `total_elapsed_s=0.22039210004732013`
  - `resident_inline_source_dq=cosmetic_star_cuda`
  - `source_dq_passed=true`
  - `source_dq_rows=4`
  - `input_invalid_samples_before_rejection=0`
  - detector `ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frame`
  - execution `cuda_star_catalog_protected_isolated_threshold_apply`

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- Checkpoint status: `runs/checkpoints/s2_gate_662_status.md`.
- Synthetic smoke dataset: `runs/checkpoints/s2_gate_662_cosmetic_star_cuda_smoke/data`.
- Synthetic smoke manifest: `runs/checkpoints/s2_gate_662_cosmetic_star_cuda_smoke/manifest.json`.
- Synthetic smoke plan: `runs/checkpoints/s2_gate_662_cosmetic_star_cuda_smoke/processing_plan.json`.
- Synthetic smoke run: `runs/checkpoints/s2_gate_662_cosmetic_star_cuda_smoke/run`.

## Known Limitations

- `cosmetic_star_cuda` is opt-in and not a default science route.
- Star catalogs are currently compact host-uploaded per frame; batch apply falls back to per-frame native calls for star-protected mode.
- The current resident grid/NMS star catalog can over-protect one-sample hot pixels if they are admitted as stars. Counts are now auditable, but later gates should improve star/cosmetic separation before default promotion.
- The synthetic smoke validates execution and artifact plumbing; it is not a 200-light performance claim.

## Next Step

The next substantive gate should batch resident star catalogs and star-protected apply across frames, then run a real 200-light A/B against the latest accepted default route and the black-box reference.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA kernels, GLASS resident histogram/star-catalog wrappers, GLASS CPU baseline tests, GLASS synthetic fixtures, and user-owned local hardware. No external or proprietary implementation source was inspected, copied, summarized, or reworked, and input image directories were not modified.
