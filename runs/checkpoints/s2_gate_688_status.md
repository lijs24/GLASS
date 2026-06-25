# S2-Gate 688 Status: Resident Sample-Accounting Closure Hard Requirement

## Gate

- Gate: S2-Gate 688
- Theme: resident DQ/count-map sample-accounting closure becomes a hard
  pipeline contract.
- Status: passed

## Completed

- Added resident result-contract policy that requires
  `dq_provenance_summary.sample_accounting_closure` whenever a resident CUDA
  output writes DQ, coverage, low-rejection, or high-rejection surfaces.
- Added matching pipeline-contract policy and evidence fields:
  `required`, `required_count`, `required_policy`, and `required_maps`.
- Preserved the explicit resident master-only output exception: if DQ and
  count maps are intentionally skipped, missing sample closure is not required.
- Upgraded resident contract fixtures so current artifacts carry coherent
  input sample, input-valid, input-invalid, rejected, and final-valid counts by
  default.
- Added tests for required missing closure, master-only exemption, and pipeline
  contract failure evidence.
- Replayed real Gate687 200-light resident artifacts through the new contracts
  with pixel verification.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "sample_closure or resident_result_contract"`
- `.venv\Scripts\glass.exe resident-result-contract --run C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch --out C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_resident_result_contract.json --markdown C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_resident_result_contract.md --pixel-verify --fail-on-failed`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch --out C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_pipeline_contract.md --pixel-verify`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_result_contract.py tests/test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "sample_closure or resident_result_contract or pipeline_contract"`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "pipeline_contract or resident_result_contract or guardrails_auto_discovers_run_resident_result_contract"`
- `.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py -k "sample_accounting_closure or pipeline_contract or resident_result_contract"`
- `.venv\Scripts\python.exe -m ruff check src/glass/report/resident_result_contract.py src/glass/report/pipeline_contract.py tests/test_resident_cuda_run.py tests/test_cli_smoke.py tests/test_resident_result_contract.py tests/test_pipeline_contract.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`

## Test Results

- Focused resident result/pipeline contract tests:
  `64 passed in 2.28 s`.
- Focused resident CUDA contract tests:
  `6 passed, 130 deselected`.
- Focused CLI guardrail contract tests:
  `2 passed, 92 deselected`.
- Focused acceptance audit contract tests:
  `9 passed, 42 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1429 passed in 66.28 s`.
- Real 200-light resident-result-contract replay: passed with pixel
  verification.
- Real 200-light pipeline-contract replay: passed with pixel verification.

## Real Artifact Outputs

- Resident result contract:
  `C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_resident_result_contract.json`
- Resident result contract markdown:
  `C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_resident_result_contract.md`
- Pipeline contract:
  `C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_pipeline_contract.json`
- Pipeline contract markdown:
  `C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_pipeline_contract.md`

## CUDA

- CUDA available to GLASS: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Driver: 596.21.
- VRAM reported by GLASS: 97886 MiB.
- VRAM reported by `nvidia-smi`: 97887 MiB.

## Known Limitations

- This gate hardens resident DQ/mask contracts; it does not change calibration,
  registration, warp, local normalization, rejection thresholds, integration
  math, output pixels, or runtime performance.
- The real validation replays the existing Gate687 200-light run rather than
  executing a new full 200-light stack, because the code change is contract
  validation logic and fixture modernization.
- Master-only resident outputs are intentionally exempt when DQ/count-map
  surfaces are explicitly skipped by output policy.

## Next Step

- Return to a substantive Phase 2 mainline gate: either resident registration
  and warp residency/orchestration reduction, or a larger deterministic
  cooperative/segmented hardened reducer that attacks the remaining 200-light
  integration cost without weakening DQ/sample closure.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned DQ/provenance contracts, GLASS tests,
  and user-owned benchmark artifacts.
- No proprietary or external implementation source was inspected or used.
- Original image directories were not modified.
