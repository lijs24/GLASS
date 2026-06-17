# S2 Gate 179 Status: Release Promotion Decision Audit

## Gate

- Gate: S2-Gate 179
- Status: green
- Commit: pending at checkpoint write time
- Clean-room: compliant. This gate consumes GLASS acceptance, StackEngine,
  pipeline, runtime-compare, and repeat-preflight artifacts only. It does not
  read external implementation source, rerun heavy processing, alter image
  calculations, modify input data, or change defaults.

## Completed

- Added `glass release-promotion-decision`.
- Added a release/default decision artifact that separates:
  - `release_candidate_ready`
  - `default_change_ready`
- Release-candidate readiness requires:
  - passing acceptance audit;
  - speedup threshold;
  - passing pipeline release evidence;
  - passing StackEngine default-promotion release evidence;
  - StackEngine `default_promotion.ready=true`;
  - StackEngine scope `all`.
- Default-change readiness additionally requires stable repeat/runtime evidence:
  - minimum runtime observation count;
  - a non-repeat recommendation from `resident-runtime-compare`;
  - bounded slowest/best elapsed-time ratio.
- Optional repeat-preflight evidence records whether a controlled repeat window
  is currently available.
- Added CLI `--fail-on-not-ready` for strict release/CI usage.
- Added unit tests and CLI help coverage.

## Real Artifact Results

- Artifact root:
  `C:\glass_runs\phase2_s2_gate_179_release_promotion_decision`
- Decision JSON:
  `C:\glass_runs\phase2_s2_gate_179_release_promotion_decision\release_promotion_decision.json`
- Decision Markdown:
  `C:\glass_runs\phase2_s2_gate_179_release_promotion_decision\release_promotion_decision.md`

Key real-data outcomes:

- `status`: `release_candidate_ready`
- `recommendation`: `wait_for_controlled_window`
- `release_candidate_ready`: true
- `default_change_ready`: false
- Speedup: `46.82815250883293x`
- Runtime compare recommendation: `repeat_with_warm_cache_or_dedicated_io_window`
- Runtime observation count: `2`
- Slowest/best elapsed ratio: `1.364279174741225`
- Repeat preflight recommendation: `wait_for_controlled_window`
- Preflight GPU status: `busy`

Interpretation:

- The Gate178 result is acceptable as a release candidate.
- It is not yet ready to change runtime/default settings because the current
  repeat/runtime evidence still asks for a warm-cache or dedicated-I/O repeat.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src/glass/report/release_promotion_decision.py src/glass/cli.py tests/test_release_promotion_decision.py tests/test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_release_promotion_decision.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe release-promotion-decision --acceptance-audit C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\acceptance_resident_stack_calibration_parity.json --stack-engine-contract C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.json --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --runtime-compare C:\glass_runs\phase2_s2_gate_161_runtime_compare\runtime_compare.json --repeat-preflight C:\glass_runs\phase2_s2_gate_164_repeat_preflight\repeat_preflight.json --out C:\glass_runs\phase2_s2_gate_179_release_promotion_decision\release_promotion_decision.json --markdown C:\glass_runs\phase2_s2_gate_179_release_promotion_decision\release_promotion_decision.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_179_doctor.json
.\.venv\Scripts\glass.exe release-promotion-decision --help
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
```

## Test Results

- Focused pytest: `5 passed in 0.90s`.
- Full ruff: `All checks passed`.
- Full pytest: `447 passed in 22.14s`.

## CUDA Status

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB reported by GLASS doctor.
- Driver: 596.21.
- `nvidia-smi` at checkpoint time: GPU utilization 7%, memory 2083 / 97887 MiB.

## Known Limitations

- The decision artifact does not run repeat benchmarks; it evaluates supplied
  artifacts only.
- Runtime stability is judged by a simple slowest/best elapsed ratio and the
  existing `resident-runtime-compare` recommendation.
- The referenced repeat preflight artifact reflects the preflight moment when it
  was captured; current GPU status can change and should be rechecked before the
  next heavy benchmark.
- This gate intentionally does not alter GLASS defaults.

## Next Step

- S2-Gate 180 should run the controlled resident repeat benchmark now that the
  local GPU appears mostly free, then feed the resulting runtime compare back
  into `release-promotion-decision`.
