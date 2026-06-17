# GLASS StackEngine Default Contract Audit

- Status: passed
- Run: `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident`
- Scope: `all`
- Expected integration engine: `cuda_resident_stack`
- Resident calibration contract attached: `True`
- Resident result contract attached: `True`
- StackEngine adoption recommendation: `stack_engine_default_ready`
- Phase 2 StackEngine default gaps: `0`
- Default promotion ready: `True`

## Checks

- PASS: `calibration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\calibration_artifacts.json', 'exists': False, 'resident_calibration_contract_attached': True}
- PASS: `calibration_master_records_present` - {'actual': 1, 'required_min': 1}
- PASS: `calibration_masters_use_stack_engine` - {'master_count': 1, 'failed': []}
- PASS: `integration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\integration_results.json'}
- PASS: `integration_output_records_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_outputs_use:cuda_resident_stack` - {'output_count': 1, 'failed': []}

## StackEngine Adoption

- Target engine: `stack_engine_cpu`
- Surface count: `2`
- StackEngine surfaces: `0`
- Resident CUDA surfaces: `2`
- Contract-ready surfaces: `2`
- Gap count: `0`
- Recommendation: `stack_engine_default_ready`
- master_calibration:resident_calibration_H engine=cuda_resident_stack ready=True gap=False reason=
- integration:H engine=cuda_resident_stack ready=True gap=False reason=

## Default Promotion Guard

- Status: `ready`
- Ready: `True`
- Required scope: `all`
- Actual scope: `all`
- Blocker count: `0`
