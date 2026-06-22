# S2-Gate 465 Status: Admission-Selected Chunk Capacity Execution

## Gate

- Gate: S2-Gate 465
- Scope: enforce resident memory-admission reduced chunk capacity in resident CUDA matrix-warp execution.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Extended resident memory admission with selected peak/headroom fields:
  - `selected_chunk_capacity_frames`
  - `selected_warp_batch_dispatch`
  - `selected_estimated_peak_bytes`
  - `selected_estimated_peak_gib`
  - `selected_headroom_bytes`
  - `selected_headroom_gib`
  - `selected_fits_budget`
  - `preferred_fits_budget`
- Changed admission semantics so an explicit VRAM budget can pass with `resident_reduced_chunk_capacity` when a reduced chunk capacity fits.
- Kept truly too-small explicit budgets blocking before CUDA allocation.
- Added CLI plumbing from `resident_memory_admission.json` to resident execution.
- Added `resident_warp_chunk_capacity_frames` to `run_resident_calibration_integration`.
- Taught `_apply_resident_registration_matrix_batch` to split matrix batch submissions by a reduced capacity and aggregate timing/workspace/kernel-launch evidence.
- Preserved the default full-capacity path: full `resident_full_frame` admission does not pass an external chunk capacity, so native chunked dispatch remains a single native batch call.
- Added resident registration artifact fields:
  - `triangle_warp_batch_requested_chunk_capacity_frames`
  - `triangle_warp_batch_effective_chunk_capacity_frames`
  - `triangle_warp_batch_capacity_source`
- Updated tests and documentation.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Driver version from device list: 596.21.

## Real 200-Light Results

- Final green run: `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622`
- Input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat.
- Backend: CUDA resident stack.
- Registration: `similarity_cuda_triangle`.
- Warp interpolation: `lanczos3`.
- Warp batch dispatch: `chunked`.
- Local normalization: off.
- Rejection: `winsorized_sigma`.
- Weighting: none.
- Integrated / weighted frames: `193/200`.
- Zero-weight / quality-rejected frames: `7`.
- Internal GLASS run timing: `36.103794 s`.
- Outer PowerShell timing: `36.485266 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Acceptance-audit speedup vs WBPP: `30.261113x`.
- Acceptance audit: passed.

## Admission And Capacity Evidence

- Admission artifact: `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622\resident_memory_admission.json`
- Admission status: `passed`.
- Recommended action: `resident_full_frame`.
- Selected dispatch: `chunked`.
- Selected chunk capacity: `8`.
- Selected estimated peak: `49.608422 GiB`.
- Budget: `86.032617 GiB`.
- Selected headroom: `36.424195 GiB`.
- Planned active frames after excludes: `193`.
- Planned warp frames: `192`.
- Runtime capacity source: `native_preferred`.
- Runtime requested/effective forced capacity: `null`.
- Native chunk frames: `8`.
- Native chunk count: `24`.
- Timing model: `native_chunked_batch_warp_scatter_one_sync`.
- Memory planned/observed capacity: `8/8`.

## Compare Metrics

- Compare report: `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622\s2_gate_465_compare.html`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622\s2_gate_465_compare.json`
- Shape match: true.
- Coverage fraction at `min_coverage=190`: `0.9610426399`.
- Compared pixels: `59249432`.
- RMS diff: `0.0017005768`.
- P99 absolute diff: `0.0004598012`.

## Contract Results

- Resident calibration contract: passed.
- Resident result contract: passed with pixel verification.
- Pipeline contract: passed with pixel verification.
- StackEngine contract: passed.
- StackEngine default-promotion ready: true.
- Acceptance audit: passed.
- HTML report: `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622\s2_gate_465_report.html`

## Diagnostic Runs

- `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r1_20260622`
  was deleted after it exposed an implementation issue: passing full preferred
  capacity `8` into Python-level splitting changed the default path into 24
  Python/native calls. The implementation was corrected so only reduced-capacity
  admission forces splitting.
