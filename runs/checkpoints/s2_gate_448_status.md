# S2-Gate448 Status: Resident Input-DQ Sidecar Plumbing

## Gate

S2-Gate448: Resident Input-DQ Sidecar Plumbing And File Regression

## Completed

- Added resident CUDA input-DQ sidecar routing from light-frame plan records.
- Accepted plan keys:
  - `source_dq_mask_path`
  - `dq_mask_path`
  - `calibration_dq_mask_path`
  - `input_dq_mask_path`
- Added FITS DQ sidecar decoding into resident source invalid masks.
- Unioned sidecar invalid samples with source-array nonfinite samples before resident integration.
- Preserved source-DQ sidecar paths and component summaries in `source_dq_summary.rows`.
- Added helper tests for FITS sidecar DQ bit counts and union semantics.
- Added resident CUDA CLI regression proving a finite sidecar hot pixel is excluded from master/weight output.
- Updated Phase 2 gate plan and algorithm source notes.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_plan_source_dq_sidecar`
  - Initial run exposed expected test-path issues, then passed after fixes.
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_plan_source_dq_sidecar tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_simple_snr_weighting`
  - Result: `7 passed in 0.73s`.
- Synthetic file-level resident CUDA validation script:
  - dataset: 8 light frames, 3 bias, 3 dark, 3 flat, 64x64, 2 FITS source-DQ sidecars;
  - output artifact: `runs/checkpoints/s2_gate_448_perf/synthetic_file_sidecar_resident_cuda_vs_cpu_expected.json`.
- `.venv\Scripts\python.exe -m pytest -q`
  - Result: `1068 passed in 39.82s`.

## Synthetic Validation Result

- Resident run elapsed: `0.1647007 s`.
- `master_max_abs`: `0.0`.
- `master_mean_abs`: `0.0`.
- `weight_max_abs`: `0.0`.
- `weight_mean_abs`: `0.0`.
- Source-DQ summary:
  - `passed=true`;
  - `input_invalid_samples_before_rejection=2`;
  - `input_flagged_samples=2`;
  - `source_dq_flag_counts.hot_pixel=2`;
  - `applied_frame_count=2`;
  - status counts: `applied=2`, `no_invalid_samples=6`.

## CUDA

- CUDA available to GLASS: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Real Data

- The M38 200-light benchmark was not rerun in this gate.
- Reason: this gate changes source-DQ sidecar input plumbing. The known real M38 resident path does not currently provide explicit source-DQ sidecars, so rerunning it would not exercise the new code path.
- Next real-data gate should rerun 200-light once calibration/cosmetic DQ cache outputs are automatically routed into resident source-DQ sidecars or once a real sidecar-bearing dataset is available.

## Known Limitations

- Sidecar reader currently supports FITS primary-image DQ bitfields.
- XISF DQ sidecars and multi-extension FITS DQ sidecars are not implemented in this gate.
- Plan-sidecar paths are consumed when present, but the calibration/cosmetic pipeline does not yet automatically attach its generated `dq_mask_path` outputs to resident execution plans.
- This gate does not promote resident CUDA to a native StackEngine implementation; it closes the input-DQ route into the existing resident StackEngine-shaped surface.

## Next Step

S2-Gate449 should wire calibration/cosmetic DQ cache artifacts into the resident default path automatically, then rerun a small file-level regression and a 200-light real regression if output semantics change.

## Clean-Room Compliance

- Only GLASS source code, GLASS-generated synthetic FITS fixtures, GLASS plan JSON, and GLASS resident artifacts were used.
- No official PixInsight/WBPP/PJSR source was read, summarized, copied, or used.
- Input image directories were treated as read-only.
