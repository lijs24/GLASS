# S2-Gate 161 Status: Resident Runtime Variance Compare

## Gate

S2-Gate 161: Resident Runtime Variance Compare

## Completed

- Added `glass resident-runtime-compare`.
- Added `src/glass/report/resident_runtime_compare.py`.
- Added focused tests in `tests/test_resident_runtime_compare.py`.
- Added CLI help coverage for `resident-runtime-compare`.
- Generated a real timing comparison between:
  - `gate158_prefetch12_workers7`
  - `gate160_throughput_v1`
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_runtime_compare.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe resident-runtime-compare --run gate158_prefetch12_workers7=C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\runs\prefetch12_workers7 --run gate160_throughput_v1=C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --baseline-label gate158_prefetch12_workers7 --out C:\glass_runs\phase2_s2_gate_161_runtime_compare\runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate_161_runtime_compare\runtime_compare.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_161_doctor.json
```

## Test Results

- Focused tests: `3 passed in 0.77s`.
- Full tests: `401 passed in 22.55s`.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_161_doctor.json`.

## Artifacts

- Runtime comparison JSON:
  `C:\glass_runs\phase2_s2_gate_161_runtime_compare\runtime_compare.json`
- Runtime comparison Markdown:
  `C:\glass_runs\phase2_s2_gate_161_runtime_compare\runtime_compare.md`

## Runtime Findings

- Best measured run: `gate158_prefetch12_workers7`.
- Best elapsed: `17.101234800000043 s`.
- Preset confirmation elapsed: `23.330858499999977 s`.
- Preset / Gate158 elapsed ratio: `1.364279174741225`.
- Read-wait ratio: `2.451504514719359`.
- Worker-read cumulative ratio: `2.0380521300990586`.
- H2D+calibration ratio: `1.0188032944786403`.
- Registration/warp ratio: `0.9938565939958394`.

The Gate160 preset path used the same effective resident scheduling settings as
the Gate158 winner. The slower Gate160 measurement is therefore dominated by
read/decode and cache/I/O variance, not by a throughput preset contract failure.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- This gate compares existing timing artifacts only. It does not rerun image
  processing, change defaults, or validate new image outputs.
- The recommendation is diagnostic: repeat the throughput preset in a warm-cache
  or dedicated I/O window before considering default promotion.
- The local GPU had external load during validation, but this gate does not need
  heavy GPU execution.

## Next Step

Repeat the 200-light throughput preset benchmark in a controlled I/O window, or
add warm-cache/cold-cache benchmark labels so future performance regressions can
separate disk/decode variance from GPU scheduling changes.

## Clean-Room Compliance

Compliant. This gate reads GLASS-owned JSON timing and resident artifact files
only. It does not read proprietary source code, modify input data, or infer
implementation details from external software internals.
