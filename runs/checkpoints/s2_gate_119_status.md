# S2-Gate 119 Status: Agreement Downweight Policy

## Gate

- Gate: S2-Gate 119
- Completed at: 2026-06-01T12:48:23+08:00
- Scope: add an optional non-hard-fail resident triangle agreement policy and
  test whether linear downweighting can preserve the 193-frame contract while
  improving strict image agreement.

## Completed

- Added `--resident-triangle-agreement-action` with choices:
  - `fail`: current default hard gate behavior.
  - `downweight`: keep the registered frame active with a
    `score / threshold` multiplier.
  - `flag`: record the agreement miss without changing frame weight.
- Added `--resident-triangle-agreement-min-weight` for a bounded downweight
  floor.
- Kept default behavior unchanged.
- Applied agreement downweight multipliers after resident frame-quality
  weighting and before local normalization/integration, so the policy composes
  with `simple_snr` rather than being overwritten by it.
- Recorded agreement action, minimum weight, downweighted-frame count, and
  per-frame agreement multipliers in resident artifacts and registration audit
  rows.
- Added unit coverage for the agreement policy helper and audit parsing.
- Ran deterministic 200-light downweight sweeps over thresholds
  `0.05,0.1,0.2,0.3,0.5,0.8,1.0` using the S2-Gate 118 contract conditions.

## Commands

```powershell
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate_119_agreement_downweight `
  --common-run-args-from-command C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96\run_command.txt `
  --common-run-arg=--resident-triangle-agreement-action `
  --common-run-arg=downweight `
  --frame-gate-from-contract benchmarks\phase2_m38_h_200_contract.json `
  --compare-from-contract benchmarks\phase2_m38_h_200_contract.json `
  --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 `
  --streams 4 --wave-frames 2 `
  --release-modes callback_queue --refill-modes queued `
  --star-catalog-deterministic-modes on `
  --triangle-min-agreement-scores 0.05,0.1 `
  --triangle-agreement-rms-scales 200 `
  --baseline-total-seconds 15.382999500259757 `
  --reference-master C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf `
  --reference-label WBPP_blackbox `
  --ignore-border-px 16 `
  --compare-use-candidate-coverage-map `
  --compare-require-shape-match `
  --compare-max-rms 0.0016 `
  --compare-max-p99 0.00042 `
  --guardrails `
  --guardrails-stack-scope integration `
  --guardrails-expected-integration-engine cuda_resident_stack `
  --guardrails-pixel-verify `
  --max-variant-seconds 300 `
  --max-guardrails-seconds 300

.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --out C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended `
  ... `
  --triangle-min-agreement-scores 0.2,0.3,0.5

.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --out C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high `
  ... `
  --triangle-min-agreement-scores 0.8,1.0

glass resident-registration-audit --run <variant-run-dir> --out <audit-json> --markdown <audit-md>
glass resident-registration-compare --sweep-summary <summary-json> --audit-root <audit-root> --out <compare-json> --markdown <compare-md> --fail-on-missing-audits

.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py src\glass\report\resident_registration_audit.py tests\test_resident_cuda_run.py tests\test_resident_registration_audit.py docs\phase2_algorithm_hardening.md docs\algorithm_sources.md
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_triangle_agreement_quality_scores_pixel_refinement tests\test_resident_cuda_run.py::test_resident_triangle_agreement_policy_can_downweight_without_hard_failure tests\test_resident_registration_audit.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
glass doctor --json runs\checkpoints\s2_gate_119_doctor.json
```

## Real 200-Light Result

All downweight variants preserved the benchmark frame contract and passed
guardrails:

| Threshold | Total s | Active / zero | Downweighted | Compare gate | RMS | P99 | Speedup vs reference |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 0.05 | 16.527 | 193 / 7 | 1 | failed | 0.001535208 | 0.000433332 | 66.10x |
| 0.10 | 16.140 | 193 / 7 | 2 | failed | 0.001532295 | 0.000432844 | 67.69x |
| 0.20 | 15.884 | 193 / 7 | 5 | failed | 0.001525953 | 0.000430183 | 68.78x |
| 0.30 | 15.848 | 193 / 7 | 6 | failed | 0.001520729 | 0.000428321 | 68.94x |
| 0.50 | 16.612 | 193 / 7 | 73 | failed | 0.001501103 | 0.000426863 | 65.77x |
| 0.80 | 17.907 | 193 / 7 | 192 | failed | 0.001493635 | 0.000440029 | 61.01x |
| 1.00 | 18.225 | 193 / 7 | 192 | failed | 0.001493354 | 0.000441020 | 59.95x |

The best tested p99 was `0.000426863` at threshold `0.5`, still above the
strict `0.00042` gate. High thresholds downweighted almost every active frame
and made p99 worse, even though RMS continued to improve.

## Artifacts

- Primary downweight sweep:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight`
- Extended downweight sweep:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended`
- High-threshold downweight sweep:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high`
- Each sweep root includes:
  - `resident_prefetch_sweep_summary.json`
  - `candidate_audits\`
  - `resident_registration_compare.json`
  - `resident_registration_compare.md`
- Doctor:
  `runs\checkpoints\s2_gate_119_doctor.json`

## Test Result

- Focused `ruff`: passed.
- Focused tests: `5 passed in 0.27s`.
- Full `ruff check .`: passed.
- Full `python -m pytest -q`: `321 passed in 17.80s`.
- Native CUDA build: passed, `ninja: no work to do`.
- `glass doctor`: passed.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- No downweight threshold is promoted.
- Linear `score / threshold` downweighting preserves frame accounting and
  avoids registration hard failures, but it still misses the strict p99
  comparison gate on the 200-light benchmark.
- The policy currently affects resident triangle agreement only.
- The sweep used hot local data and an established benchmark command; it is a
  controlled algorithm experiment, not a cold end-user runtime benchmark.

## Next Step

- S2-Gate 120 should add a non-linear or multi-signal agreement weighting mode,
  for example using agreement score plus pixel RMS/NCC buckets, then rerun the
  deterministic 200-light strict compare. A second promising direction is to
  inspect the p99 outlier locations for the `0.5` run before inventing more
  global weighting knobs.

## Clean-Room Compliance

- This gate used GLASS-owned code, CLI controls, resident artifacts, benchmark
  summaries, registration audits, and user-generated reference output only.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
