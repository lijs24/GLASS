# S2-Gate 570 Status: Default Resident Reference Scout

## Gate

S2-Gate 570 makes the default resident CUDA matrix-registration path runnable
without a manual `--reference-frame-id` by adding an auditable raw-light
reference scout before reference admission.

## Completed

- Added `glass.engine.resident_reference_scout`.
- Added `FitsImageReader.read_sampled`.
- Added `--resident-reference-scout` controls for `glass run` and `glass audit`:
  - `--resident-reference-scout auto|off`
  - `--resident-reference-scout-stride`
  - `--resident-reference-scout-sample-side`
  - `--resident-reference-scout-max-frames`
  - `--resident-reference-scout-threshold-sigma`
  - `--resident-reference-scout-max-stars`
- The default resident CUDA matrix-registration path now writes
  `resident_reference_scout.json` and `frame_quality.json` when no explicit,
  external, or precomputed reference exists.
- Scout selection uses bounded raw-light center crops, an evenly spaced frame
  subset, dominant `PIERSIDE`/rotation preference when metadata is available,
  and GLASS-owned star/quality metrics.
- Explicit concrete resident-registration diagnostics still keep the
  first-light fallback escape hatch and do not auto-scout.
- `--resident-reference-scout off` preserves the S2-Gate 569 hard block for
  default matrix registration without reference evidence.
- Updated `docs/registration_model.md`.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py::test_fits_image_reader_sampled_read_preserves_blank_mapping tests/test_cli_smoke.py::test_cli_resident_run_can_disable_reference_scout_and_block_first_light_fallback tests/test_cli_smoke.py::test_cli_resident_run_auto_reference_scout_feeds_reference_admission`
- `.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py::test_fits_image_reader_sampled_read_preserves_blank_mapping tests/test_cli_smoke.py::test_cli_resident_run_can_disable_reference_scout_and_block_first_light_fallback tests/test_cli_smoke.py::test_cli_resident_run_auto_reference_scout_feeds_reference_admission tests/test_cli_smoke.py::test_resident_reference_scout_prefers_dominant_orientation`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py tests/test_fits_io.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2 --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m py_compile src\glass\cli.py src\glass\engine\resident_reference_scout.py src\glass\io\fits_io.py tests\test_cli_smoke.py tests\test_fits_io.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe doctor`

## Test Results

- Focused scout/FITS tests: `3 passed in 0.41 s`, then `4 passed in 0.56 s`.
- CLI/FITS related suites: `75 passed in 5.90 s`.
- Syntax check: passed.
- Full pytest: `1226 passed in 48.43 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2`
- WBPP black-box elapsed reference: `1092.541 s`.
- GLASS run timing total: `7.475622300000396 s`.
- Speedup versus WBPP reference: `146.1471642300524x`.
- Stage timings:
  - `resident_reference_scout`: `0.35959409998031333 s`
  - `resident_reference_admission`: `0.006777699978556484 s`
  - `resident_memory_admission`: `0.003085100033786148 s`
  - `resident_calibration_integration`: `6.784465399978217 s`
  - `local_norm_contract`: `0.17468410002766177 s`
  - `pipeline_contract`: `0.14701590000186116 s`
- Selected reference:
  - frame id: `F000225`
  - path: `C:\gpwbpp_runs\final_m38_h_200\input\Light\LIGHT_H_0165.fits`
  - orientation key: `east / 92.0`
  - dominant orientation key: `east / 92.0`
  - orientation constraint applied: `true`
- Pipeline contract: passed.
- Local-normalization contract: passed.
- Registration quality summary: 193 accepted/reference frames, 7 rejected.
- Output master/maps written under the run `integration/` directory.

## Result Consistency

The default scout selected the dominant East pier reference, while the previous
Gate569 baseline used an explicit West pier reference (`LIGHT_H_0136`). Direct
pixel differencing is therefore dominated by a reference-coordinate flip and is
not a valid scientific comparison.

An aligned comparison was written to:
`C:\glass_runs\phase2_s2_gate570_reference_scout\aligned_compare_gate569_v2.json`

After warping the auto-reference master into the Gate569 baseline coordinate
frame with the Gate569 F000225 registration matrix:

- valid pixels: `60958862`
- mean absolute residual: `7.876279985220731`
- RMS residual: `64.79087744463654`
- p95 absolute residual: `13.42593765258789`
- p99 absolute residual: `22.01966094970703`
- max absolute residual: `24695.560546875`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2\resident_reference_scout.json`
- `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2\frame_quality.json`
- `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2\resident_reference_admission.json`
- `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2\run_timing.json`
- `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2\pipeline_contract.json`
- `C:\glass_runs\phase2_s2_gate570_reference_scout\default_auto_reference_v2\local_norm_contract.json`
- `C:\glass_runs\phase2_s2_gate570_reference_scout\aligned_compare_gate569_v2.json`

## Known Limitations

- This is a CPU/raw-light scout. It avoids a full calibrated CPU cache and full
  disk pass, but it is not yet resident GPU quality-reference selection.
- Different valid reference choices can produce masters in different output
  coordinate systems. Comparisons across different references must use the
  recorded registration matrix or an equivalent alignment step.
- The raw scout uses center crops and may miss edge-only star fields; the CLI
  exposes `sample-side`, `stride`, and `max-frames` to tune this before the GPU
  replacement lands.

## Next Step

Replace the scout internals with resident GPU star catalog/quality evidence:
compute compact catalogs for candidate frames in VRAM, score reference quality
without extra CPU FITS reads, keep the same `resident_reference_scout.json`
contract, and rerun the 200-light A/B against this gate.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned FITS reading, star metrics, reference
selection policy, tests, and user-owned 200-light artifacts only. It does not
inspect external proprietary source code, copy external algorithms, or modify
input image directories.
