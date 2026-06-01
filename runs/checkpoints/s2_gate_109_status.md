# S2-Gate 109 Status: Contract-Gated 200-Light NMS Separation Sweep

## Gate

S2-Gate 109: Contract-Gated 200-Light NMS Separation Sweep

## Completed

- Ran a bounded real 200-light resident CUDA NMS separation sweep.
- Kept the faster catalog-capacity setting from S2-Gate 108:
  `triangle_grid_top_per_cell=2`.
- Swept `triangle_nms_min_separation_px=48,64,80,96`.
- Imported known-good science arguments from the S2-Gate 32 `run_command.txt`.
- Imported frame-count and compare defaults from
  `benchmarks/phase2_m38_h_200_contract.json`.
- Applied strict promotion compare overrides:
  - `max_rms_diff=0.0016`
  - `max_abs_diff_p99=0.00042`
  - shape match required
- Ran per-variant guardrails with pixel verification.
- Compared every output against the user-generated external reference master
  using candidate coverage maps and minimum coverage 190.
- Updated Phase 2 gate documentation and algorithm-source tracking.

## Commands

- `.\\.venv\\Scripts\\python.exe benchmarks\\bench_resident_prefetch_sweep.py --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_109_nms_separation_sweep --common-run-args-from-command C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\run_command.txt --frame-gate-from-contract benchmarks\\phase2_m38_h_200_contract.json --compare-from-contract benchmarks\\phase2_m38_h_200_contract.json --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off --triangle-grid-top-per-cell 2 --triangle-nms-min-separation-px 48,64,80,96 --baseline-total-seconds 15.493763700127602 --reference-master C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --reference-label WBPP_blackbox --compare-use-candidate-coverage-map --compare-max-rms 0.0016 --compare-max-p99 0.00042 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --max-variant-seconds 600 --max-guardrails-seconds 600`

## Real 200-Light Artifacts

- Sweep root:
  `C:\\glass_runs\\phase2_s2_gate_109_nms_separation_sweep`
- Sweep summary:
  `C:\\glass_runs\\phase2_s2_gate_109_nms_separation_sweep\\resident_prefetch_sweep_summary.json`
- Sweep analysis:
  `C:\\glass_runs\\phase2_s2_gate_109_nms_separation_sweep\\resident_prefetch_sweep_analysis.json`
- Markdown analysis:
  `C:\\glass_runs\\phase2_s2_gate_109_nms_separation_sweep\\resident_prefetch_sweep_analysis.md`

## Sweep Results

| Variant | Total s | Speedup vs reference | Catalog s | Reg/warp s | Frame gate | Guardrails | Compare gate | RMS | P99 |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| `sep64` | 15.251409 | 71.635412x | 0.780016 | 2.315624 | passed | passed | failed: RMS | 0.001690218 | 0.000407245 |
| `sep48` | 15.270949 | 71.543752x | 0.756025 | 2.285952 | passed | passed | failed: RMS | 0.001604798 | 0.000408962 |
| `sep96` | 15.417518 | 70.863609x | 0.754183 | 2.362167 | passed | passed | failed: P99 | 0.001562837 | 0.000421612 |
| `sep80` | 15.593228 | 70.065093x | 0.753048 | 2.361534 | passed | passed | failed: RMS | 0.001693859 | 0.000407182 |

Top-level results:

- Frame gate: 4 passed, 0 failed.
- Guardrails: 4 passed, 0 failed.
- Compare gate: 0 passed, 4 failed.
- Promotion candidates: 0.
- Recommendation: `candidate_blocked_by_compare_gate`.

## Interpretation

NMS separation alone does not produce a promotable `triangle_grid_top_per_cell=2`
variant under the strict compare gate. The useful edge cases are:

- `sep48`: lowest registration/warp time and safe p99, but RMS is only slightly
  above threshold (`0.001604798 > 0.0016`).
- `sep96`: RMS passes with margin, but p99 is only slightly above threshold
  (`0.000421612 > 0.00042`).

This narrows the next search to combinations of separation, grid shape, and
candidate density rather than a one-dimensional separation change.

## Test Results

- Full pytest: `312 passed in 15.45s`
- Ruff full check: passed
- Native CUDA build: passed, `ninja: no work to do`
- GLASS doctor report: `runs/checkpoints/s2_gate_109_doctor.json`

## CUDA Status

- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Known Limitations

- This gate records benchmark evidence and does not change CUDA kernels or
  image math.
- No NMS separation value is promoted.
- The sweep keeps `triangle_grid_top_per_cell=2` fixed; grid shape and candidate
  density remain for a follow-up gate.

## Next Step

Run a small two-dimensional sweep around the near-miss points:

- `sep48` with adjusted grid shape or candidate density to lower RMS.
- `sep96` with adjusted grid shape or candidate density to lower p99.

No default should change until guardrails, frame gate, and strict compare gate
all pass.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned run commands, sweep artifacts, guardrail
artifacts, frame-accounting artifacts, coverage maps, and user-generated
reference output. It does not use proprietary implementation source and does
not modify input image directories.
