# S2-Gate 691 Status: Resident Frame-Index Alignment Contract

## Gate

S2-Gate 691.

## Completed Content

- Hardened `resident_frame_masks.json` around resident stack frame indices.
- Added `frame_index` to every resident frame-mask row.
- Added active, masked, and unknown zero-weight frame-index lists to the
  resident frame-mask summary.
- Added `frame_index_alignment_contract` to group and aggregate summaries.
- `build_resident_frame_mask_contract` now optionally accepts
  `frame_weight_by_id`.
- Resident CUDA passes its authoritative `frame_weights` map into the
  frame-mask contract builder by default.
- Runtime validation now fails if `frame_weights[index]` does not match
  `frame_weights_by_id[frame_id]`, or if a frame ID is missing from the map.
- Added focused tests for:
  - row frame indices;
  - active/masked index lists;
  - intentional frame-weight index drift;
  - resident CUDA completion/exclusion regression where the excluded second
    light must remain frame index `1`.

## Real 200-Light Validation

- Baseline run:
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned`.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract`.
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_mainline_audit.json`.
- Resident regression gate:
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_regression_gate.json`.
- Phase 2 mainline A/B:
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_phase2_mainline_ab.json`.
- A/B Markdown:
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_phase2_mainline_ab.md`.

Results:

- Mainline audit: passed, failed checks `[]`.
- Resident regression gate: passed, failed checks `[]`.
- Phase 2 mainline A/B: passed, failed checks `[]`.
- Candidate active/masked frames: `193 / 7`.
- Candidate tracked map count: `6`.
- Hash mismatch count: `0`.
- Baseline-to-candidate elapsed ratio: `0.9972782917458977`.
- Candidate total elapsed: `12.359771899762563 s`.
- `resident_frame_masks.json` alignment:
  - checked: `true`;
  - passed: `true`;
  - `weight_mismatch_frame_count=0`;
  - `weight_missing_frame_count=0`.

Resident component timing:

- `resident_light_read_upload_calibrate`: `3.3616618000669405 s`.
- `resident_registration_warp`: `0.2609440995147452 s`.
- `resident_local_normalization`: `0.3568277000449598 s`.
- `resident_integration`: `3.2981458000140265 s`.
- `resident_output_write`: `0.2789147000294179 s`.

## Commands Run

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_resident_frame_mask_contract.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_active_registered_inline_cosmetic_cuda_skips_excluded_frame
.venv\Scripts\ruff.exe check src\glass\engine\resident_frame_mask.py src\glass\engine\resident_cuda.py tests\test_resident_frame_mask_contract.py tests\test_resident_cuda_run.py
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract --out C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_mainline_audit.md --fail-on-not-green
.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned --candidate-run C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract --out C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_phase2_mainline_ab.json --markdown C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_phase2_mainline_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned --candidate-run C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract --out C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate691_frame_index_alignment\gate691_regression_gate.md --fail-on-failure
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `6 passed in 0.48 s`.
- Ruff: passed.
- Full pytest: `1435 passed in 66.84 s`.

## CUDA Status

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend: available.

## Known Limitations

- This is a resident pipeline correctness gate, not a performance optimization.
- It does not change calibration, registration, warp, local normalization,
  rejection, or integration math.
- It protects resident frame-level admission and weight alignment; pixel-level
  DQ, coverage, and rejection semantics remain governed by existing DQ/count-map
  contracts.

## Next Step

Continue with a substantive Phase 2 mainline performance gate:

- reduce `resident_light_read_upload_calibrate` through deeper native read,
  H2D, and calibration overlap; or
- redesign resident integration around a deterministic cooperative or segmented
  CUDA reducer while preserving Gate690/Gate691 contracts.

## Clean-Room Compliance

- No external proprietary implementation source was read, copied, summarized,
  or reworked.
- The real input data was used read-only.
- The new contract is derived from GLASS-owned resident stack indexing,
  frame-weight maps, frame-mask semantics, and GLASS-generated benchmark
  artifacts.
- CUDA remains optional; CPU-only tests still pass.
