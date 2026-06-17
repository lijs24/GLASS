# S2-Gate 151 Status - Soft Downweight Candidate Execution

## Gate

S2-Gate 151: execute the `agreement_soft_downweight` candidate from the
S2-Gate 150 rejection/registration experiment plan.

## Status

Failed / not promotable.

The candidate completed integration and passed the corrected numerical compare
thresholds, but failed the benchmark acceptance contract on runtime and
minimum speedup. Per gate rules, no further candidate is promoted and no later
gate should build on this candidate as accepted.

## Completed

- Executed the `agreement_soft_downweight` resident CUDA candidate from the
  S2-Gate 150 plan.
- Ran compare against the same user-generated WBPP black-box reference.
- Ran acceptance-audit with the benchmark contract.
- Discovered the first compare/acceptance attempt used incorrect contract
  parameters (`glass_offset=0`, `min_coverage=1`).
- Re-ran compare/acceptance with the contract parameters:
  - `glass_scale=8.764434957115609e-06`
  - `glass_offset=0.0006274500691899127`
  - `min_coverage=190`
- Confirmed the corrected run passes numerical compare but fails performance
  acceptance.

## Real-Data Artifacts

- Candidate run:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight`
- Initial compare report:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference.html`
- Initial acceptance audit:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\acceptance\agreement_soft_downweight_acceptance.json`
- Corrected contract compare report:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference_contract.html`
- Corrected contract acceptance audit:
  `C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\acceptance\agreement_soft_downweight_acceptance_contract.json`

## Real-Data Results

- Candidate run elapsed: `483.80420529982075 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP: `2.258229647513989`.
- Contract required minimum speedup vs WBPP: `20.0`.
- Contract runtime baseline: `30.361440100008622 s`.
- Contract maximum allowed runtime: `39.46987213001121 s`.
- Frame accounting:
  - Input light frames: `200`.
  - Integrated frames: `193`.
  - Zero-weight frames: `7`.
  - Registration accepted frames: `193`.
- Corrected compare:
  - RMS diff: `0.0014945534429799121`.
  - Abs diff P99: `0.00043544556712731865`.
  - Mean diff: `1.5098402628873614e-05`.
  - Abs diff P50: `6.217684131115675e-05`.
  - Abs diff P90: `0.0001238255063071847`.
  - Abs diff P999: `0.003971506122501051`.

Failed acceptance checks after corrected compare:

| check | actual | required |
| --- | ---: | ---: |
| `contract_max_runtime_vs_release_baseline` | `483.80420529982075 s` | `<= 39.46987213001121 s` |
| `contract_minimum_speedup_vs_reference` | `2.258229647513989` | `>= 20.0` |

The corrected numerical compare is good, but the runtime is far outside the
release benchmark contract.

## Performance Diagnosis

Dominant current timing from `resident_artifacts.json`:

- `light_read_upload_calibrate`: `359.76352230040357 s`.
- `light_h2d_calibrate_store`: `293.73334669927135 s`.
- `light_calibrate_store`: `273.3016881866455 s`.
- `master_build_or_load`: `62.27954580029473 s`.
- `resident_registration_warp`: `61.668716395273805 s`.
- `resident_integration`: `21.9391489000991 s`.
- `output_write`: `2.7968108002096415 s`.

The failure is dominated by the I/O/upload/calibration path, with additional
registration/warp and master-cache regressions. This must be addressed before
running more heavy candidates as acceptance gates.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-prefetch-refill-mode queued --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.6 --resident-triangle-agreement-rms-scale 200.0
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0 --glass-coverage-map C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight\integration\resident_coverage_map_H.fits --min-coverage 1.0
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference.json --out C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\acceptance\agreement_soft_downweight_acceptance.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference_contract.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\runs\agreement_soft_downweight --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\compare\agreement_soft_downweight_vs_reference_contract.json --out C:\glass_runs\phase2_s2_gate_150_rejection_registration_plan\acceptance\agreement_soft_downweight_acceptance_contract.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json
```

## Test Results

- No code was changed for S2-Gate 151.
- The latest full validation before this experiment was S2-Gate 150:
  `382 passed in 25.80s`.
- Candidate acceptance status: `failed`.

## CUDA Status

- CUDA was available for the candidate run.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- The run completed with CUDA resident integration, but failed the performance
  contract.

## Known Limitations

- This is a failed candidate experiment, not a green gate.
- The initial compare/acceptance attempt used incorrect compare offset and
  coverage threshold; corrected artifacts are the authoritative numerical
  evidence.
- No later candidate should be run as an acceptance gate until the runtime
  regression source is understood or a cheaper bounded experiment is defined.

## Next Step

Do not promote `agreement_soft_downweight`. The next useful work is a Gate151
repair path focused on runtime: explain why this run spent about `360 s` in
light read/upload/calibration and about `62 s` in master cache load/build, then
rerun the same candidate only if the runtime path can return near the existing
release benchmark contract.

## Clean-Room Compliance

Compliant. This experiment uses GLASS commands, GLASS artifacts, and
user-generated WBPP black-box reference outputs only. No proprietary
implementation source was read, copied, summarized, or reworked.
