# S2-Gate450 Status: Two-Phase Cosmetic DQ Cache Resident Regression

## Gate

S2-Gate450: Two-Phase Cosmetic DQ Cache Resident Regression

## Completed

- Added a true two-phase GLASS regression:
  - phase 1: CPU/tile calibration with cosmetic correction enabled;
  - phase 2: resident CUDA integration on the same run directory;
  - no manual light-frame sidecar fields are added between phases.
- Fixed resident calibration-artifact DQ path handling for GLASS-generated relative `dq_mask_path` values that already include the run path.
- Proved resident CUDA consumes the pre-existing CPU/tile calibration DQ cache before resident artifacts rewrite `calibration_artifacts.json`.
- Proved the finite cosmetic hot pixel is excluded from resident master/weight output:
  - master remains `100.0` at the flagged pixel;
  - weight drops from `2.0` to `1.0` only at the flagged pixel.
- Updated Phase 2 gate plan and algorithm source notes.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_consumes_two_phase_cosmetic_calibration_cache tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_calibration_artifact_dq_sidecar tests/test_resident_cuda_run.py::test_resident_source_dq_calibration_artifact_candidates_keep_relative_run_path`
  - Initial run exposed a real GLASS-generated relative `dq_mask_path` resolution bug.
  - After the fix: `3 passed in 0.63s`.
- Synthetic two-phase validation script:
  - dataset: 2 light frames, 1 bias, 1 dark, 1 flat, 32x32;
  - phase 1: CPU/tile calibration with cosmetic correction;
  - phase 2: resident CUDA integration with automatic calibration-artifact DQ routing;
  - output artifact: `runs/checkpoints/s2_gate_450_perf/two_phase_cpu_cosmetic_calibration_cache_to_resident_cuda.json`.
- `.venv\Scripts\python.exe -m pytest -q`
  - Result: `1071 passed in 40.65s`.

## Synthetic Validation Result

- CPU/tile calibration elapsed: `0.2379053 s`.
- Resident CUDA run elapsed: `0.1306747 s`.
- `master_max_abs`: `0.0`.
- `master_mean_abs`: `0.0`.
- `weight_max_abs`: `0.0`.
- `weight_mean_abs`: `0.0`.
- Hot pixel output:
  - coordinate: `[9, 11]`;
  - master: `100.0`;
  - weight: `1.0`.
- Source-DQ summary:
  - `passed=true`;
  - `input_invalid_samples_before_rejection=1`;
  - `input_flagged_samples=1`;
  - `source_dq_flag_counts.hot_pixel=1`;
  - `source_dq_flag_counts.cosmetic_corrected=1`;
  - `applied_frame_count=1`;
  - `sidecar_source_counts.calibration_artifacts=2`;
  - `sidecar_artifact_path_count=1`.

## CUDA

- CUDA available to GLASS: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Real Data

- The M38 200-light benchmark was not rerun in this gate.
- Reason: this gate proves the two-phase DQ cache handoff on a controlled small dataset. The next real-data gate should decide whether to run the expensive 200-light path with a two-phase calibration cache or first add a CLI preset/option to make that workflow ergonomic and reproducible.

## Known Limitations

- The two-phase handoff currently relies on an existing `calibration_artifacts.json` in the resident run directory or an explicit plan artifact path.
- Resident CUDA still recalibrates raw light frames; it consumes the DQ cache for valid-sample masking, not the cosmetically corrected calibrated pixel values.
- XISF and multi-extension FITS DQ sidecars remain future work.
- This gate does not change registration, local normalization, rejection, resident integration kernels, or real-data benchmark outputs.

## Next Step

S2-Gate451 should make the two-phase DQ cache resident workflow a first-class CLI/runtime route, for example with a guarded option or preset that runs CPU/tile calibration DQ generation before resident CUDA integration, then run a small regression and decide whether the M38 H 200-light benchmark should be rerun under that route.

## Clean-Room Compliance

- Only GLASS code, GLASS-generated FITS fixtures, GLASS CPU/tile calibration artifacts, and GLASS resident CUDA artifacts were used.
- No official PixInsight/WBPP/PJSR source was read, summarized, copied, or used.
- Input image directories were treated as read-only.
