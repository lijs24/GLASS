# S2-Gate 104 Status: Resident Sweep Analysis Artifact

- Status: green
- Date: 2026-06-01T10:14:32+08:00
- Scope: resident sweep benchmark analysis and promotion decision support

## Completed

- Added automatic `resident_prefetch_sweep_analysis.json` emission for every resident sweep summary write.
- Added companion `resident_prefetch_sweep_analysis.md`.
- Added analysis records for:
  - completed variant count
  - promotion candidate count
  - fastest variant
  - lowest moving-catalog variant
  - lowest registration/warp variant
  - fastest promotion candidate
  - recommendation status and reason
- Promotion candidates require completed status plus enabled guardrails and compare gate.
- Preserved the existing `resident_prefetch_sweep_summary.json` schema.
- Updated Phase 2 plan and algorithm-source ledger.
- Generated the analysis artifact for the real S2-Gate 103 200-light catalog sweep without rerunning CUDA.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py -q
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_sweep.py tests\test_benchmarks.py docs\algorithm_sources.md docs\phase2_algorithm_hardening.md
git diff --check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_104_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

Additional real-artifact generation:

```powershell
@'
from pathlib import Path
from glass.io.json_io import read_json, write_json
from glass.report.resident_sweep import build_resident_sweep_analysis, _write_analysis_markdown
out = Path(r'C:\glass_runs\phase2_s2_gate_103_catalog_sweep')
payload = read_json(out / 'resident_prefetch_sweep_summary.json')
analysis = build_resident_sweep_analysis(payload)
write_json(out / 'resident_prefetch_sweep_analysis.json', analysis)
_write_analysis_markdown(out / 'resident_prefetch_sweep_analysis.md', analysis)
'@ | .\.venv\Scripts\python.exe -
```

## Test Results

- Focused benchmark tests: 15 passed.
- Ruff full check: passed.
- Full pytest: 309 passed in 14.67 s.
- Native CUDA build: passed; Ninja reported no work to do.
- Doctor JSON: `runs/checkpoints/s2_gate_104_doctor.json`.

## 200-Light Evidence

- Source sweep: `C:\glass_runs\phase2_s2_gate_103_catalog_sweep\resident_prefetch_sweep_summary.json`.
- New analysis JSON: `C:\glass_runs\phase2_s2_gate_103_catalog_sweep\resident_prefetch_sweep_analysis.json`.
- New analysis Markdown: `C:\glass_runs\phase2_s2_gate_103_catalog_sweep\resident_prefetch_sweep_analysis.md`.

Analysis result:

- Recommendation: `candidate_blocked_by_compare_gate`.
- Variant: `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_gt2`.
- Reason: lowest moving-catalog time did not satisfy the compare gate.
- Compare-gate reasons:
  - `rms_diff 0.00165201 > 0.0016`
  - `abs_diff_p99 0.000420911 > 0.00042`
- Promotion candidates: 0.
- Fastest variant: `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_gt2`, total 15.600916900206357 s.
- Lowest catalog variant: `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_gt2`, moving catalog 0.7481854963116348 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- The analysis artifact is decision support only; it does not automatically promote defaults.
- Recommendations depend on the enabled guardrail and compare-gate policy.
- The real-data analysis uses the hot/shared-cache S2-Gate 103 sweep and does not replace cold-start packaging benchmarks.

## Next Step

- Use the analysis artifact to run a broader but bounded catalog/grid sweep and search for a variant that preserves the strict compare gate while retaining part of the `top_per_cell=2` catalog-time reduction.

## Clean-Room Compliance

- No official PixInsight or PJSR source code was read or used.
- This gate consumes only GLASS-generated sweep, guardrail, compare, and timing artifacts plus a user-generated external reference master.
- Input image directories remain read-only.
