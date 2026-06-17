# S2-Gate 151 Repair Status - Soft Downweight Candidate Accepted

## Gate

S2-Gate 151: execute and accept the `agreement_soft_downweight` candidate from
the S2-Gate 150 rejection/registration experiment plan.

## Status

Green after retry.

The first S2-Gate 151 run is preserved in
`runs/checkpoints/s2_gate_151_status.md` as a failed anomalous runtime record.
It used an incorrect initial compare offset/min-coverage and, after corrected
compare, still failed the performance contract with a `483.80420529982075 s`
runtime. A retry of the same candidate in a new run directory completed in
`26.005688100121915 s` and passed the benchmark acceptance contract.

## Completed

- Re-ran the `agreement_soft_downweight` candidate in an isolated retry
  directory.
- Kept the same 200-light resident CUDA benchmark inputs and candidate
  behavior:
  - `--resident-triangle-agreement-action downweight`
  - `--resident-triangle-min-agreement-score 0.6`
  - `--integration-rejection winsorized_sigma`
  - `--resident-output-maps audit`
- Used the benchmark contract compare parameters:
  - `glass_scale=8.764434957115609e-06`
  - `glass_offset=0.0006274500691899127`
  - `min_coverage=190`
- Ran compare against the user-generated WBPP black-box reference.
- Ran acceptance-audit with `benchmarks\phase2_m38_h_200_contract.json`.
- Ran full pytest, ruff, and CUDA doctor after the successful retry.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- Retry run:
  `C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1`
- Retry compare HTML:
  `C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_vs_reference.html`
- Retry compare JSON:
  `C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_vs_reference.json`
- Retry acceptance audit:
  `C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_acceptance.json`
- Doctor report:
  `runs\checkpoints\s2_gate_151_repair_doctor.json`

## Real-Data Results

- Candidate acceptance status: `passed`.
- Candidate run elapsed: `26.005688100121915 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP: `42.011616681462776`.
- Integrated frames: `193`.
- Zero-weight frames: `7`.
- Corrected compare:
  - RMS diff: `0.0014945534429799121`.
  - Abs diff P99: `0.00043544556712731865`.
  - Abs diff P50: `6.217684131115675e-05`.
  - Abs diff P90: `0.0001238255063071847`.
  - Abs diff P999: `0.003971506122501051`.
  - Mean diff: `1.5098402628873614e-05`.
  - Relative RMS diff: `0.39387848661696695`.

Dominant retry timings:

- `master_build_or_load`: `1.3055161000229418 s`.
- `light_read_upload_calibrate`: `12.485881200060248 s`.
- `light_h2d_calibrate_store`: `1.9326748009771109 s`.
- `light_calibrate_store`: `1.9090888442993168 s`.
- `resident_registration_warp`: `1.870910997968167 s`.
- `resident_integration`: `0.586593700107187 s`.
- `output_write`: `2.402434800285846 s`.

The retry runtime is close to the existing fast resident benchmark path and
well inside the contract limit. The failed first run is best treated as an
anomalous runtime incident, not as evidence that the soft-downweight candidate
is inherently slow.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-star-grid-cols 28 --resident-star-grid-rows 16 --resident-triangle-grid-top-per-cell 2 --resident-triangle-nms-min-separation-px 96.0 --resident-triangle-agreement-action downweight --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-prefetch-refill-mode queued --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue --resident-star-catalog-deterministic --resident-triangle-min-agreement-score 0.6 --resident-triangle-agreement-rms-scale 200.0
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_vs_reference.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_vs_reference.json --out C:\glass_runs\phase2_s2_gate_151_repair\agreement_soft_downweight_retry1_acceptance.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_151_repair_doctor.json
```

## Test Results

- Full pytest: `382 passed in 21.98s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_151_repair_doctor.json`.
- Acceptance-audit: `passed`.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Recommended package: `cuda`.

## Known Limitations

- Passing S2-Gate 151 does not make `agreement_soft_downweight` a default
  policy. It is one measured candidate.
- The initial failed run remains unexplained beyond being an anomalous runtime
  incident; future measured candidate runs should record GPU/process state when
  runtime is unexpectedly slow.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 152 should compare `agreement_soft_downweight` against the baseline
run and the other planned candidates at the artifact level. It should answer
whether the candidate improves the residual/rejection-registration hotspot
without damaging full-frame agreement, DQ maps, frame accounting, or runtime.

## Clean-Room Compliance

Compliant. This gate uses GLASS commands, GLASS artifacts, and user-generated
WBPP black-box reference outputs only. No proprietary implementation source was
read, copied, summarized, or reworked.
