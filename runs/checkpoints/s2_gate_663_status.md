# S2-Gate 663 Status: Real 200-Light Star-Protected CUDA Source-DQ A/B

## Gate

S2-Gate 663

## Completed

- Ran the real M38 200-light resident CUDA benchmark with the new opt-in `cosmetic_star_cuda` detector.
- Matched the Gate660 source-DQ policy shape:
  - `--resident-inline-source-dq-policy conservative`
  - `--resident-inline-source-dq-admission active_registered`
  - same plan, calibration policy, resident registration parameters, output maps, and shared master cache.
- Compared the candidate against the Gate660 conservative active-registered `cosmetic_cuda` baseline.
- Wrote real A/B artifacts under:
  `C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000`.
- Updated Phase 2 validation and algorithm-source documentation.

## Commands Run

- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_star_cuda --resident-inline-source-dq-policy conservative --resident-inline-source-dq-admission active_registered --resident-mainline-framework-gate warn --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 0 --resident-mainline-min-source-dq-applied-samples 0 --out C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\star_cuda_conservative_active_warn`
- `.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict --candidate-run C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\star_cuda_conservative_active_warn --out C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\gate663_vs_gate660_regression.json --markdown C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\gate663_vs_gate660_regression.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10`
- FITS output diff summary script writing:
  `C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\gate663_vs_gate660_output_diff_summary.json`.
- A/B summary script writing:
  `C:\glass_runs\phase2_s2_gate663_star_cuda_real\runs_20260625_230000\s2_gate_663_real_ab_summary.json`.
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`

## Test And Validation Results

- Candidate real run completed through integration.
- Ruff:
  `All checks passed`.
- Full pytest:
  `1398 passed in 61.99s`.
- Candidate elapsed:
  `21.259431299986318 s`.
- Gate660 baseline elapsed:
  `18.553858600207604 s`.
- Candidate/Gate660 ratio:
  `1.1458226430457135`.
- Candidate speedup versus the `1092.541 s` black-box reference:
  `51.39088551257263x`.
- Gate660 speedup versus the same reference:
  `58.884840266475636x`.
- Required resident artifacts/contracts passed in the regression gate.
- Frame accounting matched:
  - active frames: `193`
  - masked frames: `7`
  - masked frame max threshold: `10`
- `resident-regression-gate` status:
  - overall `passed=false`
  - failed check: `resident_determinism_passed`
  - reason: expected output change from the opt-in star-protected detector.

## Source-DQ Results

- Candidate status counts:
  - `applied=10`
  - `skipped_high_invalid_fraction=183`
  - `skipped_admission_policy=7`
- Baseline status counts were identical.
- Gate660 invalid samples:
  `147179`.
- Gate663 invalid samples:
  `146985`.
- Gate663 star protection summary:
  - `star_count_total=24256`
  - `star_protected_hot_pixels=186`
  - `star_protected_cold_pixels=8`
  - `star_protected_cosmetic_pixels=194`
  - `applied_star_protected_cosmetic_pixels=194`
- The `194` protected samples exactly explain the invalid-sample difference versus Gate660.

## Output Difference Versus Gate660

- Master:
  - shape matched: `6422 x 9600`
  - changed pixels: `7718931`
  - changed fraction: `0.12520325638430396`
  - RMS: `0.1315372868894881`
  - p99 absolute difference: `0.14057159423828125`
  - max absolute difference: `449.1663932800293`
- Weight map:
  - changed fraction: `0.0014720881345375273`
  - max absolute difference: `2.0`
- Coverage map:
  - changed fraction: `0.0014720881345375273`
  - max absolute difference: `2.0`
- Low rejection map:
  - changed fraction: `0.0007988814491850929`
  - max absolute difference: `2.0`
- High rejection map:
  - changed fraction: `0.0009832574224021592`
  - max absolute difference: `2.0`
- DQ map:
  - changed fraction: `0.0011994738139728019`
  - max absolute difference: `768.0`

## Runtime Diagnosis

Compared with Gate660, the candidate is slower mostly in `light_read_upload_calibrate`:

- `light_read_upload_calibrate`: `7.715091700083576 s` -> `10.374038000009023 s`.
- `light_h2d_calibrate_store`: `0.7419246999779716 s` -> `0.931884299730882 s`.
- `resident_registration_warp`: `0.2607602991629392 s` -> `0.2680024995934218 s`.
- `resident_integration`: `3.294742300058715 s` -> `3.3551198000786826 s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- This gate is not a default promotion.
- The run is intentionally not deterministic against Gate660 because `cosmetic_star_cuda` changes source-DQ semantics by protecting 194 candidate cosmetic samples.
- Runtime is `14.6%` slower than Gate660, mainly because star catalogs and star-protected apply are not batched yet.
- The master has a small RMS drift but a non-trivial max outlier; later gates should inspect the worst changed pixels if this mode becomes a promotion candidate.

## Next Step

Implement batched resident star catalog upload/apply for `cosmetic_star_cuda`, or move catalog generation fully device-resident across the batch, then rerun the same Gate663 real A/B. Promotion should require lower runtime overhead and an explicit source-DQ science acceptance threshold rather than bit-identical output.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned code, GLASS-generated artifacts, the existing user-owned M38 benchmark data, and the existing user-generated black-box reference elapsed time. It does not inspect, copy, summarize, or rework external/proprietary implementation source, and it does not modify input image directories.
