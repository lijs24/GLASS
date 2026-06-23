# S2-Gate 555 Status: Throughput-v3 Prefetch32 Default Retune

- Gate: S2-Gate 555
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_555_prefetch32_default_summary.json`
- Result: green checkpoint, default resident I/O preset retuned from p24/w16 to p32/w16

## Completed

- Changed default `throughput-v3-io` from `resident_prefetch_frames=24` to `resident_prefetch_frames=32`.
- Kept `resident_prefetch_workers=16`, pinned-ring H2D, queued refill, calibration batch `16`, streams `4`, wave `4`, and callback-queue release.
- Updated benchmark-contract expectations and focused CLI/acceptance tests for the new preset.
- Ran broad, nearby, and refined real 200-light prefetch-depth matrices.
- Verified the postpatch no-override default records `prefetch_frames=32`.

## Commands Run

- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests/test_acceptance_audit.py::test_acceptance_audit_accepts_io_runtime_preset_from_artifact`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light broad prefetch matrix:
  - p24/w16, p48/w16, p96/w16, p200/w16, p96/w32.
- Real 200-light nearby prefetch matrix:
  - p8/w8, p12/w12, p16/w16, p20/w16, p24/w16, p32/w16, p24/w24.
- Real 200-light refined prefetch matrix:
  - p24/w16, p28/w16, p32/w16 twice, p36/w16, p40/w16.
- Postpatch default validation with no explicit `--resident-prefetch-frames`.

## Test Results

- Focused CLI/acceptance preset tests: `3 passed in 0.42 s`
- Full pytest: `1189 passed in 45.03 s`

## Real 200-Light Validation

- Gate554 default no-env baseline:
  `C:\glass_runs\phase2_s2_gate554_ready_batch_select\final_20260623_165105\default_noenv`
- Broad matrix:
  `C:\glass_runs\phase2_s2_gate555_prefetch_depth_matrix\runs_20260623_165707`
- Nearby matrix:
  `C:\glass_runs\phase2_s2_gate555_prefetch_depth_matrix\nearby_20260623_165816`
- Refined matrix:
  `C:\glass_runs\phase2_s2_gate555_prefetch_depth_matrix\refine_20260623_165929`
- Postpatch default:
  `C:\glass_runs\phase2_s2_gate555_prefetch32_default\runs_20260623_170124\default_prefetch32_postpatch`
- Full postpatch summary:
  `C:\glass_runs\phase2_s2_gate555_prefetch32_default\runs_20260623_170124\gate555_postpatch_default_summary.json`
- Frame count: 200 lights
- Active frame count after registration masks: 193
- Masked frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`

| Run | Shell s | Resident stage s | Light read/upload/calibrate s | Ready wait s | Pinned bytes | SHA256 vs Gate554 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Gate554 default no-env baseline | `5.429829` | `5.031444` | `2.588569` | `1.158067` | `2959257600` | baseline |
| Gate555 postpatch default p32/w16 | `5.251073` | `4.872004` | `2.417012` | `0.748604` | `3945676800` | identical |
| Nearby p24/w16 control | `5.355637` | `4.994760` | `2.567499` | `1.159996` | `2959257600` | identical |
| Nearby p32/w16 | `5.126908` | `4.731957` | `2.419902` | `0.739668` | `3945676800` | identical |
| Refined p36/w16 | `5.128637` | `4.759546` | `2.454329` | `0.724921` | `4438886400` | identical |
| Broad p48/w16 | `6.010976` | `5.632519` | `2.626816` | `0.627772` | `5918515200` | identical |
| Broad p96/w16 | `7.039116` | `6.652209` | `3.565068` | `0.575984` | `11837030400` | identical |
| Broad p200/w16 | `10.414094` | `10.043203` | `6.126009` | `0.599989` | `24660480000` | identical |

## Numerical Validation

The postpatch default p32/w16 run is SHA256-identical to the Gate554 default no-env baseline for all six output FITS artifacts:

- `resident_master_H.fits`: `8BC069CE6858AB5E065B5D9AF297C35C36D4240C13980546E43CFB480115E110`
- `resident_weight_map_H.fits`: `5862111EE6F527A40671AC13F1FAA43F037C90271F872F27AF4ACF17040FBFE8`
- `resident_coverage_map_H.fits`: `B87517BE794A3B4BDCFF0D8536EE0188DA6AFA54ED2BE818BD911BA6CF1BE1B3`
- `resident_low_rejection_map_H.fits`: `F1181E0CE52A7FF77B988AFAF8A8911A1BEAF94DF54B25B0AA51014CB0D66E23`
- `resident_high_rejection_map_H.fits`: `ADB66C931C5A48D6E0D7F5C2FCBCC58481420AD4912304843A3802089050C805`
- `resident_dq_map_H.fits`: `934F661119CE18BBCAC1D369488AED4D959669C6EF614D6076D74BE06E69CCFB`

Resident StackEngine surface contract and DQ pixel closure passed.

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Decision

- Promote p32/w16 as the default `throughput-v3-io` prefetch setting.
- Do not promote 48/96/200-frame prefetch: those runs reduce ready wait but regress the target light-stage and total runtime.
- Keep user override support through `--resident-prefetch-frames`.

## Known Limitations

- The default consumes `986419200` more pinned host bytes than p24/w16 on this 200-light raw-u16 dataset.
- This is a scheduling retune for the current real-data path, not a universal full-preload policy.
- The next optimization still needs to reduce remaining ready wait and Python/native read orchestration without increasing host memory pressure too far.

## Clean-Room

- This gate uses GLASS-owned runtime scheduling controls, GLASS artifacts, and user-provided FITS data only.
- No external implementation source was inspected or copied.
- The gate does not change calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
