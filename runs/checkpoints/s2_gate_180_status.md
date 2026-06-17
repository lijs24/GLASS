# S2 Gate 180 Status: Controlled Repeat Benchmark Promotion Evidence

## Gate

- Gate: S2-Gate 180
- Status: green
- Commit: pending at checkpoint write time
- Clean-room: compliant. This gate executes GLASS repeat-plan commands and
  consumes GLASS acceptance, StackEngine, pipeline, runtime-compare, and
  preflight artifacts only. It does not read external implementation source,
  alter image calculations, modify input directories, or silently discard
  timing evidence.

## Completed

- Ran a fresh repeat preflight for the Gate162 three-run resident repeat plan.
- Preflight result: `execute_repeat_plan`, GPU status `ready`.
- Executed all three resident CUDA repeat runs with
  `glass resident-runtime-repeat-execute` using the current venv executable.
- Generated/updated the resident runtime comparison at
  `C:\glass_runs\phase2_s2_gate_162_repeat_plan\runtime_compare.json`.
- Extended `glass release-promotion-decision` with explicit
  `--ignore-warmup-runs`.
- Added tests proving a slow first warm-up run blocks default promotion unless
  the operator explicitly ignores it, and that ignored labels/counts are
  recorded in the decision evidence.
- Generated two decision artifacts:
  - without warm-up trimming: default change remains blocked;
  - with `--ignore-warmup-runs 1`: strict `--fail-on-not-ready` passes.

## Real Artifact Results

- Gate180 artifact root:
  `C:\glass_runs\phase2_s2_gate_180_controlled_repeat`
- Fresh preflight:
  `repeat_preflight.json`
- Execution audit:
  `repeat_execution.json`
- Execution preflight:
  `repeat_execution_preflight.json`
- Untrimmed decision:
  `release_promotion_decision_after_repeat.json`
- Warm-up-aware final decision:
  `release_promotion_decision_after_warmup.json`
- Runtime compare:
  `C:\glass_runs\phase2_s2_gate_162_repeat_plan\runtime_compare.json`

Measured repeat timing:

- `throughput_v1_repeat01`: `29.639423599999645 s`
- `throughput_v1_repeat02`: `18.54452279999896 s`
- `throughput_v1_repeat03`: `18.585318899999038 s`

Final decision with `--ignore-warmup-runs 1`:

- `status`: `default_change_ready`
- `recommendation`: `promote_default_candidate`
- `release_candidate_ready`: true
- `default_change_ready`: true
- Ignored warm-up labels: `throughput_v1_repeat01`
- Considered run count: `2`
- Best considered elapsed: `18.54452279999896 s`
- Slowest considered elapsed: `18.585318899999038 s`
- Slowest/best ratio: `1.0021999002314625`
- Speedup evidence retained from Gate178 acceptance: `46.82815250883293x`

## Commands Run

```powershell
.\.venv\Scripts\glass.exe resident-runtime-repeat-preflight --plan C:\glass_runs\phase2_s2_gate_162_repeat_plan\repeat_plan.json --out C:\glass_runs\phase2_s2_gate_180_controlled_repeat\repeat_preflight.json --fail-when-not-ready
.\.venv\Scripts\glass.exe resident-runtime-repeat-execute --plan C:\glass_runs\phase2_s2_gate_162_repeat_plan\repeat_plan.json --out C:\glass_runs\phase2_s2_gate_180_controlled_repeat\repeat_execution.json --require-preflight-ready --preflight-out C:\glass_runs\phase2_s2_gate_180_controlled_repeat\repeat_execution_preflight.json --glass-executable C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\glass.exe --cwd C:\Users\ljs\WORK\astro\gpuwbpp
.\.venv\Scripts\glass.exe release-promotion-decision --acceptance-audit C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\acceptance_resident_stack_calibration_parity.json --stack-engine-contract C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.json --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --runtime-compare C:\glass_runs\phase2_s2_gate_162_repeat_plan\runtime_compare.json --repeat-preflight C:\glass_runs\phase2_s2_gate_180_controlled_repeat\repeat_execution_preflight.json --out C:\glass_runs\phase2_s2_gate_180_controlled_repeat\release_promotion_decision_after_repeat.json --markdown C:\glass_runs\phase2_s2_gate_180_controlled_repeat\release_promotion_decision_after_repeat.md --fail-on-not-ready
.\.venv\Scripts\glass.exe release-promotion-decision --acceptance-audit C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\acceptance_resident_stack_calibration_parity.json --stack-engine-contract C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity\resident_stack_calibration_parity_contract.json --pipeline-contract C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract\pipeline_contract.json --runtime-compare C:\glass_runs\phase2_s2_gate_162_repeat_plan\runtime_compare.json --repeat-preflight C:\glass_runs\phase2_s2_gate_180_controlled_repeat\repeat_execution_preflight.json --ignore-warmup-runs 1 --out C:\glass_runs\phase2_s2_gate_180_controlled_repeat\release_promotion_decision_after_warmup.json --markdown C:\glass_runs\phase2_s2_gate_180_controlled_repeat\release_promotion_decision_after_warmup.md --fail-on-not-ready
.\.venv\Scripts\ruff.exe check src/glass/report/release_promotion_decision.py src/glass/cli.py tests/test_release_promotion_decision.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_release_promotion_decision.py
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_180_doctor.json
.\.venv\Scripts\glass.exe release-promotion-decision --help
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits
```

Note: the first strict `release-promotion-decision --fail-on-not-ready` command
is expected to return nonzero because no warm-up trimming was requested and the
first cold-cache run makes slowest/best ratio exceed the threshold.

## Test Results

- Focused pytest: `5 passed in 0.21s`.
- Full ruff: `All checks passed`.
- Full pytest: `448 passed in 22.96s`.

## CUDA Status

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB reported by GLASS doctor.
- Driver: 596.21.
- `nvidia-smi` at checkpoint time: GPU utilization 7%, memory 2084 / 97887 MiB.

## Known Limitations

- Warm-up handling is explicit and operator-controlled; default remains
  `--ignore-warmup-runs 0`.
- Gate180 proves runtime stability for this 200-light H-alpha benchmark and
  hardware window, not universal stability across all targets, filters, disks,
  or GPUs.
- This gate still does not change GLASS runtime defaults; it creates evidence
  that a later promotion gate can use.

## Next Step

- S2-Gate 181 should either promote the measured resident runtime preset/default
  using this evidence, or introduce a stricter release policy requiring
  additional datasets/hardware before changing defaults.
