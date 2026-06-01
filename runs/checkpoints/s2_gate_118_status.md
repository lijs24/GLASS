# S2-Gate 118 Status: Deterministic Agreement Threshold Sweep

## Gate

- Gate: S2-Gate 118
- Completed at: 2026-06-01T12:32:51+08:00
- Scope: rerun the agreement-threshold 200-light benchmark under explicit
  deterministic resident star-catalog control, then repeat candidate compare
  and rejection triage.

## Completed

- Added the S2-Gate 118 contract to
  `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md` with the deterministic agreement sweep
  result and clean-room boundary.
- Ran a 3-variant real M38 H-alpha 200-light resident CUDA sweep with
  `--star-catalog-deterministic-modes on`:
  - audit-only threshold, RMS scale 200
  - minimum agreement score `0.05`, RMS scale 200
  - minimum agreement score `0.1`, RMS scale 200
- Used the known-good S2-Gate 110 grid-shape command as common run arguments.
- Imported frame gate and compare normalization from
  `benchmarks/phase2_m38_h_200_contract.json`.
- Enabled candidate coverage maps, strict compare gate overrides, and
  per-variant guardrails with pixel verification.
- Generated per-variant resident registration audits.
- Joined candidate-audit statistics with compare metrics.
- Repeated S2-Gate 116 triage against the deterministic audit-only baseline.

## Commands

```powershell
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep `
  --common-run-args-from-command C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96\run_command.txt `
  --frame-gate-from-contract benchmarks\phase2_m38_h_200_contract.json `
  --compare-from-contract benchmarks\phase2_m38_h_200_contract.json `
  --prefetch-frames 16 `
  --prefetch-workers 8 `
  --batch-frames 8 `
  --streams 4 `
  --wave-frames 2 `
  --release-modes callback_queue `
  --refill-modes queued `
  --star-catalog-deterministic-modes on `
  --triangle-min-agreement-scores inherit,0.05,0.1 `
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

glass resident-registration-audit --run <variant-run-dir> --out <audit-json> --markdown <audit-md>

glass resident-registration-compare `
  --sweep-summary C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_prefetch_sweep_summary.json `
  --audit-root C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\candidate_audits `
  --out C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_registration_compare.json `
  --markdown C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_registration_compare.md `
  --fail-on-missing-audits

glass resident-registration-triage `
  --baseline-audit C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\candidate_audits\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agrs200_candidate_audit.json `
  --candidate-audit C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\candidate_audits\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p05_agrs200_candidate_audit.json `
  --candidate-audit C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\candidate_audits\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p1_agrs200_candidate_audit.json `
  --out C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_registration_triage.json `
  --markdown C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_registration_triage.md

.\.venv\Scripts\python.exe -m ruff check docs\phase2_algorithm_hardening.md docs\algorithm_sources.md benchmarks\bench_resident_prefetch_sweep.py tests\test_benchmarks.py tests\test_resident_registration_triage.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py -k "resident_prefetch_sweep" tests\test_resident_registration_triage.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
glass doctor --json runs\checkpoints\s2_gate_118_doctor.json
```

## Real 200-Light Result

| Variant | Total s | Active / zero | Guardrails | Frame gate | Compare gate | RMS | P99 | Speedup vs reference |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agrs200` | 15.574 | 193 / 7 | passed | passed | failed | 0.001541084 | 0.000437588 | 70.15x |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p05_agrs200` | 15.958 | 192 / 8 | passed | failed | passed | 0.001496759 | 0.000406988 | 68.46x |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p1_agrs200` | 15.953 | 191 / 9 | passed | failed | passed | 0.001500451 | 0.000382001 | 68.49x |

The deterministic audit-only baseline is now very close to the strict external
comparison target: RMS passes the `0.0016` gate, but p99 misses by
`0.000017588`. The thresholded variants pass strict RMS and p99, but both fail
the 193-frame benchmark contract by hard-rejecting required frames.

## Triage Result

- `0.05` extra rejected frame: `F000061`.
- `0.1` extra rejected frames: `F000061`, `F000159`.
- Reference catalog signature match: true for both threshold variants.
- Reference descriptor signature match: true for both threshold variants.
- Selected fit changes: 0.
- Recommendation: `threshold_rejects_required_frames`.

This means the S2-Gate 115 signature drift is resolved under deterministic
catalog control. The remaining blocker is the scalar agreement cutoff itself:
it improves image agreement by removing frames the benchmark contract still
requires.

## Artifacts

- Sweep root:
  `C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep`
- Sweep summary:
  `C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_prefetch_sweep_summary.json`
- Candidate audits:
  `C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\candidate_audits`
- Candidate/compare join:
  `C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_registration_compare.json`
- Rejection triage:
  `C:\glass_runs\phase2_s2_gate_118_deterministic_agreement_sweep\resident_registration_triage.json`
- Doctor:
  `runs\checkpoints\s2_gate_118_doctor.json`

## Test Result

- Focused `ruff`: passed.
- Focused benchmark/triage tests: `8 passed, 13 deselected in 1.84s`.
- Full `ruff check .`: passed.
- Full `python -m pytest -q`: `320 passed in 17.43s`.
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

- No agreement threshold is promoted.
- The deterministic baseline still misses the strict p99 target slightly.
- Hard agreement rejection can improve RMS/p99, but it changes the required
  frame accounting. The next policy should avoid a blunt scalar hard cutoff.
- The 200-light run uses hot local benchmark data and shared tuning context; it
  remains valid for relative algorithm decisions, not as a cold-distribution
  package benchmark.

## Next Step

- S2-Gate 119 should implement a non-promoting agreement quality policy that
  can mark or down-weight low-agreement frames without failing the 193-frame
  benchmark contract, then rerun the same deterministic 200-light comparison.

## Clean-Room Compliance

- This gate used GLASS-owned sweep commands, resident artifacts, candidate
  audits, triage outputs, timing ledgers, and user-generated benchmark/reference
  output only.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