- `E:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622`
  passed numerical and contract checks except release runtime. It failed the
  runtime contract because `output_write=13.127945 s` on E: pushed total runtime
  to `49.299420 s`, above the release baseline factor. This is recorded as an
  I/O placement diagnostic rather than green gate evidence.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\resident_cuda.py src\\glass\\cli.py tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py::test_resident_memory_admission_recommends_reduced_chunk_capacity tests\\test_resident_cuda_run.py::test_resident_registration_matrix_batch_honors_chunk_capacity tests\\test_cli_smoke.py::test_cli_resident_run_passes_reduced_chunk_capacity_from_admission tests\\test_cli_smoke.py::test_cli_resident_run_blocks_explicit_low_vram_budget`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_gpu_warp_vs_cpu.py tests\\test_cuda_resident_stack.py`
- `.\\.venv\\Scripts\\python.exe -m glass.cli run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 --resident-h2d-mode pinned_ring --resident-output-maps audit --resident-registration similarity_cuda_triangle --resident-registration-quality-gate warn --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-rejection winsorized_sigma --resident-winsorized-mode fast_approx --integration-weighting none --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\python.exe -m glass.cli compare --glass C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\integration\\resident_master_H.fits --reference C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_compare.html --glass-time-seconds 36.4852659 --reference-time-seconds 1092.541 --glass-label GLASS-S2G465-admission-capacity-default-parity --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\python.exe -m glass.cli resident-calibration-contract --run C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_calibration_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_calibration_contract.md --fail-on-failed`
- `.\\.venv\\Scripts\\python.exe -m glass.cli resident-result-contract --run C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_result_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_result_contract.md --pixel-verify --pixel-verify-tile-size 2048 --fail-on-failed`
- `.\\.venv\\Scripts\\python.exe -m glass.cli pipeline-contract --run C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_pipeline_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_pipeline_contract.md --pixel-verify --pixel-verify-tile-size 2048 --resident-calibration-contract-json C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_calibration_contract.json`
- `.\\.venv\\Scripts\\python.exe -m glass.cli stack-engine-contract --run C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_stack_engine_contract.json --markdown C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_stack_engine_contract.md --scope all --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_calibration_contract.json --resident-result-contract-json C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_resident_result_contract.json --require-default-ready`
- `.\\.venv\\Scripts\\python.exe -m glass.cli acceptance-audit --manifest C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_compare.json --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_acceptance_audit.json --markdown C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --benchmark-contract benchmarks\\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_pipeline_contract.json --stack-engine-contract-json C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_stack_engine_contract.json`
- `.\\.venv\\Scripts\\python.exe -m glass.cli report --run C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622 --out C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_report.html --acceptance-audit C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_acceptance_audit.json --stack-engine-contract C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_stack_engine_contract.json --pipeline-contract C:\\glass_runs\\phase2_s2_gate_465_200\\admission_capacity_default_parity_r3_20260622\\s2_gate_465_pipeline_contract.json`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused admission/chunk/CLI tests: `4 passed`.
- Resident/CLI suite: `104 passed`.
- GPU warp/resident stack suite: `51 passed`.
- Full pytest: `1099 passed in 48.22s`.

## Known Limitations

- Reduced-capacity execution is currently enforced by Python-level batch splitting, which adds extra native calls and synchronizations for budget-constrained runs.
- A future native CUDA binding should accept a max chunk capacity so reduced-capacity execution can stay inside one native dispatcher call.
- C: drive free space was very low during validation. Output disk placement can dominate total runtime, as shown by the diagnostic E: run.

## Next Step

- S2-Gate466 should add native CUDA binding support for a max chunk-capacity argument in matrix batch warp, then prove a reduced-capacity synthetic or real-budget run keeps native dispatch compact while respecting the selected workspace budget.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- WBPP was used only through user-generated black-box timing and output artifacts.
- Input image directories were treated as read-only.
