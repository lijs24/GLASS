# S2-Gate 476 Status: Clean 200-Light Resident A/B Execution

- Gate: S2-Gate 476
- Status: green checkpoint
- Date: 2026-06-22

## Completed

- Added wait-ready controls to `glass resident-ab-matrix-execute`:
  - `--wait-ready-timeout-s`
  - `--wait-ready-interval-s`
  - `--wait-ready-consecutive-samples`
- Added default replacement for planned `glass` commands with the current
  `glass.exe`.
- Added default replacement for planned `python` commands with the current
  virtual-environment interpreter.
- Captured subprocess launch errors as failed execution steps instead of
  allowing the executor to crash without an artifact.
- Ran the real M38 H-alpha 200-light A/B matrix after six consecutive clean GPU
  readiness samples.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests docs
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_ab_matrix_plan.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_475_ab_matrix_plan_blocked.json --out runs\checkpoints\s2_gate_476_wait_ready_execution_probe.json --wait-ready-timeout-s 3 --wait-ready-interval-s 1 --wait-ready-consecutive-samples 999
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_475_ab_matrix_plan_blocked.json --out runs\checkpoints\s2_gate_476_ab_matrix_execution_real.json --wait-ready-timeout-s 180 --wait-ready-interval-s 5 --wait-ready-consecutive-samples 6 --fail-on-failed --fail-on-blocked
```

## Test Results

- `ruff check src tests docs`: passed.
- Focused pytest:
  - `tests/test_resident_ab_matrix_plan.py`
  - `tests/test_cli_smoke.py::test_cli_help_commands`
  - result: `11 passed in 1.60s`

Full pytest was run after the checkpoint edits and is recorded in the final
Gate476 summary:

- `python -m pytest -q`: `1117 passed in 40.65s`

## Clean Readiness

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Driver: `596.21`
- Required consecutive ready samples: `6`
- Observed consecutive ready samples: `6`
- GPU utilization during all readiness samples: `0%`
- Free VRAM at launch: `97062 MiB`
- C:\ target free space at launch: `64.94022369384766 GiB`

## Real A/B Result

Reference WBPP black-box elapsed time:

- `1092.541 s`

Baseline `throughput_v1_lanczos3_parity`:

- GLASS elapsed: `30.953057600010652 s`
- Speedup vs WBPP: `35.29670684293315x`
- Acceptance: passed
- Active/weighted frames: `193`
- Zero-weight frames: `7`
- Estimated peak VRAM: `49.608429938554764 GiB`
- WBPP-reference coverage fraction: `0.960532609259836`
- WBPP-reference RMS: `0.0017794216505176163`
- WBPP-reference p99 abs diff: `0.00042621337808668863`

Candidate `throughput_v2_fused_bilinear`:

- GLASS elapsed: `30.661248599993996 s`
- Speedup vs WBPP: `35.63263239058744x`
- Acceptance: passed
- Active/weighted frames: `193`
- Zero-weight frames: `7`
- Estimated peak VRAM: `47.3117358982563 GiB`
- WBPP-reference coverage fraction: `0.9680247262015986`
- WBPP-reference RMS: `0.0018004970117125889`
- WBPP-reference p99 abs diff: `0.0004224973497912281`

Candidate vs baseline:

- Coverage fraction: `0.9680247262015986`
- RMS: `4.5849533818006405` ADU
- Relative RMS: `0.016454569155982254`
- p50 abs diff: `0.6654815673828125` ADU
- p99 abs diff: `2.975449752807606` ADU
- p99.9 abs diff: `9.921587371827627` ADU
- Robust-fit RMS: `1.0147844203102725` ADU
- Robust-fit p99 abs diff: `2.7769658584364603` ADU

## Performance Interpretation

- Both variants are cleanly much faster than the WBPP black-box reference.
- The fused bilinear candidate is only `0.2918090000166558 s` faster than the
  Lanczos3 registered-stack baseline on this dataset.
- The candidate saves about `2.296694040298464 GiB` estimated peak VRAM.
- Current dominant runtime remains FITS read/upload/calibration overlap:
  - baseline light read/upload/calibrate wall time: `14.113322600023821 s`
  - candidate light read/upload/calibrate wall time: `14.069710099953227 s`
  - cumulative native FITS read time: about `20.4 s`
- The next optimization should target resident I/O/calibration scheduling,
  pinned-memory/prefetch efficiency, and reducing per-run orchestration before
  promoting fused integration defaults.

## Artifacts

- `runs/checkpoints/s2_gate_476_ab_matrix_execution_real.json`
- `runs/checkpoints/s2_gate_476_wait_ready_execution_probe.json`
- `runs/checkpoints/s2_gate_476_real_ab_summary.json`
- `runs/checkpoints/s2_gate_476_status.md`
- Baseline report:
  - `C:\glass_runs\phase2_s2_gate475_ab_matrix_real\reports\throughput_v1_lanczos3_parity_report.html`
- Candidate report:
  - `C:\glass_runs\phase2_s2_gate475_ab_matrix_real\reports\throughput_v2_fused_bilinear_report.html`
- Candidate-vs-baseline compare:
  - `C:\glass_runs\phase2_s2_gate475_ab_matrix_real\compare\throughput_v2_fused_bilinear_vs_throughput_v1_lanczos3_parity.html`

## Known Limitations

- The fused bilinear candidate passed WBPP-reference acceptance, but it is not
  parity-equivalent to the Lanczos3 baseline. It remains opt-in.
- The speed advantage of fused bilinear is small on this clean run, so default
  promotion is not justified.
- Full release/default-promotion claims should wait for additional clean runs
  or a stronger interpolation-consistent fused route.

## Next Step

Use this clean benchmark to drive the next substantive optimization gate:

- target resident I/O/calibration scheduling first;
- keep `throughput-v1` Lanczos3 as the parity baseline;
- keep `throughput-v2-fused` bilinear as an explicit candidate until
  candidate-vs-baseline numerical policy is settled.

## Clean-Room Compliance

- This gate used GLASS-owned code and artifacts plus user-generated WBPP
  black-box timing/output metadata.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Original image directories were not modified.
