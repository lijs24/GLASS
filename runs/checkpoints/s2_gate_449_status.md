# S2-Gate449 Status: Resident Calibration-Artifact DQ Cache Routing

## Gate

S2-Gate449: Resident Calibration-Artifact DQ Cache Routing

## Completed

- Added resident CUDA indexing for existing GLASS `calibration_artifacts.json`.
- Reads `calibrated_lights[].dq_mask_path` sidecars and matches them by `frame_id`.
- Uses calibration artifact DQ sidecars only when the frame plan does not already provide an explicit sidecar field.
- Preserves source-DQ provenance:
  - sidecar source counts;
  - sidecar artifact paths;
  - sidecar frame ids;
  - component summaries.
- Adds `source_dq_calibration_artifact_index` to resident artifacts and integration outputs.
- Fixed relative run-dir candidate handling so `--out runs/...` does not resolve `run/calibration_artifacts.json` under `plan_root` twice.
- Added focused resident CUDA tests for:
  - explicit plan sidecar routing;
  - calibration artifact sidecar routing;
  - relative candidate path behavior.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq.py`
  - Result: passed.
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_cuda_run.py::test_resident_source_dq_calibration_artifact_candidates_keep_relative_run_path tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_plan_source_dq_sidecar tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_calibration_artifact_dq_sidecar`
  - Result: `8 passed in 0.72s`.
- Synthetic file-level resident CUDA validation script:
  - dataset: 8 light frames, 3 bias, 3 dark, 3 flat, 64x64;
  - DQ source: pre-existing GLASS `calibration_artifacts.json` with 2 FITS hot-pixel sidecars;
  - output artifact: `runs/checkpoints/s2_gate_449_perf/synthetic_calibration_artifact_dq_cache_resident_cuda_vs_cpu_expected.json`.
- `.venv\Scripts\python.exe -m pytest -q`
  - Result: `1070 passed in 40.14s`.

## Synthetic Validation Result

- Resident run elapsed: `0.1608689 s`.
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
  - `sidecar_source_counts.calibration_artifacts=2`;
  - `sidecar_artifact_path_count=1`;
  - status counts: `applied=2`, `no_invalid_samples=6`.

## CUDA

- CUDA available to GLASS: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Real Data

- The M38 200-light benchmark was not rerun in this gate.
- Reason: normal resident M38 runs still do not have calibration/cosmetic DQ cache sidecars in the default resident invocation. This gate proves the automatic handoff once such a GLASS calibration artifact is present.
- Next real-data gate should run a two-phase real-data regression that first generates calibration/cosmetic DQ cache artifacts and then exercises resident artifact-DQ routing on the same light set.

## Known Limitations

- Calibration artifact routing currently consumes FITS DQ sidecars from `calibrated_lights[].dq_mask_path`.
- Existing resident runs overwrite `run/calibration_artifacts.json` at the end with resident calibration artifacts; this gate indexes any pre-existing file before that overwrite.
- Multi-extension FITS DQ and XISF sidecar masks remain future work.
- This gate does not change calibration math, registration, rejection, or resident integration kernels.

## Next Step

S2-Gate450 should make a small two-phase pipeline regression: generate CPU/tile calibration artifacts with cosmetic DQ enabled, then run resident CUDA from those artifacts without manual sidecar editing. If that changes the default real-data route, rerun the M38 H 200-light benchmark and compare timing/results against the current resident baseline.

## Clean-Room Compliance

- Only GLASS code, GLASS-generated FITS fixtures, GLASS calibration artifacts, and GLASS resident artifacts were used.
- No official PixInsight/WBPP/PJSR source was read, summarized, copied, or used.
- Input image directories were treated as read-only.
