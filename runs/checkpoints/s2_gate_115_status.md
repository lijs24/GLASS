# S2-Gate 115 Status: Contract-Gated Agreement Threshold Sweep

## Gate

- Gate: S2-Gate 115
- Completed at: 2026-06-01T12:06:18+08:00
- Scope: execute a bounded real 200-light resident CUDA sweep over the S2-Gate
  113 triangle agreement threshold, then audit candidate statistics and compare
  each variant against the same external reference master.

## Completed

- Added the S2-Gate 115 contract to `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md` with the executed agreement-threshold
  sweep result and clean-room boundary.
- Ran a 3-variant real 200-light M38 H-alpha resident CUDA sweep:
  - `inherit` threshold with RMS scale 200
  - minimum agreement score `0.05` with RMS scale 200
  - minimum agreement score `0.1` with RMS scale 200
- Used the known-good S2-Gate 110 grid-shape command as common run arguments.
- Imported frame gate and compare normalization from
  `benchmarks/phase2_m38_h_200_contract.json`.
- Enabled candidate coverage maps, strict compare gate overrides, and
  per-variant guardrails with pixel verification.
- Generated per-variant resident registration audits.
- Joined candidate-audit statistics with compare metrics.

## Commands

```powershell
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep `
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
  --sweep-summary C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\resident_prefetch_sweep_summary.json `
  --audit-root C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\candidate_audits `
  --out C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\resident_registration_compare.json `
  --markdown C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\resident_registration_compare.md `
  --fail-on-missing-audits

.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
glass doctor --json runs\checkpoints\s2_gate_115_doctor.json
```

An initial doctor command with obsolete `--json --out` syntax failed and was
immediately rerun with the current CLI syntax shown above.

## Real 200-Light Result

| Variant | Total s | Active / zero | Guardrails | Frame gate | Compare gate | RMS | P99 | Speedup vs reference |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agrs200` | 18.453 | 193 / 7 | passed | passed | failed | 0.001900184 | 0.000388442 | 59.21x |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agr0p05_agrs200` | 18.277 | 192 / 8 | passed | failed | failed | 0.001600890 | 0.000378563 | 59.78x |
| `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agr0p1_agrs200` | 18.795 | 189 / 11 | passed | failed | failed | NaN at >=190 coverage | n/a | 58.13x |

The `0.05` threshold moved the reference RMS almost onto the strict 0.0016
gate, but it rejected one additional frame, failing the required 193 integrated
frame count. The `0.1` threshold rejected too many frames for the >=190 coverage
comparison region. No threshold is promoted.

## Artifacts

- Sweep root:
  `C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep`
- Sweep summary:
  `C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\resident_prefetch_sweep_summary.json`
- Sweep analysis:
  `C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\resident_prefetch_sweep_analysis.json`
- Candidate audits:
  `C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\candidate_audits`
- Candidate/compare join:
  `C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\resident_registration_compare.json`
- Doctor:
  `runs\checkpoints\s2_gate_115_doctor.json`

## Test Result

- `ruff check .`: passed.
- `python -m pytest -q`: `317 passed in 16.35s`.
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

- Agreement thresholding is not promoted. It can improve image agreement on the
  tested dataset, but the current scalar gate rejects required frames before all
  benchmark contracts pass.
- The `0.1` variant has no valid contract compare pixels at min coverage 190
  because only 189 frames remained active.
- Correlations in `resident_registration_compare.md` are based on three
  variants and are decision-support evidence only.

## Next Step

- S2-Gate 116 should triage the specific frames rejected by agreement gating,
  especially the `0.05` extra rejection, and separate true bad-frame rejection
  from overly blunt scalar scoring before changing defaults.

## Clean-Room Compliance

- This gate used GLASS-owned commands, artifacts, registration warnings, timing
  ledgers, candidate audits, and user-generated reference output only.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
