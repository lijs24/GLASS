# S2-Gate 181 Status - Promote Resident Throughput Preset Default

## Gate

- Gate: S2-Gate 181
- Scope: Promote `throughput-v1` from opt-in to default resident CUDA runtime preset.
- Status: green

## Completed

- `glass run` and `glass audit` now default `--resident-runtime-preset` to `throughput-v1`.
- Explicit `--resident-runtime-preset manual` remains available for legacy conservative resident scheduling.
- Explicit runtime overrides still take precedence over preset defaults.
- Acceptance benchmark token-group checks now accept effective resident runtime evidence from `resident_artifacts.json` `resident_io_pipeline` when defaults supply the schedule.
- Legacy resident CUDA scheduling tests now explicitly request `manual`.
- Phase 2 plan and algorithm-source documentation now record the default promotion and evidence.

## Real 200-Light Evidence

- Run root: `C:\glass_runs\phase2_s2_gate_181_default_runtime`
- No-preset run: `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident`
- Command record: `run_command.txt` contains no `--resident-runtime-preset`.
- Effective runtime schedule:
  - `h2d_mode=pinned_ring`
  - `prefetch_frames=12`
  - `prefetch_workers=7`
  - `calibration_batch_requested_frames=8`
  - `calibration_batch_requested_streams=4`
  - `calibration_wave_requested_frames=2`
  - `calibration_release_mode_effective=callback_queue`
- Elapsed: `18.80478299999959 s`
- Compare report: `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.html`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json`
- Acceptance audit: `C:\glass_runs\phase2_s2_gate_181_default_runtime\acceptance_default_no_preset.json`
- Release decision: `C:\glass_runs\phase2_s2_gate_181_default_runtime\release_promotion_decision_default.json`
- Acceptance status: `passed`
- Speedup versus WBPP black-box timing: `58.099101701945926x`
- Runtime slowest/best ratio: `1.0140343433372492`
- Release decision status: `default_change_ready`
- Default change ready: `true`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\benchmark_contract.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py::test_acceptance_audit_applies_benchmark_contract tests\test_acceptance_audit.py::test_acceptance_audit_accepts_resident_runtime_preset_from_artifact`
- `.\.venv\Scripts\glass.exe compare --glass ...\resident_master_H.fits --reference ...\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --glass-coverage-map ...\resident_coverage_map_H.fits --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --out ...\default_vs_reference.html`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest ... --glass-run ...\default_resident --wbpp-result ...\wbpp_blackbox_result.json --compare-json ...\default_vs_reference.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --pipeline-contract-json ...\pipeline_contract.json --stack-engine-contract-json ...\stack_engine_contract.json --out ...\acceptance_default_no_preset.json --markdown ...\acceptance_default_no_preset.md`
- `.\.venv\Scripts\glass.exe release-promotion-decision --acceptance-audit ...\acceptance_default_no_preset.json --stack-engine-contract ...\stack_engine_contract.json --pipeline-contract ...\pipeline_contract.json --runtime-compare ...\runtime_compare_default.json --ignore-warmup-runs 0 --out ...\release_promotion_decision_default.json --markdown ...\release_promotion_decision_default.md --fail-on-not-ready`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_181_doctor.json`
- `.\.venv\Scripts\glass.exe run --help > runs\checkpoints\s2_gate_181_run_help.txt`
- `.\.venv\Scripts\glass.exe audit --help > runs\checkpoints\s2_gate_181_audit_help.txt`

## Test Results

- Focused acceptance tests: `2 passed`
- Focused legacy/default resident tests: `5 passed`
- Full suite: `451 passed in 23.52 s`
- Ruff: `All checks passed`

## CUDA

- CUDA available: yes
- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Doctor JSON: `runs/checkpoints/s2_gate_181_doctor.json`

## Known Limitations

- `throughput-v1` is promoted from the controlled M38 H-alpha 200-light benchmark and local RTX PRO 6000 evidence; other disks, cameras, and GPUs still need release-matrix coverage.
- The default is a resident CUDA runtime schedule change, not a scientific algorithm change.
- CPU-only and non-resident paths remain available and are not promoted by this gate.

## Next Step

- S2-Gate 182 should add release-matrix/default-runtime regression evidence for packaged Windows CUDA variants and keep the no-preset 200-light path as the main release guard.

## Clean-Room

- Compliant. This gate uses GLASS-owned source, GLASS runtime artifacts, and user-generated black-box reference outputs only.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Original image directories were treated as read-only.
