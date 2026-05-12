# GPWBPP Completion Audit

Date: 2026-05-12

## Objective

Build a clean-room, installable, testable, resumable CUDA/WBPP-like
astronomical preprocessing system, advancing by gates. Each completed gate must
write a checkpoint, run tests, and commit. The expanded user goal requires a
real-data timing comparison against PixInsight/WBPP and an observed speedup.

## Gate Evidence

| Gate | Status | Evidence |
| --- | --- | --- |
| 0 | complete | `runs/checkpoints/gate_00_status.md`, commit `8bbfe63` |
| 1 | complete | `runs/checkpoints/gate_01_status.md`, commit `3a95bf5` |
| 2 | complete | `runs/checkpoints/gate_02_status.md`, commit `2cb5d1f` |
| 3 | complete | `runs/checkpoints/gate_03_status.md`, commits `78a5f81`, `cfda2bd` |
| 4 | complete | `runs/checkpoints/gate_04_status.md`, commit `fb33390` |
| 5 | complete | `runs/checkpoints/gate_05_status.md`, commit `abb6602` |
| 6 | complete | `runs/checkpoints/gate_06_status.md`, commit `5f273ba` |
| 7 | complete | `runs/checkpoints/gate_07_status.md`, commit `0dfeb63` |
| 8 | complete | `runs/checkpoints/gate_08_status.md`, commit `dc40dbb` |
| 9 | complete | `runs/checkpoints/gate_09_status.md`, commit `a0eeefd` |
| 10 | complete | `runs/checkpoints/gate_10_status.md`, commit `1060a47` |
| 11 | complete | `runs/checkpoints/gate_11_status.md`, commit `379d134` |
| 12 | complete | `runs/checkpoints/gate_12_status.md`, commit `84f938e` |
| 13 | blocked | `runs/checkpoints/gate_13_status.md`; PixInsight/WBPP executable or reference output is missing |
| 14 | not started | Must not proceed while Gate 13 is blocked |

## Requirement Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Clean-room boundary documented | `docs/pixinsight_blackbox_reference.md` | covered |
| No official WBPP/PJSR source used | checkpoints record compliance; no source paths accessed | covered by process evidence |
| Python package installable | `pyproject.toml`; editable install used throughout | covered |
| Project-local virtual environment | `.venv` used for commands | covered |
| Metadata scan and planning | `gpwbpp scan`, `gpwbpp plan`, tests | covered |
| FITS metadata and scaled FITS handling | `src/gpwbpp/io/fits_io.py`, `runs/checkpoints/out_of_core_fits_tile_reader_status.md` | covered for light/warp/LN/integration tile paths |
| Master calibration out-of-core path | `src/gpwbpp/engine/pipeline.py`, `runs/checkpoints/streaming_master_frames_status.md`, `runs/checkpoints/exact_flat_median_status.md`, `runs/checkpoints/bounded_master_accumulator_status.md` | covered for mean master bias/dark/flat, bounded tile accumulation, and exact median flat normalization |
| XISF metadata warning path | `src/gpwbpp/metadata/xisf_reader.py`, tests | minimal covered |
| Synthetic data/golden truth | `src/gpwbpp/synthetic/generator.py`, tests | covered baseline |
| CPU calibration baseline | `src/gpwbpp/cpu`, tests | covered |
| CUDA extension and wrappers | `cpp/cuda`, `src/gpwbpp_cuda.py`, tests | covered |
| Tile light calibration | Gate 6 checkpoint, tests | covered |
| Quality metrics/reference selection | Gate 7 checkpoint, `runs/checkpoints/streaming_quality_status.md`, tests | streaming tile metrics with exact scratch median and halo star detection |
| Registration | Gate 8 checkpoint, `runs/checkpoints/streaming_registration_status.md`, tests | translation baseline on bounded streaming previews |
| Warp/coverage | Gate 9 checkpoint, tests | integer nearest-neighbor baseline |
| Local normalization | Gate 10 checkpoint, tests | tile baseline only |
| Weighted integration/rejection/maps | Gate 11 checkpoint, `runs/checkpoints/streaming_integration_status.md`, tests | streaming weighted mean for no-rejection path; tile stack retained for rejection modes |
| End-to-end audit | Gate 12 checkpoint, synthetic CUDA/CPU compare | covered on synthetic |
| Resume from partial run | `runs/checkpoints/resume_status.md`, pipeline fixture test | covered with artifact-presence skip |
| Real-data GPWBPP run | `runs/checkpoints/real_data_m5_lum_status.md` | covered small subset |
| Benchmarks | `benchmarks/*.py`, `runs/checkpoints/benchmark_status.md` | covered baseline |
| Install and CLI smoke validation | `runs/checkpoints/validation_status.md` | covered |
| HTML report | report tests and run artifacts | covered baseline |
| PixInsight/WBPP numerical comparison | `gpwbpp compare`, black-box handoff, `gpwbpp blackbox-finalize` | blocked pending WBPP output |
| PixInsight/WBPP timing comparison | timing fields, handoff package, finalize command | blocked pending WBPP run/log |
| Observed speedup over WBPP | none | not achieved |

## Current Blocking Items

1. `PixInsight.exe` was not found on C:/D:/E: by filename search.
2. No user-generated WBPP output/log was found under the provided real-data root.
3. Without a WBPP master and elapsed time for the same subset, Gate 13 cannot be green.
4. Because Gate 13 is blocked, Gate 14 and Phase B should not start.

## Next Concrete Action

Provide or discover a callable PixInsight installation, or manually run WBPP on
the files listed in:

```text
runs/real_m5_lum_subset/wbpp_blackbox_handoff/input_frames.csv
```

Then fill in:

```text
runs/real_m5_lum_subset/wbpp_blackbox_handoff/timing_template.json
```

and run:

```powershell
gpwbpp blackbox-finalize --timing runs/real_m5_lum_subset/wbpp_blackbox_handoff/timing_template.json --out runs/real_m5_lum_subset/wbpp_blackbox_handoff/final
```
