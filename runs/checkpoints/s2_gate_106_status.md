# S2-Gate 106 Status: Resident Sweep Contract Frame-Gate Import

## Gate

S2-Gate 106: Resident Sweep Contract Frame-Gate Import

## Completed

- Added `--frame-gate-from-contract` to
  `benchmarks/bench_resident_prefetch_sweep.py`.
- The sweep harness can now import frame-accounting promotion requirements from
  a GLASS benchmark contract JSON:
  - `required_input_light_frames` -> `expected_input_light_frames`
  - `required_integrated_frames` -> `expected_active_light_frames`
  - `required_zero_weight_frames` -> `expected_zero_weight_frames`
  - `min_integrated_frames` -> `min_active_light_frames`
- Explicit CLI frame-gate values remain overrides over imported contract
  defaults.
- Sweep summaries record contract provenance under
  `common_run_args.frame_gate_contract`.
- Markdown summaries display the imported frame-gate contract path.
- Updated Phase 2 gate documentation and algorithm-source tracking.
- Generated a real Phase 2 benchmark-contract dry-run artifact using
  `benchmarks/phase2_m38_h_200_contract.json`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_benchmarks.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check benchmarks\\bench_resident_prefetch_sweep.py src\\glass\\report\\resident_sweep.py tests\\test_benchmarks.py`
- `.\\.venv\\Scripts\\python.exe benchmarks\\bench_resident_prefetch_sweep.py --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_106_contract_frame_gate\\dry_run --frame-gate-from-contract benchmarks\\phase2_m38_h_200_contract.json --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --dry-run`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `cmd.exe /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\\.venv\\Scripts\\cmake.exe --build build\\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_106_doctor.json --allow-cpu-only`

## Test Results

- Focused benchmark tests: `17 passed in 3.40s`
- Full pytest: `311 passed in 15.93s`
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
- Doctor artifact: `runs/checkpoints/s2_gate_106_doctor.json`

## Real Benchmark-Contract Artifact

- Contract:
  `benchmarks/phase2_m38_h_200_contract.json`
- Dry-run output:
  `C:\\glass_runs\\phase2_s2_gate_106_contract_frame_gate\\dry_run\\resident_prefetch_sweep_summary.json`
- Imported frame-gate policy:
  - expected input lights: 200
  - expected active/integrated lights: 193
  - expected zero-weight lights: 7
  - minimum active/integrated lights: 190
- Dry-run frame-gate result: 0 passed, 0 failed, 1 planned.

## Known Limitations

- This gate imports only frame-accounting requirements from benchmark
  contracts.
- Compare thresholds, compare normalization, reference-master paths, and
  guardrail settings remain explicit sweep arguments.
- The real artifact is a dry run and does not execute CUDA image processing.

## Next Step

Use `--frame-gate-from-contract` in the next bounded 200-light catalog/grid
sweep together with explicit strict compare-gate thresholds and guardrails, so
candidate promotion requires contract-derived frame counts, guardrails, image
agreement, and only then speed.

## Clean-Room Compliance

Compliant. This gate reads GLASS-owned benchmark contract JSON and GLASS sweep
artifacts only. It does not use proprietary implementation source, does not
alter image math, and does not modify input image directories.
