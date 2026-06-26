# S2 Gate 702 Status

Date: 2026-06-26
Branch: `main`
Status: green

## Gate

S2-Gate 702: Pipeline DQ ledger contract.

## Completed

- Added a top-level `summary` and `dq_ledger` to `pipeline_contract.json`.
- The new DQ ledger aggregates:
  - integration DQ contract status and sample-accounting closure,
  - resident source-DQ execution,
  - resident source-DQ integration effect,
  - frame-accounting resident DQ ledger,
  - resident frame masks,
  - resident registration quality,
  - resident DQ pixel closure,
  - resident DQ lifecycle,
  - frame-accounting resident DQ lifecycle.
- `phase2-mainline-audit` now requires resident mainline runs to expose a
  passing `pipeline_contract.dq_ledger`.
- Pipeline contract markdown and Phase 2 mainline markdown now surface the DQ
  ledger status.
- Updated Phase 2 mainline and resident mainline framework fixtures so green
  resident runs must carry the same DQ ledger contract.
- Cleaned the superseded Gate702 parameter-probe directory:
  `C:\glass_runs\phase2_s2_gate702_native_completion_probe`.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py -k "resident_source_dq_execution or source_dq_not_reflected"`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_audit.py`
- `.\.venv\Scripts\python.exe -m ruff check src/glass/report/pipeline_contract.py src/glass/report/phase2_mainline_audit.py tests/test_pipeline_contract.py tests/test_phase2_mainline_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_contract.py`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\runs_20260626_102533\pipeline_dq_ledger_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\runs_20260626_102533\pipeline_dq_ledger_candidate --out C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\gate702_pipeline_dq_ledger_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\gate702_pipeline_dq_ledger_mainline_audit.md`
- `.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate701_radix_admission\runs_20260626_100214\radix_reason_candidate --candidate-run C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\runs_20260626_102533\pipeline_dq_ledger_candidate --out C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\gate702_vs_gate701_ab.json --markdown C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\gate702_vs_gate701_ab.md`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py`
- `.\.venv\Scripts\python.exe -m ruff check src/glass/report/pipeline_contract.py src/glass/report/phase2_mainline_audit.py tests/test_pipeline_contract.py tests/test_phase2_mainline_audit.py tests/test_resident_mainline_framework.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `nvidia-smi --query-gpu=name,compute_cap,memory.total,driver_version --format=csv,noheader`

## Test Results

- Focused source-DQ pipeline contract tests: `4 passed, 45 deselected`.
- Focused Phase 2 mainline audit tests: `11 passed`.
- Full pipeline-contract tests: `49 passed`.
- Focused resident mainline framework tests: `14 passed`.
- Ruff on touched files: passed.
- First full pytest exposed old resident mainline framework fixtures that lacked
  the new `pipeline_contract.dq_ledger` field.
- Full pytest after fixture updates: `1450 passed in 72.78 s`.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\runs_20260626_102533\pipeline_dq_ledger_candidate`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\gate702_pipeline_dq_ledger_mainline_audit.json`
- A/B versus Gate701:
  `C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\gate702_vs_gate701_ab.json`
- Audit passed: `True`.
- Input lights / active frames / masked frames: `200 / 193 / 7`.
- A/B passed: `True`.
- Elapsed ratio versus Gate701: `1.0396590671104042`.
- Worst component ratio: `1.06867136255919`.
- A/B failed checks: `[]`.
- Total elapsed: `12.230225099949166 s`.
- Component evidence:
  - largest component: `resident_integration=3.2608898000326008 s`
  - resident calibration/integration stage: `10.353069200064056 s`
  - component artifact status: `passed`
  - missing required components: `[]`

## DQ Ledger Evidence

The real candidate `pipeline_contract.json` recorded:

- `summary.dq_ledger_status`: `passed`
- `summary.dq_ledger_passed`: `True`
- `dq_ledger.resident_integration_required`: `True`
- `dq_ledger.integration_output_count`: `1`
- `dq_ledger.resident_integration_output_count`: `1`
- `dq_ledger.failed_sections`: `[]`
- `dq_ledger.failed_integration_outputs`: `[]`

## CUDA

- CUDA was available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97887 MiB reported by `nvidia-smi`.
- Driver: 596.21.
- Native CUDA backend was used through the installed GLASS environment.

## Known Limitations

- This gate is DQ/mask contract hardening, not a runtime optimization.
- No science pixel math changed: calibration, registration, warp, local
  normalization, rejection thresholds, integration math, CUDA kernels, frame
  admission, reducer selection, and output pixels are unchanged.
- The real run was about `3.97%` slower than Gate701, within the current A/B
  budget. This is run-to-run variation and not a new execution path.
- C drive remained tight after the formal run, with about `5.9 GB` free.

## Next Step

Return to substantive Phase 2 mainline work. The highest-value next gates are:

- resident integration/reducer architecture improvements;
- read/upload/calibration overlap with pinned memory and double or multi
  buffering;
- continued numerical and hash stability checks on the 200-light benchmark.

## Clean-Room

- This gate uses only GLASS-owned DQ/mask artifacts, frame accounting, resident
  contract surfaces, tests, and user-owned 200-light benchmark artifacts.
- No external implementation source was read or copied.
- Input image directories were treated as read-only.
