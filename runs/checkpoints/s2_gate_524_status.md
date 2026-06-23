# S2-Gate 524 Status: Resident Throughput-v3 Prefetch32 Default

## Gate

- Gate: S2-Gate 524
- Theme: Resident light-pipeline scheduling/default retune
- Date: 2026-06-23

## Completed

- Retuned the default `throughput-v3-io` resident runtime preset from
  `resident_prefetch_frames=48` to `resident_prefetch_frames=32`.
- Kept `resident_prefetch_workers=16`.
- Kept resident calibration batch/stream/wave/release settings unchanged at
  `16/4/4/callback_queue`.
- Updated benchmark-contract expectations for `throughput-v3-io`.
- Updated CLI and acceptance tests so the v3 preset requires 32 prefetch frames.

## Real 200-Light Probe

- Probe root:
  `C:\glass_runs\phase2_s2_gate524_prefetch_depth_probe\runs_20260623_110004`
- All candidates used the same 200-light M38 H-alpha plan, shared master cache,
  resident CUDA triangle registration, Lanczos3 warp, and audit output maps.
- Same-window prefetch-depth summary:
  - 16 slots: shell `6.869540199999999 s`, pinned host
    `1.8373489379882812 GiB`
  - 24 slots: average shell `6.71086155 s`, pinned host
    `2.756023406982422 GiB`
  - 32 slots: average shell `6.67240465 s`, pinned host
    `3.6746978759765625 GiB`
  - 48 slots: average shell `7.2235844 s`, pinned host
    `5.512046813964844 GiB`

## Real Default-Path Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate524_prefetch32_default\runs_20260623_110233`
- No explicit `--resident-prefetch-frames` was passed.
- `run_timing.json` recorded:
  - `resident_runtime_preset=throughput-v3-io`
  - `resident_prefetch_frames=32`
  - `resident_prefetch_workers=16`
- Warm repeat with shared master cache:
  - internal: `6.247844900004566 s`
  - shell: `6.6213798 s`
- Full run with per-run master cache policy:
  - internal: `13.36458739999216 s`
  - shell: `13.715893099999999 s`
- Versus Gate523 default-48 validation:
  - warm-repeat shell delta: `-0.3746900000000002 s`
  - warm-repeat internal delta: `-0.36951350001618266 s`
  - full shell delta: `-0.5148215 s`
  - full internal delta: `-0.5116491999360733 s`
  - pinned host prefetch memory saved: `1972838400` bytes,
    `1.8373489379882812 GiB`
- WBPP black-box baseline: `1092.541 s`
- Gate524 warm shell speedup versus WBPP: `165.00201362863976x`

## Numerical Results

- Gate524 warm-repeat master vs Gate523 warm-repeat master:
  - RMS: `0.0`
  - p99 absolute difference: `0.0`
  - max absolute difference: `0.0`
- Gate524 full run vs Gate524 warm-repeat:
  - RMS: `0.0`
  - p99 absolute difference: `0.0`
  - max absolute difference: `0.0`
- GLASS vs WBPP black-box robust linear-fit comparison:
  - RMS: `0.0015009512947433384`
  - p99 absolute difference: `0.00034034321741462114`
  - fit fraction: `0.982980688129347`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\report\benchmark_contract.py tests\test_cli_smoke.py tests\test_acceptance_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests\test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests\test_acceptance_audit.py::test_acceptance_audit_accepts_io_runtime_preset_from_artifact
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_524_doctor.json
.\.venv\Scripts\python.exe -m json.tool runs\checkpoints\s2_gate_524_prefetch32_default_summary.json
.\.venv\Scripts\python.exe -m pytest -q
```

Real validation used the same 200-light resident CUDA run settings as Gate523,
with no explicit `--resident-prefetch-frames` for the default-path validation.

## Test Results

- Ruff: passed
- Focused CLI/acceptance tests: `3 passed`
- JSON validation: passed
- Full pytest: `1169 passed in 42.39s`

## CUDA

- CUDA available: yes
- CUDA wrapper importable: yes
- Native extension loaded: yes
- GPU 0:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_524_prefetch32_default_summary.json`
- Doctor JSON:
  `runs/checkpoints/s2_gate_524_doctor.json`
- External summary:
  `C:\glass_runs\phase2_s2_gate524_prefetch32_default\runs_20260623_110233\gate524_prefetch32_default_summary.json`
- Compare reports:
  - `C:\glass_runs\phase2_s2_gate524_prefetch32_default\runs_20260623_110233\compare_gate524_vs_gate523.html`
  - `C:\glass_runs\phase2_s2_gate524_prefetch32_default\runs_20260623_110233\compare_full_vs_warm_repeat.html`
  - `C:\glass_runs\phase2_s2_gate524_prefetch32_default\runs_20260623_110233\compare_gate524_vs_wbpp.html`

## Known Limitations

- This is a runtime scheduling/default gate, not a scientific algorithm change.
- The 32-slot default is selected from this machine and this 200-light H-alpha
  benchmark; other storage devices may have different optimal prefetch depth.
- Registration/warp remains a larger resident runtime target than this preset
  retune.

## Next Step

- Continue with resident registration/warp batching and GPU-resident
  orchestration, or deeper light read/upload/calibration overlap if new
  profiling shows the I/O wall dominates again.

## Clean-Room Compliance

- Compliant.
- Only GLASS code, GLASS-generated artifacts, and user-generated WBPP
  black-box outputs were read.
- No official PixInsight/WBPP/PJSR source was accessed.
- Original input image directories were treated as read-only.
