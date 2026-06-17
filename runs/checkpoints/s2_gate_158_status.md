# S2-Gate 158 Status: Prefetch/Worker Matrix Execution

## Gate

S2-Gate 158: Prefetch/Worker Matrix Execution.

## Completed Content

- Executed the S2-Gate 156 prefetch-frame/prefetch-worker 3x3 matrix with the
  S2-Gate 157 resumable executor.
- For each variant, executed:
  - resident CUDA integration on the 200-light benchmark plan
  - compare versus the user-generated black-box reference
  - compare versus the historical GLASS baseline
  - acceptance audit with the 200-light benchmark contract
  - candidate-comparison artifact generation
- Ran the generated candidate-comparison sweep summary.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --plan C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.json --out C:\glass_runs\phase2_s2_gate_158_prefetch_matrix_execution\prefetch_matrix_execution.json --skip-existing --glass-executable C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\glass.exe --cwd C:\Users\ljs\WORK\astro\gpuwbpp --fail-on-failed`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_158_doctor.json`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits`

## Test Results

- Full test suite: `397 passed in 22.03s`.
- Ruff: `All checks passed!`

## Matrix Result

Sweep status: `passed`.

Recommendation: `promote_top_candidate_to_broader_sweep`.

| Rank | Candidate | Elapsed s | Speedup vs reference | Runtime ratio vs baseline | Recommendation |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | `prefetch12_workers7` | 17.101234800000043 | 63.88667325940681x | 0.9549992718308159 | `eligible_for_broader_sweep` |
| 2 | `prefetch10_workers6` | 17.160483599999907 | 63.66609621654286x | 0.9583079545966194 | `eligible_for_broader_sweep` |
| 3 | `prefetch12_workers6` | 17.1972356 | 63.530036187909175x | 0.9603603288052008 | `eligible_for_broader_sweep` |
| 4 | `prefetch12_workers5` | 17.354161800000043 | 62.95556147229175x | 0.9691236963914536 | `eligible_for_broader_sweep` |
| 5 | `prefetch14_workers7` | 17.50216910000006 | 62.423177022098145x | 0.9773889980131623 | `eligible_for_broader_sweep` |
| 6 | `prefetch14_workers6` | 17.567721300000017 | 62.19025116251127x | 0.9810496870802972 | `eligible_for_broader_sweep` |
| 7 | `prefetch10_workers7` | 17.661264500000016 | 61.860859396562404x | 0.9862735021398228 | `eligible_for_broader_sweep` |
| 8 | `prefetch14_workers5` | 17.808660499999974 | 61.3488588880675x | 0.9945046663988348 | `eligible_for_broader_sweep` |
| 9 | `prefetch10_workers5` | 29.428168000000028 | 37.12568855798291x | 1.6433830270148022 | `eligible_but_needs_runtime_sweep` |

All variants passed acceptance. The top candidate has the same reference
agreement metrics as the other passing variants in this matrix:

- reference RMS diff: `0.0014945534429799121`
- reference RMS relative delta: `0.000614575672043593`
- reference abs diff p99: `0.00043544556712731865`
- p99 relative delta: `-0.01041714662729686`

## Artifacts

- Execution audit:
  `C:\glass_runs\phase2_s2_gate_158_prefetch_matrix_execution\prefetch_matrix_execution.json`
- Executor stdout:
  `C:\glass_runs\phase2_s2_gate_158_prefetch_matrix_execution\executor_stdout.log`
- Executor stderr:
  `C:\glass_runs\phase2_s2_gate_158_prefetch_matrix_execution\executor_stderr.log`
- Sweep JSON:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep.json`
- Sweep Markdown:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep.md`
- Per-variant runs:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\runs\`
- Per-variant compares:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\compare\`
- Per-variant acceptance artifacts:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\acceptance\`
- Per-variant candidate-comparison artifacts:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\comparison\`
- Doctor report:
  `runs/checkpoints/s2_gate_158_doctor.json`

## CUDA Status

- `glass doctor`: CUDA available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB reported by GLASS doctor
- Driver: 596.21
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`
- `nvidia-smi` after execution:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 596.21, 97887, 1535, 0, 39`

## Known Limitations

- Gate158 is benchmark evidence only. It does not promote
  `prefetch12_workers7` to defaults or rewrite recommended command templates.
- The first matrix cell, `prefetch10_workers5`, was much slower than the
  others and should not be promoted without rerun evidence.
- The measured result is specific to the current 200-light M38 H-alpha
  benchmark, current GPU, current disk/cache state, and current resident
  science settings.

## Next Step

S2-Gate 159 should either promote `prefetch12_workers7` as a documented
runtime preset after one confirmation run, or run a narrower confirmation sweep
around `prefetch12_workers7` and `prefetch10_workers6` to separate real
performance from run-to-run noise.

## Clean-Room Compliance

Compliant. This gate executed GLASS commands and compared GLASS outputs against
user-generated black-box reference artifacts. It did not read external
implementation source, did not modify input image directories, and did not
change scientific defaults.
