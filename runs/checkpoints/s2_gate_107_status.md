# S2-Gate 107 Status: Resident Sweep Contract Compare Import

## Gate

S2-Gate 107: Resident Sweep Contract Compare Import

## Completed

- Added `--compare-from-contract` to
  `benchmarks/bench_resident_prefetch_sweep.py`.
- The resident sweep harness can now import compare settings from a GLASS
  benchmark contract JSON:
  - shape-match requirement
  - maximum RMS difference
  - maximum p99 absolute difference
  - candidate scale
  - candidate offset
  - minimum coverage threshold
  - external reference runtime
- Explicit CLI compare values remain overrides over imported contract defaults.
- Dry-run compare gates now report `planned` instead of `failed`, matching the
  existing dry-run semantics used by frame gates.
- Sweep summaries record compare-contract provenance under
  `common_run_args.compare_contract`.
- Markdown summaries display the imported compare-contract path and planned
  compare-gate count.
- Updated Phase 2 gate documentation and algorithm-source tracking.
- Generated a real Phase 2 benchmark-contract dry-run artifact using
  `benchmarks/phase2_m38_h_200_contract.json`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_benchmarks.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check benchmarks\\bench_resident_prefetch_sweep.py src\\glass\\report\\resident_sweep.py tests\\test_benchmarks.py`
- `.\\.venv\\Scripts\\python.exe benchmarks\\bench_resident_prefetch_sweep.py --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_107_contract_compare\\dry_run --frame-gate-from-contract benchmarks\\phase2_m38_h_200_contract.json --compare-from-contract benchmarks\\phase2_m38_h_200_contract.json --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --dry-run`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `cmd.exe /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\\.venv\\Scripts\\cmake.exe --build build\\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_107_doctor.json --allow-cpu-only`

## Test Results

- Focused benchmark tests: `18 passed in 3.07s`
- Full pytest: `312 passed in 15.53s`
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
- Doctor artifact: `runs/checkpoints/s2_gate_107_doctor.json`

## Real Benchmark-Contract Artifact

- Contract:
  `benchmarks/phase2_m38_h_200_contract.json`
- Dry-run output:
  `C:\\glass_runs\\phase2_s2_gate_107_contract_compare\\dry_run\\resident_prefetch_sweep_summary.json`
- Imported compare-gate policy:
  - require shape match: true
  - maximum RMS difference: 0.01
  - maximum p99 absolute difference: 0.01
- Imported compare defaults:
  - candidate scale: `8.764434957115609e-06`
  - candidate offset: `0.0006274500691899127`
  - minimum coverage: 190
  - external reference runtime: 1092.541 s
- Dry-run compare-gate result: 0 passed, 0 failed, 1 planned.

## Known Limitations

- The imported benchmark-contract thresholds are acceptance thresholds. They may
  be looser than the stricter exploratory thresholds used when deciding whether
  a registration-tuning candidate should become a new default.
- This gate does not run CUDA image processing; the real artifact is a dry run
  that proves command planning and policy import.
- Reference-master path import is not included; `--reference-master` remains an
  explicit sweep argument.

## Next Step

Run a bounded 200-light catalog/grid sweep using:

- `--frame-gate-from-contract benchmarks/phase2_m38_h_200_contract.json`
- `--compare-from-contract benchmarks/phase2_m38_h_200_contract.json`
- explicit stricter compare overrides when evaluating promotion candidates
- guardrails and candidate coverage maps

Candidate promotion should require guardrails, contract-derived frame counts,
image agreement, and only then speed.

## Clean-Room Compliance

Compliant. This gate reads GLASS-owned benchmark contract JSON and GLASS sweep
artifacts only. It does not use proprietary implementation source, does not
alter image math, and does not modify input image directories.
