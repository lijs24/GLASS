# S2-Gate 623 Status: Segmented Fallback Active-Frame Replay

## Gate

S2-Gate 623

## Completed Content

- Updated the over-native-limit resident hardened winsorized CPUStackEngine
  fallback to filter finite positive integration weights before downloading
  resident tiles.
- The fallback now downloads/replays only active frame indices, records original
  resident frame count, active replay count, skipped inactive count, and
  StackEngine request count in timing/metrics/DQ provenance/request metadata.
- All-zero or otherwise all-inactive fallback groups now fail with a clear
  `ValueError` instead of silently producing an empty stack.
- Added focused tests for active-only parity, batch-download active-index
  filtering, single-frame fallback compatibility, all-inactive rejection, and
  the over-native-limit resolver.
- Ran a synthetic 520-frame probe with 20 zero-weight frames to verify no
  zero-weight resident indices are downloaded and all output maps match the
  active-only CPUStackEngine baseline.
- Updated Phase 2, integration, known-limitations, and algorithm-source docs.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_segmented_cpu_hardened_fallback_matches_stack_engine_baseline tests/test_resident_cuda_run.py::test_resident_segmented_cpu_hardened_fallback_keeps_single_frame_download_escape_hatch tests/test_resident_cuda_run.py::test_resident_segmented_cpu_hardened_fallback_requires_positive_weight_frame tests/test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_uses_segmented_cpu_over_native_limit tests/test_resident_cuda_run.py::test_resident_auto_winsorized_contract_selects_segmented_cpu_over_native_limit
.\.venv\Scripts\python.exe - <synthetic 520-frame active-replay probe>
```

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused segmented fallback tests: `5 passed in 0.79 s`.
- Re-run focused segmented fallback tests after documentation updates:
  `5 passed in 0.17 s`.
- Ruff over touched Python files: passed.
- Full pytest: `1309 passed in 53.72 s`.
- Synthetic probe:
  `C:\glass_runs\phase2_s2_gate623_segmented_active_frames\synthetic_520_active_frame_probe.json`.
  - Input frames: `520`.
  - Active finite positive-weight frames: `500`.
  - Skipped zero-weight frames: `20`.
  - Tiles: `4`.
  - Batch tile downloads: `4`.
  - Zero-weight indices downloaded: `[]`.
  - Master/weight/coverage/low/high maps matched active-only CPUStackEngine:
    `true`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: yes.
- CUDA Toolkit used by the current native build: 13.2.

## Known Limitations

- This gate improves the correctness fallback for resident groups above the
  native 512-frame hardened CUDA prototype limit, but it is still a host
  CPUStackEngine fallback.
- The final high-throughput solution remains a device-resident segmented or
  cooperative order-statistic reducer that avoids active tile downloads.
- The real 200-light default path is unchanged because it remains inside the
  native 512-frame hardened CUDA limit.

## Next Step

Return to Phase 2 mainline performance work: design and validate a true
device-resident segmented reducer for over-512-frame hardened winsorized groups,
or run a larger real/synthetic A/B where the fallback is exercised to quantify
active-frame download savings.

## Clean-Room Compliance

Compliant. The change is derived from GLASS-owned resident frame-weight and
StackEngine contracts plus GLASS synthetic validation. It does not inspect,
copy, summarize, or rework external proprietary implementation source, and it
does not modify input image directories.
