# S2-Gate 305 Status: Acceptance Direct Fastpath Runtime-Default Evidence

## Gate

- Gate: S2-Gate 305
- Status: Green
- Scope: acceptance-audit direct resident registration fastpath evidence
- Date: 2026-06-18

## Completed

- Added `acceptance-audit --resident-registration-fastpath-json`.
- The explicit input accepts either:
  - a resident fastpath summary record, or
  - a `resident_artifacts.json` file containing resident registration fastpath
    fields.
- The default behavior is unchanged: if the explicit input is omitted,
  acceptance audit still collects fastpath evidence from `--glass-run`.
- Refactored resident fastpath parsing into
  `resident_registration_fastpath_record_from_payload` so explicit and
  run-collected paths share the same parser.
- Added unit coverage proving an acceptance audit can pass benchmark fastpath
  contract checks from explicit `resident_artifacts.json` even when
  `--glass-run` lacks a resident fastpath artifact.
- Generated a real 200-light Gate305 acceptance artifact using:
  - Gate304 direct pipeline contract,
  - Gate211 StackEngine contract,
  - benchmark `benchmarks/phase2_m38_h_200_contract.json`,
  - explicit real-run `resident_artifacts.json`.
- Re-generated release decision, Phase2 status, and default-promotion manifest
  without using `s2_gate_303_acceptance_runtime_default_fastpath_handoff.json`.

## Artifacts

- `runs/checkpoints/s2_gate_305_acceptance_direct_fastpath_runtime_default.json`
- `runs/checkpoints/s2_gate_305_acceptance_direct_fastpath_runtime_default.md`
- `runs/checkpoints/s2_gate_305_release_decision_direct_acceptance_fastpath.json`
- `runs/checkpoints/s2_gate_305_release_decision_direct_acceptance_fastpath.md`
- `runs/checkpoints/s2_gate_305_phase2_status_direct_acceptance_fastpath.json`
- `runs/checkpoints/s2_gate_305_phase2_status_direct_acceptance_fastpath.md`
- `runs/checkpoints/s2_gate_305_default_promotion_direct_acceptance_fastpath.json`
- `runs/checkpoints/s2_gate_305_default_promotion_direct_acceptance_fastpath.md`
- `runs/checkpoints/s2_gate_305_doctor.json`

## Commands

- `.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json --out runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --markdown runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.md --pipeline-contract-json runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --stack-engine-contract-json runs\checkpoints\s2_gate_211_stack_engine_contract.json --resident-registration-fastpath-json C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\resident_artifacts.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --out runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --markdown runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.md --fail-on-not-ready`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --release-decision runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --out runs\checkpoints\s2_gate_305_phase2_status_direct_acceptance_fastpath.json --markdown runs\checkpoints\s2_gate_305_phase2_status_direct_acceptance_fastpath.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_305_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --phase2-status runs\checkpoints\s2_gate_305_phase2_status_direct_acceptance_fastpath.json --doctor-json runs\checkpoints\s2_gate_305_doctor.json --require-doctor --out runs\checkpoints\s2_gate_305_default_promotion_direct_acceptance_fastpath.json --markdown runs\checkpoints\s2_gate_305_default_promotion_direct_acceptance_fastpath.md --fail-on-not-ready`
- `.venv\Scripts\ruff.exe check src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py src\glass\cli.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m pytest tests\test_acceptance_audit.py -q`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Results

- Acceptance audit: `passed`
- Acceptance speedup vs WBPP: 58.099101701945926
- Resident fastpath source: `explicit_resident_artifacts_json`
- Resident fastpath available: true
- Resident fastpath contract checks: 24 passed, 0 failed
- Pipeline runtime-default in acceptance: `passed`
- Release decision: `default_change_ready`
- Phase2 status: `green`
- Default-promotion manifest: `default_promotion_ready`
- Focused tests: 39 passed in 1.17 s
- Full tests: 706 passed in 30.12 s
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

- This gate changes acceptance/report evidence wiring only. It does not change
  image math, CUDA kernels, runtime defaults, package builds, or GitHub
  releases.
- The explicit fastpath JSON must be supplied by the caller when `--glass-run`
  does not itself contain the desired resident fastpath artifact.
- The real benchmark was not rerun; this gate re-audits existing read-only
  artifacts.

## Next Step

- Continue reducing publication handoff glue by making the default route and
  release-publication evidence consume the latest direct acceptance and pipeline
  artifacts by default.

## Clean-Room Compliance

- No PixInsight or WBPP source code was read, copied, summarized, or modified.
- No input image directories were modified.
- The gate only consumed GLASS artifacts and user-generated black-box benchmark
  metadata.
