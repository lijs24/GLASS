# S2-Gate 304 Status: Pipeline Resident Calibration Direct Visibility

## Gate

- Gate: S2-Gate 304
- Status: Green
- Scope: pipeline-contract direct resident calibration visibility
- Date: 2026-06-18

## Completed

- Added an in-memory `pipeline-contract` fallback that builds resident
  calibration visibility from `resident_artifacts.json` when a resident-only run
  has no `calibration_artifacts.json` on disk.
- The fallback does not write back to the run directory and does not modify
  image outputs.
- The pipeline contract now directly exposes:
  - resident calibration artifact presence,
  - resident calibrated light count,
  - resident master surfaces,
  - resident calibrated-light contracts,
  - artifact source `resident_artifacts_json_fallback`,
  - `generated_for_pipeline_contract` and `write_back=false` provenance.
- Added a focused unit test proving this direct visibility path works without
  creating `calibration_artifacts.json`.
- Documented S2-Gate 304 in `docs/phase2_algorithm_hardening.md`.

## Artifacts

- `runs/checkpoints/s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json`
- `runs/checkpoints/s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.md`
- `runs/checkpoints/s2_gate_304_release_decision_resident_calibration_direct_visibility.json`
- `runs/checkpoints/s2_gate_304_release_decision_resident_calibration_direct_visibility.md`
- `runs/checkpoints/s2_gate_304_phase2_status_resident_calibration_direct_visibility.json`
- `runs/checkpoints/s2_gate_304_phase2_status_resident_calibration_direct_visibility.md`
- `runs/checkpoints/s2_gate_304_default_promotion_resident_calibration_direct_visibility.json`
- `runs/checkpoints/s2_gate_304_default_promotion_resident_calibration_direct_visibility.md`
- `runs/checkpoints/s2_gate_304_doctor.json`

## Commands

- `.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident --out runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --markdown runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.md --pixel-verify --pixel-verify-tile-size 2048`
- `.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_294_acceptance_runtime_default_ready.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --out runs\checkpoints\s2_gate_304_release_decision_resident_calibration_direct_visibility.json --markdown runs\checkpoints\s2_gate_304_release_decision_resident_calibration_direct_visibility.md --fail-on-not-ready`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_303_acceptance_runtime_default_fastpath_handoff.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --release-decision runs\checkpoints\s2_gate_304_release_decision_resident_calibration_direct_visibility.json --out runs\checkpoints\s2_gate_304_phase2_status_resident_calibration_direct_visibility.json --markdown runs\checkpoints\s2_gate_304_phase2_status_resident_calibration_direct_visibility.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_304_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_304_release_decision_resident_calibration_direct_visibility.json --phase2-status runs\checkpoints\s2_gate_304_phase2_status_resident_calibration_direct_visibility.json --doctor-json runs\checkpoints\s2_gate_304_doctor.json --require-doctor --out runs\checkpoints\s2_gate_304_default_promotion_resident_calibration_direct_visibility.json --markdown runs\checkpoints\s2_gate_304_default_promotion_resident_calibration_direct_visibility.md --fail-on-not-ready`
- `.venv\Scripts\ruff.exe check src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest tests\test_pipeline_contract.py -q`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Results

- Direct pipeline contract: `passed`
- Release decision: `default_change_ready`
- Phase2 status: `green`
- Default-promotion manifest: `default_promotion_ready`
- Pipeline resident calibration source: `resident_artifacts_json_fallback`
- Pipeline resident calibrated light count: 200
- `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\calibration_artifacts.json` remained absent.
- Focused tests: 23 passed in 1.21 s
- Full tests: 705 passed in 29.98 s
- `git diff --check`: passed, with expected Windows line-ending warnings only

## CUDA

- CUDA wrapper importable: true
- CUDA native extension loaded: true
- CUDA available: true
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Windows package try order: cuda13, cuda12, cuda11, cpu

## Known Limitations

- This gate removes the Gate303 pipeline handoff dependency only. The Phase2
  status command still uses the Gate303 acceptance fastpath handoff; removing
  that remaining acceptance-side handoff is left for a later gate.
- The fallback requires `resident_artifacts.json` to contain resident master
  stats and frame ids. Sparse legacy resident artifacts remain sparse and do
  not synthesize calibration visibility.
- No image math, CUDA kernels, runtime defaults, packages, or GitHub releases
  changed in this gate.

## Next Step

- Add direct acceptance-side fastpath/runtime-default evidence so Phase2 status
  no longer needs the Gate303 acceptance handoff bundle.

## Clean-Room Compliance

- No PixInsight or WBPP source code was read, copied, summarized, or modified.
- No input image directories were modified.
- The real GLASS run directory was audited read-only; no
  `calibration_artifacts.json` was created there.
