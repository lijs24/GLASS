# S2-Gate 591 Status: Native Queue Read Default For Throughput-v3

Status: passed
Date: 2026-06-24

## Completed

- Promoted resident native raw-FITS queue reading from env-only experiment to
  formal CLI/preset controls.
- Added run/audit CLI options:
  - `--resident-native-batch-read off|on`
  - `--resident-native-queue-read off|on`
  - `--resident-native-queue-drain-mode thread|inline`
- Updated `throughput-v3-io` so compatible resident CUDA runs default to
  `resident_native_queue_read=on` and `resident_native_queue_drain_mode=thread`.
- Updated `_LightPrefetcher` to prefer CLI/preset controls, keep env controls as
  a fallback path, and record clear policy values such as `cli_enabled`,
  `cli_requested_not_candidate`, and `env_enabled`.
- Added timing/artifact fields for native batch/queue defaults and queue drain
  source.
- Added focused CLI/resident CUDA tests for default preset behavior and explicit
  override behavior.
- Updated Phase 2 hardening docs and the algorithm-source independence log.

## Commands Run

- Focused tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests/test_cli_smoke.py::test_resident_runtime_preset_manual_keeps_legacy_values tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_native_queue_override tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_queue_read_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_queue_read_default_drain_is_thread tests/test_resident_cuda_run.py::test_cli_resident_cuda_throughput_v3_uses_cli_native_queue_read tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_batch_read_is_opt_in`
- Lint:
  `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py tests\test_cli_smoke.py tests\test_resident_cuda_run.py`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`
- Real 200-light A/B probes:
  `GLASS_RESIDENT_NATIVE_BATCH_READ=1` and `GLASS_RESIDENT_NATIVE_QUEUE_READ=1` resident runs under
  `C:\glass_runs\phase2_s2_gate591_native_read_ab`.
- Fresh default resident CUDA run:
  `glass run --plan C:\glass_runs\phase2_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate591_native_queue_default\default_resident_regression --backend cuda --until-stage integration --resident --resident-runtime-preset throughput-v3-io --allow-partial`
- Compare:
  `glass compare --gpwbpp C:\glass_runs\phase2_s2_gate591_native_queue_default\default_resident_regression\integration\master_light_H.fits --reference C:\glass_runs\wbpp_m38_reference\master_light_H_fastintegration_scaled.fits --out C:\glass_runs\phase2_s2_gate591_native_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- Acceptance audit:
  `glass acceptance-audit --run C:\glass_runs\phase2_s2_gate591_native_queue_default\default_resident_regression --compare C:\glass_runs\phase2_s2_gate591_native_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate591_native_queue_default\acceptance_audit.json`
- CUDA doctor:
  `glass doctor --json --out C:\glass_runs\phase2_s2_gate591_native_queue_default\doctor.json`

## Test Results

- Focused tests: 8 passed in 2.07 s.
- Ruff: all checks passed.
- Full pytest: 1261 passed in 56.79 s.

## Real 200-Light Validation

A/B probe summary:

- Summary path:
  `C:\glass_runs\phase2_s2_gate591_native_read_ab\native_read_probe_summary.json`
- Gate590 default:
  - total elapsed: 8.27696210006252 s
  - light read/upload/calibrate: 2.697366200038232 s
- Env native batch read:
  - total elapsed: 7.984438900370151 s
  - light read/upload/calibrate: 2.5847186000319198 s
  - native batch frames: 200
  - hash parity versus Gate590: true
- Env native queue read, thread drain:
  - total elapsed: 7.960773499915376 s
  - light read/upload/calibrate: 2.532509900047444 s
  - native queue completions: 200
  - hash parity versus Gate590: true

Fresh default regression:

- Run path:
  `C:\glass_runs\phase2_s2_gate591_native_queue_default\default_resident_regression`
- Validation summary:
  `C:\glass_runs\phase2_s2_gate591_native_queue_default\gate591_validation_summary.json`
- Effective native queue route:
  - policy: `cli_enabled`
  - enabled: true
  - drain mode: `thread`
  - drain source: `cli`
  - submit count: 200
  - completion count: 200
- GLASS elapsed: 8.165057000005618 s.
- Speedup versus Gate590 default: 1.0137053666688212x.
- WBPP black-box reference elapsed: 1092.541 s.
- Speedup versus reference: 133.8069042260511x.
- Compare RMS: 0.005340835487175878.
- Compare abs diff p99: 0.002133606873685496.
- Coverage190 fraction: 0.905523489118409.
- Pipeline contract: passed.
- StackEngine contract: passed.
- Warp-quality contract: passed.
- Acceptance audit: passed.
- Hash parity versus Gate590: 6 / 6 integration FITS files matched.

## CUDA

- CUDA available to GLASS: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `C:\glass_runs\phase2_s2_gate591_native_read_ab\native_read_probe_summary.json`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\default_resident_regression`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\gate591_validation_summary.json`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\acceptance_audit.json`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\acceptance_audit.md`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\hash_parity_vs_gate590.json`
- `C:\glass_runs\phase2_s2_gate591_native_queue_default\doctor.json`

## Known Limitations

- The default speed gain is modest and depends on OS file cache and disk state.
- Native queue read is only enabled for compatible native_u16_gpu resident FITS
  routes; non-candidate runs fall back and record the reason.
- This gate does not change registration, warp, local normalization, rejection,
  or integration math.
- Larger remaining work is resident registration/warp/LN orchestration and
  deeper read/upload/calibrate overlap.

## Next Step

The next substantive gate should target resident registration/warp/LN residency
and orchestration, or a deeper native read-to-H2D/calibration wave scheduler
that reduces host-side queue drain and Python handoff.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned runtime scheduling, GLASS tests/artifacts,
user-owned 200-light inputs, and user-generated external black-box timing/output
artifacts. It does not read, copy, summarize, or rework proprietary source code.
