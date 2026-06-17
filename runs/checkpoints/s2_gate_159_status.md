# S2-Gate 159 Status: Explicit Throughput Runtime Preset

## Gate

S2-Gate 159: Explicit Throughput Runtime Preset.

## Completed Content

- Added opt-in `--resident-runtime-preset` to `glass run`.
- Added opt-in `--resident-runtime-preset` to `glass audit`.
- Added `throughput-v1`, derived from the S2-Gate 158 winning matrix cell
  `prefetch12_workers7`.
- Kept the default as `manual`.
- Preset values:
  - `resident_prefetch_frames=12`
  - `resident_prefetch_workers=7`
  - `resident_prefetch_refill_mode=queued`
  - `resident_h2d_mode=pinned_ring`
  - `resident_calibration_batch_frames=8`
  - `resident_calibration_streams=4`
  - `resident_calibration_wave_frames=2`
  - `resident_calibration_release_mode=callback_queue`
- Explicit per-option user overrides are respected.
- Existing resident artifacts record effective values through
  `resident_io_pipeline`.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests/test_cli_smoke.py::test_resident_runtime_preset_applies_gate158_values tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_overrides`
- `.\.venv\Scripts\glass.exe run --help`
- `.\.venv\Scripts\glass.exe audit --help`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_159_doctor.json`
- `nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits`

## Test Results

- Focused preset tests and resident CUDA audit smoke: `3 passed in 0.35s`.
- Full test suite: `399 passed in 21.53s`.
- Ruff: `All checks passed!`

## CUDA Status

- `glass doctor`: CUDA available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB reported by GLASS doctor
- Driver: 596.21
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`
- `nvidia-smi` during checkpoint:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 596.21, 97887, 1535, 0, 39`

## Artifacts

- Doctor report:
  `runs/checkpoints/s2_gate_159_doctor.json`
- Source benchmark evidence:
  `C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep.json`
- Winning measured candidate:
  `prefetch12_workers7`, `17.101234800000043 s`,
  `63.88667325940681x` versus the black-box reference, and
  `0.9549992718308159` runtime ratio versus the historical GLASS baseline.

## Known Limitations

- `throughput-v1` is opt-in and benchmark-derived from one 200-light M38
  H-alpha workload on the current workstation.
- The preset changes runtime scheduling only. It does not change calibration
  math, registration model, weighting, rejection, output maps, or scientific
  defaults.
- The default remains `manual`; changing defaults requires a later gate with
  broader confirmation.

## Next Step

S2-Gate 160 should run at least one confirmation end-to-end command using
`--resident-runtime-preset throughput-v1` on the 200-light benchmark and compare
its result/time against the Gate158 winner and historical baseline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned benchmark artifacts and command-line
orchestration only. It does not read external implementation source, does not
modify input image directories, and does not change scientific defaults.
