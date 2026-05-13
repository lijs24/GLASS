# Gate 01 Increment: Subset All-Compatible Calibration Selection

- Gate: 01
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added `--all-compatible-calibration` to `glass subset`.
- Default subset behavior remains lightweight and unchanged.
- When the new flag is set, the subset manifest keeps every calibration frame
  compatible with the selected lights by camera sampling:
  - bias: same shape/binning/gain/offset.
  - dark: same shape/binning/gain/offset and matching light exposure.
  - flat: same shape/binning/gain/offset and matching light filter.
- Added test coverage proving all compatible synthetic calibration frames are
  retained.
- Verified the flag against the real M38 manifest to produce a 50-light probe
  with 20 bias, 20 dark, and 20 flat frames.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\planner\subset.py src\glass\cli.py tests\test_subset.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_subset.py
$base='C:\glass_runs\final_m38_h_200'; $run=Join-Path $base 'glass_resident_ncc_subset50_allcal_probe'; New-Item -ItemType Directory -Force -Path $run | Out-Null; .\.venv\Scripts\glass.exe subset --manifest (Join-Path $base 'manifest.json') --out (Join-Path $run 'manifest.json') --plan-out (Join-Path $run 'processing_plan.json') --filter H --exposure-s 600 --light-limit 50 --all-compatible-calibration
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Targeted subset tests: 3 passed.
- Full pytest: 101 passed.
- Real M38 all-compatible subset probe:
  - 110 total frames.
  - 50 light frames.
  - 20 bias frames.
  - 20 dark frames.
  - 20 flat frames.
  - Plan executable: true.
  - Plan warnings: 0.

## CUDA Availability

- CUDA native extension: available in this environment.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_resident_ncc_subset50_allcal_probe\manifest.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_ncc_subset50_allcal_probe\processing_plan.json`

## Known Limitations

- The new flag is a subset/planning aid; it does not change calibration
  matching semantics in the main planner.
- Compatibility intentionally ignores calibration-frame temperature grouping
  because the final M38 acceptance case treats the available -19.5 to -20.2 C
  calibration spread as acceptable.
- It does not select by acquisition date yet.

## Next Step

- Use `--all-compatible-calibration` for the larger resident M38 runs so the
  final benchmark satisfies the user's at-least-20 calibration-frame target.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Only GLASS outputs and user-provided M38 metadata were used.
- Original input data directories were not modified.
