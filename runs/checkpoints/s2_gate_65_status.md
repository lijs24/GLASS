# S2-Gate65 Status - Resident Output Numerical Drift Audit

## Gate
- Gate: S2-Gate65
- Name: Resident Output Numerical Drift Audit
- Status: passed
- Date: 2026-06-01 Asia/Shanghai

## Completed content
- Extended `glass resident-determinism` with numerical drift metrics for output FITS image/map mismatches.
- Strict pass/fail semantics are unchanged:
  - exact hash mismatches still count as output differences;
  - `--fail-on-mismatch` still fails when strict differences exist.
- For mismatched compatible FITS outputs, the audit now records:
  - joint finite pixel count
  - non-finite mismatch count
  - signed mean difference
  - mean/median absolute difference
  - RMS difference
  - p95/p99/max absolute difference
  - baseline/candidate mean and standard deviation
  - RMS relative to baseline standard deviation
- Markdown output now includes a compact "First Output Numerical Drifts" section.
- Added synthetic FITS audit coverage for the new drift fields.
- Updated Phase 2 gate documentation and the algorithm source ledger.

## Commands run
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_determinism.py`
- Real 200-light conservative-vs-fast audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601 --out C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.json --markdown C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.md`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test results
- Focused resident determinism tests: passed (`5 passed in 0.23s`)
- Real 200-light audit command: completed and wrote JSON/Markdown
- Ruff: passed (`All checks passed!`)
- Full pytest: passed (`269 passed in 11.42s`)

## 200-light audit result
- Baseline: `C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_a_20260601`
- Candidate: `C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601`
- Audit JSON: `C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.json`
- Audit Markdown: `C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.md`
- Strict result: failed as expected for conservative-vs-fast comparison
  - frame signature differences: 0
  - registration differences: 64
  - frame accounting differences: 0
  - output differences: 1
  - output numerical drift count: 1
- Numerical drift for master output:
  - joint finite pixels: 61651200
  - mean signed difference: 0.000111721 ADU
  - mean absolute difference: 0.642260 ADU
  - median absolute difference: 0.417107 ADU
  - RMS difference: 3.751400 ADU
  - p95 absolute difference: 1.489120 ADU
  - p99 absolute difference: 3.408920 ADU
  - max absolute difference: 1836.101562 ADU
  - baseline std: 314.820862 ADU
  - candidate std: 314.730194 ADU
  - RMS relative to baseline std: 0.011916

## CUDA availability
- CUDA backend: available
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Driver: 596.21

## Known limitations
- Numerical drift metrics explain strict output mismatches but do not decide scientific acceptability by themselves.
- The audit reads mismatched FITS outputs into CPU memory to compute drift metrics; this is acceptable for audit/reporting but not a streaming integration path.
- The metrics are image-level statistics. They do not yet include spatial heatmaps, star-core residual metrics, or external-reference visual scoring.

## Next step
- Surface the numerical drift section in HTML/acceptance reports and use it as the quality gate for explicit fast presets such as S2-Gate64 fast-coarse.
- Continue reducing pixel-refine and warp time while preserving strict A/B determinism for each fixed mode.

## Clean-room compliance
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- Only GLASS source, generated GLASS artifacts, tests, and user-provided benchmark data were used.
- Original input image directories were treated as read-only.
