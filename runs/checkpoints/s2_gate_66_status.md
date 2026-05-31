# S2-Gate66 Status - HTML Numerical Drift Reporting

## Gate
- Gate: S2-Gate66
- Name: HTML Numerical Drift Reporting
- Status: passed
- Date: 2026-06-01 Asia/Shanghai

## Completed content
- Added an `Output numerical drift` section to the main GLASS HTML report.
- The section renders rows from `output_numerical_drifts` when the supplied acceptance/resident-determinism audit JSON contains S2-Gate65 drift evidence.
- The table includes:
  - artifact key and output field
  - availability
  - joint finite pixels
  - non-finite mismatch pixels
  - signed mean difference
  - mean/median absolute difference
  - RMS difference
  - p95/p99/max absolute difference
  - baseline/candidate standard deviation
  - RMS relative to baseline standard deviation
- Report rendering is read-only and does not alter strict audit pass/fail semantics.
- Updated CLI report smoke coverage, Phase 2 gate documentation, and the algorithm source ledger.

## Commands run
- Focused report test:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- Real 200-light report rendering:
  - `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601 --out C:\glass_runs\phase2_s2_gate_66_200\fast_coarse_with_numeric_drift_report.html --acceptance-audit C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.json`
- HTML evidence grep:
  - `Select-String -Path C:\glass_runs\phase2_s2_gate_66_200\fast_coarse_with_numeric_drift_report.html -Pattern 'Output numerical drift|H:200:F000061:F000260|relative_rms_to_baseline_std|3.751400|0.011915'`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test results
- Focused report test: passed (`1 passed in 0.09s`)
- Real report command: passed
- HTML grep found the numerical drift section and real 200-light artifact key/columns.
- Ruff: passed (`All checks passed!`)
- Full pytest: passed (`269 passed in 11.31s`)

## Real artifact generated
- HTML report: `C:\glass_runs\phase2_s2_gate_66_200\fast_coarse_with_numeric_drift_report.html`
- Source run: `C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601`
- Source audit: `C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.json`

## CUDA availability
- CUDA backend: available
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Driver: 596.21

## Known limitations
- The HTML section renders drift evidence already present in JSON. It does not compute new drift metrics itself.
- The table is intentionally compact; the resident-determinism JSON remains the authoritative artifact for full paths and exact values.
- Acceptance-audit production does not yet embed resident-determinism output automatically; the report can render it when supplied via `--acceptance-audit`.

## Next step
- Wire resident-determinism numerical drift into acceptance/benchmark audit workflows more explicitly, so fast-mode benchmark reports can carry both strict mismatch status and numerical magnitude without requiring a manually supplied JSON path.

## Clean-room compliance
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- Only GLASS source, generated GLASS artifacts, tests, and user-provided benchmark data were used.
- Original input image directories were treated as read-only.
