# S2-Gate 93 Status: Pipeline Pixel Delta Reporting

## Gate

S2-Gate 93: Pipeline Pixel Delta Reporting

## Completed Content

- Expanded the HTML pipeline-contract report section with per-map/per-flag
  pixel verification deltas.
- The report now shows `actual`, `summary`, `delta`, and `passed` for:
  - DQ bitfield pixel counts;
  - coverage `no_data` matching;
  - low-rejection positive-pixel matching;
  - high-rejection positive-pixel matching.
- Kept `pipeline_contract.json` as the authoritative machine-readable artifact.
- Added fixture coverage for both failed and passing delta rows in the report.
- Updated Phase 2 gate documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_report_summarizes_pipeline_contract
.\.venv\Scripts\python.exe -m ruff check src/glass/report/html_report.py tests/test_cli_smoke.py docs/algorithm_sources.md docs/phase2_algorithm_hardening.md
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531" --out runs\checkpoints\s2_gate_93_gate32_report.html --pipeline-contract runs\checkpoints\s2_gate_92_pipeline_contract_gate32_pixel.json
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_93_doctor.json
```

## Test Results

- Focused pytest: 1 passed.
- Full pytest: 300 passed in 13.68 s.
- Ruff: passed.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real Artifact Verification

- Source pixel contract:
  `runs/checkpoints/s2_gate_92_pipeline_contract_gate32_pixel.json`
- Preserved 200-light audit-map run:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`
- Regenerated HTML report:
  `runs/checkpoints/s2_gate_93_gate32_report.html`
- Result: the report shows per-flag delta rows for `high_rejected`,
  `low_rejected`, `no_data`, `valid`, and `warp_edge`, plus coverage and
  rejection map rows. All real-artifact deltas were `0` and passed.

## Known Limitations

- This gate is report-only. It does not add new verification logic beyond the
  Gate92 contract JSON.
- The detailed table appears only when a pipeline contract includes pixel
  verification matches.
- No new 200-light benchmark was run because no image math, CUDA kernels, or
  routing changed.

## Next Step

Return to the resident CUDA performance line with these contract reports as
guardrails, or add a compact failed-delta-only report view if large audit runs
produce many pixel verification rows.

## Clean-Room Compliance

Compliant. This gate renders GLASS-owned contract artifacts only and does not
read, copy, summarize, or rework any proprietary implementation source.
