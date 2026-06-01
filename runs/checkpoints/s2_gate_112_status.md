# S2-Gate 112 Status: Resident Candidate/Compare Correlation

## Gate

S2-Gate 112 joins resident CUDA registration candidate audits with resident
sweep compare results. The goal is to turn the S2-Gate 110/111 evidence into a
machine-readable decision-support artifact before changing descriptor scoring or
pixel-refine behavior.

## Completed

- Added `src/glass/report/resident_registration_compare.py`.
- Added CLI command:
  `glass resident-registration-compare`.
- Added tests in `tests/test_resident_registration_compare.py`.
- Updated CLI help coverage in `tests/test_cli_smoke.py`.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`
- Joined the S2-Gate 110 resident sweep summary with S2-Gate 111 candidate audit
  files.
- Wrote CUDA doctor evidence to
  `runs/checkpoints/s2_gate_112_doctor.json`.

## New CLI

```powershell
glass resident-registration-compare `
  --sweep-summary resident_prefetch_sweep_summary.json `
  --audit-root C:\path\to\candidate_audits `
  --out resident_registration_candidate_compare.json `
  --markdown resident_registration_candidate_compare.md
```

Optional:

```powershell
--audit-json explicit_candidate_audit.json
--fail-on-missing-audits
```

## Real-Data Command

```powershell
$out='C:\glass_runs\phase2_s2_gate_112_candidate_compare'
New-Item -ItemType Directory -Force -Path $out | Out-Null
.\.venv\Scripts\glass.exe resident-registration-compare `
  --sweep-summary C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\resident_prefetch_sweep_summary.json `
  --audit-root C:\glass_runs\phase2_s2_gate_111_candidate_audit `
  --out "$out\resident_registration_candidate_compare.json" `
  --markdown "$out\resident_registration_candidate_compare.md"
```

## Real-Data Artifacts

- Analysis root:
  `C:\glass_runs\phase2_s2_gate_112_candidate_compare`
- JSON:
  `C:\glass_runs\phase2_s2_gate_112_candidate_compare\resident_registration_candidate_compare.json`
- Markdown:
  `C:\glass_runs\phase2_s2_gate_112_candidate_compare\resident_registration_candidate_compare.md`

## Real-Data Results

Summary:

- Variants: 4.
- Missing audits: 0.
- Compare-gate failed variants: 4.
- Compare-gate passed variants: 0.
- Registration hard-failure variants: 0.
- Recommendation status:
  `compare_failures_without_registration_hard_failures`.
- Next target: descriptor scoring or pixel-refine agreement.

| Variant | Compare | RMS | P99 | Failed reg | Candidate median | Fit RMS median | Pixel RMS median | Pixel NCC median |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `g28x16_gt2_sep48` | failed | 0.001678125 | 0.000434982 | 0 | 152066.0 | 0.638593 | 157.59 | 0.9296485 |
| `g28x16_gt2_sep96` | failed | 0.001674460 | 0.000356952 | 0 | 156750.0 | 0.623392 | 164.1985 | 0.917817 |
| `g20x16_gt2_sep96` | failed | 0.002802847 | 0.000368809 | 0 | 150676.0 | 0.591433 | 202.123 | 0.8710095 |
| `g20x16_gt2_sep48` | failed | 0.001675648 | 0.000392369 | 0 | 140418.0 | 0.642062 | 157.8935 | 0.928183 |

Top small-sample correlations from the four-variant slice:

| Metric | Target | Pearson |
| --- | --- | ---: |
| `pixel_ncc_mean` | `relative_rms_diff` | -0.999316 |
| `pixel_rms_adu_mean` | `relative_rms_diff` | 0.998170 |
| `fit_rms_px_mean` | `relative_rms_diff` | -0.998021 |
| `pixel_rms_adu_median` | `relative_rms_diff` | 0.997501 |
| `pixel_ncc_median` | `relative_rms_diff` | -0.995918 |
| `fit_rms_px_mean` | `rms_diff` | -0.992018 |
| `pixel_rms_adu_median` | `rms_diff` | 0.989449 |
| `pixel_ncc_mean` | `rms_diff` | -0.984894 |

## Interpretation

- The joined evidence reinforces S2-Gate 111: compare failures are not explained
  by hard registration failure, quality-gated triangle frames, or missing
  candidate audits.
- Pixel-refine NCC/RMS metrics are the strongest indicators in this small
  four-variant slice.
- Correlation is not causation; S2-Gate 113 should validate a narrow
  pixel-refine or descriptor-scoring change under the same frame/guardrail/
  compare gates.
- No registration defaults were changed in this gate.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_compare.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_compare.py tests\test_resident_registration_compare.py src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_112_doctor.json --allow-cpu-only
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused tests: 3 passed in 0.27s.
- Full test suite: 316 passed in 15.48s.
- Ruff: all checks passed.
- Native CUDA build: `ninja: no work to do`.
- `glass doctor`: completed and wrote
  `runs/checkpoints/s2_gate_112_doctor.json`.

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

- The correlation rows are based on four variants, so they are useful for
  directing the next experiment but not sufficient to prove causation.
- This gate reads existing S2-Gate 110/111 artifacts and does not rerun the
  200-light CUDA pipeline.
- This gate is an observability/reporting gate and does not alter registration
  scoring, pixel refinement, or CUDA kernels.

## Next Step

S2-Gate 113 should implement and test a narrow agreement-driven scoring or
pixel-refine candidate selection change, then rerun a bounded 200-light
contract/guardrail/compare sweep to prove whether the change reduces RMS/P99
without losing the resident speed path.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned sweep summaries, candidate audits, timing,
guardrail, and compare artifacts only. It did not read, copy, summarize, or
rework proprietary implementation source and did not modify source image
directories.
