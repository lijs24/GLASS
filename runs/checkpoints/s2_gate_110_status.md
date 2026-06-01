# S2-Gate 110 Status: Contract-Gated 200-Light Grid-Shape Sweep

## Gate

S2-Gate 110 records a bounded 200-light resident CUDA grid-shape sweep around
the S2-Gate 109 near-miss settings. The purpose was to test whether changing
star-grid column density, while keeping the fast `triangle_grid_top_per_cell=2`
path, can recover strict reference image agreement without losing the resident
runtime gains.

## Completed

- Ran a four-variant real-data resident CUDA sweep over:
  - `star_grid_cols=20,28`
  - fixed `star_grid_rows=16`
  - `triangle_nms_min_separation_px=48,96`
  - fixed `triangle_grid_top_per_cell=2`
- Imported the known-good S2-Gate 32 science/tuning command.
- Imported frame and compare defaults from
  `benchmarks/phase2_m38_h_200_contract.json`.
- Required frame accounting gate, strict compare gate, candidate coverage maps,
  and per-variant guardrails with pixel verification.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`
- Wrote CUDA doctor evidence to
  `runs/checkpoints/s2_gate_110_doctor.json`.

## Run Command

```powershell
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep --common-run-args-from-command C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt --frame-gate-from-contract benchmarks\phase2_m38_h_200_contract.json --compare-from-contract benchmarks\phase2_m38_h_200_contract.json --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off --triangle-grid-top-per-cell 2 --triangle-nms-min-separation-px 48,96 --star-grid-cols 20,28 --star-grid-rows 16 --baseline-total-seconds 15.493763700127602 --reference-master C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --reference-label WBPP_blackbox --compare-use-candidate-coverage-map --compare-max-rms 0.0016 --compare-max-p99 0.00042 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --max-variant-seconds 600 --max-guardrails-seconds 600
```

## Artifacts

- Sweep root:
  `C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\resident_prefetch_sweep_summary.json`
- Analysis JSON:
  `C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\resident_prefetch_sweep_analysis.json`
- Analysis Markdown:
  `C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\resident_prefetch_sweep_analysis.md`
- Per-variant compare HTML/JSON and guardrail bundles are stored under the same
  sweep root.

## Results

| Rank | Variant | Total s | External Speedup | Catalog s | Registration/Warp s | Frames | Guardrails | Compare Gate | RMS | P99 |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| 1 | `g28x16_gt2_sep48` | 15.382999 | 71.022625x | 0.760188 | 2.333401 | 200/193/7 | passed | failed | 0.001678125 | 0.000434982 |
| 2 | `g28x16_gt2_sep96` | 15.448060 | 70.723508x | 0.767324 | 2.329182 | 200/193/7 | passed | failed | 0.001674460 | 0.000356952 |
| 3 | `g20x16_gt2_sep96` | 15.457323 | 70.681125x | 1.136383 | 2.720394 | 200/193/7 | passed | failed | 0.002802847 | 0.000368809 |
| 4 | `g20x16_gt2_sep48` | 15.773450 | 69.264557x | 1.085037 | 2.683905 | 200/193/7 | passed | failed | 0.001675648 | 0.000392369 |

Frame counts are `input/active/zero-weight`.

## Interpretation

- No variant is promoted.
- All variants preserved the 200/193/7 frame-accounting contract and passed
  guardrails with pixel verification.
- All variants failed the strict compare gate against the external reference.
- Reducing grid columns from 28 to 20 did not improve the outcome; it worsened
  catalog time and, for `sep96`, produced a much larger RMS delta.
- The best speed and lowest moving-catalog variant was `g28x16_gt2_sep48`, but
  it failed both RMS and p99 strict thresholds.
- The lowest registration/warp variant was `g28x16_gt2_sep96`; p99 passed, but
  RMS remained above the strict threshold.
- Next tuning should avoid repeating grid-column-only searches and instead
  target descriptor scoring, candidate density, or pixel-refine agreement.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_110_doctor.json --allow-cpu-only
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- `python -m pytest -q`: 312 passed in 15.34s.
- `python -m ruff check .`: all checks passed.
- Native CUDA build: `ninja: no work to do`.
- `glass doctor`: completed and wrote
  `runs/checkpoints/s2_gate_110_doctor.json`.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor recommendation: `cuda`.

## Known Limitations

- This gate is evidence and documentation only; it does not change algorithmic
  defaults.
- The sweep used warm/local run conditions and shared project artifacts, so it
  is valid for relative tuning evidence in this session, not for release-package
  cold-start timing claims.
- The strict compare thresholds are benchmark-promotion thresholds, not a claim
  that failed variants are unusable for every dataset.

## Next Step

S2-Gate 111 should focus on reducing the remaining image-agreement drift without
reopening grid-shape-only tuning. The most likely targets are resident descriptor
candidate scoring, richer candidate density controls, or a more agreement-driven
pixel-refine path.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned benchmark commands, GLASS artifacts,
user-provided image data, and user-generated external reference outputs only.
No proprietary implementation source was read, copied, summarized, or reworked.
