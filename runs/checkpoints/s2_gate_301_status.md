# S2-Gate 301 Status: Release Decision Sample Accounting Scope Guard

- Gate: S2-Gate 301
- Date: 2026-06-18
- Status: Green

## Completed Work

- Hardened `glass release-promotion-decision` sample-accounting readiness checks.
- Release decisions now distinguish `passed`, explicitly `not_required`, and missing/stale required evidence.
- Missing `rejection_sample_accounting` rows are now diagnosed as `missing_required` when low/high rejection count maps are required by pixel-verification evidence.
- Added release-decision JSON fields:
  - `pipeline_rejection_sample_release`
  - `pipeline_sample_closure_release`
- Extended release-decision Markdown with sample-accounting release scope, readiness, required counts, verified counts, and present counts.
- Added focused tests for not-required sample scopes and missing required rejection-sample evidence.
- Documented S2-Gate 301 in `docs/phase2_algorithm_hardening.md`.

## Commands Run

- `.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident --out runs\checkpoints\s2_gate_301_pipeline_contract_sample_accounting_reaudit.json --markdown runs\checkpoints\s2_gate_301_pipeline_contract_sample_accounting_reaudit.md --pixel-verify --pixel-verify-tile-size 2048`
- `.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_294_acceptance_runtime_default_ready.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_211_pipeline_contract.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --out runs\checkpoints\s2_gate_301_release_decision_sample_scope_old_contract.json --markdown runs\checkpoints\s2_gate_301_release_decision_sample_scope_old_contract.md`
- `.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_294_acceptance_runtime_default_ready.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_301_pipeline_contract_sample_accounting_reaudit.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --out runs\checkpoints\s2_gate_301_release_decision_current_reaudit.json --markdown runs\checkpoints\s2_gate_301_release_decision_current_reaudit.md`
- `.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.venv\Scripts\python.exe -m pytest tests\test_release_promotion_decision.py tests\test_pipeline_contract.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Targeted ruff: passed.
- Targeted pytest: `34 passed in 1.18s`.
- Full pytest: `701 passed in 29.48s`.
- `git diff --check`: passed with line-ending warnings only.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_301_pipeline_contract_sample_accounting_reaudit.json`
- `runs/checkpoints/s2_gate_301_pipeline_contract_sample_accounting_reaudit.md`
- `runs/checkpoints/s2_gate_301_release_decision_sample_scope_old_contract.json`
- `runs/checkpoints/s2_gate_301_release_decision_sample_scope_old_contract.md`
- `runs/checkpoints/s2_gate_301_release_decision_current_reaudit.json`
- `runs/checkpoints/s2_gate_301_release_decision_current_reaudit.md`
- `runs/checkpoints/s2_gate_301_status.md`

## Real-Data Diagnostic State

- Old Gate211 pipeline contract:
  - Release decision remains blocked.
  - Rejection sample accounting is now diagnosed as `missing_required`.
  - Required low/high rejection maps: 1 output.
  - Accounted outputs: 0.
- Current re-audit of the same resident run:
  - Pipeline contract remains failed because the old run lacks the newer resident winsorized rejection semantics descriptor.
  - Rejection sample accounting check: passed.
  - Rejection map sample sum: 62488423.
  - Provenance rejected sample count: 62488423.
  - Sample closure check: passed as explicitly not required by this old artifact.
  - Release decision now blocks only on `pipeline_result_contracts_passed` for the current re-audit path.

## Known Limitations

- This gate changes release-decision guardrails only.
- It does not modify image math, CUDA kernels, StackEngine defaults, packaging, GitHub releases, or the 200-light run outputs.
- The current 200-light run predates resident winsorized semantics disclosure and therefore still fails the newest resident result contract when re-audited.
- `docs/algorithm_sources.md` was not updated because no algorithmic method or scientific formula changed.

## Next Step

- S2-Gate 302 should close the remaining `pipeline_result_contracts_passed` blocker by preserving or backfilling resident winsorized rejection semantics for release audits, without hiding old-run provenance gaps.

## Clean-Room Compliance

- No PixInsight or WBPP source code was read or used.
- This gate only consumed GLASS-generated artifacts and local run outputs.
- Original image directories were not modified.
