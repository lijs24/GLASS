# S2-Gate 155 Status: Runtime-Focused Candidate Sweep Execution

## Gate

- Gate: S2-Gate 155
- Status: green
- Completed at: 2026-06-17
- Scope: measured execution of the S2-Gate 154 runtime-only candidate sweep on the 200-light benchmark dataset.

## Completed Content

- Executed all five runtime-only variants planned in S2-Gate 154.
- For each variant, ran:
  - `glass run`
  - `glass compare` against the black-box reference
  - `glass compare` against the GLASS baseline
  - `glass acceptance-audit`
  - `glass candidate-comparison`
- Ran the generated `glass candidate-comparison-sweep` summary.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.
- Generated doctor report `runs\checkpoints\s2_gate_155_doctor.json`.

## Real-Data Artifacts

- Run directories: `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\runs\*`
- Compare artifacts: `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\compare\*`
- Acceptance artifacts: `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\acceptance\*`
- Candidate comparison artifacts: `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\comparison\*`
- Final sweep JSON: `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\candidate_runtime_sweep.json`
- Final sweep Markdown: `C:\glass_runs\phase2_s2_gate_154_runtime_sweep_plan\candidate_runtime_sweep.md`

## Commands Run

- Executed the S2-Gate 154 planned command chain for each variant:
  - `retry_settings_control`
  - `prefetch12_workers6`
  - `prefetch20_workers8`
  - `batch16_wave4`
  - `streams2_batch8`
- Executed generated `glass candidate-comparison-sweep`.
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_155_doctor.json`

## Test Results

- Full pytest: 388 passed in 22.46 s.
- Ruff: all checks passed.
- Doctor: completed successfully.

## CUDA Availability

- CUDA wrapper importable: true
- CUDA native extension loaded: true
- CUDA available: true
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Sweep Result

- Candidate count: 5
- Passed candidate count: 5
- Top candidate: `prefetch12_workers6`
- Final recommendation: `run_runtime_sweep_for_top_candidate`

| Rank | Variant | Runtime s | Speedup vs reference | Candidate/baseline runtime | Reference RMS | Reference p99 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `prefetch12_workers6` | 19.55820359988138 | 55.8610096484846 | 1.0922059380300138 | 0.0014945534429799121 | 0.00043544556712731865 |
| 2 | `prefetch20_workers8` | 19.902367299888283 | 54.895027487817124 | 1.1114253737456843 | 0.0014945534429799121 | 0.00043544556712731865 |
| 3 | `streams2_batch8` | 21.881362000014633 | 49.93021001157375 | 1.2219401125748188 | 0.0014945534429799121 | 0.00043544556712731865 |
| 4 | `retry_settings_control` | 26.454558600205928 | 41.29878016530184 | 1.4773251461234977 | 0.0014945534429799121 | 0.00043544556712731865 |
| 5 | `batch16_wave4` | 27.569034300278872 | 39.62928073940365 | 1.539561791283343 | 0.0014945534429799121 | 0.00043544556712731865 |

## Stage Timing Highlights

| Variant | Read/upload/calibrate s | Read wait s | H2D/calibrate/store s | Registration/warp s | Integration s | Output write s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `retry_settings_control` | 13.76471639983356 | 9.76233289949596 | 2.176637200638652 | 1.832213799469173 | 0.41583909979090095 | 2.372065699659288 |
| `prefetch12_workers6` | 7.335514300037175 | 4.253366302698851 | 2.3349030991084874 | 1.839749907143414 | 0.2987005999311805 | 2.5770955001935363 |
| `prefetch20_workers8` | 7.058610599953681 | 2.8800652022473514 | 3.1404418000020087 | 1.7854427993297577 | 0.6004337002523243 | 2.6206005001440644 |
| `batch16_wave4` | 11.258642499800771 | 3.6162201981060207 | 4.395840099547058 | 1.791653600987047 | 0.7285473002120852 | 5.949058400001377 |
| `streams2_batch8` | 8.50798669969663 | 3.3688519005663693 | 3.156540500931442 | 1.8205075962468982 | 0.7964481003582478 | 2.8221481000073254 |

## Interpretation

- Lowering prefetch from 16/8 to 12/6 recovered most of the Gate151 retry runtime penalty while preserving identical reference metrics and frame accounting.
- Increasing prefetch depth to 20/8 also helped, but was slightly slower than 12/6.
- Larger calibration batch/wave settings were slower in this benchmark.
- Lowering calibration streams to 2 was better than the original retry settings but slower than 12/6.
- The best measured setting is still 9.2% slower than the historical Gate119 baseline, so it should be confirmed before default promotion.

## Known Limitations

- This gate executed only runtime orchestration variants derived from the accepted soft-downweight candidate.
- It did not vary science parameters, rejection thresholds, registration settings, or output map policy.
- All candidates share identical reference compare metrics in this run; the sweep is primarily a runtime comparison.
- The best variant is a measured candidate, not a default.

## Next Step

- S2-Gate 156 should either run a narrow confirmation sweep around prefetch 10-14 / workers 5-7, or promote `prefetch12_workers6` behind an explicit opt-in/default policy gate with another acceptance run.

## Clean-Room Compliance

- This gate used GLASS commands, GLASS artifacts, and user-generated black-box reference outputs only.
- It did not read or summarize official PixInsight/WBPP source code.
- It did not modify input image directories.
- It did not alter CUDA kernels, resident integration defaults, or scientific formulas.
