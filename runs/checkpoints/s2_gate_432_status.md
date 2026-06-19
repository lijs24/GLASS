# S2-Gate 432 Status: Real 200-Light Acceptance Parity

## Gate

- Gate: S2-Gate 432
- Scope: Phase 2 mainline runtime validation, not release/default-promotion/report-contract-only work.
- Objective: summarize the practical value boundary of Gate400-413, return to the real resident CUDA pipeline, and validate accepted-frame/timing/result behavior on the M38 H 200-light dataset.

## Gate400-413 Value Summary

- Gate400-413 are useful evidence-chain guardrails:
  - release evidence-chain fixture;
  - resident CUDA DQ provenance benchmark-contract wiring;
  - runtime/Phase2 status exposure;
  - release-promotion, default-promotion, Windows matrix, publish-preflight, and publication-audit handoff checks.
- They did not change image math, CUDA kernels, StackEngine execution defaults, DQ pixel semantics, real 200-light output, or runtime performance.
- Decision: stop adding pure release/default-promotion/report-only gates unless a missing evidence artifact directly blocks runtime validation.

## Completed

- Ran a real M38 H resident CUDA 200-light regression using the preserved plan:
  `C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json`.
- Dataset:
  - 200 light frames;
  - 20 bias frames;
  - 20 dark frames;
  - 20 flat frames;
  - image shape `9600x6422`.
- Pipeline:
  - backend `cuda`;
  - memory mode `resident`;
  - resident registration `similarity_cuda_triangle`;
  - auto-grid resident catalog default `8x8`, top 8 per cell;
  - `winsorized_sigma` rejection;
  - `weighting=none`;
  - local normalization off;
  - reference `LIGHT_H_0136`;
  - Lanczos3 resident warp;
  - audit output maps enabled.
- Discovery: the historical current `192 ok` + `7 excluded` accepted-frame set came from an explicit resident frame mask, not from automatic registration-quality rejection.
- Re-ran the real 200-light regression with the same explicit mask:
  `LIGHT_H_0100`, `LIGHT_H_0153`, `LIGHT_H_0154`, `LIGHT_H_0155`, `LIGHT_H_0156`, `LIGHT_H_0157`, `LIGHT_H_0158`.
- Generated report and compare artifacts for:
  - Gate432 masked vs historical current;
  - Gate432 masked vs Gate431 unmasked auto-grid.
- Wrote the strict JSON summary:
  `runs/checkpoints/s2_gate_432_acceptance_parity_summary.json`.

## Commands

- `.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\report.html"`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate432_masked_vs_old_current_compare.html" --glass-time-seconds 27.910495800024364 --reference-time-seconds 31.516450299997814 --glass-label "Gate432 auto-grid masked" --reference-label "Historical current masked"`
- `.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate431_auto_grid_top8_repeat_20260619\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate432_masked_vs_unmasked_auto_compare.html" --glass-time-seconds 27.910495800024364 --reference-time-seconds 28.351825499994447 --glass-label "Gate432 masked auto-grid" --reference-label "Gate431 unmasked auto-grid"`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_432_cuda_doctor.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Gate432 masked run directory:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619`.
- Status counts exactly matched historical current:
  `192 ok`, `7 excluded`, `1 reference`.
- Excluded frame IDs:
  `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`.
- Total elapsed: `27.910496 s`.
- Stage timings:
  - `light_read_upload_calibrate`: `17.339915 s`;
  - `resident_registration_warp`: `1.594249 s`;
  - `triangle_moving_catalog`: `0.951209 s`;
  - `resident_integration`: `0.297217 s`;
  - output write: `2.343207 s`.
- Estimated peak VRAM: `47.311736 GiB`.
- Gate432 masked vs historical current:
  - shape match: true;
  - p50/p90/p99 absolute delta: `2.1048` / `5.3775` / `19.2199` ADU;
  - relative RMS: `0.069624`;
  - robust fit-pixel RMS: `3.620003`;
  - speedup: `1.129197x`.
- Gate432 masked vs Gate431 unmasked auto-grid:
  - shape match: true;
  - p50/p90/p99 absolute delta: `1.4539` / `2.3806` / `4.1221` ADU;
  - relative RMS: `0.013693`;
  - robust fit-pixel RMS: `0.800978`;
  - speedup: `1.015812x`.
- Historical WBPP black-box time remains `1092.541 s`; Gate432 timing ratio against that record is `39.14445x`.
- Full pytest: `1007 passed in 37.10s`.

## CUDA

- CUDA wrapper importable: yes.
- Native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- CUDA doctor artifact: `runs/checkpoints/s2_gate_432_cuda_doctor.json`.

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_432_acceptance_parity_summary.json`.
- CUDA doctor:
  `runs/checkpoints/s2_gate_432_cuda_doctor.json`.
- Run state:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\run_state.json`.
- HTML report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\report.html`.
- Master:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate432_auto_grid_masked_20260619\integration\resident_master_H.fits`.
- Maps:
  `resident_coverage_map_H.fits`, `resident_low_rejection_map_H.fits`, `resident_high_rejection_map_H.fits`.
- Compare reports:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate432_masked_vs_old_current_compare.html`;
  `C:\glass_runs\final_m38_h_200\glass_s2_gate432_masked_vs_unmasked_auto_compare.html`.

## Known Limitations

- Gate432 uses an explicit frame mask to reproduce historical accepted-frame parity. It proves the policy boundary, but it does not yet implement automatic low-confidence frame rejection.
- Direct WBPP output comparison was not refreshed because the historical WBPP reference XISF path is not currently present on disk; this gate uses the previously recorded user-generated WBPP black-box time.
- Strict warp/rejection value parity still has residual deltas; the strongest remaining runtime-science target is automatic registration-quality gating plus resident warp/rejection numerical consistency.

## Next Step

- S2-Gate 433: implement or validate an automatic resident frame-quality decision contract so the real M38 H 200-light run can reject low-confidence frames without explicit masks, while recording per-frame reasons and preserving resident CUDA auto-grid performance.

## Clean-Room Compliance

- No PixInsight/WBPP source code was read, copied, summarized, or reworked.
- PixInsight/WBPP information used here is limited to user-generated black-box timing/output references already present in local run artifacts.
- Input image directories were treated as read-only.
