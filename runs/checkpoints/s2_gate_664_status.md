# S2-Gate 664 Status: Batched Resident Star-Protected CUDA Source-DQ

## Gate

S2-Gate 664

## Completed

- Added native resident CUDA batch count/apply for star-protected isolated cosmetic source-DQ:
  - `ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frames`
  - `ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frames`
- Added Python wrappers and flattened per-frame star-catalog upload support.
- Routed homogeneous `cosmetic_star_cuda` resident source-DQ batches through the native batch methods.
- Preserved per-frame fallback for mixed detector batches.
- Updated resident mainline framework evidence matching so `cosmetic_star_cuda` source names satisfy `inline_cosmetic_cuda_positive`.
- Added focused tests, including native batch count/apply and batch-vs-single fuzz parity.
- Ran two real 200-light M38 `cosmetic_star_cuda` resident CUDA validations.
- Updated Phase 2 hardening, validation, and algorithm-source documentation.

## Commands Run

- `cmd /d /s /c "\"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 -host_arch=x64 && \".venv\Scripts\python.exe\" -m cmake --build build --config Release --target _glass_cuda_native"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_batch_count_matches_single tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_batch_apply_keeps_star_core tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_uses_star_protected_batch_native`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_star_cuda --resident-inline-source-dq-policy conservative --resident-inline-source-dq-admission active_registered --resident-mainline-framework-gate warn --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 0 --resident-mainline-min-source-dq-applied-samples 0 --out C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\star_cuda_batch_conservative_active_warn`
- Strict framework regeneration for run A with `write_resident_mainline_framework(...)`.
- `.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\star_cuda_conservative_active_warn --candidate-run C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\star_cuda_batch_conservative_active_warn --out C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\gate664_vs_gate663_regression.json --markdown C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\gate664_vs_gate663_regression.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10`
- `.venv\Scripts\python.exe -m glass.cli resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\star_cuda_conservative_active_warn --candidate-run C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\star_cuda_batch_conservative_active_warn --out C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\gate664_vs_gate663_determinism.json --markdown C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\gate664_vs_gate663_determinism.md`
- `.venv\Scripts\python.exe -m glass.cli run ... --resident-mainline-framework-gate strict --out C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_232500\star_cuda_batch_repeat_strict`
- `.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\star_cuda_batch_conservative_active_warn --candidate-run C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_232500\star_cuda_batch_repeat_strict --out C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_232500\gate664_repeat_regression.json --markdown C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_232500\gate664_repeat_regression.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_batch_matches_single_fuzz tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_batch_count_matches_single tests\test_cuda_resident_stack.py::test_resident_stack_star_protected_isolated_cosmetic_threshold_batch_apply_keeps_star_core tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_uses_star_protected_batch_native tests\test_resident_mainline_framework.py::test_resident_mainline_framework_inline_cosmetic_star_cuda_scope_passes`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused CUDA/source-DQ/framework tests: `5 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1402 passed in 62.36s`.

## Real 200-Light Results

- Run A:
  `C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\star_cuda_batch_conservative_active_warn`
- Run B:
  `C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_232500\star_cuda_batch_repeat_strict`
- Run A elapsed: `20.791611200082116 s`.
- Run B elapsed: `20.913607999915257 s`.
- Gate663 single-frame star-protected elapsed: `21.259431299986318 s`.
- Gate660 conservative active-registered `cosmetic_cuda` elapsed: `18.553858600207604 s`.
- Black-box reference elapsed used for speedup: `1092.541 s`.
- Run A speedup versus black-box reference: `52.54720230607645x`.
- Run B speedup versus black-box reference: `52.240675066895534x`.
- Run A source-DQ deferred apply: `0.6506714000133798 s`.
- Gate663 source-DQ deferred apply: `0.7322519001318142 s`.

## Run A Component Timing

- `resident_light_read_upload_calibrate`: `10.217619500006549 s`
- `resident_registration_warp`: `0.26487090112641454 s`
- `resident_local_normalization`: `0.36363069992512465 s`
- `resident_integration`: `3.2947529000230134 s`
- `resident_output_write`: `0.24940850003622472 s`

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: available to GLASS.

## Known Limitations

- Gate664 is not a default-promotion gate; `cosmetic_star_cuda` remains opt-in.
- The native batch-vs-single fuzz test passes on synthetic resident stacks.
- Real repeat determinism is not yet green for this opt-in source-DQ route:
  - Run A source-DQ invalid samples: `146987`.
  - Run B source-DQ invalid samples: `146992`.
  - Repeat regression passes runtime and required contracts but fails `resident_determinism_passed`.
- This points to remaining threshold/catalog repeat determinism work in the opt-in source-DQ path or to the need for a tolerance-based diagnostic acceptance rule.

## Next Step

- Return to Phase 2 mainline substance: make resident source-DQ threshold/catalog generation repeat-deterministic, or shift back to the larger default-route bottlenecks:
  - read/upload/calibration overlap,
  - hardened winsorized integration,
  - DQ/mask contract parity for default StackEngine promotion.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA kernels, GLASS Python wrappers, GLASS resident artifacts, GLASS tests, and user-owned benchmark outputs.
- It does not inspect, copy, summarize, or rework external/proprietary implementation source.
- Input image directories were treated as read-only.
