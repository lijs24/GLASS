# S2-Gate 105 Status: Resident Sweep Frame-Accounting Gate

## Gate

S2-Gate 105: Resident Sweep Frame-Accounting Gate

## Completed

- Added an optional frame-accounting promotion gate to resident sweep ranking.
- The gate can require:
  - exact input light frame count
  - exact active/integrated light frame count
  - exact zero-weight frame count
  - minimum active/integrated light frame count
- Added per-variant `frame_gate` status, pass/fail reasons, and policy to
  `resident_prefetch_sweep_summary.json`.
- Added top-level frame-gate passed/failed/planned counts to sweep summaries.
- Added frame-gate fields to `resident_prefetch_sweep_analysis.json` and
  Markdown analysis output.
- Updated the sweep CLI with:
  - `--frame-gate-expected-input-light-frames`
  - `--frame-gate-expected-active-light-frames`
  - `--frame-gate-expected-zero-weight-frames`
  - `--frame-gate-min-active-light-frames`
- Updated Phase 2 gate documentation and algorithm-source tracking.
- Regenerated a 200-light frame-gated analysis from the existing S2-Gate 103
  catalog sweep without rerunning CUDA.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_benchmarks.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\resident_sweep.py benchmarks\\bench_resident_prefetch_sweep.py tests\\test_benchmarks.py`
- Regenerated Gate103 frame-gated sweep summary with GLASS Python APIs into
  `C:\\glass_runs\\phase2_s2_gate_105_frame_gate\\gate103_frame_gated`.
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `cmd.exe /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\\.venv\\Scripts\\cmake.exe --build build\\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_105_doctor.json --allow-cpu-only`

## Test Results

- Focused benchmark tests: `16 passed in 2.79s`
- Full pytest: `310 passed in 15.00s`
- Ruff focused check: passed
- Ruff full check: passed
- Native CUDA build: passed, `ninja: no work to do`

## CUDA Status

- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_105_doctor.json`

## Real 200-Light Artifact

- Source sweep:
  `C:\\glass_runs\\phase2_s2_gate_103_catalog_sweep\\resident_prefetch_sweep_summary.json`
- Frame-gated output:
  `C:\\glass_runs\\phase2_s2_gate_105_frame_gate\\gate103_frame_gated\\resident_prefetch_sweep_summary.json`
- Analysis:
  `C:\\glass_runs\\phase2_s2_gate_105_frame_gate\\gate103_frame_gated\\resident_prefetch_sweep_analysis.json`
- Frame gate policy: 200 input lights, 193 active/integrated lights, 7
  zero-weight lights, minimum 193 active lights.
- Frame gate result: 2 passed, 0 failed, 0 planned.
- Promotion result: no promoted variant because both candidates still fail the
  strict compare gate; the frame gate confirms the candidates are at least
  frame-count comparable.

## Known Limitations

- This gate changes benchmark ranking and analysis only; it does not change
  resident CUDA image math, registration, warp, or integration kernels.
- The 200-light artifact is regenerated from existing Gate103 run outputs and
  does not represent a new CUDA execution.
- Frame accounting protects benchmark comparability but does not decide whether
  a particular rejected frame is scientifically optimal.

## Next Step

Use the frame-gated and compare-gated sweep artifacts to run a broader bounded
catalog-grid search. Candidate promotion should require guardrails, frame gate,
and compare gate all passing before runtime is considered.

## Clean-Room Compliance

Compliant. This gate consumes only GLASS-owned sweep, frame-accounting,
guardrail, and compare artifacts. It does not use proprietary implementation
source, and it does not modify input image directories.
