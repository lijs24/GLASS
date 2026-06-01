# S2-Gate 108 Status: Contract-Gated 200-Light Catalog Sweep

## Gate

S2-Gate 108: Contract-Gated 200-Light Catalog Sweep

## Completed

- Ran a bounded real 200-light resident CUDA catalog-capacity sweep.
- Imported known-good science arguments from the S2-Gate 32 `run_command.txt`.
- Imported frame-count requirements from
  `benchmarks/phase2_m38_h_200_contract.json`.
- Imported compare normalization/defaults from
  `benchmarks/phase2_m38_h_200_contract.json`.
- Applied stricter promotion compare overrides:
  - `max_rms_diff=0.0016`
  - `max_abs_diff_p99=0.00042`
  - shape match required
- Swept `triangle_grid_top_per_cell=2,4`.
- Ran per-variant guardrails with pixel verification.
- Compared both outputs against the user-generated external reference master
  using candidate coverage maps and minimum coverage 190.
- Updated Phase 2 gate documentation and algorithm-source tracking.

## Commands

- `.\\.venv\\Scripts\\python.exe benchmarks\\bench_resident_prefetch_sweep.py --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_108_contract_gated_catalog_sweep --common-run-args-from-command C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\run_command.txt --frame-gate-from-contract benchmarks\\phase2_m38_h_200_contract.json --compare-from-contract benchmarks\\phase2_m38_h_200_contract.json --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes off --triangle-grid-top-per-cell 2,4 --baseline-total-seconds 15.493763700127602 --reference-master C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --reference-label WBPP_blackbox --compare-use-candidate-coverage-map --compare-max-rms 0.0016 --compare-max-p99 0.00042 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --max-variant-seconds 600 --max-guardrails-seconds 600`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `cmd.exe /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\\.venv\\Scripts\\cmake.exe --build build\\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_108_doctor.json --allow-cpu-only`

## Test Results

- Full pytest: `312 passed in 15.39s`
- Ruff full check: passed
- Native CUDA build: passed, `ninja: no work to do`

## CUDA Status

- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_108_doctor.json`

## Real 200-Light Artifacts

- Sweep root:
  `C:\\glass_runs\\phase2_s2_gate_108_contract_gated_catalog_sweep`
- Sweep summary:
  `C:\\glass_runs\\phase2_s2_gate_108_contract_gated_catalog_sweep\\resident_prefetch_sweep_summary.json`
- Sweep analysis:
  `C:\\glass_runs\\phase2_s2_gate_108_contract_gated_catalog_sweep\\resident_prefetch_sweep_analysis.json`
- Markdown analysis:
  `C:\\glass_runs\\phase2_s2_gate_108_contract_gated_catalog_sweep\\resident_prefetch_sweep_analysis.md`

## Sweep Results

| Variant | Total s | Speedup vs reference | Catalog s | Reg/warp s | Frame gate | Guardrails | Compare gate | RMS | P99 |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |
| `gt2` | 15.199100 | 71.881954x | 0.777179 | 2.342819 | passed | passed | failed: RMS | 0.001711219 | 0.000400466 |
| `gt4` | 15.427919 | 70.815837x | 1.084156 | 2.653843 | passed | passed | failed: P99 | 0.001560585 | 0.000437232 |

Top-level results:

- Frame gate: 2 passed, 0 failed.
- Guardrails: 2 passed, 0 failed.
- Compare gate: 0 passed, 2 failed.
- Promotion candidates: 0.
- Recommendation: `candidate_blocked_by_compare_gate`.

## Interpretation

`triangle_grid_top_per_cell=2` remains the fastest and lowest moving-catalog
variant in this bounded sweep. It also keeps the expected 200 input lights, 193
active/integrated lights, and 7 zero-weight frames. However, it fails strict
reference agreement on RMS. The `gt4` variant passes the RMS threshold but fails
the strict p99 threshold. Neither variant should be promoted as a default.

## Known Limitations

- This gate records benchmark evidence and does not change CUDA kernels or
  image math.
- The sweep uses two catalog-capacity variants only; it is deliberately bounded
  to keep evidence interpretable.
- The strict compare thresholds are exploratory promotion thresholds, not the
  broader benchmark-contract acceptance thresholds.

## Next Step

Search for a catalog/registration tuning point that preserves the `gt2`
catalog-time advantage while reducing RMS below 0.0016 and keeping p99 below
0.00042. Good next dimensions are NMS separation, NMS scan count, and possibly
grid shape, but no default should change until guardrails, frame gate, and
strict compare gate all pass.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned run commands, sweep artifacts, guardrail
artifacts, frame-accounting artifacts, coverage maps, and user-generated
reference output. It does not use proprietary implementation source and does
not modify input image directories.
