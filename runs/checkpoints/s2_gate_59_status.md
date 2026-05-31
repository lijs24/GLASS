# S2-Gate 59 Status: Resident Output Pixel Determinism Audit

## Gate

- Gate: S2-Gate 59
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Work

- Extended `glass resident-determinism` to compare final resident output FITS
  pixel data in addition to resident triangle signatures, registration rows,
  and frame accounting.
- Added canonical FITS data signatures for resident outputs:
  - master output
  - weight map
  - coverage map
  - low rejection map
  - high rejection map
  - DQ map
- Each output signature records shape, dtype, SHA-256 data hash, finite and
  non-finite pixel counts, and compact finite-value statistics.
- Updated CLI summary output and `--fail-on-mismatch` help text to include
  output pixel mismatches.
- Added synthetic FITS audit fixtures that prove output pixel drift fails the
  audit while matching `NaN` registration sentinels remain equal.
- Updated Phase 2 planning docs with the S2-Gate 59 scope.

## Commands Run

- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_determinism.py`
- Real 200-light resident output audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_c_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_d_20260601 --out C:\glass_runs\phase2_s2_gate_59_200\resident_determinism_outputs_c_vs_d_final.json --markdown C:\glass_runs\phase2_s2_gate_59_200\resident_determinism_outputs_c_vs_d_final.md --fail-on-mismatch`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: passed, `5 passed in 0.19s`.
- Ruff: passed, `All checks passed!`.
- Full pytest: passed, `269 passed in 11.55s`.

## Real 200-Light Result

- Baseline run: `C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_c_20260601`
- Candidate run: `C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_d_20260601`
- Audit JSON:
  - `C:\glass_runs\phase2_s2_gate_59_200\resident_determinism_outputs_c_vs_d_final.json`
- Audit Markdown:
  - `C:\glass_runs\phase2_s2_gate_59_200\resident_determinism_outputs_c_vs_d_final.md`
- Audit result: pass.
- Artifact differences: 0.
- Frame signature differences: 0.
- Registration differences: 0.
- Frame accounting differences: 0.
- Output pixel/map differences: 0.

## CUDA Availability

- CUDA available: yes.
- Device used in the source runs:
  - NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
  - Compute capability: 12.0.
  - VRAM: 97886 MiB.
  - Driver: 596.21.

## Known Limitations

- Output signatures are exact data hashes; they do not yet support tolerance
  windows for intentionally approximate algorithm changes.
- The Gate59 real audit used the S2-Gate58 `minimal` output-map policy, so the
  master FITS was compared while optional maps were absent in both runs.
- The audit reads output FITS files but does not rewrite any run artifact or
  input image directory.

## Next Step

- Use the output-pixel audit as a regression guard while optimizing resident
  registration throughput, especially catalog extraction and batch scheduling.

## Clean-Room Compliance

- No PixInsight or WBPP/PJSR source was read or used.
- Only GLASS source, tests, generated artifacts, and local benchmark outputs
  were inspected or modified.
- Input image directories were treated as read-only.
