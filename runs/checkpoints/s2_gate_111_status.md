# S2-Gate 111 Status: Resident Registration Candidate Audit

## Gate

S2-Gate 111 adds an observability layer for resident CUDA triangle registration.
It parses existing `registration_results.json` and `resident_artifacts.json`
outputs into stable JSON/Markdown candidate diagnostics so the next scoring or
pixel-refine gate can target evidence rather than guessing from free-form
warnings.

## Completed

- Added `src/glass/report/resident_registration_audit.py`.
- Added CLI command:
  `glass resident-registration-audit`.
- Added tests in `tests/test_resident_registration_audit.py`.
- Updated CLI help coverage in `tests/test_cli_smoke.py`.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`
- Ran the audit over all four S2-Gate 110 200-light variants without rerunning
  GPU stacking.
- Wrote CUDA doctor evidence to
  `runs/checkpoints/s2_gate_111_doctor.json`.

## New CLI

```powershell
glass resident-registration-audit --run RUN_OR_REGISTRATION_JSON --out audit.json --markdown audit.md
```

Optional:

```powershell
--fail-on-registration-failures
```

returns exit code 2 when any triangle registration frame failed or was
quality-gated.

## Real-Data Audit Commands

```powershell
$out='C:\glass_runs\phase2_s2_gate_111_candidate_audit'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$variants=@(
  'pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep48',
  'pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96',
  'pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g20x16_gt2_sep96',
  'pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g20x16_gt2_sep48'
)
foreach($v in $variants){
  .\.venv\Scripts\glass.exe resident-registration-audit `
    --run "C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\$v" `
    --out "$out\${v}_candidate_audit.json" `
    --markdown "$out\${v}_candidate_audit.md"
}
```

## Real-Data Artifacts

- Audit root:
  `C:\glass_runs\phase2_s2_gate_111_candidate_audit`
- Per-variant JSON/Markdown files:
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep48_candidate_audit.json`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep48_candidate_audit.md`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96_candidate_audit.json`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96_candidate_audit.md`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g20x16_gt2_sep96_candidate_audit.json`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g20x16_gt2_sep96_candidate_audit.md`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g20x16_gt2_sep48_candidate_audit.json`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g20x16_gt2_sep48_candidate_audit.md`

## Real-Data Results

| Variant | Frames | Triangle frames | Failed triangle frames | Candidate median | Fit RMS median | Pixel RMS median | Pixel NCC median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `g28x16_gt2_sep48` | 200 | 200 | 0 | 152066.0 | 0.638593 | 157.59 | 0.9296485 |
| `g28x16_gt2_sep96` | 200 | 200 | 0 | 156750.0 | 0.623392 | 164.1985 | 0.917817 |
| `g20x16_gt2_sep96` | 200 | 200 | 0 | 150676.0 | 0.591433 | 202.123 | 0.8710095 |
| `g20x16_gt2_sep48` | 200 | 200 | 0 | 140418.0 | 0.642062 | 157.8935 | 0.928183 |

Component timings recovered by the audit:

| Variant | Moving catalog s | Descriptor fit s | Pixel refine s |
| --- | ---: | ---: | ---: |
| `g28x16_gt2_sep48` | 0.760188 | 0.061954 | 0.898957 |
| `g28x16_gt2_sep96` | 0.767324 | 0.063850 | 0.891320 |
| `g20x16_gt2_sep96` | 1.136383 | 0.062058 | 0.915831 |
| `g20x16_gt2_sep48` | 1.085037 | 0.059816 | 0.933943 |

## Interpretation

- All four S2-Gate 110 variants produced 200 triangle registration frame
  records and zero failed triangle frames in this audit.
- Therefore the strict compare failures from S2-Gate 110 are not explained by
  outright triangle registration failure.
- The audit makes the next target narrower: descriptor candidate scoring and
  pixel-refine agreement should be inspected for subtle drift, especially
  because grid-column changes shifted candidate counts and pixel NCC/RMS without
  causing hard registration failures.
- No registration defaults were changed in this gate.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_audit.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_audit.py tests\test_resident_registration_audit.py src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_111_doctor.json --allow-cpu-only
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused tests: 3 passed in 0.26s.
- Full test suite: 314 passed in 15.31s.
- Ruff: all checks passed.
- Native CUDA build: `ninja: no work to do`.
- `glass doctor`: completed and wrote
  `runs/checkpoints/s2_gate_111_doctor.json`.

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

- The audit parses current GLASS registration warning keys; if future
  registration output moves to first-class structured fields, this parser should
  be kept backward-compatible but no longer be the primary source.
- This gate diagnoses candidate/refine evidence. It does not prove which scoring
  change should be promoted.
- The real-data audit used existing S2-Gate 110 run artifacts and did not rerun
  the 200-light pipeline.

## Next Step

S2-Gate 112 should use this audit to compare accepted candidate statistics
against image-difference outcomes, then test a narrow descriptor-scoring or
pixel-refine agreement change with the same contract/guardrail/compare gates.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned registration/run artifacts and
user-generated benchmark outputs only. It did not read, copy, summarize, or
rework proprietary implementation source and did not modify source image
directories.
