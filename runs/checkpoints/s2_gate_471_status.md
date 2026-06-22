# S2-Gate 471 Status: Fused Throughput Runtime Preset

## Gate

- Gate: S2-Gate 471
- Scope: add a non-default resident runtime preset that packages the Gate470
  fused matrix dispatch candidate for the next real 200-light A/B run.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added `--resident-runtime-preset throughput-v2-fused`.
- The new preset inherits the `throughput-v1` resident scheduling values:
  - `resident_prefetch_frames=12`
  - `resident_prefetch_workers=7`
  - `resident_prefetch_refill_mode=queued`
  - `resident_h2d_mode=pinned_ring`
  - `resident_calibration_batch_frames=8`
  - `resident_calibration_streams=4`
  - `resident_calibration_wave_frames=2`
  - `resident_calibration_release_mode=callback_queue`
- The new preset adds `resident_integration_dispatch=auto`.
- Explicit user `--resident-integration-dispatch` still overrides the preset.
- Updated `glass run` and `glass audit` help text.
- Updated benchmark-contract runtime-preset artifact matching so
  `--resident-runtime-preset throughput-v2-fused` can be validated from
  resident I/O pipeline evidence.
- Updated the small resident CUDA auto-fused smoke path to trigger auto dispatch
  via the new preset.
- Updated Phase 2 documentation and algorithm-source provenance.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Multiprocessors: 188.

## Validation

- CLI smoke tests prove:
  - `throughput-v2-fused` applies the throughput-v1 I/O schedule;
  - `throughput-v2-fused` applies `resident_integration_dispatch=auto`;
  - explicit `--resident-integration-dispatch stack` overrides the preset;
  - default resident preset remains `throughput-v1` and default integration
    dispatch remains `stack`.
- Resident CUDA smoke proves:
  - a small bilinear triangle-alignment run using
    `--resident-runtime-preset throughput-v2-fused` records
    `resident_integration_dispatch_requested=auto`;
  - auto selects `fused_matrix`;
  - triangle registration records `fused_matrix_deferred`;
  - the run completes through integration.
- Acceptance-audit tests prove:
  - `--resident-runtime-preset throughput-v2-fused` command-token evidence can
    be satisfied from matching resident I/O pipeline artifacts.

## Real 200-Light Baseline

- A new 200-light run was not launched for this gate.
- Reason: C: free space remained too low for a safe large output directory.
- Current accepted real-data baseline remains S2-Gate465:
  - GLASS internal timing: `36.103794 s`
  - WBPP black-box timing: `1092.541 s`
  - speedup vs WBPP: `30.261113x`
  - compare RMS diff: `0.00170058`
  - P99 absolute diff: `0.000459801`
- Current fused-dispatch synthetic evidence remains S2-Gate470:
  - 32 synthetic 512x512 frames;
  - median stack dispatch: `0.005378499976359308 s`;
  - median fused dispatch: `0.0013046000385656953 s`;
  - median speedup: `4.122719467548494x`;
  - master/weight differences: `0.0`.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src tests docs`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v2_fused_applies_auto_dispatch tests\test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_overrides tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests\test_acceptance_audit.py::test_acceptance_audit_accepts_fused_runtime_preset_from_artifact`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py tests\test_resident_cuda_run.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused pytest: `4 passed in 1.34 s`.
- Broader CLI/resident/acceptance pytest: `151 passed in 16.53 s`.
- Full pytest: `1105 passed in 51.43 s`.

## Artifacts

- `runs/checkpoints/s2_gate_471_status.md`

## Known Limitations

- `throughput-v2-fused` is opt-in only.
- It is not a default promotion and does not change release/default-promotion
  evidence.
- The preset still requires a 200-light A/B run before any default change.

## Next Step

- Free enough C: output space, then run the real M38 200-light A/B:
  - current default `throughput-v1` stack route;
  - `throughput-v2-fused`;
  - explicit `--resident-integration-dispatch fused_matrix` if needed;
  and compare timing, frame accounting, DQ maps, acceptance contracts, and
  master-image agreement.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, summarized, copied, or used.
- The gate uses GLASS-owned runtime options, CUDA smoke fixtures, and
  acceptance-contract fixtures only.
- User image input directories were not modified.
