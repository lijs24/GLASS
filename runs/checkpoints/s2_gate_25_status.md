# S2-Gate 25 Status: StackEngine DQ Provenance

## Gate

S2-Gate 25: StackEngine DQ provenance.

## Completed Content

- Added `dq_provenance` to `StackEngineResult`.
- CPU StackEngine now records:
  - total input stack samples
  - source DQ-flagged sample count
  - non-finite sample count
  - per-flag source DQ sample counts
  - output zero-coverage pixel count
  - output low/high rejected pixel counts
  - output DQ summary when a DQ map is requested
- Preserved existing numerical combine/rejection behavior.
- Preserved the existing semantics that source DQ flags and non-finite samples
  are consumed as invalid stack samples.
- Kept output DQ map semantics focused on no-data and low/high rejection
  pixels for this first provenance gate.
- Added a direct synthetic StackEngine test for DQ provenance.
- Updated Phase 2 gate planning and algorithm source tracking.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results

- Ruff: `All checks passed`
- Focused StackEngine tests: `9 passed in 0.05s`
- Full pytest: `240 passed in 11.36s`

## CUDA Availability

CUDA is available, but this gate did not change or exercise the resident CUDA
fast path.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Benchmark

The 200-light benchmark was not rerun for this gate.

Reason: S2-Gate 25 changes only CPU StackEngine result provenance and direct
StackEngine tests. It does not change resident CUDA kernels, resident pipeline
routing, default 200-light benchmark options, FITS/XISF readers, calibration,
registration, warp, integration math, or output artifacts for the resident fast
path.

The latest preserved real-data benchmark remains S2-Gate 24:

- Run directory:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531`
- Runtime: `30.949304700363427 s`
- Speedup vs reference: `35.30098690673237x`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Acceptance audit: passed

## Performance Or Numerical Regression Note

No resident CUDA, pipeline routing, or image math path changed. The new
provenance dictionary is built during CPU StackEngine tile accounting and does
not change the produced master, weight, coverage, variance, rejection, or DQ
maps. Focused StackEngine tests and full pytest passed.

## Known Limitations

- DQ provenance is currently implemented for the CPU StackEngine reference
  path.
- Resident CUDA DQ provenance remains in its existing resident artifact schema.
- Output DQ still marks no-data and rejection pixels only; source DQ flags are
  counted for audit but are not yet projected onto output pixels as persistent
  source-flag provenance bits.
- Report-level rendering of StackEngine `dq_provenance` remains a later gate.

## Next Step

Unify StackEngine DQ provenance with pipeline/report artifacts, then extend the
same contract toward resident CUDA output maps and default master/light
StackEngine routing.

## Clean-Room Compliance

Compliant. This gate implements GLASS-owned DQ accounting from the existing
`DQFlag` bitfield and StackEngine tile loop. No proprietary source code was
read, copied, summarized, or reworked.
