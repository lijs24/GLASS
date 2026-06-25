# S2-Gate 692 Status: Mainline A/B Requires Frame-Index Alignment

## Gate

S2-Gate 692.

## Completed Content

- Connected the Gate691 resident frame-index invariant to
  `glass phase2-mainline-ab`.
- Added candidate `resident_frame_masks.json` inspection to the A/B gate.
- Added the hard check
  `candidate_frame_index_alignment_contract_pass`.
- The check requires:
  - `resident_frame_masks.json` exists;
  - `summary.frame_index_alignment_contract` exists;
  - `checked=true`;
  - `passed=true`.
- A/B output summary now reports:
  - `frame_index_alignment_passed`;
  - `frame_index_alignment_status`.
- Added focused tests for passing alignment and missing-alignment failure.
- Revalidated the current default resident path on the real 200-light dataset.
- Probed `--resident-native-completion-wave-fill-us 0`; it is not promoted
  because same-session current default was slightly faster.

## Real 200-Light Validation

- Baseline run:
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract`.
- Candidate current-default repeat:
  `C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\default_repeat`.
- Phase 2 mainline A/B:
  `C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\gate692_default_repeat_phase2_mainline_ab.json`.
- A/B Markdown:
  `C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\gate692_default_repeat_phase2_mainline_ab.md`.

Results:

- Phase 2 mainline A/B: passed, failed checks `[]`.
- Candidate active/masked frames: `193 / 7`.
- Candidate tracked map count: `6`.
- Hash mismatch count: `0`.
- Frame-index alignment status: `passed`.
- Frame-index alignment passed: `true`.
- Candidate weight mismatch count: `0`.
- Baseline-to-candidate elapsed ratio: `0.9312209070964549`.
- Candidate total elapsed: `11.509678000002168 s`.

Resident component timing:

- `resident_light_read_upload_calibrate`: `3.0809543000068516 s`.
- `resident_integration`: `3.266167899942957 s`.

Wave-fill probe:

- Sequential `--resident-native-completion-wave-fill-us 0` candidate:
  `C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\wave0_seq`.
- Wave0 A/B versus Gate691 passed with elapsed ratio `0.9371476911967143`.
- Same-session current default remained slightly faster:
  - default repeat total `11.509678000002168 s`;
  - wave0 total `11.582931699580513 s`.
- Earlier parallel queue/wave probes were discarded as timing evidence because
  concurrent resident runs contended for the same disk and GPU and inflated the
  light read/upload/calibrate stage.

## Commands Run

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_phase2_mainline_ab.py
.venv\Scripts\ruff.exe check src\glass\report\phase2_mainline_ab.py tests\test_phase2_mainline_ab.py
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\wave0_seq --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-wave-fill-us 0
.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract --candidate-run C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\wave0_seq --out C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\wave0_seq_ab_vs_gate691.json --markdown C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\wave0_seq_ab_vs_gate691.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\default_repeat --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract --candidate-run C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\default_repeat --out C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\gate692_default_repeat_phase2_mainline_ab.json --markdown C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\gate692_default_repeat_phase2_mainline_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused A/B tests: `4 passed in 0.28 s`.
- Ruff: passed.
- Full pytest: `1436 passed in 72.71 s`.

## CUDA Status

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend: available.

## Known Limitations

- This gate strengthens the validation surface for future performance work. It
  does not change science pixels or the default native-completion preset.
- The current `throughput-v4-native-completion` wave-fill policy is not changed.
- Parallel resident CUDA runs are not useful timing evidence on this workstation
  because they contend for the same external storage and GPU.

## Next Step

Return to a substantive implementation gate:

- reduce `resident_light_read_upload_calibrate` by changing read/H2D/calibration
  orchestration rather than single wait constants; or
- redesign resident integration around a deterministic cooperative or segmented
  CUDA reducer while preserving Gate690-Gate692 A/B contracts.

## Clean-Room Compliance

- No external proprietary implementation source was read, copied, summarized,
  or reworked.
- The real input data was used read-only.
- The new check is derived from GLASS-owned A/B gate schemas and GLASS-owned
  resident frame-mask artifacts.
- CUDA remains optional; CPU-only tests still pass.
