# S2 Gate 42 Status: Frame Accounting Acceptance Contract

## Gate

S2-Gate 42: Frame Accounting Acceptance Contract

## Completed Content

- Added benchmark-contract support for a `frame_accounting` section.
- Acceptance audit now collects `frame_accounting.json` diagnostics and includes
  them in JSON and Markdown outputs.
- Contract checks now verify:
  - accounting artifact presence
  - required input, integrated, zero-weight, and registration-accepted counts
  - required integration source stage
  - exact final-status counts
  - consistency with integration frame weights
  - consistency with speedup-summary active/zero-weight counts
  - consistency with DQ active-frame provenance
  - consistency with resident registration status counts
- Updated both M38 H-alpha 200-light benchmark contracts to require 200 input
  lights, 193 integrated lights, and 7 zero-weight lights.
- Added acceptance-audit tests for passing and mismatched frame-accounting
  contract cases.
- Updated Phase 2 planning and algorithm-source documentation.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\benchmark_contract.py src\\glass\\report\\acceptance_audit.py tests\\test_acceptance_audit.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_acceptance_audit.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\s2_gate_32_compare.json" --benchmark-contract benchmarks\\phase2_m38_h_200_audit_maps_contract.json --out "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_42.json" --markdown "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_42.md"`
- `.\\.venv\\Scripts\\python.exe -c "from glass.capabilities import capability_report; import json; print(json.dumps(capability_report(), indent=2))"`
- `.\\.venv\\Scripts\\python.exe -c "import glass_cuda, json; print(json.dumps(glass_cuda.get_device_info(0), indent=2))"`

## Test Results

- Focused acceptance-audit tests: `9 passed in 0.36s`
- Full pytest: `257 passed in 11.48s`
- Ruff: all checks passed

## CUDA Availability

- CUDA extension importable: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native resident stack available: yes

## Real Artifact Validation

- Real acceptance audit output:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_42.json`
- Markdown output:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_42.md`
- Status: passed
- Speedup vs external reference: `34.3178020369665`
- New frame-accounting contract checks: 13 checks, all passed
- Verified real counts:
  - input lights: 200
  - integrated frames: 193
  - zero-weight frames: 7
  - registration status counts: `ok=192`, `reference=1`, `excluded=7`
  - DQ active-frame counts: 193 for integration and resident records

## Known Limitations

- This gate is audit-only and does not alter image math or runtime scheduling.
- The contract enforces benchmark frame-count parity, not the scientific
  optimality of each individual exclusion.
- Older run directories without `frame_accounting.json` now fail benchmark
  contracts that opt into `frame_accounting.required=true`.

## Next Step

S2-Gate 43 should reduce resident report/accounting noise further by adding a
compact rejected-frame detail table or JSON export that focuses only on
zero-weight/rejected frames and their primary reasons.

## Clean-Room Compliance

Compliant. The gate uses GLASS-owned artifacts and user-generated benchmark
outputs only. No official PixInsight/WBPP/PJSR source code was read, copied, or
summarized.
